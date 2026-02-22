# 18. Next.js Caching — Deep Dive

## Topic Introduction

Caching in Next.js is one of the most critical performance topics for senior developers. Next.js has **four distinct caching layers**, each operating at a different level of the request lifecycle. Understanding how they interact — and how to invalidate them — is essential for building fast, correct production applications.

### The Four Caching Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  4. Router Cache                                          │ │
│  │     In-memory cache of RSC payloads                       │ │
│  │     Duration: Session (dynamic) / 5 min (static)          │ │
│  │     Scope: Client-side navigation only                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (on cache miss or revalidation)
┌─────────────────────────────────────────────────────────────────┐
│                        SERVER (Next.js)                         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  1. Request Memoization (React cache)                     │ │
│  │     Deduplicates identical fetch calls in a single render │ │
│  │     Duration: Single request/render lifecycle             │ │
│  │     Scope: Server Components in the same render tree      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  2. Data Cache                                            │ │
│  │     Persistent cache of fetch() results                   │ │
│  │     Duration: Until revalidated                           │ │
│  │     Scope: Across requests and deployments                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  3. Full Route Cache                                      │ │
│  │     Pre-rendered HTML + RSC payload at build time         │ │
│  │     Duration: Until revalidated                           │ │
│  │     Scope: Static routes only                             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Next.js 15 Caching Defaults (BREAKING CHANGE)

In Next.js 14, `fetch()` was cached by default. **In Next.js 15, nothing is cached by default**. This is a major breaking change:

| Behavior | Next.js 14 | Next.js 15 |
|----------|-----------|-----------|
| `fetch()` | Cached by default (`force-cache`) | **Not cached** (`no-store`) |
| Route Handlers (GET) | Cached by default | **Not cached** |
| Client Router Cache | 5 min for static, 30s for dynamic | **0 seconds** (no client cache) |

```tsx
// Next.js 14: This was cached automatically
const data = await fetch('https://api.example.com/posts');

// Next.js 15: Same call is NOT cached — fetches every time
const data = await fetch('https://api.example.com/posts');

// Next.js 15: To opt INTO caching, you must be explicit
const data = await fetch('https://api.example.com/posts', {
  cache: 'force-cache',           // Opt into Data Cache
  next: { revalidate: 3600 },     // Or use ISR with revalidation
});
```

**Why this matters for senior developers**: The caching defaults change means many Next.js 14 apps will see **performance regressions** when upgrading to Next.js 15 without explicitly opting into caching. You need to audit every `fetch()` call and decide its caching strategy.

---

## Q1. (Beginner) What are the four caching layers in Next.js, and what does each one cache?

**Scenario**: A junior developer asks why their API data sometimes seems stale and sometimes seems fresh. You need to explain the entire caching architecture.

**Answer**:

Next.js has four caching mechanisms, each at a different layer:

**Layer 1: Request Memoization**

```
What: Deduplicates identical fetch() calls within a SINGLE render
Where: Server-side only (during RSC rendering)
Duration: One request/render cycle
Key: fetch() URL + options

Example: If Layout and Page both call fetch('/api/user'),
         only ONE actual HTTP request is made.

┌─────────────────────────────────────────┐
│  Single Page Render                     │
│                                         │
│  Layout: fetch('/api/user') ──┐         │
│                                ├→ 1 HTTP │
│  Page:   fetch('/api/user') ──┘   call  │
│                                         │
│  Component: fetch('/api/posts') → 1 HTTP│
└─────────────────────────────────────────┘
```

```tsx
// Both components share one fetch automatically
// app/layout.tsx
export default async function Layout({ children }) {
  const user = await fetch('https://api.example.com/user'); // Request #1
  return <div>{children}</div>;
}

// app/page.tsx
export default async function Page() {
  const user = await fetch('https://api.example.com/user'); // DEDUPLICATED — no new request!
  return <div>{user.name}</div>;
}
```

**Layer 2: Data Cache**

```
What: Persistent cache of fetch() results on the server
Where: Server-side, persists across requests and deployments
Duration: Indefinite (until revalidated)
Key: fetch() URL + options

┌────────────┐    ┌────────────┐    ┌────────────┐
│  Request 1  │    │  Request 2  │    │  Request 3  │
│  (User A)   │    │  (User B)   │    │  (User A)   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
  ┌──────────────────────────────────────────────┐
  │              Data Cache                       │
  │  /api/posts → { data: [...], exp: ... }      │
  │  /api/user  → { data: {...}, exp: ... }      │
  └──────────────────────────────────────────────┘
```

**Layer 3: Full Route Cache**

```
What: Pre-rendered HTML + RSC Payload at build time
Where: Server-side
Duration: Until revalidated
Applies to: Static routes only (no dynamic functions like cookies(), headers())

Build Time:
  /about   → about.html + about.rsc   (cached)
  /blog/1  → blog-1.html + blog-1.rsc (cached)
  /dashboard → NOT cached (uses cookies() — dynamic)
```

**Layer 4: Router Cache**

```
What: Client-side in-memory cache of visited routes (RSC payloads)
Where: Browser memory
Duration (Next.js 15): 0 seconds by default (configurable)
Purpose: Instant back/forward navigation

User visits /about → cached in browser
User visits /blog  → cached in browser
User clicks back   → /about served from Router Cache (instant!)
```

**Summary table**:

| Layer | What | Where | Duration | Invalidation |
|-------|------|-------|----------|-------------|
| Request Memoization | `fetch()` dedup | Server (per render) | 1 request | Automatic |
| Data Cache | `fetch()` results | Server (persistent) | Until revalidated | `revalidateTag`, `revalidatePath` |
| Full Route Cache | HTML + RSC | Server (build time) | Until revalidated | Redeploy, revalidation |
| Router Cache | RSC Payload | Client (memory) | Session / configurable | `router.refresh()`, revalidation |

---

## Q2. (Beginner) How did Next.js 15 change the default caching behavior, and what do you need to update?

**Scenario**: You're upgrading from Next.js 14 to 15. After the upgrade, pages that were fast are now slow because data is being fetched on every request.

**Answer**:

Next.js 15 made a **philosophy shift**: from "cached by default, opt out" to "uncached by default, opt in." This matches how most developers expect caching to work.

**What changed**:

```tsx
// ═══════════════════════════════════════════════════════
// FETCH BEHAVIOR
// ═══════════════════════════════════════════════════════

// Next.js 14 (implicit caching)
await fetch('https://api.example.com/data');
// ↑ Equivalent to: cache: 'force-cache'
// ↑ Result stored in Data Cache indefinitely

// Next.js 15 (no implicit caching)
await fetch('https://api.example.com/data');
// ↑ Equivalent to: cache: 'no-store'
// ↑ Fresh fetch on EVERY request


// ═══════════════════════════════════════════════════════
// ROUTE HANDLERS
// ═══════════════════════════════════════════════════════

// Next.js 14: GET route handlers were cached at build time
export async function GET() {
  const data = await db.query('SELECT * FROM posts');
  return Response.json(data);
  // ↑ Cached at build time, returned from cache on every request
}

// Next.js 15: GET route handlers are dynamic by default
export async function GET() {
  const data = await db.query('SELECT * FROM posts');
  return Response.json(data);
  // ↑ Runs on EVERY request (dynamic by default)
}


// ═══════════════════════════════════════════════════════
// ROUTER CACHE (client-side)
// ═══════════════════════════════════════════════════════

// Next.js 14:
// - Static pages: cached for 5 minutes
// - Dynamic pages: cached for 30 seconds

// Next.js 15:
// - Default stale time: 0 seconds
// - Pages are not cached on client by default
```

**Migration checklist — adding explicit caching**:

```tsx
// Step 1: Audit all fetch() calls and add caching where appropriate

// Static data that rarely changes — use force-cache
const config = await fetch('https://api.example.com/site-config', {
  cache: 'force-cache',
});

// Data that changes periodically — use ISR
const posts = await fetch('https://api.example.com/posts', {
  next: { revalidate: 60 }, // Revalidate every 60 seconds
});

// Data that must be fresh — leave as default (no cache)
const cartItems = await fetch('https://api.example.com/cart');

// Data that should be cached and invalidated on-demand
const products = await fetch('https://api.example.com/products', {
  next: { tags: ['products'] }, // Tag-based invalidation
});
```

```tsx
// Step 2: Configure Router Cache if needed
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    staleTimes: {
      dynamic: 30,  // Cache dynamic pages for 30s on client
      static: 180,  // Cache static pages for 3 min on client
    },
  },
};

export default nextConfig;
```

```tsx
// Step 3: Make Route Handlers explicitly static if needed
// app/api/config/route.ts
export const dynamic = 'force-static'; // Opt into static caching
export const revalidate = 3600;        // Revalidate every hour

export async function GET() {
  const config = await getAppConfig();
  return Response.json(config);
}
```

---

## Q3. (Beginner) What is the difference between `revalidateTag` and `revalidatePath`? When do you use each?

**Scenario**: You have a blog where authors can publish and edit posts. You need to invalidate caches when content changes.

**Answer**:

Both functions trigger **on-demand cache invalidation**, but they target different things:

```
revalidatePath('/blog')
  → Invalidates the Full Route Cache for /blog
  → Re-renders the page on next request
  → Also invalidates Data Cache entries used by that path

revalidateTag('posts')
  → Invalidates ALL Data Cache entries tagged with 'posts'
  → Any route that used tagged data will re-fetch on next request
  → More granular than path-based invalidation
```

**Visual comparison**:

```
revalidatePath('/blog'):
┌─────────────────────────────────────────┐
│  Invalidates everything at /blog         │
│                                         │
│  /blog page.tsx  ← RE-RENDERED          │
│    ├── fetch('/api/posts') ← RE-FETCHED │
│    ├── fetch('/api/author') ← RE-FETCHED│
│    └── fetch('/api/ads') ← RE-FETCHED   │
│                                         │
│  /blog/[slug] pages ← NOT affected      │
└─────────────────────────────────────────┘

revalidateTag('posts'):
┌─────────────────────────────────────────┐
│  Invalidates all fetches tagged 'posts' │
│                                         │
│  /blog page.tsx                         │
│    ├── fetch('/api/posts',              │
│    │   { next: { tags: ['posts'] } })   │
│    │   ← RE-FETCHED ✓                  │
│    ├── fetch('/api/author') ← NOT       │
│    │   affected (no tag)                │
│    └── fetch('/api/ads') ← NOT affected │
│                                         │
│  /blog/[slug] page.tsx                  │
│    └── fetch('/api/posts/[slug]',       │
│        { next: { tags: ['posts'] } })   │
│        ← ALSO RE-FETCHED ✓             │
│                                         │
│  /home page.tsx                         │
│    └── fetch('/api/featured-posts',     │
│        { next: { tags: ['posts'] } })   │
│        ← ALSO RE-FETCHED ✓             │
└─────────────────────────────────────────┘
```

**Production example — Blog CMS**:

```tsx
// lib/api.ts — Tag your fetches
export async function getPosts() {
  const res = await fetch('https://cms.example.com/api/posts', {
    next: { tags: ['posts'] },
  });
  return res.json();
}

export async function getPost(slug: string) {
  const res = await fetch(`https://cms.example.com/api/posts/${slug}`, {
    next: { tags: ['posts', `post-${slug}`] },
  });
  return res.json();
}

export async function getAuthor(id: string) {
  const res = await fetch(`https://cms.example.com/api/authors/${id}`, {
    next: { tags: ['authors', `author-${id}`] },
  });
  return res.json();
}
```

```tsx
// app/api/cms-webhook/route.ts — CMS sends webhook on content change
import { revalidateTag, revalidatePath } from 'next/cache';
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const secret = request.headers.get('x-webhook-secret');

  if (secret !== process.env.CMS_WEBHOOK_SECRET) {
    return new Response('Unauthorized', { status: 401 });
  }

  switch (body.event) {
    case 'post.published':
    case 'post.updated':
      // Invalidate the specific post AND the post list
      revalidateTag(`post-${body.data.slug}`);
      revalidateTag('posts');
      break;

    case 'post.deleted':
      revalidateTag('posts');
      revalidatePath('/blog'); // Also invalidate the blog index page
      break;

    case 'author.updated':
      revalidateTag(`author-${body.data.id}`);
      break;

    case 'site.settings.updated':
      // Nuclear option — invalidate everything
      revalidatePath('/', 'layout');
      break;
  }

  return Response.json({ revalidated: true });
}
```

**Decision guide**:

| Scenario | Use | Why |
|----------|-----|-----|
| Single page needs refresh | `revalidatePath('/page')` | Simple, path-based |
| Data shared across many pages | `revalidateTag('tag')` | Invalidates everywhere the tag is used |
| All pages under a segment | `revalidatePath('/blog', 'layout')` | Invalidates layout and all children |
| Specific data entity changed | `revalidateTag('entity-id')` | Granular, entity-level invalidation |
| Everything is stale | `revalidatePath('/', 'layout')` | Nuclear option — re-renders entire site |

---

## Q4. (Beginner) How does Request Memoization work, and what are its limitations?

**Scenario**: Your layout fetches user data, and your page also fetches user data. You want to confirm only one HTTP request is made.

**Answer**:

**Request Memoization** is a React feature (not Next.js-specific) that automatically deduplicates identical `fetch()` calls within the same server render pass.

```
How it works:

 render()
  ├── Layout calls fetch('https://api.example.com/user')
  │   → Check memo cache → MISS → Make HTTP request → Store in memo
  │
  ├── Page calls fetch('https://api.example.com/user')
  │   → Check memo cache → HIT → Return cached result (NO HTTP request)
  │
  └── Component calls fetch('https://api.example.com/user')
      → Check memo cache → HIT → Return cached result (NO HTTP request)

Result: 1 HTTP request, 3 components get the same data
```

```tsx
// This pattern is ENCOURAGED — fetch the same data wherever you need it
// No need to prop-drill or use context for data sharing

// app/layout.tsx
export default async function Layout({ children }) {
  const res = await fetch('https://api.example.com/user');
  const user = await res.json();
  return (
    <html>
      <body>
        <header>Welcome, {user.name}</header>
        {children}
      </body>
    </html>
  );
}

// app/page.tsx
export default async function Page() {
  // SAME URL and options → memoized, no extra HTTP call
  const res = await fetch('https://api.example.com/user');
  const user = await res.json();
  return <div>Email: {user.email}</div>;
}
```

**Limitations**:

| Limitation | Detail |
|-----------|--------|
| Only works with `fetch()` | Direct DB queries, ORM calls, or `axios` are NOT memoized |
| Same URL + options required | Different headers, method, or body = different request |
| Single render pass only | Does NOT persist across requests |
| GET requests only | POST, PUT, DELETE are NOT memoized |
| Server Components only | Does not work in Client Components |

**For non-fetch data sources, use React `cache()`**:

```tsx
// lib/db.ts
import { cache } from 'react';

// React cache() gives you request memoization for ANY function
export const getUser = cache(async (userId: string) => {
  // Direct database query — not using fetch()
  const user = await db.user.findUnique({ where: { id: userId } });
  return user;
});

// Now calling getUser('123') multiple times in the same render
// only executes the DB query ONCE
```

```tsx
// app/layout.tsx
import { getUser } from '@/lib/db';
import { auth } from '@/lib/auth';

export default async function Layout({ children }) {
  const session = await auth();
  const user = await getUser(session.userId); // DB query #1
  return <div>{children}</div>;
}

// app/page.tsx
import { getUser } from '@/lib/db';
import { auth } from '@/lib/auth';

export default async function Page() {
  const session = await auth();
  const user = await getUser(session.userId); // MEMOIZED — no DB query
  return <div>{user.name}</div>;
}
```

---

## Q5. (Beginner) What is the Full Route Cache and how does it relate to static vs dynamic rendering?

**Scenario**: You built a marketing page that should be pre-rendered at build time but it keeps re-rendering on every request.

**Answer**:

The **Full Route Cache** stores the pre-rendered HTML and RSC Payload of **static routes** at build time. On subsequent requests, the cached result is served without re-rendering.

```
Build Time:
┌─────────────┐     ┌────────────────────┐
│  next build  │────▶│  Full Route Cache   │
│              │     │                    │
│  /about      │     │  /about.html       │
│  /pricing    │     │  /about.rsc        │
│  /blog/hello │     │  /pricing.html     │
│              │     │  /pricing.rsc      │
│              │     │  /blog/hello.html  │
│              │     │  /blog/hello.rsc   │
└─────────────┘     └────────────────────┘

Runtime:
  Request for /about
  → Check Full Route Cache → HIT
  → Return cached HTML + RSC payload
  → No server rendering needed
```

**A route becomes dynamic (NOT cached) if it uses**:

```tsx
// Any of these make a route dynamic:
import { cookies, headers } from 'next/headers';
import { searchParams } from 'next/navigation';

export default async function Page({
  searchParams, // ← dynamic (Next.js 15: searchParams is a Promise)
}) {
  const { page } = await searchParams;
  // Route is now dynamic — re-renders on every request
}

// Using cookies() or headers()
export default async function Page() {
  const cookieStore = await cookies();    // ← dynamic
  const headerList = await headers();     // ← dynamic
}

// Using fetch() with no-store
export default async function Page() {
  const data = await fetch('https://api.example.com/data', {
    cache: 'no-store', // ← dynamic
  });
}

// Using connection() or draftMode()
import { connection } from 'next/server';
export default async function Page() {
  await connection(); // ← force dynamic
}
```

**Force a route to be static or dynamic**:

```tsx
// Force static (will error if dynamic functions are used)
export const dynamic = 'force-static';
export const revalidate = 3600; // ISR: rebuild every hour

export default async function PricingPage() {
  const plans = await fetch('https://api.example.com/plans', {
    cache: 'force-cache',
  }).then(res => res.json());

  return <PricingTable plans={plans} />;
}

// Force dynamic (never cache the full route)
export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  const data = await getPersonalizedDashboard();
  return <Dashboard data={data} />;
}
```

**How to check if routes are static or dynamic**:

```
After `next build`, you'll see:

Route (app)                    Size     First Load JS
┌ ○ /                          5.2 kB   89.1 kB
├ ○ /about                     1.2 kB   85.1 kB
├ ● /blog/[slug]               3.4 kB   87.3 kB
├ λ /dashboard                 8.1 kB   92.0 kB
└ λ /api/data                  0 B      83.9 kB

○ = Static (fully cached at build time)
● = Static with ISR (cached, revalidated periodically)
λ = Dynamic (rendered on every request)
```

---

## Q6. (Intermediate) How does the Data Cache work, and how do you control its behavior per fetch?

**Scenario**: Your e-commerce site has product data (changes hourly), user cart data (must be fresh), and site configuration (changes monthly). Each needs a different caching strategy.

**Answer**:

The **Data Cache** persists `fetch()` results on the server across requests and deployments. In Next.js 15, it's **opt-in** — you must explicitly configure caching per fetch.

```
Request Flow with Data Cache:

fetch('https://api.example.com/products', { next: { revalidate: 3600 } })

  ┌─────────────────────────────────────────────────┐
  │ 1. Check Request Memoization → MISS             │
  │ 2. Check Data Cache                             │
  │    ├── HIT + FRESH → Return cached data         │
  │    ├── HIT + STALE → Return stale data,         │
  │    │                  trigger background refetch  │
  │    └── MISS → Fetch from API, store in cache    │
  └─────────────────────────────────────────────────┘
```

**Per-fetch caching strategies**:

```tsx
// Strategy 1: No cache (default in Next.js 15)
// Use for: user-specific data, real-time data, cart, auth
const cart = await fetch('https://api.example.com/cart', {
  cache: 'no-store',
});

// Strategy 2: Cache forever until manually invalidated
// Use for: site config, rarely changing reference data
const config = await fetch('https://api.example.com/config', {
  cache: 'force-cache',
});

// Strategy 3: Time-based revalidation (ISR for data)
// Use for: product catalog, blog posts, pricing
const products = await fetch('https://api.example.com/products', {
  next: { revalidate: 3600 }, // Stale after 1 hour
});

// Strategy 4: Tag-based invalidation
// Use for: CMS content, any data with webhook-based invalidation
const posts = await fetch('https://api.example.com/posts', {
  next: { tags: ['posts'] },
});

// Strategy 5: Combined — tags + time-based
// Use for: data that needs both scheduled and on-demand invalidation
const featured = await fetch('https://api.example.com/featured', {
  next: {
    revalidate: 300,         // Revalidate every 5 minutes at minimum
    tags: ['featured'],       // Also invalidate on-demand via tag
  },
});
```

**Production example — E-commerce data strategies**:

```tsx
// lib/api/products.ts
import { cache } from 'react';

// Product catalog: cached for 1 hour, tagged for on-demand invalidation
export const getProducts = cache(async (category?: string) => {
  const url = new URL('https://api.example.com/products');
  if (category) url.searchParams.set('category', category);

  const res = await fetch(url.toString(), {
    next: {
      revalidate: 3600,
      tags: ['products', ...(category ? [`products-${category}`] : [])],
    },
  });

  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
});

// Single product: cached and tagged individually
export const getProduct = cache(async (id: string) => {
  const res = await fetch(`https://api.example.com/products/${id}`, {
    next: {
      revalidate: 3600,
      tags: ['products', `product-${id}`],
    },
  });

  if (!res.ok) throw new Error('Failed to fetch product');
  return res.json();
});

// Cart: never cached (user-specific, real-time)
export async function getCart(userId: string) {
  const res = await fetch(`https://api.example.com/cart/${userId}`, {
    cache: 'no-store',
    headers: { 'Authorization': `Bearer ${await getToken()}` },
  });
  return res.json();
}

// Site config: cached aggressively
export const getSiteConfig = cache(async () => {
  const res = await fetch('https://api.example.com/config', {
    cache: 'force-cache',
    next: { tags: ['site-config'] },
  });
  return res.json();
});
```

**Data Cache entry lifecycle**:

```
t=0     : fetch() → MISS → call API → store { data, timestamp, revalidate: 3600 }
t=1s    : fetch() → HIT (fresh) → return cached data
t=3599s : fetch() → HIT (fresh) → return cached data
t=3601s : fetch() → HIT (STALE) → return stale data, trigger background refetch
t=3602s : background refetch completes → cache updated with fresh data
t=3603s : fetch() → HIT (fresh) → return new cached data
```

---

## Q7. (Intermediate) How does the Router Cache work in Next.js 15, and how do you configure `staleTimes`?

**Scenario**: Users on your SaaS dashboard complain that after performing an action (e.g., deleting a project), navigating back to the project list still shows the deleted project.

**Answer**:

The **Router Cache** is a client-side, in-memory cache that stores the RSC Payload of previously visited routes. In Next.js 15, its default stale time is **0 seconds**, meaning every navigation triggers a server fetch.

```
How Router Cache works:

Visit /dashboard → Server renders → Store RSC payload in Router Cache
Visit /settings  → Server renders → Store RSC payload in Router Cache
Click back       → Check Router Cache for /dashboard
                   ├── If fresh → Return cached payload (instant)
                   └── If stale → Fetch from server (may show stale while fetching)
```

**Configuring `staleTimes` in Next.js 15**:

```tsx
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    staleTimes: {
      // How long dynamic pages are cached on the client (seconds)
      dynamic: 30,   // Default: 0 in Next.js 15

      // How long static pages are cached on the client (seconds)
      static: 180,   // Default: 0 in Next.js 15 (was 300 in v14)
    },
  },
};

export default nextConfig;
```

**When the Router Cache is invalidated**:

```tsx
// Method 1: router.refresh() — Invalidate current route
'use client';
import { useRouter } from 'next/navigation';

function DeleteButton({ projectId }: { projectId: string }) {
  const router = useRouter();

  async function handleDelete() {
    await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
    router.refresh(); // Invalidates Router Cache for current route
  }

  return <button onClick={handleDelete}>Delete</button>;
}

// Method 2: Server Action with revalidation
'use server';
import { revalidatePath } from 'next/cache';

export async function deleteProject(projectId: string) {
  await db.project.delete({ where: { id: projectId } });
  revalidatePath('/dashboard/projects'); // Invalidates both Data + Router Cache
}

// Method 3: revalidateTag invalidates Router Cache for affected routes
'use server';
import { revalidateTag } from 'next/cache';

export async function updateProject(projectId: string, data: FormData) {
  await db.project.update({ where: { id: projectId }, data: { ... } });
  revalidateTag('projects'); // All routes using 'projects' tag are invalidated
}
```

**Router Cache behavior comparison**:

| Action | Router Cache Effect |
|--------|-------------------|
| `<Link>` navigation | Checks cache → serves if fresh, otherwise fetches |
| `router.push()` | Same as `<Link>` |
| `router.refresh()` | Invalidates cache for current route, re-fetches |
| `router.back()` / `router.forward()` | Uses cached version (even if stale) |
| Browser refresh (F5) | Bypasses Router Cache entirely (hard nav) |
| `revalidatePath()` in Server Action | Invalidates affected routes in Router Cache |
| `revalidateTag()` in Server Action | Invalidates affected routes in Router Cache |
| Cookie change (`cookies().set()`) | Invalidates Router Cache for all routes |

**Practical pattern — Immediate UI update + cache invalidation**:

```tsx
'use client';

import { useOptimistic, useTransition } from 'react';
import { deleteProject } from '@/actions/projects';
import { useRouter } from 'next/navigation';

function ProjectList({ projects }: { projects: Project[] }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [optimisticProjects, removeOptimistic] = useOptimistic(
    projects,
    (state, deletedId: string) => state.filter((p) => p.id !== deletedId)
  );

  function handleDelete(id: string) {
    startTransition(async () => {
      removeOptimistic(id); // Immediately remove from UI
      await deleteProject(id); // Server Action revalidates cache
      router.refresh(); // Ensure Router Cache is fresh
    });
  }

  return (
    <ul>
      {optimisticProjects.map((project) => (
        <li key={project.id}>
          {project.name}
          <button onClick={() => handleDelete(project.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

---

## Q8. (Intermediate) How do you implement on-demand revalidation vs time-based revalidation? When do you choose each?

**Scenario**: Your content management system needs both scheduled content updates (new articles every hour) and instant updates when an editor hits "Publish."

**Answer**:

```
TIME-BASED REVALIDATION (ISR):
┌──────────────────────────────────────────────────────┐
│                                                      │
│  t=0    Build: Generate static page                  │
│  t=1s   Request: Serve cached page ✓                │
│  t=59s  Request: Serve cached page ✓                │
│  t=61s  Request: Serve STALE page, trigger rebuild   │
│  t=62s  Rebuild complete: New page ready             │
│  t=63s  Request: Serve NEW page ✓                   │
│                                                      │
│  Pros: Automatic, no webhook needed                  │
│  Cons: Up to {revalidate} seconds of stale data     │
└──────────────────────────────────────────────────────┘

ON-DEMAND REVALIDATION:
┌──────────────────────────────────────────────────────┐
│                                                      │
│  t=0    Build: Generate static page                  │
│  t=1s   Request: Serve cached page ✓                │
│  t=100s Request: Serve cached page ✓ (still fresh!) │
│  t=200s Editor publishes → webhook triggers          │
│         revalidateTag('posts') → cache purged        │
│  t=201s Request: Re-render page with new data ✓     │
│                                                      │
│  Pros: Instant updates when content changes          │
│  Cons: Requires webhook integration                  │
└──────────────────────────────────────────────────────┘
```

**Time-based revalidation**:

```tsx
// Every fetch can have its own revalidation interval

// Blog posts — check for updates every 60 seconds
export default async function BlogPage() {
  const posts = await fetch('https://cms.example.com/api/posts', {
    next: { revalidate: 60 },
  }).then((res) => res.json());

  return <PostList posts={posts} />;
}

// Alternatively, set revalidation for the entire route segment:
export const revalidate = 60; // Revalidate this page every 60 seconds
```

**On-demand revalidation**:

```tsx
// app/api/revalidate/route.ts
import { revalidateTag, revalidatePath } from 'next/cache';
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const { secret, tag, path, type } = await request.json();

  // Verify webhook secret
  if (secret !== process.env.REVALIDATION_SECRET) {
    return Response.json({ error: 'Invalid secret' }, { status: 401 });
  }

  try {
    if (tag) {
      revalidateTag(tag);
      return Response.json({ revalidated: true, tag });
    }

    if (path) {
      revalidatePath(path, type === 'layout' ? 'layout' : 'page');
      return Response.json({ revalidated: true, path });
    }

    return Response.json({ error: 'No tag or path provided' }, { status: 400 });
  } catch (error) {
    return Response.json({ error: 'Revalidation failed' }, { status: 500 });
  }
}
```

**Production pattern — Combine both strategies**:

```tsx
// Best of both worlds: time-based as safety net + on-demand for instant updates
const posts = await fetch('https://cms.example.com/api/posts', {
  next: {
    revalidate: 3600,          // Safety net: at least every hour
    tags: ['posts'],            // On-demand: instant when webhook fires
  },
});
```

**Decision matrix**:

| Scenario | Strategy | Reason |
|----------|----------|--------|
| Marketing pages | Time-based (1 hour) | Content changes are planned |
| Blog/CMS content | On-demand + time backup | Editors need instant publish |
| Product catalog | On-demand via admin API | Price changes must be immediate |
| User dashboard | No cache (dynamic) | Personalized, real-time data |
| API documentation | Time-based (24 hours) | Rarely changes |
| Social feed | No cache | Real-time content |
| Search results | No cache | Query-dependent |
| Site navigation/config | On-demand + long TTL | Changes are rare, must be instant when they happen |

---

## Q9. (Intermediate) How do you debug caching issues in Next.js? What tools and techniques are available?

**Scenario**: Data on your production site appears stale, but you're not sure which caching layer is causing the issue. How do you diagnose it?

**Answer**:

**Step 1: Enable verbose logging**:

```tsx
// next.config.ts
const nextConfig = {
  logging: {
    fetches: {
      fullUrl: true,    // Log complete fetch URLs
      hmrRefreshes: true, // Log HMR-triggered fetches
    },
  },
};
```

This outputs:

```
GET /dashboard 200 in 245ms
 │ GET https://api.example.com/user 200 in 34ms (cache: HIT)
 │ GET https://api.example.com/projects 200 in 189ms (cache: MISS)
 │ GET https://api.example.com/notifications 200 in 12ms (cache: SKIP)
```

**Step 2: Check cache headers in responses**:

```tsx
// Middleware to add cache debugging headers
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  if (process.env.NODE_ENV === 'development') {
    response.headers.set('X-Cache-Debug', 'enabled');
    response.headers.set('X-Request-Time', new Date().toISOString());
  }

  return response;
}
```

**Step 3: Verify cache status per fetch**:

```tsx
// lib/debug-fetch.ts
export async function debugFetch(
  url: string,
  options?: RequestInit & { next?: { revalidate?: number; tags?: string[] } }
) {
  const start = performance.now();
  const res = await fetch(url, options);
  const duration = performance.now() - start;

  if (process.env.NODE_ENV === 'development') {
    const cacheStatus = res.headers.get('x-vercel-cache') || 'unknown';
    const age = res.headers.get('age') || '0';
    console.log(
      `[fetch] ${url}\n` +
      `  Status: ${res.status}\n` +
      `  Cache: ${cacheStatus}\n` +
      `  Age: ${age}s\n` +
      `  Duration: ${duration.toFixed(0)}ms\n` +
      `  Options: ${JSON.stringify(options?.next || {})}`
    );
  }

  return res;
}
```

**Step 4: Vercel cache headers** (when deployed on Vercel):

```
X-Vercel-Cache: HIT    → Served from edge cache
X-Vercel-Cache: MISS   → Not in cache, fetched from origin
X-Vercel-Cache: STALE  → Served stale while revalidating
X-Vercel-Cache: BYPASS  → Cache bypassed (dynamic route)

Cache-Control: s-maxage=3600, stale-while-revalidate
                │                   │
                │                   └─ Serve stale while fetching fresh
                └─ Fresh for 1 hour on CDN
```

**Step 5: Build output analysis**:

```bash
next build

# Check the output:
Route (app)                    Size    First Load JS
┌ ○ /                          5.2 kB   89.1 kB      ← Static (cached)
├ ○ /about                     1.2 kB   85.1 kB      ← Static (cached)
├ ● /blog/[slug]               3.4 kB   87.3 kB      ← ISR (revalidate)
├ λ /dashboard                 8.1 kB   92.0 kB      ← Dynamic (never cached)
└ λ /api/data                  0 B      83.9 kB      ← Dynamic

○  Static       → Full Route Cache active
●  ISR          → Full Route Cache with revalidation
λ  Dynamic      → No Full Route Cache
```

**Common debugging scenarios and solutions**:

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Data always stale | Data Cache not invalidated | Add `revalidateTag`/`revalidatePath` |
| Data always fresh (slow) | No caching configured (Next.js 15 default) | Add `next: { revalidate }` |
| Stale after back navigation | Router Cache serving old data | Use `router.refresh()` or set `staleTimes` |
| Cache not working in dev | Dev mode doesn't use Data/Route Cache | Test with `next build && next start` |
| ISR not triggering | Missing `revalidate` config | Add `export const revalidate = N` or `next: { revalidate: N }` |
| On-demand revalidation not working | Wrong tag name or webhook issue | Log tag names, verify webhook delivery |

---

## Q10. (Intermediate) How do you implement `stale-while-revalidate` pattern in Next.js?

**Scenario**: Your product page should show content instantly (even if slightly stale) while fresh data is fetched in the background.

**Answer**:

The stale-while-revalidate (SWR) pattern is **built into Next.js's ISR**. When you set `revalidate`, Next.js automatically serves stale data while fetching fresh data in the background.

```
SWR Timeline:

Build     → Generate page → Cache
Request 1 → Serve cached (FRESH)
...
TTL expires
Request N → Serve cached (STALE) + trigger background rebuild
Request N+1 → Serve NEW cached page (FRESH)

┌──────────┐    ┌──────────┐    ┌──────────┐
│  FRESH   │    │  STALE   │    │  FRESH   │
│  Serve   │    │  Serve   │    │  Serve   │
│  cached  │    │  stale + │    │  new     │
│          │    │  rebuild │    │  cached  │
└──────────┘    └──────────┘    └──────────┘
 0s ──── revalidate ──── rebuild done ────>
```

**Implementation at the page level**:

```tsx
// app/products/[id]/page.tsx

// Option 1: Route segment config
export const revalidate = 60; // Seconds

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);
  return <ProductDetail product={product} />;
}
```

**Implementation at the fetch level**:

```tsx
// More granular: different revalidation per data source
export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // Product data: stale-while-revalidate every 60s
  const product = await fetch(`https://api.example.com/products/${id}`, {
    next: { revalidate: 60 },
  }).then((r) => r.json());

  // Reviews: stale-while-revalidate every 5 minutes
  const reviews = await fetch(`https://api.example.com/products/${id}/reviews`, {
    next: { revalidate: 300 },
  }).then((r) => r.json());

  // Inventory: always fresh (no cache)
  const inventory = await fetch(`https://api.example.com/inventory/${id}`, {
    cache: 'no-store',
  }).then((r) => r.json());

  return (
    <div>
      <ProductDetail product={product} />
      <InventoryBadge count={inventory.count} /> {/* Always fresh */}
      <ReviewList reviews={reviews} />
    </div>
  );
}
```

**Client-side SWR with `useSWR`** (for real-time updates on client):

```tsx
// For data that needs to stay fresh on the client after initial server render
'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(r => r.json());

export function InventoryBadge({ productId, initialCount }: {
  productId: string;
  initialCount: number;
}) {
  const { data } = useSWR(
    `/api/inventory/${productId}`,
    fetcher,
    {
      fallbackData: { count: initialCount }, // SSR data as initial
      refreshInterval: 10000,                // Poll every 10 seconds
      revalidateOnFocus: true,               // Refresh when tab gains focus
    }
  );

  return (
    <span className={data.count > 0 ? 'text-green-600' : 'text-red-600'}>
      {data.count > 0 ? `${data.count} in stock` : 'Out of stock'}
    </span>
  );
}
```

---

## Q11. (Intermediate) How do you set up cache-control headers for CDN caching in both Vercel and self-hosted deployments?

**Scenario**: You're deploying Next.js behind Cloudflare CDN (self-hosted) and need fine-grained control over which pages are cached at the CDN edge.

**Answer**:

```
CDN Caching Layer:

Client → CDN Edge → Next.js Server
                      │
    Cache-Control headers tell CDN what to cache

Headers:
  Cache-Control: public, s-maxage=3600, stale-while-revalidate=86400
                  │        │                │
                  │        │                └─ CDN can serve stale for 24h
                  │        └─ Fresh on CDN for 1 hour
                  └─ CDN (shared cache) can cache this
```

**Setting cache headers in Route Handlers**:

```tsx
// app/api/products/route.ts
export async function GET() {
  const products = await getProducts();

  return Response.json(products, {
    headers: {
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      'CDN-Cache-Control': 'max-age=3600', // Cloudflare-specific
      'Vercel-CDN-Cache-Control': 'max-age=3600', // Vercel-specific
    },
  });
}
```

**Setting headers in `next.config.ts`**:

```tsx
// next.config.ts
const nextConfig = {
  async headers() {
    return [
      {
        // Static assets — cache aggressively
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Images — cache for 1 day
        source: '/images/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=86400, stale-while-revalidate=604800',
          },
        ],
      },
      {
        // API responses — cache for 5 minutes at CDN
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=300, stale-while-revalidate=600',
          },
        ],
      },
      {
        // HTML pages — short cache with revalidation
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=60, stale-while-revalidate=3600',
          },
        ],
      },
    ];
  },
};
```

**Self-hosted with Cloudflare — Middleware for dynamic cache control**:

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  const pathname = request.nextUrl.pathname;

  // Static pages — cache at CDN edge
  if (pathname.startsWith('/blog') || pathname.startsWith('/docs')) {
    response.headers.set(
      'Cache-Control',
      'public, s-maxage=3600, stale-while-revalidate=86400'
    );
    response.headers.set('CDN-Cache-Control', 'max-age=3600');
  }

  // Dynamic pages — don't cache at CDN
  if (pathname.startsWith('/dashboard') || pathname.startsWith('/account')) {
    response.headers.set('Cache-Control', 'private, no-cache, no-store');
  }

  // API routes — vary by authorization
  if (pathname.startsWith('/api')) {
    response.headers.set('Vary', 'Authorization, Accept-Encoding');
  }

  return response;
}
```

**Vercel vs Self-hosted caching comparison**:

| Feature | Vercel | Self-hosted + CDN |
|---------|--------|-------------------|
| Automatic ISR | Built-in | Must configure CDN purge |
| Edge caching | Automatic | Manual Cache-Control headers |
| On-demand revalidation | `revalidateTag`/`revalidatePath` | Need CDN purge API integration |
| Cache purge | Instant, automatic | Must call CDN purge API |
| Stale-while-revalidate | Built-in | CDN must support SWR |
| Regional caching | Edge network | Depends on CDN config |

---

## Q12. (Intermediate) How do you integrate Redis for caching in a self-hosted Next.js application?

**Scenario**: You're running Next.js on a Kubernetes cluster. The built-in filesystem-based Data Cache doesn't work well with multiple pods. You need a shared cache.

**Answer**:

Next.js supports custom **cache handlers** that replace the default filesystem cache with external stores like Redis.

```
Default (single server):             Redis (multi-server):
┌─────────┐                          ┌─────────┐  ┌─────────┐
│ Pod 1    │                          │ Pod 1    │  │ Pod 2    │
│ ┌─────┐ │                          │          │  │          │
│ │Cache│ │  ← filesystem cache      │          │  │          │
│ └─────┘ │    (not shared!)         └────┬─────┘  └────┬─────┘
└─────────┘                               │             │
┌─────────┐                               ▼             ▼
│ Pod 2    │                          ┌─────────────────────┐
│ ┌─────┐ │                          │    Redis Cluster     │
│ │Cache│ │  ← different cache!      │    (shared cache)    │
│ └─────┘ │                          └─────────────────────┘
└─────────┘
```

**Step 1: Install dependencies**:

```bash
npm install @neshca/cache-handler ioredis
```

**Step 2: Create the cache handler**:

```tsx
// cache-handler.mjs
import { CacheHandler } from '@neshca/cache-handler';
import createRedisHandler from '@neshca/cache-handler/redis-strings';
import { createClient } from 'redis';

CacheHandler.onCreation(async () => {
  let redisHandler;

  if (process.env.REDIS_URL) {
    try {
      const client = createClient({
        url: process.env.REDIS_URL,
        socket: {
          connectTimeout: 5000,
          reconnectStrategy(retries) {
            if (retries > 10) return new Error('Redis max retries reached');
            return Math.min(retries * 100, 3000);
          },
        },
      });

      client.on('error', (err) => {
        console.error('Redis client error:', err);
      });

      await client.connect();

      redisHandler = await createRedisHandler({
        client,
        keyPrefix: 'nextjs-cache:',
        timeoutMs: 1000, // Redis operation timeout
      });

      console.log('Redis cache handler connected');
    } catch (error) {
      console.warn('Redis connection failed, falling back to in-memory cache:', error);
    }
  }

  return {
    handlers: [
      redisHandler, // Primary: Redis
      // Falls back to in-memory if Redis is unavailable
    ].filter(Boolean),
  };
});

export default CacheHandler;
```

**Step 3: Configure Next.js to use the custom handler**:

```tsx
// next.config.ts
const nextConfig = {
  cacheHandler:
    process.env.NODE_ENV === 'production'
      ? require.resolve('./cache-handler.mjs')
      : undefined,
  cacheMaxMemorySize: 0, // Disable in-memory cache (use Redis only)
};

export default nextConfig;
```

**Step 4: Production Redis cache with manual implementation**:

```tsx
// lib/redis-cache.ts
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!, {
  maxRetriesPerRequest: 3,
  enableReadyCheck: true,
  lazyConnect: true,
});

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  revalidate?: number;
  tags: string[];
}

export async function getCached<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: { revalidate?: number; tags?: string[] } = {}
): Promise<T> {
  const cacheKey = `cache:${key}`;

  try {
    // Check cache
    const cached = await redis.get(cacheKey);
    if (cached) {
      const entry: CacheEntry<T> = JSON.parse(cached);
      const age = (Date.now() - entry.timestamp) / 1000;

      // Fresh: return cached data
      if (!entry.revalidate || age < entry.revalidate) {
        return entry.data;
      }

      // Stale: return cached data + trigger background refresh
      void refreshCache(cacheKey, fetcher, options);
      return entry.data;
    }
  } catch (error) {
    console.error('Redis cache read error:', error);
  }

  // Cache miss: fetch fresh data
  const data = await fetcher();

  // Store in cache
  try {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      revalidate: options.revalidate,
      tags: options.tags || [],
    };

    const ttl = options.revalidate
      ? options.revalidate * 2 // Store for 2x revalidate period
      : 86400; // Default: 24 hours

    await redis.setex(cacheKey, ttl, JSON.stringify(entry));

    // Index by tags for invalidation
    if (options.tags) {
      for (const tag of options.tags) {
        await redis.sadd(`tag:${tag}`, cacheKey);
      }
    }
  } catch (error) {
    console.error('Redis cache write error:', error);
  }

  return data;
}

async function refreshCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: { revalidate?: number; tags?: string[] }
) {
  try {
    const data = await fetcher();
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      revalidate: options.revalidate,
      tags: options.tags || [],
    };
    const ttl = options.revalidate ? options.revalidate * 2 : 86400;
    await redis.setex(key, ttl, JSON.stringify(entry));
  } catch (error) {
    console.error('Background cache refresh failed:', error);
  }
}

// Tag-based invalidation
export async function invalidateTag(tag: string) {
  const keys = await redis.smembers(`tag:${tag}`);
  if (keys.length > 0) {
    await redis.del(...keys);
    await redis.del(`tag:${tag}`);
  }
}
```

**Usage in Server Components**:

```tsx
// app/products/page.tsx
import { getCached } from '@/lib/redis-cache';

export default async function ProductsPage() {
  const products = await getCached(
    'products:all',
    () => fetch('https://api.example.com/products').then(r => r.json()),
    { revalidate: 3600, tags: ['products'] }
  );

  return <ProductGrid products={products} />;
}
```

---

## Q13. (Advanced) How do you implement cache warming to prevent cold start latency?

**Scenario**: After a deployment, the first request to each page is slow because all caches are cold. You want to pre-warm caches so users never hit a cold cache.

**Answer**:

Cache warming is the process of proactively populating caches before users hit them. In Next.js, this involves warming the Data Cache, Full Route Cache, and optionally CDN edge caches.

```
Cold Deploy (no warming):
Deploy → First request → SLOW (cache miss) → Subsequent requests FAST

Warm Deploy:
Deploy → Cache warm script → All caches populated → First request FAST

┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│  Deploy   │──▶│  Warm Script  │──▶│  Caches   │──▶│  Users   │
│           │    │  hits key     │    │  Hot ✓    │    │  Fast!   │
│           │    │  pages        │    │           │    │          │
└──────────┘    └──────────────┘    └──────────┘    └──────────┘
```

**Strategy 1: Build-time static generation (most pages)**:

```tsx
// app/products/[id]/page.tsx
// Use generateStaticParams to pre-build popular product pages
export async function generateStaticParams() {
  // Pre-render the top 1000 most viewed products at build time
  const topProducts = await fetch('https://api.example.com/products/top?limit=1000')
    .then(r => r.json());

  return topProducts.map((product: { id: string }) => ({
    id: product.id,
  }));
}

// Enable dynamic rendering for non-pre-built products
export const dynamicParams = true; // Allow pages not in generateStaticParams
```

**Strategy 2: Post-deploy cache warming script**:

```tsx
// scripts/warm-cache.ts
interface WarmTarget {
  url: string;
  priority: 'high' | 'medium' | 'low';
}

async function warmCache() {
  const baseUrl = process.env.SITE_URL || 'https://example.com';

  // Discover pages to warm
  const targets: WarmTarget[] = [];

  // High priority: homepage, key landing pages
  targets.push(
    { url: '/', priority: 'high' },
    { url: '/pricing', priority: 'high' },
    { url: '/features', priority: 'high' },
  );

  // Medium priority: popular content pages
  const popularPosts = await fetch(`${baseUrl}/api/internal/popular-pages`)
    .then(r => r.json());
  for (const post of popularPosts) {
    targets.push({ url: post.path, priority: 'medium' });
  }

  // Low priority: sitemap pages
  const sitemapRes = await fetch(`${baseUrl}/sitemap.xml`);
  const sitemapText = await sitemapRes.text();
  const urlMatches = sitemapText.matchAll(/<loc>(.*?)<\/loc>/g);
  for (const match of urlMatches) {
    const path = new URL(match[1]).pathname;
    if (!targets.some(t => t.url === path)) {
      targets.push({ url: path, priority: 'low' });
    }
  }

  // Warm in priority order with concurrency control
  const concurrency = 10;
  const sorted = targets.sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return order[a.priority] - order[b.priority];
  });

  console.log(`Warming ${sorted.length} pages...`);

  let warmed = 0;
  let errors = 0;

  for (let i = 0; i < sorted.length; i += concurrency) {
    const batch = sorted.slice(i, i + concurrency);
    const results = await Promise.allSettled(
      batch.map(async (target) => {
        const res = await fetch(`${baseUrl}${target.url}`, {
          headers: {
            'X-Cache-Warm': 'true',
            'User-Agent': 'CacheWarmer/1.0',
          },
        });

        if (!res.ok) {
          throw new Error(`${target.url}: ${res.status}`);
        }
        return target.url;
      })
    );

    for (const result of results) {
      if (result.status === 'fulfilled') {
        warmed++;
      } else {
        errors++;
        console.error(`Failed: ${result.reason}`);
      }
    }

    // Progress
    console.log(`Progress: ${warmed}/${sorted.length} warmed, ${errors} errors`);
  }

  console.log(`\nCache warming complete: ${warmed} pages warmed, ${errors} errors`);
}

warmCache().catch(console.error);
```

**Strategy 3: CI/CD integration**:

```yaml
# .github/workflows/deploy.yml
name: Deploy and Warm Cache
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - run: npm ci
      - run: npm run build
      - run: npm run deploy # Your deployment command

      - name: Wait for deployment
        run: sleep 30 # Wait for deployment to stabilize

      - name: Warm cache
        run: npx tsx scripts/warm-cache.ts
        env:
          SITE_URL: ${{ vars.PRODUCTION_URL }}

      - name: Verify cache
        run: |
          # Check that key pages return cached responses
          for url in "/" "/pricing" "/blog"; do
            status=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL$url")
            cache=$(curl -s -I "$SITE_URL$url" | grep -i "x-vercel-cache" | awk '{print $2}')
            echo "$url: status=$status cache=$cache"
          done
```

**Strategy 4: Incremental cache warming with Redis**:

```tsx
// lib/cache-warmer.ts
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!);
const WARM_QUEUE = 'cache:warm:queue';

export async function queueWarm(paths: string[]) {
  await redis.rpush(WARM_QUEUE, ...paths);
}

export async function processWarmQueue(batchSize = 5) {
  while (true) {
    const paths = await redis.lpop(WARM_QUEUE, batchSize);
    if (!paths || paths.length === 0) break;

    await Promise.allSettled(
      paths.map((path) =>
        fetch(`${process.env.SITE_URL}${path}`, {
          headers: { 'X-Cache-Warm': 'true' },
        })
      )
    );
  }
}
```

---

## Q14. (Advanced) How do you prevent cache stampedes in high-traffic Next.js applications?

**Scenario**: Your site gets 10,000 requests per second. When the ISR revalidation period expires, all 10,000 requests hit the origin simultaneously, causing a spike.

**Answer**:

A **cache stampede** (also called "thundering herd") occurs when a cached entry expires and many concurrent requests all try to regenerate it simultaneously.

```
Cache Stampede:

Cache expires at t=3600s
  t=3600.001 → Request A: cache MISS → regenerate
  t=3600.002 → Request B: cache MISS → regenerate
  t=3600.003 → Request C: cache MISS → regenerate
  ...
  t=3600.010 → Request J: cache MISS → regenerate

10 concurrent regeneration requests to origin!
┌──────────────────────────────────────┐
│  Origin Server                       │
│  ████████████████ CPU 100% ████████  │
│  10 parallel renders of same page    │
└──────────────────────────────────────┘
```

**Next.js ISR built-in protection**: Next.js ISR already implements a form of stampede prevention through **coalescing** — only one re-render is triggered, and stale content is served to all other requests while the re-render happens.

```
ISR with coalescing (built-in):

  t=3600.001 → Request A: STALE → serve stale, trigger rebuild
  t=3600.002 → Request B: STALE → serve stale (rebuild already in progress)
  t=3600.003 → Request C: STALE → serve stale (rebuild already in progress)
  t=3601.000 → Rebuild complete → cache updated
  t=3601.001 → Request D: FRESH → serve new cached page
```

**For custom caching (Redis), implement locking**:

```tsx
// lib/cache-with-stampede-prevention.ts
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!);

interface CacheOptions {
  key: string;
  ttl: number; // Cache TTL in seconds
  lockTtl?: number; // Lock TTL in seconds (default: 30)
  staleTtl?: number; // How long to serve stale while refreshing
}

export async function getWithStampedeProtection<T>(
  fetcher: () => Promise<T>,
  options: CacheOptions
): Promise<T> {
  const { key, ttl, lockTtl = 30, staleTtl = ttl * 2 } = options;
  const cacheKey = `data:${key}`;
  const lockKey = `lock:${key}`;

  // Step 1: Check cache
  const cached = await redis.get(cacheKey);
  if (cached) {
    const entry = JSON.parse(cached);
    const age = (Date.now() - entry.timestamp) / 1000;

    // Fresh: return immediately
    if (age < ttl) {
      return entry.data;
    }

    // Stale but within stale window: try to acquire lock for background refresh
    if (age < staleTtl) {
      const acquired = await redis.set(lockKey, '1', 'EX', lockTtl, 'NX');

      if (acquired) {
        // This request won the lock — refresh in background
        void refreshInBackground(fetcher, cacheKey, staleTtl, lockKey);
      }

      // All requests (including lock winner) serve stale data immediately
      return entry.data;
    }
  }

  // Step 2: Cache miss or expired beyond stale window
  // Try to acquire lock
  const acquired = await redis.set(lockKey, '1', 'EX', lockTtl, 'NX');

  if (acquired) {
    // Won the lock — fetch and cache
    try {
      const data = await fetcher();
      await redis.setex(
        cacheKey,
        staleTtl,
        JSON.stringify({ data, timestamp: Date.now() })
      );
      return data;
    } finally {
      await redis.del(lockKey);
    }
  } else {
    // Lost the lock — another request is fetching
    // Wait and retry (with exponential backoff)
    for (let attempt = 0; attempt < 10; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 100 * Math.pow(2, attempt)));
      const result = await redis.get(cacheKey);
      if (result) {
        return JSON.parse(result).data;
      }
    }

    // Fallback: fetch directly (lock holder may have failed)
    return fetcher();
  }
}

async function refreshInBackground<T>(
  fetcher: () => Promise<T>,
  cacheKey: string,
  staleTtl: number,
  lockKey: string
) {
  try {
    const data = await fetcher();
    await redis.setex(
      cacheKey,
      staleTtl,
      JSON.stringify({ data, timestamp: Date.now() })
    );
  } catch (error) {
    console.error('Background refresh failed:', error);
  } finally {
    await redis.del(lockKey);
  }
}
```

**Usage**:

```tsx
// app/products/page.tsx
import { getWithStampedeProtection } from '@/lib/cache-with-stampede-prevention';

export default async function ProductsPage() {
  const products = await getWithStampedeProtection(
    () => fetch('https://api.example.com/products').then(r => r.json()),
    {
      key: 'products:all',
      ttl: 3600,       // Fresh for 1 hour
      staleTtl: 7200,  // Serve stale for up to 2 hours while refreshing
      lockTtl: 30,     // Lock expires after 30 seconds
    }
  );

  return <ProductGrid products={products} />;
}
```

**Stampede prevention strategies comparison**:

| Strategy | Implementation | Pros | Cons |
|----------|---------------|------|------|
| ISR (built-in) | `revalidate` config | Zero setup | Limited to fetch-level |
| Lock-based | Redis SETNX | Prevents duplicate work | Adds latency for lock losers |
| Probabilistic | Refresh randomly before TTL | No coordination needed | May still have some duplicates |
| Pre-emptive refresh | Cron job refreshes before TTL | Zero user impact | Wastes resources if unused |

---

## Q15. (Advanced) How do you build a production caching architecture for a large-scale Next.js application?

**Scenario**: Your e-commerce platform serves 50M pageviews/month with 100K products. Design the complete caching architecture.

**Answer**:

```
Production Caching Architecture:

┌────────────────────────────────────────────────────────────┐
│                       CLIENTS                               │
│  Browser Cache: static assets (365d), SW cache             │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                    CDN EDGE                                  │
│  Vercel Edge / Cloudflare / CloudFront                      │
│  • Static pages: s-maxage=3600                              │
│  • API responses: s-maxage=300                              │
│  • Assets: immutable, max-age=31536000                      │
│  • HTML: stale-while-revalidate=86400                       │
└──────────────────────┬─────────────────────────────────────┘
                       │ (cache miss)
┌──────────────────────▼─────────────────────────────────────┐
│                 NEXT.JS SERVERS (K8s pods)                   │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │ Request Memo     │  │ Full Route Cache                │  │
│  │ (per request)    │  │ (pre-rendered static pages)     │  │
│  └─────────────────┘  └─────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Data Cache                           │  │
│  │  Backed by Redis Cluster (shared across pods)         │  │
│  │  • Product data: TTL 1h + tag invalidation            │  │
│  │  • CMS content: TTL 24h + webhook invalidation        │  │
│  │  • User sessions: TTL 30m                             │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬─────────────────────────────────────┘
                       │ (cache miss)
┌──────────────────────▼─────────────────────────────────────┐
│                 DATA SOURCES                                │
│  • PostgreSQL (products, orders, users)                     │
│  • CMS API (content, blog posts)                            │
│  • Search Service (Elasticsearch / Algolia)                 │
│  • Inventory Service (real-time stock)                      │
└────────────────────────────────────────────────────────────┘
```

**Cache strategy per data type**:

```tsx
// lib/cache-strategies.ts

// === TIER 1: Aggressive Cache (static content) ===
// Marketing pages, docs, legal
export const STATIC_CONTENT = {
  cache: 'force-cache' as const,
  next: { revalidate: 86400, tags: ['static-content'] },
};

// === TIER 2: Moderate Cache (product catalog) ===
// Products, categories, search facets
export const CATALOG_DATA = {
  next: { revalidate: 3600, tags: ['catalog'] },
};

// === TIER 3: Short Cache (dynamic content) ===
// Reviews, ratings, availability
export const DYNAMIC_CONTENT = {
  next: { revalidate: 60, tags: ['dynamic'] },
};

// === TIER 4: No Cache (personalized/real-time) ===
// Cart, user profile, checkout, inventory
export const REAL_TIME = {
  cache: 'no-store' as const,
};
```

```tsx
// app/products/[id]/page.tsx — Multi-tier caching in one page
import { CATALOG_DATA, DYNAMIC_CONTENT, REAL_TIME } from '@/lib/cache-strategies';

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // Tier 2: Product data cached for 1 hour
  const product = await fetch(
    `${API_URL}/products/${id}`,
    { ...CATALOG_DATA, next: { ...CATALOG_DATA.next, tags: ['catalog', `product-${id}`] } }
  ).then(r => r.json());

  // Tier 3: Reviews cached for 60 seconds
  const reviews = await fetch(
    `${API_URL}/products/${id}/reviews`,
    { ...DYNAMIC_CONTENT, next: { ...DYNAMIC_CONTENT.next, tags: [`reviews-${id}`] } }
  ).then(r => r.json());

  // Tier 4: Inventory always fresh
  const inventory = await fetch(
    `${API_URL}/inventory/${id}`,
    REAL_TIME
  ).then(r => r.json());

  return (
    <div>
      <ProductInfo product={product} />
      <InventoryStatus inventory={inventory} />
      <ReviewSection reviews={reviews} />
    </div>
  );
}
```

**Cache invalidation orchestrator**:

```tsx
// app/api/cache/invalidate/route.ts
import { revalidateTag, revalidatePath } from 'next/cache';
import { invalidateTag as redisInvalidateTag } from '@/lib/redis-cache';

const INVALIDATION_RULES: Record<string, (data: any) => Promise<void>> = {
  'product.updated': async (data) => {
    revalidateTag(`product-${data.id}`);
    revalidateTag('catalog');
    await redisInvalidateTag(`product-${data.id}`);
  },
  'product.created': async (data) => {
    revalidateTag('catalog');
    revalidatePath('/products');
    await redisInvalidateTag('catalog');
  },
  'review.created': async (data) => {
    revalidateTag(`reviews-${data.productId}`);
    await redisInvalidateTag(`reviews-${data.productId}`);
  },
  'content.published': async (data) => {
    revalidateTag('static-content');
    revalidatePath(data.path);
    await redisInvalidateTag('static-content');
  },
  'deploy.complete': async () => {
    revalidatePath('/', 'layout');
    // Trigger cache warming
    await fetch(`${process.env.SITE_URL}/api/internal/warm-cache`, {
      method: 'POST',
    });
  },
};

export async function POST(request: Request) {
  const { event, data, secret } = await request.json();

  if (secret !== process.env.CACHE_SECRET) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const handler = INVALIDATION_RULES[event];
  if (!handler) {
    return Response.json({ error: 'Unknown event' }, { status: 400 });
  }

  await handler(data);
  return Response.json({ invalidated: true, event });
}
```

---

## Q16. (Advanced) How do you manage cache keys effectively and avoid cache pollution?

**Scenario**: Your cache is growing unbounded, storing millions of entries for URL variations (`?page=1`, `?sort=name`, `?utm_source=twitter`). You need a cache key management strategy.

**Answer**:

Cache key pollution happens when unnecessary URL variations create unique cache entries. Marketing UTM parameters, tracking parameters, and unnecessary query strings multiply cache entries.

```
Without key normalization:
  /products?sort=price              → Cache Entry 1
  /products?sort=price&utm=twitter  → Cache Entry 2  (same content!)
  /products?utm=twitter&sort=price  → Cache Entry 3  (same content!)
  /products?sort=price&fbclid=abc   → Cache Entry 4  (same content!)

4 cache entries for identical content = waste!

With key normalization:
  All above → /products?sort=price  → Cache Entry 1 (single entry)
```

**Middleware for URL normalization**:

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Parameters that should be stripped before caching
const STRIP_PARAMS = new Set([
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
  'fbclid', 'gclid', 'msclkid', 'twclid',
  'ref', 'source', '_ga', '_gl',
]);

// Parameters that affect content (keep for cache key)
const CACHE_RELEVANT_PARAMS = new Set([
  'page', 'limit', 'sort', 'order', 'category', 'q', 'filter',
]);

export function middleware(request: NextRequest) {
  const url = request.nextUrl.clone();
  const params = url.searchParams;
  let stripped = false;

  // Remove tracking parameters
  for (const key of [...params.keys()]) {
    if (STRIP_PARAMS.has(key)) {
      params.delete(key);
      stripped = true;
    }
  }

  // Sort remaining parameters for consistent cache keys
  if (params.toString()) {
    const sorted = new URLSearchParams(
      [...params.entries()].sort(([a], [b]) => a.localeCompare(b))
    );

    if (sorted.toString() !== params.toString()) {
      url.search = sorted.toString();
      stripped = true;
    }
  }

  if (stripped) {
    return NextResponse.redirect(url, 308); // Permanent redirect to clean URL
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api).*)'],
};
```

**Cache key generation for custom caching**:

```tsx
// lib/cache-keys.ts

interface CacheKeyOptions {
  path: string;
  params?: Record<string, string | string[] | undefined>;
  userId?: string; // For personalized caches
  locale?: string;
}

export function generateCacheKey(options: CacheKeyOptions): string {
  const { path, params, userId, locale } = options;

  // Normalize path
  const normalizedPath = path.replace(/\/+$/, '') || '/';

  // Filter and sort parameters
  const relevantParams: Record<string, string> = {};
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value && CACHE_RELEVANT_PARAMS.has(key)) {
        relevantParams[key] = Array.isArray(value) ? value.sort().join(',') : value;
      }
    }
  }

  const paramString = Object.entries(relevantParams)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join('&');

  // Build key
  const parts = [normalizedPath];
  if (locale) parts.push(`locale:${locale}`);
  if (userId) parts.push(`user:${userId}`);
  if (paramString) parts.push(`params:${paramString}`);

  return parts.join(':');
}

// Usage:
// generateCacheKey({ path: '/products', params: { sort: 'price', utm_source: 'twitter' } })
// → '/products:params:sort=price'  (utm_source stripped)
```

**Cache eviction strategies**:

```tsx
// lib/cache-eviction.ts
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!);

// LRU-based eviction with max cache size
export async function enforceCacheLimit(maxEntries: number = 100000) {
  const currentSize = await redis.dbsize();

  if (currentSize > maxEntries) {
    // Get oldest entries and remove them
    const keysToRemove = currentSize - maxEntries;
    console.log(`Cache size ${currentSize} exceeds limit ${maxEntries}, evicting ${keysToRemove} entries`);

    // Use SCAN to find old entries (don't block Redis with KEYS)
    let cursor = '0';
    let removed = 0;

    while (removed < keysToRemove) {
      const [newCursor, keys] = await redis.scan(
        cursor,
        'MATCH',
        'data:*',
        'COUNT',
        100
      );

      for (const key of keys) {
        if (removed >= keysToRemove) break;
        const ttl = await redis.ttl(key);
        if (ttl < 300) { // Remove entries with less than 5 min TTL
          await redis.del(key);
          removed++;
        }
      }

      cursor = newCursor;
      if (cursor === '0') break;
    }

    console.log(`Evicted ${removed} cache entries`);
  }
}
```

---

## Q17. (Advanced) How do you implement cache tagging and dependency tracking for complex data relationships?

**Scenario**: A product belongs to a category, has reviews, and references an author. When any of these entities change, all pages displaying that product must be invalidated. How do you model these cache dependencies?

**Answer**:

```
Data Relationships:
  Product #42
    ├── belongs to Category: "Electronics"
    ├── has Reviews: [R1, R2, R3]
    ├── authored by Brand: "Acme"
    └── displayed on Pages:
        ├── /products/42
        ├── /categories/electronics
        ├── /brands/acme
        └── /home (featured products)

When Product #42 changes → invalidate all 4 pages
When Category "Electronics" changes → invalidate /categories/electronics + all product pages in it
```

**Multi-level tag system**:

```tsx
// lib/cache-tags.ts

// Tag taxonomy:
// entity:<type>:<id>         — Specific entity
// collection:<type>          — All entities of a type
// page:<path>                — Specific page
// relation:<type>:<id>       — Related entities

export const CacheTags = {
  product: (id: string) => `entity:product:${id}`,
  productCollection: () => 'collection:products',
  category: (slug: string) => `entity:category:${slug}`,
  categoryProducts: (slug: string) => `relation:category-products:${slug}`,
  brand: (id: string) => `entity:brand:${id}`,
  review: (id: string) => `entity:review:${id}`,
  productReviews: (productId: string) => `relation:product-reviews:${productId}`,
  page: (path: string) => `page:${path}`,
} as const;

// Build tag arrays for fetch calls
export function getProductPageTags(product: {
  id: string;
  categorySlug: string;
  brandId: string;
}) {
  return [
    CacheTags.product(product.id),
    CacheTags.productCollection(),
    CacheTags.category(product.categorySlug),
    CacheTags.categoryProducts(product.categorySlug),
    CacheTags.brand(product.brandId),
    CacheTags.productReviews(product.id),
  ];
}
```

**Using tags in data fetching**:

```tsx
// app/products/[id]/page.tsx
import { CacheTags, getProductPageTags } from '@/lib/cache-tags';

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // Fetch product with comprehensive tags
  const product = await fetch(`${API}/products/${id}`, {
    next: {
      tags: [
        CacheTags.product(id),
        CacheTags.productCollection(),
      ],
    },
  }).then(r => r.json());

  // Fetch category with its own tags
  const category = await fetch(`${API}/categories/${product.categorySlug}`, {
    next: {
      tags: [
        CacheTags.category(product.categorySlug),
        CacheTags.categoryProducts(product.categorySlug),
      ],
    },
  }).then(r => r.json());

  // Fetch reviews
  const reviews = await fetch(`${API}/products/${id}/reviews`, {
    next: {
      tags: [CacheTags.productReviews(id)],
    },
  }).then(r => r.json());

  return (
    <div>
      <Breadcrumb category={category} product={product} />
      <ProductDetail product={product} />
      <ReviewList reviews={reviews} />
    </div>
  );
}
```

**Invalidation orchestrator with dependency tracking**:

```tsx
// lib/cache-invalidation.ts
import { revalidateTag } from 'next/cache';
import { CacheTags } from './cache-tags';

type EntityEvent =
  | { type: 'product.updated'; productId: string }
  | { type: 'product.deleted'; productId: string; categorySlug: string }
  | { type: 'category.updated'; slug: string }
  | { type: 'review.created'; reviewId: string; productId: string }
  | { type: 'brand.updated'; brandId: string };

export async function handleCacheInvalidation(event: EntityEvent) {
  const tags: string[] = [];

  switch (event.type) {
    case 'product.updated':
      tags.push(
        CacheTags.product(event.productId),
        CacheTags.productCollection()
      );
      break;

    case 'product.deleted':
      tags.push(
        CacheTags.product(event.productId),
        CacheTags.productCollection(),
        CacheTags.categoryProducts(event.categorySlug),
        CacheTags.productReviews(event.productId)
      );
      break;

    case 'category.updated':
      tags.push(
        CacheTags.category(event.slug),
        CacheTags.categoryProducts(event.slug)
      );
      break;

    case 'review.created':
      tags.push(
        CacheTags.productReviews(event.productId),
        CacheTags.product(event.productId) // Product page shows review count
      );
      break;

    case 'brand.updated':
      tags.push(CacheTags.brand(event.brandId));
      break;
  }

  // Deduplicate and invalidate
  const uniqueTags = [...new Set(tags)];
  console.log(`Invalidating tags: ${uniqueTags.join(', ')}`);

  for (const tag of uniqueTags) {
    revalidateTag(tag);
  }

  return uniqueTags;
}
```

---

## Q18. (Advanced) How do you handle cache consistency in a distributed Next.js deployment with multiple regions?

**Scenario**: Your app is deployed to Vercel in multiple regions (US, EU, Asia). After a content update, US users see the new content but EU users still see the old content for minutes.

**Answer**:

```
Multi-Region Caching Challenge:

                   ┌─── US Edge ───┐
                   │  Cache: OLD    │ ← revalidation reached here first
  User (US) ──────▶│  Updated ✓    │
                   └───────────────┘

                   ┌─── EU Edge ───┐
                   │  Cache: OLD    │ ← stale! revalidation hasn't propagated
  User (EU) ──────▶│  Stale ✗      │
                   └───────────────┘

                   ┌── APAC Edge ──┐
                   │  Cache: OLD    │ ← also stale
  User (APAC) ────▶│  Stale ✗      │
                   └───────────────┘
```

**Strategy 1: Purge all edge caches on invalidation**:

```tsx
// lib/global-invalidation.ts

async function purgeGlobalCache(paths: string[]) {
  // Step 1: Invalidate Next.js Data Cache
  for (const path of paths) {
    revalidatePath(path);
  }

  // Step 2: Purge CDN edge caches in all regions
  if (process.env.VERCEL_URL) {
    // Vercel handles this automatically with revalidateTag/revalidatePath
    // Tags invalidation is globally consistent on Vercel
  } else if (process.env.CLOUDFLARE_ZONE_ID) {
    // Cloudflare: purge specific URLs across all edge locations
    await fetch(
      `https://api.cloudflare.com/client/v4/zones/${process.env.CLOUDFLARE_ZONE_ID}/purge_cache`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${process.env.CLOUDFLARE_API_TOKEN}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          files: paths.map(p => `${process.env.SITE_URL}${p}`),
        }),
      }
    );
  } else if (process.env.AWS_CLOUDFRONT_DISTRIBUTION_ID) {
    // CloudFront: create invalidation
    const { CloudFrontClient, CreateInvalidationCommand } = await import(
      '@aws-sdk/client-cloudfront'
    );
    const client = new CloudFrontClient({});
    await client.send(
      new CreateInvalidationCommand({
        DistributionId: process.env.AWS_CLOUDFRONT_DISTRIBUTION_ID,
        InvalidationBatch: {
          CallerReference: Date.now().toString(),
          Paths: {
            Quantity: paths.length,
            Items: paths,
          },
        },
      })
    );
  }
}
```

**Strategy 2: Use short TTLs with stale-while-revalidate**:

```tsx
// next.config.ts headers
async headers() {
  return [
    {
      source: '/:path*',
      headers: [
        {
          key: 'Cache-Control',
          // Short TTL (60s) means max staleness across regions is ~60s
          // SWR (3600s) means requests are always fast (served from cache)
          value: 'public, s-maxage=60, stale-while-revalidate=3600',
        },
      ],
    },
  ];
}
```

**Strategy 3: Region-aware caching with Redis Cluster**:

```tsx
// lib/regional-cache.ts
import Redis from 'ioredis';

const regions = {
  'us-east': new Redis(process.env.REDIS_US_URL!),
  'eu-west': new Redis(process.env.REDIS_EU_URL!),
  'ap-south': new Redis(process.env.REDIS_APAC_URL!),
};

const currentRegion = process.env.FLY_REGION || process.env.VERCEL_REGION || 'us-east';

export async function getCachedRegional<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number
): Promise<T> {
  const redis = regions[currentRegion as keyof typeof regions] || regions['us-east'];

  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const data = await fetcher();
  await redis.setex(key, ttl, JSON.stringify(data));
  return data;
}

export async function invalidateAllRegions(key: string) {
  await Promise.all(
    Object.values(regions).map(redis => redis.del(key))
  );
}
```

---

## Q19. (Advanced) How do you implement cache versioning for zero-downtime deployments?

**Scenario**: During deployment, the old version's cached data is incompatible with the new version's code (e.g., new fields, changed shape). You need cache versioning.

**Answer**:

```
Problem: Schema change during deploy

Old Version Cache:
  { name: "Widget", price: 9.99 }

New Version Code expects:
  { name: "Widget", price: { amount: 9.99, currency: "USD" } }

Result: Runtime error! 💥
```

**Solution: Version-prefixed cache keys**:

```tsx
// lib/cache-version.ts

// Increment this when cache data shape changes
const CACHE_VERSION = 'v3';

// Build hash from environment (changes on each deploy)
const BUILD_ID = process.env.NEXT_BUILD_ID || process.env.VERCEL_GIT_COMMIT_SHA || 'dev';

export function versionedKey(key: string, strategy: 'version' | 'build' = 'version'): string {
  switch (strategy) {
    case 'version':
      // Manual version — bump when schema changes
      return `${CACHE_VERSION}:${key}`;
    case 'build':
      // Build-based — new cache on every deploy (most aggressive)
      return `${BUILD_ID}:${key}`;
  }
}

export function versionedTags(tags: string[]): string[] {
  return tags.map(tag => `${CACHE_VERSION}:${tag}`);
}
```

```tsx
// Usage in fetch
const products = await fetch('https://api.example.com/products', {
  next: {
    tags: versionedTags(['products']),
  },
});

// Usage with custom cache
const data = await getCached(
  versionedKey('products:all'),
  () => fetchProducts(),
  { ttl: 3600 }
);
```

**Automated cache migration during deploy**:

```tsx
// scripts/cache-migration.ts

interface Migration {
  fromVersion: string;
  toVersion: string;
  migrate: (data: any) => any;
}

const migrations: Migration[] = [
  {
    fromVersion: 'v2',
    toVersion: 'v3',
    migrate: (data) => {
      // Transform price from number to object
      if (typeof data.price === 'number') {
        return {
          ...data,
          price: { amount: data.price, currency: 'USD' },
        };
      }
      return data;
    },
  },
];

async function runCacheMigration() {
  const redis = new Redis(process.env.REDIS_URL!);

  for (const migration of migrations) {
    console.log(`Migrating cache from ${migration.fromVersion} to ${migration.toVersion}`);

    let cursor = '0';
    let migrated = 0;

    do {
      const [newCursor, keys] = await redis.scan(
        cursor,
        'MATCH',
        `${migration.fromVersion}:*`,
        'COUNT',
        100
      );

      for (const oldKey of keys) {
        const data = await redis.get(oldKey);
        if (!data) continue;

        const parsed = JSON.parse(data);
        const migrated_data = migration.migrate(parsed);

        const newKey = oldKey.replace(migration.fromVersion, migration.toVersion);
        const ttl = await redis.ttl(oldKey);

        if (ttl > 0) {
          await redis.setex(newKey, ttl, JSON.stringify(migrated_data));
        }

        migrated++;
      }

      cursor = newCursor;
    } while (cursor !== '0');

    console.log(`Migrated ${migrated} entries from ${migration.fromVersion} to ${migration.toVersion}`);

    // Clean up old version keys (optional, with delay)
    // await cleanupOldVersionKeys(redis, migration.fromVersion);
  }
}
```

---

## Q20. (Advanced) How do you monitor cache performance and build a cache observability dashboard?

**Scenario**: Your application is in production but you have no visibility into cache hit rates, miss rates, or latency. You need to instrument caching for observability.

**Answer**:

```
Cache Observability Metrics:

┌─────────────────────────────────────────────────┐
│  Dashboard                                       │
│                                                 │
│  Hit Rate: ████████████████░░░░ 82%             │
│  Miss Rate: ████░░░░░░░░░░░░░░ 18%             │
│  Avg Latency (hit):  2ms                        │
│  Avg Latency (miss): 450ms                      │
│  Cache Size: 24,521 entries (1.2 GB)            │
│  Evictions/min: 12                              │
│                                                 │
│  Top Cache Misses:                              │
│  1. /api/products?page=47  (156 misses/hr)      │
│  2. /api/search?q=*        (98 misses/hr)       │
│  3. /api/user/profile      (87 misses/hr)       │
└─────────────────────────────────────────────────┘
```

**Instrumented fetch wrapper**:

```tsx
// lib/instrumented-fetch.ts

interface CacheMetrics {
  hits: number;
  misses: number;
  errors: number;
  totalLatencyMs: number;
  hitLatencyMs: number;
  missLatencyMs: number;
}

const metrics: Map<string, CacheMetrics> = new Map();

function getMetrics(key: string): CacheMetrics {
  if (!metrics.has(key)) {
    metrics.set(key, {
      hits: 0,
      misses: 0,
      errors: 0,
      totalLatencyMs: 0,
      hitLatencyMs: 0,
      missLatencyMs: 0,
    });
  }
  return metrics.get(key)!;
}

export async function instrumentedFetch(
  url: string,
  options?: RequestInit & { next?: { revalidate?: number; tags?: string[] } }
): Promise<Response> {
  const cacheKey = new URL(url).pathname;
  const m = getMetrics(cacheKey);
  const start = performance.now();

  try {
    const response = await fetch(url, options);
    const duration = performance.now() - start;

    // Detect cache hit vs miss based on response timing and headers
    const cacheStatus = response.headers.get('x-vercel-cache') ||
                         response.headers.get('cf-cache-status');
    const isHit = cacheStatus === 'HIT' || duration < 10; // <10ms likely a cache hit

    if (isHit) {
      m.hits++;
      m.hitLatencyMs += duration;
    } else {
      m.misses++;
      m.missLatencyMs += duration;
    }
    m.totalLatencyMs += duration;

    // Report to metrics service
    reportMetric('cache.request', {
      key: cacheKey,
      status: isHit ? 'hit' : 'miss',
      latencyMs: duration,
      httpStatus: response.status,
      tags: options?.next?.tags?.join(',') || 'none',
    });

    return response;
  } catch (error) {
    m.errors++;
    reportMetric('cache.error', { key: cacheKey, error: String(error) });
    throw error;
  }
}

// Report to your metrics service (DataDog, Prometheus, etc.)
function reportMetric(name: string, data: Record<string, any>) {
  if (process.env.DATADOG_API_KEY) {
    // Send to DataDog
    void fetch('https://api.datadoghq.com/api/v2/series', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'DD-API-KEY': process.env.DATADOG_API_KEY,
      },
      body: JSON.stringify({
        series: [{
          metric: `nextjs.${name}`,
          type: 0, // count
          points: [{ timestamp: Math.floor(Date.now() / 1000), value: 1 }],
          tags: Object.entries(data).map(([k, v]) => `${k}:${v}`),
        }],
      }),
    });
  }

  // Also log for local debugging
  if (process.env.NODE_ENV === 'development') {
    console.log(`[metric] ${name}`, data);
  }
}
```

**Cache health API endpoint**:

```tsx
// app/api/internal/cache-health/route.ts
import Redis from 'ioredis';

export const dynamic = 'force-dynamic';

export async function GET() {
  const redis = new Redis(process.env.REDIS_URL!);

  try {
    const info = await redis.info('stats');
    const memory = await redis.info('memory');
    const keyspace = await redis.info('keyspace');

    // Parse Redis info
    const parseInfo = (info: string) => {
      const result: Record<string, string> = {};
      info.split('\n').forEach(line => {
        const [key, value] = line.split(':');
        if (key && value) result[key.trim()] = value.trim();
      });
      return result;
    };

    const stats = parseInfo(info);
    const mem = parseInfo(memory);

    const hitRate = Number(stats.keyspace_hits) /
      (Number(stats.keyspace_hits) + Number(stats.keyspace_misses)) * 100;

    return Response.json({
      status: 'healthy',
      metrics: {
        hitRate: `${hitRate.toFixed(1)}%`,
        totalHits: stats.keyspace_hits,
        totalMisses: stats.keyspace_misses,
        usedMemory: mem.used_memory_human,
        peakMemory: mem.used_memory_peak_human,
        totalKeys: await redis.dbsize(),
        connectedClients: stats.connected_clients,
        evictedKeys: stats.evicted_keys,
        uptime: `${Math.floor(Number(stats.uptime_in_seconds) / 3600)}h`,
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return Response.json(
      { status: 'unhealthy', error: String(error) },
      { status: 503 }
    );
  } finally {
    redis.disconnect();
  }
}
```

**Prometheus metrics exporter**:

```tsx
// lib/cache-prometheus.ts
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

export const cacheHitCounter = new Counter({
  name: 'nextjs_cache_hits_total',
  help: 'Total cache hits',
  labelNames: ['layer', 'key'],
  registers: [registry],
});

export const cacheMissCounter = new Counter({
  name: 'nextjs_cache_misses_total',
  help: 'Total cache misses',
  labelNames: ['layer', 'key'],
  registers: [registry],
});

export const cacheLatencyHistogram = new Histogram({
  name: 'nextjs_cache_latency_seconds',
  help: 'Cache operation latency in seconds',
  labelNames: ['layer', 'operation'],
  buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5],
  registers: [registry],
});

export const cacheSizeGauge = new Gauge({
  name: 'nextjs_cache_size_bytes',
  help: 'Current cache size in bytes',
  labelNames: ['layer'],
  registers: [registry],
});

// Expose metrics endpoint
// app/api/metrics/route.ts
export async function GET() {
  const metrics = await registry.metrics();
  return new Response(metrics, {
    headers: { 'Content-Type': registry.contentType },
  });
}
```

**Key metrics to monitor in production**:

| Metric | Healthy Range | Alert Threshold | Action |
|--------|-------------|----------------|--------|
| Cache hit rate | > 80% | < 60% | Review cache configuration |
| Avg hit latency | < 5ms | > 50ms | Check Redis performance |
| Avg miss latency | < 500ms | > 2000ms | Optimize origin queries |
| Cache size | Growing slowly | > 80% memory | Implement eviction policy |
| Eviction rate | Low, steady | Sudden spikes | Increase memory or reduce TTLs |
| Error rate | < 0.1% | > 1% | Check Redis connectivity |
| Stale serve rate | < 20% | > 50% | Reduce revalidation intervals |

---
