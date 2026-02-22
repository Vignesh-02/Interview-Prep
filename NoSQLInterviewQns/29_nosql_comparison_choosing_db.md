# 29. NoSQL Comparison & Choosing the Right DB — Senior

## Q1. (Beginner) When would you choose MongoDB over PostgreSQL (or vice versa)?

**Answer:**  
**MongoDB**: flexible schema, document model, rich queries and aggregation, horizontal scale (sharding), good for catalogs, content, app data with nested structures. **PostgreSQL**: relational, ACID, JOINs, complex queries, strong consistency, good for transactions and normalized data. Choose MongoDB when schema evolves often, data is document-like, or you need scale-out document store; choose PostgreSQL when you need strict schema, relations, and complex transactional logic.

---

## Q2. (Beginner) When would you use Redis vs MongoDB for “session store”?

**Answer:**  
**Redis**: in-memory, very fast, TTL natively, simple key-value; ideal for **session store** (session id → session data, expire after 30 min). **MongoDB**: persistent, can store sessions too; use when you need to **query** sessions (e.g. “all sessions for user”), persist long-term, or already use MongoDB and don’t want another store. Prefer **Redis** for performance and TTL; use MongoDB if you need queryability or single DB.

---

## Q3. (Intermediate) Compare Cassandra and DynamoDB: data model, consistency, and operational model.

**Answer:**  
**Data model**: both partition key + sort key (DynamoDB PK/SK, Cassandra PK/clustering). No JOINs; design for access patterns. **Consistency**: Cassandra tunable (ONE, QUORUM, etc.); DynamoDB strong or eventual read. **Operational**: DynamoDB is **managed** (serverless or provisioned on AWS); Cassandra is **self-managed** or managed (e.g. Astra). Cassandra: multi-DC, more control; DynamoDB: less ops, AWS-native, global table. Choose DynamoDB for managed and AWS; Cassandra for multi-cloud or heavy multi-DC and control.

---

## Q4. (Intermediate) When would you use Elasticsearch as the primary store vs a secondary search index?

**Answer:**  
**Primary store**: only when the main use case is **search and analytics** and you can tolerate no ACID (e.g. log platform, some content platforms). **Secondary index**: use a **primary store** (e.g. PostgreSQL, MongoDB) for source of truth and **sync** to Elasticsearch for search; use ES for full-text and aggregations, primary for writes and consistency. Prefer secondary index in most apps; primary only for search-first workloads.

---

## Q5. (Intermediate) Give a 2x2 or short comparison: MongoDB, Redis, Cassandra, DynamoDB — by “primary use case” and “consistency model.”

**Answer:**  
| Store     | Primary use case        | Consistency model        |
|----------|-------------------------|---------------------------|
| MongoDB  | Document app data       | Strong (primary); tunable |
| Redis    | Cache, sessions, queues | Single-node strong        |
| Cassandra| High-write, multi-DC    | Tunable (AP or CP-like)  |
| DynamoDB | Serverless key/doc     | Strong or eventual        |

---

## Q6. (Advanced) Production scenario: You are building a system with: (1) user accounts and profiles, (2) real-time presence and chat, (3) full-text search over content, (4) high-volume event ingestion. Which stores would you use and why?

**Answer:**  
(1) **User accounts/profiles**: **PostgreSQL** or **MongoDB** — source of truth, flexible or relational. (2) **Real-time presence/chat**: **Redis** — pub/sub or structures (presence set, recent messages); low latency. (3) **Full-text search**: **Elasticsearch** — index content from (1); search and facets. (4) **High-volume events**: **Cassandra** or **DynamoDB** — append-heavy, partition by device/user+time; or **Kafka** + sink. Use the right tool per sub-system; integrate via APIs or events.

---

## Q7. (Advanced) How do MongoDB, Cassandra, and DynamoDB differ in “schema flexibility” and “query flexibility”?

**Answer:**  
**MongoDB**: **schema-flexible** (documents can have different fields); **query-flexible** (rich queries, aggregation, $lookup). **Cassandra**: **schema required** (table with columns); **query inflexible** — query by partition key (+ clustering); no ad-hoc filter on arbitrary columns without secondary index or scan. **DynamoDB**: **schema-flexible** per item (attributes); **query** by PK/SK or GSI/LSI only. So: MongoDB most query-flexible; Cassandra and DynamoDB require access-pattern-first design.

---

## Q8. (Advanced) When would you use both Redis and Memcached? When is Redis enough?

**Answer:**  
**Redis** is enough for most caching: structures (hash, set, sorted set), persistence, TTL, Lua, pub/sub, replication. **Memcached**: simpler (key-value only), multi-threaded, sometimes lower latency for pure get/set at very high QPS. Use **both** only if you have an existing Memcached deployment and want to keep it while adding Redis for richer features. Prefer **Redis only** for new systems.

---

## Q9. (Advanced) Compare “single-table design” in DynamoDB to “one collection per entity” in MongoDB. What is the philosophical difference?

**Answer:**  
**DynamoDB single-table**: put multiple **entity types** and relationships in one table with **overloaded** PK/SK (e.g. USER#id, ORDER#id); design keys for **all** access patterns; use GSI for alternate keys. **MongoDB**: often **one collection per entity** (users, orders); use indexes and aggregation for access patterns. **Philosophy**: DynamoDB favors **one table, many patterns** (key design is critical); MongoDB favors **one collection per concept** and flexible query/index. Both can denormalize; DynamoDB pushes more design into the key model.

---

## Q10. (Advanced) How would you explain to a team “we use PostgreSQL + Redis + Elasticsearch” in one sentence per store and when the backend talks to which?

**Answer:**  
**PostgreSQL**: source of truth for users, orders, and transactional data; backend reads/writes for CRUD and transactions. **Redis**: cache and sessions; backend checks cache (e.g. cache-aside), writes on update; rate limits and real-time structures. **Elasticsearch**: search index; backend queries ES for full-text search and facets; index is updated from PostgreSQL (dual-write or CDC). So: **write to Postgres (and invalidate/update cache, index)**; **read from Postgres or Redis or ES** depending on the API.
