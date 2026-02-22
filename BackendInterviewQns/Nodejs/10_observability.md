# 10. Observability: Logs, Metrics & Traces

## Topic Introduction

Observability answers: "What is my system doing right now and why?" It's built on three pillars: **Logs** (event records), **Metrics** (numerical measurements), and **Traces** (request journey across services).

```
Request → Service A → Service B → Database
             │            │           │
          Log + Metric  Log + Metric  Log + Metric
             │            │           │
             └────── Trace (linked by trace-id) ──────┘
```

Without observability, debugging production issues is guesswork. With it, you can: find which service is slow, why errors spike at 3 PM, and which deployment caused the regression.

**Go/Java tradeoff**: Go uses `log/slog` (structured) + Prometheus client + OpenTelemetry. Java uses SLF4J/Logback + Micrometer + OpenTelemetry. Node.js uses `pino`/`winston` + `prom-client` + `@opentelemetry/sdk-node`. The concepts are identical — tooling differs.

---

## Q1. (Beginner) What are the three pillars of observability? How do they complement each other?

**Answer**:

| Pillar | What | Example | Tool |
|--------|------|---------|------|
| **Logs** | Text/JSON records of events | `"User 123 failed login from IP 10.0.0.1"` | Pino, ELK, Loki |
| **Metrics** | Numerical measurements over time | `http_requests_total = 50000` | Prometheus, Datadog |
| **Traces** | Request journey across services | `API → Auth → DB → Cache` with timing | Jaeger, Zipkin |

They complement:
- **Metrics** tell you **something is wrong** (error rate spiked)
- **Logs** tell you **what happened** (which error, which user)
- **Traces** tell you **where the bottleneck is** (DB call took 5s)

```js
// All three in one request
app.get('/orders/:id', async (req, res) => {
  const span = tracer.startSpan('getOrder');          // TRACE
  metrics.httpRequests.inc({ method: 'GET', path: '/orders/:id' }); // METRIC
  logger.info({ orderId: req.params.id, requestId: req.id }, 'Fetching order'); // LOG
  // ...
});
```

---

## Q2. (Beginner) How do you implement structured logging in Node.js?

```js
const pino = require('pino');

// Structured logger (JSON output)
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  serializers: {
    err: pino.stdSerializers.err,
    req: pino.stdSerializers.req,
  },
});

// Usage
logger.info({ userId: 123, action: 'login', ip: '10.0.0.1' }, 'User logged in');
// Output: {"level":"info","userId":123,"action":"login","ip":"10.0.0.1","msg":"User logged in","time":1709...}

// DON'T: unstructured logs
console.log('User 123 logged in from 10.0.0.1'); // can't search/filter/aggregate

// DO: structured logs
logger.info({ userId: 123, ip: '10.0.0.1' }, 'User logged in'); // searchable, parseable
```

**Answer**: Structured logging outputs JSON with consistent fields. This allows log aggregation tools (ELK, Loki, Datadog) to **search**, **filter**, and **aggregate** by any field. Pino is the fastest Node.js logger (~30% faster than Winston).

---

## Q3. (Beginner) How do you add a request ID to all logs for a request?

```js
const { randomUUID } = require('crypto');
const pino = require('pino');
const logger = pino();

// Middleware to create child logger with request ID
app.use((req, res, next) => {
  req.id = req.headers['x-request-id'] || randomUUID();
  req.log = logger.child({ requestId: req.id });
  res.setHeader('x-request-id', req.id);
  next();
});

// All logs in this request automatically include requestId
app.get('/users/:id', async (req, res) => {
  req.log.info({ userId: req.params.id }, 'Fetching user');
  // {"requestId":"abc-123","userId":"42","msg":"Fetching user"}
  const user = await getUser(req.params.id);
  req.log.info('User found');
  // {"requestId":"abc-123","msg":"User found"}
  res.json(user);
});
```

**Answer**: Request IDs correlate all logs from a single request. Pass the same ID to downstream services so you can trace the entire request across microservices. Use the incoming `x-request-id` header if present (for service-to-service calls).

---

## Q4. (Beginner) What are the four types of Prometheus metrics? Give a backend example of each.

```js
const client = require('prom-client');

// 1. Counter — monotonically increasing (never decreases)
const httpRequests = new client.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
});

// 2. Gauge — current value (can go up or down)
const activeConnections = new client.Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
});

// 3. Histogram — distribution of values (latency, size)
const requestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Request duration in seconds',
  labelNames: ['method', 'path'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5], // 10ms to 5s
});

// 4. Summary — similar to histogram but calculates percentiles client-side
const responseSizes = new client.Summary({
  name: 'http_response_size_bytes',
  help: 'Response size in bytes',
  percentiles: [0.5, 0.9, 0.99],
});
```

---

## Q5. (Beginner) How do you expose a `/metrics` endpoint for Prometheus?

```js
const client = require('prom-client');

// Collect default Node.js metrics (GC, event loop, heap)
client.collectDefaultMetrics({ prefix: 'node_' });

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.setHeader('Content-Type', client.register.contentType);
  res.send(await client.register.metrics());
});

// Middleware to track HTTP metrics
app.use((req, res, next) => {
  const start = process.hrtime.bigint();
  res.on('finish', () => {
    const duration = Number(process.hrtime.bigint() - start) / 1e9;
    httpRequests.inc({ method: req.method, path: req.route?.path || req.path, status: res.statusCode });
    requestDuration.observe({ method: req.method, path: req.route?.path || req.path }, duration);
  });
  next();
});
```

---

## Q6. (Intermediate) What is distributed tracing? How do you implement it with OpenTelemetry?

```js
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');

// Auto-instrument HTTP, Express, pg, Redis, etc.
const sdk = new NodeSDK({
  traceExporter: new JaegerExporter({ endpoint: 'http://jaeger:14268/api/traces' }),
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();

// Now every HTTP request, DB query, and Redis call creates spans automatically
// Trace: [API handler 50ms] → [DB query 30ms] → [Redis cache 2ms]
```

**Answer**: Distributed tracing tracks a request across service boundaries. Each service creates a **span** (unit of work) linked by a **trace ID**. OpenTelemetry auto-instruments popular libraries (Express, pg, ioredis) — you get traces with minimal code. Jaeger or Zipkin visualize the trace waterfall.

---

## Q7. (Intermediate) How do you measure and alert on the RED method (Rate, Errors, Duration)?

```js
// RED metrics for every endpoint
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const labels = { method: req.method, route: req.route?.path || 'unknown', status: res.statusCode };

    // Rate
    httpRequestsTotal.inc(labels);
    // Errors (5xx)
    if (res.statusCode >= 500) httpErrorsTotal.inc(labels);
    // Duration
    httpDurationHistogram.observe(labels, duration);
  });
  next();
});

// Prometheus alerting rules (in YAML):
// rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
// → "Error rate > 5% for 5 minutes"

// histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
// → "p99 latency > 2 seconds"
```

**Answer**: RED (Rate, Errors, Duration) gives you the essential health of any service. Rate = throughput. Errors = reliability. Duration = latency. Alert on: error rate > threshold, p99 latency > SLO, request rate drop (potential outage).

---

## Q8. (Intermediate) What Node.js-specific metrics should you monitor in production?

```js
const client = require('prom-client');
client.collectDefaultMetrics(); // includes:

// 1. Event loop lag — most critical Node.js metric
// node_eventloop_lag_seconds — gauge
// node_eventloop_lag_p99_seconds — high percentile

// 2. Heap memory
// process_heap_bytes — total heap
// nodejs_heap_size_used_bytes — used heap

// 3. GC metrics
// nodejs_gc_duration_seconds — GC pause duration by type

// 4. Active handles and requests
// nodejs_active_handles_total — open sockets, timers
// nodejs_active_requests_total — pending async operations

// Custom Node.js metrics
const eventLoopLag = new client.Gauge({
  name: 'custom_eventloop_lag_ms',
  help: 'Event loop lag in ms',
});

const { monitorEventLoopDelay } = require('perf_hooks');
const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();
setInterval(() => {
  eventLoopLag.set(h.mean / 1e6);
  h.reset();
}, 5000);
```

**Answer**: Beyond standard HTTP metrics, monitor: event loop lag (Node-specific), heap usage, GC pauses, active handles (connection leaks), and libuv thread pool utilization.

---

## Q9. (Intermediate) How do you implement log levels properly? What goes at each level?

```js
const pino = require('pino');
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

// TRACE/DEBUG — development only, verbose details
logger.debug({ query: sql, params }, 'DB query executed');

// INFO — normal operations, important state changes
logger.info({ userId, action: 'signup' }, 'New user registered');

// WARN — unexpected but recoverable situations
logger.warn({ retries: 3, service: 'payment' }, 'Payment service slow, retrying');

// ERROR — operation failed, needs attention
logger.error({ err, orderId }, 'Order processing failed');

// FATAL — application cannot continue
logger.fatal({ err }, 'Database connection lost, shutting down');
```

**Production rules**:
- Default level: `info` (don't use `debug` in production — too much volume)
- Change level dynamically without restart:
```js
process.on('SIGUSR2', () => {
  logger.level = logger.level === 'debug' ? 'info' : 'debug';
  logger.info({ level: logger.level }, 'Log level changed');
});
```

---

## Q10. (Intermediate) How do you propagate trace context across microservices?

```js
// Service A → Service B → Service C
// Each service passes trace headers

// Automatic with OpenTelemetry (recommended)
// OTel injects W3C traceparent header automatically
// Headers: traceparent: 00-<trace-id>-<span-id>-01

// Manual propagation
async function callServiceB(data, traceId) {
  return fetch('http://service-b/api', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-trace-id': traceId,       // propagate trace
      'x-request-id': requestId,   // propagate request ID
    },
    body: JSON.stringify(data),
  });
}

// Service B extracts trace context
app.use((req, res, next) => {
  req.traceId = req.headers['x-trace-id'] || randomUUID();
  req.log = logger.child({ traceId: req.traceId });
  next();
});
```

---

## Q11. (Intermediate) How do you create a custom health check endpoint?

```js
app.get('/health', (req, res) => res.json({ status: 'ok' })); // liveness

app.get('/ready', async (req, res) => {
  const checks = {
    database: false,
    redis: false,
    queue: false,
  };

  try {
    await pool.query('SELECT 1');
    checks.database = true;
  } catch {}

  try {
    await redis.ping();
    checks.redis = true;
  } catch {}

  try {
    await queue.getWaitingCount();
    checks.queue = true;
  } catch {}

  const healthy = Object.values(checks).every(Boolean);
  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'ready' : 'degraded',
    checks,
    uptime: process.uptime(),
    memory: process.memoryUsage().heapUsed,
  });
});
```

**Answer**: Separate **liveness** (process running) from **readiness** (can serve traffic). K8s uses liveness to restart pods and readiness to route traffic. Readiness should check all dependencies.

---

## Q12. (Intermediate) What are SLIs, SLOs, and SLAs? How do you implement them?

**Answer**:
- **SLI** (Service Level Indicator): measurable metric (e.g., 99.5% of requests < 200ms)
- **SLO** (Service Level Objective): target for the SLI (e.g., "99.9% availability per month")
- **SLA** (Service Level Agreement): contractual commitment with penalties

```js
// SLI: track availability and latency
const successfulRequests = new Counter({ name: 'sli_requests_success_total' });
const totalRequests = new Counter({ name: 'sli_requests_total' });
const latencyHistogram = new Histogram({ name: 'sli_latency_seconds', buckets: [0.1, 0.2, 0.5, 1] });

app.use((req, res, next) => {
  totalRequests.inc();
  const start = Date.now();
  res.on('finish', () => {
    if (res.statusCode < 500) successfulRequests.inc();
    latencyHistogram.observe((Date.now() - start) / 1000);
  });
  next();
});

// SLO calculation (in Prometheus):
// Availability SLO: sum(sli_requests_success_total) / sum(sli_requests_total) > 0.999
// Latency SLO: histogram_quantile(0.99, sli_latency_seconds) < 0.5
```

---

## Q13. (Advanced) Production scenario: P99 latency jumped from 100ms to 5s after a deploy. CPU and memory are normal. Debug it.

**Answer**:

```
Step 1: Check event loop lag metric
  → Normal? Not event loop blocking
  → High? CPU-heavy code in hot path

Step 2: Check distributed traces
  → Find slow span: is it DB? Redis? External API?
  → Example: DB query taking 4.9s (was 50ms before)

Step 3: Check DB slow query log
  → New query without index? (EXPLAIN ANALYZE)
  → Missing index on new column?

Step 4: Check recent deploy diff
  → New query? Changed ORM configuration?
  → Removed connection pool limit?

Step 5: Check dependency metrics
  → Redis: key evictions? Memory full?
  → Database: connection pool exhaustion?
  → External API: new timeout?
```

```js
// Quick diagnostic middleware
app.use(async (req, res, next) => {
  const timings = {};
  const originalQuery = pool.query.bind(pool);
  pool.query = async (...args) => {
    const start = Date.now();
    const result = await originalQuery(...args);
    timings.db = (timings.db || 0) + (Date.now() - start);
    return result;
  };
  res.on('finish', () => {
    if (Date.now() - req.startTime > 1000) {
      req.log.warn({ timings, path: req.path }, 'Slow request breakdown');
    }
  });
  next();
});
```

---

## Q14. (Advanced) How do you implement error budgets and burn-rate alerting?

```js
// Error budget = 1 - SLO
// If SLO = 99.9%, error budget = 0.1% of requests can fail

// Burn rate = how fast you're consuming the error budget
// burn_rate = actual_error_rate / allowed_error_rate

// Prometheus multi-window burn-rate alerting
// Fast burn: consuming budget 14x faster than allowed (alerts in hours)
// rate(http_errors_total[1h]) / rate(http_requests_total[1h]) > (14 * 0.001)
// AND
// rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > (14 * 0.001)

// Slow burn: consuming budget 3x faster (alerts in days)
// rate(http_errors_total[6h]) / rate(http_requests_total[6h]) > (3 * 0.001)
// AND
// rate(http_errors_total[30m]) / rate(http_requests_total[30m]) > (3 * 0.001)
```

**Answer**: Error budgets quantify how much unreliability is acceptable. Burn-rate alerting detects when you're consuming the budget too fast. Multi-window checks prevent false positives (short window for severity, long window for persistence).

---

## Q15. (Advanced) How do you debug memory leaks in Node.js production?

```js
// Step 1: Monitor heap growth
setInterval(() => {
  const { heapUsed, heapTotal, rss } = process.memoryUsage();
  metrics.heapUsed.set(heapUsed);
  metrics.rss.set(rss);
  // Alert if heapUsed grows linearly over hours
}, 10000);

// Step 2: Take heap snapshots (in production, carefully)
const v8 = require('v8');
app.get('/debug/heap', (req, res) => {
  if (req.headers['x-debug-key'] !== process.env.DEBUG_KEY) return res.status(403).end();
  const filename = `/tmp/heap-${Date.now()}.heapsnapshot`;
  v8.writeHeapSnapshot(filename);
  res.json({ filename });
});

// Step 3: Common Node.js memory leak causes
// - Event listeners not removed (emitter.on without off)
// - Closures holding references to large objects
// - Global caches without eviction (Map grows forever)
// - Unresolved Promises accumulating
// - Streams not properly destroyed

// Step 4: Use --expose-gc for manual GC testing
// node --expose-gc app.js
// global.gc(); // force GC, then check if memory drops
```

---

## Q16. (Advanced) How do you implement correlation IDs across an async microservices architecture?

```js
const { AsyncLocalStorage } = require('async_hooks');
const als = new AsyncLocalStorage();

// Middleware: set context for entire request lifecycle
app.use((req, res, next) => {
  const context = {
    requestId: req.headers['x-request-id'] || randomUUID(),
    traceId: req.headers['x-trace-id'] || randomUUID(),
    userId: null, // set after auth
  };
  als.run(context, () => next());
});

// Logger automatically includes context
function log(level, message, data = {}) {
  const ctx = als.getStore() || {};
  logger[level]({ ...data, requestId: ctx.requestId, traceId: ctx.traceId, userId: ctx.userId }, message);
}

// Works even in deeply nested async calls
async function getOrder(id) {
  log('info', 'Fetching order', { orderId: id });
  const order = await db.query('SELECT * FROM orders WHERE id = $1', [id]);
  log('info', 'Order found', { orderId: id });
  return order.rows[0];
}
// All logs automatically include requestId and traceId!
```

**Answer**: `AsyncLocalStorage` provides request-scoped context that propagates through the entire async call chain — no need to pass `requestId` through every function parameter.

---

## Q17. (Advanced) How does observability differ between Node.js, Go, and Java?

| Aspect | **Node.js** | **Go** | **Java** |
|--------|-------------|--------|----------|
| Logging | pino (JSON, fast) | slog/zap (structured) | Logback/SLF4J |
| Metrics | prom-client | prometheus/client_golang | Micrometer |
| Tracing | OpenTelemetry JS | OpenTelemetry Go | OpenTelemetry Java |
| Special metrics | Event loop lag, GC pauses | Goroutine count, GC | Thread pools, GC, heap gen |
| Memory profiling | v8.writeHeapSnapshot | pprof (built-in, amazing) | JFR, VisualVM |
| CPU profiling | --prof, clinic.js | pprof (built-in) | async-profiler |

**Go advantage**: `pprof` is built into the runtime — you can profile CPU, memory, goroutines in production with zero overhead. Node.js requires external tools.

**Java advantage**: JFR (Java Flight Recorder) provides continuous low-overhead profiling in production. Node.js has no equivalent.

---

## Q18. (Advanced) How do you build a production alerting strategy that minimizes alert fatigue?

**Answer**: Follow the **SRE alerting philosophy**: alert on symptoms (user impact), not causes (CPU high).

```yaml
# GOOD alerts (symptom-based)
- alert: HighErrorRate
  expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 5m
  labels: { severity: critical }

- alert: HighLatency
  expr: histogram_quantile(0.99, http_duration_bucket[5m]) > 2
  for: 5m
  labels: { severity: warning }

# BAD alerts (cause-based, noisy)
- alert: HighCPU
  expr: process_cpu_seconds_total > 0.8
  # CPU being high doesn't mean users are affected!
```

**Rules**:
1. Every alert must be **actionable** (human needs to do something)
2. Alert on **symptoms** first, include **cause** in dashboard
3. Use **severity levels**: critical (pager), warning (next business day)
4. Set **`for` duration** to avoid flapping (5m minimum)
5. Include **runbook link** in every alert

---

## Q19. (Advanced) How do you implement canary analysis with observability?

```js
// During canary deployment, compare metrics between stable and canary
// Canary gets 5% of traffic, stable gets 95%

// Tag metrics with deployment version
const httpRequests = new Counter({
  name: 'http_requests_total',
  labelNames: ['method', 'status', 'version'],
});

app.use((req, res, next) => {
  res.on('finish', () => {
    httpRequests.inc({
      method: req.method,
      status: res.statusCode,
      version: process.env.APP_VERSION, // 'v2.1-canary' or 'v2.0-stable'
    });
  });
  next();
});

// Prometheus query to compare:
// Canary error rate:
// rate(http_requests_total{version="v2.1-canary", status=~"5.."}[5m])
// / rate(http_requests_total{version="v2.1-canary"}[5m])

// Stable error rate:
// rate(http_requests_total{version="v2.0-stable", status=~"5.."}[5m])
// / rate(http_requests_total{version="v2.0-stable"}[5m])

// If canary error rate > stable + threshold → auto-rollback
```

---

## Q20. (Advanced) Senior observability red flags.

**Answer**:

1. **No structured logging** — `console.log` in production (unsearchable)
2. **No request ID correlation** — can't trace a request across logs
3. **Alerting on CPU/memory instead of user impact** — noisy, not actionable
4. **No p99 latency monitoring** — averages hide tail latency
5. **No dashboards for each service** — flying blind during incidents
6. **Logging sensitive data** — tokens, passwords, PII in logs
7. **No log rotation/retention policy** — disk fills up
8. **Not monitoring Node.js-specific metrics** — event loop lag, GC pauses invisible
9. **No distributed tracing in microservices** — can't find cross-service bottlenecks
10. **Over-logging** — logging every DB query in production overwhelms storage

**Senior interview answer**: "I implement the three pillars: structured JSON logs with request correlation, RED metrics (Rate, Errors, Duration) with Prometheus, and distributed tracing with OpenTelemetry. I alert on symptoms (error rate, latency) not causes, and monitor Node.js-specific metrics like event loop lag and GC pauses."
