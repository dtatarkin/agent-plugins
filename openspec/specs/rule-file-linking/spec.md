# rule-file-linking Specification

## Purpose

An opt-in way for a Claude Code user to have this repository's path-scoped rule
files attached on touch, by linking them into Claude Code's user-level rules
directory, and to undo it.

## Requirements

### Requirement: The script links every scoped rule file

`scripts/link-rules` SHALL link each plugin rule file
(`plugins/*/skills/*/references/*.md`) carrying `paths:` frontmatter into the
rules directory `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/rules`, creating it when
absent. Each link SHALL be a symbolic link named `<plugin>--<topic>.md` whose
absolute target is the rule file in the repository the script belongs to. A
rule file without `paths:` SHALL NOT be linked.

#### Scenario: First run

- **WHEN** a user runs `scripts/link-rules` with no argument and the rules
  directory does not exist
- **THEN** the directory is created and holds one symbolic link per scoped rule
  file, named `<plugin>--<topic>.md` and resolving to that file
- **AND** the script prints `linked <name>` for each and exits 0

#### Scenario: An unscoped rule file

- **WHEN** a rule file has no frontmatter, or frontmatter without `paths:`
- **THEN** no link is made for it

#### Scenario: The configuration directory is moved

- **WHEN** `CLAUDE_CONFIG_DIR` is set
- **THEN** the links are made under `$CLAUDE_CONFIG_DIR/rules`, and nothing is
  written under `$HOME/.claude`

#### Scenario: The clone is updated

- **WHEN** a linked rule file's content changes in the repository
- **THEN** the attached rule reflects the change without a re-run, because the
  link is not a copy

### Requirement: Plugin names narrow the selection

When given plugin names as arguments, the script SHALL link only the scoped rule
files of those plugins. An argument that names no plugin of the repository SHALL
be a usage error: the script SHALL change nothing and exit 2.

#### Scenario: One plugin named

- **WHEN** a user runs `scripts/link-rules <plugin>`
- **THEN** only that plugin's scoped rule files are linked

#### Scenario: An unknown plugin named

- **WHEN** an argument names no plugin directory of the repository
- **THEN** the script exits 2 with a message naming the argument, and the rules
  directory is unchanged

### Requirement: A re-run converges and prunes only its own links

A link is the script's own when its literal target lies under the `plugins/`
directory of the repository the script belongs to. On every run the script
SHALL remove each own link whose target is gone or no longer carries `paths:`,
and SHALL remove nothing else. Narrowing by plugin SHALL NOT remove another
plugin's live own links.

#### Scenario: Nothing changed

- **WHEN** the script runs twice with no change in between
- **THEN** the second run changes nothing, prints nothing and exits 0

#### Scenario: A rule file is removed or unscoped

- **WHEN** a linked rule file is deleted, or loses its `paths:` frontmatter,
  and the script runs again
- **THEN** its link is removed and the script prints `unlinked <name>`

#### Scenario: Foreign entries are left alone

- **WHEN** the rules directory holds a regular file, or a symbolic link into
  another location, under a name the script does not produce
- **THEN** a run leaves it unchanged

#### Scenario: A narrowed run keeps other plugins' links

- **WHEN** links of two plugins exist and the script runs naming only one
- **THEN** the other plugin's links remain

### Requirement: The script never replaces what it does not own

When the name a link would take is already held by a regular file, or by a
symbolic link that is not the script's own and does not resolve to the same
rule file, the script SHALL leave it unchanged, SHALL report it on standard
error, SHALL finish the rest of the run, and SHALL then exit 1.

#### Scenario: A regular file holds the name

- **WHEN** the rules directory holds a regular file named as a link would be
- **THEN** the file is unchanged, the script reports it and exits 1, and every
  other link is still made

#### Scenario: A foreign link holds the name

- **WHEN** a symbolic link with that name points elsewhere
- **THEN** it is unchanged, the script reports it and its target, and exits 1

#### Scenario: A foreign link already resolves to the file

- **WHEN** a symbolic link with that name is not the script's own but resolves
  to the same rule file
- **THEN** it is unchanged and the run counts it as done, exiting 0

### Requirement: Unlink removes only the script's own links

`scripts/link-rules --unlink` SHALL remove every own link from the rules
directory, and with plugin names SHALL remove only those plugins' own links. It
SHALL remove nothing else and SHALL make no link.

#### Scenario: Opting out

- **WHEN** a user runs `scripts/link-rules --unlink`
- **THEN** every own link is removed, each reported as `unlinked <name>`, and
  every other entry in the rules directory remains

#### Scenario: Opting out of one plugin

- **WHEN** a user runs `scripts/link-rules --unlink <plugin>`
- **THEN** only that plugin's own links are removed

### Requirement: Linking is opt-in and Claude Code only

Nothing in the repository SHALL run the script on a user's behalf: no plugin
ships it and no hook invokes it. It serves Claude Code's user-level rules
directory only, on POSIX systems with symbolic links. It SHALL need nothing
beyond `python3` 3.12 or later on `PATH`, with no virtual environment; under
an older interpreter it SHALL change nothing and exit 2 with a message naming
the requirement.

#### Scenario: A plugin is installed

- **WHEN** a user installs a plugin of this repository and never runs the script
- **THEN** nothing is written to the rules directory, and the plugin's rules
  reach the agent through its router skill alone

#### Scenario: The interpreter is too old

- **WHEN** a user runs the script with a `python3` older than 3.12
- **THEN** the script exits 2 with a message naming the required version, and
  the rules directory is unchanged
