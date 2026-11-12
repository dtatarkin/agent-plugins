"""The two questions the rest of the tool asks: what does this repository's
files break, and what does this one file break.

Both go through `just`'s parse of an entrypoint. The audit reports every unit
of every entrypoint it reaches; the hook asks about a single file and gets the
findings of the unit that file belongs to — its own, when `mod` loads it, and
the importing unit's otherwise, since `just` merges an import into its
importer and the dump keeps no trace of where a merged recipe came from.
"""

from collections.abc import Iterable, Sequence
from pathlib import Path

from agent_plugins.justlint.dump import dump_entrypoint
from agent_plugins.justlint.errors import JustLintError, JustParseFailed
from agent_plugins.justlint.resolve import (
    entrypoint_for,
    is_checked_file,
    iter_checked_files,
    iter_units,
    repository_root,
)
from agent_plugins.justlint.rules import check_unit
from agent_plugins.justlint.types import Finding, RuleId


def audit(paths: Sequence[Path]) -> list[Finding]:
    """Every finding of the named files and directories.

    Raises `JustMissing` when `just` cannot be run and `JustLintError` when a
    named path does not exist.
    """
    findings: list[Finding] = []
    for entrypoint in _entrypoints(paths):
        findings.extend(_audit_entrypoint(entrypoint))
    return sorted(set(findings))


def file_findings(path: Path) -> list[Finding]:
    """The findings of the unit `path` belongs to, keyed by recipe and rule.

    Returns nothing for a name the checker does not act on, for a file that
    does not exist — a file being created has no findings yet — and for a
    fragment no `justfile` at or above it can parse.

    Raises `JustMissing` when `just` cannot be run.
    """
    if not is_checked_file(path) or not path.is_file():
        return []
    # `just` reports absolute sources; the harness may hand over any spelling.
    path = path.resolve()
    entrypoint = entrypoint_for(path)
    if entrypoint is None:
        return []
    try:
        root = dump_entrypoint(entrypoint)
    except JustParseFailed as failure:
        return [Finding(path, "", RuleId.PARSE, failure.message)]
    units = list(iter_units(root, repository_root(entrypoint)))
    for unit, is_entrypoint in units:
        if Path(unit["source"]) == path:
            return check_unit(unit, is_entrypoint=is_entrypoint)
    # Not a unit of its own: an imported fragment, merged into the entrypoint
    # that pulls it in. Its recipes are checked there.
    return check_unit(root, is_entrypoint=True)


def keys_of(findings: Iterable[Finding]) -> set[tuple[str, str]]:
    """The ratchet keys of `findings` — what a baseline stores."""
    return {finding.key for finding in findings}


def _audit_entrypoint(entrypoint: Path) -> list[Finding]:
    try:
        root = dump_entrypoint(entrypoint)
    except JustParseFailed as failure:
        return [Finding(entrypoint, "", RuleId.PARSE, failure.message)]
    boundary = repository_root(entrypoint)
    findings: list[Finding] = []
    for unit, is_entrypoint in iter_units(root, boundary):
        findings.extend(check_unit(unit, is_entrypoint=is_entrypoint))
    return findings


def _entrypoints(paths: Sequence[Path]) -> list[Path]:
    """The entrypoints that parse the named paths, in a stable order."""
    found: dict[Path, None] = {}
    for path in paths:
        if path.is_dir():
            files: Iterable[Path] = iter_checked_files(path)
        elif path.is_file():
            files = [path]
        else:
            raise JustLintError(f"no such file or directory: {path}")
        for file in files:
            entrypoint = entrypoint_for(file.resolve())
            if entrypoint is not None:
                found[entrypoint] = None
    return list(found)
