"""The reported production bugs, as eval turns and as a check on what fixed them.

Every one of these was reported by a user against a served model, and none of them was in
the eval set — the eval was written before they were known, so the reported number could
not have caught any of them. They live in a ``regression`` split so ``dev`` and
``holdout`` keep the row counts every recorded result was measured against.

The tests below draw a line the dataset cannot: which of these the filters fix, and which
only a different model can. Running the split against the served v6 is what settled it,
and it corrected two guesses --

* ``size-lost-behind-price``, ``floors-are-not-a-size`` and ``clear-height-is-not-a-size``
  **no longer reproduce on v6**. All three were reported against a v5 endpoint that the
  ``.env`` still pointed at. Their tests below therefore check the filters against the
  output as reported, not against anything v6 emits today; they are guards, not repros.
* ``sqft-is-not-a-budget`` **does** reproduce: v6 reads the size correctly and adds a
  budget of 100000 beside it. The filters remove it.
* ``docks-are-not-a-type`` reproduces and the filters deliberately do **not** remove it.

Measured on the served v6 over this split, ``--post-process`` moves field F1 from 0.917 to
0.957 and leaves value accuracy at 1.000.
"""

from __future__ import annotations

import json

import pytest

from app.domain.intake_criteria import apply_criteria_filters
from pipeline.paths import EVAL_DATASET_PATH, QUESTIONS_PATH

QUESTIONS = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
QUESTION_KEYS = {row["key"] for row in QUESTIONS}
TURNS = {
    row["id"]: row
    for line in EVAL_DATASET_PATH.read_text(encoding="utf-8").splitlines()
    if line.strip()
    for row in [json.loads(line)]
    if row.get("split") == "regression"
}


def _production(turn_id: str, emitted: dict) -> dict:
    """``emitted`` as the intake service would leave it."""
    turn = TURNS[turn_id]
    criteria, _ = apply_criteria_filters(
        emitted, QUESTIONS, turn["user_input"],
        turn.get("current_criteria") or {}, allowed_keys=QUESTION_KEYS,
    )
    return criteria


class TestTheTurnsThemselves:
    def test_every_reported_bug_is_a_turn(self):
        assert set(TURNS) == {
            "regression-size-lost-behind-price",
            "regression-sqft-is-not-a-budget",
            "regression-docks-are-not-a-type",
            "regression-floors-are-not-a-size",
            "regression-clear-height-is-not-a-size",
        }

    @pytest.mark.parametrize("turn_id", sorted(TURNS))
    def test_a_turn_is_shaped_like_every_other_turn(self, turn_id):
        turn = TURNS[turn_id]
        assert turn["category"] == "reported-bug"
        assert isinstance(turn["user_input"], str) and turn["user_input"].strip()
        assert set(turn["gold"]) == {"extracted", "skipped_fields", "next_question_key"}
        assert set(turn["gold"]["extracted"]) <= QUESTION_KEYS

    @pytest.mark.parametrize("turn_id", sorted(TURNS))
    def test_gold_names_the_next_unanswered_required_question(self, turn_id):
        """A wrong next_question_key would score the model against a typo."""
        turn = TURNS[turn_id]
        answered = set(turn["gold"]["extracted"])
        remaining = [
            row["key"] for row in sorted(QUESTIONS, key=lambda r: r["order_index"])
            if row.get("required") and row["key"] not in answered
        ]
        assert turn["gold"]["next_question_key"] == (remaining[0] if remaining else None)


class TestFixedByTheFilters:
    """Each case is the extraction as reported, run through the production filters."""

    def test_a_size_in_square_feet_is_no_longer_also_a_budget(self):
        """The live repro: this is verbatim what the served v6 returns today. It reads
        the size correctly and puts a budget of 100000 beside it, because 100000 really
        is in the message -- as "100k sqft"."""
        criteria = _production(
            "regression-sqft-is-not-a-budget",
            {"size_sqft": {"min": 100000}, "price": {"min": 100000}},
        )
        assert "price" not in criteria

    def test_a_count_of_floors_is_no_longer_a_size(self):
        """As reported against v5. v6 does not emit this, so it guards rather than
        reproduces -- and the guard is the point: nothing else stops a storey count
        becoming a floor area."""
        criteria = _production("regression-floors-are-not-a-size", {"size_sqft": {"max": 3}})
        assert "size_sqft" not in criteria

    def test_a_clear_height_is_no_longer_a_size(self):
        """Feet, not square feet. Also a v5 report that v6 no longer produces."""
        criteria = _production(
            "regression-clear-height-is-not-a-size", {"size_sqft": {"max": 32}}
        )
        assert "size_sqft" not in criteria

    def test_a_size_stated_after_a_price_survives(self):
        """The first report: size went missing behind the price clause. v6 returns all
        four fields, so what this guards is the filters not undoing that."""
        criteria = _production(
            "regression-size-lost-behind-price",
            {"property_type": ["retail"], "location": "Texas",
             "price": {"min": 1000000}, "size_sqft": {"min": 1000}},
        )
        assert criteria == TURNS["regression-size-lost-behind-price"]["gold"]["extracted"]


class TestStillNeedsARetrainedModel:
    """The one gap the filters are not allowed to close.

    "at least 20 dock doors" names no property type, so the check abstains and the model's
    reading stands. That is deliberate: the same abstention is what lets "a depot for our
    trucks" and "a boutique on the high street" through, and a rule strict enough to drop
    ``industrial`` here drops 7 of 35 correct types elsewhere. So the value is kept and
    marked unconfirmed, and the questionnaire asks -- but the key is still there, and
    against a gold of ``{}`` it is still a false positive.

    Only a model that stops inventing a type from an attribute clause closes this, which
    is what the distractor work in 80e9c415 was for. Whether it worked is what the next
    adapter's run over this split will say.
    """

    def test_a_type_invented_from_an_attribute_clause_survives_the_filters(self):
        criteria, unconfirmed = apply_criteria_filters(
            {"property_type": ["industrial"]},
            QUESTIONS,
            TURNS["regression-docks-are-not-a-type"]["user_input"],
            {},
            allowed_keys=QUESTION_KEYS,
        )
        assert criteria == {"property_type": ["industrial"]}
        assert unconfirmed == {"property_type"}
        assert TURNS["regression-docks-are-not-a-type"]["gold"]["extracted"] == {}, (
            "gold says the message answers nothing; if this turn starts scoring a clean "
            "field F1, the retrain worked"
        )
