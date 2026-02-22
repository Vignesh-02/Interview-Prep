# Topic 11: Component Design Patterns in React 18

## Introduction

Component design patterns are reusable architectural solutions to recurring problems in React application development. Just as the Gang of Four catalogued object-oriented patterns decades ago, the React community has evolved its own set of composition and abstraction patterns — Container/Presentational, Higher-Order Components, Render Props, Compound Components, Headless UI, Polymorphic Components, and many more — each addressing a specific challenge around code reuse, separation of concerns, and API flexibility. In React 18, the introduction of concurrent features (`useTransition`, `useDeferredValue`, automatic batching) and the maturation of hooks have shifted the pattern landscape significantly: custom hooks have largely replaced HOCs and render props for sharing stateful logic, while composition-first patterns (compound components, headless components, polymorphic "as" props) have become the gold standard for building flexible, accessible component libraries. Understanding these patterns is not about memorising recipes; it is about recognising the underlying forces — coupling, cohesion, inversion of control, implicit versus explicit state — that make one design more maintainable, testable, and extensible than another.

In a production codebase, you rarely use a single pattern in isolation. A design system, for instance, might expose a `<Select>` built with the **compound component** pattern (so consumers compose `<Select.Trigger>`, `<Select.Option>`, etc.), implemented internally with the **headless UI** pattern (logic separated from markup), offered as a **polymorphic component** (so the trigger can render as a `<button>`, `<div>`, or a custom component via an `as` prop), and themed through the **provider pattern** (a `<ThemeProvider>` using React Context). Meanwhile, application-level code might organise features using the **Feature-Sliced Design** architecture, wire up forms with the **controlled/uncontrolled** pattern, and customise third-party component behaviour via the **state reducer** or **props getter** pattern. Mastering this layered composition of patterns is what separates a junior developer who can build components from a senior developer who can design APIs that scale across teams and years.

Below is an illustrative code example that weaves several patterns together — a compound, polymorphic, context-powered `Tabs` component — to set the stage for the detailed questions that follow:

```jsx
import { createContext, useContext, useState, useCallback } from 'react';

// --- Provider Pattern: implicit state sharing via Context ---
const TabsContext = createContext(null);

function useTabs() {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('Tabs compound components must be used within <Tabs>');
  return ctx;
}

// --- Compound Component Root ---
function Tabs({ defaultValue, children }) {
  const [activeTab, setActiveTab] = useState(defaultValue);
  const value = { activeTab, setActiveTab };
  return <TabsContext.Provider value={value}>{children}</TabsContext.Provider>;
}

// --- Polymorphic Component: "as" prop lets consumers control the rendered element ---
function TabTrigger({ value, as: Component = 'button', ...rest }) {
  const { activeTab, setActiveTab } = useTabs();
  return (
    <Component
      role="tab"
      aria-selected={activeTab === value}
      onClick={() => setActiveTab(value)}
      data-state={activeTab === value ? 'active' : 'inactive'}
      {...rest}
    />
  );
}

function TabContent({ value, children }) {
  const { activeTab } = useTabs();
  if (activeTab !== value) return null;
  return <div role="tabpanel">{children}</div>;
}

// Attach sub-components for clean dot-notation API
Tabs.Trigger = TabTrigger;
Tabs.Content = TabContent;

// --- Consumer Usage ---
function SettingsPage() {
  return (
    <Tabs defaultValue="general">
      <div role="tablist">
        <Tabs.Trigger value="general">General</Tabs.Trigger>
        <Tabs.Trigger value="security">Security</Tabs.Trigger>
        <Tabs.Trigger value="billing" as="a" href="#billing">Billing</Tabs.Trigger>
      </div>
      <Tabs.Content value="general"><GeneralSettings /></Tabs.Content>
      <Tabs.Content value="security"><SecuritySettings /></Tabs.Content>
      <Tabs.Content value="billing"><BillingSettings /></Tabs.Content>
    </Tabs>
  );
}
```

This snippet demonstrates compound components (`Tabs`, `Tabs.Trigger`, `Tabs.Content`), the provider pattern (Context-based implicit state), and the polymorphic pattern (the `as` prop on `TabTrigger`). Each question below dives deep into one of these patterns, progressing from foundational concepts to production-grade architecture.

---

## Beginner Level (Q1–Q5)

---

### Q1. What is the Container/Presentational pattern in React, and why was it historically popular for separating logic from UI?

**Answer:**

The Container/Presentational pattern (also called Smart/Dumb or Stateful/Stateless) divides components into two categories. **Presentational components** are concerned exclusively with *how things look*: they receive data and callbacks via props, render markup and styles, and contain no business logic, side effects, or state management (other than trivial UI state like a tooltip open/close). **Container components** are concerned with *how things work*: they fetch data, manage state, handle side effects, and pass the results down to presentational components. This separation yields several benefits: presentational components are trivially reusable (they work with any data source), easy to test (just pass props), and simple to style or snapshot-test in isolation. Container components consolidate business logic in one place, making it easier to trace data flow.

The pattern was popularised by Dan Abramov in 2015 during the class-component era, when mixins and inheritance were the primary means of code reuse and separating "data fetching" from "rendering" improved clarity. With the arrival of hooks in React 16.8 (and matured in React 18), the pattern has become less rigidly enforced because custom hooks now extract and share stateful logic without requiring a wrapper container component. However, the *principle* behind the pattern — separating concerns — remains a cornerstone of clean React architecture. Many codebases still use the pattern implicitly: a page component fetches data and passes it to child display components.

```jsx
// --- Presentational Component ---
// Pure UI: receives data, renders it. No fetching, no state management.
function UserProfile({ user, onFollow }) {
  return (
    <div className="user-profile">
      <img src={user.avatarUrl} alt={user.name} className="avatar" />
      <h2>{user.name}</h2>
      <p>{user.bio}</p>
      <span className="stats">{user.followers} followers</span>
      <button onClick={onFollow} className="follow-btn">
        Follow
      </button>
    </div>
  );
}

// --- Container Component ---
// Handles data fetching, state, side effects.
import { useState, useEffect } from 'react';

function UserProfileContainer({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => {
        if (!cancelled) {
          setUser(data);
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [userId]);

  const handleFollow = async () => {
    await fetch(`/api/users/${userId}/follow`, { method: 'POST' });
    setUser(prev => ({ ...prev, followers: prev.followers + 1 }));
  };

  if (loading) return <ProfileSkeleton />;
  return <UserProfile user={user} onFollow={handleFollow} />;
}
```

In modern React 18 code, you would likely extract the fetching logic into a `useUser(userId)` custom hook, collapsing the need for a separate container component entirely — but the mental separation of "data" and "display" remains invaluable.

---

### Q2. What is a Higher-Order Component (HOC), and how does it enable cross-cutting concerns like authentication or logging?

**Answer:**

A Higher-Order Component is a **function** that takes a component and returns a new enhanced component. It is not a React API; it is a pattern that emerges naturally from JavaScript's functional composition and React's compositional model. The HOC wraps the original component, injecting additional props, guarding access, or adding side effects — all without modifying the original component's source code. This makes HOCs ideal for **cross-cutting concerns**: behaviour that many components need (authentication checks, analytics tracking, error boundaries, data fetching, theming) but that should not be duplicated in every component.

The classic shape of an HOC is:

```jsx
function withEnhancement(WrappedComponent) {
  return function EnhancedComponent(props) {
    // add logic here
    return <WrappedComponent {...props} />;
  };
}
```

Here is a concrete production example — a `withAuth` HOC that redirects unauthenticated users:

```jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

function withAuth(WrappedComponent) {
  function AuthenticatedComponent(props) {
    const { user, isLoading } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
      if (!isLoading && !user) {
        navigate('/login', { replace: true });
      }
    }, [user, isLoading, navigate]);

    if (isLoading) return <div className="spinner" />;
    if (!user) return null; // will redirect

    return <WrappedComponent {...props} user={user} />;
  }

  // Preserve the display name for React DevTools
  AuthenticatedComponent.displayName =
    `withAuth(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;

  return AuthenticatedComponent;
}

// Usage
const ProtectedDashboard = withAuth(Dashboard);

function App() {
  return <ProtectedDashboard title="My Dashboard" />;
}
```

While HOCs were the dominant reuse pattern in the class-component era (connect from Redux, withRouter from React Router), custom hooks have largely supplanted them in React 18 for sharing stateful logic. However, HOCs are still useful when you need to **wrap JSX output** (e.g., wrapping a component in an error boundary or a layout) — something hooks cannot do because hooks only return data, not elements.

---

### Q3. What is the Render Props pattern, and how does it differ from HOCs for sharing component logic?

**Answer:**

The Render Props pattern shares code between components by using a prop whose value is a **function** that returns React elements. Instead of wrapping a component externally (like an HOC), the component with the logic *calls* the function prop at render time, passing its internal state as arguments. This gives the consumer complete control over what gets rendered while the provider component owns the logic.

The key difference from HOCs:
- **HOCs** create a new component at module level (compile time); the consumer has no control over how the injected props are named or what JSX wraps the inner component.
- **Render Props** are consumed at render time (inside JSX); the consumer sees exactly what data is available and decides how to render it.

This makes render props more explicit and easier to follow in a code review, but they can lead to deeply nested JSX (the "callback hell" of React) when composed. Here is a practical example — a `MouseTracker` that shares mouse position:

```jsx
import { useState, useEffect, useCallback } from 'react';

// The logic-owning component: tracks mouse position and calls the render prop
function MouseTracker({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = useCallback((e) => {
    setPosition({ x: e.clientX, y: e.clientY });
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [handleMouseMove]);

  return render(position);
}

// Consumer A: renders a tooltip that follows the cursor
function CursorTooltip() {
  return (
    <MouseTracker
      render={({ x, y }) => (
        <div
          className="cursor-tooltip"
          style={{ position: 'fixed', left: x + 12, top: y + 12 }}
        >
          ({x}, {y})
        </div>
      )}
    />
  );
}

// Consumer B: renders a heatmap overlay
function HeatmapOverlay() {
  return (
    <MouseTracker
      render={({ x, y }) => (
        <canvas
          data-cursor-x={x}
          data-cursor-y={y}
          className="heatmap-canvas"
        />
      )}
    />
  );
}
```

In React 18, the render props pattern is less common for **stateful logic sharing** (use a `useMouse()` custom hook instead), but it remains valuable for **UI slot patterns** — e.g., virtualized lists (`react-window`) pass a render function for each row, and data tables pass render functions for custom cell rendering.

---

### Q4. How do Custom Hooks compare to HOCs and Render Props in React 18, and when would you still choose an HOC or Render Prop over a hook?

**Answer:**

Custom Hooks are the modern React 18 solution for extracting and sharing **stateful logic**. A custom hook is simply a JavaScript function whose name starts with `use` and which may call other hooks. Unlike HOCs and render props, hooks do not add extra components to the tree, do not introduce prop-name collisions, and compose naturally using plain variable assignment.

| Criteria | Custom Hooks | HOCs | Render Props |
|---|---|---|---|
| Adds wrapper components | No | Yes | Yes |
| Can share stateful logic | Yes | Yes | Yes |
| Can modify rendered JSX | No (returns data only) | Yes (wraps elements) | Yes (consumer controls JSX) |
| Prop name conflicts | None | Possible | None |
| TypeScript ergonomics | Excellent | Verbose generics | Good |
| DevTools tree clutter | None | Extra wrapper nodes | Extra wrapper nodes |
| Composability | Simple function calls | Nested function calls (`compose`) | Nested JSX |

**When hooks are the default choice (most cases):**

```jsx
// Custom hook extracts the logic cleanly
function useMouse() {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handler = (e) => setPosition({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  return position;
}

// Any component can use it — no wrappers, no nesting
function CursorTooltip() {
  const { x, y } = useMouse();
  return (
    <div style={{ position: 'fixed', left: x + 12, top: y + 12 }}>
      ({x}, {y})
    </div>
  );
}
```

**When you would still reach for an HOC:**
1. **Wrapping JSX** — e.g., wrapping a component in an error boundary, a layout, or a `<Suspense>` boundary cannot be done from inside a hook.
2. **Third-party integration** — some libraries still expose HOCs (e.g., older Redux `connect`), and wrapping is the only option.
3. **Conditional rendering guards** — an `withAuth` HOC that prevents the wrapped component from rendering at all is cleaner than putting auth checks inside every component.

**When you would still use render props:**
1. **UI injection slots** — virtualized list libraries (`react-window`, `@tanstack/virtual`) need a render function for each item.
2. **Scoped rendering** — when the component providing logic also provides a DOM container (like a `<Draggable>` that must wrap the draggable element).

In practice in React 18, **hooks cover 90%+ of logic-sharing needs**. HOCs and render props are reserved for the specific structural situations described above.

---

### Q5. What is the Controlled vs Uncontrolled component pattern, and how do you decide which to use for a form input in React 18?

**Answer:**

A **controlled component** stores its current value in React state and updates it through an event handler on every change. React is the "single source of truth" — the input always reflects `state`. An **uncontrolled component** lets the DOM itself hold the value; you access it via a `ref` when needed (e.g., on form submission). This mirrors the broader controlled/uncontrolled pattern that applies to any component with internal state that can optionally be driven externally.

**Controlled** — use when you need to:
- Validate or transform input on every keystroke (e.g., enforce uppercase, limit characters)
- Conditionally enable/disable a submit button based on current values
- Synchronise the input with other state (e.g., a search-as-you-type filter)
- Programmatically reset or set values

**Uncontrolled** — use when you need to:
- Integrate with non-React code or third-party DOM libraries
- Optimize forms with many fields where re-rendering on every keystroke hurts performance
- Quickly prototype simple forms where validation happens only on submit

```jsx
import { useState, useRef } from 'react';

// --- Controlled Component ---
function ControlledSearch({ onSearch }) {
  const [query, setQuery] = useState('');

  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    onSearch(value); // filter results on every keystroke
  };

  return (
    <input
      type="text"
      value={query}
      onChange={handleChange}
      placeholder="Search..."
    />
  );
}

// --- Uncontrolled Component ---
function UncontrolledLoginForm({ onSubmit }) {
  const emailRef = useRef(null);
  const passwordRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      email: emailRef.current.value,
      password: passwordRef.current.value,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input ref={emailRef} type="email" defaultValue="" placeholder="Email" />
      <input ref={passwordRef} type="password" defaultValue="" placeholder="Password" />
      <button type="submit">Log In</button>
    </form>
  );
}

// --- Hybrid: component supports both controlled and uncontrolled usage ---
function TextInput({ value: controlledValue, defaultValue, onChange, ...rest }) {
  const isControlled = controlledValue !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue ?? '');

  const value = isControlled ? controlledValue : internalValue;

  const handleChange = (e) => {
    if (!isControlled) setInternalValue(e.target.value);
    onChange?.(e);
  };

  return <input value={value} onChange={handleChange} {...rest} />;
}
```

The hybrid pattern shown at the bottom is how production component libraries (Radix, MUI, Headless UI) expose inputs: consumers can use them as controlled (passing `value` + `onChange`) or uncontrolled (passing only `defaultValue`), providing maximum flexibility.

---

## Intermediate Level (Q6–Q12)

---

### Q6. Explain the Compound Components pattern. How would you build a production `<Select>` component using this pattern?

**Answer:**

Compound Components is a pattern where a parent component and its child sub-components work together to form a cohesive unit, sharing implicit state without requiring the consumer to wire props between them. The canonical examples are HTML's `<select>` + `<option>`, and `<table>` + `<thead>` + `<tr>` + `<td>`. In React, this is achieved by using **Context** to share state from the parent to deeply nested children, and by exporting sub-components as static properties of the parent for a clean dot-notation API.

The pattern shines when a component has multiple co-dependent pieces of UI that the consumer should be free to arrange, style, and compose however they want — while the parent manages the coordination logic behind the scenes.

Here is a production-quality `<Select>` component:

```jsx
import {
  createContext,
  useContext,
  useState,
  useRef,
  useEffect,
  useCallback,
  useId,
} from 'react';

// 1. Context for implicit state sharing
const SelectContext = createContext(null);

function useSelectContext() {
  const ctx = useContext(SelectContext);
  if (!ctx) throw new Error('Select sub-components must be rendered inside <Select>');
  return ctx;
}

// 2. Root: manages open/close state and selected value
function Select({ value, defaultValue, onValueChange, children }) {
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue ?? '');
  const [open, setOpen] = useState(false);
  const triggerRef = useRef(null);
  const listboxId = useId();

  const selectedValue = isControlled ? value : internalValue;

  const selectValue = useCallback(
    (newValue) => {
      if (!isControlled) setInternalValue(newValue);
      onValueChange?.(newValue);
      setOpen(false);
      triggerRef.current?.focus();
    },
    [isControlled, onValueChange]
  );

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (!triggerRef.current?.parentElement?.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <SelectContext.Provider
      value={{ open, setOpen, selectedValue, selectValue, triggerRef, listboxId }}
    >
      <div className="select-root" style={{ position: 'relative' }}>
        {children}
      </div>
    </SelectContext.Provider>
  );
}

// 3. Trigger sub-component
function SelectTrigger({ placeholder = 'Select...', children }) {
  const { open, setOpen, selectedValue, triggerRef, listboxId } = useSelectContext();

  return (
    <button
      ref={triggerRef}
      role="combobox"
      aria-expanded={open}
      aria-controls={listboxId}
      onClick={() => setOpen((prev) => !prev)}
      className="select-trigger"
    >
      {selectedValue || placeholder}
      <span aria-hidden="true">{open ? '▲' : '▼'}</span>
    </button>
  );
}

// 4. Content (dropdown) sub-component
function SelectContent({ children }) {
  const { open, listboxId } = useSelectContext();
  if (!open) return null;

  return (
    <ul role="listbox" id={listboxId} className="select-content">
      {children}
    </ul>
  );
}

// 5. Item sub-component
function SelectItem({ value, children }) {
  const { selectedValue, selectValue } = useSelectContext();
  const isSelected = selectedValue === value;

  return (
    <li
      role="option"
      aria-selected={isSelected}
      onClick={() => selectValue(value)}
      className={`select-item ${isSelected ? 'selected' : ''}`}
    >
      {children}
      {isSelected && <span aria-hidden="true">✓</span>}
    </li>
  );
}

// 6. Attach sub-components
Select.Trigger = SelectTrigger;
Select.Content = SelectContent;
Select.Item = SelectItem;

// --- Consumer Usage ---
function CountryPicker() {
  const [country, setCountry] = useState('');

  return (
    <Select value={country} onValueChange={setCountry}>
      <Select.Trigger placeholder="Choose country" />
      <Select.Content>
        <Select.Item value="us">United States</Select.Item>
        <Select.Item value="uk">United Kingdom</Select.Item>
        <Select.Item value="de">Germany</Select.Item>
        <Select.Item value="jp">Japan</Select.Item>
      </Select.Content>
    </Select>
  );
}
```

The consumer never passes `open`, `selectedValue`, or handlers between sub-components — the parent `<Select>` handles all coordination via Context. This produces a clean, declarative API while keeping the internals fully encapsulated.

---

### Q7. How does the Provider pattern work with React Context, and what are the best practices for structuring Context providers in a production app?

**Answer:**

The Provider pattern uses React's Context API to make values available to a subtree of components without explicit prop drilling. A provider component wraps part of the tree and exposes a value; any descendant can consume it via `useContext`. This pattern is fundamental to theming, authentication state, locale/i18n, feature flags, and toast/notification systems.

**Best practices for production:**
1. **Split contexts by domain** — don't put everything in a single `AppContext`. Separate concerns (auth, theme, locale) so that a change in one context does not re-render components that only consume another.
2. **Separate state and dispatch contexts** — for contexts using `useReducer`, provide the state and dispatch in separate contexts so components that only dispatch actions don't re-render when state changes.
3. **Always provide a custom hook** — wrap `useContext` in a named hook (e.g., `useTheme()`) that throws a helpful error if used outside the provider.
4. **Memoize the context value** — wrap the value object in `useMemo` to prevent unnecessary re-renders of consumers.

```jsx
import {
  createContext,
  useContext,
  useReducer,
  useMemo,
  useCallback,
} from 'react';

// --- 1. Separate state and dispatch contexts ---
const AuthStateContext = createContext(null);
const AuthDispatchContext = createContext(null);

// --- 2. Reducer for predictable state transitions ---
function authReducer(state, action) {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return { ...state, user: action.payload, isAuthenticated: true, isLoading: false };
    case 'LOGOUT':
      return { ...state, user: null, isAuthenticated: false };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    default:
      throw new Error(`Unhandled action type: ${action.type}`);
  }
}

const initialState = { user: null, isAuthenticated: false, isLoading: true };

// --- 3. Provider component ---
function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Memoize so consumers don't re-render on every AuthProvider render
  const stateValue = useMemo(() => state, [state]);

  // Wrap dispatch in stable action creators
  const login = useCallback(
    (userData) => dispatch({ type: 'LOGIN_SUCCESS', payload: userData }),
    []
  );
  const logout = useCallback(() => dispatch({ type: 'LOGOUT' }), []);

  const actions = useMemo(() => ({ login, logout }), [login, logout]);

  return (
    <AuthStateContext.Provider value={stateValue}>
      <AuthDispatchContext.Provider value={actions}>
        {children}
      </AuthDispatchContext.Provider>
    </AuthStateContext.Provider>
  );
}

// --- 4. Custom hooks with error boundaries ---
function useAuthState() {
  const context = useContext(AuthStateContext);
  if (context === null) {
    throw new Error('useAuthState must be used within an <AuthProvider>');
  }
  return context;
}

function useAuthActions() {
  const context = useContext(AuthDispatchContext);
  if (context === null) {
    throw new Error('useAuthActions must be used within an <AuthProvider>');
  }
  return context;
}

// --- 5. Consumer components ---
// This component ONLY re-renders when auth state changes
function UserGreeting() {
  const { user, isAuthenticated } = useAuthState();
  if (!isAuthenticated) return <p>Please log in.</p>;
  return <p>Welcome back, {user.name}!</p>;
}

// This component NEVER re-renders due to state changes — it only dispatches
function LogoutButton() {
  const { logout } = useAuthActions();
  return <button onClick={logout}>Log Out</button>;
}

// --- 6. Compose providers at the app root ---
function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <LocaleProvider>
          <Router />
        </LocaleProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
```

Splitting state and dispatch into separate contexts is a critical optimization: `LogoutButton` holds only a reference to the stable `actions` object and never re-renders when the user state changes. This technique scales well — in a production app with dozens of consumers, it dramatically reduces unnecessary re-renders.

---

### Q8. What is the Composition pattern using `children` and slots, and how does it help avoid prop drilling?

**Answer:**

The Composition pattern leverages React's `children` prop (and the broader concept of "slots") to build flexible layouts where the parent decides *where* content goes, and the consumer decides *what* content goes there. Instead of passing data down through multiple intermediate components (prop drilling), you compose the actual elements at a higher level and pass them as children or named slots. This is React's most fundamental pattern and the one the React team recommends reaching for first, before Context or any other abstraction.

**Slot-based composition** generalises `children` by accepting multiple named props that each receive JSX:

```jsx
// --- Layout Component with Named Slots ---
function PageLayout({ header, sidebar, children, footer }) {
  return (
    <div className="page-layout">
      <header className="page-header">{header}</header>
      <div className="page-body">
        <aside className="page-sidebar">{sidebar}</aside>
        <main className="page-content">{children}</main>
      </div>
      <footer className="page-footer">{footer}</footer>
    </div>
  );
}

// --- Consumer: composes real elements into slots ---
function DashboardPage() {
  const { user } = useAuthState();

  return (
    <PageLayout
      header={<TopNav user={user} />}
      sidebar={<DashboardSidebar role={user.role} />}
      footer={<AppFooter />}
    >
      {/* children = main content */}
      <DashboardStats />
      <RecentActivity />
    </PageLayout>
  );
}
```

Notice that `PageLayout` does not need to know about `user` — it never receives it as a prop. `DashboardPage` creates `<TopNav user={user} />` at the top level where `user` is available, then passes the fully-formed element to the layout. This completely eliminates prop drilling through `PageLayout`.

**The deeper insight:** This works because React elements are just objects. When you write `<TopNav user={user} />`, React doesn't render it immediately — it creates a descriptor object. Passing that object as a prop or child to another component is free; the element renders in place when React reaches it in the tree, with the props it was originally given.

```jsx
// --- Comparison: Prop Drilling vs Composition ---

// BAD: Prop drilling — Page passes user through Layout which doesn't use it
function BadLayout({ user, children }) {
  return (
    <div>
      <BadHeader user={user} /> {/* Layout forced to know about "user" */}
      {children}
    </div>
  );
}

// GOOD: Composition — Layout has no idea about user
function GoodLayout({ header, children }) {
  return (
    <div>
      {header} {/* Layout just renders whatever element it receives */}
      {children}
    </div>
  );
}

function App() {
  const user = useUser();
  return (
    <GoodLayout header={<Header user={user} />}>
      <MainContent />
    </GoodLayout>
  );
}
```

This pattern is the first tool you should reach for to solve prop drilling. Context should be reserved for truly global or deeply shared state; composition handles the rest.

---

### Q9. What are the common pitfalls of Higher-Order Components, and how do you address prop conflicts, ref forwarding, and displayName issues?

**Answer:**

Despite their usefulness, HOCs introduce several well-known pitfalls that can cause subtle bugs in production:

**1. Prop Name Conflicts:** If an HOC injects a prop (e.g., `data`) and the consumer also passes a prop named `data`, one silently overwrites the other. Multiple HOCs composed together (`withA(withB(withC(Component)))`) make this worse — each layer might shadow props from another.

**2. Ref Forwarding:** When you wrap a component in an HOC, a `ref` placed on the HOC-wrapped component points to the *wrapper*, not the inner component. This breaks imperative handles, focus management, and any parent that needs direct DOM access.

**3. Lost `displayName`:** React DevTools shows the wrapper function's name (or just "Anonymous"), making debugging difficult in a tree full of HOC wrappers.

**4. Static Method Loss:** Any static methods on the original component are not automatically available on the HOC wrapper.

Here is how to address all four issues:

```jsx
import { forwardRef, useEffect } from 'react';

// A robust HOC that handles all common pitfalls
function withAnalytics(WrappedComponent, trackingId) {
  // 1. Use forwardRef to pass refs through to the wrapped component
  const WithAnalytics = forwardRef(function WithAnalytics(props, ref) {
    useEffect(() => {
      // Track component mount
      analytics.track(`${trackingId}_viewed`, {
        timestamp: Date.now(),
        props: Object.keys(props), // log prop names, not values (privacy)
      });
    }, []);

    // 2. Avoid prop conflicts by namespacing injected props,
    //    or better yet, don't inject props — use hooks inside the HOC instead
    const analyticsProps = {
      trackEvent: (eventName, data) => {
        analytics.track(`${trackingId}_${eventName}`, data);
      },
    };

    // Spread consumer props LAST so they can override if needed intentionally
    return <WrappedComponent ref={ref} {...analyticsProps} {...props} />;
  });

  // 3. Preserve displayName for DevTools
  WithAnalytics.displayName =
    `withAnalytics(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;

  // 4. Copy static methods (or use hoist-non-react-statics)
  // Manual approach:
  if (WrappedComponent.getInitialData) {
    WithAnalytics.getInitialData = WrappedComponent.getInitialData;
  }
  // Better: use the hoist-non-react-statics library
  // hoistNonReactStatics(WithAnalytics, WrappedComponent);

  return WithAnalytics;
}

// Usage
const TrackedCheckoutForm = withAnalytics(CheckoutForm, 'checkout');

// Now refs work correctly:
function PaymentPage() {
  const formRef = useRef(null);

  const handleSubmit = () => {
    // formRef.current points to CheckoutForm's imperative handle or DOM node
    formRef.current.validate();
  };

  return <TrackedCheckoutForm ref={formRef} onSubmit={handleSubmit} />;
}
```

**Modern alternative:** In React 18, the cleanest way to avoid all HOC pitfalls is to convert the HOC logic into a custom hook. If you *must* use an HOC (e.g., to wrap JSX), always use `forwardRef`, set `displayName`, and use `hoist-non-react-statics` to copy static methods.

---

### Q10. How does the Render Props pattern work when using `children` as a function, and what are the performance considerations in React 18?

**Answer:**

The "children as a function" variant of render props uses the `children` prop itself as the render function, instead of a separate named prop. This produces slightly cleaner JSX for the consumer (no explicit `render=` prop), and the pattern is widely used in libraries like React Spring, Downshift, and Formik.

The performance concern is that a new inline function is created on every render of the parent, which means the render-prop component receives a new `children` reference each time. In React 18 with automatic batching, this is less problematic than it was, but for high-frequency updates (e.g., tracking mouse position at 60fps), it can cause excessive re-renders.

```jsx
import { useState, useEffect, useCallback, memo, useMemo } from 'react';

// --- Render Props with children-as-a-function ---
function WindowSize({ children }) {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const handler = () => {
      setSize({ width: window.innerWidth, height: window.innerHeight });
    };
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  // children is a function: call it with the state
  return children(size);
}

// --- Consumer uses it with children as a function ---
function ResponsiveLayout() {
  return (
    <WindowSize>
      {({ width, height }) => (
        <div>
          {width > 768 ? <DesktopNav /> : <MobileNav />}
          <main style={{ minHeight: height - 64 }}>
            <Outlet />
          </main>
        </div>
      )}
    </WindowSize>
  );
}
```

**Performance optimisation strategies:**

```jsx
// PROBLEM: Inline function creates a new reference every render,
// preventing memo from working on child elements.
function App() {
  const [count, setCount] = useState(0);

  return (
    <>
      <button onClick={() => setCount((c) => c + 1)}>Count: {count}</button>
      <WindowSize>
        {/* This function is re-created every time count changes,
            even though it doesn't use count */}
        {({ width }) => <Sidebar width={width} />}
      </WindowSize>
    </>
  );
}

// SOLUTION 1: Extract the render function to a stable reference
function App() {
  const [count, setCount] = useState(0);

  // Stable: only re-created if deps change (none here)
  const renderSidebar = useCallback(
    ({ width }) => <Sidebar width={width} />,
    []
  );

  return (
    <>
      <button onClick={() => setCount((c) => c + 1)}>Count: {count}</button>
      <WindowSize>{renderSidebar}</WindowSize>
    </>
  );
}

// SOLUTION 2 (preferred in React 18): Just use a custom hook
function useWindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });
  useEffect(() => {
    const handler = () =>
      setSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);
  return size;
}

function App() {
  const { width } = useWindowSize();
  return <Sidebar width={width} />;
}
```

In React 18, `useCallback` and `useMemo` are free to use as optimisation hints (React may even auto-memoize in the future with the React Compiler). The bottom line: use render props when you need them for UI slots, but prefer custom hooks for pure stateful logic.

---

### Q11. What is the State Reducer pattern, and how does it give component consumers control over internal state transitions?

**Answer:**

The State Reducer pattern, popularised by Kent C. Dodds, allows the consumer of a reusable component to **intercept and modify state changes** without the component needing to expose every possible customisation via props. The component defines its default state transitions (in a reducer), and the consumer can pass a `stateReducer` prop that wraps or replaces specific transitions. This is a powerful form of **inversion of control** — the component owns the *shape* of state and the *set of actions*, but the consumer controls the *outcome* of each action.

This pattern is used in production libraries like Downshift (`useSelect`, `useCombobox`) and is invaluable for building reusable components where you cannot anticipate every use case at design time.

```jsx
import { useReducer, useCallback } from 'react';

// --- 1. Define action types and default reducer ---
const actionTypes = {
  TOGGLE: 'TOGGLE',
  OPEN: 'OPEN',
  CLOSE: 'CLOSE',
  RESET: 'RESET',
};

function defaultReducer(state, action) {
  switch (action.type) {
    case actionTypes.TOGGLE:
      return { ...state, isOpen: !state.isOpen };
    case actionTypes.OPEN:
      return { ...state, isOpen: true };
    case actionTypes.CLOSE:
      return { ...state, isOpen: false };
    case actionTypes.RESET:
      return { ...state, isOpen: false };
    default:
      return state;
  }
}

// --- 2. Hook that accepts an optional stateReducer ---
function useDisclosure({ initialOpen = false, stateReducer = defaultReducer } = {}) {
  const [state, dispatch] = useReducer(
    // Wrap: call the consumer's reducer, falling back to default
    (state, action) => stateReducer(state, action, defaultReducer),
    { isOpen: initialOpen }
  );

  const toggle = useCallback(() => dispatch({ type: actionTypes.TOGGLE }), []);
  const open = useCallback(() => dispatch({ type: actionTypes.OPEN }), []);
  const close = useCallback(() => dispatch({ type: actionTypes.CLOSE }), []);
  const reset = useCallback(() => dispatch({ type: actionTypes.RESET }), []);

  return { ...state, toggle, open, close, reset, actionTypes };
}

// --- 3. Default usage (no customisation) ---
function SimpleModal() {
  const { isOpen, toggle } = useDisclosure();

  return (
    <>
      <button onClick={toggle}>Toggle Modal</button>
      {isOpen && <div className="modal">Modal Content</div>}
    </>
  );
}

// --- 4. Consumer overrides: prevent closing unless a condition is met ---
function UnsavedChangesModal() {
  const { isOpen, toggle, open, close } = useDisclosure({
    stateReducer: (state, action, defaultReducer) => {
      // Intercept CLOSE and TOGGLE-to-close: require confirmation
      if (
        action.type === actionTypes.CLOSE ||
        (action.type === actionTypes.TOGGLE && state.isOpen)
      ) {
        const hasUnsavedChanges = checkForUnsavedChanges(); // app logic
        if (hasUnsavedChanges) {
          const confirmed = window.confirm('You have unsaved changes. Discard?');
          if (!confirmed) return state; // block the state change
        }
      }
      // For all other actions, use default behaviour
      return defaultReducer(state, action);
    },
  });

  return (
    <>
      <button onClick={open}>Edit Settings</button>
      {isOpen && (
        <div className="modal">
          <SettingsForm />
          <button onClick={close}>Close</button>
        </div>
      )}
    </>
  );
}
```

The critical design choice is passing `defaultReducer` as the third argument to the consumer's state reducer. This lets the consumer selectively override only specific transitions while delegating everything else to the default. Without this, the consumer would have to re-implement the entire reducer.

---

### Q12. What is the Props Getter pattern, and how does it help safely merge consumer props with component-internal props?

**Answer:**

The Props Getter pattern exposes a function (e.g., `getToggleProps`, `getInputProps`) that returns a complete set of props to spread onto a DOM element. The function handles merging the component's required internal props (event handlers, ARIA attributes, roles) with any additional props the consumer passes in. This prevents a common bug where spreading user props accidentally overwrites an internal `onClick` handler, for example.

This pattern is heavily used in Downshift, React Table (TanStack Table), and other headless UI libraries. It pairs naturally with the State Reducer pattern.

```jsx
import { useState, useCallback } from 'react';

// --- Utility: safely merge multiple event handlers ---
function callAll(...fns) {
  return (...args) => {
    fns.forEach((fn) => fn?.(...args));
  };
}

// --- Hook exposing props getters ---
function useToggle({ initialOn = false, onToggle } = {}) {
  const [on, setOn] = useState(initialOn);

  const toggle = useCallback(() => {
    setOn((prev) => {
      const next = !prev;
      onToggle?.(next);
      return next;
    });
  }, [onToggle]);

  // Props getter for the toggle button
  const getTogglerProps = useCallback(
    ({ onClick, ...restProps } = {}) => ({
      'aria-pressed': on,
      role: 'switch',
      onClick: callAll(onClick, toggle), // merge consumer's onClick with internal toggle
      ...restProps,
    }),
    [on, toggle]
  );

  // Props getter for the content area
  const getContentProps = useCallback(
    (props = {}) => ({
      role: 'region',
      hidden: !on,
      'aria-hidden': !on,
      ...props,
    }),
    [on]
  );

  return { on, toggle, getTogglerProps, getContentProps };
}

// --- Consumer ---
function FAQ({ question, answer }) {
  const { on, getTogglerProps, getContentProps } = useToggle();

  return (
    <div className="faq-item">
      {/* Consumer adds their own onClick AND className — both are preserved */}
      <button
        {...getTogglerProps({
          onClick: () => analytics.track('faq_toggled', { question }),
          className: `faq-question ${on ? 'expanded' : ''}`,
        })}
      >
        {question}
        <span>{on ? '−' : '+'}</span>
      </button>

      <div
        {...getContentProps({
          className: 'faq-answer',
          'data-testid': 'faq-answer',
        })}
      >
        {answer}
      </div>
    </div>
  );
}

// --- Usage ---
function HelpPage() {
  return (
    <div className="faq-list">
      <FAQ question="How do I reset my password?" answer="Go to Settings > Security..." />
      <FAQ question="What payment methods do you accept?" answer="Visa, Mastercard, PayPal..." />
    </div>
  );
}
```

The `callAll` utility is the key insight: instead of having the consumer choose between their `onClick` and the component's `onClick`, `getTogglerProps` merges them so both fire. This is safer than asking the consumer to remember to call an internal handler — the merge happens automatically. The consumer's additional props are spread last so they can override non-critical props (like `className`) while handlers are always composed.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you build Compound Components with implicit state sharing using Context, and what are the trade-offs compared to using `React.Children` and `cloneElement`?

**Answer:**

There are two approaches to implementing compound components in React:

**Approach 1: `React.Children.map` + `cloneElement`** — The parent iterates over its children and clones each one, injecting additional props. This was common before hooks and Context, and it still works, but it has significant limitations:
- Only works for **direct children** — if the consumer wraps a sub-component in a `<div>` or fragment, the clone misses it.
- **Brittle** — it relies on matching component types via `child.type`, which breaks with HOCs, `memo`, or `forwardRef`.
- **Opaque** — the consumer doesn't know which props are being injected.

**Approach 2: Context (recommended)** — The parent provides state through Context, and sub-components consume it with `useContext`. This works at any depth, is not affected by wrapping elements, and is fully type-safe with TypeScript.

```jsx
import {
  createContext,
  useContext,
  useState,
  useCallback,
  Children,
  cloneElement,
  isValidElement,
} from 'react';

// ================================================================
// APPROACH 1: cloneElement (legacy, shown for comparison)
// ================================================================
function AccordionLegacy({ children }) {
  const [openIndex, setOpenIndex] = useState(null);

  return (
    <div className="accordion">
      {Children.map(children, (child, index) => {
        if (!isValidElement(child)) return child;
        // Inject props into direct children only — fragile!
        return cloneElement(child, {
          isOpen: openIndex === index,
          onToggle: () => setOpenIndex(openIndex === index ? null : index),
        });
      })}
    </div>
  );
}

// This breaks if consumer wraps items:
// <AccordionLegacy>
//   <div className="group">              ← not an AccordionItem, clone fails
//     <AccordionItemLegacy title="A">... ← never receives isOpen
//   </div>
// </AccordionLegacy>

// ================================================================
// APPROACH 2: Context-based (robust, production-grade)
// ================================================================
const AccordionContext = createContext(null);

function useAccordion() {
  const ctx = useContext(AccordionContext);
  if (!ctx) throw new Error('Accordion sub-components must be inside <Accordion>');
  return ctx;
}

function Accordion({ type = 'single', children }) {
  // 'single' = only one item open at a time; 'multiple' = many can be open
  const [openItems, setOpenItems] = useState(new Set());

  const toggle = useCallback(
    (value) => {
      setOpenItems((prev) => {
        const next = new Set(prev);
        if (next.has(value)) {
          next.delete(value);
        } else {
          if (type === 'single') next.clear(); // close others
          next.add(value);
        }
        return next;
      });
    },
    [type]
  );

  const isOpen = useCallback(
    (value) => openItems.has(value),
    [openItems]
  );

  return (
    <AccordionContext.Provider value={{ toggle, isOpen }}>
      <div className="accordion" role="region">
        {children}
      </div>
    </AccordionContext.Provider>
  );
}

function AccordionItem({ value, children }) {
  const { isOpen } = useAccordion();
  return (
    <div className="accordion-item" data-state={isOpen(value) ? 'open' : 'closed'}>
      {children}
    </div>
  );
}

function AccordionTrigger({ value, children }) {
  const { toggle, isOpen } = useAccordion();
  return (
    <button
      className="accordion-trigger"
      aria-expanded={isOpen(value)}
      onClick={() => toggle(value)}
    >
      {children}
      <span className="icon">{isOpen(value) ? '−' : '+'}</span>
    </button>
  );
}

function AccordionContent({ value, children }) {
  const { isOpen } = useAccordion();
  if (!isOpen(value)) return null;
  return (
    <div className="accordion-content" role="region">
      {children}
    </div>
  );
}

Accordion.Item = AccordionItem;
Accordion.Trigger = AccordionTrigger;
Accordion.Content = AccordionContent;

// --- Consumer: wrapping in custom divs works perfectly ---
function FAQSection() {
  return (
    <Accordion type="single">
      <div className="faq-group">
        <Accordion.Item value="q1">
          <Accordion.Trigger value="q1">What is your refund policy?</Accordion.Trigger>
          <Accordion.Content value="q1">
            We offer a 30-day money-back guarantee...
          </Accordion.Content>
        </Accordion.Item>
      </div>
      <div className="faq-group">
        <Accordion.Item value="q2">
          <Accordion.Trigger value="q2">How do I contact support?</Accordion.Trigger>
          <Accordion.Content value="q2">
            Email us at support@example.com...
          </Accordion.Content>
        </Accordion.Item>
      </div>
    </Accordion>
  );
}
```

**Trade-off summary:**

| | `cloneElement` | Context |
|---|---|---|
| Works with nested wrappers | No | Yes |
| TypeScript friendly | Requires casts | Fully typed |
| Performance | Clones on every render | Context subscription |
| Works with `memo`/`forwardRef` | Can break | Works fine |
| Explicit data flow | No (magic props) | Yes (via hook) |

The Context-based approach is the production standard in React 18. Reserve `cloneElement` only for very simple cases where children are always direct and you need to avoid the boilerplate of creating a Context.

---

### Q14. What is the Polymorphic Component pattern (the `as` prop), and how do you implement it with proper TypeScript-level type safety?

**Answer:**

A polymorphic component is a component that can render as different HTML elements or other React components, controlled by an `as` (or `component`) prop. This pattern is ubiquitous in design systems (Chakra UI's `<Box as="section">`, MUI's `component` prop, Radix Primitives' `asChild`) because it lets a single styled component adapt to any semantic HTML context without duplicating styles.

The challenge is **type safety**: when the consumer writes `<Button as="a" href="/about">`, TypeScript should know that `href` is valid because the rendered element is `<a>`, but `<Button as="button" href="/about">` should error because `<button>` doesn't accept `href`.

```jsx
import { forwardRef } from 'react';

// ================================================================
// JavaScript implementation (runtime-safe, no TS types shown)
// ================================================================
const Box = forwardRef(function Box({ as: Component = 'div', children, ...rest }, ref) {
  return (
    <Component ref={ref} {...rest}>
      {children}
    </Component>
  );
});

// Usage: renders a <section> with all valid section attributes
function HeroSection() {
  return (
    <Box as="section" className="hero" aria-label="Hero section">
      <Box as="h1" className="hero-title">Welcome</Box>
      <Box as="p" className="hero-subtitle">Build amazing things.</Box>
    </Box>
  );
}
```

```jsx
// ================================================================
// TypeScript implementation with full polymorphic type safety
// ================================================================

// 1. Generic type that extracts valid props based on the "as" element type
// (Shown as JSX comments for clarity in this .md file)

// type PolymorphicRef<C extends React.ElementType> =
//   React.ComponentPropsWithRef<C>['ref'];
//
// type PolymorphicProps<C extends React.ElementType, Props = {}> = Props &
//   Omit<React.ComponentPropsWithoutRef<C>, keyof Props> & {
//     as?: C;
//     ref?: PolymorphicRef<C>;
//   };

// 2. The component
const Button = forwardRef(function Button({ as, variant = 'primary', children, ...rest }, ref) {
  const Component = as || 'button';

  return (
    <Component
      ref={ref}
      className={`btn btn-${variant}`}
      {...(Component === 'button' ? { type: 'button' } : {})}
      {...rest}
    >
      {children}
    </Component>
  );
});

// 3. Consumer usage — TypeScript enforces correct props per element type
function Navigation() {
  return (
    <nav>
      {/* Renders as <button> — onClick is valid */}
      <Button variant="primary" onClick={() => console.log('clicked')}>
        Click Me
      </Button>

      {/* Renders as <a> — href is valid */}
      <Button as="a" href="/dashboard" variant="secondary">
        Go to Dashboard
      </Button>

      {/* Renders as a React Router Link — "to" is valid */}
      <Button as={Link} to="/settings" variant="ghost">
        Settings
      </Button>

      {/* TypeScript ERROR: href is not valid on <button>
      <Button as="button" href="/oops">Bad</Button>
      */}
    </nav>
  );
}
```

**Production considerations:**
- **Default element:** Always provide a sensible default (e.g., `'div'` or `'button'`) so consumers don't have to specify `as` every time.
- **Ref forwarding:** Use `forwardRef` so the ref targets the actual rendered element.
- **Conditional default props:** When the default is `'button'`, inject `type="button"` to prevent accidental form submissions — but don't inject it when `as` is `'a'`.
- **`asChild` alternative (Radix approach):** Instead of an `as` prop, Radix uses `asChild` which clones the single child and merges props into it. This avoids the TypeScript complexity entirely but requires the consumer to always provide a child element.

---

### Q15. What is the Headless UI pattern, and how does it separate logic from presentation? Build a headless `useCombobox` hook.

**Answer:**

The Headless UI pattern provides **all the logic, state management, keyboard interactions, and accessibility** of a complex component, but renders **zero UI**. The consumer provides all the markup, styling, and visual structure. This achieves maximum flexibility: the same headless engine powers a dropdown in a corporate design system, a mobile app, and a CLI tool with completely different visual implementations.

Libraries like Headless UI (Tailwind Labs), Radix Primitives, Downshift, TanStack Table, and React Aria are built on this pattern. They typically expose:
1. A custom hook (or set of hooks) returning state and props getters
2. Zero opinions about CSS, class names, or DOM structure
3. Full ARIA compliance and keyboard navigation built-in

Here is a simplified but production-aware headless `useCombobox` hook:

```jsx
import { useState, useRef, useCallback, useMemo, useId, useEffect } from 'react';

function useCombobox({ items, onSelect, itemToString = (item) => String(item) }) {
  const [inputValue, setInputValue] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef(null);
  const listboxId = useId();

  // Filter items based on input
  const filteredItems = useMemo(
    () =>
      items.filter((item) =>
        itemToString(item).toLowerCase().includes(inputValue.toLowerCase())
      ),
    [items, inputValue, itemToString]
  );

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setIsOpen(true);
          setHighlightedIndex((prev) =>
            prev < filteredItems.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev > 0 ? prev - 1 : filteredItems.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (highlightedIndex >= 0 && filteredItems[highlightedIndex]) {
            const selected = filteredItems[highlightedIndex];
            setInputValue(itemToString(selected));
            onSelect?.(selected);
            setIsOpen(false);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          setHighlightedIndex(-1);
          break;
      }
    },
    [filteredItems, highlightedIndex, itemToString, onSelect]
  );

  // Reset highlight when filtered items change
  useEffect(() => {
    setHighlightedIndex(-1);
  }, [filteredItems.length]);

  // --- Props Getters ---
  const getInputProps = useCallback(
    ({ onChange, onKeyDown, onFocus, ...rest } = {}) => ({
      role: 'combobox',
      'aria-expanded': isOpen,
      'aria-controls': listboxId,
      'aria-activedescendant':
        highlightedIndex >= 0 ? `${listboxId}-option-${highlightedIndex}` : undefined,
      autoComplete: 'off',
      value: inputValue,
      ref: inputRef,
      onChange: (e) => {
        setInputValue(e.target.value);
        setIsOpen(true);
        onChange?.(e);
      },
      onKeyDown: (e) => {
        handleKeyDown(e);
        onKeyDown?.(e);
      },
      onFocus: (e) => {
        setIsOpen(true);
        onFocus?.(e);
      },
      ...rest,
    }),
    [isOpen, listboxId, highlightedIndex, inputValue, handleKeyDown]
  );

  const getListboxProps = useCallback(
    (props = {}) => ({
      role: 'listbox',
      id: listboxId,
      ...props,
    }),
    [listboxId]
  );

  const getItemProps = useCallback(
    ({ item, index, onClick, ...rest } = {}) => ({
      role: 'option',
      id: `${listboxId}-option-${index}`,
      'aria-selected': highlightedIndex === index,
      onClick: (e) => {
        setInputValue(itemToString(item));
        onSelect?.(item);
        setIsOpen(false);
        onClick?.(e);
      },
      onMouseEnter: () => setHighlightedIndex(index),
      ...rest,
    }),
    [listboxId, highlightedIndex, itemToString, onSelect]
  );

  return {
    inputValue,
    isOpen,
    highlightedIndex,
    filteredItems,
    getInputProps,
    getListboxProps,
    getItemProps,
    setIsOpen,
    setInputValue,
  };
}

// --- Consumer provides ALL the UI ---
function CountrySearch({ countries, onCountrySelect }) {
  const {
    isOpen,
    filteredItems,
    highlightedIndex,
    getInputProps,
    getListboxProps,
    getItemProps,
  } = useCombobox({
    items: countries,
    onSelect: onCountrySelect,
    itemToString: (country) => country.name,
  });

  return (
    <div className="combobox-wrapper">
      <input
        {...getInputProps({
          placeholder: 'Search countries...',
          className: 'combobox-input',
        })}
      />

      {isOpen && filteredItems.length > 0 && (
        <ul {...getListboxProps({ className: 'combobox-listbox' })}>
          {filteredItems.map((country, index) => (
            <li
              key={country.code}
              {...getItemProps({
                item: country,
                index,
                className: `combobox-option ${
                  highlightedIndex === index ? 'highlighted' : ''
                }`,
              })}
            >
              <span className="flag">{country.flag}</span>
              <span>{country.name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

The hook provides behaviour, accessibility, and keyboard navigation. The consumer provides every DOM element, class name, and visual detail. This is the gold standard for building reusable components in a design system that must serve multiple products with different visual identities.

---

### Q16. What is the Layout Component pattern, and how do you design page layouts with named slots for a production application?

**Answer:**

The Layout Component pattern creates reusable page scaffolds with predefined regions (slots) where consumers inject their own content. Unlike CSS-only layouts, layout components can encapsulate responsive behaviour, scroll management, sidebar collapse/expand state, and breakpoint-driven rendering — all in one composable unit. This pattern is especially powerful in applications with multiple layout variants (admin dashboard, public marketing pages, onboarding flows) that share structural elements.

```jsx
import { createContext, useContext, useState, useCallback } from 'react';

// --- 1. Sidebar state shared via Context ---
const LayoutContext = createContext(null);

function useLayout() {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error('useLayout must be used within a LayoutProvider');
  return ctx;
}

// --- 2. Core layout component with named slots ---
function DashboardLayout({ nav, sidebar, header, footer, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const toggleSidebar = useCallback(() => setSidebarOpen((prev) => !prev), []);

  return (
    <LayoutContext.Provider value={{ sidebarOpen, toggleSidebar }}>
      <div
        className="dashboard-layout"
        style={{
          display: 'grid',
          gridTemplateColumns: sidebarOpen ? '260px 1fr' : '60px 1fr',
          gridTemplateRows: 'auto 1fr auto',
          gridTemplateAreas: `
            "sidebar header"
            "sidebar main"
            "sidebar footer"
          `,
          minHeight: '100vh',
          transition: 'grid-template-columns 0.2s ease',
        }}
      >
        <header style={{ gridArea: 'header' }} className="layout-header">
          {header}
        </header>

        <aside style={{ gridArea: 'sidebar' }} className="layout-sidebar">
          {nav}
          {sidebar}
        </aside>

        <main style={{ gridArea: 'main' }} className="layout-main">
          {children}
        </main>

        <footer style={{ gridArea: 'footer' }} className="layout-footer">
          {footer}
        </footer>
      </div>
    </LayoutContext.Provider>
  );
}

// --- 3. Slot components that consume layout state ---
function SidebarToggle() {
  const { sidebarOpen, toggleSidebar } = useLayout();
  return (
    <button onClick={toggleSidebar} aria-label="Toggle sidebar">
      {sidebarOpen ? '◀' : '▶'}
    </button>
  );
}

// --- 4. Consumer wires everything together ---
function AdminApp() {
  const { user } = useAuthState();

  return (
    <DashboardLayout
      nav={<MainNavigation role={user.role} />}
      sidebar={
        <>
          <SidebarToggle />
          <SidebarFilters />
        </>
      }
      header={
        <div className="header-content">
          <Breadcrumbs />
          <UserMenu user={user} />
        </div>
      }
      footer={<AppFooter version="2.4.0" />}
    >
      {/* children = main content area, driven by router */}
      <Outlet />
    </DashboardLayout>
  );
}

// --- 5. Different layout for public pages — same pattern, different structure ---
function PublicLayout({ hero, children }) {
  return (
    <div className="public-layout">
      <PublicNavbar />
      {hero && <section className="hero-slot">{hero}</section>}
      <main className="public-main">{children}</main>
      <PublicFooter />
    </div>
  );
}

function LandingPage() {
  return (
    <PublicLayout hero={<HeroBanner />}>
      <FeatureGrid />
      <Testimonials />
      <PricingTable />
    </PublicLayout>
  );
}
```

**Production considerations:**
- **Responsive slots:** Use `useMediaQuery` or CSS container queries to conditionally render slot content (e.g., hide the sidebar below 768px and show a hamburger menu in the header instead).
- **Skeleton layouts:** Define a `DashboardLayoutSkeleton` that mirrors the grid structure with placeholder shimmer elements, for use during route transitions with `Suspense`.
- **Type safety:** Define a `LayoutProps` interface that documents each slot prop, making it clear what the layout expects.
- **Layout routes:** In React Router v6, layouts are best expressed as parent routes with `<Outlet>`, which naturally maps to this pattern.

---

### Q17. What is the Builder pattern for complex component configuration, and how does it improve the API ergonomics of components with many options?

**Answer:**

The Builder pattern provides a fluent, chainable API for constructing complex component configurations, avoiding "prop explosion" (components with 20+ props that are hard to read and maintain). Instead of passing a massive props object, consumers build up a configuration step by step using method chaining or a builder object, then pass the final configuration to the component.

This pattern is common in non-React JavaScript (e.g., Knex query builder, D3 method chaining) and translates well to React for components like data tables, charts, form builders, and complex modals.

```jsx
import { useMemo } from 'react';

// --- 1. Builder class for table column configuration ---
class ColumnBuilder {
  constructor(key) {
    this._config = {
      key,
      header: key,
      sortable: false,
      filterable: false,
      width: 'auto',
      align: 'left',
      render: null,
      hidden: false,
      pinned: false,
    };
  }

  header(label) {
    this._config.header = label;
    return this; // enable chaining
  }

  sortable(enabled = true) {
    this._config.sortable = enabled;
    return this;
  }

  filterable(enabled = true) {
    this._config.filterable = enabled;
    return this;
  }

  width(value) {
    this._config.width = value;
    return this;
  }

  align(value) {
    this._config.align = value;
    return this;
  }

  render(renderFn) {
    this._config.render = renderFn;
    return this;
  }

  pin(side = 'left') {
    this._config.pinned = side;
    return this;
  }

  hidden(isHidden = true) {
    this._config.hidden = isHidden;
    return this;
  }

  build() {
    return Object.freeze({ ...this._config });
  }
}

// Helper to create a column builder
function column(key) {
  return new ColumnBuilder(key);
}

// --- 2. DataTable component that accepts built column configs ---
function DataTable({ data, columns, onSort, onFilter }) {
  const visibleColumns = useMemo(
    () => columns.filter((col) => !col.hidden),
    [columns]
  );

  return (
    <table className="data-table">
      <thead>
        <tr>
          {visibleColumns.map((col) => (
            <th
              key={col.key}
              style={{ width: col.width, textAlign: col.align }}
              className={col.pinned ? `pinned-${col.pinned}` : ''}
            >
              {col.header}
              {col.sortable && (
                <button onClick={() => onSort?.(col.key)} className="sort-btn">
                  ↕
                </button>
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={row.id ?? i}>
            {visibleColumns.map((col) => (
              <td key={col.key} style={{ textAlign: col.align }}>
                {col.render ? col.render(row[col.key], row) : row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// --- 3. Consumer: fluent column definitions ---
function OrdersTable({ orders }) {
  const columns = useMemo(
    () => [
      column('id')
        .header('Order ID')
        .width('100px')
        .pin('left')
        .sortable()
        .build(),

      column('customer')
        .header('Customer Name')
        .sortable()
        .filterable()
        .build(),

      column('total')
        .header('Total')
        .width('120px')
        .align('right')
        .sortable()
        .render((value) => `$${value.toFixed(2)}`)
        .build(),

      column('status')
        .header('Status')
        .filterable()
        .render((value) => (
          <span className={`badge badge-${value.toLowerCase()}`}>{value}</span>
        ))
        .build(),

      column('createdAt')
        .header('Date')
        .sortable()
        .render((value) => new Date(value).toLocaleDateString())
        .build(),

      column('internalNotes')
        .header('Notes')
        .hidden() // hidden by default, can toggle
        .build(),
    ],
    []
  );

  return <DataTable data={orders} columns={columns} onSort={handleSort} />;
}
```

**Why this is better than a giant props object:**
- **Readability:** Each column is self-documenting — you can see its configuration at a glance.
- **Discoverability:** IDE autocomplete shows available methods on the builder.
- **Composability:** You can create base builders and extend them: `baseColumn('email').filterable().sortable()`.
- **Immutability:** `build()` returns a frozen object, preventing accidental mutation.
- **Reusability:** Column definitions can be shared across tables.

---

### Q18. What is Inversion of Control in component APIs, and how do patterns like State Reducer, Props Getters, and Render Props implement it?

**Answer:**

**Inversion of Control (IoC)** is a design principle where a framework or library calls *your* code rather than your code calling the library. In React component design, IoC means giving consumers progressively more control over a component's behaviour and rendering. Instead of the component author trying to anticipate every use case with configuration props (which leads to prop explosion and rigid APIs), IoC patterns let consumers inject their own logic at strategic extension points.

There is a spectrum of IoC in React component design, from least to most control:

```
Least Control ←────────────────────────────→ Most Control
  Props          Compound         State Reducer     Render Props
  Config         Components       Props Getters     Full Headless
```

Here is a concrete example showing the same `Toggle` component at each IoC level:

```jsx
import { useState, useReducer, useCallback, createContext, useContext } from 'react';

// ================================================================
// Level 1: Configuration Props (least IoC)
// Consumer can only configure predefined options
// ================================================================
function ToggleV1({ label, onToggle, disabled = false }) {
  const [on, setOn] = useState(false);
  const handleClick = () => {
    if (disabled) return;
    setOn((prev) => !prev);
    onToggle?.(!on);
  };
  return (
    <button onClick={handleClick} aria-pressed={on} disabled={disabled}>
      {label}: {on ? 'ON' : 'OFF'}
    </button>
  );
}
// Problem: What if you need a custom label format? A different element? Conditional toggling?

// ================================================================
// Level 2: Compound Components (more IoC)
// Consumer controls structure and composition
// ================================================================
const ToggleContext = createContext(null);

function ToggleV2({ children, onToggle }) {
  const [on, setOn] = useState(false);
  const toggle = useCallback(() => {
    setOn((prev) => {
      onToggle?.(!prev);
      return !prev;
    });
  }, [onToggle]);
  return (
    <ToggleContext.Provider value={{ on, toggle }}>
      {children}
    </ToggleContext.Provider>
  );
}
ToggleV2.Button = function ToggleButton(props) {
  const { on, toggle } = useContext(ToggleContext);
  return <button onClick={toggle} aria-pressed={on} {...props} />;
};
ToggleV2.Status = function ToggleStatus() {
  const { on } = useContext(ToggleContext);
  return <span>{on ? '🟢 Active' : '🔴 Inactive'}</span>;
};

// ================================================================
// Level 3: State Reducer (consumer controls state logic)
// ================================================================
function toggleReducer(state, action) {
  switch (action.type) {
    case 'TOGGLE': return { on: !state.on };
    case 'ON': return { on: true };
    case 'OFF': return { on: false };
    default: return state;
  }
}

function useToggleV3({ reducer = toggleReducer } = {}) {
  const [state, dispatch] = useReducer(
    (state, action) => reducer(state, action, toggleReducer),
    { on: false }
  );
  const toggle = () => dispatch({ type: 'TOGGLE' });
  return { on: state.on, toggle };
}

// Consumer overrides: limit toggles to 4 times
function LimitedToggle() {
  const [count, setCount] = useState(0);
  const { on, toggle } = useToggleV3({
    reducer: (state, action, defaultReducer) => {
      if (action.type === 'TOGGLE' && count >= 4) return state; // block!
      if (action.type === 'TOGGLE') setCount((c) => c + 1);
      return defaultReducer(state, action);
    },
  });
  return (
    <button onClick={toggle}>
      {on ? 'ON' : 'OFF'} (toggled {count}/4)
    </button>
  );
}

// ================================================================
// Level 4: Props Getters (consumer controls DOM mapping)
// ================================================================
function useToggleV4() {
  const [on, setOn] = useState(false);
  const toggle = useCallback(() => setOn((prev) => !prev), []);

  const getTogglerProps = ({ onClick, ...rest } = {}) => ({
    'aria-pressed': on,
    onClick: (...args) => { onClick?.(...args); toggle(); },
    ...rest,
  });

  return { on, toggle, getTogglerProps };
}

// ================================================================
// Level 5: Full Headless / Render Props (maximum IoC)
// Consumer controls everything
// ================================================================
function useToggleV5() {
  const [on, setOn] = useState(false);
  const toggle = useCallback(() => setOn((prev) => !prev), []);
  return { on, toggle, setOn }; // raw state and setters
}

function SettingsPage() {
  const { on, toggle, setOn } = useToggleV5();

  // Full control: render whatever you want, wire events however you want
  return (
    <div className="setting-row">
      <label htmlFor="darkMode">Dark Mode</label>
      <div
        id="darkMode"
        role="switch"
        aria-checked={on}
        tabIndex={0}
        onClick={toggle}
        onKeyDown={(e) => e.key === 'Enter' && toggle()}
        className={`toggle-track ${on ? 'on' : 'off'}`}
      >
        <div className="toggle-thumb" />
      </div>
      <button onClick={() => setOn(false)}>Reset</button>
    </div>
  );
}
```

**The key insight:** As you move right on the IoC spectrum, the component becomes more flexible but also shifts more responsibility to the consumer. A good API starts with sensible defaults (low IoC) and progressively exposes more control for advanced use cases. Headless UI libraries live at the far right; opinionated component libraries like Ant Design live at the far left. The best production APIs — like Radix, Downshift, and TanStack — offer escape hatches at every level.

---

### Q19. What is Feature-Sliced Design (FSD) architecture, and how does it organise components, hooks, and business logic in a large-scale React application?

**Answer:**

Feature-Sliced Design (FSD) is a front-end architectural methodology that organises code by **layers** (levels of abstraction) and **slices** (business domains), enforcing strict dependency rules. Unlike "folder-by-type" (putting all components in `/components`, all hooks in `/hooks`) or ad-hoc "folder-by-feature," FSD provides a formal, scalable structure with clear import boundaries that prevent spaghetti dependencies as a codebase grows.

**The FSD Layers (from top to bottom — higher layers can only import from lower layers):**

| Layer | Purpose | Example |
|---|---|---|
| `app/` | App-wide setup: providers, router, global styles | `app/providers.jsx`, `app/router.jsx` |
| `pages/` | Full page compositions, route entry points | `pages/dashboard/`, `pages/settings/` |
| `widgets/` | Large composite UI blocks used on pages | `widgets/user-table/`, `widgets/sidebar/` |
| `features/` | User interactions, business actions | `features/auth/login/`, `features/cart/add-to-cart/` |
| `entities/` | Business entities with their data models and UI | `entities/user/`, `entities/product/`, `entities/order/` |
| `shared/` | Reusable utilities, UI kit, configs — no business logic | `shared/ui/`, `shared/lib/`, `shared/api/` |

**The strict rule:** Each layer can only import from layers **below** it. A `feature` can import from `entities` and `shared`, but never from `widgets` or `pages`. This prevents circular dependencies and ensures clear data flow.

```jsx
// ================================================================
// Project Structure (Feature-Sliced Design)
// ================================================================

// src/
// ├── app/
// │   ├── providers.jsx          ← wraps all global providers
// │   ├── router.jsx             ← route definitions
// │   └── global.css
// ├── pages/
// │   ├── dashboard/
// │   │   └── ui/DashboardPage.jsx
// │   └── orders/
// │       └── ui/OrdersPage.jsx
// ├── widgets/
// │   ├── order-table/
// │   │   ├── ui/OrderTable.jsx
// │   │   └── index.js
// │   └── header/
// │       ├── ui/Header.jsx
// │       └── index.js
// ├── features/
// │   ├── auth/
// │   │   ├── login/
// │   │   │   ├── ui/LoginForm.jsx
// │   │   │   ├── model/useLogin.js
// │   │   │   └── index.js
// │   │   └── logout/
// │   │       ├── ui/LogoutButton.jsx
// │   │       └── index.js
// │   └── order/
// │       ├── create-order/
// │       │   ├── ui/CreateOrderForm.jsx
// │       │   ├── model/useCreateOrder.js
// │       │   └── index.js
// │       └── cancel-order/
// │           ├── ui/CancelOrderButton.jsx
// │           ├── model/useCancelOrder.js
// │           └── index.js
// ├── entities/
// │   ├── user/
// │   │   ├── ui/UserCard.jsx
// │   │   ├── model/types.js
// │   │   ├── api/userApi.js
// │   │   └── index.js
// │   └── order/
// │       ├── ui/OrderRow.jsx
// │       ├── model/types.js
// │       ├── api/orderApi.js
// │       └── index.js
// └── shared/
//     ├── ui/
//     │   ├── Button.jsx
//     │   ├── Input.jsx
//     │   ├── Modal.jsx
//     │   └── DataTable.jsx
//     ├── lib/
//     │   ├── formatCurrency.js
//     │   └── cn.js               ← className merge utility
//     └── api/
//         └── apiClient.js

// ================================================================
// Example: entities/order — reusable order data and display
// ================================================================

// entities/order/api/orderApi.js
import { apiClient } from '@/shared/api/apiClient';

export const orderApi = {
  getAll: (params) => apiClient.get('/orders', { params }),
  getById: (id) => apiClient.get(`/orders/${id}`),
  cancel: (id) => apiClient.post(`/orders/${id}/cancel`),
};

// entities/order/ui/OrderRow.jsx
import { formatCurrency } from '@/shared/lib/formatCurrency';

export function OrderRow({ order, actions }) {
  return (
    <tr>
      <td>{order.id}</td>
      <td>{order.customerName}</td>
      <td>{formatCurrency(order.total)}</td>
      <td>
        <span className={`badge badge-${order.status}`}>{order.status}</span>
      </td>
      <td>{actions}</td> {/* slot for feature-level actions */}
    </tr>
  );
}

// ================================================================
// Example: features/order/cancel-order — a specific user action
// ================================================================

// features/order/cancel-order/model/useCancelOrder.js
import { useState, useCallback } from 'react';
import { orderApi } from '@/entities/order'; // ✅ feature imports from entity

export function useCancelOrder() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const cancelOrder = useCallback(async (orderId) => {
    setIsLoading(true);
    setError(null);
    try {
      await orderApi.cancel(orderId);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { cancelOrder, isLoading, error };
}

// features/order/cancel-order/ui/CancelOrderButton.jsx
import { useCancelOrder } from '../model/useCancelOrder';
import { Button } from '@/shared/ui/Button'; // ✅ feature imports from shared

export function CancelOrderButton({ orderId, onCancelled }) {
  const { cancelOrder, isLoading } = useCancelOrder();

  const handleClick = async () => {
    if (window.confirm('Cancel this order?')) {
      await cancelOrder(orderId);
      onCancelled?.();
    }
  };

  return (
    <Button variant="danger" onClick={handleClick} disabled={isLoading}>
      {isLoading ? 'Cancelling...' : 'Cancel Order'}
    </Button>
  );
}

// ================================================================
// Example: widgets/order-table — composes entities + features
// ================================================================

// widgets/order-table/ui/OrderTable.jsx
import { OrderRow } from '@/entities/order';           // ✅ widget imports entity
import { CancelOrderButton } from '@/features/order/cancel-order'; // ✅ widget imports feature

export function OrderTableWidget({ orders, onRefresh }) {
  return (
    <table>
      <thead>
        <tr><th>ID</th><th>Customer</th><th>Total</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        {orders.map((order) => (
          <OrderRow
            key={order.id}
            order={order}
            actions={
              order.status === 'pending' && (
                <CancelOrderButton orderId={order.id} onCancelled={onRefresh} />
              )
            }
          />
        ))}
      </tbody>
    </table>
  );
}
```

**Why FSD works at scale:**
- **No circular dependencies** — the strict layer hierarchy makes them structurally impossible.
- **Easy onboarding** — new developers know exactly where to find and place code.
- **Independent feature development** — teams can work on separate features/entities without stepping on each other.
- **Refactoring safety** — you can delete an entire feature slice and nothing outside that slice breaks.

---

### Q20. How would you architect a production design system that combines compound components, polymorphic rendering, and headless UI patterns? Build a `Button` component that demonstrates this.

**Answer:**

A production design system must satisfy competing demands: it needs to be **accessible by default** (ARIA, keyboard navigation, focus management), **visually customisable** (theming, variants, sizes), **semantically flexible** (render as `<button>`, `<a>`, or a router `<Link>`), **composable** (icons, loading spinners, badges as children), and **incrementally adoptable** (works out of the box with defaults, but every aspect can be overridden).

The architecture that achieves this combines three patterns:
1. **Headless logic layer** — a custom hook (`useButton`) encapsulates focus, disabled state, loading state, and ARIA attributes with zero UI.
2. **Polymorphic rendering** — the `as` prop allows the Button to render as any element or component.
3. **Compound sub-components** — `Button.Icon`, `Button.Spinner` compose cleanly within the button.

Additionally, a **theme provider** (Context) supplies design tokens, and a **`cn` utility** (like `clsx` + `tailwind-merge`) merges class names safely.

```jsx
import {
  createContext,
  useContext,
  forwardRef,
  useMemo,
  useCallback,
} from 'react';

// ================================================================
// 1. SHARED: Theme Provider
// ================================================================
const ThemeContext = createContext({ mode: 'light', radius: 'md' });
function useTheme() { return useContext(ThemeContext); }

function ThemeProvider({ theme, children }) {
  const value = useMemo(() => theme, [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

// ================================================================
// 2. SHARED: className merge utility
// ================================================================
function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

// ================================================================
// 3. HEADLESS: useButton hook — all logic, no UI
// ================================================================
function useButton({
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
} = {}) {
  const isDisabled = disabled || loading;

  const handleClick = useCallback(
    (e) => {
      if (isDisabled) {
        e.preventDefault();
        return;
      }
      onClick?.(e);
    },
    [isDisabled, onClick]
  );

  const getButtonProps = useCallback(
    ({ onClick: userOnClick, ...rest } = {}) => ({
      type,
      disabled: isDisabled,
      'aria-disabled': isDisabled || undefined,
      'aria-busy': loading || undefined,
      onClick: (e) => {
        userOnClick?.(e);
        handleClick(e);
      },
      ...rest,
    }),
    [type, isDisabled, loading, handleClick]
  );

  return { isDisabled, loading, getButtonProps };
}

// ================================================================
// 4. COMPOUND SUB-COMPONENTS
// ================================================================
const ButtonContext = createContext(null);

function ButtonIcon({ children, position = 'left', className }) {
  const ctx = useContext(ButtonContext);
  return (
    <span
      className={cn(
        'btn-icon',
        position === 'left' ? 'btn-icon-left' : 'btn-icon-right',
        ctx?.loading && 'btn-icon-hidden',
        className
      )}
      aria-hidden="true"
    >
      {children}
    </span>
  );
}

function ButtonSpinner({ className }) {
  return (
    <span className={cn('btn-spinner', className)} aria-hidden="true">
      <svg className="animate-spin" viewBox="0 0 24 24" width="16" height="16">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"
          fill="none" opacity="0.25" />
        <path fill="currentColor" opacity="0.75"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </span>
  );
}

// ================================================================
// 5. POLYMORPHIC BUTTON — ties everything together
// ================================================================
const VARIANT_CLASSES = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  danger: 'btn-danger',
  ghost: 'btn-ghost',
  link: 'btn-link',
};

const SIZE_CLASSES = {
  sm: 'btn-sm',
  md: 'btn-md',
  lg: 'btn-lg',
};

const Button = forwardRef(function Button(
  {
    as,
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    fullWidth = false,
    className,
    children,
    onClick,
    type = 'button',
    ...rest
  },
  ref
) {
  // Determine rendered element
  const Component = as || 'button';

  // Headless logic
  const { isDisabled, getButtonProps } = useButton({
    disabled,
    loading,
    onClick,
    type,
  });

  // Build class names
  const classes = cn(
    'btn',
    VARIANT_CLASSES[variant],
    SIZE_CLASSES[size],
    fullWidth && 'btn-full-width',
    loading && 'btn-loading',
    isDisabled && 'btn-disabled',
    className
  );

  // Context for sub-components
  const ctxValue = useMemo(() => ({ loading, size, variant }), [loading, size, variant]);

  // Polymorphic props: don't pass `type` to non-button elements
  const polymorphicProps = Component === 'button'
    ? getButtonProps({ className: classes, ...rest })
    : { className: classes, 'aria-disabled': isDisabled || undefined, ...rest };

  return (
    <ButtonContext.Provider value={ctxValue}>
      <Component ref={ref} {...polymorphicProps}>
        {loading && <ButtonSpinner />}
        <span className={cn('btn-content', loading && 'btn-content-invisible')}>
          {children}
        </span>
      </Component>
    </ButtonContext.Provider>
  );
});

// Attach compound sub-components
Button.Icon = ButtonIcon;
Button.Spinner = ButtonSpinner;

// ================================================================
// 6. CONSUMER USAGE — the payoff of this architecture
// ================================================================
import { Link } from 'react-router-dom';

function CheckoutPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCheckout = async () => {
    setIsSubmitting(true);
    await processPayment();
    setIsSubmitting(false);
  };

  return (
    <div className="checkout-actions">
      {/* Standard button */}
      <Button variant="primary" size="lg" loading={isSubmitting} onClick={handleCheckout}>
        <Button.Icon><CreditCardIcon /></Button.Icon>
        Complete Purchase
      </Button>

      {/* Renders as <a> tag — href is valid */}
      <Button as="a" href="/terms" variant="link" size="sm" target="_blank">
        Terms & Conditions
      </Button>

      {/* Renders as React Router Link — "to" is valid */}
      <Button as={Link} to="/cart" variant="ghost">
        <Button.Icon position="left"><ArrowLeftIcon /></Button.Icon>
        Back to Cart
      </Button>

      {/* Renders as a custom component */}
      <Button as={motion.button} whileHover={{ scale: 1.05 }} variant="secondary">
        Animated Button
      </Button>

      {/* Full width on mobile */}
      <Button variant="danger" fullWidth onClick={handleCancel}>
        Cancel Order
      </Button>
    </div>
  );
}

// ================================================================
// 7. THEME INTEGRATION — wrap the app
// ================================================================
function App() {
  return (
    <ThemeProvider theme={{ mode: 'dark', radius: 'lg', primaryColor: '#6366f1' }}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}
```

**Architecture summary:**

| Layer | Pattern | Responsibility |
|---|---|---|
| `useButton` hook | Headless UI | Focus, disabled, loading, ARIA — no DOM |
| `Button` component | Polymorphic | Renders as any element via `as` prop |
| `Button.Icon`, `Button.Spinner` | Compound Components | Composable sub-elements with implicit state |
| `ButtonContext` | Provider | Shares loading/size/variant to sub-components |
| `ThemeProvider` | Provider | Design tokens (colors, radii, spacing) |
| `VARIANT_CLASSES`, `SIZE_CLASSES` | Configuration | Variant-to-class mapping (works with Tailwind or CSS Modules) |

This layered architecture scales from a single product to a multi-brand design system serving dozens of applications. Each layer can be tested independently: the headless hook with unit tests, the component with integration tests, and the full composition with visual regression tests (Storybook + Chromatic).
