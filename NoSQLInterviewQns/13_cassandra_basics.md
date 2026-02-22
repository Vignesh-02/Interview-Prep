# 13. Cassandra Basics & Data Model

## Q1. (Beginner) What is Apache Cassandra? What type of NoSQL is it?

**Answer:**  
**Cassandra** is a **wide-column** (column-family) distributed database. Data is stored in **tables** with **partition key** + **clustering columns**; rows are grouped by partition and sorted within partition. It’s designed for **high write throughput**, **horizontal scaling**, and **multi-datacenter** replication. No single point of failure; tunable consistency.

---

## Q2. (Beginner) What is a partition key? What is a clustering column?

**Answer:**  
**Partition key** determines which node(s) own the row and groups rows together. All rows with the same partition key are stored together (same partition). **Clustering column(s)** define the **order** of rows within a partition. So primary key = (partition key, clustering columns). Example: (user_id) as partition key; (created_at) as clustering column → “all events for user, ordered by time.”

---

## Q3. (Intermediate) Write a CQL statement to create a table `events` with partition key `user_id`, clustering column `event_time`, and columns `event_type`, `payload`. Choose appropriate types.

**Answer:**
```sql
CREATE TABLE events (
  user_id uuid,
  event_time timestamp,
  event_type text,
  payload text,
  PRIMARY KEY (user_id, event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);
```
Use **CLUSTERING ORDER BY** for default sort (e.g. latest first). For payload you might use **blob** or **text** (JSON).

---

## Q4. (Intermediate) How do you insert and query by partition key in Cassandra? Why can’t you query by only clustering column?

**Answer:**  
**Insert**: `INSERT INTO events (user_id, event_time, event_type, payload) VALUES (?, ?, ?, ?);`  
**Query**: `SELECT * FROM events WHERE user_id = ?;` — fetches entire partition. You can add clustering filter: `WHERE user_id = ? AND event_time &gt; ?`. You **cannot** query by only clustering column (e.g. `WHERE event_time &gt; ...`) because that would require scanning all partitions. Queries must include the partition key (or use a secondary index / materialized view, with caveats).

---

## Q5. (Intermediate) What is eventual consistency in Cassandra? What are ONE, QUORUM, and ALL?

**Answer:**  
Cassandra is **tunable consistency**. **ONE**: one replica responds (fast, may be stale). **QUORUM**: majority of replicas (e.g. 2 of 3) must respond; strong consistency for reads and writes at QUORUM. **ALL**: every replica (slowest, strongest). **LOCAL_ONE**, **LOCAL_QUORUM**: within same DC. Use QUORUM for read and write to get linearizability for that key; ONE for low latency when you accept staleness.

---

## Q6. (Advanced) How does the backend (e.g. Node.js) connect to Cassandra and run a query? Show driver usage.

**Answer:**  
Use **cassandra-driver** (DataStax Node.js driver). Connect with contact points and keyspace; execute with parameterized queries.

```javascript
const cassandra = require('cassandra-driver');
const client = new cassandra.Client({
  contactPoints: ['127.0.0.1'],
  localDataCenter: 'datacenter1',
  keyspace: 'myapp'
});
const q = 'SELECT * FROM events WHERE user_id = ? LIMIT 100';
const result = await client.execute(q, [userId], { prepare: true });
const rows = result.rows;
```
Use **prepare: true** for prepared statements (performance and safety). Handle reconnection and pool in production.

---

## Q7. (Advanced) What is a secondary index in Cassandra? When is it useful and when should you avoid it?

**Answer:**  
A **secondary index** lets you query by a non-partition key column (e.g. by `email`). Cassandra maintains an index per node for its local data; query fans out to all nodes and can be slow. **Use** for low-cardinality or when query volume on that column is low. **Avoid** for high-cardinality (e.g. unique email) or high query rate — use a **denormalized table** (separate table keyed by email) instead.

---

## Q8. (Advanced) Production scenario: You need to store high-volume click events (user_id, timestamp, url, device). Design the table for efficient “get last 100 events per user” and “get events in time range for one user.” Show CQL and justify the key.

**Answer:**  
Partition by **user_id**; cluster by **timestamp** (desc for “last first”):

```sql
CREATE TABLE click_events (
  user_id uuid,
  event_time timestamp,
  url text,
  device text,
  PRIMARY KEY (user_id, event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);
```
**Last 100**: `SELECT * FROM click_events WHERE user_id = ? LIMIT 100;` — single partition, already sorted. **Time range**: `WHERE user_id = ? AND event_time &gt;= ? AND event_time &lt;= ?`. Partition key user_id keeps one user’s data together and on the same node; clustering gives order and range support.

---

## Q9. (Advanced) What is a materialized view in Cassandra? How does it differ from a secondary index?

**Answer:**  
A **materialized view** is a separate table that’s automatically updated when the base table changes; it has a **different primary key** (e.g. base table keyed by user_id, MV keyed by (event_type, user_id)). So you get a different partition layout for different query patterns. **Secondary index** is an index on one column, query still goes to base table partitions. MV = new table (storage cost, write amplification); use when you need a different partition key for a query pattern.

---

## Q10. (Advanced) Why does Cassandra not support JOINs or subqueries? How does the backend typically assemble “joined” data?

**Answer:**  
Cassandra is optimized for **partition-local** reads; JOINs would require cross-partition or cross-node reads, which don’t scale. **Approach**: **denormalize** — store data in the shape you need for each query (multiple tables with different partition keys). Backend does multiple queries (e.g. get user, get orders by user_id) and assembles in application code. Design tables per query pattern; accept duplication.
