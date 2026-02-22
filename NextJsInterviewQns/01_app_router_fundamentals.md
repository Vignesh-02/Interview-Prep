# 1. App Router Fundamentals & File Conventions

## Topic Introduction

The **App Router** is the modern routing paradigm introduced in Next.js 13 and refined in Next.js 15/16. It replaces the legacy Pages Router with a **file-system-based** approach rooted in the `app/` directory. The App Router is built on top of **React Server Components (RSC)** by default, meaning every component inside `app/` is a Server Component unless explicitly marked with `"use client"`.

The file-convention system uses **special filenames** to define behavior:

```
app/
├── layout.tsx          ← Root layout (wraps entire app)
├── page.tsx            ← Root page (renders at /)
├── loading.tsx         ← Loading UI (Suspense boundary)
├── error.tsx           ← Error boundary
├── not-found.tsx       ← 404 page
├── template.tsx        ← Re-mounts on navigation (unlike layout)
├── dashboard/
│   ├── layout.tsx      ← Nested layout (persists across sub-routes)
│   ├── page.tsx        ← Renders at /dashboard
│   └── settings/
│       └── page.tsx    ← Renders at /dashboard/settings
```

**Key Architectural Shift**: In the Pages Router, each file was a route AND the component. In the App Router, `page.tsx` is the route entry, but layouts, loading states, error boundaries, and templates are separate concerns defined by convention.

**Why this matters for senior developers**: The App Router enables **nested layouts** that persist across navigations (no re-mount), **streaming SSR** with Suspense, and **granular caching** — all critical for production performance. Understanding file conventions deeply lets you architect applications that are both fast and maintainable.

---

## Q1. (Beginner) What is the App Router in Next.js 15, and how does it differ from the Pages Router?

**Scenario**: Your team is starting a new project and debating whether to use the `pages/` or `app/` directory.

**Answer**:

The **App Router** (introduced in Next.js 13, stable from 13.4+) uses the `app/` directory and is built on React Server Components. The **Pages Router** uses the `pages/` directory and renders everything as Client Components by default.

| Feature | Pages Router (`pages/`) | App Router (`app/`) |
|---------|------------------------|---------------------|
| Default component type | Client Component | Server Component |
| Layouts | Manual (`_app.tsx`, `_document.tsx`) | File-based (`layout.tsx`) |
| Data fetching | `getServerSideProps`, `getStaticProps` | `async` Server Components, `fetch` |
| Loading states | Manual | `loading.tsx` (auto Suspense) |
| Error handling | `_error.tsx` (global) | `error.tsx` (per-route) |
| Streaming | Limited | Built-in with Suspense |
| Nested layouts | Not supported natively | First-class support |

```tsx
// Pages Router — data fetching is separate from the component
// pages/users.tsx
export async function getServerSideProps() {
  const res = await fetch('https://api.example.com/users');
  const users = await res.json();
  return { props: { users } };
}

export default function UsersPage({ users }) {
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}

// App Router — data fetching is inline in the component
// app/users/page.tsx
export default async function UsersPage() {
  const res = await fetch('https://api.example.com/users');
  const users = await res.json();
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
```

**Production recommendation**: New projects should use the App Router. Both routers can coexist in the same project during migration.

---

## Q2. (Beginner) What are the special file conventions in the App Router? List each and its purpose.

**Answer**:

| File | Purpose | When it renders |
|------|---------|----------------|
| `page.tsx` | Route UI — makes a route publicly accessible | When the URL matches the folder path |
| `layout.tsx` | Shared UI that wraps child routes; persists across navigations | On initial load, persists on navigation |
| `template.tsx` | Like layout but **re-mounts** on every navigation | On every navigation |
| `loading.tsx` | Loading UI — auto-wrapped in `<Suspense>` | While page/child is loading |
| `error.tsx` | Error boundary — catches runtime errors in child tree | When an error occurs |
| `not-found.tsx` | 404 UI — triggered by `notFound()` | When `notFound()` is called or no route matches |
| `route.ts` | API Route Handler (GET, POST, etc.) | When an API request hits the route |
| `default.tsx` | Fallback for parallel routes | When no matching slot is found |
| `global-error.tsx` | Root-level error boundary (wraps root layout) | When root layout/page throws |

```tsx
// app/dashboard/layout.tsx — persists sidebar across all /dashboard/* pages
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <aside className="w-64 border-r p-4">
        <nav>
          <a href="/dashboard">Overview</a>
          <a href="/dashboard/analytics">Analytics</a>
          <a href="/dashboard/settings">Settings</a>
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
```

**Key insight**: `layout.tsx` does NOT re-render when you navigate between child routes. This is a major performance win over the Pages Router.

---

## Q3. (Beginner) How does folder-based routing work in the App Router? Create a route for `/blog/[slug]`.

**Scenario**: You need a blog with dynamic URLs like `/blog/my-first-post`.

**Answer**:

In the App Router, the folder structure directly maps to URL paths. Only folders with a `page.tsx` file become publicly accessible routes.

```
app/
├── page.tsx                    → /
├── about/
│   └── page.tsx                → /about
├── blog/
│   ├── page.tsx                → /blog (list page)
│   └── [slug]/
│       └── page.tsx            → /blog/:slug (dynamic route)
```

```tsx
// app/blog/[slug]/page.tsx
interface BlogPostProps {
  params: Promise<{ slug: string }>;
}

// In Next.js 15, params is a Promise that must be awaited
export default async function BlogPost({ params }: BlogPostProps) {
  const { slug } = await params;

  const post = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { revalidate: 3600 }, // ISR: revalidate every hour
  }).then(res => res.json());

  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.content }} />
    </article>
  );
}

// Generate static paths at build time
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());
  return posts.map((post: { slug: string }) => ({ slug: post.slug }));
}
```

**Next.js 15 change**: `params` and `searchParams` are now **Promises** that must be `await`ed. This was synchronous in Next.js 14.

---

## Q4. (Beginner) What is the difference between `layout.tsx` and `template.tsx`?

**Scenario**: You have an analytics dashboard and want to log a page view every time the user navigates between dashboard sub-pages.

**Answer**:

| Feature | `layout.tsx` | `template.tsx` |
|---------|-------------|----------------|
| Re-mounts on navigation | No — persists state | Yes — creates new instance |
| Maintains state (e.g., input values) | Yes | No |
| useEffect re-runs on navigation | No | Yes |
| Use case | Persistent UI (sidebars, navs) | Per-navigation effects (analytics, animations) |

```tsx
// app/dashboard/template.tsx — re-mounts on every navigation
'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { trackPageView } from '@/lib/analytics';

export default function DashboardTemplate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  useEffect(() => {
    // This runs on EVERY navigation because template re-mounts
    trackPageView(pathname);
  }, [pathname]);

  return <div className="animate-fadeIn">{children}</div>;
}
```

```tsx
// app/dashboard/layout.tsx — does NOT re-mount
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  // This sidebar persists. If it had a useState for "collapsed",
  // that state survives when the user navigates between /dashboard/analytics
  // and /dashboard/settings.
  return (
    <div className="flex">
      <Sidebar />
      {children}
    </div>
  );
}
```

**Production tip**: Use `layout.tsx` by default. Only use `template.tsx` when you need per-navigation side effects like page-view tracking, entrance animations, or resetting form state.

---

## Q5. (Beginner) How do you create a "catch-all" route and an "optional catch-all" route?

**Answer**:

```
app/
├── docs/
│   └── [...slug]/
│       └── page.tsx        → Matches /docs/a, /docs/a/b, /docs/a/b/c
│                             Does NOT match /docs
│
├── shop/
│   └── [[...slug]]/
│       └── page.tsx        → Matches /shop, /shop/a, /shop/a/b, /shop/a/b/c
│                             Double brackets = optional (matches the base too)
```

```tsx
// app/docs/[...slug]/page.tsx
interface DocsPageProps {
  params: Promise<{ slug: string[] }>;
}

export default async function DocsPage({ params }: DocsPageProps) {
  const { slug } = await params;
  // /docs/getting-started/install → slug = ['getting-started', 'install']

  const docPath = slug.join('/');
  const doc = await getDocByPath(docPath);

  return (
    <article>
      <nav>
        {/* Breadcrumb from slug segments */}
        {slug.map((segment, i) => (
          <span key={i}>
            {i > 0 && ' / '}
            <a href={`/docs/${slug.slice(0, i + 1).join('/')}`}>
              {segment.replace(/-/g, ' ')}
            </a>
          </span>
        ))}
      </nav>
      <h1>{doc.title}</h1>
      <div>{doc.content}</div>
    </article>
  );
}
```

**When to use each**:
- `[...slug]` — When the base route (`/docs`) should show a different page or 404
- `[[...slug]]` — When the base route (`/shop`) and all sub-paths use the same component

---

## Q6. (Intermediate) Explain Route Groups and how they help organize a large Next.js application without affecting the URL structure.

**Scenario**: Your e-commerce app has a marketing site and an authenticated dashboard. Both are at the root level but need completely different layouts.

**Answer**:

Route groups are created by wrapping a folder name in parentheses `(folderName)`. They are **excluded from the URL path** but allow you to:
1. Organize routes logically
2. Create multiple root layouts
3. Split code by team/feature

```
app/
├── (marketing)/
│   ├── layout.tsx          ← Public layout (header, footer)
│   ├── page.tsx            → /
│   ├── about/
│   │   └── page.tsx        → /about
│   └── pricing/
│       └── page.tsx        → /pricing
│
├── (dashboard)/
│   ├── layout.tsx          ← Authenticated layout (sidebar, topbar)
│   ├── dashboard/
│   │   └── page.tsx        → /dashboard
│   └── settings/
│       └── page.tsx        → /settings
│
├── (auth)/
│   ├── layout.tsx          ← Minimal layout (centered card)
│   ├── login/
│   │   └── page.tsx        → /login
│   └── register/
│       └── page.tsx        → /register
```

```tsx
// app/(marketing)/layout.tsx
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="border-b">
        <nav className="max-w-6xl mx-auto p-4 flex justify-between">
          <a href="/" className="font-bold text-xl">Brand</a>
          <div className="space-x-4">
            <a href="/pricing">Pricing</a>
            <a href="/about">About</a>
            <a href="/login" className="bg-blue-600 text-white px-4 py-2 rounded">Login</a>
          </div>
        </nav>
      </header>
      <main>{children}</main>
      <footer className="border-t p-8 text-center text-gray-500">
        © 2025 Brand Inc.
      </footer>
    </>
  );
}

// app/(dashboard)/layout.tsx
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect('/login');

  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-900 text-white p-4">
        <nav className="space-y-2">
          <a href="/dashboard">Dashboard</a>
          <a href="/settings">Settings</a>
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
```

**Senior insight**: Route groups enable **multiple root layouts** — each group can have its own `layout.tsx` with completely different HTML structure, CSS, and auth logic. This is impossible with the Pages Router's single `_app.tsx`.

---

## Q7. (Intermediate) How does the component hierarchy render in the App Router? Explain the nesting order of layout, template, error, loading, and page.

**Answer**:

When Next.js renders a route, it constructs a nested component tree following this exact order:

```tsx
<Layout>                    {/* layout.tsx — outermost, persistent */}
  <Template>                {/* template.tsx — re-mounts on nav */}
    <ErrorBoundary           {/* error.tsx — catches errors below */}
      fallback={<Error />}
    >
      <Suspense              {/* loading.tsx — shows while page loads */}
        fallback={<Loading />}
      >
        <Page />             {/* page.tsx — the actual route content */}
      </Suspense>
    </ErrorBoundary>
  </Template>
</Layout>
```

This nesting is **automatic** and applies per route segment. For nested routes:

```
app/
├── layout.tsx              → Root Layout
├── dashboard/
│   ├── layout.tsx          → Dashboard Layout
│   ├── loading.tsx         → Dashboard Loading
│   ├── error.tsx           → Dashboard Error
│   └── analytics/
│       ├── loading.tsx     → Analytics Loading
│       └── page.tsx        → Analytics Page
```

Renders as:

```tsx
<RootLayout>
  <DashboardLayout>
    <DashboardErrorBoundary>
      <Suspense fallback={<DashboardLoading />}>
        <Suspense fallback={<AnalyticsLoading />}>
          <AnalyticsPage />
        </Suspense>
      </Suspense>
    </DashboardErrorBoundary>
  </DashboardLayout>
</RootLayout>
```

**Critical production implication**: An `error.tsx` boundary CANNOT catch errors in the `layout.tsx` at the same level — the error boundary sits inside the layout. To catch layout errors, place the error boundary in the parent segment. For root layout errors, use `global-error.tsx`.

---

## Q8. (Intermediate) What is the `metadata` API in the App Router, and how do you implement dynamic metadata for SEO?

**Scenario**: Your blog needs unique `<title>`, `<meta description>`, and Open Graph tags for each post.

**Answer**:

The App Router provides two ways to define metadata:

**1. Static metadata (export a `metadata` object):**

```tsx
// app/about/page.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About Us | MyApp',
  description: 'Learn about our mission and team.',
  openGraph: {
    title: 'About Us',
    description: 'Learn about our mission and team.',
    images: ['/images/about-og.jpg'],
  },
};

export default function AboutPage() {
  return <h1>About Us</h1>;
}
```

**2. Dynamic metadata (export a `generateMetadata` function):**

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from 'next';

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await fetch(`https://api.example.com/posts/${slug}`).then(r => r.json());

  return {
    title: `${post.title} | My Blog`,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: [post.coverImage],
      type: 'article',
      publishedTime: post.publishedAt,
      authors: [post.author.name],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description: post.excerpt,
      images: [post.coverImage],
    },
    alternates: {
      canonical: `https://myblog.com/blog/${slug}`,
    },
  };
}

export default async function BlogPost({ params }: Props) {
  const { slug } = await params;
  const post = await fetch(`https://api.example.com/posts/${slug}`).then(r => r.json());
  return <article><h1>{post.title}</h1></article>;
}
```

**Metadata merging**: Child metadata merges with parent metadata. Child values override parent for the same field.

```tsx
// app/layout.tsx — base metadata
export const metadata: Metadata = {
  title: {
    template: '%s | MyApp',    // %s is replaced by child title
    default: 'MyApp',
  },
  metadataBase: new URL('https://myapp.com'),
};
```

**Production tip**: Use `generateMetadata` for any page with dynamic content. The `fetch` calls inside `generateMetadata` are **deduplicated** with the same `fetch` calls in the page component — Next.js memoizes them automatically.

---

## Q9. (Intermediate) How do `params` and `searchParams` work in Next.js 15? Why are they now Promises?

**Scenario**: In Next.js 15, your existing code that destructured `params` synchronously is now broken.

**Answer**:

In **Next.js 15**, both `params` and `searchParams` changed from synchronous objects to **Promises**. This is a breaking change that enables performance optimizations (the router can start rendering before all params are resolved).

```tsx
// ❌ Next.js 14 (old — no longer works in 15)
export default function Page({ params }: { params: { id: string } }) {
  return <div>ID: {params.id}</div>;
}

// ✅ Next.js 15 (params is a Promise)
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <div>ID: {id}</div>;
}
```

For **Client Components** that can't use `async/await`:

```tsx
'use client';

import { use } from 'react';

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params); // React 19's use() hook unwraps Promises
  return <div>ID: {id}</div>;
}
```

**searchParams** work the same way:

```tsx
// app/search/page.tsx
interface SearchPageProps {
  searchParams: Promise<{ q?: string; page?: string }>;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q = '', page = '1' } = await searchParams;

  const results = await fetch(
    `https://api.example.com/search?q=${q}&page=${page}`
  ).then(r => r.json());

  return (
    <div>
      <h1>Results for "{q}" (Page {page})</h1>
      {results.map((item: any) => (
        <div key={item.id}>{item.title}</div>
      ))}
    </div>
  );
}
```

**Why the change**: Making params async allows Next.js to start rendering the shell (layout, loading states) before dynamic segments are resolved, enabling faster initial paint through streaming.

---

## Q10. (Intermediate) How do you handle colocation of non-route files in the `app/` directory? What's the difference between private folders, `_components`, and the `src/` pattern?

**Answer**:

Only `page.tsx` and `route.ts` make a folder a publicly accessible route. Other files (components, utils, types) can live alongside routes without creating new routes.

**Strategy 1: Colocation (recommended for feature-specific code)**

```
app/dashboard/
├── page.tsx
├── _components/           ← Private folder (underscore prefix)
│   ├── DashboardChart.tsx
│   └── StatsCard.tsx
├── _lib/
│   └── dashboard-utils.ts
└── _types/
    └── dashboard.ts
```

**Strategy 2: Private folders with underscore prefix**

Folders prefixed with `_` are excluded from routing entirely:

```
app/
├── _components/           ← Never becomes a route
│   ├── Button.tsx
│   └── Modal.tsx
├── dashboard/
│   └── page.tsx
```

**Strategy 3: `src/` directory pattern**

```
src/
├── app/                   ← Route files only
│   ├── layout.tsx
│   └── dashboard/
│       └── page.tsx
├── components/            ← Shared components
├── lib/                   ← Utilities
├── hooks/                 ← Custom hooks
└── types/                 ← TypeScript types
```

**Production recommendation**: For large teams, use the `src/` pattern with the `app/` directory containing only route files. This provides clear separation and avoids accidental route creation. Private `_` folders are useful for route-specific components.

---

## Q11. (Intermediate) How does navigation work in the App Router? Compare `<Link>`, `useRouter`, `redirect()`, and `permanentRedirect()`.

**Scenario**: You need to implement navigation across different contexts — user clicks, programmatic redirects, and server-side redirects.

**Answer**:

| Method | Context | Use Case |
|--------|---------|----------|
| `<Link>` | Client Component / RSC | Declarative navigation (replaces `<a>`) |
| `useRouter()` | Client Component only | Programmatic navigation (after form submit, etc.) |
| `redirect()` | Server Component / Server Action / Route Handler | Server-side redirect (throws internally) |
| `permanentRedirect()` | Same as `redirect()` | 308 permanent redirect |
| `usePathname()` | Client Component | Read current path |
| `useSearchParams()` | Client Component | Read query params |

```tsx
// 1. <Link> — Prefetches by default, client-side navigation
import Link from 'next/link';

export default function Nav() {
  return (
    <nav>
      <Link href="/dashboard">Dashboard</Link>
      <Link href="/blog/hello-world" prefetch={false}>Blog Post</Link>
      <Link href={{ pathname: '/search', query: { q: 'nextjs' } }}>Search</Link>
    </nav>
  );
}
```

```tsx
// 2. useRouter — Programmatic navigation in Client Components
'use client';

import { useRouter } from 'next/navigation'; // NOT 'next/router'!

export default function LoginForm() {
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const success = await loginUser(/* ... */);
    if (success) {
      router.push('/dashboard');      // Navigate
      // router.replace('/dashboard'); // Replace (no back button)
      // router.refresh();             // Re-fetch server components
      // router.back();                // Go back
      // router.prefetch('/settings'); // Prefetch a route
    }
  }

  return <form onSubmit={handleSubmit}>{/* ... */}</form>;
}
```

```tsx
// 3. redirect() — Server-side redirect (in Server Components or Server Actions)
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';

export default async function ProtectedPage() {
  const session = await getSession();
  if (!session) {
    redirect('/login'); // Throws a NEXT_REDIRECT error — stops rendering
  }
  return <div>Welcome, {session.user.name}</div>;
}
```

**Senior gotcha**: `redirect()` works by throwing a special error, so it must NOT be called inside a `try/catch` block (the catch would swallow it). If you must use try/catch, re-throw `NEXT_REDIRECT` errors.

---

## Q12. (Intermediate) What happens during a client-side navigation in the App Router? Explain prefetching, the Router Cache, and partial rendering.

**Answer**:

When a user clicks a `<Link>`, Next.js performs a **soft navigation** (no full page reload). Here's the full flow:

```
1. PREFETCH (on hover / viewport entry)
   └─ Next.js fetches the RSC payload for the target route
   └─ Stores it in the client-side Router Cache

2. NAVIGATE (on click)
   └─ Check Router Cache for prefetched data
   └─ If cached → instant navigation
   └─ If not → show loading.tsx while fetching

3. PARTIAL RENDERING
   └─ Only the segments that changed are re-rendered
   └─ Shared layouts are NOT re-rendered or re-mounted
   └─ React reconciles the new page into the existing tree

4. SCROLL RESTORATION
   └─ Scroll position is restored for back/forward navigation
   └─ New navigations scroll to top
```

```tsx
// Prefetch behavior:
<Link href="/dashboard">
  {/* Default: prefetched when visible in viewport */}
  {/* Static routes: full route prefetched */}
  {/* Dynamic routes: prefetched up to nearest loading.tsx boundary */}
</Link>

<Link href="/dashboard" prefetch={false}>
  {/* No prefetch — only fetches on click */}
</Link>

<Link href="/dashboard" prefetch={true}>
  {/* Force full prefetch even for dynamic routes */}
</Link>
```

**Router Cache (Next.js 15 change)**: In Next.js 15, `GET` Route Handlers and client-side router cache are **no longer cached by default**. Pages using `searchParams` or dynamic functions opt out of caching. This was a major change from Next.js 14 where everything was aggressively cached.

**Production impact**: Understanding partial rendering is key — if you navigate from `/dashboard/analytics` to `/dashboard/settings`, only the `page.tsx` changes. The `DashboardLayout` stays mounted with its state intact. This is why layouts should hold persistent state (sidebar collapsed state, etc.).

---

## Q13. (Advanced) How do you coexist the App Router and Pages Router in a single project during a migration? What are the pitfalls?

**Scenario**: You're migrating a large production app from Pages Router to App Router incrementally.

**Answer**:

Next.js supports both routers simultaneously. The App Router takes priority for matching routes.

```
├── app/
│   ├── layout.tsx
│   ├── dashboard/
│   │   └── page.tsx        → Handled by App Router
│   └── settings/
│       └── page.tsx        → Handled by App Router
│
├── pages/
│   ├── _app.tsx            → Still wraps Pages Router pages
│   ├── _document.tsx
│   ├── about.tsx           → Handled by Pages Router (/about)
│   └── blog/
│       └── [slug].tsx      → Handled by Pages Router (/blog/:slug)
```

**Migration strategy**:

```tsx
// Step 1: Create app/layout.tsx (required root layout)
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

// Step 2: Move routes one by one from pages/ to app/
// Delete pages/dashboard.tsx → Create app/dashboard/page.tsx

// Step 3: Move global providers
// Before (pages/_app.tsx):
function MyApp({ Component, pageProps }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Component {...pageProps} />
      </AuthProvider>
    </ThemeProvider>
  );
}

// After (app/layout.tsx):
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

**Pitfalls**:

1. **Duplicate routes**: If the same route exists in both `app/` and `pages/`, the App Router wins. This can cause silent bugs.
2. **Middleware applies to both**: Middleware runs for all routes regardless of router.
3. **Provider duplication**: If `_app.tsx` wraps providers and `layout.tsx` also wraps providers, Pages Router pages get double providers.
4. **Different `useRouter`**: `next/navigation` (App Router) vs `next/router` (Pages Router) — using the wrong one crashes.
5. **SEO**: Metadata API (App Router) vs `next/head` (Pages Router) — they don't mix.

**Senior approach**: Migrate leaf pages first (no children), then move up to layout-heavy sections. Keep shared components in `src/components/` to work with both routers.

---

## Q14. (Advanced) Explain the Next.js 15 `after()` API. How does it enable post-response work?

**Scenario**: After a user submits a form, you want to log analytics and send a notification email without making the user wait.

**Answer**:

`after()` is a new API in Next.js 15 that schedules work to run **after the response has been sent to the client**. This is similar to Go's `defer` or a background job, but lightweight.

```tsx
// app/api/checkout/route.ts
import { after } from 'next/server';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const order = await processOrder(request);

  // Schedule post-response work
  after(async () => {
    // These run AFTER the response is sent — user doesn't wait
    await sendOrderConfirmationEmail(order);
    await updateAnalytics('order_completed', order.id);
    await notifyWarehouse(order);
    await syncWithCRM(order.customerId);
  });

  // Response is sent immediately
  return NextResponse.json({ success: true, orderId: order.id });
}
```

```tsx
// Also works in Server Components
import { after } from 'next/server';

export default async function Page() {
  const data = await fetchData();

  after(async () => {
    await logPageView('/dashboard');
    await warmCache('dashboard-data');
  });

  return <Dashboard data={data} />;
}
```

**How it works**:
- Response streams to the client immediately
- `after()` callbacks run in the same serverless invocation
- If the serverless function is killed (e.g., Lambda timeout), `after()` work may be lost
- Not a replacement for durable background jobs (use a queue for those)

**Production use cases**:
- Analytics/logging that shouldn't block the response
- Cache warming
- Sending notifications
- Lightweight data synchronization

**Comparison with alternatives**:
| Method | Durability | Latency Impact | Use Case |
|--------|-----------|----------------|----------|
| `after()` | Low (same invocation) | None | Analytics, logging |
| Queue (SQS, BullMQ) | High | None | Critical jobs, emails |
| `waitUntil()` (Vercel) | Medium | None | Edge runtime post-work |
| Inline `await` | N/A | High | Don't do this for non-critical work |

---

## Q15. (Advanced) How does the Next.js compiler (SWC/Turbopack) handle the `"use client"` and `"use server"` boundaries? What happens under the hood?

**Answer**:

The `"use client"` and `"use server"` directives are **module-level boundaries** that tell the compiler how to split the module graph.

```
Module Graph Split:
                                    
  Server Component Graph        Client Component Graph
  ┌──────────────────┐          ┌──────────────────┐
  │ app/page.tsx     │          │                  │
  │ (Server)         │──refs──→ │ components/      │
  │                  │          │ Counter.tsx       │
  │ Can import:      │          │ "use client"     │
  │ - Server modules │          │                  │
  │ - Client refs    │          │ Can import:      │
  │                  │          │ - Client modules │
  │ Cannot:          │          │ - Hooks          │
  │ - useState       │          │ - Browser APIs   │
  │ - onClick        │          │                  │
  └──────────────────┘          └──────────────────┘
```

**What the compiler does**:

1. **Identifies boundaries**: Scans for `"use client"` at the top of files
2. **Splits the graph**: Creates separate bundles for server and client
3. **Creates references**: Server Components that import Client Components get a **reference placeholder** (not the actual code)
4. **Serializes the tree**: The RSC payload includes serialized Server Component output and Client Component references
5. **Client hydrates**: The client runtime resolves references and hydrates only Client Components

```tsx
// What you write:
// app/page.tsx (Server Component)
import Counter from './Counter'; // Client Component

export default async function Page() {
  const data = await db.query('SELECT count FROM stats');
  return (
    <div>
      <h1>Stats</h1>
      <Counter initialCount={data.count} /> {/* Client Component */}
    </div>
  );
}

// components/Counter.tsx
'use client';
import { useState } from 'react';

export default function Counter({ initialCount }: { initialCount: number }) {
  const [count, setCount] = useState(initialCount);
  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>;
}
```

```
// What gets sent to the client (simplified RSC payload):
{
  "type": "div",
  "children": [
    { "type": "h1", "children": "Stats" },         // Already rendered HTML
    { "$ref": "Counter", "props": { "initialCount": 42 } }  // Client reference
  ]
}
// + Client bundle containing Counter.tsx code
```

**Critical rules**:
- `"use client"` marks the boundary — everything imported by that file is also client
- You can pass serializable props from Server → Client (no functions, no classes)
- `"use server"` marks functions as Server Actions (callable from client)
- You cannot import a Server Component INTO a Client Component (but you can pass it as `children`)

```tsx
// ✅ Correct: Pass Server Component as children
'use client';
export function ClientWrapper({ children }: { children: React.ReactNode }) {
  const [show, setShow] = useState(true);
  return show ? children : null;
}

// In a Server Component:
<ClientWrapper>
  <ServerComponent /> {/* This works! Rendered on server, passed as prop */}
</ClientWrapper>
```

---

## Q16. (Advanced) Your Next.js 15 app has slow initial page loads. Walk through your systematic debugging process.

**Scenario**: A production e-commerce page takes 4.2 seconds for LCP. The target is under 2.5 seconds.

**Answer**:

**Step 1: Identify the bottleneck type**

```bash
# Enable Next.js build analysis
ANALYZE=true next build

# Check the server-side rendering time
# In next.config.js:
module.exports = {
  logging: {
    fetches: {
      fullUrl: true,   // Log all fetch URLs during SSR
    },
  },
};
```

**Step 2: Check data fetching waterfall**

```tsx
// ❌ PROBLEM: Sequential fetches (waterfall)
export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  const product = await getProduct(id);          // 200ms
  const reviews = await getReviews(id);          // 300ms
  const recommendations = await getRecommendations(id); // 400ms
  // Total: 900ms sequential

  return <div>{/* ... */}</div>;
}

// ✅ FIX: Parallel fetches
export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  const [product, reviews, recommendations] = await Promise.all([
    getProduct(id),            // 200ms ─┐
    getReviews(id),            // 300ms ─┤ parallel
    getRecommendations(id),    // 400ms ─┘
  ]);
  // Total: 400ms (max of the three)

  return <div>{/* ... */}</div>;
}
```

**Step 3: Add streaming for non-critical content**

```tsx
import { Suspense } from 'react';

export default async function ProductPage({ params }: Props) {
  const { id } = await params;
  const product = await getProduct(id); // Critical — await

  return (
    <div>
      <ProductInfo product={product} />   {/* Renders immediately */}

      <Suspense fallback={<ReviewsSkeleton />}>
        <Reviews productId={id} />         {/* Streams in later */}
      </Suspense>

      <Suspense fallback={<RecommendationsSkeleton />}>
        <Recommendations productId={id} /> {/* Streams in later */}
      </Suspense>
    </div>
  );
}
```

**Step 4: Check bundle size**

```bash
# Install bundle analyzer
npm install @next/bundle-analyzer

# next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({
  // ...config
});
```

**Step 5: Profile with Next.js instrumentation**

```tsx
// instrumentation.ts (Next.js 15)
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { NodeSDK } = await import('@opentelemetry/sdk-node');
    const sdk = new NodeSDK({
      // Configure tracing to see exactly where time is spent
    });
    sdk.start();
  }
}
```

**Common culprits and fixes**:
| Bottleneck | Diagnosis | Fix |
|-----------|-----------|-----|
| Sequential data fetching | Logging shows waterfall | `Promise.all()` + Suspense |
| Large client bundle | Bundle analyzer | Dynamic imports, tree shaking |
| Unoptimized images | LCP element is an image | `next/image` with priority |
| No caching | Same fetch on every request | `revalidate` / `cache()` |
| Cold starts | First request after deploy is slow | Provisioned concurrency / warm-up |
| Third-party scripts | Render-blocking JS | `next/script` with `strategy="lazyOnload"` |

---

## Q17. (Advanced) How do you handle environment variables in Next.js 15, and what security pitfalls should senior developers watch for?

**Answer**:

Next.js has a strict environment variable system:

```
.env                  ← Default for all environments
.env.local            ← Local overrides (gitignored)
.env.development      ← Only in `next dev`
.env.production       ← Only in `next build` / `next start`
.env.test             ← Only when NODE_ENV=test
```

**The critical security rule**:

```bash
# Server-only (NEVER sent to browser)
DATABASE_URL=postgres://user:pass@host:5432/db
API_SECRET_KEY=sk_live_abc123

# Client-exposed (MUST have NEXT_PUBLIC_ prefix)
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_STRIPE_KEY=pk_live_xyz789
```

```tsx
// Server Component — can access ALL env vars
export default async function Page() {
  const db = await connectDB(process.env.DATABASE_URL); // ✅ Works
  return <div>{/* ... */}</div>;
}

// Client Component — can ONLY access NEXT_PUBLIC_ vars
'use client';
export default function Checkout() {
  // ✅ Works — has NEXT_PUBLIC_ prefix
  const stripeKey = process.env.NEXT_PUBLIC_STRIPE_KEY;

  // ❌ undefined — no NEXT_PUBLIC_ prefix
  const secret = process.env.API_SECRET_KEY; // undefined!

  return <div>...</div>;
}
```

**Senior-level security pitfalls**:

```tsx
// ❌ PITFALL 1: Accidentally exposing secrets via props
// app/page.tsx (Server Component)
export default function Page() {
  return (
    <ClientComponent
      config={{
        apiUrl: process.env.API_URL,
        apiKey: process.env.API_SECRET_KEY, // 💀 This gets serialized to client!
      }}
    />
  );
}

// ✅ FIX: Only pass non-sensitive data
export default function Page() {
  return (
    <ClientComponent
      config={{
        apiUrl: process.env.NEXT_PUBLIC_API_URL,
      }}
    />
  );
}

// ❌ PITFALL 2: Server-only module imported in client
// lib/db.ts
import { Pool } from 'pg';
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

// If a Client Component somehow imports this, DATABASE_URL leaks.
// ✅ FIX: Use the 'server-only' package
// lib/db.ts
import 'server-only'; // Throws build error if imported in Client Component
import { Pool } from 'pg';
```

```tsx
// ✅ Runtime validation of env vars (recommended for production)
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  API_SECRET_KEY: z.string().min(1),
  NEXT_PUBLIC_API_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
// Throws at build/start time if any var is missing — fail fast
```

---

## Q18. (Advanced) Design a Next.js 15 app structure for a multi-tenant SaaS application where each tenant has a custom subdomain.

**Scenario**: Your SaaS product serves tenants at `acme.myapp.com`, `globex.myapp.com`, etc. Each tenant has different branding and data.

**Answer**:

```tsx
// middleware.ts — Extract tenant from subdomain
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const subdomain = hostname.split('.')[0];

  // Skip for main domain and static files
  if (subdomain === 'www' || subdomain === 'myapp') {
    return NextResponse.next();
  }

  // Verify tenant exists (use edge-compatible check)
  // Rewrite to tenant-specific path internally
  const url = request.nextUrl.clone();
  url.pathname = `/tenant/${subdomain}${url.pathname}`;

  return NextResponse.rewrite(url);
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

```
app/
├── tenant/
│   └── [domain]/
│       ├── layout.tsx       ← Tenant-specific layout with branding
│       ├── page.tsx         ← Tenant dashboard
│       ├── settings/
│       │   └── page.tsx
│       └── billing/
│           └── page.tsx
```

```tsx
// app/tenant/[domain]/layout.tsx
import { notFound } from 'next/navigation';

interface TenantLayoutProps {
  children: React.ReactNode;
  params: Promise<{ domain: string }>;
}

export default async function TenantLayout({ children, params }: TenantLayoutProps) {
  const { domain } = await params;
  const tenant = await getTenant(domain);

  if (!tenant) notFound();

  return (
    <div
      style={{
        '--primary-color': tenant.brandColor,
        '--logo-url': `url(${tenant.logoUrl})`,
      } as React.CSSProperties}
    >
      <header className="border-b p-4">
        <img src={tenant.logoUrl} alt={tenant.name} className="h-8" />
        <h1>{tenant.name}</h1>
      </header>
      <TenantContext.Provider value={tenant}>
        {children}
      </TenantContext.Provider>
    </div>
  );
}
```

```tsx
// lib/tenant.ts
import 'server-only';
import { cache } from 'react';

// cache() deduplicates across the same request
export const getTenant = cache(async (domain: string) => {
  const tenant = await db.tenant.findUnique({
    where: { domain },
    select: {
      id: true,
      name: true,
      domain: true,
      brandColor: true,
      logoUrl: true,
      plan: true,
    },
  });
  return tenant;
});
```

**Senior considerations**:
- **DNS**: Configure wildcard DNS (`*.myapp.com`) pointing to your deployment
- **SSL**: Use wildcard SSL certificates or services like Vercel/Cloudflare that handle this
- **Data isolation**: Use tenant ID in all database queries (row-level security in Postgres)
- **Caching**: Cache key must include the tenant domain
- **Rate limiting**: Per-tenant rate limits to prevent one tenant from affecting others

---

## Q19. (Advanced) Explain the full request lifecycle in a Next.js 15 production deployment (from DNS resolution to hydrated page).

**Answer**:

```
1. DNS Resolution
   └─ Browser resolves myapp.com → CDN edge IP (e.g., Vercel Edge Network)

2. TLS Handshake
   └─ HTTPS connection established at the edge

3. Edge Network (CDN)
   ├─ Static assets? → Serve from edge cache (immutable, long max-age)
   ├─ Cached page? → Serve stale-while-revalidate if configured
   └─ Dynamic/uncached? → Forward to origin

4. Middleware (runs at the edge)
   ├─ middleware.ts executes
   ├─ Can rewrite, redirect, add headers
   ├─ Runs BEFORE any rendering
   └─ Uses the Edge Runtime (V8 isolates, no Node.js APIs)

5. Routing Resolution
   └─ Next.js matches URL to route segment in app/

6. Layout/Page Rendering (on origin server)
   ├─ Execute layouts from root → leaf
   ├─ Execute page.tsx
   ├─ Server Components render to RSC payload
   ├─ Data fetching happens (fetch, db queries)
   ├─ Check caches (Data Cache, Full Route Cache)
   └─ Generate HTML + RSC payload

7. Streaming Response
   ├─ HTML shell sent immediately (layout + loading.tsx)
   ├─ Suspense boundaries stream as they resolve
   ├─ RSC payload chunks stream alongside HTML
   └─ Client can start parsing/rendering before stream completes

8. Client-Side (Browser)
   ├─ Parse HTML → paint First Contentful Paint (FCP)
   ├─ Download JS bundles (code-split per route)
   ├─ React hydration:
   │   ├─ Match server HTML to Client Components
   │   ├─ Attach event listeners
   │   └─ Selective Hydration (prioritize interacted components)
   ├─ Page becomes interactive (TTI)
   └─ Prefetch visible <Link> targets into Router Cache

9. Subsequent Navigation (client-side)
   ├─ Fetch RSC payload for new route
   ├─ Partial rendering (only changed segments)
   ├─ No full page reload
   └─ Shared layouts stay mounted
```

**Production performance levers at each stage**:
- **CDN**: Use `Cache-Control` headers, Vercel's ISR
- **Middleware**: Keep it lightweight — heavy middleware adds latency to every request
- **Rendering**: Parallel data fetching, `cache()` deduplication
- **Streaming**: Wrap slow components in Suspense
- **Client**: Minimize Client Components, use dynamic imports
- **Prefetching**: Ensure `<Link>` prefetches critical routes

---

## Q20. (Advanced) How would you implement A/B testing in a Next.js 15 App Router application without causing layout shift or hurting caching?

**Scenario**: Marketing wants to test two different hero sections on the landing page. 50% of users see variant A, 50% see variant B.

**Answer**:

```tsx
// middleware.ts — Assign variant at the edge (before rendering)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const EXPERIMENT_COOKIE = 'ab-hero-variant';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Check if user already has a variant
  if (!request.cookies.has(EXPERIMENT_COOKIE)) {
    // Assign randomly (50/50)
    const variant = Math.random() < 0.5 ? 'A' : 'B';
    response.cookies.set(EXPERIMENT_COOKIE, variant, {
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 30, // 30 days
      sameSite: 'lax',
    });
  }

  return response;
}
```

```tsx
// app/page.tsx — Server Component reads the cookie
import { cookies } from 'next/headers';
import { HeroA } from './_components/HeroA';
import { HeroB } from './_components/HeroB';
import { trackExperimentView } from '@/lib/analytics';
import { after } from 'next/server';

export default async function HomePage() {
  const cookieStore = await cookies();
  const variant = cookieStore.get('ab-hero-variant')?.value || 'A';

  // Track view without blocking the response
  after(async () => {
    await trackExperimentView('hero-experiment', variant);
  });

  return (
    <main>
      {variant === 'A' ? <HeroA /> : <HeroB />}
      <Features />
      <Pricing />
    </main>
  );
}
```

**Why this approach is production-grade**:

1. **No layout shift**: Variant is determined server-side before HTML is sent
2. **Consistent experience**: Cookie persists the assignment for 30 days
3. **Cacheable**: Use `Vary: Cookie` header or segment caching per variant
4. **Edge-fast**: Middleware assigns variant at the edge — no origin round-trip

**Advanced: Edge Config for instant experiment changes**:

```tsx
// middleware.ts — Use Vercel Edge Config for live experiment config
import { get } from '@vercel/edge-config';

export async function middleware(request: NextRequest) {
  const experiments = await get('experiments') as Record<string, { enabled: boolean; split: number }>;

  if (experiments?.['hero-test']?.enabled) {
    const variant = Math.random() < experiments['hero-test'].split ? 'A' : 'B';
    // ... set cookie
  }
}
```

**Caching strategy**:

```tsx
// next.config.js — Vary cache by experiment cookie
module.exports = {
  async headers() {
    return [
      {
        source: '/',
        headers: [
          { key: 'Vary', value: 'Cookie' }, // CDN caches separate versions per cookie
        ],
      },
    ];
  },
};
```

This ensures CDN doesn't serve variant A's cached page to a variant B user.
