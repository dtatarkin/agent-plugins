# Design

## Context

See proposal.md for why. What exists today:

- **The standard.** `lint-rules` keeps one topic file per set under `plugins/lint-rules/skills/lint/references/`.
  `applying.md` carries the signals table, and the router `skills/lint/SKILL.md` indexes the topics. Every topic
  attaches on `**/.pre-commit-config.yaml` through `paths:`, some also on their linters' own files.
- **The checker** (`src/agent_plugins/lintlint/`) works in four steps:
  - it derives a `Signal` set from `git ls-files` (`signals.py`);
  - it compares the configuration with `HOUSE_HOOKS`, which maps each hook id to its topic and signal (`consts.py`);
  - it checks each hook against `HOOK_CANON` (flags, whole-program, filtered, serial, manual);
  - it checks each hook's form (`rules.py`).

  `Canon.manual` demands both `stages: [manual]` and `always_run: true`. That is the shape of the dependency audit.
- **The tests.** `tests/lintlint/test_acceptance.py` asserts `audit(REPO_ROOT) == []`. Adding a house hook therefore
  fails the suite until this repository's configuration carries it.
  - `tests/lintlint/test_citations.py` holds every `HOUSE_HOOKS` id to its topic as `id: <hook>`, and every canonical
    flag to its topic's text.
  - The fixtures `tests/lintlint/data/{compliant,drifted,lockless}/` each carry `README.md`, so they carry the markup
    signal. The `umbrella` fixture is read by the tests as it is.
- **This repository** carries no `.github/`. When this change applies, it tracks nine plugins, each with a portable
  root `plugin.json` and a `.claude-plugin/plugin.json`: the eight imported ones plus `plugin-rules`, which the change
  `rules-authoring-plugin` lands first. It also tracks `.claude-plugin/marketplace.json`, and
  `.agents/plugins/marketplace.json`, which is not for this change.

What was measured or read while planning:

- **`claude plugin validate`** (2.1.322) takes **one** path. A second path is ignored silently: `validate --strict
  plugins/lint-rules /nonexistent` exits 0.
  - It accepts a manifest file as well as a directory, and given a plugin manifest file it still runs the plugin
    directory checks.
  - `--strict` passes today on the marketplace and on every plugin. It works with the network off (`unshare -rn`), and
    takes about 0.65 s a call.
- **check-jsonschema's cache.** In the upstream source (`cachedownloader.py`, main), a cached remote schema is used
  only when an HTTP response arrives and its `Last-Modified` is not newer than the cached file. A connection error is
  retried and then raised as `FailedDownloadError`, with no fall-back to the cache. So a cached schema is expected
  **not** to validate offline. D1 still has the result measured, as the roadmap's decision asks.
- **The Agent Plugins schema** (`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`) is draft 2020-12 with no
  remote `$ref`. It requires `$schema` (a const equal to its own URL) and `name`, and its top level is closed.
- **Upstream hook manifests:**
  - `lychee`: `language: script`, installs its binary into the hook's checkout on first run only;
    `args: ["--no-progress"]`; `types: [text]`; `require_serial: true`.
  - `zizmor` (`zizmorcore/zizmor-pre-commit`): `args: ["--no-progress"]`. Its `files:` matches workflows, dependabot
    files, `action.y?ml` and `.pre-commit-{config,hooks}.y?ml`.
  - `check-jsonschema`: `types_or: [json, yaml]`, no args.
  - `check-github-workflows`: uses the vendored workflow schema, so it runs offline.
  - `actionlint` (`rhysd/actionlint`): a golang hook on `.github/workflows/`.
- **`unshare -rn <cmd>`** runs a command with no network on this machine, without root.

## Goals / Non-Goals

**Goals:**

- The three new signals are derived. The new hooks join the set where their signals are, and leave where they are not.
- Each new hook's canonical entry is stated once, in its topic, and enforced by the checker where it is mechanical.
- This repository converges on what it derives, and the CI topic is proven by tests.

**Non-Goals:**

- No other repository is converged. The reach into repositories with markdown or manifests is accepted.
- No CI workflow is added here.
- The Codex marketplace file, `.agents/`, is not checked.
- Manifests do not attach the lint topics: no new governed file names. Rules about manifests themselves belong to
  `plugin-rules`.
- No requirement other than the four in the delta specs is amended.

## Decisions

### D1: The plugin schema check is measured first, and runs in the manual stage

The first task pins `check-jsonschema` and measures it:

1. once online, over every portable manifest;
2. again under `unshare -rn`, after the online run has filled the cache.

The result goes into this file under `## Measurements`, written by the applier: the commands, both exit codes, and the
first error line of the offline run.

- **Expected result: the offline run fails.** The hook then runs in the manual stage. `stages.md` already sends a schema
  fetched from a catalogue there, so no requirement changes. The delta specs assume this outcome.
- **If the offline run passes,** the applier records it and stops the section. The hook would then belong at commit,
  which contradicts the `lint-checking` delta's "The plugin schema check blocks" scenario. The lead decides on the spec
  change.

**The manual entry stays file-scoped.** It keeps `files:` for root `plugin.json` files outside `.claude-plugin/`, and
filenames are passed. It is run with `prek run --hook-stage manual check-jsonschema --all-files`.

- The checker gains a way to require `stages: [manual]` without `always_run: true`. For example, `Canon` splits its
  `manual` flag from a new `always_run` flag, and the dependency audit keeps both.
- `stages.md` gains one sentence: a manual check that is handed files runs with `--all-files`.
- Alternative rejected: the dependency audit's shape (`always_run`, `pass_filenames: false`). The hook is a hosted
  Python hook and cannot glob the project's manifest list. With `always_run` and no file matched, it would be handed
  nothing and fail.

### D2: The schema is the one the manifest declares, so no topic states its version

The schema URL carries `1.0.0`, and "Canonical configuration carries no version numbers" bars a topic from stating a
release number. So the topic does not write the URL as a constant. It says that `--schemafile` is the Agent Plugins
schema URL the manifest's own `$schema` declares, which the schema requires to be its own `$id`.

- The checker accepts any `--schemafile` value matching `https://agent-plugins.org/schemas/<any>/plugin.schema.json`,
  separate or joined by `=`. That pattern lives in `consts.py`.
- This repository's configuration names the URL its manifests declare. That is a project value, like a path.
- Alternative rejected: amending the version requirement. The roadmap amends only the house-tools requirement for this
  slot.

### D3: The Claude validator is a local hook handed manifest files in a loop

```yaml
  - repo: local
    hooks:
      - id: claude-plugin-validate
        name: claude plugin validate
        entry: bash -c 'for f in "$@"; do claude plugin validate --strict "$f" || exit 1; done' --
        language: system
        files: (^|/)\.claude-plugin/(plugin|marketplace)\.json$
```

- **Why local.** No lockfile can pin `claude`, and pre-commit cannot install it, so the hook calls it by name. A machine
  without it fails as an environment failure.
- **Why a loop.** The tool takes one path, so the loop stops at the first manifest that fails.
- **Why file-scoped rather than whole-program over named directories.** It needs no project-chosen directory list. A
  new plugin, such as `plugin-rules`, is covered with no configuration edit. Editing a skill file alone does not run it,
  and that is accepted: skill content is `plugin-rules`' subject.
- **Canon.** The flag `--strict`. The checker already reads a `bash -c` loop by the command its body runs.
- Variant: `|| exit 1` may be replaced by `set -e`. Either form satisfies the canon, which compares leading tokens and
  flags.

### D4: Link checking is lychee's hosted script hook, offline, on markdown

```yaml
  - repo: https://github.com/lycheeverse/lychee
    hooks:
      - id: lychee
        args: [--offline, --no-progress]
        types: [markdown]
```

- `--offline` limits the check to local targets, so a commit never waits on a remote host. Fragment checking stays off,
  as lychee's default, which leaves anchors to the markdown linter.
- **The args trap.** `args:` replaces upstream's `["--no-progress"]`, so the canon has both flags. The same trap is why
  `TYPOS_DEFAULT_FLAGS` exists.
- **Signal.** It is derived on the existing markup signal, as `rumdl` is: the set is one set.
- **Pin quirk.** The repository's release tags have the form `lychee-v<version>`, beside tags for its library crate.
  `versions.md` states that the pin is a `lychee-v*` tag.
- Alternatives rejected:
  - `lychee-system` needs a declared system install on every committing machine;
  - `lychee-docker` needs a Docker daemon at commit.

### D5: Three signals, each stated as content

| Signal | Content | Derives |
|---|---|---|
| workflows | a tracked `*.yml`/`*.yaml` directly under `.github/workflows/` | `actionlint`, `zizmor`, `check-github-workflows` |
| Claude manifest | a tracked `.claude-plugin/plugin.json` or `.claude-plugin/marketplace.json` | `claude-plugin-validate` |
| portable manifest | a tracked `plugin.json` outside `.claude-plugin/` whose `$schema` is an Agent Plugins schema URL | `check-jsonschema` |

- **Not a layout choice.** `.github/workflows/` and `.claude-plugin/` are the only places their hosts read, so the
  signals stay content rather than a layout's directory names.
- **The portable signal reads JSON.** It reads each candidate `plugin.json` once. An unreadable or unparsable one
  carries no signal; parsing is the hygiene set's JSON check.
- **Derive nothing:** `action.yml`, dependabot files and `.agents/` manifests.
- The `Signal` member names are the implementer's choice.

### D6: The house set and the canon

| Hook | Topic | Canon |
|---|---|---|
| `actionlint` | ci | none |
| `zizmor` | ci | flags `--offline`, `--no-progress` |
| `check-github-workflows` | ci | none |
| `check-jsonschema` | agent-plugins | `--schemafile` an Agent Plugins URL (D2); manual without `always_run` (D1) |
| `claude-plugin-validate` | agent-plugins | flag `--strict` |
| `lychee` | markup | flags `--offline`, `--no-progress` |

**zizmor's own filter.** Upstream's `files:` also reaches `.pre-commit-config.yaml`. The topic keeps upstream's filter
and says why: the auditor reads hook pins too. Filters are the project's, and the checker compares none.

### D7: A schema check of any other schema is the project's

`check-jsonschema` is a generic id. The checker treats an entry with that id as the house hook only when its
`--schemafile` matches D2's pattern. Any other such entry:

- raises no `hook-args` finding;
- does not satisfy the derived set's `check-jsonschema`;
- is not reported as stray.

Where no entry matches, `missing-hook` is raised. The hook set is computed over the house-qualifying entries only, so
the change stays inside `rules.py`.

### D8: Topics, router and applying table

- **`ci.md`:** the signal, the three entries, why each is its own concern, and zizmor's offline flag and filter.
- **`agent-plugins.md`:** the signal, the two entries, the manual run command for the schema check, the reason for the
  manual stage, and that a missing `claude` is an environment failure.
- **`markup.md`:** a `## Links` section for lychee.
- **Both new topics** carry `paths: ["**/.pre-commit-config.yaml"]`. No new governed name, so `GOVERNED_GLOBS` and
  `hooks.json` stay as they are.
- **`applying.md`:** two signals-table rows.
- **The router:** two index rows.
- **`stages.md`:** D1's sentence.
- **`versions.md`:** D4's pin quirk.
- No topic states a version, and the schema URL is described per D2.

### D9: This repository's configuration

- **Under the markup sets:** `# Markup: links.` with lychee.
- **A new block, `# Agent plugins.`,** with the hosted `check-jsonschema` and the local `claude-plugin-validate`:

  ```yaml
  - id: check-jsonschema
    args: [--schemafile, <the manifests' $schema URL>]
    files: (^|/)plugin\.json$
    exclude: (^|/)\.claude-plugin/
    stages: [manual]
  ```

- **No CI block:** there is no workflow signal.
- **The header comment's** list of signals gains the two manifest signals.
- **Pins** come from `prek update --cooldown-days 7 --repo-exclude-tag https://github.com/crate-ci/typos=v1`, then the
  age is checked by hand per `versions.md`. lychee's pin must be a `lychee-v*` tag.
- `uvx pre-commit validate-config` confirms the file runs under plain pre-commit, the script hook included.

### D10: Version bump

`lint-rules` goes from 0.4.1 to 0.5.0 in `plugin.json` and `.claude-plugin/plugin.json`. The descriptions name no
topic list, so they stay. The marketplace entry carries no version.

### D11: Sections follow the sets

The tasks land in this order:

1. topics, the spike and the bump;
2. lychee end to end;
3. agent-plugins end to end;
4. CI.

Every section that adds a house hook also converges this repository's configuration and the fixtures in the same
section, because the acceptance test fails otherwise.

## Risks / Trade-offs

- [Every commit here needs `claude`] → It is the host the repository's plugins serve. Its absence is reported as an
  environment failure, and a colleague without it reads that in `agent-plugins.md`.
- [lychee's script hook downloads an installer and the binary on first run] → This is the same trust as any hosted
  hook's install, pinned by `rev:`. Later runs reuse the binary in the hook's checkout and need no network.
- [The manual schema check is forgotten] → `claude-plugin-validate` gates every commit for the Claude manifests. The
  portable manifest repeats their fields, so a drift shows when the manual stage runs. The topic names the command.
- [A consuming repository's audit grows findings] → This was accepted by the roadmap. A finding is legacy to the
  ratchet until a convergence is asked for.
- [Old archived changes carry relative links that no longer resolve] → The first lychee run over all files shows them.
  An archived change is history: exclude its tree on the hook, not by rewriting it.

## Migration Plan

None beyond the sections. The plugin's new version reaches a consumer at its next update. Rollback is reverting the
change's commits.

## Measurements

<!-- Written by the applier of task 1.1: the commands, both exit codes, and the first error line of the offline run. -->

## Assumptions

- **A1.** The change `rules-authoring-plugin` has landed `plugins/plugin-rules/` with a root `plugin.json` declaring
  the Agent Plugins schema and a `.claude-plugin/plugin.json`. If it has not landed, the file-scoped hooks cover
  whatever plugins exist, and nothing in this change names a plugin.
- **A2.** `claude` 2.1.322 or later is on `PATH` for every applier turn, and `unshare -rn` works without root.
- **A3.** The probe's assumptions stand, per the planning answers:
  - hosted hooks are pinned by `rev:`;
  - `claude plugin validate` is a local hook;
  - lychee and zizmor run with `--offline`;
  - the signal definitions are D5's;
  - the topic files are `ci.md` and `agent-plugins.md`, with lychee in `markup.md`;
  - `lint-rules` gets a minor version bump.

  D3 refines the probe: the validator is handed files rather than project-named directories.
- **A4.** The current portable manifests validate against the schema. Task 1.1's online run confirms it; a failure
  there is fixed in the manifest within that task.
- **A5.** No artifact or commit message names the private source repository or the plugins that stay there.
