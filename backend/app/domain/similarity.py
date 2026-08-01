"""Cosine similarity helpers for listing embeddings."""

from __future__ import annotations

import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity in [-1, 1], or 0.0 when either vector is zero-length."""
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = 0.0
    left_norm_sq = 0.0
    right_norm_sq = 0.0
    for a, b in zip(left, right, strict=True):
        dot += a * b
        left_norm_sq += a * a
        right_norm_sq += b * b
    if left_norm_sq <= 0.0 or right_norm_sq <= 0.0:
        return 0.0
    return dot / (math.sqrt(left_norm_sq) * math.sqrt(right_norm_sq))


def similarity_to_match_score(similarity: float) -> float:
    """Map cosine similarity to the 0–100 ``match_score`` scale used by search."""
    clamped = max(0.0, min(1.0, similarity))
    return round(clamped * 100.0, 1)
