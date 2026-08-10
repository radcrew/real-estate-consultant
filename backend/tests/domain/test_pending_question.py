"""The question a turn is answering, derived rather than passed in.

Without this in the prompt, a reply of "10" to "What size are you looking for (in square
feet)?" is unattributable — nothing in the turn payload says which question was put. The
model guessed ``price``, and then echoed the stored budget back on every later turn.
"""

from app.domain.intake_next_question import pending_question_key

QUESTIONS = [
    {"key": "property_type", "order_index": 0, "required": True},
    {"key": "location", "order_index": 1, "required": True},
    {"key": "price", "order_index": 2, "required": True},
    {"key": "size_sqft", "order_index": 3, "required": True},
]
REQUIRED = [q["key"] for q in QUESTIONS]


def pending(answered=None, skipped=None):
    return pending_question_key(
        QUESTIONS,
        answered=answered or {},
        required_fields=REQUIRED,
        skipped=skipped or [],
    )


class TestOrder:
    def test_nothing_answered_gives_the_first_question(self):
        assert pending() == "property_type"

    def test_follows_questionnaire_order_not_dict_order(self):
        assert pending({"location": "Austin", "property_type": ["office"]}) == "price"

    def test_the_last_outstanding_field(self):
        answered = {"property_type": ["office"], "location": "Austin", "price": {"max": 1}}
        assert pending(answered) == "size_sqft"

    def test_none_when_everything_is_answered(self):
        assert pending({k: "x" for k in REQUIRED}) is None


class TestSkips:
    def test_a_skipped_field_is_not_pending(self):
        """It was declined, so it is never asked again — the next one is pending."""
        assert pending({"property_type": ["office"], "location": "Austin"},
                       skipped=["price"]) == "size_sqft"

    def test_none_when_the_rest_are_skipped(self):
        assert pending({"property_type": ["office"]},
                       skipped=["location", "price", "size_sqft"]) is None

    def test_answered_wins_over_skipped(self):
        """A field the user later answered is no longer outstanding either way."""
        assert pending({"property_type": ["office"], "price": {"max": 1}},
                       skipped=["price"]) == "location"


class TestEdges:
    def test_an_optional_field_is_never_pending(self):
        questions = [*QUESTIONS, {"key": "extras", "order_index": 4, "required": False}]
        assert pending_question_key(
            questions, answered={k: "x" for k in REQUIRED}, required_fields=REQUIRED, skipped=[]
        ) is None

    def test_a_required_key_with_no_configured_row_is_ignored(self):
        """Guards against a required_fields list drifting from the questionnaire."""
        assert pending_question_key(
            QUESTIONS,
            answered={k: "x" for k in REQUIRED},
            required_fields=[*REQUIRED, "ghost_field"],
            skipped=[],
        ) is None

    def test_no_questions_at_all(self):
        assert pending_question_key([], answered={}, required_fields=[], skipped=[]) is None


class TestItReachesThePrompt:
    def test_the_turn_payload_carries_it(self):
        import json

        from app.llm.intake.service import build_intake_messages

        rows = [{**q, "type": "text", "title": q["key"]} for q in QUESTIONS]
        prompt = build_intake_messages(
            user_input="10",
            current_criteria={"property_type": ["industrial"], "location": "Austin"},
            questions=rows,
        )
        payload = json.loads(prompt.messages[1]["content"])
        assert payload["pending_question"] == "price"

    def test_it_is_null_rather_than_absent_when_nothing_is_outstanding(self):
        """A missing key and a null one read differently to the model."""
        import json

        from app.llm.intake.service import build_intake_messages

        rows = [{**q, "type": "text", "title": q["key"]} for q in QUESTIONS]
        prompt = build_intake_messages(
            user_input="thanks",
            current_criteria={k: "x" for k in REQUIRED},
            questions=rows,
        )
        payload = json.loads(prompt.messages[1]["content"])
        assert "pending_question" in payload
        assert payload["pending_question"] is None
