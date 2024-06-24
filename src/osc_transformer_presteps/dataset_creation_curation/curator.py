"""Python Script for Curation."""
import ast
import json
import math
import os
import random
import re
from pathlib import Path
from typing import List, Union

import pandas as pd
from pydantic import BaseModel, FilePath


class AnnotationData(BaseModel):
    """Pydantic model for annotation data."""

    annotation_folder: FilePath
    extract_json: FilePath
    kpi_mapping_path: FilePath


class Curator:
    """
    A data curator component responsible for creating table and text training data based on annotated data.

    Args:
        annotation_folder (str): path to the folder containing annotation files
        extract_json (str): path to the JSON file containing extracted content
        kpi_mapping_path (str): path to KPI Mapping csv
        neg_pos_ratio (int): ratio of negative to positive examples
        create_neg_samples (bool): whether to create negative samples
    """

    def __init__(
            self,
            annotation_folder: str,
            extract_json: Path,
            kpi_mapping_path: str,
            neg_pos_ratio: int = 1,
            create_neg_samples: bool = False,
    ) -> None:
        """Initialize the constructor for Curator object."""
        self.annotation_folder = annotation_folder
        self.extract_json = extract_json
        self.json_file_name = os.path.basename(extract_json).replace("_output", "")
        self.kpi_mapping_path = kpi_mapping_path
        self.neg_pos_ratio = neg_pos_ratio
        self.create_neg_samples = create_neg_samples

        self.pdf_content = self.load_pdf_content()

    def load_pdf_content(self) -> dict:
        """
        Load PDF content from the JSON file specified by `extract_json`.

        Reads the content of the JSON file and returns it as a dictionary.

        Returns:
            dict: A dictionary containing the loaded JSON data.

        Raises:
            FileNotFoundError: If the JSON file specified by `extract_json` does not exist.
            JSONDecodeError: If the content of the JSON file cannot be decoded.

        Note:
            This method assumes `extract_json` is a `Path` object pointing to a valid JSON file.
        """
        with self.extract_json.open() as f:
            return json.load(f)

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean a sentence by removing unwanted characters and control characters.

        Args:
            text (str): The text to be cleaned.

        Returns:
            str: The cleaned text.
        """
        if text is None or isinstance(text, float) and math.isnan(text) or text == "":
            return ""

        # Replace fancy quotes
        text = re.sub(r"[“”]", '"', text)

        # Replace specific fancy quotes within square brackets
        text = re.sub(r"(?<=\[)“", '"', text)
        text = re.sub(r"”(?=])", '"', text)

        # Replace newline and tab characters with spaces
        text = re.sub(r"[\n\t]", " ", text)

        # Remove control characters (except line feed, carriage return, and horizontal tab)
        text = re.sub(r"[^\x20-\x7E\x0A\x0D\x09]", "", text)

        # Replace multiple spaces with a single space
        text = re.sub(r"\s{2,}", " ", text)

        # Remove the term "BOE"
        text = text.replace("BOE", "")

        # Remove invalid escape sequence
        text = text.replace("\x9d", "")

        # Remove extra backslashes
        text = text.replace("\\", "")

        return text

    def create_pos_examples(self, row: pd.Series) -> List[Union[str, List[str]]]:
        """
        Create positive examples based on the provided row from a DataFrame.

        Returns a list of matching sentences or an empty list.
        """
        value: str = row["relevant_paragraphs"]
        cleaned_value: str = self.clean_text(value)

        try:
            cleaned_value_list = ast.literal_eval(cleaned_value)
            if isinstance(cleaned_value_list, list):
                sentences = cleaned_value_list
            else:
                sentences = [cleaned_value]
        except (ValueError, SyntaxError):
            return [""]

        if not sentences or \
                self.json_file_name.replace(".json", "") != row["source_file"].replace(".pdf", "") or \
                row["data_type"] != "TEXT":
            return [""]

        source_page = str(row["source_page"])

        match = re.search(r"\d+", source_page)
        page_number = match.group() if match else None

        if page_number and page_number in self.pdf_content:
            paragraphs = [
                self.pdf_content[page_number][key_inner]["paragraph"] for key_inner in self.pdf_content[page_number]
            ]
            matching_sentences = [
                para for para in paragraphs if any(sentence in para for sentence in sentences)
            ]
            return matching_sentences if matching_sentences else sentences

        return [""]

    def create_neg_examples(self, row: pd.Series) -> List[str]:
        """
        Create negative examples based on the provided row from a DataFrame.

        Returns a list of context paragraphs or an empty list.
        """
        if not self.pdf_content or \
                self.json_file_name.replace(".json", "") != row["source_file"].replace(".pdf", "") or \
                row["data_type"] != "TEXT":
            return [""]

        paragraphs = [
            self.pdf_content[key_outer][key_inner]["paragraph"]
            for key_outer in self.pdf_content
            for key_inner in self.pdf_content[key_outer]
        ]

        context = random.choices(paragraphs[1:], k=self.neg_pos_ratio)
        return context

    def create_examples_annotate(self, filepath: str) -> List[pd.DataFrame]:
        """
        Create examples for annotation.

        Args:
            filepath (Path): Path to the file to be annotated.

        Returns:
            List[pd.DataFrame]: List of DataFrames containing the examples to be annotated.
        """
        df = pd.read_excel(filepath, sheet_name="data_ex_in_xls")
        df["annotation_file"] = os.path.basename(filepath)

        # Update the "source_page" column
        df["source_page"] = df["source_page"].apply(lambda x: [str(p - 1) for p in ast.literal_eval(x)])

        # List to store new DataFrames
        new_dfs: List[pd.DataFrame] = []

        for i, row in df.iterrows():
            row["Index"] = i
            contexts = [
                (self.create_pos_examples(row.copy()), 1),
                (self.create_neg_examples(row.copy()) if self.create_neg_samples else [], 0)
            ]

            for context, label in contexts:
                if context:
                    context_df = pd.DataFrame({"context": context, "label": label})
                    combined_df = pd.concat([row.to_frame().T.reset_index(drop=True), context_df], axis=1)
                    new_dfs.append(combined_df)

        return new_dfs

    def create_curator_df(self) -> pd.DataFrame:
        """
        Create a DataFrame containing the examples to be annotated by the curator.

        The DataFrame is saved as a CSV file in the output directory.
        """
        columns_order = [
            "question",
            "context",
            "label",
            "answer",
            "annotation_file",
            "company",
            "year",
            "source_file",
            "source_page",
            "Index",
            "data_type",
            "kpi_id"
        ]

        # Initialize an empty DataFrame with specified columns
        result_df = pd.DataFrame(columns=columns_order)

        if self.pdf_content:  # Check if pdf_content is not empty
            new_dfs = self.create_examples_annotate(self.annotation_folder)
            if new_dfs:
                # Concatenate the dataframes in new_dfs
                new_df = pd.concat(new_dfs, ignore_index=True)
                new_df.drop(columns=["question"], inplace=True, errors='ignore')  # Drop 'question' if it exists

                kpi_df = pd.read_csv(self.kpi_mapping_path, usecols=["kpi_id", "question"])
                merged_df = pd.merge(new_df, kpi_df, on="kpi_id", how="left")

                result_df = merged_df[columns_order]

        return result_df
