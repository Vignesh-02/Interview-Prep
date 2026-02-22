# 3. Routing, Layouts & Templates — Deep Dive

## Topic Introduction

Next.js App Router uses a **file-system-based routing** paradigm that goes far beyond simple URL → component mapping. It introduces **nested layouts**, **route groups**, **parallel routes**, **intercepting routes**, and **template patterns** that enable sophisticated UI architectures.

```
Route Matching Hierarchy:
URL: /dashboard/analytics/monthly

app/
├── layout.tsx                    ← Root Layout (always renders)
├── dashboard/
│   ├── layout.tsx                ← Dashboard Layout (persists)
│   └── analytics/
│       ├── layout.tsx            ← Analytics Layout (persists)
│       └── monthly/
│           └── page.tsx          ← Page Component (route match)

Rendered as:
<RootLayout>
  <DashboardLayout>
    <AnalyticsLayout>
      <MonthlyPage />
    </AnalyticsLayout>
  </DashboardLayout>
</RootLayout>
```

Understanding advanced routing patterns is essential for senior Next.js developers because they directly impact **user experience** (instant navigations, persistent state), **performance** (partial rendering, streaming), and **code organization** (route groups, colocation).

---

## Q1. (Beginner) What is a nested layout, and why does it persist across navigations?

**Scenario**: You have a dashboard with a sidebar. When navigating between `/dashboard/analytics` and `/dashboard/settings`, the sidebar should not remount or lose its scroll position.

**Answer**:

A **nested layout** is a `layout.tsx` file inside a route folder. It wraps all child routes and **does not remount** when navigating between sibling routes.

```tsx
// app/dashboard/layout.tsx
'use client'; // Only needed if layout has state

import { useState } from 'react';
import Link from 'next/link';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  // This state PERSISTS when navigating between child routes!
  return (
    <div className="flex h-screen">
      <aside className={`${collapsed ? 'w-16' : 'w-64'} border-r transition-all`}>
        <button onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? '→' : '←'}
        </button>
        <nav className="space-y-1 p-2">
          <Link href="/dashboard" className="block p-2 rounded hover:bg-gray-100">
            Overview
          </Link>
          <Link href="/dashboard/analytics" className="block p-2 rounded hover:bg-gray-100">
            Analytics
          </Link>
          <Link href="/dashboard/settings" className="block p-2 rounded hover:bg-gray-100">
            Settings
          </Link>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        {children} {/* Only this part changes on navigation */}
      </main>
    </div>
  );
}
```

**Why it persists**: React's reconciliation only re-renders what changed. Since the layout component is the same between `/dashboard/analytics` and `/dashboard/settings`, React keeps it mounted and only swaps the `children` prop.

**Performance benefit**: No unnecessary re-renders of complex navigation, no lost scroll state, no refetching of layout data.

---

## Q2. (Beginner) How do you create a root layout, and what are its requirements?

**Answer**:

The **root layout** (`app/layout.tsx`) is the only **required** layout. It must include `<html>` and `<body>` tags.

```tsx
// app/layout.tsx — Root layout (REQUIRED)
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: {
    template: '%s | MyApp',
    default: 'MyApp — Build Faster',
  },
  description: 'A production Next.js application',
  metadataBase: new URL('https://myapp.com'),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
```

**Rules**:
- Must be in `app/layout.tsx`
- Must render `<html>` and `<body>`
- Is a **Server Component** by default (can be async)
- Cannot use `<Head>` from `next/head` — use `metadata` export instead
- Is NOT re-rendered on navigation (most persistent component)

---

## Q3. (Beginner) How do you create a loading state for a route?

**Answer**:

Add a `loading.tsx` file to automatically wrap the page in a `<Suspense>` boundary.

```tsx
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div className="space-y-4 p-6 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3" />
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-32 bg-gray-200 rounded" />
        ))}
      </div>
      <div className="h-64 bg-gray-200 rounded" />
    </div>
  );
}
```

This is equivalent to:

```tsx
// What Next.js does internally:
<DashboardLayout>
  <Suspense fallback={<DashboardLoading />}>
    <DashboardPage />
  </Suspense>
</DashboardLayout>
```

**When it shows**: The loading UI displays when navigating to a route whose `page.tsx` has async data fetching. It also shows on the initial server render while streaming.

---

## Q4. (Beginner) How do you handle 404 (not found) pages in the App Router?

**Answer**:

```tsx
// app/not-found.tsx — Global 404 page
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-6xl font-bold">404</h1>
      <p className="text-xl text-gray-600 mt-4">Page not found</p>
      <Link href="/" className="mt-6 text-blue-600 hover:underline">
        Go back home
      </Link>
    </div>
  );
}
```

**Triggering programmatically** with `notFound()`:

```tsx
// app/blog/[slug]/page.tsx
import { notFound } from 'next/navigation';

export default async function BlogPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(slug);

  if (!post) {
    notFound(); // Renders the nearest not-found.tsx
  }

  return <article><h1>{post.title}</h1></article>;
}
```

**Nested not-found**: You can have segment-specific 404 pages:

```
app/
├── not-found.tsx           ← Global 404
├── blog/
│   ├── not-found.tsx       ← Blog-specific 404 (e.g., "Post not found")
│   └── [slug]/
│       └── page.tsx
```

---

## Q5. (Beginner) What is the difference between `redirect()` and `permanentRedirect()`?

**Answer**:

```tsx
import { redirect, permanentRedirect } from 'next/navigation';

// redirect() — HTTP 307 (Temporary Redirect)
// Use for: auth redirects, temporary moves, conditional redirects
export default async function ProtectedPage() {
  const session = await getSession();
  if (!session) redirect('/login'); // 307 — browser will check again next time
  return <div>Protected content</div>;
}

// permanentRedirect() — HTTP 308 (Permanent Redirect)
// Use for: URL changes, slug changes, moved content
export default async function OldBlogPost({ params }: Props) {
  const { slug } = await params;
  const newSlug = await getNewSlug(slug); // Blog was restructured
  if (newSlug !== slug) {
    permanentRedirect(`/blog/${newSlug}`); // 308 — browser caches this
  }
  return <article>...</article>;
}
```

| Type | Status Code | Browser Caches? | SEO Impact |
|------|------------|----------------|------------|
| `redirect()` | 307 | No | Temporary — search engines keep old URL |
| `permanentRedirect()` | 308 | Yes | Permanent — search engines update to new URL |

**Production tip**: Use `permanentRedirect()` carefully — browsers cache 308 redirects aggressively. If you make a mistake, users may be stuck on the wrong URL until they clear their cache.

---

## Q6. (Intermediate) Explain Parallel Routes with a real-world example. How do `@slots` and `default.tsx` work?

**Scenario**: You're building a dashboard that shows analytics and a notification feed side by side, each independently loading and error-handling.

**Answer**:

**Parallel Routes** allow you to render multiple pages in the same layout simultaneously. They use named slots defined by `@folder` convention.

```
app/dashboard/
├── layout.tsx
├── page.tsx
├── @analytics/
│   ├── page.tsx            → Renders in the analytics slot
│   ├── loading.tsx         → Independent loading state
│   └── error.tsx           → Independent error boundary
├── @notifications/
│   ├── page.tsx            → Renders in the notifications slot
│   ├── loading.tsx
│   └── error.tsx
└── default.tsx             → Fallback when no slot matches
```

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  analytics,
  notifications,
}: {
  children: React.ReactNode;
  analytics: React.ReactNode;
  notifications: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-6">{children}</div>   {/* page.tsx */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">{analytics}</div>       {/* @analytics/page.tsx */}
        <div className="col-span-1">{notifications}</div>    {/* @notifications/page.tsx */}
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/@analytics/page.tsx
export default async function AnalyticsSlot() {
  const stats = await getAnalytics(); // Takes 2 seconds
  return (
    <div className="border rounded p-4">
      <h2>Analytics</h2>
      <div className="grid grid-cols-2 gap-4">
        <StatCard label="Revenue" value={`$${stats.revenue}`} />
        <StatCard label="Users" value={stats.activeUsers} />
      </div>
    </div>
  );
}

// app/dashboard/@notifications/page.tsx
export default async function NotificationsSlot() {
  const notifications = await getNotifications(); // Takes 500ms
  return (
    <div className="border rounded p-4">
      <h2>Notifications</h2>
      <ul>
        {notifications.map(n => (
          <li key={n.id}>{n.message}</li>
        ))}
      </ul>
    </div>
  );
}
```

**Benefits of parallel routes**:
1. **Independent loading**: Notifications loads in 500ms while analytics shows a skeleton
2. **Independent errors**: If analytics fails, notifications still works
3. **Independent streaming**: Each slot streams independently

**`default.tsx` explained**: When soft-navigating, if a parallel route doesn't have a matching sub-route, `default.tsx` is rendered. Without it, you get a 404.

```tsx
// app/dashboard/@analytics/default.tsx
export default function AnalyticsDefault() {
  // Shown when navigating to a dashboard sub-route that
  // @analytics doesn't have a matching page for
  return <div>Select a time period to view analytics</div>;
}
```

---

## Q7. (Intermediate) How do Intercepting Routes work? Build a modal pattern like Instagram's photo modal.

**Scenario**: When a user clicks a photo in the feed, it opens in a modal. If they share the URL, the full photo page loads instead.

**Answer**:

Intercepting routes allow you to load a route from another part of your app within the current layout. The convention uses `(.)`, `(..)`, `(...)`, or `(..)(..)`:

```
Convention    Matches
(.)           Same level
(..)          One level up
(..)(..)      Two levels up
(...)         From root
```

```
app/
├── layout.tsx
├── page.tsx                     → Feed page
├── @modal/
│   ├── default.tsx              → Empty (no modal by default)
│   └── (.)photo/
│       └── [id]/
│           └── page.tsx         → Photo modal (intercepts /photo/[id])
├── photo/
│   └── [id]/
│       └── page.tsx             → Full photo page (direct URL access)
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
        {modal}    {/* Modal slot — empty by default */}
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
// app/@modal/(.)photo/[id]/page.tsx — The intercepted modal view
'use client';

import { useRouter } from 'next/navigation';

export default function PhotoModal({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = React.use(params);

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center"
      onClick={() => router.back()}
    >
      <div
        className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <img src={`/photos/${id}.jpg`} alt="" className="w-full" />
        <div className="p-4">
          <h2>Photo {id}</h2>
          <p>Comments and details...</p>
        </div>
      </div>
    </div>
  );
}
```

```tsx
// app/photo/[id]/page.tsx — Full page view (direct URL or hard refresh)
export default async function PhotoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const photo = await getPhoto(id);

  return (
    <div className="max-w-4xl mx-auto p-8">
      <img src={photo.url} alt={photo.title} className="w-full rounded" />
      <h1 className="text-3xl mt-4">{photo.title}</h1>
      <p className="mt-2">{photo.description}</p>
    </div>
  );
}
```

**How it works**:
- **Soft navigation** (clicking a link in the feed): The intercepting route `@modal/(.)photo/[id]` renders in the modal slot, overlaying the feed
- **Hard navigation** (direct URL, refresh, shared link): The full `photo/[id]/page.tsx` renders normally
- **Back button**: `router.back()` closes the modal and restores the feed

---

## Q8. (Intermediate) How does the root layout differ from nested layouts in terms of re-rendering?

**Answer**:

```tsx
// Key principle: Layouts ONLY re-render when their own data changes,
// NOT when child routes change

// app/layout.tsx — Root layout
export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // This function runs on:
  // ✅ Initial page load
  // ✅ When router.refresh() is called
  // ❌ NOT on client-side navigation between routes

  const config = await getAppConfig();

  return (
    <html lang="en">
      <body>
        <AppHeader config={config} />
        {children}   {/* ← Only this prop changes on navigation */}
      </body>
    </html>
  );
}
```

```tsx
// app/dashboard/layout.tsx — Nested layout
export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  // This function runs on:
  // ✅ First visit to any /dashboard/* route
  // ✅ When router.refresh() is called
  // ❌ NOT when navigating between /dashboard/analytics and /dashboard/settings

  const user = await getCurrentUser();

  return (
    <div className="flex">
      <DashboardSidebar user={user} />
      <main>{children}</main>
    </div>
  );
}
```

**The "stale layout" problem**:

```tsx
// Scenario: User updates their name in /dashboard/settings
// The sidebar in DashboardLayout still shows the old name!

// Fix 1: router.refresh() — forces all Server Components to re-render
'use client';
import { useRouter } from 'next/navigation';

function UpdateNameForm() {
  const router = useRouter();

  async function handleSubmit(formData: FormData) {
    await updateName(formData);
    router.refresh(); // Re-renders ALL Server Components (layouts + page)
  }

  return <form action={handleSubmit}>...</form>;
}

// Fix 2: revalidatePath() in a Server Action
'use server';
import { revalidatePath } from 'next/cache';

export async function updateName(formData: FormData) {
  await db.user.update({ /* ... */ });
  revalidatePath('/dashboard'); // Revalidates the route and its layout
}
```

---

## Q9. (Intermediate) How do you implement breadcrumbs that dynamically reflect the current route hierarchy?

**Answer**:

```tsx
// components/Breadcrumbs.tsx
'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';

const routeLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  analytics: 'Analytics',
  settings: 'Settings',
  users: 'Users',
  billing: 'Billing',
};

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  return (
    <nav aria-label="Breadcrumb" className="text-sm text-gray-600">
      <ol className="flex items-center space-x-2">
        <li>
          <Link href="/" className="hover:text-gray-900">Home</Link>
        </li>
        {segments.map((segment, index) => {
          const href = '/' + segments.slice(0, index + 1).join('/');
          const isLast = index === segments.length - 1;
          const label = routeLabels[segment] || segment.replace(/-/g, ' ');

          return (
            <li key={href} className="flex items-center space-x-2">
              <span>/</span>
              {isLast ? (
                <span className="font-medium text-gray-900">{label}</span>
              ) : (
                <Link href={href} className="hover:text-gray-900">{label}</Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
```

```tsx
// For dynamic segments, use a Server Component approach:
// app/blog/[slug]/page.tsx
export default async function BlogPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(slug);

  return (
    <div>
      <nav className="text-sm mb-4">
        <Link href="/">Home</Link> / <Link href="/blog">Blog</Link> / <span>{post.title}</span>
      </nav>
      <h1>{post.title}</h1>
    </div>
  );
}
```

---

## Q10. (Intermediate) How do you create a multi-step form wizard with the App Router while preserving form state?

**Scenario**: A 3-step registration form: Personal Info → Company Info → Confirmation. The URL should reflect the step, but navigating back shouldn't lose data.

**Answer**:

```
app/register/
├── layout.tsx              ← Shared wizard layout with step indicator
├── page.tsx                → Redirect to step 1
├── step-1/
│   └── page.tsx            → Personal info form
├── step-2/
│   └── page.tsx            → Company info form
└── step-3/
    └── page.tsx            → Confirmation
```

```tsx
// app/register/layout.tsx
'use client';

import { usePathname } from 'next/navigation';
import { FormProvider, useFormContext } from './FormContext';

const steps = [
  { path: '/register/step-1', label: 'Personal' },
  { path: '/register/step-2', label: 'Company' },
  { path: '/register/step-3', label: 'Confirm' },
];

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const currentStep = steps.findIndex(s => s.path === pathname) + 1;

  return (
    <FormProvider>
      <div className="max-w-2xl mx-auto p-8">
        {/* Step indicator */}
        <div className="flex justify-between mb-8">
          {steps.map((step, i) => (
            <div key={step.path} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center
                ${i + 1 <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                {i + 1}
              </div>
              <span className="ml-2 text-sm">{step.label}</span>
            </div>
          ))}
        </div>

        {/* Form content changes per step, but layout (and state) persists */}
        {children}
      </div>
    </FormProvider>
  );
}
```

```tsx
// app/register/FormContext.tsx
'use client';

import { createContext, useContext, useState } from 'react';

interface FormData {
  name: string;
  email: string;
  company: string;
  role: string;
}

const FormContext = createContext<{
  data: FormData;
  updateData: (partial: Partial<FormData>) => void;
} | null>(null);

export function FormProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<FormData>({
    name: '', email: '', company: '', role: '',
  });

  const updateData = (partial: Partial<FormData>) => {
    setData(prev => ({ ...prev, ...partial }));
  };

  return (
    <FormContext.Provider value={{ data, updateData }}>
      {children}
    </FormContext.Provider>
  );
}

export const useFormData = () => {
  const ctx = useContext(FormContext);
  if (!ctx) throw new Error('useFormData must be used within FormProvider');
  return ctx;
};
```

```tsx
// app/register/step-1/page.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useFormData } from '../FormContext';

export default function Step1() {
  const { data, updateData } = useFormData();
  const router = useRouter();

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      router.push('/register/step-2');
    }}>
      <input
        value={data.name}
        onChange={e => updateData({ name: e.target.value })}
        placeholder="Full Name"
        className="w-full border p-2 rounded mb-4"
      />
      <input
        value={data.email}
        onChange={e => updateData({ email: e.target.value })}
        placeholder="Email"
        className="w-full border p-2 rounded mb-4"
      />
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
        Next
      </button>
    </form>
  );
}
```

**Why this works**: The layout (with FormProvider) persists across step navigations. The form state lives in the layout's context and survives route changes.

---

## Q11. (Intermediate) What are route segment config options, and how do you use them to control rendering behavior?

**Answer**:

Each route segment can export configuration that overrides default behavior:

```tsx
// app/blog/[slug]/page.tsx

// Force dynamic rendering (no caching)
export const dynamic = 'force-dynamic'; // or 'auto' | 'error' | 'force-static'

// Revalidation period (ISR)
export const revalidate = 3600; // seconds (0 = no cache, false = infinite)

// Runtime
export const runtime = 'edge'; // or 'nodejs' (default)

// Maximum duration for serverless function
export const maxDuration = 30; // seconds

// Enable/disable dynamic params
export const dynamicParams = true; // false = 404 for params not in generateStaticParams
```

```tsx
// Practical examples:

// 1. Static marketing page — never re-renders
// app/pricing/page.tsx
export const dynamic = 'force-static';
export const revalidate = false; // Cache forever (until next build)

export default function PricingPage() {
  return <div>Pricing content</div>;
}

// 2. Real-time dashboard — always fresh
// app/dashboard/live/page.tsx
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default async function LiveDashboard() {
  const data = await getRealtimeMetrics(); // Always fresh
  return <Dashboard data={data} />;
}

// 3. Blog post — revalidate every hour
// app/blog/[slug]/page.tsx
export const revalidate = 3600;

export default async function BlogPost({ params }: Props) {
  const { slug } = await params;
  const post = await getPost(slug);
  return <article>{/* ... */}</article>;
}

// 4. Edge-optimized API
// app/api/geo/route.ts
export const runtime = 'edge';

export async function GET(request: Request) {
  const country = request.headers.get('x-vercel-ip-country');
  return Response.json({ country });
}
```

---

## Q12. (Intermediate) How do you implement route-based code splitting in the App Router?

**Answer**:

Code splitting is **automatic** in the App Router — each route segment is its own chunk. But you can further optimize with dynamic imports:

```tsx
// Automatic code splitting:
// app/dashboard/page.tsx → dashboard-page-chunk.js
// app/settings/page.tsx  → settings-page-chunk.js
// These chunks are only loaded when the route is visited

// Manual code splitting for heavy components within a route:
import dynamic from 'next/dynamic';

const HeavyEditor = dynamic(
  () => import('@/components/RichTextEditor'),
  {
    loading: () => <div className="h-64 bg-gray-100 animate-pulse rounded" />,
    ssr: true, // Still server-render (default)
  }
);

const MapView = dynamic(
  () => import('@/components/MapView'),
  {
    ssr: false, // Skip server render (uses window/document)
    loading: () => <div className="h-96 bg-gray-100 animate-pulse rounded" />,
  }
);

export default function EditorPage() {
  return (
    <div>
      <HeavyEditor />  {/* Loaded asynchronously */}
      <MapView />       {/* Loaded only on client */}
    </div>
  );
}
```

```tsx
// Named exports with dynamic:
const Chart = dynamic(
  () => import('@/components/Charts').then(mod => mod.LineChart),
  { loading: () => <ChartSkeleton /> }
);
```

---

## Q13. (Advanced) Design a dashboard with conditional parallel routes where different user roles see different slots.

**Scenario**: Admin users see analytics + user management. Regular users see analytics + support tickets.

**Answer**:

```
app/dashboard/
├── layout.tsx
├── page.tsx
├── @analytics/           ← Shared slot
│   └── page.tsx
├── @admin/               ← Admin-only slot
│   ├── page.tsx
│   └── default.tsx
├── @support/             ← User-only slot
│   ├── page.tsx
│   └── default.tsx
```

```tsx
// app/dashboard/layout.tsx
import { getSession } from '@/lib/auth';

export default async function DashboardLayout({
  children,
  analytics,
  admin,
  support,
}: {
  children: React.ReactNode;
  analytics: React.ReactNode;
  admin: React.ReactNode;
  support: React.ReactNode;
}) {
  const session = await getSession();
  const isAdmin = session?.role === 'admin';

  return (
    <div className="p-6">
      <div className="mb-6">{children}</div>
      <div className="grid grid-cols-2 gap-6">
        <div>{analytics}</div>
        <div>
          {isAdmin ? admin : support}
        </div>
      </div>
    </div>
  );
}
```

```tsx
// app/dashboard/@admin/page.tsx
import { requireRole } from '@/lib/auth';

export default async function AdminPanel() {
  await requireRole('admin');

  const users = await getRecentUsers();
  return (
    <div className="border rounded p-4">
      <h2 className="text-lg font-bold mb-4">User Management</h2>
      <table>
        <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
        <tbody>
          {users.map(u => (
            <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td>{u.role}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// app/dashboard/@admin/default.tsx
export default function AdminDefault() {
  return null; // Hidden for non-admin routes
}
```

---

## Q14. (Advanced) How does middleware interact with routing in Next.js 15? Build a middleware that handles auth, geo-routing, and A/B testing.

**Answer**:

Middleware runs **before** any routing logic. It executes at the edge on every request.

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // === 1. AUTHENTICATION ===
  const protectedPaths = ['/dashboard', '/admin', '/api/protected'];
  const isProtected = protectedPaths.some(p => request.nextUrl.pathname.startsWith(p));

  if (isProtected) {
    const token = request.cookies.get('auth-token')?.value;
    if (!token) {
      const loginUrl = new URL('/login', request.url);
      loginUrl.searchParams.set('from', request.nextUrl.pathname);
      return NextResponse.redirect(loginUrl);
    }

    // Verify token at edge (lightweight check)
    try {
      const payload = decodeJWT(token); // Simple decode, no DB call
      if (payload.exp < Date.now() / 1000) {
        return NextResponse.redirect(new URL('/login', request.url));
      }
      // Pass user info to Server Components via headers
      response.headers.set('x-user-id', payload.sub);
      response.headers.set('x-user-role', payload.role);
    } catch {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  // === 2. GEO-ROUTING ===
  const country = request.geo?.country || 'US';
  const euCountries = ['DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PL'];

  if (request.nextUrl.pathname === '/' && euCountries.includes(country)) {
    // Show GDPR consent banner for EU users
    response.headers.set('x-show-gdpr', 'true');
  }

  // Geo-based pricing page
  if (request.nextUrl.pathname === '/pricing') {
    response.cookies.set('user-region', country);
  }

  // === 3. A/B TESTING ===
  if (!request.cookies.has('experiment-nav')) {
    const variant = Math.random() < 0.5 ? 'control' : 'variant';
    response.cookies.set('experiment-nav', variant, {
      maxAge: 60 * 60 * 24 * 30,
    });
  }

  // === 4. RATE LIMITING (simple) ===
  // Note: For production, use a proper rate limiter (Upstash, etc.)
  const ip = request.ip || 'unknown';
  response.headers.set('x-client-ip', ip);

  // === 5. SECURITY HEADERS ===
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  return response;
}

export const config = {
  matcher: [
    // Match all paths except static files and _next
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
```

**Performance warning**: Middleware runs on EVERY matched request. Keep it lightweight:
- No database calls (use edge-compatible auth like JWT decode)
- No heavy computation
- Use `matcher` to skip static assets

---

## Q15. (Advanced) Implement a type-safe routing system with Next.js 15 that catches route errors at compile time.

**Answer**:

```tsx
// lib/routes.ts — Type-safe route definitions
const routes = {
  home: '/',
  blog: '/blog',
  blogPost: (slug: string) => `/blog/${slug}` as const,
  dashboard: '/dashboard',
  dashboardAnalytics: '/dashboard/analytics',
  dashboardSettings: '/dashboard/settings',
  userProfile: (userId: string) => `/users/${userId}` as const,
  userProfileTab: (userId: string, tab: 'posts' | 'comments' | 'likes') =>
    `/users/${userId}/${tab}` as const,
  search: (params: { q: string; page?: number }) => {
    const searchParams = new URLSearchParams();
    searchParams.set('q', params.q);
    if (params.page) searchParams.set('page', String(params.page));
    return `/search?${searchParams.toString()}`;
  },
} as const;

export type AppRoutes = typeof routes;

// Type-safe link component
import Link from 'next/link';
import { ComponentProps } from 'react';

type AppLinkProps = Omit<ComponentProps<typeof Link>, 'href'> & {
  href: ReturnType<AppRoutes[keyof AppRoutes]> extends (...args: any) => infer R
    ? R : AppRoutes[keyof AppRoutes];
};

export function AppLink({ href, ...props }: AppLinkProps) {
  return <Link href={href} {...props} />;
}
```

```tsx
// Usage in components:
import { routes, AppLink } from '@/lib/routes';

export default function Navigation() {
  return (
    <nav>
      <AppLink href={routes.home}>Home</AppLink>
      <AppLink href={routes.blog}>Blog</AppLink>
      <AppLink href={routes.blogPost('hello-world')}>My Post</AppLink>
      <AppLink href={routes.userProfileTab('123', 'posts')}>User Posts</AppLink>

      {/* ❌ TypeScript error: Argument of type '"invalid"' is not assignable */}
      {/* <AppLink href={routes.userProfileTab('123', 'invalid')}>Error!</AppLink> */}
    </nav>
  );
}
```

---

## Q16. (Advanced) How do you handle complex redirects during a large-scale URL migration?

**Answer**:

```tsx
// next.config.js — Static redirects (evaluated at build time)
module.exports = {
  async redirects() {
    return [
      // Simple redirect
      {
        source: '/old-blog/:slug',
        destination: '/blog/:slug',
        permanent: true, // 308
      },
      // Regex redirect
      {
        source: '/docs/v1/:path*',
        destination: '/docs/v2/:path*',
        permanent: true,
      },
      // Conditional redirect (based on header, cookie, query)
      {
        source: '/features',
        has: [
          { type: 'query', key: 'ref', value: 'partner' },
        ],
        destination: '/partner-features',
        permanent: false,
      },
    ];
  },
};
```

```tsx
// For 1000+ redirects, use middleware with a map:
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Generate this from your CMS or a database export
const redirectMap: Record<string, { destination: string; permanent: boolean }> = {
  '/old-page-1': { destination: '/new-page-1', permanent: true },
  '/old-page-2': { destination: '/new-page-2', permanent: true },
  // ... thousands of entries
};

export function middleware(request: NextRequest) {
  const redirect = redirectMap[request.nextUrl.pathname];

  if (redirect) {
    return NextResponse.redirect(
      new URL(redirect.destination, request.url),
      redirect.permanent ? 308 : 307
    );
  }

  return NextResponse.next();
}
```

```tsx
// For dynamic redirects (slug changes in CMS):
// app/[...slug]/page.tsx
import { redirect, permanentRedirect } from 'next/navigation';

export default async function CatchAllPage({ params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  const path = '/' + slug.join('/');

  // Check if this URL was redirected
  const redirectEntry = await db.redirect.findUnique({ where: { fromPath: path } });
  if (redirectEntry) {
    if (redirectEntry.permanent) {
      permanentRedirect(redirectEntry.toPath);
    } else {
      redirect(redirectEntry.toPath);
    }
  }

  // Normal page rendering
  const page = await getPageByPath(path);
  if (!page) notFound();
  return <PageRenderer page={page} />;
}
```

---

## Q17. (Advanced) What are the edge cases and gotchas with the `back/forward` cache in the App Router?

**Answer**:

The App Router maintains a **client-side Router Cache** (also called Back/Forward cache or bfcache) that stores RSC payloads for visited routes.

**Next.js 15 cache behavior**:

```
Static Routes:   Cached for 5 minutes (prefetch: auto)
Dynamic Routes:  NOT cached by default (was 30s in Next 14)
Prefetch (full): Cached for 5 minutes
Prefetch (partial): Cached for 30 seconds
```

**Gotchas**:

```tsx
// Gotcha 1: Stale data after mutation
// User updates their profile, navigates away, then comes back
// The Router Cache shows stale data!

// Fix: Invalidate after mutation
'use server';
import { revalidatePath } from 'next/cache';

export async function updateProfile(data: FormData) {
  await db.user.update({ /* ... */ });
  revalidatePath('/profile');      // Invalidates server cache
  // router.refresh() on client invalidates client Router Cache
}
```

```tsx
// Gotcha 2: Shared layout shows stale user data
// Layout fetches user at first render, then caches
// If user logs out and logs in as a different user,
// layout might show old user's data

// Fix: Use router.refresh() after auth changes
'use client';
export function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.refresh(); // Force all Server Components to re-render
    router.push('/login');
  }

  return <button onClick={handleLogout}>Logout</button>;
}
```

```tsx
// Gotcha 3: Time-sensitive data looks stale on back navigation
// User views a stock price page, navigates away, comes back
// They see the cached (old) price

// Fix: Set staleTimes in next.config.js (Next.js 15)
module.exports = {
  experimental: {
    staleTimes: {
      dynamic: 0,    // Don't cache dynamic pages in Router Cache
      static: 180,   // Cache static pages for 3 minutes
    },
  },
};
```

---

## Q18. (Advanced) How do you implement URL-based state management (filters, sorting) that works with Server Components?

**Scenario**: A product listing page with filters in the URL: `/products?category=shoes&sort=price&page=2`.

**Answer**:

```tsx
// app/products/page.tsx — Server Component reads searchParams
interface ProductsPageProps {
  searchParams: Promise<{
    category?: string;
    sort?: 'price' | 'name' | 'rating';
    order?: 'asc' | 'desc';
    page?: string;
    q?: string;
  }>;
}

export default async function ProductsPage({ searchParams }: ProductsPageProps) {
  const params = await searchParams;
  const {
    category,
    sort = 'name',
    order = 'asc',
    page = '1',
    q,
  } = params;

  const products = await db.product.findMany({
    where: {
      ...(category && { category }),
      ...(q && { name: { contains: q, mode: 'insensitive' } }),
    },
    orderBy: { [sort]: order },
    skip: (parseInt(page) - 1) * 20,
    take: 20,
  });

  const total = await db.product.count({
    where: { ...(category && { category }), ...(q && { name: { contains: q } }) },
  });

  return (
    <div>
      <FilterBar currentParams={params} />
      <ProductGrid products={products} />
      <Pagination currentPage={parseInt(page)} total={total} pageSize={20} />
    </div>
  );
}
```

```tsx
// components/FilterBar.tsx — Client Component updates URL
'use client';

import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useCallback } from 'react';

export function FilterBar({ currentParams }: { currentParams: Record<string, string | undefined> }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const updateFilter = useCallback((key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.set('page', '1'); // Reset to page 1 on filter change
    router.push(`${pathname}?${params.toString()}`);
  }, [router, pathname, searchParams]);

  return (
    <div className="flex gap-4 mb-6">
      <select
        value={currentParams.category || ''}
        onChange={e => updateFilter('category', e.target.value || null)}
        className="border rounded p-2"
      >
        <option value="">All Categories</option>
        <option value="shoes">Shoes</option>
        <option value="clothing">Clothing</option>
        <option value="accessories">Accessories</option>
      </select>

      <select
        value={currentParams.sort || 'name'}
        onChange={e => updateFilter('sort', e.target.value)}
        className="border rounded p-2"
      >
        <option value="name">Name</option>
        <option value="price">Price</option>
        <option value="rating">Rating</option>
      </select>

      <input
        type="search"
        placeholder="Search..."
        defaultValue={currentParams.q || ''}
        onChange={e => {
          // Debounce search
          clearTimeout((window as any).__searchTimeout);
          (window as any).__searchTimeout = setTimeout(() => {
            updateFilter('q', e.target.value || null);
          }, 300);
        }}
        className="border rounded p-2"
      />
    </div>
  );
}
```

**Benefits of URL-based state**:
- Shareable links (copy URL = share filters)
- Browser back/forward works
- SEO-friendly (each filter combination is indexable)
- Server-side filtering (no waterfall)
- No client-side state management needed

---

## Q19. (Advanced) How do you handle route transitions and animations in the App Router?

**Answer**:

```tsx
// Method 1: CSS transitions with template.tsx
// app/dashboard/template.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { usePathname } from 'next/navigation';

export default function DashboardTemplate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```

```tsx
// Method 2: View Transitions API (modern browsers)
// app/layout.tsx
'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';

function TransitionLink({ href, children }: { href: string; children: React.ReactNode }) {
  const router = useRouter();

  function handleClick(e: React.MouseEvent) {
    e.preventDefault();

    if (document.startViewTransition) {
      document.startViewTransition(() => {
        router.push(href);
      });
    } else {
      router.push(href);
    }
  }

  return <a href={href} onClick={handleClick}>{children}</a>;
}
```

```css
/* globals.css — View Transition styles */
::view-transition-old(root) {
  animation: fade-out 0.2s ease-in;
}

::view-transition-new(root) {
  animation: fade-in 0.2s ease-out;
}

@keyframes fade-out {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

```tsx
// Method 3: useTransition for non-blocking navigations
'use client';

import { useTransition } from 'react';
import { useRouter } from 'next/navigation';

export function NavigationItem({ href, label }: { href: string; label: string }) {
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  return (
    <button
      onClick={() => {
        startTransition(() => {
          router.push(href);
        });
      }}
      className={isPending ? 'opacity-50' : ''}
    >
      {label}
      {isPending && <span className="ml-2 animate-spin">⏳</span>}
    </button>
  );
}
```

---

## Q20. (Advanced) Design a Next.js routing architecture for a SaaS application with workspace isolation, role-based routing, and feature flags.

**Answer**:

```
app/
├── (public)/                   ← Marketing (no auth)
│   ├── layout.tsx
│   ├── page.tsx               → /
│   ├── pricing/page.tsx       → /pricing
│   └── blog/[slug]/page.tsx   → /blog/:slug
│
├── (auth)/                     ← Auth flows
│   ├── layout.tsx
│   ├── login/page.tsx         → /login
│   └── register/page.tsx      → /register
│
├── (app)/                      ← Authenticated app
│   ├── layout.tsx             ← Auth check + workspace loader
│   ├── [workspaceId]/         ← Workspace-scoped routes
│   │   ├── layout.tsx         ← Workspace layout + RBAC
│   │   ├── page.tsx           → /:workspaceId (dashboard)
│   │   ├── @sidebar/
│   │   │   └── default.tsx
│   │   ├── projects/
│   │   │   ├── page.tsx       → /:workspaceId/projects
│   │   │   └── [projectId]/
│   │   │       └── page.tsx   → /:workspaceId/projects/:projectId
│   │   ├── settings/          ← Admin only
│   │   │   └── page.tsx
│   │   └── billing/           ← Owner only
│   │       └── page.tsx
│   └── onboarding/
│       └── page.tsx           → /onboarding
```

```tsx
// app/(app)/layout.tsx — Auth + workspace initialization
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect('/login');

  // Check if user needs onboarding
  if (!session.onboardingComplete) redirect('/onboarding');

  return children;
}
```

```tsx
// app/(app)/[workspaceId]/layout.tsx — Workspace RBAC
import { notFound, redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';
import { getWorkspace, getMembership } from '@/lib/workspace';
import { WorkspaceProvider } from '@/providers/WorkspaceProvider';
import { FeatureFlagProvider } from '@/providers/FeatureFlags';

export default async function WorkspaceLayout({
  children,
  sidebar,
  params,
}: {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  const session = await getSession();

  const [workspace, membership] = await Promise.all([
    getWorkspace(workspaceId),
    getMembership(workspaceId, session!.userId),
  ]);

  if (!workspace) notFound();
  if (!membership) redirect('/');

  // Load feature flags for this workspace
  const flags = await getFeatureFlags(workspace.plan);

  return (
    <WorkspaceProvider workspace={workspace} membership={membership}>
      <FeatureFlagProvider flags={flags}>
        <div className="flex h-screen">
          {sidebar}
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </FeatureFlagProvider>
    </WorkspaceProvider>
  );
}
```

```tsx
// app/(app)/[workspaceId]/settings/page.tsx — Admin-only route
import { requireWorkspaceRole } from '@/lib/workspace';

export default async function SettingsPage({ params }: { params: Promise<{ workspaceId: string }> }) {
  const { workspaceId } = await params;
  await requireWorkspaceRole(workspaceId, 'admin'); // Redirects if not admin

  return <SettingsForm workspaceId={workspaceId} />;
}
```

```tsx
// Feature flag gating within routes
// app/(app)/[workspaceId]/projects/[projectId]/page.tsx
import { getFeatureFlags } from '@/lib/features';

export default async function ProjectPage({ params }: Props) {
  const { workspaceId, projectId } = await params;
  const flags = await getFeatureFlags(workspaceId);

  return (
    <div>
      <ProjectDetails projectId={projectId} />

      {flags.aiAssistant && (
        <Suspense fallback={<AISkeleton />}>
          <AIAssistantPanel projectId={projectId} />
        </Suspense>
      )}

      {flags.advancedAnalytics && (
        <Suspense fallback={<AnalyticsSkeleton />}>
          <AdvancedAnalytics projectId={projectId} />
        </Suspense>
      )}
    </div>
  );
}
```

This architecture provides:
- **URL-based workspace isolation**: Each workspace has its own URL namespace
- **Layout-level RBAC**: Membership is checked once in the layout, not in every page
- **Feature flag integration**: Flags are loaded per workspace/plan and available to all children
- **Parallel routes**: Sidebar is an independent slot that can update independently
