# host-support Specification

## Purpose

Which agent hosts the plugins of this repository support, how a user installs
them in each, and the committed record that each host's install was run and
what it did.

## Requirements

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

`docs/host-support.md` SHALL record, for each supported host, what the host
does with these plugins as last verified. It holds one table with a column per
supported host and a row for each of: the host version and date last verified,
the install sources run, the skills, the hooks, the plugin manifest read and
the marketplace file read. Each host's quirks follow as a list. The README
SHALL point to the record.

#### Scenario: Reading the record for a host

- **WHEN** a reader opens `docs/host-support.md` for Claude Code, Codex or the
  Antigravity CLI
- **THEN** the table's column for that host names the host version and date it
  was last verified, which install sources (local clone, GitHub) were run,
  whether the skills load and under what name, whether the hooks are loaded
  and fire, and which plugin manifest and marketplace file the host read

#### Scenario: An install not yet run

- **WHEN** an install form the README gives has not been run in a host
- **THEN** the record's cell for it reads "not run", rather than the row or
  column being omitted

#### Scenario: The record and the README name the same hosts

- **WHEN** the README gives an install block for a host the record's table has
  no column for, or the table has a column for a host the README gives no
  install block for, or a required row is missing or a cell is empty
- **THEN** a test fails, naming the host, row or cell

#### Scenario: Where a run's detail is kept

- **WHEN** a change runs an install or a skill or hook run in a host
- **THEN** the commands and observations of that run are kept in that change's
  artifacts, and the record carries only the facts the run established

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

### Requirement: A plugin's version follows its files

A commit that changes any file under `plugins/<name>/` SHALL bump that
plugin's version, in both its manifests, unless the commit already carries a
bump of that plugin not yet tagged. Before 1.0, a changed or added rule bumps
the minor version and a change that alters no rule bumps the patch version.

#### Scenario: A plugin changed without a bump

- **WHEN** a plugin's files differ from those at the tag `<name>--v<version>`
  of the version its manifests declare
- **THEN** a test fails, naming the plugin and its version

#### Scenario: A bump not yet tagged

- **WHEN** a plugin's manifests declare a version that has no tag
- **THEN** the test passes for that plugin

#### Scenario: A clone without tags

- **WHEN** the test runs in a clone that holds no plugin tags
- **THEN** it is skipped, saying so, rather than failing

### Requirement: Plugin releases are tagged

A commit that bumps a plugin's version SHALL be tagged `<name>--v<version>`
with `claude plugin tag plugins/<name>`, once that commit is on the trunk.
When the trunk is pushed to a remote, the plugin tags SHALL be pushed with it,
and to both of the repository's remotes. The push stays the owner's call.

#### Scenario: Tagging a bump

- **WHEN** a commit that bumps a plugin's version lands on the trunk
- **THEN** that commit carries the tag `<name>--v<version>`, made by
  `claude plugin tag`, which checks that the plugin's manifest and its
  marketplace entry agree

#### Scenario: Pushing the trunk

- **WHEN** the owner pushes the trunk to one remote
- **THEN** the plugin tags are pushed to it too, and the same trunk and tags
  are pushed to the other remote
