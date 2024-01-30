from pathlib import Path
from typing import Optional

import pytest

from osc_transformer_presteps.content_extraction.extractors.base_extractor import (
    BaseExtractor,
)


def concrete_base_extractor(name: str):
    """This function replaces all abstract methods by concrete ones."""

    class ConcreteBaseExtractor(BaseExtractor):
        extractor_name = name

        def extract(
            self,
            input_file_path: Path,
        ) -> Optional[dict]:
            return None

    return ConcreteBaseExtractor()


class TestBaseExtractor:
    @pytest.fixture()
    def base_extractor(self):
        return concrete_base_extractor("base_test")

    def test_extractor_name_is_base(self):
        """This function tests if we get a ValueError in case a subclass has not changed extractor_name to
        something different then base.
        """
        with pytest.raises(ValueError, match="Subclass must define an extractor_name not equal to 'base'."):
            concrete_base_extractor("base")

    def test_get_settings(self, base_extractor):
        settings = base_extractor.get_settings()
        assert settings["annotation_folder"] is None
        assert settings["min_paragraph_length"] == 20
        assert settings["skip_extracted_files"] is False
        assert settings["store_to_file"] is True

    def test_get_extractions(self, base_extractor):
        base_extractor._extraction_dict = {"a": "b"}
        assert base_extractor.get_extractions() == {"a": "b"}

    def test_check_for_skip_files(self, base_extractor):
        input_file_path = Path(__file__).resolve().parent / "test.pdf"
        output_folder_path = Path(__file__).resolve().parent
        assert not base_extractor.check_for_skip_files(input_file_path, output_folder_path)

        # Create a JSON file in the output folder
        json_file_path = output_folder_path / "test.json"
        json_file_path.touch()

        # Set skip_extracted_files to True
        base_extractor._settings["skip_extracted_files"] = True
        assert base_extractor.check_for_skip_files(input_file_path, output_folder_path)

        # Set skip_extracted_files to False
        base_extractor._settings["skip_extracted_files"] = False
        assert not base_extractor.check_for_skip_files(input_file_path, output_folder_path)

        json_file_path.unlink(missing_ok=True)

    def test_save_extraction_to_file(self, base_extractor):
        """
        The
        """
        output_file_path = Path(__file__).resolve().parent / "output.json"
        base_extractor._extraction_dict = {"key": "value"}
        base_extractor.save_extraction_to_file(output_file_path)
        assert output_file_path.exists()
        output_file_path.unlink(missing_ok=True)
