"""The ratchet's per-context state.

A *context* is one session plus, inside a subagent, its agent: `session_id`
survives compaction, and a subagent carries `agent_id`, so the pair is what
"this context" means for both the baselines and the Stop gate's guard.

Each baseline is one file, written once — before the context's first edit of
that file — and read after every later edit of it. Markers are created
with `O_EXCL`, so "once per context" holds even when two hooks of the same
event run in parallel.
"""

import hashlib
import json
import os
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Self

from agent_plugins.lintlint.consts import (
    DIGEST_LENGTH,
    MARKER_PREFIX,
    PRUNE_AFTER,
    STATE_DIR_NAME,
    STATE_ENV,
    STATE_FALLBACK,
)
from agent_plugins.lintlint.types import FindingKey, TrackedBaseline


def state_root() -> Path:
    """Where every context's state lives. `CLAUDE_PLUGIN_DATA` is set for a
    plugin's hooks; the fallback keeps the tool usable outside one.
    """
    configured = os.environ.get(STATE_ENV)
    base = Path(configured) if configured else Path.home() / STATE_FALLBACK
    return base / STATE_DIR_NAME


class LintState:
    """The baselines and markers of one context."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    @classmethod
    def for_context(cls, session_id: str, agent_id: str | None) -> Self:
        name = _sanitize(session_id)
        if agent_id:
            name = f"{name}--{_sanitize(agent_id)}"
        return cls(state_root() / name)

    @property
    def exists(self) -> bool:
        """Whether this context has any lint state at all.

        A context that edited no governed file has none, which is how the Stop gate
        leaves read-only contexts — and the harness's own compaction subagent —
        alone.
        """
        return any(self._baselines())

    def baseline(self, path: Path) -> set[FindingKey] | None:
        """The findings recorded before this context first edited `path`, or
        `None` when it never did.
        """
        file = self._baseline_file(path)
        if not file.is_file():
            return None
        record = json.loads(file.read_text())
        return {FindingKey(subject, rule) for subject, rule in record["baseline"]}

    def record_baseline(self, path: Path, keys: set[FindingKey]) -> None:
        """Record `keys` as the baseline of `path`, replacing any earlier one."""
        self.directory.mkdir(parents=True, exist_ok=True)
        record = {"path": str(path), "baseline": sorted(keys)}
        self._baseline_file(path).write_text(json.dumps(record))

    def tracked(self) -> Iterator[TrackedBaseline]:
        """Every file this context has a baseline for, with that baseline."""
        for file in sorted(self._baselines()):
            record = json.loads(file.read_text())
            keys = {FindingKey(subject, rule) for subject, rule in record["baseline"]}
            yield TrackedBaseline(Path(record["path"]), keys)

    def claim(self, marker: str) -> bool:
        """Claim a once-per-context marker, `True` the first time only."""
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{MARKER_PREFIX}{_sanitize(marker)}"
        try:
            handle = os.open(path, os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            return False
        os.close(handle)
        return True

    def _baselines(self) -> Iterator[Path]:
        if not self.directory.is_dir():
            return
        for file in self.directory.iterdir():
            if file.is_file() and not file.name.startswith(MARKER_PREFIX):
                yield file

    def _baseline_file(self, path: Path) -> Path:
        digest = _digest(str(path.resolve() if path.is_absolute() else path.absolute()))
        return self.directory / f"{path.name}-{digest}.json"


def prune(root: Path, now: float | None = None) -> None:
    """Drop state untouched for longer than `PRUNE_AFTER`, and the context
    directories it empties.

    Called at the end of a turn rather than on every edit: it is a directory
    scan, and a turn always ends.
    """
    if not root.is_dir():
        return
    deadline = (time.time() if now is None else now) - PRUNE_AFTER.total_seconds()
    for context in root.iterdir():
        if not context.is_dir():
            continue
        for file in context.iterdir():
            if file.is_file() and file.stat().st_mtime < deadline:
                file.unlink()
        if not any(context.iterdir()):
            context.rmdir()


def _digest(text: str) -> str:
    # A path is not a filename: it is too long and full of separators. The
    # digest only has to separate one context's files from each other.
    return hashlib.sha256(text.encode()).hexdigest()[:DIGEST_LENGTH]


def _sanitize(name: str) -> str:
    """A path component that cannot escape the state directory."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
