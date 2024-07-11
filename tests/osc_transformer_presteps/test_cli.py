"""The module contains tests for the Typer-based CLI application `osc_transformer_presteps`.

The tests include checking the execution and output of various CLI commands.

Fixtures
--------
runner : CliRunner
    Provides a CliRunner instance for invoking CLI commands.

Functions
---------
test_extraction_command(runner)
    Tests the 'extraction' command.

test_curation_command(runner)
    Tests the 'curation' command.

test_no_args(runner)
    Tests running the CLI with no arguments.

test_invalid_command(runner)
    Tests running the CLI with an invalid command.
"""

import pytest
from typer.testing import CliRunner
from osc_transformer_presteps.cli import app  # Import the Typer app
import re


@pytest.fixture
def runner():
    """Fixture that provides a CliRunner instance for invoking CLI commands.

    Returns
    -------
        CliRunner: An instance of CliRunner to invoke commands.

    """
    return CliRunner()


def strip_ansi(text):
    """A helper function."""
    ansi_escape = re.compile(
        r"(?:\x1B[@-_]|[\x80-\x9F]|\x1B\[0?m|\x1B\[38;5;\d+m|\x1B\[48;5;\d+m|\x1B\[\d+;\d+;\d+;\d+;\d+m|\x1B\[\d+;\d+m|\x1B\[\d+m)"
    )
    return ansi_escape.sub("", text)


def test_extraction_command(runner):
    """Test the 'extraction' command.

    Args:
    ----
        runner (CliRunner): The CLI runner fixture.

    """
    result = runner.invoke(app, ["extraction"])
    output = strip_ansi(result.output)
    assert result.exit_code == 0
    assert (
        "If you want to run local extraction of text from files to json then this is the subcommand to use."
        in output
    )


def test_curation_command(runner):
    """Test the 'curation' command.

    Args:
    ----
        runner (CliRunner): The CLI runner fixture.

    """
    result = runner.invoke(app, ["curation"])
    output = strip_ansi(result.output)
    assert result.exit_code == 0
    assert (
        "If you want to run local creation of dataset of json files then this is the subcommand to use."
        in output
    )


def test_no_args(runner):
    """Test running the CLI with no arguments.

    Args:
    ----
        runner (CliRunner): The CLI runner fixture.

    """
    result = runner.invoke(app, [])
    output = strip_ansi(result.output)
    assert result.exit_code == 0
    assert "Usage:" in output
    assert "extraction" in output
    assert "curation" in output


def test_invalid_command(runner):
    """Test running the CLI with an invalid command.

    Args:
    ----
        runner (CliRunner): The CLI runner fixture.

    """
    result = runner.invoke(app, ["invalid_command"])
    output = strip_ansi(result.output)
    assert result.exit_code != 0
    assert "No such command" in output
