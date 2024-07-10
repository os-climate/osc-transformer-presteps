"""Module to collect settings for the FastAPI server."""

from pydantic import BaseModel
from enum import Enum
import logging


class LogLevel(str, Enum):
    """Class for different log levels."""

    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"
    notset = "notset"


_log_dict = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "notset": logging.NOTSET,
}


class ExtractionServerSettingsBase(BaseModel):
    """Class for Extraction server settings."""

    port: int = 8000
    host: str = "localhost"
    log_type: int = 20
    log_level: LogLevel = LogLevel("info")


class ExtractionServerSettings(ExtractionServerSettingsBase):
    """Settings for configuring the extraction server.

    This class extends `ExtractionServerSettingsBase` and adds additional
    logging configuration.
    """

    def __init__(self, **data) -> None:
        """Initialize the ExtractionServerSettings."""
        if "log_level" in data:
            data["log_level"] = LogLevel(data["log_level"])
        super().__init__(**data)
        self.log_type: int = _log_dict[self.log_level.value]
