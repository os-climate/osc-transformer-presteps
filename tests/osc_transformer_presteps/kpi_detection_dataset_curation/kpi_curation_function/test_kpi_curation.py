import pandas as pd
from unittest.mock import patch
from src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_curation import (
    curate,
)


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.read_agg"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.clean"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.example_creation.create_answerable"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.example_creation.create_unanswerable"
)
def test_curate(
    mock_json_load,
    mock_listdir,
    mock_create_unanswerable,
    mock_create_answerable,
    mock_clean,
    mock_read_agg,
):
    # Mocking read_agg to return a dummy DataFrame
    mock_read_agg.return_value = pd.DataFrame(
        {
            "data_type": ["TEXT"],
            "source_file": ["sample_file.pdf"],
            "kpi_id": [5],
            "relevant_paragraphs": ["Relevant paragraph"],
            "answer": ["Sample answer"],
        }
    )

    # Mocking clean to return the same DataFrame
    mock_clean.side_effect = lambda df, kpi_mapping_file: df

    # Mocking listdir to return a list of JSON files
    mock_listdir.return_value = ["sample_file.json"]

    # Mocking json.load to return a sample JSON dictionary
    mock_json_load.return_value = {"1": ["This is a paragraph from the JSON file."]}

    # Mocking create_answerable to return a dummy DataFrame of answerable examples
    mock_create_answerable.return_value = pd.DataFrame(
        {
            "source_file": ["sample_file.pdf"],
            "paragraph": ["This is an answerable paragraph."],
            "question": ["Sample KPI question?"],
            "answer": ["Sample answer"],
            "answer_start": [[0]],
        }
    )

    # Mocking create_unanswerable to return a dummy DataFrame of unanswerable examples
    mock_create_unanswerable.return_value = pd.DataFrame(
        {
            "source_file": ["sample_file.pdf"],
            "paragraph": ["This is an unanswerable paragraph."],
            "question": ["Sample KPI question?"],
            "answer": [""],
            "answer_start": [[]],
        }
    )

    # Call the curate function
    train_df, val_df = curate(
        annotation_folder="dummy_annotation_folder",
        agg_annotation="dummy_agg_annotation",
        extracted_text_json_folder="dummy_json_folder",
        kpi_mapping_file="dummy_kpi_mapping_file",
        relevance_file_path="dummy_relevance_file.xlsx",
        val_ratio=0.2,
    )

    # Assertions for training and validation split
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(train_df) + len(val_df) == 2  # 1 answerable + 1 unanswerable example
