# Proposal

## Why

`scripts/link-rules` is the last piece of this repository's own tooling
written in bash. Most of it is shell plumbing:

- `case` globs that decide link ownership,
- guards for globs that match nothing,
- an `awk` program that detects `paths:` frontmatter,
- `${1+"$@"}` forwarding of arguments.

None of this is what the script is about, and it makes the code harder to
review. The private-names guard was just ported to stdlib-only Python for the
same reason (archived change `port-private-names-guard-to-python`). That port
set the pattern this change follows.

## What Changes

- Rewrite `scripts/link-rules` as a stdlib-only Python 3.12 program at the
  same path, still executable and still extensionless. These stay exactly as
  they are:
  - the CLI: `[PLUGIN...]`, `--unlink [PLUGIN...]`, `-h | --help`;
  - the exit codes: 0 done, 1 a name was skipped, 2 cannot run;
  - the `linked <name>` / `unlinked <name>` lines on stdout;
  - every `link-rules: …` diagnostic on stderr.
- The script checks the interpreter version first. Under an older `python3` it
  exits 2 with a message naming the requirement, as the guard does.
- Scoped-file detection stays line-based and dependency-free: first line
  `---`, then a `paths:` line before the closing `---`. It is not changed to
  parse YAML. The existing real-tree test already holds the linked set equal to
  the files the contract test's YAML-based `declares_paths` accepts. A table
  of edge-case frontmatters is added, holding the two detections to the same
  verdict where they could drift.
- The script falls under the repository's Python checks (ruff, ruff-format,
  mypy, ty). shellcheck stays: the plugins' `hooks/run-checker` scripts are
  still shell, so the shell signal and its hook remain.
- `tests/test_link_rules.py` keeps driving the script as a black box through
  `subprocess`. It runs unchanged against the port first, then gains the
  version-check and detection-agreement tests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rule-file-linking`: the requirement "Linking is opt-in and Claude Code only"
  gains the runtime the script needs: `python3` 3.12 or later on `PATH`.
  Without it, the script exits 2 and changes nothing. No other requirement
  changes.
- `rule-file-frontmatter`: a new requirement fixes how frontmatter is written:
  the opening and closing `---` lines carry nothing else, the block is closed,
  and `paths:` starts its line. Testing the edge cases showed the script's
  line-based detection and the contract's YAML reading disagree on three
  shapes the contract accepted and on one it ignored. A rule file in any of
  those shapes now fails the tests, so the two agree on every file that
  passes.

## Impact

- `scripts/link-rules`: rewritten in Python.
- `tests/test_link_rules.py`: new tests for the version check and for
  detection agreement. The existing scenarios stay.
- `tests/plugins/test_rule_frontmatter.py`: the shape check over every rule
  file, with a rejection test per shape.
- `.pre-commit-config.yaml`: the `ty` hook entry names `scripts/link-rules`,
  and a `mypy-link-rules` hook runs mypy on it alone, because mypy cannot check
  two suffix-less scripts in one run.
  The header comment stops citing `scripts/link-rules` as the reason for the
  shell set and cites the plugins' `run-checker` scripts instead.
- `README.md`: the "Attach rules on touch" section states the `python3` 3.12
  requirement.
- Users who link rules: `python3` 3.12 or later must be on `PATH`. The script
  needs no virtual environment and no `uv sync`. Stock macOS `python3`
  (3.9) is no longer enough. This drops the old design's promise that the
  script runs with stock tools.
