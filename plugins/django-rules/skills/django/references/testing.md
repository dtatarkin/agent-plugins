# Django testing — recommendations

Django-specific testing conventions. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Gate DB access with `@pytest.mark.django_db`. A test that does not ask for
   the database cannot touch it by accident.
   - Test code that defers work with `on_commit` through the
     `django_capture_on_commit_callbacks` fixture, which captures the
     callbacks, and runs them with `execute=True`, inside the ordinary
     rolled-back test.
   - Reserve `transaction=True` for a test where another connection or thread
     must see the rows, as a Celery worker or an async path does: a
     rolled-back test transaction hides them, and a transactional test flushes
     the tables afterwards and runs far slower.
2. Build model objects with model-bakery wrapped in callable builder fixtures
   that carry sensible defaults. A test then states only the fields it is
   about, and a new required field is filled in one place, not in every test.
