"""Justfile trees to check, and the hook state the ratchet keeps beside them.

Two builders: `justfile_tree` writes a tree from a mapping, and `data_tree`
copies one of the committed trees under `tests/justlint/data/`.

A committed tree is written in disguise and restored on copy, for two reasons.
Git will not track a path named `.git`, so a nested repository is marked with
a `NESTED_REPO` file; and a justfile that breaks rules on purpose must not be
found by an audit of this repository — the checker has no ignore list, by
design — so every such file carries a `.fixture` suffix and the `.just`
dotfile is spelled `dot.just`.
"""

import io
import json
import shutil
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from agent_plugins.justlint.hook import run_hook
from agent_plugins.justlint.types import JsonObject

DATA = Path(__file__).resolve().parents[2] / "justlint" / "data"

# How a committed tree spells the names it cannot carry in the open.
NESTED_REPO_MARKER = "NESTED_REPO"
DOTFILE_PREFIX = "dot"
FIXTURE_SUFFIX = ".fixture"

# The key that asks `justfile_tree` for a repository boundary in a directory.
REPO_KEY = ".git"


@pytest.fixture
def justfile_tree(tmp_path: Path) -> Callable[..., Path]:
    """Write a tree of files under a fresh directory and return its root.

    A key ending in `.git` becomes a repository boundary rather than a file,
    which is how a nested repository is staged.
    """

    def build(files: Mapping[str, str], name: str = "repo", *, repo: bool = True) -> Path:
        root = tmp_path / name
        root.mkdir(parents=True, exist_ok=True)
        if repo:
            (root / REPO_KEY).mkdir(exist_ok=True)
        for relative, text in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.name == REPO_KEY:
                target.mkdir(exist_ok=True)
            else:
                target.write_text(text)
        return root

    return build


@pytest.fixture
def data_tree(tmp_path: Path) -> Callable[[str], Path]:
    """Copy a committed tree from `tests/justlint/data/` and undo its disguise:
    a `NESTED_REPO` marker becomes a repository of its own, a `.fixture` suffix
    comes off, and `dot.just` becomes the `.just` dotfile.
    """

    def build(name: str) -> Path:
        root = tmp_path / name
        shutil.copytree(DATA / name, root)
        (root / REPO_KEY).mkdir(exist_ok=True)
        for marker in sorted(root.rglob(NESTED_REPO_MARKER)):
            (marker.parent / REPO_KEY).mkdir(exist_ok=True)
            marker.unlink()
        for disguised in sorted(root.rglob(f"*{FIXTURE_SUFFIX}")):
            plain = disguised.name.removesuffix(FIXTURE_SUFFIX)
            if plain.startswith(f"{DOTFILE_PREFIX}."):
                plain = plain[len(DOTFILE_PREFIX) :]
            disguised.rename(disguised.with_name(plain))
        return root

    return build


@pytest.fixture
def plugin_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the ratchet's state at a directory of this test's own."""
    root = tmp_path / "plugin-data"
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(root))
    return root


@pytest.fixture
def hook(
    plugin_data: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> Callable[..., JsonObject | None]:
    """Feed one hook event through stdin and hand back what reached stdout.

    The payload is shaped as the harness sends it, so the tests exercise the
    same path a session does: JSON in, JSON or silence out.
    """

    def call(
        event: str,
        *,
        path: Path | None = None,
        tool: str = "Edit",
        session: str = "session-1",
        agent: str | None = None,
        prompt: str = "prompt-1",
        cwd: Path | None = None,
        stop_hook_active: bool = False,
    ) -> JsonObject | None:
        # A session's cwd is its project directory; with no tree named, the
        # one the edited file sits in stands in for it.
        working = cwd or (path.parent if path else Path.cwd())
        payload: JsonObject = {
            "session_id": session,
            "prompt_id": prompt,
            "hook_event_name": event,
            "cwd": str(working),
        }
        if agent is not None:
            payload["agent_id"] = agent
        if path is not None:
            payload["tool_name"] = tool
            payload["tool_input"] = {"file_path": str(path)}
        if event in ("Stop", "SubagentStop"):
            payload["stop_hook_active"] = stop_hook_active
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        assert run_hook() == 0
        written = capsys.readouterr().out
        return json.loads(written) if written else None

    return call
