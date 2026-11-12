# Spec Delta

## Purpose

Which agent hosts the plugins of this repository support, how a user installs
them in each, and the committed record that each host's install was run and
what it did.

## ADDED Requirements

### Requirement: Supported hosts

The supported hosts SHALL be Claude Code, Codex and the Antigravity CLI. The
README SHALL give one install block for each of them and for no other host.

#### Scenario: One block per supported host

- **WHEN** a reader looks for how to install a plugin in Claude Code, Codex or
  the Antigravity CLI
- **THEN** the README gives exactly one install block for that host, with the
  plugin's name as a placeholder

#### Scenario: Unsupported hosts get no install line

- **WHEN** the README is searched for an install line for OpenCode, Copilot CLI
  or Cursor
- **THEN** none is found

### Requirement: Codex marketplace lists every plugin

`.agents/plugins/marketplace.json` SHALL list every plugin under `plugins/`,
under the same names and the same relative paths, in the same order, as
`.claude-plugin/marketplace.json`, and a test SHALL hold that equality before
commit.

#### Scenario: A plugin added to one marketplace only

- **WHEN** a plugin is listed in the Claude Code marketplace but not in the
  Codex marketplace, or the other way round
- **THEN** the test fails naming that plugin

#### Scenario: A plugin directory listed in neither

- **WHEN** a directory under `plugins/` is listed in neither marketplace
- **THEN** the test fails naming that directory

#### Scenario: Paths disagree

- **WHEN** an entry's path in the Codex marketplace differs from the Claude
  Code marketplace's source for the same plugin
- **THEN** the test fails naming that plugin

### Requirement: Antigravity CLI installs one plugin from a subdirectory

The Antigravity CLI install block SHALL install one plugin from that plugin's
subdirectory of a clone of this repository, and the host-support record SHALL
state what such an install puts in the host: whether it holds only that
plugin's files, and whether it depends on the clone staying in place.

#### Scenario: Installing one plugin from a clone

- **WHEN** a user follows the Antigravity CLI install block for one plugin
- **THEN** that plugin is installed and no other plugin of the repository is

### Requirement: Host-support record

`docs/host-support.md` SHALL record, for Codex and for the Antigravity CLI,
each install run: the host version, the install form and the source it used (a
local clone or GitHub), its outcome, one skill run in that host and its
outcome, and what the plugins' hooks did there. The README SHALL point to it.

#### Scenario: Reading the record for a host

- **WHEN** a reader opens `docs/host-support.md` for Codex or the Antigravity
  CLI
- **THEN** it names the host version the install ran on, the install command
  form, whether it ran from a local clone or from GitHub, whether it succeeded,
  the skill that was run and what the host did with it, and the hooks'
  behaviour

#### Scenario: An install not yet run

- **WHEN** an install form the README gives has not been run in a host
- **THEN** the record says it has not been run, rather than omitting it

### Requirement: The record names no local path

The host-support record SHALL name no absolute path, home directory or user
name of the machine the runs were made on; a clone is written as `<clone>`.

#### Scenario: Host output quoted in the record

- **WHEN** a host's output that carries a local path is quoted or summarised in
  the record
- **THEN** the path appears as `<clone>` or relative to the host's own
  configuration directory, never as the machine's absolute path

### Requirement: Hooks are supported in Claude Code only

Plugin hooks SHALL be supported in Claude Code only. Their behaviour in Codex
and in the Antigravity CLI SHALL be recorded in the host-support record and
SHALL NOT be relied on; the README SHALL say so where it describes the hooks.

#### Scenario: A plugin with hooks installed in another host

- **WHEN** a plugin that ships hooks is installed in Codex or the Antigravity
  CLI
- **THEN** the host-support record says whether its hooks were loaded, fired or
  failed there, and the README does not promise them in that host

### Requirement: Two manifests suffice

Each plugin SHALL install in Codex and in the Antigravity CLI from its two
manifests, the `.claude-plugin/plugin.json` and the root Agent Plugins
`plugin.json`, with no third host manifest.

#### Scenario: A plugin installed in another host

- **WHEN** a plugin is installed in Codex or the Antigravity CLI by its
  README install block
- **THEN** the install succeeds with no manifest beyond the two, and the
  host-support record names which manifest the host read where that is
  observable
