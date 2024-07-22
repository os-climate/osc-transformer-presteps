"""Module to test the pdf_extractor.py."""

import json
from pathlib import Path
from pypdf.errors import PdfStreamError
import pytest

from osc_transformer_presteps.content_extraction.extractors.pdf_text_extractor import (
    PDFExtractor,
)


class TestPdfExtractor:
    """Class to collect tests for the PDFExtractor class."""

    def test_pdf_with_extraction_issues(self):
        """Test with extraction issue.

        A test where we try to extract the data from a pdf, where one can not extract text as it was produced via
        a "print". Check the file test_issue.pdf.
        """
        extractor = PDFExtractor()
        input_file_path = (
            Path(__file__).resolve().parents[3]
            / "data"
            / "pdf_files"
            / "test_issue.pdf"
        )
        extraction_response = extractor.extract(input_file_path=input_file_path)
        assert extraction_response.dictionary == {}

    def test_encrypted_pdf(self):
        """Test with encrypted pdf.

        A test where we try to extract the data from a pdf which is encrypted.
        """
        extractor = PDFExtractor()
        input_file_path = (
            Path(__file__).resolve().parents[3] / "data" / "pdf_files" / "encrypted.pdf"
        )
        extraction_response = extractor.extract(input_file_path=input_file_path)
        assert extraction_response.dictionary == {}

    def test_error_pdf(self):
        """Test with encrypted pdf.

        A test where we try to extract the data from a pdf which is encrypted.
        """
        extractor = PDFExtractor()
        input_file_path = (
            Path(__file__).resolve().parents[3] / "data" / "pdf_files" / "no_pdf.pdf"
        )
        with pytest.raises(PdfStreamError):
            extractor.extract(input_file_path=input_file_path)

    def test_pdf_with_no_extraction_issues(self):
        """Test with no extraction issue.

        In this test we try to extract the data from a pdf, where one can not extract text as it was produced via
        a "print". Check the file test_issue.pdf.
        """
        extractor = PDFExtractor()
        input_file_path = (
            Path(__file__).resolve().parents[3] / "data" / "pdf_files" / "test.pdf"
        )
        extraction_response = extractor.extract(input_file_path=input_file_path)

        json_file_path = str(
            Path(__file__).resolve().parents[3]
            / "data"
            / "json_files"
            / "test_data.json"
        )
        with open(json_file_path, "r") as file:
            json_data = file.read()
        test_data = json.loads(json_data)
        assert extraction_response.dictionary == test_data
