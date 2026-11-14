# Tasks

## 1. The record as a current-state table

- [ ] 1.1 Add `tests/plugins/test_host_support_record.py` per design D3, and
  verify it fails against the current `docs/host-support.md` (no table)
- [ ] 1.2 Rewrite `docs/host-support.md` per design D1 from the facts the
  current record holds, with no local path, and verify the record test passes
  and the private-names guard passes on the file
- [ ] 1.3 Reword the README's description of the record (after the install
  blocks) to say it records what each host does with the plugins as last
  verified, and verify both README links to the record still resolve with the
  link checker

## 2. Versions follow files

- [ ] 2.1 Add `tests/plugins/test_plugin_versions.py` per design D4, and
  verify it fails naming `lint-rules` 0.5.0 and passes for the other eight
  plugins
- [ ] 2.2 Add the `plugin-versions` local hook to `.pre-commit-config.yaml`
  per design D4, and verify `pre-commit run plugin-versions --all-files` runs
  the test
- [ ] 2.3 Bump `lint-rules` to 0.6.0 in both its manifests, and verify the
  version test and `tests/plugins/test_portable_manifests.py` pass
- [ ] 2.4 Add a "Releasing a plugin" section to `AGENTS.md` per design D6, and
  verify it names the bump, `claude plugin tag plugins/<name>`, pushing tags
  to both remotes with the trunk, and points to the `host-support` spec
- [ ] 2.5 Run `uv run pytest` and `pre-commit run --all-files`, and verify
  both pass

## 3. Tags

- [ ] 3.1 After the work above is committed on the trunk, run
  `claude plugin tag plugins/just-rules`, then `python-rules`, then
  `lint-rules`, and verify `git tag --points-at HEAD` lists
  `just-rules--v0.2.0`, `python-rules--v0.2.0` and `lint-rules--v0.6.0`

## Workflow follow-up

- The owner pushes the trunk and the plugin tags to `github` and `aws`.
- Archive the change.
