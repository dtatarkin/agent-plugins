# Django testing — recommendations

Django-specific testing conventions.

1. Gate DB access with `@pytest.mark.django_db` (`transaction=True` for
   Celery/async paths). A test that does not ask for the database cannot touch
   it by accident, and `transaction=True` lets `on_commit` callbacks and other
   connections see the rows, which a rolled-back test transaction hides.
2. Build model objects with model-bakery wrapped in callable builder fixtures
   that carry sensible defaults. A test then states only the fields it is
   about, and a new required field is filled in one place, not in every test.
