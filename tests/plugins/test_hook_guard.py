"""Guards the `run-checker` script both checker plugins route their hooks through.

The plugins must run where their checker is not installed: every edit and
turn-end hook then exits quietly, and one notice at session start says what is
off. The guard is what makes that so, and it also hides the tool name from
`test_hook_manifests.py`, which sees only the guard as the `command`. This
test checks the tool that now sits in `args` instead.
"""

import json
import os
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_COMMAND = "${CLAUDE_PLUGIN_ROOT}/hooks/run-checker"
TOOLS = {"lint-rules": "lint-lint", "just-rules": "just-lint"}
GUARD = REPO_ROOT / "plugins" / "lint-rules" / "hooks" / "run-checker"
# Unique to this test, so a machine with the real checkers installed cannot
# skew the behaviour checks.
STUB_TOOL = "hook-guard-test-stub-tool"
LARGE_PAYLOAD = b"x" * (128 * 1024)


def manifest(plugin: str) -> dict:
    path = REPO_ROOT / "plugins" / plugin / "hooks" / "hooks.json"
    return json.loads(path.read_text())


def run_guard(
    args: list[str], path_dir: Path, stdin: bytes = b"{}"
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(GUARD), *args],
        input=stdin,
        capture_output=True,
        env={"PATH": f"{path_dir}:/usr/bin:/bin"},
        check=False,
        timeout=10,
    )


class TestWiring:
    def test_guard_copies_are_identical_executable_sh_scripts(self) -> None:
        copies = [REPO_ROOT / "plugins" / plugin / "hooks" / "run-checker" for plugin in TOOLS]
        contents = [copy.read_bytes() for copy in copies]
        assert contents[0] == contents[1]
        for copy, content in zip(copies, contents, strict=True):
            assert os.access(copy, os.X_OK), copy
            assert content.startswith(b"#!/bin/sh\n"), copy

    @pytest.mark.parametrize("plugin", sorted(TOOLS))
    def test_every_edit_and_turn_end_hook_runs_through_the_guard(self, plugin: str) -> None:
        routed = 0
        for event, groups in manifest(plugin)["hooks"].items():
            if event == "SessionStart":
                continue
            for group in groups:
                for hook in group["hooks"]:
                    assert hook["command"] == GUARD_COMMAND, (event, hook)
                    assert hook["args"] == [TOOLS[plugin], "hook"], (event, hook)
                    routed += 1
        assert routed > 0

    @pytest.mark.parametrize("plugin", sorted(TOOLS))
    def test_the_guarded_tool_is_a_console_script(self, plugin: str) -> None:
        pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
        assert TOOLS[plugin] in pyproject["project"]["scripts"]

    @pytest.mark.parametrize("plugin", sorted(TOOLS))
    def test_one_session_start_group_carries_the_notice(self, plugin: str) -> None:
        groups = manifest(plugin)["hooks"]["SessionStart"]
        assert len(groups) == 1
        (group,) = groups
        assert "matcher" not in group
        (hook,) = group["hooks"]
        assert hook["command"] == GUARD_COMMAND
        assert hook["args"] == ["--notice", TOOLS[plugin], plugin]


class TestRunningTheGuard:
    @pytest.fixture
    def stub_dir(self, tmp_path: Path) -> Path:
        stub = tmp_path / STUB_TOOL
        stub.write_text('#!/bin/sh\necho "args: $*"\ncat\nexit 3\n')
        stub.chmod(0o755)
        return tmp_path

    @pytest.mark.parametrize("stdin", [b"{}", LARGE_PAYLOAD], ids=["small", "over-64k"])
    def test_missing_tool_exits_quietly(self, tmp_path: Path, stdin: bytes) -> None:
        result = run_guard([STUB_TOOL, "hook"], tmp_path, stdin)
        assert (result.returncode, result.stdout, result.stderr) == (0, b"", b"")

    def test_present_tool_takes_over_untouched(self, stub_dir: Path) -> None:
        result = run_guard([STUB_TOOL, "hook"], stub_dir, b'{"payload": 1}')
        assert result.returncode == 3
        assert result.stdout == b'args: hook\n{"payload": 1}'

    def test_notice_is_silent_when_the_tool_is_present(self, stub_dir: Path) -> None:
        result = run_guard(["--notice", STUB_TOOL, "some-plugin"], stub_dir)
        assert (result.returncode, result.stdout) == (0, b"")

    def test_notice_names_the_missing_tool_and_plugin(self, tmp_path: Path) -> None:
        result = run_guard(["--notice", STUB_TOOL, "some-plugin"], tmp_path, LARGE_PAYLOAD)
        assert result.returncode == 0
        notice = json.loads(result.stdout)
        assert notice["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        message = notice["systemMessage"]
        assert STUB_TOOL in message
        assert "some-plugin" in message
        assert "uv tool install" in message
        assert "git+https://github.com/dtatarkin/agent-plugins" in message
        context = notice["hookSpecificOutput"]["additionalContext"]
        assert STUB_TOOL in context
        assert "some-plugin" in context
