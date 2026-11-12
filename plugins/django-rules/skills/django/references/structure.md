# Django app structure — recommendations

Recommendations for laying out a Django app. Prefer these defaults; deviate when
a situation genuinely warrants it.

1. Explode `models.py`/`admin.py`/`tasks.py` into `models/`/`admin/`/`tasks/`
   packages, one class/function per file named after it, re-exported from
   `__init__.py`.
   - "Named after it" is the class's own name, in full: a model's file after
     the model, an admin's after the admin class — not after the model it
     serves — and an admin form's after the form. A class is then found from
     its name, and a model's file and its admin's never share a basename.
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
2. Keep a per-app `types.py` (enums/`TextChoices`, state-machine states) and
   `consts.py` (module constants); cross-app `ErrorCode` and registries live at
   the top level.
3. Use the `signals.py` (define `Signal()`s) + `signal_receivers.py`
   (`@receiver(..., dispatch_uid="app.handler")`, imported in `apps.py` `ready()`)
   split; keep one Celery task per file, registered in a top-level `CELERY_IMPORTS`.
4. Don't nest Django apps under an `apps/` subpackage — each app is a top-level
   package of the project (e.g. `myproj.billing`, not `myproj.apps.billing`).
   `INSTALLED_APPS`, `AppConfig.name`, and imports reference the app directly.
