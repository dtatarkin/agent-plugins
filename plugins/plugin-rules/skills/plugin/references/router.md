---
paths:
  - "**/skills/*/SKILL.md"
  - "**/skills/*/references/*.md"
---

# One thin router skill per domain

Binds conventions plugins only; a plugin that operates a tool is not held to it.

- **Ship exactly one router skill per domain.** Never give a topic its own
  skill: a new topic lands as a new `references/<topic>.md` beside the router,
  plus an entry in its index.
- **Give it a sharp one-line description.** The description is the skill's
  only always-on context cost, so it must say precisely when to load it.
- **Limit the body to a topic index** that directs the agent to the topic
  files relevant to the task, and to nothing else.
- **Name each of the domain's own topic files relative to the skill**, as
  `references/<topic>.md`, never through a harness variable. Every host that
  resolves a skill's files from the skill's own directory then finds them.
- **Put a cross-domain pointer only in the index**, as a row held apart from
  the domain's own rows. A rule file names no plugin, so the router is the only
  place such a pointer can live. The row names the other domain and the files
  to read, and never restates what they say.
