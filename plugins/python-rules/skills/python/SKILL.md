---
name: python
description: General Python conventions and patterns — typing, configuration, command-line interfaces, error handling, services/use-cases, dependency injection, testing, file organization, comments. Load when writing Python code, independent of framework.
---

# Python rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change, then follow them.

| You are editing… | Read |
|------------------|------|
| Type hints, enums, structured returns | `references/typing.md` |
| Env/config loading | `references/config.md` |
| Command-line interfaces / entry points | `references/cli.md` |
| Error handling / raising vs returning failures | `references/error-handling.md` |
| Service / use-case modules | `references/services.md` |
| Dependency-injection wiring | `references/dependency-injection.md` |
| Tests | `references/testing.md` |
| Module / package layout | `references/file-organization.md` |
| Comments and docstrings | `references/comments.md` |

Some topics live in other domains, and this router points rather than repeats:

| You are editing… | Read |
|------------------|------|
| Which type checker runs, and the lint gates a Python repository wires | `lint-rules:lint` → its `applying.md` and `python.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
