# 11. Dynamic Routes & Static Generation

## Topic Introduction

Dynamic routes and static generation are at the heart of Next.js's rendering strategy. They let you build pages that combine the **performance of static HTML** with the **flexibility of dynamic content**. The App Router in Next.js 15/16 refines these concepts with `generateStaticParams`, `dynamicParams`, on-demand ISR via `revalidatePath`/`revalidateTag`, and draft mode — giving you fine-grained control over what's pre-rendered at build time and what's generated on-demand.

```
Dynamic Route Patterns:
┌───────────────────────────────────────────────────────────────────┐
│                                                                    │
│  [slug]           Single dynamic segment    /blog/hello-world     │
│  [...slug]        Catch-all segments        /docs/a/b/c           │
│  [[...slug]]      Optional catch-all        /docs OR /docs/a/b    │
│                                                                    │
│  Examples:                                                         │
│  app/blog/[slug]/page.tsx         → /blog/my-post                 │
│  app/docs/[...slug]/page.tsx      → /docs/getting-started/install │
│  app/shop/[[...slug]]/page.tsx    → /shop OR /shop/shoes/nike     │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

```
Static Generation Pipeline:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Build Time                                                      │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ generateStatic    │───▶│ Pre-render HTML  │                   │
│  │ Params()          │    │ + JSON payload    │                   │
│  │                   │    │                   │                   │
│  │ Returns list of   │    │ Stored in .next/  │                   │
│  │ {slug} values     │    │ server/app/...    │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  Runtime                                                         │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ Request arrives   │───▶│ dynamicParams?   │                   │
│  │ /blog/new-post    │    │                   │                   │
│  │ (not pre-rendered)│    │ true → generate   │                   │
│  │                   │    │        on demand  │                   │
│  │                   │    │ false → 404       │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  ISR (Incremental Static Regeneration)                          │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ Stale page served │───▶│ Background       │                   │
│  │ instantly          │    │ revalidation     │                   │
│  │                   │    │                   │                   │
│  │ revalidate: 60    │    │ Next request gets │                   │
│  │                   │    │ fresh page        │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  On-Demand Revalidation                                          │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ CMS webhook fires │───▶│ revalidatePath() │                   │
│  │                   │    │ revalidateTag()   │                   │
│  │ Content changed!  │    │                   │                   │
│  │                   │    │ Regenerate NOW    │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Next.js 15/16 Changes**:
- `params` is now a **Promise** that must be awaited: `const { slug } = await params`
- `searchParams` is also a **Promise** in page components
- `generateStaticParams` supports returning params for nested dynamic segments
- `dynamicParams` config controls whether non-pre-rendered paths return 404 or generate on-demand
- Improved ISR with tag-based revalidation across deployment regions
- Draft mode replaces the deprecated preview mode
- `unstable_cache` and `cacheTag`/`cacheLife` for granular cache control (Next.js 15+)

---

## Q1. (Beginner) What are the three types of dynamic route segments in Next.js, and when do you use each?

**Scenario**: You're building a documentation site with URLs like `/docs`, `/docs/getting-started`, `/docs/getting-started/installation`, and `/docs/api/components/button`.

**Answer**:

Next.js provides three dynamic segment patterns:

| Pattern | Syntax | Matches | Example URL | `params` value |
|---------|--------|---------|-------------|----------------|
| Dynamic | `[slug]` | One segment | `/blog/hello` | `{ slug: 'hello' }` |
| Catch-all | `[...slug]` | One or more | `/docs/a/b/c` | `{ slug: ['a','b','c'] }` |
| Optional catch-all | `[[...slug]]` | Zero or more | `/docs` or `/docs/a/b` | `{}` or `{ slug: ['a','b'] }` |

```
app/
├── blog/
│   └── [slug]/                    ← Single dynamic segment
│       └── page.tsx               → /blog/my-post
│                                  → /blog/another-post
│                                  ✗ /blog (needs app/blog/page.tsx)
│                                  ✗ /blog/a/b (too many segments)
│
├── docs/
│   └── [...slug]/                 ← Catch-all (one or more segments)
│       └── page.tsx               → /docs/intro
│                                  → /docs/getting-started/install
│                                  → /docs/api/components/button
│                                  ✗ /docs (zero segments — doesn't match!)
│
└── shop/
    └── [[...slug]]/               ← Optional catch-all (zero or more)
        └── page.tsx               → /shop (zero segments — matches!)
                                   → /shop/shoes
                                   → /shop/shoes/nike/air-max
```

```tsx
// app/blog/[slug]/page.tsx — Single dynamic segment
export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  // slug is always a string: "my-post"

  const post = await fetch(`https://api.example.com/posts/${slug}`).then(r => r.json());
  return <article><h1>{post.title}</h1></article>;
}

// app/docs/[...slug]/page.tsx — Catch-all segments
export default async function DocsPage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  // slug is always an array: ["getting-started", "installation"]

  const path = slug.join('/');
  const doc = await fetch(`https://cms.example.com/docs/${path}`).then(r => r.json());
  return <div><h1>{doc.title}</h1></div>;
}

// app/shop/[[...slug]]/page.tsx — Optional catch-all
export default async function ShopPage({
  params,
}: {
  params: Promise<{ slug?: string[] }>;
}) {
  const { slug } = await params;
  // slug is undefined (for /shop) or an array (for /shop/shoes/nike)

  if (!slug || slug.length === 0) {
    // Render shop homepage
    return <div><h1>All Products</h1></div>;
  }

  // Parse the category path
  const [category, ...rest] = slug;
  return <div><h1>Category: {category}</h1></div>;
}
```

**When to use each**:
- `[slug]` — Blog posts, product pages, user profiles (single-level URLs)
- `[...slug]` — Documentation, file browsers, nested categories (multi-level URLs that always have at least one segment)
- `[[...slug]]` — Same as catch-all but the base URL also needs to render content (e.g., `/shop` shows all products, `/shop/shoes` shows shoes)

---

## Q2. (Beginner) What is `generateStaticParams` and how does it pre-render dynamic routes at build time?

**Scenario**: Your blog has 500 posts. You want all of them pre-rendered as static HTML at build time for instant loading.

**Answer**:

`generateStaticParams` is an async function exported from a dynamic route's `page.tsx` (or `layout.tsx`). It tells Next.js which parameter values to pre-render at build time.

```tsx
// app/blog/[slug]/page.tsx
import { notFound } from 'next/navigation';

// This runs at BUILD TIME
export async function generateStaticParams() {
  // Fetch all blog post slugs from your CMS
  const posts = await fetch('https://api.example.com/posts', {
    next: { tags: ['posts'] },
  }).then((r) => r.json());

  // Return an array of { slug: string } objects
  return posts.map((post: { slug: string }) => ({
    slug: post.slug,
  }));
}

// This function is called once per slug during build
export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const post = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { tags: [`post-${slug}`] },
  }).then((r) => r.json());

  if (!post) notFound();

  return (
    <article className="max-w-3xl mx-auto">
      <h1 className="text-4xl font-bold">{post.title}</h1>
      <time className="text-gray-500">{post.publishedAt}</time>
      <div className="mt-6 prose" dangerouslySetInnerHTML={{ __html: post.content }} />
    </article>
  );
}
```

**Build output**:

```
Build log:
┌ ● /blog/[slug]
│   ├ /blog/getting-started-with-nextjs     (SSG)  2.1kB
│   ├ /blog/react-server-components         (SSG)  3.4kB
│   ├ /blog/understanding-caching           (SSG)  2.8kB
│   └ ... (497 more pages)
│
│ ● = Static (pre-rendered at build time)
```

**For catch-all routes**:

```tsx
// app/docs/[...slug]/page.tsx
export async function generateStaticParams() {
  const docs = await fetch('https://cms.example.com/docs/all').then(r => r.json());

  return docs.map((doc: { path: string }) => ({
    slug: doc.path.split('/'),  // ["getting-started", "installation"]
  }));

  // Example return value:
  // [
  //   { slug: ['getting-started'] },
  //   { slug: ['getting-started', 'installation'] },
  //   { slug: ['api', 'components', 'button'] },
  // ]
}
```

**For nested dynamic routes**:

```tsx
// app/blog/[category]/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());

  return posts.map((post: { category: string; slug: string }) => ({
    category: post.category,
    slug: post.slug,
  }));

  // Returns:
  // [
  //   { category: 'tech', slug: 'nextjs-15' },
  //   { category: 'design', slug: 'tailwind-tips' },
  // ]
}
```

**Key behavior**: `generateStaticParams` runs at build time (or during ISR regeneration). Pages returned by it are **statically generated** — they're just HTML files served from the CDN, with zero server rendering at request time.

---

## Q3. (Beginner) What is `dynamicParams` and how does it control fallback behavior for non-pre-rendered paths?

**Scenario**: You pre-render your top 100 blog posts at build time. A user visits `/blog/new-post-just-published` which wasn't in the build. What happens?

**Answer**:

The `dynamicParams` segment config controls whether dynamic routes accept parameters that weren't returned by `generateStaticParams`:

```tsx
// app/blog/[slug]/page.tsx

// Option 1: dynamicParams = true (DEFAULT)
// Non-pre-rendered paths are generated on-demand at request time
export const dynamicParams = true;

// Option 2: dynamicParams = false
// Non-pre-rendered paths return 404
export const dynamicParams = false;
```

```
dynamicParams = true (default):
┌────────────────────────────────────────────────────────────┐
│                                                             │
│  Request: /blog/my-pre-rendered-post                       │
│  ├── Found in build cache → Serve static HTML instantly    │
│                                                             │
│  Request: /blog/brand-new-post (not in generateStaticParams)│
│  ├── Not in cache → Render on demand (like SSR)            │
│  ├── Cache the result for future requests                   │
│  └── Next visitor gets static HTML                          │
│                                                             │
└────────────────────────────────────────────────────────────┘

dynamicParams = false:
┌────────────────────────────────────────────────────────────┐
│                                                             │
│  Request: /blog/my-pre-rendered-post                       │
│  ├── Found in build cache → Serve static HTML instantly    │
│                                                             │
│  Request: /blog/brand-new-post (not in generateStaticParams)│
│  ├── Not in cache → Return 404                              │
│  └── Page is NOT generated                                  │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

```tsx
// app/blog/[slug]/page.tsx
// Pre-render top posts, generate new ones on demand
export const dynamicParams = true; // default, but being explicit

export async function generateStaticParams() {
  // Only pre-render the top 100 most popular posts
  const topPosts = await fetch('https://api.example.com/posts?sort=popular&limit=100')
    .then((r) => r.json());

  return topPosts.map((post: { slug: string }) => ({
    slug: post.slug,
  }));
}

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const post = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { revalidate: 3600 }, // ISR: revalidate hourly
  }).then((r) => {
    if (!r.ok) return null;
    return r.json();
  });

  if (!post) {
    notFound(); // Show not-found.tsx
  }

  return <article>{/* ... */}</article>;
}
```

```tsx
// app/products/[sku]/page.tsx
// Only allow pre-rendered product SKUs (strict catalog)
export const dynamicParams = false;

export async function generateStaticParams() {
  const products = await fetch('https://api.example.com/products/all')
    .then((r) => r.json());

  return products.map((p: { sku: string }) => ({
    sku: p.sku,
  }));
}

// Any request to /products/INVALID_SKU will get a 404
// without even hitting the page component
```

**When to use `dynamicParams = false`**:
- Fixed catalog where all valid paths are known at build time
- Security: prevent enumeration of IDs
- When you want to guarantee all pages are pre-rendered (no runtime generation)

**When to use `dynamicParams = true` (default)**:
- Content is frequently added (blog posts, user profiles)
- Can't pre-render everything at build time (too many pages)
- Want "generate on first visit, cache forever" behavior

---

## Q4. (Beginner) How does ISR (Incremental Static Regeneration) work with the `revalidate` option in the App Router?

**Scenario**: Your pricing page should be static for performance but needs to update when prices change. You want it to revalidate every 5 minutes.

**Answer**:

ISR lets you serve **static pages** while updating them in the **background** at a specified interval. It combines the speed of static with the freshness of dynamic.

```
ISR Timeline (revalidate: 300 — 5 minutes):
────────────────────────────────────────────────────────────── Time

0s     Build: Page generated → cached
       │
60s    Request A → Serves cached page (instant) ✅
       │                  Page is 60s old (< 300s, still fresh)
       │
300s   REVALIDATION WINDOW OPENS (page is stale)
       │
350s   Request B → Serves STALE cached page (instant) ✅
       │                  BUT triggers background regeneration
       │                  ┌─────────────────────────────┐
       │                  │ Server re-renders page       │
       │                  │ New HTML cached              │
       │                  └─────────────────────────────┘
       │
360s   Request C → Serves NEW cached page ✅ (fresh content!)
```

**Time-based ISR**:

```tsx
// app/pricing/page.tsx
// The entire page is statically generated with ISR

export const revalidate = 300; // Revalidate every 5 minutes

export default async function PricingPage() {
  const plans = await fetch('https://api.example.com/pricing', {
    next: { revalidate: 300 }, // fetch-level revalidation (same as segment)
  }).then((r) => r.json());

  return (
    <div className="max-w-5xl mx-auto p-8">
      <h1 className="text-4xl font-bold text-center mb-12">Pricing</h1>
      <div className="grid grid-cols-3 gap-8">
        {plans.map((plan: any) => (
          <div key={plan.id} className="border rounded-2xl p-8 text-center">
            <h2 className="text-xl font-semibold">{plan.name}</h2>
            <p className="text-4xl font-bold mt-4">
              ${plan.price}
              <span className="text-sm text-gray-500">/month</span>
            </p>
            <ul className="mt-6 space-y-2 text-left">
              {plan.features.map((f: string, i: number) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-green-500">✓</span> {f}
                </li>
              ))}
            </ul>
            <button className="mt-8 w-full py-3 bg-blue-600 text-white rounded-lg">
              Get Started
            </button>
          </div>
        ))}
      </div>
      <p className="text-center text-sm text-gray-400 mt-8">
        Last updated: {new Date().toISOString()}
      </p>
    </div>
  );
}
```

**Segment-level vs fetch-level revalidation**:

```tsx
// Segment-level: applies to the entire route segment
export const revalidate = 300;

// Fetch-level: applies per-fetch (can have different values)
const pricing = await fetch('/api/pricing', { next: { revalidate: 300 } });
const features = await fetch('/api/features', { next: { revalidate: 3600 } }); // 1 hour

// The page revalidation = the MINIMUM of all revalidation values
// In this case: min(segment=300, pricing=300, features=3600) = 300 seconds
```

**Revalidation value quick reference**:

| Value | Behavior |
|-------|----------|
| `0` | Always dynamic (no caching) |
| `false` | Cache indefinitely (only revalidate on-demand) |
| `60` | Revalidate after 60 seconds |
| Not set | Inherits from parent layout or defaults to `false` |

---

## Q5. (Beginner) What is on-demand revalidation with `revalidatePath` and `revalidateTag`, and how does it differ from time-based ISR?

**Scenario**: An editor publishes a new blog post in your CMS. You don't want to wait 5 minutes for the time-based ISR — the site should update immediately.

**Answer**:

On-demand revalidation lets you **programmatically invalidate cached pages** when content changes, rather than waiting for a timer to expire.

```
Time-based ISR:
Content changes → Wait up to revalidate seconds → Page updates

On-demand ISR:
Content changes → CMS webhook → revalidatePath/Tag → Page updates IMMEDIATELY
```

**`revalidatePath`** — Revalidate a specific URL path:

```tsx
// app/api/revalidate/route.ts
import { revalidatePath } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const { secret, path } = await request.json();

  // Verify webhook secret
  if (secret !== process.env.REVALIDATION_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 });
  }

  // Revalidate the specific path
  revalidatePath(path);
  // Examples:
  // revalidatePath('/blog/my-post')       → revalidates this specific page
  // revalidatePath('/blog')               → revalidates the blog listing
  // revalidatePath('/', 'layout')         → revalidates everything using root layout
  // revalidatePath('/blog', 'layout')     → revalidates all /blog/* pages
  // revalidatePath('/blog', 'page')       → revalidates only /blog page

  return NextResponse.json({ revalidated: true, path });
}
```

**`revalidateTag`** — Revalidate all pages that use a specific cache tag:

```tsx
// app/blog/[slug]/page.tsx
export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Tag this fetch so it can be revalidated by tag
  const post = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { tags: [`post-${slug}`, 'posts'] }, // multiple tags
  }).then((r) => r.json());

  return <article>{/* ... */}</article>;
}
```

```tsx
// app/api/cms-webhook/route.ts
import { revalidateTag } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const payload = await request.json();

  // Verify webhook signature (CMS-specific)
  const signature = request.headers.get('x-webhook-signature');
  if (!verifySignature(payload, signature)) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
  }

  switch (payload.event) {
    case 'post.published':
    case 'post.updated':
      // Revalidate the specific post AND the listing page
      revalidateTag(`post-${payload.slug}`);
      revalidateTag('posts');
      break;

    case 'post.deleted':
      revalidateTag(`post-${payload.slug}`);
      revalidateTag('posts');
      break;

    case 'settings.updated':
      // Revalidate everything
      revalidateTag('site-settings');
      break;
  }

  return NextResponse.json({
    revalidated: true,
    event: payload.event,
  });
}

function verifySignature(payload: any, signature: string | null): boolean {
  // Implement CMS-specific signature verification
  return true; // placeholder
}
```

**Comparison**:

```
┌────────────────────┬──────────────────┬──────────────────────┐
│                     │ revalidatePath   │ revalidateTag        │
├────────────────────┼──────────────────┼──────────────────────┤
│ Granularity        │ URL path         │ Cache tag (semantic)  │
│ Multi-page         │ One path at a    │ All fetches with tag │
│                     │ time (or layout) │ across all pages     │
│ Use case           │ "Revalidate      │ "Revalidate all      │
│                     │  /blog/my-post"  │  pages using this    │
│                     │                  │  data source"        │
│ Best for           │ Known URLs       │ Data-driven cache    │
│                     │                  │ invalidation         │
└────────────────────┴──────────────────┴──────────────────────┘
```

---

## Q6. (Intermediate) How does `generateStaticParams` work with nested dynamic routes?

**Scenario**: Your e-commerce site has URLs like `/shop/[category]/[product]`. You need to pre-render the top categories and their top products.

**Answer**:

For nested dynamic routes, `generateStaticParams` can be defined at each level. The child level receives the parent's params, enabling efficient hierarchical generation.

```
app/shop/[category]/[product]/page.tsx

URL: /shop/shoes/nike-air-max-90
params: { category: 'shoes', product: 'nike-air-max-90' }
```

**Pattern 1: Generate all params at the leaf level**:

```tsx
// app/shop/[category]/[product]/page.tsx
export async function generateStaticParams() {
  // Return ALL combinations
  const products = await fetch('https://api.example.com/products/all').then(r => r.json());

  return products.map((p: { category: string; slug: string }) => ({
    category: p.category,
    product: p.slug,
  }));

  // Returns:
  // [
  //   { category: 'shoes', product: 'nike-air-max-90' },
  //   { category: 'shoes', product: 'adidas-ultraboost' },
  //   { category: 'clothing', product: 'levis-501' },
  // ]
}
```

**Pattern 2: Hierarchical generation (parent passes to child)**:

```tsx
// app/shop/[category]/layout.tsx
export async function generateStaticParams() {
  const categories = await fetch('https://api.example.com/categories').then(r => r.json());

  return categories.map((c: { slug: string }) => ({
    category: c.slug,
  }));

  // Returns: [{ category: 'shoes' }, { category: 'clothing' }, ...]
}
```

```tsx
// app/shop/[category]/[product]/page.tsx
export async function generateStaticParams({
  params,
}: {
  params: { category: string }; // receives parent params
}) {
  // Fetch products for THIS category only
  const products = await fetch(
    `https://api.example.com/categories/${params.category}/products`
  ).then(r => r.json());

  return products.map((p: { slug: string }) => ({
    product: p.slug,
  }));

  // Returns for category='shoes':
  // [{ product: 'nike-air-max-90' }, { product: 'adidas-ultraboost' }]
  //
  // Next.js combines with parent: { category: 'shoes', product: 'nike-air-max-90' }
}
```

**Pattern 3: Catch-all with nested paths**:

```tsx
// app/docs/[...slug]/page.tsx
export async function generateStaticParams() {
  const docs = await fetch('https://cms.example.com/docs/sitemap').then(r => r.json());

  return docs.map((doc: { path: string }) => ({
    slug: doc.path.split('/'),
  }));

  // Returns:
  // [
  //   { slug: ['getting-started'] },
  //   { slug: ['getting-started', 'installation'] },
  //   { slug: ['api', 'reference'] },
  //   { slug: ['api', 'reference', 'components'] },
  //   { slug: ['api', 'reference', 'components', 'button'] },
  // ]
}

export default async function DocsPage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  const path = slug.join('/');

  const doc = await fetch(`https://cms.example.com/docs/${path}`, {
    next: { tags: [`doc-${path}`] },
  }).then(r => r.json());

  if (!doc) notFound();

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumbs from slug */}
      <nav className="flex gap-2 text-sm text-gray-500 mb-6">
        <a href="/docs">Docs</a>
        {slug.map((segment, i) => (
          <span key={i}>
            <span className="mx-1">/</span>
            <a href={`/docs/${slug.slice(0, i + 1).join('/')}`}>
              {segment.replace(/-/g, ' ')}
            </a>
          </span>
        ))}
      </nav>
      <h1 className="text-3xl font-bold">{doc.title}</h1>
      <div className="prose mt-6" dangerouslySetInnerHTML={{ __html: doc.content }} />
    </div>
  );
}
```

**Build optimization**: When using hierarchical generation, Next.js can deduplicate fetch requests. If `generateStaticParams` in the child calls the same API as the parent, the response is cached and shared.

---

## Q7. (Intermediate) How do you implement ISR with tag-based revalidation for a content-heavy site?

**Scenario**: Your news site has articles, categories, authors, and a homepage that shows "trending" articles. When an article is updated, you need to revalidate: the article page, the category listing, the author page, and the homepage (if the article is trending).

**Answer**:

Tag-based revalidation creates a **dependency graph** between content and pages. When content changes, you revalidate all pages that depend on it.

```
Content-to-Page Dependency Graph:
┌──────────────┐
│  Article #42  │
│  tags:        │
│  • article-42 │─────────▶  /articles/breaking-news  (article page)
│  • cat-tech   │─────────▶  /categories/tech          (category listing)
│  • author-jane│─────────▶  /authors/jane              (author page)
│  • trending   │─────────▶  /                           (homepage trending)
│  • articles   │─────────▶  /articles                   (article listing)
└──────────────┘
```

**Setting up cache tags on pages**:

```tsx
// app/articles/[slug]/page.tsx
export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const article = await fetch(`https://api.example.com/articles/${slug}`, {
    next: {
      tags: [
        `article-${slug}`,           // specific article
        `cat-${article?.category}`,   // category dependency
        `author-${article?.authorId}`, // author dependency
        'articles',                    // global articles collection
      ],
    },
  }).then(async (r) => {
    if (!r.ok) return null;
    return r.json();
  });

  if (!article) notFound();

  return (
    <article>
      <h1 className="text-4xl font-bold">{article.title}</h1>
      <div className="flex gap-4 text-gray-500 mt-2">
        <span>By {article.author.name}</span>
        <span>{article.category}</span>
        <time>{new Date(article.publishedAt).toLocaleDateString()}</time>
      </div>
      <div className="prose mt-8" dangerouslySetInnerHTML={{ __html: article.content }} />
    </article>
  );
}
```

```tsx
// app/categories/[category]/page.tsx
export default async function CategoryPage({
  params,
}: {
  params: Promise<{ category: string }>;
}) {
  const { category } = await params;

  const articles = await fetch(
    `https://api.example.com/articles?category=${category}`,
    {
      next: {
        tags: [`cat-${category}`, 'articles'],
      },
    }
  ).then((r) => r.json());

  return (
    <div>
      <h1 className="text-3xl font-bold capitalize">{category}</h1>
      <div className="grid gap-6 mt-8">
        {articles.map((article: any) => (
          <a key={article.id} href={`/articles/${article.slug}`} className="border p-4 rounded-lg">
            <h2 className="font-semibold">{article.title}</h2>
            <p className="text-gray-600 mt-1">{article.excerpt}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
```

```tsx
// app/page.tsx (Homepage with trending)
export default async function HomePage() {
  const trending = await fetch('https://api.example.com/articles?trending=true&limit=5', {
    next: { tags: ['trending', 'articles'] },
  }).then((r) => r.json());

  const latestNews = await fetch('https://api.example.com/articles?limit=10', {
    next: { tags: ['articles'] },
  }).then((r) => r.json());

  return (
    <div>
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-6">Trending Now</h2>
        {/* trending articles */}
      </section>
      <section>
        <h2 className="text-2xl font-bold mb-6">Latest News</h2>
        {/* latest articles */}
      </section>
    </div>
  );
}
```

**CMS webhook handler with tag-based revalidation**:

```tsx
// app/api/cms-webhook/route.ts
import { revalidateTag } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

interface CMSWebhookPayload {
  event: 'article.created' | 'article.updated' | 'article.deleted' | 'article.published';
  data: {
    slug: string;
    category: string;
    authorId: string;
    isTrending: boolean;
    previousCategory?: string; // if category changed
  };
}

export async function POST(request: NextRequest) {
  const signature = request.headers.get('x-cms-signature');
  if (!verifyWebhookSignature(signature, request)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const payload: CMSWebhookPayload = await request.json();
  const tagsToRevalidate: string[] = [];

  switch (payload.event) {
    case 'article.published':
    case 'article.updated':
      // Always revalidate the article itself
      tagsToRevalidate.push(`article-${payload.data.slug}`);

      // Revalidate the category listing
      tagsToRevalidate.push(`cat-${payload.data.category}`);

      // If category changed, revalidate old category too
      if (payload.data.previousCategory) {
        tagsToRevalidate.push(`cat-${payload.data.previousCategory}`);
      }

      // Revalidate author page
      tagsToRevalidate.push(`author-${payload.data.authorId}`);

      // Revalidate article listings
      tagsToRevalidate.push('articles');

      // If trending, revalidate homepage trending section
      if (payload.data.isTrending) {
        tagsToRevalidate.push('trending');
      }
      break;

    case 'article.deleted':
      tagsToRevalidate.push(`article-${payload.data.slug}`);
      tagsToRevalidate.push(`cat-${payload.data.category}`);
      tagsToRevalidate.push('articles');
      if (payload.data.isTrending) {
        tagsToRevalidate.push('trending');
      }
      break;
  }

  // Revalidate all tags
  const results = tagsToRevalidate.map((tag) => {
    revalidateTag(tag);
    return tag;
  });

  console.log(`[Revalidation] Event: ${payload.event}, Tags: ${results.join(', ')}`);

  return NextResponse.json({
    revalidated: true,
    tags: results,
  });
}

function verifyWebhookSignature(signature: string | null, request: NextRequest): boolean {
  // Implement CMS-specific signature verification
  return signature === process.env.CMS_WEBHOOK_SECRET;
}
```

This approach ensures that when an article is updated, all pages showing that article's data are refreshed — the article page, its category listing, the author page, and the homepage trending section if applicable.

---

## Q8. (Intermediate) How do you implement Draft Mode (preview mode) for previewing unpublished content from a CMS?

**Scenario**: Content editors need to preview unpublished articles on the live site before publishing them. The preview should bypass ISR caching and show the latest draft content.

**Answer**:

Draft mode in Next.js 15+ enables a per-user bypass of the static cache. When enabled, pages render dynamically with fresh data — perfect for CMS previews.

```
Normal Mode (Default):
Request → Check cache → Serve static HTML (fast, cached)

Draft Mode (Enabled):
Request → Skip cache → Server render with draft data (fresh, uncached)
```

**Step 1: Enable draft mode via API route**:

```tsx
// app/api/draft/enable/route.ts
import { draftMode } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const secret = searchParams.get('secret');
  const slug = searchParams.get('slug');
  const type = searchParams.get('type') || 'article';

  // Validate the secret token
  if (secret !== process.env.DRAFT_MODE_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 });
  }

  // Validate that the content exists
  const content = await fetch(
    `https://api.example.com/preview/${type}/${slug}`,
    {
      headers: {
        Authorization: `Bearer ${process.env.CMS_PREVIEW_TOKEN}`,
      },
    }
  );

  if (!content.ok) {
    return NextResponse.json({ error: 'Content not found' }, { status: 404 });
  }

  // Enable Draft Mode — sets a cookie
  const draft = await draftMode();
  draft.enable();

  // Redirect to the content page
  const redirectUrl = type === 'article' ? `/articles/${slug}` : `/${type}/${slug}`;
  return NextResponse.redirect(new URL(redirectUrl, request.url));
}
```

**Step 2: Disable draft mode**:

```tsx
// app/api/draft/disable/route.ts
import { draftMode } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const draft = await draftMode();
  draft.disable();

  const redirectTo = request.nextUrl.searchParams.get('redirect') || '/';
  return NextResponse.redirect(new URL(redirectTo, request.url));
}
```

**Step 3: Use draft mode in page components**:

```tsx
// app/articles/[slug]/page.tsx
import { draftMode } from 'next/headers';
import { notFound } from 'next/navigation';

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const { isEnabled: isDraftMode } = await draftMode();

  // Choose API endpoint based on draft mode
  const apiUrl = isDraftMode
    ? `https://api.example.com/preview/articles/${slug}` // includes drafts
    : `https://api.example.com/articles/${slug}`;        // only published

  const article = await fetch(apiUrl, {
    headers: isDraftMode
      ? { Authorization: `Bearer ${process.env.CMS_PREVIEW_TOKEN}` }
      : {},
    // Don't cache in draft mode
    cache: isDraftMode ? 'no-store' : 'force-cache',
    next: isDraftMode ? undefined : { tags: [`article-${slug}`], revalidate: 3600 },
  }).then((r) => {
    if (!r.ok) return null;
    return r.json();
  });

  if (!article) notFound();

  return (
    <article className="max-w-3xl mx-auto p-6">
      {/* Draft mode indicator banner */}
      {isDraftMode && (
        <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-4 mb-8 flex items-center justify-between">
          <div>
            <p className="font-semibold text-yellow-800">Draft Mode</p>
            <p className="text-sm text-yellow-700">
              You are viewing unpublished content. This page is not cached.
            </p>
          </div>
          <a
            href={`/api/draft/disable?redirect=/articles/${slug}`}
            className="px-4 py-2 bg-yellow-600 text-white rounded-lg text-sm hover:bg-yellow-700"
          >
            Exit Preview
          </a>
        </div>
      )}

      {/* Draft status badge */}
      {article.status === 'draft' && (
        <span className="inline-block bg-orange-100 text-orange-700 text-xs font-medium px-2 py-1 rounded mb-4">
          DRAFT
        </span>
      )}

      <h1 className="text-4xl font-bold">{article.title}</h1>
      <div className="prose mt-8" dangerouslySetInnerHTML={{ __html: article.content }} />
    </article>
  );
}
```

**CMS preview URL setup** (e.g., in Sanity/Contentful admin):

```
Preview URL:
https://yoursite.com/api/draft/enable?secret=YOUR_SECRET&slug={slug}&type=article

This URL is configured in your CMS dashboard so editors can click
"Open Preview" from the editor.
```

**Draft mode cookie details**:
- Sets a `__prerender_bypass` cookie
- Valid for the current browser session
- Not shared between users (secure, httpOnly)
- Automatically disables after session ends
- Can be explicitly disabled via the disable endpoint

---

## Q9. (Intermediate) How do you optimize `generateStaticParams` for large sites with 100K+ pages?

**Scenario**: Your e-commerce site has 200,000 products. Running `generateStaticParams` with all products at build time takes over 30 minutes and frequently times out.

**Answer**:

For very large sites, you need a tiered approach: pre-render the most important pages at build time, and let the rest generate on-demand.

```
Tiered Static Generation Strategy:
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Tier 1: Build Time (top ~5,000 pages)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Homepage, category pages                              │ │
│  │ • Top 1000 products (by traffic/revenue)               │ │
│  │ • Top 500 blog posts                                    │ │
│  │ • All static pages (/about, /contact, etc.)            │ │
│  │                                                         │ │
│  │ Result: Pre-rendered, instant on first visit            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Tier 2: On-Demand Generation (remaining ~195,000 pages)    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • dynamicParams = true (generate on first visit)        │ │
│  │ • Once generated, cached like Tier 1                    │ │
│  │ • ISR keeps them fresh                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**:

```tsx
// app/products/[slug]/page.tsx
export const dynamicParams = true; // Allow on-demand generation

export async function generateStaticParams() {
  // Only pre-render top products (by traffic or revenue)
  const topProducts = await fetch(
    'https://api.example.com/products?sort=popular&limit=1000',
    { next: { tags: ['products'] } }
  ).then((r) => r.json());

  return topProducts.map((p: { slug: string }) => ({
    slug: p.slug,
  }));
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const product = await fetch(`https://api.example.com/products/${slug}`, {
    next: { tags: [`product-${slug}`, 'products'], revalidate: 3600 },
  }).then((r) => {
    if (!r.ok) return null;
    return r.json();
  });

  if (!product) notFound();

  return <div>{/* product page content */}</div>;
}
```

**Pattern: Paginated `generateStaticParams` for very large catalogs**:

```tsx
// app/products/[slug]/page.tsx
export async function generateStaticParams() {
  const params: { slug: string }[] = [];
  let page = 1;
  const perPage = 500;
  let hasMore = true;

  // Paginate through the API to avoid timeouts
  while (hasMore && params.length < 5000) { // cap at 5000
    const batch = await fetch(
      `https://api.example.com/products?page=${page}&per_page=${perPage}&sort=popular`,
    ).then((r) => r.json());

    if (batch.length === 0) {
      hasMore = false;
    } else {
      params.push(...batch.map((p: { slug: string }) => ({ slug: p.slug })));
      page++;
    }
  }

  console.log(`[generateStaticParams] Pre-rendering ${params.length} products`);
  return params;
}
```

**Pattern: Category-based hierarchical generation**:

```tsx
// app/shop/[category]/page.tsx
export async function generateStaticParams() {
  // Pre-render ALL category pages (usually < 100)
  const categories = await fetch('https://api.example.com/categories').then(r => r.json());
  return categories.map((c: { slug: string }) => ({ category: c.slug }));
}

// app/shop/[category]/[product]/page.tsx
export async function generateStaticParams({
  params,
}: {
  params: { category: string };
}) {
  // Pre-render top 50 products per category
  const products = await fetch(
    `https://api.example.com/categories/${params.category}/products?sort=popular&limit=50`
  ).then(r => r.json());

  return products.map((p: { slug: string }) => ({ product: p.slug }));
}
```

**Build time optimization tips**:

```
Optimization                          │ Impact
──────────────────────────────────────┼──────────────
Limit generateStaticParams to top N   │ Build: 30min → 5min
Use parallel data fetching            │ Build: 5min → 2min
Cache API responses across builds     │ Build: 2min → 1min
Use Vercel's incremental builds       │ Rebuild only changed pages
Set dynamicParams = true              │ Rest generated on-demand
Use next.config.ts staticPageGen*     │ Control concurrency
```

```ts
// next.config.ts
const nextConfig = {
  experimental: {
    // Control how many pages are generated in parallel during build
    staticGenerationMaxConcurrency: 25, // default varies by platform
  },
};
```

---

## Q10. (Intermediate) How do you handle `searchParams` in the App Router and understand its impact on static vs dynamic rendering?

**Scenario**: Your product listing page supports filters like `/products?category=shoes&sort=price&page=2`. You need to handle these search parameters while maintaining performance.

**Answer**:

In Next.js 15+, `searchParams` is a **Promise** that must be awaited. Importantly, **accessing `searchParams` makes a page dynamic** — it cannot be statically generated because the parameters vary per request.

```tsx
// app/products/page.tsx
// This page is DYNAMIC because it reads searchParams
export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;

  const category = typeof params.category === 'string' ? params.category : undefined;
  const sort = typeof params.sort === 'string' ? params.sort : 'popular';
  const page = typeof params.page === 'string' ? parseInt(params.page, 10) : 1;
  const perPage = 24;

  // Build API URL with search params
  const apiUrl = new URL('https://api.example.com/products');
  if (category) apiUrl.searchParams.set('category', category);
  apiUrl.searchParams.set('sort', sort);
  apiUrl.searchParams.set('page', page.toString());
  apiUrl.searchParams.set('per_page', perPage.toString());

  const data = await fetch(apiUrl.toString(), {
    next: { revalidate: 60 }, // still use ISR for fresh data
  }).then((r) => r.json());

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Products</h1>

      {/* Filters */}
      <div className="flex gap-4 mb-8">
        <FilterLink label="All" href="/products" active={!category} />
        <FilterLink label="Shoes" href="/products?category=shoes" active={category === 'shoes'} />
        <FilterLink label="Clothing" href="/products?category=clothing" active={category === 'clothing'} />
      </div>

      {/* Sort */}
      <div className="flex gap-2 mb-6">
        <SortLink label="Popular" sort="popular" currentSort={sort} category={category} />
        <SortLink label="Price: Low" sort="price_asc" currentSort={sort} category={category} />
        <SortLink label="Price: High" sort="price_desc" currentSort={sort} category={category} />
        <SortLink label="Newest" sort="newest" currentSort={sort} category={category} />
      </div>

      {/* Product grid */}
      <div className="grid grid-cols-4 gap-6">
        {data.products.map((product: any) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>

      {/* Pagination */}
      <Pagination
        currentPage={page}
        totalPages={data.totalPages}
        baseUrl={`/products${category ? `?category=${category}&sort=${sort}` : `?sort=${sort}`}`}
      />
    </div>
  );
}

function FilterLink({ label, href, active }: { label: string; href: string; active: boolean }) {
  return (
    <a
      href={href}
      className={`px-4 py-2 rounded-full text-sm ${
        active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {label}
    </a>
  );
}

function SortLink({
  label,
  sort,
  currentSort,
  category,
}: {
  label: string;
  sort: string;
  currentSort: string;
  category?: string;
}) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  params.set('sort', sort);

  return (
    <a
      href={`/products?${params.toString()}`}
      className={`text-sm ${currentSort === sort ? 'font-bold text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
    >
      {label}
    </a>
  );
}

function Pagination({
  currentPage,
  totalPages,
  baseUrl,
}: {
  currentPage: number;
  totalPages: number;
  baseUrl: string;
}) {
  return (
    <div className="flex gap-2 justify-center mt-12">
      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
        <a
          key={page}
          href={`${baseUrl}&page=${page}`}
          className={`w-10 h-10 flex items-center justify-center rounded ${
            page === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
          }`}
        >
          {page}
        </a>
      ))}
    </div>
  );
}

function ProductCard({ product }: { product: any }) {
  return (
    <a href={`/products/${product.slug}`} className="group">
      <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
        {/* product image */}
      </div>
      <h3 className="mt-2 font-medium group-hover:text-blue-600">{product.name}</h3>
      <p className="text-green-600 font-semibold">${product.price}</p>
    </a>
  );
}
```

**Static vs Dynamic rendering impact**:

```
Page rendering decision:
┌─────────────────────────────────────────────────────┐
│                                                      │
│  Does the page read searchParams?                   │
│  ├── No  → STATIC (pre-rendered at build time)      │
│  └── Yes → DYNAMIC (rendered at request time)       │
│                                                      │
│  Other factors that force dynamic rendering:         │
│  • headers() or cookies() used                       │
│  • fetch with { cache: 'no-store' }                  │
│  • export const dynamic = 'force-dynamic'           │
│  • Route has middleware that reads cookies            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Tip**: If you want to keep the listing page **static** and handle filters client-side, move the filter logic to a Client Component and fetch filtered data via client-side fetching.

---

## Q11. (Intermediate) How do you implement a sitemap and robots.txt for statically generated pages?

**Scenario**: Your site has 50,000 product pages with ISR. You need a dynamic sitemap that includes all pages (pre-rendered and on-demand generated) for SEO.

**Answer**:

Next.js 15+ supports programmatic sitemap generation via `sitemap.ts` and `robots.ts` files.

```tsx
// app/sitemap.ts
import type { MetadataRoute } from 'next';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: 'https://example.com',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: 'https://example.com/about',
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.5,
    },
    {
      url: 'https://example.com/contact',
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.5,
    },
  ];

  // Dynamic pages: fetch all products
  const products = await fetch('https://api.example.com/products/sitemap').then(r => r.json());
  const productPages: MetadataRoute.Sitemap = products.map((p: any) => ({
    url: `https://example.com/products/${p.slug}`,
    lastModified: new Date(p.updatedAt),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  // Blog posts
  const posts = await fetch('https://api.example.com/posts/sitemap').then(r => r.json());
  const postPages: MetadataRoute.Sitemap = posts.map((p: any) => ({
    url: `https://example.com/blog/${p.slug}`,
    lastModified: new Date(p.updatedAt),
    changeFrequency: 'monthly' as const,
    priority: 0.6,
  }));

  return [...staticPages, ...productPages, ...postPages];
}
```

**For sites with 50,000+ URLs, use multiple sitemaps**:

```tsx
// app/sitemap.ts — Sitemap index
import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  // This generates a sitemap index pointing to individual sitemaps
  return [
    { url: 'https://example.com/sitemaps/static.xml', lastModified: new Date() },
    { url: 'https://example.com/sitemaps/products-1.xml', lastModified: new Date() },
    { url: 'https://example.com/sitemaps/products-2.xml', lastModified: new Date() },
    { url: 'https://example.com/sitemaps/blog.xml', lastModified: new Date() },
  ];
}
```

```tsx
// app/sitemaps/[id]/route.ts — Generate individual sitemap chunks
import { NextRequest, NextResponse } from 'next/server';

const URLS_PER_SITEMAP = 10000; // Google limit is 50,000

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  let urls: Array<{ loc: string; lastmod: string; priority: number }> = [];

  if (id === 'static') {
    urls = [
      { loc: 'https://example.com', lastmod: new Date().toISOString(), priority: 1.0 },
      { loc: 'https://example.com/about', lastmod: new Date().toISOString(), priority: 0.5 },
    ];
  } else if (id.startsWith('products-')) {
    const page = parseInt(id.replace('products-', ''));
    const products = await fetch(
      `https://api.example.com/products?page=${page}&per_page=${URLS_PER_SITEMAP}`
    ).then(r => r.json());

    urls = products.map((p: any) => ({
      loc: `https://example.com/products/${p.slug}`,
      lastmod: new Date(p.updatedAt).toISOString(),
      priority: 0.8,
    }));
  } else if (id === 'blog') {
    const posts = await fetch('https://api.example.com/posts/all').then(r => r.json());
    urls = posts.map((p: any) => ({
      loc: `https://example.com/blog/${p.slug}`,
      lastmod: new Date(p.updatedAt).toISOString(),
      priority: 0.6,
    }));
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(u => `  <url>
    <loc>${u.loc}</loc>
    <lastmod>${u.lastmod}</lastmod>
    <priority>${u.priority}</priority>
  </url>`).join('\n')}
</urlset>`;

  return new NextResponse(xml, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}
```

```tsx
// app/robots.ts
import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/admin/', '/dashboard/'],
      },
      {
        userAgent: 'Googlebot',
        allow: '/',
        disallow: ['/api/'],
      },
    ],
    sitemap: 'https://example.com/sitemap.xml',
  };
}
```

---

## Q12. (Intermediate) How do you use the `dynamic`, `revalidate`, and `fetchCache` route segment configuration options?

**Scenario**: Your application has routes with different rendering requirements — some must be fully static, some must always be dynamic, and some need specific caching behaviors.

**Answer**:

Route segment config exports let you control rendering behavior at the route level:

```tsx
// Force static generation (error if any dynamic API is used)
export const dynamic = 'force-static';

// Force dynamic rendering (always server-render)
export const dynamic = 'force-dynamic';

// Default: auto-detect based on usage
export const dynamic = 'auto';

// Error if accidentally cached
export const dynamic = 'error';
```

| Config | Values | Effect |
|--------|--------|--------|
| `dynamic` | `'auto'`, `'force-dynamic'`, `'force-static'`, `'error'` | Controls static vs dynamic |
| `revalidate` | `false`, `0`, `number` | ISR revalidation interval |
| `fetchCache` | `'auto'`, `'force-no-store'`, `'only-cache'`, etc. | Override fetch caching |
| `runtime` | `'nodejs'`, `'edge'` | Execution runtime |
| `preferredRegion` | `'auto'`, `'home'`, `'iad1'`, etc. | Deployment region |
| `maxDuration` | `number` (seconds) | Max execution time |

```tsx
// app/dashboard/page.tsx — Always dynamic (shows real-time data)
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default async function DashboardPage() {
  // Always fetches fresh data on every request
  const data = await fetch('https://api.example.com/realtime-stats');
  // ...
}
```

```tsx
// app/about/page.tsx — Fully static (never changes)
export const dynamic = 'force-static';
export const revalidate = false; // never revalidate

export default function AboutPage() {
  return <div>About us content...</div>;
}
```

```tsx
// app/pricing/page.tsx — ISR with 5-minute revalidation
export const revalidate = 300;

export default async function PricingPage() {
  const pricing = await fetch('https://api.example.com/pricing');
  // Page is static but refreshes every 5 minutes
  // ...
}
```

```tsx
// app/api/search/route.ts — Edge runtime for global low-latency
export const runtime = 'edge';
export const preferredRegion = ['iad1', 'sfo1', 'lhr1']; // multi-region

export async function GET(request: Request) {
  // Runs at the edge closest to the user
  // ...
}
```

```tsx
// app/reports/generate/page.tsx — Long-running generation
export const maxDuration = 60; // Allow up to 60 seconds
export const dynamic = 'force-dynamic';

export default async function ReportPage() {
  // Heavy data processing that may take a while
  const report = await generateReport();
  // ...
}
```

**Interaction between segment config and fetch options**:

```
Precedence (highest to lowest):
1. Individual fetch() options:   fetch(url, { cache: 'no-store' })
2. fetchCache segment config:    export const fetchCache = 'force-no-store'
3. dynamic segment config:       export const dynamic = 'force-dynamic'
4. revalidate segment config:    export const revalidate = 60
5. Default behavior:             auto-detect
```

---

## Q13. (Advanced) How do you architect static generation for a large e-commerce site with categories, products, variants, and regional pricing?

**Scenario**: You're building an e-commerce platform with 500 categories, 200K products (each with 3-5 variants), pricing that varies by region (US, EU, UK, JP), and content in 4 languages. Build time must stay under 10 minutes.

**Answer**:

This requires a multi-dimensional static generation strategy with careful tiering and caching.

```
URL Structure:
/[locale]/shop/[category]/[product]
/en/shop/shoes/nike-air-max-90
/de/shop/schuhe/nike-air-max-90
/ja/shop/靴/nike-air-max-90

Total potential pages:
  4 locales × 500 categories × 200K products = 400,000,000 URLs (!!)
  Obviously, we can't pre-render all of these.
```

```
Tiered Generation Strategy:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Tier 1: BUILD TIME (~2,000 pages, ~3 minutes)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • All category pages (4 locales × 500 = 2,000)             │ │
│  │ • Homepage per locale (4 pages)                             │ │
│  │ • Static pages (/about, /contact, etc.)                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Tier 2: ON-DEMAND + ISR (~10,000 popular products)             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • dynamicParams = true                                      │ │
│  │ • Generated on first visit, cached for 24 hours             │ │
│  │ • Revalidated via CMS webhook                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Tier 3: FULLY DYNAMIC (long-tail products)                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • Products with < 10 views/month                            │ │
│  │ • Still uses ISR, but shorter revalidation                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Category pages (Tier 1 — all pre-rendered)**:

```tsx
// app/[locale]/shop/[category]/page.tsx
export async function generateStaticParams() {
  const locales = ['en', 'de', 'fr', 'ja'];
  const categories = await fetch('https://api.example.com/categories').then(r => r.json());

  // Generate all locale × category combinations
  return locales.flatMap((locale) =>
    categories.map((cat: { slug: string; localizedSlugs: Record<string, string> }) => ({
      locale,
      category: cat.localizedSlugs[locale] || cat.slug,
    }))
  );
}

export const revalidate = 3600; // Revalidate categories hourly

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ locale: string; category: string }>;
}) {
  const { locale, category } = await params;

  const [categoryData, products] = await Promise.all([
    fetch(`https://api.example.com/categories/${category}?locale=${locale}`, {
      next: { tags: [`cat-${category}`] },
    }).then(r => r.json()),
    fetch(`https://api.example.com/products?category=${category}&locale=${locale}&limit=48`, {
      next: { tags: [`cat-${category}-products`, 'products'] },
    }).then(r => r.json()),
  ]);

  return (
    <div>
      <h1>{categoryData.name}</h1>
      <p>{categoryData.description}</p>
      <div className="grid grid-cols-4 gap-6">
        {products.map((p: any) => (
          <a key={p.id} href={`/${locale}/shop/${category}/${p.slug}`}>
            <h3>{p.name}</h3>
            <p>{formatPrice(p.price, locale)}</p>
          </a>
        ))}
      </div>
    </div>
  );
}

function formatPrice(price: number, locale: string): string {
  const currencyMap: Record<string, string> = {
    en: 'USD', de: 'EUR', fr: 'EUR', ja: 'JPY',
  };
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currencyMap[locale] || 'USD',
  }).format(price);
}
```

**Product pages (Tier 2 — on-demand with ISR)**:

```tsx
// app/[locale]/shop/[category]/[product]/page.tsx
export const dynamicParams = true; // Generate on-demand
export const revalidate = 86400; // 24-hour ISR

// Don't pre-render any product pages at build time
// (they'll be generated on first visit)
// Optionally, pre-render top 100:
export async function generateStaticParams() {
  // Pre-render ONLY for the default locale and top products
  const topProducts = await fetch(
    'https://api.example.com/products?sort=popular&limit=100'
  ).then(r => r.json());

  return topProducts.map((p: any) => ({
    locale: 'en',
    category: p.categorySlug,
    product: p.slug,
  }));
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; category: string; product: string }>;
}) {
  const { locale, category, product: productSlug } = await params;

  const product = await fetch(
    `https://api.example.com/products/${productSlug}?locale=${locale}`,
    {
      next: {
        tags: [
          `product-${productSlug}`,
          `cat-${category}-products`,
          `locale-${locale}`,
        ],
        revalidate: 86400,
      },
    }
  ).then(r => {
    if (!r.ok) return null;
    return r.json();
  });

  if (!product) notFound();

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="grid grid-cols-2 gap-12">
        {/* Product images */}
        <div className="space-y-4">
          {/* image gallery */}
        </div>

        {/* Product details */}
        <div>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-2xl mt-2">{formatPrice(product.price, locale)}</p>

          {/* Variant selector */}
          {product.variants.map((variant: any) => (
            <button key={variant.id} className="border rounded px-4 py-2 mr-2 mt-4">
              {variant.name} {variant.inStock ? '' : '(Out of Stock)'}
            </button>
          ))}

          <button className="w-full mt-8 py-4 bg-black text-white rounded-lg text-lg font-semibold">
            Add to Cart
          </button>

          <div className="mt-8 prose" dangerouslySetInnerHTML={{ __html: product.description }} />
        </div>
      </div>
    </div>
  );
}
```

**Webhook for product updates across locales**:

```tsx
// app/api/product-webhook/route.ts
import { revalidateTag } from 'next/cache';

export async function POST(request: Request) {
  const payload = await request.json();

  // Revalidate all locale variants of this product
  revalidateTag(`product-${payload.slug}`);

  // Revalidate category listings
  revalidateTag(`cat-${payload.category}-products`);

  // If price changed, revalidate all locale-specific caches
  if (payload.priceChanged) {
    ['en', 'de', 'fr', 'ja'].forEach((locale) => {
      revalidateTag(`locale-${locale}`);
    });
  }

  return Response.json({ ok: true });
}
```

This architecture handles 200K+ products across 4 locales with a build time under 5 minutes by only pre-rendering category pages and top products, letting everything else generate on-demand with ISR.

---

## Q14. (Advanced) How do you implement incremental migration from Pages Router to App Router while maintaining static generation?

**Scenario**: Your existing Next.js application uses Pages Router with `getStaticProps` and `getStaticPaths` for 5,000 pages. You need to incrementally migrate to App Router without breaking existing pages or losing SEO.

**Answer**:

Next.js supports running both `pages/` and `app/` directories simultaneously. You can migrate route by route.

```
Migration Strategy:
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  Phase 1: Setup (Day 1)                                      │
│  • Create app/ directory alongside pages/                     │
│  • Set up root layout.tsx                                     │
│  • Configure shared providers                                 │
│                                                               │
│  Phase 2: Migrate leaf routes first (Week 1-2)               │
│  • Start with simple static pages (/about, /contact)          │
│  • Move data fetching from getStaticProps to async components │
│  • Verify SEO metadata with new Metadata API                 │
│                                                               │
│  Phase 3: Migrate dynamic routes (Week 3-4)                  │
│  • Convert getStaticPaths → generateStaticParams              │
│  • Convert getStaticProps → async Server Components           │
│  • Convert getServerSideProps → dynamic Server Components     │
│                                                               │
│  Phase 4: Migrate layouts (Week 5-6)                         │
│  • Convert _app.tsx logic → app/layout.tsx                    │
│  • Move providers, analytics, fonts                           │
│                                                               │
│  Phase 5: Remove pages/ (Week 7)                             │
│  • Delete migrated pages/ routes                              │
│  • Verify all routes work from app/                           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Before (Pages Router)**:

```tsx
// pages/blog/[slug].tsx
import type { GetStaticPaths, GetStaticProps } from 'next';
import Head from 'next/head';

interface BlogPostProps {
  post: {
    title: string;
    content: string;
    publishedAt: string;
    slug: string;
  };
}

export const getStaticPaths: GetStaticPaths = async () => {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();

  return {
    paths: posts.map((post: any) => ({
      params: { slug: post.slug },
    })),
    fallback: 'blocking', // generate on-demand
  };
};

export const getStaticProps: GetStaticProps<BlogPostProps> = async ({ params }) => {
  const res = await fetch(`https://api.example.com/posts/${params?.slug}`);

  if (!res.ok) {
    return { notFound: true };
  }

  const post = await res.json();

  return {
    props: { post },
    revalidate: 3600, // ISR: 1 hour
  };
};

export default function BlogPost({ post }: BlogPostProps) {
  return (
    <>
      <Head>
        <title>{post.title} | My Blog</title>
        <meta name="description" content={post.content.substring(0, 160)} />
      </Head>
      <article>
        <h1>{post.title}</h1>
        <time>{post.publishedAt}</time>
        <div dangerouslySetInnerHTML={{ __html: post.content }} />
      </article>
    </>
  );
}
```

**After (App Router)**:

```tsx
// app/blog/[slug]/page.tsx
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

interface Post {
  title: string;
  content: string;
  publishedAt: string;
  slug: string;
}

// getStaticPaths → generateStaticParams
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts', {
    next: { tags: ['posts'] },
  }).then(r => r.json());

  return posts.map((post: Post) => ({
    slug: post.slug,
  }));
}

// fallback: 'blocking' → dynamicParams = true (default)
export const dynamicParams = true;

// revalidate: 3600 → export const revalidate = 3600
export const revalidate = 3600;

// Head → generateMetadata
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(slug);

  if (!post) {
    return { title: 'Post Not Found' };
  }

  return {
    title: `${post.title} | My Blog`,
    description: post.content.substring(0, 160),
    openGraph: {
      title: post.title,
      type: 'article',
      publishedTime: post.publishedAt,
    },
  };
}

async function getPost(slug: string): Promise<Post | null> {
  const res = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { tags: [`post-${slug}`], revalidate: 3600 },
  });

  if (!res.ok) return null;
  return res.json();
}

// getStaticProps + Component → async Server Component
export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);

  // notFound: true → notFound()
  if (!post) notFound();

  return (
    <article className="max-w-3xl mx-auto">
      <h1 className="text-4xl font-bold">{post.title}</h1>
      <time className="text-gray-500 block mt-2">{post.publishedAt}</time>
      <div className="prose mt-8" dangerouslySetInnerHTML={{ __html: post.content }} />
    </article>
  );
}
```

**Migration mapping cheat sheet**:

```
Pages Router                    →  App Router
─────────────────────────────────────────────────
getStaticPaths                  →  generateStaticParams
getStaticProps                  →  async Server Component + fetch
getServerSideProps              →  async Server Component + no-store
fallback: false                 →  dynamicParams = false
fallback: true/'blocking'       →  dynamicParams = true
revalidate: N (in getStaticProps)→  revalidate = N (segment) or fetch option
notFound: true                  →  notFound()
redirect (in getStaticProps)    →  redirect() from next/navigation
Head                            →  generateMetadata / Metadata API
_app.tsx                        →  app/layout.tsx
_document.tsx                   →  app/layout.tsx (html/body tags)
useRouter().query               →  params (await) + searchParams (await)
```

---

## Q15. (Advanced) How do you implement static generation for a multi-tenant SaaS platform where each tenant has their own subdomain?

**Scenario**: Your SaaS platform hosts 5,000 customer storefronts. Each has a subdomain like `acme.yourplatform.com`. You need to statically generate key pages for each tenant while keeping build times manageable.

**Answer**:

Multi-tenant static generation requires middleware for tenant detection, dynamic routing with tenant context, and selective pre-rendering.

```
Architecture:
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  acme.yourplatform.com/products                              │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────────────────────┐                                │
│  │  Middleware                │                                │
│  │  1. Extract subdomain     │                                │
│  │  2. Look up tenant        │                                │
│  │  3. Set x-tenant header   │                                │
│  │  4. Rewrite to /[tenant]  │                                │
│  └──────────┬───────────────┘                                │
│              │                                                │
│              ▼                                                │
│  ┌──────────────────────────┐                                │
│  │  app/[tenant]/products/   │                                │
│  │  page.tsx                 │                                │
│  │                           │                                │
│  │  Uses tenant context to   │                                │
│  │  fetch tenant-specific    │                                │
│  │  products, theme, etc.    │                                │
│  └──────────────────────────┘                                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Middleware for tenant detection**:

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const subdomain = hostname.split('.')[0];

  // Skip for main domain, www, and special subdomains
  if (['www', 'app', 'api', 'admin'].includes(subdomain) || !hostname.includes('.')) {
    return NextResponse.next();
  }

  // Rewrite the URL to include tenant slug
  const url = request.nextUrl.clone();
  url.pathname = `/${subdomain}${url.pathname}`;

  const response = NextResponse.rewrite(url);
  response.headers.set('x-tenant', subdomain);

  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api/).*)'],
};
```

**Tenant layout with theme**:

```tsx
// app/[tenant]/layout.tsx
import { notFound } from 'next/navigation';

interface TenantConfig {
  id: string;
  name: string;
  theme: {
    primaryColor: string;
    logo: string;
  };
  plan: 'free' | 'pro' | 'enterprise';
}

async function getTenantConfig(tenant: string): Promise<TenantConfig | null> {
  const res = await fetch(`https://api.yourplatform.com/tenants/${tenant}`, {
    next: { tags: [`tenant-${tenant}`], revalidate: 3600 },
  });
  if (!res.ok) return null;
  return res.json();
}

export async function generateStaticParams() {
  // Pre-render layouts for paid tenants (they get priority)
  const paidTenants = await fetch(
    'https://api.yourplatform.com/tenants?plan=pro,enterprise'
  ).then(r => r.json());

  return paidTenants.map((t: { slug: string }) => ({
    tenant: t.slug,
  }));
}

export default async function TenantLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ tenant: string }>;
}) {
  const { tenant } = await params;
  const config = await getTenantConfig(tenant);

  if (!config) notFound();

  return (
    <div
      style={{
        '--primary-color': config.theme.primaryColor,
      } as React.CSSProperties}
    >
      <header className="border-b p-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <img src={config.theme.logo} alt={config.name} className="h-8" />
          <nav className="flex gap-6">
            <a href={`/products`}>Products</a>
            <a href={`/about`}>About</a>
            <a href={`/contact`}>Contact</a>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto p-6">{children}</main>
    </div>
  );
}
```

**Tenant product pages**:

```tsx
// app/[tenant]/products/[slug]/page.tsx
export const dynamicParams = true;

export async function generateStaticParams({
  params,
}: {
  params: { tenant: string };
}) {
  // Pre-render top 20 products per paid tenant
  const products = await fetch(
    `https://api.yourplatform.com/tenants/${params.tenant}/products?sort=popular&limit=20`
  ).then(r => r.json());

  return products.map((p: { slug: string }) => ({
    slug: p.slug,
  }));
}

export default async function TenantProductPage({
  params,
}: {
  params: Promise<{ tenant: string; slug: string }>;
}) {
  const { tenant, slug } = await params;

  const product = await fetch(
    `https://api.yourplatform.com/tenants/${tenant}/products/${slug}`,
    {
      next: {
        tags: [`tenant-${tenant}`, `product-${tenant}-${slug}`],
        revalidate: 3600,
      },
    }
  ).then(r => {
    if (!r.ok) return null;
    return r.json();
  });

  if (!product) notFound();

  return (
    <div>
      <h1 className="text-3xl font-bold">{product.name}</h1>
      <p className="text-2xl mt-2">${product.price}</p>
      <div className="mt-6">{product.description}</div>
    </div>
  );
}
```

This architecture handles 5,000 tenants by only pre-rendering paid tenant layouts and their top products. Free tier tenants are generated on-demand. ISR with tag-based revalidation ensures content stays fresh.

---

## Q16. (Advanced) How do you implement parallel data fetching patterns with `generateStaticParams` and streaming for optimal build and runtime performance?

**Scenario**: Your product page needs data from 5 different APIs (product details, reviews, inventory, pricing, recommendations). During build with `generateStaticParams`, you need to fetch all of these efficiently for 10,000 products.

**Answer**:

```tsx
// app/products/[slug]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';

// Deduplicated fetch functions (Next.js auto-deduplicates same URL)
async function getProduct(slug: string) {
  return fetch(`https://api.example.com/products/${slug}`, {
    next: { tags: [`product-${slug}`] },
  }).then(r => r.ok ? r.json() : null);
}

async function getReviews(productId: string) {
  return fetch(`https://api.example.com/reviews/${productId}`, {
    next: { tags: ['reviews'], revalidate: 300 },
  }).then(r => r.json());
}

async function getInventory(sku: string) {
  return fetch(`https://api.example.com/inventory/${sku}`, {
    next: { revalidate: 60 }, // inventory changes frequently
  }).then(r => r.json());
}

async function getPricing(productId: string, region: string) {
  return fetch(`https://api.example.com/pricing/${productId}?region=${region}`, {
    next: { tags: [`pricing-${productId}`], revalidate: 300 },
  }).then(r => r.json());
}

async function getRecommendations(productId: string) {
  return fetch(`https://ml.example.com/recommendations/${productId}`, {
    next: { revalidate: 3600 },
  }).then(r => r.json());
}

export async function generateStaticParams() {
  const products = await fetch(
    'https://api.example.com/products?sort=popular&limit=5000'
  ).then(r => r.json());

  return products.map((p: { slug: string }) => ({ slug: p.slug }));
}

// The main page component uses parallel fetching + streaming
export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Critical data — must have before rendering anything
  const product = await getProduct(slug);
  if (!product) notFound();

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Critical: Product hero (renders immediately) */}
      <div className="grid grid-cols-2 gap-12">
        <ProductImages images={product.images} />
        <div>
          <h1 className="text-3xl font-bold">{product.name}</h1>

          {/* Pricing streams in when ready */}
          <Suspense fallback={<PricingSkeleton />}>
            <PricingSection productId={product.id} />
          </Suspense>

          {/* Inventory status streams in when ready */}
          <Suspense fallback={<InventorySkeleton />}>
            <InventorySection sku={product.sku} />
          </Suspense>

          <button className="w-full mt-6 py-4 bg-black text-white rounded-lg font-semibold">
            Add to Cart
          </button>
        </div>
      </div>

      {/* Reviews stream in when ready */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <ReviewsSection productId={product.id} />
      </Suspense>

      {/* Recommendations stream in last (lowest priority) */}
      <Suspense fallback={<RecommendationsSkeleton />}>
        <RecommendationsSection productId={product.id} />
      </Suspense>
    </div>
  );
}

// Each section is an async Server Component that fetches independently
async function PricingSection({ productId }: { productId: string }) {
  const pricing = await getPricing(productId, 'us');
  return (
    <div className="mt-4">
      <span className="text-3xl font-bold">${pricing.current}</span>
      {pricing.original > pricing.current && (
        <span className="ml-2 text-lg text-gray-400 line-through">${pricing.original}</span>
      )}
    </div>
  );
}

async function InventorySection({ sku }: { sku: string }) {
  const inventory = await getInventory(sku);
  return (
    <p className={`mt-2 text-sm ${inventory.inStock ? 'text-green-600' : 'text-red-600'}`}>
      {inventory.inStock ? `In Stock (${inventory.quantity} available)` : 'Out of Stock'}
    </p>
  );
}

async function ReviewsSection({ productId }: { productId: string }) {
  const reviews = await getReviews(productId);
  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-6">
        Reviews ({reviews.total}) — {reviews.averageRating} ★
      </h2>
      {reviews.items.map((review: any) => (
        <div key={review.id} className="border-b py-4">
          <div className="flex items-center gap-2">
            <span className="font-medium">{review.author}</span>
            <span className="text-yellow-500">{'★'.repeat(review.rating)}</span>
          </div>
          <p className="mt-1 text-gray-700">{review.text}</p>
        </div>
      ))}
    </section>
  );
}

async function RecommendationsSection({ productId }: { productId: string }) {
  const recs = await getRecommendations(productId);
  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-6">You Might Also Like</h2>
      <div className="grid grid-cols-4 gap-6">
        {recs.map((rec: any) => (
          <a key={rec.id} href={`/products/${rec.slug}`} className="group">
            <div className="aspect-square bg-gray-100 rounded-lg" />
            <h3 className="mt-2 font-medium group-hover:text-blue-600">{rec.name}</h3>
            <p className="text-green-600">${rec.price}</p>
          </a>
        ))}
      </div>
    </section>
  );
}

// Skeleton components
function PricingSkeleton() { return <div className="h-10 w-32 bg-gray-200 animate-pulse rounded mt-4" />; }
function InventorySkeleton() { return <div className="h-5 w-40 bg-gray-200 animate-pulse rounded mt-2" />; }
function ReviewsSkeleton() { return <div className="h-64 bg-gray-100 animate-pulse rounded-xl mt-12" />; }
function RecommendationsSkeleton() { return <div className="h-48 bg-gray-100 animate-pulse rounded-xl mt-12" />; }
function ProductImages({ images }: { images: any[] }) { return <div className="aspect-square bg-gray-100 rounded-xl" />; }
```

During build, Next.js renders each product page with streaming. The critical product data renders first, while reviews and recommendations stream in. This keeps build times fast because each page doesn't need to wait for all 5 APIs to complete before starting to output HTML.

---

## Q17. (Advanced) How do you implement on-demand ISR with webhook authentication for multiple CMS providers?

**Scenario**: Your site pulls content from three sources: Contentful (blog), Shopify (products), and Sanity (marketing pages). Each has its own webhook format and authentication. You need a unified revalidation system.

**Answer**:

```tsx
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

// Webhook handler registry
type WebhookHandler = {
  verify: (request: NextRequest, body: string) => boolean;
  getRevalidationTargets: (payload: any) => {
    paths: string[];
    tags: string[];
  };
};

const handlers: Record<string, WebhookHandler> = {
  // Contentful webhook handler
  contentful: {
    verify: (request, body) => {
      const secret = process.env.CONTENTFUL_WEBHOOK_SECRET!;
      const signature = request.headers.get('x-contentful-signature');
      if (!signature) return false;

      const hmac = crypto.createHmac('sha256', secret).update(body).digest('hex');
      return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(hmac));
    },
    getRevalidationTargets: (payload) => {
      const paths: string[] = [];
      const tags: string[] = [];

      const contentType = payload.sys?.contentType?.sys?.id;
      const slug = payload.fields?.slug?.['en-US'];

      if (contentType === 'blogPost') {
        paths.push(`/blog/${slug}`);
        tags.push(`post-${slug}`, 'posts', 'blog');
      } else if (contentType === 'page') {
        paths.push(`/${slug}`);
        tags.push(`page-${slug}`);
      }

      // Always revalidate the homepage (might show latest posts)
      tags.push('homepage');

      return { paths, tags };
    },
  },

  // Shopify webhook handler
  shopify: {
    verify: (request, body) => {
      const secret = process.env.SHOPIFY_WEBHOOK_SECRET!;
      const hmac = request.headers.get('x-shopify-hmac-sha256');
      if (!hmac) return false;

      const computed = crypto
        .createHmac('sha256', secret)
        .update(body, 'utf8')
        .digest('base64');

      return crypto.timingSafeEqual(Buffer.from(hmac), Buffer.from(computed));
    },
    getRevalidationTargets: (payload) => {
      const paths: string[] = [];
      const tags: string[] = [];

      if (payload.handle) {
        paths.push(`/products/${payload.handle}`);
        tags.push(`product-${payload.handle}`, 'products');
      }

      // Collection (category) update
      if (payload.collection_id) {
        tags.push(`collection-${payload.collection_id}`);
      }

      // Inventory update
      if (payload.inventory_item_id) {
        tags.push('inventory');
      }

      return { paths, tags };
    },
  },

  // Sanity webhook handler
  sanity: {
    verify: (request, body) => {
      const secret = process.env.SANITY_WEBHOOK_SECRET!;
      const signature = request.headers.get('sanity-webhook-signature');
      if (!signature) return false;

      const hmac = crypto.createHmac('sha256', secret).update(body).digest('hex');
      return signature === hmac;
    },
    getRevalidationTargets: (payload) => {
      const paths: string[] = [];
      const tags: string[] = [];
      const docType = payload._type;

      if (docType === 'landingPage') {
        const slug = payload.slug?.current;
        if (slug) {
          paths.push(`/${slug}`);
          tags.push(`landing-${slug}`);
        }
      } else if (docType === 'siteSettings') {
        tags.push('site-settings');
        // Revalidate entire site layout
        paths.push('/', 'layout');
      }

      return { paths, tags };
    },
  },
};

export async function POST(request: NextRequest) {
  // Determine which CMS sent the webhook
  const source = request.nextUrl.searchParams.get('source');

  if (!source || !handlers[source]) {
    return NextResponse.json(
      { error: `Unknown webhook source: ${source}` },
      { status: 400 }
    );
  }

  const handler = handlers[source];
  const body = await request.text();

  // Verify webhook authenticity
  if (!handler.verify(request, body)) {
    console.error(`[Revalidation] Invalid signature from ${source}`);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
  }

  // Parse payload and determine what to revalidate
  const payload = JSON.parse(body);
  const { paths, tags } = handler.getRevalidationTargets(payload);

  // Execute revalidation
  const results = {
    paths: paths.map((path) => {
      try {
        revalidatePath(path);
        return { path, status: 'revalidated' };
      } catch (error) {
        return { path, status: 'failed', error: String(error) };
      }
    }),
    tags: tags.map((tag) => {
      try {
        revalidateTag(tag);
        return { tag, status: 'revalidated' };
      } catch (error) {
        return { tag, status: 'failed', error: String(error) };
      }
    }),
  };

  console.log(`[Revalidation] Source: ${source}, Paths: ${paths.join(', ')}, Tags: ${tags.join(', ')}`);

  return NextResponse.json({
    revalidated: true,
    source,
    ...results,
  });
}
```

**Webhook URLs to configure in each CMS**:

```
Contentful: https://yoursite.com/api/revalidate?source=contentful
Shopify:    https://yoursite.com/api/revalidate?source=shopify
Sanity:     https://yoursite.com/api/revalidate?source=sanity
```

---

## Q18. (Advanced) How do you implement a documentation site with nested dynamic routes, table of contents, and cross-references?

**Scenario**: You're building a docs site like Next.js docs or React docs. It needs nested URLs (`/docs/getting-started/installation`), auto-generated table of contents, prev/next navigation, and all pages statically generated.

**Answer**:

```tsx
// app/docs/[...slug]/page.tsx
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { getAllDocs, getDocBySlug, getDocNavigation } from '@/lib/docs';
import { TableOfContents } from '@/components/table-of-contents';
import { DocsPagination } from '@/components/docs-pagination';

export async function generateStaticParams() {
  const allDocs = await getAllDocs();

  return allDocs.map((doc) => ({
    slug: doc.slugPath.split('/'),
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = await getDocBySlug(slug.join('/'));

  if (!doc) return { title: 'Not Found' };

  return {
    title: `${doc.title} | Documentation`,
    description: doc.description,
  };
}

export default async function DocsPage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const { slug } = await params;
  const path = slug.join('/');

  const [doc, navigation] = await Promise.all([
    getDocBySlug(path),
    getDocNavigation(),
  ]);

  if (!doc) notFound();

  // Find prev/next pages
  const flatDocs = flattenNavigation(navigation);
  const currentIndex = flatDocs.findIndex((d) => d.slug === path);
  const prevDoc = currentIndex > 0 ? flatDocs[currentIndex - 1] : null;
  const nextDoc = currentIndex < flatDocs.length - 1 ? flatDocs[currentIndex + 1] : null;

  return (
    <div className="flex gap-12">
      {/* Left sidebar navigation */}
      <aside className="w-64 flex-shrink-0 border-r pr-6">
        <DocsNavigation navigation={navigation} currentPath={path} />
      </aside>

      {/* Main content */}
      <article className="flex-1 max-w-3xl">
        {/* Breadcrumbs */}
        <nav className="flex gap-1 text-sm text-gray-500 mb-6">
          <a href="/docs" className="hover:text-gray-900">Docs</a>
          {slug.map((segment, i) => (
            <span key={i}>
              <span className="mx-1">/</span>
              <a
                href={`/docs/${slug.slice(0, i + 1).join('/')}`}
                className={i === slug.length - 1 ? 'text-gray-900 font-medium' : 'hover:text-gray-900'}
              >
                {segment.replace(/-/g, ' ')}
              </a>
            </span>
          ))}
        </nav>

        <h1 className="text-4xl font-bold">{doc.title}</h1>
        {doc.description && (
          <p className="mt-3 text-xl text-gray-600">{doc.description}</p>
        )}

        {/* Rendered MDX content */}
        <div className="prose prose-lg mt-8">
          {doc.content}
        </div>

        {/* Prev/Next pagination */}
        <DocsPagination prev={prevDoc} next={nextDoc} />
      </article>

      {/* Right sidebar: Table of Contents */}
      <aside className="w-56 flex-shrink-0">
        <div className="sticky top-24">
          <TableOfContents headings={doc.headings} />
        </div>
      </aside>
    </div>
  );
}

// Navigation tree component
function DocsNavigation({
  navigation,
  currentPath,
}: {
  navigation: NavSection[];
  currentPath: string;
}) {
  return (
    <nav className="sticky top-24 space-y-6">
      {navigation.map((section) => (
        <div key={section.title}>
          <h3 className="font-semibold text-sm uppercase text-gray-400 mb-2">
            {section.title}
          </h3>
          <ul className="space-y-1">
            {section.items.map((item) => (
              <li key={item.slug}>
                <a
                  href={`/docs/${item.slug}`}
                  className={`block py-1 px-2 rounded text-sm ${
                    item.slug === currentPath
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  {item.title}
                </a>
                {/* Nested items */}
                {item.children && item.children.length > 0 && (
                  <ul className="ml-4 mt-1 space-y-1">
                    {item.children.map((child) => (
                      <li key={child.slug}>
                        <a
                          href={`/docs/${child.slug}`}
                          className={`block py-1 px-2 rounded text-sm ${
                            child.slug === currentPath
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
                          }`}
                        >
                          {child.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface NavItem {
  title: string;
  slug: string;
  children?: NavItem[];
}

function flattenNavigation(navigation: NavSection[]): NavItem[] {
  const flat: NavItem[] = [];
  for (const section of navigation) {
    for (const item of section.items) {
      flat.push(item);
      if (item.children) {
        flat.push(...item.children);
      }
    }
  }
  return flat;
}
```

```tsx
// lib/docs.ts
interface Doc {
  title: string;
  description: string;
  slugPath: string;
  content: React.ReactNode;
  headings: Array<{ id: string; text: string; level: number }>;
}

export async function getAllDocs(): Promise<Doc[]> {
  const res = await fetch('https://cms.example.com/docs', {
    next: { tags: ['docs'] },
  });
  return res.json();
}

export async function getDocBySlug(slug: string): Promise<Doc | null> {
  const res = await fetch(`https://cms.example.com/docs/${slug}`, {
    next: { tags: [`doc-${slug}`, 'docs'] },
  });
  if (!res.ok) return null;
  return res.json();
}

export async function getDocNavigation(): Promise<NavSection[]> {
  const res = await fetch('https://cms.example.com/docs/navigation', {
    next: { tags: ['docs-nav'] },
  });
  return res.json();
}
```

This builds a full documentation site where every page is statically generated with proper navigation, breadcrumbs, table of contents, and prev/next links.

---

## Q19. (Advanced) How do you handle static generation with authentication — pre-rendering public pages while keeping authenticated pages dynamic?

**Scenario**: Your app has public pages (marketing, blog, docs) that should be static, and authenticated pages (dashboard, settings, billing) that must be dynamic. Some pages show different content based on auth state (pricing page shows current plan).

**Answer**:

The key is a **hybrid approach**: static for public, dynamic for authenticated, and client-side personalization for mixed pages.

```
Route Classification:
┌──────────────────────────────┬──────────────┬────────────────────┐
│  Route                        │ Rendering    │ Auth Handling      │
├──────────────────────────────┼──────────────┼────────────────────┤
│  / (homepage)                 │ Static + ISR │ Client-side CTA    │
│  /blog/[slug]                 │ Static + ISR │ None needed        │
│  /docs/[...slug]              │ Static       │ None needed        │
│  /pricing                     │ Static + ISR │ Client personalize │
│  /dashboard/*                 │ Dynamic      │ Server auth check  │
│  /settings/*                  │ Dynamic      │ Server auth check  │
│  /api/*                       │ Dynamic      │ Server auth check  │
└──────────────────────────────┴──────────────┴────────────────────┘
```

```tsx
// app/dashboard/layout.tsx — Force dynamic for all dashboard routes
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';

export const dynamic = 'force-dynamic'; // Never static

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  if (!session) {
    redirect('/login');
  }

  return (
    <div className="flex">
      <aside className="w-64 border-r">
        <nav className="p-4 space-y-2">
          <a href="/dashboard">Overview</a>
          <a href="/dashboard/billing">Billing</a>
          <a href="/dashboard/settings">Settings</a>
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
```

```tsx
// app/pricing/page.tsx — Static page with client-side personalization
export const revalidate = 3600; // ISR: 1 hour

export default async function PricingPage() {
  // This data is statically generated (same for all users)
  const plans = await fetch('https://api.example.com/pricing', {
    next: { tags: ['pricing'] },
  }).then(r => r.json());

  return (
    <div className="max-w-5xl mx-auto p-8">
      <h1 className="text-4xl font-bold text-center mb-12">Pricing</h1>

      <div className="grid grid-cols-3 gap-8">
        {plans.map((plan: any) => (
          <div key={plan.id} className="border rounded-2xl p-8">
            <h2 className="text-xl font-semibold">{plan.name}</h2>
            <p className="text-4xl font-bold mt-4">${plan.price}/mo</p>
            <ul className="mt-6 space-y-2">
              {plan.features.map((f: string, i: number) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-green-500">✓</span>{f}
                </li>
              ))}
            </ul>
            {/* Client component handles auth-aware CTA */}
            <PlanCTA planId={plan.id} planName={plan.name} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

```tsx
// components/plan-cta.tsx — Client Component for auth-aware UI
'use client';

import { useEffect, useState } from 'react';

interface PlanCTAProps {
  planId: string;
  planName: string;
}

export function PlanCTA({ planId, planName }: PlanCTAProps) {
  const [currentPlan, setCurrentPlan] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Client-side fetch to check user's current plan
    fetch('/api/user/plan')
      .then((r) => {
        if (r.ok) return r.json();
        return null;
      })
      .then((data) => {
        setCurrentPlan(data?.planId || null);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <button className="w-full mt-8 py-3 bg-gray-100 rounded-lg text-gray-400" disabled>
        Loading...
      </button>
    );
  }

  if (currentPlan === planId) {
    return (
      <button className="w-full mt-8 py-3 bg-green-100 text-green-800 rounded-lg" disabled>
        Current Plan
      </button>
    );
  }

  if (currentPlan) {
    return (
      <a
        href={`/dashboard/billing/change?plan=${planId}`}
        className="block w-full mt-8 py-3 bg-blue-600 text-white text-center rounded-lg hover:bg-blue-700"
      >
        Switch to {planName}
      </a>
    );
  }

  return (
    <a
      href={`/signup?plan=${planId}`}
      className="block w-full mt-8 py-3 bg-blue-600 text-white text-center rounded-lg hover:bg-blue-700"
    >
      Get Started
    </a>
  );
}
```

This pattern keeps the pricing page fully static (great for SEO and performance) while the CTA buttons personalize on the client after hydration. The static HTML shows a loading state briefly, then updates to show the user's current plan.

---

## Q20. (Advanced) How do you build a complete blog platform with static generation, MDX, search, RSS feed, and optimized build times?

**Scenario**: You're building a developer blog with 2,000+ posts, MDX content with code highlighting, full-text search, RSS feed, category/tag pages, and need sub-5-minute builds.

**Answer**:

```tsx
// Content layer with MDX processing
// lib/blog.ts
import { cache } from 'react';

export interface BlogPost {
  slug: string;
  title: string;
  description: string;
  content: string; // compiled MDX
  publishedAt: string;
  updatedAt: string;
  author: { name: string; avatar: string };
  category: string;
  tags: string[];
  readingTime: number;
  headings: Array<{ id: string; text: string; level: number }>;
}

// Cache the fetch to deduplicate during build
export const getAllPosts = cache(async (): Promise<BlogPost[]> => {
  const res = await fetch('https://cms.example.com/posts?limit=all', {
    next: { tags: ['posts'] },
  });
  return res.json();
});

export const getPostBySlug = cache(async (slug: string): Promise<BlogPost | null> => {
  const res = await fetch(`https://cms.example.com/posts/${slug}`, {
    next: { tags: [`post-${slug}`, 'posts'] },
  });
  if (!res.ok) return null;
  return res.json();
});

export const getCategories = cache(async (): Promise<string[]> => {
  const posts = await getAllPosts();
  return [...new Set(posts.map(p => p.category))];
});

export const getPostsByCategory = cache(async (category: string): Promise<BlogPost[]> => {
  const posts = await getAllPosts();
  return posts.filter(p => p.category === category);
});

export const getPostsByTag = cache(async (tag: string): Promise<BlogPost[]> => {
  const posts = await getAllPosts();
  return posts.filter(p => p.tags.includes(tag));
});
```

**Blog post page with MDX**:

```tsx
// app/blog/[slug]/page.tsx
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { getAllPosts, getPostBySlug } from '@/lib/blog';
import { TableOfContents } from '@/components/table-of-contents';

export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}

export const dynamicParams = true;
export const revalidate = 3600;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPostBySlug(slug);

  if (!post) return { title: 'Not Found' };

  return {
    title: post.title,
    description: post.description,
    authors: [{ name: post.author.name }],
    openGraph: {
      title: post.title,
      description: post.description,
      type: 'article',
      publishedTime: post.publishedAt,
      modifiedTime: post.updatedAt,
      authors: [post.author.name],
      tags: post.tags,
    },
    alternates: {
      canonical: `https://blog.example.com/blog/${slug}`,
    },
  };
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPostBySlug(slug);

  if (!post) notFound();

  // Get related posts
  const allPosts = await getAllPosts();
  const relatedPosts = allPosts
    .filter(p => p.slug !== slug && p.tags.some(t => post.tags.includes(t)))
    .slice(0, 3);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <article className="flex gap-12">
        <div className="flex-1 max-w-3xl">
          {/* Header */}
          <header className="mb-8">
            <div className="flex gap-2 mb-4">
              <a
                href={`/blog/category/${post.category}`}
                className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full"
              >
                {post.category}
              </a>
              {post.tags.map((tag) => (
                <a
                  key={tag}
                  href={`/blog/tag/${tag}`}
                  className="text-sm bg-gray-100 text-gray-600 px-3 py-1 rounded-full"
                >
                  {tag}
                </a>
              ))}
            </div>
            <h1 className="text-4xl font-bold leading-tight">{post.title}</h1>
            <p className="text-xl text-gray-600 mt-3">{post.description}</p>
            <div className="flex items-center gap-4 mt-6 text-sm text-gray-500">
              <img
                src={post.author.avatar}
                alt={post.author.name}
                className="w-10 h-10 rounded-full"
              />
              <div>
                <p className="font-medium text-gray-900">{post.author.name}</p>
                <p>
                  {new Date(post.publishedAt).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                  {' · '}
                  {post.readingTime} min read
                </p>
              </div>
            </div>
          </header>

          {/* MDX content */}
          <div
            className="prose prose-lg prose-blue max-w-none"
            dangerouslySetInnerHTML={{ __html: post.content }}
          />

          {/* Related posts */}
          {relatedPosts.length > 0 && (
            <section className="mt-16 border-t pt-8">
              <h2 className="text-2xl font-bold mb-6">Related Posts</h2>
              <div className="grid grid-cols-3 gap-6">
                {relatedPosts.map((related) => (
                  <a key={related.slug} href={`/blog/${related.slug}`} className="group">
                    <h3 className="font-semibold group-hover:text-blue-600">{related.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{related.description}</p>
                  </a>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Table of Contents sidebar */}
        <aside className="w-56 flex-shrink-0 hidden xl:block">
          <div className="sticky top-24">
            <TableOfContents headings={post.headings} />
          </div>
        </aside>
      </article>
    </div>
  );
}
```

**RSS feed**:

```tsx
// app/feed.xml/route.ts
import { getAllPosts } from '@/lib/blog';

export async function GET() {
  const posts = await getAllPosts();
  const sortedPosts = posts.sort(
    (a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
  );

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Developer Blog</title>
    <link>https://blog.example.com</link>
    <description>Latest posts from our developer blog</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="https://blog.example.com/feed.xml" rel="self" type="application/rss+xml"/>
    ${sortedPosts.slice(0, 50).map((post) => `
    <item>
      <title>${escapeXml(post.title)}</title>
      <link>https://blog.example.com/blog/${post.slug}</link>
      <description>${escapeXml(post.description)}</description>
      <pubDate>${new Date(post.publishedAt).toUTCString()}</pubDate>
      <guid isPermaLink="true">https://blog.example.com/blog/${post.slug}</guid>
      ${post.tags.map((tag) => `<category>${escapeXml(tag)}</category>`).join('\n      ')}
    </item>`).join('')}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}
```

**Category and tag pages**:

```tsx
// app/blog/category/[category]/page.tsx
import { getAllPosts, getCategories, getPostsByCategory } from '@/lib/blog';

export async function generateStaticParams() {
  const categories = await getCategories();
  return categories.map((category) => ({ category }));
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ category: string }>;
}) {
  const { category } = await params;
  const posts = await getPostsByCategory(category);

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold capitalize mb-8">{category}</h1>
      <div className="space-y-6">
        {posts.map((post) => (
          <a key={post.slug} href={`/blog/${post.slug}`} className="block border rounded-lg p-6 hover:border-blue-300">
            <h2 className="text-xl font-semibold">{post.title}</h2>
            <p className="text-gray-600 mt-2">{post.description}</p>
            <div className="flex gap-4 mt-3 text-sm text-gray-500">
              <span>{post.author.name}</span>
              <span>{new Date(post.publishedAt).toLocaleDateString()}</span>
              <span>{post.readingTime} min read</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
```

**Build optimization with `cache()`**: The `cache()` wrapper from React ensures that `getAllPosts()` is called once during the entire build, regardless of how many pages reference it. This is crucial for 2,000+ post sites — without it, each page would re-fetch the full post list.

This architecture gives you: all 2,000+ pages statically generated, instant page loads from CDN, MDX rendering with code highlighting, SEO-optimized metadata, RSS feed, category/tag browsing, and builds under 5 minutes thanks to deduplication.

---
