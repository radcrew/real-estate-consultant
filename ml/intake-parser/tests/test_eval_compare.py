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


class TestSkipRegressionsReachTheVerdict:
    """Finding 8. `turn_is_exact` reads no skip counter, so the gate could not see them.

    The scenario, from the review: a candidate fixes 12 field turns while ceasing to emit
    `skipped_fields` at all. 12 won / 0 lost, p ~ 0.0005, exit 0 promote -- with skip
    recall collapsed from 0.83 to 0.00 and printed two lines above the verdict.
    """

    def _pair(self, base_spec, cand_spec):
        """Each spec entry is (field_exact, skips_handled)."""
        def build(spec):
            return [
                _turn(f"t{i}", exact=field_ok, skips=(1, 0, 0) if skip_ok else (0, 0, 1))
                for i, (field_ok, skip_ok) in enumerate(spec)
            ]
        return _run("base", build(base_spec)), _run("cand", build(cand_spec))

    def test_the_review_scenario_no_longer_promotes(self, capsys):
        # 12 turns: baseline handles every skip and gets every field wrong; the candidate
        # inverts both. Fields say promote loudly; skips say the opposite just as loudly.
        base = [(False, True)] * 12
        cand = [(True, False)] * 12
        code = gate.compare(*self._pair(base, cand), alpha=0.05)
        out = capsys.readouterr().out
        assert code == 1
        assert "VERDICT reject" in out
        assert "skip handling went backwards" in out

    def test_it_says_the_fields_improved_rather_than_hiding_it(self, capsys):
        code = gate.compare(
            *self._pair([(False, True)] * 12, [(True, False)] * 12), alpha=0.05
        )
        assert code == 1
        assert "this is a trade, not a failure" in capsys.readouterr().out

    def test_a_field_win_with_skips_intact_still_promotes(self, capsys):
        code = gate.compare(
            *self._pair([(False, True)] * 12, [(True, True)] * 12), alpha=0.05
        )
        assert code == 0
        assert "VERDICT promote" in capsys.readouterr().out

    def test_a_skip_regression_too_small_to_measure_is_noted_not_rejected(self, capsys):
        # One skip lost against 11 field wins: p = 1.0 on a single discordant pair.
        base = [(False, True)] + [(False, True)] * 11
        cand = [(True, False)] + [(True, True)] * 11
        code = gate.compare(*self._pair(base, cand), alpha=0.05)
        out = capsys.readouterr().out
        assert code == 0
        assert "Skip handling fell on 1 turns" in out
        assert "not a reason to reject, and not nothing" in out.lower()

    def test_recovering_skips_is_never_a_reject(self, capsys):
        code = gate.compare(
            *self._pair([(True, False)] * 12, [(True, True)] * 12), alpha=0.05
        )
        assert code != 1

    def test_the_skip_pairing_is_reported_even_when_nothing_moved(self, capsys):
        gate.compare(*self._pair([(True, True)] * 5, [(True, True)] * 5), alpha=0.05)
        assert "paired on skip decisions" in capsys.readouterr().out


class TestSkipExactness:
    def test_a_clean_skip_turn_is_exact(self):
        assert gate.turn_skips_are_exact(_turn("t", skips=(2, 0, 0))) is True

    def test_a_missed_skip_is_not(self):
        assert gate.turn_skips_are_exact(_turn("t", skips=(0, 0, 1))) is False

    def test_an_invented_skip_is_not(self):
        assert gate.turn_skips_are_exact(_turn("t", skips=(0, 1, 0))) is False

    def test_an_errored_turn_is_not(self):
        turn = _turn("t", skips=(0, 0, 0))
        turn["error"] = "timeout"
        assert gate.turn_skips_are_exact(turn) is False

    def test_it_is_independent_of_field_correctness(self):
        """The whole point: a turn can be field-perfect and skip-wrong."""
        turn = _turn("t", exact=True, skips=(0, 0, 1))
        assert gate.turn_is_exact(turn) is True
        assert gate.turn_skips_are_exact(turn) is False


class TestF1OfZeroIsAMeasurement:
    """Finding 6. `if precision and recall` is truthiness, so 0.0 became None -> `n/a`."""

    def test_a_candidate_predicting_only_wrong_keys_scores_zero_not_n_a(self):
        # tp=0 with both fp and fn positive: precision and recall are both exactly 0.0.
        run = _run("r", [_turn("t", fields=(0, 3, 2))])
        assert gate.totals(run)["field_f1"][0] == 0.0

    def test_it_agrees_with_the_scorer_that_wrote_the_results_file(self):
        from pipeline.eval.metrics import prf

        run = _run("r", [_turn("t", fields=(0, 3, 2))])
        assert gate.totals(run)["field_f1"][0] == prf(tp=0, fp=3, fn=2)["f1"]

    def test_a_run_with_no_fields_at_all_is_genuinely_not_measured(self):
        run = _run("r", [_turn("t", fields=(0, 0, 0))])
        assert gate.totals(run)["field_f1"][0] is None

    def test_zero_prints_as_a_number(self, capsys):
        gate.compare(
            _run("base", [_turn("t", fields=(1, 0, 0))]),
            _run("cand", [_turn("t", fields=(0, 3, 2))]),
            alpha=0.05,
        )
        line = next(
            row for row in capsys.readouterr().out.splitlines() if row.startswith("field_f1")
        )
        assert "0.0000" in line and "n/a" not in line


class TestTheItemsColumnStatesOneDenominator:
    """Finding 12. Two runs' numerators were printed over the candidate's denominator."""

    def _line(self, capsys, metric):
        return next(
            row for row in capsys.readouterr().out.splitlines() if row.startswith(metric)
        )

    def test_differing_denominators_are_both_shown(self, capsys):
        gate.compare(
            _run("base", [_turn("t", values=(4, 5))]),
            _run("cand", [_turn("t", values=(6, 8))]),
            alpha=0.05,
        )
        line = self._line(capsys, "value_accuracy")
        assert "6/8 vs 4/5" in line
        assert "denominators differ" in line

    def test_a_shared_denominator_still_reads_as_items(self, capsys):
        gate.compare(
            _run("base", [_turn("t", values=(4, 8))]),
            _run("cand", [_turn("t", values=(6, 8))]),
            alpha=0.05,
        )
        line = self._line(capsys, "value_accuracy")
        assert "6 vs 4 of 8" in line
        assert "1 item = 0.1250" in line

    def test_it_never_claims_a_denominator_the_baseline_did_not_have(self, capsys):
        gate.compare(
            _run("base", [_turn("t", values=(4, 5))]),
            _run("cand", [_turn("t", values=(6, 8))]),
            alpha=0.05,
        )
        assert "6 vs 4 of 8" not in self._line(capsys, "value_accuracy")
