"""Files and roles: which entrypoint parses a file, and what that makes it.

A role comes from the nearest `justfile` at or above the file, never from
trying a standalone dump — some imported fragments parse alone and others do
not, so a trial would decide the role by accident and move the ratchet's keys
between runs.
"""

from collections.abc import Callable
from pathlib import Path

from agent_plugins.justlint.checker import audit, file_findings
from agent_plugins.justlint.resolve import entrypoint_for, is_checked_file
from agent_plugins.justlint.types import RuleId

# An importer with a violation of its own, and a fragment that parses alone.
IMPORTER = "import 'fragment.just'\n\n# help in a comment\nown:\n    echo hi\n"
FRAGMENT = '[doc("Merged in")]\nmerged *args:\n    uv run app {{ args }}\n'

# A sub-repository an umbrella loads with `mod`: its own entrypoint, and none
# of the umbrella's business.
UMBRELLA = "mod sub 'sub/justfile'\n"
SUB_ENTRYPOINT = '[doc("Run it")]\nrun *args:\n    uv run app {{ args }}\n'

UNPARSABLE = "# help in a comment\nrun\n    echo hi\n"


def _keys(findings: list) -> set[tuple[str, str]]:
    return {(finding.subject, finding.rule.value) for finding in findings}


class TestImportedFragments:
    def test_a_fragment_is_keyed_under_its_importer(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": IMPORTER, "fragment.just": FRAGMENT})
        # A standalone dump of the fragment would see `merged` alone. The
        # importer's own violation proves the entrypoint decided the role.
        assert _keys(file_findings(tree / "fragment.just")) == {
            ("own", "doc-attr"),
            ("merged", "splat"),
        }

    def test_an_imported_fragment_needs_no_module_preamble(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": IMPORTER, "fragment.just": FRAGMENT})
        rules = {rule for _, rule in _keys(file_findings(tree / "fragment.just"))}
        assert RuleId.MODULE_PREAMBLE.value not in rules

    def test_a_module_of_the_same_repository_is_keyed_under_itself(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder(
            {"justfile": "mod tools 'tools.just'\n", "tools.just": FRAGMENT}
        )
        assert _keys(file_findings(tree / "tools.just")) == {
            ("", "module-preamble"),
            ("merged", "splat"),
        }


class TestSubRepository:
    def test_a_sub_repository_entrypoint_needs_no_module_preamble(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder(
            {"justfile": UMBRELLA, "sub/.git": "", "sub/justfile": SUB_ENTRYPOINT}
        )
        assert _keys(file_findings(tree / "sub" / "justfile")) == {("run", "splat")}

    def test_the_umbrella_reports_nothing_from_it(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder(
            {"justfile": UMBRELLA, "sub/.git": "", "sub/justfile": SUB_ENTRYPOINT}
        )
        assert audit([tree / "justfile"]) == []


class TestUnparsableFiles:
    def test_one_parse_finding_and_no_rule_findings(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": UNPARSABLE})
        findings = file_findings(tree / "justfile")
        assert [finding.rule for finding in findings] == [RuleId.PARSE]
        assert findings[0].detail

    def test_a_fragment_of_an_unparsable_entrypoint_reports_the_parse(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": UNPARSABLE, "fragment.just": FRAGMENT})
        findings = file_findings(tree / "fragment.just")
        assert [(f.source, f.rule) for f in findings] == [(tree / "fragment.just", RuleId.PARSE)]


class TestNameFilter:
    def test_the_three_checked_names(self) -> None:
        assert is_checked_file(Path("justfile"))
        assert is_checked_file(Path(".just"))
        assert is_checked_file(Path("tools.just"))

    def test_other_names_are_not_checked(self) -> None:
        assert not is_checked_file(Path("notes.txt"))
        assert not is_checked_file(Path("Justfile"))
        assert not is_checked_file(Path(".just.example"))

    def test_another_kind_of_file_has_no_findings(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": IMPORTER, "notes.txt": "not a justfile\n"})
        assert file_findings(tree / "notes.txt") == []


class TestEntrypointResolution:
    def test_a_justfile_is_its_own_entrypoint(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": IMPORTER, "sub/justfile": SUB_ENTRYPOINT})
        assert entrypoint_for(tree / "sub" / "justfile") == tree / "sub" / "justfile"

    def test_a_fragment_takes_the_nearest_justfile_above_it(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder({"justfile": IMPORTER, "sub/fragment.just": FRAGMENT})
        assert entrypoint_for(tree / "sub" / "fragment.just") == tree / "justfile"

    def test_the_search_stops_at_the_repository_boundary(
        self, justfile_tree_builder: Callable[..., Path]
    ) -> None:
        tree = justfile_tree_builder(
            {"justfile": IMPORTER, "sub/.git": "", "sub/fragment.just": FRAGMENT}
        )
        assert entrypoint_for(tree / "sub" / "fragment.just") is None
