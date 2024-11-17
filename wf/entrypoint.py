import json
import os
import shutil
import subprocess
import sys
import typing
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import requests
import typing_extensions
from latch.resources.tasks import custom_task, snakemake_runtime_task
from latch.resources.workflow import workflow
from latch.types.directory import LatchDir, LatchOutputDir
from latch.types.file import LatchFile
from latch_cli.services.register.utils import import_module_by_path
from latch_cli.snakemake.v2.utils import get_config_val

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
            "storage_expiration_hours": 0,
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
    mode: PipelineMode = PipelineMode.search,
    input_dir: LatchDir = LatchDir(
        "latch://38.account/arcadia-data/inputs",
        remote_path="latch://38.account/arcadia-data/inputs",
    ),
    output_dir: LatchDir = LatchDir(
        "latch://38.account/arcadia-results", remote_path="latch://38.account/arcadia-results"
    ),
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

    config = {
        "mode": get_config_val(mode),
        "input_dir": get_config_val(input_dir),
        "output_dir": get_config_val(output_dir),
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
        "--jobs",
        "1000",
        "--rerun-triggers",
        "mtime",
        "--conda-frontend",
        "mamba",
        "--use-conda",
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
def snakemake_v2_arcadia_protein_cartography_workflow(
    mode: PipelineMode = PipelineMode.search,
    input_dir: LatchDir = LatchDir(
        "latch://38.account/arcadia-data/input",
        remote_path="latch://38.account/arcadia-data/input",
    ),
    output_dir: LatchDir = LatchDir(
        "latch://38.account/arcadia-results", remote_path="latch://38.account/arcadia-results"
    ),
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
    """
    Sample Description
    """

    snakemake_runtime(
        pvc_name=initialize(),
        mode=mode,
        input_dir=input_dir,
        output_dir=output_dir,
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
