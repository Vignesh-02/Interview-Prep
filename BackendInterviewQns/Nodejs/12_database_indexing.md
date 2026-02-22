# 12. Database Indexing & Query Optimization

## Topic Introduction

Indexes are **data structures** (B-trees, hash tables, GiST) that speed up database lookups from **O(n) full table scan** to **O(log n) index seek**. They're the single most impactful performance optimization for any backend.

```
Without index: Scan 10 million rows → 5 seconds
With index:    B-tree lookup → 2 milliseconds
```

But indexes aren't free: they consume **storage** and slow **writes** (every INSERT/UPDATE must update the index). The skill is knowing **what** to index, **when** to add composite indexes, and **how** to read query execution plans.

**Go/Java tradeoff**: Indexing is database-level, not language-level. The concepts are identical. However, ORMs in Java (Hibernate) and Node.js (Prisma, TypeORM) can generate unexpected queries that bypass indexes. Understanding `EXPLAIN` is critical regardless of language.

---

## Q1. (Beginner) What is a database index? How does it speed up queries?

**Scenario**: You have 10 million users. `SELECT * FROM users WHERE email = 'alice@example.com'` takes 5 seconds.

```sql
-- Without index: full table scan (reads every row)
EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';
-- Seq Scan on users  (cost=0.00..185000.00 rows=1)
-- Actual time: 5200ms

-- Create index
CREATE INDEX idx_users_email ON users(email);

-- With index: index scan (reads 1-3 pages)
EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';
-- Index Scan using idx_users_email  (cost=0.43..8.45 rows=1)
-- Actual time: 0.05ms
```

**Answer**: An index is like a book's table of contents. Instead of reading every page (row), you jump directly to the right page. PostgreSQL uses **B-tree indexes** by default, which provide O(log n) lookup for equality and range queries.

---

## Q2. (Beginner) What types of indexes does PostgreSQL support? When do you use each?

**Answer**:

| Index Type | Best For | Example |
|-----------|----------|---------|
| **B-tree** (default) | Equality, range, sorting | `WHERE id = 5`, `WHERE date > '2024-01-01'` |
| **Hash** | Equality only (faster than B-tree for =) | `WHERE session_id = 'abc'` |
| **GIN** | Full-text search, JSONB, arrays | `WHERE tags @> '{"urgent"}'` |
| **GiST** | Geometric, range types, full-text | `WHERE location <-> point(0,0) < 1000` |
| **BRIN** | Large, naturally ordered tables | `WHERE created_at > '2024-01-01'` on time-series |

```sql
-- B-tree (default, most common)
CREATE INDEX idx_orders_user ON orders(user_id);

-- GIN for JSONB queries
CREATE INDEX idx_products_tags ON products USING GIN(metadata);
-- Enables: SELECT * FROM products WHERE metadata @> '{"color": "red"}';

-- BRIN for time-series (very small index)
CREATE INDEX idx_logs_timestamp ON logs USING BRIN(created_at);
-- Good when data is physically ordered by time
```

---

## Q3. (Beginner) What is a composite (multi-column) index? Does column order matter?

**Scenario**: You frequently query `WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC`.

```sql
-- Composite index (column order matters!)
CREATE INDEX idx_orders_user_status_date
ON orders(user_id, status, created_at DESC);

-- This index supports:
-- ✅ WHERE user_id = 1
-- ✅ WHERE user_id = 1 AND status = 'active'
-- ✅ WHERE user_id = 1 AND status = 'active' ORDER BY created_at DESC
-- ❌ WHERE status = 'active' (doesn't use leftmost column)
-- ❌ WHERE created_at > '2024-01-01' (doesn't use leftmost column)
```

**Answer**: Column order follows the **leftmost prefix** rule. The index is used only if the query includes the leftmost columns. Put the most selective (highest cardinality) column first, or the column used in equality conditions.

---

## Q4. (Beginner) How do you read an `EXPLAIN ANALYZE` output?

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42 AND created_at > '2024-01-01';
```

```
Index Scan using idx_orders_user_date on orders (cost=0.43..52.16 rows=15 width=120)
  Index Cond: ((user_id = 42) AND (created_at > '2024-01-01'))
  Actual Time: 0.025..0.130 ms
  Actual Rows: 12
  Planning Time: 0.120 ms
  Execution Time: 0.180 ms
```

**Answer**: Key things to look for:
- **Index Scan** (good) vs **Seq Scan** (bad for filtered queries)
- **Actual Time** vs **Estimated cost** (are estimates accurate?)
- **Actual Rows** vs **estimated rows** (if way off, run `ANALYZE`)
- **Planning Time + Execution Time** (where is time spent?)

```js
// In Node.js, use EXPLAIN to debug slow queries
async function debugQuery(userId) {
  const plan = await pool.query('EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = $1', [userId]);
  console.log(plan.rows.map(r => r['QUERY PLAN']).join('\n'));
}
```

---

## Q5. (Beginner) What is the cost of too many indexes?

**Answer**:

| Impact | Details |
|--------|---------|
| **Slower writes** | Every INSERT/UPDATE/DELETE must update ALL indexes on the table |
| **More storage** | Indexes can be as large as the table itself |
| **More memory** | Indexes compete for `shared_buffers` (cache) |
| **Slower VACUUM** | More index entries to clean up |
| **Confusing planner** | Too many choices can lead to suboptimal plans |

```sql
-- Check index sizes
SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find unused indexes (candidates for removal)
SELECT indexrelname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND schemaname = 'public';
-- idx_scan = 0 means the index has NEVER been used in a query
```

---

## Q6. (Intermediate) How do you identify slow queries in a Node.js + PostgreSQL application?

```js
// Method 1: Log slow queries from the application
const originalQuery = pool.query.bind(pool);
pool.query = async function (...args) {
  const start = Date.now();
  const result = await originalQuery(...args);
  const duration = Date.now() - start;
  if (duration > 100) { // > 100ms
    logger.warn({ query: args[0], params: args[1], duration }, 'Slow query');
  }
  return result;
};

// Method 2: PostgreSQL slow query log
// postgresql.conf:
// log_min_duration_statement = 100  -- log queries > 100ms

// Method 3: pg_stat_statements extension
// SELECT query, mean_time, calls, total_time
// FROM pg_stat_statements
// ORDER BY mean_time DESC LIMIT 20;
```

**Answer**: Enable `pg_stat_statements` in PostgreSQL — it tracks all query statistics. Sort by `mean_time` to find the slowest queries, or by `total_time` to find queries consuming the most total resources.

---

## Q7. (Intermediate) What is a covering index (index-only scan)? Why is it fast?

```sql
-- Regular index: look up index → go to table to get all columns
CREATE INDEX idx_orders_user ON orders(user_id);
SELECT user_id, total, created_at FROM orders WHERE user_id = 42;
-- Index Scan → must read table rows for 'total' and 'created_at'

-- Covering index: all needed columns are IN the index
CREATE INDEX idx_orders_user_covering ON orders(user_id) INCLUDE (total, created_at);
SELECT user_id, total, created_at FROM orders WHERE user_id = 42;
-- Index Only Scan → no table access needed!
```

**Answer**: A covering index includes all columns needed by the query. The database reads ONLY the index, skipping the table entirely. This is significantly faster because:
1. Index is smaller than table → fits in memory better
2. Index is physically sorted → sequential I/O
3. No random I/O to table pages

---

## Q8. (Intermediate) How do you optimize pagination queries?

```js
// BAD: OFFSET-based pagination (slow for large offsets)
app.get('/orders', async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = 20;
  const offset = (page - 1) * limit;
  // For page 5000: OFFSET 99980 → DB scans 100k rows then discards 99980
  const orders = await pool.query(
    'SELECT * FROM orders ORDER BY id DESC LIMIT $1 OFFSET $2',
    [limit, offset]
  );
  res.json(orders.rows);
});

// GOOD: Cursor-based pagination (constant performance)
app.get('/orders', async (req, res) => {
  const limit = 20;
  const cursor = req.query.cursor; // last seen ID

  let query, params;
  if (cursor) {
    query = 'SELECT * FROM orders WHERE id < $1 ORDER BY id DESC LIMIT $2';
    params = [cursor, limit];
  } else {
    query = 'SELECT * FROM orders ORDER BY id DESC LIMIT $1';
    params = [limit];
  }

  const orders = await pool.query(query, params);
  const nextCursor = orders.rows.length > 0 ? orders.rows[orders.rows.length - 1].id : null;
  res.json({ data: orders.rows, nextCursor });
});
```

**Answer**: OFFSET pagination degrades with page number (O(offset + limit)). Cursor pagination is O(limit) regardless of position. Use cursor-based for large datasets, infinite scroll, and API pagination.

---

## Q9. (Intermediate) What is a partial index? When would you use one?

```sql
-- Regular index: indexes ALL rows (10 million)
CREATE INDEX idx_orders_status ON orders(status);

-- Partial index: only indexes rows matching the condition (500 active)
CREATE INDEX idx_orders_active ON orders(user_id, created_at)
WHERE status = 'active';

-- Much smaller index, only useful for queries that include WHERE status = 'active'
SELECT * FROM orders WHERE status = 'active' AND user_id = 42 ORDER BY created_at DESC;
-- Uses idx_orders_active efficiently
```

**Answer**: Partial indexes cover a subset of rows. They're smaller, faster to maintain, and ideal when you frequently query a small subset of data (active records, recent records, non-null values).

```sql
-- Great for soft-delete patterns
CREATE INDEX idx_users_active ON users(email) WHERE deleted_at IS NULL;
```

---

## Q10. (Intermediate) How do you optimize JSON/JSONB queries in PostgreSQL?

```sql
-- JSONB column
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT,
  metadata JSONB  -- { "color": "red", "size": "L", "tags": ["sale", "new"] }
);

-- GIN index for containment queries
CREATE INDEX idx_products_metadata ON products USING GIN(metadata);

-- Efficient JSONB queries:
SELECT * FROM products WHERE metadata @> '{"color": "red"}';        -- ✅ uses GIN
SELECT * FROM products WHERE metadata->>'color' = 'red';             -- ❌ no index
SELECT * FROM products WHERE metadata ? 'color';                     -- ✅ uses GIN

-- Expression index for specific fields
CREATE INDEX idx_products_color ON products((metadata->>'color'));
SELECT * FROM products WHERE metadata->>'color' = 'red';             -- ✅ now uses index
```

**Answer**: Use **GIN** indexes for containment operators (`@>`, `?`). Use **expression indexes** for specific field lookups. Avoid indexing the entire JSONB column if you only query specific paths.

---

## Q11. (Intermediate) How do you handle N+1 query problems with proper indexing?

```js
// The N+1 problem (100 orders → 100 separate queries for items)
const orders = await db.query('SELECT * FROM orders WHERE user_id = $1 LIMIT 100', [userId]);
for (const order of orders.rows) {
  // This runs 100 times! Each query does an index lookup.
  order.items = await db.query('SELECT * FROM items WHERE order_id = $1', [order.id]);
}

// Fix 1: Single query with JOIN (best)
const ordersWithItems = await db.query(`
  SELECT o.*, json_agg(i.*) as items
  FROM orders o
  LEFT JOIN items i ON i.order_id = o.id
  WHERE o.user_id = $1
  GROUP BY o.id
  ORDER BY o.created_at DESC
  LIMIT 100
`, [userId]);

// Fix 2: Batch fetch with IN clause
const orderIds = orders.rows.map(o => o.id);
const items = await db.query('SELECT * FROM items WHERE order_id = ANY($1)', [orderIds]);
```

**Index needed**:
```sql
CREATE INDEX idx_items_order ON items(order_id); -- crucial for both fixes
```

---

## Q12. (Intermediate) How do you analyze and optimize a slow query with EXPLAIN?

**Scenario**: This query takes 8 seconds on 50M rows:

```sql
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) as order_count
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.created_at > '2024-01-01'
  AND o.status = 'completed'
GROUP BY u.id
ORDER BY order_count DESC
LIMIT 10;
```

```
Sort  (actual time=8200ms)
  └─ HashAggregate  (actual time=8100ms)
       └─ Hash Join  (actual time=7800ms)
            └─ Seq Scan on orders (actual time=7500ms, rows=5000000)
                 Filter: status = 'completed' AND created_at > '2024-01-01'
                 Rows Removed by Filter: 45000000
```

**Fix**: The Seq Scan on orders is reading 50M rows and filtering 90%. Add an index:
```sql
CREATE INDEX idx_orders_status_date ON orders(status, created_at) WHERE status = 'completed';
-- Now: Index Scan → reads only matching rows
```

---

## Q13. (Advanced) Production scenario: A table has 500M rows. Queries are slow despite indexes. What else can you do?

**Answer**:

```sql
-- 1. Table partitioning (split into manageable chunks)
CREATE TABLE orders (
  id BIGSERIAL,
  user_id INTEGER,
  created_at TIMESTAMP,
  total NUMERIC
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2024_q1 PARTITION OF orders
FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
-- Queries with date range only scan relevant partitions

-- 2. Materialized views for complex aggregations
CREATE MATERIALIZED VIEW daily_stats AS
SELECT date_trunc('day', created_at) as day, COUNT(*), SUM(total)
FROM orders GROUP BY 1;
-- Refresh periodically: REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats;

-- 3. Read replicas for heavy queries
-- Reports/analytics → read replica (doesn't slow primary)

-- 4. Archive old data
-- Move orders > 2 years to archive table
-- Main table stays fast
```

```js
// In Node.js: route heavy queries to read replica
const reportPool = new Pool({ host: 'read-replica.db.internal' });

app.get('/analytics', async (req, res) => {
  const stats = await reportPool.query('SELECT * FROM daily_stats WHERE day > $1', [startDate]);
  res.json(stats.rows);
});
```

---

## Q14. (Advanced) How do you handle database connection pool tuning for optimal query performance?

```js
// Connection pool sizing
const pool = new Pool({
  max: 20,                    // max connections
  min: 5,                     // min idle connections
  idleTimeoutMillis: 30000,   // close idle connections after 30s
  connectionTimeoutMillis: 5000, // fail if can't connect in 5s
  statement_timeout: 30000,    // kill queries longer than 30s
});

// Monitor pool health
setInterval(() => {
  console.log({
    total: pool.totalCount,
    idle: pool.idleCount,
    waiting: pool.waitingCount, // requests waiting for a connection
  });
  // Alert if waitingCount > 0 consistently → pool is too small
}, 10000);
```

**Pool sizing formula**: `max_connections = (CPU cores * 2) + effective_spindle_count`
- For a 4-core DB with SSD: max = 10-20
- For 10 app pods × 20 connections each = 200 total DB connections
- PostgreSQL default max_connections = 100 (might need increase)

---

## Q15. (Advanced) How do you implement full-text search in PostgreSQL without Elasticsearch?

```sql
-- Add tsvector column
ALTER TABLE products ADD COLUMN search_vector tsvector;

-- Populate it
UPDATE products SET search_vector =
  to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''));

-- Create GIN index
CREATE INDEX idx_products_search ON products USING GIN(search_vector);

-- Keep it updated automatically
CREATE TRIGGER products_search_update
BEFORE INSERT OR UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', name, description);
```

```js
// Search query in Node.js
app.get('/search', async (req, res) => {
  const results = await pool.query(`
    SELECT id, name, ts_rank(search_vector, query) as rank
    FROM products, plainto_tsquery('english', $1) query
    WHERE search_vector @@ query
    ORDER BY rank DESC
    LIMIT 20
  `, [req.query.q]);
  res.json(results.rows);
});
```

**Answer**: PostgreSQL's built-in full-text search with GIN index handles most search needs without Elasticsearch. Add `ts_rank` for relevance ranking. For complex search (fuzzy, facets, suggestions), consider Elasticsearch.

---

## Q16. (Advanced) How do you prevent and detect index bloat?

```sql
-- Check index bloat
SELECT
  schemaname || '.' || indexrelname as index,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  idx_scan as scans,
  idx_tup_read as tuples_read
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Rebuild bloated indexes (online, non-blocking)
REINDEX INDEX CONCURRENTLY idx_orders_user;

-- Or create new index then swap
CREATE INDEX CONCURRENTLY idx_orders_user_new ON orders(user_id);
DROP INDEX idx_orders_user;
ALTER INDEX idx_orders_user_new RENAME TO idx_orders_user;
```

**Answer**: Index bloat happens when many updates/deletes leave dead tuples. VACUUM cleans table bloat but not always index bloat efficiently. Monitor index size relative to data size. Use `REINDEX CONCURRENTLY` for zero-downtime rebuild.

---

## Q17. (Advanced) How do you optimize queries that use OR conditions?

```sql
-- BAD: OR often prevents index use
SELECT * FROM orders WHERE user_id = 42 OR status = 'urgent';
-- May result in Seq Scan even with separate indexes on each column

-- GOOD: Use UNION (each branch uses its own index)
SELECT * FROM orders WHERE user_id = 42
UNION
SELECT * FROM orders WHERE status = 'urgent';

-- Or create a composite index if the pattern is common
-- For PostgreSQL, bitmap scan can combine two indexes:
-- Bitmap Index Scan on idx_user → Bitmap Index Scan on idx_status → Bitmap Heap Scan
-- PostgreSQL may do this automatically
```

---

## Q18. (Advanced) How do you handle database query performance in ORMs (Prisma/TypeORM)?

```js
// Prisma: watch for unoptimized queries
const prisma = new PrismaClient({
  log: [
    { level: 'query', emit: 'event' }, // log all queries
  ],
});

prisma.$on('query', (e) => {
  if (e.duration > 100) {
    console.warn(`Slow Prisma query (${e.duration}ms): ${e.query}`);
  }
});

// Common Prisma performance pitfalls:
// 1. include with deep nesting (generates JOINs or multiple queries)
const order = await prisma.order.findFirst({
  include: {
    user: true,
    items: { include: { product: { include: { category: true } } } },
  },
}); // May generate 4+ queries!

// 2. Using findMany without pagination
const allOrders = await prisma.order.findMany(); // loads everything!

// Fix: use raw SQL for complex queries
const result = await prisma.$queryRaw`
  SELECT o.*, json_agg(i.*) as items
  FROM orders o JOIN items i ON i.order_id = o.id
  WHERE o.user_id = ${userId}
  GROUP BY o.id LIMIT 20
`;
```

---

## Q19. (Advanced) How does indexing work differently in MongoDB vs PostgreSQL?

**Answer**:

| Aspect | **PostgreSQL** | **MongoDB** |
|--------|---------------|-------------|
| Default index | B-tree | B-tree |
| Composite index | Leftmost prefix rule | Same leftmost prefix |
| Full-text | `tsvector` + GIN | Built-in text index |
| JSON/BSON | JSONB + GIN/expression index | Native (fields are documents) |
| Partial index | `WHERE condition` | `partialFilterExpression` |
| Unique | `UNIQUE` constraint | `{ unique: true }` |
| Geospatial | PostGIS + GiST | `2dsphere` native |
| Query plan | `EXPLAIN ANALYZE` | `explain()` |

```js
// MongoDB index creation
db.collection('orders').createIndex(
  { userId: 1, createdAt: -1 },  // compound index
  { partialFilterExpression: { status: 'active' } } // partial
);
```

**Key difference**: MongoDB indexes individual **fields within documents** (including nested). PostgreSQL indexes **columns** (JSONB field indexing requires GIN or expression indexes).

---

## Q20. (Advanced) Senior red flags in database query and indexing code reviews.

**Answer**:

1. **No index on foreign key columns** — JOINs become table scans
2. **`SELECT *` in production queries** — fetches unnecessary columns, breaks covering index potential
3. **OFFSET-based pagination on large tables** — O(offset) performance
4. **Missing `EXPLAIN ANALYZE` for new queries** — deploying without knowing the query plan
5. **ORM-generated N+1 queries** — `findMany` with nested `include` without batching
6. **No query timeout** — single runaway query can exhaust connections
7. **Indexing every column** — write performance degrades, maintenance cost
8. **No monitoring of `pg_stat_statements`** — unaware of slow queries
9. **Composite index with wrong column order** — doesn't serve the query pattern
10. **No partitioning on large time-series tables** — queries scan entire history

**Senior interview answer**: "I analyze every new query with EXPLAIN ANALYZE, design indexes based on actual query patterns, use cursor pagination for large datasets, partition time-series tables, and monitor pg_stat_statements for slow query regression."
