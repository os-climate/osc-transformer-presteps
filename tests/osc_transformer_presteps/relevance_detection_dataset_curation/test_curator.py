"""Module to test the curator.py."""

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

# Define the common current working directory
cwd = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def mock_curator_data():
    """Mimics the curator settings data."""
    return {
        "annotation_folder": cwd / "test_annotations_sliced.xlsx",
        "extract_json": cwd / "json_files" / "Test.json",
        "kpi_mapping_path": cwd / "kpi_mapping_sliced.csv",
        "neg_pos_ratio": 1,
        "create_neg_samples": True,
    }


@pytest.fixture
def curator_object(mock_curator_data):
    """Fixture to create a fixed Curator object with the given mocked settings data."""
    return Curator(
        annotation_folder=str(mock_curator_data["annotation_folder"]),
        extract_json=mock_curator_data["extract_json"],
        kpi_mapping_path=str(mock_curator_data["kpi_mapping_path"]),
        neg_pos_ratio=1,
        create_neg_samples=True,
    )


def annotation_to_df(filepath: Path) -> pd.Series:
    """Load curation data and return the first row."""
    df = pd.read_excel(filepath, sheet_name="data_ex_in_xls")
    df["annotation_file"] = os.path.basename(filepath)

    # Update the "source_page" column
    df["source_page"] = df["source_page"].apply(
        lambda x: [str(p - 1) for p in ast.literal_eval(x)]
    )

    return df.iloc[0]


class TestAnnotationData:
    """Class to collect tests for the AnnotationData class."""

    def test_annotation_data_valid_paths(self, mock_curator_data):
        """A test to validate that all mentioned paths are ok."""
        data = AnnotationData(
            annotation_folder=mock_curator_data["annotation_folder"],
            extract_json=mock_curator_data["extract_json"],
            kpi_mapping_path=mock_curator_data["kpi_mapping_path"],
        )
        assert data.annotation_folder == cwd / "test_annotations_sliced.xlsx"
        assert data.extract_json == cwd / "json_files" / "Test.json"
        assert data.kpi_mapping_path == cwd / "kpi_mapping_sliced.csv"

    def test_annotation_data_invalid_paths(self):
        """A test to validate that wrong paths will raise an error."""
        with pytest.raises(ValidationError):
            AnnotationData(
                annotation_folder="/invalid/path",
                extract_json="/path/to/file.json",
                kpi_mapping_path="/path/to/kpi_mapping_sliced.csv",
            )


class TestCurator:
    """Class to collect tests for the curator module."""

    @pytest.mark.parametrize(
        "input_text, expected_output",
        [
            ("This is a test sentence.", "This is a test sentence."),
            (
                "This\\ sentence\\ has\\ extra\\ backslashes.",
                "This sentence has extra backslashes.",
            ),
            (None, ""),
            (float("nan"), ""),
            ("", ""),
        ],
    )
    def test_clean_text(self, curator_object, input_text, expected_output):
        """A test where we test multiple test sentences."""
        cleaned_text = curator_object.clean_text(input_text)
        assert cleaned_text == expected_output

    def test_clean_text_basic(self, curator_object):
        """A test where test sentence is already clean."""
        cleaned_text = curator_object.clean_text("This is a test sentence.")
        assert cleaned_text == "This is a test sentence."

    def test_clean_text_with_fancy_quotes(self, curator_object):
        """A test on cleaning text with special quotes."""
        text_with_fancy_quotes = "“This is a test sentence.”"
        cleaned_text = curator_object.clean_text(text_with_fancy_quotes)
        assert cleaned_text == '"This is a test sentence."'

    def test_clean_text_with_newlines_and_tabs(self, curator_object):
        """A test on removing new lines and tabs."""
        text_with_newlines_tabs = "This\nis\ta\ttest\nsentence."
        cleaned_text = curator_object.clean_text(text_with_newlines_tabs)
        assert cleaned_text == "This is a test sentence."

    def test_clean_text_removing_specific_terms(self, curator_object):
        """A test on removing specific terms."""
        text_with_boe = "This sentence contains the term BOE."
        cleaned_text = curator_object.clean_text(text_with_boe)
        assert cleaned_text == "This sentence contains the term ."

    def test_clean_text_removing_invalid_escape_sequence(self, curator_object):
        """A test on removing invalid escape sequence."""
        text_with_invalid_escape_sequence = (
            "This sentence has an invalid escape sequence: \x9d"
        )
        cleaned_text = curator_object.clean_text(text_with_invalid_escape_sequence)
        assert cleaned_text == "This sentence has an invalid escape sequence: "

    def test_clean_text_removing_extra_backslashes(self, curator_object):
        """A test on removing extra  backslashes."""
        text_with_extra_backslashes = "This\\ sentence\\ has\\ extra\\ backslashes."
        cleaned_text = curator_object.clean_text(text_with_extra_backslashes)
        assert cleaned_text == "This sentence has extra backslashes."

    def test_create_pos_examples_correct_samples(self, curator_object):
        """A test where we create positive examples via curator."""
        row = annotation_to_df(Path(curator_object.annotation_folder))
        pos_example = curator_object.create_pos_examples(row)
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
        """A test for positive examples where we have a json filename mismatch."""
        curator = Curator(
            annotation_folder=str(mock_curator_data["annotation_folder"]),
            extract_json=cwd / "json_files" / "Test_issue.json",
            kpi_mapping_path=str(mock_curator_data["kpi_mapping_path"]),
            neg_pos_ratio=1,
            create_neg_samples=True,
        )
        row = annotation_to_df(Path(curator.annotation_folder))
        pos_example = curator.create_pos_examples(row)
        assert pos_example == [""]

    def test_create_neg_examples_correct_samples(self, curator_object):
        """A test where we create negative examples via curator."""
        row = annotation_to_df(Path(curator_object.annotation_folder))
        neg_example = curator_object.create_neg_examples(row)
        assert neg_example == ["Shell 2019 Sustainability Report"]

    def test_create_neg_examples_json_filename_mismatch(self, mock_curator_data):
        """A test for negative examples where we have a json filename mismatch."""
        curator = Curator(
            annotation_folder=str(mock_curator_data["annotation_folder"]),
            extract_json=cwd / "json_files" / "Test_issue.json",
            kpi_mapping_path=str(mock_curator_data["kpi_mapping_path"]),
            neg_pos_ratio=1,
            create_neg_samples=True,
        )
        row = annotation_to_df(Path(curator.annotation_folder))
        neg_example = curator.create_neg_examples(row)
        assert neg_example == [""]

    def test_create_curator_df(self, curator_object):
        """A test to create the final dataframe output."""
        actual_df = pd.read_csv(cwd / "Actual_curator.csv")
        output = curator_object.create_curator_df()

        output_file_path = cwd / "Expected.csv"
        output.to_csv(output_file_path, index=False)
        expected_df = pd.read_csv(output_file_path)

        assert actual_df.equals(expected_df)
        output_file_path.unlink(missing_ok=True)
