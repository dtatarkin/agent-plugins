---
paths:
  - "**/models.py"
  - "**/models/*.py"
---

# Django model validation and constraints — recommendations

Recommendations for model-level validation and database constraints. Prefer
these defaults; deviate when a situation genuinely warrants it.

1. Put cross-field invariants in `clean()`, raising
   `ValidationError(message, code="snake_case_code")` with a stable
   machine-readable code, and reserve database constraints for true
   uniqueness. Forms and the admin call `clean()` and show the message beside
   the form, and the code lets callers and tests match the failure without
   parsing text. `save()` does not call `clean()`, so code that writes rows
   outside a form calls `full_clean()` first.
2. Express composite uniqueness as a named `UniqueConstraint` in
   `Meta.constraints`, not `unique_together`. Django's documentation steers
   new code to `UniqueConstraint` and warns that `unique_together` may be
   deprecated; a constraint also takes a `condition`, and `nulls_distinct`
   where the database supports it, and its name identifies it in an
   integrity error.
