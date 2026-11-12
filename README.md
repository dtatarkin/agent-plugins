# agent-plugins

Agent plugins that carry coding conventions, for Claude Code, Codex and the
Antigravity CLI.

## Plugins

- `python-rules`: general Python conventions, from typing to tests.
- `logging-rules`: log call sites and centralized logging configuration.
- `lint-rules`: the house lint standard, with hooks that check lint
  configuration as it is edited.
- `clickhouse-rules`: reading deduplicated ClickHouse tables, and table design.
- `django-rules`: Django models, django-ninja APIs, admin, settings and tests.
- `just-rules`: justfile conventions, with hooks that check justfiles as they
  are edited.
- `metabase-rules`: Metabase queries, collections, and content kept as code.
- `redis-rules`: distributed locking with Redis.

## Install in Claude Code

```text
/plugin marketplace add dtatarkin/agent-plugins
/plugin install <name>@agent-plugins
```

The Codex marketplace file (`.agents/plugins/marketplace.json`) lists nothing
yet.

## Install the checkers

`lint-rules` and `just-rules` run their checks through two console scripts,
`lint-lint` and `just-lint`, which this repository's Python package provides:

```sh
uv tool install git+https://github.com/dtatarkin/agent-plugins
```

Both plugins work without them: their hooks then check nothing, and one notice
at session start says so.

## Attach rules on touch (Claude Code)

Some plugins carry rule files that name the paths they govern, in `paths:`
frontmatter. Claude Code attaches such a file when a matching file is read, but
only from its user-level rules directory, and installing a plugin puts nothing
there. This step is optional: without it, each plugin's rules still reach the
agent through its skill.

From your clone of this repository, link every scoped rule file into
`~/.claude/rules`, one symbolic link per file named `<plugin>--<topic>.md`:

```sh
scripts/link-rules
```

Name plugins to link only theirs:

```sh
scripts/link-rules lint-rules just-rules
```

The links point into the clone, so a `git pull` updates the rules in place.
Re-run the same command after an update: it links new rule files and removes
its links to rule files that are gone or no longer scoped. A converged run
prints nothing.

To opt out, remove the links, all of them or those of the named plugins:

```sh
scripts/link-rules --unlink
scripts/link-rules --unlink lint-rules
```

Unlink before moving or deleting the clone; a link left behind dangles, and
Claude Code ignores it.

When `CLAUDE_CONFIG_DIR` is set, the links go to `$CLAUDE_CONFIG_DIR/rules`
instead. The script never replaces a file or a link it did not make: when one
already holds a name it would use, it leaves it, says so, and exits 1 once the
rest is linked.

## Development

```sh
uv sync
uv run pytest
```

## Contributing

Install the hooks once per clone, with either runner:

```sh
prek install
# or
pre-commit install
```

One install enables both the pre-commit and the commit-msg hooks.

The hooks include a guard that fails any commit whose paths, content or
message match a list of names that must not be published. Give it the list
in one of two ways:

- the file named by the `AGENT_PLUGINS_PRIVATE_NAMES` environment variable,
  when the variable is set; or
- `~/.config/agent-plugins/private-names`, when it is not.

The file holds one POSIX extended regular expression per line; lines starting
with `#` and empty lines are ignored. Without a list, every commit fails.

`scripts/check-private-names --history` runs the same check over every commit
reachable from any ref.

## Licence

MIT; see [LICENSE](LICENSE).
