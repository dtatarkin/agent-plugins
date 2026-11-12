# agent-plugins

Agent plugins that carry coding conventions, for Claude Code, Codex and the
Antigravity CLI.

The repository holds no plugin yet. The marketplace files for Claude Code
(`.claude-plugin/marketplace.json`) and Codex (`.agents/plugins/marketplace.json`)
are in place and list nothing; install instructions arrive with the first
plugins.

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
