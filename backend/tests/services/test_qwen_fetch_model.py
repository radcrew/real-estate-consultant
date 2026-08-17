"""Tests for the Qwen image's weight-fetching helper.

Only the selection logic is covered — the download itself is Hugging Face's code, and
the interesting decision is which file gets picked.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

FETCH_PATH = Path(__file__).resolve().parents[3] / "services" / "qwen-lambda" / "fetch_model.py"


def _load_fetch_model():
    spec = importlib.util.spec_from_file_location("qwen_fetch_model", FETCH_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fetch_model = _load_fetch_model()

_SAFETENSORS_REPO = ["config.json", "model.safetensors", "tokenizer.json"]


class TestSelectGguf:
    def test_single_gguf_is_chosen(self):
        files = [*_SAFETENSORS_REPO, "qwen2.5-0.5b-instruct-q8_0.gguf"]
        assert fetch_model.select_gguf(files) == "qwen2.5-0.5b-instruct-q8_0.gguf"

    def test_several_quantisations_refuse_to_be_guessed(self):
        """Quantisation trades accuracy against size — the caller has to decide."""
        files = ["qwen-q4_k_m.gguf", "qwen-q8_0.gguf"]
        with pytest.raises(fetch_model.NoGgufFound) as info:
            fetch_model.select_gguf(files)
        assert "qwen-q4_k_m.gguf" in str(info.value)
        assert "qwen-q8_0.gguf" in str(info.value)

    def test_explicit_filename_wins(self):
        files = ["qwen-q4_k_m.gguf", "qwen-q8_0.gguf"]
        assert fetch_model.select_gguf(files, filename="qwen-q8_0.gguf") == "qwen-q8_0.gguf"

    def test_unknown_filename_lists_what_exists(self):
        files = ["qwen-q8_0.gguf"]
        with pytest.raises(fetch_model.NoGgufFound) as info:
            fetch_model.select_gguf(files, filename="qwen-q2_k.gguf")
        assert "qwen-q8_0.gguf" in str(info.value)

    def test_safetensors_only_repo_explains_the_conversion(self):
        """The common case: a fine-tune published in HF format, not GGUF."""
        with pytest.raises(fetch_model.NoGgufFound) as info:
            fetch_model.select_gguf(_SAFETENSORS_REPO)
        assert "convert_hf_to_gguf" in str(info.value)

    def test_matching_is_case_insensitive(self):
        assert fetch_model.select_gguf(["Qwen-Q8_0.GGUF"]) == "Qwen-Q8_0.GGUF"
