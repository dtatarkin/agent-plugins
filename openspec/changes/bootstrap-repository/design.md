# Design

## Context

The repository holds one commit: the OpenSpec root as `openspec init --tools
claude` generated it (`openspec/`, `.claude/commands/opsx/`,
`.claude/skills/openspec-*/`). It has two remotes, `github` and `aws`, both
private and empty; `main` tracks `github`. There is no hook configuration and
no hook installed. See proposal.md for why the gates come before any plugin.

Constraints:

- **Everything here is public**, artifacts and commit messages included. The
  list of names the guard matches is held outside the repository, and nothing
  in the repository says more about it than the variable and the `~/.config`
  fallback the guard reads.
- **The house lint standard** (the `lint-rules` plugin's applying, baseline,
  markup, shell, stages and versions topics) decides which checks run: the set
  is derived from the repository's signals, pins are the newest tag at least
  seven days old, and the configuration must run under plain pre-commit as well
  as prek.
- The repository stays without plugin enablement: no `.claude/settings.json`.

## Goals / Non-Goals

**Goals:**

- A guard that fails closed and that no exclusion, file type or hook stage can
  route around, specified in `specs/private-names-guard/spec.md`.
- A hook configuration that equals the derived set, hook for hook, and passes
  `lint-lint check`.
- A history that is clean from the first commit, proven by a sweep at the end.

**Non-Goals:**

- A way for a contributor without the list to commit. Decided when the
  repository is made public.
- A pre-push check. The history mode makes one cheap to add later.
- Install lines, plugins, CI, agent instruction files.

## Decisions

### D1 — The variable, when set, is the only source

`AGENT_PLUGINS_PRIVATE_NAMES`, set and non-empty, names the list; its file
missing or unreadable is a failure, with no fallback. Unset (or empty), the
guard reads `${HOME}/.config/agent-plugins/private-names`. The path is written
with `$HOME`, never as a literal home directory.
*Alternative:* fall back when the variable's file is missing. Rejected: a
mis-set variable would then go unnoticed while another list is read.

### D2 — Case-sensitive POSIX extended expressions

Patterns are matched with `grep -E` / `git grep -E`, case-sensitively. The list
is written for it: portable ERE only, capitalisations spelled out. Portable ERE
keeps the guard working with GNU and BSD `grep` alike.
*Alternative:* `-i`. Not needed, since the list spells out the forms it means,
and it would make short patterns match more ordinary text.

### D3 — Fail closed on every way the list can be unusable

After stripping lines that start with `#` and empty lines, zero patterns is a
failure. The stripped patterns go to a `mktemp` file, removed by an `EXIT`
trap, and are passed with `-f`. Exit codes are read explicitly: `grep` and
`git grep` exit 0 on a match (findings → fail), 1 on none (pass), and ≥ 2 on an
error such as an invalid pattern (→ fail). `if grep …` alone would read an
error as clean. The guard exits 1 on findings and 2 when it cannot run.

### D4 — Staged mode reads the index, for every path handed to it

The pre-commit hook passes filenames and sets `types: []`, because the default
`types: [file]` would drop symbolic links (tagged `symlink` only) and submodule
paths (tagged `directory`). For the paths it is handed, the guard:

- matches the path strings (`printf '%s\n' "$@" | grep -n -o -E -f …`);
- matches content as staged: `git grep --cached -n -o -E --text -f … -- "$@"`,
  which prints `path:line:match`. `--text` keeps binary files in; `-o` prints
  the matched text rather than the whole line. A submodule path has no blob and
  gets the path check only. If the self-test shows `git grep --cached` does not
  read a symbolic link's blob, symbolic links are read with
  `git cat-file blob ":<path>"` instead.

Reading the index is exact under the runner's stash of unstaged changes, under
`--all-files`, and when run by hand on a dirty tree.
*Alternative:* `pass_filenames: false` and the guard lists the staged paths
itself. Rejected: `--all-files` would then still check only the staged diff.

### D5 — No top-level exclusion anywhere

The hook configuration has no top-level `exclude:`, and the guard's hooks no
`files:` or `exclude:`. The generated OpenSpec files and the archive of closed
changes are excluded on each hook that rewrites files, by `exclude:` on the
entry or in the tool's own configuration (`_typos.toml`, `.rumdl.toml`), and
only where the generated-tree test shows it is needed.

### D6 — Message mode drops what git strips

`scripts/check-private-names --message <file>`, run by its own hook id at the
`commit-msg` stage. The file handed to commit-msg still holds git's comment
lines (`# On branch …`) and, under `commit -v`, the diff below the scissors
line; git strips them only afterwards. The guard drops everything from the
line `# ------------------------ >8 ------------------------` on, then every
line starting with `#` (git's default comment character), and matches the rest.
Findings print as `commit message:<line>: <match>`.

### D7 — History mode

`scripts/check-private-names --history` checks, for each commit of
`git rev-list --all`: the tree's content (`git grep -n -o -E --text -f … <commit>`),
its paths (`git ls-tree -r --name-only <commit>`), and its author, committer and
message (`git log -1 --format=…`); then every ref name
(`git for-each-ref --format='%(refname)'`) and every annotated tag's message.
Findings print prefixed with the commit or ref. Whole trees per commit are
redundant work, accepted while the history is small.

### D8 — Hook configuration shape

- `default_install_hook_types: [pre-commit, commit-msg]`, so one install covers
  both stages.
- `default_stages: [pre-commit]`: with commit-msg installed, a hook whose
  manifest declares no stages would otherwise also run at commit-msg and be
  handed the message file (the spelling fixer would rewrite it). Hooks whose
  manifests declare stages keep theirs.
- Three local hooks, `language: script`: `check-private-names` (pre-commit,
  `types: []`), `check-private-names-message` (`stages: [commit-msg]`), and
  `check-private-names-selftest` (`files:` the guard and its test,
  `pass_filenames: false`). Each carries a comment saying why it takes what it
  takes.
- The derived sets: baseline (the fifteen `pre-commit-hooks` ids whole,
  `gitleaks`, `typos`, and by-name `format-justfile` and `nixfmt`, inert with no
  justfile and no nix file, by-name because the repository tracks no lockfile),
  markup (`yamllint --strict`, `taplo-format`, `rumdl-check --fix`), shell
  (`shellcheck` from `shellcheck-py`). No Python, infrastructure, web or data
  signal.
- House configuration files at width 120: `.yamllint.yaml`, `.rumdl.toml`,
  `_typos.toml`.
- A header comment states the derivation and why there is no top-level
  exclusion.

### D9 — Self-test on synthetic names, run as a hook

`tests/check-private-names.sh` builds a throwaway repository under `mktemp -d`,
points `HOME` and `AGENT_PLUGINS_PRIVATE_NAMES` at temporary files holding
synthetic patterns that match nothing real, and asserts every scenario of the
spec, including the history mode (whose fixture commit is made with
`--no-verify` inside the throwaway repository, which has no hooks). It runs as
the `check-private-names-selftest` hook whenever the guard or the test changes.
The real guard checks the test file too; its synthetic names match nothing.

### D10 — Matched text is printed

Findings print the matched text (`-o`), not just the location. Acceptable
because the guard's output only ever reaches a local terminal (the spec forbids
CI).

### D11 — Marketplace files

- `.claude-plugin/marketplace.json`: `name` `agent-plugins`, `owner`
  `{"name": "Dmitry Tatarkin", "email": "tatarkin@gmail.com"}` (the schema
  requires an owner; the author identity the plugin manifests carry), and
  `"plugins": []`. Checked with `claude plugin validate .`; `--strict` is run
  too, and a warning about missing metadata is met by adding
  `"metadata": {"description": …}`.
- `.agents/plugins/marketplace.json`: `name` `agent-plugins`, `"plugins": []`.
  No Codex validator is used here; the change that lists the first plugins for
  Codex validates it.

### D12 — README, licence, OpenSpec context

- `LICENSE`: the MIT text, `Copyright (c) 2026 Dmitry Tatarkin`.
- `README.md`: what the repository is for (agent plugins carrying coding
  conventions for Claude Code, Codex and the Antigravity CLI); that it holds no
  plugin yet and install lines come with the first plugins; *Contributing*:
  install the hooks with `prek install` or `pre-commit install`, and give the
  guard its list through `AGENT_PLUGINS_PRIVATE_NAMES` or
  `~/.config/agent-plugins/private-names`, without which every commit fails;
  *Licence*: MIT. It says nothing about who keeps the list or where it comes
  from. No bare e-mail address (the markdown fixer would autolink it).
- `openspec/config.yaml`: keeps `schema: spec-driven` and gains a short
  `context`: the repository is public; no artifact, path, commit message or
  branch name may name anything the guard's list holds; the list is described
  only as held outside the repository, through the variable and the fallback
  path; artifacts are written in English.

### D13 — Commit order during apply

Each `tasks.md` section is one commit. The guard lands first, with a hook
configuration holding only its own hooks, so that every later commit of this
change is already checked; the lint convergence is its own commit, as the
standard asks; the repository files follow; the history sweep closes the change
and commits nothing unless it finds something.

## Assumptions

- **A1** The list exists on the applying machine, at the variable's path or the
  fallback, and is current. Without it the first guarded commit fails, which is
  the intended behaviour, not a defect to work around.
- **A2** `prek`, `git`, `bash`, GNU `grep`, `claude` and `lint-lint` are on the
  applying machine's path, and the hook repositories can be fetched over the
  network. A tool that is missing stops the apply as an environment failure.
- **A3** The commits made before the guard existed (the OpenSpec root's, and the
  commit that adds this change) were swept by hand against the list before they
  were made. Section 4's history sweep confirms it.
- **A4** No global `core.hooksPath` is set on the applying machine, so the
  runner installs into `.git/hooks`.
- **A5** In an agent's shell, `grep` may be a wrapper that hides ignored files;
  verification commands in `tasks.md` use `git grep` or `command grep`, and the
  guard itself runs as a script, where `grep` is the real binary.
- **A6** The generated-tree exclusion, if the test confirms one, is
  `^(\.claude/commands/opsx/|\.claude/skills/openspec-[^/]+/|openspec/changes/archive/)`,
  repeated literally on each rewriting hook that needs it. Section 2 records the
  pattern it confirmed under *Findings* below.
- **A7** (section 1) A list line holding only whitespace counts as empty and is
  dropped, like an empty line: as a pattern it would match nearly every line.
- **A8** (section 1) Staged mode with no path handed to it checks nothing and
  exits 0, after the list has been read and compiled; it does not go looking
  for staged paths itself (D4). The pre-commit hook's entry ends in `--`, so a
  path starting with `-` is never read as an option.
- **A9** (section 1) Findings print as `path:line: match` (content),
  `path: path matches: match` (path), `path: link target matches: match`
  (symbolic link), `commit message:line: match` (message), and, in history
  mode, the same prefixed with the commit id, with `ref` and the ref name, or
  with the tag's ref name.
- **A10** (section 1) The guard and its self-test run `unset -f grep` before
  their first `grep`, so a shell function of that name never stands in for the
  binary; the self-test also unsets git's per-repository variables
  (`git rev-parse --local-env-vars`) and the committer's git configuration, so
  that running as a hook does not leak into its throwaway repository.
- **A11** (section 1) The section-1 hook configuration holds only the guard's
  hooks (task 1.3); the `lint-lint` edit hook reports every house hook as
  missing until section 2 adds them, which is expected, not a finding to fix
  here. `shellcheck` was run by hand (`uvx --from shellcheck-py shellcheck`)
  on both scripts and is clean.
- **A12** (section 2) The archive part of the exclusion is applied to every
  rewriting hook by name, as the frozen-archive rule asks, though the archive
  is empty today; the read-only checks (`check-yaml`, `yamllint`, `gitleaks`,
  `shellcheck` and the rest) still read the generated files and the archive.
- **A13** (section 2) `tasks.md` lines are wrapped at 120 with two-space
  continuation lines, to meet MD013; the OpenSpec CLI still counts every task,
  and reports only a task's first line as its description. The section-2
  all-files run reformatted no file outside what the configuration added (its
  one markdown fix, in this design, was replaced by a hand rewording), so no
  separate reformat commit and no `.git-blame-ignore-revs` were needed.
- **A14** (section 2) `typos` accepts `mis` (the prefix in "mis-set") through
  `_typos.toml`; it rewrote nothing on its solo run.
- **A15** (section 2) "The guard's hooks carry no `files:`/`exclude:`" is read
  as the two checking hooks; the self-test hook keeps the `files:` D8 gives it,
  which narrows only when the test runs, never what the guard checks.
- **A16** (section 3) `claude plugin validate .` (Claude Code 2.1.316) accepts
  the empty marketplace, with one warning: the marketplace defines no plugins.
  That is task 3.3's pass. `claude plugin validate --strict .` fails on that
  warning alone, once the requested `metadata.description` is present, and
  cannot pass until a plugin is listed; the first change that adds a plugin
  re-runs `--strict` (a later slot makes `--strict` a lint check). No
  placeholder plugin is added.

## Risks / Trade-offs

- [The guard fails closed for anyone without the list] → intended while the
  repository is private and has one committer; the change that makes it public
  decides how others commit.
- [`git commit --no-verify`, or a commit made outside the hooks, skips the
  guard] → the history mode catches it; run it before any push.
- [The list is only as complete as its keeper makes it] → out of this
  repository's reach; the guard enforces whatever the list holds.
- [`rumdl-check --fix` can turn a wrapped line starting `#<digit>` into a
  heading, and strip spaces inside code spans] → read every change the fixer
  makes before committing.
- [The spelling fixer rewrites in place, silently] → run it alone first and read
  its whole diff, as the baseline topic prescribes.
- [Claude Code might reject an empty `plugins` list] → `claude plugin validate`
  in section 3; if it does, stop and report rather than inventing a placeholder
  plugin.

## Findings

Recorded by the apply sections for the sections after them.

- Generated-tree exclusion confirmed (section 2): **A6 as written**,
  `^(\.claude/commands/opsx/|\.claude/skills/openspec-[^/]+/|openspec/changes/archive/)`.
  In a throwaway worktree with every exclusion removed, `prek run --all-files`
  followed by `openspec update --force` (CLI 1.16.0) re-dirtied exactly the 24
  generated files under `.claude/commands/opsx/` and
  `.claude/skills/openspec-*/` (rewritten by `rumdl-check --fix`) and nothing
  else; on the generated tree alone, `openspec update --force` changes nothing.
  The pattern sits on every rewriting hook (`trailing-whitespace`,
  `end-of-file-fixer`, `mixed-line-ending`, `taplo-format`, `rumdl-check`), and
  as globs in `_typos.toml` and `.rumdl.toml`; with it, `openspec update
  --force` after a passing all-files run leaves the tree unchanged.
- Symbolic-link blob read by `git grep --cached` (section 1): **not read**.
  With git 2.53.0, neither `git grep --cached` nor `git grep <commit>` matches
  a symbolic link's target, so the guard reads every link's blob with
  `git cat-file blob` instead, in staged mode (links found through
  `git ls-files -s`, mode `120000`) and in history mode (through
  `git ls-tree -r`). The self-test covers both.
