###   Start by creating a "builder"   ###
# We'll compile all needed packages in the builder, and then
# we'll just get only what we need for the actual APP

# Use CBI's BIDSApp_builder as a parent image:
ARG BIDSAPP_BUILDER_VERSION=v1.4
FROM cbinyu/bidsapp_builder:${BIDSAPP_BUILDER_VERSION} as builder

## install:
# -gcc compiler     (needed to install traits/pydeface)
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    g++ \
  && apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y


###   Install Pydeface   ###

# Latest release: 2.0.0 (Nov. '19)
ENV PYDEFACE_VERSION=2.0.0

# Install pydeface from github:
# 1. When running pydeface, we don't need to check that 'fsl' is installed.
#    We only need 'flirt', so we just check for it.
# 2. Installing using the official "setup.py" file does not work because
#    it installs some of the dependencies as zipped, and when you
#    call pydeface, it tries to unzip it to the PYTHON_EGG_CACHE,
#    which is set to /.cache (at least for a regular user, as opposed
#    to 'root').
#    My solution is to add the flag "zip_safe=False" to setup.py

RUN pip install pydeface==${PYDEFACE_VERSION} && \
    sed -i -e "s/which('fsl')/which('flirt')/" ${PYTHON_LIB_PATH}/site-packages/pydeface/utils.py


###   Clean up a little   ###



#############

###  Now, get a new machine with only the essentials,   ###
###    copy from the builder stage and fsl6-core what's ###
###    needed and add the BIDS-Apps wrapper (run.py)    ###
FROM cbinyu/bidsapp_builder:${BIDSAPP_BUILDER_VERSION} as Application

ENV FSLDIR=/usr/local/fsl/ \
    FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH=${FSLDIR}/bin:$PATH \
    LD_LIBRARY_PATH=${FSLDIR}:${LD_LIBRARY_PATH}

# Copy any extra python packages installed in the builder stage:
# (Note the variable ${PYTHON_LIB_PATH} is defined in the bidsapp_builder container) 
COPY --from=builder ./${PYTHON_LIB_PATH}/site-packages/      ${PYTHON_LIB_PATH}/site-packages/
COPY --from=builder ./usr/local/bin/           /usr/local/bin/
COPY --from=cbinyu/fsl6-core ./${FSLDIR}/bin/flirt  ${FSLDIR}/bin/
# The following copies both libraries to the $FSLDIR/lib folder:
COPY --from=cbinyu/fsl6-core ./${FSLDIR}/lib/libopenblas.so.0 \
                             ./${FSLDIR}/lib/libgfortran.so.3 \
			            ${FSLDIR}/lib/
# Copy an extra library needed by FSL:
COPY --from=cbinyu/fsl6-core ./usr/lib/x86_64-linux-gnu/libquadmath.so.0     \
                             ./usr/lib/x86_64-linux-gnu/libquadmath.so.0.0.0 \
                                    /usr/lib/x86_64-linux-gnu/

COPY run.py version /
RUN chmod a+rx /run.py /version

ENTRYPOINT ["/run.py"]
