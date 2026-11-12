"""Typed vocabulary of the checker: rule identities and the one finding shape.

A finding is a ratchet key plus presentation. The key — the recipe (or the
empty subject, for a file-level rule) and the rule id — is what a baseline
stores and what "introduced since the baseline" is measured on; `detail`
qualifies the same key in prose and is deliberately outside it, so a recipe
that moves from "no help at all" to "bare-comment help" does not read as a new
violation.
"""

from enum import StrEnum
from pathlib import Path
from typing import Any, NamedTuple

# `just --dump --dump-format json` hands back plain JSON; the checker reads it
# structurally rather than modelling every key `just` may add.
JsonObject = dict[str, Any]


class RuleId(StrEnum):
    """The mechanically checkable rules. Judgment rules have no id here: they
    reach the agent through the rule files' own attachment, never the checker.
    """

    DOC_ATTR = "doc-attr"
    PRIVATE_DOC = "private-doc"
    PRIVATE_PREFIX = "private-prefix"
    SHEBANG = "shebang"
    STRICT = "strict"
    SPLAT = "splat"
    MODULE_PREAMBLE = "module-preamble"
    PARSE = "parse"


class FindingKey(NamedTuple):
    """A baseline key: the recipe name (empty for a file-level rule) and the rule id."""

    subject: str
    rule: str


class Unit(NamedTuple):
    """One parsed unit of an entrypoint's dump, and whether it is the entrypoint."""

    node: JsonObject
    is_entrypoint: bool


class TrackedBaseline(NamedTuple):
    """A file this context has a baseline for, and that baseline."""

    path: Path
    keys: set[FindingKey]


class Rule(NamedTuple):
    """How a rule id is reported: a one-line fix and the file stating the rule.

    The fix says what to do and nothing else — the rationale belongs to the
    cited rule file, which the checker points at rather than duplicates.
    """

    fix: str
    topic: str


class Finding(NamedTuple):
    """One violation, attributed to the file whose unit `just` parsed it from."""

    source: Path
    subject: str
    rule: RuleId
    detail: str = ""

    @property
    def key(self) -> FindingKey:
        return FindingKey(self.subject, self.rule.value)
