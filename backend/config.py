from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    SPARQL_ENDPOINT: str = "http://fuseki:3030/securechain/query"
    SBOM_MAX_DEPTH: int = 10
    SBOM_TOOL_NAME: str = "Secure-Chain SBOM Generator"
    SBOM_TOOL_VERSION: str = "1.0.0"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def parse_allowed_origins(cls, v):
        if isinstance(v, str) and v:
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SPARQL_ENDPOINT", mode="before")
    def warn_missing_endpoint(cls, v):
        if not v:
            logger.warning("SPARQL_ENDPOINT is not set. Using default: http://fuseki:3030/ds/query")
        return v or "http://fuseki:3030/ds/query"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

try:
    settings = Settings()
except Exception as e:
    logger.warning(f"Configuration warning: {e}. Using default settings.")
    settings = Settings()