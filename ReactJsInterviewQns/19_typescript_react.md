# TypeScript with React 18 — Interview Questions

## Topic Introduction

**TypeScript** has become the default language for professional React development, and for good reason. React 18 introduced concurrent rendering, automatic batching, transitions, and new hooks like `useId` and `useSyncExternalStore` — all of which become dramatically safer and more productive when paired with TypeScript's static type system. The core promise is simple: **if your code compiles, an entire class of runtime bugs — wrong prop types, misspelled event handlers, mismatched context values, impossible state combinations — simply cannot exist.** But TypeScript in React is not just about slapping `string` on props. It is about modeling your component APIs so precisely that the compiler becomes a design tool: discriminated unions eliminate impossible UI states, generic components create reusable data-driven layouts, template literal types enforce design-system naming conventions, and conditional types let you build polymorphic APIs where the return type adapts to the input. The gap between "knows TypeScript syntax" and "designs type-safe component architectures" is exactly what separates a junior from a senior React engineer — and it is precisely the gap that interviewers probe.

In a production React 18 codebase, TypeScript touches every layer. At the component layer, you type props, state, refs, and event handlers. At the hook layer, you write generic custom hooks whose return types narrow based on configuration. At the data layer, you type API responses end-to-end — from the server schema through Zod validation to TanStack Query generic parameters — so that a backend field rename produces a compile error, not a runtime crash. At the routing layer, you type route params and search params so links are validated at build time. At the state management layer, Redux Toolkit's `createSlice` and typed hooks (`useAppSelector`, `useAppDispatch`) ensure that selectors never access nonexistent state paths and dispatched actions always carry the correct payload shape. At the architecture layer, patterns like polymorphic `as` props, type-safe form builders, and recursive types for nested configurations let you build design-system-grade component libraries that are self-documenting through their type signatures. This file covers all of these layers — from the beginner fundamentals through advanced type-level programming — with production code examples.

```tsx
// A taste of TypeScript + React 18 — a fully typed component with generics
import { useState, useCallback, type ReactNode } from 'react';

// 1. Typed props with a generic constraint
interface ListProps<T extends { id: string | number }> {
  items: T[];
  renderItem: (item: T) => ReactNode;
  onSelect?: (item: T) => void;
  emptyMessage?: string;
}

// 2. Generic function component — no React.FC needed
function List<T extends { id: string | number }>({
  items,
  renderItem,
  onSelect,
  emptyMessage = 'No items found.',
}: ListProps<T>) {
  const [selectedId, setSelectedId] = useState<T['id'] | null>(null);

  const handleClick = useCallback(
    (item: T) => {
      setSelectedId(item.id);
      onSelect?.(item);
    },
    [onSelect]
  );

  if (items.length === 0) return <p>{emptyMessage}</p>;

  return (
    <ul>
      {items.map((item) => (
        <li
          key={item.id}
          onClick={() => handleClick(item)}
          style={{ fontWeight: item.id === selectedId ? 'bold' : 'normal' }}
        >
          {renderItem(item)}
        </li>
      ))}
    </ul>
  );
}

// 3. Usage — TypeScript infers T as User
interface User {
  id: number;
  name: string;
  role: 'admin' | 'viewer';
}

function UserDirectory({ users }: { users: User[] }) {
  return (
    <List
      items={users}
      renderItem={(user) => `${user.name} (${user.role})`} // ✅ user is User
      onSelect={(user) => console.log(user.role)}           // ✅ user.role is 'admin' | 'viewer'
    />
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. How do you type component props in React 18 with TypeScript — and when should you use `interface` vs `type`?

**Answer:**

In React 18 + TypeScript, every component's props should be explicitly typed. You define the shape of the props as a TypeScript `interface` or `type` alias and then annotate the function parameter with it.

**`interface` vs `type` — key differences:**

| Feature | `interface` | `type` |
|---|---|---|
| **Declaration merging** | ✅ Interfaces with the same name merge automatically | ❌ Types cannot be re-declared |
| **Extends** | `interface B extends A {}` | `type B = A & { ... }` (intersection) |
| **Union types** | ❌ Cannot represent unions | ✅ `type Status = 'idle' \| 'loading'` |
| **Computed properties** | ❌ | ✅ `type Keys = { [K in MyUnion]: string }` |
| **Performance** | Slightly better for large codebases (cached by name) | Aliases are expanded inline in error messages |

**Rule of thumb for React props:** Use `interface` for component props (it is extendable, readable, and the React community convention). Use `type` when you need unions, intersections, mapped types, or conditional types.

```tsx
// ✅ interface — the standard for component props
interface ButtonProps {
  label: string;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  onClick: () => void;
}

function Button({ label, variant = 'primary', disabled = false, onClick }: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant}`}
      disabled={disabled}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

// ✅ type — useful when you need a union or intersection
type AlertType = 'success' | 'warning' | 'error' | 'info';

type AlertProps = {
  type: AlertType;
  message: string;
  dismissible?: boolean;
  onDismiss?: () => void;
};

function Alert({ type, message, dismissible, onDismiss }: AlertProps) {
  return (
    <div className={`alert alert-${type}`} role="alert">
      <span>{message}</span>
      {dismissible && <button onClick={onDismiss}>✕</button>}
    </div>
  );
}

// ✅ interface extending another interface
interface BaseInputProps {
  name: string;
  label: string;
  error?: string;
}

interface TextInputProps extends BaseInputProps {
  type: 'text' | 'email' | 'password';
  placeholder?: string;
}

function TextInput({ name, label, error, type, placeholder }: TextInputProps) {
  return (
    <div>
      <label htmlFor={name}>{label}</label>
      <input id={name} name={name} type={type} placeholder={placeholder} />
      {error && <span className="error">{error}</span>}
    </div>
  );
}
```

---

### Q2. How do you type `useState`, `useRef`, and `useEffect` in React 18?

**Answer:**

React 18's built-in hooks are fully generic. TypeScript can often infer types from the initial value, but there are critical cases where you must provide an explicit type parameter — especially when the initial value is `null`, `undefined`, or a narrower type than what the state will eventually hold.

**`useState`** — The generic parameter defines what types the state variable can hold. If you pass `null` as an initial value but will later set it to an object, you must use a union type.

**`useRef`** — Has two overloads. When typing DOM refs (for `ref={myRef}`), pass `null` as the initial value and do *not* include `null` in the generic — React manages the `.current` assignment. When typing a mutable value container, include `null` in the generic or provide a non-null initial value.

**`useEffect`** — Does not take a generic parameter. The type safety comes from what you do inside the callback. The return value must be `void` or a cleanup function `() => void`.

```tsx
import { useState, useRef, useEffect } from 'react';

// ---------- useState ----------

// ✅ Inferred as number — no explicit type needed
const [count, setCount] = useState(0);

// ✅ Explicit union — initial value is null, later set to an object
interface User {
  id: number;
  name: string;
  email: string;
}
const [user, setUser] = useState<User | null>(null);

// ✅ Typing a complex state
type FetchStatus = 'idle' | 'loading' | 'success' | 'error';
const [status, setStatus] = useState<FetchStatus>('idle');

// ✅ Array state — must be explicit when starting empty
const [items, setItems] = useState<string[]>([]);

// ---------- useRef ----------

// ✅ DOM ref — pass null, do NOT include null in the generic
// This creates React.RefObject<HTMLInputElement> (readonly .current)
const inputRef = useRef<HTMLInputElement>(null);

function focusInput() {
  inputRef.current?.focus(); // .current is HTMLInputElement | null
}

// ✅ Mutable ref — for storing values (like an interval ID)
// Include null in the generic to match the initial value
const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

function startTimer() {
  intervalRef.current = setInterval(() => console.log('tick'), 1000);
}

function stopTimer() {
  if (intervalRef.current) clearInterval(intervalRef.current);
}

// ---------- useEffect ----------

// ✅ Typed fetch inside useEffect with cleanup via AbortController
function UserProfile({ userId }: { userId: number }) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchUser() {
      try {
        const res = await fetch(`/api/users/${userId}`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: User = await res.json();
        setUser(data);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err.message);
        }
      }
    }

    fetchUser();
    return () => controller.abort(); // ✅ cleanup function
  }, [userId]);

  return user ? <h1>{user.name}</h1> : <p>{error ?? 'Loading…'}</p>;
}
```

---

### Q3. How do you type event handlers in React 18 — what are `React.ChangeEvent`, `React.FormEvent`, and `React.MouseEvent`?

**Answer:**

React provides its own **synthetic event types** that wrap native DOM events. Every event handler in JSX has a corresponding React type parameterized by the HTML element it originates from. The most common pattern in production is to type the handler inline (where TypeScript infers the event type) or to define a standalone handler function with an explicit event type.

**Common event types:**

| Event Type | Triggered By |
|---|---|
| `React.ChangeEvent<HTMLInputElement>` | `onChange` on inputs, selects, textareas |
| `React.FormEvent<HTMLFormElement>` | `onSubmit` on forms |
| `React.MouseEvent<HTMLButtonElement>` | `onClick` on buttons, divs, etc. |
| `React.KeyboardEvent<HTMLInputElement>` | `onKeyDown`, `onKeyUp` |
| `React.FocusEvent<HTMLInputElement>` | `onFocus`, `onBlur` |
| `React.DragEvent<HTMLDivElement>` | `onDrag`, `onDrop` |

The generic parameter is the **HTML element** the event originates from — this types the `event.currentTarget` property correctly.

```tsx
import { useState, type FormEvent, type ChangeEvent, type MouseEvent } from 'react';

interface LoginForm {
  email: string;
  password: string;
}

function LoginPage() {
  const [form, setForm] = useState<LoginForm>({ email: '', password: '' });

  // ✅ Typing onChange — ChangeEvent parameterized by the element
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.currentTarget;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  // ✅ Typing onSubmit — FormEvent parameterized by <form>
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    console.log('Submitting:', form);
  };

  // ✅ Typing onClick — MouseEvent parameterized by <button>
  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    console.log('Button clicked at:', e.clientX, e.clientY);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="email"
        type="email"
        value={form.email}
        onChange={handleChange} // ✅ TypeScript knows e is ChangeEvent<HTMLInputElement>
      />
      <input
        name="password"
        type="password"
        value={form.password}
        onChange={handleChange}
      />
      <button type="submit" onClick={handleClick}>
        Log In
      </button>
    </form>
  );
}

// ✅ Typing a select change handler
function RoleSelector() {
  const [role, setRole] = useState<'admin' | 'editor' | 'viewer'>('viewer');

  const handleSelect = (e: ChangeEvent<HTMLSelectElement>) => {
    setRole(e.currentTarget.value as 'admin' | 'editor' | 'viewer');
  };

  return (
    <select value={role} onChange={handleSelect}>
      <option value="admin">Admin</option>
      <option value="editor">Editor</option>
      <option value="viewer">Viewer</option>
    </select>
  );
}

// ✅ Inline handler — TypeScript infers the event type automatically
function SearchBar({ onSearch }: { onSearch: (query: string) => void }) {
  return (
    <input
      type="search"
      placeholder="Search…"
      onChange={(e) => onSearch(e.currentTarget.value)} // inferred: ChangeEvent<HTMLInputElement>
    />
  );
}
```

---

### Q4. What is `React.FC` (FunctionComponent), and why has the React community moved away from it?

**Answer:**

`React.FC<Props>` (short for `React.FunctionComponent<Props>`) is a type that annotates a function as a React component. It was once the recommended way to type React components, but the community — including the React TypeScript Cheatsheet and Create React App (which removed it from templates) — has moved decisively away from it.

**Why `React.FC` was popular:**
- It provided an implicit `children` prop (in React 17 and earlier typings).
- It typed the return value as `ReactElement | null`.
- It allowed adding `defaultProps` and `displayName` as static properties.

**Why `React.FC` fell out of favor:**

1. **Implicit `children` was removed** — In `@types/react` 18, `React.FC` no longer includes `children`. This was the main convenience it offered.
2. **Breaks generic components** — You cannot write `const List: React.FC<ListProps<T>>` because `T` has no scope. Generic components require plain function declarations.
3. **Adds unnecessary indirection** — `React.FC` wraps your function type, making it harder to read and adding no real safety benefit over just typing the props parameter.
4. **`defaultProps` is deprecated** — TypeScript default parameters are the standard now, and `React.FC` originally encouraged `defaultProps`.
5. **Return type is overly restrictive** — `React.FC` forces the return to be `ReactElement | null`, disallowing returning `string` or `number` (which are valid in React 18).

```tsx
// ❌ React.FC — the older pattern (avoid in new code)
import { type FC } from 'react';

interface GreetingProps {
  name: string;
  children?: React.ReactNode; // must be explicit in React 18
}

const Greeting: FC<GreetingProps> = ({ name, children }) => {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      {children}
    </div>
  );
};

// ❌ Cannot make React.FC generic — this does not work
// const List: FC<ListProps<T>> = ({ items }) => { ... }

// ✅ Plain function — the modern standard
interface GreetingProps {
  name: string;
  children?: React.ReactNode;
}

function Greeting({ name, children }: GreetingProps) {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      {children}
    </div>
  );
}

// ✅ Arrow function with typed parameter — also fine
const Greeting = ({ name, children }: GreetingProps) => (
  <div>
    <h1>Hello, {name}!</h1>
    {children}
  </div>
);

// ✅ Generic component — only possible with plain function syntax
function List<T extends { id: string }>({ items }: { items: T[] }) {
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{JSON.stringify(item)}</li>
      ))}
    </ul>
  );
}
```

---

### Q5. How do you type the `children` prop — and what is the difference between `React.ReactNode`, `React.ReactElement`, and `React.JSX.Element`?

**Answer:**

The `children` prop is one of the most commonly mistyped props. Choosing the wrong type either blocks valid usage or allows invalid usage.

| Type | What It Accepts | When to Use |
|---|---|---|
| `React.ReactNode` | Strings, numbers, booleans, `null`, `undefined`, JSX elements, arrays, fragments | **Default choice — use this for 99% of `children` props** |
| `React.ReactElement` | Only JSX elements (`<Component />` or `<div />`) — **not** strings or numbers | When you need to manipulate children (e.g., `React.cloneElement`) |
| `React.JSX.Element` | Equivalent to `React.ReactElement` but from the JSX namespace | Rarely used directly — it is what JSX expressions resolve to |
| `React.PropsWithChildren<P>` | Utility type that adds `children?: React.ReactNode` to your props | Convenience wrapper — same as adding `children?: ReactNode` manually |

**Key insight:** In `@types/react` 18, `React.FC` no longer includes `children` automatically. You must always declare it explicitly in your props interface.

```tsx
import { type ReactNode, type ReactElement, Children, cloneElement, isValidElement } from 'react';

// ✅ ReactNode — accepts everything (the standard choice)
interface CardProps {
  title: string;
  children: ReactNode;
}

function Card({ title, children }: CardProps) {
  return (
    <div className="card">
      <h2>{title}</h2>
      <div className="card-body">{children}</div>
    </div>
  );
}

// Usage — all of these work with ReactNode
<Card title="Info">
  <p>A paragraph element</p>
</Card>

<Card title="Simple">
  Just a string
</Card>

<Card title="Mixed">
  <>
    <p>Element</p>
    {42}
    {null}
    {['a', 'b', 'c']}
  </>
</Card>

// ✅ ReactElement — when you need to manipulate children
interface ToolbarProps {
  children: ReactElement | ReactElement[];
}

function Toolbar({ children }: ToolbarProps) {
  // We need actual elements to clone — strings/numbers wouldn't work here
  return (
    <div className="toolbar">
      {Children.map(children, (child) =>
        isValidElement(child)
          ? cloneElement(child, { className: 'toolbar-item' })
          : child
      )}
    </div>
  );
}

// ✅ Optional children — note the `?`
interface LayoutProps {
  sidebar?: ReactNode;
  children?: ReactNode;
}

function Layout({ sidebar, children }: LayoutProps) {
  return (
    <div className="layout">
      {sidebar && <aside>{sidebar}</aside>}
      <main>{children}</main>
    </div>
  );
}

// ✅ Render prop pattern — children as a function
interface DataFetcherProps<T> {
  url: string;
  children: (data: T, isLoading: boolean) => ReactNode;
}

function DataFetcher<T>({ url, children }: DataFetcherProps<T>) {
  // ... fetch logic ...
  const data = {} as T;
  const isLoading = false;
  return <>{children(data, isLoading)}</>;
}
```

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you type custom hooks with generics — and why is it essential for reusable hook libraries?

**Answer:**

Custom hooks in React are just functions, so they can leverage the full power of TypeScript generics. A generic custom hook is parameterized by one or more type variables, letting callers control the types of inputs and outputs. This is essential because a reusable hook — like `useFetch<T>()`, `useLocalStorage<T>()`, or `useForm<T>()` — operates on data whose shape the hook author cannot know in advance. Without generics, you'd either use `any` (losing all safety) or create separate hooks for every data shape (losing all reusability).

The key patterns are: (1) the generic parameter flows from input to output so the return type narrows automatically, (2) constraints (`extends`) ensure the generic satisfies required interfaces, and (3) tuple return types preserve named positions for destructuring.

```tsx
import { useState, useEffect, useCallback, useRef } from 'react';

// ✅ Generic useLocalStorage hook — T inferred from defaultValue
function useLocalStorage<T>(
  key: string,
  defaultValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const [stored, setStored] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item !== null ? (JSON.parse(item) as T) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStored((prev) => {
        const next = value instanceof Function ? value(prev) : value;
        window.localStorage.setItem(key, JSON.stringify(next));
        return next;
      });
    },
    [key]
  );

  const removeValue = useCallback(() => {
    window.localStorage.removeItem(key);
    setStored(defaultValue);
  }, [key, defaultValue]);

  return [stored, setValue, removeValue];
}

// Usage — T is inferred as { theme: string; fontSize: number }
const [settings, setSettings, clearSettings] = useLocalStorage('user-settings', {
  theme: 'dark',
  fontSize: 14,
});
// settings.theme  → string ✅
// settings.fontSize → number ✅
// setSettings({ theme: 'light', fontSize: 16 }) ✅
// setSettings({ theme: 'light' }) ❌ — missing fontSize

// ✅ Generic useFetch hook — with constrained return type
interface UseFetchResult<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
  refetch: () => void;
}

function useFetch<T>(url: string, options?: RequestInit): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(url, {
        ...options,
        signal: abortRef.current.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as T;
      setData(json);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, [url, options]);

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, [fetchData]);

  return { data, error, isLoading, refetch: fetchData };
}

// Usage — T is explicitly provided
interface Product {
  id: number;
  name: string;
  price: number;
}

function ProductList() {
  const { data: products, isLoading, error } = useFetch<Product[]>('/api/products');

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <ul>
      {products?.map((p) => (
        <li key={p.id}>
          {p.name} — ${p.price.toFixed(2)}
        </li>
      ))}
    </ul>
  );
}
```

---

### Q7. What are discriminated unions, and how do you use them to type component variants in React 18?

**Answer:**

A **discriminated union** (also called a "tagged union") is a TypeScript pattern where a union of object types shares a common **discriminant property** (a literal type field) that TypeScript uses to narrow the union to a specific variant. In React, this pattern is invaluable for components that behave differently based on a "kind" or "variant" prop — where each variant requires a different set of props. Instead of making everything optional and hoping the caller passes the right combination, discriminated unions make it **impossible to pass an invalid combination**.

The discriminant property is typically a string literal union (like `variant: 'text' | 'checkbox' | 'select'`). When TypeScript sees a check on this discriminant (in a `switch`, `if`, or destructuring), it automatically narrows the type to the correct variant — giving you access to only the properties that exist for that variant.

```tsx
// ✅ Discriminated union for a notification component
type NotificationProps =
  | {
      type: 'success';
      message: string;
      autoClose?: boolean;
      autoCloseMs?: number;
    }
  | {
      type: 'error';
      message: string;
      errorCode: number;
      retryable: boolean;
      onRetry?: () => void;
    }
  | {
      type: 'loading';
      message?: string;
      progress?: number; // 0–100
    };

function Notification(props: NotificationProps) {
  switch (props.type) {
    case 'success':
      // ✅ TypeScript knows autoClose and autoCloseMs are available here
      return (
        <div className="notification success">
          ✅ {props.message}
          {props.autoClose && <span>Closing in {props.autoCloseMs ?? 3000}ms</span>}
        </div>
      );

    case 'error':
      // ✅ TypeScript knows errorCode, retryable, onRetry are available here
      return (
        <div className="notification error">
          ❌ {props.message} (Code: {props.errorCode})
          {props.retryable && (
            <button onClick={props.onRetry}>Retry</button>
          )}
        </div>
      );

    case 'loading':
      // ✅ TypeScript knows progress is available here
      return (
        <div className="notification loading">
          ⏳ {props.message ?? 'Loading…'}
          {props.progress !== undefined && (
            <progress value={props.progress} max={100} />
          )}
        </div>
      );
  }
}

// ✅ Usage — compiler enforces valid prop combinations
<Notification type="success" message="Saved!" autoClose />
<Notification type="error" message="Failed" errorCode={500} retryable onRetry={() => refetch()} />
<Notification type="loading" progress={45} />

// ❌ Compile error — 'errorCode' does not exist on type '{ type: "success"; ... }'
// <Notification type="success" message="Saved!" errorCode={200} />

// ✅ Discriminated union for form field config
type FieldConfig =
  | { kind: 'text'; label: string; placeholder?: string; maxLength?: number }
  | { kind: 'number'; label: string; min?: number; max?: number; step?: number }
  | { kind: 'select'; label: string; options: { value: string; label: string }[] }
  | { kind: 'checkbox'; label: string; defaultChecked?: boolean };

function FormField({ config }: { config: FieldConfig }) {
  switch (config.kind) {
    case 'text':
      return <input type="text" placeholder={config.placeholder} maxLength={config.maxLength} />;
    case 'number':
      return <input type="number" min={config.min} max={config.max} step={config.step} />;
    case 'select':
      return (
        <select>
          {config.options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      );
    case 'checkbox':
      return <input type="checkbox" defaultChecked={config.defaultChecked} />;
  }
}
```

---

### Q8. How do you type React Context with `createContext` and `useContext` in a type-safe way — and how do you avoid the `undefined` default problem?

**Answer:**

A common pain point with typed Context is the **default value problem**. `createContext` requires a default value, but for many contexts (auth, theme, feature flags) there is no meaningful default — the context only makes sense inside a Provider. If you pass `undefined` as the default, every consumer must check for `undefined` before using the value, leading to defensive `if (!ctx) throw ...` everywhere. The production pattern is to create a **typed custom hook** that throws if the context is used outside a Provider, eliminating the `undefined` check at every call site.

```tsx
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';

// ---------- Pattern 1: The "throw-on-missing-provider" pattern ----------

// 1. Define the context value shape
interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

// 2. Create context with undefined — we KNOW it will be provided
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// 3. Custom hook that narrows out undefined
function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an <AuthProvider>');
  }
  return context; // ✅ Return type is AuthContextValue (not | undefined)
}

// 4. Provider component
function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Login failed');
    const userData: User = await res.json();
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  // ✅ Memoize to prevent unnecessary re-renders
  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      login,
      logout,
    }),
    [user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// 5. Consumer — no undefined checks needed
function UserMenu() {
  const { user, isAuthenticated, logout } = useAuth();
  //      ^^^^ AuthContextValue — no undefined ✅

  if (!isAuthenticated) return <a href="/login">Sign In</a>;

  return (
    <div>
      <span>{user!.name}</span>
      <button onClick={logout}>Sign Out</button>
    </div>
  );
}

// ---------- Pattern 2: Generic context factory ----------

// For projects with many contexts, a factory eliminates boilerplate
function createSafeContext<T>(displayName: string) {
  const Context = createContext<T | undefined>(undefined);
  Context.displayName = displayName;

  function useSafeContext(): T {
    const ctx = useContext(Context);
    if (ctx === undefined) {
      throw new Error(`use${displayName} must be used within <${displayName}Provider>`);
    }
    return ctx;
  }

  return [Context.Provider, useSafeContext] as const;
}

// Usage of the factory
interface ThemeContextValue {
  mode: 'light' | 'dark';
  toggleMode: () => void;
}

const [ThemeProvider, useTheme] = createSafeContext<ThemeContextValue>('Theme');

function App() {
  const [mode, setMode] = useState<'light' | 'dark'>('light');
  const toggleMode = useCallback(() => setMode((m) => (m === 'light' ? 'dark' : 'light')), []);

  return (
    <ThemeProvider value={{ mode, toggleMode }}>
      <Dashboard />
    </ThemeProvider>
  );
}

function Dashboard() {
  const { mode, toggleMode } = useTheme(); // ✅ ThemeContextValue — never undefined
  return <button onClick={toggleMode}>Current: {mode}</button>;
}
```

---

### Q9. How do you type Higher-Order Components (HOCs) in TypeScript — and why are they notoriously difficult to type?

**Answer:**

A **Higher-Order Component** is a function that takes a component and returns a new component with additional behavior (e.g., `withAuth`, `withTheme`, `withLogging`). HOCs are difficult to type because they must: (1) accept a component with *any* props, (2) "consume" some of those props (the injected ones), (3) pass through remaining props, and (4) preserve the original component's generic type parameters. This requires intersection types, `Omit`, `ComponentType`, and careful use of `as` assertions.

**Modern recommendation:** Prefer custom hooks and composition over HOCs in new code. But many production codebases still use HOCs, and typing them is a frequent interview question.

```tsx
import { type ComponentType, type FC, useEffect, useState } from 'react';

// ---------- Example 1: withLoading HOC ----------

// The HOC injects `isLoading` behavior and shows a spinner
interface WithLoadingProps {
  isLoading: boolean;
}

function withLoading<P extends object>(
  WrappedComponent: ComponentType<P>
): FC<P & WithLoadingProps> {
  const WithLoadingComponent: FC<P & WithLoadingProps> = ({
    isLoading,
    ...restProps
  }) => {
    if (isLoading) return <div className="spinner">Loading…</div>;
    return <WrappedComponent {...(restProps as P)} />;
  };

  WithLoadingComponent.displayName = `withLoading(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return WithLoadingComponent;
}

// Usage
interface UserListProps {
  users: { id: string; name: string }[];
}

function UserList({ users }: UserListProps) {
  return (
    <ul>
      {users.map((u) => <li key={u.id}>{u.name}</li>)}
    </ul>
  );
}

const UserListWithLoading = withLoading(UserList);
// Type: FC<UserListProps & WithLoadingProps>

<UserListWithLoading users={[]} isLoading={true} />; // ✅
// <UserListWithLoading users={[]} />;              // ❌ missing isLoading

// ---------- Example 2: withAuth HOC — injects user, omits from outer props ----------

interface AuthInjectedProps {
  currentUser: {
    id: string;
    name: string;
    role: 'admin' | 'user';
  };
}

function withAuth<P extends AuthInjectedProps>(
  WrappedComponent: ComponentType<P>
): ComponentType<Omit<P, keyof AuthInjectedProps>> {
  function WithAuthComponent(props: Omit<P, keyof AuthInjectedProps>) {
    const [user, setUser] = useState<AuthInjectedProps['currentUser'] | null>(null);

    useEffect(() => {
      // Simulate fetching current user
      fetch('/api/me')
        .then((res) => res.json())
        .then(setUser);
    }, []);

    if (!user) return <div>Authenticating…</div>;

    // We need to cast because TS can't verify Omit + injected = P
    const combinedProps = { ...props, currentUser: user } as unknown as P;
    return <WrappedComponent {...combinedProps} />;
  }

  WithAuthComponent.displayName = `withAuth(${
    WrappedComponent.displayName || WrappedComponent.name
  })`;

  return WithAuthComponent;
}

// Usage
interface DashboardProps extends AuthInjectedProps {
  title: string;
}

function Dashboard({ title, currentUser }: DashboardProps) {
  return (
    <div>
      <h1>{title}</h1>
      <p>Welcome, {currentUser.name} ({currentUser.role})</p>
    </div>
  );
}

const ProtectedDashboard = withAuth(Dashboard);
// Type: ComponentType<Omit<DashboardProps, 'currentUser'>>
// = ComponentType<{ title: string }>

<ProtectedDashboard title="Admin Panel" />;  // ✅ currentUser is injected
```

---

### Q10. How do you build generic components like a type-safe `Table` or `Select` in React 18?

**Answer:**

Generic components are components whose props are parameterized by a type variable, allowing the same component to work with any data shape while maintaining full type safety. The classic examples are `<Table<T>>`, `<Select<T>>`, `<List<T>>`, and `<Autocomplete<T>>`. You declare the generic on the function itself (not on `React.FC`) and let TypeScript infer it from the props.

```tsx
import { useState, useCallback, type ReactNode, type Key } from 'react';

// ✅ Generic Table component
interface Column<T> {
  key: keyof T & string;
  header: string;
  render?: (value: T[keyof T], row: T) => ReactNode;
  sortable?: boolean;
}

interface TableProps<T extends { id: Key }> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

function Table<T extends { id: Key }>({
  data,
  columns,
  onRowClick,
  emptyMessage = 'No data available.',
}: TableProps<T>) {
  const [sortKey, setSortKey] = useState<keyof T | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const handleSort = (key: keyof T) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedData = sortKey
    ? [...data].sort((a, b) => {
        const aVal = a[sortKey];
        const bVal = b[sortKey];
        const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        return sortDir === 'asc' ? cmp : -cmp;
      })
    : data;

  if (data.length === 0) return <p>{emptyMessage}</p>;

  return (
    <table>
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={col.key}
              onClick={() => col.sortable && handleSort(col.key)}
              style={{ cursor: col.sortable ? 'pointer' : 'default' }}
            >
              {col.header}
              {sortKey === col.key && (sortDir === 'asc' ? ' ▲' : ' ▼')}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sortedData.map((row) => (
          <tr key={row.id} onClick={() => onRowClick?.(row)}>
            {columns.map((col) => (
              <td key={col.key}>
                {col.render
                  ? col.render(row[col.key], row)
                  : String(row[col.key])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ✅ Usage — T is inferred as Employee
interface Employee {
  id: number;
  name: string;
  department: string;
  salary: number;
}

function EmployeeTable({ employees }: { employees: Employee[] }) {
  return (
    <Table
      data={employees}
      columns={[
        { key: 'name', header: 'Name', sortable: true },
        { key: 'department', header: 'Department', sortable: true },
        {
          key: 'salary',
          header: 'Salary',
          sortable: true,
          render: (val) => `$${(val as number).toLocaleString()}`,
        },
      ]}
      onRowClick={(emp) => console.log(emp.department)} // ✅ emp is Employee
    />
  );
}

// ✅ Generic Select component
interface SelectOption<V extends string | number> {
  value: V;
  label: string;
  disabled?: boolean;
}

interface SelectProps<V extends string | number> {
  options: SelectOption<V>[];
  value: V;
  onChange: (value: V) => void;
  placeholder?: string;
}

function Select<V extends string | number>({
  options,
  value,
  onChange,
  placeholder,
}: SelectProps<V>) {
  return (
    <select
      value={value}
      onChange={(e) => {
        const raw = e.currentTarget.value;
        // Determine whether V is number or string
        const parsed = typeof value === 'number' ? Number(raw) : raw;
        onChange(parsed as V);
      }}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value} disabled={opt.disabled}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

// Usage — V inferred as 'admin' | 'editor' | 'viewer'
type Role = 'admin' | 'editor' | 'viewer';

function RolePicker() {
  const [role, setRole] = useState<Role>('viewer');

  return (
    <Select
      options={[
        { value: 'admin' as const, label: 'Admin' },
        { value: 'editor' as const, label: 'Editor' },
        { value: 'viewer' as const, label: 'Viewer' },
      ]}
      value={role}
      onChange={setRole} // ✅ setRole expects Role, onChange sends Role
    />
  );
}
```

---

### Q11. How do you type `forwardRef` with generics — and what are the challenges?

**Answer:**

`React.forwardRef` is used to pass a `ref` through a component to a child DOM element (or another component). The challenge with TypeScript is that `forwardRef` has its own generic signature `forwardRef<RefType, Props>`, and combining this with a *component-level* generic (like `<T>` for a generic List) is notoriously tricky because `forwardRef` returns a fixed type — you cannot easily make the *returned component* generic.

**The basic case (non-generic component + forwardRef) is straightforward.** The hard part is generic components with forwardRef.

```tsx
import { forwardRef, useRef, useImperativeHandle, type ReactNode, type Ref } from 'react';

// ---------- Basic forwardRef typing ----------

interface InputProps {
  label: string;
  error?: string;
  type?: 'text' | 'email' | 'password';
}

// forwardRef<RefElementType, PropsType>
const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, type = 'text' }, ref) => {
    return (
      <div className="form-group">
        <label>{label}</label>
        <input ref={ref} type={type} className={error ? 'input-error' : ''} />
        {error && <span className="error">{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';

// Usage
function LoginForm() {
  const emailRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    emailRef.current?.focus(); // ✅ .current is HTMLInputElement | null
  };

  return (
    <form onSubmit={handleSubmit}>
      <Input ref={emailRef} label="Email" type="email" />
    </form>
  );
}

// ---------- useImperativeHandle — exposing a custom ref API ----------

interface FormHandle {
  reset: () => void;
  validate: () => boolean;
  getValues: () => Record<string, string>;
}

interface ContactFormProps {
  onSubmit: (data: Record<string, string>) => void;
}

const ContactForm = forwardRef<FormHandle, ContactFormProps>(
  ({ onSubmit }, ref) => {
    const formRef = useRef<HTMLFormElement>(null);

    useImperativeHandle(ref, () => ({
      reset() {
        formRef.current?.reset();
      },
      validate() {
        return formRef.current?.checkValidity() ?? false;
      },
      getValues() {
        const formData = new FormData(formRef.current!);
        return Object.fromEntries(formData.entries()) as Record<string, string>;
      },
    }));

    return (
      <form ref={formRef} onSubmit={(e) => { e.preventDefault(); onSubmit({}); }}>
        <input name="name" required />
        <input name="email" type="email" required />
        <button type="submit">Send</button>
      </form>
    );
  }
);

ContactForm.displayName = 'ContactForm';

// Usage
function App() {
  const formRef = useRef<FormHandle>(null);

  const handleReset = () => {
    formRef.current?.reset();     // ✅ typed as FormHandle
    formRef.current?.validate();  // ✅
  };

  return <ContactForm ref={formRef} onSubmit={console.log} />;
}

// ---------- Generic component + forwardRef (the workaround) ----------

// forwardRef doesn't support generic components directly.
// The workaround: cast forwardRef to a generic function signature.

interface GenericListProps<T> {
  items: T[];
  renderItem: (item: T) => ReactNode;
}

// Define the generic forwardRef signature
function GenericListInner<T>(
  { items, renderItem }: GenericListProps<T>,
  ref: Ref<HTMLUListElement>
) {
  return (
    <ul ref={ref}>
      {items.map((item, i) => (
        <li key={i}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}

// Cast to preserve the generic
const GenericList = forwardRef(GenericListInner) as <T>(
  props: GenericListProps<T> & { ref?: Ref<HTMLUListElement> }
) => ReactNode;

// Usage — T inferred as { id: number; name: string }
function App2() {
  const listRef = useRef<HTMLUListElement>(null);

  return (
    <GenericList
      ref={listRef}
      items={[{ id: 1, name: 'Alice' }]}
      renderItem={(item) => item.name} // ✅ item is { id: number; name: string }
    />
  );
}
```

---

### Q12. How do you build type-safe forms with React Hook Form and Zod in a React 18 project?

**Answer:**

**React Hook Form** + **Zod** is the gold standard for type-safe forms in production React 18 applications. Zod defines the validation schema, and its `z.infer<typeof schema>` extracts the TypeScript type — so the form shape, validation rules, and TypeScript types are all derived from a **single source of truth**. React Hook Form's `useForm<T>` accepts this inferred type, giving you autocomplete on `register`, `watch`, `setValue`, `getValues`, and `errors`.

The key integration point is the `@hookform/resolvers/zod` package, which provides a `zodResolver` that connects Zod validation to React Hook Form's validation pipeline.

```tsx
import { useForm, type SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// ✅ Step 1: Define the Zod schema — single source of truth
const registrationSchema = z
  .object({
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(20, 'Username must be at most 20 characters')
      .regex(/^[a-zA-Z0-9_]+$/, 'Only letters, numbers, and underscores'),
    email: z.string().email('Invalid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[0-9]/, 'Must contain a number'),
    confirmPassword: z.string(),
    role: z.enum(['developer', 'designer', 'manager']),
    agreeToTerms: z.literal(true, {
      errorMap: () => ({ message: 'You must agree to the terms' }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

// ✅ Step 2: Infer the TypeScript type from the schema
type RegistrationFormData = z.infer<typeof registrationSchema>;
// Inferred type:
// {
//   username: string;
//   email: string;
//   password: string;
//   confirmPassword: string;
//   role: 'developer' | 'designer' | 'manager';
//   agreeToTerms: true;
// }

// ✅ Step 3: Build the form component
function RegistrationForm() {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
    watch,
    reset,
  } = useForm<RegistrationFormData>({
    resolver: zodResolver(registrationSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: 'developer',
      agreeToTerms: undefined as unknown as true,
    },
  });

  const onSubmit: SubmitHandler<RegistrationFormData> = async (data) => {
    // data is fully typed as RegistrationFormData ✅
    console.log(data.username); // ✅ string
    console.log(data.role);     // ✅ 'developer' | 'designer' | 'manager'

    await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    reset();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          {...register('username')} // ✅ autocomplete: 'username' | 'email' | ...
        />
        {errors.username && <span className="error">{errors.username.message}</span>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register('email')} />
        {errors.email && <span className="error">{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input id="password" type="password" {...register('password')} />
        {errors.password && <span className="error">{errors.password.message}</span>}
      </div>

      <div>
        <label htmlFor="confirmPassword">Confirm Password</label>
        <input id="confirmPassword" type="password" {...register('confirmPassword')} />
        {errors.confirmPassword && (
          <span className="error">{errors.confirmPassword.message}</span>
        )}
      </div>

      <div>
        <label htmlFor="role">Role</label>
        <select id="role" {...register('role')}>
          <option value="developer">Developer</option>
          <option value="designer">Designer</option>
          <option value="manager">Manager</option>
        </select>
        {errors.role && <span className="error">{errors.role.message}</span>}
      </div>

      <div>
        <label>
          <input type="checkbox" {...register('agreeToTerms')} />
          I agree to the Terms and Conditions
        </label>
        {errors.agreeToTerms && (
          <span className="error">{errors.agreeToTerms.message}</span>
        )}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Registering…' : 'Register'}
      </button>
    </form>
  );
}

// ✅ Bonus: Reusable typed form field component
interface TypedFieldProps<T extends z.ZodType> {
  schema: T;
  name: string;
  label: string;
}

// ✅ Nested object schema example — address form
const addressSchema = z.object({
  street: z.string().min(1, 'Required'),
  city: z.string().min(1, 'Required'),
  state: z.string().length(2, 'Use 2-letter state code'),
  zip: z.string().regex(/^\d{5}(-\d{4})?$/, 'Invalid ZIP code'),
});

const orderSchema = z.object({
  items: z.array(z.object({
    productId: z.string(),
    quantity: z.number().min(1),
  })).min(1, 'At least one item required'),
  shippingAddress: addressSchema,
  billingAddress: addressSchema.optional(),
  sameAsShipping: z.boolean(),
});

type OrderFormData = z.infer<typeof orderSchema>;
// Fully typed nested structure — shippingAddress.city is string, etc.
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you build polymorphic components with an `as` prop that provides correct type inference?

**Answer:**

A **polymorphic component** accepts an `as` prop that determines the underlying HTML element or component it renders. For example, a `<Button as="a" href="/home">` should render an anchor tag and require `href`, while `<Button as="button" type="submit">` should render a button and require `type`. The challenge is making TypeScript infer the correct prop types based on the `as` value — so you get compile-time errors when you pass `href` to a `<button>` or `type="submit"` to an `<a>`.

This requires several advanced TypeScript features: generic components, `React.ComponentPropsWithoutRef`, `ElementType`, and the `Omit` utility to remove conflicting props.

```tsx
import {
  type ElementType,
  type ComponentPropsWithoutRef,
  type ReactNode,
} from 'react';

// ✅ Step 1: Define the base props your component always has
interface ButtonOwnProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: ReactNode;
  children: ReactNode;
}

// ✅ Step 2: Create the polymorphic props type
type PolymorphicProps<
  E extends ElementType,
  OwnProps = object,
> = OwnProps &
  Omit<ComponentPropsWithoutRef<E>, keyof OwnProps> & {
    as?: E;
  };

// ✅ Step 3: Define the component type
type ButtonProps<E extends ElementType = 'button'> = PolymorphicProps<E, ButtonOwnProps>;

// ✅ Step 4: Implement the component
function Button<E extends ElementType = 'button'>({
  as,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  children,
  ...restProps
}: ButtonProps<E>) {
  const Component = as || 'button';

  return (
    <Component
      className={`btn btn-${variant} btn-${size}`}
      disabled={isLoading}
      {...restProps}
    >
      {isLoading ? (
        <span className="spinner" />
      ) : (
        <>
          {leftIcon && <span className="btn-icon">{leftIcon}</span>}
          {children}
        </>
      )}
    </Component>
  );
}

// ✅ Usage — TypeScript infers the correct element props

// Default: renders a <button>, accepts ButtonHTMLAttributes
<Button variant="primary" onClick={() => console.log('click')}>
  Submit
</Button>

// as="a": renders an <a>, accepts AnchorHTMLAttributes
<Button as="a" href="/dashboard" variant="ghost">
  Go to Dashboard
</Button>

// ❌ Compile error — href does not exist on <button>
// <Button href="/dashboard">Click</Button>

// ❌ Compile error — type="submit" does not exist on <a>
// <Button as="a" type="submit">Click</Button>

// ✅ as={Link} — works with React Router's Link component
import { Link } from 'react-router-dom';

<Button as={Link} to="/profile" variant="secondary">
  Profile
</Button>

// ✅ Reusable polymorphic type for a design system
type TextProps<E extends ElementType = 'p'> = PolymorphicProps<
  E,
  {
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
    weight?: 'normal' | 'medium' | 'bold';
    color?: 'primary' | 'secondary' | 'muted';
    children: ReactNode;
  }
>;

function Text<E extends ElementType = 'p'>({
  as,
  size = 'md',
  weight = 'normal',
  color = 'primary',
  children,
  ...rest
}: TextProps<E>) {
  const Component = as || 'p';
  return (
    <Component
      className={`text-${size} font-${weight} color-${color}`}
      {...rest}
    >
      {children}
    </Component>
  );
}

// Usage
<Text as="h1" size="xl" weight="bold">Page Title</Text>
<Text as="span" size="sm" color="muted">Subtitle</Text>
<Text>Default paragraph text.</Text>
```

---

### Q14. How do you achieve type-safe routing with React Router v6 in a TypeScript project?

**Answer:**

React Router v6 is not fully type-safe out of the box — `useParams()` returns `Record<string, string | undefined>`, `useSearchParams()` returns untyped `URLSearchParams`, and `<Link to="...">` accepts any string. In production, you want compile-time guarantees that route params match their definitions, links point to valid routes, and loader/action data is typed.

The strategy involves: (1) defining route params as typed interfaces, (2) creating typed wrapper hooks, (3) using `satisfies` and `const` assertions for route config, and (4) leveraging the newer React Router type utilities.

```tsx
import {
  useParams,
  useSearchParams,
  Link,
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  type LoaderFunctionArgs,
} from 'react-router-dom';

// ✅ Step 1: Define all route paths as a const map
const ROUTES = {
  home: '/',
  products: '/products',
  productDetail: '/products/:productId',
  userProfile: '/users/:userId',
  userSettings: '/users/:userId/settings',
  search: '/search',
} as const;

// ✅ Step 2: Type-safe params for each parameterized route
interface RouteParams {
  productDetail: { productId: string };
  userProfile: { userId: string };
  userSettings: { userId: string };
}

// ✅ Step 3: Typed useParams wrapper
function useTypedParams<T extends keyof RouteParams>(): RouteParams[T] {
  return useParams() as RouteParams[T];
}

// ✅ Step 4: Typed search params with Zod validation
import { z } from 'zod';

const searchParamsSchema = z.object({
  q: z.string().optional(),
  page: z.coerce.number().min(1).default(1),
  sort: z.enum(['relevance', 'price-asc', 'price-desc']).default('relevance'),
  category: z.string().optional(),
});

type SearchParams = z.infer<typeof searchParamsSchema>;

function useTypedSearchParams(): [SearchParams, (params: Partial<SearchParams>) => void] {
  const [searchParams, setSearchParams] = useSearchParams();

  const parsed = searchParamsSchema.parse(Object.fromEntries(searchParams));

  const setTypedParams = (newParams: Partial<SearchParams>) => {
    const merged = { ...parsed, ...newParams };
    const entries = Object.entries(merged).filter(
      ([, v]) => v !== undefined
    ) as [string, string][];
    setSearchParams(new URLSearchParams(entries.map(([k, v]) => [k, String(v)])));
  };

  return [parsed, setTypedParams];
}

// ✅ Step 5: Type-safe path builder
function buildPath<T extends keyof typeof ROUTES>(
  route: T,
  params?: T extends keyof RouteParams ? RouteParams[T] : never
): string {
  let path: string = ROUTES[route];
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      path = path.replace(`:${key}`, String(value));
    });
  }
  return path;
}

// Usage
buildPath('home');                                    // → '/'
buildPath('productDetail', { productId: '42' });      // → '/products/42'
// buildPath('productDetail');                         // ❌ Error — params required
// buildPath('productDetail', { userId: '1' });        // ❌ Error — wrong param name

// ✅ Step 6: Typed loader data
interface Product {
  id: string;
  name: string;
  price: number;
  description: string;
}

async function productLoader({ params }: LoaderFunctionArgs): Promise<Product> {
  const res = await fetch(`/api/products/${params.productId}`);
  if (!res.ok) throw new Response('Not found', { status: 404 });
  return res.json();
}

function ProductDetailPage() {
  const product = useLoaderData() as Product; // typed loader data
  const { productId } = useTypedParams<'productDetail'>();

  return (
    <div>
      <h1>{product.name}</h1>
      <p>Product ID: {productId}</p>
      <p>${product.price.toFixed(2)}</p>
      <p>{product.description}</p>
      <Link to={buildPath('products')}>← Back to Products</Link>
    </div>
  );
}

function SearchPage() {
  const [params, setParams] = useTypedSearchParams();

  return (
    <div>
      <h1>Search: {params.q ?? 'All'}</h1>
      <p>Page: {params.page}, Sort: {params.sort}</p>
      <button onClick={() => setParams({ page: params.page + 1 })}>
        Next Page
      </button>
    </div>
  );
}

// ✅ Step 7: Router config
const router = createBrowserRouter([
  { path: ROUTES.home, element: <div>Home</div> },
  { path: ROUTES.products, element: <div>Products List</div> },
  { path: ROUTES.productDetail, element: <ProductDetailPage />, loader: productLoader },
  { path: ROUTES.search, element: <SearchPage /> },
]);

function App() {
  return <RouterProvider router={router} />;
}
```

---

### Q15. How do you type Redux Toolkit — including `createSlice`, typed hooks, and async thunks?

**Answer:**

Redux Toolkit (RTK) is designed for TypeScript. The key pattern is: (1) define `RootState` and `AppDispatch` types from the store, (2) create typed hooks (`useAppSelector`, `useAppDispatch`) that replace the generic `useSelector` and `useDispatch`, and (3) type `createSlice` state and action payloads. For async operations, `createAsyncThunk` is generic over the return type, the argument type, and the thunk API config.

```tsx
// ---------- store.ts ----------
import { configureStore } from '@reduxjs/toolkit';
import { useSelector, useDispatch, type TypedUseSelectorHook } from 'react-redux';
import { productsSlice } from './productsSlice';
import { cartSlice } from './cartSlice';
import { authSlice } from './authSlice';

export const store = configureStore({
  reducer: {
    products: productsSlice.reducer,
    cart: cartSlice.reducer,
    auth: authSlice.reducer,
  },
});

// ✅ Infer types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// ✅ Typed hooks — use these everywhere instead of plain useSelector/useDispatch
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
export const useAppDispatch = () => useDispatch<AppDispatch>();

// ---------- productsSlice.ts ----------
import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from './store';

// ✅ Typed state
interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
}

interface ProductsState {
  items: Product[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  selectedCategory: string | null;
}

const initialState: ProductsState = {
  items: [],
  status: 'idle',
  error: null,
  selectedCategory: null,
};

// ✅ Typed async thunk — createAsyncThunk<ReturnType, ArgType, ThunkApiConfig>
export const fetchProducts = createAsyncThunk<
  Product[],                     // Return type on success
  { category?: string },         // Argument type
  { rejectValue: string }        // ThunkAPI config (for rejectWithValue)
>(
  'products/fetchProducts',
  async ({ category }, { rejectWithValue }) => {
    try {
      const url = category
        ? `/api/products?category=${category}`
        : '/api/products';
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as Product[];
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to fetch products'
      );
    }
  }
);

// ✅ Typed createSlice
export const productsSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    // PayloadAction<T> types the action.payload
    setCategory(state, action: PayloadAction<string | null>) {
      state.selectedCategory = action.payload;
    },
    clearProducts(state) {
      state.items = [];
      state.status = 'idle';
    },
    updateProductPrice(
      state,
      action: PayloadAction<{ id: string; newPrice: number }>
    ) {
      const product = state.items.find((p) => p.id === action.payload.id);
      if (product) {
        product.price = action.payload.newPrice;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload; // ✅ typed as Product[]
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload ?? 'Unknown error'; // ✅ typed as string
      });
  },
});

export const { setCategory, clearProducts, updateProductPrice } = productsSlice.actions;

// ✅ Typed selector
export const selectFilteredProducts = (state: RootState): Product[] => {
  const { items, selectedCategory } = state.products;
  if (!selectedCategory) return items;
  return items.filter((p) => p.category === selectedCategory);
};

// ---------- Component usage ----------
import { useEffect } from 'react';

function ProductList() {
  const dispatch = useAppDispatch();
  const products = useAppSelector(selectFilteredProducts); // ✅ Product[]
  const status = useAppSelector((state) => state.products.status); // ✅ 'idle' | 'loading' | ...
  const error = useAppSelector((state) => state.products.error);

  useEffect(() => {
    if (status === 'idle') {
      dispatch(fetchProducts({ category: undefined }));
    }
  }, [status, dispatch]);

  if (status === 'loading') return <p>Loading…</p>;
  if (status === 'failed') return <p>Error: {error}</p>;

  return (
    <div>
      {products.map((p) => (
        <div key={p.id}>
          <h3>{p.name}</h3>
          <p>${p.price.toFixed(2)}</p>
          <button
            onClick={() =>
              dispatch(updateProductPrice({ id: p.id, newPrice: p.price * 0.9 }))
            }
          >
            Apply 10% Discount
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

### Q16. How do you use template literal types to enforce design-system naming conventions in React components?

**Answer:**

**Template literal types** (introduced in TypeScript 4.1) let you construct string types from other string types using interpolation syntax. In a React design system, this is powerful for: (1) ensuring only valid CSS class combinations, (2) typing responsive prop variants, (3) creating type-safe spacing/color tokens, and (4) enforcing naming conventions across a component library.

The syntax mirrors JavaScript template literals but at the type level: `` type Greeting = `Hello, ${string}` ``. You can combine them with union types to generate all valid permutations automatically.

```tsx
// ✅ Example 1: Type-safe spacing scale
type SpacingUnit = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16 | 20 | 24;
type SpacingProp = `${SpacingUnit}` | `${SpacingUnit} ${SpacingUnit}` | `${SpacingUnit} ${SpacingUnit} ${SpacingUnit} ${SpacingUnit}`;

// ✅ Example 2: Type-safe color tokens
type ColorScale = 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900;
type ColorName = 'gray' | 'red' | 'blue' | 'green' | 'yellow' | 'purple';
type ColorToken = `${ColorName}-${ColorScale}`;
// Result: 'gray-50' | 'gray-100' | ... | 'purple-900' (60 valid tokens)

// ✅ Example 3: Responsive props with template literals
type Breakpoint = 'sm' | 'md' | 'lg' | 'xl';
type ResponsivePrefix = `${Breakpoint}:`;

type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
type ResponsiveSize = Size | `${Breakpoint}:${Size}`;

interface BoxProps {
  padding?: ResponsiveSize | ResponsiveSize[];
  margin?: ResponsiveSize | ResponsiveSize[];
  fontSize?: ResponsiveSize | ResponsiveSize[];
  display?: 'block' | 'flex' | 'grid' | 'none' | `${Breakpoint}:${'block' | 'flex' | 'grid' | 'none'}`;
}

function Box({ padding, margin, fontSize, display }: BoxProps) {
  // Convert responsive props to CSS classes
  const classes: string[] = [];

  if (padding) {
    const values = Array.isArray(padding) ? padding : [padding];
    values.forEach((v) => classes.push(`p-${v}`));
  }

  return <div className={classes.join(' ')} />;
}

// Usage
<Box padding="md" margin="lg" />                        // ✅
<Box padding={['sm', 'md:lg', 'xl:xl']} />              // ✅
// <Box padding="xxxl" />                                // ❌ Error — 'xxxl' not in Size

// ✅ Example 4: Event handler naming convention
type EventName = 'click' | 'hover' | 'focus' | 'blur' | 'change' | 'submit';
type EventHandlerName = `on${Capitalize<EventName>}`;
// Result: 'onClick' | 'onHover' | 'onFocus' | 'onBlur' | 'onChange' | 'onSubmit'

// ✅ Example 5: Type-safe CSS variable names
type CSSVariable = `--${string}`;
type ThemeVariable =
  | `--color-${ColorName}-${ColorScale}`
  | `--font-size-${Size}`
  | `--spacing-${SpacingUnit}`
  | `--radius-${'sm' | 'md' | 'lg' | 'full'}`;

function setThemeVariable(name: ThemeVariable, value: string) {
  document.documentElement.style.setProperty(name, value);
}

setThemeVariable('--color-blue-500', '#3b82f6');  // ✅
setThemeVariable('--spacing-4', '1rem');           // ✅
// setThemeVariable('--foo-bar', '1');              // ❌ Error

// ✅ Example 6: Component variant system with template literals
type Intent = 'primary' | 'secondary' | 'danger' | 'success' | 'warning';
type Appearance = 'solid' | 'outline' | 'ghost' | 'link';
type ButtonVariant = `${Intent}-${Appearance}`;
// Result: 'primary-solid' | 'primary-outline' | ... | 'warning-link' (20 variants)

interface DesignButtonProps {
  variant: ButtonVariant;
  size: Size;
  children: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  'primary-solid': 'bg-blue-600 text-white',
  'primary-outline': 'border-blue-600 text-blue-600',
  'primary-ghost': 'text-blue-600',
  'primary-link': 'text-blue-600 underline',
  'secondary-solid': 'bg-gray-600 text-white',
  // ... all 20 variants must be defined — compiler enforces completeness
} as Record<ButtonVariant, string>;

function DesignButton({ variant, size, children }: DesignButtonProps) {
  return (
    <button className={`${variantStyles[variant]} size-${size}`}>
      {children}
    </button>
  );
}

<DesignButton variant="primary-solid" size="md">Save</DesignButton>    // ✅
<DesignButton variant="danger-outline" size="lg">Delete</DesignButton>  // ✅
// <DesignButton variant="primary-big" size="md">Nope</DesignButton>   // ❌ Error
```

---

### Q17. How do you use conditional types to build adaptive component APIs in React 18?

**Answer:**

**Conditional types** follow the syntax `T extends U ? X : Y` — if `T` is assignable to `U`, the type resolves to `X`, otherwise `Y`. In React component design, conditional types let you create APIs where **the shape of the props changes based on the value of another prop**. This goes beyond discriminated unions (which require a literal discriminant) — conditional types can make entire groups of props appear or disappear, change types, or alter return types based on a generic parameter.

Common production uses: (1) a `<Field>` component where `type="select"` requires `options` but `type="text"` doesn't, (2) a `useQuery` hook where `enabled: false` changes the return type to exclude `data`, and (3) a `<Modal>` where `dismissable={true}` requires `onDismiss`.

```tsx
import type { ReactNode } from 'react';

// ✅ Example 1: Modal that conditionally requires onDismiss
type ModalProps<Dismissable extends boolean = false> = {
  title: string;
  children: ReactNode;
  isOpen: boolean;
  dismissable?: Dismissable;
} & (Dismissable extends true
  ? { onDismiss: () => void }  // Required when dismissable is true
  : { onDismiss?: never });     // Forbidden when dismissable is false

function Modal<D extends boolean = false>({
  title,
  children,
  isOpen,
  dismissable,
  ...rest
}: ModalProps<D>) {
  if (!isOpen) return null;

  const onDismiss = (rest as { onDismiss?: () => void }).onDismiss;

  return (
    <div className="modal-overlay" onClick={dismissable ? onDismiss : undefined}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          {dismissable && <button onClick={onDismiss}>✕</button>}
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

// ✅ Correct usage
<Modal title="Info" isOpen={true}>
  <p>Non-dismissable modal — onDismiss not needed</p>
</Modal>

<Modal title="Confirm" isOpen={true} dismissable={true} onDismiss={() => setOpen(false)}>
  <p>Dismissable — onDismiss is required</p>
</Modal>

// ❌ Error — dismissable is true but onDismiss is missing
// <Modal title="Oops" isOpen={true} dismissable={true}><p>Broken</p></Modal>

// ✅ Example 2: Conditional return type based on config
type QueryResult<TData, TEnabled extends boolean> = TEnabled extends true
  ? { data: TData; isLoading: boolean; error: Error | null }
  : { data: undefined; isLoading: false; error: null };

interface QueryConfig<TData, TEnabled extends boolean = true> {
  queryKey: string[];
  queryFn: () => Promise<TData>;
  enabled?: TEnabled;
}

declare function useTypedQuery<TData, TEnabled extends boolean = true>(
  config: QueryConfig<TData, TEnabled>
): QueryResult<TData, TEnabled>;

// When enabled is true (default), data is TData
const { data: user } = useTypedQuery({
  queryKey: ['user'],
  queryFn: () => fetch('/api/user').then((r) => r.json()),
}); // data: User ✅

// When enabled is false, data is undefined
const { data: nope } = useTypedQuery({
  queryKey: ['user'],
  queryFn: () => fetch('/api/user').then((r) => r.json()),
  enabled: false as const,
}); // data: undefined ✅ — no need to check for undefined at runtime

// ✅ Example 3: Extracting specific types conditionally
type ExtractArrayItem<T> = T extends (infer U)[] ? U : T;

type A = ExtractArrayItem<string[]>;   // string
type B = ExtractArrayItem<number>;     // number (not an array, returns T)

// ✅ Example 4: Component that changes behavior based on `multiple` prop
type SelectFieldProps<Multiple extends boolean = false> = {
  label: string;
  options: { value: string; label: string }[];
  multiple?: Multiple;
} & (Multiple extends true
  ? { value: string[]; onChange: (values: string[]) => void }
  : { value: string; onChange: (value: string) => void });

function SelectField<M extends boolean = false>(props: SelectFieldProps<M>) {
  const { label, options, multiple } = props;

  if (multiple) {
    const { value, onChange } = props as SelectFieldProps<true>;
    return (
      <div>
        <label>{label}</label>
        <select
          multiple
          value={value}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions, (o) => o.value);
            onChange(selected);
          }}
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>
    );
  }

  const { value, onChange } = props as SelectFieldProps<false>;
  return (
    <div>
      <label>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

// Usage
<SelectField
  label="Country"
  options={[{ value: 'us', label: 'USA' }]}
  value="us"
  onChange={(v) => console.log(v)} // v: string ✅
/>

<SelectField
  label="Languages"
  options={[{ value: 'en', label: 'English' }, { value: 'es', label: 'Spanish' }]}
  multiple={true}
  value={['en', 'es']}
  onChange={(v) => console.log(v)} // v: string[] ✅
/>
```

---

### Q18. How do you build a type-safe API layer with typed server responses in a React 18 application?

**Answer:**

In production, the API layer is where **the untyped outside world meets your typed application**. A type-safe API layer ensures: (1) every endpoint has a defined request and response shape, (2) runtime data is validated before it enters the React tree, (3) generic fetch wrappers propagate types through the call chain, and (4) adding or modifying an endpoint produces compile-time errors everywhere the change matters.

The pattern combines: a typed endpoint registry (mapping paths to request/response types), a generic API client, Zod for runtime validation, and integration with TanStack Query for React consumption.

```tsx
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// ✅ Step 1: Define Zod schemas for all API entities
const userSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  email: z.string().email(),
  role: z.enum(['admin', 'editor', 'viewer']),
  createdAt: z.string().datetime(),
});

const productSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  price: z.number().positive(),
  category: z.string(),
  inStock: z.boolean(),
});

const paginatedResponseSchema = <T extends z.ZodType>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number(),
    page: z.number(),
    pageSize: z.number(),
    hasNextPage: z.boolean(),
  });

// Infer TypeScript types from schemas
type User = z.infer<typeof userSchema>;
type Product = z.infer<typeof productSchema>;

// ✅ Step 2: Define the API endpoint registry
interface ApiEndpoints {
  // GET endpoints
  'GET /api/users': {
    params: { page?: number; role?: User['role'] };
    response: z.infer<ReturnType<typeof paginatedResponseSchema<typeof userSchema>>>;
  };
  'GET /api/users/:id': {
    params: { id: string };
    response: User;
  };
  'GET /api/products': {
    params: { page?: number; category?: string };
    response: z.infer<ReturnType<typeof paginatedResponseSchema<typeof productSchema>>>;
  };
  // POST endpoints
  'POST /api/users': {
    body: Omit<User, 'id' | 'createdAt'>;
    response: User;
  };
  'POST /api/products': {
    body: Omit<Product, 'id'>;
    response: Product;
  };
  // PUT endpoints
  'PUT /api/users/:id': {
    params: { id: string };
    body: Partial<Omit<User, 'id' | 'createdAt'>>;
    response: User;
  };
  // DELETE endpoints
  'DELETE /api/users/:id': {
    params: { id: string };
    response: { success: boolean };
  };
}

// ✅ Step 3: Type-safe API client
class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

async function apiClient<E extends keyof ApiEndpoints>(
  endpoint: E,
  options?: {
    params?: 'params' extends keyof ApiEndpoints[E] ? ApiEndpoints[E]['params'] : never;
    body?: 'body' extends keyof ApiEndpoints[E] ? ApiEndpoints[E]['body'] : never;
  }
): Promise<ApiEndpoints[E]['response']> {
  const [method, pathTemplate] = (endpoint as string).split(' ') as [string, string];

  // Replace URL params
  let path = pathTemplate;
  if (options?.params && typeof options.params === 'object') {
    const params = options.params as Record<string, unknown>;
    Object.entries(params).forEach(([key, value]) => {
      if (path.includes(`:${key}`)) {
        path = path.replace(`:${key}`, String(value));
      }
    });

    // Add remaining params as query string (for GET)
    if (method === 'GET') {
      const queryParams = Object.entries(params)
        .filter(([key]) => !pathTemplate.includes(`:${key}`))
        .filter(([, v]) => v !== undefined);

      if (queryParams.length > 0) {
        path += '?' + new URLSearchParams(
          queryParams.map(([k, v]) => [k, String(v)])
        ).toString();
      }
    }
  }

  const res = await fetch(path, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: options?.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    throw new ApiError(res.status, res.statusText, await res.json().catch(() => null));
  }

  return res.json();
}

// ✅ Step 4: Type-safe React hooks built on TanStack Query

function useUsers(params?: ApiEndpoints['GET /api/users']['params']) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => apiClient('GET /api/users', { params }),
  });
}

function useUser(id: string) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => apiClient('GET /api/users/:id', { params: { id } }),
    enabled: !!id,
  });
}

function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ApiEndpoints['POST /api/users']['body']) =>
      apiClient('POST /api/users', { body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

// ✅ Step 5: Usage in components — fully typed end-to-end
function UserManagement() {
  const { data, isLoading, error } = useUsers({ page: 1, role: 'admin' });
  const createUser = useCreateUser();

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <ul>
        {data?.items.map((user) => (
          <li key={user.id}>
            {user.name} — {user.email} — {user.role}
          </li>
        ))}
      </ul>
      <button
        onClick={() =>
          createUser.mutate({
            name: 'New User',
            email: 'new@example.com',
            role: 'viewer',
          })
        }
      >
        Add User
      </button>
    </div>
  );
}
```

---

### Q19. What is the recommended strict-mode TypeScript configuration for a React 18 project — and what does each option do?

**Answer:**

A production React 18 project should use the strictest TypeScript configuration practical. The `strict` flag is actually a shorthand that enables ~10 individual checks. Beyond `strict`, there are additional flags that catch common React bugs. Understanding each flag helps you explain to a team *why* strict mode matters and handle legacy codebases where you must enable flags incrementally.

```tsx
// tsconfig.json — recommended strict configuration for React 18
{
  "compilerOptions": {
    // ---------- Strict mode family ----------
    "strict": true,
    // "strict": true enables ALL of the following:
    //   "noImplicitAny": true        — error when TS infers 'any'
    //   "strictNullChecks": true     — null/undefined are distinct types
    //   "strictFunctionTypes": true  — contravariant function param checks
    //   "strictBindCallApply": true  — type-check bind/call/apply
    //   "strictPropertyInitialization": true — class props must be initialized
    //   "noImplicitThis": true       — error when 'this' is 'any'
    //   "useUnknownInCatchVariables": true — catch(e) types e as 'unknown'
    //   "alwaysStrict": true         — emit 'use strict' in every file

    // ---------- Additional strictness beyond "strict" ----------
    "noUncheckedIndexedAccess": true,
    // Array/object index access returns T | undefined, not just T
    // Without this: const x = arr[999] → typed as string (wrong — may be undefined)
    // With this:    const x = arr[999] → typed as string | undefined ✅

    "noUnusedLocals": true,
    // Error on declared but unused variables

    "noUnusedParameters": true,
    // Error on unused function parameters (prefix with _ to suppress)

    "noImplicitReturns": true,
    // Error if a function with a return type doesn't return in all branches

    "noFallthroughCasesInSwitch": true,
    // Error on switch case fallthrough without break/return

    "exactOptionalPropertyTypes": true,
    // Distinguishes between { x?: string } (missing) and { x: undefined }
    // Prevents accidentally passing undefined to optional props

    "noPropertyAccessFromIndexSignature": true,
    // Forces bracket notation for index-signature access

    // ---------- Module & JSX ----------
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",           // React 18's automatic JSX transform
    "esModuleInterop": true,
    "isolatedModules": true,       // Required for most bundlers (Vite, esbuild)
    "resolveJsonModule": true,
    "allowJs": false,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "skipLibCheck": true,          // Speeds up compilation; checks your code, not node_modules

    // ---------- Path aliases ----------
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@utils/*": ["./src/utils/*"],
      "@types/*": ["./src/types/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx"],
  "exclude": ["node_modules", "dist", "build"]
}
```

**Why each strict flag matters for React 18:**

```tsx
// ✅ noImplicitAny — catches untyped event handlers
// Without: onChange={(e) => setName(e.target.value)} — e is 'any'
// With: TS forces you to type the parameter or rely on contextual typing

// ✅ strictNullChecks — the MOST important flag for React
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  // Without strictNullChecks: user.name compiles (💥 runtime null crash)
  // With strictNullChecks: user.name is an error — must check null first
  if (!user) return <p>Loading…</p>;
  return <h1>{user.name}</h1>; // ✅ user is narrowed to User
}

// ✅ noUncheckedIndexedAccess — catches array out-of-bounds
function FirstItem({ items }: { items: string[] }) {
  const first = items[0];
  // Without: first is string (but items could be empty!)
  // With: first is string | undefined — forces a check ✅
  return <p>{first ?? 'No items'}</p>;
}

// ✅ useUnknownInCatchVariables — forces safe error handling
async function fetchData() {
  try {
    await fetch('/api/data');
  } catch (error) {
    // Without: error is 'any' — error.message compiles (could be anything)
    // With: error is 'unknown' — must check type first
    if (error instanceof Error) {
      console.error(error.message); // ✅ safe
    }
  }
}

// ✅ exactOptionalPropertyTypes — prevents sneaky undefined
interface Config {
  theme?: 'light' | 'dark';
}

// Without: { theme: undefined } is valid (but probably a bug)
// With: { theme: undefined } is an ERROR — either set a value or omit the key
const config: Config = {}; // ✅ key omitted — correct way
```

---

### Q20. How do you build a fully type-safe form builder with recursive types in TypeScript + React 18?

**Answer:**

A **type-safe form builder** is an advanced pattern where you define a form's structure as a nested TypeScript type, and the builder generates: (1) the correct form field components, (2) the typed initial values, (3) the typed validation rules, and (4) the typed `onSubmit` output — all from a single schema definition. **Recursive types** are needed because forms can have nested field groups (e.g., `address.street`, `contacts[0].email`).

This is the kind of problem that pushes TypeScript to its limits — requiring recursive types, mapped types, conditional types, template literal types, and infer patterns all working together.

```tsx
import { useState, useCallback, type ReactNode, type ChangeEvent } from 'react';

// ============================================================
// Part 1: The Type-Level Form Schema
// ============================================================

// A field definition — each kind of field has different config
type FieldDef =
  | { kind: 'text'; label: string; required?: boolean; placeholder?: string }
  | { kind: 'number'; label: string; required?: boolean; min?: number; max?: number }
  | { kind: 'select'; label: string; required?: boolean; options: readonly string[] }
  | { kind: 'checkbox'; label: string }
  | { kind: 'group'; label: string; fields: FormSchema }  // ← recursive!
  | { kind: 'array'; label: string; itemFields: FormSchema }; // ← recursive!

// A form schema is a record of field names to field definitions
type FormSchema = Record<string, FieldDef>;

// ============================================================
// Part 2: Infer the form VALUES type from the schema
// ============================================================

// This recursive mapped type derives the data shape from the schema
type InferFormValues<S extends FormSchema> = {
  [K in keyof S]: S[K] extends { kind: 'text' }
    ? string
    : S[K] extends { kind: 'number' }
    ? number
    : S[K] extends { kind: 'select'; options: readonly (infer O)[] }
    ? O
    : S[K] extends { kind: 'checkbox' }
    ? boolean
    : S[K] extends { kind: 'group'; fields: infer F extends FormSchema }
    ? InferFormValues<F>  // ← recurse into group
    : S[K] extends { kind: 'array'; itemFields: infer F extends FormSchema }
    ? InferFormValues<F>[]  // ← recurse into array
    : never;
};

// ============================================================
// Part 3: Define a schema and see the magic
// ============================================================

const userFormSchema = {
  name: { kind: 'text', label: 'Full Name', required: true, placeholder: 'John Doe' },
  age: { kind: 'number', label: 'Age', required: true, min: 0, max: 150 },
  role: {
    kind: 'select',
    label: 'Role',
    required: true,
    options: ['admin', 'editor', 'viewer'] as const,
  },
  isActive: { kind: 'checkbox', label: 'Active' },
  address: {
    kind: 'group',
    label: 'Address',
    fields: {
      street: { kind: 'text', label: 'Street', required: true },
      city: { kind: 'text', label: 'City', required: true },
      zip: { kind: 'text', label: 'ZIP Code' },
    },
  },
  contacts: {
    kind: 'array',
    label: 'Contacts',
    itemFields: {
      type: { kind: 'select', label: 'Type', options: ['email', 'phone'] as const },
      value: { kind: 'text', label: 'Value', required: true },
    },
  },
} as const satisfies FormSchema;

// ✅ The inferred type — automatically derived from the schema!
type UserFormValues = InferFormValues<typeof userFormSchema>;
// Result:
// {
//   name: string;
//   age: number;
//   role: 'admin' | 'editor' | 'viewer';
//   isActive: boolean;
//   address: {
//     street: string;
//     city: string;
//     zip: string;
//   };
//   contacts: {
//     type: 'email' | 'phone';
//     value: string;
//   }[];
// }

// ============================================================
// Part 4: Type-safe dot-path access for nested fields
// ============================================================

// Recursive template literal type for dot paths: 'address.street', 'contacts.0.value'
type DotPath<T> = T extends object
  ? {
      [K in keyof T & string]: T[K] extends (infer U)[]
        ? K | `${K}.${number}` | `${K}.${number}.${DotPath<U> & string}`
        : T[K] extends object
        ? K | `${K}.${DotPath<T[K]> & string}`
        : K;
    }[keyof T & string]
  : never;

type UserFormPaths = DotPath<UserFormValues>;
// 'name' | 'age' | 'role' | 'isActive'
// | 'address' | 'address.street' | 'address.city' | 'address.zip'
// | 'contacts' | `contacts.${number}` | `contacts.${number}.type` | `contacts.${number}.value`

// Get the type at a specific dot path
type GetAtPath<T, P extends string> = P extends `${infer K}.${infer Rest}`
  ? K extends keyof T
    ? T[K] extends (infer U)[]
      ? Rest extends `${number}.${infer DeepRest}`
        ? GetAtPath<U, DeepRest>
        : Rest extends `${number}`
        ? U
        : never
      : GetAtPath<T[K], Rest>
    : never
  : P extends keyof T
  ? T[P]
  : never;

// Examples:
type NameType = GetAtPath<UserFormValues, 'name'>;            // string
type CityType = GetAtPath<UserFormValues, 'address.city'>;    // string
type ContactType = GetAtPath<UserFormValues, 'contacts.0.type'>; // 'email' | 'phone'

// ============================================================
// Part 5: The form builder hook
// ============================================================

function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, key) => {
    if (acc && typeof acc === 'object') return (acc as Record<string, unknown>)[key];
    return undefined;
  }, obj);
}

function setNestedValue(obj: Record<string, unknown>, path: string, value: unknown): Record<string, unknown> {
  const clone = structuredClone(obj);
  const keys = path.split('.');
  let current: Record<string, unknown> = clone;
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (!(key in current) || typeof current[key] !== 'object') {
      current[key] = isNaN(Number(keys[i + 1])) ? {} : [];
    }
    current = current[key] as Record<string, unknown>;
  }
  current[keys[keys.length - 1]] = value;
  return clone;
}

interface UseFormBuilderReturn<S extends FormSchema> {
  values: InferFormValues<S>;
  getValue: <P extends DotPath<InferFormValues<S>> & string>(
    path: P
  ) => GetAtPath<InferFormValues<S>, P>;
  setValue: <P extends DotPath<InferFormValues<S>> & string>(
    path: P,
    value: GetAtPath<InferFormValues<S>, P>
  ) => void;
  handleSubmit: (onSubmit: (data: InferFormValues<S>) => void) => (e: React.FormEvent) => void;
  reset: () => void;
}

function useFormBuilder<S extends FormSchema>(
  _schema: S,
  initialValues: InferFormValues<S>
): UseFormBuilderReturn<S> {
  const [values, setValues] = useState(initialValues);

  const getValue = useCallback(
    (path: string) => getNestedValue(values as Record<string, unknown>, path),
    [values]
  ) as UseFormBuilderReturn<S>['getValue'];

  const setValue = useCallback(
    (path: string, value: unknown) => {
      setValues((prev) =>
        setNestedValue(prev as Record<string, unknown>, path, value) as InferFormValues<S>
      );
    },
    []
  ) as unknown as UseFormBuilderReturn<S>['setValue'];

  const handleSubmit = useCallback(
    (onSubmit: (data: InferFormValues<S>) => void) => (e: React.FormEvent) => {
      e.preventDefault();
      onSubmit(values);
    },
    [values]
  );

  const reset = useCallback(() => setValues(initialValues), [initialValues]);

  return { values, getValue, setValue, handleSubmit, reset };
}

// ============================================================
// Part 6: Usage — everything is type-safe
// ============================================================

function UserForm() {
  const { values, getValue, setValue, handleSubmit, reset } = useFormBuilder(
    userFormSchema,
    {
      name: '',
      age: 0,
      role: 'viewer',
      isActive: true,
      address: { street: '', city: '', zip: '' },
      contacts: [],
    }
  );

  const onSubmit = (data: UserFormValues) => {
    console.log(data.name);              // ✅ string
    console.log(data.role);              // ✅ 'admin' | 'editor' | 'viewer'
    console.log(data.address.city);      // ✅ string
    console.log(data.contacts[0]?.type); // ✅ 'email' | 'phone'
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        value={getValue('name')}
        onChange={(e) => setValue('name', e.target.value)} // ✅ value must be string
      />
      <input
        type="number"
        value={getValue('age')}
        onChange={(e) => setValue('age', Number(e.target.value))} // ✅ value must be number
      />
      <select
        value={getValue('role')}
        onChange={(e) => setValue('role', e.target.value as 'admin' | 'editor' | 'viewer')}
      >
        <option value="admin">Admin</option>
        <option value="editor">Editor</option>
        <option value="viewer">Viewer</option>
      </select>
      <input
        value={getValue('address.city')}
        onChange={(e) => setValue('address.city', e.target.value)} // ✅ nested path is typed
      />

      {/* ❌ These would cause compile-time errors: */}
      {/* setValue('name', 42)                — number is not string */}
      {/* setValue('age', 'twenty')            — string is not number */}
      {/* setValue('role', 'superadmin')       — not in the union */}
      {/* setValue('nonexistent.path', 'foo')  — path does not exist */}
      {/* getValue('address.country')          — path does not exist */}

      <button type="submit">Submit</button>
      <button type="button" onClick={reset}>Reset</button>
    </form>
  );
}
```

**Key takeaways for the interview:**

1. **Recursive types** (`InferFormValues` calls itself for `group` and `array` kinds) are the foundation — they let a single schema drive the entire type structure to arbitrary depth.
2. **Template literal types** (`DotPath`) generate all valid path strings from the nested structure.
3. **Conditional types** (`GetAtPath`) resolve the type at any path — so `setValue('address.city', ...)` knows the second argument must be `string`.
4. **`as const satisfies`** locks the schema to its literal types while ensuring it conforms to `FormSchema`.
5. This pattern is used in production by form libraries like **react-hook-form** (deep `Path<T>` type), **tRPC** (end-to-end type inference), and **Zod** (recursive schema inference).

---
