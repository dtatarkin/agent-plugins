---
paths:
  - "**/views/**/*.py"
  - "**/api.py"
---

# Django APIs (django-ninja) — recommendations

Recommendations for laying out and routing HTTP APIs. Prefer these defaults;
deviate when a situation genuinely warrants it.

## Framework

1. Prefer django-ninja for all API endpoints. Its schemas are Pydantic models,
   so request validation, response serialization and the OpenAPI document
   come from one declaration.

## Files & routing

2. Prefer one endpoint per file named `<method>_<resource>.py`, with the
   handler function suffixed `_view` (`get_config_view` in `get_config.py`).
   An endpoint is found from its method and resource, and the suffix keeps a
   handler's name apart from the service function it calls.
3. Define one bare `Router(tags=["<app>"])` per app in `views/router.py`; each
   endpoint file imports that router and registers itself via
   `@<app>_router.<method>(...)`. Keep the router module free of view imports,
   and have `views/__init__.py` re-export every `*_view` so importing the
   package registers them all. A new endpoint file then joins the API without
   an edit elsewhere, and the router never imports a view that imports it
   back.
4. Mount every app's user-facing router on a single top-level `NinjaAPI` via
   `add_router("<prefix>", …)`, served from `urls.py` under
   `path("api/", api.urls)`. One API is one OpenAPI document, one auth
   default and one set of error handlers.
5. Give every route a stable `url_name=`, a human `summary=`, and a version
   prefix (`vN/…`) in its path. `reverse()` and tests then name a route rather
   than its path, the generated docs read as prose, and a breaking change
   ships beside the old version instead of replacing it.

## Integration APIs

6. Give each third-party or server-to-server integration its own `NinjaAPI`
   instance — its own module, URL prefix, `urls_namespace` and auth — rather
   than folding it into the user-facing API. A partner's credentials then
   reach only its routes, and its contract is documented and versioned apart.
