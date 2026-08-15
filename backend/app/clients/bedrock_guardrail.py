"""Bedrock Guardrails screening for intake free text.

``ApplyGuardrail`` evaluates text on its own, without invoking a model, so one policy
covers every path — the Qwen Lambda, Bedrock, OpenRouter — rather than each provider
needing its own filter.

This exists for the intake path specifically: users describe budget, location and
personal circumstances in free text, and that text is persisted (the job row, the session
criteria) and passed to third-party providers. PII redaction is the piece that is
genuinely hard to build yourself.

Priced per text unit, so the whole feature is opt-in: an empty ``BEDROCK_GUARDRAIL_ID``
disables it and screening becomes a pass-through.
"""

from __future__ import annotations

import logging
from functools import partial
from typing import Any, Literal, NamedTuple

import anyio.to_thread
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings, settings
from app.llm.providers.exceptions import raise_guardrail_unavailable

GUARDRAIL_CONNECT_TIMEOUT = 10.0
GUARDRAIL_READ_TIMEOUT = 20.0
GUARDRAIL_TRANSIENT_RETRIES = 2

GuardrailSource = Literal["INPUT", "OUTPUT"]

logger = logging.getLogger(__name__)


class GuardrailOutcome(NamedTuple):
    """``text`` is the version safe to keep — masked when a policy anonymised it."""

    text: str
    blocked: bool


def contains_blocked(node: Any) -> bool:
    """Whether any assessment says a policy *blocked* rather than anonymised.

    Assessment shapes differ per policy type (topic, content, word, sensitive
    information) and have gained fields over time, so this walks the structure looking
    for the verdict instead of hard-coding one policy's layout — a new policy type would
    otherwise read as "not blocked".
    """
    if isinstance(node, dict):
        if node.get("action") == "BLOCKED":
            return True
        return any(contains_blocked(value) for value in node.values())
    if isinstance(node, list):
        return any(contains_blocked(item) for item in node)
    return False


class BedrockGuardrail:
    """Applies one guardrail policy to a piece of text."""

    def __init__(self, *, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self._client = client

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.bedrock_guardrail_id.strip()
            and self.settings.aws_region.strip()
        )

    @property
    def client(self) -> Any:
        """Built on first use — boto3 raises on a blank region, including in CI."""
        if self._client is None:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.settings.aws_region,
                config=Config(
                    connect_timeout=GUARDRAIL_CONNECT_TIMEOUT,
                    read_timeout=GUARDRAIL_READ_TIMEOUT,
                    retries={"max_attempts": GUARDRAIL_TRANSIENT_RETRIES, "mode": "standard"},
                ),
            )
        return self._client

    def _apply(self, text: str, source: GuardrailSource) -> dict[str, Any]:
        """Blocking ``ApplyGuardrail`` — always run via ``anyio.to_thread``."""
        return self.client.apply_guardrail(
            guardrailIdentifier=self.settings.bedrock_guardrail_id,
            guardrailVersion=self.settings.bedrock_guardrail_version,
            source=source,
            content=[{"text": {"text": text}}],
        )

    async def screen(self, text: str, *, source: GuardrailSource) -> GuardrailOutcome:
        """Return the text to keep, and whether the policy refused it outright.

        On a guardrail outage this **fails closed** by default: a screening control that
        silently stops screening is worse than an error, because the PII it exists to
        catch flows into storage with nothing recording that it was never checked. Set
        ``BEDROCK_GUARDRAIL_FAIL_OPEN=true`` to prefer availability instead — a
        deliberate, reversible choice rather than an accident of error handling.
        """
        if not self.enabled or not text.strip():
            return GuardrailOutcome(text=text, blocked=False)

        try:
            response = await anyio.to_thread.run_sync(partial(self._apply, text, source))
        except (ClientError, BotoCoreError) as exc:
            logger.warning("guardrail_unavailable", extra={"source": source})
            if self.settings.bedrock_guardrail_fail_open:
                return GuardrailOutcome(text=text, blocked=False)
            raise_guardrail_unavailable(cause=exc)

        if not isinstance(response, dict) or response.get("action") != "GUARDRAIL_INTERVENED":
            return GuardrailOutcome(text=text, blocked=False)

        assessments = response.get("assessments") or []
        blocked = contains_blocked(assessments)
        outputs = response.get("outputs") or []
        masked = outputs[0].get("text") if outputs and isinstance(outputs[0], dict) else None
        logger.info(
            "guardrail_intervened",
            extra={"source": source, "blocked": blocked, "masked": bool(masked)},
        )
        # A blocked verdict has no usable replacement, so keep the original for the caller
        # to discard rather than storing a policy message as though the user wrote it.
        return GuardrailOutcome(
            text=text if blocked or not isinstance(masked, str) else masked,
            blocked=blocked,
        )


bedrock_guardrail = BedrockGuardrail(settings=settings)
