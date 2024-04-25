import logging

import uvicorn
from fastapi import APIRouter, FastAPI
from starlette.responses import RedirectResponse

from osc_transformer_presteps.api.extract import router as extraction_router
from osc_transformer_presteps.settings import ExtractionServerSettings

_logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(extraction_router)
app = FastAPI(title="OSC Transformer Pre-Steps")
app.include_router(api_router)


@app.get("/", tags=["info"], include_in_schema=False)
async def get_root() -> RedirectResponse:
    return RedirectResponse("docs")


def run_api(bind_hosts: str, port: int, log_level: str = "info") -> None:
    uvicorn.run(app, host=bind_hosts, port=port, log_config=None, log_level=log_level)


if __name__ == "__main__":
    Settings = ExtractionServerSettings()
    run_api(bind_hosts=Settings.host, port=Settings.port)
