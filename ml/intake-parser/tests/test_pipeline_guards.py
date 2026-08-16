"""Tests for the parts of `train/`, `quantize/` and `data/make_phrasings` that are not wrappers.

These three modules sit at 0% coverage, and the review called that defensible: they shell
out to llama.cpp or drive torch, and a test of a subprocess call is a test of `mock`. That
holds for the wrappers. It stopped holding once real decisions moved into them -- whether
to overwrite an irreplaceable artifact, whether to train on a truncated row, which option
keeps an ambiguous word. None of those touch a subprocess, a GPU or a network, and each is
a decision whose wrong answer is silent.

`torch` is an optional extra and CI does not install it, so the trainer tests skip rather
than fail there.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.data.make_phrasings import drop_ambiguous_claims
from pipeline.quantize.build_gguf import _refuse_to_clobber, quantize_flags


class TestRefusingToOverwriteAnArtifact:
    """A GGUF filename carries the model version, not the run.

    So a retrain of v6 writes over the exact file a published v6 row was measured on. That
    happened: every `*-v6-*` artifact on this machine is the retrain, the adapter behind
    the 0.912 row is gone, and the only surviving evidence was a step count in a
    checkpoint. Both files had the right name the whole time.
    """

    @pytest.fixture
    def existing(self, tmp_path: Path) -> Path:
        path = tmp_path / "qwen2.5-0.5b-instruct-intake-v6-q4_k_m.gguf"
        path.write_bytes(b"\0" * 4096)
        return path

    def test_a_free_path_is_not_an_error(self, tmp_path: Path):
        assert _refuse_to_clobber(tmp_path / "new.gguf", force=False) is None

    def test_an_existing_artifact_stops_the_build(self, existing: Path):
        assert _refuse_to_clobber(existing, force=False) == 1

    def test_force_is_the_way_past_it(self, existing: Path):
        assert _refuse_to_clobber(existing, force=True) is None

    def test_it_names_the_file_and_when_it_was_written(self, existing: Path, capsys):
        _refuse_to_clobber(existing, force=False)
        err = capsys.readouterr().err
        assert existing.name in err
        assert "already exists" in err
        # The date is what tells you whether this is the artifact your row cites.
        assert "written" in err

    def test_it_says_how_to_proceed(self, existing: Path, capsys):
        _refuse_to_clobber(existing, force=False)
        assert "--force" in capsys.readouterr().err

    def test_nothing_is_printed_when_there_is_no_clash(self, tmp_path: Path, capsys):
        _refuse_to_clobber(tmp_path / "new.gguf", force=False)
        assert capsys.readouterr().err == ""

    def test_the_existing_file_is_left_alone(self, existing: Path):
        before = existing.read_bytes()
        _refuse_to_clobber(existing, force=False)
        _refuse_to_clobber(existing, force=True)
        assert existing.read_bytes() == before


class TestQuantizeFlags:
    def test_a_plain_build_passes_no_flags(self):
        assert quantize_flags(None) == []

    def test_an_imatrix_build_also_protects_the_big_tensors(self, tmp_path: Path):
        flags = quantize_flags(tmp_path / "imatrix.dat")
        assert "--imatrix" in flags
        # The ~152k vocabulary makes these a large share of the parameters, and they are
        # the tensors emitting exact field values.
        assert flags.count("q8_0") == 2
        assert "--token-embedding-type" in flags and "--output-tensor-type" in flags


class TestAmbiguousWordsLeaveEveryClaimant:
    """The stated reason for dropping is that either label would be wrong on an example.

    A one-pass version recorded the first claimant and stripped the second, so the word
    survived under whichever option the dict yielded first. The artifact has no duplicate
    either way, which is why the committed file could not settle whether it had happened.
    """

    def test_a_contested_word_goes_from_both(self):
        result = drop_ambiguous_claims(
            {"industrial": ["warehouse", "depot"], "land": ["acreage", "depot"]}
        )
        assert result == {"industrial": ["warehouse"], "land": ["acreage"]}

    def test_the_result_is_the_same_whichever_option_comes_first(self):
        forward = drop_ambiguous_claims(
            {"industrial": ["depot"], "land": ["depot", "acreage"]}
        )
        reverse = drop_ambiguous_claims(
            {"land": ["depot", "acreage"], "industrial": ["depot"]}
        )
        assert forward["industrial"] == reverse["industrial"] == []
        assert forward["land"] == reverse["land"] == ["acreage"]

    def test_a_word_claimed_three_times_goes_from_all_three(self):
        result = drop_ambiguous_claims({"a": ["x"], "b": ["x"], "c": ["x", "y"]})
        assert result == {"a": [], "b": [], "c": ["y"]}

    def test_unique_words_are_untouched_and_keep_their_order(self):
        original = {"industrial": ["warehouse", "factory"], "retail": ["shop", "mall"]}
        assert drop_ambiguous_claims(original) == original

    def test_every_option_survives_as_a_key_even_when_emptied(self):
        """The generator falls back to the literal option for an empty pool; a missing
        key is a different thing and would read as an option that was never asked about."""
        result = drop_ambiguous_claims({"a": ["x"], "b": ["x"], "specialty": []})
        assert set(result) == {"a", "b", "specialty"}

    def test_it_says_which_options_contested_the_word(self, capsys):
        drop_ambiguous_claims({"industrial": ["depot"], "land": ["depot"]})
        out = capsys.readouterr().out
        assert "depot" in out
        assert "industrial" in out and "land" in out

    def test_it_does_not_mutate_its_argument(self):
        original = {"industrial": ["depot"], "land": ["depot"]}
        drop_ambiguous_claims(original)
        assert original == {"industrial": ["depot"], "land": ["depot"]}


class TestOverLengthRowsAreDroppedNotTrimmed:
    """Truncation cut the supervised span, teaching an unterminated answer.

    `labels` mask the prompt and supervise the tail, so `full[:max_len]` removes the
    closing braces and the EOS from inside the loss -- against `raw_json_valid`, which is
    the metric this project optimises. The prefix-mismatch path already dropped rows.
    """

    @pytest.fixture
    def dataset_cls(self):
        pytest.importorskip("torch", reason="the train extra is not installed")
        from pipeline.train.train_lora import IntakeDataset

        return IntakeDataset

    @pytest.fixture
    def encode(self, dataset_cls):
        """`_encode` against a stub tokenizer, so no model or GPU is involved.

        The stub emits a role marker per message and one token per character. The marker
        matters: a real chat template opens the assistant turn before the completion, and
        that is what makes the generation prompt a strict prefix of the full sequence.
        Without it every row takes the prefix-mismatch path and the test measures nothing.
        """
        role = {"user": 1000, "assistant": 1001}

        class StubTokenizer:
            def apply_chat_template(self, messages, *, tokenize, add_generation_prompt,
                                    return_dict):
                ids: list[int] = []
                for message in messages:
                    ids.append(role[message["role"]])
                    ids.extend(ord(c) for c in message["content"])
                if add_generation_prompt:
                    ids.append(role["assistant"])
                return {"input_ids": ids}

        instance = dataset_cls.__new__(dataset_cls)
        instance.rows, instance.dropped, instance.truncated = [], 0, 0
        instance.prefix_mismatches = 0

        def run(prompt_len: int, completion_len: int, max_len: int):
            messages = [
                {"role": "user", "content": "p" * prompt_len},
                {"role": "assistant", "content": "c" * completion_len},
            ]
            return instance._encode(messages, StubTokenizer(), max_len)

        run.instance = instance
        return run

    def test_the_stub_produces_a_strict_prefix(self, encode):
        """Guards the fixture itself: a bad stub makes every assertion below vacuous."""
        assert encode(prompt_len=10, completion_len=10, max_len=100) is not None
        assert encode.instance.prefix_mismatches == 0

    def test_a_row_that_fits_is_kept(self, encode):
        assert encode(prompt_len=10, completion_len=10, max_len=100) is not None
        assert encode.instance.truncated == 0

    def test_an_over_length_row_is_dropped(self, encode):
        assert encode(prompt_len=10, completion_len=200, max_len=50) is None

    def test_the_drop_is_counted_so_the_run_can_report_it(self, encode):
        encode(prompt_len=10, completion_len=200, max_len=50)
        assert encode.instance.truncated == 1

    def test_a_dropped_row_is_never_appended(self, encode):
        encode(prompt_len=10, completion_len=200, max_len=50)
        assert encode.instance.rows == []

    def test_a_kept_row_supervises_only_the_completion(self, encode):
        from pipeline.train.train_lora import IGNORE_INDEX

        encoded = encode(prompt_len=10, completion_len=10, max_len=100)
        supervised = [x for x in encoded.labels if x != IGNORE_INDEX]
        assert len(supervised) == 10
        assert supervised == encoded.input_ids[-10:]
        assert supervised == [ord("c")] * 10, "the completion, not the prompt"

    def test_no_kept_row_is_ever_longer_than_max_len(self, encode):
        for completion in (1, 20, 200, 2000):
            encoded = encode(prompt_len=10, completion_len=completion, max_len=64)
            assert encoded is None or len(encoded.input_ids) <= 64
