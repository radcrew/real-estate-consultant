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
    # Both http and https localhost are allowed by default so the Next dev server
    # works whether or not it's started with --experimental-https.
    frontend_origin: str = "http://localhost:3000,https://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        """`frontend_origin` parsed into a de-duplicated list of allowed origins."""
        seen: dict[str, None] = {}
        for origin in self.frontend_origin.split(","):
            trimmed = origin.strip().rstrip("/")
            if trimmed:
                seen.setdefault(trimmed, None)
        return list(seen)

    hf_token: str = Field(default="", validation_alias=AliasChoices("HF_TOKEN", "hf_token"))
    hf_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_base_url: str = "https://router.huggingface.co/v1"
    # Embeddings speak HF's feature-extraction protocol, which llama.cpp does not
    # implement, so their base URL is separate from chat's. Without this, pointing
    # intake at a self-hosted server would silently break embeddings.
    hf_embedding_base_url: str = "https://router.huggingface.co/v1"
    # USD per 1M tokens, for cost-attribution telemetry. 0 disables cost estimates.
    hf_input_cost_per_1m: float = 0.0
    hf_output_cost_per_1m: float = 0.0

    # Per-task override for intake criteria extraction only. Empty means "use the
    # default chat provider", so unset behaviour is byte-identical to before.
    # Clearing these is the rollback: env change and redeploy, no code revert.
    intake_chat_model: str = ""
    intake_chat_base_url: str = ""
    # Its own credential. The provider sends one bearer token for whatever host it is
    # pointed at, so without this the self-hosted box would receive HF_TOKEN.
    intake_chat_api_key: str = ""

    @property
    def intake_chat_override(self) -> tuple[str, str, str] | None:
        """Return (model, base_url, api_key) when intake is pinned elsewhere, else None."""
        model = self.intake_chat_model.strip()
        base_url = self.intake_chat_base_url.strip()
        if not model or not base_url:
            return None
        return model, base_url, self.intake_chat_api_key.strip()

    # Chat: OPENROUTER_API_KEY wins over HF_TOKEN when both are set (see llm.providers.chat).
    # Embeddings: HF_TOKEN wins when both are set (see llm.providers.embeddings).
    openrouter_api_key: str = Field(
        default="", validation_alias=AliasChoices("OPENROUTER_API_KEY", "openrouter_api_key")
    )
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_chat_model: str = "meta-llama/llama-3.1-8b-instruct"
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    openrouter_http_referer: str = ""
    openrouter_app_title: str = "Real Estate Consultant"
    openrouter_input_cost_per_1m: float = 0.0
    openrouter_output_cost_per_1m: float = 0.0

    log_level: str = "INFO"

    # SolarWinds Observability bulk HTTP log ingestion. Leave blank to disable.
    swo_logs_url: str = ""
    swo_token: str = ""

    # URL of the ingestion microservice (Phase 3). Empty string disables the feature.
    ingestion_service_url: str = ""
    # Bearer token sent to the ingestion service (must match its SERVICE_AUTH_TOKEN).
    ingestion_service_token: str = ""

    # Pepper for MCP API key hashing (sha256 of pepper||raw_key). Empty allowed in local tests.
    mcp_api_key_pepper: str = ""
    # Per-key sliding-window limit for MCP API key auth (single process).
    mcp_api_key_rate_limit_per_minute: int = 120

    # Populated automatically by Vercel; set manually for other hosts.
    git_sha: str = Field(
        default="", validation_alias=AliasChoices("GIT_SHA", "VERCEL_GIT_COMMIT_SHA")
    )



settings = Settings()
