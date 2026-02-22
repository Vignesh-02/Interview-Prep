# 21. MongoDB Sharding & Replication — Senior

## Q1. (Beginner) What is a replica set? What are primary and secondary?

**Answer:**  
A **replica set** is a group of MongoDB instances that hold the same data. One is **primary** (accepts writes); others are **secondaries** (replicate from primary, can serve reads). If the primary fails, secondaries elect a new primary (automatic failover). Used for **high availability** and **read scaling** (read from secondaries).

---

## Q2. (Beginner) What is sharding in MongoDB? When would you use it?

**Answer:**  
**Sharding** is **horizontal partitioning**: data is distributed across **shards** (each can be a replica set) by a **shard key**. Use when: data size or write/read throughput exceeds what a single replica set can handle. **mongos** routes queries to the right shard(s). Sharding is for **scale**; replica set is for **HA** and read scaling.

---

## Q3. (Intermediate) What makes a good shard key? What are high cardinality and low frequency?

**Answer:**  
**Good shard key**: (1) **High cardinality** — many distinct values so chunks can be split. (2) **Low frequency** — no single value gets most traffic (avoids hot shard). (3) Matches query patterns (often equality on shard key). **Bad**: monotonic (e.g. timestamp only) → all new writes to one shard; low cardinality (e.g. boolean) → few chunks. **Ideal**: compound like (userId, date) or hashed userId.

---

## Q4. (Intermediate) What is the role of `mongos` in a sharded cluster?

**Answer:**  
**mongos** is the **router** that applications connect to. It: (1) parses queries, (2) determines which shard(s) have the data (from config servers’ chunk metadata), (3) sends the query to shard(s), (4) merges results and returns to the client. Clients never connect directly to shards for normal operations; they connect to mongos.

---

## Q5. (Intermediate) How do you read from a secondary in MongoDB from the driver? What is read preference?

**Answer:**  
**Read preference**: primary (default), primaryPreferred, secondary, secondaryPreferred, nearest. In Node driver: `client.db().collection('c').find().readPreference('secondary')` or in connection string `?readPreference=secondary`. **Mongoose**: `Model.find().read('secondary')` or set at schema/query level. Use secondary for read scaling; accept eventual consistency. Use primary when you need read-your-writes.

---

## Q6. (Advanced) What is a chunk in sharding? What is chunk migration and when does it happen?

**Answer:**  
Data in a sharded collection is divided into **chunks** (ranges of shard key values). Each chunk lives on one shard. **Chunk migration**: when the balancer moves chunks between shards to balance data or load. Happens in the background. **Jumbo chunks** (too large to move) can cause imbalance; avoid with a shard key that splits well (e.g. hashed).

---

## Q7. (Advanced) Production scenario: Your app is single-replica-set and growing. You need zero-downtime HA and the ability to scale reads. Describe adding a replica set and what the backend (MongoDB connection string and read preference) must do.

**Answer:**  
**Setup**: Add 2+ secondaries; form replica set (e.g. 1 primary, 2 secondaries). **Connection string**: use **replica set name** and multiple hosts, e.g. `mongodb://host1:27017,host2:27017,host3:27017/?replicaSet=rs0`. Driver discovers primary and secondaries. **HA**: If primary goes down, driver automatically reconnects to new primary (with retryWrites). **Read scaling**: set **readPreference=secondary** or **secondaryPreferred** for read-only or non-critical reads; keep **primary** for writes and for reads that must see latest. Backend: no code change for HA; optional read preference for read scaling.

---

## Q8. (Advanced) Why can’t you change the shard key after sharding? What are the workarounds?

**Answer:**  
Shard key is used to **route** and **split** data; it’s embedded in every document and chunk. Changing it would require re-distributing all data. **Workarounds**: (1) Create a new sharded collection with the new shard key and **migrate** data (ETL or dual-write then switch). (2) Use **hashed** shard key if you need even distribution and can’t change the key later. Design the shard key carefully up front.

---

## Q9. (Advanced) What is read concern and write concern? How do they affect consistency in a replica set?

**Answer:**  
**Write concern**: how many members must acknowledge a write (e.g. w: 1, w: 'majority'). **Read concern**: what visibility of data (e.g. local, majority, linearizable). **majority** read concern reads data acknowledged by majority; with **majority** write concern you get read-your-writes. **linearizable** for strict linearizability on read. In driver: `readConcern: 'majority'`, `writeConcern: { w: 'majority' }`.

---

## Q10. (Advanced) Compare MongoDB replica set + sharding to Cassandra’s replication and partitioning. What is conceptually similar and different?

**Answer:**  
**Similar**: both replicate data for HA; both partition (shard) by a key for scale. **MongoDB**: primary accepts writes; replica set + optional sharding; shard key chosen by you; config servers + mongos. **Cassandra**: no single primary; partition key + replication factor; every node can accept writes; consistent hashing. MongoDB has a primary for strong consistency per shard; Cassandra is peer-to-peer and tunable consistency. Both scale horizontally; MongoDB’s model is “replica set per shard”; Cassandra is “ring with replicas per partition.”
