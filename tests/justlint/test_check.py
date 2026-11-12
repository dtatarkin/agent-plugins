"""`just-lint check` — the audit mode a cleanup pass is verified with.

The umbrella case is a synthetic umbrella repository: a root justfile that
loads three nested repositories with `mod` and imports a `.just` dotfile. Its
legacy recipes are planted to give this block:

    justfile  [6]
        - provision: public recipe without [doc] (bare-comment help)
        - serve: public recipe without [doc] (no help at all)
        - serve: splats variadic {{ args }} into body
        - shell: public recipe without [doc] (bare-comment help)
        - shell: splats variadic {{ args }} into body
        - sync-docs: public recipe without [doc] (bare-comment help)

Every nested repository carries legacy recipes of its own, which are exactly
what this audit must leave alone.
"""

from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from agent_plugins.justlint.checker import audit
from agent_plugins.justlint.cli import app

# The umbrella's block for its root justfile, as rule ids.
UMBRELLA_FINDINGS = {
    ("provision", "doc-attr"),
    ("serve", "doc-attr"),
    ("serve", "splat"),
    ("shell", "doc-attr"),
    ("shell", "splat"),
    ("sync-docs", "doc-attr"),
}

# The sub-repositories the umbrella loads with `mod`, none of them its business.
NESTED_REPOSITORIES = ("shared", "app", "ops")


class TestUmbrellaAudit:
    def test_the_planted_findings_are_reported(
        self, data_tree_builder: Callable[[str], Path]
    ) -> None:
        tree = data_tree_builder("umbrella")
        findings = audit([tree])
        assert {(f.subject, f.rule.value) for f in findings} == UMBRELLA_FINDINGS

    def test_the_findings_come_from_the_root_justfile_alone(
        self, data_tree_builder: Callable[[str], Path]
    ) -> None:
        tree = data_tree_builder("umbrella")
        assert {f.source for f in audit([tree])} == {tree / "justfile"}

    def test_the_details_keep_both_flavours(self, data_tree_builder: Callable[[str], Path]) -> None:
        tree = data_tree_builder("umbrella")
        details = {f.subject: f.detail for f in audit([tree]) if f.rule.value == "doc-attr"}
        assert details["serve"] == "no help at all"
        assert details["sync-docs"] == "bare-comment help"


class TestRepositoryBoundary:
    def test_no_module_inside_a_nested_repository_is_reported(
        self, data_tree_builder: Callable[[str], Path]
    ) -> None:
        tree = data_tree_builder("umbrella")
        reported = {str(f.source.relative_to(tree)).split("/")[0] for f in audit([tree])}
        assert reported.isdisjoint(NESTED_REPOSITORIES)

    def test_the_nested_repository_audits_on_its_own(
        self, data_tree_builder: Callable[[str], Path]
    ) -> None:
        tree = data_tree_builder("umbrella")
        findings = audit([tree / "app"])
        assert {(f.subject, f.rule.value) for f in findings} == {
            ("run", "doc-attr"),
            ("run", "splat"),
        }


class TestAuditCommand:
    def test_a_repository_with_legacy_recipes_exits_one(
        self, data_tree_builder: Callable[[str], Path]
    ) -> None:
        result = CliRunner().invoke(app, ["check", str(data_tree_builder("violating"))])
        assert result.exit_code == 1
        assert "module-preamble" in result.stdout
        assert "10 finding(s) in 2 file(s)" in result.stdout

    def test_a_clean_repository_exits_zero_and_says_nothing(self, data_tree: Path) -> None:
        result = CliRunner().invoke(app, ["check", str(data_tree)])
        assert result.exit_code == 0
        assert result.stdout == ""

    def test_a_missing_path_is_a_usage_failure(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["check", str(tmp_path / "absent")])
        assert result.exit_code == 2
