"""`just`'s own parse of an entrypoint, as JSON.

The dump is the single source of structure: attributes, where help text came
from, parameter kinds, body fragments with interpolations marked, `shebang`,
`private`, and each module's `source`. It carries no line numbers, which is
why findings name recipes.

The `just` used is whichever one the process's PATH resolves — for a hook,
the one on the PATH the harness runs with, because exec-form hooks skip a
project's devShell by design. Findings therefore rest on parsed structure
alone, which a `just` release does not move the way it moves formatter output.
"""

import json
import subprocess
from pathlib import Path

from agent_plugins.justlint.errors import JustMissing, JustParseFailed
from agent_plugins.justlint.types import JsonObject


def dump_entrypoint(justfile: Path) -> JsonObject:
    """Parse `justfile` and its module tree. Raises `JustMissing` when `just`
    is not on the PATH, `JustParseFailed` when `just` refuses the file.
    """
    try:
        completed = subprocess.run(
            [
                "just",
                "--justfile",
                str(justfile),
                "--working-directory",
                str(justfile.parent),
                "--dump",
                "--dump-format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise JustMissing("`just` is not on PATH") from exc
    if completed.returncode != 0:
        raise JustParseFailed(_diagnostic(completed.stderr))
    parsed: JsonObject = json.loads(completed.stdout)
    return parsed


def _diagnostic(stderr: str) -> str:
    """The one line of a `just` error worth repeating.

    `just` frames its message with the offending source line and a caret rule;
    the `error:` line is the part that says what is wrong.
    """
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("error:"):
            return line.removeprefix("error:").strip()
    return lines[0] if lines else "unparsable"
