"""The parsed files: the hook configuration as the hook runner reads it, and
the linter files as their tools do.

The comparison is never made with the file's text. A YAML anchor resolves
here, so what the rules compare is what the runner would run.
"""

import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from agent_plugins.lintlint.consts import PROJECT_FILE, RUFF_FILES
from agent_plugins.lintlint.errors import ConfigParseFailed
from agent_plugins.lintlint.types import JsonObject


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

    def hook_ids(self) -> set[str]:
        return {hook.id for hook in self.hooks}


class RuffSettings(NamedTuple):
    """The ruff lint table, the file holding it, and that file's key prefix."""

    source: Path
    lint: JsonObject
    prefix: str


def load_hook_config(path: Path) -> HookConfig | None:
    """The configuration at `path`, or `None` when no such file exists.

    Raises `ConfigParseFailed` when it is not YAML or holds no list of
    repositories.
    """
    if not path.is_file():
        return None
    document = read_yaml(path)
    repos = document.get("repos")
    if not isinstance(repos, list):
        raise ConfigParseFailed("no list of `repos:`")
    hooks: list[HookEntry] = []
    pins: list[RepoPin] = []
    for repository in repos:
        if not isinstance(repository, dict):
            raise ConfigParseFailed("an entry of `repos:` is not a mapping")
        url = str(repository.get("repo", ""))
        if "rev" in repository:
            pins.append(RepoPin(url, str(repository["rev"])))
        entries = repository.get("hooks") or []
        if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
            raise ConfigParseFailed(f"the hooks of {url} are not a list of mappings")
        hooks.extend(_hook_entry(url, entry) for entry in entries)
    return HookConfig(tuple(hooks), tuple(pins), _optional_string(document.get("exclude")))


def read_yaml(path: Path) -> JsonObject:
    """A YAML file holding a mapping, anchors resolved.

    Raises `ConfigParseFailed` otherwise.
    """
    try:
        document = YAML(typ="safe").load(path.read_text())
    except (YAMLError, OSError, UnicodeDecodeError) as failure:
        raise ConfigParseFailed(_first_line(failure)) from failure
    if not isinstance(document, dict):
        raise ConfigParseFailed("not a mapping")
    return document


def read_toml(path: Path) -> JsonObject:
    """A TOML file. Raises `ConfigParseFailed` when it does not parse."""
    try:
        return tomllib.loads(path.read_text())
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError) as failure:
        raise ConfigParseFailed(_first_line(failure)) from failure


def first_existing(root: Path, names: Sequence[str]) -> Path | None:
    """The first of `names` present at the root."""
    return next((root / name for name in names if (root / name).is_file()), None)


def load_project(root: Path) -> JsonObject | None:
    """The Python project file, or `None` when the repository has none.

    Raises `ConfigParseFailed` when it does not parse.
    """
    path = root / PROJECT_FILE
    return read_toml(path) if path.is_file() else None


def load_ruff(root: Path, project: JsonObject | None) -> RuffSettings | None:
    """The ruff table the tool reads, in its own order of precedence: its own
    file, then the project file. `None` when neither carries one.

    Raises `ConfigParseFailed` when ruff's own file does not parse.
    """
    own = first_existing(root, RUFF_FILES)
    if own is not None:
        return RuffSettings(own, _table(read_toml(own), "lint"), "lint")
    tool = _table(project or {}, "tool")
    if "ruff" not in tool:
        return None
    return RuffSettings(root / PROJECT_FILE, _table(tool["ruff"], "lint"), "tool.ruff.lint")


def lookup(document: JsonObject, key: str) -> Any:
    """The value at a dotted key, or `None` when any step of it is absent."""
    value: Any = document
    for step in key.split("."):
        if not isinstance(value, dict) or step not in value:
            return None
        value = value[step]
    return value


def _hook_entry(repo: str, raw: JsonObject) -> HookEntry:
    return HookEntry(
        id=str(raw.get("id", "")),
        repo=repo,
        entry=str(raw.get("entry", "")),
        args=_strings(raw.get("args")),
        types=_strings(raw.get("types")),
        types_or=_strings(raw.get("types_or")),
        files=_optional_string(raw.get("files")),
        exclude=_optional_string(raw.get("exclude")),
        stages=_strings(raw.get("stages")),
        pass_filenames=raw.get("pass_filenames"),
        require_serial=raw.get("require_serial"),
        always_run=raw.get("always_run"),
        additional_dependencies=_strings(raw.get("additional_dependencies")),
    )


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in value) if isinstance(value, list) else ()


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)


def _table(document: JsonObject, key: str) -> JsonObject:
    value = document.get(key)
    return value if isinstance(value, dict) else {}


def _first_line(failure: Exception) -> str:
    lines = str(failure).strip().splitlines()
    return lines[0] if lines else type(failure).__name__
