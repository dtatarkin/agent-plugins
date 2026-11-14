# ClickHouse read-time deduplication — recommendations

Recommendations for reading tables whose duplicates are resolved only when
parts merge (`ReplacingMergeTree`, `CollapsingMergeTree`,
`VersionedCollapsingMergeTree`). An aggregating or summing table is read by
aggregating again with `-Merge` combinators, and is not covered here. Prefer
these defaults; deviate when a situation genuinely warrants it.

1. Keep `FINAL` off read paths, and do not set the `final` setting that
   applies it to every table of a query. `FINAL` runs the engine's merge at
   query time, in memory, over every part range whose keys overlap another:
   it reads every sorting-key column and the version whether or not the query
   names them, merges across partitions unless the server can tell that no
   key spans two, and cannot read a projection. Newer versions read the
   non-overlapping ranges plainly, which narrows the cost but does not remove
   it: it is paid on every read and grows with the number of un-merged parts,
   so the table written most is the one it hurts most — and it is silent,
   since the query looks like any other.
2. When a read must be exact across un-merged parts, deduplicate in SQL:
   - Replacing: `GROUP BY <key>` with `argMax(<column>, <version>)` per
     column wanted; read the deletion flag the same way and drop deleted keys
     in `HAVING`. Parallel and sort-free; verbose on wide rows. On a version
     tie each `argMax` picks its own winner, so one result row can mix
     columns from different source rows: make `<version>` a tuple with a
     tie-breaker, or take the columns together as
     `argMax(tuple(<columns>), <version>)`.
   - Replacing: `ORDER BY <version> DESC LIMIT 1 BY <key>` when the row is
     wanted as it was written. It sorts what it reads, so filter by the key
     first and never run it over a whole table.
   - Collapsing, versioned or not: aggregate with the sign —
     `sum(<column> * sign)` for a sum, `sum(sign)` for a count, and
     `HAVING sum(sign) > 0` to drop collapsed keys. A plain collapsing table
     has no version, and a cancellation repeats its state's version, so
     `argMax` cannot pick the live row.
3. Design so most reads need no deduplication at all. Write a fact once: an
   idempotent insert or a state transition in the source that makes a second
   write unreachable. An `insert_deduplication_token` set from the thing being
   recorded catches only a retry inside the table's deduplication window, and
   a non-replicated table deduplicates nothing until
   `non_replicated_deduplication_window` is set. Keep the version an unsigned
   integer or a date-time — the engine's `ver` accepts nothing else, and a
   version used only in queries should follow it — because every
   deduplicating read sorts or compares it. Keep mutable state in a table of
   its own, or outside ClickHouse, rather than as versions of a fact row.
4. Where a read tolerates duplicates, say so beside the query and read
   plainly. Counts and sums then include every duplicate no merge has
   collapsed, and merges are opportunistic: rows in different partitions are
   never merged, and a part past the merge size limit is not merged again, so
   the error need not shrink to zero. Fine for a dashboard, not for a verdict.
5. `OPTIMIZE TABLE … FINAL` is no substitute. It rewrites whole parts and is
   for a closed partition in a quiet window, never a read path's warm-up.
