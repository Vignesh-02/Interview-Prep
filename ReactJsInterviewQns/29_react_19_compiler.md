# React 19 Compiler & Auto-Memoization — Interview Questions

## Topic Introduction

The **React Compiler** (formerly known as "React Forget") is a build-time tool introduced alongside React 19 that automatically optimizes React applications by inserting memoization at compile time. In React 18 and earlier, developers were responsible for manually optimizing re-renders using `React.memo()`, `useMemo()`, and `useCallback()`. This manual approach was error-prone — developers either over-memoized (adding unnecessary complexity) or under-memoized (missing optimization opportunities), and stale closures caused subtle bugs. The React Compiler eliminates this entire category of work by analyzing your component code during the build step and automatically inserting fine-grained memoization where it determines it is safe and beneficial. It understands the **Rules of React** — components must be pure, props are immutable, hooks follow their rules — and uses this contract to determine what can be safely cached between renders.

The Compiler works as a **Babel plugin** that transforms your React components at build time. It analyzes the data flow within each component, tracks which values depend on which props/state, and wraps computations and JSX output in memoization guards so that unchanged portions of the render tree are skipped automatically. Unlike runtime approaches (like Angular Signals or Svelte's compile-time reactivity), the React Compiler preserves the standard React programming model — you write plain JavaScript functions and JSX, and the compiler handles the optimization. This means existing React codebases can adopt the compiler **gradually**, even on a per-file or per-directory basis, without rewriting any application logic. The compiler also ships with an **ESLint plugin** that detects code patterns that violate the Rules of React and would prevent the compiler from optimizing correctly.

Why is this revolutionary? Because it removes the single largest source of "accidental complexity" in React development. Teams spent enormous effort debating where to place `useMemo`, reviewing pull requests for missing memoization, and debugging stale closure bugs caused by incorrect dependency arrays. The React Compiler makes all of that obsolete for the vast majority of cases. Here is a before/after illustration of what the compiler does:

```jsx
// ─── BEFORE: What you write (standard React code) ───
function ProductCard({ product, onAddToCart }) {
  const discountedPrice = product.price * (1 - product.discount);

  const handleClick = () => {
    onAddToCart(product.id, discountedPrice);
  };

  return (
    <div className="card">
      <h2>{product.name}</h2>
      <p>${discountedPrice.toFixed(2)}</p>
      <button onClick={handleClick}>Add to Cart</button>
    </div>
  );
}

// ─── AFTER: What the React Compiler outputs (simplified) ───
function ProductCard({ product, onAddToCart }) {
  const $ = _c(4); // compiler-managed cache with 4 slots

  let discountedPrice;
  if ($[0] !== product.price || $[1] !== product.discount) {
    discountedPrice = product.price * (1 - product.discount);
    $[0] = product.price;
    $[1] = product.discount;
    $[2] = discountedPrice;
  } else {
    discountedPrice = $[2];
  }

  let handleClick;
  if ($[3] !== product.id || $[2] !== discountedPrice || $[4] !== onAddToCart) {
    handleClick = () => {
      onAddToCart(product.id, discountedPrice);
    };
    $[3] = product.id;
    $[4] = onAddToCart;
    $[5] = handleClick;
  } else {
    handleClick = $[5];
  }

  // JSX is also memoized — skipped if inputs haven't changed
  let t0;
  if ($[6] !== product.name || $[7] !== discountedPrice || $[8] !== handleClick) {
    t0 = (
      <div className="card">
        <h2>{product.name}</h2>
        <p>${discountedPrice.toFixed(2)}</p>
        <button onClick={handleClick}>Add to Cart</button>
      </div>
    );
    $[6] = product.name;
    $[7] = discountedPrice;
    $[8] = handleClick;
    $[9] = t0;
  } else {
    t0 = $[9];
  }

  return t0;
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1: What is the React Compiler and what problem does it solve?

**Answer:**

The React Compiler is an **automatic optimization tool** that runs at build time (as a Babel plugin) and analyzes your React components to insert memoization automatically. It solves the problem of **unnecessary re-renders** — React's core re-rendering model is "re-render everything when state changes, then diff," which means child components and computed values are re-created even when their inputs haven't changed.

Before the compiler, developers had to manually prevent this waste using `React.memo()`, `useMemo()`, and `useCallback()`. This was tedious, easy to get wrong, and cluttered the codebase with optimization logic. The React Compiler automates all of it.

```jsx
// ─── React 18: The problem — unnecessary re-renders ───
function ParentComponent() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('Alice');

  // Every time count changes, this object is re-created
  // even though ExpensiveChild only cares about name
  const userData = { name, role: 'admin' };

  // This function is re-created every render
  const handleUpdate = () => {
    console.log('Updating user:', name);
  };

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      {/* ExpensiveChild re-renders EVERY time count changes! */}
      <ExpensiveChild data={userData} onUpdate={handleUpdate} />
    </div>
  );
}

// ─── React 18: The manual fix ───
const ExpensiveChild = React.memo(function ExpensiveChild({ data, onUpdate }) {
  // ... expensive rendering
  return <div>{data.name}</div>;
});

function ParentComponent() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('Alice');

  // Manually memoize the object
  const userData = useMemo(() => ({ name, role: 'admin' }), [name]);

  // Manually memoize the callback
  const handleUpdate = useCallback(() => {
    console.log('Updating user:', name);
  }, [name]);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <ExpensiveChild data={userData} onUpdate={handleUpdate} />
    </div>
  );
}

// ─── React 19 with Compiler: Just write the code. Compiler handles it. ───
function ParentComponent() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('Alice');

  // The compiler automatically detects that this object only depends on `name`
  // and memoizes it. No manual useMemo needed.
  const userData = { name, role: 'admin' };

  // The compiler detects the closure over `name` and caches the function.
  // No manual useCallback needed.
  const handleUpdate = () => {
    console.log('Updating user:', name);
  };

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      {/* Compiler ensures ExpensiveChild doesn't re-render when only count changes */}
      <ExpensiveChild data={userData} onUpdate={handleUpdate} />
    </div>
  );
}

// No React.memo wrapper needed either — the compiler memoizes the JSX output
function ExpensiveChild({ data, onUpdate }) {
  return <div>{data.name}</div>;
}
```

**Key takeaway:** The React Compiler lets you write simple, idiomatic React code and get optimal performance automatically. You no longer have to choose between "clean code" and "fast code."

---

### Q2: How did manual memoization work in React 18, and what were its problems?

**Answer:**

React 18 provided three memoization primitives that developers had to apply manually:

1. **`React.memo(Component)`** — wraps a component to skip re-rendering if props are shallowly equal.
2. **`useMemo(() => value, [deps])`** — caches a computed value, only recomputing when dependencies change.
3. **`useCallback(fn, [deps])`** — caches a function reference, only creating a new one when dependencies change.

The problems were numerous: **forgotten memoization** (missing `memo` or `useMemo`), **incorrect dependency arrays** (stale closures), **over-memoization** (wrapping everything "just in case"), and **readability degradation** (business logic buried inside memoization wrappers).

```jsx
// ─── React 18: Manual memoization — a realistic component ───
import { useState, useMemo, useCallback, memo } from 'react';

// Problem 1: Must remember to wrap with memo
const UserList = memo(function UserList({ users, onSelect, filter }) {
  // Problem 2: Must manually memoize computed values
  const filteredUsers = useMemo(() => {
    return users.filter(u =>
      u.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [users, filter]); // Problem 3: Easy to forget a dependency

  // Problem 4: Must manually memoize callbacks
  const handleSelect = useCallback((userId) => {
    onSelect(userId);
  }, [onSelect]); // Did we get the deps right?

  // Problem 5: Must memoize objects passed as props
  const listStyle = useMemo(() => ({
    maxHeight: '400px',
    overflow: 'auto',
  }), []); // Static object — still needs useMemo to maintain identity

  return (
    <div style={listStyle}>
      {filteredUsers.map(user => (
        // Problem 6: Inline arrow breaks memoization of child
        // This undoes the child's React.memo!
        <UserItem
          key={user.id}
          user={user}
          onSelect={handleSelect}
        />
      ))}
    </div>
  );
});

// Must also be memoized
const UserItem = memo(function UserItem({ user, onSelect }) {
  return (
    <div onClick={() => onSelect(user.id)}>
      {user.name}
    </div>
  );
});

// ─── React 19 with Compiler: Same logic, zero memoization boilerplate ───
function UserList({ users, onSelect, filter }) {
  const filteredUsers = users.filter(u =>
    u.name.toLowerCase().includes(filter.toLowerCase())
  );

  const handleSelect = (userId) => {
    onSelect(userId);
  };

  const listStyle = {
    maxHeight: '400px',
    overflow: 'auto',
  };

  return (
    <div style={listStyle}>
      {filteredUsers.map(user => (
        <UserItem
          key={user.id}
          user={user}
          onSelect={handleSelect}
        />
      ))}
    </div>
  );
}

function UserItem({ user, onSelect }) {
  return (
    <div onClick={() => onSelect(user.id)}>
      {user.name}
    </div>
  );
}
// The compiler automatically memoizes filteredUsers, handleSelect, listStyle,
// and the JSX output of both components. No memo(), useMemo(), or useCallback().
```

---

### Q3: How does the React Compiler detect what to memoize automatically?

**Answer:**

The React Compiler performs **static analysis** of your component's source code at build time. It traces the data flow from props and state through every variable, function, and JSX expression in the component. For each value, it determines the **minimal set of reactive inputs** (props, state, context values) that the value depends on. It then wraps that value in a cache guard that checks whether those specific inputs have changed since the last render.

The compiler tracks three categories of values:
1. **Computed values** — variables derived from props/state (equivalent to `useMemo`)
2. **Function definitions** — callbacks and event handlers (equivalent to `useCallback`)
3. **JSX expressions** — the rendered output (equivalent to `React.memo`)

```jsx
// ─── What you write (React 19) ───
function Dashboard({ user, notifications }) {
  // Compiler sees: depends on user.name
  const greeting = `Hello, ${user.name}!`;

  // Compiler sees: depends on notifications (array)
  const unreadCount = notifications.filter(n => !n.read).length;

  // Compiler sees: depends on user.id (closure)
  const handleLogout = () => {
    logout(user.id);
  };

  // Compiler sees: JSX depends on greeting, unreadCount, handleLogout
  return (
    <header>
      <h1>{greeting}</h1>
      <span>Unread: {unreadCount}</span>
      <button onClick={handleLogout}>Logout</button>
    </header>
  );
}

// ─── What the compiler produces (conceptual) ───
function Dashboard({ user, notifications }) {
  const $ = _c(8);

  // greeting: only recompute if user.name changed
  let greeting;
  if ($[0] !== user.name) {
    greeting = `Hello, ${user.name}!`;
    $[0] = user.name;
    $[1] = greeting;
  } else {
    greeting = $[1];
  }

  // unreadCount: only recompute if notifications array changed
  let unreadCount;
  if ($[2] !== notifications) {
    unreadCount = notifications.filter(n => !n.read).length;
    $[2] = notifications;
    $[3] = unreadCount;
  } else {
    unreadCount = $[3];
  }

  // handleLogout: only recreate if user.id changed
  let handleLogout;
  if ($[4] !== user.id) {
    handleLogout = () => {
      logout(user.id);
    };
    $[4] = user.id;
    $[5] = handleLogout;
  } else {
    handleLogout = $[5];
  }

  // JSX: only recreate if any of greeting, unreadCount, handleLogout changed
  let t0;
  if ($[6] !== greeting || $[6] !== unreadCount || $[7] !== handleLogout) {
    t0 = (
      <header>
        <h1>{greeting}</h1>
        <span>Unread: {unreadCount}</span>
        <button onClick={handleLogout}>Logout</button>
      </header>
    );
    $[6] = greeting;
    $[7] = unreadCount;
    $[8] = handleLogout;
    $[9] = t0;
  } else {
    t0 = $[9];
  }

  return t0;
}
```

**Key insight:** The compiler is smarter than manually written `useMemo` because it tracks **individual property access** (e.g., `user.name` vs. the entire `user` object), producing more fine-grained cache keys than most developers would write by hand.

---

### Q4: Does the React Compiler make useMemo and useCallback obsolete?

**Answer:**

**For most use cases, yes.** The compiler automatically handles what `useMemo`, `useCallback`, and `React.memo` were designed for — preventing unnecessary recomputation and re-rendering. After adopting the compiler, you can (and should) remove the vast majority of manual memoization from your codebase.

However, there are **specific edge cases** where `useMemo` is still useful — particularly for **expensive computations that are not related to rendering**, or for ensuring **referential identity for values used outside the React render cycle** (e.g., as keys for external caches or subscriptions).

```jsx
// ─── Case 1: Compiler handles this — REMOVE useMemo/useCallback ───

// React 18 (manual)
function SearchResults({ query, items }) {
  const filtered = useMemo(
    () => items.filter(item => item.name.includes(query)),
    [items, query]
  );
  const handleClick = useCallback(
    (id) => navigate(`/item/${id}`),
    []
  );
  return filtered.map(item => (
    <Item key={item.id} item={item} onClick={handleClick} />
  ));
}

// React 19 (compiler) — just remove the wrappers
function SearchResults({ query, items }) {
  const filtered = items.filter(item => item.name.includes(query));
  const handleClick = (id) => navigate(`/item/${id}`);
  return filtered.map(item => (
    <Item key={item.id} item={item} onClick={handleClick} />
  ));
}

// ─── Case 2: useMemo STILL useful — expensive non-render computation ───

function DataAnalytics({ dataset }) {
  // This takes 500ms+ to compute. Even though the compiler would memoize it,
  // useMemo makes the INTENT explicit: "this is expensive, cache it."
  // The compiler respects existing useMemo and leaves it in place.
  const statistics = useMemo(() => {
    return computeHeavyStatistics(dataset); // O(n²) algorithm
  }, [dataset]);

  // The compiler handles everything else automatically
  const chartData = formatForChart(statistics);

  return <Chart data={chartData} />;
}

// ─── Case 3: useMemo STILL useful — external subscription identity ───

function LiveFeed({ channel }) {
  // The WebSocket subscription compares the options object by reference
  // to decide whether to reconnect. useMemo ensures stable identity.
  const subscriptionOptions = useMemo(() => ({
    channel,
    reconnect: true,
    bufferSize: 100,
  }), [channel]);

  // External library (not React-aware) uses this as a cache key
  useExternalSubscription(subscriptionOptions);

  return <FeedDisplay channel={channel} />;
}
```

**Rule of thumb:** After adopting the compiler, remove `useMemo`/`useCallback`/`memo` from your code. Only add them back if you have a specific, measurable reason (e.g., profiling shows a bottleneck, or an external API requires referential stability).

---

### Q5: How do you set up the React Compiler in a project?

**Answer:**

The React Compiler is distributed as a **Babel plugin** (`babel-plugin-react-compiler`) and optionally an **ESLint plugin** (`eslint-plugin-react-compiler`). It works with any build tool that supports Babel (Vite, Next.js, Webpack, etc.). The compiler requires **React 19** as the runtime.

```jsx
// ─── Step 1: Install the compiler packages ───
// npm install babel-plugin-react-compiler eslint-plugin-react-compiler

// ─── Step 2a: Vite configuration (vite.config.js) ───
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', {
            // Optional: restrict compilation to specific files
            // sources: (filename) => filename.includes('src/components'),
          }],
        ],
      },
    }),
  ],
});

// ─── Step 2b: Next.js configuration (next.config.js) ───
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    reactCompiler: true,
    // Or with options:
    // reactCompiler: {
    //   compilationMode: 'annotation', // only compile opted-in files
    // },
  },
};
module.exports = nextConfig;

// ─── Step 2c: Webpack / Create React App (babel.config.js) ───
module.exports = {
  plugins: [
    ['babel-plugin-react-compiler', {
      // Compiler options
      runtimeModule: 'react/compiler-runtime',
    }],
  ],
};

// ─── Step 3: ESLint plugin setup (.eslintrc.js) ───
module.exports = {
  plugins: ['react-compiler'],
  rules: {
    'react-compiler/react-compiler': 'error', // Flags code that breaks compiler assumptions
  },
};

// ─── Step 4: Verify it's working — check the compiled output ───
// In development mode, the compiler adds debugging hints.
// You can inspect the compiled output in your browser's devtools:
//
// Original:   function MyComponent({ name }) { ... }
// Compiled:   function MyComponent({ name }) { const $ = _c(3); ... }
//
// The _c() call is the compiler's cache initialization — its presence
// confirms the compiler is active.

// ─── Verifying with React DevTools ───
// React DevTools shows a "Memo ✨" badge next to compiler-optimized
// components, so you can visually confirm which components are optimized.
```

**Important notes:**
- The compiler is **opt-in at the build level** — you must explicitly add the Babel plugin.
- It requires **React 19 runtime** because it uses internal memoization primitives (`_c()`) that only exist in React 19's reconciler.
- The ESLint plugin is **strongly recommended** because it catches code that the compiler cannot safely optimize before you encounter runtime issues.

---

## Intermediate Level (Q6–Q12)

---

### Q6: What are the "Rules of React" that the compiler enforces, and why do they matter?

**Answer:**

The React Compiler's ability to auto-memoize depends on a fundamental contract: the **Rules of React**. These rules have always existed as best practices, but before the compiler they were merely guidelines. Now, violating them prevents the compiler from optimizing your code (and the ESLint plugin will flag violations). The core rules are:

1. **Components and hooks must be pure** — given the same inputs, they must return the same output. No observable side effects during render.
2. **Props and state are immutable** — never mutate them directly; always create new values.
3. **Hook call order must be stable** — hooks cannot be called conditionally or in loops.
4. **Render must be idempotent** — calling a component function multiple times with the same props/state must produce the same result.

```jsx
// ─── RULE 1: Components must be pure (no side effects during render) ───

// BAD — breaks the compiler (side effect during render)
function BadCounter({ items }) {
  // Mutating an external variable during render — impure!
  analytics.pageViews++; // Side effect!

  // The compiler cannot cache this because the side effect
  // must run every render, defeating memoization.
  return <div>{items.length} items</div>;
}

// GOOD — pure component, compiler can optimize
function GoodCounter({ items }) {
  // Side effects go in useEffect, not in render
  useEffect(() => {
    analytics.trackPageView();
  }, []);

  return <div>{items.length} items</div>;
}

// ─── RULE 2: Never mutate props or state ───

// BAD — mutates the prop object
function BadSorter({ items }) {
  items.sort((a, b) => a.name.localeCompare(b.name)); // Mutating prop!
  return items.map(item => <div key={item.id}>{item.name}</div>);
}

// GOOD — creates a new sorted array
function GoodSorter({ items }) {
  const sorted = [...items].sort((a, b) => a.name.localeCompare(b.name));
  return sorted.map(item => <div key={item.id}>{item.name}</div>);
}

// ─── RULE 3: Render must be idempotent ───

// BAD — different result each call (uses Date.now() during render)
function BadTimestamp() {
  // The compiler caches this, but it returns stale timestamps!
  const time = Date.now(); // Non-deterministic during render
  return <span>Rendered at: {time}</span>;
}

// GOOD — use state or effects for dynamic values
function GoodTimestamp() {
  const [time, setTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => setTime(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  return <span>Rendered at: {time}</span>;
}

// ─── RULE 4: Local mutation is fine (create-then-mutate pattern) ───

// GOOD — the compiler understands local mutation
function TagList({ tags }) {
  // Creating a new array and mutating it locally is fine
  const sorted = [];
  for (const tag of tags) {
    sorted.push(tag.toLowerCase());
  }
  sorted.sort();

  return sorted.map(tag => <span key={tag}>{tag}</span>);
}
// The compiler recognizes that `sorted` is locally created and never escapes
// the component in a mutated state, so it can safely memoize this computation.
```

**Why these rules matter for the compiler:** The compiler inserts caching guards like `if ($[0] !== prop) { recompute } else { return cached }`. If the component has side effects or mutates inputs, the cached path would skip those side effects or return stale data, breaking correctness. The rules guarantee that skipping re-execution when inputs haven't changed is always safe.

---

### Q7: What code patterns can the compiler NOT optimize?

**Answer:**

The compiler bails out (skips optimization) for components that violate the Rules of React or use patterns where the compiler cannot prove safety. When it bails out, your component still works — it just doesn't get auto-memoized, behaving exactly like React 18 code. The ESLint plugin flags these patterns.

```jsx
// ─── Pattern 1: External mutable state read during render ───
let globalCounter = 0;

function BrokenComponent({ name }) {
  // Compiler CANNOT optimize: reading mutable external state
  // If cached, globalCounter changes would be invisible
  const count = globalCounter;
  return <div>{name}: {count}</div>;
}

// FIX: Use React state or a store (useSyncExternalStore)
function FixedComponent({ name }) {
  const count = useSyncExternalStore(
    store.subscribe,
    store.getSnapshot
  );
  return <div>{name}: {count}</div>;
}

// ─── Pattern 2: Mutating objects that escape the component ───
function BrokenForm({ formRef }) {
  // Compiler cannot optimize: mutating an external ref during render
  formRef.current.isDirty = true; // Mutation of external state!
  return <input />;
}

// FIX: Perform mutations in effects or event handlers
function FixedForm({ formRef }) {
  useEffect(() => {
    formRef.current.isDirty = true;
  });
  return <input />;
}

// ─── Pattern 3: Dynamic hook calls (conditionally calling hooks) ───
function BrokenConditionalHook({ shouldFetch }) {
  // Compiler bails out: hook call order isn't static
  if (shouldFetch) {
    const data = useFetch('/api/data'); // Conditional hook call!
    return <div>{data}</div>;
  }
  return <div>No data</div>;
}

// FIX: Always call hooks, conditionally use the result
function FixedConditionalHook({ shouldFetch }) {
  const data = useFetch(shouldFetch ? '/api/data' : null);
  return <div>{shouldFetch ? data : 'No data'}</div>;
}

// ─── Pattern 4: Spread of unknown dynamic object as props ───
function BrokenSpread({ config }) {
  // The compiler may not optimize when spreading unknown objects
  // because it cannot track individual properties
  return <Child {...config} />;
}

// This is fine — compiler can track known properties
function FixedExplicit({ config }) {
  return <Child name={config.name} age={config.age} />;
}

// ─── Pattern 5: Using eval or dynamic code generation ───
function BrokenDynamic({ expression }) {
  // Compiler cannot analyze dynamic code
  const result = eval(expression);
  return <div>{result}</div>;
}

// ─── Opting out: The "use no memo" directive ───
function LegacyComponent({ data }) {
  'use no memo'; // Tells the compiler to skip this component entirely

  // Maybe this component relies on referential inequality for some reason
  // or has a known pattern the compiler doesn't handle well
  return <ThirdPartyWidget data={data} />;
}
```

**Key takeaway:** When the compiler cannot optimize a component, it simply doesn't transform it — the component works exactly as it did in React 18. There's no runtime crash. The ESLint plugin helps you find and fix these patterns proactively.

---

### Q8: What does the compiled output actually look like, and what is the `_c()` function?

**Answer:**

The React Compiler transforms component functions by inserting a **cache array** (initialized with `_c(numSlots)`) and wrapping every computed value, callback, and JSX expression in **conditional cache guards**. The `_c()` function is provided by React 19's internal runtime (`react/compiler-runtime`) and returns a persistent array that survives across re-renders — similar to how `useRef` persists, but optimized for the compiler's access patterns.

```jsx
// ─── Original component ───
function PriceDisplay({ price, currency, discount }) {
  const finalPrice = price * (1 - discount);
  const formatted = `${currency}${finalPrice.toFixed(2)}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(formatted);
  };

  return (
    <div className="price">
      <span>{formatted}</span>
      {discount > 0 && <span className="discount">-{discount * 100}% off</span>}
      <button onClick={handleCopy}>Copy</button>
    </div>
  );
}

// ─── Compiler output (actual shape, slightly simplified) ───
import { c as _c } from 'react/compiler-runtime';

function PriceDisplay({ price, currency, discount }) {
  const $ = _c(12); // 12 cache slots for this component

  // Slot 0-2: finalPrice computation
  let finalPrice;
  if ($[0] !== price || $[1] !== discount) {
    finalPrice = price * (1 - discount);
    $[0] = price;
    $[1] = discount;
    $[2] = finalPrice;
  } else {
    finalPrice = $[2];
  }

  // Slot 3-5: formatted string
  let formatted;
  if ($[3] !== currency || $[4] !== finalPrice) {
    formatted = `${currency}${finalPrice.toFixed(2)}`;
    $[3] = currency;
    $[4] = finalPrice;
    $[5] = formatted;
  } else {
    formatted = $[5];
  }

  // Slot 6-7: handleCopy callback
  let handleCopy;
  if ($[6] !== formatted) {
    handleCopy = () => {
      navigator.clipboard.writeText(formatted);
    };
    $[6] = formatted;
    $[7] = handleCopy;
  } else {
    handleCopy = $[7];
  }

  // Slot 8-9: discount badge (conditional JSX)
  let t0;
  if ($[8] !== discount) {
    t0 = discount > 0
      ? <span className="discount">-{discount * 100}% off</span>
      : undefined;
    $[8] = discount;
    $[9] = t0;
  } else {
    t0 = $[9];
  }

  // Slot 10-11: entire JSX tree
  let t1;
  if ($[10] !== formatted || $[10] !== handleCopy || $[11] !== t0) {
    t1 = (
      <div className="price">
        <span>{formatted}</span>
        {t0}
        <button onClick={handleCopy}>Copy</button>
      </div>
    );
    $[10] = formatted;
    $[11] = handleCopy;
    // Note: more slots used in practice for the JSX guard
  } else {
    t1 = $[12]; // cached JSX
  }

  return t1;
}
```

**How `_c()` works internally:**
- `_c(n)` allocates an array of `n` slots, initialized with a special `REACT_MEMO_CACHE_SENTINEL` symbol.
- The array is stored on the fiber node (like `useRef` data), so it persists across re-renders.
- The `$[i] !== value` comparison uses `Object.is()` semantics (same as React's dependency comparison).
- First render: all guards fail (sentinel !== any real value), so everything computes fresh.
- Subsequent renders: guards pass for unchanged inputs, returning cached values instantly.

---

### Q9: How do you gradually adopt the React Compiler in an existing codebase?

**Answer:**

The compiler supports **gradual adoption** — you don't have to compile your entire codebase at once. There are three strategies: **directory-based**, **annotation-based**, and **file-filter-based**. This is critical for large codebases where some code may violate the Rules of React and needs refactoring before it can be compiled.

```jsx
// ─── Strategy 1: File/directory filter (Babel plugin option) ───
// In your build config (vite.config.js, babel.config.js, etc.)
{
  plugins: [
    ['babel-plugin-react-compiler', {
      sources: (filename) => {
        // Only compile files in specific directories
        return filename.includes('src/components/') ||
               filename.includes('src/pages/');
        // Files outside these directories are left untouched
      },
    }],
  ],
}

// ─── Strategy 2: Annotation-based opt-in (compilationMode: 'annotation') ───
// In your build config:
{
  plugins: [
    ['babel-plugin-react-compiler', {
      compilationMode: 'annotation',
      // Only functions with "use memo" directive are compiled
    }],
  ],
}

// Then opt in per-component:
function OptimizedDashboard({ data }) {
  'use memo'; // Compiler will optimize this component

  const processed = heavyTransform(data);
  return <Chart data={processed} />;
}

function LegacyWidget({ config }) {
  // No "use memo" directive — compiler skips this
  return <div>{config.value}</div>;
}

// ─── Strategy 3: Opt-out with "use no memo" ───
// Default: compile everything. Opt out where needed.
{
  plugins: [
    ['babel-plugin-react-compiler', {}], // Compile all files
  ],
}

function ProblematicComponent({ data }) {
  'use no memo'; // Skip compilation for this function only

  // This component has patterns the compiler can't handle yet
  // (e.g., it mutates external state during render)
  externalCache[data.id] = data;
  return <div>{data.name}</div>;
}

// ─── Recommended gradual adoption plan for a large app ───
// Phase 1: Install ESLint plugin, fix all violations
//   eslint-plugin-react-compiler identifies problem code
//
// Phase 2: Enable compiler on new code only
//   sources: (filename) => filename.includes('src/features/new-feature/')
//
// Phase 3: Expand to stable, well-tested directories
//   sources: (filename) => !filename.includes('src/legacy/')
//
// Phase 4: Enable for entire codebase, use "use no memo" for exceptions
//   compilationMode: 'all' (default)
//
// Phase 5: Remove manual useMemo/useCallback/memo and "use no memo" directives
//   npx react-codemod remove-unnecessary-memo

// ─── Monitoring: Verify compiler effectiveness ───
// React DevTools Profiler shows which components are compiler-optimized
// Look for the "Memo ✨" badge and reduced render counts
```

---

### Q10: How does the React Compiler work alongside TypeScript, and do types help the compiler?

**Answer:**

The React Compiler operates at the **JavaScript/JSX level** after TypeScript compilation. It does not read TypeScript types directly. However, TypeScript **indirectly helps** the compiler in several ways: typed code tends to follow the Rules of React more consistently, TypeScript prevents many mutation patterns that would break compiler assumptions, and the type system guides developers toward immutable data patterns.

```jsx
// ─── TypeScript code that HELPS the compiler (indirectly) ───

// Readonly types prevent mutations that would break the compiler
interface Product {
  readonly id: string;
  readonly name: string;
  readonly price: number;
}

// TypeScript enforces immutability — compiler can safely cache
function ProductCard({ product }: { product: Product }) {
  // TypeScript error: Cannot assign to 'name' because it is a read-only property
  // product.name = 'hacked'; // TS prevents this rule violation!

  const formattedPrice = `$${product.price.toFixed(2)}`;
  return (
    <div>
      <h3>{product.name}</h3>
      <p>{formattedPrice}</p>
    </div>
  );
}

// ─── TypeScript patterns that work well with the compiler ───

// Discriminated unions — compiler tracks the narrowed type
type LoadState<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function DataDisplay({ state }: { state: LoadState<Product[]> }) {
  // Compiler memoizes each branch independently
  if (state.status === 'loading') return <Spinner />;
  if (state.status === 'error') return <Error message={state.error.message} />;

  // Compiler knows: this block depends on state.data
  const total = state.data.reduce((sum, p) => sum + p.price, 0);
  return (
    <div>
      <ProductList products={state.data} />
      <p>Total: ${total.toFixed(2)}</p>
    </div>
  );
}

// ─── Generic hooks — TypeScript ensures type-safe memoization ───
function useSorted<T>(items: T[], compareFn: (a: T, b: T) => number): T[] {
  // Compiler auto-memoizes: recomputes only when items or compareFn change
  return [...items].sort(compareFn);
}

function LeaderBoard({ players }: { players: Player[] }) {
  // TypeScript ensures compareFn signature matches Player type
  const ranked = useSorted(players, (a, b) => b.score - a.score);

  return ranked.map((player, i) => (
    <div key={player.id}>
      #{i + 1} {player.name}: {player.score}
    </div>
  ));
}

// ─── Caveat: Type assertions can hide compiler-breaking patterns ───

function DangerousComponent({ data }: { data: unknown }) {
  // Type assertion hides the mutation from TypeScript
  // but the compiler's static analysis still catches it
  const obj = data as { count: number };
  obj.count++; // Compiler detects prop mutation — bails out!

  return <div>{obj.count}</div>;
}
```

**Key takeaways:**
- The compiler doesn't read `.d.ts` files or type annotations — it analyzes the emitted JavaScript.
- TypeScript helps indirectly by encouraging immutable patterns and catching mutations at the type level.
- `Readonly<T>`, `ReadonlyArray<T>`, and `as const` make your code both type-safe and compiler-friendly.

---

### Q11: How does the performance of compiler-optimized code compare to manually memoized React 18 code?

**Answer:**

In benchmarks, compiler-optimized code performs **comparably to or better than** expert-level manual memoization — and significantly better than the typical codebase where memoization is inconsistently applied. The compiler's advantage is **consistency**: it memoizes *every* computation, callback, and JSX node, while developers typically only memoize the obvious cases and miss the subtle ones.

```jsx
// ─── React 18: Typical developer memoization (inconsistent) ───
// A real-world scenario where developers usually miss optimizations

function OrderSummary({ items, taxRate, shippingCost, onCheckout }) {
  // Developer remembered to memoize the expensive calculation
  const subtotal = useMemo(
    () => items.reduce((sum, item) => sum + item.price * item.qty, 0),
    [items]
  );

  // Developer remembered this one too
  const total = useMemo(
    () => subtotal + (subtotal * taxRate) + shippingCost,
    [subtotal, taxRate, shippingCost]
  );

  // MISSED: Developer forgot to memoize the callback
  const handleCheckout = () => {
    onCheckout({ items, total });
  };

  // MISSED: This inline object creates new reference every render
  const summaryData = { subtotal, tax: subtotal * taxRate, shipping: shippingCost, total };

  // MISSED: This JSX subtree re-creates every render
  const taxLine = <span className="tax">Tax ({taxRate * 100}%): ${(subtotal * taxRate).toFixed(2)}</span>;

  return (
    <div>
      {items.map(item => (
        // MISSED: Inline arrow function defeats child memoization
        <LineItem key={item.id} item={item} onRemove={() => removeItem(item.id)} />
      ))}
      {taxLine}
      <p>Total: ${total.toFixed(2)}</p>
      {/* MISSED: summaryData is a new object → OrderDetails re-renders */}
      <OrderDetails data={summaryData} />
      <button onClick={handleCheckout}>Checkout</button>
    </div>
  );
}

// ─── React 19 Compiler: Memoizes EVERYTHING automatically ───
function OrderSummary({ items, taxRate, shippingCost, onCheckout }) {
  // All of these are automatically memoized:
  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const total = subtotal + (subtotal * taxRate) + shippingCost;
  const handleCheckout = () => onCheckout({ items, total });
  const summaryData = { subtotal, tax: subtotal * taxRate, shipping: shippingCost, total };
  const taxLine = <span className="tax">Tax ({taxRate * 100}%): ${(subtotal * taxRate).toFixed(2)}</span>;

  return (
    <div>
      {items.map(item => (
        <LineItem key={item.id} item={item} onRemove={() => removeItem(item.id)} />
      ))}
      {taxLine}
      <p>Total: ${total.toFixed(2)}</p>
      <OrderDetails data={summaryData} />
      <button onClick={handleCheckout}>Checkout</button>
    </div>
  );
}

// ─── Performance comparison (conceptual benchmark results) ───
//
// Scenario: 500 items, taxRate change triggers re-render
//
// React 18 (no memoization):          ~45ms render
// React 18 (manual memo, typical):    ~18ms render  (developer missed 3 opportunities)
// React 18 (manual memo, expert):     ~8ms render   (everything perfectly memoized)
// React 19 (compiler):                ~7ms render   (compiler catches everything)
//
// The compiler matches expert-level memoization but with zero developer effort.
// The real win is in typical codebases where manual memoization is inconsistent.
```

**The compiler's performance advantages:**
1. **Granular cache keys** — the compiler tracks individual property access (`item.price`) instead of whole objects (`item`), causing fewer cache invalidations.
2. **Complete coverage** — memoizes JSX, callbacks, objects, and intermediate computations that developers typically skip.
3. **No overhead of `useMemo`/`useCallback` hooks** — the `_c()` cache array is a lighter mechanism than hook state.

---

### Q12: How does the React Compiler compare to Angular signals and Svelte's compile-time reactivity?

**Answer:**

All three frameworks now have compile-time optimization strategies, but they take fundamentally different approaches. React's Compiler is unique in that it **preserves the existing programming model** — you write the same React code you always have, and the compiler optimizes it transparently. Angular and Svelte require you to adopt new primitives.

```jsx
// ─── React 19 (Compiler): Standard JavaScript, auto-optimized ───
function Counter() {
  const [count, setCount] = useState(0);
  const doubled = count * 2;

  return (
    <div>
      <p>Count: {count}</p>
      <p>Doubled: {doubled}</p>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
    </div>
  );
}
// The compiler auto-memoizes `doubled` and the JSX.
// You write plain JS — no new syntax or primitives.

// ─── Angular 19 (Signals): Explicit reactive primitives ───
// @Component({
//   template: `
//     <div>
//       <p>Count: {{ count() }}</p>
//       <p>Doubled: {{ doubled() }}</p>
//       <button (click)="increment()">Increment</button>
//     </div>
//   `
// })
// export class CounterComponent {
//   count = signal(0);                         // New primitive
//   doubled = computed(() => this.count() * 2); // Explicit derivation
//
//   increment() {
//     this.count.update(c => c + 1);            // Signal update API
//   }
// }

// ─── Svelte 5 (Runes): Compiler-driven with special syntax ───
// <script>
//   let count = $state(0);          // $state rune (compiler directive)
//   let doubled = $derived(count * 2); // $derived rune
//
//   function increment() {
//     count++;                       // Direct mutation (Svelte compiles this)
//   }
// </script>
//
// <div>
//   <p>Count: {count}</p>
//   <p>Doubled: {doubled}</p>
//   <button onclick={increment}>Increment</button>
// </div>

// ─── Comparison table ───
//
// | Aspect             | React Compiler     | Angular Signals   | Svelte Runes      |
// |--------------------|--------------------|-------------------|-------------------|
// | Programming model  | Same (no changes)  | New signal API    | New rune syntax   |
// | When it runs       | Build time         | Runtime           | Build time        |
// | Granularity        | Per-expression     | Per-signal        | Per-statement     |
// | Migration cost     | Near zero          | High (rewrite)    | Medium            |
// | Learning curve     | None (existing JS) | Learn signals     | Learn runes       |
// | Component overhead | Memoized renders   | Skips re-renders  | No virtual DOM    |
// | Existing codebase  | Drop-in Babel plugin| Gradual migration| Must use Svelte   |
```

**React's unique advantage:** Because the React Compiler doesn't change the programming model, you get the optimization benefits without any learning curve, migration effort, or lock-in to new primitives. Your code remains standard JavaScript functions and JSX, portable and easy to understand. The tradeoff is that React still uses a virtual DOM and reconciliation, while Svelte compiles away the framework entirely.

---

## Advanced Level (Q13–Q20)

---

### Q13: When is manual useMemo still genuinely needed even with the React Compiler?

**Answer:**

While the compiler handles the vast majority of memoization, there are specific scenarios where **explicit `useMemo` remains valuable or necessary**. The compiler always respects existing `useMemo` calls — it won't remove them or double-wrap them. The key question is: does the memoization serve a purpose beyond preventing re-renders?

```jsx
// ─── Case 1: Expensive computations with intentional caching semantics ───
// The compiler WILL memoize this, but useMemo makes the performance intent explicit
// for code reviewers and future maintainers.

function AnalyticsDashboard({ rawData }: { rawData: DataPoint[] }) {
  // 50,000+ data points, complex statistical computation
  // useMemo here is documentation: "This is intentionally expensive and cached"
  const statistics = useMemo(() => {
    const mean = rawData.reduce((s, d) => s + d.value, 0) / rawData.length;
    const stdDev = Math.sqrt(
      rawData.reduce((s, d) => s + (d.value - mean) ** 2, 0) / rawData.length
    );
    const percentiles = computePercentiles(rawData, [25, 50, 75, 90, 99]);
    const outliers = rawData.filter(d => Math.abs(d.value - mean) > 3 * stdDev);
    return { mean, stdDev, percentiles, outliers };
  }, [rawData]);

  return <StatisticsPanel stats={statistics} />;
}

// ─── Case 2: Referential identity needed by external (non-React) systems ───

function MapView({ locations }: { locations: Location[] }) {
  // The Mapbox SDK uses reference equality to decide whether to re-initialize
  // the map layer. Even though the compiler memoizes this, using useMemo
  // makes the contract with the external library explicit.
  const geoJsonSource = useMemo(() => ({
    type: 'FeatureCollection' as const,
    features: locations.map(loc => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [loc.lng, loc.lat] },
      properties: { name: loc.name },
    })),
  }), [locations]);

  // Mapbox internally does: if (newSource !== prevSource) reinitialize()
  useMapboxSource('locations', geoJsonSource);

  return <div id="map" />;
}

// ─── Case 3: Lazy initialization that should NOT re-run ───

function CodeEditor({ language }: { language: string }) {
  // This creates a heavyweight parser instance. The compiler would memoize it
  // based on `language`, but useMemo makes the intent clearer and ensures
  // the parser is only created when the language actually changes.
  const parser = useMemo(() => {
    console.log(`Initializing ${language} parser...`); // Takes ~200ms
    return createLanguageParser(language, {
      errorRecovery: true,
      syntaxHighlighting: true,
      autoComplete: true,
    });
  }, [language]);

  // Without useMemo, a reader might not realize this is expensive
  // and might refactor the code in a way that breaks the caching.

  return <MonacoEditor parser={parser} />;
}

// ─── Case 4: Values shared via context where identity matters ───

function AppProviders({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [theme, setTheme] = useState<Theme>(defaultTheme);

  // Context value — every consumer re-renders when this changes.
  // The compiler memoizes this, but useMemo makes it explicit that
  // identity stability is critical for preventing cascade re-renders.
  const authContext = useMemo(
    () => ({ user, login: setUser, logout: () => setUser(null) }),
    [user]
  );

  return (
    <AuthContext value={authContext}>
      <ThemeContext value={theme}>
        {children}
      </ThemeContext>
    </AuthContext>
  );
}

// ─── Case 5: When the compiler can't analyze the computation ───

function DynamicComponent({ config }: { config: PluginConfig }) {
  // The compiler may bail out on dynamic imports or complex
  // control flow that it can't statically analyze
  const PluginComponent = useMemo(() => {
    return loadPlugin(config.pluginId).component;
  }, [config.pluginId]);

  return <PluginComponent settings={config.settings} />;
}
```

**Summary:** After adopting the compiler, keep `useMemo` only when (1) the computation is genuinely expensive and you want to document that intent, (2) an external system requires referential identity, or (3) the compiler bails out on a specific pattern. For everything else, let the compiler handle it.

---

### Q14: How does the React Compiler interact with third-party libraries?

**Answer:**

The React Compiler only transforms **your** source code (files that pass through the Babel plugin). It does **not** recompile third-party libraries from `node_modules`. This means third-party components behave exactly as they did before. The interaction points are: (a) how compiled parent components pass props to uncompiled children, and (b) whether third-party hooks and components follow the Rules of React.

```jsx
// ─── Scenario 1: Passing props to third-party components ───

// Your compiled component
function Dashboard({ data }) {
  // Compiler memoizes these:
  const chartConfig = { type: 'bar', animate: true };
  const handleSelect = (point) => console.log(point);

  // Recharts is NOT compiled, but it receives stable prop references
  // thanks to the compiler memoizing chartConfig and handleSelect.
  // This is BETTER than React 18 without manual memoization!
  return (
    <div>
      <RechartsBarChart
        data={data}
        config={chartConfig}
        onSelect={handleSelect}
      />
    </div>
  );
}

// ─── Scenario 2: Third-party hooks that follow Rules of React ───

// Works perfectly — TanStack Query follows the Rules of React
function UserProfile({ userId }) {
  // Third-party hook — not compiled, but doesn't need to be
  const { data, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  });

  // Compiler memoizes everything in YOUR component
  if (isLoading) return <Skeleton />;

  const fullName = `${data.firstName} ${data.lastName}`;
  return <ProfileCard name={fullName} avatar={data.avatar} />;
}

// ─── Scenario 3: Third-party hooks that BREAK the rules ───

// Some older libraries mutate state during render or have side effects
function ProblematicIntegration({ formId }) {
  // Hypothetical old form library that mutates a global registry during render
  const form = useOldFormLib(formId); // Mutates window.__FORMS__ during render!

  // The compiler may memoize this component and skip re-renders,
  // which means the global registry mutation gets skipped too.
  // This causes bugs!

  return <form>{form.fields.map(f => <input key={f.name} {...f} />)}</form>;
}

// FIX: Opt out for this specific component
function FixedIntegration({ formId }) {
  'use no memo'; // Tell compiler to skip this component

  const form = useOldFormLib(formId);
  return <form>{form.fields.map(f => <input key={f.name} {...f} />)}</form>;
}

// ─── Scenario 4: Component libraries (MUI, Chakra, etc.) ───

// These work seamlessly because:
// 1. The library code in node_modules is NOT compiled (no change)
// 2. YOUR usage of the components IS compiled
// 3. The compiler memoizes the props you pass to them

function SettingsPage({ settings, onSave }) {
  // All compiler-optimized — MUI components receive stable props
  const handleToggle = (key) => (event) => {
    onSave({ ...settings, [key]: event.target.checked });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4">Settings</Typography>
      <FormGroup>
        <FormControlLabel
          control={
            <Switch
              checked={settings.darkMode}
              onChange={handleToggle('darkMode')}
            />
          }
          label="Dark Mode"
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.notifications}
              onChange={handleToggle('notifications')}
            />
          }
          label="Notifications"
        />
      </FormGroup>
    </Box>
  );
}

// ─── Scenario 5: Ensuring library compatibility before adoption ───
// Use the ESLint plugin on your code to check for rule violations:
//
// npx eslint --rule 'react-compiler/react-compiler: error' src/
//
// For third-party libraries, check:
// 1. Does the library use forwardRef? (works fine)
// 2. Does the library expose hooks? (check they follow rules)
// 3. Does the library use React.memo internally? (harmless, just redundant)
// 4. Does the library mutate props? (problem — use "use no memo")
```

**Best practices for library compatibility:**
- Most popular, well-maintained libraries (TanStack Query, React Router, Zustand, MUI, etc.) work perfectly with the compiler.
- Test your app thoroughly after enabling the compiler — if a third-party integration breaks, add `'use no memo'` to the specific component.
- Report issues to library maintainers — they should be following the Rules of React anyway.

---

### Q15: How do you debug compiler-optimized code?

**Answer:**

Debugging compiler-optimized code is a common concern, but React provides excellent tooling. The key principle is: **you debug your source code, not the compiled output**. Source maps ensure breakpoints and stack traces point to your original code. React DevTools provides compiler-specific insights.

```jsx
// ─── Tool 1: React DevTools — Compiler badges and insights ───

// React DevTools shows which components are compiler-optimized:
// - Components panel: "Memo ✨" badge on compiled components
// - Profiler: Shows "Compiler optimized" in the flame chart
// - Props panel: Shows which props caused re-render vs. were cached

// ─── Tool 2: Source maps — Debug your original code ───

// Your source code:
function OrderList({ orders, currency }) {
  const formatted = orders.map(order => ({
    ...order,
    displayPrice: formatCurrency(order.total, currency),
  }));

  // Set breakpoint HERE — source maps point to this exact line
  // even though the compiled code wraps it in a cache guard
  debugger;

  return formatted.map(order => (
    <OrderRow key={order.id} order={order} />
  ));
}

// ─── Tool 3: The "use no memo" escape hatch for debugging ───

function SuspiciousComponent({ data }) {
  'use no memo'; // Temporarily disable compiler for this component

  // Now this component behaves exactly like React 18
  // If the bug disappears, the issue is compiler-related
  const processed = transformData(data);
  return <Display data={processed} />;
}

// ─── Tool 4: Compiler playground for inspecting output ───
// Visit: https://playground.react.dev/
// Paste your component and see the exact compiled output
// This helps understand what the compiler is doing and why
// certain patterns might cause unexpected behavior

// ─── Tool 5: Runtime validation in development mode ───

// In development, the compiler inserts additional checks:
function DebugExample({ items }) {
  // In DEV mode, the compiler double-invokes the render function
  // and compares results to detect impurity.
  //
  // If your component returns different results for the same inputs,
  // you'll see a console warning:
  // "Warning: Component DebugExample rendered with the same props
  //  but returned a different result. This breaks compiler assumptions."

  const sorted = [...items].sort(); // Pure — same input → same output ✓

  return sorted.map(item => <span key={item}>{item}</span>);
}

// ─── Debugging strategy: Bisection with "use no memo" ───

// Step 1: Bug observed in production
// Step 2: Add "use no memo" to ALL components in the affected area
// Step 3: If bug disappears, the compiler is involved
// Step 4: Remove "use no memo" one component at a time
// Step 5: Identify the specific component where the bug reappears
// Step 6: Inspect that component for Rules of React violations

// Example of a subtle bug the compiler exposes:
function ChatMessages({ messages, userId }) {
  // BUG: This reads Date.now() during render — non-deterministic!
  // The compiler caches the result, so timestamps freeze.
  const withTimestamps = messages.map(msg => ({
    ...msg,
    timeAgo: formatTimeAgo(msg.createdAt, Date.now()),
  }));

  return withTimestamps.map(msg => (
    <Message key={msg.id} message={msg} isOwn={msg.authorId === userId} />
  ));
}

// FIX: Use state for time-dependent values
function ChatMessages({ messages, userId }) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(interval);
  }, []);

  const withTimestamps = messages.map(msg => ({
    ...msg,
    timeAgo: formatTimeAgo(msg.createdAt, now), // now is state, tracked by compiler
  }));

  return withTimestamps.map(msg => (
    <Message key={msg.id} message={msg} isOwn={msg.authorId === userId} />
  ));
}
```

---

### Q16: How does the React Compiler ESLint plugin work, and what violations does it detect?

**Answer:**

The `eslint-plugin-react-compiler` is a static analysis tool that runs alongside the compiler to detect code that **violates the Rules of React** and would prevent the compiler from optimizing correctly. Unlike the compiler itself (which silently skips problematic code), the ESLint plugin actively **warns** developers so they can fix issues before they become subtle runtime bugs.

```jsx
// ─── Setup ───
// .eslintrc.js
module.exports = {
  plugins: ['react-compiler'],
  rules: {
    'react-compiler/react-compiler': 'error',
  },
};

// ─── Violation 1: Mutating props ───
function UserCard({ user }) {
  user.displayName = user.firstName + ' ' + user.lastName;
  // ⛔ ESLint: "Mutating component props breaks the Rules of React.
  //    Props should be treated as immutable."
  return <div>{user.displayName}</div>;
}

// Fix:
function UserCard({ user }) {
  const displayName = user.firstName + ' ' + user.lastName; // ✅ New variable
  return <div>{displayName}</div>;
}

// ─── Violation 2: Mutating state directly ───
function TodoList() {
  const [todos, setTodos] = useState([]);

  const addTodo = (text) => {
    todos.push({ text, done: false }); // ⛔ Mutating state directly
    setTodos(todos);
  };

  return <div>{todos.map(t => <span key={t.text}>{t.text}</span>)}</div>;
}

// Fix:
function TodoList() {
  const [todos, setTodos] = useState([]);

  const addTodo = (text) => {
    setTodos(prev => [...prev, { text, done: false }]); // ✅ Immutable update
  };

  return <div>{todos.map(t => <span key={t.text}>{t.text}</span>)}</div>;
}

// ─── Violation 3: Side effects during render ───
let renderCount = 0;

function Analytics({ page }) {
  renderCount++; // ⛔ Side effect during render — modifies external variable
  // ESLint: "Modifying external variables during render breaks compiler
  //    memoization. Move this to useEffect."

  return <div>Page: {page}</div>;
}

// Fix:
function Analytics({ page }) {
  useEffect(() => {
    trackRender(page); // ✅ Side effect in useEffect
  });
  return <div>Page: {page}</div>;
}

// ─── Violation 4: Non-deterministic values during render ───
function RandomGreeting({ name }) {
  const greetings = ['Hello', 'Hi', 'Hey', 'Welcome'];
  const greeting = greetings[Math.floor(Math.random() * greetings.length)];
  // ⛔ ESLint: "Using Math.random() during render produces non-deterministic
  //    output. The compiler may cache this, returning stale random values."

  return <h1>{greeting}, {name}!</h1>;
}

// Fix:
function RandomGreeting({ name }) {
  const [greeting] = useState(() => {
    const greetings = ['Hello', 'Hi', 'Hey', 'Welcome'];
    return greetings[Math.floor(Math.random() * greetings.length)];
  }); // ✅ Computed once during initialization

  return <h1>{greeting}, {name}!</h1>;
}

// ─── Violation 5: Ref access during render ───
function MeasuredBox({ children }) {
  const ref = useRef(null);
  const width = ref.current?.offsetWidth || 0;
  // ⛔ ESLint: "Reading ref.current during render is unsafe.
  //    ref.current may not be up to date during render."

  return <div ref={ref} style={{ minWidth: width }}>{children}</div>;
}

// Fix:
function MeasuredBox({ children }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    if (ref.current) {
      setWidth(ref.current.offsetWidth); // ✅ Read ref in effect
    }
  });

  return <div ref={ref} style={{ minWidth: width }}>{children}</div>;
}

// ─── Violation 6: Calling hooks conditionally ───
function ConditionalComponent({ showExtra }) {
  const [name, setName] = useState('');

  if (showExtra) {
    const [extra, setExtra] = useState(''); // ⛔ Conditional hook call
  }

  return <div>{name}</div>;
}

// Fix:
function ConditionalComponent({ showExtra }) {
  const [name, setName] = useState('');
  const [extra, setExtra] = useState(''); // ✅ Always called

  return (
    <div>
      {name}
      {showExtra && <span>{extra}</span>}
    </div>
  );
}
```

**The ESLint plugin's value proposition:** It catches problems **before** the compiler encounters them, at lint time rather than at build time. This gives developers immediate feedback in their editor, with specific error messages and fix suggestions.

---

### Q17: What is the migration path for removing manual memoization after adopting the compiler?

**Answer:**

Removing manual memoization is a **phased process** that should be done carefully, with testing at each stage. The React team provides a **codemod** that automates the removal, but understanding the strategy is important for interviews and for safely migrating large codebases.

```jsx
// ─── Phase 1: Enable the compiler alongside existing memoization ───
// The compiler respects existing useMemo/useCallback/memo — they coexist safely.
// This means you can enable the compiler with ZERO code changes.

// Before compiler: works
const UserCard = memo(function UserCard({ user }) {
  const fullName = useMemo(() => `${user.first} ${user.last}`, [user.first, user.last]);
  const handleClick = useCallback(() => navigate(`/user/${user.id}`), [user.id]);
  return <div onClick={handleClick}>{fullName}</div>;
});

// After enabling compiler: STILL works (compiler doesn't interfere with existing memo)
// The component is now double-memoized (harmless, just redundant)

// ─── Phase 2: Run the codemod to remove unnecessary memoization ───
// npx react-codemod remove-unnecessary-memo src/

// The codemod transforms:
const UserCard = memo(function UserCard({ user }) {
  const fullName = useMemo(() => `${user.first} ${user.last}`, [user.first, user.last]);
  const handleClick = useCallback(() => navigate(`/user/${user.id}`), [user.id]);
  return <div onClick={handleClick}>{fullName}</div>;
});

// Into:
function UserCard({ user }) {
  const fullName = `${user.first} ${user.last}`;
  const handleClick = () => navigate(`/user/${user.id}`);
  return <div onClick={handleClick}>{fullName}</div>;
}

// ─── Phase 3: Review and keep intentional memoization ───
// The codemod is conservative — it removes clear cases but flags ambiguous ones.
// Review flagged cases manually:

// KEEP: Expensive computation (intentional memoization)
function DataGrid({ rows }) {
  // Codemod flags this: "useMemo may be intentional — review manually"
  const sortedRows = useMemo(() => {
    return rows.toSorted((a, b) => {
      // Complex multi-column sort with locale-aware comparison
      return a.name.localeCompare(b.name) || a.date - b.date || a.id - b.id;
    });
  }, [rows]);

  return <VirtualizedTable rows={sortedRows} />;
}

// REMOVE: Simple derivation (compiler handles this)
function StatusBadge({ status }) {
  // Codemod removes this — trivial computation
  // const color = useMemo(() => STATUS_COLORS[status], [status]);
  const color = STATUS_COLORS[status]; // Compiler auto-memoizes

  return <Badge color={color}>{status}</Badge>;
}

// ─── Phase 4: Full migration example — before and after ───

// BEFORE (React 18 with heavy manual memoization):
const ProductPage = memo(function ProductPage({ productId }) {
  const [quantity, setQuantity] = useState(1);

  const product = useProductQuery(productId);

  const price = useMemo(
    () => product ? formatPrice(product.price * quantity) : '',
    [product, quantity]
  );

  const savings = useMemo(
    () => product?.discount ? formatPrice(product.price * product.discount * quantity) : null,
    [product, quantity]
  );

  const handleAddToCart = useCallback(() => {
    addToCart(productId, quantity);
  }, [productId, quantity]);

  const handleQuantityChange = useCallback((e) => {
    setQuantity(Number(e.target.value));
  }, []);

  const relatedProducts = useMemo(
    () => product?.related?.slice(0, 4) ?? [],
    [product?.related]
  );

  if (!product) return <Skeleton />;

  return (
    <div>
      <h1>{product.name}</h1>
      <p>Price: {price}</p>
      {savings && <p>You save: {savings}</p>}
      <input type="number" value={quantity} onChange={handleQuantityChange} />
      <button onClick={handleAddToCart}>Add to Cart</button>
      <RelatedProducts products={relatedProducts} />
    </div>
  );
});

// AFTER (React 19 with compiler — clean, readable code):
function ProductPage({ productId }) {
  const [quantity, setQuantity] = useState(1);

  const product = useProductQuery(productId);

  if (!product) return <Skeleton />;

  const price = formatPrice(product.price * quantity);
  const savings = product.discount
    ? formatPrice(product.price * product.discount * quantity)
    : null;
  const relatedProducts = product.related?.slice(0, 4) ?? [];

  return (
    <div>
      <h1>{product.name}</h1>
      <p>Price: {price}</p>
      {savings && <p>You save: {savings}</p>}
      <input
        type="number"
        value={quantity}
        onChange={(e) => setQuantity(Number(e.target.value))}
      />
      <button onClick={() => addToCart(productId, quantity)}>
        Add to Cart
      </button>
      <RelatedProducts products={relatedProducts} />
    </div>
  );
}
// 40% fewer lines, 100% more readable, same (or better) performance.
```

**Migration checklist:**
1. Enable the compiler with zero code changes (it coexists with existing memoization).
2. Run the test suite — everything should pass.
3. Run the codemod: `npx react-codemod remove-unnecessary-memo`.
4. Review the codemod output for flagged cases.
5. Run the test suite again.
6. Profile the app to verify performance is equal or better.
7. Ship.

---

### Q18: What are the known limitations and edge cases of the React Compiler?

**Answer:**

While the React Compiler handles the vast majority of real-world React code, it has specific **limitations** where it either bails out (doesn't optimize) or where developers need to be aware of behavioral differences. Understanding these is critical for advanced interviews.

```jsx
// ─── Limitation 1: Class components are NOT compiled ───

class LegacyWidget extends React.Component {
  // The compiler only transforms function components and hooks.
  // Class components are left entirely untouched.
  render() {
    return <div>{this.props.name}</div>;
  }
}

// Solution: Convert to function components (recommended anyway)
function LegacyWidget({ name }) {
  return <div>{name}</div>; // Now the compiler optimizes this
}

// ─── Limitation 2: Dynamic property access on props ───

function DynamicAccess({ data, fieldName }) {
  // The compiler cannot track which property of `data` is accessed
  // because `fieldName` is dynamic
  const value = data[fieldName]; // Compiler uses `data` as the cache key, not `data[fieldName]`

  // This means: if data is a new object but data[fieldName] hasn't changed,
  // the cache is still invalidated (less granular than ideal)
  return <div>{value}</div>;
}

// ─── Limitation 3: Generators and iterators with side effects ───

function* generateSteps(config) {
  // Generators maintain internal state — compiler cannot safely memoize them
  yield { step: 1, label: 'Start' };
  yield { step: 2, label: config.middleLabel };
  yield { step: 3, label: 'Finish' };
}

function Wizard({ config }) {
  // Compiler may bail out on generator consumption during render
  const steps = [...generateSteps(config)]; // Spread consumes generator
  return steps.map(s => <Step key={s.step} label={s.label} />);
}

// ─── Limitation 4: Closures over mutable refs read during render ───

function SearchWithRef({ query }) {
  const cacheRef = useRef(new Map());

  // The compiler cannot track ref mutations — refs are intentionally
  // outside the reactive system
  const cachedResult = cacheRef.current.get(query);
  if (cachedResult) return <Results data={cachedResult} />;

  // This pattern mixes render-time logic with mutable refs
  // The compiler may cache this and skip the ref read on re-renders
  const result = performSearch(query);
  cacheRef.current.set(query, result);
  return <Results data={result} />;
}

// Fix: Use state for render-affecting data
function SearchWithState({ query }) {
  const [cache, setCache] = useState(new Map());

  const result = cache.get(query) ?? performSearch(query);

  useEffect(() => {
    if (!cache.has(query)) {
      setCache(prev => new Map(prev).set(query, result));
    }
  }, [query, result, cache]);

  return <Results data={result} />;
}

// ─── Limitation 5: try/catch blocks around reactive code ───

function SafeRender({ data }) {
  let content;
  try {
    // The compiler may have difficulty with granular memoization
    // inside try blocks because the control flow has multiple exit paths
    const processed = transformData(data);
    content = <DataView data={processed} />;
  } catch (error) {
    content = <ErrorView error={error} />;
  }

  return <div>{content}</div>;
}

// ─── Limitation 6: The compiler doesn't optimize across component boundaries ───

function Parent({ items }) {
  // Compiler memoizes within Parent
  const filtered = items.filter(i => i.active);

  return <Child items={filtered} />;
}

function Child({ items }) {
  // Compiler memoizes within Child — but independently
  // It does NOT know that Parent already filtered the items
  // Each component is compiled in isolation
  const sorted = [...items].sort((a, b) => a.name.localeCompare(b.name));
  return sorted.map(item => <span key={item.id}>{item.name}</span>);
}
// This is by design — components are independent compilation units.

// ─── Limitation 7: Effects and subscriptions aren't memoized ───

function LiveData({ channelId }) {
  // The compiler memoizes values and JSX, but effects run on their own schedule.
  // It does NOT skip or deduplicate effect execution.
  useEffect(() => {
    const subscription = subscribe(channelId, (data) => {
      // This runs regardless of compiler memoization
      setData(data);
    });
    return () => subscription.unsubscribe();
  }, [channelId]); // Dependencies still matter for effects

  const [data, setData] = useState(null);
  return <Display data={data} />;
}
```

**Summary of limitations:**
| Limitation | Impact | Workaround |
|---|---|---|
| Class components | Not compiled | Convert to function components |
| Dynamic property access | Less granular caching | Destructure known props |
| Generators in render | Bail out | Use plain arrays/maps |
| Ref reads during render | Potentially stale cache | Use state instead |
| Cross-component analysis | None | By design — components are independent |
| Effects | Not memoized | Correct — effects should always run |

---

### Q19: How does the Compiler ESLint plugin differ from the standard react-hooks/exhaustive-deps rule, and how do they work together?

**Answer:**

The `react-compiler/react-compiler` ESLint rule and the `react-hooks/exhaustive-deps` rule serve **complementary but different purposes**. The hooks rule checks that dependency arrays are correct. The compiler rule checks that your code follows the Rules of React, which is a broader concern. After adopting the compiler, the hooks `exhaustive-deps` rule becomes **less critical** (because the compiler manages dependencies automatically), but the compiler's ESLint rule becomes **essential**.

```jsx
// ─── What react-hooks/exhaustive-deps catches (React 18 concern) ───

function SearchComponent({ query }) {
  const [results, setResults] = useState([]);

  useEffect(() => {
    fetchResults(query).then(setResults);
  }, []); // react-hooks/exhaustive-deps: "query" is missing from dependencies
  // ⚠️ This warning is about MANUAL dependency arrays

  return <ResultList results={results} />;
}

// ─── What react-compiler/react-compiler catches (React 19 concern) ───

let analyticsBuffer = [];

function TrackedPage({ page }) {
  // react-compiler/react-compiler:
  // ⛔ "Modifying external variable 'analyticsBuffer' during render.
  //    This side effect prevents the compiler from memoizing this component."
  analyticsBuffer.push(page);

  // react-hooks/exhaustive-deps would NOT catch this —
  // there's no dependency array involved
  return <div>Page: {page}</div>;
}

// ─── How they work together ───

// Scenario: Migrating to the compiler
function Dashboard({ userId, dateRange }) {
  const [data, setData] = useState(null);

  // react-hooks/exhaustive-deps:
  // ⚠️ Missing dependency: dateRange
  useEffect(() => {
    fetchDashboardData(userId, dateRange).then(setData);
  }, [userId]); // Missing dateRange!

  // react-compiler/react-compiler: ✅ No violations here
  // (The effect dependency issue is a different category of bug)

  // IMPORTANT: The compiler does NOT fix effect dependency bugs.
  // Effects are not auto-memoized — their deps arrays still matter.
  // Keep react-hooks/exhaustive-deps enabled!

  if (!data) return <Spinner />;

  // Compiler handles memoization of render logic:
  const summary = computeSummary(data);
  return <DashboardView summary={summary} />;
}

// ─── Recommended ESLint config for React 19 with compiler ───
module.exports = {
  plugins: ['react-hooks', 'react-compiler'],
  rules: {
    // KEEP: Still essential for useEffect/useLayoutEffect deps
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',

    // ADD: Essential for compiler correctness
    'react-compiler/react-compiler': 'error',
  },
};

// ─── Example showing all three rules in action ───

let cache = {};

function ProductSearch({ category }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  // react-compiler/react-compiler:
  // ⛔ Reading mutable external variable `cache` during render
  const cached = cache[query]; // Rule violation!

  // react-hooks/exhaustive-deps:
  // ⚠️ Missing dependency: `category`
  useEffect(() => {
    search(query, category).then(setResults);
  }, [query]); // Missing `category`!

  // react-hooks/rules-of-hooks:
  if (query.length > 3) {
    const [suggestions] = useState([]); // ⛔ Conditional hook!
  }

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      {results.map(r => <Result key={r.id} result={r} />)}
    </div>
  );
}

// FIXED version:
function ProductSearch({ category }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [suggestions] = useState([]); // ✅ Always called

  // ✅ Use state or useSyncExternalStore instead of external mutable variable
  // (cache logic moved to a custom hook or TanStack Query)

  useEffect(() => {
    search(query, category).then(setResults);
  }, [query, category]); // ✅ All deps included

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      {results.map(r => <Result key={r.id} result={r} />)}
    </div>
  );
}
```

**Key takeaway:** Keep **both** ESLint plugins enabled. `react-hooks` catches dependency array issues (still relevant for effects). `react-compiler` catches Rules of React violations (essential for compiler optimization). They complement each other — neither is a replacement for the other.

---

### Q20: Walk through a production scenario: adopting the React Compiler in a large-scale existing React app.

**Answer:**

This question tests practical migration experience. Here's a realistic step-by-step adoption plan for a large e-commerce application with 500+ components, a mix of function and class components, multiple third-party libraries, and a team of 15 developers.

```jsx
// ═══════════════════════════════════════════════════
// PHASE 1: Assessment (Week 1-2)
// ═══════════════════════════════════════════════════

// Step 1: Audit the codebase
// Run the ESLint plugin in "report-only" mode to assess readiness

// .eslintrc.js — Phase 1 config
module.exports = {
  plugins: ['react-compiler'],
  rules: {
    'react-compiler/react-compiler': 'warn', // Warn, don't error yet
  },
};

// Run: npx eslint src/ --format json > compiler-audit.json
// Typical results for a large app:
// - 47 files with prop mutations
// - 23 files with external state reads during render
// - 12 files with conditional hook calls
// - 8 class components
// - 156 files: clean ✅

// Step 2: Quantify the memoization landscape
// Count existing manual memoization (to measure cleanup later)
// grep -r "useMemo\|useCallback\|React.memo\|memo(" src/ --include="*.tsx" | wc -l
// Result: 892 instances of manual memoization

// ═══════════════════════════════════════════════════
// PHASE 2: Fix violations (Week 3-6)
// ═══════════════════════════════════════════════════

// Step 3: Fix the most common violations

// BEFORE: Prop mutation (47 files)
function OrderItem({ item, onQuantityChange }) {
  item.formattedPrice = formatCurrency(item.price); // ⛔ Mutating prop!
  return (
    <div>
      <span>{item.formattedPrice}</span>
      <QuantitySelector value={item.quantity} onChange={onQuantityChange} />
    </div>
  );
}

// AFTER: Compute locally
function OrderItem({ item, onQuantityChange }) {
  const formattedPrice = formatCurrency(item.price); // ✅ Local variable
  return (
    <div>
      <span>{formattedPrice}</span>
      <QuantitySelector value={item.quantity} onChange={onQuantityChange} />
    </div>
  );
}

// BEFORE: External mutable state during render (23 files)
const featureFlags = window.__FEATURE_FLAGS__;

function FeatureGate({ feature, children }) {
  if (featureFlags[feature]) { // ⛔ External mutable state
    return children;
  }
  return null;
}

// AFTER: Use a React-friendly approach
function FeatureGate({ feature, children }) {
  const flags = useSyncExternalStore(  // ✅ React-aware subscription
    flagStore.subscribe,
    flagStore.getSnapshot
  );
  if (flags[feature]) {
    return children;
  }
  return null;
}

// Step 4: Convert remaining class components
// BEFORE: Class component (8 files)
class CartSummary extends React.Component {
  render() {
    const { items, taxRate } = this.props;
    const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);
    return <div>Total: ${(subtotal * (1 + taxRate)).toFixed(2)}</div>;
  }
}

// AFTER: Function component
function CartSummary({ items, taxRate }) {
  const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);
  return <div>Total: ${(subtotal * (1 + taxRate)).toFixed(2)}</div>;
}

// ═══════════════════════════════════════════════════
// PHASE 3: Enable the compiler gradually (Week 7-10)
// ═══════════════════════════════════════════════════

// Step 5: Enable for the cleanest directories first
// vite.config.js
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', {
            sources: (filename) => {
              // Phase 3a: Only new feature code
              return filename.includes('src/features/checkout-v2/') ||
                     filename.includes('src/components/ui/');
            },
          }],
        ],
      },
    }),
  ],
});

// Step 6: Run the full test suite + E2E tests
// npm run test:unit -- --coverage
// npm run test:e2e
// npm run test:visual-regression

// Step 7: Performance baseline comparison
// Using React DevTools Profiler:
// - Record interaction: "Add item to cart, go to checkout, complete purchase"
// - Compare: render counts, render durations, total blocking time
// - Expected: 20-40% reduction in unnecessary re-renders

// ═══════════════════════════════════════════════════
// PHASE 4: Full rollout (Week 11-14)
// ═══════════════════════════════════════════════════

// Step 8: Expand to entire codebase with opt-out for problem areas
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', {}], // Compile everything
        ],
      },
    }),
  ],
});

// Opt out for components that still have issues:
function LegacyPaymentForm({ config }) {
  'use no memo'; // Third-party payment SDK mutates the DOM directly
  return <div ref={paymentSDK.mount} />;
}

// Step 9: Remove manual memoization
// npx react-codemod remove-unnecessary-memo src/
// Result: 847 of 892 useMemo/useCallback/memo instances removed
// 45 intentionally kept (expensive computations, external API contracts)

// Step 10: Final validation
// - All 2,400 unit tests passing ✅
// - All 180 E2E tests passing ✅
// - Lighthouse performance score: 92 → 96 ✅
// - Bundle size: -2.3KB (removed memo imports) ✅
// - P95 Interaction to Next Paint: 180ms → 120ms ✅

// ═══════════════════════════════════════════════════
// PHASE 5: Ongoing maintenance
// ═══════════════════════════════════════════════════

// .eslintrc.js — Final config
module.exports = {
  plugins: ['react-hooks', 'react-compiler'],
  rules: {
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    'react-compiler/react-compiler': 'error', // Block PRs that break compiler
  },
};

// CI pipeline addition:
// - ESLint with react-compiler rule runs on every PR
// - Performance regression test: flag if render count increases >10%
// - Bundle size check: flag if size increases >5KB

// Team guidelines:
// 1. Do NOT use useMemo/useCallback unless you can justify why (PR review)
// 2. Do NOT use React.memo() — the compiler handles it
// 3. If you see "use no memo" in code, add a comment explaining WHY
// 4. Write pure components — no side effects during render
// 5. Use useSyncExternalStore for external state, not direct reads
```

**Interview-ready summary of the adoption process:**
1. **Assess** — Run the ESLint plugin to quantify violations.
2. **Fix** — Resolve Rules of React violations (prop mutations, external state, class components).
3. **Enable gradually** — Use `sources` filter to compile clean directories first.
4. **Test extensively** — Unit, E2E, visual regression, and performance benchmarks.
5. **Expand** — Enable for the full codebase, `'use no memo'` for exceptions.
6. **Clean up** — Remove manual memoization with the codemod.
7. **Maintain** — ESLint rule in CI prevents regressions.

The entire process takes 10-14 weeks for a large app, with zero downtime and gradual risk reduction. The result is a codebase that is **simpler** (less memoization boilerplate), **faster** (more consistent optimization), and **easier to maintain** (new developers write plain React and get optimal performance automatically).
