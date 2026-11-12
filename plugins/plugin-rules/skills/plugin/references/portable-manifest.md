---
paths:
  - "**/plugin.json"
  - "**/.claude-plugin/plugin.json"
---

# The portable manifest

Binds every plugin meant for hosts beyond Claude Code, conventions or not. A
plugin for Claude Code alone is described by its `.claude-plugin/plugin.json`
and is not bound.

- **Carry two manifests**: the `.claude-plugin/plugin.json`, and beside it a
  root `plugin.json` in the Agent Plugins 1.0 format.
- **Declare `$schema` in the root one** as
  `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.
- **Use only the top-level fields that schema permits.** A field only Claude
  Code knows, such as `category`, stays out of the root `plugin.json`; the
  schema rejects it.
- **Declare the same name, version, description and author in both, and hold
  them equal** rather than deriving one from the other. Claude Code reads only
  the first, so a root manifest that drifts fails silently in every other host
  while Claude Code goes on working. Check the two agree before commit; hold
  it with a test where the repository has one, failing with the plugin and
  the field.
- **Parse the root `plugin.json` successfully before committing** any change
  that creates or edits it.
