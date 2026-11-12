"""`lint-lint check` — the audit a convergence is verified with."""

from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from agent_plugins.lintlint.cli import app
from agent_plugins.lintlint.rules import audit

Tree = Callable[[str], Path]

# Every finding planted in the `drifted` tree, as subject and rule.
DRIFTED = {
    # Three hygiene ids dropped, and hooks of the set nobody carries.
    ("check-shebang-scripts-are-executable", "missing-hook"),
    ("debug-statements", "missing-hook"),
    ("detect-private-key", "missing-hook"),
    ("nixfmt", "missing-hook"),
    ("ruff-check", "missing-hook"),
    ("uv-lock", "missing-hook"),
    ("taplo-format", "missing-hook"),
    ("rumdl-check", "missing-hook"),
    # The tools the standard retires.
    ("codespell", "retired-tool"),
    ("ruff", "retired-tool"),
    ("mypy", "retired-tool"),
    ("pip-audit", "retired-tool"),
    ("format-justfile", "retired-tool"),
    ("pyright", "retired-tool"),
    # The wrong entries.
    ("mixed-line-ending", "hook-args"),
    ("gitleaks", "hook-args"),
    ("typos", "hook-args"),
    ("ruff-format", "hook-args"),
    ("mypy", "hook-args"),
    ("pip-audit", "hook-args"),
    ("yamllint", "hook-args"),
    ("validate-pyproject", "hook-args"),
    ("ty", "hook-args"),
    ("ty", "hook-form"),
    # The pins.
    ("repos[https://github.com/pre-commit/pre-commit-hooks].rev", "rev-pin"),
    ("repos[https://github.com/crate-ci/typos].rev", "rev-pin"),
    # The linter files.
    ("", "missing-config"),
    ("extends", "config-value"),
    ("rules.document-start", "config-value"),
    ("rules.line-length.max", "config-value"),
    ("tool.ruff.lint.select", "config-value"),
    ("tool.ruff.lint.ignore", "config-value"),
    ('tool.ruff.lint.per-file-ignores."tests/**"', "config-value"),
    ("tool.uv.exclude-newer", "config-value"),
    ("dependency-groups.dev.ty", "config-value"),
    ("dependency-groups.dev.rust-just", "config-value"),
}


# A repository holding nothing but a workflow: the baseline, the markup set its
# YAML derives, and the CI trio.
WORKFLOW_REPOSITORY = {
    ".github/workflows/ci.yml": "on: push\njobs: {}\n",
    ".yamllint.yaml": (
        "extends: default\n\nrules:\n  document-start: disable\n  line-length:\n    max: 120\n"
    ),
    ".rumdl.toml": (
        "[MD013]\nline_length = 120\ntables = false\ncode_blocks = false\n\n"
        "[MD041]\nenabled = false\n"
    ),
    ".pre-commit-config.yaml": """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: mixed-line-ending
        args: [--fix=lf]
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: check-symlinks
      - id: destroyed-symlinks
      - id: check-executables-have-shebangs
      - id: check-shebang-scripts-are-executable
      - id: debug-statements
      - id: detect-private-key

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks

  - repo: https://github.com/crate-ci/typos
    rev: v1.52.0
    hooks:
      - id: typos

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.38.0
    hooks:
      - id: yamllint
        args: [--strict]

  - repo: https://github.com/ComPWA/taplo-pre-commit
    rev: v0.9.3
    hooks:
      - id: taplo-format

  - repo: https://github.com/rvben/rumdl-pre-commit
    rev: v0.3.2
    hooks:
      - id: rumdl-check
        args: [--fix]

  - repo: https://github.com/lycheeverse/lychee
    rev: lychee-v0.24.2
    hooks:
      - id: lychee
        args: [--offline, --no-progress]
        types: [markdown]

  - repo: https://github.com/rhysd/actionlint
    rev: v1.7.12
    hooks:
      - id: actionlint

  - repo: https://github.com/zizmorcore/zizmor-pre-commit
    rev: v1.24.1
    hooks:
      - id: zizmor
        args: [--offline, --no-progress]

  - repo: https://github.com/python-jsonschema/check-jsonschema
    rev: 0.39.0
    hooks:
      - id: check-github-workflows

  - repo: local
    hooks:
      - id: format-justfile
        name: format justfile
        entry: bash -c 'for f in "$@"; do just --fmt --unstable --justfile "$f"; done' --
        language: system
        files: (^|/)justfile$|\\.just$
      - id: nixfmt
        name: nixfmt
        entry: nixfmt
        language: system
        files: \\.nix$
""",
}


class TestAudit:
    def test_a_converged_repository_exits_zero_and_says_nothing(
        self, lint_data_tree_builder: Tree
    ) -> None:
        result = CliRunner().invoke(app, ["check", str(lint_data_tree_builder("compliant"))])
        assert result.exit_code == 0
        assert result.stdout == ""

    def test_a_drifted_repository_names_every_planted_finding(
        self, lint_data_tree_builder: Tree
    ) -> None:
        assert {
            (f.subject, f.rule.value) for f in audit(lint_data_tree_builder("drifted"))
        } == DRIFTED

    def test_a_drifted_repository_exits_one(self, lint_data_tree_builder: Tree) -> None:
        result = CliRunner().invoke(app, ["check", str(lint_data_tree_builder("drifted"))])
        assert result.exit_code == 1
        assert "finding(s) in 5 file(s)" in result.stdout

    def test_a_report_line_names_the_file_subject_rule_fix_and_topic(
        self, lint_data_tree_builder: Tree
    ) -> None:
        result = CliRunner().invoke(app, ["check", str(lint_data_tree_builder("drifted"))])
        assert ".pre-commit-config.yaml  [" in result.stdout
        assert (
            "    uv-lock  missing-hook: add the house entry  (skills/lint/references/python.md)"
            in result.stdout
        )

    def test_a_lockless_repository_is_told_the_runner_form_is_out(
        self, lint_data_tree_builder: Tree
    ) -> None:
        tree = lint_data_tree_builder("lockless")
        assert {(f.subject, f.rule.value) for f in audit(tree)} == {
            ("uv-lock", "stray-hook"),
            ("mypy", "hook-form"),
        }

    def test_no_configuration_is_one_finding_and_the_linter_files(
        self, lint_tree_builder: Callable[..., Path]
    ) -> None:
        tree = lint_tree_builder({"README.md": "# A\n"})
        result = CliRunner().invoke(app, ["check", str(tree)])
        assert result.exit_code == 1
        assert {(f.source.name, f.rule.value) for f in audit(tree)} == {
            (".pre-commit-config.yaml", "no-configuration"),
            (".yamllint.yaml", "missing-config"),
            (".rumdl.toml", "missing-config"),
        }

    def test_a_directory_outside_any_repository_exits_two(
        self, lint_tree_builder: Callable[..., Path]
    ) -> None:
        tree = lint_tree_builder({"README.md": ""}, repo=False)
        result = CliRunner().invoke(app, ["check", str(tree)])
        assert result.exit_code == 2

    def test_a_missing_directory_exits_two(self, tmp_path: Path) -> None:
        assert CliRunner().invoke(app, ["check", str(tmp_path / "absent")]).exit_code == 2

    def test_git_missing_exits_two(self, lint_data_tree_builder: Tree, monkeypatch) -> None:
        tree = lint_data_tree_builder("compliant")
        monkeypatch.setenv("PATH", str(tree))
        assert CliRunner().invoke(app, ["check", str(tree)]).exit_code == 2

    def test_a_subdirectory_audits_the_repository_holding_it(
        self, lint_data_tree_builder: Tree
    ) -> None:
        tree = lint_data_tree_builder("drifted")
        (tree / "deep").mkdir()
        assert audit(tree / "deep") == audit(tree)

    def test_a_repository_with_a_workflow_and_the_ci_trio_is_clean(
        self, lint_tree_builder: Callable[..., Path]
    ) -> None:
        tree = lint_tree_builder(WORKFLOW_REPOSITORY)
        assert audit(tree) == []
        result = CliRunner().invoke(app, ["check", str(tree)])
        assert result.exit_code == 0


class TestUmbrella:
    def test_the_nested_repository_is_neither_read_nor_audited(
        self, lint_data_tree_builder: Tree
    ) -> None:
        assert audit(lint_data_tree_builder("umbrella")) == []

    def test_the_nested_repository_audits_on_its_own(self, lint_data_tree_builder: Tree) -> None:
        findings = audit(lint_data_tree_builder("umbrella") / "sub")
        assert ("tflint", "missing-hook") in {(f.subject, f.rule.value) for f in findings}
        assert {f.source.parent.name for f in findings} == {"sub"}
