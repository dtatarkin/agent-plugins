---
name: clickhouse
description: ClickHouse conventions — reading merge-time-deduplicated tables without FINAL (argMax / LIMIT 1 BY in SQL), write-once facts and cheap version columns; joins with a small filtered right side, dictionaries for lookups, denormalization at write time. Load when writing a ClickHouse query, the DDL of a MergeTree-family table, or a read model over one.
---

# ClickHouse rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change, then follow them.

| You are editing… | Read |
|------------------|------|
| A query or read model over a `ReplacingMergeTree` / `CollapsingMergeTree` table, or the DDL of one | `references/read-time-dedup.md` |
| A query with a `JOIN`, or the choice between a join, a dictionary and a denormalized column | `references/joins.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
