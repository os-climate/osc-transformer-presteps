"""Python Script for running extraction on cli."""

import json
import logging
import traceback
from pathlib import Path
import numpy as np

# External modules
import typer

# Internal modules
from osc_transformer_presteps.content_extraction.extraction_factory import get_extractor
from osc_transformer_presteps.settings import ExtractionSettings
from osc_transformer_presteps.utils import (
    _specify_root_logger,
    set_log_folder,
    log_dict,
    LogLevel,
)
from osc_transformer_presteps.content_extraction.extractors.base_extractor import (
    ExtractionResponse,
)

_logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)


@app.command()
def run_local_extraction(
    file_or_folder_name: str = typer.Argument(
        help="This is the name of the file you want to extract"
        " data from or the folder in which you want to "
        "extract data from every file. This should be in the current folder or some subfolder. Absolute path is not"
        "possible.",
    ),
    skip_extracted_files: bool = typer.Option(
        False,
        "--skip_extracted_files",
        show_default=True,
        help="Declares if you want to skip files which have already been extracted in the past.",
    ),
    protected_extraction: bool = typer.Option(
        False,
        "--force",
        show_default=False,
        help="Boolean to allow users to extract data from protected pdf.",
    ),
    output_folder: str = typer.Option(
        default=None,
        help="This is the folder where we store the output to. The folder should be a subfolder of the current one."
        " If no folder is provided the output is stored in the current directory.",
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
    # Set logging set-up
    cwd = Path.cwd()
    logs_folder = set_log_folder(cwd=cwd, logs_folder=logs_folder)
    _specify_root_logger(
        log_level=log_dict[LogLevel(log_level)], logs_folder=logs_folder
    )

    # Set input path
    file_or_folder_path_temp = cwd / file_or_folder_name
    _logger.debug(f"The given file_or_folder_path is {file_or_folder_path_temp}.")
    assert file_or_folder_path_temp.exists(), "Given path does not exist."

    # Set settings
    extraction_settings = ExtractionSettings(
        skip_extracted_files=skip_extracted_files,
        protected_extraction=protected_extraction,
    )

    # Set output path
    output_folder_path = cwd if output_folder is None else cwd / output_folder
    _logger.debug(f"The given output_folder_path is {output_folder_path}.")
    assert output_folder_path.exists(), "The provided output folder does not exist."

    if file_or_folder_path_temp.is_file():
        _logger.debug(f"Start extracting file {file_or_folder_path_temp.stem}.")
        extract_one_file(
            output_folder=output_folder_path,
            file_path=file_or_folder_path_temp,
            extraction_settings=extraction_settings.model_dump(),
        )
        _logger.info(f"Done with extracting file {file_or_folder_path_temp.stem}.")
    elif file_or_folder_path_temp.is_dir():
        files = [f for f in file_or_folder_path_temp.iterdir() if f.is_file()]
        _logger.info(f"Files to extract: {len(files)}.")
        extracted_files = 0
        count = 0
        for file in files:
            _logger.debug(f"Start extracting file {file.stem}.")
            try:
                extraction_response = extract_one_file(
                    output_folder=output_folder_path,
                    file_path=file,
                    extraction_settings=extraction_settings.model_dump(),
                )
                if extraction_response.success:
                    extracted_files += 1
            except Exception as e:
                _logger.error(
                    f"There was an error for file {file.stem}. See logs for more details."
                )
                _logger.debug(repr(e))
                _logger.debug(traceback.format_exc())
            count += 1
            _logger.info(
                f"Done with extracting file {file.stem}. Files to go: {len(files) - count}, "
                f"{np.round(100 * count / len(files), 2)}% done."
            )
        _logger.info(
            f"We are done with extraction. Extracted files: {extracted_files}, "
            f"{np.round(100*extracted_files/len(files),2)}%."
            f" Not extracted files: {len(files)-extracted_files}, "
            f"{np.round(100*(len(files)-extracted_files)/len(files),2)}%."
        )
    else:
        _logger.error("Given file or folder name is neither a file nor a folder.")


def extract_one_file(
    output_folder: Path, file_path: Path, extraction_settings: dict
) -> ExtractionResponse:
    """Extract data for a given file to a given folder for a specific setting."""
    extractor = get_extractor(
        extractor_type=file_path.suffix, settings=extraction_settings
    )
    extraction_response = extractor.extract(input_file_path=file_path)
    output_file_name = file_path.stem + "_output.json"
    output_file_path = output_folder / output_file_name
    with open(str(output_file_path), "w") as file:
        json.dump(extraction_response.dictionary, file, indent=4)
    return extraction_response


if __name__ == "__main__":
    app()
