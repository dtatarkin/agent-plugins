# Tasks

Every verification command below uses `git grep` or `command grep`, never a
shell's `grep` wrapper (design.md, A5). Each section ends in one commit on the
current branch; nothing is pushed.

## 1. The guard

- [x] 1.1 Write `scripts/check-private-names` (bash, `#!/usr/bin/env bash`, `set -euo pipefail`) with its staged,
  `--message` and `--history` modes, list resolution and exit codes as design.md D1–D4, D6, D7 and D10 give them; make
  it executable in the index (`git add --chmod=+x`). Verify: `bash -n scripts/check-private-names` passes and `git
  ls-files -s scripts/check-private-names` shows mode `100755`.
- [x] 1.2 Write `tests/check-private-names.sh` (design.md D9), executable, asserting every scenario of
  `specs/private-names-guard/spec.md` on synthetic names in a throwaway repository; record under design.md *Findings*
  whether `git grep --cached` reads a symbolic link's target, and adjust the guard as D4 says if it does not. Verify:
  the test exits 0, and exits non-zero when one assertion is deliberately inverted (then restore it).
- [x] 1.3 Write `.pre-commit-config.yaml` holding only `default_install_hook_types`, `default_stages` and the three
  local guard hooks of design.md D8, each with its comment. Verify: `prek validate-config` and `uvx pre-commit
  validate-config` both pass.
- [x] 1.4 Run `prek install`. Verify: `.git/hooks/pre-commit` and `.git/hooks/commit-msg` both exist; `prek run
  --all-files` passes with the real list; and with `AGENT_PLUGINS_PRIVATE_NAMES` pointed at a temporary file holding the
  synthetic pattern `zz-probe-name`, `git commit --allow-empty -m 'zz-probe-name'` fails at commit-msg and leaves no
  commit (`git log -1` unchanged).
- [x] 1.5 Commit the section (`scripts: add the private-names commit guard`) with the real list in place. Verify: the
  commit succeeds with both guard hooks reported as passed.

## 2. House lint convergence

- [x] 2.1 Add the baseline, markup and shell sets to `.pre-commit-config.yaml` as design.md D8 lists them, with the
  header comment stating the derivation and why there is no top-level exclusion; pin with `prek update --cooldown-days 7
  --repo-exclude-tag https://github.com/crate-ci/typos=v1` (never `--freeze`). Verify: each `rev:` is a tag whose
  release (or, for a repository without releases, tag) date is at least seven days old, and `uvx pre-commit
  validate-config` passes.
- [x] 2.2 Write `.yamllint.yaml`, `.rumdl.toml` and `_typos.toml` with the house values of the markup and baseline
  topics (width 120; `document-start` off; MD013 tables and code blocks exempt; MD041 off), exclusions left empty for
  now. Verify: `prek run taplo-format --all-files` passes and leaves the three files unchanged.
- [x] 2.3 On a clean tree, run `prek run typos --all-files` alone and read the whole `git diff`; revert every rewrite of
  a deliberate spelling and allowlist it in `_typos.toml`. Verify: a second `prek run typos --all-files` changes
  nothing.
- [x] 2.4 Run `prek run --all-files` and fix each finding (re-read every markdown fix, design.md Risks). Then run the
  generated-tree test: `openspec update --force`, and every file it re-dirties gets the exclusion of design.md A6 on
  each rewriting hook and in `_typos.toml` / `.rumdl.toml`; the archive of closed changes is excluded by name too.
  Record the confirmed pattern under design.md *Findings*. Verify: after `prek run --all-files` passes, `openspec update
  --force` leaves `git status --porcelain` empty.
- [x] 2.5 Verify: `lint-lint check` reports nothing; the guard's hooks still carry no `files:`/`exclude:` and the
  configuration has no top-level `exclude:` (`command grep -n '^exclude:' .pre-commit-config.yaml` finds nothing).
- [x] 2.6 Commit the convergence alone (`lint: converge on the house lint sets`). If the all-files run reformatted files
  the new configuration did not add, commit those rewrites first as their own commit and list its full hash in
  `.git-blame-ignore-revs`, setting `blame.ignoreRevsFile`, as the applying topic prescribes. Verify: the commit passes
  every hook.

## 3. Repository files

- [x] 3.1 Write `LICENSE`: the MIT licence text with `Copyright (c) 2026 Dmitry Tatarkin`. Verify: the file matches the
  standard MIT text apart from the copyright line.
- [x] 3.2 Write `README.md` as design.md D12 describes. Verify: `prek run rumdl-check --files README.md` passes and the
  commands it gives (`prek install`, the variable and the fallback path) match the hook configuration and the guard.
- [x] 3.3 Write `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` as design.md D11 gives them.
  Verify: `claude plugin validate .` passes, and `claude plugin validate --strict .` passes after any metadata it asks
  for is added; if an empty `plugins` list is rejected, stop and report (design.md Risks).
- [x] 3.4 Add the `context` of design.md D12 to `openspec/config.yaml`. Verify: `openspec validate bootstrap-repository`
  still passes and `prek run yamllint --files openspec/config.yaml` is clean.
- [x] 3.5 Commit the section (`add licence, README, marketplaces and OpenSpec context`). Verify: the commit passes every
  hook.

## 4. History sweep

- [x] 4.1 Run `scripts/check-private-names --history`. Verify: it exits 0 over every commit, including the OpenSpec
  root's and the change's own commits made before the guard existed. On any finding, stop and report it; do not rewrite
  history.
- [x] 4.2 Verify nothing was pushed: `git branch -vv` shows no remote branch updated by this change, and both remotes
  are left as they were.

## Workflow follow-up

- Archive the change once its sections are landed.
- Pushing to `github` and `aws` is the owner's decision.
