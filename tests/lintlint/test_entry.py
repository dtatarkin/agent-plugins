"""The console script: a plain dispatching entry, a stdlib-only hook path, and
a hook answer fast enough to sit on every governed edit.

An app at the entry would import typer on every governed edit and at every
turn end. `ruamel.yaml` is the one third-party module the hook path may load,
which is why it is not in the tuple below.
"""

import json
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

ENTRY_MODULE = "agent_plugins.lintlint.entry"

# Everything the repo depends on that the hook path must never pull in.
THIRD_PARTY = ("typer", "click", "rich", "shellingham")

# The console script the harness runs, as installed beside this interpreter.
SCRIPT = Path(sys.executable).parent / "lint-lint"

# One hook answer must cost less than this. The budget is the whole process:
# interpreter start, imports, stdin, dispatch.
BUDGET_SECONDS = 0.2


def _run(*args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT), *args], input=stdin, capture_output=True, text=True, check=False
    )


class TestEntryPurity:
    def test_importing_the_entry_loads_no_third_party_module(self) -> None:
        # In a subprocess: this test session has typer loaded already.
        code = f"import {ENTRY_MODULE}, json, sys; print(json.dumps(sorted(sys.modules)))"
        loaded = json.loads(
            subprocess.run(
                [sys.executable, "-c", code], capture_output=True, text=True, check=True
            ).stdout
        )
        assert [name for name in loaded if name.split(".")[0] in THIRD_PARTY] == []

    def test_the_hook_path_loads_no_third_party_module(self, tmp_path: Path) -> None:
        code = (
            "import json, sys;"
            "sys.argv = ['lint-lint', 'hook'];"
            f"import {ENTRY_MODULE} as entry;"
            "entry.main();"
            "print(json.dumps(sorted(sys.modules)), file=sys.stderr)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            input=json.dumps({"hook_event_name": "Stop", "session_id": "s"}),
            capture_output=True,
            text=True,
            check=True,
        )
        loaded = json.loads(result.stderr.splitlines()[-1])
        assert [name for name in loaded if name.split(".")[0] in THIRD_PARTY] == []


class TestConsoleScript:
    def test_the_script_is_installed(self) -> None:
        assert SCRIPT.is_file(), "run `uv sync` to install the console scripts"

    def test_check_over_the_drifted_fixtures_exits_one(
        self, lint_data_tree: Callable[[str], Path]
    ) -> None:
        result = _run("check", str(lint_data_tree("drifted")))
        assert result.returncode == 1
        assert "finding(s) in 5 file(s)" in result.stdout

    def test_check_over_the_compliant_fixtures_exits_zero(
        self, lint_data_tree: Callable[[str], Path]
    ) -> None:
        result = _run("check", str(lint_data_tree("compliant")))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_a_hook_answer_is_written_to_stdout_alone(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        payload = json.dumps({"hook_event_name": "Stop", "session_id": "empty"})
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "data"))
        result = _run("hook", stdin=payload)
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_a_hook_answers_within_the_budget(
        self,
        lint_data_tree: Callable[[str], Path],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "data"))
        tree = lint_data_tree("compliant")
        payload = json.dumps(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "timing",
                "tool_name": "Edit",
                "tool_input": {"file_path": str(tree / ".pre-commit-config.yaml")},
            }
        )
        _run("hook", stdin=payload)  # warm the interpreter's caches
        started = time.monotonic()
        result = _run("hook", stdin=payload)
        elapsed = time.monotonic() - started
        assert result.returncode == 0
        assert elapsed < BUDGET_SECONDS, f"{elapsed:.3f}s"
