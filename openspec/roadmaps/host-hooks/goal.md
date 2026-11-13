# Host hooks

## Destination

The plugins that check on edit do so in every supported host, not only in
Claude Code: the `lint-rules` and `just-rules` hooks load and report in Codex
and the Antigravity CLI as they do in Claude Code, and `agy plugin validate
--strict` passes on `lint-rules`. The `host-support` record names every host it
records, Claude Code included, and says when a plugin is bumped and re-tagged.

## Why

The repository is public and its install has been run from GitHub in all three
hosts, but checking on edit works in one of them. A colleague on Codex or the
Antigravity CLI gets the rules without the checks that hold them.

## Out of scope

- Hosts beyond Claude Code, Codex and the Antigravity CLI.
- New checks: the port carries the existing checkers, unchanged.
