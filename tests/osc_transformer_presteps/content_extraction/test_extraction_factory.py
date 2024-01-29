import pytest

from osc_transformer_presteps.content_extraction.extraction_factory import get_extractor
from osc_transformer_presteps.content_extraction.extractors.pdf_text_extractor import (
    PDFExtractor,
)


class TestGetExtractor:
    def test_get_pdf_extractor(self):
        extractor = get_extractor(".pdf")
        assert isinstance(extractor, PDFExtractor)

    def test_get_non_existing_extractor(self):
        with pytest.raises(KeyError, match="Invalid extractor type"):
            get_extractor(".thisdoesnotexist")
