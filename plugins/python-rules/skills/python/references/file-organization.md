# File organization — recommendations

Recommendations for organizing modules and packages. Prefer these defaults;
deviate when a situation genuinely warrants it.

1. Prefer one class/function per file named after the entity, re-exporting public
   symbols from the package `__init__.py`. An entity is then found from its
   name alone, a diff touches only the file of what changed, and callers import
   from the package without depending on its internal layout.
2. Keep a per-package `types.py` (enums, state) and `consts.py` (module constants);
   put cross-cutting types and consts at the top level. Shared definitions then
   have one predictable home, and modules that need them import it without
   importing each other in a cycle.
