from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_SVC_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_SVC_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "radestate"
    version: str = "0.1.0"

    backend_api_url: str = "http://127.0.0.1:8888"
    mcp_user_access_token: str = ""
    mcp_transport: str = "stdio"
    http_timeout_seconds: float = Field(default=60.0, gt=0)
    log_level: str = "INFO"


settings = Settings()
