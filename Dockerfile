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
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniforge3-Linux-x86_64.sh -b \
    && rm -f Miniforge3-Linux-x86_64.sh

env PATH /root/miniforge3/bin:$PATH

copy envs /root/envs
run mamba env create -f /root/envs/analysis.yml
run mamba env create -f /root/envs/blast.yml
run mamba env create -f /root/envs/cartography_dev.yml
run mamba env create -f /root/envs/cartography_pub.yml
run mamba env create -f /root/envs/cartography_test.yml
run mamba env create -f /root/envs/foldseek.yml
run mamba env create -f /root/envs/pandas.yml
run mamba env create -f /root/envs/plotting.yml
run mamba env create -f /root/envs/web_apis.yml

run mamba env create -f /root/envs/cartography_tidy.yml

env PATH /root/miniforge3/envs/cartography_tidy/bin:$PATH

run pip install \
        latch==2.54.0a8 \
        snakemake

# Copy workflow data (use .dockerignore to skip files)
copy . /root/

# Latch workflow registration metadata
# DO NOT CHANGE
arg tag
# DO NOT CHANGE
env FLYTE_INTERNAL_IMAGE $tag

workdir /root
