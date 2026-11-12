# Tasks

## 1. The linking script, its tests and its README section

- [ ] 1.1 Write `scripts/link-rules` as design.md D1-D9 give it: root (D2), scoped detection (D3), ownership (D4),
  per-name policy (D5), prune then link (D6), arguments, `--unlink` and exit codes (D7), output (D8), bash 3.2
  portability (D9); header comment with usage and exit codes in the style of `scripts/check-private-names`; executable
  in the index (`git add --chmod=+x scripts/link-rules`). Verify: `bash -n scripts/link-rules` passes, `git ls-files -s
  scripts/link-rules` shows mode `100755`, and `prek run shellcheck --files scripts/link-rules` passes.
- [ ] 1.2 Write `tests/test_link_rules.py` as design.md D10 gives it, one test per scenario of
  `specs/rule-file-linking/spec.md` plus the `HOME`-only and real-tree smoke tests. Verify: `uv run pytest
  tests/test_link_rules.py` passes, and fails when the D5 regular-file check is deliberately removed from the script
  (then restore it).
- [ ] 1.3 Add the README section of design.md D11. Verify: each command it shows runs as written with
  `CLAUDE_CONFIG_DIR` exported to one temporary directory (link, re-run, `--unlink`), leaving the real rules directory untouched.
- [ ] 1.4 Run the whole suite and the hooks. Verify: `uv run pytest` passes, and `prek run --all-files` passes without
  rewriting a file.
