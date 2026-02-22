# 22. Distributed Systems Patterns

## Topic Introduction

Distributed systems run across multiple machines, communicating over a network. They offer **scalability** and **fault tolerance** but introduce challenges: network failures, partial failures, clock skew, and data consistency.

```
Single Server:                    Distributed System:
┌──────────┐                     ┌──────────┐   ┌──────────┐
│ App + DB │                     │ App Node │←→│ App Node │
└──────────┘                     └────┬─────┘   └────┬─────┘
                                      │              │
                                 ┌────┴─────┐   ┌────┴─────┐
                                 │  DB Primary│←→│ DB Replica│
                                 └──────────┘   └──────────┘
```

As a senior backend engineer, you must understand: **CAP theorem**, **consensus algorithms**, **distributed locks**, **leader election**, **event sourcing**, **CRDTs**, and **idempotency** in distributed contexts.

**Go/Java tradeoff**: Java has the richest ecosystem for distributed systems (Zookeeper, Hazelcast, Akka). Go is used for infrastructure (etcd, Consul, Kubernetes itself). Node.js typically consumes distributed infrastructure (Redis, Kafka, PostgreSQL replication) rather than implementing it.

---

## Q1. (Beginner) What makes a system "distributed"? What problems does distribution introduce?

**Answer**:

A system is distributed when components run on multiple networked machines and coordinate to appear as one system.

**Problems distribution introduces** (the "fallacies of distributed computing"):
1. **Network is reliable** — NO, packets drop, connections timeout
2. **Latency is zero** — NO, network calls are 1000x slower than local calls
3. **Bandwidth is infinite** — NO, serialization/deserialization costs matter
4. **Network is secure** — NO, messages can be intercepted
5. **Topology doesn't change** — NO, servers come and go
6. **There is one administrator** — NO, different teams manage different parts
7. **Transport cost is zero** — NO, serialization and network hops have cost
8. **Network is homogeneous** — NO, different protocols, versions, languages

```js
// Local function call: ~1 nanosecond, always succeeds (or crashes)
const user = getUserById(42);

// Distributed call: ~1-100 milliseconds, might fail in many ways:
// - Network timeout
// - Service is down
// - Partial response
// - Response lost (did the operation succeed?)
// - Response is from a stale replica
try {
  const user = await fetch('http://user-service/users/42', {
    signal: AbortSignal.timeout(5000),
  }).then(r => r.json());
} catch (err) {
  // Did the request reach the server? Unknown!
}
```

---

## Q2. (Beginner) What is the CAP theorem? Can you explain it with examples?

**Answer**:

CAP states that a distributed data store can only guarantee **two of three** properties during a network partition:

- **C (Consistency)**: Every read receives the most recent write
- **A (Availability)**: Every request receives a response (no errors)
- **P (Partition tolerance)**: System works despite network failures between nodes

```
Network partition occurs:
┌──────────┐     ✕ broken ✕     ┌──────────┐
│  Node A  │ ──── ✕✕✕✕✕ ──── │  Node B  │
│  Data: X │                     │  Data: X │
└──────────┘                     └──────────┘

Client writes Y to Node A:

CP choice (Consistency + Partition tolerance):
  Node A rejects write until it can sync with Node B
  → Consistent but UNAVAILABLE during partition

AP choice (Availability + Partition tolerance):
  Node A accepts write, Node B still has old value
  → Available but INCONSISTENT during partition
```

| System | Choice | Behavior during partition |
|---|---|---|
| PostgreSQL (single) | CA | No partition tolerance (single node) |
| PostgreSQL (sync replica) | CP | Rejects writes if replica is unreachable |
| MongoDB (default) | CP | Writes only to primary |
| Cassandra | AP | Accepts writes to any node, resolves later |
| DynamoDB | AP | Eventual consistency by default |
| Redis Cluster | CP | Rejects if majority nodes unavailable |

---

## Q3. (Beginner) What is eventual consistency? How does it differ from strong consistency?

```js
// Strong consistency: read always returns latest write
await db.query('UPDATE users SET name = $1 WHERE id = $2', ['Jane', userId]);
const user = await db.query('SELECT name FROM users WHERE id = $1', [userId]);
// user.name is ALWAYS 'Jane'

// Eventual consistency: read MIGHT return stale data
await redis.set('user:42:name', 'Jane');
const name = await redisReplica.get('user:42:name');
// name MIGHT be 'John' (old value) for a brief period
// Eventually (milliseconds to seconds) it will be 'Jane'
```

| | **Strong consistency** | **Eventual consistency** |
|---|---|---|
| Read guarantee | Always latest value | May be stale |
| Write latency | Higher (must sync) | Lower (async replication) |
| Availability | Lower during failures | Higher during failures |
| Use case | Banking, inventory | Social media feeds, analytics |
| Example | PostgreSQL primary | DynamoDB, Cassandra, Redis replicas |

---

## Q4. (Beginner) What are idempotent operations and why do they matter in distributed systems?

```js
// In distributed systems, messages can be delivered more than once
// (at-least-once delivery is the practical guarantee)

// NON-IDEMPOTENT: calling twice produces different results
app.post('/transfer', async (req, res) => {
  await db.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [100, req.body.from]);
  await db.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [100, req.body.to]);
  // If client retries, money is transferred TWICE!
});

// IDEMPOTENT: calling twice produces the same result
app.post('/transfer', async (req, res) => {
  const { idempotencyKey } = req.body;

  // Check if already processed
  const existing = await db.query('SELECT * FROM transfers WHERE idempotency_key = $1', [idempotencyKey]);
  if (existing.rows.length > 0) {
    return res.json(existing.rows[0]); // return cached result
  }

  // Process and store result atomically
  const result = await db.transaction(async (trx) => {
    const transfer = await trx('transfers').insert({
      idempotency_key: idempotencyKey,
      from_account: req.body.from,
      to_account: req.body.to,
      amount: 100,
    }).returning('*');

    await trx.raw('UPDATE accounts SET balance = balance - ? WHERE id = ?', [100, req.body.from]);
    await trx.raw('UPDATE accounts SET balance = balance + ? WHERE id = ?', [100, req.body.to]);
    return transfer[0];
  });

  res.json(result);
});
```

**Answer**: In distributed systems, networks are unreliable. Clients retry. Queues redeliver. Idempotency ensures that processing the same operation multiple times has the same effect as processing it once. **Every write operation in a distributed system should be idempotent.**

---

## Q5. (Beginner) What is a message queue and why is it essential for distributed systems?

```js
// Direct calls: tight coupling, cascading failures
// Service A → Service B → Service C (if B is down, A fails too)

// Message queue: decoupling, resilience
// Service A → Queue → Service B (if B is down, messages wait)

const { Kafka } = require('kafkajs');
const kafka = new Kafka({ brokers: ['kafka:9092'] });

// Producer: fire and forget (async, decoupled)
const producer = kafka.producer();
await producer.send({
  topic: 'order-events',
  messages: [{ key: orderId, value: JSON.stringify({ type: 'ORDER_CREATED', data: order }) }],
});
// Producer doesn't wait for consumer — returns immediately

// Consumer: processes at its own pace
const consumer = kafka.consumer({ groupId: 'email-service' });
await consumer.run({
  eachMessage: async ({ message }) => {
    const event = JSON.parse(message.value);
    if (event.type === 'ORDER_CREATED') {
      await sendConfirmationEmail(event.data); // can retry independently
    }
  },
});
```

**Answer**: Message queues provide: (1) Decoupling (services don't need to know about each other), (2) Buffering (handle traffic spikes), (3) Resilience (messages survive consumer failures), (4) Ordering (within partitions).

---

## Q6. (Intermediate) How do distributed locks work? Implement one with Redis.

**Scenario**: Two servers process payments concurrently. Both read the same account balance, both deduct — double-spending.

```js
const Redis = require('ioredis');
const redis = new Redis();

class DistributedLock {
  constructor(redis, key, ttlMs = 10000) {
    this.redis = redis;
    this.key = `lock:${key}`;
    this.ttlMs = ttlMs;
    this.token = crypto.randomUUID(); // unique per lock holder
  }

  async acquire(retries = 10, retryDelay = 100) {
    for (let i = 0; i < retries; i++) {
      // SET NX (only if not exists) with expiration
      const result = await this.redis.set(this.key, this.token, 'PX', this.ttlMs, 'NX');
      if (result === 'OK') return true;
      await new Promise(r => setTimeout(r, retryDelay + Math.random() * retryDelay));
    }
    return false;
  }

  async release() {
    // Lua script: atomic check-and-delete (prevent releasing someone else's lock)
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
      else
        return 0
      end
    `;
    return this.redis.eval(script, 1, this.key, this.token);
  }
}

// Usage
async function processPayment(orderId, amount) {
  const lock = new DistributedLock(redis, `payment:${orderId}`, 30000);

  if (!(await lock.acquire())) {
    throw new Error('Could not acquire lock — payment already being processed');
  }

  try {
    const balance = await db.query('SELECT balance FROM accounts WHERE id = $1 FOR UPDATE', [accountId]);
    if (balance < amount) throw new Error('Insufficient funds');
    await db.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, accountId]);
    return { success: true };
  } finally {
    await lock.release();
  }
}
```

**Important**: Redis distributed locks (Redlock) are not 100% safe due to clock skew and GC pauses. For critical operations (financial), use database-level locks (`SELECT ... FOR UPDATE`) or a proper consensus system (Zookeeper, etcd).

---

## Q7. (Intermediate) What is leader election and when do you need it?

**Scenario**: You have 3 instances of a cron job service. The daily report should run on exactly ONE instance.

```js
// Leader election with Redis
class LeaderElection {
  constructor(redis, name, ttlMs = 30000) {
    this.redis = redis;
    this.key = `leader:${name}`;
    this.instanceId = `${os.hostname()}-${process.pid}`;
    this.ttlMs = ttlMs;
    this.isLeader = false;
  }

  async start() {
    // Try to become leader
    await this.tryBecomeLeader();
    // Renew leadership periodically
    this.interval = setInterval(() => this.tryBecomeLeader(), this.ttlMs / 3);
  }

  async tryBecomeLeader() {
    const result = await this.redis.set(this.key, this.instanceId, 'PX', this.ttlMs, 'NX');
    if (result === 'OK') {
      this.isLeader = true;
      console.log(`${this.instanceId} became leader`);
      return;
    }

    // Check if we're still the leader (renew TTL)
    const currentLeader = await this.redis.get(this.key);
    if (currentLeader === this.instanceId) {
      await this.redis.pexpire(this.key, this.ttlMs);
      this.isLeader = true;
    } else {
      this.isLeader = false;
    }
  }

  async stop() {
    clearInterval(this.interval);
    if (this.isLeader) {
      await this.redis.del(this.key);
    }
  }
}

// Usage: only the leader runs the cron job
const election = new LeaderElection(redis, 'report-generator');
await election.start();

cron.schedule('0 0 * * *', async () => {
  if (!election.isLeader) return; // skip on non-leader instances
  await generateDailyReport();
});
```

---

## Q8. (Intermediate) What is the Outbox pattern and why is it needed?

**Scenario**: Save an order to the database AND publish an event. What if the app crashes between the two?

```js
// PROBLEM: not atomic
await db.query('INSERT INTO orders ...'); // ✅ succeeds
await kafka.publish('order-created', ...); // ❌ app crashes here — DB has order but no event

// SOLUTION: Outbox pattern
await db.transaction(async (trx) => {
  // Both in the SAME transaction = atomic
  await trx('orders').insert(orderData);
  await trx('outbox').insert({
    id: uuid(),
    aggregate_type: 'Order',
    event_type: 'ORDER_CREATED',
    payload: JSON.stringify(orderData),
    created_at: new Date(),
  });
});

// Separate process reads outbox and publishes to Kafka
async function processOutbox() {
  const events = await db('outbox')
    .where({ published_at: null })
    .orderBy('created_at')
    .limit(100);

  for (const event of events) {
    await kafka.producer.send({
      topic: `${event.aggregate_type.toLowerCase()}-events`,
      messages: [{ key: event.id, value: event.payload }],
    });
    await db('outbox').where({ id: event.id }).update({ published_at: new Date() });
  }
}

// Poll every second
setInterval(processOutbox, 1000);
```

**Answer**: The Outbox pattern guarantees at-least-once delivery. Both the business data and the event are written to the same database in one transaction. A background process publishes events from the outbox table. For enterprise: use Debezium (CDC) which reads the DB transaction log directly.

---

## Q9. (Intermediate) How do you handle clock skew in distributed systems?

```js
// Problem: each server has a slightly different clock
// Server A: 10:00:00.000
// Server B: 10:00:00.150  (150ms ahead)
// Server C: 09:59:59.800  (200ms behind)

// Using timestamps for ordering is UNRELIABLE

// Solution 1: Logical clocks (Lamport timestamps)
class LamportClock {
  constructor() { this.counter = 0; }
  increment() { this.counter++; return this.counter; }
  update(receivedTimestamp) {
    this.counter = Math.max(this.counter, receivedTimestamp) + 1;
    return this.counter;
  }
}

// Solution 2: Vector clocks (tracks causality per node)
class VectorClock {
  constructor(nodeId) {
    this.nodeId = nodeId;
    this.clock = {};
  }
  increment() {
    this.clock[this.nodeId] = (this.clock[this.nodeId] || 0) + 1;
    return { ...this.clock };
  }
  merge(otherClock) {
    for (const [node, time] of Object.entries(otherClock)) {
      this.clock[node] = Math.max(this.clock[node] || 0, time);
    }
    this.increment();
  }
  happensBefore(other) {
    return Object.entries(this.clock).every(([node, time]) => time <= (other[node] || 0));
  }
}

// Solution 3: NTP synchronization + hybrid logical clocks
// In practice: use NTP to keep clocks within ~10ms, and use logical ordering for exact ordering
```

---

## Q10. (Intermediate) What is a quorum and how is it used in distributed databases?

**Answer**:

A quorum is the minimum number of nodes that must agree for an operation to be considered successful.

```
Cluster of 5 nodes: N=5
Write quorum: W=3 (majority must confirm write)
Read quorum:  R=3 (majority must confirm read)

Rule: W + R > N guarantees strong consistency
  3 + 3 = 6 > 5 ✓ (at least one node has latest write)

Write to node 1,2,3 (W=3) ✓
Read from node 3,4,5 (R=3) → node 3 has latest data ✓
```

```js
// Simulating quorum writes in application code
async function quorumWrite(key, value, nodes, quorumSize) {
  const results = await Promise.allSettled(
    nodes.map(node => node.write(key, value))
  );
  const successes = results.filter(r => r.status === 'fulfilled').length;

  if (successes >= quorumSize) {
    return { success: true, acks: successes };
  }
  throw new Error(`Quorum not met: ${successes}/${quorumSize} nodes acknowledged`);
}

// Usage: write to majority of 5 Redis nodes
await quorumWrite('session:abc', sessionData, redisNodes, 3);
```

| Config | W | R | Consistency | Availability |
|---|---|---|---|---|
| Strong consistency | N/2+1 | N/2+1 | Strong | Lower |
| Write-heavy | N | 1 | Strong | Lowest for writes |
| Read-heavy | 1 | N | Strong | Lowest for reads |
| Eventual consistency | 1 | 1 | Eventual | Highest |

---

## Q11. (Intermediate) What is the Saga pattern for distributed transactions?

**Answer**: See Q6 in file 18 (Microservices) for a detailed implementation. Key summary:

```
Traditional Transaction:          Saga (Distributed):
BEGIN                             Step 1: Reserve inventory
  reserve inventory               Step 2: Charge payment
  charge payment                  Step 3: Create order
  create order                    (if step 2 fails → compensate step 1)
COMMIT or ROLLBACK               Each step has a compensating action
```

- **Choreography**: Each service publishes events, others react
- **Orchestration**: Central coordinator manages the flow
- Compensating transactions instead of rollback

---

## Q12. (Intermediate) What is event sourcing? How does it differ from traditional CRUD?

```js
// Traditional CRUD: store current state
// UPDATE orders SET status = 'shipped' WHERE id = 'o1';
// Previous state is LOST

// Event sourcing: store events, derive state
const eventStore = [
  { type: 'ORDER_CREATED', data: { id: 'o1', items: [...], total: 100 }, timestamp: '...' },
  { type: 'PAYMENT_RECEIVED', data: { orderId: 'o1', amount: 100 }, timestamp: '...' },
  { type: 'ORDER_SHIPPED', data: { orderId: 'o1', trackingNumber: 'TR123' }, timestamp: '...' },
];

// Rebuild current state by replaying events
function buildOrderState(events) {
  return events.reduce((state, event) => {
    switch (event.type) {
      case 'ORDER_CREATED': return { ...event.data, status: 'created' };
      case 'PAYMENT_RECEIVED': return { ...state, status: 'paid', paidAt: event.timestamp };
      case 'ORDER_SHIPPED': return { ...state, status: 'shipped', trackingNumber: event.data.trackingNumber };
      case 'ORDER_DELIVERED': return { ...state, status: 'delivered' };
      case 'ORDER_CANCELLED': return { ...state, status: 'cancelled' };
      default: return state;
    }
  }, {});
}

// Snapshots for performance (don't replay millions of events)
class EventSourcedOrder {
  constructor(id) { this.id = id; }

  async loadState() {
    // Try snapshot first
    const snapshot = await db('snapshots').where({ aggregate_id: this.id }).orderBy('version', 'desc').first();
    const fromVersion = snapshot ? snapshot.version : 0;
    const events = await db('events').where({ aggregate_id: this.id }).where('version', '>', fromVersion).orderBy('version');

    this.state = snapshot ? snapshot.data : {};
    for (const event of events) {
      this.state = this.apply(event);
    }
    this.version = events.length > 0 ? events[events.length - 1].version : fromVersion;
  }

  async saveSnapshot() {
    await db('snapshots').insert({ aggregate_id: this.id, version: this.version, data: this.state });
  }
}
```

**Answer**: Event sourcing stores every state change as an immutable event. Benefits: complete audit trail, time-travel debugging, easy to add new projections (read models). Tradeoffs: more complex, eventual consistency for read models, snapshots needed for performance.

---

## Q13. (Advanced) What are CRDTs and when would you use them?

**Answer**: CRDTs (Conflict-free Replicated Data Types) are data structures that can be replicated across nodes and merged without conflicts, guaranteeing eventual consistency.

```js
// G-Counter (Grow-only counter) — each node has its own counter
class GCounter {
  constructor(nodeId) {
    this.nodeId = nodeId;
    this.counts = {}; // nodeId → count
  }

  increment() {
    this.counts[this.nodeId] = (this.counts[this.nodeId] || 0) + 1;
  }

  value() {
    return Object.values(this.counts).reduce((sum, c) => sum + c, 0);
  }

  merge(other) {
    for (const [node, count] of Object.entries(other.counts)) {
      this.counts[node] = Math.max(this.counts[node] || 0, count);
    }
  }
}

// Usage: like counter across multiple servers
const server1Counter = new GCounter('server-1');
const server2Counter = new GCounter('server-2');

server1Counter.increment(); // {server-1: 1}
server1Counter.increment(); // {server-1: 2}
server2Counter.increment(); // {server-2: 1}

// Merge — no conflicts, no coordination needed
server1Counter.merge(server2Counter);
console.log(server1Counter.value()); // 3

// LWW-Register (Last-Writer-Wins) for simple values
class LWWRegister {
  constructor() { this.value = null; this.timestamp = 0; }
  set(value, timestamp = Date.now()) {
    if (timestamp > this.timestamp) {
      this.value = value;
      this.timestamp = timestamp;
    }
  }
  merge(other) {
    if (other.timestamp > this.timestamp) {
      this.value = other.value;
      this.timestamp = other.timestamp;
    }
  }
}
```

**Use cases**: Collaborative editing (Yjs), shopping carts, like/view counters, offline-first apps. CRDTs trade off conflict resolution complexity for guaranteed convergence without coordination.

---

## Q14. (Advanced) How do you implement the Circuit Breaker pattern in a distributed system?

See Q7 in file 18 (Microservices) for full implementation. In distributed systems context:

```js
// Distributed circuit breaker state shared via Redis
class DistributedCircuitBreaker {
  constructor(redis, name, options = {}) {
    this.redis = redis;
    this.key = `circuit:${name}`;
    this.threshold = options.threshold || 5;
    this.resetTimeout = options.resetTimeout || 30000;
  }

  async execute(fn) {
    const state = await this.getState();
    if (state === 'OPEN') {
      const openedAt = await this.redis.get(`${this.key}:opened_at`);
      if (Date.now() - parseInt(openedAt) > this.resetTimeout) {
        await this.setState('HALF_OPEN');
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      await this.recordSuccess();
      return result;
    } catch (err) {
      await this.recordFailure();
      throw err;
    }
  }

  async recordFailure() {
    const failures = await this.redis.incr(`${this.key}:failures`);
    await this.redis.expire(`${this.key}:failures`, 60);
    if (failures >= this.threshold) {
      await this.setState('OPEN');
      await this.redis.set(`${this.key}:opened_at`, Date.now());
    }
  }

  async recordSuccess() {
    await this.redis.set(`${this.key}:failures`, 0);
    const state = await this.getState();
    if (state === 'HALF_OPEN') await this.setState('CLOSED');
  }

  async getState() { return (await this.redis.get(`${this.key}:state`)) || 'CLOSED'; }
  async setState(state) { await this.redis.set(`${this.key}:state`, state); }
}
```

**Answer**: In distributed systems, circuit breaker state must be shared across all instances (via Redis). Otherwise, each instance tracks failures independently and the circuit never opens.

---

## Q15. (Advanced) What is the Split Brain problem and how do you prevent it?

```
Normal:  Node A (leader) ←→ Node B (follower) ←→ Node C (follower)

Network partition:
  [Node A (thinks it's leader)]  ✕  [Node B + Node C (elect new leader)]

Split brain: TWO leaders accepting writes → data divergence!
```

**Prevention strategies**:

```js
// 1. Quorum-based leadership: need majority to be leader
// With 3 nodes: need 2 to confirm → only the partition with 2+ nodes can have a leader
// Node A alone (1/3) → steps down
// Node B + C (2/3) → elect B as new leader

// 2. Fencing tokens: each leader gets an incrementing token
class FencedLeader {
  constructor(redis, name) {
    this.redis = redis;
    this.key = `leader:${name}`;
  }

  async acquireLeadership() {
    const fencingToken = await this.redis.incr(`${this.key}:token`);
    const acquired = await this.redis.set(this.key, JSON.stringify({
      instanceId: this.instanceId,
      fencingToken,
    }), 'PX', 30000, 'NX');

    return acquired ? fencingToken : null;
  }

  async writeWithFence(db, fencingToken, query) {
    // Include fencing token in write — DB rejects if token is stale
    return db.query(
      `${query} WHERE fencing_token < $1`,
      [fencingToken]
    );
  }
}
```

**Answer**: Split brain occurs when a network partition causes two leaders. Prevention: quorum-based leadership (only majority partition can elect leader), fencing tokens (stale leaders' writes are rejected), and STONITH ("Shoot The Other Node In The Head" — literally power off the old leader).

---

## Q16. (Advanced) How do you design a distributed rate limiter?

```js
// Sliding window rate limiter using Redis
class DistributedRateLimiter {
  constructor(redis) { this.redis = redis; }

  async isAllowed(key, maxRequests, windowMs) {
    const now = Date.now();
    const windowStart = now - windowMs;
    const redisKey = `ratelimit:${key}`;

    // Lua script for atomic check-and-update
    const script = `
      -- Remove expired entries
      redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
      -- Count current entries
      local count = redis.call('ZCARD', KEYS[1])
      if count < tonumber(ARGV[2]) then
        -- Under limit: add new entry
        redis.call('ZADD', KEYS[1], ARGV[3], ARGV[3] .. '-' .. math.random())
        redis.call('PEXPIRE', KEYS[1], ARGV[4])
        return 1
      else
        return 0
      end
    `;

    const allowed = await this.redis.eval(
      script, 1, redisKey,
      windowStart.toString(), maxRequests.toString(), now.toString(), windowMs.toString()
    );

    return {
      allowed: allowed === 1,
      remaining: Math.max(0, maxRequests - await this.redis.zcard(redisKey)),
    };
  }
}

// Usage
const limiter = new DistributedRateLimiter(redis);

app.use(async (req, res, next) => {
  const key = req.user?.id || req.ip;
  const { allowed, remaining } = await limiter.isAllowed(key, 100, 60000);

  res.set('X-RateLimit-Remaining', remaining);
  if (!allowed) return res.status(429).json({ error: 'Rate limit exceeded' });
  next();
});
```

---

## Q17. (Advanced) What is consensus and how do algorithms like Raft work?

**Answer**: Consensus is how distributed nodes agree on a value. Required for: leader election, distributed locks, replicated state machines.

```
Raft algorithm (simplified):
1. Leader election: nodes vote, majority wins
2. Log replication: leader sends entries to followers
3. Commitment: entry committed when majority acknowledges

States: Follower → Candidate → Leader

Term 1: Node A is leader
  A → writes to B, C (majority = committed)

Term 2: A goes down, B becomes candidate
  B requests votes from C → B wins (2/3 majority)
  B is new leader for term 2
```

```js
// In practice, you don't implement Raft — you use systems built on it:
// - etcd (Kubernetes uses this for cluster state)
// - Consul (service discovery, KV store)
// - CockroachDB (distributed SQL using Raft)
// - Redis Cluster (uses Raft-like protocol for failover)

// Using etcd for distributed coordination
const { Etcd3 } = require('etcd3');
const client = new Etcd3();

// Distributed lock via etcd (consensus-backed)
const lock = client.lock('my-resource');
await lock.acquire();
try {
  await processExclusiveTask();
} finally {
  await lock.release();
}
```

**Answer**: Use Raft/Paxos-based systems (etcd, Consul, Zookeeper) for coordination. Never implement consensus yourself in production. Node.js apps should consume these services, not implement the algorithms.

---

## Q18. (Advanced) How do you handle partial failures in distributed systems?

```js
// Partial failure: some operations succeed, others fail
// Example: order creation touches 3 services

async function createOrder(orderData) {
  // Step 1: Reserve inventory (succeeds)
  const reservation = await inventoryService.reserve(orderData.items);

  try {
    // Step 2: Charge payment (fails!)
    const payment = await paymentService.charge(orderData.userId, orderData.total);
  } catch (err) {
    // Must compensate step 1
    await inventoryService.release(reservation.id);
    throw err;
  }

  // Step 3: Create order record
  const order = await Order.create({ ...orderData, reservationId: reservation.id });
  return order;
}

// Better approach: use an orchestrated saga with state machine
class OrderSagaStateMachine {
  constructor() {
    this.transitions = {
      CREATED: { INVENTORY_RESERVED: 'INVENTORY_RESERVED', INVENTORY_FAILED: 'FAILED' },
      INVENTORY_RESERVED: { PAYMENT_CHARGED: 'PAYMENT_CHARGED', PAYMENT_FAILED: 'COMPENSATING' },
      PAYMENT_CHARGED: { ORDER_CONFIRMED: 'COMPLETED' },
      COMPENSATING: { INVENTORY_RELEASED: 'FAILED' },
    };
  }

  async run(orderId) {
    let state = 'CREATED';
    try {
      await inventoryService.reserve(orderId);
      state = this.transitions[state]['INVENTORY_RESERVED'];

      await paymentService.charge(orderId);
      state = this.transitions[state]['PAYMENT_CHARGED'];

      await orderService.confirm(orderId);
      state = 'COMPLETED';
    } catch (err) {
      // Compensate based on current state
      if (state === 'INVENTORY_RESERVED' || state === 'COMPENSATING') {
        await inventoryService.release(orderId);
      }
      state = 'FAILED';
    }

    await db('saga_state').update({ state }).where({ order_id: orderId });
    return state;
  }
}
```

---

## Q19. (Advanced) How do you design a distributed cache with consistency?

```js
// Cache-aside pattern with distributed invalidation
class DistributedCache {
  constructor(redis, db) {
    this.redis = redis;
    this.db = db;
    this.subscriber = redis.duplicate();
  }

  async get(key, fetchFn, ttl = 300) {
    // Try cache first
    const cached = await this.redis.get(key);
    if (cached) return JSON.parse(cached);

    // Cache miss — fetch from DB
    const data = await fetchFn();
    if (data) {
      await this.redis.set(key, JSON.stringify(data), 'EX', ttl);
    }
    return data;
  }

  async invalidate(key) {
    // Delete locally AND broadcast to all instances
    await this.redis.del(key);
    await this.redis.publish('cache-invalidation', key);
  }

  async startListening() {
    await this.subscriber.subscribe('cache-invalidation');
    this.subscriber.on('message', (channel, key) => {
      // Other instances invalidate their local cache too
      this.localCache?.delete(key);
    });
  }
}

// Usage with write-through
async function updateUser(id, data) {
  await db('users').where({ id }).update(data);
  await cache.invalidate(`user:${id}`);  // invalidate across all servers
  return data;
}
```

---

## Q20. (Advanced) Senior red flags in distributed systems.

**Answer**:

1. **Assuming network is reliable** — no timeouts, no retries, no circuit breakers
2. **Using wall clock for ordering** — clocks skew between machines
3. **Not making operations idempotent** — duplicate processing causes data corruption
4. **Two-phase commit across services** — blocks everything, doesn't scale
5. **Distributed monolith** — services tightly coupled via synchronous calls
6. **No dead letter queue** — poison messages block consumers forever
7. **Using Redis for distributed locks in critical paths** — Redis isn't a consensus system
8. **Ignoring partial failures** — assuming all-or-nothing when reality is some-succeed-some-fail
9. **No distributed tracing** — impossible to debug cross-service issues
10. **Mixing consistency levels without understanding** — reading from eventually-consistent replica after a write

```js
// RED FLAG: relying on timestamps for ordering
const order1 = { timestamp: Date.now() }; // Server A: 10:00:00.000
const order2 = { timestamp: Date.now() }; // Server B: 10:00:00.150 (but happened BEFORE order1!)

// FIX: use logical ordering (sequence numbers, vector clocks)
const order1 = { sequenceNumber: await getNextSequence() };
```

**Senior interview answer**: "I design distributed systems with the understanding that networks fail, clocks skew, and partial failures are normal. I use idempotency keys for all writes, the Outbox pattern for reliable event publishing, sagas for distributed transactions, distributed tracing for observability, and CRDTs or consensus-backed stores for coordination. I prefer eventual consistency where acceptable and reserve strong consistency for critical operations like payments."
