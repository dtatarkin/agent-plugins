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
