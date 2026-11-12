# Design

## Context

`scripts/check-private-names` is a bash script that three local hooks call
(`.pre-commit-config.yaml`, `language: script`): the staged-paths check, the
commit-msg check, and the self-test `tests/check-private-names.sh`. The
self-test drives the guard only as a black box: it builds a throwaway
repository, points `HOME` and `AGENT_PLUGINS_PRIVATE_NAMES` at synthetic
lists, and asserts on exit codes and finding text. The rest of the repository
is a uv-managed Python 3.12 package (`src/agent_plugins`) checked by ruff,
mypy and ty, with pytest suites under `tests/`. `tests/test_link_rules.py`
already tests a script under `scripts/` from pytest through `subprocess`.

## Goals / Non-Goals

**Goals:**

- Keep every observable output the same: arguments, exit codes, finding
  lines, and the stderr wording of each `die` message.
- Match with one regex engine, so a pattern means the same thing for paths,
  content, link targets, messages, identities, refs and tags.
- Make `--history` read each object once.

**Non-Goals:**

- No new modes, flags or output formats.
- No packaging as a `[project.scripts]` entry point (see Decision 1).
- No change to which objects history mode covers.

## Decisions

### 1. A stdlib-only script at the same path, not a package entry point

The guard stays the executable `scripts/check-private-names`, with
`#!/usr/bin/env python3`, and imports only the standard library.

*Why:* the hook has to run, and fail closed, in a fresh clone before
`uv sync`, and in a checkout whose virtual environment is broken. A
`language: script` hook needs nothing except `python3` on `PATH`, and the hook
entries stay as they are. *Alternative:* a module under `src/agent_plugins`
run through `uv run`. That ties the commit gate to resolving the lockfile, and
it would let a broken environment block every commit for reasons unrelated to
the list. Rejected.

The script checks `sys.version_info >= (3, 12)` first and exits 2 with a
message if the interpreter is older.

### 2. Python `re` as the pattern dialect, with ERE-only constructs rejected

Each list line is compiled on its own with `re.compile` (no flags), so an
invalid line can be reported by its number. The lines are then combined into
one alternation, `(?:p1)|(?:p2)|…`, that is used for every match. As with
`grep -o -f`, findings are the non-overlapping matches of that alternation,
found left to right.

Before compiling, each line is scanned for constructs that POSIX ERE (GNU
grep) and Python `re` both accept but read differently:

- POSIX bracket expressions `[:name:]`, `[.x.]`, `[=x=]` inside a bracket.
  Python reads these as plain character sets, and warns about only some of
  them.
- `\<` and `\>`. GNU grep reads them as word boundaries, Python as the literal
  characters `<` and `>`.
- `` \` `` and `\'`. GNU grep reads them as buffer anchors, Python as
  literals.

If any line holds one, the guard exits 2. The message gives the line number
and the construct's kind. It never includes the pattern, because the pattern
is itself a private name. Python also rejects unknown escapes of ASCII
letters (`\y`), so the remaining GNU-only escapes already fail compilation.

*Why:* the list lives outside the repository on each committer's machine. A
dialect change that silently changes what a line matches is the worst way this
guard can fail. Rejecting the constructs means each committer has to rewrite
any affected line once. *Alternatives:* (a) keep ERE by shelling out to
`grep -E`. That keeps one process per check, and keeps a second engine next
to `git grep`, which is most of what this port removes. (b) Translate ERE to
`re`. The translation would be a new, hard-to-test part of a security guard.
Both rejected.

Leftmost-longest (ERE) and leftmost-first (`re`) choice among alternatives can
report a different span for the same match. Whether a line matches does not
change, and only the reported text can. This is accepted, and it does not
affect the guard's verdict.

### 3. Content is decoded with `surrogateescape` and matched as text

Blob bytes are decoded as UTF-8 with `errors="surrogateescape"` and split on
`\n`, with line numbers starting at 1. Binary content therefore still matches
(as `grep -a` did), non-ASCII patterns match by character, and a finding
re-encodes to the original bytes when it is printed to stdout, which is
opened with `surrogateescape`. A trailing `\r` stays on the line, as it did
under grep.

### 4. One `git cat-file --batch` process feeds every object read

A small reader class owns one `git cat-file --batch` subprocess. It writes an
object name and reads back the header and the content. It serves the blobs in
the index (`git ls-files -s -z`), the blobs in each historical tree
(`git ls-tree -r -z <commit>`), link targets (mode `120000` entries, read from
their blob) and annotated tag objects. Content matching skips mode `120000`
and `160000` (gitlink) entries, as `git grep` did. A link is reported once, as
a link-target finding.

In history mode, a cache keyed by object id holds each blob's findings, so a
blob shared by many commits is read and matched once. Its findings are then
printed under each commit that contains it, which keeps the current output.
Each commit's `ls-tree` is cached by tree id for the same reason. Commit
identities and messages come from a single
`git log --all --format=…%x00` stream instead of one `git log -1` per commit.

All subprocesses run with an argument list (never `shell=True`), with
`--literal-pathspecs` where pathspecs are passed, and their exit codes are
checked. A failing git command exits 2, as `die` does now.

### 5. Output is kept byte-for-byte

The finding formats are fixed in the design, and the tests compare them
exactly:

| Source          | Line                                                      |
| --------------- | --------------------------------------------------------- |
| staged content  | `PATH:LINE: MATCH`                                        |
| staged path     | `PATH: path matches: MATCH`                               |
| staged link     | `PATH: link target matches: MATCH`                        |
| message         | `commit message:LINE: MATCH`                              |
| history content | `COMMIT: PATH:LINE: MATCH`                                |
| history path    | `COMMIT: PATH: path matches: MATCH`                       |
| history link    | `COMMIT: PATH: link target matches: MATCH`                |
| history log     | `COMMIT: identity and message line N: MATCH`              |
| ref name        | `ref REFNAME: path matches: MATCH`                        |
| tag object      | `REFNAME: tag object line N: MATCH`                       |

The history-log line numbers count the three-part block
`author …` / `committer …` / message body, as now. The closing stderr line and
every `check-private-names: …` diagnostic keep their wording.

Findings go to stdout in the order the bash guard printed them: paths, then
content, then links in staged mode, and per commit in `git rev-list --all`
order in history mode.

### 6. The bash self-test is the gate, then pytest replaces it

First, `tests/check-private-names.sh` runs unchanged against the Python guard
and must pass. Only then is it ported to `tests/test_check_private_names.py`,
which follows the `test_link_rules.py` pattern: a throwaway repository under
`tmp_path`, `HOME` and the variable pointed at synthetic lists, git config
isolated, and the guard run through `subprocess`. The pytest suite adds the
dialect-rejection and case-sensitivity scenarios, plus a check that the
verdict and findings match the bash guard on a fixture history. That check
runs once, against the bash script as it is in `git show HEAD:…` at port
time, and its expected output is then stored in the test. The self-test hook
switches to `uv run pytest tests/test_check_private_names.py`, triggered by
changes to the guard or its test.

## Risks / Trade-offs

- [A committer's list holds an ERE-only construct] → the guard exits 2 and
  names the line, so the committer finds out at their next commit instead of
  the guard quietly matching less.
- [A list line uses ERE syntax that `re` accepts with a different meaning and
  that is not in the rejected set] → none is known beyond those listed. The
  list format is documented as `re`, and the pytest suite includes a table of
  the rejected constructs that can be extended.
- [`python3` is missing or older than 3.12 on a committer's machine] → the
  hook cannot run, so the commit is blocked, which fails closed. The message
  names the requirement.
- [Reported match text differs for overlapping alternatives] → this is
  accepted (see Decision 2). The verdict does not change.
- [ruff, mypy or ty do not discover an extensionless file] → each tool's
  configuration names `scripts/check-private-names` explicitly, and a task
  checks that each tool really reports on it.

## Migration Plan

1. Before landing, each committer runs the new guard once with `--history`
   against their own list. Exit 2 with a POSIX-only message means the line it
   names needs rewriting (for example, `[[:alpha:]]` → `[A-Za-z]`).
2. The change lands as one commit, with the guard and its tests swapped
   together, so the hook never runs a half-ported guard.
3. Rollback: revert the commit. The list format is backwards-compatible in
   practice, because a list the new guard accepts uses no POSIX-only constructs
   and the remaining syntax means the same in ERE, apart from `re`-only
   additions such as `\d` or lookarounds, which a committer adds only after
   the port.
