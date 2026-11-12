"""Holds the Codex marketplace to the Claude Code marketplace and to `plugins/`.

Codex reads `.agents/plugins/marketplace.json`; Claude Code reads
`.claude-plugin/marketplace.json`. The two formats differ, so each lists the
plugins in its own file, and nothing reads them together: a plugin added to
one only, moved in one only, or added under `plugins/` and listed in neither,
installs in one host and is missing or broken in the other without any error.
This catches each of those drifts, naming the plugin or directory.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_ENTRIES = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())[
    "plugins"
]
CODEX_ENTRIES = json.loads((REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text())[
    "plugins"
]
CLAUDE_PATHS = {entry["name"]: entry["source"] for entry in CLAUDE_ENTRIES}
CODEX_PATHS = {entry["name"]: entry["source"]["path"] for entry in CODEX_ENTRIES}
PLUGIN_DIRECTORIES = sorted(
    path.name for path in (REPO_ROOT / "plugins").iterdir() if path.is_dir()
)


class TestTheTwoMarketplaces:
    def test_list_the_same_plugins_in_the_same_order(self) -> None:
        assert list(CODEX_PATHS.items()) == list(CLAUDE_PATHS.items())

    @pytest.mark.parametrize("name", CLAUDE_PATHS, ids=str)
    def test_codex_lists_each_claude_plugin_at_its_path(self, name: str) -> None:
        assert CODEX_PATHS.get(name) == CLAUDE_PATHS[name]

    @pytest.mark.parametrize("name", CODEX_PATHS, ids=str)
    def test_claude_lists_each_codex_plugin_at_its_path(self, name: str) -> None:
        assert CLAUDE_PATHS.get(name) == CODEX_PATHS[name]


class TestEveryPluginDirectory:
    @pytest.mark.parametrize("directory", PLUGIN_DIRECTORIES, ids=str)
    def test_is_listed_in_the_codex_marketplace(self, directory: str) -> None:
        assert directory in CODEX_PATHS

    @pytest.mark.parametrize("directory", PLUGIN_DIRECTORIES, ids=str)
    def test_is_listed_in_the_claude_marketplace(self, directory: str) -> None:
        assert directory in CLAUDE_PATHS

    def test_every_listed_name_is_a_directory(self) -> None:
        assert sorted(CODEX_PATHS) == PLUGIN_DIRECTORIES


class TestEveryCodexEntry:
    @pytest.mark.parametrize("entry", CODEX_ENTRIES, ids=lambda entry: entry["name"])
    def test_is_a_local_source(self, entry: dict) -> None:
        assert entry["source"]["source"] == "local"
