"""Python script for using local curation as CLI."""

import logging
from pathlib import Path
from datetime import datetime

# External modules
import typer
import pandas as pd
from osc_transformer_presteps.dataset_creation_curation.curator import Curator


_logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)

# Set the log level (e.g., DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = logging.INFO


def _specify_root_logger(log_level: int):
    """Configure the root logger with specific formatting, log level, and handlers.

    This function sets up the root logger with both a StreamHandler for stdout and a FileHandler for a log file.

    Args:
    ----
        log_level (int): The log level to use for logging.

    """
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # StreamHandler for logging to stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    # FileHandler for logging to a file
    log_dir = Path("logs")  # Specify the directory where you want to store log files
    log_dir.mkdir(
        parents=True, exist_ok=True
    )  # Create the directory if it doesn't exist
    log_filename = log_dir / datetime.now().strftime("curation_log_%d%m%Y_%H%M.log")
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    logging.root.handlers = [stream_handler, file_handler]
    logging.root.setLevel(log_level)


@app.command()
def run_local_curation(
    file_or_folder_name: str = typer.Argument(
        help="This is the directory of list of files you want to curate"
        " data from. All the files in the directory should be "
        "of json format generated from Extraction module.",
    ),
    annotation_dir: str = typer.Argument(
        help="This is the directory of annotation_xlsx file"
    ),
    kpi_mapping_dir: str = typer.Argument(
        help="This is the directory of kpi_mapping_csv file"
    ),
    create_neg_samples: bool = typer.Option(
        False,
        "--create_neg_samples",
        show_default=True,
        help="Boolean to declare if you want to include negative samples in your dataset.",
    ),
    neg_pos_ratio: int = typer.Option(
        1,
        "--neg_pos_ratio",
        show_default=True,
        help="Ratio of number of negative samples you want per positive samples.",
    ),
) -> None:
    """Start the creation of the dataset based on the extracted text on your local machine."""
    _specify_root_logger(LOG_LEVEL)

    cwd = Path.cwd()
    extracted_json_temp = cwd / file_or_folder_name
    annotation_temp = cwd / annotation_dir
    kpi_mapping_temp = cwd / kpi_mapping_dir

    _logger.info("Curation started.")

    if extracted_json_temp.is_file():
        _logger.info(f"Processing file {extracted_json_temp.stem}.")
        curated_data = curate_one_file(
            dir_extracted_json_name=extracted_json_temp,
            annotation_dir=annotation_temp,
            kpi_mapping_dir=kpi_mapping_temp,
            create_neg_samples=create_neg_samples,
            neg_pos_ratio=neg_pos_ratio,
        )
        curated_data.to_csv("Curated_dataset.csv", index=False)
        _logger.info(
            f"Added info from file {extracted_json_temp.stem}.json to the curation file."
        )

    elif extracted_json_temp.is_dir():
        files = [f for f in extracted_json_temp.iterdir() if f.is_file()]
        curator_df = pd.DataFrame()

        for file in files:
            _logger.info(f"Processing file {file.stem}.")
            temp_df = curate_one_file(
                dir_extracted_json_name=file,
                annotation_dir=annotation_temp,
                kpi_mapping_dir=kpi_mapping_temp,
                create_neg_samples=create_neg_samples,
                neg_pos_ratio=neg_pos_ratio,
            )
            curator_df = pd.concat([curator_df, temp_df], ignore_index=True)
            _logger.info(f"Added info from file {file.stem}.json to the curation file.")

        timestamp = datetime.now().strftime("%d%m%Y_%H%M")
        csv_filename = f"Curated_dataset_{timestamp}.csv"
        curator_df.to_csv(csv_filename, index=False)

    _logger.info("Curation ended.")


def curate_one_file(
    dir_extracted_json_name: Path,
    annotation_dir: Path,
    kpi_mapping_dir: Path,
    create_neg_samples: bool,
    neg_pos_ratio: int,
):
    """Curate data for a given file to a given folder for a specific setting.

    Return: Curated Dataframe
    """
    return Curator(
        annotation_folder=annotation_dir,
        extract_json=dir_extracted_json_name,
        kpi_mapping_path=kpi_mapping_dir,
        create_neg_samples=create_neg_samples,
        neg_pos_ratio=neg_pos_ratio,
    ).create_curator_df()


if __name__ == "__main__":
    app()
