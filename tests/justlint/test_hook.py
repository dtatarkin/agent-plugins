"""The ratchet: a baseline before the context's first edit, and afterwards
only what that context introduced.

The first sequence replays the hook spike's `real-lint-noattach` run of
2026-09-11 verbatim — the legacy file it started from, the edit that added
`test` and `release`, and the follow-up that fixed them. The prototype
reported four findings after the first edit and stayed silent after the
second; so must this.
"""

from collections.abc import Callable
from pathlib import Path

from agent_plugins.justlint.consts import INLINE_LIMIT
from agent_plugins.justlint.types import JsonObject

LEGACY = """# Say hello
hello:
    echo hello

# Run the app with extra args
run *args:
    uv run app {{ args }}
"""

FIRST_EDIT = (
    LEGACY
    + """
# Run tests with optional arguments
test *args:
    uv run pytest {{ args }}

# Bump version and create git tag
release:
    uv version --bump patch
    git tag v$(uv version)
"""
)

SECOND_EDIT = (
    LEGACY
    + """
[doc("Run tests with optional arguments")]
[positional-arguments]
test *args:
    uv run pytest "$@"

[doc("Bump version and create git tag")]
release:
    #!/usr/bin/env bash
    set -euo pipefail
    uv version --bump patch
    git tag v$(uv version)
"""
)

# What the spike's prototype reported after the first edit.
SPIKE_FINDINGS = [
    ("release", "doc-attr"),
    ("release", "shebang"),
    ("test", "doc-attr"),
    ("test", "splat"),
]


def _context(answer: JsonObject | None) -> str:
    assert answer is not None
    context: str = answer["hookSpecificOutput"]["additionalContext"]
    assert answer["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    return context


def _reported(answer: JsonObject | None) -> list[str]:
    return [line.strip() for line in _context(answer).splitlines()[1:]]


class TestSpikeSequence:
    def test_four_findings_after_the_first_edit(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        assert hook_builder("PreToolUse", path=path) is None
        path.write_text(FIRST_EDIT)
        reported = _reported(hook_builder("PostToolUse", path=path))
        assert len(reported) == len(SPIKE_FINDINGS)
        for recipe, rule in SPIKE_FINDINGS:
            assert any(line.startswith(f"justfile  {recipe}  {rule}:") for line in reported)

    def test_the_legacy_recipes_are_not_reported(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(FIRST_EDIT)
        reported = " ".join(_reported(hook_builder("PostToolUse", path=path)))
        assert "hello" not in reported
        assert "  run  " not in reported

    def test_silence_after_the_fix(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(FIRST_EDIT)
        hook_builder("PostToolUse", path=path)
        hook_builder("PreToolUse", path=path)
        path.write_text(SECOND_EDIT)
        assert hook_builder("PostToolUse", path=path) is None


class TestBaseline:
    def test_a_new_file_starts_empty_and_reports_everything(
        self, justfile_tree: Path, hook_builder: Callable[..., JsonObject | None]
    ) -> None:
        tree = justfile_tree
        path = tree / "justfile"
        assert hook_builder("PreToolUse", path=path, tool="Write") is None
        path.write_text(LEGACY)
        reported = _reported(hook_builder("PostToolUse", path=path, tool="Write"))
        assert len(reported) == 3

    def test_a_renamed_recipe_counts_as_new(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(LEGACY.replace("hello:", "greet:"))
        reported = _reported(hook_builder("PostToolUse", path=path))
        assert [line.split("  ")[1] for line in reported] == ["greet"]

    def test_a_recipe_copied_from_a_legacy_neighbour_is_new(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        # `run`'s violations are legacy; the copy beside it is this context's.
        path.write_text(LEGACY + "\n# Run the app twice\nrerun *args:\n    uv run app {{ args }}\n")
        reported = _reported(hook_builder("PostToolUse", path=path))
        assert {line.split("  ")[1] for line in reported} == {"rerun"}
        assert {line.split(":")[0].split("  ")[-1] for line in reported} == {"doc-attr", "splat"}

    def test_a_legacy_recipe_touched_without_a_new_violation_is_silent(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(LEGACY.replace("uv run app", "uv run application"))
        assert hook_builder("PostToolUse", path=path) is None

    def test_a_legacy_recipe_that_gains_one_reports_only_that(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        # `run` already breaks doc-attr and splat; the second line is new.
        path.write_text(LEGACY.replace("    uv run app {{ args }}", "    echo one\n    echo two"))
        reported = _reported(hook_builder("PostToolUse", path=path))
        assert [line.split(":")[0].split("  ")[-1] for line in reported] == ["shebang"]

    def test_the_baseline_is_taken_once_per_context(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(FIRST_EDIT)
        # A second PreToolUse must not adopt the damage as the new baseline.
        hook_builder("PreToolUse", path=path)
        assert len(_reported(hook_builder("PostToolUse", path=path))) == len(SPIKE_FINDINGS)

    def test_another_context_keeps_its_own_baseline(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(FIRST_EDIT)
        # A subagent of the same session: its own context, its own baseline,
        # taken from the file as it stands when that context first edits it.
        hook_builder("PreToolUse", path=path, agent="agent-7")
        assert hook_builder("PostToolUse", path=path, agent="agent-7") is None

    def test_a_baseline_outlives_the_session_ending(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY})
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path)
        path.write_text(FIRST_EDIT)
        hook_builder("PostToolUse", path=path)
        # The session ends and is resumed: same id, same state, still new.
        assert len(_reported(hook_builder("PostToolUse", path=path))) == len(SPIKE_FINDINGS)


class TestFileFilter:
    def test_another_file_kind_yields_nothing(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
        plugin_data: Path,
    ) -> None:
        tree = justfile_tree_builder({"justfile": LEGACY, "notes.txt": "not a justfile\n"})
        notes = tree / "notes.txt"
        assert hook_builder("PreToolUse", path=notes) is None
        notes.write_text("still not a justfile\n")
        assert hook_builder("PostToolUse", path=notes) is None
        assert not plugin_data.exists()

    def test_a_dotfile_and_a_module_are_both_watched(
        self,
        justfile_tree_builder: Callable[..., Path],
        hook_builder: Callable[..., JsonObject | None],
    ) -> None:
        tree = justfile_tree_builder({"justfile": "import? '.just'\n", ".just": ""})
        local = tree / ".just"
        hook_builder("PreToolUse", path=local)
        local.write_text("claude *args:\n    claude {{ args }}\n")
        reported = _reported(hook_builder("PostToolUse", path=local))
        assert {line.split(":")[0].split("  ")[-1] for line in reported} == {"doc-attr", "splat"}


class TestInlineLimit:
    def test_a_report_over_the_limit_names_the_remainder(
        self, justfile_tree: Path, hook_builder: Callable[..., JsonObject | None]
    ) -> None:
        crowded = "".join(
            f"# recipe {index}\nrecipe-{index:03d}:\n    echo one\n    echo two\n\n"
            for index in range(200)
        )
        tree = justfile_tree
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path, tool="Write")
        path.write_text(crowded)
        context = _context(hook_builder("PostToolUse", path=path, tool="Write"))
        assert len(context) <= INLINE_LIMIT
        remainder = context.splitlines()[-1].strip()
        assert remainder.startswith("… and ")
        assert "more" in remainder

    def test_a_report_under_the_limit_names_no_remainder(
        self, justfile_tree: Path, hook_builder: Callable[..., JsonObject | None]
    ) -> None:
        tree = justfile_tree
        path = tree / "justfile"
        hook_builder("PreToolUse", path=path, tool="Write")
        path.write_text(LEGACY)
        assert "… and " not in _context(hook_builder("PostToolUse", path=path, tool="Write"))
