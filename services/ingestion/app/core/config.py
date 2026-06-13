from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_SVC_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_SVC_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Real Estate Ingestion Service"
    version: str = "0.1.0"

    supabase_url: str
    supabase_service_role_key: str

    # Path to the raw listing JSON file used by the loopnet-seed connector.
    # For local dev point at ../../backend/dataset/raw-data.json if needed.
    dataset_path: str = "dataset/raw-data.json"

    log_level: str = "INFO"

    # Set to the CRON_SECRET Vercel injects on cron requests (leave empty to skip auth).
    cron_secret: str = ""

    # Shared bearer token the backend sends when calling this service directly.
    # See app/core/auth.py for the rotation procedure.
    service_auth_token: str = ""
    service_auth_token_next: str = ""

    # Outbound rate limiting for HTTP-fetching connectors ("polite ingestion").
    # See app/connectors/rate_limit.py.
    connector_max_concurrency: int = 2
    connector_rate_per_second: float = 1.0

    git_sha: str = Field(
        default="", validation_alias=AliasChoices("GIT_SHA", "VERCEL_GIT_COMMIT_SHA")
    )


settings = Settings()
