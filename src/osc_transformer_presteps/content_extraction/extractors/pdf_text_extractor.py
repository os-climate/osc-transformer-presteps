"""Python script for extracting content from large pdf in desired format."""

import io
import logging
import re
from pathlib import Path
from typing import List, Optional

import numpy as np
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pypdf import PdfReader

from .base_extractor import BaseExtractor

_logger = logging.getLogger(__name__)


def clean_text(text):
    """Clean text.

    Args:
    ----
        text (str): The input text to clean
    Returns:
        str: The cleaned text

    """
    # Substitute unusual quotes at the start of the string with usual quotes
    text = re.sub(r"(?<=\[)“", '"', text)
    # Substitute unusual quotes at the end of the string with usual quotes
    text = re.sub(r"”(?=])", '"', text)
    # Remove the remaining unusual quotes
    text = re.sub(r"\|", "", text)
    # Replace newline and tab characters with a space
    text = re.sub(r"[\n\t]", " ", text)
    # Remove control characters and non-printable ASCII characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", text)
    # Replace multiple consecutive spaces with a single space
    text = re.sub(r"\s{2,}", " ", text)

    return text


def check_pdf_accessibility(pdf_file: str, protected_extraction: bool) -> bool:
    """Check if it can access the content of the pdf at all.

    Args:
    ----
        pdf_file (str): Path to the pdf file.
        protected_extraction (bool): Allow user to extract protected pdf.

    Returns:
    -------
        boolean: If an error occurs while loading the pdf it returns false, otherwise true.

    """
    pdf_instance = PdfReader(pdf_file)
    if not protected_extraction and pdf_instance.is_encrypted:
        _logger.warning(
            f"Extraction of protected PDF data is not allowed: Problem with pdf_file: {Path(pdf_file).name}."
        )
        return False
    _ = len(pdf_instance.pages)
    return True


class PDFExtractor(BaseExtractor):
    """Class responsible for extracting text data from PDFs and saving the result in a json format file.

    Each name/value pair in the json file refers to page_number and
    the list of paragraphs in that page.

    Args:
    ----
        settings (dict)(optional): See specification under _Settings class.

    """

    extractor_name = "pdf_text_extractor"

    def __init__(self, settings: Optional[dict] = None):
        """Initialize the settings for pdf_text_extractor."""
        super().__init__(settings)

    def _generate_extractions(
        self,
        input_file_path: Path,
    ) -> bool:
        """Extract text from a single pdf file and stores it to the <filename>.json.

        The dictionary output will be returned. If the file was already processed
        or it was not possible to extract the content it will return an empty dict.

        Args:
        ----
            input_file_path (Path): full path to the pdf file

        """
        _logger.debug(f"Extracting {input_file_path.name} ...")

        extracted = self.extract_pdf_by_page(str(input_file_path))
        if extracted:
            _logger.debug(
                f"The number of pages extracted: {len(self._extraction_response.dictionary)}"
            )
            paragraphs = (
                0
                if len(self._extraction_response.dictionary.keys()) == 0
                else max(
                    self._extraction_response.dictionary[
                        max(self._extraction_response.dictionary.keys())
                    ].keys()
                )
            )
            _logger.debug(f"The number of paragraphs found: {paragraphs}.")
            return True
        return False

    def extract_pdf_by_page(self, pdf_file: str) -> bool:
        """Read the content of each page in a pdf file.

        Args:
        ----
            pdf_file (str): Path to the pdf file.

        """
        # pdfminer logger issue: https://stackoverflow.com/questions/29762706/warnings-on-pdfminer
        orig_level = _logger.level
        logging.root.setLevel(logging.ERROR)
        try:
            self._extraction_response.dictionary = {}
            extracted = False
            pdf_accessibility = check_pdf_accessibility(
                pdf_file, self._settings["protected_extraction"]
            )
            if pdf_accessibility:
                idx = 0

                # Create a PDF resource manager
                rsrcmgr = PDFResourceManager()
                retstr = io.StringIO()
                laparams = LAParams()

                # Create a PDF page interpreter
                device = TextConverter(rsrcmgr, retstr, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)

                with open(pdf_file, "rb") as fp:
                    for page_number, page in enumerate(
                        PDFPage.get_pages(fp, check_extractable=False)
                    ):
                        interpreter.process_page(page)
                        data = retstr.getvalue()
                        paragraphs_data = self.process_page(data)
                        if len(paragraphs_data) == 0:
                            continue
                        idx = self.update_extraction_dict(
                            idx, page_number, paragraphs_data, str(Path(pdf_file).name)
                        )
                        retstr.truncate(0)
                        retstr.seek(0)
                extracted = True
            logging.root.setLevel(orig_level)
            _logger.debug("Pdf was accessible: " + str(pdf_accessibility))
            return extracted
        except Exception as e:
            logging.root.setLevel(orig_level)
            raise e

    def process_page(self, input_text):
        r"""Process the input text from a PDF page.

        Function receives a text following:
        1. Divide it into  paragraphs, using \n\n
        2. Remove table data: To achieve this, if number of alphabet characters of paragraph
            is less min_paragraph_length, it is considered as table cell and it will be removed.

        Args:
        ----
            input_text (str): Content of each pdf.

        Returns:
        -------
            paragraphs (list of str): List of paragraphs.

        """
        paragraphs = input_text.split("\n\n")

        # Get rid of table data if the number of alphabets in a paragraph is less than `min_paragraph_length`
        mpl = self._settings["min_paragraph_length"]
        paragraphs_cleaned = [
            clean_text(p)
            for p in paragraphs
            if np.sum([c.isalpha() + c.isnumeric() for c in clean_text(p)]) > mpl
        ]
        return paragraphs_cleaned

    def update_extraction_dict(
        self, idx: int, page_number: int, paragraphs_data: List[str], file_name: str
    ) -> int:
        """Update the extraction dictionary with the provided data and return the updated index.

        Args:
        ----
            idx (int): The starting index for the paragraphs in the extraction dictionary.
            page_number (int): The page number of the paragraphs.
            paragraphs_data (List[str]): The list of paragraphs data.
            file_name (str): The name of the PDF file.

        Returns:
        -------
            int: The updated index after adding the paragraphs to the extraction dictionary.

        """
        (
            self._extraction_response.dictionary.update(
                {
                    str(page_number): {
                        str(x): {
                            "pdf_name": file_name,
                            "unique_paragraph_id": x,
                            "paragraph": y,
                            "page": page_number,
                            "start_index_page": idx,
                            "last_index_page": idx + len(paragraphs_data) - 1,
                        }
                        for (x, y) in zip(
                            range(idx, idx + len(paragraphs_data)), paragraphs_data
                        )
                    }
                }
            )
        )
        return idx + len(paragraphs_data)
