import logging
from enum import Enum

from pydantic import BaseModel


class LogLevel(str, Enum):
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


class ExtractionServerSettings(BaseModel):
    log_level: LogLevel = LogLevel("info")
    port: int = 8000
    host: str = "localhost"

    def __init__(self, **data) -> None:
        if "log_level" in data:
            data["log_level"] = LogLevel(data["log_level"])
        super().__init__(**data)
        self.log_type: int = _log_dict[self.log_level.value]


class ExtractionSettings(BaseModel):
    skip_extracted_files: bool = False
    store_to_file: bool = True
