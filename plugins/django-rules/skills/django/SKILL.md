---
name: django
description: Rules and patterns for writing Django code — models/fields/managers, django-ninja routers and schemas, admin, settings, app layout, and Django-specific tests. Load this whenever creating or editing Django source.
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
| App layout — `models/`/`admin/`/`tasks/`, signals, Celery tasks, app nesting | `references/structure.md` |
| Tests (Django specifics) | `references/testing.md` |

Some topics live in other domains, and this router points rather than repeats:

| You are editing… | Read |
|------------------|------|
| Env-bound configuration read by settings | `python-rules:python` → `references/config.md` |
| One class or function per file, per-package `types.py`/`consts.py` | `python-rules:python` → `references/file-organization.md` |
| Tests in general — pytest style, layout, fixtures | `python-rules:python` → `references/testing.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
