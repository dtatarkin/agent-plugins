# Proposal

## Why

The house link-checker entry fails on any commit made from a linked git
worktree. Upstream's hook script finds the version it installs by running
`git rev-parse --show-toplevel` and `git describe --tags` inside its own
pre-commit cache checkout. On a commit from a linked worktree, git exports
`GIT_DIR` to the hook, so both calls read the committing repository instead.
They find no `lychee-v*` tag, and the hook exits 100 before checking a link.

Upstream supports `LYCHEE_VERSION=<version>` as the first argument, which
skips that lookup. With it, the hook installs the named version and runs
normally in a linked worktree. This was verified by a real commit from a
detached worktree: before, the hook exited 100; after, it failed on a dead
link and passed a live one.

## What Changes

- The standard's entry in `references/markup.md`, section "Links", becomes
  `args: [LYCHEE_VERSION=<version>, --offline, --no-progress]`, where
  `<version>` is the `rev:` with its `lychee-v` prefix removed. The reason is
  given beside it. The choice of the hosted script hook stays.
- `references/versions.md` says the override moves with the `rev:` when the
  pin is bumped.
- The checker reports a hosted link-checker hook whose first argument is not
  the version override, or whose override names a version other than its
  pin's. A stale override would silently install the old tool.
- This repository's own configuration takes the override.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `lint-checking`: the link checker's version override is checked against
  its pin.

## Impact

- `plugins/lint-rules/skills/lint/references/markup.md`, `versions.md`.
- `src/agent_plugins/lintlint/` (`consts.py`, `rules.py`) and its tests and
  fixtures under `tests/lintlint/`.
- `.pre-commit-config.yaml`.
- A consumer whose configuration follows the old entry gets one new
  `hook-args` finding on the link checker until it adds the override.
