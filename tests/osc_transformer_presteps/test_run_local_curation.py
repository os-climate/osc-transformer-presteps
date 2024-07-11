"""Module to test the run_local_curation.py."""

import pytest
from typer.testing import CliRunner
from osc_transformer_presteps.run_local_curation import app, curate_one_file
from pathlib import Path

# Define a CliRunner instance for invoking CLI commands
runner = CliRunner()

# Define the common current working directory
cwd = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def mock_curator_data():
    """Fixture that provides mock curator settings data for testing."""
    return {
        "annotation_folder": cwd / "test_annotations_sliced.xlsx",
        "extract_json": cwd / "json_files" / "Test.json",
        "kpi_mapping_path": cwd / "kpi_mapping_sliced.csv",
        "neg_pos_ratio": 1,
        "create_neg_samples": True,
    }


class TestCurationCLI:
    """Test suite for CLI commands related to data curation."""

    def test_curate_one_file(self, mock_curator_data):
        """Test curate_one_file function."""
        result_df = curate_one_file(
            dir_extracted_json_name=mock_curator_data["extract_json"],
            annotation_dir=mock_curator_data["annotation_folder"],
            kpi_mapping_dir=mock_curator_data["kpi_mapping_path"],
            create_neg_samples=True,
            neg_pos_ratio=1,
        )
        # Assert that the resulting DataFrame is not empty
        assert not result_df.empty

    def test_run_local_curation_file(self, mock_curator_data):
        """Test running local curation using a single file."""
        result = runner.invoke(
            app,
            [
                str(mock_curator_data["extract_json"]),
                str(mock_curator_data["annotation_folder"]),
                str(mock_curator_data["kpi_mapping_path"]),
                "--create_neg_samples",
                "--neg_pos_ratio",
                "1",
            ],
        )
        # Assert that the CLI command exited successfully
        assert result.exit_code == 0
        # Assert that the output CSV file was created
        output_file = Path.cwd() / "Curated_dataset.csv"
        assert output_file.exists()
        # Clean up: Remove the created output file
        output_file.unlink(missing_ok=True)

    def test_run_local_curation_folder(self, mock_curator_data):
        """Test running local curation using a folder of JSON files."""
        result = runner.invoke(
            app,
            [
                str(cwd / "json_files"),
                str(mock_curator_data["annotation_folder"]),
                str(mock_curator_data["kpi_mapping_path"]),
                "--create_neg_samples",
                "--neg_pos_ratio",
                "1",
            ],
        )
        # Assert that the CLI command exited successfully
        assert result.exit_code == 0
        # Assert that the output CSV file was created
        output_file = Path.cwd() / "Curated_dataset.csv"
        assert output_file.exists()
        # Clean up: Remove the created output file
        output_file.unlink(missing_ok=True)
