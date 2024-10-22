"""Python script for using local curation as CLI."""

import logging
from pathlib import Path
from datetime import datetime

# External modules
import typer
import pandas as pd
from osc_transformer_presteps.relevance_detection_dataset_curation.curator import (
    Curator,
)
from osc_transformer_presteps.utils import (
    specify_root_logger,
    set_log_folder,
    log_dict,
    LogLevel,
)


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
    annotation_file_path: str = typer.Argument(
        help="This is the path to annotations.xlsx file"
    ),
    kpi_mapping_file_path: str = typer.Argument(
        help="This is the path to kpi_mapping.csv file"
    ),
    output_path: str = typer.Argument(
        help="Path to directory to save the output curated file.",
    ),
    create_neg_samples: bool = typer.Option(
        False,
        "--create_neg_samples",
        show_default=True,
        help="Boolean to declare if you want to include negative samples in your dataset.",
    ),
    neg_sample_rate: int = typer.Option(
        1,
        "--neg_sample_rate",
        show_default=True,
        help="Number of negative samples you want per positive samples.",
    ),
    logs_folder: str = typer.Option(
        default=None,
        help="This is the folder where we store the log file. You can either provide a folder relative "
        "to the current folder or you provide an absolute path. The default will be the current folder.",
    ),
    log_level: str = typer.Option(
        "info",
        show_default=True,
        help="This gives you the possibilities to set different kinds of logging depth. Values you can choose are:"
        "'critical', 'error', 'warning', 'info', 'debug', 'notset'.",
    ),
) -> None:
    """Start the creation of the dataset based on the extracted text on your local machine."""
    cwd = Path.cwd()
    logs_folder = set_log_folder(cwd=cwd, logs_folder=logs_folder)
    specify_root_logger(
        log_level=log_dict[LogLevel(log_level)], logs_folder=logs_folder
    )

    def resolve_path(path_name: str, cwd: Path) -> Path:
        """Resolve a path as either absolute or relative to the current working directory."""
        try:
            # Try to resolve the path as an absolute path
            resolved_path = Path(path_name).resolve(strict=True)
            _logger.debug(f"The given path {resolved_path} is a valid absolute path.")
        except FileNotFoundError:
            # If it fails, check if the path exists relative to the cwd
            _logger.debug(
                f"The given path {path_name} is not an absolute path, checking as a relative path."
            )
            resolved_path = cwd / path_name
            _logger.debug(
                f"Trying to resolve the path relative to cwd: {resolved_path}"
            )
            try:
                # Try to resolve the relative path
                resolved_path = resolved_path.resolve(strict=True)
                _logger.debug(
                    f"The given path {resolved_path} is a valid relative path."
                )
            except FileNotFoundError:
                # If neither works, raise an error
                _logger.error(
                    f"Given path {path_name} does not exist as an absolute or relative path."
                )
                raise FileNotFoundError(
                    f"Given path {path_name} does not exist as an absolute or relative path."
                ) from None

        return resolved_path

    cwd = Path.cwd()
    try:
        extracted_json_temp = resolve_path(file_or_folder_name, cwd)
        annotation_temp = resolve_path(annotation_file_path, cwd)
        kpi_mapping_temp = resolve_path(kpi_mapping_file_path, cwd)

    except FileNotFoundError as e:
        _logger.error(f"Error resolving paths: {e}")
        raise

    _logger.info("Curation started.")

    if extracted_json_temp.is_file():
        _logger.info(f"Processing file {extracted_json_temp.stem}.")
        curated_data = curate_one_file(
            dir_extracted_json_name=extracted_json_temp,
            annotation_file_path=annotation_temp,
            kpi_mapping_file_path=kpi_mapping_temp,
            create_neg_samples=create_neg_samples,
            neg_sample_rate=neg_sample_rate,
        )
        curated_data.to_csv("Curated_dataset.csv", index=False)
        _logger.info(
            f"Added info from file {extracted_json_temp.stem}.json to the curation file."
        )

    elif extracted_json_temp.is_dir():
        files = [
            f
            for f in extracted_json_temp.iterdir()
            if f.is_file() and f.name.endswith(".json")
        ]
        curator_df = pd.DataFrame()

        for file in files:
            _logger.info(f"Processing file {file.stem}.")
            temp_df = curate_one_file(
                dir_extracted_json_name=file,
                annotation_file_path=annotation_temp,
                kpi_mapping_file_path=kpi_mapping_temp,
                create_neg_samples=create_neg_samples,
                neg_sample_rate=neg_sample_rate,
            )
            curator_df = pd.concat([curator_df, temp_df], ignore_index=True)
            _logger.info(f"Added info from file {file.stem}.json to the curation file.")

        timestamp = datetime.now().strftime("%d%m%Y_%H%M")
        csv_filename = Path(output_path) / f"Curated_dataset_{timestamp}.csv"
        curator_df.to_csv(csv_filename, index=False)

    _logger.info("Curation ended.")


def curate_one_file(
    dir_extracted_json_name: Path,
    annotation_file_path: Path,
    kpi_mapping_file_path: Path,
    create_neg_samples: bool,
    neg_sample_rate: int,
):
    """Curate data for a given file to a given folder for a specific setting.

    Return: Curated Dataframe
    """
    return Curator(
        annotation_folder=annotation_file_path,
        extract_json=dir_extracted_json_name,
        kpi_mapping_path=kpi_mapping_file_path,
        create_neg_samples=create_neg_samples,
        neg_sample_rate=neg_sample_rate,
    ).create_curator_df()


if __name__ == "__main__":
    app()
