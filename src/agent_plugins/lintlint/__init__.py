"""`lint-lint` — the mechanically checkable half of the `lint-rules` standard.

Two modes over one engine: `lint-lint check` audits one repository's hook
configuration and linter files against the set its tracked files derive, and
`lint-lint hook` answers Claude Code hook events with the findings an edit
introduced. The rule text the findings cite lives in the plugin's
`skills/lint/references/` files and is never restated here.

Nothing is imported at package level on purpose: the hook path runs on every
governed edit and at every turn end, so it stays on the standard library and
the YAML library this package already depends on.
"""
