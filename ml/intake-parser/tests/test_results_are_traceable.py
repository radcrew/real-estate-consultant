"""Every published row must keep the raw output it was computed from.

`results/.gitignore` already states the rule -- "Committing a row is therefore explicit:
`git add -f results/<label>.json`. Do that for any run `results.md` cites" -- and nothing
enforced it, so it was followed for 4 of 15 rows. Eight rows now have no raw output
anywhere and cannot be re-derived, re-checked against a scorer fix, or replayed through
`test_bound_correction_replay`.

That is not hypothetical here. `metrics.percentile` was wrong, and correcting the six
affected p50 figures was only possible because those runs' per-turn `latency_ms` still
existed. For the eight rows below the same correction is simply unavailable.

It is sharper still for v6: its adapter and GGUFs were overwritten by a retrain, so
`results/0.5b-lora-v6-q4km.json` is now the *only* surviving evidence of what the shipped
model did. It was untracked until this test was written.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from pipeline.paths import PROJECT_DIR, RESULTS_DIR

RESULTS_MD = RESULTS_DIR / "results.md"

_MARKERS = str.maketrans("", "", "*`†")

# Rows published before the convention existed, whose per-turn output is gone from this
# machine and from the index. Listed rather than silently tolerated: an allowlist that
# names its members is a debt, an unenforced rule is not even that.
#
# Do not add to this list. Adding a row here means deleting evidence; the fix for a new
# failure is `git add -f results/<label>.json`, which is what the rule asks for.
RAW_OUTPUT_LOST = {
    "0.5b-lora-v2-q4km-r5",
    "0.5b-lora-v3-q4km",
    "0.5b-lora-v3-q4km-r6",
    "0.5b-lora-v4-f16",
    "0.5b-lora-v4-q4km",
    "0.5b-lora-v4-q4km-r7",
    "0.5b-lora-v5-f16",
    "0.5b-lora-v5-q4km",
}


def _published_labels() -> dict[str, int]:
    """Labels of every results row in `results.md`, mapped to their line number.

    A results row is recognised by shape rather than by position, so a new table does not
    need registering here: twelve-ish cells, an integer `Turns`, and a numeric `Raw JSON`.
    Category breakdowns and turn-by-turn tables have neither and are skipped.
    """
    labels: dict[str, int] = {}
    for number, line in enumerate(RESULTS_MD.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            continue
        # Remove emphasis and the dagger wholesale rather than stripping in some fixed
        # order: the label cell reads `**0.5b-lora-v6-q4km** †`, and chained strips leave
        # the inner `**` behind whichever order they run in. No label contains these.
        cells = [c.translate(_MARKERS).strip() for c in line.strip("|").split("|")]
        if len(cells) < 11:
            continue
        if not re.fullmatch(r"\d+", cells[2]) or not re.fullmatch(r"[\d.]+", cells[3]):
            continue
        labels.setdefault(cells[0], number)
    return labels


def _tracked_result_files() -> set[str] | None:
    """Labels with a committed results JSON, or ``None`` if git cannot answer.

    Tracked, not merely present. On a fresh checkout the two coincide, which is the state
    that matters -- but locally an untracked file would make this pass while CI, and
    anyone else's clone, has nothing.
    """
    try:
        listing = subprocess.run(
            ["git", "ls-files", "results"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if listing.returncode != 0:
        return None
    return {
        Path(line).stem
        for line in listing.stdout.splitlines()
        if line.strip().endswith(".json")
    }


@pytest.fixture(scope="module")
def published() -> dict[str, int]:
    labels = _published_labels()
    assert labels, "no results rows parsed - the table shape changed, fix the parser"
    return labels


@pytest.fixture(scope="module")
def tracked() -> set[str]:
    found = _tracked_result_files()
    if found is None:
        pytest.skip("git is not available to answer what is tracked")
    return found


class TestEveryPublishedRowKeepsItsRawOutput:

    def test_the_parser_still_recognises_the_current_table(self, published):
        """Guards the guard. A parser that silently matches nothing passes everything."""
        assert "0.5b-lora-v6-q4km" in published
        assert len(published) >= 15

    def test_every_row_has_its_per_turn_output_committed(self, published, tracked):
        missing = sorted(
            f"results.md:{line} {label}"
            for label, line in published.items()
            if label not in tracked and label not in RAW_OUTPUT_LOST
        )
        assert not missing, (
            "these rows publish numbers whose raw output is not committed, so nothing can "
            "re-check them against a scorer fix or replay them:\n  "
            + "\n  ".join(missing)
            + "\n\nRun: git add -f results/<label>.json"
        )

    def test_the_lost_list_does_not_name_a_row_that_is_actually_fine(self, tracked):
        """Keeps the allowlist honest as files are recovered."""
        recovered = sorted(RAW_OUTPUT_LOST & tracked)
        assert not recovered, (
            f"{recovered} are tracked after all - drop them from RAW_OUTPUT_LOST rather "
            "than carrying an exemption that excuses nothing"
        )

    def test_the_lost_list_does_not_name_a_row_nobody_publishes(self, published):
        stale = sorted(RAW_OUTPUT_LOST - set(published))
        assert not stale, (
            f"{stale} are exempted but no longer appear in results.md; remove them"
        )

    def test_the_shipped_model_row_is_covered(self, tracked):
        """v6's adapter and both GGUFs were overwritten by a retrain. These files are the
        only remaining record of what the model behind the deployed numbers actually did."""
        for label in ("0.5b-lora-v6-q4km", "0.5b-lora-v6-f16"):
            assert label in tracked, f"{label} is the last evidence of v6 and is untracked"
