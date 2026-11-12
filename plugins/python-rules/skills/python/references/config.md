# Configuration — recommendations

Recommendations for loading and validating configuration. Prefer these defaults;
deviate when a situation genuinely warrants it.

1. Validate env-bound configuration through `pydantic-settings` `BaseSettings`
   DTOs — never bare `os.getenv` or untyped config dicts. Convert to the units an
   API expects (e.g. seconds) only at the boundary that requires it.
