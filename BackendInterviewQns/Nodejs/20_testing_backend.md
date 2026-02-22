# 20. Testing Backend Services

## Topic Introduction

Testing is how you **prove your code works** and **prevent regressions**. In backend development, tests span from isolated unit tests to full system integration tests. A senior engineer writes tests that give confidence to ship fast.

```
Testing Pyramid:
                    ┌─────┐
                    │ E2E │  (few, slow, expensive)
                   ┌┴─────┴┐
                   │ Integ. │  (moderate, test real dependencies)
                  ┌┴───────┴┐
                  │  Unit    │  (many, fast, isolated)
                  └──────────┘
```

**Key frameworks**: Jest (most popular), Vitest (faster, ESM-native), Mocha + Chai, Supertest (HTTP testing), Nock (HTTP mocking), Testcontainers (real DB in Docker).

**Go/Java tradeoff**: Go has built-in `testing` package — no framework needed. Java uses JUnit + Mockito + Spring Test. Node.js has many choices — Jest is dominant, Vitest is gaining for ESM projects.

---

## Q1. (Beginner) What are the different types of tests for a backend service?

**Answer**:

| Type | Scope | Speed | Dependencies | Example |
|---|---|---|---|---|
| **Unit** | Single function/class | Fast (ms) | None (all mocked) | Test `calculateTotal()` |
| **Integration** | Multiple modules + DB | Medium (s) | Real DB, mocked external APIs | Test POST /orders with Postgres |
| **Contract** | Service interface | Medium | Mock server | Verify API contract with consumer |
| **E2E** | Full system | Slow (min) | All services running | Test checkout flow across 5 services |
| **Load/Performance** | System capacity | Slow | All services | 1000 concurrent requests |

```js
// Unit test — pure logic, no I/O
function calculateDiscount(items, coupon) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  if (coupon?.type === 'percent') return subtotal * (1 - coupon.value / 100);
  if (coupon?.type === 'fixed') return Math.max(0, subtotal - coupon.value);
  return subtotal;
}

describe('calculateDiscount', () => {
  it('applies percentage coupon', () => {
    expect(calculateDiscount([{ price: 100, qty: 2 }], { type: 'percent', value: 10 })).toBe(180);
  });
  it('applies fixed coupon', () => {
    expect(calculateDiscount([{ price: 50, qty: 1 }], { type: 'fixed', value: 20 })).toBe(30);
  });
  it('does not go negative', () => {
    expect(calculateDiscount([{ price: 10, qty: 1 }], { type: 'fixed', value: 50 })).toBe(0);
  });
});
```

---

## Q2. (Beginner) How do you write API integration tests with Supertest?

```js
const request = require('supertest');
const app = require('../app');
const db = require('../db');

describe('POST /api/users', () => {
  beforeAll(async () => {
    await db.migrate.latest();
  });

  afterEach(async () => {
    await db('users').truncate(); // clean slate each test
  });

  afterAll(async () => {
    await db.destroy();
  });

  it('creates a user with valid data', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ name: 'John Doe', email: 'john@example.com', password: 'Secure123!' })
      .expect(201);

    expect(res.body).toMatchObject({
      id: expect.any(String),
      name: 'John Doe',
      email: 'john@example.com',
    });
    expect(res.body.password).toBeUndefined(); // never return password
  });

  it('returns 400 for invalid email', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ name: 'John', email: 'not-an-email', password: 'pass' })
      .expect(400);

    expect(res.body.error.code).toBe('VALIDATION_ERROR');
  });

  it('returns 409 for duplicate email', async () => {
    await request(app).post('/api/users').send({ name: 'A', email: 'dupe@test.com', password: 'Pass123!' });
    const res = await request(app)
      .post('/api/users')
      .send({ name: 'B', email: 'dupe@test.com', password: 'Pass123!' })
      .expect(409);

    expect(res.body.error.code).toBe('CONFLICT');
  });
});
```

**Answer**: Supertest sends real HTTP requests to your Express app without starting a network server. Test the full request/response cycle including middleware, validation, database operations, and error handling.

---

## Q3. (Beginner) How do you mock external services in tests?

```js
const nock = require('nock');

describe('Order Service', () => {
  afterEach(() => nock.cleanAll());

  it('creates order when payment succeeds', async () => {
    // Mock payment service
    nock('http://payment-service:3003')
      .post('/charge', { userId: '42', amount: 99.99 })
      .reply(200, { transactionId: 'txn_123', status: 'success' });

    // Mock inventory service
    nock('http://inventory-service:3004')
      .post('/reserve', { productId: 'p1', qty: 2 })
      .reply(200, { reserved: true });

    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${testToken}`)
      .send({ productId: 'p1', qty: 2 })
      .expect(201);

    expect(res.body.status).toBe('confirmed');
    expect(nock.isDone()).toBe(true); // verify all mocks were called
  });

  it('returns 503 when payment service is down', async () => {
    nock('http://payment-service:3003').post('/charge').reply(503);
    nock('http://inventory-service:3004').post('/reserve').reply(200, { reserved: true });

    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${testToken}`)
      .send({ productId: 'p1', qty: 2 })
      .expect(503);

    expect(res.body.error.message).toContain('Payment service');
  });
});
```

**Answer**: Nock intercepts HTTP requests at the Node.js level — no real network calls. Verify both success and failure paths. Always call `nock.cleanAll()` after each test. Use `nock.isDone()` to verify all expected calls were made.

---

## Q4. (Beginner) What is test coverage and how much is enough?

```js
// jest.config.js
module.exports = {
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/test/',
    '/migrations/',
  ],
};

// Run: npx jest --coverage
// Output:
// Statements: 85.2%
// Branches:   78.5% ← below threshold!
// Functions:  90.1%
// Lines:      85.2%
```

**Answer**: Coverage measures what percentage of your code is executed during tests. **80% is a good target** — enough to catch regressions without wasting time testing trivial code. But coverage doesn't measure quality: 100% coverage with no assertions is worthless. Focus on testing **behavior**, not chasing numbers.

---

## Q5. (Beginner) How do you structure test files and what naming conventions should you use?

```
project/
├── src/
│   ├── services/
│   │   └── orderService.js
│   ├── routes/
│   │   └── orderRoutes.js
│   └── utils/
│       └── pricing.js
├── test/
│   ├── unit/
│   │   ├── services/
│   │   │   └── orderService.test.js
│   │   └── utils/
│   │       └── pricing.test.js
│   ├── integration/
│   │   └── orders.integration.test.js
│   ├── e2e/
│   │   └── checkout.e2e.test.js
│   ├── fixtures/
│   │   └── orders.json
│   └── helpers/
│       ├── testDb.js
│       └── auth.js
```

```js
// test/helpers/testDb.js — shared test database setup
const knex = require('knex');

const testDb = knex({
  client: 'pg',
  connection: process.env.TEST_DATABASE_URL || 'postgres://localhost/myapp_test',
});

beforeAll(async () => { await testDb.migrate.latest(); });
afterAll(async () => { await testDb.destroy(); });

module.exports = testDb;
```

**Answer**: Separate test types into directories (`unit/`, `integration/`, `e2e/`). Name test files `*.test.js` or `*.spec.js`. Share test utilities in `helpers/`. Use fixtures for test data. Run unit tests in CI on every commit, integration tests on PR, E2E tests on deploy.

---

## Q6. (Intermediate) How do you test database operations with real databases?

**Scenario**: You want to test that your ORM queries work correctly, not just mock them.

```js
// Using Testcontainers — spin up real Postgres in Docker for tests
const { PostgreSqlContainer } = require('@testcontainers/postgresql');
const { Pool } = require('pg');
const { migrate } = require('../db/migrate');

let container;
let pool;

beforeAll(async () => {
  // Start real Postgres container
  container = await new PostgreSqlContainer('postgres:15')
    .withDatabase('testdb')
    .start();

  pool = new Pool({ connectionString: container.getConnectionUri() });
  await migrate(pool); // run migrations
}, 30000); // 30s timeout for container startup

afterAll(async () => {
  await pool.end();
  await container.stop();
});

beforeEach(async () => {
  // Clean tables between tests (faster than recreating container)
  await pool.query('TRUNCATE orders, order_items CASCADE');
});

describe('OrderRepository', () => {
  it('creates order with items in a transaction', async () => {
    const repo = new OrderRepository(pool);
    const order = await repo.create({
      userId: 'user-1',
      items: [
        { productId: 'p1', qty: 2, price: 25.00 },
        { productId: 'p2', qty: 1, price: 50.00 },
      ],
    });

    expect(order.id).toBeDefined();
    expect(order.total).toBe(100.00);

    // Verify items were saved
    const items = await pool.query('SELECT * FROM order_items WHERE order_id = $1', [order.id]);
    expect(items.rows).toHaveLength(2);
  });

  it('rolls back on item insert failure', async () => {
    const repo = new OrderRepository(pool);
    await expect(repo.create({
      userId: 'user-1',
      items: [{ productId: null, qty: 1, price: 10 }], // null violates NOT NULL constraint
    })).rejects.toThrow();

    // Verify order was NOT created (transaction rolled back)
    const orders = await pool.query('SELECT * FROM orders WHERE user_id = $1', ['user-1']);
    expect(orders.rows).toHaveLength(0);
  });
});
```

**Answer**: Testcontainers provides real databases in Docker for tests. This catches SQL bugs, constraint violations, and migration issues that mocks would miss. The tradeoff: slower than mocks (30s startup), but much more reliable. Run these in CI.

---

## Q7. (Intermediate) How do you test authentication and authorization?

```js
const jwt = require('jsonwebtoken');

// Test helper: generate tokens for different roles
function createTestToken(overrides = {}) {
  return jwt.sign(
    { userId: 'test-user', email: 'test@example.com', role: 'user', ...overrides },
    process.env.JWT_SECRET || 'test-secret',
    { expiresIn: '1h' }
  );
}

const adminToken = createTestToken({ role: 'admin', userId: 'admin-1' });
const userToken = createTestToken({ role: 'user', userId: 'user-1' });
const expiredToken = jwt.sign({ userId: 'old' }, 'test-secret', { expiresIn: '-1h' });

describe('Authorization', () => {
  it('allows admin to delete users', async () => {
    await request(app)
      .delete('/api/users/user-2')
      .set('Authorization', `Bearer ${adminToken}`)
      .expect(204);
  });

  it('denies regular user from deleting users', async () => {
    const res = await request(app)
      .delete('/api/users/user-2')
      .set('Authorization', `Bearer ${userToken}`)
      .expect(403);

    expect(res.body.error.code).toBe('FORBIDDEN');
  });

  it('returns 401 for missing token', async () => {
    await request(app).get('/api/users/me').expect(401);
  });

  it('returns 401 for expired token', async () => {
    await request(app)
      .get('/api/users/me')
      .set('Authorization', `Bearer ${expiredToken}`)
      .expect(401);
  });

  it('prevents users from accessing other users data', async () => {
    const res = await request(app)
      .get('/api/users/user-2/orders')
      .set('Authorization', `Bearer ${userToken}`) // user-1's token
      .expect(403);
  });
});
```

**Answer**: Test all auth scenarios: no token (401), expired token (401), wrong role (403), accessing another user's data (403), valid admin access (200/204). These are the most critical security tests — a missing auth check is a vulnerability.

---

## Q8. (Intermediate) How do you test async operations (events, queues, background jobs)?

```js
// Testing Kafka event publishing
describe('Order creation publishes event', () => {
  const publishedMessages = [];

  beforeAll(() => {
    // Mock Kafka producer
    jest.spyOn(kafkaProducer, 'send').mockImplementation(async (record) => {
      publishedMessages.push(record);
    });
  });

  afterEach(() => { publishedMessages.length = 0; });

  it('publishes ORDER_CREATED event after order is saved', async () => {
    await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${userToken}`)
      .send({ items: [{ productId: 'p1', qty: 1 }] })
      .expect(201);

    expect(publishedMessages).toHaveLength(1);
    expect(publishedMessages[0].topic).toBe('order-events');
    const event = JSON.parse(publishedMessages[0].messages[0].value);
    expect(event.eventType).toBe('ORDER_CREATED');
    expect(event.data.items).toHaveLength(1);
  });
});

// Testing event consumers
describe('Payment event consumer', () => {
  it('updates order status on PAYMENT_COMPLETED', async () => {
    // Create an order first
    const order = await OrderRepository.create({ userId: 'u1', items: [...], status: 'pending_payment' });

    // Simulate Kafka message
    await paymentEventHandler({
      topic: 'payment-events',
      message: {
        key: order.id,
        value: JSON.stringify({
          eventType: 'PAYMENT_COMPLETED',
          data: { orderId: order.id, transactionId: 'txn_123' },
        }),
      },
    });

    // Verify order was updated
    const updated = await OrderRepository.findById(order.id);
    expect(updated.status).toBe('confirmed');
    expect(updated.transactionId).toBe('txn_123');
  });
});

// Testing with real events (integration) — wait for async propagation
it('end-to-end: order → payment → notification', async () => {
  const res = await request(app).post('/api/orders').send({ ... }).expect(201);

  // Poll until order status changes (async processing)
  await waitForExpect(async () => {
    const order = await request(app).get(`/api/orders/${res.body.id}`).expect(200);
    expect(order.body.status).toBe('confirmed');
  }, 10000, 500); // 10s timeout, check every 500ms
});
```

---

## Q9. (Intermediate) How do you test error scenarios and edge cases?

```js
describe('Error handling', () => {
  it('returns 400 for negative quantity', async () => {
    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${userToken}`)
      .send({ items: [{ productId: 'p1', qty: -1 }] })
      .expect(400);

    expect(res.body.error.details).toContainEqual(
      expect.objectContaining({ field: 'items.0.qty', message: expect.stringContaining('positive') })
    );
  });

  it('handles database connection failure gracefully', async () => {
    // Simulate DB failure
    jest.spyOn(db, 'query').mockRejectedValueOnce(new Error('Connection refused'));

    const res = await request(app)
      .get('/api/orders')
      .set('Authorization', `Bearer ${userToken}`)
      .expect(500);

    expect(res.body.error.code).toBe('INTERNAL_ERROR');
    expect(res.body.error.message).not.toContain('Connection refused'); // don't leak
  });

  it('handles concurrent order creation (race condition)', async () => {
    // Limited stock: only 1 item left
    await db('inventory').insert({ product_id: 'p1', quantity: 1 });

    // Two concurrent orders for the same item
    const [res1, res2] = await Promise.all([
      request(app).post('/api/orders').set('Authorization', `Bearer ${userToken}`).send({ items: [{ productId: 'p1', qty: 1 }] }),
      request(app).post('/api/orders').set('Authorization', `Bearer ${adminToken}`).send({ items: [{ productId: 'p1', qty: 1 }] }),
    ]);

    // One should succeed, one should fail
    const statuses = [res1.status, res2.status].sort();
    expect(statuses).toEqual([201, 409]);
  });

  it('handles extremely large request body', async () => {
    const largeBody = { items: Array.from({ length: 10000 }, (_, i) => ({ productId: `p${i}`, qty: 1 })) };
    await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${userToken}`)
      .send(largeBody)
      .expect(400); // should reject, not crash
  });
});
```

---

## Q10. (Intermediate) What are test doubles (mocks, stubs, spies, fakes)? When do you use each?

**Answer**:

| Type | What it does | Example |
|---|---|---|
| **Spy** | Wraps real function, records calls | Verify `sendEmail` was called with correct args |
| **Stub** | Replaces function with canned response | `findById` always returns a test user |
| **Mock** | Stub + expectations on how it's called | Verify `save` was called exactly once |
| **Fake** | Working implementation for testing | In-memory database instead of Postgres |

```js
// Spy — observe real behavior
const sendEmail = jest.fn(realSendEmail);
await createUser({ email: 'test@test.com' });
expect(sendEmail).toHaveBeenCalledWith('test@test.com', expect.objectContaining({ subject: 'Welcome' }));

// Stub — replace with canned response
jest.spyOn(UserRepository, 'findById').mockResolvedValue({ id: '42', name: 'John', email: 'j@t.com' });
const user = await UserRepository.findById('42'); // returns mock data

// Mock — stub with assertions
const mockPaymentService = {
  charge: jest.fn().mockResolvedValue({ transactionId: 'txn_123' }),
};
await processOrder(order, mockPaymentService);
expect(mockPaymentService.charge).toHaveBeenCalledTimes(1);
expect(mockPaymentService.charge).toHaveBeenCalledWith(order.userId, order.total);

// Fake — lightweight real implementation
class InMemoryUserRepository {
  constructor() { this.users = new Map(); }
  async create(user) { const id = uuid(); this.users.set(id, { ...user, id }); return this.users.get(id); }
  async findById(id) { return this.users.get(id) || null; }
  async findByEmail(email) { return [...this.users.values()].find(u => u.email === email) || null; }
}
```

**Recommendation**: Use fakes for repositories (most realistic). Spies for side effects (email, events). Stubs for external services. Reserve mocks for verifying interaction patterns.

---

## Q11. (Intermediate) How do you test middleware in isolation?

```js
const { authMiddleware, rateLimitMiddleware } = require('../middleware');

describe('authMiddleware', () => {
  function createMockReqRes(headers = {}) {
    const req = { headers, path: '/test' };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();
    return { req, res, next };
  }

  it('passes with valid token', () => {
    const token = createTestToken();
    const { req, res, next } = createMockReqRes({ authorization: `Bearer ${token}` });

    authMiddleware(req, res, next);

    expect(next).toHaveBeenCalled();
    expect(req.user).toBeDefined();
    expect(req.user.userId).toBe('test-user');
  });

  it('returns 401 without token', () => {
    const { req, res, next } = createMockReqRes();

    authMiddleware(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
  });

  it('returns 401 for malformed token', () => {
    const { req, res, next } = createMockReqRes({ authorization: 'Bearer invalid-token' });

    authMiddleware(req, res, next);

    expect(res.status).toHaveBeenCalledWith(401);
    expect(res.json).toHaveBeenCalledWith(expect.objectContaining({ error: expect.any(Object) }));
  });
});
```

---

## Q12. (Intermediate) How do you use factory functions and fixtures for test data?

```js
// test/factories/userFactory.js
const { faker } = require('@faker-js/faker');

function buildUser(overrides = {}) {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    role: 'user',
    createdAt: new Date(),
    ...overrides,
  };
}

async function createUser(db, overrides = {}) {
  const user = buildUser(overrides);
  const [inserted] = await db('users').insert(user).returning('*');
  return inserted;
}

// test/factories/orderFactory.js
function buildOrder(overrides = {}) {
  return {
    id: faker.string.uuid(),
    userId: faker.string.uuid(),
    status: 'pending',
    total: faker.number.float({ min: 10, max: 1000, fractionDigits: 2 }),
    items: [{ productId: faker.string.uuid(), qty: faker.number.int({ min: 1, max: 5 }), price: faker.number.float({ min: 5, max: 200, fractionDigits: 2 }) }],
    ...overrides,
  };
}

// Usage in tests — clear, readable
describe('GET /orders', () => {
  it('returns only orders belonging to the authenticated user', async () => {
    const user = await createUser(db, { role: 'user' });
    const otherUser = await createUser(db);
    const myOrder = await createOrder(db, { userId: user.id });
    const otherOrder = await createOrder(db, { userId: otherUser.id });

    const res = await request(app)
      .get('/api/orders')
      .set('Authorization', `Bearer ${createTestToken({ userId: user.id })}`)
      .expect(200);

    expect(res.body.orders).toHaveLength(1);
    expect(res.body.orders[0].id).toBe(myOrder.id);
  });
});
```

**Answer**: Factories create test data with sensible defaults. Override only what's relevant to the test. This makes tests readable — you can see exactly what's being tested without wading through irrelevant data setup.

---

## Q13. (Advanced) How do you implement contract testing between microservices?

**Scenario**: Order Service calls User Service. How do you ensure User Service doesn't break Order Service's expectations?

```js
// Consumer side (Order Service) — defines what it expects from User Service
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');
const { string, integer, eachLike } = MatchersV3;

const provider = new PactV3({
  consumer: 'OrderService',
  provider: 'UserService',
  dir: './pacts', // generates pact contract file
});

describe('Order Service → User Service contract', () => {
  it('can fetch a user by ID', async () => {
    provider
      .given('user 42 exists')
      .uponReceiving('a request for user 42')
      .withRequest({ method: 'GET', path: '/users/42' })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: string('42'),
          name: string('John Doe'),
          email: string('john@example.com'),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const user = await fetchUser(mockServer.url, '42');
      expect(user.id).toBe('42');
      expect(user.name).toBeDefined();
    });
  });

  it('returns 404 for non-existent user', async () => {
    provider
      .given('user 999 does not exist')
      .uponReceiving('a request for non-existent user')
      .withRequest({ method: 'GET', path: '/users/999' })
      .willRespondWith({ status: 404 });

    await provider.executeTest(async (mockServer) => {
      await expect(fetchUser(mockServer.url, '999')).rejects.toThrow('User not found');
    });
  });
});

// Provider side (User Service) — verifies it satisfies the contract
const { Verifier } = require('@pact-foundation/pact');

describe('User Service contract verification', () => {
  it('satisfies Order Service contract', async () => {
    await new Verifier({
      providerBaseUrl: 'http://localhost:3001',
      pactUrls: ['./pacts/orderservice-userservice.json'],
      stateHandlers: {
        'user 42 exists': async () => {
          await db('users').insert({ id: '42', name: 'John Doe', email: 'john@example.com' });
        },
        'user 999 does not exist': async () => {
          await db('users').where({ id: '999' }).delete();
        },
      },
    }).verifyProvider();
  });
});
```

**Answer**: Contract testing ensures services don't break each other. Consumer defines expectations (generates a pact file). Provider verifies it meets those expectations. Run in CI — if verification fails, the deploy is blocked.

---

## Q14. (Advanced) How do you write load/performance tests for a backend API?

```js
// Using k6 (Go-based load testing tool, scriptable in JS)
// k6 is NOT Node.js — it's a standalone tool

// loadtest.js — run with: k6 run loadtest.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const orderDuration = new Trend('order_creation_duration');

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // ramp up to 50 users
    { duration: '1m', target: 50 },    // hold at 50
    { duration: '30s', target: 200 },  // spike to 200
    { duration: '1m', target: 200 },   // hold at 200
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95th percentile < 500ms
    errors: ['rate<0.01'],             // error rate < 1%
  },
};

export default function () {
  // Login
  const loginRes = http.post('http://api:3000/auth/login', JSON.stringify({
    email: `user${__VU}@test.com`, password: 'test123',
  }), { headers: { 'Content-Type': 'application/json' } });

  const token = loginRes.json('token');

  // Create order
  const start = Date.now();
  const orderRes = http.post('http://api:3000/orders', JSON.stringify({
    items: [{ productId: 'p1', qty: 1 }],
  }), {
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  });

  orderDuration.add(Date.now() - start);
  errorRate.add(orderRes.status !== 201);

  check(orderRes, {
    'order created': (r) => r.status === 201,
    'has order id': (r) => r.json('id') !== undefined,
  });

  sleep(1); // think time between requests
}
```

**Answer**: Load testing reveals bottlenecks before production traffic does. Test scenarios: ramp-up, steady state, spike, soak (long duration). Key metrics: p95 latency, error rate, throughput (req/s). Run regularly in CI against staging.

---

## Q15. (Advanced) How do you test database migrations?

```js
// Test that migrations run cleanly and are reversible
describe('Database Migrations', () => {
  let testDb;

  beforeAll(async () => {
    testDb = knex({ client: 'pg', connection: process.env.TEST_DB_URL });
  });

  afterAll(async () => { await testDb.destroy(); });

  it('runs all migrations forward', async () => {
    await testDb.migrate.latest();
    const [, migrations] = await testDb.migrate.list();
    expect(migrations).toHaveLength(0); // all applied, none pending
  });

  it('can rollback and re-apply', async () => {
    await testDb.migrate.rollback(undefined, true); // rollback all
    await testDb.migrate.latest();
    // No errors = success
  });

  it('preserves data during migration', async () => {
    // Setup: create data in pre-migration state
    await testDb.migrate.latest();
    await testDb('users').insert({ id: '1', name: 'John', email: 'j@t.com' });

    // Apply new migration (e.g., adding a column)
    // In practice, you'd test a specific migration
    const users = await testDb('users').where({ id: '1' });
    expect(users[0].name).toBe('John');
  });

  it('adds NOT NULL column with default value correctly', async () => {
    // Specific migration test: adding a 'status' column with default 'active'
    await testDb.migrate.latest();
    await testDb('users').insert({ id: '2', name: 'Jane', email: 'jane@t.com' });

    // After migration, existing rows should have default value
    const user = await testDb('users').where({ id: '2' }).first();
    expect(user.status).toBe('active');
  });
});
```

---

## Q16. (Advanced) How do you test WebSocket connections?

```js
const WebSocket = require('ws');

describe('WebSocket Chat', () => {
  let server;
  let port;

  beforeAll((done) => {
    server = createServer(); // your HTTP + WS server
    server.listen(0, () => { // random available port
      port = server.address().port;
      done();
    });
  });

  afterAll((done) => { server.close(done); });

  function createClient(token) {
    return new Promise((resolve) => {
      const ws = new WebSocket(`ws://localhost:${port}/ws?token=${token}`);
      ws.on('open', () => resolve(ws));
    });
  }

  function waitForMessage(ws) {
    return new Promise((resolve) => {
      ws.once('message', (data) => resolve(JSON.parse(data.toString())));
    });
  }

  it('authenticates and receives welcome message', async () => {
    const ws = await createClient(testToken);
    const msg = await waitForMessage(ws);

    expect(msg.type).toBe('welcome');
    ws.close();
  });

  it('broadcasts messages to room members', async () => {
    const ws1 = await createClient(user1Token);
    const ws2 = await createClient(user2Token);

    // Both join room
    ws1.send(JSON.stringify({ type: 'join', roomId: 'room-1' }));
    ws2.send(JSON.stringify({ type: 'join', roomId: 'room-1' }));
    await new Promise(r => setTimeout(r, 100)); // wait for joins

    // User 1 sends message
    ws1.send(JSON.stringify({ type: 'chat', roomId: 'room-1', text: 'Hello!' }));

    // User 2 should receive it
    const msg = await waitForMessage(ws2);
    expect(msg.type).toBe('chat');
    expect(msg.text).toBe('Hello!');

    ws1.close();
    ws2.close();
  });

  it('rejects unauthenticated connections', async () => {
    const ws = new WebSocket(`ws://localhost:${port}/ws`);
    const closePromise = new Promise((resolve) => {
      ws.on('close', (code) => resolve(code));
    });
    const code = await closePromise;
    expect(code).toBe(4001); // custom auth error code
  });
});
```

---

## Q17. (Advanced) How do you achieve test isolation and prevent test pollution?

```js
// Problem: Test A leaves data in DB, Test B depends on that state (or is broken by it)

// Solution 1: Transaction rollback (fastest)
const { beforeEach, afterEach } = require('@jest/globals');

let trx;
beforeEach(async () => {
  trx = await db.transaction();
  // All queries in this test use `trx` instead of `db`
});

afterEach(async () => {
  await trx.rollback(); // rollback everything — DB unchanged
});

// Solution 2: Truncate tables (works across connections)
beforeEach(async () => {
  await db.raw('TRUNCATE orders, users, payments CASCADE');
});

// Solution 3: Database per test (slowest, most isolated)
// Testcontainers creates fresh DB for each test suite

// Environment isolation
beforeEach(() => {
  // Reset environment variables
  process.env.FEATURE_NEW_CHECKOUT = 'false';
  // Reset singletons
  jest.resetModules();
  // Clear caches
  cache.clear();
});

// Mock isolation
afterEach(() => {
  jest.restoreAllMocks(); // restore original implementations
  nock.cleanAll();        // clean HTTP mocks
});
```

**Answer**: Test isolation means each test runs independently — no shared state. Use transaction rollback (fastest), table truncation (reliable), or separate containers (most isolated). Always restore mocks and clear caches between tests.

---

## Q18. (Advanced) How do you test cron jobs and scheduled tasks?

```js
// Testing scheduled tasks requires controlling time

describe('Daily report generator', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('generates report at midnight', async () => {
    const generateReport = jest.fn().mockResolvedValue({ sent: true });
    const cron = require('node-cron');

    // Schedule task
    cron.schedule('0 0 * * *', generateReport);

    // Advance time to midnight
    jest.setSystemTime(new Date('2024-01-15T23:59:59'));
    jest.advanceTimersByTime(2000); // tick past midnight

    expect(generateReport).toHaveBeenCalledTimes(1);
  });

  it('handles report generation failure', async () => {
    const generateReport = jest.fn()
      .mockRejectedValueOnce(new Error('DB timeout'))
      .mockResolvedValueOnce({ sent: true });

    const task = new RetryableTask(generateReport, { maxRetries: 3 });
    await task.run();

    expect(generateReport).toHaveBeenCalledTimes(2); // retry succeeded
  });
});

// Testing the actual report logic separately
describe('ReportGenerator', () => {
  it('aggregates sales data for the previous day', async () => {
    // Setup: create orders for yesterday
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    await createOrder(db, { createdAt: yesterday, total: 100 });
    await createOrder(db, { createdAt: yesterday, total: 200 });
    await createOrder(db, { createdAt: new Date(), total: 500 }); // today — should be excluded

    const report = await ReportGenerator.generate(yesterday);

    expect(report.totalRevenue).toBe(300);
    expect(report.orderCount).toBe(2);
  });
});
```

---

## Q19. (Advanced) How do you set up CI/CD pipeline for running tests?

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env: { POSTGRES_DB: test, POSTGRES_PASSWORD: test }
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:integration
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]  # run after other tests pass
    steps:
      - uses: actions/checkout@v4
      - run: docker-compose -f docker-compose.test.yml up -d
      - run: npm run test:e2e
      - run: docker-compose -f docker-compose.test.yml down
```

```json
// package.json scripts
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest --testPathPattern=test/unit",
    "test:integration": "jest --testPathPattern=test/integration --runInBand",
    "test:e2e": "jest --testPathPattern=test/e2e --runInBand",
    "test:watch": "jest --watch"
  }
}
```

---

## Q20. (Advanced) Senior red flags in backend testing.

**Answer**:

1. **No tests at all** — "it works on my machine" is not a test strategy
2. **Only happy path tests** — no error scenarios, edge cases, or auth tests
3. **Mocking everything** — unit tests pass but integration is broken. Testing mocks, not behavior.
4. **Slow test suite** — 30+ minute CI pipeline. Developers skip running tests locally.
5. **Flaky tests** — tests that sometimes pass, sometimes fail. Erode trust in the suite.
6. **Test pollution** — tests depend on execution order or shared state
7. **No integration tests with real DB** — SQL bugs, constraint violations, migration issues go undetected
8. **Testing implementation, not behavior** — tests break on refactoring even when behavior is unchanged
9. **No contract tests** — deploying service A breaks service B
10. **Ignoring test coverage of error paths** — the `catch` block is never tested

```js
// RED FLAG: testing implementation details
it('calls repository.save()', async () => {
  await createUser({ name: 'John' });
  expect(mockRepo.save).toHaveBeenCalled(); // breaks if you refactor to use .create()
});

// BETTER: testing behavior
it('persists user and returns it', async () => {
  const user = await createUser({ name: 'John' });
  const found = await findUser(user.id);
  expect(found.name).toBe('John'); // behavior unchanged regardless of internal implementation
});
```

**Senior interview answer**: "I follow the testing pyramid — many fast unit tests for business logic, integration tests with real databases for data layer, contract tests for service boundaries, and a few E2E tests for critical flows. I use Testcontainers for realistic DB testing, factory functions for readable test data, and transaction rollback for test isolation. I aim for 80% coverage with focus on error paths, auth, and edge cases — not just happy paths."
