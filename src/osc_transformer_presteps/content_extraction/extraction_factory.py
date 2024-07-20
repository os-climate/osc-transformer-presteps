"""Python Script to register and call extraction factory."""

import logging
from typing import Callable, Optional

from .extractors.base_extractor import BaseExtractor
from .extractors.pdf_text_extractor import PDFExtractor

_extractors: dict = {}
_logger = logging.getLogger(__name__)


def register_extractor(extractor_type: str) -> Callable:
    """Register an extractor class for a specific type.

    This function acts as a decorator that registers an extractor class
    under a specified type. The registered extractors are stored in the
    `_extractors` dictionary.
    """

    def decorator(extractor_cls: Callable) -> Callable:
        _extractors[extractor_type] = extractor_cls
        return extractor_cls

    return decorator


@register_extractor(".pdf")
def pdf_extractor(settings: Optional[dict] = None) -> PDFExtractor:
    """Create and return a PDFExtractor instance."""
    return PDFExtractor(settings)


def get_extractor(
    extractor_type: str, settings: Optional[dict] = None
) -> BaseExtractor:
    """Get an extractor instance based on the extractor_type.

    Args:
    ----
        extractor_type (str): Type of extractor to be retrieved
        settings: Settings specific to the extractor

    Returns:
    -------
        BaseExtractor: Instance of the specified extractor type

    """
    _logger.debug("The extractor type is: " + extractor_type)
    extractor_class = _extractors.get(extractor_type.lower())
    if extractor_class:
        _logger.debug(f"Retrieving {extractor_type} extractor instance")
        extractor_instance = extractor_class(settings)
        return extractor_instance
    else:
        _logger.error(f"Invalid extractor type: {extractor_type}")
        raise KeyError("Invalid extractor type")
