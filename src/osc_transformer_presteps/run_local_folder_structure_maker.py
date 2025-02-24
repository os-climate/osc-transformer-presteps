"""File to locally run make-folder-structure module."""

import typer
from osc_transformer_presteps.folderizer.folderizer_main import (
    create_osc_folder_structure,
)

folderizer_app = typer.Typer(no_args_is_help=True)


@folderizer_app.callback(invoke_without_command=True)
def folderizer(ctx: typer.Context):
    """Commands for Folderizer .

    Available commands:
    - make-folder-structure
    """
    if ctx.invoked_subcommand is None:
        typer.echo(folderizer.__doc__)
        raise typer.Exit()


@folderizer_app.command("run-folder-structure-maker")
def run_folderizer(
    base_path: str = typer.Argument(
        ..., help="Base Path where the folder structure will be made"
    ),
):
    """Create a folder structure needed for running OSC pipelines."""
    try:
        # Call the create folder maker function
        create_osc_folder_structure(base_path=base_path)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
