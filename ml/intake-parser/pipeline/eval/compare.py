"""Decide whether one adapter beats another, mechanically.

    python -m pipeline.eval.compare v6-q4km r8-v7-q4km
    python -m pipeline.eval.compare results/a.json results/b.json --alpha 0.05

Exit codes: 0 promote, 1 reject, 2 cannot say. The third is the useful one.

The last retrain would have been rejected by any gate at all — 0.851 against 0.912 — and
that would have been known before anyone else noticed. But a gate needs a threshold, and
the naive one is wrong in a specific way worth spelling out.

Value accuracy runs over about 102 comparisons, so a single item is worth 0.0098. The
"regression" that cost a cycle was 93 correct against 86: **seven items**. Skip recall has
41 denominators, so its seven items were 0.171 of the metric. Differences that small are
routinely produced by nothing at all, and a gate comparing two rates cannot tell you
which kind of difference it is looking at.

**Two sources of variance, and only one of them is measurable here.**

*Eval-set noise* — 129 turns is a sample, and the same pair of adapters scored on a
different 129 turns would differ. This is measurable from the runs themselves, because
both scored the same turns: the comparison is **paired**, so the question is not "are
these two rates far apart" but "of the turns where the two disagree, is the split lopsided
enough to be surprising". That is McNemar's test, and it is exact for these counts. It is
computed below.

*Training variance* — shuffle and seed produce different adapters from identical data, and
we have never trained two adapters on the same data to find out how different. That number
is **not** in these files and cannot be derived from them. Until 2-3 adapters are trained
on identical data with different seeds, a small difference cannot be attributed to the
change under test.

So the verdict here is deliberately conservative: a difference that does not clear
eval-set noise is reported as *cannot say* rather than as a pass or a fail, and even a
difference that does clear it is flagged as unattributed while the training floor is
unknown. A gate that answers confidently on an unmeasured threshold rejects good adapters
and passes bad ones with equal confidence.

**Two paired tests, not one.** Whole-turn correctness and skip handling are scored
separately, because a turn can be exact on every field and still fail the user: nothing in
``turn_is_exact`` reads a skip counter, so a candidate that stopped emitting
``skipped_fields`` entirely -- skip recall 0.83 to 0.00 -- once cleared this gate on field
wins alone. Skip recall was printed directly above the verdict the whole time. A measured
skip regression is now a reject on its own, whatever the field test says; an unmeasurable
one is printed under the promote rather than swallowed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from pipeline.eval.metrics import prf, ratio
from pipeline.paths import RESULTS_DIR

# Metrics a candidate must not go backwards on, in the order they are reported.
HEADLINE = ("turn_exact", "value_accuracy", "skip_recall", "field_f1")


def load_run(reference: str) -> dict[str, Any]:
    """A results file by path, or by the label it was recorded under."""
    path = Path(reference)
    if not path.exists():
        path = RESULTS_DIR / f"{reference}.json"
    if not path.exists():
        raise SystemExit(f"no results at {reference} or {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def turn_is_exact(turn: dict[str, Any]) -> bool:
    """Whether the turn came out entirely right: every key, every value.

    The metric a user experiences. It is also the only per-turn number here that is
    binary, which is what makes the paired test below exact rather than approximate.
    """
    return bool(
        not turn.get("error")
        and turn.get("schema_valid")
        and turn.get("field_fp", 0) == 0
        and turn.get("field_fn", 0) == 0
        and turn.get("value_correct", 0) == turn.get("value_compared", 0)
    )


def turn_skips_are_exact(turn: dict[str, Any]) -> bool:
    """Whether the turn's skip decisions came out right: none missed, none invented.

    Separate from ``turn_is_exact``, which is documented as "every key, every value" and
    is the number every historical row was computed with -- folding skips into it would
    silently redefine a published metric. This is a second binary per-turn outcome, so the
    same exact paired test applies to it without any new statistics.

    It exists because the verdict read only field outcomes. A candidate could stop
    emitting ``skipped_fields`` altogether -- skip recall 0.83 to 0.00 -- and still
    promote, because none of that reaches ``turn_is_exact``. The user-facing consequence
    is being re-asked a question they explicitly declined.
    """
    return bool(
        not turn.get("error")
        and turn.get("schema_valid")
        and turn.get("skip_fp", 0) == 0
        and turn.get("skip_fn", 0) == 0
    )


def _binomial_two_sided(successes: int, trials: int) -> float:
    """Exact two-sided binomial p at p=0.5 — McNemar's test on discordant pairs.

    No scipy: this package is a training pipeline, and one exact test is twelve lines.
    """
    if trials == 0:
        return 1.0
    extreme = max(successes, trials - successes)
    tail = sum(math.comb(trials, k) for k in range(extreme, trials + 1))
    return min(1.0, 2 * tail / (2 ** trials))


def mcnemar(baseline: dict[str, bool], candidate: dict[str, bool]) -> dict[str, Any]:
    """Compare two runs on the turns where they disagree.

    Turns both got right, and turns both got wrong, carry no information about which is
    better. Only the disagreements do, and under "the two are equally good" each
    disagreement is a coin flip.
    """
    shared = sorted(set(baseline) & set(candidate))
    lost = [t for t in shared if baseline[t] and not candidate[t]]
    won = [t for t in shared if candidate[t] and not baseline[t]]
    discordant = len(lost) + len(won)
    return {
        "lost": lost,
        "won": won,
        "discordant": discordant,
        "p": _binomial_two_sided(len(won), discordant),
    }


def totals(run: dict[str, Any]) -> dict[str, Any]:
    """Metric numerators and denominators, so a delta can be stated in items."""
    turns = run["turns"]
    value_correct = sum(t.get("value_correct", 0) for t in turns)
    value_compared = sum(t.get("value_compared", 0) for t in turns)
    skip_tp = sum(t.get("skip_tp", 0) for t in turns)
    skip_fn = sum(t.get("skip_fn", 0) for t in turns)
    skip_fp = sum(t.get("skip_fp", 0) for t in turns)
    tp = sum(t.get("field_tp", 0) for t in turns)
    fp = sum(t.get("field_fp", 0) for t in turns)
    fn = sum(t.get("field_fn", 0) for t in turns)
    # metrics.prf, not a second copy of it. The copy here guarded with `if precision and
    # recall`, so a candidate emitting only keys absent from gold -- precision exactly 0.0
    # -- printed `n/a`, and the metric that had just collapsed to zero read as "not
    # measured". metrics.prf guards with `is None` and returns 0.0 for the same input, so
    # the project's two scorers disagreed about one run.
    field = prf(tp, fp, fn)
    exact = sum(1 for t in turns if turn_is_exact(t))
    return {
        "turn_exact": (exact, len(turns)),
        "value_accuracy": (value_correct, value_compared),
        "skip_recall": (skip_tp, skip_tp + skip_fn),
        "field_f1": (field["f1"], None),
        "_field_precision": (tp, tp + fp),
        "_field_recall": (tp, tp + fn),
        "_skip_fp": skip_fp,
    }


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def _rate_of(pair: tuple[Any, Any]) -> float | None:
    numerator, denominator = pair
    if denominator is None:
        return numerator
    return ratio(numerator, denominator)


def _items(base: tuple[Any, Any], cand: tuple[Any, Any]) -> str:
    """The delta stated in items -- which is this column's entire purpose.

    It printed one denominator for both numerators. ``value_accuracy``'s denominator is
    ``value_compared``, the size of ``gold n pred``, which is a property of the *run*: a
    candidate that predicts more keys is compared on more of them. Baseline 86/98 against
    candidate 93/102 rendered as `93 vs 86 of 102`, stating a shared denominator that does
    not exist, and a per-item weight taken from one side only.

    Only ``value_accuracy`` moves in practice -- ``turn_exact`` is guarded by the
    same-turns refusal, and ``skip_recall``'s denominator is the gold skip count -- but
    the one that moves is the one the cycle-costing "regression" was measured in.
    """
    base_num, base_den = base
    cand_num, cand_den = cand
    if base_den is None or cand_den is None or not (base_den or cand_den):
        return ""
    if base_den == cand_den:
        return f"{cand_num} vs {base_num} of {cand_den}   (1 item = {1 / cand_den:.4f})"
    return (f"{cand_num}/{cand_den} vs {base_num}/{base_den}"
            f"   (denominators differ; a rate delta is not an item count)")


def compare(baseline: dict[str, Any], candidate: dict[str, Any], alpha: float) -> int:
    base_turns = {t["turn_id"]: t for t in baseline["turns"]}
    cand_turns = {t["turn_id"]: t for t in candidate["turns"]}
    only_base = sorted(set(base_turns) - set(cand_turns))
    only_cand = sorted(set(cand_turns) - set(base_turns))

    print(f"baseline   {baseline.get('label')!r}  {baseline.get('model')}  "
          f"split={baseline.get('split')}  turns={len(base_turns)}")
    print(f"candidate  {candidate.get('label')!r}  {candidate.get('model')}  "
          f"split={candidate.get('split')}  turns={len(cand_turns)}")
    if baseline.get("post_process") != candidate.get("post_process"):
        print("\nREFUSING: one run was post-processed and the other was not. Those "
              "measure different things -- the model, and the product.")
        return 2
    gold = _gold_check(baseline, candidate)
    if gold == "differs":
        print("\nREFUSING: the two runs were scored against different dataset revisions. "
              "Whatever separates them includes however much gold moved, and there is no "
              "way to tell the two apart from these files.")
        return 2
    if only_base or only_cand:
        print(f"\nREFUSING: the two runs scored different turns "
              f"({len(only_base)} only in baseline, {len(only_cand)} only in candidate). "
              "A paired comparison needs the same turns on both sides.")
        return 2
    if not base_turns:
        print("\nREFUSING: no turns.")
        return 2

    base_totals, cand_totals = totals(baseline), totals(candidate)

    print(f"\n{'metric':<16} {'baseline':>10} {'candidate':>10} {'delta':>9}   items")
    for name in HEADLINE:
        was, now = _rate_of(base_totals[name]), _rate_of(cand_totals[name])
        delta = None if was is None or now is None else now - was
        print(f"{name:<16} {_fmt(was):>10} {_fmt(now):>10} "
              f"{'n/a' if delta is None else f'{delta:+.4f}':>9}   "
              f"{_items(base_totals[name], cand_totals[name])}")

    test = mcnemar(
        {tid: turn_is_exact(t) for tid, t in base_turns.items()},
        {tid: turn_is_exact(t) for tid, t in cand_turns.items()},
    )

    print(f"\npaired on whole turns: {len(test['won'])} won, {len(test['lost'])} lost, "
          f"{len(base_turns) - test['discordant']} unchanged")
    if test["discordant"]:
        print(f"exact McNemar p = {test['p']:.4f} over {test['discordant']} disagreements")
    for tid in test["lost"]:
        print(f"  lost      {tid}")
    for tid in test["won"]:
        print(f"  won       {tid}")

    skips = mcnemar(
        {tid: turn_skips_are_exact(t) for tid, t in base_turns.items()},
        {tid: turn_skips_are_exact(t) for tid, t in cand_turns.items()},
    )
    print(f"\npaired on skip decisions: {len(skips['won'])} won, {len(skips['lost'])} lost, "
          f"{len(base_turns) - skips['discordant']} unchanged")
    if skips["discordant"]:
        print(f"exact McNemar p = {skips['p']:.4f} over {skips['discordant']} disagreements")
        for tid in skips["lost"]:
            print(f"  skip lost {tid}")

    regressions = _category_regressions(baseline, candidate)
    if regressions:
        print("\ncategories where value accuracy fell:")
        for name, was, now in regressions:
            print(f"  {name:<22} {_fmt(was)} -> {_fmt(now)}")

    return _verdict(test, skips, alpha, regressions)


def _gold_check(baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    """Whether the two runs were scored against the same gold.

    This is the confound that produced the most misleading number in the results table.
    ``0.5b-lora-v5-q4km-r8`` and ``0.5b-lora-v5-q4km-repro`` are the same model over the
    same split and differ by 7 value items -- and 126 of their 129 replies are
    byte-identical. The model barely moved; the dataset did, between the two runs.

    A run recorded before the dataset hash existed cannot be checked, so it warns rather
    than refuses. Refusing would make every historical comparison impossible, and the
    warning is what tells you the number needs a re-run to be trusted.
    """
    was = (baseline.get("dataset") or {}).get("sha256")
    now = (candidate.get("dataset") or {}).get("sha256")
    if was and now:
        return "same" if was == now else "differs"
    print("\nWARNING: at least one run predates dataset stamping, so this cannot check "
          "that both were scored against the same gold. Re-run both to be sure.")
    return "unknown"


def _category_regressions(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> list[tuple[str, float, float]]:
    fell = []
    for name, was in (baseline.get("by_category") or {}).items():
        now = (candidate.get("by_category") or {}).get(name)
        if not now:
            continue
        before, after = was.get("value_accuracy"), now.get("value_accuracy")
        if before is not None and after is not None and after < before:
            fell.append((name, before, after))
    return sorted(fell, key=lambda row: row[2] - row[1])


def _skips_significantly_worse(skips: dict[str, Any], alpha: float) -> bool:
    return bool(
        skips["discordant"]
        and skips["p"] < alpha
        and len(skips["lost"]) > len(skips["won"])
    )


def _verdict(
    test: dict[str, Any], skips: dict[str, Any], alpha: float, regressions: list
) -> int:
    print()
    # Checked before the field verdict, not after it, because it can only ever make the
    # answer more conservative. A measured skip regression is a result whatever the field
    # test says -- and the field test cannot see it: `turn_is_exact` reads error,
    # schema_valid, field_fp/fn and value_correct, and no skip counter at all. Skip
    # recall is printed directly above this line and nothing used to read it.
    if _skips_significantly_worse(skips, alpha):
        print(f"VERDICT reject -- skip handling went backwards on "
              f"{len(skips['lost'])} turns against {len(skips['won'])} recovered "
              f"(p = {skips['p']:.4f} < {alpha}), which is a regression the whole-turn "
              f"test cannot see.")
        if test["discordant"] and test["p"] < alpha and len(test["won"]) > len(test["lost"]):
            print(f"         Fields did improve -- {len(test['won'])} turns won against "
                  f"{len(test['lost'])} lost -- so this is a trade, not a failure. Being "
                  f"re-asked a declined question is the cost; decide it deliberately "
                  f"rather than by exit code.")
        return 1
    if test["discordant"] == 0:
        print("VERDICT cannot say -- the two runs agree on every turn. Identical "
              "behaviour, or a decode that is deterministic and data that did not move.")
        return 2
    if test["p"] >= alpha:
        print(f"VERDICT cannot say -- {len(test['won'])} won against "
              f"{len(test['lost'])} lost is what a coin produces (p = {test['p']:.4f} "
              f">= {alpha}). Not a result in either direction.")
        return 2
    if len(test["lost"]) > len(test["won"]):
        print(f"VERDICT reject -- {len(test['lost'])} turns lost against "
              f"{len(test['won'])} won (p = {test['p']:.4f}).")
        return 1
    print(f"VERDICT promote on eval-set noise -- {len(test['won'])} turns won against "
          f"{len(test['lost'])} lost (p = {test['p']:.4f}).")
    if len(skips["lost"]) > len(skips["won"]):
        print(f"         Skip handling fell on {len(skips['lost'])} turns against "
              f"{len(skips['won'])} recovered, which does not clear eval-set noise "
              f"(p = {skips['p']:.4f}). Not a reason to reject, and not nothing.")
    if regressions:
        print(f"         but {len(regressions)} categor"
              f"{'y' if len(regressions) == 1 else 'ies'} went backwards; read them above.")
    print("         UNATTRIBUTED: training variance is still unmeasured, so this says "
          "the difference is not eval-set noise, not that the change under test caused "
          "it. Train 2-3 adapters on identical data with different seeds to close that.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("baseline", help="results JSON path, or the label it was saved as")
    parser.add_argument("candidate", help="results JSON path, or the label")
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Significance for the paired test. Below this a difference is reported as "
             "a result; at or above it, as noise. Default 0.05",
    )
    args = parser.parse_args(argv)
    return compare(load_run(args.baseline), load_run(args.candidate), args.alpha)


if __name__ == "__main__":
    sys.exit(main())
