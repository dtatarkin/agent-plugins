# Tasks

## 1. Port the guard behind the existing black-box test

- [x] 1.1 Rewrite `scripts/check-private-names` as a stdlib-only Python 3.12 script at the same path (`#!/usr/bin/env
  python3`, still executable, extensionless). It covers list loading, the fail-closed `die` paths, the 3.12 version
  check, and argument dispatch for `[--] PATH...`, `--message FILE` and `--history`, with the same diagnostics.
  Verify: `AGENT_PLUGINS_PRIVATE_NAMES=/nonexistent scripts/check-private-names` exits 2 with the same message as the
  bash version.
- [x] 1.2 Implement pattern loading per design Decision 2: compile each line separately, combine the lines into one
  alternation, and reject the POSIX-only constructs with exit 2 and a message that gives the line number and kind but
  never the pattern. Verify: synthetic lists holding `[[:alpha:]]`, `[[.a.]]`, `[[=a=]]`, `\<`, `\>`, `` \` `` and
  `\'` each exit 2 in all three modes, and the pattern text does not appear in the output.
- [x] 1.3 Implement the `git cat-file --batch` object reader and staged mode (paths, index content decoded with
  `surrogateescape`, link targets, gitlinks skipped for content) per design Decisions 3 and 4. Verify:
  `tests/check-private-names.sh` passes unchanged through its staged-mode assertions.
- [x] 1.4 Implement `--message` (scissors line and `#` lines dropped, original line numbers kept). Verify: the message
  assertions of `tests/check-private-names.sh` pass.
- [x] 1.5 Implement `--history` with the blob and tree caches and a single `git log --all` stream for identities and
  messages, plus ref names and annotated tag objects, in the output order of design Decision 5. Verify: the whole of
  `tests/check-private-names.sh` passes unchanged against the Python guard.
- [x] 1.6 Parity check: on a fixture repository with findings of every row of the design's output table (including
  binary content, a CRLF line and two commits sharing a blob), run the bash guard from `git show
  HEAD:scripts/check-private-names` and the new guard in all three modes. Verify: exit codes and stdout are
  byte-identical, and stderr differs only where design Decision 2 allows (none is expected for this fixture).
- [x] 1.7 Bring the script under the Python checks: confirm that ruff, ruff-format, mypy (strict) and ty each report
  on `scripts/check-private-names`, and name the file in their configuration in `pyproject.toml` or in the hook
  entries where one does not. Verify: inserting a deliberate type error and a lint error into a scratch copy makes
  each tool fail, and the real file passes all four.

## 2. Replace the bash self-test with pytest

- [x] 2.1 Port every assertion of `tests/check-private-names.sh` to `tests/test_check_private_names.py`, following the
  `tests/test_link_rules.py` pattern (throwaway repository under `tmp_path`, isolated `HOME`,
  `GIT_CONFIG_GLOBAL=/dev/null`, git's local environment variables unset, synthetic `zzq-` names only). Verify: `uv
  run pytest tests/test_check_private_names.py` passes, and every scenario name in the bash test has a matching test.
- [x] 2.2 Add tests for the modified spec scenarios: case-sensitive matching, plus a parametrized table of the
  POSIX-only constructs that are rejected in all three modes, without the pattern text in the output. Store the parity
  fixture's expected stdout from 1.6 as a test. Verify: the new tests pass, and each fails when the corresponding
  check in the guard is disabled.
- [x] 2.3 Point the `check-private-names-selftest` hook at `uv run pytest tests/test_check_private_names.py` (files:
  the guard and the new test), delete `tests/check-private-names.sh`, and update the config header comment so it no
  longer calls the guard a bash script. Verify: `prek run check-private-names-selftest --all-files` passes, and
  `shellcheck` still covers `scripts/link-rules`.

## 3. Spec-facing documentation

- [x] 3.1 Update `README.md` (the list-format paragraph near line 111) to say each line is a Python `re` expression,
  matched case-sensitively, and to list the rejected POSIX-only constructs with their rewrites (for example,
  `[[:alpha:]]` → `[A-Za-z]`). Verify: `rumdl` and `lychee` hooks pass on `README.md`, and the text matches the delta
  spec.

## 4. Integration

- [x] 4.1 Run the full hook suite and the test suite: `prek run --all-files` and `uv run pytest`. Verify: both pass,
  and the staged-path hook runs the Python guard on every file.
- [x] 4.2 Run `scripts/check-private-names --history` with the committer's own list, and compare its runtime with the
  bash guard's on this repository. Verify: exit 0 (or exit 2 naming a POSIX-only line, which the committer rewrites
  before landing), and the run time is recorded in the commit message body.

## Workflow follow-up

- Land groups 1–3 as one commit so the hook never runs a half-ported guard.
- Archive the change with `/opsx:archive` after review.
