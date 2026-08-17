"""Every deployable setting has to reach whoever deploys it.

`Settings` reads the environment, so a field added without a line in `.env.example` is
invisible: the app starts on its default and the operator never learns there was a choice.
That is how a screening control or a routing pin ends up unset in one environment and set
in another — nothing errors, behaviour just differs.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.core.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"

# Settings that are not deployment configuration. Kept as an explicit list so adding one
# is a decision rather than an omission.
NOT_DEPLOYMENT_CONFIG = {
    # Service identity, the same in every environment.
    "APP_NAME",
    "VERSION",
    # Populated automatically by the host (VERCEL_GIT_COMMIT_SHA).
    "GIT_SHA",
}


def documented_keys() -> set[str]:
    """Keys assigned in the example file, including ones commented out on purpose."""
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    return {match.group(1) for match in re.finditer(r"^#?\s*([A-Z][A-Z0-9_]*)=", text, re.M)}


def settings_keys() -> list[str]:
    return [name.upper() for name in Settings.model_fields]


class TestEnvExampleCoverage:
    def test_the_parser_finds_the_obvious_ones(self):
        """Guard the guard: a regex that matched nothing would pass everything below."""
        found = documented_keys()
        assert {"DATABASE_URL", "SUPABASE_URL", "LOG_LEVEL"} <= found
        assert len(found) > 30

    @pytest.mark.parametrize("name", sorted(set(settings_keys()) - NOT_DEPLOYMENT_CONFIG))
    def test_every_setting_is_documented(self, name):
        assert name in documented_keys(), (
            f"{name} is a Settings field with no line in .env.example. Add it, or add it "
            f"to NOT_DEPLOYMENT_CONFIG if it is not something anyone deploys."
        )

    def test_the_exemptions_are_real_settings(self):
        """A stale exemption would silently excuse a field that no longer exists."""
        assert NOT_DEPLOYMENT_CONFIG <= set(settings_keys())

    def test_no_documented_key_has_been_removed_from_settings(self):
        """The other direction: a leftover line describes a knob that does nothing.

        Scoped to the keys Settings would recognise — the file also carries credentials
        read by boto3 rather than by Settings, which are deliberately listed there.
        """
        boto3_credentials = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}
        stale = documented_keys() - set(settings_keys()) - boto3_credentials
        assert not stale, f"documented but no longer a setting: {sorted(stale)}"
