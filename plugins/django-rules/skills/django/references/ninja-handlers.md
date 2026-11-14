---
paths:
  - "**/views/**/*.py"
---

# Django API handlers (django-ninja) — recommendations

Recommendations for the body and signature of an endpoint handler. Prefer
these defaults; deviate when a situation genuinely warrants it.

1. Keep a handler thin: authorize → call a `services.*` function → build a
   DTO → wrap it in the response schema. Business logic lives in `services/`,
   DTO builders in a `utils/` package beside the API. The logic is then
   reachable from tasks, commands and tests without an HTTP request.
2. Wrap a mutating handler in `transaction.atomic()`, pair the `for_update`
   authorization path with `select_for_update`, and defer an async side
   effect with `transaction.on_commit(partial(task.delay, obj.id))`. The row
   stays locked from check to write, and the task never runs against a write
   that was rolled back or is not yet visible to it.
3. Type path params directly in the signature, the body as a single
   `data: <Request>` argument, and optional filters as defaulted arguments —
   without ninja's `Query`/`Path`/`Body` markers. Ninja infers each source
   from the type and the path, so the markers add noise without information.
4. Keep handlers synchronous; reserve `async def` for an endpoint doing
   genuinely async I/O. An async handler that touches the ORM pays a thread
   hop per query and cannot use `transaction.atomic()`, which works only in
   synchronous code.
