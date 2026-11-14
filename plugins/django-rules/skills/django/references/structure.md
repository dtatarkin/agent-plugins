---
paths:
  - "**/apps.py"
  - "**/models/*.py"
  - "**/admin/**/*.py"
  - "**/tasks/*.py"
  - "**/signals.py"
  - "**/signal_receivers.py"
---

# Django app structure — recommendations

Recommendations for laying out a Django app. Prefer these defaults; deviate when
a situation genuinely warrants it.

1. Explode `models.py`/`admin.py`/`tasks.py` into `models/`/`admin/`/`tasks/`
   packages, one model, registered admin or task per file, each re-exported
   from the package's `__init__.py`; admin action forms go in an
   `admin/forms/` subpackage, one per file. Imports keep naming the package,
   and each file holds one thing to read, review and blame.
   - A file is named after the class's own name, in full: `LedgerEntry` in
     `models/ledger_entry.py`, never a shortened `models/entry.py`;
     `InvoiceAdmin` in `admin/invoice_admin.py`, after the admin class, not
     the model it serves; `RefundForm` in `admin/forms/refund_form.py`. A
     class is then found from its name, and a model's file and its admin's
     never share a basename, which would leave an editor tab, a file search
     or a traceback line for the reader to disambiguate. The class names the
     file, whatever private helpers, filters, inlines or forms sit beside it.
   - Guard the naming with one test that walks the app registry, the admin
     site and each app's `admin/forms/` package and fails, by class and
     module, on a file named otherwise — a habit drifts, and a list of
     expected files goes stale; a walk does neither.
     - Compare the two names with underscores removed and case ignored, so a
       class carrying a run of capitals (`HTTPProbe` in `http_probe.py`) has
       one spelling to match and the test needs no table of initialisms.
     - Judge a module only when it defines exactly one model, registered admin
       or form: "prefer one per file" stays a preference, not a gate.
     - Fail when a walk finds nothing to examine — a check that looks at
       nothing passes forever.
   - Outside the rule: an app still on a single `models.py` or `admin.py`, and
     a form defined in its admin's own file.
2. Define signals in `signals.py` and their receivers in
   `signal_receivers.py`, each `@receiver(..., dispatch_uid="app.handler")`,
   imported in `apps.py` `ready()`. A signal can then be imported without
   connecting anything, the receivers connect once at startup, and
   `dispatch_uid` keeps a repeated import from connecting a receiver twice.
3. Keep one Celery task per file under `tasks/`, each module registered in a
   top-level `CELERY_IMPORTS`. The worker then knows every task at startup,
   not only those some other import happened to load.
4. Don't nest Django apps under an `apps/` subpackage — each app is a top-level
   package of the project (e.g. `myproj.billing`, not `myproj.apps.billing`).
   `INSTALLED_APPS`, `AppConfig.name`, and imports reference the app directly.
   An `apps/` layer adds a segment to every import, settings entry and
   migration reference while grouping nothing the project package does not
   already group.
