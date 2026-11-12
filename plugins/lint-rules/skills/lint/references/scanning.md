---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.checkov.yaml"
  - "**/.checkov.yml"
  - "**/trivy.yaml"
  - "**/.trivyignore"
---

# Scanning — a deliberate pair

Signal: any `*.tf`, Ansible content, a helm chart (a `Chart.yaml`), or a
Kubernetes manifest (a YAML file with `apiVersion` and `kind` at its top
level).

**A compose file alone derives nothing**, because neither scanner of the pair
reads one, and a gate that reads nothing is not carried.

Throughout, `<dir>` is the repository's own layer directory.

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
**hosted**, pinned by `rev:`, for the reason the Ansible topic gives its
linter; the second stays by name, because the toolchain supplies it:

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

## Not in the house set

A compose-file syntax check. Where a project runs one it is the project's, and
convergence leaves it alone.
