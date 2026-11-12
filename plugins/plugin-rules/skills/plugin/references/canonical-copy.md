---
paths:
  - "**/skills/*/SKILL.md"
  - "**/skills/*/references/*.md"
---

# One canonical copy of each rule

Binds conventions plugins only; a plugin that operates a tool is not held to it.

- **Keep the text of a rule in exactly one topic file**,
  `skills/<domain>/references/<topic>.md` in its plugin, beside the domain's
  router skill. Two copies of a rule drift apart, and nobody can tell which
  one is meant.
- **Reference that file; never embed or duplicate its text** — not in a
  router skill, not in whatever attaches the rule on touch, not in a checker.
  When two skills or documents need the same rule, both point at the one file.
- **Attach the file itself, as it stands.** Store no copy of it anywhere, so
  there is nothing to keep in sync.
- **A checker's finding names the topic file and gives a one-line fix.** It
  does not restate the rule or its rationale; the file already does.
