#!/usr/bin/env python3
import argparse
import os
import subprocess
from glob import glob
from bids import BIDSLayout
import pdb

__version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'version')).read()

def run(command, env={}):
    merged_env = os.environ
    merged_env.update(env)
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, shell=True,
                               env=merged_env)

    while True:
        line = process.stdout.readline()
        line = str(line, 'utf-8')[:-1]
        print(line)
        if line == '' and process.poll() != None:
            break
    if process.returncode != 0:
        raise Exception("Non zero return code: %d"%process.returncode)

parser = argparse.ArgumentParser(description='Pydeface BIDS App')
parser.add_argument('bids_dir', help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('output_dir', help='The directory where the output files '
                    'should be stored.')
parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant'])
parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                    'corresponds to sub-<participant_label> from the BIDS spec '
                    '(so it does not include "sub-"). If this parameter is not '
                    'provided all subjects should be analyzed. Multiple '
                    'participants can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('--session_label', help='The label of the session that should be analyzed. The label '
                    'corresponds to ses-<session_label> from the BIDS spec '
                    '(so it does not include "ses-"). If this parameter is not '
                    'provided all sessions should be analyzed. Multiple '
                    'sessions can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('--n_cpus', help='Number of CPUs/cores available to use.',
                    default=1, type=int)
parser.add_argument('--modalities', help='Which modalities to deface. Space separated list.'
                    '(Use "anat" for all T1w, T2w and PD.)',
                    nargs="+", choices=['T1w', 'T2w', 'PD', 'bold',
                                        'anat', 'func', 'dwi'],
                    default=['anat'])
parser.add_argument('--skip_bids_validator', help='Whether or not to perform BIDS dataset validation',
                    action='store_true')
parser.add_argument('-v', '--version', action='version',
                    version='BIDS-App pydeface version {}'.format(__version__))


args = parser.parse_args()

if not args.skip_bids_validator:
    print("INFO: Running the bids-validator")
    run('bids-validator %s'%args.bids_dir)

print("INFO: Starting pydeface")
print("INFO: Loading bids directory")
layout = BIDSLayout(args.bids_dir)
sessions_to_analyze = []
if args.session_label:
    sessions_to_analyze = args.session_label

subjects_to_analyze = []
# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
        
# for all subjects
else:
    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

# running participant level
if args.analysis_level == "participant":

    for subject_label in subjects_to_analyze:
        print("Subject: %s"%subject_label)

        ###   Find all images to be processed:   ###
        # We'll first create a set of all the images that we need
        #   to process, to make sure we don't process the same image
        #   twice because they belong to two different modalities
        #   requested
        toBeProcessed = set()
        for modality in args.modalities:

            # In BIDSLayout, 'anat', 'func' and 'fmap' are "datatypes", while
            #    'T1w', 'T2w', 'bold', ...  are "suffixes".  ('dwi' is both).
            # So we need to make sure we call layout.get with the correct argument names:
            myKwarg = {"datatype" : modality} if modality in ['anat','func','fmap'] else {"suffix" : modality}
            if sessions_to_analyze:
                print("Sessions: %s"% sessions_to_analyze)
                myKwarg['session']=sessions_to_analyze

            # get filenames matching:
            myImages = layout.get(subject=subject_label,
                                  **myKwarg,
                                  extension=[".nii.gz", ".nii"],
                                  return_type='file')

            if (len(myImages) == 0):
                print("No {0} images found for subject {1}".format(modality, subject_label))
                if sessions_to_analyze:
                    print("  for session(s) {0}".format(sessions_to_analyze))

            toBeProcessed.update(myImages)
                
        ###   Do the processing:   ###
        # For now, we want to just overwrite the inputs, so that the BIDS root folder
        #   doesn't contain any "faced" image (well, just the 'sourcedata' DICOMS)

        # we'll be running the unwarping processes in parallel, so create a list of subprocesses:
        processes = []
        i = 0
        for myImage in toBeProcessed:
            print(myImage)
            processes.append( subprocess.Popen('pydeface {0} --outfile {0} --force'.format(myImage),
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT, shell=True,
                                                env=os.environ) )

            if len(processes) >= args.n_cpus:
                processes[i].wait()

            i = i + 1
        # Print output for each process
        for p in processes:         
            outs, errs = p.communicate()
            
            if outs is not None:
                print(str(outs, 'utf-8')[:-1])
            if errs is not None:
                print(str(errs, 'utf-8')[:-1])    
                
# nothing to run at the group level for this app
