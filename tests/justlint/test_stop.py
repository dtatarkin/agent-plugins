"""The Stop and SubagentStop gate: one block per prompt, for this context's
own files only.

The guard is the prompt, never `stop_hook_active`: that flag is also true after
another hook's block, and keying on it would let this gate fall silent exactly
when a turn was kept alive for someone else's reason.
"""

from collections.abc import Callable
from pathlib import Path

from agent_plugins.justlint.types import JsonObject
from tests.justlint.test_hook import FIRST_EDIT, LEGACY, SECOND_EDIT


def _blocked(answer: JsonObject | None) -> str:
    assert answer is not None
    assert answer["decision"] == "block"
    reason: str = answer["reason"]
    return reason


def _introduce(
    tree: Path, hook_builder: Callable[..., JsonObject | None], **context: object
) -> Path:
    """Take a baseline, then break the file the way an agent's edit would."""
    path = tree / "justfile"
    hook_builder("PreToolUse", path=path, **context)
    path.write_text(FIRST_EDIT)
    hook_builder("PostToolUse", path=path, **context)
    return path


class TestStopGate:
    def test_it_blocks_once_with_the_open_findings(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        _introduce(tree, hook_builder)
        reason = _blocked(hook_builder("Stop", cwd=tree))
        assert "release  doc-attr" in reason
        assert "test  splat" in reason

    def test_the_next_stop_for_the_same_prompt_passes(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        _introduce(tree, hook_builder)
        _blocked(hook_builder("Stop", cwd=tree))
        assert hook_builder("Stop", cwd=tree, stop_hook_active=True) is None

    def test_a_later_prompt_is_gated_again(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        _introduce(tree, hook_builder)
        _blocked(hook_builder("Stop", cwd=tree))
        assert hook_builder("Stop", cwd=tree) is None
        _blocked(hook_builder("Stop", cwd=tree, prompt="prompt-2"))

    def test_another_hook_s_block_does_not_skip_the_gate(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        _introduce(tree, hook_builder)
        # The turn is already alive because another hook blocked first. This
        # gate has not blocked for the prompt, so it still must.
        _blocked(hook_builder("Stop", cwd=tree, stop_hook_active=True))

    def test_a_context_without_lint_state_is_never_blocked(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": FIRST_EDIT})
        assert hook_builder("Stop", cwd=tree) is None

    def test_a_fixed_context_passes(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = _introduce(tree, hook_builder)
        path.write_text(SECOND_EDIT)
        assert hook_builder("Stop", cwd=tree) is None

    def test_a_context_that_only_read_is_never_blocked(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": FIRST_EDIT})
        # The compaction summarizer's shape: a subagent that edited nothing.
        assert hook_builder("SubagentStop", cwd=tree, agent="summarizer") is None


class TestSubagentScope:
    def test_a_subagent_gates_on_its_own_files(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        _introduce(tree, hook_builder, agent="agent-7")
        assert hook_builder("Stop", cwd=tree) is None
        _blocked(hook_builder("SubagentStop", cwd=tree, agent="agent-7"))
