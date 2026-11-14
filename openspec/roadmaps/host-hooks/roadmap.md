# Host hooks

## Phase 1 — Checking on edit in every host

Gate: the `lint-rules` and `just-rules` hooks are recorded in
`docs/host-support.md` as loaded and reporting in Claude Code, Codex and the
Antigravity CLI.

### HH1 Host record and release tags

- **Change:** `host-support-record-and-tags`
- **After:** —
- **State:** active
- **Effort:** s

Scope in the change: the record as a per-host table, and version bumps and tags.

### HH2 Hooks in Codex and the Antigravity CLI

- **Change:** `port-hooks-to-codex-and-agy`
- **After:** HH1
- **State:** planned
- **Effort:** l

The `lint-rules` and `just-rules` hooks load in Claude Code only: their `if`
filters, `${CLAUDE_PLUGIN_ROOT}` commands, event names and `run-checker`'s
input and output are Claude's. Measure each host's hook events and payload
first, then port the hooks per host, record each in `docs/host-support.md`,
and make `agy plugin validate --strict` pass on `lint-rules`.

## Decisions

None yet.

## Open questions

None.

## Follow-ups

None.
