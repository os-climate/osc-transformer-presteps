"""Python Script to handle logging and Extraction Settings."""

import logging
from enum import Enum

from pydantic import BaseModel


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


class ExtractionSettings(BaseModel):
    """Settings for controlling extraction behavior.

    Attributes
    ----------
    skip_extracted_files : bool, optional
        Flag indicating whether to skip files that have already been extracted.
        Defaults to False.
    store_to_file : bool, optional
        Flag indicating whether to store the extracted data to a file.
        Defaults to True.
    protected_extraction: bool, optional
        Flag allowing users to extract the protected pdf.
        Defaults to False.

    """

    skip_extracted_files: bool = False
    store_to_file: bool = True
    protected_extraction: bool = False
