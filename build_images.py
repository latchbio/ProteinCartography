import subprocess
import sys
from pathlib import Path

import boto3

storage_version = "0.1.7"
registry = "812206152185.dkr.ecr.us-west-2.amazonaws.com"
image_version = Path("version").read_text().strip()
dockerfile_content = """\
from python:3.11-slim-bullseye

run apt-get update && \\
    apt-get install -y curl git

run curl -L -O \\
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh && \\
    mkdir /root/.conda && \\
    bash Miniforge3-Linux-x86_64.sh -b && \\
    rm -f Miniforge3-Linux-x86_64.sh

env PATH /root/miniforge3/bin:$PATH

copy {env_path} /root/env.yaml

run mamba env create -f /root/env.yaml -n {env_name}

env PATH /root/miniforge3/envs/{env_name}/bin:$PATH

run pip install snakemake-storage-plugin-latch=={storage_version}

"""


def get_envs() -> dict[str, str]:
    envs = {}
    for p in Path("envs").iterdir():
        env_name = p.with_suffix("").name

        if env_name.startswith("cartography"):
            continue

        envs[env_name] = p

    return envs


def get_image(env: str) -> str:
    return f"snakemake/arcadia/{env}"


def create_repositories(images: list[str]):
    ecr = boto3.client("ecr")
    for image in images:
        ecr.create_repository(
            registryId="812206152185",
            repositoryName=image,
            tags=[],
            imageTagMutability="IMMUTABLE",
            encryptionConfiguration={"encryptionType": "AES256"},
        )


def build_images(envs: dict[str, str]):
    for env_name, env_path in envs.items():
        dockerfile = Path(f"Dockerfile.{env_name}")
        dockerfile.write_text(
            dockerfile_content.format(
                env_name=env_name,
                env_path=env_path,
                storage_version=storage_version,
            )
        )

        image_uri = f"{registry}/{get_image(env_name)}:{image_version}"

        subprocess.run(
            [
                "docker",
                "build",
                "-t",
                image_uri,
                str(Path.cwd()),
                "-f",
                dockerfile,
            ]
        )

        subprocess.run(["docker", "push", image_uri])


if __name__ == "__main__":
    build_images(get_envs())
