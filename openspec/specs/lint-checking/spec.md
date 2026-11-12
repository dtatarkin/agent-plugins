# lint-checking Specification

## Purpose

Checks a repository's lint configuration against the house lint standard —
auditing the pre-commit configuration and each linter's own configuration
file on request, and, inside agent sessions, reporting right after each edit
only the findings that edit introduced — so the standard is enforced where
prose and attachment alone do not reach.

## Requirements

### Requirement: Findings derive from the parsed configuration and the repository's signals

The checker SHALL derive a repository's set from the signals of its tracked
files alone, as the standard states them, and SHALL compare that set with the
hook configuration as the hook runner parses it, never with the file's text.
Anchors and aliases SHALL resolve before comparison. A hook configuration the
checker cannot parse SHALL yield one parse finding and no rule findings. The
derivation SHALL be the audit's and the ratchet's alike.

#### Scenario: A signal is present

- **WHEN** the repository tracks a Terraform file under any directory
- **THEN** the infrastructure set is derived, whatever the directory is named

#### Scenario: A lockfile is tracked

- **WHEN** the repository tracks a Python lockfile of its own
- **THEN** the lockfile hooks are part of the derived set and every local
  hook of the Python set is expected in the runner form

#### Scenario: No lockfile is tracked

- **WHEN** the repository tracks no lockfile of its own, whether or not one
  lies untracked in its directory or above it
- **THEN** neither lockfile hook is expected, and every local hook is
  expected in the by-name form
- **AND** the Ansible linter and the first scanner are expected as hosted
  hooks pinned by `rev:`, not as local hooks

#### Scenario: A signal is ignored, not tracked

- **WHEN** a file that would carry a signal is in the repository's directory
  but not tracked, such as a shell script inside a virtual environment
- **THEN** it contributes no signal

#### Scenario: The configuration does not parse

- **WHEN** the hook configuration is not valid YAML or carries no list of
  repositories
- **THEN** the checker reports one parse finding for it and no rule findings

#### Scenario: An alias is used

- **WHEN** a hook's exclusion is written as an alias of an anchor defined
  elsewhere in the file
- **THEN** the checker compares the resolved value

#### Scenario: Ansible content is tracked

- **WHEN** the repository tracks Ansible content — a collection manifest, a
  role's tasks, or YAML under an `ansible/` directory — and no Terraform or
  cluster content
- **THEN** the Ansible linter and both hooks of the scanning pair are part of
  the derived set, and neither scanner is reported as stray

#### Scenario: A manifest and lockfile hold no web source

- **WHEN** the repository tracks a package manifest beside a package
  manager's lockfile, and every TypeScript or JavaScript file under the
  manifest's directory is matched by the configuration's top-level exclusion
  or there is none
- **THEN** the web hooks are not part of the derived set, and a web hook the
  configuration carries is reported as stray
- **AND** the lockfile still counts as tracked, so the spelling checker's
  exclusion file is still owed

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

### Requirement: The linter configuration files are checked

Over each linter's own configuration file the checker SHALL report: a file
the standard prescribes for a derived set that is absent; a house value that
is absent or different, including the values the Python project file carries
for the Python linter and the lockfile cooldown; and a repository-wide
disable in the shell checker's file. It SHALL read the Python project file
for those values although no topic attaches on it.

#### Scenario: A linter's file is absent

- **WHEN** the repository carries the markup signal and no YAML linter
  configuration or no markdown linter configuration
- **THEN** the checker reports the absent file

#### Scenario: A house value is wrong

- **WHEN** the markdown linter's file sets a width other than the house
  width, or the Python project file's lint section lacks the security rules,
  the two house ignores, or the four test ignores, or lacks the lockfile
  cooldown where a lockfile is tracked
- **THEN** the checker reports the value, naming the file

#### Scenario: The security rules are enabled either way

- **WHEN** the Python project file enables the security rules under `select`
  or under `extend-select`
- **THEN** the checker reports nothing for them

#### Scenario: A code is disabled repository-wide

- **WHEN** the shell checker's file carries a disable directive
- **THEN** the checker reports it

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

### Requirement: Each finding names its topic file

Every finding SHALL name the file it is about, its subject — a hook id, a
configuration key, or the file as a whole — a short rule identifier, a
one-line fix, and the `lint-rules` topic file that states the rule, as its
path within the plugin, `skills/lint/references/<topic>.md`. A finding SHALL
NOT restate the rule's rationale.

#### Scenario: A violation is reported

- **WHEN** the checker reports a violation
- **THEN** the report names the file, the subject, the rule, a one-line fix,
  and the `skills/lint/references/<topic>.md` file to read

#### Scenario: A finding of the hook set

- **WHEN** a hook of the Python set is missing
- **THEN** the finding names the Python topic

### Requirement: A repository's configuration can be audited on request

The checker SHALL offer an audit mode that examines one repository — the one
holding the directory it is given — reports every finding, and exits 1 when
any finding exists, 0 when none does, and 2 when it cannot run. It SHALL NOT
read a nested repository's tracked files as signals, nor audit its
configuration. A repository with no hook configuration SHALL yield one
finding saying so, with the linter-file findings, and exit 1. The audit SHALL
be how a convergence is verified.

#### Scenario: A converged repository is audited

- **WHEN** the audit runs in a repository whose configuration matches its
  derived set
- **THEN** it reports nothing and exits zero

#### Scenario: A drifted repository is audited

- **WHEN** the audit runs in a repository carrying retired tools and missing
  hooks
- **THEN** it reports each finding and exits one

#### Scenario: An umbrella holds a sub-repository

- **WHEN** the audit runs at an umbrella root whose sub-repository tracks
  files the umbrella does not
- **THEN** the sub-repository's files contribute no signal and its
  configuration is not audited; it is audited on its own

#### Scenario: The repository has no configuration

- **WHEN** the audit runs in a repository with no hook configuration
- **THEN** it reports that one finding and the linter-file findings, and
  exits one

#### Scenario: The audit cannot run

- **WHEN** the directory is in no git repository, or git is not available
- **THEN** it says so and exits two

#### Scenario: This repository is audited

- **WHEN** the audit runs at this repository's root in its test suite
- **THEN** it reports nothing

### Requirement: Inside a session, only findings the context introduced are reported

In a session the checker SHALL act only on files the lint topics attach on.
Before a context first edits or writes such a file it SHALL record the
findings the file has; after each edit it SHALL report only findings absent
from that baseline, right after the edit, and stay silent otherwise. A new
file SHALL have an empty baseline. A baseline SHALL outlive the session for a
week. A report exceeding the inline limit SHALL hold what fits and state how
many more remain.

#### Scenario: A configuration is written where none existed

- **WHEN** an agent writes a repository's first hook configuration
- **THEN** every finding in it is reported right after the write

#### Scenario: A legacy configuration is touched without a new finding

- **WHEN** an agent edits a configuration whose existing findings predate its
  first edit, and introduces none
- **THEN** nothing is reported

#### Scenario: A legacy configuration gains a finding

- **WHEN** an edit drops a canonical argument from a hook in a configuration
  that already had other findings
- **THEN** only the dropped argument is reported

#### Scenario: A hook is renamed

- **WHEN** an edit changes a hook's id
- **THEN** the hook under its new id is new, and all of its findings are
  reported

#### Scenario: The Python project file is edited

- **WHEN** an agent edits `pyproject.toml`
- **THEN** nothing is reported in-session; its findings are the audit's

#### Scenario: A finding about another file

- **WHEN** an edit of the hook configuration leaves a linter's file still
  absent
- **THEN** the absence is not reported as introduced by that edit

#### Scenario: A file the context never edited

- **WHEN** the context has not edited a governed file
- **THEN** nothing is reported for it, whatever it contains

#### Scenario: An ungoverned file reaches the checker

- **WHEN** the checker is handed an edit to a file no lint topic attaches on
- **THEN** it reports nothing

#### Scenario: A session is resumed

- **WHEN** a session that introduced a finding ends and is resumed within a
  week
- **THEN** that finding is still reported as introduced

### Requirement: A turn cannot end quietly with introduced findings

When a context — the main session or a subagent — is about to finish while
findings it introduced remain in files it changed, the checker SHALL block
the finish once for that prompt and hand the agent the open findings. It
SHALL let the finish proceed once it has already blocked for that prompt,
whatever other hooks did, and SHALL never block a context that changed no
governed file.

#### Scenario: Introduced findings remain at the end of a turn

- **WHEN** an agent is about to finish while its introduced findings remain
- **THEN** the finish is blocked once and the findings are handed back

#### Scenario: The agent finishes again after a block

- **WHEN** the agent tries to finish again in the same turn after a block
- **THEN** the finish proceeds

#### Scenario: Another hook blocked the finish first

- **WHEN** another hook's block keeps the turn going and this context's
  introduced findings remain
- **THEN** the checker still blocks once for that prompt

#### Scenario: A context changed no governed file

- **WHEN** a context finishes without having edited a governed file —
  including the harness's own compaction subagent
- **THEN** nothing is blocked

#### Scenario: Every introduced finding was fixed

- **WHEN** no introduced finding remains
- **THEN** the finish proceeds without a block

### Requirement: The checker degrades without guessing

The checker SHALL need no tool beyond git. When git is not available
in-session, it SHALL say so once per context and report nothing else. When a
file parsed at its baseline but no longer parses after an edit, it SHALL
report a parse finding; when it did not parse at its baseline either, it
SHALL report nothing new. Edits made through shell commands SHALL NOT be
checked in-session; the audit covers them.

#### Scenario: git is missing

- **WHEN** the hook runs on a machine without git
- **THEN** it states once that lint checks are off and blocks nothing

#### Scenario: An edit breaks parsing

- **WHEN** a configuration that parsed before an edit no longer parses after
  it
- **THEN** a parse finding is reported

#### Scenario: A configuration is changed through a shell command

- **WHEN** the hook configuration is rewritten with a shell command
- **THEN** no in-session finding is reported, and the next audit reports what
  it finds

### Requirement: The hooks tolerate a missing checker

When the checker is not installed where the harness runs its hooks, the
plugin's edit and turn-end hooks SHALL exit quietly: they SHALL report
nothing, block nothing and fail no tool call. When it is installed, they SHALL
hand each event to it unchanged. Whether it is installed SHALL be decided
anew on every call, without a shell, so a project's shell prefix adds nothing
to a governed edit.

#### Scenario: A governed file is edited without the checker

- **WHEN** an agent edits a hook configuration in a session whose hooks
  cannot find the checker
- **THEN** nothing is reported, no hook error is shown, and the edit proceeds

#### Scenario: A turn ends without the checker

- **WHEN** a context finishes in a session whose hooks cannot find the
  checker
- **THEN** the finish is not blocked and no hook error is shown

#### Scenario: The checker is installed

- **WHEN** the hooks find the checker
- **THEN** its findings, its baseline and its turn-end gate behave exactly as
  the other requirements of this capability state

#### Scenario: The checker becomes available mid-session

- **WHEN** the checker becomes resolvable where the hooks run after the
  session started
- **THEN** the next governed edit is checked, with no new session needed

#### Scenario: A project wraps shell commands in a prefix

- **WHEN** a hook runs in a project whose settings route shell commands
  through a shell prefix
- **THEN** deciding whether the checker is installed enters no project
  environment and runs through no shell

### Requirement: A missing checker is announced at session start

At each session start, including a resume, a clear or a compaction, the
plugin SHALL show the user one notice when its checker is not installed. The
notice SHALL name the missing tool, state that the plugin's checks are off
and say how to install it. The agent SHALL be told the checks are off. When
the checker is installed, nothing SHALL be said.

#### Scenario: A session starts without the checker

- **WHEN** a session starts and the checker cannot be found
- **THEN** the user sees one notice naming the tool, stating that the lint
  checks are off and saying how to install it
- **AND** the agent is told that no findings will follow its edits

#### Scenario: A session starts with the checker

- **WHEN** a session starts and the checker is found
- **THEN** no notice is shown and nothing is added to the agent's context

#### Scenario: The context is compacted or cleared

- **WHEN** a session without the checker is compacted or cleared
- **THEN** the agent is told again that the checks are off
