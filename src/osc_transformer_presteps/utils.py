"""Module to collect multiple functions which are helping utils for the osc-transformer-presteps package."""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
import sys
from enum import Enum
import json


class LogLevel(str, Enum):
    """Class for different log levels."""

    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"
    notset = "notset"


log_dict = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "notset": logging.NOTSET,
}


def specify_root_logger(log_level: int, logs_folder: Path):
    """Configure the root logger with a specific formatting and log level.

    This function sets up the root logger,
    which is the top-level logger in the logging hierarchy, with a specific
    configuration. It creates a StreamHandler and a FileHandler that log messages to stdout and a file, sets the log
    level to log_level for all messages, and applies a specific formatter to format the log messages.
    Usage:
    Call this function at the beginning of your code to configure the root logger
    with the desired formatting and log level.

    Attributes
    ----------
        log_level (int): The log_level to use for the logging given as int.
        logs_folder (Path): The folder where we store the log file.

    """
    logging.root.setLevel(logging.NOTSET)

    # Create stream handler with log level from the input
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)

    # Create file handler with log level DEBUG to store all information if necessary
    file_handler = create_file_handler(logs_folder)
    file_handler.setLevel(logging.DEBUG)

    # Set formatters for both handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)-8s - %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the root logger
    logging.root.handlers = [stream_handler, file_handler]


def create_file_handler(logs_path: Path) -> logging.FileHandler:
    """Create a file handler for logging to a file.

    Attributes
    ----------
        logs_path (Path): The path where the log file should be stored.

    """
    initial_time = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file_name = "osc_transformer_presteps" + "_" + initial_time + ".log"
    log_file = logs_path / log_file_name
    return logging.FileHandler(log_file)


def set_log_folder(cwd: Path, logs_folder: Optional[str] = None) -> Path:
    """Create a path object from a given logs_folder if one is given.

    This function creates a path object from a given logs_folder if one is given. If no string
    is provided then we choose the current working directory as the logs folder. You can either just provide
    one folder which is relative to the cwd or you give an absolute path.

    Returns
    -------
        Path: The path where the logs will be stored.

    Raises
    ------
        ValueError: If `cwd` does not exist.
        ValueError: If logs_folder is not none, but neither cwd / logs_folder nor logs_folder exist as folders.

    Attributes
    ----------
        cwd (Path): The current working directory as a path object.
        logs_folder (:obj:`str`, optional): The path we should store the logs in. Defaults to None.
            If not provided cwd is the folder to store the logs in.

    """
    assert cwd.exists(), "The given cwd is not a valid folder."
    if logs_folder is not None:
        log_path_1 = Path(logs_folder)
        log_path_2 = cwd / logs_folder
        assert (
            log_path_1.exists() or log_path_2.exists()
        ), "Neither logs_folder nor cwd / logs_folder is a valid path."
        return log_path_1 if log_path_1.exists() else log_path_2
    else:
        return cwd


def dict_to_json(json_path: Path, dictionary: dict) -> None:
    """Convert a dictionary to JSON and write it to a file.

    Args:
    ----
        json_path (Path): The path to the JSON file to be written.
        dictionary (dict): The dictionary to be converted to JSON.

    Returns:
    -------
        None: This function does not return anything.

    Raises:
    ------
        OSError: If there is an error writing the JSON file.

    Note:
    ----
        This function uses the `json.dump()` method from the built-in `json` module to convert the dictionary to JSON
        and write it to the specified file. The function opens the file in write mode and overwrites any existing
        content.

    Example:
    -------
        json_path = Path("output.json")
        data = {"name": "John Doe", "age": 30, "city": "New York"}

        dict_to_json(json_path, data)

    """
    with open(str(json_path), "w") as f:
        json.dump(dictionary, f, indent=4)
