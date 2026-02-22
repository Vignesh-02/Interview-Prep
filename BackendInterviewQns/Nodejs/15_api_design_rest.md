# 15. API Design, REST & Versioning

## Topic Introduction

Good API design determines how easy your service is to use, maintain, and evolve. **REST** (Representational State Transfer) is the most common API paradigm, built on HTTP semantics: resources as URLs, HTTP methods as verbs, status codes for outcomes.

```
GET    /api/v1/users          → List users
POST   /api/v1/users          → Create user
GET    /api/v1/users/42       → Get user 42
PUT    /api/v1/users/42       → Replace user 42
PATCH  /api/v1/users/42       → Partial update user 42
DELETE /api/v1/users/42       → Delete user 42
```

A well-designed API is: **consistent** (predictable patterns), **discoverable** (self-documenting), **evolvable** (versioning without breaking clients), and **secure** (proper auth, validation, rate limiting).

**Go/Java tradeoff**: Go's `net/http` is minimal — you design everything. Java Spring Boot provides opinionated structure with annotations. Node.js Express is flexible but needs discipline. The design principles are identical across languages.

---

## Q1. (Beginner) What are RESTful naming conventions? Show correct and incorrect examples.

**Answer**:

```
✅ GOOD                        ❌ BAD
GET /users                     GET /getUsers
GET /users/42                  GET /user?id=42
POST /users                    POST /createUser
GET /users/42/orders           GET /getOrdersByUser?userId=42
DELETE /users/42               POST /deleteUser
PUT /users/42                  POST /updateUser
```

**Rules**: (1) Use **nouns** not verbs, (2) Use **plural** resources, (3) Use **path params** for identification, (4) Use **query params** for filtering/sorting, (5) **Nest** related resources.

---

## Q2. (Beginner) What HTTP status codes should a REST API return?

```js
// 2xx Success
res.status(200).json(data);      // OK — general success
res.status(201).json(created);   // Created — after POST
res.status(202).json({ jobId }); // Accepted — async processing
res.status(204).end();           // No Content — after DELETE

// 4xx Client Error
res.status(400).json({ error: 'Invalid input' });       // Bad Request
res.status(401).json({ error: 'Not authenticated' });    // Unauthorized
res.status(403).json({ error: 'Not allowed' });          // Forbidden
res.status(404).json({ error: 'Not found' });            // Not Found
res.status(409).json({ error: 'Conflict' });             // Conflict (duplicate)
res.status(422).json({ error: 'Validation failed' });    // Unprocessable Entity
res.status(429).json({ error: 'Rate limited' });         // Too Many Requests

// 5xx Server Error
res.status(500).json({ error: 'Internal server error' }); // Server bug
res.status(502).json({ error: 'Upstream failed' });        // Bad Gateway
res.status(503).json({ error: 'Service unavailable' });    // Overloaded/maintenance
```

---

## Q3. (Beginner) How do you design consistent error responses?

```js
// Standard error response format
class ApiError extends Error {
  constructor(status, code, message, details = null) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// Error handler middleware
app.use((err, req, res, next) => {
  if (err instanceof ApiError) {
    return res.status(err.status).json({
      error: { code: err.code, message: err.message, details: err.details },
    });
  }
  console.error(err);
  res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' } });
});

// Usage
throw new ApiError(404, 'USER_NOT_FOUND', 'User with ID 42 not found');
throw new ApiError(422, 'VALIDATION_ERROR', 'Invalid input', [
  { field: 'email', message: 'Must be a valid email' },
  { field: 'age', message: 'Must be at least 13' },
]);
```

---

## Q4. (Beginner) How do you implement pagination in a REST API?

```js
// Cursor-based pagination (recommended)
app.get('/api/posts', async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit) || 20, 100);
  const cursor = req.query.cursor;

  const query = cursor
    ? 'SELECT * FROM posts WHERE id < $1 ORDER BY id DESC LIMIT $2'
    : 'SELECT * FROM posts ORDER BY id DESC LIMIT $1';
  const params = cursor ? [cursor, limit + 1] : [limit + 1];

  const result = await pool.query(query, params);
  const hasMore = result.rows.length > limit;
  const data = result.rows.slice(0, limit);

  res.json({
    data,
    pagination: {
      hasMore,
      nextCursor: hasMore ? data[data.length - 1].id : null,
    },
  });
});
```

---

## Q5. (Beginner) How do you implement filtering, sorting, and field selection?

```js
// GET /api/products?category=electronics&sort=-price&fields=id,name,price&minPrice=100
app.get('/api/products', async (req, res) => {
  let query = 'SELECT ';
  const params = [];
  let paramIdx = 1;

  // Field selection
  const fields = req.query.fields?.split(',').filter(f => ALLOWED_FIELDS.includes(f));
  query += fields?.length ? fields.join(', ') : '*';
  query += ' FROM products WHERE 1=1';

  // Filtering
  if (req.query.category) {
    query += ` AND category = $${paramIdx++}`;
    params.push(req.query.category);
  }
  if (req.query.minPrice) {
    query += ` AND price >= $${paramIdx++}`;
    params.push(parseFloat(req.query.minPrice));
  }

  // Sorting
  const sortField = req.query.sort?.replace('-', '');
  if (SORTABLE_FIELDS.includes(sortField)) {
    const direction = req.query.sort.startsWith('-') ? 'DESC' : 'ASC';
    query += ` ORDER BY ${sortField} ${direction}`;
  }

  query += ` LIMIT 20`;
  const result = await pool.query(query, params);
  res.json({ data: result.rows });
});
```

---

## Q6. (Intermediate) How do you version your API? Compare URL, header, and query param approaches.

| Approach | Example | Pros | Cons |
|----------|---------|------|------|
| **URL path** | `/api/v1/users` | Clear, easy to test | URL changes on version bump |
| **Header** | `Accept: application/vnd.myapp.v2+json` | Clean URLs | Harder to test/discover |
| **Query param** | `/api/users?version=2` | Easy to switch | Pollutes query string |

```js
// URL-based versioning (most common, recommended)
const v1Router = express.Router();
const v2Router = express.Router();

v1Router.get('/users', async (req, res) => {
  const users = await db.query('SELECT id, name, email FROM users');
  res.json(users.rows); // v1 response shape
});

v2Router.get('/users', async (req, res) => {
  const users = await db.query('SELECT id, name, email, avatar, created_at FROM users');
  res.json({
    data: users.rows,       // v2 wraps in data
    meta: { total: users.rowCount },
  });
});

app.use('/api/v1', v1Router);
app.use('/api/v2', v2Router);
```

---

## Q7. (Intermediate) How do you design idempotent PUT vs PATCH? What's the difference?

```js
// PUT — Replace entire resource (idempotent)
app.put('/api/users/:id', async (req, res) => {
  const { name, email, age, role } = req.body; // ALL fields required
  const result = await db.query(
    'UPDATE users SET name=$1, email=$2, age=$3, role=$4 WHERE id=$5 RETURNING *',
    [name, email, age, role, req.params.id]
  );
  res.json(result.rows[0]);
});

// PATCH — Partial update (may or may not be idempotent)
app.patch('/api/users/:id', async (req, res) => {
  const updates = {};
  if (req.body.name !== undefined) updates.name = req.body.name;
  if (req.body.email !== undefined) updates.email = req.body.email;

  const setClauses = Object.keys(updates).map((k, i) => `${k} = $${i + 1}`);
  const values = Object.values(updates);
  values.push(req.params.id);

  const result = await db.query(
    `UPDATE users SET ${setClauses.join(', ')} WHERE id = $${values.length} RETURNING *`,
    values
  );
  res.json(result.rows[0]);
});
```

---

## Q8. (Intermediate) How do you handle long-running operations in a REST API?

```js
// Pattern: Async operation with polling
app.post('/api/reports', authenticate, async (req, res) => {
  const job = await reportQueue.add('generate', req.body);
  res.status(202).json({
    jobId: job.id,
    status: 'processing',
    statusUrl: `/api/reports/${job.id}/status`,
  });
});

app.get('/api/reports/:jobId/status', async (req, res) => {
  const job = await reportQueue.getJob(req.params.jobId);
  const state = await job.getState();

  res.json({
    jobId: job.id,
    status: state,
    progress: job.progress,
    result: state === 'completed' ? job.returnvalue : undefined,
  });
});
```

---

## Q9. (Intermediate) How do you implement HATEOAS (Hypermedia as the Engine of Application State)?

```js
app.get('/api/orders/:id', async (req, res) => {
  const order = await getOrder(req.params.id);
  res.json({
    ...order,
    _links: {
      self: { href: `/api/orders/${order.id}` },
      user: { href: `/api/users/${order.userId}` },
      items: { href: `/api/orders/${order.id}/items` },
      cancel: order.status === 'pending' ? { href: `/api/orders/${order.id}/cancel`, method: 'POST' } : undefined,
      pay: order.status === 'pending' ? { href: `/api/orders/${order.id}/pay`, method: 'POST' } : undefined,
    },
  });
});
```

---

## Q10. (Intermediate) How do you design bulk operations in REST?

```js
// Bulk create
app.post('/api/users/bulk', async (req, res) => {
  const users = req.body.users; // array of users
  if (users.length > 100) return res.status(400).json({ error: 'Max 100 items' });

  const results = [];
  for (const user of users) {
    try {
      const result = await createUser(user);
      results.push({ status: 'created', data: result });
    } catch (err) {
      results.push({ status: 'error', error: err.message, input: user });
    }
  }

  const allSuccess = results.every(r => r.status === 'created');
  res.status(allSuccess ? 201 : 207).json({ results }); // 207 = Multi-Status
});
```

---

## Q11. (Intermediate) How do you implement request/response validation with OpenAPI/Swagger?

```js
const { OpenApiValidator } = require('express-openapi-validator');

// Validate all requests/responses against your OpenAPI spec
app.use(OpenApiValidator.middleware({
  apiSpec: './openapi.yaml',
  validateRequests: true,
  validateResponses: true,
}));

// openapi.yaml defines schemas for all endpoints
// Any request not matching the schema → automatic 400
// Any response not matching → logged as server error
```

---

## Q12. (Intermediate) How do you handle API deprecation gracefully?

```js
// Deprecation middleware
function deprecated(sunset, alternative) {
  return (req, res, next) => {
    res.setHeader('Deprecation', 'true');
    res.setHeader('Sunset', sunset); // RFC 8594
    res.setHeader('Link', `<${alternative}>; rel="successor-version"`);
    logger.warn({ path: req.path, sunset }, 'Deprecated endpoint called');
    next();
  };
}

app.get('/api/v1/users', deprecated('2025-06-01', '/api/v2/users'), v1GetUsers);
```

---

## Q13. (Advanced) Design a REST API for a complex resource with nested relationships, versioning, and pagination.

```js
// GET /api/v2/organizations/42/teams?status=active&sort=-memberCount&cursor=abc&limit=10
app.get('/api/v2/organizations/:orgId/teams', authenticate, authorize('teams:read'), async (req, res) => {
  const { orgId } = req.params;
  const { status, sort, cursor, limit: rawLimit } = req.query;
  const limit = Math.min(parseInt(rawLimit) || 20, 100);

  let query = `SELECT t.*, COUNT(tm.user_id) as member_count
    FROM teams t LEFT JOIN team_members tm ON tm.team_id = t.id
    WHERE t.organization_id = $1`;
  const params = [orgId];
  let paramIdx = 2;

  if (status) { query += ` AND t.status = $${paramIdx++}`; params.push(status); }
  if (cursor) { query += ` AND t.id < $${paramIdx++}`; params.push(cursor); }

  query += ` GROUP BY t.id`;
  const sortField = sort === '-memberCount' ? 'member_count DESC' : 'member_count ASC';
  query += ` ORDER BY ${sortField}, t.id DESC LIMIT $${paramIdx}`;
  params.push(limit + 1);

  const result = await pool.query(query, params);
  const hasMore = result.rows.length > limit;
  const data = result.rows.slice(0, limit);

  res.json({
    data: data.map(t => ({
      ...t,
      _links: {
        self: `/api/v2/organizations/${orgId}/teams/${t.id}`,
        members: `/api/v2/organizations/${orgId}/teams/${t.id}/members`,
      },
    })),
    pagination: { hasMore, nextCursor: hasMore ? data[data.length - 1].id : null },
    _links: { self: req.originalUrl, organization: `/api/v2/organizations/${orgId}` },
  });
});
```

---

## Q14. (Advanced) How do you handle backward compatibility when evolving API schemas?

```js
// Rule 1: Adding fields is safe (non-breaking)
// v1: { id, name, email }
// v2: { id, name, email, avatar, createdAt }  ← additive, clients ignore unknown fields

// Rule 2: Removing fields breaks clients (breaking change)
// Solution: keep old fields, add new ones, deprecate old

// Rule 3: Changing field types breaks clients
// Solution: add new field with new type, keep old
// v1: { date: "2024-01-01" }         ← string
// v2: { date: "2024-01-01", dateISO: "2024-01-01T00:00:00Z" }  ← keep both

// Response transformer for backward compatibility
function transformForVersion(data, version) {
  if (version === 1) {
    return { id: data.id, name: data.name, email: data.email }; // v1 shape
  }
  return data; // v2 returns everything
}
```

---

## Q15. (Advanced) How do you implement rate limiting per API tier with different limits per endpoint?

```js
const RATE_LIMITS = {
  free: {
    default: { limit: 100, window: 3600 },
    '/api/*/search': { limit: 10, window: 3600 },
    '/api/*/export': { limit: 5, window: 86400 },
  },
  pro: {
    default: { limit: 1000, window: 3600 },
    '/api/*/search': { limit: 100, window: 3600 },
    '/api/*/export': { limit: 50, window: 86400 },
  },
};

function getLimit(plan, path) {
  const limits = RATE_LIMITS[plan] || RATE_LIMITS.free;
  const matchedRoute = Object.keys(limits).find(pattern =>
    pattern !== 'default' && new RegExp(pattern.replace(/\*/g, '[^/]+')).test(path)
  );
  return limits[matchedRoute] || limits.default;
}
```

---

## Q16. (Advanced) How do you implement content negotiation (JSON, XML, CSV)?

```js
app.get('/api/users', async (req, res) => {
  const users = await getUsers();

  switch (req.accepts(['json', 'xml', 'csv'])) {
    case 'json':
      res.json(users);
      break;
    case 'csv':
      res.setHeader('Content-Type', 'text/csv');
      const csv = [Object.keys(users[0]).join(','), ...users.map(u => Object.values(u).join(','))].join('\n');
      res.send(csv);
      break;
    case 'xml':
      res.setHeader('Content-Type', 'application/xml');
      res.send(jsonToXml(users));
      break;
    default:
      res.status(406).json({ error: 'Not Acceptable' });
  }
});
```

---

## Q17. (Advanced) How do you design a webhook API for third-party integrations?

```js
// Webhook registration
app.post('/api/webhooks', authenticate, async (req, res) => {
  const { url, events, secret } = req.body;
  // Validate URL is reachable
  const webhook = await db.query(
    'INSERT INTO webhooks(user_id, url, events, secret) VALUES($1,$2,$3,$4) RETURNING *',
    [req.user.id, url, events, secret || crypto.randomBytes(32).toString('hex')]
  );
  res.status(201).json(webhook.rows[0]);
});

// Webhook delivery with signature
async function deliverWebhook(webhook, event, payload) {
  const body = JSON.stringify({ event, data: payload, timestamp: new Date().toISOString() });
  const signature = crypto.createHmac('sha256', webhook.secret).update(body).digest('hex');
  await webhookQueue.add('deliver', {
    webhookId: webhook.id, url: webhook.url, body, signature,
  }, { attempts: 5, backoff: { type: 'exponential', delay: 60000 } });
}
```

---

## Q18. (Advanced) How do you implement ETag-based caching for REST APIs?

```js
const crypto = require('crypto');

app.get('/api/products/:id', async (req, res) => {
  const product = await getProduct(req.params.id);
  const etag = crypto.createHash('md5').update(JSON.stringify(product)).digest('hex');

  if (req.headers['if-none-match'] === etag) {
    return res.status(304).end(); // Not Modified — client cache is valid
  }

  res.setHeader('ETag', etag);
  res.setHeader('Cache-Control', 'private, max-age=0, must-revalidate');
  res.json(product);
});
```

---

## Q19. (Advanced) How do you design an API for file operations (upload, download, processing)?

```js
// Multipart upload with metadata
app.post('/api/documents', authenticate, upload.single('file'), async (req, res) => {
  const doc = await db.query(
    'INSERT INTO documents(user_id, name, size, mime_type, s3_key) VALUES($1,$2,$3,$4,$5) RETURNING *',
    [req.user.id, req.file.originalname, req.file.size, req.file.mimetype, req.file.key]
  );
  res.status(201).json({
    ...doc.rows[0],
    _links: {
      self: `/api/documents/${doc.rows[0].id}`,
      download: `/api/documents/${doc.rows[0].id}/download`,
      thumbnail: `/api/documents/${doc.rows[0].id}/thumbnail`,
    },
  });
});

// Download with streaming
app.get('/api/documents/:id/download', authenticate, async (req, res) => {
  const doc = await getDocument(req.params.id);
  res.setHeader('Content-Disposition', `attachment; filename="${doc.name}"`);
  res.setHeader('Content-Type', doc.mime_type);
  const stream = s3.getObject({ Bucket: 'docs', Key: doc.s3_key }).createReadStream();
  stream.pipe(res);
});
```

---

## Q20. (Advanced) Senior API design red flags in code reviews.

**Answer**:

1. **Using verbs in URLs** — `POST /createUser` instead of `POST /users`
2. **Inconsistent response shapes** — some endpoints wrap in `{ data }`, others don't
3. **No pagination on list endpoints** — `SELECT *` returns all rows
4. **200 OK for errors** — returning `{ success: false }` instead of proper status codes
5. **No input validation** — accepting whatever the client sends
6. **Leaking internal IDs or database structure** — exposing auto-increment IDs or table names
7. **Breaking changes without versioning** — renaming fields in existing endpoints
8. **No documentation** — no OpenAPI spec, no examples
9. **Inconsistent naming** — mixing camelCase and snake_case in the same API
10. **No rate limiting or authentication on public endpoints**

**Senior interview answer**: "I design APIs with consistent resource naming, proper HTTP semantics, cursor-based pagination, schema validation, versioning from day one, and comprehensive OpenAPI documentation. I follow the principle of least surprise — any developer using my API should be able to guess the next endpoint's shape."
