"""Python Script for running extraction on cli."""

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
    specify_root_logger,
    set_log_folder,
    log_dict,
    LogLevel,
    dict_to_json,
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
    specify_root_logger(
        log_level=log_dict[LogLevel(log_level)], logs_folder=logs_folder
    )

    # Set input path
    try:
        # Try to resolve the input path as an absolute path
        file_or_folder_path_temp = Path(file_or_folder_name).resolve(strict=True)
        _logger.debug(
            f"The given path {file_or_folder_path_temp} is a valid absolute path."
        )
    except FileNotFoundError:
        # If the path is not absolute, check if it exists relative to the current working directory (cwd)
        _logger.debug(
            f"The given file_or_folder_name {file_or_folder_name} is not an absolute path, "
            f"checking as a relative path."
        )
        file_or_folder_path_temp = Path.cwd() / file_or_folder_name
        _logger.debug(
            f"Trying to resolve the path relative to cwd: {file_or_folder_path_temp}"
        )

        try:
            # Try to resolve the relative path
            file_or_folder_path_temp = file_or_folder_path_temp.resolve(strict=True)
            _logger.debug(
                f"The given path {file_or_folder_path_temp} is a valid relative path."
            )
        except FileNotFoundError:
            # If the relative path also doesn't exist, raise an error
            _logger.error(
                f"Given path {file_or_folder_name} does not exist as an absolute or relative path."
            )
            raise FileNotFoundError(
                f"Given path {file_or_folder_name} does not exist as an absolute or relative path."
            ) from None

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
    if file_or_folder_path_temp.is_dir():
        extract_from_folder(
            file_or_folder_path_temp=file_or_folder_path_temp,
            output_folder_path=output_folder_path,
            extraction_settings=extraction_settings,
        )


def extract_from_folder(
    file_or_folder_path_temp: Path,
    output_folder_path: Path,
    extraction_settings: ExtractionSettings,
) -> None:
    """Coordinate the extraction from a folder.

    Args:
    ----
        file_or_folder_path_temp (Path): The path to the folder from where we want to extract data.
        output_folder_path (Path): The path where we should store the output
        extraction_settings (ExtractionSettings): The additional settings needed.

    """
    files = [f for f in file_or_folder_path_temp.iterdir() if f.is_file()]
    _logger.info(f"Files to extract: {len(files)}.")
    extracted_files = 0
    extracted_files_list = []
    not_extracted_files_list = []
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
                extracted_files_list.append(file.name)
            else:
                not_extracted_files_list.append(file.name)
        except Exception as e:
            _logger.error(
                f"There was an error for file {file.stem}. See logs for more details."
            )
            not_extracted_files_list.append(file.name)
            _logger.debug(repr(e))
            _logger.debug(traceback.format_exc())
        count += 1
        _logger.info(
            f"Done with extracting file {file.stem}. Files to go: {len(files) - count}, "
            f"{np.round(100 * count / len(files), 2)}% done."
        )
    _logger.info(
        f"We are done with extraction. Extracted files: {extracted_files}, "
        f"{np.round(100 * extracted_files / len(files), 2)}%."
        f" Not extracted files: {len(files) - extracted_files}, "
        f"{np.round(100 * (len(files) - extracted_files) / len(files), 2)}%."
    )
    _logger.info("Extracted files: " + ", ".join(extracted_files_list))
    _logger.info("Not extracted files: " + ", ".join(not_extracted_files_list))


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
    if len(extraction_response.dictionary) > 0:
        dict_to_json(
            json_path=output_file_path, dictionary=extraction_response.dictionary
        )
    else:
        _logger.warning(
            f"There was no data extracted from file {file_path.name}. Check file and rerun."
        )
        extraction_response.success = False
    return extraction_response


if __name__ == "__main__":
    app()
