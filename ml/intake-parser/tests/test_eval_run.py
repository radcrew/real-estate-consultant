"""Tests for the eval harness itself -- the module that writes results.md's numbers.

`eval/run.py` was the only module here with no tests, and it is the one whose bugs are
silent: a metric that is wrong crashes nothing, it just publishes a different number. All
three defects these cover shared that shape. Nothing here touches the network; the client
is a stub, so what is being tested is the harness's own bookkeeping.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from openai import APIStatusError

from app.llm.intake.service import build_intake_messages
from app.schemas.llm_intake_parse import LlmParseModelOutput
from pipeline.eval import run as run_module
from pipeline.paths import EVAL_DATASET_PATH, QUESTIONS_PATH

QUESTIONS = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
TURNS_BY_ID = {
    row["id"]: row
    for row in (
        json.loads(line)
        for line in EVAL_DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
}


# A reply that parses and scores, so a turn's outcome is decided by the harness rather
# than by whether the fixture happens to be valid JSON.
GOOD_REPLY = json.dumps(
    {"extracted": {}, "skipped_fields": [], "missing_fields": [], "next_question": None}
)


@dataclass
class _Usage:
    prompt_tokens: int = 100
    completion_tokens: int = 20


@dataclass
class _Completion:
    choices: list[Any] = field(default_factory=list)
    usage: Any = field(default_factory=_Usage)

    @classmethod
    def of(cls, content: str) -> _Completion:
        message = SimpleNamespace(content=content)
        return cls(choices=[SimpleNamespace(message=message)])


def _status_error(code: int) -> APIStatusError:
    request = httpx.Request("POST", "http://stub/v1/chat/completions")
    return APIStatusError(
        f"stub {code}", response=httpx.Response(code, request=request), body=None
    )


class _StubClient:
    """Stands in for AsyncOpenAI. `responder` receives the 1-based call number."""

    def __init__(self, responder):
        self.calls = 0

        async def create(**request):
            self.calls += 1
            result = responder(self.calls)
            if isinstance(result, Exception):
                raise result
            return result

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def _dev_turns(n: int) -> list[dict[str, Any]]:
    rows = [t for t in TURNS_BY_ID.values() if t.get("split", "dev") == "dev"]
    assert len(rows) >= n
    return rows[:n]


async def _run(turns, responder, **kwargs):
    return await run_module.run_dataset(
        turns,
        client=_StubClient(responder),
        questions=QUESTIONS,
        model="stub",
        concurrency=1,
        duplicate_schema=False,
        json_mode=True,
        score_next_question=False,
        **kwargs,
    )


class TestAnAbortedRunSaysSo:
    """Finding 3. `aborted` was a nonlocal that got printed to stderr and dropped.

    A 401 on turn 3 of 129 wrote results/<label>.json holding 3 turns, printed a
    paste-ready results.md row whose rates were computed over those 3, and exited 0.
    Nothing in the file or the row distinguished it from a complete run, so a script
    keying on the exit code treated it as success and a human pasted the row.
    """

    ABORT_AT = 3

    def _responder(self, call: int):
        return _status_error(401) if call == self.ABORT_AT else _Completion.of(GOOD_REPLY)

    @pytest.mark.asyncio
    async def test_run_dataset_returns_the_reason(self):
        _, _, aborted = await _run(_dev_turns(10), self._responder)
        assert aborted and "401" in aborted

    @pytest.mark.asyncio
    async def test_a_clean_run_returns_no_reason(self):
        scores, _, aborted = await _run(_dev_turns(4), lambda c: _Completion.of(GOOD_REPLY))
        assert aborted is None
        assert len(scores) == 4

    @pytest.mark.asyncio
    async def test_it_stops_rather_than_burning_the_rest_of_the_set(self):
        scores, _, _ = await _run(_dev_turns(10), self._responder)
        assert len(scores) == self.ABORT_AT - 1

    @pytest.mark.asyncio
    async def test_a_non_fatal_status_is_one_bad_turn_not_an_abort(self):
        """503 is the endpoint being busy. 401 is the key being wrong."""
        scores, _, aborted = await _run(
            _dev_turns(4),
            lambda c: _status_error(503) if c == 2 else _Completion.of(GOOD_REPLY),
        )
        assert aborted is None
        assert len(scores) == 4
        assert sum(1 for s in scores if s.error) == 1


class TestAnAbortedRunDoesNotLookLikeAResult:
    """The same finding at the `main_async` level, where the damage actually lands."""

    @pytest.fixture
    def invoke(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        async def go(responder, *extra: str, out_name: str = "row.json") -> tuple[int, Path]:
            out = tmp_path / out_name
            monkeypatch.setattr(
                run_module, "AsyncOpenAI", lambda **kw: _StubClient(responder)
            )
            code = await run_module.main_async(
                ["--label", "stub", "--out", str(out), "--limit", "6",
                 "--no-next-question", *extra]
            )
            return code, out

        return go

    @pytest.mark.asyncio
    async def test_a_clean_run_exits_zero_and_writes_the_named_file(self, invoke):
        code, out = await invoke(lambda c: _Completion.of(GOOD_REPLY))
        assert code == 0
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8"))["complete"] is True

    @pytest.mark.asyncio
    async def test_an_aborted_run_exits_non_zero(self, invoke):
        code, _ = await invoke(
            lambda c: _status_error(401) if c == 3 else _Completion.of(GOOD_REPLY)
        )
        assert code == 1

    @pytest.mark.asyncio
    async def test_an_aborted_run_never_writes_the_name_a_complete_run_owns(self, invoke):
        """The default path comes from --label, so a partial re-run would replace the
        raw corpus behind a published row -- and no re-run reproduces it."""
        _, out = await invoke(
            lambda c: _status_error(401) if c == 3 else _Completion.of(GOOD_REPLY)
        )
        assert not out.exists()
        assert out.with_suffix(".partial.json").exists()

    @pytest.mark.asyncio
    async def test_the_partial_file_labels_itself(self, invoke):
        _, out = await invoke(
            lambda c: _status_error(401) if c == 3 else _Completion.of(GOOD_REPLY)
        )
        written = json.loads(out.with_suffix(".partial.json").read_text(encoding="utf-8"))
        assert written["complete"] is False
        assert "401" in written["aborted"]
        assert written["turns_scored"] == 2
        assert written["turns_requested"] == 6

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("out_name", "expected"),
        [
            ("row.json", "row.partial.json"),
            # These are the real shapes. `Path.suffix` splits on the last dot, so an --out
            # without a `.json` extension has a "suffix" of `.5b-lora-v6-q4km` -- and
            # `with_suffix` would replace it, writing `0.partial.json` and colliding every
            # aborted run onto one name.
            ("0.5b-lora-v6-q4km", "0.5b-lora-v6-q4km.partial.json"),
            ("0.5b-lora-v6-q4km.json", "0.5b-lora-v6-q4km.partial.json"),
            ("v1.2-run", "v1.2-run.partial.json"),
            ("plain", "plain.partial.json"),
        ],
    )
    async def test_the_partial_name_keeps_the_whole_label(self, invoke, out_name, expected):
        _, out = await invoke(
            lambda c: _status_error(401) if c == 3 else _Completion.of(GOOD_REPLY),
            out_name=out_name,
        )
        assert (out.parent / expected).exists(), sorted(p.name for p in out.parent.iterdir())
        assert not out.exists()

    @pytest.mark.asyncio
    async def test_no_paste_ready_row_is_offered(self, invoke, capsys):
        await invoke(lambda c: _status_error(401) if c == 3 else _Completion.of(GOOD_REPLY))
        captured = capsys.readouterr()
        assert "Paste into" not in captured.out
        assert "PARTIAL RUN" in captured.err

    @pytest.mark.asyncio
    async def test_a_clean_run_still_offers_one(self, invoke, capsys):
        await invoke(lambda c: _Completion.of(GOOD_REPLY))
        assert "Paste into" in capsys.readouterr().out


class TestAResponseWithNoChoices:
    """Finding 10. `completion.choices[0]` on a 200 carrying an empty list.

    Not a FatalRunError, so it propagated out of `worker`, through `asyncio.gather`, and
    out of `main_async` -- unlike the abort path, nothing was written at all. Hours of CPU
    serving and every other scored turn lost to a traceback.
    """

    @pytest.mark.asyncio
    async def test_it_does_not_take_the_run_down(self):
        scores, _, aborted = await _run(
            _dev_turns(5),
            lambda c: _Completion(choices=[]) if c == 2 else _Completion.of(GOOD_REPLY),
        )
        assert aborted is None
        assert len(scores) == 5

    @pytest.mark.asyncio
    async def test_the_turn_is_scored_as_an_error(self):
        scores, _, _ = await _run(
            _dev_turns(5),
            lambda c: _Completion(choices=[]) if c == 2 else _Completion.of(GOOD_REPLY),
        )
        errored = [s for s in scores if s.error]
        assert len(errored) == 1
        assert "no choices" in errored[0].error

    @pytest.mark.asyncio
    async def test_a_null_content_is_still_scored(self):
        """Distinct from an empty choices list: the reply exists and is empty."""
        scores, _, _ = await _run(
            _dev_turns(3),
            lambda c: _Completion.of(None) if c == 2 else _Completion.of(GOOD_REPLY),
        )
        assert len(scores) == 3


class TestPostProcessingScoresBothHalves:
    """Finding 4. `--post-process` rewrote `extracted` and left `skipped_fields` raw.

    The docstring's claim is "scoring this measures the product". Production recomputes
    skips as (prior | model) & required - answered; the harness did not, so a run with the
    flag on reported the product's fields beside the raw model's skips -- a pairing
    production never returns.
    """

    def _answer(self, turn_id: str, model_output: dict[str, Any]) -> LlmParseModelOutput:
        turn = TURNS_BY_ID[turn_id]
        prompt = build_intake_messages(
            user_input=turn["user_input"],
            current_criteria=turn.get("current_criteria") or {},
            questions=QUESTIONS,
        )
        parsed = LlmParseModelOutput.model_validate(
            {"missing_fields": [], "next_question": None, **model_output}
        )
        return run_module.production_answer(parsed, turn, QUESTIONS, prompt)

    def test_a_skip_the_same_turn_answers_is_dropped(self):
        """`carry-skip-unskip`: property_type was skipped earlier, this turn answers it.

        The model emitting the stale skip is charged a false positive by the raw scorer,
        though production drops it. Gold for this turn is [].
        """
        answered = self._answer(
            "carry-skip-unskip",
            {"extracted": {"property_type": ["office"]}, "skipped_fields": ["property_type"]},
        )
        assert answered.skipped_fields == []

    def test_a_skip_the_turn_does_not_answer_is_carried(self):
        """`carry-two-then-unskip`: two prior skips, one answered. Gold is ['price']."""
        answered = self._answer(
            "carry-two-then-unskip",
            {"extracted": {"property_type": ["office"]}, "skipped_fields": []},
        )
        assert answered.skipped_fields == ["price"]

    def test_a_prior_skip_survives_a_turn_that_says_nothing_about_it(self):
        answered = self._answer("carry-one-skip", {"extracted": {}, "skipped_fields": []})
        assert answered.skipped_fields == ["property_type"]

    def test_the_extracted_half_still_works(self):
        answered = self._answer(
            "carry-skip-unskip",
            {"extracted": {"property_type": ["office"]}, "skipped_fields": []},
        )
        assert answered.extracted["property_type"] == ["office"]

    def test_the_reserved_skip_key_is_not_read_as_a_criterion(self):
        """Production strips `_skipped_fields` into `criteria_for_prompt` before filtering.

        Reading `current_criteria` straight off the turn passed it through as though it
        were an answered field, which is not what production does with it.
        """
        answered = self._answer("carry-one-skip", {"extracted": {}, "skipped_fields": []})
        assert "_skipped_fields" not in answered.extracted


class TestTheRawRecordingIsAlwaysTheModelsOwnWords:
    """`--post-process` changes the score, never the corpus.

    The recordings are the evidence behind every claim in results.md. If the flag rewrote
    them, a turn's raw_output would show a reply the model never wrote.
    """

    @pytest.mark.asyncio
    async def test_post_processing_does_not_touch_raw_output(self):
        reply = json.dumps(
            {"extracted": {"property_type": ["office"]},
             "skipped_fields": ["property_type"],
             "missing_fields": [], "next_question": None}
        )
        turns = [TURNS_BY_ID["carry-one-skip"]]
        _, raw, _ = await _run(turns, lambda c: _Completion.of(reply), post_process=True)
        assert raw["carry-one-skip"] == reply
