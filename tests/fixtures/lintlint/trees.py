"""Repositories to audit, and the hook state the ratchet keeps beside them.

Two builders: `lint_tree_builder` writes a tree from a mapping, and
`lint_data_tree_builder` copies one of the committed trees under
`tests/lintlint/data/`. Both end in a real `git add`, because the checker
derives from the tracked files and nothing else. Their concrete forms are an
empty repository (`lint_tree`) and the `compliant` tree (`lint_data_tree`).
`lint_hook_builder` has no concrete form: every call names the event it feeds,
so there is no default answer to hand a test.

A committed tree is written in disguise and restored on copy, as `justlint`'s
are. Git will not track a path named `.git`, so a nested repository is marked
with a `NESTED_REPO` file. And a hook configuration kept in the open would
attach the lint topics to any session that reads it and be linted by this
repository's own hooks, so every file carries a `.fixture` suffix and a dotfile
is spelled `dot.<name>`. The fixtures are named apart from `justlint`'s, which
this suite's root registers beside them.
"""

import io
import json
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path

import pytest

from agent_plugins.lintlint.hook import run_hook
from agent_plugins.lintlint.types import JsonObject

DATA = Path(__file__).resolve().parents[2] / "lintlint" / "data"

# How a committed tree spells the names it cannot carry in the open.
NESTED_REPO_MARKER = "NESTED_REPO"
DOTFILE_PREFIX = "dot"
FIXTURE_SUFFIX = ".fixture"

GIT_IDENTITY = ("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *GIT_IDENTITY, *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def track(root: Path, files: Mapping[str, str]) -> None:
    """Write `files` into a repository and add them to its index."""
    _write(root, files)
    git(root, "add", "--all")


def _write(root: Path, files: Mapping[str, str]) -> None:
    for relative, text in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)


def _index(root: Path) -> None:
    """Make `root` a repository tracking what it holds. A nested repository
    needs a commit of its own, or the outer `git add` cannot record its gitlink.
    """
    for marker in sorted(root.rglob(NESTED_REPO_MARKER), key=lambda p: -len(p.parts)):
        marker.unlink()
        git(marker.parent.parent, "init", "--quiet", marker.parent.name)
        git(marker.parent, "add", "--all")
        git(marker.parent, "commit", "--quiet", "--allow-empty", "--message", "nested")
    git(root, "init", "--quiet")
    git(root, "add", "--all")


@pytest.fixture
def lint_tree_builder(tmp_path: Path) -> Callable[..., Path]:
    """Write a tree of files under a fresh directory and return its root.

    A `NESTED_REPO` file makes its directory a repository of its own, `repo=False`
    leaves the root outside any repository, and `executable` names the files to
    track with the executable bit.
    """

    def build(
        files: Mapping[str, str],
        name: str = "repo",
        *,
        repo: bool = True,
        executable: Iterable[str] = (),
    ) -> Path:
        root = tmp_path / name
        root.mkdir(parents=True, exist_ok=True)
        _write(root, files)
        for relative in executable:
            (root / relative).chmod(0o755)
        if repo:
            _index(root)
        return root

    return build


@pytest.fixture
def lint_tree(lint_tree_builder: Callable[..., Path]) -> Path:
    """An empty repository."""
    return lint_tree_builder({})


@pytest.fixture
def lint_data_tree_builder(tmp_path: Path) -> Callable[[str], Path]:
    """Copy a committed tree from `tests/lintlint/data/`, undo its disguise and
    add it to a fresh repository's index.
    """

    def build(name: str) -> Path:
        root = tmp_path / name
        shutil.copytree(DATA / name, root)
        for disguised in sorted(root.rglob(f"*{FIXTURE_SUFFIX}")):
            plain = disguised.name.removesuffix(FIXTURE_SUFFIX)
            if plain.startswith(f"{DOTFILE_PREFIX}."):
                plain = plain[len(DOTFILE_PREFIX) :]
            disguised.rename(disguised.with_name(plain))
        _index(root)
        return root

    return build


@pytest.fixture
def lint_data_tree(lint_data_tree_builder: Callable[[str], Path]) -> Path:
    """The committed `compliant` tree."""
    return lint_data_tree_builder("compliant")


@pytest.fixture
def lint_hook_builder(
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
