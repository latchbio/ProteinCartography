import subprocess
import sys
from pathlib import Path

import boto3

storage_version = "0.1.5"
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

        # subprocess.run(
        #     [
        #         "docker",
        #         "build",
        #         "-t",
        #         image_uri,
        #         str(Path.cwd()),
        #         "-f",
        #         dockerfile,
        #     ]
        # )

        subprocess.run(["docker", "push", image_uri])


if __name__ == "__main__":
    build_images(get_envs())


# sys.exit()

# images = [
#     "snakemake/seqtk",
#     "snakemake/pandas",
#     "snakemake/pheniqs",
#     "snakemake/minimap",
#     "snakemake/plot-observed",
# ]

# new_images = []

# for image in images:
#     dockerfile = dockerfiles_root_path / image / "Dockerfile"
#     version_file = dockerfiles_root_path / image / "version"

#     ver = version_file.read_text()
#     old_tagged = f"{image}:{ver}"

#     major, minor, patch = ver.split(".")
#     next_ver = f"{major}.{minor}.{int(patch) + 1}"
#     version_file.write_text(next_ver)

#     new_image = f"{registry}/{image}:{next_ver}"
#     new_images.append(new_image)

#     dockerfile_content = dockerfile.read_text()
#     base_image, rest = dockerfile_content.split("\n", 1)
#     base_image = f"from {registry}/{image}:{ver}"

#     dockerfile.write_text("\n".join([base_image, rest]))

#     # subprocess.run(
#     #     [
#     #         "docker",
#     #         "build",
#     #         "-t",
#     #         new_image,
#     #         str(Path.cwd()),
#     #         "-f",
#     #         dockerfile,
#     #         "--build-arg",
#     #         f"snakemake_storage_plugin_ver={storage_version}",
#     #     ]
#     # )

#     # subprocess.run(["docker", "push", new_image])

#     snakefile_content = snakefile_content.replace(old_tagged, new_image)


# print("Built and Pushed Images:")
# for new_image in new_images:
#     print(new_image)


# snakefile.write_text(snakefile_content)
