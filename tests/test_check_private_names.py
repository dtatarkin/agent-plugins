"""Tests for `scripts/check-private-names` against the private-names-guard spec.

Each test drives the guard as a black box in a throwaway repository under
`tmp_path`, with synthetic `zzq-` names only. It never reads the real list:
`HOME` and `AGENT_PLUGINS_PRIVATE_NAMES` point at temporary files, and the
environment is built from scratch, so neither a hook's git variables nor the
committer's git configuration leak in.
"""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD = REPO_ROOT / "scripts" / "check-private-names"
FALLBACK = ".config/agent-plugins/private-names"
SCISSORS = "# ------------------------ >8 ------------------------"

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
def repo(tmp_path: Path) -> Repo:
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


def fallback(repo: Repo, content: str = LIST) -> None:
    path = repo.home / FALLBACK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# The list is read from outside the repository.


def test_the_variable_names_the_list(repo: Repo) -> None:
    repo.stage("content.txt")
    assert repo.guard("content.txt").returncode == 1


def test_the_fallback_path_holds_the_list(repo: Repo) -> None:
    repo.stage("content.txt")
    fallback(repo)
    assert repo.guard("content.txt", use_list=False).returncode == 1


def test_comment_and_empty_lines_are_not_patterns(repo: Repo) -> None:
    repo.stage("clean.txt", "comment.txt")
    fallback(repo)
    assert repo.guard("clean.txt", "comment.txt", use_list=False).returncode == 0


def test_patterns_are_matched_case_sensitively(repo: Repo) -> None:
    repo.write("upper.txt", "ZZQ-NAME\n")
    repo.stage("upper.txt")
    assert repo.guard("upper.txt").returncode == 0


# The guard fails closed without a usable list.


def test_neither_source_exists(repo: Repo) -> None:
    repo.stage("content.txt")
    result = repo.guard("content.txt", use_list=False)
    assert result.returncode == 2
    assert "AGENT_PLUGINS_PRIVATE_NAMES" in result.stderr
    assert f"~/{FALLBACK}" in result.stderr


def test_the_variable_names_a_missing_file(repo: Repo) -> None:
    repo.stage("content.txt")
    fallback(repo)
    assert repo.guard("content.txt", names=repo.tmp / "missing").returncode == 2


def test_the_list_has_no_pattern(repo: Repo) -> None:
    repo.stage("clean.txt")
    empty = repo.list_file("empty-list", "# only a comment\n\n   \n")
    assert repo.guard("clean.txt", names=empty).returncode == 2


@pytest.mark.parametrize("mode", ["staged", "message", "history"])
def test_a_pattern_is_invalid(repo: Repo, mode: str) -> None:
    repo.stage("clean.txt")
    bad = repo.list_file("bad-list", "zzq-(\n")
    result = repo.guard(*mode_args(repo, mode), names=bad)
    assert result.returncode == 2
    assert "line 1 is not a valid Python regular expression" in result.stderr


POSIX_ONLY = {
    "[[:alpha:]]": "POSIX bracket expression",
    "[^[:digit:]]": "POSIX bracket expression",
    "[[.a.]]": "POSIX bracket expression",
    "[[=a=]]": "POSIX bracket expression",
    "\\<": "GNU word-boundary escape",
    "\\>": "GNU word-boundary escape",
    "\\`": "GNU buffer-anchor escape",
    "\\'": "GNU buffer-anchor escape",
}


def mode_args(repo: Repo, mode: str) -> list[str]:
    if mode == "staged":
        return ["clean.txt"]
    if mode == "message":
        message = repo.tmp / "msg"
        message.write_text("Subject\n")
        return ["--message", str(message)]
    return ["--history"]


@pytest.mark.parametrize("construct", sorted(POSIX_ONLY))
@pytest.mark.parametrize("mode", ["staged", "message", "history"])
def test_a_posix_only_construct_is_refused(repo: Repo, construct: str, mode: str) -> None:
    repo.stage("clean.txt")
    pattern = f"zzq{construct}secret"
    names = repo.list_file("posix-list", f"# a comment\nzzq-[a-z]+\n{pattern}\n")
    result = repo.guard(*mode_args(repo, mode), names=names)
    assert result.returncode == 2
    assert f"line 3 uses a {POSIX_ONLY[construct]}, which is POSIX-only" in result.stderr
    assert "AGENT_PLUGINS_PRIVATE_NAMES" in result.stderr
    # The pattern is itself a private name: it is never printed.
    assert pattern not in result.stdout + result.stderr
    assert "secret" not in result.stdout + result.stderr


@pytest.mark.parametrize("pattern", ["zzq\\[:x", "zzq[\\[:x]", "zzq[a-z][:]", "zzq\\\\<"])
def test_an_escaped_lookalike_is_accepted(repo: Repo, pattern: str) -> None:
    repo.stage("clean.txt")
    names = repo.list_file("lookalike-list", f"{pattern}\n")
    assert repo.guard("clean.txt", names=names).returncode == 0


# Every staged path and its staged content are checked.


def test_staged_content_names_a_private_name(repo: Repo) -> None:
    repo.stage("content.txt")
    result = repo.guard("content.txt")
    assert result.returncode == 1
    assert result.stdout == "content.txt:3: zzq-content\n"


def test_a_staged_path_names_a_private_name(repo: Repo) -> None:
    repo.write("dir/zzq-path.txt", "nothing\n")
    repo.stage("dir/zzq-path.txt")
    result = repo.guard("dir/zzq-path.txt")
    assert result.returncode == 1
    assert result.stdout == "dir/zzq-path.txt: path matches: zzq-path\n"


def test_a_symbolic_link_points_at_a_private_name(repo: Repo) -> None:
    (repo.root / "link").symlink_to("zzq-link")
    repo.stage("link")
    result = repo.guard("link")
    assert result.returncode == 1
    assert result.stdout == "link: link target matches: zzq-link\n"


@pytest.mark.parametrize(
    "path", [".claude/commands/opsx/x.md", "openspec/changes/archive/old/y.md"]
)
def test_generated_and_archived_files_are_not_exempt(repo: Repo, path: str) -> None:
    repo.write(path, "zzq-generated\n")
    repo.stage(path)
    assert repo.guard(path).returncode == 1


def test_binary_files_are_not_exempt(repo: Repo) -> None:
    repo.write("blob.bin", b"bin\x00zzq-binary\x00\n")
    repo.stage("blob.bin")
    assert repo.guard("blob.bin").returncode == 1


def test_the_index_is_read_not_the_working_tree(repo: Repo) -> None:
    repo.write("dirty.txt", "zzq-staged\n")
    repo.stage("dirty.txt")
    repo.write("dirty.txt", "clean now\n")
    assert repo.guard("dirty.txt").returncode == 1


def test_an_unstaged_match_does_not_fail_the_commit(repo: Repo) -> None:
    repo.stage("clean.txt")
    repo.write("clean.txt", "nothing to see\nzzq-unstaged\n")
    assert repo.guard("clean.txt").returncode == 0


def test_a_clean_commit_passes(repo: Repo) -> None:
    repo.stage("clean.txt", "comment.txt")
    result = repo.guard("clean.txt", "comment.txt")
    assert result.returncode == 0
    assert result.stdout == ""


def test_no_paths_handed_passes(repo: Repo) -> None:
    assert repo.guard().returncode == 0
    assert repo.guard("--").returncode == 0


def test_an_unknown_option_cannot_run(repo: Repo) -> None:
    result = repo.guard("--bogus")
    assert result.returncode == 2
    assert "unknown option '--bogus'" in result.stderr


# The commit message is checked.


def test_the_message_names_a_private_name(repo: Repo) -> None:
    message = repo.tmp / "msg"
    message.write_text("Subject\n\nbody zzq-message\n")
    result = repo.guard("--message", str(message))
    assert result.returncode == 1
    assert result.stdout == "commit message:3: zzq-message\n"


def test_gits_comment_lines_are_ignored(repo: Repo) -> None:
    message = repo.tmp / "msg"
    message.write_text(f"Subject\n# zzq-comment\n{SCISSORS}\nzzq-diff\n")
    assert repo.guard("--message", str(message)).returncode == 0


# One install enables both checks; the guard runs only locally.


def test_one_install_enables_both_checks() -> None:
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
    assert re.search(r"^default_install_hook_types: \[pre-commit, commit-msg\]$", config, re.M)


def test_no_workflow_runs_the_guard() -> None:
    for name in (".github", ".gitlab-ci.yml", ".circleci", ".woodpecker", ".forgejo", ".gitea"):
        path = REPO_ROOT / name
        files = [path] if path.is_file() else (p for p in path.rglob("*") if p.is_file())
        for file in files:
            assert "check-private-names" not in file.read_text(errors="replace"), file


# The whole history can be checked.


def test_history(repo: Repo) -> None:
    repo.stage("clean.txt")
    repo.commit("-m", "clean start")
    assert repo.guard("--history").returncode == 0

    repo.stage("content.txt")
    bad = repo.commit("-m", "made without the hooks")
    repo.commit("--allow-empty", "-m", "clean on top")
    result = repo.guard("--history")
    assert result.returncode == 1
    assert f"{bad}: content.txt:3: zzq-content" in result.stdout

    repo.git("reset", "-q", "--hard", "HEAD~2")
    assert repo.guard("--history").returncode == 0


@pytest.mark.parametrize(
    "case", ["message", "author", "link", "branch", "tag"], ids=lambda c: f"a {c}"
)
def test_history_covers(repo: Repo, case: str) -> None:
    repo.stage("clean.txt")
    repo.commit("-m", "clean start")
    if case == "message":
        repo.commit("--allow-empty", "-m", "clean subject", "-m", "zzq-history-message")
    elif case == "author":
        repo.commit("--allow-empty", "-m", "clean", GIT_AUTHOR_NAME="zzq-author")
    elif case == "link":
        (repo.root / "hlink").symlink_to("zzq-history-link")
        repo.git("add", "hlink")
        repo.commit("-m", "a link")
    elif case == "branch":
        repo.git("branch", "zzq-branch")
    else:
        repo.git("tag", "-a", "-m", "zzq-tag-message", "v0")
    assert repo.guard("--history").returncode == 1


# The output, byte for byte, on a fixture with a finding of every kind. The
# expected text was produced by the bash guard this one replaced.

PARITY_STAGED = """\
d/zzq-dir/f: path matches: zzq-dir
blob.bin:1: zzq-bin
crlf.txt:1: zzq-crlf
shared.txt:1: zzq-one
shared.txt:1: zzq-two
shared.txt:2: yyq
lnk: link target matches: zzq-target
"""

PARITY_MESSAGE = """\
commit message:1: zzq-s
commit message:3: yyq
commit message:3: zzq-b
"""

PARITY_HISTORY = """\
{third}: blob.bin:1: zzq-bin
{third}: copy.txt:1: zzq-one
{third}: copy.txt:1: zzq-two
{third}: copy.txt:2: yyq
{third}: crlf.txt:1: zzq-crlf
{third}: shared.txt:1: zzq-one
{third}: shared.txt:1: zzq-two
{third}: shared.txt:2: yyq
{third}: d/zzq-dir/f: path matches: zzq-dir
{third}: lnk: link target matches: zzq-target
{second}: blob.bin:1: zzq-bin
{second}: copy.txt:1: zzq-one
{second}: copy.txt:1: zzq-two
{second}: copy.txt:2: yyq
{second}: crlf.txt:1: zzq-crlf
{second}: shared.txt:1: zzq-one
{second}: shared.txt:1: zzq-two
{second}: shared.txt:2: yyq
{second}: d/zzq-dir/f: path matches: zzq-dir
{second}: lnk: link target matches: zzq-target
{second}: identity and message line 1: zzq-auth
{first}: blob.bin:1: zzq-bin
{first}: crlf.txt:1: zzq-crlf
{first}: shared.txt:1: zzq-one
{first}: shared.txt:1: zzq-two
{first}: shared.txt:2: yyq
{first}: d/zzq-dir/f: path matches: zzq-dir
{first}: lnk: link target matches: zzq-target
{first}: identity and message line 3: zzq-msg
{first}: identity and message line 5: yyq
ref refs/heads/zzq-br: path matches: zzq-br
refs/tags/v1: tag object line 6: zzq-tag
"""


def test_output_parity(repo: Repo) -> None:
    names = repo.list_file("parity-list", "# c\n\nzzq-[a-z]+\nyyq\n")
    repo.write("shared.txt", "a zzq-one b zzq-two\nyyq\n")
    repo.write("crlf.txt", b"crlf zzq-crlf\r\nok\r\n")
    repo.write("blob.bin", b"bin\x00zzq-bin\x00\n")
    repo.write("d/zzq-dir/f", "x\n")
    (repo.root / "lnk").symlink_to("zzq-target")
    staged = ["shared.txt", "crlf.txt", "blob.bin", "d/zzq-dir/f", "lnk"]
    repo.stage(*staged)

    result = repo.guard("--", *staged, names=names)
    assert (result.returncode, result.stdout) == (1, PARITY_STAGED)

    message = repo.tmp / "msg"
    message.write_text(f"Subject zzq-s\n\nbody yyq zzq-b\n# zzq-c\n{SCISSORS}\nzzq-d\n")
    result = repo.guard("--message", str(message), names=names)
    assert (result.returncode, result.stdout) == (1, PARITY_MESSAGE)

    first = repo.commit("-m", "first zzq-msg", "-m", "body yyq")
    repo.write("copy.txt", "a zzq-one b zzq-two\nyyq\n")
    repo.git("add", "copy.txt")
    second = repo.commit("-m", "second", GIT_AUTHOR_NAME="zzq-auth")
    # An empty commit shares its parent's tree, and so its findings.
    third = repo.commit("--allow-empty", "-m", "empty")
    repo.git("branch", "zzq-br")
    repo.git("tag", "-a", "-m", "tag zzq-tag", "v1")

    result = repo.guard("--history", names=names)
    assert result.returncode == 1
    assert result.stdout == PARITY_HISTORY.format(first=first, second=second, third=third)
    assert result.stderr == (
        "check-private-names: the list matched; nothing above may be committed\n"
    )
