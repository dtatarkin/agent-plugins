---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.tflint.hcl"
---

# Terraform

Signal: any `*.tf`.

Throughout, `<dir>` is the repository's own layer directory. **The directory is
the project's, the rest of the entry is the standard's.**

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

## Several directories

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

## Initialising a root is not the gate's

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
