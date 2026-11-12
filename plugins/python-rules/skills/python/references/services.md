# Services / use-cases — recommendations

Recommendations for structuring application/service logic. Prefer these defaults;
deviate when a situation genuinely warrants it.

1. Prefer one service per file under `services/`: a verb-named function for a
   single use-case, or a `<Noun>Service` class when wrapping a stateful external
   client. Keep private helpers `_`-prefixed in the same file, and import services
   from their module rather than re-exporting from `__init__.py`.
2. Raise a single typed domain error (carrying `code` + `message` + `details`) for
   domain failures, wrapping third-party exceptions through a converter helper.
   Keep services synchronous and hand long-running work to a task queue.
