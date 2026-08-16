"""Tests for the Qwen Lambda handler.

The handler ships in the image, not the backend package, but it is the other half of the
contract ``QwenLambdaProvider`` speaks — so it is tested here, where a change to either
side breaks the same suite. ``llama_cpp`` is stubbed: the image carries it, CI does not.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

HANDLER_PATH = Path(__file__).resolve().parents[3] / "services" / "qwen-lambda" / "handler.py"


class _StubGrammar:
    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_string(cls, text: str, verbose: bool = False) -> _StubGrammar:
        return cls(text)


def _load_handler():
    stub = types.ModuleType("llama_cpp")
    stub.Llama = object
    stub.LlamaGrammar = _StubGrammar
    sys.modules.setdefault("llama_cpp", stub)
    spec = importlib.util.spec_from_file_location("qwen_image_handler", HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


handler_module = _load_handler()


class _FakeLlm:
    def __init__(self, completion: dict) -> None:
        self.completion = completion
        self.calls: list[dict] = []

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        return self.completion


def _completion(content: str = '{"is_complete": false}', finish_reason: str = "stop") -> dict:
    return {
        "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 40},
    }


_MESSAGES = [
    {"role": "system", "content": "You extract criteria."},
    {"role": "user", "content": "3 bed in Austin"},
]
_GRAMMARS = {"LlmParseModelOutput": _StubGrammar("root ::= object")}


def _event(**overrides):
    event = {
        "messages": _MESSAGES,
        "schema_name": "LlmParseModelOutput",
        "max_tokens": 800,
        "temperature": 0.1,
    }
    event.update(overrides)
    return event


class TestGenerate:
    def test_returns_the_provider_contract(self):
        llm = _FakeLlm(_completion())
        result = handler_module.generate(_event(), llm=llm, grammars=_GRAMMARS)
        assert result == {
            "text": '{"is_complete": false}',
            "stop_reason": "stop",
            "usage": {"prompt_tokens": 120, "completion_tokens": 40},
        }

    def test_forwards_generation_settings_and_the_grammar(self):
        llm = _FakeLlm(_completion())
        handler_module.generate(_event(), llm=llm, grammars=_GRAMMARS)
        call = llm.calls[0]
        assert call["messages"] == _MESSAGES
        assert call["grammar"] is _GRAMMARS["LlmParseModelOutput"]
        assert call["max_tokens"] == 800
        assert call["temperature"] == 0.1

    def test_applies_defaults_when_limits_are_absent(self):
        llm = _FakeLlm(_completion())
        event = _event()
        del event["max_tokens"], event["temperature"]
        handler_module.generate(event, llm=llm, grammars=_GRAMMARS)
        assert llm.calls[0]["max_tokens"] == handler_module.DEFAULT_MAX_TOKENS
        assert llm.calls[0]["temperature"] == handler_module.DEFAULT_TEMPERATURE

    def test_truncation_is_reported_as_length(self):
        """The caller treats this as incomplete rather than parsing a half-object."""
        llm = _FakeLlm(_completion(finish_reason="length"))
        result = handler_module.generate(_event(), llm=llm, grammars=_GRAMMARS)
        assert result["stop_reason"] == "length"

    def test_temperature_zero_is_forwarded_not_defaulted(self):
        """A falsy-but-meaningful value: 0.0 means deterministic, not 'unset'."""
        llm = _FakeLlm(_completion())
        handler_module.generate(_event(temperature=0.0), llm=llm, grammars=_GRAMMARS)
        assert llm.calls[0]["temperature"] == 0.0

    @pytest.mark.parametrize("messages", [None, [], "not a list"])
    def test_rejects_missing_messages(self, messages):
        """Raising sets Lambda's FunctionError, which is what the caller classifies on."""
        llm = _FakeLlm(_completion())
        with pytest.raises(ValueError):
            handler_module.generate(
                _event(messages=messages), llm=llm, grammars=_GRAMMARS
            )

    def test_unknown_schema_name_names_what_the_image_has(self):
        llm = _FakeLlm(_completion())
        with pytest.raises(ValueError) as info:
            handler_module.generate(_event(schema_name="Nope"), llm=llm, grammars=_GRAMMARS)
        assert "LlmParseModelOutput" in str(info.value)

    def test_never_generates_without_a_grammar(self):
        """Unconstrained decoding is the failure mode this whole design exists to avoid."""
        llm = _FakeLlm(_completion())
        with pytest.raises(ValueError):
            handler_module.generate(_event(schema_name="Nope"), llm=llm, grammars=_GRAMMARS)
        assert llm.calls == []

    def test_missing_choices_yields_empty_text(self):
        llm = _FakeLlm({"choices": [], "usage": {}})
        result = handler_module.generate(_event(), llm=llm, grammars=_GRAMMARS)
        assert result["text"] == ""


class TestLoadGrammars:
    def test_loads_gbnf_files_and_ignores_others(self, tmp_path):
        (tmp_path / "LlmParseModelOutput.gbnf").write_text("root ::= object", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")
        grammars = handler_module.load_grammars(str(tmp_path))
        assert set(grammars) == {"LlmParseModelOutput"}
        assert grammars["LlmParseModelOutput"].text == "root ::= object"


class TestHandler:
    def test_raises_when_the_image_has_no_weights(self):
        """Outside the image there is no GGUF, and a clear error beats an AttributeError."""
        assert handler_module.LLM is None
        with pytest.raises(RuntimeError):
            handler_module.handler(_event(), None)
