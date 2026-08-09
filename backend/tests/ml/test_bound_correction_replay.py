"""Replay recorded eval outputs through the bound-direction corrector.

``ml/eval/results/*.json`` stores the raw reply for every scored turn, which makes it a
free corpus of real model mistakes. The corrector is a heuristic over message text, so
the risk that matters is not "does it fix things" but "does it break things it should
have left alone" — and these recordings are the only place that question can be asked
against real output rather than invented examples.

The invariant is one-directional: for every recorded turn, correcting must not reduce the
number of values that match gold. It may leave a turn untouched, and usually does.

Turn ids absent from the current ``dataset.jsonl`` are skipped, so an older revision's
results file (r1's 52 turns, or a row scored before turns were renamed) neither fails nor
silently vanishes from the count.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.domain.bounds import correct_bound_direction
from ml.eval.metrics import values_equal
from ml.paths import EVAL_DATASET_PATH, RESULTS_DIR

RESULTS = sorted(RESULTS_DIR.glob("*.json"))


@pytest.fixture(scope="module")
def gold_by_id() -> dict[str, dict[str, Any]]:
    lines = EVAL_DATASET_PATH.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    return {row["id"]: row for row in rows}


def _matching_values(extracted: dict[str, Any], gold: dict[str, Any]) -> int:
    """Values that agree with gold, scored the way ``ml/eval`` scores them."""
    return sum(
        1 for key in set(extracted) & set(gold) if values_equal(gold[key], extracted[key])
    )


def _replay(path: Path, gold_by_id: dict[str, Any]) -> tuple[int, int, list[str]]:
    """Return (turns improved, turns worsened, ids worsened) for one results file."""
    run = json.loads(path.read_text(encoding="utf-8"))
    improved, worsened, offenders = 0, 0, []
    for turn in run["turns"]:
        row = gold_by_id.get(turn["turn_id"])
        if row is None:
            continue
        try:
            raw = json.loads(turn["raw_output"]).get("extracted", {})
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(raw, dict):
            continue
        gold = row["gold"]["extracted"]
        fixed = correct_bound_direction(raw, row["user_input"])
        if fixed == raw:
            continue
        before, after = _matching_values(raw, gold), _matching_values(fixed, gold)
        if after > before:
            improved += 1
        elif after < before:
            worsened += 1
            offenders.append(turn["turn_id"])
    return improved, worsened, offenders


@pytest.mark.skipif(not RESULTS, reason="no recorded eval runs")
@pytest.mark.parametrize("path", RESULTS, ids=lambda p: p.stem)
def test_correction_never_worsens_a_recorded_turn(path, gold_by_id):
    _, worsened, offenders = _replay(path, gold_by_id)
    assert worsened == 0, f"{path.stem}: correction made {worsened} turn(s) worse: {offenders}"


@pytest.mark.skipif(not RESULTS, reason="no recorded eval runs")
def test_correction_is_doing_something(gold_by_id):
    """A corrector that never fires would pass the invariant above trivially."""
    total = sum(_replay(path, gold_by_id)[0] for path in RESULTS)
    assert total > 0, "no recorded turn was improved — is the corrector still wired up?"
