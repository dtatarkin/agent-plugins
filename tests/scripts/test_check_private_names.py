"""Tests for `scripts/check-private-names` against the private-names-guard spec.

Each test drives the guard as a black box in the throwaway repository the
`guard_repo` fixture builds, with synthetic `zzq-` names only.
"""

import re
from pathlib import Path

import pytest

from tests.fixtures.scripts.check_private_names import LIST, Repo

REPO_ROOT = Path(__file__).resolve().parents[2]
FALLBACK = ".config/agent-plugins/private-names"
SCISSORS = "# ------------------------ >8 ------------------------"


def fallback(guard_repo: Repo, content: str = LIST) -> None:
    path = guard_repo.home / FALLBACK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


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


def mode_args(guard_repo: Repo, mode: str) -> list[str]:
    if mode == "staged":
        return ["clean.txt"]
    if mode == "message":
        message = guard_repo.tmp / "msg"
        message.write_text("Subject\n")
        return ["--message", str(message)]
    return ["--history"]


EXPECTED_STAGED = """\
d/zzq-dir/f: path matches: zzq-dir
blob.bin:1: zzq-bin
crlf.txt:1: zzq-crlf
shared.txt:1: zzq-one
shared.txt:1: zzq-two
shared.txt:2: yyq
lnk: link target matches: zzq-target
"""

EXPECTED_MESSAGE = """\
commit message:1: zzq-s
commit message:3: yyq
commit message:3: zzq-b
"""

EXPECTED_HISTORY = """\
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


class TestListSource:
    """The list is read from outside the repository."""

    def test_the_variable_names_the_list(self, guard_repo: Repo) -> None:
        guard_repo.stage("content.txt")
        assert guard_repo.guard("content.txt").returncode == 1

    def test_the_fallback_path_holds_the_list(self, guard_repo: Repo) -> None:
        guard_repo.stage("content.txt")
        fallback(guard_repo)
        assert guard_repo.guard("content.txt", use_list=False).returncode == 1

    def test_comment_and_empty_lines_are_not_patterns(self, guard_repo: Repo) -> None:
        guard_repo.stage("clean.txt", "comment.txt")
        fallback(guard_repo)
        assert guard_repo.guard("clean.txt", "comment.txt", use_list=False).returncode == 0

    def test_patterns_are_matched_case_sensitively(self, guard_repo: Repo) -> None:
        guard_repo.write("upper.txt", "ZZQ-NAME\n")
        guard_repo.stage("upper.txt")
        assert guard_repo.guard("upper.txt").returncode == 0


class TestFailClosed:
    """The guard fails closed without a usable list."""

    def test_neither_source_exists(self, guard_repo: Repo) -> None:
        guard_repo.stage("content.txt")
        result = guard_repo.guard("content.txt", use_list=False)
        assert result.returncode == 2
        assert "AGENT_PLUGINS_PRIVATE_NAMES" in result.stderr
        assert f"~/{FALLBACK}" in result.stderr

    def test_the_variable_names_a_missing_file(self, guard_repo: Repo) -> None:
        guard_repo.stage("content.txt")
        fallback(guard_repo)
        assert guard_repo.guard("content.txt", names=guard_repo.tmp / "missing").returncode == 2

    def test_the_list_has_no_pattern(self, guard_repo: Repo) -> None:
        guard_repo.stage("clean.txt")
        empty = guard_repo.list_file("empty-list", "# only a comment\n\n   \n")
        assert guard_repo.guard("clean.txt", names=empty).returncode == 2

    @pytest.mark.parametrize("mode", ["staged", "message", "history"])
    def test_a_pattern_is_invalid(self, guard_repo: Repo, mode: str) -> None:
        guard_repo.stage("clean.txt")
        bad = guard_repo.list_file("bad-list", "zzq-(\n")
        result = guard_repo.guard(*mode_args(guard_repo, mode), names=bad)
        assert result.returncode == 2
        assert "line 1 is not a valid Python regular expression" in result.stderr

    @pytest.mark.parametrize("construct", sorted(POSIX_ONLY))
    @pytest.mark.parametrize("mode", ["staged", "message", "history"])
    def test_a_posix_only_construct_is_refused(
        self, guard_repo: Repo, construct: str, mode: str
    ) -> None:
        guard_repo.stage("clean.txt")
        pattern = f"zzq{construct}secret"
        names = guard_repo.list_file("posix-list", f"# a comment\nzzq-[a-z]+\n{pattern}\n")
        result = guard_repo.guard(*mode_args(guard_repo, mode), names=names)
        assert result.returncode == 2
        assert f"line 3 uses a {POSIX_ONLY[construct]}, which is POSIX-only" in result.stderr
        assert "AGENT_PLUGINS_PRIVATE_NAMES" in result.stderr
        # The pattern is itself a private name: it is never printed.
        assert pattern not in result.stdout + result.stderr
        assert "secret" not in result.stdout + result.stderr

    @pytest.mark.parametrize("pattern", ["zzq\\[:x", "zzq[\\[:x]", "zzq[a-z][:]", "zzq\\\\<"])
    def test_an_escaped_lookalike_is_accepted(self, guard_repo: Repo, pattern: str) -> None:
        guard_repo.stage("clean.txt")
        names = guard_repo.list_file("lookalike-list", f"{pattern}\n")
        assert guard_repo.guard("clean.txt", names=names).returncode == 0


class TestStaged:
    """Every staged path and its staged content are checked."""

    def test_staged_content_names_a_private_name(self, guard_repo: Repo) -> None:
        guard_repo.stage("content.txt")
        result = guard_repo.guard("content.txt")
        assert result.returncode == 1
        assert result.stdout == "content.txt:3: zzq-content\n"

    def test_a_staged_path_names_a_private_name(self, guard_repo: Repo) -> None:
        guard_repo.write("dir/zzq-path.txt", "nothing\n")
        guard_repo.stage("dir/zzq-path.txt")
        result = guard_repo.guard("dir/zzq-path.txt")
        assert result.returncode == 1
        assert result.stdout == "dir/zzq-path.txt: path matches: zzq-path\n"

    def test_a_symbolic_link_points_at_a_private_name(self, guard_repo: Repo) -> None:
        (guard_repo.root / "link").symlink_to("zzq-link")
        guard_repo.stage("link")
        result = guard_repo.guard("link")
        assert result.returncode == 1
        assert result.stdout == "link: link target matches: zzq-link\n"

    @pytest.mark.parametrize(
        "path", [".claude/commands/opsx/x.md", "openspec/changes/archive/old/y.md"]
    )
    def test_generated_and_archived_files_are_not_exempt(self, guard_repo: Repo, path: str) -> None:
        guard_repo.write(path, "zzq-generated\n")
        guard_repo.stage(path)
        assert guard_repo.guard(path).returncode == 1

    def test_binary_files_are_not_exempt(self, guard_repo: Repo) -> None:
        guard_repo.write("blob.bin", b"bin\x00zzq-binary\x00\n")
        guard_repo.stage("blob.bin")
        assert guard_repo.guard("blob.bin").returncode == 1

    def test_the_index_is_read_not_the_working_tree(self, guard_repo: Repo) -> None:
        guard_repo.write("dirty.txt", "zzq-staged\n")
        guard_repo.stage("dirty.txt")
        guard_repo.write("dirty.txt", "clean now\n")
        assert guard_repo.guard("dirty.txt").returncode == 1

    def test_an_unstaged_match_does_not_fail_the_commit(self, guard_repo: Repo) -> None:
        guard_repo.stage("clean.txt")
        guard_repo.write("clean.txt", "nothing to see\nzzq-unstaged\n")
        assert guard_repo.guard("clean.txt").returncode == 0

    def test_a_clean_commit_passes(self, guard_repo: Repo) -> None:
        guard_repo.stage("clean.txt", "comment.txt")
        result = guard_repo.guard("clean.txt", "comment.txt")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_no_paths_handed_passes(self, guard_repo: Repo) -> None:
        assert guard_repo.guard().returncode == 0
        assert guard_repo.guard("--").returncode == 0

    def test_an_unknown_option_cannot_run(self, guard_repo: Repo) -> None:
        result = guard_repo.guard("--bogus")
        assert result.returncode == 2
        assert "unknown option '--bogus'" in result.stderr


class TestMessage:
    """The commit message is checked."""

    def test_the_message_names_a_private_name(self, guard_repo: Repo) -> None:
        message = guard_repo.tmp / "msg"
        message.write_text("Subject\n\nbody zzq-message\n")
        result = guard_repo.guard("--message", str(message))
        assert result.returncode == 1
        assert result.stdout == "commit message:3: zzq-message\n"

    def test_gits_comment_lines_are_ignored(self, guard_repo: Repo) -> None:
        message = guard_repo.tmp / "msg"
        message.write_text(f"Subject\n# zzq-comment\n{SCISSORS}\nzzq-diff\n")
        assert guard_repo.guard("--message", str(message)).returncode == 0


class TestInstall:
    """One install enables both checks; the guard runs only locally."""

    def test_one_install_enables_both_checks(self) -> None:
        config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
        assert re.search(r"^default_install_hook_types: \[pre-commit, commit-msg\]$", config, re.M)

    def test_no_workflow_runs_the_guard(self) -> None:
        for name in (".github", ".gitlab-ci.yml", ".circleci", ".woodpecker", ".forgejo", ".gitea"):
            path = REPO_ROOT / name
            files = [path] if path.is_file() else (p for p in path.rglob("*") if p.is_file())
            for file in files:
                assert "check-private-names" not in file.read_text(errors="replace"), file


class TestHistory:
    """The whole history can be checked."""

    def test_a_finding_fails_until_its_commit_is_gone(self, guard_repo: Repo) -> None:
        guard_repo.stage("clean.txt")
        guard_repo.commit("-m", "clean start")
        assert guard_repo.guard("--history").returncode == 0

        guard_repo.stage("content.txt")
        bad = guard_repo.commit("-m", "made without the hooks")
        guard_repo.commit("--allow-empty", "-m", "clean on top")
        result = guard_repo.guard("--history")
        assert result.returncode == 1
        assert f"{bad}: content.txt:3: zzq-content" in result.stdout

        guard_repo.git("reset", "-q", "--hard", "HEAD~2")
        assert guard_repo.guard("--history").returncode == 0

    @pytest.mark.parametrize(
        "case", ["message", "author", "link", "branch", "tag"], ids=lambda c: f"a {c}"
    )
    def test_covers(self, guard_repo: Repo, case: str) -> None:
        guard_repo.stage("clean.txt")
        guard_repo.commit("-m", "clean start")
        if case == "message":
            guard_repo.commit("--allow-empty", "-m", "clean subject", "-m", "zzq-history-message")
        elif case == "author":
            guard_repo.commit("--allow-empty", "-m", "clean", GIT_AUTHOR_NAME="zzq-author")
        elif case == "link":
            (guard_repo.root / "hlink").symlink_to("zzq-history-link")
            guard_repo.git("add", "hlink")
            guard_repo.commit("-m", "a link")
        elif case == "branch":
            guard_repo.git("branch", "zzq-branch")
        else:
            guard_repo.git("tag", "-a", "-m", "zzq-tag-message", "v0")
        assert guard_repo.guard("--history").returncode == 1


class TestOutput:
    """The output, byte for byte, on a fixture with a finding of every kind.

    The expected text is the guard's output contract, held to the byte: a change
    to it is a change of that contract, not a refresh of the test.
    """

    def test_every_kind_of_finding(self, guard_repo: Repo) -> None:
        names = guard_repo.list_file("parity-list", "# c\n\nzzq-[a-z]+\nyyq\n")
        guard_repo.write("shared.txt", "a zzq-one b zzq-two\nyyq\n")
        guard_repo.write("crlf.txt", b"crlf zzq-crlf\r\nok\r\n")
        guard_repo.write("blob.bin", b"bin\x00zzq-bin\x00\n")
        guard_repo.write("d/zzq-dir/f", "x\n")
        (guard_repo.root / "lnk").symlink_to("zzq-target")
        staged = ["shared.txt", "crlf.txt", "blob.bin", "d/zzq-dir/f", "lnk"]
        guard_repo.stage(*staged)

        result = guard_repo.guard("--", *staged, names=names)
        assert (result.returncode, result.stdout) == (1, EXPECTED_STAGED)

        message = guard_repo.tmp / "msg"
        message.write_text(f"Subject zzq-s\n\nbody yyq zzq-b\n# zzq-c\n{SCISSORS}\nzzq-d\n")
        result = guard_repo.guard("--message", str(message), names=names)
        assert (result.returncode, result.stdout) == (1, EXPECTED_MESSAGE)

        first = guard_repo.commit("-m", "first zzq-msg", "-m", "body yyq")
        guard_repo.write("copy.txt", "a zzq-one b zzq-two\nyyq\n")
        guard_repo.git("add", "copy.txt")
        second = guard_repo.commit("-m", "second", GIT_AUTHOR_NAME="zzq-auth")
        # An empty commit shares its parent's tree, and so its findings.
        third = guard_repo.commit("--allow-empty", "-m", "empty")
        guard_repo.git("branch", "zzq-br")
        guard_repo.git("tag", "-a", "-m", "tag zzq-tag", "v1")

        result = guard_repo.guard("--history", names=names)
        assert result.returncode == 1
        assert result.stdout == EXPECTED_HISTORY.format(first=first, second=second, third=third)
        assert result.stderr == (
            "check-private-names: the list matched; nothing above may be committed\n"
        )
