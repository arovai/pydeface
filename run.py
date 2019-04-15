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
    print(command)
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


## def run_in_parallel(command_list, env={}):
##     merged_env = os.environ
##     merged_env.update(env)
##     print(command_list)
##     procs_list = [subprocess.Popen(cmd, stdout=subprocess.PIPE,
##                              stderr=subprocess.STDOUT,
##                              shell=True,
##                              env=merged_env) for cmd in command_list]
##     for proc in procs_list:
##         proc.wait()
    
##     while True:
##         line = process.stdout.readline()
##         line = str(line, 'utf-8')[:-1]
##         print(line)
##         if line == '' and process.poll() != None:
##             break
##     if process.returncode != 0:
##         raise Exception("Non zero return code: %d"%process.returncode)

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
    run('bids-validator %s'%args.bids_dir)

layout = BIDSLayout(args.bids_dir)
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
            # get filenames matching:
            myImages = layout.get(subject=subject_label,
                                  **myKwarg,
                                  extensions=["nii.gz", "nii"],
                                  return_type='file')
            if (len(myImages) == 0):
                print("No {0} images found for subject {1}".format(modality, subject_label))

            toBeProcessed.update(myImages)
                
        ###   Do the processing:   ###
        # For now, we want to just overwrite the inputs, so that the BIDS root folder
        #   doesn't contain any "faced" image (well, just the 'sourcedata' DICOMS)

        # we'll be running the unwarping processes in parallel, so create a set of subprocesses:
        processes = set()

        for myImage in toBeProcessed:
            processes.add( subprocess.Popen('pydeface {0} --outfile {0} --force'.format(myImage),
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT, shell=True,
                                                env=os.environ) )
            if len(processes) >= args.n_cpus:
                os.wait()
                processes.difference_update(
                    [p for p in processes if p.poll() is not None])


        # Check if all the child processes were closed:
        for p in processes:
            if p.poll() is None:
                p.wait()


# nothing to run at the group level for this app
