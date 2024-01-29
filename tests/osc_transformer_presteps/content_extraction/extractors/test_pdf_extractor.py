import json
from pathlib import Path

from osc_transformer_presteps.content_extraction.extractors.pdf_text_extractor import (
    PDFExtractor,
)


class TestPdfExtractor:
    def test_pdf_with_extraction_issues(self):
        """
        In this test we try to extract the data from a pdf, where one can not extract text as it was produced via
        a "print". Check the file test_issue.pdf.
        """
        extractor = PDFExtractor()
        input_file_path = Path(__file__).resolve().parent / "test_issue.pdf"
        extractor.extract(input_file_path=input_file_path)
        assert extractor.get_extractions() == {}

    def test_pdf_with_no_extraction_issues(self):
        """
        In this test we try to extract the data from a pdf, where one can not extract text as it was produced via
        a "print". Check the file test_issue.pdf.
        """
        extractor = PDFExtractor()
        input_file_path = Path(__file__).resolve().parent / "test.pdf"
        extractor.extract(input_file_path=input_file_path)

        with open("test_data.json", "r") as file:
            json_data = file.read()
        test_data = json.loads(json_data)
        assert extractor.get_extractions() == test_data
