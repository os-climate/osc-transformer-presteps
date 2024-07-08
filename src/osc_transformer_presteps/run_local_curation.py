"""Python script for using local curation as cli."""

import logging
import traceback
from pathlib import Path

# External modules
import typer
import pandas as pd

# Internal modules
from dataset_creation_curation.curator import Curator

_logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)


def _specify_root_logger(log_level: int):
    """
    Configure the root logger with a specific formatting and log level.

    This function sets up the root logger, which is the top-level logger in the logging hierarchy, with a specific
    configuration. It creates a StreamHandler that logs messages to stdout, sets the log level to DEBUG for all
    messages, and applies a specific formatter to format the log messages.

    Args:
        log_level (int): The log_level to use for the logging given as int.

    Usage:
    Call this function at the beginning of your code to configure the root logger
    with the desired formatting and log level.
    """
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logging.root.handlers = [handler]
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
    cwd = Path.cwd()
    extracted_json_temp = cwd / file_or_folder_name
    annotation_temp = cwd / annotation_dir
    kpi_mapping_temp = cwd / kpi_mapping_dir
    if extracted_json_temp.is_file():
        _logger.info(f"Start curating file {extracted_json_temp.stem}.")
        curate_one_file(
            dir_extracted_json_name=extracted_json_temp,
            annotation_dir=annotation_temp,
            kpi_mapping_dir=kpi_mapping_temp,
            create_neg_samples=create_neg_samples,
            neg_pos_ratio=neg_pos_ratio,
        ).to_csv("Curated_dataset.csv", index=False)
        _logger.info(f"Done with creating dataset {extracted_json_temp.stem}.")
    elif extracted_json_temp.is_dir():
        files = [f for f in extracted_json_temp.iterdir() if f.is_file()]
        curator_df = pd.DataFrame()

        for file in files:
            _logger.info(f"Start curating file {file.stem}.")
            try:
                temp_df = curate_one_file(
                    dir_extracted_json_name=file,
                    annotation_dir=annotation_temp,
                    kpi_mapping_dir=kpi_mapping_temp,
                    create_neg_samples=create_neg_samples,
                    neg_pos_ratio=neg_pos_ratio,
                )
                curator_df = pd.concat([curator_df, temp_df], ignore_index=True)
                curator_df.to_csv("Curated_dataset.csv", index=False)
                _logger.info(f"Done with creating dataset {file.stem}.")
            except Exception as e:
                _logger.error(f"The was an error for file {file.stem}.")
                _logger.error(repr(e))
                _logger.error(traceback.format_exc())
    else:
        _logger.error("Given file or folder name is neither a file nor a folder.")


def curate_one_file(
    dir_extracted_json_name: Path,
    annotation_dir: Path,
    kpi_mapping_dir: Path,
    create_neg_samples: bool,
    neg_pos_ratio: int,
):
    """
    Curate data for a given file to a given folder for a specific setting.

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
