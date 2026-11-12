# Django settings — recommendations

Recommendations for organizing Django settings. Prefer these defaults; deviate
when a situation genuinely warrants it.

1. Split settings by concern (base/web/celery/tests/…) and split `INSTALLED_APPS`
   into third-party vs first-party tuples composed into one list.
2. Env-bound configuration follows the general Python `config` rule; nothing
   Django-specific is added here.
