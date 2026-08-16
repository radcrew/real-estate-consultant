"""Tests for the provenance stamps written beside a dataset and beside an adapter.

The cycle this exists to prevent: v7 was regenerated at the default ``--count 2500``
rather than v6's ``--count 3000``, 2,250 rows against 2,700, and nothing beside the
weights recorded which. The tests that matter are the ones about ``--count`` reaching the
stamp and about a stamp noticing it describes a file that has since been regenerated.
"""

from __future__ import annotations

import pytest

from pipeline import provenance


@pytest.fixture
def dataset(tmp_path):
    """A written dataset and its stamp, as the generator would leave them."""
    train = tmp_path / "train.jsonl"
    val = tmp_path / "validation.jsonl"
    train.write_text('{"a": 1}\n{"a": 2}\n{"a": 3}\n', encoding="utf-8")
    val.write_text('{"a": 4}\n', encoding="utf-8")
    provenance.write_dataset_stamp(
        out_dir=tmp_path,
        args={"count": 3000, "seed": 17, "val_fraction": 0.1},
        inputs={"questions": tmp_path / "questions.json"},
        outputs={"train": train, "validation": val},
        counts={"requested": 3000, "produced": 3, "train": 3, "validation": 1},
    )
    return tmp_path, train, val


class TestReadingAFile:
    def test_a_digest_identifies_the_contents(self, tmp_path):
        one, two = tmp_path / "one", tmp_path / "two"
        one.write_text("same", encoding="utf-8")
        two.write_text("same", encoding="utf-8")
        assert provenance.file_digest(one) == provenance.file_digest(two)

    def test_a_digest_changes_with_the_contents(self, tmp_path):
        path = tmp_path / "f"
        path.write_text("before", encoding="utf-8")
        before = provenance.file_digest(path)
        path.write_text("after", encoding="utf-8")
        assert provenance.file_digest(path) != before

    def test_blank_lines_are_not_rows(self, tmp_path):
        path = tmp_path / "f.jsonl"
        path.write_text('{"a": 1}\n\n{"a": 2}\n\n', encoding="utf-8")
        assert provenance.line_count(path) == 2

    @pytest.mark.parametrize("call", [provenance.file_digest, provenance.line_count])
    def test_a_missing_file_is_none_not_an_exception(self, tmp_path, call):
        """Provenance wraps work that costs hours. It never raises."""
        assert call(tmp_path / "absent") is None


class TestDatasetStamp:
    def test_the_flag_that_cost_a_cycle_is_recorded(self, dataset):
        stamp = provenance.read_stamp(dataset[0])
        assert stamp["args"]["count"] == 3000
        assert stamp["counts"]["train"] == 3

    def test_rows_are_counted_from_the_file_not_the_caller(self, dataset):
        """The caller's numbers and the file's can disagree; the file is the fact."""
        assert stamp_outputs(dataset[0])["train"]["rows"] == 3

    def test_the_output_is_identified_by_hash(self, dataset):
        directory, train, _ = dataset
        assert stamp_outputs(directory)["train"]["sha256"] == provenance.file_digest(train)

    def test_a_stamp_is_found_from_the_directory_holding_it(self, dataset):
        assert provenance.read_stamp(dataset[0])["kind"] == "dataset"

    def test_a_directory_with_no_stamp_reads_as_none(self, tmp_path):
        assert provenance.read_stamp(tmp_path) is None

    def test_unreadable_json_reads_as_none(self, tmp_path):
        (tmp_path / provenance.DATASET_STAMP_NAME).write_text("{ not json", encoding="utf-8")
        assert provenance.read_stamp(tmp_path) is None

    def test_the_git_state_is_recorded_even_when_git_says_nothing(self, dataset):
        """Fields are always present. Values may be None outside a checkout."""
        assert set(provenance.read_stamp(dataset[0])["git"]) == {"commit", "branch", "dirty"}


class TestAdapterStamp:
    def _write(self, dataset, out_dir):
        _, train, val = dataset
        return provenance.write_adapter_stamp(
            out_dir=out_dir,
            base_model="Qwen/Qwen2.5-0.5B-Instruct",
            hyperparameters={"rank": 16, "alpha": 32, "epochs": 1.0},
            train_path=train,
            val_path=val,
            counts={"train": 3, "validation": 1},
            versions={"torch": "2.4.0"},
        )

    def test_the_dataset_stamp_is_copied_in_not_referenced(self, dataset, tmp_path):
        """train.jsonl is regenerated in place, so a pointer to it goes stale exactly
        when the question gets asked."""
        out = tmp_path / "adapter"
        self._write(dataset, out)
        stamp = provenance.read_stamp(out)
        assert stamp["dataset"]["args"]["count"] == 3000

    def test_data_matching_its_stamp_is_recorded_as_matching(self, dataset, tmp_path):
        out = tmp_path / "adapter"
        self._write(dataset, out)
        assert provenance.read_stamp(out)["dataset_matches_stamp"] is True
        assert provenance.stamp_says_data_changed(out) is False

    def test_data_regenerated_after_its_stamp_is_caught(self, dataset, tmp_path):
        """The whole point. The stamp still says --count 3000 and 3 rows; the file the
        weights actually saw is a different file, and the record has to say so."""
        _, train, _ = dataset
        train.write_text('{"a": 9}\n', encoding="utf-8")
        out = tmp_path / "adapter"
        self._write(dataset, out)
        stamp = provenance.read_stamp(out)
        assert stamp["dataset_matches_stamp"] is False
        assert stamp["trained_on"]["train"]["rows"] == 1
        assert provenance.stamp_says_data_changed(out) is True

    def test_no_dataset_stamp_is_unknown_rather_than_broken(self, tmp_path):
        """Data predating this feature must not warn on every run, or the warning that
        matters gets ignored."""
        train, val = tmp_path / "train.jsonl", tmp_path / "validation.jsonl"
        train.write_text('{"a": 1}\n', encoding="utf-8")
        val.write_text('{"a": 2}\n', encoding="utf-8")
        out = tmp_path / "adapter"
        provenance.write_adapter_stamp(
            out_dir=out, base_model="b", hyperparameters={}, train_path=train,
            val_path=val, counts={}, versions={},
        )
        assert provenance.read_stamp(out)["dataset_matches_stamp"] is None
        assert provenance.stamp_says_data_changed(out) is False

    def test_the_hyperparameters_travel_with_the_weights(self, dataset, tmp_path):
        out = tmp_path / "adapter"
        self._write(dataset, out)
        stamp = provenance.read_stamp(out)
        assert stamp["hyperparameters"]["rank"] == 16
        assert stamp["base_model"] == "Qwen/Qwen2.5-0.5B-Instruct"


class TestComparingTwoStamps:
    def test_the_count_difference_is_reported(self):
        left = {"args": {"count": 3000}, "counts": {"train": 2700}}
        right = {"args": {"count": 2500}, "counts": {"train": 2250}}
        assert provenance.differences(left, right) == [
            ("args.count", 3000, 2500),
            ("counts.train", 2700, 2250),
        ]

    def test_the_timestamp_is_not_a_difference(self):
        """Two runs always differ here and it has never explained anything."""
        left = {"generated_at": "2026-08-15T10:00:00+00:00", "args": {"count": 3000}}
        right = {"generated_at": "2026-08-16T11:00:00+00:00", "args": {"count": 3000}}
        assert provenance.differences(left, right) == []

    def test_a_field_only_one_side_has_is_a_difference(self):
        assert provenance.differences({}, {"args": {"seed": 17}}) == [("args.seed", "-", 17)]

    def test_identical_stamps_have_nothing_to_report(self, dataset):
        stamp = provenance.read_stamp(dataset[0])
        assert provenance.differences(stamp, stamp) == []


def stamp_outputs(directory):
    return provenance.read_stamp(directory)["outputs"]
