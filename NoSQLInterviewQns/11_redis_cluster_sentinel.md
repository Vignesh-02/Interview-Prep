# 11. Redis Cluster, Sentinel & High Availability

## Q1. (Beginner) What is Redis replication? What are master and replica?

**Answer:**  
**Replication**: one **master** and one or more **replicas**. Master handles writes; data is asynchronously replicated to replicas. Replicas can serve reads (scale read capacity). If the master fails, a replica can be promoted to master (manually or via Sentinel/Cluster) for high availability.

---

## Q2. (Beginner) What is Redis Sentinel? What problem does it solve?

**Answer:**  
**Sentinel** provides **automatic failover**: it monitors the master and replicas; if the master is down, Sentinels elect a replica as the new master and reconfigure clients. It also notifies clients of the current master. So you get **HA** (high availability) without manual promotion. Sentinel does **not** shard data; it’s for single-master replication with failover.

---

## Q3. (Intermediate) What is Redis Cluster? How does it differ from Sentinel?

**Answer:**  
**Redis Cluster** shards data across **multiple masters** (each with optional replicas). Data is partitioned by hash slots (16384 slots); each key is assigned to a slot and thus to a node. **Sentinel**: one logical dataset, one master + replicas, automatic failover. **Cluster**: multiple masters, horizontal scaling, data distributed; each shard can have its own replicas and failover. Use Sentinel for single-node dataset with HA; use Cluster for larger data/throughput.

---

## Q4. (Intermediate) How does Redis Cluster assign keys to nodes? What are hash slots?

**Answer:**  
Cluster has **16384 hash slots**. Key assignment: **CRC16(key) mod 16384** → slot. Each node is responsible for a subset of slots (e.g. node 1: 0–5460, node 2: 5461–10922, node 3: 10923–16383). So the key determines the slot and thus the node. **Hash tags**: `{user:123}:profile` — only `user:123` is hashed so related keys land on the same node.

---

## Q5. (Intermediate) What is a hash tag in Redis Cluster? Why would you use it?

**Answer:**  
**Hash tag**: part of the key in curly braces, e.g. `{user:123}:profile`, `{user:123}:settings`. Only the part inside `{}` is used for slot calculation. So multiple keys with the same tag go to the **same node**, enabling **MGET**, **MULTI/EXEC**, and Lua scripts that touch multiple keys. Use when you need to run multi-key operations on the same node.

---

## Q6. (Advanced) How does a Redis client (e.g. ioredis in Node) work with Cluster? What happens on MOVED/ASK?

**Answer:**  
Client connects to one or more nodes and gets the **slot map**. It sends commands to the node that owns the key’s slot. If the key was moved (**MOVED**), the client updates the slot map and retries. **ASK** means the key is temporarily on another node (during migration); client sends ASKING and then the command to that node. A good client (e.g. ioredis with `new Cluster([...])`) handles MOVED/ASK and maintains the slot map.

---

## Q7. (Advanced) Production scenario: Your Node.js app uses a single Redis instance. You need HA and read scaling. Describe moving to Sentinel and what code changes are needed.

**Answer:**  
**Setup**: Deploy Redis master + 2 replicas + 3 Sentinel nodes. **Code**: Replace single connection with a Sentinel-aware client. With **ioredis**: connect to Sentinels and use the master name:

```javascript
const Redis = require('ioredis');
const redis = new Redis({
  sentinels: [
    { host: 'sentinel1', port: 26379 },
    { host: 'sentinel2', port: 26379 },
    { host: 'sentinel3', port: 26379 }
  ],
  name: 'mymaster'
});
```
Client discovers current master from Sentinels and reconnects on failover. No change to GET/SET usage; only connection config changes. For read scaling, use **replicas** option (if supported) to send read commands to replicas.

---

## Q8. (Advanced) What are the limitations of Redis Cluster regarding multi-key operations and Lua?

**Answer:**  
**Multi-key commands** (MGET, MSET, etc.) and **MULTI/EXEC** with multiple keys only work if all keys are in the **same slot** (use hash tags). **Lua scripts**: all keys in the script must be in the same slot (same node); use hash tags. Otherwise Redis returns **CROSSSLOT** error. Design keys with hash tags when you need multi-key ops in Cluster.

---

## Q9. (Advanced) How do you achieve high availability for Redis in AWS (ElastiCache)? What about multi-AZ?

**Answer:**  
**ElastiCache Redis**: Enable **Multi-AZ** with automatic failover — replica in another AZ; on primary failure, replica is promoted. **Cluster mode**: use replication group with multiple node groups (shards), each with a replica. Application connects to the **primary endpoint**; ElastiCache updates DNS on failover. Use **read replicas** for read scaling; primary endpoint for writes.

---

## Q10. (Advanced) Compare Redis Sentinel vs Redis Cluster for: (1) data size, (2) write throughput, (3) operational complexity, (4) multi-key operations.

**Answer:**  
(1) **Data size**: Sentinel = single node limit (memory); Cluster = horizontal scale. (2) **Write throughput**: Sentinel = single master; Cluster = multiple masters, higher aggregate write. (3) **Ops**: Sentinel simpler (one master, failover); Cluster has slot migration, rebalancing. (4) **Multi-key**: Sentinel = no restriction; Cluster = same slot (hash tags) for multi-key and Lua. Choose Sentinel for moderate data/throughput and simplicity; Cluster for scale.
