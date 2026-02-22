# React 19 New Features — Interview Questions

## Topic Introduction

React 19 is the most significant major release since React 18 introduced concurrent rendering. While React 18 focused on *how* React renders (interruptible, concurrent), React 19 focuses on *what* developers actually build — data fetching, form handling, metadata management, and reducing boilerplate. The headline features include **Actions** (a new pattern for handling async mutations with built-in pending/error/optimistic states), the **`use()` API** (a new way to read Promises and Context that breaks the "rules of hooks" by working inside conditionals and loops), **`useActionState`** and **`useFormStatus`** (first-class form state management), **`useOptimistic`** (instant UI feedback while the server processes), **ref as a prop** (eliminating `forwardRef`), **native document metadata** (`<title>`, `<meta>`, `<link>` hoisted automatically), **resource preloading APIs** (`preload`, `preinit`), and **ref cleanup functions**. React 19 also brings Server Actions into the stable API, improved error reporting, and significant TypeScript improvements. The overall theme is: *less boilerplate, more built-in solutions for real-world patterns*.

For developers coming from React 18, the migration is relatively smooth — React 19 is largely additive. The biggest breaking changes are the removal of legacy APIs that were already deprecated (`ReactDOM.render`, `ReactDOM.hydrate`, string refs, legacy Context, etc.) and some subtle behavioral changes like stricter Strict Mode, ref cleanup functions, and Context rendering changes. The React team provides **codemods** (`npx codemod@latest react/19/...`) that automate most migration tasks. Understanding these changes is critical for 2026 interviews because companies are actively migrating to React 19, and interviewers want candidates who understand not just *what* changed, but *why* it changed and how to leverage the new APIs to write cleaner, more performant code.

Here is a comparison table showing the key differences between React 18 and React 19, followed by a code illustration:

| Feature | React 18 | React 19 |
|---|---|---|
| Async data in components | `useEffect` + `useState` | `use(promise)` + `<Suspense>` |
| Reading context | `useContext(MyContext)` | `use(MyContext)` (works in conditionals) |
| Forwarding refs | `forwardRef((props, ref) => ...)` | `ref` is a regular prop |
| Form submission state | Manual `useState` for pending/error | `useActionState(action, initialState)` |
| Form pending status | Prop drill `isPending` to children | `useFormStatus()` reads parent form |
| Optimistic updates | Manual state management | `useOptimistic(state, updateFn)` |
| Data mutations | Custom async handlers | Actions with `<form action={fn}>` |
| Context providers | `<MyContext.Provider value={...}>` | `<MyContext value={...}>` |
| Document `<title>` | `react-helmet` or `useEffect` | `<title>` in component JSX (hoisted) |
| Resource preloading | Manual `<link>` tags | `preload()`, `preinit()` APIs |
| Ref cleanup | No cleanup; use `useEffect` | Return cleanup fn from ref callback |
| Error handling | `onRecoverableError` only | Detailed `onCaughtError`, `onUncaughtError` |

```jsx
// React 19 at a glance — a single component using multiple new features
import { use, useOptimistic, useActionState, Suspense } from 'react';

// A context used with use() instead of useContext
const ThemeContext = React.createContext('light');

// An async server action
async function addTodo(prevState, formData) {
  'use server';
  const title = formData.get('title');
  await db.todos.create({ title });
  return { ...prevState, todos: [...prevState.todos, { title }] };
}

function TodoApp() {
  const theme = use(ThemeContext); // use() instead of useContext()

  const [state, submitAction, isPending] = useActionState(addTodo, {
    todos: [],
  });

  const [optimisticTodos, addOptimistic] = useOptimistic(
    state.todos,
    (current, newTitle) => [...current, { title: newTitle, pending: true }]
  );

  return (
    // Context shorthand — no more .Provider
    <ThemeContext value={theme}>
      <title>My Todo App</title> {/* Native metadata — hoisted to <head> */}
      <meta name="description" content="A React 19 todo app" />

      <form action={async (formData) => {
        addOptimistic(formData.get('title'));
        await submitAction(formData);
      }}>
        <input name="title" required />
        {/* ref as prop — no forwardRef needed */}
        <SubmitButton />
      </form>

      <ul>
        {optimisticTodos.map((todo, i) => (
          <li key={i} style={{ opacity: todo.pending ? 0.5 : 1 }}>
            {todo.title}
          </li>
        ))}
      </ul>
    </ThemeContext>
  );
}
```

In the example above, a single component leverages `use()` for context, `useActionState` for form handling, `useOptimistic` for instant feedback, the Context shorthand, native `<title>` and `<meta>` tags, and the Actions pattern — all new to React 19.

---

## Beginner Level (Q1–Q5)

---

### Q1. What are the major new features in React 19 and why is this release significant?

**Answer:**

React 19 is a paradigm shift in how React handles common application patterns. While React 18 focused on rendering mechanics (concurrent rendering, automatic batching, transitions), React 19 focuses on **developer experience and built-in solutions** for patterns that previously required boilerplate code or third-party libraries.

The major new features are:

1. **Actions** — A new pattern for handling data mutations. Functions passed to `<form action={fn}>` or `startTransition` that perform async work are called "Actions." React automatically manages pending states, errors, and optimistic updates.

2. **`use()` API** — A new function (not a hook) that can read Promises and Context. Unlike hooks, it can be called inside conditionals, loops, and early returns.

3. **`useActionState`** — A hook that manages the full lifecycle of a form action: the result, pending state, and error handling.

4. **`useFormStatus`** — A hook that lets child components read the pending/submitting status of a parent `<form>` without prop drilling.

5. **`useOptimistic`** — A hook for showing optimistic UI updates immediately while the actual async operation completes.

6. **Ref as a prop** — Function components can accept `ref` as a regular prop. `forwardRef` is no longer needed.

7. **Context shorthand** — `<MyContext value={...}>` replaces `<MyContext.Provider value={...}>`.

8. **Document Metadata** — `<title>`, `<meta>`, and `<link>` tags rendered inside components are automatically hoisted to `<head>`.

9. **Resource Preloading** — New `preload()`, `preinit()` APIs for optimizing resource loading.

10. **Ref Cleanup Functions** — Ref callbacks can return a cleanup function, similar to `useEffect`.

```jsx
// React 18: The old way — lots of boilerplate for a simple form
import { useState, useContext, forwardRef } from 'react';

const ThemeContext = React.createContext('light');

const Input = forwardRef((props, ref) => (
  <input ref={ref} {...props} />
));

function AddTodoForm() {
  const theme = useContext(ThemeContext);
  const [title, setTitle] = useState('');
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsPending(true);
    setError(null);
    try {
      await saveTodo(title);
      setTitle('');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsPending(false);
    }
  };

  return (
    <ThemeContext.Provider value={theme}>
      <form onSubmit={handleSubmit}>
        <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        <button disabled={isPending}>
          {isPending ? 'Saving...' : 'Add'}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </ThemeContext.Provider>
  );
}
```

```jsx
// React 19: The new way — built-in form handling, no forwardRef, context shorthand
import { useActionState } from 'react';

const ThemeContext = React.createContext('light');

// ref is now just a prop — no forwardRef needed
function Input({ ref, ...props }) {
  return <input ref={ref} {...props} />;
}

function AddTodoForm() {
  const [state, submitAction, isPending] = useActionState(
    async (prevState, formData) => {
      try {
        await saveTodo(formData.get('title'));
        return { error: null };
      } catch (err) {
        return { error: err.message };
      }
    },
    { error: null }
  );

  return (
    <ThemeContext value="light"> {/* No .Provider needed */}
      <form action={submitAction}>
        <Input name="title" required />
        <button disabled={isPending}>
          {isPending ? 'Saving...' : 'Add'}
        </button>
        {state.error && <p className="error">{state.error}</p>}
      </form>
    </ThemeContext>
  );
}
```

**Key takeaway:** React 19 eliminates the majority of "ceremony" code that developers have been writing for years — manual pending states, `forwardRef` wrappers, `useEffect` for data fetching, third-party libraries for metadata, and prop drilling for form states.

---

### Q2. What is the `use()` API and how does it differ from React hooks?

**Answer:**

`use()` is a new React API introduced in React 19 that can **read the value of a resource** — currently supporting **Promises** and **Context**. Despite looking similar to hooks, `use()` is fundamentally different: it is **not a hook** and does **not** follow the Rules of Hooks. This means you can call `use()` inside conditionals, loops, early returns, and after other hooks — something that would be illegal with `useContext` or any other hook.

When used with a **Promise**, `use()` integrates with Suspense. It suspends the component while the Promise is pending, and when the Promise resolves, React re-renders the component with the resolved value. If the Promise rejects, the nearest Error Boundary catches the error.

When used with **Context**, `use()` works like `useContext()` but with the added flexibility of conditional calls.

**Key differences from hooks:**

| Aspect | Hooks (`useContext`, etc.) | `use()` |
|---|---|---|
| Conditionals/loops | Not allowed | Allowed |
| Early returns | Cannot call after return | Can call after return |
| Reads Promises | No | Yes (suspends) |
| Reads Context | `useContext(Ctx)` | `use(Ctx)` |
| Rules of Hooks | Must follow | Does not apply |

```jsx
// React 18: useContext — MUST be called at top level, unconditionally
import { useContext } from 'react';

function Greeting({ showExtras }) {
  // ❌ This is ILLEGAL in React 18:
  // if (showExtras) {
  //   const theme = useContext(ThemeContext); // Hook in conditional!
  // }

  // ✅ Must always call at top level, even if not needed
  const theme = useContext(ThemeContext);
  const user = useContext(UserContext);

  if (!showExtras) {
    return <p>Hello!</p>;
  }

  return (
    <div style={{ color: theme.textColor }}>
      <p>Hello, {user.name}!</p>
    </div>
  );
}
```

```jsx
// React 19: use() — CAN be called conditionally
import { use } from 'react';

function Greeting({ showExtras }) {
  // ✅ Totally legal in React 19 — use() is not a hook
  if (!showExtras) {
    return <p>Hello!</p>;
  }

  // Only read context when we actually need it
  const theme = use(ThemeContext);
  const user = use(UserContext);

  return (
    <div style={{ color: theme.textColor }}>
      <p>Hello, {user.name}!</p>
    </div>
  );
}
```

```jsx
// React 19: use() with Promises — data fetching with Suspense
import { use, Suspense } from 'react';

function UserProfile({ userPromise }) {
  // use() suspends until the promise resolves
  const user = use(userPromise);

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}

// Parent wraps with Suspense to show fallback while loading
function App() {
  const userPromise = fetchUser(123); // Returns a Promise

  return (
    <Suspense fallback={<p>Loading user...</p>}>
      <UserProfile userPromise={userPromise} />
    </Suspense>
  );
}
```

**Key takeaway:** `use()` is not a hook — it's a new kind of API that reads resources. Its superpower is that it can be called conditionally, making it far more flexible than `useContext`. When used with Promises, it provides a clean alternative to `useEffect`-based data fetching.

---

### Q3. How does `ref` as a prop work in React 19, and why was `forwardRef` removed?

**Answer:**

In React 19, function components can accept `ref` as a **regular prop** in their props object. This eliminates the need for `React.forwardRef()`, which was the only way to pass a `ref` from a parent to a child function component in React 18 and earlier.

`forwardRef` was always considered an awkward API — it wrapped your component in a higher-order component, made the type signature more complex, and confused developers learning React. The React team identified it as unnecessary ceremony since `ref` is conceptually just another prop that happens to hold a mutable ref object.

In React 19, `forwardRef` still works (it's not removed yet) but is **deprecated**. The React team provides a codemod to automatically remove `forwardRef` wrappers: `npx codemod@latest react/19/replace-reactdom-render`.

```jsx
// React 18: forwardRef required to pass refs to function components
import { forwardRef, useRef } from 'react';

// Wrapping in forwardRef — extra boilerplate, confusing signature
const FancyInput = forwardRef((props, ref) => {
  return (
    <div className="fancy-wrapper">
      <input
        ref={ref}
        className="fancy-input"
        placeholder={props.placeholder}
      />
    </div>
  );
});

// TypeScript made it even more verbose:
// const FancyInput = forwardRef<HTMLInputElement, FancyInputProps>(
//   (props, ref) => { ... }
// );

FancyInput.displayName = 'FancyInput'; // Needed for DevTools

function Form() {
  const inputRef = useRef(null);

  const focusInput = () => {
    inputRef.current?.focus();
  };

  return (
    <div>
      <FancyInput ref={inputRef} placeholder="Type here..." />
      <button onClick={focusInput}>Focus</button>
    </div>
  );
}
```

```jsx
// React 19: ref is just a prop — no forwardRef needed
import { useRef } from 'react';

// ref is destructured alongside other props — clean and simple
function FancyInput({ placeholder, ref }) {
  return (
    <div className="fancy-wrapper">
      <input
        ref={ref}
        className="fancy-input"
        placeholder={placeholder}
      />
    </div>
  );
}

// TypeScript is cleaner too:
// function FancyInput({ placeholder, ref }: {
//   placeholder: string;
//   ref?: React.Ref<HTMLInputElement>;
// }) { ... }

function Form() {
  const inputRef = useRef(null);

  const focusInput = () => {
    inputRef.current?.focus();
  };

  return (
    <div>
      <FancyInput ref={inputRef} placeholder="Type here..." />
      <button onClick={focusInput}>Focus</button>
    </div>
  );
}
```

**Key takeaway:** In React 19, `ref` is a regular prop. No wrapping, no `forwardRef`, no `displayName` hacks. This simplifies component APIs, improves TypeScript support, and reduces one of React's most common sources of confusion.

---

### Q4. What is the new Context shorthand in React 19?

**Answer:**

In React 19, you can render a Context object directly as a provider using `<MyContext value={...}>` instead of the verbose `<MyContext.Provider value={...}>`. The `.Provider` property still works but is **deprecated** and will be removed in a future major version.

This is a small but meaningful change that reduces nesting and makes JSX cleaner, especially when you have multiple contexts. The Context object itself now acts as the provider component.

```jsx
// React 18: Must use .Provider — verbose, especially with multiple contexts
import { createContext, useContext } from 'react';

const ThemeContext = createContext('light');
const AuthContext = createContext(null);
const LocaleContext = createContext('en');

function App() {
  return (
    // Deep nesting with .Provider everywhere
    <ThemeContext.Provider value="dark">
      <AuthContext.Provider value={{ user: 'Alice', role: 'admin' }}>
        <LocaleContext.Provider value="en-US">
          <Dashboard />
        </LocaleContext.Provider>
      </AuthContext.Provider>
    </ThemeContext.Provider>
  );
}

function Dashboard() {
  const theme = useContext(ThemeContext);
  const auth = useContext(AuthContext);
  const locale = useContext(LocaleContext);

  return <p>{`${auth.user} in ${theme} mode (${locale})`}</p>;
}
```

```jsx
// React 19: Render Context directly — cleaner JSX
import { createContext, use } from 'react';

const ThemeContext = createContext('light');
const AuthContext = createContext(null);
const LocaleContext = createContext('en');

function App() {
  return (
    // No .Provider needed — much cleaner
    <ThemeContext value="dark">
      <AuthContext value={{ user: 'Alice', role: 'admin' }}>
        <LocaleContext value="en-US">
          <Dashboard />
        </LocaleContext>
      </AuthContext>
    </ThemeContext>
  );
}

function Dashboard() {
  // Can also use use() instead of useContext — works the same
  const theme = use(ThemeContext);
  const auth = use(AuthContext);
  const locale = use(LocaleContext);

  return <p>{`${auth.user} in ${theme} mode (${locale})`}</p>;
}
```

**Codemod:** Run `npx codemod@latest react/19/replace-use-form-state` (the React 19 codemods cover multiple transformations — check the official docs for the context-specific one).

**Key takeaway:** `<MyContext value={...}>` is the new way to provide context. It's a drop-in replacement that reduces visual noise. Combined with `use(MyContext)` instead of `useContext(MyContext)`, React 19 makes the context API significantly cleaner.

---

### Q5. How does React 19 handle document metadata like `<title>` and `<meta>` tags?

**Answer:**

In React 19, you can render `<title>`, `<meta>`, and `<link>` tags **directly inside your component JSX**, and React will automatically **hoist** them into the document's `<head>` section. This is a built-in feature that eliminates the need for third-party libraries like `react-helmet` or `react-helmet-async`.

React 19 handles deduplication intelligently — if multiple components render a `<title>`, the last one rendered wins. For `<meta>` tags, React deduplicates by `name` or `property` attribute. For `<link rel="stylesheet">`, React also ensures stylesheets are loaded before the content that depends on them is displayed.

```jsx
// React 18: Required third-party library (react-helmet-async)
import { Helmet } from 'react-helmet-async';

function ProductPage({ product }) {
  return (
    <>
      <Helmet>
        <title>{product.name} | MyStore</title>
        <meta name="description" content={product.description} />
        <meta property="og:title" content={product.name} />
        <meta property="og:image" content={product.imageUrl} />
        <link rel="canonical" href={`https://mystore.com/p/${product.slug}`} />
      </Helmet>

      <div className="product-page">
        <h1>{product.name}</h1>
        <p>{product.description}</p>
        <img src={product.imageUrl} alt={product.name} />
      </div>
    </>
  );
}

// Also required a HelmetProvider wrapper at the root
function App() {
  return (
    <HelmetProvider>
      <Router>
        <Routes>
          <Route path="/product/:id" element={<ProductPage />} />
        </Routes>
      </Router>
    </HelmetProvider>
  );
}
```

```jsx
// React 19: Native metadata support — no library needed
function ProductPage({ product }) {
  return (
    <>
      {/* These are hoisted to <head> automatically */}
      <title>{product.name} | MyStore</title>
      <meta name="description" content={product.description} />
      <meta property="og:title" content={product.name} />
      <meta property="og:image" content={product.imageUrl} />
      <link rel="canonical" href={`https://mystore.com/p/${product.slug}`} />

      <div className="product-page">
        <h1>{product.name}</h1>
        <p>{product.description}</p>
        <img src={product.imageUrl} alt={product.name} />
      </div>
    </>
  );
}

// No provider wrapper needed at root
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/product/:id" element={<ProductPage />} />
      </Routes>
    </Router>
  );
}
```

**How it works under the hood:** When React encounters `<title>`, `<meta>`, or `<link>` tags during rendering, it does not insert them where they appear in the component tree. Instead, it hoists them to the `<head>` element of the document. During SSR, these tags are included in the streamed `<head>` HTML. During client-side rendering, React inserts/updates them in the DOM's `<head>`.

**Key takeaway:** React 19 eliminates the need for `react-helmet`. You can render SEO-critical metadata directly in your components, and React handles hoisting, deduplication, and SSR streaming automatically.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How does `use()` with Suspense replace `useEffect` for data fetching?

**Answer:**

In React 18, the standard pattern for data fetching was `useEffect` + `useState` — you'd start a fetch in an effect, manage loading/error/data states manually, and handle race conditions yourself. This pattern had well-known problems: waterfalls (child components can't fetch until parent renders), no SSR support, and race conditions when dependencies change.

React 19's `use()` API integrates with Suspense to provide a fundamentally different model: you **pass a Promise to the component** and `use()` **suspends** until it resolves. The parent component wraps the child in `<Suspense>` to show a fallback. This model eliminates manual loading state, prevents waterfalls (since Promises are created in the parent before the child renders), and works seamlessly with SSR streaming.

**Important:** The Promise should be created **outside** the rendering component — typically in a parent, a loader, or a data cache. If you create the Promise inside the component that calls `use()`, it will create a new Promise on every render, causing an infinite suspend loop.

```jsx
// React 18: useEffect + useState — manual loading, error, race conditions
import { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false; // Race condition guard
    setLoading(true);
    setError(null);

    fetch(`/api/users/${userId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
      })
      .then((data) => {
        if (!cancelled) {
          setUser(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true; // Cleanup for race conditions
    };
  }, [userId]);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}

function App() {
  return <UserProfile userId={123} />;
}
```

```jsx
// React 19: use() + Suspense — no manual state, no race conditions
import { use, Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

// Data fetching utility — creates a cached Promise
function fetchUser(userId) {
  return fetch(`/api/users/${userId}`).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  });
}

function UserProfile({ userPromise }) {
  // use() suspends until the promise resolves
  // No loading state, no error state, no useEffect, no cleanup
  const user = use(userPromise);

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}

function App() {
  // Promise is created in the PARENT — not inside UserProfile
  const userPromise = fetchUser(123);

  return (
    <ErrorBoundary fallback={<ErrorMessage />}>
      <Suspense fallback={<Spinner />}>
        <UserProfile userPromise={userPromise} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

**Why is this better?**

1. **No waterfall** — The Promise starts in the parent, so data fetching begins before UserProfile even mounts.
2. **No race conditions** — React handles component unmounting/remounting; stale Promises are discarded.
3. **No manual loading/error state** — Suspense handles loading, ErrorBoundary handles errors.
4. **SSR compatible** — Suspense boundaries stream HTML as data resolves.
5. **Less code** — The component only contains the "happy path" rendering logic.

**Key takeaway:** `use(promise)` + Suspense replaces the `useEffect` data-fetching pattern with a model that's simpler, race-condition-free, SSR-compatible, and eliminates loading/error boilerplate.

---

### Q7. What is `useActionState` and how does it manage form submissions?

**Answer:**

`useActionState` is a new hook in React 19 that manages the **complete lifecycle of a form action**: the result/state from the last submission, a wrapped action function to pass to `<form action={...}>`, and a boolean `isPending` flag. It replaces the manual pattern of `useState` + `useTransition` that was required in React 18 for form handling.

**Signature:** `const [state, formAction, isPending] = useActionState(fn, initialState, permalink?)`

- `fn` — The action function. Receives `(previousState, formData)` and returns the new state.
- `initialState` — The initial state value before the form is submitted.
- `permalink` — Optional URL for progressive enhancement (used with SSR).
- Returns `[state, formAction, isPending]` — current state, wrapped action, and pending boolean.

The action function can be `async` — React will automatically set `isPending` to `true` while it executes and `false` when it completes.

```jsx
// React 18: Manual form state management — verbose and error-prone
import { useState, useTransition } from 'react';

function ContactForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    startTransition(async () => {
      try {
        const response = await fetch('/api/contact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, message }),
        });

        if (!response.ok) {
          const data = await response.json();
          setError(data.error || 'Submission failed');
          return;
        }

        setSuccess(true);
        setName('');
        setEmail('');
        setMessage('');
      } catch (err) {
        setError('Network error. Please try again.');
      }
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      <textarea value={message} onChange={(e) => setMessage(e.target.value)} />
      <button disabled={isPending}>
        {isPending ? 'Sending...' : 'Send'}
      </button>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">Message sent!</p>}
    </form>
  );
}
```

```jsx
// React 19: useActionState — clean, declarative form handling
import { useActionState } from 'react';

async function submitContact(prevState, formData) {
  const name = formData.get('name');
  const email = formData.get('email');
  const message = formData.get('message');

  try {
    const response = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, message }),
    });

    if (!response.ok) {
      const data = await response.json();
      return { error: data.error || 'Submission failed', success: false };
    }

    return { error: null, success: true };
  } catch (err) {
    return { error: 'Network error. Please try again.', success: false };
  }
}

function ContactForm() {
  const [state, formAction, isPending] = useActionState(submitContact, {
    error: null,
    success: false,
  });

  return (
    <form action={formAction}>
      <input name="name" required />
      <input name="email" type="email" required />
      <textarea name="message" required />
      <button disabled={isPending}>
        {isPending ? 'Sending...' : 'Send'}
      </button>
      {state.error && <p className="error">{state.error}</p>}
      {state.success && <p className="success">Message sent!</p>}
    </form>
  );
}
```

**Key differences:**

1. **No `e.preventDefault()`** — The form `action` prop handles submission natively.
2. **No controlled inputs** — Using `name` attributes + `FormData` means no `useState` per field.
3. **No manual `isPending`** — `useActionState` provides it automatically.
4. **Previous state pattern** — The action receives `prevState`, enabling reducer-like state management.
5. **Progressive enhancement** — If JavaScript hasn't loaded yet, the form can still submit (with the `permalink` option).

**Key takeaway:** `useActionState` replaces the multi-`useState` + `useTransition` pattern with a single hook that manages form action state, pending status, and error handling in a declarative, progressive-enhancement-friendly way.

---

### Q8. What is `useFormStatus` and how does it solve prop drilling in forms?

**Answer:**

`useFormStatus` is a hook in React 19 (from `react-dom`) that lets a **child component** read the status of its **parent `<form>`** — specifically whether the form is currently submitting. This eliminates the common pattern of drilling `isPending` props down through form component hierarchies.

**Signature:** `const { pending, data, method, action } = useFormStatus()`

- `pending` — `true` while the form's action is executing.
- `data` — The `FormData` object being submitted.
- `method` — The HTTP method (`'get'` or `'post'`).
- `action` — A reference to the action function.

**Critical rule:** `useFormStatus` must be called from a component that is **rendered inside a `<form>`**. It reads the status of the nearest parent `<form>`, not a form you pass to it.

```jsx
// React 18: Prop drilling isPending through form components
import { useState, useTransition } from 'react';

function SubmitButton({ isPending, label }) {
  return (
    <button type="submit" disabled={isPending}>
      {isPending ? 'Submitting...' : label}
    </button>
  );
}

function FormFields({ isPending }) {
  return (
    <fieldset disabled={isPending}>
      <input name="title" placeholder="Title" />
      <textarea name="body" placeholder="Body" />
      {/* Must pass isPending deeper if there are more nested components */}
      <SubmitButton isPending={isPending} label="Publish" />
    </fieldset>
  );
}

function PostForm() {
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (e) => {
    e.preventDefault();
    startTransition(async () => {
      const formData = new FormData(e.target);
      await fetch('/api/posts', {
        method: 'POST',
        body: formData,
      });
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* isPending must be drilled to every child that needs it */}
      <FormFields isPending={isPending} />
    </form>
  );
}
```

```jsx
// React 19: useFormStatus — no prop drilling needed
import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';

// This component automatically knows the form's pending state
function SubmitButton({ label }) {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Submitting...' : label}
    </button>
  );
}

// Fieldset that disables itself during submission
function FormFields() {
  const { pending } = useFormStatus();

  return (
    <fieldset disabled={pending}>
      <input name="title" placeholder="Title" />
      <textarea name="body" placeholder="Body" />
      <SubmitButton label="Publish" />
    </fieldset>
  );
}

// The parent form — no need to pass isPending anywhere
function PostForm() {
  const [state, formAction] = useActionState(async (prev, formData) => {
    await fetch('/api/posts', { method: 'POST', body: formData });
    return { success: true };
  }, { success: false });

  return (
    <form action={formAction}>
      {/* No props needed — children use useFormStatus() */}
      <FormFields />
      {state.success && <p>Published!</p>}
    </form>
  );
}
```

**Key takeaway:** `useFormStatus` eliminates prop drilling for form submission state. Any component inside a `<form>` can independently read whether the form is submitting, what data is being sent, and what action is being called — without receiving any props from the parent.

---

### Q9. How does `useOptimistic` work and when should you use it?

**Answer:**

`useOptimistic` is a React 19 hook that lets you show an **optimistic (hopeful) UI update immediately** while an async operation (like a server request) is in progress. If the operation succeeds, the real server data replaces the optimistic data. If it fails, the optimistic update is automatically rolled back to the previous state.

**Signature:** `const [optimisticState, addOptimistic] = useOptimistic(state, updateFn)`

- `state` — The actual current state (source of truth, typically from server).
- `updateFn` — A pure function `(currentState, optimisticValue) => newState` that produces the optimistic state.
- Returns `[optimisticState, addOptimistic]` — the state to render (which may be optimistic) and a function to trigger optimistic updates.

The optimistic state automatically reverts to the real `state` when the async Action completes (whether it succeeds or fails). This means you get rollback for free.

```jsx
// React 18: Manual optimistic updates — complex and error-prone
import { useState, useTransition } from 'react';

function MessageList({ initialMessages }) {
  const [messages, setMessages] = useState(initialMessages);
  const [optimisticIds, setOptimisticIds] = useState(new Set());
  const [isPending, startTransition] = useTransition();

  const sendMessage = async (text) => {
    // Optimistic: add message with a temporary ID
    const tempId = `temp-${Date.now()}`;
    const optimisticMsg = { id: tempId, text, sending: true };

    setMessages((prev) => [...prev, optimisticMsg]);
    setOptimisticIds((prev) => new Set(prev).add(tempId));

    startTransition(async () => {
      try {
        const savedMsg = await fetch('/api/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        }).then((r) => r.json());

        // Replace optimistic message with real server response
        setMessages((prev) =>
          prev.map((m) => (m.id === tempId ? savedMsg : m))
        );
      } catch (err) {
        // Rollback on failure
        setMessages((prev) => prev.filter((m) => m.id !== tempId));
        alert('Failed to send message');
      } finally {
        setOptimisticIds((prev) => {
          const next = new Set(prev);
          next.delete(tempId);
          return next;
        });
      }
    });
  };

  return (
    <div>
      {messages.map((msg) => (
        <div
          key={msg.id}
          style={{ opacity: optimisticIds.has(msg.id) ? 0.6 : 1 }}
        >
          {msg.text}
          {msg.sending && <span> (sending...)</span>}
        </div>
      ))}
      <ComposeBox onSend={sendMessage} />
    </div>
  );
}
```

```jsx
// React 19: useOptimistic — clean, with automatic rollback
import { useOptimistic, useActionState } from 'react';

function MessageList({ messages, sendMessageAction }) {
  const [optimisticMessages, addOptimistic] = useOptimistic(
    messages,
    // Pure function: merge optimistic value into current state
    (currentMessages, newMessageText) => [
      ...currentMessages,
      { id: `temp-${Date.now()}`, text: newMessageText, sending: true },
    ]
  );

  const [state, formAction] = useActionState(
    async (prevState, formData) => {
      const text = formData.get('message');
      // Show optimistic update IMMEDIATELY
      addOptimistic(text);
      // Perform the actual server mutation
      const result = await sendMessageAction(text);
      // When this completes, optimistic state automatically reverts
      // and `messages` prop updates with the real server data
      return result;
    },
    null
  );

  return (
    <div>
      {optimisticMessages.map((msg) => (
        <div key={msg.id} style={{ opacity: msg.sending ? 0.6 : 1 }}>
          {msg.text}
          {msg.sending && <span> (sending...)</span>}
        </div>
      ))}
      <form action={formAction}>
        <input name="message" required />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

**When to use `useOptimistic`:**

- **Like/unlike** buttons — show the heart filled immediately.
- **Todo completion** — check the checkbox instantly.
- **Chat messages** — display the message before server confirms.
- **Any mutation** where the user expects instant feedback and the server rarely fails.

**Key takeaway:** `useOptimistic` provides automatic optimistic updates with built-in rollback. You define *how* the optimistic state should look, and React automatically reverts to the real state when the Action completes — no manual rollback code needed.

---

### Q10. What are Actions in React 19 and how do they change data mutation patterns?

**Answer:**

**Actions** are a new concept in React 19 that represent the standard pattern for performing data mutations. An Action is any async function used in a transition — whether it's a function passed to `<form action={fn}>`, called inside `startTransition`, or wrapped by `useActionState`. React 19 provides built-in support for the three things every mutation needs: **pending state** (is the operation in progress?), **optimistic updates** (show expected result immediately), and **error handling** (what if it fails?).

The key insight is that React now understands `<form action={fn}>` natively. When a form is submitted with an action function, React automatically wraps the call in a transition, provides the `FormData` to the function, and manages the form's pending state. This works for both client-side actions and Server Actions.

```jsx
// React 18: The manual mutation pattern — lots of ceremony
import { useState, useTransition, useCallback } from 'react';

function TodoApp() {
  const [todos, setTodos] = useState([]);
  const [error, setError] = useState(null);
  const [isPending, startTransition] = useTransition();

  const addTodo = useCallback(async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const title = formData.get('title');
    setError(null);

    startTransition(async () => {
      try {
        const res = await fetch('/api/todos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title }),
        });
        if (!res.ok) throw new Error('Failed to add todo');
        const newTodo = await res.json();
        setTodos((prev) => [...prev, newTodo]);
        e.target.reset();
      } catch (err) {
        setError(err.message);
      }
    });
  }, []);

  const deleteTodo = useCallback(async (id) => {
    setError(null);
    startTransition(async () => {
      try {
        await fetch(`/api/todos/${id}`, { method: 'DELETE' });
        setTodos((prev) => prev.filter((t) => t.id !== id));
      } catch (err) {
        setError(err.message);
      }
    });
  }, []);

  return (
    <div>
      <form onSubmit={addTodo}>
        <input name="title" disabled={isPending} />
        <button disabled={isPending}>
          {isPending ? 'Adding...' : 'Add'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      <ul>
        {todos.map((todo) => (
          <li key={todo.id}>
            {todo.title}
            <button onClick={() => deleteTodo(todo.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

```jsx
// React 19: Actions — clean, declarative data mutations
import { useActionState, useOptimistic } from 'react';

// Action function — receives prevState and formData
async function addTodoAction(prevState, formData) {
  const title = formData.get('title');

  try {
    const res = await fetch('/api/todos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Failed to add todo');
    const newTodo = await res.json();
    return {
      todos: [...prevState.todos, newTodo],
      error: null,
    };
  } catch (err) {
    return { ...prevState, error: err.message };
  }
}

function TodoApp() {
  const [state, formAction, isPending] = useActionState(addTodoAction, {
    todos: [],
    error: null,
  });

  const [optimisticTodos, addOptimistic] = useOptimistic(
    state.todos,
    (current, newTitle) => [...current, { id: `temp-${Date.now()}`, title: newTitle, pending: true }]
  );

  return (
    <div>
      <form action={async (formData) => {
        addOptimistic(formData.get('title'));
        await formAction(formData);
      }}>
        <input name="title" required />
        <SubmitButton /> {/* Uses useFormStatus — no props needed */}
      </form>

      {state.error && <p className="error">{state.error}</p>}

      <ul>
        {optimisticTodos.map((todo) => (
          <li key={todo.id} style={{ opacity: todo.pending ? 0.5 : 1 }}>
            {todo.title}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**What makes something an "Action"?**

1. Functions passed to `<form action={fn}>` — React provides `FormData` automatically.
2. Async functions used inside `startTransition(async () => { ... })`.
3. Functions wrapped by `useActionState` — get `prevState` and return new state.
4. **Server Actions** — functions marked with `'use server'` that run on the server.

**Key takeaway:** Actions unify the data mutation pattern in React 19. They provide automatic pending states, integrate with `useOptimistic` for instant feedback, and work with `useFormStatus` for prop-drilling-free UI updates — all with less code than the React 18 equivalent.

---

### Q11. How do Form Actions work with progressive enhancement in React 19?

**Answer:**

Progressive enhancement means that a form works **before JavaScript loads** (plain HTML form submission) and then **enhances** with JavaScript once the app hydrates. React 19's `<form action={fn}>` pattern supports this natively, especially when combined with Server Actions in frameworks like Next.js.

When you pass a function to `<form action={...}>`, React intercepts the submission client-side. But if you also provide a `permalink` to `useActionState`, the form can submit as a traditional HTML form before JavaScript loads — the server handles the submission and redirects to the permalink URL.

This matters for:
- **Slow connections** — Users can interact with forms before the JS bundle downloads.
- **SEO** — Search engine crawlers can submit forms.
- **Accessibility** — Assistive technologies work with native form submission.

```jsx
// React 18: No progressive enhancement — form is dead without JS
import { useState } from 'react';

function SearchForm() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  // This handler ONLY works when JavaScript is loaded
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevents native behavior
    const res = await fetch(`/api/search?q=${query}`);
    const data = await res.json();
    setResults(data.results);
  };

  return (
    // If JS fails to load, this form does NOTHING
    <form onSubmit={handleSubmit}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
      />
      <button type="submit">Search</button>
      <ul>
        {results.map((r) => <li key={r.id}>{r.title}</li>)}
      </ul>
    </form>
  );
}
```

```jsx
// React 19: Progressive enhancement — works before AND after JS loads
import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';

async function searchAction(prevState, formData) {
  const query = formData.get('q');
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  const data = await res.json();
  return { results: data.results };
}

function SearchButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Searching...' : 'Search'}
    </button>
  );
}

function SearchForm() {
  const [state, formAction, isPending] = useActionState(
    searchAction,
    { results: [] },
    // Permalink: where to go if JS hasn't loaded and the form submits natively
    '/search'
  );

  return (
    // Before JS: submits as native POST to /search
    // After JS: intercepted by React, runs searchAction client-side
    <form action={formAction}>
      <input name="q" placeholder="Search..." />
      <SearchButton />
      <ul>
        {state.results.map((r) => <li key={r.id}>{r.title}</li>)}
      </ul>
    </form>
  );
}
```

```jsx
// React 19 + Next.js: Server Action with full progressive enhancement
// app/search/page.tsx
import { searchProducts } from './actions';

export default function SearchPage() {
  return (
    // action={serverFunction} — works as native POST before hydration
    <form action={searchProducts}>
      <input name="q" placeholder="Search products..." />
      <button type="submit">Search</button>
    </form>
  );
}

// app/search/actions.ts
'use server';

export async function searchProducts(formData) {
  const query = formData.get('q');
  const results = await db.products.search(query);
  redirect(`/search?q=${query}`);
}
```

**Key takeaway:** React 19's form actions enable true progressive enhancement — forms work as native HTML submissions before JavaScript loads, then enhance with client-side handling, optimistic updates, and pending states after hydration. This is a significant improvement over React 18 where forms were completely inert without JavaScript.

---

### Q12. What are the resource preloading APIs (`preload`, `preinit`) in React 19?

**Answer:**

React 19 introduces new APIs in `react-dom` for **preloading resources** — stylesheets, fonts, scripts, and other external assets. These APIs let you tell the browser to start fetching resources early, before they're actually needed in the render tree. This reduces perceived load times by parallelizing resource fetching with rendering.

**The APIs:**

| API | Purpose | Example |
|---|---|---|
| `preload(href, options)` | Fetch a resource early (doesn't execute) | Fonts, images |
| `preinit(href, options)` | Fetch AND execute/apply immediately | Stylesheets, scripts |
| `prefetchDNS(href)` | Resolve DNS for a domain early | Third-party APIs |
| `preconnect(href)` | Establish TCP/TLS connection early | CDNs |

```jsx
// React 18: Manual resource hints — scattered across your app
import { useEffect } from 'react';

function App() {
  // Approach 1: Static HTML (not dynamic)
  // <link rel="preload" href="/fonts/inter.woff2" as="font" />

  // Approach 2: useEffect (too late — runs after paint)
  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = '/fonts/inter.woff2';
    link.as = 'font';
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
    return () => document.head.removeChild(link);
  }, []);

  return <div>App content</div>;
}

// Approach 3: Next.js-specific Head component
import Head from 'next/head';

function Page() {
  return (
    <>
      <Head>
        <link rel="preconnect" href="https://api.example.com" />
        <link
          rel="preload"
          href="/fonts/inter.woff2"
          as="font"
          crossOrigin="anonymous"
        />
      </Head>
      <div>Page content</div>
    </>
  );
}
```

```jsx
// React 19: Built-in preloading APIs — declarative and automatic
import { preload, preinit, prefetchDNS, preconnect } from 'react-dom';

function App() {
  // Preconnect to CDNs and APIs early
  prefetchDNS('https://analytics.example.com');
  preconnect('https://cdn.example.com');

  // Preload a font — browser fetches it but doesn't apply yet
  preload('/fonts/inter.woff2', { as: 'font', type: 'font/woff2' });

  // Preinit a stylesheet — browser fetches AND applies it
  preinit('/styles/critical.css', { as: 'style' });

  // Preinit a script — browser fetches AND executes it
  preinit('https://cdn.example.com/analytics.js', { as: 'script' });

  return <div>App content</div>;
}

// Use in route-level components for route-specific preloading
function ProductPage({ productId }) {
  // Preload the product image as soon as this component starts rendering
  preload(`/api/products/${productId}/image.jpg`, { as: 'image' });

  // Preload the reviews API endpoint
  preload(`/api/products/${productId}/reviews`, { as: 'fetch' });

  return (
    <Suspense fallback={<Skeleton />}>
      <ProductDetails id={productId} />
      <ProductReviews id={productId} />
    </Suspense>
  );
}

// Dynamic preloading based on user interaction
function NavigationLink({ href, children }) {
  const handleMouseEnter = () => {
    // Preload the page's resources when user hovers
    preload(href, { as: 'document' });
    preload(`${href}/data.json`, { as: 'fetch' });
  };

  return (
    <a href={href} onMouseEnter={handleMouseEnter}>
      {children}
    </a>
  );
}
```

**How React handles stylesheets in components:**

```jsx
// React 19: Stylesheet components with ordering control
function DashboardWidget({ data }) {
  return (
    <>
      {/* React ensures this stylesheet is loaded BEFORE the content paints */}
      <link rel="stylesheet" href="/styles/widget.css" precedence="default" />

      <div className="widget">
        <h3>{data.title}</h3>
        <p>{data.value}</p>
      </div>
    </>
  );
}
```

**Key takeaway:** React 19's preloading APIs (`preload`, `preinit`, `prefetchDNS`, `preconnect`) provide declarative, component-level control over resource loading. They emit proper resource hints during SSR and dynamically during client-side rendering, eliminating the need for `useEffect` hacks or framework-specific head components.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do Server Actions work in React 19 and how do they bridge client-server boundaries?

**Answer:**

Server Actions are functions marked with `'use server'` that execute on the **server** but can be called from **client components** as if they were regular async functions. They are a stable feature in React 19 (previously experimental in React canary builds used by Next.js). Server Actions eliminate the need to create API routes for data mutations — you write a function, mark it as a server function, and React handles the serialization, network request, and response.

**How they work under the hood:**

1. You define a function with `'use server'` at the top (either in a `'use server'` file or inline).
2. The bundler replaces the function in the client bundle with a **reference** (a URL + ID).
3. When the client calls the function, React serializes the arguments, sends an HTTP POST to the server, the server executes the function, and the result is serialized back.
4. Server Actions can be passed to `<form action={...}>`, `useActionState`, or called directly.

```jsx
// React 18 / Traditional: Separate API route + client fetch
// ─── api/routes/todo.js (server) ───
export async function POST(request) {
  const { title } = await request.json();

  // Validation
  if (!title || title.length < 3) {
    return Response.json({ error: 'Title too short' }, { status: 400 });
  }

  const todo = await db.todos.create({ data: { title } });
  return Response.json(todo);
}

// ─── components/TodoForm.jsx (client) ───
import { useState, useTransition } from 'react';

function TodoForm({ onAdd }) {
  const [error, setError] = useState(null);
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (e) => {
    e.preventDefault();
    const title = new FormData(e.target).get('title');
    setError(null);

    startTransition(async () => {
      const res = await fetch('/api/routes/todo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.error);
        return;
      }

      const todo = await res.json();
      onAdd(todo);
      e.target.reset();
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="title" />
      <button disabled={isPending}>Add</button>
      {error && <p>{error}</p>}
    </form>
  );
}
```

```jsx
// React 19: Server Action — no API route needed
// ─── actions/todo.js (server) ───
'use server';

import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';

export async function addTodo(prevState, formData) {
  const title = formData.get('title');

  // Server-side validation
  if (!title || title.length < 3) {
    return { error: 'Title must be at least 3 characters' };
  }

  try {
    await db.todos.create({ data: { title } });
    revalidatePath('/todos'); // Refresh cached data
    return { error: null };
  } catch (err) {
    return { error: 'Failed to create todo' };
  }
}

// ─── components/TodoForm.jsx (client) ───
'use client';

import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';
import { addTodo } from '@/actions/todo';

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Adding...' : 'Add Todo'}
    </button>
  );
}

function TodoForm() {
  const [state, formAction] = useActionState(addTodo, { error: null });

  return (
    <form action={formAction}>
      <input name="title" required minLength={3} />
      <SubmitButton />
      {state.error && <p className="error">{state.error}</p>}
    </form>
  );
}
```

**Security considerations:**

- Server Actions are exposed as public HTTP endpoints. **Always validate inputs** on the server.
- Never trust that the caller is authenticated just because the action is called from your UI.
- Use session/token validation inside every Server Action.

```jsx
// ─── Secure Server Action ───
'use server';

import { auth } from '@/lib/auth';

export async function deletePost(prevState, formData) {
  // ALWAYS verify authentication — anyone can call this endpoint
  const session = await auth();
  if (!session) {
    return { error: 'Unauthorized' };
  }

  const postId = formData.get('postId');
  const post = await db.posts.findUnique({ where: { id: postId } });

  // Authorization check
  if (post.authorId !== session.userId) {
    return { error: 'Forbidden' };
  }

  await db.posts.delete({ where: { id: postId } });
  revalidatePath('/posts');
  return { error: null };
}
```

**Key takeaway:** Server Actions eliminate the API route layer for data mutations. You write a server function, call it from a client component, and React handles serialization and transport. They integrate seamlessly with `useActionState`, `useFormStatus`, and `useOptimistic`, but you must always validate inputs and authenticate users since they are public HTTP endpoints.

---

### Q14. How do ref cleanup functions work in React 19?

**Answer:**

In React 19, **ref callback functions can return a cleanup function**, similar to how `useEffect` returns a cleanup function. When the element is removed from the DOM (or the ref changes), React calls the cleanup function. This eliminates the need for a separate `useEffect` to clean up ref-related side effects.

Previously in React 18, when a ref callback returned `undefined`, React would call the same callback with `null` when the element unmounted. This was confusing and error-prone. React 19's cleanup function pattern is much cleaner and more intuitive.

**Important breaking change:** Because React 19 uses the return value as a cleanup function, returning anything other than a function (like accidentally returning a value from an arrow function without braces) can cause issues. React will warn if you return something that isn't a function.

```jsx
// React 18: Ref callback with separate useEffect for cleanup
import { useCallback, useEffect, useRef } from 'react';

function AutoResizeTextarea() {
  const textareaRef = useRef(null);
  const observerRef = useRef(null);

  // Ref callback — receives null on unmount
  const setTextareaRef = useCallback((node) => {
    if (node !== null) {
      // Setup: element mounted
      textareaRef.current = node;
    } else {
      // Cleanup: node is null, element unmounted
      // But we need to clean up the observer!
      textareaRef.current = null;
    }
  }, []);

  // Separate useEffect needed for observer cleanup
  useEffect(() => {
    const node = textareaRef.current;
    if (!node) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const height = entry.contentRect.height;
        console.log('Textarea height:', height);
      }
    });

    observer.observe(node);
    observerRef.current = observer;

    return () => {
      observer.disconnect();
      observerRef.current = null;
    };
  }, []); // Tricky: this only runs once, but what if the ref changes?

  return <textarea ref={setTextareaRef} />;
}
```

```jsx
// React 19: Ref callback with cleanup function — clean and self-contained
function AutoResizeTextarea() {
  return (
    <textarea
      ref={(node) => {
        // Setup: element mounted — node is the DOM element
        const observer = new ResizeObserver((entries) => {
          for (const entry of entries) {
            const height = entry.contentRect.height;
            console.log('Textarea height:', height);
          }
        });

        observer.observe(node);

        // Cleanup: return a function, called when element unmounts
        return () => {
          observer.disconnect();
        };
      }}
    />
  );
}
```

Here is a more complex real-world example showing the difference:

```jsx
// React 18: Intersection Observer with ref — needs useEffect coordination
import { useRef, useEffect, useCallback, useState } from 'react';

function LazyImage({ src, alt }) {
  const [isVisible, setIsVisible] = useState(false);
  const imgRef = useRef(null);

  useEffect(() => {
    const node = imgRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(node);
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={imgRef}>
      {isVisible ? (
        <img src={src} alt={alt} />
      ) : (
        <div className="placeholder" />
      )}
    </div>
  );
}
```

```jsx
// React 19: Intersection Observer with ref cleanup — everything in one place
import { useState } from 'react';

function LazyImage({ src, alt }) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      ref={(node) => {
        if (isVisible) return; // Already loaded, no need to observe

        const observer = new IntersectionObserver(
          ([entry]) => {
            if (entry.isIntersecting) {
              setIsVisible(true);
              observer.unobserve(node);
            }
          },
          { threshold: 0.1 }
        );

        observer.observe(node);

        return () => observer.disconnect();
      }}
    >
      {isVisible ? (
        <img src={src} alt={alt} />
      ) : (
        <div className="placeholder" />
      )}
    </div>
  );
}
```

**Migration note:** If your React 18 ref callbacks return something (like an implicit arrow function return), you'll get warnings in React 19. The fix is to use explicit braces `{}` so the callback returns `undefined`:

```jsx
// ❌ Implicit return — React 19 thinks this is a cleanup function
<div ref={(node) => (instanceRef.current = node)} />

// ✅ Explicit block — returns undefined, no cleanup
<div ref={(node) => { instanceRef.current = node; }} />
```

**Key takeaway:** Ref cleanup functions in React 19 mirror the `useEffect` cleanup pattern. They make ref-related side effects self-contained — setup and cleanup live together in the ref callback, eliminating the need for coordinating between ref callbacks and `useEffect`.

---

### Q15. What are the error handling improvements in React 19?

**Answer:**

React 19 significantly improves error handling with two new `createRoot` options — `onCaughtError` and `onUncaughtError` — that replace the less specific `onRecoverableError` from React 18. React 19 also changes how errors are reported to the console: it no longer double-logs errors and provides more useful error information including component stacks by default.

**The three error callbacks in React 19:**

| Callback | When it fires | Example |
|---|---|---|
| `onCaughtError` | An error caught by an Error Boundary | Component render error, caught by `<ErrorBoundary>` |
| `onUncaughtError` | An error NOT caught by any Error Boundary | Top-level render crash |
| `onRecoverableError` | An error React recovers from automatically | Hydration mismatch (recovers by client-rendering) |

**Console logging changes:**

- React 18: `console.error` called twice for every error (once by React, once by the browser's error handling) — confusing in logs.
- React 19: Each error is logged once with a clear, actionable message including component stack traces.

```jsx
// React 18: Limited error reporting
import { createRoot } from 'react-dom/client';

const root = createRoot(document.getElementById('root'), {
  // Only one callback — hard to distinguish error types
  onRecoverableError: (error) => {
    // Fires for hydration mismatches and some edge cases
    // But NOT for errors caught by Error Boundaries
    // And NOT for uncaught render errors
    console.error('Recoverable:', error);
  },
});

root.render(<App />);

// In React 18, error boundaries had no global hook:
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // This is the ONLY place to log boundary-caught errors
    // No way to report them centrally from createRoot
    logToService(error, info.componentStack);
  }

  render() {
    if (this.state.hasError) return <p>Something went wrong</p>;
    return this.props.children;
  }
}
```

```jsx
// React 19: Comprehensive error handling with three callbacks
import { createRoot } from 'react-dom/client';

const root = createRoot(document.getElementById('root'), {
  // NEW: Fires when an Error Boundary catches an error
  onCaughtError: (error, errorInfo) => {
    // Report to error tracking service (Sentry, DataDog, etc.)
    errorTracker.captureException(error, {
      extra: {
        componentStack: errorInfo.componentStack,
        type: 'caught',
      },
    });
    console.warn('Caught by boundary:', error.message);
  },

  // NEW: Fires when an error is NOT caught by any Error Boundary
  onUncaughtError: (error, errorInfo) => {
    // This is critical — the app is crashing
    errorTracker.captureException(error, {
      level: 'fatal',
      extra: {
        componentStack: errorInfo.componentStack,
        type: 'uncaught',
      },
    });
    console.error('UNCAUGHT (app crash):', error.message);
  },

  // Still available: fires for hydration mismatches and auto-recoveries
  onRecoverableError: (error, errorInfo) => {
    errorTracker.captureException(error, {
      level: 'warning',
      extra: {
        componentStack: errorInfo.componentStack,
        type: 'recoverable',
      },
    });
    console.warn('Recovered automatically:', error.message);
  },
});

root.render(<App />);
```

```jsx
// React 19: Better error messages with component stacks
// Before (React 18): Error messages were cryptic and double-logged

// After (React 19): Clear, single-logged errors with component context
// Error: Failed to fetch user data
//   at UserProfile (app/components/UserProfile.jsx:15:5)
//   at Suspense
//   at Dashboard (app/pages/Dashboard.jsx:8:3)
//   at App (app/App.jsx:12:1)

// Production Error Handling Pattern
function setupErrorHandling() {
  const root = createRoot(document.getElementById('root'), {
    onCaughtError(error, { componentStack }) {
      // Non-critical: a boundary caught it, UI is still functional
      sendToErrorService({
        severity: 'warning',
        message: error.message,
        stack: error.stack,
        componentStack,
        timestamp: Date.now(),
        url: window.location.href,
      });
    },

    onUncaughtError(error, { componentStack }) {
      // Critical: show a full-page error screen
      sendToErrorService({
        severity: 'critical',
        message: error.message,
        stack: error.stack,
        componentStack,
        timestamp: Date.now(),
        url: window.location.href,
      });

      // Optionally show a crash screen
      document.getElementById('root').innerHTML = `
        <div class="crash-screen">
          <h1>Something went wrong</h1>
          <button onclick="location.reload()">Reload</button>
        </div>
      `;
    },
  });

  return root;
}
```

**Key takeaway:** React 19 gives you three distinct error reporting callbacks at the root level, enabling proper error classification (caught vs uncaught vs recoverable) for production monitoring. Errors are no longer double-logged, and component stacks are included by default, making debugging significantly easier.

---

### Q16. How do you use `use()` in conditionals and loops, and how does it differ from hooks?

**Answer:**

The `use()` API fundamentally breaks from the "Rules of Hooks" that have governed React since hooks were introduced in React 16.8. While all hooks (`useState`, `useEffect`, `useContext`, etc.) **must** be called at the top level of a component in the same order every render, `use()` can be called **anywhere** — inside `if` statements, inside `for`/`while` loops, inside `try`/`catch` blocks, and after early returns.

This is because `use()` is not a hook — it's a new type of primitive. Internally, hooks rely on a **call order linked list** to match state slots across renders. `use()` doesn't use this mechanism — it reads from a resource (Promise or Context) and either returns the value or suspends the component.

**Practical implications:**

1. **Conditional context reading** — Only read context when you need it, avoiding unnecessary subscriptions.
2. **Conditional data loading** — Only suspend on a Promise when certain conditions are met.
3. **Looping over Promises** — Read multiple Promises in a loop (all must be created outside the loop).

```jsx
// React 18: Cannot use hooks conditionally — forced to read all context always
import { useContext } from 'react';

const AdminContext = React.createContext(null);
const ThemeContext = React.createContext('light');
const FeatureFlagsContext = React.createContext({});

function UserDashboard({ user, isAdmin }) {
  // ❌ ILLEGAL: Cannot call useContext conditionally
  // if (isAdmin) {
  //   const adminTools = useContext(AdminContext);
  // }

  // ✅ Must always call all hooks, even if values aren't needed
  const adminTools = useContext(AdminContext); // Wasted if not admin
  const theme = useContext(ThemeContext);
  const flags = useContext(FeatureFlagsContext); // Wasted if not checking flags

  if (!user) {
    return <LoginPrompt />;
  }

  return (
    <div className={theme}>
      <h1>Welcome, {user.name}</h1>
      {isAdmin && <AdminPanel tools={adminTools} />}
      {flags.showBetaFeature && <BetaWidget />}
    </div>
  );
}
```

```jsx
// React 19: use() in conditionals — read only what you need
import { use } from 'react';

const AdminContext = React.createContext(null);
const ThemeContext = React.createContext('light');
const FeatureFlagsContext = React.createContext({});

function UserDashboard({ user, isAdmin }) {
  // Early return BEFORE any resource reading — perfectly legal
  if (!user) {
    return <LoginPrompt />;
  }

  // Read theme — always needed after the early return
  const theme = use(ThemeContext);

  // ✅ Conditional context reading — only subscribe when needed
  let adminTools = null;
  if (isAdmin) {
    adminTools = use(AdminContext); // Only read if admin
  }

  // ✅ Another conditional read
  const flags = use(FeatureFlagsContext);

  return (
    <div className={theme}>
      <h1>Welcome, {user.name}</h1>
      {isAdmin && <AdminPanel tools={adminTools} />}
      {flags.showBetaFeature && <BetaWidget />}
    </div>
  );
}
```

```jsx
// React 19: use() in loops — reading multiple Promises
import { use, Suspense } from 'react';

// Parent creates promises OUTSIDE the child component
function Dashboard({ widgetConfigs }) {
  // Create all promises up front
  const widgetPromises = widgetConfigs.map((config) =>
    fetchWidgetData(config.id)
  );

  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <WidgetGrid promises={widgetPromises} configs={widgetConfigs} />
    </Suspense>
  );
}

function WidgetGrid({ promises, configs }) {
  // ✅ use() inside a loop — reads each promise, suspends until ALL resolve
  const widgetDataList = promises.map((promise) => use(promise));

  return (
    <div className="grid">
      {widgetDataList.map((data, index) => (
        <Widget key={configs[index].id} data={data} config={configs[index]} />
      ))}
    </div>
  );
}
```

```jsx
// React 19: use() in try/catch (with Error Boundaries as the primary pattern)
import { use } from 'react';

function DataDisplay({ dataPromise, fallbackPromise }) {
  let data;

  // ✅ use() after conditional logic
  try {
    data = use(dataPromise);
  } catch (error) {
    // Note: In practice, Error Boundaries handle Promise rejections.
    // This try/catch works for synchronous errors around use().
    // For async rejections, wrap in an ErrorBoundary.
    console.error('Error reading data:', error);
    data = use(fallbackPromise); // Fallback to secondary data source
  }

  return <div>{JSON.stringify(data)}</div>;
}
```

**Key takeaway:** `use()` can be called inside conditionals, loops, try/catch, and after early returns — something impossible with hooks. This enables more efficient context subscriptions (only subscribe when needed) and flexible data loading patterns. The key constraint is that Promises passed to `use()` must be created outside the component that reads them.

---

### Q17. What are the breaking changes when migrating from React 18 to React 19, and what codemods are available?

**Answer:**

Migrating from React 18 to React 19 involves several breaking changes, though most are removing **already-deprecated APIs**. The React team provides automated codemods that handle the majority of changes. Here's a comprehensive breakdown:

**Breaking Changes:**

| Change | What was removed/changed | Migration |
|---|---|---|
| `ReactDOM.render` | Removed (deprecated in 18) | Use `createRoot` |
| `ReactDOM.hydrate` | Removed (deprecated in 18) | Use `hydrateRoot` |
| `ReactDOM.unmountComponentAtNode` | Removed | Use `root.unmount()` |
| `ReactDOM.findDOMNode` | Removed | Use refs |
| String refs | Removed (`ref="myRef"`) | Use `useRef` / callback refs |
| Legacy Context (`contextTypes`) | Removed | Use `createContext` |
| `defaultProps` for function components | Deprecated | Use JS default parameters |
| Ref callback return value | Now treated as cleanup | Use explicit `{}` blocks |
| `ReactDOM.renderToStaticNodeStream` | Removed from `react-dom/server` | Use modern SSR APIs |
| `propTypes` | Removed from React package | Use TypeScript |
| Implicit children in JSX | Must be explicit | Add `children` prop type |
| Context `.Provider` | Deprecated (still works) | Use `<Context value={}>` |
| `forwardRef` | Deprecated (still works) | Use ref as prop |
| UMD builds | Removed | Use ESM |

```jsx
// Migration Example 1: ReactDOM.render → createRoot
// ─── React 18 (already deprecated) ───
import ReactDOM from 'react-dom';
ReactDOM.render(<App />, document.getElementById('root'));

// ─── React 19 ───
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

```jsx
// Migration Example 2: defaultProps → default parameters
// ─── React 18 ───
function Button({ size, variant, disabled }) {
  return <button className={`btn-${size} btn-${variant}`} disabled={disabled} />;
}
Button.defaultProps = {
  size: 'medium',
  variant: 'primary',
  disabled: false,
};

// ─── React 19 ───
function Button({ size = 'medium', variant = 'primary', disabled = false }) {
  return <button className={`btn-${size} btn-${variant}`} disabled={disabled} />;
}
```

```jsx
// Migration Example 3: forwardRef → ref as prop
// ─── React 18 ───
const Input = React.forwardRef(({ label, ...props }, ref) => (
  <label>
    {label}
    <input ref={ref} {...props} />
  </label>
));
Input.displayName = 'Input';

// ─── React 19 ───
function Input({ label, ref, ...props }) {
  return (
    <label>
      {label}
      <input ref={ref} {...props} />
    </label>
  );
}
```

```jsx
// Migration Example 4: Ref callback implicit return → explicit block
// ─── React 18 (worked fine) ───
<div ref={(node) => (myRef.current = node)} />

// ─── React 19 (implicit return is treated as cleanup!) ───
// ❌ This breaks — the assignment's return value is interpreted as a cleanup
<div ref={(node) => (myRef.current = node)} />

// ✅ Fix: use explicit block
<div ref={(node) => { myRef.current = node; }} />
```

**Available Codemods:**

```bash
# Run all React 19 codemods at once
npx codemod@latest react/19

# Or run individual codemods:
npx codemod@latest react/19/replace-reactdom-render
npx codemod@latest react/19/replace-string-ref
npx codemod@latest react/19/replace-act-import
npx codemod@latest react/19/replace-use-form-state

# For TypeScript-specific changes:
npx types-react-codemod@latest preset-19 ./src

# Common TypeScript changes:
# - useRef requires an argument: useRef<T>(null) instead of useRef<T>()
# - Ref cleanup: RefCallback type now expects void | (() => void) return
# - Removed implicit children from FC type
```

**Step-by-step migration checklist:**

```jsx
// Step 1: Update dependencies
// package.json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@types/react": "^19.0.0",      // If using TypeScript
    "@types/react-dom": "^19.0.0"   // If using TypeScript
  }
}

// Step 2: Run codemods
// npx codemod@latest react/19 ./src
// npx types-react-codemod@latest preset-19 ./src

// Step 3: Fix remaining issues manually
// - Search for forwardRef and convert to ref-as-prop
// - Search for .Provider and convert to context shorthand
// - Search for defaultProps on function components
// - Search for ref callbacks with implicit returns
// - Test hydration (stricter in React 19)
```

**Key takeaway:** React 19 migration is mostly about removing deprecated APIs that already had replacements in React 18. The codemods handle the bulk of changes automatically. The trickiest breaking change is ref callback return values being treated as cleanup functions, which can cause subtle bugs if not addressed.

---

### Q18. What are the React 19 TypeScript improvements?

**Answer:**

React 19 brings significant TypeScript improvements, both in the React type definitions (`@types/react@19`) and in how new APIs are typed. The changes make React code more type-safe and reduce the amount of manual type annotations needed.

**Major TypeScript changes:**

1. **`useRef` requires an initial argument** — `useRef<T>()` without an argument is no longer valid; use `useRef<T>(null)` or `useRef<T>(undefined)`.
2. **Ref cleanup types** — `RefCallback<T>` now expects a return type of `void | (() => void)` to support cleanup functions.
3. **No implicit `children`** — `React.FC` no longer includes `children` in props by default.
4. **`ref` in props** — Function component props can include `ref` directly; no need for `React.forwardRef`.
5. **`useActionState` typing** — Properly typed state + action pattern.
6. **Removed deprecated types** — `React.SFC`, `React.StatelessComponent`, etc.

```tsx
// React 18 TypeScript: Common patterns and their issues

import React, { useRef, forwardRef, useContext, FC } from 'react';

// 1. useRef — no argument was allowed
const inputRef = useRef<HTMLInputElement>(); // ✅ in React 18

// 2. forwardRef — verbose generic signature
interface InputProps {
  label: string;
  placeholder?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, placeholder }, ref) => (
    <label>
      {label}
      <input ref={ref} placeholder={placeholder} />
    </label>
  )
);

// 3. FC included children implicitly
const Card: FC<{ title: string }> = ({ title, children }) => (
  // children was always available even if not declared in props
  <div>
    <h2>{title}</h2>
    {children}
  </div>
);

// 4. Context typing
const ThemeContext = React.createContext<'light' | 'dark'>('light');

function ThemedButton() {
  const theme = useContext(ThemeContext); // type: 'light' | 'dark'
  return <button className={theme}>Click</button>;
}

// 5. Ref callback — any return was fine
function Component() {
  return (
    <div ref={(node): any => {
      // Could return anything — no type safety on cleanup
      return node;
    }} />
  );
}
```

```tsx
// React 19 TypeScript: Cleaner, stricter, better

import { useRef, use, useActionState, useOptimistic } from 'react';

// 1. useRef — MUST provide initial argument
const inputRef = useRef<HTMLInputElement>(null);   // ✅ Required
// const badRef = useRef<HTMLInputElement>();       // ❌ Error in React 19

// 2. ref as prop — no forwardRef wrapper
interface InputProps {
  label: string;
  placeholder?: string;
  ref?: React.Ref<HTMLInputElement>; // ref is just a prop now
}

function Input({ label, placeholder, ref }: InputProps) {
  return (
    <label>
      {label}
      <input ref={ref} placeholder={placeholder} />
    </label>
  );
}

// 3. FC no longer includes children — must be explicit
interface CardProps {
  title: string;
  children: React.ReactNode; // Must explicitly declare
}

function Card({ title, children }: CardProps) {
  return (
    <div>
      <h2>{title}</h2>
      {children}
    </div>
  );
}

// 4. use() with Context — properly typed
const ThemeContext = React.createContext<'light' | 'dark'>('light');

function ThemedButton() {
  const theme = use(ThemeContext); // type: 'light' | 'dark' — same typing
  return <button className={theme}>Click</button>;
}

// 5. Ref callback cleanup — properly typed return
function Component() {
  return (
    <div ref={(node): (() => void) => {
      // Setup
      const observer = new ResizeObserver(() => {});
      observer.observe(node!);
      // Cleanup must return void function or nothing
      return () => observer.disconnect();
    }} />
  );
}

// 6. useActionState — fully typed
interface FormState {
  error: string | null;
  data: { id: string; name: string } | null;
}

async function saveUser(
  prevState: FormState,
  formData: FormData
): Promise<FormState> {
  try {
    const name = formData.get('name') as string;
    const result = await api.createUser({ name });
    return { error: null, data: result };
  } catch (e) {
    return { error: (e as Error).message, data: null };
  }
}

function UserForm() {
  // TypeScript infers: [FormState, (payload: FormData) => void, boolean]
  const [state, formAction, isPending] = useActionState(saveUser, {
    error: null,
    data: null,
  });

  return (
    <form action={formAction}>
      <input name="name" />
      <button disabled={isPending}>Save</button>
      {state.error && <p>{state.error}</p>}
      {state.data && <p>Created: {state.data.name}</p>}
    </form>
  );
}

// 7. useOptimistic — typed optimistic updates
interface Todo {
  id: string;
  title: string;
  pending?: boolean;
}

function TodoList({ todos }: { todos: Todo[] }) {
  // TypeScript infers the optimistic state type from the base state
  const [optimisticTodos, addOptimistic] = useOptimistic<Todo[], string>(
    todos,
    (current, newTitle) => [
      ...current,
      { id: `temp-${Date.now()}`, title: newTitle, pending: true },
    ]
  );

  return (
    <ul>
      {optimisticTodos.map((todo) => (
        <li key={todo.id} style={{ opacity: todo.pending ? 0.5 : 1 }}>
          {todo.title}
        </li>
      ))}
    </ul>
  );
}
```

**Running the TypeScript codemod:**

```bash
# Automatically fix most TypeScript breaking changes
npx types-react-codemod@latest preset-19 ./src

# This handles:
# - Adding null to useRef calls that need it
# - Removing implicit children from FC usage
# - Updating ref callback return types
# - Replacing deprecated type aliases
```

**Key takeaway:** React 19's TypeScript changes enforce stricter and more correct types — `useRef` must have an initial value, `FC` doesn't include `children`, ref callbacks must return `void` or a cleanup function, and `ref` is a normal prop. The `types-react-codemod` automates most of the migration.

---

### Q19. What performance improvements does React 19 bring over React 18?

**Answer:**

While React 18's performance story centered on concurrent rendering (interrupting long renders), React 19 adds several **additional performance improvements** that reduce bundle size, improve hydration speed, and optimize how React handles updates internally.

**Key performance improvements:**

1. **No more double-rendering in Strict Mode for effects** — React 18's Strict Mode ran effects twice in development (mount → unmount → mount). React 19 continues this for state but improves the developer experience by logging cleanup more clearly. In production, there's no double-rendering.

2. **Improved SSR streaming with Suspense** — React 19 has better streaming heuristics. It can flush content earlier and more efficiently, reducing time-to-first-byte (TTFB) and time-to-interactive (TTI).

3. **Automatic batching improvements** — React 18 introduced automatic batching (grouping multiple `setState` calls into one render). React 19 extends this to Actions — multiple state updates within an Action are batched, including across `await` boundaries within the same transition.

4. **Reduced re-renders with `use()`** — By replacing `useEffect` + `useState` patterns with `use()` + Suspense, components have fewer renders (no render-then-fetch-then-re-render cycle).

5. **Stylesheet deduplication and ordering** — React 19 manages stylesheets at the component level, ensuring they're loaded before content paints and not duplicated.

6. **Smaller client bundle for Server Components** — Code that runs only on the server (Server Components, Server Actions) is completely excluded from the client bundle.

```jsx
// React 18: The "render waterfall" problem with useEffect
import { useState, useEffect } from 'react';

function UserDashboard({ userId }) {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState(null);

  // Render 1: Initial render — shows loading
  // Render 2: user loaded — shows user, starts loading posts
  // Render 3: posts loaded — shows everything
  // TOTAL: 3 renders, sequential fetches (waterfall)

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  useEffect(() => {
    if (user) {
      // Can't fetch until user is loaded — WATERFALL!
      fetchPosts(user.id).then(setPosts);
    }
  }, [user]);

  if (!user) return <Spinner />;
  if (!posts) return <UserHeader user={user} />;

  return (
    <div>
      <UserHeader user={user} />
      <PostList posts={posts} />
    </div>
  );
}
```

```jsx
// React 19: Parallel fetching with use() — no waterfall
import { use, Suspense } from 'react';

function UserDashboard({ userId }) {
  // Both promises start in PARALLEL — no waterfall
  const userPromise = fetchUser(userId);
  const postsPromise = fetchPosts(userId);

  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <UserContent userPromise={userPromise} postsPromise={postsPromise} />
    </Suspense>
  );
}

function UserContent({ userPromise, postsPromise }) {
  // Render 1: Both resolve → single render with all data
  const user = use(userPromise);
  const posts = use(postsPromise);

  // TOTAL: 1 render after both promises resolve
  return (
    <div>
      <UserHeader user={user} />
      <PostList posts={posts} />
    </div>
  );
}
```

```jsx
// React 19: Action batching — multiple updates in one render
import { useActionState, useOptimistic } from 'react';

async function processOrder(prevState, formData) {
  // All of these state changes are batched into ONE render
  // even though they happen across await boundaries
  const items = JSON.parse(formData.get('items'));

  // Validate
  const validation = await validateItems(items);
  if (validation.errors.length > 0) {
    return { ...prevState, errors: validation.errors };
  }

  // Calculate pricing
  const pricing = await calculatePricing(items);

  // Process payment
  const payment = await processPayment(pricing.total);

  // Confirm order
  const order = await createOrder({ items, pricing, payment });

  // React batches all state updates from this Action into ONE re-render
  return {
    errors: [],
    order,
    pricing,
    status: 'confirmed',
  };
}
```

```jsx
// React 19: Stylesheet optimization — no duplicate styles, correct ordering
function ProductCard({ product }) {
  return (
    <>
      {/* React deduplicates this across all ProductCard instances */}
      <link rel="stylesheet" href="/styles/product-card.css" precedence="default" />

      <div className="product-card">
        <h3>{product.name}</h3>
        <p>${product.price}</p>
      </div>
    </>
  );
}

function ProductGrid({ products }) {
  return (
    <>
      {/* Higher precedence — loaded after product-card.css */}
      <link rel="stylesheet" href="/styles/product-grid.css" precedence="high" />

      <div className="product-grid">
        {/* Even though each ProductCard renders the same <link>,
            React only includes it ONCE in the document */}
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </>
  );
}
```

**Performance comparison summary:**

| Aspect | React 18 | React 19 |
|---|---|---|
| Data fetching renders | 3+ (mount → fetch → re-render) | 1 (suspend → render with data) |
| Sequential fetch fix | Manual `Promise.all` | Natural with `use()` |
| Action batching | Within `startTransition` | Across `await` in Actions |
| Style loading | Manual, potential FOUC | Automatic, no FOUC |
| Server-only code | Included in bundle | Excluded from client |

**Key takeaway:** React 19's performance improvements come from eliminating render waterfalls (via `use()` + Suspense), better Action batching, intelligent stylesheet management, and Server Component code exclusion from client bundles. These improvements are architectural — they change how you structure data loading, resulting in fewer renders and faster time-to-interactive.

---

### Q20. How do you perform a complete React 18 to React 19 migration? Walk through converting a real application feature-by-feature.

**Answer:**

Let's walk through migrating a complete feature — a **Product Review System** — from React 18 patterns to React 19. This covers data fetching, forms, optimistic updates, context, refs, metadata, and error handling.

**Phase 1: Setup — Update dependencies and run codemods**

```bash
# Step 1: Update packages
npm install react@19 react-dom@19
npm install -D @types/react@19 @types/react-dom@19

# Step 2: Run automated codemods
npx codemod@latest react/19 ./src
npx types-react-codemod@latest preset-19 ./src

# Step 3: Fix any remaining build errors
npm run build
```

**Phase 2: Migrate the Context Setup**

```jsx
// ─── REACT 18: Context with .Provider wrapper ───
// src/contexts/ReviewContext.jsx (BEFORE)

import { createContext, useContext, useState, useCallback } from 'react';

const ReviewContext = createContext(null);

export function ReviewProvider({ productId, children }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const addReview = useCallback(async (review) => {
    const res = await fetch(`/api/products/${productId}/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(review),
    });
    const newReview = await res.json();
    setReviews((prev) => [newReview, ...prev]);
  }, [productId]);

  return (
    <ReviewContext.Provider value={{ reviews, loading, addReview }}>
      {children}
    </ReviewContext.Provider>
  );
}

export function useReviews() {
  const ctx = useContext(ReviewContext);
  if (!ctx) throw new Error('useReviews must be inside ReviewProvider');
  return ctx;
}
```

```jsx
// ─── REACT 19: Context shorthand + use() ───
// src/contexts/ReviewContext.jsx (AFTER)

import { createContext } from 'react';

// Context with shorthand rendering — no .Provider needed
export const ReviewContext = createContext(null);

export function ReviewProvider({ productId, children }) {
  // We'll move state management to useActionState in the form component
  // The provider just supplies the productId and review data

  return (
    // ✅ Direct Context rendering — no .Provider
    <ReviewContext value={{ productId }}>
      {children}
    </ReviewContext>
  );
}
```

**Phase 3: Migrate Data Fetching (useEffect → use())**

```jsx
// ─── REACT 18: useEffect for data fetching ───
// src/components/ReviewList.jsx (BEFORE)

import { useState, useEffect } from 'react';
import { useReviews } from '../contexts/ReviewContext';

function ReviewList({ productId }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch(`/api/products/${productId}/reviews`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load reviews');
        return res.json();
      })
      .then((data) => {
        if (!cancelled) {
          setReviews(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [productId]);

  if (loading) return <ReviewsSkeleton />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="reviews">
      <h2>Reviews ({reviews.length})</h2>
      {reviews.map((review) => (
        <ReviewCard key={review.id} review={review} />
      ))}
    </div>
  );
}
```

```jsx
// ─── REACT 19: use() + Suspense ───
// src/components/ReviewList.jsx (AFTER)

import { use } from 'react';

function ReviewList({ reviewsPromise }) {
  // Suspends until data is ready — no loading/error state needed
  const reviews = use(reviewsPromise);

  return (
    <div className="reviews">
      <h2>Reviews ({reviews.length})</h2>
      {reviews.map((review) => (
        <ReviewCard key={review.id} review={review} />
      ))}
    </div>
  );
}

// Parent creates the promise and wraps with Suspense + ErrorBoundary
// src/pages/ProductPage.jsx

import { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

function ProductPage({ productId }) {
  // Promise created in parent — starts fetching immediately
  const reviewsPromise = fetchReviews(productId);

  return (
    <ErrorBoundary fallback={<ErrorMessage />}>
      <Suspense fallback={<ReviewsSkeleton />}>
        <ReviewList reviewsPromise={reviewsPromise} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

**Phase 4: Migrate the Review Form (manual state → useActionState + useOptimistic)**

```jsx
// ─── REACT 18: Manual form handling ───
// src/components/ReviewForm.jsx (BEFORE)

import { useState, useTransition, forwardRef, useRef } from 'react';

const StarRating = forwardRef(({ value, onChange }, ref) => (
  <div ref={ref} className="star-rating">
    {[1, 2, 3, 4, 5].map((star) => (
      <button key={star} type="button" onClick={() => onChange(star)}>
        {star <= value ? '★' : '☆'}
      </button>
    ))}
  </div>
));
StarRating.displayName = 'StarRating';

function ReviewForm({ productId, onReviewAdded }) {
  const [rating, setRating] = useState(0);
  const [text, setText] = useState('');
  const [error, setError] = useState(null);
  const [isPending, startTransition] = useTransition();
  const formRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    startTransition(async () => {
      try {
        const res = await fetch(`/api/products/${productId}/reviews`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rating, text }),
        });

        if (!res.ok) {
          const data = await res.json();
          setError(data.error);
          return;
        }

        const newReview = await res.json();
        onReviewAdded(newReview);
        setRating(0);
        setText('');
      } catch (err) {
        setError('Failed to submit review');
      }
    });
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit}>
      <h3>Write a Review</h3>
      <StarRating value={rating} onChange={setRating} />
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Share your experience..."
        disabled={isPending}
      />
      <button disabled={isPending || rating === 0}>
        {isPending ? 'Submitting...' : 'Submit Review'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

```jsx
// ─── REACT 19: useActionState + useOptimistic + useFormStatus ───
// src/components/ReviewForm.jsx (AFTER)

import { useActionState, useOptimistic, use } from 'react';
import { useFormStatus } from 'react-dom';
import { ReviewContext } from '../contexts/ReviewContext';

// ref is a regular prop now — no forwardRef
function StarRating({ value, name, ref }) {
  return (
    <div ref={ref} className="star-rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <label key={star}>
          <input type="radio" name={name} value={star} defaultChecked={star === value} />
          {star <= value ? '★' : '☆'}
        </label>
      ))}
    </div>
  );
}

// Reads parent form status — no props needed
function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Submitting...' : 'Submit Review'}
    </button>
  );
}

// Action function — receives prevState and formData
async function submitReviewAction(prevState, formData) {
  const productId = formData.get('productId');
  const rating = Number(formData.get('rating'));
  const text = formData.get('text');

  if (rating === 0) {
    return { ...prevState, error: 'Please select a rating' };
  }

  try {
    const res = await fetch(`/api/products/${productId}/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating, text }),
    });

    if (!res.ok) {
      const data = await res.json();
      return { ...prevState, error: data.error };
    }

    const newReview = await res.json();
    return {
      reviews: [newReview, ...prevState.reviews],
      error: null,
    };
  } catch (err) {
    return { ...prevState, error: 'Failed to submit review' };
  }
}

function ReviewForm({ reviews }) {
  // Read context conditionally with use()
  const { productId } = use(ReviewContext);

  const [state, formAction, isPending] = useActionState(submitReviewAction, {
    reviews,
    error: null,
  });

  // Optimistic update — show review immediately
  const [optimisticReviews, addOptimistic] = useOptimistic(
    state.reviews,
    (current, newReview) => [
      { ...newReview, id: `temp-${Date.now()}`, pending: true },
      ...current,
    ]
  );

  return (
    <>
      {/* Native metadata — hoisted to <head> */}
      <title>Reviews | Product #{productId}</title>
      <meta name="description" content={`${state.reviews.length} reviews`} />

      <form action={async (formData) => {
        // Show optimistic review immediately
        addOptimistic({
          rating: Number(formData.get('rating')),
          text: formData.get('text'),
          author: 'You',
        });
        await formAction(formData);
      }}>
        <input type="hidden" name="productId" value={productId} />
        <h3>Write a Review</h3>
        <StarRating name="rating" value={0} />
        <textarea name="text" placeholder="Share your experience..." required />
        <SubmitButton />
        {state.error && <p className="error">{state.error}</p>}
      </form>

      {/* Render optimistic reviews */}
      <div className="reviews">
        {optimisticReviews.map((review) => (
          <ReviewCard
            key={review.id}
            review={review}
            style={{ opacity: review.pending ? 0.6 : 1 }}
          />
        ))}
      </div>
    </>
  );
}
```

**Phase 5: Migrate Error Handling**

```jsx
// ─── REACT 18: Basic error boundary + onRecoverableError ───
// src/index.jsx (BEFORE)

import { createRoot } from 'react-dom/client';

const root = createRoot(document.getElementById('root'), {
  onRecoverableError: (error) => {
    console.error('Recoverable:', error);
  },
});

root.render(<App />);
```

```jsx
// ─── REACT 19: Comprehensive error callbacks ───
// src/index.jsx (AFTER)

import { createRoot } from 'react-dom/client';

const root = createRoot(document.getElementById('root'), {
  onCaughtError: (error, errorInfo) => {
    // Error Boundary caught it — app is still functional
    errorReporter.send({
      level: 'warning',
      error,
      componentStack: errorInfo.componentStack,
    });
  },

  onUncaughtError: (error, errorInfo) => {
    // Nothing caught it — app is crashing
    errorReporter.send({
      level: 'critical',
      error,
      componentStack: errorInfo.componentStack,
    });
  },

  onRecoverableError: (error, errorInfo) => {
    // Hydration mismatch or similar — React recovered
    errorReporter.send({
      level: 'info',
      error,
      componentStack: errorInfo.componentStack,
    });
  },
});

root.render(<App />);
```

**Phase 6: Migrate Ref Patterns**

```jsx
// ─── REACT 18: Ref callback without cleanup ───
// src/components/TextEditor.jsx (BEFORE)

import { useRef, useEffect, forwardRef } from 'react';

const TextEditor = forwardRef(({ onReady }, ref) => {
  const editorRef = useRef(null);

  useEffect(() => {
    const editor = initEditor(editorRef.current);
    if (ref) {
      if (typeof ref === 'function') ref(editor);
      else ref.current = editor;
    }
    onReady?.(editor);

    return () => editor.destroy();
  }, []);

  return <div ref={editorRef} className="editor" />;
});
```

```jsx
// ─── REACT 19: Ref cleanup + ref as prop ───
// src/components/TextEditor.jsx (AFTER)

function TextEditor({ onReady, ref }) {
  return (
    <div
      className="editor"
      ref={(node) => {
        // Setup: initialize editor
        const editor = initEditor(node);
        onReady?.(editor);

        // Expose editor instance via parent ref
        if (ref) {
          if (typeof ref === 'function') ref(editor);
          else ref.current = editor;
        }

        // Cleanup: destroy editor when unmounted
        return () => {
          editor.destroy();
          if (ref && typeof ref !== 'function') {
            ref.current = null;
          }
        };
      }}
    />
  );
}
```

**Complete Migration Checklist:**

```markdown
## React 18 → 19 Migration Checklist

### Automated (run codemods)
- [ ] `npx codemod@latest react/19 ./src`
- [ ] `npx types-react-codemod@latest preset-19 ./src` (TypeScript)
- [ ] Fix any build errors from codemods

### Manual — High Priority
- [ ] Replace `useEffect` data fetching with `use()` + Suspense
- [ ] Replace form `onSubmit` handlers with `useActionState`
- [ ] Add `useFormStatus` to child form components (remove prop drilling)
- [ ] Add `useOptimistic` where appropriate
- [ ] Convert `forwardRef` to ref-as-prop pattern
- [ ] Fix ref callbacks that have implicit returns (add `{}`)

### Manual — Medium Priority
- [ ] Replace `<Context.Provider>` with `<Context>`
- [ ] Replace `react-helmet` with native `<title>`, `<meta>`, `<link>`
- [ ] Add resource preloading (`preload`, `preinit`)
- [ ] Add ref cleanup functions where `useEffect` was used for ref cleanup
- [ ] Update error handling with `onCaughtError` / `onUncaughtError`

### Manual — Low Priority
- [ ] Replace `defaultProps` with JS default parameters
- [ ] Remove `displayName` from converted `forwardRef` components
- [ ] Replace `useContext` with `use()` where conditional reading helps
- [ ] Audit for removed APIs (string refs, legacy context, etc.)

### Testing
- [ ] Run full test suite — fix broken tests
- [ ] Test SSR/hydration — React 19 is stricter about mismatches
- [ ] Test forms with JS disabled (progressive enhancement)
- [ ] Test error boundaries with new error callbacks
- [ ] Performance audit — verify no render waterfalls remain
```

**Key takeaway:** A complete React 18 → 19 migration follows a phased approach: (1) update deps and run codemods, (2) migrate context to shorthand, (3) replace `useEffect` data fetching with `use()`, (4) convert forms to `useActionState` + `useFormStatus` + `useOptimistic`, (5) upgrade error handling, and (6) modernize ref patterns. The codemods handle the mechanical changes; the real value comes from adopting the new patterns that eliminate boilerplate and improve performance.

---

*End of React 19 New Features Interview Questions*
