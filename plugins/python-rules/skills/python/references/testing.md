# Testing — recommendations

General pytest conventions. Prefer these defaults; deviate when a situation
genuinely warrants it.

1. Prefer pytest with plain `assert`. Pytest rewrites the assertion to show
   both sides on failure, so no `assertEqual` family is needed to get a useful
   message.
2. Mirror the source layout under `tests/`; prefix files `test_<thing>.py`, group
   scenarios in `class Test...`, name methods `test_<scenario>`. The tests for a
   module are then found from its path, and a failure's node id reads as the
   thing and the scenario that broke.
3. Mock external HTTP at the boundary (e.g. pytest-httpserver, requests-mock,
   moto), loading canned responses from a `data/` directory. The code under
   test runs unchanged down to the wire, and tests stay fast and deterministic
   without the network.
4. Build test objects via callable `<thing>_builder` fixtures (sensible defaults)
   plus a concrete `<thing>` fixture; register fixture modules via `pytest_plugins`,
   kept in a `fixtures/` directory. A test then states only the fields it is
   about, and every test file shares the same builders without importing them.
