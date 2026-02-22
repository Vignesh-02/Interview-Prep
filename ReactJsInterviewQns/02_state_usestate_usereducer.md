# State Management with `useState` and `useReducer` in React 18

## Introduction

State is the beating heart of any interactive React application. In React's declarative model, the UI is a function of state — when state changes, React re-renders the component tree to reflect the new reality. Unlike regular JavaScript variables that vanish between function calls, React state **persists across renders** and **triggers re-renders** when updated. React 18 introduced significant improvements to how state updates are batched and processed, making state management more predictable and performant than ever before.

React provides two primary hooks for managing local component state: `useState` and `useReducer`. While `useState` is ideal for simple, independent pieces of state (a toggle, an input value, a counter), `useReducer` shines when state logic becomes complex — when the next state depends on the previous one through multiple possible actions, or when several sub-values are tightly coupled. Understanding when and how to use each hook, how React 18 batches their updates, and the common pitfalls around closures and immutability is essential knowledge for any production React developer.

Here is a minimal illustration that contrasts both hooks side by side:

```jsx
import { useState, useReducer } from 'react';

// --- useState approach ---
function CounterWithState() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(prev => prev + 1)}>Count: {count}</button>;
}

// --- useReducer approach ---
function counterReducer(state, action) {
  switch (action.type) {
    case 'increment': return { count: state.count + 1 };
    case 'decrement': return { count: state.count - 1 };
    case 'reset':     return { count: 0 };
    default: throw new Error(`Unknown action: ${action.type}`);
  }
}

function CounterWithReducer() {
  const [state, dispatch] = useReducer(counterReducer, { count: 0 });
  return (
    <div>
      <span>Count: {state.count}</span>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>−</button>
      <button onClick={() => dispatch({ type: 'reset' })}>Reset</button>
    </div>
  );
}
```

Both hooks store state that survives re-renders and trigger UI updates. The choice between them is a matter of complexity, testability, and team preference — topics we will explore in depth throughout these 20 questions.

---

## Beginner Level (Q1–Q5)

---

### Q1. What is state in React and why is it needed?

**Answer:**

State is a built-in mechanism in React that allows components to **remember values between renders** and **trigger re-renders** when those values change. Without state, a React component is a pure function of its props — it can only display what it is given from the outside. State gives a component its own internal memory.

**Why can't we just use regular variables?**

A regular `let` variable declared inside a component function is re-created from scratch on every render. Changes to it are invisible to React — the component won't re-render, and the value is lost the moment the function exits. State, managed through `useState` or `useReducer`, is stored by React _outside_ the component function in an internal fiber data structure, so it persists across renders.

**Key characteristics of React state:**

1. **Persistent** — values survive between renders.
2. **Triggers re-renders** — calling the setter function tells React to re-render the component.
3. **Scoped to the component instance** — each instance of a component has its own independent state.
4. **Immutable by convention** — you replace state rather than mutate it.

```jsx
import { useState } from 'react';

function ToggleButton() {
  // `isOn` persists across renders; `setIsOn` triggers a re-render
  const [isOn, setIsOn] = useState(false);

  // This regular variable is re-created every render — useless for tracking state
  let clickCount = 0;

  const handleClick = () => {
    clickCount += 1;          // Lost on next render — React doesn't know about this
    setIsOn(prev => !prev);   // React will re-render with the new value
    console.log(clickCount);  // Always logs 1, because it resets each render
  };

  return (
    <button onClick={handleClick}>
      {isOn ? 'ON' : 'OFF'}
    </button>
  );
}
```

**Production insight:** A very common beginner mistake is attempting to track derived or temporary values in state when a `const` or `useMemo` would suffice (see Q11 on derived state). State should be reserved for values that (a) change over time and (b) need to trigger a UI update when they do.

---

### Q2. How do you initialize, read, and update state with `useState`?

**Answer:**

The `useState` hook follows a simple API:

```jsx
const [currentValue, setterFunction] = useState(initialValue);
```

- **`initialValue`** — the value used on the very first render. It is ignored on subsequent renders.
- **`currentValue`** — the state value for the current render.
- **`setterFunction`** — a stable function that enqueues a state update and triggers a re-render.

You can pass **any type** as the initial value: number, string, boolean, object, array, or `null`.

```jsx
import { useState } from 'react';

function UserProfile() {
  // Initialize different types of state
  const [name, setName] = useState('');           // string
  const [age, setAge] = useState(0);              // number
  const [isAdmin, setIsAdmin] = useState(false);  // boolean
  const [tags, setTags] = useState([]);            // array
  const [address, setAddress] = useState(null);    // null (will later hold an object)

  const handleNameChange = (e) => {
    // Update with a direct value
    setName(e.target.value);
  };

  const addTag = (tag) => {
    // Update based on previous state (functional update)
    setTags(prev => [...prev, tag]);
  };

  return (
    <div>
      {/* Reading state is just referencing the variable */}
      <p>Name: {name}</p>
      <p>Age: {age}</p>
      <p>Tags: {tags.join(', ')}</p>

      <input value={name} onChange={handleNameChange} />
      <button onClick={() => setAge(prev => prev + 1)}>Birthday 🎂</button>
      <button onClick={() => addTag('react')}>Add "react" tag</button>
    </div>
  );
}
```

**Important rules:**

1. **Hooks must be called at the top level** — never inside conditions, loops, or nested functions.
2. **The setter can accept a value or a function** — when the new value depends on the old one, always use the functional form `setValue(prev => newValue)`.
3. **React uses `Object.is` to bail out** — if you call `setName('Alice')` and `name` is already `'Alice'`, React skips the re-render.

---

### Q3. Why are state updates asynchronous, and what is batching in React 18?

**Answer:**

When you call a state setter like `setCount(5)`, React does **not** immediately update the variable and re-render the component. Instead, it **enqueues** the update and processes it later, batching multiple updates together for performance. This means the state variable still holds the _old_ value for the rest of the current function execution.

**Before React 18**, batching only worked inside React event handlers. Updates inside `setTimeout`, `Promise.then`, or native event listeners were _not_ batched, causing multiple unnecessary re-renders.

**React 18 introduced automatic batching everywhere** — inside promises, timeouts, native event handlers, and any other context. This is one of the biggest performance improvements in React 18.

```jsx
import { useState } from 'react';

function BatchingDemo() {
  const [count, setCount] = useState(0);
  const [flag, setFlag] = useState(false);

  console.log('Rendered!'); // How many times does this log?

  const handleClick = () => {
    // React 18: ALL of these are batched into a single re-render

    // 1. Inside an event handler (batched in all React versions)
    setCount(c => c + 1);
    setFlag(f => !f);
    // → 1 render

    // 2. Inside a setTimeout (batched only in React 18+)
    setTimeout(() => {
      setCount(c => c + 1);
      setFlag(f => !f);
      // React 17: 2 renders ❌
      // React 18: 1 render  ✅
    }, 1000);

    // 3. Inside a promise (batched only in React 18+)
    fetch('/api/data').then(() => {
      setCount(c => c + 1);
      setFlag(f => !f);
      // React 17: 2 renders ❌
      // React 18: 1 render  ✅
    });
  };

  return <button onClick={handleClick}>Count: {count}</button>;
}
```

**Key takeaway:** In React 18, you get automatic batching for free. If you ever _need_ to force a synchronous re-render (rare), you can use `flushSync` from `react-dom`:

```jsx
import { flushSync } from 'react-dom';

function handleClick() {
  flushSync(() => {
    setCount(c => c + 1);
  });
  // DOM is updated here
  flushSync(() => {
    setFlag(f => !f);
  });
  // DOM is updated here
}
```

---

### Q4. What are functional updates in `useState` and why should you use them?

**Answer:**

A **functional update** is when you pass a function (rather than a value) to the state setter. The function receives the previous state as its argument and returns the new state:

```jsx
setCount(prevCount => prevCount + 1);
```

This is critical when the new state **depends on the previous state**, because state updates are batched and the state variable you close over may be stale.

```jsx
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  const incrementThreeTimes = () => {
    // ❌ WRONG — all three read the same stale `count` (e.g., 0)
    // After this, count will be 1, not 3
    setCount(count + 1);  // 0 + 1 = 1
    setCount(count + 1);  // 0 + 1 = 1 (same stale closure)
    setCount(count + 1);  // 0 + 1 = 1 (same stale closure)
  };

  const incrementThreeTimesCorrectly = () => {
    // ✅ CORRECT — each updater receives the latest pending state
    setCount(prev => prev + 1);  // 0 → 1
    setCount(prev => prev + 1);  // 1 → 2
    setCount(prev => prev + 1);  // 2 → 3
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={incrementThreeTimes}>+3 (broken)</button>
      <button onClick={incrementThreeTimesCorrectly}>+3 (correct)</button>
    </div>
  );
}
```

**Rule of thumb:** Always use the functional form (`prev => ...`) when the new value is derived from the old value. Use direct value assignment (`setValue(newValue)`) when the new value is independent of the old one (e.g., resetting to a known value, setting from an input field).

**Production scenario — debounced search counter:**

```jsx
function SearchTracker() {
  const [searchCount, setSearchCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // If we used `searchCount + 1` here, it would always be 1
      // because the closure captures the initial searchCount (0).
      setSearchCount(prev => prev + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []); // Empty deps — functional update is essential here

  return <p>Searches performed: {searchCount}</p>;
}
```

---

### Q5. How do you use `useState` with objects and arrays while maintaining immutability?

**Answer:**

React relies on **referential equality** (`Object.is`) to detect state changes. If you mutate an object or array in place, the reference stays the same, and React will **not** re-render. You must always create a **new** object or array.

```jsx
import { useState } from 'react';

function UserForm() {
  const [user, setUser] = useState({
    name: '',
    email: '',
    preferences: { theme: 'light', notifications: true },
  });

  // ❌ WRONG — mutates existing object
  const handleNameWrong = (e) => {
    user.name = e.target.value; // Mutation!
    setUser(user);              // Same reference — React skips re-render
  };

  // ✅ CORRECT — creates a new object (shallow copy + override)
  const handleName = (e) => {
    setUser(prev => ({ ...prev, name: e.target.value }));
  };

  // ✅ Updating nested objects — spread at every level
  const toggleTheme = () => {
    setUser(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        theme: prev.preferences.theme === 'light' ? 'dark' : 'light',
      },
    }));
  };

  return (
    <div>
      <input value={user.name} onChange={handleName} />
      <button onClick={toggleTheme}>Theme: {user.preferences.theme}</button>
    </div>
  );
}
```

**Array operations cheat-sheet:**

```jsx
function TodoList() {
  const [todos, setTodos] = useState([
    { id: 1, text: 'Learn React', done: false },
    { id: 2, text: 'Build app',   done: false },
  ]);

  // Add item
  const addTodo = (text) => {
    setTodos(prev => [...prev, { id: Date.now(), text, done: false }]);
  };

  // Remove item
  const removeTodo = (id) => {
    setTodos(prev => prev.filter(todo => todo.id !== id));
  };

  // Update an item
  const toggleTodo = (id) => {
    setTodos(prev =>
      prev.map(todo =>
        todo.id === id ? { ...todo, done: !todo.done } : todo
      )
    );
  };

  // Reorder (move item to top)
  const moveToTop = (id) => {
    setTodos(prev => {
      const item = prev.find(t => t.id === id);
      return [item, ...prev.filter(t => t.id !== id)];
    });
  };

  return (
    <ul>
      {todos.map(todo => (
        <li key={todo.id}>
          <span style={{ textDecoration: todo.done ? 'line-through' : 'none' }}>
            {todo.text}
          </span>
          <button onClick={() => toggleTodo(todo.id)}>Toggle</button>
          <button onClick={() => removeTodo(todo.id)}>Delete</button>
          <button onClick={() => moveToTop(todo.id)}>Move to Top</button>
        </li>
      ))}
    </ul>
  );
}
```

**Production tip:** For deeply nested state, consider using a library like **Immer** (used internally by Redux Toolkit) that lets you write "mutative" code while producing immutable updates under the hood.

---

## Intermediate Level (Q6–Q12)

---

### Q6. What is lazy initialization of `useState` and when should you use it?

**Answer:**

The initial value passed to `useState` is used only on the **first render**, but the _expression_ is **evaluated on every render**. If computing the initial value is expensive, this wastes work on every subsequent render.

**Lazy initialization** solves this by passing a **function** to `useState` instead of a value. React calls this function only once — during the initial render.

```jsx
import { useState } from 'react';

// ❌ EXPENSIVE — parseJSON runs on EVERY render, but only the first result is used
function SettingsPanel() {
  const [settings, setSettings] = useState(
    JSON.parse(localStorage.getItem('settings') || '{}')
  );
  // ...
}

// ✅ LAZY — parseJSON runs only on the FIRST render
function SettingsPanel() {
  const [settings, setSettings] = useState(() => {
    console.log('Computing initial state...'); // Logged only once
    return JSON.parse(localStorage.getItem('settings') || '{}');
  });
  // ...
}
```

**When to use lazy initialization:**

1. **Reading from `localStorage` or `sessionStorage`** — synchronous I/O.
2. **Complex computation** — filtering a large array, transforming data.
3. **Creating expensive objects** — `new Map()`, `new Set()`, `new Date()` with parsing.

**Production example — data grid with pre-computed index:**

```jsx
function DataGrid({ rawData }) {
  // Build an index map only once, not on every render
  const [indexedData, setIndexedData] = useState(() => {
    console.log('Building index from', rawData.length, 'rows');
    const index = new Map();
    rawData.forEach(row => {
      index.set(row.id, {
        ...row,
        searchKey: `${row.name} ${row.email}`.toLowerCase(),
      });
    });
    return { rows: rawData, index };
  });

  const findById = (id) => indexedData.index.get(id);

  return (
    <table>
      <tbody>
        {indexedData.rows.map(row => (
          <tr key={row.id}>
            <td>{row.name}</td>
            <td>{row.email}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

**Gotcha:** Do not confuse lazy initialization `useState(() => value)` with passing a function _as_ the state value `useState(myFunction)`. If your state value itself is a function, you must wrap it: `useState(() => myFunction)`.

---

### Q7. What is `useReducer`, and when should you use it over `useState`?

**Answer:**

`useReducer` is an alternative to `useState` for managing state. It follows the **reducer pattern** from functional programming (and Redux): you define a pure function that takes the current state and an action, and returns the new state.

```jsx
const [state, dispatch] = useReducer(reducer, initialState);
```

- **`reducer(state, action)`** — a pure function that computes the next state.
- **`dispatch(action)`** — sends an action to the reducer. Stable across renders (no need for dependency arrays).
- **`initialState`** — the initial state value.

**When to choose `useReducer` over `useState`:**

| Criteria | `useState` | `useReducer` |
|---|---|---|
| Number of state values | 1–2 independent values | Multiple related values |
| Update logic complexity | Simple set / toggle | Complex transitions, multiple action types |
| Next state depends on | New value directly | Previous state + action type |
| Testability need | Low | High (reducer is a pure function, easy to unit test) |
| Event handler simplicity | Handlers compute new value | Handlers just dispatch an action name |

```jsx
import { useReducer } from 'react';

// Define the reducer — all logic is centralized and testable
const initialState = {
  items: [],
  isLoading: false,
  error: null,
};

function shoppingCartReducer(state, action) {
  switch (action.type) {
    case 'ADD_ITEM':
      return {
        ...state,
        items: [...state.items, action.payload],
      };
    case 'REMOVE_ITEM':
      return {
        ...state,
        items: state.items.filter(item => item.id !== action.payload),
      };
    case 'UPDATE_QUANTITY':
      return {
        ...state,
        items: state.items.map(item =>
          item.id === action.payload.id
            ? { ...item, quantity: action.payload.quantity }
            : item
        ),
      };
    case 'CLEAR_CART':
      return initialState;
    case 'FETCH_START':
      return { ...state, isLoading: true, error: null };
    case 'FETCH_SUCCESS':
      return { ...state, isLoading: false, items: action.payload };
    case 'FETCH_ERROR':
      return { ...state, isLoading: false, error: action.payload };
    default:
      throw new Error(`Unhandled action type: ${action.type}`);
  }
}

function ShoppingCart() {
  const [state, dispatch] = useReducer(shoppingCartReducer, initialState);

  const addItem = (product) => {
    dispatch({ type: 'ADD_ITEM', payload: { ...product, quantity: 1 } });
  };

  const loadCart = async () => {
    dispatch({ type: 'FETCH_START' });
    try {
      const response = await fetch('/api/cart');
      const data = await response.json();
      dispatch({ type: 'FETCH_SUCCESS', payload: data });
    } catch (error) {
      dispatch({ type: 'FETCH_ERROR', payload: error.message });
    }
  };

  if (state.isLoading) return <p>Loading cart...</p>;
  if (state.error) return <p>Error: {state.error}</p>;

  return (
    <div>
      <h2>Cart ({state.items.length} items)</h2>
      {state.items.map(item => (
        <div key={item.id}>
          {item.name} × {item.quantity}
          <button onClick={() => dispatch({ type: 'REMOVE_ITEM', payload: item.id })}>
            Remove
          </button>
        </div>
      ))}
      <button onClick={() => dispatch({ type: 'CLEAR_CART' })}>Clear Cart</button>
    </div>
  );
}
```

**The real power:** The reducer is a pure function — you can unit test it in isolation without rendering anything:

```jsx
// shoppingCartReducer.test.js
test('ADD_ITEM adds an item to an empty cart', () => {
  const state = { items: [], isLoading: false, error: null };
  const action = { type: 'ADD_ITEM', payload: { id: 1, name: 'Widget', quantity: 1 } };
  const next = shoppingCartReducer(state, action);
  expect(next.items).toHaveLength(1);
  expect(next.items[0].name).toBe('Widget');
});
```

---

### Q8. How does `useReducer` work with complex state logic — dispatch, actions, and patterns?

**Answer:**

In production applications, `useReducer` becomes powerful when combined with well-structured action types, action creators, and a disciplined reducer design. Think of the reducer as a **state machine transition table** — given a current state and an event (action), it deterministically produces the next state.

**Pattern 1: Action creators for type safety and reuse**

```jsx
// actions.js — centralize action creation
export const actions = {
  setFilter: (filter) => ({ type: 'SET_FILTER', payload: filter }),
  setPage: (page) => ({ type: 'SET_PAGE', payload: page }),
  setSortBy: (field, direction) => ({
    type: 'SET_SORT',
    payload: { field, direction },
  }),
  resetFilters: () => ({ type: 'RESET_FILTERS' }),
  fetchStart: () => ({ type: 'FETCH_START' }),
  fetchSuccess: (data, total) => ({
    type: 'FETCH_SUCCESS',
    payload: { data, total },
  }),
  fetchError: (error) => ({ type: 'FETCH_ERROR', payload: error }),
};
```

**Pattern 2: Structured reducer for a data table**

```jsx
import { useReducer, useEffect } from 'react';

const initialState = {
  data: [],
  totalCount: 0,
  page: 1,
  pageSize: 20,
  sortBy: { field: 'createdAt', direction: 'desc' },
  filter: '',
  isLoading: false,
  error: null,
};

function dataTableReducer(state, action) {
  switch (action.type) {
    case 'SET_FILTER':
      // Reset to page 1 when filter changes
      return { ...state, filter: action.payload, page: 1 };

    case 'SET_PAGE':
      return { ...state, page: action.payload };

    case 'SET_SORT':
      return {
        ...state,
        sortBy: action.payload,
        page: 1, // Reset to page 1 on sort change
      };

    case 'RESET_FILTERS':
      return {
        ...state,
        filter: '',
        sortBy: initialState.sortBy,
        page: 1,
      };

    case 'FETCH_START':
      return { ...state, isLoading: true, error: null };

    case 'FETCH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        data: action.payload.data,
        totalCount: action.payload.total,
      };

    case 'FETCH_ERROR':
      return { ...state, isLoading: false, error: action.payload };

    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

function UsersTable() {
  const [state, dispatch] = useReducer(dataTableReducer, initialState);

  // Fetch data whenever page, filter, or sort changes
  useEffect(() => {
    let cancelled = false;
    dispatch({ type: 'FETCH_START' });

    const params = new URLSearchParams({
      page: state.page,
      pageSize: state.pageSize,
      sortField: state.sortBy.field,
      sortDir: state.sortBy.direction,
      filter: state.filter,
    });

    fetch(`/api/users?${params}`)
      .then(res => res.json())
      .then(json => {
        if (!cancelled) {
          dispatch({ type: 'FETCH_SUCCESS', payload: json });
        }
      })
      .catch(err => {
        if (!cancelled) {
          dispatch({ type: 'FETCH_ERROR', payload: err.message });
        }
      });

    return () => { cancelled = true; };
  }, [state.page, state.sortBy, state.filter, state.pageSize]);

  return (
    <div>
      <input
        placeholder="Search users..."
        value={state.filter}
        onChange={(e) => dispatch({ type: 'SET_FILTER', payload: e.target.value })}
      />
      <button onClick={() => dispatch({ type: 'RESET_FILTERS' })}>Reset</button>

      {state.isLoading && <p>Loading...</p>}
      {state.error && <p className="error">{state.error}</p>}

      <table>
        <thead>
          <tr>
            {['name', 'email', 'createdAt'].map(field => (
              <th
                key={field}
                onClick={() =>
                  dispatch({
                    type: 'SET_SORT',
                    payload: {
                      field,
                      direction:
                        state.sortBy.field === field && state.sortBy.direction === 'asc'
                          ? 'desc'
                          : 'asc',
                    },
                  })
                }
                style={{ cursor: 'pointer' }}
              >
                {field}
                {state.sortBy.field === field && (state.sortBy.direction === 'asc' ? ' ▲' : ' ▼')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {state.data.map(user => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{new Date(user.createdAt).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div>
        Page {state.page} of {Math.ceil(state.totalCount / state.pageSize)}
        <button
          disabled={state.page === 1}
          onClick={() => dispatch({ type: 'SET_PAGE', payload: state.page - 1 })}
        >
          Previous
        </button>
        <button
          disabled={state.page >= Math.ceil(state.totalCount / state.pageSize)}
          onClick={() => dispatch({ type: 'SET_PAGE', payload: state.page + 1 })}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

**Why this works well in production:** Resetting the page to 1 when the filter or sort changes is a perfect example of _related state transitions_ that are easy to forget with standalone `useState` calls but trivially expressed in a reducer.

---

### Q9. What is state colocation, and why is keeping state close to where it's used important?

**Answer:**

**State colocation** means placing state as close as possible to the components that actually _use_ it. Instead of hoisting all state to a top-level provider or root component, you keep it in the lowest common ancestor that needs it.

**Why it matters:**

1. **Performance** — when state changes, only the component owning that state (and its children) re-render. If you store a form's input value at the app root, the _entire_ app re-renders on every keystroke.
2. **Readability** — developers can understand a component by looking at it in isolation, without tracing state through many layers.
3. **Maintainability** — deleting a feature means deleting its component and its state. No orphaned state in a global store.

```jsx
// ❌ BAD — searchTerm is stored way too high; the entire app re-renders on every keystroke
function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [theme, setTheme] = useState('light');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <Layout theme={theme} sidebarOpen={sidebarOpen}>
      <Header onToggleSidebar={() => setSidebarOpen(s => !s)} />
      <SearchBar value={searchTerm} onChange={setSearchTerm} />
      <UserList searchTerm={searchTerm} onSelect={setSelectedUser} />
      <UserDetail user={selectedUser} />
    </Layout>
  );
}
```

```jsx
// ✅ GOOD — each piece of state is colocated with the component that uses it
function App() {
  const [theme, setTheme] = useState('light');

  return (
    <Layout theme={theme}>
      <Header />
      <MainContent />
    </Layout>
  );
}

function MainContent() {
  const [selectedUser, setSelectedUser] = useState(null);

  return (
    <div className="main">
      <SearchableUserList onSelect={setSelectedUser} />
      <UserDetail user={selectedUser} />
    </div>
  );
}

function SearchableUserList({ onSelect }) {
  // searchTerm is colocated here — only this component re-renders on keystroke
  const [searchTerm, setSearchTerm] = useState('');

  const filteredUsers = useMemo(
    () => users.filter(u => u.name.toLowerCase().includes(searchTerm.toLowerCase())),
    [searchTerm]
  );

  return (
    <div>
      <input
        placeholder="Search users..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <ul>
        {filteredUsers.map(user => (
          <li key={user.id} onClick={() => onSelect(user)}>
            {user.name}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Rule of thumb:** Start with state colocated at the lowest possible level. Only lift it up when a sibling component genuinely needs it. If _many_ distant components need the same state, that's when Context or external state management enters the picture — not before.

---

### Q10. When should you lift state up, and what are the trade-offs of prop drilling?

**Answer:**

**Lifting state up** is React's primary pattern for sharing state between sibling components. When two or more components need to reflect the same changing data, you move the state to their closest common ancestor and pass it down via props.

**Prop drilling** is when you pass props through intermediate components that don't use them, just to get data to a deeply nested child.

```jsx
import { useState } from 'react';

// Scenario: TemperatureInput and BoilingVerdict both need the same temperature value.
// Solution: Lift `temperature` state to their parent.

function TemperatureCalculator() {
  // Lifted state — shared by both children
  const [temperature, setTemperature] = useState('');
  const [scale, setScale] = useState('celsius');

  const celsius = scale === 'fahrenheit'
    ? ((parseFloat(temperature) - 32) * 5) / 9
    : parseFloat(temperature);

  const fahrenheit = scale === 'celsius'
    ? (parseFloat(temperature) * 9) / 5 + 32
    : parseFloat(temperature);

  return (
    <div>
      <TemperatureInput
        scale="celsius"
        value={scale === 'celsius' ? temperature : String(celsius.toFixed(2))}
        onChange={(val) => { setTemperature(val); setScale('celsius'); }}
      />
      <TemperatureInput
        scale="fahrenheit"
        value={scale === 'fahrenheit' ? temperature : String(fahrenheit.toFixed(2))}
        onChange={(val) => { setTemperature(val); setScale('fahrenheit'); }}
      />
      <BoilingVerdict celsius={celsius} />
    </div>
  );
}

function TemperatureInput({ scale, value, onChange }) {
  return (
    <fieldset>
      <legend>Enter temperature in {scale}:</legend>
      <input value={value} onChange={(e) => onChange(e.target.value)} />
    </fieldset>
  );
}

function BoilingVerdict({ celsius }) {
  return <p>{celsius >= 100 ? 'The water would boil.' : 'The water would not boil.'}</p>;
}
```

**Dealing with deep prop drilling in production:**

```jsx
// ❌ Prop drilling — `currentUser` passes through 4 levels but only NavBar uses it
function App() {
  const [currentUser, setCurrentUser] = useState(null);
  return <Layout currentUser={currentUser}><Page currentUser={currentUser} /></Layout>;
}
function Layout({ currentUser, children }) {
  return <div><Header currentUser={currentUser} />{children}</div>;
}
function Header({ currentUser }) {
  return <nav><NavBar currentUser={currentUser} /></nav>;
}
function NavBar({ currentUser }) {
  return <span>Hello, {currentUser?.name}</span>;
}
```

```jsx
// ✅ Solution: Use Context to avoid drilling, or component composition
import { createContext, useContext, useState } from 'react';

const UserContext = createContext(null);

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  return (
    <UserContext.Provider value={currentUser}>
      <Layout><Page /></Layout>
    </UserContext.Provider>
  );
}

function NavBar() {
  const currentUser = useContext(UserContext);
  return <span>Hello, {currentUser?.name}</span>;
}
```

**Trade-offs:**

| Approach | Pros | Cons |
|---|---|---|
| Lift state + props | Explicit data flow, easy to trace | Verbose when deeply nested |
| Context | Avoids drilling | All consumers re-render on any context change |
| Composition (children) | Flexible, avoids drilling | Can make parent components large |

---

### Q11. What is derived state, and why should you compute values from state instead of storing them separately?

**Answer:**

**Derived state** is any value that can be computed entirely from existing state or props. The core rule is: **don't store what you can compute.** Storing derived values in state creates synchronization bugs — you have to keep two pieces of state in sync, and forgetting an update path leads to stale or inconsistent UI.

```jsx
import { useState, useMemo } from 'react';

// ❌ BAD — `filteredProducts` is derived from `products` + `searchTerm`
// Storing it separately creates a sync nightmare
function ProductList() {
  const [products, setProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredProducts, setFilteredProducts] = useState([]); // DON'T DO THIS

  // You now have to manually keep filteredProducts in sync:
  const handleSearch = (term) => {
    setSearchTerm(term);
    setFilteredProducts(products.filter(p =>
      p.name.toLowerCase().includes(term.toLowerCase())
    ));
  };

  // Bug: if `products` changes (e.g., from a fetch), `filteredProducts` is stale!
  // You'd need another effect to re-sync... and the complexity snowballs.
}
```

```jsx
// ✅ GOOD — compute filteredProducts on the fly during render
function ProductList() {
  const [products, setProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('name');

  // Derived: computed from source-of-truth state on every render
  const filteredProducts = useMemo(() => {
    const filtered = products.filter(p =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    return filtered.sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'price') return a.price - b.price;
      return 0;
    });
  }, [products, searchTerm, sortBy]);

  // More derived values
  const totalPrice = useMemo(
    () => filteredProducts.reduce((sum, p) => sum + p.price, 0),
    [filteredProducts]
  );

  const isEmpty = filteredProducts.length === 0;

  return (
    <div>
      <input
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="Filter products..."
      />
      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
        <option value="name">Sort by Name</option>
        <option value="price">Sort by Price</option>
      </select>

      {isEmpty ? (
        <p>No products match "{searchTerm}"</p>
      ) : (
        <>
          <p>Showing {filteredProducts.length} products — Total: ${totalPrice.toFixed(2)}</p>
          <ul>
            {filteredProducts.map(p => (
              <li key={p.id}>{p.name} — ${p.price}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
```

**When to use `useMemo` vs. just computing inline:**

- If the computation is cheap (e.g., `items.length`, a boolean check), compute it inline — no `useMemo` needed.
- If the computation is expensive (e.g., filtering/sorting thousands of items), wrap it in `useMemo` to avoid recalculating on every render.

**The litmus test:** If you ever find yourself writing a `useEffect` that watches one piece of state and updates another, you almost certainly have derived state that should be computed, not stored.

---

### Q12. What is the anti-pattern of initializing state from props, and what is the correct approach?

**Answer:**

The anti-pattern is using a prop to initialize state and then expecting the state to stay in sync with the prop. Since `useState`'s initial value is only used on the **first render**, if the prop changes later, the state will **not** update.

```jsx
// ❌ ANTI-PATTERN — state ignores prop changes after mount
function EditableTitle({ title }) {
  const [localTitle, setLocalTitle] = useState(title); // Only uses `title` on mount

  // If parent passes a new `title`, localTitle stays stale!
  return (
    <input value={localTitle} onChange={(e) => setLocalTitle(e.target.value)} />
  );
}

function Parent() {
  const [selectedItem, setSelectedItem] = useState(items[0]);
  // When `selectedItem` changes, EditableTitle still shows the OLD title
  return <EditableTitle title={selectedItem.title} />;
}
```

**Correct approaches:**

**Approach 1: Fully controlled component — don't use local state**

```jsx
// The parent owns the state; child is a pure display/input component
function EditableTitle({ title, onTitleChange }) {
  return (
    <input value={title} onChange={(e) => onTitleChange(e.target.value)} />
  );
}

function Parent() {
  const [selectedItem, setSelectedItem] = useState(items[0]);
  const handleTitleChange = (newTitle) => {
    setSelectedItem(prev => ({ ...prev, title: newTitle }));
  };
  return <EditableTitle title={selectedItem.title} onTitleChange={handleTitleChange} />;
}
```

**Approach 2: Uncontrolled with a `key` — reset state when identity changes**

```jsx
// Use React's `key` prop to force remounting when the item changes
function EditableTitle({ initialTitle }) {
  const [localTitle, setLocalTitle] = useState(initialTitle); // Fine here!
  return (
    <input value={localTitle} onChange={(e) => setLocalTitle(e.target.value)} />
  );
}

function Parent() {
  const [selectedItem, setSelectedItem] = useState(items[0]);
  // When `key` changes, React unmounts the old instance and mounts a new one
  // → useState re-initializes with the new `initialTitle`
  return (
    <EditableTitle
      key={selectedItem.id}
      initialTitle={selectedItem.title}
    />
  );
}
```

**Approach 3: Derived state reset with explicit sync (rare)**

```jsx
// Only when the above patterns don't fit — use with caution
function EditableTitle({ title, itemId }) {
  const [localTitle, setLocalTitle] = useState(title);
  const [prevItemId, setPrevItemId] = useState(itemId);

  // Reset local state when the item changes (during render, not in an effect)
  if (itemId !== prevItemId) {
    setPrevItemId(itemId);
    setLocalTitle(title);
  }

  return (
    <input value={localTitle} onChange={(e) => setLocalTitle(e.target.value)} />
  );
}
```

**Recommendation order:** Prefer Approach 1 (fully controlled) for most cases. Use Approach 2 (`key`) when the component has complex internal state that should reset on identity change. Use Approach 3 only as a last resort.

---

## Advanced Level (Q13–Q20)

---

### Q13. How can you implement a middleware pattern with `useReducer` (e.g., logging, analytics)?

**Answer:**

While React's `useReducer` doesn't natively support middleware like Redux, you can implement the pattern by wrapping the `dispatch` function. This is powerful for cross-cutting concerns like logging, analytics tracking, optimistic updates, and validation.

**Pattern 1: Enhanced dispatch wrapper**

```jsx
import { useReducer, useCallback, useRef } from 'react';

function useReducerWithMiddleware(reducer, initialState, middlewares = []) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const stateRef = useRef(state);
  stateRef.current = state;

  const enhancedDispatch = useCallback((action) => {
    // Run "before" middlewares
    middlewares.forEach(middleware => {
      middleware.before?.(stateRef.current, action);
    });

    // Dispatch the action
    dispatch(action);

    // Run "after" middlewares (note: state won't be updated yet due to async nature)
    // For after-effects, we use a ref that gets updated on next render
    middlewares.forEach(middleware => {
      middleware.after?.(stateRef.current, action);
    });
  }, [middlewares]);

  return [state, enhancedDispatch];
}

// --- Define middlewares ---
const loggingMiddleware = {
  before: (state, action) => {
    console.group(`Action: ${action.type}`);
    console.log('Previous state:', state);
    console.log('Payload:', action.payload);
  },
  after: (state, action) => {
    console.log('Next state:', state);
    console.groupEnd();
  },
};

const analyticsMiddleware = {
  before: (state, action) => {
    if (['ADD_TO_CART', 'REMOVE_FROM_CART', 'CHECKOUT'].includes(action.type)) {
      analytics.track(action.type, {
        payload: action.payload,
        cartSize: state.items.length,
        timestamp: Date.now(),
      });
    }
  },
};

const validationMiddleware = {
  before: (state, action) => {
    if (action.type === 'UPDATE_QUANTITY' && action.payload.quantity < 0) {
      console.warn('Attempted to set negative quantity — action will be dispatched but reducer should guard this.');
    }
  },
};
```

**Pattern 2: Full middleware chain with next() (Redux-like)**

```jsx
import { useReducer, useMemo, useRef } from 'react';

function useReducerWithMiddlewareChain(reducer, initialState, middlewares = []) {
  const [state, rawDispatch] = useReducer(reducer, initialState);
  const stateRef = useRef(state);
  stateRef.current = state;

  const dispatch = useMemo(() => {
    // Build middleware chain from right to left
    let chain = rawDispatch;

    const getState = () => stateRef.current;

    // Each middleware is: (getState) => (next) => (action) => { ... }
    for (let i = middlewares.length - 1; i >= 0; i--) {
      const next = chain;
      chain = middlewares[i](getState)(next);
    }

    return chain;
  }, [middlewares, rawDispatch]);

  return [state, dispatch];
}

// Redux-style logging middleware
const logger = (getState) => (next) => (action) => {
  console.log('[Dispatch]', action.type, action.payload);
  console.log('[State before]', getState());
  next(action);
  // State in ref will be updated after the next render
};

// Async action middleware (thunk-like)
const thunk = (getState) => (next) => (action) => {
  if (typeof action === 'function') {
    return action(next, getState);
  }
  return next(action);
};

// Usage in a component
function App() {
  const [state, dispatch] = useReducerWithMiddlewareChain(
    appReducer,
    initialState,
    [logger, thunk]
  );

  // Now you can dispatch thunks!
  const loadUser = () => {
    dispatch(async (dispatch, getState) => {
      dispatch({ type: 'FETCH_USER_START' });
      try {
        const res = await fetch(`/api/user/${getState().userId}`);
        const user = await res.json();
        dispatch({ type: 'FETCH_USER_SUCCESS', payload: user });
      } catch (err) {
        dispatch({ type: 'FETCH_USER_ERROR', payload: err.message });
      }
    });
  };

  return <button onClick={loadUser}>Load User</button>;
}
```

**Production value:** This pattern is excellent for debugging complex state flows in development, tracking user behavior in production, and keeping side-effect logic out of your components.

---

### Q14. How does automatic batching in React 18 differ from React 17, and what are the edge cases?

**Answer:**

React 18's **automatic batching** is a fundamental change in how state updates are processed. In React 17 and earlier, batching only applied inside React synthetic event handlers. React 18 extends batching to **all** contexts: promises, `setTimeout`, native event listeners, and any other asynchronous code.

**Detailed comparison:**

```jsx
import { useState } from 'react';
import { flushSync } from 'react-dom';

function BatchingDeepDive() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState('hello');
  const [flag, setFlag] = useState(false);

  let renderCount = 0;
  renderCount++;
  console.log(`Render #${renderCount}: count=${count}, text=${text}, flag=${flag}`);

  // CASE 1: Event handler — batched in BOTH React 17 and 18
  const handleClick = () => {
    setCount(c => c + 1);
    setText('world');
    setFlag(f => !f);
    // Single re-render with all three updates
  };

  // CASE 2: setTimeout — batched ONLY in React 18
  const handleTimeout = () => {
    setTimeout(() => {
      setCount(c => c + 1);
      setText('timeout');
      setFlag(f => !f);
      // React 17: 3 separate re-renders
      // React 18: 1 re-render (automatic batching)
    }, 0);
  };

  // CASE 3: Promise / async — batched ONLY in React 18
  const handleAsync = async () => {
    const data = await fetch('/api/data').then(r => r.json());
    setCount(data.count);
    setText(data.text);
    setFlag(true);
    // React 17: 3 separate re-renders
    // React 18: 1 re-render
  };

  // CASE 4: Native event listener — batched ONLY in React 18
  useEffect(() => {
    const handler = () => {
      setCount(c => c + 1);
      setFlag(f => !f);
      // React 17: 2 re-renders
      // React 18: 1 re-render
    };
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  // CASE 5: Opting OUT of batching with flushSync
  const handleFlushSync = () => {
    flushSync(() => {
      setCount(c => c + 1);
    });
    // DOM is updated, component has re-rendered

    flushSync(() => {
      setFlag(f => !f);
    });
    // DOM updated again — 2 total re-renders
  };

  return (
    <div>
      <button onClick={handleClick}>Event handler (batched)</button>
      <button onClick={handleTimeout}>setTimeout (batched in 18)</button>
      <button onClick={handleAsync}>Async (batched in 18)</button>
      <button onClick={handleFlushSync}>flushSync (NOT batched)</button>
    </div>
  );
}
```

**Edge cases and gotchas:**

```jsx
// Edge case 1: Reading DOM between state updates
// Sometimes you need the DOM to update between two state changes
function ScrollToBottom() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const listRef = useRef(null);

  const handleSend = () => {
    // We need the DOM to update with the new message BEFORE we scroll
    flushSync(() => {
      setMessages(prev => [...prev, inputValue]);
    });
    // Now the DOM has the new message
    listRef.current.scrollTop = listRef.current.scrollHeight;
    setInputValue('');
  };

  return (
    <div>
      <ul ref={listRef}>{messages.map((m, i) => <li key={i}>{m}</li>)}</ul>
      <input value={inputValue} onChange={e => setInputValue(e.target.value)} />
      <button onClick={handleSend}>Send</button>
    </div>
  );
}

// Edge case 2: Batching does NOT apply across different microtask boundaries
async function handleMultiStep() {
  setLoading(true);     // Batched with below

  const data = await fetchData(); // Async boundary — React flushes here

  setData(data);        // New batch starts
  setLoading(false);    // Batched with setData above
}
```

**Key takeaway:** React 18's automatic batching is almost always what you want. Use `flushSync` sparingly — only when you need to read the DOM between updates (e.g., scrolling, measuring elements).

---

### Q15. How can you model finite state machines with `useReducer`?

**Answer:**

A **finite state machine (FSM)** has a set of defined states and valid transitions between them. Using `useReducer` to model an FSM means invalid state transitions are physically impossible — the reducer simply doesn't handle them. This eliminates entire categories of bugs like "loading spinner stuck because `isLoading` and `isError` are both true."

```jsx
import { useReducer } from 'react';

// Define the states and valid transitions for a data fetch
// States: idle → loading → success | error
//         error → loading (retry)
//         success → loading (refresh)

const initialState = {
  status: 'idle', // 'idle' | 'loading' | 'success' | 'error'
  data: null,
  error: null,
};

function fetchReducer(state, event) {
  // Guard: only allow valid transitions from the current state
  switch (state.status) {
    case 'idle':
      switch (event.type) {
        case 'FETCH':
          return { status: 'loading', data: null, error: null };
        default:
          return state; // Invalid transition — no-op
      }

    case 'loading':
      switch (event.type) {
        case 'RESOLVE':
          return { status: 'success', data: event.payload, error: null };
        case 'REJECT':
          return { status: 'error', data: null, error: event.payload };
        default:
          return state; // Can't FETCH while already loading
      }

    case 'success':
      switch (event.type) {
        case 'FETCH':
          return { status: 'loading', data: state.data, error: null }; // Keep stale data for UX
        case 'RESET':
          return initialState;
        default:
          return state;
      }

    case 'error':
      switch (event.type) {
        case 'FETCH':
          return { status: 'loading', data: null, error: null }; // Retry
        case 'RESET':
          return initialState;
        default:
          return state;
      }

    default:
      throw new Error(`Unknown status: ${state.status}`);
  }
}

function UserProfile({ userId }) {
  const [state, send] = useReducer(fetchReducer, initialState);

  const fetchUser = async () => {
    send({ type: 'FETCH' });
    try {
      const res = await fetch(`/api/users/${userId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      send({ type: 'RESOLVE', payload: data });
    } catch (err) {
      send({ type: 'REJECT', payload: err.message });
    }
  };

  // Render based on the single `status` field — no impossible states
  return (
    <div>
      {state.status === 'idle' && (
        <button onClick={fetchUser}>Load Profile</button>
      )}

      {state.status === 'loading' && (
        <div>
          <p>Loading...</p>
          {state.data && <p>Showing stale data: {state.data.name}</p>}
        </div>
      )}

      {state.status === 'success' && (
        <div>
          <h2>{state.data.name}</h2>
          <p>{state.data.email}</p>
          <button onClick={fetchUser}>Refresh</button>
        </div>
      )}

      {state.status === 'error' && (
        <div>
          <p>Error: {state.error}</p>
          <button onClick={fetchUser}>Retry</button>
        </div>
      )}
    </div>
  );
}
```

**Production example — multi-step form wizard:**

```jsx
const formMachine = {
  personalInfo: { NEXT: 'address', CANCEL: 'cancelled' },
  address:      { NEXT: 'payment', BACK: 'personalInfo', CANCEL: 'cancelled' },
  payment:      { NEXT: 'review', BACK: 'address', CANCEL: 'cancelled' },
  review:       { SUBMIT: 'submitting', BACK: 'payment', CANCEL: 'cancelled' },
  submitting:   { RESOLVE: 'success', REJECT: 'error' },
  success:      { RESET: 'personalInfo' },
  error:        { RETRY: 'submitting', BACK: 'review' },
  cancelled:    { RESET: 'personalInfo' },
};

function wizardReducer(state, event) {
  const currentTransitions = formMachine[state.step];
  const nextStep = currentTransitions?.[event.type];

  if (!nextStep) {
    console.warn(`No transition for event "${event.type}" in step "${state.step}"`);
    return state;
  }

  return {
    ...state,
    step: nextStep,
    formData: event.payload ? { ...state.formData, ...event.payload } : state.formData,
  };
}

function CheckoutWizard() {
  const [state, send] = useReducer(wizardReducer, {
    step: 'personalInfo',
    formData: {},
  });

  return (
    <div>
      {state.step === 'personalInfo' && (
        <PersonalInfoStep
          data={state.formData}
          onNext={(data) => send({ type: 'NEXT', payload: data })}
        />
      )}
      {state.step === 'address' && (
        <AddressStep
          data={state.formData}
          onNext={(data) => send({ type: 'NEXT', payload: data })}
          onBack={() => send({ type: 'BACK' })}
        />
      )}
      {/* ... other steps ... */}
    </div>
  );
}
```

**Why FSMs matter in production:** Without FSMs, you end up with boolean soup — `isLoading && !isError && !isSuccess` — that's fragile and impossible to verify. With an FSM, **the status field is the single source of truth**, and the type system (if using TypeScript) can exhaustively check all states.

---

### Q16. What is the stale closure problem with state, and how do you solve it?

**Answer:**

The **stale closure** problem occurs when a callback or timer captures a reference to a state variable at a particular point in time, and then uses that value later — after the state has changed. Because JavaScript closures capture variables by reference (but React state values are immutable snapshots per render), the callback sees the old value forever.

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

// ❌ THE PROBLEM: stale closure in a timer
function StaleClosureDemo() {
  const [count, setCount] = useState(0);

  const handleAlertClick = () => {
    // This closure captures `count` at the time the button was clicked
    setTimeout(() => {
      // After 3 seconds, this shows the OLD count, not the current one
      alert(`Count was: ${count}`);
    }, 3000);
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
      <button onClick={handleAlertClick}>Show Alert in 3s</button>
      {/* Click "Show Alert", then rapidly click "Increment" — alert shows stale value */}
    </div>
  );
}
```

**Solution 1: Use a ref to always access the latest value**

```jsx
function FixedWithRef() {
  const [count, setCount] = useState(0);
  const countRef = useRef(count);

  // Keep the ref in sync with state
  useEffect(() => {
    countRef.current = count;
  }, [count]);

  const handleAlertClick = () => {
    setTimeout(() => {
      // Reads the latest value through the ref
      alert(`Count is: ${countRef.current}`);
    }, 3000);
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
      <button onClick={handleAlertClick}>Show Alert in 3s</button>
    </div>
  );
}
```

**Solution 2: Use functional updates to access latest state (when you need to update, not just read)**

```jsx
function IntervalCounter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // ❌ Stale: always adds 1 to the initial count (0)
      // setCount(count + 1); // count is always 0 in this closure

      // ✅ Functional update: always gets the latest `count`
      setCount(prevCount => prevCount + 1);
    }, 1000);

    return () => clearInterval(id);
  }, []); // Empty deps — closure never refreshes, but functional update saves us

  return <p>Count: {count}</p>;
}
```

**Solution 3: Custom hook for the latest value**

```jsx
function useLatest(value) {
  const ref = useRef(value);
  ref.current = value;
  return ref;
}

function WebSocketHandler() {
  const [messages, setMessages] = useState([]);
  const [filter, setFilter] = useState('all');
  const latestFilter = useLatest(filter);

  useEffect(() => {
    const ws = new WebSocket('wss://api.example.com/feed');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      // Without useLatest, `filter` would be stale (captured at mount time)
      if (latestFilter.current === 'all' || message.type === latestFilter.current) {
        setMessages(prev => [...prev, message]);
      }
    };

    return () => ws.close();
  }, []); // WebSocket setup runs once, but always reads latest filter

  return (
    <div>
      <select value={filter} onChange={e => setFilter(e.target.value)}>
        <option value="all">All</option>
        <option value="trade">Trades</option>
        <option value="alert">Alerts</option>
      </select>
      <ul>
        {messages.map((m, i) => <li key={i}>[{m.type}] {m.text}</li>)}
      </ul>
    </div>
  );
}
```

**The mental model:** Each render is a snapshot. Closures created during that render see that render's snapshot. If you need to "reach across renders" to see the latest value, use a `ref`.

---

### Q17. How do you implement undo/redo functionality with `useReducer`?

**Answer:**

Undo/redo requires maintaining a **history stack** of past states and a pointer to the current position. `useReducer` is the ideal tool for this because the reducer can manage the history alongside the application state in a single, predictable transition function.

```jsx
import { useReducer, useCallback } from 'react';

// Generic undo/redo wrapper for any reducer
function undoable(reducer, initialState) {
  const initialUndoState = {
    past: [],
    present: initialState,
    future: [],
  };

  function undoReducer(state, action) {
    const { past, present, future } = state;

    switch (action.type) {
      case 'UNDO': {
        if (past.length === 0) return state;
        const previous = past[past.length - 1];
        const newPast = past.slice(0, -1);
        return {
          past: newPast,
          present: previous,
          future: [present, ...future],
        };
      }

      case 'REDO': {
        if (future.length === 0) return state;
        const next = future[0];
        const newFuture = future.slice(1);
        return {
          past: [...past, present],
          present: next,
          future: newFuture,
        };
      }

      case 'RESET':
        return initialUndoState;

      default: {
        // Delegate to the wrapped reducer
        const newPresent = reducer(present, action);
        if (newPresent === present) return state; // No change, skip history entry

        return {
          past: [...past, present],
          present: newPresent,
          future: [], // Clear redo stack on new action
        };
      }
    }
  }

  return { undoReducer, initialUndoState };
}

// --- Application-specific reducer ---
function drawingReducer(state, action) {
  switch (action.type) {
    case 'ADD_SHAPE':
      return {
        ...state,
        shapes: [...state.shapes, action.payload],
      };
    case 'MOVE_SHAPE':
      return {
        ...state,
        shapes: state.shapes.map(s =>
          s.id === action.payload.id
            ? { ...s, x: action.payload.x, y: action.payload.y }
            : s
        ),
      };
    case 'DELETE_SHAPE':
      return {
        ...state,
        shapes: state.shapes.filter(s => s.id !== action.payload),
      };
    case 'CHANGE_COLOR':
      return {
        ...state,
        shapes: state.shapes.map(s =>
          s.id === action.payload.id
            ? { ...s, color: action.payload.color }
            : s
        ),
      };
    default:
      return state;
  }
}

const initialDrawingState = { shapes: [] };

// --- Component ---
function DrawingCanvas() {
  const { undoReducer, initialUndoState } = undoable(drawingReducer, initialDrawingState);
  const [state, dispatch] = useReducer(undoReducer, initialUndoState);

  const { past, present, future } = state;
  const canUndo = past.length > 0;
  const canRedo = future.length > 0;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          dispatch({ type: 'REDO' });
        } else {
          dispatch({ type: 'UNDO' });
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const addRect = () => {
    dispatch({
      type: 'ADD_SHAPE',
      payload: {
        id: Date.now(),
        type: 'rect',
        x: Math.random() * 400,
        y: Math.random() * 400,
        color: '#' + Math.floor(Math.random() * 16777215).toString(16),
      },
    });
  };

  return (
    <div>
      <div style={{ marginBottom: 10 }}>
        <button onClick={() => dispatch({ type: 'UNDO' })} disabled={!canUndo}>
          Undo ({past.length})
        </button>
        <button onClick={() => dispatch({ type: 'REDO' })} disabled={!canRedo}>
          Redo ({future.length})
        </button>
        <button onClick={addRect}>Add Rectangle</button>
        <button onClick={() => dispatch({ type: 'RESET' })}>Reset</button>
      </div>

      <svg width={500} height={500} style={{ border: '1px solid #ccc' }}>
        {present.shapes.map(shape => (
          <rect
            key={shape.id}
            x={shape.x}
            y={shape.y}
            width={50}
            height={50}
            fill={shape.color}
            onClick={() =>
              dispatch({ type: 'DELETE_SHAPE', payload: shape.id })
            }
            style={{ cursor: 'pointer' }}
          />
        ))}
      </svg>

      <p>{present.shapes.length} shapes on canvas</p>
    </div>
  );
}
```

**Production considerations:**

- **Memory:** For large states, store diffs (patches) instead of full snapshots. Libraries like `immer` can produce patches via `produceWithPatches`.
- **History limit:** Cap `past.length` to avoid unbounded memory growth: `past: [...past, present].slice(-MAX_HISTORY)`.
- **Batch actions:** Some user interactions (e.g., dragging) produce many intermediate states. Consider debouncing or grouping them into a single history entry.

---

### Q18. When should you use `useState` vs `useReducer` vs external state management?

**Answer:**

This is one of the most important architectural decisions in a React application. Here's a comprehensive decision framework:

**Decision matrix:**

```jsx
/*
  ┌──────────────────────────────┬────────────┬─────────────┬──────────────────┐
  │ Criteria                     │ useState   │ useReducer  │ External (Zustand│
  │                              │            │             │ Redux, Jotai...) │
  ├──────────────────────────────┼────────────┼─────────────┼──────────────────┤
  │ Simple toggle/input          │ ✅ Best    │ Overkill    │ Overkill         │
  │ Form with 2-3 fields        │ ✅ Good    │ ✅ Good     │ Overkill         │
  │ Complex form (10+ fields)   │ Messy      │ ✅ Best     │ Good             │
  │ Data fetching (one comp)    │ Workable   │ ✅ Best     │ Good             │
  │ Shared auth state           │ ❌         │ + Context   │ ✅ Best          │
  │ Global shopping cart        │ ❌         │ + Context   │ ✅ Best          │
  │ Server cache (API data)     │ ❌         │ ❌          │ React Query ✅   │
  │ Real-time collaboration     │ ❌         │ ❌          │ ✅ Specialized   │
  │ State machines              │ Limited    │ ✅ Best     │ XState ✅        │
  │ DevTools / time-travel      │ ❌         │ Partial     │ ✅ Best          │
  └──────────────────────────────┴────────────┴─────────────┴──────────────────┘
*/
```

**Concrete examples for each:**

```jsx
// 1. useState — simple, independent values
function SearchBar() {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  return (
    <input
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      className={isFocused ? 'focused' : ''}
    />
  );
}

// 2. useReducer — multiple related values, complex transitions
function useAsync(asyncFn) {
  const [state, dispatch] = useReducer(
    (state, action) => {
      switch (action.type) {
        case 'pending':  return { status: 'pending', data: null, error: null };
        case 'resolved': return { status: 'resolved', data: action.payload, error: null };
        case 'rejected': return { status: 'rejected', data: null, error: action.payload };
        default: throw new Error(`Unhandled action: ${action.type}`);
      }
    },
    { status: 'idle', data: null, error: null }
  );

  const run = useCallback(async (...args) => {
    dispatch({ type: 'pending' });
    try {
      const data = await asyncFn(...args);
      dispatch({ type: 'resolved', payload: data });
      return data;
    } catch (error) {
      dispatch({ type: 'rejected', payload: error });
      throw error;
    }
  }, [asyncFn]);

  return { ...state, run };
}

// 3. External state — global, shared across routes/components
// Using Zustand (lightweight, minimal boilerplate)
import { create } from 'zustand';

const useAuthStore = create((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: async (credentials) => {
    const res = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    const { user, token } = await res.json();
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    set({ user: null, token: null, isAuthenticated: false });
    localStorage.removeItem('token');
  },

  // Any component can access:
  // const { user, login, logout } = useAuthStore();
}));
```

**The golden rules:**

1. **Start with `useState`** — default choice, simplest API.
2. **Graduate to `useReducer`** when you have 3+ related state values or complex update logic.
3. **Add Context** when siblings or distant children need the same state, but updates are infrequent.
4. **Reach for external state management** when you need: global state across routes, middleware/devtools, persistence, or high-frequency updates shared by many consumers.
5. **Use React Query / TanStack Query** for server state (caching, background refetching, pagination). Don't put server data in Redux.

---

### Q19. How do React 18 concurrent features interact with state updates, and what is `useTransition`?

**Answer:**

React 18 introduced **concurrent rendering**, which allows React to prepare multiple versions of the UI simultaneously. The key state-related feature is `useTransition`, which lets you mark certain state updates as **non-urgent**, so they don't block the UI from responding to urgent updates (like typing in an input).

**The problem it solves:**

```jsx
import { useState, useTransition, useMemo } from 'react';

// Without useTransition — typing is laggy because filtering 10,000 items
// blocks the main thread on every keystroke
function SlowFilterList() {
  const [query, setQuery] = useState('');

  // This blocks the UI on every keystroke
  const filteredItems = useMemo(
    () => generateItems(10000).filter(item =>
      item.name.toLowerCase().includes(query.toLowerCase())
    ),
    [query]
  );

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <ul>
        {filteredItems.map(item => <li key={item.id}>{item.name}</li>)}
      </ul>
    </div>
  );
}
```

**The solution with `useTransition`:**

```jsx
function FastFilterList() {
  const [query, setQuery] = useState('');
  const [deferredQuery, setDeferredQuery] = useState('');
  const [isPending, startTransition] = useTransition();

  const handleChange = (e) => {
    const value = e.target.value;

    // URGENT: update the input immediately (user sees their typing)
    setQuery(value);

    // NON-URGENT: update the filtered list in a transition
    // React can interrupt this if a new keystroke comes in
    startTransition(() => {
      setDeferredQuery(value);
    });
  };

  const filteredItems = useMemo(
    () => generateItems(10000).filter(item =>
      item.name.toLowerCase().includes(deferredQuery.toLowerCase())
    ),
    [deferredQuery]
  );

  return (
    <div>
      <input value={query} onChange={handleChange} />
      {isPending && <p>Updating list...</p>}
      <ul style={{ opacity: isPending ? 0.7 : 1 }}>
        {filteredItems.map(item => <li key={item.id}>{item.name}</li>)}
      </ul>
    </div>
  );
}
```

**Production example — tab switching with heavy content:**

```jsx
import { useState, useTransition, Suspense, lazy } from 'react';

const DashboardTab = lazy(() => import('./DashboardTab'));
const AnalyticsTab = lazy(() => import('./AnalyticsTab'));
const SettingsTab = lazy(() => import('./SettingsTab'));

function AppWithTabs() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isPending, startTransition] = useTransition();

  const switchTab = (tab) => {
    startTransition(() => {
      setActiveTab(tab);
    });
    // The old tab content stays visible (with optional opacity dimming)
    // while the new tab loads — no blank screen or spinner flash
  };

  return (
    <div>
      <nav>
        {['dashboard', 'analytics', 'settings'].map(tab => (
          <button
            key={tab}
            onClick={() => switchTab(tab)}
            style={{
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              opacity: isPending && activeTab !== tab ? 0.5 : 1,
            }}
          >
            {tab}
          </button>
        ))}
      </nav>

      {isPending && <div className="tab-loading-bar" />}

      <Suspense fallback={<div>Loading...</div>}>
        <div style={{ opacity: isPending ? 0.8 : 1, transition: 'opacity 0.2s' }}>
          {activeTab === 'dashboard' && <DashboardTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
          {activeTab === 'settings' && <SettingsTab />}
        </div>
      </Suspense>
    </div>
  );
}
```

**How `useTransition` interacts with state:**

1. State updates inside `startTransition` are marked as **low priority**.
2. React can **interrupt** a low-priority render if a high-priority update (e.g., user typing) comes in.
3. The `isPending` flag is `true` while the transition is in progress — use it for loading indicators.
4. The old UI stays visible until the new one is ready — no jarring flash of loading state.
5. Multiple rapid transitions are automatically **debounced** — only the latest one renders.

**`useDeferredValue` — a simpler alternative:**

```jsx
import { useState, useDeferredValue, useMemo } from 'react';

function SearchResults() {
  const [query, setQuery] = useState('');
  // React defers updating `deferredQuery` until after urgent updates
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  const results = useMemo(
    () => expensiveSearch(deferredQuery),
    [deferredQuery]
  );

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <div style={{ opacity: isStale ? 0.7 : 1 }}>
        {results.map(r => <div key={r.id}>{r.title}</div>)}
      </div>
    </div>
  );
}
```

---

### Q20. What is the optimistic state update pattern, and how do you implement it in React?

**Answer:**

An **optimistic update** assumes a server request will succeed and immediately updates the UI _before_ receiving a response. If the request fails, the update is rolled back. This makes the application feel instant and responsive, which is critical for production UX in actions like liking a post, adding to favorites, or toggling settings.

**Implementation with `useReducer`:**

```jsx
import { useReducer, useRef, useCallback } from 'react';

function optimisticReducer(state, action) {
  switch (action.type) {
    case 'TOGGLE_LIKE': {
      const post = state.posts.find(p => p.id === action.payload);
      return {
        ...state,
        posts: state.posts.map(p =>
          p.id === action.payload
            ? { ...p, isLiked: !p.isLiked, likes: p.isLiked ? p.likes - 1 : p.likes + 1 }
            : p
        ),
      };
    }

    case 'ROLLBACK_LIKE': {
      // Revert to the snapshot saved before the optimistic update
      return {
        ...state,
        posts: state.posts.map(p =>
          p.id === action.payload.id ? action.payload.snapshot : p
        ),
      };
    }

    case 'CONFIRM_LIKE': {
      // Server confirmed — update with server's authoritative data
      return {
        ...state,
        posts: state.posts.map(p =>
          p.id === action.payload.id
            ? { ...p, likes: action.payload.serverLikes }
            : p
        ),
      };
    }

    case 'SET_POSTS':
      return { ...state, posts: action.payload };

    default:
      return state;
  }
}

function PostFeed() {
  const [state, dispatch] = useReducer(optimisticReducer, { posts: [] });
  const pendingRequests = useRef(new Map());

  const handleLike = useCallback(async (postId) => {
    // 1. Save a snapshot for rollback
    const snapshot = state.posts.find(p => p.id === postId);

    // 2. Optimistically update the UI immediately
    dispatch({ type: 'TOGGLE_LIKE', payload: postId });

    // 3. Track the pending request (for deduplication/cancellation)
    const controller = new AbortController();
    pendingRequests.current.set(postId, controller);

    try {
      // 4. Send the request to the server
      const response = await fetch(`/api/posts/${postId}/like`, {
        method: 'POST',
        body: JSON.stringify({ liked: !snapshot.isLiked }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error('Failed to update like');

      const serverData = await response.json();

      // 5. Confirm with server's authoritative data
      dispatch({
        type: 'CONFIRM_LIKE',
        payload: { id: postId, serverLikes: serverData.likes },
      });
    } catch (error) {
      if (error.name === 'AbortError') return; // Request was cancelled

      // 6. Rollback on failure
      console.error('Like failed, rolling back:', error);
      dispatch({
        type: 'ROLLBACK_LIKE',
        payload: { id: postId, snapshot },
      });

      // Optionally show a toast notification
      showToast('Failed to update. Please try again.');
    } finally {
      pendingRequests.current.delete(postId);
    }
  }, [state.posts]);

  return (
    <div>
      {state.posts.map(post => (
        <article key={post.id}>
          <h3>{post.title}</h3>
          <p>{post.body}</p>
          <button
            onClick={() => handleLike(post.id)}
            style={{ color: post.isLiked ? 'red' : 'gray' }}
          >
            {post.isLiked ? '♥' : '♡'} {post.likes}
          </button>
        </article>
      ))}
    </div>
  );
}
```

**A reusable `useOptimistic` hook:**

```jsx
import { useState, useCallback, useRef } from 'react';

function useOptimistic(initialValue) {
  const [value, setValue] = useState(initialValue);
  const [isPending, setIsPending] = useState(false);
  const rollbackRef = useRef(null);

  const update = useCallback(async (optimisticValue, serverAction) => {
    // Save rollback point
    rollbackRef.current = value;

    // Apply optimistic update
    setValue(optimisticValue);
    setIsPending(true);

    try {
      // Execute server action
      const serverResult = await serverAction();
      // Confirm with server data
      setValue(serverResult);
    } catch (error) {
      // Rollback on failure
      setValue(rollbackRef.current);
      throw error;
    } finally {
      setIsPending(false);
      rollbackRef.current = null;
    }
  }, [value]);

  return [value, update, isPending];
}

// Usage
function TodoItem({ todo }) {
  const [isDone, setIsDone, isSaving] = useOptimistic(todo.done);

  const handleToggle = async () => {
    try {
      await setIsDone(!isDone, async () => {
        const res = await fetch(`/api/todos/${todo.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ done: !isDone }),
        });
        const updated = await res.json();
        return updated.done;
      });
    } catch {
      showToast('Failed to update todo');
    }
  };

  return (
    <li style={{ opacity: isSaving ? 0.7 : 1 }}>
      <input
        type="checkbox"
        checked={isDone}
        onChange={handleToggle}
        disabled={isSaving}
      />
      <span style={{ textDecoration: isDone ? 'line-through' : 'none' }}>
        {todo.text}
      </span>
    </li>
  );
}
```

**Production best practices for optimistic updates:**

1. **Always save a rollback snapshot** before the optimistic mutation.
2. **Use `AbortController`** to cancel in-flight requests when the user navigates away or triggers a new action.
3. **Reconcile with server data** — even on success, prefer using the server's response to update the UI (the server might have computed additional fields, like a new `updatedAt` timestamp).
4. **Show subtle pending indicators** (reduced opacity, spinner) so users know the action is in flight.
5. **Handle rapid toggles** — if the user likes and unlikes a post quickly, make sure only the latest request wins. A simple approach is to abort the previous request before starting a new one.
6. **Consider `useOptimistic` from React 19 canary** — React is working on a first-class `useOptimistic` hook, signaling that this pattern is so common it deserves core library support.

---

## Summary

| # | Topic | Level | Key Takeaway |
|---|-------|-------|-------------|
| 1 | What is state | Beginner | State persists across renders and triggers re-renders |
| 2 | useState basics | Beginner | `[value, setter] = useState(initial)` — read, write, initialize |
| 3 | Async & batching | Beginner | React 18 batches all state updates automatically |
| 4 | Functional updates | Beginner | Use `prev =>` when new state depends on old state |
| 5 | Objects & arrays | Beginner | Always create new references — never mutate |
| 6 | Lazy init | Intermediate | Pass a function to `useState` for expensive initial values |
| 7 | useReducer basics | Intermediate | Use when state transitions are complex or involve multiple sub-values |
| 8 | Complex useReducer | Intermediate | Centralize logic with action types, action creators, and structured reducers |
| 9 | State colocation | Intermediate | Keep state as close as possible to where it's used |
| 10 | Lifting state up | Intermediate | Share state between siblings via their common ancestor |
| 11 | Derived state | Intermediate | Compute from state, don't store it — avoid sync bugs |
| 12 | State from props | Intermediate | Anti-pattern; use controlled components or `key` to reset |
| 13 | Middleware pattern | Advanced | Wrap dispatch for logging, analytics, and thunks |
| 14 | Batching deep dive | Advanced | React 18 batches everywhere; use `flushSync` to opt out |
| 15 | State machines | Advanced | Model valid transitions explicitly — eliminate impossible states |
| 16 | Stale closures | Advanced | Use refs or functional updates to access the latest state |
| 17 | Undo/redo | Advanced | Maintain past/present/future stacks in the reducer |
| 18 | useState vs useReducer vs external | Advanced | Start simple, escalate based on sharing scope and complexity |
| 19 | Concurrent features | Advanced | `useTransition` marks updates as non-urgent for responsive UIs |
| 20 | Optimistic updates | Advanced | Update UI immediately, rollback on server failure |
