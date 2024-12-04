import json
import subprocess
import sys
import typing
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path

from latch.ldata.path import LPath
from latch.resources.tasks import custom_task
from latch.resources.workflow import workflow
from latch.types.directory import LatchDir, LatchOutputDir
from latch.types.file import LatchFile
from latch.types.metadata import LatchAuthor, LatchMetadata, LatchParameter


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


metadata = LatchMetadata(
    display_name="Arcadia Protein Cartography Workflow (Single Task)",
    author=LatchAuthor(name="Arcadia Biosciences"),
    parameters={
        "mode": LatchParameter(display_name="mode"),
        "input_dir": LatchParameter(display_name="input_dir"),
        "output_dir": LatchParameter(display_name="output_dir"),
        "analysis_name": LatchParameter(display_name="analysis_name"),
        "foldseek_databases": LatchParameter(display_name="foldseek_databases"),
        "max_foldseek_hits": LatchParameter(display_name="max_foldseek_hits"),
        "max_blast_hits": LatchParameter(display_name="max_blast_hits"),
        "blast_word_size": LatchParameter(display_name="blast_word_size"),
        "blast_word_size_backoff": LatchParameter(display_name="blast_word_size_backoff"),
        "blast_evalue": LatchParameter(display_name="blast_evalue"),
        "blast_num_attempts": LatchParameter(display_name="blast_num_attempts"),
        "max_structures": LatchParameter(display_name="max_structures"),
        "min_length": LatchParameter(display_name="min_length"),
        "max_length": LatchParameter(display_name="max_length"),
        "plotting_modes": LatchParameter(display_name="plotting_modes"),
        "taxon_focus": LatchParameter(display_name="taxon_focus"),
    },
)


def get_config_val(val: typing.Any):
    if isinstance(val, list):
        return [get_config_val(x) for x in val]
    if isinstance(val, dict):
        return {k: get_config_val(v) for k, v in val.items()}
    if isinstance(val, (LatchFile, LatchDir)):
        if val.remote_path is not None:
            return val.remote_path

        return str(val.path)
    if isinstance(val, (int, float, bool, type(None))):
        return val
    if is_dataclass(val):
        return {f.name: get_config_val(getattr(val, f.name)) for f in fields(val)}
    if isinstance(val, Enum):
        return val.value

    return str(val)


@custom_task(cpu=4, memory=8)
def snakemake_runtime(
    mode: PipelineMode = PipelineMode.search,
    input_dir: LatchDir = LatchDir("latch://1721.account/arcadia-data/search-mode/input"),
    output_dir: LatchDir = LatchDir("latch://1721.account/arcadia-results"),
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
    local_input_dir = LPath(input_dir.remote_path).download()
    local_output_dir = Path("/root/results")

    config = {
        "mode": get_config_val(mode),
        "input_dir": get_config_val(local_input_dir),
        "output_dir": get_config_val(local_output_dir),
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

    config_path = Path("/root/latch.config.json").resolve()
    config_path.write_text(json.dumps(config, indent=2))

    cmd = [
        "snakemake",
        "--cores",
        "1",
        "--configfile",
        str(config_path),
        "--rerun-triggers",
        "mtime",
        "--conda-frontend",
        "mamba",
        "--use-conda",
    ]

    print("Launching Snakemake Runtime")
    print(" ".join(cmd), flush=True)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)

    LPath(output_dir.remote_path).upload_from(local_output_dir)


@workflow(metadata)
def single_task_arcadia_protein_cartography_workflow(
    mode: PipelineMode = PipelineMode.search,
    input_dir: LatchDir = LatchDir("latch://1721.account/arcadia-data/search-mode/input"),
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
    """
    Sample Description
    """

    snakemake_runtime(
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
