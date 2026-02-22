# 12. Redis Use Cases (Locks, Leaderboards, Sessions)

## Q1. (Beginner) How would you implement a “top 10” leaderboard in Redis? Which structure and commands?

**Answer:**  
Use a **sorted set (ZSET)**. Score = points (or time for “latest”). **ZADD leaderboard 150 "user1" 200 "user2"** … **ZREVRANGE leaderboard 0 9 WITHSCORES** for top 10. **ZREVRANK leaderboard "user1"** for a user’s rank (0-based). **ZINCRBY leaderboard 10 "user1"** to add points.

---

## Q2. (Beginner) How do you store a user session in Redis so it expires after 30 minutes?

**Answer:**  
**SET session:SESSION_ID &lt;session_data&gt; EX 1800** (1800 seconds). Or **SETEX session:SESSION_ID 1800 &lt;data&gt;**. On each request, **GET session:SESSION_ID**; if null, session expired. Optionally **EXPIRE session:SESSION_ID 1800** on activity to extend (sliding expiry).

---

## Q3. (Intermediate) Implement “user X liked post Y” and “liked by” count per post using Redis. Show data structures and commands.

**Answer:**  
**Count per post**: `INCR likes:post:POST_ID` on like, `DECR` on unlike (guard &gt; 0). **Who liked** (optional): `SADD liked:post:POST_ID USER_ID`; `SISMEMBER liked:post:POST_ID USER_ID` to check; `SMEMBERS` or `SSCAN` for list. **Toggle like** (idempotent): check SISMEMBER; if not member, SADD and INCR; if member, SREM and DECR. Use two keys: one for count (fast read), one for set (check + list).

---

## Q4. (Intermediate) How would you implement a “recently viewed products” list (max 20) per user in Redis?

**Answer:**  
**List**: **LPUSH recent:user:USER_ID productId**, then **LTRIM recent:user:USER_ID 0 19**. Before LPUSH, **LREM recent:user:USER_ID 1 productId** to remove if already present (then LPUSH so it moves to front). **LRANGE recent:user:USER_ID 0 19** to read. Set **EXPIRE** on the key for TTL (e.g. 7 days).

---

## Q5. (Intermediate) What is Redis Pub/Sub? Give one use case and a simple Node.js subscribe/publish example.

**Answer:**  
**Pub/Sub**: publishers send messages to **channels**; subscribers receive messages on channels they subscribe to. No persistence; fire-and-forget. Use for: real-time notifications, cache invalidation signals, chat. **Node (ioredis):**
```javascript
// Subscriber
redis.subscribe('notifications');
redis.on('message', (channel, message) => console.log(channel, message));
// Publisher (can be another process)
redis.publish('notifications', JSON.stringify({ type: 'alert', data: {} }));
```

---

## Q6. (Advanced) Production scenario: A background job must run exactly once per “run window” (e.g. daily report). Multiple app instances might try to run it. Implement a distributed lock so only one instance runs the job. Show Redis + Node.js.

**Answer:**  
Use a lock key with NX and TTL; only the instance that acquires it runs the job. Release when done (or let it expire as safety).

```javascript
const lockKey = 'lock:daily-report';
const lockVal = `${process.pid}:${Date.now()}`;
const acquired = await redis.set(lockKey, lockVal, 'NX', 'EX', 3600); // 1h TTL
if (!acquired) return; // another instance has it
try {
  await runDailyReport();
} finally {
  const script = `if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end; return 0`;
  await redis.eval(script, 1, lockKey, lockVal);
}
```

---

## Q7. (Advanced) How do you implement a “sliding window” rate limit (e.g. 10 requests per 60 seconds) with Redis? Show ZSET approach.

**Answer:**  
Key per client (e.g. IP or user). ZSET: member = request id (e.g. timestamp:random), score = timestamp in ms. For each request: **ZREMRANGEBYSCORE key (now-60000) +inf** to drop old entries; **ZCARD key**; if &lt; 10, **ZADD key now member**, allow; else reject. **EXPIRE key 61** to clean up.

```javascript
async function slidingWindowLimit(redis, key, limit = 10, windowMs = 60000) {
  const now = Date.now();
  const k = `ratelimit:${key}`;
  await redis.zremrangebyscore(k, 0, now - windowMs);
  const count = await redis.zcard(k);
  if (count >= limit) return false;
  await redis.zadd(k, now, `${now}:${Math.random()}`);
  await redis.expire(k, Math.ceil(windowMs / 1000) + 1);
  return true;
}
```

---

## Q8. (Advanced) When would you use Redis Streams instead of Pub/Sub? What are consumer groups?

**Answer:**  
Use **Streams** when you need: persistence, **replay**, **ack** (message not lost until acknowledged), and **competing consumers** (consumer groups). **Consumer group**: multiple consumers share the stream; each message is delivered to one consumer in the group; messages are acknowledged so they’re not redelivered. Good for task queues, event sourcing, reliable messaging. Pub/Sub is ephemeral and broadcast; Streams are durable and support at-least-once processing.

---

## Q9. (Advanced) How would you use Redis to invalidate application cache when data changes (e.g. “user updated” invalidate cache for that user)?

**Answer:**  
**Option 1**: On user update in the app, **DEL user:USER_ID** (or cache key for that user) so next read does cache-aside load. **Option 2**: **Pub/Sub** — one service publishes `invalidate:user:123`; all app instances subscribe and **DEL** the key in their local cache or in a shared Redis. **Option 3**: **Cache version** — store version in Redis; cache key includes version; on update bump version so old keys are never hit. Option 1 is simplest for single-instance or when all use same Redis; Pub/Sub helps with local caches across instances.

---

## Q10. (Advanced) What are Redis Modules? Name two and their use cases.

**Answer:**  
**Modules** extend Redis with new data types and commands. **RediSearch**: full-text search and secondary indexes on hashes; use for search inside Redis. **RedisJSON**: native JSON type and path queries; use for document-like storage and querying. **RedisGraph**: graph DB; use for relationships. **RedisBloom**: probabilistic structures (Bloom filter); use for “might exist” checks. Use when you need these capabilities without a separate system; otherwise use dedicated search/JSON stores.
