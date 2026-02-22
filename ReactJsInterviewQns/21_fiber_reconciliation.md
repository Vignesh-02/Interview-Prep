# React Fiber & Reconciliation Deep Dive — React 18 Interview Questions

## Topic Introduction

**React Fiber** is the complete rewrite of React's core reconciliation engine, introduced in React 16 and fully leveraged in React 18's concurrent features. The original "stack reconciler" processed component trees synchronously in a single, uninterruptible pass — once rendering started, the main thread was blocked until every component in the subtree had been processed. This was acceptable for small applications but catastrophic for complex UIs: a large tree update could lock the browser for hundreds of milliseconds, dropping frames and making inputs feel sluggish. Fiber replaces this architecture with an incremental, interruptible work loop. Each unit of work is represented by a **fiber node** — a mutable JavaScript object that holds information about a component, its input (props), its output (rendered elements), its position in the tree, and its pending state changes. Because each fiber is a plain object linked to its parent, child, and sibling via pointers (forming a singly-linked list / tree hybrid), React can pause in the middle of a tree traversal, yield control back to the browser for high-priority tasks like animations or input handling, and then resume exactly where it left off. This is the foundation that makes React 18's `startTransition`, `useDeferredValue`, Suspense streaming, and selective hydration possible.

**Reconciliation** is the algorithm React uses to determine the minimal set of DOM mutations needed when state or props change. When you call `setState` or a hook dispatcher, React does not immediately touch the DOM. Instead, it builds a new tree of React elements (the "virtual DOM") via your render functions and then **diffs** this new tree against the current fiber tree. This diff is governed by two heuristics that reduce the comparison from O(n³) to O(n): (1) elements of different **types** produce entirely different subtrees and are fully unmounted/remounted, and (2) the developer can hint at stable identity across renders using **keys**. Fiber enhances this by splitting the work into two distinct phases — the **render phase** (pure, interruptible, side-effect-free) where React walks the tree, calls your components, and computes what changed, and the **commit phase** (synchronous, uninterruptible) where React applies those mutations to the real DOM, runs refs, and fires layout effects. Understanding this two-phase architecture, the role of priority lanes, the double-buffering technique (current tree vs. work-in-progress tree), and how effects are scheduled is essential for diagnosing performance issues, writing correct concurrent-safe code, and passing senior-level React interviews.

```jsx
// A mental model: React Fiber turns your component tree into a linked-list of work units

// Imagine this JSX tree:
function App() {
  return (
    <div>
      <Header />
      <Main>
        <Sidebar />
        <Content />
      </Main>
      <Footer />
    </div>
  );
}

// React Fiber internally represents it as linked fiber nodes:
//
//   App (fiber)
//    |
//    div (child)
//    |
//   Header (child) --> Main (sibling) --> Footer (sibling)
//                       |
//                     Sidebar (child) --> Content (sibling)
//
// Each fiber node has: child (first child), sibling (next sibling), return (parent)
// React walks this structure using a depth-first work loop:
//   beginWork(App) → beginWork(div) → beginWork(Header) → completeWork(Header)
//   → beginWork(Main) → beginWork(Sidebar) → completeWork(Sidebar)
//   → beginWork(Content) → completeWork(Content) → completeWork(Main)
//   → beginWork(Footer) → completeWork(Footer) → completeWork(div) → completeWork(App)
//
// At any "→" arrow, React can PAUSE and yield to the browser if using concurrent mode.
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is the Virtual DOM and why does React use it?

**Answer:**

The **Virtual DOM (VDOM)** is a lightweight, in-memory JavaScript representation of the actual browser DOM. When you write JSX, React doesn't create real DOM nodes directly. Instead, your component's render output produces a tree of plain JavaScript objects — React elements — that describe *what* the UI should look like. This element tree is often referred to as the "virtual DOM."

React uses the VDOM because direct DOM manipulation is expensive. Reading `offsetHeight`, appending children, or changing `innerHTML` triggers browser layout recalculations (reflow) and repaints. By diffing two virtual trees first and computing the **minimal** set of real DOM operations, React avoids unnecessary work. This approach also decouples your component logic from the rendering target — the same virtual tree can be rendered to the browser DOM (`react-dom`), native mobile views (`react-native`), or even a string (`react-dom/server`).

**Important nuance for interviews:** The VDOM is *not* inherently faster than hand-tuned imperative DOM code. Its value lies in the **developer experience** — you describe *what* you want declaratively and React figures out *how* to get there efficiently, which is a better tradeoff for large applications than micromanaging every DOM mutation.

```jsx
// When you write this component:
function UserCard({ name, email }) {
  return (
    <div className="card">
      <h2>{name}</h2>
      <p>{email}</p>
    </div>
  );
}

// React internally creates an element tree (the "virtual DOM") like:
// {
//   type: 'div',
//   props: {
//     className: 'card',
//     children: [
//       { type: 'h2', props: { children: 'Alice' } },
//       { type: 'p',  props: { children: 'alice@example.com' } }
//     ]
//   }
// }

// On the next render, if only `email` changed:
// React diffs old VDOM vs new VDOM → finds only the <p> text changed
// → issues a single DOM text node update instead of rebuilding the entire card.
```

---

### Q2. What is reconciliation — how does React's diffing process work?

**Answer:**

**Reconciliation** is the algorithm React uses to compare the previous element tree with the new one and determine the minimum number of operations to transform the real DOM from its current state to the desired state. A naive tree diff algorithm runs in O(n³) time, which is impractical for UI trees with hundreds or thousands of nodes. React solves this by relying on two heuristics:

1. **Different types → full remount.** If the root element type changes (e.g., `<div>` becomes `<section>`, or `<UserCard>` becomes `<AdminCard>`), React tears down the entire old subtree (unmounts it, destroys DOM nodes and state) and builds the new one from scratch. It does not attempt to diff children across type boundaries.

2. **Keys identify stable children.** When diffing lists of children, React uses the `key` prop to match old children with new children. Without keys, React compares children positionally (index 0 vs index 0, etc.). With keys, React can detect insertions, deletions, and reorderings efficiently.

Within same-type elements, React compares old and new props, updates only the changed attributes on the DOM node, and then recurses into children.

```jsx
// Heuristic 1 — Type change triggers unmount + remount
function App({ isAdmin }) {
  // When isAdmin toggles, React UNMOUNTS one and MOUNTS the other.
  // All internal state in the old component is destroyed.
  return isAdmin ? <AdminDashboard /> : <UserDashboard />;
}

// Heuristic 2 — Same type triggers prop update (no remount)
function App({ theme }) {
  // When theme changes from "light" to "dark", React keeps the same
  // <div> DOM node and only updates the className attribute.
  return <div className={theme}>Hello</div>;
}

// List diffing — keys allow React to track identity
function TodoList({ items }) {
  return (
    <ul>
      {items.map((item) => (
        // With key={item.id}, React can reorder existing DOM nodes
        // rather than destroying and recreating them.
        <li key={item.id}>{item.text}</li>
      ))}
    </ul>
  );
}
```

---

### Q3. What is React Fiber and why did it replace the stack reconciler?

**Answer:**

**React Fiber** is the name for React's reimplemented reconciliation engine, shipped in React 16. The term "Fiber" refers to both the architecture and the individual data structure (a "fiber node") that represents a unit of work.

The **old stack reconciler** used the JavaScript call stack to traverse the component tree. It worked like a recursive function: `render(App)` calls `render(div)` calls `render(Header)` and so on. Because the call stack is all-or-nothing, React could not pause partway through rendering a large tree. If rendering 10,000 list items took 200ms, the main thread was blocked for the entire 200ms — animations froze, user input was queued, and the UI felt unresponsive.

**Fiber solves this** by replacing the implicit call stack with an explicit linked-list data structure. Each fiber node is a JavaScript object that stores: the component type, its state, its props, pointers to child/sibling/parent fibers, and any pending effects. React's work loop iterates through these nodes one at a time. After processing each fiber, React can check `shouldYield()` — a function that returns `true` if the browser needs the main thread back (e.g., for an input event or animation frame). If it should yield, React saves its position and returns control to the browser. It resumes later from exactly where it paused.

This interruptibility is what enables **concurrent rendering** in React 18 — transitions, Suspense, streaming SSR, and selective hydration all depend on Fiber's ability to pause, prioritize, and resume work.

```jsx
// Conceptual: the old stack reconciler (simplified pseudocode)
function reconcile(element) {
  // This is a BLOCKING recursive walk — no way to pause.
  const dom = createDomNode(element);
  element.children.forEach((child) => {
    dom.appendChild(reconcile(child)); // recursive call on the JS call stack
  });
  return dom;
}

// Conceptual: the Fiber work loop (simplified pseudocode)
function workLoop(deadline) {
  let fiber = nextUnitOfWork;

  while (fiber && !shouldYield()) {
    // Process ONE fiber node
    fiber = performUnitOfWork(fiber);
  }

  if (fiber) {
    // More work remains — schedule a callback to continue later
    requestIdleCallback(workLoop);
  } else {
    // All work done — commit changes to the DOM in one synchronous pass
    commitRoot();
  }
}

// The key insight: React controls the "call stack" manually via the fiber
// linked list, so it can pause/resume at will.
```

---

### Q4. What does a fiber node look like — what are its key properties?

**Answer:**

A **fiber node** is a plain JavaScript object that represents a single unit of work in the React tree. Every React element (host DOM node, function component, class component, fragment, portal, etc.) gets a corresponding fiber. Fiber nodes are **mutable** and **persistent** — React reuses and updates them across renders rather than creating new ones each time (unlike React elements, which are recreated on every render).

Key properties of a fiber node:

| Property | Description |
|---|---|
| `tag` | Numeric tag identifying the fiber type (FunctionComponent = 0, ClassComponent = 1, HostComponent = 5, etc.) |
| `type` | The component function/class or DOM tag string (e.g., `MyComponent` or `'div'`) |
| `key` | The React key from JSX, used during reconciliation |
| `stateNode` | For host components: the actual DOM node. For class components: the class instance. For function components: `null` |
| `child` | Pointer to the first child fiber |
| `sibling` | Pointer to the next sibling fiber |
| `return` | Pointer to the parent fiber (called "return" because it's where control returns after processing this fiber) |
| `pendingProps` | Props from the new element tree (incoming) |
| `memoizedProps` | Props from the last completed render |
| `memoizedState` | State from the last completed render (for hooks: the linked list of hook states) |
| `flags` | Bitmask of side effects (Placement, Update, Deletion, etc.) |
| `lanes` | Priority lanes assigned to pending work on this fiber |
| `alternate` | Pointer to the counterpart fiber in the other tree (current ↔ work-in-progress) |

```jsx
// Imagine this component tree:
function App() {
  const [count, setCount] = useState(0);
  return (
    <div id="root">
      <span>{count}</span>
      <button onClick={() => setCount(count + 1)}>+</button>
    </div>
  );
}

// The fiber tree (conceptual) looks like:
//
// FiberNode {
//   tag: FunctionComponent,
//   type: App,
//   stateNode: null,               // function components have no instance
//   memoizedState: { queue: ..., next: null },  // useState hook
//   child: ──→ FiberNode {
//                tag: HostComponent,
//                type: 'div',
//                stateNode: <div id="root">,   // real DOM node
//                child: ──→ FiberNode {
//                             tag: HostComponent,
//                             type: 'span',
//                             stateNode: <span>,
//                             sibling: ──→ FiberNode {
//                                            tag: HostComponent,
//                                            type: 'button',
//                                            stateNode: <button>,
//                                          }
//                           }
//              }
// }
//
// Navigation: child goes DOWN, sibling goes RIGHT, return goes UP.
```

---

### Q5. What are the two phases of rendering in React Fiber — render phase vs. commit phase?

**Answer:**

React Fiber splits the work of updating the UI into two distinct phases:

**1. Render Phase (also called "reconciliation phase")**
- This is where React walks the fiber tree, calls your component functions (or class render methods), diffs old vs. new elements, and computes what needs to change.
- This phase is **pure** — it should have no observable side effects (no DOM mutations, no subscriptions, no network calls).
- In concurrent mode, this phase is **interruptible** — React can pause, abort, or restart rendering without the user noticing, because no side effects have been committed yet.
- React may call your component function **more than once** for a single update (this is why React 18 Strict Mode double-invokes renders in development).

**2. Commit Phase**
- After the render phase completes, React has a list of fibers tagged with side-effect flags (Placement, Update, Deletion).
- The commit phase walks this list and applies mutations to the real DOM **synchronously** — it cannot be interrupted.
- The commit phase has three sub-phases: (a) **Before mutation** — read DOM snapshots via `getSnapshotBeforeUpdate`, (b) **Mutation** — insert, update, or remove DOM nodes, (c) **Layout** — run `useLayoutEffect` callbacks and `componentDidMount`/`componentDidUpdate`, attach refs.
- After the commit phase, `useEffect` callbacks are scheduled asynchronously (they run after the browser has painted).

```jsx
import { useState, useEffect, useLayoutEffect } from 'react';

function Timer() {
  const [seconds, setSeconds] = useState(0);

  // ── RENDER PHASE ──
  // Everything above the return and the return itself runs during render.
  // This must be pure — no DOM mutations, no subscriptions.
  console.log('Render phase: computing UI for seconds =', seconds);

  const display = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;

  // ── COMMIT PHASE (layout sub-phase) ──
  useLayoutEffect(() => {
    // Runs synchronously AFTER DOM mutation but BEFORE browser paint.
    // Use for measurements that need to be reflected before the user sees anything.
    console.log('Commit phase (layout): DOM is updated, before paint');
  });

  // ── AFTER COMMIT (asynchronous) ──
  useEffect(() => {
    // Runs AFTER the browser has painted.
    // Safe for subscriptions, data fetching, timers.
    console.log('Post-commit: browser has painted, setting up timer');
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);

  return <h1>{display}</h1>;
}

// Execution order on mount:
// 1. "Render phase: computing UI for seconds = 0"     ← render phase
// 2. DOM is created/updated                             ← commit (mutation sub-phase)
// 3. "Commit phase (layout): DOM is updated..."         ← commit (layout sub-phase)
// 4. Browser paints pixels to screen
// 5. "Post-commit: browser has painted..."              ← useEffect runs
```

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do keys affect the diffing algorithm and why do keys matter for lists?

**Answer:**

When React reconciles a list of children, it needs to match old children to new children to determine which were added, removed, or moved. Without keys, React uses **positional matching** — it compares the child at index 0 with the new child at index 0, index 1 with index 1, and so on. This is efficient for static lists that don't reorder, but it leads to **incorrect behavior and wasted work** when items are inserted, removed, or reordered.

With `key` props, React builds a **map** of old children keyed by their `key` value. For each new child, it looks up the old fiber by key. If found, React reuses the fiber (and its associated DOM node and state), moving it to the correct position. If not found, React creates a new fiber. Old fibers with keys not present in the new list are deleted.

**Why `index` as key is dangerous:** When you use the array index as key and an item is inserted at the beginning, every item's key shifts (item that was key=0 is now key=1, etc.). React sees key=0 as the "same" element and tries to update it in place — which means it patches the wrong component with the wrong props, potentially preserving stale state from the wrong item.

```jsx
import { useState } from 'react';

// ❌ BAD: Using index as key — inserting at top breaks state
function BadList() {
  const [items, setItems] = useState([
    { id: 'a', text: 'Apple' },
    { id: 'b', text: 'Banana' },
  ]);

  const addToTop = () => {
    setItems([{ id: 'c', text: 'Cherry' }, ...items]);
  };

  return (
    <div>
      <button onClick={addToTop}>Add Cherry to top</button>
      <ul>
        {items.map((item, index) => (
          // key={index} means: after adding Cherry at top,
          // React thinks key=0 ("Cherry") is the same element as old key=0 ("Apple").
          // It UPDATES Apple's fiber with Cherry's props — but any internal
          // state (e.g., a checked checkbox) from Apple stays with key=0!
          <li key={index}>
            <input type="checkbox" /> {item.text}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ✅ GOOD: Using stable unique ID as key
function GoodList() {
  const [items, setItems] = useState([
    { id: 'a', text: 'Apple' },
    { id: 'b', text: 'Banana' },
  ]);

  const addToTop = () => {
    setItems([{ id: 'c', text: 'Cherry' }, ...items]);
  };

  return (
    <div>
      <button onClick={addToTop}>Add Cherry to top</button>
      <ul>
        {items.map((item) => (
          // key={item.id} means: React correctly identifies Cherry as NEW,
          // Apple and Banana as EXISTING (just moved). Checkbox state is preserved
          // correctly with the right items.
          <li key={item.id}>
            <input type="checkbox" /> {item.text}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

### Q7. When does React remount a component vs. update it in place — how do element types affect reconciliation?

**Answer:**

React's core reconciliation rule: **if the element type at a given position in the tree changes, React destroys the entire old subtree and builds a new one from scratch.** If the type stays the same, React updates the existing fiber in place (patching props and recursing into children).

This applies to both host elements and component elements:
- `<div>` → `<section>`: different host types → remount
- `<UserCard>` → `<AdminCard>`: different component types → remount (even if they render identical JSX)
- `<UserCard>` → `<UserCard>`: same type → update props, keep state

A critical pitfall is **defining components inside other components**. Each render creates a new function reference, so React sees a "new" component type every time and **remounts** instead of updating.

```jsx
import { useState } from 'react';

// ❌ BAD: Component defined inside another component
function Parent() {
  const [count, setCount] = useState(0);

  // This creates a NEW function reference every render.
  // React sees a different "type" each time → unmounts and remounts Input.
  // The text typed into the input is LOST on every count change.
  function Input() {
    return <input placeholder="Type here..." />;
  }

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Count: {count}</button>
      <Input />
    </div>
  );
}

// ✅ GOOD: Component defined outside
function StableInput() {
  return <input placeholder="Type here..." />;
}

function Parent() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Count: {count}</button>
      {/* Same function reference every render → React updates in place */}
      <StableInput />
    </div>
  );
}

// Another common scenario: conditional rendering that changes type
function Profile({ user }) {
  // ❌ This remounts the entire form when isEditing toggles
  // because <EditForm> and <ViewProfile> are different types.
  const [isEditing, setIsEditing] = useState(false);

  return isEditing ? (
    <EditForm user={user} onSave={() => setIsEditing(false)} />
  ) : (
    <ViewProfile user={user} onEdit={() => setIsEditing(true)} />
  );
  // If you need to preserve state across these, lift state up or use a
  // single component that switches its rendering based on a prop.
}
```

---

### Q8. How do `shouldComponentUpdate`, `React.memo`, and `PureComponent` bail out of reconciliation?

**Answer:**

React provides several mechanisms to **skip re-rendering** a component when its output would not change. This is called "bailing out" of reconciliation — React stops the diffing process for that subtree.

- **`shouldComponentUpdate(nextProps, nextState)`** — class component lifecycle method. Return `false` to tell React to skip rendering this component and all its children.
- **`React.PureComponent`** — a class component base that implements `shouldComponentUpdate` with a **shallow comparison** of props and state.
- **`React.memo(Component, arePropsEqual?)`** — the functional component equivalent. Wraps a component so React skips re-rendering if props haven't changed (shallow comparison by default, or a custom comparator).

When React bails out, it does not call the component's render function, does not diff its children, and reuses the previous fiber subtree as-is. This can yield massive performance wins for expensive subtrees — but incorrect use (e.g., mutating objects) can cause stale renders.

```jsx
import { memo, useState, useCallback, useMemo } from 'react';

// An expensive list component — we want to avoid unnecessary re-renders
const ExpensiveList = memo(function ExpensiveList({ items, onSelect }) {
  console.log('ExpensiveList rendered — this should be rare');
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id} onClick={() => onSelect(item.id)}>
          {item.name}
        </li>
      ))}
    </ul>
  );
});

function Dashboard() {
  const [search, setSearch] = useState('');
  const [items] = useState([
    { id: 1, name: 'Revenue Report' },
    { id: 2, name: 'User Analytics' },
    { id: 3, name: 'System Health' },
  ]);

  // ❌ Without useCallback, a new function is created every render.
  // React.memo sees onSelect as a new prop → ExpensiveList re-renders.
  // const onSelect = (id) => console.log('Selected:', id);

  // ✅ Stabilize the callback reference so memo can bail out
  const onSelect = useCallback((id) => {
    console.log('Selected:', id);
  }, []);

  // ✅ Stabilize the items reference if it's derived from computation
  const filteredItems = useMemo(
    () => items.filter((i) => i.name.toLowerCase().includes(search.toLowerCase())),
    [items, search]
  );

  return (
    <div>
      {/* Typing in the search input causes Dashboard to re-render */}
      <input value={search} onChange={(e) => setSearch(e.target.value)} />

      {/* With memo + stable props, ExpensiveList only re-renders when
          filteredItems actually changes (search changed), not on every
          keystroke if search doesn't affect the filter result. */}
      <ExpensiveList items={filteredItems} onSelect={onSelect} />
    </div>
  );
}

// Custom comparator example — deep comparison of specific props
const ChartWidget = memo(
  function ChartWidget({ data, config }) {
    console.log('ChartWidget rendered');
    return <canvas data-config={JSON.stringify(config)} />;
  },
  (prevProps, nextProps) => {
    // Return true to SKIP re-render, false to allow it
    return (
      prevProps.data.length === nextProps.data.length &&
      prevProps.data.every((d, i) => d.value === nextProps.data[i].value) &&
      prevProps.config.type === nextProps.config.type
    );
  }
);
```

---

### Q9. What is the "double buffering" technique in Fiber — current tree vs. work-in-progress tree?

**Answer:**

React Fiber maintains **two fiber trees** at any given time — an approach borrowed from graphics programming called **double buffering**:

1. **Current tree** — the fiber tree that is currently rendered on screen. It represents the committed state of the UI. Every fiber node in the current tree has an `alternate` pointer to its counterpart in the work-in-progress tree (and vice versa).

2. **Work-in-progress (WIP) tree** — a draft copy that React builds during the render phase. React clones fibers from the current tree, applies updates (new props, new state), and diffs the output. If rendering is interrupted (in concurrent mode), the WIP tree can be discarded without affecting the on-screen UI.

When the render phase completes and the commit phase finishes, React **swaps the pointer** — the WIP tree becomes the new current tree, and the old current tree becomes available for reuse as the next WIP tree. This pointer swap is essentially one assignment (`fiberRoot.current = wipRoot`), making the "flip" instantaneous.

This technique ensures that the user never sees a half-rendered UI. All mutations are computed on the WIP tree, and only after everything is consistent does React commit it to the screen.

```jsx
// Conceptual illustration of double buffering

// Before update:
// ┌─────────────────┐       ┌─────────────────┐
// │  CURRENT TREE   │  alt  │   WIP TREE       │
// │  (on screen)    │◄─────►│   (not used yet)  │
// │                 │       │                   │
// │  App            │       │  App (clone)      │
// │   ├─ Header     │       │   ├─ Header       │
// │   └─ Content    │       │   └─ Content      │
// │       count: 5  │       │       count: 5    │
// └─────────────────┘       └─────────────────┘

// User clicks increment → React starts building WIP tree:
// ┌─────────────────┐       ┌─────────────────┐
// │  CURRENT TREE   │  alt  │   WIP TREE       │
// │  (still on      │◄─────►│   (building...)   │
// │   screen)       │       │                   │
// │  App            │       │  App (re-rendered) │
// │   ├─ Header     │       │   ├─ Header (reused — no change) │
// │   └─ Content    │       │   └─ Content      │
// │       count: 5  │       │       count: 6 ← updated │
// └─────────────────┘       └─────────────────┘

// After commit phase — pointer swap:
// ┌─────────────────┐       ┌─────────────────┐
// │  OLD TREE       │  alt  │  CURRENT TREE    │
// │  (recyclable)   │◄─────►│  (now on screen)  │
// │  App            │       │  App              │
// │   ├─ Header     │       │   ├─ Header       │
// │   └─ Content    │       │   └─ Content      │
// │       count: 5  │       │       count: 6    │
// └─────────────────┘       └─────────────────┘

// In code, the swap is just:
// fiberRootNode.current = finishedWork;

// Production implication: React.StrictMode double-renders in dev to help
// catch impure render logic — because in concurrent mode, React may
// discard and rebuild the WIP tree at any time.
import { StrictMode } from 'react';

function App() {
  // This will log twice in development (StrictMode) to simulate
  // the "discard WIP and re-render" behavior.
  console.log('App rendering');
  return <div>My App</div>;
}

// root.render(
//   <StrictMode>
//     <App />
//   </StrictMode>
// );
```

---

### Q10. What is time slicing and how does React break rendering into chunks?

**Answer:**

**Time slicing** is the technique React uses (in concurrent mode) to break a long rendering task into small chunks, yielding control back to the browser's main thread between chunks. This prevents large updates from blocking user interactions, animations, and other high-priority browser tasks.

Here's how it works under the hood:

1. React schedules work using its own **scheduler** (the `scheduler` package). It posts a callback via `MessageChannel` (not `requestIdleCallback` in production — that has issues with tab backgrounding and inconsistent timing).
2. The work loop picks up the next fiber and processes it (`performUnitOfWork`).
3. After each unit of work, React checks `shouldYield()`, which returns `true` if the allotted time slice (~5ms) has elapsed.
4. If `shouldYield()` is `true` and the current work is **interruptible** (i.e., part of a transition or deferred update), React pauses the work loop and posts a new callback to resume later.
5. The browser gets a chance to handle events, paint frames, and run other tasks.
6. The next callback picks up where React left off.

**Critical detail:** Not all renders are interruptible. Updates from `setState` inside event handlers are **synchronous** by default in React 18 (they go through the default `SyncLane`). Only updates wrapped in `startTransition` or `useDeferredValue` use concurrent lanes that support time slicing.

```jsx
import { useState, useTransition } from 'react';

// Production scenario: filtering a list of 10,000 items
function HeavyFilterableList({ allItems }) {
  const [query, setQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState(allItems);
  const [isPending, startTransition] = useTransition();

  const handleSearch = (e) => {
    const value = e.target.value;

    // This update is synchronous — input stays responsive
    setQuery(value);

    // This update is wrapped in startTransition — React can time-slice it.
    // If the user types another character before filtering completes,
    // React ABORTS the in-progress WIP tree and starts a new one.
    startTransition(() => {
      const result = allItems.filter((item) =>
        item.name.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredItems(result);
    });
  };

  return (
    <div>
      <input value={query} onChange={handleSearch} placeholder="Search..." />
      {isPending && <span>Filtering...</span>}
      <ul style={{ opacity: isPending ? 0.7 : 1 }}>
        {filteredItems.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}

// Without startTransition: typing "abc" quickly causes 3 synchronous
// filter operations that block the main thread — input feels laggy.
//
// With startTransition: each keystroke's filter is interruptible.
// React yields between fiber units, keeping input at 60fps.
// If "a" filter is still running when "b" is typed, React discards
// the "a" WIP tree and starts fresh with "ab".
```

---

### Q11. How does React assign priorities using lanes — what is the lanes model?

**Answer:**

**Lanes** are React 18's priority system for scheduling updates. They replaced the earlier "expiration time" model and are represented as **bitmasks** — each lane is a single bit in a 31-bit integer. This allows React to efficiently combine, compare, and subset priorities using bitwise operations.

Key lanes (from highest to lowest priority):

| Lane | Bit | Used For |
|---|---|---|
| `SyncLane` | `0b0000000000000000000000000000010` | `flushSync`, legacy sync updates |
| `InputContinuousLane` | `0b0000000000000000000000000001000` | Continuous input events (drag, scroll) |
| `DefaultLane` | `0b0000000000000000000000000100000` | Normal `setState` in event handlers |
| `TransitionLanes` | Multiple bits | `startTransition` updates (interruptible) |
| `IdleLane` | `0b0100000000000000000000000000000` | `useDeferredValue`, offscreen work |

When an update is dispatched, React assigns it a lane based on the context:
- `setState` in a click handler → `DefaultLane`
- `setState` inside `startTransition` → one of the `TransitionLanes`
- `flushSync(() => setState(...))` → `SyncLane`

During the work loop, React processes the **highest-priority pending lane first**. If a higher-priority update arrives while React is rendering a lower-priority transition, React **interrupts** the current render, processes the high-priority update, commits it, and then restarts the transition.

```jsx
import { useState, useTransition, startTransition } from 'react';
import { flushSync } from 'react-dom';

function PriorityDemo() {
  const [urgent, setUrgent] = useState('');
  const [list, setList] = useState([]);
  const [isPending, startT] = useTransition();

  const handleChange = (e) => {
    const value = e.target.value;

    // HIGH PRIORITY (DefaultLane) — input updates immediately
    setUrgent(value);

    // LOW PRIORITY (TransitionLane) — list update is interruptible
    startT(() => {
      // Imagine this triggers expensive child renders
      setList(generateHugeList(value));
    });
  };

  const handleCriticalAction = () => {
    // HIGHEST PRIORITY (SyncLane) — bypasses batching, flushes immediately
    flushSync(() => {
      setUrgent('CRITICAL');
    });
    // DOM is guaranteed to be updated by this line
    console.log(document.getElementById('display').textContent); // "CRITICAL"
  };

  return (
    <div>
      <input value={urgent} onChange={handleChange} />
      <span id="display">{urgent}</span>
      <button onClick={handleCriticalAction}>Critical Update</button>
      <div style={{ opacity: isPending ? 0.5 : 1 }}>
        {list.map((item, i) => (
          <div key={i}>{item}</div>
        ))}
      </div>
    </div>
  );
}

// Lane assignment pseudocode (simplified from React source):
// function requestUpdateLane() {
//   if (isInsideFlushSync)        return SyncLane;        // 0b10
//   if (isInsideTransition)       return claimTransitionLane(); // 0b01000000...
//   if (isContinuousInputEvent)   return InputContinuousLane;
//   return DefaultLane;                                     // 0b100000
// }
//
// React merges lanes with bitwise OR:
//   pendingLanes |= updateLane;
//
// And checks inclusion with bitwise AND:
//   if (pendingLanes & SyncLane) { /* sync work exists */ }
```

---

### Q12. How are effects scheduled in Fiber — the lifecycle of `useEffect` and `useLayoutEffect`?

**Answer:**

Effects in React Fiber are not plain function calls — they are **tagged on fiber nodes** during the render phase and **executed during or after the commit phase** based on their type.

**During the render phase:**
- When React processes a fiber and encounters a `useEffect` or `useLayoutEffect` hook, it creates an **effect object** and appends it to the fiber's `updateQueue`.
- The effect is flagged (e.g., `HookHasEffect | HookPassive` for `useEffect`, `HookHasEffect | HookLayout` for `useLayoutEffect`).
- No effect callback runs during the render phase.

**During the commit phase:**

1. **Before Mutation** — `getSnapshotBeforeUpdate` (class only). DOM is still the old version.
2. **Mutation sub-phase** — React applies DOM insertions, updates, and deletions. Previous `useLayoutEffect` **cleanup** functions run here (for updates/unmounts).
3. **Layout sub-phase** — `useLayoutEffect` **setup** callbacks run synchronously. Refs are attached. `componentDidMount` / `componentDidUpdate` fire. The DOM is updated but the browser has **not yet painted**.
4. **After commit (asynchronous)** — React schedules `useEffect` cleanup and setup callbacks to run after the browser has painted. They are batched and flushed asynchronously, typically before the next frame.

**Why this matters in production:** If you measure DOM dimensions or synchronously adjust scroll position, you must use `useLayoutEffect` to avoid visual flicker. But heavy computation in `useLayoutEffect` blocks painting and causes jank.

```jsx
import { useState, useEffect, useLayoutEffect, useRef } from 'react';

// Production example: auto-resizing textarea
function AutoResizeTextarea({ value, onChange }) {
  const textareaRef = useRef(null);
  const [height, setHeight] = useState('auto');

  // useLayoutEffect: runs synchronously AFTER DOM mutation, BEFORE paint.
  // Perfect for measuring DOM and adjusting layout to prevent flicker.
  useLayoutEffect(() => {
    const el = textareaRef.current;
    // Reset height to auto to get the correct scrollHeight
    el.style.height = 'auto';
    const scrollHeight = el.scrollHeight;
    setHeight(`${scrollHeight}px`);
    // Because this runs before paint, the user never sees the textarea
    // at the wrong height.
  }, [value]);

  // useEffect: runs AFTER paint. Good for side effects that don't affect layout.
  useEffect(() => {
    // Analytics, logging, or API calls
    console.log('Textarea value changed, length:', value.length);
  }, [value]);

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={onChange}
      style={{ height, overflow: 'hidden', resize: 'none' }}
    />
  );
}

// Execution order when `value` changes:
// 1. Render phase: React calls AutoResizeTextarea, creates new elements
// 2. Commit — Mutation: DOM text content updated; previous useLayoutEffect cleanup runs
// 3. Commit — Layout: useLayoutEffect fires → measures scrollHeight → calls setHeight
//    (setHeight triggers a synchronous re-render within the commit phase!)
// 4. Re-render with new height → commit again (DOM height attribute updated)
// 5. Browser paints (user sees textarea at correct height — no flicker)
// 6. useEffect fires → logs to console

// Cleanup order for effects:
useEffect(() => {
  const subscription = dataSource.subscribe(handleChange);
  console.log('Effect setup');

  return () => {
    subscription.unsubscribe();
    console.log('Effect cleanup');
  };
}, [dataSource]);

// On re-render with new dataSource:
// 1. New render completes
// 2. Old cleanup runs: "Effect cleanup" (unsubscribes from OLD dataSource)
// 3. New setup runs:   "Effect setup"   (subscribes to NEW dataSource)
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How does Fiber enable concurrent rendering — interruptible rendering in depth?

**Answer:**

Concurrent rendering is Fiber's flagship capability. It means React can work on multiple versions of the UI simultaneously, interrupt low-priority work to handle urgent updates, and present a consistent UI without tearing.

**The mechanics:**

1. **Cooperative scheduling:** React's work loop calls `performUnitOfWork(fiber)` in a `while` loop. Each iteration processes one fiber node (calling the component function, diffing children). Between iterations, React calls `shouldYield()` which checks if the current time slice (~5ms) has elapsed. If yes, React exits the loop, saving `workInProgress` as a module-level variable.

2. **Resumable work:** Because the fiber tree is a linked list (not the JS call stack), React can resume from `workInProgress` in the next time slice. It just calls `workLoop()` again, and the `while` loop picks up where it left off.

3. **Interruption and restart:** If a high-priority update arrives (e.g., user types while a transition is rendering), React checks if `pendingLanes` includes a higher-priority lane than what it's currently rendering. If so, it **abandons** the current WIP tree (simply stops processing it) and starts a new render pass for the high-priority update. The abandoned WIP tree is garbage collected.

4. **No tearing guarantee:** React ensures that a single commit never mixes state from different updates. The render phase builds a complete, consistent snapshot. The commit phase applies it atomically. `useSyncExternalStore` exists specifically to prevent tearing with external stores that might change during an interruptible render.

```jsx
import { useState, useTransition, useSyncExternalStore } from 'react';

// Demonstrating interruptible rendering with transitions
function SearchApp() {
  const [input, setInput] = useState('');
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();

  const handleInput = (e) => {
    const val = e.target.value;
    // Urgent: update input field immediately (SyncLane / DefaultLane)
    setInput(val);

    // Non-urgent: filter results (TransitionLane — interruptible)
    startTransition(() => {
      // If user types again before this completes, React INTERRUPTS this
      // render and starts fresh with the new input value.
      // The WIP tree for the old value is discarded.
      setResults(heavySearch(val));
    });
  };

  return (
    <div>
      <input value={input} onChange={handleInput} />
      {isPending ? <Spinner /> : <ResultsList results={results} />}
    </div>
  );
}

// Preventing tearing with external stores
// If you read from a mutable external store during a concurrent render,
// the store might change between the start and end of the render,
// causing different components to see different values (tearing).

const externalStore = {
  value: 0,
  listeners: new Set(),
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  },
  getSnapshot() {
    return this.value;
  },
  increment() {
    this.value++;
    this.listeners.forEach((l) => l());
  },
};

function Counter() {
  // useSyncExternalStore guarantees consistency during concurrent renders.
  // If the store changes mid-render, React detects it and does a
  // synchronous re-render to avoid tearing.
  const count = useSyncExternalStore(
    externalStore.subscribe.bind(externalStore),
    externalStore.getSnapshot.bind(externalStore)
  );

  return <div>Count: {count}</div>;
}

// Under the hood (simplified work loop pseudocode):
// function workLoopConcurrent() {
//   while (workInProgress !== null && !shouldYield()) {
//     workInProgress = performUnitOfWork(workInProgress);
//   }
//   // If workInProgress !== null, work was interrupted.
//   // React will schedule a continuation via the scheduler.
// }
//
// function performConcurrentWorkOnRoot(root) {
//   const exitStatus = renderRootConcurrent(root, lanes);
//   if (exitStatus === RootIncomplete) {
//     // Work was interrupted — schedule a continuation
//     ensureRootIsScheduled(root);
//     return;
//   }
//   // Work completed — proceed to commit phase (synchronous)
//   commitRoot(root);
// }
```

---

### Q14. How does React reconcile different types of children — single child, arrays, fragments, and iterators?

**Answer:**

The `reconcileChildFibers` function in React handles multiple child shapes. React internally normalizes children and applies different reconciliation strategies based on the shape:

1. **Single element child** (`<div><span>Hello</span></div>`): React compares the old child fiber with the new element. If types match and keys match (or both are null), it updates in place. If not, it deletes the old fiber and creates a new one.

2. **Array of elements** (`items.map(...)` or `[<A/>, <B/>, <C/>]`): React uses the **key-based reconciliation** algorithm. It iterates through both old fibers (linked list via `sibling`) and new elements (array). It builds a map of keyed old fibers, matches them with new elements, and determines insertions, deletions, and moves.

3. **Fragments** (`<React.Fragment>` or `<>...</>`): Fragments don't create DOM nodes. React treats the fragment's children as if they were directly children of the parent. The fragment itself gets a fiber with `tag: Fragment`, and its children are reconciled as an array.

4. **String/number children**: Treated as text content. React creates or updates a `HostText` fiber.

5. **Iterators/generators**: React can reconcile any iterable (objects with `Symbol.iterator`). It consumes the iterator and reconciles like an array.

6. **null/undefined/boolean**: Produce no fiber — React deletes any existing child.

```jsx
import { Fragment, useState } from 'react';

// 1. Single child reconciliation
function SingleChild({ showGreeting }) {
  return (
    <div>
      {/* When showGreeting toggles, if the type changes (span→null or vice versa),
          React creates/deletes the fiber. If it stays <span>, React updates text. */}
      {showGreeting ? <span>Hello!</span> : null}
    </div>
  );
}

// 2. Array reconciliation — the "two-pass" algorithm
function ArrayChildren() {
  const [items, setItems] = useState([
    { id: 1, text: 'A' },
    { id: 2, text: 'B' },
    { id: 3, text: 'C' },
  ]);

  // React's array reconciliation (simplified):
  // Pass 1: Walk old fibers and new array in parallel.
  //   - If key matches → update fiber, continue.
  //   - If key doesn't match → break out of linear walk.
  // Pass 2: Build a Map<key, oldFiber> from remaining old fibers.
  //   - For each remaining new element, look up by key.
  //   - Found → reuse fiber (move). Not found → create new fiber.
  //   - Delete any old fibers not matched.

  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{item.text}</li>
      ))}
    </ul>
  );
}

// 3. Fragment reconciliation
function FragmentExample() {
  return (
    <div>
      {/* The Fragment itself gets a fiber (tag: Fragment), but no DOM node.
          Its children (h1, p) become children of the div fiber. */}
      <Fragment>
        <h1>Title</h1>
        <p>Body</p>
      </Fragment>
    </div>
  );
}

// 4. Mixed children — React normalizes these internally
function MixedChildren({ user }) {
  return (
    <div>
      {/* string → HostText fiber */}
      Hello,
      {/* element → HostComponent fiber */}
      <strong>{user.name}</strong>
      {/* conditional null → no fiber */}
      {user.isAdmin && <span className="badge">Admin</span>}
      {/* array → each item reconciled as a child */}
      {user.tags.map((tag) => (
        <span key={tag} className="tag">{tag}</span>
      ))}
    </div>
  );
}

// 5. Iterator reconciliation (advanced pattern)
function* generateItems(data) {
  for (const item of data) {
    yield <li key={item.id}>{item.name}</li>;
  }
}

function IteratorList({ data }) {
  // React can consume generators/iterators as children
  return <ul>{generateItems(data)}</ul>;
}
```

---

### Q15. How does hydration reconciliation work — matching server HTML with the client tree?

**Answer:**

**Hydration** is the process where React "attaches" to server-rendered HTML rather than creating new DOM nodes from scratch. During hydration, React walks the fiber tree and the existing DOM tree simultaneously, attempting to **reuse** DOM nodes rather than creating them.

**The hydration reconciliation process:**

1. `hydrateRoot(container, <App />)` starts the process. React begins rendering the component tree just like a normal render.
2. For each host fiber (e.g., `div`, `span`), instead of calling `document.createElement`, React tries to **claim** the next existing DOM node from the server HTML.
3. React compares: does the existing DOM node match the fiber's type? If `<div>` fiber encounters a `<div>` DOM node → match. If `<div>` fiber encounters a `<span>` → mismatch.
4. On mismatch, React 18 **logs a warning** and falls back to client rendering for that subtree (deletes server HTML, creates from scratch).
5. Props are compared — React patches any differences (e.g., event handlers, which don't exist in server HTML).
6. Text content mismatches are particularly common (timestamps, randomized IDs).

**React 18 enhancements:** Selective hydration with Suspense — React can hydrate high-priority parts of the page first (e.g., what the user clicked on) and defer low-priority sections.

```jsx
// server.js (SSR with React 18 streaming)
import { renderToPipeableStream } from 'react-dom/server';
import App from './App';

function handleRequest(req, res) {
  const { pipe } = renderToPipeableStream(<App />, {
    bootstrapScripts: ['/client.js'],
    onShellReady() {
      res.statusCode = 200;
      res.setHeader('Content-Type', 'text/html');
      pipe(res);
    },
  });
}

// client.js (hydration)
import { hydrateRoot } from 'react-dom/client';
import App from './App';

// React walks existing DOM and attaches event listeners / reconciles
hydrateRoot(document.getElementById('root'), <App />);

// ❌ Common hydration mismatch: using Date or Math.random during render
function Timestamp() {
  // Server renders "10:30:00 AM", client hydrates at "10:30:02 AM"
  // React will warn: "Text content did not match"
  return <span>{new Date().toLocaleTimeString()}</span>;
}

// ✅ Fix: suppress hydration warning or use useEffect for client-only values
function SafeTimestamp() {
  const [time, setTime] = useState(null);

  useEffect(() => {
    // useEffect only runs on the client, after hydration
    setTime(new Date().toLocaleTimeString());
    const interval = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // During SSR and initial hydration, render nothing (or a placeholder).
  // After hydration, useEffect sets the real time.
  return <span>{time ?? '...'}</span>;
}

// React 18 Selective Hydration with Suspense:
function App() {
  return (
    <div>
      {/* This section hydrates immediately */}
      <Header />
      <SearchBar />

      {/* This section hydrates lazily — React streams the HTML,
          then hydrates it when the JS loads or when the user
          interacts with it (whichever comes first). */}
      <Suspense fallback={<Spinner />}>
        <HeavyProductList />
      </Suspense>

      <Suspense fallback={<Spinner />}>
        <Comments />
      </Suspense>
    </div>
  );
}
// If user clicks on Comments before it's hydrated, React PRIORITIZES
// hydrating Comments over HeavyProductList — this is selective hydration.
```

---

### Q16. How do error boundaries work in Fiber — unwinding the fiber tree?

**Answer:**

Error boundaries are class components that catch JavaScript errors during rendering, in lifecycle methods, and in constructors of their child tree. In Fiber, error handling is implemented through a **throw-and-unwind** mechanism analogous to try/catch but operating on the fiber tree instead of the call stack.

**The Fiber error handling process:**

1. During the render phase, if a component throws an error, React catches it in the work loop.
2. React **unwinds** the fiber tree — it walks up the `return` (parent) pointers looking for a fiber that is an error boundary (a class component with `static getDerivedStateFromError` and/or `componentDidCatch`).
3. When found, React marks the error boundary fiber with an `Update` effect containing the error.
4. React **restarts** rendering from the error boundary — it calls `getDerivedStateFromError(error)` to compute new state, re-renders the boundary with the fallback UI, and continues with the rest of the tree.
5. During the commit phase, `componentDidCatch(error, errorInfo)` is called (for logging, reporting).
6. If no error boundary is found, React unmounts the entire tree.

**What error boundaries do NOT catch:** Errors in event handlers (use try/catch), asynchronous code (promises, setTimeout), SSR, or the error boundary component itself.

```jsx
import { Component, useState } from 'react';

// Production-grade error boundary
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  // Called during RENDER PHASE — must be pure (no side effects)
  // React uses this to compute the fallback state before committing.
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  // Called during COMMIT PHASE — safe for side effects (logging, reporting)
  componentDidCatch(error, errorInfo) {
    // errorInfo.componentStack contains the fiber component stack trace:
    // "at BrokenComponent (BrokenComponent.js:5)"
    // "at div"
    // "at Dashboard (Dashboard.js:12)"
    // "at ErrorBoundary (ErrorBoundary.js:3)"

    console.error('Error caught by boundary:', error);
    console.error('Component stack:', errorInfo.componentStack);

    // Report to monitoring service
    reportErrorToService(error, {
      componentStack: errorInfo.componentStack,
      userId: this.props.userId,
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return this.props.fallback ? (
        this.props.fallback({ error: this.state.error, reset: this.handleReset })
      ) : (
        <div role="alert">
          <h2>Something went wrong</h2>
          <pre>{this.state.error?.message}</pre>
          <button onClick={this.handleReset}>Try Again</button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Usage: granular error boundaries per feature
function App() {
  return (
    <div>
      <Header /> {/* If header crashes, whole app is broken anyway */}

      <ErrorBoundary
        fallback={({ error, reset }) => (
          <div>
            <p>Dashboard failed: {error.message}</p>
            <button onClick={reset}>Retry</button>
          </div>
        )}
      >
        <Dashboard />
      </ErrorBoundary>

      <ErrorBoundary fallback={() => <p>Chat unavailable</p>}>
        <ChatWidget />
      </ErrorBoundary>
    </div>
  );
}

// The unwind process in Fiber (simplified pseudocode):
// function handleError(root, thrownValue) {
//   let workInProgress = /* the fiber that threw */;
//
//   // Walk UP the fiber tree via return pointers
//   while (workInProgress !== null) {
//     workInProgress = workInProgress.return; // go to parent
//
//     if (workInProgress.tag === ClassComponent) {
//       const instance = workInProgress.stateNode;
//       if (typeof instance.componentDidCatch === 'function' ||
//           typeof workInProgress.type.getDerivedStateFromError === 'function') {
//
//         // Found an error boundary! Schedule an update on it.
//         const update = createClassErrorUpdate(workInProgress, thrownValue);
//         enqueueUpdate(workInProgress, update);
//
//         // Restart rendering from this boundary
//         return workInProgress;
//       }
//     }
//   }
//   // No boundary found → fatal: unmount everything
// }

// Catching errors that boundaries CANNOT catch
function ClickHandler() {
  const handleClick = () => {
    try {
      riskyOperation();
    } catch (error) {
      // Error boundaries don't catch event handler errors.
      // Use try/catch directly.
      console.error('Click handler error:', error);
    }
  };

  return <button onClick={handleClick}>Do Something Risky</button>;
}
```

---

### Q17. How do you use the Profiler API to measure reconciliation cost?

**Answer:**

The **Profiler API** is a built-in React component that measures the rendering cost of its subtree. It collects timing data for every render (mount, update, or re-render) that occurs within it, making it invaluable for identifying performance bottlenecks in production.

The `<Profiler>` component accepts an `id` (string) and an `onRender` callback that fires after the profiled tree commits. The callback receives:

- `id` — which Profiler tree committed
- `phase` — `"mount"` or `"update"` (or `"nested-update"`)
- `actualDuration` — time (ms) spent rendering the subtree in this commit
- `baseDuration` — estimated time to render the full subtree without memoization
- `startTime` — when React started rendering this update
- `commitTime` — when React committed this update

**Production tip:** `baseDuration` includes the cost of all descendants, even memoized ones. Compare `actualDuration` (what actually ran) vs. `baseDuration` (what would run without memo) to assess how effective your memoization strategy is.

The Profiler can be nested, used in production builds (with `react-dom/profiling`), and combined with React DevTools' "Profiler" tab for flame chart visualization.

```jsx
import { Profiler, useState, memo, useMemo } from 'react';

// Production-grade profiling callback
function onRenderCallback(
  id,           // "Dashboard" or "UserList"
  phase,        // "mount" | "update" | "nested-update"
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) {
  // Log slow renders to monitoring
  if (actualDuration > 16) {
    // > 16ms means we dropped at least one frame at 60fps
    console.warn(
      `[Profiler] Slow render: ${id} (${phase})`,
      `actual: ${actualDuration.toFixed(2)}ms`,
      `base: ${baseDuration.toFixed(2)}ms`,
      `memo savings: ${((1 - actualDuration / baseDuration) * 100).toFixed(1)}%`
    );

    // In production, send to observability platform
    // analytics.track('slow_render', {
    //   component: id,
    //   phase,
    //   actualDuration,
    //   baseDuration,
    //   startTime,
    //   commitTime,
    // });
  }
}

function App() {
  return (
    <div>
      {/* Profile the entire dashboard */}
      <Profiler id="Dashboard" onRender={onRenderCallback}>
        <Dashboard />
      </Profiler>

      {/* Profile a specific expensive section separately */}
      <Profiler id="UserList" onRender={onRenderCallback}>
        <UserList />
      </Profiler>
    </div>
  );
}

// Nested profilers for granular measurement
function Dashboard() {
  const [tab, setTab] = useState('overview');

  return (
    <div>
      <nav>
        <button onClick={() => setTab('overview')}>Overview</button>
        <button onClick={() => setTab('analytics')}>Analytics</button>
      </nav>

      <Profiler id="Dashboard-Content" onRender={onRenderCallback}>
        {tab === 'overview' ? <OverviewPanel /> : <AnalyticsPanel />}
      </Profiler>
    </div>
  );
}

// Using baseDuration to evaluate memoization effectiveness
const ExpensiveChart = memo(function ExpensiveChart({ data }) {
  // Simulate expensive render
  const processed = useMemo(() => {
    return data.map((d) => ({ ...d, computed: heavyCalculation(d) }));
  }, [data]);

  return (
    <div>
      {processed.map((d) => (
        <div key={d.id} style={{ height: d.computed }}>{d.label}</div>
      ))}
    </div>
  );
});

// Enabling Profiler in production:
// By default, React strips Profiler in production builds.
// To keep it, use the profiling build:
//
// import { createRoot } from 'react-dom/profiling';
//
// OR in webpack:
// resolve: {
//   alias: {
//     'react-dom$': 'react-dom/profiling',
//     'scheduler/tracing': 'scheduler/tracing-profiling',
//   }
// }

// React DevTools integration:
// 1. Open React DevTools → "Profiler" tab
// 2. Click "Record" → interact with the app → "Stop"
// 3. Flame chart shows: which components rendered, how long each took
// 4. "Why did this render?" panel shows: props changed, state changed,
//    parent rendered, hooks changed, or context changed
// 5. Ranked chart sorts components by render duration — find the bottleneck
```

---

### Q18. What are common reconciliation pitfalls — index as key, unstable keys, and excessive nesting?

**Answer:**

Reconciliation pitfalls cause React to do unnecessary work (destroying and recreating DOM nodes and component state) or produce incorrect UI. Here are the most common ones:

**Pitfall 1: Using array index as key.** When items are reordered, inserted, or removed, indices shift. React matches old key=0 to new key=0, which is now a different item. This causes (a) state to be associated with the wrong item, (b) unnecessary DOM mutations, and (c) broken animations.

**Pitfall 2: Unstable keys (e.g., `Math.random()`, `Date.now()`).** A new key every render means React treats every item as new — unmounts all old items and mounts new ones. This destroys all state and DOM nodes, kills performance, and breaks focus/selections.

**Pitfall 3: Inline component definitions.** Defining a component inside another component's render creates a new function reference each render → React sees a new type → unmounts + remounts the entire subtree.

**Pitfall 4: Wrapping elements in unnecessary nesting that changes.** If you conditionally wrap content in different container types, React sees a type change and remounts.

**Pitfall 5: Forgetting that same-position, same-type = preserved state.** Two visually different sections rendered with the same component at the same position share state unless you use a `key` to reset it.

```jsx
import { useState } from 'react';

// ────────────────────────────────────────────
// PITFALL 1: Index as key
// ────────────────────────────────────────────
function ChatRooms({ rooms }) {
  const [messages, setMessages] = useState({});

  // ❌ BAD: If a room is deleted, all subsequent rooms shift index.
  // Room B (key=1) becomes key=0, inheriting Room A's uncontrolled input state.
  return rooms.map((room, index) => (
    <ChatRoom key={index} room={room} />
  ));

  // ✅ GOOD: Stable identity.
  return rooms.map((room) => (
    <ChatRoom key={room.id} room={room} />
  ));
}

// ────────────────────────────────────────────
// PITFALL 2: Unstable keys
// ────────────────────────────────────────────
function NotificationList({ notifications }) {
  return (
    <ul>
      {notifications.map((n) => (
        // ❌ BAD: New key every render → unmounts and remounts every <li>.
        // Animations break, input focus lost, performance destroyed.
        <li key={Math.random()}>{n.text}</li>
      ))}
    </ul>
  );

  return (
    <ul>
      {notifications.map((n) => (
        // ✅ GOOD: Stable unique identifier.
        <li key={n.id}>{n.text}</li>
      ))}
    </ul>
  );
}

// ────────────────────────────────────────────
// PITFALL 3: Inline component definition
// ────────────────────────────────────────────
function Form() {
  const [name, setName] = useState('');

  // ❌ BAD: New component type every render → input remounts → loses focus!
  const NameInput = () => (
    <input value={name} onChange={(e) => setName(e.target.value)} />
  );

  return <NameInput />;
}

function FormFixed() {
  const [name, setName] = useState('');

  // ✅ GOOD: Inline JSX, not a new component.
  return <input value={name} onChange={(e) => setName(e.target.value)} />;
}

// ────────────────────────────────────────────
// PITFALL 4: Conditional wrapper changing type
// ────────────────────────────────────────────
function Card({ isSpecial, children }) {
  // ❌ BAD: Toggling isSpecial changes the wrapper from <div> to <section>.
  // React remounts all children, destroying their state.
  if (isSpecial) {
    return <section className="special">{children}</section>;
  }
  return <div className="normal">{children}</div>;
}

function CardFixed({ isSpecial, children }) {
  // ✅ GOOD: Same element type, only className changes → update in place.
  return (
    <div className={isSpecial ? 'special' : 'normal'}>
      {children}
    </div>
  );
}

// ────────────────────────────────────────────
// PITFALL 5: Same position = preserved state (surprising behavior)
// ────────────────────────────────────────────
function Scoreboard({ isPlayerA }) {
  // Both branches render <Counter> at the same position with the same type.
  // React KEEPS the state! Switching players doesn't reset the count.
  return (
    <div>
      {isPlayerA ? (
        <Counter person="Alice" />
      ) : (
        <Counter person="Bob" />
      )}
    </div>
  );
}

function ScoreboardFixed({ isPlayerA }) {
  // ✅ FIX: Use key to force React to treat them as different instances.
  return (
    <div>
      {isPlayerA ? (
        <Counter key="alice" person="Alice" />
      ) : (
        <Counter key="bob" person="Bob" />
      )}
    </div>
  );
}
```

---

### Q19. How are effects in Fiber scheduled — the full effect lifecycle and `useLayoutEffect` vs `useEffect` under the hood?

**Answer:**

Understanding the precise scheduling of effects requires knowing how Fiber tags and processes them internally.

**During the render phase**, when React encounters `useEffect` or `useLayoutEffect`, it creates an **effect object** and stores it on the fiber's `updateQueue` (a circular linked list). The effect is tagged with flags:
- `useEffect` → `HookPassive | HookHasEffect`
- `useLayoutEffect` → `HookLayout | HookHasEffect`

The `HookHasEffect` flag is only set if the dependency array changed (or on mount). If deps haven't changed, the effect object is created but without `HookHasEffect`, so its callback is skipped.

**During the commit phase**, effects are executed in a specific order across three sub-phases:

1. **Before Mutation**: `getSnapshotBeforeUpdate` runs (class only).
2. **Mutation**: DOM changes applied. `useLayoutEffect` **cleanup** from the previous render runs (for unmounting fibers and fibers with changed deps).
3. **Layout**: `useLayoutEffect` **setup** runs synchronously. Refs are attached. Class `componentDidMount`/`componentDidUpdate` fire.
4. **Passive effects** (after commit): `useEffect` cleanup and setup are scheduled via `flushPassiveEffects`. In React 18, these run asynchronously after the browser has had a chance to paint. React flushes them before the next discrete event to ensure consistency.

**Critical production detail**: `useLayoutEffect` blocks the browser from painting. If you do expensive work here, the user sees a frozen frame. `useEffect` runs after paint, so it's non-blocking but means the user might briefly see a "before" state.

```jsx
import { useState, useEffect, useLayoutEffect, useInsertionEffect, useRef } from 'react';

// Complete effect ordering demonstration
function EffectOrderDemo() {
  const [count, setCount] = useState(0);
  const renderCount = useRef(0);
  renderCount.current++;

  console.log(`1. Render phase: count = ${count} (render #${renderCount.current})`);

  // React 18+ only: runs before any DOM mutations
  // Used by CSS-in-JS libraries to inject <style> tags
  useInsertionEffect(() => {
    console.log('2. useInsertionEffect: inject styles BEFORE DOM mutations');
    return () => console.log('   useInsertionEffect cleanup');
  });

  useLayoutEffect(() => {
    console.log('3. useLayoutEffect: DOM is updated, BEFORE paint');
    // Safe to read DOM measurements here (getBoundingClientRect, etc.)
    // Safe to synchronously set state here (causes synchronous re-render
    // before the browser paints — the user sees only the final state).
    return () => console.log('   useLayoutEffect cleanup');
  });

  useEffect(() => {
    console.log('4. useEffect: AFTER paint — browser has rendered pixels');
    return () => console.log('   useEffect cleanup');
  });

  return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;
}

// Mount order:
// 1. Render phase: count = 0
// 2. useInsertionEffect: inject styles
// 3. useLayoutEffect: DOM is updated, BEFORE paint
// -- browser paints --
// 4. useEffect: AFTER paint

// Update order (click):
// 1. Render phase: count = 1
//    useInsertionEffect cleanup
// 2. useInsertionEffect: inject styles
//    useLayoutEffect cleanup    ← cleanup runs BEFORE new setup
// 3. useLayoutEffect: DOM is updated, BEFORE paint
// -- browser paints --
//    useEffect cleanup          ← cleanup runs BEFORE new setup
// 4. useEffect: AFTER paint

// Production scenario: Tooltip positioning without flicker
function Tooltip({ anchorEl, children }) {
  const tooltipRef = useRef(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  // ✅ useLayoutEffect: measure anchor and position tooltip BEFORE paint.
  // Without this, the tooltip would flash at (0,0) then jump to the right position.
  useLayoutEffect(() => {
    if (!anchorEl || !tooltipRef.current) return;

    const anchorRect = anchorEl.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    setPosition({
      top: anchorRect.bottom + 8,
      left: anchorRect.left + (anchorRect.width - tooltipRect.width) / 2,
    });
  }, [anchorEl]);

  return (
    <div
      ref={tooltipRef}
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

// How React flushes passive effects (simplified):
// function commitRoot(root) {
//   commitBeforeMutationEffects(root);  // getSnapshotBeforeUpdate
//   commitMutationEffects(root);         // DOM mutations + layoutEffect cleanup
//   root.current = finishedWork;         // swap trees
//   commitLayoutEffects(root);           // layoutEffect setup + refs
//
//   // Schedule passive effects to run asynchronously
//   scheduleCallback(NormalPriority, () => {
//     flushPassiveEffects();             // useEffect cleanup + setup
//   });
// }
```

---

### Q20. Production scenario: Diagnosing why a component keeps re-mounting instead of updating — a systematic debugging approach

**Answer:**

One of the most common and frustrating React performance bugs is a component that **unmounts and remounts** on every render instead of updating in place. This destroys all internal state, re-runs mount effects, recreates DOM nodes, kills animations, and massacres performance. Here's a systematic approach to diagnose and fix it.

**Step 1: Confirm the symptom.** Add a `useEffect` with no deps — if its cleanup runs on every "update," the component is unmounting, not updating.

**Step 2: Check the common causes:**

| Cause | What Happens | Fix |
|---|---|---|
| Component defined inside another component | New type reference each render → remount | Move component definition outside |
| Unstable `key` (Math.random, Date.now) | New key each render → remount | Use stable ID |
| Element type changes conditionally | `<div>` → `<section>` at same position → remount | Use same element type, vary via props |
| Higher-order component called in render | `memo(Component)` inside render creates new wrapper each time → remount | Call HOC outside component |
| Dynamic `React.lazy` import | `lazy(() => import(...))` inside render creates new lazy component each time → remount | Define lazy component at module scope |
| Parent key changes | If a parent has an unstable key, entire subtree remounts | Fix parent's key |

**Step 3: Use React DevTools.** The "Highlight updates" feature and the Profiler's "Why did this render?" panel can confirm whether a component mounted or updated.

```jsx
import { useState, useEffect, useRef, memo, lazy, Suspense } from 'react';

// ────────────────────────────────────────────
// DIAGNOSTIC: Detect mount vs. update
// ────────────────────────────────────────────
function useDebugMountCycle(componentName) {
  const mountCount = useRef(0);
  const renderCount = useRef(0);

  renderCount.current++;

  useEffect(() => {
    mountCount.current++;
    console.log(
      `[${componentName}] MOUNTED (mount #${mountCount.current}, render #${renderCount.current})`
    );
    return () => {
      console.log(`[${componentName}] UNMOUNTED`);
    };
  }, []); // Empty deps: runs only on mount/unmount

  useEffect(() => {
    console.log(
      `[${componentName}] rendered (mount #${mountCount.current}, render #${renderCount.current})`
    );
  });
}

// ────────────────────────────────────────────
// BUG 1: Component defined inside render
// ────────────────────────────────────────────
function BuggyPage() {
  const [query, setQuery] = useState('');

  // ❌ New function every render → new type → remount!
  function SearchResults() {
    useDebugMountCycle('SearchResults');
    return <div>Results for: {query}</div>;
  }

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <SearchResults /> {/* REMOUNTS on every keystroke! */}
    </div>
  );
}

// ✅ FIX: Define outside + pass data via props
function SearchResults({ query }) {
  useDebugMountCycle('SearchResults');
  return <div>Results for: {query}</div>;
}

function FixedPage() {
  const [query, setQuery] = useState('');
  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <SearchResults query={query} /> {/* UPDATES, doesn't remount */}
    </div>
  );
}

// ────────────────────────────────────────────
// BUG 2: HOC/memo called inside render
// ────────────────────────────────────────────
function BuggyDashboard() {
  const [tab, setTab] = useState('home');

  // ❌ memo() called every render → creates new wrapper type → remount!
  const MemoizedWidget = memo(function Widget() {
    useDebugMountCycle('Widget');
    return <div>Widget content</div>;
  });

  return <MemoizedWidget />;
}

// ✅ FIX: Memoize at module scope
const MemoizedWidget = memo(function Widget() {
  useDebugMountCycle('Widget');
  return <div>Widget content</div>;
});

function FixedDashboard() {
  const [tab, setTab] = useState('home');
  return <MemoizedWidget />;
}

// ────────────────────────────────────────────
// BUG 3: lazy() called inside render
// ────────────────────────────────────────────
function BuggyRouter({ path }) {
  // ❌ lazy() inside render → new lazy component each time → remount + re-fetch!
  const Page = lazy(() => import(`./pages/${path}`));
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Page />
    </Suspense>
  );
}

// ✅ FIX: Create lazy components at module scope or use a stable map
const pageMap = {
  home: lazy(() => import('./pages/Home')),
  about: lazy(() => import('./pages/About')),
  settings: lazy(() => import('./pages/Settings')),
};

function FixedRouter({ path }) {
  const Page = pageMap[path] || pageMap.home;
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Page />
    </Suspense>
  );
}

// ────────────────────────────────────────────
// BUG 4: Unstable key on a wrapper element
// ────────────────────────────────────────────
function BuggyForm({ formConfig }) {
  return (
    // ❌ If formConfig.id changes unexpectedly (e.g., server returns new ID
    // on each fetch), the entire form remounts, losing all user input.
    <div key={formConfig.id}>
      <h2>{formConfig.title}</h2>
      <FormFields config={formConfig} />
    </div>
  );
}

function FixedForm({ formConfig }) {
  // ✅ Only use key when you INTENTIONALLY want to reset state.
  // For normal updates, let React reconcile by position.
  return (
    <div>
      <h2>{formConfig.title}</h2>
      <FormFields config={formConfig} />
    </div>
  );
}

// ────────────────────────────────────────────
// DEBUGGING CHECKLIST (summary)
// ────────────────────────────────────────────
// 1. Add useDebugMountCycle to the suspect component
// 2. If it logs "MOUNTED" on every parent state change:
//    a. Check: Is the component defined inside another component?
//    b. Check: Is memo/HOC wrapping happening inside render?
//    c. Check: Is lazy() called inside render?
//    d. Check: Does the component or any ancestor have an unstable key?
//    e. Check: Does the element type change conditionally?
// 3. Use React DevTools Profiler → "Why did this render?" for each commit
// 4. Search for key={} in JSX — verify all keys are stable identifiers
// 5. Search for function/const Component = inside component bodies
```

---

*This concludes the 20-question deep dive into React Fiber & Reconciliation. Mastering these internals — from the virtual DOM fundamentals through fiber nodes, the work loop, priority lanes, concurrent rendering, and production debugging — is what separates senior React engineers from the rest. In interviews, demonstrating that you understand not just the API surface but the underlying architecture will set you apart.*
