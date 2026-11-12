# Design

## Context

See proposal.md for why. The current state:

- `scripts/link-rules` is a bash script of about 220 lines. Its behaviour is
  fixed by the `rule-file-linking` spec and by the archived design
  `2026-11-12-colleague-rule-linking`:
  - D2: the root is the script's own clone, resolved physically.
  - D3: line-based scoped detection.
  - D4: ownership is the literal target prefix.
  - D5: per-name policy.
  - D6: prune before linking.
  - D7: exit codes.
  - D8: output.
- `tests/test_link_rules.py` drives the script only as a black box. A fixture
  copies `scripts/link-rules` into a throwaway repository under `tmp_path` and
  runs it through `subprocess` with `HOME` and `CLAUDE_CONFIG_DIR` pointed
  into `tmp_path`. `test_the_real_tree` runs the real script and holds its
  links equal to the files `declares_paths` accepts. `declares_paths` is the
  contract test's YAML-based detection in `tests/plugins/test_rule_frontmatter.py`.
- `scripts/check-private-names` is the model this port follows:
  - `#!/usr/bin/env python3`, executable, no file suffix, standard library
    only;
  - a `sys.version_info < (3, 12)` check at the top that exits 2;
  - named in mypy's `files` and in the `ty` hook entry.
- The shell signal that keeps shellcheck in the lint set does not depend on
  this script. `plugins/*/hooks/run-checker` are executable `#!/bin/sh` files.

## Goals / Non-Goals

**Goals:**

- Behaviour is identical to the bash script for every spec scenario and every
  existing test. Each stderr diagnostic keeps its wording.
- The existing test file passes unchanged against the port before anything is
  added to it.

**Non-Goals:**

- No new flags or modes. No change to which files are linked, how links are
  named, or how ownership is decided.
- No packaging as a `[project.scripts]` entry point. The archived design's D1
  still holds: the installed package ships no `plugins/`.
- No sharing of code between the script and the contract test (see
  Decision 3).

## Decisions

### 1. A stdlib-only script at the same path

The script stays the executable `scripts/link-rules`, now with
`#!/usr/bin/env python3`. It imports only the standard library. It runs from
a clone with no virtual environment, as the bash script did.

*Alternative:* a module under `src/agent_plugins` that `uv run` calls. That
makes a one-off opt-in step depend on resolving the lockfile, and it still
needs the clone. Rejected.

### 2. The version check runs before anything else, and the file parses on old interpreters

The first statement after the imports is
`if sys.version_info < (3, 12): print(...); sys.exit(2)`. The message is
`link-rules: needs python3 3.12 or later` on stderr.

The check is only useful if an old interpreter can parse the file and reach
it. So the script uses no syntax newer than what Python 3.9 parses: no
`match`, no PEP 695 generics or `type` aliases, no `except*`. Stock macOS
ships 3.9, which makes it the realistic old interpreter. Annotations such as
`str | None` parse on 3.9. Definitions after the check never run there, so
their annotations are never evaluated. ruff's `target-version` stays `py312`
for the rest of the repository. A test pins the parse constraint (see
Decision 6).

*Alternative:* no check, and let an old interpreter fail wherever it fails.
That would mean a traceback, or wrong behaviour from a missing method, instead
of exit 2 with a clear message. Rejected.

### 3. Detection stays line-based, and the tests hold it to the contract

`is_scoped(path)` reads lines, not YAML. The file is scoped when its first
line is exactly `---` and a line starting with `paths:` comes before the next
line that is exactly `---`. This is D3 from the archived design, unchanged.

The ask was to share the detection with `declares_paths`. It cannot be shared
in either direction:

- the script must stay stdlib-only, so it cannot import a YAML parser;
- the contract test must stay YAML-based, because that is what makes it a
  contract.

The two are held together by tests instead:

- `test_the_real_tree` already requires the linked set to equal the set
  `declares_paths` accepts over the real tree.
- A new parametrized test builds one rule file per edge case in the fixture
  repository. The cases:
  - no frontmatter;
  - frontmatter without `paths:`;
  - `paths:` after the closing `---`;
  - a `paths:` key followed by other keys;
  - an indented `paths:`;
  - a CRLF frontmatter;
  - a trailing space on a delimiter;
  - an unclosed frontmatter.

  For each case the test asserts one of two things: the script links the file
  exactly when `declares_paths` accepts its text, or the contract's shape
  check fails the file.

Running these cases showed four real disagreements. The contract called a
file scoped and the script would not link it when `paths:` was indented, the
frontmatter used CRLF, or a delimiter carried a trailing space. The script
linked a file the contract ignored when its frontmatter was never closed.
The bash script had the same gaps; nothing tested them.

The fix tightens the contract, not the script (`rule-file-frontmatter` delta,
"A rule file's frontmatter has one written shape"). The contract test gains
`shape_violations(raw)`, applied to every rule file read with its line endings
intact. When the first line strips to `---`, the opening line must be exactly
`---`. The first later line that strips to `---` must exist and be exactly
`---`. When `declares_paths` holds, a line between them must start with
`paths:`.

On a file that passes, the script's region (up to the first exact `---`) is
the YAML reader's region (up to the first line that strips to `---`). The
script's `paths:` line is then the YAML top-level key, so the two verdicts
agree.

*Alternative:* loosen the script to strip delimiters and accept an indented
key. The script would then differ from the bash version on these files, and
it still would not match YAML in general. The contract change keeps the
script byte-for-byte and narrows the files to the shape every reader agrees
on. Chosen by the owner.

### 4. Structure: small functions over pathlib, one exit point

The program maps one-to-one onto the bash functions: `usage`, `die`, `warn`,
`is_scoped`, `is_own`, `in_plugins`, `prune`, `link_one`, `link_candidate`,
`link_files`, `unlink_all`, then `main(argv) -> int`, with
`sys.exit(main(sys.argv[1:]))`.

- **Root.** `os.path.realpath(os.path.abspath(<script dir>/..))`: the `..`
  is taken lexically and the result is then resolved physically, as
  `cd "$(dirname "$0")/.." && pwd -P` does (D2).
- **Ownership.** `os.readlink(link)` gives the literal, unresolved target.
  The link is owned when the target string starts with `<plugins_dir>/`. This
  is exactly the bash `case "${plugins_dir}"/*`. `PurePath.is_relative_to`
  was the first plan, but it normalizes `//` and `/./` segments, which the
  bash comparison does not. Like the bash, the check does not resolve `..`.
- **Paths as strings.** Paths are joined by string concatenation
  (`f"{dest}/{name}"`), not `os.path.join`, so every message naming a path
  matches the bash output even when `CLAUDE_CONFIG_DIR` ends with `/`.
- **Same file.** `os.path.samefile`, which is the bash `-ef` test. Its
  `OSError` on a dangling link counts as "not the same file".
- **Linking.** Only an own link, or a missing name, is (re)linked. A stale own
  link is first removed with `os.unlink`, then created with
  `os.symlink(file, link)`. This is the observable effect of `ln -sfn` and
  needs no temporary name.
- **Glob order.** `sorted(glob.glob(...))` over an escaped prefix (`glob`
  skips dot-files, as the shell does, while `pathlib.glob` would not), so
  `linked …` lines come out in the same order as bash's sorted glob expansion
  (C locale ordering under the tests' environment).
- **Failures.** A failing `mkdir`, `symlink` or `unlink` is caught as
  `OSError` and becomes `die(...)` with the bash message, exiting 2 (the
  archived design's A6).
- **Exit status.** `link_one` returns whether it skipped a name, and `main`
  returns 1 when any was skipped, which is the bash `status=1`.

*Alternative:* argparse. It would change the usage text, the error wording
and the exit code for unknown options (argparse exits 2 but prints its own
messages), and `-h` would print a different help. Hand-parsing the three
forms keeps every message byte-identical. Rejected.

### 5. Tooling coverage

- **mypy.** The script is checked by a hook of its own, `mypy-link-rules`, with
  the entry `uv run mypy scripts/link-rules`. It runs under the same
  configuration. The first plan was to add the script to mypy's `files`, next
  to the guard. That fails: mypy names every suffix-less script `__main__`,
  so two of them in one run are a duplicate module and checking stops.
  `lint-lint check` accepts the extra hook as project-owned.
- **ty.** The hook entry becomes
  `uv run ty check src tests scripts/check-private-names scripts/link-rules`.
- **ruff and ruff-format.** They see the file through pre-commit's `types`
  detection, because identify classifies a `python3` shebang as python.
  A task confirms this, as the guard's port did.
- **shellcheck.** It stops seeing this file but keeps its hook, because the
  `run-checker` scripts are still shell. The `.pre-commit-config.yaml`
  header's shell-set reason is rewritten to cite them.

### 6. Tests: unchanged first, then extended

1. Run `tests/test_link_rules.py` unchanged against the port. It must pass
   before any test is added.
2. Add the edge-case detection table (Decision 3).
3. Add `test_the_interpreter_is_too_old`. It puts a `python3` shim first on
   `PATH`. The shim execs the real interpreter on a small bootstrap that sets
   `sys.version_info` to `(3, 11, 0, "final", 0)` and then runs the script
   with `runpy.run_path(..., run_name="__main__")`. The test asserts exit 2,
   the message, and an untouched rules directory.
4. Add `test_the_script_parses_as_python_39`. It calls
   `ast.parse(source, feature_version=(3, 9))` on the script text.

## Risks / Trade-offs

- [A user has only stock macOS `python3` 3.9] → the script exits 2 with a
  message naming the requirement, and changes nothing. README states the
  requirement. This drops a promise of the archived design (D9), as the
  proposal says.
- [`linked` line order differs from bash under a non-C locale] → bash sorts
  its glob by the locale's collation and Python sorts by code point. Plugin
  and topic names are lowercase kebab-case ASCII, where the two orders agree.
  No test pins cross-locale order.
- [A target with `..` segments] → ownership is a literal prefix test, as in
  bash, so a target such as `<plugins>/../elsewhere` counts as owned. This is
  unchanged behaviour and is not tightened here.
- [ruff skips the extensionless file] → a task checks that ruff really
  reports on it, and names the file in configuration if it does not.

## Migration Plan

1. Land the port, the tests and the configuration as one commit, so the
   hooks never see a half-ported script.
2. Users need do nothing beyond having `python3` 3.12 or later. Existing links
   are owned by literal target prefix, which does not change, so the Python
   script prunes and unlinks links the bash script made.
3. Rollback: revert the commit. Links made by either version are
   interchangeable.
