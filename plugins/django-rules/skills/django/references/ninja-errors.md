---
paths:
  - "**/views/**/*.py"
  - "**/api.py"
---

# Django API errors (django-ninja) — recommendations

Recommendations for raising and rendering API errors. Prefer these defaults;
deviate when a situation genuinely warrants it.

1. Raise a typed exception hierarchy — a base error carrying `http_status`,
   `code` and `details`, and one subclass per HTTP status. Service code then
   signals a failure by its type, without knowing how it is rendered.
2. Centralize error shaping in `@api.exception_handler(...)` handlers that
   emit one uniform `{status, code, message, details}` envelope via
   `api.create_response(...)`. Define the handlers once and register them on
   every `NinjaAPI` rather than copying the block per API. Clients then parse
   one error shape everywhere, and a fix lands in every API at once.
3. Always carry a machine-readable `code`, from one project-wide `ErrorCode`
   enum, in an error body, plus the contextual identifiers in
   `details=dict(...)` rather than only in the message. Clients branch on the
   code, not on wording that changes, and the identifiers stay parseable.
