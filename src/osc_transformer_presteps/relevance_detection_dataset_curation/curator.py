"""Python Script for Curation."""

import ast
import json
import math
import os
import random
import re
from typing import List, Tuple, Optional
import pandas as pd
from Levenshtein import distance as levenshtein_distance
from pathlib import Path
from pydantic import BaseModel, FilePath


class AnnotationData(BaseModel):
    """Pydantic model for annotation data."""

    annotation_folder: FilePath
    extract_json: FilePath
    kpi_mapping_path: FilePath


class Curator:
    """A data curator component responsible for creating table and text training data based on annotated data.

    Args:
    ----
        annotation_folder (str): path to the folder containing annotation files
        extract_json (str): path to the JSON file containing extracted content
        kpi_mapping_path (str): path to KPI Mapping csv

        neg_sample_rate (int): number of negative samples to positive examples
        create_neg_samples (bool): whether to create negative samples

    """

    def __init__(
        self,
        annotation_folder: str,
        extract_json: Path,
        kpi_mapping_path: str,
        neg_sample_rate: int = 1,
        create_neg_samples: bool = False,
    ) -> None:
        """Initialize the constructor for Curator object."""
        self.annotation_folder = annotation_folder
        self.extract_json = extract_json
        self.json_file_name = os.path.basename(extract_json).replace("_output", "")
        self.kpi_mapping_path = kpi_mapping_path
        self.neg_sample_rate = neg_sample_rate
        self.create_neg_samples = create_neg_samples

        self.pdf_content = self.load_pdf_content()

    def load_pdf_content(self) -> dict:
        """Load PDF content from the JSON file specified by `extract_json`.

        Reads the content of the JSON file and returns it as a dictionary.

        Returns:
        -------
            dict: A dictionary containing the loaded JSON data.

        Raises:
        ------
            FileNotFoundError: If the JSON file specified by `extract_json` does not exist.
            JSONDecodeError: If the content of the JSON file cannot be decoded.

        Note:
        ----
            This method assumes `extract_json` is a `Path` object pointing to a valid JSON file.

        """
        with self.extract_json.open() as f:
            return json.load(f)

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean a sentence by removing unwanted characters and control characters.

        Args:
        ----
            text (str): The text to be cleaned.

        Returns:
        -------
            str: The cleaned text.

        """
        if text is None or isinstance(text, float) and math.isnan(text) or text == "":
            return ""

        text = re.sub(r"[“”]", '"', text)
        text = re.sub(r"(?<=\[)“", '"', text)
        text = re.sub(r"”(?=])", '"', text)
        text = re.sub(r"[\n\t]", " ", text)
        text = re.sub(r"[^\x20-\x7E\x0A\x0D\x09]", "", text)
        text = re.sub(r"\s{2,}", " ", text)
        text = text.replace("BOE", "")
        text = text.replace("\x9d", "")
        text = text.replace("\\", "")
        return text

    def create_pos_examples(
        self, row: pd.Series
    ) -> Tuple[List[Tuple[Optional[str], str]], bool]:
        """Create positive examples based on the provided row from a DataFrame.

        Returns a list of matching sentences or an empty list, along with a flag
        indicating if sentences were found in the JSON.
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
            return ([(None, "")], False)  # Return with in_json_flag as False

        if (
            not sentences
            or self.json_file_name.replace(".json", "")
            != row["source_file"].replace(".pdf", "")
            or row["data_type"] != "TEXT"
        ):
            return ([(None, "")], False)  # Return with in_json_flag as False

        source_page = str(row["source_page"])
        match = re.search(r"\d+", source_page)
        if match:
            page_number = match.group()
        else:
            return ([(None, "")], False)

        if page_number in self.pdf_content:
            matching_sentences = [
                (key_inner, para)
                for key_inner in self.pdf_content[page_number]
                for para in [self.pdf_content[page_number][key_inner]["paragraph"]]
                if any(sentence in para for sentence in sentences)
            ]

            if matching_sentences:
                # If matching sentences found, return them with in_json_flag as True
                return matching_sentences, True

            # If no exact match found, find the closest paragraph and its ID
            closest_para, para_id, sent = self._get_closest_paragraph(
                sentences, page_number
            )

            if closest_para and row["answer"] in closest_para:
                return [(para_id, closest_para)], True
            else:
                return [(None, sent if sent else "")], False

        # If no relevant paragraph found, return with in_json_flag as False
        return ([(None, "")], False)

    def _get_closest_paragraph(
        self, sentences: List[str], page_number: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Find the closest paragraph on the given page and return it with its ID and the matched sentence."""
        closest_para = None
        closest_para_id = None
        closest_sentence = (
            None  # Initialize to store the sentence with the closest match
        )
        min_distance = float("inf")

        # Iterate over paragraphs on the page and compute Levenshtein distance
        for key_inner in self.pdf_content[page_number]:
            para = self.pdf_content[page_number][key_inner]["paragraph"]

            # Compute the minimum distance between the target sentences and this paragraph
            for sentence in sentences:
                dist = levenshtein_distance(sentence, para)
                if dist < min_distance:
                    min_distance = dist
                    closest_para = para
                    closest_para_id = key_inner  # Store the unique paragraph ID
                    closest_sentence = sentence  # Store the closest matching sentence

        return closest_para, closest_para_id, closest_sentence

    def create_neg_examples(self, row: pd.Series) -> List[str]:
        """Create negative examples excluding relevant paragraphs or close ones.

        Returns a list of context paragraphs or an empty list.
        """
        if (
            not self.pdf_content
            or self.json_file_name.replace(".json", "")
            != row["source_file"].replace(".pdf", "")
            or row["data_type"] != "TEXT"
        ):
            return [""]

        # Flatten all paragraphs from the PDF content
        paragraphs = [
            self.pdf_content[key_outer][key_inner]["paragraph"]
            for key_outer in self.pdf_content
            for key_inner in self.pdf_content[key_outer]
        ]

        relevant_paragraphs = row["relevant_paragraphs"]

        # Filter out paragraphs that are identical or too similar
        def is_similar(paragraph):
            return any(
                levenshtein_distance(paragraph, rel_para)
                <= 5  # Adjust threshold if needed
                for rel_para in relevant_paragraphs
            )

        negative_paragraphs = [p for p in paragraphs if not is_similar(p)]

        # Randomly select `neg_sample_rate` paragraphs from the filtered list
        context = (
            random.choices(negative_paragraphs, k=self.neg_sample_rate)
            if negative_paragraphs
            else [""]
        )

        return context

    def create_examples_annotate(self) -> List[pd.DataFrame]:
        """Create examples for annotation.

        Returns
        -------
            List[pd.DataFrame]: List of DataFrames containing the examples to be annotated.

        """
        df = pd.read_excel(self.annotation_folder, sheet_name="data_ex_in_xls")
        df["annotation_file"] = os.path.basename(self.annotation_folder)

        # Update the "source_page" column
        df["source_page"] = df["source_page"].apply(
            lambda x: [str(p - 1) for p in ast.literal_eval(x)]
        )

        new_dfs: List[pd.DataFrame] = []

        new_dfs = []

        for i, row in df.iterrows():
            if self.json_file_name.replace(".json", "") == row["source_file"].replace(
                ".pdf", ""
            ):
                row["annotation_file_row"] = i

                # Create positive examples and get the in_json_flag
                pos_examples, in_json_flag = self.create_pos_examples(row.copy())

                row["in_extraction_data_flag"] = in_json_flag

                # Extract unique_para_id and paragraph from pos_examples
                pos_contexts = [
                    (para, unique_para_id) for unique_para_id, para in pos_examples
                ]

                if self.create_neg_samples:
                    contexts = [
                        (pos_contexts, 1),
                        (
                            [
                                (neg_example, None)
                                for neg_example in self.create_neg_examples(row.copy())
                            ]
                            if self.create_neg_samples
                            else [("", None)],
                            0,
                        ),
                    ]
                else:
                    contexts = [(pos_contexts, 1)]

                for context, label in contexts:
                    if (
                        isinstance(context, list) and context
                    ):  # Check if context is a list and not empty
                        context_df = pd.DataFrame(
                            {
                                "context": [
                                    ctx[0] if isinstance(ctx, tuple) else ""
                                    for ctx in context
                                ],
                                "label": label,
                                "unique_paragraph_id": [
                                    ctx[1] if isinstance(ctx, tuple) else None
                                    for ctx in context
                                ],
                            }
                        )
                        combined_df = pd.concat(
                            [row.to_frame().T.reset_index(drop=True), context_df],
                            axis=1,
                        )
                        new_dfs.append(combined_df)

        return new_dfs

    def create_curator_df(self) -> pd.DataFrame:
        """Create a DataFrame containing the examples to be annotated by the curator.

        The DataFrame is saved as a CSV file in the output directory.
        """
        # Define the order of columns for the final DataFrame
        columns_order = [
            "company",
            "year",
            "source_file",
            "source_page",
            "context",
            "question",
            "kpi_id",
            "label",
            "in_extraction_data_flag",
            "unique_paragraph_id",
            "annotation_file_name",
            "annotation_file_row",
            "annotation_answer",
        ]

        if self.pdf_content:  # Check if pdf_content is not empty
            new_dfs = self.create_examples_annotate()
            if new_dfs:
                new_df = pd.concat(new_dfs, ignore_index=True)

                # Load the KPI mapping and merge with the newly created DataFrame
                kpi_df = pd.read_csv(
                    self.kpi_mapping_path, usecols=["kpi_id", "question"]
                )

                merged_df = pd.merge(new_df, kpi_df, on="kpi_id", how="left")

                result_df = merged_df.rename(columns={"answer": "annotation_answer"})

                # result_df.loc[result_df["label"] == 0, "in_extraction_data_flag"] = (
                #    bool(0)
                # )
                result_df.loc[
                    result_df["in_extraction_data_flag"] == 0, "unique_paragraph_id"
                ] = None

                result_df["annotation_file_name"] = Path(self.annotation_folder).name
                result_df["annotation_file_row"] += 2
                result_df = result_df[
                    result_df["context"].notna() & (result_df["context"] != "")
                ]

                # Reorder columns as specified in columns_order
                result_df = result_df[columns_order]
                result_df = result_df.reset_index(drop=True)

        return result_df
