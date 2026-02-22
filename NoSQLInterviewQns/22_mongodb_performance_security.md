# 22. MongoDB Performance, Profiling & Security — Senior

## Q1. (Beginner) How do you find slow queries in MongoDB?

**Answer:**  
(1) **Database profiler**: `db.setProfilingLevel(1, { slowms: 100 })` — log queries slower than 100ms; `db.system.profile.find()` to inspect. (2) **currentOp**: `db.currentOp({ "active": true, "secs_running": { "$gte": 2 } })` for long-running ops. (3) **explain**: `db.collection.find(...).explain("executionStats")` to see plan, docs examined, time. Use profiler in dev/staging; be careful in production (overhead).

---

## Q2. (Beginner) What does `explain("executionStats")` tell you? What should you look for?

**Answer:**  
It returns the **execution plan** and **stats**: which index was used (inputStage), **totalDocsExamined** vs **nReturned** (ideal: examined ≈ returned), **executionTimeMillis**. Look for: **COLLSCAN** (collection scan) on large collections = bad; **IXSCAN** (index scan) = good. If examined >> returned, consider a better index or query shape.

---

## Q3. (Intermediate) What are capped collections? When would you use one?

**Answer:**  
**Capped collections** are fixed-size, **circular** buffers: when full, oldest documents are overwritten. They maintain **insertion order** and support fast inserts and in-order reads. Use for: **logging** (last N), **recent activity**, **cache**-like data, or when you want automatic eviction. Create: `db.createCollection("logs", { capped: true, size: 1048576, max: 1000 })`.

---

## Q4. (Intermediate) How do you configure role-based access control (RBAC) in MongoDB?

**Answer:**  
Enable **authentication** (e.g. SCRAM-SHA-256 or x.509). **Create users** with roles: `db.createUser({ user: "app", pwd: "...", roles: [ { role: "readWrite", db: "myapp" } ] })`. Built-in roles: read, readWrite, dbAdmin, userAdmin, clusterAdmin, etc. **Custom roles**: `db.createRole({ role: "custom", privileges: [...], roles: [] })`. Connect with username/password or x.509 cert; backend uses connection string with credentials.

---

## Q5. (Intermediate) What is a covered query? How do you achieve it?

**Answer:**  
A **covered** query is satisfied entirely from the **index** (no document fetch). All projected fields and filter fields must be in the index; then **totalDocsExamined** is 0. Create an index that includes the fields you filter and return (e.g. compound index); use projection to only request those fields. Use **explain()** to confirm.

---

## Q6. (Advanced) Production scenario: A production query is slow (2+ seconds). Walk through the steps you’d take to diagnose and fix it (including backend and DB).

**Answer:**  
(1) **Reproduce**: run the same query with explain("executionStats"); check for COLLSCAN, high totalDocsExamined. (2) **Index**: add compound index matching filter + sort; verify with explain that IXSCAN is used. (3) **Query shape**: ensure filter uses indexed fields (no $where, no heavy regex on unindexed field). (4) **Backend**: ensure no N+1; use projection to limit fields; add pagination (limit). (5) **Profiler**: enable briefly to capture slow ops; review system.profile. (6) **Hardware**: check RAM, disk; ensure working set fits in RAM. Document the fix (index + query) and monitor latency after.

---

## Q7. (Advanced) How do you secure a MongoDB deployment (authentication, network, encryption)?

**Answer:**  
(1) **Authentication**: enable auth (e.g. `security.authorization: enabled`); create users with least privilege; use strong passwords or x.509. (2) **Network**: bind to private IP; firewall so only app and admin can reach MongoDB; no public internet. (3) **Encryption**: TLS for client-server; encryption at rest (WiredTiger or storage layer). (4) **Audit**: enable audit log for sensitive actions. (5) **Updates**: keep MongoDB patched.

---

## Q8. (Advanced) What is the difference between `db.collection.find()` and aggregation `$match` in terms of index usage? When would you prefer aggregation for performance?

**Answer:**  
Both can use an index if the filter matches an index prefix. **find()** uses a single index (or index intersection in some cases). **Aggregation** $match at the **beginning** of the pipeline is pushed down and can use an index; later stages (e.g. $group) don’t use indexes. Prefer aggregation when you need $group, $lookup, $sort on computed fields; put $match first and ensure it’s selective so the pipeline is efficient.

---

## Q9. (Advanced) How would you implement connection pooling in a Node.js app for MongoDB? What are best practices?

**Answer:**  
**Mongoose**: one connection (pool) per process: `mongoose.connect(uri, { maxPoolSize: 10 })`. **Native driver**: `new MongoClient(uri, { maxPoolSize: 10 })` then `client.connect()`; reuse the same client for all requests. **Best practices**: single client per process; set maxPoolSize to match expected concurrency (and DB max connections); use connection string with replica set for HA; handle disconnect/reconnect (driver often does automatically). Don’t open a new client per request.

---

## Q10. (Advanced) What is MongoDB’s read concern “majority” and “linearizable”? When would you use linearizable read in the backend?

**Answer:**  
**majority**: read data that has been acknowledged by a majority of replica set members; no dirty reads. **linearizable**: single read that is linearizable with concurrent writes (strongest); use when you need to be sure you see the very latest committed state once (e.g. “read after write” for critical path). **Use linearizable** sparingly (higher latency); use **majority** for most strong-consistency reads. Backend: pass readConcern in options for that specific read.
