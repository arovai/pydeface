## Pydeface BIDS App

[![Docker image](https://img.shields.io/badge/docker-cbinyu/pydeface-brightgreen.svg?logo=docker&style=flat)](https://hub.docker.com/r/cbinyu/pydeface/tags/)
[![DOI](https://zenodo.org/badge/172774738.svg)](https://zenodo.org/badge/latestdoi/172774738)

This a [BIDS App](https://bids-apps.neuroimaging.io) wrapper for [Pydeface](https://github.com/poldracklab/pydeface).
Like every BIDS App it consists of a container that includes all of the dependencies and run script that parses a [BIDS dataset](http://bids.neuroimaging.io).
BIDS Apps run on Windows, Linux, Mac as well as HCPs/clusters.


### Description
Pydeface BIDS App will grab the images corresponding to the subject
and image modality requested and run Pydeface on them, overwritting
the original images.

### Documentation
Please read the official [**Pydeface**](https://github.com/poldracklab/pydeface) docs.

### Error Reporting
Experiencing problems? Please open an [issue](http://github.com/cbinyu/pydeface/issues/new) and explain what's happening so we can help.

### Usage
This App has the following command line arguments:

		usage: run.py [-h]
		              [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
			      [--session_label SESSION_LABEL [SESSION_LABEL ...]]
		              bids_dir output_dir {participant}

		Pydeface BIDS App.

		positional arguments:
		  bids_dir              The directory with the input dataset formatted
		                        according to the BIDS standard.
		  output_dir            This argument is here for BIDS-Apps
		                        compatibility. All images will be written to the bids_dir
					overwriting the input.
		  {participant}         Level of the analysis that will be performed. Multiple
		                        participant level analyses can be run independently
		                        (in parallel).

		optional arguments:
                  -h, --help            show this help message and exit
                  --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
                                        The label(s) of the participant(s) that should be
                                        analyzed. The label corresponds to
                                        sub-<participant_label> from the BIDS spec (so it does
                                        not include "sub-"). If this parameter is not provided
                                        all subjects will be analyzed. Multiple participants
                                        can be specified with a space separated list.
                  --session_label SESSION_LABEL [SESSION_LABEL ...]
                                        The label of the session that should be analyzed. The
                                        label corresponds to ses-<session_label> from the BIDS
                                        spec (so it does not include "ses-"). If this
                                        parameter is not provided all sessions should be
                                        analyzed.
                  --modality MODALITY1 [MODALITY2 ...]
                                        The modalities of images that will be defaced. They can be
                                        either suffixes (e.g.: T1w, T2w, bold) or datatype (e.g.:
                                        anat, func, fmap).  Default: anat
                  --skip_bids_validator
                                        If set, it will not run the BIDS validator before defacing.


To run it in participant level mode (for one participant):

    docker run -i --rm \
		-v /Users/filo/data/ds005:/bids_dataset \
		cbinyu/pydeface \
		/bids_dataset /bids_dataset participant --participant_label 01

To run it for a specific modality of images:

    docker run -i --rm \
                -v /Users/filo/data/ds005:/bids_dataset \
		cbinyu/pydeface \
		/bids_dataset /bids_dataset participant --participant_label 01 --modalities T1w

