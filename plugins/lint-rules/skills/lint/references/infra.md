---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.tflint.hcl"
  - "**/.checkov.yaml"
  - "**/.checkov.yml"
  - "**/trivy.yaml"
  - "**/.trivyignore"
  - "**/.ansible-lint"
  - "**/.hadolint.yaml"
---

# Infrastructure

Signal: any `*.tf`, Ansible content — an `ansible/` directory, a collection
manifest, or a role's tasks under `roles/` — a `Dockerfile`, a helm chart, or
Kubernetes manifests. The signal is the content, wherever the layout puts it,
and each piece switches on its own hooks:

| Content | Hooks |
|---|---|
| any `*.tf` | the Terraform trio and the scanning pair |
| Ansible content | the Ansible linter and the scanning pair |
| a `Dockerfile` | `hadolint` |
| a helm chart (a `Chart.yaml`) | the scanning pair |
| a Kubernetes manifest (a YAML file with `apiVersion` and `kind` at its top level) | the scanning pair |
| a compose file alone | nothing |

**A compose file alone derives nothing**, because neither scanner of the pair
reads one, and a gate that reads nothing is not carried.

Throughout, `<dir>` is the repository's own layer directory. **The directory is
the project's, the rest of the entry is the standard's.**

## Terraform

```yaml
  - repo: local
    hooks:
      - id: terraform-fmt
        name: terraform fmt
        entry: terraform fmt -recursive <dir>
        language: system
        files: ^<dir>/.*\.tf$
        pass_filenames: false

      - id: terraform-validate
        name: terraform validate
        entry: terraform -chdir=<dir> validate
        language: system
        files: ^<dir>/.*\.tf$
        pass_filenames: false

      - id: tflint
        name: tflint
        entry: tflint --chdir <dir> --recursive
        language: system
        files: ^<dir>/.*\.tf$
        pass_filenames: false
```

All three by name: the toolchain is pinned where the project pins its
toolchain, and a hook never reaches outside its own repository to find one. On
a machine where the tool is missing, the hook has **not produced a finding** —
it is an environment failure, and the commit waits.

All three are whole-directory commands, hence `pass_filenames: false` with a
path filter: the language's tooling reasons about a root, not about files.

### Several directories

**Each stays one hook, under the same id, however many directories it runs
in.** A repository with a second root beside the first, or a module library
with nothing at its top, runs the entry over each directory the project names
— never one hook per directory, whose ids would differ from repository to
repository:

```yaml
      - id: terraform-fmt
        name: terraform fmt
        entry: terraform fmt -recursive <dir> <other-dir>
        language: system
        files: ^(<dir>|<other-dir>)/.*\.tf$
        pass_filenames: false

      - id: terraform-validate
        name: terraform validate
        entry: >-
          bash -c 'rc=0; for d in "$@"; do echo "$d:";
          terraform -chdir="$d" validate || rc=1; done; exit $rc'
          -- <dir> <other-dir>
        language: system
        files: ^(<dir>|<other-dir>)/.*\.tf$
        pass_filenames: false

      - id: tflint
        name: tflint
        entry: >-
          bash -c 'rc=0; for d in "$@"; do echo "$d:";
          tflint --chdir "$d" --recursive || rc=1; done; exit $rc'
          -- <dir> <other-dir>
        language: system
        files: ^(<dir>|<other-dir>)/.*\.tf$
        pass_filenames: false
```

The loop prints each directory before its result and runs them all, so a
failure names its root and one bad root does not hide the next. **Which
directories those are is the project's**: a library names its example roots or
its modules, because only it knows which of them stand alone.

### Initialising a root is not the gate's

`terraform validate` needs an initialised root: its providers and the modules
it calls. Initialising reaches the network, so it is a step run **before** the
gate, never inside a hook:

```text
terraform -chdir=<dir> init -backend=false
```

`-backend=false` is what keeps it credential-free: it fetches providers and
modules and never opens the state backend. Give it as a task-runner recipe
where the repository has a task runner, and as a comment beside the hook where
it has none. **A root that was not initialised is an environment failure, not
a finding** — the hook fails saying so, and the commit waits.

## Ansible

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
declared. The linter meets that test, and so does the first scanner below.
Three keys of the hosted entry override the upstream manifest's:

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

## Dockerfiles

```yaml
      - id: hadolint
        name: hadolint
        entry: hadolint
        language: system
        types: [dockerfile]
```

By name, **not** the container-image variant: that one needs a running
container daemon in whatever session is committing, which is a dependency on
the developer's machine state rather than on the repository.

Verified on a scratch tree holding a single Dockerfile, because the
repositories this set was drawn from have none.

## Scanning — a deliberate pair

```yaml
      - id: checkov
        name: checkov
        entry: uv run checkov --quiet --directory <dir>
        language: system
        files: ^<dir>/
        pass_filenames: false

      - id: trivy-config
        name: trivy config
        entry: trivy config --exit-code 1 --severity HIGH,CRITICAL <dir>
        language: system
        files: ^<dir>/
        pass_filenames: false
```

Two scanners on purpose: their rule sets overlap but neither contains the
other, and the cost of the second is one more pass over files already in cache.
The first runs through the lockfile that pins it; the second by name, from the
pinned toolchain. Where the repository tracks no lockfile, the first is
**hosted**, pinned by `rev:`, for the reason the Ansible linter is (above); the
second stays by name, because the toolchain supplies it:

```yaml
  - repo: https://github.com/bridgecrewio/checkov
    rev: <tag>
    hooks:
      - id: checkov
        entry: checkov --quiet --directory <dir>
        files: ^<dir>/
        pass_filenames: false
```

The hosted entry overrides two keys of the upstream manifest. **`entry:` is the
house command**, because upstream's scans the repository root, and a directory
given through `args:` would scan the root as well; what runs is still the
package installed from `rev:`. **`files:` is the project's path filter**,
because upstream's matches Terraform files only and would never fire on roles
or manifests. Upstream's exclusion of `.terraform/` stays unless the project
overrides it. No interpreter version is stated: the hook takes its default.

So a repository that tracks a lockfile runs both Python-borne scanners — the
Ansible linter and the first scanner — through its runner and never hosts them
a second time; a repository that pins nothing hosts both; and every
repository calls the second scanner and the Terraform trio by name.

**Where the first scanner's own bounds would move a pin the project's runtime
relies on, it goes in a dependency group of its own**, declared conflicting
with the development group so the lock resolves it apart:

```toml
[dependency-groups]
checkov = ["checkov"]

[tool.uv]
conflicts = [[{ group = "checkov" }, { group = "dev" }]]
```

```yaml
        entry: uv run --isolated --only-group checkov checkov --quiet --directory <dir>
```

Without the `conflicts` declaration the lock resolves the group jointly with
the rest, and the pin moves anyway; the isolated run only keeps the scanner
out of the project's environment, not out of its resolution. A group made for
another reason than a bound — two packages writing the same module, say —
needs the isolated run and not the declaration. Where what the scanner moves
is a package nothing at runtime uses, it stays in the development group.

**Ansible content carries both scanners**, though they read it differently.
The first reads roles wherever they sit. The second reads Ansible through a
playbook — the playbook and the roles it applies — and nothing in a collection
of roles alone: measured, a tree holding a playbook that applies a role, each
carrying a misconfiguration, raised findings in both and failed the gate,
while the role's tasks file alone detected no configuration file and passed.
In a roles-only repository the second hook is therefore inert, accepted
because the first reads the content and the second starts reading the day a
playbook is tracked. That is what separates it from a compose file, which
neither scanner reads at all.

**`--exit-code 1` is what makes the second one a gate.** Without it the scan
prints its findings and exits 0 — measured, on a tree raising five HIGH
findings: the hook reports `Passed` and the commit goes through. The first
scanner exits non-zero on a finding by itself and needs no such flag. A
severity filter is not an exit condition, and a scanner that only narrates is
worse than no scanner, because the configuration says the gate is there.

**A finding both raise is suppressed where it was raised, never in the other
tool, and always with a reason** — an inline skip comment naming the rule id
for the first, an ignore-file entry with a comment line for the second.
Suppressing in the wrong tool leaves the finding live in the other and makes
the pair look like it disagrees with itself; suppressing in both hides which
scanner actually had the opinion.

**Where an inline skip cannot attach to the construct, it goes in the
scanner's configuration file** — the first scanner does not read one on a task
`block:`. Write the reason in a comment above the entry, since a skip in a
configuration file reaches every file the scanner reads, and remove it when
the inline form works.

A repository with infrastructure signals but no pinned toolchain above it runs
the container-image form of the second scanner instead. That is the recorded
fallback, not the default.

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

## Not in the house set

A compose-file syntax check. Where a project runs one it is the project's, and
convergence leaves it alone.
