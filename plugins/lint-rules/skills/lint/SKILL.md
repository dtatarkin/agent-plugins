---
name: lint
description: The house lint standard — deriving a repository's checks from its signals, the canonical hook entries per language and stack, version pinning under a release-age cooldown, how a local hook resolves its tool, and when a whole repository is brought into line. Load when writing or changing a pre-commit configuration or a linter's own configuration file, or when asked to converge a repository's quality gates.
---

# Lint rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change, then follow them.

Start with `applying.md`: it carries the signals table that says which of the
others apply.

| You are doing… | Read |
|------------------|------|
| Any lint work — the procedure, the signals, when to converge | `references/applying.md` |
| Pinning or bumping hook versions | `references/versions.md` |
| Deciding when a check runs and what it is handed | `references/stages.md` |
| The set every repository runs — hygiene, secrets, spelling, justfiles, nix | `references/baseline.md` |
| A repository with a Python project file or any Python source | `references/python.md` |
| YAML, TOML or markdown | `references/markup.md` |
| Shell scripts | `references/shell.md` |
| Terraform, Ansible, Dockerfiles, compose or Kubernetes manifests | `references/infra.md` |
| A web package with a package manager's lockfile | `references/web.md` |
| A dbt project | `references/data.md` |
| GitHub Actions workflows | `references/ci.md` |
| Agent plugin manifests — portable or Claude | `references/agent-plugins.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
