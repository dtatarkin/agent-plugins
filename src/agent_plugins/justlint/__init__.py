"""`just-lint` — the mechanically checkable half of the `just-rules` conventions.

Two modes over one engine: `just-lint check` audits a repository's justfiles,
and `just-lint hook` answers Claude Code hook events with the findings an edit
introduced. Findings come from `just --dump --dump-format json`, so they never
disagree with what `just` itself parses; the rule text they cite lives in the
plugin's `skills/just/references/` files and is never restated here.

Nothing is imported at package level on purpose: the hook path runs on every
governed edit and at every turn end, so it must stay standard-library only.
"""
