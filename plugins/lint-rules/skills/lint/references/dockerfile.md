---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/.hadolint.yaml"
---

# Dockerfiles

Signal: a `Dockerfile`.

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
