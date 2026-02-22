# 10. Error Handling & Loading States

## Topic Introduction

Next.js App Router provides a **convention-based error and loading system** built on React's Suspense and Error Boundary primitives. Instead of manually wrapping components, you define special files (`error.tsx`, `loading.tsx`, `not-found.tsx`, `global-error.tsx`) that automatically create the right boundaries at the right level of the component tree. This gives you **per-route error isolation**, **streaming-aware loading states**, and **graceful degradation** without complex boilerplate.

```
┌─────────────────────────────────────────────────────────────────────┐
│            Next.js Error & Loading Architecture                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  app/layout.tsx (Root Layout — NOT caught by error.tsx)              │
│  ├── global-error.tsx  ◄── Catches ROOT layout errors               │
│  │                                                                   │
│  ├── error.tsx         ◄── Catches page.tsx errors at this level    │
│  │                                                                   │
│  ├── loading.tsx       ◄── Auto-wraps page.tsx in <Suspense>       │
│  │                                                                   │
│  ├── not-found.tsx     ◄── Triggered by notFound() or 404          │
│  │                                                                   │
│  └── dashboard/                                                      │
│      ├── layout.tsx    ◄── Dashboard layout                         │
│      ├── error.tsx     ◄── Catches dashboard/* page errors          │
│      ├── loading.tsx   ◄── Loading state for dashboard/*            │
│      └── page.tsx      ◄── Dashboard page                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**How the component tree is assembled**:

```
Conceptual React tree for /dashboard:

<RootLayout>                           ← app/layout.tsx
  <GlobalErrorBoundary>                ← app/global-error.tsx
    <ErrorBoundary fallback={Error}>   ← app/error.tsx
      <Suspense fallback={Loading}>    ← app/loading.tsx
        <DashboardLayout>              ← app/dashboard/layout.tsx
          <ErrorBoundary fallback={DashError}> ← app/dashboard/error.tsx
            <Suspense fallback={DashLoading}>  ← app/dashboard/loading.tsx
              <DashboardPage />                ← app/dashboard/page.tsx
            </Suspense>
          </ErrorBoundary>
        </DashboardLayout>
      </Suspense>
    </ErrorBoundary>
  </GlobalErrorBoundary>
</RootLayout>
```

**Key architectural rules**:
1. `error.tsx` catches errors in `page.tsx` and all child components at the same directory level — but NOT in `layout.tsx` at the same level
2. To catch layout errors, the `error.tsx` must be in the **parent** directory
3. `global-error.tsx` is the only way to catch root layout errors
4. `loading.tsx` creates an automatic `<Suspense>` boundary around `page.tsx`
5. `not-found.tsx` is triggered by the `notFound()` function or unmatched routes
6. Error boundaries are **Client Components** — they must use `"use client"`

**Next.js 15/16 Updates**:
- `error.tsx` now receives the `error` object with `digest` property for server error identification
- Improved streaming error recovery — errors in Suspense boundaries don't kill the entire stream
- Better error overlay in development with source map integration
- `reset()` function works with server-side cache invalidation
- Parallel route error isolation — one slot can error without affecting others

---

## Q1. (Beginner) What is `error.tsx` and how does it work as an error boundary in the App Router?

**Scenario**: Your `/products` page crashes because the product API is down. Without error handling, users see a blank white screen. You need graceful error recovery.

**Answer**:

`error.tsx` is a special file that automatically creates a React Error Boundary around the page component in the same directory. It must be a **Client Component** (because React error boundaries are class-based or use client-side hooks).

```tsx
// app/products/error.tsx
'use client'; // Error boundaries MUST be Client Components

import { useEffect } from 'react';

export default function ProductsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to your monitoring service
    console.error('Products page error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <div className="text-center max-w-md">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Something went wrong
        </h2>
        <p className="text-gray-600 mb-6">
          We couldn&apos;t load the products. This might be a temporary issue.
        </p>

        {/* Show error details in development */}
        {process.env.NODE_ENV === 'development' && (
          <pre className="text-left text-sm bg-red-50 text-red-800 p-4 rounded-lg mb-4 overflow-auto">
            {error.message}
            {error.stack && `\n\n${error.stack}`}
          </pre>
        )}

        {/* Show digest for server errors (useful for support tickets) */}
        {error.digest && (
          <p className="text-xs text-gray-400 mb-4">
            Error ID: {error.digest}
          </p>
        )}

        <div className="flex gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
          <a
            href="/"
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Go Home
          </a>
        </div>
      </div>
    </div>
  );
}
```

**How `reset()` works**:

```
Error occurs:
┌────────────┐     ┌──────────────┐
│ page.tsx    │────▶│ error.tsx     │
│ throws!    │     │ (displayed)   │
└────────────┘     └──────┬───────┘
                          │
User clicks "Try Again":  │
                          │ reset()
                          ▼
                   ┌──────────────┐
                   │ page.tsx      │
                   │ (re-rendered) │
                   │ (fresh attempt│
                   │  — no cache)  │
                   └──────────────┘
```

The `reset()` function attempts to re-render the error boundary's children. If the underlying issue is fixed (e.g., the API is back up), the page will render successfully. If not, the error boundary catches the error again.

```tsx
// app/products/page.tsx — The page that might throw
export default async function ProductsPage() {
  // If this fetch fails, error.tsx catches it
  const res = await fetch('https://api.example.com/products', {
    next: { revalidate: 60 },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch products: ${res.status} ${res.statusText}`);
  }

  const products = await res.json();

  return (
    <div className="grid grid-cols-3 gap-6">
      {products.map((p: any) => (
        <div key={p.id} className="border rounded-lg p-4">
          <h3>{p.name}</h3>
          <p>${p.price}</p>
        </div>
      ))}
    </div>
  );
}
```

**Important**: `error.tsx` does NOT catch errors thrown in `layout.tsx` at the same level. That's because the error boundary wraps inside the layout, not around it.

---

## Q2. (Beginner) What is `loading.tsx` and how does it create automatic Suspense boundaries?

**Scenario**: Your dashboard page fetches data from 3 different APIs. Users see nothing for 2 seconds while all data loads. You want an instant loading skeleton.

**Answer**:

`loading.tsx` is a special file that Next.js automatically wraps around `page.tsx` using React's `<Suspense>`. This means the loading UI shows **immediately** while the page component's async operations complete.

```tsx
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div className="p-6 animate-pulse">
      {/* Stats row skeleton */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-gray-200 rounded-xl h-28" />
        ))}
      </div>

      {/* Chart skeleton */}
      <div className="bg-gray-200 rounded-xl h-64 mb-8" />

      {/* Table skeleton */}
      <div className="space-y-3">
        <div className="bg-gray-200 rounded h-10" /> {/* header */}
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="bg-gray-100 rounded h-12" />
        ))}
      </div>
    </div>
  );
}
```

**What Next.js generates behind the scenes**:

```tsx
// This is conceptually what Next.js creates:
import Loading from './loading';
import Page from './page';

<Suspense fallback={<Loading />}>
  <Page />
</Suspense>
```

```tsx
// app/dashboard/page.tsx — async Server Component
export default async function DashboardPage() {
  // All these fetches run in parallel on the server
  const [stats, chart, orders] = await Promise.all([
    fetch('https://api.example.com/stats').then(r => r.json()),
    fetch('https://api.example.com/chart-data').then(r => r.json()),
    fetch('https://api.example.com/recent-orders').then(r => r.json()),
  ]);

  return (
    <div className="p-6">
      <StatsCards stats={stats} />
      <RevenueChart data={chart} />
      <OrdersTable orders={orders} />
    </div>
  );
}
```

**Loading state flow**:

```
1. User navigates to /dashboard
2. Next.js immediately sends loading.tsx HTML (streaming SSR)
3. Server starts fetching data for page.tsx
4. loading.tsx skeleton is visible to user (instant!)
5. When all data is fetched, page.tsx renders
6. Streaming SSR replaces skeleton with real content
7. React hydrates the page
```

**Nested loading states**:

```
app/
├── loading.tsx          → Shows while root page loads
├── page.tsx
└── dashboard/
    ├── loading.tsx      → Shows while dashboard page loads
    ├── page.tsx
    └── settings/
        ├── loading.tsx  → Shows while settings page loads
        └── page.tsx
```

When navigating from `/` to `/dashboard/settings`, the user sees:
1. Root layout stays visible (persists)
2. Dashboard `loading.tsx` appears instantly
3. Dashboard layout renders when ready
4. Settings `loading.tsx` appears
5. Settings page renders when data is ready

---

## Q3. (Beginner) How do `not-found.tsx` and the `notFound()` function work?

**Scenario**: Users access `/products/nonexistent-id`. Instead of a generic error, you need a helpful 404 page with search suggestions and navigation.

**Answer**:

`not-found.tsx` renders when `notFound()` is called or when a URL doesn't match any route. It works at every route level, allowing custom 404 pages per section.

```tsx
// app/not-found.tsx — Root-level 404 page
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <h1 className="text-6xl font-bold text-gray-200 mb-4">404</h1>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        Page Not Found
      </h2>
      <p className="text-gray-600 mb-8 text-center max-w-md">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <div className="flex gap-4">
        <Link
          href="/"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Go Home
        </Link>
        <Link
          href="/search"
          className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Search
        </Link>
      </div>
    </div>
  );
}
```

**Using `notFound()` in a dynamic route**:

```tsx
// app/products/[id]/page.tsx
import { notFound } from 'next/navigation';

interface Product {
  id: string;
  name: string;
  price: number;
  description: string;
}

async function getProduct(id: string): Promise<Product | null> {
  const res = await fetch(`https://api.example.com/products/${id}`, {
    next: { revalidate: 3600 },
  });

  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API Error: ${res.status}`);

  return res.json();
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);

  // Calling notFound() triggers the nearest not-found.tsx
  if (!product) {
    notFound();
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold">{product.name}</h1>
      <p className="text-2xl text-green-600 mt-2">${product.price}</p>
      <p className="mt-4 text-gray-700">{product.description}</p>
    </div>
  );
}
```

**Per-section 404 page**:

```tsx
// app/products/not-found.tsx — Product-specific 404
import Link from 'next/link';

export default function ProductNotFound() {
  return (
    <div className="max-w-2xl mx-auto p-8 text-center">
      <h2 className="text-2xl font-bold mb-4">Product Not Found</h2>
      <p className="text-gray-600 mb-6">
        This product may have been removed or the URL might be incorrect.
      </p>
      <div className="space-y-3">
        <Link
          href="/products"
          className="block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Browse All Products
        </Link>
        <Link
          href="/products?sale=true"
          className="block px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          View Sale Items
        </Link>
      </div>
    </div>
  );
}
```

**Key behaviors**:

| Trigger | Behavior |
|---------|----------|
| `notFound()` in page | Renders nearest `not-found.tsx` up the tree |
| URL matches no route | Renders root `app/not-found.tsx` |
| `notFound()` returns HTTP 404 status | Yes, automatically sets `404` status code |
| `notFound()` in layout | Renders the `not-found.tsx` from the PARENT route |
| `notFound()` in Server Component | Works — caught during server render |
| `notFound()` in Client Component | Works — throws a special error caught by Next.js |

---

## Q4. (Beginner) What is `global-error.tsx` and when do you need it?

**Scenario**: Your root `layout.tsx` has a bug in the authentication provider that crashes on certain user sessions. Since `error.tsx` at the root level can't catch layout errors at the same level, users see a blank screen.

**Answer**:

`global-error.tsx` is a special error boundary that wraps the **entire application**, including the root `layout.tsx`. It's the last line of defense.

```
Error Boundary Hierarchy:
┌─────────────────────────────────────────────┐
│  global-error.tsx (catches EVERYTHING)       │
│  ┌─────────────────────────────────────────┐ │
│  │  layout.tsx (root layout)               │ │
│  │  ┌───────────────────────────────────┐  │ │
│  │  │  error.tsx (catches page errors)  │  │ │
│  │  │  ┌─────────────────────────────┐  │  │ │
│  │  │  │  page.tsx                   │  │  │ │
│  │  │  └─────────────────────────────┘  │  │ │
│  │  └───────────────────────────────────┘  │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

```tsx
// app/global-error.tsx
'use client'; // Must be a Client Component

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    // IMPORTANT: global-error MUST include <html> and <body> tags
    // because it REPLACES the root layout when triggered
    <html lang="en">
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen bg-white p-8">
          <div className="text-center max-w-lg">
            <div className="text-6xl mb-4">⚠️</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Application Error
            </h1>
            <p className="text-gray-600 mb-6">
              A critical error occurred. Our team has been notified.
            </p>

            {error.digest && (
              <p className="text-sm text-gray-400 mb-4 font-mono">
                Reference: {error.digest}
              </p>
            )}

            <div className="flex gap-3 justify-center">
              <button
                onClick={() => reset()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Try Again
              </button>
              <a
                href="/"
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Return Home
              </a>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
```

**Key differences between `error.tsx` and `global-error.tsx`**:

| Feature | `error.tsx` | `global-error.tsx` |
|---------|-------------|-------------------|
| Catches layout errors at same level | No | Yes (root layout) |
| Must include `<html>/<body>` | No | **Yes** (replaces root layout) |
| Can be nested per-route | Yes | Only one (at root) |
| When triggered | Page/child component errors | Root layout/page errors |
| In production | Common fallback | Last resort emergency |
| Development only? | No, works in all envs | Works in all envs |

**When `global-error.tsx` activates**:

```
Root layout throws → global-error.tsx activates
Root page throws AND no root error.tsx → global-error.tsx activates
Any unhandled error bubbles to root → global-error.tsx activates
```

**Important**: `global-error.tsx` is NOT shown in development — Next.js shows its development error overlay instead. It only renders in production. Always test it by building with `next build` and running `next start`.

---

## Q5. (Beginner) How does the `reset()` function work in error boundaries, and what are its limitations?

**Scenario**: A transient network error crashes your page. The user clicks "Try Again" but it doesn't seem to work because the cached data still causes the same error.

**Answer**:

The `reset()` function attempts to re-render the error boundary's children (the page component). However, it has important nuances:

```tsx
// app/dashboard/error.tsx
'use client';

import { useEffect, useState } from 'react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  useEffect(() => {
    // Log each error occurrence
    console.error(`Dashboard error (attempt ${retryCount + 1}):`, error.message);
  }, [error, retryCount]);

  const handleRetry = () => {
    if (retryCount < maxRetries) {
      setRetryCount((prev) => prev + 1);
      reset(); // Re-render the page component
    }
  };

  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold mb-4">Dashboard Error</h2>
      <p className="text-gray-600 mb-6">{error.message}</p>

      {retryCount < maxRetries ? (
        <button
          onClick={handleRetry}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Try Again ({maxRetries - retryCount} attempts remaining)
        </button>
      ) : (
        <div>
          <p className="text-red-600 mb-4">
            Multiple retry attempts failed. Please try again later.
          </p>
          <a href="/dashboard" className="text-blue-600 underline">
            Hard Refresh
          </a>
        </div>
      )}
    </div>
  );
}
```

**What `reset()` does and doesn't do**:

```
reset() DOES:
  ✅ Re-renders the error boundary's children
  ✅ Clears the error state in the boundary
  ✅ Attempt to render page.tsx again

reset() DOES NOT:
  ❌ Clear the Next.js Data Cache (fetch cache)
  ❌ Clear React's client-side cache
  ❌ Perform a hard navigation
  ❌ Re-run the full server render from scratch
  ❌ Clear router cache
```

**Pattern: Reset with cache invalidation using Server Action**:

```tsx
// app/dashboard/error.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useTransition } from 'react';
import { revalidateDashboard } from './actions';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const handleRetryWithRevalidation = () => {
    startTransition(async () => {
      // Invalidate server cache first
      await revalidateDashboard();
      // Then refresh the router cache
      router.refresh();
      // Then reset the error boundary
      reset();
    });
  };

  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold mb-4">Something went wrong</h2>
      <button
        onClick={handleRetryWithRevalidation}
        disabled={isPending}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
      >
        {isPending ? 'Retrying...' : 'Try Again'}
      </button>
    </div>
  );
}
```

```tsx
// app/dashboard/actions.ts
'use server';

import { revalidatePath } from 'next/cache';

export async function revalidateDashboard() {
  revalidatePath('/dashboard');
}
```

---

## Q6. (Intermediate) How do nested error boundaries work, and how do you handle errors at different route levels?

**Scenario**: Your e-commerce site has: root layout → shop layout → product page. An error in the product page should show a product-level error, but an error in the shop layout should show a shop-level error while keeping the root navigation intact.

**Answer**:

Error boundaries follow a **bubbling** pattern. An error travels up the tree until it finds the nearest `error.tsx` that can catch it.

```
Route structure:
app/
├── layout.tsx          ← Root layout (navigation, footer)
├── error.tsx           ← Catches errors from app/page.tsx
├── shop/
│   ├── layout.tsx      ← Shop layout (sidebar, categories)
│   ├── error.tsx       ← Catches errors from shop pages
│   └── [productId]/
│       ├── error.tsx   ← Catches product page errors
│       └── page.tsx    ← Product page
```

```
Component tree (for /shop/abc123):

<RootLayout>                                    ← app/layout.tsx
  <ErrorBoundary fallback={RootError}>          ← app/error.tsx
    <ShopLayout>                                ← app/shop/layout.tsx
      <ErrorBoundary fallback={ShopError}>      ← app/shop/error.tsx
        <ErrorBoundary fallback={ProductError}> ← app/shop/[productId]/error.tsx
          <ProductPage />                       ← app/shop/[productId]/page.tsx
        </ErrorBoundary>
      </ErrorBoundary>
    </ShopLayout>
  </ErrorBoundary>
</RootLayout>
```

**Error routing scenarios**:

```
Scenario 1: Product page throws
  ProductPage throws → ProductError catches ✅
  ShopLayout stays intact ✅
  RootLayout stays intact ✅

Scenario 2: Shop layout throws
  ShopLayout throws → ShopError CANNOT catch (same level!)
  Error bubbles up → RootError catches ✅
  RootLayout stays intact ✅

Scenario 3: Root layout throws
  RootLayout throws → RootError CANNOT catch (same level!)
  Error bubbles up → global-error.tsx catches ✅
```

**Implementation**:

```tsx
// app/layout.tsx — Root layout
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="h-16 border-b flex items-center px-6">
          <nav>
            <a href="/">Home</a>
            <a href="/shop" className="ml-4">Shop</a>
          </nav>
        </header>
        <main>{children}</main>
        <footer className="h-16 border-t" />
      </body>
    </html>
  );
}
```

```tsx
// app/error.tsx — Root-level error (keeps nav/footer)
'use client';

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
      <p className="text-gray-600 mb-6">{error.message}</p>
      <button onClick={reset} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
        Try Again
      </button>
    </div>
  );
}
```

```tsx
// app/shop/layout.tsx — Shop layout with sidebar
export default function ShopLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <aside className="w-64 border-r p-4">
        <h3 className="font-bold mb-3">Categories</h3>
        <ul className="space-y-2">
          <li><a href="/shop?cat=electronics">Electronics</a></li>
          <li><a href="/shop?cat=clothing">Clothing</a></li>
          <li><a href="/shop?cat=books">Books</a></li>
        </ul>
      </aside>
      <div className="flex-1 p-6">{children}</div>
    </div>
  );
}
```

```tsx
// app/shop/error.tsx — Shop-level error (keeps root nav + shop sidebar)
'use client';

export default function ShopError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="text-center py-12">
      <h2 className="text-xl font-bold mb-3">Shop Error</h2>
      <p className="text-gray-600 mb-4">
        We couldn&apos;t load this shop section.
      </p>
      <button onClick={reset} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
        Retry
      </button>
    </div>
  );
}
```

```tsx
// app/shop/[productId]/error.tsx — Product-level error (keeps root nav + sidebar)
'use client';

import Link from 'next/link';

export default function ProductError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="text-center py-12">
      <h2 className="text-xl font-bold mb-3">Product Unavailable</h2>
      <p className="text-gray-600 mb-4">
        This product couldn&apos;t be loaded. It may be temporarily unavailable.
      </p>
      <div className="flex gap-3 justify-center">
        <button onClick={reset} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
          Try Again
        </button>
        <Link href="/shop" className="px-4 py-2 border rounded-lg">
          Browse Shop
        </Link>
      </div>
    </div>
  );
}
```

This nested structure ensures that errors are contained to the smallest possible scope while keeping the rest of the UI functional.

---

## Q7. (Intermediate) How do you implement production error logging with Sentry in Next.js App Router?

**Scenario**: Your production application needs comprehensive error tracking. You need to capture server-side errors, client-side errors, and errors in error boundaries, all with proper source maps and user context.

**Answer**:

Sentry integration in Next.js 15+ uses the `@sentry/nextjs` SDK, which hooks into both the server and client error pipelines.

```
Error Flow with Sentry:
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Server Components    Client Components     Edge Runtime     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ captureExcept│    │ ErrorBoundary│    │ captureExcept│  │
│  │ ion()        │    │ + onError    │    │ ion()        │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                    │          │
│         └───────────────────┼────────────────────┘          │
│                             │                               │
│                             ▼                               │
│                   ┌──────────────────┐                      │
│                   │  Sentry Backend   │                      │
│                   │  • Source maps    │                      │
│                   │  • Session replay │                      │
│                   │  • Performance    │                      │
│                   │  • Alerts         │                      │
│                   └──────────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Setup**:

```bash
npx @sentry/wizard@latest -i nextjs
```

```ts
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,

  // Performance Monitoring
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

  // Session Replay
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  // Filter out noisy errors
  beforeSend(event) {
    // Ignore network errors from ad blockers
    if (event.exception?.values?.[0]?.value?.includes('Failed to fetch')) {
      return null;
    }
    return event;
  },
});
```

```ts
// sentry.server.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.2 : 1.0,

  beforeSend(event) {
    // Scrub sensitive data
    if (event.request?.headers) {
      delete event.request.headers['authorization'];
      delete event.request.headers['cookie'];
    }
    return event;
  },
});
```

```ts
// sentry.edge.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

**Instrumentation hook for server-side error capture**:

```ts
// instrumentation.ts (Next.js 15+ instrumentation hook)
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    await import('./sentry.server.config');
  }

  if (process.env.NEXT_RUNTIME === 'edge') {
    await import('./sentry.edge.config');
  }
}

export const onRequestError = async (
  err: { digest: string } & Error,
  request: {
    path: string;
    method: string;
    headers: { [key: string]: string };
  },
  context: {
    routerKind: 'Pages Router' | 'App Router';
    routePath: string;
    routeType: 'page' | 'route' | 'middleware';
    renderSource: 'react-server-components' | 'react-server-components-payload' | 'server-rendering';
  }
) => {
  const Sentry = await import('@sentry/nextjs');

  Sentry.captureException(err, {
    tags: {
      routerKind: context.routerKind,
      routePath: context.routePath,
      routeType: context.routeType,
    },
    extra: {
      digest: err.digest,
      method: request.method,
      path: request.path,
    },
  });
};
```

**Error boundary with Sentry context**:

```tsx
// app/dashboard/error.tsx
'use client';

import * as Sentry from '@sentry/nextjs';
import { useEffect } from 'react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Capture the error with additional context
    Sentry.captureException(error, {
      tags: {
        section: 'dashboard',
        errorBoundary: true,
      },
      extra: {
        digest: error.digest,
        componentStack: (error as any).componentStack,
      },
    });
  }, [error]);

  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold mb-4">Dashboard Error</h2>
      <p className="text-gray-600 mb-2">
        An unexpected error occurred. Our team has been notified.
      </p>
      {error.digest && (
        <p className="text-xs text-gray-400 mb-6 font-mono">
          Error ID: {error.digest}
        </p>
      )}

      <div className="flex gap-3 justify-center">
        <button onClick={reset} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
          Try Again
        </button>
        <button
          onClick={() => Sentry.showReportDialog({ eventId: Sentry.lastEventId() })}
          className="px-4 py-2 border rounded-lg"
        >
          Report Feedback
        </button>
      </div>
    </div>
  );
}
```

**Next.js config for Sentry source maps**:

```ts
// next.config.ts
import { withSentryConfig } from '@sentry/nextjs';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // ... your config
};

export default withSentryConfig(nextConfig, {
  org: 'your-org',
  project: 'your-project',
  silent: !process.env.CI,

  // Upload source maps for better stack traces
  widenClientFileUpload: true,

  // Hide source maps from end users
  hideSourceMaps: true,

  // Automatically instrument components
  autoInstrumentServerFunctions: true,
  autoInstrumentMiddleware: true,
  autoInstrumentAppDirectory: true,
});
```

---

## Q8. (Intermediate) How do you implement granular loading states using Suspense boundaries inside a single page?

**Scenario**: Your dashboard page has a stats section (fast API, 100ms), a chart section (medium API, 500ms), and a recommendations section (slow ML API, 3s). You want each section to stream in independently as its data becomes available.

**Answer**:

Instead of a single `loading.tsx` for the entire page, use multiple `<Suspense>` boundaries within the page to enable **progressive streaming**:

```
Progressive Streaming Timeline:
────────────────────────────────────────────────── Time
  │
  ├─ 100ms: Stats section renders  ████
  │
  ├─ 500ms: Chart section renders       ████████
  │
  ├─ 3000ms: Recommendations render                    ████████████████
  │
  └─ Each section streams independently!
```

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react';
import { StatsSection } from './components/stats-section';
import { ChartSection } from './components/chart-section';
import { RecommendationsSection } from './components/recommendations-section';

// Skeleton components
function StatsSkeleton() {
  return (
    <div className="grid grid-cols-4 gap-4 animate-pulse">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="h-28 bg-gray-200 rounded-xl" />
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-6 w-48 bg-gray-200 rounded mb-4" />
      <div className="h-64 bg-gray-200 rounded-xl" />
    </div>
  );
}

function RecommendationsSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-6 w-56 bg-gray-200 rounded mb-4" />
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-40 bg-gray-200 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="space-y-8 p-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {/* Fast section — renders in ~100ms */}
      <Suspense fallback={<StatsSkeleton />}>
        <StatsSection />
      </Suspense>

      {/* Medium section — renders in ~500ms */}
      <Suspense fallback={<ChartSkeleton />}>
        <ChartSection />
      </Suspense>

      {/* Slow section — renders in ~3s */}
      <Suspense fallback={<RecommendationsSkeleton />}>
        <RecommendationsSection />
      </Suspense>
    </div>
  );
}
```

```tsx
// app/dashboard/components/stats-section.tsx
// Server Component — fetches data during render

interface DashboardStats {
  totalRevenue: number;
  totalOrders: number;
  activeUsers: number;
  conversionRate: number;
}

async function getStats(): Promise<DashboardStats> {
  const res = await fetch('https://api.example.com/dashboard/stats', {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function StatsSection() {
  const stats = await getStats();

  const cards = [
    { label: 'Total Revenue', value: `$${stats.totalRevenue.toLocaleString()}`, color: 'text-green-600' },
    { label: 'Total Orders', value: stats.totalOrders.toLocaleString(), color: 'text-blue-600' },
    { label: 'Active Users', value: stats.activeUsers.toLocaleString(), color: 'text-purple-600' },
    { label: 'Conversion Rate', value: `${stats.conversionRate}%`, color: 'text-orange-600' },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="bg-white border rounded-xl p-5">
          <p className="text-sm text-gray-500">{card.label}</p>
          <p className={`text-2xl font-bold mt-1 ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}
```

```tsx
// app/dashboard/components/chart-section.tsx
async function getChartData() {
  const res = await fetch('https://api.example.com/dashboard/chart', {
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error('Failed to fetch chart data');
  return res.json();
}

export async function ChartSection() {
  const data = await getChartData();

  return (
    <div className="bg-white border rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Revenue Overview</h2>
      {/* Your chart component here */}
      <div className="h-64 flex items-end gap-2">
        {data.monthly.map((month: { name: string; value: number }, i: number) => (
          <div key={i} className="flex-1 flex flex-col items-center">
            <div
              className="w-full bg-blue-500 rounded-t"
              style={{ height: `${(month.value / data.max) * 100}%` }}
            />
            <span className="text-xs text-gray-500 mt-1">{month.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/components/recommendations-section.tsx
async function getRecommendations() {
  // Slow ML-powered recommendations API
  const res = await fetch('https://ml.example.com/recommendations', {
    next: { revalidate: 3600 },
  });
  if (!res.ok) throw new Error('Failed to fetch recommendations');
  return res.json();
}

export async function RecommendationsSection() {
  const recs = await getRecommendations();

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Recommended for You</h2>
      <div className="grid grid-cols-3 gap-4">
        {recs.map((rec: any) => (
          <div key={rec.id} className="border rounded-lg p-4">
            <h3 className="font-medium">{rec.title}</h3>
            <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Important**: Each `<Suspense>` boundary creates an independent streaming chunk. The HTML for the skeleton is sent immediately, and each section's HTML is streamed in as its data resolves. This means the user sees a progressively building page rather than waiting for the slowest API.

---

## Q9. (Intermediate) How do error boundaries interact with parallel routes and intercepting routes?

**Scenario**: Your dashboard uses parallel routes for `@analytics`, `@notifications`, and `@activity` slots. If the analytics API fails, you want only the analytics panel to show an error — the other slots should continue working normally.

**Answer**:

Parallel routes provide **natural error isolation**. Each slot can have its own `error.tsx`, so a failure in one slot doesn't affect the others.

```
app/dashboard/
├── layout.tsx                 ← Composes the slots
├── page.tsx                   ← Main dashboard content
├── @analytics/
│   ├── page.tsx              ← Analytics panel
│   ├── error.tsx             ← Error ONLY for analytics ✅
│   ├── loading.tsx           ← Loading ONLY for analytics
│   └── default.tsx           ← Fallback for unmatched routes
├── @notifications/
│   ├── page.tsx              ← Notifications panel
│   ├── error.tsx             ← Error ONLY for notifications ✅
│   ├── loading.tsx           ← Loading ONLY for notifications
│   └── default.tsx
└── @activity/
    ├── page.tsx              ← Activity feed
    ├── error.tsx             ← Error ONLY for activity ✅
    ├── loading.tsx           ← Loading ONLY for activity
    └── default.tsx
```

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  analytics,
  notifications,
  activity,
}: {
  children: React.ReactNode;
  analytics: React.ReactNode;
  notifications: React.ReactNode;
  activity: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-12 gap-6 p-6">
      {/* Main content area */}
      <div className="col-span-8">{children}</div>

      {/* Right sidebar with parallel route slots */}
      <div className="col-span-4 space-y-6">
        {analytics}
        {notifications}
        {activity}
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/@analytics/page.tsx
async function getAnalytics() {
  const res = await fetch('https://api.example.com/analytics', {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error('Analytics API unavailable');
  return res.json();
}

export default async function AnalyticsPanel() {
  const data = await getAnalytics();
  return (
    <div className="bg-white border rounded-xl p-4">
      <h3 className="font-semibold mb-3">Analytics</h3>
      <p className="text-2xl font-bold">{data.visitors.toLocaleString()}</p>
      <p className="text-sm text-gray-500">visitors today</p>
    </div>
  );
}
```

```tsx
// app/dashboard/@analytics/error.tsx
'use client';

export default function AnalyticsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="bg-white border border-red-200 rounded-xl p-4">
      <h3 className="font-semibold mb-2 text-red-600">Analytics Unavailable</h3>
      <p className="text-sm text-gray-600 mb-3">
        Could not load analytics data.
      </p>
      <button
        onClick={reset}
        className="text-sm text-blue-600 hover:underline"
      >
        Retry
      </button>
    </div>
  );
}
```

**Error isolation visualization**:

```
When analytics API fails:

┌────────────────────────────────────────────────┐
│                Dashboard Layout                  │
│  ┌──────────────────┐  ┌───────────────────┐   │
│  │                   │  │ Analytics ERROR    │   │
│  │   Main Content    │  │ ┌───────────────┐ │   │
│  │   (works fine ✅) │  │ │ "Unavailable" │ │   │
│  │                   │  │ │  [Retry]      │ │   │
│  │                   │  │ └───────────────┘ │   │
│  │                   │  ├───────────────────┤   │
│  │                   │  │ Notifications ✅   │   │
│  │                   │  │ (works fine)      │   │
│  │                   │  ├───────────────────┤   │
│  │                   │  │ Activity Feed ✅   │   │
│  │                   │  │ (works fine)      │   │
│  └──────────────────┘  └───────────────────┘   │
└────────────────────────────────────────────────┘
```

**Intercepting route error handling**:

```tsx
// app/@modal/(.)photo/[id]/error.tsx
// Error in intercepted modal route
'use client';

import { useRouter } from 'next/navigation';

export default function ModalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-md">
        <h3 className="font-bold text-lg mb-2">Could not load photo</h3>
        <p className="text-gray-600 mb-4">{error.message}</p>
        <div className="flex gap-3">
          <button onClick={reset} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
            Retry
          </button>
          <button onClick={() => router.back()} className="px-4 py-2 border rounded-lg">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
```

Parallel routes provide the best error isolation pattern in Next.js. Each slot is independently rendered, loaded, and error-handled. This is ideal for dashboard-style layouts where partial functionality is better than total failure.

---

## Q10. (Intermediate) How do you implement custom error pages for different HTTP status codes (400, 403, 500)?

**Scenario**: Your app needs distinct error pages for different scenarios: 400 for bad requests, 403 for unauthorized access, 404 for not found, and 500 for server errors. Each should have a unique design and helpful actions.

**Answer**:

Next.js App Router doesn't have built-in per-status-code error pages like the Pages Router's `pages/404.tsx` and `pages/500.tsx`. Instead, you create a custom error handling system.

```tsx
// lib/errors.ts
export class AppError extends Error {
  public readonly statusCode: number;
  public readonly code: string;

  constructor(message: string, statusCode: number, code: string) {
    super(message);
    this.name = 'AppError';
    this.statusCode = statusCode;
    this.code = code;
  }
}

export class BadRequestError extends AppError {
  constructor(message = 'Bad Request') {
    super(message, 400, 'BAD_REQUEST');
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'Access Denied') {
    super(message, 403, 'FORBIDDEN');
  }
}

export class NotFoundError extends AppError {
  constructor(message = 'Resource Not Found') {
    super(message, 404, 'NOT_FOUND');
  }
}

export class InternalError extends AppError {
  constructor(message = 'Internal Server Error') {
    super(message, 500, 'INTERNAL_ERROR');
  }
}
```

```tsx
// app/error.tsx — Unified error boundary with status-aware UI
'use client';

import { useEffect, useMemo } from 'react';
import Link from 'next/link';

interface ErrorConfig {
  title: string;
  description: string;
  icon: string;
  actions: Array<{ label: string; href?: string; onClick?: () => void; primary?: boolean }>;
}

function getErrorConfig(error: Error & { digest?: string }, reset: () => void): ErrorConfig {
  const message = error.message.toLowerCase();

  // Parse error type from message or custom properties
  if (message.includes('forbidden') || message.includes('access denied') || message.includes('403')) {
    return {
      title: 'Access Denied',
      description: 'You don\'t have permission to view this page. Please contact your administrator if you believe this is an error.',
      icon: '🔒',
      actions: [
        { label: 'Go to Dashboard', href: '/dashboard', primary: true },
        { label: 'Contact Support', href: '/support' },
      ],
    };
  }

  if (message.includes('bad request') || message.includes('validation') || message.includes('400')) {
    return {
      title: 'Bad Request',
      description: 'The request could not be processed. Please check your input and try again.',
      icon: '⚠️',
      actions: [
        { label: 'Try Again', onClick: reset, primary: true },
        { label: 'Go Back', href: 'javascript:history.back()' },
      ],
    };
  }

  if (message.includes('rate limit') || message.includes('429')) {
    return {
      title: 'Too Many Requests',
      description: 'You\'ve made too many requests. Please wait a moment and try again.',
      icon: '⏳',
      actions: [
        { label: 'Try Again', onClick: reset, primary: true },
      ],
    };
  }

  // Default: 500 / Unknown error
  return {
    title: 'Something Went Wrong',
    description: 'An unexpected error occurred. Our team has been notified and is working on a fix.',
    icon: '💥',
    actions: [
      { label: 'Try Again', onClick: reset, primary: true },
      { label: 'Go Home', href: '/' },
    ],
  };
}

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const config = useMemo(() => getErrorConfig(error, reset), [error, reset]);

  useEffect(() => {
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4">{config.icon}</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{config.title}</h1>
        <p className="text-gray-600 mb-8">{config.description}</p>

        {error.digest && (
          <p className="text-xs text-gray-400 mb-6 font-mono">
            Error Reference: {error.digest}
          </p>
        )}

        <div className="flex gap-3 justify-center flex-wrap">
          {config.actions.map((action, i) =>
            action.onClick ? (
              <button
                key={i}
                onClick={action.onClick}
                className={`px-5 py-2.5 rounded-lg transition-colors ${
                  action.primary
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {action.label}
              </button>
            ) : (
              <Link
                key={i}
                href={action.href!}
                className={`px-5 py-2.5 rounded-lg transition-colors ${
                  action.primary
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {action.label}
              </Link>
            )
          )}
        </div>
      </div>
    </div>
  );
}
```

**Throwing typed errors from Server Components**:

```tsx
// app/admin/page.tsx
import { getSession } from '@/lib/auth';

export default async function AdminPage() {
  const session = await getSession();

  if (!session) {
    throw new Error('403: Access Denied — You must be logged in');
  }

  if (session.role !== 'admin') {
    throw new Error('403: Access Denied — Admin access required');
  }

  // ... admin page content
}
```

This pattern gives you status-aware error pages while working within the constraints of App Router error boundaries.

---

## Q11. (Intermediate) How do you implement retry patterns with exponential backoff in error boundaries?

**Scenario**: Your page depends on a flaky third-party API that sometimes returns 503 errors. You want automatic retries with exponential backoff before showing the error UI.

**Answer**:

There are two levels of retry: **server-side** (retry the fetch before rendering) and **client-side** (retry via the error boundary reset).

**Server-side retry with exponential backoff**:

```tsx
// lib/fetch-with-retry.ts
interface RetryConfig {
  maxRetries: number;
  baseDelay: number;      // ms
  maxDelay: number;        // ms
  retryableStatuses: number[];
}

const defaultConfig: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

export async function fetchWithRetry(
  url: string,
  options?: RequestInit & { retry?: Partial<RetryConfig> }
): Promise<Response> {
  const config = { ...defaultConfig, ...options?.retry };
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      if (response.ok) return response;

      if (config.retryableStatuses.includes(response.status) && attempt < config.maxRetries) {
        const delay = Math.min(
          config.baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
          config.maxDelay
        );
        console.warn(
          `[Retry] ${url} returned ${response.status}, attempt ${attempt + 1}/${config.maxRetries}, waiting ${delay}ms`
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
        continue;
      }

      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < config.maxRetries) {
        const delay = Math.min(
          config.baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
          config.maxDelay
        );
        console.warn(
          `[Retry] ${url} failed: ${lastError.message}, attempt ${attempt + 1}/${config.maxRetries}, waiting ${delay}ms`
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError || new Error(`Failed to fetch ${url} after ${config.maxRetries} retries`);
}
```

```tsx
// app/dashboard/page.tsx — Using fetchWithRetry
import { fetchWithRetry } from '@/lib/fetch-with-retry';

export default async function DashboardPage() {
  const data = await fetchWithRetry('https://flaky-api.example.com/data', {
    next: { revalidate: 60 },
    retry: {
      maxRetries: 3,
      baseDelay: 500,
      retryableStatuses: [502, 503, 504],
    },
  });

  const result = await data.json();
  return <div>{/* render data */}</div>;
}
```

**Client-side auto-retry error boundary**:

```tsx
// components/auto-retry-error-boundary.tsx
'use client';

import { useEffect, useState, useCallback, useRef } from 'react';

interface AutoRetryErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function AutoRetryError({ error, reset }: AutoRetryErrorProps) {
  const [retryCount, setRetryCount] = useState(0);
  const [isAutoRetrying, setIsAutoRetrying] = useState(true);
  const [countdown, setCountdown] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const maxAutoRetries = 3;
  const getDelay = (attempt: number) => Math.min(1000 * Math.pow(2, attempt), 16000);

  const retry = useCallback(() => {
    setRetryCount((prev) => prev + 1);
    reset();
  }, [reset]);

  useEffect(() => {
    if (!isAutoRetrying || retryCount >= maxAutoRetries) {
      setIsAutoRetrying(false);
      return;
    }

    const delay = getDelay(retryCount);
    setCountdown(Math.ceil(delay / 1000));

    // Countdown timer
    const countdownInterval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(countdownInterval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // Retry timer
    timerRef.current = setTimeout(() => {
      clearInterval(countdownInterval);
      retry();
    }, delay);

    return () => {
      clearInterval(countdownInterval);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [retryCount, isAutoRetrying, retry]);

  const cancelAutoRetry = () => {
    setIsAutoRetrying(false);
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold mb-4">Connection Issue</h2>

      {isAutoRetrying ? (
        <div>
          <p className="text-gray-600 mb-2">
            Retrying automatically... (attempt {retryCount + 1}/{maxAutoRetries})
          </p>
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full" />
            <span className="text-sm text-gray-500">
              Next retry in {countdown}s
            </span>
          </div>
          <button
            onClick={cancelAutoRetry}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Stop auto-retry
          </button>
        </div>
      ) : (
        <div>
          <p className="text-gray-600 mb-4">
            {retryCount >= maxAutoRetries
              ? `Failed after ${maxAutoRetries} automatic retries.`
              : error.message}
          </p>
          <button
            onClick={retry}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again Manually
          </button>
        </div>
      )}
    </div>
  );
}
```

```
Auto-retry flow:
Error occurs → Attempt 1 (wait 1s) → Error → Attempt 2 (wait 2s) → Error → Attempt 3 (wait 4s) → Error → Show manual retry UI

Exponential backoff: 1s → 2s → 4s → 8s → 16s (capped)
```

---

## Q12. (Intermediate) How do you handle streaming errors when using React Server Components with Suspense?

**Scenario**: Your page has three Suspense boundaries. The first two resolve successfully and stream to the client. The third one fails during rendering on the server. What happens to the HTML already sent?

**Answer**:

When a Server Component fails inside a `<Suspense>` boundary during streaming, Next.js handles it gracefully — the error is **contained** to that Suspense boundary while already-streamed content remains intact.

```
Streaming with partial error:

Server starts streaming HTML:
┌────────────────────────────────────┐
│ <html>                             │
│   <body>                           │
│     <Header /> (rendered)          │──▶ Sent to client ✅
│     <Suspense fallback={Skel1}>   │
│       <Stats /> (resolved)         │──▶ Sent to client ✅
│     </Suspense>                    │
│     <Suspense fallback={Skel2}>   │
│       <Chart /> (resolved)         │──▶ Sent to client ✅
│     </Suspense>                    │
│     <Suspense fallback={Skel3}>   │
│       <Recs /> ← throws error!    │──▶ Error boundary HTML sent ❌
│     </Suspense>                    │
│   </body>                          │
│ </html>                            │
└────────────────────────────────────┘

Client receives:
✅ Header — fully rendered
✅ Stats — fully rendered
✅ Chart — fully rendered
❌ Recs — error boundary UI shown
```

**Implementation with error containment**:

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react';
import { ErrorBoundary } from '@/components/error-boundary-wrapper';

export default function DashboardPage() {
  return (
    <div className="space-y-6 p-6">
      {/* Each section is independently error-isolated */}
      <ErrorBoundary fallbackRender={({ resetError }) => (
        <div className="p-4 border border-amber-200 bg-amber-50 rounded-lg">
          <p className="text-amber-800">Stats temporarily unavailable</p>
          <button onClick={resetError} className="text-sm text-amber-600 underline mt-2">
            Retry
          </button>
        </div>
      )}>
        <Suspense fallback={<div className="h-28 bg-gray-100 animate-pulse rounded-xl" />}>
          <StatsSection />
        </Suspense>
      </ErrorBoundary>

      <ErrorBoundary fallbackRender={({ resetError }) => (
        <div className="p-4 border border-amber-200 bg-amber-50 rounded-lg">
          <p className="text-amber-800">Chart could not be loaded</p>
          <button onClick={resetError} className="text-sm text-amber-600 underline mt-2">
            Retry
          </button>
        </div>
      )}>
        <Suspense fallback={<div className="h-64 bg-gray-100 animate-pulse rounded-xl" />}>
          <ChartSection />
        </Suspense>
      </ErrorBoundary>

      <ErrorBoundary fallbackRender={({ resetError }) => (
        <div className="p-4 border border-amber-200 bg-amber-50 rounded-lg">
          <p className="text-amber-800">Recommendations unavailable</p>
          <button onClick={resetError} className="text-sm text-amber-600 underline mt-2">
            Retry
          </button>
        </div>
      )}>
        <Suspense fallback={<div className="h-40 bg-gray-100 animate-pulse rounded-xl" />}>
          <RecommendationsSection />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
```

**Custom ErrorBoundary wrapper for inline use**:

```tsx
// components/error-boundary-wrapper.tsx
'use client';

import React, { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackRender: (props: { error: Error; resetError: () => void }) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      return this.props.fallbackRender({
        error: this.state.error,
        resetError: this.resetError,
      });
    }

    return this.props.children;
  }
}
```

**Key insight**: During streaming SSR, if an error occurs in a Suspense boundary:
1. The fallback (skeleton) was already sent to the client
2. Next.js sends the error boundary's HTML as the "resolution" of that Suspense boundary
3. The error boundary UI replaces the skeleton
4. Already-streamed content above is NOT affected
5. The client can hydrate and the error boundary becomes interactive (retry works)

---

## Q13. (Advanced) How do you build a production-grade error monitoring and reporting system integrated with Next.js error boundaries?

**Scenario**: You're building a monitoring system that captures all types of errors (server, client, edge, streaming) with full context, deduplication, and alerting. You need to correlate errors with user sessions and deployment versions.

**Answer**:

A production error monitoring system needs five layers: capture, enrichment, transport, storage, and alerting.

```
Production Error Monitoring Architecture:
┌────────────────────────────────────────────────────────────────┐
│                    Error Capture Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Server RSC    │  │ Client CSR   │  │ Edge Middleware      │ │
│  │ errors        │  │ errors       │  │ errors               │ │
│  │               │  │              │  │                      │ │
│  │ instrumentation│  │ error.tsx    │  │ try/catch in        │ │
│  │ .ts hook      │  │ boundaries   │  │ middleware.ts        │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘ │
│         │                 │                      │             │
│         ▼                 ▼                      ▼             │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              Error Enrichment Layer                   │      │
│  │  • Stack trace (with source maps)                    │      │
│  │  • User session / ID                                 │      │
│  │  • Request context (URL, method, headers)            │      │
│  │  • Build version / commit SHA                        │      │
│  │  • Route path and segment config                     │      │
│  │  • Error fingerprint (deduplication)                  │      │
│  └──────────────────────┬──────────────────────────────┘      │
│                          │                                     │
│                          ▼                                     │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              Transport Layer                          │      │
│  │  • Batched HTTP POST to /api/errors                  │      │
│  │  • navigator.sendBeacon for page unload              │      │
│  │  • Rate limiting (max 10 errors/minute/user)         │      │
│  └──────────────────────┬──────────────────────────────┘      │
│                          │                                     │
│                          ▼                                     │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              Storage & Alerting                       │      │
│  │  • Database (Postgres/ClickHouse)                    │      │
│  │  • Slack/PagerDuty alerts for spike detection        │      │
│  │  • Dashboard for error trends                        │      │
│  └─────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────┘
```

**Layer 1: Error capture with instrumentation**:

```ts
// instrumentation.ts
import { type Instrumentation } from 'next';

export const onRequestError: Instrumentation.onRequestError = async (
  error,
  request,
  context
) => {
  // Create enriched error payload
  const errorPayload = {
    // Error details
    message: error.message,
    stack: error.stack,
    digest: error.digest,
    name: error.name,

    // Request context
    path: request.path,
    method: request.method,
    userAgent: request.headers['user-agent'],
    referer: request.headers['referer'],

    // Next.js context
    routerKind: context.routerKind,
    routePath: context.routePath,
    routeType: context.routeType,
    renderSource: context.renderSource,

    // Build context
    buildId: process.env.NEXT_BUILD_ID || 'dev',
    commitSha: process.env.VERCEL_GIT_COMMIT_SHA || 'unknown',
    nodeEnv: process.env.NODE_ENV,

    // Fingerprint for deduplication
    fingerprint: generateFingerprint(error),

    timestamp: new Date().toISOString(),
    runtime: process.env.NEXT_RUNTIME, // 'nodejs' or 'edge'
  };

  // Send to monitoring endpoint
  try {
    await fetch(process.env.ERROR_MONITORING_URL || 'http://localhost:3000/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorPayload),
    });
  } catch {
    // Don't let monitoring errors affect the user
    console.error('[Monitoring] Failed to report error:', error.message);
  }
};

function generateFingerprint(error: Error & { digest?: string }): string {
  // Create a consistent fingerprint for deduplication
  const parts = [
    error.name,
    error.message.replace(/\b[0-9a-f]{8,}\b/g, '<hash>'), // normalize hashes
    error.stack?.split('\n')[1]?.trim() || '', // first stack frame
  ];
  return hashString(parts.join('|'));
}

function hashString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}
```

**Layer 2: Client-side error capture**:

```tsx
// lib/client-error-reporter.ts
'use client';

interface ClientErrorPayload {
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  userAgent: string;
  timestamp: string;
  type: 'error-boundary' | 'unhandled-rejection' | 'unhandled-error';
  buildId?: string;
  sessionId: string;
}

class ErrorReporter {
  private queue: ClientErrorPayload[] = [];
  private flushTimeout: NodeJS.Timeout | null = null;
  private errorCounts = new Map<string, number>();
  private readonly MAX_ERRORS_PER_MINUTE = 10;
  private sessionId: string;

  constructor() {
    this.sessionId = this.getSessionId();
    this.setupGlobalHandlers();
  }

  private getSessionId(): string {
    if (typeof window === 'undefined') return 'server';
    let id = sessionStorage.getItem('error_session_id');
    if (!id) {
      id = Math.random().toString(36).substring(2);
      sessionStorage.setItem('error_session_id', id);
    }
    return id;
  }

  private setupGlobalHandlers() {
    if (typeof window === 'undefined') return;

    // Catch unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.report({
        message: event.reason?.message || String(event.reason),
        stack: event.reason?.stack,
        type: 'unhandled-rejection',
      });
    });

    // Catch unhandled errors
    window.addEventListener('error', (event) => {
      this.report({
        message: event.message,
        stack: event.error?.stack,
        type: 'unhandled-error',
      });
    });
  }

  report(params: {
    message: string;
    stack?: string;
    componentStack?: string;
    type: ClientErrorPayload['type'];
  }) {
    // Rate limiting
    const fingerprint = params.message.substring(0, 100);
    const count = this.errorCounts.get(fingerprint) || 0;
    if (count >= this.MAX_ERRORS_PER_MINUTE) return;
    this.errorCounts.set(fingerprint, count + 1);

    // Reset counts every minute
    setTimeout(() => this.errorCounts.delete(fingerprint), 60000);

    const payload: ClientErrorPayload = {
      ...params,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      buildId: (window as any).__NEXT_DATA__?.buildId,
      sessionId: this.sessionId,
    };

    this.queue.push(payload);
    this.scheduleFlush();
  }

  private scheduleFlush() {
    if (this.flushTimeout) return;
    this.flushTimeout = setTimeout(() => this.flush(), 1000);
  }

  private async flush() {
    this.flushTimeout = null;
    if (this.queue.length === 0) return;

    const errors = [...this.queue];
    this.queue = [];

    try {
      // Use sendBeacon for reliability (survives page unload)
      const blob = new Blob([JSON.stringify(errors)], { type: 'application/json' });
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/errors/client', blob);
      } else {
        await fetch('/api/errors/client', {
          method: 'POST',
          body: blob,
          keepalive: true,
        });
      }
    } catch {
      // Re-queue on failure
      this.queue.unshift(...errors);
    }
  }
}

export const errorReporter = typeof window !== 'undefined'
  ? new ErrorReporter()
  : null;
```

**Layer 3: Error API route handler**:

```tsx
// app/api/errors/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const error = await request.json();

  // Store in database
  // await db.errorLog.create({ data: error });

  // Check for error spike (alerting)
  const recentCount = await getRecentErrorCount(error.fingerprint, 5); // last 5 mins
  if (recentCount > 50) {
    await sendSlackAlert({
      text: `Error spike detected: "${error.message}" (${recentCount} occurrences in 5 minutes)`,
      route: error.routePath,
      digest: error.digest,
    });
  }

  return NextResponse.json({ received: true });
}

async function getRecentErrorCount(fingerprint: string, minutes: number): Promise<number> {
  // Query your error store
  return 0; // placeholder
}

async function sendSlackAlert(payload: { text: string; route: string; digest: string }) {
  if (!process.env.SLACK_WEBHOOK_URL) return;

  await fetch(process.env.SLACK_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: payload.text,
      blocks: [
        {
          type: 'section',
          text: { type: 'mrkdwn', text: `*Error Spike Alert*\n${payload.text}` },
        },
        {
          type: 'context',
          elements: [
            { type: 'mrkdwn', text: `*Route:* ${payload.route}` },
            { type: 'mrkdwn', text: `*Digest:* \`${payload.digest}\`` },
          ],
        },
      ],
    }),
  });
}
```

This system provides comprehensive error monitoring across all Next.js rendering modes while respecting rate limits and deduplication.

---

## Q14. (Advanced) How do you implement graceful degradation patterns where parts of the page fail but the rest works?

**Scenario**: Your e-commerce product page has: product details (critical), reviews (important), recommendations (nice-to-have), and recently viewed (nice-to-have). If reviews or recommendations fail, the page should still work. Only product details failure should show an error.

**Answer**:

Graceful degradation uses a priority-based error handling strategy where each section defines its own failure behavior.

```
Degradation Priority Matrix:
┌───────────────────┬──────────┬───────────────────────────────┐
│  Section           │ Priority │ On Failure                    │
├───────────────────┼──────────┼───────────────────────────────┤
│  Product Details   │ Critical │ Show error page (error.tsx)   │
│  Price & Buy       │ Critical │ Show error page (error.tsx)   │
│  Reviews           │ High     │ Show "Reviews unavailable"    │
│  Recommendations   │ Medium   │ Show nothing (hide section)   │
│  Recently Viewed   │ Low      │ Show nothing (hide section)   │
└───────────────────┴──────────┴───────────────────────────────┘
```

```tsx
// components/graceful-section.tsx
'use client';

import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  priority: 'critical' | 'high' | 'medium' | 'low';
  fallback?: ReactNode;
  name: string;
  onError?: (error: Error, section: string) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class GracefulSection extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    this.props.onError?.(error, this.props.name);
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    const { priority, fallback, name } = this.props;

    // Critical sections should bubble up to error.tsx
    if (priority === 'critical') {
      throw this.state.error;
    }

    // High priority shows a visible fallback
    if (priority === 'high') {
      return (
        fallback || (
          <div className="border border-amber-200 bg-amber-50 rounded-lg p-4">
            <p className="text-amber-800 font-medium">
              {name} temporarily unavailable
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="text-sm text-amber-600 hover:underline mt-2"
            >
              Try again
            </button>
          </div>
        )
      );
    }

    // Medium/Low priority — hide completely
    return null;
  }
}
```

```tsx
// app/products/[id]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { GracefulSection } from '@/components/graceful-section';

async function getProduct(id: string) {
  const res = await fetch(`https://api.example.com/products/${id}`, {
    next: { revalidate: 60 },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Product API error: ${res.status}`);
  return res.json();
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);

  if (!product) notFound();

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* CRITICAL — Product details must render, errors bubble to error.tsx */}
      <section className="grid grid-cols-2 gap-8">
        <div className="aspect-square relative">
          {/* product image */}
        </div>
        <div>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-2xl text-green-600 mt-2">${product.price}</p>
          <p className="mt-4 text-gray-700">{product.description}</p>
          <button className="mt-6 px-8 py-3 bg-blue-600 text-white rounded-lg">
            Add to Cart
          </button>
        </div>
      </section>

      {/* HIGH — Reviews show fallback on error */}
      <GracefulSection name="Reviews" priority="high">
        <Suspense fallback={<ReviewsSkeleton />}>
          <ReviewsSection productId={id} />
        </Suspense>
      </GracefulSection>

      {/* MEDIUM — Recommendations hidden on error */}
      <GracefulSection name="Recommendations" priority="medium">
        <Suspense fallback={<RecommendationsSkeleton />}>
          <RecommendationsSection productId={id} />
        </Suspense>
      </GracefulSection>

      {/* LOW — Recently viewed hidden on error */}
      <GracefulSection name="Recently Viewed" priority="low">
        <Suspense fallback={null}>
          <RecentlyViewedSection />
        </Suspense>
      </GracefulSection>
    </div>
  );
}

// Individual async sections
async function ReviewsSection({ productId }: { productId: string }) {
  const reviews = await fetch(`https://api.example.com/products/${productId}/reviews`, {
    next: { revalidate: 300 },
  }).then((r) => {
    if (!r.ok) throw new Error('Reviews unavailable');
    return r.json();
  });

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Customer Reviews ({reviews.length})</h2>
      {reviews.map((review: any) => (
        <div key={review.id} className="border-b py-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium">{review.author}</span>
            <span className="text-yellow-500">{'★'.repeat(review.rating)}</span>
          </div>
          <p className="text-gray-700">{review.text}</p>
        </div>
      ))}
    </div>
  );
}

async function RecommendationsSection({ productId }: { productId: string }) {
  const recs = await fetch(`https://ml.example.com/recommendations/${productId}`, {
    next: { revalidate: 3600 },
  }).then((r) => {
    if (!r.ok) throw new Error('Recommendations unavailable');
    return r.json();
  });

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">You Might Also Like</h2>
      <div className="grid grid-cols-4 gap-4">
        {recs.map((rec: any) => (
          <a key={rec.id} href={`/products/${rec.id}`} className="border rounded-lg p-3">
            <p className="font-medium">{rec.name}</p>
            <p className="text-green-600">${rec.price}</p>
          </a>
        ))}
      </div>
    </div>
  );
}

async function RecentlyViewedSection() {
  // This reads from cookies/localStorage — may fail
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Recently Viewed</h2>
      {/* ... */}
    </div>
  );
}

function ReviewsSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-6 w-48 bg-gray-200 rounded" />
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="space-y-2 py-4 border-b">
          <div className="h-4 w-32 bg-gray-200 rounded" />
          <div className="h-4 w-full bg-gray-100 rounded" />
        </div>
      ))}
    </div>
  );
}

function RecommendationsSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-6 w-56 bg-gray-200 rounded mb-4" />
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-32 bg-gray-200 rounded-lg" />
        ))}
      </div>
    </div>
  );
}
```

This pattern ensures the product page always shows the essential content. Non-critical sections degrade gracefully — either showing a helpful message (high priority) or silently disappearing (medium/low priority) — without affecting the user's ability to view and purchase the product.

---

## Q15. (Advanced) How do you handle errors in Server Actions and display them in the UI?

**Scenario**: Your checkout form uses Server Actions for payment processing. You need to handle validation errors, payment failures, network issues, and display appropriate messages — all without losing form state.

**Answer**:

Server Actions can throw errors that are caught by error boundaries, or return structured error responses that the client handles directly. For forms, the structured response pattern is preferred.

```tsx
// lib/action-result.ts
// Type-safe action result pattern
export type ActionResult<T = void> =
  | { success: true; data: T }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };
```

```tsx
// app/checkout/actions.ts
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import type { ActionResult } from '@/lib/action-result';

const checkoutSchema = z.object({
  email: z.string().email('Valid email required'),
  cardNumber: z.string().regex(/^\d{16}$/, 'Card number must be 16 digits'),
  expiry: z.string().regex(/^\d{2}\/\d{2}$/, 'Format: MM/YY'),
  cvv: z.string().regex(/^\d{3,4}$/, 'CVV must be 3-4 digits'),
  name: z.string().min(2, 'Name required'),
});

export async function processCheckout(
  prevState: ActionResult<{ orderId: string }> | null,
  formData: FormData
): Promise<ActionResult<{ orderId: string }>> {
  // Step 1: Validate input
  const raw = Object.fromEntries(formData);
  const parsed = checkoutSchema.safeParse(raw);

  if (!parsed.success) {
    const fieldErrors: Record<string, string[]> = {};
    for (const [key, value] of Object.entries(parsed.error.flatten().fieldErrors)) {
      if (value) fieldErrors[key] = value;
    }
    return {
      success: false,
      error: 'Please fix the errors below',
      fieldErrors,
    };
  }

  // Step 2: Process payment
  try {
    const paymentResult = await fetch('https://payment.example.com/charge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: parsed.data.email,
        card: parsed.data.cardNumber,
        expiry: parsed.data.expiry,
        cvv: parsed.data.cvv,
        name: parsed.data.name,
      }),
    });

    if (!paymentResult.ok) {
      const errorBody = await paymentResult.json().catch(() => ({}));

      if (paymentResult.status === 402) {
        return {
          success: false,
          error: errorBody.message || 'Payment declined. Please check your card details.',
        };
      }

      if (paymentResult.status === 429) {
        return {
          success: false,
          error: 'Too many attempts. Please wait a moment and try again.',
        };
      }

      return {
        success: false,
        error: 'Payment processing failed. Please try again.',
      };
    }

    const order = await paymentResult.json();

    // Step 3: Revalidate cache
    revalidatePath('/orders');

    return {
      success: true,
      data: { orderId: order.id },
    };
  } catch (error) {
    console.error('Checkout error:', error);
    return {
      success: false,
      error: 'A network error occurred. Please check your connection and try again.',
    };
  }
}
```

```tsx
// app/checkout/checkout-form.tsx
'use client';

import { useActionState } from 'react';
import { useRouter } from 'next/navigation';
import { useEffect, useRef } from 'react';
import { processCheckout } from './actions';
import type { ActionResult } from '@/lib/action-result';

export function CheckoutForm() {
  const [state, formAction, isPending] = useActionState(processCheckout, null);
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);

  // Redirect on success
  useEffect(() => {
    if (state?.success) {
      router.push(`/orders/${state.data.orderId}/confirmation`);
    }
  }, [state, router]);

  return (
    <form ref={formRef} action={formAction} className="max-w-md mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Checkout</h2>

      {/* Global error message */}
      {state && !state.success && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg" role="alert">
          <p className="text-red-800 font-medium">{state.error}</p>
        </div>
      )}

      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium mb-1">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          className={`w-full border rounded-lg px-3 py-2 ${
            state && !state.success && state.fieldErrors?.email
              ? 'border-red-500'
              : 'border-gray-300'
          }`}
        />
        {state && !state.success && state.fieldErrors?.email && (
          <p className="text-sm text-red-600 mt-1">{state.fieldErrors.email[0]}</p>
        )}
      </div>

      {/* Card Number */}
      <div>
        <label htmlFor="cardNumber" className="block text-sm font-medium mb-1">
          Card Number
        </label>
        <input
          id="cardNumber"
          name="cardNumber"
          type="text"
          required
          maxLength={16}
          placeholder="1234567890123456"
          className={`w-full border rounded-lg px-3 py-2 ${
            state && !state.success && state.fieldErrors?.cardNumber
              ? 'border-red-500'
              : 'border-gray-300'
          }`}
        />
        {state && !state.success && state.fieldErrors?.cardNumber && (
          <p className="text-sm text-red-600 mt-1">{state.fieldErrors.cardNumber[0]}</p>
        )}
      </div>

      {/* Expiry and CVV */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="expiry" className="block text-sm font-medium mb-1">
            Expiry
          </label>
          <input
            id="expiry"
            name="expiry"
            type="text"
            required
            placeholder="MM/YY"
            maxLength={5}
            className={`w-full border rounded-lg px-3 py-2 ${
              state && !state.success && state.fieldErrors?.expiry
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          />
          {state && !state.success && state.fieldErrors?.expiry && (
            <p className="text-sm text-red-600 mt-1">{state.fieldErrors.expiry[0]}</p>
          )}
        </div>
        <div>
          <label htmlFor="cvv" className="block text-sm font-medium mb-1">
            CVV
          </label>
          <input
            id="cvv"
            name="cvv"
            type="text"
            required
            maxLength={4}
            placeholder="123"
            className={`w-full border rounded-lg px-3 py-2 ${
              state && !state.success && state.fieldErrors?.cvv
                ? 'border-red-500'
                : 'border-gray-300'
            }`}
          />
          {state && !state.success && state.fieldErrors?.cvv && (
            <p className="text-sm text-red-600 mt-1">{state.fieldErrors.cvv[0]}</p>
          )}
        </div>
      </div>

      {/* Cardholder Name */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">
          Cardholder Name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          required
          className={`w-full border rounded-lg px-3 py-2 ${
            state && !state.success && state.fieldErrors?.name
              ? 'border-red-500'
              : 'border-gray-300'
          }`}
        />
        {state && !state.success && state.fieldErrors?.name && (
          <p className="text-sm text-red-600 mt-1">{state.fieldErrors.name[0]}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isPending}
        className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {isPending ? (
          <>
            <span className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
            Processing...
          </>
        ) : (
          'Pay Now'
        )}
      </button>
    </form>
  );
}
```

**Key benefits of the structured result pattern over throwing errors**:
1. Form state is preserved (inputs aren't cleared)
2. Field-level error messages are possible
3. No full-page error boundary activation
4. Graceful handling of expected errors (validation, payment decline)
5. `isPending` state provides loading feedback

---

## Q16. (Advanced) How do you implement error recovery patterns for data mutations with optimistic updates?

**Scenario**: Your task management app uses optimistic updates — when a user marks a task as complete, it instantly updates the UI, then syncs with the server. If the server request fails, you need to roll back the optimistic update and show an error.

**Answer**:

Optimistic updates with error recovery require careful state management to track the "optimistic" state separately from the "confirmed" state.

```tsx
// lib/use-optimistic-mutation.ts
'use client';

import { useCallback, useRef, useState, useTransition } from 'react';

interface OptimisticMutationConfig<TData, TVariables> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  onMutate?: (variables: TVariables) => TData | void;  // optimistic update
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables, rollbackData: TData | void) => void;
  onSettled?: () => void;
}

export function useOptimisticMutation<TData, TVariables>(
  config: OptimisticMutationConfig<TData, TVariables>
) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<Error | null>(null);
  const rollbackRef = useRef<TData | void>();

  const mutate = useCallback(
    (variables: TVariables) => {
      setError(null);

      // Apply optimistic update immediately
      rollbackRef.current = config.onMutate?.(variables);

      startTransition(async () => {
        try {
          const result = await config.mutationFn(variables);
          config.onSuccess?.(result, variables);
        } catch (err) {
          const error = err instanceof Error ? err : new Error(String(err));
          setError(error);

          // Rollback optimistic update
          config.onError?.(error, variables, rollbackRef.current);
        } finally {
          config.onSettled?.();
        }
      });
    },
    [config]
  );

  return { mutate, isPending, error };
}
```

```tsx
// app/tasks/actions.ts
'use server';

import { revalidateTag } from 'next/cache';

export async function toggleTaskComplete(taskId: string, completed: boolean) {
  const res = await fetch(`https://api.example.com/tasks/${taskId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed }),
  });

  if (!res.ok) {
    throw new Error(`Failed to update task: ${res.status}`);
  }

  revalidateTag('tasks');
  return res.json();
}

export async function deleteTask(taskId: string) {
  const res = await fetch(`https://api.example.com/tasks/${taskId}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    throw new Error(`Failed to delete task: ${res.status}`);
  }

  revalidateTag('tasks');
}
```

```tsx
// app/tasks/task-list.tsx
'use client';

import { useOptimistic, useCallback, useState } from 'react';
import { toggleTaskComplete, deleteTask } from './actions';

interface Task {
  id: string;
  title: string;
  completed: boolean;
}

type OptimisticAction =
  | { type: 'toggle'; taskId: string }
  | { type: 'delete'; taskId: string };

export function TaskList({ initialTasks }: { initialTasks: Task[] }) {
  const [error, setError] = useState<string | null>(null);

  // useOptimistic for instant UI updates
  const [optimisticTasks, addOptimistic] = useOptimistic(
    initialTasks,
    (state: Task[], action: OptimisticAction) => {
      switch (action.type) {
        case 'toggle':
          return state.map((task) =>
            task.id === action.taskId
              ? { ...task, completed: !task.completed }
              : task
          );
        case 'delete':
          return state.filter((task) => task.id !== action.taskId);
        default:
          return state;
      }
    }
  );

  const handleToggle = useCallback(
    async (task: Task) => {
      setError(null);

      // Optimistic update
      addOptimistic({ type: 'toggle', taskId: task.id });

      try {
        await toggleTaskComplete(task.id, !task.completed);
      } catch (err) {
        // On error, React will revert the optimistic state
        // because the transition failed
        setError(`Failed to update "${task.title}". Please try again.`);
      }
    },
    [addOptimistic]
  );

  const handleDelete = useCallback(
    async (task: Task) => {
      setError(null);

      // Optimistic delete
      addOptimistic({ type: 'delete', taskId: task.id });

      try {
        await deleteTask(task.id);
      } catch (err) {
        setError(`Failed to delete "${task.title}". Please try again.`);
      }
    },
    [addOptimistic]
  );

  return (
    <div>
      {/* Error toast */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <p className="text-red-800 text-sm">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800 text-sm"
          >
            Dismiss
          </button>
        </div>
      )}

      <ul className="space-y-2">
        {optimisticTasks.map((task) => (
          <li
            key={task.id}
            className="flex items-center gap-3 p-3 border rounded-lg group"
          >
            <button
              onClick={() => handleToggle(task)}
              className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                task.completed
                  ? 'bg-green-500 border-green-500 text-white'
                  : 'border-gray-300 hover:border-green-400'
              }`}
            >
              {task.completed && '✓'}
            </button>

            <span
              className={`flex-1 ${
                task.completed ? 'line-through text-gray-400' : 'text-gray-900'
              }`}
            >
              {task.title}
            </span>

            <button
              onClick={() => handleDelete(task)}
              className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Optimistic update flow**:

```
User clicks "Complete"
         │
         ├──▶ UI instantly updates (optimistic) ──▶ User sees ✓
         │
         └──▶ Server Action fires (async)
                    │
                    ├──▶ Success → State confirmed, done ✅
                    │
                    └──▶ Failure → React reverts optimistic state
                                   Error toast shown
                                   UI returns to original state ↩️
```

---

## Q17. (Advanced) How do you implement error boundaries that work correctly with React Server Components streaming and partial hydration?

**Scenario**: Your app streams a complex page with interleaved Server and Client Components. Some Client Components fail during hydration while Server Components rendered successfully. How do you handle this gracefully?

**Answer**:

Hydration errors are a special class of errors that occur when the server-rendered HTML doesn't match what the client tries to render. Next.js 15+ has improved hydration error handling, but you need proper strategies for production.

```
Streaming + Hydration Error Scenarios:
┌──────────────────────────────────────────────────────┐
│ Server Stream                                         │
│                                                       │
│ ┌─────────────┐  ← Sent first, renders fine           │
│ │ Header (SC)  │                                      │
│ └─────────────┘                                       │
│ ┌─────────────┐  ← Streamed, renders fine             │
│ │ Content (SC) │                                      │
│ └─────────────┘                                       │
│ ┌─────────────┐  ← Client Component — hydration error!│
│ │ Widget (CC)  │  ← Server HTML ≠ Client render       │
│ └─────────────┘                                       │
│ ┌─────────────┐  ← Streamed, renders fine             │
│ │ Footer (SC)  │                                      │
│ └─────────────┘                                       │
└──────────────────────────────────────────────────────┘
```

**Hydration-safe Client Component wrapper**:

```tsx
// components/hydration-safe.tsx
'use client';

import { Component, type ReactNode, Suspense } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error) => void;
}

interface State {
  hasError: boolean;
  isHydrationError: boolean;
}

export class HydrationSafe extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, isHydrationError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    const isHydrationError =
      error.message.includes('Hydration') ||
      error.message.includes('hydrat') ||
      error.message.includes('server-rendered') ||
      error.message.includes('did not match');

    return { hasError: true, isHydrationError };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.props.onError?.(error);

    if (this.state.isHydrationError) {
      console.warn(
        '[HydrationSafe] Hydration mismatch detected, re-rendering client-only:',
        error.message
      );
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.state.isHydrationError) {
        // For hydration errors, try rendering client-only
        return (
          <Suspense fallback={this.props.fallback || null}>
            <ClientOnly>{this.props.children}</ClientOnly>
          </Suspense>
        );
      }

      return this.props.fallback || null;
    }

    return this.props.children;
  }
}

// Forces client-only rendering (skips hydration)
function ClientOnly({ children }: { children: ReactNode }) {
  // This component only renders on the client
  // by leveraging the fact that it's inside a Suspense
  // that was resolved on error recovery
  return <>{children}</>;
}
```

**Preventing common hydration errors**:

```tsx
// components/client-date.tsx
'use client';

import { useState, useEffect } from 'react';

// ❌ BAD — Causes hydration mismatch (server time ≠ client time)
function BadDate() {
  return <span>{new Date().toLocaleString()}</span>;
}

// ✅ GOOD — Renders nothing on server, date on client
export function ClientDate({ date }: { date: string | Date }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    // Return same content as server to avoid hydration mismatch
    return <span suppressHydrationWarning>{new Date(date).toISOString().split('T')[0]}</span>;
  }

  return <span>{new Date(date).toLocaleDateString()}</span>;
}
```

**Error boundary for streaming chunks**:

```tsx
// app/feed/page.tsx
import { Suspense } from 'react';

// Each item streams independently with its own error boundary
export default function FeedPage() {
  return (
    <div className="space-y-4 max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold">Activity Feed</h1>

      {/* Each feed section streams independently */}
      {['trending', 'following', 'suggested'].map((section) => (
        <Suspense
          key={section}
          fallback={
            <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
          }
        >
          <FeedSection type={section} />
        </Suspense>
      ))}
    </div>
  );
}

// Each section is an async Server Component that might fail
async function FeedSection({ type }: { type: string }) {
  try {
    const data = await fetch(`https://api.example.com/feed/${type}`, {
      next: { revalidate: 60 },
    });

    if (!data.ok) throw new Error(`Feed ${type} unavailable`);

    const items = await data.json();

    return (
      <section className="border rounded-xl p-4">
        <h2 className="font-semibold capitalize mb-3">{type}</h2>
        {items.map((item: any) => (
          <div key={item.id} className="py-2 border-b last:border-0">
            {item.content}
          </div>
        ))}
      </section>
    );
  } catch (error) {
    // Return inline error UI instead of throwing
    // This prevents the error from bubbling to the error boundary
    return (
      <section className="border border-amber-200 bg-amber-50 rounded-xl p-4">
        <h2 className="font-semibold capitalize mb-1">{type}</h2>
        <p className="text-sm text-amber-700">This section is temporarily unavailable.</p>
      </section>
    );
  }
}
```

The key insight for streaming + hydration: handle errors **at the component level** (try/catch in Server Components) when you want graceful inline degradation, and use `error.tsx` boundaries when you want page-level error recovery.

---

## Q18. (Advanced) How do you implement a toast notification system for error feedback across the entire application?

**Scenario**: Errors can occur anywhere in your app — Server Actions, client-side operations, API calls, form submissions. You need a centralized toast notification system that any component can use to display errors, warnings, and success messages.

**Answer**:

A production toast system requires a global state manager, portal-based rendering, and integration with both Server Actions and client-side error handlers.

```tsx
// lib/toast-context.tsx
'use client';

import {
  createContext,
  useContext,
  useCallback,
  useState,
  useRef,
  useEffect,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible: boolean;
}

interface ToastContextType {
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  success: (title: string, message?: string) => string;
  error: (title: string, message?: string) => string;
  warning: (title: string, message?: string) => string;
  info: (title: string, message?: string) => string;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [mounted, setMounted] = useState(false);
  const timers = useRef<Map<string, NodeJS.Timeout>>(new Map());

  useEffect(() => {
    setMounted(true);
    return () => {
      timers.current.forEach((timer) => clearTimeout(timer));
    };
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const addToast = useCallback(
    (toast: Omit<Toast, 'id'>) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const newToast = { ...toast, id };

      setToasts((prev) => {
        // Max 5 toasts visible
        const updated = [...prev, newToast];
        if (updated.length > 5) {
          const removed = updated.shift();
          if (removed) {
            const timer = timers.current.get(removed.id);
            if (timer) clearTimeout(timer);
            timers.current.delete(removed.id);
          }
        }
        return updated;
      });

      // Auto dismiss
      if (toast.duration > 0) {
        const timer = setTimeout(() => removeToast(id), toast.duration);
        timers.current.set(id, timer);
      }

      return id;
    },
    [removeToast]
  );

  const success = useCallback(
    (title: string, message?: string) =>
      addToast({ type: 'success', title, message, duration: 4000, dismissible: true }),
    [addToast]
  );

  const error = useCallback(
    (title: string, message?: string) =>
      addToast({ type: 'error', title, message, duration: 8000, dismissible: true }),
    [addToast]
  );

  const warning = useCallback(
    (title: string, message?: string) =>
      addToast({ type: 'warning', title, message, duration: 6000, dismissible: true }),
    [addToast]
  );

  const info = useCallback(
    (title: string, message?: string) =>
      addToast({ type: 'info', title, message, duration: 5000, dismissible: true }),
    [addToast]
  );

  return (
    <ToastContext.Provider value={{ addToast, removeToast, success, error, warning, info }}>
      {children}
      {mounted &&
        createPortal(
          <ToastContainer toasts={toasts} onRemove={removeToast} />,
          document.body
        )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}

// Toast container with animations
function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: Toast[];
  onRemove: (id: string) => void;
}) {
  const typeStyles: Record<ToastType, string> = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  const typeIcons: Record<ToastType, string> = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
  };

  return (
    <div
      className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 w-96"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`
            border rounded-lg p-4 shadow-lg
            animate-in slide-in-from-right duration-300
            ${typeStyles[toast.type]}
          `}
          role="alert"
        >
          <div className="flex items-start gap-3">
            <span className="text-lg font-bold flex-shrink-0">
              {typeIcons[toast.type]}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-medium">{toast.title}</p>
              {toast.message && (
                <p className="text-sm mt-1 opacity-80">{toast.message}</p>
              )}
              {toast.action && (
                <button
                  onClick={toast.action.onClick}
                  className="text-sm font-medium underline mt-2"
                >
                  {toast.action.label}
                </button>
              )}
            </div>
            {toast.dismissible && (
              <button
                onClick={() => onRemove(toast.id)}
                className="flex-shrink-0 opacity-60 hover:opacity-100"
                aria-label="Dismiss"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Integration with error boundaries**:

```tsx
// app/error.tsx
'use client';

import { useEffect } from 'react';
import { useToast } from '@/lib/toast-context';

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const toast = useToast();

  useEffect(() => {
    toast.error('Page Error', error.message);
  }, [error, toast]);

  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold mb-4">Something went wrong</h2>
      <button onClick={reset} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
        Try Again
      </button>
    </div>
  );
}
```

**Integration with Server Actions**:

```tsx
// components/task-actions.tsx
'use client';

import { useToast } from '@/lib/toast-context';
import { deleteTask } from '@/app/tasks/actions';

export function DeleteTaskButton({ taskId, taskName }: { taskId: string; taskName: string }) {
  const toast = useToast();

  async function handleDelete() {
    try {
      await deleteTask(taskId);
      toast.success('Task deleted', `"${taskName}" has been removed.`);
    } catch (error) {
      toast.error(
        'Delete failed',
        `Could not delete "${taskName}". Please try again.`
      );
    }
  }

  return (
    <button
      onClick={handleDelete}
      className="text-red-600 hover:text-red-800"
    >
      Delete
    </button>
  );
}
```

---

## Q19. (Advanced) How do you implement error handling for Edge Runtime and Middleware in Next.js?

**Scenario**: Your middleware handles authentication, geolocation-based redirects, and A/B testing. If the auth service is down, the middleware shouldn't crash — it should degrade gracefully.

**Answer**:

Middleware runs at the Edge and has different error handling constraints than Node.js server components. There's no `error.tsx` for middleware — you must use try/catch and design for resilience.

```
Middleware Error Handling Strategy:
┌──────────────────────────────────────────────────────────────┐
│  Request arrives                                              │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Middleware (Edge Runtime)                             │    │
│  │                                                       │    │
│  │  try {                                                │    │
│  │    1. Auth check       → fail? → allow + log         │    │
│  │    2. Geo redirect     → fail? → skip + continue     │    │
│  │    3. A/B assignment   → fail? → default variant     │    │
│  │    4. Rate limiting    → fail? → allow + log         │    │
│  │  } catch (e) {                                        │    │
│  │    → Log error                                        │    │
│  │    → Return NextResponse.next() (fail open)          │    │
│  │  }                                                    │    │
│  └──────────────────────────────────────────────────────┘    │
│       │                                                       │
│       ▼                                                       │
│  Request continues to page/route                             │
└──────────────────────────────────────────────────────────────┘
```

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export async function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Each middleware concern is wrapped in its own try/catch
  // so one failure doesn't block the others

  // 1. Authentication
  try {
    const authResult = await checkAuth(request);
    if (authResult.redirect) {
      return NextResponse.redirect(new URL(authResult.redirect, request.url));
    }
    if (authResult.userId) {
      response.headers.set('x-user-id', authResult.userId);
    }
  } catch (error) {
    // FAIL OPEN: If auth service is down, allow the request
    // The page-level auth check will handle it
    console.error('[Middleware] Auth check failed:', error);
    logMiddlewareError('auth', error, request);
  }

  // 2. Geolocation-based redirect
  try {
    const geo = request.geo;
    if (geo?.country && shouldRedirectCountry(geo.country, request.nextUrl.pathname)) {
      const localizedPath = getLocalizedPath(geo.country, request.nextUrl.pathname);
      return NextResponse.redirect(new URL(localizedPath, request.url));
    }
  } catch (error) {
    // FAIL OPEN: Skip geo redirect if it fails
    console.error('[Middleware] Geo redirect failed:', error);
    logMiddlewareError('geo', error, request);
  }

  // 3. A/B Testing
  try {
    const variant = request.cookies.get('ab_variant')?.value || assignVariant();
    response.cookies.set('ab_variant', variant, {
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 30,
    });
    response.headers.set('x-ab-variant', variant);
  } catch (error) {
    // FAIL OPEN: Use default variant
    response.headers.set('x-ab-variant', 'control');
    console.error('[Middleware] A/B test failed:', error);
    logMiddlewareError('ab-test', error, request);
  }

  // 4. Rate Limiting
  try {
    const ip = request.headers.get('x-forwarded-for') || request.ip || 'unknown';
    const isRateLimited = await checkRateLimit(ip, request.nextUrl.pathname);

    if (isRateLimited) {
      return new NextResponse('Too Many Requests', {
        status: 429,
        headers: {
          'Retry-After': '60',
          'Content-Type': 'text/plain',
        },
      });
    }
  } catch (error) {
    // FAIL OPEN: Don't rate limit if the service is down
    console.error('[Middleware] Rate limit check failed:', error);
    logMiddlewareError('rate-limit', error, request);
  }

  return response;
}

// Auth helper with timeout
async function checkAuth(request: NextRequest): Promise<{
  userId?: string;
  redirect?: string;
}> {
  const token = request.cookies.get('session')?.value;
  if (!token) {
    const isProtected = request.nextUrl.pathname.startsWith('/dashboard') ||
                         request.nextUrl.pathname.startsWith('/account');
    if (isProtected) {
      return { redirect: `/login?from=${encodeURIComponent(request.nextUrl.pathname)}` };
    }
    return {};
  }

  // Validate token with timeout
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2000); // 2s timeout

  try {
    const res = await fetch(`${process.env.AUTH_SERVICE_URL}/validate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) {
      // Token invalid — redirect to login
      return { redirect: '/login' };
    }

    const user = await res.json();
    return { userId: user.id };
  } catch (error) {
    clearTimeout(timeout);
    throw error; // Let caller handle
  }
}

// Geo helpers
function shouldRedirectCountry(country: string, pathname: string): boolean {
  const countryPrefixes = ['de', 'fr', 'es', 'ja'];
  const hasPrefix = countryPrefixes.some((p) => pathname.startsWith(`/${p}`));
  return !hasPrefix && countryPrefixes.includes(country.toLowerCase());
}

function getLocalizedPath(country: string, pathname: string): string {
  return `/${country.toLowerCase()}${pathname}`;
}

// A/B helper
function assignVariant(): string {
  return Math.random() < 0.5 ? 'control' : 'treatment';
}

// Rate limit check (using KV store)
async function checkRateLimit(ip: string, pathname: string): Promise<boolean> {
  // In production, use Vercel KV, Upstash Redis, etc.
  return false; // placeholder
}

// Error logging for middleware
function logMiddlewareError(concern: string, error: unknown, request: NextRequest) {
  // In production, send to monitoring service
  // Note: Can't use Node.js APIs in Edge Runtime
  const errorData = {
    concern,
    message: error instanceof Error ? error.message : String(error),
    url: request.nextUrl.pathname,
    timestamp: new Date().toISOString(),
  };

  // Use waitUntil if available (Vercel/Cloudflare)
  // to send error report without blocking the response
  if (typeof globalThis !== 'undefined') {
    fetch(process.env.ERROR_LOG_URL || '', {
      method: 'POST',
      body: JSON.stringify(errorData),
    }).catch(() => {});
  }
}

export const config = {
  matcher: [
    // Match all paths except static files and API routes
    '/((?!_next/static|_next/image|favicon.ico|api/).*)',
  ],
};
```

**Key principles for middleware error handling**:
1. **Fail open**: Never crash the entire request. If a middleware concern fails, skip it and continue.
2. **Timeout everything**: Edge runtime has strict execution time limits. Use `AbortController` with aggressive timeouts.
3. **Log asynchronously**: Use `waitUntil` or fire-and-forget fetch to log errors without blocking.
4. **Independent concerns**: Wrap each middleware concern in its own try/catch so they're isolated.
5. **No `error.tsx`**: Middleware has no error boundary — all error handling must be explicit.

---

## Q20. (Advanced) How do you design a comprehensive error handling strategy for a large-scale Next.js application with multiple teams?

**Scenario**: You're the tech lead of a large Next.js application with 200+ routes, 15 development teams, and millions of daily users. You need to establish an error handling standard that every team follows.

**Answer**:

A large-scale error handling strategy requires standardized patterns, shared infrastructure, and clear ownership.

```
Enterprise Error Handling Architecture:
┌──────────────────────────────────────────────────────────────────┐
│                    Application Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Team A (Checkout)  │ Team B (Catalog) │ Team C (Account) │   │
│  │  error.tsx           │ error.tsx         │ error.tsx         │   │
│  │  loading.tsx         │ loading.tsx       │ loading.tsx       │   │
│  │  not-found.tsx       │ not-found.tsx     │ not-found.tsx     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                    │
│  ┌──────────────────────────┴────────────────────────────────┐  │
│  │               Shared Error Infrastructure                  │  │
│  │                                                            │  │
│  │  • @company/error-boundary  (shared error.tsx template)    │  │
│  │  • @company/error-logger    (centralized logging)          │  │
│  │  • @company/toast           (notification system)          │  │
│  │  • @company/retry           (retry utilities)              │  │
│  │  • @company/error-types     (typed error classes)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                    │
│  ┌──────────────────────────┴────────────────────────────────┐  │
│  │               Platform Layer                                │  │
│  │                                                            │  │
│  │  • global-error.tsx  (platform team owns)                  │  │
│  │  • instrumentation.ts (centralized error capture)          │  │
│  │  • middleware.ts      (auth/rate-limit error handling)     │  │
│  │  • Sentry project     (shared monitoring)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Shared error boundary template**:

```tsx
// packages/shared-ui/src/error-boundary-template.tsx
'use client';

import { useEffect } from 'react';

interface ErrorBoundaryConfig {
  section: string;
  team: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  supportUrl?: string;
  customActions?: Array<{
    label: string;
    onClick: () => void;
    variant: 'primary' | 'secondary';
  }>;
}

export function createErrorBoundary(config: ErrorBoundaryConfig) {
  return function ErrorBoundary({
    error,
    reset,
  }: {
    error: Error & { digest?: string };
    reset: () => void;
  }) {
    useEffect(() => {
      // Centralized error reporting
      reportError({
        error,
        section: config.section,
        team: config.team,
        severity: config.severity,
      });
    }, [error]);

    return (
      <div
        className="p-6 text-center"
        data-testid={`error-boundary-${config.section}`}
        data-team={config.team}
        data-severity={config.severity}
      >
        <h2 className="text-xl font-bold mb-3">Something went wrong</h2>
        <p className="text-gray-600 mb-6">{getErrorMessage(error, config.severity)}</p>

        {error.digest && (
          <p className="text-xs text-gray-400 mb-4 font-mono">
            Ref: {error.digest}
          </p>
        )}

        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>

          {config.customActions?.map((action, i) => (
            <button
              key={i}
              onClick={action.onClick}
              className={`px-4 py-2 rounded-lg ${
                action.variant === 'primary'
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {action.label}
            </button>
          ))}

          {config.supportUrl && (
            <a href={config.supportUrl} className="px-4 py-2 border rounded-lg hover:bg-gray-50">
              Contact Support
            </a>
          )}
        </div>
      </div>
    );
  };
}

function getErrorMessage(error: Error, severity: string): string {
  if (severity === 'critical') {
    return 'A critical error occurred. Our team has been notified and is investigating.';
  }
  if (process.env.NODE_ENV === 'development') {
    return error.message;
  }
  return 'An unexpected error occurred. Please try again.';
}

async function reportError(params: {
  error: Error & { digest?: string };
  section: string;
  team: string;
  severity: string;
}) {
  try {
    await fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: params.error.message,
        digest: params.error.digest,
        stack: params.error.stack,
        section: params.section,
        team: params.team,
        severity: params.severity,
        url: window.location.href,
        timestamp: new Date().toISOString(),
      }),
      keepalive: true,
    });
  } catch {
    // Silent fail — don't throw in error boundary
  }
}
```

**Team usage**:

```tsx
// app/checkout/error.tsx
import { createErrorBoundary } from '@company/shared-ui';

export default createErrorBoundary({
  section: 'checkout',
  team: 'payments',
  severity: 'critical',
  supportUrl: '/support/checkout',
});
```

```tsx
// app/catalog/error.tsx
import { createErrorBoundary } from '@company/shared-ui';

export default createErrorBoundary({
  section: 'catalog',
  team: 'catalog',
  severity: 'high',
});
```

**Standardized error classification**:

```tsx
// packages/error-types/src/index.ts
export enum ErrorSeverity {
  CRITICAL = 'critical',   // Revenue impact, page broken
  HIGH = 'high',           // Major feature broken
  MEDIUM = 'medium',       // Minor feature degraded
  LOW = 'low',             // Cosmetic or non-blocking
}

export enum ErrorCategory {
  NETWORK = 'network',
  AUTH = 'auth',
  VALIDATION = 'validation',
  PAYMENT = 'payment',
  DATA = 'data',
  PERMISSION = 'permission',
  RATE_LIMIT = 'rate_limit',
  UNKNOWN = 'unknown',
}

export interface ClassifiedError {
  category: ErrorCategory;
  severity: ErrorSeverity;
  retryable: boolean;
  userMessage: string;
  internalMessage: string;
}

export function classifyError(error: Error): ClassifiedError {
  const message = error.message.toLowerCase();

  if (message.includes('fetch') || message.includes('network') || message.includes('econnrefused')) {
    return {
      category: ErrorCategory.NETWORK,
      severity: ErrorSeverity.HIGH,
      retryable: true,
      userMessage: 'Network error. Please check your connection.',
      internalMessage: error.message,
    };
  }

  if (message.includes('401') || message.includes('unauthorized')) {
    return {
      category: ErrorCategory.AUTH,
      severity: ErrorSeverity.MEDIUM,
      retryable: false,
      userMessage: 'Your session has expired. Please log in again.',
      internalMessage: error.message,
    };
  }

  if (message.includes('403') || message.includes('forbidden')) {
    return {
      category: ErrorCategory.PERMISSION,
      severity: ErrorSeverity.MEDIUM,
      retryable: false,
      userMessage: 'You don\'t have permission to access this resource.',
      internalMessage: error.message,
    };
  }

  if (message.includes('payment') || message.includes('402')) {
    return {
      category: ErrorCategory.PAYMENT,
      severity: ErrorSeverity.CRITICAL,
      retryable: true,
      userMessage: 'Payment could not be processed. Please try again.',
      internalMessage: error.message,
    };
  }

  if (message.includes('429') || message.includes('rate limit')) {
    return {
      category: ErrorCategory.RATE_LIMIT,
      severity: ErrorSeverity.LOW,
      retryable: true,
      userMessage: 'Too many requests. Please wait a moment.',
      internalMessage: error.message,
    };
  }

  return {
    category: ErrorCategory.UNKNOWN,
    severity: ErrorSeverity.HIGH,
    retryable: true,
    userMessage: 'An unexpected error occurred.',
    internalMessage: error.message,
  };
}
```

**Error handling governance checklist for teams**:

```
Every route segment MUST have:
  ✅ error.tsx using createErrorBoundary()
  ✅ loading.tsx with skeleton matching real content dimensions
  ✅ not-found.tsx for dynamic routes

Every Server Component MUST:
  ✅ Handle fetch errors (check res.ok)
  ✅ Use fetchWithRetry for external APIs
  ✅ Call notFound() for missing resources (not throw)

Every Server Action MUST:
  ✅ Return ActionResult<T> (not throw for expected errors)
  ✅ Validate input with zod schemas
  ✅ Log errors with team and section context

Every Client Component MUST:
  ✅ Wrap async operations in try/catch
  ✅ Use toast notifications for operation feedback
  ✅ Handle loading states explicitly

Platform team provides:
  ✅ global-error.tsx (last resort)
  ✅ instrumentation.ts (server error capture)
  ✅ Sentry integration (monitoring)
  ✅ Error alerting (PagerDuty/Slack)
  ✅ Error dashboard (trends/ownership)
```

This architecture ensures consistent error handling across teams while allowing team-specific customization. The shared infrastructure reduces boilerplate, and the error classification system enables automated severity-based alerting and routing.

---
