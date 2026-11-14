---
paths:
  - "**/justfile"
  - "**/*.just"
  - "**/.just"
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
  cosmetic: `just` binds the last comment line *touching* a recipe as its
  doc-comment. `[doc("…")]` outranks it, but the binding stays: drop or lose
  the attribute and that line of rationale becomes the help text
  `just --list` prints.

  ```just
  # The tool reads its config only at the subcommand level, so
  # `tool <cmd> [args]` becomes `tool <cmd> --config conf/tool.toml [args]`.

  [doc("Wrap `tool` with its config baked in")]
  [positional-arguments]
  tool cmd *args:
      shift; uv run tool {{ quote(cmd) }} --config conf/tool.toml "$@"
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
- **A body is a command or two; longer logic is a script file.** A recipe
  whose work takes more than a couple of commands, or carries any state from
  one line to the next — a variable, a conditional, a loop, `set -e` — moves
  that logic into a script file and calls it in one line. The recipe keeps its
  `[doc("…")]`, its parameters and that line; the rationale lives in the
  script, beside the logic it explains. A script runs, tests and lints without
  `just`; logic inlined in a justfile gets none of that, and without a shebang
  `just` runs each line in its own shell, so no state survives to the next
  line anyway.

  ```just
  [doc("Check the generated schema against the published one")]
  [positional-arguments]
  schema-check *args:
      uv run scripts/schema_check.py "$@"
  ```

  Never write a shebang body: it is that script, hidden in the justfile. A
  single command, or two independent ones on their own lines, stays a plain
  recipe body.
- **Group recipes with `[group("…")]` when concerns cluster.** A justfile whose
  public recipes span several distinct concerns (bootstrap, git, qa, codegen, …)
  carries `[group("…")]` so `just --list` prints them organized. Group names are
  lowercase single words, reused across repositories for recurring concerns
  (`qa`, `git`, `codegen`). Small single-concern files need no groups.

## Formatting

Format with `just --fmt --unstable --justfile <justfile>` before committing
any justfile change — through the shared `just::format` recipe where that
module is loaded. Don't fight the formatter: let it normalize spacing and
alignment, since a commit hook that checks formatting rejects anything else.
