# 7. Rate Limiting & Abuse Prevention

## Topic Introduction

Rate limiting **controls how many requests** a client can make in a given time window. Without it, a single user can DOS your service, brute-force passwords, scrape your data, or exhaust your API quotas.

```
Client (IP/User) → Rate Limiter → Allowed? ─ Yes → Handler
                                            └ No  → 429 Too Many Requests
```

Common algorithms: **Fixed Window**, **Sliding Window**, **Token Bucket**, **Leaky Bucket**. Each has different tradeoffs for burst handling, accuracy, and implementation complexity.

**Production reality**: At scale, rate limiting must be **distributed** (Redis) and **layered** (edge/CDN → API gateway → application). A startup can use in-process limiting; an enterprise needs multi-tier defense.

**Go/Java tradeoff**: Go has `golang.org/x/time/rate` (token bucket) built into the ecosystem. Java uses Resilience4j or Bucket4j. Node.js typically uses `express-rate-limit` or custom Redis-based solutions. The algorithms are identical across languages.

---

## Q1. (Beginner) What is rate limiting? Why is it necessary for a backend API?

**Scenario**: Your login endpoint has no rate limit. An attacker sends 10,000 login attempts per second to brute-force passwords.

```js
// Without rate limiting: anyone can hammer your API
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body); // called 10,000 times/sec by attacker
  // CPU maxed, legit users can't log in
});
```

**Answer**: Rate limiting prevents abuse by capping requests per client per time window. It protects against: brute force attacks, DDoS, resource exhaustion, API abuse (scraping, bot traffic), and runaway client bugs.

---

## Q2. (Beginner) What is a token bucket algorithm? Show a simple implementation.

```js
class TokenBucket {
  constructor(capacity, refillRate) {
    this.capacity = capacity;     // max tokens (burst size)
    this.tokens = capacity;       // current tokens
    this.refillRate = refillRate; // tokens per second
    this.lastRefill = Date.now();
  }

  consume(count = 1) {
    this.refill();
    if (this.tokens >= count) {
      this.tokens -= count;
      return true; // allowed
    }
    return false; // rate limited
  }

  refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }
}

// 10 requests/sec with burst up to 20
const bucket = new TokenBucket(20, 10);

app.use((req, res, next) => {
  if (bucket.consume()) return next();
  res.status(429).json({ error: 'Too many requests' });
});
```

**Answer**: Token bucket allows **bursts** up to capacity, then throttles to the refill rate. It's the most common algorithm because it handles both sustained load and traffic spikes.

---

## Q3. (Beginner) What HTTP headers should you return with rate-limited responses?

```js
app.use(async (req, res, next) => {
  const result = await checkRateLimit(req.ip);

  // Standard rate limit headers (RFC 6585 + draft-ietf-httpapi-ratelimit-headers)
  res.setHeader('RateLimit-Limit', result.limit);        // max requests in window
  res.setHeader('RateLimit-Remaining', result.remaining); // requests left
  res.setHeader('RateLimit-Reset', result.resetAt);       // when window resets (epoch)
  res.setHeader('Retry-After', result.retryAfter);        // seconds until allowed

  if (!result.allowed) {
    return res.status(429).json({
      error: 'Rate limit exceeded',
      retryAfter: result.retryAfter,
    });
  }
  next();
});
```

**Answer**: Return `429 Too Many Requests` with `Retry-After`, `RateLimit-Remaining`, and `RateLimit-Reset` headers. This helps clients implement backoff and reduces unnecessary retries.

---

## Q4. (Beginner) What is the difference between per-IP, per-user, and per-route rate limiting?

**Answer**:

| Scope | Key | When |
|-------|-----|------|
| **Per-IP** | Client IP | Unauthenticated endpoints, login |
| **Per-User** | User ID / API key | Authenticated API (fair usage) |
| **Per-Route** | Route + User/IP | Protect expensive endpoints |
| **Global** | None (total) | Protect backend capacity |

```js
// Per-IP for login
app.post('/login', rateLimit({ key: req => req.ip, limit: 5, window: 60 }), loginHandler);

// Per-user for API
app.use('/api', rateLimit({ key: req => req.user.id, limit: 100, window: 60 }), apiRouter);

// Per-route for expensive operations
app.post('/reports', rateLimit({ key: req => req.user.id, limit: 5, window: 3600 }), reportHandler);
```

---

## Q5. (Beginner) What is the difference between fixed window and sliding window rate limiting?

**Answer**:

```
Fixed Window (1 min window, 10 req limit):
  [00:00 - 01:00] = 10 requests allowed
  [01:00 - 02:00] = 10 requests allowed
  Problem: User sends 10 at 00:59 and 10 at 01:01 → 20 in 2 seconds!

Sliding Window (60 sec window, 10 req limit):
  Always checks the last 60 seconds from NOW
  At 01:01, it counts requests from 00:01 to 01:01
  No boundary spike problem
```

```js
// Fixed window (simple but has boundary problem)
async function fixedWindow(key, limit, windowSec) {
  const window = Math.floor(Date.now() / (windowSec * 1000));
  const redisKey = `rate:${key}:${window}`;
  const count = await redis.incr(redisKey);
  if (count === 1) await redis.expire(redisKey, windowSec);
  return count <= limit;
}

// Sliding window log (accurate but more memory)
async function slidingWindow(key, limit, windowSec) {
  const now = Date.now();
  const pipe = redis.pipeline();
  pipe.zremrangebyscore(key, 0, now - windowSec * 1000); // prune old
  pipe.zadd(key, now, `${now}:${Math.random()}`);         // add current
  pipe.zcard(key);                                          // count
  pipe.expire(key, windowSec);
  const results = await pipe.exec();
  return results[2][1] <= limit;
}
```

---

## Q6. (Intermediate) How do you implement distributed rate limiting with Redis?

**Scenario**: You have 10 Node.js pods behind a load balancer. Rate limit must be shared across all pods.

```js
// Sliding window counter using Redis (distributed, accurate)
async function rateLimitRedis(userId, limit = 100, windowSec = 60) {
  const key = `ratelimit:${userId}`;
  const now = Date.now();

  // Lua script for atomic sliding window (single Redis call)
  const script = `
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])

    redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
    local count = redis.call('ZCARD', key)

    if count < limit then
      redis.call('ZADD', key, now, now .. '-' .. math.random())
      redis.call('EXPIRE', key, math.ceil(window / 1000))
      return count + 1
    end
    return -1
  `;

  const result = await redis.eval(script, 1, key, now, windowSec * 1000, limit);
  return {
    allowed: result !== -1,
    remaining: result === -1 ? 0 : limit - result,
  };
}
```

**Answer**: Use a **Lua script** for atomicity — all operations (prune, count, add) happen in a single Redis call with no race conditions. This works across all Node.js pods because Redis is the shared state.

---

## Q7. (Intermediate) How do you implement tiered rate limits (free vs premium users)?

```js
const TIERS = {
  free:    { limit: 100,  window: 3600 }, // 100/hour
  pro:     { limit: 1000, window: 3600 }, // 1000/hour
  enterprise: { limit: 10000, window: 3600 }, // 10000/hour
};

app.use(async (req, res, next) => {
  const user = req.user;
  const tier = TIERS[user?.plan || 'free'];

  const result = await rateLimitRedis(
    user?.id || req.ip,
    tier.limit,
    tier.window
  );

  res.setHeader('RateLimit-Limit', tier.limit);
  res.setHeader('RateLimit-Remaining', result.remaining);

  if (!result.allowed) {
    return res.status(429).json({
      error: 'Rate limit exceeded',
      upgrade: user?.plan === 'free' ? 'Upgrade to Pro for higher limits' : undefined,
    });
  }
  next();
});
```

**Answer**: Look up the user's plan and apply different limits. Free users get lower limits, paid users get higher. Include upgrade prompts in 429 responses for free-tier users. Store tier config externally (DB/config) so limits can be changed without deploys.

---

## Q8. (Intermediate) How do you protect against distributed denial of service (DDoS) at the application layer?

**Answer**: Application-layer DDoS defense is **multi-layered**:

```
Layer 1: CDN/Edge (Cloudflare, AWS Shield)
  → Block known bad IPs, absorb volume attacks

Layer 2: Load Balancer / WAF
  → Rate limit by IP, block suspicious patterns

Layer 3: API Gateway (Kong, nginx)
  → Per-route rate limits, request size limits

Layer 4: Application
  → Per-user limits, CAPTCHA on login, request validation
```

```js
// Application-level defenses
app.use(helmet()); // security headers
app.use(express.json({ limit: '100kb' })); // prevent large payload attacks

// Slow loris protection (slow HTTP headers)
const server = http.createServer(app);
server.headersTimeout = 10000; // 10s max for headers
server.requestTimeout = 30000; // 30s max for full request

// Connection limiting per IP
const connections = new Map();
server.on('connection', (socket) => {
  const ip = socket.remoteAddress;
  const count = (connections.get(ip) || 0) + 1;
  connections.set(ip, count);
  if (count > 100) socket.destroy(); // too many connections from one IP
  socket.on('close', () => connections.set(ip, connections.get(ip) - 1));
});
```

---

## Q9. (Intermediate) How do you implement rate limiting for WebSocket connections?

```js
const WebSocket = require('ws');
const wss = new WebSocket.Server({ server });

// Rate limit per connection (messages per second)
wss.on('connection', (ws, req) => {
  const userId = authenticate(req);
  const bucket = new TokenBucket(20, 10); // 10 msg/sec, burst 20

  ws.on('message', (data) => {
    if (!bucket.consume()) {
      ws.send(JSON.stringify({ error: 'Rate limited', retryAfter: 1 }));
      return;
    }

    // Also limit message size
    if (data.length > 10240) { // 10KB max
      ws.send(JSON.stringify({ error: 'Message too large' }));
      return;
    }

    handleMessage(userId, data);
  });
});
```

**Answer**: WebSocket rate limiting is per-connection (message rate) AND per-user (across connections). Use token bucket for burst tolerance. Also limit: connection count per user, message size, and subscription count.

---

## Q10. (Intermediate) How do you implement graceful degradation when rate limited (instead of hard rejection)?

**Answer**: Instead of always returning 429, degrade the response quality:

```js
app.get('/search', async (req, res) => {
  const rateStatus = await checkRateLimit(req.user.id);

  if (rateStatus.remaining > 50) {
    // Full response — fresh data, all fields
    const results = await searchWithFullFeatures(req.query);
    res.json(results);
  } else if (rateStatus.remaining > 0) {
    // Degraded — cached results, limited fields
    const cached = await redis.get(`search:${req.query.q}`);
    if (cached) return res.json({ ...JSON.parse(cached), _degraded: true });
    const results = await searchBasic(req.query);
    res.json({ ...results, _degraded: true });
  } else {
    // Hard limit
    res.status(429).json({ error: 'Rate limit exceeded', retryAfter: rateStatus.retryAfter });
  }
});
```

**Answer**: Graceful degradation serves cached/simplified responses as the user approaches the limit, reserving hard 429s for abuse. This improves user experience for legitimate users who occasionally burst.

---

## Q11. (Intermediate) How do you test rate limiting? What edge cases should you cover?

```js
describe('Rate Limiting', () => {
  it('allows requests within limit', async () => {
    for (let i = 0; i < 10; i++) {
      const res = await request(app).get('/api/data').set('Authorization', 'Bearer token');
      expect(res.status).toBe(200);
      expect(res.headers['ratelimit-remaining']).toBe(String(9 - i));
    }
  });

  it('returns 429 when limit exceeded', async () => {
    // Exhaust limit
    for (let i = 0; i < 10; i++) await request(app).get('/api/data').set('Authorization', 'Bearer token');
    // Next request should be rejected
    const res = await request(app).get('/api/data').set('Authorization', 'Bearer token');
    expect(res.status).toBe(429);
    expect(res.body.retryAfter).toBeGreaterThan(0);
  });

  it('resets after window expires', async () => {
    // Exhaust limit
    // Advance time (using fake timers or short window)
    // Verify requests are allowed again
  });

  it('limits per-user not per-IP', async () => {
    // User A is rate limited
    // User B from same IP should NOT be limited
  });

  it('handles Redis failure gracefully', async () => {
    // Redis down → should either allow (fail-open) or reject (fail-close)
    // Decision depends on security requirements
  });
});
```

---

## Q12. (Intermediate) What is the leaky bucket algorithm? How is it different from token bucket?

**Answer**:

| | **Token Bucket** | **Leaky Bucket** |
|---|---|---|
| Allows bursts | Yes (up to capacity) | No (constant rate) |
| Analogy | Bucket fills with tokens | Bucket leaks at constant rate |
| Behavior | Bursty then throttled | Always constant output rate |
| Use case | API rate limiting | Traffic shaping, queue processing |

```js
// Leaky bucket — processes requests at a constant rate
class LeakyBucket {
  constructor(rate) {
    this.rate = rate; // requests per second
    this.queue = [];
    this.processing = false;
  }

  add(requestHandler) {
    return new Promise((resolve, reject) => {
      this.queue.push({ handler: requestHandler, resolve, reject });
      if (!this.processing) this.drain();
    });
  }

  async drain() {
    this.processing = true;
    while (this.queue.length > 0) {
      const { handler, resolve, reject } = this.queue.shift();
      try { resolve(await handler()); }
      catch (err) { reject(err); }
      await new Promise(r => setTimeout(r, 1000 / this.rate));
    }
    this.processing = false;
  }
}

// Usage: process at most 10 requests/sec
const bucket = new LeakyBucket(10);
app.post('/webhook', (req, res) => {
  bucket.add(() => processWebhook(req.body))
    .then(result => res.json(result))
    .catch(err => res.status(500).json({ error: err.message }));
});
```

---

## Q13. (Advanced) Production scenario: Your rate limiter uses Redis. What happens during a Redis failover and how do you handle it?

**Answer**: During Redis failover (typically 5-30 seconds), rate limit checks fail.

```js
async function rateLimitWithFallback(key, limit, window) {
  try {
    return await rateLimitRedis(key, limit, window);
  } catch (redisErr) {
    console.error('Redis rate limit failed:', redisErr.message);

    // Decision: fail-open or fail-closed?
    // For most APIs: fail-OPEN (allow requests, accept temporary abuse)
    // For security-critical (login): fail-CLOSED (reject, protect against brute force)

    if (isSecurityCritical(key)) {
      return { allowed: false, remaining: 0, retryAfter: 10 }; // fail-closed
    }
    return { allowed: true, remaining: limit, retryAfter: 0 }; // fail-open
  }
}
```

**Answer**: Decision depends on the endpoint's security posture. Login/payment endpoints should fail-closed (reject requests if rate limiting is unavailable). Regular API endpoints can fail-open to maintain availability. Log the failure and alert the team.

---

## Q14. (Advanced) How do you implement rate limiting at the API gateway level (nginx) to protect upstream Node.js?

```nginx
# nginx rate limiting configuration
http {
    # Define rate limit zones
    limit_req_zone $binary_remote_addr zone=ip:10m rate=10r/s;
    limit_req_zone $http_authorization zone=user:10m rate=100r/m;

    server {
        # Per-IP limit with burst
        location /api/ {
            limit_req zone=ip burst=20 nodelay;
            limit_req_status 429;
            proxy_pass http://node_backend;
        }

        # Stricter limit for login
        location /auth/login {
            limit_req zone=ip burst=5;
            limit_req_status 429;
            proxy_pass http://node_backend;
        }
    }
}
```

**Answer**: nginx handles rate limiting BEFORE requests reach Node.js. This protects your app from high-volume attacks without wasting Node.js event loop cycles. nginx is C-based and can handle millions of requests for rate limit checks.

**Layered approach**: nginx (blunt per-IP) → application (smart per-user with tiering) → per-route (expensive endpoints).

---

## Q15. (Advanced) How do you implement adaptive rate limiting that adjusts based on server load?

```js
const { monitorEventLoopDelay } = require('perf_hooks');
const histogram = monitorEventLoopDelay();
histogram.enable();

function getAdaptiveLimit(baseLimit) {
  const lagMs = histogram.mean / 1e6;

  if (lagMs > 200) return Math.floor(baseLimit * 0.25); // severe: 25% of base
  if (lagMs > 100) return Math.floor(baseLimit * 0.5);  // stressed: 50%
  if (lagMs > 50)  return Math.floor(baseLimit * 0.75); // moderate: 75%
  return baseLimit; // healthy: full limit
}

app.use(async (req, res, next) => {
  const adaptiveLimit = getAdaptiveLimit(100);
  const result = await rateLimitRedis(req.user?.id || req.ip, adaptiveLimit, 60);

  if (!result.allowed) {
    return res.status(429).json({
      error: 'Rate limit exceeded',
      note: 'Limits reduced due to high server load',
    });
  }
  next();
});
```

**Answer**: Adaptive rate limiting tightens limits when the server is under stress (high event loop lag, high CPU). This acts as an automatic circuit breaker — when the system is overwhelmed, it sheds load by reducing the rate limit.

---

## Q16. (Advanced) How do you implement API quotas (monthly limits) vs rate limits (per-second)?

**Answer**: Quotas and rate limits serve different purposes:

| | **Rate Limit** | **Quota** |
|---|---|---|
| Window | Seconds to minutes | Hours to months |
| Purpose | Prevent abuse/overload | Control resource usage |
| Example | 100 req/min | 10,000 req/month |
| Response | 429 (retry soon) | 403 (upgrade plan) |

```js
async function checkQuotaAndRateLimit(userId, plan) {
  // Rate limit (short window)
  const rateResult = await rateLimitRedis(`rate:${userId}`, TIERS[plan].rateLimit, 60);
  if (!rateResult.allowed) {
    return { allowed: false, reason: 'rate_limit', retryAfter: 60 };
  }

  // Quota (monthly)
  const quotaKey = `quota:${userId}:${new Date().toISOString().slice(0, 7)}`; // 2024-01
  const used = await redis.incr(quotaKey);
  if (used === 1) await redis.expire(quotaKey, 35 * 86400); // 35 days (covers month)

  if (used > TIERS[plan].monthlyQuota) {
    return { allowed: false, reason: 'quota_exceeded', upgradeUrl: '/pricing' };
  }

  return { allowed: true, rateRemaining: rateResult.remaining, quotaUsed: used };
}
```

---

## Q17. (Advanced) How do you prevent sophisticated abuse like distributed scraping (many IPs, low rate per IP)?

**Answer**: Distributed scrapers use different IPs to stay under per-IP limits. Defenses:

```js
// 1. Fingerprinting — group requests by behavior pattern
function createFingerprint(req) {
  return crypto.createHash('sha256').update([
    req.headers['user-agent'],
    req.headers['accept-language'],
    req.headers['accept-encoding'],
  ].join('|')).digest('hex').slice(0, 16);
}

// 2. Rate limit by fingerprint (catches distributed scrapers)
app.use(async (req, res, next) => {
  const fp = createFingerprint(req);
  const result = await rateLimitRedis(`fp:${fp}`, 1000, 3600);
  if (!result.allowed) return res.status(429).end();
  next();
});

// 3. Behavioral analysis — detect patterns
// - Sequential page access (page 1, 2, 3, 4...)
// - No CSS/image requests (bot doesn't render)
// - Unusual headers or missing cookies
// - High speed with no think time

// 4. CAPTCHA challenge on suspicious behavior
// 5. Honeypot endpoints (trap scrapers)
```

---

## Q18. (Advanced) How do you implement rate limiting for GraphQL (where one "request" can vary wildly in cost)?

```js
// GraphQL query complexity analysis
const { getComplexity, simpleEstimator } = require('graphql-query-complexity');

app.use('/graphql', async (req, res, next) => {
  const complexity = getComplexity({
    schema,
    query: req.body.query,
    estimators: [simpleEstimator({ defaultComplexity: 1 })],
  });

  // Rate limit by complexity cost, not request count
  const cost = Math.ceil(complexity);
  const result = await rateLimitRedis(
    `gql:${req.user.id}`,
    1000,  // 1000 complexity points per minute
    60
  );

  // Consume 'cost' tokens instead of 1
  if (result.remaining < cost) {
    return res.status(429).json({
      error: 'Rate limit exceeded',
      complexity: cost,
      remaining: result.remaining,
    });
  }

  next();
});
```

**Answer**: For GraphQL, rate limit by **query complexity** (cost), not request count. A simple `{ user { name } }` costs 1, but `{ users { posts { comments { author } } } }` costs 1000+. This prevents expensive queries from bypassing simple request-count limits.

---

## Q19. (Advanced) How do rate limiting implementations compare across Go, Java, and Node.js?

**Answer**:

```go
// Go — built-in rate limiter
import "golang.org/x/time/rate"

limiter := rate.NewLimiter(rate.Limit(10), 20) // 10/sec, burst 20
if !limiter.Allow() {
    http.Error(w, "rate limited", http.StatusTooManyRequests)
    return
}
// Advantage: in-process, zero-allocation, goroutine-safe
```

```java
// Java — Resilience4j
RateLimiter limiter = RateLimiter.of("api", RateLimiterConfig.custom()
    .limitForPeriod(10)
    .limitRefreshPeriod(Duration.ofSeconds(1))
    .build());

Supplier<Response> decorated = RateLimiter.decorateSupplier(limiter, () -> callService());
// Advantage: decorator pattern, integrates with Spring
```

```js
// Node.js — Redis-based for distributed
const result = await redis.eval(luaScript, 1, key, ...args);
// Advantage: distributed by default, works across cluster workers
```

**Key difference**: Go and Java can use in-process limiters effectively because they're multi-threaded. Node.js in cluster mode needs distributed state (Redis) because each worker is a separate process.

---

## Q20. (Advanced) Senior red flags in rate limiting code reviews.

**Answer**:

1. **No rate limiting at all on public endpoints** — open to abuse
2. **In-process rate limiting in clustered Node.js** — each worker has its own counter, limits multiplied
3. **Only per-IP limiting** — misses authenticated abuse; NAT causes false positives
4. **No rate limit headers in response** — clients can't implement backoff
5. **Fail-open on security-critical endpoints** (login, password reset) — allows brute force during Redis failure
6. **Rate limit AFTER expensive computation** — damage already done
7. **No different limits for different endpoints** — expensive endpoints (/reports) need tighter limits
8. **Hardcoded limits** — can't adjust without deploy
9. **No monitoring of 429 responses** — can't distinguish abuse from legitimate traffic

**Senior interview answer**: "Rate limiting must be distributed, layered (edge → gateway → app), tiered by user plan, adaptive to server load, and monitored. I fail-closed on security endpoints and fail-open on regular APIs."
