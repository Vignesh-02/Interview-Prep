# 24. Logging, Tracing & Distributed Debugging

## Topic Introduction

When something breaks in production at 3 AM, **logs and traces are your only witnesses**. Effective observability means you can answer: What happened? When? Why? Which users were affected?

```
Three Pillars of Observability:
  Logs:    What happened (discrete events)
  Metrics: How much / how often (aggregated numbers)
  Traces:  The journey of a request across services
```

**Structured logging** with JSON replaces `console.log('error happened')` with searchable, queryable, actionable events. **Distributed tracing** follows a single request across 10+ microservices with timing and context.

**Go/Java tradeoff**: Go uses `slog` (stdlib) or `zerolog`. Java uses SLF4J + Logback. Node.js uses Pino (fastest), Winston (most popular), or Bunyan. Pino is the best choice for production Node.js — it's ~5x faster than Winston.

---

## Q1. (Beginner) Why is `console.log` insufficient for production logging?

```js
// BAD: console.log in production
console.log('User login failed'); // no context, not searchable, no level

// GOOD: structured logging with Pino
const pino = require('pino');
const logger = pino({ level: 'info' });

logger.error({
  event: 'login_failed',
  userId: 'user-42',
  email: 'john@example.com',
  reason: 'invalid_password',
  ip: req.ip,
  userAgent: req.headers['user-agent'],
  requestId: req.id,
}, 'User login failed');

// Output (JSON):
// {"level":50,"time":1706000000000,"event":"login_failed","userId":"user-42",
//  "email":"john@example.com","reason":"invalid_password","ip":"1.2.3.4",
//  "requestId":"abc-123","msg":"User login failed"}
```

**Problems with console.log**: no log levels, no structure (can't filter/search), no timestamps, no context, synchronous (blocks event loop with large outputs), no rotation/transport.

---

## Q2. (Beginner) What are log levels and when should you use each?

```js
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

// FATAL (60): Process is about to crash
logger.fatal({ err }, 'Unrecoverable database connection failure');

// ERROR (50): Operation failed, needs attention
logger.error({ orderId, err: err.message }, 'Payment processing failed');

// WARN (40): Something unexpected but handled
logger.warn({ userId, rateLimitRemaining: 5 }, 'User approaching rate limit');

// INFO (30): Normal business operations
logger.info({ orderId, total: 99.99 }, 'Order created successfully');

// DEBUG (20): Detailed technical information
logger.debug({ query: sql, params, duration: '12ms' }, 'Database query executed');

// TRACE (10): Very verbose, usually disabled
logger.trace({ headers: req.headers }, 'Incoming request details');
```

| Level | Production | When to use |
|---|---|---|
| FATAL | Always on | Process is dying |
| ERROR | Always on | Something broke, needs fixing |
| WARN | Always on | Something is wrong but handled |
| INFO | Usually on | Business events (orders, logins) |
| DEBUG | Off (enable to troubleshoot) | Technical details |
| TRACE | Off | Extremely verbose |

---

## Q3. (Beginner) How do you set up Pino for production logging?

```js
const pino = require('pino');

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  // Add default fields to every log line
  base: {
    service: 'order-service',
    version: process.env.APP_VERSION || 'unknown',
    environment: process.env.NODE_ENV,
    hostname: require('os').hostname(),
  },
  // Redact sensitive fields
  redact: {
    paths: ['req.headers.authorization', 'password', 'creditCard', 'ssn'],
    censor: '[REDACTED]',
  },
  // Pretty print in development
  transport: process.env.NODE_ENV === 'development'
    ? { target: 'pino-pretty', options: { colorize: true, translateTime: true } }
    : undefined,
  // Serializers for common objects
  serializers: {
    req: pino.stdSerializers.req,
    res: pino.stdSerializers.res,
    err: pino.stdSerializers.err,
  },
});

// Express middleware for request logging
const pinoHttp = require('pino-http');
app.use(pinoHttp({
  logger,
  autoLogging: { ignore: (req) => req.url === '/health' },
  customLogLevel: (req, res, err) => {
    if (res.statusCode >= 500 || err) return 'error';
    if (res.statusCode >= 400) return 'warn';
    return 'info';
  },
}));
```

---

## Q4. (Beginner) How do you correlate logs across a single request?

```js
// Problem: 10 log lines from one request, but they're mixed with logs from other requests
// Solution: Request ID that appears in every log line for that request

const { AsyncLocalStorage } = require('async_hooks');
const { randomUUID } = require('crypto');

const als = new AsyncLocalStorage();

// Middleware: set request ID
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] || randomUUID();
  req.id = requestId;
  res.setHeader('x-request-id', requestId);

  // Store in AsyncLocalStorage so ALL code in this request can access it
  als.run({ requestId, userId: null }, () => next());
});

// Create a child logger that always includes requestId
function getLogger() {
  const store = als.getStore();
  return logger.child({
    requestId: store?.requestId,
    userId: store?.userId,
  });
}

// Now every log line in this request includes requestId
app.get('/orders', async (req, res) => {
  const log = getLogger();
  log.info('Fetching orders');
  const orders = await orderService.getOrders(); // logs inside here also have requestId
  log.info({ count: orders.length }, 'Orders fetched');
  res.json(orders);
});

// Even deep in service code:
class OrderService {
  async getOrders() {
    const log = getLogger(); // gets same requestId!
    log.debug('Querying database');
    return db.query('SELECT * FROM orders');
  }
}
```

**Answer**: `AsyncLocalStorage` (ALS) is Node.js's equivalent of Java's `ThreadLocal`. It propagates context through the entire async call chain without passing it as a parameter. Every log line in a request gets the same `requestId`.

---

## Q5. (Beginner) How do you ship logs to a centralized system?

```js
// Architecture: App → stdout → Log collector → Centralized storage
// App writes JSON to stdout. Container runtime collects it.

// Option 1: Docker + Fluentd/Fluent Bit → Elasticsearch
// docker-compose.yml:
// logging:
//   driver: fluentd
//   options:
//     fluentd-address: localhost:24224
//     tag: order-service

// Option 2: Pino transport to Elasticsearch directly
const pino = require('pino');
const logger = pino({
  transport: {
    targets: [
      { target: 'pino/file', options: { destination: 1 } }, // stdout
      { target: 'pino-elasticsearch', options: {
        node: 'http://elasticsearch:9200',
        index: 'logs-order-service',
        flushInterval: 1000,
      }},
    ],
  },
});

// Option 3: AWS CloudWatch
const logger = pino({
  transport: {
    target: '@serdnam/pino-cloudwatch-transport',
    options: {
      logGroupName: '/app/order-service',
      logStreamName: `${process.env.HOSTNAME}`,
      awsRegion: 'us-east-1',
    },
  },
});
```

**Recommendation**: Write JSON to stdout. Let infrastructure handle collection (Fluent Bit, Datadog Agent, CloudWatch Agent). This keeps your app simple and infrastructure-agnostic.

---

## Q6. (Intermediate) How do you implement distributed tracing with OpenTelemetry?

```js
// OpenTelemetry setup — instrument once, export to any backend
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const sdk = new NodeSDK({
  serviceName: 'order-service',
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://jaeger:4318/v1/traces',
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      // Auto-instruments: HTTP, Express, pg, Redis, Kafka, gRPC, etc.
      '@opentelemetry/instrumentation-http': {
        ignoreIncomingPaths: ['/health', '/metrics'],
      },
    }),
  ],
});

sdk.start();
process.on('SIGTERM', () => sdk.shutdown());

// Auto-instrumentation gives you traces like:
// POST /orders (45ms)
// ├── pg.query INSERT INTO orders (12ms)
// ├── HTTP GET http://user-service/users/42 (8ms)
// ├── HTTP POST http://payment-service/charge (15ms)
// └── kafka.produce order-events (3ms)
```

**Answer**: OpenTelemetry auto-instruments HTTP, database, and messaging libraries. A unique trace ID flows through all services via HTTP headers (`traceparent`). Visualize in Jaeger, Zipkin, or Datadog APM.

---

## Q7. (Intermediate) How do you create custom spans for business logic tracing?

```js
const { trace, SpanStatusCode } = require('@opentelemetry/api');
const tracer = trace.getTracer('order-service');

app.post('/orders', async (req, res) => {
  // Create a span for the entire operation
  return tracer.startActiveSpan('create-order', async (span) => {
    try {
      span.setAttribute('user.id', req.user.id);
      span.setAttribute('order.items_count', req.body.items.length);

      // Nested span for validation
      const validatedData = await tracer.startActiveSpan('validate-order', async (validSpan) => {
        const result = orderSchema.validate(req.body);
        validSpan.setAttribute('validation.valid', !result.error);
        validSpan.end();
        return result;
      });

      // Nested span for DB insert
      const order = await tracer.startActiveSpan('db-insert-order', async (dbSpan) => {
        dbSpan.setAttribute('db.system', 'postgresql');
        dbSpan.setAttribute('db.operation', 'INSERT');
        const result = await Order.create(validatedData.value);
        dbSpan.setAttribute('db.rows_affected', 1);
        dbSpan.end();
        return result;
      });

      // Nested span for event publishing
      await tracer.startActiveSpan('publish-order-event', async (pubSpan) => {
        await kafka.publish('order-events', { type: 'ORDER_CREATED', data: order });
        pubSpan.setAttribute('messaging.system', 'kafka');
        pubSpan.setAttribute('messaging.destination', 'order-events');
        pubSpan.end();
      });

      span.setStatus({ code: SpanStatusCode.OK });
      res.status(201).json(order);
    } catch (err) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
      span.recordException(err);
      throw err;
    } finally {
      span.end();
    }
  });
});
```

---

## Q8. (Intermediate) How do you implement structured error logging with context?

```js
// Error logging should answer: What, When, Where, Why, Who was affected?

class AppError extends Error {
  constructor(message, code, statusCode, context = {}) {
    super(message);
    this.code = code;
    this.statusCode = statusCode;
    this.context = context;
    this.isOperational = true;
  }
}

// Centralized error logging
app.use((err, req, res, next) => {
  const log = getLogger();

  const errorLog = {
    err: {
      message: err.message,
      code: err.code || 'UNKNOWN',
      statusCode: err.statusCode || 500,
      stack: err.stack,
    },
    request: {
      method: req.method,
      path: req.path,
      query: req.query,
      body: req.method !== 'GET' ? req.body : undefined,
      ip: req.ip,
      userAgent: req.headers['user-agent'],
    },
    user: req.user ? { id: req.user.id, email: req.user.email } : undefined,
    context: err.context,
  };

  if (err.statusCode >= 500 || !err.isOperational) {
    log.error(errorLog, `Unhandled error: ${err.message}`);
    // Send to Sentry for tracking
    Sentry.captureException(err, { extra: errorLog });
  } else {
    log.warn(errorLog, `Client error: ${err.message}`);
  }

  res.status(err.statusCode || 500).json({
    error: { code: err.code || 'INTERNAL_ERROR', message: err.isOperational ? err.message : 'Something went wrong' },
  });
});
```

---

## Q9. (Intermediate) How do you set up alerts based on log patterns?

```js
// Prometheus alerting rules (in YAML)
const alertRules = `
groups:
  - name: backend-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High 5xx error rate (>5%)"

      - alert: SlowResponses
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency above 2 seconds"

      - alert: HighEventLoopLag
        expr: nodejs_eventloop_lag_seconds > 0.1
        for: 1m
        labels:
          severity: warning
`;

// Application-level alerting for specific log patterns
const alertablePatterns = [
  { pattern: /database connection refused/i, severity: 'critical' },
  { pattern: /out of memory/i, severity: 'critical' },
  { pattern: /rate limit exceeded/i, severity: 'warning' },
];

logger.on('data', (log) => {
  for (const { pattern, severity } of alertablePatterns) {
    if (pattern.test(log.msg)) {
      sendAlert(severity, log);
    }
  }
});
```

---

## Q10. (Intermediate) How do you implement audit logging for compliance?

```js
// Audit logs are immutable records of who did what, when
const auditLogger = pino({
  level: 'info',
  transport: {
    target: 'pino-elasticsearch',
    options: { node: 'http://elasticsearch:9200', index: 'audit-logs' },
  },
});

function auditLog(action, actor, resource, details = {}) {
  auditLogger.info({
    event: 'audit',
    action,              // 'CREATE', 'UPDATE', 'DELETE', 'READ', 'LOGIN', 'EXPORT'
    actor: {
      userId: actor.id,
      email: actor.email,
      role: actor.role,
      ip: actor.ip,
    },
    resource: {
      type: resource.type,  // 'User', 'Order', 'Payment'
      id: resource.id,
    },
    changes: details.changes,  // { field: { from: 'old', to: 'new' } }
    timestamp: new Date().toISOString(),
    requestId: als.getStore()?.requestId,
  });
}

// Usage in routes
app.put('/api/users/:id', async (req, res) => {
  const before = await User.findById(req.params.id);
  const after = await User.update(req.params.id, req.body);

  auditLog('UPDATE', req.user, { type: 'User', id: req.params.id }, {
    changes: {
      name: { from: before.name, to: after.name },
      email: { from: before.email, to: after.email },
    },
  });

  res.json(after);
});

app.delete('/api/users/:id', async (req, res) => {
  auditLog('DELETE', req.user, { type: 'User', id: req.params.id });
  await User.softDelete(req.params.id);
  res.status(204).send();
});
```

---

## Q11. (Intermediate) How do you implement log sampling for high-throughput services?

```js
// Problem: 100k req/s × 5 log lines each = 500k log lines/second = expensive storage

// Solution: Sample non-error logs
const pino = require('pino');

const logger = pino({
  level: 'info',
  hooks: {
    logMethod(inputArgs, method, level) {
      // Always log errors
      if (level >= 50) return method.apply(this, inputArgs);
      // Sample info/debug at 10%
      if (Math.random() > 0.1) return; // drop 90% of info logs
      return method.apply(this, inputArgs);
    },
  },
});

// Better: head-based sampling (log all lines for 10% of requests)
app.use((req, res, next) => {
  const sampled = Math.random() < 0.1; // 10% of requests get full logging
  als.run({ requestId: randomUUID(), sampled }, () => next());
});

function getLogger() {
  const store = als.getStore();
  if (!store?.sampled) {
    return { info: () => {}, debug: () => {}, warn: logger.warn.bind(logger), error: logger.error.bind(logger) };
  }
  return logger.child({ requestId: store.requestId });
}
```

---

## Q12. (Intermediate) How do you debug production issues using logs and traces?

**Scenario**: Users report orders failing intermittently. How do you investigate?

```
Step 1: Check error rate in Prometheus/Grafana
  → Spike in 5xx errors starting at 14:32

Step 2: Query logs for errors in that timeframe
  → Elasticsearch: level:error AND timestamp:[14:30 TO 14:45]
  → Found: "Payment service timeout" errors

Step 3: Get a specific request trace from Jaeger
  → Search by requestId from the error log
  → Trace shows: payment-service HTTP call took 35 seconds (timeout was 5s)

Step 4: Check payment service logs
  → Payment service shows: "Database connection pool exhausted"
  → All 20 connections were in use, new queries queued

Step 5: Root cause
  → A new report query was running without timeout, holding connections for 2+ minutes
  → Fix: add query_timeout to the report query, increase pool size
```

```js
// Tools for debugging:
// 1. Structured query in Elasticsearch/Kibana
// requestId:"abc-123" AND service:"order-service"

// 2. Jaeger trace search
// service=order-service AND operation=POST /orders AND minDuration=5s

// 3. Correlate logs with traces
logger.info({
  requestId,
  traceId: trace.getActiveSpan()?.spanContext().traceId,
  orderId,
}, 'Order created');
// Now you can jump from log → trace → see full request journey
```

---

## Q13. (Advanced) How do you implement a centralized logging pipeline for microservices?

```
Architecture:
Services → stdout (JSON) → Fluent Bit (collect) → Kafka (buffer) → Elasticsearch (store)
                                                                  → S3 (archive)
                                                                  → Alerting rules
```

```yaml
# Fluent Bit configuration (runs as sidecar or DaemonSet)
[INPUT]
    Name tail
    Path /var/log/containers/*.log
    Parser json
    Tag kube.*
    Refresh_Interval 5

[FILTER]
    Name kubernetes
    Match kube.*
    Merge_Log On
    K8S-Logging.Parser On

[OUTPUT]
    Name kafka
    Match *
    Brokers kafka:9092
    Topics logs
    Format json

[OUTPUT]
    Name es
    Match *
    Host elasticsearch
    Port 9200
    Index logs-%Y.%m.%d
    Type _doc
```

```js
// Application-side: just write structured JSON to stdout
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  base: { service: process.env.SERVICE_NAME, version: process.env.APP_VERSION },
  timestamp: pino.stdTimeFunctions.isoTime,
});

// Infrastructure handles:
// - Collection (Fluent Bit reads stdout)
// - Buffering (Kafka absorbs spikes)
// - Storage (Elasticsearch for search, S3 for archive)
// - Retention (delete logs >30 days from ES, keep S3 for 1 year)
```

---

## Q14. (Advanced) How do you implement trace-based testing?

```js
// Record traces during tests, assert on them
const { InMemorySpanExporter, SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const memoryExporter = new InMemorySpanExporter();

// Setup in test
beforeAll(() => {
  tracerProvider.addSpanProcessor(new SimpleSpanProcessor(memoryExporter));
});

afterEach(() => memoryExporter.reset());

it('creates order with correct trace structure', async () => {
  await request(app).post('/orders').send({ items: [{ productId: 'p1', qty: 1 }] }).expect(201);

  const spans = memoryExporter.getFinishedSpans();
  const spanNames = spans.map(s => s.name);

  // Verify expected operations happened
  expect(spanNames).toContain('create-order');
  expect(spanNames).toContain('db-insert-order');
  expect(spanNames).toContain('publish-order-event');

  // Verify timing
  const dbSpan = spans.find(s => s.name === 'db-insert-order');
  expect(dbSpan.duration[1] / 1e6).toBeLessThan(100); // < 100ms

  // Verify attributes
  const orderSpan = spans.find(s => s.name === 'create-order');
  expect(orderSpan.attributes['order.items_count']).toBe(1);
});
```

---

## Q15. (Advanced) How do you implement log-based metrics (extracting metrics from logs)?

```js
// Extract metrics from log patterns
const logBasedMetrics = {
  orderCreated: new Counter({ name: 'orders_created_total', help: 'Orders created', labelNames: ['status'] }),
  paymentAmount: new Histogram({ name: 'payment_amount', help: 'Payment amounts', buckets: [10, 50, 100, 500, 1000] }),
  externalApiLatency: new Histogram({ name: 'external_api_latency_ms', help: 'External API latency', labelNames: ['service'] }),
};

// Hook into logger to extract metrics
const originalInfo = logger.info.bind(logger);
logger.info = function (obj, msg) {
  if (obj.event === 'order_created') {
    logBasedMetrics.orderCreated.inc({ status: obj.status });
  }
  if (obj.event === 'payment_processed') {
    logBasedMetrics.paymentAmount.observe(obj.amount);
  }
  if (obj.event === 'external_api_call') {
    logBasedMetrics.externalApiLatency.observe({ service: obj.service }, obj.durationMs);
  }
  return originalInfo(obj, msg);
};

// Now you get metrics AND logs from the same instrumentation
```

---

## Q16. (Advanced) How do you handle log rotation and retention?

```js
// Option 1: Let the container runtime handle it (recommended)
// Docker: max-size and max-file options
// K8s: log rotation configured at node level

// Option 2: pino-roll for file-based logging
const logger = pino({
  transport: {
    target: 'pino-roll',
    options: {
      file: '/var/log/app/order-service.log',
      frequency: 'daily',
      size: '100m',
      limit: { count: 30 }, // keep 30 files
      mkdir: true,
    },
  },
});

// Retention strategy:
// Hot: Elasticsearch (searchable) → 30 days
// Warm: Compressed in S3 → 90 days
// Cold: S3 Glacier → 1 year (compliance)
// Delete: After 1 year
```

---

## Q17. (Advanced) How do you implement dynamic log level changes without restarting?

```js
// Change log level at runtime via API or config change

// Option 1: Admin endpoint
app.post('/admin/log-level', authAdmin, (req, res) => {
  const { level } = req.body; // 'debug', 'info', 'warn', 'error'
  if (!['trace', 'debug', 'info', 'warn', 'error', 'fatal'].includes(level)) {
    return res.status(400).json({ error: 'Invalid log level' });
  }
  logger.level = level;
  console.log(`Log level changed to: ${level}`);
  res.json({ level: logger.level });
});

// Option 2: Watch config from Consul/etcd
const consul = require('consul')();
consul.watch({ method: consul.kv.get, options: { key: 'order-service/log-level' } })
  .on('change', (data) => {
    const newLevel = data.Value;
    logger.level = newLevel;
    logger.info(`Log level dynamically changed to: ${newLevel}`);
  });

// Option 3: Environment-based with hot reload (PM2)
// PM2 watches .env file changes and sends SIGUSR2
process.on('SIGUSR2', () => {
  const newLevel = process.env.LOG_LEVEL || 'info';
  logger.level = newLevel;
});
```

**Answer**: Dynamic log level is crucial for production debugging. Set to `debug` temporarily to get detailed logs for a specific issue, then revert to `info`. No restart, no redeploy.

---

## Q18. (Advanced) How do you implement distributed context propagation?

```js
// Context propagation: pass trace context AND business context across services

const { propagation, context, trace } = require('@opentelemetry/api');

// Service A: add business context to outgoing requests
async function callOrderService(userId, orderData) {
  const span = trace.getActiveSpan();
  span.setAttribute('user.id', userId);

  // OpenTelemetry auto-injects trace headers
  // Also inject business context as custom headers
  const headers = {};
  propagation.inject(context.active(), headers); // adds traceparent header

  headers['x-user-id'] = userId;
  headers['x-request-id'] = als.getStore()?.requestId;
  headers['x-tenant-id'] = als.getStore()?.tenantId;

  return fetch('http://order-service/orders', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData),
  });
}

// Service B: extract context from incoming requests
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] || randomUUID();
  const tenantId = req.headers['x-tenant-id'];
  const userId = req.headers['x-user-id'];

  als.run({ requestId, tenantId, userId }, () => next());
});
```

---

## Q19. (Advanced) How do you implement RED method monitoring?

**Answer**: RED = Rate, Errors, Duration — the essential metrics for every service.

```js
const { Counter, Histogram, register } = require('prom-client');

// Rate: requests per second
const requestRate = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status'],
});

// Errors: error rate
const errorRate = new Counter({
  name: 'http_errors_total',
  help: 'Total HTTP errors',
  labelNames: ['method', 'route', 'status'],
});

// Duration: request latency
const requestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});

// Middleware to collect RED metrics
app.use((req, res, next) => {
  const end = requestDuration.startTimer();
  res.on('finish', () => {
    const route = req.route?.path || req.path;
    const labels = { method: req.method, route, status: res.statusCode };
    requestRate.inc(labels);
    if (res.statusCode >= 400) errorRate.inc(labels);
    end({ method: req.method, route });
  });
  next();
});

// Prometheus endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.send(await register.metrics());
});

// Grafana dashboard queries:
// Rate:     rate(http_requests_total[5m])
// Errors:   rate(http_errors_total[5m]) / rate(http_requests_total[5m])
// Duration: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

---

## Q20. (Advanced) Senior red flags in logging, tracing, and observability.

**Answer**:

1. **Using console.log in production** — unstructured, no levels, no context
2. **No request ID correlation** — can't trace a request through multiple log lines
3. **Logging sensitive data** — passwords, tokens, PII in plain text
4. **No log levels** — everything is `info`, can't filter noise
5. **No distributed tracing** — impossible to debug cross-service issues
6. **Logging too much** — 10GB/day of debug logs costing $1000/month in storage
7. **Logging too little** — errors in production with no context to debug
8. **No alerting on error patterns** — errors happen and nobody knows
9. **Synchronous logging** — `console.log` of large objects blocks the event loop
10. **No audit trail** — can't answer "who changed this and when" for compliance

**Senior interview answer**: "I use Pino for structured JSON logging with request ID correlation via AsyncLocalStorage. Every log line includes requestId, userId, service, and version. I use OpenTelemetry for distributed tracing across services with auto-instrumentation. Logs go to stdout (collected by Fluent Bit → Elasticsearch), metrics to Prometheus, traces to Jaeger. I monitor RED metrics (Rate, Errors, Duration) and alert on error rate spikes and p95 latency degradation. I can change log levels dynamically without restarting for production debugging."
