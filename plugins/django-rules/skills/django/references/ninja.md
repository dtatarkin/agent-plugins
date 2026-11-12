# Django APIs (django-ninja) — recommendations

Recommendations for building HTTP APIs. Prefer these defaults; deviate when a
situation genuinely warrants it.

## Framework

1. Prefer django-ninja for all API endpoints.

## Files & routing

2. Prefer one endpoint per file named `<method>_<resource>.py`, with the handler
   function suffixed `_view` (e.g. `get_config_view`).
3. Define one bare `Router(tags=["<app>"])` per app in `views/router.py`; each
   endpoint file imports that router and self-registers via
   `@<app>_router.<method>(...)`. Keep the router module import-free of views;
   `views/__init__.py` re-exports every `*_view` to trigger registration.
4. Assemble all per-app routers on a single top-level `NinjaAPI` via
   `add_router("<prefix>", …)`, mounted in `urls.py` under `path("api/", api.urls)`.
5. Give every route a stable `url_name=`, a human `summary=`, and a version prefix
   (`vN/…`) in the path.

## Schemas & serialization

6. Build a small schema hierarchy — `BaseSchema`, `BaseRequest`, `BaseResponse`
   (carrying a status enum), with `SuccessResponse`/`ErrorResponse` pinning status
   via `Literal[...]`.
7. Name body schemas `<Verb><Resource>Request` and envelopes
   `<Verb><Resource>Response` (payload under a named field); name inner DTOs
   `<Thing>Schema`. Alias when request/response payloads coincide rather than
   duplicating.
8. Declare `response=` as an explicit `{HTTPStatus -> schema}` map enumerating
   every error status, serialized with `exclude_none=True`. (Simple/internal
   endpoints may pass a single schema instead of a map.)
9. For create-or-update routes, return a `(HTTPStatus, schema)` tuple and map both
   statuses to one schema via `frozenset((CREATED, OK)): Schema`, choosing the
   status in the body.
10. Emit snake_case JSON as-is — no alias generator, no `by_alias`, no
    `populate_by_name`.
11. Push validation into Pydantic schemas (constrained `Annotated` types,
    `@model_validator(mode="after")`, discriminated unions via
    `Field(discriminator=…)`), not handler bodies; hand-write schemas (no
    `ModelSchema`).
12. Wire one shared custom JSON renderer into every `NinjaAPI` for consistent
    serialization.

## Auth & authorization

13. Configure authentication once on the `NinjaAPI` (via `auth=(...)`); opt
    individual public routes out with per-route `auth=None`.
14. Resolve authorization with an explicit per-call helper
    (`authorize_*_access(request, …)`) at the top of each handler — returning the
    authorized model or raising Forbidden/404, with a `for_update` flag for
    row-locking — not middleware or ninja deps.

## Errors

15. Raise a typed exception hierarchy — a base error carrying `http_status` +
    `code` + `details`, one subclass per HTTP status.
16. Centralize error shaping in `@api.exception_handlers` that emit one uniform
    `{status, code, message, details}` envelope via `api.create_response(...)`.
    Prefer sharing this block across APIs over copy-pasting it per API.
17. Always carry a machine-readable `code` (a project-wide `ErrorCode` enum) in
    error bodies, plus contextual identifiers in `details=dict(...)`, not only in
    the message.

## Handler shape

18. Keep handlers thin: authorize → call a `services.*` function → build a DTO →
    wrap in the response schema. Business logic lives in `services/`, DTO builders
    in `frontend_api/utils/`.
19. Wrap mutating handlers in `transaction.atomic()`, pair the `for_update`
    authorize path with `select_for_update`, and defer async side-effects with
    `on_commit(task.delay)`.
20. Type path params directly in the signature, the body as a single
    `data: <Request>` arg, and optional filters as defaulted args — without ninja's
    `Query`/`Path`/`Body` markers (ninja infers from type + path).
21. Keep handlers synchronous (the Django ORM is sync); reserve `async def` for
    endpoints doing genuinely async I/O.

## Structure

22. Isolate third-party/server-to-server integrations as their own `NinjaAPI`
    instance (own module, URL prefix, and auth) rather than folding them into the
    user-facing API.
23. Return list endpoints as a full collection under a descriptive key (`accounts`,
    `beneficiaries`). Add a pagination convention for collections that can grow
    large.
