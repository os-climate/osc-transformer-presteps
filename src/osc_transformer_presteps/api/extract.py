import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from starlette import status

from osc_transformer_presteps.content_extraction.extraction_factory import get_extractor
from osc_transformer_presteps.content_extraction.extractors.base_extractor import (
    ExtractionError,
    ExtractionResponse,
)
from osc_transformer_presteps.settings import get_settings

router = APIRouter(tags=["extract"])
_logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/liveness")
def liveness():
    """
    Endpoint to check the liveness of the FastAPI application.
    """
    return {"message": "OSC Transformer Pre-Steps Server is running."}


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    description="Endpoint takes a file and tries to extract the data of that file via a known extraction class.",
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ExtractionError,
            "description": "There was an error during the extraction.",
        },
        status.HTTP_200_OK: {
            "model": ExtractionResponse,
            "description": "Extraction successful.",
        },
    },
)
def extract(
    file: UploadFile,
) -> ExtractionResponse:
    """Extracts information from a file. For that the file is stored temporarily and deleted at the end.

    Args:
        file (UploadFile): The file from which information will be extracted.

    Returns:
        ExtractionResponse: The response containing the extracted information.

    Raises:
        HTTPException: If an error occurs during extraction process.
    """
    assert file.filename
    _logger.info(f"Received file {file.filename} of type {Path(file.filename).suffix}.")
    file_path_temp = Path(settings.local_storage) / file.filename
    try:
        save_upload_file(file, file_path_temp)

        extraction_settings = {"skip_extracted_files": False, "store_to_file": True}
        extractor = get_extractor(file_path_temp.suffix, extraction_settings)
        extraction_response = extractor.extract(input_file_path=file_path_temp)

        file_path_temp.unlink()
        return extraction_response
    except ExtractionError as v:
        try:
            file_path_temp.unlink()
        except Exception:
            pass
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=jsonable_encoder(v))


def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Saves an uploaded file to a specified destination.

    Args:
        upload_file (UploadFile): The file to be saved.
        destination (Path): The path where the file will be saved.
    """
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
