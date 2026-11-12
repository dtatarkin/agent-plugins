---
paths:
  - "**/.claude-plugin/marketplace.json"
  - "**/.claude-plugin/plugin.json"
  - "**/hooks/hooks.json"
---

# Parse every manifest before commit

Binds every plugin, conventions or not.

- **Confirm the file parses before committing** any change that creates or
  edits the marketplace manifest `.claude-plugin/marketplace.json`, a plugin's
  `.claude-plugin/plugin.json`, or a plugin's `hooks/hooks.json`. A malformed
  file of any of these kinds fails plugin discovery silently rather than
  loudly, so nothing else will tell you.
