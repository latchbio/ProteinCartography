import json
import os
import shutil
import subprocess
import sys
import typing
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from latch.ldata.path import LPath
from latch.resources.tasks import custom_task, snakemake_runtime_task
from latch.resources.workflow import workflow
from latch.types.directory import LatchDir, LatchOutputDir
from latch.types.file import LatchFile
from latch.utils import current_workspace
from latch_cli.services.register.utils import import_module_by_path


def get_config_val(val: Any):
    if val is None:
        return ""
    if isinstance(val, list):
        return [get_config_val(x) for x in val]
    if isinstance(val, dict):
        return {k: get_config_val(v) for k, v in val.items()}
    if isinstance(val, (LatchFile, LatchDir)):
        if val.remote_path is not None:
            parsed = urlparse(val.remote_path)
            domain = parsed.netloc
            if domain == "":
                ws = current_workspace()
                domain = f"{ws}.account"

            return f"/ldata/{domain}{parsed.path}"
    if isinstance(val, (int, float, bool, type(None))):
        return val
    if is_dataclass(val):
        return {f.name: get_config_val(getattr(val, f.name)) for f in fields(val)}
    if isinstance(val, Enum):
        return val.value

    return str(val)


import_module_by_path(Path("latch_metadata/__init__.py"))

import latch.types.metadata.snakemake_v2 as smv2


class PipelineMode(Enum):
    search = "search"
    cluster = "cluster"


class PlottingMode(Enum):
    pca = "pca"
    tsne = "tsne"
    umap = "umap"
    pca_tsne = "pca_tsne"
    pca_umap = "pca_umap"


class TaxonFocus(Enum):
    euk = "euk"
    bac = "bac"


@custom_task(cpu=0.25, memory=0.5, storage_gib=1)
def initialize() -> str:
    token = os.environ.get("FLYTE_INTERNAL_EXECUTION_ID")
    if token is None:
        raise RuntimeError("failed to get execution token")

    headers = {"Authorization": f"Latch-Execution-Token {token}"}

    print("Provisioning shared storage volume... ", end="")
    resp = requests.post(
        "http://nf-dispatcher-service.flyte.svc.cluster.local/provision-storage-ofs",
        headers=headers,
        json={
            "storage_expiration_hours": 2,
            "version": 2,
            "snakemake": True,
        },
    )
    resp.raise_for_status()
    print("Done.")

    return resp.json()["name"]


@snakemake_runtime_task(cpu=1, memory=2, storage_gib=50)
def snakemake_runtime(
    pvc_name: str,
    features_file: typing.Optional[LatchFile],
    features_override_file: typing.Optional[LatchFile],
    mode: PipelineMode = PipelineMode.search,
    input_dir: LatchDir = LatchDir(
        "/snakemake-workdir/inputs", "latch://1721.account/arcadia-data/inputs"
    ),
    output_dir: LatchOutputDir = LatchDir("latch://1721.account/arcadia-results"),
    analysis_name: str = "example",
    foldseek_databases: typing.List[str] = ["afdb50", "afdb-swissprot", "afdb-proteome"],
    max_foldseek_hits: int = 3000,
    max_blast_hits: int = 3000,
    blast_word_size: int = 5,
    blast_word_size_backoff: int = 6,
    blast_evalue: float = 1.0,
    blast_num_attempts: int = 3,
    max_structures: int = 5000,
    min_length: int = 0,
    max_length: int = 0,
    plotting_modes: typing.List[PlottingMode] = [PlottingMode.pca_tsne, PlottingMode.pca_umap],
    taxon_focus: TaxonFocus = TaxonFocus.euk,
):
    print(f"Using shared filesystem: {pvc_name}")

    shared = Path("/snakemake-workdir")
    snakefile = shared / "Snakefile"

    print(f"Staging {input_dir.remote_path}...", flush=True)
    input_dir = LPath(input_dir.remote_path).download(shared / "input_dir")
    print("Done.")

    config = {
        "mode": get_config_val(mode),
        "input_dir": get_config_val(input_dir),
        "output_dir": get_config_val(output_dir),
        "features_file": get_config_val(features_file),
        "features_override_file": get_config_val(features_override_file),
        "analysis_name": get_config_val(analysis_name),
        "foldseek_databases": get_config_val(foldseek_databases),
        "max_foldseek_hits": get_config_val(max_foldseek_hits),
        "max_blast_hits": get_config_val(max_blast_hits),
        "blast_word_size": get_config_val(blast_word_size),
        "blast_word_size_backoff": get_config_val(blast_word_size_backoff),
        "blast_evalue": get_config_val(blast_evalue),
        "blast_num_attempts": get_config_val(blast_num_attempts),
        "max_structures": get_config_val(max_structures),
        "min_length": get_config_val(min_length),
        "max_length": get_config_val(max_length),
        "plotting_modes": get_config_val(plotting_modes),
        "taxon_focus": get_config_val(taxon_focus),
    }

    config_path = (shared / "__latch.config.json").resolve()
    config_path.write_text(json.dumps(config, indent=2))

    print(json.dumps(config, indent=2))

    ignore_list = [
        "latch",
        ".latch",
        ".git",
        "nextflow",
        ".nextflow",
        ".snakemake",
        "results",
        "miniconda",
        "anaconda3",
        "mambaforge",
    ]

    shutil.copytree(
        Path("/root"),
        shared,
        ignore=lambda src, names: ignore_list,
        ignore_dangling_symlinks=True,
        dirs_exist_ok=True,
    )

    cmd = [
        "snakemake",
        "--snakefile",
        str(snakefile),
        "--configfile",
        str(config_path),
        "--executor",
        "latch",
        "--default-storage-provider",
        "latch",
        "--jobs",
        "1000",
        "--rerun-triggers",
        "mtime",
    ]

    print("Launching Snakemake Runtime")
    print(" ".join(cmd), flush=True)

    failed = False
    try:
        subprocess.run(cmd, cwd=shared, check=True)
    except subprocess.CalledProcessError:
        failed = True
    finally:
        if not failed:
            return

        sys.exit(1)


@workflow(smv2._snakemake_v2_metadata)
def snakemake_v2_arcadia_protein_cartography_workflow_new_storage(
    mode: PipelineMode = PipelineMode.search,
    input_dir: LatchDir = LatchDir("latch://1721.account/arcadia-data/search-mode/input"),
    output_dir: LatchOutputDir = LatchDir("latch://1721.account/arcadia-results-new-storage"),
    analysis_name: str = "example",
    foldseek_databases: typing.List[str] = ["afdb50", "afdb-swissprot", "afdb-proteome"],
    features_file: typing.Optional[LatchFile] = None,
    features_override_file: typing.Optional[LatchFile] = None,
    max_foldseek_hits: int = 3000,
    max_blast_hits: int = 3000,
    blast_word_size: int = 5,
    blast_word_size_backoff: int = 6,
    blast_evalue: float = 1.0,
    blast_num_attempts: int = 3,
    max_structures: int = 5000,
    min_length: int = 0,
    max_length: int = 0,
    plotting_modes: typing.List[PlottingMode] = [PlottingMode.pca_tsne, PlottingMode.pca_umap],
    taxon_focus: TaxonFocus = TaxonFocus.euk,
):
    """
    Sample Description
    """

    snakemake_runtime(
        pvc_name=initialize(),
        mode=mode,
        input_dir=input_dir,
        output_dir=output_dir,
        features_file=features_file,
        features_override_file=features_override_file,
        analysis_name=analysis_name,
        foldseek_databases=foldseek_databases,
        max_foldseek_hits=max_foldseek_hits,
        max_blast_hits=max_blast_hits,
        blast_word_size=blast_word_size,
        blast_word_size_backoff=blast_word_size_backoff,
        blast_evalue=blast_evalue,
        blast_num_attempts=blast_num_attempts,
        max_structures=max_structures,
        min_length=min_length,
        max_length=max_length,
        plotting_modes=plotting_modes,
        taxon_focus=taxon_focus,
    )
