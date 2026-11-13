# Host support

The record of each supported host's install of these plugins: each install run
once, with its result. `<clone>` stands for a local clone of this repository.

## Claude Code

Claude Code is the plugins' primary host: the plugins and their hooks are
written for it first.

### Install from GitHub

- Host version: Claude Code 2.1.322.
- Date: 2026-11-13.
- Source: GitHub, the public repository at the commit its plugin tags mark.
- Clean account: a configuration directory of its own holding no plugin and
  no marketplace beyond the built-in directory, and Git with no global or
  system configuration (so no credential helper), no token in the
  environment, prompts off and SSH disabled. The fetch therefore succeeded
  only because the repository is public.
- Install form run: the command-line equivalent of the README's `/plugin`
  lines:

  ```sh
  claude plugin marketplace add dtatarkin/agent-plugins
  claude plugin install python-rules@agent-plugins
  claude plugin install lint-rules@agent-plugins
  ```

- Outcome: Claude Code reported SSH not configured and cloned over HTTPS,
  validated the marketplace and added it as `agent-plugins` (source: GitHub);
  its clone lists all nine plugins. Both installs succeeded at user scope;
  `claude plugin list` shows `lint-rules` 0.5.0 and `python-rules` 0.1.0
  enabled, each copied into `plugins/cache/agent-plugins/<name>/<version>`
  of the configuration directory and recorded against the commit it came
  from.
- Checkers: the README's `uv tool install
  git+https://github.com/dtatarkin/agent-plugins`, run with uv's tool and
  cache directories of their own and the same anonymous Git, built
  `agent-plugins` 0.1.0 from that commit and installed the two executables
  `just-lint` and `lint-lint`; both answer `--help`. Only these, not any
  other copy, were on the `PATH` of the runs below.
- Skill run:
  - Command form: `claude -p "<prompt>" --model sonnet --output-format
    stream-json --verbose --include-hook-events --allowedTools Read`, in an
    empty scratch directory. A headless run needs the explicit `--model`.
  - Prompt: the same as for Codex and the Antigravity CLI below.
  - Outcome: Claude Code invoked the skill `python-rules:python`, read
    `references/config.md` from the plugin's folder in its cache, and
    answered by quoting that file's first rule (configuration validated
    through `pydantic-settings` settings classes, never bare `os.getenv`),
    naming the file. A first run without `--allowedTools Read` loaded the
    skill but was refused the topic file, because print mode's default
    permissions deny reading outside the working directory; it then
    declined to answer from memory.
- Hooks: fired. Both runs show `lint-rules`' `SessionStart` hook and its
  `Stop` hook, each exiting 0 with no output: with `lint-lint` on the `PATH`,
  the session-start notice stays silent. A further print-mode run, in
  `--permission-mode acceptEdits`, in a scratch Git repository holding a
  staged `pyproject.toml` and one Python file, wrote a `ruff.toml` lacking
  the house values. Its `PreToolUse` hook took the (empty) baseline; its
  `PostToolUse` hook returned two `config-value` findings for `ruff.toml`
  (`lint.ignore`, `lint.select`) as context introduced by the edit; its
  `Stop` hook blocked the turn once, naming the same two findings, and let
  it end on the second attempt. An earlier attempt to have the run write a
  `.pre-commit-config.yaml` instead was refused by Claude Code as a write to
  a sensitive file, after the `PreToolUse` hook had run.
- The test installs were left installed in that configuration.

## Codex

### Install from a local clone

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

### Install from GitHub

- Host version: `codex-cli` 0.167.2.
- Date: 2026-11-13.
- Source: GitHub, the public repository at the commit its plugin tags mark.
- Clean account: a Codex configuration directory of its own holding no
  plugin and no marketplace, and the same anonymous Git as for Claude Code.
- Install form run:

  ```sh
  codex plugin marketplace add dtatarkin/agent-plugins --json
  codex plugin add python-rules@agent-plugins --json
  codex plugin add lint-rules@agent-plugins --json
  ```

- Outcome: the marketplace was added under the name `agent-plugins`, as a
  `git` source naming the repository's HTTPS URL in Codex's configuration,
  cloned into `.tmp/marketplaces/agent-plugins` of the configuration
  directory. Both installs succeeded, each with the authentication policy
  `ON_INSTALL`, into `plugins/cache/agent-plugins/<name>/<version>`.
  `codex plugin list --available --json` shows `python-rules` and
  `lint-rules` installed and enabled from `agent-plugins`, and the other
  seven plugins available with the install policy `AVAILABLE`. Codex's app
  server reports `lint-rules` with the category `Coding` and the skill
  `lint-rules:lint`.
- Skill run:
  - Command form: the same as for the local clone, `codex exec
    --skip-git-repo-check --ephemeral -s read-only -C <scratch> --json
    "<prompt>"`, in an empty scratch directory, with standard input closed
    (otherwise `codex exec` waits to read more of the prompt from it).
  - Prompt: the same as for the local clone.
  - Outcome: Codex read the plugin's `SKILL.md` from its plugin cache, then
    `references/config.md`, and answered by quoting that file's first rule,
    naming the file.
- Hooks: not loaded, as with the local clone. The app server's `plugin/read`
  gives `lint-rules` an empty hook list, and its `hooks/list` is empty for
  both scratch directories, so no hook-trust step arose. The skill run's
  event stream held no hook event, nor did a second print-mode run, with
  `-s workspace-write`, that wrote a `.pre-commit-config.yaml` in a scratch
  directory; that run read the `lint` skill unprompted before writing the
  file. `--dangerously-bypass-hook-trust` was not passed.
- The test installs were left installed in that configuration.

## Antigravity CLI

### Install from a local clone

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

### Install from GitHub

- Host version: `agy` 1.5.7.
- Date: 2026-11-13.
- Source: GitHub, cloned over HTTPS from the public repository at the commit
  its plugin tags mark.
- Clean account: a home directory of its own, so `agy`'s `.gemini` folder
  starts with no plugin, and the same anonymous Git as for Claude Code.
- Install form run, the README's:

  ```sh
  git clone https://github.com/dtatarkin/agent-plugins
  agy plugin install agent-plugins/plugins/python-rules
  agy plugin install agent-plugins/plugins/lint-rules
  ```

- Outcome: the clone succeeded with no credentials. Both installs succeeded;
  each summary named one skill installed (`python`, `lint`) and no hook, and
  the folder installed to, `config/plugins/<name>` of `agy`'s `.gemini`
  folder. `agy plugin list --json` shows `python-rules` 0.1.0 and
  `lint-rules` 0.5.0 enabled, each with its one skill.
- Sign-in: not isolated. With its own home directory, `agy` still reached
  the owner's existing sign-in, which it keeps in the desktop session's
  keyring rather than under `.gemini`; only its configuration and plugin
  state were isolated.
- Skill run:
  - Command form: the same as for the local clone, `agy -p "<prompt>"
    --output-format json --mode plan`, run from an empty scratch directory.
  - Prompt: the same as for Codex.
  - Outcome: `agy` read the plugin's `SKILL.md` and then
    `references/config.md` from its plugin folder, and answered by quoting
    that file's opening and its first rule, naming the file.
- Hooks: not loaded, as with the local clone. The install summaries named no
  hook. A second print-mode run, in `--mode accept-edits`, wrote a
  `.pre-commit-config.yaml` in a scratch directory with no hook step, and
  `agy`'s log for that run reports no hooks loaded from any `hooks.json`.
- The test installs were left installed in that configuration.
