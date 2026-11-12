# Proposal

## Why

The private-names guard is the only piece of this Python repository's logic
still written in bash. Most of its 243 lines are shell plumbing: NUL-separated
`git grep` output, `ls-files`/`ls-tree` records split with `IFS`, and a shield
against an exported `grep` function. That makes the guard hard to read and
review, and it is a safety guard, so it has to stay easy to review. Its
history mode also starts several processes for every commit, so the cost of
an audit grows with the length of the history.

## What Changes

- Rewrite `scripts/check-private-names` as a stdlib-only Python 3.12 program
  at the same path, still executable and still extensionless. The hook
  entries, the CLI (`[--] PATH...`, `--message FILE`, `--history`), the exit
  codes (0 clean, 1 findings, 2 cannot run) and every finding line stay
  byte-for-byte as they are.
- **BREAKING** (for the list, not the CLI): each line of the list becomes a
  Python `re` expression instead of a POSIX extended regular expression. A
  line that uses a construct the two dialects read differently, such as a
  POSIX bracket expression like `[[:alpha:]]`, is rejected as unusable
  (exit 2) instead of matching something else without warning. A committer
  whose list holds such a line rewrites that line once.
- All matching uses one engine. Staged and historical content is read through
  a single `git cat-file --batch` process and matched in Python. `git grep`
  and `grep` are no longer called.
- History mode reads each blob and tree once, however many commits share it,
  and reuses its findings.
- The bash self-test `tests/check-private-names.sh` first runs unchanged
  against the Python guard to show nothing changed. It is then replaced by a
  pytest suite, `tests/test_check_private_names.py`, which covers the same
  scenarios plus the new dialect rejection.
- The guard falls under the repository's Python checks (ruff, mypy, ty) and
  leaves shellcheck. Shell stays in the derived lint set because
  `scripts/link-rules` is bash.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `private-names-guard`: the list's pattern dialect changes from POSIX ERE to
  Python `re`, and a pattern written in a construct the dialects read
  differently now counts as an unusable list. No other requirement changes.

## Impact

- `scripts/check-private-names`: rewritten in Python.
- `tests/check-private-names.sh`: removed after the pytest port.
  `tests/test_check_private_names.py`: added.
- `.pre-commit-config.yaml`: the self-test hook runs the pytest suite, and the
  header comment no longer says the guard is a bash script.
- `README.md`: the list-format paragraph names Python `re` and the rejected
  POSIX-only constructs.
- `pyproject.toml`: ruff, mypy and ty include the extensionless guard, if
  their file discovery does not already pick it up.
- Committers: `python3` 3.12 or later must be on `PATH` when committing. The
  guard needs no virtual environment, so a fresh clone can commit before
  `uv sync`. Without `python3` the hook cannot run, and the commit is blocked.
- Each committer's private list (held outside the repository) may need a
  one-time rewrite of POSIX bracket expressions.
