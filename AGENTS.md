# agent-plugins

This repository publishes conventions plugins, and it is held to them itself.
A rule that does not hold here is not credible anywhere else.

## The rules that govern this repository

| You are changing… | Follow |
|-------------------|--------|
| Python under `src/`, `tests/` or `scripts/` | `plugins/python-rules` |
| A plugin under `plugins/`, or a marketplace manifest | `plugins/plugin-rules` |
| The lint configuration (`.pre-commit-config.yaml`, `pyproject.toml` tool sections, linter config files) | `plugins/lint-rules` |
| A justfile, should one appear | `plugins/just-rules` |

Read the rule files in the clone, not an installed copy: the clone is what is
being changed. The scripts in `scripts/` carry no `.py` suffix, so no path
glob attaches the Python rules to them; load the router yourself before
editing one.

## Deviating

- **A deviation is deliberate or it is a defect.** Where a rule does not fit,
  say why where it is broken: a comment beside the code, or the design of the
  change that introduced it. An unexplained deviation gets fixed, not copied.
- **A rule that can be checked is checked.** When a change relies on a rule a
  test, linter or hook could hold, add the check with it: tests for the
  plugin texts under `tests/plugins/`, linters for code. A rule held only by
  prose drifts.

## Changes

Changes are proposed, applied and archived through OpenSpec (`openspec/`).
The archive under `openspec/changes/archive/` is frozen: never edit it.
