# lint-standards Specification

## Purpose

The house lint standard as a contract: which checks a repository runs,
derived from its own signals; one tool per concern; configuration that
carries no version numbers, and the procedure that supplies them; how a local
hook finds its tool; when the rules reach an agent and what they let it
change; and when a whole repository is brought into line.

## Requirements

### Requirement: The checks a repository runs are derived from its signals

The standard SHALL state, for every topic it covers, the repository signal
that makes the topic's checks apply: a baseline set that applies to every
repository, and per-topic sets that apply when the topic's signal is present
in the tree. An agent applying the standard SHALL detect the signals, derive
the set of checks, and compare it with the repository's hook configuration,
rather than copy another repository's configuration. A signal for which the
standard has no topic SHALL prescribe nothing, and hooks the standard does
not cover SHALL be left to the project. Derivation SHALL run in both
directions: a set whose signal a repository no longer carries SHALL leave the
configuration at the next convergence, and SHALL return if the signal does,
so that the derived set and the committed configuration never diverge. A
signal SHALL be stated as content a repository holds, never as the name of a
directory one layout happens to use, so that the same content under another
layout derives the same set. Whether a repository tracks a lockfile of its
own SHALL be a signal as well: the hooks of a set that act on a lockfile —
keeping it in step with the project file, auditing the set it resolves —
SHALL apply only where the repository tracks one, and SHALL leave and return
with it as any derived hook does.

#### Scenario: A Python repository is derived

- **WHEN** an agent derives the checks for a repository containing
  `pyproject.toml` or any `*.py` file
- **THEN** the derived set is the baseline set plus the Python set
- **AND** no set is added on the strength of a signal the repository lacks

#### Scenario: A repository carries only baseline signals

- **WHEN** an agent derives the checks for a repository with no language,
  infrastructure, web or data signal
- **THEN** the derived set is the baseline set alone

#### Scenario: A signal without a topic

- **WHEN** a repository carries files of a kind the standard has no topic for
- **THEN** nothing is prescribed for them, and whatever hooks the project runs
  on them are left as they are

#### Scenario: A repository loses a signal it once had

- **WHEN** the last file of a kind is deleted from a repository whose
  configuration carries that topic's checks
- **THEN** the next convergence removes them, because the derived set is what
  the tree says today
- **AND** they return unchanged if a file of that kind is added again

#### Scenario: A repository tracks no lockfile of its own

- **WHEN** an agent derives the checks for a Python repository that is
  developed only as a member of another repository's workspace and tracks no
  lockfile
- **THEN** the derived set is the baseline set plus the Python set without
  its lockfile hook and its dependency audit
- **AND** both return at the convergence after the repository starts tracking
  a lockfile

#### Scenario: A repository is itself an Ansible collection

- **WHEN** a repository holds roles and a collection manifest at its root and
  no `ansible/` directory
- **THEN** the infrastructure set's Ansible checks and the scanning pair are
  derived for it, because the signal is the Ansible content and not the
  directory's name

#### Scenario: A repository holds Ansible playbooks

- **WHEN** an agent derives the checks for a repository tracking Ansible
  playbooks and the roles they apply
- **THEN** the derived set carries the Ansible linter and both scanners of
  the scanning pair, as Terraform content derives the pair beside its own
  checks

#### Scenario: A package manifest pins only a command-line tool

- **WHEN** a repository tracks a package manifest beside its package
  manager's lockfile, and no TypeScript or JavaScript file under the
  manifest's directory is left to the hooks by the configuration's top-level
  exclusion
- **THEN** the web set is not derived for it
- **AND** the manifest's lockfile is still a lockfile the repository tracks

#### Scenario: A compose file is the only infrastructure content

- **WHEN** the only infrastructure content a repository tracks is a compose
  file
- **THEN** no infrastructure check is derived for it, because neither scanner
  of the pair reads a compose file, and a gate that reads nothing is not
  carried

### Requirement: One house tool per concern, with two deliberate pairs

For each concern the standard covers it SHALL name exactly one tool, and it
SHALL name the tools it retires, so that a converged configuration carries no
second tool for a concern. Two concerns are deliberate pairs and SHALL be
stated as such: Python type checking runs mypy and ty, both blocking, with
mypy as the reference gate; infrastructure scanning runs checkov and trivy's
configuration scan, and a finding both raise is suppressed in the tool that
raised it, always with a reason.

#### Scenario: The house tools are read

- **WHEN** the standard is consulted for a concern
- **THEN** it names one tool: the hygiene hook set with private-key detection
  for file hygiene, gitleaks for secret scanning, typos for spelling, the
  justfile formatter for justfiles, nixfmt for nix, ruff for Python linting
  and formatting with its security rules in place of bandit, the lockfile
  hook and the project-file validator for Python packaging, yamllint for
  YAML, taplo for TOML, rumdl for markdown, shellcheck for shell, terraform's
  own formatter and validator with tflint for terraform, ansible-lint for
  ansible, hadolint for Dockerfiles, eslint and prettier with the project's
  type checker for web code, and sqlfluff with dbt's own parse and the
  dbt-checkpoint hooks for dbt projects

#### Scenario: A retired tool is found in a configuration

- **WHEN** a configuration being converged runs codespell, pyright, bandit,
  dprint, prettier over markup rather than code, or the third-party justfile
  hook
- **THEN** the house tool for that concern replaces it, and the retired tool
  leaves the configuration

#### Scenario: A finding is raised by both scanners

- **WHEN** checkov and trivy report the same finding
- **THEN** it is suppressed in the tool that raised it, with a reason recorded
  beside the suppression, and not in the other

#### Scenario: A hook the standard does not cover

- **WHEN** a configuration runs a hook for a concern the standard has no tool
  for, such as a project's own drift check
- **THEN** the hook belongs to the project, and convergence leaves it as it is

### Requirement: Canonical configuration carries no version numbers

Every topic SHALL give the exact hook entries that make up its set — the hook
repository, hook ids, arguments, the file filters that are part of the
standard, and for a local hook its entry — and the house values for each
linter's own configuration file, so that any two agents applying a topic
write the same configuration. Neither a topic nor a configuration value in it
SHALL state a version: no `rev:`, no tag, no release number. A per-hook quirk
that would otherwise be rediscovered SHALL be stated once, in the topic that
owns the hook. A hook's exclusions, a repository's allowlists, and paths that
follow from a repository's layout are the project's, not the standard's.

#### Scenario: Two repositories are converged on different days

- **WHEN** two agents converge two repositories with the same signals
- **THEN** the two configurations carry the same hooks, ids, arguments and
  configuration values, and differ at most in `rev:` values and in
  project-owned exclusions, allowlists and paths

#### Scenario: A reader looks for a version

- **WHEN** any topic of the standard is read
- **THEN** it states no version for any hook or tool

#### Scenario: A hook with a known quirk is written

- **WHEN** an agent writes the spelling hook, whose upstream publishes a
  moving major-version tag
- **THEN** the topic already states the quirk, and the pin the agent writes is
  a release tag rather than the moving one

### Requirement: Versions come from upstream under a release-age cooldown

When the standard is applied, each hook repository's `rev:` SHALL be the
newest release tag that is at least seven days old, found with a tool that
honours a release-age cooldown, and SHALL be pinned by tag rather than by
commit hash. The configuration SHALL remain runnable by the reference
implementation of its format: no key, syntax or hook form that only a faster
reimplementation understands, whether or not that reimplementation is what the
converging machine runs. This is a property of the artifact and SHALL be
checked rather than assumed. Versions converge across repositories each time a
repository is converged, not by a sweep. A Python lockfile a repository tracks
SHALL resolve under the same seven-day cooldown, and the cooldown SHALL be
stated in the project file rather than on a command line, so that every
resolution honours it — the lockfile hook's among them. A release younger
than the cooldown SHALL be admitted only by an entry in the project file that
names the package, with the reason beside it, and the entry SHALL leave once
the release is older than the cooldown. Where stating the cooldown would move
back a pin the lockfile already holds, the session SHALL report each such
pin, and SHALL exempt one taken to close an advisory before the lockfile is
committed.

#### Scenario: A repository is converged

- **WHEN** an agent converges a repository's configuration
- **THEN** every `rev:` is a release tag at least seven days old, and none is
  a commit hash

#### Scenario: A release is younger than the cooldown

- **WHEN** the newest tag of a hook repository was published within the last
  seven days
- **THEN** the pin is the newest tag older than that, and the younger release
  is picked up at a later convergence

#### Scenario: The reference implementation runs the configuration

- **WHEN** `pre-commit run --all-files` runs on a converged repository, on a
  machine that has only the reference implementation
- **THEN** every hook runs

#### Scenario: The converging machine runs a reimplementation

- **WHEN** the machine that converges a repository runs a faster
  reimplementation of the format and has no reference implementation at all
- **THEN** the configuration it writes is still checked against the reference
  implementation before it lands, because the guarantee is about the file and
  not about that machine

#### Scenario: A tracked lockfile is refreshed

- **WHEN** a session adds or upgrades a dependency in a Python repository
  that tracks a lockfile
- **THEN** the resolution takes no release younger than seven days, because
  the project file states the cooldown
- **AND** the lockfile hook's own re-lock leaves the lockfile as that
  resolution wrote it

#### Scenario: A fix release is younger than the cooldown

- **WHEN** the dependency audit reports an advisory whose fix was released
  within the last seven days
- **THEN** the project file exempts that one package, with the advisory named
  beside the entry
- **AND** the entry is removed once the release is older than the cooldown

#### Scenario: The cooldown is first stated in a repository

- **WHEN** the cooldown is added to a repository whose lockfile holds a pin
  younger than seven days
- **THEN** the session reports each pin the resolution moved back
- **AND** a pin that was taken to close an advisory is exempted before the
  lockfile is committed, so the advisory does not reopen

### Requirement: A local hook resolves its tool one way

Only a hook that pre-commit cannot install itself SHALL be a local hook; a
hook pre-commit installs carries its pin in `rev:`. A local hook whose tool
the repository's own lockfile pins SHALL run it through that lockfile's
runner, and where the lockfile's ecosystem can pin such a tool but does not
yet, convergence SHALL add it to the repository's development dependencies. A
local hook whose tool no lockfile of the repository pins, and pre-commit
itself, SHALL call the tool by name and expect it on `PATH`. No hook SHALL
reach into an umbrella or a sibling repository, and no lockfile SHALL be
created for lint's sake. A repository with a consumer pins nothing — one
that tracks no lockfile of its own because it is developed inside a
consumer's environment, a member of another repository's workspace included:
every local hook there SHALL call its tool by name, and SHALL NOT go through
a runner that would resolve a lockfile above or beside the repository, or
write one where none is tracked. There, a tool pre-commit can install, and
which needs nothing from the consumer's environment beyond what the hook's own
additional dependencies carry, SHALL be a hosted hook pinned by `rev:` rather
than a local one — the Ansible linter and the first scanner are such tools;
where the repository tracks a lockfile, they stay local hooks through its
runner. A repository with no consumer — Python that
is loose scripts with no project file — SHALL take a root project file and a
lockfile declaring the scripts' dependencies and the checkers, and its hooks
the runner form; that lockfile pins dependencies that exist either way, and
is not one created for lint's sake. The environment such a repository's hooks find on
`PATH` is its consumer's, so whatever its checkers need in order to see the
code — the repository's extras, its stub packages — SHALL be carried by the
consumer's lockfile and installed there. A topic that gives a local hook
through a lockfile's runner SHALL give its by-name form as well, or its hosted form for a tool a repository
that pins nothing hosts, unless the topic's own signal already requires the
lockfile. Every tool that **formats**
a justfile SHALL resolve `just` by this same rule, because formatter output
moves between releases. A checker that reports only on the structure `just`
parses SHALL NOT be held to it: parsed recipe structure does not move with the
pin, so such a checker may use whichever `just` its own harness finds, and the
two cannot disagree because the checker never formats.

#### Scenario: A Python repository runs a Python tool

- **WHEN** a local hook runs mypy, ty or the justfile formatter in a
  repository whose lockfile is uv's
- **THEN** the entry runs the tool through `uv run`, and the tool is a
  development dependency the lockfile pins

#### Scenario: A web repository runs its tools

- **WHEN** a local hook runs eslint, prettier or the type checker in a
  repository whose lockfile is a package manager's
- **THEN** the entry runs the tool through that package manager's executor,
  and `just`, which that lockfile cannot pin, is called by name

#### Scenario: A repository pins nothing

- **WHEN** a local hook is written in a repository that has a consumer and
  tracks no lockfile
- **THEN** the tool is called by name, and no lockfile is added

#### Scenario: A tool the umbrella's flake provides

- **WHEN** a hook needs terraform, tflint, trivy, hadolint or nixfmt
- **THEN** it calls the tool by name, and its entry contains no path outside
  the repository

#### Scenario: A second tool formats a justfile

- **WHEN** anything besides the formatter hook formats a justfile — a recipe,
  a script, a checker that rewrites the file
- **THEN** it resolves `just` from the repository's lockfile pin where there is
  one and from `PATH` otherwise, so the two cannot disagree on one file

#### Scenario: A checker reads a justfile without formatting it

- **WHEN** a checker reports on a justfile from the structure `just` parses,
  and never rewrites the file
- **THEN** the resolution rule does not reach it, and it may use whichever
  `just` its own harness finds, because parsed recipe structure does not move
  with the pin

#### Scenario: A workspace member runs a Python tool

- **WHEN** a local hook runs a type checker or the justfile formatter in a
  repository that is a member of another repository's workspace and tracks no
  lockfile of its own
- **THEN** the entry calls the tool by name
- **AND** it does not go through `uv run`, which resolves the workspace above
  the repository where there is one and writes an untracked lockfile where
  there is none

#### Scenario: A member's checkers need what only its extras provide

- **WHEN** the type checkers of a repository that tracks no lockfile need
  packages that only its optional extras or its stub packages provide
- **THEN** the consumer's lockfile carries them and the consumer's environment
  installs them
- **AND** their absence is repaired in the consumer's environment, never by a
  suppression in the member

#### Scenario: A topic gives a hook through the lockfile's runner

- **WHEN** a topic gives a local hook whose entry goes through a lockfile's
  runner, and the topic's signal does not itself require a lockfile
- **THEN** the topic gives the by-name entry beside it — or the hosted entry,
  for a tool a repository that pins nothing hosts — and says which
  repositories take which

#### Scenario: Loose scripts have no consumer

- **WHEN** a repository's Python is loose scripts with no project file, and
  nothing above or beside it carries the scripts' dependencies or the
  checkers
- **THEN** it takes a root project file declaring both and a lockfile pinning
  them, its local hooks take the runner form, and the lockfile hooks are
  carried
- **AND** a checker that cannot see whether a repository has a consumer
  reports such a repository by the lockfile it tracks, and raises no finding
  of its own for the missing project file

#### Scenario: A repository that pins nothing runs a scanner pre-commit installs

- **WHEN** the Ansible linter or the first scanner runs in a repository that
  has a consumer and tracks no lockfile
- **THEN** it is a hosted hook from its upstream repository, pinned by `rev:`,
  and no lockfile is added
- **AND** the tool comes from the hook's own environment, never from a
  virtualenv above or beside the repository

#### Scenario: A repository with a lockfile runs a scanner pre-commit installs

- **WHEN** the Ansible linter or the first scanner runs in a repository that
  tracks a lockfile
- **THEN** it is a local hook through the lockfile's runner, and no hosted
  hook pins it a second time

#### Scenario: The hosted Ansible linter reads collection content

- **WHEN** the hosted Ansible linter runs offline over content that calls
  modules from collections beyond the core engine
- **THEN** its additional dependencies carry those collections, so every
  module the content calls resolves in the hook's own environment

### Requirement: Blocking checks run at commit and network checks on demand

A check that blocks SHALL run at the commit stage, filtered to the file types
it applies to. A check that needs the network, such as a dependency audit,
SHALL run only on demand, in the manual stage, so that a commit never waits
on a remote service. Preparation a blocking check depends on that reaches the
network or needs credentials — initialising a Terraform root, fetching
collections — SHALL NOT run inside the gate: it is a step the project runs
before it, and a check whose preparation is missing has produced no finding.
A check that runs over a whole directory SHALL be one hook however many such
directories a repository has, run over each directory the project names. A
manual-stage check SHALL be runnable through the hook runner alone, and the
standard SHALL NOT require a task-runner recipe for it.

#### Scenario: A dependency audit is configured

- **WHEN** a repository's set includes a dependency audit
- **THEN** it is placed in the manual stage and does not run at commit

#### Scenario: A whole-program check is configured

- **WHEN** a check such as a type checker runs over the whole program
- **THEN** it runs at commit, is triggered only by files of its type, and is
  not handed the file list

#### Scenario: A blocking check needs prepared state

- **WHEN** a blocking check needs state that is fetched over the network or
  with credentials, such as an initialised Terraform root or installed
  collections
- **THEN** the hook fetches nothing, and the preparation is a step the project
  runs before the gate
- **AND** a directory that was not prepared is an environment failure, not a
  finding

#### Scenario: A whole-directory check has several directories

- **WHEN** a repository holds several directories a whole-directory check must
  run in, or none at its top
- **THEN** the check is one hook under the standard's id, run over each
  directory the project names
- **AND** which directories those are is the project's

#### Scenario: A manual check is run by hand

- **WHEN** someone runs the dependency audit of a repository
- **THEN** they run its hook through the hook runner's manual stage
- **AND** the standard requires no recipe for it; a recipe the project keeps
  is the project's

### Requirement: The rules attach on lint configuration and state their scope

The topics that govern a file SHALL attach when an agent reads a repository's
pre-commit configuration or a linter's own configuration file, and SHALL NOT
attach on a file read for other reasons, such as the Python project file,
even where it carries a linter's settings. Because path-scoped attachment
reaches every session it is set up for, the attached rules SHALL carry a scope
statement: they apply to what the agent adds or changes, and bringing the rest
of the file into line is a separate act, taken only when the user asks for it.
Where path-scoped attachment is not set up, the router alone SHALL deliver
them. The files
the topics attach on SHALL be the files the checker's ratchet acts on, so a
governed file written where none existed is reported whole by the checker
although nothing attached.

#### Scenario: A lint configuration is read

- **WHEN** an agent reads `.pre-commit-config.yaml` in any repository, in a
  session where path-scoped attachment is set up
- **THEN** the topics governing it arrive in context once, with the scope
  statement among them

#### Scenario: A linter's own configuration is read

- **WHEN** an agent reads a linter's configuration file the standard
  prescribes, such as the markdown linter's
- **THEN** the topic owning that linter arrives, and the scope statement with
  it

#### Scenario: The Python project file is read

- **WHEN** an agent reads `pyproject.toml`, whether or not it carries a
  `[tool.ruff]` section
- **THEN** nothing attaches, and the Python topic is reached through the
  router

#### Scenario: Path-scoped attachment is not set up

- **WHEN** a session has no path-scoped attachment of the rule files
- **THEN** reading a lint configuration attaches nothing, and the router
  delivers the topics in projects that enable the plugin

#### Scenario: A configuration is created where none existed

- **WHEN** an agent writes a repository's first lint configuration, having
  read no file the rules govern
- **THEN** nothing attaches, and the router is the only delivery, in a
  project that enables the plugin
- **AND** the checker's ratchet, whose baseline for a new file is empty,
  reports every finding of the written file right after the write

### Requirement: The standard is one conventions domain with one canonical copy of each rule

The standard SHALL be delivered as the conventions plugin `lint-rules`: one
router skill, `lint-rules:lint`, whose body is a topic index, and one rule
file per topic, each tool-neutral and stating its rationale inline. Lint
policy SHALL live in the lint domain alone: another domain's rules do not
prescribe which quality gates or checkers a repository runs, and its router
points to the lint domain for them — the Python typing rules name no type checker, and the `python` router
points to the lint domain for it. Justfile conventions SHALL stay with their
own domain; the lint domain owns only the formatter hook that runs on
justfiles.

#### Scenario: Another domain's reader needs the quality gates

- **WHEN** a domain's rules are read for which gates a repository wires
- **THEN** they prescribe none, and that domain's router points at the lint
  domain for the gates themselves

#### Scenario: The Python typing rules are read

- **WHEN** the Python typing rules are read
- **THEN** they name no type checker, and the `python` router's index points
  at the lint domain for it

#### Scenario: A rule is looked for

- **WHEN** any rule of the standard is looked for
- **THEN** it exists in exactly one rule file, and no router or other domain
  restates it

### Requirement: The repository hosting the standard converges first

This repository SHALL carry a pre-commit configuration derived from the
standard by its own signals, with the linter configuration files the
standard prescribes, its hooks installed, and every hook passing on all
files; it is the standard's acceptance test. Its baseline set carries the
secret-scanning and private-key gates. The hook-for-hook equality of its
derived set and its committed configuration SHALL be asserted by the
checker's audit, run over this repository in its own test suite, so a hook
its signals derive and its configuration lacks fails a test rather than
waiting to be noticed.

#### Scenario: This repository's configuration is derived

- **WHEN** an agent derives this repository's checks from the rules alone
- **THEN** the derived set equals the committed configuration, hook for hook
- **AND** the checker's audit of this repository, run in its test suite,
  reports nothing

#### Scenario: Every hook runs on all files

- **WHEN** `pre-commit run --all-files` runs in this repository
- **THEN** every hook passes, and the OpenSpec artifacts still validate

### Requirement: The spelling hook runs alone before the rest of a convergence

The spelling hook rewrites in place, so a wrong correction lands among the
other changes of an all-files run and cannot be told from them. When a
convergence runs every hook on all files, the spelling hook SHALL run first
and alone, on a clean working tree, and the session SHALL read everything it
rewrote before any other hook runs. A rewrite of a deliberate spelling — an
identifier, a path, a quoted string, a name under test — SHALL be reverted
and the spelling allowlisted, and only then SHALL the whole set run. This
SHALL hold at every convergence and not only the first, because a release the
pin moves to corrects words the earlier one left alone.

#### Scenario: The fixer would respell a deliberate spelling

- **WHEN** the spelling hook's run at a repository's first convergence
  rewrites a role string, a public module path or a test's name
- **THEN** the session finds it in a diff that holds the spelling hook's
  changes and no other hook's
- **AND** it reverts the rewrite and allowlists the spelling before the other
  hooks run

#### Scenario: A newer release respells what the pinned one accepted

- **WHEN** a convergence moves the spelling hook's pin in a repository that
  has long run the hook, and the newer release corrects a word the older one
  left alone
- **THEN** the correction is found the same way, in the spelling hook's own
  diff, before the other hooks run

### Requirement: A generated tree is excluded by what its generator rewrites

Where a repository holds files a generator rewrites — a planning tool's agent
files, a generated client — the configuration SHALL keep exactly those files
from every hook that rewrites, and SHALL NOT exclude a hand-written file that
sits beside them. The exclusion SHALL be confirmed rather than guessed: with the
generator's output committed, every hook is run on all files and the
generator is run again, and that second run changes nothing. A frozen record
— an archive of closed changes or closed roadmaps — SHALL be excluded as
well, because rewriting it edits history for no reader. Which paths these are
remains the project's to name; that they are found and confirmed this way is
the standard's.

#### Scenario: The generator runs again after the hooks

- **WHEN** the generator's output is committed, every hook has run on all
  files, and the generator runs again
- **THEN** the working tree is clean, because no hook rewrote a file the
  generator owns

#### Scenario: A hand-written file sits beside generated ones

- **WHEN** a directory holds files a generator rewrites and a file a person
  maintains, such as a settings file
- **THEN** the exclusion matches the generated files only, and the hooks
  still read the hand-written one

#### Scenario: A repository keeps a frozen archive

- **WHEN** a repository keeps closed changes or closed roadmaps as an archive
  nobody edits
- **THEN** the archive is excluded from the hooks, and its text is not
  rewritten

### Requirement: A whole repository is converged only on request

Bringing a whole repository's lint configuration into line SHALL be taken only
when the user asks for it. Without a request, a session that edits a lint
configuration SHALL change only what its task requires and say nothing about
the rest. A request SHALL be acted on as it is worded: asked for a proposal,
the session shows the diff the standard implies and writes nothing; asked to
converge, it follows the convergence procedure.

#### Scenario: A configuration is touched without a request

- **WHEN** a session edits a repository's lint configuration and nobody has
  asked for a convergence
- **THEN** it changes only what the task requires, and neither converges the
  rest nor proposes to

#### Scenario: The user asks for a convergence

- **WHEN** the user asks for a repository's quality gates to be brought into
  line
- **THEN** the session brings the whole configuration into line — hooks,
  arguments, configuration values, versions — by the convergence procedure

#### Scenario: The user asks for a proposal

- **WHEN** the user asks what a convergence would change
- **THEN** the session shows the diff the standard implies and writes nothing

### Requirement: A convergence lands alone, after the audit and every hook

A convergence SHALL land in a commit of its own, after every hook has run on
all files, and only when the checker's audit, run before the commit, reports
nothing. What the audit does not name — exclusions, allowlists, paths, the
project's own hooks — SHALL be left as it is, and hooks the standard does not
cover SHALL never be changed by convergence.

#### Scenario: The audit is run before the convergence commit

- **WHEN** a session has brought a repository's configuration into line and
  is about to commit the convergence
- **THEN** it runs the checker's audit there, fixes what the audit names,
  leaves what it does not, and commits only when the audit reports nothing

#### Scenario: A convergence is triggered by another task

- **WHEN** a convergence is asked for in the middle of an unrelated task
- **THEN** the convergence is committed separately from the task's own
  changes, with every hook run on all files first

### Requirement: A mass reformat is listed for blame in the form git parses

A convergence that reformats files en masse SHALL be listed in
`.git-blame-ignore-revs`, one line per commit, holding the commit's full hash
alone or followed by a `#` comment. The converging clone SHALL set
`blame.ignoreRevsFile` to that file, and before the listing is committed the
session SHALL confirm there that `git blame` attributes a line the reformat only
re-shaped to the commit that last changed it before.

#### Scenario: A convergence reformats many files

- **WHEN** the first run of a converged configuration rewrites files across
  the repository
- **THEN** that commit's hash is listed in `.git-blame-ignore-revs`, in full,
  with anything said about the commit behind a `#`
- **AND** the converging clone sets `blame.ignoreRevsFile` to that file
- **AND** before the listing is committed, `git blame` on a line the reformat
  only re-shaped names the commit that last changed the line before it, and
  names the reformat when run with `--ignore-revs-file ""`

#### Scenario: A line of the list says what the commit was in plain text

- **WHEN** a line of `.git-blame-ignore-revs` holds a hash followed by a
  description that no `#` precedes, or holds an abbreviated hash
- **THEN** the list is out of form: every `git blame` in a clone that honours
  it fails with `invalid object name`, and the line is rewritten — the full
  hash, then `#` and the description — before it is committed

### Requirement: A repository consumers pin is converged without changing their surface

A repository whose consumers depend on it at pinned versions SHALL be converged
under release discipline: nothing such a consumer depends on may change.
Reformatting source SHALL NOT count as a surface change; renaming a recipe or a
configuration key consumers read SHALL.

#### Scenario: A released repository is converged

- **WHEN** a repository whose consumers pin it is converged
- **THEN** nothing a consumer depends on at a pinned version changes, and a
  change that would is treated as breaking under release discipline

#### Scenario: A convergence would rename a configuration key

- **WHEN** converging such a repository would rename a recipe or a
  configuration key its consumers read
- **THEN** the rename is left out of the convergence
