"""Guards the `if` filters of the `just-rules` hooks against the topics' `paths:`.

The ratchet acts on exactly the files the topics attach on, and each of those
files reaches it through one `if` per glob per tool. A topic gaining a glob the
manifest does not list would leave that file unwatched, silently: a hook whose
filter never fires reports nothing. This is the test that notices.
"""

import json
from pathlib import Path

import pytest

from agent_plugins.justlint.resolve import is_checked_file

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "just-rules"
EDIT_EVENTS = ("PreToolUse", "PostToolUse")


def paths_union() -> set[str]:
    """Every glob of every topic's frontmatter."""
    globs: set[str] = set()
    for topic in (PLUGIN_DIR / "skills" / "just" / "references").glob("*.md"):
        for line in topic.read_text().split("---")[1].splitlines():
            if line.startswith("  - "):
                globs.add(line.strip(' -"'))
    return globs


def if_filters(event: str) -> set[str]:
    manifest = json.loads((PLUGIN_DIR / "hooks" / "hooks.json").read_text())
    return {hook["if"] for group in manifest["hooks"][event] for hook in group["hooks"]}


class TestJustHookFilters:
    @pytest.mark.parametrize("event", EDIT_EVENTS)
    def test_the_filters_equal_the_topics_paths(self, event: str) -> None:
        expected = {f"{tool}({glob})" for tool in ("Edit", "Write") for glob in paths_union()}
        assert if_filters(event) == expected

    @pytest.mark.parametrize("glob", sorted(paths_union()))
    def test_the_checker_acts_on_every_topic_glob(self, glob: str) -> None:
        assert is_checked_file(Path(glob.replace("*", "example")))

    @pytest.mark.parametrize("event", ["Stop", "SubagentStop"])
    def test_the_turn_end_gate_is_unconditional(self, event: str) -> None:
        manifest = json.loads((PLUGIN_DIR / "hooks" / "hooks.json").read_text())
        hooks = [hook for group in manifest["hooks"][event] for hook in group["hooks"]]
        assert [hook.get("if") for hook in hooks] == [None]
