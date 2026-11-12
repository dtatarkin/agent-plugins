---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/_typos.toml"
  - "**/.typos.toml"
  - "**/.gitleaks.toml"
  - "**/ruff.toml"
  - "**/.ruff.toml"
  - "**/mypy.ini"
  - "**/.mypy.ini"
  - "**/ty.toml"
  - "**/.yamllint"
  - "**/.yamllint.yaml"
  - "**/.yamllint.yml"
  - "**/.taplo.toml"
  - "**/taplo.toml"
  - "**/.rumdl.toml"
  - "**/.shellcheckrc"
  - "**/.tflint.hcl"
  - "**/.checkov.yaml"
  - "**/.checkov.yml"
  - "**/trivy.yaml"
  - "**/.trivyignore"
  - "**/.ansible-lint"
  - "**/.hadolint.yaml"
  - "**/eslint.config.*"
  - "**/.eslintrc*"
  - "**/.prettierrc*"
  - "**/prettier.config.*"
  - "**/.sqlfluff"
  - "**/.sqlfluffignore"
---

# Applying the standard

## Scope

**Apply these rules to what you add or change.** Bringing the rest of a file,
or of the repository, into line is a *separate act*, taken only when the user
asks for it. They hold in repositories whose conventions are not these too,
and are not a licence to rewrite one.

Inside a session, the checker's ratchet reports only what that session
introduced, never what the file already held.

## Which checks apply

Derive the set from the tree. Never copy another repository's configuration.

| Signal in the repository | Set |
|---|---|
| always | the baseline set |
| `pyproject.toml`, or any `*.py` | Python |
| any YAML, TOML or markdown file | markup |
| any `*.sh`, or a file carrying a shell shebang | shell |
| any `*.tf` | Terraform, and scanning |
| Ansible content (an `ansible/` directory, a collection manifest, or a role's tasks under `roles/`) | Ansible, and scanning |
| a `Dockerfile` | Dockerfiles |
| a helm chart, or Kubernetes manifests | scanning |
| `package.json` beside a package manager's lockfile, with a TypeScript or JavaScript file under it that the configuration's top-level exclusion leaves to the hooks | web |
| a dbt project file | data |
| a YAML file directly under `.github/workflows/` | CI |
| a `plugin.json` outside `.claude-plugin/` declaring the Agent Plugins schema, or a `.claude-plugin/plugin.json` or `marketplace.json` | agent plugins |

A Kubernetes manifest is a YAML file with `apiVersion` and `kind` at its top
level; a helm chart is a `Chart.yaml`. **A compose file alone derives no
hook**: neither scanner of the scanning pair reads one.
**A manifest that pins only a command-line tool derives no web set** — with no
TypeScript or JavaScript under it there is nothing for the web hooks to read —
though its lockfile is still one the repository tracks. **An action metadata
file or a dependabot file alone derives no CI set**, and **each plugin
manifest kind derives only its own check** — the agent-plugins topic says
which.

A signal the standard has no set for prescribes nothing: leave whatever the
project runs on those files alone.

**A signal is content, not a directory's name.** The table names where the
content usually sits, and the same content under another layout derives the
same set: a repository that is itself a collection — roles and a manifest at
its root, no `ansible/` directory — carries the Ansible signal all the same.
Which paths a hook then filters on is the project's, as every directory
argument is.

**A lockfile the repository tracks is a signal too.** Where it tracks one of
its own, the set brings its lockfile hooks — the one that keeps the lockfile in
step with the project file, and the dependency audit that exports it — and its
local hooks take the runner form. **A repository with a consumer pins
nothing**: one that tracks no lockfile because it is developed inside a
consumer's environment — a library, a member of another repository's
workspace — takes the by-name form for every local hook, carries neither
lockfile hook, and step 2 of the procedure adds no development dependency.
Both hooks return at the convergence after the repository starts tracking a
lockfile. Never go through a runner there: it resolves a lockfile above the
repository where there is one, which is not this repository's file, and
writes an untracked one where there is none. **A tool pre-commit installs is a
hosted hook there, pinned by `rev:`**, as its topic gives it. A repository
with **no consumer** — Python that is loose scripts with no project file — is
not that case: nothing else carries its checkers, so it takes the Python
topic's root project file and lockfile, and its hooks the runner form (the
Python topic, "Loose scripts with no project file"). Each topic gives a local
hook in both forms, or in the runner form and the hosted one for a tool hosted
where nothing pins it.

**Derivation runs in both directions.** A set whose signal the repository no
longer carries *leaves* the configuration at the next convergence, and returns
unchanged if the signal returns. The derived set and the committed
configuration are the same thing, hook for hook; a hook that stays behind
after its signal is gone breaks that, and then nobody can tell the two apart
again.

## When to converge

Converge a whole repository only when the user asks. Without a request, change
what the task requires and say nothing about the rest. A request is acted on as
it is worded: asked for a proposal, show the diff the standard implies and
write nothing; asked to converge, follow the procedure.

A repository whose consumers depend on it at pinned versions is converged under
release discipline: nothing they depend on may change. Reformatting source is
not a surface change; renaming a recipe or a configuration key consumers read
is.

## The procedure

1. Detect the signals, derive the set, and diff it against the configuration:
   `lint-lint check` does the three and exits non-zero while anything is
   wanting. Write the house entries; retire the tools the standard retires; fix
   what it names, and leave what it does not — every hook the standard does not
   cover and every project-owned value.
2. Where the repository tracks a lockfile, add the development dependencies
   it can pin and refresh it under the release-age cooldown — the language
   topic gives the setting. Where it tracks none because a consumer carries
   it, add nothing: no dependency, and no lockfile. A repository with no
   consumer takes the Python topic's project file and lockfile first.
3. Pin versions by the version procedure.
4. Write or adjust each linter's own configuration file to the house values.
5. Install the hooks in this clone. **Run the spelling hook first and alone**,
   on a clean tree, and read its whole diff before anything else runs — the
   baseline topic gives the run. Then run **every hook on all files**. Fix
   each finding, or suppress it with a reason where the tool is wrong. A hook
   that cannot run — its tool missing, its environment not entered — is an
   environment failure, not a finding: it stops the procedure.
6. Commit the convergence **alone**, separate from whatever task triggered it,
   and only when `lint-lint check` reports nothing. A run that reformatted files
   across the repository is its own commit again, and its hash is listed in
   `.git-blame-ignore-revs` — which git honours only where the clone sets
   `blame.ignoreRevsFile` to that path, so set it.
   **A line of the list holds one commit's full hash, alone or followed by a
   `#` comment**: git reads the line, comment aside, as one full object name,
   so an abbreviated hash, or a description with no `#` before it, fails every
   `git blame` in a clone that honours the list. **Before committing the list,
   run `git blame` in that clone** on a line the reformat only re-shaped:
   honoured, it names the commit that last changed the line before the
   reformat; with `--ignore-revs-file ""`, the reformat. It takes both runs —
   git skips a hash it cannot find without a word, and a line the reformat
   never touched names its earlier commit either way.

## What belongs to the project, not to the standard

Never rewrite these while converging:

- **exclusions** — a generated tree, a vendored tree, a frozen archive; the
  paths are the project's, and the test at the end of this topic is how a
  generated tree's are confirmed;
- **allowlists** — the spelling checker's accepted words, a scanner's ignore
  file, an inline suppression;
- **paths and directory arguments** that follow the repository's layout;
- **hooks for concerns the standard names no tool for** — a project's own
  drift check, a snapshot test, a generated-file check. They are the
  project's, and convergence leaves them exactly as they are.

The standard owns the tools, the hook ids, the arguments and the house
configuration values. Everything above is the repository's own knowledge of
itself.

## A generated tree is excluded by test

Which paths a generator owns is the project's to name. How they are found is
the standard's, and it is the one thing convergence does change in an
exclusion.

**Exclude exactly the files the generator rewrites, from every hook that
rewrites** — never the directory around them. A directory-wide pattern also
hides the hand-written file that sits beside the generated ones, a settings
file say, and then no hook has ever read it.

Confirm the exclusion; do not guess it:

1. Commit the generator's output.
2. Run every hook on all files.
3. Run the generator again.

The tree is clean. A file the second run re-dirties was rewritten by a hook
and belongs in the exclusion; a file it leaves alone is hand-written and
belongs out of it. A generator's header cannot stand in for the test:
generators also write files that carry none.

The rule binds the hooks that rewrite, because only they can fail the test.
Whether the read-only checks skip the generated files too is the project's.

**A frozen archive is excluded as well, by name** — closed changes, closed
roadmaps. The reason is a different one: nobody edits it, and rewriting it
edits history for no reader.
