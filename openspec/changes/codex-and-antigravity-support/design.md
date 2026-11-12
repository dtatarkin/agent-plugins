# Design

## Context

See proposal.md for why. What the tree and the hosts hold today:

- Nine plugin directories under `plugins/`. Each carries a root `plugin.json`
  (Agent Plugins 1.0) and a `.claude-plugin/plugin.json`, held equal by
  `tests/plugins/test_portable_manifests.py`. Only `lint-rules` and
  `just-rules` ship hooks: `hooks/hooks.json`, exec form, command
  `${CLAUDE_PLUGIN_ROOT}/hooks/run-checker`, matcher `Edit|Write` with `if:
  Edit(...)` / `Write(...)` filters, plus `SessionStart`, `Stop` and
  `SubagentStop`. `run-checker` exits silently when its checker is not on
  `PATH`, and its `SessionStart` notice speaks only when the checker is
  missing.
- `.claude-plugin/marketplace.json` lists all nine, `source:
  "./plugins/<name>"`, in this order: python, logging, lint, clickhouse,
  django, just, metabase, redis, plugin (each `-rules`).
  `tests/plugins/test_marketplace_descriptions.py` is the pattern for a
  marketplace test.
- `.agents/plugins/marketplace.json` is `{"name": "agent-plugins", "plugins":
  []}`. The bootstrap change left its validation to the change that lists the
  first plugins for Codex, which is this one; Codex has no validator verb, so
  the measured install is that validation.
- lint-rules' agent-plugins topic says other hosts' marketplace files, such as
  those under `.agents/`, derive no lint check. The baseline `check-json` hook
  parses the file. No `.pre-commit-config.yaml` change is needed.
- `docs/` does not exist. The README has a Claude Code install block and the
  sentence "The Codex marketplace file (`.agents/plugins/marketplace.json`)
  lists nothing yet."

Codex 0.167.2 (`codex`), read-only exploration:

- Verbs: `codex plugin marketplace add <SOURCE>` (a local path,
  `owner/repo[@ref]`, or an HTTPS or SSH Git URL; `--json`), `codex plugin add
  PLUGIN@MARKETPLACE [--json]`, `codex plugin list [--available] [--json]`,
  `codex plugin marketplace list --json`. No validate verb.
- Its own marketplaces (in its user configuration's temporary directory) have
  the top level `{name, interface: {displayName}, plugins}` and entries of
  exactly `name`, `source: {source: "local", path: "./plugins/<name>"}`,
  `policy: {installation: "AVAILABLE", authentication: "ON_INSTALL"}` and
  `category` (values in use: Productivity, Coding, Research, Design,
  Lifestyle).
- The binary names plugin manifests in the order `.codex-plugin/plugin.json`,
  `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, then a root
  `plugin.json` with an Agent Plugins `$schema`, and marketplace files both
  under `.agents/plugins/` and `.claude-plugin/`. Which marketplace file wins
  when both exist is not known statically.
- Codex is hook-capable: it knows `hooks/hooks.json` and sets
  `CLAUDE_PLUGIN_ROOT`; the `hooks` feature is on; `codex exec` has
  `--dangerously-bypass-hook-trust`, so plugin hooks are probably gated by a
  trust step. Installed plugins are copied into its plugin cache.

Antigravity CLI 1.5.7 (`agy`), read-only exploration:

- Verbs: `agy plugin install <target>` (a directory, or
  `plugin@marketplace`), `list [--json]`, `validate [path] [--strict]
  [--json]`, `uninstall`, `enable`, `disable`, `import`, `link`. No
  marketplace-add verb and no Git or URL install target.
- `agy plugin validate plugins/<name> --strict` passes on `python-rules` and
  `lint-rules`, and warns on `lint-rules` that `hooks/hooks.json` is never
  loaded because plugin hooks are read only from a `hooks.json` at the plugin
  root. It notes an Agent Plugins `$schema` manifest loads as an Agent Plugins
  plugin only under the `enable-agent-plugins-spec` flag, otherwise as a
  native plugin.
- Its changelog says some installs are symbolic links, that the install
  summary names each skill and hook installed and the folder installed to, and
  that plugin hooks get `PLUGIN_ROOT`, not `CLAUDE_PLUGIN_ROOT`. `agy` can
  update itself.

Both hosts are signed in (Codex through ChatGPT; `agy models` succeeds).
`lint-lint` and `just-lint` are on `PATH` on the measuring machine.

## Goals / Non-Goals

**Goals:**

- Codex and the Antigravity CLI each install a plugin by the README's block
  (local-clone form here) and run one of its skills, with the result committed.
- The Codex marketplace cannot drift from the Claude Code marketplace
  unnoticed.
- The `agy` subdirectory question is answered by measurement.

**Non-Goals:**

- The install from GitHub in either host: it needs the repository public and
  is recorded in the same file afterwards.
- Making hooks work, or stop, in Codex or `agy`.
- A host validator hook for `.agents/plugins/marketplace.json`.
- Declaring `agy` in the machine's package set (an owner follow-up outside
  this repository).

## Decisions

### D1. Binding decisions this change inherits

- The supported hosts are Claude Code, Codex and the Antigravity CLI; OpenCode,
  Copilot CLI and Cursor are not.
- Both hosts were installed and signed in by the owner before the change. The
  runs use the installed `agy` 1.5.7 and `codex` 0.167.2.
- The measurement runs from local paths: a local marketplace for Codex, and
  `agy plugin install <clone>/plugins/<name>` for `agy`. The GitHub-URL forms
  wait until the repository is public.
- A host that needs a third manifest stops the change: the manifest is not
  added (see D9).
- Hooks are supported in Claude Code only. Hooks found loading, firing or
  failing in Codex or `agy` are recorded and left as they are.
- The record is a committed `docs/host-support.md`, which the `host-support`
  spec points to and which the later GitHub installs also write.
- The test installs stay in Codex and `agy` after the record is made; nothing
  is uninstalled.
- `.agents/plugins/marketplace.json` lists every plugin under `plugins/`,
  `plugin-rules` included, and a test holds its names and paths equal to the
  Claude marketplace's.
- Artifacts, the record, the README and commit messages name no private
  repository and no plugin kept outside this repository; the private-names
  guard checks every commit.

### D2. The Codex marketplace file

```json
{
  "name": "agent-plugins",
  "interface": { "displayName": "Agent Plugins" },
  "plugins": [
    {
      "name": "python-rules",
      "source": { "source": "local", "path": "./plugins/python-rules" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Coding"
    }
  ]
}
```

Nine entries in the Claude marketplace's order, written out as above (two-space
indentation, one key per line as `json.dumps(indent=2)` gives, final newline).
The shape is copied from the marketplaces Codex ships, the only format
reference available; no descriptions, because Codex's entries carry none and
read them from the plugin. `category` is a Codex label (`Coding`), not the
Claude file's `conventions`, which also lets the measurement tell the two
files apart (D5). Alternative: one shared file for both hosts — rejected, the
formats differ (`source` is a string in one and an object in the other).

### D3. The test

`tests/plugins/test_agents_marketplace.py`, in the style of
`test_marketplace_descriptions.py` (module docstring stating what drift it
catches, `REPO_ROOT`, classes of tests, parametrized ids naming the plugin):

- the ordered list of `(name, source.path)` of the Codex file equals the
  ordered `(name, source)` of the Claude file;
- the set of names equals the set of directories under `plugins/`;
- every entry's `source.source` is `local`.

Each failing assertion names the plugin or directory. It holds the
"Codex marketplace lists every plugin" requirement.

### D4. Which plugins are installed

`python-rules` (the skill run) and `lint-rules` (the hooks observation) in each
host. Not all nine: fewer test installs left behind, and `codex plugin list
--available --json` still shows whether all nine entries were read.

### D5. Codex measurement

From the main checkout (`<clone>`) on the change's branch, in order:

1. `codex --version`.
2. `codex plugin marketplace add <clone> --json`, then `codex plugin
   marketplace list --json`.
3. `codex plugin list --available --json`: all nine listed? Which file was
   read — an entry showing `category` `Coding` or the display name `Agent
   Plugins` means the `.agents` file; `conventions` means the Claude file.
4. `codex plugin add python-rules@agent-plugins --json` and the same for
   `lint-rules`; note where the plugin landed (cache folder, relative to
   Codex's configuration directory) and, if observable, which manifest it read.
5. Skill run (D7).
6. Hooks (D8).

If Codex reads the Claude file instead of the `.agents` file, that is recorded,
not fixed. If an install fails on the marketplace file's format, fix the file
(D2 is reversible), re-run the test, and re-measure; record the final form.

### D6. Antigravity CLI measurement

From the same clone:

1. `agy --version` (again after the last step; record the version that ran).
2. `agy plugin validate <clone>/plugins/python-rules --strict --json` and the
   same for `lint-rules`.
3. `agy plugin install <clone>/plugins/python-rules`, then `lint-rules`; keep
   the install summary (skills and hooks named, folder installed to).
4. The subdirectory answer: inspect the installed folder — does it hold only
   that plugin's files (no sibling plugin, no repository root files)? Is it a
   copy or a symbolic link into the clone? Which manifest mode (Agent Plugins
   or native) does `agy plugin list --json` or the summary report?
5. Skill run (D7).
6. Hooks (D8).

### D7. The skill run

One print-mode prompt per host, in an empty scratch directory outside the
repository, read-only where the host allows:

- Codex: `codex exec --skip-git-repo-check --ephemeral -s read-only -C
  <scratch> --json "<prompt>"`.
- `agy`: `agy -p "<prompt>" --output-format json`, run from `<scratch>`, in
  `--mode plan` if that keeps it from editing.

The prompt asks for something only the `python-rules` skill's topic files
answer, naming the skill as the host lists it (for example: "Use the python
skill from the python-rules plugin: what do its rules say about where
configuration is read? Quote the topic file you read."). The run succeeds when
the transcript shows the host loading the plugin's `SKILL.md` or a topic file
and answering from it. The record gives the command form, the prompt, and a
short paraphrase of the outcome, not the transcript.

### D8. The hooks observation

With `lint-rules` installed, look in each host's run for hook activity: the
install summary, the `--json` event stream of the skill run, and, in Codex,
any hook-trust prompt or refusal. If neither shows anything, run one more
print-mode prompt in the scratch directory that edits a
`.pre-commit-config.yaml` there, and look for a lint-lint finding or hook
event. Do not pass `--dangerously-bypass-hook-trust`. Record one of: not
loaded, loaded but untrusted, fired (what it did), failed (how). Change
nothing in the hooks.

### D9. Stop condition

If either host refuses a plugin for want of a third manifest (for example a
Codex error naming `.codex-plugin/plugin.json` with no valid Agent Plugin
manifest found), do not add one: write the host's scrubbed error under
"Findings" at the end of this design.md, leave the task unticked, and end the
turn reporting the stop. Any other failure is recorded in the record, and the
change goes on.

### D10. The record, `docs/host-support.md`

One file, created by the Codex section and completed by the `agy` section:

- An opening line on what it is: each supported host's install run once, with
  its result.
- Claude Code: a short note that it is the plugins' primary host and its
  GitHub install is recorded once the repository is public.
- One section per host, Codex and Antigravity CLI, each with: host version;
  date; install form run, with `<clone>` for the clone; source (local clone);
  outcome; which marketplace file and manifest the host read, where
  observable; for `agy`, the subdirectory answer (only that plugin installed;
  copy or link); the skill run (command form, prompt, outcome); hooks
  behaviour; that the test installs were left installed.
- In each section a line "Install from GitHub: not yet run; recorded once the
  repository is public."

It names no absolute path, home directory or user name: the clone is
`<clone>`, and a host folder is named by its role ("Codex's plugin cache",
"`agy`'s plugin folder"), never by a path.
It does not name roadmap slots or any private repository.

### D11. The README

- Replace "The Codex marketplace file … lists nothing yet." with two install
  blocks after the Claude Code one:
  - "Install in Codex": `codex plugin marketplace add dtatarkin/agent-plugins`
    then `codex plugin add <name>@agent-plugins`.
  - "Install in the Antigravity CLI": `git clone
    https://github.com/dtatarkin/agent-plugins` then `agy plugin install
    agent-plugins/plugins/<name>`, with one sentence on whether the clone must
    stay in place (from the record's subdirectory answer).
- One sentence where the README describes the hooks (the plugin list and
  "Install the checkers"): hooks run in Claude Code only; what they do in the
  other hosts is in `docs/host-support.md`.
- A pointer to `docs/host-support.md` as the record of each host's install.

The blocks give the public GitHub forms; the record says the local-clone form
is what was run.

## House rules

- **python-rules**: the new test follows its testing topic (layout under
  `tests/plugins/`, plain asserts, parametrized ids) and comments topic
  (module docstring stating the drift caught).
- **plugin-rules**: a marketplace manifest is edited. Its manifest-validation
  topic (parse before commit) is attached by path only to `.claude-plugin/`
  files; the `.agents` file is held to it through this repository's AGENTS.md
  table, and `check-json` parses it. No plugin manifest, skill or hook changes.
- **lint-rules**, **just-rules**: not touched (no lint configuration, no
  justfile).

None broken.

## Risks / Trade-offs

- [Codex reads `.claude-plugin/marketplace.json` rather than the `.agents`
  file for a repository carrying both] → the `.agents` file would be unused
  by Codex; recorded, not fixed, and the GitHub install later shows the same.
- [Codex runs `lint-rules`' hooks: it knows `hooks/hooks.json` and sets
  `CLAUDE_PLUGIN_ROOT`; the `Edit|Write` matcher and `if:` filters name Claude
  Code tools] → recorded; the README promises hooks in Claude Code only.
- [`agy` installs a local directory as a link into the clone] → the README's
  Antigravity block says the clone must stay.
- [A host updates itself before or during the runs] → the version is read
  before and after, and the record names the one that ran.
- [Host output carries absolute paths] → scrubbed to `<clone>` before writing;
  the private-names guard is a second check, not the first.
- [The skill run answers from general knowledge without loading the skill] →
  the prompt asks for the topic file's own wording and the run counts only
  when the transcript shows the file being read.

## Assumptions

- A1. The pinned host versions are those the record names: `codex` 0.167.2
  and `agy` 1.5.7, unless a host updated before the runs, in which case the
  version that ran is recorded. Nothing in this repository pins them.
- A2. The local marketplace registered in Codex is the main checkout, which
  stays at the same path after the change lands; the record writes it as
  `<clone>`.
- A3. Host state written by the installs (Codex's configuration and plugin
  cache, `agy`'s plugin folder) is outside the repository and stays.
- A4. Skill names may be namespaced differently per host (`python-rules:python`
  or `python`); the skill run uses whatever the host lists.
- A5. The Codex section (tasks 2) creates `docs/host-support.md` with both
  host sections, the Antigravity one marked "not yet measured"; the `agy`
  section (tasks 3) fills it. The README section (tasks 4) reads the
  subdirectory answer and the hooks behaviour from that file, not from
  memory.
- A6. A stop under D9 is recorded under "Findings" below; with no such entry,
  no host needed a third manifest.
- A7. Codex's hooks outcome is read from its app server: `plugin/read` for
  `lint-rules` and `hooks/list` for a working directory, which list a plugin's
  hooks with their trust status when Codex loads them. Both were empty, so the
  record says "not loaded" rather than "untrusted"; a later Codex release may
  load them, which the GitHub install would show.
- A8. Which marketplace file and which manifest Codex reads was settled by
  probes on a scratch copy of the files under an isolated Codex configuration
  directory, so the only additions to the owner's Codex configuration are the
  `agent-plugins` marketplace and the two test installs.

## Findings

None yet.
