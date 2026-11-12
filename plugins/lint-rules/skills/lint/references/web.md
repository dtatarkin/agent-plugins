---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/eslint.config.*"
  - "**/.eslintrc*"
  - "**/.prettierrc*"
  - "**/prettier.config.*"
---

# Web

Signal: a package manifest beside a package manager's lockfile, with a
TypeScript or JavaScript file (`.ts`, `.tsx`, `.mts`, `.cts`, `.js`, `.jsx`,
`.mjs` or `.cjs`) anywhere under the manifest's directory that the
configuration's top-level exclusion leaves to the hooks. A manifest that pins
only a command-line tool derives nothing — the hooks below would have nothing
to read — though its lockfile still counts as one the repository tracks. A
hook's own `exclude:` does not take a file out of the signal; only the
top-level one does. Stylesheets and HTML templates do not carry the signal:
a server-rendered project's templates are not the web hooks' to read.

Every hook here is **local and runs through the package manager's executor**.
The tools are already pinned in the repository's own lockfile, so a hook
repository would install a second, unrelated copy — and then the gate and the
editor would disagree about the same file.

```yaml
  - repo: local
    hooks:
      - id: eslint
        name: eslint
        entry: pnpm exec eslint --fix
        language: system
        types_or: [ts, tsx, javascript, jsx]
        require_serial: true

      - id: prettier
        name: prettier
        entry: pnpm exec prettier --write --ignore-unknown
        language: system
        types_or: [ts, tsx, javascript, jsx, css, html]
        require_serial: true

      - id: typecheck
        name: typecheck
        entry: pnpm run typecheck
        language: system
        types_or: [ts, tsx]
        pass_filenames: false
        require_serial: true
```

## The formatter is scoped to code

**Markdown, YAML and JSON are deliberately absent** from the formatter's type
list. Each has a house tool in the markup and baseline topics, and a repository
that lets this formatter near them ends up with two tools rewriting one file in
opposite directions on alternate commits.

## The type check is whole-program

`pass_filenames: false`, because the checker reasons about the whole project
and a per-file invocation reports errors that depend on which files were
staged. The type filter keeps it inert on a commit that touches none.

It goes through the package's own script rather than calling the compiler
directly: the script carries the flags the project has agreed on, and
duplicating them in a hook entry is one more copy to drift.

## Substitutions

The executor follows the lockfile, and nothing else:

| Lockfile | Executor | Script runner |
|---|---|---|
| pnpm's | `pnpm exec` | `pnpm run` |
| npm's | `npm exec` | `npm run` |
| yarn's | `yarn` | `yarn` |

All three are serial, for two different reasons. The first two write files in
place, and two of them rewriting one file at once is a corrupted file, not a
race that resolves itself. The third is one whole-program invocation that
writes a build cache; a second copy racing it there rebuilds work the first
had already done, and can report against a half-written cache.

The justfile formatter of the baseline set calls the task runner **by name**
here: a node lockfile cannot pin it, and the resolution rule says a tool no
lockfile of the repository pins is called by name. No lockfile is added for
lint's sake.
