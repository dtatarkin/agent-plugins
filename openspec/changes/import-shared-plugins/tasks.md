# Tasks

`$SOURCE` is the source repository's clone, given in the applier's brief (design.md, A1). It is read and never written,
and its name is never written here. Searches use `git grep` or `command grep`. Each section ends in commits on the
current branch with every hook run, the private-names guard included. Nothing is pushed.

## 1. Checker package, its tests, and the Python lint set

- [x] 1.1 Write `pyproject.toml` as design.md D1 and D3 give it, `.gitignore` as D11 gives it, and
  `src/agent_plugins/__init__.py` (a one-line module docstring naming the two checkers). Run `uv lock` and `uv sync`.
  Verify:
  - `uv.lock` exists and `uv run python -c "import agent_plugins"` succeeds;
  - `git status --porcelain` lists nothing under `.idea/` or `.venv/`.
- [x] 1.2 Copy the source package's `lintlint/` and `justlint/` (the directories `$SOURCE/src/*/lintlint` and
  `$SOURCE/src/*/justlint`, without `__pycache__`) to `src/agent_plugins/`. Rewrite every reference to the source
  package's prefix to `agent_plugins` as D2 says, and apply D6's docstring rewording to `justlint/dump.py` and both
  `entry.py`. Verify:
  - `command grep -rnE '\b[a-z]+_ai\.' src/` finds nothing;
  - `uv run lint-lint --help` and `uv run just-lint --help` both print their usage;
  - `uv run mypy` passes.
- [x] 1.3 Copy the source's `tests/__init__.py`, `tests/fixtures/__init__.py`, `tests/fixtures/{lintlint,justlint}/` and
  `tests/{lintlint,justlint}/`, with their `data/` trees and keeping file modes. Leave out both `test_citations.py`
  (they come with the plugins in section 2, D5). Apply D2's rename and D6's `test_entry.py` changes. Write
  `tests/conftest.py` registering only `tests.fixtures.lintlint.trees` and `tests.fixtures.justlint.trees`, keeping the
  source's docstring. Verify:
  - `command grep -rnE '\b[a-z]+_ai\.' tests/` finds nothing;
  - `uv run pytest tests/lintlint tests/justlint --deselect tests/lintlint/test_acceptance.py` passes.
- [x] 1.4 Converge `.pre-commit-config.yaml` on the Python set and adjust `_typos.toml` as design.md D4 says. Pin new
  repositories with `prek update --cooldown-days 7 --repo-exclude-tag https://github.com/crate-ci/typos=v1`, and check
  each new `rev:` is a tag at least seven days old. Then `prek install`. Verify:
  - `uvx pre-commit validate-config` passes;
  - `uv run lint-lint check .` reports nothing;
  - `uv run pytest tests/lintlint/test_acceptance.py` passes.
- [x] 1.5 Stage the section's files (`git add` by path), run `prek run typos --all-files` alone, and read the whole
  `git diff`. Revert each rewrite of a deliberate spelling and allowlist it in `_typos.toml` (design.md, Risks). Then
  run `prek run --all-files` and fix each finding, re-reading every markdown fix. Verify:
  - a second `prek run --all-files` changes nothing and passes;
  - `uv run pytest` passes.
- [x] 1.6 Commit the section as two commits. First the configuration and packaging: `pyproject.toml`, `uv.lock`,
  `.gitignore`, `src/agent_plugins/__init__.py`, `.pre-commit-config.yaml` and `_typos.toml`, as
  `lint: converge on the Python set`. Then the subpackages and tests, as `src: add the lint-lint and just-lint checkers`.
  If an all-files run reformatted a file this section did not add, commit that rewrite first, on its own, and list its
  full hash in `.git-blame-ignore-revs` with `blame.ignoreRevsFile` set. Verify:
  - every hook reports passed on each commit;
  - `git status --porcelain` is empty apart from `.idea/` if it is not yet ignored.

## 2. The eight plugins, their tests, marketplace and README

- [ ] 2.1 Copy `$SOURCE/plugins/<name>/` for `python-rules`, `logging-rules`, `lint-rules`, `clickhouse-rules`,
  `django-rules`, `just-rules`, `metabase-rules` and `redis-rules` into `plugins/`, keeping modes. Verify:
  - `git ls-files -s` (after staging) shows both `hooks/run-checker` as `100755`;
  - `diff -r` against the source shows no difference before the next task.
- [ ] 2.2 Write design.md D7's install line into both `plugins/{lint,just}-rules/hooks/run-checker`, and bump
  `lint-rules` to 0.4.1 and `just-rules` to 0.1.1 in both manifests of each. Verify:
  - `cmp` of the two scripts reports them identical;
  - `printf '{}' | env PATH=/usr/bin:/bin plugins/lint-rules/hooks/run-checker --notice zz-absent-tool lint-rules |
    python3 -m json.tool` parses and shows the URL;
  - `jq .version` agrees across each plugin's two manifests.
- [ ] 2.3 Copy the source's `tests/plugins/__init__.py`, `test_lint_hook_filters.py`, `test_hook_guard.py`,
  `test_portable_manifests.py`, `test_rule_frontmatter.py` and `test_hook_manifests.py`. Also copy
  `tests/lintlint/test_citations.py` and `tests/justlint/test_citations.py`. Apply D2's rename. Reword
  `test_rule_frontmatter.py`'s docstrings as D6 says, and add the URL assertion to `test_hook_guard.py` (D7). Verify:
  - `command grep -rnE '\b[a-z]+_ai\.|link-rules|link recipe' tests/plugins/` finds nothing;
  - `uv run pytest tests/plugins tests/lintlint/test_citations.py tests/justlint/test_citations.py` passes;
  - with the notice line reverted to the generic hint, the URL assertion fails (then restore it).
- [ ] 2.4 List the eight in `.claude-plugin/marketplace.json` as design.md D8 gives the entries. Verify:
  - `jq '.plugins | length'` prints 8, and each `source` names an existing directory;
  - `claude plugin validate --strict .` passes, and so does `claude plugin validate --strict plugins/<name>` for each
    of the eight. If the CLI rejects something the source accepted, record it under design.md *Risks* and stop.
- [ ] 2.5 Rewrite `README.md`. Replace the "holds no plugin yet" paragraph with:
  - a list of the eight plugins, one line each;
  - the Claude Code install (`/plugin marketplace add dtatarkin/agent-plugins`, then
    `/plugin install <name>@agent-plugins`);
  - the checkers' install (`uv tool install git+https://github.com/dtatarkin/agent-plugins`), with a sentence that
    `lint-rules` and `just-rules` run without it and say so at session start;
  - a development line (`uv sync`, `uv run pytest`).

  Keep the hook section. Verify:
  - `prek run rumdl-check --files README.md` passes;
  - the install line matches the one in both `run-checker` scripts character for character.
- [ ] 2.6 Stage the section's files, run `prek run typos --all-files` alone and read the whole `git diff`, as in 1.5.
  Then run `prek run --all-files`, re-reading every markdown fix in the plugins against the source. Verify:
  - a second `prek run --all-files` changes nothing and passes;
  - `uv run pytest` passes in full;
  - `uv run lint-lint check .` and `uv run just-lint check .` report nothing;
  - `uv build` succeeds;
  - `uvx --from . lint-lint --help` runs.
- [ ] 2.7 Commit the section as `plugins: import the eight conventions plugins`. Then run
  `scripts/check-private-names --history`. Verify:
  - the commit passes every hook;
  - the history sweep exits 0;
  - `openspec validate import-shared-plugins` passes.

## Workflow follow-up

- Archive the change, which turns the five deltas into this root's specs, once the apply is done.
- The source repository then removes its copies and consumes this marketplace. That is its own change.
