# Spec Delta

## MODIFIED Requirements

### Requirement: Rule files are tool-neutral, consumer-free prose

The prose of a topic file MUST read correctly outside any specific agent tool:
it SHALL NOT refer to how the file itself is loaded, SHALL NOT mention skills,
plugins, marketplaces, or any agent product unless they are the file's subject,
and SHALL NOT name any consuming project — consumers are described generically.
A rule file whose subject is the plugin format MAY name that format, its files
and the hosts that read it. Each rule SHALL state its rationale inline so it
stands on its own. A rule file MAY carry frontmatter that a harness reads to
decide when to load it, such as `paths:` globs. That frontmatter is metadata,
not prose: it SHALL hold nothing but such loading keys, SHALL carry no rule
text, and SHALL be inert wherever it is not understood, so the file reads
correctly with the frontmatter ignored.

#### Scenario: A rule file is added or edited

- **WHEN** a rules file is written
- **THEN** its prose names no agent tool and no consuming project
- **AND** each rule's rationale is stated in the file itself

#### Scenario: A rule file carries loading metadata

- **WHEN** a rules file carries frontmatter telling a harness when to load it
- **THEN** the frontmatter holds only such loading keys and no rule text
- **AND** the file reads correctly with the frontmatter ignored

#### Scenario: A rule file's subject is the plugin format

- **WHEN** a rule file governs plugin skills, rule files, manifests or hooks
- **THEN** it may name those files, their formats and the hosts that read them
- **AND** it neither refers to how it itself is loaded nor names any consuming
  project

## ADDED Requirements

### Requirement: The authoring requirements are delivered as the conventions plugin plugin-rules

This spec's requirements and those of `rule-file-frontmatter` SHALL be
delivered as the portable conventions plugin `plugin-rules`: one router skill,
`plugin-rules:plugin`, whose body is a topic index, and exactly one rule file
per requirement, each tool-neutral in the sense above and stating its
rationale inline. The plugin SHALL ship no hooks and no checker.

#### Scenario: A rule of the authoring contract is looked for

- **WHEN** any requirement of this spec or of `rule-file-frontmatter` is
  looked for in its working form
- **THEN** it is stated in exactly one rule file of `plugin-rules`, and the
  router names that file without restating it

#### Scenario: A requirement is added or removed

- **WHEN** a requirement is added to or removed from this spec or
  `rule-file-frontmatter`
- **THEN** the same change adds or removes its rule file in `plugin-rules` and
  the router's index entry for it

#### Scenario: The plugin is enabled

- **WHEN** a project enables `plugin-rules`
- **THEN** its router is available and no hook of the plugin runs, because it
  ships none

### Requirement: The authoring rules attach on the plugin files they govern

Each rule file of `plugin-rules` SHALL carry `paths:` frontmatter naming the
plugin files its requirement governs: a skill's `SKILL.md`, its references,
plugin or marketplace manifests, or `hooks/hooks.json`. The manifest and hook
rules SHALL bind every plugin; the router and rule-file rules SHALL bind
conventions plugins only, and each rule file SHALL say which it binds.

#### Scenario: A plugin's skill or rule file is read

- **WHEN** path-scoped attachment of the rule files is set up and an agent
  reads a `SKILL.md` or a file under a skill's `references/`
- **THEN** the rules on router skills and rule files attach, together with the
  scope statement
- **AND** each says it binds conventions plugins only

#### Scenario: A plugin manifest or hook file is read

- **WHEN** path-scoped attachment of the rule files is set up and an agent
  reads a plugin manifest, a marketplace manifest or a `hooks/hooks.json`
- **THEN** the rules on manifests, hooks and their validation attach,
  whatever kind of plugin the file belongs to

#### Scenario: A session has no path-scoped attachment

- **WHEN** a session has no path-scoped attachment of the rule files
- **THEN** reading a plugin file attaches nothing, and the router delivers the
  rules in projects that enable the plugin
