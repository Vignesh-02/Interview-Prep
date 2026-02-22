# 30. NoSQL Backend Integration & Production Patterns — Senior

## Q1. (Beginner) How does a Node.js backend typically connect to MongoDB and Redis at startup? What should happen on shutdown?

**Answer:**  
**Startup**: create **one** client per process (MongoDB: Mongoose or MongoClient; Redis: ioredis). Connect at app start (e.g. `mongoose.connect(uri)`, `new Redis(url)`). Use env vars for URLs. **Shutdown**: on SIGTERM/SIGINT, **close** the connection (e.g. `mongoose.connection.close()`, `redis.quit()`) so in-flight ops complete and connections drain. Don’t create a new client per request.

---

## Q2. (Beginner) What is connection pooling? How does it apply to MongoDB and Redis in the backend?

**Answer:**  
**Connection pooling**: reuse a fixed set of connections for many requests instead of opening/closing per request. **MongoDB**: driver maintains a pool (e.g. maxPoolSize: 10); each request uses a connection from the pool. **Redis**: one connection (or a small pool) per process is often enough; ioredis uses one by default. Set pool size to match concurrency and DB limits (e.g. max connections per DB).

---

## Q3. (Intermediate) How do you handle “database unavailable” (e.g. MongoDB or Redis down) in the API? What do you return to the client?

**Answer:**  
(1) **Catch** connection/network errors in the data layer. (2) **Retry** with backoff for transient failures (driver may do this). (3) **Return 503** (or 500) with a generic message; don’t leak internal errors. (4) **Circuit breaker** (optional): after N failures, stop calling DB for a period, then try again. (5) **Health check** endpoint that checks DB; load balancer can use it. For cache down: serve from DB (degraded but working); for primary DB down: return 503 and retry later.

---

## Q4. (Intermediate) Describe a pattern where the backend writes to MongoDB and then updates Redis (e.g. cache invalidation). What order and what if Redis update fails?

**Answer:**  
**Order**: (1) Write to **MongoDB** first (source of truth). (2) Then **invalidate or update** Redis (e.g. DEL key or SET new value). If Redis update **fails**: log and optionally retry; next read will miss cache and load from MongoDB (cache-aside), so data stays correct. **Don’t** write to Redis first then MongoDB — if MongoDB fails, cache has wrong data. Optionally: publish “invalidate” event and let a subscriber update Redis (eventual).

---

## Q5. (Intermediate) How would you implement “read-your-writes” for a user session when using MongoDB with read preference secondary?

**Answer:**  
After a **write** (e.g. profile update), either: (1) **Read from primary** for the next request (e.g. pass a flag or use primary for that user for a short time). (2) **Sticky session** to primary: route that user’s requests to primary for N seconds. (3) Use **read preference primary** for requests that must see latest (e.g. “get my profile” after edit); use **secondary** only for non-critical reads. In code: use different read preference per route or per request context.

---

## Q6. (Advanced) Production scenario: Your API uses MongoDB (primary), Redis (cache), and Elasticsearch (search). Describe how a “create product” flow would touch all three and how you’d keep them eventually consistent.

**Answer:**  
(1) **API** receives create product. (2) **Write to MongoDB** (source of truth); get product id. (3) **Invalidate or skip** cache for “product list” or related keys (e.g. DEL cache key or tag). (4) **Index in Elasticsearch**: either (a) same process after MongoDB success (fire-and-forget or await), or (b) publish event (e.g. to queue) and a worker indexes to ES. **Eventually consistent**: ES may lag; search could show product after a short delay. If ES write fails, retry (queue or cron to sync from MongoDB). Cache-aside on read: miss will load from MongoDB and repopulate cache.

---

## Q7. (Advanced) How do you run database migrations (e.g. schema or index changes) for MongoDB in a zero-downtime deployment?

**Answer:**  
(1) **Indexes**: create with **background: true** (or 4.2+ default); application works during build. (2) **Schema**: MongoDB is schema-flexible; add new fields and backfill in batches; application handles both old and new shape. (3) **Multi-phase**: deploy code that reads old and new format; run migration job; then deploy code that writes only new format; then remove old field. (4) **Replica set**: deploy app that works with both versions; migrate; no single “big bang” migration window.

---

## Q8. (Advanced) What is the role of health checks for MongoDB, Redis, and Elasticsearch in a Kubernetes or load balancer setup?

**Answer:**  
**Health checks**: **liveness** (is the app up?) and **readiness** (can the app serve traffic?). **Readiness** should **depend on DBs**: e.g. ping MongoDB, Redis, (and optionally ES); if any critical store is down, mark pod not ready so LB doesn’t send traffic. **Liveness** may only check process. Use **short timeouts** so unhealthy pods are removed quickly. Don’t fail liveness on transient DB blip; use readiness and retries. Expose `/health` that checks DB connectivity.

---

## Q9. (Advanced) How would you implement idempotent “create order” when the backend writes to MongoDB and publishes to a queue (e.g. for search or notifications)? What if the publish fails?

**Answer:**  
**Idempotency**: client sends **idempotency key** (e.g. header). Backend: (1) Check **Redis** (or DB) for that key; if found, return stored response. (2) **Create order** in MongoDB. (3) **Publish** to queue. (4) Store idempotency key → response in Redis (TTL e.g. 24h). If **publish fails**: (a) retry publish with backoff, or (b) store “pending events” in MongoDB and a job retries publish; or (c) return 201 but queue is eventually consistent (worker polls MongoDB for new orders). Ensure order is committed before publish so retry is safe.

---

## Q10. (Advanced) Compare how a Python (Django/Flask) backend would integrate with MongoDB vs a Node.js backend. What is similar and what is different (libraries, connection, patterns)?

**Answer:**  
**Similar**: one connection (or pool) per process; connect at startup; use env for URL; same patterns (cache-aside, read preference). **Node**: **mongoose** or **mongodb** driver; async/await. **Python**: **pymongo** or **motor** (async); Django may use **djongo** or raw pymongo. **Connection**: Node `mongoose.connect(uri)`; Python `MongoClient(uri)`. **Patterns**: same (replica set, read preference, transactions with session). Difference: sync vs async (Flask/Django sync vs Node async); connection is typically in app factory or startup in both.
