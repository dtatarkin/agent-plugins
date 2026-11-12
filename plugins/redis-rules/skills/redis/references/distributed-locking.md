# Distributed locking with Redis — recommendations

Recommendations for coordinating exclusive access across processes and hosts with
Redis. Prefer these defaults; deviate when a situation genuinely warrants it.

1. Acquire distributed locks through redis-py's `redis.lock.Lock` (e.g. your cache
   framework's `.lock(key, timeout=…)` helper) — never a hand-rolled
   `SET key val NX PX` plus `DEL`. The library embeds a per-holder UUID token in
   the lock value and releases via a check-and-delete Lua script, so it won't
   delete a lock that has since expired and been re-acquired by someone else.
   Don't reimplement that.
2. Give locks their own Redis connection — a dedicated cache instance /
   connection pool, ideally its own logical DB, separate from data and API caches
   **and from any broker/queue (e.g. a task queue) sharing the same Redis**. Lock
   acquire/release must stay low-latency and predictable; bulk cache or broker
   traffic on a shared pool starves lock operations and widens contention windows.
3. Express every lock TTL and blocking-timeout as a `timedelta`, not bare
   int/float seconds. Convert with `.total_seconds()` only at the redis-py call
   boundary that requires it, so durations stay self-describing and composable
   (e.g. `request_timeout + margin`) everywhere else.
4. Size a lock's TTL to outlast the work it guards. When a lock protects a
   long-running operation (e.g. an external API call), set
   `timeout = operation_timeout + margin` and comment why the TTL is that long. A
   lock that expires mid-operation provides no mutual exclusion — a second holder
   enters while the first is still working.
5. Never exit a code path still holding a lock. Use the lock as a context manager
   (`with lock:`) for inline critical sections, or acquire/release across
   `try`/`finally` with `release()` in the `finally`. An exception between acquire
   and release must not strand the lock — it would block every other holder until
   the TTL expires.
6. Name lock keys hierarchically as `"domain:resource:id"`, built from `StrEnum`
   prefixes — never string literals scattered across call sites. Use two levels: a
   **shared root enum** with one member per domain (`billing = "billing:"`), and a
   **per-module leaf enum** whose members extend a root member
   (`invoice = f"{Root.billing}invoice:"`). The root is the single registry of
   domains; each module owns its leaf. Keep the key builder (`_build_lock_key()`,
   returning the `str`) separate from the lock builder (`_build_lock()`, returning
   the `Lock`), so the key string can be reused for related cache operations
   without duplicating the naming scheme.
7. In background/worker tasks, acquire non-blocking (`blocking=False`) and fall
   back rather than stalling a worker. The standard fallback is
   `task.retry(countdown=<lock TTL>)` — coupling the retry delay to the lock's TTL
   so the task retries roughly when the current holder is expected to be done,
   instead of hammer-retrying. Factor acquire-or-fallback into one shared decorator
   — `acquire_lock_or_default(func, *, lock_builder, blocking, blocking_timeout,
   default)`, where `default` is a value or a callable and `lock_builder` is
   **zero-argument** — and bind per-task specifics with `functools.partial`. The
   zero-arg `lock_builder` means this fits **fixed-key** tasks (one lock per task).
   For a **per-entity** lock whose key comes from a runtime id, don't force it
   through the decorator — acquire inline via the context manager (rule 5), passing
   the id to the key builder.
8. After acquiring a blocking lock, re-check the condition that motivated the work.
   For create-if-missing or refresh-if-stale flows, a concurrent caller you waited
   behind may have already done it — so re-read state under the lock and return
   early if it's now satisfied. This collapses concurrent callers into a single
   external call instead of each redundantly hitting the upstream.
9. Don't rely on reentrant locking. redis-py's `Lock` is not reentrant:
   re-acquiring the same key from a holder that already owns it blocks until the
   TTL expires (a self-deadlock). Don't nest acquisition of the same lock —
   refactor so the critical section acquires once, or split the key.
