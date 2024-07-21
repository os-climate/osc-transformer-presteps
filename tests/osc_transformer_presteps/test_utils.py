"""Module to test the utils.py."""

import pytest

from osc_transformer_presteps.utils import specify_root_logger, set_log_folder
import logging
from pathlib import Path

cwd = Path(__file__).resolve().parent.parent


def test_specify_root_logger():
    """Test the specify_root_logger function."""
    specify_root_logger(log_level=20, logs_folder=cwd)
    for file in cwd.iterdir():
        if file.suffix == ".log":
            file.unlink()
    assert len(logging.root.handlers) == 2
    assert isinstance(logging.root.handlers[0], logging.StreamHandler)
    assert isinstance(logging.root.handlers[1], logging.FileHandler)
    assert logging.root.handlers[0].level == 20


class TestSetLogFolder:
    """Class to collect tests for set_log_folder."""

    def test_set_log_folder_no_folder(self):
        """Test set_log_folder without a given folder."""
        log_folder = set_log_folder(cwd=Path.cwd(), logs_folder=None)
        assert log_folder == Path.cwd()

    def test_set_log_folder_given_folder_exists(self):
        """Test set_log_folder with a given existing folder."""
        log_folder = set_log_folder(cwd=Path.cwd(), logs_folder="data")
        assert log_folder.name == "data"

    def test_set_log_folder_given_folder_not_existing(self):
        """Test set_log_folder with a given non-existing folder."""
        with pytest.raises(AssertionError):
            set_log_folder(cwd=Path.cwd(), logs_folder="bla")
