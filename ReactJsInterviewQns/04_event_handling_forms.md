# Topic 4: Event Handling & Forms in React 18

## Introduction

Event handling and forms are the backbone of any interactive React application. React implements its own event system called **SyntheticEvent**, which wraps the browser's native events to provide a consistent cross-browser interface. Unlike vanilla DOM manipulation where you attach event listeners imperatively with `addEventListener`, React uses a declarative approach — you pass event handler functions as props directly in JSX. In React 18, events are attached to the root DOM container (not `document` as in earlier versions), and the legacy event pooling mechanism has been completely removed since React 17. Understanding how React's event system works under the hood is critical for building performant, bug-free UIs.

Forms in React follow two primary paradigms: **controlled components**, where React state is the single source of truth for form values, and **uncontrolled components**, where the DOM itself manages the state and React reads it via refs. Controlled components give you full programmatic control — validation on every keystroke, conditional formatting, disabling submit buttons — while uncontrolled components are useful for simple integrations or when you need to interface with non-React code. React 18 introduced concurrent features that affect how form state updates batch, and React 19 is pushing the boundaries further with built-in **form Actions**, `useActionState`, and `useFormStatus` that dramatically simplify server-mutation workflows.

Here is a quick illustration that shows the core pattern of a controlled form with event handling in React 18:

```jsx
import { useState } from 'react';

function ContactForm() {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [status, setStatus] = useState('idle');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('submitting');
    try {
      await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      setStatus('success');
      setFormData({ name: '', email: '', message: '' });
    } catch {
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" value={formData.name} onChange={handleChange} />
      <input name="email" type="email" value={formData.email} onChange={handleChange} />
      <textarea name="message" value={formData.message} onChange={handleChange} />
      <button type="submit" disabled={status === 'submitting'}>
        {status === 'submitting' ? 'Sending…' : 'Send'}
      </button>
      {status === 'error' && <p className="error">Something went wrong. Please try again.</p>}
    </form>
  );
}
```

This single snippet demonstrates controlled inputs, a generic change handler, form submission with `preventDefault`, loading/error state management, and the declarative style that React encourages. Every question below builds on these fundamentals.

---

## Beginner Level (Q1–Q5)

---

### Q1. How does React handle events differently from the native DOM, and what is `SyntheticEvent`?

**Answer:**

React wraps every native browser event in a **SyntheticEvent** object. This provides a consistent, cross-browser interface so you don't have to worry about IE quirks or browser-specific differences. Key differences from native DOM event handling:

1. **Naming convention** — React uses camelCase (`onClick`, `onChange`, `onKeyDown`) instead of lowercase (`onclick`, `onchange`).
2. **JSX handler syntax** — You pass a function reference, not a string: `onClick={handleClick}` instead of `onclick="handleClick()"`.
3. **Event delegation** — React does not attach listeners to individual DOM nodes. Instead, it attaches a single listener for each event type at the **root container** (as of React 17+). When an event fires, React's internal system figures out which component should handle it by traversing the fiber tree.
4. **SyntheticEvent interface** — The wrapper exposes the same interface as native events (`stopPropagation`, `preventDefault`, `target`, `currentTarget`, etc.) plus a `nativeEvent` property to access the underlying browser event.

```jsx
function EventDemo() {
  const handleClick = (e) => {
    // e is a SyntheticEvent
    console.log('Event type:', e.type);             // "click"
    console.log('Target element:', e.target);        // the DOM node clicked
    console.log('Native event:', e.nativeEvent);     // the real MouseEvent

    // Works exactly like native
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <button onClick={handleClick}>
      Click Me
    </button>
  );
}
```

**Why this matters in interviews:** Interviewers ask this to gauge whether you understand that React doesn't use `addEventListener` on every element. Understanding event delegation to the root is important for debugging event ordering issues and knowing why `e.stopPropagation()` in React won't stop a vanilla `document.addEventListener` handler from firing.

---

### Q2. How do you bind event handlers in functional components, and why is it different from class components?

**Answer:**

In **functional components**, there is no `this` binding problem. You simply define functions inside the component body (or use arrow functions inline) and pass them as props. In class components, you had to either bind in the constructor (`this.handleClick = this.handleClick.bind(this)`), use class fields with arrow functions, or wrap in an arrow function in JSX — all to ensure `this` pointed to the component instance.

With functional components and hooks, every render creates a new closure over the current state and props, so event handlers naturally have access to the latest values without any binding gymnastics.

```jsx
// Functional component — no binding needed
function Counter() {
  const [count, setCount] = useState(0);

  // Defined as a regular function — works fine
  function handleIncrement() {
    setCount((prev) => prev + 1);
  }

  // Or as a const arrow function — also works fine
  const handleDecrement = () => {
    setCount((prev) => prev - 1);
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={handleIncrement}>+</button>
      <button onClick={handleDecrement}>-</button>

      {/* Inline arrow function — fine for simple cases */}
      <button onClick={() => setCount(0)}>Reset</button>
    </div>
  );
}
```

**Common interview follow-up: "Does creating a new function every render cause performance issues?"**

In the vast majority of cases, no. Creating a function object is extremely cheap in JavaScript. The concern only matters when passing callbacks to heavily memoized child components (wrapped in `React.memo`), because a new function reference breaks memoization. In those cases, wrap the handler in `useCallback`. But premature optimization with `useCallback` everywhere is an anti-pattern — profile first.

---

### Q3. How do you pass arguments to event handlers in React?

**Answer:**

There are two common patterns for passing extra arguments to an event handler:

**Pattern 1: Wrap in an arrow function (most common)**

```jsx
function TaskList({ tasks, onDelete }) {
  return (
    <ul>
      {tasks.map((task) => (
        <li key={task.id}>
          {task.title}
          {/* Arrow function wraps the call with the specific task id */}
          <button onClick={() => onDelete(task.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

**Pattern 2: Use a curried function (useful for reusable handlers)**

```jsx
function TaskList({ tasks, onDelete }) {
  // Curried: returns a new handler for each id
  const handleDelete = (taskId) => (e) => {
    e.stopPropagation();
    onDelete(taskId);
  };

  return (
    <ul>
      {tasks.map((task) => (
        <li key={task.id}>
          {task.title}
          <button onClick={handleDelete(task.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

**Pattern 3: Use data attributes (avoids creating functions per item)**

```jsx
function TaskList({ tasks, onDelete }) {
  const handleDelete = (e) => {
    const taskId = e.currentTarget.dataset.taskId;
    onDelete(taskId);
  };

  return (
    <ul>
      {tasks.map((task) => (
        <li key={task.id}>
          {task.title}
          <button data-task-id={task.id} onClick={handleDelete}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

Pattern 3 creates only one function regardless of list size, but it's less type-safe and forces you to parse strings from the dataset. In practice, Pattern 1 (inline arrow) is the most readable and idiomatic in modern React. Pattern 2 is elegant for handlers that need the event object *and* custom arguments.

---

### Q4. What are controlled components in React? Show examples for input, textarea, and select.

**Answer:**

A **controlled component** is a form element whose value is driven by React state. The component's rendered value always reflects the state, and every user interaction flows through an `onChange` handler that updates state. This creates a single source of truth — the React state, not the DOM.

```jsx
import { useState } from 'react';

function ProfileForm() {
  const [profile, setProfile] = useState({
    username: '',
    bio: '',
    role: 'developer',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Submitted:', profile);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Controlled <input> */}
      <label>
        Username:
        <input
          type="text"
          name="username"
          value={profile.username}
          onChange={handleChange}
          maxLength={20}
        />
      </label>

      {/* Controlled <textarea> — uses value prop, NOT children */}
      <label>
        Bio:
        <textarea
          name="bio"
          value={profile.bio}
          onChange={handleChange}
          rows={4}
        />
      </label>

      {/* Controlled <select> — value on the <select>, not selected on <option> */}
      <label>
        Role:
        <select name="role" value={profile.role} onChange={handleChange}>
          <option value="developer">Developer</option>
          <option value="designer">Designer</option>
          <option value="manager">Manager</option>
        </select>
      </label>

      <button type="submit">Save Profile</button>
    </form>
  );
}
```

**Key points:**
- `<textarea>` in React uses a `value` prop (not inner text as in HTML).
- `<select>` in React uses a `value` prop on the `<select>` element (not a `selected` attribute on individual `<option>` elements).
- If you set `value` without an `onChange`, React will warn you about a read-only field. Use `defaultValue` instead if you want an uncontrolled element.
- Controlled components enable real-time validation, conditional disabling, formatted inputs (e.g., phone number masking), and computed values.

---

### Q5. How do you handle form submission and prevent the default browser behavior?

**Answer:**

When a `<form>` is submitted (via a submit button click or pressing Enter in an input), the browser's default behavior is to perform a full-page navigation (GET or POST to the form's `action` URL). In a React SPA, you almost always want to prevent this and handle submission in JavaScript.

You call `e.preventDefault()` in the submit handler attached via `onSubmit` on the `<form>` element — not on the button.

```jsx
import { useState } from 'react';

function LoginForm() {
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing again
    if (error) setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent full-page reload

    // Client-side validation
    if (!credentials.email || !credentials.password) {
      setError('Both fields are required.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!res.ok) throw new Error('Invalid credentials');
      const data = await res.json();
      // redirect or store token
      console.log('Logged in:', data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <input
        name="email"
        type="email"
        value={credentials.email}
        onChange={handleChange}
        placeholder="Email"
        autoComplete="email"
      />
      <input
        name="password"
        type="password"
        value={credentials.password}
        onChange={handleChange}
        placeholder="Password"
        autoComplete="current-password"
      />
      {error && <p role="alert" className="error">{error}</p>}
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Signing in…' : 'Sign In'}
      </button>
    </form>
  );
}
```

**Why `onSubmit` on `<form>` instead of `onClick` on `<button>`?**

Using `onSubmit` on the form element catches both button clicks *and* Enter key submissions. If you put the logic in `onClick` on the button, pressing Enter in an input field won't trigger your handler (unless the form wrapping it triggers a native submit). Always prefer `onSubmit` for form handling.

**Why `noValidate`?** When you're handling validation in React, you typically want to suppress the browser's built-in validation popups. `noValidate` on the form disables those, allowing your custom validation UI to take over.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you handle multiple form inputs with a single change handler?

**Answer:**

The standard pattern is to use the input's `name` attribute as the key into your state object. This lets you write one handler that works for every field, regardless of how many you have.

```jsx
import { useState } from 'react';

function RegistrationForm() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    age: '',
    newsletter: false,
    plan: 'free',
  });

  // Single handler for ALL inputs
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      // Checkbox uses `checked`, everything else uses `value`
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form data:', formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="firstName" value={formData.firstName} onChange={handleChange} placeholder="First name" />
      <input name="lastName" value={formData.lastName} onChange={handleChange} placeholder="Last name" />
      <input name="email" type="email" value={formData.email} onChange={handleChange} placeholder="Email" />
      <input name="age" type="number" value={formData.age} onChange={handleChange} placeholder="Age" />

      <label>
        <input
          name="newsletter"
          type="checkbox"
          checked={formData.newsletter}
          onChange={handleChange}
        />
        Subscribe to newsletter
      </label>

      <select name="plan" value={formData.plan} onChange={handleChange}>
        <option value="free">Free</option>
        <option value="pro">Pro</option>
        <option value="enterprise">Enterprise</option>
      </select>

      <button type="submit">Register</button>
    </form>
  );
}
```

**Production enhancement — nested objects:**

For deeply nested forms (e.g., `address.street`, `address.city`), you can extend the handler with a dot-notation path setter:

```jsx
import { useState, useCallback } from 'react';

function useFormState(initialState) {
  const [formData, setFormData] = useState(initialState);

  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    const val = type === 'checkbox' ? checked : value;

    setFormData((prev) => {
      const keys = name.split('.');
      if (keys.length === 1) return { ...prev, [name]: val };

      // Handle nested path like "address.street"
      const updated = { ...prev };
      let current = updated;
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = val;
      return updated;
    });
  }, []);

  const resetForm = useCallback(() => setFormData(initialState), [initialState]);

  return { formData, handleChange, setFormData, resetForm };
}

// Usage
function AddressForm() {
  const { formData, handleChange } = useFormState({
    name: '',
    address: { street: '', city: '', zip: '' },
  });

  return (
    <form>
      <input name="name" value={formData.name} onChange={handleChange} />
      <input name="address.street" value={formData.address.street} onChange={handleChange} />
      <input name="address.city" value={formData.address.city} onChange={handleChange} />
      <input name="address.zip" value={formData.address.zip} onChange={handleChange} />
    </form>
  );
}
```

---

### Q7. What are uncontrolled components and when should you use them? Explain with `useRef`.

**Answer:**

An **uncontrolled component** lets the DOM itself be the source of truth. Instead of tracking every keystroke in React state, you read the value imperatively (usually on submit) via a ref. React provides `defaultValue` (and `defaultChecked`) to set the initial value without taking control of future updates.

**When to use uncontrolled components:**
- Simple forms where you only need the value on submit (no real-time validation).
- Integrating with non-React libraries (e.g., a jQuery date picker).
- File inputs (`<input type="file">`) — these are *always* uncontrolled because their value is read-only for security reasons.
- Performance-critical scenarios with hundreds of fields where you want to avoid state updates on every keystroke.

```jsx
import { useRef } from 'react';

function QuickSearchForm({ onSearch }) {
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const query = inputRef.current.value.trim();
    if (query) {
      onSearch(query);
      inputRef.current.value = ''; // Direct DOM manipulation to clear
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        ref={inputRef}
        type="text"
        defaultValue=""
        placeholder="Search…"
        autoFocus
      />
      <button type="submit">Go</button>
    </form>
  );
}
```

**File input — always uncontrolled:**

```jsx
import { useRef, useState } from 'react';

function AvatarUpload() {
  const fileInputRef = useRef(null);
  const [preview, setPreview] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const file = fileInputRef.current.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('avatar', file);
    fetch('/api/upload', { method: 'POST', body: formData });
  };

  return (
    <form onSubmit={handleSubmit}>
      {preview && <img src={preview} alt="Preview" width={100} />}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
      />
      <button type="submit">Upload</button>
    </form>
  );
}
```

**Interview insight:** Know that controlled vs. uncontrolled is not a binary choice for an entire form. You can mix them — use controlled inputs for fields that need validation and uncontrolled for file inputs or fields that don't need real-time tracking.

---

### Q8. How does event delegation work in React, and how did it change in React 17+?

**Answer:**

**Event delegation** means attaching a single event listener at a parent level and using event bubbling to catch events from descendant elements. React has *always* used delegation internally — it doesn't call `addEventListener` on every individual DOM node.

**Before React 17:** All events were attached to `document`.

**React 17+ (including 18):** Events are attached to the **root DOM container** (the element you pass to `createRoot`).

This change was critical for enabling multiple React roots on the same page (micro-frontend architecture, gradual migration) and for fixing subtle bugs where `e.stopPropagation()` in React didn't stop handlers attached to `document`.

```jsx
// React 18 — events attach to this root element, not document
import { createRoot } from 'react-dom/client';

const rootElement = document.getElementById('root');
const root = createRoot(rootElement);
root.render(<App />);

// Now, React's click listener is on #root, NOT on document.
// This means two React apps on the same page don't interfere.
```

**Practical scenario — mixing React with non-React event listeners:**

```jsx
import { useEffect, useRef } from 'react';

function DropdownMenu() {
  const menuRef = useRef(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Native listener on document — for "click outside" to close
    const handleClickOutside = (nativeEvent) => {
      if (menuRef.current && !menuRef.current.contains(nativeEvent.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = (e) => {
    // This stopPropagation stops React's own delegation,
    // but the native document listener above still fires
    // because React 17+ attaches to root, not document.
    e.stopPropagation();
    setIsOpen((prev) => !prev);
  };

  return (
    <div ref={menuRef}>
      <button onClick={handleToggle}>Menu</button>
      {isOpen && (
        <ul className="dropdown">
          <li>Option A</li>
          <li>Option B</li>
        </ul>
      )}
    </div>
  );
}
```

**Key takeaway:** React's `e.stopPropagation()` stops propagation within the React tree. A native listener added directly to `document` will still fire. This distinction matters a lot in production when integrating third-party scripts or analytics libraries.

---

### Q9. What was event pooling in React, and why was it removed?

**Answer:**

**Event pooling** was a performance optimization in React versions prior to 17. When a SyntheticEvent was created, React would reuse (pool) the event object after the handler finished executing. All properties on the event were nullified after the callback returned. This meant that accessing `e.target` in an asynchronous callback (like `setTimeout` or inside a `.then()`) would return `null`.

To work around it, you had to call `e.persist()` to remove the event from the pool and keep it alive.

```jsx
// Pre-React 17 — THIS WOULD BREAK without e.persist()
function OldSearch() {
  const handleChange = (e) => {
    // e.persist(); // Required before React 17

    setTimeout(() => {
      // Without persist(), e.target would be null here
      console.log(e.target.value);
    }, 300);
  };

  return <input onChange={handleChange} />;
}

// React 17+ — event pooling REMOVED, this just works
function ModernSearch() {
  const handleChange = (e) => {
    // No persist() needed — event object is not reused
    setTimeout(() => {
      console.log(e.target.value); // Works perfectly
    }, 300);
  };

  return <input onChange={handleChange} />;
}
```

**Why was it removed?** The React team found that event pooling did not actually improve performance in modern browsers. The overhead of nullifying and reusing event objects was not measurable, but the developer confusion it caused (bugs from stale events in async code) was very real. So in React 17, they removed it entirely.

**Interview tip:** This is a popular question because it tests whether you know React's evolution. The correct answer for React 18 is: "Event pooling no longer exists. You can freely access event properties asynchronously without calling `e.persist()`." But mentioning *why* it existed and why it was removed demonstrates depth.

---

### Q10. How do you implement debounced search (search-as-you-type) in a React form?

**Answer:**

Debouncing delays the execution of a function until a specified time has passed since the last invocation. For search-as-you-type, you want to fire the API call only after the user stops typing, not on every keystroke.

**Key principle:** Keep the input state controlled (update on every keystroke for responsive UI), but debounce the *API call*, not the state update.

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

// Custom hook for debounced values
function useDebouncedValue(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // Debounce the query — only changes 300ms after user stops typing
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([]);
      return;
    }

    const controller = new AbortController();
    setIsSearching(true);

    fetch(`/api/search?q=${encodeURIComponent(debouncedQuery)}`, {
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data) => {
        setResults(data.results);
        setIsSearching(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setIsSearching(false);
        }
      });

    // Abort the previous request if a new debounced value arrives
    return () => controller.abort();
  }, [debouncedQuery]);

  return (
    <div>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search products…"
        aria-label="Search"
      />
      {isSearching && <p>Searching…</p>}
      <ul>
        {results.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

**Why this approach is production-ready:**
1. The input stays instantly responsive (state updates on every keystroke).
2. The API is only called after 300ms of silence.
3. `AbortController` cancels stale in-flight requests, preventing race conditions.
4. The debounced value hook is reusable across the entire app.

**Alternative — debouncing the callback directly with `useCallback` + a ref:**

```jsx
import { useState, useRef, useCallback } from 'react';

function useDebounceCallback(callback, delay) {
  const timerRef = useRef(null);

  return useCallback((...args) => {
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => callback(...args), delay);
  }, [callback, delay]);
}

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');
  const debouncedSearch = useDebounceCallback(onSearch, 300);

  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
  };

  return <input value={query} onChange={handleChange} placeholder="Search…" />;
}
```

---

### Q11. How do you handle file uploads in React?

**Answer:**

File inputs are inherently uncontrolled — the browser's security model prevents programmatically setting a file input's value. You handle file uploads by capturing the file from the change event or via a ref, then sending it via `FormData`.

```jsx
import { useState, useRef } from 'react';

function DocumentUploader() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState({});
  const inputRef = useRef(null);

  const handleFilesSelected = (e) => {
    const selected = Array.from(e.target.files);
    // Validate before adding
    const validated = selected.filter((file) => {
      if (file.size > 10 * 1024 * 1024) {
        alert(`${file.name} exceeds 10 MB limit.`);
        return false;
      }
      return true;
    });
    setFiles((prev) => [...prev, ...validated]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    setUploading(true);

    for (const file of files) {
      const formData = new FormData();
      formData.append('document', file);

      try {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/documents/upload');

        // Track per-file upload progress
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const pct = Math.round((event.loaded / event.total) * 100);
            setProgress((prev) => ({ ...prev, [file.name]: pct }));
          }
        };

        await new Promise((resolve, reject) => {
          xhr.onload = () => (xhr.status < 400 ? resolve() : reject(new Error(xhr.statusText)));
          xhr.onerror = () => reject(new Error('Network error'));
          xhr.send(formData);
        });
      } catch (err) {
        console.error(`Failed to upload ${file.name}:`, err);
      }
    }

    setUploading(false);
    setFiles([]);
    setProgress({});
    inputRef.current.value = ''; // Reset the file input
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.doc,.docx,.txt"
        onChange={handleFilesSelected}
      />

      {files.length > 0 && (
        <ul>
          {files.map((file, index) => (
            <li key={`${file.name}-${index}`}>
              {file.name} ({(file.size / 1024).toFixed(1)} KB)
              {progress[file.name] !== undefined && (
                <progress value={progress[file.name]} max={100} />
              )}
              <button onClick={() => removeFile(index)} disabled={uploading}>✕</button>
            </li>
          ))}
        </ul>
      )}

      <button onClick={uploadFiles} disabled={uploading || files.length === 0}>
        {uploading ? 'Uploading…' : `Upload ${files.length} file(s)`}
      </button>
    </div>
  );
}
```

**Production considerations:**
- **Drag and drop:** Use the `onDragOver`, `onDragEnter`, `onDragLeave`, and `onDrop` events on a drop zone `<div>` (remember `e.preventDefault()` in `onDragOver` to allow dropping).
- **Progress tracking:** `XMLHttpRequest` gives you `upload.onprogress`; `fetch` does not natively support upload progress (you'd need a `ReadableStream` workaround).
- **Chunked uploads:** For large files, split into chunks and upload in parallel or sequentially with retry logic.
- **Server validation:** Always validate file type and size on the server — client-side validation is bypassable.

---

### Q12. How do you implement dynamic form fields (add/remove fields) in React?

**Answer:**

Dynamic forms maintain an array in state where each element represents a field (or group of fields). You provide "Add" and "Remove" controls that modify this array.

```jsx
import { useState, useId } from 'react';

function InvoiceLineItems() {
  const baseId = useId();
  const [lineItems, setLineItems] = useState([
    { id: crypto.randomUUID(), description: '', quantity: 1, unitPrice: '' },
  ]);

  const addItem = () => {
    setLineItems((prev) => [
      ...prev,
      { id: crypto.randomUUID(), description: '', quantity: 1, unitPrice: '' },
    ]);
  };

  const removeItem = (id) => {
    setLineItems((prev) => prev.filter((item) => item.id !== id));
  };

  const updateItem = (id, field, value) => {
    setLineItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, [field]: value } : item))
    );
  };

  const total = lineItems.reduce(
    (sum, item) => sum + (Number(item.quantity) || 0) * (Number(item.unitPrice) || 0),
    0
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    // Validate: at least one line item with description
    const valid = lineItems.every((item) => item.description.trim());
    if (!valid) {
      alert('Every line item needs a description.');
      return;
    }
    console.log('Invoice submitted:', { lineItems, total });
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Invoice Line Items</h2>

      {lineItems.map((item, index) => (
        <fieldset key={item.id} className="line-item-row">
          <legend>Item {index + 1}</legend>

          <label htmlFor={`${baseId}-desc-${item.id}`}>Description</label>
          <input
            id={`${baseId}-desc-${item.id}`}
            value={item.description}
            onChange={(e) => updateItem(item.id, 'description', e.target.value)}
            placeholder="Service or product"
            required
          />

          <label htmlFor={`${baseId}-qty-${item.id}`}>Qty</label>
          <input
            id={`${baseId}-qty-${item.id}`}
            type="number"
            min="1"
            value={item.quantity}
            onChange={(e) => updateItem(item.id, 'quantity', e.target.value)}
          />

          <label htmlFor={`${baseId}-price-${item.id}`}>Unit Price</label>
          <input
            id={`${baseId}-price-${item.id}`}
            type="number"
            min="0"
            step="0.01"
            value={item.unitPrice}
            onChange={(e) => updateItem(item.id, 'unitPrice', e.target.value)}
            placeholder="0.00"
          />

          <span className="line-total">
            ${((Number(item.quantity) || 0) * (Number(item.unitPrice) || 0)).toFixed(2)}
          </span>

          {lineItems.length > 1 && (
            <button type="button" onClick={() => removeItem(item.id)} aria-label="Remove item">
              Remove
            </button>
          )}
        </fieldset>
      ))}

      <button type="button" onClick={addItem}>+ Add Line Item</button>
      <p className="invoice-total"><strong>Total: ${total.toFixed(2)}</strong></p>
      <button type="submit">Submit Invoice</button>
    </form>
  );
}
```

**Critical notes:**
- **Use stable unique IDs as `key`** — never use array index as key for dynamic lists. When items are removed, index-based keys cause React to mismatch state with elements.
- `crypto.randomUUID()` is available in all modern browsers and generates unique IDs.
- Each field's update handler takes the item's `id` and the `field` name, making the update function generic.
- Real invoices would use `useReducer` for more complex state transitions (reorder, duplicate, bulk delete).

---

## Advanced Level (Q13–Q20)

---

### Q13. What are the main form validation strategies in React, and how do you implement them with Yup or Zod?

**Answer:**

There are three major strategies:

1. **Inline/custom validation** — Write validation logic directly in the component. Fine for simple forms.
2. **Schema-based validation** — Define a validation schema (Yup, Zod, Joi) separately from the component. Schemas are reusable (share between client and server), composable, and declarative.
3. **Library-integrated validation** — Use a form library (React Hook Form, Formik) that natively integrates with schema validators via resolvers.

**Strategy 1: Custom inline validation**

```jsx
import { useState } from 'react';

function useFormValidation(initialValues, validate) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));

    // Validate single field on change (if it's been touched)
    if (touched[name]) {
      const fieldErrors = validate({ ...values, [name]: value });
      setErrors((prev) => ({ ...prev, [name]: fieldErrors[name] || null }));
    }
  };

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
    const fieldErrors = validate(values);
    setErrors((prev) => ({ ...prev, [name]: fieldErrors[name] || null }));
  };

  const handleSubmit = (onSubmit) => (e) => {
    e.preventDefault();
    const allErrors = validate(values);
    setErrors(allErrors);
    // Mark all as touched
    const allTouched = Object.keys(values).reduce((acc, key) => ({ ...acc, [key]: true }), {});
    setTouched(allTouched);

    if (Object.keys(allErrors).length === 0) {
      onSubmit(values);
    }
  };

  return { values, errors, touched, handleChange, handleBlur, handleSubmit };
}

// Validation function
const validateSignup = (values) => {
  const errors = {};
  if (!values.email) errors.email = 'Email is required';
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) errors.email = 'Invalid email';
  if (!values.password) errors.password = 'Password is required';
  else if (values.password.length < 8) errors.password = 'Must be at least 8 characters';
  if (values.password !== values.confirmPassword) errors.confirmPassword = 'Passwords must match';
  return errors;
};
```

**Strategy 2: Zod schema validation (recommended for TypeScript projects)**

```jsx
import { z } from 'zod';

// Define schema — reusable on client AND server
const signupSchema = z
  .object({
    email: z.string().email('Invalid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
      .regex(/[0-9]/, 'Must contain at least one number'),
    confirmPassword: z.string(),
    role: z.enum(['user', 'admin', 'editor']),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

// Type inference — no separate TypeScript interface needed
type SignupForm = z.infer<typeof signupSchema>;

function SignupPage() {
  const [values, setValues] = useState({ email: '', password: '', confirmPassword: '', role: 'user' });
  const [errors, setErrors] = useState({});

  const handleSubmit = (e) => {
    e.preventDefault();

    const result = signupSchema.safeParse(values);
    if (!result.success) {
      // Convert Zod errors to a flat map
      const fieldErrors = {};
      result.error.errors.forEach((err) => {
        const field = err.path.join('.');
        if (!fieldErrors[field]) fieldErrors[field] = err.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setErrors({});
    // result.data is fully typed and validated
    submitToServer(result.data);
  };

  // ... render form with errors[fieldName] displayed below each input
}
```

**Strategy 3: React Hook Form + Zod resolver (production favorite)**

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data) => {
    // data is already validated and typed
    await login(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} placeholder="Email" />
      {errors.email && <span role="alert">{errors.email.message}</span>}

      <input {...register('password')} type="password" placeholder="Password" />
      {errors.password && <span role="alert">{errors.password.message}</span>}

      <button type="submit" disabled={isSubmitting}>Log In</button>
    </form>
  );
}
```

**Senior-level insight:** Zod is preferred over Yup in modern projects because it's TypeScript-first (infers types from the schema), tree-shakeable, and has a smaller bundle size. React Hook Form with Zod is the current industry standard for production forms.

---

### Q14. How do you build a complex multi-step form wizard in React?

**Answer:**

A multi-step wizard breaks a long form into sequential steps. The key architectural decisions are: (1) where to store shared state across steps, (2) how to navigate between steps, and (3) how to handle partial validation per step.

```jsx
import { useState, createContext, useContext, useCallback } from 'react';
import { z } from 'zod';

// Step-specific schemas
const personalInfoSchema = z.object({
  firstName: z.string().min(1, 'Required'),
  lastName: z.string().min(1, 'Required'),
  email: z.string().email('Invalid email'),
});

const addressSchema = z.object({
  street: z.string().min(1, 'Required'),
  city: z.string().min(1, 'Required'),
  state: z.string().length(2, 'Use 2-letter state code'),
  zip: z.string().regex(/^\d{5}$/, 'Must be 5 digits'),
});

const paymentSchema = z.object({
  cardNumber: z.string().regex(/^\d{16}$/, 'Must be 16 digits'),
  expiry: z.string().regex(/^\d{2}\/\d{2}$/, 'Format: MM/YY'),
  cvc: z.string().regex(/^\d{3,4}$/, 'Must be 3-4 digits'),
});

// Wizard context
const WizardContext = createContext(null);

function WizardProvider({ children, steps }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({});
  const [stepErrors, setStepErrors] = useState({});

  const updateFields = useCallback((fields) => {
    setFormData((prev) => ({ ...prev, ...fields }));
  }, []);

  const goToStep = useCallback((step) => {
    setCurrentStep(step);
  }, []);

  const next = useCallback(() => {
    const { schema } = steps[currentStep];
    if (schema) {
      const result = schema.safeParse(formData);
      if (!result.success) {
        const errors = {};
        result.error.errors.forEach((err) => {
          errors[err.path[0]] = err.message;
        });
        setStepErrors(errors);
        return false;
      }
    }
    setStepErrors({});
    setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1));
    return true;
  }, [currentStep, formData, steps]);

  const back = useCallback(() => {
    setStepErrors({});
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  }, []);

  return (
    <WizardContext.Provider
      value={{
        currentStep,
        formData,
        stepErrors,
        updateFields,
        next,
        back,
        goToStep,
        isFirstStep: currentStep === 0,
        isLastStep: currentStep === steps.length - 1,
        totalSteps: steps.length,
      }}
    >
      {children}
    </WizardContext.Provider>
  );
}

const useWizard = () => useContext(WizardContext);

// Individual step components
function PersonalInfoStep() {
  const { formData, updateFields, stepErrors } = useWizard();

  return (
    <div>
      <h2>Personal Information</h2>
      <input
        value={formData.firstName || ''}
        onChange={(e) => updateFields({ firstName: e.target.value })}
        placeholder="First name"
      />
      {stepErrors.firstName && <span className="error">{stepErrors.firstName}</span>}

      <input
        value={formData.lastName || ''}
        onChange={(e) => updateFields({ lastName: e.target.value })}
        placeholder="Last name"
      />
      {stepErrors.lastName && <span className="error">{stepErrors.lastName}</span>}

      <input
        value={formData.email || ''}
        onChange={(e) => updateFields({ email: e.target.value })}
        placeholder="Email"
        type="email"
      />
      {stepErrors.email && <span className="error">{stepErrors.email}</span>}
    </div>
  );
}

// Orchestrator
function CheckoutWizard() {
  const steps = [
    { label: 'Personal Info', component: PersonalInfoStep, schema: personalInfoSchema },
    { label: 'Address', component: AddressStep, schema: addressSchema },
    { label: 'Payment', component: PaymentStep, schema: paymentSchema },
    { label: 'Review', component: ReviewStep, schema: null },
  ];

  return (
    <WizardProvider steps={steps}>
      <WizardContent steps={steps} />
    </WizardProvider>
  );
}

function WizardContent({ steps }) {
  const { currentStep, next, back, isFirstStep, isLastStep, formData, totalSteps } = useWizard();
  const StepComponent = steps[currentStep].component;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLastStep) {
      await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
    } else {
      next();
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Progress indicator */}
      <nav aria-label="Checkout progress">
        <ol className="wizard-steps">
          {steps.map((step, index) => (
            <li
              key={step.label}
              className={index === currentStep ? 'active' : index < currentStep ? 'completed' : ''}
            >
              {step.label}
            </li>
          ))}
        </ol>
        <p>Step {currentStep + 1} of {totalSteps}</p>
      </nav>

      <StepComponent />

      <div className="wizard-nav">
        {!isFirstStep && (
          <button type="button" onClick={back}>Back</button>
        )}
        <button type="submit">
          {isLastStep ? 'Place Order' : 'Continue'}
        </button>
      </div>
    </form>
  );
}
```

**Production considerations:**
- **Persist to `sessionStorage`** so users don't lose progress on accidental navigation.
- **Step-level validation** — only validate fields relevant to the current step.
- **Route-based steps** — for SEO or deep linking, map each step to a URL (`/checkout/address`).
- **Review step** — show a summary of all entered data before final submission.

---

### Q15. What are optimistic form submission patterns and how do you implement them?

**Answer:**

**Optimistic updates** assume the server will succeed and update the UI immediately, then reconcile (or roll back) when the server responds. This makes the app feel instant, even on slow connections.

```jsx
import { useState, useCallback } from 'react';

// Generic hook for optimistic updates
function useOptimisticAction(asyncAction) {
  const [state, setState] = useState({
    data: null,
    optimisticData: null,
    error: null,
    isRollingBack: false,
  });

  const execute = useCallback(
    async (optimisticValue, ...args) => {
      const previousData = state.data;

      // Immediately show optimistic result
      setState((prev) => ({
        ...prev,
        data: optimisticValue,
        optimisticData: optimisticValue,
        error: null,
      }));

      try {
        const serverResult = await asyncAction(...args);
        // Replace optimistic data with real server response
        setState({
          data: serverResult,
          optimisticData: null,
          error: null,
          isRollingBack: false,
        });
      } catch (error) {
        // Roll back to previous state
        setState({
          data: previousData,
          optimisticData: null,
          error,
          isRollingBack: true,
        });
      }
    },
    [asyncAction, state.data]
  );

  return { ...state, execute };
}

// Production example: Inline editable comment
function CommentItem({ comment, onUpdate }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.text);
  const [displayText, setDisplayText] = useState(comment.text);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSave = async () => {
    const previousText = displayText;
    const newText = editText.trim();

    if (!newText || newText === previousText) {
      setIsEditing(false);
      return;
    }

    // Optimistically update the displayed text
    setDisplayText(newText);
    setIsEditing(false);
    setIsSaving(true);
    setError(null);

    try {
      const updated = await fetch(`/api/comments/${comment.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newText }),
      });

      if (!updated.ok) throw new Error('Failed to save');
      const data = await updated.json();
      setDisplayText(data.text); // Use server-authoritative text
    } catch (err) {
      // Roll back to previous text
      setDisplayText(previousText);
      setEditText(previousText);
      setError('Failed to save. Your edit has been reverted.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className={`comment ${isSaving ? 'saving' : ''}`}>
      {isEditing ? (
        <>
          <textarea value={editText} onChange={(e) => setEditText(e.target.value)} autoFocus />
          <button onClick={handleSave}>Save</button>
          <button onClick={() => { setIsEditing(false); setEditText(displayText); }}>Cancel</button>
        </>
      ) : (
        <>
          <p>{displayText}</p>
          {isSaving && <span className="badge">Saving…</span>}
          <button onClick={() => setIsEditing(true)}>Edit</button>
        </>
      )}
      {error && <p role="alert" className="error">{error}</p>}
    </div>
  );
}
```

**Optimistic todo list with add/delete:**

```jsx
function TodoList() {
  const [todos, setTodos] = useState([]);
  const [newTodo, setNewTodo] = useState('');

  const addTodo = async (e) => {
    e.preventDefault();
    if (!newTodo.trim()) return;

    const tempId = `temp-${Date.now()}`;
    const optimisticTodo = { id: tempId, text: newTodo, isPending: true };

    // Optimistic add
    setTodos((prev) => [...prev, optimisticTodo]);
    setNewTodo('');

    try {
      const res = await fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newTodo }),
      });
      const savedTodo = await res.json();

      // Replace temp item with real server item
      setTodos((prev) =>
        prev.map((t) => (t.id === tempId ? { ...savedTodo, isPending: false } : t))
      );
    } catch {
      // Remove the optimistic item on failure
      setTodos((prev) => prev.filter((t) => t.id !== tempId));
    }
  };

  const deleteTodo = async (id) => {
    const previousTodos = todos;

    // Optimistic delete
    setTodos((prev) => prev.filter((t) => t.id !== id));

    try {
      const res = await fetch(`/api/todos/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
    } catch {
      // Restore on failure
      setTodos(previousTodos);
    }
  };

  return (
    <div>
      <form onSubmit={addTodo}>
        <input value={newTodo} onChange={(e) => setNewTodo(e.target.value)} />
        <button type="submit">Add</button>
      </form>
      <ul>
        {todos.map((todo) => (
          <li key={todo.id} style={{ opacity: todo.isPending ? 0.5 : 1 }}>
            {todo.text}
            <button onClick={() => deleteTodo(todo.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Key pattern:** Always capture the previous state before the optimistic update. If the server fails, restore to that snapshot. Use a visual indicator (`isPending`, opacity, "Saving…" badge) so users know the change hasn't been confirmed.

---

### Q16. What are React 19 form Actions and `useActionState`? How do they compare to traditional form handling?

**Answer:**

React 19 introduces a native **Actions** paradigm for forms. Instead of using `onSubmit` with `e.preventDefault()`, you can pass an async function directly to the `<form>`'s `action` prop. React manages pending state, errors, and progressive enhancement automatically.

**Key new APIs:**
- `<form action={asyncFunction}>` — the action receives `FormData` directly.
- `useActionState(action, initialState)` — manages the result state of a form action (replaces the earlier experimental `useFormState`).
- `useFormStatus()` — lets child components read whether their parent `<form>` is submitting.

```jsx
// React 19 — Form Actions with useActionState
import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';

// Server action or async function
async function createUser(previousState, formData) {
  const name = formData.get('name');
  const email = formData.get('email');

  // Validate
  if (!name || !email) {
    return { error: 'All fields are required', data: null };
  }

  try {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email }),
    });

    if (!res.ok) {
      const err = await res.json();
      return { error: err.message, data: null };
    }

    const user = await res.json();
    return { error: null, data: user };
  } catch {
    return { error: 'Network error. Please try again.', data: null };
  }
}

// Submit button that automatically knows form's pending state
function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Creating…' : 'Create User'}
    </button>
  );
}

function CreateUserForm() {
  const [state, formAction, isPending] = useActionState(createUser, {
    error: null,
    data: null,
  });

  return (
    <form action={formAction}>
      <input name="name" placeholder="Name" required />
      <input name="email" type="email" placeholder="Email" required />

      {state.error && <p role="alert" className="error">{state.error}</p>}
      {state.data && <p className="success">Created user: {state.data.name}</p>}

      <SubmitButton />
    </form>
  );
}
```

**Comparison with traditional React 18 approach:**

```jsx
// React 18 — Traditional approach (still works in 19)
function CreateUserFormTraditional() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState(null);
  const [isPending, setIsPending] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsPending(true);
    setError(null);

    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email }),
      });
      if (!res.ok) throw new Error('Failed');
      // handle success
    } catch (err) {
      setError(err.message);
    } finally {
      setIsPending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      {error && <p>{error}</p>}
      <button disabled={isPending}>{isPending ? 'Creating…' : 'Create'}</button>
    </form>
  );
}
```

**Why Actions matter:**
- **Less boilerplate:** No `e.preventDefault()`, no manual `isPending` state, no manual error state.
- **Progressive enhancement:** Forms work even before JavaScript loads (if using server actions with a framework like Next.js).
- **Composable:** `useFormStatus` lets deeply nested buttons know when a parent form is submitting — no prop drilling.
- **Server-first:** Works naturally with React Server Components and server actions.

---

### Q17. How do you implement keyboard shortcuts and accessibility in React forms?

**Answer:**

Accessible forms and keyboard shortcuts require proper HTML semantics, ARIA attributes, focus management, and keyboard event handling. This is a critical production concern — forms that aren't accessible exclude users and may violate legal requirements (ADA, WCAG 2.1).

```jsx
import { useState, useRef, useEffect, useCallback } from 'react';

// Reusable keyboard shortcut hook
function useKeyboardShortcut(keyCombo, callback, options = {}) {
  const { enabled = true, target = document } = options;

  useEffect(() => {
    if (!enabled) return;

    const handler = (e) => {
      const keys = keyCombo.toLowerCase().split('+');
      const modifiers = {
        ctrl: keys.includes('ctrl') || keys.includes('mod'),
        shift: keys.includes('shift'),
        alt: keys.includes('alt'),
        meta: keys.includes('meta') || keys.includes('mod'),
      };
      const key = keys.filter(
        (k) => !['ctrl', 'shift', 'alt', 'meta', 'mod'].includes(k)
      )[0];

      const isMac = navigator.platform.toUpperCase().includes('MAC');
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      if (
        (modifiers.ctrl || modifiers.meta ? modKey : true) &&
        (modifiers.shift ? e.shiftKey : !e.shiftKey) &&
        (modifiers.alt ? e.altKey : !e.altKey) &&
        e.key.toLowerCase() === key
      ) {
        e.preventDefault();
        callback(e);
      }
    };

    target.addEventListener('keydown', handler);
    return () => target.removeEventListener('keydown', handler);
  }, [keyCombo, callback, enabled, target]);
}

// Accessible form with keyboard shortcuts
function AccessibleTaskForm({ onSave, onCancel }) {
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState('medium');
  const [errors, setErrors] = useState({});
  const titleRef = useRef(null);
  const errorSummaryRef = useRef(null);

  // Ctrl/Cmd + Enter to submit from anywhere in the form
  useKeyboardShortcut('mod+enter', () => {
    document.getElementById('task-form').requestSubmit();
  });

  // Escape to cancel
  useKeyboardShortcut('escape', () => {
    onCancel();
  });

  // Focus the first error field when validation fails
  useEffect(() => {
    const firstErrorField = Object.keys(errors)[0];
    if (firstErrorField && errorSummaryRef.current) {
      errorSummaryRef.current.focus();
    }
  }, [errors]);

  const validate = () => {
    const newErrors = {};
    if (!title.trim()) newErrors.title = 'Task title is required';
    if (title.length > 200) newErrors.title = 'Title must be 200 characters or fewer';
    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validate();

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    onSave({ title, priority });
  };

  return (
    <form
      id="task-form"
      onSubmit={handleSubmit}
      aria-label="Create new task"
      noValidate
    >
      {/* Error summary — announced by screen readers */}
      {Object.keys(errors).length > 0 && (
        <div
          ref={errorSummaryRef}
          role="alert"
          aria-live="assertive"
          tabIndex={-1}
          className="error-summary"
        >
          <h3>Please fix the following errors:</h3>
          <ul>
            {Object.entries(errors).map(([field, message]) => (
              <li key={field}>
                <a href={`#field-${field}`}>{message}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="form-field">
        <label htmlFor="field-title">
          Task Title <span aria-hidden="true">*</span>
        </label>
        <input
          ref={titleRef}
          id="field-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          aria-required="true"
          aria-invalid={!!errors.title}
          aria-describedby={errors.title ? 'title-error' : 'title-hint'}
          autoFocus
        />
        <span id="title-hint" className="hint">
          Brief description of the task (max 200 chars)
        </span>
        {errors.title && (
          <span id="title-error" className="error" role="alert">
            {errors.title}
          </span>
        )}
      </div>

      <fieldset>
        <legend>Priority</legend>
        {['low', 'medium', 'high'].map((level) => (
          <label key={level}>
            <input
              type="radio"
              name="priority"
              value={level}
              checked={priority === level}
              onChange={(e) => setPriority(e.target.value)}
            />
            {level.charAt(0).toUpperCase() + level.slice(1)}
          </label>
        ))}
      </fieldset>

      <div className="form-actions">
        <button type="submit">
          Save Task <kbd>⌘↵</kbd>
        </button>
        <button type="button" onClick={onCancel}>
          Cancel <kbd>Esc</kbd>
        </button>
      </div>
    </form>
  );
}
```

**Accessibility checklist for forms:**
- Every `<input>` has a `<label>` with a matching `htmlFor`/`id`.
- Error messages use `role="alert"` or `aria-live="assertive"` so screen readers announce them.
- `aria-invalid` and `aria-describedby` connect inputs to their error messages.
- Error summary links to the specific fields so users can jump directly.
- `<fieldset>` and `<legend>` group related inputs (radio buttons, checkboxes).
- Focus management: move focus to the error summary on failed validation.
- Keyboard shortcuts have visual hints (`<kbd>` elements).

---

### Q18. How do you prevent double form submission in production?

**Answer:**

Double submission is a common production bug — a user clicks "Submit" twice quickly and creates duplicate records. There are multiple defense layers:

```jsx
import { useState, useRef, useCallback } from 'react';

// Layer 1: Custom hook with multiple protection mechanisms
function useSafeSubmit(submitFn) {
  const [status, setStatus] = useState('idle'); // idle | submitting | success | error
  const isSubmittingRef = useRef(false);
  const lastSubmitTimeRef = useRef(0);

  const handleSubmit = useCallback(
    async (...args) => {
      // Guard 1: Ref-based lock (survives re-renders)
      if (isSubmittingRef.current) {
        console.warn('Submission already in progress');
        return;
      }

      // Guard 2: Throttle — reject if less than 1s since last submit
      const now = Date.now();
      if (now - lastSubmitTimeRef.current < 1000) {
        console.warn('Too many submissions');
        return;
      }

      isSubmittingRef.current = true;
      lastSubmitTimeRef.current = now;
      setStatus('submitting');

      try {
        const result = await submitFn(...args);
        setStatus('success');
        return result;
      } catch (error) {
        setStatus('error');
        throw error;
      } finally {
        isSubmittingRef.current = false;
      }
    },
    [submitFn]
  );

  return {
    handleSubmit,
    status,
    isSubmitting: status === 'submitting',
    isSuccess: status === 'success',
    isError: status === 'error',
    reset: () => setStatus('idle'),
  };
}

// Layer 2: Production payment form with all guards
function PaymentForm({ orderId, amount }) {
  const [cardNumber, setCardNumber] = useState('');

  const processPayment = useCallback(
    async (formData) => {
      const res = await fetch('/api/payments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': `${orderId}-${Date.now()}`, // Server-side dedup
        },
        body: JSON.stringify({
          orderId,
          amount,
          cardNumber: formData.cardNumber,
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.message || 'Payment failed');
      }
      return res.json();
    },
    [orderId, amount]
  );

  const { handleSubmit, isSubmitting, isSuccess, isError, reset } =
    useSafeSubmit(processPayment);

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      await handleSubmit({ cardNumber });
    } catch {
      // Error handled by hook status
    }
  };

  if (isSuccess) {
    return (
      <div role="status">
        <h2>Payment Successful!</h2>
        <p>Your order #{orderId} has been processed.</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit}>
      <input
        value={cardNumber}
        onChange={(e) => setCardNumber(e.target.value)}
        placeholder="Card number"
        disabled={isSubmitting}
      />
      <p>Amount: ${amount.toFixed(2)}</p>

      {isError && (
        <div role="alert">
          <p>Payment failed. Please try again.</p>
          <button type="button" onClick={reset}>Retry</button>
        </div>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        aria-busy={isSubmitting}
      >
        {isSubmitting ? 'Processing…' : `Pay $${amount.toFixed(2)}`}
      </button>
    </form>
  );
}
```

**All layers of protection:**

| Layer | Where | How |
|-------|-------|-----|
| Disable button | Client UI | `disabled={isSubmitting}` |
| Ref-based lock | Client logic | `isSubmittingRef.current` check |
| Throttle/debounce | Client logic | Reject rapid successive calls |
| Idempotency key | Server | Same key = same result (no duplicate) |
| Database constraint | Server | Unique constraint on `(order_id, status)` |

**Why the ref and not just state?** State updates are asynchronous. Two rapid clicks might both read `isSubmitting === false` before the first `setStatus('submitting')` has taken effect. The ref updates synchronously and is checked synchronously, making it a reliable guard.

---

### Q19. How do you choose between React Hook Form, Formik, and native React for form state management at scale?

**Answer:**

This is a common senior/staff-level interview question. The answer depends on form complexity, performance requirements, bundle size tolerance, and team familiarity.

**Comparison:**

| Feature | Native React | Formik | React Hook Form |
|---------|-------------|--------|-----------------|
| Re-renders | Every keystroke (controlled) | Every keystroke | Only on submit/blur (uncontrolled by default) |
| Bundle size | 0 KB | ~13 KB | ~9 KB |
| TypeScript DX | Manual types | Good | Excellent |
| Validation | DIY | Yup built-in | Resolver pattern (Zod, Yup, etc.) |
| Complex forms | Manual wiring | Good | Excellent |
| Performance | Depends on impl | Can be slow with large forms | Best (minimal re-renders) |
| Learning curve | None (just React) | Low | Medium |

**Native React — best for:**

```jsx
// Simple forms with 1-5 fields, no complex validation
function NewsletterForm() {
  const [email, setEmail] = useState('');

  return (
    <form onSubmit={(e) => { e.preventDefault(); subscribe(email); }}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
      <button type="submit">Subscribe</button>
    </form>
  );
}
```

**React Hook Form — best for large/dynamic forms (recommended default):**

```jsx
import { useForm, useFieldArray, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  teamName: z.string().min(1, 'Required'),
  members: z
    .array(
      z.object({
        name: z.string().min(1, 'Name is required'),
        email: z.string().email('Invalid email'),
        role: z.enum(['admin', 'member', 'viewer']),
      })
    )
    .min(1, 'At least one member'),
});

function TeamForm() {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
    reset,
    watch,
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      teamName: '',
      members: [{ name: '', email: '', role: 'member' }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'members',
  });

  // Watch specific field for conditional rendering
  const watchedMembers = watch('members');

  const onSubmit = async (data) => {
    await fetch('/api/teams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    reset();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('teamName')} placeholder="Team name" />
      {errors.teamName && <span>{errors.teamName.message}</span>}

      <h3>Members</h3>
      {fields.map((field, index) => (
        <div key={field.id} className="member-row">
          <input
            {...register(`members.${index}.name`)}
            placeholder="Name"
          />
          {errors.members?.[index]?.name && (
            <span>{errors.members[index].name.message}</span>
          )}

          <input
            {...register(`members.${index}.email`)}
            placeholder="Email"
          />
          {errors.members?.[index]?.email && (
            <span>{errors.members[index].email.message}</span>
          )}

          <select {...register(`members.${index}.role`)}>
            <option value="member">Member</option>
            <option value="admin">Admin</option>
            <option value="viewer">Viewer</option>
          </select>

          {fields.length > 1 && (
            <button type="button" onClick={() => remove(index)}>Remove</button>
          )}
        </div>
      ))}

      <button type="button" onClick={() => append({ name: '', email: '', role: 'member' })}>
        + Add Member
      </button>

      <p>{watchedMembers?.length || 0} member(s) configured</p>

      <button type="submit" disabled={isSubmitting || !isDirty}>
        {isSubmitting ? 'Creating…' : 'Create Team'}
      </button>
    </form>
  );
}
```

**When to choose what:**
- **Native React:** Simple forms, minimal validation, small apps, want zero dependencies.
- **React Hook Form:** Large forms (10+ fields), dynamic fields, performance-critical (dashboard editors, admin panels), TypeScript projects.
- **Formik:** Legacy projects already using it. For new projects, React Hook Form is generally preferred due to better performance and smaller bundle.

**Senior insight:** React Hook Form's performance advantage comes from using uncontrolled components internally. It only re-renders the specific fields that change, not the entire form. For a form with 50 fields, this is a massive difference compared to Formik or native controlled components where every keystroke re-renders everything.

---

### Q20. How do you build a production-grade form system with error recovery?

**Answer:**

A production-grade form system goes beyond basic state management. It needs: draft persistence, network error recovery, field-level server errors, retry logic, and conflict resolution. Here is a comprehensive architecture:

```jsx
import { useState, useEffect, useCallback, useRef } from 'react';

// ─── Hook: Auto-save drafts to localStorage ───
function useFormDraft(key, initialValues, debounceMs = 1000) {
  const [values, setValues] = useState(() => {
    try {
      const saved = localStorage.getItem(`form-draft:${key}`);
      return saved ? JSON.parse(saved) : initialValues;
    } catch {
      return initialValues;
    }
  });

  const [hasDraft, setHasDraft] = useState(() => !!localStorage.getItem(`form-draft:${key}`));

  // Debounced save to localStorage
  useEffect(() => {
    const timer = setTimeout(() => {
      localStorage.setItem(`form-draft:${key}`, JSON.stringify(values));
      setHasDraft(true);
    }, debounceMs);
    return () => clearTimeout(timer);
  }, [key, values, debounceMs]);

  const clearDraft = useCallback(() => {
    localStorage.removeItem(`form-draft:${key}`);
    setHasDraft(false);
  }, [key]);

  const resetToInitial = useCallback(() => {
    setValues(initialValues);
    clearDraft();
  }, [initialValues, clearDraft]);

  return { values, setValues, hasDraft, clearDraft, resetToInitial };
}

// ─── Hook: Submit with retry and error recovery ───
function useResilientSubmit(submitFn, options = {}) {
  const { maxRetries = 3, retryDelay = 1000 } = options;
  const [state, setState] = useState({
    status: 'idle',
    error: null,
    fieldErrors: {},
    retryCount: 0,
  });
  const abortControllerRef = useRef(null);

  const submit = useCallback(
    async (data) => {
      // Cancel any in-flight request
      abortControllerRef.current?.abort();
      abortControllerRef.current = new AbortController();

      setState({ status: 'submitting', error: null, fieldErrors: {}, retryCount: 0 });

      let lastError = null;

      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          const result = await submitFn(data, {
            signal: abortControllerRef.current.signal,
            attempt,
          });
          setState({ status: 'success', error: null, fieldErrors: {}, retryCount: attempt });
          return result;
        } catch (error) {
          lastError = error;

          // Don't retry on abort
          if (error.name === 'AbortError') {
            setState({ status: 'idle', error: null, fieldErrors: {}, retryCount: 0 });
            return;
          }

          // Don't retry on validation errors (4xx)
          if (error.status >= 400 && error.status < 500) {
            setState({
              status: 'error',
              error: error.message,
              fieldErrors: error.fieldErrors || {},
              retryCount: attempt,
            });
            return;
          }

          // Retry on network/server errors with exponential backoff
          if (attempt < maxRetries) {
            setState((prev) => ({ ...prev, status: 'retrying', retryCount: attempt + 1 }));
            await new Promise((r) => setTimeout(r, retryDelay * Math.pow(2, attempt)));
          }
        }
      }

      // All retries exhausted
      setState({
        status: 'error',
        error: lastError?.message || 'Request failed after multiple attempts',
        fieldErrors: {},
        retryCount: maxRetries,
      });
    },
    [submitFn, maxRetries, retryDelay]
  );

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
    setState({ status: 'idle', error: null, fieldErrors: {}, retryCount: 0 });
  }, []);

  return { ...state, submit, cancel };
}

// ─── Production form with everything wired together ───
function ProductEditForm({ productId, initialProduct }) {
  const {
    values,
    setValues,
    hasDraft,
    clearDraft,
    resetToInitial,
  } = useFormDraft(`product-${productId}`, initialProduct);

  const submitProduct = useCallback(
    async (data, { signal }) => {
      const res = await fetch(`/api/products/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal,
      });

      if (!res.ok) {
        const body = await res.json();
        const error = new Error(body.message || 'Save failed');
        error.status = res.status;
        error.fieldErrors = body.errors || {};
        throw error;
      }

      return res.json();
    },
    [productId]
  );

  const {
    status,
    error,
    fieldErrors,
    retryCount,
    submit,
    cancel,
  } = useResilientSubmit(submitProduct);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await submit(values);
    if (result) {
      clearDraft(); // Only clear draft on successful save
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Edit product">
      {/* Draft recovery banner */}
      {hasDraft && status === 'idle' && (
        <div role="status" className="draft-banner">
          <p>You have unsaved changes from a previous session.</p>
          <button type="button" onClick={resetToInitial}>
            Discard Draft
          </button>
        </div>
      )}

      {/* Network error with retry info */}
      {status === 'error' && (
        <div role="alert" className="error-banner">
          <p>{error}</p>
          {retryCount > 0 && <p>Failed after {retryCount} retry attempt(s).</p>}
          <button type="button" onClick={() => submit(values)}>
            Try Again
          </button>
        </div>
      )}

      {status === 'retrying' && (
        <div role="status" className="retry-banner">
          <p>Connection issue. Retrying… (attempt {retryCount})</p>
          <button type="button" onClick={cancel}>Cancel</button>
        </div>
      )}

      {/* Form fields with server-side field errors */}
      <div className="form-field">
        <label htmlFor="product-name">Product Name</label>
        <input
          id="product-name"
          name="name"
          value={values.name}
          onChange={handleChange}
          aria-invalid={!!fieldErrors.name}
          aria-describedby={fieldErrors.name ? 'name-error' : undefined}
          disabled={status === 'submitting' || status === 'retrying'}
        />
        {fieldErrors.name && (
          <span id="name-error" className="field-error" role="alert">
            {fieldErrors.name}
          </span>
        )}
      </div>

      <div className="form-field">
        <label htmlFor="product-price">Price</label>
        <input
          id="product-price"
          name="price"
          type="number"
          step="0.01"
          value={values.price}
          onChange={handleChange}
          aria-invalid={!!fieldErrors.price}
          aria-describedby={fieldErrors.price ? 'price-error' : undefined}
          disabled={status === 'submitting' || status === 'retrying'}
        />
        {fieldErrors.price && (
          <span id="price-error" className="field-error" role="alert">
            {fieldErrors.price}
          </span>
        )}
      </div>

      <div className="form-field">
        <label htmlFor="product-description">Description</label>
        <textarea
          id="product-description"
          name="description"
          value={values.description}
          onChange={handleChange}
          rows={6}
          disabled={status === 'submitting' || status === 'retrying'}
        />
      </div>

      <div className="form-actions">
        <button
          type="submit"
          disabled={status === 'submitting' || status === 'retrying'}
          aria-busy={status === 'submitting'}
        >
          {status === 'submitting' ? 'Saving…' : 'Save Product'}
        </button>
        <button type="button" onClick={resetToInitial} disabled={status === 'submitting'}>
          Reset
        </button>
      </div>

      {status === 'success' && (
        <div role="status" className="success-banner">
          Product saved successfully.
        </div>
      )}
    </form>
  );
}
```

**Architecture summary of a production-grade form system:**

| Concern | Solution |
|---------|----------|
| Draft persistence | `localStorage` with debounced auto-save |
| Network errors | Automatic retry with exponential backoff |
| Server validation errors | Map to individual fields via `fieldErrors` |
| Double submission | Ref-based lock + disabled button |
| Request cancellation | `AbortController` on new submission |
| Stale data | Optimistic UI with rollback on failure |
| Accessibility | ARIA attributes, focus management, `role="alert"` |
| Progressive enhancement | React 19 form actions (works without JS) |
| Complex validation | Zod schemas shared between client and server |

This architecture scales from simple contact forms to complex enterprise workflows. The hooks (`useFormDraft`, `useResilientSubmit`) are composable and reusable across the entire application. In a large codebase, you would extract these into a shared form infrastructure package used by every team.

---

*End of Topic 4 — Event Handling & Forms in React 18*
