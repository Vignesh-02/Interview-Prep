# Topic 7: Context API & Dependency Injection in React 18

## Introduction

React's **Context API** is a mechanism for passing data through the component tree without manually threading props at every level. In any non-trivial application, you inevitably have "global-ish" values — the current authenticated user, a UI theme, a locale string, feature flags — that dozens of deeply nested components need access to. Without Context, you'd resort to **prop drilling**: passing these values from parent to child to grandchild, through components that don't even use the data themselves. Context solves this by creating a broadcast channel: a Provider sits near the top of the tree, and any descendant can subscribe to that channel with `useContext`, no matter how deep it is. React 18 supports Context fully within its concurrent rendering model, and React 19 introduces a shorthand where `<Context>` itself acts as the provider, removing the need for `<Context.Provider>`.

A critical mental model shift is understanding that Context is **not** a state management solution — it is a **dependency injection** mechanism. Context itself doesn't hold state, trigger updates, or provide selectors. It simply makes a value available to a subtree. When you pair Context with `useState` or `useReducer`, *those hooks* manage the state, and Context merely distributes it. This distinction matters enormously for performance: every time the context value changes (by reference), **every** consumer re-renders, regardless of whether the specific piece of data they care about actually changed. This is why large-scale apps often split contexts, memoize values, or reach for dedicated state libraries like Zustand or Redux Toolkit when the number of consumers or update frequency grows.

Here is a minimal but complete illustration of creating, providing, and consuming context in React 18:

```jsx
import { createContext, useContext, useState } from 'react';

// 1. Create context with a sensible default
const ThemeContext = createContext('light');

// 2. Provider component that holds the actual state
function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');

  const toggleTheme = () =>
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// 3. Custom hook for consuming — enforces Provider presence
function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// 4. Any deeply nested component can consume without prop drilling
function Toolbar() {
  const { theme, toggleTheme } = useTheme();
  return (
    <header style={{ background: theme === 'dark' ? '#1a1a2e' : '#ffffff' }}>
      <button onClick={toggleTheme}>
        Switch to {theme === 'light' ? 'dark' : 'light'} mode
      </button>
    </header>
  );
}

// 5. App wires it together — Toolbar never receives theme as a prop
function App() {
  return (
    <ThemeProvider>
      <Toolbar />
      {/* hundreds of other components, all with access to theme */}
    </ThemeProvider>
  );
}
```

This pattern — `createContext` → Provider with state → custom `useXxx` hook → consumer components — is the backbone of every Context-based architecture. Every question below drills into a specific facet of this pattern, from beginner fundamentals through advanced production scenarios.

---

## Beginner Level (Q1–Q5)

---

### Q1. What is React Context and when should you use it?

**Answer:**

React Context is a built-in API that lets you share values across a component subtree without passing props explicitly at every level. It was re-introduced in its modern form in React 16.3 (`createContext` / `useContext`) and remains fully supported in React 18.

**When to use Context:**

1. **Theming** — light/dark mode, brand colors, spacing tokens.
2. **Authentication** — current user, tokens, roles.
3. **Locale / i18n** — language strings, date/number formatting.
4. **Feature flags** — toggling experimental features for subsets of users.
5. **Dependency injection** — providing a logger, analytics client, or API service so components don't import singletons directly.

**When NOT to use Context:**

- Frequently updating, fine-grained state (e.g., a text input that updates on every keystroke shared across many consumers) — this causes performance issues because every consumer re-renders on every change.
- State that is local to one component or a small subtree — `useState` or `useReducer` at the nearest common parent is simpler.
- Complex state with selectors, middleware, or devtools — use a dedicated state library.

```jsx
import { createContext, useContext } from 'react';

// Context for the current locale — changes infrequently, many components need it
const LocaleContext = createContext('en');

function LocaleProvider({ children, locale }) {
  return (
    <LocaleContext.Provider value={locale}>
      {children}
    </LocaleContext.Provider>
  );
}

function useLocale() {
  return useContext(LocaleContext);
}

// Deeply nested component consumes locale without prop drilling
function PriceDisplay({ amount }) {
  const locale = useLocale();

  const formatted = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: locale === 'en' ? 'USD' : 'EUR',
  }).format(amount);

  return <span>{formatted}</span>;
}

function App() {
  return (
    <LocaleProvider locale="en">
      <div>
        <h1>Product Page</h1>
        {/* PriceDisplay is 5 levels deep, but never receives locale as a prop */}
        <PriceDisplay amount={29.99} />
      </div>
    </LocaleProvider>
  );
}
```

The key insight: Context is ideal for data that is **read by many components** but **updated infrequently**. It is a distribution mechanism, not a state container.

---

### Q2. How do you create and provide a context using `createContext` and `Provider`?

**Answer:**

Creating and providing context is a two-step process:

1. **`createContext(defaultValue)`** — Creates a context object with an optional default value. The default is used only when a component calls `useContext` and there is no matching Provider above it in the tree.
2. **`<MyContext.Provider value={...}>`** — Wraps a subtree and supplies the current value. Any descendant calling `useContext(MyContext)` receives this value.

Important details:

- The `value` prop on Provider is the *only* way to pass data — there is no "setter" built into Context itself.
- You can nest multiple Providers of the same context; the nearest ancestor Provider wins.
- The default value passed to `createContext` should match the shape of what the Provider will supply, or be a sentinel like `undefined` / `null` so you can detect missing Providers.

```jsx
import { createContext, useContext, useState } from 'react';

// Step 1: Create with a default that matches the Provider's shape
const UserContext = createContext({
  user: null,
  login: () => {},
  logout: () => {},
});

// Step 2: Build a Provider component that wraps state logic
function UserProvider({ children }) {
  const [user, setUser] = useState(null);

  const login = async (credentials) => {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    const data = await res.json();
    setUser(data.user);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };

  return (
    <UserContext.Provider value={{ user, login, logout }}>
      {children}
    </UserContext.Provider>
  );
}

// Step 3: Consume in any descendant
function ProfileMenu() {
  const { user, logout } = useContext(UserContext);

  if (!user) return <button>Sign In</button>;

  return (
    <div>
      <span>Welcome, {user.name}</span>
      <button onClick={logout}>Log Out</button>
    </div>
  );
}

// Step 4: Wire in the app root
function App() {
  return (
    <UserProvider>
      <nav>
        <ProfileMenu />
      </nav>
      <main>{/* rest of the app */}</main>
    </UserProvider>
  );
}
```

The Provider acts as the boundary: everything inside the `<UserProvider>` subtree has access; everything outside falls back to the default value. In practice, you almost always wrap your entire app (or a major section) so that all routes and layouts have access to the context.

---

### Q3. How does `useContext` work, and how does it compare to the older Consumer pattern?

**Answer:**

`useContext(MyContext)` is a hook that subscribes the calling component to the nearest `MyContext.Provider` above it. Whenever the Provider's `value` changes, every component that calls `useContext(MyContext)` re-renders with the new value.

Before hooks (React < 16.8), you had to use the **render prop** pattern with `<MyContext.Consumer>`:

```jsx
import { createContext, useContext } from 'react';

const ThemeContext = createContext('light');

// ✅ Modern approach — useContext hook (React 16.8+)
function ModernButton() {
  const theme = useContext(ThemeContext);
  return (
    <button className={`btn-${theme}`}>
      Current theme: {theme}
    </button>
  );
}

// ❌ Legacy approach — Consumer render prop (pre-hooks)
function LegacyButton() {
  return (
    <ThemeContext.Consumer>
      {(theme) => (
        <button className={`btn-${theme}`}>
          Current theme: {theme}
        </button>
      )}
    </ThemeContext.Consumer>
  );
}

// Both produce identical output, but useContext is far more ergonomic
```

**Why `useContext` is superior:**

| Aspect | `useContext` | `Consumer` render prop |
|---|---|---|
| Readability | Clean, single line at top | Nested render function |
| Multiple contexts | Multiple `useContext` calls | Deeply nested Consumers |
| Access in logic | Available anywhere in the function body | Only inside the render callback |
| TypeScript | Automatic type inference | Requires manual typing of the render prop |

The only remaining use case for `<Consumer>` is if you need context inside a class component's `render()` without converting to a function component, or in very rare JSX-only patterns. In new code, always use `useContext`.

---

### Q4. What is prop drilling, and how does Context solve it?

**Answer:**

**Prop drilling** is the practice of passing data through multiple intermediate components that don't use the data themselves, just to get it to a deeply nested child that does. It's not inherently bad — for shallow trees or a small number of props, it's actually the simplest and most explicit approach. It becomes a problem when:

1. You have 5+ levels of components that merely forward props.
2. Adding a new piece of data requires editing every intermediate component.
3. Refactoring becomes brittle — renaming a prop means touching a dozen files.

```jsx
import { createContext, useContext, useState } from 'react';

// ❌ Prop drilling: every intermediate component must forward `user`
function App_Drilling() {
  const [user] = useState({ name: 'Alice', role: 'admin' });

  return <Layout user={user} />;
}

function Layout({ user }) {
  // Layout doesn't use `user` — it just passes it down
  return (
    <div className="layout">
      <Sidebar user={user} />
      <Content user={user} />
    </div>
  );
}

function Sidebar({ user }) {
  // Sidebar doesn't use `user` either
  return (
    <aside>
      <Navigation user={user} />
    </aside>
  );
}

function Navigation({ user }) {
  // Finally, the component that actually needs `user`
  return <span>Logged in as {user.name} ({user.role})</span>;
}

// ✅ Context: only the producer and the consumer know about `user`
const UserContext = createContext(null);

function App_Context() {
  const [user] = useState({ name: 'Alice', role: 'admin' });

  return (
    <UserContext.Provider value={user}>
      <Layout />
    </UserContext.Provider>
  );
}

function Layout_Clean() {
  // No user prop — Layout is blissfully unaware
  return (
    <div className="layout">
      <Sidebar_Clean />
      <Content />
    </div>
  );
}

function Sidebar_Clean() {
  return (
    <aside>
      <Navigation_Clean />
    </aside>
  );
}

function Navigation_Clean() {
  const user = useContext(UserContext);
  return <span>Logged in as {user.name} ({user.role})</span>;
}
```

**When prop drilling is still appropriate:**

- The data only passes through 1–2 levels.
- The intermediate components genuinely use the prop (not just forwarding).
- You want explicit data flow that's easy to trace in the code.

**Rule of thumb:** If you're adding a prop to a component *only* because its child needs it, that's a sign Context (or component composition) might be a better fit.

---

### Q5. What are default values in `createContext` and when are they actually used?

**Answer:**

The argument you pass to `createContext(defaultValue)` is the value returned by `useContext` when there is **no matching Provider** above the consuming component in the tree. This is the *only* situation where the default kicks in.

Common misconceptions:
- The default is **not** used when the Provider's `value` is `undefined` explicitly. If you write `<MyContext.Provider value={undefined}>`, consumers receive `undefined`, not the default.
- The default is **not** used as an initial value for the Provider — the Provider's `value` prop is always independent.

```jsx
import { createContext, useContext } from 'react';

// Default value: used when NO Provider wraps the consumer
const FeatureFlagContext = createContext({
  darkMode: false,
  newDashboard: false,
  betaFeatures: false,
});

function FeatureBanner() {
  const flags = useContext(FeatureFlagContext);
  // If no Provider exists above, flags === { darkMode: false, newDashboard: false, betaFeatures: false }
  // If a Provider exists, flags === whatever the Provider supplies
  return flags.newDashboard ? <p>Try our new dashboard!</p> : null;
}

// Scenario 1: No Provider — default value is used
function AppWithoutProvider() {
  return <FeatureBanner />; // flags will be the default object
}

// Scenario 2: Provider present — default is ignored
function AppWithProvider() {
  const flags = { darkMode: true, newDashboard: true, betaFeatures: false };
  return (
    <FeatureFlagContext.Provider value={flags}>
      <FeatureBanner /> {/* flags from Provider, not default */}
    </FeatureFlagContext.Provider>
  );
}
```

**Best practices for default values:**

1. **For library/reusable contexts** — provide a meaningful default so consumers work without a Provider (useful in Storybook, tests, or standalone usage).
2. **For app-level contexts** — use `undefined` or `null` as the default and throw in your custom hook if the Provider is missing. This catches wiring bugs early.

```jsx
const AuthContext = createContext(undefined);

function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error(
      'useAuth must be used within an <AuthProvider>. ' +
      'Wrap your component tree with <AuthProvider> in your app root.'
    );
  }
  return ctx;
}
```

This "fail-fast" pattern is the industry standard for application-level contexts.

---

## Intermediate Level (Q6–Q12)

---

### Q6. Why is Context a dependency injection mechanism and NOT a state management tool?

**Answer:**

This is one of the most important conceptual distinctions in React architecture. **Context does not manage state.** It has no built-in mechanism to:

- Store values (that's `useState` or `useReducer`).
- Compute derived data (that's `useMemo` or selectors).
- Handle side effects on state changes (that's `useEffect`).
- Provide middleware, devtools, or time-travel debugging.

Context is a **transport layer** — it makes a value available to a subtree without prop drilling. It is functionally equivalent to dependency injection in backend frameworks (Spring, .NET, NestJS): you declare "I need X" and the framework provides it, without the consumer knowing where X comes from.

```jsx
import { createContext, useContext, useState, useReducer } from 'react';

// --- The state management layer (useReducer) ---
const initialState = { items: [], total: 0 };

function cartReducer(state, action) {
  switch (action.type) {
    case 'ADD_ITEM': {
      const items = [...state.items, action.payload];
      return { items, total: items.reduce((sum, i) => sum + i.price, 0) };
    }
    case 'REMOVE_ITEM': {
      const items = state.items.filter((i) => i.id !== action.payload);
      return { items, total: items.reduce((sum, i) => sum + i.price, 0) };
    }
    case 'CLEAR':
      return initialState;
    default:
      return state;
  }
}

// --- The dependency injection layer (Context) ---
const CartContext = createContext(undefined);

function CartProvider({ children }) {
  // State lives HERE — in the hook, not in Context
  const [state, dispatch] = useReducer(cartReducer, initialState);

  return (
    <CartContext.Provider value={{ state, dispatch }}>
      {children}
    </CartContext.Provider>
  );
}

function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
}

// --- Consumer doesn't know or care how state is managed ---
function CartSummary() {
  const { state, dispatch } = useCart();

  return (
    <div>
      <p>{state.items.length} items — ${state.total.toFixed(2)}</p>
      <button onClick={() => dispatch({ type: 'CLEAR' })}>Clear Cart</button>
    </div>
  );
}
```

**Why this distinction matters in production:**

| Concern | Context provides | State library (Zustand/Redux) provides |
|---|---|---|
| Broadcasting a value | Yes | Yes |
| Selective subscriptions | No (all consumers re-render) | Yes (selectors) |
| Middleware / side effects | No | Yes |
| Devtools / time-travel | No | Yes |
| State persistence | No | Yes (plugins) |
| Performance at scale | Degrades with many consumers | Optimized with selectors |

When someone says "I use Context for state management," what they usually mean is "I use `useState`/`useReducer` for state management and Context to distribute it." The distribution is Context's job; the management is the hook's job.

---

### Q7. What is the performance pitfall of Context, and why does every consumer re-render when the value changes?

**Answer:**

When a Context Provider's `value` changes (by reference — `Object.is` comparison), React marks **every** component that calls `useContext(ThatContext)` as needing a re-render. There is no built-in selector or "bail out if my slice didn't change" mechanism. This is fundamentally different from Redux or Zustand, where you can subscribe to a specific slice of state.

This means if your context value is an object with 10 fields, and only 1 field changes, all consumers re-render — even those that only read one of the other 9 unchanged fields.

```jsx
import { createContext, useContext, useState, memo } from 'react';

const AppContext = createContext(undefined);

function AppProvider({ children }) {
  const [user, setUser] = useState({ name: 'Alice' });
  const [theme, setTheme] = useState('light');
  const [notifications, setNotifications] = useState(0);

  // ❌ BAD: Single object context with everything
  // Every keystroke in notifications counter re-renders Toolbar AND UserMenu
  const value = { user, setUser, theme, setTheme, notifications, setNotifications };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// This component only cares about `theme`
const Toolbar = memo(function Toolbar() {
  const { theme } = useContext(AppContext);
  console.log('Toolbar rendered'); // Fires even when only notifications change!
  return <header className={theme}>Toolbar</header>;
});

// This component only cares about `user`
const UserMenu = memo(function UserMenu() {
  const { user } = useContext(AppContext);
  console.log('UserMenu rendered'); // Fires even when only theme changes!
  return <span>{user.name}</span>;
});

// This component updates notifications frequently
function NotificationBell() {
  const { notifications, setNotifications } = useContext(AppContext);

  return (
    <button onClick={() => setNotifications((n) => n + 1)}>
      🔔 {notifications}
    </button>
  );
}

function App() {
  return (
    <AppProvider>
      <Toolbar />
      <UserMenu />
      <NotificationBell />
    </AppProvider>
  );
}
```

**Why `memo` doesn't help here:**

`React.memo` prevents re-renders caused by parent re-renders with unchanged props. But `useContext` **bypasses** `memo` — when the context value changes, the component re-renders regardless of memoization. This is by design: context is a subscription, and React guarantees subscribers see the latest value.

**The fix** is covered in Q8 (splitting contexts) and Q9 (memoizing values).

---

### Q8. How do you optimize Context by splitting it into multiple smaller contexts?

**Answer:**

The most effective optimization is to separate values that change at different rates or are consumed by different components into **distinct contexts**. This way, a change in one context only re-renders the consumers of that specific context.

The common splits are:

1. **State vs. Dispatch** — State changes often; dispatch functions are stable references.
2. **Domain boundaries** — Theme, Auth, Locale, and Notifications are independent concerns.
3. **Read vs. Write** — Components that only trigger actions don't need the current state.

```jsx
import { createContext, useContext, useReducer, useMemo } from 'react';

// Split 1: Separate state from dispatch
const CartStateContext = createContext(undefined);
const CartDispatchContext = createContext(undefined);

function cartReducer(state, action) {
  switch (action.type) {
    case 'ADD_ITEM':
      return { ...state, items: [...state.items, action.payload] };
    case 'REMOVE_ITEM':
      return { ...state, items: state.items.filter((i) => i.id !== action.payload) };
    default:
      return state;
  }
}

function CartProvider({ children }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [] });

  // dispatch is already a stable reference from useReducer — no memo needed
  return (
    <CartDispatchContext.Provider value={dispatch}>
      <CartStateContext.Provider value={state}>
        {children}
      </CartStateContext.Provider>
    </CartDispatchContext.Provider>
  );
}

// Components that only ADD items don't re-render when the cart list changes
function useCartDispatch() {
  const ctx = useContext(CartDispatchContext);
  if (!ctx) throw new Error('useCartDispatch must be within CartProvider');
  return ctx;
}

// Components that DISPLAY the cart re-render only when state changes
function useCartState() {
  const ctx = useContext(CartStateContext);
  if (ctx === undefined) throw new Error('useCartState must be within CartProvider');
  return ctx;
}

// ✅ This component never re-renders when items change — it only dispatches
function AddToCartButton({ product }) {
  const dispatch = useCartDispatch();
  return (
    <button onClick={() => dispatch({ type: 'ADD_ITEM', payload: product })}>
      Add to Cart
    </button>
  );
}

// ✅ This component re-renders only when items change — it doesn't dispatch
function CartBadge() {
  const { items } = useCartState();
  return <span className="badge">{items.length}</span>;
}

// Split 2: Multiple domain contexts at the app level
const ThemeContext = createContext('light');
const AuthContext = createContext(null);
const LocaleContext = createContext('en');

function AppProviders({ children }) {
  return (
    <AuthProvider>
      <ThemeProvider>
        <LocaleProvider>
          <CartProvider>
            {children}
          </CartProvider>
        </LocaleProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
```

**Production rule of thumb:** If a context value is an object with more than 2-3 fields that update independently, split it. The small overhead of extra Providers is negligible compared to unnecessary re-renders of dozens of consumers.

---

### Q9. How do you memoize context values to prevent unnecessary re-renders?

**Answer:**

Every time a Provider's parent re-renders, a new `value` object is created (even if its contents are identical). Since Context uses reference equality (`Object.is`), a new object reference triggers all consumers to re-render. The fix is `useMemo`.

```jsx
import { createContext, useContext, useState, useMemo, useCallback } from 'react';

const ThemeContext = createContext(undefined);

// ❌ BAD: New object reference on every render of ThemeProvider
function ThemeProvider_Bad({ children }) {
  const [mode, setMode] = useState('light');
  const [fontSize, setFontSize] = useState(16);

  // This creates a NEW object every render → all consumers re-render
  return (
    <ThemeContext.Provider value={{ mode, fontSize, setMode, setFontSize }}>
      {children}
    </ThemeContext.Provider>
  );
}

// ✅ GOOD: Memoized value — only creates a new object when dependencies change
function ThemeProvider({ children }) {
  const [mode, setMode] = useState('light');
  const [fontSize, setFontSize] = useState(16);

  // Stabilize callback references
  const toggleMode = useCallback(() => {
    setMode((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  const increaseFontSize = useCallback(() => {
    setFontSize((prev) => Math.min(prev + 2, 24));
  }, []);

  // Memoize the entire value object
  const value = useMemo(
    () => ({ mode, fontSize, toggleMode, increaseFontSize }),
    [mode, fontSize, toggleMode, increaseFontSize]
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

// Consumer: only re-renders when mode or fontSize actually change
function ThemeDisplay() {
  const { mode, fontSize } = useTheme();
  return (
    <div style={{ fontSize }}>
      Current theme: {mode}, Font size: {fontSize}px
    </div>
  );
}

// Consumer: has stable callback reference, won't cause child re-renders
function ThemeControls() {
  const { toggleMode, increaseFontSize } = useTheme();
  return (
    <div>
      <button onClick={toggleMode}>Toggle Mode</button>
      <button onClick={increaseFontSize}>Increase Font</button>
    </div>
  );
}
```

**When memoization matters:**

- The Provider component re-renders frequently (e.g., it's near the top of a tree that re-renders on navigation).
- You have many consumers (10+).
- The context value is an object or array (primitives like strings/numbers are compared by value, so memoization is unnecessary).

**When memoization is overkill:**

- The Provider only re-renders when its own state changes (which means the value actually *did* change).
- You have very few consumers.

In most production apps, memoizing context values is a good default — it's cheap insurance against accidental re-renders.

---

### Q10. How do you combine Context with `useReducer` to build a mini Redux pattern?

**Answer:**

Pairing `useReducer` with Context gives you a Redux-like architecture without any external dependencies: a single state object, a dispatch function, typed actions, and predictable state transitions. This pattern is excellent for medium-complexity state that doesn't need devtools or middleware.

```jsx
import { createContext, useContext, useReducer, useMemo } from 'react';

// 1. Define types of actions and state shape
const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  FETCH_SUCCESS: 'FETCH_SUCCESS',
  FETCH_ERROR: 'FETCH_ERROR',
  ADD_TODO: 'ADD_TODO',
  TOGGLE_TODO: 'TOGGLE_TODO',
  DELETE_TODO: 'DELETE_TODO',
  SET_FILTER: 'SET_FILTER',
};

const initialState = {
  todos: [],
  filter: 'all', // 'all' | 'active' | 'completed'
  loading: false,
  error: null,
};

// 2. Pure reducer function — easy to test in isolation
function todoReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, loading: true, error: null };

    case ACTIONS.FETCH_SUCCESS:
      return { ...state, loading: false, todos: action.payload };

    case ACTIONS.FETCH_ERROR:
      return { ...state, loading: false, error: action.payload };

    case ACTIONS.ADD_TODO:
      return {
        ...state,
        todos: [...state.todos, {
          id: crypto.randomUUID(),
          text: action.payload,
          completed: false,
          createdAt: Date.now(),
        }],
      };

    case ACTIONS.TOGGLE_TODO:
      return {
        ...state,
        todos: state.todos.map((t) =>
          t.id === action.payload ? { ...t, completed: !t.completed } : t
        ),
      };

    case ACTIONS.DELETE_TODO:
      return {
        ...state,
        todos: state.todos.filter((t) => t.id !== action.payload),
      };

    case ACTIONS.SET_FILTER:
      return { ...state, filter: action.payload };

    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

// 3. Split contexts for performance (state vs dispatch)
const TodoStateContext = createContext(undefined);
const TodoDispatchContext = createContext(undefined);

function TodoProvider({ children }) {
  const [state, dispatch] = useReducer(todoReducer, initialState);

  return (
    <TodoDispatchContext.Provider value={dispatch}>
      <TodoStateContext.Provider value={state}>
        {children}
      </TodoStateContext.Provider>
    </TodoDispatchContext.Provider>
  );
}

function useTodoState() {
  const ctx = useContext(TodoStateContext);
  if (ctx === undefined) throw new Error('useTodoState requires TodoProvider');
  return ctx;
}

function useTodoDispatch() {
  const ctx = useContext(TodoDispatchContext);
  if (!ctx) throw new Error('useTodoDispatch requires TodoProvider');
  return ctx;
}

// 4. Derived state via useMemo (like Redux selectors)
function useFilteredTodos() {
  const { todos, filter } = useTodoState();

  return useMemo(() => {
    switch (filter) {
      case 'active':
        return todos.filter((t) => !t.completed);
      case 'completed':
        return todos.filter((t) => t.completed);
      default:
        return todos;
    }
  }, [todos, filter]);
}

// 5. Components that resemble a Redux-connected component
function TodoList() {
  const filteredTodos = useFilteredTodos();
  const dispatch = useTodoDispatch();

  if (filteredTodos.length === 0) return <p>No todos yet.</p>;

  return (
    <ul>
      {filteredTodos.map((todo) => (
        <li key={todo.id}>
          <label>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => dispatch({ type: ACTIONS.TOGGLE_TODO, payload: todo.id })}
            />
            <span style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}>
              {todo.text}
            </span>
          </label>
          <button onClick={() => dispatch({ type: ACTIONS.DELETE_TODO, payload: todo.id })}>
            ×
          </button>
        </li>
      ))}
    </ul>
  );
}

function AddTodo() {
  const dispatch = useTodoDispatch();

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = e.target.elements.todo.value.trim();
    if (!text) return;
    dispatch({ type: ACTIONS.ADD_TODO, payload: text });
    e.target.reset();
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="todo" placeholder="What needs to be done?" autoFocus />
      <button type="submit">Add</button>
    </form>
  );
}
```

This pattern scales well for a single domain (todos, cart, form wizard). When you need multiple domains with cross-cutting concerns, or you need middleware (logging, analytics, persistence), that's when you graduate to Zustand or Redux Toolkit.

---

### Q11. How do you compose multiple contexts in a real application (auth + theme + locale)?

**Answer:**

Production React apps commonly have 3–6 context Providers wrapping the app root. Composing them is straightforward: nest them. Since each is independent, order rarely matters (unless one Provider consumes another). To keep `App.jsx` clean, create a `Providers` wrapper.

```jsx
import { createContext, useContext, useState, useReducer, useMemo, useCallback } from 'react';

// --- Auth Context ---
const AuthContext = createContext(undefined);

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));

  const login = useCallback(async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    setUser(data.user);
    setToken(data.token);
    localStorage.setItem('token', data.token);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  }, []);

  const value = useMemo(
    () => ({ user, token, login, logout, isAuthenticated: !!token }),
    [user, token, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth requires AuthProvider');
  return ctx;
}

// --- Theme Context ---
const ThemeContext = createContext(undefined);

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
  });

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', next);
      return next;
    });
  }, []);

  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme requires ThemeProvider');
  return ctx;
}

// --- Locale Context ---
const LocaleContext = createContext(undefined);

function LocaleProvider({ children }) {
  const [locale, setLocale] = useState('en');

  const value = useMemo(() => ({ locale, setLocale }), [locale]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error('useLocale requires LocaleProvider');
  return ctx;
}

// --- Compose all Providers cleanly ---
function AppProviders({ children }) {
  return (
    <AuthProvider>
      <ThemeProvider>
        <LocaleProvider>
          {children}
        </LocaleProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

// --- Optional: Generic compose utility to avoid deep nesting ---
function composeProviders(...providers) {
  return ({ children }) =>
    providers.reduceRight(
      (acc, Provider) => <Provider>{acc}</Provider>,
      children
    );
}

const AllProviders = composeProviders(AuthProvider, ThemeProvider, LocaleProvider);

// --- Usage in components: consume any combination of contexts ---
function DashboardHeader() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { locale, setLocale } = useLocale();

  return (
    <header className={`header-${theme}`}>
      <span>
        {locale === 'en' ? `Welcome, ${user?.name}` : `Bienvenue, ${user?.name}`}
      </span>
      <div>
        <button onClick={toggleTheme}>
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
        <select value={locale} onChange={(e) => setLocale(e.target.value)}>
          <option value="en">English</option>
          <option value="fr">Français</option>
          <option value="es">Español</option>
        </select>
        <button onClick={logout}>Log Out</button>
      </div>
    </header>
  );
}

// App root
function App() {
  return (
    <AppProviders>
      <DashboardHeader />
      <main>{/* Routes, pages, etc. */}</main>
    </AppProviders>
  );
}
```

**Key considerations:**

- **Order matters when Providers depend on each other.** If `ThemeProvider` needs the current user to determine the default theme, it must be nested inside `AuthProvider`.
- **The `composeProviders` utility** is a pattern seen in production apps to avoid the "Provider pyramid of doom."
- **Each context remains independently testable** — in tests, you only wrap the Providers the component actually needs.

---

### Q12. How do you test components that consume Context?

**Answer:**

The key principle is: **wrap the component under test with the necessary Provider(s) and pass controlled values.** This lets you test the component in isolation without needing the real state management logic.

```jsx
// useAuth.js — the hook and context
import { createContext, useContext, useMemo, useState, useCallback } from 'react';

const AuthContext = createContext(undefined);

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const login = useCallback(async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    setUser(data.user);
  }, []);

  const logout = useCallback(() => setUser(null), []);

  const value = useMemo(
    () => ({ user, login, logout, isAuthenticated: !!user }),
    [user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth requires AuthProvider');
  return ctx;
}
```

```jsx
// UserGreeting.jsx — the component under test
function UserGreeting() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <p>Please log in to continue.</p>;
  }

  return (
    <div>
      <h2>Hello, {user.name}!</h2>
      <p>Role: {user.role}</p>
      <button onClick={logout}>Sign Out</button>
    </div>
  );
}
```

```jsx
// UserGreeting.test.jsx — testing with controlled context values
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';

// Technique 1: Create a test wrapper that provides a controlled value
function renderWithAuth(ui, { authValue } = {}) {
  const defaultValue = {
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
    isAuthenticated: false,
    ...authValue,
  };

  return render(
    <AuthContext.Provider value={defaultValue}>
      {ui}
    </AuthContext.Provider>
  );
}

describe('UserGreeting', () => {
  test('shows login prompt when not authenticated', () => {
    renderWithAuth(<UserGreeting />);
    expect(screen.getByText('Please log in to continue.')).toBeInTheDocument();
  });

  test('shows user info when authenticated', () => {
    renderWithAuth(<UserGreeting />, {
      authValue: {
        user: { name: 'Alice', role: 'Admin' },
        isAuthenticated: true,
      },
    });

    expect(screen.getByText('Hello, Alice!')).toBeInTheDocument();
    expect(screen.getByText('Role: Admin')).toBeInTheDocument();
  });

  test('calls logout when Sign Out is clicked', () => {
    const mockLogout = vi.fn();

    renderWithAuth(<UserGreeting />, {
      authValue: {
        user: { name: 'Alice', role: 'Admin' },
        isAuthenticated: true,
        logout: mockLogout,
      },
    });

    fireEvent.click(screen.getByText('Sign Out'));
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  test('throws error when rendered without AuthProvider', () => {
    // Suppress console.error for the expected error
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<UserGreeting />)).toThrow(
      'useAuth requires AuthProvider'
    );

    consoleSpy.mockRestore();
  });
});

// Technique 2: Reusable test utility for multiple contexts
function renderWithProviders(ui, {
  authValue = {},
  themeValue = { theme: 'light', toggleTheme: vi.fn() },
} = {}) {
  const defaultAuth = {
    user: null, login: vi.fn(), logout: vi.fn(), isAuthenticated: false,
    ...authValue,
  };

  return render(
    <AuthContext.Provider value={defaultAuth}>
      <ThemeContext.Provider value={themeValue}>
        {ui}
      </ThemeContext.Provider>
    </AuthContext.Provider>
  );
}
```

**Testing best practices:**

1. **Never mock `useContext` directly** — always wrap with a Provider carrying controlled values.
2. **Create reusable `renderWith*` helpers** — reduces boilerplate across test files.
3. **Test the Provider itself separately** — verify that state transitions (login, logout) produce the expected context values.
4. **Test the missing-Provider error** — confirm your custom hook throws a helpful message.

---

## Advanced Level (Q13–Q20)

---

### Q13. What is the context selector pattern and how does it avoid unnecessary re-renders?

**Answer:**

React Context has no built-in selector support — when the value changes, all consumers re-render. The **context selector pattern** is a workaround that gives consumers the ability to subscribe to a *slice* of the context value and only re-render when that slice changes.

There are two primary approaches:

**Approach 1: `use-context-selector` library** (most popular, used by Jotai and others internally)

```jsx
import { createContext, useContextSelector } from 'use-context-selector';
import { useState, useCallback } from 'react';

// Note: uses the library's createContext, not React's
const AppContext = createContext(null);

function AppProvider({ children }) {
  const [user, setUser] = useState({ name: 'Alice', role: 'admin' });
  const [theme, setTheme] = useState('light');
  const [notifications, setNotifications] = useState(0);

  return (
    <AppContext.Provider value={{ user, setUser, theme, setTheme, notifications, setNotifications }}>
      {children}
    </AppContext.Provider>
  );
}

// ✅ Only re-renders when `theme` changes — ignores user and notifications
function Toolbar() {
  const theme = useContextSelector(AppContext, (ctx) => ctx.theme);
  console.log('Toolbar rendered');
  return <header className={theme}>Toolbar</header>;
}

// ✅ Only re-renders when `user.name` changes
function UserBadge() {
  const userName = useContextSelector(AppContext, (ctx) => ctx.user.name);
  console.log('UserBadge rendered');
  return <span>{userName}</span>;
}

// ✅ Only re-renders when `notifications` changes
function NotificationBell() {
  const notifications = useContextSelector(AppContext, (ctx) => ctx.notifications);
  const setNotifications = useContextSelector(AppContext, (ctx) => ctx.setNotifications);

  return (
    <button onClick={() => setNotifications((n) => n + 1)}>
      Notifications: {notifications}
    </button>
  );
}
```

**Approach 2: Manual selector with `useSyncExternalStore` (no library needed)**

```jsx
import { useRef, useCallback, useSyncExternalStore, createContext, useContext } from 'react';

function createSelectableContext() {
  const Context = createContext(null);

  function Provider({ value, children }) {
    const storeRef = useRef({ value, listeners: new Set() });
    storeRef.current.value = value;

    const subscribe = useCallback((listener) => {
      storeRef.current.listeners.add(listener);
      return () => storeRef.current.listeners.delete(listener);
    }, []);

    // Notify subscribers when value changes
    const prevValue = useRef(value);
    if (!Object.is(prevValue.current, value)) {
      prevValue.current = value;
      storeRef.current.listeners.forEach((l) => l());
    }

    return (
      <Context.Provider value={{ subscribe, getSnapshot: () => storeRef.current.value }}>
        {children}
      </Context.Provider>
    );
  }

  function useSelector(selector) {
    const { subscribe, getSnapshot } = useContext(Context);

    return useSyncExternalStore(
      subscribe,
      () => selector(getSnapshot()),
    );
  }

  return { Provider, useSelector };
}

// Usage
const { Provider: AppProvider, useSelector: useAppSelector } = createSelectableContext();

function ThemeToggle() {
  // Only re-renders when the selected `theme` value changes
  const theme = useAppSelector((state) => state.theme);
  return <button>{theme}</button>;
}
```

**Trade-offs:**

| Approach | Pros | Cons |
|---|---|---|
| Split contexts (Q8) | Zero dependencies, idiomatic React | More boilerplate, more Providers |
| `use-context-selector` | Ergonomic, minimal code changes | External dependency, uses internal React APIs |
| `useSyncExternalStore` | No external dependency, React-approved API | More complex implementation |
| Use Zustand/Redux | Battle-tested, devtools, middleware | External dependency, more concepts |

For most apps, **splitting contexts** is the recommended approach. Reach for selectors only when you have a single large context that can't easily be split.

---

### Q14. How do you build a complete theme system with Context?

**Answer:**

A production theme system goes beyond toggling light/dark. It manages CSS variables, persists user preference, respects OS-level preference, and provides type-safe theme tokens to components.

```jsx
import { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';

// 1. Define theme tokens
const themes = {
  light: {
    mode: 'light',
    colors: {
      background: '#ffffff',
      surface: '#f5f5f5',
      text: '#1a1a2e',
      textSecondary: '#666666',
      primary: '#3b82f6',
      primaryHover: '#2563eb',
      danger: '#ef4444',
      border: '#e2e8f0',
    },
    shadows: {
      sm: '0 1px 2px rgba(0,0,0,0.05)',
      md: '0 4px 6px rgba(0,0,0,0.07)',
      lg: '0 10px 15px rgba(0,0,0,0.1)',
    },
    spacing: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px' },
    borderRadius: { sm: '4px', md: '8px', lg: '16px', full: '9999px' },
  },
  dark: {
    mode: 'dark',
    colors: {
      background: '#0f0f23',
      surface: '#1a1a2e',
      text: '#e2e8f0',
      textSecondary: '#94a3b8',
      primary: '#60a5fa',
      primaryHover: '#93c5fd',
      danger: '#f87171',
      border: '#334155',
    },
    shadows: {
      sm: '0 1px 2px rgba(0,0,0,0.3)',
      md: '0 4px 6px rgba(0,0,0,0.4)',
      lg: '0 10px 15px rgba(0,0,0,0.5)',
    },
    spacing: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px' },
    borderRadius: { sm: '4px', md: '8px', lg: '16px', full: '9999px' },
  },
};

// 2. Context for theme
const ThemeContext = createContext(undefined);

function getInitialMode() {
  // Priority: localStorage > OS preference > default
  const stored = localStorage.getItem('theme-mode');
  if (stored === 'light' || stored === 'dark') return stored;

  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) return 'dark';
  return 'light';
}

function ThemeProvider({ children }) {
  const [mode, setMode] = useState(getInitialMode);

  // Sync CSS custom properties with the DOM
  useEffect(() => {
    const theme = themes[mode];
    const root = document.documentElement;

    Object.entries(theme.colors).forEach(([key, val]) => {
      root.style.setProperty(`--color-${key}`, val);
    });
    Object.entries(theme.shadows).forEach(([key, val]) => {
      root.style.setProperty(`--shadow-${key}`, val);
    });

    root.setAttribute('data-theme', mode);
    localStorage.setItem('theme-mode', mode);
  }, [mode]);

  // Listen for OS-level theme changes
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => {
      const stored = localStorage.getItem('theme-mode');
      if (!stored) setMode(e.matches ? 'dark' : 'light');
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const toggleTheme = useCallback(() => {
    setMode((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  const value = useMemo(
    () => ({
      mode,
      theme: themes[mode],
      toggleTheme,
      setMode,
    }),
    [mode, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within <ThemeProvider>');
  return ctx;
}

// 3. Components consuming theme tokens
function Card({ title, children }) {
  const { theme } = useTheme();

  return (
    <div
      style={{
        background: theme.colors.surface,
        color: theme.colors.text,
        borderRadius: theme.borderRadius.md,
        padding: theme.spacing.lg,
        boxShadow: theme.shadows.md,
        border: `1px solid ${theme.colors.border}`,
      }}
    >
      <h3 style={{ marginBottom: theme.spacing.sm }}>{title}</h3>
      {children}
    </div>
  );
}

function ThemeToggle() {
  const { mode, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${mode === 'light' ? 'dark' : 'light'} mode`}
    >
      {mode === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
    </button>
  );
}

function App() {
  return (
    <ThemeProvider>
      <ThemeToggle />
      <Card title="Dashboard">
        <p>Theme-aware content goes here.</p>
      </Card>
    </ThemeProvider>
  );
}
```

This theme system handles: token-based design, CSS variable syncing, OS preference detection, localStorage persistence, and provides a type-safe theme object to all consumers.

---

### Q15. How does Context enable dependency injection for testability?

**Answer:**

Dependency injection (DI) means a component declares *what* it needs (an interface) but doesn't decide *where* it comes from. Context is React's native DI mechanism. Instead of importing a concrete module (API client, analytics SDK, logger), you inject it via Context. This makes components testable because you can swap in mocks without module-level mocking hacks.

```jsx
import { createContext, useContext, useMemo } from 'react';

// 1. Define the "interface" — what services are available
const ServicesContext = createContext(undefined);

// 2. Production implementations
const productionServices = {
  api: {
    get: (url) => fetch(url).then((r) => r.json()),
    post: (url, body) =>
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then((r) => r.json()),
  },
  analytics: {
    track: (event, props) => {
      window.gtag?.('event', event, props);
      window.mixpanel?.track(event, props);
    },
    page: (name) => {
      window.gtag?.('event', 'page_view', { page_title: name });
    },
  },
  logger: {
    info: (...args) => console.log('[INFO]', ...args),
    warn: (...args) => console.warn('[WARN]', ...args),
    error: (...args) => {
      console.error('[ERROR]', ...args);
      // Send to Sentry in production
      window.Sentry?.captureException(args[0]);
    },
  },
  storage: {
    get: (key) => JSON.parse(localStorage.getItem(key)),
    set: (key, value) => localStorage.setItem(key, JSON.stringify(value)),
    remove: (key) => localStorage.removeItem(key),
  },
};

function ServicesProvider({ children, overrides = {} }) {
  const services = useMemo(
    () => ({ ...productionServices, ...overrides }),
    [overrides]
  );

  return (
    <ServicesContext.Provider value={services}>
      {children}
    </ServicesContext.Provider>
  );
}

function useServices() {
  const ctx = useContext(ServicesContext);
  if (!ctx) throw new Error('useServices requires ServicesProvider');
  return ctx;
}

// Convenience hooks
function useApi() { return useServices().api; }
function useAnalytics() { return useServices().analytics; }
function useLogger() { return useServices().logger; }

// 3. Component uses injected dependencies — no direct imports
function ProductList() {
  const api = useApi();
  const analytics = useAnalytics();
  const logger = useLogger();
  const [products, setProducts] = useState([]);

  useEffect(() => {
    api.get('/api/products')
      .then((data) => {
        setProducts(data);
        analytics.track('products_loaded', { count: data.length });
      })
      .catch((err) => {
        logger.error(err);
      });
  }, [api, analytics, logger]);

  return (
    <ul>
      {products.map((p) => (
        <li key={p.id}>{p.name} — ${p.price}</li>
      ))}
    </ul>
  );
}

// 4. In tests — inject mocks with zero module mocking
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

const mockServices = {
  api: {
    get: vi.fn().mockResolvedValue([
      { id: 1, name: 'Widget', price: 9.99 },
      { id: 2, name: 'Gadget', price: 19.99 },
    ]),
    post: vi.fn(),
  },
  analytics: { track: vi.fn(), page: vi.fn() },
  logger: { info: vi.fn(), warn: vi.fn(), error: vi.fn() },
  storage: { get: vi.fn(), set: vi.fn(), remove: vi.fn() },
};

test('ProductList fetches and displays products', async () => {
  render(
    <ServicesProvider overrides={mockServices}>
      <ProductList />
    </ServicesProvider>
  );

  await waitFor(() => {
    expect(screen.getByText('Widget — $9.99')).toBeInTheDocument();
    expect(screen.getByText('Gadget — $19.99')).toBeInTheDocument();
  });

  expect(mockServices.api.get).toHaveBeenCalledWith('/api/products');
  expect(mockServices.analytics.track).toHaveBeenCalledWith('products_loaded', { count: 2 });
});

// 5. In Storybook — inject different scenarios
export const WithProducts = () => (
  <ServicesProvider overrides={{ api: { get: () => Promise.resolve(mockProducts) } }}>
    <ProductList />
  </ServicesProvider>
);

export const WithError = () => (
  <ServicesProvider overrides={{ api: { get: () => Promise.reject(new Error('Network error')) } }}>
    <ProductList />
  </ServicesProvider>
);
```

**Why this is superior to module mocking:**

- **No `vi.mock()` or `jest.mock()` calls** — tests are simpler and more deterministic.
- **Multiple scenarios in one test file** — just pass different overrides.
- **Storybook-friendly** — each story injects a different service implementation.
- **Framework-agnostic logic** — the services object can be used outside React; Context is just the delivery mechanism.

---

### Q16. When should you stop using Context and reach for Zustand, Redux, or another state library?

**Answer:**

Context is not infinitely scalable. Here are concrete signals that you've outgrown it:

1. **You have 20+ consumers of a single context** and the value changes frequently (every few seconds or on user interaction) — consumers re-render in a cascade.
2. **You need selectors** — components consume slices of state, and re-rendering all of them on every change is wasteful.
3. **You need middleware** — logging, analytics, persistence, undo/redo, optimistic updates.
4. **You need devtools** — time-travel debugging, state inspection, action history.
5. **You have cross-cutting state** — multiple unrelated components read and write the same global state, and coordinating via multiple contexts becomes unwieldy.
6. **Server-side state** — if your "state" is really server data (lists of entities, pagination, caching, background refresh), you need React Query or SWR, not Context.

```jsx
// Scenario: A real-time dashboard with frequently updating metrics

// ❌ Context approach — EVERY metric consumer re-renders on ANY metric change
import { createContext, useContext, useState, useEffect } from 'react';

const MetricsContext = createContext(undefined);

function MetricsProvider({ children }) {
  const [metrics, setMetrics] = useState({
    cpu: 0, memory: 0, requests: 0, errors: 0, latency: 0,
  });

  useEffect(() => {
    const ws = new WebSocket('wss://api.example.com/metrics');
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setMetrics((prev) => ({ ...prev, ...data }));
    };
    return () => ws.close();
  }, []);

  return (
    <MetricsContext.Provider value={metrics}>
      {children}
    </MetricsContext.Provider>
  );
}

// These ALL re-render every time ANY metric changes (WebSocket fires ~1/sec)
function CpuGauge() {
  const { cpu } = useContext(MetricsContext); // Re-renders when `memory` changes too!
  return <div>CPU: {cpu}%</div>;
}

// ✅ Zustand approach — each component subscribes to its own slice
import { create } from 'zustand';

const useMetricsStore = create((set) => ({
  cpu: 0,
  memory: 0,
  requests: 0,
  errors: 0,
  latency: 0,

  connectWebSocket: () => {
    const ws = new WebSocket('wss://api.example.com/metrics');
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      set(data); // Zustand only notifies subscribers whose slice changed
    };
    return () => ws.close();
  },
}));

// Only re-renders when cpu changes — ignores memory, latency, etc.
function CpuGauge_Zustand() {
  const cpu = useMetricsStore((state) => state.cpu);
  return <div>CPU: {cpu}%</div>;
}

// Only re-renders when memory changes
function MemoryGauge_Zustand() {
  const memory = useMetricsStore((state) => state.memory);
  return <div>Memory: {memory}%</div>;
}
```

**Decision framework:**

| Scenario | Recommendation |
|---|---|
| Theme, locale, auth (infrequent updates, simple shape) | Context |
| Form state within a feature | `useState` / `useReducer` locally |
| Server data (lists, caching, pagination, refetching) | React Query / SWR |
| Complex client state with many subscribers | Zustand (lightweight) or Redux Toolkit (large team) |
| Real-time data (WebSockets, polling) | Zustand with subscriptions |
| State shared between disconnected parts of the tree | Zustand (works outside React) |

**The takeaway:** Context is the right tool when updates are infrequent and the consumer count is moderate. For anything high-frequency or with many independent subscribers, use a library with selectors.

---

### Q17. What changes does React 19 bring to Context (the `<Context>` shorthand)?

**Answer:**

React 19 introduces a quality-of-life improvement: you can render `<Context>` directly as the Provider instead of `<Context.Provider>`. The old syntax still works but is expected to be deprecated in a future version.

```jsx
import { createContext, useContext, useState } from 'react';

const ThemeContext = createContext('light');

// React 18 (and earlier): Must use .Provider
function App_React18() {
  const [theme, setTheme] = useState('light');

  return (
    <ThemeContext.Provider value={theme}>
      <Page />
    </ThemeContext.Provider>
  );
}

// React 19: Use <Context> directly as the Provider
function App_React19() {
  const [theme, setTheme] = useState('light');

  return (
    <ThemeContext value={theme}>
      <Page />
    </ThemeContext>
  );
}

// Consuming remains exactly the same in both versions
function Page() {
  const theme = useContext(ThemeContext);
  return <div className={theme}>Hello, themed world!</div>;
}
```

**What changed and why:**

1. **Shorter syntax** — `<ThemeContext value={theme}>` instead of `<ThemeContext.Provider value={theme}>`. Less boilerplate, especially when composing multiple Providers.
2. **`<Context.Provider>` will be deprecated** — React 19 logs a deprecation warning in development. It still works but will be removed in a future major version.
3. **No functional difference** — the rendering behavior, re-render semantics, default values, and `useContext` consumption are all identical.

```jsx
// React 19: Multiple contexts are less verbose
function AppProviders_React19({ children }) {
  const [theme, setTheme] = useState('light');
  const [locale, setLocale] = useState('en');
  const [user, setUser] = useState(null);

  return (
    <ThemeContext value={{ theme, setTheme }}>
      <LocaleContext value={{ locale, setLocale }}>
        <AuthContext value={{ user, setUser }}>
          {children}
        </AuthContext>
      </LocaleContext>
    </ThemeContext>
  );
}

// Compare React 18 equivalent
function AppProviders_React18({ children }) {
  const [theme, setTheme] = useState('light');
  const [locale, setLocale] = useState('en');
  const [user, setUser] = useState(null);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <LocaleContext.Provider value={{ locale, setLocale }}>
        <AuthContext.Provider value={{ user, setUser }}>
          {children}
        </AuthContext.Provider>
      </LocaleContext.Provider>
    </ThemeContext.Provider>
  );
}
```

**Migration path:**

- If you're on React 18 today, keep using `<Context.Provider>`.
- When you upgrade to React 19, you can migrate incrementally — both syntaxes work simultaneously.
- A codemod from the React team will automate the replacement: `npx react-codemod update-context-provider`.
- The new `use()` hook in React 19 also reads context (alternative to `useContext`) and can be called conditionally.

---

### Q18. What are the limitations of Context with React Server Components?

**Answer:**

React Server Components (RSC), available in frameworks like Next.js App Router, run on the server and cannot use hooks, state, or browser APIs. This has direct implications for Context:

1. **Server Components cannot use `useContext`** — they have no access to React's client-side fiber tree.
2. **Server Components cannot be Providers** — `<Context.Provider>` requires a client component.
3. **Context only works within the client component boundary** — once you mark a component with `'use client'`, it and its children can use Context normally.

```jsx
// layout.jsx — Server Component (default in Next.js App Router)
// ❌ Cannot use context directly in a Server Component

// ✅ Solution: Create a client-side Provider wrapper
// providers.jsx
'use client';

import { ThemeProvider } from './ThemeContext';
import { AuthProvider } from './AuthContext';

export function Providers({ children }) {
  return (
    <AuthProvider>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </AuthProvider>
  );
}
```

```jsx
// layout.jsx — Server Component that delegates to client Providers
import { Providers } from './providers';

export default function RootLayout({ children }) {
  // This is a Server Component — no hooks, no context
  // But it can render a Client Component that provides context
  return (
    <html lang="en">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
```

```jsx
// page.jsx — Server Component (fetches data on server)
import { Dashboard } from './Dashboard';

export default async function DashboardPage() {
  // Fetch data on the server — no loading spinner needed
  const stats = await fetch('https://api.example.com/stats').then((r) => r.json());

  // Pass server data as props to client components
  return <Dashboard initialStats={stats} />;
}
```

```jsx
// Dashboard.jsx — Client Component (can use context)
'use client';

import { useTheme } from './ThemeContext';
import { useAuth } from './AuthContext';

export function Dashboard({ initialStats }) {
  const { theme } = useTheme();     // ✅ Works — we're in a client component
  const { user } = useAuth();       // ✅ Works — AuthProvider is above us

  return (
    <div className={`dashboard-${theme}`}>
      <h1>Welcome, {user?.name}</h1>
      <p>Total users: {initialStats.totalUsers}</p>
    </div>
  );
}
```

**Key patterns for RSC + Context:**

| Pattern | How |
|---|---|
| Global context (theme, auth) | Client `Providers` component in root layout |
| Server data → client context | Fetch in Server Component, pass as props to Client Component that sets context |
| Avoid context entirely | For server data, prefer `fetch` in Server Components and pass via props |
| Per-page context | Wrap individual client subtrees, not the entire app |

**What you should NOT do:**

- Don't wrap your entire app in Context just to pass server-fetched data — use props from Server Components instead.
- Don't put `'use client'` at the top of every file to "make Context work" — you lose the benefits of Server Components.
- Don't try to "hydrate" context from server-side data via global variables — use the Server Component → props → Client Component pattern.

---

### Q19. How do you implement feature flags and A/B testing with Context?

**Answer:**

Context is an excellent fit for feature flags because flags change rarely (typically on app load or when a config endpoint is polled), and many components across the app need access to them. Here is a production-grade implementation:

```jsx
import { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';

// 1. Feature flag types and defaults
const DEFAULT_FLAGS = {
  newCheckout: false,
  darkModeV2: false,
  aiSearch: false,
  betaPricing: false,
  experimentalEditor: false,
};

const FeatureFlagContext = createContext(undefined);

function FeatureFlagProvider({ children, userId }) {
  const [flags, setFlags] = useState(DEFAULT_FLAGS);
  const [loading, setLoading] = useState(true);

  // Fetch flags from your feature flag service (LaunchDarkly, Unleash, custom)
  useEffect(() => {
    let cancelled = false;

    async function fetchFlags() {
      try {
        const res = await fetch(`/api/feature-flags?userId=${userId}`);
        const data = await res.json();
        if (!cancelled) {
          setFlags((prev) => ({ ...prev, ...data.flags }));
          setLoading(false);
        }
      } catch (err) {
        console.error('Failed to fetch feature flags:', err);
        if (!cancelled) setLoading(false); // Fall back to defaults
      }
    }

    fetchFlags();

    // Poll for flag updates every 5 minutes
    const interval = setInterval(fetchFlags, 5 * 60 * 1000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [userId]);

  const isEnabled = useCallback(
    (flagName) => {
      if (!(flagName in flags)) {
        console.warn(`Unknown feature flag: "${flagName}". Returning false.`);
        return false;
      }
      return flags[flagName];
    },
    [flags]
  );

  const value = useMemo(
    () => ({ flags, isEnabled, loading }),
    [flags, isEnabled, loading]
  );

  return (
    <FeatureFlagContext.Provider value={value}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

function useFeatureFlags() {
  const ctx = useContext(FeatureFlagContext);
  if (!ctx) throw new Error('useFeatureFlags requires FeatureFlagProvider');
  return ctx;
}

function useFeatureFlag(flagName) {
  const { isEnabled } = useFeatureFlags();
  return isEnabled(flagName);
}

// 2. Declarative feature gate component
function FeatureGate({ flag, fallback = null, children }) {
  const enabled = useFeatureFlag(flag);
  return enabled ? children : fallback;
}

// 3. Usage in components
function SearchBar() {
  const aiEnabled = useFeatureFlag('aiSearch');

  return (
    <div className="search-bar">
      <input placeholder={aiEnabled ? 'Ask AI anything...' : 'Search products...'} />
      {aiEnabled && <span className="badge">AI-Powered</span>}
    </div>
  );
}

function CheckoutPage() {
  return (
    <div>
      <h1>Checkout</h1>

      {/* Declarative: show new checkout if flag is on, old otherwise */}
      <FeatureGate flag="newCheckout" fallback={<LegacyCheckoutForm />}>
        <NewCheckoutForm />
      </FeatureGate>

      {/* A/B test: show different pricing for beta users */}
      <FeatureGate flag="betaPricing" fallback={<StandardPricing />}>
        <BetaPricing />
      </FeatureGate>
    </div>
  );
}

// 4. A/B testing with analytics tracking
function useABTest(experimentName, flagName) {
  const enabled = useFeatureFlag(flagName);
  const variant = enabled ? 'treatment' : 'control';

  useEffect(() => {
    // Track exposure — user saw this variant
    fetch('/api/analytics/exposure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ experiment: experimentName, variant }),
    });
  }, [experimentName, variant]);

  return { variant, isTreatment: enabled };
}

function PricingPage() {
  const { variant, isTreatment } = useABTest('pricing-experiment-2024', 'betaPricing');

  return (
    <div data-experiment-variant={variant}>
      {isTreatment ? (
        <NewPricingTiers />
      ) : (
        <CurrentPricingTiers />
      )}
    </div>
  );
}

// 5. App root
function App() {
  return (
    <FeatureFlagProvider userId={currentUser.id}>
      <SearchBar />
      <CheckoutPage />
    </FeatureFlagProvider>
  );
}
```

**Production considerations:**

- **Defaults are critical** — if the flag service is down, your app should still work with sensible defaults.
- **Flag evaluation should be fast** — flags are fetched once and cached in state; components read from memory, not the network.
- **Stale flags are better than no flags** — use the last successful response if a poll fails.
- **Track exposures, not just flag values** — for A/B tests, you must record which users saw which variant to compute statistical significance.

---

### Q20. How do you build a production authentication system with Context (tokens, refresh, and role-based access)?

**Answer:**

A production auth system with Context handles: login/logout, access token storage, automatic token refresh, role-based route protection, and clean error handling. Here is a complete implementation:

```jsx
import {
  createContext, useContext, useState, useEffect,
  useCallback, useMemo, useRef,
} from 'react';

// --- Auth Context ---
const AuthContext = createContext(undefined);

// Token utilities
function decodeJWT(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload;
  } catch {
    return null;
  }
}

function isTokenExpired(token) {
  const payload = decodeJWT(token);
  if (!payload?.exp) return true;
  // Consider expired 60 seconds before actual expiry (buffer for network latency)
  return Date.now() >= (payload.exp * 1000) - 60000;
}

// --- Auth Provider ---
function AuthProvider({ children }) {
  const [state, setState] = useState({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: true, // True during initial token validation
  });

  const refreshTimeoutRef = useRef(null);

  // Schedule automatic token refresh
  const scheduleRefresh = useCallback((accessToken) => {
    if (refreshTimeoutRef.current) clearTimeout(refreshTimeoutRef.current);

    const payload = decodeJWT(accessToken);
    if (!payload?.exp) return;

    const expiresIn = payload.exp * 1000 - Date.now();
    // Refresh 2 minutes before expiry
    const refreshIn = Math.max(expiresIn - 120000, 0);

    refreshTimeoutRef.current = setTimeout(() => {
      refreshAccessToken();
    }, refreshIn);
  }, []);

  // Refresh the access token using the refresh token
  const refreshAccessToken = useCallback(async () => {
    const currentRefreshToken = localStorage.getItem('refreshToken');
    if (!currentRefreshToken) {
      setState((prev) => ({
        ...prev,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
      }));
      return null;
    }

    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: currentRefreshToken }),
      });

      if (!res.ok) throw new Error('Refresh failed');

      const data = await res.json();

      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);

      const user = decodeJWT(data.accessToken);

      setState({
        user: { id: user.sub, name: user.name, email: user.email, roles: user.roles },
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        isAuthenticated: true,
        isLoading: false,
      });

      scheduleRefresh(data.accessToken);
      return data.accessToken;
    } catch {
      // Refresh token is invalid — force logout
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      setState({
        user: null, accessToken: null, refreshToken: null,
        isAuthenticated: false, isLoading: false,
      });
      return null;
    }
  }, [scheduleRefresh]);

  // Initialize auth state from stored tokens
  useEffect(() => {
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');

    if (accessToken && !isTokenExpired(accessToken)) {
      const payload = decodeJWT(accessToken);
      setState({
        user: { id: payload.sub, name: payload.name, email: payload.email, roles: payload.roles },
        accessToken,
        refreshToken,
        isAuthenticated: true,
        isLoading: false,
      });
      scheduleRefresh(accessToken);
    } else if (refreshToken) {
      refreshAccessToken();
    } else {
      setState((prev) => ({ ...prev, isLoading: false }));
    }

    return () => {
      if (refreshTimeoutRef.current) clearTimeout(refreshTimeoutRef.current);
    };
  }, [refreshAccessToken, scheduleRefresh]);

  // Login
  const login = useCallback(async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.message || 'Login failed');
    }

    const data = await res.json();

    localStorage.setItem('accessToken', data.accessToken);
    localStorage.setItem('refreshToken', data.refreshToken);

    const payload = decodeJWT(data.accessToken);

    setState({
      user: { id: payload.sub, name: payload.name, email: payload.email, roles: payload.roles },
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      isAuthenticated: true,
      isLoading: false,
    });

    scheduleRefresh(data.accessToken);
  }, [scheduleRefresh]);

  // Logout
  const logout = useCallback(async () => {
    try {
      const token = localStorage.getItem('accessToken');
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // Best-effort server logout
    } finally {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      if (refreshTimeoutRef.current) clearTimeout(refreshTimeoutRef.current);
      setState({
        user: null, accessToken: null, refreshToken: null,
        isAuthenticated: false, isLoading: false,
      });
    }
  }, []);

  // Authenticated fetch helper
  const authFetch = useCallback(async (url, options = {}) => {
    let token = state.accessToken;

    if (!token || isTokenExpired(token)) {
      token = await refreshAccessToken();
      if (!token) throw new Error('Authentication required');
    }

    const res = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      },
    });

    // If 401, try one refresh
    if (res.status === 401) {
      token = await refreshAccessToken();
      if (!token) throw new Error('Authentication required');

      return fetch(url, {
        ...options,
        headers: { ...options.headers, Authorization: `Bearer ${token}` },
      });
    }

    return res;
  }, [state.accessToken, refreshAccessToken]);

  const value = useMemo(
    () => ({
      ...state,
      login,
      logout,
      authFetch,
      hasRole: (role) => state.user?.roles?.includes(role) ?? false,
      hasAnyRole: (...roles) => roles.some((r) => state.user?.roles?.includes(r)),
    }),
    [state, login, logout, authFetch]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth requires AuthProvider');
  return ctx;
}

// --- Role-Based Access Components ---
function RequireAuth({ children, fallback = null }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <div className="spinner">Loading...</div>;
  if (!isAuthenticated) return fallback || <Navigate to="/login" />;

  return children;
}

function RequireRole({ roles, children, fallback = null }) {
  const { hasAnyRole, isLoading } = useAuth();

  if (isLoading) return <div className="spinner">Loading...</div>;
  if (!hasAnyRole(...roles)) return fallback || <ForbiddenPage />;

  return children;
}

// --- Usage in routes ---
function AppRoutes() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Protected route — any authenticated user */}
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <DashboardPage />
            </RequireAuth>
          }
        />

        {/* Role-protected route — only admins */}
        <Route
          path="/admin/*"
          element={
            <RequireRole roles={['admin']}>
              <AdminPanel />
            </RequireRole>
          }
        />

        {/* Role-protected — admins or managers */}
        <Route
          path="/reports"
          element={
            <RequireRole roles={['admin', 'manager']}>
              <ReportsPage />
            </RequireRole>
          }
        />
      </Routes>
    </AuthProvider>
  );
}

// --- Using authFetch in components ---
function UserSettings() {
  const { user, authFetch } = useAuth();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    authFetch('/api/user/profile')
      .then((res) => res.json())
      .then(setProfile)
      .catch(console.error);
  }, [authFetch]);

  if (!profile) return <p>Loading profile...</p>;

  return (
    <div>
      <h2>{profile.name}'s Settings</h2>
      <p>Email: {profile.email}</p>
      <p>Roles: {profile.roles.join(', ')}</p>
    </div>
  );
}

// --- Conditional UI based on roles ---
function NavigationMenu() {
  const { user, hasRole, logout } = useAuth();

  return (
    <nav>
      <a href="/dashboard">Dashboard</a>
      {hasRole('manager') && <a href="/reports">Reports</a>}
      {hasRole('admin') && <a href="/admin">Admin Panel</a>}
      <span>{user.name}</span>
      <button onClick={logout}>Log Out</button>
    </nav>
  );
}
```

**Production checklist for Context-based auth:**

1. **Token storage** — `localStorage` is used here for simplicity. For higher security, store the access token in memory (React state) and the refresh token in an `httpOnly` cookie set by the server.
2. **Automatic refresh** — schedule a refresh before the access token expires, and handle 401 responses by attempting a single refresh.
3. **Race conditions** — if multiple `authFetch` calls trigger simultaneous refreshes, use a promise lock so only one refresh request fires.
4. **XSS protection** — never store sensitive tokens where JavaScript can access them in a production environment without CSP headers and input sanitization.
5. **Role-based access** — enforce roles on **both** the client (for UX) and the server (for security). Client-side role checks are for UI gating only; the API must independently verify permissions.
6. **Loading state** — always account for the initial loading state when tokens are being validated; rendering a protected route before auth state is resolved will flash the login page.

This is a complete, production-ready auth system built entirely with React Context, `useState`, `useCallback`, and `useMemo` — no external auth libraries required (though libraries like `next-auth` or `clerk` abstract much of this for you).

---

*End of Topic 7 — Context API & Dependency Injection in React 18*
