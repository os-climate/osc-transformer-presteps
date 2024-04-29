import ast
import json
import os
import random
import re
from pathlib import Path
from typing import List, Union

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel, FilePath, validator


class AnnotationData(BaseModel):
    """Pydantic model for annotation data."""

    annotation_folder: FilePath
    extract_json: FilePath
    kpi_mapping_path: FilePath
    output_path: Path

    @validator("output_path")
    def validate_output_path(cls, value):
        path_obj = Path(value)
        if not path_obj.parent.is_dir():
            raise ValueError("Output path should point to an existing directory.")
        return path_obj

    @validator("extract_json")
    def validate_extract_json(cls, value):
        path_obj = Path(value)
        if not path_obj.is_file():
            raise ValueError("Extract JSON path should point to an existing file.")
        return path_obj


class Curator:
    """A data curator component responsible for creating table and text training data based on annotated data.

    Args:
        annotation_folder (str): path to the folder containing annotation excel files
        extract_json (str): path to the JSON file containing extracted content
        kpi_mapping_path (str): path to KPI Mapping csv
        output_path (str): path to Curation.csv
        retrieve_paragraph (bool): whether to retrieve paragraphs
        neg_pos_ratio (int): ratio of negative to positive examples
        columns_to_read (List[str]): columns to read from the Excel file
        company_to_exclude (List[str]): companies to exclude
        create_neg_samples (bool): whether to create negative samples
        min_length_neg_sample (int): minimum length of negative samples
        seed (int): random seed
    """

    def __init__(
        self,
        annotation_folder: str,
        extract_json: str,
        kpi_mapping_path: str,
        output_path: str,
        retrieve_paragraph: bool = False,
        neg_pos_ratio: int = 1,
        columns_to_read: List[str] = [
            "company",
            "source_file",
            "source_page",
            "kpi_id",
            "year",
            "answer",
            "data_type",
            "relevant_paragraphs",
        ],
        company_to_exclude: List[str] = [],
        create_neg_samples: bool = True,
        min_length_neg_sample: int = 50,
        seed: int = 42,
    ) -> None:
        self.annotation_folder = Path(annotation_folder)
        self.extract_json = Path(extract_json)
        self.kpi_mapping_path = Path(kpi_mapping_path)
        self.output_path = Path(output_path)
        self.retrieve_paragraph = retrieve_paragraph
        self.neg_pos_ratio = neg_pos_ratio
        self.columns_to_read = columns_to_read
        self.company_to_exclude = company_to_exclude
        self.create_neg_samples = create_neg_samples
        self.min_length_neg_sample = min_length_neg_sample
        self.seed = seed

        self.pdf_content = self.load_pdf_content()
        self.create_curator_df(self.output_path)

    def load_pdf_content(self) -> dict:
        with self.extract_json.open() as f:
            return json.load(f)

    def clean_text(self, text: str) -> str:
        """Clean text."""
        text = re.sub(r"(?<=\[)“", '"', text)
        text = re.sub(r"”(?=])", '"', text)
        text = re.sub(r"[“”]", "", text)
        text = re.sub(r"[\n\t]", " ", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text

    def create_pos_examples(self, row: pd.Series) -> List[Union[str, List[str]]]:
        value: str = row["relevant_paragraphs"]
        sentences: List[str] = ast.literal_eval(self.clean_text(value))

        paragraphs: List[str] = [
            self.pdf_content[row["source_page"][0]][key_inner]["paragraph"]
            for key_inner in self.pdf_content[row["source_page"][0]]
        ]
        matching_sentences: List[str] = [para for para in paragraphs if sentences[0] in para]

        return matching_sentences if matching_sentences else sentences

    def create_neg_examples(self, row: pd.Series) -> List[str]:
        paragraphs: List[str] = [
            self.pdf_content[key_outer][key_inner]["paragraph"]
            for key_outer in self.pdf_content
            for key_inner in self.pdf_content[key_outer]
        ]

        context: List[str] = random.choices(paragraphs, k=self.neg_pos_ratio)

        return context

    def create_examples_annotate(self, filepath: Path) -> list[DataFrame]:
        df = pd.read_excel(filepath, sheet_name="data_ex_in_xls")[self.columns_to_read]
        df["annotator"] = os.path.basename(filepath)

        # Update the "source_page" column
        df["source_page"] = df["source_page"].apply(lambda x: [str(p - 1) for p in ast.literal_eval(x)])

        # Create an empty list to store new DataFrames
        new_dfs: List[pd.DataFrame] = []

        for i, row in df.iterrows():
            row["Index"] = i
            positive_context = self.create_pos_examples(row.copy())

            negative_context: List[str] = self.create_neg_examples(row.copy()) if self.create_neg_samples else []

            # Create DataFrames for positive contexts
            pos_df = pd.DataFrame({"context": positive_context, "label": 1})
            pos_df = pd.concat([row.to_frame().T.reset_index(drop=True), pos_df], axis=1)
            new_dfs.append(pos_df)

            # Create DataFrames for negative contexts
            neg_df = pd.DataFrame({"context": negative_context, "label": 0})
            neg_df = pd.concat([row.to_frame().T.reset_index(drop=True), neg_df], axis=1)
            new_dfs.append(neg_df)
        return new_dfs

    def create_curator_df(self, output_path) -> None:
        new_dfs = self.create_examples_annotate(self.annotation_folder)
        new_df = pd.concat(new_dfs, ignore_index=True)

        kpi_df = pd.read_csv(self.kpi_mapping_path, header=0)
        merged_df = pd.merge(new_df, kpi_df[["kpi_id", "question"]], on="kpi_id", how="left")

        columns_order = [
            "question",
            "context",
            "company",
            "source_file",
            "source_page",
            "kpi_id",
            "year",
            "answer",
            "data_type",
            "relevant_paragraphs",
            "annotator",
            "Index",
            "label",
        ]

        result_df = merged_df[columns_order]
        result_df.to_csv(output_path, index=False)
