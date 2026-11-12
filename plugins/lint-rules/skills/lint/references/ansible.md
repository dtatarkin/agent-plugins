---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.ansible-lint"
---

# Ansible

Signal: Ansible content — an `ansible/` directory, a collection manifest, or a
role's tasks under `roles/`. The signal is the content, wherever the layout
puts it.

```yaml
      - id: ansible-lint
        name: ansible-lint
        entry: uv run ansible-lint --offline
        language: system
        files: ^ansible/
        exclude: \.sops\.ya?ml$
        require_serial: true
        pass_filenames: false
```

Through the repository's lockfile where it tracks one, which then pins the
linter as a project dependency. A repository that tracks no lockfile — a
collection developed inside its consumer's environment — **hosts it instead**,
pinned by `rev:` like any hook pre-commit installs:

```yaml
  - repo: https://github.com/ansible/ansible-lint
    rev: <tag>
    hooks:
      - id: ansible-lint
        args: [--offline]
        additional_dependencies: [ansible]
        files: ^ansible/
        exclude: \.sops\.ya?ml$
        always_run: false
        require_serial: true
        pass_filenames: false
```

**Hosted, not by name, where nothing pins it**, because a tool pre-commit can
install, and which needs nothing from the consumer's environment that the
hook's own `additional_dependencies` cannot carry, is not left to whatever the
`PATH` holds: called by name there, it is whichever copy the nearest virtual
environment above the repository happens to have, which the repository never
declared. The linter meets that test, and so does the first scanner of the
scanning pair. Three keys of the hosted entry override the upstream manifest's:

- **`additional_dependencies: [ansible]`** — offline, the linter resolves every
  module the content calls from its own environment, and upstream installs the
  core engine alone. The community package carries the collections, and the
  core engine with them. A per-project list of collections is not an option: a
  hook dependency installs Python packages, not collections by name.
- **`always_run: false`** — upstream sets it, which would run the linter on
  every commit whatever it touches; the path filter decides, as it does for the
  local hook.
- **`pass_filenames: false` and `require_serial: true`** are stated although
  upstream defaults the first: the checker compares what the configuration
  states, and a stated value survives a change of the upstream manifest.

The path filter follows the layout: `^ansible/` where the content sits there,
the collection's own content paths where the repository is the collection.

**The linter reads the YAML linter's configuration file too**, and refuses
values it disagrees with. Those values are the markup topic's to state.

`--offline` because otherwise it fetches collections mid-commit, which is both
slow and a network dependency in a blocking gate. Fetching them is a task-runner
recipe run **before** the gate, not part of it.

Serial: it writes a shared collection path, and two invocations race there.

Encrypted files are excluded because they are ciphertext — the linter can only
report that it cannot parse them.

## The YAML parse check

Where encrypted files or vault files carry custom tags, the baseline's YAML
parse check gains `--unsafe`:

```yaml
      - id: check-yaml
        args: [--unsafe]
```

Those files are valid YAML with tags the plain loader refuses to construct.
`--unsafe` checks syntax without constructing, which is all this gate ever
wanted. An exclusion for a template directory whose files are not YAML until
rendered is the **project's**, not the standard's.
