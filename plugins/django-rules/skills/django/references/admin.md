# Django admin — recommendations

Recommendations for Django admin. Prefer these defaults; deviate when a situation
genuinely warrants it.

1. Prefer one `ModelAdmin` per file under an `admin/` package, re-exported from
   `admin/__init__.py`. Name the file after the admin class, not after the
   model it serves — `InvoiceAdmin` lives in `admin/invoice_admin.py`. A file
   named after the model shares a basename with the model's own file, and an
   editor tab, a file search or a traceback line then leaves the reader to
   guess which of the two is meant.
   - The registered admin names the file, whatever filters, inlines or forms
     sit beside it.
2. Register with the `@register(Model)` decorator, not `admin.site.register(...)`.
3. Compose admin behavior from reusable mixins; put custom admin action forms in
   an `admin/forms/` subpackage, one per file, each named after its form class
   (`RefundForm` in `admin/forms/refund_form.py`).
4. Prefer rendering related entities as clickable links rather than raw ids —
   decorate a method returning the related object with
   `@admin_change_link("Label")` from `biased.django.admin`.
5. Register an admin for every concrete model the project defines — a model
   without one is a table only a database shell can read, and the gap is found
   on the day the row is needed.
   - An inline on a parent's page is an addition, not a substitute: the model
     gets a changelist of its own, where its rows can be filtered across
     parents.
   - A model only the system writes gets a read-only admin
     (`ReadOnlyModelAdminMixin` from `biased.django.admin`: no add, change or
     delete), not none.
   - Outside the rule: models the project does not define (the framework's, a
     third-party app's) and the tables auto-created for many-to-many
     relations.
   - Guard it with one test that walks the app registry and fails, by name, on
     a project model missing from the admin site — a list of expected models
     goes stale, the registry cannot.
