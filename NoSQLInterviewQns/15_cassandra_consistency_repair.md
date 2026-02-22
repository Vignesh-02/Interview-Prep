# 15. Cassandra Consistency, Repair & Tunables

## Q1. (Beginner) What does consistency level (CL) control in Cassandra?

**Answer:**  
**Consistency level** controls how many replicas must **respond** for a read or **acknowledge** for a write. Examples: ONE, TWO, THREE, QUORUM, ALL, LOCAL_ONE, LOCAL_QUORUM. Higher CL = stronger consistency and more latency; lower = faster but possible staleness. Write CL and read CL together determine whether you see your own writes (e.g. QUORUM write + QUORUM read).

---

## Q2. (Beginner) What is QUORUM? How do you choose CL for strong consistency?

**Answer:**  
**QUORUM** = majority of replicas (e.g. 2 of 3). For **strong consistency**: use **QUORUM** (or higher) for both read and write. Then read always sees the latest write (assuming replication factor allows). Rule of thumb: **write CL + read CL &gt; replication factor** (e.g. W=QUORUM, R=QUORUM with RF=3) guarantees read-your-writes for that key.

---

## Q3. (Intermediate) What is read repair? What is hinted handoff?

**Answer:**  
**Read repair**: when a read at CL &lt; ALL contacts multiple replicas and gets different data, Cassandra compares and **repairs** the stale replica(s) in the background (or blocking, depending on CL). **Hinted handoff**: when a replica is down, the coordinator stores a “hint” and later replays it to the down replica when it’s back. Hinted handoff is not permanent (time-limited); run **repair** for full consistency.

---

## Q4. (Intermediate) What is anti-entropy repair (e.g. nodetool repair)? Why run it?

**Answer:**  
**Anti-entropy repair** (e.g. `nodetool repair`) compares data across replicas (e.g. Merkle trees) and syncs differences. It fixes divergence from hints expiry, failures, or bugs. Run **regularly** (e.g. weekly per node or incremental repair) so replicas stay in sync. Critical for consistency when using lower CL or after outages.

---

## Q5. (Intermediate) What is a coordinator node in Cassandra? What does it do for a write?

**Answer:**  
The **coordinator** is the node the client talks to. For a write: coordinator hashes the partition key to get replicas, sends the write to **replica nodes** (based on replication strategy), waits for **CL** acks, then responds to the client. The coordinator does not necessarily own the partition; it routes the request.

---

## Q6. (Advanced) How does the backend specify consistency level per query (e.g. in Node.js driver)?

**Answer:**  
Pass **consistency** in the options:

```javascript
await client.execute(
  'SELECT * FROM events WHERE user_id = ?',
  [userId],
  { prepare: true, consistency: cassandra.types.consistencies.quorum }
);
// For writes:
await client.execute(
  'INSERT INTO events (...) VALUES (...)',
  params,
  { prepare: true, consistency: cassandra.types.consistencies.one }
);
```
Use higher CL for critical reads/writes; ONE or LOCAL_ONE for low-latency, non-critical paths.

---

## Q7. (Advanced) What is LOCAL_QUORUM vs QUORUM? When would you use LOCAL_QUORUM in a multi-DC setup?

**Answer:**  
**QUORUM** (global): majority across **all** datacenters — strong consistency, higher latency (cross-DC). **LOCAL_QUORUM**: majority within the **local** DC only — faster, but cross-DC reads might be stale. Use **LOCAL_QUORUM** when you want low latency and can accept that reads in DC2 might not see the latest write from DC1 until replication catches up. Use QUORUM when you need cross-DC consistency.

---

## Q8. (Advanced) Production scenario: Your app writes to Cassandra in DC1 and reads from DC2 (for geo latency). What consistency levels and replication would you use, and what trade-off do you accept?

**Answer:**  
**Replication**: use **NetworkTopologyStrategy** with RF ≥ 1 per DC (e.g. 2 per DC). **Write**: LOCAL_QUORUM in DC1 (fast). **Read in DC2**: LOCAL_ONE or ONE in DC2 — low latency but **eventual consistency**; may not see latest DC1 writes immediately. **Trade-off**: latency vs freshness. If you need read-your-writes across DC, use QUORUM for read (slower) or route the user’s reads to the DC where they wrote (e.g. sticky to DC).

---

## Q9. (Advanced) What is replication strategy? What is SimpleStrategy vs NetworkTopologyStrategy?

**Answer:**  
**Replication strategy** decides which nodes get replicas. **SimpleStrategy**: single DC; you specify RF (e.g. 3); replicas placed in ring order. **NetworkTopologyStrategy**: multi-DC; you specify RF per DC (e.g. DC1: 2, DC2: 2). Use **NetworkTopologyStrategy** in production (and for multi-DC); SimpleStrategy is for single-DC or dev only.

---

## Q10. (Advanced) How do you monitor replication lag or consistency issues in Cassandra from an ops perspective?

**Answer:**  
**nodetool**: `nodetool status` (node state), `nodetool describecluster` (schema, etc.). **Repair**: run repair and monitor duration; **nodetool compactionstats**. **Metrics**: expose and alert on pending compactions, read/write latencies, timeouts, read repair activity. **Application**: periodically read at QUORUM and compare with ONE to detect staleness; run repair and use QUORUM for critical paths.
