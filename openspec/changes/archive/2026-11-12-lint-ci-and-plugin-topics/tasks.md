# Tasks

Every section ends with the following checks passing, and with the section's own commit on the current branch:

- `uv run pytest`;
- `prek run --all-files`, the private-names guard included;
- `openspec validate lint-ci-and-plugin-topics --strict`.

Nothing is pushed. No artifact, commit message or code comment names the private source repository or the plugins
that stay there (design.md A5). Searches use `git grep` or `command grep`.

## 1. Spike, topics and version bump

- [x] 1.1 Pick `check-jsonschema`'s release by the cooldown (the newest tag of
  `python-jsonschema/check-jsonschema` at least seven days old; check its date by hand per `versions.md`). Then run the
  measurement:
  1. Online, run `uvx --from check-jsonschema==<version> check-jsonschema --schemafile <the $schema URL> <every
     plugins/*/plugin.json>`.
  2. Run the same command under `unshare -rn` with `uvx --offline`.

  Record in design.md under `## Measurements`: the version, both commands, both exit codes, and the first error line of
  the offline run.
  - If the online run fails, fix the manifest (design.md A4).
  - If the offline run **passes**, record that and stop this section for the lead (design.md D1).

  Verify: `## Measurements` holds both results, and the online run exited 0.
- [x] 1.2 Write `plugins/lint-rules/skills/lint/references/ci.md` per design.md D6 and D8: the workflows signal, the
  three entries with `id: actionlint`, `id: zizmor` (args `--offline`, `--no-progress`) and
  `id: check-github-workflows`, one concern each, and zizmor's filter. Front matter: `paths:
  ["**/.pre-commit-config.yaml"]`. Verify: `uv run pytest tests/plugins` passes, and the file states no version
  (`command grep -nE 'v?[0-9]+\.[0-9]+' <file>` finds none).
- [x] 1.3 Write `references/agent-plugins.md` per D1, D2, D3, D6 and D8: the two manifest signals; the hosted
  `id: check-jsonschema` entry, with `--schemafile` described as the URL the manifest's `$schema` declares (no literal
  URL); the manual stage and its `prek run --hook-stage manual check-jsonschema --all-files`; the local
  `id: claude-plugin-validate` loop with `--strict`; and that a missing `claude` is an environment failure. Same
  `paths:`. Verify: as in 1.2.
- [x] 1.4 Edit the existing topics:
  - `markup.md` gains a `## Links` section with `id: lychee`, args `--offline`, `--no-progress`, `types: [markdown]`,
    and the args trap (D4);
  - `applying.md` gains the two signals-table rows;
  - `stages.md` gains D1's sentence on a manual check that is handed files;
  - `versions.md` gains lychee's `lychee-v*` tag quirk;
  - the router `skills/lint/SKILL.md` gains rows for `ci.md` and `agent-plugins.md`.

  Verify: `uv run pytest tests/plugins tests/lintlint/test_citations.py` passes, and `prek run --all-files` leaves no
  rewritten file.
- [x] 1.5 Bump `lint-rules` to 0.5.0 in `plugins/lint-rules/plugin.json` and `plugins/lint-rules/.claude-plugin/plugin.json`
  (D10). Verify: `claude plugin validate --strict plugins/lint-rules` passes, and `uv run pytest
  tests/plugins/test_portable_manifests.py` passes.

## 2. Link checking end to end

- [x] 2.1 In the checker, add `HouseHook("lychee", "markup", Signal.MARKUP)` and its canon (flags `--offline`,
  `--no-progress`) in `consts.py`. Add tests:
  - in `tests/lintlint/test_rules.py`: a markup tree lacking lychee reports `missing-hook`; lychee without either flag
    reports `hook-args`;
  - `test_citations.py` passes with the new entries.

  Verify: those tests pass.
- [x] 2.2 Add the lychee entry of design.md D4 to the configuration of each fixture under `tests/lintlint/data/` that
  carries the markup signal, keeping every fixture's expected findings. Verify: `uv run pytest tests/lintlint` passes,
  except `test_acceptance.py` until 2.3.
- [x] 2.3 Converge this repository: add `# Markup: links.` with lychee to `.pre-commit-config.yaml`, pinned per D9 to a
  `lychee-v*` tag past the cooldown, with the age checked by hand.
  - Run `prek run lychee --all-files`. A dead relative link in a live file is fixed. One inside the archive of closed
    changes is excluded on the hook, by the pattern the rewriting hooks already carry.
  - Run `uvx pre-commit validate-config`.

  Verify: `uv run pytest` passes (`test_acceptance.py` included), and `prek run --all-files` passes.

## 3. Agent plugin manifests end to end

- [x] 3.1 In `types.py`, `consts.py` and `signals.py`, derive the Claude-manifest and portable-manifest signals per
  design.md D5. The portable one reads each candidate `plugin.json`'s `$schema` against D2's URL pattern; unreadable or
  invalid JSON carries no signal. Tests in `tests/lintlint/test_signals.py`:
  - each manifest kind carries its signal;
  - a `plugin.json` without the schema carries none;
  - `.agents/plugins/marketplace.json`, `action.yml` and a dependabot file carry none.

  Verify: those tests pass.
- [x] 3.2 Add `check-jsonschema` and `claude-plugin-validate` to `HOUSE_HOOKS` with their canon per D6:
  - `--strict` for the validator;
  - `--schemafile` matching D2's pattern, separate or joined by `=`;
  - manual without `always_run` for the schema check (D1), splitting `Canon.manual` so `pip-audit` keeps both.

  Apply D7: only an entry pointed at an Agent Plugins schema is the house hook. Tests in `test_rules.py`:
  - each hook missing;
  - each hook stray;
  - `--strict` absent;
  - the schema check at commit;
  - the schema check with `always_run` absent passes;
  - a `check-jsonschema` entry with another schema raises nothing and does not satisfy the set;
  - `pip-audit` still owes `always_run`.

  `test_citations.py` passes. Verify: `uv run pytest tests/lintlint`, except `test_acceptance.py` until 3.3.
- [x] 3.3 Converge this repository: add the `# Agent plugins.` block of design.md D9 to `.pre-commit-config.yaml`. The
  `check-jsonschema` pin is task 1.1's version tag. Update the header comment's signal list. Run
  `uvx pre-commit validate-config`. Verify:
  - `uv run pytest` passes, `test_acceptance.py` included;
  - `prek run --all-files` passes, with `claude-plugin-validate` run over every `.claude-plugin/` manifest;
  - `prek run --hook-stage manual check-jsonschema --all-files` passes, online.

## 4. CI set, proven by tests

- [x] 4.1 Derive the workflows signal per design.md D5, and add `actionlint`, `zizmor` (flags `--offline`,
  `--no-progress`) and `check-github-workflows` to `HOUSE_HOOKS` and `HOOK_CANON` under topic `ci`. Tests:
  - in `test_signals.py`: a workflow under `.github/workflows/` carries the signal, and a nested file, `action.yml` or
    `.github/dependabot.yml` does not;
  - in `test_rules.py`: a tree with a workflow and a configuration lacking each of the three reports three
    `missing-hook` findings, each cited to `ci`; a compliant trio reports nothing; zizmor without `--offline` reports
    `hook-args`; the trio without a workflow is stray;
  - in `tests/lintlint/test_check.py`: an audit of an inline repository tree carrying a workflow and the trio reports
    nothing.

  Verify: `uv run pytest` passes, and `uv run lint-lint check` over this repository
  reports nothing, with no CI hook derived.
