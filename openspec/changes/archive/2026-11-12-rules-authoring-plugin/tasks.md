# Tasks

## 1. The plugin-rules plugin

- [x] 1.1 Create `plugins/plugin-rules/.claude-plugin/plugin.json` and
  `plugins/plugin-rules/plugin.json` as design.md D1 gives them: same name,
  version, description, author and keywords; `$schema` only in the root one;
  `category` in neither. Verify with `python -m json.tool` on both files.
- [x] 1.2 Write the seven rule files for the `agent-rules-authoring`
  requirements under `plugins/plugin-rules/skills/plugin/references/`:
  `canonical-copy.md`, `prose.md`, `router.md`, `brevity.md`,
  `portable-manifest.md`, `hooks.md` and `manifest-validation.md`.
  - Each file's `paths:` is exactly the row in design.md D2, and nothing
    else is in its frontmatter.
  - Each file opens with the line saying which plugins it binds (D3).
  - Generalise the requirement text as D4 says, stating its rationale
    inline. Use the spec as modified by this change for `prose.md`.
  - Verify by checking each file against its requirement in
    `openspec/specs/agent-rules-authoring/spec.md` and this change's delta:
    every SHALL appears, no consuming project is named, and no line opens
    with `@`.
- [x] 1.3 Write the three rule files for the `rule-file-frontmatter`
  requirements in the same directory: `paths.md`, `always-on.md` and
  `scope.md`.
  - `paths.md` and `always-on.md` follow the same rules as task 1.2.
  - `scope.md` carries the union of all six globs and only the scope
    statement (D3).
  - Verify against `openspec/specs/rule-file-frontmatter/spec.md`.
- [x] 1.4 Write the router `plugins/plugin-rules/skills/plugin/SKILL.md` in
  just-rules' shape (D5).
  - Frontmatter `name: plugin`, plus the D1 description.
  - One table row per rule file, each naming it as `references/<topic>.md`,
    with `scope.md` first.
  - Verify that each of the ten files is named exactly once and that no
    rule text is restated.
- [x] 1.5 List the plugin.
  - Append the marketplace entry to `.claude-plugin/marketplace.json`:
    category `conventions`, source `./plugins/plugin-rules`, the D1
    description, author name. Verify with `python -m json.tool`.
  - Add `"plugin-rules"` to `PORTABLE` in
    `tests/plugins/test_portable_manifests.py`.
  - Add one line to the README's "Plugins" list: `plugin-rules`, how an
    agent plugin is authored (rule files, router skills, manifests and
    hooks).
- [x] 1.6 Run `uv run pytest` and confirm it passes, including the portable
  manifest and rule frontmatter tests for `plugin-rules`.
- [x] 1.7 Check how the hooks treat the new files.
  - Run `prek run --files` over every file this section created or changed,
    or `pre-commit run --files` if prek is not available.
  - Repeat until no hook rewrites a file.
  - Re-read each rule file after the run: a wrapped line must not have
    turned into a heading, and code spans must be intact.
- [x] 1.8 Check which files would be linked.
  - If `scripts/link-rules` exists (design.md A1), run it with
    `CLAUDE_CONFIG_DIR` set to a scratch directory. Confirm that the
    scratch `rules/` gains exactly ten `plugin-rules--*.md` links pointing
    into `plugins/plugin-rules/`, then delete the scratch directory.
  - If the script does not exist, record in the tick that the check was
    skipped under A1.
- [x] 1.9 Run `openspec validate rules-authoring-plugin --strict` and
  confirm it passes.

## Workflow follow-up

- Commit section 1 as one milestone (`plugins: add plugin-rules`). The
  commit message names no consuming repository.
- Archive the change. `agent-rules-authoring` then gains the modified prose
  requirement and the two delivery requirements.
- A consuming repository enables `plugin-rules@agent-plugins` and links its
  rule files. That is not part of this change.
