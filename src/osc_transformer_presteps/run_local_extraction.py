"""Python Script for running extraction on cli."""

import json
import logging
import traceback
from pathlib import Path

# External modules
import typer

# Internal modules
from osc_transformer_presteps.content_extraction.extraction_factory import get_extractor
from osc_transformer_presteps.settings import ExtractionSettings
from osc_transformer_presteps.utils import _specify_root_logger, set_log_folder
from osc_transformer_presteps.settings import log_dict, LogLevel

_logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)


@app.command()
def run_local_extraction(
    file_or_folder_name: str = typer.Argument(
        help="This is the name of the file you want to extract"
        " data from or the folder in which you want to "
        "extract data from every file. This should be in the current folder.",
    ),
    skip_extracted_files_david: bool = typer.Option(
        False,
        "--skip_extracted_files",
        show_default=True,
        help="Declares if you want to skip files which have already been extracted in the past.",
    ),
    store_to_file: bool = typer.Option(
        True,
        "--store_to_file",
        show_default=True,
        help="Boolean to declare if you want to have the output as a file or not. Note that the output will"
        " be stored next to your input file with the name <input_file_name>_output.json.",
    ),
    protected_extraction: bool = typer.Option(
        False,
        "--force",
        show_default=False,
        help="Boolean to allow users to extract data from protected pdf.",
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
    """Command to start the extraction of text to json on your local machine. Check help for details."""
    cwd = Path.cwd()
    logs_folder = set_log_folder(cwd=cwd, logs_folder=logs_folder)
    _specify_root_logger(
        log_level=log_dict[LogLevel(log_level)], logs_folder=logs_folder
    )

    file_or_folder_path_temp = cwd / file_or_folder_name
    extraction_settings = ExtractionSettings(
        store_to_file=store_to_file,
        skip_extracted_files=skip_extracted_files_david,
        protected_extraction=protected_extraction,
    )
    if file_or_folder_path_temp.is_file():
        _logger.info(f"Start extracting file {file_or_folder_path_temp.stem}.")
        extract_one_file(
            output_folder=cwd,
            file_path=file_or_folder_path_temp,
            extraction_settings=extraction_settings.model_dump(),
        )
        _logger.info(f"Done with extracting file {file_or_folder_path_temp.stem}.")
    elif file_or_folder_path_temp.is_dir():
        files = [f for f in file_or_folder_path_temp.iterdir() if f.is_file()]
        for file in files:
            _logger.info(f"Start extracting file {file.stem}.")
            try:
                extract_one_file(
                    output_folder=cwd,
                    file_path=file,
                    extraction_settings=extraction_settings.model_dump(),
                )
                _logger.info(f"Done with extracting file {file.stem}.")
            except Exception as e:
                _logger.error(f"The was an error for file {file.stem}.")
                _logger.error(repr(e))
                _logger.error(traceback.format_exc())
    else:
        _logger.error("Given file or folder name is neither a file nor a folder.")


def extract_one_file(
    output_folder: Path, file_path: Path, extraction_settings: dict
) -> None:
    """Extract data for a given file to a given folder for a specific setting."""
    extractor = get_extractor(
        extractor_type=file_path.suffix, settings=extraction_settings
    )
    extraction_response = extractor.extract(input_file_path=file_path)
    output_file_name = file_path.stem + "_output.json"
    output_file_path = output_folder / output_file_name
    with open(str(output_file_path), "w") as file:
        json.dump(extraction_response.dictionary, file, indent=4)


if __name__ == "__main__":
    app()
