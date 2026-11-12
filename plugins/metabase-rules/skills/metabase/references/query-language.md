# Metabase query language — recommendations

Recommendations for authoring queries in Metabase questions and models.
Prefer these defaults; deviate when a situation genuinely warrants it.

1. Always start in the query builder (MBQL). Escalate to a native SQL query
   only when MBQL cannot express the question, or the MBQL formulation
   becomes substantially harder to follow than the SQL would be. MBQL
   questions stay editable in the GUI, keep drill-through, survive field
   renames via field metadata, and remain modifiable without SQL knowledge —
   a native query loses all four.
2. Before escalating, try custom expressions and composing on saved
   questions or models; much of what looks SQL-only is reachable that way.
3. When SQL is unavoidable, push it down into a model and build MBQL
   questions on top of that model, so the native-SQL surface stays as small
   as possible and downstream consumers keep the query-builder benefits.
4. When editing an existing MBQL question, keep it MBQL — do not convert it
   to native SQL for convenience. Conversion is one-way: once saved as
   native, the structured query and its benefits are gone.
