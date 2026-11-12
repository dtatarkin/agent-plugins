# Spec Delta

## ADDED Requirements

### Requirement: A rule file's frontmatter has one written shape

A rule file whose first line, ignoring trailing whitespace, is `---` SHALL
open its frontmatter with a line that is exactly `---` and close it with a
line that is exactly `---`. When its frontmatter declares `paths:`, that key
SHALL start its line. A line-based reader then sees exactly the frontmatter a
YAML reader sees. The repository's tests SHALL fail on any violation, naming
the file.

#### Scenario: A delimiter carries more than `---`

- **WHEN** a rule file's opening or closing delimiter line carries trailing
  whitespace or a carriage return
- **THEN** the repository's tests fail, naming the delimiter

#### Scenario: The frontmatter is never closed

- **WHEN** a rule file opens with `---` and no later line closes it
- **THEN** the repository's tests fail, saying the frontmatter is not closed

#### Scenario: The `paths:` key is indented

- **WHEN** a rule file's frontmatter declares `paths:` on an indented line
- **THEN** the repository's tests fail, saying `paths:` does not start its line

#### Scenario: A file without frontmatter is unconstrained

- **WHEN** a rule file's first line is not `---`
- **THEN** this requirement does not bind it
