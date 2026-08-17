"""Guards on the worker image, which nothing else would catch until a cold start.

The handler path and the required environment are only exercised when Lambda boots the
container — by which point the failure is a turn that never ran.
"""
from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest

from app.core.config import Settings

WORKER_DIR = Path(__file__).resolve().parents[3] / "infra" / "chat-intake-worker"
DOCKERFILE = WORKER_DIR / "Dockerfile"
README = WORKER_DIR / "README.md"


def _cmd_target() -> str:
    """The handler path from the Dockerfile's CMD."""
    match = re.search(r'^CMD\s+(\[.*\])\s*$', DOCKERFILE.read_text(encoding="utf-8"), re.MULTILINE)
    assert match, "Dockerfile has no CMD"
    return json.loads(match.group(1))[0]


def _required_settings() -> list[str]:
    """Settings with no default — absent from the environment, the import fails."""
    return [
        name for name, field in Settings.model_fields.items() if field.is_required()
    ]


class TestHandlerPath:
    def test_the_cmd_resolves_to_a_real_callable(self):
        """A renamed handler would surface as a cold-start error in production."""
        target = _cmd_target()
        module_path, _, attribute = target.rpartition(".")
        module = importlib.import_module(module_path)
        assert callable(getattr(module, attribute))

    def test_the_cmd_points_at_the_chat_worker(self):
        assert _cmd_target() == "app.workers.chat_job_worker.handler"


class TestRequiredEnvironmentIsDocumented:
    @pytest.mark.parametrize("name", _required_settings())
    def test_every_required_setting_is_in_the_readme(self, name):
        """A new required setting silently breaks the worker's boot, not the API's.

        The API gets its values from Vercel; this deployable has its own environment, so
        anything mandatory has to be written down where whoever deploys it will look.
        """
        assert name.upper() in README.read_text(encoding="utf-8"), (
            f"{name.upper()} is required by Settings but not documented in "
            f"{README.name} — the worker would fail to import without it."
        )


class TestBuildContext:
    def test_the_image_copies_the_whole_app_package(self):
        """A curated file list would be a second thing to keep in step with the API."""
        assert "COPY app/" in DOCKERFILE.read_text(encoding="utf-8")

    def test_the_sample_event_matches_the_publisher_shape(self):
        """The publisher sends ids only; a sample carrying more would mislead."""
        event = json.loads((WORKER_DIR / "sample-event.json").read_text(encoding="utf-8"))
        body = json.loads(event["Records"][0]["body"])
        assert set(body) == {"job_id", "session_id"}
        assert "MessageGroupId" in event["Records"][0]["attributes"]
