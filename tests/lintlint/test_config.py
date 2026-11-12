"""The parsed hook configuration: what the runner reads, never the file's text."""

from collections.abc import Callable
from pathlib import Path

import pytest

from agent_plugins.lintlint.config import load_hook_config, load_ruff, lookup
from agent_plugins.lintlint.errors import ConfigParseFailed
from agent_plugins.lintlint.rules import audit
from agent_plugins.lintlint.types import RuleId

ALIASED = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
        exclude: &generated ^src/generated/
      - id: end-of-file-fixer
        exclude: *generated
  - repo: local
    hooks:
      - id: mypy
        entry: uv run mypy
        args: [--strict]
        types: [python]
        pass_filenames: false
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / ".pre-commit-config.yaml"
    path.write_text(text)
    return path


class TestHookConfig:
    def test_an_alias_resolves(self, tmp_path: Path) -> None:
        config = load_hook_config(_write(tmp_path, ALIASED))
        assert config is not None
        assert config.hooks[1].exclude == "^src/generated/"

    def test_entries_keep_their_repository_and_order(self, tmp_path: Path) -> None:
        config = load_hook_config(_write(tmp_path, ALIASED))
        assert config is not None
        assert [hook.id for hook in config.hooks] == [
            "trailing-whitespace",
            "end-of-file-fixer",
            "mypy",
        ]
        assert config.hooks[2].repo == "local"
        assert config.hooks[2].command == "uv run mypy --strict"
        assert config.hooks[2].pass_filenames is False
        assert config.pins[0].rev == "v6.0.0"

    def test_a_missing_file_is_none(self, tmp_path: Path) -> None:
        assert load_hook_config(tmp_path / ".pre-commit-config.yaml") is None

    @pytest.mark.parametrize("text", ["repos: [\n", "hooks: []\n", "just a string\n", "repos: 1\n"])
    def test_an_unparsable_file_raises(self, tmp_path: Path, text: str) -> None:
        with pytest.raises(ConfigParseFailed):
            load_hook_config(_write(tmp_path, text))

    @pytest.mark.parametrize("text", ["repos: [\n", "hooks: []\n"])
    def test_it_is_one_parse_finding_and_no_rule_findings(
        self, lint_tree: Callable[..., Path], text: str
    ) -> None:
        tree = lint_tree({".pre-commit-config.yaml": text})
        findings = [f for f in audit(tree) if f.source.name == ".pre-commit-config.yaml"]
        assert [f.rule for f in findings] == [RuleId.PARSE]


class TestRuff:
    def test_its_own_file_outranks_the_project_file(self, tmp_path: Path) -> None:
        (tmp_path / "ruff.toml").write_text('[lint]\nselect = ["S"]\n')
        ruff = load_ruff(tmp_path, {"tool": {"ruff": {"lint": {"select": ["E"]}}}})
        assert ruff is not None
        assert ruff.source == tmp_path / "ruff.toml"
        assert ruff.lint == {"select": ["S"]}
        assert ruff.prefix == "lint"

    def test_the_project_file_s_table(self, tmp_path: Path) -> None:
        ruff = load_ruff(tmp_path, {"tool": {"ruff": {"lint": {"select": ["E"]}}}})
        assert ruff is not None
        assert ruff.prefix == "tool.ruff.lint"

    def test_no_table_at_all(self, tmp_path: Path) -> None:
        assert load_ruff(tmp_path, {"project": {}}) is None


def test_lookup_walks_a_dotted_key() -> None:
    document = {"rules": {"line-length": {"max": 120}}}
    assert lookup(document, "rules.line-length.max") == 120
    assert lookup(document, "rules.line-length.min") is None
    assert lookup(document, "rules.line-length.max.deeper") is None
