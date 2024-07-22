"""Module to test the base_extractor.py."""

from pathlib import Path
from typing import Optional

import pytest

from osc_transformer_presteps.content_extraction.extractors.base_extractor import (
    BaseExtractor,
    ExtractionResponse,
)


def concrete_base_extractor(name: str):
    """Replace all abstract methods by concrete ones."""

    class ConcreteBaseExtractor(BaseExtractor):
        extractor_name = name

        def _generate_extractions(
            self,
            input_file_path: Path,
        ) -> Optional[dict]:
            return None

    return ConcreteBaseExtractor()


class TestBaseExtractor:
    """Class to collect tests for the BaseExtractor."""

    @pytest.fixture()
    def base_extractor(self):
        """Initialize a concrete BaseExtractor element to test it."""
        return concrete_base_extractor("base_test")

    def test_extractor_name_is_base(self):
        """Tests if we get a ValueError in case a subclass has not changed extractor_name."""
        with pytest.raises(
            ValueError,
            match="Subclass must define an extractor_name not equal to 'base'.",
        ):
            concrete_base_extractor("base")

    def test_get_settings(self, base_extractor):
        """Test if retrieving the right settings."""
        settings = base_extractor.get_settings()
        assert settings["annotation_folder"] is None
        assert settings["min_paragraph_length"] == 20
        assert settings["skip_extracted_files"] is False

    def test_get_extractions(self, base_extractor):
        """Test if we can retrieve extraction response correctly."""
        base_extractor._extraction_response = ExtractionResponse(
            **{"dictionary": {"a": "b"}, "success": True}
        )
        assert base_extractor.get_extractions().dictionary == {"a": "b"}
        assert base_extractor.get_extractions().success is True

    def test_check_for_skip_files(self, base_extractor):
        """Test if files are really skipped when defined as such."""
        input_file_path = (
            Path(__file__).resolve().parents[3] / "data" / "pdf_files" / "test.pdf"
        )
        output_folder_path = Path(__file__).resolve().parents[3] / "data" / "pdf_files"
        assert not base_extractor.check_for_skip_files(
            input_file_path, output_folder_path
        )

        # Create a JSON file in the output folder
        json_file_path = output_folder_path / "test.json"
        json_file_path.touch()

        # Set skip_extracted_files to True
        base_extractor._settings["skip_extracted_files"] = True
        assert base_extractor.check_for_skip_files(input_file_path, output_folder_path)

        # Set skip_extracted_files to False
        base_extractor._settings["skip_extracted_files"] = False
        assert not base_extractor.check_for_skip_files(
            input_file_path, output_folder_path
        )

        json_file_path.unlink(missing_ok=True)
