from pathlib import Path
from osc_transformer_presteps.content_extraction.extractors.base_extractor import ExtractionResponse, BaseExtractor
from osc_transformer_presteps.utils import dict_to_json
from typing import Optional
import pytest

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


class TestExtractOneFile:

    @pytest.fixture()
    def base_extractor(self):
        """Initialize a concrete BaseExtractor element to test it."""
        return concrete_base_extractor("base_test")

    def test_save_extraction_to_file(self, base_extractor):
        """Test if we can save the output."""
        output_file_path = (
                Path(__file__).resolve().parents[1] / "data" / "json_files" / "output.json"
        )
        er = ExtractionResponse()
        er.dictionary = {"key": "value"}
        base_extractor._extraction_response = er
        dict_to_json(
            json_path=output_file_path, dictionary=er.dictionary
        )
        assert output_file_path.exists()
        output_file_path.unlink(missing_ok=True)