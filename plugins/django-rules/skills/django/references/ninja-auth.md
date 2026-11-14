---
paths:
  - "**/views/**/*.py"
  - "**/api.py"
---

# Django API authentication and authorization (django-ninja) — recommendations

Recommendations for who may call an endpoint and what it may touch. Prefer
these defaults; deviate when a situation genuinely warrants it.

1. Configure authentication once on the `NinjaAPI` (via `auth=(...)`), and
   opt an individual public route out with a per-route `auth=None`. A new
   route is then protected by default, and every public one is visibly
   marked.
2. Resolve authorization with an explicit per-call helper
   (`authorize_<resource>_access(request, …)`) at the top of each handler —
   returning the authorized object or raising Forbidden or 404, with a
   `for_update` flag that locks the row — not in middleware or ninja
   dependencies. The check sits beside the code it guards, takes the
   handler's own arguments, and hands back the row it checked, so the handler
   cannot go on to act on a different one.
