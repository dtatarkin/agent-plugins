# Design

## Context

See proposal.md for why. The repository today holds:

- the private-names guard and its self-test;
- the baseline, markup and shell lint sets (`lint-lint check .` reports nothing);
- a licence and a README;
- two empty marketplace files;
- one spec, `private-names-guard`.

It has no Python, no lockfile, no `.gitignore`, and an untracked `.idea/`.

Everything this change adds already exists in a private source repository, where it is maintained, tested and in use:

- the eight plugins;
- the checker package (two subpackages, `lintlint` and `justlint`, of a package named for that repository);
- the checker test suites with their fixtures and data;
- five plugin tests;
- the specs.

The import is a copy of the current trees, which already carry every ruling made there. Its two hard constraints:

- **The private-names guard** blocks any staged path, content or commit message matching its list. In what moves, the
  only hit is the source's import package name: in every module path under the package and in its imports. A few
  pieces of prose also name private context without matching the list: a machine being "wired", a link step, the
  source repository's own dependencies. Both are rewritten on the way in. The source's name never appears in this
  repository: not in a path, a file, an artifact or a commit message.
- **The house lint standard** governs this repository like any other. Once Python and a lockfile arrive, the set its
  signals derive grows. `tests/lintlint/test_acceptance.py` asserts the audit of this root is empty, so the
  configuration must converge before that test lands.

## Goals / Non-Goals

**Goals:**

- The eight plugins, both checkers and their tests run here as they do at the source. Identifiers, behaviour, tests and
  rule text are unchanged, apart from the rename, the notice line and the rewording listed in D6.
- `uv run pytest` passes at the end, the root's own audit included.
- Every commit passes every hook, the guard included. A history sweep at the end is clean.

**Non-Goals:**

- Removing anything from the source repository, or changing how it consumes these plugins. That is a separate change
  there.
- The Codex and Antigravity listings, CI, a rule-linking script, an authoring plugin, publishing, pushing.
- Restructuring the imported specs. Several imported requirements exceed the 500-character description length that
  `openspec validate --strict` warns about. They are copied as maintained, not split (D9).
- Switching the machine's installed `lint-lint` and `just-lint` to this repository.

## Decisions

### D1: The repository root is the package, in a src layout

- **Distribution and modules:** the root `pyproject.toml` builds the distribution `agent-plugins`. The import package
  is `src/agent_plugins/`, with `lintlint/` and `justlint/` copied whole. Build with hatchling,
  `packages = ["src/agent_plugins"]`. `version = "0.1.0"`, `requires-python = ">=3.12"`, `license = "MIT"`,
  `readme = "README.md"`.
- **Console scripts:** `lint-lint = "agent_plugins.lintlint.entry:main"` and
  `just-lint = "agent_plugins.justlint.entry:main"`.
- **Runtime dependencies:** `typer>=0.12` and `ruamel.yaml>=0.18`, the only third-party imports of the two subpackages.
- **Dev group:** `ruff`, `mypy`, `ty`, `pytest`, and `rust-just>=1.40`. The justfile checker's tests run `just`, and
  the `format-justfile` hook runs through the lockfile once one exists.

Alternative considered: a flat `agent_plugins/` at the root. Rejected. The src layout is what the code and its tests
were written against, and it keeps `plugins/` and `tests/` out of the wheel without exclusion lists.

The install line is `uv tool install git+https://github.com/dtatarkin/agent-plugins`.

### D2: The rename is mechanical, and nothing else in the code moves

Every import of the source package's `lintlint`/`justlint` becomes `agent_plugins.lintlint` /
`agent_plugins.justlint`. The same goes for the two string literals naming the entry modules (`ENTRY_MODULE` in both
`test_entry.py`). Files are written straight into their new paths. The source's package path is never staged, because
the guard reads staged paths too.

Copy with `rsync -a --exclude __pycache__` (or `cp -a` and then delete the caches), so modes survive. Rename with a
pattern that matches the source package's import prefix (a lowercase word ending in `_ai`, followed by `.lintlint` or
`.justlint`). A pattern on `lintlint`/`justlint` alone would also rewrite `tests.fixtures.lintlint`.

### D3: Tooling configuration is taken from the source and narrowed to this root

`pyproject.toml` carries the tooling below. The source's exclusions of vendored trees and of paths that do not exist
here are dropped.

- **ruff:** `line-length = 100`, `target-version = "py312"`, `src = ["src"]`.
  - lint `select = ["E", "W", "F", "I", "B", "UP", "SIM", "RUF", "TID", "S"]`, each with its comment;
  - `ignore = ["S603", "S607"]`, with the reason (tools are called by name);
  - `per-file-ignores` `"tests/**" = ["S101", "S105", "S106", "S107"]`;
  - the banned-api entry forbidding `__future__`;
  - format `quote-style = "double"`.
- **mypy:** `python_version = "3.12"`, `strict = true`, `namespace_packages = true`, `explicit_package_bases = true`,
  `mypy_path = "src"`, `files = ["src/agent_plugins"]`.
- **uv:** `[tool.uv] exclude-newer = "7 days"`, with the comment that the lock resolves under the hooks' cooldown.
- **pytest:** `[tool.pytest.ini_options] testpaths = ["tests"]`.

### D4: The root converges on the Python set in the section that adds Python

The signals added are `pyproject.toml`, Python sources and a tracked `uv.lock`. They derive the Python set of the
standard's python topic, which joins `.pre-commit-config.yaml`:

- `ruff-check` with `args: [--fix]`, and `ruff-format` with `types_or: [python, pyi, jupyter]`
  (`astral-sh/ruff-pre-commit`);
- `uv-lock` (`astral-sh/uv-pre-commit`);
- `validate-pyproject` (`abravalheri/validate-pyproject`);
- local `mypy` (`entry: uv run mypy`) and `ty` (`entry: uv run ty check src tests`), both `types: [python]` and
  `pass_filenames: false`;
- local `pip-audit` at `stages: [manual]`, with the standard's entry.

Two existing entries change because a lockfile is now tracked. The `format-justfile` entry becomes
`uv run just --fmt ...`. The header comment's "tracks no lockfile" sentence is rewritten to state the Python signal and
the lockfile. `_typos.toml` gains `uv.lock` in `extend-exclude`, with the standard's reason.

New pins come from `prek update --cooldown-days 7 --repo-exclude-tag https://github.com/crate-ci/typos=v1`, never
`--freeze`. Check that the configuration still validates under plain pre-commit (`uvx pre-commit validate-config`).

The configuration converges in the same section that adds the package and the acceptance test (section 1), so every
commit's tests are green.

Alternative considered: import everything first and converge after. Rejected, because the acceptance test would be red
between the two commits.

### D5: Two sections, split by what each test reads

| Section | Adds | Needs |
|---|---|---|
| 1 | package, `pyproject.toml`, `uv.lock`, `.gitignore`, the Python set; the checker test suites with fixtures, data and `conftest.py`, the acceptance test included; **not** the two `test_citations.py` | nothing |
| 2 | the eight plugins, the notice line, both `test_citations.py`, the five plugin tests, marketplace, README | the package (`test_lint_hook_filters` imports it), `pyproject.toml` (`test_hook_guard`, `test_hook_manifests` read its scripts) |

Only the two citation tests read the plugins' topic files. The other checker tests name topic paths as strings in
expected findings and read nothing under `plugins/`. Each section therefore lands the tests of its own work and leaves
`uv run pytest` green.

Alternative considered: three sections, with the plugins before the checker tests. Rejected, because the package would
then land in section 1 without its tests.

### D6: What is reworded on the way in

Rule text, identifiers, test names and behaviour are not touched. Only prose naming a private repository, a machine
being "wired", a linking step or the source repository's own dependencies is reworded:

- `justlint/dump.py` module docstring: "on a wired machine …" becomes the `just` on the process's `PATH`.
- Both `entry.py` docstrings, both `test_entry.py` docstrings and the comment above the dependency tuple: "typer,
  pydantic and `biased`" becomes "typer".
- Both `test_entry.py` `THIRD_PARTY` tuples hold the source repository's dependency list. They become this package's
  own: `("typer", "click", "rich", "shellingham")`. `ruamel.yaml` stays allowed on the hook path, as at the source.
- `test_rule_frontmatter.py`'s module docstring, and the docstrings of `declares_paths` and `TestOneLayout`, speak of
  linking into a user-level rules directory and of a link recipe. They are restated against the `rule-file-frontmatter`
  contract: a scoped file would attach on touch, and an empty glob list, a stray key or an import would widen it into
  an always-on rule. Test and function names stay.
- The specs are reworded as `specs/` shows:
  - attachment is described as "where path-scoped attachment is set up", with no link step;
  - `just` is "the one on the harness's `PATH`";
  - the lint domain's cross-domain rule names no domain this repository does not ship;
  - the canonical-copy rule names no pointer and no link.

References to `biased` in `django-rules` and `logging-rules` stay: that library is public.

### D7: The missing-checker notice names this repository

In both `hooks/run-checker` copies, the user-facing sentence changes from a generic `uv tool install` hint to
"Install it with `uv tool install git+https://github.com/dtatarkin/agent-plugins`; the checks resume once it is on the
PATH Claude Code runs with." The copies stay byte-identical and executable, and the line holds no `"` or `\`, so the
`printf` JSON stays valid. `lint-rules` goes from 0.4.0 to 0.4.1 and `just-rules` from 0.1.0 to 0.1.1, in both
manifests of each. `test_hook_guard.py` keeps its `"uv tool install"` assertion and adds one for the URL.

The specs keep saying the notice tells the user "how to install it". The URL is a value the script, README and test
carry, and the spec does not.

### D8: The marketplace lists the eight with the source's entries

Each entry carries:

- `name`;
- `description`;
- `author: {"name": "Dmitry Tatarkin"}`;
- `source: "./plugins/<name>"`;
- `category: "conventions"`.

Descriptions are the source's, except `lint-rules`. Its last sentence spoke of a delivery tier, and it is replaced by
"Loaded when a lint configuration is touched, or when a repository's quality gates are converged." Manifests keep
`Dmitry Tatarkin <tatarkin@gmail.com>` as author. `.agents/plugins/marketplace.json` stays empty.

### D9: Imported specs are copied, not restructured

`lint-standards`, `lint-checking` and `justfile-checking` are the source specs with D6's rewording. `openspec validate`
passes. `--strict` warns only on requirement descriptions longer than 500 characters, which are carried as maintained;
splitting them is a separate change if wanted.

`agent-rules-authoring` keeps that name and takes these requirements from the source:

- the four structure requirements;
- the dual-manifest requirement;
- "A plugin may ship hooks", with one scenario added that states what `test_hook_manifests.py` already checks;
- "Manifests are validated before commit".

The pointer requirement and the delivery spec's marketplace and enablement requirements do not come.

`rule-file-frontmatter` is new. It holds the declaration requirement and the scope-statement requirement from the
source, plus the frontmatter contract `test_rule_frontmatter.py` enforces. That contract is stated as "the repository's
tests fail": no hook runs the suite at commit, and the spec says what is true.

### D10: Things that stay as they are

- `test_portable_manifests.py` keeps its explicit tuple of eight portable plugins: the spec leaves naming them to the
  test.
- `CLAUDE_PLUGIN_DATA` remains where the hook ratchet keeps baselines. Under this marketplace's id it starts empty.
- The README's hook section stays.

### D11: `.gitignore` covers the Python tooling and the IDE directory

`.venv/`, `__pycache__/`, `dist/`, `*.egg-info/`, `.idea/`. The tool caches carry their own `.gitignore`. `.idea/`
holds machine-local IDE state and must never be staged.

### D12: `category` leaves the eight Claude plugin manifests

Every imported `.claude-plugin/plugin.json` carried `"category": "conventions"`. Claude Code 2.1.322 warns that the
field belongs in the marketplace entry and is ignored at load time, and `claude plugin validate --strict` turns that
warning into a failure: on the marketplace and on each of the eight plugins (measured 2026-11-12; the same CLI fails
the source's copies the same way). The field is therefore deleted from the eight Claude manifests. The marketplace
entries keep it (D8), and the portable root manifests never had it. This is the one way the manifests differ from the
copies beyond D7's version bumps. Ruled by the owner on 2026-11-12.

Alternative considered: keep the copies as they are and check with plain `validate`. Rejected, because the warning
names a field nothing reads, and the strict check is what holds the manifests to the CLI from here on.

## Risks / Trade-offs

- **[The newer spelling and markdown fixers rewrite imported text]**
  - Why: this repository pins newer `typos` and `rumdl` than the source.
  - Mitigation: in each section, stage the new files, run `prek run typos --all-files` alone and read the whole
    `git diff` before any other hook. Revert each rewrite of a deliberate spelling and allowlist it. Re-read every
    `rumdl` fix: it has turned a wrapped `#4` into a heading and stripped spaces inside code spans.
  - Known candidate: two lintlint test files carry a 40-hex commit SHA. Allowlist SHAs only if `typos` actually
    rewrites one.
- **[The guard blocks a commit]**
  - Mitigation: rename before staging (D2). If the guard still fires, fix the content. Never bypass it, and never
    commit a workaround that names the hit.
- **[`test_entry.py`'s 0.2 s budget]**
  - Why: it runs the console script installed beside the interpreter, which `uv sync` installs.
  - Mitigation: a cold first run can be slow. Re-run before treating a miss as a finding, as at the source.
- **[The machine's installed checkers come from the source]**
  - Mitigation: verify through `uv run lint-lint` / `uv run just-lint`, or `uvx --from . lint-lint`, never
    `uv tool install` over the installed ones.
- **[The repository is private until it is made public]**
  - Why: the README's GitHub install lines need credentials until then.
  - Mitigation: verify the package builds and installs from the working tree (`uv build`; `uvx --from . lint-lint
    --help`). The install from GitHub is exercised when the repository goes public.
- **[`claude plugin validate --strict` rejects `category` in a Claude manifest]** (found by the section 2 applier,
  2026-11-12, Claude Code 2.1.322)
  - What: every imported `.claude-plugin/plugin.json` carries `"category": "conventions"`. The CLI now warns that the
    field belongs in the marketplace entry and is ignored at load time, and `--strict` turns the warning into a
    failure. Task 2.4's `--strict` checks therefore fail: on the marketplace (eight warnings, one per plugin) and on
    each of the eight plugins. The same CLI fails the source's own `plugins/lint-rules` under `--strict` for the same
    reason. Without `--strict`, the marketplace and all eight plugins pass here.
  - Mitigation: D12. With `category` deleted from the eight Claude manifests, the marketplace and the plugins pass
    `--strict`. The plugin-directory `ICON_MISSING` note does not affect the result.

## Migration Plan

There is nothing to migrate here. Each section is a commit on the trunk. Rollback reverts those commits; nothing
outside this repository changes.

## Assumptions

- **A1:** The applier knows the source repository's clone path, given in its brief and written here as `$SOURCE`. The
  source package directory is the one `$SOURCE/src/*/lintlint` resolves to. The applier reads `$SOURCE` and never
  writes there.
- **A2:** The source trees are copied as they stand when each section runs. The rulings already made there are in
  them, and nothing in them is re-decided here.
- **A3:** The two subpackages import nothing from the source package outside themselves, and nothing third-party
  beyond `typer` and `ruamel.yaml`. The tests need `pytest`, `git` on `PATH`, and `just` (from `rust-just`). Checked
  by reading their imports.
- **A4:** The plugins, the data fixtures and the spec texts match nothing in the guard's list. Only the source package
  name does. Checked against the list read-only. The guard is the proof at each commit.
- **A5:** The checker test data are all `.fixture`-suffixed files and `NESTED_REPO` markers. That is why they add no
  signal to this root's own audit.
- **A6:** `uv` resolves `exclude-newer = "7 days"` as it does at the source.
- **A7:** No section's applier relies on another's memory. Section 2 relies on what section 1 left in the tree:
  `src/agent_plugins/`, `pyproject.toml` with both console scripts, `tests/__init__.py`, and a converged
  `.pre-commit-config.yaml`. A spelling allowlisted in section 1 is in `_typos.toml`.
- **A8:** Of the checker tests, only `tests/lintlint/test_citations.py` and `tests/justlint/test_citations.py` read
  files under `plugins/`. Checked by reading every checker test for `plugins` and `skills/`.
- **A9 (section 1 applier):** `justlint/entry.py` and `tests/justlint/test_entry.py` also opened their docstrings with
  "the repo's other four scripts", the source repository's other console scripts. That is the same class of prose as
  D6's dependency list, so it went too: both now say only that the entry is not a `typer` app. The comment above each
  `THIRD_PARTY` tuple names no private context and stays as it was.
- **A10 (section 1 applier):** `prek update` ran with `--repo` naming the three new repositories only, so the existing
  pins did not move in this change. The new pins and their tag dates: `ruff-pre-commit` v0.17.3 (2026-10-27),
  `uv-pre-commit` 0.13.7 (2026-11-03), `validate-pyproject` v0.27 (2026-10-22), all at least seven days old on
  2026-11-12.
- **A11 (section 1 applier):** `prek run typos --all-files` rewrote nothing in section 1, so `_typos.toml` gained only
  `uv.lock`. No SHA allowlist was needed. `prek run --all-files` changed no file this section did not add, so there is
  no `.git-blame-ignore-revs`.
- **A12 (section 1 applier):** `pyproject.toml`'s `description` and the comments above the two console scripts are
  written for this package. They restate the source's reasons (a plain function, so the hook path imports no `typer`)
  without its list of other scripts and dependencies.
- **A13 (section 2 applier):** in `test_rule_frontmatter.py`, the `frontmatter_violations` docstring also spoke of a
  "linkable" file that is "never linked", so it was restated with the three D6 names. The violation message
  `linked file imports:` and the test names stay: they are behaviour and identifiers, which D6 leaves alone.
- **A14 (section 2 applier):** D12 bumps no version. The six plugins other than `lint-rules` and `just-rules` stay at
  their source versions: the deleted field was ignored at load time, so nothing an installed plugin does changes, and
  this marketplace publishes them for the first time. `lint-rules` and `just-rules` carry D7's bumps only.
