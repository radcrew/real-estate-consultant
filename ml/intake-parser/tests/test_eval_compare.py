"""Tests for the promote/reject gate.

The gate's job is to be right about *not knowing*. Two adapters differing by seven items
out of a hundred look different in a table and are not, and the failure that matters here
is answering confidently either way.
"""

from __future__ import annotations

import json

import pytest

from pipeline.eval import compare as gate


def _turn(turn_id, *, exact=True, values=(1, 1), skips=(0, 0, 0), fields=(1, 0, 0)):
    correct, compared = values
    tp, fp, fn = fields
    skip_tp, skip_fp, skip_fn = skips
    if not exact:
        fp = max(fp, 1)
    return {
        "turn_id": turn_id, "category": "single-field", "error": None,
        "schema_valid": True, "raw_json_valid": True,
        "field_tp": tp, "field_fp": fp, "field_fn": fn, "invented_keys": 0,
        "value_correct": correct, "value_compared": compared,
        "skip_tp": skip_tp, "skip_fp": skip_fp, "skip_fn": skip_fn,
        "next_question_correct": None, "latency_ms": 1.0, "raw_output": "{}",
    }


def _run(label, turns, *, dataset_sha="abc", post_process=False):
    return {
        "label": label, "model": "m", "split": "dev", "post_process": post_process,
        "dataset": {"path": "d.jsonl", "sha256": dataset_sha, "rows": len(turns)},
        "by_category": {}, "turns": turns,
    }


class TestExactTurns:
    def test_a_turn_with_every_value_right_and_no_stray_keys_is_exact(self):
        assert gate.turn_is_exact(_turn("t", values=(3, 3))) is True

    def test_a_spurious_key_is_not_exact(self):
        assert gate.turn_is_exact(_turn("t", fields=(1, 1, 0))) is False

    def test_a_missing_key_is_not_exact(self):
        assert gate.turn_is_exact(_turn("t", fields=(1, 0, 1))) is False

    def test_a_wrong_value_is_not_exact(self):
        assert gate.turn_is_exact(_turn("t", values=(2, 3))) is False

    def test_an_errored_turn_is_not_exact(self):
        turn = _turn("t")
        turn["error"] = "timeout"
        assert gate.turn_is_exact(turn) is False


class TestTheExactTest:
    """McNemar over discordant pairs. Values checked by hand against the binomial."""

    @pytest.mark.parametrize(("wins", "trials", "expected"), [
        (0, 0, 1.0),        # nothing disagreed
        (1, 1, 1.0),        # one disagreement says nothing
        (6, 7, 0.125),      # the v5 pair
        (4, 13, 0.2668),    # v6 against its regenerated retrain
        (10, 10, 0.0020),   # ten out of ten is a result
    ])
    def test_the_p_value(self, wins, trials, expected):
        assert gate._binomial_two_sided(wins, trials) == pytest.approx(expected, abs=5e-5)

    def test_agreements_carry_no_information(self):
        """Turns both runs get right, or both get wrong, cannot separate them."""
        base = {"a": True, "b": False, "c": True}
        cand = {"a": True, "b": False, "c": False}
        result = gate.mcnemar(base, cand)
        assert result["lost"] == ["c"]
        assert result["won"] == []
        assert result["discordant"] == 1

    def test_only_shared_turns_are_paired(self):
        result = gate.mcnemar({"a": True, "x": True}, {"a": False, "y": True})
        assert result["discordant"] == 1


class TestRefusals:
    def test_it_will_not_compare_across_dataset_revisions(self, capsys):
        """The confound that produced the most misleading row in the results table."""
        code = gate.compare(
            _run("a", [_turn("t")], dataset_sha="one"),
            _run("b", [_turn("t")], dataset_sha="two"),
            alpha=0.05,
        )
        assert code == 2
        assert "different dataset revisions" in capsys.readouterr().out

    def test_it_will_not_compare_different_turn_sets(self, capsys):
        code = gate.compare(_run("a", [_turn("x")]), _run("b", [_turn("y")]), alpha=0.05)
        assert code == 2
        assert "different turns" in capsys.readouterr().out

    def test_it_will_not_compare_the_model_against_the_product(self, capsys):
        """One run post-processed and one not measures two different things."""
        code = gate.compare(
            _run("a", [_turn("t")]),
            _run("b", [_turn("t")], post_process=True),
            alpha=0.05,
        )
        assert code == 2
        assert "post-processed" in capsys.readouterr().out

    def test_an_unstamped_run_warns_rather_than_refusing(self, capsys):
        """Refusing would make every historical comparison impossible."""
        old = _run("a", [_turn("t")])
        del old["dataset"]
        code = gate.compare(old, _run("b", [_turn("t")]), alpha=0.05)
        assert code == 2  # identical turns, so "cannot say" for a different reason
        assert "predates dataset stamping" in capsys.readouterr().out


class TestVerdicts:
    def _pair(self, baseline_exact, candidate_exact):
        base = [_turn(f"t{i}", exact=flag) for i, flag in enumerate(baseline_exact)]
        cand = [_turn(f"t{i}", exact=flag) for i, flag in enumerate(candidate_exact)]
        return _run("base", base), _run("cand", cand)

    def test_identical_runs_cannot_say(self, capsys):
        code = gate.compare(*self._pair([True] * 5, [True] * 5), alpha=0.05)
        assert code == 2
        assert "agree on every turn" in capsys.readouterr().out

    def test_a_seven_item_swing_is_not_a_result(self, capsys):
        """The shape of the regression that cost a training cycle."""
        code = gate.compare(
            *self._pair([True] * 9 + [False] * 4, [False] * 9 + [True] * 4), alpha=0.05
        )
        assert code == 2
        assert "what a coin produces" in capsys.readouterr().out

    def test_a_lopsided_loss_is_rejected(self, capsys):
        code = gate.compare(*self._pair([True] * 10, [False] * 10), alpha=0.05)
        assert code == 1
        assert "VERDICT reject" in capsys.readouterr().out

    def test_a_lopsided_win_is_promoted_but_flagged(self, capsys):
        code = gate.compare(*self._pair([False] * 10, [True] * 10), alpha=0.05)
        out = capsys.readouterr().out
        assert code == 0
        assert "VERDICT promote" in out
        assert "UNATTRIBUTED" in out, "training variance is still unmeasured"


class TestLoading:
    def test_a_run_loads_by_path(self, tmp_path):
        path = tmp_path / "r.json"
        path.write_text(json.dumps(_run("a", [_turn("t")])), encoding="utf-8")
        assert gate.load_run(str(path))["label"] == "a"

    def test_a_missing_run_is_a_clear_error(self):
        with pytest.raises(SystemExit, match="no results at"):
            gate.load_run("definitely-not-a-label")
