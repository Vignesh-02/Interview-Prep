# 18. Microservices Architecture

## Topic Introduction

Microservices decompose a monolith into **small, independently deployable services**, each owning a specific business domain. Each service has its own database, codebase, and deployment pipeline.

```
Monolith:                    Microservices:
┌──────────────┐             ┌─────────┐  ┌──────────┐  ┌───────────┐
│  Users       │             │ User    │  │ Order    │  │ Payment   │
│  Orders      │    →        │ Service │  │ Service  │  │ Service   │
│  Payments    │             │ (own DB)│  │ (own DB) │  │ (own DB)  │
│  Inventory   │             └─────────┘  └──────────┘  └───────────┘
└──────────────┘                    ↕ HTTP/gRPC/Events ↕
```

**When to use**: Team scale >20 developers, independent deployment needed, different scaling requirements per domain, polyglot requirements. **When NOT to use**: Small team (<10), early-stage product, unclear domain boundaries.

**Go/Java tradeoff**: Go microservices compile to single-binary deploys (~10MB, fast startup). Java Spring Boot provides extensive microservice tooling (Spring Cloud, Eureka, Zuul). Node.js is great for I/O-heavy services but may need Go/Rust for CPU-heavy ones. Many orgs use polyglot microservices — Node for APIs, Go for data pipelines, Python for ML.

---

## Q1. (Beginner) What are microservices and how do they differ from a monolith?

**Answer**:

| | **Monolith** | **Microservices** |
|---|---|---|
| Deployment | Deploy entire app | Deploy individual services |
| Database | Single shared DB | Database per service |
| Scaling | Scale entire app | Scale individual services |
| Team ownership | Everyone works in one codebase | Teams own services |
| Technology | Single stack | Polyglot (Node, Go, Python) |
| Failure isolation | One bug can crash everything | Failure isolated to one service |
| Complexity | Simple to start | Complex infrastructure needed |

```js
// Monolith — everything in one Express app
app.post('/orders', async (req, res) => {
  const user = await db.query('SELECT * FROM users WHERE id = $1', [req.userId]);
  const inventory = await db.query('SELECT * FROM inventory WHERE product_id = $1', [req.body.productId]);
  const payment = await chargeCard(user.cardToken, req.body.total);
  const order = await db.query('INSERT INTO orders ...', [...]);
  await sendEmail(user.email, 'Order confirmed');
  res.json(order);
});

// Microservice — order service calls other services
app.post('/orders', async (req, res) => {
  const user = await userService.getUser(req.userId);           // HTTP/gRPC call
  const available = await inventoryService.check(req.body.productId); // HTTP/gRPC call
  if (!available) return res.status(409).json({ error: 'Out of stock' });
  const payment = await paymentService.charge(user.id, req.body.total); // HTTP/gRPC call
  const order = await Order.create({ userId: user.id, ...req.body });   // own DB
  await eventBus.publish('order.created', { orderId: order.id });       // async event
  res.json(order);
});
```

**Tradeoff**: Start with a monolith. Extract microservices when team size, deployment frequency, or scaling demands justify the complexity.

---

## Q2. (Beginner) What are the main communication patterns between microservices?

**Answer**:

```
Synchronous (request/response):
  Service A → HTTP/gRPC → Service B → Response

Asynchronous (event-driven):
  Service A → Message Queue/Event Bus → Service B (processes later)
```

```js
// 1. Synchronous — HTTP REST
async function getUser(userId) {
  const res = await fetch(`http://user-service:3001/users/${userId}`);
  if (!res.ok) throw new Error(`User service error: ${res.status}`);
  return res.json();
}

// 2. Synchronous — gRPC (faster, typed)
const client = new userProto.UserService('user-service:50051', grpc.credentials.createInsecure());
const user = await new Promise((resolve, reject) => {
  client.getUser({ id: userId }, (err, response) => err ? reject(err) : resolve(response));
});

// 3. Asynchronous — Event via Kafka/RabbitMQ
const { Kafka } = require('kafkajs');
const kafka = new Kafka({ brokers: ['kafka:9092'] });
const producer = kafka.producer();
await producer.send({
  topic: 'order-events',
  messages: [{ key: orderId, value: JSON.stringify({ event: 'order.created', data: order }) }],
});
```

| | **HTTP** | **gRPC** | **Events (Kafka)** |
|---|---|---|---|
| Coupling | Temporal + spatial | Temporal + spatial | None (decoupled) |
| Speed | Slower (JSON/text) | Faster (protobuf/binary) | Async (eventual) |
| Use case | Simple CRUD | Performance-critical | Event-driven workflows |
| Error handling | HTTP status codes | gRPC status codes | Dead letter queues |

---

## Q3. (Beginner) What is an API Gateway? Why do microservices need one?

**Scenario**: You have 10 microservices. The frontend needs to call 5 different services for one page.

```
Without Gateway:                    With API Gateway:
Client → User Service               Client → API Gateway → User Service
Client → Order Service                                   → Order Service
Client → Product Service                                 → Product Service
Client → Payment Service                                 (single entry point)
```

```js
// Simple API Gateway with Express
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

// Route to appropriate service
app.use('/api/users', createProxyMiddleware({ target: 'http://user-service:3001', changeOrigin: true }));
app.use('/api/orders', createProxyMiddleware({ target: 'http://order-service:3002', changeOrigin: true }));
app.use('/api/products', createProxyMiddleware({ target: 'http://product-service:3003', changeOrigin: true }));

// Cross-cutting concerns (applied to ALL routes)
app.use(authMiddleware);          // centralized authentication
app.use(rateLimitMiddleware);     // rate limiting
app.use(requestLogger);          // logging

app.listen(3000); // single port for all clients
```

**Answer**: API Gateway provides: single entry point, centralized auth, rate limiting, request routing, response aggregation, SSL termination. Production options: **Kong**, **AWS API Gateway**, **nginx**, **Envoy**. Don't build your own for production — use battle-tested solutions.

---

## Q4. (Beginner) What is service discovery? Why can't you hard-code service URLs?

```js
// BAD: hard-coded URLs — breaks when services scale or move
const USER_SERVICE = 'http://10.0.1.5:3001';

// GOOD: service discovery — services register themselves
// Option 1: DNS-based (Kubernetes default)
const USER_SERVICE = 'http://user-service.default.svc.cluster.local:3001';

// Option 2: Consul service discovery
const consul = require('consul')();
async function getServiceUrl(serviceName) {
  const services = await consul.health.service({ service: serviceName, passing: true });
  if (services.length === 0) throw new Error(`No healthy instances of ${serviceName}`);
  const instance = services[Math.floor(Math.random() * services.length)]; // random LB
  return `http://${instance.Service.Address}:${instance.Service.Port}`;
}

// Register this service on startup
await consul.agent.service.register({
  name: 'order-service',
  address: os.hostname(),
  port: 3002,
  check: { http: `http://${os.hostname()}:3002/health`, interval: '10s' },
});
```

**Answer**: In dynamic environments (Kubernetes, cloud), IP addresses change. Service discovery lets services find each other by name. Kubernetes has built-in DNS-based discovery. Outside K8s, use **Consul**, **etcd**, or **Eureka**. Always combine with health checks so traffic only goes to healthy instances.

---

## Q5. (Beginner) What does "database per service" mean? Why is it important?

```
WRONG: Shared database (tight coupling)
┌─────────────┐  ┌──────────────┐
│ User Service │→ │              │
├─────────────┤  │  Shared DB   │ ← any service can read/write any table
│ Order Service│→ │  (all tables)│    schema changes break everyone
└─────────────┘  └──────────────┘

RIGHT: Database per service (loose coupling)
┌─────────────┐  ┌──────────┐
│ User Service │→ │ Users DB │   ← only User Service touches this
└─────────────┘  └──────────┘
┌──────────────┐  ┌──────────┐
│ Order Service│→ │ Orders DB│   ← only Order Service touches this
└──────────────┘  └──────────┘
```

```js
// Order service needs user data? Call the user service API
app.post('/orders', async (req, res) => {
  // DON'T: query user table directly
  // const user = await db.query('SELECT * FROM users WHERE id = $1', [req.userId]);

  // DO: call user service
  const user = await fetch(`http://user-service:3001/users/${req.userId}`).then(r => r.json());
  // ...
});
```

**Answer**: Database per service ensures: (1) services can evolve schemas independently, (2) no hidden coupling through shared tables, (3) each service can choose the best DB (Postgres for orders, MongoDB for products, Redis for sessions). The tradeoff: cross-service queries become harder — solved with events, API calls, or CQRS.

---

## Q6. (Intermediate) What is the Saga pattern? How do you handle distributed transactions?

**Scenario**: An order requires: (1) reserve inventory, (2) charge payment, (3) create order. If payment fails, you need to release the inventory. You can't use a database transaction across services.

```js
// Choreography-based saga — each service publishes events
// 1. Order Service publishes 'order.initiated'
await eventBus.publish('order.initiated', { orderId, userId, items, total });

// 2. Inventory Service listens, reserves stock, publishes result
consumer.on('order.initiated', async (event) => {
  try {
    await reserveInventory(event.items);
    await eventBus.publish('inventory.reserved', { orderId: event.orderId });
  } catch {
    await eventBus.publish('inventory.reservation.failed', { orderId: event.orderId });
  }
});

// 3. Payment Service listens to inventory.reserved, charges card
consumer.on('inventory.reserved', async (event) => {
  try {
    await chargePayment(event.orderId);
    await eventBus.publish('payment.completed', { orderId: event.orderId });
  } catch {
    await eventBus.publish('payment.failed', { orderId: event.orderId });
  }
});

// 4. Compensating actions (rollback)
consumer.on('payment.failed', async (event) => {
  await releaseInventory(event.orderId); // compensate step 2
  await cancelOrder(event.orderId);      // compensate step 1
});
```

```js
// Orchestration-based saga — central coordinator
class OrderSaga {
  constructor(orderId) { this.orderId = orderId; this.state = 'initiated'; }

  async execute(orderData) {
    try {
      this.state = 'reserving_inventory';
      await inventoryService.reserve(orderData.items);

      this.state = 'charging_payment';
      await paymentService.charge(orderData.userId, orderData.total);

      this.state = 'creating_order';
      await orderService.create(orderData);

      this.state = 'completed';
    } catch (err) {
      await this.compensate(err);
    }
  }

  async compensate(err) {
    console.error(`Saga failed at ${this.state}:`, err.message);
    // Rollback in reverse order
    if (this.state === 'creating_order' || this.state === 'charging_payment') {
      await paymentService.refund(this.orderId);
    }
    if (this.state !== 'reserving_inventory') {
      await inventoryService.release(this.orderId);
    }
    this.state = 'failed';
  }
}
```

**Answer**: Choreography = services coordinate via events (decentralized, harder to debug). Orchestration = central coordinator manages the flow (easier to debug, single point of failure). Use choreography for simple flows (2-3 steps), orchestration for complex flows (4+ steps).

---

## Q7. (Intermediate) What is the Circuit Breaker pattern? Implement one.

**Scenario**: Payment service is down. Your order service keeps calling it — each call times out after 30 seconds, blocking your event loop.

```js
class CircuitBreaker {
  constructor(fn, options = {}) {
    this.fn = fn;
    this.state = 'CLOSED';     // CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)
    this.failures = 0;
    this.successes = 0;
    this.threshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 30000;
    this.halfOpenMax = options.halfOpenMax || 3;
    this.lastFailureTime = null;
  }

  async call(...args) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.resetTimeout) {
        this.state = 'HALF_OPEN';
        this.successes = 0;
      } else {
        throw new Error('Circuit breaker is OPEN — service unavailable');
      }
    }

    try {
      const result = await this.fn(...args);
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      throw err;
    }
  }

  onSuccess() {
    if (this.state === 'HALF_OPEN') {
      this.successes++;
      if (this.successes >= this.halfOpenMax) {
        this.state = 'CLOSED';
        this.failures = 0;
        console.log('Circuit breaker CLOSED — service recovered');
      }
    }
    this.failures = 0;
  }

  onFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();
    if (this.failures >= this.threshold) {
      this.state = 'OPEN';
      console.warn('Circuit breaker OPEN — stopping calls to service');
    }
  }
}

// Usage
const paymentBreaker = new CircuitBreaker(
  (userId, amount) => fetch(`http://payment-service:3003/charge`, {
    method: 'POST',
    body: JSON.stringify({ userId, amount }),
    signal: AbortSignal.timeout(5000), // 5s timeout
  }),
  { failureThreshold: 5, resetTimeout: 30000 }
);

try {
  const result = await paymentBreaker.call(userId, 99.99);
} catch (err) {
  if (err.message.includes('Circuit breaker is OPEN')) {
    return res.status(503).json({ error: 'Payment service temporarily unavailable' });
  }
  throw err;
}
```

**Answer**: Circuit breaker prevents cascading failures. After N failures, it "opens" and fails fast (no waiting for timeouts). After a cooldown, it enters "half-open" state to test if the service recovered. Libraries: `opossum` (Node.js), `resilience4j` (Java), Go has no standard library — you build it.

---

## Q8. (Intermediate) How do you implement inter-service authentication?

**Scenario**: User Service needs to trust that the request from Order Service is legitimate, not from a random attacker.

```js
// Option 1: mTLS (mutual TLS) — services verify each other's certificates
// Usually handled by service mesh (Istio/Linkerd), not application code

// Option 2: Internal JWT / Service tokens
const INTERNAL_SECRET = process.env.INTERNAL_SERVICE_SECRET;

// Order Service — include service token in requests
async function callUserService(userId) {
  const serviceToken = jwt.sign(
    { service: 'order-service', iss: 'internal' },
    INTERNAL_SECRET,
    { expiresIn: '5m' }
  );

  return fetch(`http://user-service:3001/internal/users/${userId}`, {
    headers: {
      'Authorization': `Bearer ${serviceToken}`,
      'X-Request-ID': requestId,
    },
  }).then(r => r.json());
}

// User Service — verify internal service token
function internalAuthMiddleware(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  try {
    const decoded = jwt.verify(token, INTERNAL_SECRET);
    if (decoded.iss !== 'internal') throw new Error('Not a service token');
    req.callingService = decoded.service;
    next();
  } catch {
    res.status(401).json({ error: 'Invalid service token' });
  }
}

app.get('/internal/users/:id', internalAuthMiddleware, getUser);
```

**Answer**: Options ranked by maturity: (1) Shared secret/API key (simple, fine for small deployments), (2) Service JWT tokens (medium, good for most teams), (3) mTLS via service mesh (enterprise, zero-trust). Never expose internal endpoints publicly.

---

## Q9. (Intermediate) What is the Strangler Fig pattern for migrating from monolith to microservices?

**Scenario**: You have a 5-year-old monolith with 200k lines of code. Rewriting everything at once is too risky.

```
Phase 1: Route new features to microservice
┌──────────┐     ┌───────────┐     ┌──────────┐
│  Client   │ →   │  Reverse  │ ──→ │ Monolith │ (all traffic)
└──────────┘     │  Proxy    │     └──────────┘
                 └───────────┘

Phase 2: Extract one module
┌──────────┐     ┌───────────┐     ┌──────────┐
│  Client   │ →   │  Reverse  │ ──→ │ Monolith │ (most traffic)
└──────────┘     │  Proxy    │ ──→ ┌──────────────┐
                 └───────────┘     │ User Service  │ (extracted)
                                   └──────────────┘

Phase N: Monolith is empty
┌──────────┐     ┌───────────┐     ┌──────────────┐
│  Client   │ →   │  API      │ ──→ │ User Service  │
└──────────┘     │  Gateway  │ ──→ │ Order Service │
                 └───────────┘ ──→ │ Payment Svc   │
```

```nginx
# nginx routes — gradually move routes from monolith to microservices
upstream monolith { server monolith:3000; }
upstream user_service { server user-service:3001; }
upstream order_service { server order-service:3002; }

server {
    # Extracted services
    location /api/users { proxy_pass http://user_service; }
    location /api/orders { proxy_pass http://order_service; }

    # Everything else still goes to monolith
    location / { proxy_pass http://monolith; }
}
```

**Answer**: The Strangler Fig pattern incrementally replaces monolith functionality. Route by route, you extract modules into services. The monolith shrinks until it disappears. Key: always keep production running. Never big-bang rewrite.

---

## Q10. (Intermediate) What is the BFF (Backend for Frontend) pattern?

**Scenario**: Your mobile app needs minimal data (save bandwidth). Your web dashboard needs rich data. One API can't serve both well.

```
Without BFF:
Mobile App  → Generic API → (over-fetches data)
Web Dashboard → Generic API → (under-fetches, needs multiple calls)

With BFF:
Mobile App    → Mobile BFF  → [Microservices]  (returns minimal data)
Web Dashboard → Web BFF     → [Microservices]  (aggregates rich data)
Admin Panel   → Admin BFF   → [Microservices]  (different auth, full access)
```

```js
// Mobile BFF — lightweight responses
const mobileBFF = express();
mobileBFF.get('/api/dashboard', async (req, res) => {
  const [user, orders] = await Promise.all([
    fetch('http://user-service/users/' + req.userId).then(r => r.json()),
    fetch('http://order-service/users/' + req.userId + '/orders?limit=5').then(r => r.json()),
  ]);

  // Return only what mobile needs
  res.json({
    name: user.name,
    avatar: user.avatarThumb, // small image
    recentOrders: orders.map(o => ({ id: o.id, total: o.total, status: o.status })),
  });
});

// Web BFF — rich responses
const webBFF = express();
webBFF.get('/api/dashboard', async (req, res) => {
  const [user, orders, analytics, recommendations] = await Promise.all([
    fetch('http://user-service/users/' + req.userId).then(r => r.json()),
    fetch('http://order-service/users/' + req.userId + '/orders?limit=50').then(r => r.json()),
    fetch('http://analytics-service/users/' + req.userId + '/stats').then(r => r.json()),
    fetch('http://recommendation-service/users/' + req.userId).then(r => r.json()),
  ]);

  res.json({ user, orders, analytics, recommendations }); // everything
});
```

**Answer**: BFF avoids the "one API fits all" problem. Each client type gets an optimized backend. The BFF handles aggregation, formatting, and client-specific logic. It's also a natural fit for GraphQL (one schema per client type).

---

## Q11. (Intermediate) How do you handle service versioning and backward compatibility?

```js
// API versioning strategies
// 1. URL versioning
app.use('/api/v1/users', v1UserRoutes);
app.use('/api/v2/users', v2UserRoutes);

// 2. Header versioning
app.use('/api/users', (req, res, next) => {
  const version = req.headers['api-version'] || 'v1';
  if (version === 'v2') return v2Handler(req, res);
  return v1Handler(req, res);
});

// Backward-compatible changes (SAFE):
// - Adding new fields to response
// - Adding new optional query parameters
// - Adding new endpoints

// Breaking changes (NEED NEW VERSION):
// - Removing or renaming fields
// - Changing field types
// - Changing required parameters
// - Changing error response format

// Example: evolving a response without breaking clients
// v1 response
{ "name": "John Doe", "email": "john@example.com" }

// v1-compatible addition (safe — new field added)
{ "name": "John Doe", "email": "john@example.com", "avatar": "https://..." }

// v2 response (breaking — name split into firstName/lastName)
{ "firstName": "John", "lastName": "Doe", "email": "john@example.com" }
```

```js
// Consumer-driven contract testing with Pact
const { Pact } = require('@pact-foundation/pact');

const provider = new Pact({
  consumer: 'OrderService',
  provider: 'UserService',
});

describe('User Service Contract', () => {
  it('returns user by ID', async () => {
    await provider.addInteraction({
      state: 'user 42 exists',
      uponReceiving: 'a request for user 42',
      withRequest: { method: 'GET', path: '/users/42' },
      willRespondWith: {
        status: 200,
        body: { id: '42', name: like('John'), email: like('john@example.com') },
      },
    });

    const user = await userService.getUser('42');
    expect(user.name).toBeDefined();
  });
});
```

**Answer**: Always make backward-compatible changes (additive). When breaking changes are necessary, version the API and run old + new versions simultaneously. Use contract testing (Pact) to ensure services don't break their consumers.

---

## Q12. (Intermediate) What is event-driven architecture? How does Kafka fit in?

```js
// Event-driven: services communicate via events, not direct calls

// Producer — Order Service publishes events to Kafka
const { Kafka } = require('kafkajs');
const kafka = new Kafka({ clientId: 'order-service', brokers: ['kafka:9092'] });
const producer = kafka.producer();

app.post('/orders', async (req, res) => {
  const order = await Order.create(req.body);

  // Publish event — other services react asynchronously
  await producer.send({
    topic: 'order-events',
    messages: [{
      key: order.id,
      value: JSON.stringify({
        eventType: 'ORDER_CREATED',
        timestamp: new Date().toISOString(),
        data: { orderId: order.id, userId: order.userId, items: order.items, total: order.total },
      }),
      headers: { 'correlation-id': req.headers['x-request-id'] },
    }],
  });

  res.status(201).json(order);
});

// Consumer — Notification Service reacts to order events
const consumer = kafka.consumer({ groupId: 'notification-service' });
await consumer.subscribe({ topic: 'order-events', fromBeginning: false });

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const event = JSON.parse(message.value.toString());

    switch (event.eventType) {
      case 'ORDER_CREATED':
        await sendEmail(event.data.userId, 'Your order has been placed!');
        break;
      case 'ORDER_SHIPPED':
        await sendPushNotification(event.data.userId, 'Your order is on the way!');
        break;
    }
  },
});
```

**Answer**: Event-driven architecture decouples services — the producer doesn't know (or care) who consumes its events. Kafka provides: durable storage (events persisted), consumer groups (parallel processing), ordering (per partition). This is how Netflix, Uber, and LinkedIn handle millions of events/sec.

---

## Q13. (Advanced) How do you implement distributed tracing across microservices?

**Scenario**: A user request touches 5 services. The request is slow. Which service is the bottleneck?

```js
// OpenTelemetry — instrument all services
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({ url: 'http://jaeger:4318/v1/traces' }),
  instrumentations: [getNodeAutoInstrumentations()], // auto-instruments HTTP, Express, pg, etc.
});
sdk.start();

// Trace propagation — context flows across services automatically
// Service A calls Service B
const response = await fetch('http://order-service:3002/orders', {
  headers: {
    // OpenTelemetry auto-injects trace context headers:
    // traceparent: 00-traceId-spanId-01
    // tracestate: ...
  },
});

// Manual span creation for business logic
const { trace } = require('@opentelemetry/api');
const tracer = trace.getTracer('order-service');

app.post('/orders', async (req, res) => {
  const span = tracer.startSpan('create-order');
  try {
    span.setAttribute('user.id', req.userId);
    span.setAttribute('order.items_count', req.body.items.length);

    const order = await tracer.startActiveSpan('db-insert', async (dbSpan) => {
      const result = await Order.create(req.body);
      dbSpan.setAttribute('db.rows_affected', 1);
      dbSpan.end();
      return result;
    });

    span.setStatus({ code: SpanStatusCode.OK });
    res.json(order);
  } catch (err) {
    span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
    throw err;
  } finally {
    span.end();
  }
});
```

**Trace visualization in Jaeger**:
```
Request: POST /checkout
├─ API Gateway (2ms)
├─ Order Service (45ms)
│  ├─ DB: INSERT order (12ms)
│  ├─ HTTP: User Service /users/42 (8ms)
│  ├─ HTTP: Inventory Service /reserve (15ms)
│  └─ Kafka: publish order.created (3ms)
├─ Payment Service (320ms)  ← BOTTLENECK!
│  ├─ HTTP: Stripe API /charges (310ms)
│  └─ DB: INSERT payment (5ms)
└─ Total: 367ms
```

**Answer**: Distributed tracing assigns a unique trace ID to each request that flows through all services. Each service creates spans (timed operations). Tools: **Jaeger**, **Zipkin**, **Datadog APT**, **AWS X-Ray**. OpenTelemetry is the standard — instrument once, export to any backend.

---

## Q14. (Advanced) What is CQRS (Command Query Responsibility Segregation)?

**Scenario**: Your e-commerce app has complex read queries (join 5 tables for product listing with reviews, ratings, inventory) but simple writes (add product, update price). The read model is a performance bottleneck.

```js
// CQRS: separate write model and read model

// WRITE SIDE — normalized, optimized for consistency
app.post('/products', async (req, res) => {
  const product = await db.query(
    'INSERT INTO products (name, price, category_id) VALUES ($1, $2, $3) RETURNING *',
    [req.body.name, req.body.price, req.body.categoryId]
  );

  // Publish event for read model to update
  await eventBus.publish('product.created', product);
  res.status(201).json(product);
});

// READ SIDE — denormalized, optimized for queries
// Event consumer builds a read-optimized view
consumer.on('product.created', async (event) => {
  const category = await db.query('SELECT name FROM categories WHERE id = $1', [event.categoryId]);

  // Store in a read-optimized format (denormalized)
  await elasticsearch.index({
    index: 'products',
    id: event.id,
    body: {
      name: event.name,
      price: event.price,
      category: category.name,
      rating: 0,
      reviewCount: 0,
      inStock: true,
      // All data needed for listing — NO joins needed at query time
    },
  });
});

// Read queries are fast — no joins
app.get('/products', async (req, res) => {
  const results = await elasticsearch.search({
    index: 'products',
    body: {
      query: { bool: { must: [{ match: { category: req.query.category } }], filter: [{ range: { price: { lte: req.query.maxPrice } } }] } },
      sort: [{ rating: 'desc' }],
    },
  });
  res.json(results.hits.hits.map(h => h._source));
});
```

**Answer**: CQRS separates read and write paths. Writes go to a normalized DB (PostgreSQL). Events update a denormalized read model (Elasticsearch, Redis, materialized view). Reads are fast because all data is pre-joined. Tradeoff: **eventual consistency** — the read model lags behind writes by milliseconds to seconds.

---

## Q15. (Advanced) How do you handle data consistency across microservices without distributed transactions?

```js
// The Outbox Pattern — reliable event publishing
// Problem: save to DB + publish event is NOT atomic
// If app crashes between DB write and event publish, data is inconsistent

// BAD:
await db.query('INSERT INTO orders ...');
await kafka.publish('order.created', ...); // what if this fails?

// GOOD: Outbox pattern
// 1. Write business data + event to same DB in one transaction
await db.transaction(async (trx) => {
  const order = await trx('orders').insert(orderData).returning('*');

  // Write event to outbox table (same transaction = atomic)
  await trx('outbox_events').insert({
    id: uuid(),
    aggregate_type: 'Order',
    aggregate_id: order.id,
    event_type: 'ORDER_CREATED',
    payload: JSON.stringify(order),
    created_at: new Date(),
    published: false,
  });
});

// 2. Separate process reads outbox and publishes to Kafka
async function publishOutboxEvents() {
  const events = await db('outbox_events').where({ published: false }).orderBy('created_at').limit(100);

  for (const event of events) {
    await kafka.producer.send({
      topic: `${event.aggregate_type.toLowerCase()}-events`,
      messages: [{ key: event.aggregate_id, value: event.payload }],
    });
    await db('outbox_events').where({ id: event.id }).update({ published: true });
  }
}

// Run every second (or use CDC — Change Data Capture with Debezium)
setInterval(publishOutboxEvents, 1000);
```

**Answer**: The Outbox pattern guarantees at-least-once event delivery. Write the event to an outbox table in the same DB transaction as the business data. A separate publisher reads and sends events. Use **Debezium** (CDC) for a more elegant approach — it reads the DB transaction log directly.

---

## Q16. (Advanced) What is a Service Mesh? When do you need one?

**Answer**: A service mesh is an infrastructure layer that handles service-to-service communication (security, observability, traffic management) without changing application code.

```
Without Service Mesh:
┌────────────────┐     ┌────────────────┐
│  Order Service │ →→→ │  User Service  │
│  (circuit      │     │  (retry logic, │
│   breaker,     │     │   TLS, auth,   │
│   retry, TLS)  │     │   logging)     │
└────────────────┘     └────────────────┘
   ALL logic in app code — duplicated in every service

With Service Mesh (Istio/Linkerd):
┌────────────────┐     ┌────────────────┐
│  Order Service │     │  User Service  │
│  (just business│     │  (just business│
│   logic)       │     │   logic)       │
│  ┌──────────┐  │     │  ┌──────────┐  │
│  │ Sidecar  │←──────→│  │ Sidecar  │  │
│  │ (Envoy)  │  │     │  │ (Envoy)  │  │
│  └──────────┘  │     │  └──────────┘  │
└────────────────┘     └────────────────┘
   Sidecar handles: mTLS, retry, circuit breaker, tracing, metrics
```

```yaml
# Istio VirtualService — traffic management without code changes
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: user-service
spec:
  hosts: [user-service]
  http:
    - route:
        - destination:
            host: user-service
            subset: v2
          weight: 90
        - destination:
            host: user-service
            subset: v1
          weight: 10   # canary: 10% traffic to v1
      retries:
        attempts: 3
        perTryTimeout: 2s
      timeout: 10s
```

**When to use**: 10+ microservices, need mTLS everywhere, complex traffic routing (canary, A/B), centralized observability. **When NOT to use**: <5 services, simple deployment, team not ready for K8s complexity.

---

## Q17. (Advanced) How do you test microservices? (Unit, Integration, Contract, E2E)

```js
// 1. Unit tests — test business logic in isolation
describe('OrderService.calculateTotal', () => {
  it('applies discount for orders over $100', () => {
    const items = [{ price: 60, quantity: 2 }]; // $120
    expect(calculateTotal(items, { discountPercent: 10 })).toBe(108);
  });
});

// 2. Integration tests — test with real DB, mock external services
describe('POST /orders', () => {
  beforeAll(async () => {
    await db.migrate.latest(); // real test DB
  });

  it('creates an order and publishes event', async () => {
    // Mock external services
    nock('http://user-service:3001').get('/users/42').reply(200, { id: '42', name: 'John' });
    nock('http://inventory-service:3003').post('/reserve').reply(200, { reserved: true });

    const res = await request(app).post('/orders').send({ userId: '42', items: [{ productId: '1', qty: 2 }] });

    expect(res.status).toBe(201);
    expect(res.body.id).toBeDefined();
    // Verify event was published
    expect(kafkaMock.published).toContainEqual(expect.objectContaining({ topic: 'order-events' }));
  });
});

// 3. Contract tests — verify service interfaces don't break
// Using Pact
const { PactV3 } = require('@pact-foundation/pact');

describe('User Service contract', () => {
  const provider = new PactV3({ consumer: 'OrderService', provider: 'UserService' });

  it('returns user data', async () => {
    provider.addInteraction({
      states: [{ description: 'user 42 exists' }],
      uponReceiving: 'get user 42',
      withRequest: { method: 'GET', path: '/users/42' },
      willRespondWith: {
        status: 200,
        body: { id: string('42'), name: string('John'), email: string('john@test.com') },
      },
    });

    await provider.executeTest(async (mockServer) => {
      const user = await getUserFromService(mockServer.url, '42');
      expect(user.name).toBeDefined();
    });
  });
});

// 4. E2E tests — test full flow across all services
describe('E2E: Checkout flow', () => {
  it('places order, charges payment, sends notification', async () => {
    // Uses docker-compose to spin up all services
    const res = await fetch('http://api-gateway:3000/orders', {
      method: 'POST',
      body: JSON.stringify({ userId: '42', items: [{ productId: '1', qty: 1 }] }),
    });
    expect(res.status).toBe(201);

    // Wait for async events to propagate
    await waitFor(() => expect(getNotifications('42')).toHaveLength(1), { timeout: 5000 });
  });
});
```

**Testing pyramid for microservices**: Many unit tests → Fewer integration tests → Contract tests for every service boundary → Few E2E tests.

---

## Q18. (Advanced) How do you handle configuration management across microservices?

```js
// Centralized config with environment-specific overrides

// Option 1: Environment variables (simplest)
const config = {
  port: parseInt(process.env.PORT || '3000'),
  db: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    name: process.env.DB_NAME || 'orders',
    password: process.env.DB_PASSWORD, // from secrets manager
  },
  redis: { url: process.env.REDIS_URL || 'redis://localhost:6379' },
  kafka: { brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(',') },
  features: {
    newCheckout: process.env.FEATURE_NEW_CHECKOUT === 'true',
  },
};

// Option 2: Consul KV for dynamic config (no restart needed)
const consul = require('consul')();

class ConfigManager {
  constructor() { this.cache = {}; this.watchers = new Map(); }

  async get(key) {
    if (this.cache[key]) return this.cache[key];
    const { Value } = await consul.kv.get(key);
    this.cache[key] = JSON.parse(Buffer.from(Value, 'base64').toString());
    return this.cache[key];
  }

  watch(key, callback) {
    const watcher = consul.watch({ method: consul.kv.get, options: { key } });
    watcher.on('change', (data) => {
      const value = JSON.parse(Buffer.from(data.Value, 'base64').toString());
      this.cache[key] = value;
      callback(value);
    });
    this.watchers.set(key, watcher);
  }
}

// Usage: dynamically change rate limits without restarting
const configManager = new ConfigManager();
configManager.watch('order-service/rate-limit', (newLimit) => {
  console.log('Rate limit updated to:', newLimit);
  rateLimiter.setMax(newLimit.max);
});
```

**Answer**: Use environment variables for static config (12-factor app). Use Consul/etcd/AWS Parameter Store for dynamic config that needs to change without redeploy. Never hard-code config in source code. Secrets should come from Vault/AWS Secrets Manager, not env vars in Dockerfiles.

---

## Q19. (Advanced) How do you decompose a monolith? What are the criteria for service boundaries?

**Answer**: Use **Domain-Driven Design (DDD)** to identify bounded contexts:

```
E-commerce Monolith → Bounded Contexts:
┌────────────────────────────────────────────────────────┐
│                     Monolith                           │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌─────────┐ │
│  │ User     │ │ Catalog  │ │ Order     │ │ Payment │ │
│  │ Context  │ │ Context  │ │ Context   │ │ Context │ │
│  │ ─────    │ │ ─────    │ │ ─────     │ │ ─────   │ │
│  │ Register │ │ Products │ │ Cart      │ │ Charge  │ │
│  │ Login    │ │ Search   │ │ Checkout  │ │ Refund  │ │
│  │ Profile  │ │ Reviews  │ │ Shipping  │ │ Invoice │ │
│  └──────────┘ └──────────┘ └───────────┘ └─────────┘ │
└────────────────────────────────────────────────────────┘
```

**Criteria for splitting**:
1. **Team ownership** — can one team fully own this service?
2. **Deployment independence** — can it be deployed without deploying others?
3. **Data ownership** — does it own a distinct set of data?
4. **Business domain** — does it represent a clear business capability?
5. **Scaling requirements** — does it need different scaling than the rest?

**Process**:
```
1. Identify bounded contexts (DDD)
2. Define APIs between contexts (while still in monolith)
3. Extract the most independent context first (often Auth or Notifications)
4. Use Strangler Fig pattern to route traffic
5. Repeat for next context
```

**Red flags that you're decomposing wrong**:
- Service needs to call 5 other services to do anything (too fine-grained)
- Every change requires updating 3+ services (wrong boundaries)
- Services share a database (not really microservices)
- Team can't deploy their service independently

---

## Q20. (Advanced) Senior red flags in microservices architecture.

**Answer**:

1. **Distributed monolith** — services are tightly coupled via synchronous calls. Change one, break three.
2. **Shared database** — defeats the entire purpose. Services are coupled at the data layer.
3. **No circuit breakers** — one slow service takes down the entire system (cascading failure).
4. **No distributed tracing** — impossible to debug cross-service issues.
5. **Chatty inter-service communication** — 50 HTTP calls to render one page. Use async events or aggregate.
6. **Premature decomposition** — microservices for a 3-person team is overhead, not architecture.
7. **No contract testing** — deploying service A breaks service B because the API contract changed.
8. **No event schema registry** — event formats change without consumers knowing.
9. **Synchronous chains** — A calls B calls C calls D. Latency is additive, failure is multiplicative.
10. **No graceful degradation** — if payment service is down, the entire app shows 500 errors instead of allowing browsing.

```js
// RED FLAG: synchronous chain
app.get('/dashboard', async (req, res) => {
  const user = await fetch('http://user-service/users/1');        // 50ms
  const orders = await fetch('http://order-service/orders/1');    // 100ms
  const payments = await fetch('http://payment-service/pay/1');   // 200ms
  // Total: 350ms sequential, and if ANY fails, the whole request fails

  res.json({ user, orders, payments });
});

// FIX: parallel calls + graceful degradation
app.get('/dashboard', async (req, res) => {
  const [user, orders, payments] = await Promise.allSettled([
    fetch('http://user-service/users/1').then(r => r.json()),
    fetch('http://order-service/orders/1').then(r => r.json()),
    fetch('http://payment-service/pay/1').then(r => r.json()),
  ]);

  res.json({
    user: user.status === 'fulfilled' ? user.value : null,
    orders: orders.status === 'fulfilled' ? orders.value : [],
    payments: payments.status === 'fulfilled' ? payments.value : { status: 'unavailable' },
  });
});
```

**Senior interview answer**: "I decompose by business domain using DDD bounded contexts. Each service owns its data, communicates asynchronously where possible via Kafka events, implements circuit breakers for resilience, and uses OpenTelemetry for distributed tracing. I start with a modular monolith and extract services when the team and scale justify it. I use contract testing to ensure service interfaces don't break consumers, and the Outbox pattern for reliable event publishing."
