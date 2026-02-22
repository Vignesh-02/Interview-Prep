# 5. Idempotent APIs

## Topic Introduction

An **idempotent** operation produces the **same result** no matter how many times it's executed. In distributed systems, network failures cause **retries** — if your API isn't idempotent, a retry can charge a customer twice, create duplicate orders, or send the same email 10 times.

```
Client → POST /charge  ── network timeout ──► Server (processed but response lost)
Client → POST /charge  ── retry ──► Server (processes AGAIN = double charge!)

With idempotency key:
Client → POST /charge (key: abc123) → Server (checks: abc123 already processed → return stored result)
```

**GET**, **PUT**, **DELETE** are naturally idempotent by HTTP spec. **POST** (create) is NOT — it needs explicit idempotency handling. This is the most important pattern for **payment systems**, **order creation**, and any **state-changing** operation.

**Go/Java tradeoff**: The concept is language-agnostic. Go typically uses middleware + Redis. Java Spring can use aspects/annotations. Node.js typically uses middleware or per-route logic. The storage backend (Redis, DB) is the same across languages.

---

## Q1. (Beginner) What does "idempotent" mean? Which HTTP methods are naturally idempotent?

**Scenario**: You call `DELETE /users/42` three times. What happens?

**Answer**: An operation is idempotent if calling it once or multiple times produces the **same side effect**.

| Method | Idempotent? | Why |
|--------|------------|-----|
| **GET** | Yes | Read-only, no side effects |
| **PUT** | Yes | Replaces entire resource with same data |
| **DELETE** | Yes | First call deletes, subsequent calls return 404 (same end state) |
| **PATCH** | It depends | `PATCH { balance: balance + 10 }` is NOT idempotent |
| **POST** | No | Each call may create a new resource |

```js
// DELETE is idempotent — calling multiple times is safe
app.delete('/users/:id', async (req, res) => {
  const result = await db.query('DELETE FROM users WHERE id = $1', [req.params.id]);
  if (result.rowCount === 0) return res.status(404).json({ error: 'Not found' });
  res.status(204).end();
});
// Second call returns 404, but the end state is the same: user is deleted
```

---

## Q2. (Beginner) What is an idempotency key? How does it work?

**Scenario**: Client retries a payment after a timeout.

```js
// Client sends:
// POST /payments
// Headers: Idempotency-Key: pay_abc123
// Body: { amount: 100, currency: "USD" }

app.post('/payments', async (req, res) => {
  const key = req.headers['idempotency-key'];
  if (!key) return res.status(400).json({ error: 'Idempotency-Key header required' });

  // Check if this key was already processed
  const cached = await redis.get(`idem:${key}`);
  if (cached) return res.status(200).json(JSON.parse(cached));

  // Process the payment
  const result = await processPayment(req.body);

  // Store result with TTL (e.g., 24 hours)
  await redis.set(`idem:${key}`, JSON.stringify(result), 'EX', 86400);
  res.status(201).json(result);
});
```

**Answer**: The client generates a unique key (UUID) and sends it with each request. The server checks if the key was already used — if yes, returns the stored result without reprocessing. The key has a TTL so storage doesn't grow forever.

---

## Q3. (Beginner) Why can't you just use a database unique constraint instead of idempotency keys?

**Answer**: A unique constraint prevents duplicate **records**, but doesn't solve the full problem:

```js
// Unique constraint catches this:
await db.query('INSERT INTO orders(id, ...) VALUES($1, ...)', [orderId]);
// Second insert fails with unique_violation

// But it DOESN'T handle:
// 1. The client doesn't know if the first request succeeded
// 2. Side effects (sending email, calling Stripe) may have already fired
// 3. Error response on retry confuses the client
```

**Idempotency keys** solve the full flow: store the **complete response** so retries get the **same response** the first call would have returned. The client can't tell the difference between the first call and a retry.

Use **both**: unique constraint as a safety net + idempotency key for correct client behavior.

---

## Q4. (Beginner) How do you generate good idempotency keys on the client side?

```js
// Option 1: UUID (most common)
const key = crypto.randomUUID();
// 'f47ac10b-58cc-4372-a567-0e02b2c3d479'

// Option 2: Deterministic key from request content
const crypto = require('crypto');
const key = crypto.createHash('sha256')
  .update(`${userId}:${orderId}:${amount}`)
  .digest('hex');
// Same inputs always produce same key — natural idempotency

// Option 3: Client-generated request ID
const key = `req_${Date.now()}_${Math.random().toString(36).slice(2)}`;
```

**Answer**: **Deterministic keys** (Option 2) are best — if the client retries with the same data, the key is automatically the same. **Random UUIDs** work but require the client to store and resend the same UUID on retry. Never let the server generate the key — the client must control it.

---

## Q5. (Beginner) What's the difference between idempotency and deduplication?

**Answer**:

| | **Idempotency** | **Deduplication** |
|---|---|---|
| **Focus** | Same effect regardless of retries | Prevent processing the same message twice |
| **Scope** | API layer (request/response) | Message/event layer (queues) |
| **Implementation** | Idempotency key → stored response | Message ID → "already processed" flag |
| **Returns** | Original response on retry | May silently discard duplicate |

```js
// API idempotency — returns stored response
const cached = await redis.get(`idem:${key}`);
if (cached) return res.json(JSON.parse(cached)); // client gets same response

// Queue deduplication — skips duplicate processing
async function handleJob(job) {
  const processed = await redis.get(`dedup:${job.data.messageId}`);
  if (processed) return; // silently skip
  await processMessage(job.data);
  await redis.set(`dedup:${job.data.messageId}`, '1', 'EX', 86400);
}
```

---

## Q6. (Intermediate) How do you implement idempotency for a payment API using Redis + PostgreSQL?

**Scenario**: Stripe-like payment API. Must never double-charge. Handles 1000 req/s.

```js
async function createPayment(req, res) {
  const key = req.headers['idempotency-key'];

  // Step 1: Check Redis for cached result
  const cached = await redis.get(`idem:${key}`);
  if (cached) return res.status(200).json(JSON.parse(cached));

  // Step 2: Acquire lock to prevent concurrent processing of same key
  const lockKey = `idem-lock:${key}`;
  const locked = await redis.set(lockKey, '1', 'NX', 'EX', 30); // 30s lock
  if (!locked) return res.status(409).json({ error: 'Request in progress' });

  try {
    // Step 3: Check DB for persisted result (Redis may have evicted)
    const existing = await db.query('SELECT response FROM idempotency WHERE key = $1', [key]);
    if (existing.rows.length > 0) {
      const response = existing.rows[0].response;
      await redis.set(`idem:${key}`, JSON.stringify(response), 'EX', 86400);
      return res.json(response);
    }

    // Step 4: Process payment
    const result = await chargeStripe(req.body);

    // Step 5: Store result in DB + Redis atomically-ish
    await db.query('INSERT INTO idempotency(key, response, created_at) VALUES($1, $2, NOW())',
      [key, JSON.stringify(result)]);
    await redis.set(`idem:${key}`, JSON.stringify(result), 'EX', 86400);

    res.status(201).json(result);
  } finally {
    await redis.del(lockKey);
  }
}
```

**Answer**: Three layers: (1) **Redis cache** for fast lookups, (2) **DB persistence** as source of truth (survives Redis restart), (3) **Distributed lock** prevents concurrent processing of the same key. This handles: retries, concurrent duplicates, and Redis failures.

---

## Q7. (Intermediate) How do you make database writes idempotent without idempotency keys?

**Scenario**: An inventory service receives "decrement stock by 1" messages. Retries could over-decrement.

```js
// BAD: not idempotent — each retry decrements again
await db.query('UPDATE products SET stock = stock - 1 WHERE id = $1', [productId]);

// GOOD: idempotent using unique order reference
await db.query(`
  UPDATE products SET stock = stock - 1
  WHERE id = $1
  AND NOT EXISTS (SELECT 1 FROM reservations WHERE order_id = $2)
`, [productId, orderId]);
await db.query('INSERT INTO reservations(order_id, product_id) VALUES($1, $2) ON CONFLICT DO NOTHING',
  [orderId, productId]);

// ALSO GOOD: use version/sequence number
await db.query(`
  UPDATE products SET stock = stock - 1, last_event_seq = $2
  WHERE id = $1 AND last_event_seq < $2
`, [productId, eventSequenceNumber]);
```

**Answer**: Idempotent writes using: (1) **Unique constraint** + `ON CONFLICT DO NOTHING`, (2) **Sequence numbers** (only process if sequence > last processed), (3) **Conditional update** (check if already applied).

---

## Q8. (Intermediate) How do you handle idempotency for operations with external side effects (email, SMS)?

**Scenario**: After creating an order, you send a confirmation email. On retry, you don't want to send the email again.

```js
async function createOrder(req, res) {
  const key = req.headers['idempotency-key'];
  const cached = await redis.get(`idem:${key}`);
  if (cached) return res.json(JSON.parse(cached));

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const order = await client.query('INSERT INTO orders ... RETURNING *', [...]);

    // Record that we INTEND to send email (but haven't yet)
    await client.query(
      'INSERT INTO outbox(order_id, type, status) VALUES($1, $2, $3)',
      [order.rows[0].id, 'confirmation_email', 'pending']
    );
    await client.query('COMMIT');

    // Email sent asynchronously by a separate worker
    // Worker checks: if status = 'sent', skip (idempotent)
    const result = { orderId: order.rows[0].id, status: 'created' };
    await redis.set(`idem:${key}`, JSON.stringify(result), 'EX', 86400);
    res.status(201).json(result);
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}
```

**Answer**: Use the **Outbox Pattern** — record side effects as pending in the same transaction. A separate worker processes them idempotently. If the email worker crashes and retries, it checks the outbox status before re-sending.

---

## Q9. (Intermediate) What is the "at-most-once" vs "at-least-once" vs "exactly-once" delivery guarantee? How does idempotency help?

**Answer**:

| Guarantee | Meaning | Risk |
|-----------|---------|------|
| **At-most-once** | Send and forget; may be lost | Missing events |
| **At-least-once** | Retry until acknowledged; may duplicate | Duplicate processing |
| **Exactly-once** | Process exactly once | Hardest to achieve |

```
At-least-once + Idempotent consumer = Effectively exactly-once
```

```js
// Queue consumer with at-least-once + idempotency = effectively exactly-once
worker.on('job', async (job) => {
  const dedup = await redis.get(`processed:${job.id}`);
  if (dedup) {
    await job.ack(); // already processed, just acknowledge
    return;
  }

  await processJob(job.data);
  await redis.set(`processed:${job.id}`, '1', 'EX', 604800); // 7 days TTL
  await job.ack();
});
```

**Senior insight**: True exactly-once delivery is essentially impossible in distributed systems. The practical solution is **at-least-once delivery + idempotent processing**.

---

## Q10. (Intermediate) How do you test idempotent APIs?

```js
describe('POST /payments', () => {
  it('returns same response on retry with same idempotency key', async () => {
    const key = 'test-key-123';
    const body = { amount: 100, currency: 'USD' };

    // First request
    const res1 = await request(app).post('/payments')
      .set('Idempotency-Key', key).send(body);
    expect(res1.status).toBe(201);

    // Retry with same key
    const res2 = await request(app).post('/payments')
      .set('Idempotency-Key', key).send(body);
    expect(res2.status).toBe(200);
    expect(res2.body).toEqual(res1.body); // SAME response

    // Different key = new payment
    const res3 = await request(app).post('/payments')
      .set('Idempotency-Key', 'different-key').send(body);
    expect(res3.status).toBe(201);
    expect(res3.body.id).not.toBe(res1.body.id);
  });

  it('handles concurrent duplicate requests', async () => {
    const key = 'concurrent-key';
    const body = { amount: 50, currency: 'USD' };

    const [res1, res2] = await Promise.all([
      request(app).post('/payments').set('Idempotency-Key', key).send(body),
      request(app).post('/payments').set('Idempotency-Key', key).send(body),
    ]);

    // One succeeds, other gets cached result OR 409 (in-progress)
    const bodies = [res1.body, res2.body];
    const successful = bodies.filter(b => b.id);
    expect(new Set(successful.map(b => b.id)).size).toBe(1); // same payment ID
  });
});
```

---

## Q11. (Intermediate) How does Stripe implement idempotency? What can we learn?

**Answer**: Stripe's API accepts an `Idempotency-Key` header on all POST requests.

**Stripe's implementation details**:
1. Keys are stored for **24 hours**
2. If a request is **in-progress** and a retry arrives, Stripe returns **409 Conflict**
3. If the retry has a **different body** but same key, Stripe returns **400** (payload mismatch)
4. On **network error** (no response received), the key is safe to retry
5. On **4xx error**, the error response is cached too (retries get same error)

```js
// Implementing Stripe-like payload validation
async function checkIdempotency(key, bodyHash) {
  const stored = await redis.hgetall(`idem:${key}`);
  if (!stored.response) return null; // not seen before

  if (stored.bodyHash !== bodyHash) {
    throw new Error('Idempotency key reused with different request body');
  }
  return JSON.parse(stored.response);
}
```

**Lesson**: Store the **request hash** alongside the response to detect misuse.

---

## Q12. (Intermediate) How do you handle idempotency key expiration and cleanup?

**Answer**:

```js
// Redis: TTL handles cleanup automatically
await redis.set(`idem:${key}`, response, 'EX', 86400); // expires in 24h

// PostgreSQL: periodic cleanup job
// CREATE INDEX idx_idempotency_created ON idempotency(created_at);
setInterval(async () => {
  await pool.query("DELETE FROM idempotency WHERE created_at < NOW() - INTERVAL '7 days'");
}, 3600000); // hourly cleanup

// Or use PostgreSQL partitioning by date for efficient drops
// DROP old daily partitions instead of DELETE
```

**TTL considerations**:
- **Too short** (minutes): Client retries after TTL → duplicate processing
- **Too long** (months): Storage grows, slower lookups
- **Sweet spot**: 24h–7d depending on retry window

---

## Q13. (Advanced) Production scenario: Your idempotency implementation uses Redis. Redis goes down. What happens and how do you handle it?

**Answer**: Without Redis, the idempotency check fails. Options:

```js
async function processWithFallback(key, body, processFn) {
  try {
    const cached = await redis.get(`idem:${key}`);
    if (cached) return JSON.parse(cached);
  } catch (redisErr) {
    console.error('Redis down, falling back to DB check');
  }

  // Fallback: check PostgreSQL idempotency table
  const existing = await db.query('SELECT response FROM idempotency WHERE key = $1', [key]);
  if (existing.rows.length > 0) return existing.rows[0].response;

  // Process with DB-level unique constraint as safety net
  try {
    const result = await processFn();
    await db.query(
      'INSERT INTO idempotency(key, response) VALUES($1, $2)',
      [key, JSON.stringify(result)]
    );
    // Try to populate Redis if it's back
    redis.set(`idem:${key}`, JSON.stringify(result), 'EX', 86400).catch(() => {});
    return result;
  } catch (err) {
    if (err.code === '23505') { // unique_violation — concurrent duplicate
      const stored = await db.query('SELECT response FROM idempotency WHERE key = $1', [key]);
      return stored.rows[0].response;
    }
    throw err;
  }
}
```

**Answer**: The **database** is the source of truth, not Redis. Redis is a **performance optimization** (fast cache). When Redis fails, fall back to the DB idempotency table. The unique constraint on the key column is the ultimate safety net.

---

## Q14. (Advanced) How do you implement idempotency in a microservices saga (distributed workflow)?

**Scenario**: Order creation spans: Order Service → Payment Service → Inventory Service. Any step can fail and be retried.

```js
// Each service is independently idempotent
// Order Service
async function createOrder(orderId, data) {
  const existing = await db.query('SELECT * FROM orders WHERE id = $1', [orderId]);
  if (existing.rows.length > 0) return existing.rows[0]; // idempotent
  return db.query('INSERT INTO orders(id, ...) VALUES($1, ...) RETURNING *', [orderId, ...]);
}

// Payment Service
async function chargePayment(orderId, amount) {
  const existing = await db.query('SELECT * FROM payments WHERE order_id = $1', [orderId]);
  if (existing.rows.length > 0) return existing.rows[0]; // idempotent
  const charge = await stripe.charges.create({ amount }, { idempotencyKey: `charge-${orderId}` });
  return db.query('INSERT INTO payments(order_id, stripe_id) VALUES($1, $2) RETURNING *',
    [orderId, charge.id]);
}

// Saga orchestrator — retries any failed step
async function executeSaga(orderId, data) {
  await createOrder(orderId, data);       // idempotent — safe to retry
  await chargePayment(orderId, data.amount); // idempotent — safe to retry
  await reserveInventory(orderId, data.items); // idempotent — safe to retry
}
```

**Answer**: Every service in the saga must be independently idempotent using the same `orderId` as the natural key. The orchestrator can retry any step without causing duplicates. Compensating actions (refunds, cancellations) must also be idempotent.

---

## Q15. (Advanced) How do you prevent idempotency key abuse (e.g., replaying old requests with stolen keys)?

**Answer**:

```js
async function validateIdempotencyKey(key, userId, bodyHash) {
  // 1. Key must be tied to authenticated user
  const stored = await redis.hgetall(`idem:${key}`);
  if (stored.userId && stored.userId !== userId) {
    throw new Error('Idempotency key belongs to another user');
  }

  // 2. Store user + body hash when first seen
  if (!stored.userId) {
    await redis.hmset(`idem:${key}`, { userId, bodyHash, createdAt: Date.now() });
    await redis.expire(`idem:${key}`, 86400);
  }

  // 3. Reject if body changed (replay with different payload)
  if (stored.bodyHash && stored.bodyHash !== bodyHash) {
    throw new Error('Request body does not match original');
  }
}
```

**Defenses**: (1) Bind key to authenticated user, (2) Validate request body hash matches original, (3) Short TTL limits replay window, (4) Rate limit key creation per user.

---

## Q16. (Advanced) How do you implement idempotent event consumers in Kafka/SQS?

```js
// Kafka consumer with exactly-once semantics via idempotent processing
const consumer = kafka.consumer({ groupId: 'order-processor' });

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const eventId = message.headers['event-id']?.toString();
    if (!eventId) return; // malformed

    // Atomic check-and-process using DB transaction
    const client = await pool.connect();
    try {
      await client.query('BEGIN');

      // Check if already processed (unique constraint on event_id)
      const result = await client.query(
        'INSERT INTO processed_events(event_id) VALUES($1) ON CONFLICT DO NOTHING RETURNING event_id',
        [eventId]
      );

      if (result.rowCount === 0) {
        // Already processed — skip
        await client.query('COMMIT');
        return;
      }

      // Process the event within the same transaction
      const data = JSON.parse(message.value.toString());
      await processOrderEvent(client, data);

      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err; // message will be retried
    } finally {
      client.release();
    }
  },
});
```

**Answer**: The deduplication check and business logic happen in the **same DB transaction**. If either fails, both roll back. The `ON CONFLICT DO NOTHING` makes the check atomic. This gives effectively exactly-once processing.

---

## Q17. (Advanced) How does idempotency interact with caching? Can they conflict?

**Answer**: Yes, they can conflict if not careful:

```
Scenario: CDN caches a 201 response for POST /orders
Client retries → CDN returns cached 201 (correct!)
Client sends NEW order with DIFFERENT key → CDN returns stale cached 201 (WRONG!)
```

**Rules**:
1. **Never cache POST responses** at CDN/proxy level
2. Idempotency cache is **server-side only** (Redis/DB)
3. Set `Cache-Control: no-store` on mutation responses
4. Idempotency and HTTP caching solve **different problems**

```js
app.post('/orders', async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  // ... idempotent logic ...
});
```

---

## Q18. (Advanced) Design an idempotency middleware that works for any Express route.

```js
const crypto = require('crypto');

function idempotent({ ttl = 86400, required = true } = {}) {
  return async (req, res, next) => {
    if (req.method === 'GET') return next(); // GET is already idempotent

    const key = req.headers['idempotency-key'];
    if (!key) {
      if (required) return res.status(400).json({ error: 'Idempotency-Key required' });
      return next();
    }

    const bodyHash = crypto.createHash('sha256').update(JSON.stringify(req.body)).digest('hex');

    // Check cache
    const cached = await redis.hgetall(`idem:${key}`);
    if (cached.response) {
      if (cached.bodyHash !== bodyHash) {
        return res.status(422).json({ error: 'Key reused with different payload' });
      }
      return res.status(parseInt(cached.statusCode)).json(JSON.parse(cached.response));
    }

    // Lock
    const locked = await redis.set(`idem-lock:${key}`, '1', 'NX', 'EX', 30);
    if (!locked) return res.status(409).json({ error: 'Duplicate request in progress' });

    // Intercept res.json to capture response
    const originalJson = res.json.bind(res);
    res.json = (body) => {
      redis.hmset(`idem:${key}`, {
        response: JSON.stringify(body),
        statusCode: res.statusCode.toString(),
        bodyHash,
      });
      redis.expire(`idem:${key}`, ttl);
      redis.del(`idem-lock:${key}`);
      return originalJson(body);
    };

    next();
  };
}

// Usage
app.post('/payments', idempotent({ ttl: 86400, required: true }), paymentHandler);
app.post('/comments', idempotent({ required: false }), commentHandler);
```

---

## Q19. (Advanced) How do you monitor idempotency in production? What metrics matter?

**Answer**:

```js
// Metrics to track
const metrics = {
  idempotencyHits: new Counter({ name: 'idempotency_cache_hits_total' }),
  idempotencyMisses: new Counter({ name: 'idempotency_cache_misses_total' }),
  idempotencyLockConflicts: new Counter({ name: 'idempotency_lock_conflicts_total' }),
  idempotencyPayloadMismatch: new Counter({ name: 'idempotency_payload_mismatch_total' }),
};

// Dashboard alerts:
// 1. High hit rate on same key → client retry storms (investigate network issues)
// 2. Payload mismatch → client bug or abuse
// 3. Lock conflicts → high concurrency on same key (may need queue)
// 4. Redis errors → fallback to DB (monitor DB load increase)
```

**What to alert on**:
- Hit rate > 50% → too many retries (investigate root cause)
- Payload mismatch spikes → possible bug or attack
- Lock conflict rate increasing → consider request queueing

---

## Q20. (Advanced) Senior red flags for idempotency in code review.

**Answer**:

1. **POST endpoint with no idempotency and side effects** — recipe for double-processing
2. **Idempotency key generated server-side** — defeats the purpose (client must own it)
3. **No TTL on stored results** — storage grows forever
4. **Check-then-act without lock** — race condition between check and process
5. **Only caching success, not errors** — retry after 4xx causes re-processing
6. **Redis-only storage** — Redis restart loses idempotency state → duplicates
7. **No body hash validation** — key reuse with different payload goes undetected
8. **Side effects outside transaction** — email sent but idempotency record not saved (crash = duplicate email)

**Senior interview answer**: "Idempotency is not optional for any state-changing API in a distributed system. I implement it with client-generated keys, Redis for fast lookup, database for durability, distributed locks for concurrent safety, and body hash validation to prevent key misuse."
