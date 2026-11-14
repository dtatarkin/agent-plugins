# Design

## Context

See proposal.md, Why. What the tree holds today:

- `docs/host-support.md` has one `##` section per host and one `###` section
  per install run: Claude Code (GitHub), Codex (local clone, GitHub) and the
  Antigravity CLI (local clone, GitHub). The Codex and Antigravity CLI
  local-clone runs came from the archived change
  `2026-11-12-codex-and-antigravity-support`, whose design (D5 to D10) holds
  their method. The three GitHub runs landed directly as `docs:` commits
  (`6ccdd50`, `11451f5`).
- The README gives install blocks under `## Install in Claude Code`,
  `## Install in Codex` and `## Install in the Antigravity CLI`. It points to
  the record twice: after the install blocks and in "Install the checkers".
- Plugin tags (`<name>--v<version>`, annotated) all mark `8853169`. Since then
  `lint-rules` changed `hooks/run-checker`, `references/markup.md` and
  `references/versions.md` and still declares 0.5.0. `just-rules` and
  `python-rules` declare 0.2.0, which has no tag. The marketplace entries
  carry no version, so the two `plugin.json` files are the only places a
  version lives, and `tests/plugins/test_portable_manifests.py` holds them
  equal.
- Tests under `tests/plugins/` are run by `uv run pytest`; no pre-commit hook
  runs them. The one local pytest hook, the private-names self-test, is a
  `language: system` entry running `uv run pytest -q <file>`.
- The remotes are `github` and `aws`. `github/main` is at `6d3df33` and
  `aws/main` at `d4aa8a4`, both behind the trunk.

## Goals / Non-Goals

**Goals:**

- The record answers "what does host X do with these plugins" from a table,
  and HH2 can update cells, not append runs.
- The version rule is enforced at commit time, not just written down.

**Non-Goals:**

- Re-running any install. The table is filled from facts the current record
  already established.
- Pushing anything. The tags are made locally; the push is the owner's.
- Choosing a version scheme past 1.0.

## Decisions

### D1. The record's form

One table, hosts as columns in the README's order, and these rows:

| Row | Holds |
|-----|-------|
| Verified on | host version and date of the latest run |
| Install sources run | local clone, GitHub, or "not run" for each |
| Skills | loaded or not, and the name they are listed under |
| Hooks | loaded and fire, or not loaded and why |
| Plugin manifest read | which `plugin.json`, or "not observed" |
| Marketplace file read | which file, "none", or "not observed" |

Then a `## Quirks` section with one `###` per host listing the facts a
maintainer needs that fit no row: the Antigravity CLI's subdirectory install
copying only that plugin and not depending on the clone (which the
subdirectory requirement asks the record to state), the flags a headless run
needs, the Antigravity CLI's root-only `hooks.json`, and its sign-in living
outside its configuration folder.

"Not run" and "not observed" are distinct values. "Not run" is required by
the spec for an install form that was never run. "Not observed" covers a fact
the runs could not see, such as which manifest Claude Code read.

Alternative: one short `##` section per host with a fixed bullet list. It
reads well but makes comparison across hosts harder, and a test over three
bullet lists is no simpler than one over a table.

### D2. Where a run's detail goes

A run's commands, account isolation and observations go into the change that
makes the run, in its design or a note beside it, which the archive keeps. A
run made without a change goes in its commit message. The record carries the
outcome. The current narrative is not copied anywhere: the archived change
and the history of `docs/host-support.md` already hold it.

### D3. The record test

`tests/plugins/test_host_support_record.py` reads the README's
`## Install in <host>` headings (dropping a leading "the ") as the supported
hosts. It then reads the first Markdown table in `docs/host-support.md` and
checks that:

- the header's columns after the first are those hosts, in that order;
- each row of D1 is present, by its first cell;
- no cell is empty.

It tests the record against the README, not against a list in the test, so
adding a host's install block without adding its column fails.

### D4. The version test and its hook

`tests/plugins/test_plugin_versions.py` reads each plugin's version from its
root `plugin.json`. It skips the whole module, with its reason, when the
clone holds no `*--v*` tag. For each plugin whose tag `<name>--v<version>`
exists, it fails when `git diff --quiet <tag> -- plugins/<name>` reports a
difference or `git ls-files --others --exclude-standard plugins/<name>` lists
an untracked file. A plugin whose version has no tag passes: it is a bump
not yet released.

The diff is taken against the working tree, so under pre-commit, which
stashes unstaged changes, it sees exactly what is being committed. A local
hook runs it on any staged file under `plugins/`:

```yaml
- id: plugin-versions
  name: plugin versions follow their files
  entry: uv run pytest -q tests/plugins/test_plugin_versions.py
  language: system
  files: ^plugins/
  pass_filenames: false
```

Alternative: compare against the latest tag of the plugin, not the tag of
the declared version. That would fail on every commit between a bump and its
tag, so a release could not span two commits.

### D5. Fixing the drift

Bump `lint-rules` to 0.6.0: `markup.md` and `versions.md` change rules, so
under the new requirement this is a minor bump. Commit the change, then run
`claude plugin tag plugins/<name>` for `just-rules`, `python-rules` and
`lint-rules` on the trunk. Their files are unchanged since their bumps, so
tagging the trunk tip marks the same content as tagging the bump commits
would. The other six plugins are unchanged since `8853169` and keep their
tags.

### D6. Telling agents

The spec is the normative home, but agents read `AGENTS.md`. A short
"Releasing a plugin" section there states the bump and tag steps and points
to the `host-support` spec. The hook from D4 enforces the bump half.

## House rules

- **python-rules**: the two tests follow its testing topic and the pattern of
  the existing `tests/plugins/` tests. None broken.
- **plugin-rules**: the `lint-rules` bump keeps both manifests equal, per the
  portable-manifest topic. None broken.
- **lint-rules**: the new local hook follows the existing local pytest hook
  (`language: system`, `uv run`). None broken.

## Risks / Trade-offs

- [Pushing the trunk without tags leaves the remote's plugins untagged] →
  The `Pushing the trunk` scenario names the step, and `AGENTS.md` repeats
  it. A push is never done without the owner.
- [A clone made without tags, such as a CI checkout, skips the version test]
  → The skip says why. The pre-commit hook runs in the owner's clone, which
  has the tags.
- [Dropping the narrative loses the "how" of past runs from the current file]
  → The history of `docs/host-support.md` and the archived change keep it,
  and D2 says where future runs' detail goes.
