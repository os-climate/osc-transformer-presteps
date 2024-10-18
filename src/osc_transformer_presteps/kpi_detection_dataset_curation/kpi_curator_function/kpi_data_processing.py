"""Functions for Data Processing."""

import os
import re
import ast
import logging
import pandas as pd
import numpy as np
import Levenshtein
from osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_utils import (
    load_kpi_mapping,
)

_logger = logging.getLogger(__name__)

COLUMNS_TO_READ = [
    "company",
    "source_file",
    "source_page",
    "kpi_id",
    "year",
    "answer",
    "data_type",
    "relevant_paragraphs",
]

COL_ORDER = [
    "company",
    "source_file",
    "source_page",
    "kpi_id",
    "year",
    "answer",
    "data_type",
    "relevant_paragraphs",
    "annotator",
    "sector",
]


def aggregate_annots(annotation_folder: str) -> pd.DataFrame:
    """Aggregate Excel files containing annotations from a specified folder.

    This function looks for Excel files with 'annotation' in their names,
    reads them, ensures required columns are present, and aggregates the data
    into a single DataFrame.

    Args:
        annotation_folder (str): Path to the folder containing the
        annotation Excel files.

    Returns:
        pd.DataFrame: A DataFrame containing the aggregated data from
        the annotation files. Returns an empty DataFrame
        if no valid files are found.

    """
    xlsxs = [
        f
        for f in os.listdir(annotation_folder)
        if f.endswith(".xlsx") and "annotation" in f
    ]
    dfs = []

    for f in xlsxs:
        fname = os.path.join(annotation_folder, f)
        try:
            df = pd.read_excel(fname, sheet_name="data_ex_in_xls")

            # Ensure required columns exist
            missing_columns = [col for col in COLUMNS_TO_READ if col not in df.columns]
            assert (
                not missing_columns
            ), f"{f} is missing required columns: {missing_columns}"

            # Handle 'sector'/'Sector' columns
            if "Sector" in df.columns:
                df.rename(columns={"Sector": "sector"}, inplace=True)
            columns_to_read = COLUMNS_TO_READ + (
                ["sector"] if "sector" in df.columns else []
            )

            # Add 'annotator' column if it doesn't exist
            if "annotator" not in df.columns:
                df["annotator"] = f
            columns_to_read += ["annotator"]

            # Append filtered DataFrame to list
            dfs.append(df[columns_to_read])

        except Exception as e:
            _logger.error(f"Error processing file {f}: {str(e)}")
            continue  # Skip to the next file if there's an error

    # Log information about the aggregation process
    if dfs:
        _logger.info(f"Aggregating {len(dfs)} files.")
        return pd.concat(dfs) if len(dfs) > 1 else dfs[0]

    _logger.warning(
        f"No valid annotation files found in {annotation_folder}. "
        "Make sure the names have 'annotation' in the file names."
    )
    return pd.DataFrame()  # Return empty DataFrame if no files are processed


def read_agg(
    agg_annotation: str, annotation_folder: str, kpi_mapping_file: str
) -> pd.DataFrame:
    """Read an annotation file.

    Read the aggregated annotation file. If it doesn't exist, create it from the specified annotation folder.

    Args:
        agg_annotation (str): Path to the aggregated annotation file.
        annotation_folder (str): Path to the folder containing the annotation files.
        kpi_mapping_file (str): Path to the KPI mapping CSV file.

    Returns:
        pd.DataFrame: The DataFrame containing aggregated annotation data.

    """
    if not os.path.exists(agg_annotation):
        _logger.info(
            "{} not available, will create it from the annotation folder.".format(
                agg_annotation
            )
        )
        df = aggregate_annots(annotation_folder)
        df = clean_annotation(df, kpi_mapping_file)
    else:
        _logger.info("{} found, loading the data.".format(agg_annotation))
        df = pd.read_excel(agg_annotation)

        # Ensure columns are ordered according to COL_ORDER
        df = df[COL_ORDER]
        df["source_page"] = df["source_page"].apply(ast.literal_eval)

    return df


def clean_annotation(
    df: pd.DataFrame, kpi_mapping_file: str, exclude=None
) -> pd.DataFrame:
    """Clean the given DataFrame and saves the cleaned data to a specified path.

    The cleaning process involves:
        1. Dropping all rows with NaN values.
        2. Dropping rows with NaN values in specified columns.
        3. Removing specified companies.
        4. Cleaning the 'source_file' column.
        5. Cleaning the 'data_type' column.
        6. Cleaning the 'source_page' column.
        7. Removing examples with incorrect (kpi, data_type) pairs.

    Args:
        df (pd.DataFrame): The DataFrame to clean.
        kpi_mapping_file (str): Path to the KPI mapping CSV file.
        exclude (list[str], optional): List of companies to exclude from the DataFrame. Defaults to ["CEZ"].

    Returns:
        pd.DataFrame: The cleaned DataFrame.

    """
    if exclude is None:
        exclude = ["CEZ"]

    # Drop all rows with NaN values
    df = df.dropna(axis=0, how="all").reset_index(drop=True)

    # Drop rows with NaN for specific columns
    df = df.dropna(
        axis=0,
        how="any",
        subset=["company", "source_file", "source_page", "kpi_id", "year"],
    ).reset_index(drop=True)

    # Remove specified companies
    if exclude:
        df = df[~df.company.isin(exclude)]

    # Clean 'source_file' column
    def get_pdf_name_right(f: str) -> str:
        if not f.endswith(".pdf"):
            if f.endswith(",pdf"):
                filename = f.split(",pdf")[0].strip() + ".pdf"
            else:
                filename = f.strip() + ".pdf"
        else:
            filename = f.split(".pdf")[0].strip() + ".pdf"

        return filename

    df["source_file"] = df["source_file"].apply(get_pdf_name_right)

    # Clean 'data_type' column
    df["data_type"] = df["data_type"].apply(str.strip)

    # Clean 'source_page' column
    def clean_page(sp: str):
        if sp[0] != "[" or sp[-1] != "]":
            return None
        else:
            return [str(int(i)) for i in sp[1:-1].split(",")]

    temp = df["source_page"].apply(clean_page)
    invalid_source_page = df["source_page"][temp.isna()].unique().tolist()
    if invalid_source_page:
        _logger.warning(
            "Has invalid source_page format: {} and {} such examples".format(
                invalid_source_page, len(invalid_source_page)
            )
        )

    df["source_page"] = temp
    df = df.dropna(axis=0, subset=["source_page"]).reset_index(drop=True)

    # Load KPI mapping
    _, kpi_category, _ = load_kpi_mapping(kpi_mapping_file)

    # Remove examples with incorrect (kpi, data_type) pairs
    def clean_id(r: pd.Series) -> bool:
        try:
            kpi_id = float(r["kpi_id"])
        except ValueError:
            kpi_id = r["kpi_id"]

        try:
            return r["data_type"] in kpi_category.get(kpi_id, [])
        except KeyError:
            return True

    correct_id_bool = df[["kpi_id", "data_type"]].apply(clean_id, axis=1)
    df = df[correct_id_bool].reset_index(drop=True)

    # Log the number of dropped examples
    diff = correct_id_bool.shape[0] - df.shape[0]
    if diff > 0:
        _logger.debug(
            "Dropped {} examples due to incorrect kpi-data_type pair".format(diff)
        )

    save_path = "aggregated_annotation.xlsx"
    # Save the cleaned DataFrame
    df.to_excel(save_path, index=False)
    _logger.info(
        "Aggregated annotation file is created and saved at location {}.".format(
            save_path
        )
    )

    return df


def clean_paragraph(r: pd.Series) -> list[str] | None:
    """Clean the relevant_paragraphs column.

    This function takes a string representation of relevant paragraphs, fixes any issues with
    brackets or parentheses, and splits the paragraphs into a list.

    Args:
        r (pd.Series): A pandas Series row containing the relevant paragraphs as a string.

    Returns:
        list[str] | None: A list of cleaned paragraphs or None if the input is not valid.

    """
    # Remove any starting or trailing white spaces
    strp = r.strip()

    # Attempt to fix issues with brackets and parentheses
    if strp[0] == "{" or strp[0] == "]":
        strp = "[" + strp[1:]
    elif strp[-1] == "}" or strp[-1] == "[":
        strp = strp[:-1] + "]"

    s = strp[0]
    e = strp[-1]

    if s != "[" or e != "]":
        _logger.warning("Input string is not a valid list format: {}".format(strp))
        return None  # Return None if unable to fix

    # Deal with multiple paragraphs
    strp = strp[2:-2]  # Remove the outer brackets
    first_type = list(re.finditer('", "', strp))
    second_type = list(re.finditer('","', strp))

    # Determine how to split the paragraphs based on the types found
    if not first_type and not second_type:
        return [strp]  # Return as a single paragraph

    temp = []
    start = 0

    if first_type and not second_type:
        for i in first_type:
            temp.append(strp[start : i.start()])
            start = i.start() + 4
        temp.append(strp[start:])
        return temp

    if not first_type and second_type:
        for i in second_type:
            temp.append(strp[start : i.start()])
            start = i.start() + 3
        temp.append(strp[start:])
        return temp

    # Handle a combination of both types
    track1, track2 = 0, 0
    while track1 < len(first_type) or track2 < len(second_type):
        if track1 == len(first_type):
            for i in second_type[track2:]:
                temp.append(strp[start : i.start()])
                start = i.start() + 3
                break

        if track2 == len(second_type):
            for i in first_type[track1:]:
                temp.append(strp[start : i.start()])
                start = i.start() + 4
                break

        if first_type[track1].start() < second_type[track2].start():
            temp.append(strp[start : first_type[track1].start()])
            start = first_type[track1].start() + 4
            track1 += 1
        else:
            temp.append(strp[start : second_type[track2].start()])
            start = second_type[track2].start() + 3
            track2 += 1

    return temp


def split_multi_paragraph(df: pd.DataFrame) -> pd.DataFrame:
    """Split DataFrame entries with multiple relevant paragraphs into separate rows.

    Args:
        df (pd.DataFrame): DataFrame containing relevant paragraphs.

    Returns:
        pd.DataFrame: A new DataFrame with split relevant paragraphs.

    """
    _logger.debug("Starting to split multi-paragraph entries.")

    # Selecting rows where "relevant_paragraphs" has exactly 1 paragraph
    df_single = df[
        df["relevant_paragraphs"].apply(len) == 1
    ].copy()  # Use .copy() to avoid modifying the slice
    df_single.loc[:, "source_page"] = df_single["source_page"].apply(lambda x: x[0])
    df_single.loc[:, "relevant_paragraphs"] = df_single["relevant_paragraphs"].apply(
        lambda x: x[0]
    )

    # Selecting rows where "relevant_paragraphs" has more than 1 paragraph
    df_multi = df[df["relevant_paragraphs"].apply(len) > 1].copy()

    # Create an empty list to store the new rows
    new_multi = []

    # Ensure col_order contains the necessary columns
    col_order = COL_ORDER + ["question"]
    df_multi = df_multi[col_order]

    # Iterate over the rows of df_multi
    for row in df_multi.itertuples():
        paragraph_count = len(
            row[3]
        )  # Number of paragraphs in the "relevant_paragraphs" column
        for i in range(paragraph_count):
            new_row = list(row[1:])  # Convert row to a list for modification
            new_row[2] = row[3][i]  # Set the relevant paragraph
            new_row[7] = row[8][i]  # Set the source page
            new_multi.append(new_row)

    # Convert the new_multi list to a DataFrame with the same columns as df_multi
    df_multi = pd.DataFrame(new_multi, columns=df_multi.columns)

    # Concatenate df_single and df_multi and reset the index
    df = pd.concat([df_single, df_multi], axis=0).reset_index(drop=True)

    _logger.debug("Completed splitting multi-paragraph entries.")
    return df


def clean(df: pd.DataFrame, kpi_mapping_file: str) -> pd.DataFrame:
    """Clean the DF.

    Clean the DataFrame by mapping KPI IDs to questions, dropping invalid entries,
    and formatting relevant paragraphs.

    Args:
        df (pd.DataFrame): The DataFrame to clean.
        kpi_mapping_file (str): Path to the KPI mapping CSV file.

    Returns:
        pd.DataFrame: The cleaned DataFrame.

    """
    _logger.debug("Starting to clean the DataFrame.")

    kpi_mapping, kpi_category, add_year = load_kpi_mapping(kpi_mapping_file)

    def map_kpi(r: pd.Series) -> str | None:
        """Map KPI ID to question."""
        try:
            question = kpi_mapping[float(r["kpi_id"])]
        except (KeyError, ValueError):
            question = None

        if question:
            try:
                year = int(float(r["year"]))
            except ValueError:
                year = r["year"]
            if float(r["kpi_id"]) in add_year:
                front = question.split("?")[0]
                question = f"{front} in year {year}?"
        return question

    df["question"] = df[["kpi_id", "year"]].apply(map_kpi, axis=1)
    df = df.dropna(subset=["question"]).reset_index(drop=True)
    df = df[~df["relevant_paragraphs"].isna()]
    df = df[~df["answer"].isna()]

    # Clean answer format
    df["answer"] = df["answer"].apply(lambda x: " ".join(str(x).split("\n")).strip())

    # Clean relevant paragraphs
    df["relevant_paragraphs"] = df["relevant_paragraphs"].apply(clean_paragraph)
    df = df.dropna(subset=["relevant_paragraphs"]).reset_index(drop=True)

    df = split_multi_paragraph(df)

    _logger.debug("DataFrame cleaning completed.")
    return df


def clean_text(text: str) -> str:
    """Clean the Text.

    Clean the input text by removing unusual quotes, excessive whitespace,
    special characters, and converting to lowercase.

    Args:
        text (str): The text to be cleaned.

    Returns:
        str: The cleaned text.

    """
    _logger.debug("Cleaning text.")

    # Substitute unusual quotes at the start and end of the string
    text = re.sub(r"(?<=\[)“", '"', text)
    text = re.sub(r"”(?=\])", '"', text)
    text = re.sub(r"“|”", "", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", text)
    text = re.sub(r"\s{2,}", " ", text)

    # Replace special regex characters
    special_regex_char = [
        "(",
        ")",
        "^",
        "+",
        "*",
        "$",
        "|",
        "\\",
        "?",
        "[",
        "]",
        "{",
        "}",
    ]
    text = "".join(["" if c in special_regex_char else c for c in text])

    text = text.lower()

    # Remove consecutive dots
    consecutive_dots = re.compile(r"\.{2,}")
    text = consecutive_dots.sub("", text)

    _logger.debug("Text cleaning completed.")
    return text


def find_answer_start(answer: str, par: str) -> list[int]:
    """Find the starting indices of the answer in the provided paragraph.

    Args:
        answer (str): The answer to search for.
        par (str): The paragraph in which to search for the answer.

    Returns:
        list[int]: A list of starting indices where the answer is found in the paragraph.

    """
    _logger.debug("Finding answer start indices.")

    answer = "".join([r"\." if c == "." else c for c in answer])

    # Avoid matching numeric values like '0' to '2016'
    if answer.isnumeric():
        pat1 = f"[^0-9]{answer}"
        pat2 = f"{answer}[^0-9]"
        matches1 = re.finditer(pat1, par)
        matches2 = re.finditer(pat2, par)
        ans_start_1 = [i.start() + 1 for i in matches1]
        ans_start_2 = [i.start() for i in matches2]
        ans_start = list(set(ans_start_1 + ans_start_2))
    else:
        pat = answer
        matches = re.finditer(pat, par)
        ans_start = [i.start() for i in matches]

    _logger.debug(f"Found starting indices: {ans_start}")
    return ans_start


def find_closest_paragraph(
    pars: list[str], clean_rel_par: str, clean_answer: str
) -> str:
    """Find the closest matching paragraph to the annotated relevant paragraph.

    If the exact paragraph match is not found, use Levenshtein distance to find the closest
    paragraph that contains the answer.

    Args:
        pars (list[str]): A list of paragraphs to search within.
        clean_rel_par (str): Annotated clean relevant paragraph.
        clean_answer (str): The clean answer to search for.

    Returns:
        str: The closest full paragraph or the original annotated relevant paragraph if no better match is found.

    """
    _logger.info("Finding closest paragraph.")

    # Clean all paragraphs using the `clean_text` function
    clean_pars = [clean_text(p) for p in pars]
    found = False

    # Try to find an exact match with the annotated relevant paragraph
    for p in clean_pars:
        sentence_start = find_answer_start(clean_rel_par, p)
        if len(sentence_start) != 0:
            clean_rel_par = p
            found = True
            _logger.info("Exact match found for relevant paragraph.")
            break

    # If no exact match, use Levenshtein distance to find the closest paragraph
    if not found:
        _logger.info(
            "Exact match not found, performing fuzzy matching with Levenshtein distance."
        )

        # Calculate Levenshtein distances between the annotated paragraph and the list of paragraphs
        distances = [Levenshtein.distance(clean_rel_par, p) for p in clean_pars]
        min_index = np.argmin(distances)  # Find the index of the closest paragraph
        max_par = clean_pars[min_index]

        ans_start = find_answer_start(clean_answer, max_par)

        if len(ans_start) != 0:
            _logger.info(
                "Closest paragraph with the answer found using Levenshtein distance."
            )
            clean_rel_par = max_par

    return clean_rel_par
