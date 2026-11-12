# Proposal

## Why

`agent-rules-authoring` and `rule-file-frontmatter` say how a plugin is
built. So far that has been a contract on paper only. An agent editing a
plugin's skill, rule files, manifests or hooks file sees none of it unless
it goes and reads the specs. `lint-standards` already has a working form,
the conventions plugin `lint-rules`, whose rules attach on touch. The
authoring requirements need the same: rules that reach the agent at the
moment it touches the files those rules govern, in any repository that
authors plugins.

## What Changes

- Add `plugin-rules`, a portable conventions plugin in two manifests: a root
  `plugin.json` in the Agent Plugins 1.0 format and a
  `.claude-plugin/plugin.json`.
  - Its router skill is `plugin-rules:plugin`.
  - It has one rule file per requirement of `agent-rules-authoring` and
    `rule-file-frontmatter`.
  - Each rule file carries `paths:` frontmatter naming the plugin files it
    governs: a skill's `SKILL.md` and references, plugin and marketplace
    manifests, and `hooks/hooks.json`. Wherever path-scoped attachment is
    set up, the rule attaches when such a file is read.
  - The manifest and hook rules bind every plugin. The router and rule-file
    rules bind conventions plugins only.
  - The plugin ships no hooks and no checker.
- List the plugin in `.claude-plugin/marketplace.json` under category
  `conventions`, in the README's plugin list, and among the portable plugins
  that the manifest test holds equal.
- Change `agent-rules-authoring`'s tool-neutral-prose requirement so that a
  rule file whose subject is the plugin format may name that format, its
  files and the hosts that read it. The plugin's own rules could not be
  written without this. A rule file still names no consuming project and
  never refers to how it itself is loaded.
- Add a requirement to `agent-rules-authoring` naming `plugin-rules` as the
  delivery of these requirements, as `lint-standards` names `lint-rules`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-rules-authoring`: the requirement "Rule files are tool-neutral,
  consumer-free prose" allows a rule file whose subject is the plugin format
  to name that format and its hosts. A new requirement delivers this spec's
  requirements and those of `rule-file-frontmatter` as the conventions
  plugin `plugin-rules`.

## Impact

- New: `plugins/plugin-rules/`, containing two manifests, a router skill and
  ten rule files.
- Edited:
  - `.claude-plugin/marketplace.json`: a new entry.
  - `tests/plugins/test_portable_manifests.py`: the plugin joins the
    portable set.
  - `README.md`: the plugin list.
- No code, no console script, no new dependency. The Codex marketplace file
  is unchanged.
- A repository that enables the plugin gets the router. A repository that
  also links the rule files into a harness's path-scoped rules gets them on
  touch.
