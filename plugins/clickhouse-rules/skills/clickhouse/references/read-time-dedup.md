# ClickHouse read-time deduplication — recommendations

Recommendations for reading tables whose duplicates are resolved only when
parts merge (`ReplacingMergeTree`, `CollapsingMergeTree`, their versioned and
aggregating kin). Prefer these defaults; deviate when a situation genuinely
warrants it.

1. Never write `FINAL` in a query, and never set the `final` setting that
   applies it to every table of a query. `FINAL` re-runs the engine's merge at
   query time over every part the key range touches, in memory: it reads every
   `ORDER BY` column whether or not the query names it, merges across
   partitions unless told not to, parallelises worse than a plain scan, and
   cannot read a projection. The cost is paid on every read and grows with the
   number of un-merged parts, so the table written most is the one it hurts
   most — and it is silent, since the query looks like any other.
2. When a read must be exact across un-merged parts, deduplicate in SQL:
   - `GROUP BY <key>` with `argMax(<column>, <version>)` per column wanted;
     read the deletion flag or sign the same way and drop the losers in
     `HAVING`. Parallel and sort-free; verbose on wide rows. Make `<version>`
     a tuple when two rows can share one, or the winner of a tie is arbitrary.
   - `ORDER BY <version> DESC LIMIT 1 BY <key>` when the row is wanted as it
     was written. It sorts what it reads, so filter by the key first and never
     run it over a whole table.
3. Design so most reads need no deduplication at all. Write a fact once: an
   idempotent insert (`insert_deduplication_token` set from the thing being
   recorded) or a state transition in the source that makes a second write
   unreachable. Keep the version column cheap — `UInt64` or `DateTime64`, not
   `UUID` or `String` — because every deduplicating read sorts or compares it.
   Keep mutable state in a table of its own, or outside ClickHouse, rather
   than as versions of a fact row.
4. Where a read tolerates eventual deduplication, say so beside the query and
   read plainly: counts and sums are then off by the un-merged duplicates until
   the next merge — fine for a dashboard, not for a verdict.
5. `OPTIMIZE TABLE … FINAL` is no substitute. It rewrites whole parts and is
   for a closed partition in a quiet window, never a read path's warm-up.
