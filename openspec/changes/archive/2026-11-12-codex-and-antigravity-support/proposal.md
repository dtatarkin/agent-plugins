# Proposal

## Why

The README says these plugins are for Claude Code, Codex and the Antigravity
CLI, but only Claude Code has an install line and a marketplace that lists
anything: `.agents/plugins/marketplace.json` is empty, and no plugin has ever
been installed or run in Codex or in the Antigravity CLI (`agy`). A claim of
support that was never tried is not support, and it has to hold before the
repository goes public.

## What Changes

- Fill `.agents/plugins/marketplace.json`, the marketplace file Codex reads,
  with every plugin under `plugins/`, under the same names and paths as the
  Claude Code marketplace; a test holds the two files equal on names and paths.
- Install two plugins in Codex and in `agy` from a local clone, run one skill
  in each host, and observe what the plugins' hooks do there. Measure whether
  `agy` installs one plugin from a subdirectory of this multi-plugin
  repository.
- Add `docs/host-support.md`, the committed record of those runs: per host,
  the host version, the install form and its outcome, the skill run, and the
  hooks' behaviour. It names no local path. The install from GitHub is
  recorded there once the repository is public; this change records only the
  local-clone installs.
- Give the README one install block per supported host: Codex through its
  marketplace, the Antigravity CLI from a clone's plugin subdirectory, and
  drop the sentence that the Codex marketplace lists nothing.
- Not in this change: any third plugin manifest (if a host needs one, the
  change stops rather than adding it), any change to the plugins' hooks
  whatever they are found to do in the other hosts, removing the test
  installs, and hosts other than the three (OpenCode, Copilot CLI and Cursor
  are not supported).

## Capabilities

### New Capabilities

- `host-support`: which hosts the plugins support, how each installs them
  (the README's install blocks and the Codex marketplace file), and the
  committed record of each host's install, skill run and hook behaviour.

### Modified Capabilities

None. `agent-rules-authoring` keeps its two-manifest contract; this change
measures that the two manifests suffice in the other hosts.

## Impact

- New: `docs/host-support.md`, `tests/plugins/test_agents_marketplace.py`.
- Changed: `.agents/plugins/marketplace.json`, `README.md`.
- No plugin, manifest, hook or lint configuration changes; no dependency is
  added. `check-json` already parses the marketplace file; no host validator
  hook is added for it.
- Outside the repository: the runs register a local marketplace and two
  plugins in Codex's user configuration and install two plugins into `agy`'s
  plugin folder. They stay installed.
