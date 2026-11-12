"""What a repository's tracked files say.

The listing is `git ls-files`, never a directory walk: "tracks a lockfile" is
literally a tracked-file question, ignored trees hold shell scripts and
Terraform by the thousand, and a nested repository appears as one gitlink
entry, so its files contribute no signal without a rule saying so.
"""

import json
import re
import subprocess
from collections.abc import Iterable, Iterator
from pathlib import Path, PurePosixPath

from agent_plugins.lintlint.consts import (
    AGENT_PLUGINS_SCHEMA,
    ANSIBLE_DIR,
    ANSIBLE_MANIFEST,
    CLAUDE_MANIFESTS,
    CLAUDE_PLUGIN_DIR,
    DBT_PROJECT,
    DOCKERFILE_NAME,
    DOCKERFILE_SUFFIX,
    EXECUTABLE_MODE,
    GITLINK_MODE,
    HELM_MANIFEST,
    LOCKFILE_NAME,
    MANIFEST_KEYS,
    MANIFEST_READ_LIMIT,
    MARKUP_SUFFIXES,
    NODE_LOCKFILES,
    PORTABLE_MANIFEST,
    PYTHON_PROJECT,
    PYTHON_SUFFIX,
    ROLE_TASKS_DIR,
    ROLES_DIR,
    SCHEMA_KEY,
    SHEBANG,
    SHELL_SUFFIX,
    SUBMODULES_FILE,
    TERRAFORM_SUFFIX,
    TESTS_DIR,
    WEB_MANIFEST,
    WEB_SOURCE_SUFFIXES,
    WORKFLOWS_DIR,
    YAML_SUFFIXES,
)
from agent_plugins.lintlint.errors import GitMissing, NotARepository
from agent_plugins.lintlint.types import NodeLockfile, Repository, Signal, Signals, TrackedFile


def find_repository(directory: Path) -> Repository:
    """The repository holding `directory`.

    Raises `GitMissing` when `git` cannot be run and `NotARepository` when the
    directory is in no repository.
    """
    root = Path(_git(directory, "rev-parse", "--show-toplevel").rstrip("\n"))
    return Repository(root, tuple(_parse_listing(_git(root, "ls-files", "--stage", "-z"))))


def derive(repository: Repository, exclude: str | None = None) -> Signals:
    """The signals of the repository's tracked files, in the one derivation the
    audit and the ratchet share.

    `exclude` is the hook configuration's top-level pattern. A file it matches
    is one no hook could ever run on, so it carries no content signal. The
    lockfile signals stand regardless: what a repository tracks is a fact about
    it, not about the hooks.
    """
    top_level = {file.path.name for file in repository.files if len(file.path.parts) == 1}
    repository = _without_excluded(repository, exclude)
    paths = [file.path for file in repository.files]
    names = {path.name for path in paths}
    suffixes = {path.suffix for path in paths}

    present = {Signal.ALWAYS}
    if PYTHON_PROJECT in names or PYTHON_SUFFIX in suffixes:
        present.add(Signal.PYTHON)
    if LOCKFILE_NAME in top_level:
        present.add(Signal.PYTHON_LOCK)
    if suffixes & MARKUP_SUFFIXES:
        present.add(Signal.MARKUP)
    if SHELL_SUFFIX in suffixes or _has_shell_shebang(repository):
        present.add(Signal.SHELL)
    if TERRAFORM_SUFFIX in suffixes:
        present.update({Signal.TERRAFORM, Signal.SCANNED})
    if any(_is_ansible(path) for path in paths):
        present.update({Signal.ANSIBLE, Signal.SCANNED})
    if any(_is_dockerfile(path) for path in paths):
        present.add(Signal.DOCKERFILE)
    if Signal.SCANNED not in present and _has_cluster_content(repository):
        present.add(Signal.SCANNED)
    if DBT_PROJECT in names:
        present.add(Signal.DATA)
    if any(_is_claude_manifest(path) for path in paths):
        present.add(Signal.CLAUDE_MANIFEST)
    if any(_is_portable_manifest(repository.root, path) for path in paths):
        present.add(Signal.PORTABLE_MANIFEST)
    if any(path.parent == WORKFLOWS_DIR and path.suffix in YAML_SUFFIXES for path in paths):
        present.add(Signal.WORKFLOWS)

    pairs = list(_node_lockfile_pairs(paths))
    executors = frozenset(
        executor for manifest, executor in pairs if _has_web_source(manifest, paths)
    )
    if executors:
        present.add(Signal.WEB)
    return Signals(
        frozenset(present),
        executors=executors,
        tracks_lockfile=LOCKFILE_NAME in top_level or bool(pairs),
        tracks_submodules=SUBMODULES_FILE in top_level,
        tracks_tests=any(path.parts[0] == TESTS_DIR for path in paths),
    )


def _without_excluded(repository: Repository, exclude: str | None) -> Repository:
    if exclude is None:
        return repository
    try:
        pattern = re.compile(exclude)
    except re.error:
        return repository  # the hook runner's to refuse, not a signal's
    return repository._replace(
        files=tuple(file for file in repository.files if not pattern.search(str(file.path)))
    )


def _git(directory: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), *args],
            capture_output=True,
            encoding="utf-8",
            errors="surrogateescape",
            check=False,
        )
    except FileNotFoundError:
        raise GitMissing("`git` is not on PATH") from None
    if result.returncode != 0:
        raise NotARepository(f"not in a git repository: {directory}")
    return result.stdout


def _parse_listing(listing: str) -> Iterator[TrackedFile]:
    """The `--stage` listing, one `<mode> <object> <stage>\\t<path>` per entry."""
    for record in listing.split("\0"):
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        mode = metadata.split(" ", 1)[0]
        if mode != GITLINK_MODE:
            yield TrackedFile(PurePosixPath(path), mode == EXECUTABLE_MODE)


def _has_shell_shebang(repository: Repository) -> bool:
    """Whether an executable tracked file opens with a shell shebang.

    Executable files only: the baseline's two shebang hooks make the two sets
    equal in a converged repository, and the scan has to fit the hook's budget.
    """
    return any(
        file.executable and SHEBANG.match(_first_line(repository.root / file.path))
        for file in repository.files
    )


def _first_line(path: Path) -> bytes:
    try:
        with path.open("rb") as stream:
            return stream.readline(256)
    except OSError:
        return b""  # tracked but deleted from the tree


def _is_ansible(path: PurePosixPath) -> bool:
    if path.name == ANSIBLE_MANIFEST:
        return True
    directories = path.parts[:-1]
    if ANSIBLE_DIR in directories and path.suffix in YAML_SUFFIXES:
        return True
    return any(
        directories[index] == ROLES_DIR and directories[index + 2] == ROLE_TASKS_DIR
        for index in range(len(directories) - 2)
    )


def _is_dockerfile(path: PurePosixPath) -> bool:
    return (
        path.name == DOCKERFILE_NAME
        or path.name.startswith(f"{DOCKERFILE_NAME}.")
        or path.name.endswith(DOCKERFILE_SUFFIX)
    )


def _is_claude_manifest(path: PurePosixPath) -> bool:
    return path.parent.name == CLAUDE_PLUGIN_DIR and path.name in CLAUDE_MANIFESTS


def _is_portable_manifest(root: Path, path: PurePosixPath) -> bool:
    """A `plugin.json` outside the Claude directory whose `$schema` is an
    Agent Plugins schema. One that cannot be read or parsed carries no signal:
    parsing is the hygiene set's JSON check.
    """
    if path.name != PORTABLE_MANIFEST or CLAUDE_PLUGIN_DIR in path.parts[:-1]:
        return False
    try:
        document = json.loads((root / path).read_bytes())
    except (OSError, ValueError):
        return False
    schema = document.get(SCHEMA_KEY) if isinstance(document, dict) else None
    return isinstance(schema, str) and AGENT_PLUGINS_SCHEMA.fullmatch(schema) is not None


def _has_cluster_content(repository: Repository) -> bool:
    """A helm chart or a Kubernetes manifest. A compose file is neither: no
    scanner of the pair reads one, so it would derive a gate over nothing.
    Terraform and Ansible content derive the same pair, so the caller skips the
    one read this costs when either is there.
    """
    paths = [file.path for file in repository.files]
    if any(path.name == HELM_MANIFEST for path in paths):
        return True
    return any(
        _is_kubernetes_manifest(repository.root / path)
        for path in paths
        if path.suffix in YAML_SUFFIXES
    )


def _is_kubernetes_manifest(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            head = stream.read(MANIFEST_READ_LIMIT)
    except OSError:
        return False
    return all(key.search(head) for key in MANIFEST_KEYS)


def _node_lockfile_pairs(paths: Iterable[PurePosixPath]) -> Iterator[NodeLockfile]:
    """Each package manifest with a lockfile beside it, and that lockfile's
    executor. Every pair is a tracked lockfile; only one with web source under
    it owes the web set.
    """
    listed = set(paths)
    for path in listed:
        executor = NODE_LOCKFILES.get(path.name)
        manifest = path.with_name(WEB_MANIFEST)
        if executor is not None and manifest in listed:
            yield NodeLockfile(manifest, executor)


def _has_web_source(manifest: PurePosixPath, paths: Iterable[PurePosixPath]) -> bool:
    """Whether a TypeScript or JavaScript file sits anywhere under the
    manifest's directory. A manifest pinning only a command-line tool has none,
    and the web hooks would read nothing there.
    """
    directory = manifest.parent
    return any(path.suffix in WEB_SOURCE_SUFFIXES and directory in path.parents for path in paths)
