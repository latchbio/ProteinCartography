from latch.types.metadata.latch import LatchAuthor
from latch.types.metadata.snakemake_v2 import SnakemakeV2Metadata

from .parameters import generated_parameters

SnakemakeV2Metadata(
    display_name="Arcadia Protein Cartography Workflow",
    author=LatchAuthor(name="Arcadia Biosciences"),
    # Add more parameters
    parameters=generated_parameters,
)
