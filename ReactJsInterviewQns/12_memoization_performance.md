# Memoization & Performance — React 18 Interview Questions

## Topic Introduction

React's rendering model is built on a simple principle: **when state changes, the component re-renders, and so do all of its descendants**. Every time a parent component's state or props change, React calls the parent's function body again, producing a new virtual DOM tree. It then recursively does the same for every child component in that subtree — regardless of whether the child's own props actually changed. This is React's default behavior and it is intentional: re-rendering is how React keeps the UI in sync with state. The reconciliation algorithm (the "diffier") then compares the new virtual DOM with the previous one and commits only the actual DOM mutations needed. While this diffing step is efficient, the **rendering step** (calling component functions, running hooks, creating JSX objects) can become expensive in large component trees — especially when most of that work produces the exact same output as before.

This is where **memoization** enters the picture. React provides three core memoization primitives: `React.memo` (a higher-order component that skips re-rendering when props haven't changed), `useMemo` (a hook that caches the result of an expensive computation between renders), and `useCallback` (a hook that caches a function reference between renders). All three rely on **referential equality** — they compare previous and next values using `Object.is`. Because JavaScript creates new object/array/function references on every render, passing inline objects or callbacks as props defeats shallow comparison by default. Understanding when and where to apply these tools — and equally importantly, when **not** to — is what separates junior developers who sprinkle `useMemo` everywhere from senior engineers who profile first, memoize strategically, and architect component trees to minimize unnecessary work. React 18's concurrent features (automatic batching, `useTransition`, `useDeferredValue`) add another dimension to performance, and the upcoming **React 19 Compiler (React Forget)** promises to auto-memoize components and hooks, making many manual optimizations obsolete.

```jsx
// Demonstration: Why memoization matters
import { useState, useMemo, useCallback, memo } from 'react';

function Dashboard() {
  const [search, setSearch] = useState('');
  const [theme, setTheme] = useState('light');

  // ❌ Without memoization: recalculated every render (even when only theme changes)
  // const filtered = hugeList.filter(item => item.name.includes(search));

  // ✅ With useMemo: only recalculated when `search` actually changes
  const filtered = useMemo(
    () => hugeList.filter(item => item.name.includes(search)),
    [search]
  );

  // ✅ With useCallback: stable reference prevents <MemoizedChild> re-renders
  const handleSelect = useCallback((id) => {
    console.log('Selected:', id);
  }, []);

  return (
    <div className={theme}>
      <input value={search} onChange={e => setSearch(e.target.value)} />
      <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
        Toggle Theme
      </button>
      {/* MemoizedList only re-renders when `filtered` or `handleSelect` change */}
      <MemoizedList items={filtered} onSelect={handleSelect} />
    </div>
  );
}

const MemoizedList = memo(function ItemList({ items, onSelect }) {
  console.log('ItemList rendered');
  return (
    <ul>
      {items.map(item => (
        <li key={item.id} onClick={() => onSelect(item.id)}>{item.name}</li>
      ))}
    </ul>
  );
});
```

---

## Beginner Level (Q1–Q5)

---

### Q1. How does React re-rendering work — when does a component re-render?

**Answer:**

A React component re-renders in three situations:

1. **Its own state changes** — calling `setState` (or `useState`'s setter, or `useReducer`'s `dispatch`) schedules a re-render of that component.
2. **Its parent re-renders** — when a parent component re-renders, React re-renders *all* of its children by default, even if the child's props haven't changed. This is the most common source of "unnecessary" re-renders.
3. **A context it consumes changes** — if a component calls `useContext(SomeContext)` and the context's value changes, that component re-renders.

A common misconception is that props changing causes re-renders. In reality, the parent re-rendering causes the child to re-render — changed props are a *consequence*, not a cause. This default behavior exists because React cannot cheaply know whether a child's output would differ; it's cheaper to just re-render and diff the virtual DOM.

**Important:** Re-rendering does **not** mean the DOM is updated. React's reconciliation compares the new virtual tree with the old one and only commits actual DOM mutations where differences exist. So a "wasted" re-render (one that produces the same output) costs CPU time to execute the component function but does not touch the DOM.

React 18 also introduced **automatic batching**: multiple state updates inside event handlers, promises, `setTimeout`, and native event handlers are batched into a single re-render, reducing unnecessary renders.

```jsx
import { useState } from 'react';

function Parent() {
  const [count, setCount] = useState(0);
  console.log('Parent rendered');

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Increment: {count}</button>
      {/* Child re-renders every time Parent re-renders, even though its
          props never change — because it receives no props at all! */}
      <Child />
    </div>
  );
}

function Child() {
  console.log('Child rendered'); // logs on EVERY parent re-render
  return <p>I am a child component</p>;
}

// Fix: wrap Child with React.memo to skip re-render when props are unchanged
// const Child = memo(function Child() { ... });
```

**React 18 automatic batching example:**

```jsx
function handleClick() {
  // In React 17, only the first two were batched (inside event handler).
  // In React 18, ALL of these are batched into ONE re-render:
  setCount(c => c + 1);
  setFlag(f => !f);

  // Even inside setTimeout — React 18 batches this too:
  setTimeout(() => {
    setCount(c => c + 1);
    setFlag(f => !f);
    // Only ONE re-render, not two
  }, 1000);
}
```

---

### Q2. What is `React.memo` and when should you use it?

**Answer:**

`React.memo` is a **higher-order component (HOC)** that wraps a functional component and tells React: "Skip re-rendering this component if its props haven't changed." It performs a **shallow comparison** of the previous and next props using `Object.is` for each prop key. If all props are shallowly equal, React reuses the previous render result and skips calling the component function entirely.

**When to use it:**
- A component renders often because its parent re-renders frequently, but the child's own props rarely change.
- The component's render is expensive (large JSX tree, heavy computations).
- The component is a leaf node or subtree root that doesn't need the parent's every update.

**When NOT to use it:**
- The component's props change on almost every render anyway (memo adds overhead with no benefit).
- The component is cheap to render (the comparison cost may exceed the render cost).
- You're passing new object/array/function references as props on every render without `useMemo`/`useCallback` (memo will never bail out).

```jsx
import { memo, useState } from 'react';

// Without memo: re-renders every time Parent re-renders
// With memo: only re-renders when `title` or `count` props actually change
const ExpensiveChart = memo(function ExpensiveChart({ title, count }) {
  console.log('ExpensiveChart rendered');
  // Imagine a heavy D3 or Chart.js rendering here
  return (
    <div>
      <h2>{title}</h2>
      <p>Data points: {count}</p>
      {/* ... expensive chart rendering ... */}
    </div>
  );
});

function Dashboard() {
  const [search, setSearch] = useState('');
  const [chartData] = useState({ title: 'Revenue', count: 1500 });

  return (
    <div>
      {/* Typing in the search box re-renders Dashboard on every keystroke */}
      <input value={search} onChange={e => setSearch(e.target.value)} />

      {/* But ExpensiveChart skips re-rendering because its props haven't changed */}
      <ExpensiveChart title={chartData.title} count={chartData.count} />
    </div>
  );
}
```

**Note on React 19 Compiler:** The React 19 Compiler (React Forget) will auto-memoize components, making manual `React.memo` wrappers unnecessary in many cases. Until then, `React.memo` remains the standard tool for preventing unnecessary child re-renders.

---

### Q3. What is `useMemo` and how does it memoize expensive computations?

**Answer:**

`useMemo` is a React hook that **caches the result** of a computation between renders. It accepts a "create" function and a dependency array. React calls the create function on the initial render and stores the result. On subsequent renders, it compares the current dependencies with the previous ones using `Object.is`. If all dependencies are the same, it returns the cached value without re-executing the function. If any dependency has changed, it re-runs the function, caches the new result, and returns it.

**Syntax:** `const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);`

**Primary use cases:**
1. **Expensive computations** — filtering, sorting, or transforming large datasets.
2. **Referential stability** — ensuring that an object or array passed as a prop to a memoized child maintains the same reference when its contents haven't changed.

```jsx
import { useState, useMemo } from 'react';

function ProductList({ products }) {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('name');

  // ✅ Expensive filtering + sorting only recalculated when products, search, or sortBy change
  const filteredAndSorted = useMemo(() => {
    console.log('Filtering and sorting...');
    const filtered = products.filter(p =>
      p.name.toLowerCase().includes(search.toLowerCase())
    );
    return filtered.sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'price') return a.price - b.price;
      return 0;
    });
  }, [products, search, sortBy]);

  return (
    <div>
      <input
        placeholder="Search products..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />
      <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
        <option value="name">Name</option>
        <option value="price">Price</option>
      </select>
      <ul>
        {filteredAndSorted.map(p => (
          <li key={p.id}>{p.name} — ${p.price}</li>
        ))}
      </ul>
    </div>
  );
}
```

**Key caveat:** `useMemo` is a performance optimization, not a semantic guarantee. React may discard cached values to free memory (e.g., for offscreen components). Write your code so it still works without `useMemo`, then add it for performance.

---

### Q4. What is `useCallback` and how does it prevent child re-renders?

**Answer:**

`useCallback` is a React hook that **caches a function definition** between renders. Every time a component re-renders, any inline functions defined in the function body are re-created as new JavaScript function objects. Even if two functions have identical code, they are different references in memory (`fn1 !== fn2`). This breaks referential equality checks that `React.memo` relies on.

`useCallback(fn, deps)` is essentially syntactic sugar for `useMemo(() => fn, deps)` — it returns the same function reference as long as the dependencies haven't changed.

**When to use it:**
- You're passing a callback as a prop to a child wrapped in `React.memo`.
- You're passing a callback as a dependency of `useEffect`, `useMemo`, or another `useCallback` in a child.

**When NOT to use it:**
- The child is not memoized — caching the function gains nothing.
- The function is only used in the same component (no referential equality concern).

```jsx
import { useState, useCallback, memo } from 'react';

const TodoItem = memo(function TodoItem({ todo, onToggle, onDelete }) {
  console.log(`TodoItem ${todo.id} rendered`);
  return (
    <li>
      <input
        type="checkbox"
        checked={todo.done}
        onChange={() => onToggle(todo.id)}
      />
      <span style={{ textDecoration: todo.done ? 'line-through' : 'none' }}>
        {todo.text}
      </span>
      <button onClick={() => onDelete(todo.id)}>Delete</button>
    </li>
  );
});

function TodoList() {
  const [todos, setTodos] = useState([
    { id: 1, text: 'Learn React', done: false },
    { id: 2, text: 'Learn memoization', done: false },
  ]);

  // ✅ Stable reference: TodoItem (wrapped in memo) won't re-render when
  // other state changes cause TodoList to re-render
  const handleToggle = useCallback((id) => {
    setTodos(prev =>
      prev.map(t => t.id === id ? { ...t, done: !t.done } : t)
    );
  }, []);

  const handleDelete = useCallback((id) => {
    setTodos(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ul>
      {todos.map(todo => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggle={handleToggle}
          onDelete={handleDelete}
        />
      ))}
    </ul>
  );
}
```

**Note:** Both `handleToggle` and `handleDelete` use the **functional updater form** (`setTodos(prev => ...)`) so they never need `todos` in their dependency array. This is a critical pattern — without it, you'd need `[todos]` as a dependency, and the callbacks would change on every state update, defeating the purpose of `useCallback`.

---

### Q5. What is referential equality and why does it matter in React?

**Answer:**

**Referential equality** means two values point to the exact same location in memory. JavaScript compares objects, arrays, and functions by reference, not by their content. Two objects with identical properties are **not** referentially equal if they are different instances:

```jsx
const a = { name: 'React' };
const b = { name: 'React' };

console.log(a === b);       // false — different references
console.log(a === a);       // true  — same reference

const c = a;
console.log(a === c);       // true  — c points to the same object as a
```

This matters enormously in React because:

1. **`React.memo`** uses shallow comparison (`Object.is`) on each prop. If you pass a new object/array/function reference as a prop on every render, `React.memo` will never bail out.
2. **`useEffect`/`useMemo`/`useCallback` dependency arrays** use `Object.is` to compare each dependency. A new reference means the dependency "changed," causing the effect/memo to re-run.
3. **Context** — when the context value is a new object on every render, every consumer re-renders.

```jsx
import { useState, memo, useMemo, useCallback } from 'react';

const UserCard = memo(function UserCard({ user, onEdit }) {
  console.log('UserCard rendered');
  return (
    <div>
      <p>{user.name}</p>
      <button onClick={onEdit}>Edit</button>
    </div>
  );
});

function App() {
  const [count, setCount] = useState(0);

  // ❌ BAD: new object on every render — UserCard always re-renders
  // const user = { name: 'Vignesh' };
  // const handleEdit = () => console.log('edit');

  // ✅ GOOD: stable references — UserCard skips re-render
  const user = useMemo(() => ({ name: 'Vignesh' }), []);
  const handleEdit = useCallback(() => console.log('edit'), []);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <UserCard user={user} onEdit={handleEdit} />
    </div>
  );
}
```

**Primitives are safe:** Strings, numbers, booleans, `null`, and `undefined` are compared by value, so `"hello" === "hello"` is `true`. You never need to memoize primitive props.

---

## Intermediate Level (Q6–Q12)

---

### Q6. When should you NOT memoize? What is premature optimization in React?

**Answer:**

Memoization has a cost: `useMemo` and `useCallback` consume memory to store the cached value and the dependency array, and React must compare dependencies on every render. `React.memo` adds a shallow comparison step before every render. If the component is cheap to render or its props change frequently, memoization adds overhead without saving work.

**Do NOT memoize when:**

1. **The component is trivially cheap** — rendering a few DOM elements with no heavy logic.
2. **Props change on almost every render** — memo's comparison will always fail and you pay the comparison cost on top of the render cost.
3. **You're memoizing primitive values** — `useMemo(() => a + b, [a, b])` is slower than just writing `a + b`.
4. **The function/value isn't passed to a memoized child or used in a dependency array** — there's no consumer that benefits from referential stability.
5. **You haven't profiled first** — optimizing without measurement is guessing.

**The right approach:**
1. Write clean, readable code first.
2. If you notice performance issues, use the **React DevTools Profiler** to identify which components render too often or take too long.
3. Apply memoization surgically to the specific bottleneck.

```jsx
import { useState, useMemo } from 'react';

function App() {
  const [name, setName] = useState('');

  // ❌ PREMATURE: Memoizing a simple string concatenation is slower than just doing it
  const greeting = useMemo(() => `Hello, ${name}!`, [name]);

  // ❌ PREMATURE: Memoizing a tiny inline style object when no memo'd child uses it
  const style = useMemo(() => ({ color: 'blue', fontSize: 16 }), []);

  // ✅ JUSTIFIED: Filtering 50,000 rows on every keystroke is genuinely expensive
  const [items] = useState(() => generateLargeDataset(50000));
  const filtered = useMemo(
    () => items.filter(item => item.name.toLowerCase().includes(name.toLowerCase())),
    [items, name]
  );

  return (
    <div>
      <input value={name} onChange={e => setName(e.target.value)} />
      <p>{greeting}</p>
      <ul>
        {filtered.slice(0, 100).map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

**React 19 Compiler note:** The React 19 Compiler (React Forget) will auto-memoize at the compiler level, making this entire debate less relevant. The compiler statically analyzes your code and inserts the equivalent of `useMemo`/`useCallback` wherever beneficial — without developer intervention or risk of premature optimization.

---

### Q7. How do you use the React DevTools Profiler to identify unnecessary re-renders?

**Answer:**

The **React DevTools Profiler** is the primary tool for diagnosing rendering performance. It records a timeline of component renders and shows you exactly which components rendered, why they rendered, and how long each render took.

**Steps to profile:**

1. Install the React DevTools browser extension (Chrome/Firefox).
2. Open DevTools → **Profiler** tab.
3. Click **"Record"**, interact with the app, then click **"Stop"**.
4. Analyze the **flamegraph** or **ranked** view.

**Key information the Profiler provides:**
- **Why did this render?** — Enable "Record why each component rendered" in Profiler settings. It shows: "Props changed", "State changed", "Hooks changed", or "Parent rendered."
- **Render duration** — how long each component took to render.
- **Commit information** — how many renders occurred and total commit time.
- **Gray components** — components that did NOT render (skipped via `React.memo`).

**Highlight Updates (visual):** In React DevTools settings, enable "Highlight updates when components render." This draws colored borders around components as they render — green for infrequent, yellow/red for frequent updates.

```jsx
// Production scenario: Diagnosing a slow search filter in a data table

import { useState, useMemo, memo, useCallback } from 'react';

// STEP 1: Profile reveals TableRow renders 5000 times on every keystroke
function DataTable({ rows }) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(
    () => rows.filter(r => r.name.includes(search)),
    [rows, search]
  );

  // STEP 2: Profile shows handleClick creates new ref each render
  const handleClick = useCallback((id) => {
    console.log('Row clicked:', id);
  }, []);

  return (
    <div>
      <input value={search} onChange={e => setSearch(e.target.value)} />
      {filtered.map(row => (
        <TableRow key={row.id} row={row} onClick={handleClick} />
      ))}
    </div>
  );
}

// STEP 3: Wrap in memo — Profiler now shows gray (skipped) for unchanged rows
const TableRow = memo(function TableRow({ row, onClick }) {
  return (
    <tr onClick={() => onClick(row.id)}>
      <td>{row.name}</td>
      <td>{row.email}</td>
    </tr>
  );
});

// After optimization: Profiler shows only changed rows re-render,
// render time drops from 200ms to 15ms per keystroke.
```

**Tip:** In production builds, component names are minified. Use the `displayName` property or the Profiler's "Components" tab with source maps for accurate component identification.

---

### Q8. How do you use `React.memo` with a custom comparison function?

**Answer:**

By default, `React.memo` performs a **shallow comparison** of all props using `Object.is`. You can override this by passing a custom comparison function as the second argument: `memo(Component, arePropsEqual)`.

The comparison function receives `(prevProps, nextProps)` and should return `true` if the component should **skip** re-rendering (props are considered equal), or `false` if it should re-render.

**Use cases for custom comparison:**
- You want to compare only a subset of props (ignoring frequently-changing but irrelevant ones).
- You need deep comparison for nested objects.
- You want to compare derived values rather than the raw props.

**Warning:** Custom comparison functions can introduce subtle bugs if you forget to compare a prop that affects the output. It also bypasses React's default behavior, so use it sparingly.

```jsx
import { memo } from 'react';

// Scenario: A chat message component that receives a `message` object
// and an `onReply` callback. The `onReply` changes on every render
// (parent doesn't use useCallback), but the message content rarely changes.

const ChatMessage = memo(
  function ChatMessage({ message, onReply }) {
    console.log(`Rendering message: ${message.id}`);
    return (
      <div className="chat-message">
        <strong>{message.author}</strong>
        <p>{message.text}</p>
        <span className="timestamp">{message.timestamp}</span>
        <button onClick={() => onReply(message.id)}>Reply</button>
      </div>
    );
  },
  // Custom comparison: only re-render if the message itself changed
  (prevProps, nextProps) => {
    // Return true = skip re-render, false = re-render
    return (
      prevProps.message.id === nextProps.message.id &&
      prevProps.message.text === nextProps.message.text &&
      prevProps.message.timestamp === nextProps.message.timestamp
    );
    // We intentionally skip comparing `onReply` because the
    // latest closure is captured via ref or it doesn't matter
    // for render output.
  }
);

// Usage in a chat app
function ChatThread({ messages }) {
  // Even without useCallback on handleReply, ChatMessage won't
  // re-render because our custom comparison ignores onReply
  const handleReply = (messageId) => {
    console.log('Replying to:', messageId);
  };

  return (
    <div>
      {messages.map(msg => (
        <ChatMessage key={msg.id} message={msg} onReply={handleReply} />
      ))}
    </div>
  );
}
```

**Caution:** If `onReply`'s behavior depends on state that changes, skipping its comparison could cause stale closure bugs. Always verify that ignored props don't affect visible output or behavior.

---

### Q9. How do you use `useMemo` effectively for expensive list filtering and sorting?

**Answer:**

In production applications, you often have large datasets (thousands of items) that need to be filtered, sorted, and paginated based on user input. Without `useMemo`, every unrelated state change (e.g., toggling a modal, changing a theme) would re-run the entire filtering pipeline.

**Key principles:**
1. Only memoize when the dataset is large enough that filtering/sorting is measurable (profile first!).
2. Include all dependencies that affect the computation in the dependency array.
3. Consider debouncing the search input to reduce how often the memoized computation re-runs.

```jsx
import { useState, useMemo, useDeferredValue } from 'react';

function EmployeeDirectory({ employees }) {
  // employees = array of ~10,000 employee objects
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('all');
  const [sortField, setSortField] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  // React 18: useDeferredValue lets React show stale results while
  // the expensive filter runs in a lower-priority render
  const deferredSearch = useDeferredValue(search);

  const processedEmployees = useMemo(() => {
    console.time('filter-sort');

    // Step 1: Filter
    let result = employees;
    if (department !== 'all') {
      result = result.filter(e => e.department === department);
    }
    if (deferredSearch) {
      const q = deferredSearch.toLowerCase();
      result = result.filter(e =>
        e.name.toLowerCase().includes(q) ||
        e.email.toLowerCase().includes(q)
      );
    }

    // Step 2: Sort
    result = [...result].sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      const cmp = typeof valA === 'string'
        ? valA.localeCompare(valB)
        : valA - valB;
      return sortDir === 'asc' ? cmp : -cmp;
    });

    console.timeEnd('filter-sort');
    return result;
  }, [employees, deferredSearch, department, sortField, sortDir]);

  return (
    <div>
      <input
        placeholder="Search employees..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />
      <select value={department} onChange={e => setDepartment(e.target.value)}>
        <option value="all">All Departments</option>
        <option value="engineering">Engineering</option>
        <option value="design">Design</option>
        <option value="marketing">Marketing</option>
      </select>
      <button onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}>
        Sort: {sortDir === 'asc' ? '↑' : '↓'}
      </button>

      {/* Show visual feedback when deferred value is stale */}
      <div style={{ opacity: search !== deferredSearch ? 0.6 : 1 }}>
        <p>{processedEmployees.length} results</p>
        <ul>
          {processedEmployees.slice(0, 50).map(e => (
            <li key={e.id}>{e.name} — {e.department}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

**Why `useDeferredValue` here?** While `useMemo` prevents redundant computation when dependencies haven't changed, `useDeferredValue` lets React keep the UI responsive during rapid typing by deferring the expensive filter to a lower-priority update. The input stays snappy, and the list updates slightly behind.

---

### Q10. How do you use `useCallback` with event handlers passed to child lists?

**Answer:**

When rendering a list of items where each item receives a callback (like `onClick`, `onDelete`, `onSelect`), creating a new function for each item inside `.map()` means every child gets a new prop reference on every render. Combined with `React.memo` on the list items, `useCallback` ensures the handler reference stays stable.

**The challenge:** Often the callback needs the item's `id`, which tempts you to write `onClick={() => handleClick(item.id)}` — creating a new function per item per render. The solution is to pass the `id` as a prop and let the child call back with it.

```jsx
import { useState, useCallback, memo } from 'react';

// ✅ Pattern: Child receives a stable callback + its own id
const OrderRow = memo(function OrderRow({ order, onCancel, onView }) {
  console.log(`OrderRow ${order.id} rendered`);
  return (
    <tr>
      <td>{order.id}</td>
      <td>{order.product}</td>
      <td>${order.total.toFixed(2)}</td>
      <td>{order.status}</td>
      <td>
        {/* Child calls the stable callback with its own id */}
        <button onClick={() => onView(order.id)}>View</button>
        {order.status === 'pending' && (
          <button onClick={() => onCancel(order.id)}>Cancel</button>
        )}
      </td>
    </tr>
  );
});

function OrdersTable() {
  const [orders, setOrders] = useState(initialOrders); // 1000+ orders
  const [selectedId, setSelectedId] = useState(null);

  // ✅ Stable references — won't cause OrderRow re-renders
  const handleCancel = useCallback((orderId) => {
    setOrders(prev =>
      prev.map(o => o.id === orderId ? { ...o, status: 'cancelled' } : o)
    );
  }, []);

  const handleView = useCallback((orderId) => {
    setSelectedId(orderId);
  }, []);

  return (
    <div>
      {selectedId && <OrderDetail orderId={selectedId} />}
      <table>
        <thead>
          <tr><th>ID</th><th>Product</th><th>Total</th><th>Status</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {orders.map(order => (
            <OrderRow
              key={order.id}
              order={order}
              onCancel={handleCancel}
              onView={handleView}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**Why this works:** `handleCancel` and `handleView` use functional updaters or only reference setters (which are stable), so their dependency arrays are empty `[]`. Every `OrderRow` receives the exact same function references across renders. When one order is cancelled, only that specific `OrderRow` re-renders (its `order` prop changed) — the other 999 rows are skipped by `React.memo`.

---

### Q11. What are common mistakes with `useMemo` and `useCallback`?

**Answer:**

Even experienced developers make these mistakes with memoization hooks:

**Mistake 1: Missing or wrong dependencies**

```jsx
// ❌ Missing `discount` in deps — stale closure, uses the initial discount forever
const total = useMemo(() => {
  return items.reduce((sum, item) => sum + item.price, 0) * (1 - discount);
}, [items]); // Bug: should be [items, discount]

// ✅ Correct
const total = useMemo(() => {
  return items.reduce((sum, item) => sum + item.price, 0) * (1 - discount);
}, [items, discount]);
```

**Mistake 2: Memoizing primitive values**

```jsx
// ❌ Pointless: `a + b` is a primitive — it's always referentially equal if the value is the same
const sum = useMemo(() => a + b, [a, b]);

// ✅ Just compute it directly
const sum = a + b;
```

**Mistake 3: Using `useCallback` without `React.memo` on the child**

```jsx
// ❌ useCallback is useless here — ChildComponent is not wrapped in memo
const handleClick = useCallback(() => { doSomething(); }, []);
return <ChildComponent onClick={handleClick} />;
// ChildComponent re-renders every time Parent renders regardless

// ✅ Either memo the child, or skip useCallback
const ChildComponent = memo(function ChildComponent({ onClick }) { ... });
```

**Mistake 4: Object/array in dependency array that's recreated every render**

```jsx
function App({ userId }) {
  // ❌ `options` is a new object every render, so useMemo re-runs every time
  const options = { includeArchived: true, limit: 50 };
  const data = useMemo(() => processData(userId, options), [userId, options]);

  // ✅ Either memoize `options` too, or inline the values
  const data = useMemo(
    () => processData(userId, { includeArchived: true, limit: 50 }),
    [userId]
  );
}
```

**Mistake 5: Forgetting the functional updater pattern with `useCallback`**

```jsx
// ❌ `count` in deps means the callback changes on every count update
const increment = useCallback(() => {
  setCount(count + 1);
}, [count]); // defeats the purpose of useCallback

// ✅ Functional updater — no dependency on `count`
const increment = useCallback(() => {
  setCount(prev => prev + 1);
}, []); // stable forever
```

**Mistake 6: Wrapping everything in `useMemo`/`useCallback` "just in case"**

```jsx
// ❌ Over-memoization: adds complexity and overhead with no measurable benefit
const title = useMemo(() => 'Dashboard', []);
const handleMouseMove = useCallback((e) => { /* ... */ }, []);
const className = useMemo(() => `container ${theme}`, [theme]);

// ✅ Just write it naturally — memoize only after profiling shows a need
const title = 'Dashboard';
const className = `container ${theme}`;
```

**Tip:** Use the `eslint-plugin-react-hooks` rule `exhaustive-deps` — it catches missing dependencies automatically.

---

### Q12. How do you prevent unnecessary re-renders caused by React Context?

**Answer:**

When a context's value changes, **every component** that calls `useContext(ThatContext)` re-renders — even if it only uses a small slice of the context that didn't change. This is a major source of performance issues in large apps.

**Strategies to prevent context-triggered re-renders:**

**Strategy 1: Split contexts by rate of change**

```jsx
// ❌ BAD: One big context — theme changes cause re-renders in components
// that only need auth data
const AppContext = createContext();

function AppProvider({ children }) {
  const [theme, setTheme] = useState('light');
  const [user, setUser] = useState(null);

  // New object every render — every consumer re-renders
  return (
    <AppContext.Provider value={{ theme, setTheme, user, setUser }}>
      {children}
    </AppContext.Provider>
  );
}

// ✅ GOOD: Split into separate contexts
const ThemeContext = createContext();
const AuthContext = createContext();

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  const value = useMemo(() => ({ theme, setTheme }), [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const value = useMemo(() => ({ user, setUser }), [user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

**Strategy 2: Memoize the context value**

```jsx
function CartProvider({ children }) {
  const [items, setItems] = useState([]);

  // ✅ Memoize so the object reference is stable when `items` hasn't changed
  const value = useMemo(() => ({
    items,
    addItem: (item) => setItems(prev => [...prev, item]),
    removeItem: (id) => setItems(prev => prev.filter(i => i.id !== id)),
    total: items.reduce((sum, i) => sum + i.price, 0),
  }), [items]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
```

**Strategy 3: Separate state and dispatch contexts**

```jsx
const StateContext = createContext();
const DispatchContext = createContext();

function TodoProvider({ children }) {
  const [todos, dispatch] = useReducer(todoReducer, []);

  return (
    <DispatchContext.Provider value={dispatch}>
      {/* dispatch is stable (from useReducer), so DispatchContext never triggers re-renders */}
      <StateContext.Provider value={todos}>
        {children}
      </StateContext.Provider>
    </DispatchContext.Provider>
  );
}

// Components that only dispatch actions (e.g., AddTodoForm) subscribe
// only to DispatchContext — they never re-render when todos change
function AddTodoForm() {
  const dispatch = useContext(DispatchContext); // stable, never re-renders
  const [text, setText] = useState('');

  return (
    <form onSubmit={e => {
      e.preventDefault();
      dispatch({ type: 'ADD', text });
      setText('');
    }}>
      <input value={text} onChange={e => setText(e.target.value)} />
      <button type="submit">Add</button>
    </form>
  );
}
```

**Strategy 4: Wrap consumers in `React.memo`**

```jsx
// If splitting context is impractical, memoize the consumer component
const Sidebar = memo(function Sidebar() {
  const { theme } = useContext(AppContext);
  return <aside className={theme}>...</aside>;
});
// Sidebar only re-renders if its props change (none) OR its context changes.
// Unfortunately, memo doesn't help with context — it still re-renders.
// This only works if the component ALSO receives changing props from a parent.
```

**Best practice:** Combine Strategy 1 (split contexts) and Strategy 2 (memoize values) for optimal performance. For state-heavy apps, consider external state managers like Zustand or Jotai which provide fine-grained subscriptions out of the box.

---

## Advanced Level (Q13–Q20)

---

### Q13. Explain the "children as props" optimization pattern for avoiding re-renders without memo.

**Answer:**

One of the most elegant and underutilized performance patterns in React is **lifting content up as children**. When you pass JSX as `children` (or any prop), the JSX elements are created in the *parent's* scope. If the parent doesn't re-render, those JSX elements retain their original references, and React can skip re-rendering them — without any `memo`, `useMemo`, or `useCallback`.

**The principle:** React elements (JSX) are objects. If the reference to a React element hasn't changed between renders, React skips reconciliation for that entire subtree.

```jsx
// ❌ PROBLEM: Moving the mouse re-renders App, which re-renders ExpensiveTree
function App() {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  return (
    <div onMouseMove={e => setPosition({ x: e.clientX, y: e.clientY })}>
      <p>Mouse: {position.x}, {position.y}</p>
      {/* ExpensiveTree re-renders on every mouse move! */}
      <ExpensiveTree />
    </div>
  );
}

function ExpensiveTree() {
  console.log('ExpensiveTree rendered'); // logs on every mouse move
  return <div>{/* ...thousands of nodes... */}</div>;
}
```

```jsx
// ✅ SOLUTION 1: Extract the stateful part into its own component
function App() {
  return (
    <MouseTracker>
      {/* ExpensiveTree JSX is created in App's scope.
          App never re-renders, so this JSX reference is stable.
          MouseTracker re-renders, but its `children` prop hasn't changed. */}
      <ExpensiveTree />
    </MouseTracker>
  );
}

function MouseTracker({ children }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  return (
    <div onMouseMove={e => setPosition({ x: e.clientX, y: e.clientY })}>
      <p>Mouse: {position.x}, {position.y}</p>
      {children}
    </div>
  );
}

function ExpensiveTree() {
  console.log('ExpensiveTree rendered'); // only logs ONCE on mount
  return <div>{/* ...thousands of nodes... */}</div>;
}
```

```jsx
// ✅ SOLUTION 2: Pass JSX as a named prop (same principle)
function App() {
  return (
    <Layout
      header={<Header />}
      sidebar={<Sidebar />}
      content={<ExpensiveContent />}
    />
  );
}

function Layout({ header, sidebar, content }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  // Toggling collapse re-renders Layout, but header, sidebar, and content
  // are stable references (created in App which doesn't re-render)
  return (
    <div className={isCollapsed ? 'collapsed' : 'expanded'}>
      {header}
      <button onClick={() => setIsCollapsed(c => !c)}>Toggle</button>
      <div className="layout-body">
        {sidebar}
        {content}
      </div>
    </div>
  );
}
```

**Why this works:** In the fixed version, `<ExpensiveTree />` is created in `App`'s render scope. `App` has no state and never re-renders. So the JSX element reference stays the same. When `MouseTracker` re-renders (due to mouse move), React sees that `children` is the same reference and skips the entire subtree — no `memo` needed.

**This pattern is zero-cost:** No extra memory, no dependency arrays, no comparison functions. It leverages React's own reconciliation optimization.

---

### Q14. How do you implement virtualization with react-window or react-virtuoso for large lists?

**Answer:**

**Virtualization** (or "windowing") is the technique of rendering only the items visible in the viewport plus a small overscan buffer, rather than rendering the entire list. For a list of 100,000 items, instead of mounting 100,000 DOM nodes, you mount ~20-50. This dramatically reduces initial render time, memory usage, and scroll jank.

**Popular libraries:**
- **`react-window`** — lightweight (~6KB), Dan Abramov recommended, by Brian Vaughn (React core team).
- **`react-virtuoso`** — feature-rich, auto-sizing, grouped lists, table support.

**react-window example:**

```jsx
import { FixedSizeList as List } from 'react-window';
import { memo } from 'react';

// Each row component receives index and style (positioning) from react-window
const Row = memo(function Row({ index, style, data }) {
  const item = data[index];
  return (
    <div style={style} className={index % 2 ? 'row-odd' : 'row-even'}>
      <span>{item.name}</span>
      <span>{item.email}</span>
      <span>${item.revenue.toLocaleString()}</span>
    </div>
  );
});

function VirtualizedTable({ items }) {
  // items = array of 100,000 rows

  return (
    <List
      height={600}          // viewport height in px
      width="100%"
      itemCount={items.length}
      itemSize={40}          // row height in px (fixed)
      itemData={items}       // passed as `data` prop to Row
      overscanCount={10}     // render 10 extra rows above/below viewport
    >
      {Row}
    </List>
  );
}
```

**react-virtuoso example (variable height + grouped):**

```jsx
import { GroupedVirtuoso } from 'react-virtuoso';

function GroupedEmployeeList({ employees }) {
  // Group by department
  const departments = [...new Set(employees.map(e => e.department))];
  const groupCounts = departments.map(
    dept => employees.filter(e => e.department === dept).length
  );

  const flatEmployees = departments.flatMap(
    dept => employees.filter(e => e.department === dept)
  );

  return (
    <GroupedVirtuoso
      style={{ height: '80vh' }}
      groupCounts={groupCounts}
      groupContent={index => (
        <div style={{
          background: '#f0f0f0',
          padding: '8px 16px',
          fontWeight: 'bold',
          position: 'sticky',
          top: 0
        }}>
          {departments[index]} ({groupCounts[index]})
        </div>
      )}
      itemContent={index => {
        const employee = flatEmployees[index];
        return (
          <div style={{ padding: '8px 16px', borderBottom: '1px solid #eee' }}>
            <strong>{employee.name}</strong> — {employee.role}
            <br />
            <small>{employee.email}</small>
          </div>
        );
      }}
    />
  );
}
```

**When to virtualize:**
- Lists with **500+ items** that cause noticeable scroll lag.
- Tables with thousands of rows (analytics dashboards, admin panels, log viewers).
- Infinite scroll feeds.

**When NOT to virtualize:**
- Small lists (< 100 items) — the library overhead isn't worth it.
- SEO-critical content that needs to be in the DOM for crawlers (use server rendering instead).
- When items have complex focus/keyboard navigation (virtualization can break accessibility if not handled carefully).

---

### Q15. How do you implement code splitting and lazy loading for performance in React?

**Answer:**

**Code splitting** breaks your JavaScript bundle into smaller chunks that are loaded on demand, reducing the initial bundle size and improving Time to Interactive (TTI). React provides `React.lazy` and `Suspense` for component-level code splitting.

**How it works:**
1. `React.lazy(() => import('./HeavyComponent'))` creates a lazy component.
2. The dynamic `import()` tells the bundler (Webpack/Vite) to split this module into a separate chunk.
3. The chunk is fetched over the network only when the component is first rendered.
4. `Suspense` shows a fallback UI while the chunk is loading.

```jsx
import { lazy, Suspense, useState } from 'react';

// These components are split into separate chunks — not included in the main bundle
const AdminDashboard = lazy(() => import('./AdminDashboard'));
const Analytics = lazy(() => import('./Analytics'));
const Settings = lazy(() => import('./Settings'));

// Named export support (React.lazy requires default exports by default)
const UserProfile = lazy(() =>
  import('./UserProfile').then(module => ({ default: module.UserProfile }))
);

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div>
      <nav>
        <button onClick={() => setActiveTab('dashboard')}>Dashboard</button>
        <button onClick={() => setActiveTab('analytics')}>Analytics</button>
        <button onClick={() => setActiveTab('settings')}>Settings</button>
      </nav>

      {/* Suspense provides loading fallback for any lazy component below it */}
      <Suspense fallback={<LoadingSpinner />}>
        {activeTab === 'dashboard' && <AdminDashboard />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'settings' && <Settings />}
      </Suspense>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="spinner-container">
      <div className="spinner" />
      <p>Loading...</p>
    </div>
  );
}
```

**Route-level splitting (with React Router):**

```jsx
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const Home = lazy(() => import('./pages/Home'));
const Products = lazy(() => import('./pages/Products'));
const Checkout = lazy(() => import('./pages/Checkout'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageSkeleton />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/checkout" element={<Checkout />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

**Prefetching for better UX:**

```jsx
// Prefetch on hover — load the chunk before the user clicks
function NavLink({ to, loadComponent, children }) {
  return (
    <Link
      to={to}
      onMouseEnter={() => loadComponent()} // trigger chunk download
      onFocus={() => loadComponent()}
    >
      {children}
    </Link>
  );
}

// Create a prefetchable lazy component
function lazyWithPreload(factory) {
  const Component = lazy(factory);
  Component.preload = factory;
  return Component;
}

const Settings = lazyWithPreload(() => import('./pages/Settings'));

// Usage: <NavLink to="/settings" loadComponent={Settings.preload}>Settings</NavLink>
```

**Production tip:** Analyze your bundle with `webpack-bundle-analyzer` or `vite-plugin-visualizer` to identify the largest modules and split them first. Common candidates: charting libraries (Recharts, Chart.js), rich text editors (Draft.js, TipTap), PDF viewers, date libraries (Moment.js → use date-fns instead).

---

### Q16. How do you optimize Web Vitals (LCP, FID, CLS) in React applications?

**Answer:**

Google's **Core Web Vitals** measure real user experience and affect search rankings. The three metrics are:

- **LCP (Largest Contentful Paint):** Time until the largest visible element renders. Target: < 2.5s.
- **FID (First Input Delay):** Time from first user interaction to browser response. Target: < 100ms. (Being replaced by **INP — Interaction to Next Paint** in 2024+.)
- **CLS (Cumulative Layout Shift):** Visual stability — how much content shifts during load. Target: < 0.1.

**Optimizing LCP in React:**

```jsx
// 1. Preload critical resources in your HTML head
// <link rel="preload" href="/hero-image.webp" as="image" />
// <link rel="preload" href="/fonts/inter.woff2" as="font" crossorigin />

// 2. Server-Side Rendering (SSR) or Static Site Generation (SSG)
// Use Next.js for automatic SSR — React SPA has blank HTML until JS loads
// SSR sends fully-rendered HTML, dramatically improving LCP

// 3. Avoid lazy-loading above-the-fold content
// ❌ Don't lazy-load the hero section
const Hero = lazy(() => import('./Hero')); // delays LCP!

// ✅ Include critical components in the main bundle
import Hero from './Hero'; // renders immediately with SSR

// 4. Optimize images — use next/image or responsive images
function HeroSection() {
  return (
    <section>
      <img
        src="/hero.webp"
        srcSet="/hero-400.webp 400w, /hero-800.webp 800w, /hero-1200.webp 1200w"
        sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
        alt="Hero"
        width={1200}
        height={600}
        fetchPriority="high"      // tell browser this is the LCP element
        decoding="async"
      />
    </section>
  );
}
```

**Optimizing FID/INP:**

```jsx
import { useTransition, useDeferredValue, useState } from 'react';

function SearchableList({ items }) {
  const [query, setQuery] = useState('');
  const [isPending, startTransition] = useTransition();

  const handleSearch = (e) => {
    const value = e.target.value;
    // Urgent update: input stays responsive
    setQuery(value);

    // Non-urgent update: filter can be interrupted
    startTransition(() => {
      setFilterQuery(value);
    });
  };

  return (
    <div>
      <input value={query} onChange={handleSearch} />
      {isPending && <span>Filtering...</span>}
      <FilteredResults query={filterQuery} items={items} />
    </div>
  );
}

// Also: break up long tasks with scheduling
function processLargeDataset(data) {
  // ❌ Blocks main thread for 500ms — causes poor INP
  // return data.map(item => expensiveTransform(item));

  // ✅ Break into chunks using scheduler or requestIdleCallback
  const CHUNK_SIZE = 1000;
  let processed = [];

  function processChunk(startIndex) {
    const end = Math.min(startIndex + CHUNK_SIZE, data.length);
    for (let i = startIndex; i < end; i++) {
      processed.push(expensiveTransform(data[i]));
    }
    if (end < data.length) {
      requestIdleCallback(() => processChunk(end));
    }
  }

  processChunk(0);
}
```

**Optimizing CLS:**

```jsx
// 1. Always set explicit dimensions on images and videos
// ❌ No dimensions — image loads and pushes content down
<img src="/photo.jpg" alt="Photo" />

// ✅ Explicit dimensions — browser reserves space before image loads
<img src="/photo.jpg" alt="Photo" width={800} height={400} />

// 2. Use CSS aspect-ratio for responsive containers
function VideoEmbed({ src }) {
  return (
    <div style={{ aspectRatio: '16 / 9', width: '100%', background: '#000' }}>
      <iframe src={src} style={{ width: '100%', height: '100%' }} />
    </div>
  );
}

// 3. Reserve space for dynamic content (ads, lazy-loaded sections)
function AdSlot() {
  return (
    <div style={{ minHeight: 250, width: 300, background: '#f5f5f5' }}>
      {/* Ad loads here without causing layout shift */}
    </div>
  );
}

// 4. Avoid inserting content above existing content
// ❌ Notification banner pushes everything down
// ✅ Use position: fixed/sticky, or reserve space upfront
```

**Measuring Web Vitals in React:**

```jsx
// Using the web-vitals library
import { onLCP, onFID, onCLS, onINP } from 'web-vitals';

function reportWebVitals(metric) {
  // Send to your analytics endpoint
  fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify({
      name: metric.name,
      value: metric.value,
      rating: metric.rating, // 'good', 'needs-improvement', 'poor'
      navigationType: metric.navigationType,
    }),
  });
}

onLCP(reportWebVitals);
onFID(reportWebVitals);
onCLS(reportWebVitals);
onINP(reportWebVitals);
```

---

### Q17. What is the React 19 Compiler (React Forget) and how does it change memoization?

**Answer:**

The **React 19 Compiler** (previously known as "React Forget") is a build-time compiler that automatically memoizes React components and hooks. It analyzes your source code at compile time and inserts the equivalent of `useMemo`, `useCallback`, and `React.memo` wherever it determines they would be beneficial — without you writing a single memoization hook.

**The problem it solves:** Manual memoization is error-prone (wrong deps, missing deps, premature optimization), verbose, and a frequent source of bugs. Developers either under-memoize (causing performance issues) or over-memoize (adding complexity). The compiler eliminates this entire category of decisions.

**How it works:**

1. The compiler runs at **build time** (as a Babel/SWC plugin).
2. It performs **static analysis** of your component functions.
3. It tracks which values depend on which inputs (reactive values).
4. It automatically caches values and functions that don't need to change.
5. The output is equivalent to hand-optimized code with `useMemo`/`useCallback`.

```jsx
// What you write (no manual memoization):
function ProductPage({ productId }) {
  const [quantity, setQuantity] = useState(1);

  const product = useProduct(productId);
  const total = product.price * quantity;

  const handleAddToCart = () => {
    addToCart(productId, quantity);
  };

  return (
    <div>
      <ProductDetails product={product} />
      <p>Total: ${total}</p>
      <QuantitySelector value={quantity} onChange={setQuantity} />
      <AddToCartButton onClick={handleAddToCart} />
    </div>
  );
}

// What the compiler outputs (conceptually):
function ProductPage({ productId }) {
  const [quantity, setQuantity] = useState(1);

  const product = useProduct(productId);

  // Compiler auto-memoizes: only recalculates when product.price or quantity changes
  const total = _useMemo(() => product.price * quantity, [product.price, quantity]);

  // Compiler auto-memoizes: stable reference when productId and quantity haven't changed
  const handleAddToCart = _useCallback(() => {
    addToCart(productId, quantity);
  }, [productId, quantity]);

  // Compiler auto-memoizes the JSX: ProductDetails only re-renders when product changes
  // AddToCartButton only re-renders when handleAddToCart changes
  return (
    <div>
      <ProductDetails product={product} />
      <p>Total: ${total}</p>
      <QuantitySelector value={quantity} onChange={setQuantity} />
      <AddToCartButton onClick={handleAddToCart} />
    </div>
  );
}
```

**What this means for existing code:**

1. **You can remove manual `useMemo`/`useCallback`/`React.memo`** — the compiler handles it better because it has full visibility of the component's data flow.
2. **Existing memoization still works** — the compiler respects and works alongside manual memos.
3. **No code changes required** — it's a build plugin, not a code migration.
4. **The "Rules of React" matter more** — the compiler relies on components being pure functions and hooks following the rules. Mutating props, reading from external mutable variables without hooks, and other violations will cause the compiler to produce incorrect output or bail out.

**Current status (2025–2026):** The React Compiler has shipped as experimental in React 19. Meta has been using it in production at Instagram. Community adoption is growing as the API stabilizes.

```jsx
// The Rules of React that the compiler enforces:
// 1. Components must be pure (same inputs → same output)
// 2. Don't mutate props, state, or values during render
// 3. Follow the Rules of Hooks

// ❌ This breaks the compiler — mutating during render
function BadComponent({ items }) {
  items.sort(); // Mutating a prop! Compiler assumes props are immutable.
  return <List items={items} />;
}

// ✅ Compiler-friendly
function GoodComponent({ items }) {
  const sorted = [...items].sort(); // New array, no mutation
  return <List items={sorted} />;
}
```

**Should you stop writing `useMemo`/`useCallback` today?**
If you're on React 19 with the compiler enabled, you can gradually remove manual memoization. If you're still on React 18, continue using manual memoization where profiling shows it's needed. The compiler will make the transition seamless.

---

### Q18. What are image and asset optimization strategies for React applications?

**Answer:**

Images are typically the largest assets on a web page and the primary driver of slow LCP. A comprehensive image optimization strategy in React combines format selection, responsive sizing, lazy loading, and CDN delivery.

**Strategy 1: Modern image formats**

```jsx
// Use WebP/AVIF with fallback — 30-50% smaller than JPEG/PNG
function OptimizedImage({ src, alt, width, height }) {
  const avifSrc = src.replace(/\.(jpg|png)$/, '.avif');
  const webpSrc = src.replace(/\.(jpg|png)$/, '.webp');

  return (
    <picture>
      <source srcSet={avifSrc} type="image/avif" />
      <source srcSet={webpSrc} type="image/webp" />
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading="lazy"
        decoding="async"
      />
    </picture>
  );
}
```

**Strategy 2: Responsive images with srcSet**

```jsx
function ResponsiveHero() {
  return (
    <img
      srcSet="
        /hero-400.webp 400w,
        /hero-800.webp 800w,
        /hero-1200.webp 1200w,
        /hero-1600.webp 1600w
      "
      sizes="(max-width: 600px) 100vw, (max-width: 1200px) 80vw, 1200px"
      src="/hero-1200.webp"
      alt="Dashboard hero"
      width={1200}
      height={600}
      fetchPriority="high" // Mark as LCP element
    />
  );
}
```

**Strategy 3: Lazy loading images with Intersection Observer**

```jsx
import { useState, useEffect, useRef } from 'react';

function LazyImage({ src, alt, width, height, placeholder }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '200px' } // start loading 200px before viewport
    );

    if (imgRef.current) observer.observe(imgRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={imgRef}
      style={{
        width,
        height,
        backgroundColor: '#f0f0f0',
        overflow: 'hidden',
      }}
    >
      {isInView && (
        <img
          src={src}
          alt={alt}
          width={width}
          height={height}
          onLoad={() => setIsLoaded(true)}
          style={{
            opacity: isLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease',
          }}
        />
      )}
      {!isLoaded && placeholder && (
        <img
          src={placeholder} // tiny blurred placeholder (LQIP)
          alt=""
          style={{ width: '100%', height: '100%', filter: 'blur(20px)' }}
        />
      )}
    </div>
  );
}
```

**Strategy 4: Next.js Image component (production-grade)**

```jsx
import Image from 'next/image';

// Next.js automatically:
// - Resizes images at build/request time
// - Converts to WebP/AVIF
// - Lazy loads by default
// - Prevents CLS with required width/height
// - Serves from built-in image CDN
function ProductCard({ product }) {
  return (
    <div>
      <Image
        src={product.imageUrl}
        alt={product.name}
        width={400}
        height={300}
        sizes="(max-width: 768px) 100vw, 400px"
        placeholder="blur"
        blurDataURL={product.blurHash}
        priority={false} // set true for above-the-fold images
      />
      <h3>{product.name}</h3>
    </div>
  );
}
```

**Strategy 5: SVG optimization and icon strategies**

```jsx
// Use SVG sprites or inline SVGs for icons — avoid icon fonts
// Inline SVGs are tree-shakeable and can be styled with CSS

// Use SVGO to optimize SVG files (removes metadata, simplifies paths)
// Use a React SVG loader (vite-plugin-svgr or @svgr/webpack) to import as components
import { ReactComponent as SearchIcon } from './icons/search.svg';

function SearchBar() {
  return (
    <div className="search-bar">
      <SearchIcon width={20} height={20} aria-hidden="true" />
      <input placeholder="Search..." />
    </div>
  );
}
```

**Asset optimization checklist for production:**
- Compress images with tools like Sharp, Squoosh, or image CDNs (Cloudinary, imgix).
- Use `loading="lazy"` for below-the-fold images; `fetchPriority="high"` for LCP images.
- Set explicit `width` and `height` to prevent CLS.
- Serve from a CDN with proper `Cache-Control` headers.
- Use font subsetting for custom fonts (only include characters you need).
- Preload critical fonts: `<link rel="preload" href="/font.woff2" as="font" crossorigin>`.

---

### Q19. How would you profile and diagnose a slow React dashboard in production? Walk through a real scenario.

**Answer:**

**Scenario:** Your team's internal analytics dashboard loads slowly (5s+), and users complain that interacting with filters causes noticeable lag (300ms+ per interaction). Here's a systematic approach to diagnose and fix it.

**Phase 1: Measure and identify bottlenecks**

```jsx
// Step 1: Add performance marks to measure real user experience
// Wrap the app with a performance observer
useEffect(() => {
  // Measure component mount time
  performance.mark('dashboard-mount-start');
  return () => {
    performance.mark('dashboard-mount-end');
    performance.measure('dashboard-mount',
      'dashboard-mount-start', 'dashboard-mount-end');
  };
}, []);

// Step 2: Use React Profiler API to capture render timings in production
import { Profiler } from 'react';

function onRender(id, phase, actualDuration, baseDuration, startTime, commitTime) {
  // Send to monitoring (DataDog, NewRelic, custom endpoint)
  if (actualDuration > 16) { // slower than 60fps
    reportSlowRender({
      component: id,
      phase,           // "mount" or "update"
      actualDuration,  // time spent rendering (ms)
      baseDuration,    // estimated time without memoization (ms)
      startTime,
      commitTime,
    });
  }
}

function Dashboard() {
  return (
    <Profiler id="Dashboard" onRender={onRender}>
      <Profiler id="Filters" onRender={onRender}>
        <FilterPanel />
      </Profiler>
      <Profiler id="DataTable" onRender={onRender}>
        <DataTable />
      </Profiler>
      <Profiler id="Charts" onRender={onRender}>
        <ChartSection />
      </Profiler>
    </Profiler>
  );
}
```

**Phase 2: Use Chrome DevTools Performance tab**

```jsx
// Step 3: Record a performance trace
// 1. Open Chrome DevTools → Performance tab
// 2. Click Record, interact with filters, click Stop
// 3. Look for:
//    - Long Tasks (>50ms) — shown as red triangles
//    - Layout Thrashing — forced reflows in the "Layout" section
//    - JavaScript execution time — expand "Main" thread

// Step 4: Use React DevTools Profiler
// 1. Open React DevTools → Profiler tab
// 2. Enable "Record why each component rendered"
// 3. Record while interacting with filters
// 4. Identify: which components render? Why? How long?
```

**Phase 3: Common findings and fixes**

```jsx
// FINDING 1: DataTable renders 10,000 rows on every filter change
// FIX: Virtualize with react-window

import { FixedSizeList } from 'react-window';

function DataTable({ rows }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={rows.length}
      itemSize={35}
      itemData={rows}
      overscanCount={5}
    >
      {({ index, style, data }) => (
        <div style={style} className="table-row">
          {data[index].name} — {data[index].value}
        </div>
      )}
    </FixedSizeList>
  );
}

// FINDING 2: Chart re-renders when filters change but chart data hasn't
// FIX: Memoize the chart component and its data transformation

const ChartSection = memo(function ChartSection({ rawData, dateRange }) {
  const chartData = useMemo(() => {
    return aggregateByDay(rawData, dateRange);
  }, [rawData, dateRange]);

  return <LineChart data={chartData} />;
});

// FINDING 3: Expensive data transformation runs on every render
// FIX: Move to Web Worker for heavy computation

// worker.js
self.onmessage = function(e) {
  const { data, filters } = e.data;
  const result = expensiveAggregation(data, filters);
  self.postMessage(result);
};

// useWorker.js — custom hook for Web Worker communication
function useWorkerComputation(data, filters) {
  const [result, setResult] = useState(null);
  const workerRef = useRef(null);

  useEffect(() => {
    workerRef.current = new Worker(new URL('./worker.js', import.meta.url));
    workerRef.current.onmessage = (e) => setResult(e.data);
    return () => workerRef.current.terminate();
  }, []);

  useEffect(() => {
    workerRef.current?.postMessage({ data, filters });
  }, [data, filters]);

  return result;
}

// FINDING 4: Context value changes on every render, causing all consumers to re-render
// FIX: Memoize context value

function DashboardProvider({ children }) {
  const [filters, setFilters] = useState(defaultFilters);
  const [data] = useQuery('dashboard-data');

  // ✅ Memoize to prevent unnecessary consumer re-renders
  const value = useMemo(() => ({
    filters,
    setFilters,
    data,
    summary: computeSummary(data, filters),
  }), [filters, data]);

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
}
```

**Phase 4: Validate improvements**

```jsx
// Use the Profiler to compare before/after:
// Before: DataTable render = 340ms, Chart render = 120ms, Total = 580ms
// After:  DataTable render = 12ms, Chart render = 0ms (skipped), Total = 35ms

// Automate with Lighthouse CI in your CI/CD pipeline
// lighthouse-ci.yaml
// assertions:
//   largest-contentful-paint: ["warn", { maxNumericValue: 2500 }]
//   interactive: ["error", { maxNumericValue: 3800 }]
//   cumulative-layout-shift: ["warn", { maxNumericValue: 0.1 }]
```

---

### Q20. How would you build a high-performance dashboard displaying 100K rows with virtualization, memoization, and Web Workers?

**Answer:**

This is the ultimate React performance challenge that combines every optimization technique. Here's a complete architecture for a production analytics dashboard.

**Architecture overview:**
1. **Web Worker** — heavy data processing off the main thread.
2. **Virtualization** — render only visible rows.
3. **Memoization** — prevent cascading re-renders.
4. **Debounced inputs** — reduce processing frequency.
5. **`useTransition`** — keep the UI responsive during updates.

**Step 1: Web Worker for data processing**

```jsx
// dataWorker.js — runs off the main thread
self.onmessage = function (e) {
  const { type, payload } = e.data;

  switch (type) {
    case 'FILTER_AND_SORT': {
      const { data, filters, sortConfig } = payload;
      const start = performance.now();

      // Step 1: Filter
      let result = data;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        result = result.filter(row =>
          row.name.toLowerCase().includes(q) ||
          row.email.toLowerCase().includes(q) ||
          row.department.toLowerCase().includes(q)
        );
      }
      if (filters.department !== 'all') {
        result = result.filter(row => row.department === filters.department);
      }
      if (filters.minRevenue > 0) {
        result = result.filter(row => row.revenue >= filters.minRevenue);
      }

      // Step 2: Sort
      if (sortConfig.field) {
        result.sort((a, b) => {
          const valA = a[sortConfig.field];
          const valB = b[sortConfig.field];
          const cmp = typeof valA === 'string'
            ? valA.localeCompare(valB)
            : valA - valB;
          return sortConfig.direction === 'asc' ? cmp : -cmp;
        });
      }

      // Step 3: Compute aggregates
      const aggregates = {
        totalRevenue: result.reduce((sum, r) => sum + r.revenue, 0),
        avgRevenue: result.length ? result.reduce((sum, r) => sum + r.revenue, 0) / result.length : 0,
        count: result.length,
        departments: [...new Set(result.map(r => r.department))].length,
      };

      const elapsed = performance.now() - start;
      self.postMessage({ type: 'RESULT', payload: { rows: result, aggregates, elapsed } });
      break;
    }
  }
};
```

**Step 2: Custom hook for worker communication**

```jsx
// useDataWorker.js
import { useRef, useEffect, useState, useCallback } from 'react';

export function useDataWorker(rawData) {
  const workerRef = useRef(null);
  const [result, setResult] = useState({ rows: [], aggregates: null, elapsed: 0 });
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    workerRef.current = new Worker(
      new URL('./dataWorker.js', import.meta.url),
      { type: 'module' }
    );

    workerRef.current.onmessage = (e) => {
      if (e.data.type === 'RESULT') {
        setResult(e.data.payload);
        setIsProcessing(false);
      }
    };

    return () => workerRef.current?.terminate();
  }, []);

  const process = useCallback((filters, sortConfig) => {
    if (!workerRef.current || !rawData.length) return;
    setIsProcessing(true);
    workerRef.current.postMessage({
      type: 'FILTER_AND_SORT',
      payload: { data: rawData, filters, sortConfig },
    });
  }, [rawData]);

  return { ...result, isProcessing, process };
}
```

**Step 3: Virtualized table component**

```jsx
// VirtualTable.jsx
import { memo, useCallback, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';

const COLUMNS = [
  { key: 'name', label: 'Name', width: 200 },
  { key: 'email', label: 'Email', width: 250 },
  { key: 'department', label: 'Department', width: 150 },
  { key: 'revenue', label: 'Revenue', width: 120, format: (v) => `$${v.toLocaleString()}` },
  { key: 'status', label: 'Status', width: 100 },
];

const ROW_HEIGHT = 40;
const HEADER_HEIGHT = 48;

// Memoized row component — only re-renders when its specific row data changes
const TableRow = memo(function TableRow({ index, style, data }) {
  const { rows, onRowClick, selectedId } = data;
  const row = rows[index];
  const isSelected = row.id === selectedId;

  return (
    <div
      style={{
        ...style,
        display: 'flex',
        alignItems: 'center',
        borderBottom: '1px solid #eee',
        backgroundColor: isSelected ? '#e3f2fd' : index % 2 ? '#fafafa' : '#fff',
        cursor: 'pointer',
      }}
      onClick={() => onRowClick(row.id)}
    >
      {COLUMNS.map(col => (
        <div key={col.key} style={{ width: col.width, padding: '0 12px', flexShrink: 0 }}>
          {col.format ? col.format(row[col.key]) : row[col.key]}
        </div>
      ))}
    </div>
  );
});

export const VirtualTable = memo(function VirtualTable({
  rows,
  height = 600,
  onRowClick,
  selectedId,
  onSort,
  sortConfig,
}) {
  const listRef = useRef();

  // Stable itemData object to prevent all rows from re-rendering
  const itemData = useMemo(() => ({
    rows,
    onRowClick,
    selectedId,
  }), [rows, onRowClick, selectedId]);

  return (
    <div>
      {/* Fixed header */}
      <div style={{
        display: 'flex',
        height: HEADER_HEIGHT,
        alignItems: 'center',
        fontWeight: 'bold',
        borderBottom: '2px solid #ddd',
        backgroundColor: '#f5f5f5',
      }}>
        {COLUMNS.map(col => (
          <div
            key={col.key}
            style={{ width: col.width, padding: '0 12px', cursor: 'pointer', flexShrink: 0 }}
            onClick={() => onSort(col.key)}
          >
            {col.label}
            {sortConfig.field === col.key && (sortConfig.direction === 'asc' ? ' ↑' : ' ↓')}
          </div>
        ))}
      </div>

      {/* Virtualized body — only renders ~15-20 rows at a time out of 100K */}
      <List
        ref={listRef}
        height={height}
        itemCount={rows.length}
        itemSize={ROW_HEIGHT}
        itemData={itemData}
        overscanCount={10}
        width="100%"
      >
        {TableRow}
      </List>
    </div>
  );
});
```

**Step 4: Dashboard with all optimizations combined**

```jsx
// Dashboard.jsx
import { useState, useCallback, useTransition, useMemo, useEffect } from 'react';
import { useDataWorker } from './useDataWorker';
import { VirtualTable } from './VirtualTable';

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export default function Dashboard() {
  // Raw data — loaded once from API
  const [rawData, setRawData] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  // Filter state
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('all');
  const [minRevenue, setMinRevenue] = useState(0);

  // Sort state
  const [sortConfig, setSortConfig] = useState({ field: 'name', direction: 'asc' });

  // React 18 concurrent feature: keep UI responsive during heavy updates
  const [isPending, startTransition] = useTransition();

  // Debounce search to avoid processing on every keystroke
  const debouncedSearch = useDebounce(search, 200);

  // Web Worker handles all heavy computation off the main thread
  const { rows, aggregates, isProcessing, process } = useDataWorker(rawData);

  // Load data on mount
  useEffect(() => {
    fetch('/api/dashboard-data')
      .then(res => res.json())
      .then(data => setRawData(data)); // 100,000 rows
  }, []);

  // Trigger worker processing when filters/sort change
  useEffect(() => {
    const filters = { search: debouncedSearch, department, minRevenue };
    process(filters, sortConfig);
  }, [debouncedSearch, department, minRevenue, sortConfig, process]);

  // Stable callbacks for memoized children
  const handleRowClick = useCallback((id) => {
    setSelectedId(id);
  }, []);

  const handleSort = useCallback((field) => {
    startTransition(() => {
      setSortConfig(prev => ({
        field,
        direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
      }));
    });
  }, []);

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1>Analytics Dashboard</h1>

      {/* Aggregates summary — memoized to prevent re-render during filter typing */}
      {aggregates && (
        <AggregateCards aggregates={aggregates} />
      )}

      {/* Filter controls */}
      <div style={{ display: 'flex', gap: 16, margin: '16px 0' }}>
        <input
          placeholder="Search 100K rows..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ padding: 8, flex: 1 }}
        />
        <select value={department} onChange={e => setDepartment(e.target.value)}>
          <option value="all">All Departments</option>
          <option value="engineering">Engineering</option>
          <option value="sales">Sales</option>
          <option value="marketing">Marketing</option>
        </select>
        <input
          type="number"
          placeholder="Min revenue"
          value={minRevenue || ''}
          onChange={e => setMinRevenue(Number(e.target.value) || 0)}
          style={{ padding: 8, width: 150 }}
        />
      </div>

      {/* Status bar */}
      <div style={{ marginBottom: 8, color: '#666' }}>
        {isProcessing || isPending ? 'Processing...' : `${rows.length.toLocaleString()} rows`}
      </div>

      {/* Virtualized table — renders only ~20 rows out of 100K */}
      <VirtualTable
        rows={rows}
        height={600}
        onRowClick={handleRowClick}
        selectedId={selectedId}
        onSort={handleSort}
        sortConfig={sortConfig}
      />
    </div>
  );
}

// Memoized aggregate cards — only re-renders when aggregates change
const AggregateCards = memo(function AggregateCards({ aggregates }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
      <StatCard label="Total Rows" value={aggregates.count.toLocaleString()} />
      <StatCard label="Total Revenue" value={`$${aggregates.totalRevenue.toLocaleString()}`} />
      <StatCard label="Avg Revenue" value={`$${Math.round(aggregates.avgRevenue).toLocaleString()}`} />
      <StatCard label="Departments" value={aggregates.departments} />
    </div>
  );
});

const StatCard = memo(function StatCard({ label, value }) {
  return (
    <div style={{
      padding: 16,
      borderRadius: 8,
      backgroundColor: '#f8f9fa',
      border: '1px solid #e9ecef',
    }}>
      <div style={{ fontSize: 14, color: '#666' }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 'bold', marginTop: 4 }}>{value}</div>
    </div>
  );
});
```

**Performance breakdown of this architecture:**

| Technique | Impact |
|-----------|--------|
| **Web Worker** | Data processing (filter + sort + aggregate of 100K rows) runs in ~50ms on a background thread, zero main thread blocking |
| **Virtualization** | Only ~20 DOM nodes rendered instead of 100,000 — initial render < 5ms |
| **`React.memo`** | Unchanged rows skip re-render entirely — only the selected row updates |
| **`useCallback`** | Stable handler references prevent memo from bailing |
| **Debounce** | Search triggers processing at most every 200ms instead of per-keystroke |
| **`useTransition`** | Sort interactions stay responsive — React can interrupt and prioritize user input |
| **`useMemo` (itemData)** | Prevents all virtualized rows from re-rendering when only selection changes |

**React 19 Compiler note:** With the React 19 Compiler enabled, you could remove most of the manual `memo`, `useMemo`, and `useCallback` calls from this code. The compiler would auto-memoize `handleRowClick`, `handleSort`, `itemData`, `AggregateCards`, `StatCard`, and `TableRow` automatically. However, the **architectural** decisions — virtualization, Web Workers, debouncing, and `useTransition` — remain manual and essential. The compiler optimizes rendering; it cannot decide to virtualize a list or move computation to a worker.

---

*End of Memoization & Performance — React 18 Interview Questions*
