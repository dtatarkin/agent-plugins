---
paths:
  - "**/justfile"
  - "**/.just"
---

# Consumer (per-project) files

- **The project entrypoint is `justfile`.** It pulls in the shared modules and,
  optionally, a project-local file:

  ```just
  import? ".just"          # optional: only if the local file exists

  mod test 'test.just'     # project-local submodules live alongside

  source_file := source_file()
  set dotenv-load          # only when the project uses a .env

  [default]
  [doc("List all available recipes")]
  list: (just::list source_file)
  ```

- **`.just` holds the local imports and local recipes.** It is optional and
  gitignored — the place for machine-local paths and values, written by hand in
  the checkouts that need one. Nothing commits a template it is copied from.
- **Use the optional forms `mod?` / `import?`** for anything that must parse
  *before* the shared `justfiles/` submodule is checked out — otherwise a
  non-recursive clone fails to parse. Every reference into the submodule from a
  bootstrap-reachable file takes the optional form.
- **Bootstrap-entrypoint exception.** An entrypoint `justfile` that must parse
  *and run* before `justfiles/` is checked out (an umbrella root whose `init`
  performs the submodule checkout, say) MAY inline `@just --list` in its `list`
  recipe instead of delegating to `just::list`, and MAY inline its bootstrap
  recipes (`init`, `status`) rather than forwarding to shared modules. A
  dependency on a recipe from an unresolved `mod?` is a **parse error**, so in a
  bootstrap entrypoint *every* forward into an optional module uses a
  `just <module>::<recipe>` shell-body line instead of a dependency call (`push`
  runs `just git-submodule::push`, then `just git::push`). The same applies to
  any local module the entrypoint loads **non-optionally** — it is parsed
  pre-init too, so its `list` re-spells
  `@just --justfile {{ source_file }} --list`.
