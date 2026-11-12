# Django testing — recommendations

Django-specific testing conventions. General pytest conventions live in the
general Python `testing` rules.

1. Gate DB access with `@pytest.mark.django_db` (`transaction=True` for
   Celery/async paths).
2. Build model objects with model-bakery wrapped in callable builder fixtures
   that carry sensible defaults.
