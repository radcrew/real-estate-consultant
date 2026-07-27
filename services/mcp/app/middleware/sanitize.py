"""Sanitize tool outputs before they re-enter model context."""

from __future__ import annotations

import re

# Patterns that look like secrets accidentally echoed from upstream errors/payloads.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),  # JWT
    re.compile(r"\brad_[A-Za-z0-9_-]{16,}\b"),  # MCP API keys
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)service[_-]?role[_-]?key\s*[:=]\s*\S+"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*\S+"),
)

# Soft-neutralize common indirect prompt-injection phrases in untrusted text.
_INJECTION_PHRASES: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?"),
    re.compile(r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+instructions?"),
    re.compile(r"(?i)system\s*prompt\s*:"),
    re.compile(r"(?i)<\|?(system|im_start|im_end)\|?>"),
    re.compile(r"(?i)you\s+are\s+now\s+(?:a|an|the)\s+"),
)


def redact_secrets(text: str) -> str:
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def neutralize_injection_phrases(text: str) -> str:
    out = text
    for pattern in _INJECTION_PHRASES:
        out = pattern.sub("[filtered]", out)
    return out


def sanitize_tool_text(text: str, *, max_chars: int) -> str:
    """Redact secrets, soften injection markers, and cap size."""
    cleaned = neutralize_injection_phrases(redact_secrets(text))
    if len(cleaned) > max_chars:
        # Keep headroom for the suffix; avoid negative slices when max_chars is small.
        cleaned = cleaned[: max(0, max_chars - 20)] + "\n…[truncated]"
    return cleaned
