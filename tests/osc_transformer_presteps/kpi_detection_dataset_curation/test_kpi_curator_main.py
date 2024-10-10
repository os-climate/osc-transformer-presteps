import pytest
from unittest.mock import patch
from src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_main import (
    run_kpi_curator,
)
import os
from datetime import date
import pandas as pd


@pytest.fixture
def mock_curator_data():
    """Fixture that provides mock data for KPI curation function testing."""
    return {
        "annotation_folder": "tests/mock_data/test_annotations.xlsx",
        "agg_annotation": "",
        "extracted_text_json_folder": "tests/mock_data/json_files",
        "output_folder": "tests/mock_data/output",
        "kpi_mapping_file": "tests/mock_data/kpi_mapping.csv",
        "relevance_file_path": "tests/mock_data/relevance_file.xlsx",
        "val_ratio": 0.2,
        "find_new_answerable": True,
        "create_unanswerable": True,
    }


@pytest.fixture
def mock_train_val_dfs():
    """Fixture to provide mock training and validation DataFrames."""
    train_df = pd.DataFrame({"kpi_id": [1, 2], "kpi_value": ["value1", "value2"]})
    val_df = pd.DataFrame({"kpi_id": [3], "kpi_value": ["value3"]})
    return train_df, val_df


class TestKPICurator:
    """Test suite for the run_kpi_curator function."""

    @patch("src.osc_transformer_presteps.kpi_curator_main.curate")
    @patch("src.osc_transformer_presteps.kpi_curator_main._logger")
    def test_run_kpi_curator(
        self, mock_logger, mock_curate, mock_curator_data, mock_train_val_dfs
    ):
        """Test the run_kpi_curator function with valid inputs and mocks."""

        # Set up the mock for curate function
        mock_curate.return_value = mock_train_val_dfs

        # Ensure output folder exists for testing
        os.makedirs(mock_curator_data["output_folder"], exist_ok=True)

        # Call the function
        run_kpi_curator(
            annotation_folder=mock_curator_data["annotation_folder"],
            agg_annotation=mock_curator_data["agg_annotation"],
            extracted_text_json_folder=mock_curator_data["extracted_text_json_folder"],
            output_folder=mock_curator_data["output_folder"],
            kpi_mapping_file=mock_curator_data["kpi_mapping_file"],
            relevance_file_path=mock_curator_data["relevance_file_path"],
            val_ratio=mock_curator_data["val_ratio"],
            find_new_answerable=mock_curator_data["find_new_answerable"],
            create_unanswerable=mock_curator_data["create_unanswerable"],
        )

        # Get today's date for output file check
        today_date = date.today().strftime("%d-%m-%Y")

        # Expected output file paths
        expected_train_output = os.path.join(
            mock_curator_data["output_folder"], f"train_kpi_data_{today_date}.xlsx"
        )
        expected_val_output = os.path.join(
            mock_curator_data["output_folder"], f"val_kpi_data_{today_date}.xlsx"
        )

        # Assert files were saved
        assert os.path.exists(expected_train_output)
        assert os.path.exists(expected_val_output)

        # Assert logger info messages
        mock_logger.info.assert_any_call("Starting KPI curation process")
        mock_logger.info.assert_any_call(
            f"Train data saved to: {expected_train_output}"
        )
        mock_logger.info.assert_any_call(
            f"Validation data saved to: {expected_val_output}"
        )
        mock_logger.info.assert_any_call("KPI curation completed successfully.")

        # Clean up by removing the created files
        os.remove(expected_train_output)
        os.remove(expected_val_output)

    @patch(
        "src.osc_transformer_presteps.kpi_curator_main.curate",
        side_effect=Exception("Test error"),
    )
    @patch("src.osc_transformer_presteps.kpi_curator_main._logger")
    def test_run_kpi_curator_error(self, mock_logger, mock_curate, mock_curator_data):
        """Test the run_kpi_curator function handling an exception."""

        with pytest.raises(Exception, match="Test error"):
            run_kpi_curator(
                annotation_folder=mock_curator_data["annotation_folder"],
                agg_annotation=mock_curator_data["agg_annotation"],
                extracted_text_json_folder=mock_curator_data[
                    "extracted_text_json_folder"
                ],
                output_folder=mock_curator_data["output_folder"],
                kpi_mapping_file=mock_curator_data["kpi_mapping_file"],
                relevance_file_path=mock_curator_data["relevance_file_path"],
                val_ratio=mock_curator_data["val_ratio"],
                find_new_answerable=mock_curator_data["find_new_answerable"],
                create_unanswerable=mock_curator_data["create_unanswerable"],
            )

        # Assert the logger error message
        mock_logger.error.assert_called_with("Error during KPI curation: Test error")
