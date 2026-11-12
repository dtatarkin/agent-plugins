---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.yamllint"
  - "**/.yamllint.yaml"
  - "**/.yamllint.yml"
  - "**/.taplo.toml"
  - "**/taplo.toml"
  - "**/.rumdl.toml"
---

# Markup

Signal: any YAML, TOML or markdown file — in practice, every repository.

JSON is covered by the hygiene set's parse check in the baseline topic and
needs nothing here.

## YAML

```yaml
  - repo: https://github.com/adrienverge/yamllint
    hooks:
      - id: yamllint
        args: [--strict]
```

`--strict` is not a default and must be passed: without it warnings pass the
gate, and a gate that reports without blocking is documentation, not a gate.

House configuration:

```yaml
extends: default
rules:
  document-start: disable
  line-length:
    max: 120
```

`document-start` is disabled because the file types this rule set meets most
often — hook configurations, generated metadata — do not carry the leading
marker, and requiring it would mean editing files the project did not write.
The width is the house width, the same one the markdown rules use; one number
across the repository so nobody has to remember which file type gets which.

**Where the repository holds Ansible content, the file gains six values:**

```yaml
extends: default
rules:
  document-start: disable
  line-length:
    max: 120
  comments:
    min-spaces-from-content: 1
  comments-indentation: false
  braces:
    min-spaces-inside: 0
    max-spaces-inside: 1
  octal-values:
    forbid-implicit-octal: true
    forbid-explicit-octal: true
```

The Ansible linter reads this same file and checks those six. On a mismatch it
reports the file as incompatible and turns its own fix mode off, on every run.
Its advice is to remove the custom file, which would take the house width and
the `document-start` exemption with it — so the file stays and meets the
linter instead. **The linter's own message outranks this list**: the values it
requires move between its releases, and the message names the ones it wants.

## TOML

```yaml
  - repo: https://github.com/ComPWA/taplo-pre-commit
    hooks:
      - id: taplo-format
```

The formatter only. The linter that ships beside it defaults to fetching schema
catalogues over the network, which belongs to the manual stage if anywhere, and
the formatter is what stops two people arguing about table ordering.

## Markdown

```yaml
  - repo: https://github.com/rvben/rumdl-pre-commit
    hooks:
      - id: rumdl-check
        args: [--fix]
```

One hook that lints **and** fixes. Use the check id with the fix flag rather
than the separate format id: the format id always exits zero, so it can only
rewrite, never block — a lint finding it cannot fix would pass silently.

House configuration:

```toml
[global]
exclude = ["<the repository's generated tree>", "<its frozen archive>"]

[MD013]
line_length = 120
tables = false
code_blocks = false

[MD041]
enabled = false
```

- **Width 120, with tables and code blocks exempt.** A table cannot be wrapped
  without breaking it, and wrapping a code block changes the code.
- **The first-line-heading rule is off.** Documents that are fragments of a
  larger whole legitimately start below the top level, and the rule cannot tell
  them from a file missing its title.
- **Generated and archived trees are excluded**, and *which* trees those are
  is the project's to name — the two placeholders above are the shape, not the
  paths. A generated file re-dirties itself the moment it is regenerated, so
  the gate fires on work nobody did. An archive of closed decisions is a frozen
  record, not maintained text: rewrapping it edits history for no reader. This
  `exclude` mirrors the hook configuration's own: name the generated files, not
  the directory around them, and confirm the list by the test the applying
  topic gives.

### The bare-address rewrite

The fixer **autolinks a bare e-mail address**, wrapping it in angle brackets.
That is correct markdown and usually wanted. Where it is not — a page that
lists addresses as data rather than as links — write the address in a code
span. Do this *before* the first run, not after: otherwise the fixer rewrites
prose the author did not intend to change, and the diff hides among the
formatting.

## Links

```yaml
  - repo: https://github.com/lycheeverse/lychee
    hooks:
      - id: lychee
        args: [--offline, --no-progress]
        types: [markdown]
```

A relative link that does not resolve fails the commit. This is its own
concern, beside markdown style: the markdown linter reads how a page is
written, and this reads whether what it points at is there.

- **`--offline`** limits the check to local targets, so a commit never waits
  on a remote host and never fails because one is down. Fragments stay
  unchecked, the tool's default, which leaves anchors to the markdown linter.
- **The args trap.** `args:` replaces upstream's, which are `--no-progress`
  alone, so the entry writes both flags; with `--offline` only, the progress
  output comes back.
- **`types: [markdown]`** narrows upstream's filter, which hands it every text
  file.
- **The hosted script hook**, not its system or container variants: the
  system one needs a declared install on every committing machine, the
  container one a running daemon at commit. The script hook installs the tool
  into its own checkout on the first run, which needs the network once; later
  runs reuse it.

A dead link inside a frozen archive is history, not a finding to fix: exclude
the archive on this hook, by the pattern the rewriting hooks already carry,
rather than rewrite it.

## Tools that leave

Retire, on sight, in a converged repository: a general-purpose formatter
driven through a package runner with no pin; a code formatter pointed at
markup, YAML or JSON, which have the house tools above; a second spell checker.
One tool per concern is what makes two repositories comparable.
