# Proposal

## Why

This repository was bootstrapped to publish agent plugins that carry coding conventions, and its gates now hold. The
plugins are still kept in a private source repository, beside material that cannot be published. Until they and the
two checkers that enforce `lint-rules` and `just-rules` live here with their tests and their specs, nothing can be
installed from this repository. The source repository also cannot drop its copies, and the later steps can't start:
other hosts, colleague rule linking, an authoring plugin and going public.

## What Changes

- Import eight conventions plugins as a plain copy with no history: `python-rules`, `logging-rules`, `lint-rules`,
  `clickhouse-rules`, `django-rules`, `just-rules`, `metabase-rules` and `redis-rules`. Each keeps its two manifests,
  its router skill and its topic files under `skills/<domain>/references/`. Both checker plugins keep their hooks.
- Import the two checkers, `lint-lint` and `just-lint`, as one Python package of this repository's own. The
  distribution is `agent-plugins` and the import package is `agent_plugins`, with subpackages `lintlint` and
  `justlint`. The console scripts keep their names. The repository root becomes an installable package:
  `uv tool install git+https://github.com/dtatarkin/agent-plugins`.
- Import the checkers' test suites and fixtures, and the plugin tests that guard what moves:
  - `test_lint_hook_filters.py`
  - `test_hook_guard.py`
  - `test_portable_manifests.py`
  - `test_rule_frontmatter.py`
  - `test_hook_manifests.py`

  Prose that names a private repository, a machine, a linking step or wiring is reworded. Identifiers stay.
- The missing-checker notice the two hook guards show at session start now gives this repository's install line, in
  place of a generic hint. `lint-rules` and `just-rules` get a patch version bump.
- The repository converges on the Python lint set its new signals derive. Its own audit, run in its test suite, then
  holds the configuration to the standard.
- The Claude Code marketplace lists the eight. The README gives the Claude Code install and the checkers' install. The
  Codex marketplace file stays empty.
- Not in this change:
  - the Codex and Antigravity listings and their install lines;
  - CI;
  - a colleague rule-linking script;
  - the authoring plugin;
  - any plugin beyond the eight;
  - pushing;
  - making the repository public.

## Capabilities

### New Capabilities

- `lint-standards`: the house lint standard as a contract. It covers:
  - which checks a repository runs, derived from its signals;
  - one tool per concern;
  - pins under a release-age cooldown;
  - how a local hook finds its tool;
  - when the rules reach an agent and what they let it change;
  - when a whole repository is brought into line, this repository first.
- `lint-checking`: `lint-lint`, which audits a repository's lint configuration against the standard and, inside agent
  sessions, reports only the findings an edit introduced. It degrades to silence with one notice when it is not
  installed.
- `justfile-checking`: `just-lint`, which does the same for the mechanically checkable `just-rules` conventions.
- `agent-rules-authoring`: how a rules plugin is built:
  - one canonical copy of each rule;
  - tool-neutral, consumer-free prose;
  - one thin router skill per domain;
  - brief topic files;
  - a portable Agent Plugins manifest held equal to the Claude one;
  - hooks in exec form that resolve to a plugin script or a console script of this repository;
  - manifests that parse before commit.
- `rule-file-frontmatter`: the contract a topic file meets when it declares the paths it governs with `paths:`
  frontmatter. It holds a non-empty glob list and nothing else in its frontmatter, imports nothing, and among a
  plugin's scoped files one states the rules' scope.

### Modified Capabilities

None. `private-names-guard` is unchanged; every imported file must pass it.

## Impact

- New trees:
  - `plugins/<eight>/`
  - `src/agent_plugins/`
  - `tests/` (Python), beside the existing `tests/check-private-names.sh`
- New root files: `pyproject.toml`, `uv.lock`, `.gitignore`.
- Changed: `.pre-commit-config.yaml` (the Python set), `_typos.toml`, `.claude-plugin/marketplace.json`, `README.md`.
- Runtime dependencies of the package: `typer`, `ruamel.yaml`. Development: `ruff`, `mypy`, `ty`, `pytest`,
  `rust-just`. Committers now also need `uv`.
- A ratchet baseline is kept under the plugin's data directory. It starts fresh for anyone who installs from this
  marketplace.
- The repository is still private, so the GitHub install lines are exercised only once it goes public. Until then the
  checkers are verified from the working tree.
