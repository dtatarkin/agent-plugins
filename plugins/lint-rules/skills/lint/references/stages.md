---
paths:
  - "**/.pre-commit-config.yaml"
---

# Stages

## Blocking checks run at commit

A check that blocks runs at the **commit** stage, filtered to the file types it
applies to. That is the whole point of the gate: a finding that arrives later
arrives after the bad commit exists.

Filter by type rather than by path wherever the tool has a type — `types:`,
`types_or:`, `exclude_types:` — so the filter follows the file and not the
repository's current layout. Use `files:` only where the boundary really is a
path: a directory argument, a generated tree, a vendored copy.

## Network checks run on demand

A check that reaches the network — a dependency audit against an advisory
database, a schema fetched from a catalogue — runs **only in the manual
stage**. A commit must never wait on a remote service, and must never fail
because one is down: that failure is indistinguishable from a finding, and the
instinct it trains is to bypass the gate.

Say in the entry that it is manual. It is run by hand through the hook
runner's manual stage, by the hook's id:

```text
prek run --hook-stage manual <id>
```

That command is the whole interface: the standard asks for nothing beside the
hook, so a manual check is runnable in every repository that carries it,
whatever else the repository has.

A manual check that is handed files — one that keeps its filter and has no
`always_run` — runs with `--all-files`; otherwise it is handed only the staged
files, which on a clean tree is none.

## A whole-program check is not handed the file list

A check that reasons over the whole program — a type checker, a project-wide
validator — gets:

- `pass_filenames: false`, because handing it the changed files makes it check
  a fragment of the program and report errors that depend on which files you
  happened to touch;
- a **type filter anyway**, so it is triggered by files of its kind and stays
  inert on a commit that touches none.

Both together. Only the filter without `pass_filenames: false` re-runs the tool
over a partial view; only `pass_filenames: false` without the filter runs a
whole-program check on a commit that changed one line of documentation.

## Serial where the tool races

Set `require_serial: true` where the tool writes shared state — a cache, a
downloaded dependency tree, a lockfile — or where its own output interleaves
into nonsense under parallel invocation. Parallel is the default and is right
for most checks; serial is a statement about that tool, and the entry says
which of the two reasons applies.
