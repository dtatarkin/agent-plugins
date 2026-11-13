# Tasks

## 1. Amend the standard

- [x] 1.1 In `plugins/lint-rules/skills/lint/references/markup.md`, section
  "Links", write the entry as
  `args: [LYCHEE_VERSION=<version>, --offline, --no-progress]` and state the
  reason beside it. Verify: the hosted script hook is still the one chosen.
- [x] 1.2 In `references/versions.md`, say the override moves with the `rev:`
  when the pin is bumped.

## 2. Check it

- [x] 2.1 Add the version-override rule to `src/agent_plugins/lintlint/`
  (design Decisions 1–4).
- [x] 2.2 Give the fixtures and inline configurations under `tests/lintlint/`
  the override, and add tests for each scenario of the delta spec.
- [x] 2.3 Give this repository's `.pre-commit-config.yaml` the override.
  Verify: `uv run pytest` passes and `prek run --all-files` passes.
