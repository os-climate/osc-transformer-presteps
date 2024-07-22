"""Python Script for Base Extractor."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel


_logger = logging.getLogger(__name__)


class _BaseSettings(BaseModel):
    """Get settings from the user.

    Args possible in the settings:
    min_paragraph_length (int)(Optional): Minimum alphabetic characters for paragraph,
                        any paragraph shorter than that will be disregarded.
    annotation_folder (str)(Optional): path to the folder containing all annotated
            Excel files. If provided, just the pdfs mentioned in annotation excels are
            extracted. Otherwise, all the pdfs in the pdf folder will be extracted.
    skip_extracted_files (bool)(Optional): whether to skip extracting a file if it exists in the extraction folder.
    protected_extraction: bool, optional : Flag allowing users to extract the protected pdf.

    """

    annotation_folder: Optional[str] = None
    min_paragraph_length: Optional[int] = 20
    skip_extracted_files: Optional[bool] = False
    protected_extraction: Optional[bool] = False


class ExtractionResponse(BaseModel):
    """Get Extraction Responses."""

    success: bool = True
    dictionary: Dict[str, Any] = {}


class BaseExtractor(ABC):
    """An abstract base class for extracting text from files."""

    extractor_name = "base"
    _extraction_response = ExtractionResponse()

    def __init__(self, settings: Optional[dict] = None):
        """Initialize a BaseExtractor instance."""
        settings_base: dict = {} if settings is None else settings
        settings_base = _BaseSettings(**settings_base).model_dump()
        self._settings: dict = settings_base

    def __init_subclass__(cls, **kwargs):
        """Initialize the subclass."""
        super().__init_subclass__(**kwargs)
        if cls.extractor_name == "base":
            raise ValueError(
                "Subclass must define an extractor_name not equal to 'base'."
            )

    def get_settings(self):
        """Get settings for extraction."""
        return self._settings

    def get_extractions(self):
        """Get extraction response."""
        return self._extraction_response

    def check_for_skip_files(
        self, input_file_path: Path, output_folder_path: Optional[Path]
    ) -> bool:
        """Check if a JSON file already exists in the output folder and determine whether to skip processing.

        Args:
        ----
            input_file_path (Path): The path of the input file.
            output_folder_path (Path): The path of the output folder.

        """
        if (
            "skip_extracted_files" in self._settings.keys()
            and self._settings["skip_extracted_files"]
            and output_folder_path is not None
            and input_file_path.with_suffix(".json") in output_folder_path.iterdir()
        ):
            _logger.info(
                f"The extracted JSON for `{input_file_path.name}` already exists. Skipping..."
            )
            _logger.info(
                "If you would like to re-extract the already processed files, "
                "set `skip_extracted_files` to False in the config file."
            )
            self._extraction_response.dictionary = {}
            self._extraction_response.success = False
            return True
        else:
            return False

    def extract(
        self,
        input_file_path: Path,
    ) -> ExtractionResponse:
        """Perform the extraction of text from the given input file path.

        Args:
        ----
            input_file_path (Path): The path to the input file.

        Returns:
        -------
            ExtractionResponse: An instance of the `ExtractionResponse` class containing the extraction results.

        """
        extracted = self._generate_extractions(input_file_path=input_file_path)
        extraction_response = self.get_extractions()
        extraction_response.success = extracted
        return extraction_response

    @abstractmethod
    def _generate_extractions(
        self,
        input_file_path: Path,
    ) -> bool:
        """Define how text is extracted from a give file in path.

        Args:
        ----
            input_file_path (Path): Should contain the path to a file as a pathlib.Path object.

        """
