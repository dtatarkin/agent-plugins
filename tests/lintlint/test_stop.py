"""The Stop and SubagentStop gate: one block per prompt, for this context's own
files only.

The guard is the prompt, never `stop_hook_active`: that flag is also true after
another hook's block, and keying on it would let this gate fall silent exactly
when a turn was kept alive for someone else's reason.
"""

from collections.abc import Callable
from pathlib import Path

from agent_plugins.lintlint.types import JsonObject

CONFIG = ".pre-commit-config.yaml"
Tree = Callable[[str], Path]
Hook = Callable[..., JsonObject | None]


def blocked(answer: JsonObject | None) -> str:
    assert answer is not None
    assert answer["decision"] == "block"
    reason: str = answer["reason"]
    return reason


def introduce(tree: Path, hook: Hook, **context: object) -> Path:
    """Take a baseline, then break the file the way an agent's edit would."""
    path = tree / CONFIG
    hook("PreToolUse", path=path, **context)
    path.write_text(path.read_text().replace("args: [--strict]", "args: []"))
    hook("PostToolUse", path=path, **context)
    return path


class TestStopGate:
    def test_it_blocks_once_with_the_open_findings(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        introduce(tree, lint_hook_builder)
        assert "yamllint  hook-args" in blocked(lint_hook_builder("Stop", cwd=tree))

    def test_the_next_stop_for_the_same_prompt_passes(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        introduce(tree, lint_hook_builder)
        blocked(lint_hook_builder("Stop", cwd=tree))
        assert lint_hook_builder("Stop", cwd=tree, stop_hook_active=True) is None

    def test_a_later_prompt_is_gated_again(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        introduce(tree, lint_hook_builder)
        blocked(lint_hook_builder("Stop", cwd=tree))
        blocked(lint_hook_builder("Stop", cwd=tree, prompt="prompt-2"))

    def test_another_hook_s_block_does_not_skip_the_gate(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        introduce(tree, lint_hook_builder)
        blocked(lint_hook_builder("Stop", cwd=tree, stop_hook_active=True))

    def test_a_context_that_edited_nothing_is_never_blocked(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("drifted")
        assert lint_hook_builder("Stop", cwd=tree) is None
        # The compaction summarizer's shape: a subagent that edited nothing.
        assert lint_hook_builder("SubagentStop", cwd=tree, agent="summarizer") is None

    def test_a_fixed_context_passes(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        path = introduce(tree, lint_hook_builder)
        path.write_text(path.read_text().replace("args: []", "args: [--strict]"))
        assert lint_hook_builder("Stop", cwd=tree) is None


class TestSubagentScope:
    def test_a_subagent_gates_on_its_own_files(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        introduce(tree, lint_hook_builder, agent="agent-7")
        assert lint_hook_builder("Stop", cwd=tree) is None
        blocked(lint_hook_builder("SubagentStop", cwd=tree, agent="agent-7"))
