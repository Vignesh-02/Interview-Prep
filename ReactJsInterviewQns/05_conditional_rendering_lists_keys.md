# Topic 5: Conditional Rendering, Lists & Keys in React 18

## Introduction

Conditional rendering in React follows the same logic as conditional expressions in JavaScript — you decide what UI to show based on state, props, or any runtime value. Because JSX is just syntactic sugar over `React.createElement` calls, you can use standard JavaScript constructs like `if/else`, the ternary operator (`? :`), logical AND (`&&`), and `switch` statements to conditionally include or exclude parts of your component tree. React 18 does not change the fundamental mechanics of conditional rendering, but its concurrent features (automatic batching, transitions, Suspense) interact with conditional UI in important ways — for instance, wrapping a conditionally-rendered lazy component in a `<Suspense>` boundary controls the fallback that users see during loading.

Lists are one of the most common patterns in React applications — rendering arrays of data as repeated UI elements. The idiomatic approach is to call `.map()` on an array and return JSX for each item. React requires a special `key` prop on each element in a list so that its **reconciliation algorithm** (the "diffing" engine) can efficiently determine which items were added, removed, or reordered between renders. Choosing the right key is crucial: a stable, unique identifier (like a database ID) lets React preserve component state and DOM nodes across re-renders, while using array indices as keys can lead to subtle bugs when items are reordered, inserted, or deleted. Beyond simple lists, production applications deal with virtualized lists (rendering only visible items for performance), paginated data, drag-and-drop reordering, and recursive tree structures — all of which demand a solid understanding of keys and conditional rendering.

Here is a quick illustration combining conditional rendering with list rendering and proper key usage in React 18:

```jsx
import { useState } from 'react';

function TaskBoard({ tasks, isLoggedIn }) {
  if (!isLoggedIn) {
    return <p>Please sign in to view your tasks.</p>;
  }

  const activeTasks = tasks.filter((t) => !t.completed);
  const completedTasks = tasks.filter((t) => t.completed);

  return (
    <div>
      <h2>Active Tasks ({activeTasks.length})</h2>
      {activeTasks.length > 0 ? (
        <ul>
          {activeTasks.map((task) => (
            <li key={task.id}>
              <strong>{task.title}</strong>
              {task.priority === 'high' && <span className="badge-urgent">🔴</span>}
            </li>
          ))}
        </ul>
      ) : (
        <p>All caught up — no active tasks!</p>
      )}

      {completedTasks.length > 0 && (
        <>
          <h2>Completed ({completedTasks.length})</h2>
          <ul>
            {completedTasks.map((task) => (
              <li key={task.id} className="line-through">{task.title}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
```

This snippet demonstrates early-return conditional rendering (the sign-in guard), ternary operators for either/or UI, `&&` for optional sections, `.map()` for list rendering, and stable `key` props via `task.id`. Every question below digs deeper into these patterns and their production implications.

---

## Beginner Level (Q1–Q5)

---

### Q1. What are the main techniques for conditional rendering in React, and when should you use each one?

**Answer:**

React supports several conditional rendering patterns, each suited to different situations:

1. **`if/else` statements** — Used outside the JSX return, or with early returns. Best for complex conditions with multiple branches or when you want to bail out of rendering entirely.
2. **Ternary operator (`condition ? A : B`)** — Used inline inside JSX. Best when you have exactly two outcomes (show this or that).
3. **Logical AND (`&&`)** — Used inline when you want to render something or nothing. Best for toggling a single element on or off.
4. **`switch` statements** — Used outside JSX return for multi-branch logic (e.g., rendering different views based on a status string). Best when you have three or more distinct cases.
5. **Immediately Invoked Function Expressions (IIFEs)** — Rarely used, but allow complex logic inline. Generally a sign you should extract a helper or sub-component.

```jsx
function StatusMessage({ status, count, isAdmin }) {
  // 1. if/else with early return
  if (status === 'loading') {
    return <Spinner />;
  }

  // 4. switch for multi-branch
  const renderBanner = () => {
    switch (status) {
      case 'success':
        return <div className="banner-success">Operation completed!</div>;
      case 'error':
        return <div className="banner-error">Something went wrong.</div>;
      case 'warning':
        return <div className="banner-warning">Proceed with caution.</div>;
      default:
        return null;
    }
  };

  return (
    <div>
      {renderBanner()}

      {/* 2. Ternary — two possible outcomes */}
      <h1>{count > 0 ? `${count} items found` : 'No items found'}</h1>

      {/* 3. Logical AND — show only if true */}
      {isAdmin && <button className="admin-btn">Admin Settings</button>}
    </div>
  );
}
```

**Guidelines:**
- Prefer `if/else` with early return for guard clauses (loading, error, empty states).
- Prefer ternaries for simple either/or inline rendering.
- Prefer `&&` for "show or hide" cases, but beware of falsy-value pitfalls (covered in Q2).
- Extract a helper function or sub-component when ternaries become deeply nested.

---

### Q2. What are the short-circuit evaluation pitfalls with `&&` in JSX, and how do you avoid them?

**Answer:**

The logical AND (`&&`) operator returns the **first falsy value** it encounters, or the last value if all are truthy. In JSX, this is dangerous because some falsy values in JavaScript are **rendered as visible text by React** rather than producing no output:

| Expression | What React renders |
|---|---|
| `false && <Comp />` | Nothing (correct) |
| `null && <Comp />` | Nothing (correct) |
| `undefined && <Comp />` | Nothing (correct) |
| `0 && <Comp />` | **`0`** (a visible "0" on screen!) |
| `"" && <Comp />` | Nothing (empty string is not rendered) |
| `NaN && <Comp />` | **`NaN`** (visible text!) |

The two troublemakers are **`0`** and **`NaN`** — React renders these as text nodes.

```jsx
function NotificationBadge({ notifications }) {
  // BUG: if notifications.length is 0, React renders "0" on screen
  return (
    <div>
      {notifications.length && (
        <span className="badge">{notifications.length}</span>
      )}
    </div>
  );
}

// FIX 1: Convert to a boolean explicitly
function NotificationBadgeFixed({ notifications }) {
  return (
    <div>
      {notifications.length > 0 && (
        <span className="badge">{notifications.length}</span>
      )}
    </div>
  );
}

// FIX 2: Use double negation
function NotificationBadgeFixed2({ notifications }) {
  return (
    <div>
      {!!notifications.length && (
        <span className="badge">{notifications.length}</span>
      )}
    </div>
  );
}

// FIX 3: Use a ternary to be explicit
function NotificationBadgeFixed3({ notifications }) {
  return (
    <div>
      {notifications.length > 0 ? (
        <span className="badge">{notifications.length}</span>
      ) : null}
    </div>
  );
}
```

**Rule of thumb:** Never put a number or potentially-`NaN` value on the left side of `&&` in JSX. Always convert to a proper boolean first with a comparison (`> 0`, `!== 0`) or `Boolean()` / `!!`.

---

### Q3. How do you render a list of items in React using `.map()`, and why must each element have a `key` prop?

**Answer:**

The standard pattern for rendering a list in React is to call `.map()` on an array and return a JSX element for each item. React requires a **`key` prop** on each element so that it can identify which items have changed, been added, or been removed during reconciliation (the diffing process).

Without keys, React would have to re-create every list element on each render. With keys, React matches elements across renders by their key, preserving DOM nodes and component state for elements that haven't changed.

```jsx
function UserList({ users }) {
  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>
          <img src={user.avatar} alt={user.name} />
          <div>
            <h3>{user.name}</h3>
            <p>{user.email}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

// Usage
const users = [
  { id: 'u1', name: 'Alice', email: 'alice@example.com', avatar: '/alice.jpg' },
  { id: 'u2', name: 'Bob', email: 'bob@example.com', avatar: '/bob.jpg' },
  { id: 'u3', name: 'Carol', email: 'carol@example.com', avatar: '/carol.jpg' },
];

<UserList users={users} />;
```

**Key rules:**
1. Keys must be **unique among siblings** (not globally unique — just within the same `.map()` call).
2. Keys must be **stable** — they should not change between renders.
3. Keys should come from your **data** (database IDs, slugs, etc.), not be generated at render time.
4. Keys are **not passed as a prop** to the child component — they're consumed by React internally. If the child needs the ID, pass it as a separate prop.

```jsx
// key is NOT accessible inside UserCard as props.key
{users.map((user) => (
  <UserCard key={user.id} userId={user.id} name={user.name} />
))}
```

---

### Q4. What happens when you return `null` from a component, and how is it different from returning `undefined`?

**Answer:**

Returning **`null`** from a component is the official React way to render nothing. React sees `null` and skips rendering any DOM node for that component. The component still exists in the component tree (lifecycle effects still run, hooks still execute), but it produces no visible output.

Returning **`undefined`** is different — in older React versions (pre-18), returning `undefined` from a component would throw an error. In React 18, a component returning `undefined` no longer throws, but it is still considered a bad practice and may trigger warnings in development mode. The explicit convention is to return `null` when you intentionally want to render nothing.

```jsx
// ✅ Correct: returning null to render nothing
function ConditionalBanner({ show, message }) {
  if (!show) {
    return null; // Renders nothing, no DOM node produced
  }
  return <div className="banner">{message}</div>;
}

// ❌ Avoid: returning undefined (works in React 18, but bad practice)
function BadComponent({ show, message }) {
  if (!show) {
    return; // implicitly returns undefined — avoid this
  }
  return <div className="banner">{message}</div>;
}

// Practical example: conditionally rendering a component
function App() {
  const [showBanner, setShowBanner] = useState(true);

  return (
    <div>
      <ConditionalBanner show={showBanner} message="Welcome back!" />
      {/* Even when show=false, ConditionalBanner is in the tree, 
          its hooks run, but no DOM is produced */}
      <button onClick={() => setShowBanner((prev) => !prev)}>
        Toggle Banner
      </button>
    </div>
  );
}
```

**Important nuance:** Returning `null` is different from **not mounting** the component at all. If you use `{condition && <Component />}`, the component is completely unmounted when the condition is false — its state is destroyed and effects are cleaned up. When the component itself returns `null`, it stays mounted but invisible.

---

### Q5. What is the early return pattern for conditional rendering, and why is it useful?

**Answer:**

The early return pattern uses `if` statements at the **top** of a component function to handle edge cases (loading, error, empty states, unauthorized access) before reaching the main render logic. This keeps the "happy path" render at the end, unindented and easy to read.

```jsx
function OrderDetails({ orderId }) {
  const { data: order, isLoading, error } = useOrder(orderId);

  // Early return: loading state
  if (isLoading) {
    return (
      <div className="order-skeleton">
        <Skeleton width="60%" height={24} />
        <Skeleton width="40%" height={18} />
        <Skeleton width="100%" height={200} />
      </div>
    );
  }

  // Early return: error state
  if (error) {
    return (
      <div className="order-error" role="alert">
        <h2>Failed to load order</h2>
        <p>{error.message}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  // Early return: not found
  if (!order) {
    return <p>Order not found.</p>;
  }

  // Happy path — unindented, easy to read
  return (
    <div className="order-details">
      <h1>Order #{order.id}</h1>
      <p>Status: {order.status}</p>
      <p>Total: ${order.total.toFixed(2)}</p>
      <ul>
        {order.items.map((item) => (
          <li key={item.sku}>
            {item.name} × {item.qty} — ${(item.price * item.qty).toFixed(2)}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Benefits:**
1. **Readability** — The main JSX is not nested inside multiple conditionals.
2. **Explicit handling** — Every edge case is clearly addressed at the top.
3. **Less nesting** — Avoids deeply indented ternary chains.
4. **TypeScript synergy** — TypeScript narrows types after each guard, so by the time you reach the happy path, you know `order` is defined.

**When to use:** Whenever a component has distinct states (loading, error, empty, unauthorized) that should render completely different UIs. It is one of the most common and most readable patterns in production React code.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you avoid deeply nested ternary expressions for conditional rendering, and what alternatives are cleaner?

**Answer:**

Deeply nested ternaries are a code smell — they are hard to read, hard to debug, and prone to errors when modified:

```jsx
// ❌ Deeply nested ternaries — hard to read and maintain
function StatusView({ status }) {
  return (
    <div>
      {status === 'loading' ? (
        <Spinner />
      ) : status === 'error' ? (
        <ErrorBanner />
      ) : status === 'empty' ? (
        <EmptyState />
      ) : status === 'success' ? (
        <DataView />
      ) : (
        <UnknownState />
      )}
    </div>
  );
}
```

**Better alternatives:**

**1. Extract a helper function (or use `switch`):**

```jsx
function StatusView({ status }) {
  const renderContent = () => {
    switch (status) {
      case 'loading':
        return <Spinner />;
      case 'error':
        return <ErrorBanner />;
      case 'empty':
        return <EmptyState />;
      case 'success':
        return <DataView />;
      default:
        return <UnknownState />;
    }
  };

  return <div>{renderContent()}</div>;
}
```

**2. Use a component map (object lookup):**

```jsx
const STATUS_COMPONENTS = {
  loading: Spinner,
  error: ErrorBanner,
  empty: EmptyState,
  success: DataView,
};

function StatusView({ status }) {
  const Component = STATUS_COMPONENTS[status] || UnknownState;
  return (
    <div>
      <Component />
    </div>
  );
}
```

**3. Extract sub-components for each branch:**

```jsx
function StatusView({ status, data, error }) {
  if (status === 'loading') return <Spinner />;
  if (status === 'error') return <ErrorBanner error={error} />;
  if (status === 'empty') return <EmptyState />;
  return <DataView data={data} />;
}
```

The component-map approach (option 2) is especially powerful when the set of statuses is dynamic or comes from a configuration file. It also makes the code open for extension without modifying the rendering logic.

---

### Q7. When is it acceptable to use the array index as a `key`, and when does it cause bugs?

**Answer:**

Using the array index as a key is acceptable **only** when all three conditions are met:

1. The list is **static** — items are never added, removed, or reordered.
2. The items have **no stable unique ID** available.
3. The list items have **no internal state** (no inputs, no animations, no checkboxes).

When any of those conditions is violated, index keys cause bugs:

```jsx
import { useState } from 'react';

function TodoList() {
  const [todos, setTodos] = useState([
    { text: 'Buy groceries' },
    { text: 'Walk the dog' },
    { text: 'Read a book' },
  ]);

  const addToTop = () => {
    setTodos([{ text: 'New task (added to top)' }, ...todos]);
  };

  return (
    <div>
      <button onClick={addToTop}>Add to top</button>
      <ul>
        {todos.map((todo, index) => (
          // ❌ BUG: using index as key
          <li key={index}>
            <input defaultValue={todo.text} />
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**What goes wrong:** When "New task" is added to the top, every item's index shifts by one. React sees that key `0` existed before and exists now, so it reuses the DOM node for key `0`. But key `0` now corresponds to a different todo. The `<input>` retains the old DOM state ("Buy groceries" text), creating a mismatch between data and UI.

**Fixed with stable IDs:**

```jsx
import { useState, useId } from 'react';
import { nanoid } from 'nanoid';

function TodoList() {
  const [todos, setTodos] = useState([
    { id: nanoid(), text: 'Buy groceries' },
    { id: nanoid(), text: 'Walk the dog' },
    { id: nanoid(), text: 'Read a book' },
  ]);

  const addToTop = () => {
    setTodos([{ id: nanoid(), text: 'New task (added to top)' }, ...todos]);
  };

  return (
    <div>
      <button onClick={addToTop}>Add to top</button>
      <ul>
        {todos.map((todo) => (
          // ✅ Stable unique key — DOM state follows the data
          <li key={todo.id}>
            <input defaultValue={todo.text} />
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Production tip:** If your data comes from a backend, use the database primary key or UUID. For client-created items, generate an ID at creation time (e.g., `crypto.randomUUID()`, `nanoid()`). Never generate keys inside `.map()` at render time — that defeats the purpose because a new key is created every render.

---

### Q8. How do you conditionally render different layouts or components based on authentication state and user roles?

**Answer:**

A common production pattern is to combine authentication state and role-based access control (RBAC) with conditional rendering. The approach typically involves a context provider for auth state and wrapper components that guard routes or UI sections.

```jsx
import { createContext, useContext, useState, useEffect } from 'react';

// Auth context
const AuthContext = createContext(null);

function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('/api/me')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        setUser(data);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// Role-based conditional rendering component
function RequireRole({ roles, fallback = null, children }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <Skeleton height={40} />;
  if (!user) return <LoginPrompt />;
  if (!roles.includes(user.role)) return fallback;

  return children;
}

// Dashboard with role-based sections
function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="dashboard">
      <h1>Welcome, {user.name}</h1>

      {/* Everyone sees their profile */}
      <ProfileCard user={user} />

      {/* Only managers and admins see team metrics */}
      <RequireRole roles={['manager', 'admin']}>
        <TeamMetrics />
      </RequireRole>

      {/* Only admins see system settings */}
      <RequireRole
        roles={['admin']}
        fallback={<p>You don't have access to system settings.</p>}
      >
        <SystemSettings />
      </RequireRole>

      {/* Conditional navigation based on role */}
      <nav>
        <NavLink to="/dashboard">Home</NavLink>
        {user.role === 'admin' && <NavLink to="/admin">Admin Panel</NavLink>}
        {['admin', 'manager'].includes(user.role) && (
          <NavLink to="/reports">Reports</NavLink>
        )}
      </nav>
    </div>
  );
}
```

**Production considerations:**
- **Never rely solely on client-side role checks for security.** The server must enforce authorization. Client-side checks are for UX only (hiding buttons the user can't use).
- **Show appropriate fallbacks** — don't just hide content silently. A "You don't have access" message is better UX than a mysteriously empty section.
- **Handle the loading state** — Always account for the time between page load and the auth check completing to avoid a flash of unauthorized content.

---

### Q9. What is the component map pattern for dynamic component rendering, and when is it useful?

**Answer:**

The component map pattern stores a mapping from string identifiers to React components in a plain object, then dynamically selects and renders the appropriate component at runtime. This is extremely useful for plugin architectures, CMS-driven pages, form builders, and multi-step wizards.

```jsx
import { useState } from 'react';

// Step components
function ShippingForm({ onNext }) {
  return (
    <div>
      <h2>Shipping Address</h2>
      <form onSubmit={(e) => { e.preventDefault(); onNext(); }}>
        <input placeholder="Street address" required />
        <input placeholder="City" required />
        <input placeholder="ZIP code" required />
        <button type="submit">Continue to Payment</button>
      </form>
    </div>
  );
}

function PaymentForm({ onNext, onBack }) {
  return (
    <div>
      <h2>Payment Details</h2>
      <form onSubmit={(e) => { e.preventDefault(); onNext(); }}>
        <input placeholder="Card number" required />
        <input placeholder="Expiry (MM/YY)" required />
        <button type="button" onClick={onBack}>Back</button>
        <button type="submit">Review Order</button>
      </form>
    </div>
  );
}

function OrderReview({ onBack, onSubmit }) {
  return (
    <div>
      <h2>Review Your Order</h2>
      <p>Order summary goes here...</p>
      <button onClick={onBack}>Back</button>
      <button onClick={onSubmit}>Place Order</button>
    </div>
  );
}

// Component map
const STEP_COMPONENTS = {
  shipping: ShippingForm,
  payment: PaymentForm,
  review: OrderReview,
};

const STEP_ORDER = ['shipping', 'payment', 'review'];

function CheckoutWizard() {
  const [stepIndex, setStepIndex] = useState(0);
  const currentStep = STEP_ORDER[stepIndex];
  const StepComponent = STEP_COMPONENTS[currentStep];

  if (!StepComponent) {
    return <p>Unknown checkout step.</p>;
  }

  return (
    <div className="checkout-wizard">
      {/* Progress indicator */}
      <div className="steps">
        {STEP_ORDER.map((step, i) => (
          <span
            key={step}
            className={i <= stepIndex ? 'step-active' : 'step-inactive'}
          >
            {step}
          </span>
        ))}
      </div>

      {/* Dynamic component rendering */}
      <StepComponent
        onNext={() => setStepIndex((i) => Math.min(i + 1, STEP_ORDER.length - 1))}
        onBack={() => setStepIndex((i) => Math.max(i - 1, 0))}
        onSubmit={() => alert('Order placed!')}
      />
    </div>
  );
}
```

**Why it works well:**
- **Open/closed principle** — Adding a new step only requires adding a component and an entry in the map. The wizard logic doesn't change.
- **Testability** — Each step component can be tested in isolation.
- **CMS integration** — A headless CMS can return a list of component names, and the frontend resolves them via the map, enabling content editors to compose pages without deploying code.
- **Type safety** — In TypeScript, you can type the map as `Record<StepName, React.ComponentType<StepProps>>` to ensure every step implements the required prop interface.

---

### Q10. How do you use the `key` prop as a mechanism to reset a component's internal state?

**Answer:**

When React sees a component with a **different key** than before, it **unmounts** the old instance and **mounts** a brand new one. This destroys all internal state (`useState`, `useReducer`, refs, DOM state). This is a powerful technique when you need to "reset" a component without writing explicit reset logic.

```jsx
import { useState } from 'react';

function EditForm({ user }) {
  // Local state — initialized from the user prop
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [bio, setBio] = useState(user.bio);

  const handleSubmit = (e) => {
    e.preventDefault();
    saveUser({ ...user, name, email, bio });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      <textarea value={bio} onChange={(e) => setBio(e.target.value)} />
      <button type="submit">Save</button>
    </form>
  );
}

function UserAdmin({ users }) {
  const [selectedUserId, setSelectedUserId] = useState(users[0]?.id);
  const selectedUser = users.find((u) => u.id === selectedUserId);

  return (
    <div className="admin-layout">
      <aside>
        <h3>Users</h3>
        {users.map((user) => (
          <button
            key={user.id}
            className={user.id === selectedUserId ? 'active' : ''}
            onClick={() => setSelectedUserId(user.id)}
          >
            {user.name}
          </button>
        ))}
      </aside>

      <main>
        {selectedUser && (
          // ✅ key={selectedUser.id} forces a full remount when user changes.
          // The form resets its internal state to the new user's data.
          <EditForm key={selectedUser.id} user={selectedUser} />
        )}
      </main>
    </div>
  );
}
```

**Without the key,** switching from Alice to Bob would keep the `EditForm` mounted — React would see the same component type in the same tree position and reuse it. The `useState` calls would retain Alice's values, ignoring Bob's props (because `useState` only uses the initial value on mount).

**With `key={selectedUser.id}`,** React treats it as a different component instance. It unmounts the Alice form (cleaning up effects), mounts a fresh Bob form, and `useState` initializes with Bob's data.

**Other use cases:**
- Resetting an animation component to replay from the start.
- Resetting an uncontrolled `<input>` or `<video>` element.
- Forcing a data-fetching component to refetch when a parameter changes.

---

### Q11. How do you optimize list rendering performance with `React.memo` and stable keys?

**Answer:**

When a parent component re-renders, every child in its `.map()` call re-renders by default — even if the child's props haven't changed. For large lists, this is wasteful. The combination of **`React.memo`** and **stable keys** prevents unnecessary re-renders.

```jsx
import { useState, useCallback, memo } from 'react';

// Memoized list item — only re-renders when its props change
const ProductCard = memo(function ProductCard({ product, onAddToCart }) {
  console.log(`Rendering ProductCard: ${product.name}`);
  return (
    <div className="product-card">
      <img src={product.image} alt={product.name} loading="lazy" />
      <h3>{product.name}</h3>
      <p>${product.price.toFixed(2)}</p>
      <button onClick={() => onAddToCart(product.id)}>Add to Cart</button>
    </div>
  );
});

function ProductGrid({ products }) {
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  // Stable callback — doesn't change between renders
  const handleAddToCart = useCallback((productId) => {
    setCart((prev) => [...prev, productId]);
  }, []);

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <input
        placeholder="Search products..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <p>{cart.length} items in cart</p>

      <div className="grid">
        {filtered.map((product) => (
          <ProductCard
            key={product.id}       // stable key from data
            product={product}       // same object reference if products array is stable
            onAddToCart={handleAddToCart} // stable via useCallback
          />
        ))}
      </div>
    </div>
  );
}
```

**Why this works:**
1. **`React.memo`** wraps `ProductCard` so it shallow-compares props before re-rendering. If `product` and `onAddToCart` haven't changed, the component skips rendering.
2. **`useCallback`** ensures `handleAddToCart` has a stable reference across renders. Without it, a new function is created every render, breaking `memo`'s shallow comparison.
3. **Stable keys** (`product.id`) ensure React matches the correct component instance to the correct data, preserving internal state and avoiding unnecessary unmount/remount cycles.

**When `memo` doesn't help:**
- If the `product` object is re-created every render (e.g., from a `.map()` transformation in the parent), `memo` sees a new reference and re-renders anyway. Use `useMemo` in the parent to stabilize the array, or pass primitive props.
- If most items change on every render, `memo` adds overhead (comparison cost) for no benefit.

---

### Q12. What are the trade-offs between paginated lists and infinite scroll, and how do you implement each in React 18?

**Answer:**

| Aspect | Pagination | Infinite Scroll |
|---|---|---|
| **UX** | Clear mental model; user knows page count | Feels seamless; great for browse/discovery |
| **SEO** | Each page can be a distinct URL | Harder to index content beyond first page |
| **Performance** | Bounded DOM size per page | DOM grows over time (needs virtualization) |
| **Accessibility** | Easy to navigate with keyboard/screen reader | Requires careful ARIA labeling |
| **Back button** | Works naturally with URL params | Scroll position lost without extra work |

**Paginated list implementation:**

```jsx
import { useState, useEffect } from 'react';

function PaginatedArticles() {
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const PAGE_SIZE = 20;

  useEffect(() => {
    setIsLoading(true);
    fetch(`/api/articles?page=${page}&limit=${PAGE_SIZE}`)
      .then((res) => res.json())
      .then((data) => {
        setArticles(data.items);
        setTotalPages(Math.ceil(data.total / PAGE_SIZE));
      })
      .finally(() => setIsLoading(false));
  }, [page]);

  if (isLoading) return <ArticleListSkeleton count={PAGE_SIZE} />;

  return (
    <div>
      <ul>
        {articles.map((article) => (
          <li key={article.id}>
            <a href={`/articles/${article.slug}`}>{article.title}</a>
            <span>{article.date}</span>
          </li>
        ))}
      </ul>

      <nav aria-label="Pagination">
        <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        {Array.from({ length: totalPages }, (_, i) => (
          <button
            key={i + 1}
            aria-current={page === i + 1 ? 'page' : undefined}
            className={page === i + 1 ? 'active' : ''}
            onClick={() => setPage(i + 1)}
          >
            {i + 1}
          </button>
        ))}
        <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </nav>
    </div>
  );
}
```

**Infinite scroll implementation:**

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

function InfiniteArticles() {
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const observerRef = useRef(null);

  useEffect(() => {
    setIsLoading(true);
    fetch(`/api/articles?page=${page}&limit=20`)
      .then((res) => res.json())
      .then((data) => {
        setArticles((prev) => [...prev, ...data.items]);
        setHasMore(data.items.length === 20);
      })
      .finally(() => setIsLoading(false));
  }, [page]);

  // IntersectionObserver to detect when the sentinel is visible
  const sentinelRef = useCallback(
    (node) => {
      if (isLoading) return;
      if (observerRef.current) observerRef.current.disconnect();

      observerRef.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && hasMore) {
            setPage((p) => p + 1);
          }
        },
        { rootMargin: '200px' } // trigger 200px before reaching the end
      );

      if (node) observerRef.current.observe(node);
    },
    [isLoading, hasMore]
  );

  return (
    <div>
      <ul>
        {articles.map((article) => (
          <li key={article.id}>
            <a href={`/articles/${article.slug}`}>{article.title}</a>
          </li>
        ))}
      </ul>

      {/* Sentinel element — triggers next page load when visible */}
      {hasMore && <div ref={sentinelRef} style={{ height: 1 }} />}
      {isLoading && <Spinner />}
      {!hasMore && <p>You've reached the end.</p>}
    </div>
  );
}
```

**Production recommendation:** For infinite scroll with large datasets, combine this with virtualization (e.g., `react-window`) to keep the DOM size bounded even as the data grows. Without virtualization, an infinite list with thousands of items will degrade scrolling performance.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you implement virtualized lists with `react-window` to efficiently render 10,000+ items?

**Answer:**

Virtualization (also called "windowing") renders only the items currently visible in the viewport, plus a small overscan buffer. Instead of 10,000 DOM nodes, you might only have 20–30 at any given time. The `react-window` library is the de facto standard for this in React.

```jsx
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { memo } from 'react';

// Generate test data
const items = Array.from({ length: 50000 }, (_, i) => ({
  id: `item-${i}`,
  name: `Product #${i + 1}`,
  price: (Math.random() * 100).toFixed(2),
  inStock: Math.random() > 0.3,
}));

// Memoized row renderer
const Row = memo(function Row({ index, style, data }) {
  const item = data[index];
  return (
    <div
      style={{
        ...style,
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        borderBottom: '1px solid #eee',
        backgroundColor: index % 2 === 0 ? '#fafafa' : '#fff',
      }}
    >
      <span style={{ flex: 1 }}>{item.name}</span>
      <span style={{ width: 80 }}>${item.price}</span>
      <span style={{ width: 80, color: item.inStock ? 'green' : 'red' }}>
        {item.inStock ? 'In Stock' : 'Out'}
      </span>
    </div>
  );
});

function VirtualizedProductList() {
  return (
    <div style={{ height: '80vh', width: '100%' }}>
      <AutoSizer>
        {({ height, width }) => (
          <List
            height={height}
            width={width}
            itemCount={items.length}
            itemSize={48}          // fixed row height in pixels
            itemData={items}        // passed to each Row as data prop
            overscanCount={10}      // render 10 extra rows outside viewport
          >
            {Row}
          </List>
        )}
      </AutoSizer>
    </div>
  );
}
```

**For variable-height rows, use `VariableSizeList`:**

```jsx
import { VariableSizeList } from 'react-window';

function ChatMessageList({ messages }) {
  const listRef = useRef(null);

  // Estimate row height based on message length
  const getItemSize = (index) => {
    const msg = messages[index];
    const lineCount = Math.ceil(msg.text.length / 60); // rough estimate
    return Math.max(48, lineCount * 24 + 32);           // min 48px
  };

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    listRef.current?.scrollToItem(messages.length - 1, 'end');
  }, [messages.length]);

  const MessageRow = ({ index, style }) => {
    const msg = messages[index];
    return (
      <div style={{ ...style, padding: '8px 16px' }}>
        <strong>{msg.sender}</strong>
        <p>{msg.text}</p>
        <small>{msg.timestamp}</small>
      </div>
    );
  };

  return (
    <VariableSizeList
      ref={listRef}
      height={600}
      width={400}
      itemCount={messages.length}
      itemSize={getItemSize}
      overscanCount={5}
    >
      {MessageRow}
    </VariableSizeList>
  );
}
```

**Key considerations:**
- **`itemData` prop** — Pass shared data (the items array) via `itemData` rather than closing over it. This enables `memo` to work correctly because `data` is a stable reference.
- **`overscanCount`** — A higher value reduces flicker during fast scrolling but increases DOM nodes. 5–10 is a good default.
- **`AutoSizer`** — Use `react-virtualized-auto-sizer` so the list fills its container responsively.
- **For grids,** use `FixedSizeGrid` or `VariableSizeGrid` from `react-window`.

---

### Q14. How do you implement a drag-and-drop reorderable list in React, and what key management issues arise?

**Answer:**

Drag-and-drop reorderable lists require careful key management because the order of items changes during and after a drag. The `@dnd-kit` library (successor to `react-beautiful-dnd`) is the modern choice for React 18 with full support for concurrent features.

```jsx
import { useState } from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

function SortableItem({ id, children }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    padding: '12px 16px',
    margin: '4px 0',
    background: '#fff',
    border: '1px solid #ddd',
    borderRadius: 8,
    cursor: 'grab',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <span className="drag-handle">⠿</span>
      {children}
    </div>
  );
}

function ReorderableTaskList() {
  const [tasks, setTasks] = useState([
    { id: 'task-1', title: 'Design system review', priority: 'high' },
    { id: 'task-2', title: 'API integration tests', priority: 'medium' },
    { id: 'task-3', title: 'Deploy staging build', priority: 'high' },
    { id: 'task-4', title: 'Update documentation', priority: 'low' },
    { id: 'task-5', title: 'Code review for PR #42', priority: 'medium' },
  ]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    setTasks((items) => {
      const oldIndex = items.findIndex((i) => i.id === active.id);
      const newIndex = items.findIndex((i) => i.id === over.id);
      const reordered = arrayMove(items, oldIndex, newIndex);

      // Persist new order to backend
      fetch('/api/tasks/reorder', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ taskIds: reordered.map((t) => t.id) }),
      });

      return reordered;
    });
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={tasks} strategy={verticalListSortingStrategy}>
        {tasks.map((task) => (
          <SortableItem key={task.id} id={task.id}>
            <span>{task.title}</span>
            <span className={`priority-${task.priority}`}>{task.priority}</span>
          </SortableItem>
        ))}
      </SortableContext>
    </DndContext>
  );
}
```

**Key management considerations:**
1. **Keys must be stable IDs, never indices.** During a drag, items reorder. If keys are indices, React remounts items at the wrong positions, causing visual glitches and state loss.
2. **The `id` passed to `useSortable` must match the `key`.** `@dnd-kit` uses the id to track which item is being dragged. If they're out of sync, the wrong item gets picked up.
3. **Optimistic reordering** — Update the local state immediately (`arrayMove`) and persist to the backend asynchronously. If the API call fails, roll back.
4. **Accessibility** — `@dnd-kit` supports keyboard sensors out of the box, so items can be reordered without a mouse. Announce drag status to screen readers via `aria-live` regions.

---

### Q15. How do you render recursive tree data structures (like file explorers or nested comments) in React?

**Answer:**

Recursive data structures require recursive components — a component that renders itself for each child node. The key insight is that each level of the tree is the same UI pattern, just nested deeper.

```jsx
import { useState, memo } from 'react';

// Sample tree data
const fileTree = {
  id: 'root',
  name: 'project',
  type: 'folder',
  children: [
    {
      id: 'src',
      name: 'src',
      type: 'folder',
      children: [
        {
          id: 'components',
          name: 'components',
          type: 'folder',
          children: [
            { id: 'button', name: 'Button.tsx', type: 'file' },
            { id: 'modal', name: 'Modal.tsx', type: 'file' },
            { id: 'table', name: 'DataTable.tsx', type: 'file' },
          ],
        },
        { id: 'app', name: 'App.tsx', type: 'file' },
        { id: 'index', name: 'index.tsx', type: 'file' },
      ],
    },
    { id: 'package', name: 'package.json', type: 'file' },
    { id: 'readme', name: 'README.md', type: 'file' },
  ],
};

// Recursive tree node component
const TreeNode = memo(function TreeNode({ node, depth = 0, onSelect }) {
  const [isExpanded, setIsExpanded] = useState(depth < 2); // auto-expand first 2 levels
  const isFolder = node.type === 'folder';
  const hasChildren = isFolder && node.children?.length > 0;

  const handleToggle = () => {
    if (isFolder) setIsExpanded((prev) => !prev);
  };

  return (
    <div>
      <div
        role="treeitem"
        aria-expanded={isFolder ? isExpanded : undefined}
        className="tree-node"
        style={{ paddingLeft: depth * 20 }}
        onClick={() => {
          handleToggle();
          onSelect(node);
        }}
      >
        {isFolder ? (isExpanded ? '📂' : '📁') : '📄'}
        <span style={{ marginLeft: 6 }}>{node.name}</span>
      </div>

      {/* Recursion: render children if expanded */}
      {isExpanded && hasChildren && (
        <div role="group">
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
});

function FileExplorer() {
  const [selectedNode, setSelectedNode] = useState(null);

  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <div role="tree" className="file-tree" style={{ width: 280 }}>
        <TreeNode node={fileTree} onSelect={setSelectedNode} />
      </div>

      <div className="file-preview" style={{ flex: 1 }}>
        {selectedNode ? (
          <div>
            <h3>{selectedNode.name}</h3>
            <p>Type: {selectedNode.type}</p>
            <p>ID: {selectedNode.id}</p>
          </div>
        ) : (
          <p>Select a file to preview</p>
        )}
      </div>
    </div>
  );
}
```

**Nested comments (another common recursive structure):**

```jsx
const CommentThread = memo(function CommentThread({ comment, depth = 0 }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const maxDepth = 8;

  return (
    <div
      className="comment"
      style={{
        marginLeft: Math.min(depth, maxDepth) * 24,
        borderLeft: depth > 0 ? '2px solid #e0e0e0' : 'none',
        paddingLeft: depth > 0 ? 12 : 0,
      }}
    >
      <div className="comment-header">
        <strong>{comment.author}</strong>
        <span className="comment-time">{comment.timeAgo}</span>
        {comment.replies?.length > 0 && (
          <button onClick={() => setIsCollapsed((c) => !c)}>
            {isCollapsed ? `[+${comment.replies.length} replies]` : '[-]'}
          </button>
        )}
      </div>
      <p>{comment.text}</p>

      {!isCollapsed &&
        comment.replies?.map((reply) => (
          <CommentThread key={reply.id} comment={reply} depth={depth + 1} />
        ))}
    </div>
  );
});
```

**Production tips:**
- **Cap the recursion depth** — Render a "Load more" link after a certain depth instead of going infinitely deep. This prevents performance and layout issues.
- **Memoize nodes** — Use `React.memo` to prevent re-rendering the entire tree when one node changes.
- **Use stable keys** — Each node must have a unique ID. Never use the index as a key in recursive structures, because insertion/removal at any level would cascade key mismatches.
- **Virtualize large trees** — For trees with thousands of nodes, consider `react-arborist` or a custom virtualized tree built on `react-window`.

---

### Q16. How do you implement feature flags and A/B testing with conditional rendering in a production React application?

**Answer:**

Feature flags let you deploy code to production without enabling it for all users. A/B testing extends this by assigning users to experiment groups and measuring outcomes. Both rely heavily on conditional rendering.

```jsx
import { createContext, useContext, useEffect, useState } from 'react';

// Feature flag context
const FeatureFlagContext = createContext({});

function FeatureFlagProvider({ children }) {
  const [flags, setFlags] = useState({});
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Fetch flags from your feature flag service (LaunchDarkly, Unleash, etc.)
    fetch('/api/feature-flags', {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
      .then((res) => res.json())
      .then((data) => {
        setFlags(data.flags);
        setIsLoaded(true);
      })
      .catch(() => {
        // Fall back to defaults on error
        setFlags({});
        setIsLoaded(true);
      });
  }, []);

  if (!isLoaded) return <FullPageSpinner />;

  return (
    <FeatureFlagContext.Provider value={flags}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

// Hook to check a single flag
function useFeatureFlag(flagName, defaultValue = false) {
  const flags = useContext(FeatureFlagContext);
  return flags[flagName] ?? defaultValue;
}

// Hook for A/B test variants
function useExperiment(experimentName) {
  const flags = useContext(FeatureFlagContext);
  const experiment = flags[experimentName];
  return {
    variant: experiment?.variant ?? 'control',
    isEnrolled: experiment?.enrolled ?? false,
  };
}

// Declarative FeatureFlag component
function FeatureFlag({ name, fallback = null, children }) {
  const isEnabled = useFeatureFlag(name);
  return isEnabled ? children : fallback;
}

// Production usage
function PricingPage() {
  const { variant } = useExperiment('pricing_page_redesign');
  const showAnnualToggle = useFeatureFlag('annual_pricing_toggle');

  return (
    <div>
      {/* A/B test: different pricing layouts */}
      {variant === 'control' && <PricingGridClassic />}
      {variant === 'variant_a' && <PricingGridCards />}
      {variant === 'variant_b' && <PricingSlider />}

      {/* Feature flag: gradual rollout of annual toggle */}
      <FeatureFlag name="annual_pricing_toggle" fallback={<MonthlyOnlyNotice />}>
        <BillingCycleToggle />
      </FeatureFlag>

      {/* Combine flags with role checks */}
      <FeatureFlag name="enterprise_tier">
        <RequireRole roles={['sales', 'admin']}>
          <EnterprisePricingCard />
        </RequireRole>
      </FeatureFlag>
    </div>
  );
}
```

**Tracking and measurement:**

```jsx
function useTrackExperiment(experimentName) {
  const { variant, isEnrolled } = useExperiment(experimentName);

  useEffect(() => {
    if (isEnrolled) {
      // Send exposure event to analytics
      analytics.track('experiment_exposure', {
        experiment: experimentName,
        variant,
        timestamp: Date.now(),
      });
    }
  }, [experimentName, variant, isEnrolled]);

  return variant;
}

function CheckoutButton() {
  const variant = useTrackExperiment('checkout_cta_test');

  const ctaText = {
    control: 'Proceed to Checkout',
    variant_a: 'Buy Now',
    variant_b: 'Complete Your Purchase',
  };

  return (
    <button className="checkout-btn" onClick={handleCheckout}>
      {ctaText[variant] ?? ctaText.control}
    </button>
  );
}
```

**Production best practices:**
- **Render the default/control experience on the server** and evaluate flags client-side to avoid layout shift. Or, better: evaluate flags server-side and inject them into the initial HTML.
- **Never evaluate flags in every render.** Fetch them once, put them in context, and read from context. Flag evaluation should be `O(1)` (object lookup).
- **Clean up old flags.** Dead feature flags are tech debt. After a rollout is at 100% and stable, remove the flag and the old code path.
- **Test both branches.** Your test suite should cover both the enabled and disabled state of every feature flag.

---

### Q17. How do you implement skeleton loading states and use Suspense boundaries for lists in React 18?

**Answer:**

Skeleton screens show a placeholder layout that mirrors the shape of the real content, giving users a sense of structure before data arrives. React 18's `<Suspense>` integrates with data-fetching libraries (React Query, SWR, Relay) to declaratively manage loading states.

```jsx
import { Suspense, memo } from 'react';
import { useSuspenseQuery } from '@tanstack/react-query';

// Skeleton component for a list item
function ArticleCardSkeleton() {
  return (
    <div className="article-card skeleton" aria-busy="true">
      <div className="skeleton-image" style={{ height: 200, background: '#e0e0e0' }} />
      <div className="skeleton-text" style={{ height: 20, width: '80%', margin: '12px 0' }} />
      <div className="skeleton-text" style={{ height: 14, width: '60%' }} />
      <div className="skeleton-text" style={{ height: 14, width: '90%', marginTop: 8 }} />
    </div>
  );
}

function ArticleListSkeleton({ count = 6 }) {
  return (
    <div className="article-grid" role="status" aria-label="Loading articles">
      {Array.from({ length: count }, (_, i) => (
        <ArticleCardSkeleton key={i} />
      ))}
    </div>
  );
}

// Real article card
const ArticleCard = memo(function ArticleCard({ article }) {
  return (
    <div className="article-card">
      <img src={article.coverImage} alt={article.title} loading="lazy" />
      <h3>{article.title}</h3>
      <p>{article.excerpt}</p>
      <span className="author">{article.author}</span>
    </div>
  );
});

// Data-fetching component (throws a promise for Suspense)
function ArticleList({ category }) {
  const { data: articles } = useSuspenseQuery({
    queryKey: ['articles', category],
    queryFn: () =>
      fetch(`/api/articles?category=${category}`).then((r) => r.json()),
  });

  if (articles.length === 0) {
    return <p>No articles found in "{category}".</p>;
  }

  return (
    <div className="article-grid">
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}

// Parent with Suspense boundary
function ArticlePage() {
  const [category, setCategory] = useState('technology');

  return (
    <div>
      <nav>
        {['technology', 'science', 'design'].map((cat) => (
          <button
            key={cat}
            className={cat === category ? 'active' : ''}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </nav>

      {/* Suspense catches the thrown promise from useSuspenseQuery */}
      <Suspense fallback={<ArticleListSkeleton count={6} />}>
        <ArticleList category={category} />
      </Suspense>
    </div>
  );
}
```

**Nested Suspense for progressive disclosure:**

```jsx
function DashboardPage() {
  return (
    <div className="dashboard">
      {/* Critical content loads first */}
      <Suspense fallback={<HeaderSkeleton />}>
        <DashboardHeader />
      </Suspense>

      <div className="dashboard-grid">
        {/* Each section has its own boundary — they load independently */}
        <Suspense fallback={<MetricsCardsSkeleton />}>
          <MetricsCards />
        </Suspense>

        <Suspense fallback={<RecentOrdersSkeleton />}>
          <RecentOrdersList />
        </Suspense>

        <Suspense fallback={<ChartSkeleton />}>
          <RevenueChart />
        </Suspense>
      </div>
    </div>
  );
}
```

**Best practices:**
- **Match skeleton layout to real content.** If your card has an image, title, and two lines of text, the skeleton should have corresponding rectangles in the same positions.
- **Use `aria-busy="true"` and `role="status"`** on skeletons for screen reader accessibility.
- **Place Suspense boundaries strategically.** One global boundary means the entire page shows a spinner. Multiple granular boundaries let sections load independently — the header appears first, then metrics, then the list.
- **Use `useTransition`** for tab switches so the old content stays visible while the new data loads, avoiding a flash of skeleton.

---

### Q18. How does streaming SSR in React 18 work for server-rendered lists, and what role do Suspense boundaries play?

**Answer:**

React 18's streaming SSR (`renderToPipeableStream`) sends HTML to the browser in chunks as data becomes available, instead of waiting for everything to resolve before sending a single HTML payload. `<Suspense>` boundaries define the chunk boundaries — each Suspense boundary can stream its content independently once its data resolves.

```jsx
// server.js (Node.js with Express)
import express from 'express';
import { renderToPipeableStream } from 'react-dom/server';
import App from './App';

const app = express();

app.get('*', (req, res) => {
  const { pipe, abort } = renderToPipeableStream(<App url={req.url} />, {
    bootstrapScripts: ['/static/client.js'],

    onShellReady() {
      // The shell (everything outside Suspense boundaries) is ready.
      // Start streaming immediately.
      res.setHeader('Content-Type', 'text/html');
      pipe(res);
    },

    onShellError(error) {
      // If the shell fails, send a fallback
      res.statusCode = 500;
      res.send('<!DOCTYPE html><html><body><p>Server error</p></body></html>');
    },

    onAllReady() {
      // Called when everything (including Suspense) is complete.
      // Useful for crawlers/bots that need the full page.
    },

    onError(error) {
      console.error('SSR streaming error:', error);
    },
  });

  // Abort if the response takes too long
  setTimeout(abort, 10000);
});
```

```jsx
// App.jsx — server-rendered with Suspense boundaries
import { Suspense } from 'react';

function App({ url }) {
  return (
    <html>
      <head>
        <title>Product Catalog</title>
      </head>
      <body>
        {/* Shell: streamed immediately with onShellReady */}
        <header>
          <h1>Our Products</h1>
          <SearchBar />
        </header>

        {/* This Suspense boundary streams its content when products resolve */}
        <Suspense fallback={<ProductListSkeleton count={12} />}>
          <ProductList category={getCategoryFromUrl(url)} />
        </Suspense>

        {/* This streams independently — doesn't block the product list */}
        <Suspense fallback={<RecommendationsSkeleton />}>
          <PersonalizedRecommendations />
        </Suspense>

        <footer>© 2025 Our Store</footer>
      </body>
    </html>
  );
}
```

**What happens at runtime:**

1. React renders the "shell" — the `<header>`, `<footer>`, and skeleton fallbacks for both `<Suspense>` boundaries. This HTML is streamed to the browser via `onShellReady`.
2. The browser paints the header, skeletons, and footer immediately.
3. When `ProductList`'s data resolves, React streams the product list HTML along with an inline `<script>` that replaces the skeleton in the DOM. The user sees products appear without a full-page re-render.
4. When `PersonalizedRecommendations` resolves (perhaps after a slower API call), its HTML streams and replaces its skeleton independently.
5. Selective hydration kicks in — React hydrates the sections that arrived first so they become interactive before the slower sections finish streaming.

**Benefits for lists specifically:**
- A list of 100 products can be fully server-rendered and streamed. The browser starts rendering the first products while the server is still generating the last ones.
- Combined with Suspense, you can stream the critical product list first and defer non-critical sections (recommendations, reviews) to later chunks.
- SEO crawlers receive the full HTML content (via `onAllReady` fallback), ensuring every product is indexed.

---

### Q19. How do you build a production data table with sorting, filtering, and virtualization in React 18?

**Answer:**

A production data table combines several techniques: column definitions, sorting state, filter state, virtualization for large datasets, and memoization for performance. The `@tanstack/react-table` (TanStack Table v8) library provides the headless logic, and you pair it with `react-window` for virtualization.

```jsx
import { useState, useMemo, useCallback, useRef } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from '@tanstack/react-table';
import { FixedSizeList } from 'react-window';

// Column definitions
const columns = [
  {
    accessorKey: 'id',
    header: 'ID',
    size: 80,
  },
  {
    accessorKey: 'name',
    header: 'Name',
    size: 200,
    cell: ({ getValue }) => <strong>{getValue()}</strong>,
  },
  {
    accessorKey: 'email',
    header: 'Email',
    size: 250,
  },
  {
    accessorKey: 'department',
    header: 'Department',
    size: 150,
    filterFn: 'equals',
  },
  {
    accessorKey: 'salary',
    header: 'Salary',
    size: 120,
    cell: ({ getValue }) => `$${getValue().toLocaleString()}`,
    sortingFn: 'basic',
  },
  {
    accessorKey: 'startDate',
    header: 'Start Date',
    size: 130,
    cell: ({ getValue }) => new Date(getValue()).toLocaleDateString(),
  },
];

function ProductionDataTable({ data }) {
  const [sorting, setSorting] = useState([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [columnFilters, setColumnFilters] = useState([]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter, columnFilters },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const { rows } = table.getRowModel();
  const listRef = useRef(null);

  // Reset scroll when filters/sorting change
  useMemo(() => {
    listRef.current?.scrollTo(0);
  }, [sorting, globalFilter, columnFilters]);

  // Virtualized row renderer
  const RenderRow = useCallback(
    ({ index, style }) => {
      const row = rows[index];
      return (
        <div
          style={{
            ...style,
            display: 'flex',
            alignItems: 'center',
            borderBottom: '1px solid #eee',
            backgroundColor: index % 2 === 0 ? '#fff' : '#fafafa',
          }}
        >
          {row.getVisibleCells().map((cell) => (
            <div
              key={cell.id}
              style={{
                width: cell.column.getSize(),
                padding: '0 12px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </div>
          ))}
        </div>
      );
    },
    [rows]
  );

  return (
    <div className="data-table-container">
      {/* Global search */}
      <div className="table-toolbar">
        <input
          placeholder="Search all columns..."
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="global-search"
        />
        <span className="row-count">
          {rows.length.toLocaleString()} of {data.length.toLocaleString()} rows
        </span>
      </div>

      {/* Column filters */}
      <div className="column-filters">
        {table.getHeaderGroups().map((headerGroup) =>
          headerGroup.headers.map((header) =>
            header.column.getCanFilter() ? (
              <input
                key={header.id}
                placeholder={`Filter ${header.column.columnDef.header}...`}
                value={(header.column.getFilterValue() ?? '')}
                onChange={(e) => header.column.setFilterValue(e.target.value)}
                style={{ width: header.column.getSize() }}
              />
            ) : null
          )
        )}
      </div>

      {/* Header */}
      <div className="table-header" style={{ display: 'flex', fontWeight: 'bold' }}>
        {table.getHeaderGroups().map((headerGroup) =>
          headerGroup.headers.map((header) => (
            <div
              key={header.id}
              style={{
                width: header.column.getSize(),
                padding: '8px 12px',
                cursor: header.column.getCanSort() ? 'pointer' : 'default',
                userSelect: 'none',
              }}
              onClick={header.column.getToggleSortingHandler()}
            >
              {flexRender(header.column.columnDef.header, header.getContext())}
              {{ asc: ' ▲', desc: ' ▼' }[header.column.getIsSorted()] ?? ''}
            </div>
          ))
        )}
      </div>

      {/* Virtualized body */}
      {rows.length > 0 ? (
        <FixedSizeList
          ref={listRef}
          height={600}
          width="100%"
          itemCount={rows.length}
          itemSize={44}
          overscanCount={15}
        >
          {RenderRow}
        </FixedSizeList>
      ) : (
        <div className="empty-state">
          <p>No results match your filters.</p>
        </div>
      )}
    </div>
  );
}
```

**Usage with sample data:**

```jsx
function EmployeeDirectory() {
  const { data, isLoading } = useSuspenseQuery({
    queryKey: ['employees'],
    queryFn: () => fetch('/api/employees').then((r) => r.json()),
  });

  if (isLoading) return <TableSkeleton rows={20} cols={6} />;

  return (
    <div>
      <h1>Employee Directory ({data.length.toLocaleString()} employees)</h1>
      <ProductionDataTable data={data} />
    </div>
  );
}
```

**Architecture decisions:**
- **Headless table library** (`@tanstack/react-table`) provides sorting, filtering, pagination, and grouping logic without any UI — you render whatever markup you want. This means full control over styling and layout.
- **Virtualization** ensures only ~15–20 rows are in the DOM at any time, even with 100,000 records.
- **Memoized `RenderRow`** with `useCallback` prevents `react-window` from re-rendering every visible row when only one cell changes.
- **Stable keys** from `cell.id` (provided by TanStack Table) ensure correct reconciliation during sorting and filtering.

---

### Q20. How does React's reconciliation algorithm use keys to diff lists, and what happens internally when keys are missing, duplicated, or unstable?

**Answer:**

React's reconciliation algorithm (the "fiber reconciler") compares the previous and next virtual DOM trees to determine the minimum set of DOM mutations needed. For lists, the algorithm relies heavily on **keys** to match old children to new children.

**How the algorithm works with keys:**

When React encounters a list of elements, it builds a **map** from key to fiber (the internal representation of each element). For each child in the new list, React looks up the corresponding fiber from the old list by key. If a match is found, the fiber is reused (updated in place). If not, a new fiber is created.

```jsx
// Conceptual illustration of what React does internally

// Previous render:
// [{ key: 'a', text: 'Apple' }, { key: 'b', text: 'Banana' }, { key: 'c', text: 'Cherry' }]

// Next render (item 'b' removed, item 'd' added):
// [{ key: 'a', text: 'Apple' }, { key: 'c', text: 'Cherry' }, { key: 'd', text: 'Date' }]

// React's diffing process:
// 1. Build map of old keys: { a: fiberA, b: fiberB, c: fiberC }
// 2. Walk new list:
//    - key 'a': found in map → reuse fiberA, update props if needed
//    - key 'c': found in map → reuse fiberC, move it to new position
//    - key 'd': NOT in map → create new fiberD
// 3. Any old keys not seen in new list (key 'b') → delete fiberB, unmount
// Result: 0 creates for 'a', 1 move for 'c', 1 create for 'd', 1 delete for 'b'
```

**What happens without keys (or with index keys):**

```jsx
// React falls back to index-based diffing when keys are not provided.

// Previous: [Apple, Banana, Cherry]  → indices [0, 1, 2]
// Next:     [Apple, Cherry, Date]    → indices [0, 1, 2]

// Index-based comparison:
// Index 0: Apple → Apple (no change — correct)
// Index 1: Banana → Cherry (React updates Banana's fiber with Cherry's props)
// Index 2: Cherry → Date (React updates Cherry's fiber with Date's props)

// Problem: React didn't "move" Cherry — it mutated Banana into Cherry.
// This means Banana's component STATE is now attached to Cherry's UI.
// Any uncontrolled inputs, focus state, animations, or refs are corrupted.
```

**Demonstration of the problem:**

```jsx
import { useState } from 'react';

function ListItem({ name }) {
  const [notes, setNotes] = useState('');
  return (
    <li>
      <strong>{name}</strong>
      <input
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Add notes..."
      />
    </li>
  );
}

function BuggyList() {
  const [items, setItems] = useState(['Alice', 'Bob', 'Carol']);

  const removeFirst = () => setItems((prev) => prev.slice(1));

  return (
    <div>
      <button onClick={removeFirst}>Remove first item</button>
      <ul>
        {items.map((name, index) => (
          // ❌ Using index as key
          <ListItem key={index} name={name} />
        ))}
      </ul>
      {/* Type notes for Alice, then click "Remove first".
          Bob now shows Alice's notes — state followed the index, not the data. */}
    </div>
  );
}

function CorrectList() {
  const [items, setItems] = useState([
    { id: '1', name: 'Alice' },
    { id: '2', name: 'Bob' },
    { id: '3', name: 'Carol' },
  ]);

  const removeFirst = () => setItems((prev) => prev.slice(1));

  return (
    <div>
      <button onClick={removeFirst}>Remove first item</button>
      <ul>
        {items.map((item) => (
          // ✅ Stable key — state follows the data
          <ListItem key={item.id} name={item.name} />
        ))}
      </ul>
    </div>
  );
}
```

**What happens with duplicate keys:**

```jsx
// React warns in development: "Encountered two children with the same key"
// At runtime, React's behavior is UNDEFINED with duplicate keys:
const items = [
  { id: 'dup', name: 'First' },
  { id: 'dup', name: 'Second' },  // same key!
  { id: 'dup', name: 'Third' },   // same key!
];

// React may:
// - Only render the first item and silently drop the others
// - Render all but lose track during updates, causing state to jump between items
// - Produce inconsistent DOM mutations on subsequent re-renders
// The behavior is unpredictable and varies between React versions.
```

**What happens with unstable keys (generated at render time):**

```jsx
// ❌ Key is generated fresh every render — defeats reconciliation
{items.map((item) => (
  <ListItem key={Math.random()} name={item.name} />
))}

// Every render, every key is new → React unmounts ALL old items and mounts ALL new ones.
// This means:
// 1. All component state is destroyed every render
// 2. All DOM nodes are recreated (expensive)
// 3. All effects re-run (cleanup + setup)
// 4. Focus is lost, animations restart, inputs reset
// 5. Performance is terrible for large lists
```

**Summary of key behaviors:**

| Scenario | Reconciliation | State | DOM | Performance |
|---|---|---|---|---|
| Stable unique keys | Correct matching | Preserved | Minimal mutations | Optimal |
| Index keys (static list) | Correct | Preserved | Minimal | OK |
| Index keys (dynamic list) | Incorrect matching | Corrupted | Unnecessary mutations | Suboptimal |
| Duplicate keys | Undefined | Unpredictable | Unpredictable | Degraded |
| Unstable keys (`Math.random()`) | Full remount | Destroyed | Full recreate | Terrible |
| Missing keys | Index fallback + warning | Same as index | Same as index | Same as index |

**The golden rule:** Always use a **stable, unique identifier** from your data as the key. Database IDs, UUIDs, slugs, or any immutable field that uniquely identifies each item. Generate IDs at data-creation time, never at render time.
