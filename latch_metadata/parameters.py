from dataclasses import dataclass
from enum import Enum

from latch.types.directory import LatchDir
from latch.types.file import LatchFile
from latch.types.metadata import SnakemakeParameter


class PlottingMode(str, Enum):
    pca = "pca"
    tsne = "tsne"
    umap = "umap"
    pca_tsne = "pca_tsne"
    pca_umap = "pca_umap"

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.value}"


class TaxonFocus(str, Enum):
    euk = "euk"
    bac = "bac"

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.value}"


class PipelineMode(str, Enum):
    search = "search"
    cluster = "cluster"

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.value}"


# Import these into your `__init__.py` file:
#
# from .parameters import generated_parameters, file_metadata

generated_parameters = {
    "mode": SnakemakeParameter(
        display_name="Mode",
        type=PipelineMode,
        default=PipelineMode.search,
    ),
    "input_dir": SnakemakeParameter(
        display_name="Input Dir",
        type=LatchDir,
        default=LatchDir("latch:///arcadia-data/inputs"),
    ),
    "output_dir": SnakemakeParameter(
        display_name="Output Dir",
        type=LatchDir,
        default=LatchDir("latch:///arcadia-results"),
    ),
    # ONLY NECESSARY FOR CLUSTER MODE
    # "features_file": SnakemakeParameter(
    #     display_name="Features File",
    #     type=LatchFile,
    # ),
    # "features_override_file": SnakemakeParameter(
    #     display_name="Features Override File",
    #     type=LatchFile,
    # ),
    "analysis_name": SnakemakeParameter(
        display_name="Analysis Name",
        type=str,
        default="example",
    ),
    "foldseek_databases": SnakemakeParameter(
        display_name="Foldseek Databases",
        type=list[str],
        default=["afdb50", "afdb-swissprot", "afdb-proteome"],
    ),
    "max_foldseek_hits": SnakemakeParameter(
        display_name="Max Foldseek Hits",
        type=int,
        default=3000,
    ),
    "max_blast_hits": SnakemakeParameter(
        display_name="Max Blast Hits",
        type=int,
        default=3000,
    ),
    "blast_word_size": SnakemakeParameter(
        display_name="Blast Word Size",
        type=int,
        default=5,
    ),
    "blast_word_size_backoff": SnakemakeParameter(
        display_name="Blast Word Size Backoff",
        type=int,
        default=6,
    ),
    "blast_evalue": SnakemakeParameter(
        display_name="Blast Evalue",
        type=float,
        default=1.0,
    ),
    "blast_num_attempts": SnakemakeParameter(
        display_name="Blast Num Attempts",
        type=int,
        default=3,
    ),
    "max_structures": SnakemakeParameter(
        display_name="Max Structures",
        type=int,
        default=5000,
    ),
    "min_length": SnakemakeParameter(
        display_name="Min Length",
        type=int,
        default=0,
    ),
    "max_length": SnakemakeParameter(
        display_name="Max Length",
        type=int,
        default=0,
    ),
    "plotting_modes": SnakemakeParameter(
        display_name="Plotting Modes",
        type=list[PlottingMode],
        default=[PlottingMode.pca_tsne, PlottingMode.pca_umap],
    ),
    "taxon_focus": SnakemakeParameter(
        display_name="Taxon Focus",
        type=TaxonFocus,
        default=TaxonFocus.euk,
    ),
}
