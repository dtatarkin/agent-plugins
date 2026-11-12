"""Holds each marketplace entry's description to its plugin's own manifest.

The marketplace shows its own copy of a plugin's description, beside the one
the plugin's manifest declares. Nothing reads the two together, so a manifest
edited without the marketplace leaves the listing describing a plugin that no
longer exists. The manifest is canonical; this test notices the drift.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
ENTRIES = MARKETPLACE["plugins"]


class TestEveryMarketplaceEntry:
    @pytest.mark.parametrize("entry", ENTRIES, ids=lambda entry: entry["name"])
    def test_description_equals_the_plugin_manifest(self, entry: dict) -> None:
        manifest = REPO_ROOT / entry["source"] / ".claude-plugin" / "plugin.json"
        assert entry["description"] == json.loads(manifest.read_text())["description"]

    def test_the_marketplace_lists_plugins(self) -> None:
        assert ENTRIES
