"""Typed vocabulary of the checker: rule identities, signals, and the one
finding shape.

A finding is a ratchet key plus presentation. The key — the subject (a hook id,
a configuration key, or empty for a file-level rule) and the rule id — is what
a baseline stores and what "introduced since the baseline" is measured on.
`detail` and `topic` are outside it, so a hook that moves from one wrong
argument to another does not read as a new violation.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, NamedTuple

# The parsed YAML and TOML the checker reads structurally rather than modelling
# every key a tool may add.
JsonObject = dict[str, Any]

# A baseline key: the subject (empty for a file-level rule) and the rule id.
FindingKey = tuple[str, str]


class RuleId(StrEnum):
    """The mechanically checkable rules. What the standard leaves to judgment
    or to the project has no id here: it reaches the agent through the topics.
    """

    PARSE = "parse"
    NO_CONFIGURATION = "no-configuration"
    MISSING_HOOK = "missing-hook"
    STRAY_HOOK = "stray-hook"
    RETIRED_TOOL = "retired-tool"
    HOOK_ARGS = "hook-args"
    HOOK_FORM = "hook-form"
    HOOK_ORDER = "hook-order"
    REV_PIN = "rev-pin"
    MISSING_CONFIG = "missing-config"
    CONFIG_VALUE = "config-value"
    SHELLCHECK_DISABLE = "shellcheck-disable"


class Signal(StrEnum):
    """What a repository's tracked files say. A hook of the house set is carried
    exactly where its signal is present.
    """

    ALWAYS = "always"
    PYTHON = "python"
    PYTHON_LOCK = "python-lock"
    MARKUP = "markup"
    SHELL = "shell"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    DOCKERFILE = "dockerfile"
    SCANNED = "scanned"
    WEB = "web"
    DATA = "data"


@dataclass(frozen=True)
class Signals:
    """A repository's signals, and the executors its node lockfiles owe."""

    present: frozenset[Signal]
    executors: frozenset[str] = frozenset()
    tracks_lockfile: bool = False
    tracks_submodules: bool = False
    tracks_tests: bool = False


class Rule(NamedTuple):
    """How a rule id is reported: a one-line fix and the topic stating the rule.

    The fix says what to do and nothing else — the rationale belongs to the
    cited topic, which the checker points at rather than duplicates.
    """

    fix: str
    topic: str


class HouseHook(NamedTuple):
    """A hook of the standard: the id, the topic giving its entry, its signal."""

    id: str
    topic: str
    signal: Signal


class Replacement(NamedTuple):
    """What takes over from a retired tool, and the topic that says so."""

    house_tool: str
    topic: str


class HostedTool(NamedTuple):
    """A tool hosted where no lockfile is tracked: the upstream repository's
    path on its forge and the topic giving the hosted entry.
    """

    repository: str
    topic: str


class Canon(NamedTuple):
    """The canonical arguments, filters and stages of one house hook.

    A flag holding a space is a flag and its value: either spelling, separate
    or joined by `=`, satisfies it.
    """

    topic: str
    flags: tuple[str, ...] = ()
    whole_program: bool = False
    filtered: bool = False
    serial: bool = False
    manual: bool = False


class Finding(NamedTuple):
    """One violation, attributed to the file it is about.

    `topic` overrides the rule's own citation where the rule spans topics: a
    missing hook is cited to the topic of the set it belongs to.
    """

    source: Path
    subject: str
    rule: RuleId
    detail: str = ""
    topic: str = ""

    @property
    def key(self) -> FindingKey:
        return (self.subject, self.rule.value)
