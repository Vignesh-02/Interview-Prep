# 6. Caching Strategies

## Topic Introduction

Caching stores **frequently accessed data** closer to the consumer to reduce latency and database load. A well-designed cache can reduce DB queries by 90%+ and cut response times from 100ms to <5ms.

```
Request → Cache Hit? ─── Yes ──► Return cached data (1-5ms)
                    └── No ──► Query DB (50-200ms) → Store in cache → Return
```

There are multiple strategies: **read-through**, **write-through**, **write-behind**, **cache-aside** — each with different consistency and performance tradeoffs. Getting caching wrong causes **stale data**, **cache stampedes**, and **thundering herds**.

**Go/Java tradeoff**: Go uses `groupcache` or direct Redis. Java has Spring's `@Cacheable` annotation + Caffeine (in-process) + Redis. Node.js typically uses Redis directly or `node-cache` for in-process caching. The patterns are identical across languages — the tooling differs.

---

## Q1. (Beginner) What is caching and why does it matter for backend performance?

**Scenario**: Your API endpoint hits PostgreSQL for every request. Average response time is 150ms. 80% of requests query the same 100 popular products.

```js
// Without cache: every request hits DB
app.get('/products/:id', async (req, res) => {
  const product = await db.query('SELECT * FROM products WHERE id = $1', [req.params.id]);
  res.json(product.rows[0]); // 150ms avg
});

// With cache: 80% of requests return in <5ms
app.get('/products/:id', async (req, res) => {
  const key = `product:${req.params.id}`;
  const cached = await redis.get(key);
  if (cached) return res.json(JSON.parse(cached)); // 2ms

  const product = await db.query('SELECT * FROM products WHERE id = $1', [req.params.id]);
  await redis.set(key, JSON.stringify(product.rows[0]), 'EX', 300); // cache 5 min
  res.json(product.rows[0]);
});
```

**Answer**: Caching trades **freshness** for **speed**. It reduces database load, lowers latency, and increases throughput. The tradeoff is potentially serving **stale data** during the cache TTL window.

---

## Q2. (Beginner) What is the difference between in-process cache and distributed cache?

**Answer**:

| | **In-Process** (Map, node-cache) | **Distributed** (Redis, Memcached) |
|---|---|---|
| Latency | <0.1ms (memory access) | 1-5ms (network hop) |
| Shared across processes | No (each worker has own copy) | Yes |
| Memory | Uses app heap (limited) | Separate server (scalable) |
| Consistency | Inconsistent across workers | Single source of truth |
| Survives restart | No | Yes (Redis with persistence) |

```js
// In-process cache (good for small, static data)
const NodeCache = require('node-cache');
const localCache = new NodeCache({ stdTTL: 60 });

function getConfig(key) {
  const cached = localCache.get(key);
  if (cached) return cached;
  const value = db.getConfig(key);
  localCache.set(key, value);
  return value;
}

// Distributed cache (good for shared, dynamic data)
async function getUser(userId) {
  const cached = await redis.get(`user:${userId}`);
  if (cached) return JSON.parse(cached);
  const user = await db.getUser(userId);
  await redis.set(`user:${userId}`, JSON.stringify(user), 'EX', 300);
  return user;
}
```

**Production pattern**: Use **both** — in-process for hot config/static data, Redis for shared dynamic data.

---

## Q3. (Beginner) What is TTL (Time To Live)? How do you choose the right TTL?

**Answer**: TTL defines how long a cached value stays valid before auto-expiring.

| Data Type | Suggested TTL | Reasoning |
|-----------|--------------|-----------|
| Static config | 1 hour+ | Rarely changes |
| Product catalog | 5-15 min | Changes occasionally |
| User profile | 1-5 min | May update frequently |
| Real-time prices | 5-30 sec | Must be fresh |
| Auth tokens | Until expiry | Security-sensitive |

```js
// Set TTL based on data volatility
await redis.set('products:popular', data, 'EX', 300);  // 5 min
await redis.set('user:123:profile', data, 'EX', 60);   // 1 min
await redis.set('config:features', data, 'EX', 3600);  // 1 hour
```

**Rule**: TTL = how long you can tolerate stale data. Shorter TTL = fresher data but more DB load. Longer TTL = less DB load but more staleness.

---

## Q4. (Beginner) What is cache-aside (lazy loading)? Show the pattern.

**Answer**: The application manages the cache directly — reads from cache first, fills on miss.

```js
// Cache-aside pattern
async function getProduct(id) {
  const key = `product:${id}`;

  // 1. Try cache
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  // 2. Cache miss → query DB
  const product = await db.query('SELECT * FROM products WHERE id = $1', [id]);
  if (!product.rows[0]) return null;

  // 3. Populate cache
  await redis.set(key, JSON.stringify(product.rows[0]), 'EX', 300);
  return product.rows[0];
}
```

**Pros**: Simple, only caches data that's actually requested. **Cons**: First request is always slow (cache miss), stale data possible during TTL.

---

## Q5. (Beginner) What is the difference between read-through, write-through, and write-behind?

**Answer**:

| Strategy | How it works | Consistency | Performance |
|----------|-------------|-------------|-------------|
| **Cache-aside** | App manages cache manually | Stale during TTL | Fast reads, cold misses |
| **Read-through** | Cache fetches from DB on miss | Stale during TTL | Same as cache-aside but cleaner |
| **Write-through** | Write to cache AND DB synchronously | Strong (both updated) | Slower writes |
| **Write-behind** | Write to cache, async write to DB | Eventual | Fastest writes, risk of data loss |

```js
// Write-through: update both on every write
async function updateProduct(id, data) {
  await db.query('UPDATE products SET ... WHERE id = $1', [id, ...]);
  await redis.set(`product:${id}`, JSON.stringify(data), 'EX', 300);
}

// Write-behind: write cache immediately, DB asynchronously
async function updateProduct(id, data) {
  await redis.set(`product:${id}`, JSON.stringify(data), 'EX', 300);
  await writeQueue.add('db-sync', { id, data }); // async DB write
}
```

---

## Q6. (Intermediate) What is a cache stampede? How do you prevent it?

**Scenario**: A popular product cache expires. 1,000 concurrent requests all miss cache and hit the DB simultaneously.

```js
// BAD: cache stampede — 1000 requests all query DB
async function getProduct(id) {
  const cached = await redis.get(`product:${id}`);
  if (cached) return JSON.parse(cached);
  // 1000 requests arrive here simultaneously after TTL expires
  const product = await db.query('SELECT * FROM products WHERE id = $1', [id]);
  await redis.set(`product:${id}`, JSON.stringify(product.rows[0]), 'EX', 300);
  return product.rows[0];
}

// GOOD: request coalescing — only ONE request queries DB
const inflight = new Map();
async function getProductSafe(id) {
  const key = `product:${id}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  // If another request is already fetching, wait for it
  if (inflight.has(key)) return inflight.get(key);

  const promise = (async () => {
    const product = await db.query('SELECT * FROM products WHERE id = $1', [id]);
    await redis.set(key, JSON.stringify(product.rows[0]), 'EX', 300);
    inflight.delete(key);
    return product.rows[0];
  })();

  inflight.set(key, promise);
  return promise;
}
```

**Other solutions**: (1) **Distributed lock** — only one process fetches, (2) **Stale-while-revalidate** — serve stale data while refreshing in background, (3) **Jittered TTL** — add random seconds to TTL so keys don't expire simultaneously.

---

## Q7. (Intermediate) How do you invalidate cache when data changes? Compare strategies.

```js
// Strategy 1: Invalidate on write (delete cache)
async function updateProduct(id, data) {
  await db.query('UPDATE products SET ... WHERE id = $1', [id]);
  await redis.del(`product:${id}`); // next read will re-populate
}

// Strategy 2: Update cache on write (write-through)
async function updateProduct(id, data) {
  await db.query('UPDATE products SET ... WHERE id = $1', [id]);
  await redis.set(`product:${id}`, JSON.stringify(data), 'EX', 300);
}

// Strategy 3: Event-driven invalidation
// DB change → CDC (Change Data Capture) → event → cache invalidation
// Products table → Debezium → Kafka → Consumer → redis.del()
```

**Answer**:
| Strategy | Pros | Cons |
|----------|------|------|
| **Delete on write** | Simple, no stale data | Next read has cache miss |
| **Update on write** | No miss after write | Complexity, possible inconsistency |
| **Event-driven (CDC)** | Decoupled, works across services | Eventual consistency, infrastructure |
| **TTL only** | Simplest | Stale data for up to TTL duration |

**Senior recommendation**: Delete on write + short TTL for most cases. CDC for microservices with shared data.

---

## Q8. (Intermediate) How do you implement a multi-layer cache (L1 in-process + L2 Redis)?

**Scenario**: Ultra-low latency needed. Even Redis's 1-2ms is too slow for some hot paths.

```js
const NodeCache = require('node-cache');
const l1 = new NodeCache({ stdTTL: 10, maxKeys: 1000 }); // 10s, 1000 items

async function getWithMultiLayer(key, fetchFn) {
  // L1: in-process (sub-ms)
  const l1Value = l1.get(key);
  if (l1Value) return l1Value;

  // L2: Redis (1-2ms)
  const l2Value = await redis.get(key);
  if (l2Value) {
    const parsed = JSON.parse(l2Value);
    l1.set(key, parsed);
    return parsed;
  }

  // L3: Database (50-200ms)
  const dbValue = await fetchFn();
  if (dbValue) {
    await redis.set(key, JSON.stringify(dbValue), 'EX', 300);
    l1.set(key, dbValue);
  }
  return dbValue;
}
```

**Answer**: L1 (in-process) handles the hottest data with sub-ms latency. L2 (Redis) shares state across processes with 1-2ms latency. L3 (DB) is the source of truth. L1 has a **shorter TTL** than L2 to reduce staleness. This pattern is common for **feature flags**, **config**, and **hot product pages**.

**Caveat**: L1 is per-process — in cluster mode, each worker has its own L1. Invalidation must propagate to all processes (via Redis pub/sub or short TTL).

---

## Q9. (Intermediate) How do you cache database query results with parameterized keys?

```js
// Consistent cache key generation
function cacheKey(prefix, params) {
  const sorted = Object.keys(params).sort().map(k => `${k}=${params[k]}`).join('&');
  return `${prefix}:${sorted}`;
}

// Usage
async function searchProducts({ category, page, sort }) {
  const key = cacheKey('search', { category, page, sort });
  // key = "search:category=electronics&page=1&sort=price"

  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const result = await db.query(
    'SELECT * FROM products WHERE category = $1 ORDER BY $2 LIMIT 20 OFFSET $3',
    [category, sort, (page - 1) * 20]
  );
  await redis.set(key, JSON.stringify(result.rows), 'EX', 120); // 2 min
  return result.rows;
}
```

**Answer**: Generate deterministic cache keys by sorting parameters. This ensures the same query always maps to the same key regardless of parameter order. Prefix by operation type to avoid collisions.

---

## Q10. (Intermediate) What is cache warming? When and how do you do it?

**Scenario**: After a deploy, cache is empty. The first 10,000 users all hit the DB (cold start).

```js
// Cache warming on startup
async function warmCache() {
  console.log('Warming cache...');

  // Pre-load popular products
  const popular = await db.query(
    'SELECT * FROM products ORDER BY view_count DESC LIMIT 100'
  );
  const pipeline = redis.pipeline();
  popular.rows.forEach(p => {
    pipeline.set(`product:${p.id}`, JSON.stringify(p), 'EX', 600);
  });
  await pipeline.exec();

  // Pre-load feature flags
  const flags = await db.query('SELECT * FROM feature_flags');
  await redis.set('feature_flags', JSON.stringify(flags.rows), 'EX', 3600);

  console.log('Cache warmed');
}

// Call before starting server
await warmCache();
server.listen(3000);
```

**Answer**: Cache warming pre-populates the cache with expected hot data before traffic arrives. Use it after deploys, cache flushes, or Redis restarts. Only warm data you **know** will be requested (top products, config, feature flags).

---

## Q11. (Intermediate) How do you cache negative results (cache misses for non-existent data)?

**Scenario**: Bots repeatedly request `/users/fake-id-999`. Each request hits the DB and returns 404.

```js
async function getUser(id) {
  const key = `user:${id}`;
  const cached = await redis.get(key);

  if (cached === 'NULL') return null;  // cached negative result
  if (cached) return JSON.parse(cached);

  const user = await db.query('SELECT * FROM users WHERE id = $1', [id]);
  if (!user.rows[0]) {
    await redis.set(key, 'NULL', 'EX', 60); // cache miss for 1 min (short TTL)
    return null;
  }

  await redis.set(key, JSON.stringify(user.rows[0]), 'EX', 300);
  return user.rows[0];
}
```

**Answer**: Cache a sentinel value (`NULL`, `EMPTY`) for known misses with a **shorter TTL**. This prevents repeated DB queries for non-existent data. Short TTL ensures that if the data is created, it becomes available quickly.

---

## Q12. (Intermediate) How do you handle cache consistency in a microservices architecture?

**Answer**: When Service A caches data that Service B can modify, consistency is hard.

```js
// Option 1: Event-driven invalidation
// Service B publishes event → Service A invalidates cache
subscriber.on('message', (channel, message) => {
  const { type, productId } = JSON.parse(message);
  if (type === 'product.updated') {
    redis.del(`product:${productId}`);
  }
});

// Option 2: Short TTL + eventual consistency
// Accept 30-60 seconds of staleness; no cross-service invalidation needed

// Option 3: Shared cache (Redis)
// Both services read/write the same Redis keys with agreed naming convention
// Service B updates cache directly after DB write
```

**Recommendation**: Start with short TTLs (simplest). Add event-driven invalidation for data that must be more consistent. Avoid synchronous cross-service cache invalidation (creates coupling).

---

## Q13. (Advanced) Production scenario: Your Redis cache uses 8GB RAM and is growing. How do you control it?

**Answer**:

```bash
# Redis configuration
maxmemory 8gb
maxmemory-policy allkeys-lru  # evict least recently used keys
```

**Strategies**:
1. **Set TTL on every key** — never set keys without expiry
2. **Use Redis memory analysis**: `redis-cli --bigkeys` to find large keys
3. **Compress values**: `zlib` or `snappy` before storing
```js
const zlib = require('zlib');
const compressed = zlib.deflateSync(JSON.stringify(largeObject));
await redis.set(key, compressed, 'EX', 300);
// Read: zlib.inflateSync(await redis.getBuffer(key))
```
4. **Use hashes for objects** (Redis optimizes small hashes):
```js
await redis.hmset(`user:${id}`, { name: 'Alice', email: 'a@b.com', role: 'admin' });
// More memory-efficient than JSON string for small objects
```
5. **Monitor**: Track `used_memory`, `evicted_keys`, `keyspace_hits/misses` in Prometheus

---

## Q14. (Advanced) How do you implement stale-while-revalidate caching?

**Scenario**: You want instant responses (even if stale) while refreshing the cache in the background.

```js
async function getWithSWR(key, fetchFn, { ttl = 300, staleTtl = 600 } = {}) {
  const cached = await redis.get(key);

  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    const age = (Date.now() - timestamp) / 1000;

    if (age < ttl) return data; // fresh — return immediately

    if (age < staleTtl) {
      // Stale but within grace period — return stale, refresh in background
      refreshInBackground(key, fetchFn, ttl, staleTtl).catch(console.error);
      return data;
    }
  }

  // Cache miss or beyond stale TTL — must fetch synchronously
  return refreshAndReturn(key, fetchFn, ttl, staleTtl);
}

async function refreshInBackground(key, fetchFn, ttl, staleTtl) {
  const lockKey = `refresh-lock:${key}`;
  const locked = await redis.set(lockKey, '1', 'NX', 'EX', 10);
  if (!locked) return; // another process is already refreshing

  const data = await fetchFn();
  await redis.set(key, JSON.stringify({ data, timestamp: Date.now() }), 'EX', staleTtl);
  await redis.del(lockKey);
}
```

**Answer**: Serve stale data immediately while refreshing in the background. Users get instant responses (even if slightly stale). Only one process refreshes (lock prevents stampede). This is the same concept as HTTP's `stale-while-revalidate` header.

---

## Q15. (Advanced) How do you design caching for a high-traffic e-commerce product page (1M views/day)?

**Answer**:

```
Browser Cache (Cache-Control: max-age=30)
    → CDN (edge cache, 60s TTL)
        → Application L1 (in-process, 10s)
            → Redis L2 (300s)
                → PostgreSQL (source of truth)
```

```js
app.get('/products/:id', async (req, res) => {
  // HTTP cache headers
  res.setHeader('Cache-Control', 'public, max-age=30, stale-while-revalidate=60');
  res.setHeader('Vary', 'Accept-Encoding');

  const product = await getWithMultiLayer(`product:${req.params.id}`, () =>
    db.query('SELECT * FROM products WHERE id = $1', [req.params.id]).then(r => r.rows[0])
  );

  if (!product) return res.status(404).json({ error: 'Not found' });
  res.json(product);
});
```

**Cache invalidation on update**:
```js
async function updateProduct(id, data) {
  await db.query('UPDATE products SET ... WHERE id = $1', [id]);
  await redis.del(`product:${id}`);         // invalidate Redis
  await cdn.purge(`/products/${id}`);        // invalidate CDN
  // L1 (in-process) expires naturally via short TTL
}
```

**At 1M views/day**: CDN handles ~80%, Redis handles ~15%, DB handles ~5% of actual requests.

---

## Q16. (Advanced) How do you implement cache-based rate limiting (sliding window)?

```js
async function slidingWindowRateLimit(userId, limit = 100, windowSec = 60) {
  const key = `ratelimit:${userId}`;
  const now = Date.now();
  const windowStart = now - (windowSec * 1000);

  const multi = redis.multi();
  multi.zremrangebyscore(key, 0, windowStart);  // remove old entries
  multi.zadd(key, now, `${now}-${Math.random()}`);  // add current request
  multi.zcard(key);  // count entries in window
  multi.expire(key, windowSec);  // cleanup

  const results = await multi.exec();
  const count = results[2][1]; // zcard result

  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    resetAt: new Date(now + windowSec * 1000),
  };
}
```

**Answer**: Redis sorted sets make excellent sliding window counters. Each request is a member with its timestamp as score. Old entries are pruned. The count gives the current window total. This is more accurate than fixed-window counters.

---

## Q17. (Advanced) What are the tradeoffs of caching in Go vs Node.js vs Java?

**Answer**:

| Aspect | **Node.js** | **Go** | **Java** |
|--------|-------------|--------|----------|
| In-process cache | `node-cache`, `lru-cache` (per worker) | `groupcache`, `sync.Map`, `bigcache` (shared across goroutines) | Caffeine, Guava Cache (shared across threads) |
| Distributed cache | Redis via `ioredis` (async) | Redis via `go-redis` (goroutine per call) | Redis via Lettuce/Jedis, or Hazelcast |
| Serialization | `JSON.stringify/parse` (slow for large objects) | `encoding/json` or `protobuf` (faster) | Jackson or protobuf (very fast) |
| Cache coherence | Hard in cluster mode (separate heaps) | Easy (single process, goroutines share memory) | Easy (single process, threads share heap) |

**Node.js disadvantage**: In cluster mode, each worker has its own in-process cache → N workers = N copies of the same data. Go and Java have one process with shared memory.

**Node.js advantage**: Async Redis calls don't block the event loop. In Go, each Redis call blocks a goroutine (cheap but still a context switch).

---

## Q18. (Advanced) How do you handle cache during database migrations or schema changes?

**Scenario**: You add a `discount_price` field to products. Old cached data doesn't have this field.

**Answer**:

```js
// Option 1: Cache key versioning
const CACHE_VERSION = 'v2';
const key = `product:${CACHE_VERSION}:${id}`;
// Old v1 keys expire naturally; new v2 keys have the new schema

// Option 2: Lazy migration
async function getProduct(id) {
  const cached = await redis.get(`product:${id}`);
  if (cached) {
    const product = JSON.parse(cached);
    if (product._cacheVersion !== 2) {
      // Old format — invalidate and re-fetch
      await redis.del(`product:${id}`);
    } else {
      return product;
    }
  }
  // Fetch fresh data with new schema
  const product = await db.query('SELECT *, discount_price FROM products WHERE id = $1', [id]);
  const data = { ...product.rows[0], _cacheVersion: 2 };
  await redis.set(`product:${id}`, JSON.stringify(data), 'EX', 300);
  return data;
}

// Option 3: Flush and warm (simplest, but cold cache)
// await redis.flushdb(); await warmCache();
```

---

## Q19. (Advanced) Production scenario: After a Redis failover, your app floods the database. How do you prevent this?

**Answer**: After Redis fails/restarts, ALL cache keys are gone → every request hits DB → DB overload → cascading failure.

```js
// Circuit breaker for database
const circuitBreaker = {
  state: 'closed', // closed, open, half-open
  failures: 0,
  threshold: 10,
  resetTimeout: 30000,
};

async function getProductSafe(id) {
  try {
    const cached = await redis.get(`product:${id}`);
    if (cached) return JSON.parse(cached);
  } catch {
    // Redis is down — continue to DB but with protection
  }

  // Circuit breaker: if DB is overwhelmed, return degraded response
  if (circuitBreaker.state === 'open') {
    return { id, name: 'Temporarily unavailable', _degraded: true };
  }

  try {
    const product = await db.query('SELECT * FROM products WHERE id = $1', [id]);
    circuitBreaker.failures = 0;
    // Try to repopulate Redis
    redis.set(`product:${id}`, JSON.stringify(product.rows[0]), 'EX', 300).catch(() => {});
    return product.rows[0];
  } catch (dbErr) {
    circuitBreaker.failures++;
    if (circuitBreaker.failures >= circuitBreaker.threshold) {
      circuitBreaker.state = 'open';
      setTimeout(() => { circuitBreaker.state = 'half-open'; }, circuitBreaker.resetTimeout);
    }
    throw dbErr;
  }
}
```

**Prevention**: (1) Circuit breaker on DB, (2) Request coalescing (only one DB fetch per key), (3) Cache warming script runs after Redis recovery, (4) Redis Cluster/Sentinel for HA.

---

## Q20. (Advanced) Senior red flags in caching code reviews.

**Answer**:

1. **No TTL on cache keys** — memory grows forever until OOM
2. **Caching user-specific data with shared key** — data leaks between users
3. **Cache key without version** — schema changes break deserialization
4. **No eviction policy configured** — Redis fills up and rejects writes
5. **Caching inside a transaction** — cache updated but transaction rolls back
6. **No cache stampede protection** — popular key expires, DB gets hammered
7. **Storing large blobs** (>1MB) in Redis — blocks Redis single thread
8. **Never monitoring hit/miss ratio** — flying blind on cache effectiveness
9. **`JSON.stringify` on circular objects** — crashes without error handling

**Senior interview answer**: "Effective caching requires TTLs on every key, stampede protection, multi-layer strategy, proper invalidation, and continuous monitoring of hit rates. I treat Redis as a performance layer, never the source of truth."
