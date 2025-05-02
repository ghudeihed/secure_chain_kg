from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import validator
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str) and v:
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

try:
    settings = Settings()
except ValidationError as e:
    logger.error(f"Configuration error: {e}")
    raise SystemExit(1)