# 17. Parallel Routes & Intercepting Routes — Advanced Patterns

## Topic Introduction

**Parallel Routes** and **Intercepting Routes** are two of the most powerful — and most misunderstood — features of the Next.js App Router. Together, they enable complex UI patterns like modals, split-view dashboards, tab-based layouts, and Instagram-style photo overlays that were previously painful to implement in React applications.

### Parallel Routes

Parallel Routes allow you to **simultaneously render multiple pages in the same layout**, each in its own independent "slot." Each slot gets its own `loading.tsx`, `error.tsx`, and navigation state.

```
┌──────────────────────────────────────────────┐
│  Root Layout                                  │
│  ┌────────────┐  ┌─────────────────────────┐ │
│  │  @sidebar   │  │  children (default slot)│ │
│  │             │  │                         │ │
│  │  - Nav      │  │  Main Content           │ │
│  │  - Links    │  │                         │ │
│  │             │  │                         │ │
│  └────────────┘  └─────────────────────────┘ │
│  ┌──────────────────────────────────────────┐ │
│  │  @analytics                               │ │
│  │  Chart / Metrics Panel                    │ │
│  └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

Slots are defined with the `@folder` convention:

```
app/
├── layout.tsx            ← Receives { children, sidebar, analytics }
├── page.tsx              ← children slot (default)
├── @sidebar/
│   ├── page.tsx          ← Sidebar content
│   └── default.tsx       ← Fallback when no match
├── @analytics/
│   ├── page.tsx          ← Analytics content
│   └── default.tsx       ← Fallback when no match
```

### Intercepting Routes

Intercepting Routes let you **load a route within the current layout** during soft navigation while still supporting the full page on hard navigation (direct URL access or refresh). This is the pattern behind Instagram-style photo modals.

```
Soft Navigation (click):           Hard Navigation (URL/refresh):
┌──────────────────────┐           ┌──────────────────────┐
│  /feed                │           │  /photo/123          │
│  ┌────────────────┐  │           │                      │
│  │  Modal Overlay  │  │           │  Full Photo Page     │
│  │  /photo/123     │  │           │  with all details    │
│  │  (intercepted)  │  │           │                      │
│  └────────────────┘  │           │                      │
│  Feed still visible   │           │                      │
└──────────────────────┘           └──────────────────────┘
```

Interception conventions:

| Convention   | Matches                                       |
|-------------|-----------------------------------------------|
| `(.)`       | Same level (sibling segment)                  |
| `(..)`      | One level up                                  |
| `(..)(..)`  | Two levels up                                 |
| `(...)`     | Root (`app/`) level                           |

```
app/
├── feed/
│   ├── page.tsx                  ← Feed page with photo grid
│   └── (.)photo/[id]/           ← Intercepts /photo/[id] from /feed
│       └── page.tsx             ← Renders as modal overlay
├── photo/[id]/
│   └── page.tsx                  ← Full photo page (hard nav / refresh)
```

**Why this matters for senior developers**: These patterns eliminate the "modal URL problem" (modals that lose state on refresh, or modals that can't be shared via URL). They also enable true split-view interfaces where each panel navigates independently — something that previously required complex state management with React Router or custom solutions.

---

## Q1. (Beginner) What are Parallel Routes in Next.js, and how do you define a slot?

**Scenario**: You're building a dashboard where the sidebar, main content, and a notifications panel each need their own independent loading and error states.

**Answer**:

**Parallel Routes** allow you to render multiple pages simultaneously within a single layout. Each independently-routed section is called a **slot**, defined using the `@folder` naming convention inside the `app/` directory.

A slot is **not** a URL segment — the `@` prefix tells Next.js to treat the folder as a named slot rather than a route segment.

```
app/
├── dashboard/
│   ├── layout.tsx               ← Receives all slots as props
│   ├── page.tsx                 ← Default children slot
│   ├── @sidebar/
│   │   ├── page.tsx             ← Sidebar content
│   │   ├── loading.tsx          ← Independent loading for sidebar
│   │   └── error.tsx            ← Independent error boundary
│   ├── @notifications/
│   │   ├── page.tsx             ← Notifications panel
│   │   ├── loading.tsx          ← Independent loading for notifications
│   │   └── error.tsx            ← Independent error boundary
```

The layout receives each slot as a named prop:

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  sidebar,
  notifications,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  notifications: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-[250px_1fr_350px] h-screen">
      <aside className="border-r overflow-y-auto">{sidebar}</aside>
      <main className="overflow-y-auto p-6">{children}</main>
      <aside className="border-l overflow-y-auto">{notifications}</aside>
    </div>
  );
}
```

```tsx
// app/dashboard/@sidebar/page.tsx
import { getNavigationItems } from '@/lib/navigation';

export default async function Sidebar() {
  const items = await getNavigationItems();

  return (
    <nav className="p-4 space-y-2">
      <h2 className="font-semibold text-lg mb-4">Dashboard</h2>
      {items.map((item) => (
        <a
          key={item.href}
          href={item.href}
          className="block px-3 py-2 rounded-md hover:bg-gray-100"
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
```

```tsx
// app/dashboard/@notifications/page.tsx
import { getNotifications } from '@/lib/notifications';

export default async function Notifications() {
  const notifications = await getNotifications();

  return (
    <div className="p-4">
      <h2 className="font-semibold text-lg mb-4">Notifications</h2>
      <ul className="space-y-3">
        {notifications.map((n) => (
          <li key={n.id} className="p-3 bg-gray-50 rounded-lg">
            <p className="font-medium">{n.title}</p>
            <p className="text-sm text-gray-500">{n.time}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Key points**:
- `children` is an **implicit slot** — you don't need an `@children` folder.
- Each slot is independently rendered, so a slow sidebar doesn't block the main content.
- The `@folder` name does NOT appear in the URL. `/dashboard` renders all three slots.

---

## Q2. (Beginner) What is `default.tsx` and why is it necessary for parallel routes?

**Scenario**: You navigate from `/dashboard` to `/dashboard/settings`, but the `@sidebar` slot doesn't have a `/settings` sub-route. The page crashes with a 404.

**Answer**:

`default.tsx` is the **fallback file** for a parallel route slot. When Next.js performs a soft navigation to a URL that doesn't have a matching route inside a particular slot, it needs to know what to render for that slot. Without a `default.tsx`, Next.js renders a **404**.

```
Scenario: Navigate from /dashboard to /dashboard/settings

app/
├── dashboard/
│   ├── layout.tsx                ← { children, sidebar }
│   ├── page.tsx                  ← children at /dashboard ✓
│   ├── settings/
│   │   └── page.tsx              ← children at /dashboard/settings ✓
│   ├── @sidebar/
│   │   ├── page.tsx              ← sidebar at /dashboard ✓
│   │   └── default.tsx           ← sidebar at /dashboard/settings ✓ (FALLBACK)
```

Without `default.tsx` in `@sidebar`, navigating to `/dashboard/settings` causes a 404 because Next.js can't find `@sidebar/settings/page.tsx`.

```tsx
// app/dashboard/@sidebar/default.tsx
// This renders when the sidebar doesn't have a route matching the current URL

export default function SidebarDefault() {
  // Option 1: Render the same content as page.tsx
  return <SidebarNavigation />;
}

// Or simply re-export the page component:
// export { default } from './page';
```

**How Next.js resolves slots during navigation**:

```
┌────────────────────────────────────────────────────┐
│  URL: /dashboard/settings                          │
│                                                    │
│  children slot:                                    │
│    ✓ Found: /dashboard/settings/page.tsx           │
│                                                    │
│  @sidebar slot:                                    │
│    ✗ No match: /dashboard/@sidebar/settings/page   │
│    ↓                                               │
│    Check: /dashboard/@sidebar/default.tsx           │
│    ✓ Found → Render default.tsx                    │
│    ✗ Not found → 404 Error!                        │
└────────────────────────────────────────────────────┘
```

**Soft vs Hard navigation behavior**:

| Navigation Type | Slot has match | Slot has `default.tsx` | Result |
|----------------|---------------|----------------------|--------|
| Soft (Link click) | Yes | N/A | Renders matched page |
| Soft (Link click) | No | Yes | Renders `default.tsx` |
| Soft (Link click) | No | No | Keeps previously active state |
| Hard (URL/refresh) | No | Yes | Renders `default.tsx` |
| Hard (URL/refresh) | No | No | **404 Error** |

**Best practice**: Always include `default.tsx` in every slot folder. A common pattern is to re-export the slot's main page:

```tsx
// app/dashboard/@sidebar/default.tsx
export { default } from './page';
```

---

## Q3. (Beginner) What are Intercepting Routes and what problem do they solve?

**Scenario**: You're building an e-commerce site where clicking a product card should open a modal preview, but sharing the product URL should show the full product page.

**Answer**:

**Intercepting Routes** let you load a route from another part of your application **within the current layout** during client-side (soft) navigation. When the user navigates directly to the URL (hard navigation), the full page renders instead.

This solves the **"modal URL" problem**: traditionally, modals either (a) don't have URLs (bad for sharing/SEO) or (b) replace the entire page when shared via URL (bad UX).

```
User clicks product card on /shop:
┌──────────────────────────────────┐
│  /shop (stays visible)           │
│  ┌──────────────────────────┐   │
│  │  Modal: /product/abc     │   │
│  │  Quick Preview           │   │
│  │  [Add to Cart] [Details] │   │
│  └──────────────────────────┘   │
│  ▓▓▓ dimmed background ▓▓▓      │
└──────────────────────────────────┘

User visits /product/abc directly (or refreshes):
┌──────────────────────────────────┐
│  /product/abc (full page)        │
│                                  │
│  Product Image Gallery           │
│  Full Description                │
│  Reviews, Specs, Related Items   │
│                                  │
└──────────────────────────────────┘
```

**File structure**:

```
app/
├── shop/
│   ├── page.tsx                       ← Product grid
│   └── (.)product/[id]/              ← Intercepts /product/[id]
│       └── page.tsx                   ← Renders as modal overlay
├── product/[id]/
│   └── page.tsx                       ← Full product page
```

The `(.)` prefix tells Next.js to intercept the route at the **same level**:

```tsx
// app/shop/page.tsx
import Link from 'next/link';
import { getProducts } from '@/lib/products';

export default async function ShopPage() {
  const products = await getProducts();

  return (
    <div className="grid grid-cols-3 gap-6 p-8">
      {products.map((product) => (
        <Link key={product.id} href={`/product/${product.id}`}>
          <div className="border rounded-lg p-4 hover:shadow-lg transition">
            <img src={product.image} alt={product.name} className="w-full" />
            <h3 className="mt-2 font-semibold">{product.name}</h3>
            <p className="text-green-600 font-bold">${product.price}</p>
          </div>
        </Link>
      ))}
    </div>
  );
}
```

```tsx
// app/shop/(.)product/[id]/page.tsx — INTERCEPTED (modal) version
import { getProduct } from '@/lib/products';
import { ProductModal } from '@/components/ProductModal';

export default async function InterceptedProduct({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);

  return <ProductModal product={product} />;
}
```

```tsx
// app/product/[id]/page.tsx — FULL PAGE version
import { getProduct } from '@/lib/products';

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="grid grid-cols-2 gap-8">
        <img src={product.image} alt={product.name} className="rounded-lg" />
        <div>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-2xl text-green-600 mt-2">${product.price}</p>
          <p className="mt-4 text-gray-600">{product.description}</p>
          <button className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg">
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Interception conventions summary**:

| Convention | Meaning | Example |
|-----------|---------|---------|
| `(.)` | Same level | `app/shop/(.)product` intercepts `app/product` from `app/shop` |
| `(..)` | One level up | `app/shop/cart/(..)product` intercepts `app/shop/product` |
| `(..)(..)` | Two levels up | `app/a/b/(..)(..)c` intercepts `app/c` |
| `(...)` | App root | `app/a/b/(...)c` intercepts `app/c` from anywhere |

---

## Q4. (Beginner) How do the interception conventions `(.)`, `(..)`, `(..)(..)`, and `(...)` work?

**Scenario**: Your app has a nested structure and you need to intercept routes at various levels. You're confused about which convention to use.

**Answer**:

Intercepting route conventions match **route segments** (not filesystem directories). This is a critical distinction — route groups `(groupName)` and slot folders `@slotName` don't count as segments.

```
Convention Reference:

(.)      → Same ROUTE level (like ./ for files)
(..)     → One ROUTE level up (like ../ for files)
(..)(..) → Two ROUTE levels up
(...)    → From the root (app/) level
```

**Example 1: `(.)` — Same level**

```
URL structure:
  /feed         ← source page
  /photo/[id]   ← target route

File structure:
  app/
  ├── feed/
  │   ├── page.tsx
  │   └── (.)photo/[id]/         ← (.) = same level as /feed
  │       └── page.tsx
  ├── photo/[id]/
  │   └── page.tsx
```

Both `/feed` and `/photo` are at the same route level (direct children of root), so `(.)` is correct.

**Example 2: `(..)` — One level up**

```
URL structure:
  /shop/categories      ← source page
  /shop/product/[id]    ← target route

File structure:
  app/
  ├── shop/
  │   ├── categories/
  │   │   ├── page.tsx
  │   │   └── (..)product/[id]/  ← (..) = one level up from /shop/categories → /shop
  │   │       └── page.tsx
  │   └── product/[id]/
  │       └── page.tsx
```

From `/shop/categories`, we go up one level to `/shop`, then match `product/[id]`.

**Example 3: `(...)` — Root level**

```
URL structure:
  /dashboard/settings/profile   ← source page (deeply nested)
  /auth/login                   ← target route (at root)

File structure:
  app/
  ├── dashboard/
  │   └── settings/
  │       └── profile/
  │           ├── page.tsx
  │           └── (...)auth/login/   ← (...) = jump to root
  │               └── page.tsx
  ├── auth/
  │   └── login/
  │       └── page.tsx
```

**Critical: Route groups don't count as segments**:

```
app/
├── (marketing)/              ← Route group — NOT a segment
│   └── blog/
│       ├── page.tsx          ← URL is /blog, NOT /(marketing)/blog
│       └── (.)photo/[id]/    ← (.) matches /photo/[id] at the ROUTE level
├── photo/[id]/
│   └── page.tsx
```

Even though `(marketing)` is a directory between `app/` and `blog/`, it's a route group and doesn't affect the route level. So `(.)` is still correct here (not `(..)` as you might expect from the filesystem).

**Quick decision guide**:

```
Step 1: Determine the ROUTE level of your source page
        (ignore route groups and @slots)

Step 2: Determine the ROUTE level of the target route

Step 3: Count how many levels you need to go UP
        0 levels → (.)
        1 level  → (..)
        2 levels → (..)(..)
        Any deep → (...)
```

---

## Q5. (Beginner) How do you combine parallel routes with intercepting routes to build a modal?

**Scenario**: You want a photo modal on your feed page — clicking opens a modal, refreshing shows the full page. This requires both parallel and intercepting routes.

**Answer**:

The **canonical modal pattern** combines:
1. A **parallel route slot** (`@modal`) to render the modal alongside the page
2. An **intercepting route** inside the slot to capture the navigation

```
app/
├── layout.tsx                    ← Root layout with @modal slot
├── page.tsx                      ← Home / feed page
├── @modal/
│   ├── default.tsx               ← Returns null (no modal by default)
│   └── (.)photo/[id]/
│       └── page.tsx              ← Intercepted route → renders as modal
├── photo/[id]/
│   └── page.tsx                  ← Full photo page (hard navigation)
```

```
Soft nav (click on feed):          Hard nav (direct URL/refresh):

┌─────────────────────────┐        ┌─────────────────────────┐
│  layout.tsx              │        │  layout.tsx              │
│  ┌───────────────────┐  │        │  ┌───────────────────┐  │
│  │  children: page   │  │        │  │  children:         │  │
│  │  (feed visible)   │  │        │  │  photo/[id]/page   │  │
│  └───────────────────┘  │        │  │  (full photo page) │  │
│  ┌───────────────────┐  │        │  └───────────────────┘  │
│  │  @modal:          │  │        │  ┌───────────────────┐  │
│  │  (.)photo/[id]    │  │        │  │  @modal:           │  │
│  │  (modal overlay)  │  │        │  │  default.tsx       │  │
│  └───────────────────┘  │        │  │  (returns null)    │  │
└─────────────────────────┘        │  └───────────────────┘  │
                                   └─────────────────────────┘
```

**Step-by-step implementation**:

```tsx
// app/layout.tsx
export default function RootLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        {modal}
      </body>
    </html>
  );
}
```

```tsx
// app/@modal/default.tsx — No modal shown by default
export default function ModalDefault() {
  return null;
}
```

```tsx
// app/@modal/(.)photo/[id]/page.tsx — Modal version (intercepted)
'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useCallback } from 'react';

export default function PhotoModal({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id } = React.use(params);

  const onDismiss = useCallback(() => {
    router.back();
  }, [router]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDismiss();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [onDismiss]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onDismiss}
    >
      <div
        className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <img
            src={`/photos/${id}.jpg`}
            alt={`Photo ${id}`}
            className="w-full rounded-lg"
          />
          <button
            onClick={onDismiss}
            className="mt-4 px-4 py-2 bg-gray-200 rounded-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
```

```tsx
// app/photo/[id]/page.tsx — Full page version (hard navigation)
import { getPhoto } from '@/lib/photos';

export default async function PhotoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const photo = await getPhoto(id);

  return (
    <div className="max-w-4xl mx-auto p-8">
      <img src={photo.url} alt={photo.title} className="w-full rounded-lg" />
      <h1 className="text-3xl font-bold mt-4">{photo.title}</h1>
      <p className="mt-2 text-gray-600">{photo.description}</p>
    </div>
  );
}
```

**Why this works**: On soft navigation, the `@modal` slot intercepts `/photo/[id]` and renders the modal, while `children` keeps showing the current page. On hard navigation, there's no interception — `children` renders the full `/photo/[id]/page.tsx` and `@modal` falls back to `default.tsx` (null).

---

## Q6. (Intermediate) How do parallel route slots get independent loading and error states? Show a production dashboard example.

**Scenario**: Your analytics dashboard has three panels: revenue chart, user activity table, and real-time alerts. The revenue API is slow (3s), alerts are fast (200ms). You don't want the fast panel to wait for the slow one.

**Answer**:

Each parallel route slot automatically gets its own **Suspense boundary** (via `loading.tsx`) and **Error boundary** (via `error.tsx`). This means:
- Fast slots render immediately, slow slots show their own loading spinner
- An error in one slot doesn't crash the entire page
- Users can interact with loaded slots while others are still fetching

```
app/
├── dashboard/
│   ├── layout.tsx
│   ├── page.tsx                        ← Main overview (children)
│   ├── loading.tsx                     ← Loading for children slot
│   ├── @revenue/
│   │   ├── page.tsx                    ← Revenue chart (slow: 3s)
│   │   ├── loading.tsx                 ← Revenue skeleton
│   │   └── error.tsx                   ← Revenue error boundary
│   ├── @activity/
│   │   ├── page.tsx                    ← User activity (medium: 1s)
│   │   ├── loading.tsx                 ← Activity skeleton
│   │   └── error.tsx                   ← Activity error boundary
│   ├── @alerts/
│   │   ├── page.tsx                    ← Real-time alerts (fast: 200ms)
│   │   ├── loading.tsx                 ← Alerts skeleton
│   │   └── error.tsx                   ← Alerts error boundary
```

```
Timeline of rendering:
  0ms    ────┬──── All slots start fetching in parallel
 200ms   ────┼──── @alerts renders ✓ (others still loading)
1000ms   ────┼──── @activity renders ✓ (@revenue still loading)
3000ms   ────┴──── @revenue renders ✓
```

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  revenue,
  activity,
  alerts,
}: {
  children: React.ReactNode;
  revenue: React.ReactNode;
  activity: React.ReactNode;
  alerts: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4">
        <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
      </header>
      <div className="p-6 space-y-6">
        {/* Top row: revenue + activity side by side */}
        <div className="grid grid-cols-2 gap-6">
          <section className="bg-white rounded-xl shadow-sm p-6">{revenue}</section>
          <section className="bg-white rounded-xl shadow-sm p-6">{activity}</section>
        </div>
        {/* Bottom row: alerts + main content */}
        <div className="grid grid-cols-3 gap-6">
          <section className="col-span-2 bg-white rounded-xl shadow-sm p-6">
            {children}
          </section>
          <section className="bg-white rounded-xl shadow-sm p-6">{alerts}</section>
        </div>
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/@revenue/page.tsx
import { getRevenueData } from '@/lib/analytics';
import { RevenueChart } from '@/components/charts/RevenueChart';

export default async function RevenuePanel() {
  const data = await getRevenueData(); // ~3 seconds

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Revenue</h2>
      <RevenueChart data={data} />
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-green-600">
            ${data.totalRevenue.toLocaleString()}
          </p>
          <p className="text-sm text-gray-500">Total Revenue</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-blue-600">
            {data.growth}%
          </p>
          <p className="text-sm text-gray-500">Growth</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-purple-600">
            {data.subscriptions}
          </p>
          <p className="text-sm text-gray-500">Active Subs</p>
        </div>
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/@revenue/loading.tsx
export default function RevenueLoading() {
  return (
    <div className="animate-pulse">
      <div className="h-6 w-24 bg-gray-200 rounded mb-4" />
      <div className="h-64 bg-gray-100 rounded-lg mb-4" />
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="text-center">
            <div className="h-8 w-20 bg-gray-200 rounded mx-auto mb-1" />
            <div className="h-4 w-16 bg-gray-100 rounded mx-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/@revenue/error.tsx
'use client';

export default function RevenueError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="text-center py-8">
      <div className="text-red-500 text-4xl mb-4">⚠</div>
      <h3 className="font-semibold text-lg">Revenue data unavailable</h3>
      <p className="text-gray-500 mt-1 text-sm">
        {error.message || 'Failed to load revenue data'}
      </p>
      <button
        onClick={reset}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Retry
      </button>
    </div>
  );
}
```

**Key insight**: If the revenue API fails, only the revenue panel shows an error. The activity and alerts panels continue working normally. The user can click "Retry" to re-fetch just the revenue data.

---

## Q7. (Intermediate) How do you conditionally render parallel route slots based on user authentication or roles?

**Scenario**: Your dashboard shows different content for admins vs regular users in the same layout. Admins see an `@admin` panel; regular users see a `@user` panel.

**Answer**:

Since the layout receives all slots as props, you can conditionally render them based on server-side logic like authentication. This is a powerful pattern for role-based UIs.

```
app/
├── dashboard/
│   ├── layout.tsx            ← Conditionally renders slots
│   ├── page.tsx
│   ├── @admin/
│   │   ├── page.tsx          ← Admin-only panel
│   │   └── default.tsx
│   ├── @user/
│   │   ├── page.tsx          ← Regular user panel
│   │   └── default.tsx
```

```tsx
// app/dashboard/layout.tsx
import { auth } from '@/lib/auth';

export default async function DashboardLayout({
  children,
  admin,
  user,
}: {
  children: React.ReactNode;
  admin: React.ReactNode;
  user: React.ReactNode;
}) {
  const session = await auth();
  const isAdmin = session?.user?.role === 'admin';

  return (
    <div className="flex h-screen">
      <main className="flex-1 p-6">{children}</main>
      <aside className="w-96 border-l p-6 bg-gray-50">
        {isAdmin ? admin : user}
      </aside>
    </div>
  );
}
```

```tsx
// app/dashboard/@admin/page.tsx
import { getAdminMetrics, getPendingApprovals } from '@/lib/admin';

export default async function AdminPanel() {
  const [metrics, approvals] = await Promise.all([
    getAdminMetrics(),
    getPendingApprovals(),
  ]);

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold text-red-600">Admin Panel</h2>

      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="font-semibold">System Metrics</h3>
        <ul className="mt-2 space-y-1 text-sm">
          <li>Active Users: {metrics.activeUsers}</li>
          <li>CPU Usage: {metrics.cpuUsage}%</li>
          <li>Memory: {metrics.memoryUsage}%</li>
          <li>Error Rate: {metrics.errorRate}%</li>
        </ul>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="font-semibold">Pending Approvals ({approvals.length})</h3>
        <ul className="mt-2 space-y-2">
          {approvals.map((item) => (
            <li key={item.id} className="flex justify-between items-center">
              <span className="text-sm">{item.title}</span>
              <div className="space-x-2">
                <button className="text-xs px-2 py-1 bg-green-500 text-white rounded">
                  Approve
                </button>
                <button className="text-xs px-2 py-1 bg-red-500 text-white rounded">
                  Reject
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/@user/page.tsx
import { getUserStats, getRecentActivity } from '@/lib/user';
import { auth } from '@/lib/auth';

export default async function UserPanel() {
  const session = await auth();
  const [stats, activity] = await Promise.all([
    getUserStats(session!.user.id),
    getRecentActivity(session!.user.id),
  ]);

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold">Your Dashboard</h2>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold">Your Stats</h3>
        <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
          <div>Projects: {stats.projects}</div>
          <div>Tasks: {stats.completedTasks}/{stats.totalTasks}</div>
          <div>Streak: {stats.streak} days</div>
          <div>Points: {stats.points}</div>
        </div>
      </div>

      <div>
        <h3 className="font-semibold mb-2">Recent Activity</h3>
        <ul className="space-y-2">
          {activity.map((item) => (
            <li key={item.id} className="text-sm p-2 bg-white rounded border">
              <span className="text-gray-500">{item.time}</span>
              <p>{item.description}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

**Important security note**: Both slots are rendered on the server, but only one is sent to the client. However, the **code for both slots is included in the server bundle**. For truly sensitive admin components, add an additional server-side guard inside the admin slot:

```tsx
// app/dashboard/@admin/page.tsx
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function AdminPanel() {
  const session = await auth();
  if (session?.user?.role !== 'admin') {
    redirect('/unauthorized');
  }
  // ... admin content
}
```

---

## Q8. (Intermediate) Build an Instagram-style photo gallery with intercepting routes and a modal.

**Scenario**: You're building a social media app with a photo feed. Clicking a photo opens a modal with comments; the URL changes to `/photo/[id]`. Refreshing that URL shows the full photo page.

**Answer**:

```
app/
├── layout.tsx
├── page.tsx                       ← Feed / Home
├── @modal/
│   ├── default.tsx                ← null (no modal)
│   └── (.)photo/[id]/
│       └── page.tsx               ← Modal overlay
├── photo/[id]/
│   └── page.tsx                   ← Full photo page
```

```tsx
// app/page.tsx — Photo Feed
import Link from 'next/link';
import { getPhotos } from '@/lib/photos';

export default async function FeedPage() {
  const photos = await getPhotos({ limit: 30 });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Photo Feed</h1>
      <div className="grid grid-cols-3 gap-1 md:gap-4">
        {photos.map((photo) => (
          <Link
            key={photo.id}
            href={`/photo/${photo.id}`}
            className="relative aspect-square group overflow-hidden rounded-sm"
          >
            <img
              src={photo.thumbnailUrl}
              alt={photo.caption}
              className="w-full h-full object-cover transition-transform group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
              <div className="hidden group-hover:flex gap-6 text-white font-semibold">
                <span>♥ {photo.likes}</span>
                <span>💬 {photo.comments}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

```tsx
// app/layout.tsx
export default function RootLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        {modal}
      </body>
    </html>
  );
}
```

```tsx
// app/@modal/default.tsx
export default function ModalDefault() {
  return null;
}
```

```tsx
// app/@modal/(.)photo/[id]/page.tsx — Instagram-style modal
import { getPhoto, getPhotoComments } from '@/lib/photos';
import { ModalShell } from '@/components/ModalShell';
import { CommentForm } from '@/components/CommentForm';

export default async function PhotoModal({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [photo, comments] = await Promise.all([
    getPhoto(id),
    getPhotoComments(id),
  ]);

  return (
    <ModalShell>
      <div className="flex h-[80vh] max-w-5xl w-full bg-white rounded-xl overflow-hidden">
        {/* Left: Photo */}
        <div className="flex-1 bg-black flex items-center justify-center">
          <img
            src={photo.url}
            alt={photo.caption}
            className="max-w-full max-h-full object-contain"
          />
        </div>

        {/* Right: Details & Comments */}
        <div className="w-96 flex flex-col border-l">
          {/* Author */}
          <div className="p-4 border-b flex items-center gap-3">
            <img
              src={photo.author.avatar}
              alt={photo.author.name}
              className="w-10 h-10 rounded-full"
            />
            <div>
              <p className="font-semibold text-sm">{photo.author.name}</p>
              <p className="text-xs text-gray-500">{photo.location}</p>
            </div>
          </div>

          {/* Comments */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Caption */}
            <div className="flex gap-3">
              <img
                src={photo.author.avatar}
                alt=""
                className="w-8 h-8 rounded-full flex-shrink-0"
              />
              <p className="text-sm">
                <span className="font-semibold">{photo.author.name}</span>{' '}
                {photo.caption}
              </p>
            </div>

            {/* Comment list */}
            {comments.map((comment) => (
              <div key={comment.id} className="flex gap-3">
                <img
                  src={comment.author.avatar}
                  alt=""
                  className="w-8 h-8 rounded-full flex-shrink-0"
                />
                <div>
                  <p className="text-sm">
                    <span className="font-semibold">{comment.author.name}</span>{' '}
                    {comment.text}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">{comment.time}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="border-t p-4">
            <div className="flex gap-4 mb-3">
              <button className="text-2xl hover:text-red-500">♡</button>
              <button className="text-2xl">💬</button>
              <button className="text-2xl">↗</button>
            </div>
            <p className="font-semibold text-sm">{photo.likes.toLocaleString()} likes</p>
            <p className="text-xs text-gray-400 mt-1">{photo.createdAt}</p>
          </div>

          {/* Comment Input */}
          <CommentForm photoId={id} />
        </div>
      </div>
    </ModalShell>
  );
}
```

```tsx
// components/ModalShell.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useCallback, useRef } from 'react';

export function ModalShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const overlayRef = useRef<HTMLDivElement>(null);

  const onDismiss = useCallback(() => {
    router.back();
  }, [router]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDismiss();
    };
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [onDismiss]);

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onDismiss();
      }}
    >
      <button
        onClick={onDismiss}
        className="absolute top-4 right-4 text-white text-3xl hover:text-gray-300 z-10"
        aria-label="Close modal"
      >
        ✕
      </button>
      {children}
    </div>
  );
}
```

```tsx
// app/photo/[id]/page.tsx — Full page (hard navigation / refresh)
import { getPhoto, getPhotoComments } from '@/lib/photos';
import { CommentForm } from '@/components/CommentForm';
import Link from 'next/link';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const photo = await getPhoto(id);
  return {
    title: `${photo.author.name} — ${photo.caption.slice(0, 60)}`,
    openGraph: {
      images: [photo.url],
    },
  };
}

export default async function PhotoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [photo, comments] = await Promise.all([
    getPhoto(id),
    getPhotoComments(id),
  ]);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">
        ← Back to feed
      </Link>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <img src={photo.url} alt={photo.caption} className="w-full" />

        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <img
              src={photo.author.avatar}
              alt={photo.author.name}
              className="w-12 h-12 rounded-full"
            />
            <div>
              <p className="font-bold">{photo.author.name}</p>
              <p className="text-sm text-gray-500">{photo.location}</p>
            </div>
          </div>

          <p className="text-lg mb-4">{photo.caption}</p>
          <p className="font-semibold">{photo.likes.toLocaleString()} likes</p>
          <p className="text-sm text-gray-400">{photo.createdAt}</p>

          <hr className="my-6" />

          <h2 className="font-bold text-lg mb-4">Comments ({comments.length})</h2>
          <div className="space-y-4">
            {comments.map((comment) => (
              <div key={comment.id} className="flex gap-3">
                <img
                  src={comment.author.avatar}
                  alt=""
                  className="w-8 h-8 rounded-full"
                />
                <div>
                  <p>
                    <span className="font-semibold">{comment.author.name}</span>{' '}
                    {comment.text}
                  </p>
                  <p className="text-xs text-gray-400">{comment.time}</p>
                </div>
              </div>
            ))}
          </div>

          <CommentForm photoId={id} />
        </div>
      </div>
    </div>
  );
}
```

---

## Q9. (Intermediate) How do you implement tab-based layouts using parallel routes?

**Scenario**: You have a user profile page with tabs: Posts, Followers, Following. Each tab should have its own URL (`/profile/posts`, `/profile/followers`) and load independently.

**Answer**:

Parallel routes are perfect for tab-based interfaces because each tab can be a slot with independent loading and error states. Combined with active link highlighting, you get a fully routed tab system.

```
app/
├── profile/
│   ├── layout.tsx                 ← Tab container with navigation
│   ├── page.tsx                   ← Redirect to /profile/posts
│   ├── @tabs/
│   │   ├── default.tsx
│   │   ├── posts/
│   │   │   └── page.tsx           ← Posts tab content
│   │   ├── followers/
│   │   │   ├── page.tsx           ← Followers tab content
│   │   │   └── loading.tsx        ← Independent loading
│   │   └── following/
│   │       ├── page.tsx           ← Following tab content
│   │       └── loading.tsx
```

```tsx
// app/profile/layout.tsx
import { TabNavigation } from '@/components/TabNavigation';
import { auth } from '@/lib/auth';

export default async function ProfileLayout({
  children,
  tabs,
}: {
  children: React.ReactNode;
  tabs: React.ReactNode;
}) {
  const session = await auth();

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Profile header */}
      <div className="flex items-center gap-6 mb-8">
        <img
          src={session?.user?.image ?? '/default-avatar.png'}
          alt="Profile"
          className="w-24 h-24 rounded-full"
        />
        <div>
          <h1 className="text-2xl font-bold">{session?.user?.name}</h1>
          <p className="text-gray-500">@{session?.user?.username}</p>
        </div>
      </div>

      {/* Tab navigation */}
      <TabNavigation
        tabs={[
          { href: '/profile/posts', label: 'Posts' },
          { href: '/profile/followers', label: 'Followers' },
          { href: '/profile/following', label: 'Following' },
        ]}
      />

      {/* Tab content */}
      <div className="mt-6">{tabs}</div>

      {/* Below tabs — always visible */}
      {children}
    </div>
  );
}
```

```tsx
// components/TabNavigation.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface Tab {
  href: string;
  label: string;
}

export function TabNavigation({ tabs }: { tabs: Tab[] }) {
  const pathname = usePathname();

  return (
    <div className="border-b">
      <nav className="flex gap-0 -mb-px">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                isActive
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
```

```tsx
// app/profile/@tabs/posts/page.tsx
import { getUserPosts } from '@/lib/posts';
import { auth } from '@/lib/auth';

export default async function PostsTab() {
  const session = await auth();
  const posts = await getUserPosts(session!.user.id);

  return (
    <div className="grid grid-cols-3 gap-4">
      {posts.map((post) => (
        <article key={post.id} className="border rounded-lg p-4">
          {post.image && (
            <img src={post.image} alt="" className="w-full rounded mb-2" />
          )}
          <p className="text-sm">{post.content}</p>
          <div className="mt-2 flex gap-4 text-xs text-gray-500">
            <span>♥ {post.likes}</span>
            <span>💬 {post.comments}</span>
          </div>
        </article>
      ))}
    </div>
  );
}
```

```tsx
// app/profile/@tabs/followers/page.tsx
import { getFollowers } from '@/lib/social';
import { auth } from '@/lib/auth';

export default async function FollowersTab() {
  const session = await auth();
  const followers = await getFollowers(session!.user.id);

  return (
    <ul className="space-y-4">
      {followers.map((follower) => (
        <li key={follower.id} className="flex items-center justify-between p-3 border rounded-lg">
          <div className="flex items-center gap-3">
            <img
              src={follower.avatar}
              alt={follower.name}
              className="w-10 h-10 rounded-full"
            />
            <div>
              <p className="font-semibold">{follower.name}</p>
              <p className="text-sm text-gray-500">@{follower.username}</p>
            </div>
          </div>
          <button className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-full">
            Follow Back
          </button>
        </li>
      ))}
    </ul>
  );
}
```

```tsx
// app/profile/@tabs/default.tsx
import { redirect } from 'next/navigation';

export default function TabsDefault() {
  redirect('/profile/posts');
}
```

```tsx
// app/profile/page.tsx
import { redirect } from 'next/navigation';

export default function ProfilePage() {
  redirect('/profile/posts');
}
```

**Benefits over client-side tabs**:
- Each tab has a URL → shareable, bookmarkable, browser back/forward works
- Independent `loading.tsx` per tab → fast tab switches with skeleton UIs
- Independent `error.tsx` per tab → errors isolated to one tab
- Server-side data fetching → no client-side waterfalls

---

## Q10. (Intermediate) How does soft navigation vs hard navigation affect intercepting routes?

**Scenario**: You've set up intercepting routes for a modal, but when you refresh the page, the modal disappears and the full page shows instead. A colleague asks why.

**Answer**:

This is **by design** and is the core distinction that makes intercepting routes powerful:

```
┌─────────────────────────────────────────────────────────┐
│  SOFT NAVIGATION (client-side)                          │
│  Triggered by: <Link>, router.push(), router.replace()  │
│                                                         │
│  → Next.js checks for intercepting route matches        │
│  → If found, renders intercepted version (modal)        │
│  → Original page stays mounted in background            │
│  → URL updates to the target route                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  HARD NAVIGATION                                        │
│  Triggered by: browser refresh, typing URL, <a> tag,    │
│                window.location, external link            │
│                                                         │
│  → Full server render from scratch                      │
│  → No interception — renders the actual route's page    │
│  → No previous page context to overlay on               │
└─────────────────────────────────────────────────────────┘
```

**Demonstration with code**:

```tsx
// app/feed/page.tsx
import Link from 'next/link';

export default function FeedPage() {
  return (
    <div>
      {/* Soft navigation → intercepting route activates → modal */}
      <Link href="/photo/1">View Photo (modal)</Link>

      {/* Hard navigation → full page renders */}
      <a href="/photo/1">View Photo (full page)</a>
    </div>
  );
}
```

**How Next.js decides what to render**:

```
Request: /photo/1

Is this a soft navigation?
├── YES → Check if any parent has an intercepting route
│         ├── Found: app/feed/(.)photo/[id]/page.tsx
│         │   → Render intercepted version (modal)
│         │   → Keep current page in background
│         └── Not found
│             → Render app/photo/[id]/page.tsx (navigate to full page)
│
└── NO (hard navigation)
    → Always render app/photo/[id]/page.tsx
    → @modal slot renders default.tsx (null)
```

**Practical implications**:

| Scenario | Navigation Type | What Renders |
|----------|---------------|--------------|
| Click `<Link>` to `/photo/1` on feed | Soft | Modal overlay on feed |
| Press browser refresh on `/photo/1` | Hard | Full photo page |
| Share URL `/photo/1` with friend | Hard | Full photo page |
| `router.push('/photo/1')` | Soft | Modal overlay |
| `router.refresh()` on `/photo/1` | Hard | Full photo page |
| Click browser back from modal | Soft | Previous page (feed) |
| `window.location.href = '/photo/1'` | Hard | Full photo page |

**This is the key UX insight**: Users who click through the app get the rich modal experience. Users who arrive via a shared link get the full page with complete context. Both are the same URL.

**Handling the transition gracefully**:

```tsx
// app/photo/[id]/page.tsx — Make the full page just as good
export default async function PhotoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const photo = await getPhoto(id);

  return (
    <div className="max-w-4xl mx-auto py-8">
      {/* Full page has navigation context that the modal doesn't need */}
      <nav className="mb-4">
        <Link href="/feed" className="text-blue-600 hover:underline">
          ← Back to Feed
        </Link>
      </nav>

      {/* Same photo content as modal, but with more room */}
      <img src={photo.url} alt={photo.caption} className="w-full rounded-xl" />
      <h1 className="text-2xl font-bold mt-4">{photo.caption}</h1>
      {/* ... full details, related photos, etc. */}
    </div>
  );
}
```

---

## Q11. (Intermediate) How do you handle navigation and URL state within parallel route slots?

**Scenario**: Your dashboard has a `@sidebar` slot with its own navigation. Clicking items in the sidebar should update the sidebar content and URL, but the main content should also update based on the sidebar selection.

**Answer**:

Each parallel route slot has **independent navigation state**, meaning you can navigate within a slot without affecting others. However, slots can also share URL segments to stay in sync.

```
app/
├── dashboard/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── [section]/
│   │   └── page.tsx              ← Main content for a section
│   ├── @sidebar/
│   │   ├── page.tsx              ← Sidebar at /dashboard
│   │   ├── [section]/
│   │   │   └── page.tsx          ← Sidebar updates for each section
│   │   └── default.tsx
```

When the URL is `/dashboard/analytics`, both `children` and `@sidebar` receive the `[section]` param:

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  sidebar,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <div className="w-64 border-r bg-gray-50">{sidebar}</div>
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
```

```tsx
// app/dashboard/@sidebar/[section]/page.tsx
import Link from 'next/link';

const sections = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'analytics', label: 'Analytics', icon: '📈' },
  { id: 'users', label: 'Users', icon: '👥' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export default async function SidebarSection({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;

  return (
    <nav className="p-4 space-y-1">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        Navigation
      </h2>
      {sections.map((item) => (
        <Link
          key={item.id}
          href={`/dashboard/${item.id}`}
          className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
            section === item.id
              ? 'bg-blue-50 text-blue-700 font-medium'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <span>{item.icon}</span>
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
```

```tsx
// app/dashboard/[section]/page.tsx
import { OverviewPanel } from '@/components/panels/Overview';
import { AnalyticsPanel } from '@/components/panels/Analytics';
import { UsersPanel } from '@/components/panels/Users';
import { SettingsPanel } from '@/components/panels/Settings';
import { notFound } from 'next/navigation';

const panels: Record<string, React.ComponentType> = {
  overview: OverviewPanel,
  analytics: AnalyticsPanel,
  users: UsersPanel,
  settings: SettingsPanel,
};

export default async function DashboardSection({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;
  const Panel = panels[section];

  if (!Panel) {
    notFound();
  }

  return (
    <div className="p-8">
      <Panel />
    </div>
  );
}
```

**Key architecture insight**: Both the sidebar and main content respond to the same URL parameter `[section]`. When the user clicks a sidebar link, the URL changes, which updates both slots simultaneously. This keeps them in sync without any client-side state management.

**For truly independent slot navigation** (slots navigate to different URLs), you'd use separate route segments within each slot that don't overlap with the `children` route segments.

---

## Q12. (Intermediate) How do you build breadcrumb navigation with intercepting routes?

**Scenario**: Your e-commerce site has categories → subcategories → products. Clicking a product opens a modal (intercepted), but the breadcrumb in the modal should show the full navigation path.

**Answer**:

The challenge with intercepting routes and breadcrumbs is that the intercepted modal doesn't have the same layout hierarchy as the full page. You need to pass context about where the user came from.

```tsx
// app/shop/[category]/[subcategory]/page.tsx — Product listing
import Link from 'next/link';
import { getProducts, getCategory, getSubcategory } from '@/lib/catalog';

export default async function SubcategoryPage({
  params,
}: {
  params: Promise<{ category: string; subcategory: string }>;
}) {
  const { category, subcategory } = await params;
  const [cat, subcat, products] = await Promise.all([
    getCategory(category),
    getSubcategory(subcategory),
    getProducts({ category, subcategory }),
  ]);

  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link href="/shop" className="hover:text-blue-600">Shop</Link>
        <span>/</span>
        <Link href={`/shop/${category}`} className="hover:text-blue-600">
          {cat.name}
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">{subcat.name}</span>
      </nav>

      <h1 className="text-3xl font-bold mb-8">{subcat.name}</h1>

      <div className="grid grid-cols-4 gap-6">
        {products.map((product) => (
          <Link
            key={product.id}
            href={`/product/${product.id}`}
            // Pass breadcrumb context via search params
            // so the intercepted modal can display them
          >
            <div className="border rounded-lg p-4 hover:shadow-md transition">
              <img src={product.image} alt={product.name} className="w-full rounded" />
              <h3 className="mt-2 font-semibold">{product.name}</h3>
              <p className="text-green-600 font-bold">${product.price}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

**Strategy: Use search params to pass breadcrumb context**:

```tsx
// In the product listing, include breadcrumb info in the link
<Link
  href={`/product/${product.id}?from=${category}&sub=${subcategory}`}
>
```

```tsx
// app/shop/[category]/[subcategory]/(...)product/[id]/page.tsx
// Intercepted modal with breadcrumb context
import { getProduct, getCategory, getSubcategory } from '@/lib/catalog';
import { ModalShell } from '@/components/ModalShell';

export default async function InterceptedProduct({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ from?: string; sub?: string }>;
}) {
  const { id } = await params;
  const { from, sub } = await searchParams;

  const product = await getProduct(id);
  const category = from ? await getCategory(from) : null;
  const subcategory = sub ? await getSubcategory(sub) : null;

  return (
    <ModalShell>
      <div className="bg-white rounded-xl max-w-3xl w-full p-6">
        {/* Breadcrumbs inside modal */}
        {category && (
          <nav className="flex items-center gap-2 text-sm text-gray-500 mb-4">
            <span>Shop</span>
            <span>/</span>
            <span>{category.name}</span>
            {subcategory && (
              <>
                <span>/</span>
                <span>{subcategory.name}</span>
              </>
            )}
            <span>/</span>
            <span className="text-gray-900 font-medium">{product.name}</span>
          </nav>
        )}

        <div className="grid grid-cols-2 gap-6">
          <img src={product.image} alt={product.name} className="w-full rounded-lg" />
          <div>
            <h2 className="text-2xl font-bold">{product.name}</h2>
            <p className="text-xl text-green-600 mt-2">${product.price}</p>
            <p className="mt-4 text-gray-600">{product.shortDescription}</p>
            <button className="mt-6 w-full py-3 bg-blue-600 text-white rounded-lg font-semibold">
              Add to Cart
            </button>
            <Link
              href={`/product/${id}`}
              className="block mt-2 text-center text-blue-600 text-sm hover:underline"
            >
              View Full Details →
            </Link>
          </div>
        </div>
      </div>
    </ModalShell>
  );
}
```

**Alternative approach — use a shared breadcrumb context**:

```tsx
// lib/breadcrumb-context.ts
import { cache } from 'react';

export interface BreadcrumbItem {
  label: string;
  href: string;
}

// Using React cache for request-level deduplication
export const getBreadcrumbs = cache((): BreadcrumbItem[] => []);
export const setBreadcrumbs = cache((items: BreadcrumbItem[]) => items);
```

---

## Q13. (Advanced) How do you build a split-view interface where each panel navigates independently using parallel routes?

**Scenario**: You're building an email client like Gmail where the left panel shows the email list and the right panel shows the selected email. Clicking an email in the list should update only the right panel. The left panel should maintain scroll position.

**Answer**:

This is one of the most powerful use cases for parallel routes — a true split-view where each panel is a fully independent route.

```
app/
├── mail/
│   ├── layout.tsx                        ← Split-view container
│   ├── page.tsx                          ← Redirect to /mail/inbox
│   ├── @list/
│   │   ├── default.tsx
│   │   ├── [folder]/
│   │   │   └── page.tsx                  ← Email list for folder
│   │   │   └── loading.tsx               ← List skeleton
│   │   └── search/
│   │       └── page.tsx                  ← Search results
│   ├── @detail/
│   │   ├── default.tsx                   ← "Select an email" placeholder
│   │   ├── [folder]/
│   │   │   └── [emailId]/
│   │   │       └── page.tsx              ← Email detail view
│   │   │       └── loading.tsx           ← Detail skeleton
```

```tsx
// app/mail/layout.tsx
export default function MailLayout({
  children,
  list,
  detail,
}: {
  children: React.ReactNode;
  list: React.ReactNode;
  detail: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar — folder navigation (children) */}
      <aside className="w-56 border-r bg-gray-50 flex flex-col">
        {children}
      </aside>

      {/* Email list panel */}
      <section className="w-96 border-r overflow-y-auto flex-shrink-0">
        {list}
      </section>

      {/* Email detail panel */}
      <section className="flex-1 overflow-y-auto">
        {detail}
      </section>
    </div>
  );
}
```

```tsx
// app/mail/page.tsx — Folder sidebar (children slot)
import Link from 'next/link';
import { getFolders, getUnreadCounts } from '@/lib/mail';

export default async function MailSidebar() {
  const [folders, unreadCounts] = await Promise.all([
    getFolders(),
    getUnreadCounts(),
  ]);

  return (
    <div className="p-4">
      <button className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg mb-4 font-medium">
        Compose
      </button>
      <nav className="space-y-1">
        {folders.map((folder) => (
          <Link
            key={folder.id}
            href={`/mail/${folder.slug}`}
            className="flex justify-between items-center px-3 py-2 rounded-lg hover:bg-gray-200 text-sm"
          >
            <span className="flex items-center gap-2">
              <span>{folder.icon}</span>
              {folder.name}
            </span>
            {unreadCounts[folder.id] > 0 && (
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                {unreadCounts[folder.id]}
              </span>
            )}
          </Link>
        ))}
      </nav>
    </div>
  );
}
```

```tsx
// app/mail/@list/[folder]/page.tsx
import Link from 'next/link';
import { getEmails } from '@/lib/mail';

export default async function EmailList({
  params,
}: {
  params: Promise<{ folder: string }>;
}) {
  const { folder } = await params;
  const emails = await getEmails(folder);

  return (
    <div>
      <div className="p-4 border-b bg-gray-50">
        <h2 className="font-semibold capitalize">{folder}</h2>
        <p className="text-xs text-gray-500">{emails.length} messages</p>
      </div>

      <ul>
        {emails.map((email) => (
          <li key={email.id}>
            <Link
              href={`/mail/${folder}/${email.id}`}
              className={`block p-4 border-b hover:bg-blue-50 transition ${
                email.isRead ? 'bg-white' : 'bg-blue-25 font-semibold'
              }`}
            >
              <div className="flex justify-between items-start">
                <p className="text-sm truncate max-w-[200px]">{email.from}</p>
                <span className="text-xs text-gray-400 flex-shrink-0">{email.time}</span>
              </div>
              <p className="text-sm truncate mt-1">{email.subject}</p>
              <p className="text-xs text-gray-500 truncate mt-0.5">{email.preview}</p>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

```tsx
// app/mail/@detail/default.tsx — No email selected
export default function DetailDefault() {
  return (
    <div className="flex items-center justify-center h-full text-gray-400">
      <div className="text-center">
        <div className="text-6xl mb-4">📧</div>
        <p className="text-lg">Select an email to read</p>
      </div>
    </div>
  );
}
```

```tsx
// app/mail/@detail/[folder]/[emailId]/page.tsx
import { getEmail } from '@/lib/mail';
import { MarkAsReadAction } from '@/components/mail/MarkAsReadAction';
import { EmailActions } from '@/components/mail/EmailActions';

export default async function EmailDetail({
  params,
}: {
  params: Promise<{ folder: string; emailId: string }>;
}) {
  const { folder, emailId } = await params;
  const email = await getEmail(emailId);

  return (
    <div className="p-6">
      <MarkAsReadAction emailId={emailId} />

      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold">{email.subject}</h1>
          <div className="flex items-center gap-3 mt-3">
            <img
              src={email.fromAvatar}
              alt={email.from}
              className="w-10 h-10 rounded-full"
            />
            <div>
              <p className="font-semibold">{email.from}</p>
              <p className="text-sm text-gray-500">
                To: {email.to.join(', ')}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">{email.date}</span>
          <EmailActions emailId={emailId} folder={folder} />
        </div>
      </div>

      <div
        className="prose max-w-none"
        dangerouslySetInnerHTML={{ __html: email.bodyHtml }}
      />

      {email.attachments.length > 0 && (
        <div className="mt-6 border-t pt-4">
          <h3 className="font-semibold text-sm text-gray-500 mb-3">
            Attachments ({email.attachments.length})
          </h3>
          <div className="flex gap-3">
            {email.attachments.map((att) => (
              <a
                key={att.id}
                href={att.downloadUrl}
                className="flex items-center gap-2 px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"
              >
                <span>📎</span>
                <div>
                  <p className="font-medium">{att.name}</p>
                  <p className="text-xs text-gray-400">{att.size}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

**How the independent navigation works**:

```
User clicks "inbox" folder → URL: /mail/inbox
  @list renders:  /mail/@list/inbox/page.tsx
  @detail renders: /mail/@detail/default.tsx (no email selected)

User clicks email #42 → URL: /mail/inbox/42
  @list renders:  /mail/@list/inbox/page.tsx (SAME — maintains scroll!)
  @detail renders: /mail/@detail/inbox/42/page.tsx (updates to show email)

User clicks email #99 → URL: /mail/inbox/99
  @list renders:  /mail/@list/inbox/page.tsx (SAME — still maintains scroll!)
  @detail renders: /mail/@detail/inbox/99/page.tsx (updates to new email)
```

**The layout persists**, so the email list panel never re-renders or loses scroll position when you navigate between emails.

---

## Q14. (Advanced) How do you handle parallel route slot mismatches during navigation and prevent unintended 404s?

**Scenario**: You have a complex app with multiple parallel route slots. Some routes exist in slot A but not slot B. Users are getting unexpected 404 errors when navigating between certain routes.

**Answer**:

Slot mismatches are the #1 source of bugs with parallel routes. Understanding the resolution algorithm is critical.

```
Problem:
  app/
  ├── layout.tsx               ← { children, sidebar, detail }
  ├── page.tsx                 ← children at /
  ├── @sidebar/
  │   ├── page.tsx             ← sidebar at /
  │   └── settings/
  │       └── page.tsx         ← sidebar at /settings
  ├── @detail/
  │   └── page.tsx             ← detail at / ONLY
  ├── settings/
  │   └── page.tsx             ← children at /settings

  Navigate from / to /settings:
  - children  → /settings/page.tsx ✓
  - @sidebar  → @sidebar/settings/page.tsx ✓
  - @detail   → @detail/settings/page.tsx ✗ MISSING!
```

**Resolution order for each slot**:

```
For slot @detail navigating to /settings:

1. Check: app/@detail/settings/page.tsx         → NOT FOUND
2. Check: app/@detail/default.tsx                → FOUND? Use it : 404!
```

**The fix — comprehensive `default.tsx` strategy**:

```
app/
├── layout.tsx
├── page.tsx
├── default.tsx                    ← Root default for children
├── @sidebar/
│   ├── page.tsx
│   ├── default.tsx                ← ⭐ CRITICAL: Fallback for sidebar
│   └── settings/
│       └── page.tsx
├── @detail/
│   ├── page.tsx
│   ├── default.tsx                ← ⭐ CRITICAL: Fallback for detail
├── settings/
│   └── page.tsx
```

**Advanced pattern — Cascading defaults with route groups**:

```tsx
// app/@detail/default.tsx
// Smart default that shows different content based on what's available

export default function DetailDefault() {
  return (
    <div className="flex items-center justify-center h-full text-gray-400 p-8">
      <div className="text-center max-w-md">
        <div className="text-5xl mb-4">📋</div>
        <h2 className="text-lg font-medium mb-2">No item selected</h2>
        <p className="text-sm">
          Select an item from the list to view its details here.
        </p>
      </div>
    </div>
  );
}
```

**Debugging slot mismatches**:

```tsx
// Temporary debug layout to see which slots are active
// app/layout.tsx (development only)
export default function DebugLayout({
  children,
  sidebar,
  detail,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  detail: React.ReactNode;
}) {
  const isDev = process.env.NODE_ENV === 'development';

  return (
    <html lang="en">
      <body>
        {isDev && (
          <div className="fixed bottom-0 left-0 right-0 bg-yellow-100 text-xs p-2 z-50 flex gap-4">
            <span>children: {children ? '✓' : '✗'}</span>
            <span>sidebar: {sidebar ? '✓' : '✗'}</span>
            <span>detail: {detail ? '✓' : '✗'}</span>
          </div>
        )}
        <div className="flex">
          <aside>{sidebar}</aside>
          <main>{children}</main>
          <aside>{detail}</aside>
        </div>
      </body>
    </html>
  );
}
```

**Complete matrix for navigation behavior**:

| From | To | Slot has match? | Has `default.tsx`? | Soft Nav Result | Hard Nav Result |
|------|----|-|-|-|-|
| `/` | `/settings` | Yes | N/A | Renders matched page | Renders matched page |
| `/` | `/settings` | No | Yes | Previously active state (cached) | Renders `default.tsx` |
| `/` | `/settings` | No | No | Previously active state (cached) | **404 Error** |
| Direct | `/settings` | No | Yes | N/A | Renders `default.tsx` |
| Direct | `/settings` | No | No | N/A | **404 Error** |

**Rule of thumb**: Every `@slot` folder should have a `default.tsx`. This is non-negotiable for production applications.

---

## Q15. (Advanced) How do you implement a production-grade modal system with animations, loading states, and form handling using intercepting routes?

**Scenario**: Your SaaS app needs modals for creating/editing resources (projects, tasks, invoices). Each modal needs: entrance/exit animations, loading states, form validation, optimistic updates, and the ability to handle the URL on hard navigation.

**Answer**:

```
app/
├── layout.tsx
├── projects/
│   ├── page.tsx                            ← Project list
│   └── (.)project/[id]/edit/
│       └── page.tsx                        ← Intercepted edit modal
├── project/[id]/edit/
│   └── page.tsx                            ← Full edit page
├── @modal/
│   ├── default.tsx
│   └── (.)projects/new/
│       └── page.tsx                        ← Intercepted create modal
├── projects/new/
│   └── page.tsx                            ← Full create page
```

**Reusable animated modal component**:

```tsx
// components/AnimatedModal.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';

interface AnimatedModalProps {
  children: React.ReactNode;
  title: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  onClose?: () => void;
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-xl',
  lg: 'max-w-3xl',
  xl: 'max-w-5xl',
};

export function AnimatedModal({
  children,
  title,
  size = 'md',
  onClose,
}: AnimatedModalProps) {
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  const handleClose = useCallback(() => {
    setIsClosing(true);
    setTimeout(() => {
      if (onClose) {
        onClose();
      } else {
        router.back();
      }
    }, 200); // Match animation duration
  }, [router, onClose]);

  useEffect(() => {
    // Trigger entrance animation
    requestAnimationFrame(() => setIsVisible(true));

    // Lock body scroll
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Escape key handler
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleClose]);

  // Focus trap
  useEffect(() => {
    const modal = modalRef.current;
    if (!modal) return;

    const focusableElements = modal.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusableElements[0];
    const last = focusableElements[focusableElements.length - 1];

    first?.focus();

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    };

    modal.addEventListener('keydown', handleTab);
    return () => modal.removeEventListener('keydown', handleTab);
  }, []);

  const content = (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-colors duration-200 ${
        isVisible && !isClosing ? 'bg-black/50 backdrop-blur-sm' : 'bg-transparent'
      }`}
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        ref={modalRef}
        className={`${sizeClasses[size]} w-full bg-white rounded-2xl shadow-2xl transform transition-all duration-200 ${
          isVisible && !isClosing
            ? 'scale-100 opacity-100 translate-y-0'
            : 'scale-95 opacity-0 translate-y-4'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">{title}</h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 max-h-[70vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  );

  if (typeof window === 'undefined') return null;
  return createPortal(content, document.body);
}
```

**Modal with Server Action form**:

```tsx
// app/@modal/(.)projects/new/page.tsx
import { AnimatedModal } from '@/components/AnimatedModal';
import { CreateProjectForm } from '@/components/forms/CreateProjectForm';

export default function NewProjectModal() {
  return (
    <AnimatedModal title="Create New Project" size="lg">
      <CreateProjectForm isModal />
    </AnimatedModal>
  );
}
```

```tsx
// components/forms/CreateProjectForm.tsx
'use client';

import { useActionState } from 'react';
import { useRouter } from 'next/navigation';
import { createProject } from '@/actions/projects';

interface Props {
  isModal?: boolean;
}

export function CreateProjectForm({ isModal = false }: Props) {
  const router = useRouter();
  const [state, formAction, isPending] = useActionState(createProject, {
    errors: {},
    message: '',
  });

  // Redirect after successful creation
  if (state.success && state.projectId) {
    if (isModal) {
      router.back();
      router.refresh();
    } else {
      router.push(`/project/${state.projectId}`);
    }
  }

  return (
    <form action={formAction} className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-1.5">Project Name</label>
        <input
          name="name"
          type="text"
          required
          className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
            state.errors?.name ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="My Awesome Project"
        />
        {state.errors?.name && (
          <p className="mt-1 text-sm text-red-500">{state.errors.name}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5">Description</label>
        <textarea
          name="description"
          rows={4}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="Describe your project..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1.5">Visibility</label>
          <select
            name="visibility"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg"
          >
            <option value="private">Private</option>
            <option value="team">Team</option>
            <option value="public">Public</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5">Template</label>
          <select
            name="template"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg"
          >
            <option value="blank">Blank Project</option>
            <option value="kanban">Kanban Board</option>
            <option value="scrum">Scrum Sprint</option>
          </select>
        </div>
      </div>

      {state.message && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {state.message}
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4 border-t">
        {isModal && (
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isPending}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isPending && (
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          )}
          {isPending ? 'Creating...' : 'Create Project'}
        </button>
      </div>
    </form>
  );
}
```

```tsx
// actions/projects.ts
'use server';

import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const createProjectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(100),
  description: z.string().optional(),
  visibility: z.enum(['private', 'team', 'public']),
  template: z.enum(['blank', 'kanban', 'scrum']),
});

export async function createProject(prevState: any, formData: FormData) {
  const parsed = createProjectSchema.safeParse({
    name: formData.get('name'),
    description: formData.get('description'),
    visibility: formData.get('visibility'),
    template: formData.get('template'),
  });

  if (!parsed.success) {
    return {
      errors: parsed.error.flatten().fieldErrors,
      message: 'Validation failed',
    };
  }

  try {
    const project = await db.project.create({
      data: {
        ...parsed.data,
        ownerId: await getCurrentUserId(),
      },
    });

    revalidatePath('/projects');
    return { success: true, projectId: project.id, errors: {} };
  } catch (error) {
    return {
      errors: {},
      message: 'Failed to create project. Please try again.',
    };
  }
}
```

---

## Q16. (Advanced) How do you handle parallel routes in a monorepo with shared layouts across multiple apps?

**Scenario**: Your organization has a monorepo with `apps/dashboard`, `apps/marketing`, and `packages/ui`. The dashboard uses parallel routes extensively. How do you structure shared layout components that work with slots?

**Answer**:

In a monorepo setup, parallel route slots are app-specific (defined in the filesystem), but the layout components that consume them can be shared.

```
monorepo/
├── apps/
│   ├── dashboard/
│   │   └── app/
│   │       ├── layout.tsx               ← Uses shared DashboardShell
│   │       ├── page.tsx
│   │       ├── @sidebar/
│   │       ├── @detail/
│   │       └── @notifications/
│   ├── admin/
│   │   └── app/
│   │       ├── layout.tsx               ← Uses shared DashboardShell
│   │       ├── page.tsx
│   │       ├── @sidebar/
│   │       └── @audit/
├── packages/
│   ├── ui/
│   │   └── src/
│   │       ├── layouts/
│   │       │   ├── DashboardShell.tsx   ← Generic layout accepting slot props
│   │       │   └── SplitView.tsx
│   │       └── components/
│   │           ├── Modal.tsx
│   │           └── Panel.tsx
```

```tsx
// packages/ui/src/layouts/DashboardShell.tsx
import { ReactNode } from 'react';

interface SlotConfig {
  name: string;
  node: ReactNode;
  position: 'left' | 'right' | 'top' | 'bottom' | 'center';
  width?: string;
  minWidth?: string;
  collapsible?: boolean;
}

interface DashboardShellProps {
  slots: SlotConfig[];
  header?: ReactNode;
  footer?: ReactNode;
}

export function DashboardShell({ slots, header, footer }: DashboardShellProps) {
  const leftSlots = slots.filter((s) => s.position === 'left');
  const centerSlots = slots.filter((s) => s.position === 'center');
  const rightSlots = slots.filter((s) => s.position === 'right');
  const topSlots = slots.filter((s) => s.position === 'top');
  const bottomSlots = slots.filter((s) => s.position === 'bottom');

  return (
    <div className="flex flex-col h-screen">
      {header}

      {topSlots.map((slot) => (
        <div key={slot.name} className="border-b">
          {slot.node}
        </div>
      ))}

      <div className="flex flex-1 overflow-hidden">
        {leftSlots.map((slot) => (
          <aside
            key={slot.name}
            className="border-r overflow-y-auto flex-shrink-0"
            style={{ width: slot.width || '256px', minWidth: slot.minWidth }}
          >
            {slot.node}
          </aside>
        ))}

        <div className="flex-1 overflow-y-auto">
          {centerSlots.map((slot) => (
            <div key={slot.name}>{slot.node}</div>
          ))}
        </div>

        {rightSlots.map((slot) => (
          <aside
            key={slot.name}
            className="border-l overflow-y-auto flex-shrink-0"
            style={{ width: slot.width || '350px' }}
          >
            {slot.node}
          </aside>
        ))}
      </div>

      {bottomSlots.map((slot) => (
        <div key={slot.name} className="border-t">
          {slot.node}
        </div>
      ))}

      {footer}
    </div>
  );
}
```

```tsx
// apps/dashboard/app/layout.tsx
import { DashboardShell } from '@repo/ui/layouts/DashboardShell';
import { AppHeader } from '@repo/ui/components/AppHeader';

export default function DashboardLayout({
  children,
  sidebar,
  detail,
  notifications,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  detail: React.ReactNode;
  notifications: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <DashboardShell
          header={<AppHeader appName="Dashboard" />}
          slots={[
            { name: 'sidebar', node: sidebar, position: 'left', width: '240px' },
            { name: 'main', node: children, position: 'center' },
            { name: 'detail', node: detail, position: 'right', width: '400px' },
            { name: 'notifications', node: notifications, position: 'bottom' },
          ]}
        />
      </body>
    </html>
  );
}
```

```tsx
// apps/admin/app/layout.tsx
import { DashboardShell } from '@repo/ui/layouts/DashboardShell';
import { AppHeader } from '@repo/ui/components/AppHeader';

export default function AdminLayout({
  children,
  sidebar,
  audit,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  audit: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <DashboardShell
          header={<AppHeader appName="Admin Console" />}
          slots={[
            { name: 'sidebar', node: sidebar, position: 'left', width: '200px' },
            { name: 'main', node: children, position: 'center' },
            { name: 'audit', node: audit, position: 'right', width: '350px' },
          ]}
        />
      </body>
    </html>
  );
}
```

**Key insight**: The slot names (`@sidebar`, `@detail`, etc.) are determined by the filesystem in each app, but the layout component from the shared package doesn't know about slots — it just receives `ReactNode` props. The mapping between filesystem slots and shared component props happens in each app's `layout.tsx`.

---

## Q17. (Advanced) How do you handle deep linking and scroll restoration with parallel routes and intercepting routes?

**Scenario**: Users share links to specific sections within your dashboard. The parallel route slots need to restore to the correct state, and scroll positions within each panel need to be preserved.

**Answer**:

Deep linking with parallel routes requires careful coordination of URL state, scroll positions, and slot rendering. Next.js 15 handles some of this automatically, but complex scenarios need manual intervention.

```tsx
// lib/use-scroll-restoration.ts
'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

/**
 * Saves and restores scroll position for a scrollable container
 * across soft navigations. Each panel in a split view gets its own instance.
 */
export function useScrollRestoration(panelId: string) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const scrollPositions = useRef<Map<string, number>>(new Map());

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    // Restore position for current path
    const key = `${panelId}:${pathname}`;
    const savedPosition = scrollPositions.current.get(key);
    if (savedPosition !== undefined) {
      el.scrollTop = savedPosition;
    }

    // Save position on scroll
    const handleScroll = () => {
      scrollPositions.current.set(key, el.scrollTop);
    };

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, [pathname, panelId]);

  return scrollRef;
}
```

```tsx
// components/ScrollablePanel.tsx
'use client';

import { useScrollRestoration } from '@/lib/use-scroll-restoration';

export function ScrollablePanel({
  id,
  children,
  className = '',
}: {
  id: string;
  children: React.ReactNode;
  className?: string;
}) {
  const scrollRef = useScrollRestoration(id);

  return (
    <div ref={scrollRef} className={`overflow-y-auto ${className}`}>
      {children}
    </div>
  );
}
```

**Deep linking with URL-encoded slot state**:

```tsx
// Encoding multi-slot state in the URL using search params
// URL: /dashboard/analytics?detail=report-42&sidebar=favorites

// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  sidebar,
  detail,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  detail: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <ScrollablePanel id="sidebar" className="w-64 border-r">
        {sidebar}
      </ScrollablePanel>
      <ScrollablePanel id="main" className="flex-1">
        {children}
      </ScrollablePanel>
      <ScrollablePanel id="detail" className="w-96 border-l">
        {detail}
      </ScrollablePanel>
    </div>
  );
}
```

**Handling scroll-to-section in intercepting route modals**:

```tsx
// app/@modal/(.)article/[id]/page.tsx
'use client';

import { useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { AnimatedModal } from '@/components/AnimatedModal';

export default function ArticleModal({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const searchParams = useSearchParams();
  const section = searchParams.get('section');
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (section && contentRef.current) {
      const element = contentRef.current.querySelector(`#${section}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [section]);

  return (
    <AnimatedModal title="Article Preview" size="lg">
      <div ref={contentRef}>
        {/* Article content with section anchors */}
      </div>
    </AnimatedModal>
  );
}
```

**Preserving parallel route state on browser back/forward**:

```
Navigation History:
  1. /dashboard             → sidebar: default, detail: default
  2. /dashboard/analytics   → sidebar: analytics-nav, detail: default
  3. /dashboard/analytics   → sidebar: analytics-nav, detail: report-42

Browser Back:
  Step 3 → Step 2: detail slot reverts to default, sidebar stays
  Step 2 → Step 1: both slots revert to defaults

Key: Soft navigation preserves slot state.
     Hard navigation (refresh) re-renders all slots from scratch.
```

---

## Q18. (Advanced) How do you implement a complex multi-modal flow with intercepting routes (e.g., wizard/stepper inside a modal)?

**Scenario**: Your app has a "Create Invoice" flow that spans 3 steps. Clicking "New Invoice" opens a modal with steps: Details → Line Items → Review. Each step has its own URL so users can navigate back through steps.

**Answer**:

```
app/
├── invoices/
│   ├── page.tsx                                ← Invoice list
│   └── (.)invoices/new/
│       ├── layout.tsx                          ← Modal wrapper with stepper
│       ├── page.tsx                            ← Redirect to step 1
│       ├── details/
│       │   └── page.tsx                        ← Step 1: Invoice details
│       ├── items/
│       │   └── page.tsx                        ← Step 2: Line items
│       └── review/
│           └── page.tsx                        ← Step 3: Review & submit
├── invoices/new/
│   ├── layout.tsx                              ← Full page stepper layout
│   ├── page.tsx
│   ├── details/
│   │   └── page.tsx
│   ├── items/
│   │   └── page.tsx
│   └── review/
│       └── page.tsx
```

**Shared stepper state using React context**:

```tsx
// lib/invoice-wizard-context.tsx
'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface InvoiceFormData {
  // Step 1: Details
  clientId: string;
  clientName: string;
  dueDate: string;
  currency: string;
  notes: string;
  // Step 2: Line Items
  items: Array<{
    id: string;
    description: string;
    quantity: number;
    unitPrice: number;
  }>;
}

interface WizardContextType {
  data: Partial<InvoiceFormData>;
  updateData: (partial: Partial<InvoiceFormData>) => void;
  currentStep: number;
  totalSteps: number;
}

const WizardContext = createContext<WizardContextType | null>(null);

export function InvoiceWizardProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<Partial<InvoiceFormData>>({
    items: [],
  });

  const updateData = (partial: Partial<InvoiceFormData>) => {
    setData((prev) => ({ ...prev, ...partial }));
  };

  return (
    <WizardContext.Provider value={{ data, updateData, currentStep: 0, totalSteps: 3 }}>
      {children}
    </WizardContext.Provider>
  );
}

export function useInvoiceWizard() {
  const ctx = useContext(WizardContext);
  if (!ctx) throw new Error('useInvoiceWizard must be used within InvoiceWizardProvider');
  return ctx;
}
```

**Intercepted modal layout with stepper**:

```tsx
// app/invoices/(.)invoices/new/layout.tsx
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { InvoiceWizardProvider } from '@/lib/invoice-wizard-context';

const steps = [
  { id: 'details', label: 'Details', path: '/invoices/new/details' },
  { id: 'items', label: 'Line Items', path: '/invoices/new/items' },
  { id: 'review', label: 'Review', path: '/invoices/new/review' },
];

export default function InvoiceWizardModalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const currentStepIndex = steps.findIndex((s) => pathname.includes(s.id));

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) router.back();
      }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Create Invoice</h2>
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              ✕
            </button>
          </div>

          {/* Stepper */}
          <div className="flex items-center">
            {steps.map((step, i) => (
              <div key={step.id} className="flex items-center">
                <div
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                    i === currentStepIndex
                      ? 'bg-blue-100 text-blue-700 font-semibold'
                      : i < currentStepIndex
                      ? 'text-green-600'
                      : 'text-gray-400'
                  }`}
                >
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                      i < currentStepIndex
                        ? 'bg-green-500 text-white'
                        : i === currentStepIndex
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {i < currentStepIndex ? '✓' : i + 1}
                  </span>
                  {step.label}
                </div>
                {i < steps.length - 1 && (
                  <div
                    className={`w-12 h-0.5 mx-2 ${
                      i < currentStepIndex ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step content */}
        <InvoiceWizardProvider>
          <div className="flex-1 overflow-y-auto p-6">{children}</div>
        </InvoiceWizardProvider>
      </div>
    </div>
  );
}
```

```tsx
// app/invoices/(.)invoices/new/details/page.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useInvoiceWizard } from '@/lib/invoice-wizard-context';
import { useState } from 'react';

export default function InvoiceDetailsStep() {
  const router = useRouter();
  const { data, updateData } = useInvoiceWizard();
  const [clientId, setClientId] = useState(data.clientId || '');
  const [dueDate, setDueDate] = useState(data.dueDate || '');
  const [currency, setCurrency] = useState(data.currency || 'USD');

  const handleNext = () => {
    updateData({ clientId, dueDate, currency });
    router.push('/invoices/new/items');
  };

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-1.5">Client</label>
        <select
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
          className="w-full px-4 py-2.5 border rounded-lg"
        >
          <option value="">Select a client...</option>
          <option value="client-1">Acme Corp</option>
          <option value="client-2">Globex Inc</option>
          <option value="client-3">Initech LLC</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1.5">Due Date</label>
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="w-full px-4 py-2.5 border rounded-lg"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5">Currency</label>
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="w-full px-4 py-2.5 border rounded-lg"
          >
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end pt-4 border-t">
        <button
          onClick={handleNext}
          disabled={!clientId || !dueDate}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Next: Line Items →
        </button>
      </div>
    </div>
  );
}
```

```tsx
// app/invoices/(.)invoices/new/items/page.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useInvoiceWizard } from '@/lib/invoice-wizard-context';
import { useState } from 'react';
import { nanoid } from 'nanoid';

export default function LineItemsStep() {
  const router = useRouter();
  const { data, updateData } = useInvoiceWizard();
  const [items, setItems] = useState(
    data.items?.length
      ? data.items
      : [{ id: nanoid(), description: '', quantity: 1, unitPrice: 0 }]
  );

  const addItem = () => {
    setItems([...items, { id: nanoid(), description: '', quantity: 1, unitPrice: 0 }]);
  };

  const removeItem = (id: string) => {
    setItems(items.filter((item) => item.id !== id));
  };

  const updateItem = (id: string, field: string, value: string | number) => {
    setItems(items.map((item) => (item.id === id ? { ...item, [field]: value } : item)));
  };

  const total = items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);

  const handleNext = () => {
    updateData({ items });
    router.push('/invoices/new/review');
  };

  return (
    <div className="space-y-4">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-2">Description</th>
            <th className="pb-2 w-24">Qty</th>
            <th className="pb-2 w-32">Unit Price</th>
            <th className="pb-2 w-32 text-right">Amount</th>
            <th className="pb-2 w-10" />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b">
              <td className="py-2 pr-2">
                <input
                  value={item.description}
                  onChange={(e) => updateItem(item.id, 'description', e.target.value)}
                  className="w-full px-3 py-1.5 border rounded"
                  placeholder="Service description"
                />
              </td>
              <td className="py-2 pr-2">
                <input
                  type="number"
                  min={1}
                  value={item.quantity}
                  onChange={(e) => updateItem(item.id, 'quantity', Number(e.target.value))}
                  className="w-full px-3 py-1.5 border rounded"
                />
              </td>
              <td className="py-2 pr-2">
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={item.unitPrice}
                  onChange={(e) => updateItem(item.id, 'unitPrice', Number(e.target.value))}
                  className="w-full px-3 py-1.5 border rounded"
                />
              </td>
              <td className="py-2 text-right font-medium">
                ${(item.quantity * item.unitPrice).toFixed(2)}
              </td>
              <td className="py-2 text-center">
                <button
                  onClick={() => removeItem(item.id)}
                  className="text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <button
        onClick={addItem}
        className="text-blue-600 text-sm hover:underline"
      >
        + Add Line Item
      </button>

      <div className="text-right text-lg font-bold pt-4 border-t">
        Total: ${total.toFixed(2)}
      </div>

      <div className="flex justify-between pt-4 border-t">
        <button
          onClick={() => router.push('/invoices/new/details')}
          className="px-6 py-2.5 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          ← Back
        </button>
        <button
          onClick={handleNext}
          disabled={items.length === 0}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Next: Review →
        </button>
      </div>
    </div>
  );
}
```

This pattern gives you URL-driven wizard steps inside a modal, with browser back/forward navigation between steps.

---

## Q19. (Advanced) What are the performance implications of parallel routes, and how do you optimize them?

**Scenario**: Your dashboard with 4 parallel route slots is loading slowly. Each slot fetches data independently, but the total waterfall is adding up. How do you diagnose and optimize?

**Answer**:

**Understanding parallel route rendering**:

```
Without parallel routes (sequential):
  Layout → Page → Component A → Component B → Component C
  Total: 1s + 2s + 1.5s + 0.5s = 5s waterfall

With parallel routes:
  Layout renders simultaneously:
    ├── children slot   → 1s
    ├── @slotA          → 2s  ← slowest determines total time
    ├── @slotB          → 1.5s
    └── @slotC          → 0.5s
  Total: 2s (parallel) + layout overhead
```

**Performance diagnostic checklist**:

```tsx
// Measuring slot performance in development
// app/dashboard/layout.tsx

export default async function DashboardLayout({
  children,
  revenue,
  activity,
  alerts,
}: {
  children: React.ReactNode;
  revenue: React.ReactNode;
  activity: React.ReactNode;
  alerts: React.ReactNode;
}) {
  const layoutStart = performance.now();

  // In development, wrap each slot with timing
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Layout] Render start: ${layoutStart.toFixed(0)}ms`);
  }

  return (
    <div className="grid grid-cols-2 gap-6 p-6">
      {revenue}
      {activity}
      {children}
      {alerts}
    </div>
  );
}
```

**Optimization 1: Streaming with granular Suspense boundaries**:

```tsx
// app/dashboard/@revenue/page.tsx
import { Suspense } from 'react';
import { RevenueChart } from './RevenueChart';
import { RevenueStats } from './RevenueStats';

export default function RevenuePanel() {
  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Revenue</h2>

      {/* Fast: stats from cache */}
      <Suspense fallback={<StatsSkeleton />}>
        <RevenueStats />
      </Suspense>

      {/* Slow: chart requires heavy computation */}
      <Suspense fallback={<ChartSkeleton />}>
        <RevenueChart />
      </Suspense>
    </div>
  );
}
```

**Optimization 2: Preloading data for slots**:

```tsx
// lib/preload.ts
import { cache } from 'react';

// Request-level deduplication with React cache
export const getRevenueData = cache(async () => {
  const res = await fetch('https://api.example.com/revenue', {
    next: { tags: ['revenue'] },
  });
  return res.json();
});

export const getActivityData = cache(async () => {
  const res = await fetch('https://api.example.com/activity', {
    next: { tags: ['activity'] },
  });
  return res.json();
});

// Preload function — call early to start fetches
export function preloadDashboardData() {
  void getRevenueData();
  void getActivityData();
}
```

```tsx
// app/dashboard/layout.tsx
import { preloadDashboardData } from '@/lib/preload';

export default function DashboardLayout({ children, revenue, activity, alerts }: {
  children: React.ReactNode;
  revenue: React.ReactNode;
  activity: React.ReactNode;
  alerts: React.ReactNode;
}) {
  // Start fetching data as early as possible
  preloadDashboardData();

  return (
    <div className="grid grid-cols-2 gap-6 p-6">
      {revenue}
      {activity}
      {children}
      {alerts}
    </div>
  );
}
```

**Optimization 3: Avoid unnecessary re-renders in slot layouts**:

```tsx
// BAD: This client component wraps a slot, causing hydration on every navigation
'use client';
export function SlotWrapper({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  return (
    <div className={isCollapsed ? 'hidden' : 'block'}>
      {children}
    </div>
  );
}

// GOOD: Keep the slot wrapper as a Server Component
// and only make the toggle button a Client Component
export function SlotWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <CollapseToggle /> {/* Client Component — small */}
      {children}         {/* Server Component — no hydration cost */}
    </div>
  );
}
```

**Performance comparison table**:

| Optimization | Impact | Effort | When to Use |
|---|---|---|---|
| Parallel slots (default) | ~2-4x faster initial load | Low | Always for multi-panel UIs |
| Per-slot `loading.tsx` | Perceived perf improvement | Low | Always |
| Nested Suspense in slots | Faster partial renders | Medium | When slots have mixed-speed data |
| Data preloading in layout | Eliminates waterfall | Medium | When slots share data sources |
| React `cache()` dedup | Eliminates duplicate fetches | Low | When multiple slots fetch same data |
| ISR/revalidation per slot | Reduces server load | Medium | For rarely-changing panels |

---

## Q20. (Advanced) How do you test parallel routes and intercepting routes? What are the edge cases to watch for in production?

**Scenario**: You've built a complex app with parallel routes and intercepting routes. QA reports that some navigation flows break intermittently. How do you systematically test these patterns and what edge cases should you handle?

**Answer**:

**Testing strategy for parallel and intercepting routes**:

```
Test Categories:
┌─────────────────────────────────────────────────────────┐
│  1. Unit Tests      → Individual slot components        │
│  2. Integration     → Slot rendering in layouts         │
│  3. Navigation      → Soft vs hard nav behavior         │
│  4. Edge Cases      → Back/forward, refresh, deep link  │
│  5. Accessibility   → Focus management, keyboard nav    │
│  6. E2E             → Full user flows across slots      │
└─────────────────────────────────────────────────────────┘
```

**E2E tests with Playwright**:

```typescript
// e2e/parallel-routes.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Parallel Routes — Dashboard', () => {
  test('all slots render independently', async ({ page }) => {
    await page.goto('/dashboard');

    // All slots should be visible
    await expect(page.locator('[data-slot="sidebar"]')).toBeVisible();
    await expect(page.locator('[data-slot="main"]')).toBeVisible();
    await expect(page.locator('[data-slot="detail"]')).toBeVisible();
  });

  test('slow slot shows loading while fast slot renders', async ({ page }) => {
    await page.goto('/dashboard');

    // Fast slot (alerts) should render quickly
    await expect(page.locator('[data-slot="alerts"]')).not.toContainText('Loading');

    // Slow slot (revenue) might still be loading
    // Use a short timeout to check if loading state appears
    const revenueLoading = page.locator('[data-slot="revenue"] [data-testid="skeleton"]');
    // Just verify it eventually resolves
    await expect(page.locator('[data-slot="revenue"]')).toContainText('Revenue', {
      timeout: 10000,
    });
  });

  test('error in one slot does not crash others', async ({ page }) => {
    // Trigger error in revenue API
    await page.route('**/api/revenue', (route) =>
      route.fulfill({ status: 500, body: 'Internal Server Error' })
    );

    await page.goto('/dashboard');

    // Revenue shows error
    await expect(page.locator('[data-slot="revenue"]')).toContainText('unavailable');

    // Other slots still work
    await expect(page.locator('[data-slot="activity"]')).toBeVisible();
    await expect(page.locator('[data-slot="alerts"]')).toBeVisible();

    // Retry button works
    await page.unroute('**/api/revenue');
    await page.locator('[data-slot="revenue"] button:text("Retry")').click();
    await expect(page.locator('[data-slot="revenue"]')).toContainText('Revenue');
  });

  test('slot default.tsx renders on unmatched routes', async ({ page }) => {
    await page.goto('/dashboard/settings');

    // @detail slot should show default (no detail for settings)
    await expect(page.locator('[data-slot="detail"]')).toContainText('No item selected');
  });
});

test.describe('Intercepting Routes — Photo Modal', () => {
  test('soft navigation opens modal, hard navigation shows full page', async ({ page }) => {
    await page.goto('/feed');

    // Click photo link (soft navigation)
    await page.click('a[href="/photo/1"]');

    // Modal should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Feed should still be visible behind modal
    await expect(page.locator('[data-testid="feed-grid"]')).toBeVisible();

    // URL should update
    expect(page.url()).toContain('/photo/1');

    // Now refresh (hard navigation)
    await page.reload();

    // Modal should NOT be visible
    await expect(page.locator('[role="dialog"]')).not.toBeVisible();

    // Full photo page should render
    await expect(page.locator('[data-testid="full-photo-page"]')).toBeVisible();
  });

  test('modal closes on Escape key', async ({ page }) => {
    await page.goto('/feed');
    await page.click('a[href="/photo/1"]');

    await expect(page.locator('[role="dialog"]')).toBeVisible();

    await page.keyboard.press('Escape');

    await expect(page.locator('[role="dialog"]')).not.toBeVisible();
    expect(page.url()).toContain('/feed');
  });

  test('modal closes on overlay click', async ({ page }) => {
    await page.goto('/feed');
    await page.click('a[href="/photo/1"]');

    // Click the overlay (not the modal content)
    await page.locator('[role="dialog"]').click({ position: { x: 10, y: 10 } });

    await expect(page.locator('[role="dialog"]')).not.toBeVisible();
  });

  test('browser back from modal returns to previous page', async ({ page }) => {
    await page.goto('/feed');
    await page.click('a[href="/photo/1"]');

    await expect(page.locator('[role="dialog"]')).toBeVisible();

    await page.goBack();

    await expect(page.locator('[role="dialog"]')).not.toBeVisible();
    expect(page.url()).toContain('/feed');
  });

  test('shared URL shows full page with all metadata', async ({ page }) => {
    // Direct navigation (simulating a shared link)
    await page.goto('/photo/42');

    // Should show full page, not modal
    await expect(page.locator('[data-testid="full-photo-page"]')).toBeVisible();

    // Check SEO metadata
    const title = await page.title();
    expect(title).toContain('Photo');

    // Check OG tags
    const ogImage = await page.getAttribute('meta[property="og:image"]', 'content');
    expect(ogImage).toBeTruthy();
  });
});

test.describe('Edge Cases', () => {
  test('rapid navigation between slots does not cause race conditions', async ({ page }) => {
    await page.goto('/mail/inbox');

    // Rapidly click through emails
    for (let i = 1; i <= 5; i++) {
      await page.click(`a[href="/mail/inbox/${i}"]`, { noWaitAfter: true });
    }

    // Wait for final email to load
    await expect(page.locator('[data-testid="email-detail"]')).toBeVisible();

    // Should show email 5 (the last one clicked)
    await expect(page.locator('[data-testid="email-detail"]')).toContainText('Email 5');
  });

  test('modal inside modal (nested interception) works correctly', async ({ page }) => {
    await page.goto('/projects');

    // Open project modal
    await page.click('a[href="/project/1"]');
    await expect(page.locator('[data-testid="project-modal"]')).toBeVisible();

    // Click "Edit" inside modal
    await page.click('a[href="/project/1/edit"]');
    await expect(page.locator('[data-testid="edit-modal"]')).toBeVisible();

    // Close edit modal → back to project modal
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-testid="edit-modal"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="project-modal"]')).toBeVisible();
  });

  test('parallel route with failed fetch allows retry without full reload', async ({ page }) => {
    let failCount = 0;
    await page.route('**/api/activity', (route) => {
      if (failCount < 1) {
        failCount++;
        route.fulfill({ status: 500 });
      } else {
        route.fulfill({
          status: 200,
          body: JSON.stringify({ data: [] }),
          headers: { 'Content-Type': 'application/json' },
        });
      }
    });

    await page.goto('/dashboard');

    // Should show error
    await expect(page.locator('[data-slot="activity"]')).toContainText('unavailable');

    // Click retry
    await page.click('[data-slot="activity"] button:text("Retry")');

    // Should now work
    await expect(page.locator('[data-slot="activity"]')).not.toContainText('unavailable');
  });
});
```

**Production edge cases checklist**:

| Edge Case | Issue | Solution |
|-----------|-------|---------|
| Missing `default.tsx` | 404 on hard navigation | Add `default.tsx` to every slot |
| Stale slot state | Slot shows outdated data after navigation | Use `router.refresh()` or revalidation |
| Modal scroll lock | Body scrolls behind modal | Set `overflow: hidden` on body, restore on unmount |
| Focus trap in modals | Tab key escapes modal | Implement proper focus trap |
| Multiple modals | Second modal doesn't stack correctly | Use z-index layers and portal management |
| SEO for intercepted routes | Search engines see modal, not full page | Intercepted routes aren't crawled (soft-only) |
| Prefetching parallel routes | All slot routes are prefetched (heavy) | Disable prefetch on less-used routes |
| Browser extensions | Extensions inject elements breaking z-index | Use portals for modals |
| Mobile gestures | Swipe back triggers inconsistent behavior | Test on real devices |
| `router.refresh()` in modal | Destroys modal state | Guard refresh with state check |

---
