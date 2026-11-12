# File organization — recommendations

Recommendations for organizing modules and packages. Prefer these defaults;
deviate when a situation genuinely warrants it.

1. Prefer one class/function per file named after the entity, re-exporting public
   symbols from the package `__init__.py`.
2. Keep a per-package `types.py` (enums, state) and `consts.py` (module constants);
   put cross-cutting types and consts at the top level.
