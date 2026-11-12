---
paths:
  - "**/*.py"
---

# Typing — recommendations

Recommendations for typing Python code. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Lean on the type checker and modern typed Python: `X | None`, `StrEnum`,
   `datetime.timedelta` for durations, and `NamedTuple`/`dataclass`/Pydantic
   models for structured returns. A precise type lets the checker catch a
   misuse before it runs, and a named field or unit says what a bare tuple,
   string or number of seconds leaves the reader to guess.
