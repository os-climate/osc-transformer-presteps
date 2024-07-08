import json
from pathlib import Path

from osc_transformer_presteps.content_extraction.extractors.pdf_text_extractor import (
    PDFExtractor,
)


class TestPdfExtractor:
    def test_pdf_with_extraction_issues(self):
        """In this test we try to extract the data from a pdf, where one can not extract text as it was produced via
        a "print". Check the file test_issue.pdf.
        """
        extractor = PDFExtractor()
        input_file_path = Path(__file__).resolve().parent / "test_issue.pdf"
        extraction_response = extractor.extract(input_file_path=input_file_path)
        assert extraction_response.dictionary == {}

    def test_pdf_with_no_extraction_issues(self):
        """In this test we try to extract the data from a pdf, where one can not extract text as it was produced via
        a "print". Check the file test_issue.pdf.
        """
        extractor = PDFExtractor()
        input_file_path = Path(__file__).resolve().parent / "test.pdf"
        extraction_response = extractor.extract(input_file_path=input_file_path)

        json_file_path = str(Path(__file__).resolve().parent / "test_data.json")
        with open(json_file_path, "r") as file:
            json_data = file.read()
        test_data = json.loads(json_data)
        assert extraction_response.dictionary == test_data
