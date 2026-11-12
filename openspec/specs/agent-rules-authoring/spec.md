# agent-rules-authoring Specification

## Purpose

How a rules plugin in this repository is built: one canonical copy of each
rule in tool-neutral prose, a thin router skill per domain, brief topic files,
manifests every supported host can read, and hooks that run without a shell —
so a rule stays reusable in any project and any host at near-zero idle context
cost.

## Requirements

### Requirement: Each rule has exactly one canonical copy

The text of a rule SHALL live in exactly one topic file,
`skills/<domain>/references/<topic>.md` in its plugin, beside the domain's
router skill. Router skills, whatever attaches a rule on touch, and checkers
SHALL reference that file and SHALL NOT embed or duplicate its text: what
attaches is the file itself as it stands, and a checker's finding names the
file and states only a one-line fix.

#### Scenario: A router skill surfaces a rule

- **WHEN** a router skill directs an agent to a rule
- **THEN** it names the `references/<topic>.md` file to read
- **AND** the skill body contains no copy of the rule text

#### Scenario: The same guidance is wanted in two places

- **WHEN** two skills or documents need the same rule
- **THEN** both point at the single topic file rather than duplicating it

#### Scenario: A rule is attached on touch

- **WHEN** an attachment delivers a rule into an agent's context
- **THEN** the text comes from the canonical topic file itself
- **AND** no copy of it is stored anywhere to be kept in sync

#### Scenario: A checker reports a broken rule

- **WHEN** a checker reports that a rule is broken
- **THEN** the finding names the `skills/<domain>/references/<topic>.md` file
  stating the rule
- **AND** gives a one-line fix without restating the rule's rationale

### Requirement: Rule files are tool-neutral, consumer-free prose

The prose of a topic file MUST read correctly outside any specific agent tool:
it SHALL NOT mention the loading mechanism (skills, plugins, marketplaces, or
any agent product) and SHALL NOT name any consuming project — consumers are
described generically. Each rule SHALL state its rationale inline so it stands
on its own. A rule file MAY carry frontmatter that a harness reads to decide
when to load it, such as `paths:` globs. That frontmatter is metadata, not
prose: it SHALL hold nothing but such loading keys, SHALL carry no rule text,
and SHALL be inert wherever it is not understood, so the file reads correctly
with the frontmatter ignored.

#### Scenario: A rule file is added or edited

- **WHEN** a rules file is written
- **THEN** its prose names no agent tool and no consuming project
- **AND** each rule's rationale is stated in the file itself

#### Scenario: A rule file carries loading metadata

- **WHEN** a rules file carries frontmatter telling a harness when to load it
- **THEN** the frontmatter holds only such loading keys and no rule text
- **AND** the file reads correctly with the frontmatter ignored

### Requirement: One thin router skill per domain

Each conventions plugin SHALL ship exactly one router skill for its domain.
The skill SHALL carry a sharp one-line description — its only always-on
context cost — and a body limited to a topic index directing the agent to the
relevant topic files. The index SHALL name each of the domain's own topic
files relative to the skill, as `references/<topic>.md`, and SHALL NOT reach
them through a harness variable, so every host that resolves a skill's files
from the skill's own directory finds them. Individual topics SHALL NOT get
their own skills. The index MAY additionally carry rows pointing at another
domain's rule files, held separately from the domain's own rows. Such a row is
the only place a cross-domain pointer may live, because a rule file names no
plugin; it SHALL name the domain and the files to read, and SHALL NOT restate
what they say.

#### Scenario: An agent works in a domain

- **WHEN** the router skill loads
- **THEN** the agent reads only the `references/` topic files relevant to the
  task at hand
- **AND** each is found relative to the skill's own directory, in any host

#### Scenario: A new topic is added to a domain

- **WHEN** a domain gains a new topic
- **THEN** it lands as a new `references/<topic>.md` beside the existing
  router skill plus an index entry in it, not as a new skill

#### Scenario: A domain's reader needs a rule that lives elsewhere

- **WHEN** a rule a domain's reader needs has moved to, or always belonged
  to, another domain
- **THEN** the pointer is a row in that router's index, set apart from the
  domain's own rows, naming the other domain and the files to read
- **AND** neither the router nor any rule file restates the rule

### Requirement: Rules stay brief and split by topic

Rule files are loaded into agent context on demand, so every word costs
attention. A topic file SHALL cover a single topic, stated tersely —
imperatives over prose, no throat-clearing. When a file grows to span distinct
topics, it SHALL be split into separate topic files behind the same router
skill rather than padded further.

#### Scenario: A topic file sprawls

- **WHEN** a rules file accumulates content spanning distinct topics
- **THEN** it is split into per-topic files and the router's index is updated

### Requirement: A portable plugin also carries an Agent Plugins manifest

A plugin meant for hosts beyond Claude Code SHALL carry two manifests. Beside
its `.claude-plugin/plugin.json` it SHALL carry a root `plugin.json` in the
Agent Plugins 1.0 format, declaring the same name, version, description and
author. Claude Code reads only the first, so the two are held equal rather
than one being derived from the other. The repository's manifest test names
which plugins are portable; this requirement does not.

#### Scenario: A portable plugin carries both manifests

- **WHEN** a plugin meant for hosts beyond Claude Code is shipped
- **THEN** its directory holds a root `plugin.json` and a
  `.claude-plugin/plugin.json`
- **AND** the root `plugin.json` declares `$schema` as
  `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`
- **AND** it uses only the top-level fields that schema permits, so a
  field only Claude Code knows, such as `category`, stays out of it

#### Scenario: The two manifests disagree

- **WHEN** the name, version, description or author of a root `plugin.json`
  differs from that of its plugin's `.claude-plugin/plugin.json`
- **THEN** the repository's tests fail, naming the plugin and the field

#### Scenario: A portable manifest is added or edited

- **WHEN** a plugin's root `plugin.json` is created or changed
- **THEN** the file SHALL be parsed successfully before the change is committed

#### Scenario: A plugin stays with Claude Code only

- **WHEN** a plugin is not meant for any host but Claude Code
- **THEN** this requirement does not bind it, and its
  `.claude-plugin/plugin.json` alone describes it

### Requirement: A plugin may ship hooks

A plugin MAY ship hooks in `hooks/hooks.json` at its root. Its hooks SHALL run
only in projects where the plugin is enabled, and each hook command SHALL
resolve to a script inside the plugin or to one of this repository's console
scripts. Each hook SHALL be declared in exec form — the command and its
arguments given separately — so that no shell, and no shell prefix a project
sets, stands between the harness and the command. Because a hook that fails
does so silently, a plugin's hooks SHALL be proven by observing their effect in
a running session, never inferred from the file's presence.

#### Scenario: A plugin with hooks is enabled

- **WHEN** a plugin shipping `hooks/hooks.json` is enabled in a project
- **THEN** its hooks run in that project's sessions, including their subagents,
  and in no project where the plugin is not enabled

#### Scenario: A project wraps shell commands in a prefix

- **WHEN** a plugin hook runs in a project whose settings route shell commands
  through a shell prefix
- **THEN** the hook's command runs directly, unwrapped, and its output reaches
  the harness unmixed with the prefix's

#### Scenario: A hook command does not resolve

- **WHEN** a hook names a command that is not installed on the machine
- **THEN** the failure is found by observing in a session that the hook's
  effect is missing, not assumed away because the file exists

#### Scenario: A hook is in shell form or names nothing that resolves

- **WHEN** a plugin's `hooks/hooks.json` declares a hook without separate
  arguments, or one whose command is neither a file inside the plugin nor a
  console script this repository installs
- **THEN** the repository's tests fail, naming the event and the command

### Requirement: Manifests are validated before commit

The marketplace manifest, every plugin manifest, and every plugin's
`hooks/hooks.json` SHALL be confirmed to parse before being committed, because
a malformed file of any of these kinds fails plugin discovery silently rather
than loudly.

#### Scenario: A manifest is added or edited

- **WHEN** `.claude-plugin/marketplace.json` or any `.claude-plugin/plugin.json`
  is created or changed
- **THEN** the file SHALL be parsed successfully before the change is committed

#### Scenario: A hook file is added or edited

- **WHEN** any plugin's `hooks/hooks.json` is created or changed
- **THEN** the file SHALL be parsed successfully before the change is committed
