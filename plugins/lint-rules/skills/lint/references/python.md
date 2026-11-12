---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/ruff.toml"
  - "**/.ruff.toml"
  - "**/mypy.ini"
  - "**/.mypy.ini"
  - "**/ty.toml"
---

# Python

Signal: a Python project file, or any `*.py`. Whether the repository tracks a
lockfile of its own is a second signal: it decides the two lockfile hooks and
the form of every local hook below.

## Loose scripts with no project file

A repository whose Python is loose scripts with no project file — an
umbrella's maintenance scripts, their dependencies declared inline or nowhere
— **has no consumer**. Nothing above or beside it carries the checkers or the
scripts' dependencies, so there is no environment for by-name hooks to run in,
and they would fail as an environment failure on every machine.

So it takes a root project file and lockfile declaring the scripts'
dependencies and the checkers, and its set arrives in the runner form, the
lockfile hooks with it. This is not a lockfile made for lint's sake: the
dependencies exist either way and were pinned nowhere. The project file is
where they are declared once, the lockfile is what pins them, and the hooks
follow from the lockfile as in any repository.

- **Inline script metadata leaves.** `uv run` on a script carrying a
  `# /// script` block resolves the block and ignores the project (measured,
  uv 0.13.1), so the lockfile would pin a set nothing runs. Move each block's
  entries into the project file. With no `[build-system]` uv installs nothing
  of the repository's own, and the scripts' directory stays a directory.
- **The checkers are scoped to the scripts' directory**, under the boundary
  rule of the type-checking section: most of such a tree is usually
  sub-repositories.
- **A root configuration table reaches past the scripts.** A tool that takes
  the closest table up the tree crosses repository boundaries, so sub-repository
  Python that declares none of its own is read under the root's. Say so in a
  comment beside the table.

## Lint and format

```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
        types_or: [python, pyi, jupyter]
```

Use `ruff-check`, never the legacy alias that upstream keeps for
backwards-compatibility; two repositories writing the same hook under two ids
is exactly the drift this standard exists to remove.

**`ruff-format` must be narrowed.** Upstream's default type list includes
markdown as well as Python, so left alone it reformats markdown files — which
belong to the markup topic's tool. One tool per concern means the narrowing is
part of the entry, not a project's taste.

### The security rules

`select` gains `S`. That replaces a separate security linter: the rules are the
same body of checks, and one tool reading the file once is faster and has no
second configuration to drift.

Two are ignored as house policy:

```toml
[tool.ruff.lint]
extend-select = ["S"]
ignore = ["S603", "S607"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S105", "S106", "S107"]
```

- **`S603` and `S607`** flag calling a subprocess, and calling one by name
  rather than by absolute path. Calling tools by name is a standing contract
  here — it is how a hook finds a pinned toolchain without reaching outside its
  own repository — so these two fire on correct code, every time, and an
  always-wrong rule teaches people to ignore the rest.
- **`S101`** is the assert check, and tests are made of asserts.
- **`S105`, `S106` and `S107`** are the hardcoded-credential checks, ignored
  under `tests/**` and nowhere else. They match on a *name* — a variable, an
  argument or a default called password, secret or token — never on a value,
  and a test fixture is made of those the way a test is made of asserts. The
  baseline's secret scan reads `tests/` like any other path and stays the gate
  for a real credential. An inline suppression the ignore makes redundant is
  removed, not kept: the linter's own fix drops the directive and leaves the
  reason after it as a comment.

Any other `S` finding is fixed, or suppressed **inline with a reason**. A
blanket ignore added to the configuration to make a run pass silently disables
the rule for code not yet written.

## Packaging

```yaml
  - repo: https://github.com/astral-sh/uv-pre-commit
    hooks:
      - id: uv-lock

  - repo: https://github.com/abravalheri/validate-pyproject
    hooks:
      - id: validate-pyproject
```

`uv-lock` keeps the lockfile in step with the project file — a lockfile that
lags is a build that works only on the machine that last resolved it.

**It is carried only where the repository tracks a lockfile**, and so is the
dependency audit below. A repository that tracks none carries neither: the
first would write a lockfile nobody tracks, or re-lock a workspace root that
is another repository's file, and the second would export one.

The project-file validator ships its own extra dependencies in its manifest.
Do **not** restate them in the entry: supplying `additional_dependencies:`
*replaces* the manifest's list rather than extending it, which is how a
configuration ends up validating against fewer schemas than it did before
anyone touched it.

### The lockfile cooldown

A tracked lockfile resolves under the same seven-day cooldown as the hook
pins, **stated in the project file**:

```toml
[tool.uv]
exclude-newer = "7 days"
```

Never a flag on the upgrade command. `uv-lock` runs a plain lock, and a plain
lock removes a cutoff the command line gave — so the commit that carries the
upgrade also undoes its record, and the hook fails once on the way for a file
it modified. In the project file the value binds every resolution, adding a
dependency as much as upgrading one. That is the intent: a release less than a
week old is where a broken or compromised upload is still live. The lockfile
records the span and not a date, so a re-lock on a later day changes nothing.

**A fix younger than the cooldown is admitted by a line**, for the same
reason:

```toml
[tool.uv]
exclude-newer = "7 days"
# <advisory id>: fixed in <release>. Remove once that release is a week old.
exclude-newer-package = { <package> = "0 days" }
```

One package, the advisory named in the comment above the entry, and the entry
deleted once the release is older than the cooldown. A waiver nobody can see
is a policy nobody follows; this one is in the diff.

**Stating the cooldown for the first time can reopen an advisory.** A pin the
lockfile already holds that is younger than the cutoff is moved *back*. So
after the first lock, read the lockfile's diff, report each pin that moved,
and exempt the ones that were taken to close an advisory — before the lockfile
is committed.

**Only a workspace root's value is read.** A member's is ignored, which is the
lockfile signal again: the cutoff lives where the lockfile is tracked, and a
member has neither.

## Type checking — a deliberate pair

```yaml
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
        pass_filenames: false

      - id: ty
        name: ty
        entry: uv run ty check
        language: system
        types: [python]
        pass_filenames: false
```

**Both block. This is not redundancy, it is a transition being run in the
open.** The first is the reference gate — strict, and the only one of the two
with a plugin ecosystem, which a framework-heavy codebase needs. The second is
the fast second opinion and the likely successor. Running both now means the
day the successor takes over is a deletion, not a migration.

A false positive from either is suppressed with a reason. If the newer one
blocks too often to live with, it moves to the manual stage — it does not leave
the pair.

**Local, not a mirror repository.** A type checker needs the project's own
plugins and stub packages to see the code the way the project does; a hook
repository's isolated environment gets those only as hand-copied dependency
lists, which then drift from the lockfile silently. Running in the environment
the project is developed in is the whole point.

**Which form is the lockfile signal.** A repository that tracks a lockfile
takes the entries above, and its lockfile pins both checkers as development
dependencies. A repository that tracks none calls both by name:

```yaml
        entry: mypy
```

```yaml
        entry: ty check
```

Its hooks then run in whichever consumer's environment is on the path — the
workspace or the service the library is developed inside. So **the consumer's
lockfile carries what the checkers need in order to see the code**: the
library's optional extras, its stub packages. A checker that is red for want
of them is repaired in the consumer's environment, never by a suppression in
the library. Outside any consumer's environment the hook is an environment
failure, not a finding.

`pass_filenames: false` with a type filter: the checker reasons over the whole
program, so handing it only the changed files makes its findings depend on
which files you happened to touch. The type filter still keeps it inert on a
commit that contains no Python.

**Scope each checker so it cannot walk into a vendored sub-repository.** That
code is governed by its own repository, its dependencies are not installed
here, and the resulting unresolved-import storm buries every real finding.
Measured on one repository with two vendored members: 118 diagnostics
unscoped, 26 scoped — 92 of them noise from code the repository does not own.

How much of its *own* tree each checker covers is the project's call, and the
two need not agree: one may take source only while the other takes source and
tests. What is not optional is the boundary at a vendored member.

Put the scope wherever the tool reads it. A checker with a configuration
section takes it there. A checker with none takes path arguments in the entry:

```yaml
        entry: uv run ty check src tests
```

Scoping in the entry rather than by an exclude list is deliberate — it names
what *is* checked, so a new vendored member does not silently join the run.

## Dependency audit — on demand

```yaml
      - id: pip-audit
        name: pip-audit
        entry: bash -c 'uv export --no-hashes --no-emit-workspace --no-dev --quiet | uvx --quiet pip-audit --requirement /dev/stdin --disable-pip --no-deps --strict'
        language: system
        stages: [manual]
        always_run: true
        pass_filenames: false
```

Manual, because it reaches an advisory database over the network and a commit
must never wait on — or fail because of — a remote service. Carried only where
a lockfile is tracked: it audits what the lockfile resolves, and without one
there is nothing of this repository's to export.

The export pipe is the point of the entry: it audits **the set the lockfile
actually resolves**, not whatever the audit tool's own environment happens to
contain. Auditing the latter reports on a dependency tree nobody ships.

This entry is longer than the house line width, and the configuration file is
itself linted, so write it as a folded scalar (`entry: >-`) broken before the
pipe. The folded form joins the lines with a space and the command is
unchanged. A one-line entry copied verbatim from a topic is the first thing the
YAML gate fails on.

`--no-emit-workspace`, not `--no-emit-project`. The narrower flag drops only
the root project, so in a workspace every sibling member still exports as an
`-e ../member` line — and the audit tool cannot deduce a version from a path,
so it aborts with an error instead of reporting. The two flags are equivalent
in a repository that is not a workspace, so the wider one is the only one that
is right everywhere.
