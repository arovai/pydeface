###   Start by creating a "builder"   ###
# We'll compile all needed packages in the builder, and then
# we'll just get only what we need for the actual APP

# Use an official Python runtime as a parent image
FROM python:3.5-slim as builder

## install:
# -curl, tar, unzip (to get the FSL distribution)
# -gcc compiler     (needed to install pydeface)
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    curl \
    tar \
    unzip \
    g++ \
  && apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y


###   Install BIDS-Validator   ###

# Install nodejs and bids-validator from npm:
RUN apt-get update -qq && apt-get install -y gnupg && \
    curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get update -qq && apt-get install -y nodejs && \
    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y && \
  npm install -g bids-validator


###   Install PyBIDS   ###

RUN pip install pybids

###   Clean up a little   ###

# Get rid of some test folders in some of the Python packages:
# (They are not needed for our APP):
RUN rm -fr /usr/local/lib/python3.5/site-packages/nibabel/nicom/tests && \
    rm -fr /usr/local/lib/python3.5/site-packages/nibabel/tests       && \
    rm -fr /usr/local/lib/python3.5/site-packages/nibabel/gifti/tests    \
    # Remove scipy, because we really don't need it.                     \
    # I'm leaving the EGG-INFO folder because Nipype requires it.        \
    && rm -fr /usr/local/lib/python3.5/site-packages/scipy-1.1.0-py3.5-linux-x86_64.egg/scipy


###   Install Pydeface   ###


# Latest release: v1.1.0 (Dec. '18)

# Install pydeface from github:
RUN cd /tmp && \
    mkdir pydeface && \
    curl -sSL https://github.com/poldracklab/pydeface/archive/v1.1.0.tar.gz \
        | tar -vxz -C pydeface --strip-components=1 && \
    cd pydeface && \
    easy_install -Z ./ && \
    cd / && rm -rf /tmp/pydeface

# FOR FUTURE RELEASES:
# 1. installing using "python3 setup.py install", as suggested
#    in the pydeface documentation does not work, because it
#    installs some of the dependencies as zipped, and when you
#    call pydeface, it tries to unzip it to the PYTHON_EGG_CACHE,
#    which is set to /.cache (at least for a regular user, as opposed
#    to 'root').
#    My solution is to add the flag "zip_safe=False" to setup.py:
#    Another possibility would be to install using 'pip install .'
# 2. the "which('fsl')" occurs in the current "main" branch, not
#    in the v1.1.0 tag.  I'm leaving it here for future tags, but
#    right now it's harmless.
#
#RUN apt-get update -qq && apt-get install -y git-core && \
#    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y
#RUN cd /tmp && \
#    git clone https://github.com/poldracklab/pydeface.git && \
#    cd pydeface && \
#    sed -i -e "s/which('fsl')/which('flirt')/" pydeface/utils.py && \
#    sed -i -e "s/\([ ]*\)package_data=[a-zA-Z0-9]*,$/&\n\1zip_safe=False,/" setup.py && \
#    python3 setup.py install && \
#    cd / && rm -rf /tmp/pydeface
       

#############

###  Now, get a new machine with only the essentials  ###
###       and add the BIDS-Apps wrapper (run.py)      ###
FROM python:3.5-slim as Application

ENV FSLDIR=/usr/local/fsl/ \
    FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH=${FSLDIR}/bin:$PATH \
    LD_LIBRARY_PATH=${FSLDIR}:${LD_LIBRARY_PATH}


COPY --from=builder ./usr/local/lib/python3.5/ /usr/local/lib/python3.5/
COPY --from=builder ./usr/local/bin/           /usr/local/bin/
COPY --from=cbinyu/fsl6-core ./usr/local/fsl/bin/flirt  /usr/local/fsl/bin/
COPY --from=cbinyu/fsl6-core ./usr/local/fsl/lib/libopenblas.so.0 \
                             ./usr/local/fsl/lib/libgfortran.so.3 \
			         /usr/local/fsl/lib/
COPY --from=builder ./usr/lib/x86_64-linux-gnu /usr/lib/
COPY --from=builder ./usr/bin/                 /usr/bin/
COPY --from=builder ./usr/lib/node_modules/bids-validator/    /usr/lib/node_modules/bids-validator/

COPY run.py version /
RUN chmod a+rx /run.py /version

ENTRYPOINT ["/run.py"]
