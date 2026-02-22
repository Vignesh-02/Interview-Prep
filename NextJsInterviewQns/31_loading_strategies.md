# 31. Loading Strategies — Types, Patterns & Production Scenarios

## Topic Introduction

**Loading strategies** in Next.js 15/16 determine **what users see** while data is fetched or components are resolved: route-level **loading.tsx**, **Suspense** boundaries with skeletons or spinners, **streaming**, **optimistic UI**, and **prefetching**. Choosing the right strategy improves **perceived performance**, **TTI**, and **Core Web Vitals**. Senior developers match the strategy to the page type (marketing vs dashboard), data shape (fast vs slow, parallel vs waterfall), and product requirements (SEO, real-time feel).

```
Loading strategy landscape:
┌─────────────────────────────────────────────────────────────────────────┐
│  Route-level:     loading.tsx → full-route fallback (navigation)         │
│  Component-level: <Suspense fallback={…}> → granular streaming           │
│  Client-side:     useState + skeleton in Client Component                │
│  Optimistic:      show success state first, rollback on error            │
│  Prefetch:        Link prefetch, router.prefetch for next view           │
│  Static shell:    PPR → instant shell + stream dynamic holes            │
└─────────────────────────────────────────────────────────────────────────┘
```

**Types at a glance**:

| Strategy | When it shows | Best for |
|----------|----------------|----------|
| **loading.tsx** | While the **page** (and its layout children) are resolving | Route transitions, simple pages |
| **Suspense** | While the **wrapped subtree** is resolving | Multiple async sections, streaming |
| **Skeleton** | Placeholder that mirrors layout | Reducing CLS, perceived speed |
| **Spinner** | Generic “loading” indicator | Quick fallback, small areas |
| **Optimistic** | Immediate UI update before server confirms | Mutations (like, follow, cart) |
| **Prefetch** | Next page data/chunks loaded in background | Faster navigation |

---

## Q1. (Beginner) What is `loading.tsx` and when does it appear?

**Scenario**: User navigates to `/dashboard`. The dashboard page fetches data on the server. What do they see while waiting?

**Answer**:

**loading.tsx** is a special file that defines the **fallback UI** for the **page** (and its segment) while it’s loading. Next.js wraps the page in a `<Suspense>` boundary and shows the default export of **loading.tsx** as the fallback. It appears during **initial load** of that route and during **client-side navigation** to that route while the RSC payload is being fetched.

```tsx
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
    </div>
  );
}
```

Place **loading.tsx** in the same directory as **page.tsx** (e.g. **app/dashboard/loading.tsx** for **app/dashboard/page.tsx**). It does **not** wrap the **layout** of that segment—only the page and its siblings in the same segment.

---

## Q2. (Beginner) What is the difference between a skeleton and a spinner as a loading fallback?

**Answer**:

- **Skeleton**: A placeholder that **mimics the layout** of the real content (e.g. gray blocks where title, image, and text will be). Reduces **CLS** and feels faster because layout is stable. Best for content-heavy areas (cards, lists, profile).
- **Spinner**: A generic “loading” indicator (circle, dots). Doesn’t reserve space for content, so when real content appears the layout can **shift** (worse CLS). Good for small or generic areas (button state, inline loader).

In production, prefer **skeletons** for main content and **spinners** for small or secondary loading states.

---

## Q3. (Beginner) How do you show a loading state for a single async section without blocking the whole page?

**Answer**:

Wrap that section in **React Suspense** with a **fallback**. The rest of the page can render (or stream) while that section shows the fallback until its async work (e.g. data fetch) resolves.

```tsx
// app/products/page.tsx
import { Suspense } from 'react';

async function ProductList() {
  const products = await fetchProducts();
  return <ul>{products.map((p) => <li key={p.id}>{p.name}</li>)}</ul>;
}

function ProductListSkeleton() {
  return (
    <ul className="space-y-2">
      {[1, 2, 3, 4, 5].map((i) => (
        <li key={i} className="h-10 bg-gray-200 rounded animate-pulse" />
      ))}
    </ul>
  );
}

export default function ProductsPage() {
  return (
    <>
      <h1>Products</h1>
      <Suspense fallback={<ProductListSkeleton />}>
        <ProductList />
      </Suspense>
    </>
  );
}
```

The **page** can render the heading immediately; the list streams in when **fetchProducts()** completes.

---

## Q4. (Beginner) When does the user see `loading.tsx` vs the actual page content?

**Answer**:

- **First time** visiting the route (or after a full reload): User sees **loading.tsx** until the server sends the initial RSC payload and the page segment is ready; then the page content replaces it.
- **Client-side navigation** (e.g. `<Link href="/dashboard">`): Next.js shows **loading.tsx** (or the nearest loading UI) while the **new** route’s RSC payload is fetched. When the payload arrives, the page content is rendered.
- **When the page is already in the Router Cache** (e.g. back/forward, or prefetched): Next.js may show cached content immediately and skip the loading UI, depending on **staleTimes** and **router.refresh()**.

---

## Q5. (Beginner) What is “streaming” in the context of loading in Next.js?

**Answer**:

**Streaming** means the server sends the HTML (and RSC payload) in **chunks** instead of waiting for the entire page to be ready. The browser can paint the **shell** (layout, static parts) and then **replace** placeholders as each chunk arrives. So the user sees something **fast** (e.g. layout + skeletons), then **dynamic** parts (e.g. a slow component) appear when their async work finishes. **Suspense** defines the boundaries: each Suspense boundary is a “chunk” that can be sent when its content is ready. **loading.tsx** is one big boundary for the whole page; finer **Suspense** boundaries give **granular streaming**.

---

## Q6. (Intermediate) Production scenario: Dashboard with three widgets (revenue, users, orders). Each fetches from a different API; one is slow. How do you design the loading strategy?

**Scenario**: Revenue: 200ms, Users: 300ms, Orders: 2s. You want the page to feel fast and not wait for the slow one.

**Answer**:

Use **three separate Suspense boundaries**, each with a **skeleton** that matches the widget layout. The server can stream each widget as its data is ready: revenue and users appear first; orders appear when the slow API returns. The layout (e.g. header, grid) can be static and render immediately.

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react';

async function RevenueWidget() {
  const data = await fetchRevenue();
  return <MetricCard title="Revenue" value={data.value} />;
}

async function UsersWidget() {
  const data = await fetchUsers();
  return <MetricCard title="Users" value={data.count} />;
}

async function OrdersWidget() {
  const data = await fetchOrders();
  return <MetricCard title="Orders" value={data.count} />;
}

function MetricSkeleton() {
  return <div className="h-24 bg-gray-100 rounded-lg animate-pulse" />;
}

export default function DashboardPage() {
  return (
    <div className="grid grid-cols-3 gap-4">
      <Suspense fallback={<MetricSkeleton />}>
        <RevenueWidget />
      </Suspense>
      <Suspense fallback={<MetricSkeleton />}>
        <UsersWidget />
      </Suspense>
      <Suspense fallback={<MetricSkeleton />}>
        <OrdersWidget />
      </Suspense>
    </div>
  );
}
```

No **loading.tsx** is required for this pattern; the skeletons are the fallbacks. You can still add **loading.tsx** for the overall route (e.g. while layout or other work is pending) if needed.

---

## Q7. (Intermediate) When would you use route-level `loading.tsx` vs only Suspense boundaries inside the page?

**Answer**:

- **Use loading.tsx** when you want **one** loading UI for the **entire** route (e.g. full-page spinner or skeleton layout). Good for simple pages where the whole content is one async unit, or when you want a consistent “this route is loading” experience for every navigation to that segment.
- **Use only Suspense** when you want **granular** loading: static shell + multiple parts streaming in at different times. Then you don’t need a full-page loading state; each part has its own fallback. Use both if you want: **loading.tsx** for the segment while the **page** is pending, and **Suspense** for parts inside the page that resolve later.

---

## Q8. (Intermediate) How do you implement an “above-the-fold” loading strategy so the hero and nav show immediately and the rest streams?

**Scenario**: Home page: hero + nav are static; “Featured products” and “Latest news” are fetched. You want LCP (hero) fast and the rest to stream.

**Answer**:

- Render **hero** and **nav** in the **layout** or at the top of the **page** with **no** async dependency (or with static data). They’re in the first chunk.
- Wrap **Featured products** and **Latest news** in **Suspense** with skeletons. They stream in when their data is ready. Optionally use **loading.tsx** only for a minimal fallback (e.g. nav + hero skeleton) if the whole page is async; otherwise keep the page sync and use Suspense for the two sections.

```tsx
// app/page.tsx
import { Suspense } from 'react';

export default function HomePage() {
  return (
    <>
      <Hero /> {/* static or fast data in layout */}
      <nav>...</nav>
      <Suspense fallback={<ProductGridSkeleton />}>
        <FeaturedProducts />
      </Suspense>
      <Suspense fallback={<NewsListSkeleton />}>
        <LatestNews />
      </Suspense>
    </>
  );
}
```

Ensure **Hero** (and any LCP image) uses **next/image** with **priority** so it doesn’t wait on other data.

---

## Q9. (Intermediate) What is “optimistic UI” and how do you use it with Server Actions for a “like” button?

**Scenario**: User clicks “Like”; you don’t want to wait for the server before updating the count.

**Answer**:

**Optimistic UI** means updating the UI **immediately** as if the action succeeded, then reverting or fixing if the server returns an error. For a “like” button: on click, increment the count (or show “liked” state) in client state, call the Server Action, and if the action fails, revert the state and show an error.

```tsx
'use client';

import { useOptimistic } from 'react';
import { likePost } from './actions';

export function LikeButton({ postId, initialCount, initialLiked }: Props) {
  const [optimisticState, addOptimistic] = useOptimistic(
    { count: initialCount, liked: initialLiked },
    (state, payload: 'like' | 'unlike') =>
      payload === 'like'
        ? { count: state.count + 1, liked: true }
        : { count: state.count - 1, liked: false }
  );

  async function handleClick() {
    addOptimistic(optimisticState.liked ? 'unlike' : 'like');
    try {
      await likePost(postId);
    } catch {
      // Revert is implicit if we don't update server state; or use router.refresh()
      // and let server state overwrite
      // For full revert you'd need to pass previous state and set it back
    }
  }

  return (
    <button onClick={handleClick}>
      {optimisticState.liked ? 'Unlike' : 'Like'} ({optimisticState.count})
    </button>
  );
}
```

So the loading strategy here is “no loader”: **instant** feedback, with error handling and optional **router.refresh()** to resync with server.

---

## Q10. (Intermediate) How does Link prefetching affect what the user sees when they navigate?

**Answer**:

By default, **&lt;Link&gt;** **prefetches** the linked route’s RSC payload when the link enters the viewport (in production). So when the user **clicks**, the payload may already be in the **Router Cache** and navigation feels **instant**—no or very brief loading UI. Prefetching is a **loading strategy**: you “load” the next view in the background so that when the user goes there, you show content instead of **loading.tsx**. You can disable prefetch per link with **prefetch={false}** if the route is heavy or rarely visited.

---

## Q11. (Intermediate) Find the bug: Loading skeleton flashes then the whole page goes blank for a second, then content appears.

**Wrong code** (conceptually):

```tsx
// app/shop/page.tsx
export default async function ShopPage() {
  const [products, user] = await Promise.all([
    fetchProducts(),
    fetchUser(), // slow; used in layout too
  ]);
  return <ProductGrid products={products} />;
}
```

**Scenario**: **fetchUser()** is used in a parent layout and again here; there’s a waterfall or duplicate request. The “blank” might be layout or boundary re-rendering.

**Answer**:

Possible causes: (1) **Waterfall**: Layout fetches user, then page waits for layout and then fetches products; the loading state might disappear when layout resolves but page is still pending, then re-appear or flash. (2) **No Suspense**: The **entire** page is async, so **loading.tsx** shows until **both** fetches complete. When they complete, the whole page swaps in—no streaming. So you see: loading → (everything at once) → content. If there’s a subsequent re-render (e.g. client hydration or state update), you can get a brief blank.

**Fix**: (1) **Parallelize** at the page level (you did) but avoid duplicate **fetchUser** in layout and page—fetch user once in layout and pass or read from a shared cache. (2) Use **Suspense** so the shell (e.g. layout) and part of the page can stream first; wrap only the slow part in Suspense so the rest isn’t blocked. (3) Ensure you’re not unmounting the whole tree (e.g. conditional render that removes content before re-adding it). Simplest improvement: use **Suspense** around **ProductGrid** with a skeleton so the rest of the page can show while **fetchProducts()** (and any shared user) resolve.

---

## Q12. (Intermediate) How do you show a loading state for a Client Component that fetches data with `useEffect`?

**Answer**:

The Client Component owns its loading state: **useState** for **data** and **loading** (and optionally **error**). Initially **loading === true**; render a skeleton or spinner. In **useEffect**, fetch; when done set **data** and **loading = false**. Optionally use **use** with a Promise (or a library that returns a loading state) so you can suspend and use a parent **Suspense** boundary instead of manual loading state. For classic **useEffect** fetch, the pattern is:

```tsx
'use client';

import { useEffect, useState } from 'react';

export function ClientProductList() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/products')
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <ProductListSkeleton />;
  return <ul>{data?.map((p) => <li key={p.id}>{p.name}</li>)}</ul>;
}
```

Parent can wrap **ClientProductList** in **Suspense** with the same skeleton as fallback for consistency, but the component itself already handles loading.

---

## Q13. (Advanced) How does Partial Prerendering (PPR) change the loading strategy for a page with static and dynamic parts?

**Answer**:

With **PPR**, the server sends a **static shell** immediately (pre-rendered at build or first request). “Holes” for **dynamic** content are filled by **streaming** when their Suspense boundaries resolve. So the **loading strategy** is: **no** full-route loading.tsx for the static shell—it’s instant; only the **dynamic** holes show their **Suspense fallbacks** (skeletons) until server pushes the dynamic chunks. You design the page so that static parts (nav, footer, layout) are outside Suspense and dynamic parts (user-specific, live data) are inside Suspense. The “loading” experience is **granular**: instant shell + skeleton-per-dynamic-section, then stream-in.

---

## Q14. (Advanced) Production scenario: You have a product detail page (title, price, description, reviews). Reviews API is 3s slow. How do you avoid blocking the whole page and still keep SEO for title/description?

**Answer**:

- **Title, price, description**: Fetch in the **page** (or a single async component) **without** wrapping reviews in the same async block. So the **first** chunk contains layout + title/price/description (good for SEO and LCP).
- **Reviews**: Wrap in **Suspense** with a skeleton (e.g. “Loading reviews…” or review-shaped skeletons). The reviews section streams in when the 3s API returns. Search engines get the main content in the initial response; users see the important content first and reviews when ready.

```tsx
// app/products/[id]/page.tsx
async function ProductInfo({ id }: { id: string }) {
  const product = await fetchProduct(id);
  return (
    <>
      <h1>{product.name}</h1>
      <p>{product.price}</p>
      <p>{product.description}</p>
    </>
  );
}

async function Reviews({ id }: { id: string }) {
  const reviews = await fetchReviews(id); // slow
  return <ReviewList reviews={reviews} />;
}

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <Suspense fallback={<div className="text-gray-500">Loading product…</div>}>
        <ProductInfo id={id} />
      </Suspense>
      <Suspense fallback={<ReviewListSkeleton />}>
        <Reviews id={id} />
      </Suspense>
    </>
  );
}
```

Use **generateMetadata** for the product title/description so SEO gets the right meta tags from the same data.

---

## Q15. (Advanced) How do you prevent a “loading waterfall” when the page needs user context (e.g. layout) and then page-specific data?

**Answer**:

- **Option 1**: Fetch **user** (and other shared context) in the **layout** in parallel with anything the layout needs. The **page** fetches only page-specific data. Both can run in parallel if the layout doesn’t wait for the page and the page doesn’t wait for layout’s data unnecessarily. Avoid the page **await**ing layout data unless you pass it as props (which you can’t from layout to page directly)—so the page should not depend on layout’s async result for its **first** paint; use **Suspense** in the layout for the part that needs user so the rest of the layout can stream.
- **Option 2**: **Parallel data**: In the page, if you need user + page data, call **Promise.all([getUser(), getPageData()])** so they run in parallel. Get user from **cookies()** or a shared **getSession()** that’s cached with **cache()** so it’s not re-fetched per request.
- **Option 3**: **Single layout + Suspense**: Layout has **&lt;Suspense fallback={…}&gt;&lt;UserProvider&gt;…&lt;/UserProvider&gt;&lt;/Suspense&gt;** and the page is a sibling; both resolve independently so the server can stream layout shell first, then user block, then page.

---

## Q16. (Advanced) What is the difference between showing a loading state during **initial page load** vs during **client-side navigation**? Does Next.js treat them the same?

**Answer**:

- **Initial load**: The first HTML (and RSC payload) for the route. **loading.tsx** (and any Suspense fallbacks) are sent in the initial response or streamed. The user may see loading until the first chunk(s) arrive.
- **Client-side navigation**: Next.js fetches the **RSC payload** for the new route (or uses prefetched payload). While fetching, it shows the **loading** UI for that segment (**loading.tsx** or the nearest Suspense). When the payload arrives, it’s rendered. So **loading.tsx** and Suspense work for both; the difference is **where** the request comes from (first document load vs client-side fetch) and that **prefetch** can make navigation show no loading if the payload was already cached.

Next.js treats both as “this segment is pending → show fallback”; the mechanism (streaming vs client fetch) is the same from a UX perspective.

---

## Q17. (Advanced) How do you combine loading strategies for a list that supports infinite scroll (client-side) and an initial server-rendered batch?

**Answer**:

- **Initial batch**: Server-render the first page of the list in a Server Component (e.g. **&lt;List initialItems={items} /&gt;**). No loading state for that part if the page is async and wrapped in Suspense with a skeleton, or the page waits for it and you use **loading.tsx** for the route.
- **Infinite scroll**: Use a Client Component that receives **initialItems** and then fetches more (e.g. **useEffect** or a “Load more” click) via **fetch** or a Server Action. While “load more” is in progress, show a **small spinner or skeleton** at the bottom of the list (client-side loading state). So strategy: **server** for first screen (streaming or full wait) + **client** loading state for subsequent pages.

---

## Q18. (Advanced) Production scenario: Marketing wants the “Request demo” form to show a spinner on submit but the rest of the page must stay interactive. How do you implement it?

**Answer**:

Use **useFormStatus** (or **useActionState**) in a Client Component that wraps the submit button. **useFormStatus** gives **pending** only for the form that’s submitting, so you can show a spinner **on the button** (or disable the form) while the Server Action runs. The rest of the page is unaffected because the loading state is **local** to the form.

```tsx
'use client';

import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? (
        <>
          <span className="animate-spin mr-2">⏳</span>
          Sending…
        </>
      ) : (
        'Request demo'
      )}
    </button>
  );
}

export function DemoForm({ action }: { action: (formData: FormData) => Promise<void> }) {
  return (
    <form action={action}>
      <input name="email" type="email" />
      <SubmitButton />
    </form>
  );
}
```

No full-page loading; only the form shows feedback.

---

## Q19. (Advanced) How do loading strategies interact with the Router Cache (stale-while-revalidate) in Next.js 15/16?

**Answer**:

When the user navigates **back** or to a **prefetched** route, Next.js may serve the **cached** RSC payload (depending on **staleTimes**). In that case the **loading** UI may not show at all—cached content is shown immediately. When the cache is **stale**, Next.js can show the cached content (stale) and then **refresh** in the background; or it can show **loading** and then fresh content, depending on config. So: **loading.tsx** and **Suspense** are used when the segment **isn’t** in cache or is being refetched. Understanding **staleTimes** and **router.refresh()** helps you reason about when users see loading vs cached content.

---

## Q20. (Advanced) Create a one-page “loading strategy decision” guide for a senior dev: given page type (landing, dashboard, list, detail, form), which combination of loading.tsx, Suspense, skeleton, and optimistic UI do you recommend?

**Answer**:

| Page type | Recommended loading strategy |
|-----------|-------------------------------|
| **Landing** | Static shell (layout) + **Suspense** for any dynamic sections (testimonials, featured). Use **skeletons** that match layout. **loading.tsx** optional (minimal) so nav/hero show fast. |
| **Dashboard** | **Suspense** per widget/section with **skeletons**; no single blocking **loading.tsx** so fast widgets stream first. Optional **loading.tsx** for the route shell if layout is async. |
| **List (e.g. products)** | **loading.tsx** with list skeleton, OR **Suspense** around list with same skeleton. Prefer skeleton that matches card/list layout to avoid CLS. |
| **Detail (e.g. product)** | **Suspense** for above-the-fold (title, price) with minimal fallback; **Suspense** for below-the-fold (reviews, related) with skeletons. Keeps LCP and SEO content in first chunk. |
| **Form (submit)** | **No** full-page loading. Use **useFormStatus** for button spinner/disabled; **optimistic UI** for mutations that update list/detail (e.g. like, add to cart). |
| **Auth-gated** | **Middleware** redirects before page; page can show **loading.tsx** or Suspense until session is confirmed. Prefer not to flash protected content then remove it. |

**Summary**: Prefer **Suspense + skeleton** for granular streaming; use **loading.tsx** for simple routes or as a segment shell; use **optimistic** and **useFormStatus** for mutations and forms so the rest of the page stays responsive.
