---
paths:
  - "**/*.py"
---

# Error handling — recommendations

Recommendations for signalling failure. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Signal failure by raising an exception — never by returning it. No error
   sentinels, status codes, `(value, error)` tuples, or `Result`/`Either`
   wrappers. Raising keeps the happy path free of error-checking, makes a failure
   impossible to ignore silently, and unwinds to the nearest handler without
   manual propagation. A returned `None`/empty value is for an expected
   *absence*, not a failure.
