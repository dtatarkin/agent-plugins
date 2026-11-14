# Design

## Context

See proposal.md for why. The checker reads each recipe's body from `just`'s
own dump: its lines, and whether it opens with a shebang. The two rules it
replaces both key on those facts, so the new one needs no new parsing.

## Decisions

1. **"A command or two" is two lines.** A linewise body of up to two lines
   passes; three or more is reported. Two lines cover the sanctioned
   sequential forwards, such as a bootstrap entrypoint's `push` running one
   module's recipe and then another's, and each line is still one command
   with no state between them.
2. **Every shebang body is reported, whatever its interpreter or length.** A
   shebang exists to carry state across lines, which is the logic the rule
   moves out; an inline Python shebang is the same script hidden in the
   justfile. The finding's detail says `shebang body`.
3. **One rule id, `script`, cites `recipes.md`.** Both cases have one fix —
   move the body into a script and call it in one line — so one id keeps the
   ratchet's key per recipe stable. The `shebang` and `strict` ids go: no
   finding keeps them, and nothing is pre-release-compatible to preserve.
4. **A single line chaining commands is not checked.** Whether `a; b; c` on
   one line is "a command or two" needs judgment; the rule file states it and
   the checker leaves it, as it leaves the other judgment rules.
5. **The language rule lives in python-rules alone.** A rule file names no
   plugin, so `recipes.md` says "a script file" and the just-rules router
   carries the cross-domain row to python-rules `scripts.md`. `scripts.md`
   does not restate `cli.md`: it places the bare-interpreter case under
   `cli.md`'s existing zero-dependency exception, and leaves where a loose
   script's dependencies are declared to lint-rules `python.md`, through a
   router row.
6. **Shell keeps one narrow place.** A shim that must run before any
   interpreter can be assumed, such as a hook launcher that decides whether
   a tool is installed, stays POSIX `sh`. Without it the rule would condemn
   this repository's own `run-checker` shims, which must exit quietly on a
   host with no Python.

## Risks / Trade-offs

- Consumers whose justfiles hold shebang bodies get findings on the next
  audit. That is the rule's intent; in a session the ratchet keeps legacy
  bodies quiet until touched recipes are rewritten.
- The two-line threshold lets two unrelated commands through. Accepted: the
  owner's words are "a command or two".

## House rules

- just-rules: `recipes.md` and `arguments.md` are revised so one rule stands;
  `consumer.md`'s two-line bootstrap forward stays within it.
- python-rules: the new topic follows the recommendation-file shape; the
  checker change keeps the `_check_*` generator shape and the parametrised
  case tables.
- plugin-rules canonical-copy.md and router.md: the language rule is stated
  once, in python-rules, and reached from just-rules by a router row only.
  prose.md: rationale inline, no consuming project named.
- None broken.
