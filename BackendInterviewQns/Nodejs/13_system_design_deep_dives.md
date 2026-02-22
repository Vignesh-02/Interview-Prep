# 13. System Design Deep Dives

## Topic Introduction

System design is the most important skill that separates **senior** engineers from mid-level. It's about making **tradeoff decisions** — there's no single right answer. The interviewer evaluates your ability to: clarify requirements, estimate scale, choose components, handle failure modes, and justify decisions.

```
Requirements → Estimation → High-Level Design → Deep Dive → Tradeoffs → Monitoring
```

Every system design follows a pattern: **API design**, **data model**, **compute** (where logic runs), **storage** (how data is persisted), **scaling** (how it grows), and **reliability** (how it survives failures).

This topic covers 20 mini system design problems — each with a Node.js-oriented solution, architecture diagram, and senior-level tradeoffs.

---

## Q1. (Beginner) Design a URL shortener. What components do you need?

```
POST /shorten { url: "https://example.com/very-long-path" } → { short: "abc123" }
GET /abc123 → 301 Redirect to original URL
```

```js
// Core logic
const crypto = require('crypto');

function generateShortCode(id) {
  const chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let code = '';
  while (id > 0) { code = chars[id % 62] + code; id = Math.floor(id / 62); }
  return code || '0';
}

app.post('/shorten', async (req, res) => {
  const result = await db.query('INSERT INTO urls(original_url) VALUES($1) RETURNING id', [req.body.url]);
  const code = generateShortCode(result.rows[0].id);
  await db.query('UPDATE urls SET code = $1 WHERE id = $2', [code, result.rows[0].id]);
  res.json({ short: `https://short.ly/${code}` });
});

app.get('/:code', async (req, res) => {
  const cached = await redis.get(`url:${req.params.code}`);
  if (cached) return res.redirect(301, cached);

  const result = await db.query('SELECT original_url FROM urls WHERE code = $1', [req.params.code]);
  if (!result.rows[0]) return res.status(404).json({ error: 'Not found' });

  await redis.set(`url:${req.params.code}`, result.rows[0].original_url, 'EX', 3600);
  res.redirect(301, result.rows[0].original_url);
});
```

**Architecture**: API → Redis (cache hot URLs) → PostgreSQL (source of truth). CDN for edge caching of redirects.

---

## Q2. (Beginner) Design a basic REST API for a todo app with proper structure.

```js
const express = require('express');
const { Pool } = require('pg');

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const app = express();
app.use(express.json());

// List todos (with pagination)
app.get('/api/todos', async (req, res) => {
  const { cursor, limit = 20 } = req.query;
  const query = cursor
    ? 'SELECT * FROM todos WHERE id < $1 ORDER BY id DESC LIMIT $2'
    : 'SELECT * FROM todos ORDER BY id DESC LIMIT $1';
  const params = cursor ? [cursor, limit] : [limit];
  const todos = await pool.query(query, params);
  res.json({ data: todos.rows, nextCursor: todos.rows[todos.rows.length - 1]?.id });
});

// Create todo
app.post('/api/todos', async (req, res) => {
  const { title } = req.body;
  if (!title?.trim()) return res.status(400).json({ error: 'Title required' });
  const result = await pool.query(
    'INSERT INTO todos(title) VALUES($1) RETURNING *', [title.trim()]
  );
  res.status(201).json(result.rows[0]);
});

// Update todo
app.put('/api/todos/:id', async (req, res) => {
  const result = await pool.query(
    'UPDATE todos SET title = COALESCE($1, title), completed = COALESCE($2, completed), updated_at = NOW() WHERE id = $3 RETURNING *',
    [req.body.title, req.body.completed, req.params.id]
  );
  if (!result.rows[0]) return res.status(404).json({ error: 'Not found' });
  res.json(result.rows[0]);
});

// Delete todo
app.delete('/api/todos/:id', async (req, res) => {
  const result = await pool.query('DELETE FROM todos WHERE id = $1', [req.params.id]);
  if (result.rowCount === 0) return res.status(404).json({ error: 'Not found' });
  res.status(204).end();
});
```

**Answer**: Even a simple API should have: input validation, proper status codes (201, 204, 400, 404), pagination, and parameterized queries.

---

## Q3. (Beginner) Design a rate-limited notification service.

```
API receives notification requests
Queue processes them with per-user rate limits
Delivers via email, SMS, or push
```

```js
// Producer (API)
app.post('/notify', authenticate, async (req, res) => {
  const job = await notificationQueue.add('send', {
    userId: req.user.id,
    channel: req.body.channel, // 'email' | 'sms' | 'push'
    template: req.body.template,
    data: req.body.data,
  }, { priority: req.body.priority || 5 });
  res.status(202).json({ jobId: job.id });
});

// Worker with per-user rate limiting
const worker = new Worker('notifications', async (job) => {
  // Rate limit: max 10 notifications per user per hour
  const key = `notify-rate:${job.data.userId}`;
  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, 3600);
  if (count > 10) throw new Error('User rate limit exceeded');

  switch (job.data.channel) {
    case 'email': await sendEmail(job.data); break;
    case 'sms': await sendSMS(job.data); break;
    case 'push': await sendPush(job.data); break;
  }
}, { connection: redis, concurrency: 10 });
```

---

## Q4. (Beginner) Design a file upload service. How do you handle large files?

```js
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

// Option 1: Direct upload via presigned URL (recommended for large files)
app.post('/uploads/presign', authenticate, async (req, res) => {
  const key = `uploads/${req.user.id}/${Date.now()}-${req.body.filename}`;
  const command = new PutObjectCommand({ Bucket: 'my-bucket', Key: key, ContentType: req.body.contentType });
  const url = await getSignedUrl(s3, command, { expiresIn: 300 });
  res.json({ uploadUrl: url, key });
  // Client uploads directly to S3 — no server bottleneck
});

// Option 2: Stream through server (for processing)
const Busboy = require('busboy');
app.post('/uploads', authenticate, async (req, res) => {
  const bb = Busboy({ headers: req.headers, limits: { fileSize: 100 * 1024 * 1024 } }); // 100MB
  bb.on('file', (name, file, info) => {
    const key = `uploads/${req.user.id}/${Date.now()}-${info.filename}`;
    const upload = new Upload({ client: s3, params: { Bucket: 'my-bucket', Key: key, Body: file } });
    upload.done().then(() => res.json({ key }));
  });
  req.pipe(bb);
});
```

**Answer**: For large files, use **presigned URLs** — the client uploads directly to S3, bypassing your server. For files that need processing (thumbnails, validation), stream through the server using Busboy → S3.

---

## Q5. (Beginner) Design a basic authentication system with JWT.

```js
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

app.post('/auth/register', async (req, res) => {
  const hash = await bcrypt.hash(req.body.password, 12);
  const user = await db.query(
    'INSERT INTO users(email, password_hash) VALUES($1, $2) RETURNING id, email',
    [req.body.email, hash]
  );
  res.status(201).json(user.rows[0]);
});

app.post('/auth/login', async (req, res) => {
  const user = await db.query('SELECT * FROM users WHERE email = $1', [req.body.email]);
  if (!user.rows[0] || !(await bcrypt.compare(req.body.password, user.rows[0].password_hash))) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  const token = jwt.sign({ userId: user.rows[0].id, email: user.rows[0].email },
    process.env.JWT_SECRET, { expiresIn: '24h' }
  );
  res.json({ token });
});

// Middleware
function authenticate(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'Token required' });
  try { req.user = jwt.verify(token, process.env.JWT_SECRET); next(); }
  catch { res.status(401).json({ error: 'Invalid token' }); }
}
```

---

## Q6. (Intermediate) Design a real-time chat system for 10k concurrent users.

```
Clients ←→ WebSocket ←→ Node.js Servers ←→ Redis Pub/Sub ←→ PostgreSQL
```

```js
const WebSocket = require('ws');
const Redis = require('ioredis');

const wss = new WebSocket.Server({ server });
const pub = new Redis();
const sub = new Redis();

// Map userId → WebSocket connection (per server instance)
const connections = new Map();

wss.on('connection', (ws, req) => {
  const userId = authenticate(req);
  connections.set(userId, ws);

  ws.on('message', async (raw) => {
    const msg = JSON.parse(raw);
    // Persist message
    await db.query('INSERT INTO messages(room_id, sender_id, content) VALUES($1,$2,$3)',
      [msg.roomId, userId, msg.content]);
    // Publish to all servers via Redis
    pub.publish('chat', JSON.stringify({ ...msg, senderId: userId }));
  });

  ws.on('close', () => connections.delete(userId));
});

// Receive from Redis and deliver to local connections
sub.subscribe('chat');
sub.on('message', (channel, raw) => {
  const msg = JSON.parse(raw);
  // Get room members, send to those connected to THIS server
  getRoomMembers(msg.roomId).forEach(memberId => {
    const ws = connections.get(memberId);
    if (ws?.readyState === WebSocket.OPEN) ws.send(raw);
  });
});
```

**Scale to 100k+**: Multiple Node.js servers, Redis Pub/Sub for cross-server messaging, horizontal scaling via load balancer with sticky sessions (or use Redis adapter for Socket.IO).

---

## Q7. (Intermediate) Design an API rate limiter as a standalone service.

```js
// Rate limiter microservice
const express = require('express');
const Redis = require('ioredis');
const redis = new Redis();

const app = express();
app.use(express.json());

app.post('/check', async (req, res) => {
  const { key, limit, window } = req.body;
  // Sliding window using Redis sorted set
  const now = Date.now();
  const pipe = redis.pipeline();
  pipe.zremrangebyscore(key, 0, now - window * 1000);
  pipe.zadd(key, now, `${now}:${Math.random()}`);
  pipe.zcard(key);
  pipe.expire(key, window);
  const results = await pipe.exec();
  const count = results[2][1];
  res.json({
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    resetAt: Math.ceil((now + window * 1000) / 1000),
  });
});
```

**Why standalone**: Other services call this via HTTP/gRPC. Central rate limiting state. Can apply different policies per service/user/route.

---

## Q8. (Intermediate) Design a webhook delivery system with retries.

```js
// Webhook registration
app.post('/webhooks', authenticate, async (req, res) => {
  const webhook = await db.query(
    'INSERT INTO webhooks(user_id, url, events, secret) VALUES($1,$2,$3,$4) RETURNING *',
    [req.user.id, req.body.url, req.body.events, crypto.randomBytes(32).toString('hex')]
  );
  res.status(201).json(webhook.rows[0]);
});

// Webhook delivery worker
const worker = new Worker('webhooks', async (job) => {
  const { webhookId, event, payload } = job.data;
  const webhook = await db.query('SELECT * FROM webhooks WHERE id = $1', [webhookId]);
  const { url, secret } = webhook.rows[0];

  const body = JSON.stringify({ event, data: payload, timestamp: Date.now() });
  const signature = crypto.createHmac('sha256', secret).update(body).digest('hex');

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': signature,
    },
    body,
    signal: AbortSignal.timeout(10000), // 10s timeout
  });

  if (!response.ok) throw new Error(`Webhook delivery failed: ${response.status}`);

  await db.query(
    'INSERT INTO webhook_deliveries(webhook_id, status, response_code) VALUES($1,$2,$3)',
    [webhookId, 'delivered', response.status]
  );
}, {
  connection: redis,
  attempts: 5,
  backoff: { type: 'exponential', delay: 60000 }, // 1min, 2min, 4min, 8min, 16min
});
```

---

## Q9. (Intermediate) Design a search API with autocomplete.

```js
// Option 1: PostgreSQL trigram search
// CREATE EXTENSION pg_trgm;
// CREATE INDEX idx_products_name_trgm ON products USING GIN(name gin_trgm_ops);

app.get('/search/autocomplete', async (req, res) => {
  const { q } = req.query;
  if (!q || q.length < 2) return res.json([]);

  // Check cache first
  const cached = await redis.get(`autocomplete:${q.toLowerCase()}`);
  if (cached) return res.json(JSON.parse(cached));

  const results = await pool.query(`
    SELECT id, name, similarity(name, $1) as sim
    FROM products
    WHERE name % $1  -- trigram similarity
    ORDER BY sim DESC
    LIMIT 10
  `, [q]);

  await redis.set(`autocomplete:${q.toLowerCase()}`, JSON.stringify(results.rows), 'EX', 300);
  res.json(results.rows);
});

// Option 2: Redis sorted set for prefix matching
async function addToAutocomplete(term) {
  const prefixes = [];
  for (let i = 1; i <= term.length; i++) {
    prefixes.push(term.toLowerCase().slice(0, i));
  }
  for (const prefix of prefixes) {
    await redis.zadd(`autocomplete:${prefix}`, 0, term.toLowerCase());
  }
}
```

---

## Q10. (Intermediate) Design a job scheduling system (like cron but distributed).

```js
const { Queue, Worker, QueueScheduler } = require('bullmq');
const redis = new Redis();

const scheduledQueue = new Queue('scheduled-jobs', { connection: redis });

// Register recurring jobs
async function setupScheduledJobs() {
  // Daily cleanup at midnight UTC
  await scheduledQueue.add('cleanup-expired-sessions', {}, {
    repeat: { cron: '0 0 * * *' },
  });

  // Every 5 minutes: health check
  await scheduledQueue.add('health-check-external', {}, {
    repeat: { every: 300000 },
  });

  // Monthly report on 1st at 9am
  await scheduledQueue.add('monthly-report', {}, {
    repeat: { cron: '0 9 1 * *' },
  });
}

// Worker processes scheduled jobs
const worker = new Worker('scheduled-jobs', async (job) => {
  switch (job.name) {
    case 'cleanup-expired-sessions':
      await db.query("DELETE FROM sessions WHERE expires_at < NOW()");
      break;
    case 'health-check-external':
      const status = await checkExternalServices();
      if (!status.healthy) await alertTeam(status);
      break;
    case 'monthly-report':
      await generateAndEmailReport();
      break;
  }
}, { connection: redis });
```

**Why BullMQ over cron**: Distributed (multiple servers, only one processes each job), persistent (survives restarts), retry on failure, monitoring/dashboard.

---

## Q11. (Intermediate) Design a leaderboard for a gaming platform (1M users).

```js
// Redis sorted sets — perfect for leaderboards
const LEADERBOARD_KEY = 'leaderboard:global';

// Update score
async function updateScore(userId, score) {
  await redis.zadd(LEADERBOARD_KEY, score, userId);
}

// Get top N
async function getTopN(n = 100) {
  return redis.zrevrange(LEADERBOARD_KEY, 0, n - 1, 'WITHSCORES');
}

// Get user's rank
async function getUserRank(userId) {
  const rank = await redis.zrevrank(LEADERBOARD_KEY, userId); // 0-based
  const score = await redis.zscore(LEADERBOARD_KEY, userId);
  return { rank: rank !== null ? rank + 1 : null, score };
}

// Get users around a specific user (context)
async function getAroundUser(userId, count = 5) {
  const rank = await redis.zrevrank(LEADERBOARD_KEY, userId);
  if (rank === null) return [];
  const start = Math.max(0, rank - count);
  const end = rank + count;
  return redis.zrevrange(LEADERBOARD_KEY, start, end, 'WITHSCORES');
}
```

**Answer**: Redis sorted sets provide O(log n) insert and O(log n) rank lookup. Handles millions of users with sub-millisecond responses. For time-windowed leaderboards (daily/weekly), use separate keys and rotate.

---

## Q12. (Intermediate) Design a feature flag system.

```js
// Feature flag service
class FeatureFlags {
  constructor(redis) { this.redis = redis; }

  async isEnabled(flag, context = {}) {
    const config = await this.getFlag(flag);
    if (!config) return false;
    if (!config.enabled) return false;

    // Percentage rollout
    if (config.percentage < 100) {
      const hash = crypto.createHash('md5')
        .update(`${flag}:${context.userId}`).digest('hex');
      const bucket = parseInt(hash.slice(0, 8), 16) % 100;
      if (bucket >= config.percentage) return false;
    }

    // User whitelist
    if (config.whitelist?.includes(context.userId)) return true;

    // Segment targeting
    if (config.segments) {
      const matchesSegment = config.segments.some(seg =>
        Object.entries(seg).every(([key, val]) => context[key] === val)
      );
      if (!matchesSegment) return false;
    }

    return true;
  }

  async getFlag(name) {
    const cached = await this.redis.get(`flag:${name}`);
    if (cached) return JSON.parse(cached);
    const flag = await db.query('SELECT * FROM feature_flags WHERE name = $1', [name]);
    if (flag.rows[0]) await this.redis.set(`flag:${name}`, JSON.stringify(flag.rows[0]), 'EX', 60);
    return flag.rows[0];
  }
}

// Usage
app.get('/dashboard', async (req, res) => {
  const showNewUI = await flags.isEnabled('new-dashboard', { userId: req.user.id, plan: req.user.plan });
  if (showNewUI) return renderNewDashboard(req, res);
  return renderOldDashboard(req, res);
});
```

---

## Q13. (Advanced) Design an e-commerce checkout system that handles 10k orders/minute.

```
Client → API Gateway → Order Service → Queue → Payment Worker → Inventory Worker
                                                       ↓
                                                 Notification Worker
```

```js
// Order Service — accept order, return immediately
app.post('/checkout', authenticate, idempotent(), async (req, res) => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Reserve inventory (pessimistic lock)
    for (const item of req.body.items) {
      const inv = await client.query(
        'UPDATE inventory SET reserved = reserved + $1 WHERE product_id = $2 AND (quantity - reserved) >= $1 RETURNING *',
        [item.quantity, item.productId]
      );
      if (inv.rowCount === 0) {
        await client.query('ROLLBACK');
        return res.status(409).json({ error: `${item.productId} out of stock` });
      }
    }

    // Create order
    const order = await client.query(
      'INSERT INTO orders(user_id, items, total, status) VALUES($1,$2,$3,$4) RETURNING *',
      [req.user.id, JSON.stringify(req.body.items), req.body.total, 'pending']
    );

    // Outbox event
    await client.query(
      'INSERT INTO outbox(event_type, payload) VALUES($1,$2)',
      ['order.created', JSON.stringify(order.rows[0])]
    );

    await client.query('COMMIT');
    res.status(201).json(order.rows[0]);
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
});
```

**Key decisions**: Idempotency keys prevent double-orders. Inventory reservation in same transaction as order creation. Outbox pattern for reliable event publishing. Payment processing is async via queue.

---

## Q14. (Advanced) Design a distributed task scheduler (like Temporal/AWS Step Functions).

```js
// Workflow definition
const workflow = {
  name: 'order-fulfillment',
  steps: [
    { name: 'validate', handler: 'validateOrder', timeout: 5000, retries: 0 },
    { name: 'charge', handler: 'chargePayment', timeout: 30000, retries: 3 },
    { name: 'fulfill', handler: 'fulfillOrder', timeout: 60000, retries: 2 },
    { name: 'notify', handler: 'sendConfirmation', timeout: 10000, retries: 5 },
  ],
  onFailure: 'compensate', // rollback strategy
};

// Orchestrator
async function executeWorkflow(workflowDef, input) {
  const executionId = crypto.randomUUID();
  const completed = [];

  for (const step of workflowDef.steps) {
    const job = await taskQueue.add(step.handler, { ...input, executionId }, {
      attempts: step.retries + 1,
      timeout: step.timeout,
    });

    try {
      const result = await job.waitUntilFinished(queueEvents, step.timeout);
      completed.push({ step: step.name, result });
      input = { ...input, ...result };
    } catch (err) {
      // Run compensating actions
      for (const done of completed.reverse()) {
        await taskQueue.add(`compensate_${done.step}`, { ...input, error: err.message });
      }
      throw err;
    }
  }

  return input;
}
```

---

## Q15. (Advanced) Design a multi-tenant SaaS backend where tenants are isolated.

```js
// Strategy 1: Shared database, tenant column (simplest, least isolated)
app.use(authenticate);
app.use((req, res, next) => {
  req.tenantId = req.user.tenantId; // from JWT
  next();
});

app.get('/api/projects', async (req, res) => {
  // Every query MUST include tenant filter
  const projects = await pool.query(
    'SELECT * FROM projects WHERE tenant_id = $1', [req.tenantId]
  );
  res.json(projects.rows);
});

// Strategy 2: Schema per tenant (medium isolation)
app.use((req, res, next) => {
  req.schema = `tenant_${req.tenantId}`;
  next();
});
async function tenantQuery(schema, sql, params) {
  return pool.query(`SET search_path TO ${schema}; ${sql}`, params);
}

// Strategy 3: Database per tenant (strongest isolation, hardest to manage)
function getTenantPool(tenantId) {
  return new Pool({ connectionString: `postgresql://localhost/${tenantId}` });
}
```

| Strategy | Isolation | Complexity | Cost |
|----------|-----------|------------|------|
| Shared DB + tenant column | Low | Low | Low |
| Schema per tenant | Medium | Medium | Medium |
| Database per tenant | High | High | High |

---

## Q16. (Advanced) Design an event-driven architecture for an e-commerce platform.

```
Order Service ──publish──► [OrderCreated] ──► Payment Service
                                           ──► Inventory Service
                                           ──► Notification Service
                                           ──► Analytics Service

Payment Service ──publish──► [PaymentCompleted] ──► Order Service (update status)
                                                 ──► Notification Service
```

```js
// Event bus (Kafka)
const { Kafka } = require('kafkajs');
const kafka = new Kafka({ brokers: ['kafka:9092'] });

// Order Service publishes
async function createOrder(data) {
  const order = await db.query('INSERT INTO orders ... RETURNING *', [data]);
  await producer.send({
    topic: 'order-events',
    messages: [{
      key: order.rows[0].id.toString(),
      value: JSON.stringify({ type: 'OrderCreated', data: order.rows[0] }),
    }],
  });
  return order.rows[0];
}

// Each service has its own consumer group
// Payment Service consumer
const paymentConsumer = kafka.consumer({ groupId: 'payment-service' });
await paymentConsumer.subscribe({ topic: 'order-events' });
await paymentConsumer.run({
  eachMessage: async ({ message }) => {
    const event = JSON.parse(message.value);
    if (event.type === 'OrderCreated') {
      await chargeCustomer(event.data);
      await producer.send({
        topic: 'payment-events',
        messages: [{ value: JSON.stringify({ type: 'PaymentCompleted', orderId: event.data.id }) }],
      });
    }
  },
});
```

---

## Q17. (Advanced) Design a distributed configuration service (like consul/etcd).

```js
// Config service with versioning and watch support
app.get('/config/:key', async (req, res) => {
  const config = await redis.hgetall(`config:${req.params.key}`);
  res.json({ key: req.params.key, value: config.value, version: config.version });
});

app.put('/config/:key', async (req, res) => {
  const key = `config:${req.params.key}`;
  const version = await redis.hincrby(key, 'version', 1);
  await redis.hset(key, 'value', JSON.stringify(req.body.value));

  // Notify all watchers
  await redis.publish('config-changes', JSON.stringify({
    key: req.params.key, value: req.body.value, version,
  }));
  res.json({ version });
});

// Watch for changes (SSE)
app.get('/config/:key/watch', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  const sub = new Redis();
  sub.subscribe('config-changes');
  sub.on('message', (channel, msg) => {
    const change = JSON.parse(msg);
    if (change.key === req.params.key) {
      res.write(`data: ${msg}\n\n`);
    }
  });
  req.on('close', () => sub.unsubscribe());
});
```

---

## Q18. (Advanced) Design an API that handles 1M writes per second (event ingestion).

```
Clients → Load Balancer → Ingestion API (Node.js)
                              │ batch writes
                              ▼
                         Kafka (buffer)
                              │
                         Stream Processor
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               TimescaleDB  S3 (raw)  ClickHouse
```

```js
// Ingestion API — batch and buffer, don't write to DB per-request
const buffer = [];
const BATCH_SIZE = 1000;
const FLUSH_INTERVAL = 1000; // 1 second

app.post('/events', (req, res) => {
  buffer.push(req.body);
  res.status(202).end(); // immediate response
});

// Flush buffer to Kafka periodically
setInterval(async () => {
  if (buffer.length === 0) return;
  const batch = buffer.splice(0, BATCH_SIZE);
  await producer.send({
    topic: 'events',
    messages: batch.map(e => ({ value: JSON.stringify(e) })),
  });
}, FLUSH_INTERVAL);
```

**Answer**: For extreme write throughput: buffer in-memory, batch writes to Kafka, process with stream consumers. Never write to a relational DB per-request at 1M/s — use columnar stores (ClickHouse, TimescaleDB) for analytics.

---

## Q19. (Advanced) Design a content delivery pipeline for a social media feed.

```
User posts → Write API → PostgreSQL (source of truth)
                       → Fan-out service → Redis sorted sets (per-user feeds)
                       → CDN invalidation (media)

User reads feed → Feed API → Redis → (fallback) PostgreSQL
```

```js
// Write path: fan-out on write (good for < 10k followers)
async function createPost(userId, content) {
  const post = await db.query('INSERT INTO posts(user_id, content) VALUES($1,$2) RETURNING *', [userId, content]);

  // Fan out to followers' timelines
  const followers = await db.query('SELECT follower_id FROM follows WHERE following_id = $1', [userId]);
  const pipeline = redis.pipeline();
  for (const { follower_id } of followers.rows) {
    pipeline.zadd(`feed:${follower_id}`, post.rows[0].created_at.getTime(), post.rows[0].id);
    pipeline.zremrangebyrank(`feed:${follower_id}`, 0, -501); // keep latest 500
  }
  await pipeline.exec();

  return post.rows[0];
}

// Read path: just read from Redis
async function getFeed(userId, cursor, limit = 20) {
  const end = cursor ? cursor - 1 : '+inf';
  const postIds = await redis.zrevrangebyscore(`feed:${userId}`, end, '-inf', 'LIMIT', 0, limit);
  if (postIds.length === 0) return [];
  const posts = await db.query('SELECT * FROM posts WHERE id = ANY($1)', [postIds]);
  return posts.rows;
}
```

**Tradeoff**: Fan-out on write works for users with < 10k followers. For celebrities (millions of followers), use **fan-out on read** — don't pre-compute their posts in every follower's feed.

---

## Q20. (Advanced) Senior system design red flags to avoid.

**Answer**:

1. **No capacity estimation** — "it should handle any traffic" is not a design
2. **Single point of failure** — one DB, no replicas, no failover
3. **Synchronous everything** — calling 5 services sequentially in one request
4. **No caching layer** — every request hits the database
5. **Monolith for everything or microservices for everything** — pick the right boundary
6. **No idempotency on write APIs** — retries cause duplicate data
7. **No monitoring or alerting** — can't detect or debug issues
8. **Over-engineering for day 1** — building for 10M users when you have 100
9. **Ignoring data consistency requirements** — using eventual consistency for payments
10. **No graceful degradation** — one slow dependency takes down the entire system

**Senior interview answer**: "I design systems by first understanding the requirements and estimating scale, then choosing the simplest architecture that meets those requirements. I prioritize reliability through caching, queues, circuit breakers, and observability. I avoid premature optimization but design for the next order of magnitude of growth."
