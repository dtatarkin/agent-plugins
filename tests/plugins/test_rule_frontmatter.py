"""Guards the contract a rule file meets when it declares the paths it governs.

Only a file carrying `paths:` frontmatter attaches on touch, where path-scoped
attachment is set up, and only such a file is held to this contract. A harness
loads an unscoped file — and anything a scoped file imports — into every
session unconditionally, so an empty glob list, a stray frontmatter key, or an
import would turn an on-touch rule into an always-on one. That is the failure
this test exists to catch, before any harness attaches the file.
"""

import io
from pathlib import Path

import pytest
from ruamel.yaml import YAML

REPO_ROOT = Path(__file__).resolve().parents[2]
RULE_FILES = sorted(REPO_ROOT.glob("plugins/*/skills/*/references/*.md"))

_yaml = YAML(typ="safe")


def _frontmatter(text: str) -> str | None:
    """The frontmatter block, or None when the file opens with anything else."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])
    return None


def declares_paths(text: str) -> bool:
    """Whether the file is scoped — the condition for attaching it on touch."""
    block = _frontmatter(text)
    if block is None:
        return False
    loaded = _yaml.load(io.StringIO(block))
    return isinstance(loaded, dict) and "paths" in loaded


def frontmatter_violations(text: str) -> list[str]:
    """Violations of the scoped-rule-file contract; empty for a compliant file.

    A file with no frontmatter, or whose frontmatter declares no `paths:`, never
    attaches on touch, so it is unconstrained here.
    """
    if not declares_paths(text):
        return []
    block = _frontmatter(text)
    assert block is not None
    loaded = _yaml.load(io.StringIO(block))

    violations: list[str] = []

    extra = sorted(key for key in loaded if key != "paths")
    if extra:
        violations.append(f"frontmatter holds more than `paths:`: {', '.join(map(str, extra))}")

    globs = loaded["paths"]
    if (
        not isinstance(globs, list)
        or not globs
        or not all(isinstance(glob, str) and glob.strip() for glob in globs)
    ):
        violations.append("`paths:` is not a non-empty list of globs")

    # An import is written as a line opening with `@<path>`; the estate's rule
    # files are prose, so a line-leading `@` is an import and nothing else.
    imports = [
        line.strip()
        for line in text.splitlines()
        if line.lstrip().startswith("@") and len(line.strip()) > 1
    ]
    if imports:
        violations.append(f"linked file imports: {', '.join(imports)}")

    return violations


class TestEveryRuleFile:
    def test_some_rule_file_declares_paths(self) -> None:
        """Keeps the parametrized test below from passing vacuously."""
        scoped = [path for path in RULE_FILES if declares_paths(path.read_text())]
        assert scoped, "no rule file carries `paths:` — the attachment contract is unguarded"

    @pytest.mark.parametrize("path", RULE_FILES, ids=lambda path: f"{path.parts[-5]}/{path.name}")
    def test_is_linkable_or_unscoped(self, path: Path) -> None:
        assert frontmatter_violations(path.read_text()) == []


class TestRejections:
    def test_an_import_in_a_linked_file(self) -> None:
        text = '---\npaths:\n  - "**/justfile"\n---\nRules.\n\n@/home/someone/other.md\n'
        assert frontmatter_violations(text) == ["linked file imports: @/home/someone/other.md"]

    def test_an_empty_glob_list(self) -> None:
        text = "---\npaths: []\n---\nRules.\n"
        assert frontmatter_violations(text) == ["`paths:` is not a non-empty list of globs"]

    def test_a_second_frontmatter_key(self) -> None:
        text = '---\nname: recipes\npaths:\n  - "**/justfile"\n---\nRules.\n'
        assert frontmatter_violations(text) == ["frontmatter holds more than `paths:`: name"]

    def test_an_unscoped_file_is_unconstrained(self) -> None:
        assert frontmatter_violations("# Rules\n\n@/home/someone/other.md\n") == []


class TestOneLayout:
    def test_no_plugin_keeps_a_top_level_rules_directory(self) -> None:
        """Every plugin keeps its topics under `skills/<skill>/references/`.

        A topic file left in, or written to, a top-level rules directory
        (`plugins/<plugin>/rules`) is neither attached on touch nor checked by
        this module, and nothing else would notice: its router would simply read
        nothing.
        """
        assert sorted(REPO_ROOT.glob("plugins/*/rules")) == []
