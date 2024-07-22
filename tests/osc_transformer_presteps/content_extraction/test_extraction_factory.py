"""Module to test the extraction_factory.py."""

import pytest

from osc_transformer_presteps.content_extraction.extraction_factory import get_extractor
from osc_transformer_presteps.content_extraction.extractors.pdf_text_extractor import (
    PDFExtractor,
)


class TestGetExtractor:
    """Class to collect tests for the get_extractor function."""

    def test_get_pdf_extractor(self):
        """Test if we can retrieve the pdf extractor."""
        extractor = get_extractor(".pdf")
        assert isinstance(extractor, PDFExtractor)

    def test_get_pdf_extractor_non_standard_ending(self):
        """Test if we can retrieve the pdf extractor even if file ending is not classical lowercase."""
        extractor = get_extractor(".PdF")
        assert isinstance(extractor, PDFExtractor)

    def test_get_non_existing_extractor(self):
        """Test for an error message for an invalid extractor type."""
        with pytest.raises(KeyError, match="Invalid extractor type"):
            get_extractor(".thisdoesnotexist")
