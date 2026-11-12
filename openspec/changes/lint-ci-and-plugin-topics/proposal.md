# Proposal

## Why

The lint standard has no check for two kinds of files that this repository and its consumers carry or will carry:
GitHub Actions workflows, and agent plugin manifests. Its markup set also never checks that a relative link in a
markdown file resolves. This repository now publishes plugins, so a malformed manifest or a dead link to a topic file
reaches every installer. A repository that adds CI should get the workflow checks from its signals, not from someone
remembering them.

## What Changes

- **A new `ci` topic**, derived where a repository tracks a GitHub Actions workflow. It has three hosted hooks, one per
  concern:
  - `actionlint` checks workflow semantics;
  - `zizmor`, run offline, checks workflow security;
  - `check-github-workflows` checks the workflow schema.
- **A new `agent-plugins` topic**, derived from the plugin manifests a repository tracks:
  - `check-jsonschema` validates a portable manifest (a `plugin.json` declaring the Agent Plugins schema) against the
    schema that the manifest names. The schema is fetched over the network, so the check runs in the manual stage
    unless a design spike shows that a cached schema validates offline.
  - `claude plugin validate --strict` validates each Claude plugin manifest and marketplace manifest. It is a local
    hook that calls `claude` by name.
- **`lychee` joins the markup set**, run offline, so a relative link that does not resolve fails the commit.
- **The house-tools requirement is amended.** "One house tool per concern" now names `ci` as three concerns
  (semantics, security, schema) and `agent-plugins` as two (one per manifest kind). It also names `lychee` for link
  resolution. Its two deliberate pairs are unchanged.
- **The `lint-lint` checker** derives the three new signals and the new hooks, and enforces their canonical entries:
  the offline flags, `--strict`, and the manual stage of the schema check. A `check-jsonschema` entry pointed at any
  other schema is left to the project.
- **This repository converges** on what its own signals derive: `lychee`, `check-jsonschema` and
  `claude-plugin-validate`. It tracks no workflow, so the `ci` topic is proven by the checker's tests, not by this
  repository's configuration.
- **`lint-rules` gets a minor version bump**, in both of its manifests.
- **Accepted reach.** The new topics reach every repository with markdown or plugin manifests. Their audits will report
  the new hooks as missing until each is converged on request. No other repository is converged by this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `lint-standards`: the signals requirement gains the workflow and plugin-manifest signals. The house-tools requirement
  names the new tools and how they relate to one tool per concern.
- `lint-checking`: the enforced-rules requirement covers the new canonical entries. The project-owned requirement
  leaves a schema check of any other schema to the project.

## Impact

- `plugins/lint-rules/`:
  - new topics `ci.md` and `agent-plugins.md`;
  - changed `markup.md`, `applying.md`, `stages.md`, `versions.md` and the router;
  - version bump in both manifests.
- `src/agent_plugins/lintlint/`: `types.py`, `consts.py`, `signals.py` and `rules.py`.
- `tests/lintlint/`: the signal, rule and citation tests, and the fixture configurations, which gain `lychee` because
  every fixture carries markdown.
- `.pre-commit-config.yaml`: three new hooks. Committing to this repository now needs `claude` on `PATH`. Its absence is
  an environment failure, not a finding.
- No other repository changes. A consuming repository picks up the new topics and checker when it next updates the
  plugin and the checker.
