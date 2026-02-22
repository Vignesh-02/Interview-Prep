# 14. Cassandra CQL & Partition Key Design

## Q1. (Beginner) What is CQL? How is it similar to and different from SQL?

**Answer:**  
**CQL** (Cassandra Query Language) is SQL-like syntax for Cassandra. Similar: SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, WHERE. Different: no JOINs, no subqueries, no arbitrary WHERE — **WHERE must include partition key**; clustering columns can use = or range. Limited aggregations; no foreign keys. It’s a surface syntax; the model is partition + clustering.

---

## Q2. (Beginner) What makes a “good” partition key in Cassandra?

**Answer:**  
**Good** partition key: (1) **High cardinality** — many distinct values so data spreads across nodes. (2) **Even distribution** — no hot partitions (one key with huge traffic or size). (3) **Matches query** — every query that reads by this key is efficient. Avoid: low cardinality (e.g. boolean), monotonic (e.g. timestamp alone), or one key that gets most writes (e.g. “global” partition).

---

## Q3. (Intermediate) What is a composite partition key? When would you use (a, b) as partition key vs (a) partition and (b) clustering?

**Answer:**  
**Composite partition key**: (a, b) together form the partition key; rows with same (a, b) are in one partition. Use **(a, b)** when you want **smaller partitions** (e.g. (user_id, date) so partition = one user’s one day). Use **(a)** partition and **(b)** clustering when you want **all of a** in one partition and order by b (e.g. user_id partition, event_time clustering). Composite partition key = more, smaller partitions; single partition key + clustering = fewer, potentially larger partitions.

---

## Q4. (Intermediate) Write a CQL query to insert a row and a query to update only one column of that row. What is the difference from RDBMS UPDATE?

**Answer:**  
**Insert**: `INSERT INTO events (user_id, event_time, type) VALUES (?, ?, ?);`  
**Update**: `UPDATE events SET type = ? WHERE user_id = ? AND event_time = ?;`  
In Cassandra, UPDATE is actually an **upsert** (insert if not exists). There’s no “read then write”; you set columns. No locking; last write wins per cell (with timestamp). Specify full primary key in WHERE.

---

## Q5. (Intermediate) How do you delete a row? How do you delete only one column?

**Answer:**  
**Delete row**: `DELETE FROM events WHERE user_id = ? AND event_time = ?;` (full primary key). **Delete column**: `DELETE type FROM events WHERE user_id = ? AND event_time = ?;` — only that column is removed (tombstone). Deletes create **tombstones**; avoid deleting many columns or rows and then reusing the same key (tombstone accumulation).

---

## Q6. (Advanced) What is a “hot partition”? How do you avoid it when designing for time-series data?

**Answer:**  
**Hot partition**: one partition receives disproportionate read/write (e.g. “last hour” or “current day” as partition key). **Avoid**: (1) **Composite partition key** — e.g. (sensor_id, bucket) where bucket = time window (e.g. day or hour) so writes spread across partitions. (2) **Add randomness** — e.g. (user_id, date, random_suffix). (3) **Avoid “current” as partition** — e.g. don’t use “today” as single key; use (sensor_id, date) so each day is a partition per sensor.

---

## Q7. (Advanced) Design a table for “messages by conversation,” where you need: list messages in a conversation in time order; paginate; and avoid huge partitions. Show primary key and CQL.

**Answer:**  
Partition by conversation_id; cluster by time. To avoid huge partitions, **bucket** by time (e.g. month): partition key = (conversation_id, month), clustering = message_time.

```sql
CREATE TABLE messages (
  conversation_id uuid,
  bucket int,  -- e.g. 202401 for Jan 2024
  message_time timestamp,
  message_id timeuuid,
  sender_id uuid,
  body text,
  PRIMARY KEY ((conversation_id, bucket), message_time, message_id)
) WITH CLUSTERING ORDER BY (message_time DESC, message_id DESC);
```
Query: know the month(s) you need, then `WHERE conversation_id = ? AND bucket = ? LIMIT 100`. For “latest” across months, query latest bucket(s) in app.

---

## Q8. (Advanced) Production scenario: Writes are 10M events/day by (device_id, event_time). How do you choose partition key and bucket size so partitions stay under 100MB and no hot partition?

**Answer:**  
Partition key: **(device_id, date)** or **(device_id, hour)** so each partition is one device’s data for one day (or hour). **Size estimate**: 10M / (devices * days) per partition; tune bucket (e.g. day vs hour) so partition size &lt; 100MB. If devices are few, add **hour** to partition: (device_id, date, hour). Avoid (event_time) or (date) alone as partition — that would create one hot partition per time bucket. Prefer (device_id, time_bucket) so load is spread by device.

---

## Q9. (Advanced) What is ALLOW FILTERING? Why is it dangerous and when might you still use it?

**Answer:**  
**ALLOW FILTERING** lets you run a WHERE that doesn’t include the full partition key (e.g. filter by non-indexed column). Cassandra then scans full table (or large set) and filters in memory — **very expensive**, can time out or overload. Use only for **admin/debug** or one-off scripts on small data. In production, **avoid**; design tables and secondary indexes or MVs so you don’t need ALLOW FILTERING.

---

## Q10. (Advanced) How does the Java/Node driver handle prepared statements? Why use them?

**Answer:**  
**Prepared statement**: query is parsed once on the server; client sends statement id + bound values. **Benefits**: (1) **Performance** — no repeated parsing. (2) **Safety** — parameters are bound, not concatenated (no CQL injection). (3) **Driver caching** — driver caches prepared statements per query string. In Node: `client.execute(query, params, { prepare: true })`. Always use prepare for repeated queries with parameters.
