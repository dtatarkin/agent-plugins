# Spec Delta

## Purpose

The contract a rule file meets when it declares, in `paths:` frontmatter, the
paths it governs, so a harness that attaches rules by path delivers exactly
that file on touch and never widens it into an always-on rule.

## ADDED Requirements

### Requirement: A rule file declares the paths it governs

A conventions plugin MAY adopt attachment on touch. An adopting plugin SHALL
declare it in its rule files alone: each topic file under its skill's
`references/` that attaches on touch SHALL carry `paths:` frontmatter naming
the path globs it governs, and that frontmatter SHALL be the whole
declaration. The plugin SHALL ship no attachment logic, hook or list of its
own. A rule file without `paths:` SHALL NOT attach, and a plugin that marks
no file keeps router-only delivery.

#### Scenario: A plugin adopts attachment

- **WHEN** a conventions plugin adds `paths:` frontmatter to one of its rule
  files
- **THEN** a harness that attaches rules by path attaches that rule file when
  a file matching those globs is read
- **AND** the plugin ships no attachment logic of its own

#### Scenario: A plugin does not adopt attachment

- **WHEN** no rule file of a conventions plugin carries `paths:`
- **THEN** its rules reach an agent only through its router skill

#### Scenario: Another plugin adopts the pattern later

- **WHEN** a second rules plugin wants its rules attached on touch
- **THEN** it adds `paths:` frontmatter to those rule files and nothing else —
  no new machinery is written

### Requirement: A scoped rule file cannot widen into an always-on rule

A harness loads a rule file without path scope, and anything a scoped file
imports, into every session unconditionally. A rule file carrying `paths:`
SHALL therefore give a non-empty list of non-empty glob strings, SHALL carry
no other frontmatter key, and SHALL contain no import — a line opening with
`@` followed by a path. A file without `paths:` is not held to this. The
repository's tests SHALL fail on any violation, naming the file.

#### Scenario: A scoped file imports another file

- **WHEN** a rule file carrying `paths:` holds a line opening with `@<path>`
- **THEN** the repository's tests fail, naming the import

#### Scenario: The glob list is empty

- **WHEN** a rule file's `paths:` is an empty list, or not a list of
  non-empty strings
- **THEN** the repository's tests fail, saying `paths:` is not a non-empty
  list of globs

#### Scenario: The frontmatter carries a second key

- **WHEN** a rule file's frontmatter holds `paths:` and any other key
- **THEN** the repository's tests fail, naming the extra key

#### Scenario: An unscoped file is unconstrained

- **WHEN** a rule file has no frontmatter, or frontmatter without `paths:`
- **THEN** this requirement does not bind it, imports included

#### Scenario: The contract is guarded

- **WHEN** the repository's tests run
- **THEN** at least one rule file carries `paths:`, so the check over every
  rule file cannot pass vacuously

### Requirement: Scoped rules state their scope

Among an adopting plugin's rule files carrying `paths:`, one SHALL have globs
covering every kind of file the plugin governs and SHALL state that the rules
apply to what the agent adds or changes, not to content it leaves untouched.

#### Scenario: An agent works in a file with legacy content

- **WHEN** rules attach while the agent edits a file whose existing content
  breaks them
- **THEN** the attached scope statement tells the agent to apply them to what
  it adds or changes and to leave the rest as it is
