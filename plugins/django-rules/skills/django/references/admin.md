---
paths:
  - "**/admin.py"
  - "**/admin/**/*.py"
---

# Django admin — recommendations

Recommendations for Django admin. Prefer these defaults; deviate when a situation
genuinely warrants it.

1. Lay out and name admin and admin-form files as the app-structure rules
   state.
2. Register with the `@register(Model)` decorator, not `admin.site.register(...)`.
   The registration then sits on the class it registers, and moving or
   deleting the class takes it along.
3. Compose admin behavior from reusable mixins. A behavior several admins
   share — read-only fields, an export action — is then written and fixed
   once.
4. Prefer rendering related entities as clickable links rather than raw ids —
   decorate a method returning the related object with a shared link helper,
   such as `@admin_change_link("Label")` from `biased.django.admin`. A link
   takes the reader to the related row in one click, where a raw id has to be
   copied into a search.
5. Register an admin for every concrete model the project defines — a model
   without one is a table only a database shell can read, and the gap is found
   on the day the row is needed.
   - An inline on a parent's page is an addition, not a substitute: the model
     gets a changelist of its own, where its rows can be filtered across
     parents.
   - A model only the system writes gets a read-only admin (no add, change or
     delete, such as through `ReadOnlyModelAdminMixin` from
     `biased.django.admin`), not none.
   - Outside the rule: models the project does not define (the framework's, a
     third-party app's) and the tables auto-created for many-to-many
     relations.
   - Guard it with one test that walks the app registry and fails, by name, on
     a project model missing from the admin site — a list of expected models
     goes stale, the registry cannot.
