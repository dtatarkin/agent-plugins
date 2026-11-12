---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.shellcheckrc"
---

# Shell

Signal: any `*.sh`, or a file carrying a shell shebang.

```yaml
  - repo: https://github.com/shellcheck-py/shellcheck-py
    hooks:
      - id: shellcheck
```

The packaged hook, not a local one: upstream ships the binary through the hook
repository, so the pin in `rev:` really does pin the checker.

Take its defaults. It already filters to shell by type — which is what catches
an extensionless script by its shebang, the case a path filter misses — and it
already runs serially, because that is how it follows a `source` from one file
into another.

**It skips zsh**, by its own exclusion. A repository with zsh scripts is not
covered by this hook and should not pretend otherwise; say so rather than
widening the filter, which only makes the checker report against the wrong
dialect.

Suppress a finding where the checker is wrong with a directive comment above
the line, naming the code and the reason. Never disable a code repository-wide
in a configuration file to make one script pass — that turns one known
exception into an unknown number of them.

Its repository publishes tags and no releases, so checking a pin's age reads
the tag's own date. The version topic says so.
