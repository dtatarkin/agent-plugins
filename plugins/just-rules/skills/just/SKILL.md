---
name: just
description: Justfile conventions — shared-module reuse, the module preamble, recipe attributes, comments and bodies, argument fidelity and recipe-to-recipe calls, and per-project entrypoint files. Load when writing or editing a justfile, a `.just`, or a `*.just` module.
---

# Justfile rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change, then follow them.

| You are editing… | Read |
|------------------|------|
| Any justfile — what the rules apply to | `references/scope.md` |
| Deciding whether to write a recipe at all | `references/reuse.md` |
| A reusable `*.just` module loaded with `mod` | `references/modules.md` |
| A recipe — attributes, comments, body, formatting | `references/recipes.md` |
| Recipe parameters, forwarding user args, calls between recipes | `references/arguments.md` |
| A project entrypoint `justfile` or its `.just` | `references/consumer.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
