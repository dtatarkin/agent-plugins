---
paths:
  - "**/skills/*/references/*.md"
---

# A scoped rule file never widens into an always-on rule

Binds conventions plugins only; a plugin that operates a tool is not held to it.

A harness loads a rule file without path scope, and anything a scoped file
imports, into every session unconditionally. One malformed file therefore
costs every session its full text. A rule file carrying `paths:`:

- **Gives a non-empty list of non-empty glob strings.**
- **Carries no other frontmatter key.**
- **Contains no import** — no line opening with `@` followed by a path.

A file without `paths:` is not held to this, imports included. Check it
before commit; hold it with a test where the repository has one, failing on
any violation with the file named, and seeing at least one scoped file so it
cannot pass vacuously.
