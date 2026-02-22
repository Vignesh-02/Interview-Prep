# 4. Data Fetching & Caching Strategies

## Overview & Architecture

Next.js 15/16 introduces a fundamentally different approach to data fetching compared to earlier versions. The framework provides **four layers of caching** and multiple fetching strategies that work together to optimize performance. Understanding these layers is critical for building production-grade applications.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEXT.JS CACHING LAYERS                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: REQUEST MEMOIZATION (React cache / fetch dedup)   │   │
│  │  Scope: Single request │ Duration: Request lifetime         │   │
│  │  Deduplicates identical fetch calls within one render pass  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: DATA CACHE (fetch results on server)              │   │
│  │  Scope: Cross-request │ Duration: Persistent (revalidatable)│   │
│  │  Stores fetch responses, survives deployments               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: FULL ROUTE CACHE (rendered HTML + RSC payload)    │   │
│  │  Scope: Per-route │ Duration: Persistent (revalidatable)    │   │
│  │  Caches static routes at build time                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Layer 4: ROUTER CACHE (client-side RSC payload)            │   │
│  │  Scope: Browser session │ Duration: Session / 30s–5min      │   │
│  │  Prefetched and visited routes on the client                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Next.js 15 Critical Change: No Caching by Default

```
┌──────────────────────────────────────────────────────────────┐
│              CACHING DEFAULTS COMPARISON                      │
├──────────────────────┬───────────────────┬───────────────────┤
│  Behavior            │  Next.js 14       │  Next.js 15+      │
├──────────────────────┼───────────────────┼───────────────────┤
│  fetch() default     │  force-cache      │  no-store         │
│  GET Route Handlers  │  Cached (static)  │  Not cached       │
│  Client Router Cache │  5 min (dynamic)  │  0 (stale time)   │
│  Data Cache          │  Opt-out          │  Opt-in           │
│  Full Route Cache    │  Opt-out          │  Opt-in (dynamic) │
└──────────────────────┴───────────────────┴───────────────────┘
```

### Core fetch() Options

```typescript
// NO CACHING (Next.js 15 default)
const data = await fetch('https://api.example.com/products');

// FORCE CACHE — cache indefinitely until manually revalidated
const data = await fetch('https://api.example.com/products', {
  cache: 'force-cache',
});

// TIME-BASED REVALIDATION — revalidate every 60 seconds
const data = await fetch('https://api.example.com/products', {
  next: { revalidate: 60 },
});

// TAG-BASED REVALIDATION — revalidate by tag name
const data = await fetch('https://api.example.com/products', {
  next: { tags: ['products'] },
});

// EXPLICIT NO-STORE
const data = await fetch('https://api.example.com/products', {
  cache: 'no-store',
});
```

---

## Q1. How does `fetch()` work inside Server Components, and how has the default changed in Next.js 15? (Beginner)

**Scenario:** You upgraded a project from Next.js 14 to 15. Pages that previously showed stale data now always show fresh data, and your database is getting significantly more traffic.

```typescript
// app/products/page.tsx — same code, different behavior in v14 vs v15
export default async function ProductsPage() {
  const res = await fetch('https://api.example.com/products');
  const products = await res.json();

  return (
    <ul>
      {products.map((p: { id: string; name: string; price: number }) => (
        <li key={p.id}>
          {p.name} — ${p.price}
        </li>
      ))}
    </ul>
  );
}
```

**Answer:**

In Next.js, `fetch()` inside Server Components is extended with additional options for caching and revalidation. The most significant change in **Next.js 15** is that the default caching behavior has been reversed:

| Version | Default `cache` option | Effect |
|---------|----------------------|--------|
| Next.js 14 | `force-cache` | All fetches cached by default |
| Next.js 15+ | `no-store` | No fetches cached by default |

This means the code above behaves differently:

- **In Next.js 14:** The fetch is cached indefinitely. The page is essentially static after the first request. Database traffic is minimal.
- **In Next.js 15:** Every request hits the API fresh. The page is fully dynamic. Database traffic is per-request.

**To restore caching after upgrading to Next.js 15:**

```typescript
// Option 1: Per-fetch caching
const res = await fetch('https://api.example.com/products', {
  cache: 'force-cache',
});

// Option 2: Time-based revalidation
const res = await fetch('https://api.example.com/products', {
  next: { revalidate: 3600 }, // revalidate every hour
});

// Option 3: Route segment config (applies to all fetches in this route)
export const dynamic = 'force-static';

// Option 4: Global next.config.js override (NOT recommended)
// next.config.js
module.exports = {
  experimental: {
    staleTimes: {
      dynamic: 30, // seconds
    },
  },
};
```

**Why the change was made:** Next.js 14's aggressive caching caught many developers off-guard. Fresh data is a safer default — you opt into caching explicitly rather than accidentally serving stale data.

---

## Q2. What is Request Memoization and how does React's `cache()` function enable it? (Beginner)

**Scenario:** You have a layout and a page component that both need user data. You're worried about making duplicate API calls.

```typescript
// app/dashboard/layout.tsx
import { getUser } from '@/lib/data';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getUser(); // Call #1

  return (
    <div>
      <nav>Welcome, {user.name}</nav>
      {children}
    </div>
  );
}

// app/dashboard/page.tsx
import { getUser } from '@/lib/data';

export default async function DashboardPage() {
  const user = await getUser(); // Call #2

  return <h1>{user.name}'s Dashboard</h1>;
}
```

**Answer:**

**Request Memoization** is an automatic optimization where React and Next.js deduplicate identical `fetch()` calls within a single render pass (a single incoming request). Even though `getUser()` is called in both the layout and page, the actual network request only happens **once**.

```
┌─────────────────────────────────────────────────────────┐
│                SINGLE REQUEST LIFECYCLE                   │
│                                                          │
│  Layout calls getUser() ──┐                              │
│                            ├──► fetch() executes ONCE    │
│  Page calls getUser() ────┘    Result cached in memory   │
│                                                          │
│  Memoized result returned to both components             │
└─────────────────────────────────────────────────────────┘
```

**How `fetch()` deduplication works:**
Next.js automatically extends `fetch()` with memoization. If two `fetch()` calls in the same request have the same URL and options, the second call returns the memoized result.

**Using React's `cache()` for non-fetch functions:**

```typescript
// lib/data.ts
import { cache } from 'react';
import { db } from '@/lib/db';

// Wrap your database query with cache() for request-level deduplication
export const getUser = cache(async () => {
  const user = await db.user.findUnique({
    where: { id: getCurrentUserId() },
  });
  return user;
});

// This also works for any expensive computation
export const getAnalytics = cache(async (userId: string) => {
  const analytics = await db.analytics.aggregate({
    where: { userId },
    // ... complex aggregation
  });
  return analytics;
});
```

**Key points:**
- `fetch()` memoization is **automatic** — no extra code needed.
- For direct database calls or other non-fetch functions, use React's `cache()`.
- Memoization lasts only for the **duration of a single server request** — it does NOT persist across requests.
- Memoization only works in Server Components (during the React rendering phase).
- POST requests via `fetch()` are NOT memoized.

---

## Q3. What is the difference between `cache: 'force-cache'`, `cache: 'no-store'`, and `next: { revalidate: N }`? (Beginner)

**Scenario:** Your e-commerce store has three types of data with different freshness requirements:
1. Product categories (rarely change)
2. Product prices (change daily)
3. Inventory counts (change every minute)

```typescript
// app/store/page.tsx
export default async function StorePage() {
  // Categories — almost never change
  const categories = await fetch('https://api.store.com/categories', {
    cache: 'force-cache',
  }).then((r) => r.json());

  // Prices — revalidate every hour
  const prices = await fetch('https://api.store.com/prices', {
    next: { revalidate: 3600 },
  }).then((r) => r.json());

  // Inventory — always fresh
  const inventory = await fetch('https://api.store.com/inventory', {
    cache: 'no-store',
  }).then((r) => r.json());

  return (
    <div>
      <CategoryNav categories={categories} />
      <PriceList prices={prices} />
      <InventoryStatus inventory={inventory} />
    </div>
  );
}
```

**Answer:**

| Option | Behavior | Data Cache | Full Route Cache | Use Case |
|--------|----------|-----------|-----------------|----------|
| `cache: 'force-cache'` | Cache indefinitely | Stored until manually revalidated | Route becomes static | Rarely changing data |
| `cache: 'no-store'` | Never cache | Bypassed entirely | Route becomes dynamic | Real-time data |
| `next: { revalidate: N }` | Cache with TTL | Re-fetched after N seconds | Route re-rendered after N seconds | Periodically changing data |

```
Timeline: force-cache
─────────────────────────────────────────────────────────►
Request 1        Request 2        Request 3
   │                │                │
   ▼                ▼                ▼
 [FETCH]         [CACHE HIT]     [CACHE HIT]    ← Always cached
 Store result     Return cached   Return cached


Timeline: no-store
─────────────────────────────────────────────────────────►
Request 1        Request 2        Request 3
   │                │                │
   ▼                ▼                ▼
 [FETCH]         [FETCH]          [FETCH]        ← Always fresh
 Return fresh    Return fresh     Return fresh


Timeline: revalidate: 60 (stale-while-revalidate)
─────────────────────────────────────────────────────────►
  0s              30s              61s              62s
  │                │                │                │
  ▼                ▼                ▼                ▼
[FETCH]        [CACHE HIT]    [SERVE STALE +    [CACHE HIT]
Store result   Return cached   REVALIDATE BG]   Return new data
                               Triggers re-fetch
```

**Critical detail: stale-while-revalidate behavior**

When using `next: { revalidate: 60 }`:
1. The first request fetches and caches the data.
2. For the next 60 seconds, all requests get the cached version.
3. After 60 seconds, the next request **still receives the stale data** but triggers a background re-fetch.
4. Once the background re-fetch completes, subsequent requests get the new data.

This means users never wait for a re-fetch — they always get an instant response.

**Important:** If any fetch on a route uses `no-store`, the **entire route** becomes dynamic and opts out of the Full Route Cache.

---

## Q4. What is tag-based revalidation and how do you use `revalidateTag()`? (Beginner)

**Scenario:** You have a CMS-powered blog. When an editor publishes a new post, you want to immediately invalidate the cached blog listing page and any related tag pages without redeploying.

```typescript
// lib/data.ts
export async function getBlogPosts() {
  const res = await fetch('https://cms.example.com/api/posts', {
    next: { tags: ['blog-posts'] },
  });
  return res.json();
}

export async function getPostsByTag(tag: string) {
  const res = await fetch(`https://cms.example.com/api/posts?tag=${tag}`, {
    next: { tags: ['blog-posts', `tag-${tag}`] },
  });
  return res.json();
}

export async function getFeaturedPosts() {
  const res = await fetch('https://cms.example.com/api/posts/featured', {
    next: { tags: ['blog-posts', 'featured'] },
  });
  return res.json();
}
```

```typescript
// app/api/cms-webhook/route.ts
import { revalidateTag } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const secret = request.headers.get('x-webhook-secret');

  // Verify webhook authenticity
  if (secret !== process.env.CMS_WEBHOOK_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Revalidate all blog posts
  revalidateTag('blog-posts');

  // If specific tags were affected, revalidate those too
  if (body.tags) {
    for (const tag of body.tags) {
      revalidateTag(`tag-${tag}`);
    }
  }

  return NextResponse.json({ revalidated: true, now: Date.now() });
}
```

**Answer:**

**Tag-based revalidation** lets you associate fetch requests with string tags and then invalidate all cached data associated with a specific tag on-demand.

**How it works:**

1. **Tag your fetches** using `next: { tags: ['tag-name'] }`. A single fetch can have multiple tags.
2. **Call `revalidateTag('tag-name')`** to invalidate all cached fetches that include that tag.
3. The next request for those routes/data will trigger a fresh fetch.

```
┌───────────────────────────────────────────────────────────┐
│                    TAG REVALIDATION FLOW                   │
│                                                           │
│  fetch('/api/posts', { tags: ['blog-posts'] })            │
│  fetch('/api/posts/featured', { tags: ['blog-posts',      │
│                                         'featured'] })    │
│  fetch('/api/posts?tag=react', { tags: ['blog-posts',     │
│                                          'tag-react'] })  │
│                                                           │
│  revalidateTag('blog-posts')                              │
│       │                                                   │
│       ├──► Invalidates /api/posts cache           ✓       │
│       ├──► Invalidates /api/posts/featured cache  ✓       │
│       └──► Invalidates /api/posts?tag=react cache ✓       │
│                                                           │
│  revalidateTag('featured')                                │
│       │                                                   │
│       └──► Invalidates /api/posts/featured cache  ✓       │
│            (other caches NOT affected)                     │
└───────────────────────────────────────────────────────────┘
```

**Tag-based vs Path-based revalidation:**

| Feature | `revalidateTag()` | `revalidatePath()` |
|---------|-------------------|-------------------|
| Granularity | Data-level | Route-level |
| Scope | All fetches with that tag | All data for that path |
| Use case | Invalidate specific data across routes | Invalidate an entire page |
| Precision | High — surgical invalidation | Lower — entire route re-rendered |

**Production pattern: CMS webhook handler**

```typescript
// app/api/revalidate/route.ts
import { revalidateTag, revalidatePath } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

const VALID_TAGS = ['blog-posts', 'products', 'featured', 'navigation'];

export async function POST(request: NextRequest) {
  const { tag, path, secret } = await request.json();

  if (secret !== process.env.REVALIDATION_SECRET) {
    return NextResponse.json({ message: 'Invalid secret' }, { status: 401 });
  }

  if (tag && VALID_TAGS.includes(tag)) {
    revalidateTag(tag);
    return NextResponse.json({ revalidated: true, type: 'tag', tag });
  }

  if (path) {
    revalidatePath(path);
    return NextResponse.json({ revalidated: true, type: 'path', path });
  }

  return NextResponse.json({ message: 'No tag or path provided' }, { status: 400 });
}
```

---

## Q5. How do you fetch data in parallel vs. in a waterfall pattern, and why does it matter? (Beginner)

**Scenario:** A dashboard page needs data from three independent APIs. You notice the page takes 3 seconds to load. Each API call takes about 1 second.

```typescript
// ❌ WATERFALL PATTERN — 3 seconds total
export default async function DashboardPage() {
  const user = await fetchUser();       // 1s
  const orders = await fetchOrders();   // 1s (waits for user)
  const analytics = await fetchAnalytics(); // 1s (waits for orders)
  // Total: ~3 seconds

  return (
    <div>
      <UserProfile user={user} />
      <OrderList orders={orders} />
      <AnalyticsChart analytics={analytics} />
    </div>
  );
}
```

**Answer:**

When fetches don't depend on each other, you should run them **in parallel** using `Promise.all()` or `Promise.allSettled()`:

```typescript
// ✅ PARALLEL PATTERN — 1 second total
export default async function DashboardPage() {
  const [user, orders, analytics] = await Promise.all([
    fetchUser(),       // 1s ─┐
    fetchOrders(),     // 1s ─┤ All run simultaneously
    fetchAnalytics(),  // 1s ─┘
  ]);
  // Total: ~1 second (limited by slowest call)

  return (
    <div>
      <UserProfile user={user} />
      <OrderList orders={orders} />
      <AnalyticsChart analytics={analytics} />
    </div>
  );
}
```

```
WATERFALL (Sequential)                PARALLEL (Concurrent)
─────────────────────                 ─────────────────────

Time 0s  ┌──────────┐                Time 0s  ┌──────────┐
         │ fetchUser │                         │ fetchUser │
Time 1s  └──────────┘                         ├──────────┤
         ┌────────────┐                       │fetchOrders│
         │ fetchOrders │                      ├───────────┤
Time 2s  └────────────┘                       │fetchAnalyt│
         ┌───────────────┐            Time 1s └───────────┘
         │ fetchAnalytics │
Time 3s  └───────────────┘            Total: ~1s
                                      (3x faster!)
Total: ~3s
```

**Using `Promise.allSettled()` for resilient fetching:**

```typescript
export default async function DashboardPage() {
  const results = await Promise.allSettled([
    fetchUser(),
    fetchOrders(),
    fetchAnalytics(),
  ]);

  const user = results[0].status === 'fulfilled' ? results[0].value : null;
  const orders = results[1].status === 'fulfilled' ? results[1].value : null;
  const analytics = results[2].status === 'fulfilled' ? results[2].value : null;

  return (
    <div>
      {user ? <UserProfile user={user} /> : <UserProfileFallback />}
      {orders ? <OrderList orders={orders} /> : <OrdersFallback />}
      {analytics ? <AnalyticsChart analytics={analytics} /> : <AnalyticsFallback />}
    </div>
  );
}
```

**When waterfalls are unavoidable (dependent data):**

```typescript
export default async function UserOrderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  // Step 1: Need user first to get their org
  const user = await fetchUser(id);

  // Step 2: Parallel fetch of data that depends on user
  const [orders, permissions] = await Promise.all([
    fetchOrders(user.orgId),       // Depends on user.orgId
    fetchPermissions(user.roleId), // Depends on user.roleId
  ]);

  return (
    <div>
      <UserProfile user={user} />
      <OrderList orders={orders} />
      <PermissionsPanel permissions={permissions} />
    </div>
  );
}
```

**Best pattern: Component-level parallel fetching with Suspense:**

```typescript
// Each component fetches its own data — Next.js streams them in parallel
export default function DashboardPage() {
  return (
    <div>
      <Suspense fallback={<UserSkeleton />}>
        <UserProfile />   {/* Fetches user data internally */}
      </Suspense>
      <Suspense fallback={<OrdersSkeleton />}>
        <OrderList />     {/* Fetches orders internally */}
      </Suspense>
      <Suspense fallback={<AnalyticsSkeleton />}>
        <AnalyticsChart /> {/* Fetches analytics internally */}
      </Suspense>
    </div>
  );
}
```

This approach streams each component as soon as its data is ready, giving the fastest perceived performance.

---

## Q6. How does `unstable_cache()` work for caching non-fetch data like database queries, and how does it differ from React's `cache()`? (Intermediate)

**Scenario:** You use Prisma for database access and need to cache expensive queries across multiple requests. You've tried React's `cache()` but notice the data is re-fetched on every new request.

```typescript
// lib/data.ts — Using React cache() (request-level only)
import { cache } from 'react';
import { db } from '@/lib/db';

export const getProductStats = cache(async (productId: string) => {
  // This runs once per REQUEST, not cached across requests
  return db.orderItem.aggregate({
    where: { productId },
    _sum: { quantity: true, revenue: true },
    _count: { _all: true },
  });
});
```

**Answer:**

React's `cache()` and Next.js's `unstable_cache()` (now stable as of Next.js 15 with the `use cache` directive being the future) serve different purposes:

| Feature | React `cache()` | `unstable_cache()` |
|---------|-----------------|-------------------|
| Scope | Single request | Cross-request (persistent) |
| Duration | Request lifetime | Until revalidated |
| Storage | In-memory | Data Cache (disk/CDN) |
| Use case | Request dedup | Persistent caching |
| Works with | Any function | Serializable returns only |

```
┌──────────────────────────────────────────────────────────┐
│            cache() vs unstable_cache()                    │
│                                                          │
│  Request 1:                                              │
│    cache(fn)          → Executes fn, memoizes            │
│    unstable_cache(fn) → Executes fn, stores in Data Cache│
│                                                          │
│  Request 2:                                              │
│    cache(fn)          → Executes fn AGAIN (new request)  │
│    unstable_cache(fn) → Returns from Data Cache (cached) │
│                                                          │
│  After revalidateTag('stats'):                           │
│    cache(fn)          → Not affected                     │
│    unstable_cache(fn) → Cache invalidated, re-executes   │
└──────────────────────────────────────────────────────────┘
```

**Using `unstable_cache()` for persistent caching:**

```typescript
// lib/data.ts
import { unstable_cache } from 'next/cache';
import { db } from '@/lib/db';

// Cached across requests, revalidatable via tags
export const getProductStats = unstable_cache(
  async (productId: string) => {
    return db.orderItem.aggregate({
      where: { productId },
      _sum: { quantity: true, revenue: true },
      _count: { _all: true },
    });
  },
  // Cache key parts — combined with args to form unique key
  ['product-stats'],
  {
    tags: ['product-stats'],     // For tag-based revalidation
    revalidate: 3600,            // Or time-based: 1 hour
  }
);

// Usage in a Server Component
export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const stats = await getProductStats(id); // Cached across requests!

  return <StatsDisplay stats={stats} />;
}
```

**Combining both for maximum efficiency:**

```typescript
import { cache } from 'react';
import { unstable_cache } from 'next/cache';
import { db } from '@/lib/db';

// Layer 1: unstable_cache for cross-request persistence
const _getProduct = unstable_cache(
  async (productId: string) => {
    return db.product.findUnique({
      where: { id: productId },
      include: { category: true, reviews: { take: 10 } },
    });
  },
  ['product-detail'],
  { tags: ['products'], revalidate: 300 }
);

// Layer 2: React cache() for request-level dedup
export const getProduct = cache(async (productId: string) => {
  return _getProduct(productId);
});
```

**Next.js 15+ `use cache` directive (the future replacement):**

```typescript
// lib/data.ts — Next.js 15+ with use cache directive
'use cache';

import { db } from '@/lib/db';
import { cacheTag, cacheLife } from 'next/cache';

export async function getProductStats(productId: string) {
  cacheTag('product-stats', `product-${productId}`);
  cacheLife('hours'); // Predefined cache profile

  return db.orderItem.aggregate({
    where: { productId },
    _sum: { quantity: true, revenue: true },
    _count: { _all: true },
  });
}
```

---

## Q7. How does Incremental Static Regeneration (ISR) work in the App Router, and how do you implement it for an e-commerce product catalog? (Intermediate)

**Scenario:** Your e-commerce store has 50,000 products. You need fast page loads but also reasonably fresh data. Full static generation at build time takes too long, and SSR on every request is too slow.

**Answer:**

ISR in the App Router works through a combination of `generateStaticParams()`, time-based revalidation, and on-demand revalidation.

```
┌────────────────────────────────────────────────────────────┐
│                 ISR LIFECYCLE                                │
│                                                             │
│  BUILD TIME                                                 │
│  ──────────                                                 │
│  generateStaticParams() → returns top 1000 product IDs     │
│  Next.js pre-renders those 1000 pages as static HTML       │
│                                                             │
│  RUNTIME (within revalidation window)                       │
│  ──────────                                                 │
│  Request for /product/123 → Serve cached static page        │
│  Request for /product/99999 → Generate on first request,    │
│                                cache for subsequent ones     │
│                                                             │
│  RUNTIME (after revalidation window)                        │
│  ──────────                                                 │
│  Request for /product/123 → Serve stale page,               │
│                              regenerate in background        │
│  Next request → Serve fresh page                            │
└────────────────────────────────────────────────────────────┘
```

**Full implementation:**

```typescript
// app/products/[slug]/page.tsx
import { notFound } from 'next/navigation';
import { db } from '@/lib/db';

// ISR: Revalidate every 5 minutes
export const revalidate = 300;

// Pre-generate top products at build time
export async function generateStaticParams() {
  const topProducts = await db.product.findMany({
    where: { status: 'ACTIVE' },
    orderBy: { salesCount: 'desc' },
    take: 1000,
    select: { slug: true },
  });

  return topProducts.map((product) => ({
    slug: product.slug,
  }));
}

// Dynamic params that weren't pre-generated will be generated on-demand
export const dynamicParams = true; // default — set false to 404 on unknown slugs

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) return { title: 'Product Not Found' };

  return {
    title: `${product.name} | Store`,
    description: product.description.slice(0, 160),
    openGraph: {
      images: [product.imageUrl],
    },
  };
}

async function getProduct(slug: string) {
  return db.product.findUnique({
    where: { slug },
    include: {
      category: true,
      reviews: {
        orderBy: { createdAt: 'desc' },
        take: 20,
        include: { user: { select: { name: true, avatarUrl: true } } },
      },
      variants: true,
    },
  });
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await getProduct(slug);

  if (!product) notFound();

  return (
    <article>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <ProductGallery images={product.images} />
        <div>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-2xl mt-2">${product.price.toFixed(2)}</p>
          <ProductVariantSelector variants={product.variants} />
          <AddToCartButton productId={product.id} />
        </div>
      </div>
      <ProductReviews reviews={product.reviews} />
    </article>
  );
}
```

**On-demand revalidation when products are updated:**

```typescript
// app/api/admin/products/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const { slug, action } = await request.json();
  const authHeader = request.headers.get('authorization');

  if (authHeader !== `Bearer ${process.env.ADMIN_API_KEY}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  switch (action) {
    case 'update-product':
      revalidatePath(`/products/${slug}`);
      revalidateTag('product-listings');
      break;
    case 'update-all-prices':
      revalidateTag('product-prices');
      break;
    case 'update-category':
      revalidatePath('/products', 'layout'); // Revalidate all product pages
      break;
  }

  return NextResponse.json({ revalidated: true });
}
```

---

## Q8. Explain the Full Route Cache and how different data fetching strategies affect which routes are statically or dynamically rendered. (Intermediate)

**Scenario:** You need to understand why some pages in your Next.js app are served instantly (static) while others have a delay (dynamic), and how to control this behavior.

**Answer:**

The **Full Route Cache** stores the rendered HTML and RSC payload of routes at build time. In Next.js 15, a route must explicitly opt-in to static rendering because fetches default to `no-store`.

```
┌─────────────────────────────────────────────────────────────────┐
│              ROUTE RENDERING DECISION TREE                       │
│                                                                  │
│  Does the route use any dynamic functions?                       │
│  (cookies(), headers(), searchParams, connection())              │
│       │                                                          │
│       ├── YES → DYNAMIC (rendered per-request)                   │
│       │                                                          │
│       └── NO → Does any fetch use cache: 'no-store'?            │
│                 (or default in Next.js 15)                       │
│                    │                                             │
│                    ├── YES → DYNAMIC                             │
│                    │                                             │
│                    └── NO → Are all fetches cached?              │
│                              (force-cache or revalidate)         │
│                                 │                                │
│                                 ├── YES → STATIC                 │
│                                 │    (Full Route Cache ✓)        │
│                                 │                                │
│                                 └── NO → DYNAMIC                 │
└─────────────────────────────────────────────────────────────────┘
```

**Functions that make a route dynamic:**

```typescript
import { cookies, headers } from 'next/headers';
import { connection } from 'next/server';

export default async function Page({ searchParams }: {
  searchParams: Promise<{ q?: string }>;
}) {
  // ANY of these make the route dynamic:
  const cookieStore = await cookies();      // Dynamic ❌ (reads request cookies)
  const headersList = await headers();      // Dynamic ❌ (reads request headers)
  const { q } = await searchParams;         // Dynamic ❌ (reads search params)
  await connection();                       // Dynamic ❌ (signals dynamic intent)

  // ...
}
```

**Forcing static or dynamic behavior:**

```typescript
// Force STATIC — even if the route has dynamic patterns
export const dynamic = 'force-static';
// cookies(), headers(), searchParams will return empty values

// Force DYNAMIC — even if the route could be static
export const dynamic = 'force-dynamic';
// Equivalent to cache: 'no-store' on every fetch

// Error if dynamic features are used (safety check)
export const dynamic = 'error';
// Build fails if cookies/headers/searchParams are used
```

**Seeing which routes are static vs dynamic after build:**

```bash
$ next build

Route (app)                    Size     First Load JS
┌ ○ /                          5.2 kB   89.1 kB
├ ○ /about                     1.2 kB   85.1 kB
├ ● /blog/[slug]               3.4 kB   87.3 kB
├ λ /dashboard                 8.1 kB   92.0 kB
├ λ /api/users                 0 B      0 B
└ ○ /products                  4.2 kB   88.1 kB

○  (Static)    prerendered as static content
●  (SSG)       prerendered as static HTML (uses generateStaticParams)
λ  (Dynamic)   server-rendered on demand
```

**Production recommendation: Audit your routes**

```typescript
// next.config.ts — Enable logging to debug caching
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  logging: {
    fetches: {
      fullUrl: true,  // Log full fetch URLs
    },
  },
};

export default nextConfig;
```

This logs every fetch in development with its cache status:

```
GET https://api.example.com/products 200 in 45ms (cache: HIT)
GET https://api.example.com/user 200 in 120ms (cache: SKIP)
GET https://api.example.com/cart 200 in 89ms (cache: SKIP - cache: no-store)
```

---

## Q9. How do you implement a production-ready data fetching layer with error handling, types, and caching for a SaaS application? (Intermediate)

**Scenario:** You're building a SaaS dashboard and need a reusable, type-safe data fetching layer that handles errors gracefully, caches appropriately, and works with Server Components.

**Answer:**

```typescript
// lib/api/fetcher.ts
type FetchOptions = {
  tags?: string[];
  revalidate?: number | false;
  cache?: RequestCache;
};

type ApiResponse<T> =
  | { data: T; error: null }
  | { data: null; error: { message: string; status: number } };

const API_BASE_URL = process.env.API_URL!;

export async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<ApiResponse<T>> {
  const { tags, revalidate, cache: cacheOption } = options;

  const fetchOptions: RequestInit & { next?: Record<string, unknown> } = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.API_SECRET_KEY}`,
    },
  };

  // Build next options
  if (tags || revalidate !== undefined) {
    fetchOptions.next = {};
    if (tags) fetchOptions.next.tags = tags;
    if (revalidate !== undefined) fetchOptions.next.revalidate = revalidate;
  }

  // Set cache option
  if (cacheOption) {
    fetchOptions.cache = cacheOption;
  }

  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);

    if (!res.ok) {
      return {
        data: null,
        error: {
          message: `API error: ${res.statusText}`,
          status: res.status,
        },
      };
    }

    const data: T = await res.json();
    return { data, error: null };
  } catch (err) {
    return {
      data: null,
      error: {
        message: err instanceof Error ? err.message : 'Unknown error',
        status: 500,
      },
    };
  }
}
```

```typescript
// lib/api/queries.ts
import { cache } from 'react';
import { apiFetch } from './fetcher';

// Types
interface Workspace {
  id: string;
  name: string;
  plan: 'free' | 'pro' | 'enterprise';
  memberCount: number;
}

interface DashboardMetrics {
  activeUsers: number;
  revenue: number;
  churnRate: number;
  mrr: number;
  trends: { date: string; value: number }[];
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'admin' | 'member';
  lastActive: string;
}

// Request-deduped + persistent cache
export const getWorkspace = cache(async (workspaceId: string) => {
  return apiFetch<Workspace>(`/workspaces/${workspaceId}`, {
    tags: [`workspace-${workspaceId}`],
    revalidate: 300, // 5 minutes
  });
});

// Fresh on every request — dashboard should show latest
export const getDashboardMetrics = cache(async (workspaceId: string) => {
  return apiFetch<DashboardMetrics>(
    `/workspaces/${workspaceId}/metrics`,
    { cache: 'no-store' }
  );
});

// Cached with tag-based invalidation
export const getTeamMembers = cache(async (workspaceId: string) => {
  return apiFetch<TeamMember[]>(`/workspaces/${workspaceId}/members`, {
    tags: [`team-${workspaceId}`],
    revalidate: 60,
  });
});
```

```typescript
// app/dashboard/[workspaceId]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { getWorkspace, getDashboardMetrics, getTeamMembers } from '@/lib/api/queries';

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const { data: workspace, error } = await getWorkspace(workspaceId);

  if (error || !workspace) notFound();

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold">{workspace.name} Dashboard</h1>
        <span className="text-sm text-gray-500">{workspace.plan} plan</span>
      </header>

      <Suspense fallback={<MetricsSkeleton />}>
        <MetricsSection workspaceId={workspaceId} />
      </Suspense>

      <Suspense fallback={<TeamSkeleton />}>
        <TeamSection workspaceId={workspaceId} />
      </Suspense>
    </div>
  );
}

async function MetricsSection({ workspaceId }: { workspaceId: string }) {
  const { data: metrics, error } = await getDashboardMetrics(workspaceId);

  if (error || !metrics) {
    return <div className="p-4 bg-red-50 rounded">Failed to load metrics</div>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricCard label="Active Users" value={metrics.activeUsers} />
      <MetricCard label="MRR" value={`$${metrics.mrr.toLocaleString()}`} />
      <MetricCard label="Revenue" value={`$${metrics.revenue.toLocaleString()}`} />
      <MetricCard label="Churn Rate" value={`${metrics.churnRate}%`} />
    </div>
  );
}

async function TeamSection({ workspaceId }: { workspaceId: string }) {
  const { data: members, error } = await getTeamMembers(workspaceId);

  if (error || !members) {
    return <div className="p-4 bg-red-50 rounded">Failed to load team</div>;
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Team ({members.length})</h2>
      <ul className="divide-y">
        {members.map((member) => (
          <li key={member.id} className="py-3 flex justify-between">
            <span>{member.name}</span>
            <span className="text-gray-500">{member.role}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}
```

---

## Q10. How do you use `revalidatePath()` effectively, and what are the differences between its various overloads? (Intermediate)

**Scenario:** After a user updates their profile, you need to revalidate different parts of your app — the user's profile page, the team page that shows their info, and the layout that shows their avatar.

```typescript
// app/actions/profile.ts
'use server';

import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export async function updateProfile(formData: FormData) {
  const userId = formData.get('userId') as string;
  const name = formData.get('name') as string;

  await db.user.update({
    where: { id: userId },
    data: { name },
  });

  // Which revalidatePath overload should you use?
}
```

**Answer:**

`revalidatePath()` has two forms with different scoping:

```typescript
// Signature
revalidatePath(path: string, type?: 'page' | 'layout'): void;
```

| Call | Effect |
|------|--------|
| `revalidatePath('/profile')` | Revalidates the `/profile` page only |
| `revalidatePath('/profile', 'page')` | Same as above — default is `'page'` |
| `revalidatePath('/profile', 'layout')` | Revalidates `/profile` AND all nested routes under it |
| `revalidatePath('/')` | Revalidates the home page only |
| `revalidatePath('/', 'layout')` | Revalidates the root layout and ALL routes in the app |

```
┌─────────────────────────────────────────────────────────────┐
│  revalidatePath('/dashboard', 'page')                        │
│                                                              │
│  /dashboard          ← Revalidated ✓                        │
│  /dashboard/settings ← NOT revalidated ✗                    │
│  /dashboard/team     ← NOT revalidated ✗                    │
│                                                              │
│  revalidatePath('/dashboard', 'layout')                      │
│                                                              │
│  /dashboard          ← Revalidated ✓                        │
│  /dashboard/settings ← Revalidated ✓                        │
│  /dashboard/team     ← Revalidated ✓                        │
│  /dashboard/team/123 ← Revalidated ✓                        │
└─────────────────────────────────────────────────────────────┘
```

**Complete profile update example:**

```typescript
// app/actions/profile.ts
'use server';

import { revalidatePath, revalidateTag } from 'next/cache';
import { db } from '@/lib/db';

export async function updateProfile(formData: FormData) {
  const userId = formData.get('userId') as string;
  const name = formData.get('name') as string;
  const avatarUrl = formData.get('avatarUrl') as string;

  await db.user.update({
    where: { id: userId },
    data: { name, avatarUrl },
  });

  // Strategy 1: Surgical path revalidation
  revalidatePath(`/users/${userId}`);          // User's profile page
  revalidatePath(`/team`, 'page');             // Team listing page

  // Strategy 2: If avatar changed, revalidate the layout (shows in navbar)
  if (avatarUrl) {
    revalidatePath('/', 'layout');              // Revalidates everything under root layout
  }

  // Strategy 3: Use tags for cross-cutting concerns
  revalidateTag(`user-${userId}`);             // Invalidate all cached data for this user
}
```

**When to use `revalidatePath` vs `revalidateTag`:**

```typescript
// revalidatePath — when you know WHICH ROUTES are affected
revalidatePath('/products/shoes');  // Specific product page
revalidatePath('/products', 'layout');  // All product pages

// revalidateTag — when you know WHICH DATA changed
revalidateTag('products');  // All fetches tagged with 'products'
revalidateTag('user-123');  // All fetches tagged with 'user-123'

// Best practice: Use BOTH for comprehensive invalidation
export async function updateProduct(productId: string, data: ProductUpdate) {
  await db.product.update({ where: { id: productId }, data });

  // Invalidate the specific page
  revalidatePath(`/products/${data.slug}`);

  // Invalidate all cached data tagged with this product
  revalidateTag(`product-${productId}`);

  // Invalidate listing pages
  revalidateTag('product-listings');
}
```

---

## Q11. How do you handle the Router Cache (client-side cache) in Next.js 15, and how has it changed from Next.js 14? (Intermediate)

**Scenario:** Users complain that after updating their settings, navigating back to the dashboard still shows old data. You're using `<Link>` for navigation.

**Answer:**

The **Router Cache** is a client-side, in-memory cache that stores RSC payloads of visited and prefetched routes. In Next.js 15, the default behavior changed significantly:

```
┌─────────────────────────────────────────────────────────────┐
│              ROUTER CACHE DEFAULTS                            │
├─────────────────────┬───────────────────┬───────────────────┤
│                     │  Next.js 14       │  Next.js 15+      │
├─────────────────────┼───────────────────┼───────────────────┤
│  Dynamic pages      │  30 seconds       │  0 seconds        │
│  Static pages       │  5 minutes        │  5 minutes        │
│  Prefetched (full)  │  5 minutes        │  5 minutes        │
│  Prefetched (partial)│ 30 seconds       │  0 seconds        │
└─────────────────────┴───────────────────┴───────────────────┘
```

**In Next.js 15, dynamic pages are NOT client-cached by default.** Navigation to a dynamic page always triggers a fresh server request. This is why the user complaint from the scenario should no longer occur in v15.

**Understanding prefetch behavior:**

```typescript
// FULL prefetch — caches entire route
// Triggered by: <Link href="/about" /> on static routes
// or: <Link href="/about" prefetch={true} />
// Cache duration: 5 minutes

// PARTIAL prefetch — caches up to first loading.tsx boundary
// Triggered by: <Link href="/dashboard" /> on dynamic routes
// Cache duration: 0 seconds in Next.js 15 (was 30s in v14)

// NO prefetch
// <Link href="/dashboard" prefetch={false} />
```

**Invalidating the Router Cache:**

```typescript
'use client';

import { useRouter } from 'next/navigation';

export function SettingsForm() {
  const router = useRouter();

  async function handleSubmit(formData: FormData) {
    await updateSettings(formData);

    // Method 1: router.refresh() — revalidates current route
    router.refresh(); // Fetches fresh data for the current page

    // Method 2: router.push() with server-side revalidation
    // If the Server Action calls revalidatePath/revalidateTag,
    // navigation will fetch fresh data
    router.push('/dashboard');

    // Method 3: revalidatePath in Server Action
    // This automatically invalidates the Router Cache for that path
  }

  return <form action={handleSubmit}>{/* ... */}</form>;
}
```

**Configuring Router Cache stale times:**

```typescript
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    staleTimes: {
      dynamic: 30,   // Cache dynamic pages for 30 seconds (default: 0)
      static: 180,   // Cache static pages for 3 minutes (default: 300)
    },
  },
};

export default nextConfig;
```

**Key behaviors:**

1. **Server Actions that call `revalidatePath()` or `revalidateTag()`** automatically invalidate the Router Cache for affected routes.
2. **`router.refresh()`** invalidates the Router Cache for the current route only.
3. **`cookies.set()` or `cookies.delete()`** in Server Actions invalidate the Router Cache to prevent stale auth states.

---

## Q12. How do you implement parallel route data fetching with streaming for a complex dashboard? (Intermediate)

**Scenario:** You have a dashboard with 5 independent data panels. Each panel fetches from a different service with varying response times (100ms to 3 seconds). You want each panel to appear as soon as its data is ready.

**Answer:**

```typescript
// app/dashboard/page.tsx
import { Suspense } from 'react';

export default function DashboardPage() {
  return (
    <div className="grid grid-cols-12 gap-6 p-6">
      {/* Row 1: Key metrics (fast) and revenue chart (medium) */}
      <div className="col-span-8">
        <Suspense fallback={<RevenueChartSkeleton />}>
          <RevenueChart />
        </Suspense>
      </div>
      <div className="col-span-4">
        <Suspense fallback={<MetricsSkeleton />}>
          <KeyMetrics />
        </Suspense>
      </div>

      {/* Row 2: Activity feed (fast), top products (medium), alerts (slow) */}
      <div className="col-span-4">
        <Suspense fallback={<ActivitySkeleton />}>
          <ActivityFeed />
        </Suspense>
      </div>
      <div className="col-span-4">
        <Suspense fallback={<ProductsSkeleton />}>
          <TopProducts />
        </Suspense>
      </div>
      <div className="col-span-4">
        <Suspense fallback={<AlertsSkeleton />}>
          <SystemAlerts />
        </Suspense>
      </div>
    </div>
  );
}
```

```typescript
// Each component fetches its own data independently

// components/dashboard/RevenueChart.tsx
import { getRevenueData } from '@/lib/api/queries';

export default async function RevenueChart() {
  const { data } = await getRevenueData(); // ~800ms

  if (!data) return <ErrorPanel message="Failed to load revenue data" />;

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Revenue</h2>
      <div className="h-64">
        <ChartRenderer data={data.trends} />
      </div>
    </div>
  );
}

// components/dashboard/KeyMetrics.tsx
import { getKeyMetrics } from '@/lib/api/queries';

export default async function KeyMetrics() {
  const { data } = await getKeyMetrics(); // ~200ms

  if (!data) return <ErrorPanel message="Failed to load metrics" />;

  return (
    <div className="bg-white rounded-xl shadow p-6 space-y-4">
      <h2 className="text-lg font-semibold">Key Metrics</h2>
      <MetricRow label="MRR" value={`$${data.mrr.toLocaleString()}`} trend={data.mrrTrend} />
      <MetricRow label="Users" value={data.activeUsers.toLocaleString()} trend={data.usersTrend} />
      <MetricRow label="Churn" value={`${data.churnRate}%`} trend={data.churnTrend} />
    </div>
  );
}

// components/dashboard/SystemAlerts.tsx
import { getSystemAlerts } from '@/lib/api/queries';

export default async function SystemAlerts() {
  const { data } = await getSystemAlerts(); // ~3000ms (slow service)

  if (!data) return <ErrorPanel message="Failed to load alerts" />;

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold mb-4">System Alerts</h2>
      <ul className="space-y-2">
        {data.alerts.map((alert) => (
          <li key={alert.id} className={`p-3 rounded ${severityColors[alert.severity]}`}>
            <span className="font-medium">{alert.title}</span>
            <span className="text-sm text-gray-600 block">{alert.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const severityColors: Record<string, string> = {
  critical: 'bg-red-50 border-l-4 border-red-500',
  warning: 'bg-yellow-50 border-l-4 border-yellow-500',
  info: 'bg-blue-50 border-l-4 border-blue-500',
};
```

```
STREAMING TIMELINE:
──────────────────────────────────────────────────────────────

0ms     Shell (layout + Suspense fallbacks) streamed to client
        ┌──────────────────────────────────────────────┐
        │ [RevenueChartSkeleton] [MetricsSkeleton]     │
        │ [ActivitySkeleton] [ProductsSkel] [AlertsSk] │
        └──────────────────────────────────────────────┘

~100ms  ActivityFeed resolves → streamed to client
        ┌──────────────────────────────────────────────┐
        │ [RevenueChartSkeleton] [MetricsSkeleton]     │
        │ [✓ ActivityFeed]  [ProductsSkel] [AlertsSk]  │
        └──────────────────────────────────────────────┘

~200ms  KeyMetrics resolves → streamed to client
        ┌──────────────────────────────────────────────┐
        │ [RevenueChartSkeleton] [✓ KeyMetrics]        │
        │ [✓ ActivityFeed]  [ProductsSkel] [AlertsSk]  │
        └──────────────────────────────────────────────┘

~800ms  RevenueChart resolves → streamed to client
        ┌──────────────────────────────────────────────┐
        │ [✓ RevenueChart]       [✓ KeyMetrics]        │
        │ [✓ ActivityFeed]  [ProductsSkel] [AlertsSk]  │
        └──────────────────────────────────────────────┘

~1200ms TopProducts resolves → streamed to client

~3000ms SystemAlerts resolves → final piece streamed
        ┌──────────────────────────────────────────────┐
        │ [✓ RevenueChart]       [✓ KeyMetrics]        │
        │ [✓ ActivityFeed]  [✓ TopProducts] [✓ Alerts] │
        └──────────────────────────────────────────────┘
```

**Key advantage:** The user sees the shell instantly (0ms), metrics at 200ms, the chart at 800ms — they can start reading data within milliseconds. Only the slowest panel (alerts at 3s) loads last, but it doesn't block anything else.

---

## Q13. How do you build a multi-tenant caching strategy where each tenant has isolated caches with different revalidation policies? (Advanced)

**Scenario:** Your SaaS app serves 500 tenants. Each tenant has different data freshness requirements based on their plan (Free: 5min cache, Pro: 1min cache, Enterprise: real-time). Tenants should never see each other's data.

**Answer:**

```typescript
// lib/cache/tenant-cache.ts
import { unstable_cache } from 'next/cache';
import { cache } from 'react';
import { db } from '@/lib/db';
import { getTenantFromHeaders } from '@/lib/auth';

// Tenant plan → revalidation time mapping
const PLAN_REVALIDATION: Record<string, number | false> = {
  free: 300,        // 5 minutes
  pro: 60,          // 1 minute
  enterprise: false, // no cache (always fresh)
};

// Request-level tenant resolution (deduped per request)
export const getCurrentTenant = cache(async () => {
  const tenant = await getTenantFromHeaders();
  if (!tenant) throw new Error('No tenant context');
  return tenant;
});

// Factory function to create tenant-scoped cached queries
export function createTenantQuery<TArgs extends unknown[], TResult>(
  queryFn: (tenantId: string, ...args: TArgs) => Promise<TResult>,
  keyParts: string[],
  options?: { additionalTags?: (tenantId: string) => string[] }
) {
  return cache(async (...args: TArgs): Promise<TResult> => {
    const tenant = await getCurrentTenant();
    const revalidate = PLAN_REVALIDATION[tenant.plan];

    // Enterprise plan — no caching
    if (revalidate === false) {
      return queryFn(tenant.id, ...args);
    }

    // Free/Pro plans — cached with tenant-scoped keys and tags
    const cachedFn = unstable_cache(
      () => queryFn(tenant.id, ...args),
      // Cache key includes tenant ID for isolation
      [`tenant-${tenant.id}`, ...keyParts, ...args.map(String)],
      {
        revalidate,
        tags: [
          `tenant-${tenant.id}`,
          ...keyParts.map((k) => `tenant-${tenant.id}:${k}`),
          ...(options?.additionalTags?.(tenant.id) ?? []),
        ],
      }
    );

    return cachedFn();
  });
}
```

```typescript
// lib/api/tenant-queries.ts
import { createTenantQuery } from '@/lib/cache/tenant-cache';
import { db } from '@/lib/db';

// Each query is automatically scoped to the current tenant
export const getDashboardMetrics = createTenantQuery(
  async (tenantId: string) => {
    return db.metrics.findFirst({
      where: { tenantId },
      orderBy: { createdAt: 'desc' },
    });
  },
  ['dashboard-metrics']
);

export const getTeamMembers = createTenantQuery(
  async (tenantId: string, page: number = 1) => {
    return db.user.findMany({
      where: { tenantId },
      skip: (page - 1) * 20,
      take: 20,
      orderBy: { name: 'asc' },
    });
  },
  ['team-members'],
  {
    additionalTags: (tenantId) => [`team-${tenantId}`],
  }
);

export const getProjects = createTenantQuery(
  async (tenantId: string, status?: string) => {
    return db.project.findMany({
      where: {
        tenantId,
        ...(status ? { status } : {}),
      },
      include: { owner: { select: { name: true } } },
      orderBy: { updatedAt: 'desc' },
    });
  },
  ['projects'],
  {
    additionalTags: (tenantId) => [`projects-${tenantId}`],
  }
);
```

```typescript
// Revalidation for a specific tenant
// app/api/webhooks/tenant-update/route.ts
import { revalidateTag } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const { tenantId, scope } = await request.json();

  switch (scope) {
    case 'all':
      // Invalidate ALL cached data for this tenant
      revalidateTag(`tenant-${tenantId}`);
      break;
    case 'team':
      // Invalidate only team-related caches
      revalidateTag(`team-${tenantId}`);
      break;
    case 'projects':
      revalidateTag(`projects-${tenantId}`);
      break;
  }

  return NextResponse.json({ revalidated: true, tenantId, scope });
}
```

```
┌─────────────────────────────────────────────────────────────┐
│              TENANT CACHE ISOLATION                           │
│                                                              │
│  Tenant A (Pro - 60s cache)                                  │
│  ┌─────────────────────────────┐                             │
│  │ Key: tenant-A:dashboard     │                             │
│  │ Key: tenant-A:team-members  │  ← Tags: [tenant-A,        │
│  │ Key: tenant-A:projects      │           team-A,           │
│  └─────────────────────────────┘           projects-A]       │
│                                                              │
│  Tenant B (Enterprise - no cache)                            │
│  ┌─────────────────────────────┐                             │
│  │ No cache entries!           │  ← Always fetches fresh     │
│  │ Every request hits DB       │                             │
│  └─────────────────────────────┘                             │
│                                                              │
│  Tenant C (Free - 300s cache)                                │
│  ┌─────────────────────────────┐                             │
│  │ Key: tenant-C:dashboard     │                             │
│  │ Key: tenant-C:team-members  │  ← Tags: [tenant-C,        │
│  │ Key: tenant-C:projects      │           team-C,           │
│  └─────────────────────────────┘           projects-C]       │
│                                                              │
│  revalidateTag('tenant-A') → Only Tenant A's cache purged   │
└─────────────────────────────────────────────────────────────┘
```

---

## Q14. How do you implement a cache warming strategy for a high-traffic e-commerce site that handles product launches? (Advanced)

**Scenario:** Your store launches 500 new products at midnight. You need those product pages pre-cached before the traffic spike hits. Current behavior: the first visitor to each page experiences a cold cache (3-5 second response).

**Answer:**

```typescript
// scripts/warm-cache.ts
// Run as a cron job or pre-launch script

interface ProductToWarm {
  slug: string;
  priority: 'critical' | 'high' | 'medium';
}

async function warmProductPages() {
  const baseUrl = process.env.SITE_URL!;

  // Fetch products that need warming
  const response = await fetch(`${baseUrl}/api/admin/products-to-warm`, {
    headers: { Authorization: `Bearer ${process.env.ADMIN_API_KEY}` },
  });
  const products: ProductToWarm[] = await response.json();

  // Sort by priority
  const priorityOrder = { critical: 0, high: 1, medium: 2 };
  products.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

  console.log(`Warming ${products.length} product pages...`);

  // Warm in batches to avoid overwhelming the server
  const BATCH_SIZE = 20;
  const BATCH_DELAY_MS = 500;
  let warmed = 0;
  let failed = 0;

  for (let i = 0; i < products.length; i += BATCH_SIZE) {
    const batch = products.slice(i, i + BATCH_SIZE);

    const results = await Promise.allSettled(
      batch.map(async (product) => {
        const url = `${baseUrl}/products/${product.slug}`;
        const start = Date.now();

        const res = await fetch(url, {
          headers: {
            'x-cache-warm': 'true', // Custom header for logging
            'User-Agent': 'CacheWarmer/1.0',
          },
        });

        const duration = Date.now() - start;

        if (!res.ok) throw new Error(`${res.status} for ${url}`);

        return { slug: product.slug, duration, status: res.status };
      })
    );

    for (const result of results) {
      if (result.status === 'fulfilled') {
        warmed++;
        console.log(`  ✓ ${result.value.slug} (${result.value.duration}ms)`);
      } else {
        failed++;
        console.error(`  ✗ ${result.reason}`);
      }
    }

    // Delay between batches
    if (i + BATCH_SIZE < products.length) {
      await new Promise((resolve) => setTimeout(resolve, BATCH_DELAY_MS));
    }
  }

  console.log(`\nCache warming complete: ${warmed} warmed, ${failed} failed`);
}

warmProductPages().catch(console.error);
```

```typescript
// app/api/admin/products-to-warm/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get('authorization');
  if (authHeader !== `Bearer ${process.env.ADMIN_API_KEY}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Get products launching in the next 24 hours
  const upcomingProducts = await db.product.findMany({
    where: {
      launchDate: {
        gte: new Date(),
        lte: new Date(Date.now() + 24 * 60 * 60 * 1000),
      },
      status: 'ACTIVE',
    },
    select: { slug: true, expectedTraffic: true },
    orderBy: { expectedTraffic: 'desc' },
  });

  const productsToWarm = upcomingProducts.map((p) => ({
    slug: p.slug,
    priority: p.expectedTraffic > 10000
      ? 'critical' as const
      : p.expectedTraffic > 1000
        ? 'high' as const
        : 'medium' as const,
  }));

  return NextResponse.json(productsToWarm);
}
```

```typescript
// On-demand warming via Server Action after product creation
// app/actions/product.ts
'use server';

import { revalidateTag } from 'next/cache';

export async function publishProduct(productId: string) {
  // 1. Update product status in DB
  const product = await db.product.update({
    where: { id: productId },
    data: { status: 'ACTIVE', publishedAt: new Date() },
  });

  // 2. Revalidate relevant caches
  revalidateTag('product-listings');
  revalidateTag(`category-${product.categoryId}`);

  // 3. Warm the product page by fetching it
  const siteUrl = process.env.SITE_URL!;
  await fetch(`${siteUrl}/products/${product.slug}`, {
    headers: { 'x-cache-warm': 'true' },
  });

  // 4. Warm related pages
  await Promise.all([
    fetch(`${siteUrl}/categories/${product.categorySlug}`),
    fetch(`${siteUrl}/search?q=${encodeURIComponent(product.name)}`),
  ]);

  return { success: true, slug: product.slug };
}
```

```
┌──────────────────────────────────────────────────────────────┐
│              CACHE WARMING TIMELINE                            │
│                                                               │
│  T-2h    Cron triggers warm-cache.ts                          │
│          ├── Fetches 500 product slugs                        │
│          ├── Batches of 20, 500ms delay between batches       │
│          └── All product pages cached in Data Cache           │
│                                                               │
│  T-0     Product launch! Traffic spike begins                 │
│          ├── All pages served from Full Route Cache            │
│          ├── Response time: ~20ms (cache HIT)                 │
│          └── Zero cold starts for users                       │
│                                                               │
│  T+5m    Time-based revalidation (if configured)              │
│          ├── Stale pages served instantly                      │
│          └── Background revalidation keeps cache fresh         │
│                                                               │
│  WITHOUT WARMING:                                              │
│  T-0     First 500 visitors each trigger cold page generation  │
│          ├── Response time: 3-5 seconds per cold miss          │
│          ├── Database hammered with 500 concurrent queries     │
│          └── Poor user experience at the most critical moment  │
└──────────────────────────────────────────────────────────────┘
```

---

## Q15. How do you implement a stale-while-revalidate pattern with instant fallback for a global CDN-deployed Next.js app? (Advanced)

**Scenario:** Your app is deployed on Vercel's Edge Network across 20+ regions. You need sub-100ms response times globally while keeping data fresh within 60 seconds. Some requests are for data that's never been cached in a particular region.

**Answer:**

```typescript
// lib/cache/swr-strategy.ts
import { unstable_cache } from 'next/cache';
import { cache } from 'react';

interface SWROptions<T> {
  keyParts: string[];
  tags: string[];
  revalidate: number;
  fallback?: T;
  staleWhileError?: boolean;
}

// Creates a cached function with SWR semantics and error fallback
export function createSWRQuery<TArgs extends unknown[], TResult>(
  queryFn: (...args: TArgs) => Promise<TResult>,
  options: SWROptions<TResult>
) {
  const { keyParts, tags, revalidate, fallback, staleWhileError = true } = options;

  // Persistent cache layer
  const persistentCached = (...args: TArgs) =>
    unstable_cache(
      async () => {
        try {
          const result = await queryFn(...args);
          return { data: result, fetchedAt: Date.now(), error: null };
        } catch (error) {
          if (staleWhileError && fallback !== undefined) {
            return {
              data: fallback,
              fetchedAt: Date.now(),
              error: error instanceof Error ? error.message : 'Unknown error',
            };
          }
          throw error;
        }
      },
      [...keyParts, ...args.map(String)],
      { tags, revalidate }
    )();

  // Request dedup layer
  return cache(async (...args: TArgs) => {
    const result = await persistentCached(...args);
    return result;
  });
}
```

```typescript
// lib/api/products.ts
import { createSWRQuery } from '@/lib/cache/swr-strategy';

interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  description: string;
}

// Cached for 60s with SWR behavior
export const getProduct = createSWRQuery(
  async (slug: string): Promise<Product> => {
    const res = await fetch(`${process.env.API_URL}/products/${slug}`, {
      headers: { Authorization: `Bearer ${process.env.API_KEY}` },
    });

    if (!res.ok) throw new Error(`Product API: ${res.status}`);
    return res.json();
  },
  {
    keyParts: ['product'],
    tags: ['products'],
    revalidate: 60,
    staleWhileError: true,
    fallback: undefined,
  }
);

// Product listing with aggressive caching
export const getProductListing = createSWRQuery(
  async (category: string, page: number): Promise<{ products: Product[]; total: number }> => {
    const res = await fetch(
      `${process.env.API_URL}/products?category=${category}&page=${page}`,
      { headers: { Authorization: `Bearer ${process.env.API_KEY}` } }
    );
    if (!res.ok) throw new Error(`Product Listing API: ${res.status}`);
    return res.json();
  },
  {
    keyParts: ['product-listing'],
    tags: ['products', 'product-listings'],
    revalidate: 30,
  }
);
```

```typescript
// app/products/[slug]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { getProduct } from '@/lib/api/products';

// ISR with 60s revalidation for the route itself
export const revalidate = 60;

export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const result = await getProduct(slug);

  if (!result.data) notFound();

  const { data: product, fetchedAt, error } = result;

  return (
    <div>
      {error && (
        <div className="bg-yellow-50 p-2 text-sm text-yellow-800 rounded mb-4">
          Showing cached data. Live data temporarily unavailable.
        </div>
      )}

      <h1 className="text-3xl font-bold">{product.name}</h1>
      <p className="text-2xl mt-2">${product.price}</p>
      <p className="text-gray-600 mt-4">{product.description}</p>

      <Suspense fallback={<StockSkeleton />}>
        <LiveStockIndicator slug={slug} cachedStock={product.stock} />
      </Suspense>

      <p className="text-xs text-gray-400 mt-8">
        Data fetched: {new Date(fetchedAt).toISOString()}
      </p>
    </div>
  );
}
```

```
┌────────────────────────────────────────────────────────────────┐
│                CDN EDGE CACHING FLOW                            │
│                                                                 │
│  User in Tokyo          Vercel Edge (Tokyo)       Origin (US)   │
│  ──────────────         ──────────────────        ───────────   │
│                                                                 │
│  GET /products/shoe                                             │
│       │                                                         │
│       ├─────────► Cache CHECK                                   │
│       │           │                                             │
│       │           ├── HIT (age < 60s)                           │
│       │           │   └──► Return cached (< 20ms) ◄────────    │
│       │           │                                             │
│       │           ├── STALE (age > 60s)                         │
│       │           │   ├──► Return stale (< 20ms) ◄────────     │
│       │           │   └──► Background revalidate ──────► API    │
│       │           │                                             │
│       │           └── MISS (never cached in this region)        │
│       │               └──► Forward to origin ──────────► SSR    │
│       │                                                  │      │
│       │                    Cache response ◄──────────────┘      │
│       ◄────────────────── Return (200-500ms first time)         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Q16. How do you handle cache invalidation in a microservices architecture where data changes originate from multiple services? (Advanced)

**Scenario:** Your Next.js frontend consumes data from 5 microservices: Users, Orders, Inventory, Pricing, and Search. When a product price changes in the Pricing service, the cached product pages, search results, and order history need to be invalidated.

**Answer:**

```typescript
// lib/cache/invalidation-bus.ts
// Central cache invalidation handler that processes events from all services

import { revalidateTag, revalidatePath } from 'next/cache';

// Define the invalidation event schema
interface InvalidationEvent {
  source: 'users' | 'orders' | 'inventory' | 'pricing' | 'search';
  type: string;
  entityId: string;
  metadata?: Record<string, string>;
  timestamp: number;
}

// Mapping of events to cache tags and paths that should be invalidated
const INVALIDATION_MAP: Record<
  string,
  (event: InvalidationEvent) => { tags: string[]; paths: { path: string; type?: 'page' | 'layout' }[] }
> = {
  'pricing:price-updated': (event) => ({
    tags: [
      `product-${event.entityId}`,
      'product-listings',
      'search-results',
      `category-${event.metadata?.categoryId}`,
    ],
    paths: [
      { path: `/products/${event.metadata?.slug}` },
    ],
  }),

  'inventory:stock-changed': (event) => ({
    tags: [
      `product-${event.entityId}`,
      `inventory-${event.entityId}`,
    ],
    paths: [],
  }),

  'users:profile-updated': (event) => ({
    tags: [
      `user-${event.entityId}`,
      `team-${event.metadata?.teamId}`,
    ],
    paths: [
      { path: `/users/${event.entityId}` },
    ],
  }),

  'orders:order-completed': (event) => ({
    tags: [
      `user-orders-${event.metadata?.userId}`,
      `product-${event.metadata?.productId}`,
      'order-analytics',
    ],
    paths: [],
  }),

  'search:index-updated': (event) => ({
    tags: ['search-results'],
    paths: [],
  }),
};

export async function processInvalidationEvent(event: InvalidationEvent): Promise<{
  success: boolean;
  tagsInvalidated: string[];
  pathsInvalidated: string[];
}> {
  const key = `${event.source}:${event.type}`;
  const resolver = INVALIDATION_MAP[key];

  if (!resolver) {
    console.warn(`No invalidation mapping for event: ${key}`);
    return { success: false, tagsInvalidated: [], pathsInvalidated: [] };
  }

  const { tags, paths } = resolver(event);

  // Deduplicate tags
  const uniqueTags = [...new Set(tags.filter(Boolean))];
  const validPaths = paths.filter((p) => p.path);

  // Invalidate all tags
  for (const tag of uniqueTags) {
    revalidateTag(tag);
  }

  // Invalidate all paths
  for (const { path, type } of validPaths) {
    revalidatePath(path, type);
  }

  return {
    success: true,
    tagsInvalidated: uniqueTags,
    pathsInvalidated: validPaths.map((p) => p.path),
  };
}
```

```typescript
// app/api/webhooks/invalidate/route.ts
// Single webhook endpoint for all microservices
import { NextRequest, NextResponse } from 'next/server';
import { processInvalidationEvent } from '@/lib/cache/invalidation-bus';
import { verifyWebhookSignature } from '@/lib/auth/webhook';

// Service-specific secrets for verification
const SERVICE_SECRETS: Record<string, string> = {
  users: process.env.USERS_WEBHOOK_SECRET!,
  orders: process.env.ORDERS_WEBHOOK_SECRET!,
  inventory: process.env.INVENTORY_WEBHOOK_SECRET!,
  pricing: process.env.PRICING_WEBHOOK_SECRET!,
  search: process.env.SEARCH_WEBHOOK_SECRET!,
};

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get('x-webhook-signature')!;
  const source = request.headers.get('x-source-service') as string;

  // Verify webhook authenticity
  const secret = SERVICE_SECRETS[source];
  if (!secret || !verifyWebhookSignature(body, signature, secret)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const events: InvalidationEvent[] = JSON.parse(body);

  // Process all events (some webhooks batch multiple events)
  const results = await Promise.all(
    events.map((event) => processInvalidationEvent(event))
  );

  const summary = {
    processed: results.length,
    succeeded: results.filter((r) => r.success).length,
    tagsInvalidated: [...new Set(results.flatMap((r) => r.tagsInvalidated))],
    pathsInvalidated: [...new Set(results.flatMap((r) => r.pathsInvalidated))],
  };

  console.log('[Cache Invalidation]', JSON.stringify(summary));

  return NextResponse.json(summary);
}
```

```
┌──────────────────────────────────────────────────────────────────┐
│          MICROSERVICES CACHE INVALIDATION FLOW                    │
│                                                                   │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌────────┐ ┌──────┐ │
│  │ Users   │  │  Orders  │  │ Inventory │  │Pricing │ │Search│ │
│  │ Service │  │ Service  │  │  Service  │  │Service │ │Servc │ │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘  └───┬────┘ └──┬───┘ │
│       │            │              │             │         │      │
│       └────────────┴──────────────┴─────────────┴─────────┘      │
│                                   │                              │
│                     Webhook POST /api/webhooks/invalidate        │
│                                   │                              │
│                    ┌──────────────▼───────────────┐               │
│                    │   INVALIDATION BUS           │               │
│                    │                              │               │
│                    │  Event: pricing:price-updated│               │
│                    │  Entity: product-123         │               │
│                    │                              │               │
│                    │  → revalidateTag('product-123')             │
│                    │  → revalidateTag('product-listings')        │
│                    │  → revalidateTag('search-results')          │
│                    │  → revalidatePath('/products/shoe')         │
│                    └──────────────────────────────┘               │
│                                                                   │
│                    Next request → fresh data from all services    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Q17. How do you implement request coalescing and deduplication for database-heavy pages that receive burst traffic? (Advanced)

**Scenario:** Your product page receives 10,000 requests per second during a flash sale. Even with ISR, the revalidation window causes hundreds of concurrent identical database queries during the revalidation moment.

**Answer:**

```typescript
// lib/cache/coalescing.ts
// Request coalescing — multiple concurrent requests for the same data
// share a single in-flight fetch

type InflightRequest<T> = {
  promise: Promise<T>;
  timestamp: number;
};

class RequestCoalescer {
  private inflight = new Map<string, InflightRequest<unknown>>();
  private readonly maxAge: number;

  constructor(maxAgeMs: number = 5000) {
    this.maxAge = maxAgeMs;
  }

  async dedupe<T>(key: string, fn: () => Promise<T>): Promise<T> {
    // Clean up expired entries
    this.cleanup();

    const existing = this.inflight.get(key) as InflightRequest<T> | undefined;

    if (existing) {
      // Another request is already in-flight — piggyback on it
      return existing.promise;
    }

    // Create the promise and store it
    const promise = fn().finally(() => {
      // Remove from inflight after completion + small buffer
      setTimeout(() => this.inflight.delete(key), 100);
    });

    this.inflight.set(key, { promise, timestamp: Date.now() });

    return promise;
  }

  private cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.inflight.entries()) {
      if (now - entry.timestamp > this.maxAge) {
        this.inflight.delete(key);
      }
    }
  }
}

// Singleton for the server process
export const coalescer = new RequestCoalescer(5000);
```

```typescript
// lib/data/products.ts
import { cache } from 'react';
import { unstable_cache } from 'next/cache';
import { coalescer } from '@/lib/cache/coalescing';
import { db } from '@/lib/db';

interface Product {
  id: string;
  slug: string;
  name: string;
  price: number;
  stock: number;
  description: string;
  images: string[];
}

// Layer 1: Request coalescing (prevents duplicate in-flight requests)
// Layer 2: Persistent cache (Data Cache via unstable_cache)
// Layer 3: Request dedup (React cache for same render tree)

export const getProduct = cache(async (slug: string): Promise<Product | null> => {
  // unstable_cache for persistent Data Cache
  const cachedFetch = unstable_cache(
    async () => {
      // Request coalescing for concurrent revalidations
      return coalescer.dedupe(`product:${slug}`, async () => {
        console.log(`[DB QUERY] Fetching product: ${slug}`);

        const product = await db.product.findUnique({
          where: { slug, status: 'ACTIVE' },
          include: {
            images: { orderBy: { position: 'asc' } },
            variants: { where: { inStock: true } },
            category: true,
          },
        });

        return product;
      });
    },
    [`product-${slug}`],
    {
      tags: [`product-${slug}`, 'products'],
      revalidate: 60,
    }
  );

  return cachedFetch();
});
```

```typescript
// lib/cache/batch-loader.ts
// For scenarios where many product IDs need to be fetched

export class BatchLoader<K, V> {
  private batch: Map<K, { resolve: (v: V | null) => void; reject: (e: Error) => void }[]> =
    new Map();
  private timer: ReturnType<typeof setTimeout> | null = null;
  private readonly batchFn: (keys: K[]) => Promise<Map<K, V>>;
  private readonly maxBatchSize: number;
  private readonly delayMs: number;

  constructor(
    batchFn: (keys: K[]) => Promise<Map<K, V>>,
    options: { maxBatchSize?: number; delayMs?: number } = {}
  ) {
    this.batchFn = batchFn;
    this.maxBatchSize = options.maxBatchSize ?? 100;
    this.delayMs = options.delayMs ?? 10;
  }

  async load(key: K): Promise<V | null> {
    return new Promise((resolve, reject) => {
      if (!this.batch.has(key)) {
        this.batch.set(key, []);
      }
      this.batch.get(key)!.push({ resolve, reject });

      if (this.batch.size >= this.maxBatchSize) {
        this.dispatch();
      } else if (!this.timer) {
        this.timer = setTimeout(() => this.dispatch(), this.delayMs);
      }
    });
  }

  private async dispatch() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    const currentBatch = new Map(this.batch);
    this.batch.clear();

    const keys = [...currentBatch.keys()];

    try {
      const results = await this.batchFn(keys);

      for (const [key, callbacks] of currentBatch) {
        const value = results.get(key) ?? null;
        for (const cb of callbacks) {
          cb.resolve(value);
        }
      }
    } catch (error) {
      for (const callbacks of currentBatch.values()) {
        for (const cb of callbacks) {
          cb.reject(error as Error);
        }
      }
    }
  }
}

// Usage: batch product lookups
export const productBatchLoader = new BatchLoader(
  async (ids: string[]) => {
    const products = await db.product.findMany({
      where: { id: { in: ids } },
    });
    return new Map(products.map((p) => [p.id, p]));
  },
  { maxBatchSize: 50, delayMs: 5 }
);
```

```
┌─────────────────────────────────────────────────────────────┐
│         REQUEST COALESCING DURING REVALIDATION               │
│                                                              │
│  Without Coalescing (revalidation at T=60s):                 │
│                                                              │
│  Request A ──► DB Query ──► Response                         │
│  Request B ──► DB Query ──► Response     ← 500 concurrent   │
│  Request C ──► DB Query ──► Response        DB queries!      │
│  ...                                                         │
│  Request N ──► DB Query ──► Response                         │
│                                                              │
│  With Coalescing:                                            │
│                                                              │
│  Request A ──┐                                               │
│  Request B ──┤                                               │
│  Request C ──┼──► SINGLE DB Query ──► Response to ALL        │
│  ...         │                                               │
│  Request N ──┘    ← 1 query, shared result!                  │
│                                                              │
│  DB load: 500x → 1x reduction                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Q18. How do you implement cache analytics and monitoring to identify cache performance issues in production? (Advanced)

**Scenario:** Your production app has degraded performance. You suspect caching issues but have no visibility into cache hit rates, miss rates, or stale data frequency. You need to build observability into your caching layer.

**Answer:**

```typescript
// lib/cache/instrumented-fetch.ts
// Monkey-patch fetch to instrument caching metrics

interface CacheMetric {
  url: string;
  method: string;
  cacheStatus: 'HIT' | 'MISS' | 'STALE' | 'BYPASS' | 'UNKNOWN';
  duration: number;
  tags: string[];
  revalidate?: number;
  timestamp: number;
  route: string;
}

class CacheMetricsCollector {
  private metrics: CacheMetric[] = [];
  private flushInterval: ReturnType<typeof setInterval> | null = null;

  constructor() {
    // Flush metrics every 30 seconds
    if (typeof setInterval !== 'undefined') {
      this.flushInterval = setInterval(() => this.flush(), 30000);
    }
  }

  record(metric: CacheMetric) {
    this.metrics.push(metric);

    // Flush immediately if buffer is large
    if (this.metrics.length >= 100) {
      this.flush();
    }
  }

  private async flush() {
    if (this.metrics.length === 0) return;

    const batch = this.metrics.splice(0);

    // Compute aggregates
    const summary = {
      total: batch.length,
      hits: batch.filter((m) => m.cacheStatus === 'HIT').length,
      misses: batch.filter((m) => m.cacheStatus === 'MISS').length,
      stale: batch.filter((m) => m.cacheStatus === 'STALE').length,
      bypasses: batch.filter((m) => m.cacheStatus === 'BYPASS').length,
      avgDuration: batch.reduce((sum, m) => sum + m.duration, 0) / batch.length,
      p95Duration: this.percentile(batch.map((m) => m.duration), 95),
      slowestFetches: batch
        .sort((a, b) => b.duration - a.duration)
        .slice(0, 5)
        .map((m) => ({ url: m.url, duration: m.duration, cache: m.cacheStatus })),
      hitRate: 0,
    };

    summary.hitRate = summary.total > 0
      ? ((summary.hits + summary.stale) / summary.total) * 100
      : 0;

    // Send to your analytics service
    try {
      await fetch(process.env.METRICS_ENDPOINT!, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'cache-metrics',
          ...summary,
          window: '30s',
          timestamp: Date.now(),
        }),
      });
    } catch (error) {
      console.error('[Cache Metrics] Failed to flush:', error);
    }
  }

  private percentile(values: number[], p: number): number {
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[index] ?? 0;
  }
}

export const cacheMetrics = new CacheMetricsCollector();
```

```typescript
// lib/cache/monitored-fetcher.ts
import { cacheMetrics } from './instrumented-fetch';
import { headers } from 'next/headers';

interface MonitoredFetchOptions extends RequestInit {
  next?: {
    revalidate?: number;
    tags?: string[];
  };
}

export async function monitoredFetch(
  url: string,
  options: MonitoredFetchOptions = {}
): Promise<Response> {
  const start = Date.now();

  // Determine expected cache behavior
  const isCached = options.cache === 'force-cache' ||
    (options.next?.revalidate !== undefined && options.next.revalidate > 0);

  const response = await fetch(url, options);

  const duration = Date.now() - start;

  // Infer cache status from response headers and timing
  const cacheControl = response.headers.get('x-cache') ||
    response.headers.get('cf-cache-status') ||
    response.headers.get('x-vercel-cache');

  let cacheStatus: 'HIT' | 'MISS' | 'STALE' | 'BYPASS' | 'UNKNOWN';

  if (cacheControl) {
    cacheStatus = cacheControl.toUpperCase() as typeof cacheStatus;
  } else if (options.cache === 'no-store') {
    cacheStatus = 'BYPASS';
  } else if (isCached && duration < 10) {
    cacheStatus = 'HIT'; // Heuristic: < 10ms likely a cache hit
  } else if (isCached) {
    cacheStatus = 'MISS';
  } else {
    cacheStatus = 'UNKNOWN';
  }

  // Get current route for grouping
  let route = 'unknown';
  try {
    const headersList = await headers();
    route = headersList.get('x-next-url') || 'unknown';
  } catch {
    // headers() not available outside request context
  }

  cacheMetrics.record({
    url: new URL(url).pathname,
    method: options.method || 'GET',
    cacheStatus,
    duration,
    tags: options.next?.tags || [],
    revalidate: options.next?.revalidate,
    timestamp: Date.now(),
    route,
  });

  return response;
}
```

```typescript
// app/api/admin/cache-stats/route.ts
// Dashboard API for viewing cache performance
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  // Query aggregated metrics from your metrics store
  const stats = await db.$queryRaw`
    SELECT
      route,
      COUNT(*) as total_requests,
      SUM(CASE WHEN cache_status = 'HIT' THEN 1 ELSE 0 END) as cache_hits,
      SUM(CASE WHEN cache_status = 'MISS' THEN 1 ELSE 0 END) as cache_misses,
      AVG(duration_ms) as avg_duration,
      PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration,
      ROUND(
        SUM(CASE WHEN cache_status = 'HIT' THEN 1 ELSE 0 END)::numeric /
        NULLIF(COUNT(*), 0) * 100, 2
      ) as hit_rate_pct
    FROM cache_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour'
    GROUP BY route
    ORDER BY total_requests DESC
    LIMIT 50
  `;

  return NextResponse.json({ stats, generatedAt: new Date().toISOString() });
}
```

```
┌──────────────────────────────────────────────────────────┐
│            CACHE METRICS DASHBOARD                        │
│                                                           │
│  Route              Requests  Hit Rate  Avg(ms)  P95(ms) │
│  ─────────────────  ────────  ────────  ───────  ─────── │
│  /products/[slug]   45,230    94.2%     12ms     45ms    │
│  /                  12,100    99.1%     8ms      15ms    │
│  /search            8,450     72.3%     89ms     340ms   │ ← Low hit rate!
│  /dashboard         3,200     45.1%     210ms    890ms   │ ← Investigate
│  /api/cart          15,800    0.0%      45ms     120ms   │ ← Expected (no-store)
│                                                           │
│  ALERTS:                                                  │
│  ⚠ /search hit rate dropped below 80% threshold          │
│  ⚠ /dashboard P95 latency exceeds 500ms                  │
└──────────────────────────────────────────────────────────┘
```

---

## Q19. How do you implement a distributed cache invalidation pattern for a Next.js app running across multiple serverless instances? (Advanced)

**Scenario:** Your Next.js app runs on 50+ serverless function instances. When you call `revalidateTag()`, it only invalidates the cache on the instance that processes the request. Other instances continue serving stale data until their individual caches expire.

**Answer:**

```typescript
// lib/cache/distributed-invalidation.ts
// Uses a message broker (Redis Pub/Sub, AWS SNS, etc.) to broadcast
// invalidation events across all instances

import { revalidateTag, revalidatePath } from 'next/cache';
import Redis from 'ioredis';

const CHANNEL = 'cache-invalidation';

interface InvalidationMessage {
  type: 'tag' | 'path';
  value: string;
  pathType?: 'page' | 'layout';
  sourceInstanceId: string;
  timestamp: number;
}

class DistributedCacheInvalidator {
  private publisher: Redis;
  private subscriber: Redis;
  private instanceId: string;
  private processed = new Set<string>();

  constructor() {
    this.instanceId = `${process.env.VERCEL_REGION || 'local'}-${crypto.randomUUID().slice(0, 8)}`;
    this.publisher = new Redis(process.env.REDIS_URL!);
    this.subscriber = new Redis(process.env.REDIS_URL!);

    this.setupSubscriber();
  }

  private setupSubscriber() {
    this.subscriber.subscribe(CHANNEL);

    this.subscriber.on('message', (_channel: string, message: string) => {
      const event: InvalidationMessage = JSON.parse(message);

      // Skip messages from this instance (already invalidated locally)
      if (event.sourceInstanceId === this.instanceId) return;

      // Deduplicate using message ID
      const messageId = `${event.type}:${event.value}:${event.timestamp}`;
      if (this.processed.has(messageId)) return;
      this.processed.add(messageId);

      // Clean up old message IDs (prevent memory leak)
      if (this.processed.size > 10000) {
        const entries = [...this.processed];
        this.processed = new Set(entries.slice(-5000));
      }

      // Apply invalidation locally
      if (event.type === 'tag') {
        revalidateTag(event.value);
      } else if (event.type === 'path') {
        revalidatePath(event.value, event.pathType);
      }

      console.log(
        `[Cache] Instance ${this.instanceId} invalidated ${event.type}: ${event.value} (from ${event.sourceInstanceId})`
      );
    });
  }

  // Call these instead of revalidateTag/revalidatePath directly
  async invalidateTag(tag: string) {
    // Invalidate locally first
    revalidateTag(tag);

    // Broadcast to all instances
    const message: InvalidationMessage = {
      type: 'tag',
      value: tag,
      sourceInstanceId: this.instanceId,
      timestamp: Date.now(),
    };

    await this.publisher.publish(CHANNEL, JSON.stringify(message));
  }

  async invalidatePath(path: string, type?: 'page' | 'layout') {
    revalidatePath(path, type);

    const message: InvalidationMessage = {
      type: 'path',
      value: path,
      pathType: type,
      sourceInstanceId: this.instanceId,
      timestamp: Date.now(),
    };

    await this.publisher.publish(CHANNEL, JSON.stringify(message));
  }

  // Batch invalidation for efficiency
  async invalidateBatch(
    operations: Array<
      { type: 'tag'; value: string } | { type: 'path'; value: string; pathType?: 'page' | 'layout' }
    >
  ) {
    const pipeline = this.publisher.pipeline();

    for (const op of operations) {
      if (op.type === 'tag') {
        revalidateTag(op.value);
      } else {
        revalidatePath(op.value, op.pathType);
      }

      const message: InvalidationMessage = {
        type: op.type,
        value: op.value,
        pathType: op.type === 'path' ? op.pathType : undefined,
        sourceInstanceId: this.instanceId,
        timestamp: Date.now(),
      };

      pipeline.publish(CHANNEL, JSON.stringify(message));
    }

    await pipeline.exec();
  }
}

// Singleton
let invalidator: DistributedCacheInvalidator | null = null;

export function getInvalidator(): DistributedCacheInvalidator {
  if (!invalidator) {
    invalidator = new DistributedCacheInvalidator();
  }
  return invalidator;
}
```

```typescript
// Usage in Server Actions
// app/actions/product.ts
'use server';

import { getInvalidator } from '@/lib/cache/distributed-invalidation';
import { db } from '@/lib/db';

export async function updateProductPrice(productId: string, newPrice: number) {
  const product = await db.product.update({
    where: { id: productId },
    data: { price: newPrice },
  });

  const invalidator = getInvalidator();

  // Broadcast invalidation across all instances
  await invalidator.invalidateBatch([
    { type: 'tag', value: `product-${productId}` },
    { type: 'tag', value: 'product-listings' },
    { type: 'path', value: `/products/${product.slug}` },
  ]);

  return { success: true };
}
```

```
┌──────────────────────────────────────────────────────────────────┐
│        DISTRIBUTED CACHE INVALIDATION                             │
│                                                                   │
│  Instance A (us-east-1)    Redis Pub/Sub    Instance B (eu-west)  │
│  ─────────────────────     ──────────────   ────────────────────  │
│                                                                   │
│  updateProductPrice()                                             │
│       │                                                           │
│       ├─► revalidateTag('product-123')  [LOCAL]                   │
│       │                                                           │
│       └─► PUBLISH 'cache-invalidation'                            │
│                    │                                              │
│                    ├──────────────────────► SUBSCRIBE             │
│                    │                        │                     │
│                    │                        └─► revalidateTag     │
│                    │                            ('product-123')   │
│                    │                                              │
│                    │   Instance C (ap-southeast)                  │
│                    │   ─────────────────────────                  │
│                    └──────────────────────► SUBSCRIBE             │
│                                             │                     │
│                                             └─► revalidateTag    │
│                                                 ('product-123')  │
│                                                                   │
│  Result: ALL instances have consistent cache within ~50ms         │
└──────────────────────────────────────────────────────────────────┘
```

**Alternative: Vercel's built-in solution**

On Vercel, `revalidateTag()` and `revalidatePath()` work globally across all instances because the Data Cache is centralized. The distributed pattern above is needed for self-hosted deployments or non-Vercel platforms.

```typescript
// next.config.ts for self-hosted with shared cache
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  cacheHandler: require.resolve('./lib/cache/custom-cache-handler.js'),
  cacheMaxMemorySize: 0, // Disable in-memory cache, use external store
};

export default nextConfig;
```

---

## Q20. How do you design a cache strategy for a real-time collaborative document editor that needs to balance freshness, performance, and consistency? (Advanced)

**Scenario:** You're building a Notion-like app where documents are collaboratively edited. The document view page needs:
- Instant load for the viewer (cached)
- Near-real-time updates when collaborators make changes
- Full content for SEO (server-rendered)
- Offline support for previously viewed documents

**Answer:**

```typescript
// lib/cache/collaborative-cache.ts
// Multi-layer caching strategy for collaborative documents

import { unstable_cache } from 'next/cache';
import { cache } from 'react';
import { db } from '@/lib/db';

interface Document {
  id: string;
  title: string;
  content: string; // Serialized block content
  version: number;
  lastEditedBy: string;
  updatedAt: Date;
  collaborators: { id: string; name: string; avatarUrl: string }[];
}

// Layer 1: Server-side cached document (for initial page load / SEO)
export const getCachedDocument = cache(async (docId: string) => {
  const fetchDoc = unstable_cache(
    async () => {
      const doc = await db.document.findUnique({
        where: { id: docId },
        include: {
          collaborators: {
            select: { id: true, name: true, avatarUrl: true },
          },
        },
      });
      return doc;
    },
    [`doc-${docId}`],
    {
      tags: [`doc-${docId}`, 'documents'],
      revalidate: 30, // Short TTL — document edits are frequent
    }
  );

  return fetchDoc();
});

// Layer 2: Document version check endpoint (lightweight)
// Used by the client to check if their cached version is stale
export const getDocumentVersion = cache(async (docId: string) => {
  return db.document.findUnique({
    where: { id: docId },
    select: { version: true, updatedAt: true },
  });
});
```

```typescript
// app/docs/[docId]/page.tsx
import { Suspense } from 'react';
import { getCachedDocument } from '@/lib/cache/collaborative-cache';
import { notFound } from 'next/navigation';

// Short revalidation for collaborative content
export const revalidate = 30;

export default async function DocumentPage({
  params,
}: {
  params: Promise<{ docId: string }>;
}) {
  const { docId } = await params;
  const doc = await getCachedDocument(docId);

  if (!doc) notFound();

  return (
    <div className="max-w-4xl mx-auto">
      {/* Server-rendered content for SEO and initial paint */}
      <article>
        <h1 className="text-3xl font-bold mb-4">{doc.title}</h1>
        <DocumentRenderer content={doc.content} />
      </article>

      {/* Client component for real-time collaboration */}
      <Suspense fallback={null}>
        <CollaborativeEditor
          docId={docId}
          initialContent={doc.content}
          initialVersion={doc.version}
        />
      </Suspense>

      {/* Presence indicators for active collaborators */}
      <Suspense fallback={null}>
        <PresenceIndicator docId={docId} collaborators={doc.collaborators} />
      </Suspense>
    </div>
  );
}
```

```typescript
// components/collaborative-editor.tsx
'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useOptimistic } from 'react';

interface CollaborativeEditorProps {
  docId: string;
  initialContent: string;
  initialVersion: number;
}

export function CollaborativeEditor({
  docId,
  initialContent,
  initialVersion,
}: CollaborativeEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [version, setVersion] = useState(initialVersion);
  const [isStale, setIsStale] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Optimistic content updates
  const [optimisticContent, addOptimisticUpdate] = useOptimistic(
    content,
    (currentContent: string, update: { type: string; payload: string }) => {
      if (update.type === 'insert') return currentContent + update.payload;
      return update.payload;
    }
  );

  // WebSocket connection for real-time sync
  useEffect(() => {
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/docs/${docId}?version=${version}`
    );

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'document-update':
          setContent(message.content);
          setVersion(message.version);
          setIsStale(false);
          break;

        case 'version-check':
          if (message.version > version) {
            setIsStale(true);
          }
          break;

        case 'cursor-update':
          // Handle collaborator cursor positions
          break;
      }
    };

    wsRef.current = ws;

    return () => ws.close();
  }, [docId, version]);

  // Service Worker registration for offline support
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        // Cache document content for offline access
        cacheDocumentLocally(docId, optimisticContent, version);
      });
    }
  }, [docId, optimisticContent, version]);

  const handleEdit = useCallback(
    async (newContent: string) => {
      // Optimistic update
      addOptimisticUpdate({ type: 'replace', payload: newContent });

      // Send update via WebSocket for real-time sync
      wsRef.current?.send(
        JSON.stringify({
          type: 'edit',
          content: newContent,
          version: version + 1,
        })
      );

      // Persist via Server Action
      const result = await saveDocument(docId, newContent, version);
      if (result.conflict) {
        // Handle conflict resolution
        setContent(result.mergedContent);
        setVersion(result.newVersion);
      }
    },
    [docId, version, addOptimisticUpdate]
  );

  return (
    <div>
      {isStale && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mb-4 text-sm">
          This document has been updated by a collaborator.
          <button
            onClick={() => window.location.reload()}
            className="ml-2 text-yellow-800 underline"
          >
            Refresh
          </button>
        </div>
      )}
      <Editor content={optimisticContent} onChange={handleEdit} />
    </div>
  );
}

async function cacheDocumentLocally(
  docId: string,
  content: string,
  version: number
) {
  const cache = await caches.open('documents-v1');
  const response = new Response(JSON.stringify({ content, version, cachedAt: Date.now() }));
  await cache.put(`/api/docs/${docId}/offline`, response);
}
```

```typescript
// app/actions/document.ts
'use server';

import { revalidateTag } from 'next/cache';
import { db } from '@/lib/db';

export async function saveDocument(
  docId: string,
  content: string,
  expectedVersion: number
) {
  // Optimistic concurrency control
  const current = await db.document.findUnique({
    where: { id: docId },
    select: { version: true, content: true },
  });

  if (!current) throw new Error('Document not found');

  if (current.version !== expectedVersion) {
    // Version conflict — merge changes
    const mergedContent = await mergeDocumentChanges(
      current.content,
      content,
      expectedVersion
    );

    const updated = await db.document.update({
      where: { id: docId },
      data: {
        content: mergedContent,
        version: { increment: 1 },
        updatedAt: new Date(),
      },
    });

    revalidateTag(`doc-${docId}`);

    return {
      conflict: true,
      mergedContent,
      newVersion: updated.version,
    };
  }

  // No conflict — direct update
  const updated = await db.document.update({
    where: { id: docId },
    data: {
      content,
      version: { increment: 1 },
      updatedAt: new Date(),
    },
  });

  revalidateTag(`doc-${docId}`);

  return {
    conflict: false,
    mergedContent: content,
    newVersion: updated.version,
  };
}

async function mergeDocumentChanges(
  serverContent: string,
  clientContent: string,
  _baseVersion: number
): Promise<string> {
  // In production, use a proper CRDT or OT library
  // This is a simplified last-write-wins merge
  return clientContent;
}
```

```
┌──────────────────────────────────────────────────────────────────┐
│       COLLABORATIVE DOCUMENT CACHING ARCHITECTURE                 │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  LAYER 4: Service Worker Cache (offline-first)               │ │
│  │  ├── Caches rendered documents for offline access            │ │
│  │  └── Serves stale content when offline, syncs when online   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  LAYER 3: WebSocket Real-time Layer                          │ │
│  │  ├── Pushes live edits to all connected collaborators        │ │
│  │  ├── Cursor presence (who's editing where)                  │ │
│  │  └── Bypasses HTTP caching entirely for real-time data       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  LAYER 2: Next.js Data Cache (server-side, 30s TTL)         │ │
│  │  ├── Serves cached document for initial page load            │ │
│  │  ├── SEO-friendly server-rendered content                    │ │
│  │  └── Invalidated via revalidateTag on save                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  LAYER 1: Database (source of truth)                         │ │
│  │  ├── Version tracking for conflict resolution                │ │
│  │  ├── Full document history                                   │ │
│  │  └── Optimistic concurrency control                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  USER EXPERIENCE:                                                 │
│  1. First visit: Server-rendered page (from cache or fresh)       │
│  2. Client hydrates: WebSocket connects, real-time editing begins│
│  3. Collaborator edits: Pushed via WS, optimistic UI update      │
│  4. Page reload: Fresh server-rendered content + WS reconnect     │
│  5. Offline: Service Worker serves cached version                 │
└──────────────────────────────────────────────────────────────────┘
```

---

*End of Data Fetching & Caching Strategies — 20 Questions*
