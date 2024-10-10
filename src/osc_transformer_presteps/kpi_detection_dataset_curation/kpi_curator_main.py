import os
import logging
from datetime import date, datetime
from kpi_curator_function.curator import curate

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Define log file name
log_file = os.path.join(
    log_dir, f"app_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)


# Set up logging configuration
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,  # Set to DEBUG to capture all messages
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

# Create logger
_logger = logging.getLogger()

# Create console handler for info messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Log only info messages to console
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

# Add console handler to the logger
_logger.addHandler(console_handler)

# Optional: If you want to add a file handler for debug and warning messages
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)  # Log all messages to file
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

# Add file handler to the logger
_logger.addHandler(file_handler)


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

        da = date.today().strftime("%d-%m-%Y")

        # Save DataFrames to CSV files
        train_output_path = output_folder + f"/train_kpi_data_{da}.xlsx"
        val_output_path = output_folder + f"/val_kpi_data_{da}.xlsx"

        train_df.to_excel(train_output_path, index=False)
        val_df.to_excel(val_output_path, index=False)

        # Log the successful completion of the process
        _logger.info(f"Train data saved to: {train_output_path}")
        _logger.info(f"Validation data saved to: {val_output_path}")

        _logger.info("KPI curation completed successfully.")

    except Exception as e:
        # Log any exceptions that occur during the process
        _logger.error(f"Error during KPI curation: {str(e)}")
        raise
