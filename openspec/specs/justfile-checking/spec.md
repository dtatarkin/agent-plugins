# justfile-checking Specification

## Purpose

Checks justfiles against the mechanically checkable conventions of the
`just-rules` plugin — auditing a repository's files on request and, inside
agent sessions, reporting right after each edit only the violations that edit
introduced — so compliance is enforced where prose alone did not hold.

## Requirements

### Requirement: Findings agree with how `just` parses the file

The checker SHALL derive its findings from the recipe and module structure that
`just` itself parses from a file, so a finding never disagrees with what `just`
sees. It SHALL parse with the `just` the harness process finds on its `PATH`,
never with a `just` a project pins
in its own toolchain, and its findings SHALL rest on parsed structure alone, so
the project's pin does not change them. A file that `just` cannot parse SHALL
yield a single parse finding naming the file and no rule findings.

#### Scenario: A file parses

- **WHEN** the checker examines a justfile that `just` parses
- **THEN** every finding refers to a recipe or module as `just` sees it

#### Scenario: A file does not parse

- **WHEN** `just` cannot parse the file
- **THEN** the checker reports one parse finding for it and no rule findings

#### Scenario: A project pins its own `just`

- **WHEN** a project's toolchain pins a `just` release different from the
  machine's
- **THEN** the checker parses with the machine's `just`, and its findings name
  recipe structure only, which the project's pin does not change

### Requirement: The mechanically checkable rules are enforced

The checker SHALL report: a public recipe without a `[doc("…")]` attribute; a
private recipe carrying `[doc("…")]`; a recipe named with a leading underscore
but not marked `[private]`, or marked `[private]` without the underscore; a
variadic parameter interpolated into a recipe body, except inside a quoted
command string that a nested shell re-evaluates (the rules' `git submodule
foreach` case); a recipe body of more than one line without a shebang; a bash
shebang body without `set -euo pipefail`; and a `*.just` file loaded with `mod`
that lacks `source_file := source_file()` or a `list` recipe. It SHALL NOT
report formatting: whether a file is formatted as `just --fmt` would format it
belongs to the repository's own formatter hook, which pins its own `just`. It
SHALL NOT report rules that need judgment — reusing the shared modules,
grouping recipes, preferring dependency calls to `just …` bodies, placing
`[no-cd]`, choosing `mod?` or `import?` — which reach the agent through
attachment only.

#### Scenario: A recipe carries its help in a comment

- **WHEN** a public recipe has a `#` comment above it and no `[doc("…")]`
- **THEN** the checker reports it

#### Scenario: A variadic is spliced into a body

- **WHEN** a recipe interpolates `{{ args }}` from a `*args` parameter into its
  body
- **THEN** the checker reports it, unless the interpolation sits inside a quoted
  command that a nested shell re-evaluates

#### Scenario: A multi-line body has no shebang

- **WHEN** a recipe body has two or more lines and no shebang
- **THEN** the checker reports it

#### Scenario: A file is unformatted

- **WHEN** a file is not formatted as `just --fmt` would format it and breaks
  no other checked rule
- **THEN** the checker reports nothing for it

#### Scenario: A sub-repository's justfile is loaded as a module

- **WHEN** an umbrella loads a sub-repository's `justfile` with `mod`
- **THEN** the module preamble is not required of it, since it is its own
  repository's entrypoint

#### Scenario: A judgment rule is broken

- **WHEN** a recipe re-implements what a shared module already offers
- **THEN** the checker reports nothing for it

### Requirement: Each finding names its rule file

Every finding SHALL name the recipe or file, a short rule identifier, a one-line
fix, and the `just-rules` rule file that states the rule, as its path within the
plugin, `skills/just/references/<topic>.md`. A finding SHALL NOT restate the
rule's rationale.

#### Scenario: A violation is reported

- **WHEN** the checker reports a violation
- **THEN** the report names the recipe, the rule, a one-line fix, and the
  `skills/just/references/<topic>.md` file to read

### Requirement: A repository's files can be audited on request

The checker SHALL offer an audit mode, `just-lint check`, that examines every
recipe of the named files — following modules from an entrypoint — reports
every finding, and exits non-zero when any finding exists and zero when none
does. It SHALL NOT follow a `mod` into another git repository: each repository
is audited on its own. The audit mode SHALL be how a repository's cleanup pass
is verified.

#### Scenario: A clean repository is audited

- **WHEN** the audit examines justfiles that break no checked rule
- **THEN** it reports nothing and exits zero

#### Scenario: A repository with legacy recipes is audited

- **WHEN** the audit examines recipes that break checked rules
- **THEN** it reports each finding and exits non-zero

#### Scenario: An umbrella loads another repository as a module

- **WHEN** the audit of an umbrella reaches a `mod` whose file lies in another
  git repository, such as a colleague's sub-repository
- **THEN** it reports nothing from that repository's files

### Requirement: Inside a session, only violations the context introduced are reported

Within an agent session, the checker SHALL act only on files named `justfile`,
`.just` or `*.just`. It SHALL record the findings such a file already has
before the context first edits or writes it; after each edit or write of that
file it SHALL report only findings absent from that baseline, identified by
recipe name and rule, right after the edit that introduced them, and SHALL stay
silent when there are none. A file new to the context SHALL have an empty
baseline. A baseline SHALL outlive the session ending, so a session resumed
within a week is still measured against it. When the introduced findings exceed
what the harness hands the agent inline, the report SHALL hold as many as fit
and state how many more remain, rather than be set aside whole.

#### Scenario: A new recipe breaks a rule

- **WHEN** an agent adds a recipe that breaks a checked rule
- **THEN** the finding is reported right after that edit

#### Scenario: A legacy recipe is touched without a new violation

- **WHEN** an agent changes a recipe whose existing violations predate its
  first edit, and adds none
- **THEN** nothing is reported

#### Scenario: A legacy recipe gains a new violation

- **WHEN** an edit adds a violation to a recipe that already had others
- **THEN** only the added violation is reported

#### Scenario: A recipe is copied from a legacy neighbour

- **WHEN** an agent adds a recipe copied from a legacy recipe
- **THEN** it is a new recipe, and all of its violations are reported

#### Scenario: A new justfile is written

- **WHEN** an agent writes a new justfile
- **THEN** every finding in it is reported

#### Scenario: A new justfile has more findings than fit inline

- **WHEN** a written file's findings exceed what the harness hands the agent
  inline
- **THEN** the report holds as many as fit and states how many more remain

#### Scenario: A justfile the context never edited

- **WHEN** the context has not edited a justfile
- **THEN** nothing is reported for it, whatever it contains

#### Scenario: A file that is not a justfile reaches the checker

- **WHEN** the checker is handed an edit to a file not named `justfile`,
  `.just` or `*.just`
- **THEN** it reports nothing

#### Scenario: A session is resumed

- **WHEN** a session that introduced a violation ends and is resumed within a
  week
- **THEN** that violation is still reported as introduced, not taken as legacy

### Requirement: A turn cannot end quietly with introduced violations

When a context — the main session or a subagent — is about to finish while
findings it introduced remain in files it changed, the checker SHALL block the
finish once for that prompt and hand the agent the open findings. It SHALL let
the finish proceed once it has already blocked for that prompt, whatever other
hooks did, and SHALL never block a context that changed no justfile. Because
the harness shows every block to the user as a hook error, blocking SHALL be
reserved for this case.

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

#### Scenario: A context changed no justfile

- **WHEN** a context finishes without having edited a justfile — including the
  harness's own compaction subagent
- **THEN** nothing is blocked

#### Scenario: Every introduced finding was fixed

- **WHEN** no introduced finding remains
- **THEN** the finish proceeds without a block

### Requirement: The checker degrades without guessing

When `just` is not available, the checker SHALL say so once per context and
report nothing else. When a file parsed at its baseline but no longer parses
after an edit, it SHALL report a parse finding; when it did not parse at its
baseline either, it SHALL report nothing new. Edits made through shell commands
rather than the agent's file tools SHALL NOT be checked in-session; the audit
mode covers them.

#### Scenario: `just` is missing

- **WHEN** the checker runs on a machine without `just`
- **THEN** it states once that justfile checks are off and blocks nothing

#### Scenario: An edit breaks parsing

- **WHEN** a file that parsed before an edit no longer parses after it
- **THEN** a parse finding is reported

#### Scenario: A justfile is changed through a shell command

- **WHEN** a justfile is changed with a shell command
- **THEN** no in-session finding is reported, and the next audit reports what
  it finds

### Requirement: The hooks tolerate a missing checker

When the checker is not installed where the harness runs its hooks, the
plugin's edit and turn-end hooks SHALL exit quietly: they SHALL report
nothing, block nothing and fail no tool call. When it is installed, they SHALL
hand each event to it unchanged. Whether it is installed SHALL be decided
anew on every call, without a shell, so a project's shell prefix adds nothing
to a justfile edit.

#### Scenario: A justfile is edited without the checker

- **WHEN** an agent edits a justfile in a session whose hooks cannot find the
  checker
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
- **THEN** the next justfile edit is checked, with no new session needed

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
- **THEN** the user sees one notice naming the tool, stating that the
  justfile checks are off and saying how to install it
- **AND** the agent is told that no findings will follow its edits

#### Scenario: A session starts with the checker

- **WHEN** a session starts and the checker is found
- **THEN** no notice is shown and nothing is added to the agent's context

#### Scenario: The context is compacted or cleared

- **WHEN** a session without the checker is compacted or cleared
- **THEN** the agent is told again that the checks are off
