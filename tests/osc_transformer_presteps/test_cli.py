import pytest
from typer.testing import CliRunner
from osc_transformer_presteps.cli import app  # Import the Typer app


@pytest.fixture
def runner():
    return CliRunner()


def test_extraction_command(runner):
    result = runner.invoke(app, ["extraction"])
    assert result.exit_code == 0
    assert (
        "If you want to run local extraction of text from files to json then this is the subcommand to use."
        in result.output
    )


def test_curation_command(runner):
    result = runner.invoke(app, ["curation"])
    assert result.exit_code == 0
    assert (
        "If you want to run local creation of dataset of json files then this is the subcommand to use."
        in result.output
    )


def test_no_args(runner):
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "extraction" in result.output
    assert "curation" in result.output


def test_invalid_command(runner):
    result = runner.invoke(app, ["invalid_command"])
    assert result.exit_code != 0
    assert "No such command" in result.output
