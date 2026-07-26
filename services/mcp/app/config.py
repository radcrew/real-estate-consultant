from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_SVC_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_SVC_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Empty process env (common from Cursor mcp.json) must not wipe .env values.
        env_ignore_empty=True,
    )

    app_name: str = "radestate"
    version: str = "0.1.0"

    backend_api_url: str = "http://127.0.0.1:8888"
    mcp_user_access_token: str = ""
    mcp_transport: str = "stdio"  # stdio | streamable-http
    mcp_http_host: str = "127.0.0.1"
    mcp_http_port: int = Field(default=8900, ge=1, le=65535)
    http_timeout_seconds: float = Field(default=60.0, gt=0)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    max_tool_output_chars: int = Field(default=24_000, ge=1000)
    log_level: str = "INFO"


settings = Settings()
