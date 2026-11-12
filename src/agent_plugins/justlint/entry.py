"""The `just-lint` console-script entry: a plain function dispatching on its
first argument.

Not a `typer` app. An app at the entry would import typer on every governed
edit and at every turn end, because the console script is what the hooks run.
`hook` therefore reaches only the standard library, and `check` builds its app
inside its own branch. A test imports this module and asserts that no
third-party module was loaded.
"""

import sys

HOOK_COMMAND = "hook"


def main() -> int:
    """Route to the hook path or the audit CLI, importing only what is used."""
    argv = sys.argv[1:]
    if argv and argv[0] == HOOK_COMMAND:
        from agent_plugins.justlint.hook import run_hook

        return run_hook()
    from agent_plugins.justlint.cli import app

    app(args=argv, prog_name="just-lint")
    return 0
