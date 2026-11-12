# Tasks

## 1. Port the script behind the existing black-box tests

- [x] 1.1 Rewrite `scripts/link-rules` as a stdlib-only Python script at the same path. It keeps its
  `#!/usr/bin/env python3` shebang, stays executable and extensionless, and keeps the header docstring giving usage
  and exit codes. Follow design Decisions 1, 2 and 4:
  - the version check comes first;
  - only syntax Python 3.9 parses;
  - one function per bash function, then `main(argv) -> int`;
  - hand-parsed arguments, no argparse;
  - `os.readlink` with a literal prefix test for ownership, `samefile` for the `-ef` test;
  - unlink-then-symlink for an own link;
  - sorted globbing.

  Every stdout line and every `link-rules: …` stderr message stays byte-identical to the bash script. Verify:
  `git ls-files -s scripts/link-rules` still shows mode `100755`, and `scripts/link-rules --help` prints the same
  text as `git show HEAD:scripts/link-rules | bash -s -- --help`.
- [x] 1.2 Run the existing suite unchanged against the port. Verify: `uv run pytest tests/test_link_rules.py` passes
  with no edit to the test file.
- [x] 1.3 Parity check against the bash script. Build one fixture rules directory containing:
  - own links, live and stale;
  - a foreign regular file;
  - a foreign link pointing elsewhere;
  - a foreign link resolving to a rule file;
  - a dangling foreign link.

  Run both scripts on a copy of it for `""`, `<plugin>`, `--unlink`, `--unlink <plugin>`, an unknown plugin, an
  unknown option and `--help`. The bash script is run from `git show HEAD:scripts/link-rules`, placed in a copy of
  the clone. Verify: exit codes, stdout, stderr and the resulting directory listings (names and link targets) are
  identical.

## 2. Tests the port adds

- [x] 2.0 Add `shape_violations` to `tests/plugins/test_rule_frontmatter.py` (design Decision 3,
  `rule-file-frontmatter` delta). Apply it to every rule file read with its line endings kept, and add one rejection
  test per delta scenario: a delimiter with a trailing space, a CRLF delimiter, an unclosed frontmatter, an indented
  `paths:`, and an unconstrained file with no frontmatter. Verify: `uv run pytest tests/plugins/test_rule_frontmatter.py`
  passes on the real tree, and each rejection test fails when its branch of `shape_violations` is removed.
- [x] 2.1 Add the parametrized detection-agreement test (design Decision 3) to `tests/test_link_rules.py`. It covers
  these cases:
  - no frontmatter;
  - frontmatter without `paths:`;
  - `paths:` after the closing `---`;
  - `paths:` followed by other keys;
  - an indented `paths:`;
  - CRLF line endings;
  - a trailing space on a delimiter;
  - an unclosed frontmatter.

  For each case the test asserts the script links the file exactly when `declares_paths` accepts its text, unless
  `shape_violations` fails the file. Verify: the test passes, and it fails when `is_scoped` is changed to accept
  `paths:` anywhere in the file.
- [x] 2.2 Add `test_the_interpreter_is_too_old`, which runs the script through a `python3` shim first on `PATH` (design
  Decision 6). Verify: it asserts exit 2, the message `link-rules: needs python3 3.12 or later` on stderr, and no
  rules directory. It passes, and it fails when the version check is removed.
- [x] 2.3 Add `test_the_script_parses_as_python_39`, which calls `ast.parse(source, feature_version=(3, 9))` on the
  script. Verify: it passes, and it fails when a `match` statement is added to a scratch copy.

## 3. Tooling and documentation

- [x] 3.1 Bring the script under the Python checks:
  - check it with mypy in a hook of its own, `mypy-link-rules`, because mypy's `files` cannot hold two suffix-less
    scripts (design Decision 5);
  - add it to the `ty` hook entry in `.pre-commit-config.yaml`;
  - confirm ruff and ruff-format report on it through pre-commit's shebang detection, and name it in
    configuration if they do not.

  Verify: a deliberate type error and a lint error in a scratch copy make each of ruff, ruff-format, mypy and ty
  fail. The real file passes all four (`prek run --files scripts/link-rules`).
- [x] 3.2 Rewrite the `.pre-commit-config.yaml` header comment so the shell set is attributed to the plugins'
  `hooks/run-checker` scripts, not `scripts/link-rules`. Verify: `prek run shellcheck --all-files` still runs and
  passes on both `run-checker` files.
- [x] 3.3 In the README section "Attach rules on touch", state that the script needs `python3` 3.12 or later on `PATH`
  and no virtual environment. Verify: the `rumdl` and `lychee` hooks pass on `README.md`, and the sentence matches the
  modified spec requirement.

## 4. Integration

- [x] 4.1 Run the full hook suite and test suite. Verify: `prek run --all-files` and `uv run pytest` both pass.
- [x] 4.2 Converge the committer's own rules directory, which holds links the bash script made. Run
  `scripts/link-rules` with the real configuration directory. Verify: the run prints nothing and exits 0. Then
  `scripts/link-rules --unlink just-rules && scripts/link-rules just-rules` prints the same names, unlinked and then
  relinked.

## Workflow follow-up

- Land groups 1–3 as one commit, so the hooks never see a half-ported script.
- Archive the change with `/opsx:archive` after review.
