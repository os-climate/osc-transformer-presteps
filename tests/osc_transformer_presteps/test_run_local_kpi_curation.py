import pytest
from typer.testing import CliRunner
from src.osc_transformer_presteps.kpi_curator_main import kpi_curator_app
from pathlib import Path

# Define a CliRunner instance for invoking CLI commands
runner = CliRunner()

# Define the common working directory for mock files
cwd = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def mock_kpi_curator_data():
    """Fixture that provides mock data for KPI curation CLI testing."""
    return {
        "annotation_folder": cwd / "test_annotations.xlsx",
        "agg_annotation": "",
        "extracted_text_json_folder": cwd / "json_files",
        "output_folder": cwd / "output",
        "kpi_mapping_file": cwd / "kpi_mapping.csv",
        "relevance_file_path": cwd / "relevance_file.xlsx",
        "val_ratio": 0.2,
        "find_new_answerable": True,
        "create_unanswerable": True,
    }


class TestKPICurationCLI:
    """Test suite for the KPI curation CLI commands."""

    def test_kpi_curation_command(self, mock_kpi_curator_data):
        """Test the kpi-curation CLI command."""
        result = runner.invoke(
            kpi_curator_app,
            [
                "kpi-curation",
                "--annotation-folder",
                str(mock_kpi_curator_data["annotation_folder"]),
                "--agg-annotation",
                str(mock_kpi_curator_data["agg_annotation"]),
                "--extracted-text-json-folder",
                str(mock_kpi_curator_data["extracted_text_json_folder"]),
                "--output-folder",
                str(mock_kpi_curator_data["output_folder"]),
                "--kpi-mapping-file",
                str(mock_kpi_curator_data["kpi_mapping_file"]),
                "--relevance-file-path",
                str(mock_kpi_curator_data["relevance_file_path"]),
                "--val-ratio",
                str(mock_kpi_curator_data["val_ratio"]),
                "--find-new-answerable",
                str(mock_kpi_curator_data["find_new_answerable"]),
                "--create-unanswerable",
                str(mock_kpi_curator_data["create_unanswerable"]),
            ],
        )
        # Assert that the CLI command exited successfully
        assert result.exit_code == 0
        # Assert that the output folder exists
        output_dir = Path(mock_kpi_curator_data["output_folder"])
        assert output_dir.exists()
        # Cleanup: Remove the output directory if needed
        # output_dir.rmdir()

    def test_missing_required_arguments(self):
        """Test missing required arguments in the kpi-curation CLI command."""
        result = runner.invoke(kpi_curator_app, ["kpi-curation"])
        # Assert that the CLI command failed due to missing arguments
        assert result.exit_code != 0
        assert "Missing option" in result.stdout
