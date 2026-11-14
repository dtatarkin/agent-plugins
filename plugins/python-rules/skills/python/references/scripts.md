---
paths:
  - "**/*.py"
  - "**/*.sh"
  - "**/*.bash"
---

# Scripts — Python, not shell

Logic outgrows a shell body faster than anyone rewrites it, so it starts
where it can grow.

1. **Write a script in Python, not Bash.** Logic that would have been a
   multi-line shell body — in a justfile, a CI step, a hook — or a standalone
   shell script is a Python script. Shell's word splitting, quoting and
   silently ignored failures turn every edit into a hazard as the logic grows,
   and nothing types or tests it; a Python script gets real data structures,
   exceptions, type checking and tests, and the repository's Python lint
   reaches it.
2. **A single command is not a script.** A recipe line, CI step or hook entry
   that runs one command, or two independent ones, stays as it is.
3. **Shell is left only where Python cannot be assumed**: a shim that must run
   before any interpreter or environment exists, such as a hook launcher that
   decides whether a tool is installed. Keep it POSIX `sh`, as short as it can
   be, and say in a comment why it is shell.
4. **A script's arguments follow the CLI conventions** (`cli.md`): `typer`,
   declared wherever the repository declares its scripts' dependencies. A
   script run by the bare interpreter, in a repository with no environment to
   declare a dependency in, has the standard library alone — that is the
   zero-dependency constraint under which `argparse` is allowed. Once the
   repository declares its scripts' dependencies, the script takes `typer`
   like any other CLI.
