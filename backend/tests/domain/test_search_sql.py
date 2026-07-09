"""Tests for app.domain.search_sql (score expression building)."""
from __future__ import annotations

from typing import Any

from app.domain.search_sql import component_score_exprs, match_score_expr


def _sql(expr: Any) -> str:
    """Render an expression to SQL text with literal values inlined."""
    return str(expr.compile(compile_kwargs={"literal_binds": True}))


class TestComponentScoreExprs:
    def test_returns_three_expressions(self):
        components = component_score_exprs({"location": "Austin"})
        assert len(components) == 3

    def test_neutral_without_matching_criteria(self):
        loc, price, size = component_score_exprs({})
        # No target -> Gaussian components are neutral (1.0); location falls
        # back to the "no criteria" branch (also 1.0).
        neutral = "CAST(1.0 AS FLOAT)"
        assert _sql(loc) == neutral
        assert _sql(price) == neutral
        assert _sql(size) == neutral


class TestMatchScoreExpr:
    def test_reuses_component_score_exprs(self):
        criteria = {
            "location": "Austin",
            "price": {"min": 100_000, "max": 300_000},
            "size_sqft": {"min": 1_000, "max": 5_000},
        }
        loc, price, size = component_score_exprs(criteria)
        total_sql = _sql(match_score_expr(criteria))

        # The blended total must be built from the exact same sub-expressions
        # component_score_exprs() returns, not a re-derived duplicate.
        assert _sql(loc) in total_sql
        assert _sql(price) in total_sql
        assert _sql(size) in total_sql
