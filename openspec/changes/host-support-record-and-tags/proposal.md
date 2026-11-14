# Proposal

## Why

`docs/host-support.md` is written as a run log: for each install it records
how the account was isolated, which flags the run needed, where the host
cached the copy, and what each scratch run printed. What a reader needs is
what each host does with these plugins today. That is spread across about 250
lines of narrative, and the next roadmap slot (HH2, hooks in Codex and the
Antigravity CLI) would add more runs in the same style. The record
requirement also names only Codex and the Antigravity CLI, though the file
already records Claude Code.

Releases have no rule either. The plugin tags all mark one commit
(`8853169`). Since then `lint-rules` changed its hook script and two topic
files without a version bump, so `lint-rules--v0.5.0` no longer marks what
0.5.0 ships. `just-rules` and `python-rules` were bumped to 0.2.0 and never
tagged. Claude Code caches an installed plugin by its version, so a change
shipped without a bump does not reach a user who already has the plugin.

## What Changes

- The host-support record becomes a current-state record: one table with a
  column per supported host and a fixed set of rows (version and date last
  verified, install sources run, skills, hooks, manifest read, marketplace
  file read), followed by a short list of each host's quirks. The commands
  and observations of each run stay in the change that made the run, not in
  the record.
- The record requirement names Claude Code beside Codex and the Antigravity
  CLI. An install form not yet run is a cell reading "not run", never a
  missing row or column.
- A test holds the record's table to the README: one column for each host the
  README gives an install block for, in the README's order, every required
  row present, and no empty cell.
- New requirement: a change to any file of a plugin bumps that plugin's
  version, in both its manifests, in the same commit. The commit is tagged
  `<name>--v<version>` with `claude plugin tag`. When the trunk is pushed to
  a remote, the tags go with it, to both remotes. A test fails when a plugin's
  files differ from the tag of its current version.
- The existing drift is fixed: `lint-rules` is bumped to 0.6.0, and
  `just-rules` 0.2.0, `python-rules` 0.2.0 and `lint-rules` 0.6.0 are tagged.
  Pushing the tags stays the owner's call.
- `docs/host-support.md` is rewritten in the new form from what the current
  record already established. No host is re-run.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `host-support`: the record requirement changes from a per-run log of Codex
  and the Antigravity CLI to a current-state table of all three supported
  hosts, held by a test. A new requirement covers version bumps and release
  tags.

## Impact

- `docs/host-support.md`: rewritten.
- `README.md`: the sentence describing the record.
- `AGENTS.md`: a short section on releasing a plugin, pointing at the spec.
- `tests/plugins/`: two new tests, one for the record table and one for
  version tags.
- `plugins/lint-rules/plugin.json` and `.claude-plugin/plugin.json`: version
  0.6.0.
- Git tags: three new local tags. Nothing is pushed.
- `openspec/roadmaps/host-hooks/roadmap.md`: HH1 set `active`, and its sketch
  shrunk to a pointer.
