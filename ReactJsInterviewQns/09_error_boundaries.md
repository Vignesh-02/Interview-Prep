# Topic 9: Error Boundaries & Error Handling in React 18

## Introduction

In any non-trivial React application, runtime errors are inevitable — a network response returns an unexpected shape, a deeply nested property is `undefined`, a third-party component throws during render, or a user triggers an edge case that no unit test anticipated. Without a deliberate error-handling strategy, a single uncaught error inside a component's render path will **unmount the entire React tree**, leaving the user staring at a blank white screen. React 16 introduced **Error Boundaries** as the official mechanism for catching JavaScript errors anywhere in a component tree, logging them, and displaying a fallback UI instead of crashing the whole application. An Error Boundary is a class component that implements one or both of two special lifecycle methods — `static getDerivedStateFromError(error)` (used to update state so the next render shows a fallback UI) and `componentDidCatch(error, errorInfo)` (used for side effects like logging the error to an external service). In React 18, Error Boundaries remain class components; there is no hooks-based equivalent provided by React core, although the community library `react-error-boundary` exposes a fully featured hook-based API that wraps this class component pattern internally.

Error handling in React extends far beyond Error Boundaries. Boundaries catch errors that occur **during rendering, in lifecycle methods, and in constructors** of the components beneath them — but they do **not** catch errors inside event handlers, asynchronous code (`setTimeout`, `requestAnimationFrame`, promises), or server-side rendering. For event handlers, you need traditional `try/catch` blocks. For async operations inside `useEffect`, you must attach `.catch()` handlers to promises or wrap `async/await` calls in `try/catch`. At the global level, you can listen for `window.onerror` and `window.onunhandledrejection` to capture anything that slips through component-level handling. In production applications, these layers are combined into a comprehensive error-handling architecture: Error Boundaries catch render-phase errors and show contextual fallback UIs, `try/catch` in event handlers and effects captures imperative errors, global listeners act as a safety net, and an error-monitoring service (Sentry, Datadog, Bugsnag) aggregates everything for developer visibility. React 18's concurrent features — `startTransition`, `Suspense` for data fetching — add nuance to this architecture, as transitions can be interrupted and Suspense boundaries interact with Error Boundaries to handle both loading and error states.

Here is a foundational illustration showing a reusable Error Boundary class component alongside its usage with a Suspense boundary in a React 18 application:

```jsx
import React, { Component, Suspense } from 'react';

// Reusable Error Boundary class component
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render shows the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log to an external error reporting service
    console.error('ErrorBoundary caught:', error, errorInfo.componentStack);
    logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      // Render a fallback UI — either a custom prop or a default message
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          resetErrorBoundary: this.handleReset,
        });
      }
      return (
        <div role="alert" style={{ padding: '2rem', textAlign: 'center' }}>
          <h2>Something went wrong</h2>
          <button onClick={this.handleReset}>Try Again</button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Usage: combining Error Boundary with Suspense for data-fetching components
function App() {
  return (
    <ErrorBoundary
      fallback={({ error, resetErrorBoundary }) => (
        <div role="alert">
          <p>Failed to load dashboard: {error.message}</p>
          <button onClick={resetErrorBoundary}>Retry</button>
        </div>
      )}
    >
      <Suspense fallback={<div className="skeleton-loader" />}>
        <Dashboard />
      </Suspense>
    </ErrorBoundary>
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is an Error Boundary in React and why must it be a class component?

**Answer:**

An Error Boundary is a React component that catches JavaScript errors anywhere in its child component tree during rendering, lifecycle methods, and constructors, and renders a fallback UI instead of letting the entire application crash. Before Error Boundaries existed (pre-React 16), a single runtime error in any component would corrupt React's internal state and produce cryptic, broken UIs on subsequent renders. The React team decided to adopt the philosophy that **an unhandled error in a UI should not leave a broken interface visible** — it is better to show nothing (or a fallback) than a corrupted component tree. Error Boundaries give you control over what "nothing" looks like.

Error Boundaries **must** be class components because the two lifecycle methods that power them — `static getDerivedStateFromError()` and `componentDidCatch()` — are only available on the class component API. The React team has discussed adding a hooks equivalent (e.g., a hypothetical `useErrorBoundary` in React core) but as of React 18, no such hook exists in the core library. The reason is partly design complexity: these lifecycle methods need to intercept errors during the **render phase** itself (not just during effects or event handlers), and the hooks execution model does not currently have a mechanism to catch errors thrown by sibling or child hooks during rendering.

```jsx
import React, { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  // Called during the "render" phase — must be pure (no side effects)
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  // Called during the "commit" phase — safe for side effects like logging
  componentDidCatch(error, errorInfo) {
    console.error('Caught by ErrorBoundary:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}

// Usage
function App() {
  return (
    <ErrorBoundary>
      <MyFeatureComponent />
    </ErrorBoundary>
  );
}
```

Key points to remember:
- Error Boundaries catch errors in the **rendering phase** of all descendants.
- They do **not** catch errors in event handlers, async code, SSR, or errors thrown in the boundary itself.
- You typically create one reusable Error Boundary and use it in multiple places.

---

### Q2. What is the difference between `getDerivedStateFromError` and `componentDidCatch`?

**Answer:**

These two lifecycle methods serve complementary but distinct purposes and run at different phases of React's commit cycle:

| Aspect | `getDerivedStateFromError(error)` | `componentDidCatch(error, errorInfo)` |
|---|---|---|
| **Phase** | Render phase | Commit phase |
| **Type** | Static method (no `this` access) | Instance method (has `this` access) |
| **Purpose** | Return new state to trigger fallback UI | Perform side effects (logging, analytics) |
| **Side effects** | Not allowed (must be pure) | Allowed and expected |
| **Arguments** | `error` only | `error` + `errorInfo` (with `componentStack`) |

`getDerivedStateFromError` is called first. It receives the thrown error and must return a state update object. Because it runs during the render phase, it must be a pure function — no API calls, no `console.log`, no mutations. Its sole job is to flip a boolean (e.g., `hasError: true`) so that the component's `render` method can return a fallback UI.

`componentDidCatch` is called after the DOM has been updated with the fallback UI. It receives both the error and an `errorInfo` object containing a `componentStack` string — a trace showing the component hierarchy that led to the error. This is the place to send the error to Sentry, Datadog, or any logging service.

```jsx
import React, { Component } from 'react';
import * as Sentry from '@sentry/react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  // RENDER PHASE — pure, no side effects
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  // COMMIT PHASE — side effects allowed
  componentDidCatch(error, errorInfo) {
    // Log to Sentry with the component stack trace
    Sentry.withScope((scope) => {
      scope.setExtra('componentStack', errorInfo.componentStack);
      scope.setTag('boundary', this.props.name || 'unnamed');
      Sentry.captureException(error);
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert">
          <h2>Oops! Something went wrong.</h2>
          <details>
            <summary>Error details</summary>
            <pre>{this.state.error?.message}</pre>
          </details>
        </div>
      );
    }
    return this.props.children;
  }
}
```

In practice, you almost always implement **both** methods: `getDerivedStateFromError` to show a fallback and `componentDidCatch` to report the error.

---

### Q3. Where can Error Boundaries catch errors and where can they NOT?

**Answer:**

Understanding the scope of Error Boundaries is critical for building a robust error-handling architecture. Error Boundaries catch errors thrown during specific phases and contexts — but they have well-defined blind spots.

**Error Boundaries DO catch errors in:**
1. Rendering (the `render` method / function component return)
2. Lifecycle methods (`componentDidMount`, `componentDidUpdate`, `getDerivedStateFromProps`, etc.)
3. Constructors of child class components
4. `static getDerivedStateFromProps` of child components

**Error Boundaries do NOT catch errors in:**
1. **Event handlers** — React does not need Error Boundaries for events because event handler errors don't corrupt the render tree; the UI remains intact. Use `try/catch` instead.
2. **Asynchronous code** — `setTimeout`, `setInterval`, `requestAnimationFrame`, Promises (these execute outside React's render/commit lifecycle).
3. **Server-side rendering** — Error Boundaries rely on browser DOM commit phases that don't exist in SSR.
4. **Errors thrown in the Error Boundary itself** — A boundary cannot catch its own errors; you need a parent boundary for that.

```jsx
import React, { Component, useState } from 'react';

class ErrorBoundary extends Component {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error, info) {
    console.error('Boundary caught:', error);
  }
  render() {
    if (this.state.hasError) return <p>Fallback UI</p>;
    return this.props.children;
  }
}

function BuggyComponent() {
  const [count, setCount] = useState(0);

  // ✅ CAUGHT by Error Boundary — error during render
  if (count === 3) {
    throw new Error('Render crash at count 3!');
  }

  // ❌ NOT caught by Error Boundary — error in event handler
  const handleClick = () => {
    try {
      // Must use try/catch for event handler errors
      riskyOperation();
    } catch (error) {
      console.error('Event handler error:', error);
      // Handle gracefully — show toast, set error state, etc.
    }
  };

  // ❌ NOT caught by Error Boundary — error in async code
  React.useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch('/api/data');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
      } catch (error) {
        console.error('Async error:', error);
        // Must handle manually — set error state, show fallback, etc.
      }
    }
    fetchData();
  }, []);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount((c) => c + 1)}>Increment</button>
      <button onClick={handleClick}>Risky Action</button>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BuggyComponent />
    </ErrorBoundary>
  );
}
```

---

### Q4. How do you design a fallback UI for an Error Boundary?

**Answer:**

A good fallback UI serves two audiences: the **end user** (who needs clear guidance on what happened and what they can do) and the **developer** (who needs enough detail to diagnose the problem). In production, the fallback should be friendly and actionable; in development, it can show more technical detail. Common patterns include:

1. **Simple message with retry** — best for isolated widget failures
2. **Full-page error screen** — for top-level route boundaries
3. **Contextual degradation** — e.g., hide a broken sidebar but keep the main content
4. **Different fallbacks per boundary** — pass fallback as a render prop

```jsx
import React, { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      // Use the custom fallback renderer if provided
      if (this.props.FallbackComponent) {
        const FallbackComponent = this.props.FallbackComponent;
        return (
          <FallbackComponent
            error={this.state.error}
            resetErrorBoundary={this.handleReset}
          />
        );
      }
      // Default fallback
      return <DefaultErrorFallback error={this.state.error} onReset={this.handleReset} />;
    }
    return this.props.children;
  }
}

// Pattern 1: Simple widget fallback
function WidgetErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="widget-error" role="alert">
      <p>This section couldn't load.</p>
      <button onClick={resetErrorBoundary}>Retry</button>
    </div>
  );
}

// Pattern 2: Full-page error screen
function PageErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="error-page" role="alert">
      <div className="error-page__content">
        <h1>We hit a snag</h1>
        <p>Something unexpected happened. Our team has been notified.</p>
        <div className="error-page__actions">
          <button onClick={resetErrorBoundary}>Try Again</button>
          <button onClick={() => (window.location.href = '/')}>Go Home</button>
        </div>
        {process.env.NODE_ENV === 'development' && (
          <details className="error-page__details">
            <summary>Developer Info</summary>
            <pre>{error.message}</pre>
            <pre>{error.stack}</pre>
          </details>
        )}
      </div>
    </div>
  );
}

// Pattern 3: Default minimal fallback
function DefaultErrorFallback({ error, onReset }) {
  return (
    <div role="alert" style={{ padding: '1rem', border: '1px solid #e74c3c', borderRadius: 8 }}>
      <strong>Something went wrong</strong>
      <button onClick={onReset} style={{ marginLeft: '1rem' }}>
        Retry
      </button>
    </div>
  );
}

// Usage — different fallbacks for different sections
function App() {
  return (
    <>
      {/* Top-level boundary with full-page fallback */}
      <ErrorBoundary FallbackComponent={PageErrorFallback}>
        <Header />
        <main>
          {/* Widget-level boundary with small inline fallback */}
          <ErrorBoundary FallbackComponent={WidgetErrorFallback}>
            <WeatherWidget />
          </ErrorBoundary>
          <ErrorBoundary FallbackComponent={WidgetErrorFallback}>
            <StockTicker />
          </ErrorBoundary>
        </main>
      </ErrorBoundary>
    </>
  );
}
```

Design principles for fallback UIs:
- Always include `role="alert"` for accessibility.
- Always provide an action (retry, go home, contact support).
- Never show raw stack traces to end users in production.
- Match the visual footprint of the component it replaces (don't let a tiny widget error take over the whole screen).

---

### Q5. How do you handle errors inside event handlers in React?

**Answer:**

Error Boundaries do not catch errors inside event handlers because event handler errors don't occur during React's render phase — they happen in response to user interactions, after the UI has already been committed to the DOM. The UI remains intact, so React's philosophy is that these errors should be handled imperatively with standard JavaScript `try/catch`.

The recommended pattern is to use `try/catch` inside the handler and set a local error state that the component can render conditionally. For forms and mutations, this is extremely common in production.

```jsx
import React, { useState, useCallback } from 'react';

function PaymentForm() {
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = useCallback(async (event) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const formData = new FormData(event.target);
      const response = await fetch('/api/payments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(formData)),
      });

      if (!response.ok) {
        // Parse structured error from the server
        const errorBody = await response.json().catch(() => ({}));
        throw new PaymentError(
          errorBody.message || `Payment failed (HTTP ${response.status})`,
          errorBody.code
        );
      }

      setIsSuccess(true);
    } catch (err) {
      // Differentiate between known and unknown errors
      if (err instanceof PaymentError) {
        setError({ type: 'payment', message: err.message, code: err.code });
      } else if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
        setError({ type: 'network', message: 'Network error. Check your connection.' });
      } else {
        setError({ type: 'unknown', message: 'An unexpected error occurred.' });
        // Report unexpected errors to monitoring
        reportToSentry(err);
      }
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  if (isSuccess) {
    return <p className="success">Payment successful!</p>;
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div role="alert" className="error-banner">
          {error.message}
          {error.type === 'network' && (
            <button type="submit">Retry</button>
          )}
        </div>
      )}
      <input name="cardNumber" placeholder="Card Number" required />
      <input name="amount" type="number" placeholder="Amount" required />
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Processing…' : 'Pay'}
      </button>
    </form>
  );
}

// Custom error class for payment-specific errors
class PaymentError extends Error {
  constructor(message, code) {
    super(message);
    this.name = 'PaymentError';
    this.code = code;
  }
}
```

Key takeaways:
- Always wrap async event handlers in `try/catch`.
- Set component-level error state and render appropriate feedback.
- Differentiate between error types (network, business logic, unknown) for better UX.
- Report unexpected errors to your monitoring service even though they didn't crash the render tree.

---

## Intermediate Level (Q6–Q12)

---

### Q6. What is the `react-error-boundary` library and how does it improve on hand-written Error Boundaries?

**Answer:**

The `react-error-boundary` library (by Brian Vaughn, a former React core team member) provides a production-ready `<ErrorBoundary>` component and a `useErrorBoundary` hook that eliminates the need to write and maintain your own class component. It includes features that are tedious to implement correctly from scratch: reset keys, `onReset` callbacks, `onError` callbacks, render-prop and component-prop fallback patterns, and the ability to imperatively trigger the error boundary from event handlers or effects using the `useErrorBoundary` hook.

Key features:
- **`FallbackComponent` prop** — pass a component that receives `{ error, resetErrorBoundary }`.
- **`fallbackRender` prop** — pass a render function for inline fallbacks.
- **`onError` prop** — side-effect callback for logging (replaces `componentDidCatch`).
- **`onReset` prop** — callback fired when the boundary resets (useful for clearing caches or query state).
- **`resetKeys` prop** — an array of values; when any value changes, the boundary automatically resets (e.g., when the user navigates to a new page).
- **`useErrorBoundary` hook** — lets functional components programmatically throw errors into the nearest boundary, bridging the gap for event handlers and async code.

```jsx
import { ErrorBoundary, useErrorBoundary } from 'react-error-boundary';
import { useQueryClient } from '@tanstack/react-query';

// Fallback component
function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert" className="error-card">
      <h3>Something went wrong</h3>
      <p>{error.message}</p>
      <button onClick={resetErrorBoundary}>Try Again</button>
    </div>
  );
}

// Component that uses useErrorBoundary to propagate async errors
function UserProfile({ userId }) {
  const { showBoundary } = useErrorBoundary();
  const [user, setUser] = React.useState(null);

  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch(`/api/users/${userId}`);
        if (!res.ok) throw new Error(`Failed to load user: ${res.status}`);
        const data = await res.json();
        if (!cancelled) setUser(data);
      } catch (error) {
        if (!cancelled) {
          // Propagate to the nearest Error Boundary!
          showBoundary(error);
        }
      }
    }
    load();
    return () => { cancelled = true; };
  }, [userId, showBoundary]);

  if (!user) return <div className="skeleton" />;
  return <div><h2>{user.name}</h2><p>{user.email}</p></div>;
}

// App-level wiring with resetKeys and onError
function App() {
  const queryClient = useQueryClient();
  const [selectedUserId, setSelectedUserId] = React.useState('1');

  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, info) => {
        // Log to monitoring service
        logToSentry(error, { componentStack: info.componentStack });
      }}
      onReset={() => {
        // Clear stale cached data on retry
        queryClient.clear();
      }}
      resetKeys={[selectedUserId]} // Auto-reset when user selection changes
    >
      <UserSelector value={selectedUserId} onChange={setSelectedUserId} />
      <UserProfile userId={selectedUserId} />
    </ErrorBoundary>
  );
}
```

The `useErrorBoundary` hook solves one of the biggest pain points with vanilla Error Boundaries: the inability to catch async or event handler errors. By calling `showBoundary(error)`, you can funnel **any** error — from a `fetch` call, a `setTimeout`, a WebSocket message — into the React Error Boundary system.

---

### Q7. What is the best strategy for placing Error Boundaries in a React application?

**Answer:**

Error Boundary placement is an architectural decision that balances **blast radius** (how much UI is affected when an error occurs) against **complexity** (how many boundaries you maintain). The general strategy is to layer boundaries at multiple levels:

1. **Root-level boundary** — wraps the entire app; last line of defense; shows a "something went wrong" full-page screen. This prevents the white screen of death.
2. **Route/page-level boundaries** — wraps each page or route segment; a crash in the Settings page doesn't take down the Dashboard.
3. **Feature/widget-level boundaries** — wraps independent UI sections (a chat widget, a sidebar, a data table); the rest of the page remains functional.
4. **Critical interaction boundaries** — wraps specific high-risk components (third-party embeds, user-generated content renderers, complex data visualizations).

The rule of thumb: **the boundary should match the unit of recovery**. If retrying makes sense for a single widget, put a boundary around that widget. If the entire page needs to reload, put the boundary at the route level.

```jsx
import { ErrorBoundary } from 'react-error-boundary';
import { Outlet } from 'react-router-dom';

// --- Level 1: Root Boundary ---
function RootErrorFallback({ error }) {
  return (
    <div className="root-error">
      <h1>Application Error</h1>
      <p>We're sorry — something went critically wrong.</p>
      <button onClick={() => window.location.reload()}>Reload Application</button>
    </div>
  );
}

// --- Level 2: Route/Page Boundary (used in router config) ---
function RouteErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="page-error">
      <h2>This page encountered an error</h2>
      <p>{error.message}</p>
      <button onClick={resetErrorBoundary}>Retry</button>
      <button onClick={() => (window.location.href = '/')}>Go to Home</button>
    </div>
  );
}

// --- Level 3: Widget Boundary ---
function WidgetErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="widget-error-inline">
      <span>⚠ Failed to load</span>
      <button onClick={resetErrorBoundary}>Retry</button>
    </div>
  );
}

// Layout component with layered boundaries
function DashboardLayout() {
  return (
    <div className="dashboard">
      <Sidebar />
      <main>
        {/* Route-level boundary for the page content */}
        <ErrorBoundary FallbackComponent={RouteErrorFallback}>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  );
}

// Dashboard page with widget-level boundaries
function DashboardPage() {
  return (
    <div className="dashboard-grid">
      {/* Each widget has its own boundary — one crash doesn't affect others */}
      <ErrorBoundary FallbackComponent={WidgetErrorFallback}>
        <RevenueChart />
      </ErrorBoundary>

      <ErrorBoundary FallbackComponent={WidgetErrorFallback}>
        <ActiveUsersWidget />
      </ErrorBoundary>

      <ErrorBoundary FallbackComponent={WidgetErrorFallback}>
        <RecentOrdersTable />
      </ErrorBoundary>

      {/* Third-party widget — higher risk, isolated boundary */}
      <ErrorBoundary FallbackComponent={WidgetErrorFallback}>
        <ThirdPartyAnalyticsEmbed />
      </ErrorBoundary>
    </div>
  );
}

// Root of the application
function App() {
  return (
    <ErrorBoundary FallbackComponent={RootErrorFallback}>
      <RouterProvider router={router} />
    </ErrorBoundary>
  );
}
```

Placement guidelines:
- **Don't wrap every single component** — that creates maintenance overhead and can actually worsen UX (too many small fallbacks look broken).
- **Do wrap every route** — so one page's error doesn't break navigation.
- **Do wrap third-party components** — you don't control their code quality.
- **Do wrap components that render user-generated or dynamic content** — these are the most unpredictable.

---

### Q8. How do you implement a retry/reset mechanism for Error Boundaries?

**Answer:**

Resetting an Error Boundary means clearing its error state so it re-renders its children, giving the failed component a fresh chance. There are three common reset triggers:

1. **User-initiated reset** — a "Try Again" button in the fallback UI.
2. **Prop-driven reset (resetKeys)** — the boundary automatically resets when certain props change (e.g., a route change, a new search query).
3. **Programmatic reset** — a parent component or external event calls a reset method.

For data-fetching components, a reset often needs to be paired with **cache invalidation** — if the boundary resets but the stale/errored data is still in cache, the component will immediately fail again.

```jsx
import { ErrorBoundary } from 'react-error-boundary';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';

// Component that fetches data
function OrderList() {
  const { data: orders } = useQuery({
    queryKey: ['orders'],
    queryFn: async () => {
      const res = await fetch('/api/orders');
      if (!res.ok) throw new Error('Failed to load orders');
      return res.json();
    },
    retry: 2, // React Query retries automatically, but after exhausting retries it throws
    useErrorBoundary: true, // Propagate the error to the nearest Error Boundary
  });

  return (
    <ul>
      {orders.map((order) => (
        <li key={order.id}>
          #{order.id} — {order.status} — ${order.total}
        </li>
      ))}
    </ul>
  );
}

function OrdersPage() {
  const queryClient = useQueryClient();
  const location = useLocation();

  return (
    <ErrorBoundary
      FallbackComponent={({ error, resetErrorBoundary }) => (
        <div role="alert" className="error-panel">
          <h3>Failed to load orders</h3>
          <p>{error.message}</p>
          <button
            onClick={() => {
              // Invalidate the cache before resetting so the query refetches
              queryClient.invalidateQueries({ queryKey: ['orders'] });
              resetErrorBoundary();
            }}
          >
            Retry
          </button>
        </div>
      )}
      onReset={() => {
        // Additional cleanup when boundary resets
        queryClient.removeQueries({ queryKey: ['orders'] });
      }}
      resetKeys={[location.pathname]} // Auto-reset when navigating away and back
    >
      <OrderList />
    </ErrorBoundary>
  );
}
```

How `resetKeys` works internally: the Error Boundary stores the previous `resetKeys` array and compares it on every update. If any value in the array changes and the boundary is currently in an error state, it automatically calls `setState({ hasError: false })`, which re-renders the children. This is invaluable for route-based resets — if a user navigates to a different page and comes back, the error clears automatically.

---

### Q9. How do you handle errors in `useEffect` — especially with async operations?

**Answer:**

Errors thrown inside `useEffect` callbacks are **not caught by Error Boundaries** because effects run asynchronously after the render phase. An unhandled promise rejection inside an effect will trigger the browser's `unhandledrejection` event but will not activate any Error Boundary. You have two main strategies:

1. **Set component-level error state** — catch the error and render a fallback within the same component.
2. **Propagate to an Error Boundary** — use the `useErrorBoundary` hook from `react-error-boundary` (or the `showBoundary` pattern) to funnel the error into the nearest boundary.

Strategy 2 is preferred when you want a consistent error-handling UX managed by boundaries rather than ad-hoc per-component error states.

```jsx
import React, { useState, useEffect } from 'react';
import { useErrorBoundary } from 'react-error-boundary';

// --- Strategy 1: Local error state ---
function UserProfileLocal({ userId }) {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setLoading(true);

    async function fetchUser() {
      try {
        const res = await fetch(`/api/users/${userId}`);
        if (!res.ok) {
          throw new Error(`Server responded with ${res.status}`);
        }
        const data = await res.json();
        if (!cancelled) {
          setUser(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchUser();
    return () => { cancelled = true; };
  }, [userId]);

  if (loading) return <div className="skeleton" />;
  if (error) return <div role="alert">Error: {error.message}</div>;
  return <div><h2>{user.name}</h2></div>;
}

// --- Strategy 2: Propagate to Error Boundary ---
function UserProfileBoundary({ userId }) {
  const [user, setUser] = useState(null);
  const { showBoundary } = useErrorBoundary();

  useEffect(() => {
    let cancelled = false;

    async function fetchUser() {
      try {
        const res = await fetch(`/api/users/${userId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) setUser(data);
      } catch (err) {
        if (!cancelled) {
          // This triggers the nearest <ErrorBoundary>'s fallback
          showBoundary(err);
        }
      }
    }

    fetchUser();
    return () => { cancelled = true; };
  }, [userId, showBoundary]);

  if (!user) return <div className="skeleton" />;
  return <div><h2>{user.name}</h2></div>;
}
```

Important patterns for async effect error handling:
- **Always use a `cancelled` flag** to prevent state updates on unmounted components.
- **Always check `response.ok`** — `fetch` does not reject on HTTP errors (4xx, 5xx).
- **Distinguish retryable errors** (network timeouts → retry) from permanent errors (404 → show "not found").
- **AbortController** is the modern alternative to the `cancelled` flag for cancelling fetch requests:

```jsx
useEffect(() => {
  const controller = new AbortController();

  async function fetchData() {
    try {
      const res = await fetch(`/api/data`, { signal: controller.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setData(data);
    } catch (err) {
      if (err.name !== 'AbortError') {
        showBoundary(err);
      }
    }
  }

  fetchData();
  return () => controller.abort();
}, [showBoundary]);
```

---

### Q10. How do you set up global error handling in a React application?

**Answer:**

Global error handlers act as the **outermost safety net** — they catch errors that slip past all component-level handling (Error Boundaries, `try/catch` in handlers, effect error handling). The two primary browser APIs are:

1. **`window.onerror`** (or `window.addEventListener('error')`) — catches uncaught synchronous errors and some runtime errors.
2. **`window.addEventListener('unhandledrejection')` ** — catches unhandled promise rejections (e.g., a forgotten `.catch()` on a promise).

In production, these listeners should report errors to your monitoring service. They should **not** try to recover or show UI (that's the Error Boundary's job) — they exist purely for visibility.

```jsx
// src/errorHandling/globalErrorHandler.js
export function setupGlobalErrorHandlers({ onError }) {
  // Catch uncaught synchronous errors
  const handleError = (event) => {
    // Ignore errors from browser extensions or cross-origin scripts
    if (!event.filename || event.filename.includes('extensions://')) {
      return;
    }

    onError({
      type: 'uncaught_error',
      message: event.message,
      source: event.filename,
      line: event.lineno,
      column: event.colno,
      error: event.error,
      timestamp: new Date().toISOString(),
    });
  };

  // Catch unhandled promise rejections
  const handleRejection = (event) => {
    const error = event.reason;
    onError({
      type: 'unhandled_rejection',
      message: error?.message || 'Unknown rejection',
      stack: error?.stack,
      error,
      timestamp: new Date().toISOString(),
    });
  };

  // Catch resource loading errors (images, scripts, stylesheets)
  const handleResourceError = (event) => {
    if (event.target !== window) {
      onError({
        type: 'resource_error',
        tagName: event.target?.tagName,
        source: event.target?.src || event.target?.href,
        timestamp: new Date().toISOString(),
      });
    }
  };

  window.addEventListener('error', handleError);
  window.addEventListener('unhandledrejection', handleRejection);
  window.addEventListener('error', handleResourceError, true); // capture phase for resource errors

  // Return cleanup function
  return () => {
    window.removeEventListener('error', handleError);
    window.removeEventListener('unhandledrejection', handleRejection);
    window.removeEventListener('error', handleResourceError, true);
  };
}

// src/index.jsx — set up before React renders
import { setupGlobalErrorHandlers } from './errorHandling/globalErrorHandler';
import { reportError } from './errorHandling/errorReporter';

const cleanupGlobalHandlers = setupGlobalErrorHandlers({
  onError: (errorData) => {
    // In development, log to console
    if (process.env.NODE_ENV === 'development') {
      console.error('[Global Error Handler]', errorData);
    }
    // In production, send to monitoring service
    reportError(errorData);
  },
});

// React app setup
import { createRoot } from 'react-dom/client';
import App from './App';

const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

The layered error-handling model:

```
┌──────────────────────────────────────────────────┐
│  Layer 1: Global Handlers (window.onerror, etc.) │  ← Safety net
│  ┌────────────────────────────────────────────┐  │
│  │  Layer 2: Root Error Boundary              │  │  ← Full-page fallback
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │  Layer 3: Route Error Boundaries     │  │  │  ← Per-page fallback
│  │  │  ┌────────────────────────────────┐  │  │  │
│  │  │  │  Layer 4: Widget Boundaries    │  │  │  │  ← Inline fallback
│  │  │  │  ┌──────────────────────────┐  │  │  │  │
│  │  │  │  │  Layer 5: try/catch in   │  │  │  │  │  ← Imperative handling
│  │  │  │  │  handlers & effects      │  │  │  │  │
│  │  │  │  └──────────────────────────┘  │  │  │  │
│  │  │  └────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

---

### Q11. How do you integrate Error Boundaries with an error monitoring service like Sentry?

**Answer:**

Error monitoring services like Sentry, Datadog, and Bugsnag need to receive error data from **every layer** of your error-handling stack — Error Boundaries (render errors), event handler `try/catch` blocks, effect error handlers, and global listeners. The Sentry SDK for React (`@sentry/react`) provides its own `<Sentry.ErrorBoundary>` component that automatically reports errors and includes the React component stack. But you can also integrate Sentry with a custom boundary or `react-error-boundary`.

```jsx
// src/errorHandling/errorReporter.js
import * as Sentry from '@sentry/react';

// Initialize Sentry once at app startup
export function initErrorMonitoring() {
  Sentry.init({
    dsn: process.env.REACT_APP_SENTRY_DSN,
    environment: process.env.NODE_ENV,
    release: process.env.REACT_APP_VERSION,
    integrations: [
      new Sentry.BrowserTracing(),
      new Sentry.Replay(), // Session replay for error reproduction
    ],
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
    replaysOnErrorSampleRate: 1.0, // Always capture replay on error
    replaysSessionSampleRate: 0.01, // Sample 1% of sessions
    beforeSend(event) {
      // Scrub sensitive data before sending
      if (event.request?.data) {
        event.request.data = '[REDACTED]';
      }
      return event;
    },
  });
}

// Unified error reporting function for all layers
export function reportError(error, context = {}) {
  Sentry.withScope((scope) => {
    // Attach contextual information
    if (context.componentStack) {
      scope.setExtra('componentStack', context.componentStack);
    }
    if (context.boundary) {
      scope.setTag('errorBoundary', context.boundary);
    }
    if (context.userId) {
      scope.setUser({ id: context.userId });
    }
    if (context.action) {
      scope.setTag('action', context.action);
    }
    scope.setTag('errorLayer', context.layer || 'unknown');

    Sentry.captureException(error);
  });
}

// --- Usage with react-error-boundary ---
import { ErrorBoundary } from 'react-error-boundary';

function App() {
  return (
    <ErrorBoundary
      FallbackComponent={AppErrorFallback}
      onError={(error, info) => {
        reportError(error, {
          componentStack: info.componentStack,
          boundary: 'AppRoot',
          layer: 'error_boundary',
        });
      }}
    >
      <AppContent />
    </ErrorBoundary>
  );
}

// --- Usage in event handlers ---
function DeleteButton({ itemId }) {
  const handleDelete = async () => {
    try {
      await fetch(`/api/items/${itemId}`, { method: 'DELETE' });
    } catch (error) {
      reportError(error, {
        layer: 'event_handler',
        action: 'delete_item',
        itemId,
      });
      toast.error('Failed to delete item. Please try again.');
    }
  };

  return <button onClick={handleDelete}>Delete</button>;
}

// --- Usage with Sentry's built-in ErrorBoundary (alternative) ---
import * as Sentry from '@sentry/react';

function AppWithSentryBoundary() {
  return (
    <Sentry.ErrorBoundary
      fallback={({ error, resetError }) => (
        <div role="alert">
          <h2>Something went wrong</h2>
          <p>{error.message}</p>
          <button onClick={resetError}>Try Again</button>
        </div>
      )}
      showDialog // Shows Sentry's user feedback dialog
      dialogOptions={{
        title: 'It looks like we hit a snag.',
        subtitle: 'Our team has been notified.',
        subtitle2: 'If you'd like to help, tell us what happened below.',
      }}
    >
      <AppContent />
    </Sentry.ErrorBoundary>
  );
}
```

Best practices for error monitoring integration:
- Initialize Sentry **before** rendering React so it captures errors during initial render.
- Use `beforeSend` to scrub PII and sensitive data.
- Tag errors by layer (`error_boundary`, `event_handler`, `effect`, `global`) to filter in the Sentry dashboard.
- Include the `componentStack` for Error Boundary errors — it shows exactly which component tree path led to the crash.
- Use Sentry's Session Replay to see what the user was doing when the error occurred.

---

### Q12. How do Error Boundaries interact with Suspense in React 18?

**Answer:**

In React 18, `<Suspense>` and Error Boundaries work together to handle the two failure modes of async operations: **loading** (handled by Suspense) and **errors** (handled by Error Boundaries). When a component "suspends" (throws a promise), Suspense catches it and shows a fallback. When a component throws an error (throws a non-promise), the nearest Error Boundary catches it and shows its fallback. This makes them complementary, and in production you almost always pair them.

The typical pattern with data-fetching libraries (React Query, SWR, Relay) that support Suspense:

```jsx
import React, { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { useQuery, QueryErrorResetBoundary } from '@tanstack/react-query';

// Component that uses Suspense-mode React Query
function UserDetails({ userId }) {
  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const res = await fetch(`/api/users/${userId}`);
      if (!res.ok) throw new Error('Failed to load user');
      return res.json();
    },
    suspense: true, // Enables Suspense mode — throws promise while loading, throws error on failure
  });

  return (
    <div className="user-card">
      <h2>{user.name}</h2>
      <p>{user.email}</p>
      <p>Joined: {new Date(user.createdAt).toLocaleDateString()}</p>
    </div>
  );
}

// Loading skeleton
function UserSkeleton() {
  return (
    <div className="user-card skeleton">
      <div className="skeleton-line" style={{ width: '60%' }} />
      <div className="skeleton-line" style={{ width: '80%' }} />
      <div className="skeleton-line" style={{ width: '40%' }} />
    </div>
  );
}

// Error fallback
function UserErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="user-card error" role="alert">
      <p>Couldn't load user: {error.message}</p>
      <button onClick={resetErrorBoundary}>Retry</button>
    </div>
  );
}

// Composed: Error Boundary wraps Suspense
// Order matters: ErrorBoundary OUTSIDE, Suspense INSIDE
function UserSection({ userId }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          FallbackComponent={UserErrorFallback}
          onReset={reset} // Clears React Query's error state on reset
        >
          <Suspense fallback={<UserSkeleton />}>
            <UserDetails userId={userId} />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}

// Multiple independent sections — each with its own Suspense + ErrorBoundary
function DashboardPage() {
  return (
    <div className="dashboard">
      <UserSection userId="1" />

      <ErrorBoundary FallbackComponent={WidgetError}>
        <Suspense fallback={<ChartSkeleton />}>
          <AnalyticsChart />
        </Suspense>
      </ErrorBoundary>

      <ErrorBoundary FallbackComponent={WidgetError}>
        <Suspense fallback={<TableSkeleton />}>
          <RecentActivity />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
```

Key points about the interaction:
- **Order matters**: The Error Boundary must be **above** the Suspense boundary. If Suspense is above, the error will bypass the Suspense (since it's not a promise) and propagate up to the nearest Error Boundary — which might be too far up the tree.
- **React Query's `QueryErrorResetBoundary`**: When the Error Boundary resets, React Query also needs to know to retry the query. `QueryErrorResetBoundary` provides a `reset` function that clears the query's error state, which you pass to the Error Boundary's `onReset`.
- **Granularity**: Wrapping each data-fetching section in its own Suspense + ErrorBoundary pair means independent loading and error states — one section failing doesn't affect others.

---

## Advanced Level (Q13–Q20)

---

### Q13. What are graceful degradation patterns for error handling in React?

**Answer:**

Graceful degradation means that when a part of the application fails, the rest continues to function as normally as possible. Instead of crashing or showing a generic error screen, the UI adapts — hiding the broken section, showing a simpler version, or offering an alternative path. This requires intentional design at both the component and architecture level.

There are several proven patterns:

1. **Feature flagging with fallbacks** — if a feature crashes, disable it and show a simpler alternative.
2. **Progressive enhancement** — core functionality works without advanced features; errors in enhancements don't break the core.
3. **Stale-while-error** — show the last known good data while indicating the refresh failed.
4. **Reduced functionality mode** — disable the broken feature but keep everything else operational.

```jsx
import React, { useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { useQuery } from '@tanstack/react-query';

// --- Pattern 1: Component-level graceful degradation ---
// If the rich editor fails, fall back to a plain textarea
function CommentInput({ onSubmit }) {
  return (
    <ErrorBoundary
      fallbackRender={({ resetErrorBoundary }) => (
        <div>
          <p className="warning">Rich editor unavailable. Using simple input.</p>
          <SimpleTextarea onSubmit={onSubmit} />
          <button onClick={resetErrorBoundary}>Try Rich Editor Again</button>
        </div>
      )}
    >
      <RichTextEditor onSubmit={onSubmit} />
    </ErrorBoundary>
  );
}

// --- Pattern 2: Stale-while-error with React Query ---
function StockPrice({ symbol }) {
  const { data, error, dataUpdatedAt, isError } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockPrice(symbol),
    refetchInterval: 5000,
    // Keep previous data when the refetch fails
    keepPreviousData: true,
    retry: 3,
  });

  return (
    <div className="stock-widget">
      <h3>{symbol}</h3>
      {data && (
        <>
          <p className="price">${data.price.toFixed(2)}</p>
          <p className="updated">
            Last updated: {new Date(dataUpdatedAt).toLocaleTimeString()}
          </p>
        </>
      )}
      {isError && data && (
        <p className="stale-warning">
          ⚠ Live updates paused — showing last known price.
          <br />
          <small>{error.message}</small>
        </p>
      )}
      {isError && !data && (
        <p className="error">Unable to load stock price.</p>
      )}
    </div>
  );
}

// --- Pattern 3: Feature degradation with recovery ---
function DashboardWithDegradation() {
  const [disabledWidgets, setDisabledWidgets] = useState(new Set());

  const handleWidgetError = (widgetId) => (error) => {
    console.error(`Widget ${widgetId} failed:`, error);
    // After 3 failures, auto-disable the widget
    setDisabledWidgets((prev) => new Set(prev).add(widgetId));
  };

  const widgets = [
    { id: 'analytics', component: AnalyticsWidget, label: 'Analytics' },
    { id: 'notifications', component: NotificationsWidget, label: 'Notifications' },
    { id: 'weather', component: WeatherWidget, label: 'Weather' },
  ];

  return (
    <div className="dashboard">
      {widgets.map(({ id, component: Widget, label }) =>
        disabledWidgets.has(id) ? (
          <div key={id} className="widget-disabled">
            <p>{label} is temporarily unavailable.</p>
            <button
              onClick={() =>
                setDisabledWidgets((prev) => {
                  const next = new Set(prev);
                  next.delete(id);
                  return next;
                })
              }
            >
              Re-enable
            </button>
          </div>
        ) : (
          <ErrorBoundary
            key={id}
            onError={handleWidgetError(id)}
            fallbackRender={({ resetErrorBoundary }) => (
              <div className="widget-error" role="alert">
                <p>{label} encountered an error.</p>
                <button onClick={resetErrorBoundary}>Retry</button>
              </div>
            )}
          >
            <Widget />
          </ErrorBoundary>
        )
      )}
    </div>
  );
}
```

The philosophy: **never let a non-critical feature take down a critical workflow**. A broken analytics chart should not prevent a user from placing an order.

---

### Q14. What are effective error recovery strategies in production React applications?

**Answer:**

Error recovery goes beyond simply showing a fallback — it's about getting the user back to a working state with minimal friction. Production recovery strategies include automatic retries, state reset cascades, partial re-mounting, and guided user recovery flows.

```jsx
import React, { useReducer, useCallback, useRef, useEffect } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

// --- Strategy 1: Automatic retry with exponential backoff ---
function AutoRetryBoundary({ children, maxRetries = 3, baseDelay = 1000 }) {
  const retryCountRef = useRef(0);
  const [key, forceRemount] = useReducer((c) => c + 1, 0);

  const handleError = useCallback(
    (error, info) => {
      retryCountRef.current += 1;
      const retryCount = retryCountRef.current;

      if (retryCount <= maxRetries) {
        const delay = baseDelay * Math.pow(2, retryCount - 1); // 1s, 2s, 4s
        console.warn(
          `AutoRetryBoundary: Retry ${retryCount}/${maxRetries} in ${delay}ms`,
          error
        );
        setTimeout(() => forceRemount(), delay);
      } else {
        // Max retries exhausted — report to monitoring
        reportToSentry(error, { retryCount, componentStack: info.componentStack });
      }
    },
    [maxRetries, baseDelay]
  );

  const handleReset = useCallback(() => {
    retryCountRef.current = 0;
  }, []);

  return (
    <ErrorBoundary
      key={key}
      onError={handleError}
      onReset={handleReset}
      fallbackRender={({ error, resetErrorBoundary }) => {
        if (retryCountRef.current <= maxRetries) {
          return (
            <div className="retry-notice">
              <p>Retrying... (attempt {retryCountRef.current}/{maxRetries})</p>
              <div className="spinner" />
            </div>
          );
        }
        return (
          <div role="alert" className="max-retries-reached">
            <h3>Unable to recover</h3>
            <p>{error.message}</p>
            <button onClick={() => { retryCountRef.current = 0; resetErrorBoundary(); }}>
              Reset & Try Again
            </button>
            <button onClick={() => (window.location.href = '/')}>
              Go to Home
            </button>
          </div>
        );
      }}
    >
      {children}
    </ErrorBoundary>
  );
}

// --- Strategy 2: State-clearing recovery ---
// When an error is likely caused by corrupted state, clear it and re-render
function StateRecoveryBoundary({ children, clearState }) {
  return (
    <ErrorBoundary
      fallbackRender={({ error, resetErrorBoundary }) => (
        <div role="alert">
          <h3>This section encountered a problem</h3>
          <p>{error.message}</p>
          <button
            onClick={() => {
              // Clear potentially corrupted state
              clearState();
              // Also clear relevant localStorage
              Object.keys(localStorage).forEach((key) => {
                if (key.startsWith('cache_')) localStorage.removeItem(key);
              });
              resetErrorBoundary();
            }}
          >
            Clear Data & Retry
          </button>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
}

// --- Strategy 3: Guided recovery flow ---
function GuidedRecoveryFallback({ error, resetErrorBoundary }) {
  const [step, setStep] = useState('identify');

  const recoverySteps = {
    identify: (
      <div>
        <h3>Something went wrong</h3>
        <p>Let's try to fix this. What were you doing?</p>
        <button onClick={() => setStep('retry')}>I was browsing</button>
        <button onClick={() => setStep('save')}>I was editing data</button>
      </div>
    ),
    retry: (
      <div>
        <p>Let's try loading the page again.</p>
        <button onClick={resetErrorBoundary}>Reload Section</button>
      </div>
    ),
    save: (
      <div>
        <p>Your unsaved changes may have been preserved in a draft.</p>
        <button onClick={() => { recoverDraft(); resetErrorBoundary(); }}>
          Recover Draft & Retry
        </button>
        <button onClick={resetErrorBoundary}>Discard & Retry</button>
      </div>
    ),
  };

  return <div className="guided-recovery" role="alert">{recoverySteps[step]}</div>;
}

// Usage
function ProductEditor() {
  const queryClient = useQueryClient();

  return (
    <AutoRetryBoundary maxRetries={2}>
      <StateRecoveryBoundary
        clearState={() => queryClient.removeQueries({ queryKey: ['product'] })}
      >
        <ProductForm />
      </StateRecoveryBoundary>
    </AutoRetryBoundary>
  );
}
```

Recovery strategy decision tree:
- **Transient error** (network timeout, server 503) → automatic retry with backoff.
- **Stale/corrupted state** (stale cache, bad local storage) → clear state and retry.
- **User-action error** (form submission failed) → show the form again with preserved input.
- **Persistent error** (500 on every retry, malformed data) → show guided recovery, offer to navigate away, and report to monitoring.

---

### Q15. How do you create custom error classes for React applications?

**Answer:**

Custom error classes let you carry structured metadata through your error-handling layers — making it possible to render different fallback UIs, choose different recovery strategies, and send richer data to your monitoring service based on the **type** of error. In a production React app, you typically define a hierarchy of error classes that cover your domain.

```jsx
// src/errors/index.js

// Base application error — all custom errors extend this
export class AppError extends Error {
  constructor(message, { code, statusCode, context, isRetryable = false } = {}) {
    super(message);
    this.name = 'AppError';
    this.code = code;               // Machine-readable error code
    this.statusCode = statusCode;    // HTTP status if applicable
    this.context = context;          // Arbitrary context object
    this.isRetryable = isRetryable;  // Can this error be resolved by retrying?
    this.timestamp = new Date().toISOString();

    // Maintains proper stack trace in V8 engines
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

// Network/API errors
export class ApiError extends AppError {
  constructor(message, { statusCode, endpoint, method, responseBody, ...rest } = {}) {
    super(message, { statusCode, isRetryable: statusCode >= 500, ...rest });
    this.name = 'ApiError';
    this.endpoint = endpoint;
    this.method = method;
    this.responseBody = responseBody;
  }

  static async fromResponse(response, method) {
    let body;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    return new ApiError(
      body?.message || `API request failed: ${response.status} ${response.statusText}`,
      {
        statusCode: response.status,
        endpoint: response.url,
        method,
        responseBody: body,
        code: body?.code || `HTTP_${response.status}`,
      }
    );
  }
}

// Authentication errors
export class AuthError extends AppError {
  constructor(message, opts = {}) {
    super(message, { code: 'AUTH_ERROR', ...opts });
    this.name = 'AuthError';
  }
}

// Validation errors (e.g., form submission with bad data)
export class ValidationError extends AppError {
  constructor(message, { fields = {}, ...rest } = {}) {
    super(message, { code: 'VALIDATION_ERROR', isRetryable: true, ...rest });
    this.name = 'ValidationError';
    this.fields = fields; // { fieldName: 'error message' }
  }
}

// --- Using custom errors in an API client ---
export async function apiClient(endpoint, options = {}) {
  const { method = 'GET', body, ...fetchOptions } = options;

  const response = await fetch(`/api${endpoint}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
    ...fetchOptions,
  });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new AuthError('Your session has expired. Please log in again.', {
        statusCode: response.status,
      });
    }
    throw await ApiError.fromResponse(response, method);
  }

  return response.json();
}

// --- Using custom errors in an Error Boundary fallback ---
import { ApiError, AuthError, ValidationError } from '../errors';

function SmartErrorFallback({ error, resetErrorBoundary }) {
  // Different UI for different error types
  if (error instanceof AuthError) {
    return (
      <div role="alert" className="auth-error">
        <h3>Session Expired</h3>
        <p>{error.message}</p>
        <button onClick={() => (window.location.href = '/login')}>Log In</button>
      </div>
    );
  }

  if (error instanceof ApiError && error.isRetryable) {
    return (
      <div role="alert" className="retryable-error">
        <h3>Temporary Server Issue</h3>
        <p>The server is having trouble. This usually resolves quickly.</p>
        <button onClick={resetErrorBoundary}>Retry</button>
      </div>
    );
  }

  if (error instanceof ValidationError) {
    return (
      <div role="alert" className="validation-error">
        <h3>Invalid Data</h3>
        <ul>
          {Object.entries(error.fields).map(([field, msg]) => (
            <li key={field}><strong>{field}</strong>: {msg}</li>
          ))}
        </ul>
        <button onClick={resetErrorBoundary}>Fix & Retry</button>
      </div>
    );
  }

  // Unknown error — generic fallback
  return (
    <div role="alert" className="unknown-error">
      <h3>Something went wrong</h3>
      <p>An unexpected error occurred. Our team has been notified.</p>
      <button onClick={resetErrorBoundary}>Try Again</button>
    </div>
  );
}
```

Benefits of custom error classes:
- **Type-safe error handling** — `instanceof` checks enable different fallback UIs.
- **Structured metadata** — `isRetryable`, `statusCode`, `fields` drive recovery logic.
- **Monitoring enrichment** — send `error.code`, `error.endpoint`, `error.method` as Sentry tags.
- **Factory methods** — `ApiError.fromResponse()` centralizes HTTP error parsing.

---

### Q16. How do Error Boundaries work with React Router v6 (errorElement)?

**Answer:**

React Router v6.4+ introduced a built-in error handling mechanism via the `errorElement` property on route definitions. When a route's `loader`, `action`, or the component itself throws an error, React Router catches it and renders the `errorElement` instead of the regular `element`. Inside the error element, you use the `useRouteError()` hook to access the thrown error. This is conceptually similar to an Error Boundary but is integrated into the routing layer and also catches data-loading errors (which happen **before** the component renders).

```jsx
import {
  createBrowserRouter,
  RouterProvider,
  useRouteError,
  isRouteErrorResponse,
  Outlet,
  Link,
  useNavigate,
} from 'react-router-dom';

// --- Route-level error element ---
function RouteErrorPage() {
  const error = useRouteError();
  const navigate = useNavigate();

  // React Router wraps thrown Response objects in a special format
  if (isRouteErrorResponse(error)) {
    // Handle HTTP-style errors thrown from loaders/actions
    if (error.status === 404) {
      return (
        <div className="error-page">
          <h1>404 — Page Not Found</h1>
          <p>The page you're looking for doesn't exist.</p>
          <Link to="/">Go Home</Link>
        </div>
      );
    }
    if (error.status === 403) {
      return (
        <div className="error-page">
          <h1>Access Denied</h1>
          <p>You don't have permission to view this page.</p>
          <button onClick={() => navigate(-1)}>Go Back</button>
        </div>
      );
    }
    return (
      <div className="error-page">
        <h1>{error.status} — {error.statusText}</h1>
        <p>{error.data?.message || 'Something went wrong.'}</p>
      </div>
    );
  }

  // Handle regular JavaScript errors
  return (
    <div className="error-page">
      <h1>Unexpected Error</h1>
      <p>{error?.message || 'An unknown error occurred.'}</p>
      <div className="error-actions">
        <button onClick={() => navigate(0)}>Reload Page</button>
        <Link to="/">Go Home</Link>
      </div>
      {process.env.NODE_ENV === 'development' && (
        <pre className="error-stack">{error?.stack}</pre>
      )}
    </div>
  );
}

// --- Root error boundary (catches errors in the layout itself) ---
function RootErrorPage() {
  const error = useRouteError();
  return (
    <div className="root-error">
      <h1>Application Error</h1>
      <p>Something went critically wrong.</p>
      <button onClick={() => window.location.reload()}>Reload</button>
    </div>
  );
}

// --- Loaders that throw structured errors ---
async function userLoader({ params }) {
  const res = await fetch(`/api/users/${params.userId}`);
  if (res.status === 404) {
    throw new Response('User not found', { status: 404 });
  }
  if (!res.ok) {
    throw new Response('Failed to load user', { status: res.status });
  }
  return res.json();
}

async function ordersLoader() {
  const res = await fetch('/api/orders');
  if (!res.ok) {
    throw new Response(JSON.stringify({ message: 'Orders service unavailable' }), {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  return res.json();
}

// --- Router configuration ---
const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <RootErrorPage />, // Catches errors in the root layout
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'users/:userId',
        element: <UserPage />,
        loader: userLoader,
        errorElement: <RouteErrorPage />, // Scoped to this route
      },
      {
        path: 'orders',
        element: <OrdersPage />,
        loader: ordersLoader,
        errorElement: <RouteErrorPage />,
      },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}
```

Key differences between `errorElement` and traditional Error Boundaries:
- **`errorElement` catches loader/action errors** — these happen before the component renders, so a traditional Error Boundary would never see them.
- **`errorElement` is scoped to route segments** — an error in a child route shows the child's `errorElement` while the parent layout (and its navigation) stays intact.
- **Error Boundaries still matter** — for runtime render errors within a route component (not from loaders), you may still want `<ErrorBoundary>` wrappers inside the route's component tree.
- In practice, use **both**: `errorElement` for route/loader errors and `<ErrorBoundary>` for widget-level render errors within a page.

---

### Q17. How should you differentiate between user-facing error messages and developer errors?

**Answer:**

A core principle of production error handling is that **users should never see technical error details** (stack traces, HTTP status codes, raw exception messages) and **developers should never lose them**. This requires a separation layer between the raw error and what the user sees.

The approach involves: (1) custom error classes that carry a user-friendly message alongside technical details, (2) a mapping layer that translates error codes to localized user messages, and (3) logging the full technical error to monitoring while displaying only the friendly message.

```jsx
// src/errors/messages.js

// Map error codes to user-facing messages
const USER_ERROR_MESSAGES = {
  NETWORK_ERROR: 'Please check your internet connection and try again.',
  TIMEOUT: 'The request took too long. Please try again.',
  AUTH_EXPIRED: 'Your session has expired. Please log in again.',
  FORBIDDEN: 'You don't have permission to perform this action.',
  NOT_FOUND: 'The item you're looking for could not be found.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
  VALIDATION_FAILED: 'Some of the provided information is invalid.',
  SERVER_ERROR: 'We're experiencing technical difficulties. Please try again later.',
  MAINTENANCE: 'The system is undergoing scheduled maintenance.',
  DEFAULT: 'Something unexpected happened. Please try again.',
};

export function getUserMessage(error) {
  // Custom errors with explicit user messages
  if (error.userMessage) return error.userMessage;

  // Map known error codes
  if (error.code && USER_ERROR_MESSAGES[error.code]) {
    return USER_ERROR_MESSAGES[error.code];
  }

  // Map HTTP status codes
  if (error.statusCode) {
    const statusMap = {
      401: USER_ERROR_MESSAGES.AUTH_EXPIRED,
      403: USER_ERROR_MESSAGES.FORBIDDEN,
      404: USER_ERROR_MESSAGES.NOT_FOUND,
      408: USER_ERROR_MESSAGES.TIMEOUT,
      429: USER_ERROR_MESSAGES.RATE_LIMITED,
      503: USER_ERROR_MESSAGES.MAINTENANCE,
    };
    if (statusMap[error.statusCode]) return statusMap[error.statusCode];
    if (error.statusCode >= 500) return USER_ERROR_MESSAGES.SERVER_ERROR;
  }

  // Network errors
  if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
    return USER_ERROR_MESSAGES.NETWORK_ERROR;
  }

  // Default — never expose the raw error.message to users
  return USER_ERROR_MESSAGES.DEFAULT;
}

// --- Error display component that enforces the separation ---
import { getUserMessage } from '../errors/messages';

function ErrorDisplay({ error, onRetry, onDismiss }) {
  const userMessage = getUserMessage(error);
  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div role="alert" className="error-display">
      {/* User-facing: friendly, actionable */}
      <div className="error-display__user">
        <p className="error-display__message">{userMessage}</p>
        <div className="error-display__actions">
          {error.isRetryable !== false && onRetry && (
            <button onClick={onRetry}>Try Again</button>
          )}
          {onDismiss && (
            <button onClick={onDismiss} className="secondary">Dismiss</button>
          )}
        </div>
      </div>

      {/* Developer-facing: only visible in development */}
      {isDev && (
        <details className="error-display__dev">
          <summary>Developer Details</summary>
          <table>
            <tbody>
              <tr><td>Name</td><td>{error.name}</td></tr>
              <tr><td>Message</td><td>{error.message}</td></tr>
              <tr><td>Code</td><td>{error.code || '—'}</td></tr>
              <tr><td>Status</td><td>{error.statusCode || '—'}</td></tr>
            </tbody>
          </table>
          <pre>{error.stack}</pre>
        </details>
      )}
    </div>
  );
}

// --- Usage in an Error Boundary ---
import { ErrorBoundary } from 'react-error-boundary';

function AppErrorFallback({ error, resetErrorBoundary }) {
  // Log the FULL error for developers via monitoring
  React.useEffect(() => {
    reportToSentry(error); // Full error object with stack, code, metadata
  }, [error]);

  return (
    <ErrorDisplay
      error={error}
      onRetry={error.isRetryable !== false ? resetErrorBoundary : undefined}
    />
  );
}

function App() {
  return (
    <ErrorBoundary FallbackComponent={AppErrorFallback}>
      <AppContent />
    </ErrorBoundary>
  );
}
```

The principle: the **raw error object** flows to monitoring (Sentry sees everything), while the **user sees only a curated, friendly message** determined by the error's code or type. Never pass `error.message` directly to the user in production — it can contain SQL fragments, file paths, internal API URLs, or other sensitive information.

---

### Q18. How do Error Boundaries interact with React 18's concurrent features?

**Answer:**

React 18 introduced concurrent rendering features — `startTransition`, `useDeferredValue`, `useTransition`, and Suspense for data fetching — which change how React schedules work and, consequently, how errors propagate. The key interactions are:

1. **Transitions are interruptible and rollback-safe**: If a transition update causes an error, React can discard the in-progress render and keep showing the previous (pre-transition) UI instead of immediately crashing. The Error Boundary still catches the error, but the timing and user experience differ from synchronous rendering.

2. **`startTransition` keeps the old UI on error**: When an error occurs during a transition render, React may choose to keep the current UI visible while reporting the error to the boundary. This prevents flashing — the user doesn't see a fallback for a split second before recovery.

3. **Suspense + Error Boundaries in concurrent mode**: In concurrent rendering, React may start rendering a component, suspend it, then restart. If the restarted render throws an error, the Error Boundary catches it. The interplay is well-defined but requires understanding that render is no longer a single pass.

```jsx
import React, {
  useState,
  useTransition,
  Suspense,
  startTransition,
} from 'react';
import { ErrorBoundary, useErrorBoundary } from 'react-error-boundary';

// --- startTransition preserves previous UI on error ---
function SearchWithTransition() {
  const [query, setQuery] = useState('');
  const [isPending, startTransition] = useTransition();
  const [searchQuery, setSearchQuery] = useState('');
  const { showBoundary } = useErrorBoundary();

  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value); // Urgent: update input immediately

    startTransition(() => {
      // Non-urgent: update search results
      // If this causes an error in SearchResults, React keeps the
      // previous search results visible instead of immediately
      // showing the Error Boundary fallback
      setSearchQuery(value);
    });
  };

  return (
    <div>
      <input
        value={query}
        onChange={handleSearch}
        placeholder="Search..."
        style={{ opacity: isPending ? 0.7 : 1 }}
      />
      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <div role="alert">
            <p>Search failed: {error.message}</p>
            <button onClick={resetErrorBoundary}>Retry</button>
          </div>
        )}
        resetKeys={[searchQuery]}
      >
        <Suspense fallback={<div>Loading results...</div>}>
          <SearchResults query={searchQuery} />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}

// --- Error during transition: React rolls back to previous state ---
function TabsWithTransition() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isPending, startTransition] = useTransition();

  const handleTabChange = (tabId) => {
    startTransition(() => {
      // If the new tab component throws during render,
      // React keeps the previous tab visible and reports
      // the error to the Error Boundary
      setActiveTab(tabId);
    });
  };

  return (
    <div>
      <nav className="tabs" style={{ opacity: isPending ? 0.7 : 1 }}>
        {['overview', 'analytics', 'settings'].map((tab) => (
          <button
            key={tab}
            onClick={() => handleTabChange(tab)}
            className={activeTab === tab ? 'active' : ''}
          >
            {tab}
          </button>
        ))}
      </nav>

      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <div role="alert">
            <p>Tab "{activeTab}" failed to load</p>
            <p>{error.message}</p>
            <button onClick={() => { setActiveTab('overview'); resetErrorBoundary(); }}>
              Go to Overview
            </button>
          </div>
        )}
        resetKeys={[activeTab]}
      >
        <Suspense fallback={<TabSkeleton />}>
          <TabContent tabId={activeTab} />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}

// --- Concurrent rendering and automatic batching ---
// In React 18, state updates inside promises, setTimeout, and native
// event handlers are also batched. This means errors thrown during
// these batched renders are still caught by Error Boundaries.

function ConcurrentErrorExample() {
  const [items, setItems] = useState([]);
  const { showBoundary } = useErrorBoundary();

  const loadMore = async () => {
    try {
      const newItems = await fetchItems();

      // In React 18, this state update is batched even though
      // it's inside an async function
      startTransition(() => {
        setItems((prev) => [...prev, ...newItems]);
      });
    } catch (error) {
      // If the fetchItems fails, propagate to boundary
      showBoundary(error);
    }
  };

  return (
    <div>
      {items.map((item) => (
        <ItemCard key={item.id} item={item} />
      ))}
      <button onClick={loadMore}>Load More</button>
    </div>
  );
}
```

Important considerations for concurrent React + Error Boundaries:
- **Error Boundaries still work the same way** — they catch render-phase errors regardless of whether the render was synchronous or concurrent.
- **Transitions improve the error UX** — the user sees the previous working UI for longer, rather than an immediate flash to the fallback.
- **`resetKeys` become more important** — since transitions can be interrupted, the boundary needs clear signals for when to reset.
- **Suspense integration is first-class** — React 18 treats "suspended" (promise thrown) and "errored" (error thrown) as two distinct states, with Suspense handling the former and Error Boundaries handling the latter.

---

### Q19. How do you test Error Boundaries in a React application?

**Answer:**

Testing Error Boundaries requires verifying three things: (1) the boundary catches errors and renders the fallback, (2) the boundary reports errors correctly (logging/monitoring), and (3) the reset mechanism works. React Testing Library is the standard tool, and you need to suppress React's console.error output during intentional error tests to keep test output clean.

```jsx
// src/components/__tests__/ErrorBoundary.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from 'react-error-boundary';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// --- Test helper: a component that throws on demand ---
function ThrowingComponent({ shouldThrow = false, errorMessage = 'Test error' }) {
  if (shouldThrow) {
    throw new Error(errorMessage);
  }
  return <div>Content rendered successfully</div>;
}

// --- Test helper: async component that throws ---
function AsyncThrowingComponent({ shouldThrow }) {
  const { showBoundary } = useErrorBoundary();

  React.useEffect(() => {
    if (shouldThrow) {
      // Simulating an async error
      setTimeout(() => showBoundary(new Error('Async error')), 0);
    }
  }, [shouldThrow, showBoundary]);

  return <div>Async content</div>;
}

// Fallback component used in tests
function TestFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert">
      <p>Error: {error.message}</p>
      <button onClick={resetErrorBoundary}>Reset</button>
    </div>
  );
}

describe('ErrorBoundary', () => {
  // Suppress React's console.error for intentional error tests
  const originalConsoleError = console.error;
  beforeEach(() => {
    console.error = vi.fn();
  });
  afterEach(() => {
    console.error = originalConsoleError;
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary FallbackComponent={TestFallback}>
        <ThrowingComponent shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Content rendered successfully')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('renders fallback UI when a child throws during render', () => {
    render(
      <ErrorBoundary FallbackComponent={TestFallback}>
        <ThrowingComponent shouldThrow={true} errorMessage="Render crash!" />
      </ErrorBoundary>
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Error: Render crash!')).toBeInTheDocument();
    expect(screen.queryByText('Content rendered successfully')).not.toBeInTheDocument();
  });

  it('calls onError when an error is caught', () => {
    const onError = vi.fn();

    render(
      <ErrorBoundary FallbackComponent={TestFallback} onError={onError}>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'Test error' }),
      expect.objectContaining({ componentStack: expect.any(String) })
    );
  });

  it('recovers when the reset button is clicked', () => {
    const { rerender } = render(
      <ErrorBoundary FallbackComponent={TestFallback}>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    // Verify fallback is showing
    expect(screen.getByRole('alert')).toBeInTheDocument();

    // Click reset, then re-render with shouldThrow=false
    // (In a real app, the reset would re-render children; here we
    // simulate fixing the error condition)
    rerender(
      <ErrorBoundary FallbackComponent={TestFallback}>
        <ThrowingComponent shouldThrow={false} />
      </ErrorBoundary>
    );

    fireEvent.click(screen.getByText('Reset'));

    // After reset, children should render again
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('resets automatically when resetKeys change', () => {
    const { rerender } = render(
      <ErrorBoundary FallbackComponent={TestFallback} resetKeys={['key1']}>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();

    // Change resetKey and fix the error condition
    rerender(
      <ErrorBoundary FallbackComponent={TestFallback} resetKeys={['key2']}>
        <ThrowingComponent shouldThrow={false} />
      </ErrorBoundary>
    );

    // Boundary auto-resets due to resetKeys change
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByText('Content rendered successfully')).toBeInTheDocument();
  });

  it('renders correct fallback based on error type', () => {
    function SmartFallback({ error }) {
      if (error.code === 'AUTH') return <p>Please log in</p>;
      return <p>Generic error</p>;
    }

    function AuthError() {
      const err = new Error('Unauthorized');
      err.code = 'AUTH';
      throw err;
    }

    render(
      <ErrorBoundary FallbackComponent={SmartFallback}>
        <AuthError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Please log in')).toBeInTheDocument();
  });
});
```

Testing best practices:
- **Always suppress `console.error`** during intentional throw tests — React logs errors loudly and it clutters test output.
- **Test the fallback content** — ensure the user sees the right message.
- **Test the `onError` callback** — ensure your monitoring integration receives the error with the component stack.
- **Test reset/recovery** — ensure clicking "Retry" re-renders children.
- **Test `resetKeys`** — ensure automatic reset works.
- **Test error type differentiation** — ensure different error types render different fallbacks.

---

### Q20. How do you build a comprehensive production error handling system combining boundaries, monitoring, recovery, and user feedback?

**Answer:**

A production-grade error handling system is an architecture, not a single component. It combines five layers: (1) an Error Boundary hierarchy with contextual fallbacks, (2) a centralized error reporting service, (3) automatic and user-initiated recovery mechanisms, (4) user feedback collection, and (5) global safety nets. Below is a complete implementation.

```jsx
// ============================================================
// LAYER 1: Centralized Error Reporter
// ============================================================
// src/errorHandling/ErrorReporter.js

import * as Sentry from '@sentry/react';

class ErrorReporter {
  static instance = null;
  errorBuffer = [];
  flushInterval = null;

  static getInstance() {
    if (!ErrorReporter.instance) {
      ErrorReporter.instance = new ErrorReporter();
    }
    return ErrorReporter.instance;
  }

  init({ dsn, environment, release, userId }) {
    Sentry.init({
      dsn,
      environment,
      release,
      integrations: [new Sentry.BrowserTracing(), new Sentry.Replay()],
      tracesSampleRate: environment === 'production' ? 0.1 : 1.0,
      replaysOnErrorSampleRate: 1.0,
    });

    if (userId) {
      Sentry.setUser({ id: userId });
    }

    // Batch non-critical errors to reduce network requests
    this.flushInterval = setInterval(() => this.flushBuffer(), 30000);
  }

  report(error, context = {}) {
    const enrichedContext = {
      ...context,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    if (context.severity === 'critical') {
      // Critical errors are sent immediately
      this.sendToSentry(error, enrichedContext);
    } else {
      // Non-critical errors are buffered
      this.errorBuffer.push({ error, context: enrichedContext });
    }

    // Always log in development
    if (process.env.NODE_ENV === 'development') {
      console.group(`[ErrorReporter] ${context.layer || 'unknown'}`);
      console.error(error);
      console.table(enrichedContext);
      console.groupEnd();
    }
  }

  sendToSentry(error, context) {
    Sentry.withScope((scope) => {
      Object.entries(context).forEach(([key, value]) => {
        if (typeof value === 'string' || typeof value === 'number') {
          scope.setTag(key, value);
        } else {
          scope.setExtra(key, value);
        }
      });
      Sentry.captureException(error);
    });
  }

  flushBuffer() {
    if (this.errorBuffer.length === 0) return;
    const errors = [...this.errorBuffer];
    this.errorBuffer = [];
    errors.forEach(({ error, context }) => this.sendToSentry(error, context));
  }

  destroy() {
    clearInterval(this.flushInterval);
    this.flushBuffer();
  }
}

export const errorReporter = ErrorReporter.getInstance();

// ============================================================
// LAYER 2: Global Safety Net
// ============================================================
// src/errorHandling/globalHandlers.js

export function installGlobalHandlers(reporter) {
  window.addEventListener('error', (event) => {
    if (!event.filename || event.filename.includes('extensions://')) return;
    reporter.report(event.error || new Error(event.message), {
      layer: 'global_error',
      source: event.filename,
      line: event.lineno,
      severity: 'critical',
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    reporter.report(event.reason || new Error('Unhandled rejection'), {
      layer: 'unhandled_rejection',
      severity: 'critical',
    });
  });
}

// ============================================================
// LAYER 3: Configurable Error Boundary with built-in reporting
// ============================================================
// src/errorHandling/AppErrorBoundary.jsx

import React, { Component, createContext, useContext, useCallback } from 'react';
import { errorReporter } from './ErrorReporter';
import { getUserMessage } from '../errors/messages';

// Context for nested boundaries to communicate with ancestors
const ErrorContext = createContext({
  reportError: () => {},
  addRecoveryAction: () => {},
});

export function useErrorReporting() {
  return useContext(ErrorContext);
}

export class AppErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });

    // Report to centralized error reporter
    errorReporter.report(error, {
      layer: 'error_boundary',
      boundary: this.props.name || 'unnamed',
      componentStack: errorInfo.componentStack,
      severity: this.props.level === 'root' ? 'critical' : 'warning',
    });

    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState((prev) => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prev.retryCount + 1,
    }));
    this.props.onReset?.();
  };

  render() {
    const contextValue = {
      reportError: (error, context) => errorReporter.report(error, context),
    };

    if (this.state.hasError) {
      const { error, retryCount } = this.state;
      const { FallbackComponent, level = 'widget' } = this.props;

      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={error}
            resetErrorBoundary={this.handleReset}
            retryCount={retryCount}
            level={level}
          />
        );
      }

      return (
        <DefaultFallback
          error={error}
          resetErrorBoundary={this.handleReset}
          retryCount={retryCount}
          level={level}
        />
      );
    }

    return (
      <ErrorContext.Provider value={contextValue}>
        {this.props.children}
      </ErrorContext.Provider>
    );
  }
}

// ============================================================
// LAYER 4: Tiered Fallback Components
// ============================================================

function DefaultFallback({ error, resetErrorBoundary, retryCount, level }) {
  const userMessage = getUserMessage(error);

  if (level === 'root') {
    return <RootFallback message={userMessage} onReload={() => window.location.reload()} />;
  }
  if (level === 'page') {
    return (
      <PageFallback
        message={userMessage}
        onRetry={retryCount < 3 ? resetErrorBoundary : undefined}
        onGoHome={() => (window.location.href = '/')}
      />
    );
  }
  // Widget level
  return (
    <WidgetFallback
      message={userMessage}
      onRetry={retryCount < 5 ? resetErrorBoundary : undefined}
    />
  );
}

function RootFallback({ message, onReload }) {
  return (
    <div className="fallback fallback--root" role="alert">
      <h1>Application Error</h1>
      <p>{message}</p>
      <button onClick={onReload}>Reload Application</button>
      <FeedbackForm context="root_crash" />
    </div>
  );
}

function PageFallback({ message, onRetry, onGoHome }) {
  return (
    <div className="fallback fallback--page" role="alert">
      <h2>This page isn't working</h2>
      <p>{message}</p>
      <div className="fallback__actions">
        {onRetry && <button onClick={onRetry}>Try Again</button>}
        <button onClick={onGoHome}>Go to Home</button>
      </div>
    </div>
  );
}

function WidgetFallback({ message, onRetry }) {
  return (
    <div className="fallback fallback--widget" role="alert">
      <span>{message}</span>
      {onRetry && <button onClick={onRetry}>Retry</button>}
    </div>
  );
}

// ============================================================
// LAYER 5: User Feedback Collection
// ============================================================
// src/errorHandling/FeedbackForm.jsx

function FeedbackForm({ context }) {
  const [feedback, setFeedback] = React.useState('');
  const [submitted, setSubmitted] = React.useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Attach feedback to the most recent Sentry event
      const eventId = Sentry.lastEventId();
      if (eventId) {
        Sentry.captureUserFeedback({
          event_id: eventId,
          comments: feedback,
          name: 'Anonymous User',
          email: 'n/a',
        });
      }
      // Also send to your own backend for aggregation
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feedback,
          context,
          url: window.location.href,
          timestamp: new Date().toISOString(),
        }),
      });
      setSubmitted(true);
    } catch {
      // Don't let the feedback form itself crash
      setSubmitted(true);
    }
  };

  if (submitted) return <p>Thank you for your feedback!</p>;

  return (
    <form onSubmit={handleSubmit} className="feedback-form">
      <label htmlFor="feedback">What were you doing when this happened?</label>
      <textarea
        id="feedback"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        rows={3}
        placeholder="Describe what you were doing..."
      />
      <button type="submit" disabled={!feedback.trim()}>
        Send Feedback
      </button>
    </form>
  );
}

// ============================================================
// BRINGING IT ALL TOGETHER — App Entry Point
// ============================================================
// src/index.jsx

import { createRoot } from 'react-dom/client';
import { errorReporter } from './errorHandling/ErrorReporter';
import { installGlobalHandlers } from './errorHandling/globalHandlers';
import { AppErrorBoundary } from './errorHandling/AppErrorBoundary';

// Step 1: Initialize monitoring BEFORE React renders
errorReporter.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.REACT_APP_VERSION,
});

// Step 2: Install global safety nets
installGlobalHandlers(errorReporter);

// Step 3: Render with layered boundaries
const root = createRoot(document.getElementById('root'));
root.render(
  <AppErrorBoundary name="root" level="root">
    <App />
  </AppErrorBoundary>
);

// Inside App.jsx — page and widget level boundaries
function App() {
  return (
    <Router>
      <AppErrorBoundary name="page-dashboard" level="page">
        <DashboardPage />
      </AppErrorBoundary>
    </Router>
  );
}

function DashboardPage() {
  return (
    <div className="dashboard">
      <AppErrorBoundary name="widget-chart" level="widget">
        <RevenueChart />
      </AppErrorBoundary>
      <AppErrorBoundary name="widget-users" level="widget">
        <ActiveUsers />
      </AppErrorBoundary>
    </div>
  );
}
```

**Architecture summary:**

```
┌─────────────────────────────────────────────────────────────┐
│                   Error Handling Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─── Global Handlers ──────────────────────────────────┐   │
│  │  window.onerror + unhandledrejection                 │   │
│  │  → catches anything that escapes all other layers    │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                           │
│  ┌─── Root ErrorBoundary ───────────────────────────────┐   │
│  │  level="root" → RootFallback + FeedbackForm          │   │
│  │                                                      │   │
│  │  ┌─── Page ErrorBoundary ────────────────────────┐   │   │
│  │  │  level="page" → PageFallback (retry + home)   │   │   │
│  │  │                                               │   │   │
│  │  │  ┌─── Widget ErrorBoundary ───────────────┐   │   │   │
│  │  │  │  level="widget" → WidgetFallback       │   │   │   │
│  │  │  │                                        │   │   │   │
│  │  │  │  ┌─── try/catch in handlers ───────┐   │   │   │   │
│  │  │  │  │  + showBoundary for propagation  │   │   │   │   │
│  │  │  │  └─────────────────────────────────┘   │   │   │   │
│  │  │  └────────────────────────────────────────┘   │   │   │
│  │  └───────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                 │                                           │
│  ┌─── ErrorReporter (Sentry) ───────────────────────────┐   │
│  │  All layers feed into centralized error reporting     │   │
│  │  + User feedback collection                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

This architecture ensures:
- **No white screens** — every crash shows a meaningful fallback.
- **Minimal blast radius** — widget errors don't take down pages; page errors don't take down the app.
- **Full visibility** — every error reaches Sentry with rich context (layer, boundary name, component stack, user session).
- **Recovery** — automatic retries, user-initiated retries, and state-clearing recovery.
- **User voice** — feedback forms on critical errors help reproduce issues.
- **Defense in depth** — five layers ensure no error goes unhandled.

---

*End of Topic 9: Error Boundaries & Error Handling in React 18*
