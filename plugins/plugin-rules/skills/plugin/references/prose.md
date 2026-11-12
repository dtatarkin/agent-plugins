---
paths:
  - "**/skills/*/references/*.md"
---

# Tool-neutral, consumer-free prose

Binds conventions plugins only; a plugin that operates a tool is not held to it.

- **Write prose that reads correctly outside any specific agent tool.** A rule
  file outlives the host it was first loaded in, and is read in hosts its
  author never tried.
- **Never refer to how the file itself is loaded.** The mechanism changes; the
  rule does not.
- **Mention no skills, plugins, marketplaces or agent products** unless they
  are the file's subject. A file whose subject is the plugin format may name
  that format, its files and the hosts that read them.
- **Name no consuming project; describe consumers generically.** A rule that
  names its consumer cannot be reused elsewhere, and leaks the consumer to
  every other reader.
- **State each rule's rationale inline**, so the file stands on its own when
  it is read without its neighbours.
- **Keep frontmatter to loading metadata.** A rule file may carry keys a
  harness reads to decide when to load it, such as `paths:` globs. Put nothing
  else there and no rule text: a host that does not understand the
  frontmatter ignores it, so the file must read correctly without it.
