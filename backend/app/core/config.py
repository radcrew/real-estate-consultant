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
    # How long asyncpg waits to establish a connection, and the per-statement timeout.
    # Both prevent a flaky DB call from stalling until Vercel's hard function kill.
    db_connect_timeout_s: float = 10.0
    db_statement_timeout_ms: int = 30_000
    # Set to true when DATABASE_URL points to Supabase's pgbouncer (port 6543).
    # Enables NullPool (no idle connections between invocations) and disables asyncpg
    # prepared statements, which pgbouncer transaction mode does not support.
    db_serverless: bool = False

    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str = ""
    signup_email_confirm: bool = True

    # Browser origins allowed to call the API (comma-separated). Example: Next dev or prod web URL.
    frontend_origin: str = "http://localhost:3000"

    hf_token: str = ""
    hf_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    hf_base_url: str = "https://router.huggingface.co/v1"
    # USD per 1M tokens, for cost-attribution telemetry. 0 disables cost estimates.
    hf_input_cost_per_1m: float = 0.0
    hf_output_cost_per_1m: float = 0.0

    log_level: str = "INFO"

    # URL of the ingestion microservice (Phase 3). Empty string disables the feature.
    ingestion_service_url: str = ""
    # Bearer token sent to the ingestion service (must match its SERVICE_AUTH_TOKEN).
    ingestion_service_token: str = ""

    # Populated automatically by Vercel; set manually for other hosts.
    git_sha: str = Field(
        default="", validation_alias=AliasChoices("GIT_SHA", "VERCEL_GIT_COMMIT_SHA")
    )



settings = Settings()
