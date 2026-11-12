# Spec Delta

## MODIFIED Requirements

### Requirement: The mechanically checkable rules are enforced

Over the hook configuration the checker SHALL report: a hook of the derived
set that is absent; a house hook whose set's signal the repository lacks; a
tool the standard retires; a house hook missing a canonical argument, filter
or stage; a local hook in the form the lockfile signal rules out, and a hook
of a tool the standard hosts where no lockfile is tracked — the Ansible linter
and the first scanner — local where it owes the hosted form or hosted where it
owes the runner form; a manifest
check ordered before the parse that writes its manifest; and a hook
repository pinned by commit hash or on the moving major tag.

#### Scenario: A hook of the set is absent

- **WHEN** the repository carries a Python signal and its configuration lacks
  the project-file validator
- **THEN** the checker reports that hook as missing

#### Scenario: A hygiene hook is dropped

- **WHEN** the configuration carries twelve of the fifteen hygiene ids
- **THEN** each of the three absent ids is a finding

#### Scenario: A hook outlives its signal

- **WHEN** the configuration carries the shell checker and the repository
  tracks no shell file
- **THEN** the checker reports the hook as stray

#### Scenario: A retired tool is found

- **WHEN** the configuration carries a second spell checker, a separate
  security linter, a code formatter pointed at markup, a third-party justfile
  hook, a mirror repository for a type checker, or the legacy id of the
  Python linter's check hook
- **THEN** the checker reports it, naming the house tool that replaces it

#### Scenario: A canonical argument is missing

- **WHEN** the YAML linter runs without its strict flag, the Python formatter
  without its narrowed type list, the line-ending fixer without its fix flag,
  or the second scanner without its exit-code flag
- **THEN** the checker reports the hook, naming the argument

#### Scenario: A whole-program check is handed the file list

- **WHEN** a type checker, a Terraform hook, a scanner or a web type check
  lacks `pass_filenames: false` or its type or path filter
- **THEN** the checker reports it

#### Scenario: A network check blocks

- **WHEN** the dependency audit is not confined to the manual stage
- **THEN** the checker reports it

#### Scenario: The form contradicts the lockfile signal

- **WHEN** a local hook runs its tool through the lockfile's runner in a
  repository that tracks no lockfile, or by name in one that does, or a web
  hook's executor does not match the tracked lockfile
- **THEN** the checker reports the hook, naming the form it owes

#### Scenario: A hosted-form tool is in the form the lockfile signal rules out

- **WHEN** the Ansible linter or the first scanner is a local hook, by name or
  through the lockfile's runner, in a repository that tracks no lockfile
- **THEN** the checker reports the hook, naming the hosted repository it owes
  and that the hook is pinned by `rev:`

#### Scenario: A hosted scanner shadows the lockfile's pin

- **WHEN** the Ansible linter or the first scanner is a hosted hook in a
  repository that tracks a lockfile
- **THEN** the checker reports the hook, naming the runner form it owes

#### Scenario: A hosted Ansible linter lacks its collections

- **WHEN** the hosted Ansible linter's additional dependencies do not name the
  community `ansible` package
- **THEN** the checker reports the hook, naming the dependency

#### Scenario: A manifest check runs before the parse

- **WHEN** a dbt manifest check is listed before the parse hook that writes
  the manifest
- **THEN** the checker reports the order

#### Scenario: A pin is not a tag

- **WHEN** a hook repository's `rev:` is a commit hash, or the spelling
  checker's is the moving major tag
- **THEN** the checker reports it

#### Scenario: An offline check reaches the network

- **WHEN** the link checker or the workflow security auditor runs without its
  offline flag or without its no-progress flag
- **THEN** the checker reports the hook, naming the flag

#### Scenario: The host validator is lenient

- **WHEN** the Claude manifest validator runs without `--strict`
- **THEN** the checker reports the hook, naming the flag

#### Scenario: The plugin schema check blocks

- **WHEN** the schema check of the portable plugin manifest, fetching its
  schema over the network, is not confined to the manual stage
- **THEN** the checker reports it
- **AND** it does not ask that check to run on every invocation, because the
  check is handed the manifests it validates

### Requirement: What belongs to the project is not checked

The checker SHALL NOT report: top-level or per-entry exclusions; path filters
and directory arguments; the contents of an allowlist or ignore file; hooks
the standard names no tool for; the age of a pin or the file's runnability
under the reference runner; the order of entries other than the manifest
rule; or comments. Comparison of a local hook's entry SHALL match its leading
tokens and required flags, never the whole string.

#### Scenario: A project's own hook

- **WHEN** the configuration carries a drift check the standard names no
  tool for
- **THEN** the checker reports nothing for it

#### Scenario: A directory argument differs

- **WHEN** a Terraform hook names two directories in a loop, or one directory
  the project chose
- **THEN** the checker reports nothing for the directories

#### Scenario: An exclusion is project-specific

- **WHEN** an entry carries an `exclude:` naming a generated tree
- **THEN** the checker reports nothing for it

#### Scenario: A pin is old

- **WHEN** a hook repository's tag is years behind upstream
- **THEN** the checker reports nothing: the age check is the procedure's

#### Scenario: A schema check of another schema

- **WHEN** the configuration carries the schema checker's hook pointed at a
  schema other than the Agent Plugins schema
- **THEN** the checker reports nothing for it, and it does not stand in for
  the house schema check
