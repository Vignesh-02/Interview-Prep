# 19. Error Handling & Resilience Patterns

## Topic Introduction

Production backends **will** fail. Network calls time out, databases go down, memory leaks happen. Resilience is about **designing for failure** so that when things break, they break gracefully — not catastrophically.

```
Request → Validate → Process → External Call → Response
   ↓          ↓         ↓           ↓
 Parse    Validation  Business   Network/DB
 Error     Error      Error      Error
   ↓          ↓         ↓           ↓
           ALL errors flow to centralized error handler
```

Key patterns: **Retry with exponential backoff**, **Circuit breaker**, **Bulkhead** (isolate failures), **Timeout**, **Fallback**, **Graceful degradation**. These patterns apply to ALL backend languages.

**Go/Java tradeoff**: Go returns errors explicitly (`val, err := fn()`). Java uses checked/unchecked exceptions + try/catch. Node.js uses Promises + async/await with try/catch. Go's explicit error handling avoids hidden exception flows but is more verbose. Java's checked exceptions force you to handle errors but lead to catch-and-swallow anti-patterns.

---

## Q1. (Beginner) How do you handle errors in Express.js middleware?

```js
const express = require('express');
const app = express();

// Route handler — throw errors or pass them to next()
app.get('/users/:id', async (req, res, next) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) {
      return next(new AppError('User not found', 404));
    }
    res.json(user);
  } catch (err) {
    next(err); // pass to error handler
  }
});

// Error handling middleware (4 arguments — Express recognizes this signature)
app.use((err, req, res, next) => {
  console.error(`[${req.method} ${req.path}] Error:`, err.message);

  const status = err.statusCode || 500;
  const message = err.isOperational ? err.message : 'Internal server error';

  res.status(status).json({
    error: {
      message,
      code: err.code || 'INTERNAL_ERROR',
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
    },
  });
});

// Custom error class
class AppError extends Error {
  constructor(message, statusCode, code) {
    super(message);
    this.statusCode = statusCode;
    this.code = code || 'APP_ERROR';
    this.isOperational = true; // expected errors (not bugs)
  }
}
```

**Answer**: Express uses error-handling middleware (4 parameters: `err, req, res, next`). Always call `next(err)` instead of handling errors in each route. The centralized handler logs the error, determines the status code, and returns a safe response.

---

## Q2. (Beginner) How do you catch async errors in Express without try/catch in every route?

```js
// Problem: Express doesn't catch async errors automatically (before Express 5)
app.get('/users', async (req, res) => {
  const users = await User.find(); // if this throws, Express gets unhandled rejection
  res.json(users);
});

// Solution 1: Wrapper function
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

app.get('/users', asyncHandler(async (req, res) => {
  const users = await User.find(); // errors caught and forwarded to error middleware
  res.json(users);
}));

// Solution 2: express-async-errors (monkey patches Express)
require('express-async-errors'); // just require at top of file

app.get('/users', async (req, res) => {
  const users = await User.find(); // errors now caught automatically
  res.json(users);
});

// Solution 3: Express 5 (handles async natively)
// In Express 5.x, async errors are caught automatically without any wrapper
```

**Answer**: Express 4 doesn't catch async errors. Use `asyncHandler` wrapper or `express-async-errors` package. Express 5 fixes this natively. Always ensure async errors reach your error middleware — silent unhandled rejections are the #1 cause of production mystery bugs.

---

## Q3. (Beginner) What are operational errors vs programmer errors?

**Answer**:

| | **Operational Errors** | **Programmer Errors** |
|---|---|---|
| Cause | External failures | Bugs in code |
| Examples | DB connection lost, timeout, 404, rate limit | TypeError, null reference, logic bug |
| Expected? | Yes, they will happen | No, they shouldn't happen |
| Recovery | Handle gracefully | Fix the bug, restart process |
| Response | Return error to client | Log, alert, restart |

```js
// Operational error — handle gracefully
app.post('/orders', async (req, res, next) => {
  try {
    const order = await createOrder(req.body);
    res.json(order);
  } catch (err) {
    if (err.code === 'INSUFFICIENT_INVENTORY') {
      // Operational: return meaningful error to client
      return res.status(409).json({ error: 'Item out of stock' });
    }
    if (err.code === 'ECONNREFUSED') {
      // Operational: dependency down
      return res.status(503).json({ error: 'Service temporarily unavailable' });
    }
    // Programmer error: unknown — log and return generic error
    next(err);
  }
});

// Process-level handlers for unexpected errors
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection:', reason);
  // Log to monitoring (Sentry, Datadog)
  // In production: gracefully shut down and let orchestrator restart
});

process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err);
  // MUST exit — process is in unknown state
  process.exit(1);
});
```

**Answer**: Operational errors are expected (network failures, invalid input). Handle them with proper error codes and messages. Programmer errors are bugs — they should be logged, alerted, and the process restarted. Never swallow unknown errors.

---

## Q4. (Beginner) How do you implement structured error responses in an API?

```js
// Consistent error response format
class ApiError extends Error {
  constructor(statusCode, code, message, details = null) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
  }

  toJSON() {
    return {
      error: {
        code: this.code,
        message: this.message,
        ...(this.details && { details: this.details }),
      },
    };
  }
}

// Common error factories
const Errors = {
  notFound: (resource) => new ApiError(404, 'NOT_FOUND', `${resource} not found`),
  badRequest: (message, details) => new ApiError(400, 'BAD_REQUEST', message, details),
  unauthorized: () => new ApiError(401, 'UNAUTHORIZED', 'Authentication required'),
  forbidden: () => new ApiError(403, 'FORBIDDEN', 'Insufficient permissions'),
  conflict: (message) => new ApiError(409, 'CONFLICT', message),
  tooManyRequests: () => new ApiError(429, 'RATE_LIMITED', 'Too many requests'),
  internal: () => new ApiError(500, 'INTERNAL_ERROR', 'Something went wrong'),
};

// Usage
app.get('/users/:id', asyncHandler(async (req, res) => {
  const user = await User.findById(req.params.id);
  if (!user) throw Errors.notFound('User');
  res.json(user);
}));

app.post('/users', asyncHandler(async (req, res) => {
  const { error, value } = userSchema.validate(req.body);
  if (error) throw Errors.badRequest('Validation failed', error.details);
  const user = await User.create(value);
  res.status(201).json(user);
}));
```

**Answer**: Consistent error format: always return `{ error: { code, message, details? } }`. Use HTTP status codes correctly (4xx for client errors, 5xx for server errors). Machine-readable `code` fields let clients handle errors programmatically.

---

## Q5. (Beginner) What is the difference between `throw`, `reject`, and `next(err)` in Node.js?

```js
// 1. throw — synchronous error, caught by try/catch
function parseJSON(str) {
  const data = JSON.parse(str); // throws SyntaxError if invalid
  return data;
}

// 2. Promise.reject — async error, caught by .catch() or try/catch with await
async function fetchUser(id) {
  const user = await db.findById(id);
  if (!user) return Promise.reject(new Error('User not found'));
  // OR: throw new Error('User not found'); — same behavior in async function
  return user;
}

// 3. next(err) — Express-specific, forwards to error middleware
app.get('/users/:id', (req, res, next) => {
  User.findById(req.params.id)
    .then(user => {
      if (!user) return next(new AppError('User not found', 404));
      res.json(user);
    })
    .catch(next); // forward database errors to error handler
});
```

**Answer**: `throw` and `reject` are JavaScript language features. `next(err)` is Express's way to pass errors to the error handling middleware chain. In async Express routes, `throw` becomes a rejected promise — you need a wrapper or Express 5 to catch it.

---

## Q6. (Intermediate) How do you implement retry with exponential backoff and jitter?

**Scenario**: Your service calls a payment API. It occasionally returns 503 (overloaded). Immediate retries would make it worse.

```js
async function withRetry(fn, options = {}) {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 30000,
    factor = 2,
    jitter = true,
    retryOn = (err) => err.status >= 500 || err.code === 'ECONNRESET',
    onRetry = () => {},
  } = options;

  let lastError;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn(attempt);
    } catch (err) {
      lastError = err;

      if (attempt === maxRetries || !retryOn(err)) {
        throw err;
      }

      // Exponential backoff: 1s, 2s, 4s, 8s...
      let delay = Math.min(baseDelay * Math.pow(factor, attempt), maxDelay);
      // Add jitter to prevent thundering herd
      if (jitter) delay = delay * (0.5 + Math.random());

      onRetry({ attempt: attempt + 1, delay, error: err });
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
  throw lastError;
}

// Usage
const result = await withRetry(
  () => fetch('https://api.stripe.com/v1/charges', { method: 'POST', body, signal: AbortSignal.timeout(5000) }),
  {
    maxRetries: 3,
    baseDelay: 1000,
    retryOn: (err) => err.status === 503 || err.status === 429 || err.code === 'ECONNRESET',
    onRetry: ({ attempt, delay, error }) => {
      console.warn(`Retry ${attempt} after ${delay}ms: ${error.message}`);
    },
  }
);
```

**Why jitter?** Without jitter, if 100 clients get a 503 at the same time, they all retry at exactly 1s, 2s, 4s — creating synchronized spikes (thundering herd). Jitter randomizes the delay so retries are spread out.

---

## Q7. (Intermediate) How do you implement timeouts on all external calls?

**Scenario**: Database query hangs for 5 minutes. Without a timeout, your request handler is stuck forever, consuming memory.

```js
// 1. HTTP request timeout
const response = await fetch('http://payment-service/charge', {
  method: 'POST',
  body: JSON.stringify(data),
  signal: AbortSignal.timeout(5000), // 5 second timeout
});

// 2. Database query timeout (PostgreSQL)
const pool = new Pool({
  connectionTimeoutMillis: 5000,     // wait for connection from pool
  query_timeout: 10000,              // per-query timeout
  statement_timeout: 10000,          // PostgreSQL-level timeout
  idle_in_transaction_session_timeout: 30000,
});

// 3. Generic timeout wrapper
function withTimeout(promise, ms, message = 'Operation timed out') {
  let timeoutId;
  const timeout = new Promise((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error(message)), ms);
  });

  return Promise.race([promise, timeout]).finally(() => clearTimeout(timeoutId));
}

// Usage
const user = await withTimeout(
  userService.getUser(userId),
  3000,
  'User service timeout'
);

// 4. Per-route timeout in Express
const timeout = require('connect-timeout');
app.use('/api', timeout('10s'));
app.use((req, res, next) => {
  if (!req.timedout) next();
});
```

**Answer**: Set timeouts on EVERY external call: HTTP requests, database queries, Redis operations, file I/O. Without timeouts, your service leaks resources on hung dependencies. The timeout should be shorter than the client's timeout (upstream < downstream).

**Tradeoff with Go**: Go uses `context.WithTimeout()` which propagates deadlines through the entire call chain automatically. Node.js requires manual timeout management.

---

## Q8. (Intermediate) What is the Bulkhead pattern? How does it prevent cascading failures?

**Scenario**: Your service has 3 endpoints: `/orders`, `/users`, `/reports`. The reports endpoint calls a slow external API. Under load, it consumes all available connections — making `/orders` and `/users` unresponsive too.

```js
// Bulkhead: isolate resources per dependency/operation
const { Semaphore } = require('async-mutex');

class Bulkhead {
  constructor(name, maxConcurrent) {
    this.name = name;
    this.semaphore = new Semaphore(maxConcurrent);
    this.waiting = 0;
  }

  async execute(fn) {
    this.waiting++;
    const [, release] = await this.semaphore.acquire();
    this.waiting--;

    try {
      return await fn();
    } finally {
      release();
    }
  }

  get stats() {
    return { name: this.name, active: this.semaphore.getValue(), waiting: this.waiting };
  }
}

// Create bulkheads per dependency
const bulkheads = {
  paymentService: new Bulkhead('payment', 10),  // max 10 concurrent payment calls
  reportService: new Bulkhead('reports', 5),     // max 5 concurrent report calls
  userService: new Bulkhead('users', 20),        // max 20 concurrent user calls
};

// Usage
app.get('/orders/:id/receipt', async (req, res) => {
  const receipt = await bulkheads.paymentService.execute(
    () => fetch('http://payment-service/receipts/' + req.params.id)
  );
  res.json(receipt);
});

app.get('/reports/sales', async (req, res) => {
  const report = await bulkheads.reportService.execute(
    () => generateSalesReport() // slow operation, limited to 5 concurrent
  );
  res.json(report);
});
```

**Answer**: Bulkhead isolates failures. If the report service is slow, it only uses its 5 allocated connections — the other 25 connections remain available for orders and users. Named after ship bulkheads that prevent a hull breach from sinking the entire ship.

---

## Q9. (Intermediate) How do you implement graceful shutdown in Node.js?

**Scenario**: You deploy a new version. Kubernetes sends SIGTERM. Your server has 50 in-flight requests. If you exit immediately, those requests fail.

```js
const server = app.listen(3000);
let isShuttingDown = false;

async function gracefulShutdown(signal) {
  console.log(`Received ${signal}. Starting graceful shutdown...`);
  isShuttingDown = true;

  // 1. Stop accepting new connections
  server.close(() => {
    console.log('HTTP server closed');
  });

  // 2. Health check returns unhealthy (load balancer stops sending traffic)
  // (see health check middleware below)

  // 3. Wait for in-flight requests to complete (with timeout)
  const shutdownTimeout = setTimeout(() => {
    console.error('Graceful shutdown timed out. Forcing exit.');
    process.exit(1);
  }, 30000); // 30 second grace period

  try {
    // 4. Close database connections
    await db.end();
    console.log('Database connections closed');

    // 5. Close Redis connections
    await redis.quit();
    console.log('Redis connections closed');

    // 6. Flush pending metrics/logs
    await metricsExporter.flush();
    await logger.flush();

    clearTimeout(shutdownTimeout);
    console.log('Graceful shutdown complete');
    process.exit(0);
  } catch (err) {
    console.error('Error during shutdown:', err);
    process.exit(1);
  }
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Health check middleware
app.get('/health', (req, res) => {
  if (isShuttingDown) {
    return res.status(503).json({ status: 'shutting_down' });
  }
  res.json({ status: 'healthy' });
});

// Reject new requests during shutdown
app.use((req, res, next) => {
  if (isShuttingDown) {
    return res.status(503).set('Connection', 'close').json({ error: 'Server is shutting down' });
  }
  next();
});
```

**Answer**: Graceful shutdown ensures zero dropped requests during deployments. Steps: stop accepting new connections → wait for in-flight requests → close DB/Redis → exit. Kubernetes gives a configurable grace period (`terminationGracePeriodSeconds`).

---

## Q10. (Intermediate) How do you design a fallback strategy when a dependency is down?

```js
// Graceful degradation — degrade functionality, don't crash

// Example: Product page with recommendations
app.get('/products/:id', async (req, res) => {
  // Primary data — MUST succeed
  const product = await productService.getProduct(req.params.id);
  if (!product) return res.status(404).json({ error: 'Product not found' });

  // Non-critical data — can fail gracefully
  const [recommendations, reviews, inventory] = await Promise.allSettled([
    recommendationService.getRecommendations(req.params.id),
    reviewService.getReviews(req.params.id),
    inventoryService.checkStock(req.params.id),
  ]);

  res.json({
    product,
    recommendations: recommendations.status === 'fulfilled' ? recommendations.value : [],
    reviews: reviews.status === 'fulfilled' ? reviews.value : { items: [], message: 'Reviews temporarily unavailable' },
    inStock: inventory.status === 'fulfilled' ? inventory.value.available : null, // null = unknown
  });
});

// Fallback with cache
class ServiceWithFallback {
  constructor(primaryFn, options = {}) {
    this.primaryFn = primaryFn;
    this.cache = options.cache; // Redis
    this.ttl = options.ttl || 300;
    this.fallbackValue = options.fallbackValue;
  }

  async call(key, ...args) {
    try {
      const result = await this.primaryFn(...args);
      // Cache successful responses for fallback
      if (this.cache) await this.cache.set(`fallback:${key}`, JSON.stringify(result), 'EX', this.ttl);
      return result;
    } catch (err) {
      console.warn(`Primary failed, trying fallback: ${err.message}`);
      // Try cached value
      if (this.cache) {
        const cached = await this.cache.get(`fallback:${key}`);
        if (cached) return { ...JSON.parse(cached), _stale: true };
      }
      // Last resort: return default
      return this.fallbackValue;
    }
  }
}

const productService = new ServiceWithFallback(
  (id) => fetch(`http://product-service/products/${id}`).then(r => r.json()),
  { cache: redis, ttl: 600, fallbackValue: null }
);
```

**Answer**: Use `Promise.allSettled()` (not `Promise.all()`) so one failure doesn't fail the entire response. Cache successful responses for fallback. Return degraded data (stale cache, defaults) instead of errors. Critical data fails the request; non-critical data degrades gracefully.

---

## Q11. (Intermediate) How do you prevent and detect memory leaks in production Node.js?

```js
// Common memory leak sources:
// 1. Event listeners not removed
// 2. Growing arrays/maps without cleanup
// 3. Closures holding references
// 4. Unclosed streams or connections

// Detection: monitor heap usage
const v8 = require('v8');

// Expose metrics
app.get('/debug/memory', (req, res) => {
  const heapStats = v8.getHeapStatistics();
  res.json({
    heapUsed: `${(heapStats.used_heap_size / 1024 / 1024).toFixed(2)} MB`,
    heapTotal: `${(heapStats.total_heap_size / 1024 / 1024).toFixed(2)} MB`,
    external: `${(heapStats.external_memory / 1024 / 1024).toFixed(2)} MB`,
    rss: `${(process.memoryUsage().rss / 1024 / 1024).toFixed(2)} MB`,
  });
});

// Prometheus metrics for memory monitoring
const memoryGauge = new Gauge({ name: 'nodejs_heap_used_bytes', help: 'Heap used' });
setInterval(() => {
  memoryGauge.set(process.memoryUsage().heapUsed);
}, 15000);

// Heap snapshot for debugging
// In production, trigger via admin endpoint (protected!)
app.post('/debug/heap-snapshot', authAdmin, (req, res) => {
  const filename = `/tmp/heap-${Date.now()}.heapsnapshot`;
  v8.writeHeapSnapshot(filename);
  res.json({ message: 'Snapshot written', filename });
  // Download and analyze in Chrome DevTools
});

// Common leak patterns and fixes
// LEAK: event emitter without cleanup
class Processor extends EventEmitter {
  process(data) {
    this.on('done', () => { /* listener added on every call, never removed */ });
  }
}

// FIX: use once() or removeListener()
class Processor extends EventEmitter {
  process(data) {
    this.once('done', () => { /* automatically removed after firing */ });
  }
}

// LEAK: growing cache without eviction
const cache = {};
function getUser(id) { cache[id] = fetchUser(id); return cache[id]; } // grows forever

// FIX: use LRU cache with size limit
const { LRUCache } = require('lru-cache');
const cache = new LRUCache({ max: 1000, ttl: 1000 * 60 * 5 });
```

---

## Q12. (Intermediate) How do you implement error budgets and error tracking?

**Scenario**: Your SLO is 99.9% availability (43 minutes/month downtime). You need to track whether you're on budget.

```js
// Error rate tracking with Prometheus
const totalRequests = new Counter({ name: 'http_requests_total', help: 'Total requests', labelNames: ['status'] });
const errorRequests = new Counter({ name: 'http_errors_total', help: 'Error requests', labelNames: ['status', 'path'] });

app.use((req, res, next) => {
  res.on('finish', () => {
    totalRequests.inc({ status: res.statusCode });
    if (res.statusCode >= 500) {
      errorRequests.inc({ status: res.statusCode, path: req.route?.path || 'unknown' });
    }
  });
  next();
});

// Error budget calculation (Prometheus query)
// SLO = 99.9% → Error budget = 0.1%
// Error rate = rate(http_errors_total[30d]) / rate(http_requests_total[30d])
// Budget consumed = error_rate / 0.001

// Sentry integration for error tracking
const Sentry = require('@sentry/node');
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1, // 10% of transactions
  beforeSend(event) {
    // Scrub sensitive data
    if (event.request?.headers) delete event.request.headers.authorization;
    return event;
  },
});

app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.errorHandler({
  shouldHandleError(error) {
    return error.statusCode >= 500; // only report 5xx errors
  },
}));
```

**Answer**: Track error rates against your SLO. When the error budget is nearly consumed, freeze feature deploys and focus on reliability. Use Sentry/Datadog for error grouping, alerting, and root cause analysis.

---

## Q13. (Advanced) How do you implement the Circuit Breaker + Retry + Timeout combination?

**Scenario**: Critical payment service call needs: timeout (don't wait forever), retry (transient failures), circuit breaker (stop trying when service is down).

```js
class ResilientCall {
  constructor(options = {}) {
    this.timeout = options.timeout || 5000;
    this.retries = options.retries || 3;
    this.baseDelay = options.baseDelay || 1000;
    this.circuitBreaker = new CircuitBreaker(options.circuitBreaker || {});
  }

  async execute(fn) {
    // Layer 1: Circuit breaker (outermost)
    if (this.circuitBreaker.isOpen()) {
      throw new Error('Circuit breaker is open');
    }

    // Layer 2: Retry
    let lastError;
    for (let attempt = 0; attempt <= this.retries; attempt++) {
      try {
        // Layer 3: Timeout (innermost)
        const result = await withTimeout(fn(), this.timeout);
        this.circuitBreaker.recordSuccess();
        return result;
      } catch (err) {
        lastError = err;
        this.circuitBreaker.recordFailure();

        if (this.circuitBreaker.isOpen()) {
          throw new Error('Circuit breaker opened during retries');
        }

        if (attempt < this.retries && this.isRetryable(err)) {
          const delay = this.baseDelay * Math.pow(2, attempt) * (0.5 + Math.random());
          await new Promise((r) => setTimeout(r, delay));
        }
      }
    }
    throw lastError;
  }

  isRetryable(err) {
    return err.message === 'Operation timed out' ||
           err.status === 503 ||
           err.code === 'ECONNRESET';
  }
}

// Usage
const paymentCall = new ResilientCall({
  timeout: 5000,
  retries: 2,
  circuitBreaker: { threshold: 5, resetTimeout: 30000 },
});

app.post('/orders/:id/pay', async (req, res) => {
  try {
    const result = await paymentCall.execute(() =>
      fetch('http://payment-service/charge', {
        method: 'POST',
        body: JSON.stringify({ orderId: req.params.id, amount: req.body.amount }),
      })
    );
    res.json(result);
  } catch (err) {
    if (err.message.includes('Circuit breaker')) {
      return res.status(503).json({ error: 'Payment service unavailable. Try again later.' });
    }
    res.status(500).json({ error: 'Payment failed' });
  }
});
```

**Answer**: The combination works as: Timeout (prevents hanging) → Retry (handles transient failures) → Circuit Breaker (stops calling when service is clearly down). Order matters: circuit breaker is the outermost layer (fail-fast), retry is in the middle, timeout is on each individual call.

---

## Q14. (Advanced) How do you handle poison messages / unprocessable events in event-driven systems?

**Scenario**: A Kafka consumer receives a malformed message. It throws an error, Kafka redelivers it, it fails again — infinite loop.

```js
// Dead Letter Queue (DLQ) pattern
const consumer = kafka.consumer({ groupId: 'order-processor' });
const dlqProducer = kafka.producer();

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const retryCount = parseInt(message.headers?.['x-retry-count']?.toString() || '0');

    try {
      const event = JSON.parse(message.value.toString());
      await processOrder(event);
    } catch (err) {
      console.error(`Processing failed (attempt ${retryCount + 1}):`, err.message);

      if (retryCount >= 3) {
        // Send to Dead Letter Queue after 3 retries
        await dlqProducer.send({
          topic: `${topic}.dlq`,
          messages: [{
            key: message.key,
            value: message.value,
            headers: {
              ...message.headers,
              'x-original-topic': topic,
              'x-failure-reason': err.message,
              'x-failed-at': new Date().toISOString(),
              'x-retry-count': String(retryCount + 1),
            },
          }],
        });
        console.warn('Message sent to DLQ:', message.key?.toString());
      } else {
        // Retry with backoff — send to retry topic with delay
        await dlqProducer.send({
          topic: `${topic}.retry`,
          messages: [{
            key: message.key,
            value: message.value,
            headers: { ...message.headers, 'x-retry-count': String(retryCount + 1) },
          }],
        });
      }
    }
  },
});

// DLQ consumer — for manual inspection and replay
const dlqConsumer = kafka.consumer({ groupId: 'dlq-handler' });
await dlqConsumer.subscribe({ topic: /.*\.dlq/ });

await dlqConsumer.run({
  eachMessage: async ({ message }) => {
    // Store in DB for manual review
    await db('dead_letters').insert({
      topic: message.headers['x-original-topic'],
      key: message.key?.toString(),
      value: message.value.toString(),
      reason: message.headers['x-failure-reason'],
      failed_at: message.headers['x-failed-at'],
    });
    // Alert operations team
    await alerting.send('DLQ message received', { key: message.key?.toString() });
  },
});
```

**Answer**: Use a Dead Letter Queue. After N retries, send failed messages to a DLQ topic. Monitor the DLQ, alert the team, and provide tools to inspect and replay messages once the bug is fixed. Never let poison messages block the entire consumer.

---

## Q15. (Advanced) How do you implement chaos engineering in a Node.js backend?

```js
// Chaos middleware — inject failures in non-production environments
class ChaosMiddleware {
  constructor(options = {}) {
    this.enabled = options.enabled || false;
    this.latencyMs = options.latencyMs || 0;
    this.latencyProbability = options.latencyProbability || 0;
    this.errorProbability = options.errorProbability || 0;
    this.errorCode = options.errorCode || 500;
  }

  middleware() {
    return async (req, res, next) => {
      if (!this.enabled) return next();

      // Random latency injection
      if (Math.random() < this.latencyProbability) {
        const delay = Math.random() * this.latencyMs;
        console.warn(`[CHAOS] Injecting ${delay.toFixed(0)}ms latency on ${req.path}`);
        await new Promise((r) => setTimeout(r, delay));
      }

      // Random error injection
      if (Math.random() < this.errorProbability) {
        console.warn(`[CHAOS] Injecting ${this.errorCode} error on ${req.path}`);
        return res.status(this.errorCode).json({ error: 'Chaos error injected' });
      }

      next();
    };
  }
}

// Usage in staging
const chaos = new ChaosMiddleware({
  enabled: process.env.CHAOS_ENABLED === 'true',
  latencyMs: 2000,            // up to 2s random delay
  latencyProbability: 0.1,    // 10% of requests get delayed
  errorProbability: 0.05,     // 5% of requests fail
  errorCode: 503,
});

app.use(chaos.middleware());

// Chaos experiments to run:
// 1. Kill a random service instance → does the circuit breaker activate?
// 2. Inject 5s latency → do timeouts fire correctly?
// 3. Fill up the connection pool → does the bulkhead protect other endpoints?
// 4. Send poison messages to Kafka → does the DLQ catch them?
// 5. Simulate Redis connection failure → does the fallback cache work?
```

**Answer**: Chaos engineering proactively tests resilience by injecting failures. Start small (latency injection in staging), observe behavior, fix weaknesses, then graduate to production experiments. Tools: **Chaos Monkey** (Netflix), **Gremlin**, **Litmus** (Kubernetes). The goal is to find weaknesses before customers do.

---

## Q16. (Advanced) How do you build a production incident response playbook?

**Answer**:

```
INCIDENT DETECTED (alert fires)
    │
    ▼
Phase 1: TRIAGE (first 5 minutes)
    ├─ Is it a real incident? Check dashboards, verify alert
    ├─ Assign severity (P1 = customer-facing outage, P2 = degraded, P3 = minor)
    ├─ Open incident channel (Slack #incident-2024-01-15)
    └─ Assign Incident Commander (IC)

Phase 2: MITIGATE (5-30 minutes)
    ├─ Check: what changed recently? (deploys, config changes, traffic spike)
    ├─ Rollback recent deploy if suspected (kubectl rollout undo / revert feature flag)
    ├─ Scale up if traffic spike (kubectl scale --replicas=10)
    ├─ Redirect traffic if regional (DNS failover)
    └─ Communicate: status page update, customer notification

Phase 3: RESOLVE (30min-hours)
    ├─ Root cause analysis while mitigation holds
    ├─ Implement proper fix
    ├─ Deploy fix with monitoring
    └─ Verify recovery

Phase 4: POST-MORTEM (within 48 hours)
    ├─ Blameless post-mortem document
    ├─ Timeline of events
    ├─ Root cause and contributing factors
    ├─ What went well, what didn't
    └─ Action items with owners and deadlines
```

```js
// Automated incident detection
const alertRules = {
  p1_outage: {
    condition: 'rate(http_5xx_total[5m]) / rate(http_requests_total[5m]) > 0.05',
    severity: 'P1',
    action: 'page_oncall',
  },
  p2_degraded: {
    condition: 'histogram_quantile(0.95, http_request_duration_seconds) > 5',
    severity: 'P2',
    action: 'slack_alert',
  },
  p3_elevated_errors: {
    condition: 'rate(http_4xx_total[15m]) > 100',
    severity: 'P3',
    action: 'slack_notification',
  },
};
```

**Answer**: Every team should have a documented incident response playbook. The key principle: **mitigate first, investigate later**. Rollback or disable feature flags before spending hours debugging. Blameless post-mortems focus on systems, not individuals.

---

## Q17. (Advanced) How do you handle cascading failures in a microservices architecture?

```js
// Cascading failure scenario:
// Payment service slow → Order service threads blocked waiting
// → Order service runs out of connections → API Gateway queues up
// → Client requests timeout → Users see errors everywhere

// SOLUTION: Multiple layers of protection

// 1. Timeout on every call (prevent thread blocking)
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 3000);
try {
  const result = await fetch('http://payment/charge', { signal: controller.signal });
} finally {
  clearTimeout(timeoutId);
}

// 2. Circuit breaker (stop calling when it's clearly down)
const breaker = new CircuitBreaker(chargePayment, { threshold: 5, resetTimeout: 30000 });

// 3. Bulkhead (limit concurrent calls per dependency)
const paymentBulkhead = new Bulkhead('payment', 10);

// 4. Fallback (degrade gracefully)
async function chargeWithFallback(orderId, amount) {
  try {
    return await paymentBulkhead.execute(() =>
      breaker.call(orderId, amount)
    );
  } catch (err) {
    // Fallback: queue for later processing
    await messageQueue.add('deferred-payments', { orderId, amount });
    return { status: 'pending', message: 'Payment will be processed shortly' };
  }
}

// 5. Load shedding (reject excess traffic before it overwhelms)
app.use((req, res, next) => {
  const lagMs = eventLoopLag();
  if (lagMs > 100) { // event loop is overloaded
    return res.status(503).json({ error: 'Service overloaded, try again' });
  }
  next();
});
```

**Answer**: Prevent cascading failures with defense in depth: timeouts (don't wait forever), circuit breakers (fail fast), bulkheads (isolate), fallbacks (degrade), load shedding (reject excess). Each layer catches what the previous one misses.

---

## Q18. (Advanced) How does Go handle errors differently from Node.js? What are the tradeoffs?

```go
// Go: explicit error returns — every function returns (result, error)
func GetUser(id string) (*User, error) {
    user, err := db.FindById(id)
    if err != nil {
        return nil, fmt.Errorf("failed to get user %s: %w", id, err) // wrap error
    }
    if user == nil {
        return nil, ErrNotFound // sentinel error
    }
    return user, nil
}

// Caller MUST check error
user, err := GetUser("42")
if err != nil {
    if errors.Is(err, ErrNotFound) {
        return c.JSON(404, map[string]string{"error": "User not found"})
    }
    return c.JSON(500, map[string]string{"error": "Internal error"})
}
```

```js
// Node.js: exception-based — errors thrown and caught
async function getUser(id) {
  const user = await db.findById(id); // throws on DB error
  if (!user) throw new NotFoundError('User');
  return user;
}

// Caller uses try/catch
try {
  const user = await getUser('42');
} catch (err) {
  if (err instanceof NotFoundError) return res.status(404).json({ error: err.message });
  throw err; // re-throw unexpected errors
}
```

**Tradeoffs**:

| | **Go** | **Node.js** |
|---|---|---|
| Error visibility | Always visible (must check `err`) | Can be hidden (forgot try/catch) |
| Verbosity | Very verbose (`if err != nil` everywhere) | Concise (try/catch wraps blocks) |
| Stack traces | Not included by default | Included automatically |
| Error wrapping | `fmt.Errorf("context: %w", err)` | `new Error('context', { cause: err })` |
| Risk | Forgetting to check `err` (lint catches this) | Silent unhandled rejections |

---

## Q19. (Advanced) How do you build self-healing systems in Node.js?

```js
// Self-healing: systems that detect and recover from failures automatically

// 1. Automatic reconnection
class ResilientRedis {
  constructor(url) {
    this.url = url;
    this.client = null;
    this.connect();
  }

  connect() {
    this.client = new Redis(this.url, {
      retryStrategy: (times) => Math.min(times * 200, 5000), // auto-reconnect
      maxRetriesPerRequest: 3,
    });
    this.client.on('error', (err) => console.error('Redis error:', err.message));
    this.client.on('connect', () => console.log('Redis connected'));
    this.client.on('reconnecting', () => console.log('Redis reconnecting...'));
  }
}

// 2. Automatic pool replenishment
const pool = new Pool({
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});
pool.on('error', (err) => {
  console.error('Pool connection error:', err.message);
  // Pool automatically replaces dead connections
});

// 3. Watchdog — restart stuck operations
class Watchdog {
  constructor(name, checkFn, healFn, intervalMs = 60000) {
    this.name = name;
    this.checkFn = checkFn;
    this.healFn = healFn;
    this.timer = setInterval(() => this.check(), intervalMs);
  }

  async check() {
    try {
      const healthy = await this.checkFn();
      if (!healthy) {
        console.warn(`[Watchdog] ${this.name} unhealthy, attempting recovery`);
        await this.healFn();
      }
    } catch (err) {
      console.error(`[Watchdog] ${this.name} check failed:`, err.message);
    }
  }
}

// Example: ensure Kafka consumer is running
const kafkaWatchdog = new Watchdog(
  'kafka-consumer',
  async () => { return kafkaConsumer.isRunning(); },
  async () => { await kafkaConsumer.disconnect(); await kafkaConsumer.connect(); await kafkaConsumer.subscribe({ topic: 'orders' }); await kafkaConsumer.run({ eachMessage: processMessage }); }
);

// 4. Kubernetes liveness/readiness probes
app.get('/health/live', (req, res) => {
  // Liveness: is the process alive? (restart if not)
  res.json({ status: 'ok' });
});

app.get('/health/ready', async (req, res) => {
  // Readiness: can it handle traffic? (stop sending traffic if not)
  const dbHealthy = await checkDb();
  const redisHealthy = await checkRedis();
  if (dbHealthy && redisHealthy) return res.json({ status: 'ready' });
  res.status(503).json({ status: 'not_ready', db: dbHealthy, redis: redisHealthy });
});
```

**Answer**: Self-healing combines: automatic reconnection (Redis, DB, Kafka), health checks (K8s restarts unhealthy pods), watchdogs (detect and fix stuck processes), connection pool replenishment, and graceful degradation. The system should recover from transient failures without human intervention.

---

## Q20. (Advanced) Senior red flags in error handling and resilience.

**Answer**:

1. **No try/catch around async operations** — unhandled rejections crash the process (or silently swallow errors)
2. **Swallowing errors silently** — `catch(() => {})` or `catch(console.log)` — errors disappear
3. **No timeout on external calls** — one hung dependency blocks the entire server
4. **No circuit breaker on critical dependencies** — cascading failures bring everything down
5. **Returning stack traces to clients** — leaks internal details to attackers
6. **No graceful shutdown on SIGTERM** — in-flight requests fail on every deploy
7. **Not distinguishing operational vs programmer errors** — treating all errors the same way
8. **No dead letter queue** — poison messages block event consumers forever
9. **Retry without backoff** — hammering a struggling service makes it worse
10. **No error monitoring/alerting** — errors happen in production and nobody knows

```js
// WORST PRACTICE COLLECTION:
try {
  await riskyOperation();
} catch (err) {
  // All of these are red flags:
  console.log(err);                    // logs and continues (swallowed)
  // catch(() => {})                   // completely silent
  // res.json({ error: err.stack })    // stack trace to client
  // res.json({ error: err.message })  // DB error message to client ("relation 'users' does not exist")
}

// BEST PRACTICE:
try {
  await riskyOperation();
} catch (err) {
  logger.error('Operation failed', { error: err.message, stack: err.stack, requestId });
  if (err.isOperational) {
    return res.status(err.statusCode).json({ error: { code: err.code, message: err.message } });
  }
  Sentry.captureException(err);
  return res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' } });
}
```

**Senior interview answer**: "I design for failure at every layer: timeouts on all external calls, circuit breakers on critical dependencies, retry with jitter for transient failures, bulkheads to isolate resources, graceful degradation when dependencies are down, dead letter queues for unprocessable events, and graceful shutdown on deploy. I classify errors as operational (expected, handle gracefully) or programmer (unexpected, log, alert, restart). Every error should be logged with context, tracked in Sentry, and covered by alerting rules."
