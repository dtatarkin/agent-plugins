# Tasks

## 1. State the rules

- [x] 1.1 In `plugins/just-rules/skills/just/references/recipes.md`, replace
  the shebang-body bullet with the script rule and make the `dbt` example a
  one-line body. Verify: no `#!` remains in the file.
- [x] 1.2 In `references/arguments.md`, forward past a named parameter with
  `shift` and `{{ quote(cmd) }}` on one line. Verify: no `#!` remains.
- [x] 1.3 Add `plugins/python-rules/skills/python/references/scripts.md`, and
  index it in the python-rules router with a row pointing at lint-rules for
  loose scripts' dependencies (design Decisions 5–6).
- [x] 1.4 Give the just-rules router a cross-domain row to python-rules
  `scripts.md`.
- [x] 1.5 Say in both `hooks/run-checker` shims why they are POSIX `sh`.
- [x] 1.6 Move `just-rules` and `python-rules` to 0.2.0 in both manifests.

## 2. Check it

- [x] 2.1 Replace the checker's `shebang` and `strict` rules with `script`
  (design Decisions 1–4).
- [x] 2.2 Update the case tables, citation evidence, hook tests and fixtures
  under `tests/justlint/`, with a case for each scenario of the delta spec.
  Verify: `uv run pytest` passes and `prek run --all-files` passes.
