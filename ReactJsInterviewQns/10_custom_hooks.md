# Topic 10: Custom Hooks in React 18

## Introduction

Custom hooks are one of React's most powerful composition primitives. A custom hook is simply a JavaScript function whose name starts with `use` and that may call other hooks (such as `useState`, `useEffect`, `useRef`, `useMemo`, or even other custom hooks) inside its body. They allow you to extract stateful logic out of components and into reusable, testable units — without changing the component hierarchy and without resorting to render props or higher-order components. Because a custom hook is just a function, every call to it gets its own isolated state: if two components call `useToggle()`, each component receives a completely independent `isOpen` boolean and `toggle` function. Custom hooks follow the exact same Rules of Hooks that built-in hooks follow — they must be called at the top level of a React function (not inside conditions, loops, or nested functions) and they must be called from a React function component or from another custom hook.

In a production React 18 codebase, custom hooks become the standard building blocks for virtually every cross-cutting concern: data fetching, authentication, form validation, responsive breakpoints, websocket connections, intersection observers, analytics tracking, debounced inputs, optimistic mutations, and more. Teams typically build internal hook libraries that encapsulate company-specific patterns — for example, a `useFetch` hook that automatically attaches auth tokens, retries on 401s, integrates with a global error boundary, and leverages React 18's `useSyncExternalStore` for cache synchronisation. When hooks are well-designed, components become thin rendering layers that simply declare *what* they need, while the hooks handle *how* to get it. This separation dramatically improves testability (you can test the hook in isolation with `renderHook` from React Testing Library), readability (the component JSX is free of imperative logic), and reuse (the same hook works in any component, page, or even across projects).

Here is a foundational illustration showing a custom hook that encapsulates a toggle pattern and a component that consumes it:

```jsx
import { useState, useCallback } from 'react';

// Custom hook — name starts with "use", calls built-in hooks
function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => setValue(v => !v), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse };
}

// Component that consumes the hook — no toggle logic leaks into the JSX
function Accordion({ title, children }) {
  const { value: isOpen, toggle } = useToggle(false);

  return (
    <div className="accordion">
      <button onClick={toggle} aria-expanded={isOpen}>
        {title} {isOpen ? '▲' : '▼'}
      </button>
      {isOpen && <div className="accordion-body">{children}</div>}
    </div>
  );
}
```

This snippet demonstrates the core idea: `useToggle` owns the boolean state and exposes a stable API (`toggle`, `setTrue`, `setFalse`), while `Accordion` is a pure rendering component that simply destructures what it needs. Every question below builds on this principle and pushes it into increasingly complex, production-grade scenarios.

---

## Beginner Level (Q1–Q5)

---

### Q1. What is a custom hook in React, and what are the rules for creating one?

**Answer:**

A custom hook is a regular JavaScript function whose name begins with the prefix `use` and that internally calls one or more React hooks (`useState`, `useEffect`, `useRef`, `useCallback`, `useMemo`, `useContext`, or other custom hooks). The `use` prefix is not merely a naming convention — it signals to React's linter plugin (`eslint-plugin-react-hooks`) and to the React runtime that this function follows the Rules of Hooks, enabling static analysis to verify correct usage.

The rules for creating a custom hook are:

1. **Name must start with `use`:** This is enforced by convention and by the linter. A function named `fetchData` that calls `useState` inside it will trigger a lint warning because the linter cannot verify that it is called correctly. Naming it `useFetchData` resolves this.
2. **Call hooks at the top level:** Inside your custom hook, you must call other hooks unconditionally — not inside `if` blocks, loops, or nested functions. This ensures React can preserve the correct order of hook calls between renders.
3. **Call hooks only from React functions:** A custom hook must be called either from a React function component or from another custom hook — never from a regular JavaScript function, a class method, or an event handler.
4. **Return whatever the consumer needs:** There is no required return shape. You can return a single value, an array (like `useState` returns `[state, setter]`), or an object with named fields. An object is generally preferred when there are more than two return values, because destructuring by name is more readable and refactor-safe than destructuring by position.

```jsx
import { useState, useEffect } from 'react';

// ✅ Valid custom hook — name starts with "use", calls hooks at top level
function useWindowWidth() {
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return width;
}

// ❌ Bad — does NOT start with "use", so the linter cannot verify hook rules
function getWindowWidth() {
  const [width, setWidth] = useState(window.innerWidth); // lint error
  // ...
}

// Usage in a component
function ResponsiveHeader() {
  const width = useWindowWidth();
  return <header>{width > 768 ? 'Desktop' : 'Mobile'} Header</header>;
}
```

Each component that calls `useWindowWidth()` gets its own independent `width` state. The hook encapsulates the subscription logic (adding/removing the `resize` listener) so that no component has to think about it.

---

### Q2. How do you build a simple `useToggle` custom hook, and why is it useful?

**Answer:**

`useToggle` is one of the simplest and most commonly used custom hooks. It wraps a boolean `useState` and provides stable callback functions to flip, set true, or set false the boolean — saving every consumer from re-implementing the same three-line pattern. It is useful any time the UI has binary state: modals (open/closed), accordions (expanded/collapsed), dark mode (on/off), sidebars (visible/hidden), etc.

The key design decision is wrapping the setter callbacks in `useCallback` so they maintain referential stability across renders. This prevents unnecessary re-renders of child components that receive these callbacks as props.

```jsx
import { useState, useCallback } from 'react';

function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue);

  // All callbacks use functional updater or constant — no dependencies needed
  const toggle = useCallback(() => setValue(prev => !prev), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse };
}

// --- Usage: Modal ---
function SettingsPage() {
  const { value: isModalOpen, setTrue: openModal, setFalse: closeModal } = useToggle();

  return (
    <div>
      <h1>Settings</h1>
      <button onClick={openModal}>Edit Profile</button>

      {isModalOpen && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Edit Profile</h2>
            <form>{/* form fields */}</form>
            <button onClick={closeModal}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Usage: Dark mode ---
function ThemeToggle() {
  const { value: isDark, toggle } = useToggle(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches
  );

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
  }, [isDark]);

  return (
    <button onClick={toggle} aria-pressed={isDark}>
      {isDark ? '🌙' : '☀️'} Theme
    </button>
  );
}
```

Note that `useToggle` also accepts a lazy initialiser (a function) because `useState` itself supports lazy initialisation. This means the dark mode example can read the user's OS preference only on the first render.

---

### Q3. How do you build a `useLocalStorage` hook that persists state across page reloads?

**Answer:**

`useLocalStorage` is a drop-in replacement for `useState` that automatically reads the initial value from `localStorage` and writes back to `localStorage` whenever the value changes. This is invaluable for persisting user preferences (theme, language, sidebar collapsed state), form drafts, and feature flags across sessions.

Key implementation details:

- **Lazy initialisation:** We pass a function to `useState` so we only read from `localStorage` once (on mount), not on every render.
- **JSON serialisation:** `localStorage` stores strings, so we `JSON.stringify` on write and `JSON.parse` on read.
- **Error handling:** `localStorage` can throw (private browsing mode in some browsers, quota exceeded, or corrupted data). We wrap reads and writes in try/catch.
- **Cross-tab sync (optional):** We listen for the `storage` event so that if another tab updates the same key, this tab stays in sync.

```jsx
import { useState, useEffect, useCallback } from 'react';

function useLocalStorage(key, initialValue) {
  // Lazy initialiser — runs only on mount
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item !== null ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Write to localStorage whenever key or value changes
  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (error) {
      console.warn(`Error writing localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  // Sync across tabs
  useEffect(() => {
    const handleStorageChange = (event) => {
      if (event.key === key && event.newValue !== null) {
        try {
          setStoredValue(JSON.parse(event.newValue));
        } catch {
          setStoredValue(initialValue);
        }
      }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, initialValue]);

  // Stable setter that also updates localStorage
  const setValue = useCallback(
    (valueOrFn) => {
      setStoredValue((prev) => {
        const nextValue = typeof valueOrFn === 'function' ? valueOrFn(prev) : valueOrFn;
        return nextValue;
      });
    },
    []
  );

  return [storedValue, setValue];
}

// --- Usage ---
function UserPreferences() {
  const [theme, setTheme] = useLocalStorage('theme', 'light');
  const [fontSize, setFontSize] = useLocalStorage('fontSize', 16);

  return (
    <div>
      <label>
        Theme:
        <select value={theme} onChange={e => setTheme(e.target.value)}>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </label>
      <label>
        Font Size:
        <input
          type="range"
          min={12}
          max={24}
          value={fontSize}
          onChange={e => setFontSize(Number(e.target.value))}
        />
        {fontSize}px
      </label>
    </div>
  );
}
```

Because the `storage` event only fires in *other* tabs (not the tab that made the change), the hook stays consistent across tabs without causing infinite loops. If you need same-tab synchronisation between different components using the same key, you would layer a context or an external store on top.

---

### Q4. How do you build a `useFetch` custom hook that manages loading, error, and data states for API calls?

**Answer:**

`useFetch` encapsulates the extremely common pattern of fetching data when a component mounts (or when a dependency changes) and tracking three pieces of state: `data`, `loading`, and `error`. Without a custom hook, every component that fetches data would duplicate this same boilerplate. By extracting it into `useFetch`, the component only needs to supply a URL and can destructure the result.

Important production considerations handled below:

- **Abort on unmount:** We use `AbortController` to cancel in-flight requests when the component unmounts or when the URL changes, preventing the "set state on an unmounted component" warning.
- **Race condition protection:** Because the effect cleanup aborts the previous request, we never apply stale data from an older request that resolves after a newer one.
- **Re-fetch capability:** We expose a `refetch` function so the consumer can trigger a manual reload (e.g., pull-to-refresh).

```jsx
import { useState, useEffect, useCallback, useRef } from 'react';

function useFetch(url, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  const fetchData = useCallback(async () => {
    // Abort any in-flight request
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const json = await response.json();

      if (!controller.signal.aborted) {
        setData(json);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err);
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, [url]);

  useEffect(() => {
    fetchData();
    return () => abortControllerRef.current?.abort();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// --- Usage ---
function UserList() {
  const { data: users, loading, error, refetch } = useFetch('/api/users');

  if (loading) return <div className="skeleton-list" />;
  if (error) return (
    <div className="error-banner">
      <p>Failed to load users: {error.message}</p>
      <button onClick={refetch}>Retry</button>
    </div>
  );

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name} — {user.email}</li>
      ))}
    </ul>
  );
}
```

This basic `useFetch` is ideal for learning, but production apps typically layer on caching, deduplication, background re-fetching, and pagination — which is why libraries like TanStack Query exist. Still, understanding how to build `useFetch` from scratch is critical interview knowledge.

---

### Q5. When should you extract component logic into a custom hook?

**Answer:**

Extracting logic into a custom hook is warranted in several situations. The core rule of thumb is: **if two or more components share the same stateful logic, or if a single component's logic is complex enough to obscure its rendering intent, pull that logic into a custom hook.**

Specific signals that extraction is appropriate:

1. **Duplicated stateful patterns:** Two components both subscribe to window resize, or both debounce an input, or both fetch data on mount — extract the shared pattern into a hook.
2. **Complex effect orchestration:** A component has multiple `useEffect` calls that interact with each other (e.g., a websocket connection that depends on an auth token that depends on a refresh timer). Moving this into a dedicated hook makes each piece testable and the component readable.
3. **Testability:** You want to test the logic (state transitions, side effects) independently of the JSX. `renderHook` from `@testing-library/react` lets you test hooks in isolation.
4. **Separation of concerns:** The component is mixing "how to get data" with "how to display data." Hooks let you push the imperative "how" behind a declarative API.
5. **Cross-cutting concerns:** Authentication state, analytics tracking, feature flags, theming — these cut across many components and belong in hooks.

When **not** to extract: if the logic is trivially simple (a single `useState` for a form field), used by only one component, and makes the component less readable by forcing you to jump between files.

```jsx
// ❌ Before: duplicated logic in two components
function SearchPage() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  // ... use debouncedQuery to fetch results
}

function AutocompletePage() {
  const [input, setInput] = useState('');
  const [debouncedInput, setDebouncedInput] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedInput(input), 300);
    return () => clearTimeout(timer);
  }, [input]);

  // ... use debouncedInput to fetch suggestions
}

// ✅ After: shared logic extracted into a custom hook
function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

function SearchPage() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  // ... use debouncedQuery to fetch results — zero boilerplate
}

function AutocompletePage() {
  const [input, setInput] = useState('');
  const debouncedInput = useDebounce(input, 300);
  // ... use debouncedInput to fetch suggestions — zero boilerplate
}
```

The refactored version is shorter, eliminates duplication, and makes each component's intent immediately obvious. If the debounce delay ever needs to change or the implementation needs to switch to `requestAnimationFrame`, you update one place.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you build a `useDebounce` hook, and what are its production use cases?

**Answer:**

`useDebounce` delays updating a value until a specified period of inactivity has passed. This is essential for performance in production: without debouncing, a search input that fires an API call on every keystroke would flood the server with requests and cause UI jank. `useDebounce` ensures the expensive operation (network request, heavy computation) only runs after the user pauses typing.

The implementation uses `useEffect` with a `setTimeout`. Every time the input value changes, the previous timer is cleared and a new one is set. Only when the value is stable for the full delay does the debounced value update, triggering downstream effects.

Advanced production considerations include:
- **Leading vs. trailing:** Sometimes you want the first value to fire immediately (leading edge) and then debounce subsequent changes. The hook below supports this via an `options` parameter.
- **Cancel capability:** Expose a `cancel` function so the consumer can abort the pending debounce (e.g., when a form is submitted immediately).
- **Max wait:** Cap the maximum time between invocations to prevent the debounce from delaying too long during continuous input.

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

function useDebounce(value, delay = 300, options = {}) {
  const { leading = false } = options;
  const [debouncedValue, setDebouncedValue] = useState(value);
  const timerRef = useRef(null);
  const isFirstRender = useRef(true);

  useEffect(() => {
    // Leading edge: update immediately on first change
    if (leading && isFirstRender.current) {
      setDebouncedValue(value);
      isFirstRender.current = false;
      return;
    }

    timerRef.current = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timerRef.current);
  }, [value, delay, leading]);

  const cancel = useCallback(() => {
    clearTimeout(timerRef.current);
  }, []);

  return leading ? { debouncedValue, cancel } : debouncedValue;
}

// --- Production usage: Search with API call ---
function ProductSearch() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 400);

  const { data: results, loading } = useFetch(
    debouncedQuery ? `/api/products?search=${encodeURIComponent(debouncedQuery)}` : null
  );

  return (
    <div>
      <input
        type="search"
        placeholder="Search products..."
        value={query}
        onChange={e => setQuery(e.target.value)}
      />
      {loading && <div className="spinner" />}
      {results?.map(product => (
        <div key={product.id} className="product-card">
          <h3>{product.name}</h3>
          <p>${product.price}</p>
        </div>
      ))}
    </div>
  );
}

// --- Production usage: Auto-save form draft ---
function ArticleEditor() {
  const [content, setContent] = useState('');
  const debouncedContent = useDebounce(content, 1000);

  useEffect(() => {
    if (debouncedContent) {
      fetch('/api/drafts', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: debouncedContent }),
      });
    }
  }, [debouncedContent]);

  return (
    <textarea
      value={content}
      onChange={e => setContent(e.target.value)}
      placeholder="Write your article..."
    />
  );
}
```

The `ProductSearch` example only calls `/api/products` after the user stops typing for 400ms — massively reducing server load. The `ArticleEditor` example auto-saves the draft one second after the last edit, preventing data loss without hammering the API.

---

### Q7. How do you build a `usePrevious` hook to track the value from the previous render?

**Answer:**

`usePrevious` captures and returns the value that a variable held during the *previous* render. This is useful for comparing current and previous values to trigger animations, log changes, conditionally run effects, or display "changed from X to Y" UI.

The classic implementation uses `useRef` because refs persist across renders without causing re-renders. The trick is that `useEffect` runs *after* render, so by the time the effect updates the ref, the component has already rendered with the current value — meaning the ref still holds the *previous* value during the render phase.

```jsx
import { useRef, useEffect } from 'react';

function usePrevious(value) {
  const ref = useRef(undefined);

  useEffect(() => {
    ref.current = value;
  }); // No dependency array — runs after every render

  return ref.current;
}

// --- Usage: Highlight price changes ---
function StockTicker({ symbol, price }) {
  const prevPrice = usePrevious(price);

  const direction = prevPrice !== undefined
    ? price > prevPrice ? 'up' : price < prevPrice ? 'down' : 'unchanged'
    : 'unchanged';

  return (
    <div className={`ticker ticker--${direction}`}>
      <span className="symbol">{symbol}</span>
      <span className="price">${price.toFixed(2)}</span>
      {prevPrice !== undefined && prevPrice !== price && (
        <span className="change">
          {direction === 'up' ? '▲' : '▼'}
          {Math.abs(price - prevPrice).toFixed(2)}
        </span>
      )}
    </div>
  );
}

// --- Usage: Log state transitions for debugging ---
function OrderStatus({ status }) {
  const prevStatus = usePrevious(status);

  useEffect(() => {
    if (prevStatus && prevStatus !== status) {
      console.log(`Order status changed: ${prevStatus} → ${status}`);
      analytics.track('order_status_change', {
        from: prevStatus,
        to: status,
      });
    }
  }, [status, prevStatus]);

  return <span className={`badge badge--${status}`}>{status}</span>;
}
```

**Why not just use a state variable?** Using `useState` to track the previous value would cause an extra re-render every time the value changes (the first render sets the new value, then a second render updates the "previous" state). `useRef` avoids this because updating a ref does not trigger a re-render.

---

### Q8. How do you build a `useMediaQuery` hook for responsive design in React?

**Answer:**

`useMediaQuery` subscribes to a CSS media query and returns a boolean indicating whether the query currently matches. This allows components to adapt their rendering based on screen size, orientation, colour scheme preference, or any valid media query — all without CSS-in-JS or class-based responsive utilities.

In React 18, the recommended approach is to use `useSyncExternalStore` to subscribe to the `matchMedia` API. This ensures that the subscription is compatible with React 18's concurrent features and avoids tearing (where different parts of the UI see different values during the same render).

```jsx
import { useSyncExternalStore, useCallback } from 'react';

function useMediaQuery(query) {
  const subscribe = useCallback(
    (callback) => {
      const mediaQueryList = window.matchMedia(query);
      mediaQueryList.addEventListener('change', callback);
      return () => mediaQueryList.removeEventListener('change', callback);
    },
    [query]
  );

  const getSnapshot = () => window.matchMedia(query).matches;

  // SSR fallback — return false on the server
  const getServerSnapshot = () => false;

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

// --- Usage: Responsive layout ---
function Dashboard() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');

  return (
    <div className={prefersDark ? 'dark-theme' : 'light-theme'}>
      {isMobile ? (
        <MobileNavigation />
      ) : (
        <SidebarNavigation collapsed={isTablet} />
      )}

      <main>
        <DataGrid
          columns={isMobile ? 2 : isTablet ? 3 : 5}
          animateRows={!prefersReducedMotion}
        />
      </main>
    </div>
  );
}

// --- Usage: Conditionally loading heavy components ---
function VideoPlayer({ src }) {
  const isMobile = useMediaQuery('(max-width: 480px)');

  // On mobile, render a lightweight thumbnail instead of the full player
  if (isMobile) {
    return (
      <a href={src} className="video-thumbnail">
        <img src={`${src}/thumbnail.jpg`} alt="Play video" />
      </a>
    );
  }

  return <video src={src} controls preload="metadata" />;
}
```

Using `useSyncExternalStore` is the React 18 best practice because it guarantees that the value read during render is consistent with the value used to schedule updates, even under concurrent rendering. The older `useState` + `useEffect` approach can produce a brief flicker where the component renders with a stale value before the effect fires.

---

### Q9. How do you build a `useClickOutside` hook for detecting clicks outside an element?

**Answer:**

`useClickOutside` triggers a callback when the user clicks anywhere outside a specified element. This is essential for closing dropdown menus, modals, popovers, date pickers, and autocomplete suggestions when the user clicks away. Production implementations must handle edge cases: clicks on portalled elements, touch events on mobile, and events that bubble through React portals.

```jsx
import { useEffect, useRef } from 'react';

function useClickOutside(handler) {
  const ref = useRef(null);

  useEffect(() => {
    const listener = (event) => {
      const el = ref.current;

      // Do nothing if clicking ref's element or its descendants
      if (!el || el.contains(event.target)) {
        return;
      }

      handler(event);
    };

    // Use mousedown instead of click to fire before blur events
    // (important for inputs that need to retain focus)
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [handler]);

  return ref;
}

// --- Usage: Dropdown menu ---
function Dropdown({ trigger, items, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);

  const dropdownRef = useClickOutside(() => setIsOpen(false));

  return (
    <div ref={dropdownRef} className="dropdown">
      <button onClick={() => setIsOpen(prev => !prev)}>
        {trigger}
      </button>

      {isOpen && (
        <ul className="dropdown-menu">
          {items.map(item => (
            <li key={item.id}>
              <button
                onClick={() => {
                  onSelect(item);
                  setIsOpen(false);
                }}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// --- Usage: Modal with portal support ---
function Modal({ isOpen, onClose, children }) {
  const modalRef = useClickOutside(onClose);

  if (!isOpen) return null;

  return createPortal(
    <div className="modal-overlay">
      <div ref={modalRef} className="modal-content" role="dialog">
        {children}
      </div>
    </div>,
    document.getElementById('modal-root')
  );
}
```

**Why `mousedown` instead of `click`?** The `click` event fires after `mouseup`, which means if the user starts a click inside the element and releases outside (or vice versa), the behaviour can be unpredictable. `mousedown` fires immediately when the button is pressed, giving a more responsive feel and avoiding race conditions with `blur` handlers on input fields inside the element.

**Production tip:** If the dropdown or popover is rendered inside a React Portal (e.g., via `createPortal`), the DOM hierarchy differs from the React hierarchy. The check `el.contains(event.target)` works on the *DOM* tree, so if the portal is rendered at the root of `document.body`, clicks inside the portal will appear to be "outside" the dropdown's DOM parent. To handle this, you can pass multiple refs or add a `data-` attribute to portalled elements and check for it in the listener.

---

### Q10. How do you build a `useIntersectionObserver` hook for lazy loading and infinite scroll?

**Answer:**

`useIntersectionObserver` wraps the browser's `IntersectionObserver` API to detect when an element enters or exits the viewport (or any scrollable ancestor). Production use cases include: lazy-loading images, triggering infinite scroll pagination, animating elements on scroll, and tracking ad viewability.

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

function useIntersectionObserver(options = {}) {
  const {
    threshold = 0,
    root = null,
    rootMargin = '0px',
    freezeOnceVisible = false,
  } = options;

  const [entry, setEntry] = useState(null);
  const [node, setNode] = useState(null);
  const observerRef = useRef(null);

  // Callback ref pattern — works with conditionally rendered elements
  const ref = useCallback((element) => {
    setNode(element);
  }, []);

  useEffect(() => {
    if (!node) return;

    // If already visible and frozen, skip re-observing
    if (freezeOnceVisible && entry?.isIntersecting) return;

    observerRef.current = new IntersectionObserver(
      ([observedEntry]) => setEntry(observedEntry),
      { threshold, root, rootMargin }
    );

    observerRef.current.observe(node);

    return () => observerRef.current?.disconnect();
  }, [node, threshold, root, rootMargin, freezeOnceVisible, entry?.isIntersecting]);

  const isVisible = !!entry?.isIntersecting;

  return { ref, entry, isVisible };
}

// --- Usage: Lazy-loaded image ---
function LazyImage({ src, alt, ...props }) {
  const { ref, isVisible } = useIntersectionObserver({
    rootMargin: '200px',       // Start loading 200px before visible
    freezeOnceVisible: true,   // Don't unload once loaded
  });

  return (
    <div ref={ref} className="lazy-image-wrapper">
      {isVisible ? (
        <img src={src} alt={alt} loading="lazy" {...props} />
      ) : (
        <div className="image-placeholder" aria-hidden="true" />
      )}
    </div>
  );
}

// --- Usage: Infinite scroll ---
function InfiniteProductList() {
  const [products, setProducts] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const { ref: sentinelRef, isVisible } = useIntersectionObserver({
    threshold: 1.0,
  });

  useEffect(() => {
    if (isVisible && hasMore) {
      fetch(`/api/products?page=${page}&limit=20`)
        .then(res => res.json())
        .then(data => {
          setProducts(prev => [...prev, ...data.items]);
          setHasMore(data.hasNextPage);
          setPage(prev => prev + 1);
        });
    }
  }, [isVisible, hasMore, page]);

  return (
    <div className="product-grid">
      {products.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}

      {/* Invisible sentinel element at the bottom */}
      {hasMore && (
        <div ref={sentinelRef} className="scroll-sentinel">
          Loading more...
        </div>
      )}
    </div>
  );
}
```

**Why a callback ref instead of `useRef`?** A `useRef` gives you a mutable object that persists across renders but does not notify you when its value changes. If the observed element is conditionally rendered (e.g., inside an `{isOpen && ...}` block), assigning the ref via `useRef` would not trigger the effect to re-run. A callback ref (via `useState` + setter) causes a re-render when the DOM node appears, which triggers the `useEffect` to set up the observer.

**`freezeOnceVisible`** is a common optimisation: once an image or ad has entered the viewport, there is no need to keep observing it. This reduces the work the observer has to do, improving scroll performance on pages with hundreds of elements.

---

### Q11. How do you compose multiple custom hooks together to build complex functionality?

**Answer:**

Hook composition is the primary design pattern for managing complexity in React. Just as you compose functions in functional programming, you compose hooks by calling simpler hooks inside more complex ones. Each hook in the chain owns a specific piece of state or side effect, and the outer hook orchestrates them into a cohesive API.

The key principle is the **single-responsibility principle for hooks:** each hook should do one thing well, and complex behaviour should emerge from combining simple hooks — not from building monolithic hooks.

```jsx
import { useState, useEffect, useCallback } from 'react';

// --- Layer 1: Primitive hooks ---
function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function useFetch(url) {
  const [state, setState] = useState({ data: null, loading: !!url, error: null });
  useEffect(() => {
    if (!url) { setState({ data: null, loading: false, error: null }); return; }
    const controller = new AbortController();
    setState(s => ({ ...s, loading: true, error: null }));
    fetch(url, { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => setState({ data, loading: false, error: null }))
      .catch(err => {
        if (err.name !== 'AbortError') setState({ data: null, loading: false, error: err });
      });
    return () => controller.abort();
  }, [url]);
  return state;
}

function useLocalStorage(key, initial) {
  const [value, setValue] = useState(() => {
    try { const item = localStorage.getItem(key); return item ? JSON.parse(item) : initial; }
    catch { return initial; }
  });
  useEffect(() => { localStorage.setItem(key, JSON.stringify(value)); }, [key, value]);
  return [value, setValue];
}

// --- Layer 2: Composed hook — combines debounce + fetch + localStorage ---
function useSearch(endpoint) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 400);
  const [recentSearches, setRecentSearches] = useLocalStorage('recentSearches', []);

  const url = debouncedQuery
    ? `${endpoint}?q=${encodeURIComponent(debouncedQuery)}`
    : null;
  const { data: results, loading, error } = useFetch(url);

  const search = useCallback((term) => {
    setQuery(term);
  }, []);

  // Save successful searches to recent history
  useEffect(() => {
    if (debouncedQuery && results && results.length > 0) {
      setRecentSearches(prev => {
        const updated = [debouncedQuery, ...prev.filter(s => s !== debouncedQuery)];
        return updated.slice(0, 10); // Keep last 10
      });
    }
  }, [debouncedQuery, results, setRecentSearches]);

  return {
    query,
    search,
    results,
    loading,
    error,
    recentSearches,
  };
}

// --- Component: Thin rendering layer ---
function GlobalSearch() {
  const {
    query, search, results, loading, error, recentSearches
  } = useSearch('/api/search');

  return (
    <div className="search-container">
      <input
        type="search"
        value={query}
        onChange={e => search(e.target.value)}
        placeholder="Search..."
      />

      {!query && recentSearches.length > 0 && (
        <div className="recent-searches">
          <h4>Recent Searches</h4>
          {recentSearches.map(term => (
            <button key={term} onClick={() => search(term)}>{term}</button>
          ))}
        </div>
      )}

      {loading && <div className="spinner" />}
      {error && <div className="error">{error.message}</div>}
      {results?.map(item => (
        <div key={item.id} className="search-result">{item.title}</div>
      ))}
    </div>
  );
}
```

**The composition chain:** `useSearch` composes `useDebounce` + `useFetch` + `useLocalStorage`. The component `GlobalSearch` is a thin shell that only handles rendering. Each hook is independently testable: you can test `useDebounce` in isolation, test `useFetch` with a mock server, and test `useSearch` as an integration of all three.

**Rule of thumb:** If a hook's dependency array or parameter list grows beyond 4-5 items, it might be doing too much. Split it into smaller hooks and compose them.

---

### Q12. How do you write custom hooks with TypeScript generics for maximum reusability?

**Answer:**

TypeScript generics allow custom hooks to be type-safe while remaining flexible enough to work with any data shape. Without generics, you would either lose type safety (using `any`) or duplicate hooks for every data type. With generics, the hook infers or accepts the concrete type from the caller, and the return value is correctly typed throughout.

Key patterns include: generic state hooks, generic fetch hooks, and constrained generics that enforce a minimum shape.

```jsx
// --- useLocalStorage with generics ---
import { useState, useEffect } from 'react';

function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    window.localStorage.setItem(key, JSON.stringify(storedValue));
  }, [key, storedValue]);

  return [storedValue, setStoredValue];
}

// TypeScript infers T from the initial value
const [theme, setTheme] = useLocalStorage('theme', 'light');
// theme: string, setTheme: (value: string | ((prev: string) => string)) => void

const [user, setUser] = useLocalStorage<User | null>('user', null);
// Explicit generic when initial value is null and doesn't carry the type

// --- useFetch with generics ---
interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

function useFetch<T>(url: string | null): FetchState<T> & { refetch: () => void } {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: !!url,
    error: null,
  });

  const fetchData = useCallback(async () => {
    if (!url) return;
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: T = await res.json();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  }, [url]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return { ...state, refetch: fetchData };
}

// Usage — T is inferred as User[] from the generic parameter
interface User {
  id: number;
  name: string;
  email: string;
}

function UserList() {
  const { data: users, loading, error } = useFetch<User[]>('/api/users');
  //      ^--- users is User[] | null, fully typed

  return (
    <ul>
      {users?.map(user => (
        <li key={user.id}>{user.name} — {user.email}</li>
      ))}
    </ul>
  );
}

// --- Constrained generics: hook that requires an "id" field ---
interface Identifiable {
  id: string | number;
}

function useSelection<T extends Identifiable>(items: T[]) {
  const [selectedIds, setSelectedIds] = useState<Set<T['id']>>(new Set());

  const toggle = useCallback((id: T['id']) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(items.map(item => item.id)));
  }, [items]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const selectedItems = items.filter(item => selectedIds.has(item.id));

  return { selectedIds, selectedItems, toggle, selectAll, clearSelection };
}

// Usage
interface Product { id: number; name: string; price: number; }
const products: Product[] = [{ id: 1, name: 'Widget', price: 9.99 }];
const { selectedItems, toggle } = useSelection(products);
// selectedItems is Product[], toggle expects number — fully type-safe
```

**Constrained generics** (`T extends Identifiable`) are particularly powerful because they let the hook enforce a minimum contract on the data (e.g., "must have an `id`") while still being flexible about the rest of the shape. This is the pattern that production hook libraries use extensively.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you build a `useAsync` hook — a generic handler for any asynchronous operation?

**Answer:**

`useAsync` generalises the pattern in `useFetch` to handle *any* async function, not just `fetch` calls. It accepts an async callback and returns `{ execute, data, loading, error, status }`. This is the foundation for hooks like `useMutation`, `useUpload`, `useAsyncValidation`, etc.

Production requirements include:
- **Cancellation via AbortController:** Pass a signal into the async function so it can be aborted.
- **Race condition protection:** If `execute` is called again before the first invocation resolves, only the latest result is applied.
- **Idle/pending/success/error status:** Consumers can switch on a single status string instead of juggling three booleans.
- **Immediate vs. deferred execution:** Some callers want to execute on mount; others want to execute on user action (like a form submit).

```jsx
import { useState, useCallback, useRef } from 'react';

function useAsync(asyncFunction, { immediate = false } = {}) {
  const [status, setStatus] = useState(immediate ? 'pending' : 'idle');
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const callIdRef = useRef(0);
  const abortControllerRef = useRef(null);

  const execute = useCallback(
    async (...args) => {
      // Abort previous call
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const callId = ++callIdRef.current;

      setStatus('pending');
      setData(null);
      setError(null);

      try {
        const result = await asyncFunction(...args, {
          signal: controller.signal,
        });

        // Only apply result if this is still the latest call
        if (callId === callIdRef.current && !controller.signal.aborted) {
          setData(result);
          setStatus('success');
          return result;
        }
      } catch (err) {
        if (callId === callIdRef.current && err.name !== 'AbortError') {
          setError(err);
          setStatus('error');
          throw err;
        }
      }
    },
    [asyncFunction]
  );

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setStatus('idle');
    setData(null);
    setError(null);
  }, []);

  // Execute immediately on mount if requested
  useEffect(() => {
    if (immediate) execute();
    return () => abortControllerRef.current?.abort();
  }, [immediate, execute]);

  return { execute, data, error, status, loading: status === 'pending', reset };
}

// --- Usage: File upload with progress ---
async function uploadFile(file, { signal }) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!response.ok) throw new Error('Upload failed');
  return response.json();
}

function FileUploader() {
  const { execute, data, loading, error, status, reset } = useAsync(uploadFile);

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        await execute(file);
      } catch {
        // error is already in state
      }
    }
  };

  return (
    <div className="uploader">
      <input type="file" onChange={handleFileChange} disabled={loading} />

      {loading && <progress className="upload-progress" />}

      {status === 'success' && (
        <div className="success">
          Uploaded: <a href={data.url}>{data.filename}</a>
          <button onClick={reset}>Upload another</button>
        </div>
      )}

      {status === 'error' && (
        <div className="error">
          {error.message}
          <button onClick={() => execute(/* retry with same file */)}>Retry</button>
        </div>
      )}
    </div>
  );
}
```

**Why `callIdRef`?** Consider: the user clicks "Upload", then immediately picks a different file and clicks "Upload" again. The first upload is still in flight. Without `callIdRef`, the first upload's response could arrive after the second one starts, overwriting the correct state. By incrementing a counter and checking it before applying state, we guarantee only the latest invocation's result is used.

---

### Q14. How do you build a `useMutation` hook for managing server mutations with optimistic updates?

**Answer:**

`useMutation` encapsulates the pattern of sending data to a server (POST, PUT, DELETE), managing the loading/error state, and optionally applying optimistic updates that are rolled back on failure. This is the write counterpart to `useFetch` (which is for reads). Production mutation hooks also handle retry logic, cache invalidation, and success/error callbacks.

```jsx
import { useState, useCallback, useRef } from 'react';

function useMutation(mutationFn, options = {}) {
  const {
    onSuccess,
    onError,
    onSettled,
    optimisticUpdate, // (variables) => previousData
    rollback,         // (previousData) => void
    retry = 0,
    retryDelay = 1000,
  } = options;

  const [state, setState] = useState({
    data: null,
    error: null,
    loading: false,
    isSuccess: false,
    isError: false,
  });

  const attemptRef = useRef(0);

  const mutate = useCallback(
    async (variables) => {
      let previousData;

      // Apply optimistic update immediately
      if (optimisticUpdate) {
        previousData = optimisticUpdate(variables);
      }

      setState({ data: null, error: null, loading: true, isSuccess: false, isError: false });

      const attempt = async (retryCount) => {
        try {
          const result = await mutationFn(variables);

          setState({
            data: result,
            error: null,
            loading: false,
            isSuccess: true,
            isError: false,
          });

          onSuccess?.(result, variables);
          onSettled?.(result, null, variables);
          return result;
        } catch (err) {
          if (retryCount < retry) {
            await new Promise(resolve =>
              setTimeout(resolve, retryDelay * Math.pow(2, retryCount))
            );
            return attempt(retryCount + 1);
          }

          // All retries exhausted — rollback optimistic update
          if (rollback && previousData !== undefined) {
            rollback(previousData);
          }

          setState({
            data: null,
            error: err,
            loading: false,
            isSuccess: false,
            isError: true,
          });

          onError?.(err, variables);
          onSettled?.(null, err, variables);
          throw err;
        }
      };

      return attempt(0);
    },
    [mutationFn, onSuccess, onError, onSettled, optimisticUpdate, rollback, retry, retryDelay]
  );

  const reset = useCallback(() => {
    setState({ data: null, error: null, loading: false, isSuccess: false, isError: false });
  }, []);

  return { ...state, mutate, reset };
}

// --- Usage: Todo list with optimistic updates ---
function TodoList() {
  const [todos, setTodos] = useState([]);

  const addTodo = useMutation(
    async (newTodo) => {
      const res = await fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTodo),
      });
      if (!res.ok) throw new Error('Failed to add todo');
      return res.json();
    },
    {
      // Optimistic: add the todo immediately with a temp ID
      optimisticUpdate: (variables) => {
        const snapshot = [...todos];
        setTodos(prev => [...prev, { ...variables, id: `temp-${Date.now()}`, pending: true }]);
        return snapshot; // Return snapshot for rollback
      },
      // Rollback: restore snapshot if mutation fails
      rollback: (snapshot) => setTodos(snapshot),
      // On success: replace temp item with server response
      onSuccess: (serverTodo) => {
        setTodos(prev =>
          prev.map(t => t.pending ? serverTodo : t)
        );
      },
      retry: 2,
    }
  );

  const deleteTodo = useMutation(
    async (todoId) => {
      const res = await fetch(`/api/todos/${todoId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete');
    },
    {
      optimisticUpdate: (todoId) => {
        const snapshot = [...todos];
        setTodos(prev => prev.filter(t => t.id !== todoId));
        return snapshot;
      },
      rollback: (snapshot) => setTodos(snapshot),
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    const title = e.target.title.value;
    addTodo.mutate({ title, completed: false });
    e.target.reset();
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input name="title" placeholder="New todo..." required />
        <button type="submit" disabled={addTodo.loading}>
          {addTodo.loading ? 'Adding...' : 'Add'}
        </button>
      </form>

      {addTodo.isError && <p className="error">Failed to add: {addTodo.error.message}</p>}

      <ul>
        {todos.map(todo => (
          <li key={todo.id} className={todo.pending ? 'pending' : ''}>
            {todo.title}
            <button
              onClick={() => deleteTodo.mutate(todo.id)}
              disabled={deleteTodo.loading}
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

The optimistic update makes the UI feel instant: the todo appears immediately, and only rolls back if the server rejects it. The retry with exponential backoff handles transient network failures. This pattern mirrors what TanStack Query's `useMutation` does internally, and understanding it from scratch is frequently tested in senior-level interviews.

---

### Q15. How do you build a `useWebSocket` hook for real-time data?

**Answer:**

`useWebSocket` manages a WebSocket connection lifecycle: connecting, reconnecting on failure, sending messages, and providing the latest received data to the component. Real-time features like chat, live dashboards, collaborative editing, and notifications all rely on this pattern.

Production requirements include:
- **Automatic reconnection** with exponential backoff.
- **Heartbeat/ping** to detect dead connections.
- **Message queuing** — if a message is sent while the socket is reconnecting, it should be queued and sent once the connection is re-established.
- **Cleanup** — the connection must be closed when the component unmounts.
- **JSON serialisation** — automatically parse incoming messages and stringify outgoing ones.

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

function useWebSocket(url, options = {}) {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectAttempts = 10,
    reconnectInterval = 1000,
    heartbeatInterval = 30000,
  } = options;

  const [readyState, setReadyState] = useState(WebSocket.CONNECTING);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef(null);
  const heartbeatTimerRef = useRef(null);
  const messageQueueRef = useRef([]);
  const unmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = (event) => {
      setReadyState(WebSocket.OPEN);
      reconnectCountRef.current = 0;
      onOpen?.(event);

      // Flush queued messages
      while (messageQueueRef.current.length > 0) {
        const msg = messageQueueRef.current.shift();
        ws.send(msg);
      }

      // Start heartbeat
      heartbeatTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, heartbeatInterval);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'pong') return; // Ignore heartbeat responses
        setLastMessage(data);
        onMessage?.(data, event);
      } catch {
        setLastMessage(event.data);
        onMessage?.(event.data, event);
      }
    };

    ws.onclose = (event) => {
      setReadyState(WebSocket.CLOSED);
      clearInterval(heartbeatTimerRef.current);
      onClose?.(event);

      // Reconnect with exponential backoff
      if (reconnect && !unmountedRef.current && reconnectCountRef.current < reconnectAttempts) {
        const delay = reconnectInterval * Math.pow(2, reconnectCountRef.current);
        reconnectCountRef.current += 1;
        reconnectTimerRef.current = setTimeout(connect, delay);
      }
    };

    ws.onerror = (event) => {
      onError?.(event);
    };
  }, [url, reconnect, reconnectAttempts, reconnectInterval, heartbeatInterval, onOpen, onClose, onError, onMessage]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      clearTimeout(reconnectTimerRef.current);
      clearInterval(heartbeatTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((data) => {
    const message = typeof data === 'string' ? data : JSON.stringify(data);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    } else {
      // Queue message for when connection is re-established
      messageQueueRef.current.push(message);
    }
  }, []);

  return {
    sendMessage,
    lastMessage,
    readyState,
    isConnected: readyState === WebSocket.OPEN,
  };
}

// --- Usage: Live chat ---
function ChatRoom({ roomId, userId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const { sendMessage, lastMessage, isConnected } = useWebSocket(
    `wss://chat.example.com/rooms/${roomId}`,
    {
      onMessage: (data) => {
        if (data.type === 'message') {
          setMessages(prev => [...prev, data]);
        }
      },
      onOpen: () => {
        sendMessage({ type: 'join', userId, roomId });
      },
    }
  );

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    sendMessage({
      type: 'message',
      text: input,
      userId,
      timestamp: Date.now(),
    });
    setInput('');
  };

  return (
    <div className="chat-room">
      <div className="status-bar">
        <span className={`dot ${isConnected ? 'green' : 'red'}`} />
        {isConnected ? 'Connected' : 'Reconnecting...'}
      </div>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.userId === userId ? 'own' : 'other'}>
            <strong>{msg.userId}</strong>: {msg.text}
          </div>
        ))}
      </div>

      <form onSubmit={handleSend}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={!isConnected}
        />
        <button type="submit" disabled={!isConnected}>Send</button>
      </form>
    </div>
  );
}
```

**Exponential backoff** prevents thundering-herd problems where thousands of clients simultaneously try to reconnect after a server restart. **Message queuing** ensures that if the user sends a chat message during a brief disconnection, it is delivered once the connection recovers instead of being silently dropped. **Heartbeat pings** detect zombie connections where the TCP connection appears open but the server has actually gone away (common behind load balancers with idle timeouts).

---

### Q16. How do you design custom hooks for dependency injection and testability?

**Answer:**

Dependency injection (DI) in hooks means passing the hook's external dependencies (API clients, storage adapters, timers, date functions) as parameters rather than hardcoding them. This makes hooks trivially testable because tests can inject mocks instead of stubbing globals.

The three main DI patterns for hooks are:

1. **Parameter injection:** Pass dependencies directly as hook arguments.
2. **Context injection:** Provide dependencies via React Context, and the hook reads them with `useContext`.
3. **Factory pattern:** A function that creates a hook with the given dependencies baked in.

```jsx
import { useState, useEffect, useContext, createContext, useCallback } from 'react';

// --- Pattern 1: Parameter injection ---
function useFetch(url, { fetcher = window.fetch, signal } = {}) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    let cancelled = false;
    setState(s => ({ ...s, loading: true }));

    fetcher(url, { signal })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => { if (!cancelled) setState({ data, loading: false, error: null }); })
      .catch(error => { if (!cancelled) setState({ data: null, loading: false, error }); });

    return () => { cancelled = true; };
  }, [url, fetcher, signal]);

  return state;
}

// Test — inject a mock fetcher, no need to stub window.fetch
// test('useFetch returns data', async () => {
//   const mockFetcher = jest.fn().mockResolvedValue({
//     ok: true,
//     json: () => Promise.resolve({ name: 'Alice' }),
//   });
//   const { result, waitForNextUpdate } = renderHook(() =>
//     useFetch('/api/user', { fetcher: mockFetcher })
//   );
//   await waitForNextUpdate();
//   expect(result.current.data).toEqual({ name: 'Alice' });
// });

// --- Pattern 2: Context injection ---
const ApiClientContext = createContext(null);

function ApiClientProvider({ client, children }) {
  return (
    <ApiClientContext.Provider value={client}>
      {children}
    </ApiClientContext.Provider>
  );
}

function useApiClient() {
  const client = useContext(ApiClientContext);
  if (!client) throw new Error('useApiClient must be used within ApiClientProvider');
  return client;
}

function useUsers() {
  const apiClient = useApiClient(); // Injected via context
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get('/users')
      .then(data => setUsers(data))
      .finally(() => setLoading(false));
  }, [apiClient]);

  return { users, loading };
}

// In the app:
// <ApiClientProvider client={realApiClient}><App /></ApiClientProvider>

// In tests:
// <ApiClientProvider client={mockApiClient}><ComponentUnderTest /></ApiClientProvider>

// --- Pattern 3: Factory pattern ---
function createStorageHook(storage) {
  return function useStorage(key, initialValue) {
    const [value, setValue] = useState(() => {
      try {
        const item = storage.getItem(key);
        return item ? JSON.parse(item) : initialValue;
      } catch {
        return initialValue;
      }
    });

    useEffect(() => {
      storage.setItem(key, JSON.stringify(value));
    }, [key, value]);

    return [value, setValue];
  };
}

// Production: backed by localStorage
const useLocalStorage = createStorageHook(window.localStorage);
const useSessionStorage = createStorageHook(window.sessionStorage);

// Test: backed by an in-memory map
const createMockStorage = () => {
  const store = new Map();
  return {
    getItem: (key) => store.get(key) ?? null,
    setItem: (key, val) => store.set(key, val),
    removeItem: (key) => store.delete(key),
  };
};
const useTestStorage = createStorageHook(createMockStorage());
```

**Why does testability matter for hooks?** In production codebases, hooks contain the most complex logic in the application — retry logic, token refresh, cache invalidation, optimistic updates. If this logic is coupled to global singletons (`window.fetch`, `localStorage`, `WebSocket`), testing requires brittle global mocks that leak between tests. DI makes each test hermetic: the mock is scoped to the test, and no global state is mutated.

---

### Q17. How do you build a `useEventSource` hook for Server-Sent Events?

**Answer:**

Server-Sent Events (SSE) provide a server-to-client unidirectional stream over HTTP. Unlike WebSockets, SSE uses a simple HTTP connection, supports automatic reconnection natively (the browser re-establishes the connection using the `Last-Event-ID` header), and works through HTTP/2 without special handling. Common use cases include live notifications, stock tickers, CI/CD build logs, and real-time dashboards.

`useEventSource` manages the `EventSource` lifecycle, supports typed event listeners, handles errors, and provides a clean teardown on unmount.

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

function useEventSource(url, options = {}) {
  const {
    withCredentials = false,
    events = {},          // { eventName: handler }
    retry = true,
    retryInterval = 5000,
  } = options;

  const [lastEvent, setLastEvent] = useState(null);
  const [readyState, setReadyState] = useState(EventSource.CONNECTING);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);
  const retryTimerRef = useRef(null);
  const unmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (unmountedRef.current || !url) return;

    const es = new EventSource(url, { withCredentials });
    eventSourceRef.current = es;

    es.onopen = () => {
      setReadyState(EventSource.OPEN);
      setError(null);
    };

    // Default message handler (unnamed events)
    es.onmessage = (event) => {
      const data = (() => {
        try { return JSON.parse(event.data); }
        catch { return event.data; }
      })();
      setLastEvent({ type: 'message', data, lastEventId: event.lastEventId });
    };

    // Named event handlers
    Object.entries(events).forEach(([eventName, handler]) => {
      es.addEventListener(eventName, (event) => {
        const data = (() => {
          try { return JSON.parse(event.data); }
          catch { return event.data; }
        })();
        setLastEvent({ type: eventName, data, lastEventId: event.lastEventId });
        handler(data, event);
      });
    });

    es.onerror = () => {
      setReadyState(EventSource.CLOSED);
      setError(new Error('EventSource connection failed'));
      es.close();

      // Manual retry with backoff (browser auto-retry may not work after certain errors)
      if (retry && !unmountedRef.current) {
        retryTimerRef.current = setTimeout(connect, retryInterval);
      }
    };
  }, [url, withCredentials, events, retry, retryInterval]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      clearTimeout(retryTimerRef.current);
      eventSourceRef.current?.close();
    };
  }, [connect]);

  const close = useCallback(() => {
    clearTimeout(retryTimerRef.current);
    eventSourceRef.current?.close();
    setReadyState(EventSource.CLOSED);
  }, []);

  return {
    lastEvent,
    readyState,
    error,
    isConnected: readyState === EventSource.OPEN,
    close,
  };
}

// --- Usage: Build log streaming ---
function BuildLogViewer({ buildId }) {
  const [logs, setLogs] = useState([]);

  const { isConnected, error, close } = useEventSource(
    `/api/builds/${buildId}/logs`,
    {
      events: {
        log: (data) => {
          setLogs(prev => [...prev, data]);
        },
        complete: (data) => {
          setLogs(prev => [...prev, { ...data, final: true }]);
          close(); // No more events expected
        },
        error: (data) => {
          setLogs(prev => [...prev, { ...data, level: 'error' }]);
        },
      },
    }
  );

  return (
    <div className="build-log">
      <div className="log-header">
        <span className={`status-dot ${isConnected ? 'live' : 'offline'}`} />
        Build #{buildId} — {isConnected ? 'Live' : 'Disconnected'}
      </div>

      <pre className="log-output">
        {logs.map((log, i) => (
          <div key={i} className={`log-line log-${log.level || 'info'}`}>
            <span className="timestamp">{log.timestamp}</span>
            <span className="message">{log.message}</span>
          </div>
        ))}
      </pre>

      {error && <div className="error-banner">Connection lost. Retrying...</div>}
    </div>
  );
}
```

**SSE vs. WebSocket:** Use SSE when data flows in only one direction (server → client), the protocol needs to traverse corporate proxies (SSE is regular HTTP), or you want automatic reconnection with `Last-Event-ID` for resuming where you left off. Use WebSocket when you need bidirectional communication (e.g., chat). The `useEventSource` hook abstracts all of this behind a simple declarative API.

---

### Q18. How do you build custom hooks for form validation?

**Answer:**

Form validation is one of the most common production use cases for custom hooks. A well-designed `useForm` hook manages field values, tracks which fields have been touched (for showing errors only after interaction), validates on change or blur, and prevents submission until all fields are valid. Production forms also need async validation (e.g., checking if a username is taken), field-level and form-level validation, and integration with the HTML Constraint Validation API.

```jsx
import { useState, useCallback, useRef } from 'react';

function useForm({ initialValues, validate, onSubmit }) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitCount, setSubmitCount] = useState(0);
  const mountedRef = useRef(true);

  // Run validation and return errors object
  const runValidation = useCallback(
    (currentValues) => {
      const validationErrors = validate ? validate(currentValues) : {};
      return validationErrors;
    },
    [validate]
  );

  // Handle field change
  const handleChange = useCallback(
    (event) => {
      const { name, value, type, checked } = event.target;
      const fieldValue = type === 'checkbox' ? checked : value;

      setValues(prev => {
        const next = { ...prev, [name]: fieldValue };
        // Validate on change if the field has been touched
        setErrors(runValidation(next));
        return next;
      });
    },
    [runValidation]
  );

  // Handle field blur — mark as touched
  const handleBlur = useCallback(
    (event) => {
      const { name } = event.target;
      setTouched(prev => ({ ...prev, [name]: true }));
      setErrors(runValidation(values));
    },
    [runValidation, values]
  );

  // Set a single field value programmatically
  const setFieldValue = useCallback(
    (name, value) => {
      setValues(prev => {
        const next = { ...prev, [name]: value };
        setErrors(runValidation(next));
        return next;
      });
    },
    [runValidation]
  );

  // Handle form submission
  const handleSubmit = useCallback(
    async (event) => {
      event?.preventDefault();
      setSubmitCount(c => c + 1);

      // Mark all fields as touched
      const allTouched = Object.keys(values).reduce(
        (acc, key) => ({ ...acc, [key]: true }),
        {}
      );
      setTouched(allTouched);

      const validationErrors = runValidation(values);
      setErrors(validationErrors);

      if (Object.keys(validationErrors).length > 0) {
        return; // Don't submit if there are errors
      }

      setIsSubmitting(true);
      try {
        await onSubmit(values);
      } catch (err) {
        // Let the consumer handle submission errors
        if (mountedRef.current) {
          setErrors(prev => ({ ...prev, _form: err.message }));
        }
      } finally {
        if (mountedRef.current) {
          setIsSubmitting(false);
        }
      }
    },
    [values, runValidation, onSubmit]
  );

  // Reset the form
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  // Helper to get props for an input field
  const getFieldProps = useCallback(
    (name) => ({
      name,
      value: values[name] ?? '',
      onChange: handleChange,
      onBlur: handleBlur,
    }),
    [values, handleChange, handleBlur]
  );

  // Helper to get error display info for a field
  const getFieldError = useCallback(
    (name) => (touched[name] || submitCount > 0) ? errors[name] : undefined,
    [touched, errors, submitCount]
  );

  const isValid = Object.keys(runValidation(values)).length === 0;

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    getFieldProps,
    getFieldError,
    reset,
  };
}

// --- Usage: Registration form with validation ---
const validate = (values) => {
  const errors = {};

  if (!values.username) {
    errors.username = 'Username is required';
  } else if (values.username.length < 3) {
    errors.username = 'Username must be at least 3 characters';
  }

  if (!values.email) {
    errors.email = 'Email is required';
  } else if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(values.email)) {
    errors.email = 'Invalid email address';
  }

  if (!values.password) {
    errors.password = 'Password is required';
  } else if (values.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }

  if (values.password !== values.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match';
  }

  return errors;
};

function RegistrationForm() {
  const form = useForm({
    initialValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
    validate,
    onSubmit: async (values) => {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || 'Registration failed');
      }
    },
  });

  return (
    <form onSubmit={form.handleSubmit} noValidate>
      <div className="field">
        <label htmlFor="username">Username</label>
        <input id="username" {...form.getFieldProps('username')} />
        {form.getFieldError('username') && (
          <span className="error">{form.getFieldError('username')}</span>
        )}
      </div>

      <div className="field">
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...form.getFieldProps('email')} />
        {form.getFieldError('email') && (
          <span className="error">{form.getFieldError('email')}</span>
        )}
      </div>

      <div className="field">
        <label htmlFor="password">Password</label>
        <input id="password" type="password" {...form.getFieldProps('password')} />
        {form.getFieldError('password') && (
          <span className="error">{form.getFieldError('password')}</span>
        )}
      </div>

      <div className="field">
        <label htmlFor="confirmPassword">Confirm Password</label>
        <input id="confirmPassword" type="password" {...form.getFieldProps('confirmPassword')} />
        {form.getFieldError('confirmPassword') && (
          <span className="error">{form.getFieldError('confirmPassword')}</span>
        )}
      </div>

      {form.errors._form && <div className="form-error">{form.errors._form}</div>}

      <button type="submit" disabled={form.isSubmitting}>
        {form.isSubmitting ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
}
```

The `getFieldProps` helper is inspired by Formik's API design — it returns `{ name, value, onChange, onBlur }` so you can spread it directly onto an input. The `getFieldError` helper only shows errors for fields that have been touched or after the first submission attempt, which is the standard UX pattern: don't show a "required" error on a pristine field the user hasn't interacted with yet.

---

### Q19. What are the best practices for building a custom hook library with proper API design?

**Answer:**

Building a hook library (internal or open-source) requires careful API design because hooks are consumed in every component — a bad API multiplies its ergonomic cost across the entire codebase. The key principles are:

1. **Consistent return types:** Adopt a convention and stick to it. If `useFetch` returns `{ data, loading, error }`, then `useMutation` should return the same shape plus additional fields — not a completely different structure.

2. **Options object for configuration:** Use an options object (not positional args) for anything beyond the first 1-2 parameters. This is future-proof (you can add options without breaking existing callers) and self-documenting at the call site.

3. **Stable references:** Memoize returned callbacks with `useCallback` and objects with `useMemo`. Consumers will pass these into dependency arrays, and unstable references cause infinite re-render loops.

4. **Sensible defaults:** Every option should have a default value that works for the 80% case. Power users can override; casual users get good behaviour for free.

5. **Composability over configuration:** Rather than adding every feature behind a flag, design small hooks that compose. Let users build `useSearchWithCache` from `useDebounce` + `useFetch` + `useLocalStorage`.

6. **SSR safety:** Check for `window`/`document` before using browser APIs, or use `useSyncExternalStore` with a `getServerSnapshot`.

7. **TypeScript-first:** Export types and use generics. This is table stakes for a library consumed by other developers.

```jsx
// --- Example: well-designed hook library API ---

// ✅ Consistent options pattern with defaults
function useClipboard({ timeout = 2000 } = {}) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);
  const timeoutRef = useRef(null);

  const copy = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setError(null);
      clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setCopied(false), timeout);
    } catch (err) {
      setError(err);
      setCopied(false);
    }
  }, [timeout]);

  // Cleanup on unmount
  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  return { copy, copied, error }; // Consistent shape
}

// ✅ Stable references, options object, TypeScript-ready
function useCounter(initialValue = 0, { min = -Infinity, max = Infinity, step = 1 } = {}) {
  const [count, setCount] = useState(initialValue);

  const increment = useCallback(() => {
    setCount(c => Math.min(c + step, max));
  }, [step, max]);

  const decrement = useCallback(() => {
    setCount(c => Math.max(c - step, min));
  }, [step, min]);

  const reset = useCallback(() => setCount(initialValue), [initialValue]);

  const set = useCallback(
    (value) => {
      setCount(Math.min(Math.max(value, min), max));
    },
    [min, max]
  );

  return { count, increment, decrement, reset, set }; // All callbacks are stable
}

// ✅ SSR-safe hook with useSyncExternalStore
function useOnlineStatus() {
  const subscribe = useCallback((callback) => {
    window.addEventListener('online', callback);
    window.addEventListener('offline', callback);
    return () => {
      window.removeEventListener('online', callback);
      window.removeEventListener('offline', callback);
    };
  }, []);

  const getSnapshot = () => navigator.onLine;
  const getServerSnapshot = () => true; // Assume online during SSR

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

// ✅ Library index file with named exports
// hooks/index.js
export { useToggle } from './useToggle';
export { useLocalStorage } from './useLocalStorage';
export { useFetch } from './useFetch';
export { useDebounce } from './useDebounce';
export { useMediaQuery } from './useMediaQuery';
export { useClickOutside } from './useClickOutside';
export { useClipboard } from './useClipboard';
export { useCounter } from './useCounter';
export { useOnlineStatus } from './useOnlineStatus';

// Each hook should also export its types:
// export type { UseFetchOptions, UseFetchResult } from './useFetch';
```

**Anti-patterns to avoid:**
- **Returning arrays for more than 2 values:** `const [data, loading, error, refetch, abort] = useFetch(url)` — consumers must remember the order and can't skip values. Use an object instead.
- **Mutating refs in render:** Side effects that write to refs should live in `useEffect` or event handlers, not during render.
- **Hardcoding global dependencies:** Accessing `window.fetch` or `localStorage` directly inside the hook without allowing injection makes testing painful.
- **Missing cleanup:** Every `addEventListener`, `setInterval`, `setTimeout`, or subscription created in a hook must have a corresponding cleanup in the effect's return function.

---

### Q20. How do you build a production `useAuth` hook with token refresh, retry logic, and session management?

**Answer:**

`useAuth` is one of the most critical hooks in any production application. It manages the entire authentication lifecycle: login, logout, token storage, automatic token refresh before expiry, retrying failed requests with fresh tokens, session expiration detection, and providing the current user to the entire component tree via context.

A production implementation involves multiple composed hooks and a context provider. Below is a comprehensive implementation:

```jsx
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from 'react';

// --- Token utilities ---
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

function isTokenExpired(token, bufferSeconds = 60) {
  const payload = parseJwt(token);
  if (!payload?.exp) return true;
  return Date.now() >= (payload.exp - bufferSeconds) * 1000;
}

// --- Token storage (abstracted for testability) ---
const tokenStorage = {
  get: () => {
    try {
      const raw = localStorage.getItem('auth_tokens');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
  set: (tokens) => {
    localStorage.setItem('auth_tokens', JSON.stringify(tokens));
  },
  clear: () => {
    localStorage.removeItem('auth_tokens');
  },
};

// --- Auth Context ---
const AuthContext = createContext(null);

function AuthProvider({ children, apiBaseUrl = '/api' }) {
  const [user, setUser] = useState(null);
  const [tokens, setTokens] = useState(() => tokenStorage.get());
  const [status, setStatus] = useState('loading'); // loading | authenticated | unauthenticated
  const refreshPromiseRef = useRef(null);
  const refreshTimerRef = useRef(null);

  // --- Core: refresh the access token ---
  const refreshAccessToken = useCallback(async () => {
    // If a refresh is already in progress, return the existing promise
    // This prevents multiple simultaneous refresh requests
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const currentTokens = tokenStorage.get();
    if (!currentTokens?.refreshToken) {
      throw new Error('No refresh token available');
    }

    refreshPromiseRef.current = (async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refreshToken: currentTokens.refreshToken }),
        });

        if (!response.ok) {
          throw new Error('Token refresh failed');
        }

        const newTokens = await response.json();
        tokenStorage.set(newTokens);
        setTokens(newTokens);
        return newTokens;
      } catch (error) {
        // Refresh failed — clear everything and force re-login
        tokenStorage.clear();
        setTokens(null);
        setUser(null);
        setStatus('unauthenticated');
        throw error;
      } finally {
        refreshPromiseRef.current = null;
      }
    })();

    return refreshPromiseRef.current;
  }, [apiBaseUrl]);

  // --- Authenticated fetch with automatic token refresh and retry ---
  const authenticatedFetch = useCallback(
    async (url, options = {}, _retryCount = 0) => {
      let currentTokens = tokenStorage.get();

      // Proactively refresh if token is about to expire
      if (currentTokens?.accessToken && isTokenExpired(currentTokens.accessToken)) {
        try {
          currentTokens = await refreshAccessToken();
        } catch {
          throw new Error('Session expired. Please log in again.');
        }
      }

      if (!currentTokens?.accessToken) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${currentTokens.accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      // If 401, try refreshing once and retrying
      if (response.status === 401 && _retryCount < 1) {
        try {
          await refreshAccessToken();
          return authenticatedFetch(url, options, _retryCount + 1);
        } catch {
          throw new Error('Session expired. Please log in again.');
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.message || `HTTP ${response.status}`);
        error.status = response.status;
        error.data = errorData;
        throw error;
      }

      return response.json();
    },
    [refreshAccessToken]
  );

  // --- Login ---
  const login = useCallback(
    async (credentials) => {
      setStatus('loading');
      try {
        const response = await fetch(`${apiBaseUrl}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(credentials),
        });

        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.message || 'Login failed');
        }

        const { user: userData, tokens: newTokens } = await response.json();
        tokenStorage.set(newTokens);
        setTokens(newTokens);
        setUser(userData);
        setStatus('authenticated');
        return userData;
      } catch (error) {
        setStatus('unauthenticated');
        throw error;
      }
    },
    [apiBaseUrl]
  );

  // --- Logout ---
  const logout = useCallback(async () => {
    const currentTokens = tokenStorage.get();
    // Best-effort server-side logout (don't block on failure)
    if (currentTokens?.refreshToken) {
      fetch(`${apiBaseUrl}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: currentTokens.refreshToken }),
      }).catch(() => {}); // Fire and forget
    }

    clearTimeout(refreshTimerRef.current);
    tokenStorage.clear();
    setTokens(null);
    setUser(null);
    setStatus('unauthenticated');
  }, [apiBaseUrl]);

  // --- Initialize: check stored tokens on mount ---
  useEffect(() => {
    const initAuth = async () => {
      const storedTokens = tokenStorage.get();
      if (!storedTokens?.accessToken) {
        setStatus('unauthenticated');
        return;
      }

      try {
        // If access token is expired, try to refresh
        let validTokens = storedTokens;
        if (isTokenExpired(storedTokens.accessToken)) {
          validTokens = await refreshAccessToken();
        }

        // Fetch current user profile
        const userResponse = await fetch(`${apiBaseUrl}/auth/me`, {
          headers: { Authorization: `Bearer ${validTokens.accessToken}` },
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
          setStatus('authenticated');
        } else {
          throw new Error('Failed to fetch user');
        }
      } catch {
        tokenStorage.clear();
        setTokens(null);
        setStatus('unauthenticated');
      }
    };

    initAuth();
  }, [apiBaseUrl, refreshAccessToken]);

  // --- Schedule proactive token refresh ---
  useEffect(() => {
    if (!tokens?.accessToken) return;

    const payload = parseJwt(tokens.accessToken);
    if (!payload?.exp) return;

    // Refresh 2 minutes before expiry
    const expiresAt = payload.exp * 1000;
    const refreshAt = expiresAt - 2 * 60 * 1000;
    const delay = refreshAt - Date.now();

    if (delay > 0) {
      refreshTimerRef.current = setTimeout(() => {
        refreshAccessToken().catch(() => {
          // If proactive refresh fails, the next API call will trigger it
        });
      }, delay);
    }

    return () => clearTimeout(refreshTimerRef.current);
  }, [tokens, refreshAccessToken]);

  // --- Listen for logout in other tabs ---
  useEffect(() => {
    const handleStorageChange = (event) => {
      if (event.key === 'auth_tokens' && event.newValue === null) {
        setTokens(null);
        setUser(null);
        setStatus('unauthenticated');
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const value = useMemo(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      isLoading: status === 'loading',
      login,
      logout,
      authenticatedFetch,
    }),
    [user, status, login, logout, authenticatedFetch]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// --- Consumer hook ---
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// --- Usage: App root ---
function App() {
  return (
    <AuthProvider apiBaseUrl="https://api.example.com">
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

// --- Usage: Protected route ---
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <div className="full-page-spinner" />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

// --- Usage: Login page ---
function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login({
        email: e.target.email.value,
        password: e.target.password.value,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <h1>Sign In</h1>
      {error && <div className="error-banner">{error}</div>}
      <input name="email" type="email" placeholder="Email" required />
      <input name="password" type="password" placeholder="Password" required />
      <button type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
  );
}

// --- Usage: Component that fetches authenticated data ---
function UserDashboard() {
  const { user, authenticatedFetch } = useAuth();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    authenticatedFetch('/api/dashboard/stats')
      .then(setStats)
      .catch(console.error);
  }, [authenticatedFetch]);

  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      {stats && (
        <div className="stats-grid">
          <div className="stat">Orders: {stats.totalOrders}</div>
          <div className="stat">Revenue: ${stats.revenue}</div>
        </div>
      )}
    </div>
  );
}
```

**Key production concerns addressed:**

- **Token refresh deduplication:** If three components simultaneously make API calls that all encounter an expired token, `refreshPromiseRef` ensures only one refresh request is made. All three callers await the same promise.
- **Proactive refresh:** A timer refreshes the token 2 minutes before it expires, so the user never experiences a failed request due to expiry.
- **Cross-tab session sync:** The `storage` event listener detects when another tab logs out, immediately updating the current tab's state.
- **Retry on 401:** If a request fails with 401 (e.g., the server revoked the token), the hook automatically refreshes and retries once before surfacing the error.
- **Graceful degradation:** Server-side logout is fire-and-forget. Even if the server is unreachable, the client cleans up its local state so the user can re-login.
- **`authenticatedFetch` as the single gateway:** Every API call in the app goes through this function, which transparently handles token attachment and refresh. Components never touch tokens directly.

This hook architecture — `AuthProvider` + `useAuth` + `authenticatedFetch` — is the gold standard for production React authentication. It separates the authentication *mechanism* (token refresh, storage, retry) from the authentication *policy* (which routes are protected, what happens on logout) and from the *UI* (login form, error messages).

---
