# Tasks

## 1. The Codex marketplace file and its test

- [x] 1.1 Fill `.agents/plugins/marketplace.json` as design.md D2 gives it: nine entries in the order of
  `.claude-plugin/marketplace.json`. Verify: `python3 -m json.tool .agents/plugins/marketplace.json` parses it, and
  `prek run check-json --files .agents/plugins/marketplace.json` passes.
- [x] 1.2 Write `tests/plugins/test_agents_marketplace.py` as design.md D3 gives it. Verify: `uv run pytest
  tests/plugins/test_agents_marketplace.py` passes, and fails naming the plugin when one entry is deliberately dropped
  from the `.agents` file and when one path is altered (then restore the file).
- [x] 1.3 Run the suite and the hooks. Verify: `uv run pytest` passes, and `prek run --all-files` passes without
  rewriting a file.

## 2. Codex: install, skill run, hooks, and the record's first half

- [ ] 2.1 Run the Codex measurement of design.md D5 from the main checkout, against the marketplace file section 1
  landed: version, `codex plugin marketplace add <clone> --json`, `codex plugin list --available --json` (all nine
  listed; which marketplace file was read), `codex plugin add python-rules@agent-plugins --json` and the same for
  `lint-rules`. If an install fails for want of a third manifest, stop as design.md D9 says, recording under its
  "Findings". If it fails on the marketplace file's format, fix the file, re-run section 1's test, and re-measure.
  Verify: `codex plugin list --json` shows both plugins installed from `agent-plugins`.
- [ ] 2.2 Run the Codex skill run of design.md D7 and the hooks observation of design.md D8, with
  `--dangerously-bypass-hook-trust` never passed. Verify: the transcript shows the plugin's `SKILL.md` or a
  `python-rules` topic file being read and the answer drawn from it; the hooks outcome is one of not loaded, untrusted,
  fired or failed.
- [ ] 2.3 Create `docs/host-support.md` as design.md D10 gives it, with the Claude Code note, the Codex section filled
  from 2.1 and 2.2, and the Antigravity CLI section present but marked "not yet measured" (design.md A5). Verify: every
  D10 item for Codex is present; `command grep -nE '/home/|/Users/|~/' docs/host-support.md` finds nothing; `prek run
  --files docs/host-support.md` passes without rewriting it (re-read anything the markdown hook changed).

## 3. Antigravity CLI: install, subdirectory answer, skill run, hooks, and the record's second half

- [ ] 3.1 Run the `agy` measurement of design.md D6 from the main checkout: version before, `agy plugin validate
  <clone>/plugins/<name> --strict --json` and `agy plugin install <clone>/plugins/<name>` for `python-rules` and
  `lint-rules`, then inspect each installed folder for the subdirectory answer (only that plugin's files; copy or
  link; manifest mode). Stop as design.md D9 says if a third manifest is needed. Verify: `agy plugin list --json`
  shows both plugins.
- [ ] 3.2 Run the `agy` skill run of design.md D7 and the hooks observation of design.md D8, then read the version
  again. Verify: the transcript shows the plugin's `SKILL.md` or a `python-rules` topic file being read and the answer
  drawn from it; the hooks outcome is one of not loaded, fired or failed.
- [ ] 3.3 Fill the Antigravity CLI section of `docs/host-support.md` from 3.1 and 3.2, replacing "not yet measured".
  Verify: every D10 item for the Antigravity CLI is present, including the subdirectory answer; the path grep of 2.3
  finds nothing; `prek run --files docs/host-support.md` passes without rewriting it.

## 4. README install blocks

- [ ] 4.1 Edit `README.md` as design.md D11 gives it: the Codex and Antigravity CLI install blocks in place of the
  "lists nothing yet" sentence, the Antigravity block's sentence on whether the clone must stay taken from the
  subdirectory answer in `docs/host-support.md`, the hooks sentence taken from that file's hooks outcomes, and the
  pointer to `docs/host-support.md`. Verify: the README has exactly one install block for each of Claude Code, Codex
  and the Antigravity CLI and none for another host; each command it shows matches the form the record says was run,
  with the GitHub source in place of `<clone>`.
- [ ] 4.2 Check the change against its spec and run the gates. Verify: each requirement of
  `specs/host-support/spec.md` is met by the tree or the record; `openspec validate codex-and-antigravity-support
  --strict` passes; `uv run pytest` passes; `prek run --all-files` passes without rewriting a file;
  `scripts/check-private-names` passes on the change's paths once they are staged.

## Workflow follow-up

- The install from GitHub in Codex and the Antigravity CLI is run and added to `docs/host-support.md` once the
  repository is public.
- Archive the change once applied.
