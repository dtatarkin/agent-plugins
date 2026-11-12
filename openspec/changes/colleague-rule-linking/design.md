# Design

## Context

See proposal.md for why. What the tree holds today:

- `scripts/check-private-names` is the only script. Its form is the model here:
  `#!/usr/bin/env bash`, `set -euo pipefail`, a header comment giving usage and
  exit codes, a `die` helper writing to standard error with exit 2.
- Scoped rule files are `plugins/*/skills/*/references/*.md` whose frontmatter
  carries `paths:`; 17 of them today, in three plugins. Changes planned after
  this one add more (a new plugin, an extended one), so nothing may depend on
  the count.
- `tests/plugins/test_rule_frontmatter.py` already holds every scoped file to
  the `rule-file-frontmatter` contract before commit.
- The `shellcheck` hook (shellcheck-py) selects files by `types: [shell]`, which
  detects an extensionless executable by its shebang, as it does for the guard.
  There is no shfmt hook. pytest runs `tests/`.
- A user's rules directory may already hold files and links of other origins,
  including links named `<plugin>--<topic>.md` that another tool made. The
  script must coexist with them, never fight them.

## Goals / Non-Goals

**Goals:**

- One command to opt in, the same command to converge after an update, one flag
  to opt out.
- Safe in a directory the script does not own: it removes and replaces only its
  own links.
- Runs on Linux and macOS with their stock tools.

**Non-Goals:**

- Validating the rule-file contract (the existing test does).
- Following which plugins the user has installed or enabled.
- Any host other than Claude Code; Windows.

## Decisions

### D1. A bash script, not a console script

`scripts/link-rules`, executable. The repository's Python package ships `src/`
only, not `plugins/`, so an installed console script would have no rule files
to link. Alternative rejected: a Python module that locates a clone; it would
need the clone anyway, and adds an install step.

### D2. Source root is the script's own repository

`root=$(cd "$(dirname "$0")/.." && pwd -P)`. Physical (`-P`) so that a clone
reached through a symlinked path still yields one stable prefix, which D4 relies
on. This works from any clone, including the clone Claude Code keeps for an
added marketplace; the README leads with "your clone" and does not depend on
Claude Code's internal paths.

### D3. Selection and scoped detection

Every `"$root"/plugins/*/skills/*/references/*.md` (skipping the literal glob
when nothing matches). A file is scoped when its first line is `---` and a line
starting `paths:` occurs before the next `---`:

```sh
awk 'NR == 1 && $0 != "---" { exit }
     NR > 1 && $0 == "---" { exit }
     NR > 1 && /^paths:/ { found = 1; exit }
     END { exit found ? 0 : 1 }' "$file"
```

This agrees with the contract test for every compliant file; the script does not
re-validate. Alternative rejected: parsing YAML, which would need Python and a
dependency for no gain.

### D4. Ownership is the literal target prefix

A symbolic link in the rules directory is own when `readlink "$link"` (no
flags) starts with `"$root/plugins/"`. Links are written with exactly that
absolute prefix (`ln -sfn "$root/plugins/..." "$dest/$name"`). `readlink -f`
and `realpath` are not used: older macOS lacks them, and resolving would make a
dangling link's ownership unknowable. The one resolution used is the `-ef` test
of D5, on a live link.

### D5. Per-name policy when linking

For each selected file, with `name=<plugin>--<topic>.md`:

```text
dest entry                                  action
------------------------------------------  -------------------------------
absent                                      link, print "linked <name>"
own symlink, already -ef the file           nothing
own symlink, otherwise (other file, dangling) relink, print "linked <name>"
foreign symlink that -ef the file           nothing (counts as done)
foreign symlink otherwise (incl. dangling)  leave, warn with its target, skip
regular file or anything else               leave, warn, skip
```

Any skip sets the final exit status to 1; the rest of the run proceeds. A plain
`ln -sfn` over every name (the obvious shortcut) was rejected: it would destroy
a user's own file and take over links another tool owns.

### D6. Prune before linking; narrowing is additive

Each linking run first walks every symbolic link `"$dest"/*.md`; an own link
whose target is not a regular file or is no longer scoped (D3) is removed, with
`unlinked <name>`. This runs over all own links whatever the arguments, but
removes only stale ones, so `link-rules <plugin>` never drops another plugin's
live links. Removing a plugin's links on purpose is `--unlink <plugin>`.

### D7. Arguments and exit codes

```text
scripts/link-rules [PLUGIN...]
scripts/link-rules --unlink [PLUGIN...]
scripts/link-rules -h | --help
```

Each `PLUGIN` must name a directory `"$root/plugins/$PLUGIN"`; otherwise the
script exits 2 before touching anything. `--unlink` is recognized only as the
first argument; any other argument starting with `-` is a usage error (exit 2).
`--unlink PLUGIN...` removes own links whose target lies under
`"$root/plugins/$PLUGIN/"`. Exit codes: 0 done; 1 done, at least one name
skipped (D5); 2 cannot run (usage, unknown plugin, rules directory not
creatable). Help prints usage to standard output and exits 0.

### D8. Output

One line per change on standard output: `linked <name>` or `unlinked <name>`.
Warnings go to standard error as `link-rules: <name>: <reason>`. A no-op prints
nothing, so a converged re-run is silent.

### D9. Portability

Bash 3.2 compatible (macOS's `/bin/bash`): no `mapfile`, associative arrays,
`${var,,}`, or `globstar`. Tools used: `ln -sfn`, `readlink` without flags,
`mkdir -p`, `rm --`, `awk`, `basename`, `dirname`; each is in both GNU and BSD
userlands. Unmatched globs are guarded with `[ -e "$f" ] || [ -L "$f" ] ||
continue` rather than `nullglob`.

### D10. Tests

`tests/test_link_rules.py`, beside `tests/check-private-names.sh` (it tests a
script, not a plugin). A fixture copies `scripts/link-rules` into
`tmp_path/repo/scripts/` and builds `tmp_path/repo/plugins/<p>/skills/<s>/references/`
with scoped and unscoped files for two plugins; each test runs it with
`subprocess.run`, environment `HOME=tmp_path/home` and
`CLAUDE_CONFIG_DIR=tmp_path/config`, and asserts on the rules directory, the
output and the exit code. One test per spec scenario, plus: `HOME` alone (no
`CLAUDE_CONFIG_DIR`) puts links under `tmp_path/home/.claude/rules`; and one
smoke run of the real script over the real tree asserting at least one link and
that every link `-ef`s (`os.path.samefile`) a real scoped file, never a fixed
count. Names in fixtures are synthetic.

### D11. Documentation

A README section, "Attach rules on touch (Claude Code)", after "Install the
checkers": what the script does and that it is optional; the command run from a
clone; narrowing; re-running after an update; `--unlink`; `CLAUDE_CONFIG_DIR`;
and that it never replaces a file or link it did not make.

## Risks / Trade-offs

- [A user moves or deletes the clone] -> the links dangle and Claude Code
  ignores them; running the script from the new clone prunes nothing of the old
  root (different prefix) and reports name clashes. Mitigation: the README says
  to `--unlink` before moving a clone; a stale dangling link is harmless.
- [Another tool links the same names to the same files through a different
  path] -> D5's `-ef` check treats it as done, so neither tool clobbers the
  other; if the other tool's link is dangling, this script warns rather than
  replacing it.
- [Rules for plugins the user has not installed] -> attached on touch anyway.
  Mitigation: plugin arguments narrow; documented.
- [`CLAUDE_CONFIG_DIR` semantics] -> see Assumptions A1.

## Assumptions

- A1. Claude Code reads user-level rules from `rules/` under
  `CLAUDE_CONFIG_DIR` when that is set, as it does for its other user-level
  configuration, and from `~/.claude/rules` otherwise. Not verified in this
  change; a user without the variable is unaffected either way.
- A2. Claude Code follows symbolic links in its user-level rules directory to
  targets outside any project, and attaches a linked file carrying `paths:` on
  touch.
- A3. No section of this change commits; the applier's workflow does. Nothing in
  any artifact, file or message names a repository other than this one.
