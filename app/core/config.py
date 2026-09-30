"""Application configuration and settings."""

import json
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "Mediate Healthcare MR App"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # Server binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: list[str] | str = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: list[str] | str) -> list[str]:
        """Ensure ALLOWED_ORIGINS is always returned as a list of strings."""
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(i) for i in parsed]
                except Exception:
                    pass
            return [item.strip() for item in v_stripped.split(",") if item.strip()]
        return v

    # Database
    DATABASE_URL: str = (
        "mssql+pyodbc://sa:YourStrongPassword123!@localhost:1433/mediate_db"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Security & Auth
    SECRET_KEY: str = "development-secret-key-change-in-production-must-be-32-chars-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 2

    # Storage
    STORAGE_PROVIDER: Literal["local", "s3", "azure"] = "local"
    LOCAL_STORAGE_PATH: str = "./storage"

    # Geofence Defaults
    DEFAULT_GEOFENCE_DOCTOR_RADIUS_METERS: float = 200.0
    DEFAULT_GEOFENCE_CHEMIST_RADIUS_METERS: float = 150.0
    MAX_LOCATION_ACCURACY_THRESHOLD_METERS: float = 100.0


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
