# private-names-guard Specification

## Purpose

Keeps names that must not be published out of this public repository: a local
commit check that matches a list held outside the repository against every
commit's paths, content and message, and against the whole history on demand,
and that blocks the commit when it has no list to match.

## Requirements

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

### Requirement: Every staged path and its staged content are checked

At the commit stage the guard SHALL match every staged path, and the content of
every staged file as it stands in the index, against the list, and SHALL fail
the commit on any match. No path is excluded: generated files, archived
changes, symbolic links (their target) and binary files are checked too.

#### Scenario: Staged content names a private name

- **WHEN** a staged file's content matches a pattern of the list
- **THEN** the commit fails

#### Scenario: A staged path names a private name

- **WHEN** a staged file's path matches a pattern of the list
- **THEN** the commit fails

#### Scenario: A symbolic link points at a private name

- **WHEN** a staged symbolic link's target matches a pattern of the list
- **THEN** the commit fails

#### Scenario: Generated and archived files are not exempt

- **WHEN** the matching file sits in a generated tree or in the archive of closed changes
- **THEN** the commit fails all the same

#### Scenario: The index is read, not the working tree

- **WHEN** the staged version of a file matches a pattern and the unstaged working copy does not
- **THEN** the commit fails

#### Scenario: A clean commit passes

- **WHEN** no staged path and no staged content matches any pattern
- **THEN** the guard exits zero

### Requirement: The commit message is checked

At the commit-msg stage the guard SHALL match the commit message against the
list and fail the commit on any match. Lines git strips from the message — lines
starting with `#`, and everything from the scissors line on — SHALL be ignored.

#### Scenario: The message names a private name

- **WHEN** a line of the commit message matches a pattern of the list
- **THEN** the commit fails

#### Scenario: Git's comment lines are ignored

- **WHEN** a match occurs only on a line starting with `#`, or below the scissors line
- **THEN** the guard exits zero for that message

### Requirement: Findings are reported by location

On a match the guard SHALL print each finding with its location and the matched
text: `path:line: match` for content, the path for a path, `commit message:line:
match` for the message, and the commit for a history finding.

#### Scenario: A content finding names its place

- **WHEN** line 3 of a staged file matches a pattern
- **THEN** the output holds that file's path, line number 3 and the matched text

### Requirement: One install enables both checks

The hook configuration SHALL declare both the pre-commit and the commit-msg hook
types as its default install types, so that a single `prek install` or
`pre-commit install` enables the content check and the message check together.

#### Scenario: A fresh clone installs the hooks

- **WHEN** a committer runs `prek install` or `pre-commit install` in a fresh clone
- **THEN** both the pre-commit and the commit-msg hooks are installed, and both run the guard

### Requirement: The guard runs only locally

The guard SHALL run only on a committer's machine. It SHALL NOT be added to any
hosted CI job, because a job log would publish the text it matched, and a
log's secret masking does not reliably hide it.

#### Scenario: No workflow runs the guard

- **WHEN** the repository's CI configuration is read
- **THEN** no job invokes the guard

### Requirement: The whole history can be checked

The guard SHALL offer a history mode that matches, for every commit reachable
from any ref, its tree's paths and content, its message, and its author and
committer identities, plus every ref name and annotated tag message, and SHALL
exit non-zero on any match.

#### Scenario: An earlier commit names a private name

- **WHEN** a commit reachable from a ref, made without the hooks, holds a matching line
- **THEN** the history mode exits non-zero and names that commit

#### Scenario: A clean history passes

- **WHEN** nothing reachable from any ref matches the list
- **THEN** the history mode exits zero
