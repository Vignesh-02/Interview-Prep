# 9. Security, Validation & Injection Prevention

## Topic Introduction

Backend security is about **preventing unauthorized access** and **protecting data integrity**. The three pillars for Node.js APIs: (1) **Input validation** — reject malformed data, (2) **Injection prevention** — never trust user input in queries/commands, (3) **Defense in depth** — layers of security at every level.

```
Untrusted Input → Validate (schema) → Sanitize → Parameterized Query → Response (encode)
                   │                    │              │
                   └─ Reject if invalid └─ Strip HTML  └─ Never concatenate SQL
```

The OWASP Top 10 is your checklist: Injection, Broken Auth, Sensitive Data Exposure, XXE, Broken Access Control, Security Misconfiguration, XSS, Insecure Deserialization, Using Components with Known Vulnerabilities, Insufficient Logging.

**Go/Java tradeoff**: Go's strong typing prevents some injection issues. Java's Spring Security provides declarative security. Node.js relies more on middleware (helmet, cors) and manual validation (Zod, Joi). The vulnerability classes are the same across all languages.

---

## Q1. (Beginner) What is SQL injection? Show a vulnerable Node.js example and the fix.

```js
// VULNERABLE — string concatenation
app.get('/users', async (req, res) => {
  const name = req.query.name;
  const result = await db.query(`SELECT * FROM users WHERE name = '${name}'`);
  // Attacker sends: ?name=' OR '1'='1
  // Query becomes: SELECT * FROM users WHERE name = '' OR '1'='1'
  // Returns ALL users!
  res.json(result.rows);
});

// FIXED — parameterized query
app.get('/users', async (req, res) => {
  const result = await db.query('SELECT * FROM users WHERE name = $1', [req.query.name]);
  // $1 is treated as DATA, never as SQL
  res.json(result.rows);
});
```

**Answer**: SQL injection occurs when user input is embedded directly in SQL strings. The fix is **always** use parameterized queries (prepared statements). The database treats parameters as data, not SQL code. This is language-agnostic — the same rule applies in Go, Java, Python.

---

## Q2. (Beginner) How do you validate request bodies in Node.js? Show a Zod example.

```js
const { z } = require('zod');

const createUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(13).max(150),
  role: z.enum(['user', 'admin']).default('user'),
});

app.post('/users', (req, res) => {
  const result = createUserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({
      error: 'Validation failed',
      details: result.error.issues,
    });
  }
  // result.data is typed and validated
  createUser(result.data);
});
```

**Answer**: Always validate **ALL** incoming data (body, query params, headers). Use schema validation libraries (Zod, Joi, yup) for type-safe, declarative validation. Reject invalid requests with descriptive errors (400 Bad Request). Never rely on frontend validation alone.

---

## Q3. (Beginner) What security headers should every Node.js API set? What does `helmet` do?

```js
const helmet = require('helmet');
app.use(helmet()); // sets multiple security headers

// Equivalent to:
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');        // prevent MIME sniffing
  res.setHeader('X-Frame-Options', 'DENY');                   // prevent clickjacking
  res.setHeader('Strict-Transport-Security', 'max-age=31536000'); // force HTTPS
  res.setHeader('X-XSS-Protection', '0');                     // disable legacy XSS filter
  res.setHeader('Content-Security-Policy', "default-src 'self'"); // CSP
  res.removeHeader('X-Powered-By');                           // hide Express
  next();
});
```

**Answer**: `helmet` sets security-related HTTP headers that protect against common web attacks. Every Node.js API should use it as baseline security. Additional headers for APIs: `Cache-Control: no-store` for sensitive data, `X-Request-Id` for tracing.

---

## Q4. (Beginner) What is CORS and how do you configure it properly?

```js
const cors = require('cors');

// BAD — allows everything (development only!)
app.use(cors());

// GOOD — restrict to known origins
app.use(cors({
  origin: ['https://myapp.com', 'https://admin.myapp.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true, // allow cookies
  maxAge: 86400, // cache preflight for 24 hours
}));

// Dynamic origin (multi-tenant)
app.use(cors({
  origin: (origin, callback) => {
    const allowed = allowedOrigins.includes(origin);
    callback(null, allowed ? origin : false);
  },
}));
```

**Answer**: CORS (Cross-Origin Resource Sharing) controls which domains can call your API from a browser. Always whitelist specific origins in production. `credentials: true` allows cookies — requires specific origin (not `*`).

---

## Q5. (Beginner) What is the difference between authentication and authorization?

**Answer**:

| | **Authentication** (AuthN) | **Authorization** (AuthZ) |
|---|---|---|
| Question | "Who are you?" | "What can you do?" |
| Implementation | Login, JWT, session | Roles, permissions, policies |
| Failure | 401 Unauthorized | 403 Forbidden |

```js
// Authentication middleware — verifies identity
async function authenticate(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch { res.status(401).json({ error: 'Invalid token' }); }
}

// Authorization middleware — checks permissions
function authorize(...roles) {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
}

app.delete('/users/:id', authenticate, authorize('admin'), deleteUser);
```

---

## Q6. (Intermediate) What is NoSQL injection? How do you prevent it in MongoDB?

```js
// VULNERABLE — MongoDB operator injection
app.post('/login', async (req, res) => {
  const user = await db.collection('users').findOne({
    username: req.body.username,
    password: req.body.password,
  });
  // Attacker sends: { "username": "admin", "password": {"$gt": ""} }
  // Query becomes: find({ username: "admin", password: { $gt: "" } })
  // Matches admin user because password > "" is true!
});

// FIXED — validate types explicitly
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  if (typeof username !== 'string' || typeof password !== 'string') {
    return res.status(400).json({ error: 'Invalid input' });
  }
  // Or use Zod
  const schema = z.object({
    username: z.string(),
    password: z.string(),
  });
  const data = schema.parse(req.body);
  // Now safe — data.password is guaranteed to be a string, not an object
});
```

**Answer**: MongoDB queries can be injected with operator objects (`$gt`, `$ne`, `$regex`). Prevent by: (1) validating input types (string, not object), (2) using schema validation, (3) using `mongo-sanitize` to strip `$` operators.

---

## Q7. (Intermediate) How do you prevent prototype pollution in Node.js?

```js
// VULNERABLE — merging user input into objects
function merge(target, source) {
  for (const key in source) {
    if (typeof source[key] === 'object') {
      target[key] = merge(target[key] || {}, source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

// Attacker sends: { "__proto__": { "isAdmin": true } }
merge({}, userInput);
// Now ALL objects have isAdmin = true!
({}).isAdmin // true — prototype polluted!

// FIXED — block dangerous keys
function safeMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') continue;
    if (typeof source[key] === 'object' && source[key] !== null) {
      target[key] = safeMerge(target[key] || {}, source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

// BEST: use Object.create(null) for config objects, or use libraries like lodash (patched)
```

---

## Q8. (Intermediate) How do you securely store and compare passwords?

```js
const bcrypt = require('bcrypt');
const SALT_ROUNDS = 12; // higher = slower = more secure

// Registration — hash password
async function registerUser(email, password) {
  const hash = await bcrypt.hash(password, SALT_ROUNDS); // ~250ms with 12 rounds
  await db.query('INSERT INTO users(email, password_hash) VALUES($1, $2)', [email, hash]);
}

// Login — compare password
async function loginUser(email, password) {
  const user = await db.query('SELECT * FROM users WHERE email = $1', [email]);
  if (!user.rows[0]) throw new Error('User not found');

  const match = await bcrypt.compare(password, user.rows[0].password_hash);
  if (!match) throw new Error('Invalid password');
  return user.rows[0];
}
```

**Answer**: Never store plaintext passwords. Use `bcrypt` (or `argon2`) with sufficient rounds. `bcrypt` is intentionally slow (CPU-intensive) to resist brute force. Use **async** `bcrypt.hash()` to avoid blocking the event loop.

**Tradeoff**: `argon2` is newer and resists GPU attacks better than `bcrypt`. But `bcrypt` is battle-tested and widely supported. For Node.js, use `bcrypt` (async) or `argon2` — never `crypto.createHash('sha256')` for passwords.

---

## Q9. (Intermediate) How do you prevent SSRF (Server-Side Request Forgery)?

**Scenario**: Your API fetches a URL provided by the user (e.g., webhook URL, profile picture URL).

```js
// VULNERABLE — user can fetch internal resources
app.post('/fetch-url', async (req, res) => {
  const data = await fetch(req.body.url); // Attacker sends: http://169.254.169.254/latest/meta-data/
  res.json(await data.json());            // Returns AWS metadata (IAM credentials!)
});

// FIXED — validate URL before fetching
const { URL } = require('url');

function isUrlSafe(urlString) {
  try {
    const url = new URL(urlString);
    // Block internal IPs
    const blocked = ['127.0.0.1', 'localhost', '169.254.169.254', '10.', '172.16.', '192.168.'];
    if (blocked.some(b => url.hostname.startsWith(b) || url.hostname === b)) return false;
    // Only allow HTTPS
    if (url.protocol !== 'https:') return false;
    return true;
  } catch { return false; }
}

app.post('/fetch-url', async (req, res) => {
  if (!isUrlSafe(req.body.url)) return res.status(400).json({ error: 'URL not allowed' });
  const data = await fetch(req.body.url);
  res.json(await data.json());
});
```

---

## Q10. (Intermediate) How do you implement request rate limiting and brute force protection for login?

```js
// Multi-layer login protection
const loginLimiter = {
  // Layer 1: Per-IP (catches basic brute force)
  perIp: rateLimit({ key: req => req.ip, limit: 10, window: 900 }), // 10 attempts / 15 min

  // Layer 2: Per-account (catches distributed brute force)
  perAccount: async (req, res, next) => {
    const { email } = req.body;
    const attempts = await redis.incr(`login-fail:${email}`);
    if (attempts === 1) await redis.expire(`login-fail:${email}`, 900);
    if (attempts > 5) {
      return res.status(429).json({
        error: 'Account temporarily locked',
        retryAfter: await redis.ttl(`login-fail:${email}`),
      });
    }
    next();
  },

  // Layer 3: CAPTCHA after 3 failed attempts
  captcha: async (req, res, next) => {
    const attempts = await redis.get(`login-fail:${req.body.email}`);
    if (parseInt(attempts) >= 3 && !req.body.captchaToken) {
      return res.status(400).json({ error: 'CAPTCHA required', captchaRequired: true });
    }
    next();
  },
};

app.post('/login', loginLimiter.perIp, loginLimiter.perAccount, loginLimiter.captcha, loginHandler);

// On successful login, reset failure counter
async function onLoginSuccess(email) {
  await redis.del(`login-fail:${email}`);
}
```

---

## Q11. (Intermediate) How do you prevent sensitive data leaks in API responses?

```js
// BAD — returning full user object including password hash
app.get('/users/:id', async (req, res) => {
  const user = await db.query('SELECT * FROM users WHERE id = $1', [req.params.id]);
  res.json(user.rows[0]); // includes password_hash, internal_notes, ssn!
});

// GOOD — explicit field selection
app.get('/users/:id', async (req, res) => {
  const user = await db.query(
    'SELECT id, name, email, avatar, created_at FROM users WHERE id = $1',
    [req.params.id]
  );
  res.json(user.rows[0]);
});

// BETTER — response schema (whitelist fields)
const publicUserSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string(),
  avatar: z.string().nullable(),
  createdAt: z.string(),
});

app.get('/users/:id', async (req, res) => {
  const user = await db.query('SELECT * FROM users WHERE id = $1', [req.params.id]);
  const safe = publicUserSchema.parse(user.rows[0]); // strips unknown fields
  res.json(safe);
});
```

---

## Q12. (Intermediate) How do you secure environment variables and secrets in a Node.js app?

```js
// DON'T: hardcode secrets
const stripe = require('stripe')('sk_live_abcdef123456'); // RED FLAG

// DO: use environment variables
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

// Validate all required env vars at startup
const required = ['DATABASE_URL', 'JWT_SECRET', 'STRIPE_SECRET_KEY', 'REDIS_URL'];
for (const env of required) {
  if (!process.env[env]) {
    console.error(`Missing required env var: ${env}`);
    process.exit(1);
  }
}

// Never log secrets
app.use((req, res, next) => {
  // DON'T log headers (may contain Authorization)
  console.log(req.method, req.path); // OK
  // console.log(req.headers); // RED FLAG — contains auth tokens
  next();
});
```

**Best practices**: (1) Use `.env` files only in development (never commit), (2) Use secret managers in production (Vault, AWS Secrets Manager), (3) Rotate secrets regularly, (4) Validate presence at startup, (5) Never log or expose in error responses.

---

## Q13. (Advanced) Production scenario: You discover a SQL injection vulnerability in a production API. Walk through your incident response.

**Answer**:

```
Timeline:
1. DETECT: Anomalous DB query patterns in monitoring
2. ASSESS: Determine scope — which endpoints, what data accessible
3. MITIGATE: Deploy patch or disable endpoint immediately
4. INVESTIGATE: Check logs for exploitation
5. REMEDIATE: Fix code, audit all queries, add security tests
6. COMMUNICATE: Notify affected users if data was accessed
```

```js
// Immediate patch (within minutes)
// Before: vulnerable
const result = await db.query(`SELECT * FROM orders WHERE id = ${req.params.id}`);

// After: parameterized
const result = await db.query('SELECT * FROM orders WHERE id = $1', [req.params.id]);

// Post-incident: add security scanner to CI
// eslint-plugin-security detects string concatenation in queries
// snyk test — checks dependencies for known vulnerabilities
```

**Post-incident audit**:
1. Grep codebase for string concatenation in queries
2. Add ESLint rule for `no-unsafe-query`
3. Add parameterized query requirement to code review checklist
4. Run `npm audit` and fix vulnerabilities
5. Implement WAF rule to detect SQL injection patterns

---

## Q14. (Advanced) How do you implement RBAC (Role-Based Access Control) with fine-grained permissions?

```js
// Permission model
const PERMISSIONS = {
  admin: ['users:read', 'users:write', 'users:delete', 'orders:read', 'orders:write', 'reports:read'],
  manager: ['users:read', 'orders:read', 'orders:write', 'reports:read'],
  user: ['orders:read', 'orders:write:own'], // 'own' = only their own orders
};

function requirePermission(permission) {
  return (req, res, next) => {
    const userPerms = PERMISSIONS[req.user.role] || [];
    const hasExact = userPerms.includes(permission);
    const hasOwn = userPerms.includes(`${permission}:own`);

    if (!hasExact && !hasOwn) {
      return res.status(403).json({ error: `Missing permission: ${permission}` });
    }

    if (hasOwn && !hasExact) {
      // Add ownership filter to request
      req.ownershipFilter = { userId: req.user.id };
    }

    next();
  };
}

app.get('/orders', authenticate, requirePermission('orders:read'), async (req, res) => {
  const filter = req.ownershipFilter
    ? 'WHERE user_id = $1'
    : '';
  const params = req.ownershipFilter ? [req.user.id] : [];
  const orders = await db.query(`SELECT * FROM orders ${filter}`, params);
  res.json(orders.rows);
});
```

---

## Q15. (Advanced) How do you prevent ReDoS (Regular Expression Denial of Service)?

```js
// VULNERABLE — catastrophic backtracking
const emailRegex = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z]{2,4})+$/;
// Input: "a".repeat(100) + "@" → takes SECONDS to fail

// SAFE — use validated libraries
const { z } = require('zod');
const schema = z.object({
  email: z.string().email(), // Zod's built-in email validation (safe regex)
});

// SAFE — use re2 (linear-time regex engine)
const RE2 = require('re2');
const safeRegex = new RE2('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$');

// Detection: test regexes with safe-regex or rxxr2
const safe = require('safe-regex');
console.log(safe(/^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z]{2,4})+$/)); // false
```

**Answer**: ReDoS exploits regex backtracking. A crafted input makes the regex engine take exponential time, blocking the event loop. Prevention: (1) Use `re2` (linear-time), (2) Use validation libraries instead of custom regex, (3) Set timeouts on regex operations, (4) Test with `safe-regex`.

---

## Q16. (Advanced) How do you implement API key authentication securely?

```js
const crypto = require('crypto');

// Generate API key (store hash in DB, return key to user once)
function generateApiKey() {
  const key = `sk_live_${crypto.randomBytes(32).toString('hex')}`;
  const hash = crypto.createHash('sha256').update(key).digest('hex');
  return { key, hash }; // store hash in DB, return key to user
}

// Authenticate via API key
async function apiKeyAuth(req, res, next) {
  const key = req.headers['x-api-key'];
  if (!key) return res.status(401).json({ error: 'API key required' });

  const hash = crypto.createHash('sha256').update(key).digest('hex');
  const apiKey = await db.query(
    'SELECT * FROM api_keys WHERE key_hash = $1 AND revoked = false',
    [hash]
  );

  if (!apiKey.rows[0]) return res.status(401).json({ error: 'Invalid API key' });
  if (apiKey.rows[0].expires_at < new Date()) return res.status(401).json({ error: 'Key expired' });

  req.user = { id: apiKey.rows[0].user_id, keyId: apiKey.rows[0].id };
  next();
}
```

**Answer**: Store only the **hash** of API keys (like passwords). When authenticating, hash the provided key and compare. This way, if your database is compromised, attackers can't use the keys. Add expiration, revocation, and per-key rate limits.

---

## Q17. (Advanced) How do you handle security in a microservices architecture?

**Answer**:

```
External Client → API Gateway (auth, rate limit, WAF)
                     │
              ┌──────┼──────┐
              │      │      │
          Service A  Service B  Service C
              │      │      │
              └──mTLS/JWT────┘  (internal auth)
```

```js
// Service-to-service auth with JWT
function createServiceToken(serviceName) {
  return jwt.sign({ service: serviceName, iat: Date.now() },
    process.env.SERVICE_JWT_SECRET, { expiresIn: '5m' }
  );
}

// Internal middleware — verify service identity
function verifyService(req, res, next) {
  const token = req.headers['x-service-token'];
  try {
    req.service = jwt.verify(token, process.env.SERVICE_JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid service token' });
  }
}
```

**Layers**: (1) API Gateway validates external auth, (2) Services use mTLS or JWT for internal auth, (3) Each service has minimal permissions (least privilege), (4) Network policies restrict which services can communicate.

---

## Q18. (Advanced) How do you audit and log security events without exposing sensitive data?

```js
function auditLog(event) {
  const sanitized = {
    timestamp: new Date().toISOString(),
    action: event.action,
    userId: event.userId,
    ip: event.ip,
    userAgent: event.userAgent,
    success: event.success,
    // NEVER log: passwords, tokens, credit cards, SSN
    // DO log: action, who, when, from where, success/failure
  };
  logger.info('AUDIT', sanitized);
}

// Usage
app.post('/login', async (req, res) => {
  try {
    const user = await loginUser(req.body.email, req.body.password);
    auditLog({ action: 'LOGIN', userId: user.id, ip: req.ip, success: true });
    res.json({ token: generateToken(user) });
  } catch (err) {
    auditLog({ action: 'LOGIN_FAILED', ip: req.ip, success: false,
               userAgent: req.headers['user-agent'] });
    res.status(401).json({ error: 'Invalid credentials' });
  }
});
```

---

## Q19. (Advanced) How do you implement Content Security Policy (CSP) and prevent XSS for APIs that serve HTML?

```js
// For APIs serving HTML (SSR, admin panels)
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", "'nonce-abc123'"], // allow scripts with nonce
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", "data:", "https://cdn.example.com"],
    connectSrc: ["'self'", "https://api.example.com"],
    frameSrc: ["'none'"],
    objectSrc: ["'none'"],
  },
}));

// For pure JSON APIs — prevent XSS in JSON responses
app.use((req, res, next) => {
  res.setHeader('Content-Type', 'application/json'); // never text/html
  res.setHeader('X-Content-Type-Options', 'nosniff'); // prevent browser guessing
  next();
});
```

---

## Q20. (Advanced) Senior security red flags in code reviews.

**Answer**:

1. **String concatenation in SQL/NoSQL queries** — injection
2. **`JSON.parse` without try/catch** — crashes on malformed input
3. **No input validation on any endpoint** — accepts anything
4. **Secrets in source code or logs** — API keys, passwords in code
5. **Using `eval()` or `new Function()`** — code injection
6. **No CORS configuration** — defaults to allowing everything
7. **`express.static` serving `.env` or `node_modules`** — leaks secrets
8. **Password stored as MD5/SHA256** — use bcrypt/argon2
9. **JWT with `none` algorithm accepted** — bypasses signature verification
10. **Error messages exposing stack traces** — information disclosure

```js
// RED FLAG: error handler leaking internals
app.use((err, req, res, next) => {
  res.status(500).json({ error: err.message, stack: err.stack }); // NEVER in production
});

// FIX:
app.use((err, req, res, next) => {
  console.error(err); // log full error server-side
  res.status(500).json({ error: 'Internal server error' }); // generic response to client
});
```

**Senior interview answer**: "I implement defense in depth: input validation with schema libraries, parameterized queries everywhere, security headers via helmet, RBAC for access control, audit logging for security events, and automated security scanning in CI/CD."
