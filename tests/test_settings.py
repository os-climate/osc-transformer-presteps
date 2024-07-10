import pytest
from pydantic import ValidationError
import logging 

from osc_transformer_presteps.settings import ExtractionServerSettings, ExtractionSettings, LogLevel


_log_dict = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "notset": logging.NOTSET,
}


@pytest.fixture
def default_server_settings():
    return {
        "port": 8000,
        "host": "localhost",
        "log_type": 20,
        "log_level": "info",
    }


def test_default_server_settings(default_server_settings):
    settings = ExtractionServerSettings(**default_server_settings)
    assert settings.port == 8000
    assert settings.host == "localhost"
    assert settings.log_type == 20
    assert settings.log_level == LogLevel.info


@pytest.mark.parametrize("log_level", ["critical", "error", "warning", "info", "debug", "notset"])
def test_valid_log_levels(default_server_settings, log_level):
    default_server_settings["log_level"] = log_level
    settings = ExtractionServerSettings(**default_server_settings)
    assert settings.log_level == LogLevel(log_level)
    assert settings.log_type == _log_dict[log_level]


def test_invalid_log_level(default_server_settings):
    default_server_settings["log_level"] = "invalid_log_level"
    with pytest.raises(ValueError, match="'invalid_log_level' is not a valid LogLevel"):
        ExtractionServerSettings(**default_server_settings)


def test_default_extraction_settings():
    settings = ExtractionSettings()
    assert not settings.skip_extracted_files
    assert settings.store_to_file


@pytest.mark.parametrize("skip_extracted_files,store_to_file", [(True, False), (False, False), (True, True)])
def test_extraction_settings_variations(skip_extracted_files, store_to_file):
    settings = ExtractionSettings(
        skip_extracted_files=skip_extracted_files,
        store_to_file=store_to_file
    )
    assert settings.skip_extracted_files == skip_extracted_files
    assert settings.store_to_file == store_to_file
