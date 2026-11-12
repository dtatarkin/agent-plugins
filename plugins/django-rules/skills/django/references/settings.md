# Django settings — recommendations

Recommendations for organizing Django settings. Prefer these defaults; deviate
when a situation genuinely warrants it.

1. Split settings by concern (base/web/celery/tests/…) and split `INSTALLED_APPS`
   into third-party vs first-party tuples composed into one list. Each process
   then loads only the settings it runs with, and the list shows at a glance
   which apps are the project's own.
