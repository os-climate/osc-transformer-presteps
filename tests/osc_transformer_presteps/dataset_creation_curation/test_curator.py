import os
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from osc_transformer_presteps.dataset_creation_curation.curator import (
    AnnotationData,
    Curator,
)
import ast


@pytest.fixture
def mock_curator_data():
    return {
        "annotation_folder": "test_annotations_sliced.xlsx",
        "extract_json": "Test.json",
        "kpi_mapping_path": "kpi_mapping_sliced.csv",
        "neg_pos_ratio": 1,
        "create_neg_samples": True,
    }


@pytest.fixture
def curator_instance(mock_curator_data):
    cwd = Path.cwd()
    return Curator(
        annotation_folder=cwd / mock_curator_data["annotation_folder"],
        extract_json=cwd / mock_curator_data["extract_json"],
        kpi_mapping_path=cwd / mock_curator_data["kpi_mapping_path"],
        neg_pos_ratio=1,
        create_neg_samples=True,
    )


def annotation_to_df(filepath: Path) -> pd.Series:
    df = pd.read_excel(filepath, sheet_name="data_ex_in_xls")
    df["annotation_file"] = os.path.basename(filepath)

    # Update the "source_page" column
    df["source_page"] = df["source_page"].apply(
        lambda x: [str(p - 1) for p in ast.literal_eval(x)]
    )

    return df.iloc[0]


class TestAnnotationData:
    def test_annotation_data_valid_paths(self, mock_curator_data):
        cwd = Path.cwd()
        data = AnnotationData(
            annotation_folder=cwd / mock_curator_data["annotation_folder"],
            extract_json=cwd / mock_curator_data["extract_json"],
            kpi_mapping_path=cwd / mock_curator_data["kpi_mapping_path"],
        )
        assert data.annotation_folder == cwd / "test_annotations_sliced.xlsx"
        assert data.extract_json == cwd / "Test.json"
        assert data.kpi_mapping_path == cwd / "kpi_mapping_sliced.csv"

    def test_annotation_data_invalid_paths(self):
        with pytest.raises(ValidationError):
            AnnotationData(
                annotation_folder="/invalid/path",
                extract_json="/path/to/file.json",
                kpi_mapping_path="/path/to/kpi_mapping_sliced.csv",
            )


class TestCurator:
    def test_clean_text_basic(self, curator_instance):
        cleaned_text = curator_instance.clean_text("This is a test sentence.")
        assert cleaned_text == "This is a test sentence."

    def test_clean_text_with_fancy_quotes(self, curator_instance):
        text_with_fancy_quotes = "“This is a test sentence.”"
        cleaned_text = curator_instance.clean_text(text_with_fancy_quotes)
        assert cleaned_text == '"This is a test sentence."'

    def test_clean_text_with_newlines_and_tabs(self, curator_instance):
        text_with_newlines_tabs = "This\nis\ta\ttest\nsentence."
        cleaned_text = curator_instance.clean_text(text_with_newlines_tabs)
        assert cleaned_text == "This is a test sentence."

    def test_clean_text_removing_specific_terms(self, curator_instance):
        text_with_boe = "This sentence contains the term BOE."
        cleaned_text = curator_instance.clean_text(text_with_boe)
        assert cleaned_text == "This sentence contains the term ."

    def test_clean_text_removing_invalid_escape_sequence(self, curator_instance):
        text_with_invalid_escape_sequence = (
            "This sentence has an invalid escape sequence: \x9d"
        )
        cleaned_text = curator_instance.clean_text(text_with_invalid_escape_sequence)
        assert cleaned_text == "This sentence has an invalid escape sequence: "

    def test_clean_text_removing_extra_backslashes(self, curator_instance):
        text_with_extra_backslashes = "This\\ sentence\\ has\\ extra\\ backslashes."
        cleaned_text = curator_instance.clean_text(text_with_extra_backslashes)
        assert cleaned_text == "This sentence has extra backslashes."

    def test_create_pos_examples_correct_samples(self, curator_instance):
        row = annotation_to_df(curator_instance.annotation_folder)
        pos_example = curator_instance.create_pos_examples(row)
        expected_pos_example = [
            "We continue to work towards delivering on our Net Carbon Footprint ambition to "
            "cut the intensity of the greenhouse gas emissions of the energy products we sell"
            " by about 50% by 2050, and 20% by 2035 compared to our 2016 levels, in step with "
            "society as it moves towards meeting the goals of the Paris Agreement. In 2019, "
            "we set shorter-term targets for 2021 of 2-3% lower than our 2016 baseline Net Carbon "
            "Footprint. In early 2020, we set a Net Carbon Footprint target for 2022 of 3-4% lower "
            "than our 2016 baseline. We will continue to evolve our approach over time."
        ]
        assert pos_example == expected_pos_example

    def test_create_pos_examples_json_filename_mismatch(self, mock_curator_data):
        cwd = Path.cwd()
        curator = Curator(
            annotation_folder=cwd / mock_curator_data["annotation_folder"],
            extract_json=cwd / "Test_another.json",
            kpi_mapping_path=cwd / mock_curator_data["kpi_mapping_path"],
            neg_pos_ratio=1,
            create_neg_samples=True,
        )
        row = annotation_to_df(curator.annotation_folder)
        pos_example = curator.create_pos_examples(row)
        assert pos_example == [""]

    def test_create_neg_examples_correct_samples(self, curator_instance):
        row = annotation_to_df(curator_instance.annotation_folder)
        neg_example = curator_instance.create_neg_examples(row)
        assert neg_example == ["Shell 2019 Sustainability Report"]

    def test_create_neg_examples_json_filename_mismatch(self, mock_curator_data):
        cwd = Path.cwd()
        curator = Curator(
            annotation_folder=cwd / mock_curator_data["annotation_folder"],
            extract_json=cwd / "Test_another.json",
            kpi_mapping_path=cwd / mock_curator_data["kpi_mapping_path"],
            neg_pos_ratio=1,
            create_neg_samples=True,
        )
        row = annotation_to_df(curator.annotation_folder)
        neg_example = curator.create_neg_examples(row)
        assert neg_example == [""]
