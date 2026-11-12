"""Holds every portable plugin's two manifests together.

A plugin meant for hosts beyond Claude Code carries a root `plugin.json` in
the Agent Plugins 1.0 format beside its `.claude-plugin/plugin.json`. Claude
Code reads only the latter, so a root manifest that drifts from it — a stale
description, a field the closed schema rejects — fails silently in every
other host while Claude Code goes on working. This catches both: a root
manifest that is not well formed, and one whose name, version, description or
author disagrees with its Claude manifest.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
# The plugins meant for hosts beyond Claude Code.
PORTABLE = (
    "python-rules",
    "logging-rules",
    "lint-rules",
    "clickhouse-rules",
    "django-rules",
    "just-rules",
    "metabase-rules",
    "redis-rules",
)
PERMITTED = frozenset(
    {
        "$schema",
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "extensions",
    }
)
AUTHOR_KEYS = frozenset({"name", "email", "url"})
NAME_PATTERN = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
NAME_MAX_LENGTH = 64
HELD_EQUAL = ("name", "version", "description", "author")
ROOT_MANIFESTS = sorted(REPO_ROOT.glob("plugins/*/plugin.json"))


def manifest_violations(root: dict, claude: dict) -> list[str]:
    """Violations of the portable-manifest contract; empty for a compliant pair."""
    violations: list[str] = []
    if root.get("$schema") != SCHEMA:
        violations.append(f"$schema: {root.get('$schema')!r} is not {SCHEMA!r}")
    violations.extend(
        f"{key}: not a field the schema permits" for key in sorted(root.keys() - PERMITTED)
    )
    if "author" in root:
        author = root["author"]
        if not isinstance(author, dict):
            violations.append("author: not an object")
        else:
            violations.extend(
                f"author.{key}: not a field the schema permits"
                for key in sorted(author.keys() - AUTHOR_KEYS)
            )
    name = root.get("name")
    if not isinstance(name, str):
        violations.append("name: not a string")
    elif len(name) > NAME_MAX_LENGTH:
        violations.append(f"name: longer than {NAME_MAX_LENGTH} characters")
    elif not NAME_PATTERN.match(name):
        violations.append(f"name: {name!r} does not match the schema's pattern")
    if "keywords" in root:
        keywords = root["keywords"]
        if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            violations.append("keywords: not a list of strings")
    violations.extend(
        f"{field}: differs from the Claude manifest"
        for field in HELD_EQUAL
        if root.get(field, ...) != claude.get(field, ...)
    )
    return violations


class TestEveryPortablePlugin:
    @pytest.mark.parametrize("name", PORTABLE)
    def test_carries_both_manifests(self, name: str) -> None:
        plugin = REPO_ROOT / "plugins" / name
        assert (plugin / "plugin.json").is_file()
        assert (plugin / ".claude-plugin" / "plugin.json").is_file()


class TestEveryRootManifest:
    @pytest.mark.parametrize("path", ROOT_MANIFESTS, ids=lambda path: path.parent.name)
    def test_is_well_formed_and_agrees(self, path: Path) -> None:
        root = json.loads(path.read_text())
        claude = json.loads((path.parent / ".claude-plugin" / "plugin.json").read_text())
        assert manifest_violations(root, claude) == []


AUTHOR = {"name": "A. Author", "email": "a@example.org"}
CLAUDE = {
    "name": "demo-rules",
    "version": "0.1.0",
    "description": "Demo conventions.",
    "author": AUTHOR,
    "keywords": ["demo"],
    "category": "conventions",
}
ROOT = {
    "$schema": SCHEMA,
    "name": "demo-rules",
    "version": "0.1.0",
    "description": "Demo conventions.",
    "author": AUTHOR,
    "keywords": ["demo"],
}


class TestRejections:
    def test_category_copied_over(self) -> None:
        assert manifest_violations(ROOT | {"category": "conventions"}, CLAUDE) == [
            "category: not a field the schema permits"
        ]

    def test_a_wrong_schema(self) -> None:
        assert manifest_violations(ROOT | {"$schema": "https://example.org/s.json"}, CLAUDE) == [
            f"$schema: 'https://example.org/s.json' is not {SCHEMA!r}"
        ]

    def test_a_description_that_differs(self) -> None:
        assert manifest_violations(ROOT | {"description": "Stale."}, CLAUDE) == [
            "description: differs from the Claude manifest"
        ]

    def test_an_author_with_an_extra_key(self) -> None:
        author = AUTHOR | {"twitter": "@a"}
        assert manifest_violations(ROOT | {"author": author}, CLAUDE | {"author": author}) == [
            "author.twitter: not a field the schema permits"
        ]

    def test_a_name_with_a_double_hyphen(self) -> None:
        assert manifest_violations(
            ROOT | {"name": "demo--rules"}, CLAUDE | {"name": "demo--rules"}
        ) == ["name: 'demo--rules' does not match the schema's pattern"]

    def test_a_compliant_pair(self) -> None:
        assert manifest_violations(ROOT, CLAUDE) == []
