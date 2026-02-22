# 21. Database Design & Data Modeling

## Topic Introduction

Database design is the foundation of every backend. A poorly designed schema leads to slow queries, data integrity issues, and painful migrations. A senior engineer designs schemas that are **normalized enough** for consistency, **denormalized enough** for performance, and **flexible enough** for future requirements.

```
Requirements → Entities → Relationships → Schema → Indexes → Queries → Optimization
```

**SQL vs NoSQL decision**:
- **SQL (PostgreSQL/MySQL)**: Strong consistency, complex joins, ACID transactions, mature tooling
- **NoSQL (MongoDB)**: Flexible schema, horizontal scaling, embedded documents, eventual consistency
- **Rule of thumb**: If you need transactions and joins → SQL. If you need flexible schema and horizontal scale → NoSQL.

**Go/Java tradeoff**: Java uses Hibernate/JPA (heavy ORM with entity mapping). Go uses `sqlx` or `pgx` (lightweight, write SQL directly). Node.js uses Knex (query builder), Prisma (type-safe ORM), or Sequelize. Prisma is the best modern choice for Node.js — type-safe with excellent migrations.

---

## Q1. (Beginner) What is database normalization? Explain 1NF, 2NF, 3NF.

**Answer**:

```
Unnormalized:
┌─────────────────────────────────────────────────────┐
│ order_id │ customer │ email        │ items           │
│ 1        │ John     │ j@test.com   │ "Laptop, Mouse" │  ← repeating group
└─────────────────────────────────────────────────────┘

1NF: Eliminate repeating groups (atomic values)
┌─────────────────────────────────────────────┐
│ order_id │ customer │ email       │ item    │
│ 1        │ John     │ j@test.com  │ Laptop  │
│ 1        │ John     │ j@test.com  │ Mouse   │ ← data duplication
└─────────────────────────────────────────────┘

2NF: Remove partial dependencies (every non-key depends on FULL primary key)
Orders:                    Order_Items:
│ order_id │ customer_id │  │ order_id │ item_id │ qty │
│ 1        │ 42          │  │ 1        │ 101     │ 1   │
                             │ 1        │ 102     │ 2   │

3NF: Remove transitive dependencies (non-key depends on another non-key)
Customers:                    Orders:
│ id │ name │ email       │   │ id │ customer_id │ total │
│ 42 │ John │ j@test.com  │   │ 1  │ 42          │ 150   │
```

```sql
-- 3NF schema
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id),
  status VARCHAR(50) DEFAULT 'pending',
  total DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id),
  quantity INT NOT NULL CHECK (quantity > 0),
  price DECIMAL(10,2) NOT NULL
);
```

---

## Q2. (Beginner) When should you denormalize? What are the tradeoffs?

**Answer**:

| | **Normalized** | **Denormalized** |
|---|---|---|
| Data integrity | High (single source of truth) | Risk of inconsistency |
| Write speed | Fast (update one place) | Slower (update multiple places) |
| Read speed | Slow (many joins) | Fast (data pre-joined) |
| Storage | Efficient | Redundant data |
| Use case | OLTP (transactions) | OLAP (analytics), read-heavy |

```sql
-- Normalized: need 3 JOINs to get order details
SELECT o.id, c.name, p.name as product, oi.quantity
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON oi.order_id = o.id
JOIN products p ON oi.product_id = p.id
WHERE o.id = $1;

-- Denormalized: all data in one table (for read-heavy dashboard)
CREATE TABLE order_summary (
  order_id UUID,
  customer_name VARCHAR(255),
  customer_email VARCHAR(255),
  product_name VARCHAR(255),
  quantity INT,
  price DECIMAL(10,2),
  order_date TIMESTAMP
);
-- Single query, no joins, fast for analytics
SELECT * FROM order_summary WHERE order_date > NOW() - INTERVAL '30 days';
```

**Recommendation**: Start normalized (3NF). Denormalize selectively when you have proven performance bottlenecks. Use materialized views for denormalization that stays consistent.

---

## Q3. (Beginner) What are the different types of database relationships?

```sql
-- One-to-One: user has one profile
CREATE TABLE users (id UUID PRIMARY KEY, email VARCHAR UNIQUE NOT NULL);
CREATE TABLE profiles (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE NOT NULL REFERENCES users(id),  -- UNIQUE = one-to-one
  bio TEXT,
  avatar_url VARCHAR
);

-- One-to-Many: user has many orders
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),  -- no UNIQUE = one-to-many
  total DECIMAL(10,2)
);

-- Many-to-Many: products have many tags, tags have many products
CREATE TABLE products (id UUID PRIMARY KEY, name VARCHAR NOT NULL);
CREATE TABLE tags (id UUID PRIMARY KEY, name VARCHAR UNIQUE NOT NULL);
CREATE TABLE product_tags (
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (product_id, tag_id)  -- junction table
);
```

```js
// Prisma schema for the same relationships
// schema.prisma
model User {
  id      String   @id @default(uuid())
  email   String   @unique
  profile Profile?
  orders  Order[]
}

model Profile {
  id     String @id @default(uuid())
  userId String @unique
  user   User   @relation(fields: [userId], references: [id])
  bio    String?
}

model Order {
  id     String @id @default(uuid())
  userId String
  user   User   @relation(fields: [userId], references: [id])
  total  Decimal
}
```

---

## Q4. (Beginner) How do you choose between UUID and auto-increment IDs?

**Answer**:

| | **Auto-increment (SERIAL/BIGSERIAL)** | **UUID** |
|---|---|---|
| Size | 4-8 bytes | 16 bytes |
| Readability | Easy to read (1, 2, 3) | Hard to read |
| Security | Exposes count, guessable | Not guessable |
| Distributed | Needs coordination | No coordination needed |
| Index performance | Sequential (great for B-tree) | Random (index fragmentation) |
| Best for | Single-DB, internal IDs | Distributed systems, public IDs |

```sql
-- Best of both: SERIAL for internal, UUID for public
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,           -- internal, fast joins
  public_id UUID UNIQUE DEFAULT gen_random_uuid(),  -- API exposure
  email VARCHAR(255) UNIQUE NOT NULL
);

-- Alternative: UUIDv7 (time-sorted, solves index fragmentation)
-- Available in PostgreSQL 17+ or via extension
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- use UUIDv7 when available
  -- UUIDv7 is time-ordered, so B-tree index stays efficient
);
```

---

## Q5. (Beginner) What are database constraints and why are they important?

```sql
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,                          -- NOT NULL constraint
  sku VARCHAR(50) UNIQUE NOT NULL,                     -- UNIQUE constraint
  price DECIMAL(10,2) NOT NULL CHECK (price >= 0),     -- CHECK constraint
  category_id UUID REFERENCES categories(id),          -- FOREIGN KEY constraint
  status VARCHAR(20) DEFAULT 'active'                  -- DEFAULT constraint
    CHECK (status IN ('active', 'inactive', 'discontinued')),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  -- Composite unique constraint
  UNIQUE (name, category_id)
);

-- Partial unique index (unique email per active users only)
CREATE UNIQUE INDEX idx_users_email_active
  ON users (email) WHERE deleted_at IS NULL;
```

**Answer**: Constraints enforce data integrity at the database level — regardless of which application writes to it. They are your last line of defense against bad data. Never rely solely on application validation.

---

## Q6. (Intermediate) How do you design a schema for soft deletes?

**Scenario**: Users want to "delete" records but you need to keep them for audit/legal compliance.

```sql
-- Soft delete column
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

-- Only show active users by default
CREATE VIEW active_users AS
  SELECT * FROM users WHERE deleted_at IS NULL;

-- Unique constraint that works with soft deletes
-- (allow same email if previous user was deleted)
CREATE UNIQUE INDEX idx_users_email_active
  ON users (email) WHERE deleted_at IS NULL;

-- Soft delete operation
UPDATE users SET deleted_at = NOW() WHERE id = $1;

-- Restore
UPDATE users SET deleted_at = NULL WHERE id = $1;
```

```js
// Prisma middleware for automatic soft delete filtering
const prisma = new PrismaClient();

prisma.$use(async (params, next) => {
  // Automatically filter deleted records on findMany
  if (params.action === 'findMany' || params.action === 'findFirst') {
    if (!params.args) params.args = {};
    if (!params.args.where) params.args.where = {};
    if (params.args.where.deletedAt === undefined) {
      params.args.where.deletedAt = null; // only non-deleted
    }
  }

  // Convert delete to soft delete
  if (params.action === 'delete') {
    params.action = 'update';
    params.args.data = { deletedAt: new Date() };
  }

  return next(params);
});
```

**Tradeoff**: Soft deletes add complexity (every query needs `WHERE deleted_at IS NULL`), grow table size, and complicate unique constraints. Consider: archive deleted records to a separate table, or use event sourcing where "delete" is just another event.

---

## Q7. (Intermediate) How do you design a multi-tenant database?

**Scenario**: Your SaaS app serves 100 companies. Each should only see their own data.

```sql
-- Strategy 1: Shared tables with tenant_id (most common)
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  customer_id UUID NOT NULL,
  total DECIMAL(10,2),
  -- Index for tenant isolation
  CONSTRAINT idx_orders_tenant UNIQUE (tenant_id, id)
);
-- EVERY query must include tenant_id!
CREATE INDEX idx_orders_tenant ON orders(tenant_id);

-- Strategy 2: Schema per tenant (PostgreSQL)
CREATE SCHEMA tenant_acme;
CREATE TABLE tenant_acme.orders (id UUID PRIMARY KEY, ...);
-- Switch schema per request: SET search_path TO tenant_acme;

-- Strategy 3: Database per tenant (maximum isolation)
-- Separate PostgreSQL database per tenant (expensive, hardest to manage)
```

```js
// Row-level security with Prisma + middleware
prisma.$use(async (params, next) => {
  // Inject tenant_id into every write
  if (['create', 'createMany'].includes(params.action)) {
    if (params.args.data) {
      params.args.data.tenantId = getCurrentTenantId();
    }
  }

  // Filter by tenant on every read
  if (['findMany', 'findFirst', 'findUnique', 'count'].includes(params.action)) {
    if (!params.args.where) params.args.where = {};
    params.args.where.tenantId = getCurrentTenantId();
  }

  return next(params);
});

// PostgreSQL Row-Level Security (RLS) — database-enforced
// ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
// CREATE POLICY tenant_isolation ON orders
//   USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

| Strategy | Isolation | Complexity | Cost | Best for |
|---|---|---|---|---|
| Shared tables + tenant_id | Low | Low | Low | Startups, simple apps |
| Schema per tenant | Medium | Medium | Medium | Mid-size SaaS |
| Database per tenant | High | High | High | Enterprise, compliance |

---

## Q8. (Intermediate) How do you design audit trails / event sourcing?

```sql
-- Audit trail: log every change
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name VARCHAR(100) NOT NULL,
  record_id UUID NOT NULL,
  action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  old_data JSONB,
  new_data JSONB,
  changed_by UUID REFERENCES users(id),
  changed_at TIMESTAMP DEFAULT NOW(),
  ip_address INET,
  user_agent TEXT
);

-- Trigger to automatically log changes
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by)
  VALUES (
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    TG_OP,
    CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD)::jsonb END,
    CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW)::jsonb END,
    current_setting('app.user_id', true)::uuid
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_audit AFTER INSERT OR UPDATE OR DELETE ON users
  FOR EACH ROW EXECUTE FUNCTION audit_trigger();
```

```js
// Event sourcing: store events instead of state
// Instead of updating a row, append events
const events = [
  { type: 'ORDER_CREATED', data: { id: 'o1', items: [...], total: 100 }, timestamp: '2024-01-01T00:00:00Z' },
  { type: 'ITEM_ADDED', data: { orderId: 'o1', item: { id: 'p2', qty: 1 } }, timestamp: '2024-01-01T00:01:00Z' },
  { type: 'DISCOUNT_APPLIED', data: { orderId: 'o1', discount: 10 }, timestamp: '2024-01-01T00:02:00Z' },
  { type: 'ORDER_CONFIRMED', data: { orderId: 'o1' }, timestamp: '2024-01-01T00:03:00Z' },
];

// Rebuild current state by replaying events
function buildOrderState(events) {
  return events.reduce((state, event) => {
    switch (event.type) {
      case 'ORDER_CREATED': return { ...event.data, status: 'draft' };
      case 'ITEM_ADDED': return { ...state, items: [...state.items, event.data.item] };
      case 'DISCOUNT_APPLIED': return { ...state, discount: event.data.discount };
      case 'ORDER_CONFIRMED': return { ...state, status: 'confirmed' };
      default: return state;
    }
  }, {});
}
```

---

## Q9. (Intermediate) How do you design polymorphic associations?

**Scenario**: Both Users and Teams can have Comments. How do you model this?

```sql
-- Option 1: Separate foreign keys (simplest, most DB-safe)
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  body TEXT NOT NULL,
  user_id UUID REFERENCES users(id),     -- comments ON users
  team_id UUID REFERENCES teams(id),     -- comments ON teams
  post_id UUID REFERENCES posts(id),     -- comments ON posts
  created_at TIMESTAMP DEFAULT NOW(),
  CHECK (
    (user_id IS NOT NULL)::int +
    (team_id IS NOT NULL)::int +
    (post_id IS NOT NULL)::int = 1  -- exactly one must be set
  )
);

-- Option 2: Polymorphic (commentable_type + commentable_id)
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  body TEXT NOT NULL,
  commentable_type VARCHAR(50) NOT NULL,  -- 'User', 'Team', 'Post'
  commentable_id UUID NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_comments_poly ON comments(commentable_type, commentable_id);
-- NO foreign key possible (can't reference multiple tables)

-- Option 3: Shared base table (most normalized)
CREATE TABLE commentables (id UUID PRIMARY KEY, type VARCHAR(50) NOT NULL);
CREATE TABLE users (id UUID PRIMARY KEY REFERENCES commentables(id), ...);
CREATE TABLE teams (id UUID PRIMARY KEY REFERENCES commentables(id), ...);
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  commentable_id UUID NOT NULL REFERENCES commentables(id),
  body TEXT NOT NULL
);
```

**Answer**: Option 1 is safest (real FK constraints) but doesn't scale to many types. Option 2 is flexible (used by Rails) but loses FK integrity. Option 3 is most normalized but adds complexity. For Node.js apps, Option 2 with application-level validation is pragmatic.

---

## Q10. (Intermediate) How do you model hierarchical data (categories, org charts, file systems)?

```sql
-- Option 1: Adjacency List (simplest)
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  parent_id UUID REFERENCES categories(id)
);
-- Problem: getting full tree requires recursive queries

-- Recursive CTE to get full tree
WITH RECURSIVE category_tree AS (
  SELECT id, name, parent_id, 0 AS depth
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, ct.depth + 1
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY depth;

-- Option 2: Materialized Path (fast reads)
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  path TEXT NOT NULL  -- '/electronics/computers/laptops'
);
-- Find all children of 'electronics':
SELECT * FROM categories WHERE path LIKE '/electronics/%';
-- Find ancestors: parse the path string

-- Option 3: ltree extension (PostgreSQL — best of both worlds)
CREATE EXTENSION ltree;
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  path ltree NOT NULL
);
CREATE INDEX idx_path_gist ON categories USING gist(path);

-- Query descendants
SELECT * FROM categories WHERE path <@ 'electronics.computers';
-- Query ancestors
SELECT * FROM categories WHERE path @> 'electronics.computers.laptops';
```

| Strategy | Read speed | Write speed | Move subtree | Best for |
|---|---|---|---|---|
| Adjacency list | Slow (recursive) | Fast | Easy | Small trees, frequent writes |
| Materialized path | Fast | Slow (update children) | Hard | Read-heavy, moderate depth |
| ltree (PostgreSQL) | Fast | Moderate | Moderate | PostgreSQL projects |
| Nested sets | Fast | Very slow | Very hard | Static trees |

---

## Q11. (Intermediate) How do you design a schema for a tagging system with search?

```sql
-- Tags table
CREATE TABLE tags (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL  -- url-friendly
);

-- Junction table
CREATE TABLE article_tags (
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (article_id, tag_id)
);

-- Find articles with ALL specified tags (AND)
SELECT a.*
FROM articles a
JOIN article_tags at ON a.id = at.article_id
WHERE at.tag_id IN (SELECT id FROM tags WHERE slug IN ('javascript', 'nodejs'))
GROUP BY a.id
HAVING COUNT(DISTINCT at.tag_id) = 2;  -- must match ALL tags

-- Find articles with ANY specified tags (OR)
SELECT DISTINCT a.*
FROM articles a
JOIN article_tags at ON a.id = at.article_id
WHERE at.tag_id IN (SELECT id FROM tags WHERE slug IN ('javascript', 'nodejs'));

-- Get tag cloud with counts
SELECT t.name, t.slug, COUNT(at.article_id) as article_count
FROM tags t
LEFT JOIN article_tags at ON t.id = at.tag_id
GROUP BY t.id
ORDER BY article_count DESC
LIMIT 50;
```

```js
// Node.js implementation
async function getArticlesByTags(tagSlugs, matchAll = false) {
  const query = db('articles as a')
    .join('article_tags as at', 'a.id', 'at.article_id')
    .join('tags as t', 'at.tag_id', 't.id')
    .whereIn('t.slug', tagSlugs)
    .select('a.*');

  if (matchAll) {
    query.groupBy('a.id').havingRaw('COUNT(DISTINCT t.id) = ?', [tagSlugs.length]);
  } else {
    query.distinct();
  }

  return query;
}
```

---

## Q12. (Intermediate) How do you design for temporal data (price history, status changes)?

```sql
-- Track price history
CREATE TABLE product_prices (
  id BIGSERIAL PRIMARY KEY,
  product_id UUID NOT NULL REFERENCES products(id),
  price DECIMAL(10,2) NOT NULL,
  effective_from TIMESTAMP NOT NULL DEFAULT NOW(),
  effective_until TIMESTAMP,  -- NULL = current price
  changed_by UUID REFERENCES users(id),

  -- Ensure no overlapping periods
  EXCLUDE USING gist (
    product_id WITH =,
    tsrange(effective_from, effective_until, '[)') WITH &&
  )
);

-- Get current price
SELECT price FROM product_prices
WHERE product_id = $1 AND effective_until IS NULL;

-- Get price at a specific point in time
SELECT price FROM product_prices
WHERE product_id = $1
  AND effective_from <= $2
  AND (effective_until IS NULL OR effective_until > $2);

-- Order status history
CREATE TABLE order_status_history (
  id BIGSERIAL PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id),
  status VARCHAR(50) NOT NULL,
  changed_at TIMESTAMP DEFAULT NOW(),
  changed_by UUID,
  notes TEXT
);
-- Latest status: SELECT * FROM order_status_history WHERE order_id = $1 ORDER BY changed_at DESC LIMIT 1;
```

---

## Q13. (Advanced) How do you design a schema for a social media feed (Twitter-like)?

```sql
-- Core tables
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  display_name VARCHAR(255) NOT NULL
);

CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id UUID NOT NULL REFERENCES users(id),
  content TEXT NOT NULL CHECK (char_length(content) <= 280),
  reply_to_id UUID REFERENCES posts(id),  -- for threading
  repost_of_id UUID REFERENCES posts(id), -- retweet
  created_at TIMESTAMP DEFAULT NOW(),
  like_count INT DEFAULT 0,
  reply_count INT DEFAULT 0,
  repost_count INT DEFAULT 0
);

CREATE TABLE follows (
  follower_id UUID REFERENCES users(id),
  following_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (follower_id, following_id)
);

CREATE TABLE likes (
  user_id UUID REFERENCES users(id),
  post_id UUID REFERENCES posts(id),
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, post_id)
);

-- Fan-out on write: pre-compute timelines
CREATE TABLE timelines (
  user_id UUID NOT NULL,
  post_id UUID NOT NULL REFERENCES posts(id),
  score DOUBLE PRECISION NOT NULL,  -- for ranking
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, post_id)
);

-- When user A creates a post, insert into all followers' timelines
CREATE INDEX idx_timelines_user_score ON timelines(user_id, score DESC);
```

```js
// Fan-out on write — when a post is created
async function createPost(authorId, content) {
  const post = await db('posts').insert({ author_id: authorId, content }).returning('*');

  // Get all followers
  const followers = await db('follows').where({ following_id: authorId }).select('follower_id');

  // Insert into each follower's timeline (batch for performance)
  if (followers.length > 0) {
    const timelineEntries = followers.map(f => ({
      user_id: f.follower_id,
      post_id: post[0].id,
      score: Date.now(),
    }));
    await db('timelines').insert(timelineEntries);
  }

  return post[0];
}

// Read timeline (fast — pre-computed)
async function getTimeline(userId, cursor, limit = 20) {
  return db('timelines as t')
    .join('posts as p', 't.post_id', 'p.id')
    .join('users as u', 'p.author_id', 'u.id')
    .where('t.user_id', userId)
    .where('t.score', '<', cursor || Infinity)
    .orderBy('t.score', 'desc')
    .limit(limit)
    .select('p.*', 'u.username', 'u.display_name');
}
```

**Answer**: Two approaches: (1) Fan-out on write (pre-compute timelines) — fast reads, slow writes for popular users. (2) Fan-out on read (query at read time) — slow reads, fast writes. Twitter uses fan-out on write for most users, fan-out on read for celebrities (millions of followers).

---

## Q14. (Advanced) How do you handle schema evolution with backward compatibility?

```sql
-- SAFE changes (backward compatible):
-- 1. Add nullable column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 2. Add column with default value
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- 3. Add new table
CREATE TABLE user_preferences (...);

-- 4. Add index (concurrent to avoid locking)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- UNSAFE changes (breaking):
-- 1. Drop column — old code might reference it
-- 2. Rename column — old code breaks
-- 3. Change column type — data conversion needed
-- 4. Add NOT NULL without default — existing rows fail
```

```js
// Safe column rename strategy (3-phase)
// Phase 1: Add new column, write to both
async function updateUser(id, data) {
  await db('users').where({ id }).update({
    display_name: data.name,
    name: data.name, // write to old column too
  });
}

// Phase 2: Migrate data, read from new column
await db.raw('UPDATE users SET display_name = name WHERE display_name IS NULL');

// Phase 3: Remove old column (after all code uses new column)
await db.raw('ALTER TABLE users DROP COLUMN name');
```

**Answer**: The expand-contract pattern: expand the schema (add new columns), migrate data, update code, then contract (remove old columns). Never make breaking changes in a single step.

---

## Q15. (Advanced) How do you design for sharding / horizontal partitioning?

**Scenario**: Your users table has 500M rows. Single PostgreSQL is struggling.

```sql
-- PostgreSQL native partitioning (horizontal)
CREATE TABLE orders (
  id UUID NOT NULL,
  user_id UUID NOT NULL,
  created_at TIMESTAMP NOT NULL,
  total DECIMAL(10,2)
) PARTITION BY RANGE (created_at);

-- Create partitions by month
CREATE TABLE orders_2024_01 PARTITION OF orders
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE orders_2024_02 PARTITION OF orders
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Queries automatically route to correct partition
SELECT * FROM orders WHERE created_at BETWEEN '2024-01-15' AND '2024-01-20';
-- Only scans orders_2024_01!

-- Hash partitioning for even distribution
CREATE TABLE user_data (
  user_id UUID NOT NULL,
  data JSONB
) PARTITION BY HASH (user_id);

CREATE TABLE user_data_0 PARTITION OF user_data FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE user_data_1 PARTITION OF user_data FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE user_data_2 PARTITION OF user_data FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE user_data_3 PARTITION OF user_data FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

```js
// Application-level sharding (when DB partitioning isn't enough)
class ShardRouter {
  constructor(shards) {
    this.shards = shards; // array of database connections
  }

  getShardForUser(userId) {
    const hash = crypto.createHash('md5').update(userId).digest('hex');
    const shardIndex = parseInt(hash.substring(0, 8), 16) % this.shards.length;
    return this.shards[shardIndex];
  }

  async queryUser(userId, queryFn) {
    const shard = this.getShardForUser(userId);
    return queryFn(shard);
  }

  async queryAll(queryFn) {
    // Fan-out query to all shards, merge results
    const results = await Promise.all(this.shards.map(queryFn));
    return results.flat();
  }
}
```

---

## Q16. (Advanced) How do you design for full-text search?

```sql
-- PostgreSQL built-in full-text search
ALTER TABLE articles ADD COLUMN search_vector tsvector;

-- Generate search vector from title and body
UPDATE articles SET search_vector =
  setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(body, '')), 'B');

-- GIN index for fast search
CREATE INDEX idx_articles_search ON articles USING gin(search_vector);

-- Trigger to auto-update on insert/update
CREATE TRIGGER articles_search_update
  BEFORE INSERT OR UPDATE ON articles
  FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(search_vector, 'pg_catalog.english', title, body);

-- Search query with ranking
SELECT id, title,
  ts_rank(search_vector, plainto_tsquery('english', 'nodejs performance')) AS rank
FROM articles
WHERE search_vector @@ plainto_tsquery('english', 'nodejs performance')
ORDER BY rank DESC
LIMIT 20;
```

```js
// Elasticsearch for advanced search (when PostgreSQL FTS isn't enough)
const { Client } = require('@elastic/elasticsearch');
const elastic = new Client({ node: 'http://elasticsearch:9200' });

// Index a document
await elastic.index({
  index: 'articles',
  id: article.id,
  body: {
    title: article.title,
    body: article.body,
    tags: article.tags,
    author: article.authorName,
    createdAt: article.createdAt,
  },
});

// Search with fuzzy matching, highlighting, and facets
const results = await elastic.search({
  index: 'articles',
  body: {
    query: {
      bool: {
        must: [
          { multi_match: { query: 'nodejs performance', fields: ['title^3', 'body'], fuzziness: 'AUTO' } },
        ],
        filter: [
          { terms: { tags: ['backend', 'nodejs'] } },
          { range: { createdAt: { gte: '2024-01-01' } } },
        ],
      },
    },
    highlight: { fields: { title: {}, body: { fragment_size: 150 } } },
    aggs: { tags: { terms: { field: 'tags.keyword', size: 20 } } },
  },
});
```

**Answer**: Use PostgreSQL FTS for simple search (same DB, no extra infrastructure). Use Elasticsearch for complex search (fuzzy matching, facets, highlighting, autocomplete). Sync data from PostgreSQL to Elasticsearch via events or CDC (Debezium).

---

## Q17. (Advanced) How do you model a permission system (RBAC vs ABAC)?

```sql
-- RBAC: Role-Based Access Control
CREATE TABLE roles (id SERIAL PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL);
CREATE TABLE permissions (id SERIAL PRIMARY KEY, name VARCHAR(100) UNIQUE NOT NULL);
CREATE TABLE role_permissions (
  role_id INT REFERENCES roles(id),
  permission_id INT REFERENCES permissions(id),
  PRIMARY KEY (role_id, permission_id)
);
CREATE TABLE user_roles (
  user_id UUID REFERENCES users(id),
  role_id INT REFERENCES roles(id),
  PRIMARY KEY (user_id, role_id)
);

-- Check permission
SELECT EXISTS (
  SELECT 1 FROM user_roles ur
  JOIN role_permissions rp ON ur.role_id = rp.role_id
  JOIN permissions p ON rp.permission_id = p.id
  WHERE ur.user_id = $1 AND p.name = $2
) AS has_permission;
```

```js
// Node.js permission check middleware
async function hasPermission(userId, permission) {
  const result = await db.raw(`
    SELECT EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN role_permissions rp ON ur.role_id = rp.role_id
      JOIN permissions p ON rp.permission_id = p.id
      WHERE ur.user_id = ? AND p.name = ?
    ) AS has_perm
  `, [userId, permission]);
  return result.rows[0].has_perm;
}

function requirePermission(permission) {
  return async (req, res, next) => {
    if (await hasPermission(req.user.id, permission)) return next();
    res.status(403).json({ error: 'Insufficient permissions' });
  };
}

app.delete('/api/users/:id', requirePermission('users:delete'), deleteUser);
app.put('/api/settings', requirePermission('settings:update'), updateSettings);
```

**ABAC (Attribute-Based)**: Decisions based on attributes (user role + resource owner + time + location). More flexible than RBAC but more complex. Used by AWS IAM, Google Zanzibar.

---

## Q18. (Advanced) How do you design a notification system database schema?

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  type VARCHAR(50) NOT NULL,  -- 'order_shipped', 'message_received', 'payment_failed'
  title VARCHAR(255) NOT NULL,
  body TEXT,
  data JSONB,  -- type-specific payload
  read_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP  -- auto-cleanup
);

CREATE INDEX idx_notifications_user_unread
  ON notifications(user_id, created_at DESC) WHERE read_at IS NULL;

CREATE TABLE notification_preferences (
  user_id UUID REFERENCES users(id),
  channel VARCHAR(20) NOT NULL,  -- 'email', 'push', 'in_app', 'sms'
  type VARCHAR(50) NOT NULL,     -- notification type
  enabled BOOLEAN DEFAULT true,
  PRIMARY KEY (user_id, channel, type)
);
```

```js
// Notification service
class NotificationService {
  async send(userId, notification) {
    // 1. Check user preferences
    const preferences = await db('notification_preferences')
      .where({ user_id: userId, type: notification.type, enabled: true });

    const channels = preferences.map(p => p.channel);

    // 2. Store in-app notification
    if (channels.includes('in_app')) {
      await db('notifications').insert({
        user_id: userId,
        type: notification.type,
        title: notification.title,
        body: notification.body,
        data: notification.data,
      });
    }

    // 3. Send via other channels
    if (channels.includes('email')) await emailService.send(userId, notification);
    if (channels.includes('push')) await pushService.send(userId, notification);
    if (channels.includes('sms')) await smsService.send(userId, notification);
  }

  async getUnread(userId, limit = 20) {
    return db('notifications')
      .where({ user_id: userId, read_at: null })
      .orderBy('created_at', 'desc')
      .limit(limit);
  }

  async markRead(userId, notificationIds) {
    return db('notifications')
      .whereIn('id', notificationIds)
      .where({ user_id: userId })
      .update({ read_at: new Date() });
  }
}
```

---

## Q19. (Advanced) How does MongoDB data modeling differ from relational modeling?

```js
// MongoDB: embed vs reference

// EMBED when: data is read together, one-to-few relationship, data doesn't change often
const orderDocument = {
  _id: ObjectId('...'),
  userId: ObjectId('...'),
  status: 'confirmed',
  items: [
    // Embedded — no join needed!
    { productId: ObjectId('...'), name: 'Laptop', price: 999, qty: 1 },
    { productId: ObjectId('...'), name: 'Mouse', price: 29, qty: 2 },
  ],
  shippingAddress: {
    // Embedded — belongs to this order
    street: '123 Main St',
    city: 'San Francisco',
    state: 'CA',
    zip: '94102',
  },
  total: 1057,
  createdAt: new Date(),
};

// REFERENCE when: data is shared, one-to-many, data changes independently
const userDocument = {
  _id: ObjectId('...'),
  name: 'John',
  email: 'john@example.com',
  // DON'T embed all orders — could grow to thousands
  // Use reference: query orders collection with userId
};

// Mongoose schema
const orderSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, index: true },
  status: { type: String, enum: ['pending', 'confirmed', 'shipped', 'delivered'], default: 'pending' },
  items: [{
    productId: { type: mongoose.Schema.Types.ObjectId, ref: 'Product' },
    name: String,     // denormalized for read performance
    price: Number,    // snapshot at time of order
    qty: { type: Number, min: 1 },
  }],
  total: { type: Number, required: true },
}, { timestamps: true });
```

| Pattern | SQL | MongoDB |
|---|---|---|
| One-to-one | Foreign key + JOIN | Embed subdocument |
| One-to-few | Foreign key + JOIN | Embed array |
| One-to-many | Foreign key + JOIN | Reference (separate collection) |
| Many-to-many | Junction table | Array of references on both sides |

---

## Q20. (Advanced) Senior red flags in database design.

**Answer**:

1. **No indexes on foreign keys** — JOIN performance tanks with large tables
2. **No constraints** — relying solely on application code for data integrity
3. **Storing money as FLOAT** — floating point errors. Always use `DECIMAL(10,2)` or store cents as integers.
4. **No soft delete strategy** — hard deletes lose audit trail and break foreign keys
5. **SELECT * everywhere** — fetches columns you don't need, wastes bandwidth and memory
6. **No database migrations** — manual SQL changes that can't be reproduced
7. **Storing large files in the database** — use object storage (S3), store URLs in DB
8. **No pagination** — `SELECT * FROM orders` returns 1M rows
9. **N+1 queries** — fetching related data in a loop instead of a JOIN or batch query
10. **God table** — one table with 100 columns for everything

```sql
-- RED FLAG: money as float
CREATE TABLE orders (total FLOAT); -- 0.1 + 0.2 = 0.30000000000000004 !!!

-- FIX: money as DECIMAL
CREATE TABLE orders (total DECIMAL(10,2)); -- 0.10 + 0.20 = 0.30 ✓

-- RED FLAG: no index on foreign key
CREATE TABLE orders (user_id UUID REFERENCES users(id));
-- JOIN is O(n) full table scan!

-- FIX: index on foreign key
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

**Senior interview answer**: "I design schemas normalized to 3NF, then selectively denormalize for read-heavy patterns. I use proper constraints (NOT NULL, CHECK, FK), DECIMAL for money, UUIDs for distributed systems, and always index foreign keys. For evolving schemas, I use the expand-contract pattern with backward-compatible migrations. I choose embedding vs referencing in MongoDB based on read patterns and data growth. For search, I use PostgreSQL FTS for simple needs and Elasticsearch for complex requirements."
