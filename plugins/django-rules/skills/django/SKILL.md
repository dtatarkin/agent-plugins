---
name: django
description: Rules and patterns for writing Django code — models/fields/managers, django-ninja routers and schemas, and database migrations. Load this whenever creating or editing Django source.
---

# Django rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change you are making, then follow them.

Read the topic that matches the work:

| You are editing… | Read |
|------------------|------|
| Models, fields, managers, querysets | `references/models.md` |
| django-ninja routers, schemas, API endpoints | `references/ninja.md` |
| `ModelAdmin`, admin registration, admin forms | `references/admin.md` |
| Settings modules, `INSTALLED_APPS`, env config | `references/settings.md` |
| App layout — `models/`/`admin/`/`tasks/`, signals, `types.py`/`consts.py` | `references/structure.md` |
| Tests (Django specifics) | `references/testing.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
