# Proposal

## Why

Some plugins here carry rule files with `paths:` frontmatter, so a harness that
attaches rules by path can deliver each one when a matching file is read. Claude
Code does that only for rule files in its user-level rules directory, and
installing a plugin puts nothing there. A user of this repository therefore has
no way to get those rules on touch short of copying files by hand, which goes
stale on the next update.

## What Changes

- Add `scripts/link-rules`, an opt-in bash script a Claude Code user runs from a
  clone of this repository. It symlinks every plugin rule file carrying `paths:`
  into `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/rules`, one link per file named
  `<plugin>--<topic>.md`. Plugin names given as arguments narrow the selection.
- A re-run converges: it relinks what it owns, removes its own links whose rule
  file is gone or no longer scoped, and leaves every other file in the directory
  alone, including a file or a foreign link that carries a name it would use.
- `--unlink` removes the script's own links (all, or those of the named
  plugins), and nothing else.
- A pytest suite runs the script against a temporary configuration directory and
  a temporary plugin tree.
- The README gains a section saying how to opt in, re-run and opt out.
- Not in this change: running the script automatically (no hook, no plugin ships
  it), any host other than Claude Code, Windows, and any change to the rule-file
  contract itself.

## Capabilities

### New Capabilities

- `rule-file-linking`: the opt-in linking of this repository's scoped rule files
  into Claude Code's user-level rules directory, how a re-run converges, what it
  never touches, and how a user opts out.

### Modified Capabilities

None. `rule-file-frontmatter` keeps its contract; this change provides the
harness setup its scenarios presuppose.

## Impact

- New: `scripts/link-rules`, `tests/test_link_rules.py`.
- Changed: `README.md` (one new section).
- The existing `shellcheck` hook lints the new script by its shebang; no hook
  configuration changes. No dependency is added.
- On a user's machine the script writes symlinks into one directory and removes
  only symlinks it made.
