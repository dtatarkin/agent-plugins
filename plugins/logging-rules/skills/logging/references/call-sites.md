# Logging — call sites

Recommendations for emitting logs. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Obtain loggers from the stdlib: `from logging import getLogger` and a
   module-level `log = getLogger(__name__)`. Name the variable `log` (not
   `logger`) and always pass `__name__`. Do not call `structlog.get_logger()`
   in application code — structured rendering is wired at the formatter layer,
   so application code logs through plain stdlib loggers.

2. The first positional argument is a snake_case **event identifier** (e.g.
   `"webhook_received"`), not a human-readable sentence. Never capitalize it,
   never put spaces in it, and never interpolate values with an f-string —
   contextual values belong in structured data (rule 3), not the message.

3. Attach contextual key/value data through stdlib's `extra`, double-nested
   under a `data` sub-dict: `extra=dict(data=dict(field=value, ...))`. Build
   these with the `dict(...)` constructor, not `{...}` literals. Serialize
   pydantic models with `.model_dump()` before logging — never pass the model
   object directly.

4. In `except` blocks, log a snake_case event named `<operation>_error`. Use
   `log.exception(event, ...)` to capture the active exception implicitly, or
   pass `exc_info=exc` explicitly when logging a caught exception below ERROR
   level (e.g. `log.debug("validate_cache_record_error", exc_info=e)` for
   expected/recoverable noise).

5. Choose level by intent:
   - `debug` — expected, recoverable noise (e.g. cache-record validation failures).
   - `info` — normal lifecycle events (received, processed, completed).
   - `warning` — recoverable anomalies or retried conditions.
   - `error` — unexpected but handled states (unknown status, not found, invalid input).
   - `exception` — a caught exception inside an `except` block.

   Never use `log.warn` (deprecated alias — use `warning`) or `critical`.
