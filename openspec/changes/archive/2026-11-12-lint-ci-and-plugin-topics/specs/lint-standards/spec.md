# Spec Delta

## MODIFIED Requirements

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
with it as any derived hook does. A GitHub Actions workflow SHALL derive the
CI set, and an agent plugin manifest SHALL derive the agent-plugins set: a
portable manifest declaring the Agent Plugins schema derives its schema check,
and a Claude plugin or marketplace manifest derives the host's validator.

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

#### Scenario: A repository tracks a GitHub Actions workflow

- **WHEN** an agent derives the checks for a repository tracking a YAML file
  directly under `.github/workflows/`
- **THEN** the derived set carries the CI set: the workflow linter, the
  workflow security auditor and the workflow schema check
- **AND** an action metadata file or a dependabot file alone derives none of
  them

#### Scenario: A repository tracks plugin manifests

- **WHEN** an agent derives the checks for a repository tracking a portable
  plugin manifest that declares the Agent Plugins schema, and a Claude plugin
  manifest or marketplace manifest
- **THEN** the derived set carries the schema check for the portable manifest
  and the host's validator for the Claude manifests
- **AND** a repository tracking only one kind derives only that kind's check

#### Scenario: A plugin.json declares no Agent Plugins schema

- **WHEN** a repository tracks a `plugin.json` that is not under
  `.claude-plugin/` and does not declare the Agent Plugins schema
- **THEN** no schema check is derived for it

### Requirement: One house tool per concern, with two deliberate pairs

For each concern the standard covers it SHALL name exactly one tool, and it
SHALL name the tools it retires, so that a converged configuration carries no
second tool for a concern. Two concerns are deliberate pairs and SHALL be
stated as such: Python type checking runs mypy and ty, both blocking, with
mypy as the reference gate; infrastructure scanning runs checkov and trivy's
configuration scan, and a finding both raise is suppressed in the tool that
raised it, always with a reason. A set may cover several concerns, one tool
each, and SHALL name them: the CI set is three concerns — workflow semantics,
workflow security and workflow schema — and the agent-plugins set is two, one
per manifest kind, the portable manifest's schema and the Claude manifests'
host validation. Link resolution in markdown is a concern of the markup set,
separate from markdown style.

#### Scenario: The house tools are read

- **WHEN** the standard is consulted for a concern
- **THEN** it names one tool: the hygiene hook set with private-key detection
  for file hygiene, gitleaks for secret scanning, typos for spelling, the
  justfile formatter for justfiles, nixfmt for nix, ruff for Python linting
  and formatting with its security rules in place of bandit, the lockfile
  hook and the project-file validator for Python packaging, yamllint for
  YAML, taplo for TOML, rumdl for markdown, lychee offline for relative
  links, shellcheck for shell, terraform's
  own formatter and validator with tflint for terraform, ansible-lint for
  ansible, hadolint for Dockerfiles, eslint and prettier with the project's
  type checker for web code, and sqlfluff with dbt's own parse and the
  dbt-checkpoint hooks for dbt projects, actionlint for workflow semantics,
  zizmor offline for workflow security, check-github-workflows for the
  workflow schema, check-jsonschema against the Agent Plugins schema for a
  portable plugin manifest, and `claude plugin validate --strict` for a Claude
  plugin or marketplace manifest

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

#### Scenario: A set covers several concerns

- **WHEN** the CI set or the agent-plugins set is read
- **THEN** each of its tools is named for its own concern, and no two of them
  are a pair for one concern
