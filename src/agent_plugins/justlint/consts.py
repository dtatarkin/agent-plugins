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

# Directories a directory audit never descends into. Another repository is
# pruned separately, by its own `.git`.
PRUNED_DIRS = frozenset({".git", "node_modules", "__pycache__", ".venv", ".mypy_cache"})

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

# State untouched for this long is pruned. Nothing is pruned at SessionEnd:
# desktop sessions are resumed after it, and a baseline dropped there would
# turn a violation left before the exit into legacy.
PRUNE_AFTER = timedelta(days=7)
