# Proposal

## Why

The owner set two house rules. A `just` recipe is a short pointer to a
script: a body of more than a command or two does not inline its logic, it
runs a script file that holds the logic and its rationale. And scripts are
Python, not Bash: logic that would have been a multi-line shell body or a
standalone shell script is written as a Python script.

The just-rules texts prescribe the opposite today. `recipes.md` asks for a
`#!/usr/bin/env bash` shebang body with strict mode for any multi-line shell,
`arguments.md` shows a shebang body to `shift` a named parameter, and the
justfile checker enforces both: it reports a multi-line body without a
shebang, and a bash shebang body without `set -euo pipefail`. A rule stacked on
top would contradict them, so they are replaced.

## What Changes

- `just-rules` `references/recipes.md` drops the shebang-body bullet and
  states the new rule: a body is a command or two, one per line; longer logic,
  or any state carried between lines, moves into a script file the recipe
  calls in one line, keeping its `[doc("…")]` and parameters. No shebang body.
  Its `dbt` example becomes a one-line body.
- `references/arguments.md` forwards past a named parameter with `shift` and
  `{{ quote(cmd) }}` on one line, instead of a shebang body.
- `python-rules` gains `references/scripts.md`: a script is Python, not shell;
  shell remains only for a shim that must run before any interpreter can be
  assumed; a script's interface follows `cli.md`, whose `argparse` exception
  is exactly a script run by the bare interpreter with no environment to
  declare a dependency in. Its router indexes the topic and points at
  lint-rules for where loose scripts declare their dependencies.
  Its descriptions name scripts, so it loads before shell is written.
- The just-rules router points at python-rules for the language a recipe's
  script is written in, rather than copying the rule.
- The checker's `shebang` and `strict` rules give way to one `script` rule: a
  shebang body, or a body of more than two lines, is reported.
- The two `hooks/run-checker` shims say why they are POSIX `sh`.
- `just-rules` and `python-rules` move to 0.2.0.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `justfile-checking`: a body that holds a script is reported in place of a
  multi-line body without a shebang and a bash shebang body without strict
  mode.

## Impact

- `plugins/just-rules/skills/just/` (`SKILL.md`, `references/recipes.md`,
  `references/arguments.md`) and its manifests.
- `plugins/python-rules/skills/python/` (`SKILL.md`, new
  `references/scripts.md`) and its manifests.
- `plugins/*/hooks/run-checker` comments.
- `src/agent_plugins/justlint/` (`consts.py`, `rules.py`, `types.py`) and its
  tests and fixtures under `tests/justlint/`.
- A consumer's justfile with a shebang body, which passed before, now has one
  `script` finding per such recipe; in a session it surfaces only when the
  recipe is newly written, since the ratchet keys on recipe and rule.
