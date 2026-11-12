"""The ratchet: a baseline before the context's first edit, and afterwards only
what that context introduced. One test per scenario of the spec's "only findings
the context introduced" and "degrades without guessing" requirements.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from agent_plugins.lintlint.consts import INLINE_LIMIT
from agent_plugins.lintlint.rules import audit
from agent_plugins.lintlint.types import JsonObject

CONFIG = ".pre-commit-config.yaml"
Tree = Callable[[str], Path]
Hook = Callable[..., JsonObject | None]


def context(answer: JsonObject | None) -> str:
    assert answer is not None
    assert answer["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    text: str = answer["hookSpecificOutput"]["additionalContext"]
    return text


def reported(answer: JsonObject | None) -> list[str]:
    return [line.strip() for line in context(answer).splitlines()[1:]]


def rewrite(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new))


class TestRatchet:
    def test_a_configuration_written_where_none_existed_is_reported_whole(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        path = tree / CONFIG
        text = path.read_text()
        path.unlink()
        assert lint_hook_builder("PreToolUse", path=path, tool="Write", cwd=tree) is None
        path.write_text(text.replace("      - id: yamllint\n        args: [--strict]\n", ""))
        report = context(lint_hook_builder("PostToolUse", path=path, tool="Write", cwd=tree))
        assert "1 finding(s) introduced" in report
        assert ".pre-commit-config.yaml  yamllint  missing-hook" in report

    def test_a_first_written_file_reports_every_finding(
        self, lint_tree_builder: Callable[..., Path], lint_hook_builder: Hook
    ) -> None:
        tree = lint_tree_builder({"README.md": "# A\n"})
        path = tree / CONFIG
        lint_hook_builder("PreToolUse", path=path, tool="Write")
        path.write_text("repos: []\n")
        answer = lint_hook_builder("PostToolUse", path=path, tool="Write")
        expected = [f for f in audit(tree) if f.source == path]
        assert len(reported(answer)) == len(expected) > 19

    def test_a_legacy_configuration_touched_without_a_new_finding(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("drifted") / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        path.write_text(f"# A comment.\n{path.read_text()}")
        assert lint_hook_builder("PostToolUse", path=path) is None

    def test_a_legacy_configuration_gains_a_finding(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        rewrite(path, "rev: v1.50.3", "rev: v1")
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, "args: [--strict]", "args: []")
        lines = reported(lint_hook_builder("PostToolUse", path=path))
        assert len(lines) == 1
        assert "yamllint  hook-args: `--strict` is missing" in lines[0]

    def test_a_renamed_hook_is_new(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, "id: ruff-check", "id: ruff")
        lines = reported(lint_hook_builder("PostToolUse", path=path))
        assert any("ruff  retired-tool" in line for line in lines)
        assert any("ruff-check  missing-hook" in line for line in lines)

    def test_the_python_project_file_is_the_audit_s(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        path = tree / "pyproject.toml"
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, 'exclude-newer = "7 days"', 'exclude-newer = "1 day"')
        assert lint_hook_builder("PostToolUse", path=path) is None
        assert audit(tree) != []

    def test_a_finding_about_another_file_is_not_introduced(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        (tree / ".rumdl.toml").unlink()
        path = tree / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        path.write_text(f"# A comment.\n{path.read_text()}")
        assert lint_hook_builder("PostToolUse", path=path) is None
        assert lint_hook_builder("Stop", cwd=tree) is None

    def test_a_file_the_context_never_edited_says_nothing(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("drifted")
        path = tree / ".yamllint.yaml"
        lint_hook_builder("PreToolUse", path=path)
        path.write_text(f"# A comment.\n{path.read_text()}")
        answer = lint_hook_builder("PostToolUse", path=path)
        assert answer is None
        assert lint_hook_builder("Stop", cwd=tree) is None

    def test_an_ungoverned_file_reports_nothing(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("drifted") / "README.md"
        assert lint_hook_builder("PreToolUse", path=path) is None
        path.write_text("changed\n")
        assert lint_hook_builder("PostToolUse", path=path) is None

    def test_a_linter_file_is_ratcheted_on_its_own(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / ".yamllint.yaml"
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, "max: 120", "max: 80")
        lines = reported(lint_hook_builder("PostToolUse", path=path))
        assert len(lines) == 1
        assert "rules.line-length.max  config-value" in lines[0]

    def test_a_resumed_session_still_owes_its_findings(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        path = tree / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, "args: [--strict]", "args: []")
        lint_hook_builder("PostToolUse", path=path)
        assert lint_hook_builder("SessionEnd") is None
        path.write_text(f"# Resumed.\n{path.read_text()}")
        assert "yamllint" in context(lint_hook_builder("PostToolUse", path=path))

    def test_a_baseline_is_taken_once(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, "args: [--strict]", "args: []")
        lint_hook_builder("PostToolUse", path=path)
        lint_hook_builder("PreToolUse", path=path)
        path.write_text(f"# Again.\n{path.read_text()}")
        assert "yamllint" in context(lint_hook_builder("PostToolUse", path=path))

    def test_a_subagent_keeps_its_own_baseline(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, "args: [--strict]", "args: []")
        lint_hook_builder("PostToolUse", path=path)
        lint_hook_builder("PreToolUse", path=path, agent="agent-7")
        assert lint_hook_builder("PostToolUse", path=path, agent="agent-7") is None

    def test_an_edit_no_baseline_preceded_adopts_what_is_there(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("drifted") / CONFIG
        assert lint_hook_builder("PostToolUse", path=path) is None
        assert lint_hook_builder("PostToolUse", path=path) is None

    def test_a_nested_repository_s_file_is_judged_by_its_own_signals(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("umbrella") / "sub" / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        path.write_text("repos:\n  - repo: local\n    hooks: []\n")
        assert lint_hook_builder("PostToolUse", path=path) is None
        path.write_text("repos: [\n")
        assert "parse" in context(lint_hook_builder("PostToolUse", path=path))

    def test_a_report_past_the_inline_limit_says_how_many_remain(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        hooks = "".join(
            f"      - id: format-{index}\n        entry: npx dprint fmt\n        language: system\n"
            for index in range(300)
        )
        with path.open("a") as stream:
            stream.write(hooks)
        report = context(lint_hook_builder("PostToolUse", path=path))
        assert len(report) <= INLINE_LIMIT
        assert "more — run `lint-lint check` for the rest" in report


class TestDegradation:
    def test_git_missing_is_said_once_and_blocks_nothing(
        self,
        lint_data_tree_builder: Tree,
        lint_hook_builder: Hook,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        path = tree / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        rewrite(path, "args: [--strict]", "args: []")
        monkeypatch.setenv("PATH", str(tmp_path))
        assert "lint checks are off" in context(lint_hook_builder("PostToolUse", path=path))
        assert lint_hook_builder("PostToolUse", path=path) is None
        assert lint_hook_builder("Stop", cwd=tree) is None

    def test_git_missing_before_the_edit_records_no_baseline(
        self,
        lint_data_tree_builder: Tree,
        lint_hook_builder: Hook,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        monkeypatch.setenv("PATH", str(tmp_path))
        assert lint_hook_builder("PreToolUse", path=path) is None
        assert "lint checks are off" in context(lint_hook_builder("PostToolUse", path=path))

    def test_an_edit_that_breaks_parsing(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        lint_hook_builder("PreToolUse", path=path)
        path.write_text("repos: [\n")
        lines = reported(lint_hook_builder("PostToolUse", path=path))
        assert len(lines) == 1
        assert "<file>  parse" in lines[0]

    def test_a_file_that_never_parsed_reports_nothing_new(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        path = lint_data_tree_builder("compliant") / CONFIG
        path.write_text("repos: [\n")
        lint_hook_builder("PreToolUse", path=path)
        path.write_text("repos: [\n  # still broken\n")
        assert lint_hook_builder("PostToolUse", path=path) is None

    def test_a_shell_rewrite_is_the_audit_s(
        self, lint_data_tree_builder: Tree, lint_hook_builder: Hook
    ) -> None:
        tree = lint_data_tree_builder("compliant")
        rewrite(tree / CONFIG, "args: [--strict]", "args: []")
        assert lint_hook_builder("Stop", cwd=tree) is None
        assert audit(tree) != []

    def test_a_governed_file_outside_any_repository_reports_nothing(
        self, lint_tree_builder: Callable[..., Path], lint_hook_builder: Hook
    ) -> None:
        tree = lint_tree_builder({CONFIG: "repos: [\n"}, repo=False)
        lint_hook_builder("PreToolUse", path=tree / CONFIG)
        assert lint_hook_builder("PostToolUse", path=tree / CONFIG) is None
