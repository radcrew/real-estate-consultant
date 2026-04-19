from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Real Estate Consultant API"
    version: str = "0.1.0"
    is_dev_mode: bool = Field(
        default=False,
        validation_alias=AliasChoices("IS_DEV_MODE", "DEBUG"),
        description="Reserved for future dev-only behavior (not used by the API today).",
    )

    database_url: str

    supabase_url: str
    supabase_service_role_key: str
    signup_email_confirm: bool = True


settings = Settings()
