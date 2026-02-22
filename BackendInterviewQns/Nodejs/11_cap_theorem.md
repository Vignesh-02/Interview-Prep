# 11. CAP Theorem & Distributed Tradeoffs

## Topic Introduction

The **CAP theorem** states that a distributed system can guarantee at most **two of three** properties during a network partition: **Consistency** (all nodes see the same data), **Availability** (every request gets a response), and **Partition tolerance** (system works despite network splits).

```
         Consistency
          /       \
         /    CP    \
        /   systems  \
       /              \
Partition ──────────── Availability
  Tolerance    AP
              systems
```

Since network partitions are **inevitable** in distributed systems, the real choice is between **CP** (consistent but may reject requests) and **AP** (available but may return stale data). Understanding this tradeoff is fundamental for designing any distributed backend.

**Real-world**: No system is purely CP or AP. Systems make different tradeoffs at different layers. PostgreSQL is CP for writes. A CDN is AP. Your system combines both.

---

## Q1. (Beginner) What is the CAP theorem? Explain in simple terms.

**Scenario**: You have two database servers. The network cable between them is cut.

```
Server A ──✂── Server B

Client writes to Server A: balance = 100
Client reads from Server B: balance = ???

CP choice: Server B says "I can't answer, I might have stale data" (503 error)
AP choice: Server B says "balance = 80" (stale but responds)
```

**Answer**: CAP says you can't have all three in a partition. Since partitions happen, you choose: **Consistency** (reject requests if data might be stale) or **Availability** (respond with potentially stale data).

---

## Q2. (Beginner) Give examples of CP and AP systems.

**Answer**:

| System | Type | Behavior during partition |
|--------|------|------------------------|
| **PostgreSQL** (single node) | CP | Rejects writes if unable to confirm durability |
| **MongoDB** (with majority write concern) | CP | Rejects writes if can't reach majority |
| **etcd / ZooKeeper** | CP | Leader election, minority partition can't write |
| **Cassandra** | AP | Continues accepting reads/writes, reconciles later |
| **DynamoDB** | AP (configurable) | Eventual consistency by default, strong optional |
| **Redis Cluster** | AP | Responds from available nodes, may lose recent writes |
| **DNS** | AP | Returns cached/stale records |

```js
// CP example: PostgreSQL with synchronous replication
// Write waits for replica acknowledgment before returning success
const pool = new Pool({ /* synchronous_commit: 'on' */ });

// AP example: Cassandra read with eventual consistency
const query = 'SELECT * FROM users WHERE id = ?';
client.execute(query, [userId], { consistency: types.consistencies.one });
// Returns fast from nearest node, may be slightly stale
```

---

## Q3. (Beginner) What is eventual consistency? Show a real-world example.

**Scenario**: User updates their profile on Server A. Another user reads from Server B milliseconds later.

```js
// Write goes to primary
await primaryDb.query('UPDATE users SET name = $1 WHERE id = $2', ['Alice', 123]);

// Milliseconds later, read from replica might get OLD data
const user = await replicaDb.query('SELECT * FROM users WHERE id = $1', [123]);
// user.name might still be 'Alice_old' due to replication lag

// Eventually (ms to seconds later), replica catches up
// user.name = 'Alice' ← consistent
```

**Answer**: Eventual consistency means all replicas will **eventually** converge to the same data, but reads may be stale for a short window. This is the tradeoff for availability and performance (reading from any replica).

**Real-world examples**: Social media feed (seeing a post 2 seconds late is fine), DNS propagation (takes minutes), shopping cart (eventually syncs across devices).

---

## Q4. (Beginner) Why can't you just have all three (C, A, P)?

**Answer**: During a partition, a node must choose:
- **Respond with potentially stale data** (sacrificing consistency for availability)
- **Refuse to respond** (sacrificing availability for consistency)

You can't do both. The partition forces a binary choice.

```
Normal operation (no partition): You CAN have C + A + P
During partition: Must choose C or A

This is why CAP is about partition behavior, not normal operation.
```

In practice, most systems are **CA when healthy** and choose CP or AP **during failures**.

---

## Q5. (Beginner) How does replication relate to CAP?

**Answer**: Replication creates copies of data for availability and performance. But replication introduces the consistency-availability tradeoff:

| Replication Type | Consistency | Availability | Latency |
|-----------------|-------------|--------------|---------|
| **Synchronous** | Strong (CP) | Lower (waits for replicas) | Higher |
| **Asynchronous** | Eventual (AP) | Higher (doesn't wait) | Lower |
| **Semi-sync** | Compromise | Compromise | Moderate |

```js
// PostgreSQL synchronous replication (CP)
// Write doesn't return until replica confirms
// Slower, but no data loss on primary failure

// PostgreSQL async replication (AP)
// Write returns immediately, replica catches up later
// Faster, but may lose most recent writes on primary failure
```

---

## Q6. (Intermediate) How do you design a system that is CP for writes and AP for reads?

**Scenario**: E-commerce inventory system. Writes (stock changes) must be consistent. Reads (product pages) should be fast.

```js
// CP for writes — always go to primary with strong consistency
async function decrementStock(productId) {
  const client = await primaryPool.connect();
  await client.query('BEGIN');
  const result = await client.query(
    'UPDATE inventory SET quantity = quantity - 1 WHERE product_id = $1 AND quantity > 0 RETURNING quantity',
    [productId]
  );
  await client.query('COMMIT');
  client.release();
  return result.rows[0];
}

// AP for reads — read from replica + cache (stale is OK for browsing)
async function getProduct(productId) {
  // L1: Redis cache (stale for up to 30s)
  const cached = await redis.get(`product:${productId}`);
  if (cached) return JSON.parse(cached);

  // L2: Read replica (stale by replication lag, usually <1s)
  const product = await replicaPool.query('SELECT * FROM products WHERE id = $1', [productId]);
  await redis.set(`product:${productId}`, JSON.stringify(product.rows[0]), 'EX', 30);
  return product.rows[0];
}
```

**Answer**: Split your system: writes go to the primary (CP), reads go to replicas/cache (AP). Most web applications are read-heavy, so this gives you strong consistency where it matters (money, inventory) and high performance for browsing.

---

## Q7. (Intermediate) What is the PACELC theorem? How does it extend CAP?

**Answer**: PACELC extends CAP to cover normal operation (no partition):

```
If Partition → choose Availability or Consistency (CAP)
Else (normal operation) → choose Latency or Consistency

PA/EL: Available during partition, Low latency normally (Cassandra, DynamoDB)
PC/EC: Consistent during partition, Consistent normally (PostgreSQL, MongoDB)
PA/EC: Available during partition, Consistent normally (rare)
PC/EL: Consistent during partition, Low latency normally (rare)
```

**Why it matters**: CAP only applies during failures. PACELC tells you the tradeoff during normal operation too. DynamoDB is PA/EL — it's fast and available, but you accept eventual consistency even when the network is fine.

---

## Q8. (Intermediate) How do you handle the split-brain problem in distributed systems?

**Scenario**: Two database nodes both think they're the primary. Both accept writes → data divergence.

```
Node A ──✂── Node B
Both accept writes → "split brain"

Node A: user.name = "Alice"
Node B: user.name = "Bob"
Which is correct after partition heals?
```

**Answer**: Prevention strategies:
1. **Quorum**: Writes require majority (3/5 nodes must agree). Split brain is impossible.
2. **Fencing tokens**: Each leader gets a monotonically increasing token. Storage rejects writes from old leaders.
3. **External arbiter**: A third party (etcd, ZooKeeper) decides who is leader.

```js
// Using Redis Sentinel for leader election (prevents split brain)
const Redis = require('ioredis');
const redis = new Redis({
  sentinels: [
    { host: 'sentinel1', port: 26379 },
    { host: 'sentinel2', port: 26379 },
    { host: 'sentinel3', port: 26379 },
  ],
  name: 'mymaster', // Sentinel group name
});
// Sentinel ensures only ONE master at a time
```

---

## Q9. (Intermediate) How do you implement read-your-writes consistency?

**Scenario**: User updates their profile, immediately refreshes page, sees OLD data (from replica).

```js
// Problem: write → primary, read → replica (stale)
await primaryDb.query('UPDATE users SET name = $1 WHERE id = $2', ['Alice', userId]);
// Redirect to profile page → reads from replica → still shows old name!

// Solution 1: Read from primary after own writes
async function getUser(userId, req) {
  if (req.session.lastWrite && Date.now() - req.session.lastWrite < 5000) {
    return primaryDb.query('SELECT * FROM users WHERE id = $1', [userId]); // primary
  }
  return replicaDb.query('SELECT * FROM users WHERE id = $1', [userId]); // replica
}

// Solution 2: Return updated data from the write response
app.put('/users/me', async (req, res) => {
  const updated = await primaryDb.query(
    'UPDATE users SET name = $1 WHERE id = $2 RETURNING *', [req.body.name, req.user.id]
  );
  res.json(updated.rows[0]); // client has fresh data, no need to re-read
});

// Solution 3: Cache-through on write
app.put('/users/me', async (req, res) => {
  const updated = await primaryDb.query('UPDATE ... RETURNING *', [...]);
  await redis.set(`user:${req.user.id}`, JSON.stringify(updated.rows[0]), 'EX', 60);
  res.json(updated.rows[0]);
});
```

---

## Q10. (Intermediate) What is a quorum? How does it ensure consistency in distributed reads/writes?

**Answer**: A quorum is a **majority** of nodes. If you have N replicas:
- Write quorum: W nodes must acknowledge the write
- Read quorum: R nodes must agree on the read
- **If W + R > N**, reads always see the latest write

```
N = 3 replicas
W = 2 (write to 2 of 3)
R = 2 (read from 2 of 3)
W + R = 4 > 3 → strong consistency guaranteed

Write "balance=100" acknowledged by Node A and B
Read from Node B and C → at least one has the latest write
```

**Cassandra example**:
```js
// Strong consistency: QUORUM read + QUORUM write
const query = 'SELECT * FROM accounts WHERE id = ?';
client.execute(query, [accountId], { consistency: types.consistencies.quorum });
```

---

## Q11. (Intermediate) How do you design a shopping cart that survives network partitions?

**Answer**: Shopping cart should be **AP** — users must always be able to add items, even during partitions.

```js
// CRDTs (Conflict-free Replicated Data Types) for shopping cart
// Each server independently accepts adds/removes
// On partition heal, merge using "add wins" strategy

class ShoppingCart {
  constructor() {
    this.adds = new Map();    // { itemId → { qty, timestamp } }
    this.removes = new Map(); // { itemId → { timestamp } }
  }

  addItem(itemId, qty) {
    this.adds.set(itemId, { qty, timestamp: Date.now() });
  }

  removeItem(itemId) {
    this.removes.set(itemId, { timestamp: Date.now() });
  }

  // Merge two carts (from different replicas)
  merge(other) {
    for (const [id, val] of other.adds) {
      const existing = this.adds.get(id);
      if (!existing || val.timestamp > existing.timestamp) {
        this.adds.set(id, val);
      }
    }
    for (const [id, val] of other.removes) {
      const existing = this.removes.get(id);
      if (!existing || val.timestamp > existing.timestamp) {
        this.removes.set(id, val);
      }
    }
  }

  getItems() {
    const items = [];
    for (const [id, add] of this.adds) {
      const remove = this.removes.get(id);
      if (!remove || add.timestamp > remove.timestamp) {
        items.push({ itemId: id, qty: add.qty });
      }
    }
    return items;
  }
}
```

**Answer**: Use CRDTs for conflict-free merging. The cart is available on both sides of a partition and merges automatically when connectivity is restored.

---

## Q12. (Intermediate) When should you choose strong consistency vs eventual consistency?

**Answer**:

| Use Case | Consistency Level | Why |
|----------|------------------|-----|
| Bank transfers | **Strong** (CP) | Can't lose money |
| Inventory (last item) | **Strong** (CP) | Can't oversell |
| User profile updates | **Eventual** (AP) | Stale name for 1s is OK |
| Social media feed | **Eventual** (AP) | Seeing post 2s late is fine |
| Session data | **Depends** | Strong for auth, eventual for preferences |
| Analytics counters | **Eventual** (AP) | Approximate counts are acceptable |

**Rule of thumb**: Strong consistency for **money**, **inventory**, and **access control**. Eventual consistency for **reads**, **feeds**, **analytics**, and **non-critical state**.

---

## Q13. (Advanced) Production scenario: Your PostgreSQL primary fails. You have async replicas. What data might be lost and how do you handle it?

**Answer**: With async replication, the replica may be behind the primary by some transactions.

```
Primary fails at transaction T=1000
Replica has committed up to T=997
Transactions 998, 999, 1000 are LOST
```

**Mitigation strategies**:
```js
// 1. Use synchronous replication for critical data (CP)
// PostgreSQL: synchronous_standby_names = 'replica1'
// Trade: higher latency for zero data loss

// 2. Log all writes to a WAL archive (can replay)
// If primary dies, replay WAL on new primary

// 3. Application-level recovery
// After failover, check for inconsistencies:
async function reconcileAfterFailover() {
  const recentOrders = await db.query(
    "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '1 minute'"
  );
  for (const order of recentOrders.rows) {
    // Check if payment was captured but order missing
    const payment = await paymentService.getByOrderId(order.id);
    if (payment && !order.payment_confirmed) {
      await db.query('UPDATE orders SET payment_confirmed = true WHERE id = $1', [order.id]);
    }
  }
}

// 4. Use the Outbox Pattern — events in same transaction as data
// If data is lost, the event is also lost (consistent)
// If data committed, event exists and can be replayed
```

---

## Q14. (Advanced) How do you implement a distributed lock that respects CAP tradeoffs?

```js
// Redis distributed lock (AP-leaning — may have race conditions)
async function acquireLock(key, ttlMs = 5000) {
  const lockId = crypto.randomUUID();
  const acquired = await redis.set(`lock:${key}`, lockId, 'NX', 'PX', ttlMs);
  return acquired ? lockId : null;
}

async function releaseLock(key, lockId) {
  // Lua script to atomically check-and-delete (only release if we own it)
  const script = `
    if redis.call('get', KEYS[1]) == ARGV[1] then
      return redis.call('del', KEYS[1])
    end
    return 0
  `;
  return redis.eval(script, 1, `lock:${key}`, lockId);
}

// Usage
const lockId = await acquireLock('user:123:checkout');
if (!lockId) return res.status(409).json({ error: 'Another checkout in progress' });
try {
  await processCheckout(userId);
} finally {
  await releaseLock('user:123:checkout', lockId);
}
```

**CAP tradeoff**: Redis locks are **AP** — if Redis is partitioned, two processes might both acquire the lock. For strict CP locking, use **Redlock** (consensus across Redis nodes) or **etcd**/**ZooKeeper** (true distributed consensus).

---

## Q15. (Advanced) Explain the differences between Raft, Paxos, and gossip protocols.

**Answer**:

| Protocol | Type | Use case | Systems |
|----------|------|----------|---------|
| **Raft** | Consensus (CP) | Leader election, log replication | etcd, CockroachDB |
| **Paxos** | Consensus (CP) | Agreeing on a value | Google Spanner, Chubby |
| **Gossip** | Dissemination (AP) | Membership, failure detection | Cassandra, DynamoDB |

```
Raft/Paxos: Agree on ONE value across nodes (expensive but consistent)
  Node A: "leader is X" → Node B: "I agree" → Node C: "I agree" → committed

Gossip: Spread information eventually (cheap but eventually consistent)
  Node A tells Node B → Node B tells Node C → ... → all nodes know (eventually)
```

**For backend engineers**: You rarely implement these directly. You choose **systems** that use them (etcd for config, Cassandra for data). Understanding the tradeoffs helps you pick the right tool.

---

## Q16. (Advanced) How do you design a multi-region backend with CAP tradeoffs?

```
US-East           EU-West           AP-Southeast
  │                 │                    │
  Primary       Read Replica       Read Replica
  (writes)      (reads)            (reads)
  │                 │                    │
  └─── Async replication ───────────────┘
```

```js
// Write routing: always to primary region
function getWritePool() {
  return new Pool({ host: 'us-east-primary.db.internal' });
}

// Read routing: nearest region
function getReadPool(userRegion) {
  const replicas = {
    'us-east': 'us-east-replica.db.internal',
    'eu-west': 'eu-west-replica.db.internal',
    'ap-southeast': 'ap-southeast-replica.db.internal',
  };
  return new Pool({ host: replicas[userRegion] || replicas['us-east'] });
}
```

**Tradeoffs**:
- **Single-region writes**: Simple CP, but high latency for non-local writes
- **Multi-region writes**: Low latency everywhere, but consistency hell (conflicts)
- **Hybrid**: Critical writes to primary, non-critical writes local with eventual sync

---

## Q17. (Advanced) What is CockroachDB/Spanner and how do they achieve "CP + A"?

**Answer**: CockroachDB and Google Spanner use **Raft consensus per range** of data, giving strong consistency while maintaining high availability (not during partitions, but with fast failover).

```
Unlike traditional CP systems that become unavailable during partitions:
- Data is split into ranges, each replicated across 3+ nodes
- Each range has its own Raft consensus group
- If one node fails, remaining nodes elect a new leader (seconds)
- Writes are committed only when majority confirms

Result: Strong consistency (linearizable) + High availability (but not during majority partition)
```

**From Node.js**, CockroachDB looks like PostgreSQL (wire-compatible):
```js
const pool = new Pool({
  connectionString: 'postgresql://root@cockroachdb:26257/mydb',
});
// Standard SQL, but distributed + consistent
```

---

## Q18. (Advanced) How do you test for partition tolerance in your backend?

```js
// Chaos testing: simulate network partitions
// Use tools like Toxiproxy to inject network faults

// Toxiproxy configuration (HTTP API)
// POST /proxies
// { "name": "postgres", "listen": ":5433", "upstream": "postgres:5432" }

// Test: partition the database
// POST /proxies/postgres/toxics
// { "type": "timeout", "attributes": { "timeout": 0 } }

// Now test your app's behavior:
describe('Partition tolerance', () => {
  it('returns cached data when DB is unreachable', async () => {
    await toxiproxy.createToxic('postgres', 'timeout', { timeout: 0 });
    const res = await request(app).get('/products/1');
    expect(res.status).toBe(200); // should serve from cache
    expect(res.body._stale).toBe(true); // flagged as stale
    await toxiproxy.removeToxic('postgres', 'timeout');
  });

  it('rejects writes when DB is partitioned', async () => {
    await toxiproxy.createToxic('postgres', 'timeout', { timeout: 0 });
    const res = await request(app).post('/orders').send(orderData);
    expect(res.status).toBe(503); // CP behavior for writes
    await toxiproxy.removeToxic('postgres', 'timeout');
  });
});
```

---

## Q19. (Advanced) How do you implement conflict resolution for concurrent writes in an AP system?

```js
// Last-Write-Wins (LWW) — simplest conflict resolution
async function resolveConflict(key, value1, value2) {
  return value1.timestamp > value2.timestamp ? value1 : value2;
}

// Application-level conflict resolution — merge
function mergeDocuments(doc1, doc2) {
  return {
    ...doc1,
    ...doc2,
    // For arrays, merge and deduplicate
    tags: [...new Set([...doc1.tags, ...doc2.tags])],
    // For counters, take the max
    viewCount: Math.max(doc1.viewCount, doc2.viewCount),
    // Keep the latest modification
    updatedAt: doc1.updatedAt > doc2.updatedAt ? doc1.updatedAt : doc2.updatedAt,
  };
}

// CRDTs — mathematically guaranteed conflict-free merging
// G-Counter (grow-only counter across nodes)
class GCounter {
  constructor(nodeId) { this.nodeId = nodeId; this.counts = {}; }
  increment() { this.counts[this.nodeId] = (this.counts[this.nodeId] || 0) + 1; }
  value() { return Object.values(this.counts).reduce((a, b) => a + b, 0); }
  merge(other) {
    for (const [node, count] of Object.entries(other.counts)) {
      this.counts[node] = Math.max(this.counts[node] || 0, count);
    }
  }
}
```

---

## Q20. (Advanced) Senior red flags when making CAP tradeoff decisions.

**Answer**:

1. **Treating all data the same** — payments need CP, feeds need AP
2. **Ignoring replication lag** — reads immediately after writes return stale data
3. **Using eventual consistency for financial data** — double-spending risk
4. **No fallback when primary is down** — service is unavailable for reads and writes
5. **Distributed transactions across services** — 2PC is slow and fragile
6. **No monitoring of replication lag** — unaware how stale reads are
7. **Assuming Redis is consistent** — Redis replication is async by default
8. **No chaos testing** — never tested partition behavior
9. **Over-engineering consistency** — making everything strongly consistent when eventual is fine (wastes performance)

**Senior interview answer**: "I choose consistency levels per operation: strong consistency (CP) for money and inventory writes, eventual consistency (AP) for reads and non-critical data. I implement read-your-writes for user-facing flows, monitor replication lag, and test partition behavior with chaos engineering."
