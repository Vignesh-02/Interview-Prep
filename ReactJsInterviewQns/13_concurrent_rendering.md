# Concurrent Rendering in React 18 — Interview Questions

## Topic Introduction

Concurrent Rendering is the most significant architectural change in React's history, introduced in React 18. Before concurrency, React rendering was **synchronous** — once React started rendering a component tree, it could not be interrupted until the entire tree was rendered and committed to the DOM. This meant that a heavy render (e.g., filtering a list of 10,000 items) would block the main thread, making the UI feel sluggish and unresponsive to user input like typing, clicking, or scrolling.

React 18 solves this by making rendering **interruptible**. With concurrent rendering, React can start rendering an update, pause in the middle to handle a more urgent update (like a keystroke), and then resume or even abandon the previous work. This is powered by the **Fiber architecture** — an internal rewrite of React's reconciliation engine that represents each unit of work as a "fiber" node in a linked-list tree. Each fiber is a lightweight object that tracks the component, its state, and its place in the tree, allowing React to pause at any fiber boundary, yield back to the browser, and pick up where it left off. The key APIs that unlock this power are `useTransition` (mark an update as non-urgent and get a pending state), `useDeferredValue` (defer re-rendering with a stale value), `startTransition` (fire-and-forget non-urgent updates), and automatic batching (grouping multiple state updates into a single render, even inside promises and timeouts).

Here is a quick illustration showing how `useTransition` keeps a search input responsive while filtering a massive list:

```jsx
import { useState, useTransition } from 'react';

function SearchableList({ items }) {
  const [query, setQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState(items);
  const [isPending, startTransition] = useTransition();

  const handleChange = (e) => {
    const value = e.target.value;
    // Urgent update — keep input responsive
    setQuery(value);
    // Non-urgent update — filter can be deferred
    startTransition(() => {
      const result = items.filter((item) =>
        item.name.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredItems(result);
    });
  };

  return (
    <div>
      <input value={query} onChange={handleChange} placeholder="Search..." />
      {isPending && <p>Updating list...</p>}
      <ul>
        {filteredItems.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

In the example above, typing into the input is always instant because `setQuery` is treated as an urgent update, while the expensive filtering wrapped in `startTransition` is marked as non-urgent. React can interrupt the filtering render if the user types another character, ensuring the UI never freezes.

---

## Beginner Level (Q1–Q5)

---

### Q1. What is concurrent rendering and why did React 18 introduce it?

**Answer:**

Concurrent rendering is a fundamental change in how React renders component trees. In previous versions of React (17 and below), rendering was **synchronous and blocking** — once React started processing an update, it had to finish the entire render pass before the browser could paint or respond to user events. If the render was expensive (e.g., rendering thousands of list items), the UI would freeze.

React 18 introduces **concurrent rendering**, which allows React to:

1. **Pause** rendering work in the middle of a component tree
2. **Yield** to the browser so it can handle user input, animations, or paint
3. **Resume** the paused work later
4. **Abandon** work entirely if a newer, more relevant update comes in

This is an opt-in mechanism — simply upgrading to React 18 doesn't change behavior of existing code. You unlock concurrency by using concurrent features like `useTransition`, `useDeferredValue`, or `<Suspense>`.

```jsx
import { createRoot } from 'react-dom/client';
import App from './App';

// React 18: createRoot enables concurrent features
// (The old ReactDOM.render still works but without concurrency)
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

**Key takeaway:** Concurrent rendering doesn't make your code run faster — it makes React **smarter about scheduling** so that high-priority updates (user input) are never blocked by low-priority work (data filtering, background computation).

---

### Q2. What is `startTransition` and how does it mark updates as non-urgent?

**Answer:**

`startTransition` is a function imported from React that lets you mark a state update as **non-urgent** (a "transition"). React treats transitions as lower priority — they can be interrupted by urgent updates (like typing or clicking) and they won't block the UI.

Without `startTransition`, every `setState` call is treated as urgent, meaning React will process it immediately and synchronously. By wrapping a `setState` call inside `startTransition`, you tell React: "This update can wait if something more important comes along."

```jsx
import { useState, startTransition } from 'react';

function TabContainer() {
  const [tab, setTab] = useState('home');

  const switchTab = (nextTab) => {
    // This is a non-urgent update — if the tab content is heavy to render,
    // React can interrupt it if the user clicks another tab quickly.
    startTransition(() => {
      setTab(nextTab);
    });
  };

  return (
    <div>
      <nav>
        <button onClick={() => switchTab('home')}>Home</button>
        <button onClick={() => switchTab('analytics')}>Analytics</button>
        <button onClick={() => switchTab('settings')}>Settings</button>
      </nav>
      <TabContent tab={tab} />
    </div>
  );
}

function TabContent({ tab }) {
  // Imagine each tab renders thousands of rows or complex charts
  if (tab === 'home') return <HomeTab />;
  if (tab === 'analytics') return <AnalyticsTab />; // expensive
  if (tab === 'settings') return <SettingsTab />;
}
```

**Important rules about `startTransition`:**
- The callback must be **synchronous** — you cannot put `await` inside it.
- Only `setState` calls inside the callback are marked as transitions.
- `startTransition` does NOT provide a pending state — use `useTransition` if you need that.

---

### Q3. What is `useTransition` and how does `isPending` work?

**Answer:**

`useTransition` is a React hook that gives you two things:

1. **`isPending`** — a boolean that is `true` while the transition is rendering in the background
2. **`startTransition`** — a function to wrap non-urgent state updates (same behavior as the standalone `startTransition`)

The `isPending` flag is what makes `useTransition` more powerful than the standalone `startTransition` — it lets you show loading indicators while the background render is in progress.

```jsx
import { useState, useTransition } from 'react';

function ProductFilter({ products }) {
  const [query, setQuery] = useState('');
  const [filtered, setFiltered] = useState(products);
  const [isPending, startTransition] = useTransition();

  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value); // Urgent: keep input in sync

    startTransition(() => {
      // Non-urgent: filter thousands of products
      const results = products.filter((p) =>
        p.title.toLowerCase().includes(value.toLowerCase())
      );
      setFiltered(results);
    });
  };

  return (
    <div>
      <input
        value={query}
        onChange={handleSearch}
        placeholder="Filter products..."
      />

      {/* Show a subtle loading state while filtering */}
      <div style={{ opacity: isPending ? 0.6 : 1, transition: 'opacity 0.2s' }}>
        <p>{filtered.length} products found</p>
        <ul>
          {filtered.map((p) => (
            <li key={p.id}>{p.title} — ${p.price}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

**When to use `useTransition` vs `startTransition`:**
- Use `useTransition` when you need the `isPending` state (most of the time in components).
- Use standalone `startTransition` in non-component code (event handlers in utility modules, library code) where you cannot call hooks.

---

### Q4. What is `useDeferredValue` and how does it differ from debouncing?

**Answer:**

`useDeferredValue` is a hook that accepts a value and returns a **deferred copy** of it. When the original value updates, React first renders with the old (stale) deferred value, then schedules a background re-render with the new value. This background re-render is interruptible — if the value changes again before the background render finishes, React abandons the old work and starts fresh with the newest value.

This is fundamentally different from debouncing:
- **Debouncing** delays the update by a fixed time (e.g., 300ms). Even on a fast device, you always wait.
- **`useDeferredValue`** is adaptive — on fast devices the deferred render finishes almost immediately; on slow devices it naturally falls behind to keep the UI responsive. There is no fixed delay.

```jsx
import { useState, useDeferredValue, useMemo } from 'react';

function SearchResults({ items }) {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);

  // This expensive computation uses the deferred value,
  // so it won't block typing in the input
  const filteredItems = useMemo(() => {
    return items.filter((item) =>
      item.name.toLowerCase().includes(deferredQuery.toLowerCase())
    );
  }, [deferredQuery, items]);

  const isStale = query !== deferredQuery;

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Type to search..."
      />
      <div style={{ opacity: isStale ? 0.7 : 1 }}>
        {filteredItems.map((item) => (
          <div key={item.id}>{item.name}</div>
        ))}
      </div>
    </div>
  );
}
```

**Key points:**
- `useDeferredValue` is most useful when you receive a value from a parent or external source and cannot wrap the corresponding `setState` in `startTransition`.
- Pair it with `React.memo` or `useMemo` so that the child component/computation actually skips re-rendering when the deferred value hasn't changed yet.

---

### Q5. What is automatic batching in React 18 and how is it different from React 17?

**Answer:**

**Batching** means React groups multiple state updates into a single re-render for better performance.

In **React 17**, batching only happened inside React event handlers:

```jsx
// React 17 behavior
function handleClick() {
  setCount(1);    // Does NOT re-render yet
  setFlag(true);  // Does NOT re-render yet
  // React batches both → ONE re-render ✅
}

// But inside promises, timeouts, or native events:
fetch('/api/data').then(() => {
  setCount(1);    // Re-renders immediately ❌
  setFlag(true);  // Re-renders again ❌
  // TWO separate re-renders!
});
```

In **React 18**, batching is **automatic everywhere** — inside promises, `setTimeout`, native event handlers, and any other context:

```jsx
// React 18 behavior — all of these are batched

// Inside a promise
fetch('/api/data').then(() => {
  setCount(1);
  setFlag(true);
  // ONE re-render ✅
});

// Inside setTimeout
setTimeout(() => {
  setCount(1);
  setFlag(true);
  // ONE re-render ✅
}, 1000);

// Inside a native event listener
document.getElementById('btn').addEventListener('click', () => {
  setCount(1);
  setFlag(true);
  // ONE re-render ✅
});
```

**Why this matters:** Automatic batching reduces unnecessary renders, which improves performance without any code changes when migrating to React 18. In most applications, this alone can eliminate dozens of redundant re-renders per interaction.

**Opt-out with `flushSync`:** If you need a state update to be applied immediately (e.g., to read the updated DOM), you can use `flushSync` — covered in Q12.

---

## Intermediate Level (Q6–Q12)

---

### Q6. `useTransition` vs `useDeferredValue` — when should you use which?

**Answer:**

Both achieve the same goal — keeping the UI responsive by marking work as non-urgent — but they apply to different situations:

| Aspect | `useTransition` | `useDeferredValue` |
|---|---|---|
| **What it wraps** | A `setState` call | A value (prop, state, or derived) |
| **When you control the state update** | Yes — you wrap `setState` | No — you receive the value from elsewhere |
| **Provides pending state** | Yes (`isPending`) | No (compare original vs deferred) |
| **Best for** | Actions you trigger | Values you receive |

**Use `useTransition` when you own the state update:**

```jsx
function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();

  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value); // urgent
    startTransition(() => {
      setResults(computeExpensiveResults(value)); // non-urgent
    });
  };

  return (
    <>
      <input value={query} onChange={handleSearch} />
      {isPending ? <Spinner /> : <ResultsList results={results} />}
    </>
  );
}
```

**Use `useDeferredValue` when you don't control the state update:**

```jsx
// You receive `searchQuery` as a prop — you can't wrap the parent's setState
function ExpensiveResultsList({ searchQuery }) {
  const deferredQuery = useDeferredValue(searchQuery);
  const isStale = searchQuery !== deferredQuery;

  const results = useMemo(
    () => computeExpensiveResults(deferredQuery),
    [deferredQuery]
  );

  return (
    <div style={{ opacity: isStale ? 0.5 : 1 }}>
      {results.map((r) => <ResultCard key={r.id} result={r} />)}
    </div>
  );
}
```

**Production rule of thumb:** If you can modify the `setState` call, prefer `useTransition` because `isPending` gives you explicit control over loading states. If you receive the value as a prop from a parent or third-party component, use `useDeferredValue`.

---

### Q7. How does the Fiber architecture enable React to pause and resume rendering?

**Answer:**

The **Fiber architecture** (introduced in React 16 but fully leveraged in React 18) replaces React's old recursive stack-based reconciler with an **iterative, linked-list-based** work loop.

**Old reconciler (stack):** React called components recursively. Once it started, the call stack had to unwind completely — no way to pause mid-render.

**Fiber reconciler:** Each component instance is represented by a **fiber node** — a plain JavaScript object. Fibers form a tree connected by three pointers: `child`, `sibling`, and `return` (parent). The work loop processes one fiber at a time, then checks if it should yield to the browser.

```jsx
// Conceptual view of a Fiber node (simplified)
const fiber = {
  tag: FunctionComponent,       // Type of fiber (function, class, host, etc.)
  type: MyComponent,            // The component function/class
  key: null,                    // React key for reconciliation
  stateNode: null,              // DOM node (for host components)
  
  // Tree structure (linked list)
  child: childFiber,            // First child
  sibling: siblingFiber,        // Next sibling
  return: parentFiber,          // Parent

  // Work tracking
  pendingProps: { name: 'new' },
  memoizedProps: { name: 'old' },
  memoizedState: { count: 0 },
  
  // Priority & scheduling
  lanes: 0b0000000000000000010, // Bitfield representing priority lanes
  
  // Alternate (double buffering)
  alternate: currentFiber,      // Points to the "current" version
};
```

**How pausing works:**

React's work loop looks conceptually like this:

```jsx
// Simplified React concurrent work loop
function workLoop(deadline) {
  while (nextUnitOfWork && !shouldYield()) {
    // Process one fiber
    nextUnitOfWork = performUnitOfWork(nextUnitOfWork);
  }

  if (nextUnitOfWork) {
    // Still work left — schedule continuation
    requestIdleCallback(workLoop); // (React uses its own scheduler, not this)
  } else {
    // All work complete — commit to DOM
    commitRoot();
  }
}

function shouldYield() {
  // Check if the browser needs the main thread
  // (e.g., user input is waiting, frame deadline passed)
  return scheduler.shouldYield();
}
```

Because each unit of work is just moving a pointer from one fiber to the next (not a recursive call stack), React can stop anywhere, save its position, and come back later. This is the foundation that makes `useTransition` and `useDeferredValue` possible.

---

### Q8. How does React 18 handle priority-based rendering (urgent vs non-urgent updates)?

**Answer:**

React 18 uses a **lanes** system for priority scheduling. Each update is assigned a "lane" — a bit in a bitfield — that represents its priority. React processes higher-priority lanes first and can interrupt lower-priority work.

There are several priority levels:

1. **Sync lane** (highest): `flushSync` calls
2. **Input continuous lane**: User input like typing, clicking
3. **Default lane**: Regular `setState` calls
4. **Transition lane** (lower): `startTransition` / `useTransition` updates
5. **Idle lane** (lowest): Offscreen or `useDeferredValue` work

```jsx
import { useState, useTransition, startTransition } from 'react';

function PriorityDemo() {
  const [urgent, setUrgent] = useState('');     // High-priority lane
  const [deferred, setDeferred] = useState(''); // Transition lane
  const [isPending, startTransitionHook] = useTransition();

  const handleInput = (e) => {
    const value = e.target.value;

    // This fires on the default/input lane — processed immediately
    setUrgent(value);

    // This fires on the transition lane — can be interrupted
    startTransitionHook(() => {
      // Imagine this triggers an expensive computation
      setDeferred(computeExpensiveValue(value));
    });
  };

  return (
    <div>
      <input value={urgent} onChange={handleInput} />
      <p>Input (instant): {urgent}</p>
      <p style={{ opacity: isPending ? 0.5 : 1 }}>
        Computed (deferred): {deferred}
      </p>
    </div>
  );
}
```

**What happens under the hood:**
1. User types "a" → React schedules `setUrgent("a")` on the input lane and `setDeferred(...)` on the transition lane.
2. React starts processing the input lane first (higher priority) → the input updates instantly.
3. React begins the transition lane work (filtering/computing).
4. User types "ab" before transition finishes → React **interrupts** the transition work, processes the new input lane update, and **restarts** the transition with "ab".
5. When the user stops typing, the transition lane finally completes and commits.

This model ensures the UI always feels responsive regardless of how expensive the non-urgent computation is.

---

### Q9. How would you implement search-as-you-type with `useTransition`? (Classic interview scenario)

**Answer:**

This is one of the most commonly asked React 18 interview questions. The goal is to keep the input responsive while filtering/fetching results in the background.

**Production implementation:**

```jsx
import { useState, useTransition, useCallback } from 'react';

// Simulating a large dataset
const generateProducts = () =>
  Array.from({ length: 50000 }, (_, i) => ({
    id: i,
    name: `Product ${i} - ${['Widget', 'Gadget', 'Tool', 'Device'][i % 4]}`,
    category: ['Electronics', 'Clothing', 'Books', 'Home'][i % 4],
    price: Math.round(Math.random() * 500 * 100) / 100,
  }));

const ALL_PRODUCTS = generateProducts();

function SearchableProductList() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(ALL_PRODUCTS.slice(0, 100));
  const [isPending, startTransition] = useTransition();

  const handleSearch = useCallback((e) => {
    const value = e.target.value;

    // URGENT: Update the input value immediately so it doesn't feel laggy
    setQuery(value);

    // NON-URGENT: Filter 50,000 products — this can be interrupted
    startTransition(() => {
      if (value.trim() === '') {
        setResults(ALL_PRODUCTS.slice(0, 100));
      } else {
        const filtered = ALL_PRODUCTS.filter(
          (p) =>
            p.name.toLowerCase().includes(value.toLowerCase()) ||
            p.category.toLowerCase().includes(value.toLowerCase())
        );
        setResults(filtered.slice(0, 100)); // Paginate to avoid DOM bloat
      }
    });
  }, []);

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 20 }}>
      <input
        value={query}
        onChange={handleSearch}
        placeholder="Search 50,000 products..."
        style={{ width: '100%', padding: 12, fontSize: 16 }}
      />

      {isPending && (
        <div style={{ padding: '8px 0', color: '#888' }}>
          Filtering results...
        </div>
      )}

      <div style={{ opacity: isPending ? 0.6 : 1, transition: 'opacity 0.15s' }}>
        <p style={{ color: '#666', marginTop: 12 }}>
          Showing {results.length} results
        </p>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {results.map((product) => (
            <li
              key={product.id}
              style={{
                padding: '8px 12px',
                borderBottom: '1px solid #eee',
              }}
            >
              <strong>{product.name}</strong>
              <span style={{ color: '#666', marginLeft: 8 }}>
                {product.category} — ${product.price}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default SearchableProductList;
```

**Why this works:**
1. `setQuery(value)` updates immediately — the input character appears instantly.
2. `startTransition(() => setResults(...))` schedules the expensive filter on a low-priority lane.
3. If the user types another character before filtering completes, React abandons the in-progress filter and starts a new one with the latest query.
4. `isPending` lets you show a subtle visual cue (reduced opacity, loading text) without a jarring spinner.

**Interview follow-up — "Why not debounce?":** Debouncing waits a fixed time (e.g., 300ms) regardless of device speed. On a powerful machine the filter might take 5ms, but debounce still waits 300ms. `useTransition` is adaptive — on fast devices the result appears almost immediately; on slow devices it naturally defers to keep the input responsive.

---

### Q10. How do you use `useDeferredValue` to optimize expensive child components?

**Answer:**

`useDeferredValue` shines when you have an expensive child component that re-renders based on a prop you receive. By passing a deferred version of the prop and wrapping the child in `React.memo`, you avoid blocking the UI while the child re-renders.

**Production scenario:** A data table component that re-renders with every filter change.

```jsx
import { useState, useDeferredValue, memo, useMemo } from 'react';

// Expensive child component — memoized to skip renders
// when deferredFilter hasn't changed yet
const DataTable = memo(function DataTable({ filter, data }) {
  console.log('DataTable rendering with filter:', filter);

  const filtered = useMemo(() => {
    // Simulate expensive computation
    return data.filter((row) => {
      return Object.values(row).some((val) =>
        String(val).toLowerCase().includes(filter.toLowerCase())
      );
    });
  }, [filter, data]);

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Department</th>
          <th>Revenue</th>
        </tr>
      </thead>
      <tbody>
        {filtered.map((row) => (
          <tr key={row.id}>
            <td>{row.name}</td>
            <td>{row.email}</td>
            <td>{row.department}</td>
            <td>${row.revenue.toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
});

function Dashboard({ data }) {
  const [filter, setFilter] = useState('');
  const deferredFilter = useDeferredValue(filter);
  const isStale = filter !== deferredFilter;

  return (
    <div>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter table..."
        style={{ padding: 8, fontSize: 16, width: 300 }}
      />

      <div
        style={{
          opacity: isStale ? 0.5 : 1,
          transition: 'opacity 0.1s',
          position: 'relative',
        }}
      >
        {isStale && (
          <div style={{
            position: 'absolute',
            top: 10,
            right: 10,
            background: '#fef3c7',
            padding: '4px 8px',
            borderRadius: 4,
            fontSize: 12,
          }}>
            Updating...
          </div>
        )}
        <DataTable filter={deferredFilter} data={data} />
      </div>
    </div>
  );
}
```

**Why `React.memo` is critical here:** Without `memo`, `DataTable` would re-render on every keystroke because the parent re-renders when `filter` changes. With `memo`, `DataTable` only re-renders when `deferredFilter` actually changes, which happens on the lower-priority deferred schedule.

**Pattern summary:**
1. Hold the original value in state (`filter`)
2. Create a deferred copy (`deferredFilter = useDeferredValue(filter)`)
3. Pass the deferred copy to the expensive child
4. Wrap the child in `React.memo`
5. Use `filter !== deferredFilter` to detect staleness and show visual feedback

---

### Q11. How does concurrent rendering affect third-party library compatibility?

**Answer:**

Concurrent rendering introduces a new behavior that can break libraries that rely on **synchronous rendering assumptions**: React may render a component multiple times before committing to the DOM, or abandon a render entirely. This breaks libraries that:

1. **Mutate external state during render** — the mutation happens multiple times or on an abandoned render
2. **Read from external mutable stores during render** — they may get inconsistent ("torn") values across the component tree
3. **Rely on render being called exactly once per commit**

```jsx
// ❌ BROKEN: Mutating external state during render
let renderCount = 0;

function BrokenCounter() {
  // In concurrent mode, this may execute multiple times for a single commit
  renderCount++; // Side effect during render!
  return <div>Rendered {renderCount} times</div>;
}

// ✅ FIXED: Use useEffect for side effects
import { useEffect, useRef } from 'react';

function FixedCounter() {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  return <div>Rendered {renderCount.current} times</div>;
}
```

**Common library compatibility issues and solutions:**

```jsx
// ❌ PROBLEM: Reading from an external store (e.g., Redux before v8, MobX)
// Different components may read different snapshots during a concurrent render
function BrokenStoreConsumer() {
  // If this store updates mid-render, some components see old value,
  // others see new value → "tearing"
  const value = externalStore.getValue();
  return <div>{value}</div>;
}

// ✅ SOLUTION: Use useSyncExternalStore (React 18)
import { useSyncExternalStore } from 'react';

function SafeStoreConsumer() {
  const value = useSyncExternalStore(
    externalStore.subscribe,   // Subscribe function
    externalStore.getSnapshot, // Get current value (must return immutable snapshot)
    externalStore.getServerSnapshot // Optional: for SSR
  );
  return <div>{value}</div>;
}
```

**Libraries to verify compatibility:**
- **Redux:** v8+ (uses `useSyncExternalStore`) is compatible. Older versions may tear.
- **Zustand:** v4+ is compatible.
- **MobX:** `mobx-react-lite` v4+ handles concurrent mode.
- **CSS-in-JS:** Libraries that insert styles during render (like older Emotion/styled-components) may insert duplicate styles on abandoned renders. Ensure you use their latest versions.

**Rule for library authors:** Never mutate shared state during render. Always use `useSyncExternalStore` for external store subscriptions.

---

### Q12. What is `flushSync` and when would you use it to opt out of automatic batching?

**Answer:**

`flushSync` forces React to flush all pending state updates synchronously and update the DOM immediately. It is an escape hatch from automatic batching — use it when you need to read the updated DOM immediately after a state change.

```jsx
import { useState } from 'react';
import { flushSync } from 'react-dom';

function ScrollToBottom() {
  const [messages, setMessages] = useState([]);
  const listRef = useRef(null);

  const addMessage = (text) => {
    // Without flushSync, both updates are batched and the DOM
    // isn't updated until after this function returns.
    // We need the DOM updated so we can scroll to the new message.

    flushSync(() => {
      setMessages((prev) => [...prev, { id: Date.now(), text }]);
    });

    // DOM is now updated — we can scroll to the bottom
    listRef.current.scrollTop = listRef.current.scrollHeight;
  };

  return (
    <div>
      <div ref={listRef} style={{ height: 300, overflow: 'auto' }}>
        {messages.map((msg) => (
          <div key={msg.id}>{msg.text}</div>
        ))}
      </div>
      <button onClick={() => addMessage('New message')}>
        Send
      </button>
    </div>
  );
}
```

**Another production use case — integrating with non-React libraries:**

```jsx
import { flushSync } from 'react-dom';

function ChartWithReactControls({ chart }) {
  const [range, setRange] = useState([0, 100]);

  const handleBrushEnd = (newRange) => {
    // We need the DOM updated immediately so the D3 chart
    // can read the new axis labels rendered by React
    flushSync(() => {
      setRange(newRange);
    });

    // Now the React-rendered axis labels are in the DOM
    chart.updateOverlay(); // D3 reads from the DOM
  };

  return (
    <div>
      <AxisLabels range={range} />
      <D3Chart onBrushEnd={handleBrushEnd} />
    </div>
  );
}
```

**When to use `flushSync`:**
- Reading DOM measurements immediately after a state update (scroll position, element dimensions)
- Synchronizing with non-React code that reads the DOM (D3, canvas libraries, analytics)
- Accessibility: ensuring screen readers see updated content immediately

**When NOT to use `flushSync`:**
- General performance optimization (it actually hurts performance)
- Working around slow renders (use `useTransition` instead)
- In render functions (it will throw an error)

**Warning:** `flushSync` forces synchronous rendering, which means it bypasses all concurrent features. Use it sparingly.

---

## Advanced Level (Q13–Q20)

---

### Q13. How does time slicing work — how does React split rendering work across frames?

**Answer:**

Time slicing is the mechanism by which React's concurrent renderer divides rendering work into small units and spreads them across multiple browser frames, ensuring the main thread is never blocked for too long (target: ~5ms per slice to maintain 60fps).

**How it works internally:**

React uses its own **Scheduler** package (`scheduler`) which implements a cooperative scheduling model:

1. React's work loop processes fibers one at a time.
2. After each fiber, it calls `shouldYield()` which checks if the current time slice has exceeded its deadline (~5ms).
3. If `shouldYield()` returns `true`, React stops processing and schedules a new task via `MessageChannel` (not `setTimeout` or `requestIdleCallback`).
4. The browser gets a chance to process input events, paint, and run other tasks.
5. When the browser is idle again, React picks up where it left off.

```jsx
// Conceptual representation of React's scheduler work loop
// (Based on React source code — simplified)

function workLoopConcurrent() {
  // Process fibers until we run out of work or need to yield
  while (workInProgress !== null && !shouldYield()) {
    performUnitOfWork(workInProgress);
  }
}

function shouldYield() {
  const currentTime = getCurrentTime();
  // deadline is typically ~5ms from when this slice started
  return currentTime >= deadline;
}

// React uses MessageChannel for scheduling, not setTimeout
// MessageChannel fires before the next paint, with minimal delay
const channel = new MessageChannel();
const port = channel.port2;
channel.port1.onmessage = performWorkUntilDeadline;

function schedulePerformWorkUntilDeadline() {
  port.postMessage(null);
}

function performWorkUntilDeadline() {
  const currentTime = getCurrentTime();
  deadline = currentTime + yieldInterval; // ~5ms

  const hasMoreWork = scheduledCallback(currentTime);

  if (hasMoreWork) {
    // More work to do — schedule the next slice
    schedulePerformWorkUntilDeadline();
  }
}
```

**Visualizing time slicing in practice:**

```jsx
import { useState, useTransition } from 'react';

// Each SlowItem takes ~1ms to render (artificial delay via heavy computation)
function SlowItem({ text }) {
  const startTime = performance.now();
  while (performance.now() - startTime < 1) {
    // Busy wait to simulate slow render
  }
  return <li>{text}</li>;
}

function TimeSlicingDemo() {
  const [count, setCount] = useState(200);
  const [isPending, startTransition] = useTransition();

  const items = Array.from({ length: count }, (_, i) => `Item ${i + 1}`);

  const handleChange = (e) => {
    startTransition(() => {
      setCount(Number(e.target.value));
    });
  };

  // Without useTransition: rendering 200 SlowItems takes ~200ms,
  // blocking the slider completely.
  // With useTransition + time slicing: React renders ~5 items per frame,
  // yielding back to the browser between slices so the slider stays smooth.

  return (
    <div>
      <label>
        Items: {count}
        <input
          type="range"
          min="0"
          max="500"
          value={count}
          onChange={handleChange}
        />
      </label>
      {isPending && <p>Rendering...</p>}
      <ul style={{ opacity: isPending ? 0.5 : 1 }}>
        {items.map((text) => (
          <SlowItem key={text} text={text} />
        ))}
      </ul>
    </div>
  );
}
```

**Key insight:** Time slicing only applies to **concurrent** renders (triggered by transitions). Regular `setState` still renders synchronously to avoid visual inconsistencies in urgent updates.

---

### Q14. Deep dive: How does React's reconciliation algorithm work with Fiber? Explain diffing, keys, and the two-phase commit.

**Answer:**

React's reconciliation is the process of determining what changed between the current fiber tree (what's on screen) and the work-in-progress fiber tree (the new render). It uses a **heuristic O(n) diffing algorithm** (instead of the theoretical O(n³) tree diff) based on two assumptions:

1. Elements of different types produce different trees.
2. The `key` prop hints at which child elements are stable across renders.

**The two-tree architecture (double buffering):**

```jsx
// React maintains TWO fiber trees:

// 1. "current" tree — represents what's currently on the DOM
// 2. "workInProgress" tree — being built during the render phase

// Each fiber has an `alternate` pointing to its counterpart:
currentFiber.alternate = workInProgressFiber;
workInProgressFiber.alternate = currentFiber;

// When the render is complete, React swaps the pointers:
// workInProgress becomes current (this is the "commit")
```

**The two-phase process:**

**Phase 1 — Render (reconciliation):** Pure, no side effects, interruptible in concurrent mode.

```jsx
// Simplified reconciliation for child elements
function reconcileChildFibers(returnFiber, currentChild, newChild) {
  // Case 1: Single element
  if (typeof newChild === 'object' && newChild !== null) {
    // Same type? → Reuse the fiber, update props
    if (currentChild && currentChild.type === newChild.type) {
      const existing = useFiber(currentChild, newChild.props);
      existing.return = returnFiber;
      return existing;
    }
    // Different type? → Delete old, create new
    deleteChild(returnFiber, currentChild);
    const created = createFiberFromElement(newChild);
    created.return = returnFiber;
    return created;
  }

  // Case 2: Array of elements — this is where keys matter
  if (Array.isArray(newChild)) {
    return reconcileChildrenArray(returnFiber, currentChild, newChild);
  }
}
```

**How keys optimize list reconciliation:**

```jsx
// WITHOUT keys — React matches by index (position)
// Old:  [A, B, C, D]
// New:  [D, A, B, C]
// React thinks: A→D (update), B→A (update), C→B (update), D→C (update)
// Result: 4 updates (inefficient!)

// WITH keys — React matches by key
// Old:  [A(key=a), B(key=b), C(key=c), D(key=d)]
// New:  [D(key=d), A(key=a), B(key=b), C(key=c)]
// React thinks: D moved to front, A/B/C shifted — reuse all fibers
// Result: Just DOM moves, no prop updates (efficient!)

function UserList({ users }) {
  return (
    <ul>
      {users.map((user) => (
        // ✅ Stable, unique key from data — React can track identity
        <li key={user.id}>
          <UserCard user={user} />
        </li>
      ))}
    </ul>
  );
}

// ❌ NEVER: Using index as key when list can reorder
// This causes React to re-render every item and lose local state
{users.map((user, index) => (
  <li key={index}><UserCard user={user} /></li>
))}
```

**Phase 2 — Commit:** Synchronous, cannot be interrupted.

```jsx
// The commit phase has three sub-phases:
// 1. Before mutation — read DOM (getSnapshotBeforeUpdate)
// 2. Mutation — apply DOM changes (insertions, updates, deletions)
// 3. Layout — run synchronous effects (useLayoutEffect, componentDidMount)

// After commit:
// - useEffect callbacks are scheduled (asynchronous)
// - The workInProgress tree becomes the new "current" tree
```

**Why this matters for interviews:** Understanding the two-phase model explains why:
- Side effects in render can fire multiple times (Phase 1 is interruptible → may restart)
- `useLayoutEffect` fires synchronously after DOM mutation (Phase 2)
- `useEffect` fires asynchronously after paint
- Keys are essential for list performance and state preservation

---

### Q15. How does Suspense integrate with concurrent rendering features?

**Answer:**

Suspense and concurrent rendering are deeply intertwined in React 18. Suspense boundaries define "loading states" in your component tree, while concurrent features control **how** and **when** those loading states appear.

**Suspense without concurrency (React 17 behavior):**

```jsx
// Without concurrent features, navigating shows the fallback immediately
function App() {
  const [page, setPage] = useState('home');

  return (
    <Suspense fallback={<FullPageSpinner />}>
      {page === 'home' && <Home />}
      {page === 'profile' && <Profile />} {/* Suspends while loading */}
    </Suspense>
  );
}

// User clicks "Profile" → <FullPageSpinner> appears immediately
// This is jarring — the existing content (Home) disappears
```

**Suspense WITH concurrent features (React 18):**

```jsx
import { useState, useTransition, Suspense, lazy } from 'react';

const Home = lazy(() => import('./Home'));
const Profile = lazy(() => import('./Profile'));
const Settings = lazy(() => import('./Settings'));

function App() {
  const [page, setPage] = useState('home');
  const [isPending, startTransition] = useTransition();

  const navigate = (nextPage) => {
    startTransition(() => {
      setPage(nextPage);
    });
  };

  return (
    <div>
      <nav>
        <button
          onClick={() => navigate('home')}
          disabled={isPending}
        >
          Home
        </button>
        <button
          onClick={() => navigate('profile')}
          disabled={isPending}
        >
          Profile
        </button>
        <button
          onClick={() => navigate('settings')}
          disabled={isPending}
        >
          Settings
        </button>
      </nav>

      {isPending && <TopProgressBar />}

      <div style={{ opacity: isPending ? 0.7 : 1 }}>
        <Suspense fallback={<PageSkeleton />}>
          {page === 'home' && <Home />}
          {page === 'profile' && <Profile />}
          {page === 'settings' && <Settings />}
        </Suspense>
      </div>
    </div>
  );
}
```

**What happens when user clicks "Profile":**
1. `startTransition` marks the navigation as non-urgent.
2. React starts rendering `<Profile />` in the background.
3. `<Profile />` suspends (lazy loading or data fetching).
4. Because this is a transition, React **keeps showing the current page** (Home) instead of showing the fallback spinner.
5. `isPending` becomes `true` → a progress bar and reduced opacity provide feedback.
6. Once `<Profile />` resolves, React commits the new UI atomically.

**Nested Suspense with concurrent rendering:**

```jsx
function ProfilePage() {
  return (
    <div>
      <h1>Profile</h1>
      {/* Each section can load independently */}
      <Suspense fallback={<Skeleton type="header" />}>
        <ProfileHeader />
      </Suspense>

      <Suspense fallback={<Skeleton type="posts" />}>
        <ProfilePosts />
      </Suspense>

      <Suspense fallback={<Skeleton type="friends" />}>
        <ProfileFriends />
      </Suspense>
    </div>
  );
}

// With concurrent rendering, React can:
// 1. Show ProfileHeader as soon as it's ready (even if Posts/Friends aren't)
// 2. Stream in each section independently
// 3. If wrapped in a transition, keep the old page until the "shell" is ready
```

**Key integration point:** `useTransition` + `Suspense` = the old content stays on screen during loading, with `isPending` providing feedback. Without the transition, Suspense immediately shows its fallback.

---

### Q16. How does concurrent rendering interact with race conditions and how do you handle them?

**Answer:**

Concurrent rendering naturally handles certain race conditions that developers previously needed to manage manually. When multiple transitions overlap, React automatically abandons stale renders. However, you still need to handle race conditions in asynchronous operations outside of React's render cycle.

**Race condition that concurrent rendering solves automatically:**

```jsx
import { useState, useTransition } from 'react';

function AutocompleteSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();

  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    startTransition(() => {
      // If user types "rea", "reac", "react" quickly:
      // - The transition for "rea" starts rendering
      // - User types "c" → React ABANDONS the "rea" render
      // - The transition for "reac" starts
      // - User types "t" → React ABANDONS "reac"
      // - Only "react" render completes
      // No stale results ever appear!
      setResults(filterProducts(value));
    });
  };

  return (
    <>
      <input value={query} onChange={handleChange} />
      <ResultsList results={results} isPending={isPending} />
    </>
  );
}
```

**Race condition that still needs manual handling (async fetching):**

```jsx
import { useState, useTransition, useRef, useEffect } from 'react';

function SearchWithAPI() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();

  // Track the latest request to prevent stale responses
  const latestRequestRef = useRef(0);

  const handleChange = async (e) => {
    const value = e.target.value;
    setQuery(value);

    if (!value.trim()) {
      startTransition(() => setResults([]));
      return;
    }

    const requestId = ++latestRequestRef.current;

    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(value)}`);
      const data = await response.json();

      // Only update if this is still the latest request
      // Without this check:
      // 1. User types "re" → fetch starts (takes 500ms)
      // 2. User types "react" → fetch starts (takes 100ms)
      // 3. "react" response arrives first → setResults(reactResults) ✅
      // 4. "re" response arrives later → setResults(reResults) ❌ STALE!
      if (requestId === latestRequestRef.current) {
        startTransition(() => {
          setResults(data.results);
        });
      }
    } catch (error) {
      if (requestId === latestRequestRef.current) {
        console.error('Search failed:', error);
      }
    }
  };

  return (
    <div>
      <input value={query} onChange={handleChange} />
      <div style={{ opacity: isPending ? 0.6 : 1 }}>
        {results.map((r) => <ResultItem key={r.id} result={r} />)}
      </div>
    </div>
  );
}
```

**Using AbortController for proper cleanup:**

```jsx
function useSearchWithAbort() {
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();
  const abortControllerRef = useRef(null);

  const search = useCallback(async (query) => {
    // Abort any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    if (!query.trim()) {
      startTransition(() => setResults([]));
      return;
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
        signal: controller.signal,
      });
      const data = await res.json();

      startTransition(() => {
        setResults(data.results);
      });
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Search failed:', err);
      }
    }
  }, []);

  return { results, isPending, search };
}
```

**Summary:**
- **Synchronous work** (filtering, computing): `useTransition` handles race conditions automatically by abandoning stale renders.
- **Asynchronous work** (API calls): You still need request IDs or AbortController because `fetch` runs outside of React's render cycle.

---

### Q17. What is the "tearing" problem and how does `useSyncExternalStore` solve it?

**Answer:**

**Tearing** occurs when different parts of the UI show inconsistent data from the same source during a single render. This is a problem specific to concurrent rendering.

**How tearing happens:**

```jsx
// External store (e.g., a global state manager)
let externalState = { theme: 'light', count: 0 };
const listeners = new Set();

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function updateState(newState) {
  externalState = { ...externalState, ...newState };
  listeners.forEach((l) => l());
}

// ❌ BROKEN: Direct read during concurrent render
function BrokenComponentA() {
  // React starts rendering this component → reads count: 0
  return <div>Count in A: {externalState.count}</div>;
}

function BrokenComponentB() {
  // React yields to browser (time slicing)
  // External store updates: count becomes 1
  // React resumes → reads count: 1
  return <div>Count in B: {externalState.count}</div>;
}

// Result: A shows 0, B shows 1 — TEARING!
// Both are in the same render pass but show different values
```

**`useSyncExternalStore` solves this:**

```jsx
import { useSyncExternalStore } from 'react';

// The store
let store = { theme: 'light', count: 0 };
const listeners = new Set();

function subscribe(callback) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function getSnapshot() {
  return store; // Must return immutable value
}

function getServerSnapshot() {
  return { theme: 'light', count: 0 }; // For SSR
}

function increment() {
  store = { ...store, count: store.count + 1 };
  listeners.forEach((l) => l());
}

// ✅ FIXED: useSyncExternalStore ensures consistency
function SafeComponentA() {
  const state = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  return <div>Count in A: {state.count}</div>;
}

function SafeComponentB() {
  const state = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  return <div>Count in B: {state.count}</div>;
}

// Both components ALWAYS see the same snapshot,
// even across time-sliced concurrent renders
```

**Building a full external store with `useSyncExternalStore`:**

```jsx
import { useSyncExternalStore, useCallback } from 'react';

function createStore(initialState) {
  let state = initialState;
  const listeners = new Set();

  return {
    getSnapshot: () => state,
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setState: (updater) => {
      const newState =
        typeof updater === 'function' ? updater(state) : updater;
      if (Object.is(state, newState)) return;
      state = newState;
      listeners.forEach((l) => l());
    },
  };
}

// Create a typed store
const counterStore = createStore({ count: 0, step: 1 });

// Custom hook with selector for performance
function useStore(store, selector) {
  const getSnapshot = useCallback(
    () => selector(store.getSnapshot()),
    [store, selector]
  );
  return useSyncExternalStore(store.subscribe, getSnapshot);
}

// Usage in components
function Counter() {
  const count = useStore(counterStore, (s) => s.count);
  const step = useStore(counterStore, (s) => s.step);

  return (
    <div>
      <p>Count: {count}</p>
      <p>Step: {step}</p>
      <button
        onClick={() =>
          counterStore.setState((s) => ({ ...s, count: s.count + s.step }))
        }
      >
        Increment
      </button>
    </div>
  );
}
```

**How `useSyncExternalStore` prevents tearing internally:**
1. During a concurrent render, React takes a snapshot of the store value at the start.
2. If the store changes mid-render, React detects the inconsistency.
3. React falls back to a synchronous render to guarantee all components see the same value.
4. This is why it's called "sync" external store — it forces synchronous behavior when needed for consistency.

**Interview insight:** Libraries like Redux (v8+), Zustand (v4+), and Jotai all use `useSyncExternalStore` internally to be concurrent-rendering safe.

---

### Q18. Build a dashboard with filtering that never blocks UI interaction.

**Answer:**

This is a comprehensive production scenario combining `useTransition`, `useDeferredValue`, `Suspense`, and memoization to build a real-world analytics dashboard where filtering thousands of data points never blocks user interaction.

```jsx
import {
  useState,
  useTransition,
  useDeferredValue,
  useMemo,
  memo,
  Suspense,
  lazy,
} from 'react';

// ---- Data & Types ----
const DEPARTMENTS = ['Engineering', 'Sales', 'Marketing', 'Support', 'HR'];
const STATUSES = ['Active', 'On Leave', 'Terminated'];

function generateEmployees(count) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Employee ${i + 1}`,
    department: DEPARTMENTS[i % DEPARTMENTS.length],
    status: STATUSES[i % STATUSES.length],
    salary: 40000 + Math.floor(Math.random() * 160000),
    performance: Math.round(Math.random() * 100),
    joinDate: new Date(2015 + (i % 10), i % 12, (i % 28) + 1)
      .toISOString()
      .split('T')[0],
  }));
}

const ALL_EMPLOYEES = generateEmployees(25000);

// ---- Filter Logic ----
function applyFilters(employees, filters) {
  let result = employees;

  if (filters.search) {
    const q = filters.search.toLowerCase();
    result = result.filter((e) => e.name.toLowerCase().includes(q));
  }
  if (filters.department !== 'All') {
    result = result.filter((e) => e.department === filters.department);
  }
  if (filters.status !== 'All') {
    result = result.filter((e) => e.status === filters.status);
  }
  if (filters.minSalary > 0) {
    result = result.filter((e) => e.salary >= filters.minSalary);
  }

  // Sort
  result = [...result].sort((a, b) => {
    const dir = filters.sortDir === 'asc' ? 1 : -1;
    if (filters.sortBy === 'salary') return (a.salary - b.salary) * dir;
    if (filters.sortBy === 'performance')
      return (a.performance - b.performance) * dir;
    return a.name.localeCompare(b.name) * dir;
  });

  return result;
}

// ---- Memoized Summary ----
const SummaryCards = memo(function SummaryCards({ employees }) {
  const stats = useMemo(() => {
    const total = employees.length;
    const avgSalary =
      total > 0
        ? Math.round(employees.reduce((s, e) => s + e.salary, 0) / total)
        : 0;
    const avgPerf =
      total > 0
        ? Math.round(employees.reduce((s, e) => s + e.performance, 0) / total)
        : 0;
    const deptCounts = {};
    employees.forEach((e) => {
      deptCounts[e.department] = (deptCounts[e.department] || 0) + 1;
    });
    return { total, avgSalary, avgPerf, deptCounts };
  }, [employees]);

  return (
    <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
      <Card title="Total Employees" value={stats.total.toLocaleString()} />
      <Card title="Avg Salary" value={`$${stats.avgSalary.toLocaleString()}`} />
      <Card title="Avg Performance" value={`${stats.avgPerf}%`} />
    </div>
  );
});

function Card({ title, value }) {
  return (
    <div
      style={{
        flex: 1,
        padding: 16,
        background: '#f8fafc',
        borderRadius: 8,
        border: '1px solid #e2e8f0',
      }}
    >
      <div style={{ fontSize: 13, color: '#64748b' }}>{title}</div>
      <div style={{ fontSize: 24, fontWeight: 'bold', marginTop: 4 }}>
        {value}
      </div>
    </div>
  );
}

// ---- Memoized Table (the expensive part) ----
const EmployeeTable = memo(function EmployeeTable({ employees, page }) {
  const PAGE_SIZE = 50;
  const start = page * PAGE_SIZE;
  const pageData = employees.slice(start, start + PAGE_SIZE);

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr style={{ background: '#f1f5f9' }}>
          <th style={{ textAlign: 'left', padding: 8 }}>Name</th>
          <th style={{ textAlign: 'left', padding: 8 }}>Department</th>
          <th style={{ textAlign: 'left', padding: 8 }}>Status</th>
          <th style={{ textAlign: 'right', padding: 8 }}>Salary</th>
          <th style={{ textAlign: 'right', padding: 8 }}>Performance</th>
          <th style={{ textAlign: 'left', padding: 8 }}>Joined</th>
        </tr>
      </thead>
      <tbody>
        {pageData.map((emp) => (
          <tr key={emp.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
            <td style={{ padding: 8 }}>{emp.name}</td>
            <td style={{ padding: 8 }}>{emp.department}</td>
            <td style={{ padding: 8 }}>
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: 12,
                  fontSize: 12,
                  background:
                    emp.status === 'Active'
                      ? '#dcfce7'
                      : emp.status === 'On Leave'
                        ? '#fef9c3'
                        : '#fee2e2',
                }}
              >
                {emp.status}
              </span>
            </td>
            <td style={{ padding: 8, textAlign: 'right' }}>
              ${emp.salary.toLocaleString()}
            </td>
            <td style={{ padding: 8, textAlign: 'right' }}>
              {emp.performance}%
            </td>
            <td style={{ padding: 8 }}>{emp.joinDate}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
});

// ---- Main Dashboard ----
function HRDashboard() {
  // Filter state — urgent (input stays responsive)
  const [filters, setFilters] = useState({
    search: '',
    department: 'All',
    status: 'All',
    minSalary: 0,
    sortBy: 'name',
    sortDir: 'asc',
  });
  const [page, setPage] = useState(0);
  const [isPending, startTransition] = useTransition();

  // Deferred filters for the expensive table and summary
  const deferredFilters = useDeferredValue(filters);
  const isStale = filters !== deferredFilters;

  // Expensive computation uses deferred filters
  const filteredEmployees = useMemo(
    () => applyFilters(ALL_EMPLOYEES, deferredFilters),
    [deferredFilters]
  );

  // Update a single filter key
  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    startTransition(() => {
      setPage(0); // Reset to first page on filter change
    });
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <h1>HR Dashboard — 25,000 Employees</h1>

      {/* Filter Bar — always responsive */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <input
          placeholder="Search by name..."
          value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          style={{ padding: 8, flex: 2, minWidth: 200 }}
        />
        <select
          value={filters.department}
          onChange={(e) => updateFilter('department', e.target.value)}
          style={{ padding: 8 }}
        >
          <option value="All">All Departments</option>
          {DEPARTMENTS.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <select
          value={filters.status}
          onChange={(e) => updateFilter('status', e.target.value)}
          style={{ padding: 8 }}
        >
          <option value="All">All Statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          Min Salary: ${filters.minSalary.toLocaleString()}
          <input
            type="range"
            min="0"
            max="200000"
            step="10000"
            value={filters.minSalary}
            onChange={(e) => updateFilter('minSalary', Number(e.target.value))}
          />
        </label>
      </div>

      {/* Results — opacity indicates stale data */}
      <div
        style={{
          opacity: isStale || isPending ? 0.5 : 1,
          transition: 'opacity 0.15s',
        }}
      >
        {(isStale || isPending) && (
          <div style={{ color: '#6366f1', fontWeight: 500, marginBottom: 8 }}>
            Updating dashboard...
          </div>
        )}

        <SummaryCards employees={filteredEmployees} />

        <div style={{ marginBottom: 12, color: '#64748b' }}>
          Showing {Math.min(50, filteredEmployees.length)} of{' '}
          {filteredEmployees.length.toLocaleString()} results (page {page + 1})
        </div>

        <EmployeeTable employees={filteredEmployees} page={page} />

        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button
            disabled={page === 0}
            onClick={() => startTransition(() => setPage((p) => p - 1))}
          >
            Previous
          </button>
          <button
            disabled={(page + 1) * 50 >= filteredEmployees.length}
            onClick={() => startTransition(() => setPage((p) => p + 1))}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

export default HRDashboard;
```

**Architecture decisions explained:**
1. **`useDeferredValue(filters)`** — The filter bar is always responsive because `filters` updates immediately; only the table uses the deferred version.
2. **`memo(EmployeeTable)`** — Skips re-render when deferred filters haven't changed yet.
3. **`useMemo` for filtering** — Avoids recomputation when the deferred value is still the stale one.
4. **`useTransition` for pagination** — Page changes are non-urgent so they don't block UI.
5. **Visual staleness indicator** — Comparing `filters !== deferredFilters` shows users that an update is pending.

---

### Q19. How do you profile concurrent rendering performance in a React 18 application?

**Answer:**

Profiling concurrent rendering requires understanding that React now does work across multiple frames, so traditional profiling approaches may be misleading. Here are the tools and techniques:

**1. React DevTools Profiler — Concurrent Mode Timeline:**

React DevTools (v4.24+) has a **Timeline** tab that shows exactly how React schedules and processes concurrent work:

```jsx
// Enable profiling in production for real-world measurements
// In your build config:
// webpack: resolve.alias['react-dom$'] = 'react-dom/profiling'
// Or set: schedulerProfiling = true

// Wrap your app to see Profiler data
import { Profiler } from 'react';

function App() {
  const onRender = (
    id,           // Profiler id
    phase,        // "mount" | "update" | "nested-update"
    actualDuration,  // Time spent rendering this update
    baseDuration,    // Estimated time without memoization
    startTime,       // When React began rendering
    commitTime       // When React committed
  ) => {
    // Log to analytics or performance monitoring
    console.table({
      id,
      phase,
      actualDuration: `${actualDuration.toFixed(2)}ms`,
      baseDuration: `${baseDuration.toFixed(2)}ms`,
      startTime: `${startTime.toFixed(2)}ms`,
      commitTime: `${commitTime.toFixed(2)}ms`,
      memoSavings: `${((1 - actualDuration / baseDuration) * 100).toFixed(0)}%`,
    });

    // Send to monitoring (e.g., DataDog, New Relic)
    if (actualDuration > 16) {
      // Took longer than one frame
      reportSlowRender({ id, phase, actualDuration, baseDuration });
    }
  };

  return (
    <Profiler id="Dashboard" onRender={onRender}>
      <Dashboard />
    </Profiler>
  );
}
```

**2. Custom transition performance measurement:**

```jsx
import { useState, useTransition, useEffect, useRef } from 'react';

function useTransitionWithMetrics(label) {
  const [isPending, startTransition] = useTransition();
  const startTimeRef = useRef(null);
  const prevPendingRef = useRef(false);

  useEffect(() => {
    if (isPending && !prevPendingRef.current) {
      // Transition started
      startTimeRef.current = performance.now();
      console.log(`[${label}] Transition started`);
    }

    if (!isPending && prevPendingRef.current && startTimeRef.current) {
      // Transition completed
      const duration = performance.now() - startTimeRef.current;
      console.log(`[${label}] Transition completed in ${duration.toFixed(1)}ms`);

      // Report to monitoring
      performance.measure(`transition-${label}`, {
        start: startTimeRef.current,
        duration,
      });

      startTimeRef.current = null;
    }

    prevPendingRef.current = isPending;
  }, [isPending, label]);

  return [isPending, startTransition];
}

// Usage
function SearchableList({ items }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(items);
  const [isPending, startTransition] = useTransitionWithMetrics('search-filter');

  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value);
    startTransition(() => {
      setResults(items.filter((i) => i.name.includes(value)));
    });
  };

  return (
    <>
      <input value={query} onChange={handleSearch} />
      {isPending && <span>Filtering...</span>}
      {results.map((item) => <Item key={item.id} item={item} />)}
    </>
  );
}
```

**3. Identifying when concurrent features help (or don't):**

```jsx
// Performance comparison utility
function useConcurrencyBenchmark() {
  const frameDropsRef = useRef([]);
  const rafIdRef = useRef(null);

  useEffect(() => {
    let lastFrameTime = performance.now();

    function checkFrame() {
      const now = performance.now();
      const frameDuration = now - lastFrameTime;

      // A dropped frame means >20ms between rAF callbacks (at 60fps = ~16.67ms)
      if (frameDuration > 20) {
        frameDropsRef.current.push({
          time: now,
          duration: frameDuration,
          droppedFrames: Math.floor(frameDuration / 16.67) - 1,
        });
      }

      lastFrameTime = now;
      rafIdRef.current = requestAnimationFrame(checkFrame);
    }

    rafIdRef.current = requestAnimationFrame(checkFrame);

    return () => {
      cancelAnimationFrame(rafIdRef.current);
    };
  }, []);

  const getReport = useCallback(() => {
    const drops = frameDropsRef.current;
    const total = drops.reduce((s, d) => s + d.droppedFrames, 0);
    return {
      totalDroppedFrames: total,
      longFrames: drops.length,
      worstFrame: drops.reduce(
        (max, d) => Math.max(max, d.duration),
        0
      ),
      drops: drops.slice(-10), // Last 10 drops
    };
  }, []);

  return { getReport, resetDrops: () => (frameDropsRef.current = []) };
}
```

**4. Chrome DevTools Performance tab tips for concurrent React:**
- Look for multiple short "Render" blocks spread across frames (time slicing working).
- `Task` blocks should be under 50ms (Long Task threshold).
- In the **Timings** lane, look for `useTransition` and `useDeferredValue` markers (React DevTools injects these).
- Use `performance.mark()` and `performance.measure()` around transitions for custom measurement.

**Key metrics to track:**
- **Input delay:** Time between keystroke and input updating (<50ms is good)
- **Transition duration:** Time for non-urgent update to commit (<200ms for search, <500ms for navigation)
- **Dropped frames:** Number of frames >16ms during transition (should be near 0)
- **Interaction to Next Paint (INP):** Web vital that concurrent features directly improve

---

### Q20. Real-world production scenario: Diagnosing and fixing a flickering dashboard using concurrent features.

**Answer:**

**The problem:** A production analytics dashboard flickers when users change filters. The chart and table visually disappear and reappear on every filter change, users report the app feels "broken," and the performance team has flagged high INP (Interaction to Next Paint) scores.

**Step 1 — Identify the root cause:**

```jsx
// ❌ THE BROKEN DASHBOARD (before fix)
import { useState, useEffect } from 'react';

function AnalyticsDashboard() {
  const [filters, setFilters] = useState({
    dateRange: '7d',
    metric: 'revenue',
    region: 'all',
  });
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Problem 1: Every filter change triggers loading state → content disappears
  useEffect(() => {
    setIsLoading(true); // ❌ Immediately hides content
    setData(null);      // ❌ Clears existing data

    fetch(`/api/analytics?${new URLSearchParams(filters)}`)
      .then((res) => res.json())
      .then((newData) => {
        setData(newData);
        setIsLoading(false);
      });
  }, [filters]);

  // Problem 2: No batching consideration — each setState causes a separate render
  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    // This triggers the useEffect above immediately
  };

  // Problem 3: Content completely unmounts during loading
  if (isLoading || !data) {
    return <FullPageSpinner />; // ❌ FLICKER — entire dashboard disappears
  }

  return (
    <div>
      <FilterBar filters={filters} onChange={handleFilterChange} />
      <ChartPanel data={data} />
      <DataTable data={data} />
    </div>
  );
}
```

**Problems identified:**
1. `setData(null)` + `setIsLoading(true)` causes the dashboard content to unmount
2. New data fetch starts → UI shows spinner → data arrives → UI shows content = **flicker**
3. No concurrent features — every update blocks the UI
4. No race condition handling — fast filter changes can cause stale data
5. If the chart component is expensive to render, the filter inputs feel sluggish

**Step 2 — Fix with concurrent features:**

```jsx
// ✅ THE FIXED DASHBOARD (after applying concurrent features)
import {
  useState,
  useTransition,
  useDeferredValue,
  useEffect,
  useRef,
  useMemo,
  memo,
  Suspense,
} from 'react';

// ---- Custom hook for concurrent-safe data fetching ----
function useConcurrentFetch(url) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    // Abort previous request
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    fetch(url, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((newData) => {
        // Wrap in transition so existing data stays visible
        // while React processes the new data
        startTransition(() => {
          setData(newData);
          setError(null);
        });
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err);
        }
      });

    return () => controller.abort();
  }, [url]);

  return { data, error, isPending };
}

// ---- Memoized expensive components ----
const ChartPanel = memo(function ChartPanel({ data, metric }) {
  // Expensive chart rendering with SVG/Canvas
  const chartData = useMemo(
    () => processChartData(data, metric),
    [data, metric]
  );

  return (
    <div style={{ height: 400, border: '1px solid #e2e8f0', borderRadius: 8 }}>
      {/* Chart rendering */}
      <svg viewBox="0 0 800 400">
        {chartData.map((point, i) => (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r={4}
            fill="#6366f1"
          />
        ))}
        {/* ... lines, axes, labels ... */}
      </svg>
    </div>
  );
});

const DataTable = memo(function DataTable({ data, page }) {
  const pageData = useMemo(
    () => data.rows.slice(page * 50, (page + 1) * 50),
    [data, page]
  );

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          {data.columns.map((col) => (
            <th key={col.key} style={{ padding: 8, textAlign: 'left' }}>
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {pageData.map((row, i) => (
          <tr key={row.id || i}>
            {data.columns.map((col) => (
              <td key={col.key} style={{ padding: 8 }}>{row[col.key]}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
});

// ---- Main Dashboard (fixed) ----
function AnalyticsDashboard() {
  const [filters, setFilters] = useState({
    dateRange: '7d',
    metric: 'revenue',
    region: 'all',
  });
  const [page, setPage] = useState(0);

  // Defer the filters so the filter bar stays responsive
  const deferredFilters = useDeferredValue(filters);
  const isStale = filters !== deferredFilters;

  // Build URL from deferred filters (only fetches when deferred value settles)
  const url = useMemo(
    () => `/api/analytics?${new URLSearchParams(deferredFilters)}`,
    [deferredFilters]
  );

  // Concurrent-safe fetch — keeps old data visible while new data loads
  const { data, error, isPending } = useConcurrentFetch(url);

  const handleFilterChange = (key, value) => {
    // This updates immediately — filter controls stay responsive
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h1>Analytics Dashboard</h1>
        {(isStale || isPending) && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              color: '#6366f1',
              fontSize: 14,
            }}
          >
            <span className="spinner" /> Updating...
          </div>
        )}
      </header>

      {/* Filter bar — ALWAYS responsive */}
      <FilterBar filters={filters} onChange={handleFilterChange} />

      {error && (
        <div style={{ color: '#dc2626', padding: 16 }}>
          Error loading data: {error.message}
          <button onClick={() => setFilters({ ...filters })}>Retry</button>
        </div>
      )}

      {/* Content — NEVER disappears (old data stays while new data loads) */}
      {data && (
        <div
          style={{
            opacity: isStale || isPending ? 0.6 : 1,
            transition: 'opacity 0.2s',
            pointerEvents: isPending ? 'none' : 'auto',
          }}
        >
          <ChartPanel data={data} metric={deferredFilters.metric} />

          <div style={{ marginTop: 24 }}>
            <DataTable data={data} page={page} />
            <Pagination
              page={page}
              total={data.rows.length}
              pageSize={50}
              onPageChange={setPage}
            />
          </div>
        </div>
      )}

      {/* Only show skeleton on initial load (no data yet) */}
      {!data && !error && <DashboardSkeleton />}
    </div>
  );
}

function FilterBar({ filters, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
      <select
        value={filters.dateRange}
        onChange={(e) => onChange('dateRange', e.target.value)}
      >
        <option value="1d">Last 24 hours</option>
        <option value="7d">Last 7 days</option>
        <option value="30d">Last 30 days</option>
        <option value="90d">Last 90 days</option>
      </select>
      <select
        value={filters.metric}
        onChange={(e) => onChange('metric', e.target.value)}
      >
        <option value="revenue">Revenue</option>
        <option value="users">Active Users</option>
        <option value="conversions">Conversions</option>
      </select>
      <select
        value={filters.region}
        onChange={(e) => onChange('region', e.target.value)}
      >
        <option value="all">All Regions</option>
        <option value="na">North America</option>
        <option value="eu">Europe</option>
        <option value="apac">Asia Pacific</option>
      </select>
    </div>
  );
}

function Pagination({ page, total, pageSize, onPageChange }) {
  const totalPages = Math.ceil(total / pageSize);
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
      <button disabled={page === 0} onClick={() => onPageChange(page - 1)}>
        Previous
      </button>
      <span>
        Page {page + 1} of {totalPages}
      </span>
      <button
        disabled={page >= totalPages - 1}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </button>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div style={{ opacity: 0.5 }}>
      <div
        style={{
          height: 400,
          background: '#f1f5f9',
          borderRadius: 8,
          marginBottom: 24,
        }}
      />
      <div style={{ height: 300, background: '#f1f5f9', borderRadius: 8 }} />
    </div>
  );
}

export default AnalyticsDashboard;
```

**What changed and why:**

| Issue | Before (Broken) | After (Fixed) |
|---|---|---|
| **Flickering** | `setData(null)` clears content | Old data stays visible via deferred updates |
| **Input lag** | Filters trigger immediate fetch + re-render | `useDeferredValue` keeps filter bar responsive |
| **Loading state** | Full-page spinner replaces content | Subtle opacity change + "Updating..." text |
| **Race conditions** | None handled | `AbortController` cancels stale requests |
| **Expensive re-renders** | Chart/table re-render on every keystroke | `memo` + deferred values skip unnecessary renders |
| **Skeleton flash** | Shows on every filter change | Only shows on initial load (`!data && !error`) |

**The key insight:** The flicker was caused by treating every filter change as a "fresh load" (clear data → show spinner → fetch → show data). With concurrent features, the existing content acts as the "fallback" while new data loads in the background. Users see a smooth transition instead of a jarring flash.
