---
paths:
  - "**/*.just"
---

# Module files

These rules govern a reusable module: a `*.just` file another file loads with
`mod`. A fragment pulled in with `import` merges into the file that imports it
and is not a module — none of the rules below apply to it.

A module is named `<name>.just` and MUST open with this preamble:

```just
mod just 'just.just'      # only if the module calls a just:: recipe

source_file := source_file()

[default]
[doc("List all available recipes")]
list: (just::list source_file)
```

- **Always assign `source_file := source_file()`.** It lets recipes name their
  own file for `just --justfile {{ source_file }} …` cross-recipe calls.
- **Every module exposes `list`**, so `just <module> list` prints its recipes.
  Delegate to `just::list` rather than re-spelling `just --list`.
- **`[default]` normally sits on `list`**, so a bare `just <module>` lists it. A
  single-purpose module — one whose name *is* its primary action, like a `test`
  module whose main recipe runs the suite — MAY put `[default]` on that recipe
  instead, so `just test` runs the tests. Keep `list` available either way.
- **Declare `mod <dep> '<dep>.just'` for every sibling module the file calls.**
