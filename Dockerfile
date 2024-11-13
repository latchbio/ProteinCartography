# DO NOT CHANGE
from 812206152185.dkr.ecr.us-west-2.amazonaws.com/latch-base-snakemake:0.1.0

workdir /tmp/docker-build/work/

shell [ \
    "/usr/bin/env", "bash", \
    "-o", "errexit", \
    "-o", "pipefail", \
    "-o", "nounset", \
    "-o", "verbose", \
    "-o", "errtrace", \
    "-O", "inherit_errexit", \
    "-O", "shift_verbose", \
    "-c" \
]
env TZ='Etc/UTC'
env LANG='en_US.UTF-8'

arg DEBIAN_FRONTEND=noninteractive

# Latch SDK
# DO NOT REMOVE
run mkdir /opt/latch

run apt-get update && apt-get install -y git

run curl -L -O \
    https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Mambaforge-Linux-x86_64.sh -b \
    && rm -f Mambaforge-Linux-x86_64.sh

env PATH /root/mambaforge/bin:$PATH

copy envs/cartography_tidy.yml /root/envs/cartography_tidy.yml
run mamba env create -f /root/envs/cartography_tidy.yml -n cartography_tidy

env PATH /root/mambaforge/envs/cartography_tidy/bin:$PATH

copy snakemake_executor_plugin_latch /root/snakemake_executor_plugin_latch
run pip install /root/snakemake_executor_plugin_latch
run pip install latch==2.54.0a8 snakemake snakemake_storage_plugin_latch



# FOR DEV
env LATCH_SDK_DOMAIN ligma.ai
env LATCH_AUTHENTICATION_ENDPOINT https://nucleus.ligma.ai

# Copy workflow data (use .dockerignore to skip files)
copy . /root/

# Latch workflow registration metadata
# DO NOT CHANGE
arg tag
# DO NOT CHANGE
env FLYTE_INTERNAL_IMAGE $tag

workdir /root
