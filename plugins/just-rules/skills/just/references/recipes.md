---
paths:
  - "**/justfile"
  - "**/*.just"
---

# Recipes — attributes, comments, bodies

- **Help text via `[doc("…")]`, always.** Every recipe that shows up in
  `just --list` carries an explicit `[doc("…")]` holding its one-line help.
  Never rely on the bare-comment fallback: `just` takes only the *last* `#` line
  above the recipe as the description, which silently breaks the moment
  multi-line rationale grows above it. The `[doc("…")]` is the help text, full
  stop.
- **Comments are rationale only — never the help text.** Use `#` lines above a
  recipe for the *why*, examples, gotchas, when-to-run notes. Never duplicate
  the `[doc("…")]` string in a comment; a recipe that needs no extra context has
  its `[doc("…")]` and no comment at all.
- **Separate a rationale comment from the recipe with one blank line.** Not
  cosmetic: `just` binds a comment line *touching* a recipe as its doc-comment,
  and `just --fmt` then **deletes that line** because `[doc("…")]` supersedes it
  — silently dropping your last line of rationale.

  ```just
  # dbt wants these at the subcommand level, not the top level, so `dbt <cmd>
  # [args]` becomes `dbt <cmd> --project-dir … --profiles-dir … [args]`.

  [doc("Wrap `dbt` with the project/profiles dirs baked in")]
  [positional-arguments]
  dbt cmd *args:
      #!/usr/bin/env bash
      set -euo pipefail
      cmd=$1; shift
      uv run dbt "$cmd" --project-dir dbt_proj --profiles-dir dbt_proj "$@"
  ```

- **Don't hand-order attributes.** `just --fmt` sorts them alphabetically
  (`[default]`, `[doc("…")]`, `[linux]`, `[no-cd]`, `[private]`, …): write them
  in any order and let the formatter normalize.
- **`[no-cd]` on any recipe meant to act in the caller's directory** (most git,
  submodule and lint recipes). Without it `just` runs the recipe from the
  module's own directory, which is almost never what a shared recipe wants.
- **`[private]` plus a `_underscore` name prefix for internal helpers** that
  must not appear in `--list` (e.g. `_members`). A private recipe has no help
  text, so it carries **no** `[doc("…")]`; a `#` rationale comment is fine.
- **Shebang body for multi-line shell**, with strict mode. A recipe with more
  than one shell statement needs it: without a shebang `just` runs each line in
  its own shell, so neither `set -e` nor a variable survives to the next line.

  ```just
  [doc("…")]
  recipe arg:
      #!/usr/bin/env bash
      set -euo pipefail
      …
  ```

  A single command stays a plain recipe line — no shebang.
- **Group recipes with `[group("…")]` when concerns cluster.** A justfile whose
  public recipes span several distinct concerns (bootstrap, git, qa, codegen, …)
  carries `[group("…")]` so `just --list` prints them organized. Group names are
  lowercase single words, reused across repositories for recurring concerns
  (`qa`, `git`, `codegen`). Small single-concern files need no groups.

## Formatting

Format with `just just::format <justfile>` (a wrapper over
`just --fmt --unstable`) before committing any justfile change. Commit hooks
reject an unformatted justfile, so don't fight the formatter — let it normalize
spacing and alignment.
