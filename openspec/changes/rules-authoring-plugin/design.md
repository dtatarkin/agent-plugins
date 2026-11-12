# Design

## Context

See proposal.md for why. The requirements are in
`specs/agent-rules-authoring/spec.md` of this change.

The repository holds eight conventions plugins, all laid out the same way:
`plugins/<p>/.claude-plugin/plugin.json`, a root `plugin.json`,
`skills/<d>/SKILL.md` and `skills/<d>/references/*.md`. `just-rules` is the
closest model:

- Its router is a "this skill is a router" paragraph and a two-column table,
  "You are editing…" against "Read", that names each `references/<topic>.md`.
- Every topic carries `paths:`.
- Its `scope.md` holds only the union of the globs and the statement "Apply
  these rules to what you add or change; leave other content as it is."

The tests find plugins by globbing `plugins/*`:

- `tests/plugins/test_rule_frontmatter.py` checks every scoped rule file.
- `tests/plugins/test_hook_manifests.py` checks every `hooks/hooks.json`.

The exception is `tests/plugins/test_portable_manifests.py`. It keeps an
explicit `PORTABLE` tuple and holds name, version, description and author
equal across the two manifests.

Pre-commit runs `check-json`, `rumdl-check`, `typos` and the private-names
guard. The guard checks paths, content and the commit message.

## Goals / Non-Goals

**Goals:**

- A plugin whose rule files are the working form of the ten requirements:
  the seven of `agent-rules-authoring` and the three of
  `rule-file-frontmatter`.
- The rule files attach on touch wherever path-scoped attachment is set up,
  and through the router everywhere else.

**Non-Goals:**

- Hooks or a checker. Any checking stays with this repository's tests.
- A Codex or Antigravity listing. `.agents/plugins/marketplace.json` is left
  exactly as it is.
- Linking the rule files on any machine, and enabling the plugin in any
  consuming repository. Both are a consumer's work.
- Any change to `rule-file-frontmatter`. The plugin only adopts it.

## Decisions

### D1: Name, layout and manifests

- The plugin is `plugins/plugin-rules/`, its router
  `skills/plugin/SKILL.md` with skill name `plugin`, invoked as
  `plugin-rules:plugin`. This follows the house `<domain>-rules` pattern,
  where the domain is "plugin".
- Alternatives `authoring-rules` and `rules-authoring` were rejected: a
  plugin is what the rules govern, and a reader looks for the domain by the
  thing they are editing.
- It is portable: `.claude-plugin/plugin.json` and a root `plugin.json` with
  `$schema` `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.
- Both manifests declare:
  - name `plugin-rules`, version `0.1.0`
  - one shared description
  - author `{"name": "Dmitry Tatarkin", "email": "tatarkin@gmail.com"}`
  - keywords `["plugins", "skills", "manifests", "hooks", "conventions",
    "rules"]`
- Neither manifest carries `category`. The marketplace entry carries
  `"category": "conventions"` and `"source": "./plugins/plugin-rules"`, and
  is appended after the existing eight.
- The description is the router's one-line description. Use the same text
  in the router frontmatter, both manifests and the marketplace entry:

  > Agent plugin authoring conventions — one canonical copy of each rule in
  > tool-neutral prose, a thin router skill per domain, brief rule files with
  > `paths:` frontmatter, the two portable manifests, exec-form hooks, and
  > parsing every manifest before commit. Load when writing or changing a
  > plugin's skill, rule files, manifests or hooks.

### D2: One rule file per requirement, ten in all

The planning answer fixed "one topic per requirement", so no requirements
are merged:

| Rule file | Requirement | Binds | `paths:` |
|---|---|---|---|
| `canonical-copy.md` | Each rule has exactly one canonical copy | conventions plugins | SKILL, REFS |
| `prose.md` | Rule files are tool-neutral, consumer-free prose (as modified here) | conventions plugins | REFS |
| `router.md` | One thin router skill per domain | conventions plugins | SKILL, REFS |
| `brevity.md` | Rules stay brief and split by topic | conventions plugins | REFS |
| `portable-manifest.md` | A portable plugin also carries an Agent Plugins manifest | every plugin | ROOTMAN, CLAUDEMAN |
| `hooks.md` | A plugin may ship hooks | every plugin | HOOKS |
| `manifest-validation.md` | Manifests are validated before commit | every plugin | MARKET, CLAUDEMAN, HOOKS |
| `paths.md` | A rule file declares the paths it governs (`rule-file-frontmatter`) | conventions plugins | REFS |
| `always-on.md` | A scoped rule file cannot widen into an always-on rule (`rule-file-frontmatter`) | conventions plugins | REFS |
| `scope.md` | Scoped rules state their scope (`rule-file-frontmatter`) | the scope statement | all six globs |

The globs, written exactly so:

- SKILL: `"**/skills/*/SKILL.md"`
- REFS: `"**/skills/*/references/*.md"`
- CLAUDEMAN: `"**/.claude-plugin/plugin.json"`
- MARKET: `"**/.claude-plugin/marketplace.json"`
- ROOTMAN: `"**/plugin.json"`
- HOOKS: `"**/hooks/hooks.json"`

The rejected alternative was the probe's draft of eight files. It merged the
two manifest requirements, and two frontmatter requirements into one file,
which breaks the one-to-one mapping the ADDED requirement now states.

### D3: Who each rule binds, said in the file

The manifest and hook rules bind every plugin, conventions or not. The
router and rule-file rules bind conventions plugins only. A plugin that
operates a tool keeps its topics in the same layout but is not held to them.

Each rule file says which plugins it binds, in its opening line. The
statement belongs there, not only in `scope.md`, because each file is a
canonical copy that must stand alone when it attaches by itself.

`scope.md` carries only the scope statement, in the same words as
just-rules': apply the rules to what you add or change, and leave other
content as it is.

### D4: How the rule text is generalised from the requirement

Each file states its requirement as terse imperatives with the rationale
inline, and names no consuming project:

- "this repository's console scripts" becomes "a console script the plugin's
  own repository installs".
- An enforcement clause such as "the repository's tests fail" becomes
  "check it before commit" or "hold it with a test where the repository has
  one". A rule file obliges the author, not every repository to own a test
  suite.
- A fact about this repository rather than a rule, such as "the
  repository's manifest test names which plugins are portable", is dropped.

No line opens with `@`. A file may name `SKILL.md`, `plugin.json`,
`hooks/hooks.json`, the Agent Plugins format and the hosts that read them:
that is what the modified prose requirement allows. A file never says how
it itself is loaded.

### D5: Router shape

The router is a copy of just-rules' shape:

- the router paragraph
- a table whose rows name each rule file as `references/<topic>.md`
- the closing "If a change spans several topics…" line

It has no harness variable and no cross-domain rows. A first row points at
`references/scope.md`, as just-rules' does.

### D6: Spec delta

The spec delta has three parts:

- MODIFIED "Rule files are tool-neutral, consumer-free prose": the ban on
  naming skills, plugins, marketplaces and agent products now holds unless
  they are the file's subject.
- ADDED "…delivered as the conventions plugin plugin-rules".
- ADDED "The authoring rules attach on the plugin files they govern".

The existing scenario titles are kept verbatim, because in a MODIFIED delta
a scenario's title is its identity. One scenario is added.

The rejected alternative was to state the exception only inside the
delivery requirement. That would leave the general prose rule contradicting
the plugin's own files.

`rule-file-frontmatter` gets no delta. Its scenario "Another plugin adopts
the pattern later" already describes this plugin.

### D7: No new test

The existing glob-driven tests cover the new plugin once `plugin-rules`
joins `PORTABLE`. `test_some_rule_file_declares_paths` is already
non-vacuous.

The rejected alternative was a test that maps each requirement to a rule
file. It would be brittle against wording changes, and `lint-rules` has no
counterpart.

### D8: Public naming

Artifacts, rule files and commit messages name no consuming repository and
none of the plugins kept elsewhere. A consumer is "a consuming repository".
The private-names guard enforces this at commit.

## Risks / Trade-offs

- [`**/plugin.json` also matches unrelated files named `plugin.json`, for
  example a Grafana plugin's, so `portable-manifest.md` attaches where it
  does not apply.] → The cost is one short file in context, and its opening
  line says what it binds. Narrower globs would miss a single-plugin
  repository whose manifest sits at the root.
- [`**/skills/*/SKILL.md` also matches a project's own non-plugin skills.] →
  The router and rule-file rules say they bind conventions plugins only.
- [The rumdl hook's autofix can change meaning: it turns a wrapped `#<digit>`
  into a heading and strips spaces inside code spans.] → Re-read every rule
  file after the hooks run, and never start a wrapped line with `#`.
- [The skill name `plugin` could be confused with a host's `/plugin`
  command.] → Plugin skills are always namespaced (`plugin-rules:plugin`).
  Renaming the skill is cheap until the first release.
- [The modified prose requirement is cited by specs in a consuming
  repository.] → It only narrows the ban for one subject. Every file that
  met it still meets it.

## Migration Plan

This is additive. Rolling back means removing `plugins/plugin-rules/`, its
marketplace entry, its `PORTABLE` entry and its README line. Nothing is
published before the repository's first release, so there is no installed
base to migrate.

## Assumptions

- A1: When this change is applied, the rule-linking change for this
  repository (`scripts/link-rules`) may already be on the trunk; the planned
  apply order puts it first. If `scripts/link-rules` exists, the attachment
  check in tasks.md uses it against a scratch config directory. If it does
  not, that check is skipped and the tick says so.
- A2: Live attachment in a running session is not proven here. The scoped
  rule files contract is the same one `just-rules` and `lint-rules` already
  rely on, and a consuming repository proves attachment when it links the
  files.
- A3: The topic file names and the exact wording of the descriptions are
  reversible until the first release. The one-to-one mapping and the six
  globs are not open to change.
