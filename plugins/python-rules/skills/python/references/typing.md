# Typing — recommendations

Recommendations for typing Python code. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Lean on the type checker and modern typed Python: `X | None`, `StrEnum`,
   `datetime.timedelta` for durations, and `NamedTuple`/`dataclass`/Pydantic
   models for structured returns.
