"""KPI-CURATOR-MAIN file."""

from datetime import date
from pathlib import Path
import logging
from osc_transformer_presteps.utils import (
    specify_root_logger,
    set_log_folder,
    log_dict,
    LogLevel,
)
from osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_curation import (
    curate,
)


def run_kpi_curator(
    annotation_folder: str,
    agg_annotation: str,
    extracted_text_json_folder: str,
    output_folder: str,
    kpi_mapping_file: str,
    relevance_file_path: str,
    val_ratio: float,
    find_new_answerable: bool = True,
    create_unanswerable: bool = True,
) -> None:
    """Curates KPI data and splits it into training and validation sets. Saves the results as CSV files.

    Args:
        annotation_folder (str): Path to the folder containing annotations.
        agg_annotation (str): File path for the aggregated annotation data. (if available)
        extracted_text_json_folder (str): Folder containing extracted text data in JSON format.
        output_folder (str): Folder where the resulting train and validation CSV files will be saved.
        kpi_mapping_file (str): Path to the KPI mapping file.
        relevance_file_path (str): Path to the relevant text file.
        val_ratio (float): Ratio of validation data (e.g., 0.2 for a 20% validation split).
        find_new_answerable (bool, optional): Whether to find new answerable KPIs. Defaults to True.
        create_unanswerable (bool, optional): Whether to create unanswerable KPIs. Defaults to True.

    Returns:
        None: Saves the resulting DataFrames (train and validation) to CSV files.

    """
    try:
        # Set up log folder and initialize logger
        cwd = Path.cwd()
        logs_folder_path = set_log_folder(cwd, "logs")
        log_level = "info"
        specify_root_logger(
            log_level=log_dict[LogLevel(log_level)], logs_folder=logs_folder_path
        )
        _logger = logging.getLogger(__name__)

        # Log the start of the process
        _logger.info("Starting KPI curation process")

        # Perform the curation and split data into training and validation DataFrames
        train_df, val_df = curate(
            annotation_folder,
            agg_annotation,
            extracted_text_json_folder,
            kpi_mapping_file,
            relevance_file_path,
            val_ratio,
            find_new_answerable,
            create_unanswerable,
        )

        # Format current date for file naming
        da = date.today().strftime("%d-%m-%Y")

        # Save DataFrames to Excel files
        train_output_path = Path(output_folder) / f"train_kpi_data_{da}.xlsx"
        val_output_path = Path(output_folder) / f"val_kpi_data_{da}.xlsx"

        train_df.to_excel(train_output_path, index=False)
        val_df.to_excel(val_output_path, index=False)

        # Log the successful completion of the process
        _logger.info(f"Train data saved to: {train_output_path}")
        _logger.info(f"Validation data saved to: {val_output_path}")
        _logger.info("KPI curation completed successfully.")

    except Exception as e:
        # Log any exceptions that occur during the process
        _logger.error(f"Error during KPI curation: {str(e)}", exc_info=True)
        raise
