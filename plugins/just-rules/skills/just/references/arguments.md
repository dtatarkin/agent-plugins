---
paths:
  - "**/justfile"
  - "**/*.just"
---

# Recipe arguments, and calls between recipes

- **Pass user arguments as positionals — never splat `{{ args }}` into a body.**
  `just` joins a variadic with spaces and splices it into the recipe line as
  *text*, which the shell then re-parses: any quoted argument (`-k 'a or b'`, a
  JMESPath `--query`, a path with spaces) is silently re-split or becomes a
  syntax error. A wrapper that forwards user args to a tool declares
  `[positional-arguments]` and passes `"$@"`:

  ```just
  [doc("Run a command in the project environment")]
  [positional-arguments]
  run *args:
      uv run "$@"
  ```

- **With a named parameter *before* the variadic**, `"$@"` would include it —
  use a shebang body and `shift`:

  ```just
  [positional-arguments]
  dbt cmd *args:
      #!/usr/bin/env bash
      set -euo pipefail
      cmd=$1; shift
      uv run dbt "$cmd" --project-dir dbt_proj "$@"
  ```

- **For a single named parameter interpolated into shell text**, escape it with
  `{{ quote(param) }}`.
- **Two spots where argument fidelity is impossible by construction**, so plain
  tokens only: a variadic forwarded through a **dependency call** (space-joined
  into one argument — see below), and args embedded in a quoted command string
  that a nested shell re-evaluates, e.g.
  `git submodule foreach "git fetch {{ args }}"`.

## Calling another recipe

- **Call another recipe as a dependency, not from the shell body.** When a
  recipe only forwards to another recipe, use the dependency-call syntax
  `recipe: (other "arg" …)` instead of a `just other arg …` body line. The call
  is resolved at parse time, spawns no nested `just` process, and reads as
  composition:

  ```just
  # prefer
  [doc("List the per-session keys in the sessions KV bucket")]
  sessions-ls: (nats "kv" "ls" "sessions")

  # not
  [doc("List the per-session keys in the sessions KV bucket")]
  sessions-ls:
      just nats kv ls sessions
  ```

  Fixed literal args pass cleanly — each literal is one argument. A **variadic**
  in a dependency call is space-joined into a single argument (`just` has no
  arrays), so quoting cannot survive that hop: `(run "pytest" args)` is fine
  only when the args are plain tokens.

- **Three cases keep the `just …` body form**, because a dependency call can't
  express them:
  - the value must be computed in the shell, e.g. inside a command substitution:
    `@git remote get-url $(just --justfile {{ source_file }} remote-name)`;
  - the target recipe is **out of scope** — a dependency resolves only recipes
    in this file plus its imported modules, so a module recipe that forwards to
    one the consuming project defines must call `just run …` in its body;
  - forwarded user args must keep their boundaries — the forwarder declares
    `[positional-arguments]` and calls
    `just --justfile {{ source_file }} run pytest "$@"`, so the args travel as
    real argv, never as re-parsed text.

  Reach across modules with `{{ module_file() }}`, and locate the caller with
  `{{ invocation_directory() }}`.

- **Thin tool wrappers keep that `run`/`*args` shape at every hop** — a wrapper
  over a wrapper stays positional:

  ```just
  [doc("Start an IPython shell in the project environment")]
  [positional-arguments]
  ipython *args:
      just --justfile {{ source_file }} run ipython "$@"
  ```
