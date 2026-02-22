# 24. Redis Memory, Eviction & Hot Keys — Senior

## Q1. (Beginner) What happens when Redis runs out of memory (maxmemory)? What is the default behavior?

**Answer:**  
When **maxmemory** is reached, Redis can **evict** keys (depending on **maxmemory-policy**) or **refuse writes** (noeviction). Default is **noeviction** — returns errors on write when memory is full. In production you usually set an eviction policy (e.g. allkeys-lru, volatile-lru) so Redis evicts keys instead of failing writes.

---

## Q2. (Beginner) Name and briefly explain three eviction policies.

**Answer:**  
**volatile-lru**: evict among keys that have an **expiration** set, by LRU. **allkeys-lru**: evict among **all** keys by LRU (most common for cache). **volatile-ttl**: evict among keys with TTL, by shortest TTL. **noeviction**: no eviction, return errors on write. Use **allkeys-lru** when the whole dataset is a cache; use **volatile-lru** when only some keys are cache and others must not be evicted.

---

## Q3. (Intermediate) How do you monitor memory usage in Redis? What does INFO memory show?

**Answer:**  
**INFO memory** shows: used_memory (bytes), used_memory_rss, maxmemory, mem_fragmentation_ratio, evicted_keys, etc. Use **redis-cli INFO memory** or from app with INFO command. Monitor: used_memory vs maxmemory; evicted_keys (eviction rate); fragmentation. Set alerts when used_memory approaches maxmemory or evictions spike.

---

## Q4. (Intermediate) What is a “hot key” problem? Why is it a problem in Redis Cluster?

**Answer:**  
**Hot key**: one key (or few keys) gets a **disproportionate** share of traffic. In a single node it can saturate CPU/network; in **Redis Cluster** that key lives on one node, so that node gets all the traffic and can become a bottleneck. The key cannot be spread across nodes (one key = one slot = one node).

---

## Q5. (Intermediate) How can you mitigate hot keys in the backend (without changing Redis topology)?

**Answer:**  
(1) **Local cache** in the app: cache the hot key value in process (e.g. in-memory with TTL); reduce Redis reads. (2) **Replicate reads**: if using replica(s), spread read traffic across replicas (hot key is still on one primary/replica set per shard). (3) **Key splitting**: if the hot “key” is logical (e.g. “global config”), split into N keys (config:1, config:2, …) and read from a random one — write to all; read from one (consistency trade-off). (4) **Reduce access**: batch or shorten TTL so fewer hits.

---

## Q6. (Advanced) Production scenario: Redis memory keeps growing and you see evictions. How do you diagnose which keys use the most memory and whether eviction policy is appropriate?

**Answer:**  
(1) **INFO memory** and **INFO stats** (evicted_keys, keyspace_hits/misses). (2) **MEMORY USAGE key** (per key) or **redis-cli --bigkeys** to sample large keys. (3) **MEMORY STATS** (Redis 4+) for breakdown. (4) Check **maxmemory-policy**: if cache, use allkeys-lru; if mixed, use volatile-lru and set TTL on cache keys. (5) Find large or numerous keys (bigkeys, scan + memory usage); fix app (limit key size, set TTL, cap cardinality). (6) Increase maxmemory or scale (Cluster) if data set is legitimately large.

---

## Q7. (Advanced) What is memory fragmentation in Redis? How do you reduce it?

**Answer:**  
**Fragmentation**: used_memory_rss &gt; used_memory (RSS is what OS gives; internal allocator may fragment). **mem_fragmentation_ratio** = RSS / used_memory; &gt; 1.5 may indicate fragmentation. **Reduce**: (1) **Restart** (loses data unless persisted). (2) **Active defragmentation** (Redis 4+, activedefrag yes) — reclaims memory in background. (3) Use **jemalloc** and tune. (4) Avoid very large values or many small allocations that get freed.

---

## Q8. (Advanced) How would you implement a “cache warming” strategy after a restart so the backend doesn’t thump the DB? Where would you run it?

**Answer:**  
**Strategy**: preload critical keys after Redis is up. (1) **List of critical keys** (e.g. config, top products) or a key that holds key patterns. (2) **Job** (cron or on startup): for each key (or pattern), fetch from DB and SET in Redis. (3) Run in **backend** (one designated instance) or a **separate worker**; use a lock so only one warmer runs. (4) Optionally **stale-while-revalidate**: serve stale from DB or a backup cache while warming. Don’t warm everything; prioritize hot keys.

---

## Q9. (Advanced) What is the SLOWLOG? How do you use it to find problematic commands?

**Answer:**  
**SLOWLOG** records commands that exceed a threshold (config: slowlog-log-slower-than in microseconds). **SLOWLOG GET 10** returns the last 10 slow commands with timestamp, duration, command, client. Use to find: (1) Slow commands (e.g. KEYS *, large HGETALL). (2) Hot keys (same key repeated). (3) Bad patterns (full scan). Fix: add indexes (for structures that support it), avoid KEYS (use SCAN), split or cache hot keys.

---

## Q10. (Advanced) In a Redis Cluster, how would you “spread” a logical hot key (e.g. global counter) across multiple keys so load is distributed? Show the read/write pattern and trade-off.

**Answer:**  
**Shard the key**: e.g. instead of `global:counter`, use `global:counter:0` … `global:counter:N-1`. **Write**: update all N keys (INCR each, or use a Lua that updates one chosen by hash). **Read**: sum all N keys (MGET or pipeline GET then sum). **Trade-off**: N times read/write for one logical value; but load spreads across N nodes. Use **hash tag** so all N keys are in the same slot if you need atomicity across them (then same node — no spread). So for **spread** you give up same-slot; use N keys without same tag, or accept multi-key read/write and possible inconsistency (e.g. eventual sum).
