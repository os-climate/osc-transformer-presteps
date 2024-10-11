import pandas as pd
from unittest.mock import patch
from src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_example_creation import (
    create_unanswerable,
    filter_relevant_examples,
    create_answerable,
    find_extra_answerable,
    return_full_paragraph,
)


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.clean_text"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.find_closest_paragraph"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.find_answer_start"
)
def test_return_full_paragraph(
    mock_find_answer_start, mock_find_closest_paragraph, mock_clean_text
):
    # Mocking the clean_text function
    mock_clean_text.side_effect = lambda x: x

    # Mocking return values for find_closest_paragraph and find_answer_start
    mock_find_closest_paragraph.return_value = "closest paragraph"
    mock_find_answer_start.return_value = [10]

    # Input data
    json_dict = {"sample_file": {"0": ["paragraph 1", "paragraph 2"]}}
    r = pd.Series(
        {
            "answer": "sample answer",
            "relevant_paragraphs": "relevant paragraph",
            "source_file": "sample_file",
            "source_page": 1,
        }
    )

    clean_rel_par, clean_answer, ans_start = return_full_paragraph(r, json_dict)

    # Assertions
    assert clean_rel_par == "closest paragraph"
    assert clean_answer == "sample answer"
    assert ans_start == [10]


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.clean_text"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.example_creation.find_answer_start"
)
def test_find_extra_answerable(mock_find_answer_start, mock_clean_text):
    # Mocking the clean_text function
    mock_clean_text.side_effect = lambda x: x

    # Mocking find_answer_start return value
    mock_find_answer_start.return_value = [5]

    # Input data
    df = pd.DataFrame(
        {
            "source_file": ["sample_file"],
            "source_page": [2],
            "answer": ["sample answer"],
            "kpi_id": [5],
        }
    )

    json_dict = {"sample_file": {"1": ["paragraph 1", "paragraph 2"]}}

    new_positive_df = find_extra_answerable(df, json_dict)

    # Assertions
    assert len(new_positive_df) == 1
    assert new_positive_df.iloc[0]["source_file"] == "sample_file"


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.example_creation.return_full_paragraph"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.example_creation.find_extra_answerable"
)
def test_create_answerable(mock_find_extra_answerable, mock_return_full_paragraph):
    # Mocking return_full_paragraph function
    mock_return_full_paragraph.side_effect = lambda r, json_dict: (
        "paragraph",
        "answer",
        [5],
    )

    # Mocking find_extra_answerable return value
    mock_find_extra_answerable.return_value = pd.DataFrame(
        {
            "source_file": ["sample_file"],
            "paragraph": ["extra paragraph"],
            "question": ["sample question"],
            "answer": ["sample answer"],
            "answer_start": [[10]],
        }
    )

    # Input data
    df = pd.DataFrame(
        {
            "source_file": ["sample_file"],
            "relevant_paragraphs": ["relevant paragraph"],
            "answer": ["sample answer"],
            "answer_start": [[]],
        }
    )

    json_dict = {"sample_file": {"1": ["paragraph 1", "paragraph 2"]}}

    pos_df = create_answerable(df, json_dict, find_new_answerable=True)

    # Assertions
    assert len(pos_df) == 2
    assert "extra paragraph" in pos_df["paragraph"].values


def test_filter_relevant_examples():
    # Input data
    annotation_df = pd.DataFrame(
        {
            "source_file": ["sample_file"],
            "source_page": [2],
            "kpi_id": [5],
            "question": ["sample question"],
            "answer": ["sample answer"],
            "relevant_paragraph": ["relevant paragraph"],
        }
    )

    relevant_df = pd.DataFrame(
        {
            "pdf_name": ["sample_file"],
            "paragraph_relevance_flag": [1],
            "kpi_id": [5],
            "paragraph": ["relevant paragraph"],
            "answer": ["sample answer"],
            "question": ["sample question"],
        }
    )

    filtered_df = filter_relevant_examples(annotation_df, relevant_df)

    # Assertions
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]["paragraph"] == "relevant paragraph"


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.data_processing.clean_text"
)
@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.example_creation.filter_relevant_examples"
)
def test_create_unanswerable(
    mock_filter_relevant_examples, mock_clean_text, mock_read_excel
):
    # Mocking read_excel function to return a dummy relevant DataFrame
    mock_read_excel.return_value = pd.DataFrame(
        {
            "page": [1],
            "pdf_name": ["sample_file.pdf"],
            "unique_paragraph_id": [101],
            "paragraph": ["This is a relevant paragraph."],
            "kpi_id": [5],
            "question": ["Sample KPI question?"],
            "paragraph_relevance_flag": [1],
            "paragraph_relevance_score(for_label=1)": [0.9],
        }
    )

    # Mocking clean_text to return the same paragraph
    mock_clean_text.side_effect = lambda x: x

    # Mocking filter_relevant_examples to return a filtered DataFrame
    mock_filter_relevant_examples.return_value = pd.DataFrame(
        {
            "pdf_name": ["sample_file.pdf"],
            "paragraph": ["This is a relevant paragraph."],
            "question": ["Sample KPI question?"],
            "answer": [""],
            "answer_start": [[]],
        }
    )

    # Sample annotation DataFrame
    annotation_df = pd.DataFrame(
        {
            "source_file": ["sample_file.pdf"],
            "page": [1],
            "kpi_id": [5],
            "question": ["Sample KPI question?"],
            "answer": ["Sample answer"],
            "relevant_paragraph": ["This is a relevant paragraph."],
        }
    )

    relevant_text_path = "dummy_relevant_text_path.xlsx"

    # Run the function
    result_df = create_unanswerable(annotation_df, relevant_text_path)

    # Assertions
    assert len(result_df) == 1
    assert result_df.iloc[0]["source_file"] == "sample_file.pdf"
    assert result_df.iloc[0]["answer"] == ""
    assert result_df.iloc[0]["paragraph"] == "This is a relevant paragraph."
