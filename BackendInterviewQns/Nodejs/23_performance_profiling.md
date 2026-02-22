# 23. Performance Optimization & Profiling

## Topic Introduction

Performance is not about premature optimization — it's about **measuring first, then optimizing bottlenecks**. A senior engineer profiles before coding, optimizes the right thing, and knows when "good enough" is the right answer.

```
Performance workflow:
  Measure → Identify bottleneck → Optimize → Measure again → Repeat
  (never skip step 1)
```

Node.js performance characteristics: single-threaded event loop (fast I/O, bad for CPU), V8 JIT compilation, garbage collection pauses, event loop blocking. Most Node.js perf issues are: (1) blocking the event loop, (2) memory leaks, (3) N+1 queries, (4) missing indexes.

**Go/Java tradeoff**: Go compiles to native code (no JIT warmup), uses goroutines (cheap concurrency). Java has the JVM with sophisticated JIT and GC. Node.js V8 is fast for I/O but weaker for CPU. For CPU-heavy work, consider offloading to Go/Rust services or Worker Threads.

---

## Q1. (Beginner) How do you measure the performance of a Node.js API endpoint?

```js
// 1. Simple timing
app.use((req, res, next) => {
  const start = process.hrtime.bigint();
  res.on('finish', () => {
    const duration = Number(process.hrtime.bigint() - start) / 1e6;
    console.log(`${req.method} ${req.path} ${res.statusCode} ${duration.toFixed(2)}ms`);
  });
  next();
});

// 2. Prometheus histogram for production
const httpDuration = new Histogram({
  name: 'http_request_duration_ms',
  help: 'HTTP request duration in milliseconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [5, 10, 25, 50, 100, 250, 500, 1000, 2500],
});

app.use((req, res, next) => {
  const end = httpDuration.startTimer();
  res.on('finish', () => {
    end({ method: req.method, route: req.route?.path || req.path, status: res.statusCode });
  });
  next();
});
```

**Key metrics**: p50 (median), p95 (95th percentile), p99 (99th percentile), throughput (req/s), error rate. Focus on p95/p99 — these affect real users.

---

## Q2. (Beginner) What tools are available for profiling Node.js?

**Answer**:

| Tool | What it measures | When to use |
|---|---|---|
| `--prof` flag | CPU profiling (V8) | Find slow functions |
| `--inspect` + Chrome DevTools | CPU, Memory, Heap | Interactive debugging |
| `clinic.js` | Event loop, I/O, flame graph | Automated diagnostics |
| `0x` | Flame graphs | Visual CPU profiling |
| `perf_hooks` | Custom timings | Measure specific operations |
| `v8.getHeapStatistics()` | Memory usage | Memory monitoring |
| `process.memoryUsage()` | RSS, heap, external | Quick memory check |

```js
// Using perf_hooks for custom measurements
const { performance, PerformanceObserver } = require('perf_hooks');

// Measure specific operations
performance.mark('db-query-start');
const users = await db.query('SELECT * FROM users');
performance.mark('db-query-end');
performance.measure('db-query', 'db-query-start', 'db-query-end');

// Observer collects measurements
const obs = new PerformanceObserver((items) => {
  items.getEntries().forEach((entry) => {
    console.log(`${entry.name}: ${entry.duration.toFixed(2)}ms`);
  });
});
obs.observe({ entryTypes: ['measure'] });
```

---

## Q3. (Beginner) What is event loop lag and why does it matter?

```js
// Event loop lag = time between when a callback is scheduled and when it runs
// High lag = your server is unresponsive

// Measure event loop lag
function measureEventLoopLag() {
  const start = process.hrtime.bigint();
  setImmediate(() => {
    const lag = Number(process.hrtime.bigint() - start) / 1e6;
    eventLoopLagGauge.set(lag); // Prometheus metric
    if (lag > 100) console.warn(`Event loop lag: ${lag.toFixed(2)}ms`);
  });
}
setInterval(measureEventLoopLag, 1000);

// Using monitorEventLoopDelay (built-in, more accurate)
const { monitorEventLoopDelay } = require('perf_hooks');
const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();

setInterval(() => {
  console.log(`Event loop delay: min=${h.min/1e6}ms p50=${h.percentile(50)/1e6}ms p99=${h.percentile(99)/1e6}ms`);
  h.reset();
}, 5000);
```

**Answer**: Event loop lag >100ms means your server is struggling. Common causes: synchronous operations (JSON.parse of large objects, crypto, regex), unoptimized database queries, too many in-flight requests. Target: <10ms p99.

---

## Q4. (Beginner) How do you identify and fix N+1 query problems?

```js
// N+1 PROBLEM:
app.get('/orders', async (req, res) => {
  const orders = await db.query('SELECT * FROM orders'); // 1 query

  for (const order of orders) {
    // N queries (one per order!)
    order.customer = await db.query('SELECT * FROM users WHERE id = $1', [order.user_id]);
    order.items = await db.query('SELECT * FROM order_items WHERE order_id = $1', [order.id]);
  }
  // 100 orders = 201 queries!

  res.json(orders);
});

// FIX 1: JOIN (1 query)
app.get('/orders', async (req, res) => {
  const orders = await db.query(`
    SELECT o.*, u.name as customer_name,
      json_agg(json_build_object('product', oi.product_name, 'qty', oi.quantity)) as items
    FROM orders o
    JOIN users u ON o.user_id = u.id
    LEFT JOIN order_items oi ON oi.order_id = o.id
    GROUP BY o.id, u.name
  `);
  res.json(orders);
});

// FIX 2: Batch loading (2 queries)
const orders = await db.query('SELECT * FROM orders');
const orderIds = orders.map(o => o.id);
const userIds = orders.map(o => o.user_id);

const [users, items] = await Promise.all([
  db.query('SELECT * FROM users WHERE id = ANY($1)', [userIds]),
  db.query('SELECT * FROM order_items WHERE order_id = ANY($1)', [orderIds]),
]);

// Map results
const userMap = new Map(users.map(u => [u.id, u]));
const itemMap = new Map();
items.forEach(i => {
  if (!itemMap.has(i.order_id)) itemMap.set(i.order_id, []);
  itemMap.get(i.order_id).push(i);
});

orders.forEach(o => {
  o.customer = userMap.get(o.user_id);
  o.items = itemMap.get(o.id) || [];
});
```

---

## Q5. (Beginner) How does connection pooling improve performance?

```js
// WITHOUT pool: new connection per query (~50ms overhead each)
async function query(sql) {
  const client = new Client(connectionString); // new TCP connection
  await client.connect();                       // TLS handshake, auth
  const result = await client.query(sql);       // actual query
  await client.end();                           // close connection
  return result; // total: query time + 50ms overhead
}

// WITH pool: reuse connections (near-zero overhead)
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,              // max connections in pool
  min: 5,               // keep 5 idle connections ready
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

async function query(sql, params) {
  return pool.query(sql, params); // reuses existing connection
}

// Monitor pool health
setInterval(() => {
  console.log({
    total: pool.totalCount,
    idle: pool.idleCount,
    waiting: pool.waitingCount, // requests waiting for connection
  });
}, 10000);
```

**Tuning pool size**: `max = (core_count * 2) + effective_spindle_count`. For a 4-core server with SSD: `max = 10`. Too many connections → context switching overhead. Too few → requests queue.

---

## Q6. (Intermediate) How do you use `EXPLAIN ANALYZE` to optimize slow queries?

```sql
-- Find the slow query
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT o.*, u.name
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at > '2024-01-01'
  AND o.status = 'pending'
ORDER BY o.created_at DESC
LIMIT 20;

-- Output (BAD):
-- Seq Scan on orders  (cost=0..50000 rows=100000 actual time=0.01..450ms)
--   Filter: (created_at > '2024-01-01' AND status = 'pending')
--   Rows Removed by Filter: 900000
-- → FULL TABLE SCAN! Reading 1M rows to find 100k

-- FIX: Add composite index
CREATE INDEX idx_orders_status_date ON orders(status, created_at DESC);

-- Output (GOOD):
-- Index Scan using idx_orders_status_date on orders (actual time=0.02..2.5ms)
--   Index Cond: (status = 'pending' AND created_at > '2024-01-01')
-- → INDEX SCAN! Reads only matching rows
```

```js
// Automated slow query detection in Node.js
const pool = new Pool({ ... });

// Log slow queries
pool.on('query', (query) => {
  const start = Date.now();
  query.on('end', () => {
    const duration = Date.now() - start;
    if (duration > 100) {
      console.warn(`Slow query (${duration}ms):`, query.text, query.values);
    }
  });
});

// Or with Knex
const knex = require('knex')({
  client: 'pg',
  connection: process.env.DATABASE_URL,
  pool: { min: 2, max: 20 },
});

knex.on('query', (query) => {
  query._startTime = Date.now();
});
knex.on('query-response', (response, query) => {
  const duration = Date.now() - query._startTime;
  if (duration > 100) {
    console.warn(`Slow query (${duration}ms): ${query.sql}`);
  }
});
```

---

## Q7. (Intermediate) How do you detect and fix memory leaks in Node.js?

```js
// Step 1: Monitor memory usage
setInterval(() => {
  const { heapUsed, heapTotal, rss, external } = process.memoryUsage();
  console.log({
    heapUsed: `${(heapUsed / 1024 / 1024).toFixed(1)}MB`,
    heapTotal: `${(heapTotal / 1024 / 1024).toFixed(1)}MB`,
    rss: `${(rss / 1024 / 1024).toFixed(1)}MB`,
  });
  // If heapUsed grows continuously → memory leak!
}, 30000);

// Step 2: Take heap snapshots
const v8 = require('v8');
// Before: take snapshot at startup
v8.writeHeapSnapshot(); // writes to current dir

// After 1 hour: take another snapshot
setTimeout(() => v8.writeHeapSnapshot(), 60 * 60 * 1000);

// Step 3: Compare snapshots in Chrome DevTools
// Memory tab → Load both snapshots → Compare → See what's growing

// Common leak patterns:
// 1. Growing Map/Set without cleanup
const cache = new Map(); // grows forever!
function getUser(id) {
  if (!cache.has(id)) cache.set(id, fetchUser(id));
  return cache.get(id);
}
// FIX: use LRU cache with max size
const { LRUCache } = require('lru-cache');
const cache = new LRUCache({ max: 1000 });

// 2. Event listeners not removed
emitter.on('data', handler); // called in a loop — listeners pile up
// FIX: use once() or removeListener()

// 3. Closures holding references
function createProcessor() {
  const hugeData = loadGBofData(); // captured by closure
  return (input) => process(input, hugeData);
}
// FIX: only capture what you need
```

---

## Q8. (Intermediate) How do you optimize JSON serialization/deserialization?

```js
// JSON.parse/stringify are synchronous and can block the event loop

// Problem: parsing 50MB JSON blocks event loop for 500ms
const data = JSON.parse(hugeJsonString); // BLOCKS!

// Solution 1: Use streaming JSON parser
const { parser } = require('stream-json');
const { streamArray } = require('stream-json/streamers/StreamArray');
const fs = require('fs');

const pipeline = fs.createReadStream('huge.json')
  .pipe(parser())
  .pipe(streamArray());

pipeline.on('data', ({ value }) => {
  processItem(value); // process one item at a time
});

// Solution 2: Use faster serializer
const fastJson = require('fast-json-stringify');

const stringify = fastJson({
  type: 'object',
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    email: { type: 'string' },
    orders: {
      type: 'array',
      items: { type: 'object', properties: { id: { type: 'string' }, total: { type: 'number' } } },
    },
  },
});

// 2-5x faster than JSON.stringify for known schemas
const json = stringify(userData);

// Solution 3: Use Protocol Buffers for internal communication
// 5-10x smaller than JSON, 10-20x faster to serialize
const protobuf = require('protobufjs');
const root = await protobuf.load('user.proto');
const UserMessage = root.lookupType('User');
const buffer = UserMessage.encode(userData).finish(); // binary, tiny, fast
```

---

## Q9. (Intermediate) How do you implement response compression?

```js
const compression = require('compression');

// Enable gzip/brotli compression
app.use(compression({
  level: 6,            // compression level (1=fast, 9=best compression)
  threshold: 1024,     // only compress responses > 1KB
  filter: (req, res) => {
    if (req.headers['x-no-compression']) return false;
    return compression.filter(req, res);
  },
}));

// Result: 100KB JSON → ~10KB compressed (90% reduction!)

// For static files, pre-compress at build time
// nginx:
// gzip_static on;  # serve pre-compressed .gz files
// brotli_static on; # serve pre-compressed .br files
```

---

## Q10. (Intermediate) How do you use caching to improve API performance?

```js
// Multi-layer caching strategy

// Layer 1: In-memory cache (fastest, limited size)
const { LRUCache } = require('lru-cache');
const localCache = new LRUCache({ max: 1000, ttl: 60 * 1000 });

// Layer 2: Redis cache (shared across instances)
const redis = require('ioredis');
const redisClient = new redis();

async function getCachedUser(userId) {
  // Check local cache first (~0.01ms)
  const local = localCache.get(`user:${userId}`);
  if (local) return local;

  // Check Redis (~1ms)
  const cached = await redisClient.get(`user:${userId}`);
  if (cached) {
    const user = JSON.parse(cached);
    localCache.set(`user:${userId}`, user); // populate local cache
    return user;
  }

  // Cache miss: fetch from DB (~10-50ms)
  const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
  if (user) {
    await redisClient.set(`user:${userId}`, JSON.stringify(user), 'EX', 300);
    localCache.set(`user:${userId}`, user);
  }
  return user;
}

// Cache invalidation on write
async function updateUser(userId, data) {
  await db.query('UPDATE users SET name = $1 WHERE id = $2', [data.name, userId]);
  await redisClient.del(`user:${userId}`);  // invalidate Redis
  localCache.delete(`user:${userId}`);       // invalidate local
}
```

---

## Q11. (Intermediate) How do you optimize database query patterns?

```js
// 1. Select only needed columns
// BAD: SELECT * FROM users (fetches avatar blob, bio, etc.)
const user = await db.query('SELECT * FROM users WHERE id = $1', [id]);

// GOOD: Select only what you need
const user = await db.query('SELECT id, name, email FROM users WHERE id = $1', [id]);

// 2. Use cursor-based pagination (not OFFSET)
// BAD: OFFSET gets slower as page number increases
const page10 = await db.query('SELECT * FROM orders ORDER BY created_at DESC OFFSET 200 LIMIT 20');
// Scans and discards 200 rows!

// GOOD: cursor-based
const nextPage = await db.query(
  'SELECT * FROM orders WHERE created_at < $1 ORDER BY created_at DESC LIMIT 20',
  [lastSeenCreatedAt]
);
// Uses index, always fast regardless of page number

// 3. Batch operations
// BAD: 100 individual inserts
for (const item of items) {
  await db.query('INSERT INTO order_items ...', [item.productId, item.qty]);
}

// GOOD: single batch insert
await db.query(
  'INSERT INTO order_items (product_id, quantity) SELECT * FROM unnest($1::uuid[], $2::int[])',
  [items.map(i => i.productId), items.map(i => i.qty)]
);

// 4. Use prepared statements (avoid re-parsing)
const { Pool } = require('pg');
const pool = new Pool();
// pg module automatically prepares statements that are used multiple times
```

---

## Q12. (Intermediate) How do you use Worker Threads for CPU-intensive tasks?

```js
// Main thread: handles HTTP requests
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

if (isMainThread) {
  app.post('/reports/generate', async (req, res) => {
    try {
      const result = await runInWorker('./workers/reportGenerator.js', {
        startDate: req.body.startDate,
        endDate: req.body.endDate,
      });
      res.json(result);
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  function runInWorker(workerFile, data) {
    return new Promise((resolve, reject) => {
      const worker = new Worker(workerFile, { workerData: data });
      worker.on('message', resolve);
      worker.on('error', reject);
      worker.on('exit', (code) => {
        if (code !== 0) reject(new Error(`Worker exited with code ${code}`));
      });
    });
  }
} else {
  // Worker thread: CPU-intensive work
  // workers/reportGenerator.js
  const { workerData, parentPort } = require('worker_threads');

  async function generateReport(startDate, endDate) {
    // Heavy computation: aggregate data, generate PDF, etc.
    const data = await fetchData(startDate, endDate);
    const aggregated = heavyAggregation(data); // CPU-bound
    const pdf = generatePDF(aggregated);        // CPU-bound
    return { url: await uploadToS3(pdf) };
  }

  generateReport(workerData.startDate, workerData.endDate)
    .then(result => parentPort.postMessage(result));
}

// Worker pool for reuse (avoid creating new workers per request)
const { Pool } = require('worker-threads-pool');
const workerPool = new Pool({ max: 4 }); // 4 worker threads
```

---

## Q13. (Advanced) How do you profile and optimize a Node.js application end-to-end?

```bash
# Step 1: CPU profiling with --prof
node --prof app.js
# Run load test against the app
# Stop app — generates isolate-*.log file
node --prof-process isolate-*.log > profile.txt
# Look for "ticks" on hot functions

# Step 2: Use clinic.js for automated analysis
npx clinic doctor -- node app.js
# Run load test, then Ctrl+C
# Opens browser with analysis: event loop delay, CPU, memory

# Step 3: Flame graph with 0x
npx 0x app.js
# Run load test, then Ctrl+C
# Opens flame graph showing time spent in each function
```

```js
// Step 4: Add custom tracing to find bottlenecks
const { AsyncLocalStorage } = require('async_hooks');
const als = new AsyncLocalStorage();

app.use((req, res, next) => {
  const timings = {};
  als.run({ timings }, () => {
    res.on('finish', () => {
      if (Object.values(timings).some(t => t > 50)) {
        console.warn('Slow request:', { path: req.path, timings });
      }
    });
    next();
  });
});

// Instrument slow operations
async function timedQuery(name, queryFn) {
  const start = performance.now();
  try {
    return await queryFn();
  } finally {
    const duration = performance.now() - start;
    const store = als.getStore();
    if (store) store.timings[name] = duration;
  }
}

// Usage
const users = await timedQuery('fetch-users', () => db.query('SELECT * FROM users'));
```

---

## Q14. (Advanced) How do you handle the "thundering herd" problem?

**Scenario**: Cache key expires. 1000 concurrent requests all see cache miss and all query the database simultaneously.

```js
// Problem: cache stampede / thundering herd
async function getProduct(id) {
  const cached = await redis.get(`product:${id}`);
  if (cached) return JSON.parse(cached);

  // 1000 requests hit this simultaneously!
  const product = await db.query('SELECT * FROM products WHERE id = $1', [id]); // DB overloaded
  await redis.set(`product:${id}`, JSON.stringify(product), 'EX', 300);
  return product;
}

// Solution 1: Request coalescing (single-flight)
const inflight = new Map();

async function getProductCoalesced(id) {
  const cached = await redis.get(`product:${id}`);
  if (cached) return JSON.parse(cached);

  const key = `product:${id}`;
  if (inflight.has(key)) {
    return inflight.get(key); // wait for the same promise
  }

  const promise = (async () => {
    const product = await db.query('SELECT * FROM products WHERE id = $1', [id]);
    await redis.set(key, JSON.stringify(product), 'EX', 300);
    return product;
  })();

  inflight.set(key, promise);
  try {
    return await promise;
  } finally {
    inflight.delete(key);
  }
}

// Solution 2: Distributed lock
async function getProductLocked(id) {
  const cached = await redis.get(`product:${id}`);
  if (cached) return JSON.parse(cached);

  const lockKey = `lock:product:${id}`;
  const locked = await redis.set(lockKey, '1', 'PX', 5000, 'NX');

  if (locked) {
    // Winner: fetch and cache
    const product = await db.query('SELECT * FROM products WHERE id = $1', [id]);
    await redis.set(`product:${id}`, JSON.stringify(product), 'EX', 300);
    await redis.del(lockKey);
    return product;
  } else {
    // Loser: wait and retry cache
    await new Promise(r => setTimeout(r, 100));
    return getProductLocked(id);
  }
}

// Solution 3: Stale-while-revalidate
async function getProductStale(id) {
  const cached = await redis.get(`product:${id}`);
  if (cached) {
    const data = JSON.parse(cached);
    if (data._expiresAt < Date.now()) {
      // Stale: return stale data, refresh in background
      refreshCache(id); // fire and forget
    }
    return data;
  }
  return fetchAndCache(id);
}
```

---

## Q15. (Advanced) How do you optimize Node.js for high throughput (100k req/s)?

```js
// 1. Use cluster mode (utilize all CPU cores)
const cluster = require('cluster');
const numCPUs = require('os').cpus().length;

if (cluster.isPrimary) {
  for (let i = 0; i < numCPUs; i++) cluster.fork();
  cluster.on('exit', (worker) => cluster.fork()); // auto-restart
} else {
  app.listen(3000);
}

// 2. Use Fastify instead of Express (2-5x faster)
const fastify = require('fastify')({ logger: false });
fastify.get('/api/users/:id', async (req) => {
  return cache.get(`user:${req.params.id}`);
});

// 3. Pre-serialize responses (avoid JSON.stringify per request)
const fastJson = require('fast-json-stringify');
const serialize = fastJson({
  type: 'object',
  properties: { id: { type: 'string' }, name: { type: 'string' } },
});

// 4. Use HTTP keep-alive
const http = require('http');
const agent = new http.Agent({ keepAlive: true, maxSockets: 100 });

// 5. Tune the kernel
// /etc/sysctl.conf:
// net.core.somaxconn = 65535
// net.ipv4.tcp_max_syn_backlog = 65535
// fs.file-max = 2097152

// 6. Disable unnecessary middleware
// Remove: morgan (logging), cors (if behind proxy), helmet (if behind CDN)
// Every middleware adds ~0.1ms latency × 100k req/s = 10 seconds wasted/second
```

---

## Q16. (Advanced) How do you diagnose and fix V8 garbage collection issues?

```js
// Expose GC metrics
const v8 = require('v8');

// Enable GC events
const { PerformanceObserver } = require('perf_hooks');
const obs = new PerformanceObserver((list) => {
  list.getEntries().forEach((entry) => {
    if (entry.entryType === 'gc') {
      console.log(`GC: ${entry.detail.kind} took ${entry.duration.toFixed(2)}ms`);
      // kind: 1=Scavenge (young gen), 2=Major (old gen), 4=Incremental
      if (entry.duration > 100) {
        console.warn('LONG GC PAUSE:', entry.detail);
      }
    }
  });
});
obs.observe({ entryTypes: ['gc'] });

// Tune V8 heap (for high-memory workloads)
// node --max-old-space-size=4096 app.js  (4GB max heap)
// node --expose-gc app.js  (allow manual GC for testing)

// Reduce GC pressure:
// 1. Reuse objects instead of creating new ones
// BAD:
function transform(items) {
  return items.map(item => ({ ...item, processed: true })); // creates N new objects
}
// BETTER: mutate in place (if safe)
function transform(items) {
  items.forEach(item => { item.processed = true; });
  return items;
}

// 2. Use typed arrays for numeric data
// BAD: array of objects
const points = [{ x: 1, y: 2 }, { x: 3, y: 4 }]; // each object is a heap allocation
// BETTER: typed array (contiguous memory, no GC overhead)
const xs = new Float64Array([1, 3]);
const ys = new Float64Array([2, 4]);

// 3. Use Buffer.allocUnsafe() for performance-critical paths
// Buffer.alloc() zeros memory. Buffer.allocUnsafe() doesn't (faster but may contain old data)
const buf = Buffer.allocUnsafe(1024); // only if you'll write to all bytes
```

---

## Q17. (Advanced) How do you perform load testing and establish performance baselines?

```js
// Using autocannon (Node.js built-in load tester)
// npx autocannon -c 100 -d 30 http://localhost:3000/api/users
// -c = connections, -d = duration in seconds

// Programmatic load test
const autocannon = require('autocannon');

const result = await autocannon({
  url: 'http://localhost:3000/api/users',
  connections: 100,
  duration: 30,
  headers: { 'Authorization': 'Bearer test-token' },
});

console.log({
  requests: result.requests.total,
  throughput: `${result.requests.average} req/s`,
  latency_p50: `${result.latency.p50}ms`,
  latency_p95: `${result.latency.p95}ms`,
  latency_p99: `${result.latency.p99}ms`,
  errors: result.errors,
});

// Establish baselines and alert on regression
const BASELINE = { p95: 50, p99: 200, throughput: 5000 };

if (result.latency.p95 > BASELINE.p95 * 1.2) {
  console.error('PERFORMANCE REGRESSION: p95 latency 20% above baseline');
}
```

---

## Q18. (Advanced) How do you optimize a Node.js app serving 10 million requests per day?

**Answer**: 10M req/day = ~115 req/s average, ~500 req/s peak.

```js
// 1. Architecture
// Load Balancer → 2-4 Node.js instances (cluster mode) → Redis cache → PostgreSQL

// 2. Caching strategy
// Cache hit rate target: >90%
// Hot data in local LRU cache (0.01ms)
// Warm data in Redis (1ms)
// Cold data in PostgreSQL (10-50ms)

// 3. Connection pooling
const pool = new Pool({ max: 20, idleTimeoutMillis: 30000 });

// 4. Response optimization
app.use(compression()); // gzip
app.use(express.json({ limit: '1mb' })); // limit body size

// 5. Static assets via CDN (not Node.js)
// 6. Database read replicas for read-heavy endpoints
// 7. Rate limiting to protect from abuse
// 8. Health checks for load balancer

// 9. Monitoring dashboard
// - p95 latency < 100ms
// - Error rate < 0.1%
// - Event loop lag < 10ms
// - Memory usage stable (no growing trend)
// - Connection pool utilization < 80%
// - Cache hit rate > 90%
```

---

## Q19. (Advanced) How do you benchmark and compare Node.js with Go for the same API?

```js
// Node.js (Fastify)
const fastify = require('fastify')();
fastify.get('/api/fibonacci/:n', (req) => {
  const n = parseInt(req.params.n);
  return { result: fibonacci(n) };
});

function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
```

```go
// Go equivalent
func main() {
    http.HandleFunc("/api/fibonacci/", func(w http.ResponseWriter, r *http.Request) {
        n, _ := strconv.Atoi(strings.TrimPrefix(r.URL.Path, "/api/fibonacci/"))
        json.NewEncoder(w).Encode(map[string]int{"result": fibonacci(n)})
    })
    http.ListenAndServe(":3000", nil)
}
```

| Metric | Node.js (Fastify) | Go (net/http) |
|---|---|---|
| I/O-bound (DB fetch) | ~50k req/s | ~60k req/s |
| CPU-bound (fib 30) | ~200 req/s | ~8000 req/s |
| Memory usage (idle) | ~50MB | ~10MB |
| Startup time | ~500ms | ~10ms |
| Cold start (serverless) | ~200ms | ~5ms |

**Conclusion**: Node.js is competitive for I/O-bound APIs. For CPU-heavy work, Go is 10-40x faster. Use Node.js for most APIs, offload CPU-intensive work to Go/Rust microservices or Worker Threads.

---

## Q20. (Advanced) Senior red flags in performance.

**Answer**:

1. **Premature optimization** — optimizing without profiling first
2. **No connection pooling** — creating new DB connections per request
3. **Blocking the event loop** — synchronous file I/O, CPU-heavy JSON parsing
4. **N+1 queries** — 100 orders = 201 database queries
5. **No caching** — fetching the same data from DB thousands of times
6. **SELECT *** — fetching 50 columns when you need 3
7. **OFFSET pagination** — gets slower as page number increases
8. **No monitoring** — can't optimize what you can't measure
9. **Ignoring p99 latency** — average looks fine, but 1% of users wait 10 seconds
10. **No load testing** — discovering capacity limits in production

**Senior interview answer**: "I always profile before optimizing — using clinic.js for diagnostics, EXPLAIN ANALYZE for queries, and Prometheus for production metrics. My optimization priorities: fix N+1 queries, add proper indexes, implement multi-layer caching (local LRU → Redis → DB), use connection pooling, and offload CPU-heavy work to Worker Threads. I target <50ms p95 latency and >90% cache hit rates."
