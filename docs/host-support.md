# Host support

What each supported host does with these plugins, as last verified. `<clone>`
stands for a local clone of this repository. The commands and observations of
each run are kept in the change that made it, or in the commit that recorded
it.

| | Claude Code | Codex | Antigravity CLI |
|---|---|---|---|
| Verified on | 2.1.322, 2026-11-13 | 0.167.2, 2026-11-13 | 1.5.7, 2026-11-13 |
| Install sources run | GitHub; local clone not run | local clone, GitHub | local clone, GitHub |
| Skills | load, namespaced: `python-rules:python` | load, namespaced: `python-rules:python` | load, not namespaced: `python` |
| Hooks | load and fire | not loaded | not loaded: read only from a root `hooks.json` |
| Plugin manifest read | not observed | root `plugin.json` | root `plugin.json`, as a native plugin |
| Marketplace file read | `.claude-plugin/marketplace.json`, its only form | `.agents/plugins/marketplace.json` | none: no marketplace verb |

## Quirks

### Claude Code

- The `lint-rules` hooks run as designed: `PreToolUse` takes a baseline,
  `PostToolUse` reports the findings an edit introduced, and `Stop` blocks
  the turn once while findings remain. With the checkers on the `PATH`, the
  `SessionStart` notice stays silent.
- A headless run, `claude -p`, needs an explicit `--model`, and
  `--allowedTools Read` to read a skill's topic files from the plugin cache:
  print mode's default permissions deny reads outside the working directory.
- Print mode refuses to write `.pre-commit-config.yaml`, as a sensitive file,
  after the `PreToolUse` hook has run.

### Codex

- An install copies the plugin, and only its files, into Codex's plugin
  cache, one folder per marketplace, plugin and version.
- With both marketplace files present, Codex reads only
  `.agents/plugins/marketplace.json`; without it, it falls back to
  `.claude-plugin/marketplace.json`. With both manifests present it reads the
  root `plugin.json`; without it, `.claude-plugin/plugin.json`. No third
  manifest is needed.
- Codex lists no hooks for `lint-rules`, so no hook-trust step arises.
- `codex exec` waits to read more of the prompt from standard input unless it
  is closed.

### Antigravity CLI

- `agy plugin install <clone>/plugins/<name>` installs that plugin alone. The
  installed folder is a copy holding only that plugin's files, with no
  sibling plugin and no file from the repository root, so the installed plugin
  does not depend on the clone staying in place.
- The root `plugin.json` declares Agent Plugins 1.0, which `agy` loads as such
  only under its `enable-agent-plugins-spec` flag; without it the plugins load
  as native plugins.
- `agy plugin validate --strict` fails on `lint-rules`, because its
  `hooks/hooks.json` is never loaded.
- A home directory of its own isolates `agy`'s configuration and plugins, but
  not its sign-in, which it keeps in the desktop session's keyring.
