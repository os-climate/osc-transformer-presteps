"""Module to test the run_local_extraction.py."""

from pathlib import Path
from osc_transformer_presteps.content_extraction.extractors.base_extractor import (
    ExtractionResponse,
    BaseExtractor,
)
from osc_transformer_presteps.utils import dict_to_json
from typing import Optional
import pytest
import os

from typer.testing import CliRunner
from osc_transformer_presteps.cli import app


def empty_folder_beside_gitkeep(path: Path) -> None:
    """Delete all files beside gitkeep.

    Attributes
    ----------
    path : Path where the files are stored.

    """
    for file in path.iterdir():
        if ".gitkeep" not in file.name:
            file.unlink()


def concrete_base_extractor(name: str):
    """Replace all abstract methods by concrete ones."""

    class ConcreteBaseExtractor(BaseExtractor):
        extractor_name = name

        def _generate_extractions(
            self,
            input_file_path: Path,
        ) -> Optional[dict]:
            return None

    return ConcreteBaseExtractor()


class TestExtractOneFile:
    """Class to store tests for extract_one_file function."""

    @pytest.fixture()
    def base_extractor(self):
        """Initialize a concrete BaseExtractor element to test it."""
        return concrete_base_extractor("base_test")

    def test_save_extraction_to_file(self, base_extractor):
        """Test if we can save the output."""
        output_file_path = (
            Path(__file__).resolve().parents[1] / "data" / "json_files" / "output.json"
        )
        er = ExtractionResponse()
        er.dictionary = {"key": "value"}
        base_extractor._extraction_response = er
        dict_to_json(json_path=output_file_path, dictionary=er.dictionary)
        assert output_file_path.exists()
        output_file_path.unlink(missing_ok=True)


class TestRunLocalExtraction:
    """Class to store tests for run_local_extraction function."""

    @pytest.fixture
    def runner(self):
        """Fixture that provides a CliRunner instance for invoking CLI commands.

        Returns
        -------
            CliRunner: An instance of CliRunner to invoke commands.

        """
        return CliRunner()

    @pytest.fixture()
    def cwd(self):
        """Define current working directory."""
        return Path(__file__).resolve().parent.parent

    @pytest.fixture()
    def pdf_path(self):
        """Define folder for pdf_files."""
        return Path("data/pdf_files")

    @pytest.fixture()
    def output_path(self):
        """Define folder for output."""
        return Path("data/output_files")

    @pytest.fixture()
    def log_path(self):
        """Define folder for logs."""
        return Path("data/logs")

    def test_run_local_extraction_one_file(
        self, cwd, pdf_path, output_path, log_path, runner
    ):
        """Test the 'extraction' command.

        Args:
        ----
            cwd: See fixture.
            pdf_path: See fixture.
            output_path: See fixture.
            log_path: See fixture.
            runner (CliRunner): The CLI runner fixture.

        """
        os.chdir(cwd)
        file_path = pdf_path / "test.pdf"
        result = runner.invoke(
            app,
            [
                "extraction",
                "run-local-extraction",
                str(file_path),
                "--output-folder=" + str(output_path),
                "--logs-folder=" + str(log_path),
                "--force",
            ],
        )
        assert result.exit_code == 0
        output_file = output_path / "test_output.json"
        assert output_file.exists()
        output_file.unlink()
        empty_folder_beside_gitkeep(log_path)

    def test_run_local_extraction_folder(
        self, cwd, pdf_path, output_path, log_path, runner
    ):
        """Test the 'extraction' command.

        Args:
        ----
            cwd: See fixture.
            pdf_path: See fixture.
            output_path: See fixture.
            log_path: See fixture.
            runner (CliRunner): The CLI runner fixture.

        """
        os.chdir(cwd)
        result = runner.invoke(
            app,
            [
                "extraction",
                "run-local-extraction",
                str(pdf_path),
                "--output-folder=" + str(output_path),
                "--logs-folder=" + str(log_path),
            ],
        )
        assert result.exit_code == 0
        output_file = output_path / "test_output.json"
        assert output_file.exists()
        empty_folder_beside_gitkeep(output_path)
        empty_folder_beside_gitkeep(log_path)
