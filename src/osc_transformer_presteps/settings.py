from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    log_level: str = "INFO"
    host: str
    port: int
    protocol: str = "http"
    api_url: str
    local_storage: str


@lru_cache
def get_settings() -> _Settings:
    env_file = Path(__file__).parent / ".env"
    return _Settings(_env_file=env_file)
