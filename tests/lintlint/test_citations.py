"""Guards the citation every finding carries — the topic that states the rule.

A finding names a rule id, a one-line fix, and the `lint-rules` topic holding
the rationale, which is the only copy of it. Nothing resolves that citation at
runtime: the checker formats a path and the agent goes looking, so a renamed
topic, or a rule quietly dropped from a file it still cites, leaves findings
pointing at text that no longer says what they claim.

Existence is the cheap half. The substantive half is that the file still
*states* the rule, so the evidence below is scoped: the tokens of one rule must
meet inside one block, because a token found anywhere in a 50 KB standard proves
nothing. The house tables are held to the topics the same way: every id of the
set stands in its topic as `id: <hook>`, and every canonical flag and house
value is still written there.
"""

from pathlib import Path

import pytest

from agent_plugins.lintlint.consts import (
    FORM_TOOLS,
    GOVERNED_GLOBS,
    HOOK_CANON,
    HOSTED_FORM_TOOLS,
    HOSTED_URL_TEMPLATE,
    HOUSE_HOOKS,
    RETIRED_ENTRY_PIN_REPLACEMENT,
    RETIRED_IDS,
    RETIRED_REPOS,
    RETIRED_TOOLS,
    RULES,
    RUMDL_VALUES,
    TOPIC_TEMPLATE,
    TYPOS_DEFAULT_FLAGS,
    YAMLLINT_ANSIBLE_VALUES,
    YAMLLINT_VALUES,
)
from agent_plugins.lintlint.types import Replacement, RuleId

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "lint-rules"

# One marker is a set of tokens that must co-occur in a single block; a rule is
# stated only when every one of its markers is met. Tokens are the standard's
# own phrases, lowercased: its topics are prose, so a marker is the sentence's
# load-bearing words and a reflow cannot move them out of reach.
Marker = tuple[str, ...]
EVIDENCE: dict[RuleId, tuple[Marker, ...]] = {
    # Both failures are one step of the procedure: there is nothing to diff.
    RuleId.PARSE: (("derive the set", "diff it against the configuration"),),
    RuleId.NO_CONFIGURATION: (("derive the set", "write the house entries"),),
    RuleId.MISSING_HOOK: (("derived set", "hook for hook"),),
    RuleId.STRAY_HOOK: (("derivation runs in both directions", "leaves the configuration"),),
    RuleId.RETIRED_TOOL: (("retire the tools the standard retires",),),
    # The topic the generic statement sits in; each hook's own arguments are
    # held to the hook's topic by the canonical table below.
    RuleId.HOOK_ARGS: (("pass_filenames: false", "a type filter anyway"),),
    RuleId.HOOK_FORM: (("runner form", "by-name form"), ("hosted hook", "pinned by rev:")),
    RuleId.HOOK_ORDER: (("parse hook comes first", "writes the manifest"),),
    RuleId.REV_PIN: (("pinned by tag", "not by commit hash"), ("moving major tag",)),
    RuleId.MISSING_CONFIG: (("house configuration", "line_length = 120"),),
    RuleId.CONFIG_VALUE: (("document-start: disable",), ("line_length = 120",)),
    RuleId.SHELLCHECK_DISABLE: (("never disable a code repository-wide",),),
}

# What each retired tool's topic says about it, by the name the table keys it
# under. The topics state the retirement in prose and name few of the tools,
# which is why the spec's list, not a topic, carries `pyright`.
RETIRED_EVIDENCE: dict[str, Marker] = {
    "codespell": ("a second spell checker",),
    "pyright": ("a deliberate pair",),
    "bandit": ("replaces a separate security linter",),
    "dprint": ("general-purpose formatter driven through a package runner",),
    "ruff": ("never the legacy alias",),
    "hadolint-docker": ("not the container-image variant",),
    "instrumentl/pre-commit-just": ("do not use a third-party justfile hook repository",),
    "pre-commit/mirrors-mypy": ("local, not a mirror repository",),
    "pypa/pip-audit": ("the export pipe is the point of the entry",),
    "a formatter pin": ("never pin the formatter inside the hook entry",),
}

RETIRED: dict[str, Replacement] = {
    **RETIRED_TOOLS,
    **RETIRED_IDS,
    **RETIRED_REPOS,
    "a formatter pin": RETIRED_ENTRY_PIN_REPLACEMENT,
}

# The python topic's values, which live in TOML snippets rather than a table.
PYTHON_VALUES: tuple[Marker, ...] = (
    ('extend-select = ["s"]', 'ignore = ["s603", "s607"]'),
    ('"tests/" = ["s101", "s105", "s106", "s107"]',),
    ('exclude-newer = "7 days"',),
)


def _normalize(text: str) -> str:
    """Lowercased, backticks and emphasis dropped, whitespace collapsed.

    Rewrapping a paragraph, bolding a lead-in or fencing an example must not
    move a token out of reach — only the token itself is evidence.
    """
    return " ".join(text.replace("`", "").replace("*", "").lower().split())


def _blocks(text: str) -> list[str]:
    """The file split into rule statements: every paragraph, with the list or
    example it runs into, so a marker is met inside one statement.
    """
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith(("#", "- ")):
            blocks.append("\n".join(current))
            current = []
        current.append(line)
    blocks.append("\n".join(current))
    return [_normalize(block) for block in blocks]


def _states(blocks: list[str], marker: Marker) -> bool:
    return any(all(token in block for token in marker) for block in blocks)


def citation_violations(rule: RuleId, topic: str, plugin_dir: Path) -> list[str]:
    """Violations of one rule id's citation; empty when the file states the rule."""
    citation = TOPIC_TEMPLATE.format(topic=topic)
    path = plugin_dir / citation
    if not path.is_file():
        return [f"{rule.value} cites {citation}, which the plugin does not ship"]
    blocks = _blocks(path.read_text())
    return [
        f"{rule.value}: {citation} states no rule holding {' + '.join(marker)}"
        for marker in EVIDENCE[rule]
        if not _states(blocks, marker)
    ]


def _topic_text(topic: str, plugin_dir: Path = PLUGIN_DIR) -> str:
    return _normalize((plugin_dir / TOPIC_TEMPLATE.format(topic=topic)).read_text())


class TestEveryCitation:
    def test_the_evidence_covers_the_checker_table(self) -> None:
        """Keeps the parametrized test below from passing vacuously."""
        assert set(RULES) == set(RuleId), "the checker's table has lost a rule id"
        assert set(EVIDENCE) == set(RULES), "a rule id in the checker's table has no evidence here"

    @pytest.mark.parametrize("rule", RULES, ids=lambda rule: rule.value)
    def test_cites_a_file_that_states_the_rule(self, rule: RuleId) -> None:
        assert citation_violations(rule, RULES[rule].topic, PLUGIN_DIR) == []


class TestTheHouseTables:
    @pytest.mark.parametrize("house", HOUSE_HOOKS, ids=lambda house: house.id)
    def test_every_hook_stands_in_its_topic(self, house) -> None:
        assert f"id: {house.id}" in _topic_text(house.topic)

    @pytest.mark.parametrize("hook", HOOK_CANON)
    def test_every_canonical_flag_is_written_in_the_hook_s_topic(self, hook: str) -> None:
        canon = HOOK_CANON[hook]
        assert f"id: {hook}" in _topic_text(canon.topic)
        for flag in canon.flags:
            assert flag.lower() in _topic_text(canon.topic), flag

    def test_the_spelling_checker_s_default_flags(self) -> None:
        text = _topic_text("baseline")
        assert all(flag.removeprefix("--") in text for flag in TYPOS_DEFAULT_FLAGS)

    @pytest.mark.parametrize("hook", FORM_TOOLS)
    def test_every_form_tool_has_both_forms_in_its_topic(self, hook: str) -> None:
        """The runner form, and beside it the by-name form — or, for a tool a
        repository that pins nothing hosts, the hosted repository's URL.
        """
        tool, topic = FORM_TOOLS[hook]
        text = _topic_text(topic)
        assert f"uv run {tool}" in text
        hosted = HOSTED_FORM_TOOLS.get(hook)
        if hosted is None:
            assert f"entry: {tool}" in text or f"do {tool}" in text
        else:
            assert hosted.topic == topic
            url = HOSTED_URL_TEMPLATE.format(repository=hosted.repository)
            assert f"repo: {url.lower()}" in text

    @pytest.mark.parametrize("tool", RETIRED, ids=str)
    def test_every_retirement_is_stated(self, tool: str) -> None:
        blocks = _blocks(
            (PLUGIN_DIR / TOPIC_TEMPLATE.format(topic=RETIRED[tool].topic)).read_text()
        )
        assert _states(blocks, RETIRED_EVIDENCE[tool])

    def test_the_retired_evidence_covers_the_table(self) -> None:
        assert set(RETIRED_EVIDENCE) == set(RETIRED)

    def test_the_yaml_values_are_the_markup_topic_s(self) -> None:
        text = _topic_text("markup")
        for key in (*YAMLLINT_VALUES, *YAMLLINT_ANSIBLE_VALUES):
            assert key.rsplit(".", 1)[-1] in text, key

    def test_the_markdown_values_are_the_markup_topic_s(self) -> None:
        text = _topic_text("markup")
        for key, value in RUMDL_VALUES.items():
            assert f"{key.rsplit('.', 1)[-1].lower()} = {str(value).lower()}" in text, key

    def test_the_python_values_are_the_python_topic_s(self) -> None:
        blocks = _blocks((PLUGIN_DIR / "skills" / "lint" / "references" / "python.md").read_text())
        assert all(_states(blocks, marker) for marker in PYTHON_VALUES)


class TestGovernedGlobs:
    def test_the_filter_equals_the_topics_paths(self) -> None:
        globs: set[str] = set()
        for topic in (PLUGIN_DIR / "skills" / "lint" / "references").glob("*.md"):
            for line in topic.read_text().split("---")[1].splitlines():
                if line.startswith("  - "):
                    globs.add(line.strip(' -"').removeprefix("**/"))
        assert globs == set(GOVERNED_GLOBS)


# `shell.md` as it might read after the disable rule was dropped: the word stays
# in a neighbouring sentence, so only the phrase catches the loss.
DROPPED_DISABLE = """\
# Shell

Take its defaults. Disable nothing it already filters.
"""

KEPT_DISABLE = """\
# Shell

Suppress at the line. Never disable a code repository-wide in a configuration file.
"""


def _plugin(tmp_path: Path, topic: str, text: str) -> Path:
    """A stand-in plugin directory shipping one topic file."""
    path = tmp_path / TOPIC_TEMPLATE.format(topic=topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return tmp_path


class TestRejections:
    def test_a_citation_to_a_file_that_is_not_there(self, tmp_path: Path) -> None:
        assert citation_violations(RuleId.SHELLCHECK_DISABLE, "shell", tmp_path) == [
            "shellcheck-disable cites skills/lint/references/shell.md, "
            "which the plugin does not ship"
        ]

    def test_a_renamed_topic(self, tmp_path: Path) -> None:
        plugin = _plugin(tmp_path, "scripts", KEPT_DISABLE)
        assert citation_violations(RuleId.SHELLCHECK_DISABLE, "shell", plugin) == [
            "shellcheck-disable cites skills/lint/references/shell.md, "
            "which the plugin does not ship"
        ]

    def test_a_file_that_no_longer_states_the_rule(self, tmp_path: Path) -> None:
        plugin = _plugin(tmp_path, "shell", DROPPED_DISABLE)
        assert citation_violations(RuleId.SHELLCHECK_DISABLE, "shell", plugin) == [
            "shellcheck-disable: skills/lint/references/shell.md states no rule holding "
            "never disable a code repository-wide"
        ]

    def test_a_file_that_states_it(self, tmp_path: Path) -> None:
        plugin = _plugin(tmp_path, "shell", KEPT_DISABLE)
        assert citation_violations(RuleId.SHELLCHECK_DISABLE, "shell", plugin) == []
