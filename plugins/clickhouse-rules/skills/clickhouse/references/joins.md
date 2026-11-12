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
   repeats the join. Copy what reads filter or group by; leave the rest
   behind the key. Never copy mutable state into a fact row: a copied
   attribute is frozen at insert and stale the moment its source changes.
4. Cap a read-path query at three or four joins. Each join is another hash
   table, another pass over the left side and another order the planner can
   get wrong. A query that needs more is reading a model that does not exist
   yet — build the mart (3) and read that.
5. Give a large-against-large join a spill threshold, not a memory cap.
   Without one a hash join never spills: it grows until the query's memory
   limit kills it. `max_bytes_before_external_join` (or the
   `_ratio_` variant) makes the right side spill to disk instead; every hash
   algorithm honours it, and `grace_hash` partitions from the first block.
   `max_rows_in_join` / `max_bytes_in_join` are hard caps that fail the
   query, not spill it. Set the threshold on the query or its settings
   profile, not server-wide: a non-zero threshold also makes the planner
   sort an `ORDER BY … LIMIT` on the preserved side instead of reading it in
   key order, which slows the joins that would have fit anyway.
