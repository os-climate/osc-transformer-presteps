from unittest.mock import patch
from src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.kpi_utils import (
    load_kpi_mapping,
)


@patch(
    "src.osc_transformer_presteps.kpi_detection_dataset_curation.kpi_curator_function.utils._logger"
)
def test_load_kpi_mapping(mock_logger, mock_kpi_mapping_file):
    """Test the load_kpi_mapping function with a valid KPI mapping file."""

    # Call the function
    kpi_mapping, kpi_category, add_year = load_kpi_mapping(mock_kpi_mapping_file)

    # Assert the mapping dictionaries and list are correct
    assert kpi_mapping == {1.0: "What is A?", 2.0: "What is B?"}
    assert kpi_category == {1: ["typeA", "typeB"], 2: ["typeB", "typeC"]}
    assert add_year == [1]

    # Assert logger info was called
    mock_logger.info.assert_called_with("KPI mapping loaded successfully.")
