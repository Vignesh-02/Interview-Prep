# 8. Redis Basics & Data Structures

## Q1. (Beginner) What is Redis? What type of store is it?

**Answer:**  
**Redis** is an in-memory **key-value** store that can persist to disk. It supports multiple **data structures** (strings, hashes, lists, sets, sorted sets, streams, etc.) and is often used for caching, sessions, rate limiting, pub/sub, and real-time features. Single-threaded for commands; very fast.

---

## Q2. (Beginner) Name five Redis data types and one typical use for each.

**Answer:**  
(1) **String** — cache value, counter (INCR), simple key-value. (2) **Hash** — object (e.g. user profile: HGET/HSET by field). (3) **List** — queue, recent items (LPUSH/LRANGE). (4) **Set** — unique members, tags, “who liked.” (5) **Sorted Set (ZSET)** — leaderboard, time-ordered feed (score = timestamp or rank). (6) **Stream** — event log, consumer groups.

---

## Q3. (Intermediate) How do you set a key with an expiration in Redis? What is the TTL?

**Answer:**  
**SET key value EX 3600** (expire in 3600 seconds) or **SETEX key 3600 value**. Or **SET key value** then **EXPIRE key 3600**. **TTL key** returns seconds until expiry (-1 = no expiry, -2 = key doesn’t exist). **PTTL** returns milliseconds.

---

## Q4. (Intermediate) Write Redis commands to: (1) increment a counter, (2) get the counter, (3) add a member to a set, (4) get all members of the set.

**Answer:**  
(1) **INCR mycounter** (or INCRBY mycounter 5). (2) **GET mycounter**. (3) **SADD myset "member1"**. (4) **SMEMBERS myset**. For “add only if not exists”: **SET key value NX EX 60**.

---

## Q5. (Intermediate) What is a Redis Hash? When would you use it instead of a string (e.g. JSON)?

**Answer:**  
A **hash** is a map of field-value pairs (e.g. user:123 → { name, email, age }). **HSET user:123 name "Jane" email "j@x.com"**; **HGET user:123 name**. Use a hash when you need to read/update **individual fields** without serializing the whole object. Use a string (JSON) when you always read/write the whole object. Hashes allow partial updates and smaller network payloads per field.

---

## Q6. (Advanced) How do you implement a “recent 10 items” list per user using Redis? Show commands and a simple Node.js example.

**Answer:**  
Use a **list**: LPUSH to add new item, LTRIM to keep only 0..9, LRANGE to read.

**Redis:**  
`LPUSH recent:user:123 itemId` then `LTRIM recent:user:123 0 9`.  
`LRANGE recent:user:123 0 9` to get recent 10.

**Node (ioredis):**
```javascript
async function addRecent(redis, userId, itemId) {
  const key = `recent:user:${userId}`;
  await redis.lpush(key, itemId);
  await redis.ltrim(key, 0, 9);
  await redis.expire(key, 86400); // optional: expire after 1 day
}
async function getRecent(redis, userId) {
  return redis.lrange(`recent:user:${userId}`, 0, 9);
}
```

---

## Q7. (Advanced) What is a sorted set (ZSET)? How do you add a member with a score and retrieve the top 5 by score?

**Answer:**  
**ZSET** stores unique members with a numeric **score**; ordered by score. **ZADD leaderboard 100 "user1" 200 "user2"**. **ZRANGE leaderboard 0 4 REV WITHSCORES** — top 5 by highest score. **ZRANK leaderboard "user1"** — 0-based rank (ascending); **ZREVRANK** for high-to-low. Use for leaderboards, priority queues, time-ordered feeds (score = timestamp).

---

## Q8. (Advanced) Production scenario: You need to rate-limit API requests to 100 per minute per API key. Design the solution with Redis and show the Node.js logic.

**Answer:**  
**Sliding window** with a sorted set: key = `ratelimit:api:${apiKey}`, member = request id (e.g. uuid), score = timestamp in ms. Each request: (1) ZREMRANGEBYSCORE key -inf (now - 60000) to remove older than 1 min. (2) ZCARD key → if &lt; 100, ZADD and allow; else reject.

**Node (ioredis):**
```javascript
async function checkRateLimit(redis, apiKey, limit = 100, windowMs = 60000) {
  const key = `ratelimit:api:${apiKey}`;
  const now = Date.now();
  const windowStart = now - windowMs;
  await redis.zremrangebyscore(key, '-inf', windowStart);
  const count = await redis.zcard(key);
  if (count >= limit) return { allowed: false };
  await redis.zadd(key, now, `${now}:${Math.random()}`);
  await redis.expire(key, Math.ceil(windowMs / 1000) + 1);
  return { allowed: true };
}
```

---

## Q9. (Advanced) How does Redis handle persistence? What are RDB and AOF?

**Answer:**  
**RDB**: snapshot of the dataset at a point in time (SAVE/BGSAVE); compact, fast restore; can lose data since last snapshot. **AOF**: append-only log of write commands; better durability (fsync policy); larger and slower replay. Can use both: RDB for backup, AOF for durability. Configure **appendonly yes** and **appendfsync everysec** (or always for stronger durability, slower).

---

## Q10. (Advanced) From a backend (e.g. Node.js), how do you connect to Redis and run commands? Show connection and error handling.

**Answer:**  
Use **ioredis** (or **redis**): create client, use async commands, handle errors and reconnection.

```javascript
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379', {
  maxRetriesPerRequest: 3,
  retryStrategy(times) { return Math.min(times * 100, 3000); }
});
redis.on('error', (err) => console.error('Redis error', err));
redis.on('connect', () => console.log('Redis connected'));

await redis.set('key', 'value', 'EX', 60);
const val = await redis.get('key');
```
Use one client per process (connection pool inside client); close on shutdown.
