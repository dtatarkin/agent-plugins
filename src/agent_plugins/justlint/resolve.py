"""Which files the checker acts on, which entrypoint parses them, and where a
repository ends.

A file's role comes from the nearest `justfile` at or above it — never from
trying a standalone dump. Some fragments dump on their own although they are
imported and others do not, so a trial would decide the role by accident and
shift the ratchet's keys between one run and the next.
"""

from collections.abc import Iterator
from pathlib import Path

from agent_plugins.justlint.consts import ENTRYPOINT_NAME, LOCAL_NAME, MODULE_SUFFIX, PRUNED_DIRS
from agent_plugins.justlint.types import JsonObject, Unit


def is_checked_file(path: Path) -> bool:
    """Whether the checker acts on this name at all: `justfile`, `.just` or
    `*.just`. The hook re-applies it to the path it is handed, so an
    over-firing `if` filter cannot make it dump anything else.
    """
    return path.name in (ENTRYPOINT_NAME, LOCAL_NAME) or path.suffix == MODULE_SUFFIX


def repository_root(path: Path) -> Path | None:
    """The nearest ancestor holding a `.git` entry, or `None` outside a
    repository. A submodule and a worktree carry `.git` as a file, so the
    entry's kind is not examined.
    """
    start = path if path.is_dir() else path.parent
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def entrypoint_for(path: Path) -> Path | None:
    """The `justfile` that parses `path`: itself when it is one, else the
    nearest one above it, never leaving `path`'s own repository.
    """
    if path.name == ENTRYPOINT_NAME:
        return path
    boundary = repository_root(path)
    for directory in (path.parent, *path.parent.parents):
        candidate = directory / ENTRYPOINT_NAME
        if candidate.is_file():
            return candidate
        if directory == boundary:
            break
    return None


def iter_units(root: JsonObject, boundary: Path | None) -> Iterator[Unit]:
    """The entrypoint and each module of it inside `boundary`'s repository,
    paired with whether it is the entrypoint.

    A `mod` into another repository is not followed: each repository is
    audited on its own, so an umbrella never reports a colleague's
    sub-repository. A file reached twice — the shared modules are — is yielded
    once.
    """
    seen: set[str] = set()

    def walk(unit: JsonObject, is_entrypoint: bool) -> Iterator[Unit]:
        source = unit["source"]
        if source in seen:
            return
        seen.add(source)
        yield Unit(unit, is_entrypoint)
        for module in unit["modules"].values():
            if repository_root(Path(module["source"])) == boundary:
                yield from walk(module, False)

    yield from walk(root, True)


def iter_checked_files(directory: Path) -> Iterator[Path]:
    """Every file the checker acts on under `directory`, skipping build and
    tooling directories and anything belonging to a nested repository.

    The nested-repository skip applies only when the walk itself starts inside
    a repository — that is the umbrella case the boundary exists for. A
    directory that is no repository at all, a scratch parent of several
    clones, still reaches each of them.
    """
    boundary = repository_root(directory)
    for entry in sorted(directory.iterdir()):
        if entry.is_dir():
            # A symlinked directory is not descended into: it can close a loop,
            # and whatever it points at is audited where it really lives.
            if entry.is_symlink() or entry.name in PRUNED_DIRS or entry.name.startswith("."):
                continue
            if boundary is not None and (entry / ".git").exists():
                continue
            yield from iter_checked_files(entry)
        elif entry.is_file() and is_checked_file(entry):
            yield entry
