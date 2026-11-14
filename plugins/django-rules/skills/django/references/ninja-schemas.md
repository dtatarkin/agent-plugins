---
paths:
  - "**/views/**/*.py"
  - "**/schemas.py"
  - "**/schemas/*.py"
---

# Django API schemas (django-ninja) — recommendations

Recommendations for request and response schemas and serialization. Prefer
these defaults; deviate when a situation genuinely warrants it.

1. Build a small schema hierarchy — `BaseSchema`, `BaseRequest`,
   `BaseResponse` carrying a status enum, with `SuccessResponse` and
   `ErrorResponse` pinning that status via `Literal[...]`. Shared config lives
   in one base, and every response states on its face whether it succeeded.
2. Name a body schema `<Verb><Resource>Request` and its envelope
   `<Verb><Resource>Response`, with the payload under a named field; name an
   inner DTO `<Thing>Schema`. Alias one to the other when a request and a
   response payload coincide rather than duplicating it. The name says which
   side of which call a schema serves, and an alias keeps two identical shapes
   from drifting apart.
3. Declare `response=` as an explicit `{HTTPStatus: schema}` map enumerating
   every error status, serialized with `exclude_none=True`. The generated docs
   then show each failure a client must handle, and an absent optional field
   is omitted rather than sent as null. A simple or internal endpoint may pass
   a single schema instead of a map.
4. For a create-or-update route, return an `(HTTPStatus, schema)` tuple and
   map both statuses to one schema via
   `frozenset((HTTPStatus.CREATED, HTTPStatus.OK)): Schema`, choosing the
   status in the body. The client learns which happened from the status
   alone, and the response shape is declared once.
5. Emit snake_case JSON as-is — no alias generator, no `by_alias`, no
   `populate_by_name`. One spelling from model to wire means a field is
   searched for under one name, and no alias can go stale.
6. Push validation into the schemas — constrained `Annotated` types,
   `@model_validator(mode="after")`, discriminated unions via
   `Field(discriminator=…)` — not handler bodies, and hand-write schemas
   rather than deriving them with `ModelSchema`. A bad request is then refused
   before the handler runs, and the API contract does not change when a model
   column does.
7. Wire one shared custom JSON renderer into every `NinjaAPI`, so a decimal,
   date or enum is written the same way by every API.
8. Return a list endpoint's collection whole under a descriptive key
   (`{"orders": [...]}`), not as a bare array. The envelope leaves room for a
   count or a cursor later without breaking clients. Add a pagination
   convention for a collection that can grow large.
