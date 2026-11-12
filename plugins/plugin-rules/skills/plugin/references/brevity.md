---
paths:
  - "**/skills/*/references/*.md"
---

# Brief rules, split by topic

Binds conventions plugins only; a plugin that operates a tool is not held to it.

- **Cover a single topic per file, stated tersely**: imperatives over prose,
  no throat-clearing. Rule files are loaded into an agent's context on demand,
  so every word costs attention.
- **Split a file that spans distinct topics** into separate topic files behind
  the same router skill, and update the router's index. Do not pad it further:
  an agent reading one topic should not pay for the others.
