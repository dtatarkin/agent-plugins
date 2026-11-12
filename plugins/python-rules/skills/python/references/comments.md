# Comments — what the code cannot say

A comment states what the code cannot: a constraint, a rationale, a surprise.
It is read every time the code is, so each one pays for its place or goes.

1. **Write the why, never the what.** The code already says what it does; a
   comment restating the next line, a name or a signature is noise the reader
   checks against the code and discards. Keep the non-obvious constraint, the
   workaround for a library's defect, the reason the cheaper-looking way was
   not taken — knowledge that otherwise lives only in a reviewer's head or an
   archived discussion.
2. **Give each fact one home.** A comment or docstring does not restate what
   another part of the system already states — a field's `help_text`, a
   validator's message, a constraint, another module's behaviour, a spec's
   requirement. A copy is a claim nothing checks, and it turns false silently
   the first time its original changes. Name the home instead — the function,
   the module, the capability — and keep only the why that lives nowhere
   else. Describe another module's behaviour only as far as this code depends
   on it, and say that it depends on it.
3. **Apply the deletion test.** If removing a comment loses nothing a reader
   of the code could not recover, from the code or from the home a fact
   already has, remove it. That is the whole measure — not a count, not a
   density, not one comment per function.
4. **Record no history.** No "updated to", "previously", "was X, now Y":
   version control keeps history, and a comment narrating a change is wrong
   the moment the next change lands. Say what holds now.
5. **Leave no trace of the task.** No "as requested", "per the plan", task
   numbers, ticket labels or the name of a change in flight: they point at
   context the next reader never saw. State the rationale in its own terms; a
   reference to a lasting document may supplement it, never replace it.
6. **No banners, no scaffolding.** A `# ---- helpers ----` line is structure
   the module expresses through its layout, or does not have. A `TODO` is a
   task, not a comment: do it, or report it to the user; one that stays
   carries the reason it could not be done now.
7. **Docstrings serve the caller, not the implementation.** A public name's
   docstring says what the signature does not: the contract, the units, what
   raises, what a result means. One that repeats the signature in prose —
   "Return the user's name" over `def user_name(...) -> str` — goes under the
   deletion test. A private helper needs none unless the test says otherwise.
   A docstring is written from what the author knows and the code does not
   show. One derived from reading the code, by a tool or by hand, can say
   only what the code already says, so a request to document a module is
   answered name by name under the deletion test, never with a docstring on
   every name. A module docstring orients: what the module is for, where it
   sits among its neighbours, what would surprise a reader. It is not the
   module's specification — a paragraph per field, every rule its validation
   enforces, what other commands do to its rows — which lives in the spec and
   in the code that enforces it, and reaches the docstring as a pointer.
8. **Apply this to what is added or changed.** Existing comments stay as they
   are, in their own language and tone — stripping a file of them is a change
   of its own, made when the user asks for it — and an addition matches the
   file in hand rather than standing out from it.
