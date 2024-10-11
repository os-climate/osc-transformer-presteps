import pytest
import pandas as pd
import os
from unittest.mock import patch
from src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_data_processing import (
    aggregate_annots,
    clean_annotation,
    find_closest_paragraph,
    find_answer_start,
    clean_text,
    clean,
)


@pytest.fixture
def mock_annotation_folder(tmpdir):
    """Fixture that provides a temporary directory for mock annotation files."""
    folder = tmpdir.mkdir("annotation_folder")
    file_path = os.path.join(folder, "test_annotation.xlsx")

    df = pd.DataFrame(
        {
            "company": ["CompanyA", "CompanyB"],
            "source_file": ["fileA.pdf", "fileB.pdf"],
            "source_page": ["[1, 2]", "[3, 4]"],
            "kpi_id": [1, 2],
            "year": [2021, 2022],
            "answer": ["Yes", "No"],
            "data_type": ["typeA", "typeB"],
            "relevant_paragraphs": ["para1", "para2"],
        }
    )

    df.to_excel(file_path, index=False, sheet_name="data_ex_in_xls")
    return folder


@pytest.fixture
def mock_kpi_mapping_file(tmpdir):
    """Fixture that provides a temporary KPI mapping CSV file."""
    file = tmpdir.join("kpi_mapping.csv")

    df = pd.DataFrame(
        {
            "kpi_id": [1, 2],
            "question": ["What is A?", "What is B?"],
            "add_year": [True, False],
            "kpi_category": ["typeA, typeB", "typeB, typeC"],
        }
    )

    df.to_csv(file, index=False)
    return str(file)


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.example_creation._logger"
)
def test_aggregate_annots(mock_logger, mock_annotation_folder):
    """Test the aggregate_annots function with a valid annotation folder."""

    # Call the function
    df = aggregate_annots(str(mock_annotation_folder))

    # Assert DataFrame is not empty and has expected columns
    assert not df.empty
    assert all(
        col in df.columns
        for col in ["company", "source_file", "source_page", "kpi_id", "year"]
    )

    # Assert logger info was called
    mock_logger.info.assert_called_with("Aggregating 1 files.")


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.example_creation._logger"
)
def test_aggregate_annots_invalid(mock_logger, tmpdir):
    """Test aggregate_annots with no valid files."""

    # Create an empty annotation folder
    folder = tmpdir.mkdir("empty_annotation_folder")

    # Call the function
    df = aggregate_annots(str(folder))

    # Assert DataFrame is empty
    assert df.empty

    # Assert warning was logged
    mock_logger.warning.assert_called_with(
        f"No valid annotation files found in {folder}. "
        "Make sure the names have 'annotation' in the file names."
    )


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.example_creation._logger"
)
def test_clean_annotation(mock_logger, mock_annotation_folder, mock_kpi_mapping_file):
    """Test the clean_annotation function with a valid DataFrame."""

    # Load the mock DataFrame
    df = aggregate_annots(str(mock_annotation_folder))

    # Call the clean_annotation function
    cleaned_df = clean_annotation(df, mock_kpi_mapping_file)

    # Assert the DataFrame is cleaned correctly (no NaNs in required columns, and pages cleaned)
    assert not cleaned_df.empty
    assert all(
        col in cleaned_df.columns
        for col in ["company", "source_file", "source_page", "kpi_id", "year"]
    )

    # Assert source_file column is cleaned
    assert all(cleaned_df["source_file"].apply(lambda x: x.endswith(".pdf")))

    # Assert logger info was called for saving the cleaned data
    mock_logger.info.assert_called()

    # Assert cleaned data is saved
    assert os.path.exists("aggregated_annotation.xlsx")

    # Cleanup created file
    os.remove("aggregated_annotation.xlsx")


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.example_creation._logger"
)
def test_clean_annotation_invalid(
    mock_logger, mock_annotation_folder, mock_kpi_mapping_file
):
    """Test clean_annotation function with incorrect (kpi_id, data_type) pairs."""

    # Create a DataFrame with an invalid kpi_id/data_type pair
    df = pd.DataFrame(
        {
            "company": ["CompanyA"],
            "source_file": ["fileA.pdf"],
            "source_page": ["[1, 2]"],
            "kpi_id": [1],
            "year": [2021],
            "answer": ["Yes"],
            "data_type": ["typeC"],  # Invalid data_type for kpi_id 1
            "relevant_paragraphs": ["para1"],
        }
    )

    # Call the clean_annotation function
    cleaned_df = clean_annotation(df, mock_kpi_mapping_file)

    # Assert rows with incorrect kpi_id/data_type pairs are dropped
    assert cleaned_df.empty

    # Assert logger debug was called for dropped examples
    mock_logger.debug.assert_called_with(
        "Dropped 1 examples due to incorrect kpi-data_type pair"
    )


# Test for the `clean` function
def test_clean():
    # Mock data
    data = {
        "kpi_id": [1.0, 2.0, 3.0],
        "year": [2020, 2021, 2022],
        "relevant_paragraphs": ["Paragraph 1", "Paragraph 2", None],
        "answer": ["Answer 1", None, "Answer 3"],
    }
    df = pd.DataFrame(data)

    # Mock KPI mapping
    kpi_mapping_file = "mock_kpi_mapping.csv"

    # Mock load_kpi_mapping return
    def mock_load_kpi_mapping(file):
        return {1.0: "What is KPI?"}, {}, {1.0}

    # Replace with a real call to the `clean` function once everything is ready
    cleaned_df = clean(df, kpi_mapping_file)

    assert cleaned_df.shape[0] == 1
    assert cleaned_df["question"].iloc[0] == "What is KPI? in year 2020?"


# Test for the `clean_text` function
def test_clean_text():
    input_text = "“Hello World!?”\n"
    expected_output = "hello world!?"
    assert clean_text(input_text) == expected_output


# Test for the `find_closest_paragraph` function
def test_find_closest_paragraph():
    paragraphs = ["Paragraph 1 about KPI", "Paragraph 2 about something else"]
    clean_rel_paragraph = "paragraph 1"
    clean_answer = "KPI"
    closest_paragraph = find_closest_paragraph(
        paragraphs, clean_rel_paragraph, clean_answer
    )

    assert closest_paragraph == "Paragraph 1 about KPI"


# Test for the `find_answer_start` function
def test_find_answer_start():
    answer = "2020"
    paragraph = "In the year 2020, something happened."
    expected_start_indices = [11]
    assert find_answer_start(answer, paragraph) == expected_start_indices
