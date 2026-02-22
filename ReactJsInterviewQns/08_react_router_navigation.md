# Topic 8: React Router & Navigation in React 18

## Introduction

Routing is the mechanism that maps a URL to a specific view or component in your application. In traditional **server-side routing**, every navigation triggers a full HTTP request to the server, which responds with an entirely new HTML document — the browser reloads, the JavaScript re-initializes, and the user experiences a visible flash. **Client-side routing**, the paradigm that React applications embrace, intercepts these navigations in the browser using the History API (`pushState`, `replaceState`, `popstate`), swaps out the appropriate component tree, and updates the URL — all without a full page reload. This produces the fast, seamless transitions that define modern single-page applications (SPAs). React Router is the de facto standard library for client-side routing in React, and its v6 release (including the v6.4+ data APIs) represents a major architectural evolution: declarative route definitions, relative paths by default, a powerful nested routing model with `<Outlet>`, built-in data loading via loaders and actions, and first-class hooks (`useNavigate`, `useParams`, `useSearchParams`, `useLoaderData`) that make every routing concern composable and testable.

In a production React 18 application, routing is far more than mapping paths to components. It encompasses **authentication guards** that redirect unauthorized users, **role-based layouts** that show different navigation chrome to admins versus customers, **code splitting** via `React.lazy` so users only download the JavaScript for the routes they visit, **scroll restoration** so navigating back feels native, **URL-driven state** where filters, pagination tokens, and sort orders live in query parameters rather than ephemeral component state, and **error boundaries** scoped to route segments so a crash in one section of the app doesn't take down the entire page. React Router v6.4+ introduced the **data router** pattern (inspired by Remix) which allows you to define `loader` and `action` functions directly on routes — these run before the component renders, enabling parallel data fetching, optimistic UI updates, and a clear separation between "fetch data" and "render UI." Understanding this full spectrum — from basic `<Route>` definitions to production-grade architectures — is essential for any React interview.

Here is a foundational illustration showing how a typical React Router v6 application is wired up, including nested routes, a layout, and a protected route:

```jsx
import { createBrowserRouter, RouterProvider, Outlet, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';

// Lazy-loaded pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
const Login = lazy(() => import('./pages/Login'));

// Auth guard component
function ProtectedRoute({ children }) {
  const isAuthenticated = useAuth(); // custom hook
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

// Shared layout with navigation and an Outlet for child routes
function AppLayout() {
  return (
    <div className="app">
      <nav>
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/settings">Settings</NavLink>
      </nav>
      <main>
        <Suspense fallback={<div className="spinner" />}>
          <Outlet />
        </Suspense>
      </main>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
  { path: '/login', element: <Login /> },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
```

This snippet ties together lazy-loaded pages, an authentication guard, a shared layout with `<Outlet>`, and the data router API (`createBrowserRouter` + `RouterProvider`). Every question below builds on and deepens these patterns.

---

## Beginner Level (Q1–Q5)

---

### Q1. What is the difference between client-side routing and server-side routing, and why do React applications use client-side routing?

**Answer:**

**Server-side routing** means the browser sends a request to the server for every URL change. The server processes the request, generates a full HTML page, and sends it back. The browser then throws away the current page, parses the new HTML, downloads scripts and styles, and renders from scratch. This results in full-page reloads, a white flash between pages, and lost client-side state (form inputs, scroll positions, open modals).

**Client-side routing** keeps the application running in the browser as a single page. When the user clicks a link, JavaScript intercepts the click, uses the History API (`window.history.pushState`) to update the URL bar without triggering a server request, and swaps only the portion of the component tree that corresponds to the new route. The shell (header, sidebar, footer) stays mounted, in-memory state is preserved, and transitions feel instantaneous because no network round-trip is needed for the page chrome.

React applications use client-side routing because:
1. **Speed** — No full page reloads; only the relevant components re-render.
2. **State preservation** — Global state (Redux, Context, auth tokens) survives navigation.
3. **Transitions** — You can animate route changes, show loading skeletons, or stream in content.
4. **Offline capability** — Combined with a service worker, previously visited routes can be served from cache.

```jsx
// Server-side routing equivalent (traditional HTML)
// Every <a> tag causes a full reload
<a href="/about">About</a>

// Client-side routing with React Router v6
// Intercepts the click, pushes to history, no reload
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav>
      {/* No page reload — React Router handles it in JS */}
      <Link to="/about">About</Link>
      <Link to="/dashboard">Dashboard</Link>
    </nav>
  );
}
```

**Key nuance for interviews:** Client-side routing has a trade-off — the initial bundle is larger because you're shipping the entire application (mitigated by code-splitting), and you need server-side configuration to return `index.html` for all routes (the "catch-all" rule) so that deep-linking and refreshes work. In contrast, server-side routing naturally supports deep links but sacrifices interactivity.

---

### Q2. How do you set up basic routing in a React 18 application using React Router v6's `BrowserRouter`, `Routes`, and `Route`?

**Answer:**

React Router v6 provides two approaches for setting up routing:

1. **JSX-based** (`BrowserRouter` + `Routes` + `Route`) — familiar and inline.
2. **Data router** (`createBrowserRouter` + `RouterProvider`) — the newer pattern that enables loaders, actions, and error boundaries. This is the recommended approach for new projects.

Here is the JSX-based approach, which is the simplest starting point:

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import NotFound from './pages/NotFound';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Exact match by default in v6 — no need for "exact" prop */}
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/:productId" element={<ProductDetail />} />
        {/* Catch-all for 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

And here is the same setup using the data router API (recommended for v6.4+):

```jsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import NotFound from './pages/NotFound';

const router = createBrowserRouter([
  { path: '/', element: <Home /> },
  { path: '/about', element: <About /> },
  { path: '/products', element: <Products /> },
  { path: '/products/:productId', element: <ProductDetail /> },
  { path: '*', element: <NotFound /> },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
```

Key differences from React Router v5:
- **No `<Switch>`** — it was replaced by `<Routes>`, which picks the best match automatically.
- **No `exact` prop** — every route matches exactly by default in v6. Use a trailing `/*` if you want prefix matching.
- **`element` prop** — you pass a JSX element (`element={<Home />}`) instead of `component={Home}` or `render={() => ...}`.
- **Relative paths** — child routes are relative to the parent by default, removing the need for `path={`${match.url}/details`}`.

---

### Q3. What are `Link` and `NavLink` in React Router, and how do they differ from a regular `<a>` tag?

**Answer:**

`<Link>` is React Router's replacement for the HTML `<a>` tag. When clicked, it calls `history.pushState` under the hood instead of triggering a full page navigation. This means no HTTP request is made for a new document — React Router simply re-renders the matched route component.

`<NavLink>` is a specialized version of `<Link>` that knows whether it is "active" — i.e., whether its `to` path matches the current URL. It automatically applies an `active` class (or a custom class/style) to the rendered `<a>` tag when active. This is essential for navigation menus where you want to visually highlight the current page.

```jsx
import { Link, NavLink } from 'react-router-dom';

function Navigation() {
  return (
    <nav className="sidebar">
      {/* Basic Link — no active styling */}
      <Link to="/">Home</Link>

      {/* NavLink — automatically gets className "active" when URL matches */}
      <NavLink
        to="/dashboard"
        className={({ isActive, isPending }) =>
          isActive ? 'nav-link active' : isPending ? 'nav-link pending' : 'nav-link'
        }
      >
        Dashboard
      </NavLink>

      {/* NavLink with inline style */}
      <NavLink
        to="/settings"
        style={({ isActive }) => ({
          fontWeight: isActive ? 'bold' : 'normal',
          color: isActive ? '#4f46e5' : '#6b7280',
        })}
      >
        Settings
      </NavLink>

      {/* NavLink with "end" prop — only active on exact match */}
      {/* Without "end", NavLink to="/" would be active for every route */}
      <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
        Home
      </NavLink>

      {/* Contrast with a plain <a> — this causes a FULL page reload */}
      <a href="/external-page">External Page</a>
    </nav>
  );
}
```

**Important details:**
- Use `<Link>` for generic internal navigation (cards, buttons, lists).
- Use `<NavLink>` specifically in navigation menus where active indication matters.
- Use a regular `<a>` tag only for external links or when you intentionally want a full reload.
- The `end` prop on `<NavLink>` ensures it only matches exactly (prevents `/` from being active on `/dashboard`).
- In v6.4+, `NavLink` also provides `isPending` for pending navigations when using data routers.

---

### Q4. How do you read URL parameters using `useParams` and query strings using `useSearchParams`?

**Answer:**

React Router v6 provides two hooks for extracting data from the URL:

1. **`useParams()`** — reads dynamic segments defined in the route path (e.g., `:productId` in `/products/:productId`). Returns a plain object where keys are the parameter names.

2. **`useSearchParams()`** — reads and writes the query string (`?key=value&...`). Returns a tuple `[searchParams, setSearchParams]` where `searchParams` is a `URLSearchParams` instance.

```jsx
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

// Route definition: <Route path="/products/:category/:productId" element={<ProductPage />} />
// Example URL: /products/electronics/42?color=blue&size=large

function ProductPage() {
  const { category, productId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [product, setProduct] = useState(null);

  // Read query parameters
  const color = searchParams.get('color');      // "blue"
  const size = searchParams.get('size');         // "large"

  useEffect(() => {
    fetch(`/api/products/${category}/${productId}?color=${color}`)
      .then((res) => res.json())
      .then(setProduct);
  }, [category, productId, color]);

  // Update query string without full navigation
  const handleColorChange = (newColor) => {
    setSearchParams((prev) => {
      prev.set('color', newColor);
      return prev;
    });
  };

  return (
    <div>
      <h1>Category: {category}</h1>
      <h2>Product ID: {productId}</h2>
      <p>Selected color: {color}</p>
      <p>Selected size: {size}</p>

      <div className="color-picker">
        {['red', 'blue', 'green'].map((c) => (
          <button
            key={c}
            onClick={() => handleColorChange(c)}
            className={c === color ? 'selected' : ''}
          >
            {c}
          </button>
        ))}
      </div>

      {product && <ProductCard data={product} />}
    </div>
  );
}
```

**Key distinctions:**
| Aspect | `useParams` | `useSearchParams` |
|---|---|---|
| Source | Path segments (`:id`) | Query string (`?key=val`) |
| Mutability | Read-only (change via navigation) | Read/write (`setSearchParams`) |
| Type | Plain object `{ key: string }` | `URLSearchParams` API |
| Use case | Identifying a resource | Filters, sort, pagination |

**Gotcha:** `useParams` values are always strings. If your route is `/products/:id` and the URL is `/products/42`, `id` is the string `"42"`, not the number `42`. Always parse as needed: `Number(productId)`.

---

### Q5. What are nested routes and how does `<Outlet>` work in React Router v6?

**Answer:**

Nested routes allow you to define a parent route that renders a shared layout (e.g., a sidebar, header, or tab bar) and delegate a portion of the page to **child routes** via the `<Outlet>` component. `<Outlet>` is essentially a placeholder: React Router inspects the current URL, finds the matching child route, and renders its element in place of `<Outlet>`.

This is a fundamental architectural pattern: your application is a tree of layouts, and each layout renders its children through an outlet.

```jsx
import { createBrowserRouter, RouterProvider, Outlet, NavLink } from 'react-router-dom';

// Shared layout for the dashboard section
function DashboardLayout() {
  return (
    <div className="dashboard">
      <aside className="sidebar">
        <NavLink to="/dashboard" end>Overview</NavLink>
        <NavLink to="/dashboard/analytics">Analytics</NavLink>
        <NavLink to="/dashboard/reports">Reports</NavLink>
      </aside>
      <section className="content">
        {/* Child route component renders here */}
        <Outlet />
      </section>
    </div>
  );
}

function Overview() {
  return <h2>Dashboard Overview</h2>;
}

function Analytics() {
  return <h2>Analytics Page</h2>;
}

function Reports() {
  return <h2>Reports Page</h2>;
}

const router = createBrowserRouter([
  {
    path: '/dashboard',
    element: <DashboardLayout />,
    children: [
      { index: true, element: <Overview /> },       // matches /dashboard
      { path: 'analytics', element: <Analytics /> }, // matches /dashboard/analytics
      { path: 'reports', element: <Reports /> },     // matches /dashboard/reports
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}
```

**How it works step by step:**
1. User navigates to `/dashboard/analytics`.
2. React Router matches the parent route `/dashboard` → renders `<DashboardLayout>`.
3. Inside `<DashboardLayout>`, it encounters `<Outlet>`.
4. It matches the child route `analytics` → renders `<Analytics>` inside the outlet.
5. The sidebar stays mounted; only the `<Outlet>` content swaps.

**The `index` route:** When the user is at `/dashboard` exactly (no further segments), the `index: true` child matches. This is the default content shown in the outlet.

**Nested outlets can go multiple levels deep.** A child route can itself be a layout with its own `<Outlet>`, enabling deeply nested UI hierarchies (e.g., `/dashboard/reports/:reportId/details`).

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you navigate programmatically using `useNavigate`, and when should you use it instead of `<Link>`?

**Answer:**

`useNavigate` returns a function that lets you trigger navigation from event handlers, effects, or any imperative code — situations where a declarative `<Link>` isn't appropriate (e.g., after a form submission, after a timeout, or in response to a WebSocket event).

```jsx
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

function CreateOrderPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    const formData = new FormData(e.currentTarget);

    try {
      const response = await fetch('/api/orders', {
        method: 'POST',
        body: formData,
      });
      const order = await response.json();

      // Navigate to the new order's page after successful creation
      navigate(`/orders/${order.id}`, {
        replace: true,  // replace current history entry so "Back" skips the form
        state: { fromCreate: true }, // pass transient state (not in URL)
      });
    } catch (error) {
      setIsSubmitting(false);
      // stay on page, show error
    }
  };

  // Go back (equivalent to browser back button)
  const handleCancel = () => {
    navigate(-1); // negative number = go back N entries
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="product" placeholder="Product name" required />
      <input name="quantity" type="number" placeholder="Qty" required />
      <div className="actions">
        <button type="button" onClick={handleCancel}>Cancel</button>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating…' : 'Create Order'}
        </button>
      </div>
    </form>
  );
}
```

**When to use `useNavigate` vs `<Link>`:**

| Scenario | Use |
|---|---|
| Clickable text/button in JSX | `<Link>` or `<NavLink>` |
| After async operation (form submit, API call) | `useNavigate` |
| Redirect based on condition (inside `useEffect`) | `useNavigate` or `<Navigate>` |
| Going back/forward in history | `useNavigate(-1)` / `useNavigate(1)` |
| Passing transient state to next page | `navigate(path, { state })` |

**The `replace` option** is critical in production: after creating a resource or logging in, you typically `replace: true` so the user can't press "Back" and re-submit the form or land on a stale login page.

**Reading navigation state** on the receiving end:

```jsx
import { useLocation } from 'react-router-dom';

function OrderDetailPage() {
  const location = useLocation();
  const fromCreate = location.state?.fromCreate;

  return (
    <div>
      {fromCreate && <div className="toast success">Order created successfully!</div>}
      {/* ... order details ... */}
    </div>
  );
}
```

---

### Q7. How do you implement protected (private) routes with authentication guards in React Router v6?

**Answer:**

A protected route is a route that should only be accessible to authenticated (or authorized) users. If the user is not authenticated, they are redirected to a login page — typically with the intended destination preserved so they can be sent there after login. In React Router v6, the idiomatic approach is a wrapper component that checks auth status and either renders children or redirects.

```jsx
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth'; // your auth context hook

// General auth guard — protects any nested routes
function RequireAuth({ allowedRoles }) {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  // Not logged in → redirect to login with return URL
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Logged in but doesn't have the required role
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Authorized → render child routes
  return <Outlet />;
}

// Usage in route configuration
import { createBrowserRouter } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AdminPanel from './pages/AdminPanel';
import Login from './pages/Login';
import Unauthorized from './pages/Unauthorized';

const router = createBrowserRouter([
  // Public routes
  { path: '/login', element: <Login /> },
  { path: '/unauthorized', element: <Unauthorized /> },

  // Protected routes — any authenticated user
  {
    element: <RequireAuth />,
    children: [
      { path: '/dashboard', element: <Dashboard /> },
      { path: '/profile', element: <Profile /> },
    ],
  },

  // Admin-only routes
  {
    element: <RequireAuth allowedRoles={['admin']} />,
    children: [
      { path: '/admin', element: <AdminPanel /> },
      { path: '/admin/users', element: <UserManagement /> },
    ],
  },
]);
```

**Completing the loop — redirect back after login:**

```jsx
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Where should we go after successful login?
  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    await login(formData.get('email'), formData.get('password'));
    navigate(from, { replace: true }); // go to the page they originally wanted
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" placeholder="Email" required />
      <input name="password" type="password" placeholder="Password" required />
      <button type="submit">Sign In</button>
    </form>
  );
}
```

**Production tips:**
- Use a **layout route** (a route with no `path` but with an `element`) for grouping protected routes — this avoids repeating the guard on every route.
- Store auth state in a React Context backed by a token in `httpOnly` cookies or `localStorage`.
- For SSR frameworks (Next.js, Remix), auth checks often happen in server-side loaders/middleware instead of client-side guards.

---

### Q8. How do you lazy-load route components with `React.lazy` and `Suspense` for code splitting?

**Answer:**

In a production app, shipping all route components in a single bundle means users download JavaScript for pages they may never visit. **Code splitting** at the route level is the most impactful optimization: each route becomes a separate chunk that is loaded on demand when the user navigates to it.

React provides `React.lazy()` for dynamic imports and `<Suspense>` for showing a fallback while the chunk loads. React Router v6 works seamlessly with both.

```jsx
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';
import { lazy, Suspense } from 'react';

// Each of these becomes a separate webpack/vite chunk
const Home = lazy(() => import('./pages/Home'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
const Analytics = lazy(() => import('./pages/Analytics'));
const UserProfile = lazy(() => import('./pages/UserProfile'));

// Reusable loading fallback
function PageLoader() {
  return (
    <div className="page-loader">
      <div className="spinner" />
      <p>Loading page…</p>
    </div>
  );
}

// Wrapper that provides Suspense boundary
function SuspenseLayout() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Outlet />
    </Suspense>
  );
}

const router = createBrowserRouter([
  {
    element: <SuspenseLayout />,
    children: [
      { path: '/', element: <Home /> },
      { path: '/dashboard', element: <Dashboard /> },
      { path: '/settings', element: <Settings /> },
      { path: '/analytics', element: <Analytics /> },
      { path: '/users/:userId', element: <UserProfile /> },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}
```

**Prefetching for better UX:**

You can preload a route's chunk before the user navigates — for example, on hover over a link:

```jsx
import { Link } from 'react-router-dom';

// Keep a reference to the import function
const importDashboard = () => import('./pages/Dashboard');

function Navbar() {
  return (
    <nav>
      <Link
        to="/dashboard"
        onMouseEnter={() => importDashboard()} // triggers chunk download on hover
        onFocus={() => importDashboard()}
      >
        Dashboard
      </Link>
    </nav>
  );
}
```

**Production considerations:**
- Place the `<Suspense>` boundary at the layout level (as shown) so that the shell (nav, sidebar) remains visible while the page content loads.
- Use **named chunk comments** for debugging: `lazy(() => import(/* webpackChunkName: "dashboard" */ './pages/Dashboard'))`.
- With Vite, chunks are automatically named based on the file path.
- Combine with **route-level error boundaries** so if a chunk fails to load (network error), you can show a retry button instead of a blank page.

---

### Q9. How do you handle 404 pages and route-level error handling in React Router v6?

**Answer:**

React Router v6 provides two complementary mechanisms for error handling:

1. **Catch-all route (`path="*"`)** — matches any URL that no other route matches. This is your 404 page.
2. **`errorElement`** — a data-router feature (v6.4+) that catches errors thrown in loaders, actions, or component rendering, similar to React error boundaries but scoped to the route tree.

```jsx
import { createBrowserRouter, RouterProvider, useRouteError, isRouteErrorResponse } from 'react-router-dom';

// Custom error boundary component for routes
function RouteErrorBoundary() {
  const error = useRouteError();

  // React Router throws a Response for 404s and other HTTP-like errors
  if (isRouteErrorResponse(error)) {
    return (
      <div className="error-page">
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
        {error.status === 404 && (
          <p>The page you're looking for doesn't exist.</p>
        )}
        <Link to="/">Go Home</Link>
      </div>
    );
  }

  // Unexpected errors (thrown in loaders, actions, or rendering)
  return (
    <div className="error-page">
      <h1>Something went wrong</h1>
      <p>{error?.message || 'An unexpected error occurred'}</p>
      <button onClick={() => window.location.reload()}>Reload Page</button>
    </div>
  );
}

// 404 page for unknown routes
function NotFound() {
  return (
    <div className="not-found">
      <h1>404 — Page Not Found</h1>
      <p>We couldn't find what you were looking for.</p>
      <Link to="/">Back to Home</Link>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <RouteErrorBoundary />,  // catches errors in this subtree
    children: [
      { index: true, element: <Home /> },
      {
        path: 'products/:id',
        element: <ProductDetail />,
        // Loader that might throw
        loader: async ({ params }) => {
          const res = await fetch(`/api/products/${params.id}`);
          if (!res.ok) {
            throw new Response('Product not found', { status: 404 });
          }
          return res.json();
        },
        errorElement: <RouteErrorBoundary />,  // scoped error handling
      },
    ],
  },
  // Catch-all 404 for completely unmatched routes
  { path: '*', element: <NotFound /> },
]);
```

**Error bubbling:** If a child route does not have its own `errorElement`, the error bubbles up to the nearest ancestor that does — exactly like React error boundaries. This lets you set a root-level `errorElement` as a catch-all and add more specific ones where needed.

**Production pattern — retry on chunk load failure:**

```jsx
function ChunkErrorBoundary() {
  const error = useRouteError();

  const isChunkError =
    error?.name === 'ChunkLoadError' ||
    error?.message?.includes('Failed to fetch dynamically imported module');

  if (isChunkError) {
    return (
      <div className="error-page">
        <h1>Loading Error</h1>
        <p>A new version of the app may be available.</p>
        <button onClick={() => window.location.reload()}>Reload</button>
      </div>
    );
  }

  return <GenericErrorPage error={error} />;
}
```

---

### Q10. What are route loaders and actions in React Router v6.4+, and how do they change the data-fetching pattern?

**Answer:**

React Router v6.4 introduced the **data router** API (inspired by Remix) which brings two new route-level functions:

- **`loader`** — runs *before* the route component renders. It fetches data and makes it available via the `useLoaderData()` hook. Multiple sibling loaders run **in parallel**, eliminating request waterfalls.
- **`action`** — runs when a form is submitted (via `<Form>` or `useSubmit`). It handles mutations (POST, PUT, DELETE) and React Router automatically revalidates all active loaders after the action completes.

This pattern separates data fetching from rendering — your components become pure UI, and data concerns live in the route definition.

```jsx
import {
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  useActionData,
  useNavigation,
  Form,
  redirect,
} from 'react-router-dom';

// LOADER — fetches data before render
async function projectsLoader() {
  const res = await fetch('/api/projects');
  if (!res.ok) throw new Response('Failed to load projects', { status: res.status });
  return res.json(); // this becomes the data returned by useLoaderData()
}

// ACTION — handles form mutations
async function createProjectAction({ request }) {
  const formData = await request.formData();
  const name = formData.get('name');
  const description = formData.get('description');

  const res = await fetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });

  if (!res.ok) {
    const error = await res.json();
    return { error: error.message }; // returned to useActionData()
  }

  // After successful creation, redirect to the new project
  const project = await res.json();
  return redirect(`/projects/${project.id}`);
}

// COMPONENT — purely presentational, no useEffect/fetch
function ProjectsPage() {
  const projects = useLoaderData();       // data from loader
  const actionData = useActionData();     // data from action (if any)
  const navigation = useNavigation();     // { state: 'idle' | 'loading' | 'submitting' }
  const isSubmitting = navigation.state === 'submitting';

  return (
    <div>
      <h1>Projects</h1>

      <Form method="post">
        <input name="name" placeholder="Project name" required />
        <input name="description" placeholder="Description" />
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating…' : 'New Project'}
        </button>
        {actionData?.error && <p className="error">{actionData.error}</p>}
      </Form>

      <ul>
        {projects.map((project) => (
          <li key={project.id}>
            <Link to={`/projects/${project.id}`}>{project.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: '/projects',
    element: <ProjectsPage />,
    loader: projectsLoader,
    action: createProjectAction,
  },
]);

function App() {
  return <RouterProvider router={router} />;
}
```

**Why this matters for production:**
1. **No waterfalls** — Parent and child loaders run in parallel. Previously, a parent component would fetch, render, then the child would fetch (waterfall).
2. **Automatic revalidation** — After an action runs, React Router re-calls all active loaders so your UI reflects the latest server state. No manual cache invalidation.
3. **Progressive enhancement** — `<Form>` works like a regular HTML `<form>` before JavaScript loads; with JS, it intercepts the submission for a SPA experience.
4. **Separation of concerns** — Components don't contain `useEffect` + `fetch` + loading/error state. Loaders handle fetch, `errorElement` handles errors, and the component just renders data.

---

### Q11. How do you build breadcrumbs dynamically from the route hierarchy in React Router v6?

**Answer:**

React Router v6 provides the `useMatches()` hook (available with data routers), which returns an array of all matched route objects from the root down to the current deepest match. By attaching a `handle` object to each route with metadata (like a breadcrumb label), you can build breadcrumbs dynamically from the route tree.

```jsx
import {
  createBrowserRouter,
  RouterProvider,
  useMatches,
  Link,
  Outlet,
} from 'react-router-dom';

// Route definitions with breadcrumb metadata in "handle"
const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    handle: { breadcrumb: 'Home' },
    children: [
      { index: true, element: <Home /> },
      {
        path: 'products',
        handle: { breadcrumb: 'Products' },
        children: [
          { index: true, element: <ProductList /> },
          {
            path: ':productId',
            element: <ProductDetail />,
            loader: async ({ params }) => {
              const res = await fetch(`/api/products/${params.productId}`);
              return res.json();
            },
            // Dynamic breadcrumb using loader data
            handle: {
              breadcrumb: (data) => data.name, // receives loader data
            },
          },
        ],
      },
      {
        path: 'orders',
        handle: { breadcrumb: 'Orders' },
        children: [
          { index: true, element: <OrderList /> },
          {
            path: ':orderId',
            element: <OrderDetail />,
            loader: async ({ params }) => {
              const res = await fetch(`/api/orders/${params.orderId}`);
              return res.json();
            },
            handle: {
              breadcrumb: (data) => `Order #${data.orderNumber}`,
            },
          },
        ],
      },
    ],
  },
]);

// Breadcrumbs component that reads the match hierarchy
function Breadcrumbs() {
  const matches = useMatches();

  // Filter to only matches that have a breadcrumb handle
  const crumbs = matches
    .filter((match) => match.handle?.breadcrumb)
    .map((match) => {
      const label =
        typeof match.handle.breadcrumb === 'function'
          ? match.handle.breadcrumb(match.data) // dynamic: call with loader data
          : match.handle.breadcrumb;            // static string

      return { path: match.pathname, label };
    });

  return (
    <nav aria-label="Breadcrumb" className="breadcrumbs">
      <ol>
        {crumbs.map((crumb, index) => {
          const isLast = index === crumbs.length - 1;
          return (
            <li key={crumb.path}>
              {isLast ? (
                <span aria-current="page">{crumb.label}</span>
              ) : (
                <Link to={crumb.path}>{crumb.label}</Link>
              )}
              {!isLast && <span className="separator">/</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Root layout renders breadcrumbs above the outlet
function RootLayout() {
  return (
    <div>
      <Breadcrumbs />
      <Outlet />
    </div>
  );
}
```

**Result for URL `/products/42`:**
Home / Products / Wireless Keyboard (loaded from API)

**Why `useMatches` is powerful:** It gives you the entire matched route hierarchy with each route's `data` (loader result), `params`, `pathname`, and `handle`. This makes it trivial to build not just breadcrumbs but also dynamic page titles, analytics tracking, and permission checks based on route metadata.

---

### Q12. How do you style active links and show navigation loading indicators in React Router v6?

**Answer:**

React Router v6 provides several mechanisms for indicating the current navigation state and active routes:

1. **`<NavLink>`** — its render props (`isActive`, `isPending`) let you style the active and pending states.
2. **`useNavigation()`** — returns `{ state, location, formData }` where `state` is `'idle'`, `'loading'`, or `'submitting'`. Use this for global progress bars.
3. **`useNavigationLoadingState()`** — a more granular alternative (v6.10+).

```jsx
import { NavLink, useNavigation, Outlet } from 'react-router-dom';
import { useEffect, useRef } from 'react';

// CSS Module or Tailwind approach for active link styling
function Sidebar() {
  return (
    <nav className="sidebar">
      {[
        { to: '/dashboard', label: 'Dashboard', icon: '📊' },
        { to: '/projects', label: 'Projects', icon: '📁' },
        { to: '/team', label: 'Team', icon: '👥' },
        { to: '/settings', label: 'Settings', icon: '⚙️' },
      ].map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive, isPending }) => {
            let classes = 'nav-item';
            if (isActive) classes += ' nav-item--active';
            if (isPending) classes += ' nav-item--pending';
            return classes;
          }}
        >
          <span className="nav-icon">{icon}</span>
          <span className="nav-label">{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

// Global navigation progress bar (like YouTube / GitHub)
function NavigationProgressBar() {
  const navigation = useNavigation();
  const isNavigating = navigation.state !== 'idle';
  const progressRef = useRef(null);

  useEffect(() => {
    if (!progressRef.current) return;
    if (isNavigating) {
      progressRef.current.style.width = '0%';
      // Animate to 80% while loading
      requestAnimationFrame(() => {
        progressRef.current.style.transition = 'width 10s ease-out';
        progressRef.current.style.width = '80%';
      });
    } else {
      // Snap to 100% then hide
      progressRef.current.style.transition = 'width 0.2s ease-in';
      progressRef.current.style.width = '100%';
      setTimeout(() => {
        progressRef.current.style.transition = 'none';
        progressRef.current.style.width = '0%';
      }, 200);
    }
  }, [isNavigating]);

  return (
    <div className="progress-bar-container">
      <div
        ref={progressRef}
        className="progress-bar"
        style={{
          height: '3px',
          background: '#4f46e5',
          position: 'fixed',
          top: 0,
          left: 0,
          zIndex: 9999,
        }}
      />
    </div>
  );
}

// Main layout combining both
function AppLayout() {
  const navigation = useNavigation();

  return (
    <div className="app-layout">
      <NavigationProgressBar />
      <Sidebar />
      <main className={navigation.state === 'loading' ? 'content dimmed' : 'content'}>
        <Outlet />
      </main>
    </div>
  );
}
```

**CSS for the active styles:**

```jsx
/* In your CSS file */
/*
.nav-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  color: #6b7280;
  text-decoration: none;
  border-left: 3px solid transparent;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: #f3f4f6;
  color: #111827;
}

.nav-item--active {
  background: #eef2ff;
  color: #4f46e5;
  border-left-color: #4f46e5;
  font-weight: 600;
}

.nav-item--pending {
  opacity: 0.6;
  animation: pulse 1.5s infinite;
}

.content.dimmed {
  opacity: 0.6;
  pointer-events: none;
  transition: opacity 0.2s;
}
*/
```

The `isPending` state on `NavLink` only activates with data routers — it becomes `true` when the user has clicked the link and the target route's loader is still running. This is invaluable for indicating "we're navigating there, please wait."

---

## Advanced Level (Q13–Q20)

---

### Q13. What are the strategies for route-based code splitting, and how do you handle chunk loading failures in production?

**Answer:**

Route-based code splitting is the most effective splitting strategy because routes represent distinct user workflows, and the split boundaries align naturally with navigation events. There are several strategies to consider:

**Strategy 1: Basic `React.lazy` per route (most common)**

```jsx
import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

// Utility: lazy with retry for network failures
function lazyWithRetry(importFn, retries = 3) {
  return lazy(() => {
    const attempt = (retriesLeft) =>
      importFn().catch((err) => {
        if (retriesLeft <= 0) throw err;
        return new Promise((resolve) => setTimeout(resolve, 1000)).then(() =>
          attempt(retriesLeft - 1)
        );
      });
    return attempt(retries);
  });
}

const Dashboard = lazyWithRetry(() => import('./pages/Dashboard'));
const Analytics = lazyWithRetry(() => import('./pages/Analytics'));
const Settings  = lazyWithRetry(() => import('./pages/Settings'));
```

**Strategy 2: Route-level `lazy` property (React Router v6.4+)**

React Router v6.4+ supports a `lazy` property on route definitions. The function must return an object with `Component`, `loader`, `action`, etc. This is powerful because even the loader code is lazy-loaded — you don't ship data-fetching logic for routes the user never visits.

```jsx
const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        path: 'dashboard',
        // Everything for this route is lazy-loaded: component, loader, action, errorElement
        lazy: async () => {
          const { DashboardPage, dashboardLoader } = await import('./pages/Dashboard');
          return {
            Component: DashboardPage,
            loader: dashboardLoader,
          };
        },
      },
      {
        path: 'analytics',
        lazy: async () => {
          const { AnalyticsPage, analyticsLoader } = await import('./pages/Analytics');
          return {
            Component: AnalyticsPage,
            loader: analyticsLoader,
          };
        },
      },
      {
        path: 'settings',
        lazy: async () => {
          const { SettingsPage, settingsAction } = await import('./pages/Settings');
          return {
            Component: SettingsPage,
            action: settingsAction,
          };
        },
      },
    ],
  },
]);
```

**Strategy 3: Prefetching critical routes**

```jsx
// Prefetch on mouse enter, visibility, or idle time
function usePrefetch(importFn) {
  const prefetched = useRef(false);
  return () => {
    if (!prefetched.current) {
      prefetched.current = true;
      importFn();
    }
  };
}

function Navbar() {
  const prefetchDashboard = usePrefetch(() => import('./pages/Dashboard'));
  const prefetchAnalytics = usePrefetch(() => import('./pages/Analytics'));

  return (
    <nav>
      <Link to="/dashboard" onMouseEnter={prefetchDashboard}>Dashboard</Link>
      <Link to="/analytics" onMouseEnter={prefetchAnalytics}>Analytics</Link>
    </nav>
  );
}
```

**Handling chunk loading failures in production:**

When you deploy a new version, old chunk filenames become invalid. Users with the app already open will get `ChunkLoadError` when navigating to a lazy route.

```jsx
import { useRouteError } from 'react-router-dom';

function RootErrorBoundary() {
  const error = useRouteError();

  const isChunkError =
    error?.name === 'ChunkLoadError' ||
    error?.message?.includes('Failed to fetch dynamically imported module') ||
    error?.message?.includes('Loading chunk');

  if (isChunkError) {
    return (
      <div className="error-page">
        <h2>A new version is available</h2>
        <p>Please reload to get the latest version.</p>
        <button onClick={() => {
          // Clear module cache and reload
          if ('caches' in window) {
            caches.keys().then((names) =>
              Promise.all(names.map((name) => caches.delete(name)))
            );
          }
          window.location.reload();
        }}>
          Reload Application
        </button>
      </div>
    );
  }

  return <GenericError error={error} />;
}
```

---

### Q14. How does scroll restoration work in React Router v6, and how do you customize it for production use cases?

**Answer:**

In a traditional multi-page site, the browser automatically handles scroll restoration — navigating back restores the previous scroll position. In an SPA, you lose this behavior because the browser never actually loads a new page. React Router v6.4+ provides a `<ScrollRestoration>` component that restores this behavior for data router apps.

```jsx
import { createBrowserRouter, RouterProvider, ScrollRestoration, Outlet } from 'react-router-dom';

function RootLayout() {
  return (
    <>
      <Header />
      <main>
        <Outlet />
      </main>
      <Footer />
      {/* Place this once at the root — it handles scroll for all navigations */}
      <ScrollRestoration
        // Customize which navigations restore scroll and which scroll to top
        getKey={(location, matches) => {
          // Use pathname as the key — different pages get different scroll positions
          // But for paginated pages, use the full URL so page 2 and page 3 have distinct positions
          const paginatedPaths = ['/products', '/orders', '/search'];
          if (paginatedPaths.some((p) => location.pathname.startsWith(p))) {
            return location.pathname + location.search; // include query params
          }
          return location.pathname;
        }}
      />
    </>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { path: 'products', element: <ProductList /> },
      { path: 'products/:id', element: <ProductDetail /> },
      { path: 'orders', element: <OrderList /> },
    ],
  },
]);
```

**For apps not using the data router**, or for more manual control:

```jsx
import { useLocation } from 'react-router-dom';
import { useEffect, useRef } from 'react';

function useScrollRestoration() {
  const location = useLocation();
  const scrollPositions = useRef(new Map());
  const prevKey = useRef(location.key);

  useEffect(() => {
    // Save scroll position for the route we're leaving
    scrollPositions.current.set(prevKey.current, window.scrollY);

    // Restore scroll for the route we're entering (back/forward) or scroll to top (new nav)
    const savedPosition = scrollPositions.current.get(location.key);
    if (savedPosition !== undefined) {
      // Navigating back — restore position
      window.scrollTo(0, savedPosition);
    } else {
      // New navigation — scroll to top
      window.scrollTo(0, 0);
    }

    prevKey.current = location.key;
  }, [location]);
}

// Use in your root layout
function AppLayout() {
  useScrollRestoration();

  return (
    <div>
      <Navbar />
      <Outlet />
    </div>
  );
}
```

**Edge cases to handle in production:**
- **Hash links** (`/page#section`) — you may want to scroll to the element instead of the top. Check `location.hash` and use `document.getElementById(hash).scrollIntoView()`.
- **Modal routes** (`/products/42/preview`) — you probably don't want to scroll at all when a modal opens over the current page. Detect this with route metadata or URL patterns.
- **Infinite scroll lists** — the simple approach won't work because the DOM content isn't there on restore. You need virtualized lists (`react-window` / `tanstack-virtual`) with persisted scroll state.

---

### Q15. How do you manage URL state for filters, sorting, and pagination instead of component state?

**Answer:**

Storing UI state like filters, sorting, and pagination in the URL (via query parameters) rather than in `useState` has significant advantages: the state is **shareable** (users can copy the URL), **bookmarkable**, **back-button friendly**, and **survives page refreshes**. This is a production best practice for any listing or search interface.

```jsx
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useMemo, useCallback } from 'react';

// Custom hook for type-safe URL state management
function useUrlState(defaults) {
  const [searchParams, setSearchParams] = useSearchParams();

  const state = useMemo(() => {
    const result = {};
    for (const [key, defaultValue] of Object.entries(defaults)) {
      const raw = searchParams.get(key);
      if (raw === null) {
        result[key] = defaultValue;
      } else if (typeof defaultValue === 'number') {
        result[key] = Number(raw);
      } else if (typeof defaultValue === 'boolean') {
        result[key] = raw === 'true';
      } else if (Array.isArray(defaultValue)) {
        result[key] = searchParams.getAll(key);
      } else {
        result[key] = raw;
      }
    }
    return result;
  }, [searchParams, defaults]);

  const setState = useCallback(
    (updates) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        for (const [key, value] of Object.entries(updates)) {
          if (value === null || value === undefined || value === defaults[key]) {
            next.delete(key); // remove defaults from URL to keep it clean
          } else if (Array.isArray(value)) {
            next.delete(key);
            value.forEach((v) => next.append(key, v));
          } else {
            next.set(key, String(value));
          }
        }
        return next;
      });
    },
    [setSearchParams, defaults]
  );

  return [state, setState];
}

// Production product listing page
// URL: /products?category=electronics&sort=price_asc&page=2&minPrice=100
function ProductListPage() {
  const [filters, setFilters] = useUrlState({
    category: '',
    sort: 'relevance',
    page: 1,
    minPrice: 0,
    maxPrice: 10000,
    inStock: false,
  });

  // Data fetching based on URL state (or use a route loader)
  const { data, isLoading } = useQuery({
    queryKey: ['products', filters],
    queryFn: () => fetchProducts(filters),
  });

  return (
    <div className="product-list">
      {/* Filters sidebar */}
      <aside className="filters">
        <select
          value={filters.category}
          onChange={(e) => setFilters({ category: e.target.value, page: 1 })}
        >
          <option value="">All Categories</option>
          <option value="electronics">Electronics</option>
          <option value="clothing">Clothing</option>
        </select>

        <select
          value={filters.sort}
          onChange={(e) => setFilters({ sort: e.target.value })}
        >
          <option value="relevance">Relevance</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="newest">Newest</option>
        </select>

        <label>
          <input
            type="checkbox"
            checked={filters.inStock}
            onChange={(e) => setFilters({ inStock: e.target.checked, page: 1 })}
          />
          In Stock Only
        </label>

        <div className="price-range">
          <input
            type="number"
            value={filters.minPrice}
            onChange={(e) => setFilters({ minPrice: Number(e.target.value), page: 1 })}
            placeholder="Min price"
          />
          <input
            type="number"
            value={filters.maxPrice}
            onChange={(e) => setFilters({ maxPrice: Number(e.target.value), page: 1 })}
            placeholder="Max price"
          />
        </div>
      </aside>

      {/* Product grid */}
      <section className="products">
        {isLoading ? (
          <ProductSkeleton count={12} />
        ) : (
          data.products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))
        )}

        {/* Pagination */}
        <Pagination
          currentPage={filters.page}
          totalPages={data?.totalPages ?? 1}
          onPageChange={(page) => setFilters({ page })}
        />
      </section>
    </div>
  );
}
```

**Key production details:**
- **Reset page to 1** when changing filters (otherwise the user might be on page 5 of a category that only has 2 pages).
- **Omit default values** from the URL to keep it clean (`/products` instead of `/products?category=&sort=relevance&page=1`).
- **Debounce** text inputs (like price or search) before updating the URL to avoid excessive history entries. Use `replace: true` for interim updates: `setSearchParams(next, { replace: true })`.
- **Use `useSearchParams`** for "leaf" state (filters, pagination). Use `useParams` for "identity" state (which resource you're viewing).

---

### Q16. How do you implement parallel data loading with route loaders, and how does it eliminate fetch waterfalls?

**Answer:**

A **fetch waterfall** occurs when data requests are serialized unnecessarily: the parent component mounts, fetches its data, renders the child component, which then fetches *its* data. This sequential pattern can easily add seconds to page load times. React Router v6.4+ loaders solve this by running **all matched route loaders in parallel** before any component renders.

```jsx
import {
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  Await,
  defer,
  Outlet,
} from 'react-router-dom';
import { Suspense } from 'react';

// --- API layer ---
const api = {
  getProject: (id) => fetch(`/api/projects/${id}`).then((r) => r.json()),
  getMembers: (id) => fetch(`/api/projects/${id}/members`).then((r) => r.json()),
  getActivity: (id) => fetch(`/api/projects/${id}/activity`).then((r) => r.json()),
  getTasks: (id) => fetch(`/api/projects/${id}/tasks`).then((r) => r.json()),
};

// --- ROUTE: /projects/:projectId ---
// Parent loader: fetches project data
async function projectLoader({ params }) {
  const project = await api.getProject(params.projectId);
  return project;
}

// --- ROUTE: /projects/:projectId/overview ---
// Child loader: fetches members + activity IN PARALLEL with the parent loader
function overviewLoader({ params }) {
  // Use defer() for non-critical data — renders UI immediately,
  // streams in data as it resolves
  return defer({
    members: api.getMembers(params.projectId),       // critical — await'd
    activity: api.getActivity(params.projectId),     // deferred — streams in
  });
}

// --- ROUTE: /projects/:projectId/tasks ---
async function tasksLoader({ params }) {
  const tasks = await api.getTasks(params.projectId);
  return { tasks };
}

// --- COMPONENTS ---
function ProjectLayout() {
  const project = useLoaderData(); // from projectLoader

  return (
    <div>
      <h1>{project.name}</h1>
      <nav>
        <NavLink to="overview">Overview</NavLink>
        <NavLink to="tasks">Tasks</NavLink>
      </nav>
      <Outlet /> {/* child route renders here */}
    </div>
  );
}

function ProjectOverview() {
  const { members, activity } = useLoaderData();

  return (
    <div className="overview">
      {/* members was deferred — wrap in Suspense + Await */}
      <Suspense fallback={<MembersSkeleton />}>
        <Await resolve={members}>
          {(resolvedMembers) => (
            <MembersList members={resolvedMembers} />
          )}
        </Await>
      </Suspense>

      <Suspense fallback={<ActivitySkeleton />}>
        <Await resolve={activity}>
          {(resolvedActivity) => (
            <ActivityFeed items={resolvedActivity} />
          )}
        </Await>
      </Suspense>
    </div>
  );
}

function ProjectTasks() {
  const { tasks } = useLoaderData();
  return <TaskBoard tasks={tasks} />;
}

// --- ROUTER ---
const router = createBrowserRouter([
  {
    path: '/projects/:projectId',
    element: <ProjectLayout />,
    loader: projectLoader,
    children: [
      {
        path: 'overview',
        element: <ProjectOverview />,
        loader: overviewLoader,
      },
      {
        path: 'tasks',
        element: <ProjectTasks />,
        loader: tasksLoader,
      },
    ],
  },
]);
```

**What happens when navigating to `/projects/123/overview`:**

Without loaders (waterfall):
```
GET /api/projects/123          ████████░░░░░░░░  800ms
  → Render ProjectLayout
  GET /api/projects/123/members          ████████░░  600ms
  GET /api/projects/123/activity                ████████  500ms
                                                Total: ~1900ms
```

With parallel loaders:
```
GET /api/projects/123          ████████░░░░░░░░  800ms
GET /api/projects/123/members  ████████░░░░░░░░  600ms  ← runs simultaneously
GET /api/projects/123/activity ████████░░░░░░░░  500ms  ← runs simultaneously
                                                Total: ~800ms (bottleneck is slowest request)
```

**`defer()` and `<Await>`:** For non-critical data, `defer()` lets you return a promise without awaiting it. The route renders immediately with the critical data, and `<Await>` inside a `<Suspense>` boundary streams in the deferred data when it resolves. This gives you the best of both worlds: no waterfall, and a fast initial paint.

---

### Q17. How do you implement optimistic UI updates with React Router actions?

**Answer:**

**Optimistic UI** means updating the interface immediately to reflect the user's action *before* the server confirms it, then reconciling when the server responds. This makes the app feel instant. React Router v6.4+ supports this via `useNavigation()` and `useFetcher()`, which expose the in-flight form data so you can render the "expected" state while the action is pending.

```jsx
import {
  createBrowserRouter,
  useFetcher,
  useLoaderData,
} from 'react-router-dom';

// LOADER: fetch the todo list
async function todosLoader() {
  const res = await fetch('/api/todos');
  return res.json();
}

// ACTION: handle create, update, delete
async function todosAction({ request }) {
  const formData = await request.formData();
  const intent = formData.get('intent');

  switch (intent) {
    case 'create': {
      const res = await fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: formData.get('title') }),
      });
      return res.json();
    }
    case 'toggle': {
      const id = formData.get('id');
      const completed = formData.get('completed') === 'true';
      await fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: !completed }),
      });
      return { ok: true };
    }
    case 'delete': {
      const id = formData.get('id');
      await fetch(`/api/todos/${id}`, { method: 'DELETE' });
      return { ok: true };
    }
    default:
      throw new Error(`Unknown intent: ${intent}`);
  }
}

// COMPONENT: renders with optimistic state
function TodoList() {
  const todos = useLoaderData();

  return (
    <div>
      <h1>Todos</h1>
      <NewTodoForm />
      <ul>
        {todos.map((todo) => (
          <TodoItem key={todo.id} todo={todo} />
        ))}
      </ul>
    </div>
  );
}

function TodoItem({ todo }) {
  const fetcher = useFetcher();
  const isDeleting = fetcher.formData?.get('intent') === 'delete';
  const isToggling = fetcher.formData?.get('intent') === 'toggle';

  // Optimistic state: use the in-flight data if available
  const optimisticCompleted = isToggling
    ? fetcher.formData.get('completed') !== 'true' // toggled value
    : todo.completed;

  // Hide immediately when deleting (optimistic delete)
  if (isDeleting) return null;

  return (
    <li
      className={`todo-item ${optimisticCompleted ? 'completed' : ''}`}
      style={{ opacity: fetcher.state !== 'idle' ? 0.7 : 1 }}
    >
      <fetcher.Form method="post">
        <input type="hidden" name="intent" value="toggle" />
        <input type="hidden" name="id" value={todo.id} />
        <input type="hidden" name="completed" value={String(todo.completed)} />
        <button type="submit" className="toggle-btn">
          {optimisticCompleted ? '✅' : '⬜'}
        </button>
      </fetcher.Form>

      <span className={optimisticCompleted ? 'line-through' : ''}>{todo.title}</span>

      <fetcher.Form method="post">
        <input type="hidden" name="intent" value="delete" />
        <input type="hidden" name="id" value={todo.id} />
        <button type="submit" className="delete-btn" aria-label="Delete">
          🗑️
        </button>
      </fetcher.Form>
    </li>
  );
}

function NewTodoForm() {
  const fetcher = useFetcher();
  const isAdding = fetcher.state === 'submitting';

  return (
    <fetcher.Form method="post" onSubmit={(e) => {
      // Reset form after submission
      requestAnimationFrame(() => e.target.reset());
    }}>
      <input type="hidden" name="intent" value="create" />
      <input
        name="title"
        placeholder="What needs to be done?"
        required
        disabled={isAdding}
      />
      <button type="submit" disabled={isAdding}>
        {isAdding ? 'Adding…' : 'Add'}
      </button>

      {/* Optimistic: show the pending todo */}
      {isAdding && (
        <li className="todo-item pending">
          ⬜ {fetcher.formData.get('title')}
        </li>
      )}
    </fetcher.Form>
  );
}

const router = createBrowserRouter([
  {
    path: '/todos',
    element: <TodoList />,
    loader: todosLoader,
    action: todosAction,
  },
]);
```

**Why `useFetcher` instead of `<Form>`:** `useFetcher` doesn't cause a navigation — it submits in place and revalidates data without changing the URL. This is perfect for in-page interactions like toggling a checkbox, liking a post, or deleting an item. Each `useFetcher` is independent, so multiple items can have in-flight actions simultaneously.

**Rollback on error:** After the action completes, React Router automatically revalidates all active loaders. If the server rejected the mutation, the revalidated data will override the optimistic state, effectively "rolling back" the UI. You can also check `fetcher.data` for error responses and display a toast.

---

### Q18. How does file-based routing work, and how do React Router (SPA), Remix, and Next.js compare in their routing approaches?

**Answer:**

**File-based routing** automatically generates routes from the filesystem structure — you create files in a specific directory, and the framework creates corresponding routes. This eliminates manual route configuration and enforces conventions.

Here is a comparison of three major routing paradigms in the React ecosystem:

```jsx
// ============================================================
// 1. REACT ROUTER v6 (SPA) — Manual route configuration
// ============================================================
// You define routes explicitly in code

import { createBrowserRouter } from 'react-router-dom';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'about', element: <About /> },
      {
        path: 'blog',
        children: [
          { index: true, element: <BlogList /> },
          { path: ':slug', element: <BlogPost /> },
        ],
      },
    ],
  },
]);

// ============================================================
// 2. NEXT.JS (App Router) — File-based with conventions
// ============================================================
// File structure automatically creates routes:
//
// app/
// ├── layout.tsx          → Root layout (wraps all pages)
// ├── page.tsx            → /
// ├── about/
// │   └── page.tsx        → /about
// ├── blog/
// │   ├── layout.tsx      → Shared blog layout
// │   ├── page.tsx        → /blog
// │   └── [slug]/
// │       ├── page.tsx    → /blog/:slug
// │       └── loading.tsx → Loading UI for this route
// └── not-found.tsx       → 404 page

// app/blog/[slug]/page.tsx
export default async function BlogPost({ params }) {
  const { slug } = await params;
  const post = await fetchPost(slug);
  return <article>{post.content}</article>;
}

// ============================================================
// 3. REMIX — File-based with nested routing + data APIs
// ============================================================
// File structure:
//
// app/routes/
// ├── _index.tsx              → /
// ├── about.tsx               → /about
// ├── blog._index.tsx         → /blog
// ├── blog.$slug.tsx          → /blog/:slug
// └── dashboard.tsx           → /dashboard (layout)
//     ├── dashboard._index.tsx → /dashboard (index)
//     └── dashboard.settings.tsx → /dashboard/settings

// app/routes/blog.$slug.tsx
import { json } from '@remix-run/node';
import { useLoaderData } from '@remix-run/react';

export async function loader({ params }) {
  const post = await db.post.findUnique({ where: { slug: params.slug } });
  if (!post) throw new Response('Not Found', { status: 404 });
  return json(post);
}

export default function BlogPost() {
  const post = useLoaderData();
  return <article>{post.content}</article>;
}
```

**Comparison table:**

| Feature | React Router v6 (SPA) | Next.js (App Router) | Remix |
|---|---|---|---|
| Route definition | Manual (code) | File-based (`app/`) | File-based (`routes/`) |
| Rendering | Client-only | SSR, SSG, ISR, RSC | SSR + streaming |
| Data loading | Route loaders (client) | Server Components, `fetch` | Route loaders (server) |
| Mutations | Route actions (client) | Server Actions | Route actions (server) |
| Nested layouts | `<Outlet>` | `layout.tsx` convention | Dot-delimited filenames |
| Code splitting | Manual (`React.lazy`) | Automatic per route | Automatic per route |
| SEO | Requires SSR setup | Built-in | Built-in |
| Bundle size | Smallest (client lib) | Larger (full framework) | Medium (full framework) |

**When to use which:**
- **React Router SPA** — When you're building an internal tool, dashboard, or app behind authentication where SEO doesn't matter and you want full control.
- **Next.js** — When SEO, performance, and static generation matter (marketing sites, e-commerce, blogs). React Server Components provide the latest rendering patterns.
- **Remix** — When you want progressive enhancement, excellent form handling, and the tightest integration between routing and data. Remix is now merging with React Router (React Router v7 = Remix).

---

### Q19. What are the routing considerations for server-side rendering (SSR), and how do you handle SSR routing with React Router?

**Answer:**

In SSR, the server must render the React component tree to HTML for the initial request. This means the router must work on the server (no `window`, no `History API`). React Router provides `StaticRouter` for this purpose, along with the newer `createStaticHandler` and `createStaticRouter` for data router apps.

**Key SSR routing challenges:**
1. No `window.location` or `History API` on the server — the router must accept the URL as a parameter.
2. Data fetching must complete before rendering so the HTML includes content (not loading spinners).
3. The client must **hydrate** with the same data and route state the server used.
4. Redirects in loaders/actions must translate to HTTP 301/302 responses.

```jsx
// ===========================
// server.js (Express example)
// ===========================
import express from 'express';
import { createStaticHandler, createStaticRouter, StaticRouterProvider } from 'react-router-dom/server';
import { renderToPipeableStream } from 'react-dom/server';
import { routes } from './routes'; // shared route config

const app = express();

app.get('*', async (req, res) => {
  // 1. Create a static handler from the route config
  const handler = createStaticHandler(routes);

  // 2. Create a Fetch API Request from the Express request
  const fetchRequest = createFetchRequest(req);

  // 3. Run loaders and get the routing context
  const context = await handler.query(fetchRequest);

  // 4. Handle redirects from loaders/actions
  if (context instanceof Response) {
    if ([301, 302, 303, 307, 308].includes(context.status)) {
      return res.redirect(context.status, context.headers.get('Location'));
    }
    return res.status(context.status).send(await context.text());
  }

  // 5. Create a static router with the context
  const router = createStaticRouter(handler.dataRoutes, context);

  // 6. Render to a stream
  const { pipe } = renderToPipeableStream(
    <StaticRouterProvider router={router} context={context} />,
    {
      onShellReady() {
        res.setHeader('Content-Type', 'text/html');
        res.write('<!DOCTYPE html><html><head></head><body><div id="root">');
        pipe(res);
      },
      onAllReady() {
        res.write('</div>');
        // Inject loader data for client hydration
        res.write(`<script>window.__LOADER_DATA__=${JSON.stringify(context.loaderData)}</script>`);
        res.write('<script src="/client.js"></script></body></html>');
        res.end();
      },
      onError(error) {
        console.error('SSR error:', error);
        res.status(500).send('Server Error');
      },
    }
  );
});

// Helper: convert Express req to Fetch API Request
function createFetchRequest(req) {
  const origin = `${req.protocol}://${req.get('host')}`;
  const url = new URL(req.originalUrl, origin);
  return new Request(url.href, {
    method: req.method,
    headers: new Headers(req.headers),
    body: req.method !== 'GET' && req.method !== 'HEAD' ? req.body : null,
  });
}

// ===========================
// client.js (hydration)
// ===========================
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { hydrateRoot } from 'react-dom/client';
import { routes } from './routes';

const router = createBrowserRouter(routes, {
  hydrationData: window.__LOADER_DATA__,
});

hydrateRoot(
  document.getElementById('root'),
  <RouterProvider router={router} />
);
```

**Shared route configuration (`routes.js`):**

```jsx
import { lazy } from 'react';
import RootLayout from './layouts/RootLayout';

export const routes = [
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        lazy: () => import('./pages/Home'),
      },
      {
        path: 'products',
        lazy: () => import('./pages/Products'),
      },
      {
        path: 'products/:id',
        lazy: () => import('./pages/ProductDetail'),
      },
    ],
  },
];
```

**Production SSR routing considerations:**
- **Streaming SSR** (`renderToPipeableStream`) — Send the shell immediately, stream in content as loaders resolve. Users see the page faster.
- **Status codes** — If a loader throws a 404, the server should set `res.status(404)` before sending HTML. Search engines need correct status codes.
- **Redirects** — Must happen at the HTTP level (3xx response), not just a client-side `<Navigate>`.
- **Data serialization** — Loader data embedded in HTML must be sanitized to prevent XSS (escape `</script>` tags, etc.).
- **Meta tags** — The server must render `<head>` content (title, description, OG tags) based on the matched route, critical for SEO.

---

### Q20. How do you architect a production routing system with authentication, role-based access, layout composition, and error boundaries?

**Answer:**

A production routing architecture combines all the patterns discussed — auth guards, role-based layouts, lazy loading, error boundaries, data loading, and shared layouts — into a cohesive, maintainable structure. Here is a complete, real-world route configuration:

```jsx
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { lazy, Suspense } from 'react';

// ============================
// Layouts
// ============================
import RootLayout from './layouts/RootLayout';
import AuthLayout from './layouts/AuthLayout';
import DashboardLayout from './layouts/DashboardLayout';
import AdminLayout from './layouts/AdminLayout';

// ============================
// Auth guard components
// ============================
function RequireAuth({ children }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children ?? <Outlet />;
}

function RequireRole({ roles, children }) {
  const { user } = useAuth();
  if (!roles.includes(user?.role)) return <Navigate to="/unauthorized" replace />;
  return children ?? <Outlet />;
}

function RedirectIfAuthenticated() {
  const { user } = useAuth();
  if (user) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

// ============================
// Lazy-loaded pages
// ============================
const Login = lazy(() => import('./pages/auth/Login'));
const Register = lazy(() => import('./pages/auth/Register'));
const ForgotPassword = lazy(() => import('./pages/auth/ForgotPassword'));

const DashboardHome = lazy(() => import('./pages/dashboard/Home'));
const Projects = lazy(() => import('./pages/dashboard/Projects'));
const ProjectDetail = lazy(() => import('./pages/dashboard/ProjectDetail'));
const Settings = lazy(() => import('./pages/dashboard/Settings'));
const Profile = lazy(() => import('./pages/dashboard/Profile'));
const Notifications = lazy(() => import('./pages/dashboard/Notifications'));

const AdminUsers = lazy(() => import('./pages/admin/Users'));
const AdminAnalytics = lazy(() => import('./pages/admin/Analytics'));
const AdminAuditLog = lazy(() => import('./pages/admin/AuditLog'));
const AdminSettings = lazy(() => import('./pages/admin/Settings'));

const Unauthorized = lazy(() => import('./pages/Unauthorized'));
const NotFound = lazy(() => import('./pages/NotFound'));

// ============================
// Error boundaries
// ============================
function RootErrorBoundary() {
  const error = useRouteError();
  return (
    <div className="error-page">
      <h1>Application Error</h1>
      <p>Something went wrong. Our team has been notified.</p>
      <pre>{import.meta.env.DEV ? error?.stack : error?.message}</pre>
      <button onClick={() => window.location.assign('/')}>Go Home</button>
    </div>
  );
}

function SectionErrorBoundary() {
  const error = useRouteError();
  return (
    <div className="section-error">
      <h2>This section encountered an error</h2>
      <p>{error?.message || 'Unknown error'}</p>
      <button onClick={() => window.location.reload()}>Retry</button>
    </div>
  );
}

// ============================
// Suspense wrapper
// ============================
function PageSuspense() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Outlet />
    </Suspense>
  );
}

// ============================
// Router configuration
// ============================
const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,           // global nav, toast provider, etc.
    errorElement: <RootErrorBoundary />, // catches unhandled errors everywhere
    children: [
      // Redirect root to dashboard
      { index: true, element: <Navigate to="/dashboard" replace /> },

      // ── PUBLIC / AUTH ROUTES ──────────────────────────
      {
        element: <RedirectIfAuthenticated />, // redirect logged-in users away
        children: [
          {
            element: <AuthLayout />,  // centered card layout
            children: [
              {
                element: <PageSuspense />,
                children: [
                  { path: 'login', element: <Login /> },
                  { path: 'register', element: <Register /> },
                  { path: 'forgot-password', element: <ForgotPassword /> },
                ],
              },
            ],
          },
        ],
      },

      // ── AUTHENTICATED ROUTES ──────────────────────────
      {
        element: <RequireAuth />,
        children: [
          // Dashboard section
          {
            path: 'dashboard',
            element: <DashboardLayout />,  // sidebar + top bar
            errorElement: <SectionErrorBoundary />,
            children: [
              {
                element: <PageSuspense />,
                children: [
                  {
                    index: true,
                    element: <DashboardHome />,
                    loader: () => import('./loaders/dashboard').then((m) => m.homeLoader()),
                  },
                  { path: 'projects', element: <Projects /> },
                  {
                    path: 'projects/:projectId',
                    element: <ProjectDetail />,
                    loader: ({ params }) =>
                      import('./loaders/projects').then((m) => m.projectLoader(params)),
                    errorElement: <SectionErrorBoundary />,
                  },
                  { path: 'settings', element: <Settings /> },
                  { path: 'profile', element: <Profile /> },
                  { path: 'notifications', element: <Notifications /> },
                ],
              },
            ],
          },

          // ── ADMIN ROUTES (role-gated) ────────────────
          {
            path: 'admin',
            element: <RequireRole roles={['admin', 'super_admin']} />,
            children: [
              {
                element: <AdminLayout />,  // admin-specific sidebar
                errorElement: <SectionErrorBoundary />,
                children: [
                  {
                    element: <PageSuspense />,
                    children: [
                      { index: true, element: <Navigate to="users" replace /> },
                      {
                        path: 'users',
                        element: <AdminUsers />,
                        loader: () =>
                          import('./loaders/admin').then((m) => m.usersLoader()),
                      },
                      { path: 'analytics', element: <AdminAnalytics /> },
                      { path: 'audit-log', element: <AdminAuditLog /> },
                      { path: 'settings', element: <AdminSettings /> },
                    ],
                  },
                ],
              },
            ],
          },
        ],
      },

      // ── UTILITY ROUTES ────────────────────────────────
      { path: 'unauthorized', element: <Unauthorized /> },
      { path: '*', element: <NotFound /> },
    ],
  },
]);

// ============================
// App entry
// ============================
export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
```

**Architecture decisions explained:**

1. **Layout nesting:** `RootLayout` → `DashboardLayout` / `AdminLayout` / `AuthLayout`. Each layout renders an `<Outlet>` and provides layout-specific chrome (sidebar, header, breadcrumbs). Users never see the admin sidebar on the dashboard, or the dashboard sidebar on the login page.

2. **Pathless layout routes:** Routes without a `path` but with an `element` act as layout wrappers. `<RequireAuth>` and `<RequireRole>` are pathless — they wrap child routes with a guard without adding a URL segment.

3. **Error boundary scoping:** The root error boundary catches catastrophic failures. Section-level error boundaries (`DashboardLayout`, individual routes) catch localized errors so a broken project page doesn't crash the entire dashboard.

4. **Lazy loader imports:** Even loaders are dynamically imported (`import('./loaders/dashboard').then(m => m.homeLoader())`). This keeps the initial bundle minimal — loader code for admin pages is never downloaded by regular users.

5. **Suspense at the layout level:** `<PageSuspense>` wraps groups of lazy routes so the layout (sidebar, header) stays visible while the page content loads.

6. **Redirect patterns:**
   - Root `/` → `/dashboard` (authenticated) or stays on `/login` (guest)
   - `RedirectIfAuthenticated` sends logged-in users away from auth pages
   - `RequireAuth` captures the intended URL in `state.from` for post-login redirect
   - `RequireRole` sends unauthorized users to a dedicated "unauthorized" page

This architecture scales to large applications with dozens of routes across multiple teams, while maintaining clear separation of concerns, optimal code splitting, and robust error handling.

---

## Summary

| # | Topic | Level |
|---|---|---|
| Q1 | Client-side vs server-side routing | Beginner |
| Q2 | BrowserRouter, Routes, Route setup | Beginner |
| Q3 | Link and NavLink | Beginner |
| Q4 | useParams and useSearchParams | Beginner |
| Q5 | Nested routes and Outlet | Beginner |
| Q6 | Programmatic navigation (useNavigate) | Intermediate |
| Q7 | Protected/private routes with auth guards | Intermediate |
| Q8 | Lazy loading routes with React.lazy + Suspense | Intermediate |
| Q9 | 404 pages and route error handling | Intermediate |
| Q10 | Route loaders and actions (v6.4+ data APIs) | Intermediate |
| Q11 | Breadcrumbs from route hierarchy | Intermediate |
| Q12 | Active link styling and navigation indicators | Intermediate |
| Q13 | Route-based code splitting strategies | Advanced |
| Q14 | Scroll restoration on navigation | Advanced |
| Q15 | URL state management (filters, pagination) | Advanced |
| Q16 | Parallel data loading with route loaders | Advanced |
| Q17 | Optimistic UI with React Router actions | Advanced |
| Q18 | File-based routing (Next.js, Remix comparison) | Advanced |
| Q19 | SSR routing considerations | Advanced |
| Q20 | Production routing architecture | Advanced |
