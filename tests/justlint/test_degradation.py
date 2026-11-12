"""Degrading without guessing: no `just`, and a file that stops parsing."""

from collections.abc import Callable
from pathlib import Path

import pytest

from agent_plugins.justlint.checker import audit, file_findings
from agent_plugins.justlint.errors import JustMissing
from agent_plugins.justlint.types import JsonObject
from tests.justlint.test_hook import FIRST_EDIT, LEGACY

UNPARSABLE = "# help in a comment\nrun\n    echo hi\n"


def _context(answer: JsonObject | None) -> str:
    assert answer is not None
    text: str = answer["hookSpecificOutput"]["additionalContext"]
    return text


class TestWithoutJust:
    @pytest.fixture
    def without_just(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A PATH with no `just` on it, as a machine that never installed one."""
        empty = tmp_path / "empty-path"
        empty.mkdir()
        monkeypatch.setenv("PATH", str(empty))

    def test_the_notice_is_stated_once_per_context(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
        without_just: None,
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(FIRST_EDIT)
        assert "not on PATH" in _context(hook_builder("PostToolUse", path=path))
        assert hook_builder("PostToolUse", path=path) is None

    def test_another_context_is_told_too(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
        without_just: None,
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PostToolUse", path=path)
        assert "not on PATH" in _context(
            hook_builder("PostToolUse", path=path, session="session-2")
        )

    def test_nothing_is_blocked(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
        without_just: None,
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PostToolUse", path=path)
        assert hook_builder("Stop", cwd=tree) is None

    def test_the_audit_says_so_and_raises(
        self, justfile_tree_builder: Callable[..., Path], without_just: None
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        with pytest.raises(JustMissing):
            audit([tree])


class TestParsingBreaks:
    def test_an_edit_that_breaks_parsing_is_reported(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(UNPARSABLE)
        assert "parse:" in _context(hook_builder("PostToolUse", path=path))

    def test_a_file_that_never_parsed_reports_nothing_new(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": UNPARSABLE})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(UNPARSABLE + "\n# another broken line\nalso\n")
        assert hook_builder("PostToolUse", path=path) is None

    def test_a_broken_file_yields_the_parse_finding_alone(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": UNPARSABLE})
        assert [f.rule.value for f in file_findings(tree / "justfile")] == ["parse"]
