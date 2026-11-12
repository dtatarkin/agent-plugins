"""One violating and one compliant justfile per rule id, checked through
`just`'s own parse — the checks of design Decision 5.

Each case is the smallest file that breaks exactly one rule, so a finding that
leaks into a neighbouring case fails here rather than in the audit.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from agent_plugins.justlint.checker import file_findings
from agent_plugins.justlint.types import RuleId

# Per rule: a file that breaks it and a file that does not. The compliant half
# must break nothing at all, not merely the rule under test.
CASES: dict[RuleId, tuple[str, str]] = {
    RuleId.DOC_ATTR: (
        "# help in a comment\nrun:\n    echo hi\n",
        '[doc("Run it")]\nrun:\n    echo hi\n',
    ),
    RuleId.PRIVATE_DOC: (
        '[private]\n[doc("Never listed")]\n_run:\n    echo hi\n',
        "[private]\n_run:\n    echo hi\n",
    ),
    RuleId.SHEBANG: (
        '[doc("Two commands")]\nrun:\n    echo one\n    echo two\n',
        '[doc("Two commands")]\nrun:\n'
        "    #!/usr/bin/env bash\n    set -euo pipefail\n    echo one\n    echo two\n",
    ),
    RuleId.STRICT: (
        '[doc("Loose")]\nrun:\n    #!/usr/bin/env bash\n    echo one\n    echo two\n',
        '[doc("Strict")]\nrun:\n'
        "    #!/usr/bin/env bash\n    set -euo pipefail\n    echo one\n    echo two\n",
    ),
    RuleId.SPLAT: (
        '[doc("Forward")]\nrun *args:\n    uv run app {{ args }}\n',
        '[doc("Forward")]\n[positional-arguments]\nrun *args:\n    uv run app "$@"\n',
    ),
}

# `private-prefix` has two directions, and the estate has only the first today.
PRIVATE_PREFIX_CASES = {
    "underscore without the attribute": "_run:\n    echo hi\n",
    "attribute without the underscore": "[private]\nrun:\n    echo hi\n",
}

MODULE_WITHOUT_PREAMBLE = '[doc("Build")]\nbuild:\n    echo build\n'
MODULE_WITH_PREAMBLE = (
    "source_file := source_file()\n\n"
    '[default]\n[doc("List all available recipes")]\n'
    "list justfile=source_file:\n    just --justfile {{ justfile }} --list\n\n"
    '[doc("Build")]\nbuild:\n    echo build\n'
)

# The sanctioned nested-shell form: `foreach` hands the quoted string to a
# fresh shell, which re-splits it. Everything else splats.
FOREACH_EXEMPT = (
    '[doc("Fetch")]\nfetch *args:\n'
    '    git submodule foreach --recursive "git fetch --all {{ args }}; echo"\n'
)
FOREACH_OUTSIDE_QUOTES = (
    '[doc("Status")]\nstatus *args="--recursive":\n    git submodule status {{ args }}\n'
)
# The same exemption through the other allowlisted family, written the way the
# estate writes it: single quotes, and a project recipe wrapping `sops exec-env`.
SOPS_EXEMPT = (
    '[doc("Load")]\nload *flags:\n'
    "    just sops-exec-env alpaca.sops.env.yaml 'uv run python -m pipelines.alpaca {{ flags }}'\n"
)
SOPS_OUTSIDE_QUOTES = (
    '[doc("Load")]\nload *flags:\n    sops exec-env alpaca.sops.env.yaml {{ flags }}\n'
)


def _rules(tree: Path, name: str = "justfile") -> list[str]:
    return [finding.rule.value for finding in file_findings(tree / name)]


class TestRuleChecks:
    @pytest.mark.parametrize("rule", list(CASES))
    def test_violation_is_reported(self, rule: RuleId, justfile_tree: Callable[..., Path]) -> None:
        tree = justfile_tree({"justfile": CASES[rule][0]})
        assert _rules(tree) == [rule.value]

    @pytest.mark.parametrize("rule", list(CASES))
    def test_compliant_file_is_silent(
        self, rule: RuleId, justfile_tree: Callable[..., Path]
    ) -> None:
        tree = justfile_tree({"justfile": CASES[rule][1]})
        assert _rules(tree) == []

    @pytest.mark.parametrize("direction", list(PRIVATE_PREFIX_CASES))
    def test_both_directions_of_private_prefix(
        self, direction: str, justfile_tree: Callable[..., Path]
    ) -> None:
        tree = justfile_tree({"justfile": PRIVATE_PREFIX_CASES[direction]})
        assert _rules(tree) == [RuleId.PRIVATE_PREFIX.value]

    def test_a_paired_private_recipe_is_silent(self, justfile_tree: Callable[..., Path]) -> None:
        tree = justfile_tree({"justfile": "[private]\n_run:\n    echo hi\n"})
        assert _rules(tree) == []

    def test_a_module_without_the_preamble_is_reported(
        self, justfile_tree: Callable[..., Path]
    ) -> None:
        tree = justfile_tree(
            {"justfile": "mod tools 'tools.just'\n", "tools.just": MODULE_WITHOUT_PREAMBLE}
        )
        findings = file_findings(tree / "tools.just")
        assert [(f.subject, f.rule.value) for f in findings] == [("", "module-preamble")]

    def test_a_module_with_the_preamble_is_silent(self, justfile_tree: Callable[..., Path]) -> None:
        tree = justfile_tree(
            {"justfile": "mod tools 'tools.just'\n", "tools.just": MODULE_WITH_PREAMBLE}
        )
        assert _rules(tree, "tools.just") == []


class TestNestedShellExemption:
    def test_a_splat_inside_a_foreach_string_is_exempt(
        self, justfile_tree: Callable[..., Path]
    ) -> None:
        tree = justfile_tree({"justfile": FOREACH_EXEMPT})
        assert _rules(tree) == []

    def test_a_splat_outside_the_quotes_is_reported(
        self, justfile_tree: Callable[..., Path]
    ) -> None:
        tree = justfile_tree({"justfile": FOREACH_OUTSIDE_QUOTES})
        assert _rules(tree) == [RuleId.SPLAT.value]

    def test_a_splat_inside_a_single_quoted_sops_string_is_exempt(
        self, justfile_tree: Callable[..., Path]
    ) -> None:
        tree = justfile_tree({"justfile": SOPS_EXEMPT})
        assert _rules(tree) == []

    def test_a_splat_outside_the_sops_quotes_is_reported(
        self, justfile_tree: Callable[..., Path]
    ) -> None:
        tree = justfile_tree({"justfile": SOPS_OUTSIDE_QUOTES})
        assert _rules(tree) == [RuleId.SPLAT.value]


class TestFindingShape:
    def test_a_finding_names_recipe_rule_fix_and_topic(
        self, justfile_tree: Callable[..., Path]
    ) -> None:
        from agent_plugins.justlint.report import render_audit

        tree = justfile_tree({"justfile": CASES[RuleId.SPLAT][0]})
        line = render_audit(file_findings(tree / "justfile"), tree).splitlines()[1]
        assert "run" in line
        assert "splat" in line
        assert "[positional-arguments]" in line
        assert "(skills/just/references/arguments.md)" in line

    def test_formatting_is_not_checked(self, justfile_tree: Callable[..., Path]) -> None:
        # Two spaces of indent and no blank line: `just --fmt` would rewrite
        # this, and the checker must still find nothing.
        tree = justfile_tree({"justfile": '[doc("Run it")]\nrun:\n  echo hi\n'})
        assert _rules(tree) == []
