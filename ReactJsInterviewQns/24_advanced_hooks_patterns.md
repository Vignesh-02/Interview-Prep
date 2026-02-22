# Advanced Hooks & Patterns — React 18 Interview Questions

## Topic Introduction

React 18 ships with a rich set of hooks that go far beyond `useState` and `useEffect`. Hooks like **`useReducer`**, **`useImperativeHandle`**, **`useId`**, **`useSyncExternalStore`**, **`useDebugValue`**, and **`useLayoutEffect`** exist to solve very specific problems — complex state transitions, imperative component APIs, SSR-safe ID generation, safe external-store subscriptions under concurrent rendering, DevTools observability, and synchronous DOM measurement. Mastering these hooks (and knowing when *not* to reach for them) is what separates intermediate developers who can wire together simple forms from senior engineers who can build design-system primitives, real-time collaboration features, and concurrent-safe data layers. In interviews, questions about these hooks test whether you truly understand React's rendering model — the commit phase vs. the render phase, the rules of hooks, referential stability, and the tearing problem that concurrent rendering introduced.

Beyond individual hooks, **hook composition patterns** are the backbone of scalable React architecture. Custom hooks are not just about extracting repeated logic into a function — they are a tool for **dependency injection**, **state-machine orchestration**, **middleware pipelines**, and **plugin systems**. Patterns like the "latest ref" pattern (avoiding stale closures), `usePrevious`, `useStableCallback`, compound hooks that merge multiple concerns, and `useReducer`-based undo/redo systems appear constantly in production codebases at companies like Meta, Vercel, and Shopify. Understanding how to compose hooks while keeping them concurrent-rendering-safe is a critical skill in the React 18 era.

The code snippet below illustrates the breadth of what we will cover — a single component that touches `useReducer`, `useImperativeHandle`, `useId`, and `useSyncExternalStore` to build a rich, accessible form field with external validation:

```jsx
import {
  useReducer, useImperativeHandle, useId,
  useSyncExternalStore, forwardRef
} from 'react';
import { validationStore } from './validationStore';

const reducer = (state, action) => {
  switch (action.type) {
    case 'CHANGE': return { ...state, value: action.payload, dirty: true };
    case 'BLUR':   return { ...state, touched: true };
    case 'RESET':  return { value: '', dirty: false, touched: false };
    default:       return state;
  }
};

const SmartField = forwardRef(({ name, label }, ref) => {
  const id = useId();                          // SSR-safe unique ID
  const [state, dispatch] = useReducer(reducer, {
    value: '', dirty: false, touched: false,
  });

  // Subscribe to an external validation store (concurrent-safe)
  const errors = useSyncExternalStore(
    validationStore.subscribe,
    () => validationStore.getSnapshot(name),
    () => validationStore.getServerSnapshot(name),
  );

  // Expose an imperative API to the parent
  useImperativeHandle(ref, () => ({
    reset: () => dispatch({ type: 'RESET' }),
    focus: () => document.getElementById(`${id}-input`)?.focus(),
    getValue: () => state.value,
  }), [state.value, id]);

  return (
    <div>
      <label htmlFor={`${id}-input`}>{label}</label>
      <input
        id={`${id}-input`}
        value={state.value}
        onChange={e => dispatch({ type: 'CHANGE', payload: e.target.value })}
        onBlur={() => dispatch({ type: 'BLUR' })}
      />
      {state.touched && errors && <span role="alert">{errors}</span>}
    </div>
  );
});
```

---

## Beginner Level (Q1–Q5)

---

### Q1. When should you choose `useReducer` over `useState` for complex state management?

**Answer:**

`useState` is ideal when state is a single primitive or an independent value. `useReducer` becomes the better choice when:

1. **State has multiple sub-values** that change together (e.g., `{ value, error, loading }`).
2. **The next state depends on the previous state** in non-trivial ways (e.g., toggling, incrementing with caps, conditional transitions).
3. **You want a predictable action-based API** — dispatching named actions (`{ type: 'SUBMIT' }`) makes logic easier to trace, test, and log.
4. **Multiple event handlers need to trigger the same state transition** — instead of duplicating setter logic, they all dispatch the same action.

Under the hood, `useState` is actually implemented as a `useReducer` inside React. The key difference is ergonomic: `useReducer` centralises transition logic in a pure function (the reducer), making it unit-testable outside of React.

```jsx
import { useReducer } from 'react';

// A reducer that manages a fetch lifecycle
const initialState = { data: null, loading: false, error: null };

function fetchReducer(state, action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    case 'FETCH_SUCCESS':
      return { data: action.payload, loading: false, error: null };
    case 'FETCH_ERROR':
      return { data: null, loading: false, error: action.payload };
    default:
      throw new Error(`Unhandled action: ${action.type}`);
  }
}

function UserProfile({ userId }) {
  const [state, dispatch] = useReducer(fetchReducer, initialState);

  const loadUser = async () => {
    dispatch({ type: 'FETCH_START' });
    try {
      const res = await fetch(`/api/users/${userId}`);
      if (!res.ok) throw new Error('Network error');
      const data = await res.json();
      dispatch({ type: 'FETCH_SUCCESS', payload: data });
    } catch (err) {
      dispatch({ type: 'FETCH_ERROR', payload: err.message });
    }
  };

  return (
    <div>
      <button onClick={loadUser} disabled={state.loading}>
        {state.loading ? 'Loading…' : 'Load User'}
      </button>
      {state.error && <p className="error">{state.error}</p>}
      {state.data && <h2>{state.data.name}</h2>}
    </div>
  );
}
```

**Key takeaway:** If you find yourself calling multiple `setState` calls in a single handler (e.g., `setLoading(true); setError(null);`), that is a strong signal to refactor to `useReducer`.

---

### Q2. What is `useImperativeHandle` and why is it needed alongside `forwardRef`?

**Answer:**

By default, when a parent uses a `ref` on a child component wrapped in `forwardRef`, the ref points to a raw DOM element. `useImperativeHandle` lets the child **customise** what value the parent receives via that ref — you can expose a curated API (methods, getters) instead of the entire DOM node.

**Why it exists:** React's philosophy is declarative, but sometimes parents need imperative access — focusing an input, scrolling, triggering animations, or resetting internal state. Rather than exposing the entire DOM surface (which creates coupling), `useImperativeHandle` lets you expose *only* what the parent needs.

```jsx
import { useRef, useImperativeHandle, forwardRef } from 'react';

const VideoPlayer = forwardRef(({ src }, ref) => {
  const videoRef = useRef(null);

  useImperativeHandle(ref, () => ({
    play() {
      videoRef.current?.play();
    },
    pause() {
      videoRef.current?.pause();
    },
    seekTo(seconds) {
      if (videoRef.current) {
        videoRef.current.currentTime = seconds;
      }
    },
  }), []);

  return <video ref={videoRef} src={src} style={{ width: '100%' }} />;
});

// Parent usage
function App() {
  const playerRef = useRef(null);

  return (
    <div>
      <VideoPlayer ref={playerRef} src="/intro.mp4" />
      <button onClick={() => playerRef.current.play()}>Play</button>
      <button onClick={() => playerRef.current.pause()}>Pause</button>
      <button onClick={() => playerRef.current.seekTo(30)}>Skip to 0:30</button>
    </div>
  );
}
```

The parent never touches the raw `<video>` DOM node — it only sees `play`, `pause`, and `seekTo`. This is a much safer, more maintainable contract.

---

### Q3. What is `useId` and why was it introduced in React 18?

**Answer:**

`useId` is a React 18 hook that generates a **unique, stable string ID** that is consistent across server and client renders. It was introduced to solve the **SSR hydration mismatch** problem that occurred when developers used counters, `Math.random()`, or libraries like `uuid` to generate IDs — the server would produce one ID and the client would produce a different one, causing a mismatch warning.

**How it works:**
- `useId` returns a string like `:r1:`, `:r2:`, etc.
- The same component instance always returns the same ID on the server and client.
- You can derive multiple related IDs from a single call by appending suffixes.

```jsx
import { useId } from 'react';

function FormField({ label, type = 'text' }) {
  const id = useId();

  return (
    <div className="field">
      <label htmlFor={`${id}-input`}>{label}</label>
      <input id={`${id}-input`} type={type} aria-describedby={`${id}-help`} />
      <small id={`${id}-help`}>Enter your {label.toLowerCase()}</small>
    </div>
  );
}

// Multiple instances get unique IDs automatically
function SignupForm() {
  return (
    <form>
      <FormField label="Email" type="email" />
      <FormField label="Password" type="password" />
      <FormField label="Username" />
    </form>
  );
}
```

**Important:** `useId` is *not* for generating keys in lists. List keys should come from your data (database IDs, slugs, etc.). `useId` is for accessibility attributes (`id`, `htmlFor`, `aria-describedby`, `aria-labelledby`) where you need a unique identifier that survives SSR hydration.

---

### Q4. What is `useDebugValue` and how do you use it effectively in custom hooks?

**Answer:**

`useDebugValue` is a hook that lets you add a **label** to your custom hook that appears in React DevTools. It has zero effect on runtime behaviour — it is purely a DevTools convenience. When you open the Components panel, instead of seeing opaque internal state, you see a human-readable label next to your custom hook.

It accepts an optional **formatter function** as a second argument. The formatter is only called when the DevTools panel is actually open, which means you can defer expensive formatting without affecting production performance.

```jsx
import { useState, useEffect, useDebugValue } from 'react';

function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Shows "OnlineStatus: Online" or "OnlineStatus: Offline" in DevTools
  useDebugValue(isOnline, online => `OnlineStatus: ${online ? 'Online' : 'Offline'}`);

  return isOnline;
}

function StatusBar() {
  const isOnline = useOnlineStatus();
  return <span>{isOnline ? '🟢 Connected' : '🔴 Disconnected'}</span>;
}
```

**When to use it:**
- In **shared custom hooks** consumed by many components across a team or library.
- When the internal state is not obvious from the component tree.
- **Don't** add it to every custom hook — it is noise if the hook's value is already visible in the component's state.

---

### Q5. What is the difference between `useEffect` and `useLayoutEffect`, and when does layout timing matter?

**Answer:**

Both hooks run *after* React has updated the DOM, but at different times:

| Hook | Timing | Blocking? |
|---|---|---|
| `useEffect` | Fires **asynchronously** after the browser has painted | No — does not block visual updates |
| `useLayoutEffect` | Fires **synchronously** after DOM mutations but **before** the browser paints | Yes — blocks the paint |

**When `useLayoutEffect` matters:** Whenever you need to **read layout** (e.g., measure an element's size or position) and **synchronously set state** to adjust the UI before the user sees the first frame. If you used `useEffect` in this case, the user would see a brief flicker — the initial render followed by the corrected render.

```jsx
import { useState, useRef, useLayoutEffect } from 'react';

function Tooltip({ anchorEl, children }) {
  const tooltipRef = useRef(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  useLayoutEffect(() => {
    if (!anchorEl || !tooltipRef.current) return;

    const anchorRect = anchorEl.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    // Position the tooltip above the anchor, centered horizontally
    setPosition({
      top: anchorRect.top - tooltipRect.height - 8,
      left: anchorRect.left + (anchorRect.width - tooltipRect.width) / 2,
    });
  }, [anchorEl]);

  return (
    <div
      ref={tooltipRef}
      className="tooltip"
      style={{
        position: 'fixed',
        top: position.top,
        left: position.left,
      }}
    >
      {children}
    </div>
  );
}
```

**Rule of thumb:** Default to `useEffect`. Switch to `useLayoutEffect` only when you need to measure the DOM and apply a correction *before* the user sees the result. On the server (SSR), `useLayoutEffect` fires a warning because there is no DOM to measure — use it only in client components.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How does `useImperativeHandle` with `forwardRef` enable building rich component APIs in a design system?

**Answer:**

In a design system, you often build complex components (modals, dropdowns, data grids, rich text editors) that need to expose a controlled imperative API to consumers while keeping implementation details private. `useImperativeHandle` + `forwardRef` is the pattern for this.

**Production scenario:** A `<Dialog>` component in a design system that exposes `open()`, `close()`, and `getIsOpen()` — consumers never manipulate DOM nodes or internal state directly.

```jsx
import { useRef, useState, useImperativeHandle, forwardRef, useCallback } from 'react';
import { createPortal } from 'react-dom';

const Dialog = forwardRef(({ title, children, onClose }, ref) => {
  const [isOpen, setIsOpen] = useState(false);
  const dialogRef = useRef(null);

  const open = useCallback(() => {
    setIsOpen(true);
    // Wait for DOM, then focus the dialog for accessibility
    requestAnimationFrame(() => {
      dialogRef.current?.focus();
    });
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    onClose?.();
  }, [onClose]);

  useImperativeHandle(ref, () => ({
    open,
    close,
    getIsOpen: () => isOpen,
  }), [open, close, isOpen]);

  if (!isOpen) return null;

  return createPortal(
    <div className="dialog-overlay" onClick={close}>
      <div
        ref={dialogRef}
        className="dialog-content"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        onClick={e => e.stopPropagation()}
      >
        <header>
          <h2>{title}</h2>
          <button onClick={close} aria-label="Close">×</button>
        </header>
        <div className="dialog-body">{children}</div>
      </div>
    </div>,
    document.body
  );
});

// Consumer code — clean imperative API
function SettingsPage() {
  const dialogRef = useRef(null);

  const handleDeleteAccount = () => {
    dialogRef.current.open();
  };

  return (
    <div>
      <button onClick={handleDeleteAccount}>Delete Account</button>
      <Dialog ref={dialogRef} title="Confirm Deletion" onClose={() => console.log('closed')}>
        <p>This action is irreversible. Are you sure?</p>
        <button onClick={() => dialogRef.current.close()}>Cancel</button>
        <button onClick={() => { /* delete logic */ dialogRef.current.close(); }}>
          Confirm
        </button>
      </Dialog>
    </div>
  );
}
```

**Key design principles:**
- The consumer only sees `open`, `close`, and `getIsOpen` — not internal state setters or DOM refs.
- The dependency array on `useImperativeHandle` ensures the parent's ref always has the latest values.
- This pattern scales: data grids expose `scrollToRow`, `selectAll`; rich editors expose `insertText`, `getSelection`.

---

### Q7. How does `useSyncExternalStore` work, and why was it introduced for concurrent rendering safety?

**Answer:**

Before React 18, subscribing to an external store (Redux, Zustand, browser APIs, a global `EventEmitter`) via `useEffect` + `useState` was common but had a subtle bug under concurrent rendering: **tearing**. Tearing occurs when React renders some components with a new store value and others with an old value in the same render pass — because concurrent rendering can pause and resume, an external store might change between those phases.

`useSyncExternalStore` solves this by telling React: "this value comes from outside — here's how to subscribe and how to snapshot it." React can then guarantee a consistent read across all components in a single render.

**Signature:**

```jsx
const snapshot = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot?);
```

- `subscribe(callback)`: called once; must return an unsubscribe function. Call `callback` whenever the store changes.
- `getSnapshot()`: returns the current value. Must return the same reference if the value hasn't changed (React uses `Object.is` to bail out).
- `getServerSnapshot()` (optional): used during SSR and hydration.

**Production example — subscribing to browser online status:**

```jsx
import { useSyncExternalStore } from 'react';

function subscribe(callback) {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

function getSnapshot() {
  return navigator.onLine;
}

function getServerSnapshot() {
  return true; // assume online during SSR
}

function useOnlineStatus() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

function App() {
  const isOnline = useOnlineStatus();
  return (
    <header>
      Status: {isOnline ? 'Online' : 'Offline'}
    </header>
  );
}
```

**Critical detail:** `subscribe` and `getSnapshot` should be **stable references** (declared outside the component or memoised). If they are inline functions that change every render, React will re-subscribe on every render, killing performance.

---

### Q8. How do you use `useSyncExternalStore` to safely subscribe to browser APIs like media queries and scroll position?

**Answer:**

Browser APIs like `matchMedia`, `scroll`, and `resize` are external stores — they change independently of React. `useSyncExternalStore` is the correct way to subscribe to them in React 18 because it is concurrent-rendering-safe and avoids tearing.

**Example 1 — Media query hook:**

```jsx
import { useSyncExternalStore, useCallback } from 'react';

function useMediaQuery(query) {
  const subscribe = useCallback((callback) => {
    const mql = window.matchMedia(query);
    mql.addEventListener('change', callback);
    return () => mql.removeEventListener('change', callback);
  }, [query]);

  const getSnapshot = () => window.matchMedia(query).matches;

  const getServerSnapshot = () => false; // conservative default for SSR

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

function Sidebar() {
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (isMobile) return <MobileDrawer />;
  return <DesktopSidebar />;
}
```

**Example 2 — Scroll position hook:**

```jsx
import { useSyncExternalStore } from 'react';

// Stable subscribe function — declared outside the component
function subscribeToScroll(callback) {
  window.addEventListener('scroll', callback, { passive: true });
  return () => window.removeEventListener('scroll', callback);
}

function getScrollSnapshot() {
  return window.scrollY;
}

function getServerScrollSnapshot() {
  return 0;
}

function useScrollPosition() {
  return useSyncExternalStore(
    subscribeToScroll,
    getScrollSnapshot,
    getServerScrollSnapshot
  );
}

// Production use — "back to top" button
function BackToTop() {
  const scrollY = useScrollPosition();

  if (scrollY < 400) return null;

  return (
    <button
      className="back-to-top"
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
    >
      ↑ Top
    </button>
  );
}
```

**Performance note:** For high-frequency events like `scroll`, consider debouncing inside the subscribe function or throttling with `requestAnimationFrame`, because every snapshot change triggers a re-render. Alternatively, use CSS-based solutions where possible and reserve `useSyncExternalStore` for cases where you need the value in JavaScript logic.

---

### Q9. What are compound hooks, and how do you combine multiple hooks for complex behaviour?

**Answer:**

A **compound hook** is a custom hook that composes several lower-level hooks (state, effects, refs, context) into a single, cohesive API. The goal is to encapsulate a complex behaviour so that the consuming component remains simple and declarative.

**Production scenario — `useAsync` hook** that combines `useReducer`, `useEffect`, `useRef`, and `useCallback`:

```jsx
import { useReducer, useEffect, useRef, useCallback } from 'react';

const asyncReducer = (state, action) => {
  switch (action.type) {
    case 'PENDING':  return { status: 'pending', data: null, error: null };
    case 'RESOLVED': return { status: 'resolved', data: action.payload, error: null };
    case 'REJECTED': return { status: 'rejected', data: null, error: action.payload };
    case 'IDLE':     return { status: 'idle', data: null, error: null };
    default:         throw new Error(`Unhandled action: ${action.type}`);
  }
};

function useAsync(asyncFn, { immediate = false } = {}) {
  const [state, dispatch] = useReducer(asyncReducer, {
    status: 'idle', data: null, error: null,
  });

  // Track if the component is mounted to avoid state updates after unmount
  const mountedRef = useRef(true);
  useEffect(() => {
    return () => { mountedRef.current = false; };
  }, []);

  // Store the latest asyncFn to avoid stale closures
  const fnRef = useRef(asyncFn);
  useEffect(() => { fnRef.current = asyncFn; }, [asyncFn]);

  const execute = useCallback(async (...args) => {
    dispatch({ type: 'PENDING' });
    try {
      const result = await fnRef.current(...args);
      if (mountedRef.current) {
        dispatch({ type: 'RESOLVED', payload: result });
      }
      return result;
    } catch (error) {
      if (mountedRef.current) {
        dispatch({ type: 'REJECTED', payload: error });
      }
      throw error;
    }
  }, []);

  const reset = useCallback(() => dispatch({ type: 'IDLE' }), []);

  useEffect(() => {
    if (immediate) execute();
  }, [immediate, execute]);

  return { ...state, execute, reset };
}

// Usage — very clean consumer code
function UserDashboard({ userId }) {
  const { data: user, status, error, execute: loadUser } = useAsync(
    () => fetch(`/api/users/${userId}`).then(r => r.json()),
    { immediate: true }
  );

  if (status === 'pending') return <Spinner />;
  if (status === 'rejected') return <ErrorBanner message={error.message} retry={loadUser} />;
  if (status === 'resolved') return <UserCard user={user} />;
  return null;
}
```

**Compound hook design principles:**
1. **Single Responsibility at the API level** — the hook does one *logical* thing, even if internally it uses five hooks.
2. **Return a structured object** — easier to extend than positional arrays.
3. **Accept options** — use an options object for configuration (`{ immediate, onSuccess, onError }`).
4. **Use refs for mutable values** — `mountedRef`, `fnRef` prevent stale closures and unnecessary effect re-runs.

---

### Q10. How do you implement a middleware pattern with `useReducer`?

**Answer:**

Redux popularized the middleware concept — functions that intercept dispatched actions before they reach the reducer, enabling logging, async side effects, analytics, and more. You can replicate this pattern with `useReducer` by wrapping the dispatch function.

```jsx
import { useReducer, useRef, useCallback } from 'react';

// Middleware: logger
const loggerMiddleware = (state, action, next) => {
  console.group(`Action: ${action.type}`);
  console.log('Prev State:', state);
  const result = next(action);
  console.log('Next State:', result);
  console.groupEnd();
  return result;
};

// Middleware: analytics
const analyticsMiddleware = (state, action, next) => {
  if (action.type === 'PURCHASE_COMPLETE') {
    // Fire analytics event
    window.analytics?.track('purchase', { amount: action.payload.amount });
  }
  return next(action);
};

// Middleware: async action support (thunk-like)
const asyncMiddleware = (state, action, next, dispatch) => {
  if (typeof action === 'function') {
    return action(dispatch, () => state);
  }
  return next(action);
};

function useReducerWithMiddleware(reducer, initialState, middlewares = []) {
  const [state, rawDispatch] = useReducer(reducer, initialState);
  const stateRef = useRef(state);
  stateRef.current = state;

  const dispatch = useCallback((action) => {
    // Build the middleware chain
    const chain = middlewares.reduceRight(
      (next, middleware) => (act) =>
        middleware(stateRef.current, act, next, dispatch),
      rawDispatch
    );
    return chain(action);
  }, [middlewares, rawDispatch]);

  return [state, dispatch];
}

// Application reducer
const cartReducer = (state, action) => {
  switch (action.type) {
    case 'ADD_ITEM':
      return { ...state, items: [...state.items, action.payload] };
    case 'REMOVE_ITEM':
      return { ...state, items: state.items.filter(i => i.id !== action.payload) };
    case 'PURCHASE_COMPLETE':
      return { ...state, items: [], lastOrder: action.payload };
    default:
      return state;
  }
};

function ShoppingCart() {
  const [state, dispatch] = useReducerWithMiddleware(
    cartReducer,
    { items: [], lastOrder: null },
    [loggerMiddleware, analyticsMiddleware, asyncMiddleware]
  );

  // Async action (thunk)
  const checkout = () => {
    dispatch(async (dispatchInner, getState) => {
      const { items } = getState();
      const order = await fetch('/api/checkout', {
        method: 'POST',
        body: JSON.stringify({ items }),
      }).then(r => r.json());
      dispatchInner({ type: 'PURCHASE_COMPLETE', payload: order });
    });
  };

  return (
    <div>
      <ul>
        {state.items.map(item => (
          <li key={item.id}>
            {item.name}
            <button onClick={() => dispatch({ type: 'REMOVE_ITEM', payload: item.id })}>
              Remove
            </button>
          </li>
        ))}
      </ul>
      <button onClick={checkout}>Checkout</button>
    </div>
  );
}
```

This pattern gives you Redux-like middleware capabilities with zero external dependencies, using only `useReducer` and `useRef`.

---

### Q11. How do you implement the "latest ref" pattern to avoid stale closures in hooks?

**Answer:**

Stale closures are one of the most common bugs in React hooks. They happen when a callback (created by `useCallback`, or captured inside `useEffect`) "closes over" a value from a previous render and never sees the updated value.

The **latest ref pattern** solves this: store the value in a `useRef` that is updated every render, and read from the ref inside the closure.

```jsx
import { useRef, useEffect, useCallback } from 'react';

// Generic useLatest hook
function useLatest(value) {
  const ref = useRef(value);
  // Update the ref on every render (synchronously, before effects run)
  ref.current = value;
  return ref;
}

// useStableCallback — a callback that always sees the latest closure
// but has a stable reference (never changes identity)
function useStableCallback(callback) {
  const callbackRef = useLatest(callback);
  // useCallback with [] means the returned function never changes identity
  return useCallback((...args) => callbackRef.current(...args), []);
}

// Production scenario — an interval that uses a value from state
function Counter() {
  const [count, setCount] = useState(0);
  const [step, setStep] = useState(1);

  // Without the latest ref pattern, this effect would always see step=1
  // because the effect only runs once (empty deps)
  const latestStep = useLatest(step);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(c => c + latestStep.current); // always reads current step
    }, 1000);
    return () => clearInterval(id);
  }, []); // empty deps — interval is set up once

  return (
    <div>
      <p>Count: {count}</p>
      <label>
        Step: <input type="number" value={step}
                     onChange={e => setStep(Number(e.target.value))} />
      </label>
    </div>
  );
}

// Another use case — event handler passed to a child that shouldn't re-render
function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  // onSelect always has access to the latest query, but its identity
  // never changes, so ExpensiveList won't re-render
  const onSelect = useStableCallback((item) => {
    console.log(`Selected "${item.name}" while searching for "${query}"`);
    analytics.track('select', { query, itemId: item.id });
  });

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <ExpensiveList items={results} onSelect={onSelect} />
    </div>
  );
}
```

**When to use it:**
- Callbacks passed to memoised children (`React.memo`) that depend on frequently changing state.
- Effects with empty dependency arrays that need access to current values.
- Event handlers registered with non-React systems (WebSocket listeners, third-party libraries).

**Caveat:** This pattern bypasses React's dependency tracking. Use it intentionally — if you can solve the problem with correct dependency arrays, prefer that approach.

---

### Q12. What is `useCallback` vs the proposed `useEvent`, and how do you achieve stable function references today?

**Answer:**

**`useCallback(fn, deps)`** memoises a function — it returns the same reference as long as `deps` haven't changed. The problem: if the callback reads frequently-changing state, its deps change on every render, so the memoisation provides no benefit.

**`useEvent`** (RFC, not yet shipped) was proposed to solve this: it returns a stable function reference that always calls the latest version of your function. It was designed to be the "official" latest-ref pattern. As of React 18.x, `useEvent` is not part of the stable API.

**Today's production solution** — `useStableCallback` (the latest ref pattern from Q11):

```jsx
import { useRef, useCallback, useState, memo } from 'react';

// Our stable callback hook (what useEvent would do)
function useStableCallback(fn) {
  const ref = useRef(fn);
  ref.current = fn;
  return useCallback((...args) => ref.current(...args), []);
}

// A heavy child component
const ChatMessageList = memo(({ messages, onMessageAction }) => {
  console.log('ChatMessageList rendered');
  return (
    <ul>
      {messages.map(msg => (
        <li key={msg.id}>
          {msg.text}
          <button onClick={() => onMessageAction(msg.id, 'delete')}>Delete</button>
          <button onClick={() => onMessageAction(msg.id, 'pin')}>Pin</button>
        </li>
      ))}
    </ul>
  );
});

function ChatRoom({ roomId }) {
  const [messages, setMessages] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connected');

  // Without useStableCallback: this would change identity whenever
  // currentUser or connectionStatus changes, causing ChatMessageList to re-render
  const handleMessageAction = useStableCallback((messageId, action) => {
    if (connectionStatus !== 'connected') {
      alert('You are offline. Action queued.');
      return;
    }
    fetch(`/api/rooms/${roomId}/messages/${messageId}/${action}`, {
      method: 'POST',
      headers: { 'X-User': currentUser?.id },
    });
  });

  return (
    <div>
      <header>Room: {roomId} | Status: {connectionStatus}</header>
      <ChatMessageList messages={messages} onMessageAction={handleMessageAction} />
    </div>
  );
}
```

**Comparison table:**

| | `useCallback` | `useEvent` (proposed) | `useStableCallback` (userland) |
|---|---|---|---|
| Stable identity | Only if deps are stable | Always | Always |
| Reads latest closure | Only when deps update | Yes | Yes |
| Can be called in effects | Yes | No (event handlers only) | Yes (be careful) |
| Status | Stable API | RFC / not shipped | Userland pattern |

For most production code today, `useStableCallback` is the recommended approach until `useEvent` ships.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you implement `usePrevious`, `useLatest`, and `useStableCallback` — and what are their precise semantics?

**Answer:**

These three hooks form a **foundational toolkit** for advanced React patterns. Understanding their implementation and semantics is critical.

```jsx
import { useRef, useEffect, useCallback } from 'react';

/**
 * usePrevious — returns the value from the PREVIOUS render.
 *
 * Semantics:
 * - On the first render, returns `undefined` (there is no previous value).
 * - On subsequent renders, returns the value that was current during the previous render.
 * - The update happens in useEffect (post-render), so during the current render,
 *   ref.current still holds the old value.
 */
function usePrevious(value) {
  const ref = useRef(undefined);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

/**
 * useLatest — always holds the CURRENT render's value.
 *
 * Semantics:
 * - ref.current is updated synchronously during render (assignment in the
 *   function body), so it is always up-to-date when read in effects or callbacks.
 * - Useful for avoiding stale closures.
 */
function useLatest(value) {
  const ref = useRef(value);
  ref.current = value; // synchronous update during render
  return ref;
}

/**
 * useStableCallback — returns a function with a STABLE identity that
 * always invokes the latest version of the provided callback.
 *
 * Semantics:
 * - The returned function reference never changes (empty deps on useCallback).
 * - Inside, it reads from a ref that is updated every render.
 * - Safe to pass to memo'd children without causing re-renders.
 * - Safe to use in useEffect deps without causing re-runs.
 */
function useStableCallback(callback) {
  const ref = useLatest(callback);
  return useCallback((...args) => {
    return ref.current(...args);
  }, []);
}

// ---- Production usage: detecting direction of change ----
function StockTicker({ symbol, price }) {
  const prevPrice = usePrevious(price);

  const direction =
    prevPrice === undefined ? 'neutral' :
    price > prevPrice ? 'up' :
    price < prevPrice ? 'down' : 'neutral';

  return (
    <div className={`ticker ticker--${direction}`}>
      <span>{symbol}</span>
      <span>
        {direction === 'up' && '▲'}
        {direction === 'down' && '▼'}
        ${price.toFixed(2)}
      </span>
      {prevPrice !== undefined && (
        <small>prev: ${prevPrice.toFixed(2)}</small>
      )}
    </div>
  );
}

// ---- Production usage: WebSocket with stable handler ----
function useWebSocket(url, onMessage) {
  const stableOnMessage = useStableCallback(onMessage);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.addEventListener('message', (event) => {
      stableOnMessage(JSON.parse(event.data));
    });
    return () => ws.close();
  }, [url, stableOnMessage]); // stableOnMessage never changes, so only url matters
}

function LiveDashboard() {
  const [metrics, setMetrics] = useState({});
  const [filter, setFilter] = useState('all');

  // This callback reads `filter` (which changes), but doesn't cause
  // the WebSocket to reconnect thanks to useStableCallback
  useWebSocket('wss://api.example.com/metrics', (data) => {
    if (filter === 'all' || data.category === filter) {
      setMetrics(prev => ({ ...prev, [data.key]: data.value }));
    }
  });

  return (
    <div>
      <select value={filter} onChange={e => setFilter(e.target.value)}>
        <option value="all">All</option>
        <option value="cpu">CPU</option>
        <option value="memory">Memory</option>
      </select>
      <MetricsGrid metrics={metrics} />
    </div>
  );
}
```

**Key subtlety:** `usePrevious` updates in `useEffect` (post-render), while `useLatest` updates synchronously during render. This timing difference is what gives them their distinct semantics.

---

### Q14. How do you build hook composition patterns for a plugin system?

**Answer:**

A plugin system allows consumers to extend a hook's behaviour without modifying its source. This is common in headless UI libraries (TanStack Table, Downshift) and form libraries (React Hook Form).

The pattern: the "core" hook accepts an array of plugin hooks, each of which receives shared state and returns extensions (extra state, extra handlers, extra render props).

```jsx
import { useReducer, useMemo, useCallback, useRef } from 'react';

// ---- Core hook ----
function useListManager(items, plugins = []) {
  const [state, dispatch] = useReducer(listReducer, {
    items,
    selected: new Set(),
    focusedIndex: -1,
  });

  // Run each plugin, passing it access to state and dispatch
  const pluginResults = plugins.map(plugin =>
    plugin({ state, dispatch })
  );

  // Merge all plugin extensions into a single API
  const extensions = useMemo(() => {
    return pluginResults.reduce((acc, result) => ({ ...acc, ...result }), {});
  }, [pluginResults]);

  const api = useMemo(() => ({
    // Core API
    items: state.items,
    selected: state.selected,
    select: (id) => dispatch({ type: 'SELECT', payload: id }),
    deselect: (id) => dispatch({ type: 'DESELECT', payload: id }),
    // Spread plugin extensions
    ...extensions,
  }), [state, extensions]);

  return api;
}

function listReducer(state, action) {
  switch (action.type) {
    case 'SELECT':
      return { ...state, selected: new Set([...state.selected, action.payload]) };
    case 'DESELECT': {
      const next = new Set(state.selected);
      next.delete(action.payload);
      return { ...state, selected: next };
    }
    case 'SET_FOCUS':
      return { ...state, focusedIndex: action.payload };
    case 'SORT':
      return { ...state, items: [...state.items].sort(action.payload) };
    default:
      return state;
  }
}

// ---- Plugin: keyboard navigation ----
function useKeyboardNavPlugin({ state, dispatch }) {
  const onKeyDown = useCallback((e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      dispatch({
        type: 'SET_FOCUS',
        payload: Math.min(state.focusedIndex + 1, state.items.length - 1),
      });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      dispatch({
        type: 'SET_FOCUS',
        payload: Math.max(state.focusedIndex - 1, 0),
      });
    } else if (e.key === 'Enter' && state.focusedIndex >= 0) {
      const item = state.items[state.focusedIndex];
      dispatch({ type: 'SELECT', payload: item.id });
    }
  }, [state.focusedIndex, state.items, dispatch]);

  return { onKeyDown, focusedIndex: state.focusedIndex };
}

// ---- Plugin: sort ----
function useSortPlugin({ state, dispatch }) {
  const sortBy = useCallback((compareFn) => {
    dispatch({ type: 'SORT', payload: compareFn });
  }, [dispatch]);

  return { sortBy };
}

// ---- Consumer ----
function FileExplorer({ files }) {
  const {
    items, selected, select,
    onKeyDown, focusedIndex, // from keyboard plugin
    sortBy,                  // from sort plugin
  } = useListManager(files, [useKeyboardNavPlugin, useSortPlugin]);

  return (
    <div onKeyDown={onKeyDown} tabIndex={0} role="listbox">
      <button onClick={() => sortBy((a, b) => a.name.localeCompare(b.name))}>
        Sort A-Z
      </button>
      {items.map((file, i) => (
        <div
          key={file.id}
          role="option"
          aria-selected={selected.has(file.id)}
          className={i === focusedIndex ? 'focused' : ''}
          onClick={() => select(file.id)}
        >
          {file.name}
        </div>
      ))}
    </div>
  );
}
```

**Architecture notes:**
- Plugins are just hooks — they follow the rules of hooks.
- The plugin array must be static (same length and order every render) to satisfy the rules of hooks.
- Each plugin returns a plain object that the core merges into the public API.
- This is the same pattern TanStack Table uses for column sorting, row selection, pagination, etc.

---

### Q15. How do you implement state machines with `useReducer` and optionally integrate with XState?

**Answer:**

A **state machine** makes impossible states impossible. Instead of a bag of booleans (`isLoading`, `isError`, `isSuccess`), you model a finite set of states and explicit transitions between them.

**Pure `useReducer` state machine:**

```jsx
import { useReducer, useEffect } from 'react';

// States: idle | loading | success | error
// Transitions: FETCH (idle→loading), RESOLVE (loading→success),
//              REJECT (loading→error), RETRY (error→loading), RESET (*→idle)
function fetchMachine(state, event) {
  switch (state.status) {
    case 'idle':
      if (event.type === 'FETCH') return { status: 'loading', data: null, error: null };
      return state;

    case 'loading':
      if (event.type === 'RESOLVE') return { status: 'success', data: event.payload, error: null };
      if (event.type === 'REJECT')  return { status: 'error', data: null, error: event.payload };
      return state; // Ignores FETCH while loading — impossible transition!

    case 'success':
      if (event.type === 'RESET') return { status: 'idle', data: null, error: null };
      if (event.type === 'FETCH') return { status: 'loading', data: null, error: null };
      return state;

    case 'error':
      if (event.type === 'RETRY') return { status: 'loading', data: null, error: null };
      if (event.type === 'RESET') return { status: 'idle', data: null, error: null };
      return state;

    default:
      return state;
  }
}

function useFetchMachine(url) {
  const [state, send] = useReducer(fetchMachine, {
    status: 'idle', data: null, error: null,
  });

  useEffect(() => {
    if (state.status !== 'loading') return;

    const controller = new AbortController();

    fetch(url, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => send({ type: 'RESOLVE', payload: data }))
      .catch(err => {
        if (err.name !== 'AbortError') {
          send({ type: 'REJECT', payload: err.message });
        }
      });

    return () => controller.abort();
  }, [state.status, url]);

  return { state, send };
}

function UserProfile({ userId }) {
  const { state, send } = useFetchMachine(`/api/users/${userId}`);

  return (
    <div>
      {state.status === 'idle' && (
        <button onClick={() => send({ type: 'FETCH' })}>Load Profile</button>
      )}
      {state.status === 'loading' && <Spinner />}
      {state.status === 'success' && (
        <div>
          <h2>{state.data.name}</h2>
          <button onClick={() => send({ type: 'RESET' })}>Reset</button>
        </div>
      )}
      {state.status === 'error' && (
        <div>
          <p className="error">{state.error}</p>
          <button onClick={() => send({ type: 'RETRY' })}>Retry</button>
        </div>
      )}
    </div>
  );
}
```

**XState integration (for more complex machines):**

```jsx
import { useMemo } from 'react';
import { useMachine } from '@xstate/react';
import { createMachine, assign } from 'xstate';

const authMachine = createMachine({
  id: 'auth',
  initial: 'loggedOut',
  context: { user: null, error: null, retries: 0 },
  states: {
    loggedOut: {
      on: { LOGIN: 'authenticating' },
    },
    authenticating: {
      invoke: {
        src: 'loginService',
        onDone: {
          target: 'loggedIn',
          actions: assign({ user: (_, event) => event.data }),
        },
        onError: [
          {
            target: 'authenticating',
            cond: (ctx) => ctx.retries < 3,
            actions: assign({ retries: (ctx) => ctx.retries + 1 }),
          },
          {
            target: 'error',
            actions: assign({ error: (_, event) => event.data.message }),
          },
        ],
      },
    },
    loggedIn: {
      on: { LOGOUT: 'loggedOut' },
    },
    error: {
      on: {
        RETRY: {
          target: 'authenticating',
          actions: assign({ retries: 0, error: null }),
        },
      },
    },
  },
});

function LoginPage() {
  const [state, send] = useMachine(authMachine, {
    services: {
      loginService: async (ctx, event) => {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify(event.credentials),
        });
        if (!res.ok) throw new Error('Invalid credentials');
        return res.json();
      },
    },
  });

  return (
    <div>
      {state.matches('loggedOut') && (
        <button onClick={() => send({ type: 'LOGIN', credentials: { user: 'admin', pass: '123' } })}>
          Log In
        </button>
      )}
      {state.matches('authenticating') && <p>Authenticating… (attempt {state.context.retries + 1})</p>}
      {state.matches('loggedIn') && (
        <div>
          <p>Welcome, {state.context.user.name}</p>
          <button onClick={() => send('LOGOUT')}>Log Out</button>
        </div>
      )}
      {state.matches('error') && (
        <div>
          <p className="error">{state.context.error}</p>
          <button onClick={() => send('RETRY')}>Retry</button>
        </div>
      )}
    </div>
  );
}
```

**When to use XState over plain `useReducer`:** When you have parallel states, nested states, guarded transitions, delayed transitions, or invoked services. For simple linear flows, a `useReducer` state machine is sufficient.

---

### Q16. How do you use custom hooks for dependency injection in React?

**Answer:**

Dependency injection (DI) in React hooks means providing different implementations of a dependency (API client, logger, feature flags, time provider) without the hook knowing the concrete implementation. This is essential for testability and modularity.

**Pattern: Context-based DI with a custom hook:**

```jsx
import { createContext, useContext, useMemo } from 'react';

// ---- 1. Define the service interfaces ----
// (In TypeScript, these would be interfaces. In JS, we rely on convention.)

// ---- 2. Create context for each service ----
const ApiClientContext = createContext(null);
const LoggerContext = createContext(null);
const FeatureFlagsContext = createContext(null);

// ---- 3. DI-aware custom hook ----
function useServices() {
  const apiClient = useContext(ApiClientContext);
  const logger = useContext(LoggerContext);
  const featureFlags = useContext(FeatureFlagsContext);

  if (!apiClient || !logger || !featureFlags) {
    throw new Error('useServices must be used within a ServiceProvider');
  }

  return useMemo(
    () => ({ apiClient, logger, featureFlags }),
    [apiClient, logger, featureFlags]
  );
}

// ---- 4. Service provider ----
function ServiceProvider({ apiClient, logger, featureFlags, children }) {
  return (
    <ApiClientContext.Provider value={apiClient}>
      <LoggerContext.Provider value={logger}>
        <FeatureFlagsContext.Provider value={featureFlags}>
          {children}
        </FeatureFlagsContext.Provider>
      </LoggerContext.Provider>
    </ApiClientContext.Provider>
  );
}

// ---- 5. Domain hook that depends on injected services ----
function useUserProfile(userId) {
  const { apiClient, logger, featureFlags } = useServices();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    const endpoint = featureFlags.isEnabled('new-profile-api')
      ? `/api/v2/users/${userId}`
      : `/api/v1/users/${userId}`;

    apiClient.get(endpoint)
      .then(data => {
        if (!cancelled) {
          setProfile(data);
          logger.info('Profile loaded', { userId });
        }
      })
      .catch(err => {
        logger.error('Profile load failed', { userId, error: err.message });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [userId, apiClient, logger, featureFlags]);

  return { profile, loading };
}

// ---- 6. Production setup ----
const prodServices = {
  apiClient: new HttpClient({ baseUrl: 'https://api.example.com' }),
  logger: new DatadogLogger({ service: 'web-app' }),
  featureFlags: new LaunchDarklyClient({ sdkKey: 'prod-key' }),
};

function App() {
  return (
    <ServiceProvider {...prodServices}>
      <Dashboard />
    </ServiceProvider>
  );
}

// ---- 7. Test setup — swap implementations ----
function renderWithMocks(ui, overrides = {}) {
  const testServices = {
    apiClient: { get: vi.fn().mockResolvedValue({ name: 'Test User' }) },
    logger: { info: vi.fn(), error: vi.fn(), warn: vi.fn() },
    featureFlags: { isEnabled: vi.fn().mockReturnValue(false) },
    ...overrides,
  };

  return render(
    <ServiceProvider {...testServices}>{ui}</ServiceProvider>
  );
}

// In a test:
// renderWithMocks(<UserProfile userId="123" />);
// expect(testServices.apiClient.get).toHaveBeenCalledWith('/api/v1/users/123');
```

**Why this matters:** Without DI, hooks that call `fetch` or use `console.log` directly are hard to test, hard to mock, and tightly coupled to their environment. With DI via context, you can swap in mock implementations for tests, Storybook stories, and different environments (staging vs. production) with zero changes to the hooks themselves.

---

### Q17. How does `useSyncExternalStore` power Redux and Zustand under the hood?

**Answer:**

Both Redux (via `react-redux` v8+) and Zustand use `useSyncExternalStore` internally to subscribe to their stores in a concurrent-rendering-safe way. Understanding this reveals how these libraries avoid tearing.

**Simplified Redux `useSelector` implementation:**

```jsx
import { useSyncExternalStore, useRef, useCallback } from 'react';

// Simplified version of what react-redux does internally
function useSelector(selector) {
  const store = useReduxStore(); // gets store from context

  // Memoize the selector result to avoid unnecessary re-renders
  const selectorRef = useRef(selector);
  const resultRef = useRef(undefined);
  const isInitialRef = useRef(true);

  selectorRef.current = selector;

  const getSnapshot = useCallback(() => {
    const newResult = selectorRef.current(store.getState());

    // Only return a new reference if the selected value actually changed
    if (isInitialRef.current || !Object.is(newResult, resultRef.current)) {
      resultRef.current = newResult;
      isInitialRef.current = false;
    }

    return resultRef.current;
  }, [store]);

  const subscribe = useCallback(
    (callback) => store.subscribe(callback),
    [store]
  );

  return useSyncExternalStore(subscribe, getSnapshot);
}

// Usage (identical to the real react-redux)
function CartTotal() {
  const total = useSelector(state =>
    state.cart.items.reduce((sum, item) => sum + item.price * item.qty, 0)
  );

  return <span className="total">${total.toFixed(2)}</span>;
}
```

**Simplified Zustand store creation:**

```jsx
import { useSyncExternalStore } from 'react';

function createStore(initializer) {
  let state;
  const listeners = new Set();

  const getState = () => state;

  const setState = (partial) => {
    const nextState = typeof partial === 'function' ? partial(state) : partial;
    if (!Object.is(nextState, state)) {
      state = typeof nextState === 'object'
        ? Object.assign({}, state, nextState)
        : nextState;
      listeners.forEach(listener => listener());
    }
  };

  const subscribe = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };

  // Initialize the state
  state = initializer(setState, getState);

  // The React hook
  function useStore(selector = getState) {
    return useSyncExternalStore(
      subscribe,
      () => selector(getState()),
      () => selector(getState()) // SSR snapshot
    );
  }

  return { useStore, getState, setState, subscribe };
}

// ---- Production usage ----
const useAppStore = createStore((set, get) => ({
  count: 0,
  todos: [],
  increment: () => set(s => ({ count: s.count + 1 })),
  addTodo: (text) => set(s => ({
    todos: [...s.todos, { id: Date.now(), text, done: false }],
  })),
  toggleTodo: (id) => set(s => ({
    todos: s.todos.map(t => t.id === id ? { ...t, done: !t.done } : t),
  })),
}));

// Components subscribe to slices — only re-render when their slice changes
function Counter() {
  const count = useAppStore.useStore(s => s.count);
  const increment = useAppStore.useStore(s => s.increment);
  return <button onClick={increment}>Count: {count}</button>;
}

function TodoList() {
  const todos = useAppStore.useStore(s => s.todos);
  const addTodo = useAppStore.useStore(s => s.addTodo);
  const toggleTodo = useAppStore.useStore(s => s.toggleTodo);

  return (
    <div>
      <button onClick={() => addTodo('New task')}>Add Todo</button>
      <ul>
        {todos.map(t => (
          <li
            key={t.id}
            onClick={() => toggleTodo(t.id)}
            style={{ textDecoration: t.done ? 'line-through' : 'none' }}
          >
            {t.text}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Why `useSyncExternalStore` matters here:** Without it, under concurrent rendering, `Counter` might render with `count = 5` while `TodoList` renders with the state where `count = 4`. `useSyncExternalStore` forces React to use a consistent snapshot for all components in the same render pass, eliminating tearing.

---

### Q18. How do you build `useUndo` / `useRedo` with `useReducer`?

**Answer:**

Undo/redo is a classic use case for `useReducer` because it requires tracking past and future states — a pure function that manipulates a stack is perfect.

```jsx
import { useReducer, useCallback, useMemo } from 'react';

function undoReducer(state, action) {
  const { past, present, future } = state;

  switch (action.type) {
    case 'SET': {
      if (Object.is(action.payload, present)) return state;
      return {
        past: [...past, present],
        present: action.payload,
        future: [], // new action clears redo stack
      };
    }
    case 'UNDO': {
      if (past.length === 0) return state;
      const previous = past[past.length - 1];
      return {
        past: past.slice(0, -1),
        present: previous,
        future: [present, ...future],
      };
    }
    case 'REDO': {
      if (future.length === 0) return state;
      const next = future[0];
      return {
        past: [...past, present],
        present: next,
        future: future.slice(1),
      };
    }
    case 'RESET': {
      return {
        past: [],
        present: action.payload,
        future: [],
      };
    }
    default:
      return state;
  }
}

function useUndo(initialPresent) {
  const [state, dispatch] = useReducer(undoReducer, {
    past: [],
    present: initialPresent,
    future: [],
  });

  const set = useCallback((newPresent) => {
    dispatch({ type: 'SET', payload: newPresent });
  }, []);

  const undo = useCallback(() => dispatch({ type: 'UNDO' }), []);
  const redo = useCallback(() => dispatch({ type: 'REDO' }), []);
  const reset = useCallback((newPresent) => {
    dispatch({ type: 'RESET', payload: newPresent });
  }, []);

  const api = useMemo(() => ({
    state: state.present,
    past: state.past,
    future: state.future,
    set,
    undo,
    redo,
    reset,
    canUndo: state.past.length > 0,
    canRedo: state.future.length > 0,
    historySize: state.past.length + state.future.length + 1,
  }), [state, set, undo, redo, reset]);

  return api;
}

// ---- Production: A drawing canvas with undo/redo ----
function PixelCanvas({ width = 16, height = 16 }) {
  const initialGrid = Array(height).fill(null).map(() =>
    Array(width).fill('#ffffff')
  );

  const {
    state: grid, set, undo, redo, canUndo, canRedo, reset, historySize,
  } = useUndo(initialGrid);

  const [color, setColor] = useState('#000000');

  const handleCellClick = (row, col) => {
    const newGrid = grid.map((r, ri) =>
      r.map((c, ci) => (ri === row && ci === col ? color : c))
    );
    set(newGrid);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [undo, redo]);

  return (
    <div>
      <div className="toolbar">
        <input type="color" value={color} onChange={e => setColor(e.target.value)} />
        <button onClick={undo} disabled={!canUndo}>Undo</button>
        <button onClick={redo} disabled={!canRedo}>Redo</button>
        <button onClick={() => reset(initialGrid)}>Clear</button>
        <span>History: {historySize} states</span>
      </div>
      <div className="grid" style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${width}, 20px)`,
      }}>
        {grid.map((row, ri) =>
          row.map((cellColor, ci) => (
            <div
              key={`${ri}-${ci}`}
              onClick={() => handleCellClick(ri, ci)}
              style={{
                width: 20, height: 20,
                backgroundColor: cellColor,
                border: '1px solid #eee',
                cursor: 'pointer',
              }}
            />
          ))
        )}
      </div>
    </div>
  );
}
```

**Production considerations:**
- **Memory:** For large states, store diffs instead of full snapshots. Libraries like `immer` make this easier with patches.
- **Max history:** Cap `past.length` (e.g., keep only the last 50 states) to avoid memory leaks.
- **Batching:** Group rapid changes (like dragging on the canvas) into a single undo step using a debounce before calling `set`.

---

### Q19. How do hooks interact with concurrent rendering, and what are the safety rules?

**Answer:**

React 18's concurrent rendering means that React can **start rendering** a component, **pause**, work on something else (like a higher-priority update), and **resume** or even **discard** the partially completed render. This has profound implications for hooks.

**The core safety rules:**

1. **The render function must be pure.** No side effects, no mutations, no DOM access during render. React may call your component function multiple times without committing.

2. **`useRef` reads/writes during render are unsafe under concurrent rendering** (except for initialising on first render). Reading `ref.current` during render can give stale data if React discards and retries.

3. **External store subscriptions must go through `useSyncExternalStore`** — not `useEffect` + `useState`, which can tear.

4. **Side effects belong in `useEffect` / `useLayoutEffect`** — they only run after React commits to the DOM.

5. **`useState` and `useReducer` updater functions must be pure** — `setState(prev => ...)` may be called multiple times under Strict Mode.

```jsx
import { useState, useRef, useEffect, useSyncExternalStore } from 'react';

// ❌ UNSAFE: reading/writing ref during render
function UnsafeCounter() {
  const countRef = useRef(0);
  const [, forceRender] = useState(0);

  // BAD: mutating ref during render — concurrent rendering may call this
  // multiple times, incrementing the ref more than expected
  countRef.current += 1;

  return <p>Render count: {countRef.current}</p>;
}

// ✅ SAFE: ref mutation in useEffect (commit phase)
function SafeCounter() {
  const countRef = useRef(0);
  const [renderCount, setRenderCount] = useState(0);

  useEffect(() => {
    // This runs exactly once per commit — safe to mutate refs
    countRef.current += 1;
    setRenderCount(countRef.current);
  });

  return <p>Render count: {renderCount}</p>;
}

// ❌ UNSAFE: external store via useEffect (can tear)
function UnsafeStoreConsumer() {
  const [value, setValue] = useState(externalStore.getValue());

  useEffect(() => {
    return externalStore.subscribe(() => {
      setValue(externalStore.getValue());
    });
  }, []);

  // Between render start and effect, the store may have changed.
  // Under concurrent rendering, this component and another may
  // read different values in the same render pass = tearing.
  return <span>{value}</span>;
}

// ✅ SAFE: external store via useSyncExternalStore
function SafeStoreConsumer() {
  const value = useSyncExternalStore(
    externalStore.subscribe,
    externalStore.getValue,
    externalStore.getServerValue
  );

  return <span>{value}</span>;
}

// ---- Demonstrating startTransition safety ----
import { startTransition } from 'react';

function SearchWithTransition() {
  const [query, setQuery] = useState('');
  const [deferredResults, setDeferredResults] = useState([]);

  const handleChange = (e) => {
    const value = e.target.value;
    // Urgent: update input immediately
    setQuery(value);

    // Non-urgent: update results list — React can interrupt this
    startTransition(() => {
      // This setState may be called, discarded, and called again
      // with a newer value. That's fine because it's pure.
      setDeferredResults(computeSearchResults(value));
    });
  };

  return (
    <div>
      <input value={query} onChange={handleChange} />
      <ul>
        {deferredResults.map(r => <li key={r.id}>{r.title}</li>)}
      </ul>
    </div>
  );
}
```

**Summary of concurrent-safe hook patterns:**

| Pattern | Safe? | Why |
|---|---|---|
| `useState` / `useReducer` | Yes | React manages these internally |
| `useRef` read in event handlers | Yes | Event handlers run after commit |
| `useRef` read/write during render | **No** | Render may run multiple times |
| `useEffect` for side effects | Yes | Runs only after commit |
| `useSyncExternalStore` for external data | Yes | Designed for concurrent mode |
| `useEffect` + `useState` for external data | **No** | Subject to tearing |
| Pure computation during render | Yes | Pure functions are safe to re-run |
| `startTransition` + `useState` | Yes | React handles interruption gracefully |

---

### Q20. Production: How do you build a complex hook for real-time collaborative editing?

**Answer:**

Real-time collaborative editing (like Google Docs) is one of the hardest problems in frontend engineering. It requires managing local state, remote state, conflict resolution (typically via CRDTs or Operational Transformation), presence tracking, and offline support — all while keeping the UI responsive.

Here is a production-grade `useCollaborativeEditor` hook that composes multiple lower-level hooks:

```jsx
import {
  useReducer, useRef, useEffect, useCallback,
  useSyncExternalStore, useMemo
} from 'react';

// ---- CRDT-based document model (simplified Yjs-style) ----
class CollaborativeDocument {
  constructor(docId) {
    this.docId = docId;
    this.content = '';
    this.version = 0;
    this.pendingOps = [];
    this.listeners = new Set();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getSnapshot() {
    return { content: this.content, version: this.version };
  }

  getServerSnapshot() {
    return { content: '', version: 0 };
  }

  applyLocal(op) {
    this.content = applyOperation(this.content, op);
    this.version++;
    this.pendingOps.push(op);
    this.notify();
  }

  applyRemote(ops) {
    for (const op of ops) {
      // Transform against pending local ops (OT) to avoid conflicts
      const transformedOp = transformOperation(op, this.pendingOps);
      this.content = applyOperation(this.content, transformedOp);
      this.version++;
    }
    this.notify();
  }

  acknowledgePending(upToVersion) {
    this.pendingOps = this.pendingOps.filter(op => op.version > upToVersion);
  }

  notify() {
    this.listeners.forEach(fn => fn());
  }
}

// ---- Presence tracking ----
const presenceReducer = (state, action) => {
  switch (action.type) {
    case 'USER_JOINED':
      return { ...state, [action.payload.userId]: action.payload };
    case 'USER_LEFT': {
      const { [action.payload]: _, ...rest } = state;
      return rest;
    }
    case 'CURSOR_MOVED':
      return {
        ...state,
        [action.payload.userId]: {
          ...state[action.payload.userId],
          cursor: action.payload.cursor,
          lastActive: Date.now(),
        },
      };
    default:
      return state;
  }
};

// ---- The main composite hook ----
function useCollaborativeEditor(docId, currentUser) {
  // 1. Document model (CRDT)
  const docRef = useRef(null);
  if (!docRef.current) {
    docRef.current = new CollaborativeDocument(docId);
  }
  const doc = docRef.current;

  // 2. Subscribe to document changes (concurrent-safe)
  const docSnapshot = useSyncExternalStore(
    (cb) => doc.subscribe(cb),
    () => doc.getSnapshot(),
    () => doc.getServerSnapshot()
  );

  // 3. Presence state
  const [presence, dispatchPresence] = useReducer(presenceReducer, {});

  // 4. Connection management
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(`wss://collab.example.com/docs/${docId}`);

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'join',
        userId: currentUser.id,
        name: currentUser.name,
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'ops':
          doc.applyRemote(message.operations);
          break;
        case 'ack':
          doc.acknowledgePending(message.version);
          break;
        case 'user_joined':
          dispatchPresence({ type: 'USER_JOINED', payload: message.user });
          break;
        case 'user_left':
          dispatchPresence({ type: 'USER_LEFT', payload: message.userId });
          break;
        case 'cursor':
          dispatchPresence({ type: 'CURSOR_MOVED', payload: message });
          break;
      }
    };

    ws.onclose = () => {
      // Auto-reconnect with exponential backoff
      reconnectTimeoutRef.current = setTimeout(connect, 2000);
    };

    wsRef.current = ws;
  }, [docId, currentUser, doc]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  // 5. Local editing operations
  const insertText = useCallback((position, text) => {
    const op = { type: 'insert', position, text, version: doc.version };
    doc.applyLocal(op);

    // Send to server
    wsRef.current?.send(JSON.stringify({
      type: 'op',
      operation: op,
    }));
  }, [doc]);

  const deleteText = useCallback((position, length) => {
    const op = { type: 'delete', position, length, version: doc.version };
    doc.applyLocal(op);

    wsRef.current?.send(JSON.stringify({
      type: 'op',
      operation: op,
    }));
  }, [doc]);

  // 6. Cursor broadcasting (debounced)
  const broadcastCursorTimeoutRef = useRef(null);
  const broadcastCursor = useCallback((cursor) => {
    clearTimeout(broadcastCursorTimeoutRef.current);
    broadcastCursorTimeoutRef.current = setTimeout(() => {
      wsRef.current?.send(JSON.stringify({
        type: 'cursor',
        userId: currentUser.id,
        cursor,
      }));
    }, 50); // debounce 50ms
  }, [currentUser.id]);

  // 7. Offline queue (persist pending ops to localStorage)
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (doc.pendingOps.length > 0) {
        localStorage.setItem(
          `collab-pending-${docId}`,
          JSON.stringify(doc.pendingOps)
        );
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [doc, docId]);

  // Restore pending ops on mount
  useEffect(() => {
    const saved = localStorage.getItem(`collab-pending-${docId}`);
    if (saved) {
      const ops = JSON.parse(saved);
      ops.forEach(op => doc.applyLocal(op));
      localStorage.removeItem(`collab-pending-${docId}`);
    }
  }, [docId, doc]);

  // 8. Return the public API
  return useMemo(() => ({
    // Document state
    content: docSnapshot.content,
    version: docSnapshot.version,

    // Editing operations
    insertText,
    deleteText,

    // Presence
    presence,
    broadcastCursor,

    // Metadata
    pendingOpsCount: doc.pendingOps.length,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  }), [docSnapshot, insertText, deleteText, presence, broadcastCursor, doc]);
}

// ---- Consumer component ----
function CollaborativeEditor({ docId }) {
  const currentUser = useCurrentUser(); // from auth context

  const {
    content, version, insertText, deleteText,
    presence, broadcastCursor, pendingOpsCount, isConnected,
  } = useCollaborativeEditor(docId, currentUser);

  const editorRef = useRef(null);

  const handleInput = (e) => {
    const { selectionStart, selectionEnd } = e.target;

    // Simplified — in production, diff the old and new content
    // to determine the exact insert/delete operations
    const newContent = e.target.value;
    if (newContent.length > content.length) {
      const inserted = newContent.slice(selectionStart - 1, selectionStart);
      insertText(selectionStart - 1, inserted);
    } else {
      deleteText(selectionStart, content.length - newContent.length);
    }
  };

  const handleSelect = () => {
    const { selectionStart, selectionEnd } = editorRef.current;
    broadcastCursor({ start: selectionStart, end: selectionEnd });
  };

  return (
    <div className="collab-editor">
      <header className="toolbar">
        <span className={`status ${isConnected ? 'online' : 'offline'}`}>
          {isConnected ? 'Connected' : 'Reconnecting…'}
        </span>
        <span>v{version}</span>
        {pendingOpsCount > 0 && (
          <span className="pending">Syncing {pendingOpsCount} changes…</span>
        )}
        <div className="avatars">
          {Object.values(presence).map(user => (
            <span
              key={user.userId}
              className="avatar"
              title={user.name}
              style={{ backgroundColor: user.color }}
            >
              {user.name[0]}
            </span>
          ))}
        </div>
      </header>

      <div className="editor-container" style={{ position: 'relative' }}>
        <textarea
          ref={editorRef}
          value={content}
          onChange={handleInput}
          onSelect={handleSelect}
          className="editor"
          spellCheck={false}
        />

        {/* Remote cursors overlay */}
        {Object.values(presence)
          .filter(u => u.userId !== currentUser.id && u.cursor)
          .map(user => (
            <RemoteCursor
              key={user.userId}
              name={user.name}
              color={user.color}
              position={user.cursor}
              content={content}
            />
          ))
        }
      </div>
    </div>
  );
}

function RemoteCursor({ name, color, position, content }) {
  // Calculate pixel position from character offset
  // (simplified — production would use a more precise measurement)
  const lines = content.slice(0, position.start).split('\n');
  const line = lines.length - 1;
  const col = lines[lines.length - 1].length;

  return (
    <div
      className="remote-cursor"
      style={{
        position: 'absolute',
        top: `${line * 1.5}em`,
        left: `${col * 0.6}em`,
        borderLeft: `2px solid ${color}`,
        height: '1.5em',
        pointerEvents: 'none',
      }}
    >
      <span
        className="cursor-label"
        style={{ backgroundColor: color, color: '#fff', fontSize: '10px' }}
      >
        {name}
      </span>
    </div>
  );
}
```

**Architecture summary of hooks used:**

| Hook | Purpose in this system |
|---|---|
| `useSyncExternalStore` | Subscribing to the CRDT document model (concurrent-safe) |
| `useReducer` | Managing presence state with named actions |
| `useRef` | Holding the WebSocket, document instance, and timeouts (mutable values) |
| `useEffect` | WebSocket lifecycle, offline persistence, cleanup |
| `useCallback` | Stable references for `insertText`, `deleteText`, `broadcastCursor` |
| `useMemo` | Constructing the stable return object |

**Production hardening checklist:**
- Replace simplified OT with a battle-tested CRDT library (Yjs, Automerge).
- Add exponential backoff with jitter for WebSocket reconnection.
- Implement proper operational transformation for concurrent edits.
- Add conflict resolution UI for divergent states.
- Use `useLayoutEffect` for cursor position measurement to avoid flicker.
- Add end-to-end encryption for sensitive documents.
- Implement rate limiting on cursor broadcasts.
- Add comprehensive error boundaries around the editor.

---

*End of Advanced Hooks & Patterns — 20 Interview Questions*
