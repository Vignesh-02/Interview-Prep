# 29. Database Migrations & Schema Evolution

## Topic Introduction

Database migrations are **version-controlled changes to your database schema**. Just like Git tracks code changes, migrations track schema changes — so every environment (dev, staging, prod) has the same schema, and changes can be rolled back.

```
Migration Timeline:
001_create_users.js → 002_add_email_index.js → 003_add_orders_table.js → ...
(each migration is applied in order, never modified after deployment)
```

**Key principle**: Never modify a deployed migration. Always create a new one. Migrations are immutable history.

**Tools**: Knex.js (most popular), Prisma Migrate, TypeORM migrations, Sequelize CLI, Flyway (Java), golang-migrate (Go).

**Go/Java tradeoff**: Java uses Flyway or Liquibase (XML/SQL-based). Go uses golang-migrate. Node.js uses Knex or Prisma. Flyway is the most mature, but Knex and Prisma are excellent for Node.js projects.

---

## Q1. (Beginner) What are database migrations and why do you need them?

**Answer**:

```
Without migrations:
Developer A: "Just run this SQL in production"
Developer B: "Which SQL? I have a different version"
Staging: different schema than production
Bug: schema mismatch causes crash at 2 AM

With migrations:
Developer A: creates 003_add_status_column.js
Developer B: runs `npx knex migrate:latest` → gets same schema
Staging: `npx knex migrate:latest` → identical to production
Rollback: `npx knex migrate:rollback` → reverts safely
```

```js
// Knex migration file: 001_create_users.js
exports.up = async function(knex) {
  await knex.schema.createTable('users', (table) => {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.string('name', 255).notNullable();
    table.string('email', 255).notNullable().unique();
    table.string('password_hash', 255).notNullable();
    table.timestamps(true, true); // created_at, updated_at
  });
};

exports.down = async function(knex) {
  await knex.schema.dropTableIfExists('users');
};
```

```bash
# Create a new migration
npx knex migrate:make add_orders_table

# Run all pending migrations
npx knex migrate:latest

# Rollback last batch of migrations
npx knex migrate:rollback

# Rollback all migrations
npx knex migrate:rollback --all

# Check migration status
npx knex migrate:status
```

---

## Q2. (Beginner) How do you structure migration files?

```
migrations/
├── 20240101000000_create_users.js
├── 20240101000001_create_products.js
├── 20240102000000_create_orders.js
├── 20240102000001_create_order_items.js
├── 20240115000000_add_status_to_orders.js
├── 20240120000000_add_email_index.js
└── 20240201000000_add_user_roles.js
```

```js
// Good migration: single responsibility, reversible
// 20240115000000_add_status_to_orders.js
exports.up = async function(knex) {
  await knex.schema.alterTable('orders', (table) => {
    table.string('status', 50).defaultTo('pending').notNullable();
    table.index('status');
  });
};

exports.down = async function(knex) {
  await knex.schema.alterTable('orders', (table) => {
    table.dropIndex('status');
    table.dropColumn('status');
  });
};
```

**Naming conventions**: Use timestamps (not sequential numbers) to avoid conflicts when multiple developers create migrations simultaneously.

---

## Q3. (Beginner) How do you add columns, indexes, and constraints in migrations?

```js
// Add a column
exports.up = async function(knex) {
  await knex.schema.alterTable('users', (table) => {
    table.string('phone', 20);              // nullable by default
    table.string('avatar_url', 500);
    table.boolean('is_verified').defaultTo(false);
  });
};

// Add an index
exports.up = async function(knex) {
  await knex.schema.alterTable('orders', (table) => {
    table.index(['user_id', 'created_at'], 'idx_orders_user_date');
    table.unique(['user_id', 'external_id'], 'uq_orders_user_external');
  });
};

// Add a foreign key
exports.up = async function(knex) {
  await knex.schema.alterTable('orders', (table) => {
    table.uuid('assigned_to').references('id').inTable('users').onDelete('SET NULL');
  });
};

// Add a check constraint (raw SQL for Knex)
exports.up = async function(knex) {
  await knex.raw(`
    ALTER TABLE products
    ADD CONSTRAINT chk_price_positive CHECK (price >= 0)
  `);
};

exports.down = async function(knex) {
  await knex.raw('ALTER TABLE products DROP CONSTRAINT chk_price_positive');
};
```

---

## Q4. (Beginner) What is a seed file? How does it differ from a migration?

```js
// Migration: changes SCHEMA (structure)
// Seed: populates DATA (initial/test data)

// seeds/01_roles.js
exports.seed = async function(knex) {
  // Delete existing entries
  await knex('roles').del();

  // Insert default roles
  await knex('roles').insert([
    { id: 1, name: 'admin', description: 'Full access' },
    { id: 2, name: 'editor', description: 'Can edit content' },
    { id: 3, name: 'viewer', description: 'Read-only access' },
  ]);
};

// seeds/02_test_users.js (for development only)
exports.seed = async function(knex) {
  if (process.env.NODE_ENV === 'production') return; // never in production!

  await knex('users').del();
  await knex('users').insert([
    { name: 'Admin User', email: 'admin@test.com', role_id: 1, password_hash: '...' },
    { name: 'Test User', email: 'user@test.com', role_id: 3, password_hash: '...' },
  ]);
};
```

```bash
npx knex seed:run  # run all seed files
```

---

## Q5. (Beginner) How do you use Prisma Migrate?

```prisma
// prisma/schema.prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  name      String
  role      Role     @default(USER)
  orders    Order[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

enum Role {
  USER
  ADMIN
  EDITOR
}

model Order {
  id        String      @id @default(uuid())
  userId    String
  user      User        @relation(fields: [userId], references: [id])
  status    OrderStatus @default(PENDING)
  total     Decimal     @db.Decimal(10, 2)
  createdAt DateTime    @default(now())
}

enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
}
```

```bash
# Generate migration from schema changes
npx prisma migrate dev --name add_order_status

# Apply migrations in production
npx prisma migrate deploy

# Reset database (dev only)
npx prisma migrate reset
```

**Answer**: Prisma is declarative — you describe the desired state, and Prisma generates the SQL migration. Knex is imperative — you write the migration steps manually. Prisma is safer but less flexible; Knex gives full control.

---

## Q6. (Intermediate) How do you handle data migrations (not just schema)?

**Scenario**: You're splitting the `name` column into `first_name` and `last_name`.

```js
// Step 1: Add new columns (non-breaking)
exports.up = async function(knex) {
  await knex.schema.alterTable('users', (table) => {
    table.string('first_name', 127);
    table.string('last_name', 127);
  });
};

// Step 2: Migrate data (separate migration)
exports.up = async function(knex) {
  // Batch update to avoid locking the entire table
  const BATCH_SIZE = 1000;
  let processed = 0;

  while (true) {
    const users = await knex('users')
      .whereNull('first_name')
      .limit(BATCH_SIZE);

    if (users.length === 0) break;

    for (const user of users) {
      const parts = user.name.split(' ');
      const firstName = parts[0];
      const lastName = parts.slice(1).join(' ') || '';

      await knex('users')
        .where({ id: user.id })
        .update({ first_name: firstName, last_name: lastName });
    }

    processed += users.length;
    console.log(`Migrated ${processed} users`);
  }
};

// Step 3: After code is updated to use new columns, drop old column
exports.up = async function(knex) {
  await knex.schema.alterTable('users', (table) => {
    table.string('first_name', 127).notNullable().alter();
    table.string('last_name', 127).notNullable().alter();
    table.dropColumn('name');
  });
};
```

**Answer**: The expand-contract pattern: (1) Add new columns, (2) Migrate data, (3) Update code to use new columns, (4) Remove old column. Never do all steps in one migration — that's a breaking change.

---

## Q7. (Intermediate) How do you run migrations safely in production with zero downtime?

```js
// DANGEROUS: this migration locks the table for minutes on 10M rows
exports.up = async function(knex) {
  await knex.schema.alterTable('users', (table) => {
    table.string('status').notNullable().defaultTo('active'); // locks table!
  });
};

// SAFE: non-blocking migration
exports.up = async function(knex) {
  // Step 1: Add column as nullable (instant, no lock)
  await knex.schema.alterTable('users', (table) => {
    table.string('status');
  });

  // Step 2: Set default for new rows
  await knex.raw("ALTER TABLE users ALTER COLUMN status SET DEFAULT 'active'");

  // Step 3: Backfill existing rows in batches (no lock)
  await knex.raw("UPDATE users SET status = 'active' WHERE status IS NULL");

  // Step 4: Add NOT NULL constraint (after all rows have values)
  await knex.raw('ALTER TABLE users ALTER COLUMN status SET NOT NULL');
};

// SAFE: Create index concurrently (PostgreSQL)
exports.up = async function(knex) {
  // Regular CREATE INDEX locks the table for writes
  // CONCURRENTLY doesn't lock but takes longer
  await knex.raw('CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id)');
};
// Note: CONCURRENTLY can't run inside a transaction
// Knex: set { transaction: false } in knexfile for this migration
```

---

## Q8. (Intermediate) How do you handle migration rollbacks and failures?

```js
// Always write a down() that reverses the up()
exports.up = async function(knex) {
  await knex.schema.createTable('subscriptions', (table) => {
    table.uuid('id').primary();
    table.uuid('user_id').references('users.id').onDelete('CASCADE');
    table.string('plan', 50).notNullable();
    table.timestamp('starts_at').notNullable();
    table.timestamp('ends_at');
    table.timestamps(true, true);
  });
};

exports.down = async function(knex) {
  await knex.schema.dropTableIfExists('subscriptions');
};

// What if up() fails halfway? Knex wraps each migration in a transaction
// If any statement fails, the entire migration is rolled back

// For migrations that CAN'T be in a transaction (e.g., CREATE INDEX CONCURRENTLY):
exports.config = { transaction: false };

exports.up = async function(knex) {
  try {
    await knex.raw('CREATE INDEX CONCURRENTLY idx_big_table ON big_table(column)');
  } catch (err) {
    // If index creation fails, clean up partial index
    await knex.raw('DROP INDEX CONCURRENTLY IF EXISTS idx_big_table');
    throw err;
  }
};
```

---

## Q9. (Intermediate) How do you handle migrations in a CI/CD pipeline?

```yaml
# GitHub Actions: test migrations in CI
name: Database Migrations
on: [push, pull_request]

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env: { POSTGRES_DB: test, POSTGRES_PASSWORD: test }
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci

      # Test: migrate up
      - run: npx knex migrate:latest
        env: { DATABASE_URL: postgres://postgres:test@localhost/test }

      # Test: rollback
      - run: npx knex migrate:rollback --all
        env: { DATABASE_URL: postgres://postgres:test@localhost/test }

      # Test: migrate up again (idempotent)
      - run: npx knex migrate:latest
        env: { DATABASE_URL: postgres://postgres:test@localhost/test }

      # Run integration tests
      - run: npm run test:integration
        env: { DATABASE_URL: postgres://postgres:test@localhost/test }

  deploy:
    needs: test-migrations
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: npx knex migrate:latest
        env: { DATABASE_URL: ${{ secrets.PRODUCTION_DATABASE_URL }} }
```

```js
// Run migrations on application startup (simple approach)
const knex = require('./db');

async function startApp() {
  console.log('Running database migrations...');
  await knex.migrate.latest();
  console.log('Migrations complete. Starting server...');
  app.listen(3000);
}

startApp();

// Better: run migrations in a separate step (init container in K8s)
// Don't mix migration and app startup — if migration fails, app shouldn't start
```

---

## Q10. (Intermediate) How do you manage different schemas for test, staging, and production?

```js
// knexfile.js — environment-specific configuration
module.exports = {
  development: {
    client: 'pg',
    connection: 'postgres://localhost/myapp_dev',
    migrations: { directory: './migrations' },
    seeds: { directory: './seeds/development' },
  },
  test: {
    client: 'pg',
    connection: process.env.TEST_DATABASE_URL || 'postgres://localhost/myapp_test',
    migrations: { directory: './migrations' },
    seeds: { directory: './seeds/test' },
  },
  staging: {
    client: 'pg',
    connection: process.env.DATABASE_URL,
    migrations: { directory: './migrations' },
    pool: { min: 2, max: 10 },
  },
  production: {
    client: 'pg',
    connection: {
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
    },
    migrations: { directory: './migrations' },
    pool: { min: 5, max: 20 },
  },
};
```

**Answer**: All environments use the SAME migration files. The only difference is the connection string and pool settings. Never have environment-specific migrations — that leads to schema drift.

---

## Q11. (Intermediate) How do you handle migration conflicts in a team?

**Scenario**: Two developers both create migration `003_` independently. When they merge, which runs first?

```
Developer A: 20240115_add_user_phone.js
Developer B: 20240115_add_order_notes.js

Both created on same day → timestamp collision possible
```

**Solutions**:
```js
// 1. Use precise timestamps (to the second)
// Knex does this automatically: 20240115143027_add_user_phone.js

// 2. Review migrations in PR
// CI runs migration tests to catch conflicts

// 3. Rebase before merge
// Developer B rebases, their migration timestamp is after A's

// 4. If conflict found: create a new migration
// Don't modify either existing migration
// Create 20240116_resolve_migration_conflict.js if needed
```

---

## Q12. (Intermediate) How do you rename a column or table without breaking the application?

```js
// WRONG: rename column in one step (breaks app during deploy)
exports.up = async function(knex) {
  await knex.schema.alterTable('users', (table) => {
    table.renameColumn('name', 'display_name'); // app code still uses 'name' → CRASH
  });
};

// RIGHT: expand-contract pattern (3 deployments)

// Migration 1: Add new column
exports.up = async function(knex) {
  await knex.schema.alterTable('users', (table) => {
    table.string('display_name', 255);
  });
  // Copy data
  await knex.raw("UPDATE users SET display_name = name");
};

// Deploy 1: Code reads from 'name', writes to both 'name' AND 'display_name'

// Migration 2: Make display_name NOT NULL, add trigger for backward compat
exports.up = async function(knex) {
  await knex.raw("ALTER TABLE users ALTER COLUMN display_name SET NOT NULL");
  // Trigger: sync name → display_name for old code that still writes to 'name'
  await knex.raw(`
    CREATE OR REPLACE FUNCTION sync_display_name()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.display_name = COALESCE(NEW.display_name, NEW.name);
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_sync_display_name
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION sync_display_name();
  `);
};

// Deploy 2: Code reads from 'display_name', writes only to 'display_name'

// Migration 3: Drop old column and trigger
exports.up = async function(knex) {
  await knex.raw('DROP TRIGGER IF EXISTS trg_sync_display_name ON users');
  await knex.raw('DROP FUNCTION IF EXISTS sync_display_name');
  await knex.schema.alterTable('users', (table) => {
    table.dropColumn('name');
  });
};
```

---

## Q13. (Advanced) How do you migrate a large table (100M+ rows) without downtime?

```js
// PROBLEM: ALTER TABLE on 100M rows can take hours and lock the table

// SOLUTION 1: PostgreSQL — many ALTER TABLE operations are instant
// These are instant (metadata-only change):
await knex.raw('ALTER TABLE big_table ADD COLUMN new_col VARCHAR(255)'); // nullable, no default
await knex.raw('ALTER TABLE big_table ALTER COLUMN new_col SET DEFAULT $1', ['value']); // set default for NEW rows
// These are NOT instant (rewrites table):
// ALTER TABLE big_table ADD COLUMN new_col VARCHAR(255) NOT NULL DEFAULT 'value'; // rewrites all rows!

// SOLUTION 2: Backfill in batches
async function backfillInBatches(knex, tableName, column, value, batchSize = 10000) {
  let affected = 0;
  let totalUpdated = 0;

  do {
    const result = await knex.raw(`
      UPDATE ${tableName}
      SET ${column} = ?
      WHERE id IN (
        SELECT id FROM ${tableName}
        WHERE ${column} IS NULL
        LIMIT ?
        FOR UPDATE SKIP LOCKED
      )
    `, [value, batchSize]);

    affected = result.rowCount;
    totalUpdated += affected;
    console.log(`Backfilled ${totalUpdated} rows`);

    // Pause between batches to reduce DB load
    await new Promise(r => setTimeout(r, 100));
  } while (affected > 0);

  return totalUpdated;
}

// SOLUTION 3: Shadow table approach (for major restructuring)
// 1. Create new table with desired schema
// 2. Set up trigger to copy writes from old → new table
// 3. Backfill old data in batches
// 4. Swap tables atomically (rename)
// This is what tools like gh-ost and pt-online-schema-change do
```

---

## Q14. (Advanced) How do you implement multi-tenant migrations?

```js
// Schema-per-tenant: run migrations for each tenant
async function migrateAllTenants(knex) {
  const tenants = await knex('tenants').select('schema_name');

  for (const tenant of tenants) {
    console.log(`Migrating tenant: ${tenant.schema_name}`);
    await knex.raw(`SET search_path TO ${tenant.schema_name}`);
    await knex.migrate.latest();
    await knex.raw('SET search_path TO public');
  }
}

// Shared-table multi-tenant: regular migrations (one schema for all)
// Just add tenant_id column to new tables
exports.up = async function(knex) {
  await knex.schema.createTable('invoices', (table) => {
    table.uuid('id').primary();
    table.uuid('tenant_id').notNullable().references('tenants.id');
    table.decimal('amount', 10, 2).notNullable();
    table.index('tenant_id');
  });
};
```

---

## Q15. (Advanced) How do you implement database versioning and track migration state?

```js
// Knex tracks migrations in a knex_migrations table
// SELECT * FROM knex_migrations ORDER BY id;
// id | name                         | batch | migration_time
// 1  | 20240101_create_users.js     | 1     | 2024-01-01 00:00:00
// 2  | 20240102_create_orders.js    | 1     | 2024-01-01 00:00:01
// 3  | 20240115_add_status.js       | 2     | 2024-01-15 12:00:00

// Custom migration tracking with version checks
exports.up = async function(knex) {
  // Check if this migration was already partially applied
  const exists = await knex.schema.hasColumn('users', 'status');
  if (exists) {
    console.log('Column already exists, skipping');
    return;
  }

  await knex.schema.alterTable('users', (table) => {
    table.string('status', 50).defaultTo('active');
  });
};

// Health check that verifies migration state
app.get('/health/db', async (req, res) => {
  const [completed, pending] = await Promise.all([
    knex.migrate.list().then(([completed]) => completed.length),
    knex.migrate.list().then(([, pending]) => pending.length),
  ]);

  if (pending > 0) {
    return res.status(503).json({
      status: 'pending_migrations',
      completed,
      pending,
    });
  }

  res.json({ status: 'ok', migrationsApplied: completed });
});
```

---

## Q16. (Advanced) How do you handle breaking schema changes in a microservices environment?

```
Problem: Order Service depends on Users table structure.
         User Service changes the schema.
         Order Service breaks.

Solution: Each service owns its database.
          Schema changes are internal to the service.
          Services communicate via APIs, not shared databases.
```

```js
// If you MUST share a database (not recommended):
// Use database views as a stable interface

// User Service controls the actual table
exports.up = async function(knex) {
  await knex.schema.alterTable('users', (table) => {
    table.renameColumn('name', 'display_name');
  });

  // Create a view for backward compatibility
  await knex.raw(`
    CREATE OR REPLACE VIEW users_v1 AS
    SELECT id, display_name AS name, email, created_at
    FROM users
  `);

  // New view with new column name
  await knex.raw(`
    CREATE OR REPLACE VIEW users_v2 AS
    SELECT id, display_name, email, created_at
    FROM users
  `);
};

// Order Service reads from users_v1 (still sees 'name')
// After Order Service is updated, switch to users_v2
```

---

## Q17. (Advanced) How do you implement database migration testing?

```js
// Test that migrations run cleanly
describe('Database Migrations', () => {
  let testKnex;

  beforeAll(async () => {
    testKnex = knex({ client: 'pg', connection: process.env.TEST_DATABASE_URL });
  });

  afterAll(async () => { await testKnex.destroy(); });

  it('applies all migrations without errors', async () => {
    await testKnex.migrate.latest();
    const [completed, pending] = await testKnex.migrate.list();
    expect(pending).toHaveLength(0);
  });

  it('rollbacks are reversible', async () => {
    await testKnex.migrate.rollback(undefined, true); // rollback all
    await testKnex.migrate.latest(); // re-apply all
    // No errors = success
  });

  it('migration is idempotent when re-run', async () => {
    await testKnex.migrate.latest();
    await testKnex.migrate.latest(); // running again should be no-op
  });

  it('data migration preserves existing data', async () => {
    // Apply migrations up to the one being tested
    await testKnex.migrate.latest();

    // Insert test data
    await testKnex('users').insert({ name: 'John Doe', email: 'john@test.com' });

    // The next migration should handle existing data correctly
    // (e.g., splitting 'name' into 'first_name' and 'last_name')
    const user = await testKnex('users').where({ email: 'john@test.com' }).first();
    expect(user.first_name).toBe('John');
    expect(user.last_name).toBe('Doe');
  });
});
```

---

## Q18. (Advanced) How do you handle migration performance for large production databases?

```js
// Monitor migration execution time
exports.up = async function(knex) {
  const start = Date.now();

  // Use CREATE INDEX CONCURRENTLY (doesn't lock table)
  await knex.raw('CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_date ON orders(created_at)');

  const duration = Date.now() - start;
  console.log(`Migration completed in ${duration}ms`);

  if (duration > 60000) {
    // Alert if migration takes > 1 minute
    console.warn('SLOW MIGRATION ALERT');
  }
};

// Advisory locks to prevent concurrent migration runs
exports.up = async function(knex) {
  // Acquire advisory lock (prevents two servers from migrating simultaneously)
  const lockId = 12345;
  const { rows } = await knex.raw('SELECT pg_try_advisory_lock(?)', [lockId]);

  if (!rows[0].pg_try_advisory_lock) {
    throw new Error('Migration already in progress on another instance');
  }

  try {
    // Run migration
    await knex.schema.alterTable('big_table', (table) => {
      table.string('new_column');
    });
  } finally {
    await knex.raw('SELECT pg_advisory_unlock(?)', [lockId]);
  }
};
```

---

## Q19. (Advanced) How do you implement blue-green database deployments?

```
Blue-Green DB Migration:
1. Blue DB (current) is serving production
2. Clone Blue → Green DB
3. Apply migrations to Green DB
4. Test Green DB with new code
5. Switch traffic from Blue to Green
6. Keep Blue as rollback for 24 hours
7. Decommission Blue

Problem: During switch, data written to Blue is lost
Solution: Use logical replication to keep them in sync
```

```js
// Simpler approach: backward-compatible migrations only
// Old code must work with new schema, new code must work with old schema

// Phase 1: Deploy migration (new schema, old code still works)
exports.up = async function(knex) {
  // ADD column (old code ignores it)
  await knex.schema.alterTable('orders', (table) => {
    table.string('tracking_number');
  });
};

// Phase 2: Deploy new code (reads/writes tracking_number)
// Phase 3: Clean up (remove old code paths if any)

// This way, there's never a moment where schema and code are incompatible
```

---

## Q20. (Advanced) Senior red flags in database migrations.

**Answer**:

1. **No migrations at all** — manual SQL changes that can't be reproduced
2. **Modifying existing migrations** — deployed migrations are immutable; create new ones
3. **No `down()` function** — can't rollback if the migration causes issues
4. **Locking tables in production** — `ALTER TABLE ... ADD COLUMN NOT NULL DEFAULT` on 100M rows
5. **Not testing migrations in CI** — migration fails in production, rollback also fails
6. **Running migrations from application code on startup** — risky; use dedicated migration step
7. **No backward compatibility** — deploy migration, then new code. If migration breaks old code, you have downtime.
8. **Mixing schema and data migrations** — keep them separate for clarity and rollback safety
9. **No migration for index creation** — indexes added manually, forgotten in other environments
10. **Ignoring migration performance** — 2-hour migration locks the database during peak hours

**Senior interview answer**: "I treat migrations as immutable, version-controlled schema changes. I always write reversible `down()` functions, test migrations in CI against a real database, and follow the expand-contract pattern for breaking changes. For large tables, I use `CREATE INDEX CONCURRENTLY`, batch backfills with `SKIP LOCKED`, and add nullable columns before making them required. I run migrations as a separate deployment step, not on app startup, and I ensure every migration is backward-compatible with the currently deployed code."
