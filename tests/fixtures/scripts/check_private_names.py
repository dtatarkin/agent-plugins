"""A throwaway repository for `scripts/check-private-names` to guard.

The repository lives under `tmp_path` and names only synthetic `zzq-` patterns.
It never reads the real list: `HOME` and `AGENT_PLUGINS_PRIVATE_NAMES` point at
temporary files, and the environment is built from scratch, so neither a hook's
git variables nor the committer's git configuration leak in.
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
GUARD = REPO_ROOT / "scripts" / "check-private-names"

# A comment and an empty line around one pattern.
LIST = "# qqcomment\n\nzzq-[a-z]+\n"


@dataclass
class Repo:
    root: Path
    home: Path
    list: Path
    tmp: Path

    def env(self, names: Path | None) -> dict[str, str]:
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Tester",
            "GIT_AUTHOR_EMAIL": "tester@example.invalid",
            "GIT_COMMITTER_NAME": "Tester",
            "GIT_COMMITTER_EMAIL": "tester@example.invalid",
            # Fixed dates, so commit ids are the same on every run.
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        }
        if names is not None:
            env["AGENT_PLUGINS_PRIVATE_NAMES"] = str(names)
        return env

    def guard(
        self, *args: str, names: Path | None = None, use_list: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Run the guard; NAMES overrides the list, USE_LIST=False unsets the variable."""
        chosen = names if names is not None else (self.list if use_list else None)
        return subprocess.run(
            [str(GUARD), *args],
            cwd=self.root,
            env=self.env(chosen),
            capture_output=True,
            text=True,
            check=False,
        )

    def git(self, *args: str, **extra: str) -> str:
        done = subprocess.run(
            ["git", *args],
            cwd=self.root,
            env={**self.env(None), **extra},
            capture_output=True,
            text=True,
            check=True,
        )
        return done.stdout

    def write(self, path: str, content: str | bytes) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content)

    def stage(self, *paths: str) -> None:
        """A fresh index: exactly the given paths, nothing left from before."""
        self.git("rm", "-q", "-r", "-f", "--cached", "--ignore-unmatch", ".")
        self.git("add", "--", *paths)

    def commit(self, *args: str, **extra: str) -> str:
        self.git("commit", "-q", "--no-verify", *args, **extra)
        return self.git("rev-parse", "HEAD").strip()

    def list_file(self, name: str, content: str) -> Path:
        path = self.tmp / name
        path.write_text(content)
        return path


@pytest.fixture
def guard_repo(tmp_path: Path) -> Repo:
    home = tmp_path / "home"
    home.mkdir()
    names = tmp_path / "list"
    names.write_text(LIST)
    built = Repo(root=tmp_path / "repo", home=home, list=names, tmp=tmp_path)
    built.root.mkdir()
    built.git("init", "-q")
    built.write("clean.txt", "nothing to see\n")
    built.write("comment.txt", "qqcomment\n# qqcomment\n")
    built.write("content.txt", "a\nb\nzzq-content here\n")
    return built
