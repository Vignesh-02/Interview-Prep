# 9. Redis Caching Patterns & Backend Integration

## Q1. (Beginner) What is cache-aside (lazy loading)? Describe the read and write flow.

**Answer:**  
**Cache-aside**: app owns the cache. **Read**: check cache; if miss, read from DB, then write to cache and return. **Write**: write to DB, then invalidate (delete) or update the cache entry. No automatic load from DB by Redis; the application does the load and populate. Most common pattern in backends.

---

## Q2. (Beginner) Why do we invalidate (or update) cache on write? What happens if we don’t?

**Answer:**  
So the cache doesn’t serve **stale** data after the DB has changed. If we don’t invalidate/update: reads may return old data until TTL expires. Invalidate (delete key) or update (set new value) on write so next read either loads fresh from DB (cache-aside) or gets the updated value.

---

## Q3. (Intermediate) Write Node.js code for a cache-aside get: if key exists in Redis return it; otherwise load from an async function (e.g. DB), set in Redis with TTL, and return.

**Answer:**
```javascript
async function getCached(redis, key, loader, ttlSeconds = 300) {
  const cached = await redis.get(key);
  if (cached !== null) return JSON.parse(cached);
  const data = await loader();
  await redis.set(key, JSON.stringify(data), 'EX', ttlSeconds);
  return data;
}
// Usage: getCached(redis, 'user:123', () => User.findById('123'))
```

---

## Q4. (Intermediate) What is cache stampede (thundering herd)? How can you mitigate it?

**Answer:**  
**Cache stampede**: many requests hit at once when cache expires; all miss and hit the DB simultaneously. **Mitigation**: (1) **Probabilistic early expiry** — before TTL, one request extends TTL and others keep using stale. (2) **Single-flight** (lock): first request does the load, others wait (e.g. in-process lock or Redis lock) and then read from cache. (3) **Stale-while-revalidate**: return stale, refresh in background.

---

## Q5. (Intermediate) How would you cache a user session in Redis from a Node.js backend? What key and TTL?

**Answer:**  
Store session data (e.g. JSON) under a key like **session:SESSION_ID** (session ID from cookie or token). **SET session:abc123 &lt;json&gt; EX 86400** (24 hours). On each request: GET key; if missing, treat as logged out. On login: create session, SET with TTL. On logout: DEL key. Optionally refresh TTL on activity (EXPIRE or SET with new EX).

---

## Q6. (Advanced) What is write-through vs write-behind cache? When would you use each?

**Answer:**  
**Write-through**: write to cache and DB together (or write to cache, cache writes to DB). Reads are fast; writes see full DB latency. **Write-behind** (write-back): write to cache only, async flush to DB. Lower write latency; risk of data loss if cache fails before flush. Use write-through for consistency; write-behind only when you can tolerate loss or have another durability mechanism.

---

## Q7. (Advanced) Production scenario: Your API returns a list of “trending products” computed every 5 minutes by a job. How do you cache it in Redis and serve it from the API? Show key design and invalidation.

**Answer:**  
**Key**: e.g. `trending:products`. **Job** (every 5 min): compute trending list, then **SET trending:products &lt;JSON&gt; EX 600** (10 min TTL as buffer). **API**: **GET trending:products**; on miss return empty or run computation once (or serve stale from previous key). **Invalidation**: job overwrites the key; no explicit delete needed. Optional: use two keys and flip (e.g. `trending:products:v1` / `v2`) so the job writes to the inactive key, then swap for zero-downtime update.

---

## Q8. (Advanced) How do you cache paginated list results (e.g. “page 2 of products”) in Redis? What are the pitfalls?

**Answer:**  
**Option 1**: Cache each page as a key: `products:page:2` or `products:filter:category=X:page:2`. Invalidate all `products:*` (or matching prefix) when products change — use a pattern delete (SCAN + DEL) or a versioned key: `products:v123:page:2` and bump v on update. **Pitfall**: many keys if many filter combinations; invalidation is hard. **Option 2**: Cache the full result set (or IDs) and paginate in app — good for small result sets. Prefer caching **stable** queries (e.g. “top 100”) rather than arbitrary filters.

---

## Q9. (Advanced) How would you integrate Redis cache with a Python (e.g. Django/Flask) or Java (Spring) backend? What does “cache backend” mean?

**Answer:**  
**Cache backend**: the storage used for the framework’s cache API (e.g. Django’s cache.set/get). **Django**: `CACHES = { 'default': { 'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': 'redis://127.0.0.1:6379/1' } }` then `cache.get(key)`, `cache.set(key, value, timeout)`. **Spring**: `@EnableCaching` and Redis as cache manager; `@Cacheable("users")` on method. Same pattern: abstract cache interface, Redis as implementation; connection pool and serialization handled by the driver/framework.

---

## Q10. (Advanced) How do you avoid caching sensitive data inappropriately? What should never be cached in Redis?

**Answer:**  
**Never cache**: raw passwords, full credit card numbers, unencrypted PII if Redis is not locked down and encrypted. **Minimize**: cache only non-sensitive or non-PII (e.g. product catalog, public profile). If you cache user-specific data: use a key that’s hard to guess (e.g. session id or token), set TTL, use Redis AUTH and TLS. Prefer caching **identifiers** or **public** data; fetch sensitive data from the primary store (DB) when needed.
