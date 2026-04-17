from pathlib import Path

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
    debug: bool = False

    database_url: str

    supabase_url: str
    supabase_service_role_key: str
    signup_email_confirm: bool = True


settings = Settings()
