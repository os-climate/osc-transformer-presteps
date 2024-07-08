#!/usr/bin/env python3
"""Python wrapper for the pre-steps needed for the transformer application in the OSC Data Extraction Project."""

# External modules
import typer

# Bundled modules
from osc_transformer_presteps.run_local_extraction import app as extraction
from osc_transformer_presteps.run_local_curation import app as curation

# Define command structure with typer module
app = typer.Typer(no_args_is_help=True)


# Additional sub-commands for extraction
app.add_typer(
    extraction,
    name="extraction",
    help="If you want to run local extraction of text from files to json then this is the subcommand to use.",
)

# Additional sub-commands for curation
app.add_typer(
    curation,
    name="curation",
    help="If you want to run local creation of dataset of json files then this is the subcommand to use.",
)


def run():
    """Provide main entry point for the OSC Transformer CLI application.

    This function sets up the Typer application with subcommands for local
    extraction and curation of data.

    Usage:
        To run local extraction:
            osc_transformer_presteps extraction

        To run local curation:
            osc_transformer_presteps curation
    """
    app()
