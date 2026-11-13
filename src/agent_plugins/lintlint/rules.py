"""The mechanically checkable rules, and the two questions the rest of the
tool asks: what does this repository break, and what does this one file break.

Local entries are compared on their leading tokens and required flags, never as
whole strings: a `bash -c '…' -- <dir> <dir>` loop is read by the command its
body runs, and directory arguments, `files:`, `exclude:` and comments are the
project's. So is a hook the standard names no tool for, which no rule here
reaches, and the age of a pin, which needs the network and is the procedure's.
"""

import re
from collections.abc import Iterable, Iterator, Mapping
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

from agent_plugins.lintlint.config import (
    first_existing,
    load_hook_config,
    load_project,
    load_ruff,
    lookup,
    read_toml,
    read_yaml,
)
from agent_plugins.lintlint.consts import (
    AGENT_PLUGINS_SCHEMA,
    ANSIBLE_COLLECTIONS_DEPENDENCY,
    ANSIBLE_LINT_ID,
    COMMIT_HASH,
    DBT_CHECKPOINT_REPO,
    DBT_PARSE_ID,
    DEV_DEPENDENCIES,
    DISTRIBUTION_NAME,
    FORM_TOOLS,
    GOVERNED_GLOBS,
    HOOK_CANON,
    HOOK_CONFIG_NAME,
    HOSTED_FORM_TOOLS,
    HOSTED_URL_TEMPLATE,
    HOUSE_HOOKS,
    LYCHEE_ID,
    LYCHEE_REPO,
    LYCHEE_TAG_PREFIX,
    LYCHEE_VERSION_ARG,
    MARKUP_TYPES,
    PINLESS_REPOS,
    PROJECT_FILE,
    RETIRED_ENTRY_PIN,
    RETIRED_ENTRY_PIN_REPLACEMENT,
    RETIRED_IDS,
    RETIRED_REPOS,
    RETIRED_TOOLS,
    RUFF_ALL_RULES,
    RUFF_FILES,
    RUFF_FORMAT_TYPES,
    RUFF_IGNORE_SECTIONS,
    RUFF_IGNORES,
    RUFF_PER_FILE_SECTIONS,
    RUFF_SECTIONS,
    RUFF_SECURITY_RULES,
    RUFF_TEST_GLOB,
    RUFF_TEST_GLOBS,
    RUFF_TEST_IGNORES,
    RUMDL_FILE,
    RUMDL_VALUES,
    SCHEMA_CHECK_ID,
    SCHEMA_FILE_FLAG,
    SHELLCHECK_DISABLE,
    SHELLCHECK_FILE,
    TOPIC_TEMPLATE,
    TYPOS_DEFAULT_FLAGS,
    TYPOS_FILES,
    TYPOS_MOVING_TAG,
    TYPOS_REPO,
    UV_COOLDOWN,
    UV_COOLDOWN_KEY,
    WEB_EXECUTORS,
    WEB_HOOKS,
    WORD_END,
    WORD_START,
    YAMLLINT_ANSIBLE_VALUES,
    YAMLLINT_DISABLED,
    YAMLLINT_FILES,
    YAMLLINT_VALUES,
)
from agent_plugins.lintlint.errors import ConfigParseFailed, NotARepository
from agent_plugins.lintlint.signals import derive, find_repository
from agent_plugins.lintlint.types import (
    Finding,
    FindingKey,
    HookConfig,
    HookEntry,
    JsonObject,
    Replacement,
    Repository,
    RuffSettings,
    RuleId,
    Signal,
    Signals,
)


def audit(directory: Path) -> list[Finding]:
    """Every finding of the repository holding `directory`.

    Raises `GitMissing` when `git` cannot be run and `NotARepository` when the
    directory is in no repository.
    """
    return _check(find_repository(directory))


def file_findings(path: Path) -> list[Finding]:
    """The findings about `path`, and no other file.

    Returns nothing for a name the checker does not act on, for a file that
    does not exist — a file being created has no findings yet — and for a file
    in no repository, which has no tracked files to derive from.

    Raises `GitMissing` when `git` cannot be run.
    """
    if not is_governed(path) or not path.is_file():
        return []
    path = path.resolve()
    try:
        repository = find_repository(path.parent)
    except NotARepository:
        return []
    return [finding for finding in _check(repository) if finding.source == path]


def is_governed(path: Path) -> bool:
    """Whether the lint topics attach on this name."""
    return any(fnmatchcase(path.name, glob) for glob in GOVERNED_GLOBS)


def keys_of(findings: Iterable[Finding]) -> set[FindingKey]:
    """The ratchet keys of `findings` — what a baseline stores."""
    return {finding.key for finding in findings}


def _check(repository: Repository) -> list[Finding]:
    root = repository.root
    path = root / HOOK_CONFIG_NAME
    try:
        config = load_hook_config(path)
    except ConfigParseFailed as failure:
        parse = Finding(path, "", RuleId.PARSE, failure.message)
        return sorted({parse, *_check_linter_files(root, derive(repository))})
    if config is None:
        absent = Finding(path, "", RuleId.NO_CONFIGURATION)
        return sorted({absent, *_check_linter_files(root, derive(repository))})
    signals = derive(repository, config.exclude)
    return sorted({*_check_hook_config(path, config, signals), *_check_linter_files(root, signals)})


def _check_hook_config(path: Path, config: HookConfig, signals: Signals) -> Iterator[Finding]:
    yield from _check_hook_set(path, config, signals)
    yield from _check_pins(path, config)
    yield from _check_order(path, config)
    revs = dict(config.pins)
    for hook in config.hooks:
        yield from _check_retired(path, hook)
        if _is_house_entry(hook):
            yield from _check_args(path, hook)
        yield from _check_version_override(path, hook, revs.get(hook.repo))
        yield from _check_form(path, hook, signals)


def _is_house_entry(hook: HookEntry) -> bool:
    """Whether an entry is the house hook its id names. The generic schema
    checker is that only when pointed at the Agent Plugins schema; any other
    such entry is the project's, neither satisfying the set nor straying from it.
    """
    if hook.id != SCHEMA_CHECK_ID:
        return True
    return any(AGENT_PLUGINS_SCHEMA.fullmatch(schema) for schema in _schema_files(hook.args))


def _schema_files(args: Iterable[str]) -> Iterator[str]:
    """Each value of the schema flag, separate or joined by `=`."""
    tokens = [token for arg in args for token in arg.split()]
    for index, token in enumerate(tokens):
        if token == SCHEMA_FILE_FLAG and index + 1 < len(tokens):
            yield tokens[index + 1]
        elif token.startswith(f"{SCHEMA_FILE_FLAG}="):
            yield token.removeprefix(f"{SCHEMA_FILE_FLAG}=")


def _check_hook_set(path: Path, config: HookConfig, signals: Signals) -> Iterator[Finding]:
    """The set in both directions: a hook its signal derives and the file lacks,
    and a house hook the file carries whose signal is gone.
    """
    carried = {hook.id for hook in config.hooks if _is_house_entry(hook)}
    for house in HOUSE_HOOKS:
        derived = house.signal in signals.present
        if derived and house.id not in carried:
            yield Finding(path, house.id, RuleId.MISSING_HOOK, topic=house.topic)
        elif house.id in carried and not derived:
            detail = f"no {house.signal.value} signal in the tracked files"
            yield Finding(path, house.id, RuleId.STRAY_HOOK, detail)


def _check_pins(path: Path, config: HookConfig) -> Iterator[Finding]:
    for repo, rev in config.pins:
        if repo in PINLESS_REPOS:
            continue
        subject = f"repos[{repo}].rev"
        if COMMIT_HASH.fullmatch(rev):
            yield Finding(path, subject, RuleId.REV_PIN, f"`{rev}` is a commit hash")
        elif TYPOS_REPO in repo and rev == TYPOS_MOVING_TAG:
            yield Finding(path, subject, RuleId.REV_PIN, f"`{rev}` is the moving major tag")


def _check_order(path: Path, config: HookConfig) -> Iterator[Finding]:
    """A dbt-checkpoint hook listed before the parse writing its manifest."""
    ids = [hook.id for hook in config.hooks]
    if DBT_PARSE_ID not in ids:
        return
    parse = ids.index(DBT_PARSE_ID)
    for hook in config.hooks[:parse]:
        if DBT_CHECKPOINT_REPO in hook.repo:
            yield Finding(path, hook.id, RuleId.HOOK_ORDER)


def _check_retired(path: Path, hook: HookEntry) -> Iterator[Finding]:
    def retired(tool: str, replacement: Replacement) -> Finding:
        detail = f"{tool} leaves for {replacement.house_tool}"
        return Finding(path, hook.id, RuleId.RETIRED_TOOL, detail, replacement.topic)

    if hook.id in RETIRED_IDS:
        yield retired(f"`{hook.id}`", RETIRED_IDS[hook.id])
    for repo, replacement in RETIRED_REPOS.items():
        if repo in hook.repo:
            yield retired(repo, replacement)
    for tool, replacement in RETIRED_TOOLS.items():
        if hook.id == tool or _names(hook.command, tool) or f"/{tool}" in hook.repo:
            yield retired(tool, replacement)
    if RETIRED_ENTRY_PIN in hook.command:
        yield retired("a formatter pin in the entry", RETIRED_ENTRY_PIN_REPLACEMENT)
    pointed_at = MARKUP_TYPES.intersection((*hook.types, *hook.types_or))
    if pointed_at and ("prettier" in hook.id or _names(hook.command, "prettier")):
        types = ", ".join(sorted(pointed_at))
        yield retired(f"a code formatter over {types}", Replacement("the markup tools", "web"))


def _check_args(path: Path, hook: HookEntry) -> Iterator[Finding]:
    """The canonical arguments, filters and stages of one house hook."""

    def wrong(detail: str, topic: str) -> Finding:
        return Finding(path, hook.id, RuleId.HOOK_ARGS, detail, topic)

    if hook.id == "ruff-format" and set(hook.types_or) != RUFF_FORMAT_TYPES:
        yield wrong(f"`types_or` is not {sorted(RUFF_FORMAT_TYPES)}", "python")
    if hook.id == "typos" and hook.args and not all(f in hook.args for f in TYPOS_DEFAULT_FLAGS):
        yield wrong(f"`args:` drops {' and '.join(TYPOS_DEFAULT_FLAGS)}", "baseline")
    if hook.id == "validate-pyproject" and hook.additional_dependencies:
        yield wrong("`additional_dependencies` replaces the manifest's list", "python")
    if hook.id == "gitleaks" and (hook.files is not None or hook.exclude is not None):
        yield wrong("`files:` and `exclude:` do nothing here", "baseline")
    if hook.id == "prettier" and not hook.types and not hook.types_or:
        yield wrong("no type list scoping it to code", "web")
    if (
        hook.id == ANSIBLE_LINT_ID
        and hook.repo not in PINLESS_REPOS
        and ANSIBLE_COLLECTIONS_DEPENDENCY not in _distributions(hook.additional_dependencies)
    ):
        detail = f"`additional_dependencies` lacks `{ANSIBLE_COLLECTIONS_DEPENDENCY}`"
        yield wrong(detail, HOSTED_FORM_TOOLS[ANSIBLE_LINT_ID].topic)

    canon = HOOK_CANON.get(hook.id)
    if canon is None:
        return
    for flag in canon.flags:
        if not _has_flag(hook.command, flag):
            yield wrong(f"`{flag}` is missing", canon.topic)
    if canon.whole_program and hook.pass_filenames is not False:
        yield wrong("`pass_filenames: false` is missing", canon.topic)
    if canon.filtered and not (hook.types or hook.types_or or hook.files):
        yield wrong("no type or path filter", canon.topic)
    if canon.serial and hook.require_serial is not True:
        yield wrong("`require_serial: true` is missing", canon.topic)
    if canon.manual and set(hook.stages) != {"manual"}:
        yield wrong("`stages: [manual]` is missing", canon.topic)
    if canon.always_run and hook.always_run is not True:
        yield wrong("`always_run: true` is missing", canon.topic)


def _check_version_override(path: Path, hook: HookEntry, rev: str | None) -> Iterator[Finding]:
    """The hosted link checker's first argument, naming the version its pin
    tags. A pin that is not a `lychee-v` tag yields no version to compare, so
    only the override's presence is asked of it.
    """
    if hook.id != LYCHEE_ID or LYCHEE_REPO not in hook.repo:
        return
    first = hook.args[0] if hook.args else ""
    expected = (
        rev.removeprefix(LYCHEE_TAG_PREFIX)
        if rev is not None and rev.startswith(LYCHEE_TAG_PREFIX)
        else None
    )
    owed = f"`{LYCHEE_VERSION_ARG}{expected or '<version>'}`"
    if not first.startswith(LYCHEE_VERSION_ARG):
        detail = f"{owed} is not the first argument"
    elif expected is not None and first != f"{LYCHEE_VERSION_ARG}{expected}":
        detail = f"`{first}` does not match the pin `{rev}`: write {owed}"
    else:
        return
    yield Finding(path, hook.id, RuleId.HOOK_ARGS, detail, "markup")


def _check_form(path: Path, hook: HookEntry, signals: Signals) -> Iterator[Finding]:
    """A local hook's form against the lockfile signal, and a hosted-form tool's
    whatever its repository. An entry that does not visibly run its tool is a
    project's wrapper, and no verdict is reached on it.
    """
    locked = Signal.PYTHON_LOCK in signals.present
    if hook.id in HOSTED_FORM_TOOLS:
        yield from _check_hosted_form(path, hook, locked)
        if not locked:
            return
    if hook.repo != "local":
        return
    if hook.id in WEB_HOOKS and Signal.WEB in signals.present:
        executor = next(
            (name for name in WEB_EXECUTORS if _names(hook.entry, name)),
            None,
        )
        if executor is not None and executor not in signals.executors:
            owed = " or ".join(sorted(signals.executors))
            detail = (
                f"runs through {executor}; the tracked lockfile owes {owed} (see {_topic('web')})"
            )
            yield Finding(path, hook.id, RuleId.HOOK_FORM, detail)
        return
    if hook.id not in FORM_TOOLS:
        return
    tool, topic = FORM_TOOLS[hook.id]
    if _runs_through_uv(hook.entry, tool):
        if not locked:
            detail = (
                f"`uv run` with no tracked `uv.lock`: call {tool} by name (see {_topic(topic)})"
            )
            yield Finding(path, hook.id, RuleId.HOOK_FORM, detail)
    elif locked and _names(hook.entry, tool):
        detail = (
            f"by name where `uv.lock` is tracked: run {tool} through `uv run` (see {_topic(topic)})"
        )
        yield Finding(path, hook.id, RuleId.HOOK_FORM, detail)


def _check_hosted_form(path: Path, hook: HookEntry, locked: bool) -> Iterator[Finding]:
    """A hosted-form tool local where no lockfile is tracked, or hosted from its
    upstream where one is. A tracked lockfile's local hook is left to the
    runner/by-name verdict.
    """
    repository, topic = HOSTED_FORM_TOOLS[hook.id]
    tool = FORM_TOOLS[hook.id].tool
    if hook.repo == "local":
        visible = _runs_through_uv(hook.entry, tool) or _names(hook.entry, tool)
        if not locked and visible:
            url = HOSTED_URL_TEMPLATE.format(repository=repository)
            detail = (
                f"a local hook with no tracked `uv.lock`: host it from {url}, "
                f"pinned by `rev:` (see {_topic(topic)})"
            )
            yield Finding(path, hook.id, RuleId.HOOK_FORM, detail)
    elif locked and _hosted_from(hook.repo, repository):
        detail = (
            f"hosted where `uv.lock` is tracked: run {tool} as a local hook "
            f"through `uv run` (see {_topic(topic)})"
        )
        yield Finding(path, hook.id, RuleId.HOOK_FORM, detail)


def _hosted_from(url: str, repository: str) -> bool:
    """Whether the hook repository `url` is `repository` on its forge."""
    return url.rstrip("/").removesuffix(".git").endswith(f"/{repository}")


def _distributions(requirements: Iterable[str]) -> set[str]:
    """The lowercased distribution names of `requirements`."""
    names: set[str] = set()
    for requirement in requirements:
        match = DISTRIBUTION_NAME.match(requirement)
        if match:
            names.add(match.group().lower())
    return names


def _check_linter_files(root: Path, signals: Signals) -> Iterator[Finding]:
    if Signal.MARKUP in signals.present:
        yield from _check_yamllint(root, signals)
        yield from _check_rumdl(root)
    if (signals.tracks_lockfile or signals.tracks_submodules) and not first_existing(
        root, TYPOS_FILES
    ):
        detail = "a lockfile or a submodule owes the spelling checker an exclusion"
        yield Finding(root / TYPOS_FILES[0], "", RuleId.MISSING_CONFIG, detail, "baseline")
    yield from _check_shellcheck(root)
    if Signal.PYTHON in signals.present:
        yield from _check_project_files(root, signals)


def _check_yamllint(root: Path, signals: Signals) -> Iterator[Finding]:
    path = first_existing(root, YAMLLINT_FILES)
    if path is None:
        yield Finding(root / YAMLLINT_FILES[0], "", RuleId.MISSING_CONFIG)
        return
    try:
        document = read_yaml(path)
    except ConfigParseFailed as failure:
        yield Finding(path, "", RuleId.PARSE, failure.message)
        return
    expected = dict(YAMLLINT_VALUES)
    if Signal.ANSIBLE in signals.present:
        expected |= YAMLLINT_ANSIBLE_VALUES
    for key, want in expected.items():
        got = lookup(document, key)
        if got != want and not (want in YAMLLINT_DISABLED and got in YAMLLINT_DISABLED):
            yield _wrong_value(path, key, got, want)


def _check_rumdl(root: Path) -> Iterator[Finding]:
    path = root / RUMDL_FILE
    if not path.is_file():
        yield Finding(path, "", RuleId.MISSING_CONFIG)
        return
    try:
        document = read_toml(path)
    except ConfigParseFailed as failure:
        yield Finding(path, "", RuleId.PARSE, failure.message)
        return
    for key, want in RUMDL_VALUES.items():
        got = lookup(document, key)
        if got != want:
            yield _wrong_value(path, key, got, want)


def _check_shellcheck(root: Path) -> Iterator[Finding]:
    path = root / SHELLCHECK_FILE
    if path.is_file() and SHELLCHECK_DISABLE.search(path.read_text()):
        yield Finding(path, "disable", RuleId.SHELLCHECK_DISABLE)


def _check_project_files(root: Path, signals: Signals) -> Iterator[Finding]:
    """The Python linter's values and the lockfile's cooldown. Read although no
    topic attaches on the project file; the ratchet never gets here for it,
    because a finding's source is the file it is about.
    """
    project_path = root / PROJECT_FILE
    try:
        project = load_project(root)
    except ConfigParseFailed as failure:
        yield Finding(project_path, "", RuleId.PARSE, failure.message)
        return
    try:
        ruff = load_ruff(root, project)
    except ConfigParseFailed as failure:
        yield Finding(root / RUFF_FILES[0], "", RuleId.PARSE, failure.message)
        return
    if ruff is None:
        ruff = RuffSettings(project_path, {}, "tool.ruff.lint")
    yield from _check_ruff(ruff, signals)
    if project is not None and Signal.PYTHON_LOCK in signals.present:
        yield from _check_runner_project(project_path, project)


def _check_ruff(ruff: RuffSettings, signals: Signals) -> Iterator[Finding]:
    source, lint, prefix = ruff
    selected = {code for name in RUFF_SECTIONS for code in lint.get(name) or ()}
    if not selected & {RUFF_SECURITY_RULES, RUFF_ALL_RULES}:
        detail = f"the security rules are in neither {' nor '.join(RUFF_SECTIONS)}"
        yield Finding(source, f"{prefix}.select", RuleId.CONFIG_VALUE, detail, "python")
    ignored = {code for name in RUFF_IGNORE_SECTIONS for code in lint.get(name) or ()}
    if missing := RUFF_IGNORES - ignored:
        detail = f"lacks {', '.join(sorted(missing))}"
        yield Finding(source, f"{prefix}.ignore", RuleId.CONFIG_VALUE, detail, "python")
    if signals.tracks_tests and (missing := RUFF_TEST_IGNORES - set(_test_ignores(lint))):
        subject = f'{prefix}.per-file-ignores."{RUFF_TEST_GLOB}"'
        detail = f"lacks {', '.join(sorted(missing))}"
        yield Finding(source, subject, RuleId.CONFIG_VALUE, detail, "python")


def _test_ignores(lint: JsonObject) -> Iterator[str]:
    for section in RUFF_PER_FILE_SECTIONS:
        for glob, codes in (lint.get(section) or {}).items():
            if RUFF_TEST_GLOBS.match(glob):
                yield from codes


def _check_runner_project(path: Path, project: JsonObject) -> Iterator[Finding]:
    """What a tracked lockfile owes the project file."""
    cooldown = lookup(project, UV_COOLDOWN_KEY)
    if cooldown != UV_COOLDOWN:
        yield _wrong_value(path, UV_COOLDOWN_KEY, cooldown, UV_COOLDOWN, "python")
    carried = set(_group_dependencies(project))
    for dependency in DEV_DEPENDENCIES:
        if dependency not in carried:
            subject = f"dependency-groups.dev.{dependency}"
            yield Finding(path, subject, RuleId.CONFIG_VALUE, "not in the dev group", "python")


def _group_dependencies(project: JsonObject) -> Iterator[str]:
    """The distribution names of every dependency group. All of them: `dev`
    includes others by reference, and which it is matters less than the lockfile
    carrying the tool.
    """
    groups: Mapping[str, Any] = project.get("dependency-groups") or {}
    for requirements in groups.values():
        for requirement in requirements:
            match = DISTRIBUTION_NAME.match(str(requirement))
            if match:
                yield match.group()


def _wrong_value(path: Path, key: str, got: object, want: object, topic: str = "") -> Finding:
    said = "absent" if got is None else f"{got!r}"
    return Finding(path, key, RuleId.CONFIG_VALUE, f"is {said}, the house value is {want!r}", topic)


def _names(command: str, tool: str) -> bool:
    """Whether `tool` appears in `command` as a word of its own."""
    return re.search(WORD_START + re.escape(tool) + WORD_END, command) is not None


def _runs_through_uv(command: str, tool: str) -> bool:
    """Whether `tool` runs under `uv run` in `command`, whatever flags sit
    between the two, in the same pipeline stage.
    """
    pattern = rf"{WORD_START}uv run\b[^;|&]*?{WORD_START}{re.escape(tool)}{WORD_END}"
    return re.search(pattern, command) is not None


def _has_flag(command: str, flag: str) -> bool:
    """Whether a flag, or a flag and its value in either spelling, is present."""
    name, _, value = flag.partition(" ")
    written = re.escape(name) + (rf"[ =]{re.escape(value)}" if value else "")
    return re.search(rf"(?<![\w-]){written}(?![\w,=-])", command) is not None


def _topic(topic: str) -> str:
    return TOPIC_TEMPLATE.format(topic=topic)
