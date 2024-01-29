import logging
import traceback
from pathlib import Path
from pprint import pformat
from typing import Dict, Optional, Union

from src.osc_transformer_presteps.content_extraction.extraction_factory import (
    get_extractor,
)

__author__ = "David Besslich"
__copyright__ = "David Besslich"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

log_levels = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def specify_root_logger(log_level: str):
    """
    Configures the root logger with a specific formatting and log level.

    This function sets up the root logger, which is the top-level logger in the logging hierarchy, with a specific
    configuration. It creates a StreamHandler that logs messages to stdout, sets the log level to DEBUG for all
    messages, and applies a specific formatter to format the log messages.

    Args:
        log_level (str): The log_level to use for the logging.

    Usage:
    Call this function at the beginning of your code to configure the root logger
    with the desired formatting and log level.
    """
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    log_level_value = log_levels[log_level.upper()]

    handler = logging.StreamHandler()
    handler.setLevel(log_level_value)
    handler.setFormatter(formatter)

    logging.root.handlers = [handler]
    logging.root.setLevel(log_level_value)


def extract_main(
    input_file_path: Path,
    output_file_path: Optional[Path] = None,
    settings: Optional[Dict[str, Union[str, bool]]] = None,
) -> Dict[int, Dict[str, str]]:
    """
    Extract information from an input file using a specified extractor and save the extraction results to a file.

    Args:
        input_file_path (Path): The path of the input file.
        output_file_path (Path): The path of the output file to save the extraction results.
        settings (Dict[str, Union[str, bool]]): A dictionary containing the settings for the extractor.

    Returns:
        Union[None, str]: The extracted information if successful, otherwise None.

    Example:
        input_file_path = Path("input.pdf")
        output_file_path = Path("output.json")
        settings = {
            "option1": True,
            "option2": "value2",
            "store_to_file": True
        }

        output = extract_main(input_file_path, output_file_path, settings)
    """
    extractor = get_extractor(input_file_path.suffix, settings)
    if not extractor.check_for_skip_files(input_file_path, output_file_path):
        extractor.extract(input_file_path=input_file_path)

    if extractor.get_settings()["store_to_file"] and output_file_path is not None:
        extractor.save_extraction_to_file(output_file_path=output_file_path)

    return extractor.get_extractions()


if __name__ == "__main__":
    specify_root_logger("info")
    try:
        input_folder = Path(__file__).resolve().parent / "input"
        output_folder = Path(__file__).resolve().parent / "output"

        file_name = "test.pdf"

        input_file_path_main = input_folder / file_name
        output_file_path_main = output_folder / input_file_path_main.with_suffix(".json").name
        settings_main: Optional[Dict[str, Union[str, bool]]] = {"skip_extracted_files": False, "store_to_file": False}

        _logger.info(f"Input file path is :\n {input_file_path_main}.")
        extraction_dict = extract_main(
            input_file_path=input_file_path_main, output_file_path=output_file_path_main, settings=settings_main
        )
        _logger.debug(pformat(extraction_dict))
    except Exception as e:
        _logger.error("---ERROR---" * 10)
        _logger.error(repr(e))
        _logger.error(traceback.format_exc())
