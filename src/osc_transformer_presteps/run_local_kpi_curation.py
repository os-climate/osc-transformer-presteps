"""File to locally run KPI-DETECTION module."""

import typer
from osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_main import (
    run_kpi_curator,
)


# Subcommand app for KPI curation
kpi_curator_app = typer.Typer(no_args_is_help=True)


@kpi_curator_app.callback(invoke_without_command=True)
def kpi_curator(ctx: typer.Context):
    """Commands for KPI curation tasks.

    Available commands:
    - kpi-curation
    """
    if ctx.invoked_subcommand is None:
        typer.echo(kpi_curator.__doc__)
        raise typer.Exit()


@kpi_curator_app.command("run-local-kpi-curation")
def kpi_curation(
    annotation_folder: str = typer.Argument(
        ..., help="Path to the folder containing Annotations file."
    ),
    extracted_text_json_folder: str = typer.Argument(
        ..., help="Folder containing extracted text data in JSON format."
    ),
    output_folder: str = typer.Argument(
        ...,
        help="Folder where the resulting train and validation CSV files will be saved.",
    ),
    kpi_mapping_file: str = typer.Argument(..., help="Path to the KPI mapping file."),
    relevance_file_path: str = typer.Argument(
        ..., help="Path to the relevance Excel file."
    ),
    val_ratio: float = typer.Option(
        0.2,
        help="Ratio of validation data (e.g., 0.2 for a 20% validation split).",
        show_default=True,
    ),
    agg_annotation: str = typer.Option(
        " ",
        help="File path for the aggregated annotation data. (if available)",
        show_default=True,
    ),
    find_new_answerable: bool = typer.Option(
        True,
        "--find-new-answerable/--no-find-new-answerable",
        help="Whether to find new answerable KPIs. Default is True.",
        show_default=True,
    ),
    create_unanswerable: bool = typer.Option(
        True,
        "--create-unanswerable/--no-create-unanswerable",
        help="Whether to create unanswerable KPIs. Default is True.",
        show_default=True,
    ),
):
    """Curates KPI data and splits it into training and validation sets."""
    try:
        # Call the KPI curator function
        run_kpi_curator(
            annotation_folder=annotation_folder,
            agg_annotation=agg_annotation,
            extracted_text_json_folder=extracted_text_json_folder,
            output_folder=output_folder,
            kpi_mapping_file=kpi_mapping_file,
            relevance_file_path=relevance_file_path,
            val_ratio=val_ratio,
            find_new_answerable=find_new_answerable,
            create_unanswerable=create_unanswerable,
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
