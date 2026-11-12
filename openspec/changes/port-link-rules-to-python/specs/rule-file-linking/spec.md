# Spec Delta

## MODIFIED Requirements

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
