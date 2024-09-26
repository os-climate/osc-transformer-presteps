import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_functions import *

@pytest.fixture
def mock_annotation_folder(tmpdir):
    """Fixture that provides a temporary directory for mock annotation files."""
    folder = tmpdir.mkdir("annotation_folder")
    file_path = os.path.join(folder, "test_annotation.xlsx")
    
    df = pd.DataFrame({
        'company': ['CompanyA', 'CompanyB'],
        'source_file': ['fileA.pdf', 'fileB.pdf'],
        'source_page': ['[1, 2]', '[3, 4]'],
        'kpi_id': [1, 2],
        'year': [2021, 2022],
        'answer': ['Yes', 'No'],
        'data_type': ['typeA', 'typeB'],
        'relevant_paragraphs': ['para1', 'para2']
    })
    
    df.to_excel(file_path, index=False, sheet_name='data_ex_in_xls')
    return folder

@pytest.fixture
def mock_kpi_mapping_file(tmpdir):
    """Fixture that provides a temporary KPI mapping CSV file."""
    file = tmpdir.join("kpi_mapping.csv")
    
    df = pd.DataFrame({
        'kpi_id': [1, 2],
        'question': ['What is A?', 'What is B?'],
        'add_year': [True, False],
        'kpi_category': ['typeA, typeB', 'typeB, typeC']
    })
    
    df.to_csv(file, index=False)
    return str(file)

@patch('src.osc_transformer_presteps.kpi_curator_functions._logger')
def test_aggregate_annots(mock_logger, mock_annotation_folder):
    """Test the aggregate_annots function with a valid annotation folder."""
    
    # Call the function
    df = aggregate_annots(str(mock_annotation_folder))
    
    # Assert DataFrame is not empty and has expected columns
    assert not df.empty
    assert all(col in df.columns for col in ["company", "source_file", "source_page", "kpi_id", "year"])
    
    # Assert logger info was called
    mock_logger.info.assert_called_with("Aggregating 1 files.")

@patch('src.osc_transformer_presteps.kpi_curator_functions._logger')
def test_aggregate_annots_invalid(mock_logger, tmpdir):
    """Test aggregate_annots with no valid files."""
    
    # Create an empty annotation folder
    folder = tmpdir.mkdir("empty_annotation_folder")
    
    # Call the function
    df = aggregate_annots(str(folder))
    
    # Assert DataFrame is empty
    assert df.empty
    
    # Assert warning was logged
    mock_logger.warning.assert_called_with(f"No valid annotation files found in {folder}. "
                                           "Make sure the names have 'annotation' in the file names.")

@patch('src.osc_transformer_presteps.kpi_curator_functions._logger')
def test_load_kpi_mapping(mock_logger, mock_kpi_mapping_file):
    """Test the load_kpi_mapping function with a valid KPI mapping file."""
    
    # Call the function
    kpi_mapping, kpi_category, add_year = load_kpi_mapping(mock_kpi_mapping_file)
    
    # Assert the mapping dictionaries and list are correct
    assert kpi_mapping == {1.0: 'What is A?', 2.0: 'What is B?'}
    assert kpi_category == {1: ['typeA', 'typeB'], 2: ['typeB', 'typeC']}
    assert add_year == [1]
    
    # Assert logger info was called
    mock_logger.info.assert_called_with("KPI mapping loaded successfully.")

@patch('src.osc_transformer_presteps.kpi_curator_functions._logger')
def test_clean_annotation(mock_logger, mock_annotation_folder, mock_kpi_mapping_file):
    """Test the clean_annotation function with a valid DataFrame."""
    
    # Load the mock DataFrame
    df = aggregate_annots(str(mock_annotation_folder))
    
    # Call the clean_annotation function
    cleaned_df = clean_annotation(df, mock_kpi_mapping_file)
    
    # Assert the DataFrame is cleaned correctly (no NaNs in required columns, and pages cleaned)
    assert not cleaned_df.empty
    assert all(col in cleaned_df.columns for col in ["company", "source_file", "source_page", "kpi_id", "year"])
    
    # Assert source_file column is cleaned
    assert all(cleaned_df['source_file'].apply(lambda x: x.endswith('.pdf')))
    
    # Assert logger info was called for saving the cleaned data
    mock_logger.info.assert_called()

    # Assert cleaned data is saved
    assert os.path.exists('aggregated_annotation.xlsx')

    # Cleanup created file
    os.remove('aggregated_annotation.xlsx')

@patch('src.osc_transformer_presteps.kpi_curator_functions._logger')
def test_clean_annotation_invalid(mock_logger, mock_annotation_folder, mock_kpi_mapping_file):
    """Test clean_annotation function with incorrect (kpi_id, data_type) pairs."""
    
    # Create a DataFrame with an invalid kpi_id/data_type pair
    df = pd.DataFrame({
        'company': ['CompanyA'],
        'source_file': ['fileA.pdf'],
        'source_page': ['[1, 2]'],
        'kpi_id': [1],
        'year': [2021],
        'answer': ['Yes'],
        'data_type': ['typeC'],  # Invalid data_type for kpi_id 1
        'relevant_paragraphs': ['para1']
    })
    
    # Call the clean_annotation function
    cleaned_df = clean_annotation(df, mock_kpi_mapping_file)
    
    # Assert rows with incorrect kpi_id/data_type pairs are dropped
    assert cleaned_df.empty
    
    # Assert logger debug was called for dropped examples
    mock_logger.debug.assert_called_with("Dropped 1 examples due to incorrect kpi-data_type pair")

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
    expected_output = 'hello world!?'
    assert clean_text(input_text) == expected_output

# Test for the `find_answer_start` function
def test_find_answer_start():
    answer = "2020"
    paragraph = "In the year 2020, something happened."
    expected_start_indices = [11]
    assert find_answer_start(answer, paragraph) == expected_start_indices

# Test for the `find_closest_paragraph` function
def test_find_closest_paragraph():
    paragraphs = ["Paragraph 1 about KPI", "Paragraph 2 about something else"]
    clean_rel_paragraph = "paragraph 1"
    clean_answer = "KPI"
    closest_paragraph = find_closest_paragraph(paragraphs, clean_rel_paragraph, clean_answer)
    
    assert closest_paragraph == "Paragraph 1 about KPI"

@patch("src.osc_transformer_presteps.kpi_curator_functions.clean_text")
@patch("src.osc_transformer_presteps.kpi_curator_functions.find_closest_paragraph")
@patch("src.osc_transformer_presteps.kpi_curator_functions.find_answer_start")
def test_return_full_paragraph(mock_find_answer_start, mock_find_closest_paragraph, mock_clean_text):
    # Mocking the clean_text function
    mock_clean_text.side_effect = lambda x: x

    # Mocking return values for find_closest_paragraph and find_answer_start
    mock_find_closest_paragraph.return_value = "closest paragraph"
    mock_find_answer_start.return_value = [10]

    # Input data
    json_dict = {
        "sample_file": {
            "0": ["paragraph 1", "paragraph 2"]
        }
    }
    r = pd.Series({
        "answer": "sample answer",
        "relevant_paragraphs": "relevant paragraph",
        "source_file": "sample_file",
        "source_page": 1
    })

    clean_rel_par, clean_answer, ans_start = return_full_paragraph(r, json_dict)

    # Assertions
    assert clean_rel_par == "closest paragraph"
    assert clean_answer == "sample answer"
    assert ans_start == [10]

@patch("src.osc_transformer_presteps.kpi_curator_functions.clean_text")
@patch("src.osc_transformer_presteps.kpi_curator_functions.find_answer_start")
def test_find_extra_answerable(mock_find_answer_start, mock_clean_text):
    # Mocking the clean_text function
    mock_clean_text.side_effect = lambda x: x

    # Mocking find_answer_start return value
    mock_find_answer_start.return_value = [5]

    # Input data
    df = pd.DataFrame({
        "source_file": ["sample_file"],
        "source_page": [2],
        "answer": ["sample answer"],
        "kpi_id": [5]
    })

    json_dict = {
        "sample_file": {
            "1": ["paragraph 1", "paragraph 2"]
        }
    }

    new_positive_df = find_extra_answerable(df, json_dict)

    # Assertions
    assert len(new_positive_df) == 1
    assert new_positive_df.iloc[0]["source_file"] == "sample_file"

@patch("src.osc_transformer_presteps.kpi_curator_functions.return_full_paragraph")
@patch("src.osc_transformer_presteps.kpi_curator_functions.find_extra_answerable")
def test_create_answerable(mock_find_extra_answerable, mock_return_full_paragraph):
    # Mocking return_full_paragraph function
    mock_return_full_paragraph.side_effect = lambda r, json_dict: ("paragraph", "answer", [5])

    # Mocking find_extra_answerable return value
    mock_find_extra_answerable.return_value = pd.DataFrame({
        "source_file": ["sample_file"],
        "paragraph": ["extra paragraph"],
        "question": ["sample question"],
        "answer": ["sample answer"],
        "answer_start": [[10]]
    })

    # Input data
    df = pd.DataFrame({
        "source_file": ["sample_file"],
        "relevant_paragraphs": ["relevant paragraph"],
        "answer": ["sample answer"],
        "answer_start": [[]]
    })

    json_dict = {
        "sample_file": {
            "1": ["paragraph 1", "paragraph 2"]
        }
    }

    pos_df = create_answerable(df, json_dict, find_new_answerable=True)

    # Assertions
    assert len(pos_df) == 2
    assert "extra paragraph" in pos_df["paragraph"].values

def test_filter_relevant_examples():
    # Input data
    annotation_df = pd.DataFrame({
        "source_file": ["sample_file"],
        "source_page": [2],
        "kpi_id": [5],
        "question": ["sample question"],
        "answer": ["sample answer"],
        "relevant_paragraph": ["relevant paragraph"]
    })

    relevant_df = pd.DataFrame({
        "pdf_name": ["sample_file"],
        "paragraph_relevance_flag": [1],
        "kpi_id": [5],
        "paragraph": ["relevant paragraph"],
        "answer": ["sample answer"],
        "question": ["sample question"]
    })

    filtered_df = filter_relevant_examples(annotation_df, relevant_df)

    # Assertions
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]["paragraph"] == "relevant paragraph"

@patch("src.osc_transformer_presteps.kpi_curator_functions.pd.read_excel")
@patch("src.osc_transformer_presteps.kpi_curator_functions.clean_text")
@patch("src.osc_transformer_presteps.kpi_curator_functions.filter_relevant_examples")
def test_create_unanswerable(mock_filter_relevant_examples, mock_clean_text, mock_read_excel):
    # Mocking read_excel function to return a dummy relevant DataFrame
    mock_read_excel.return_value = pd.DataFrame({
        "page": [1],
        "pdf_name": ["sample_file.pdf"],
        "unique_paragraph_id": [101],
        "paragraph": ["This is a relevant paragraph."],
        "kpi_id": [5],
        "question": ["Sample KPI question?"],
        "paragraph_relevance_flag": [1],
        "paragraph_relevance_score(for_label=1)": [0.9]
    })

    # Mocking clean_text to return the same paragraph
    mock_clean_text.side_effect = lambda x: x

    # Mocking filter_relevant_examples to return a filtered DataFrame
    mock_filter_relevant_examples.return_value = pd.DataFrame({
        "pdf_name": ["sample_file.pdf"],
        "paragraph": ["This is a relevant paragraph."],
        "question": ["Sample KPI question?"],
        "answer": [""],
        "answer_start": [[]]
    })

    # Sample annotation DataFrame
    annotation_df = pd.DataFrame({
        "source_file": ["sample_file.pdf"],
        "page": [1],
        "kpi_id": [5],
        "question": ["Sample KPI question?"],
        "answer": ["Sample answer"],
        "relevant_paragraph": ["This is a relevant paragraph."]
    })

    relevant_text_path = "dummy_relevant_text_path.xlsx"

    # Run the function
    result_df = create_unanswerable(annotation_df, relevant_text_path)

    # Assertions
    assert len(result_df) == 1
    assert result_df.iloc[0]["source_file"] == "sample_file.pdf"
    assert result_df.iloc[0]["answer"] == ""
    assert result_df.iloc[0]["paragraph"] == "This is a relevant paragraph."


@patch("src.osc_transformer_presteps.kpi_curator_functions.read_agg")
@patch("src.osc_transformer_presteps.kpi_curator_functions.clean")
@patch("src.osc_transformer_presteps.kpi_curator_functions.create_answerable")
@patch("src.osc_transformer_presteps.kpi_curator_functions.create_unanswerable")
@patch("src.osc_transformer_presteps.kpi_curator_functions.os.listdir")
@patch("src.osc_transformer_presteps.kpi_curator_functions.json.load")
def test_curate(mock_json_load, mock_listdir, mock_create_unanswerable, mock_create_answerable, mock_clean, mock_read_agg):
    # Mocking read_agg to return a dummy DataFrame
    mock_read_agg.return_value = pd.DataFrame({
        "data_type": ['TEXT'],
        "source_file": ["sample_file.pdf"],
        "kpi_id": [5],
        "relevant_paragraphs": ["Relevant paragraph"],
        "answer": ["Sample answer"]
    })

    # Mocking clean to return the same DataFrame
    mock_clean.side_effect = lambda df, kpi_mapping_file: df

    # Mocking listdir to return a list of JSON files
    mock_listdir.return_value = ["sample_file.json"]

    # Mocking json.load to return a sample JSON dictionary
    mock_json_load.return_value = {
        "1": ["This is a paragraph from the JSON file."]
    }

    # Mocking create_answerable to return a dummy DataFrame of answerable examples
    mock_create_answerable.return_value = pd.DataFrame({
        "source_file": ["sample_file.pdf"],
        "paragraph": ["This is an answerable paragraph."],
        "question": ["Sample KPI question?"],
        "answer": ["Sample answer"],
        "answer_start": [[0]]
    })

    # Mocking create_unanswerable to return a dummy DataFrame of unanswerable examples
    mock_create_unanswerable.return_value = pd.DataFrame({
        "source_file": ["sample_file.pdf"],
        "paragraph": ["This is an unanswerable paragraph."],
        "question": ["Sample KPI question?"],
        "answer": [""],
        "answer_start": [[]]
    })

    # Call the curate function
    train_df, val_df = curate(
        annotation_folder="dummy_annotation_folder",
        agg_annotation="dummy_agg_annotation",
        extracted_text_json_folder="dummy_json_folder",
        kpi_mapping_file="dummy_kpi_mapping_file",
        relevance_file_path="dummy_relevance_file.xlsx",
        val_ratio=0.2
    )

    # Assertions for training and validation split
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(train_df) + len(val_df) == 2  # 1 answerable + 1 unanswerable example
