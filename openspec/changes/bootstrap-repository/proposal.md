# Proposal

## Why

This repository will publish agent plugins that carry coding conventions, and
it will be public. Today it holds only an initialised OpenSpec root: no licence,
no README, no quality gates, no marketplace files, and nothing that stops a
commit from carrying a name that must not be published. The plugins arrive in
later changes, and each of them should land in a repository whose gates already
hold, so the gates come first.

## What Changes

- Add a commit guard, `scripts/check-private-names`, that fails any commit whose
  staged paths, staged content or message match a list of names that must not
  be published. The list is held outside the repository: the guard reads
  `$AGENT_PLUGINS_PRIVATE_NAMES`, falls back to
  `~/.config/agent-plugins/private-names`, and fails when it has no list. No
  path is excluded from it. It also has a history mode that checks every
  reachable commit. A self-test on synthetic names guards the guard.
- Add the house lint sets the repository's signals derive: the baseline set
  (file hygiene, secret scanning, spelling, justfile and nix formatting), the
  markup set (YAML, TOML, markdown) and the shell set (the guard is a bash
  script), with the linters' own configuration files. One install command
  installs both the pre-commit and the commit-msg hooks.
- Add an MIT `LICENSE` and a `README.md` saying what the repository is for, that
  it holds no plugin yet, and how a contributor installs the hooks and gives the
  guard its list.
- Add empty marketplace files for Claude Code (`.claude-plugin/marketplace.json`)
  and Codex (`.agents/plugins/marketplace.json`), both named `agent-plugins`
  with no plugin listed.
- Give `openspec/config.yaml` a short context stating that every artifact here
  is public.
- Not in this change: any plugin, any install line, any CI workflow, any agent
  instruction file, enabling plugins for this repository, and pushing.

## Capabilities

### New Capabilities

- `private-names-guard`: the local commit check that keeps names which must not
  be published out of the repository's paths, content, commit messages and
  history, and that fails closed when it has no list.

### Modified Capabilities

None. The root has no specs yet.

## Impact

- New files: `scripts/check-private-names`, `tests/check-private-names.sh`,
  `.pre-commit-config.yaml`, `.yamllint.yaml`, `.rumdl.toml`, `_typos.toml`,
  `LICENSE`, `README.md`, `.claude-plugin/marketplace.json`,
  `.agents/plugins/marketplace.json`; `openspec/config.yaml` gains a context.
- Every later commit runs the hooks. A machine without the list cannot commit
  here until one is provided: intended, since the repository is private and has
  one committer until it is made public, and how outside contributors commit is
  decided then.
- Tools a committer needs: `prek` or `pre-commit`, `git`, `bash`, a POSIX `grep`;
  the hook repositories fetch their own linters.
