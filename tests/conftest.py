"""Rootdir conftest: registers the shared fixture modules under `fixtures/`.

`pytest_plugins` is honoured here only, so every fixture module is listed
once; the suites below pick fixtures up by name.
"""

pytest_plugins = [
    "tests.fixtures.justlint.trees",
    "tests.fixtures.lintlint.trees",
]
