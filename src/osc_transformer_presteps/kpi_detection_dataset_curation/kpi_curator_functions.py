""" Helper functions for curation of KPI Detection dataset."""
import ast
import json
import logging
import os
import re
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz


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
    """
    Aggregate Excel files containing annotations from a specified folder.

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


def load_kpi_mapping(kpi_mapping_file: str) -> tuple:
    """Load the KPI mapping from a CSV file.

    This function reads the KPI mapping file and extracts mappings of KPI IDs to questions,
    identifies which KPIs should have their year added, and categorizes the KPIs.

    Args:
        kpi_mapping_file (str): Path to the KPI mapping CSV file.

    Returns:
        tuple: A tuple containing:
            - KPI_MAPPING (dict): A dictionary mapping KPI IDs to questions.
            - KPI_CATEGORY (dict): A dictionary mapping KPI IDs to their respective categories.
            - ADD_YEAR (list): A list of KPI IDs that should have their year added.

    """
    try:
        df = pd.read_csv(kpi_mapping_file)
        _kpi_mapping = {str(i[0]): i[1] for i in df[["kpi_id", "question"]].values}
        kpi_mapping = {float(key): value for key, value in _kpi_mapping.items()}

        # Which questions should have the year added
        add_year = df[df["add_year"]].kpi_id.tolist()

        # Category where the answer to the question should originate from
        kpi_category = {i[0]: [j.strip() for j in i[1].split(", ")] for i in df[["kpi_id", "kpi_category"]].values}

        _logger.info("KPI mapping loaded successfully.")

    except Exception as e:
        _logger.error(f"Error loading KPI mapping file: {e}")
        kpi_mapping = {}
        kpi_category = {}
        add_year = []
    
    return kpi_mapping, kpi_category, add_year


def clean_annotation(df: pd.DataFrame, kpi_mapping_file: str, exclude: list[str] = None) -> pd.DataFrame:
    """
    Clean the given DataFrame and saves the cleaned data to a specified path.

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


def read_agg(
    agg_annotation: str, annotation_folder: str, kpi_mapping_file: str
) -> pd.DataFrame:
    """Read the aggregated annotation CSV file. If it doesn't exist, create it from
    the specified annotation folder.

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
        df = aggregate_annots(
            annotation_folder
        )  # Assuming this function is defined elsewhere
        df = clean_annotation(df, kpi_mapping_file)
    else:
        _logger.info("{} found, loading the data.".format(agg_annotation))
        df = pd.read_excel(agg_annotation)

        # Ensure columns are ordered according to COL_ORDER (assuming COL_ORDER is defined)
        df = df[COL_ORDER]
        df["source_page"] = df["source_page"].apply(ast.literal_eval)

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
    col_order = COL_ORDER + ["question"]  # Assuming COL_ORDER is defined
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
    """Clean the DataFrame by mapping KPI IDs to questions, dropping invalid entries,
    and formatting relevant paragraphs.

    Args:
        df (pd.DataFrame): The DataFrame to clean.
        kpi_mapping_file (str): Path to the KPI mapping CSV file.

    Returns:
        pd.DataFrame: The cleaned DataFrame.

    """
    _logger.debug("Starting to clean the DataFrame.")

    KPI_MAPPING, KPI_CATEGORY, ADD_YEAR = load_kpi_mapping(kpi_mapping_file)

    def map_kpi(r: pd.Series) -> str | None:
        """Map KPI ID to question."""
        try:
            question = KPI_MAPPING[float(r["kpi_id"])]
        except (KeyError, ValueError):
            question = None

        if question:
            try:
                year = int(float(r["year"]))
            except ValueError:
                year = r["year"]
            if float(r["kpi_id"]) in ADD_YEAR:
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
    """Clean the input text by removing unusual quotes, excessive whitespace,
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

    answer = "".join(["\." if c == "." else c for c in answer])

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

    If the exact paragraph match is not found, use fuzzy matching to find the closest
    paragraph that contains the answer.

    Args:
        pars (list[str]): A list of paragraphs to search within.
        clean_rel_par (str): Annotated clean relevant paragraph.
        clean_answer (str): The clean answer to search for.

    Returns:
        str: The closest full paragraph or the original annotated relevant paragraph if no better match is found.

    """
    _logger.info("Finding closest paragraph.")

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

    # If no exact match, use fuzzy matching to find the closest paragraph
    if not found:
        _logger.info("Exact match not found, performing fuzzy matching.")
        scores = [fuzz.partial_ratio(p, clean_rel_par) for p in clean_pars]
        max_par = clean_pars[np.argmax(scores)]
        ans_start = find_answer_start(clean_answer, max_par)

        if len(ans_start) != 0:
            _logger.info(
                "Closest paragraph with the answer found using fuzzy matching."
            )
            clean_rel_par = max_par

    return clean_rel_par


def return_full_paragraph(
    r: pd.Series, json_dict: dict[str, dict[str, list[str]]]
) -> tuple[str, str, list[int]]:
    """Find the closest full paragraph to the annotated relevant paragraph using the parsed JSON dictionary.

    If the full paragraph cannot be found, return the annotated relevant paragraph instead.

    Args:
        r (pd.Series): A pandas row containing the relevant data including 'answer', 'relevant_paragraphs', 'source_file', and 'source_page'.
        json_dict (dict): A dictionary containing extracted paragraphs for each PDF file in the format:
                          {pdf_name: {page_number: list_of_paragraphs}}

    Returns:
        tuple:
            clean_rel_par (str): The closest or annotated relevant paragraph.
            clean_answer (str): The cleaned answer text.
            ans_start (list[int]): A list of starting indices of the answer in the paragraph.

    """
    # _logger.debug(f"Returning full paragraph for file {r['source_file']} on page {r['source_page']}.")

    clean_answer = clean_text(r["answer"])
    clean_rel_par = clean_text(r["relevant_paragraphs"])

    # Check if the JSON for the source file is available
    if r["source_file"] not in json_dict:
        # _logger.warning(f"{r['source_file']} JSON file not found. Using annotated relevant text.")
        # _logger.debug(f"{r['source_file']} JSON file not found. Using annotated relevant text.")
        pass
    else:
        d = json_dict[r["source_file"]]

        # Get paragraphs from the JSON dictionary for the corresponding page (PDF pages start from 1, but JSON starts from 0)
        page_number = str(int(r["source_page"]) - 1)
        pars = d.get(page_number, [])

        if len(pars) == 0:
            # _logger.warning(f"{r['source_file']} has no paragraphs on page {r['source_page']}. Using annotated relevant text.")
            # _logger.debug(f"{r['source_file']} has no paragraphs on page {r['source_page']}. Using annotated relevant text.")
            pass
        else:
            # Try to find the closest paragraph to the annotated relevant paragraph
            clean_rel_par = find_closest_paragraph(pars, clean_rel_par, clean_answer)

    # Find starting indices of the answer in the paragraph
    ans_start = find_answer_start(clean_answer, clean_rel_par)

    # Handle cases where the answer starts at index 0 (potential bug in FARM model)
    if 0 in ans_start:
        clean_rel_par = " " + clean_rel_par  # Add space to avoid index 0 issue
        ans_start = [i + 1 for i in ans_start]
        _logger.debug("Adjusted answer start indices.")

    return clean_rel_par, clean_answer, ans_start


def find_extra_answerable(
    df: pd.DataFrame, json_dict: dict[str, dict[str, list[str]]]
) -> pd.DataFrame:
    """Find extra answerable samples by searching for paragraphs in pages other than the annotated one.

    Args:
        df (pd.DataFrame): The original dataframe containing the annotated data.
        json_dict (dict): A dictionary where keys are PDF file names and values are dictionaries that map page numbers
                          (as strings) to lists of paragraphs.

    Returns:
        pd.DataFrame: A dataframe containing additional answerable samples with new paragraphs from other pages.

    """
    _logger.info("Finding extra answerable samples in the dataset.")

    new_positive = []

    for t in df.itertuples():
        pdf_name = t[2]
        page = str(int(t[3]) - 1)  # Convert page to zero-indexed
        clean_answer = clean_text(t[6])
        kpi_id = t[4]

        # Skip if the PDF is not in the JSON dictionary
        if pdf_name not in json_dict.keys():
            continue

        # Skip certain KPI IDs (year questions, company-related)
        if float(kpi_id) in [0, 1, 9, 11]:
            continue

        # Iterate over all pages of the PDF
        for p in json_dict[pdf_name].keys():
            if p == page:  # Skip the current page
                continue

            pars = json_dict[pdf_name][p]

            if len(pars) == 0:
                continue

            # Search for answers in the paragraphs
            for par in pars:
                clean_rel_par = clean_text(par)
                ans_start = find_answer_start(clean_answer, clean_rel_par)

                # Handle FARM bug where answer starts at index 0
                if 0 in ans_start:
                    clean_rel_par = " " + clean_rel_par
                    ans_start = [i + 1 for i in ans_start]

                if len(ans_start) != 0:
                    # Create a new example
                    example = [
                        t[1],
                        t[2],
                        p,
                        kpi_id,
                        t[5],
                        clean_answer,
                        t[7],
                        clean_rel_par,
                        "1QBit",
                        t[10],
                        t[11],
                        ans_start,
                    ]
                    new_positive.append(example)

    new_positive_df = pd.DataFrame(new_positive, columns=df.columns)

    _logger.info(f"Found {len(new_positive_df)} extra answerable samples.")
    return new_positive_df


def create_answerable(
    df: pd.DataFrame,
    json_dict: dict[str, dict[str, list[str]]],
    find_new_answerable: bool,
) -> pd.DataFrame:
    """Create answerable samples by finding full paragraphs and optionally searching for additional answerable samples.

    Args:
        df (pd.DataFrame): The original dataframe containing the annotated data.
        json_dict (dict): A dictionary where keys are PDF file names and values are dictionaries that map page numbers
                          (as strings) to lists of paragraphs.
        find_new_answerable (bool): A boolean flag to indicate whether to find additional answerable samples.

    Returns:
        pd.DataFrame: A dataframe with answerable samples, including both original and optionally new answerable samples.

    """
    # Apply return_full_paragraph to find closest full paragraphs
    results = df.apply(return_full_paragraph, axis=1, json_dict=json_dict)

    # Update the dataframe with new relevant paragraphs, answers, and answer start positions
    temp = pd.DataFrame(results.tolist())
    df["relevant_paragraphs"] = temp[0]
    df["answer"] = temp[1]
    df["answer_start"] = temp[2]

    # Drop rows where the answer is NaN
    df = df[~df["answer"].isna()]

    _logger.info(f"Processed {len(df)} rows for answerable samples.")

    # Find additional answerable samples if the flag is set
    if find_new_answerable:
        _logger.info("Finding additional answerable samples.")
        synthetic_pos = find_extra_answerable(df, json_dict)
    else:
        synthetic_pos = pd.DataFrame([])

    # Concatenate original and synthetic answerable samples
    """pos_df = pd.concat([df, synthetic_pos]).drop_duplicates(
        subset=["answer", "relevant_paragraphs", "question"]).reset_index(
            drop=True)"""

    # Drop columns that are entirely NA from both DataFrames before concatenation
    df_filtered = df.dropna(axis=1, how="all")
    synthetic_pos_filtered = synthetic_pos.dropna(axis=1, how="all")

    # Concatenate and drop duplicates based on specific columns
    pos_df = (
        pd.concat([df_filtered, synthetic_pos_filtered])
        .drop_duplicates(subset=["answer", "relevant_paragraphs", "question"])
        .reset_index(drop=True)
    )

    # Filter out rows where answer_start is empty
    pos_df = pos_df[pos_df["answer_start"].apply(len) != 0].reset_index(drop=True)

    # Rename the relevant_paragraphs column to paragraph
    pos_df.rename({"relevant_paragraphs": "paragraph"}, axis=1, inplace=True)

    # Select relevant columns for the final dataframe
    pos_df = pos_df[["source_file", "paragraph", "question", "answer", "answer_start"]]

    _logger.info(f"Created {len(pos_df)} final answerable samples.")

    return pos_df


def filter_relevant_examples(
    annotation_df: pd.DataFrame, relevant_df: pd.DataFrame
) -> pd.DataFrame:
    """Filters relevant examples from the relevant dataframe that are mentioned in the annotation files.
    For each source PDF, it excludes examples whose pages and questions are already annotated in the annotation file.

    Args:
        annotation_df (pd.DataFrame): DataFrame containing all annotations merged into a single DataFrame.
        relevant_df (pd.DataFrame): DataFrame of relevant examples identified by the relevance detector model.

    Returns:
        pd.DataFrame: A subset of `relevant_df` considered as negative examples (examples not in the annotation file).

    """
    _logger.debug("Filtering relevant examples based on annotations.")

    # Get the list of PDFs mentioned in the relevant DataFrame
    target_pdfs = list(relevant_df["pdf_name"].unique())

    neg_examples_df_list = []

    formatted_relevant_df = relevant_df[relevant_df["paragraph_relevance_flag"] == 1]

    relevant_df = formatted_relevant_df.merge(
        annotation_df[["kpi_id", "relevant_paragraph", "answer"]],
        left_on=["kpi_id", "paragraph"],
        right_on=["kpi_id", "relevant_paragraph"],
        how="inner",
    )

    # Drop the 'relevant_paragraph' column as it's no longer needed
    relevant_df = relevant_df.drop(columns=["relevant_paragraph"])

    for pdf_file in target_pdfs:
        # Filter annotations for the current PDF
        annotation_for_pdf = annotation_df[annotation_df["source_file"] == pdf_file]

        if len(annotation_for_pdf) == 0:
            _logger.debug(f"No annotations found for {pdf_file}. Skipping this PDF.")
            continue

        # Get unique pages in the annotation file
        pages = list(annotation_for_pdf["source_page"].unique())

        # Filter relevant examples for the current PDF
        neg_examples_df = relevant_df[relevant_df["pdf_name"] == pdf_file]

        # Get lists of questions and answers from annotations for this PDF
        questions = annotation_for_pdf["question"].tolist()
        answers = annotation_for_pdf["answer"].astype(str).tolist()

        # Ensure that negative examples do not contain the answer of any annotated question
        for q, a in zip(questions, answers):
            neg_examples_df = neg_examples_df[
                ~(
                    (neg_examples_df["question"] == q)
                    & (neg_examples_df["answer"].map(lambda x: clean_text(a) in x))
                )
            ]

        neg_examples_df_list.append(neg_examples_df)

    # Concatenate the list of negative examples DataFrames
    merged_neg_examples_df = pd.concat(neg_examples_df_list, ignore_index=True)

    _logger.info(f"Filtered {len(merged_neg_examples_df)} negative examples.")

    return merged_neg_examples_df


def create_unanswerable(
    annotation_df: pd.DataFrame, relevant_text_path: str
) -> pd.DataFrame:
    """Creates unanswerable examples by generating negative samples from pairs of KPI questions and paragraphs
    that are classified as relevant by the relevance detector but are not present in the annotation files.

    Args:
        annotation_df (pd.DataFrame): An aggregated DataFrame containing all annotations.
        relevant_text_path (str): Path to the file containing the relevant text DataFrame (in Excel format).

    Returns:
        pd.DataFrame: A DataFrame of unanswerable examples in the same format as the SQuAD dataset.

    """
    _logger.debug("Creating unanswerable examples from relevant and annotation data.")

    # Load relevant examples from the Excel file
    relevant_df = pd.read_excel(relevant_text_path)

    # Ensure that the necessary columns are present in the relevant DataFrame
    required_columns = [
        "page",
        "pdf_name",
        "unique_paragraph_id",
        "paragraph",
        "kpi_id",
        "question",
        "paragraph_relevance_flag",
        "paragraph_relevance_score(for_label=1)",
    ]
    assert all(
        [col in relevant_df.columns for col in required_columns]
    ), "The relevant DataFrame is missing one or more required columns."

    # Select only the relevant columns in the expected order
    relevant_df = relevant_df[required_columns]

    # Clean the paragraphs for consistency
    relevant_df["paragraph"] = relevant_df["paragraph"].apply(clean_text)

    # Filter out relevant examples that are annotated (i.e., not unanswerable)
    neg_df = filter_relevant_examples(annotation_df, relevant_df)

    # Rename "pdf_name" to "source_file" for consistency with other datasets
    neg_df.rename({"pdf_name": "source_file"}, axis=1, inplace=True)

    # Assign empty answers and empty answer start lists for unanswerable examples
    neg_df["answer_start"] = [[]] * neg_df.shape[0]
    neg_df["answer"] = ""

    # Remove any duplicate examples based on answer, paragraph, and question
    neg_df = neg_df.drop_duplicates(
        subset=["answer", "paragraph", "question"]
    ).reset_index(drop=True)

    # Select the relevant columns for the final DataFrame
    neg_df = neg_df[["source_file", "paragraph", "question", "answer", "answer_start"]]

    _logger.info(f"Created {len(neg_df)} unanswerable examples.")

    return neg_df


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
    """Curates the dataset by combining answerable and unanswerable examples for training and validation.
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
