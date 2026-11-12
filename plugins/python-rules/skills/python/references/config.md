# Configuration — recommendations

Recommendations for loading and validating configuration. Prefer these defaults;
deviate when a situation genuinely warrants it.

1. Validate env-bound configuration through `pydantic-settings` `BaseSettings`
   DTOs — never bare `os.getenv` or untyped config dicts. A missing or malformed
   value then fails once, at startup, with the variable named, instead of deep
   in a request as a `None` or a string where a number was meant. Convert to
   the units an API expects (e.g. seconds) only at the boundary that requires
   it, so the rest of the code works in one typed representation.
