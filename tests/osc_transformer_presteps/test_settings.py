"""Module to test the settings.py."""

import pytest
import logging
from osc_transformer_presteps.settings import ExtractionSettings

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
    """Fixture that provides default server settings for testing.

    Returns
    -------
        dict: A dictionary containing default server settings.

    """
    return {
        "port": 8000,
        "host": "localhost",
        "log_type": 20,
        "log_level": "info",
    }


def test_default_extraction_settings():
    """Test the default values of ExtractionSettings.

    Ensures that the default values for `skip_extracted_files` and `store_to_file` are set correctly.
    """
    settings = ExtractionSettings()
    assert not settings.skip_extracted_files
    assert not settings.protected_extraction


@pytest.mark.parametrize(
    "skip_extracted_files, protected_extraction",
    [(True, True), (False, False), (True, False)],
)
def test_extraction_settings_variations(skip_extracted_files, protected_extraction):
    """Test different variations of ExtractionSettings.

    Parameters
    ----------
    skip_extracted_files : bool
        Whether to skip extracted files.
    protected_extraction : bool
        Whether to allow extraction of protected PDFs.

    Ensures that the settings are correctly applied based on the parameters.

    """
    settings = ExtractionSettings(
        skip_extracted_files=skip_extracted_files,
        protected_extraction=protected_extraction,
    )
    assert settings.skip_extracted_files == skip_extracted_files
    assert settings.protected_extraction == protected_extraction
