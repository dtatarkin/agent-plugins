---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.sqlfluff"
  - "**/.sqlfluffignore"
---

# Data

Signal: a dbt project file.

`<dir>` below is the repository's own project directory. **Order matters here
more than anywhere else in this standard**, and the reason is in the third
entry.

## SQL

```yaml
  - repo: local
    hooks:
      - id: sqlfluff-fix
        name: sqlfluff fix
        entry: uv run sqlfluff fix --show-lint-violations --processes 0 --disable-progress-bar
        language: system
        types: [sql]
```

Through the repository's lockfile and never from a hook repository: its
templater runs the project's own transformation tool with the project's own
adapter, so it needs exactly the versions the lockfile resolves. A second copy
resolves macros differently and reports violations that do not exist.

A repository that tracks no lockfile of its own calls it by name, and the
environment on the path — its consumer's — carries those versions:

```yaml
        entry: sqlfluff fix --show-lint-violations --processes 0 --disable-progress-bar
```

`--show-lint-violations` because the fixer otherwise repairs what it can and
says nothing about what it cannot. `--processes 0` uses every core;
`--disable-progress-bar` keeps a progress animation out of the hook's output,
where it is noise at best and confuses log capture at worst.

**Its dialect, templater and profile are facts of the repository**, not house
values. So is its ignore file.

## The manifest, then the checks that read it

```yaml
      - id: dbt-parse
        name: dbt parse
        entry: uv run dbt parse --project-dir <dir> --profiles-dir <dir>
        language: system
        types_or: [yaml, sql]
        pass_filenames: false

  - repo: https://github.com/dbt-checkpoint/dbt-checkpoint
    hooks:
      - id: check-model-has-description
        args: [--manifest, <dir>/target/manifest.json, --]
        files: ^<dir>/models/
      - id: check-model-has-tests
        args: [--test-cnt, "1", --manifest, <dir>/target/manifest.json, --]
        files: ^<dir>/models/
```

By name where no lockfile is tracked, for the same reason as above:

```yaml
        entry: dbt parse --project-dir <dir> --profiles-dir <dir>
```

**The parse hook comes first because it writes the manifest the other two
read.** Reverse them and the checks run against the previous commit's
manifest, so documentation or tests just taken away from a model it already
knows still look present. Measured: with the descriptions of eleven models
deleted, the prescribed order failed on all eleven and the reversed order
reported success and exited zero. That failure is invisible, which is why the
order is part of the standard rather than a matter of taste.

Two things the reversed order does *not* hide, also measured. A **missing**
manifest is loud — every check aborts with `Unable to load manifest file` and
fails — so the invisible case is a stale manifest, not an absent one. And a
newly added model is still caught by the description check even against a
stale manifest, since absent from the manifest reads the same as
undocumented; `check-model-has-tests` is the one that passes it silently.

Point the profiles at the **project's own directory**, never at a user's home:
a gate that depends on a file outside the repository passes on one machine and
fails on another, and the profile it finds there may point at production.

The trailing `--` separates the tool's own flags from the file list the hook
runner appends. **On these two hooks it changes nothing** — every option they
take is single-valued, so no flag can swallow a filename, and a run with and
without it gave identical results. It is kept because it costs nothing and
because sibling hooks in the same repository do take list-valued flags
(`--models`, `--global-flags`, `--cmd-flags`), where dropping it would matter.

Neither check declares these flags in its own manifest; both are argparse
options on the entry script. `--test-cnt 1` restates the tool's default, so
passing it makes the configuration state what it relies on instead of
inheriting it silently. `--manifest` is not a restatement: its default is
`target/manifest.json` resolved from the repository root, so wherever `<dir>`
is not the root the flag is **required** — omit it and the check aborts
looking for a manifest at the wrong path.
