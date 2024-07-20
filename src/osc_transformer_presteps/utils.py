import logging
from pathlib import Path
from typing import Optional
from datetime import datetime


def _specify_root_logger(log_level: int, logs_folder: Path):
    """Configure the root logger with a specific formatting and log level.

    This function sets up the root logger, which is the top-level logger in the logging hierarchy, with a specific
    configuration. It creates a StreamHandler and a FileHandler that log messages to stdout and a file, sets the log
    level to log_level for all messages, and applies a specific formatter to format the log messages.

    Args:
    ----
        log_level (int): The log_level to use for the logging given as int.
        logs_folder (Path): The folder where we store the log file.

    Usage:
    Call this function at the beginning of your code to configure the root logger
    with the desired formatting and log level.

    """
    stream_handler = logging.StreamHandler()
    file_handler = create_file_handler(logs_folder)

    logging.root.handlers = [stream_handler, file_handler]

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    for handler in logging.root.handlers:
        handler.setLevel(log_level)
        handler.setFormatter(formatter)


def create_file_handler(logs_path: Path) -> logging.FileHandler:
    """
    Creates a file handler for logging to a file.
    Args:
        logs_path (Path): The path where the log file should be stored.
    """
    initial_time = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file_name = "osc_transformer_presteps" + "_" + initial_time + ".log"
    log_file = logs_path / log_file_name
    return logging.FileHandler(log_file)


def set_log_folder(cwd: Path, logs_folder: Optional[str] = None) -> Path:
    """
    The following function creates a path object from a given logs_folder if one is given. If no string
    is provided then we choose the current working directory as the logs folder. You can either just provide
    one folder which is relative to the cwd or you give an absolute path.

    Args:
        cwd (Path): The current working directory as a path object.
        logs_folder (:obj:`str`, optional): The path we should store the logs in. Defaults to None.
            If not provided cwd is the folder to store the logs in.

    Returns:
        Path: The path where the logs will be stored.

    Raises:
        ValueError: If `cwd` does not exist.
        ValueError: If logs_folder is not none, but neither cwd / logs_folder nor logs_folder exist as folders.
    """
    assert cwd.exists(), "The given cwd is not a valid folder."
    if logs_folder is not None:
        log_path_1 = Path(logs_folder)
        log_path_2 = cwd / logs_folder
        assert log_path_1.exists() or log_path_2.exists(), "Neither logs_folder nor cwd / logs_folder is a valid path."
        return log_path_1 if log_path_1.exists() else log_path_2
    else:
        return cwd
