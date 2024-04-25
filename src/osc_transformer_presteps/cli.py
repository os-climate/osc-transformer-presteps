#!/usr/bin/env python3

"""Python wrapper for the pre-steps needed for the transformer application in
the OSC Data Extraction Project"""

# External modules
import typer

# Bundled modules
from osc_transformer_presteps.run_local_extraction import app as extraction

# Define command structure with typer module
app = typer.Typer(no_args_is_help=True)


# Additional sub-commands
app.add_typer(
    extraction,
    name="extraction",
    help="If you want to run local extraction of text from files to json then this is the subcommand to use.",
)


def run():
    app()
