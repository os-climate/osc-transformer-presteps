"""Utils functions."""

import pandas as pd
import logging

_logger = logging.getLogger(__name__)


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
        kpi_category = {
            i[0]: [j.strip() for j in i[1].split(", ")]
            for i in df[["kpi_id", "kpi_category"]].values
        }

        _logger.info("KPI mapping loaded successfully.")

    except Exception as e:
        _logger.error(f"Error loading KPI mapping file: {e}")
        kpi_mapping = {}
        kpi_category = {}
        add_year = []

    return kpi_mapping, kpi_category, add_year
