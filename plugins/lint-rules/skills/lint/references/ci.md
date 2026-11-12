---
paths:
  - "**/.pre-commit-config.yaml"
---

# CI

Signal: a tracked YAML file directly under `.github/workflows/` — a GitHub
Actions workflow. That directory is the only place the host reads workflows
from, so the signal is still content, not a layout's choice. An action
metadata file (`action.yml`) or a dependabot file alone derives nothing.

The set is **three concerns, one tool each**: what a workflow means, whether
it is safe, and whether it is shaped as the host expects. None of the three
reads what another reads, so they are not a pair for one concern, and none of
them replaces another.

## Semantics

```yaml
  - repo: https://github.com/rhysd/actionlint
    hooks:
      - id: actionlint
```

Upstream's entry as it is. It reads what a workflow *does*: expressions and
their types, the contexts a step may reach, the inputs an action is given, the
jobs a `needs:` names. A workflow that parses and still cannot run fails here.

## Security

```yaml
  - repo: https://github.com/zizmorcore/zizmor-pre-commit
    hooks:
      - id: zizmor
        args: [--offline, --no-progress]
```

It audits a workflow for what an attacker could use: an expression injected
into a shell step, credentials a checkout leaves behind, an action pinned to a
ref that can move, permissions wider than the job needs.

- **`--offline`** turns off the audits that ask the host's API about the
  actions a workflow uses. A commit must never wait on a remote service, and
  those audits also need a token the committing machine may not hold.
- **The args trap.** `args:` replaces upstream's, which are
  `--no-progress` alone, so the entry writes both flags; with `--offline`
  only, the progress output comes back.
- **Keep upstream's filter.** It hands the auditor more than workflows: the
  dependabot file, action metadata, and the hook configuration itself, because
  the auditor reads hook pins too. The filter is the project's, as every
  filter is; the topic asks only that it is not narrowed to workflows on the
  way in.

## Schema

```yaml
  - repo: https://github.com/python-jsonschema/check-jsonschema
    hooks:
      - id: check-github-workflows
```

It validates each workflow against the workflow schema the hook vendors, so it
runs offline and blocks at commit. It catches the key in the wrong place, the
misspelled trigger, the value of the wrong kind, before either tool above is
asked what the file means.

Where the repository also carries the agent-plugins set, its schema check
comes from the same repository: both ids sit under one `repo:` entry, at one
pin.
