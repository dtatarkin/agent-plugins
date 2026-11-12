# Testing — recommendations

General pytest conventions. Prefer these defaults; deviate when a situation
genuinely warrants it.

1. Prefer pytest with plain `assert`.
2. Mirror the source layout under `tests/`; prefix files `test_<thing>.py`, group
   scenarios in `class Test...`, name methods `test_<scenario>`.
3. Mock external HTTP at the boundary (e.g. pytest-httpserver, requests-mock,
   moto), loading canned responses from a `data/` directory.
4. Build test objects via callable `<thing>_builder` fixtures (sensible defaults)
   plus a concrete `<thing>` fixture; register fixture modules via `pytest_plugins`,
   kept in a `fixtures/` directory.
