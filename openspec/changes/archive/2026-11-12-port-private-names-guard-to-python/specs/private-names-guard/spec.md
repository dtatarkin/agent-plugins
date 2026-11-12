# Spec Delta

## MODIFIED Requirements

### Requirement: The list is read from outside the repository

The guard SHALL read its list from the file named by `AGENT_PLUGINS_PRIVATE_NAMES`
when that variable is set and non-empty, and otherwise from
`~/.config/agent-plugins/private-names`. Each line is one Python regular
expression (the `re` module's syntax), matched case-sensitively; lines starting
with `#` and empty lines are ignored. The list SHALL never be committed to the
repository.

#### Scenario: The variable names the list

- **WHEN** `AGENT_PLUGINS_PRIVATE_NAMES` names a readable list file
- **THEN** the guard matches against the patterns in that file

#### Scenario: The fallback path holds the list

- **WHEN** `AGENT_PLUGINS_PRIVATE_NAMES` is unset and `~/.config/agent-plugins/private-names` is a readable list
- **THEN** the guard matches against the patterns in the fallback file

#### Scenario: Comment and empty lines are not patterns

- **WHEN** the list holds lines starting with `#` or empty lines
- **THEN** those lines match nothing, and an empty line does not make every line match

#### Scenario: Patterns are matched case-sensitively

- **WHEN** the list holds `zzq-[a-z]+` and a staged file holds only `ZZQ-NAME`
- **THEN** the guard exits zero

### Requirement: The guard fails closed without a usable list

The guard SHALL fail, blocking the commit, when it has no usable list: the
variable is set but its file is missing or unreadable, the variable is unset and
the fallback file is missing, the list holds no pattern, a pattern is not a
valid expression, or a pattern uses a construct that a POSIX extended regular
expression reads differently. Its message SHALL name the variable and the
fallback path.

#### Scenario: Neither source exists

- **WHEN** `AGENT_PLUGINS_PRIVATE_NAMES` is unset and the fallback file does not exist
- **THEN** the guard exits non-zero, and its message names both the variable and the fallback path

#### Scenario: The variable names a missing file

- **WHEN** `AGENT_PLUGINS_PRIVATE_NAMES` names a file that does not exist, and the fallback file exists
- **THEN** the guard exits non-zero instead of reading the fallback

#### Scenario: The list has no pattern

- **WHEN** every line of the list is a comment or empty
- **THEN** the guard exits non-zero

#### Scenario: A pattern is invalid

- **WHEN** a line of the list is not a valid Python regular expression
- **THEN** the guard exits non-zero, and does not report the commit as clean

#### Scenario: A pattern uses a POSIX bracket expression

- **WHEN** a line of the list holds a POSIX bracket expression such as `[[:alpha:]]`, `[[.x.]]` or `[[=x=]]`
- **THEN** the guard exits non-zero in every mode, and its message names the line number and says the construct is
  POSIX-only, without printing the pattern

#### Scenario: A pattern uses a GNU word-boundary escape

- **WHEN** a line of the list holds `\<` or `\>`
- **THEN** the guard exits non-zero in every mode, and its message names the line number and says the construct is
  POSIX-only, without printing the pattern
