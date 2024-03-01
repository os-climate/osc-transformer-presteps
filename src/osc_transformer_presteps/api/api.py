import logging

import uvicorn
from fastapi import APIRouter, FastAPI

from osc_transformer_presteps.api.extract import router as extraction_router
from osc_transformer_presteps.settings import get_settings

_logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(extraction_router)
app = FastAPI(docs_url=None, redoc_url=None, title="OSC Transformer Pre-Steps")
app.include_router(api_router)


def run_api(bind_hosts: str, port: int) -> None:
    uvicorn.run(app, host=bind_hosts, port=port, log_config=None, log_level="info")


if __name__ == "__main__":
    Settings = get_settings()
    run_api(bind_hosts=Settings.host, port=Settings.port)
