"""The ratchet's state on disk: what is pruned, and what is spared.

Seven days untouched is the line. Nothing is pruned at SessionEnd, because a
desktop session is resumed after one and a baseline dropped there would turn a
violation left before the exit into legacy.
"""

import os
import time
from collections.abc import Callable
from pathlib import Path

from agent_plugins.justlint.consts import PRUNE_AFTER
from agent_plugins.justlint.state import LintState, prune, state_root
from agent_plugins.justlint.types import JsonObject
from tests.justlint.test_hook import FIRST_EDIT, LEGACY

DAY = 24 * 60 * 60


def _age(path: Path, days: float) -> None:
    when = time.time() - days * DAY
    for file in path.rglob("*"):
        if file.is_file():
            os.utime(file, (when, when))


class TestPruning:
    def test_fresh_state_is_spared(
        self,
        justfile_tree: Callable[..., Path],
        hook: Callable[..., JsonObject | None],
        plugin_data: Path,
    ) -> None:
        tree = justfile_tree({"justfile": LEGACY})
        hook("PreToolUse", path=tree / "justfile")
        prune(state_root())
        assert LintState.for_context("session-1", None).baseline(tree / "justfile") is not None

    def test_state_untouched_for_a_week_is_dropped(
        self,
        justfile_tree: Callable[..., Path],
        hook: Callable[..., JsonObject | None],
        plugin_data: Path,
    ) -> None:
        tree = justfile_tree({"justfile": LEGACY})
        hook("PreToolUse", path=tree / "justfile")
        _age(plugin_data, PRUNE_AFTER.days + 1)
        prune(state_root())
        assert LintState.for_context("session-1", None).baseline(tree / "justfile") is None
        assert not any(state_root().iterdir())

    def test_a_stop_prunes_but_spares_this_turn(
        self,
        justfile_tree: Callable[..., Path],
        hook: Callable[..., JsonObject | None],
        plugin_data: Path,
    ) -> None:
        tree = justfile_tree({"justfile": LEGACY})
        path = tree / "justfile"
        hook("PreToolUse", path=path)
        path.write_text(FIRST_EDIT)
        # An old context of another session, beside this turn's fresh one.
        stale = LintState.for_context("session-old", None)
        stale.record_baseline(tree / "other", set())
        _age(stale.directory, PRUNE_AFTER.days + 1)
        answer = hook("Stop", cwd=tree)
        assert answer is not None and answer["decision"] == "block"
        assert not stale.directory.exists()

    def test_a_session_ending_prunes_nothing(
        self,
        justfile_tree: Callable[..., Path],
        hook: Callable[..., JsonObject | None],
        plugin_data: Path,
    ) -> None:
        tree = justfile_tree({"justfile": LEGACY})
        hook("PreToolUse", path=tree / "justfile")
        hook("SessionEnd", cwd=tree)
        assert LintState.for_context("session-1", None).baseline(tree / "justfile") is not None


class TestContextKeys:
    def test_a_subagent_gets_its_own_directory(self, plugin_data: Path) -> None:
        main = LintState.for_context("session-1", None)
        subagent = LintState.for_context("session-1", "agent-7")
        assert main.directory != subagent.directory

    def test_a_session_id_is_not_a_path(self, plugin_data: Path) -> None:
        state = LintState.for_context("../../escape", None)
        assert state.directory.parent == state_root()
