# Host support

The record of each supported host's install of these plugins: each install run
once, with its result. `<clone>` stands for a local clone of this repository.

## Claude Code

Claude Code is the plugins' primary host: the plugins and their hooks are
written for it first. Its install from GitHub is recorded here once the
repository is public.

## Codex

- Host version: `codex-cli` 0.167.2, read before and after the runs.
- Date: 2026-11-12.
- Source: a local clone of this repository.
- Install form run:

  ```sh
  codex plugin marketplace add <clone> --json
  codex plugin add python-rules@agent-plugins --json
  codex plugin add lint-rules@agent-plugins --json
  ```

- Outcome: the marketplace was added under the name `agent-plugins`;
  `codex plugin list --available --json` listed all nine plugins, each with
  the install policy `AVAILABLE` and the authentication policy `ON_INSTALL`;
  both installs succeeded, and `codex plugin list --json` shows `python-rules`
  and `lint-rules` installed and enabled from `agent-plugins`. Each plugin was
  copied, not linked, into Codex's plugin cache, one folder per marketplace,
  plugin and version; the copy holds only that plugin's files.
- Marketplace file read: `.agents/plugins/marketplace.json`. Codex reports the
  category `Coding`, which only that file gives. In a scratch copy carrying
  both marketplace files, with an isolated Codex configuration directory,
  Codex listed only the plugins of the `.agents` file; with that file
  removed, it listed those of `.claude-plugin/marketplace.json`.
- Manifest read: the root `plugin.json` (Agent Plugins 1.0). In a scratch copy
  whose two manifests gave different versions, Codex reported the root
  manifest's; with the root manifest removed, it reported
  `.claude-plugin/plugin.json`'s. No third manifest was needed.
- Skills: listed under the plugin's namespace, `python-rules:python` and
  `lint-rules:lint`.
- Skill run:
  - Command form: `codex exec --skip-git-repo-check --ephemeral -s read-only
    -C <scratch> --json "<prompt>"`, in an empty scratch directory outside any
    repository.
  - Prompt: "Use the python skill from the python-rules plugin: what do its
    rules say about where configuration is read? Quote the topic file you
    read, and name it."
  - Outcome: Codex read the plugin's `SKILL.md` from its plugin cache,
    followed the router to `references/config.md`, and answered by quoting
    that file's first rule (configuration validated through
    `pydantic-settings` settings classes, never bare `os.getenv`), naming the
    file.
- Hooks: not loaded. Codex lists no hooks for `lint-rules` (its plugin
  details give an empty hook list, and its hook listing for the scratch
  directory and for the clone is empty), so no hook-trust step arose. The
  skill run's event stream held no hook events, nor did a second print-mode
  run, with `-s workspace-write`, that wrote a `.pre-commit-config.yaml` in a
  scratch directory. `--dangerously-bypass-hook-trust` was not passed.
- The test installs were left installed, and the local marketplace left
  registered.
- Install from GitHub: not yet run; recorded once the repository is public.

## Antigravity CLI

- Host version: `agy` 1.5.7, read before and after the runs.
- Date: 2026-11-12.
- Source: a local clone of this repository.
- Validation run first:

  ```sh
  agy plugin validate <clone>/plugins/python-rules --strict --json
  agy plugin validate <clone>/plugins/lint-rules --strict --json
  ```

  `python-rules` passed, with notes only (no logo; how its manifest loads).
  `lint-rules` failed in strict mode on its one warning: `hooks/hooks.json` is
  never loaded, because `agy` reads plugin hooks only from a `hooks.json` at the
  plugin root.
- Install form run:

  ```sh
  agy plugin install <clone>/plugins/python-rules
  agy plugin install <clone>/plugins/lint-rules
  ```

- Outcome: both installs succeeded. Each summary named one skill installed
  (`python`, `lint`), no hook, and the folder installed to, inside `agy`'s
  plugin folder. `agy plugin list --json` shows both plugins enabled.
- Subdirectory answer: installing from a plugin's subdirectory of the clone
  installs that plugin alone. Its folder holds only that plugin's files, the
  same as the subdirectory's, with no sibling plugin and no file from the
  repository root. The folder is a copy, not a link: nothing in it points
  into the clone, so the installed plugin does not depend on the clone
  staying in place.
- Marketplace file read: none; `agy` installs from the plugin's directory and
  has no verb to add a local marketplace.
- Manifest read: the root `plugin.json`, as `agy plugin validate` reports.
  It declares the Agent Plugins 1.0 schema, which `agy` loads as an Agent
  Plugins plugin only under its `enable-agent-plugins-spec` flag. That flag
  was not set in `agy`'s configuration, so the plugins loaded as native
  plugins. No third manifest was needed.
- Skills: listed without the plugin's namespace, as `python` and `lint`.
- Skill run:
  - Command form: `agy -p "<prompt>" --output-format json --mode plan`, run
    from an empty scratch directory outside any repository.
  - Prompt: the same as for Codex.
  - Outcome: the conversation record shows `agy` reading the plugin's
    `SKILL.md` and then `references/config.md` from its plugin folder. It
    answered by quoting that file's first rule and naming the file. Plan mode
    added a planning instruction to the prompt, which `agy` set aside for a
    read-only question.
- Hooks: not loaded. The install summary named no hook. Neither the skill run
  nor a second print-mode run, in `--mode accept-edits`, that wrote a
  `.pre-commit-config.yaml` in a scratch directory held a hook step; at the
  start of that second run, `agy`'s log reported no hooks loaded from any
  `hooks.json`. That run read the `lint` skill unprompted before writing the
  file.
- The test installs were left installed.
- Install from GitHub: not yet run; recorded once the repository is public.
