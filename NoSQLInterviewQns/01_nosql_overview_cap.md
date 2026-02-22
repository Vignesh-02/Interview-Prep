# 1. NoSQL Overview, CAP Theorem & Data Models

## Q1. (Beginner) What is NoSQL? Name four common types of NoSQL databases.

**Answer:**  
**NoSQL** = non-relational (or “not only SQL”) databases, often schema-flexible and built for scale/performance. Four types: (1) **Document** (MongoDB, Couchbase) — JSON/BSON documents. (2) **Key-value** (Redis, DynamoDB) — key → value. (3) **Wide-column** (Cassandra, HBase) — rows keyed by partition + clustering columns. (4) **Search** (Elasticsearch) — inverted index for full-text and analytics.

---

## Q2. (Beginner) What does CAP theorem state? What do C, A, and P stand for?

**Answer:**  
**CAP**: In a distributed system you cannot have all three at once: **C**onsistency (every read sees the latest write), **A**vailability (every request gets a response), **P**artition tolerance (system works despite network partitions). In practice, **P** is assumed (networks partition), so you choose **CP** (e.g. strong consistency, may refuse writes) or **AP** (e.g. always respond, eventual consistency). MongoDB, Cassandra, Redis, DynamoDB each make different CAP trade-offs.

---

!DO_LATER
## Q3. (Intermediate) How do MongoDB, Cassandra, and Redis typically position themselves regarding CAP? Which two do they favor?

**Answer:**  
**MongoDB** (replica set): favors **CP** — primary serves reads/writes; on partition it may elect a new primary and drop availability for a short time. **Cassandra**: favors **AP** — always accepts writes/reads; tunable consistency (ONE, QUORUM, ALL). **Redis** (single node): CA when no partition; with **Redis Cluster** it’s **CP** (redirects to correct node; partition can make some keys unavailable). **DynamoDB**: configurable — strong consistency = CP-like; eventually consistent reads = AP-like.

---

## Q4. (Intermediate) Give a one-line use case for when you’d pick: (a) MongoDB, (b) Redis, (c) Cassandra, (d) Elasticsearch, (e) DynamoDB.

**Answer:**  
(a) **MongoDB**: Flexible document store for app data, catalogs, content, with rich queries and aggregation. (b) **Redis**: Caching, sessions, rate limiting, real-time leaderboards, pub/sub. (c) **Cassandra**: High-write, multi-DC, time-series or event data at scale. (d) **Elasticsearch**: Full-text search, log search, analytics over logs/metrics. (e) **DynamoDB**: Serverless key-value/document with predictable latency and AWS integration.

---

## Q5. (Intermediate) What is “eventual consistency”? When is it acceptable in a backend application?

**Answer:**  
**Eventual consistency**: After writes stop, all replicas will eventually converge to the same state; reads may temporarily return stale data. Acceptable when: (1) Read-your-writes isn’t critical (e.g. social feed). (2) You have a way to refresh (e.g. “last updated” or retry). (3) You explicitly choose it for performance (e.g. DynamoDB eventually consistent reads). Not acceptable for: payment balance, inventory deduction, without additional safeguards (e.g. conditional writes, idempotency).

---

## Q6. (Advanced) How would you explain to a backend developer the trade-off between “strong consistency” and “eventual consistency” when choosing a read preference?

**Answer:**  
**Strong consistency**: Read from primary (or quorum); you always see the latest committed write. Use for: checkout, account balance, “edit and immediately show.” **Eventual**: Read from replica or use eventually consistent API; lower latency, but might see stale data. Use for: timelines, dashboards, non-critical reads. In code: MongoDB `readPreference: 'primary'` vs `'secondary'`; DynamoDB `ConsistentRead: true` vs `false`. Document the choice in API contracts (e.g. “this endpoint may be eventually consistent”).

---

## Q7. (Advanced) Production scenario: Your product team wants a “like count” on posts that updates in real time. Writes are high (many likes). Which NoSQL store would you consider and how would the backend update and read the count?

**Answer:**  
**Redis** is a good fit: single key per post (e.g. `likes:post:123`) with **INCR**; O(1) update and read; no hot partition if keys are per post. Backend: on like → `INCR likes:post:123`; on unlike → `DECR`; read → `GET likes:post:123`. Optionally persist to MongoDB/Cassandra asynchronously for durability and recovery. **Alternative**: DynamoDB with atomic counter (UpdateItem with ADD); or MongoDB with `$inc` on a counter field — both work but Redis gives lowest latency for pure counter reads.

**Example (Node.js + ioredis):**
```javascript
async function likePost(redis, postId) {
  await redis.incr(`likes:post:${postId}`);
}
async function getLikeCount(redis, postId) {
  const n = await redis.get(`likes:post:${postId}`);
  return parseInt(n || '0', 10);
}
```

---

## Q8. (Advanced) What is BASE (in contrast to ACID)? Which NoSQL databases are often described as BASE?

**Answer:**  
**BASE**: **B**asically **A**vailable, **S**oft state, **E**ventually consistent. Prioritizes availability and partition tolerance; consistency is eventual. Contrast with **ACID** (atomicity, consistency, isolation, durability) in traditional RDBMS. Cassandra, DynamoDB (eventual read), and many distributed NoSQL systems are described as BASE when used with eventual consistency. MongoDB with replica set and default read from primary is closer to strong consistency (ACID-like for single-document writes).

---

## Q9. (Advanced) Compare how a Node.js backend would connect to MongoDB vs Redis vs Elasticsearch (library and typical connection pattern).

**Answer:**  
**MongoDB**: `mongodb` or `mongoose`; single connection URL; connection pool; `mongoose.connect(uri)` and use models. **Redis**: `ioredis` or `redis`; create client with host/port; connection pool optional (one client per process often enough); `redis.get/set`. **Elasticsearch**: `@elastic/elasticsearch`; Client with `node`; one client, connection pool inside. All: create client at startup, reuse for requests; use env vars for URLs; handle reconnection (MongoDB and Redis support auto-reconnect).

**Example connections:**
```javascript
// MongoDB (Mongoose)
const mongoose = require('mongoose');
await mongoose.connect(process.env.MONGODB_URI);

// Redis (ioredis)
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL);

// Elasticsearch
const { Client } = require('@elastic/elasticsearch');
const es = new Client({ node: process.env.ES_URL });
```

---

## Q10. (Advanced) When would you use both a relational DB (e.g. PostgreSQL) and a NoSQL store in the same backend? Give one concrete example.

**Answer:**  
Use **both** when each solves a different problem. **Example**: PostgreSQL for **transactions and source of truth** (users, orders, payments); **Redis for caching** (session, API response cache, rate limit); **Elasticsearch for search** (product search, log search). Backend: write to Postgres, invalidate or update cache in Redis on write; index to Elasticsearch (sync or async). Another: Postgres for orders, DynamoDB or Cassandra for **high-volume events** (clicks, logs) with async write path.
