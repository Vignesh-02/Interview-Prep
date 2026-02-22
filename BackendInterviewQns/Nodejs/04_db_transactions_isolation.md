# 4. Database Transactions & Isolation Levels

## Topic Introduction

A **transaction** is a group of database operations that execute as a single unit — either ALL succeed (commit) or ALL fail (rollback). **Isolation levels** control what concurrent transactions can see of each other's uncommitted changes.

```
T1: Read balance=100 → Withdraw 80 → Commit
T2: Read balance=100 → Withdraw 80 → Commit   (concurrent)

Without proper isolation → balance becomes -60 (both read 100, both withdraw 80)
With SERIALIZABLE → T2 waits or retries, balance stays correct
```

Every backend engineer must understand transactions because **every multi-step write operation** (transfers, orders, inventory) needs them. Getting isolation wrong causes **lost updates**, **phantom reads**, and **double-charges** in production.

**Go/Java tradeoff**: Go uses `sql.Tx` with explicit `Begin()`/`Commit()`/`Rollback()`. Java Spring provides `@Transactional` annotation (declarative). Node.js requires manual transaction management with most ORMs — no magic annotation.

---

## Q1. (Beginner) What is a database transaction? Show a basic example in Node.js.

**Scenario**: Transfer $100 from account A to account B. Both updates must succeed or neither should.

```js
const { Pool } = require('pg');
const pool = new Pool();

async function transfer(fromId, toId, amount) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, fromId]);
    await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, toId]);
    await client.query('COMMIT');
    return { success: true };
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release(); // always release to pool
  }
}
```

**Answer**: A transaction wraps multiple queries in `BEGIN` → operations → `COMMIT`. If any operation fails, `ROLLBACK` undoes everything. The `finally` block ensures the connection returns to the pool even on error.

---

## Q2. (Beginner) What are ACID properties? Explain each with an example.

**Answer**:

| Property | Meaning | Example |
|----------|---------|---------|
| **Atomicity** | All operations succeed or all fail | Transfer: debit AND credit, not just one |
| **Consistency** | DB moves from one valid state to another | Balance can't go negative (if constraint exists) |
| **Isolation** | Concurrent transactions don't interfere | Two transfers don't read stale balances |
| **Durability** | Committed data survives crashes | After COMMIT, data is on disk, not just in memory |

```js
// Atomicity example — if credit fails, debit is rolled back
try {
  await client.query('BEGIN');
  await client.query('UPDATE accounts SET balance = balance - 100 WHERE id = 1'); // debit
  await client.query('UPDATE accounts SET balance = balance + 100 WHERE id = 999'); // credit (ID doesn't exist)
  await client.query('COMMIT');
} catch (err) {
  await client.query('ROLLBACK'); // debit is undone
}
```

---

## Q3. (Beginner) What are the four SQL isolation levels? What problems does each prevent?

**Answer**:

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Performance |
|----------------|------------|--------------------:|-------------:|-------------|
| **READ UNCOMMITTED** | Possible | Possible | Possible | Fastest |
| **READ COMMITTED** | Prevented | Possible | Possible | Good (PostgreSQL default) |
| **REPEATABLE READ** | Prevented | Prevented | Possible* | Moderate (MySQL default) |
| **SERIALIZABLE** | Prevented | Prevented | Prevented | Slowest |

*PostgreSQL's REPEATABLE READ also prevents phantom reads via MVCC.

```js
// Set isolation level for a transaction
await client.query('BEGIN');
await client.query('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE');
// ... operations ...
await client.query('COMMIT');
```

**Key insight**: Higher isolation = more correct but slower and more likely to cause **serialization errors** (retry needed).

---

## Q4. (Beginner) What is a dirty read vs a non-repeatable read vs a phantom read?

**Scenario**: Two transactions run concurrently on a `products` table.

```
Dirty Read:
  T1: UPDATE price = 50  (not committed)
  T2: SELECT price → sees 50  (T1 hasn't committed!)
  T1: ROLLBACK
  T2 used a value that never existed ❌

Non-Repeatable Read:
  T1: SELECT price → 100
  T2: UPDATE price = 50; COMMIT
  T1: SELECT price → 50  (different value for same row!) ❌

Phantom Read:
  T1: SELECT COUNT(*) WHERE status='active' → 10
  T2: INSERT INTO products(status) VALUES('active'); COMMIT
  T1: SELECT COUNT(*) WHERE status='active' → 11  (new row appeared!) ❌
```

**Answer**: Dirty read = see uncommitted data. Non-repeatable read = same row returns different values. Phantom read = new rows appear in a range query. Use higher isolation levels to prevent each.

---

## Q5. (Beginner) What is connection pooling? Why is it critical for Node.js?

**Scenario**: Your API creates a new DB connection per request. Under load, the database runs out of connections.

```js
// BAD — new connection per request
app.get('/users', async (req, res) => {
  const client = new Client(); // opens new TCP connection
  await client.connect();
  const result = await client.query('SELECT * FROM users');
  await client.end(); // closes connection
  res.json(result.rows);
});

// GOOD — connection pool
const pool = new Pool({ max: 20 }); // reuse 20 connections
app.get('/users', async (req, res) => {
  const result = await pool.query('SELECT * FROM users'); // borrows from pool
  res.json(result.rows);
});
```

**Answer**: Opening a TCP connection to PostgreSQL takes ~50ms (DNS, TCP handshake, auth). A pool maintains a set of **pre-opened connections** and lends them to queries. This reduces latency and prevents exhausting DB connection limits.

**Pool sizing**: `max` connections = CPU cores of DB × 2 + disk spindles. For a 4-core DB, ~10-20 connections. More isn't better — connection contention increases with too many.

---

## Q6. (Intermediate) How do you prevent double-charging in a payment system using transactions?

**Scenario**: User clicks "Pay" twice quickly. Two requests hit the API simultaneously.

```js
async function chargeUser(userId, orderId, amount) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE');

    // Check if already charged (idempotency)
    const existing = await client.query(
      'SELECT id FROM payments WHERE order_id = $1', [orderId]
    );
    if (existing.rows.length > 0) {
      await client.query('COMMIT');
      return { status: 'already_charged', paymentId: existing.rows[0].id };
    }

    // Lock the user's account row
    const account = await client.query(
      'SELECT balance FROM accounts WHERE user_id = $1 FOR UPDATE', [userId]
    );
    if (account.rows[0].balance < amount) {
      await client.query('ROLLBACK');
      throw new Error('Insufficient funds');
    }

    await client.query('UPDATE accounts SET balance = balance - $1 WHERE user_id = $2', [amount, userId]);
    const payment = await client.query(
      'INSERT INTO payments(user_id, order_id, amount) VALUES($1, $2, $3) RETURNING id',
      [userId, orderId, amount]
    );

    await client.query('COMMIT');
    return { status: 'charged', paymentId: payment.rows[0].id };
  } catch (err) {
    await client.query('ROLLBACK');
    if (err.code === '40001') return chargeUser(userId, orderId, amount); // retry on serialization error
    throw err;
  } finally {
    client.release();
  }
}
```

**Answer**: Three defenses: (1) **Idempotency check** — if order already charged, return existing result. (2) **`FOR UPDATE` row lock** — prevents concurrent reads of stale balance. (3) **SERIALIZABLE isolation** — DB detects conflicts and throws error (retry). Always add a **unique constraint** on `(order_id)` in payments table as final safety net.

---

## Q7. (Intermediate) What is optimistic vs pessimistic locking? Show both in Node.js.

**Scenario**: Two users edit the same document. Last save wins (lost update problem).

```js
// PESSIMISTIC — lock the row immediately (blocks other transactions)
async function updateDocPessimistic(docId, newContent) {
  const client = await pool.connect();
  await client.query('BEGIN');
  const doc = await client.query('SELECT * FROM docs WHERE id = $1 FOR UPDATE', [docId]);
  // Other transactions trying to SELECT FOR UPDATE on this row WAIT here
  await client.query('UPDATE docs SET content = $1 WHERE id = $2', [newContent, docId]);
  await client.query('COMMIT');
  client.release();
}

// OPTIMISTIC — check version at update time (no upfront lock)
async function updateDocOptimistic(docId, newContent, expectedVersion) {
  const result = await pool.query(
    'UPDATE docs SET content = $1, version = version + 1 WHERE id = $2 AND version = $3',
    [newContent, docId, expectedVersion]
  );
  if (result.rowCount === 0) {
    throw new Error('Conflict: document was modified by another user');
    // Client should re-fetch and retry
  }
}
```

**Answer**:
| | **Pessimistic** | **Optimistic** |
|---|---|---|
| Lock | Acquired upfront (`FOR UPDATE`) | No lock; check at commit |
| Concurrency | Low (blocks others) | High (no blocking) |
| Best for | High contention (payments) | Low contention (editing) |
| Risk | Deadlocks if not careful | Retry storms under high contention |

---

## Q8. (Intermediate) How do you handle deadlocks in database transactions?

**Scenario**: T1 locks row A then tries to lock row B. T2 locks row B then tries to lock row A. Both wait forever.

```
T1: UPDATE accounts SET ... WHERE id = 1  (locks row 1)
T1: UPDATE accounts SET ... WHERE id = 2  (waits for T2's lock on row 2)

T2: UPDATE accounts SET ... WHERE id = 2  (locks row 2)
T2: UPDATE accounts SET ... WHERE id = 1  (waits for T1's lock on row 1)
// DEADLOCK!
```

**Answer**: PostgreSQL automatically **detects deadlocks** and kills one transaction (error code `40P01`).

**Prevention**:
```js
async function transferSafe(id1, id2, amount) {
  // ALWAYS lock in consistent order (lower ID first)
  const [fromId, toId] = id1 < id2 ? [id1, id2] : [id2, id1];
  const sign = id1 < id2 ? -1 : 1;

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query('SELECT * FROM accounts WHERE id = $1 FOR UPDATE', [fromId]);
    await client.query('SELECT * FROM accounts WHERE id = $1 FOR UPDATE', [toId]);
    // Now both rows locked in consistent order — no deadlock possible
    await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, id1]);
    await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, id2]);
    await client.query('COMMIT');
  } catch (err) {
    await client.query('ROLLBACK');
    if (err.code === '40P01') return transferSafe(id1, id2, amount); // retry deadlock
    throw err;
  } finally {
    client.release();
  }
}
```

**Rule**: Always lock rows in a **consistent global order** (e.g., by ascending ID). Retry on deadlock errors.

---

## Q9. (Intermediate) How do ORMs (Prisma, TypeORM) handle transactions? What are the tradeoffs vs raw SQL?

```js
// Prisma interactive transaction
const result = await prisma.$transaction(async (tx) => {
  const from = await tx.account.update({
    where: { id: fromId },
    data: { balance: { decrement: amount } },
  });
  if (from.balance < 0) throw new Error('Insufficient funds'); // triggers rollback
  const to = await tx.account.update({
    where: { id: toId },
    data: { balance: { increment: amount } },
  });
  return { from, to };
});
```

**Answer**:
| | **ORM Transactions** | **Raw SQL** |
|---|---|---|
| Developer speed | Faster (type-safe, no SQL) | Slower |
| Control | Less (can't SET ISOLATION LEVEL easily) | Full control |
| Performance | Some overhead (query generation) | Optimal |
| Complex queries | Limited (N+1, joins) | Full SQL power |
| Lock control | Limited (`FOR UPDATE` not always easy) | Full |

**Senior recommendation**: Use ORM for 90% of CRUD. Use raw SQL for critical transactions (payments, inventory). Never let the ORM hide transaction boundaries.

---

## Q10. (Intermediate) What is MVCC (Multi-Version Concurrency Control)? How does PostgreSQL use it?

**Answer**: MVCC lets readers and writers operate **concurrently without blocking** each other. Each transaction sees a **snapshot** of the database at its start time.

```
Time 1: T1 reads row (version 1) → sees value=100
Time 2: T2 updates row → creates version 2 (value=200), commits
Time 3: T1 reads same row → still sees value=100 (its snapshot)
```

PostgreSQL stores multiple versions of each row. Old versions are cleaned up by **VACUUM**.

**Impact on Node.js**:
- READ COMMITTED: Each **query** sees the latest committed data
- REPEATABLE READ: The entire **transaction** sees a consistent snapshot
- No read locks needed — readers never block writers

```sql
-- This is safe in PostgreSQL MVCC:
-- Long SELECT doesn't block concurrent INSERTs
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT COUNT(*) FROM orders WHERE date > '2024-01-01';
-- ... takes 10 seconds ...
-- Count is consistent even if new orders are inserted during this time
COMMIT;
```

---

## Q11. (Intermediate) How do you handle long-running transactions without blocking other users?

**Scenario**: A nightly report queries millions of rows. It holds a transaction open for 10 minutes, blocking VACUUM and degrading performance.

**Answer**: Long transactions in PostgreSQL prevent VACUUM from cleaning dead tuples, causing table bloat.

**Solutions**:
```js
// 1. Use a read replica for reports
const reportPool = new Pool({ host: 'read-replica.db.internal' });

// 2. Use cursor-based pagination instead of one huge query
async function generateReport(res) {
  const BATCH = 10000;
  let offset = 0;
  let rows;
  do {
    rows = await pool.query(
      'SELECT * FROM orders WHERE date > $1 ORDER BY id LIMIT $2 OFFSET $3',
      ['2024-01-01', BATCH, offset]
    );
    for (const row of rows.rows) processRow(row);
    offset += BATCH;
  } while (rows.rows.length === BATCH);
}

// 3. Use streaming with no long-held transaction
const cursor = client.query(new Cursor('SELECT * FROM orders'));
// cursor.read() fetches batches without holding a long transaction
```

**Best**: Read replicas for reports. Second best: short transactions with cursor-based pagination.

---

## Q12. (Intermediate) How do distributed transactions work? When should you avoid them?

**Answer**: Distributed transactions span multiple databases or services. The most common protocol is **Two-Phase Commit (2PC)**:

```
Coordinator → Service A: "Prepare" → "Ready"
Coordinator → Service B: "Prepare" → "Ready"
Coordinator → Both: "Commit"

If any says "Abort":
Coordinator → Both: "Rollback"
```

**Problems**: 2PC is slow (multiple round-trips), blocks on coordinator failure, and doesn't scale.

**Better alternatives for microservices**:
```js
// Saga pattern — each service does local transaction + compensating action
// Order service creates order → Payment service charges → Inventory reserves
// If payment fails → Order service cancels order (compensating transaction)

async function createOrder(data) {
  const order = await orderDb.create(data);
  try {
    await paymentService.charge(order.userId, order.total);
    await inventoryService.reserve(order.items);
  } catch (err) {
    // Compensating transaction
    await orderDb.cancel(order.id);
    await paymentService.refund(order.userId, order.total);
    throw err;
  }
}
```

**Rule**: Avoid distributed transactions. Use **sagas** (choreography or orchestration) with **idempotent** operations and **eventual consistency**.

---

## Q13. (Advanced) Production scenario: Your e-commerce checkout has a race condition. Two users buy the last item simultaneously. Both succeed. How do you fix it?

**Answer**:

```js
async function checkout(userId, productId) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Lock the inventory row
    const inv = await client.query(
      'SELECT quantity FROM inventory WHERE product_id = $1 FOR UPDATE',
      [productId]
    );
    if (inv.rows[0].quantity < 1) {
      await client.query('ROLLBACK');
      throw new Error('Out of stock');
    }

    await client.query(
      'UPDATE inventory SET quantity = quantity - 1 WHERE product_id = $1',
      [productId]
    );
    const order = await client.query(
      'INSERT INTO orders(user_id, product_id) VALUES($1, $2) RETURNING id',
      [userId, productId]
    );

    await client.query('COMMIT');
    return order.rows[0];
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}
```

**Key**: `FOR UPDATE` locks the inventory row. The second concurrent transaction **waits** until the first commits. Then it reads the updated quantity (0) and correctly returns "Out of stock."

**Alternative** (without explicit lock):
```sql
UPDATE inventory SET quantity = quantity - 1
WHERE product_id = $1 AND quantity > 0
RETURNING quantity;
-- If rowCount = 0, item was out of stock
```

This atomic `UPDATE ... WHERE quantity > 0` avoids the need for a separate lock.

---

## Q14. (Advanced) How do you implement the Outbox Pattern for reliable event publishing with transactions?

**Scenario**: After creating an order, you need to publish an event to Kafka. But the DB commit and Kafka publish aren't atomic — one can fail.

```js
// PROBLEM: order created but event lost if Kafka fails
await db.query('INSERT INTO orders ...');
await kafka.send({ topic: 'orders', value: '...' }); // ← what if this fails?

// SOLUTION: Outbox Pattern
async function createOrder(data) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const order = await client.query('INSERT INTO orders ... RETURNING *', [data]);

    // Write event to outbox table IN THE SAME TRANSACTION
    await client.query(
      'INSERT INTO outbox(aggregate_id, event_type, payload) VALUES($1, $2, $3)',
      [order.rows[0].id, 'OrderCreated', JSON.stringify(order.rows[0])]
    );

    await client.query('COMMIT');
    return order.rows[0];
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}

// Separate process: poll outbox and publish to Kafka
async function publishOutbox() {
  const events = await pool.query(
    'SELECT * FROM outbox WHERE published = false ORDER BY created_at LIMIT 100'
  );
  for (const event of events.rows) {
    await kafka.send({ topic: event.event_type, value: event.payload });
    await pool.query('UPDATE outbox SET published = true WHERE id = $1', [event.id]);
  }
}
setInterval(publishOutbox, 1000);
```

**Answer**: The Outbox Pattern ensures **atomicity** between the business operation and event creation (same DB transaction). A separate process reads the outbox and publishes to the message broker. If publishing fails, it retries from the outbox. The event is **at-least-once** delivered — consumers must be idempotent.

---

## Q15. (Advanced) How do you handle transaction retries with exponential backoff for serialization failures?

```js
async function withRetry(fn, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      const isRetryable = err.code === '40001' // serialization failure
                       || err.code === '40P01'; // deadlock
      if (!isRetryable || attempt === maxRetries) throw err;

      const delay = Math.min(100 * Math.pow(2, attempt) + Math.random() * 100, 5000);
      console.warn(`Retry ${attempt}/${maxRetries} after ${delay}ms: ${err.message}`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

// Usage
await withRetry(() => chargeUser(userId, orderId, amount));
```

**Answer**: SERIALIZABLE isolation can cause `40001` (serialization failure) errors when concurrent transactions conflict. These are **expected and normal** — the correct response is to **retry the entire transaction** (not just the failed query).

Exponential backoff with jitter prevents **retry storms** where all retrying transactions conflict again simultaneously.

---

## Q16. (Advanced) How do you choose between PostgreSQL and MongoDB for transaction-heavy workloads?

**Answer**:

| | **PostgreSQL** | **MongoDB** |
|---|---|---|
| Transactions | Full ACID, multi-table | ACID since 4.0 (multi-document) |
| Isolation levels | All four standard levels | Snapshot isolation |
| Performance at scale | Excellent with proper indexing | Good for write-heavy + sharding |
| Schema | Strict (migrations needed) | Flexible (schema-less) |
| Complex queries | Full SQL, window functions, CTEs | Aggregation pipeline |
| Joins | Native, optimized | $lookup (limited) |

**Choose PostgreSQL when**: Complex relationships, strong consistency needed, heavy transactions, reporting/analytics.

**Choose MongoDB when**: Flexible schema, document-oriented data, horizontal sharding needed, rapid prototyping.

**Senior take**: "For a payment system, I'd always choose PostgreSQL for its proven ACID guarantees and row-level locking. For a content management system with varied document structures, MongoDB might be more natural."

---

## Q17. (Advanced) What is the N+1 query problem in transactions? How do you detect and fix it?

**Scenario**: Fetching 100 orders with their items generates 101 queries instead of 2.

```js
// BAD: N+1 queries (1 for orders + 100 for items)
const orders = await db.query('SELECT * FROM orders LIMIT 100');
for (const order of orders.rows) {
  order.items = await db.query('SELECT * FROM items WHERE order_id = $1', [order.id]);
  // 100 separate queries!
}

// GOOD: 2 queries
const orders = await db.query('SELECT * FROM orders LIMIT 100');
const orderIds = orders.rows.map(o => o.id);
const items = await db.query('SELECT * FROM items WHERE order_id = ANY($1)', [orderIds]);
// Group items by order_id in JS
const itemsByOrder = {};
items.rows.forEach(item => {
  (itemsByOrder[item.order_id] ||= []).push(item);
});
orders.rows.forEach(order => { order.items = itemsByOrder[order.id] || []; });
```

**Detection**: Enable query logging and count queries per request. Or use a query analysis middleware:
```js
let queryCount = 0;
const originalQuery = pool.query.bind(pool);
pool.query = (...args) => { queryCount++; return originalQuery(...args); };
```

---

## Q18. (Advanced) How do you implement read replicas with Node.js for read/write splitting?

```js
const { Pool } = require('pg');

const writePool = new Pool({ host: 'primary.db.internal', max: 20 });
const readPool = new Pool({ host: 'replica.db.internal', max: 40 });

// Middleware to pick the right pool
function getPool(isWrite) {
  return isWrite ? writePool : readPool;
}

// Usage
app.get('/users/:id', async (req, res) => {
  const result = await getPool(false).query('SELECT * FROM users WHERE id = $1', [req.params.id]);
  res.json(result.rows[0]);
});

app.post('/users', async (req, res) => {
  const result = await getPool(true).query(
    'INSERT INTO users(name, email) VALUES($1, $2) RETURNING *', [req.body.name, req.body.email]
  );
  res.json(result.rows[0]);
});
```

**Answer**: Writes go to the primary. Reads go to replicas. This scales read throughput linearly.

**Gotcha — replication lag**: After a write, an immediate read from the replica may return stale data.
```js
// Fix: read-your-writes consistency
app.post('/users', async (req, res) => {
  const user = await writePool.query('INSERT INTO users ... RETURNING *', [...]);
  // Return the result from the write query, don't re-read from replica
  res.json(user.rows[0]);
});
```

---

## Q19. (Advanced) How does Go/Java handle transactions differently from Node.js? What can Node learn?

**Answer**:

**Go** — explicit, verbose, no magic:
```go
tx, _ := db.Begin()
_, err := tx.Exec("UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, fromId)
if err != nil { tx.Rollback(); return err }
_, err = tx.Exec("UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, toId)
if err != nil { tx.Rollback(); return err }
tx.Commit()
```

**Java Spring** — declarative:
```java
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transfer(Long fromId, Long toId, BigDecimal amount) {
    accountRepo.debit(fromId, amount);
    accountRepo.credit(toId, amount);
    // Rollback happens automatically on exception
}
```

**Node.js** — manual (most similar to Go):
```js
const client = await pool.connect();
await client.query('BEGIN');
// ... must manually ROLLBACK on error, release on finally
```

**What Node can learn**: Libraries like `knex` and Prisma provide transaction helpers that reduce boilerplate. But understanding the manual flow is essential for senior engineers.

---

## Q20. (Advanced) A senior engineer code review checklist for database transactions.

**Answer — Red flags to catch**:

1. **No transaction for multi-step writes**: Two `INSERT`s without `BEGIN`/`COMMIT` — partial failure possible
2. **Connection not released in `finally`**: Leaked connections exhaust the pool
3. **Long-held transactions**: Open transaction while calling external API → locks held, VACUUM blocked
4. **No retry on serialization failure**: SERIALIZABLE without retry logic → random 500 errors
5. **SELECT then UPDATE without lock**: Classic race condition — use `FOR UPDATE` or atomic UPDATE
6. **Using ORM without understanding generated SQL**: ORM may not use transactions where you expect
7. **Hardcoded pool size**: Pool too large for DB capacity → connection contention
8. **No read replica for read-heavy routes**: All queries hitting primary under high load
9. **Mixing business logic with transaction management**: Hard to test and maintain

**Senior interview answer**: "I check for proper transaction boundaries, pessimistic locking on contended resources, connection pool management, retry logic for serialization failures, and read/write splitting for scalable read paths."
