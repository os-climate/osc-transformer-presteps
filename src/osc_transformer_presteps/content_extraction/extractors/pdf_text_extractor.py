import io
import logging
import re
from pathlib import Path
from typing import Optional, List

import numpy as np
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pypdf import PdfReader

from .base_extractor import BaseExtractor

_logger = logging.getLogger(__name__)


def clean_text(text):
    """
    Clean text

    Args:
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


def check_pdf_accessibility(pdf_file: str) -> bool:
    """Checks if it can access the content of the pdf at all.
    Args:
        pdf_file (str): Path to the pdf file.
    Returns:
        boolean: If an error occurs while loading the pdf it returns false, otherwise true.
    """
    try:
        pdf_instance = PdfReader(pdf_file)
        _ = len(pdf_instance.pages)
        return True
    except Exception as e:
        _logger.warning(f"{e}: Unable to process {pdf_file}")
        return False


class PDFExtractor(BaseExtractor):
    """This Class is responsible for extracting text data from PDFs and saving
        the result in a json format file.
        Each name/value pair in the json file refers to page_number and
        the list of paragraphs in that page.
    Args:
        settings (dict)(optional): See specification under _Settings class.
    """

    extractor_name = "pdf_text_extractor"

    def __init__(self, settings: Optional[dict] = None):
        super().__init__(settings)

    def extract(
        self,
        input_file_path: Path,
    ) -> None:
        """Extract text from a single pdf file and stores it to the <filename>.json.
        The dictionary output will be returned. If the file was already processed
        or it was not possible to extract the content it will return an empty dict.

        Args:
            input_file_path (Path): full path to the pdf file
        """
        _logger.info(f"Extracting {input_file_path.name} ...")

        self.extract_pdf_by_page(str(input_file_path))

        _logger.info(f"The number of pages extracted: {len(self._extraction_dict)}")
        _logger.info(
            f"The number of paragraphs found: "
            f"{max(self._extraction_dict[max(self._extraction_dict.keys())].keys())}"
        )

    def extract_pdf_by_page(self, pdf_file):
        """Read the content of each page in a pdf file, this method uses pdfminer and stores the output to
        the _extraction_dict variable.
        Args:
            pdf_file (str): Path to the pdf file.
        """
        self._extraction_dict = {}
        if check_pdf_accessibility(pdf_file):
            idx = 0

            # Create a PDF resource manager
            rsrcmgr = PDFResourceManager()
            retstr = io.StringIO()
            laparams = LAParams()

            # Create a PDF page interpreter
            device = TextConverter(rsrcmgr, retstr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            with open(pdf_file, "rb") as fp:
                for page_number, page in enumerate(PDFPage.get_pages(fp)):
                    interpreter.process_page(page)
                    data = retstr.getvalue()
                    paragraphs_data = self.process_page(data)
                    if len(paragraphs_data) == 0:
                        continue
                    idx = self.update_extraction_dict(idx, page_number, paragraphs_data, str(Path(pdf_file).name))
                    retstr.truncate(0)
                    retstr.seek(0)

    def process_page(self, input_text):
        """This function receives a text following:
        1. Divide it into  paragraphs, using \n\n
        2. Remove table data: To achieve this, if number of alphabet characters of paragraph
            is less min_paragraph_length, it is considered as table cell and it will be removed.

        Args:
            input_text (str): Content of each pdf.

        Returns:
            paragraphs (list of str): List of paragraphs.
        """
        paragraphs = input_text.split("\n\n")

        # Get ride of table data if the number of alphabets in a paragraph is less than `min_paragraph_length`
        mpl = self._settings["min_paragraph_length"]
        paragraphs_cleaned = [
            clean_text(p) for p in paragraphs if np.sum([c.isalpha() + c.isnumeric() for c in clean_text(p)]) > mpl
        ]
        return paragraphs_cleaned

    def update_extraction_dict(self, idx: int, page_number: int, paragraphs_data: List[str], file_name: str) -> int:
        """
        Update the extraction dictionary with the provided data and return the updated index.

        Args:
            idx (int): The starting index for the paragraphs in the extraction dictionary.
            page_number (int): The page number of the paragraphs.
            paragraphs_data (List[str]): The list of paragraphs data.
            file_name (str): The name of the PDF file.

        Returns:
            int: The updated index after adding the paragraphs to the extraction dictionary.
        """
        self._extraction_dict.update(
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
                    for (x, y) in zip(range(idx, idx + len(paragraphs_data)), paragraphs_data)
                }
            }
        )
        return idx + len(paragraphs_data)
