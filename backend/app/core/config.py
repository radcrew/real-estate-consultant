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
    # USD per 1M tokens, for cost-attribution telemetry. 0 disables cost estimates.
    hf_input_cost_per_1m: float = 0.0
    hf_output_cost_per_1m: float = 0.0

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

    # Region for both Bedrock clients. Required: neither boto3 nor the Anthropic Bedrock
    # client applies a default. Credentials are resolved by the standard boto3 chain
    # (env vars on Vercel, instance/task role on AWS compute) and so are not repeated here.
    aws_region: str = ""

    # Chat runs on the Bedrock Messages API endpoint, whose model IDs carry an `anthropic.`
    # prefix and no date suffix. Embeddings run on bedrock-runtime InvokeModel, whose IDs
    # are versioned instead. The two conventions are not interchangeable.
    bedrock_chat_model: str = "anthropic.claude-sonnet-5"
    bedrock_effort: str = "low"
    # Adaptive thinking is on by default on Claude 5 models and counts against max_tokens.
    # Callers size max_tokens for models without thinking, so leave it off for extraction.
    bedrock_disable_thinking: bool = True
    bedrock_embedding_model: str = "cohere.embed-english-v3"
    # Cohere Embed v3 accepts roughly 96 texts per InvokeModel call.
    bedrock_embedding_batch_size: int = 96
    bedrock_input_cost_per_1m: float = 0.0
    bedrock_output_cost_per_1m: float = 0.0

    # Qwen chat runs on the Converse API, which is vendor-neutral: the Anthropic SDK
    # behind bedrock_chat cannot call non-Anthropic models. Converse IDs are versioned.
    bedrock_qwen_chat_model: str = "qwen.qwen3-32b-v1:0"
    # Qwen3 is a hybrid-thinking family, and thinking is billed against maxTokens for no
    # benefit on a structured draft. The switch is model-revision specific, so set this
    # false to omit the field entirely if a deployed revision rejects it.
    bedrock_qwen_disable_thinking: bool = True
    bedrock_qwen_input_cost_per_1m: float = 0.0
    bedrock_qwen_output_cost_per_1m: float = 0.0

    # The fine-tuned Qwen2.5-0.5B criteria extractor, self-hosted on Lambda and invoked
    # over IAM. An empty name disables the provider the same way a blank region does.
    qwen_inference_function_name: str = ""
    # Recorded on every llm_call, so "did the retrain regress intake parsing?" is a
    # dashboard question rather than a deploy.
    qwen_model_version: str = ""

    # Per-call-site provider routing (see app/llm/providers/routing.py). "auto" keeps the
    # key-presence order in providers/chat.py, so routing is opt-in and metered providers
    # are never selected by accident. Any other value pins that path to one provider.
    llm_route_intake_parse: str = "auto"
    llm_route_opening_question: str = "auto"
    llm_route_fit_explanation: str = "auto"
    llm_route_outreach_draft: str = "auto"
    llm_route_default: str = "auto"
    # Embeddings has a single call site, so one pin rather than a per-task table. An
    # explicit pin is the only way to reach Bedrock while HF_TOKEN is set, since
    # key-presence order deliberately checks Bedrock last.
    llm_route_embeddings: str = "auto"

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

    # Admission control for the anonymous, LLM-backed intake routes (see
    # core/intake_admission.py). Sessions cost money per request and carry no identity,
    # so the address budget is the real ceiling; the session budget only paces one
    # conversation. Both are per process, so the effective limit scales with instances.
    intake_ip_rate_limit_per_minute: int = 60
    intake_session_rate_limit_per_minute: int = 12

    # FIFO queue carrying LLM intake turns to the Lambda consumer. Empty disables
    # queueing and the endpoint runs the turn inline — which is what local dev and the
    # test suite do, so neither needs a queue to exist.
    sqs_chat_queue_url: str = ""

    # Populated automatically by Vercel; set manually for other hosts.
    git_sha: str = Field(
        default="", validation_alias=AliasChoices("GIT_SHA", "VERCEL_GIT_COMMIT_SHA")
    )



settings = Settings()
