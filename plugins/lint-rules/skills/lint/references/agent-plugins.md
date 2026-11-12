---
paths:
  - "**/.pre-commit-config.yaml"
---

# Agent plugins

Two signals, one per manifest kind, and each derives only its own check:

- **A portable manifest**: a tracked `plugin.json` outside `.claude-plugin/`
  whose `$schema` is an Agent Plugins schema URL. It derives the schema check.
  A `plugin.json` declaring no such schema derives nothing, and neither does
  one that does not parse: parsing is the hygiene set's JSON check.
- **A Claude manifest**: a tracked `.claude-plugin/plugin.json` or
  `.claude-plugin/marketplace.json`. It derives the host's validator.
  `.claude-plugin/` is the only place the host reads them from, so the signal
  is content, not a layout's choice.

Other hosts' marketplace files, such as those under `.agents/`, derive
nothing. Rules about what a manifest or a skill *says* are not a lint concern;
these two checks hold the files to their schema and their host.

The set is **two concerns, one tool each**: the portable manifest's schema,
and the Claude manifests' validation by their host. They read different files
and are not a pair.

## The portable manifest's schema — on demand

```yaml
  - repo: https://github.com/python-jsonschema/check-jsonschema
    hooks:
      - id: check-jsonschema
        args: [--schemafile, <the schema URL the manifests declare>]
        files: (^|/)plugin\.json$
        exclude: (^|/)\.claude-plugin/
        stages: [manual]
```

- **`--schemafile` is the Agent Plugins schema URL the manifests' own
  `$schema` declares.** The schema requires that value to be its own URL, so
  the manifest names the schema it is checked against. The topic writes no
  URL, because the URL carries the schema's version; the configuration copies
  the one its manifests declare, as it would a path.
- **Manual**, because the schema is fetched over the network, and the tool's
  cache does not stand in for the host: a cached schema is used only when the
  host answers, so with the network down the check fails rather than
  validates. A commit must not wait on that host or fail because it is down.
- **Handed files, so run with all of them.** The entry keeps its `files:`
  and `exclude:` and has no `always_run`. Run it as:

  ```text
  prek run --hook-stage manual check-jsonschema --all-files
  ```

  Without `--all-files` the run is handed only the staged manifests, which on
  a clean tree is none. Not the dependency audit's shape either: with
  `always_run` and nothing matched, the hook is handed no file and fails, and a
  hosted hook cannot glob the project's manifests itself.

Where the repository also carries the CI set, its workflow schema check comes
from the same repository: both ids sit under one `repo:` entry, at one pin.

## The Claude manifests — the host's validator

```yaml
  - repo: local
    hooks:
      - id: claude-plugin-validate
        name: claude plugin validate
        entry: bash -c 'for f in "$@"; do claude plugin validate --strict "$f" || exit 1; done' --
        language: system
        files: (^|/)\.claude-plugin/(plugin|marketplace)\.json$
```

- **`--strict`**, so a warning fails the gate: a gate that reports without
  blocking is documentation, not a gate.
- **Local, by name.** No lockfile can pin `claude` and the hook runner cannot
  install it, so the hook calls whatever `claude` is on the committing
  machine's `PATH`. It needs no network.
- **A loop, one manifest a call.** The validator takes one path and ignores a
  second without a word, so the entry hands it each manifest alone and stops
  at the first that fails. `set -e` in place of `|| exit 1` is the same entry.
  Given a plugin manifest, the validator still checks the plugin directory
  around it.
- **File-scoped**, not a whole-program run over named directories: it needs no
  list of plugins, so a new plugin is covered with no edit here. A commit that
  edits only a skill file does not run it, and that is accepted, because a
  skill's content is not what this check holds.

**A machine without `claude` cannot run the hook.** That is an environment
failure, not a finding: report it and let the commit wait, as for any hook
whose tool is missing. Never drop the hook to get past it.
