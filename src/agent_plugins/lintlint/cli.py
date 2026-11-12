"""The `lint-lint check` CLI — the audit a convergence is verified with.

Built behind the entry's own dispatch, so that a `lint-lint hook` call never
pays for `typer`. Everything imported here is imported only when `check` runs.
"""

from pathlib import Path
from typing import Annotated

import typer

from agent_plugins.lintlint.errors import LintLintError
from agent_plugins.lintlint.report import render_audit
from agent_plugins.lintlint.rules import audit

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Check a repository's lint configuration against the house lint standard.",
)


@app.callback()
def main() -> None:
    """Keep `check` a named subcommand rather than the whole CLI."""


@app.command()
def check(
    directory: Annotated[
        Path | None,
        typer.Argument(help="A directory of the repository (default: the working directory)."),
    ] = None,
) -> None:
    """Audit one repository, exiting non-zero when any finding exists.

    The repository is the one holding the directory. A nested repository is
    neither read for signals nor audited: each is audited on its own.
    """
    try:
        findings = audit(directory or Path.cwd())
    except LintLintError as failure:
        typer.echo(f"lint-lint: {failure}", err=True)
        raise typer.Exit(code=2) from None
    if not findings:
        raise typer.Exit(code=0)
    typer.echo(render_audit(findings))
    raise typer.Exit(code=1)
