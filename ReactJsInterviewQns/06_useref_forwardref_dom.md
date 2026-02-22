# Topic 6: useRef, forwardRef & DOM Manipulation in React 18

## Introduction

Refs are React's escape hatch into the imperative world. While React's declarative model encourages you to describe *what* the UI should look like and let the framework handle the DOM, there are many legitimate scenarios where you need direct access to a DOM node or need to hold a mutable value that persists across renders without triggering re-renders. The `useRef` hook returns a plain JavaScript object with a single `.current` property that React keeps stable across the entire lifetime of a component. Unlike `useState`, mutating `.current` never causes a re-render — this makes refs ideal for storing DOM references, interval IDs, previous state values, imperative animation handles, and any value that is "outside" the React rendering cycle.

`forwardRef` complements `useRef` by solving a fundamental problem: function components don't have instances, so you can't attach a ref to them the way you can to a class component or a host DOM element. `forwardRef` lets a parent pass a ref *through* a child function component and attach it to a specific DOM node inside that child. Combined with `useImperativeHandle`, you can even expose a custom imperative API from a child component — e.g., exposing `.play()`, `.pause()`, and `.seek()` methods from a custom video player component without leaking the entire underlying `<video>` DOM node. These patterns are the backbone of accessible, composable component libraries and are used heavily in production codebases.

Here is a foundational illustration showing `useRef` for DOM access and `forwardRef` for exposing a child's input element to a parent:

```jsx
import { useRef, forwardRef, useEffect } from 'react';

// A child component that forwards its ref to the inner <input>
const FancyInput = forwardRef(function FancyInput({ label, ...props }, ref) {
  return (
    <label>
      {label}
      <input ref={ref} {...props} className="fancy-input" />
    </label>
  );
});

function LoginForm() {
  const emailRef = useRef(null);
  const renderCount = useRef(0);

  // Track renders without causing re-renders
  renderCount.current += 1;

  useEffect(() => {
    // Focus the email input on mount — imperative DOM operation
    emailRef.current?.focus();
    console.log(`Component has rendered ${renderCount.current} time(s)`);
  });

  return (
    <form>
      {/* Parent ref reaches the <input> inside FancyInput */}
      <FancyInput ref={emailRef} label="Email" type="email" />
      <button type="submit">Log In</button>
    </form>
  );
}
```

This snippet captures three core ref concepts: using `useRef` to access a DOM node, using `useRef` to store a mutable render counter, and using `forwardRef` to allow the parent to reach into a child component's DOM. Every question below explores these patterns in depth, from basic usage through production-grade architectures.

---

## Beginner Level (Q1–Q5)

---

### Q1. What is `useRef` and how does it differ from `useState`?

**Answer:**

`useRef` is a React hook that returns a mutable ref object `{ current: initialValue }`. This object persists for the full lifetime of the component — it is created once on mount and the same object reference is returned on every subsequent render. The critical distinction from `useState` is that **mutating `ref.current` does not trigger a re-render**.

| Feature | `useState` | `useRef` |
|---|---|---|
| Returns | `[value, setter]` tuple | `{ current: value }` object |
| Mutation triggers re-render? | Yes | No |
| Value available during render? | Yes (the state value) | Yes (`ref.current`), but reading it during render can cause issues if it changes over time |
| Typical use | UI-driving data (text, toggles, lists) | DOM nodes, timers, previous values, mutable flags |
| Update mechanism | `setValue(newVal)` — enqueues a re-render | Direct assignment: `ref.current = newVal` |

Use `useState` when the value should be reflected in the UI. Use `useRef` when you need a persistent container that should *not* affect rendering.

```jsx
import { useState, useRef } from 'react';

function Counter() {
  const [count, setCount] = useState(0);       // Drives the UI
  const clickTimestamp = useRef(null);          // Silent bookkeeping

  const handleClick = () => {
    clickTimestamp.current = Date.now();        // No re-render
    setCount((c) => c + 1);                    // Triggers re-render
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={handleClick}>Increment</button>
      {/* clickTimestamp.current updates but won't show here unless
          something else causes a re-render */}
    </div>
  );
}
```

**Key takeaway:** If you put a value in `useRef` and display it in JSX, the displayed value will be stale until something else causes a re-render. This is by design — refs are for values that live *outside* the render cycle.

---

### Q2. How do you access and manipulate a DOM element using `useRef`?

**Answer:**

To access a DOM element, create a ref with `useRef(null)` and attach it to a JSX element via the `ref` attribute. After React commits the element to the DOM (i.e., after mount), `ref.current` will point to the underlying DOM node, giving you full access to imperative DOM APIs like `.focus()`, `.scrollIntoView()`, `.getBoundingClientRect()`, etc.

The ref is `null` during the first render (before commit) and is set by React after the DOM has been updated. This is why you typically access `ref.current` inside `useEffect`, event handlers, or callbacks — never during the render phase itself.

```jsx
import { useRef, useEffect } from 'react';

function SearchBar() {
  const inputRef = useRef(null);

  useEffect(() => {
    // Safe to access — the DOM node exists after mount
    inputRef.current.focus();
  }, []);

  const handleClear = () => {
    inputRef.current.value = '';        // Direct DOM manipulation
    inputRef.current.focus();           // Re-focus after clearing
  };

  return (
    <div className="search-bar">
      <input
        ref={inputRef}
        type="search"
        placeholder="Search products…"
        aria-label="Search products"
      />
      <button onClick={handleClear}>Clear</button>
    </div>
  );
}
```

**Production tip:** Always use optional chaining (`inputRef.current?.focus()`) or a null guard when accessing refs, especially if the element might conditionally render. Accessing `.current` on a null ref throws a `TypeError` at runtime.

---

### Q3. What are common use cases for storing mutable values in `useRef` that don't cause re-renders?

**Answer:**

Beyond DOM access, `useRef` is the go-to hook for any mutable value that needs to survive re-renders but should *not* trigger them. Common production use cases include:

1. **Timer / interval IDs** — Store the ID returned by `setTimeout` or `setInterval` so you can clear it on cleanup.
2. **Previous state values** — Track the previous value of a prop or state variable for comparison.
3. **Flags** — Track whether a component has mounted, whether a fetch has been aborted, or whether an animation is running.
4. **Accumulated values** — Count renders, aggregate event data, or buffer WebSocket messages before a batch flush.

```jsx
import { useState, useRef, useEffect, useCallback } from 'react';

function Stopwatch() {
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);

  const start = useCallback(() => {
    if (intervalRef.current) return;            // Prevent duplicate intervals
    startTimeRef.current = Date.now() - elapsed;
    intervalRef.current = setInterval(() => {
      setElapsed(Date.now() - startTimeRef.current);
    }, 16);                                     // ~60 fps updates
    setRunning(true);
  }, [elapsed]);

  const stop = useCallback(() => {
    clearInterval(intervalRef.current);
    intervalRef.current = null;
    setRunning(false);
  }, []);

  const reset = useCallback(() => {
    stop();
    setElapsed(0);
  }, [stop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => clearInterval(intervalRef.current);
  }, []);

  const format = (ms) => {
    const secs = Math.floor(ms / 1000);
    const mins = Math.floor(secs / 60);
    const centis = Math.floor((ms % 1000) / 10);
    return `${String(mins).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}.${String(centis).padStart(2, '0')}`;
  };

  return (
    <div className="stopwatch">
      <span className="display">{format(elapsed)}</span>
      <button onClick={running ? stop : start}>{running ? 'Stop' : 'Start'}</button>
      <button onClick={reset} disabled={elapsed === 0}>Reset</button>
    </div>
  );
}
```

Here, `intervalRef` and `startTimeRef` are mutable values that must persist across renders but would be pointless (and wasteful) to store in state since changing them should not cause a UI update by themselves.

---

### Q4. How do you use `useRef` for focus management, scroll position, and measuring elements?

**Answer:**

These are three of the most common imperative DOM operations in production React apps:

**Focus management** — Essential for accessibility (WCAG 2.1). When a modal opens, focus should move to the first interactive element. When a modal closes, focus should return to the trigger element.

**Scroll position** — Chat applications need to scroll to the latest message. E-commerce sites may restore scroll position when navigating back to a product listing.

**Measuring elements** — Dynamic layouts need to know an element's width, height, or position to compute tooltip placement, truncation, or animations.

```jsx
import { useRef, useEffect, useState } from 'react';

function ChatWindow({ messages }) {
  const bottomRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Auto-scroll to the newest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Measure container dimensions after mount
  useEffect(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setDimensions({ width: rect.width, height: rect.height });
    }
  }, []);

  return (
    <div ref={containerRef} className="chat-window" style={{ overflowY: 'auto', maxHeight: 500 }}>
      <p className="meta">
        Container: {dimensions.width.toFixed(0)}px × {dimensions.height.toFixed(0)}px
      </p>

      {messages.map((msg) => (
        <div key={msg.id} className="message">
          <strong>{msg.author}:</strong> {msg.text}
        </div>
      ))}

      {/* Invisible anchor at the bottom */}
      <div ref={bottomRef} />
    </div>
  );
}

function ModalWithFocusTrap({ isOpen, onClose, triggerRef }) {
  const closeButtonRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // Move focus into the modal
      closeButtonRef.current?.focus();
    } else {
      // Restore focus to the element that opened the modal
      triggerRef.current?.focus();
    }
  }, [isOpen, triggerRef]);

  if (!isOpen) return null;

  return (
    <div role="dialog" aria-modal="true" className="modal-overlay">
      <div className="modal-content">
        <button ref={closeButtonRef} onClick={onClose} aria-label="Close modal">
          ✕
        </button>
        <p>Modal content here…</p>
      </div>
    </div>
  );
}
```

**Production tip:** For measuring, note that `getBoundingClientRect()` is synchronous and can cause layout thrashing if called repeatedly. For responsive measurement, use `ResizeObserver` (covered in Q14) instead of polling dimensions.

---

### Q5. What is `forwardRef` and why is it needed to expose a child's DOM node to a parent?

**Answer:**

In React, the `ref` attribute on a *host element* (like `<div>`, `<input>`) is handled automatically — React attaches it to the DOM node. However, the `ref` prop on a *function component* does **not** work by default because function components don't have instances. If a parent writes `<MyInput ref={myRef} />`, `myRef.current` will be `undefined` unless the child opts in via `forwardRef`.

`forwardRef` is a higher-order function that wraps your component and passes the `ref` as a **second argument** (after `props`). The child can then attach that ref to whichever internal DOM node it wants to expose.

```jsx
import { useRef, forwardRef, useEffect } from 'react';

// Without forwardRef — ref does NOT reach the <input>
function BrokenInput({ placeholder }) {
  return <input placeholder={placeholder} />;
}

// With forwardRef — ref is forwarded to the <input>
const TextInput = forwardRef(function TextInput({ placeholder, ...rest }, ref) {
  return (
    <div className="input-wrapper">
      <input ref={ref} placeholder={placeholder} {...rest} />
    </div>
  );
});

function Form() {
  const brokenRef = useRef(null);
  const workingRef = useRef(null);

  useEffect(() => {
    console.log(brokenRef.current);    // null — ref never attached
    console.log(workingRef.current);   // <input> DOM node
    workingRef.current.focus();
  }, []);

  return (
    <form>
      {/* ref is silently dropped — React logs a warning in dev */}
      <BrokenInput ref={brokenRef} placeholder="This won't work" />

      {/* ref correctly reaches the inner <input> */}
      <TextInput ref={workingRef} placeholder="This works!" />
    </form>
  );
}
```

**When to use `forwardRef`:**
- Building reusable UI component libraries (input fields, buttons, modals).
- Any component that wraps a native element and needs to let parents imperatively interact with it.
- When composing with higher-order components (HOCs) that need to pass refs through.

**Note:** React 19 introduces a simpler model where `ref` is available as a regular prop on function components, removing the need for `forwardRef`. See Q19 for details.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you use `useRef` to track previous values of props or state?

**Answer:**

A common pattern is to store the "previous" value of a state variable or prop so you can compare it with the current value — for example, to animate a price change (green if up, red if down) or to skip an effect when a specific dependency hasn't actually changed.

The technique is simple: after every render, write the current value into a ref. On the *next* render, the ref still holds the old value because refs are updated imperatively, not as part of the render cycle.

```jsx
import { useState, useRef, useEffect } from 'react';

function usePrevious(value) {
  const ref = useRef(undefined);

  useEffect(() => {
    ref.current = value;
  });  // Runs after every render — stores the "old" value

  return ref.current;
}

function StockPrice({ ticker, price }) {
  const previousPrice = usePrevious(price);

  let trend = 'neutral';
  if (previousPrice !== undefined) {
    if (price > previousPrice) trend = 'up';
    else if (price < previousPrice) trend = 'down';
  }

  const trendColors = { up: '#22c55e', down: '#ef4444', neutral: '#6b7280' };

  return (
    <div className="stock-card">
      <h3>{ticker}</h3>
      <span style={{ color: trendColors[trend], fontSize: '1.5rem', fontWeight: 700 }}>
        ${price.toFixed(2)}
      </span>
      {previousPrice !== undefined && (
        <span className="change">
          {trend === 'up' && '▲'}
          {trend === 'down' && '▼'}
          {' '}
          {Math.abs(price - previousPrice).toFixed(2)}
        </span>
      )}
    </div>
  );
}

// Usage
function Dashboard() {
  const [price, setPrice] = useState(142.50);

  useEffect(() => {
    const id = setInterval(() => {
      setPrice((p) => p + (Math.random() - 0.48) * 2);
    }, 2000);
    return () => clearInterval(id);
  }, []);

  return <StockPrice ticker="AAPL" price={price} />;
}
```

**Why not just use another `useState`?** Because storing the previous value in state would trigger an additional re-render every time the current value changes, creating an infinite loop or at minimum a wasted render cycle. `useRef` avoids this entirely.

---

### Q7. What are callback refs, how do they differ from object refs, and when should you use them?

**Answer:**

React supports two ref syntaxes:

1. **Object refs** (`useRef`) — You pass a ref object and React sets `.current` to the DOM node after mount and back to `null` on unmount.
2. **Callback refs** — You pass a *function* to the `ref` attribute. React calls this function with the DOM node when it mounts and with `null` when it unmounts.

Callback refs are more powerful because they give you a *callback* at the exact moment the node is attached or detached. This is useful when:
- The element is conditionally rendered and you need to know exactly when it appears.
- You need to run setup/teardown logic (like attaching an observer) tied to the element's lifecycle.
- You need to manage refs for a dynamic list of elements.

```jsx
import { useState, useCallback } from 'react';

function MeasuredBox() {
  const [height, setHeight] = useState(0);

  // useCallback ensures the ref callback is stable across renders.
  // Without it, React would call the old callback with null and the
  // new callback with the node on every re-render.
  const measuredRef = useCallback((node) => {
    if (node !== null) {
      setHeight(node.getBoundingClientRect().height);
    }
  }, []);

  return (
    <div>
      <div ref={measuredRef} className="content-box">
        <p>This box has dynamic content that might change height.</p>
        <p>The callback ref measures it as soon as it mounts.</p>
      </div>
      <p>Measured height: {height}px</p>
    </div>
  );
}
```

**Object ref vs. callback ref comparison:**

| Feature | Object Ref (`useRef`) | Callback Ref |
|---|---|---|
| API | `ref={myRef}` → `myRef.current` | `ref={(node) => { ... }}` |
| Notification on attach/detach | No — you must poll or use `useEffect` | Yes — called with `node` or `null` |
| Stable across renders? | Always (same object) | Only if wrapped in `useCallback` |
| Best for | Simple DOM access | Measuring, observers, dynamic lists |

**Production example — refs for a dynamic list:**

```jsx
import { useRef, useCallback } from 'react';

function DynamicList({ items, onItemVisible }) {
  const observers = useRef(new Map());

  const getCallbackRef = useCallback(
    (id) => (node) => {
      // Cleanup previous observer for this id
      if (observers.current.has(id)) {
        observers.current.get(id).disconnect();
        observers.current.delete(id);
      }

      if (node) {
        const observer = new IntersectionObserver(
          ([entry]) => {
            if (entry.isIntersecting) onItemVisible(id);
          },
          { threshold: 0.5 }
        );
        observer.observe(node);
        observers.current.set(id, observer);
      }
    },
    [onItemVisible]
  );

  return (
    <ul>
      {items.map((item) => (
        <li key={item.id} ref={getCallbackRef(item.id)}>
          {item.label}
        </li>
      ))}
    </ul>
  );
}
```

---

### Q8. What is `useImperativeHandle` and how do you expose a custom API from a child component?

**Answer:**

`useImperativeHandle` customizes the value that a parent receives when it attaches a ref to a child that uses `forwardRef`. Instead of exposing the raw DOM node (which leaks implementation details), you expose only the methods the parent actually needs. This is the principle of *least privilege* applied to component APIs.

**Signature:** `useImperativeHandle(ref, createHandle, [deps])`

- `ref` — The forwarded ref from the parent.
- `createHandle` — A function that returns the object the parent will see as `ref.current`.
- `deps` — Dependency array (like `useEffect`).

```jsx
import { useRef, useImperativeHandle, forwardRef, useState } from 'react';

const Accordion = forwardRef(function Accordion({ title, children }, ref) {
  const [isOpen, setIsOpen] = useState(false);
  const contentRef = useRef(null);

  useImperativeHandle(ref, () => ({
    open() {
      setIsOpen(true);
    },
    close() {
      setIsOpen(false);
    },
    toggle() {
      setIsOpen((prev) => !prev);
    },
    scrollIntoView() {
      contentRef.current?.scrollIntoView({ behavior: 'smooth' });
    },
    get isOpen() {
      return isOpen;
    },
  }), [isOpen]);

  return (
    <div className="accordion" ref={contentRef}>
      <button
        className="accordion-header"
        onClick={() => setIsOpen((o) => !o)}
        aria-expanded={isOpen}
      >
        {title}
        <span className={`chevron ${isOpen ? 'rotate' : ''}`}>▸</span>
      </button>
      {isOpen && <div className="accordion-body">{children}</div>}
    </div>
  );
});

function FAQPage() {
  const shippingRef = useRef(null);
  const returnsRef = useRef(null);

  const expandAll = () => {
    shippingRef.current?.open();
    returnsRef.current?.open();
  };

  const collapseAll = () => {
    shippingRef.current?.close();
    returnsRef.current?.close();
  };

  return (
    <div className="faq-page">
      <div className="controls">
        <button onClick={expandAll}>Expand All</button>
        <button onClick={collapseAll}>Collapse All</button>
      </div>

      <Accordion ref={shippingRef} title="Shipping Policy">
        <p>We ship within 3–5 business days…</p>
      </Accordion>

      <Accordion ref={returnsRef} title="Return Policy">
        <p>You may return items within 30 days…</p>
      </Accordion>
    </div>
  );
}
```

**When to use `useImperativeHandle`:**
- Component libraries where you want a stable imperative API (modals: `.open()`, `.close()`; carousels: `.next()`, `.prev()`).
- When exposing the full DOM node would let consumers do dangerous things (removing children, changing attributes that your component manages).
- Custom form components that need to expose `.focus()`, `.reset()`, or `.validate()` without revealing internals.

**Anti-pattern warning:** Don't reach for `useImperativeHandle` when declarative props would suffice. If the parent can control behavior via `isOpen` prop + `onToggle` callback, that's usually better. Reserve imperative handles for cases where declarative control is awkward — like "scroll to this section now" or "play the video."

---

### Q9. How do refs work with uncontrolled form inputs, and when should you prefer them over controlled components?

**Answer:**

In an **uncontrolled** form, the DOM itself is the source of truth for input values. React doesn't manage the value via state; instead, you read the value from the DOM node directly using a ref when you need it (typically on submit). This is the opposite of the controlled pattern where every keystroke goes through `useState`.

**When to prefer uncontrolled inputs:**
- Simple forms where you only need the value on submit (no per-keystroke validation).
- Performance-sensitive situations with many fields (each keystroke in a controlled input triggers a re-render of the entire form).
- Integrating with non-React code or third-party libraries that manage their own DOM state.
- File inputs — `<input type="file">` is *always* uncontrolled in React because its value is read-only for security reasons.

```jsx
import { useRef } from 'react';

function FileUploadForm({ onUpload }) {
  const nameRef = useRef(null);
  const emailRef = useRef(null);
  const fileRef = useRef(null);
  const formRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('name', nameRef.current.value);
    formData.append('email', emailRef.current.value);

    const files = fileRef.current.files;
    if (files.length === 0) {
      alert('Please select a file.');
      fileRef.current.focus();
      return;
    }

    for (const file of files) {
      formData.append('attachments', file);
    }

    await onUpload(formData);

    // Reset all fields — easy with uncontrolled forms
    formRef.current.reset();
  };

  return (
    <form ref={formRef} onSubmit={handleSubmit}>
      <label>
        Name
        <input ref={nameRef} type="text" defaultValue="" required />
      </label>

      <label>
        Email
        <input ref={emailRef} type="email" defaultValue="" required />
      </label>

      <label>
        Attachments
        <input ref={fileRef} type="file" multiple accept=".pdf,.jpg,.png" />
      </label>

      <button type="submit">Upload</button>
    </form>
  );
}
```

**Key details:**
- Use `defaultValue` (not `value`) for uncontrolled text inputs, and `defaultChecked` for checkboxes/radios.
- `formRef.current.reset()` is the cleanest way to clear an uncontrolled form.
- You can mix controlled and uncontrolled inputs in the same form — e.g., a controlled search input for live filtering alongside an uncontrolled file input.

---

### Q10. How do you manage animations with refs using libraries like GSAP or Framer Motion?

**Answer:**

Animation libraries need direct access to DOM nodes to read positions, apply transforms, and interpolate styles. Refs are the bridge between React's declarative tree and these imperative animation engines.

**GSAP example** — GSAP's `gsap.to()`, `gsap.from()`, and `gsap.timeline()` all accept DOM elements as targets. You pass elements via refs and run animations inside `useEffect` (for mount animations) or event handlers (for interaction-driven animations). It is critical to kill animations on cleanup to prevent memory leaks and animation glitches when the component unmounts mid-animation.

```jsx
import { useRef, useEffect } from 'react';
import gsap from 'gsap';

function AnimatedCard({ title, description, delay = 0 }) {
  const cardRef = useRef(null);
  const tlRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      tlRef.current = gsap.timeline({ defaults: { ease: 'power3.out' } });
      tlRef.current
        .from(cardRef.current, {
          y: 60,
          opacity: 0,
          duration: 0.8,
          delay,
        })
        .from(
          cardRef.current.querySelector('.card-title'),
          { x: -20, opacity: 0, duration: 0.5 },
          '-=0.3'
        )
        .from(
          cardRef.current.querySelector('.card-body'),
          { y: 20, opacity: 0, duration: 0.5 },
          '-=0.2'
        );
    }, cardRef); // Scope the context to cardRef for automatic cleanup

    return () => ctx.revert(); // Kills all animations created in this context
  }, [delay]);

  const handleHover = () => {
    gsap.to(cardRef.current, { scale: 1.03, boxShadow: '0 8px 30px rgba(0,0,0,0.12)', duration: 0.3 });
  };

  const handleLeave = () => {
    gsap.to(cardRef.current, { scale: 1, boxShadow: '0 2px 10px rgba(0,0,0,0.06)', duration: 0.3 });
  };

  return (
    <div
      ref={cardRef}
      className="animated-card"
      onMouseEnter={handleHover}
      onMouseLeave={handleLeave}
    >
      <h3 className="card-title">{title}</h3>
      <p className="card-body">{description}</p>
    </div>
  );
}

function FeatureSection({ features }) {
  return (
    <section className="feature-grid">
      {features.map((f, i) => (
        <AnimatedCard key={f.id} title={f.title} description={f.description} delay={i * 0.15} />
      ))}
    </section>
  );
}
```

**Framer Motion** handles most animation declaratively through its `motion` components and doesn't need refs as frequently. However, refs are still needed when you want imperative control via `useAnimate` or when integrating with layout measurements:

```jsx
import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';

function RevealOnScroll({ children }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}
```

**Production takeaway:** Always store timeline or animation controller references in a `useRef` so you can pause, reverse, or kill them on cleanup. Never let animations outlive the component.

---

### Q11. How do you use `IntersectionObserver` with refs for lazy loading and infinite scroll?

**Answer:**

`IntersectionObserver` is a browser API that fires a callback when a target element enters or exits the viewport (or a specified root). Combined with refs, it enables efficient lazy loading of images, infinite scroll triggers, scroll-based analytics, and "sticky" header behaviors — all without polling scroll position.

**Pattern:** Create the observer in `useEffect`, observe the ref's DOM node, and clean up on unmount. The observer callback receives `IntersectionObserverEntry` objects with `isIntersecting`, `intersectionRatio`, and bounding rect info.

```jsx
import { useRef, useEffect, useState, useCallback } from 'react';

// Reusable hook
function useIntersectionObserver(options = {}) {
  const [entry, setEntry] = useState(null);
  const [node, setNode] = useState(null);

  const ref = useCallback((el) => setNode(el), []);

  useEffect(() => {
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => setEntry(entry),
      { threshold: 0.1, rootMargin: '200px', ...options }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [node, options.threshold, options.rootMargin, options.root]);

  return { ref, entry, isIntersecting: !!entry?.isIntersecting };
}

// Lazy-loaded image component
function LazyImage({ src, alt, width, height, ...rest }) {
  const { ref, isIntersecting } = useIntersectionObserver({ rootMargin: '300px' });
  const [loaded, setLoaded] = useState(false);

  return (
    <div ref={ref} style={{ width, height, background: '#f3f4f6' }}>
      {isIntersecting && (
        <img
          src={src}
          alt={alt}
          width={width}
          height={height}
          onLoad={() => setLoaded(true)}
          style={{ opacity: loaded ? 1 : 0, transition: 'opacity 0.3s' }}
          {...rest}
        />
      )}
    </div>
  );
}

// Infinite scroll
function InfiniteProductList() {
  const [products, setProducts] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const sentinelRef = useRef(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasMore) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !loading) {
          setPage((p) => p + 1);
        }
      },
      { rootMargin: '400px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loading]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch(`/api/products?page=${page}&limit=20`)
      .then((res) => res.json())
      .then((data) => {
        if (cancelled) return;
        setProducts((prev) => [...prev, ...data.items]);
        setHasMore(data.hasNextPage);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [page]);

  return (
    <div className="product-grid">
      {products.map((p) => (
        <div key={p.id} className="product-card">
          <LazyImage src={p.imageUrl} alt={p.name} width={300} height={300} />
          <h3>{p.name}</h3>
          <p>${p.price.toFixed(2)}</p>
        </div>
      ))}

      {/* Invisible sentinel element — triggers next page load */}
      {hasMore && <div ref={sentinelRef} style={{ height: 1 }} />}
      {loading && <p className="loading-indicator">Loading more products…</p>}
    </div>
  );
}
```

**Production tips:**
- Use `rootMargin` to prefetch content before the user reaches the bottom (e.g., `'400px'`).
- Always disconnect the observer on cleanup to avoid memory leaks.
- For large lists, combine with windowing/virtualization (`react-window`) so only visible items are in the DOM.

---

### Q12. How do you use `ResizeObserver` with refs to build responsive components?

**Answer:**

`ResizeObserver` watches an element for size changes and fires a callback with the new dimensions. Unlike `window.resize`, it detects size changes from *any* cause — parent resize, content change, CSS transition, sidebar toggle — making it perfect for truly responsive components that adapt based on their own dimensions rather than the viewport.

```jsx
import { useRef, useEffect, useState, useCallback } from 'react';

// Reusable hook
function useResizeObserver() {
  const ref = useRef(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setSize({ width, height });
      }
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return { ref, ...size };
}

// Responsive chart container that switches layout based on its own width
function ResponsiveChart({ data, title }) {
  const { ref, width, height } = useResizeObserver();

  const layout = width < 400 ? 'compact' : width < 700 ? 'medium' : 'full';

  return (
    <div ref={ref} className="chart-container">
      <h3>{title}</h3>
      <p className="dimensions">{width.toFixed(0)}px × {height.toFixed(0)}px</p>

      {layout === 'compact' && (
        <div className="chart-compact">
          {data.map((d) => (
            <div key={d.label} className="bar-row">
              <span className="label">{d.label}</span>
              <div className="bar" style={{ width: `${(d.value / Math.max(...data.map(x => x.value))) * 100}%` }} />
            </div>
          ))}
        </div>
      )}

      {layout === 'medium' && (
        <div className="chart-medium">
          {data.map((d) => (
            <div key={d.label} className="column" style={{ height: `${(d.value / Math.max(...data.map(x => x.value))) * 100}%` }}>
              <span>{d.label}</span>
            </div>
          ))}
        </div>
      )}

      {layout === 'full' && (
        <svg width={width} height={300}>
          {data.map((d, i) => {
            const barWidth = (width - 40) / data.length - 4;
            const maxVal = Math.max(...data.map((x) => x.value));
            const barHeight = (d.value / maxVal) * 260;
            return (
              <g key={d.label}>
                <rect
                  x={20 + i * (barWidth + 4)}
                  y={280 - barHeight}
                  width={barWidth}
                  height={barHeight}
                  fill="#6366f1"
                  rx={4}
                />
                <text
                  x={20 + i * (barWidth + 4) + barWidth / 2}
                  y={296}
                  textAnchor="middle"
                  fontSize={12}
                >
                  {d.label}
                </text>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}
```

**Container Queries vs. ResizeObserver:** CSS Container Queries (`@container`) now handle many responsive layout cases declaratively. Use `ResizeObserver` when you need the dimensions *in JavaScript* — to compute SVG coordinates, decide how many items to render, or pass dimensions to a chart library.

**Production gotcha:** `ResizeObserver` callbacks can fire at high frequency during resize drags. Debounce the state update if the component is expensive to render:

```jsx
import { useRef, useEffect, useState } from 'react';

function useDebouncedResize(delay = 100) {
  const ref = useRef(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let timer;
    const observer = new ResizeObserver((entries) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const { width, height } = entries[0].contentRect;
        setSize({ width, height });
      }, delay);
    });

    observer.observe(el);
    return () => {
      observer.disconnect();
      clearTimeout(timer);
    };
  }, [delay]);

  return { ref, ...size };
}
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How do refs behave inside React Portals, and how do you access DOM nodes rendered in a portal?

**Answer:**

A React **Portal** renders children into a DOM node that exists *outside* the parent component's DOM hierarchy (e.g., rendering a modal into `document.body` instead of inside the component's container). Despite living elsewhere in the real DOM, portals maintain React's logical tree — events still bubble through the React tree, context is still accessible, and **refs work exactly the same way**.

This means a parent component can hold a ref to a DOM node inside a portal without any special handling. The ref is attached by React when the portal content mounts, just like a normal child.

```jsx
import { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

function Tooltip({ targetRef, content, visible }) {
  const tooltipRef = useRef(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  useEffect(() => {
    if (!visible || !targetRef.current || !tooltipRef.current) return;

    const targetRect = targetRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    setPosition({
      top: targetRect.top - tooltipRect.height - 8 + window.scrollY,
      left: targetRect.left + targetRect.width / 2 - tooltipRect.width / 2 + window.scrollX,
    });
  }, [visible, targetRef]);

  if (!visible) return null;

  // Portal renders tooltip at document.body, but ref still works
  return createPortal(
    <div
      ref={tooltipRef}
      role="tooltip"
      className="tooltip"
      style={{
        position: 'absolute',
        top: position.top,
        left: position.left,
        zIndex: 9999,
        background: '#1f2937',
        color: '#fff',
        padding: '6px 12px',
        borderRadius: 6,
        fontSize: 14,
        pointerEvents: 'none',
      }}
    >
      {content}
    </div>,
    document.body
  );
}

function ProductCard({ product }) {
  const buttonRef = useRef(null);
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="product-card">
      <h3>{product.name}</h3>
      <button
        ref={buttonRef}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
      >
        Add to Cart
      </button>

      {/* Tooltip is portalled to body, but tooltipRef works fine */}
      <Tooltip
        targetRef={buttonRef}
        content={`$${product.price.toFixed(2)} — Free shipping`}
        visible={showTooltip}
      />
    </div>
  );
}
```

**Tricky part — event delegation and outside-click detection:**

When detecting clicks outside a modal (e.g., to close it), remember the portal's DOM node is *not* a descendant of the component's container. A naive `containerRef.current.contains(event.target)` will return `false` for clicks inside the portalled content. You need to check both the container and the portal's DOM node:

```jsx
import { useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

function Modal({ isOpen, onClose, children }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e) => {
      // Check if the click is on the overlay itself (not the modal content)
      if (e.target === overlayRef.current) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div ref={overlayRef} className="modal-overlay">
      <div className="modal-content" role="dialog" aria-modal="true">
        {children}
      </div>
    </div>,
    document.body
  );
}
```

---

### Q14. How do you manage multiple refs — ref arrays and callback ref maps — for dynamic lists?

**Answer:**

When you have a dynamic list of elements that each need a ref (e.g., for scroll-to-item, measuring heights for virtualization, or individual animations), you can't call `useRef` in a loop (that violates the rules of hooks). Instead, use one of two patterns:

**Pattern 1: Ref container with a Map (via callback refs)**

This is the most robust pattern. Use a single `useRef` to hold a `Map` and use callback refs to populate it.

```jsx
import { useRef, useCallback } from 'react';

function PlaylistTracker({ tracks, currentTrackId }) {
  const itemMapRef = useRef(new Map());

  const getRef = useCallback((id) => (node) => {
    if (node) {
      itemMapRef.current.set(id, node);
    } else {
      itemMapRef.current.delete(id);
    }
  }, []);

  const scrollToTrack = (id) => {
    const node = itemMapRef.current.get(id);
    node?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  // Auto-scroll to the current track when it changes
  const prevTrackRef = useRef(currentTrackId);
  if (prevTrackRef.current !== currentTrackId) {
    prevTrackRef.current = currentTrackId;
    // Schedule scroll after React commits the update
    requestAnimationFrame(() => scrollToTrack(currentTrackId));
  }

  return (
    <div className="playlist">
      <div className="controls">
        <button onClick={() => scrollToTrack(tracks[0]?.id)}>
          Jump to First
        </button>
        <button onClick={() => scrollToTrack(tracks[tracks.length - 1]?.id)}>
          Jump to Last
        </button>
      </div>

      <ul className="track-list">
        {tracks.map((track) => (
          <li
            key={track.id}
            ref={getRef(track.id)}
            className={track.id === currentTrackId ? 'active' : ''}
          >
            <span className="title">{track.title}</span>
            <span className="artist">{track.artist}</span>
            <span className="duration">{track.duration}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Pattern 2: Ref array (when indices are stable)**

Simpler but fragile — only suitable when the list order doesn't change or you don't need to look up by ID.

```jsx
import { useRef } from 'react';

function HorizontalGallery({ images }) {
  const itemRefs = useRef([]);

  const scrollToIndex = (index) => {
    itemRefs.current[index]?.scrollIntoView({
      behavior: 'smooth',
      inline: 'center',
    });
  };

  return (
    <div>
      <div className="thumbnails">
        {images.map((img, i) => (
          <button key={img.id} onClick={() => scrollToIndex(i)}>
            {i + 1}
          </button>
        ))}
      </div>

      <div className="gallery" style={{ display: 'flex', overflowX: 'auto' }}>
        {images.map((img, i) => (
          <img
            key={img.id}
            ref={(el) => { itemRefs.current[i] = el; }}
            src={img.src}
            alt={img.alt}
            width={400}
            height={300}
          />
        ))}
      </div>
    </div>
  );
}
```

**Recommendation:** Prefer the Map-based callback ref pattern in production. It handles additions, removals, and reordering correctly and avoids stale entries in the array.

---

### Q15. How do you forward refs through Higher-Order Components (HOCs)?

**Answer:**

HOCs wrap a component and return a new one, but they break ref forwarding because the `ref` attaches to the wrapper component, not the inner one. The fix is to use `forwardRef` in the HOC to plumb the ref through.

This is a classic pattern in production codebases that use HOCs for cross-cutting concerns like logging, theming, analytics, and permission gating.

```jsx
import { forwardRef, useEffect, useRef } from 'react';

// HOC that adds analytics tracking to any component
function withAnalytics(WrappedComponent, componentName) {
  const WithAnalytics = forwardRef(function WithAnalytics(props, ref) {
    const mountTime = useRef(Date.now());

    useEffect(() => {
      // Track mount
      analytics.track(`${componentName}.mounted`);

      return () => {
        // Track unmount with time spent
        const timeSpent = Date.now() - mountTime.current;
        analytics.track(`${componentName}.unmounted`, { timeSpent });
      };
    }, []);

    useEffect(() => {
      // Track prop changes
      analytics.track(`${componentName}.updated`, { props: Object.keys(props) });
    });

    // Forward ref to the wrapped component
    return <WrappedComponent ref={ref} {...props} />;
  });

  WithAnalytics.displayName = `withAnalytics(${componentName})`;
  return WithAnalytics;
}

// The inner component uses forwardRef to expose its DOM node
const TextInput = forwardRef(function TextInput({ label, error, ...rest }, ref) {
  return (
    <div className={`form-field ${error ? 'has-error' : ''}`}>
      <label>{label}</label>
      <input ref={ref} {...rest} />
      {error && <span className="error-msg">{error}</span>}
    </div>
  );
});

// Wrap with HOC — ref still reaches the <input>
const TrackedTextInput = withAnalytics(TextInput, 'TextInput');

function RegistrationForm() {
  const usernameRef = useRef(null);

  useEffect(() => {
    // This correctly focuses the <input> inside TrackedTextInput
    usernameRef.current?.focus();
  }, []);

  return (
    <form>
      <TrackedTextInput
        ref={usernameRef}
        label="Username"
        placeholder="Choose a username"
      />
    </form>
  );
}
```

**Key insight:** The ref travels through *two* layers of `forwardRef` — once in the HOC, once in `TextInput`. Each layer forwards it to the next until it reaches the actual DOM node.

**Production tip:** If you compose multiple HOCs (e.g., `withAnalytics(withTheme(TextInput))`), *every* HOC must use `forwardRef` or the chain breaks. This is one reason the React community has moved toward hooks over HOCs — hooks don't have this problem.

---

### Q16. How do you integrate third-party libraries (chart libraries, map SDKs, rich text editors) with React using refs?

**Answer:**

Third-party imperative libraries (D3, Chart.js, Leaflet, Mapbox, CodeMirror, Quill, Monaco Editor) need a DOM container to mount into. The pattern is always the same:

1. Create a ref for the container element.
2. Initialize the library instance in `useEffect` after mount, passing `ref.current`.
3. Store the library instance in another ref so you can update and destroy it.
4. Update the instance when props change (subsequent effects).
5. Destroy/dispose the instance on unmount.

```jsx
import { useRef, useEffect, memo } from 'react';
import Chart from 'chart.js/auto';

const BarChart = memo(function BarChart({ data, options = {} }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  // Initialize chart on mount
  useEffect(() => {
    const ctx = canvasRef.current.getContext('2d');

    chartRef.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map((d) => d.label),
        datasets: [
          {
            label: options.datasetLabel || 'Values',
            data: data.map((d) => d.value),
            backgroundColor: options.colors || '#6366f1',
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: 'easeOutQuart' },
        plugins: {
          legend: { display: !!options.showLegend },
        },
        scales: {
          y: { beginAtZero: true },
        },
        ...options.chartOptions,
      },
    });

    return () => {
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, []); // Mount-only

  // Update data without destroying and recreating
  useEffect(() => {
    if (!chartRef.current) return;

    chartRef.current.data.labels = data.map((d) => d.label);
    chartRef.current.data.datasets[0].data = data.map((d) => d.value);
    chartRef.current.update('active'); // Animate the transition
  }, [data]);

  return (
    <div style={{ position: 'relative', height: options.height || 300 }}>
      <canvas ref={canvasRef} />
    </div>
  );
});

// Leaflet map integration
function MapView({ center, zoom, markers }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerLayerRef = useRef(null);

  useEffect(() => {
    // Assumes leaflet CSS is already loaded
    const L = window.L;
    mapRef.current = L.map(containerRef.current).setView(center, zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
    }).addTo(mapRef.current);

    markerLayerRef.current = L.layerGroup().addTo(mapRef.current);

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Update markers when they change
  useEffect(() => {
    if (!markerLayerRef.current) return;
    const L = window.L;
    markerLayerRef.current.clearLayers();
    markers.forEach((m) => {
      L.marker([m.lat, m.lng]).addTo(markerLayerRef.current).bindPopup(m.label);
    });
  }, [markers]);

  // Pan to new center
  useEffect(() => {
    mapRef.current?.setView(center, zoom);
  }, [center, zoom]);

  return <div ref={containerRef} style={{ height: 400, width: '100%' }} />;
}
```

**Critical production considerations:**
- **Strict Mode:** In React 18 dev mode with `StrictMode`, effects run twice. Libraries that throw on double-initialization will break. Guard against this by checking if the instance already exists or by using cleanup properly.
- **Memory leaks:** Always call the library's destroy/dispose method in the effect's cleanup function.
- **Updates vs. re-initialization:** Updating data in-place (like `chart.update()`) is far cheaper than destroying and recreating. Structure your effects so mount logic and update logic are separate.

---

### Q17. How do you avoid stale refs in event handlers and timers (closures)?

**Answer:**

A "stale ref" problem occurs when a closure (event handler, timer callback, async function) captures an old value. With `useState`, values are captured at render time and can become stale. Refs, because they are mutable objects, always reflect the *latest* value — but you have to use them correctly.

**The problem:**

```jsx
import { useState, useEffect } from 'react';

function StaleCounter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // BUG: 'count' is captured from the first render (0)
      // This will always log 0
      console.log('Current count:', count);
    }, 1000);

    return () => clearInterval(id);
  }, []); // Empty deps — closure captures count = 0

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => setCount((c) => c + 1)}>Increment</button>
    </div>
  );
}
```

**The fix — use a ref to hold the latest value:**

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

function CorrectCounter() {
  const [count, setCount] = useState(0);
  const countRef = useRef(count);

  // Keep the ref in sync with the latest state
  useEffect(() => {
    countRef.current = count;
  }, [count]);

  useEffect(() => {
    const id = setInterval(() => {
      // Always reads the latest value via the ref
      console.log('Current count:', countRef.current);
    }, 1000);

    return () => clearInterval(id);
  }, []); // Safe — ref is a stable object

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => setCount((c) => c + 1)}>Increment</button>
    </div>
  );
}
```

**Production pattern — `useLatestRef` hook:**

```jsx
import { useRef, useEffect } from 'react';

function useLatestRef(value) {
  const ref = useRef(value);

  useEffect(() => {
    ref.current = value;
  });

  return ref;
}

// Debounced search with latest callback
function SearchInput({ onSearch }) {
  const onSearchRef = useLatestRef(onSearch);
  const timerRef = useRef(null);

  const handleChange = (e) => {
    const query = e.target.value;
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      // Always calls the latest onSearch, even if parent re-rendered
      // with a new function between keystrokes
      onSearchRef.current(query);
    }, 300);
  };

  useEffect(() => {
    return () => clearTimeout(timerRef.current);
  }, []);

  return <input type="search" onChange={handleChange} placeholder="Search…" />;
}
```

**Another common scenario — event handlers registered on `window` or `document`:**

```jsx
import { useEffect, useRef } from 'react';

function useKeyboardShortcut(key, callback) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === key) {
        callbackRef.current(e);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [key]); // Only re-register if the key changes, not the callback
}
```

**Rule of thumb:** If a callback is passed to something that outlives a single render (setTimeout, setInterval, addEventListener, WebSocket, IntersectionObserver), wrap it in a ref to avoid stale closures.

---

### Q18. How do you use refs with `requestAnimationFrame` for performance measurement and smooth animations?

**Answer:**

`requestAnimationFrame` (rAF) schedules a callback to run before the browser's next paint, making it ideal for smooth 60fps animations and precise performance measurements. Since rAF callbacks persist across renders, you need refs to store the animation frame ID (for cancellation) and to read the latest values without triggering re-renders.

**Smooth animation loop:**

```jsx
import { useRef, useEffect, useState, useCallback } from 'react';

function useAnimationFrame(callback, active = true) {
  const callbackRef = useRef(callback);
  const frameRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!active) return;

    const loop = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;

      callbackRef.current(elapsed, timestamp);
      frameRef.current = requestAnimationFrame(loop);
    };

    frameRef.current = requestAnimationFrame(loop);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      startTimeRef.current = null;
    };
  }, [active]);
}

// Smooth progress bar that doesn't cause React re-renders during animation
function SmoothProgressBar({ duration = 3000 }) {
  const barRef = useRef(null);
  const [running, setRunning] = useState(false);

  useAnimationFrame(
    (elapsed) => {
      const progress = Math.min(elapsed / duration, 1);
      if (barRef.current) {
        // Direct DOM mutation — no React re-renders during animation
        barRef.current.style.width = `${progress * 100}%`;
        barRef.current.style.backgroundColor = `hsl(${progress * 120}, 70%, 50%)`;
      }

      if (progress >= 1) {
        setRunning(false); // Single re-render at the end
      }
    },
    running
  );

  return (
    <div>
      <div
        style={{
          width: '100%',
          height: 24,
          background: '#e5e7eb',
          borderRadius: 12,
          overflow: 'hidden',
        }}
      >
        <div
          ref={barRef}
          style={{
            height: '100%',
            width: '0%',
            borderRadius: 12,
            transition: 'none',
          }}
        />
      </div>
      <button onClick={() => setRunning(true)} disabled={running}>
        Start
      </button>
    </div>
  );
}
```

**Performance measurement — FPS counter:**

```jsx
import { useRef, useEffect, useState } from 'react';

function FPSCounter() {
  const [fps, setFps] = useState(0);
  const framesRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const rafRef = useRef(null);

  useEffect(() => {
    const tick = (now) => {
      framesRef.current += 1;
      const delta = now - lastTimeRef.current;

      if (delta >= 1000) {
        setFps(Math.round((framesRef.current / delta) * 1000));
        framesRef.current = 0;
        lastTimeRef.current = now;
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  return (
    <div
      style={{
        position: 'fixed',
        top: 8,
        right: 8,
        background: fps > 50 ? '#22c55e' : fps > 30 ? '#eab308' : '#ef4444',
        color: '#fff',
        padding: '4px 10px',
        borderRadius: 6,
        fontFamily: 'monospace',
        fontSize: 14,
        zIndex: 10000,
      }}
    >
      {fps} FPS
    </div>
  );
}
```

**Measuring render performance with refs:**

```jsx
import { useRef, useEffect } from 'react';

function useRenderTiming(componentName) {
  const renderStartRef = useRef(null);

  // Called during render (before commit)
  renderStartRef.current = performance.now();

  useEffect(() => {
    const commitTime = performance.now();
    const renderDuration = commitTime - renderStartRef.current;

    if (renderDuration > 16) {
      console.warn(
        `[Perf] ${componentName} took ${renderDuration.toFixed(1)}ms to render — exceeds 16ms frame budget`
      );
    }
  });
}

function ExpensiveList({ items }) {
  useRenderTiming('ExpensiveList');

  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}
```

**Key point:** The common thread is that rAF callbacks and performance measurements operate *outside* React's render cycle. Refs let you read/write values from this "outside" world without the overhead of state updates.

---

### Q19. React 19 changes: How do `ref` as a prop (no `forwardRef` needed) work, and how should you prepare?

**Answer:**

React 19 introduced a major simplification: **function components can accept `ref` as a regular prop**. This eliminates the need for `forwardRef` in new code. The `ref` prop is no longer special-cased and stripped from props — it's passed through just like any other prop.

**Before (React 18 — `forwardRef` required):**

```jsx
import { forwardRef, useRef } from 'react';

const Button = forwardRef(function Button({ children, variant = 'primary', ...rest }, ref) {
  return (
    <button ref={ref} className={`btn btn-${variant}`} {...rest}>
      {children}
    </button>
  );
});

function Toolbar() {
  const saveRef = useRef(null);
  return <Button ref={saveRef} variant="primary">Save</Button>;
}
```

**After (React 19 — `ref` is a regular prop):**

```jsx
import { useRef } from 'react';

function Button({ children, variant = 'primary', ref, ...rest }) {
  return (
    <button ref={ref} className={`btn btn-${variant}`} {...rest}>
      {children}
    </button>
  );
}

function Toolbar() {
  const saveRef = useRef(null);
  return <Button ref={saveRef} variant="primary">Save</Button>;
}
```

The component is simpler — no wrapper function, no second argument. `ref` appears in the destructured props just like `children` or `variant`.

**Ref cleanup functions (React 19):**

React 19 also adds cleanup return values to ref callbacks, similar to `useEffect`:

```jsx
import { useState } from 'react';

function VideoPlayer({ src }) {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <video
      src={src}
      ref={(node) => {
        if (node) {
          // Setup: attach event listeners
          const handlePlay = () => setIsPlaying(true);
          const handlePause = () => setIsPlaying(false);

          node.addEventListener('play', handlePlay);
          node.addEventListener('pause', handlePause);

          // Cleanup: return a function (new in React 19)
          return () => {
            node.removeEventListener('play', handlePlay);
            node.removeEventListener('pause', handlePause);
          };
        }
      }}
    />
  );
}
```

**Migration strategy for React 18 → 19:**

1. `forwardRef` still works in React 19 — it's not removed, just no longer necessary.
2. A codemod is available: `npx codemod@latest react/19/replace-reactdom-render` (and others in the React 19 codemod suite) to automate migration.
3. For library authors: if you need to support both React 18 and 19, keep `forwardRef` until you drop React 18 support.

```jsx
// Dual-compatible component (works in both React 18 and 19)
import { forwardRef } from 'react';

const Input = forwardRef(function Input(props, ref) {
  const { label, ...rest } = props;
  return (
    <label>
      {label}
      <input ref={ref} {...rest} />
    </label>
  );
});

// When you drop React 18 support, simplify to:
// function Input({ label, ref, ...rest }) { ... }
```

**`useImperativeHandle` in React 19:**

`useImperativeHandle` still exists and works the same way. In React 19, pass the ref prop directly instead of using `forwardRef`:

```jsx
import { useImperativeHandle, useRef } from 'react';

function CustomDrawer({ ref, children }) {
  const [isOpen, setIsOpen] = useState(false);

  useImperativeHandle(ref, () => ({
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
  }));

  return isOpen ? <div className="drawer">{children}</div> : null;
}
```

---

### Q20. Build a production video player component with a full imperative ref API using `forwardRef` and `useImperativeHandle`.

**Answer:**

This is a real-world example that ties together everything: `forwardRef`, `useImperativeHandle`, internal refs for the DOM node, event listeners, and a clean imperative API that hides the raw `<video>` element from consumers.

The component exposes methods like `.play()`, `.pause()`, `.seek()`, `.setPlaybackRate()`, `.enterFullscreen()`, and read-only properties like `.currentTime`, `.duration`, `.isPlaying` — while keeping the `<video>` DOM node private.

```jsx
import {
  forwardRef,
  useImperativeHandle,
  useRef,
  useState,
  useEffect,
  useCallback,
} from 'react';

const VideoPlayer = forwardRef(function VideoPlayer(
  {
    src,
    poster,
    autoPlay = false,
    muted = false,
    onTimeUpdate,
    onEnded,
    onError,
    className = '',
  },
  ref
) {
  const videoRef = useRef(null);
  const [state, setState] = useState({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    buffered: 0,
    volume: 1,
    playbackRate: 1,
    isMuted: muted,
    isFullscreen: false,
    hasError: false,
  });

  // Expose imperative API to parent
  useImperativeHandle(
    ref,
    () => ({
      play() {
        return videoRef.current?.play();
      },
      pause() {
        videoRef.current?.pause();
      },
      toggle() {
        const v = videoRef.current;
        if (!v) return;
        return v.paused ? v.play() : v.pause();
      },
      seek(time) {
        if (videoRef.current) {
          videoRef.current.currentTime = Math.max(
            0,
            Math.min(time, videoRef.current.duration || 0)
          );
        }
      },
      skipForward(seconds = 10) {
        this.seek((videoRef.current?.currentTime || 0) + seconds);
      },
      skipBackward(seconds = 10) {
        this.seek((videoRef.current?.currentTime || 0) - seconds);
      },
      setVolume(vol) {
        if (videoRef.current) {
          videoRef.current.volume = Math.max(0, Math.min(1, vol));
        }
      },
      setPlaybackRate(rate) {
        if (videoRef.current) {
          videoRef.current.playbackRate = rate;
        }
      },
      toggleMute() {
        if (videoRef.current) {
          videoRef.current.muted = !videoRef.current.muted;
        }
      },
      async enterFullscreen() {
        try {
          await videoRef.current?.requestFullscreen();
        } catch (err) {
          console.warn('Fullscreen not available:', err);
        }
      },
      async exitFullscreen() {
        if (document.fullscreenElement) {
          await document.exitFullscreen();
        }
      },
      // Read-only properties
      get currentTime() {
        return videoRef.current?.currentTime || 0;
      },
      get duration() {
        return videoRef.current?.duration || 0;
      },
      get isPlaying() {
        return !videoRef.current?.paused;
      },
      get volume() {
        return videoRef.current?.volume ?? 1;
      },
      get playbackRate() {
        return videoRef.current?.playbackRate ?? 1;
      },
    }),
    []
  );

  // Sync internal state from video events
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    const handlers = {
      play: () => setState((s) => ({ ...s, isPlaying: true })),
      pause: () => setState((s) => ({ ...s, isPlaying: false })),
      timeupdate: () => {
        const time = v.currentTime;
        setState((s) => ({ ...s, currentTime: time }));
        onTimeUpdate?.(time, v.duration);
      },
      loadedmetadata: () => setState((s) => ({ ...s, duration: v.duration })),
      volumechange: () =>
        setState((s) => ({ ...s, volume: v.volume, isMuted: v.muted })),
      ratechange: () =>
        setState((s) => ({ ...s, playbackRate: v.playbackRate })),
      progress: () => {
        if (v.buffered.length > 0) {
          const bufferedEnd = v.buffered.end(v.buffered.length - 1);
          setState((s) => ({ ...s, buffered: bufferedEnd }));
        }
      },
      ended: () => {
        setState((s) => ({ ...s, isPlaying: false }));
        onEnded?.();
      },
      error: () => {
        setState((s) => ({ ...s, hasError: true, isPlaying: false }));
        onError?.(v.error);
      },
      fullscreenchange: () => {
        setState((s) => ({
          ...s,
          isFullscreen: document.fullscreenElement === v,
        }));
      },
    };

    Object.entries(handlers).forEach(([event, handler]) =>
      v.addEventListener(event, handler)
    );

    return () => {
      Object.entries(handlers).forEach(([event, handler]) =>
        v.removeEventListener(event, handler)
      );
    };
  }, [onTimeUpdate, onEnded, onError]);

  const formatTime = (seconds) => {
    if (!seconds || !isFinite(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleSeek = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const fraction = (e.clientX - rect.left) / rect.width;
    const v = videoRef.current;
    if (v) v.currentTime = fraction * v.duration;
  }, []);

  return (
    <div className={`video-player ${className}`}>
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        autoPlay={autoPlay}
        muted={muted}
        playsInline
        onClick={() => (videoRef.current?.paused ? videoRef.current.play() : videoRef.current.pause())}
        style={{ width: '100%', display: 'block', background: '#000' }}
      />

      {/* Custom controls */}
      <div className="controls-bar">
        <button
          onClick={() =>
            videoRef.current?.paused
              ? videoRef.current.play()
              : videoRef.current.pause()
          }
          aria-label={state.isPlaying ? 'Pause' : 'Play'}
        >
          {state.isPlaying ? '⏸' : '▶'}
        </button>

        <span className="time">
          {formatTime(state.currentTime)} / {formatTime(state.duration)}
        </span>

        {/* Progress bar */}
        <div
          className="progress-track"
          onClick={handleSeek}
          role="slider"
          aria-valuemin={0}
          aria-valuemax={state.duration}
          aria-valuenow={state.currentTime}
          tabIndex={0}
          style={{
            flex: 1,
            height: 6,
            background: '#374151',
            borderRadius: 3,
            cursor: 'pointer',
            position: 'relative',
            margin: '0 12px',
          }}
        >
          {/* Buffered */}
          <div
            style={{
              position: 'absolute',
              height: '100%',
              width: `${(state.buffered / (state.duration || 1)) * 100}%`,
              background: '#6b7280',
              borderRadius: 3,
            }}
          />
          {/* Played */}
          <div
            style={{
              position: 'absolute',
              height: '100%',
              width: `${(state.currentTime / (state.duration || 1)) * 100}%`,
              background: '#6366f1',
              borderRadius: 3,
            }}
          />
        </div>

        <button
          onClick={() => {
            if (videoRef.current) videoRef.current.muted = !videoRef.current.muted;
          }}
          aria-label={state.isMuted ? 'Unmute' : 'Mute'}
        >
          {state.isMuted ? '🔇' : '🔊'}
        </button>

        <select
          value={state.playbackRate}
          onChange={(e) => {
            if (videoRef.current) videoRef.current.playbackRate = Number(e.target.value);
          }}
          aria-label="Playback speed"
        >
          {[0.5, 0.75, 1, 1.25, 1.5, 2].map((r) => (
            <option key={r} value={r}>
              {r}x
            </option>
          ))}
        </select>
      </div>
    </div>
  );
});

// Parent component using the imperative API
function CoursePage({ lesson }) {
  const playerRef = useRef(null);
  const [bookmarks, setBookmarks] = useState([]);

  const handleBookmark = () => {
    const time = playerRef.current?.currentTime || 0;
    setBookmarks((prev) => [
      ...prev,
      { time, label: `Bookmark at ${formatTime(time)}` },
    ]);
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      const player = playerRef.current;
      if (!player) return;

      switch (e.key) {
        case ' ':
        case 'k':
          e.preventDefault();
          player.toggle();
          break;
        case 'ArrowRight':
          player.skipForward(10);
          break;
        case 'ArrowLeft':
          player.skipBackward(10);
          break;
        case 'ArrowUp':
          e.preventDefault();
          player.setVolume(player.volume + 0.1);
          break;
        case 'ArrowDown':
          e.preventDefault();
          player.setVolume(player.volume - 0.1);
          break;
        case 'f':
          player.enterFullscreen();
          break;
        case 'm':
          player.toggleMute();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="course-page">
      <h1>{lesson.title}</h1>

      <VideoPlayer
        ref={playerRef}
        src={lesson.videoUrl}
        poster={lesson.thumbnailUrl}
        onEnded={() => console.log('Lesson complete!')}
        onTimeUpdate={(time, duration) => {
          if (duration > 0 && time / duration > 0.9) {
            console.log('Student has watched 90%+ of the lesson');
          }
        }}
      />

      <div className="player-actions">
        <button onClick={() => playerRef.current?.skipBackward(30)}>
          ⏪ 30s
        </button>
        <button onClick={() => playerRef.current?.toggle()}>
          Play/Pause
        </button>
        <button onClick={() => playerRef.current?.skipForward(30)}>
          30s ⏩
        </button>
        <button onClick={handleBookmark}>🔖 Bookmark</button>
      </div>

      {bookmarks.length > 0 && (
        <div className="bookmarks">
          <h3>Bookmarks</h3>
          <ul>
            {bookmarks.map((b, i) => (
              <li key={i}>
                <button onClick={() => playerRef.current?.seek(b.time)}>
                  {b.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export { VideoPlayer, CoursePage };
```

**What this demonstrates:**
- `forwardRef` + `useImperativeHandle` to expose a rich, documented API.
- Internal `videoRef` is private — the parent cannot access the raw `<video>` element.
- Event listeners registered once on mount, cleaned up on unmount.
- Keyboard shortcuts use `useEffect` + `window` listener with the imperative ref API.
- Bookmark feature reads `currentTime` imperatively.
- `onTimeUpdate` and `onEnded` callbacks bridge the imperative/declarative worlds.
- Volume, playback rate, and fullscreen managed through the ref API.

This pattern scales to any media player, code editor, drawing canvas, or complex imperative widget in a production React application.

---

## Summary

| Concept | When to Use | Key API |
|---|---|---|
| `useRef` | DOM access, mutable values outside render cycle | `useRef(initialValue)` → `.current` |
| `forwardRef` | Expose a child's DOM node to a parent | `forwardRef((props, ref) => ...)` |
| `useImperativeHandle` | Expose custom methods instead of raw DOM | `useImperativeHandle(ref, () => ({...}))` |
| Callback refs | Need notification on attach/detach, dynamic lists | `ref={(node) => { ... }}` |
| Ref + Observer | IntersectionObserver, ResizeObserver, MutationObserver | Create observer in `useEffect`, observe `ref.current` |
| Ref + rAF | Smooth animations, perf measurement | Store rAF ID in ref, read latest values from refs |
| Stale ref fix | Timers, event listeners, async callbacks | `useLatestRef` pattern — sync ref in effect |
| React 19 ref-as-prop | New projects on React 19 | `function Comp({ ref }) { ... }` — no `forwardRef` |
