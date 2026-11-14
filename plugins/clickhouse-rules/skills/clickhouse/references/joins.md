# ClickHouse joins — recommendations

Recommendations for a query that joins tables, and for the table design that
decides whether it has to. Prefer these defaults; deviate when a situation
genuinely warrants it.

1. Keep the right side small, and filter it before the join. A hash join
   builds the entire right side into an in-memory hash table before a single
   left row is probed. The planner moves the smaller table to the right on
   its own (24.12 for two tables, 25.9 beyond) and pushes many filters below
   the join, but neither is guaranteed, so the lever is still yours: wrap the
   right side in a subquery that selects only the rows and columns the join
   needs.
2. Look a small dimension up through a dictionary, not a join and not a
   copied column. `dictGet` runs only on rows that survived the query's
   filters, where a join builds its hash table first and discards later. The
   exception is a value the query filters on across many rows
   (`WHERE dictGet(…) > x`): a dictionary lookup is evaluated row by row with
   no index, so that value belongs in a real column, where the primary key
   and `PREWHERE` can skip granules.
3. Denormalize at write time, and only the read-hot attributes. Join once
   where the row is produced — a materialized view, a transformation model
   (dbt), the insert path — so every read scans one wide table and none
   repeats the join. Copy what reads filter on, which a dictionary cannot
   serve from an index (2); look the rest up, or leave it behind the key.
   Never copy mutable state into a fact row: a copied
   attribute is frozen at insert and stale the moment its source changes.
4. Cap a read-path query at three or four joins. Each join is another hash
   table, another pass over the left side and another order the planner can
   get wrong. A query that needs more is reading a model that does not exist
   yet — build the mart (3) and read that.
5. Let a large-against-large join spill; never lean on a memory cap. A hash
   join spills its right side to disk, as a grace hash join, once it passes
   `max_bytes_before_external_join` or the
   `max_bytes_ratio_before_external_join` share of available memory; with
   both at 0 it never spills, and grows until the query's memory limit kills
   it. Recent servers default the ratio to 0.5 and older ones leave spilling
   off, so read the effective values from `system.settings` rather than
   assume either. Spilling also needs a temporary data path.
   `max_rows_in_join` / `max_bytes_in_join` stop the query from 26.10 on,
   where earlier versions spilled on reaching them, so a cap bounds a join
   but does not rescue it. A non-zero threshold disables reading in order
   through the join, so an `ORDER BY … LIMIT` on the left side sorts instead
   of reading in key order: where such a query's right side is known to fit,
   set both thresholds to 0 on that query alone.
