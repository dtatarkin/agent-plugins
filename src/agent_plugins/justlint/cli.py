"""The `just-lint check` CLI — the audit mode a cleanup pass is verified with.

Built behind the entry's own dispatch, so that a `just-lint hook` call never
pays for `typer`. Everything imported here is imported only when `check` runs.
"""

from pathlib import Path
from typing import Annotated

import typer

from agent_plugins.justlint.checker import audit
from agent_plugins.justlint.errors import JustLintError, JustMissing
from agent_plugins.justlint.report import render_audit

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Check justfiles against the mechanically checkable `just-rules` conventions.",
)


@app.callback()
def main() -> None:
    """Keep `check` a named subcommand rather than the whole CLI."""


@app.command()
def check(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(help="Files or directories to audit (default: the working directory)."),
    ] = None,
) -> None:
    """Audit justfiles, exiting non-zero when any finding exists.

    Every recipe of the named files is checked, and every module their
    entrypoints load — but never one in another git repository: each
    repository is audited on its own.
    """
    try:
        findings = audit(paths or [Path.cwd()])
    except JustMissing:
        typer.echo("just-lint: `just` is not on PATH", err=True)
        raise typer.Exit(code=2) from None
    except JustLintError as failure:
        typer.echo(f"just-lint: {failure}", err=True)
        raise typer.Exit(code=2) from None
    if not findings:
        raise typer.Exit(code=0)
    typer.echo(render_audit(findings))
    raise typer.Exit(code=1)
