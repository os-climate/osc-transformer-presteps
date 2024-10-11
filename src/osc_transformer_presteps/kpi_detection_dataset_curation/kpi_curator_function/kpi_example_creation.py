"""Functions to make examples."""

import logging
import pandas as pd
from osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_data_processing import (
    clean_text,
    find_answer_start,
    find_closest_paragraph,
)

_logger = logging.getLogger(__name__)


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
    clean_answer = clean_text(r["answer"])
    clean_rel_par = clean_text(r["relevant_paragraphs"])

    # Check if the JSON for the source file is available
    if r["source_file"] not in json_dict:
        pass
    else:
        d = json_dict[r["source_file"]]

        # Get paragraphs from the JSON dictionary for the corresponding page (PDF pages start from 1, but JSON starts from 0)
        page_number = str(int(r["source_page"]) - 1)
        pars = d.get(page_number, [])

        if len(pars) == 0:
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
    """Filter relevant examples.

    Filter relevant examples from the relevant dataframe that are mentioned in the annotation files.
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
        annotation_df[["kpi_id", "relevant_paragraphs", "answer"]],
        left_on=["kpi_id", "paragraph"],
        right_on=["kpi_id", "relevant_paragraphs"],
        how="inner",
    )

    # Drop the 'relevant_paragraph' column as it's no longer needed
    relevant_df = relevant_df.drop(columns=["relevant_paragraphs"])

    for pdf_file in target_pdfs:
        # Filter annotations for the current PDF
        annotation_for_pdf = annotation_df[annotation_df["source_file"] == pdf_file]

        if len(annotation_for_pdf) == 0:
            _logger.debug(f"No annotations found for {pdf_file}. Skipping this PDF.")
            continue

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
                    & (neg_examples_df["answer"].map(lambda x, a=a: clean_text(a) in x))
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
    """Create unanswerable examples.

    Create unanswerable examples by generating negative samples from pairs of KPI questions and paragraphs
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
    neg_df["answer_start"] = [[-1]] * neg_df.shape[0]
    neg_df["answer"] = ""

    # Remove any duplicate examples based on answer, paragraph, and question
    neg_df = neg_df.drop_duplicates(
        subset=["answer", "paragraph", "question"]
    ).reset_index(drop=True)

    # Select the relevant columns for the final DataFrame
    neg_df = neg_df[["source_file", "paragraph", "question", "answer", "answer_start"]]

    _logger.info(f"Created {len(neg_df)} unanswerable examples.")

    return neg_df
