---
name: plugin
description: Agent plugin authoring conventions — one canonical copy of each rule in tool-neutral prose, a thin router skill per domain, brief rule files with `paths:` frontmatter, the two portable manifests, exec-form hooks, and parsing every manifest before commit. Load when writing or changing a plugin's skill, rule files, manifests or hooks.
---

# Plugin authoring rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change, then follow them.

| You are editing… | Read |
|------------------|------|
| Any plugin file — what the rules apply to | `references/scope.md` |
| Where a rule's text lives, and who may point at it | `references/canonical-copy.md` |
| The prose of a rule file, or its frontmatter | `references/prose.md` |
| A router skill — its description and topic index | `references/router.md` |
| The length and topic split of a rule file | `references/brevity.md` |
| A root `plugin.json` beside a `.claude-plugin/plugin.json` | `references/portable-manifest.md` |
| A plugin's `hooks/hooks.json` | `references/hooks.md` |
| Any manifest or hook file, before commit | `references/manifest-validation.md` |
| Whether a rule file attaches on touch, and how it says so | `references/paths.md` |
| A rule file's `paths:` frontmatter and imports | `references/always-on.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
