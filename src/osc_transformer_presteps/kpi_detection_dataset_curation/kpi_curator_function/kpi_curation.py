"""Curator code for KPI Detection Module."""

import logging
import json
import os
import pandas as pd
from osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_data_processing import (
    read_agg,
    clean,
)
from osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_example_creation import (
    create_answerable,
    create_unanswerable,
)

_logger = logging.getLogger(__name__)


def curate(
    annotation_folder: str,
    agg_annotation: str,
    extracted_text_json_folder: str,
    kpi_mapping_file: str,
    relevance_file_path: str,
    val_ratio: float,
    find_new_answerable_flag: bool = True,
    create_unanswerable_flag: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Curate the dataset by combining answerable and unanswerable examples for training and validation.

    The function processes annotated data and relevant text, extracting answerable/unanswerable examples,
    and splits the final dataset into training and validation sets.

    Args:
        annotation_folder (str): Path to the folder containing annotation files.
        agg_annotation (str): Path to the aggregated annotation file.
        extracted_text_json_folder (str): Path to the folder containing extracted text JSONs.
        kpi_mapping_file (str): Path to the KPI mapping file.
        relevance_file_path (str): Path to the relevant text data file (Excel format).
        val_ratio (float): Ratio of data to be used for validation (between 0 and 1).
        find_new_answerable_flag (bool, optional): Flag to determine whether to find additional answerable examples. Defaults to True.
        create_unanswerable_flag (bool, optional): Flag to determine whether to create unanswerable examples. Defaults to True.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: A tuple containing the training DataFrame and validation DataFrame.

    """
    # Read and clean the aggregated annotation data
    df = read_agg(agg_annotation, annotation_folder, kpi_mapping_file)
    df = df[df["data_type"] == "TEXT"]
    df = clean(df, kpi_mapping_file)

    _logger.debug("Aggregated annotation data has been cleaned and filtered.")

    # Get all available JSON files from the extraction phase
    all_json = [
        i for i in os.listdir(extracted_text_json_folder) if i.endswith(".json")
    ]
    json_dict = {}

    _logger.info(f"Loading extracted text JSONs from {extracted_text_json_folder}.")

    for f in all_json:
        name = f.split(".json")[0]
        with open(os.path.join(extracted_text_json_folder, f), "r") as fi:
            d = json.load(fi)
        json_dict[name + ".pdf"] = d

    _logger.info(f"Loaded {len(json_dict)} JSON files.")

    # Create answerable examples
    _logger.info("Creating answerable examples.")
    answerable_df = create_answerable(df, json_dict, find_new_answerable_flag)

    # Optionally create unanswerable examples
    if create_unanswerable_flag:
        _logger.info("Creating unanswerable examples.")
        unanswerable_df = create_unanswerable(df, relevance_file_path)
        # Concatenate answerable and unanswerable data
        all_df = (
            pd.concat([answerable_df, unanswerable_df])
            .drop_duplicates(subset=["answer", "paragraph", "question"])
            .reset_index(drop=True)
        )

        _logger.info(f"Combined {len(all_df)} answerable and unanswerable examples.")
    else:
        all_df = answerable_df
        _logger.info(f"Using only answerable examples: {len(all_df)} examples.")

    # Split the data into training and validation sets based on the provided ratio
    _logger.info(
        f"Splitting data into training and validation sets with validation ratio {val_ratio}."
    )

    # Set a seed for reproducibility
    seed = 42
    all_df = all_df.sample(frac=1).reset_index(drop=True)

    train_df = all_df.sample(frac=1 - val_ratio, random_state=seed)
    val_df = all_df.drop(train_df.index)

    # Reset index for both dataframes
    train_df.reset_index(drop=True, inplace=True)
    val_df.reset_index(drop=True, inplace=True)

    _logger.info(
        f"Training set size: {len(train_df)}, Validation set size: {len(val_df)}."
    )

    return train_df, val_df
