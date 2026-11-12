---
paths:
  - "**/.pre-commit-config.yaml"
  - "**/_typos.toml"
  - "**/.typos.toml"
  - "**/.gitleaks.toml"
---

# The baseline set

Every repository runs this, whatever it is written in.

## File hygiene

```yaml
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: mixed-line-ending
        args: [--fix=lf]
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: check-symlinks
      - id: destroyed-symlinks
      - id: check-executables-have-shebangs
      - id: check-shebang-scripts-are-executable
      - id: debug-statements
      - id: detect-private-key
```

Fifteen ids, taken **whole**. They are cheap, they carry their own type
filters, and the set is easier to reason about as one block than as a
per-repository selection — a repository that drops three of them has no record
of why.

`mixed-line-ending` is the only one that needs an argument: without `--fix=lf`
it normalises to whatever the file already has most of, which is not a
decision, it is a coin toss.

`debug-statements` is Python-only. It stays in this set rather than moving to
the Python topic because it is inert elsewhere — its own `types: [python]`
sees to that — and because the hygiene set is taken whole. Its placement is
deliberate, not an oversight.

`check-case-conflict` carries no type filter of its own and runs over
everything; that is correct, a filename collision is not a property of a file
type.

`check-json` reads **strict** JSON. A file that is JSON with comments — a
compiler's configuration, an editor's settings — fails it at the first
comment, and that is not a finding to fix: the file's own reader accepts
comments. The project excludes such a file from this one hook, with `exclude:`
on the entry.

## Secret scanning

```yaml
  - repo: https://github.com/gitleaks/gitleaks
    hooks:
      - id: gitleaks
```

**It ignores filenames.** The hook runs with `pass_filenames: false` and scans
the staging area itself, so `files:` and `exclude:` on this entry do nothing —
narrowing it means a `.gitleaks.toml` allowlist, and nothing else. Write the
reason beside every allowlist entry, because an unexplained one is
indistinguishable from a leak someone got tired of.

## Spelling

```yaml
  - repo: https://github.com/crate-ci/typos
    hooks:
      - id: typos
```

**The default arguments make it a fixer**, not a checker: it rewrites files in
place and honours the exclusions in its own configuration. Supplying `args:`
**replaces** those defaults rather than adding to them — so a project that
needs an extra flag repeats the write-changes and force-exclude flags beside
it, or it has quietly turned the fixer into something else.

Its configuration file carries the exclusions:

```toml
[files]
extend-exclude = ["uv.lock", "vendored/"]
```

**At a convergence, run it first and alone.** A test that proves an unknown
field is rejected feeds the loader a *misspelled* field; correcting it makes
the field known and the test passes vacuously. Because this hook rewrites in
place, that damage is silent — and in an all-files run it lands among every
other hook's changes, where a wrong correction cannot be told from a right
one. So:

1. Start from a clean working tree.
2. Run this hook alone, by its id, on all files:

   ```text
   prek run typos --all-files
   ```

3. Read `git diff` whole. It holds this hook's rewrites and no other hook's.
4. Revert each rewrite of a deliberate spelling — an identifier, a path, a
   quoted string, a name under test — and allowlist the spelling.
5. Only then run the whole set.

**A search of the tree is not enough.** A search finds what the searcher
thinks to look for — fixtures named for the error they carry, quoted error
strings. The diff finds what the tool does, and what it does is respell a role
string, a public module path, a test's name. It costs one command.

**Every convergence, not only the first.** A release the pin moves to corrects
words the earlier one left alone, so a repository that has run the hook for
months meets new rewrites on the day its pin moves.

Lockfiles and vendored trees are excluded because neither is text anyone wrote:
a hash that spells a word is not a typo, and a vendored repository's spelling
is its own repository's business. **The accepted-words list is the project's**,
not the standard's — a domain term is a fact about the project:

```toml
[default.extend-words]
[default.extend-identifiers]
```

A word goes in the first table and is accepted wherever it appears; a whole
identifier goes in the second and leaves the word itself checked elsewhere.
Each entry maps the spelling to itself.

Its repository also publishes a moving major tag; the version topic says what
that means for the pin.

## Justfile formatting

A local hook, because the formatter is the task runner itself and no hook
repository ships it in a form worth pinning:

```yaml
  - repo: local
    hooks:
      - id: format-justfile
        name: format justfile
        entry: bash -c 'for f in "$@"; do uv run just --fmt --unstable --justfile "$f"; done' --
        language: system
        files: (^|/)justfile$|\.just$
```

The loop is not decoration: the formatter takes **one** file at a time, and the
hook runner passes many.

**Which `just` runs is the tool-resolution rule, not a preference.** Where the
repository's own lockfile pins the formatter, run it through that lockfile's
runner — as above. Where no lockfile of the repository can pin it, call it by
name and expect it on the path:

```yaml
        entry: bash -c 'for f in "$@"; do just --fmt --unstable --justfile "$f"; done' --
```

Formatter output differs between builds, so a repository that formats with one
build and rewrites with another will disagree with itself about one file.
**Anything else that *formats* a justfile — a recipe, a script — resolves
`just` by this same rule, for that reason.** A checker that only reports on the
structure `just` parses is exempt: parsed recipe structure does not move with
the pin, and a checker that never rewrites the file cannot disagree with the
formatter about it.

Never pin the formatter inside the hook entry itself. A pin belongs in the
lockfile, where the rest of the repository can see it; a pin buried in a hook
argument is invisible to every tool that resolves dependencies.

Do not use a third-party justfile hook repository. The ones that exist flap
between runs and miss `*.just` module files entirely.

## Nix formatting

```yaml
      - id: nixfmt
        name: nixfmt
        entry: nixfmt
        language: system
        files: \.nix$
```

By name: no lockfile pins it, and where a project pins its toolchain the pinned
copy is the one on the path. **Inert in a repository with no nix file** — which
is most of them — so it costs nothing to carry, and a repository that gains a
flake gets formatting the same day. **It is carried in a repository with no
nix file all the same, and its absence there is reported**: the baseline set
does not wait for its signal.

A by-name hook whose tool nothing provides is an *environment failure*, not a
finding: if a repository has nix files, the tool has to be reachable before the
configuration lands. Verified on a scratch tree holding a single
badly-formatted nix file, because the repositories this set was drawn from keep
their flakes at the umbrella root and none of them is a repository of its own:
with the tool on the path the first run reformatted the file and the second
passed clean, and with it off the path the hook failed saying the executable
was not found. The tool came from `nixpkgs#nixfmt`, which is the RFC-style
formatter now — `nixfmt-rfc-style` is an alias for the same derivation, and
`nixfmt-classic` has been removed from nixpkgs.
