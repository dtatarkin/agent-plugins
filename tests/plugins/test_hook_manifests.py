"""Guards the form and the resolvability of every hook a plugin ships.

A hook that fails does so silently, so both failures this catches are
invisible at runtime. Shell form is the first: a `command` string with no
`args` is handed to a shell, and a project's shell prefix then wraps it —
entering a devShell on every call and mixing its output into the stream where
the hook's JSON must stand alone. An unresolvable command is the second: it
fails once per event and says nothing.
"""

import json
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_FILES = sorted(REPO_ROOT.glob("plugins/*/hooks/hooks.json"))


def console_scripts() -> set[str]:
    """The names this repository installs on the PATH."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return set(pyproject["project"]["scripts"])


def hook_violations(manifest: dict, scripts: set[str], plugin_dir: Path) -> list[str]:
    """Violations of the hook contract; empty for a compliant manifest."""
    violations: list[str] = []
    for event, groups in manifest.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                where = f"{event}: {hook.get('command')!r}"
                if not isinstance(hook.get("args"), list):
                    violations.append(f"{where} is in shell form (no `args`)")
                    continue
                command = hook.get("command", "")
                relative = command.replace("${CLAUDE_PLUGIN_ROOT}/", "")
                inside_plugin = (plugin_dir / relative).is_file()
                if command not in scripts and not inside_plugin:
                    violations.append(
                        f"{where} is neither a registered console script nor a file in the plugin"
                    )
    return violations


class TestEveryHookManifest:
    def test_a_plugin_ships_hooks(self) -> None:
        """Keeps the parametrized test below from passing vacuously."""
        assert HOOK_FILES, "no plugin ships hooks — the hook contract is unguarded"

    @pytest.mark.parametrize("path", HOOK_FILES, ids=lambda path: path.parts[-3])
    def test_is_exec_form_and_resolvable(self, path: Path) -> None:
        manifest = json.loads(path.read_text())
        assert hook_violations(manifest, console_scripts(), path.parents[1]) == []


class TestRejections:
    def test_a_shell_form_hook(self) -> None:
        hook = {"type": "command", "command": "just-lint hook"}
        manifest = {"hooks": {"Stop": [{"hooks": [hook]}]}}
        assert hook_violations(manifest, {"just-lint"}, REPO_ROOT) == [
            "Stop: 'just-lint hook' is in shell form (no `args`)"
        ]

    def test_an_unregistered_command(self) -> None:
        manifest = {
            "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "nope", "args": []}]}]}
        }
        assert hook_violations(manifest, {"just-lint"}, REPO_ROOT) == [
            "Stop: 'nope' is neither a registered console script nor a file in the plugin"
        ]
