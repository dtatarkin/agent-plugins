# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
