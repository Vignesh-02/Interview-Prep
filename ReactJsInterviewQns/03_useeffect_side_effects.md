# useEffect and Side Effects in React 18 — Interview Questions

## Topic Introduction

In React's functional component model, **side effects** are any operations that reach outside the pure rendering cycle — fetching data from an API, subscribing to a WebSocket, manipulating the DOM directly, setting timers, or writing to `localStorage`. React components are meant to be pure functions of `(props, state) → JSX`, so anything that doesn't fit that description is a side effect. The `useEffect` hook is React's designated mechanism for synchronising your component with these external systems. Introduced in React 16.8 and refined in React 18, it replaces the class-based `componentDidMount`, `componentDidUpdate`, and `componentWillUnmount` lifecycle methods with a single, composable API that encourages thinking in terms of *synchronisation* rather than *lifecycle events*.

`useEffect` accepts two arguments: a **setup function** that contains the side-effect logic (and optionally returns a **cleanup function**), and a **dependency array** that tells React when to re-run the effect. Getting the dependency array right is one of the most common pain points for React developers. An empty array `[]` means "run once after mount," a populated array `[a, b]` means "re-run whenever `a` or `b` changes (by `Object.is` comparison)," and omitting the array entirely means "re-run after every render." Misunderstanding these semantics leads to stale closures, infinite loops, and leaked subscriptions — all of which are favourite topics in senior-level React interviews.

React 18 introduced **Strict Mode double-invocation** in development, which mounts every component twice to surface impure effects and missing cleanup logic. This change caught many teams off guard but ultimately makes applications more resilient. Understanding *why* React does this, and how to write effects that survive a mount → unmount → remount cycle, is essential knowledge for any production React developer. The code below shows the basic anatomy of a `useEffect` call:

```jsx
import { useState, useEffect } from "react";

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Setup: the side effect
    const controller = new AbortController();

    async function fetchUser() {
      try {
        const res = await fetch(`/api/users/${userId}`, {
          signal: controller.signal,
        });
        const data = await res.json();
        setUser(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("Fetch failed:", err);
        }
      }
    }

    fetchUser();

    // Cleanup: runs before re-running or on unmount
    return () => controller.abort();
  }, [userId]); // Dependency array: re-run when userId changes

  if (!user) return <p>Loading…</p>;
  return <h1>{user.name}</h1>;
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is `useEffect` and when does it run?

**Answer:**

`useEffect` is a React hook that lets you perform side effects in function components. A "side effect" is any operation that interacts with something outside React's rendering pipeline — network requests, DOM manipulation, logging, timers, and so on.

By default, the setup function you pass to `useEffect` runs **after React has committed the updated DOM to the screen** — that is, after the browser has painted. This is important: unlike `useLayoutEffect`, it does **not** block the browser from painting, so it is the preferred hook for the majority of side effects that don't need to measure or mutate layout.

The execution timeline for a component render is:

1. React calls your component function (render phase).
2. React updates the DOM.
3. The browser paints the screen.
4. React runs your `useEffect` callbacks.

```jsx
import { useEffect } from "react";

function Logger({ message }) {
  // Runs after every render where `message` has changed
  useEffect(() => {
    console.log("Side effect running. Current message:", message);

    // Optional cleanup — runs before the next effect or on unmount
    return () => {
      console.log("Cleaning up previous effect for message:", message);
    };
  }, [message]);

  return <p>{message}</p>;
}

// Usage:
// <Logger message="Hello" />
// Console (after paint): "Side effect running. Current message: Hello"
//
// If message changes to "World":
// Console: "Cleaning up previous effect for message: Hello"
// Console: "Side effect running. Current message: World"
```

**Key takeaway:** `useEffect` is the standard way to synchronise a React component with an external system. It runs *after* paint, making it non-blocking.

---

### Q2. How does the dependency array control when `useEffect` runs?

**Answer:**

The dependency array is the second argument to `useEffect`. It tells React which values the effect "depends on," and React uses `Object.is` comparison between renders to decide whether the effect should re-run. There are three variants:

| Dependency Array | When Effect Runs |
|---|---|
| `[a, b]` | After mount, then after every render where `a` or `b` changed |
| `[]` | Only once, after the initial mount |
| *(omitted)* | After **every** render |

Omitting the dependency array is rarely what you want in production code — it can cause performance problems and infinite loops.

```jsx
import { useState, useEffect } from "react";

function DependencyDemo() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState("React");

  // 1. Specific dependencies — re-runs only when `count` changes
  useEffect(() => {
    document.title = `Count: ${count}`;
  }, [count]);

  // 2. Empty array — runs once after mount
  useEffect(() => {
    console.log("Component mounted");
    return () => console.log("Component unmounted");
  }, []);

  // 3. No array — runs after every single render (use with caution)
  useEffect(() => {
    console.log("Render happened. count:", count, "name:", name);
  });

  return (
    <div>
      <p>{name}: {count}</p>
      <button onClick={() => setCount((c) => c + 1)}>Increment</button>
      <button onClick={() => setName("React 18")}>Change Name</button>
    </div>
  );
}
```

**Key takeaway:** Always include every reactive value your effect reads in the dependency array. The `react-hooks/exhaustive-deps` ESLint rule enforces this — treat it as a hard requirement, not a suggestion.

---

### Q3. What is the cleanup function in `useEffect` and when does it run?

**Answer:**

The function you optionally **return** from your `useEffect` callback is the cleanup function. React calls it in two situations:

1. **Before re-running the effect** — when a dependency has changed, React runs the *previous* cleanup before the *new* setup.
2. **When the component unmounts** — React runs the cleanup to tear down the effect.

Cleanup is essential for preventing memory leaks. Common cleanup tasks include clearing timers, aborting fetch requests, removing event listeners, and closing WebSocket connections.

```jsx
import { useState, useEffect } from "react";

function WindowWidth() {
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    function handleResize() {
      setWidth(window.innerWidth);
    }

    // Setup: subscribe
    window.addEventListener("resize", handleResize);

    // Cleanup: unsubscribe
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []); // Empty deps — subscribe once, cleanup on unmount

  return <p>Window width: {width}px</p>;
}
```

Without the cleanup, every mount would add another `resize` listener without removing the old one, causing the handler to fire multiple times and eventually degrading performance.

**Key takeaway:** If your effect subscribes to something, sets a timer, or acquires a resource, always return a cleanup function that releases it.

---

### Q4. How do you fetch data with `useEffect`?

**Answer:**

Data fetching is one of the most common uses of `useEffect`. Because `useEffect` callbacks cannot be `async` directly (the return value must be `undefined` or a cleanup function, not a Promise), you define an `async` function *inside* the effect and call it immediately.

A critical detail: you must handle the case where the component unmounts or the dependency changes before the fetch completes. Without this, you risk calling `setState` on an unmounted component (a React warning in React 17 and earlier) or displaying stale data from an earlier request that resolved after a newer one.

```jsx
import { useState, useEffect } from "react";

function ProductList({ categoryId }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false; // simple flag to prevent stale updates

    async function fetchProducts() {
      setLoading(true);
      setError(null);

      try {
        const res = await fetch(`/api/products?category=${categoryId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (!cancelled) {
          setProducts(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchProducts();

    return () => {
      cancelled = true; // cleanup: mark stale
    };
  }, [categoryId]);

  if (loading) return <p>Loading products…</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <ul>
      {products.map((p) => (
        <li key={p.id}>{p.name} — ${p.price}</li>
      ))}
    </ul>
  );
}
```

**Key takeaway:** Never make the `useEffect` callback itself `async`. Define an inner `async` function and call it, and always guard against stale updates in the cleanup.

---

### Q5. What are the Rules of Hooks and why can't `useEffect` be called conditionally?

**Answer:**

The Rules of Hooks are:

1. **Only call hooks at the top level** — not inside loops, conditions, or nested functions.
2. **Only call hooks from React function components or custom hooks** — not from regular JavaScript functions.

React identifies hooks by their **call order** on each render. Internally, React maintains a linked list of hook states. If you wrap a `useEffect` in a condition, the call order can change between renders and React will associate the wrong state with the wrong hook, leading to subtle, hard-to-debug bugs.

```jsx
import { useState, useEffect } from "react";

// ❌ WRONG — conditional hook call
function BadComponent({ shouldFetch }) {
  const [data, setData] = useState(null);

  if (shouldFetch) {
    // This violates Rules of Hooks — hook call order is inconsistent
    useEffect(() => {
      fetch("/api/data")
        .then((res) => res.json())
        .then(setData);
    }, []);
  }

  return <pre>{JSON.stringify(data)}</pre>;
}

// ✅ CORRECT — always call the hook, put the condition inside
function GoodComponent({ shouldFetch }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!shouldFetch) return; // early return inside the effect
    fetch("/api/data")
      .then((res) => res.json())
      .then(setData);
  }, [shouldFetch]);

  return <pre>{JSON.stringify(data)}</pre>;
}
```

The `eslint-plugin-react-hooks` rule `rules-of-hooks` will flag conditional hook calls at lint time.

**Key takeaway:** Always call `useEffect` unconditionally at the top level. Move conditional logic *inside* the effect body.

---

## Intermediate Level (Q6–Q12)

---

### Q6. What is the race condition problem in `useEffect` data fetching, and how does `AbortController` solve it?

**Answer:**

When a dependency changes rapidly (e.g., the user types in a search box), multiple fetch requests fire in sequence. Because network responses can arrive out of order, a *later* request may resolve *before* an earlier one. Without protection, the earlier (stale) response overwrites the more recent (correct) one — this is a **race condition**.

The boolean-flag approach (`let cancelled = false`) prevents calling `setState` with stale data, but it does **not** cancel the in-flight HTTP request. The `AbortController` API solves both problems: it prevents the stale state update *and* cancels the actual network request, saving bandwidth and server resources.

```jsx
import { useState, useEffect } from "react";

function SearchResults({ query }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query) {
      setResults([]);
      return;
    }

    const controller = new AbortController();
    setLoading(true);

    async function search() {
      try {
        const res = await fetch(
          `/api/search?q=${encodeURIComponent(query)}`,
          { signal: controller.signal }
        );
        const data = await res.json();
        setResults(data.items);
      } catch (err) {
        if (err.name === "AbortError") {
          // Request was cancelled — this is expected, do nothing
          return;
        }
        console.error("Search failed:", err);
      } finally {
        setLoading(false);
      }
    }

    search();

    return () => {
      // Cancel the previous request when query changes or component unmounts
      controller.abort();
    };
  }, [query]);

  return (
    <div>
      {loading && <p>Searching…</p>}
      <ul>
        {results.map((item) => (
          <li key={item.id}>{item.title}</li>
        ))}
      </ul>
    </div>
  );
}
```

**Production detail:** In a real application, you would also debounce the search input (see Q17) so you don't fire a request on every keystroke. `AbortController` is the safety net that handles the case where requests still overlap.

**Key takeaway:** Always use `AbortController` when fetching data in `useEffect` to handle race conditions and prevent wasted network traffic.

---

### Q7. What is the difference between `useEffect` and `useLayoutEffect`? When should you use each?

**Answer:**

Both hooks have the same API, but they differ in **timing**:

| Hook | Runs | Blocks Paint? |
|---|---|---|
| `useEffect` | After the browser paints | No |
| `useLayoutEffect` | After DOM mutation but **before** the browser paints | Yes |

`useLayoutEffect` is synchronous with respect to the paint cycle, making it the right choice when you need to read layout (e.g., measure an element's dimensions) and then make a visual correction *before* the user sees the first frame. Using `useEffect` in this scenario would cause a visible flicker because the component renders with incorrect layout, the browser paints it, and *then* the effect corrects it.

```jsx
import { useState, useRef, useLayoutEffect, useEffect } from "react";

function Tooltip({ targetRef, children }) {
  const tooltipRef = useRef(null);
  const [coords, setCoords] = useState({ top: 0, left: 0 });

  // ✅ useLayoutEffect — measure DOM and position before paint
  useLayoutEffect(() => {
    if (!targetRef.current || !tooltipRef.current) return;

    const targetRect = targetRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    setCoords({
      top: targetRect.top - tooltipRect.height - 8,
      left: targetRect.left + (targetRect.width - tooltipRect.width) / 2,
    });
  }, [targetRef]);

  // ✅ useEffect — analytics logging doesn't affect layout
  useEffect(() => {
    console.log("Tooltip displayed at:", coords);
  }, [coords]);

  return (
    <div
      ref={tooltipRef}
      style={{
        position: "fixed",
        top: coords.top,
        left: coords.left,
      }}
    >
      {children}
    </div>
  );
}
```

**Production rule of thumb:**
- Default to `useEffect` for everything.
- Use `useLayoutEffect` only when you need to measure the DOM and make a visual correction before the user sees the result (tooltips, popovers, animations, scroll restoration).
- Be aware that `useLayoutEffect` emits a warning during server-side rendering because there is no DOM to measure.

**Key takeaway:** `useLayoutEffect` runs synchronously before paint — use it only when you need to prevent visual flicker caused by layout measurement.

---

### Q8. Should you use multiple `useEffect` calls or combine everything into one?

**Answer:**

You should **separate concerns into multiple `useEffect` calls**. This is one of the core design principles behind hooks: each effect should represent a single synchronisation concern. Combining unrelated logic into a single `useEffect` creates artificial coupling, making code harder to reason about and maintain.

```jsx
import { useState, useEffect } from "react";

// ❌ BAD — unrelated concerns mixed into one effect
function UserDashboard({ userId }) {
  const [user, setUser] = useState(null);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Concern 1: Fetch user data
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then(setUser);

    // Concern 2: Set up notification polling (unrelated to user fetch)
    const interval = setInterval(() => {
      fetch("/api/notifications")
        .then((res) => res.json())
        .then(setNotifications);
    }, 30000);

    // Concern 3: Analytics (unrelated to both)
    window.analytics.page("Dashboard");

    return () => clearInterval(interval);
    // userId change re-runs EVERYTHING, including polling setup & analytics
  }, [userId]);

  return <div>{/* ... */}</div>;
}

// ✅ GOOD — separate effects for separate concerns
function UserDashboardRefactored({ userId }) {
  const [user, setUser] = useState(null);
  const [notifications, setNotifications] = useState([]);

  // Effect 1: Fetch user data (depends on userId)
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then((res) => res.json())
      .then(setUser)
      .catch((err) => {
        if (err.name !== "AbortError") console.error(err);
      });
    return () => controller.abort();
  }, [userId]);

  // Effect 2: Poll notifications (independent of userId)
  useEffect(() => {
    const interval = setInterval(() => {
      fetch("/api/notifications")
        .then((res) => res.json())
        .then(setNotifications);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Effect 3: Page analytics (runs once)
  useEffect(() => {
    window.analytics.page("Dashboard");
  }, []);

  return <div>{/* ... */}</div>;
}
```

**Key takeaway:** One effect per concern. Each `useEffect` should synchronise your component with exactly one external system. This makes effects independently testable, independently re-runnable, and easier to maintain.

---

### Q9. How does React 18 Strict Mode double-invocation work and why does it matter?

**Answer:**

In development mode, React 18's `<StrictMode>` intentionally **mounts every component twice**: it runs setup → cleanup → setup for every effect. This simulates a fast component remount, which can happen in production with features like Offscreen (now called Activity) or when React suspends and resumes a tree.

The double-invocation exists to catch effects that don't clean up properly. If your effect works correctly when run twice, it will also work correctly in production when components unmount and remount due to navigation, Suspense boundaries, or future React features.

```jsx
import { useEffect, useState } from "react";

// ❌ Breaks under Strict Mode double-invocation
function BrokenCounter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    // This interval is set up twice in Strict Mode.
    // The first cleanup runs, but the second one stays.
    // Without proper cleanup, you'd get TWO intervals running.
    const id = setInterval(() => {
      setCount((c) => c + 1);
    }, 1000);

    return () => clearInterval(id);
    // ✅ This cleanup actually makes it work — the first interval
    // is cleared, and only the second one runs.
  }, []);

  return <p>Count: {count}</p>;
}

// ❌ Truly broken — no cleanup, double invocation causes double subscription
function BrokenChat({ roomId }) {
  useEffect(() => {
    const connection = createConnection(roomId);
    connection.connect();
    // Missing cleanup! Strict Mode will create TWO connections.
  }, [roomId]);

  return <p>Connected to {roomId}</p>;
}

// ✅ Correct — cleanup ensures only one active connection
function FixedChat({ roomId }) {
  useEffect(() => {
    const connection = createConnection(roomId);
    connection.connect();

    return () => {
      connection.disconnect(); // Clean up on remount or unmount
    };
  }, [roomId]);

  return <p>Connected to {roomId}</p>;
}
```

**Important production detail:** The double-invocation only happens in development with `<StrictMode>`. In production builds, effects run exactly once per mount. However, writing effects that *survive* double-invocation ensures they are resilient to future React features and real-world remount scenarios.

**Key takeaway:** React 18 Strict Mode double-mounts components in development to expose missing cleanup. Write effects that are idempotent and always clean up after themselves.

---

### Q10. How do you avoid infinite loops in `useEffect`?

**Answer:**

Infinite loops in `useEffect` occur when the effect updates a dependency it also reads, causing an endless render → effect → state update → render cycle. The most common culprits are:

1. **Missing dependency array** — the effect runs after every render and triggers a re-render.
2. **Object/array/function references in the dependency array** — these are recreated every render, making them always "new."
3. **Setting state unconditionally** inside the effect when that state is a dependency.

```jsx
import { useState, useEffect, useMemo, useCallback } from "react";

// ❌ INFINITE LOOP — object is recreated every render
function InfiniteLoopBug() {
  const [data, setData] = useState(null);
  const options = { method: "GET", headers: { Accept: "application/json" } };

  useEffect(() => {
    fetch("/api/data", options)
      .then((res) => res.json())
      .then(setData);
  }, [options]); // options is a new object every render → effect re-runs → ∞

  return <pre>{JSON.stringify(data)}</pre>;
}

// ✅ FIX 1 — Move the object inside the effect
function FixedWithInternalObject() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const options = { method: "GET", headers: { Accept: "application/json" } };
    fetch("/api/data", options)
      .then((res) => res.json())
      .then(setData);
  }, []); // No external dependencies

  return <pre>{JSON.stringify(data)}</pre>;
}

// ✅ FIX 2 — Memoize the object if it must be external
function FixedWithMemo({ endpoint }) {
  const [data, setData] = useState(null);

  const options = useMemo(
    () => ({ method: "GET", headers: { Accept: "application/json" } }),
    [] // Stable reference
  );

  useEffect(() => {
    fetch(endpoint, options)
      .then((res) => res.json())
      .then(setData);
  }, [endpoint, options]); // options is now stable

  return <pre>{JSON.stringify(data)}</pre>;
}

// ❌ INFINITE LOOP — setState on every render
function InfiniteStateLoop() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    setCount(count + 1); // Updates count → triggers re-render → effect re-runs → ∞
  }, [count]);

  return <p>{count}</p>;
}

// ✅ FIX — use a condition or remove the dependency
function FixedConditional() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (count < 10) {
      setCount((c) => c + 1); // Stops after reaching 10
    }
  }, [count]);

  return <p>{count}</p>;
}
```

**Key takeaway:** If your effect writes to a value it also reads, you will get an infinite loop unless you add a termination condition. Prefer primitive dependencies, memoize objects and functions, and move non-reactive values inside the effect.

---

### Q11. How do you synchronise with external systems like event listeners or third-party libraries in `useEffect`?

**Answer:**

"Synchronising with an external system" is the core mental model for `useEffect`. When integrating with browser APIs, third-party DOM libraries (charts, maps, rich text editors), or global event systems, the pattern is always: **subscribe in setup, unsubscribe in cleanup**.

```jsx
import { useEffect, useRef, useState } from "react";

// Example 1: Synchronise with the browser's Intersection Observer
function LazyImage({ src, alt }) {
  const imgRef = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const node = imgRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(node); // Stop observing once visible
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(node);

    return () => {
      observer.disconnect(); // Cleanup
    };
  }, []);

  return (
    <img
      ref={imgRef}
      src={isVisible ? src : undefined}
      alt={alt}
      style={{ minHeight: 200, background: "#eee" }}
    />
  );
}

// Example 2: Synchronise with a third-party chart library
function SalesChart({ data }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  // Setup: create the chart instance
  useEffect(() => {
    // Hypothetical third-party chart library
    chartRef.current = new ThirdPartyChart(containerRef.current, {
      type: "bar",
      data: data,
      responsive: true,
    });

    return () => {
      // Cleanup: destroy the chart to free memory
      chartRef.current.destroy();
      chartRef.current = null;
    };
  }, []); // Create once

  // Update: sync data changes into the chart
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.updateData(data);
    }
  }, [data]);

  return <div ref={containerRef} style={{ width: "100%", height: 400 }} />;
}
```

**Production notes:**
- Always verify `ref.current` is not `null` before using it.
- When working with third-party libraries that have their own lifecycle (create → update → destroy), split creation and updates into separate effects.
- Be mindful of SSR — browser-only APIs like `IntersectionObserver` should be guarded or deferred to `useEffect` (which only runs on the client).

**Key takeaway:** Think of `useEffect` as a "sync" mechanism. Setup connects your React state to the external world; cleanup disconnects it.

---

### Q12. How does `useEffect` replace class component lifecycle methods like `componentDidMount`, `componentDidUpdate`, and `componentWillUnmount`?

**Answer:**

While there is a rough mapping between lifecycle methods and `useEffect`, the mental model is fundamentally different. Lifecycle methods think in terms of *component phases* (mount, update, unmount). `useEffect` thinks in terms of *synchronisation* — start syncing, stop syncing.

| Class Lifecycle | `useEffect` Equivalent |
|---|---|
| `componentDidMount` | `useEffect(() => { ... }, [])` |
| `componentDidUpdate` | `useEffect(() => { ... }, [deps])` |
| `componentWillUnmount` | Cleanup function in `useEffect` |
| Mount + Update combined | `useEffect(() => { ... }, [deps])` (this is the natural default) |

```jsx
import { useState, useEffect, useRef } from "react";

// Class component approach
class ClassTimer extends React.Component {
  state = { seconds: 0 };
  intervalId = null;

  componentDidMount() {
    this.intervalId = setInterval(() => {
      this.setState((prev) => ({ seconds: prev.seconds + 1 }));
    }, 1000);
    document.title = `Timer: ${this.state.seconds}s`;
  }

  componentDidUpdate(prevProps, prevState) {
    document.title = `Timer: ${this.state.seconds}s`;
  }

  componentWillUnmount() {
    clearInterval(this.intervalId);
  }

  render() {
    return <p>{this.state.seconds} seconds</p>;
  }
}

// ✅ Function component equivalent — cleaner and composable
function FunctionTimer() {
  const [seconds, setSeconds] = useState(0);

  // Effect 1: Timer (replaces componentDidMount + componentWillUnmount)
  useEffect(() => {
    const id = setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);

    return () => clearInterval(id); // "componentWillUnmount"
  }, []);

  // Effect 2: Document title sync (replaces componentDidMount + componentDidUpdate)
  useEffect(() => {
    document.title = `Timer: ${seconds}s`;
  }, [seconds]);

  return <p>{seconds} seconds</p>;
}
```

**Critical difference:** In class components, `componentDidMount` and `componentDidUpdate` are separate methods, so you often duplicate logic between them. With `useEffect`, the same effect runs on mount *and* when dependencies change, eliminating this duplication. Don't try to replicate lifecycle semantics — embrace the sync mental model.

**Key takeaway:** `useEffect` unifies mount and update into a single mechanism. Think "what do I need to synchronise?" not "what lifecycle am I in?"

---

## Advanced Level (Q13–Q20)

---

### Q13. What are stale closures in `useEffect` and how do you fix them?

**Answer:**

A **stale closure** occurs when a `useEffect` callback captures a variable from a previous render and continues to use that outdated value. This happens because JavaScript closures capture variables by reference *at the time the function is created*. If the effect's dependency array doesn't include the variable, the effect keeps using the old closure.

This is one of the most common and insidious bugs in React hooks.

```jsx
import { useState, useEffect, useRef, useCallback } from "react";

// ❌ STALE CLOSURE — count is always 0 inside the interval callback
function StaleClosureBug() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // This closure captured count = 0 at mount time.
      // count never changes from the closure's perspective.
      console.log("Current count:", count); // Always logs 0
      setCount(count + 1); // Always sets to 1
    }, 1000);

    return () => clearInterval(id);
  }, []); // count is NOT in deps — closure is stale

  return <p>{count}</p>; // Displays 1 forever after first tick
}

// ✅ FIX 1 — Use the functional updater form of setState
function FixedWithUpdater() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount((prevCount) => prevCount + 1); // Always has latest value
    }, 1000);

    return () => clearInterval(id);
  }, []); // Safe: we don't read count directly

  return <p>{count}</p>;
}

// ✅ FIX 2 — Use a ref to hold the latest value
function FixedWithRef() {
  const [count, setCount] = useState(0);
  const countRef = useRef(count);

  // Keep the ref in sync with state
  useEffect(() => {
    countRef.current = count;
  }, [count]);

  useEffect(() => {
    const id = setInterval(() => {
      // The ref always holds the latest value
      console.log("Current count:", countRef.current);
      setCount(countRef.current + 1);
    }, 1000);

    return () => clearInterval(id);
  }, []);

  return <p>{count}</p>;
}

// ✅ FIX 3 — Include count in deps (re-creates interval on each change)
function FixedWithDeps() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1);
    }, 1000);

    return () => clearInterval(id); // Clear old interval
  }, [count]); // Re-runs every time count changes

  return <p>{count}</p>;
}
```

**Production recommendation:** The functional updater (`setCount(prev => prev + 1)`) is the cleanest solution when you only need the previous state value. Use a ref when you need to read the latest value for non-setState purposes (e.g., logging, conditionals). Adding the value to the deps array works but re-creates the effect on every change, which can be costly for expensive setup/cleanup.

**Key takeaway:** Every value from the component scope that changes over time and is used inside `useEffect` must be in the dependency array — or accessed through a ref or a functional updater. Stale closures are the #1 source of subtle `useEffect` bugs.

---

### Q14. When should you NOT use `useEffect`? ("You Might Not Need an Effect")

**Answer:**

This is one of the most important React 18 concepts. Many developers overuse `useEffect` as a general-purpose "do something when something changes" mechanism. But if the operation is about **transforming data for rendering** or **responding to a user event**, you don't need an effect.

Common anti-patterns:

1. **Deriving state from props or other state** — use computation during render or `useMemo` instead.
2. **Resetting state when a prop changes** — use a `key` to remount the component.
3. **Responding to user events** — handle it in the event handler, not in an effect.
4. **Sending analytics on user action** — fire it from the event handler.

```jsx
import { useState, useMemo } from "react";

// ❌ BAD — unnecessary effect to derive filtered list
function BadFilteredList({ items, query }) {
  const [filteredItems, setFilteredItems] = useState([]);

  useEffect(() => {
    setFilteredItems(items.filter((item) => item.name.includes(query)));
  }, [items, query]);
  // Problem: causes an extra render cycle. items change → render with
  // stale filteredItems → effect runs → setFilteredItems → ANOTHER render

  return filteredItems.map((item) => <li key={item.id}>{item.name}</li>);
}

// ✅ GOOD — derive during render (no effect needed)
function GoodFilteredList({ items, query }) {
  const filteredItems = useMemo(
    () => items.filter((item) => item.name.includes(query)),
    [items, query]
  );

  return filteredItems.map((item) => <li key={item.id}>{item.name}</li>);
}

// ❌ BAD — resetting state with useEffect
function BadProfileEditor({ userId }) {
  const [name, setName] = useState("");

  useEffect(() => {
    setName(""); // Reset on userId change — causes extra render
  }, [userId]);

  return <input value={name} onChange={(e) => setName(e.target.value)} />;
}

// ✅ GOOD — use key to reset component state entirely
function ProfilePage({ userId }) {
  // When userId changes, React unmounts and remounts ProfileEditor
  return <ProfileEditor key={userId} userId={userId} />;
}

function ProfileEditor({ userId }) {
  const [name, setName] = useState(""); // Fresh state on each mount
  return <input value={name} onChange={(e) => setName(e.target.value)} />;
}

// ❌ BAD — sending analytics in useEffect based on state
function BadSubmitForm() {
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (submitted) {
      analytics.track("form_submitted"); // fires on re-renders too
    }
  }, [submitted]);

  function handleSubmit() {
    setSubmitted(true);
  }

  return <button onClick={handleSubmit}>Submit</button>;
}

// ✅ GOOD — send analytics from the event handler
function GoodSubmitForm() {
  function handleSubmit() {
    submitForm().then(() => {
      analytics.track("form_submitted"); // directly in the handler
    });
  }

  return <button onClick={handleSubmit}>Submit</button>;
}
```

**The rule:** If it can be computed during render, compute it during render. If it's a response to a user interaction, handle it in the event handler. `useEffect` is only for synchronising with *external systems*.

**Key takeaway:** `useEffect` is not `componentDidUpdate` and should not be used as a generic "watcher." The React team explicitly recommends reducing the number of effects in your application.

---

### Q15. How do you manage WebSocket connections in `useEffect` for production applications?

**Answer:**

WebSocket connections are a textbook use case for `useEffect` — you need to open a connection (setup) and close it (cleanup) when the component unmounts or the connection parameters change. In production, you must also handle reconnection logic, authentication, and message buffering.

```jsx
import { useState, useEffect, useRef, useCallback } from "react";

function useChatSocket(roomId, onMessage) {
  const [status, setStatus] = useState("disconnected");
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const onMessageRef = useRef(onMessage);

  // Keep the callback ref fresh to avoid stale closures
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    let isCancelled = false;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_DELAY = 30000;

    function connect() {
      if (isCancelled) return;

      const token = getAuthToken();
      const ws = new WebSocket(
        `wss://chat.example.com/rooms/${roomId}?token=${token}`
      );
      wsRef.current = ws;

      ws.onopen = () => {
        if (isCancelled) {
          ws.close();
          return;
        }
        setStatus("connected");
        reconnectAttempts = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessageRef.current(data);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      ws.onerror = (event) => {
        console.error("WebSocket error:", event);
      };

      ws.onclose = (event) => {
        if (isCancelled) return;
        setStatus("disconnected");

        // Reconnect with exponential backoff
        if (!event.wasClean) {
          const delay = Math.min(
            1000 * 2 ** reconnectAttempts,
            MAX_RECONNECT_DELAY
          );
          reconnectAttempts++;
          setStatus("reconnecting");
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };
    }

    connect();

    return () => {
      isCancelled = true;
      clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounted"); // Clean close
      }
    };
  }, [roomId]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket not open. Message not sent.");
    }
  }, []);

  return { status, sendMessage };
}

// Usage in a component
function ChatRoom({ roomId }) {
  const [messages, setMessages] = useState([]);

  const handleMessage = useCallback((data) => {
    setMessages((prev) => [...prev, data]);
  }, []);

  const { status, sendMessage } = useChatSocket(roomId, handleMessage);

  return (
    <div>
      <p>Status: {status}</p>
      <ul>
        {messages.map((msg, i) => (
          <li key={i}>{msg.user}: {msg.text}</li>
        ))}
      </ul>
      <button onClick={() => sendMessage({ text: "Hello!" })}>
        Send
      </button>
    </div>
  );
}
```

**Production considerations:**
- **Authentication:** Pass tokens via query params or in the first message after connection.
- **Exponential backoff:** Never reconnect immediately in a tight loop — use increasing delays with a cap.
- **Cleanup:** Always close the WebSocket with a clean status code (1000) on unmount.
- **Stale closure prevention:** Use a ref for the message handler callback so the WebSocket `onmessage` always calls the latest version.
- **Heartbeats:** In production, implement ping/pong to detect dead connections that `onclose` might not catch.

**Key takeaway:** WebSocket management in `useEffect` requires careful cleanup, reconnection logic, and stale-closure avoidance. Extract it into a custom hook for reusability and testability.

---

### Q16. How do you implement debouncing and throttling inside `useEffect`?

**Answer:**

Debouncing (delay execution until input stabilises) and throttling (execute at most once per interval) are common requirements for search inputs, window resize handlers, and scroll-based logic. Implementing them inside `useEffect` requires careful cleanup to prevent lingering timers.

```jsx
import { useState, useEffect, useRef, useCallback } from "react";

// Approach 1: Debouncing a search query inside useEffect
function DebouncedSearch({ onSearch }) {
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!query) return;

    const timerId = setTimeout(() => {
      onSearch(query);
    }, 300); // 300ms debounce

    // Cleanup: cancel the timer if query changes before 300ms
    return () => clearTimeout(timerId);
  }, [query, onSearch]);

  return (
    <input
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder="Search…"
    />
  );
}

// Approach 2: Custom useDebounce hook (reusable)
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timerId = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timerId);
  }, [value, delay]);

  return debouncedValue;
}

// Usage of the custom hook
function ProductSearch() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (!debouncedQuery) {
      setResults([]);
      return;
    }

    const controller = new AbortController();

    fetch(`/api/search?q=${encodeURIComponent(debouncedQuery)}`, {
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data) => setResults(data.items))
      .catch((err) => {
        if (err.name !== "AbortError") console.error(err);
      });

    return () => controller.abort();
  }, [debouncedQuery]);

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search products…"
      />
      <ul>
        {results.map((r) => (
          <li key={r.id}>{r.name}</li>
        ))}
      </ul>
    </div>
  );
}

// Approach 3: Throttling scroll events with useEffect
function useThrottledScroll(callback, delay) {
  const lastRun = useRef(Date.now());
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    function handleScroll() {
      const now = Date.now();
      if (now - lastRun.current >= delay) {
        lastRun.current = now;
        callbackRef.current();
      }
    }

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [delay]);
}

// Usage
function InfiniteList() {
  useThrottledScroll(() => {
    const scrollBottom =
      window.innerHeight + window.scrollY >= document.body.offsetHeight - 200;
    if (scrollBottom) {
      loadMore();
    }
  }, 200);

  return <div>{/* list items */}</div>;
}
```

**Production tips:**
- Debounce is better for user input (search, autocomplete) where you want to wait for the user to stop typing.
- Throttle is better for continuous events (scroll, resize, mousemove) where you want periodic updates.
- Always clean up timers in the effect cleanup to prevent stale timer callbacks.
- Consider using libraries like `lodash.debounce` or `lodash.throttle` for complex scenarios, but be careful — they return memoized functions that need proper cleanup.

**Key takeaway:** Debouncing in `useEffect` is elegantly handled by `setTimeout` + cleanup. Extract reusable `useDebounce` and `useThrottle` hooks for consistency across the codebase.

---

### Q17. What is the execution order of `useEffect` in parent and child components?

**Answer:**

Understanding the execution order is critical for debugging complex component trees. The rule is:

- **Setup functions** run bottom-up: **child effects fire before parent effects**.
- **Cleanup functions** also run bottom-up: child cleanups fire before parent cleanups.
- Within a single component, effects run in the order they are declared.

This is because React processes the component tree depth-first. Children render before the parent's render is complete, so their effects are queued first.

```jsx
import { useEffect } from "react";

function Child({ name }) {
  useEffect(() => {
    console.log(`[${name}] Child effect — setup`);
    return () => console.log(`[${name}] Child effect — cleanup`);
  });

  console.log(`[${name}] Child render`);
  return <p>{name}</p>;
}

function Parent() {
  useEffect(() => {
    console.log("[Parent] Parent effect 1 — setup");
    return () => console.log("[Parent] Parent effect 1 — cleanup");
  });

  useEffect(() => {
    console.log("[Parent] Parent effect 2 — setup");
    return () => console.log("[Parent] Parent effect 2 — cleanup");
  });

  console.log("[Parent] Parent render");

  return (
    <div>
      <Child name="A" />
      <Child name="B" />
    </div>
  );
}

// Console output on initial mount:
// [Parent] Parent render
// [A] Child render
// [B] Child render
// [A] Child effect — setup
// [B] Child effect — setup
// [Parent] Parent effect 1 — setup
// [Parent] Parent effect 2 — setup

// Console output when Parent re-renders:
// [Parent] Parent render
// [A] Child render
// [B] Child render
// [A] Child effect — cleanup         (previous cleanup, bottom-up)
// [B] Child effect — cleanup
// [Parent] Parent effect 1 — cleanup
// [Parent] Parent effect 2 — cleanup
// [A] Child effect — setup           (new setup, bottom-up)
// [B] Child effect — setup
// [Parent] Parent effect 1 — setup
// [Parent] Parent effect 2 — setup
```

**Why this matters in production:**
- If a parent effect depends on a DOM node rendered by a child, the child's effect (which may set up that DOM node) runs first, so the parent can safely read it.
- If you're coordinating setup/teardown between parent and child (e.g., a form context that children register with), know that children register before the parent's effect runs.
- All cleanups run before all setups — React cleans up the entire tree's previous effects before running new ones.

**Key takeaway:** Effects fire bottom-up (children before parents), and all cleanups run before any new setups. Within a component, effects run in declaration order.

---

### Q18. How does cleanup timing work in `useEffect`, and how do you prevent memory leaks in production?

**Answer:**

Memory leaks in React applications typically come from effects that acquire resources (subscriptions, timers, event listeners, AbortControllers) but fail to release them. Understanding the exact timing of cleanup is essential.

**Cleanup timing:**
1. When a dependency changes: React runs the **previous** effect's cleanup → then runs the **new** effect's setup.
2. When the component unmounts: React runs the cleanup one final time.
3. In React 18 Strict Mode (dev only): mount → cleanup → mount (to verify cleanup works).

```jsx
import { useEffect, useRef, useState } from "react";

// Production example: Preventing memory leaks in a dashboard component
function AnalyticsDashboard({ dashboardId }) {
  const [metrics, setMetrics] = useState(null);
  const [liveUpdates, setLiveUpdates] = useState([]);
  const eventSourceRef = useRef(null);

  // Effect 1: Fetch initial dashboard data with AbortController
  useEffect(() => {
    const controller = new AbortController();

    async function loadDashboard() {
      try {
        const res = await fetch(`/api/dashboards/${dashboardId}`, {
          signal: controller.signal,
        });
        const data = await res.json();
        setMetrics(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("Dashboard fetch failed:", err);
        }
      }
    }

    loadDashboard();

    // Cleanup: abort the fetch if dashboardId changes or component unmounts
    return () => {
      controller.abort();
    };
  }, [dashboardId]);

  // Effect 2: Subscribe to Server-Sent Events for live metrics
  useEffect(() => {
    const eventSource = new EventSource(
      `/api/dashboards/${dashboardId}/stream`
    );
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        setLiveUpdates((prev) => {
          // Prevent unbounded array growth (memory leak!)
          const updated = [...prev, update];
          return updated.length > 100 ? updated.slice(-100) : updated;
        });
      } catch (err) {
        console.error("Failed to parse SSE event:", err);
      }
    };

    eventSource.onerror = () => {
      console.error("SSE connection error");
      eventSource.close();
    };

    // Cleanup: close the SSE connection
    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [dashboardId]);

  // Effect 3: Periodic cleanup of stale data
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveUpdates((prev) => {
        const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
        return prev.filter((update) => update.timestamp > fiveMinutesAgo);
      });
    }, 60000); // Run every minute

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Dashboard: {dashboardId}</h2>
      {metrics && <MetricsGrid data={metrics} />}
      <LiveFeed updates={liveUpdates} />
    </div>
  );
}
```

**Common memory leak sources and fixes:**

| Leak Source | Fix |
|---|---|
| `setInterval` / `setTimeout` not cleared | Return `() => clearInterval(id)` |
| `addEventListener` not removed | Return `() => removeEventListener(...)` |
| Fetch resolving after unmount | Use `AbortController` |
| WebSocket / EventSource not closed | Return `() => ws.close()` |
| Unbounded array/map growth in state | Cap the collection size |
| Third-party library instance not destroyed | Return `() => instance.destroy()` |

**Key takeaway:** Every resource acquired in an effect must be released in cleanup. In production, also watch for *logical* memory leaks like unbounded state growth, not just missing cleanup functions.

---

### Q19. What are stale closures in the context of `useEffect` with multiple interacting effects, and how do you handle complex state dependencies?

**Answer:**

In real-world applications, you often have multiple effects that interact through shared state. Stale closures become especially dangerous when one effect reads state that another effect updates, because each effect captures its own snapshot of state at render time.

The advanced pattern for solving this involves a combination of `useRef` for mutable latest-value access, `useReducer` for complex state transitions, and careful dependency management.

```jsx
import { useEffect, useReducer, useRef, useCallback } from "react";

// Production scenario: A real-time collaborative editor status tracker
const initialState = {
  users: [],
  cursors: {},
  lastSync: null,
  connectionStatus: "disconnected",
};

function editorReducer(state, action) {
  switch (action.type) {
    case "SET_CONNECTION_STATUS":
      return { ...state, connectionStatus: action.payload };
    case "UPDATE_USERS":
      return { ...state, users: action.payload };
    case "UPDATE_CURSOR": {
      return {
        ...state,
        cursors: { ...state.cursors, [action.payload.userId]: action.payload.position },
      };
    }
    case "SYNC_COMPLETE":
      return { ...state, lastSync: Date.now() };
    default:
      return state;
  }
}

function useCollaborativeEditor(documentId) {
  const [state, dispatch] = useReducer(editorReducer, initialState);
  const stateRef = useRef(state);

  // Keep the ref in sync — avoids stale closures in long-lived callbacks
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  // Effect 1: WebSocket connection
  useEffect(() => {
    const ws = new WebSocket(`wss://collab.example.com/docs/${documentId}`);

    ws.onopen = () => {
      dispatch({ type: "SET_CONNECTION_STATUS", payload: "connected" });
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case "users":
          dispatch({ type: "UPDATE_USERS", payload: msg.users });
          break;
        case "cursor":
          dispatch({ type: "UPDATE_CURSOR", payload: msg });
          break;
        case "sync":
          dispatch({ type: "SYNC_COMPLETE" });
          break;
      }
    };

    ws.onclose = () => {
      dispatch({ type: "SET_CONNECTION_STATUS", payload: "disconnected" });
    };

    return () => ws.close(1000);
  }, [documentId]);

  // Effect 2: Periodic sync check — uses ref to read latest state
  useEffect(() => {
    const interval = setInterval(() => {
      const current = stateRef.current;

      // Access latest state without adding it to dependencies
      if (
        current.connectionStatus === "connected" &&
        current.lastSync &&
        Date.now() - current.lastSync > 10000
      ) {
        console.warn("No sync in 10s — connection may be stale");
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []); // Empty deps — interval runs for the lifetime of the hook

  return state;
}

// Usage
function Editor({ documentId }) {
  const { users, cursors, connectionStatus } = useCollaborativeEditor(documentId);

  return (
    <div>
      <span>Status: {connectionStatus}</span>
      <span>Users: {users.map((u) => u.name).join(", ")}</span>
      {/* Render editor with cursors overlay */}
    </div>
  );
}
```

**Why `useReducer` helps:**
- `dispatch` has a **stable identity** — it never changes between renders, so it's safe to include in dependency arrays without causing re-runs.
- All state transitions are centralised, making it easier to reason about what each WebSocket message does.
- You avoid the problem of stale closures reading individual `useState` values because `dispatch` doesn't need to read current state.

**Why the ref pattern helps:**
- Long-lived callbacks (intervals, WebSocket handlers) need access to the *latest* state.
- Putting state in the dependency array of a timer effect would tear down and recreate the timer on every state change — wasteful and incorrect.
- A ref gives you a mutable "window" into the latest state without triggering effect re-execution.

**Key takeaway:** For complex multi-effect scenarios, combine `useReducer` (stable `dispatch`) with `useRef` (latest-value access) to avoid stale closures without overloading dependency arrays.

---

### Q20. How is the React ecosystem moving away from `useEffect` for data fetching? What are React 19's `use()` API and Server Components?

**Answer:**

The React team has long maintained that `useEffect` is a suboptimal mechanism for data fetching. It runs *after* render, creating a "render-then-fetch" waterfall: the component renders a loading state, the browser paints it, then the effect fires the fetch, and when it resolves, the component re-renders with data. This leads to loading spinners and sequential request chains in deeply nested component trees.

React 18 introduced **Suspense for data fetching** (experimental) and React 19 formalises this with the **`use()` API** and **Server Components**, which together represent a paradigm shift away from `useEffect` for data loading.

**The problems with `useEffect` for data fetching:**

```jsx
// ❌ The waterfall problem with useEffect
function App() {
  // Renders loading → fetches user → renders user → child fetches posts
  // → renders loading → fetches posts → finally renders posts
  return <UserProfile userId={1} />;
}

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then(setUser);
  }, [userId]);

  if (!user) return <p>Loading user…</p>;

  return (
    <div>
      <h1>{user.name}</h1>
      <UserPosts userId={userId} /> {/* This only starts fetching AFTER user loads */}
    </div>
  );
}

function UserPosts({ userId }) {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    fetch(`/api/users/${userId}/posts`)
      .then((res) => res.json())
      .then(setPosts);
  }, [userId]);

  if (!posts.length) return <p>Loading posts…</p>;

  return (
    <ul>
      {posts.map((p) => <li key={p.id}>{p.title}</li>)}
    </ul>
  );
}
```

**React 19's `use()` API — reading promises during render:**

```jsx
import { use, Suspense } from "react";

// The data fetching starts BEFORE render, not after
function fetchUser(userId) {
  // This returns a Promise — can be cached by a framework or custom cache
  return fetch(`/api/users/${userId}`).then((res) => res.json());
}

function fetchPosts(userId) {
  return fetch(`/api/users/${userId}/posts`).then((res) => res.json());
}

function App() {
  // Start BOTH fetches in parallel — no waterfall!
  const userPromise = fetchUser(1);
  const postsPromise = fetchPosts(1);

  return (
    <Suspense fallback={<p>Loading…</p>}>
      <UserProfile userPromise={userPromise} postsPromise={postsPromise} />
    </Suspense>
  );
}

function UserProfile({ userPromise, postsPromise }) {
  // use() suspends the component until the promise resolves
  const user = use(userPromise);

  return (
    <div>
      <h1>{user.name}</h1>
      <Suspense fallback={<p>Loading posts…</p>}>
        <UserPosts postsPromise={postsPromise} />
      </Suspense>
    </div>
  );
}

function UserPosts({ postsPromise }) {
  const posts = use(postsPromise);

  return (
    <ul>
      {posts.map((p) => <li key={p.id}>{p.title}</li>)}
    </ul>
  );
}
```

**Server Components — no `useEffect` needed at all:**

```jsx
// This component runs on the server — no hooks, no client-side JS
// It can directly access databases, file systems, and APIs
async function UserProfilePage({ params }) {
  // Direct async/await — no useEffect, no useState, no loading states
  const user = await db.users.findById(params.userId);
  const posts = await db.posts.findByUserId(params.userId);

  return (
    <div>
      <h1>{user.name}</h1>
      <ul>
        {posts.map((p) => <li key={p.id}>{p.title}</li>)}
      </ul>
      {/* Client components can still use hooks for interactivity */}
      <LikeButton postId={posts[0]?.id} /> {/* 'use client' component */}
    </div>
  );
}
```

**When to use what (React 19+ guidance):**

| Scenario | Approach |
|---|---|
| Initial page data | Server Components (preferred) or framework-level loaders (Next.js, Remix) |
| Client-side data after user interaction | `use()` with Suspense, or event-handler-triggered fetches |
| Subscriptions (WebSocket, SSE) | `useEffect` (still the right tool) |
| Timers, DOM manipulation | `useEffect` (still the right tool) |
| Third-party library integration | `useEffect` (still the right tool) |

**Key takeaway:** `useEffect` remains essential for synchronisation with external systems (subscriptions, timers, DOM). But for data fetching — the most common use case — the ecosystem is shifting to Server Components, the `use()` API, and framework-level data loading. In new projects, prefer these patterns over `useEffect`-based data fetching. `useEffect` is not going away, but its role is narrowing to what it was always meant for: synchronising with the outside world.

---

## Summary

| # | Topic | Level |
|---|---|---|
| Q1 | What `useEffect` is and when it runs | Beginner |
| Q2 | Dependency array variants | Beginner |
| Q3 | Cleanup function | Beginner |
| Q4 | Fetching data with `useEffect` | Beginner |
| Q5 | Rules of Hooks | Beginner |
| Q6 | Race conditions and `AbortController` | Intermediate |
| Q7 | `useEffect` vs `useLayoutEffect` | Intermediate |
| Q8 | Multiple vs single `useEffect` | Intermediate |
| Q9 | Strict Mode double-invocation | Intermediate |
| Q10 | Avoiding infinite loops | Intermediate |
| Q11 | Syncing with external systems | Intermediate |
| Q12 | Replacing lifecycle methods | Intermediate |
| Q13 | Stale closures | Advanced |
| Q14 | When NOT to use `useEffect` | Advanced |
| Q15 | WebSocket connections in production | Advanced |
| Q16 | Debouncing and throttling | Advanced |
| Q17 | Execution order (parent/child) | Advanced |
| Q18 | Cleanup timing and memory leaks | Advanced |
| Q19 | Complex state deps and multi-effect coordination | Advanced |
| Q20 | Moving beyond `useEffect`: `use()` and Server Components | Advanced |
