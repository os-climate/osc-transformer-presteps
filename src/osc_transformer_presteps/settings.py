"""Python Script to define Extraction Settings."""

from pydantic import BaseModel


class ExtractionSettings(BaseModel):
    """Settings for controlling extraction behavior.

    Attributes
    ----------
    skip_extracted_files : bool, optional
        Flag indicating whether to skip files that have already been extracted.
        Defaults to False.
        Flag indicating whether to store the extracted data to a file.
        Defaults to True.
    protected_extraction: bool, optional
        Flag allowing users to extract the protected pdf.
        Defaults to False.

    """

    skip_extracted_files: bool = False
    protected_extraction: bool = False
