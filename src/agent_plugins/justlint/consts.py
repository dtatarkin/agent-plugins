"""Module constants: the rule table, the file filter, and the hook's limits."""

from datetime import timedelta

from agent_plugins.justlint.types import Rule, RuleId

# Every rule id names the `just-rules` topic file that states it. The fix is
# one line and holds no rationale: the cited file carries that, and a finding
# that restated it would be a second copy to drift.
RULES: dict[RuleId, Rule] = {
    RuleId.DOC_ATTR: Rule(
        'add a [doc("…")] attribute and drop the bare `#` help comment', "recipes"
    ),
    RuleId.PRIVATE_DOC: Rule('drop the [doc("…")] attribute', "recipes"),
    RuleId.PRIVATE_PREFIX: Rule(
        "pair a leading `_` in the name with the [private] attribute", "recipes"
    ),
    RuleId.SHEBANG: Rule(
        "open the body with `#!/usr/bin/env bash` and `set -euo pipefail`", "recipes"
    ),
    RuleId.STRICT: Rule("add `set -euo pipefail` under the shebang", "recipes"),
    RuleId.SPLAT: Rule('add [positional-arguments] and pass `"$@"`', "arguments"),
    RuleId.MODULE_PREAMBLE: Rule(
        "add `source_file := source_file()` and a `list` recipe", "modules"
    ),
    RuleId.PARSE: Rule("fix the syntax `just` refuses", "consumer"),
}

# How a rule file is cited: `skills/just/references/<topic>.md`, relative to the plugin.
TOPIC_TEMPLATE = "skills/just/references/{topic}.md"

# The entrypoint `just` looks for, and the names the checker acts on at all.
ENTRYPOINT_NAME = "justfile"
LOCAL_NAME = ".just"
MODULE_SUFFIX = ".just"

# The nested-shell commands whose quoted argument a splat may sit in: each hands
# that string to a fresh shell, which re-splits it, so a variadic inside one is
# the plain-tokens-only form the conventions sanction rather than a splat into
# this shell's text. An allowlist, not a general quote analysis.
#
# `sops exec-env` is the second family, and `sops-exec-env` catches a project
# recipe of that name wrapping it (`just sops-exec-env <file> '<command>'`),
# which is how the estate actually spells it.
NESTED_SHELL_COMMANDS = ("git submodule foreach", "sops exec-env", "sops-exec-env")

# What an interpolation contributes when the literal text around it is read.
# Anything without a quote of its own would do.
INTERPOLATION_PLACEHOLDER = "{{}}"

# `set -euo pipefail` belongs directly under the shebang, so only the opening
# lines of a body are searched for it.
STRICT_PREAMBLE_LINES = 3

# Directories a directory audit never descends into. Another repository is
# pruned separately, by its own `.git`.
PRUNED_DIRS = frozenset({".git", "node_modules", "__pycache__", ".venv", ".mypy_cache"})

# What a file-level finding is named by when it has no recipe.
FILE_SUBJECT = "<file>"

# How the hook's two reports lead, and what it says once when it cannot check.
POST_LEAD = "fix them now, before moving on"
STOP_LEAD = "still open; fix them before finishing"
NO_JUST_NOTICE = "just-lint: `just` is not on PATH, so justfile checks are off in this session."

# Marker names. The `just` notice is stated once per context; the Stop gate is
# keyed on the prompt, never on `stop_hook_active` — that flag is also true
# after another hook's block, which would skip this gate silently.
NO_JUST_MARKER = "no-just"
BLOCKED_MARKER = "blocked-{prompt}"

# `additionalContext` reaches the model inline up to 10,000 characters per
# hook; above it the harness hands over a preview the model need not open. A
# report that would exceed it is truncated with a count of the rest, so a large
# new file is still acted on.
INLINE_LIMIT = 10_000

# Where the ratchet keeps its per-context baselines. `CLAUDE_PLUGIN_DATA` is
# set for plugin hooks; the fallback keeps `just-lint hook` usable (and
# testable) outside a plugin.
STATE_ENV = "CLAUDE_PLUGIN_DATA"
STATE_DIR_NAME = "lint"
STATE_FALLBACK = ".cache/just-lint"

# Prefix of the bookkeeping files, which are not baselines: markers and guards.
MARKER_PREFIX = "_"

# How much of a path's digest names its state file. Enough to separate the
# justfiles of one context; the full path is stored inside the file.
DIGEST_LENGTH = 16

# State untouched for this long is pruned. Nothing is pruned at SessionEnd:
# desktop sessions are resumed after it, and a baseline dropped there would
# turn a violation left before the exit into legacy.
PRUNE_AFTER = timedelta(days=7)
