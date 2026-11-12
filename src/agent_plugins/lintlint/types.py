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
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple

# The parsed YAML and TOML the checker reads structurally rather than modelling
# every key a tool may add.
JsonObject = dict[str, Any]


class FindingKey(NamedTuple):
    """A baseline key: the subject (empty for a file-level rule) and the rule id."""

    subject: str
    rule: str


class TrackedBaseline(NamedTuple):
    """A file this context has a baseline for, and that baseline."""

    path: Path
    keys: set[FindingKey]


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
    CLAUDE_MANIFEST = "claude-manifest"
    PORTABLE_MANIFEST = "portable-manifest"
    WORKFLOWS = "workflows"


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


class FormTool(NamedTuple):
    """A local hook the lockfile signal decides the form of: the tool it runs
    and the topic giving both forms.
    """

    tool: str
    topic: str


class Canon(NamedTuple):
    """The canonical arguments, filters and stages of one house hook.

    A flag holding a space is a flag and its value: either spelling, separate
    or joined by `=`, satisfies it. `manual` asks for the manual stage alone;
    `always_run` is the further shape of a check that is handed no files.
    """

    topic: str
    flags: tuple[str, ...] = ()
    whole_program: bool = False
    filtered: bool = False
    serial: bool = False
    manual: bool = False
    always_run: bool = False


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
        return FindingKey(self.subject, self.rule.value)


@dataclass(frozen=True)
class HookEntry:
    """One hook of the configuration, with the repository that holds it.

    `None` where the configuration says nothing: the hook then takes its
    manifest's default, which is not the same thing as a stated value.
    """

    id: str
    repo: str
    entry: str = ""
    args: tuple[str, ...] = ()
    types: tuple[str, ...] = ()
    types_or: tuple[str, ...] = ()
    files: str | None = None
    exclude: str | None = None
    stages: tuple[str, ...] = ()
    pass_filenames: bool | None = None
    require_serial: bool | None = None
    always_run: bool | None = None
    additional_dependencies: tuple[str, ...] = ()

    @property
    def command(self) -> str:
        """The entry and its arguments as one line of text."""
        return " ".join((self.entry, *self.args)).strip()


class RepoPin(NamedTuple):
    """A hook repository and its `rev:`."""

    repo: str
    rev: str


@dataclass(frozen=True)
class HookConfig:
    """The hook configuration: hooks in the order the runner runs them."""

    hooks: tuple[HookEntry, ...]
    pins: tuple[RepoPin, ...]
    exclude: str | None = None


class RuffSettings(NamedTuple):
    """The ruff lint table, the file holding it, and that file's key prefix."""

    source: Path
    lint: JsonObject
    prefix: str


class TrackedFile(NamedTuple):
    """One entry of the listing, as a path relative to the repository's root."""

    path: PurePosixPath
    executable: bool


class Repository(NamedTuple):
    """A repository's root and what it tracks there. Gitlinks are left out."""

    root: Path
    files: tuple[TrackedFile, ...]


class NodeLockfile(NamedTuple):
    """A package manifest with a lockfile beside it, and that lockfile's executor."""

    manifest: PurePosixPath
    executor: str
