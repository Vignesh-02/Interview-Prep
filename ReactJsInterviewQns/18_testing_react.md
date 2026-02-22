# Testing React Applications (React Testing Library, Jest, Vitest) — React 18 Interview Questions

## Topic Introduction

**Testing** is not an afterthought in professional React development — it is a first-class engineering practice that determines the long-term maintainability, reliability, and velocity of a codebase. The React ecosystem has converged on a philosophy best captured by Kent C. Dodds' guiding principle: **"The more your tests resemble the way your software is used, the more confidence they can give you."** This means testing *behavior* rather than *implementation details*. You do not test whether `useState` was called with a particular value; you test that when a user clicks a button, the correct text appears on the screen. This philosophy drives the entire API design of **React Testing Library (RTL)**, which intentionally omits utilities for accessing component internals (`state`, `instance`, lifecycle methods) and instead provides queries that mirror how users and assistive technologies interact with the DOM — `getByRole`, `getByLabelText`, `getByText`. Paired with **Jest** (the dominant test runner for React) or **Vitest** (its modern Vite-native successor with near-identical APIs and dramatically faster execution), RTL enables you to write tests that survive refactors. If you rename an internal state variable, restructure your component tree, or swap a class component for a hook-based one, your tests should not break — because the user-facing behavior has not changed.

React 18 introduces specific testing considerations. **Automatic batching** means state updates inside `setTimeout`, promises, and native event handlers are now batched, which can change when re-renders occur in tests. **Concurrent features** like `startTransition`, `useDeferredValue`, and Suspense boundaries create asynchronous rendering paths that require careful use of `waitFor`, `findBy` queries, and `act()`. The `@testing-library/user-event` library (v14+) replaces the older `fireEvent` for simulating user interactions because it dispatches the full sequence of events a real browser would produce — `pointerDown`, `mouseDown`, `focus`, `pointerUp`, `mouseUp`, `click` — making tests more realistic. For server-state-heavy apps using TanStack Query, tests must wrap components in a `QueryClientProvider` with a fresh `QueryClient` per test to avoid cache leakage. For API mocking, **Mock Service Worker (MSW)** intercepts requests at the network level rather than patching `fetch` or `axios`, providing a more realistic and portable mocking layer. Understanding these tools and their interplay is essential for writing tests that provide genuine confidence in a React 18 application.

```jsx
// The testing philosophy in one example: test behavior, not implementation
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

function Counter() {
  const [count, setCount] = React.useState(0);
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
    </div>
  );
}

// ✅ Good — tests what the user sees and does
test('increments count when button is clicked', async () => {
  const user = userEvent.setup();
  render(<Counter />);

  expect(screen.getByText('Count: 0')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /increment/i }));
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});

// ❌ Bad — tests implementation details (would break on refactor)
// expect(component.state.count).toBe(1);  // Enzyme-style, fragile
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is the core testing philosophy behind React Testing Library, and how does it differ from Enzyme?

**Answer:**

React Testing Library (RTL) is built on a single guiding principle: **"The more your tests resemble the way your software is used, the more confidence they can give you."** This means you test the **output** your component renders and the **interactions** a user performs — not the internal implementation details like state variables, lifecycle methods, or component instances.

**Enzyme** (now unmaintained and incompatible with React 18) took the opposite approach. It provided methods like `shallow()` for rendering a component in isolation without its children, `.state()` for reading internal state, `.instance()` for accessing the component instance, and `.simulate()` for triggering synthetic events. This encouraged tests that were tightly coupled to implementation: if you renamed a state variable or refactored from a class to a function component, your tests would break — even though the user-facing behavior was identical.

RTL deliberately does not expose component internals. There is no `.state()`, no `.instance()`, no shallow rendering. Instead, it provides:

| RTL Concept | Purpose |
|---|---|
| `render()` | Renders the full component tree into a DOM container |
| `screen` | Provides queries to find elements (the way a user or screen reader would) |
| `getByRole`, `getByLabelText`, `getByText` | Semantic, accessibility-first queries |
| `userEvent` | Simulates real user interactions with full event sequences |
| `waitFor`, `findBy*` | Handles async rendering gracefully |

```jsx
// Enzyme style (❌ — tests implementation)
import { shallow } from 'enzyme';

test('toggles visibility', () => {
  const wrapper = shallow(<Toggle />);
  expect(wrapper.state('isVisible')).toBe(false);
  wrapper.find('button').simulate('click');
  expect(wrapper.state('isVisible')).toBe(true);
});

// React Testing Library style (✅ — tests behavior)
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('shows content when toggle button is clicked', async () => {
  const user = userEvent.setup();
  render(<Toggle />);

  expect(screen.queryByText('Hidden content')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /show/i }));
  expect(screen.getByText('Hidden content')).toBeInTheDocument();
});
```

The RTL test survives any refactor that preserves the behavior. Whether `Toggle` uses `useState`, `useReducer`, or a class component with `this.setState` — the test is unchanged.

---

### Q2. What are the main query types in React Testing Library, and what is the recommended priority for choosing them?

**Answer:**

RTL provides three categories of queries, each with a different return behavior:

| Prefix | Return on 0 matches | Return on 1 match | Return on 2+ matches | Async? |
|---|---|---|---|---|
| `getBy*` | Throws error | Returns element | Throws error | No |
| `queryBy*` | Returns `null` | Returns element | Throws error | No |
| `findBy*` | Throws (after timeout) | Returns element | Throws error | Yes (returns Promise) |

Each prefix has `*All*` variants (`getAllBy*`, `queryAllBy*`, `findAllBy*`) that return arrays.

The **recommended query priority** (from most to least preferred) is:

1. **`getByRole`** — Queries by ARIA role. This is the #1 recommended query because it mirrors how assistive technologies see the page. Most HTML elements have implicit roles (`button`, `heading`, `textbox`, `checkbox`, etc.).
2. **`getByLabelText`** — Finds form elements by their associated `<label>`. Excellent for forms.
3. **`getByPlaceholderText`** — Fallback for inputs without labels (less accessible).
4. **`getByText`** — Finds elements by visible text content. Good for non-interactive elements.
5. **`getByDisplayValue`** — Finds inputs/selects by their current displayed value.
6. **`getByAltText`** — For images.
7. **`getByTitle`** — For elements with a `title` attribute.
8. **`getByTestId`** — Last resort. Uses a `data-testid` attribute. Only when no semantic query works.

```jsx
import { render, screen } from '@testing-library/react';

function LoginForm() {
  return (
    <form>
      <label htmlFor="email">Email Address</label>
      <input id="email" type="email" placeholder="you@example.com" />

      <label htmlFor="password">Password</label>
      <input id="password" type="password" />

      <button type="submit">Sign In</button>
    </form>
  );
}

test('demonstrates query priority', () => {
  render(<LoginForm />);

  // ✅ Best — getByRole (button has implicit role)
  screen.getByRole('button', { name: /sign in/i });

  // ✅ Great — getByLabelText (tied to label, accessible)
  screen.getByLabelText(/email address/i);
  screen.getByLabelText(/password/i);

  // ✅ Acceptable — getByPlaceholderText
  screen.getByPlaceholderText('you@example.com');

  // ✅ Good — getByRole for inputs too
  screen.getByRole('textbox', { name: /email address/i });

  // ❌ Avoid unless necessary — getByTestId
  // screen.getByTestId('email-input');
});
```

Use `queryBy*` only when you need to **assert absence** (`expect(screen.queryByText('Error')).not.toBeInTheDocument()`). Use `findBy*` for elements that appear **asynchronously** (after data fetching, transitions, etc.).

---

### Q3. How do you set up a basic React testing environment with Jest (or Vitest) and React Testing Library?

**Answer:**

Both Jest and Vitest work with React Testing Library. The setup differs slightly depending on your bundler and tooling.

**With Jest (Create React App or manual setup):**

Install dependencies:
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom @babel/preset-env @babel/preset-react
```

Configure `jest.config.js`:
```jsx
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/src/setupTests.js'],
  transform: {
    '^.+\\.jsx?$': 'babel-jest',
  },
  moduleNameMapper: {
    '\\.(css|less|scss)$': 'identity-obj-proxy', // mock CSS modules
  },
};
```

Create `src/setupTests.js` to extend matchers:
```jsx
// src/setupTests.js
import '@testing-library/jest-dom';
```

**With Vitest (Vite-based projects):**

Install dependencies:
```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

Configure `vite.config.js`:
```jsx
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,           // enables describe/test/expect without imports
    setupFiles: './src/setupTests.js',
    css: true,
  },
});
```

`src/setupTests.js` is identical for both:
```jsx
import '@testing-library/jest-dom';
```

**Writing your first test:**
```jsx
// src/components/Greeting.jsx
export function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
}

// src/components/Greeting.test.jsx
import { render, screen } from '@testing-library/react';
import { Greeting } from './Greeting';

test('renders a greeting with the provided name', () => {
  render(<Greeting name="Alice" />);

  const heading = screen.getByRole('heading', { level: 1 });
  expect(heading).toHaveTextContent('Hello, Alice!');
});
```

Run tests:
```bash
# Jest
npx jest --watch

# Vitest (much faster — uses Vite's native ESM and esbuild transforms)
npx vitest --watch
```

Vitest is the recommended choice for new Vite-based projects because it shares the same config pipeline, supports ESM natively, and runs significantly faster than Jest due to Vite's on-demand transformation.

---

### Q4. What is the difference between `fireEvent` and `userEvent`, and why should you prefer `userEvent`?

**Answer:**

Both are used to simulate user interactions in tests, but they differ in **realism**:

**`fireEvent`** (from `@testing-library/react`) dispatches a single DOM event directly. When you call `fireEvent.click(button)`, it fires exactly one `click` event — nothing more.

**`userEvent`** (from `@testing-library/user-event` v14+) simulates the **full interaction sequence** a real user would produce. A real click involves: `pointerEnter` → `pointerDown` → `mouseDown` → `focus` → `pointerUp` → `mouseUp` → `click`. `userEvent.click()` dispatches all of these in order.

This matters because production code often listens to events other than `click` — `focus`, `mouseDown`, `pointerDown`, `keyDown`, etc. Using `fireEvent` can cause tests to pass even when the component is broken for real users.

| Feature | `fireEvent` | `userEvent` v14+ |
|---|---|---|
| Events dispatched | Single event | Full realistic sequence |
| Typing in inputs | Sets value directly | Types character by character (triggers `keyDown`, `keyPress`, `input`, `keyUp` per char) |
| Focus management | Manual | Automatic (moves focus like a real user) |
| Clipboard operations | Not supported | `copy()`, `paste()`, `cut()` supported |
| API style | Synchronous | Async (returns promises) |
| Setup | None | Requires `userEvent.setup()` |

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

function SearchBox({ onSearch }) {
  const [query, setQuery] = React.useState('');
  return (
    <form onSubmit={e => { e.preventDefault(); onSearch(query); }}>
      <input
        role="searchbox"
        value={query}
        onChange={e => setQuery(e.target.value)}
        onFocus={() => console.log('Focused!')}
      />
      <button type="submit">Search</button>
    </form>
  );
}

// ❌ fireEvent — doesn't trigger focus, types all at once
test('search with fireEvent', () => {
  const onSearch = jest.fn();
  render(<SearchBox onSearch={onSearch} />);

  const input = screen.getByRole('searchbox');
  fireEvent.change(input, { target: { value: 'react testing' } });
  // Focus event never fires! onChange fires once with full value.
  fireEvent.click(screen.getByRole('button', { name: /search/i }));
  expect(onSearch).toHaveBeenCalledWith('react testing');
});

// ✅ userEvent — triggers full event sequence per character
test('search with userEvent', async () => {
  const user = userEvent.setup();
  const onSearch = jest.fn();
  render(<SearchBox onSearch={onSearch} />);

  const input = screen.getByRole('searchbox');
  await user.click(input);         // triggers focus + pointer events
  await user.type(input, 'react testing'); // types char by char
  await user.click(screen.getByRole('button', { name: /search/i }));
  expect(onSearch).toHaveBeenCalledWith('react testing');
});
```

**Always use `userEvent.setup()`** at the start of each test. The setup instance configures the event system and should be used for all subsequent interactions within that test.

---

### Q5. What is `screen` in React Testing Library, and why is it preferred over destructuring `render()` results?

**Answer:**

`screen` is a convenience object exported from `@testing-library/react` that provides all query methods (`getByRole`, `queryByText`, `findByLabelText`, etc.) bound to `document.body`. It is the recommended way to access queries after rendering a component.

Before `screen` existed, the pattern was to destructure queries from the `render()` return value:

```jsx
// Old pattern — destructuring from render
const { getByText, getByRole, queryByText } = render(<MyComponent />);
getByText('Hello');
```

This has drawbacks:
1. You must destructure every query you need — leading to long destructuring lists.
2. If you add a new assertion mid-test, you need to go back and add the query to the destructure.
3. It's less readable because the queries are disconnected from where they came from.

`screen` solves all of this:

```jsx
import { render, screen } from '@testing-library/react';

function Notification({ message, type }) {
  return (
    <div role="alert" className={`notification notification--${type}`}>
      <strong>{type === 'error' ? 'Error: ' : 'Info: '}</strong>
      <span>{message}</span>
    </div>
  );
}

test('renders an error notification', () => {
  render(<Notification message="Something went wrong" type="error" />);

  // ✅ screen — clean, no destructuring, always available
  const alert = screen.getByRole('alert');
  expect(alert).toHaveTextContent('Error: Something went wrong');
  expect(screen.getByText('Something went wrong')).toBeInTheDocument();
});

test('renders an info notification', () => {
  render(<Notification message="Data saved" type="info" />);

  expect(screen.getByRole('alert')).toHaveTextContent('Info: Data saved');
});
```

**When you might still destructure `render()`:**

The `render()` return also includes non-query utilities like `container`, `unmount`, `rerender`, and `baseElement`. You destructure these when needed:

```jsx
test('re-renders with new props', () => {
  const { rerender } = render(<Notification message="Loading..." type="info" />);
  expect(screen.getByRole('alert')).toHaveTextContent('Loading...');

  rerender(<Notification message="Done!" type="info" />);
  expect(screen.getByRole('alert')).toHaveTextContent('Done!');
});
```

Use `screen` for queries, destructure `render()` only for utilities like `rerender`, `unmount`, or `container`.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you test asynchronous operations using `waitFor` and `findBy*` queries?

**Answer:**

React 18 components frequently render asynchronously — data fetching, lazy loading, transitions, and Suspense boundaries all cause elements to appear after the initial render. RTL provides two primary mechanisms for handling this:

1. **`findBy*` queries** — These are convenience wrappers around `getBy*` + `waitFor`. They return a Promise that resolves when the element appears or rejects after a timeout (default 1000ms).

2. **`waitFor(callback)`** — Repeatedly executes the callback until it stops throwing, or until the timeout is reached. Use this when you need to wait for a condition more complex than a single query.

**Production scenario:** A dashboard component fetches user data on mount and displays it:

```jsx
// UserDashboard.jsx
import { useState, useEffect } from 'react';

export function UserDashboard({ userId }) {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
      })
      .then(setUser)
      .catch(setError);
  }, [userId]);

  if (error) return <p role="alert">Error: {error.message}</p>;
  if (!user) return <p>Loading user...</p>;

  return (
    <div>
      <h1>{user.name}</h1>
      <p>Email: {user.email}</p>
      <span>Role: {user.role}</span>
    </div>
  );
}

// UserDashboard.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { UserDashboard } from './UserDashboard';

// Mock fetch at the module level
beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('displays user data after successful fetch', async () => {
  global.fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ name: 'Jane Doe', email: 'jane@example.com', role: 'Admin' }),
  });

  render(<UserDashboard userId="123" />);

  // Initially shows loading
  expect(screen.getByText('Loading user...')).toBeInTheDocument();

  // ✅ findBy — waits for the element to appear (returns a Promise)
  const heading = await screen.findByRole('heading', { name: /jane doe/i });
  expect(heading).toBeInTheDocument();

  // After data loads, check other fields
  expect(screen.getByText(/jane@example.com/)).toBeInTheDocument();
  expect(screen.getByText(/admin/i)).toBeInTheDocument();
});

test('displays error message on fetch failure', async () => {
  global.fetch.mockRejectedValueOnce(new Error('Network error'));

  render(<UserDashboard userId="123" />);

  // ✅ waitFor — retries until the assertion passes
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent('Error: Network error');
  });
});

test('refetches when userId changes', async () => {
  global.fetch
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ name: 'Jane', email: 'jane@co.com', role: 'Admin' }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ name: 'John', email: 'john@co.com', role: 'User' }),
    });

  const { rerender } = render(<UserDashboard userId="1" />);
  await screen.findByText('Jane');

  rerender(<UserDashboard userId="2" />);
  await screen.findByText('John');

  expect(global.fetch).toHaveBeenCalledTimes(2);
});
```

**Key rules:**
- Prefer `findBy*` over `waitFor` + `getBy*` when waiting for a single element.
- Never use `waitFor` around `fireEvent` or `userEvent` — those should be awaited directly.
- Set a custom timeout if your async operation takes longer than 1s: `await screen.findByText('Done', {}, { timeout: 3000 })`.
- With React 18's automatic batching, multiple state updates may be batched, changing when elements appear — `waitFor` and `findBy` handle this gracefully.

---

### Q7. How do you mock API calls using Mock Service Worker (MSW) in tests?

**Answer:**

**Mock Service Worker (MSW)** intercepts HTTP requests at the **network level** using a Service Worker (browser) or request interception (Node.js/test environment). Unlike mocking `fetch` or `axios` directly, MSW lets your application code run exactly as it would in production — the `fetch` call, headers, serialization, and error handling all execute for real. Only the network response is mocked.

This is dramatically more reliable than `jest.spyOn(global, 'fetch')` because:
- It works regardless of which HTTP client your code uses (fetch, axios, ky, etc.)
- Request/response transformations in your code are exercised
- Your mock handlers can be shared between tests and Storybook

**Setup for testing (MSW 2.x):**

```bash
npm install --save-dev msw
```

```jsx
// src/mocks/handlers.js
import { http, HttpResponse } from 'msw';

export const handlers = [
  // GET /api/products
  http.get('/api/products', () => {
    return HttpResponse.json([
      { id: 1, name: 'Keyboard', price: 79.99 },
      { id: 2, name: 'Mouse', price: 49.99 },
    ]);
  }),

  // POST /api/products
  http.post('/api/products', async ({ request }) => {
    const newProduct = await request.json();
    return HttpResponse.json(
      { id: 3, ...newProduct },
      { status: 201 }
    );
  }),
];

// src/mocks/server.js
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

Wire MSW into the test lifecycle:
```jsx
// src/setupTests.js
import '@testing-library/jest-dom';
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers()); // reset to default handlers
afterAll(() => server.close());
```

**Production scenario — testing a product listing page:**

```jsx
// ProductList.jsx
import { useState, useEffect } from 'react';

export function ProductList() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/products')
      .then(res => res.json())
      .then(data => { setProducts(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading products...</p>;

  return (
    <ul aria-label="Product list">
      {products.map(p => (
        <li key={p.id}>{p.name} — ${p.price}</li>
      ))}
    </ul>
  );
}

// ProductList.test.jsx
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { ProductList } from './ProductList';

test('renders products from the API', async () => {
  render(<ProductList />);

  expect(screen.getByText('Loading products...')).toBeInTheDocument();

  const items = await screen.findAllByRole('listitem');
  expect(items).toHaveLength(2);
  expect(items[0]).toHaveTextContent('Keyboard — $79.99');
  expect(items[1]).toHaveTextContent('Mouse — $49.99');
});

test('handles API errors gracefully', async () => {
  // ✅ Override the default handler for this single test
  server.use(
    http.get('/api/products', () => {
      return new HttpResponse(null, { status: 500 });
    })
  );

  render(<ProductList />);

  // After loading, the list should be empty (no crash)
  await screen.findByRole('list');
  expect(screen.queryAllByRole('listitem')).toHaveLength(0);
});

test('handles slow responses', async () => {
  server.use(
    http.get('/api/products', async () => {
      await new Promise(resolve => setTimeout(resolve, 200));
      return HttpResponse.json([{ id: 1, name: 'Delayed Item', price: 9.99 }]);
    })
  );

  render(<ProductList />);
  expect(screen.getByText('Loading products...')).toBeInTheDocument();

  const item = await screen.findByText(/delayed item/i);
  expect(item).toBeInTheDocument();
});
```

MSW is the recommended mocking strategy for all network requests in React tests. Use `server.use()` to override handlers per-test, and `server.resetHandlers()` in `afterEach` to restore defaults.

---

### Q8. How do you test custom hooks using `renderHook`?

**Answer:**

Custom hooks cannot be called outside of a React component — they rely on React's internal fiber tree and hook resolution. `renderHook` from `@testing-library/react` solves this by rendering the hook inside a minimal wrapper component, giving you access to the hook's return value and the ability to trigger re-renders.

**API:**
```jsx
const { result, rerender, unmount } = renderHook(() => useMyHook(args), {
  wrapper: MyProviderWrapper, // optional context provider
});
// result.current contains the hook's current return value
```

**Production scenario — a `useDebounce` hook:**

```jsx
// useDebounce.js
import { useState, useEffect } from 'react';

export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// useDebounce.test.js
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from './useDebounce';

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

test('returns the initial value immediately', () => {
  const { result } = renderHook(() => useDebounce('hello', 500));
  expect(result.current).toBe('hello');
});

test('debounces value updates', () => {
  const { result, rerender } = renderHook(
    ({ value, delay }) => useDebounce(value, delay),
    { initialProps: { value: 'hello', delay: 500 } }
  );

  // Update the value
  rerender({ value: 'hello world', delay: 500 });

  // Before the delay, still returns old value
  expect(result.current).toBe('hello');

  // Fast-forward time
  act(() => jest.advanceTimersByTime(500));

  // Now it returns the updated value
  expect(result.current).toBe('hello world');
});

test('cancels the previous timer on rapid changes', () => {
  const { result, rerender } = renderHook(
    ({ value }) => useDebounce(value, 300),
    { initialProps: { value: 'a' } }
  );

  rerender({ value: 'ab' });
  act(() => jest.advanceTimersByTime(100));

  rerender({ value: 'abc' });
  act(() => jest.advanceTimersByTime(100));

  rerender({ value: 'abcd' });
  act(() => jest.advanceTimersByTime(300));

  // Only the last value should have settled
  expect(result.current).toBe('abcd');
});
```

**Testing a hook that needs context (e.g., `useAuth`):**

```jsx
// useAuth.js
import { useContext } from 'react';
import { AuthContext } from './AuthContext';

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}

// useAuth.test.js
import { renderHook } from '@testing-library/react';
import { AuthContext } from './AuthContext';
import { useAuth } from './useAuth';

test('returns the auth context value', () => {
  const mockAuth = { user: { name: 'Alice' }, login: jest.fn(), logout: jest.fn() };

  const wrapper = ({ children }) => (
    <AuthContext.Provider value={mockAuth}>
      {children}
    </AuthContext.Provider>
  );

  const { result } = renderHook(() => useAuth(), { wrapper });

  expect(result.current.user.name).toBe('Alice');
  expect(result.current.login).toBeDefined();
});

test('throws if used outside AuthProvider', () => {
  expect(() => {
    renderHook(() => useAuth());
  }).toThrow('useAuth must be used within AuthProvider');
});
```

Use `renderHook` when you want to test hook logic in isolation. For hooks that are primarily about rendering (like `useFetch` that returns JSX-ready data), testing them through a component may be more valuable.

---

### Q9. How do you test components that consume React Context?

**Answer:**

Components that read from Context need a matching Provider in the component tree. In tests, you supply the Provider either by wrapping the component directly in `render()` or by creating a reusable custom render function.

**Production scenario — a theme-aware component:**

```jsx
// ThemeContext.jsx
import { createContext, useContext, useState } from 'react';

const ThemeContext = createContext(null);

export function ThemeProvider({ children, initialTheme = 'light' }) {
  const [theme, setTheme] = useState(initialTheme);
  const toggleTheme = () => setTheme(t => (t === 'light' ? 'dark' : 'light'));
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

// ThemeToggle.jsx
import { useTheme } from './ThemeContext';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button onClick={toggleTheme}>
      Current theme: {theme}. Switch to {theme === 'light' ? 'dark' : 'light'}
    </button>
  );
}
```

**Approach 1: Wrap inline in each test**
```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from './ThemeContext';
import { ThemeToggle } from './ThemeToggle';

test('toggles from light to dark', async () => {
  const user = userEvent.setup();

  render(
    <ThemeProvider initialTheme="light">
      <ThemeToggle />
    </ThemeProvider>
  );

  const button = screen.getByRole('button');
  expect(button).toHaveTextContent('Current theme: light');

  await user.click(button);
  expect(button).toHaveTextContent('Current theme: dark');
});
```

**Approach 2: Custom render function (recommended for repeated use)**
```jsx
// test-utils.jsx
import { render } from '@testing-library/react';
import { ThemeProvider } from './ThemeContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

export function renderWithProviders(
  ui,
  {
    theme = 'light',
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    }),
    ...renderOptions
  } = {}
) {
  function Wrapper({ children }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider initialTheme={theme}>
          {children}
        </ThemeProvider>
      </QueryClientProvider>
    );
  }

  return { ...render(ui, { wrapper: Wrapper, ...renderOptions }), queryClient };
}

// Usage in tests:
import { renderWithProviders } from '../test-utils';

test('renders in dark mode', () => {
  renderWithProviders(<ThemeToggle />, { theme: 'dark' });

  expect(screen.getByRole('button')).toHaveTextContent('Current theme: dark');
});
```

**Testing that a component without a Provider throws:**
```jsx
test('ThemeToggle throws without ThemeProvider', () => {
  // Suppress console.error for expected error boundary output
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

  expect(() => render(<ThemeToggle />)).toThrow(
    'useTheme must be used within ThemeProvider'
  );

  spy.mockRestore();
});
```

The custom `renderWithProviders` pattern scales well — as your app adds more providers (auth, router, query client, i18n), you extend the wrapper once and all tests benefit automatically.

---

### Q10. How do you test form validation and submission in React?

**Answer:**

Form testing should verify: initial state, field interactions, validation messages, submission behavior, and error handling — all from the user's perspective.

**Production scenario — a registration form with validation:**

```jsx
// RegisterForm.jsx
import { useState } from 'react';

export function RegisterForm({ onSubmit }) {
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const validate = (formData) => {
    const errs = {};
    const email = formData.get('email');
    const password = formData.get('password');
    const confirm = formData.get('confirmPassword');

    if (!email) errs.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(email)) errs.email = 'Invalid email address';

    if (!password) errs.password = 'Password is required';
    else if (password.length < 8) errs.password = 'Password must be at least 8 characters';

    if (password !== confirm) errs.confirmPassword = 'Passwords do not match';

    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const validationErrors = validate(formData);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSubmitting(true);
    setErrors({});
    try {
      await onSubmit({
        email: formData.get('email'),
        password: formData.get('password'),
      });
    } catch (err) {
      setErrors({ form: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" aria-describedby="email-error" />
        {errors.email && <span id="email-error" role="alert">{errors.email}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input id="password" name="password" type="password" aria-describedby="password-error" />
        {errors.password && <span id="password-error" role="alert">{errors.password}</span>}
      </div>

      <div>
        <label htmlFor="confirmPassword">Confirm Password</label>
        <input id="confirmPassword" name="confirmPassword" type="password" aria-describedby="confirm-error" />
        {errors.confirmPassword && <span id="confirm-error" role="alert">{errors.confirmPassword}</span>}
      </div>

      {errors.form && <div role="alert">{errors.form}</div>}

      <button type="submit" disabled={submitting}>
        {submitting ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
}
```

**Comprehensive test suite:**

```jsx
// RegisterForm.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RegisterForm } from './RegisterForm';

function setup(props = {}) {
  const user = userEvent.setup();
  const onSubmit = jest.fn().mockResolvedValue(undefined);
  render(<RegisterForm onSubmit={onSubmit} {...props} />);
  return {
    user,
    onSubmit,
    emailInput: screen.getByLabelText(/email/i),
    passwordInput: screen.getByLabelText(/^password$/i),
    confirmInput: screen.getByLabelText(/confirm password/i),
    submitButton: screen.getByRole('button', { name: /register/i }),
  };
}

test('shows validation errors for empty submission', async () => {
  const { user, submitButton } = setup();

  await user.click(submitButton);

  expect(screen.getByText('Email is required')).toBeInTheDocument();
  expect(screen.getByText('Password is required')).toBeInTheDocument();
});

test('shows error for invalid email format', async () => {
  const { user, emailInput, passwordInput, confirmInput, submitButton } = setup();

  await user.type(emailInput, 'not-an-email');
  await user.type(passwordInput, 'password123');
  await user.type(confirmInput, 'password123');
  await user.click(submitButton);

  expect(screen.getByText('Invalid email address')).toBeInTheDocument();
});

test('shows error when passwords do not match', async () => {
  const { user, emailInput, passwordInput, confirmInput, submitButton } = setup();

  await user.type(emailInput, 'alice@example.com');
  await user.type(passwordInput, 'password123');
  await user.type(confirmInput, 'different456');
  await user.click(submitButton);

  expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
});

test('submits valid form data and disables button during submission', async () => {
  const { user, emailInput, passwordInput, confirmInput, submitButton, onSubmit } = setup();

  await user.type(emailInput, 'alice@example.com');
  await user.type(passwordInput, 'password123');
  await user.type(confirmInput, 'password123');
  await user.click(submitButton);

  expect(onSubmit).toHaveBeenCalledWith({
    email: 'alice@example.com',
    password: 'password123',
  });
});

test('displays server error on submission failure', async () => {
  const { user, emailInput, passwordInput, confirmInput, submitButton, onSubmit } = setup();

  onSubmit.mockRejectedValueOnce(new Error('Email already taken'));

  await user.type(emailInput, 'alice@example.com');
  await user.type(passwordInput, 'password123');
  await user.type(confirmInput, 'password123');
  await user.click(submitButton);

  await waitFor(() => {
    expect(screen.getByText('Email already taken')).toBeInTheDocument();
  });

  // Button should be re-enabled after error
  expect(submitButton).not.toBeDisabled();
});
```

**Key patterns:** Use `getByLabelText` for form fields (tests accessibility), use `role="alert"` for error messages (screen-reader-friendly), and create a `setup()` helper to reduce duplication across tests.

---

### Q11. How do you test Error Boundaries in React?

**Answer:**

Error boundaries are class components (or libraries wrapping them) that catch JavaScript errors during rendering, in lifecycle methods, and in constructors of child components. Testing them requires deliberately causing a child component to throw during render.

**Production scenario:**

```jsx
// ErrorBoundary.jsx
import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log to error reporting service in production
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div role="alert">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

**Testing the error boundary:**

```jsx
// ErrorBoundary.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorBoundary } from './ErrorBoundary';

// A component that deliberately throws
function ThrowingComponent({ shouldThrow }) {
  if (shouldThrow) {
    throw new Error('Test explosion');
  }
  return <p>All is well</p>;
}

// Suppress console.error for expected errors — React logs caught errors
let consoleSpy;
beforeEach(() => {
  consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => {
  consoleSpy.mockRestore();
});

test('renders children when there is no error', () => {
  render(
    <ErrorBoundary>
      <ThrowingComponent shouldThrow={false} />
    </ErrorBoundary>
  );

  expect(screen.getByText('All is well')).toBeInTheDocument();
});

test('renders fallback UI when a child throws', () => {
  render(
    <ErrorBoundary>
      <ThrowingComponent shouldThrow={true} />
    </ErrorBoundary>
  );

  expect(screen.getByRole('alert')).toBeInTheDocument();
  expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  expect(screen.getByText('Test explosion')).toBeInTheDocument();
});

test('calls onError callback with error details', () => {
  const onError = jest.fn();

  render(
    <ErrorBoundary onError={onError}>
      <ThrowingComponent shouldThrow={true} />
    </ErrorBoundary>
  );

  expect(onError).toHaveBeenCalledTimes(1);
  expect(onError).toHaveBeenCalledWith(
    expect.any(Error),
    expect.objectContaining({ componentStack: expect.any(String) })
  );
});

test('recovers when "Try Again" is clicked and error is resolved', async () => {
  const user = userEvent.setup();

  const { rerender } = render(
    <ErrorBoundary>
      <ThrowingComponent shouldThrow={true} />
    </ErrorBoundary>
  );

  expect(screen.getByText('Something went wrong')).toBeInTheDocument();

  // Simulate the error condition being fixed before retry
  rerender(
    <ErrorBoundary>
      <ThrowingComponent shouldThrow={false} />
    </ErrorBoundary>
  );

  await user.click(screen.getByRole('button', { name: /try again/i }));

  expect(screen.getByText('All is well')).toBeInTheDocument();
  expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
});

test('renders custom fallback when provided', () => {
  const customFallback = <div>Custom error page</div>;

  render(
    <ErrorBoundary fallback={customFallback}>
      <ThrowingComponent shouldThrow={true} />
    </ErrorBoundary>
  );

  expect(screen.getByText('Custom error page')).toBeInTheDocument();
});
```

**Important:** Always suppress `console.error` in error boundary tests — React intentionally logs caught errors to the console, and without suppression your test output will be noisy. Restore the spy in `afterEach` to avoid leaking into other tests.

---

### Q12. How do you test components that use React Router?

**Answer:**

Components using React Router hooks (`useParams`, `useNavigate`, `useLocation`, `useSearchParams`) need a router context. RTL tests provide this using `MemoryRouter` (for unit/integration tests) or `createMemoryRouter` (for data router patterns in React Router 6.4+).

**Production scenario — a product detail page:**

```jsx
// ProductDetail.jsx
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

export function ProductDetail() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);

  useEffect(() => {
    fetch(`/api/products/${productId}`)
      .then(res => res.json())
      .then(setProduct);
  }, [productId]);

  if (!product) return <p>Loading...</p>;

  return (
    <article>
      <h1>{product.name}</h1>
      <p>Price: ${product.price}</p>
      <Link to="/products">Back to Products</Link>
      <button onClick={() => navigate(`/products/${productId}/edit`)}>
        Edit Product
      </button>
    </article>
  );
}
```

**Testing with `MemoryRouter`:**

```jsx
// ProductDetail.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { ProductDetail } from './ProductDetail';

function renderWithRouter(initialRoute = '/products/42') {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/products/:productId" element={<ProductDetail />} />
        <Route path="/products/:productId/edit" element={<p>Edit Page</p>} />
        <Route path="/products" element={<p>Product List</p>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeAll(() => {
  server.use(
    http.get('/api/products/:id', ({ params }) => {
      return HttpResponse.json({
        id: params.id,
        name: 'Mechanical Keyboard',
        price: 149.99,
      });
    })
  );
});

test('renders product details from URL params', async () => {
  renderWithRouter('/products/42');

  expect(screen.getByText('Loading...')).toBeInTheDocument();

  await screen.findByRole('heading', { name: /mechanical keyboard/i });
  expect(screen.getByText('Price: $149.99')).toBeInTheDocument();
});

test('navigates to edit page when Edit button is clicked', async () => {
  const user = userEvent.setup();
  renderWithRouter('/products/42');

  await screen.findByRole('heading', { name: /mechanical keyboard/i });

  await user.click(screen.getByRole('button', { name: /edit product/i }));

  expect(screen.getByText('Edit Page')).toBeInTheDocument();
});

test('navigates back to product list via link', async () => {
  const user = userEvent.setup();
  renderWithRouter('/products/42');

  await screen.findByRole('heading', { name: /mechanical keyboard/i });

  await user.click(screen.getByRole('link', { name: /back to products/i }));

  expect(screen.getByText('Product List')).toBeInTheDocument();
});
```

**Testing with React Router 6.4+ data routers (`createMemoryRouter`):**

```jsx
import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';

test('loader data is available to the component', async () => {
  const router = createMemoryRouter(
    [
      {
        path: '/products/:productId',
        element: <ProductDetail />,
        loader: () => ({
          id: '42',
          name: 'Ergonomic Mouse',
          price: 89.99,
        }),
      },
    ],
    { initialEntries: ['/products/42'] }
  );

  render(<RouterProvider router={router} />);

  await screen.findByRole('heading', { name: /ergonomic mouse/i });
});
```

**Key tips:**
- Use `MemoryRouter` — never `BrowserRouter` — in tests (no real browser history API in jsdom).
- Define enough `Route` elements to verify navigation actually works.
- Use `initialEntries` to set the starting URL and test URL-dependent behavior.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you test components that use TanStack Query?

**Answer:**

TanStack Query (React Query) manages server state with a shared cache. In tests, you must create a **fresh `QueryClient` per test** to prevent cache leakage between tests, and wrap components in `QueryClientProvider`. You should also disable retries and set `gcTime` to `Infinity` to avoid test interference.

**Production scenario — testing a component with `useQuery` and `useMutation`:**

```jsx
// test-utils.jsx — reusable wrapper
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,           // don't retry failed queries in tests
        gcTime: Infinity,       // don't garbage collect during test
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {},          // suppress error logging in tests
    },
  });
}

export function renderWithQueryClient(ui, { queryClient, ...options } = {}) {
  const testQueryClient = queryClient || createTestQueryClient();
  function Wrapper({ children }) {
    return (
      <QueryClientProvider client={testQueryClient}>
        {children}
      </QueryClientProvider>
    );
  }
  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
    queryClient: testQueryClient,
  };
}
```

```jsx
// UserSettings.jsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function UserSettings() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['settings'],
    queryFn: () => fetch('/api/settings').then(r => r.json()),
  });

  const updateSettings = useMutation({
    mutationFn: (newSettings) =>
      fetch('/api/settings', {
        method: 'PUT',
        body: JSON.stringify(newSettings),
        headers: { 'Content-Type': 'application/json' },
      }).then(r => r.json()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }),
  });

  if (isLoading) return <p>Loading settings...</p>;
  if (error) return <p role="alert">Failed to load settings</p>;

  return (
    <div>
      <h2>Settings</h2>
      <p>Notifications: {settings.notifications ? 'On' : 'Off'}</p>
      <button
        onClick={() =>
          updateSettings.mutate({ notifications: !settings.notifications })
        }
        disabled={updateSettings.isPending}
      >
        {updateSettings.isPending ? 'Saving...' : 'Toggle Notifications'}
      </button>
      {updateSettings.isError && (
        <p role="alert">Failed to save: {updateSettings.error.message}</p>
      )}
    </div>
  );
}

// UserSettings.test.jsx
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { renderWithQueryClient } from '../test-utils';
import { UserSettings } from './UserSettings';

test('loads and displays settings', async () => {
  server.use(
    http.get('/api/settings', () =>
      HttpResponse.json({ notifications: true })
    )
  );

  renderWithQueryClient(<UserSettings />);

  expect(screen.getByText('Loading settings...')).toBeInTheDocument();
  await screen.findByText('Notifications: On');
});

test('toggles notifications via mutation', async () => {
  const user = userEvent.setup();
  let currentNotifications = true;

  server.use(
    http.get('/api/settings', () =>
      HttpResponse.json({ notifications: currentNotifications })
    ),
    http.put('/api/settings', async ({ request }) => {
      const body = await request.json();
      currentNotifications = body.notifications;
      return HttpResponse.json({ notifications: currentNotifications });
    })
  );

  renderWithQueryClient(<UserSettings />);

  await screen.findByText('Notifications: On');

  await user.click(screen.getByRole('button', { name: /toggle notifications/i }));

  // After mutation + refetch, the UI updates
  await screen.findByText('Notifications: Off');
});

test('shows error when settings fail to load', async () => {
  server.use(
    http.get('/api/settings', () => new HttpResponse(null, { status: 500 }))
  );

  renderWithQueryClient(<UserSettings />);

  await screen.findByRole('alert');
  expect(screen.getByText('Failed to load settings')).toBeInTheDocument();
});

test('shows mutation error on save failure', async () => {
  const user = userEvent.setup();

  server.use(
    http.get('/api/settings', () =>
      HttpResponse.json({ notifications: true })
    ),
    http.put('/api/settings', () => new HttpResponse(null, { status: 500 }))
  );

  renderWithQueryClient(<UserSettings />);
  await screen.findByText('Notifications: On');

  await user.click(screen.getByRole('button', { name: /toggle notifications/i }));

  await screen.findByText(/failed to save/i);
});
```

**Key rules for TanStack Query tests:**
- Always create a fresh `QueryClient` per test — never share between tests.
- Set `retry: false` — otherwise tests wait through retry delays.
- Use MSW for network mocking — it works seamlessly with TanStack Query's real `fetch` calls.
- Use `queryClient.invalidateQueries` awareness — after mutation, the query refetches, so mock the GET handler to return updated data.

---

### Q14. What are effective integration testing patterns for React applications?

**Answer:**

Integration tests verify that **multiple units work together** correctly — a page with its child components, hooks, context providers, routing, and data fetching layer all interacting as they do in production. They provide the highest confidence-to-cost ratio in the testing pyramid.

**Philosophy:** Unit test isolated logic (utility functions, custom hooks). Integration test user flows (page-level interactions). E2E test critical paths in a real browser.

**Production scenario — testing a complete checkout flow:**

```jsx
// CheckoutPage.jsx (simplified)
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { CartSummary } from './CartSummary';
import { PaymentForm } from './PaymentForm';
import { useCart } from '../hooks/useCart';

export function CheckoutPage() {
  const { items, total, clearCart } = useCart();
  const navigate = useNavigate();
  const [step, setStep] = useState('review'); // 'review' | 'payment' | 'confirmation'

  const placeOrder = useMutation({
    mutationFn: (orderData) =>
      fetch('/api/orders', {
        method: 'POST',
        body: JSON.stringify(orderData),
        headers: { 'Content-Type': 'application/json' },
      }).then(r => {
        if (!r.ok) throw new Error('Order failed');
        return r.json();
      }),
    onSuccess: (data) => {
      clearCart();
      setStep('confirmation');
    },
  });

  if (items.length === 0 && step !== 'confirmation') {
    return <p>Your cart is empty. <a href="/products">Browse products</a></p>;
  }

  return (
    <div>
      {step === 'review' && (
        <>
          <CartSummary items={items} total={total} />
          <button onClick={() => setStep('payment')}>Proceed to Payment</button>
        </>
      )}

      {step === 'payment' && (
        <PaymentForm
          onSubmit={(paymentData) =>
            placeOrder.mutate({ items, total, ...paymentData })
          }
          isProcessing={placeOrder.isPending}
          error={placeOrder.error?.message}
        />
      )}

      {step === 'confirmation' && (
        <div>
          <h2>Order Confirmed!</h2>
          <p>Thank you for your purchase.</p>
          <button onClick={() => navigate('/products')}>Continue Shopping</button>
        </div>
      )}
    </div>
  );
}
```

**Integration test — the full checkout flow:**

```jsx
// CheckoutPage.integration.test.jsx
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { renderWithQueryClient } from '../test-utils';
import { CartProvider } from '../context/CartContext';
import { CheckoutPage } from './CheckoutPage';

function renderCheckout(cartItems = []) {
  return renderWithQueryClient(
    <CartProvider initialItems={cartItems}>
      <MemoryRouter initialEntries={['/checkout']}>
        <Routes>
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/products" element={<p>Products Page</p>} />
        </Routes>
      </MemoryRouter>
    </CartProvider>
  );
}

const mockCartItems = [
  { id: 1, name: 'Keyboard', price: 79.99, quantity: 1 },
  { id: 2, name: 'Mouse', price: 49.99, quantity: 2 },
];

test('complete checkout flow: review → payment → confirmation', async () => {
  const user = userEvent.setup();

  server.use(
    http.post('/api/orders', () =>
      HttpResponse.json({ orderId: 'ORD-123' }, { status: 201 })
    )
  );

  renderCheckout(mockCartItems);

  // Step 1: Review cart
  expect(screen.getByText('Keyboard')).toBeInTheDocument();
  expect(screen.getByText('Mouse')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: /proceed to payment/i }));

  // Step 2: Fill payment form
  await user.type(screen.getByLabelText(/card number/i), '4242424242424242');
  await user.type(screen.getByLabelText(/expiry/i), '12/27');
  await user.type(screen.getByLabelText(/cvv/i), '123');
  await user.click(screen.getByRole('button', { name: /place order/i }));

  // Step 3: Confirmation
  await screen.findByText('Order Confirmed!');
  expect(screen.getByText('Thank you for your purchase.')).toBeInTheDocument();
});

test('shows empty cart message when no items', () => {
  renderCheckout([]);

  expect(screen.getByText(/your cart is empty/i)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /browse products/i })).toBeInTheDocument();
});

test('handles order API failure', async () => {
  const user = userEvent.setup();

  server.use(
    http.post('/api/orders', () => new HttpResponse(null, { status: 500 }))
  );

  renderCheckout(mockCartItems);

  await user.click(screen.getByRole('button', { name: /proceed to payment/i }));
  await user.type(screen.getByLabelText(/card number/i), '4242424242424242');
  await user.type(screen.getByLabelText(/expiry/i), '12/27');
  await user.type(screen.getByLabelText(/cvv/i), '123');
  await user.click(screen.getByRole('button', { name: /place order/i }));

  await screen.findByText(/order failed/i);
  // User should still be on payment step to retry
  expect(screen.getByLabelText(/card number/i)).toBeInTheDocument();
});
```

**Integration test best practices:**
- Render at the page level with all real providers (router, query client, context).
- Mock only the network boundary (with MSW), not internal modules.
- Test complete user flows across multiple interactions.
- Each test should be independent — fresh query client, fresh MSW handlers.

---

### Q15. How do you test accessibility in React applications?

**Answer:**

Accessibility (a11y) testing in React operates at multiple levels: **static analysis** (eslint-plugin-jsx-a11y), **automated runtime checks** (jest-axe), and **semantic query enforcement** (RTL's query priority). Together, they catch a significant portion of a11y issues automatically, though manual testing with screen readers remains essential for complex interactions.

**`jest-axe`** runs the axe-core accessibility engine against your rendered DOM:

```bash
npm install --save-dev jest-axe
```

```jsx
// Setup — extend expect with toHaveNoViolations
// src/setupTests.js
import '@testing-library/jest-dom';
import 'jest-axe/extend-expect';
```

**Production scenario — testing a navigation component for accessibility:**

```jsx
// Navigation.jsx
import { NavLink } from 'react-router-dom';

export function Navigation({ user }) {
  return (
    <nav aria-label="Main navigation">
      <ul role="list">
        <li><NavLink to="/">Home</NavLink></li>
        <li><NavLink to="/products">Products</NavLink></li>
        <li><NavLink to="/about">About</NavLink></li>
        {user ? (
          <>
            <li><NavLink to="/dashboard">Dashboard</NavLink></li>
            <li>
              <button aria-label={`Sign out ${user.name}`}>Sign Out</button>
            </li>
          </>
        ) : (
          <li><NavLink to="/login">Sign In</NavLink></li>
        )}
      </ul>
    </nav>
  );
}

// Navigation.test.jsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe } from 'jest-axe';
import { Navigation } from './Navigation';

function renderNav(user = null) {
  return render(
    <MemoryRouter>
      <Navigation user={user} />
    </MemoryRouter>
  );
}

test('navigation has no accessibility violations (logged out)', async () => {
  const { container } = renderNav();
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

test('navigation has no accessibility violations (logged in)', async () => {
  const { container } = renderNav({ name: 'Alice', role: 'admin' });
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

test('uses correct ARIA landmarks and roles', () => {
  renderNav({ name: 'Alice' });

  // Navigation landmark
  const nav = screen.getByRole('navigation', { name: /main navigation/i });
  expect(nav).toBeInTheDocument();

  // Links are accessible by role
  expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /products/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();

  // Sign out button has descriptive label
  expect(screen.getByRole('button', { name: /sign out alice/i })).toBeInTheDocument();
});
```

**Testing a modal for focus management and keyboard accessibility:**

```jsx
// Modal.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe } from 'jest-axe';
import { Modal } from './Modal';

test('modal traps focus and can be closed with Escape', async () => {
  const user = userEvent.setup();
  const onClose = jest.fn();

  render(
    <Modal isOpen={true} onClose={onClose} title="Confirm Delete">
      <p>Are you sure you want to delete this item?</p>
      <button>Cancel</button>
      <button>Delete</button>
    </Modal>
  );

  // Modal should have dialog role
  const dialog = screen.getByRole('dialog', { name: /confirm delete/i });
  expect(dialog).toBeInTheDocument();

  // Focus should be inside the modal
  expect(document.activeElement).toBeInstanceOf(HTMLElement);
  expect(dialog.contains(document.activeElement)).toBe(true);

  // Escape key closes modal
  await user.keyboard('{Escape}');
  expect(onClose).toHaveBeenCalledTimes(1);
});

test('modal has no accessibility violations', async () => {
  const { container } = render(
    <Modal isOpen={true} onClose={() => {}} title="Settings">
      <label htmlFor="theme">Theme</label>
      <select id="theme">
        <option>Light</option>
        <option>Dark</option>
      </select>
    </Modal>
  );

  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

**Layered a11y strategy:**
1. **ESLint** (`eslint-plugin-jsx-a11y`) — catches issues at code-write time (missing alt text, invalid ARIA).
2. **RTL queries** (`getByRole`, `getByLabelText`) — tests fail if elements lack proper semantics.
3. **jest-axe** — catches runtime issues (color contrast, missing labels, invalid nesting).
4. **Manual testing** — screen readers (VoiceOver, NVDA) for complex widget interactions.

---

### Q16. How do you approach E2E testing for React applications with Playwright or Cypress?

**Answer:**

End-to-end (E2E) tests run your React application in a **real browser**, interact with it as a real user would, and verify the full stack — frontend, API, database, auth, etc. They sit at the top of the testing pyramid: highest confidence, highest cost.

**Playwright** (recommended for new projects in 2024+) is faster, supports multiple browsers natively (Chromium, Firefox, WebKit), runs in parallel, has built-in auto-waiting, and has excellent TypeScript support. **Cypress** is more established, has a rich plugin ecosystem, and provides a time-travel debugging UI.

**Production scenario — E2E testing a login flow with Playwright:**

```jsx
// e2e/login.spec.ts (Playwright)
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('successful login redirects to dashboard', async ({ page }) => {
    // Fill in credentials
    await page.getByLabel('Email').fill('alice@example.com');
    await page.getByLabel('Password').fill('securePassword123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByRole('heading', { name: /welcome, alice/i })).toBeVisible();

    // Verify auth state persists
    await page.reload();
    await expect(page.getByRole('heading', { name: /welcome, alice/i })).toBeVisible();
  });

  test('shows validation errors for invalid credentials', async ({ page }) => {
    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByRole('alert')).toContainText('Invalid credentials');
    await expect(page).toHaveURL('/login'); // stays on login page
  });

  test('is accessible', async ({ page }) => {
    // Playwright + axe-core for E2E accessibility
    const { checkA11y, injectAxe } = require('axe-playwright');
    await injectAxe(page);
    await checkA11y(page);
  });
});

test.describe('Protected Routes', () => {
  test('redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login?redirect=/dashboard');
  });

  test('redirects back after login', async ({ page }) => {
    // Navigate to protected route (redirects to login)
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login?redirect=/dashboard');

    // Login
    await page.getByLabel('Email').fill('alice@example.com');
    await page.getByLabel('Password').fill('securePassword123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should redirect back to originally requested page
    await expect(page).toHaveURL('/dashboard');
  });
});
```

**Same scenario with Cypress:**

```jsx
// cypress/e2e/login.cy.js
describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('successful login redirects to dashboard', () => {
    cy.findByLabelText(/email/i).type('alice@example.com');
    cy.findByLabelText(/password/i).type('securePassword123');
    cy.findByRole('button', { name: /sign in/i }).click();

    cy.url().should('include', '/dashboard');
    cy.findByRole('heading', { name: /welcome, alice/i }).should('be.visible');
  });

  it('shows validation errors for invalid credentials', () => {
    cy.findByLabelText(/email/i).type('wrong@example.com');
    cy.findByLabelText(/password/i).type('wrongpassword');
    cy.findByRole('button', { name: /sign in/i }).click();

    cy.findByRole('alert').should('contain', 'Invalid credentials');
    cy.url().should('include', '/login');
  });
});
```

**E2E best practices:**
- **Test critical paths only** — login, checkout, signup, core CRUD flows. E2E is expensive; don't duplicate unit/integration coverage.
- **Use Playwright's locators** — they auto-wait, are resilient, and use the same `getByRole` philosophy as RTL.
- **Seed test data** — use API calls in `beforeEach` or fixtures, not the UI, to set up test state.
- **Run in CI** — Playwright supports sharding across multiple CI runners for parallelism.
- **Visual comparison** — Playwright has built-in screenshot comparison: `await expect(page).toHaveScreenshot()`.

---

### Q17. What are effective test coverage strategies, and how do you integrate testing into CI/CD?

**Answer:**

Test coverage measures what percentage of your code is exercised by tests. While 100% coverage is not the goal (you can have 100% coverage and still miss critical bugs), coverage metrics help identify **untested risk areas**.

**Coverage configuration (Jest):**

```jsx
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/mocks/**',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
  ],
  coverageThresholds: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    // Stricter thresholds for critical paths
    './src/utils/payment.ts': {
      branches: 95,
      functions: 100,
      lines: 95,
    },
  },
};
```

**Coverage configuration (Vitest):**

```jsx
// vite.config.js
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',            // or 'istanbul'
      reporter: ['text', 'html', 'lcov', 'json-summary'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/**/*.stories.{ts,tsx}',
        'src/mocks/**',
      ],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80,
      },
    },
  },
});
```

**CI/CD pipeline (GitHub Actions):**

```jsx
// .github/workflows/test.yml
name: Test & Coverage

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  unit-and-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run type check
        run: npm run typecheck

      - name: Run unit & integration tests with coverage
        run: npx vitest run --coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true

  e2e:
    runs-on: ubuntu-latest
    needs: unit-and-integration
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Build app
        run: npm run build

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
```

**Coverage strategy by code area:**

| Code Area | Target Coverage | Test Type |
|---|---|---|
| Utility functions / pure logic | 95%+ | Unit tests |
| Custom hooks | 90%+ | `renderHook` unit tests |
| UI components (presentational) | 80%+ | Integration tests via page-level tests |
| Pages / features | 80%+ | Integration tests (render page, simulate user flows) |
| Critical paths (auth, payments) | 95%+ | Integration + E2E |
| Error handling | 85%+ | Edge case unit + integration tests |
| Config / constants / types | Exclude | N/A |

**Key principles:**
- Coverage is a **metric**, not a goal. Aim for meaningful tests, not number games.
- Enforce coverage **thresholds that only go up** — ratchet, never lower them.
- Use **per-file thresholds** for critical code (payment, auth, data validation).
- Run unit/integration tests on every PR; run E2E on merge to main (or on PRs that touch critical paths).
- Parallelize tests in CI — Vitest supports `--pool=threads`, Playwright supports sharding.

---

### Q18. How do you performance-test React components using React Profiler?

**Answer:**

React provides a built-in `<Profiler>` component that measures rendering performance — how long each render takes, whether it was caused by props, state, or context changes, and whether work was committed to the DOM. In tests, you can use the `onRender` callback to assert that components meet performance budgets.

**The `onRender` callback signature:**

```jsx
function onRender(
  id,                // the "id" prop of the Profiler tree
  phase,             // "mount" | "update" | "nested-update"
  actualDuration,    // time spent rendering the committed update (ms)
  baseDuration,      // estimated time to render the entire subtree without memoization
  startTime,         // when React began rendering this update
  commitTime         // when React committed this update
) { /* ... */ }
```

**Production scenario — verifying a large list doesn't degrade on re-render:**

```jsx
// ProductTable.jsx
import { memo, Profiler } from 'react';

const ProductRow = memo(function ProductRow({ product }) {
  return (
    <tr>
      <td>{product.name}</td>
      <td>${product.price.toFixed(2)}</td>
      <td>{product.category}</td>
    </tr>
  );
});

export function ProductTable({ products, onRenderCallback }) {
  return (
    <Profiler id="ProductTable" onRender={onRenderCallback || (() => {})}>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Price</th>
            <th>Category</th>
          </tr>
        </thead>
        <tbody>
          {products.map(p => (
            <ProductRow key={p.id} product={p} />
          ))}
        </tbody>
      </table>
    </Profiler>
  );
}
```

**Performance test:**

```jsx
// ProductTable.perf.test.jsx
import { render, screen } from '@testing-library/react';
import { Profiler } from 'react';
import { ProductTable } from './ProductTable';

function generateProducts(count) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    name: `Product ${i}`,
    price: Math.random() * 100,
    category: ['Electronics', 'Books', 'Clothing'][i % 3],
  }));
}

test('initial render of 1000 products completes within budget', () => {
  const renderTimes = [];
  const onRender = (id, phase, actualDuration) => {
    renderTimes.push({ id, phase, actualDuration });
  };

  const products = generateProducts(1000);
  render(<ProductTable products={products} onRenderCallback={onRender} />);

  const mountRender = renderTimes.find(r => r.phase === 'mount');
  expect(mountRender).toBeDefined();

  // Assert render time is within acceptable budget (adjust based on CI hardware)
  // This is a soft assertion — CI machines vary, so use generous budgets
  console.log(`Mount duration: ${mountRender.actualDuration.toFixed(2)}ms`);
  expect(mountRender.actualDuration).toBeLessThan(200); // 200ms budget
});

test('re-render with unchanged products is fast (memoization works)', () => {
  const renderTimes = [];
  const onRender = (id, phase, actualDuration) => {
    renderTimes.push({ id, phase, actualDuration });
  };

  const products = generateProducts(1000);
  const { rerender } = render(
    <ProductTable products={products} onRenderCallback={onRender} />
  );

  // Re-render with the SAME products array reference
  rerender(
    <ProductTable products={products} onRenderCallback={onRender} />
  );

  const updateRenders = renderTimes.filter(r => r.phase === 'update');

  if (updateRenders.length > 0) {
    // memo should prevent expensive re-renders
    const updateDuration = updateRenders[0].actualDuration;
    console.log(`Update duration: ${updateDuration.toFixed(2)}ms`);
    expect(updateDuration).toBeLessThan(10); // near-zero if memo works
  }
});

test('adding a single product does not re-render existing rows', () => {
  const renderCounts = { mount: 0, update: 0 };
  const onRender = (id, phase) => {
    renderCounts[phase] = (renderCounts[phase] || 0) + 1;
  };

  const products = generateProducts(100);
  const { rerender } = render(
    <ProductTable products={products} onRenderCallback={onRender} />
  );

  // Add one product (new array reference, but existing items unchanged)
  const updatedProducts = [
    ...products,
    { id: 100, name: 'New Product', price: 29.99, category: 'Books' },
  ];

  rerender(
    <ProductTable products={updatedProducts} onRenderCallback={onRender} />
  );

  // Should see 101 items rendered
  const rows = screen.getAllByRole('row');
  expect(rows).toHaveLength(102); // 101 data rows + 1 header row
});
```

**Key considerations:**
- **Performance tests are inherently flaky** on varying hardware. Use generous budgets and treat them as **canaries**, not hard gates.
- The `Profiler` only works in development mode (or with the profiler-enabled production build). Tests using jsdom run in a simulated environment, so absolute times differ from real browsers.
- For more precise measurements, use **Playwright** + Chrome DevTools Protocol to capture real browser performance traces.
- Use `React.memo`, `useMemo`, and `useCallback` and verify they work by asserting that update renders are significantly faster than mount renders.

---

### Q19. How do you implement visual regression testing with Storybook and Chromatic?

**Answer:**

Visual regression testing captures **screenshots** of your UI components and compares them pixel-by-pixel against approved baselines. This catches unintended visual changes — broken layouts, wrong colors, missing elements — that functional tests miss entirely.

**Storybook** renders components in isolation with various prop combinations (stories). **Chromatic** (by the Storybook team) captures screenshots of every story in a cloud-hosted real browser, diffs them against the baseline, and provides a review workflow for approving or rejecting changes.

**Setting up Storybook stories for visual testing:**

```jsx
// Button.stories.jsx
import { Button } from './Button';

export default {
  title: 'Components/Button',
  component: Button,
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'danger'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    disabled: { control: 'boolean' },
  },
};

const Template = (args) => <Button {...args} />;

// Each export becomes a story = a visual test case
export const Primary = Template.bind({});
Primary.args = { variant: 'primary', children: 'Primary Button' };

export const Secondary = Template.bind({});
Secondary.args = { variant: 'secondary', children: 'Secondary Button' };

export const Danger = Template.bind({});
Danger.args = { variant: 'danger', children: 'Delete Item' };

export const Disabled = Template.bind({});
Disabled.args = { variant: 'primary', children: 'Disabled', disabled: true };

export const Loading = Template.bind({});
Loading.args = { variant: 'primary', children: 'Saving...', isLoading: true };

// Complex states for visual regression
export const AllVariants = () => (
  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
    {['primary', 'secondary', 'danger'].map(variant =>
      ['sm', 'md', 'lg'].map(size => (
        <Button key={`${variant}-${size}`} variant={variant} size={size}>
          {variant} {size}
        </Button>
      ))
    )}
  </div>
);
```

**Chromatic integration:**

```bash
npm install --save-dev chromatic
```

```jsx
// package.json scripts
{
  "scripts": {
    "chromatic": "chromatic --project-token=<your-token>",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build"
  }
}
```

**CI/CD integration (GitHub Actions):**

```jsx
// .github/workflows/visual-regression.yml
name: Visual Regression

on: pull_request

jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Chromatic needs full git history

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Run Chromatic
        uses: chromaui/action@latest
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          exitOnceUploaded: true  # don't block CI; review in Chromatic UI
```

**Testing interaction states visually (using Storybook play functions):**

```jsx
// LoginForm.stories.jsx
import { within, userEvent } from '@storybook/testing-library';
import { expect } from '@storybook/jest';
import { LoginForm } from './LoginForm';

export default {
  title: 'Forms/LoginForm',
  component: LoginForm,
};

export const Empty = () => <LoginForm onSubmit={() => {}} />;

export const FilledOut = {
  render: () => <LoginForm onSubmit={() => {}} />,
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByLabelText(/email/i), 'alice@example.com');
    await userEvent.type(canvas.getByLabelText(/password/i), '••••••••');
  },
};

export const WithValidationErrors = {
  render: () => <LoginForm onSubmit={() => {}} />,
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    // Submit empty form to trigger validation
    await userEvent.click(canvas.getByRole('button', { name: /sign in/i }));
    // Chromatic captures the screenshot AFTER the play function runs
    // showing the validation error state
  },
};
```

**Visual regression workflow:**
1. Developer pushes a PR.
2. Chromatic builds Storybook and captures screenshots of every story.
3. Chromatic diffs against the baseline (last approved screenshots on the base branch).
4. If diffs are detected, Chromatic posts a status check on the PR with a link to review.
5. Reviewer approves intentional changes (new baseline) or requests fixes for unintentional changes.

**When to use visual regression vs. functional tests:**
- **Visual regression:** Layout, spacing, colors, typography, responsive breakpoints, dark/light mode, component states.
- **Functional tests (RTL):** User interactions, data flow, business logic, error handling.
- They complement each other — one catches logic bugs, the other catches visual bugs.

---

### Q20. How should you structure a production testing strategy using the unit, integration, and E2E testing pyramid?

**Answer:**

The **testing pyramid** (or "testing trophy" as Kent C. Dodds calls it) is a framework for distributing test effort across different layers to maximize confidence while minimizing cost and maintenance burden. For a React application, the recommended distribution is:

```
        /  E2E  \          ← Few, expensive, critical paths only
       /----------\
      / Integration \      ← Most tests live here (highest ROI)
     /----------------\
    /   Unit (Logic)    \  ← Pure functions, hooks, utilities
   /--------------------\
  /    Static Analysis    \ ← TypeScript, ESLint, Prettier (free confidence)
 /________________________\
```

**Layer-by-layer strategy for a production React app:**

**Layer 1: Static Analysis (foundation — runs on every keystroke/commit)**
```jsx
// eslint.config.js — catches bugs without running code
export default [
  {
    plugins: {
      'react-hooks': reactHooksPlugin,
      'jsx-a11y': jsxA11yPlugin,
    },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/anchor-is-valid': 'error',
    },
  },
];
// TypeScript catches type errors, ESLint catches patterns, Prettier catches formatting
```

**Layer 2: Unit Tests (fast, isolated, pure logic)**

```jsx
// Test utility functions, validators, reducers, formatters
// utils/formatCurrency.test.ts
import { formatCurrency } from './formatCurrency';

test.each([
  [0, '$0.00'],
  [9.99, '$9.99'],
  [1234.5, '$1,234.50'],
  [-49.99, '-$49.99'],
  [1000000, '$1,000,000.00'],
])('formatCurrency(%s) returns %s', (input, expected) => {
  expect(formatCurrency(input)).toBe(expected);
});

// Test custom hooks in isolation
// hooks/useLocalStorage.test.ts
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from './useLocalStorage';

test('reads initial value from localStorage', () => {
  localStorage.setItem('theme', JSON.stringify('dark'));
  const { result } = renderHook(() => useLocalStorage('theme', 'light'));
  expect(result.current[0]).toBe('dark');
});

test('writes to localStorage on update', () => {
  const { result } = renderHook(() => useLocalStorage('count', 0));
  act(() => result.current[1](42));
  expect(JSON.parse(localStorage.getItem('count'))).toBe(42);
});
```

**Layer 3: Integration Tests (the sweet spot — highest ROI)**

```jsx
// Test entire features/pages with real providers, mock only the network
// features/ProductCatalog.integration.test.jsx
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { renderApp } from '../test-utils'; // renders with all providers + router

test('user can search, filter, and add product to cart', async () => {
  const user = userEvent.setup();

  server.use(
    http.get('/api/products', ({ request }) => {
      const url = new URL(request.url);
      const search = url.searchParams.get('q') || '';
      const category = url.searchParams.get('category') || '';

      let products = [
        { id: 1, name: 'Mechanical Keyboard', price: 149, category: 'Electronics' },
        { id: 2, name: 'React Book', price: 39, category: 'Books' },
        { id: 3, name: 'USB Hub', price: 29, category: 'Electronics' },
      ];

      if (search) products = products.filter(p =>
        p.name.toLowerCase().includes(search.toLowerCase())
      );
      if (category) products = products.filter(p => p.category === category);

      return HttpResponse.json(products);
    })
  );

  renderApp({ route: '/products' });

  // Wait for products to load
  await screen.findByText('Mechanical Keyboard');
  expect(screen.getAllByRole('listitem')).toHaveLength(3);

  // Search for a product
  await user.type(screen.getByRole('searchbox'), 'keyboard');
  await screen.findByText('Mechanical Keyboard');
  expect(screen.queryByText('React Book')).not.toBeInTheDocument();

  // Add to cart
  await user.click(screen.getByRole('button', { name: /add to cart/i }));

  // Verify cart badge updates
  expect(screen.getByLabelText(/cart/i)).toHaveTextContent('1');
});
```

**Layer 4: E2E Tests (few, critical paths)**

```jsx
// e2e/critical-paths.spec.ts (Playwright)
import { test, expect } from '@playwright/test';

// Only test the most critical user journeys
test('complete purchase flow', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL('/dashboard');

  // Browse and add to cart
  await page.goto('/products');
  await page.getByRole('button', { name: /add.*keyboard.*cart/i }).click();

  // Checkout
  await page.goto('/checkout');
  await page.getByLabel('Card number').fill('4242424242424242');
  await page.getByLabel('Expiry').fill('12/27');
  await page.getByLabel('CVV').fill('123');
  await page.getByRole('button', { name: /place order/i }).click();

  // Confirmation
  await expect(page.getByText(/order confirmed/i)).toBeVisible();
});

test('password reset flow', async ({ page }) => {
  await page.goto('/forgot-password');
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByRole('button', { name: /send reset link/i }).click();
  await expect(page.getByText(/check your email/i)).toBeVisible();
});
```

**Distribution guidelines for a typical SaaS React app:**

| Layer | % of Tests | Speed | What to Test |
|---|---|---|---|
| Static (TS + ESLint) | N/A (always on) | Instant | Type errors, lint rules, a11y rules |
| Unit | ~20% | < 1s each | Pure functions, hooks, reducers, validators |
| Integration | ~60% | 1–5s each | Feature pages, user flows, error states |
| E2E | ~10% | 10–30s each | Login, checkout, signup, critical CRUD |
| Visual Regression | ~10% | Cloud-based | Component states, responsive layouts, themes |

**Key principles:**
1. **Integration tests give the most confidence per dollar.** A single integration test that renders a page, simulates a user flow, and verifies the outcome replaces dozens of unit tests.
2. **Push tests down the pyramid when possible.** If logic can be extracted to a pure function, unit test it. If it requires DOM rendering, integration test it. Only use E2E for flows that cross multiple pages or require real browser behavior.
3. **Every bug should become a test.** When a bug is found in production, write a test at the lowest pyramid level that reproduces it. This prevents regressions.
4. **Maintain test quality.** Delete flaky tests rather than skip them. A skipped test gives false confidence.
5. **Run fast tests on every commit, slow tests on merge.** Unit + integration in pre-commit/PR. E2E and visual regression on merge to main or nightly.

---
