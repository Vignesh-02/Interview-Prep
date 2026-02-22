# Accessibility (a11y) in React 18 — Interview Questions

## Topic Introduction

**Accessibility (a11y)** is the practice of designing and building web applications so that **everyone** — including people with visual, auditory, motor, and cognitive disabilities — can perceive, understand, navigate, and interact with your content. In the United States alone, roughly 1 in 4 adults lives with a disability (CDC, 2023). Legal frameworks like the **Americans with Disabilities Act (ADA)** and international standards like the **Web Content Accessibility Guidelines (WCAG) 2.1** are not optional nice-to-haves; they carry real legal consequences (web accessibility lawsuits exceeded 4,000 in 2023) and, more importantly, they represent a moral obligation to make the web usable for everyone. React 18, as a component-based UI library that renders to the DOM, sits at the center of this challenge: every `<div>` that should be a `<button>`, every missing `aria-label`, every unmanaged focus trap in a modal directly translates into an unusable experience for someone relying on a screen reader, keyboard, or switch device.

React 18 provides a strong foundation for accessibility but does **not** make it automatic. Because React abstracts DOM manipulation behind JSX and a virtual DOM, developers must be intentional about producing **semantic HTML**, managing **focus** during dynamic updates (modals, route changes, lazy-loaded content), and ensuring that **ARIA attributes** are used correctly — not as a replacement for native semantics, but as a supplement where HTML falls short. React 18's concurrent features — `startTransition`, `Suspense`, automatic batching — introduce new considerations: content that appears asynchronously must announce itself to assistive technology via **live regions**, transitions should not steal focus unexpectedly, and skeleton screens must convey loading state non-visually. The ecosystem provides powerful testing tools (`jest-axe`, `axe-core`, `@testing-library/react` with its accessibility-first queries) and component libraries that bake in accessibility (Radix UI, Headless UI, React Aria), but the ultimate responsibility lies with the developer to understand *why* these patterns exist, not just how to copy-paste them.

```jsx
// A taste of accessible React 18 — a simple form with proper semantics, ARIA, and focus management
import { useRef, useEffect, useState } from 'react';

function AccessibleLoginForm() {
  const [error, setError] = useState('');
  const errorRef = useRef(null);

  useEffect(() => {
    // Move focus to the error message when it appears so screen readers announce it
    if (error && errorRef.current) {
      errorRef.current.focus();
    }
  }, [error]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    if (!formData.get('email')) {
      setError('Email is required.');
      return;
    }
    setError('');
    // submit logic...
  };

  return (
    <main aria-labelledby="login-heading">
      <h1 id="login-heading">Sign In</h1>

      {error && (
        <div
          ref={errorRef}
          role="alert"          {/* Live region — announced immediately */}
          tabIndex={-1}         {/* Allows programmatic focus */}
          aria-live="assertive"
          className="error-banner"
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        {/* Proper label association via htmlFor */}
        <label htmlFor="email">Email address</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          aria-describedby="email-hint"
          aria-invalid={!!error}
          required
        />
        <span id="email-hint" className="hint">
          We'll never share your email.
        </span>

        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />

        <button type="submit">Sign In</button>
      </form>
    </main>
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is web accessibility (a11y) and why does it matter? What are WCAG and ADA?

**Answer:**

**Web accessibility (a11y)** — the numeronym stands for "a" + 11 middle letters + "y" — means designing websites and applications so people with disabilities can use them effectively. Disabilities span a wide spectrum:

| Category | Examples | Assistive Technologies |
|---|---|---|
| **Visual** | Blindness, low vision, color blindness | Screen readers (NVDA, JAWS, VoiceOver), magnifiers, high-contrast modes |
| **Auditory** | Deafness, hard of hearing | Captions, transcripts |
| **Motor** | Limited fine motor control, paralysis | Keyboard-only navigation, switch devices, voice control |
| **Cognitive** | Dyslexia, ADHD, autism | Simplified layouts, clear language, reduced motion |

**WCAG (Web Content Accessibility Guidelines)** is the international standard published by the W3C. WCAG 2.1 defines three conformance levels:

- **Level A** — bare minimum (e.g., all images have alt text)
- **Level AA** — the standard most organizations target (and most laws reference)
- **Level AAA** — highest level, often impractical for entire sites

**ADA (Americans with Disabilities Act)** is a U.S. civil rights law. Courts have consistently ruled that websites of public-facing businesses must be accessible. The Department of Justice has referenced WCAG 2.1 AA as the benchmark.

**Why it matters in React:**

React renders the DOM. If your components produce inaccessible HTML, the entire app is inaccessible. Because React encourages composition and reusability, a single inaccessible component (e.g., a custom `<div onClick>` button) can propagate throughout the entire application.

```jsx
// ❌ Inaccessible — a div pretending to be a button
function BadButton({ onClick, children }) {
  return (
    <div className="btn" onClick={onClick}>
      {children}
    </div>
  );
}
// Problems:
// - Not focusable via keyboard (no tabIndex)
// - No role="button" for screen readers
// - No Enter/Space key handler
// - Not announced as interactive element

// ✅ Accessible — use the native <button> element
function GoodButton({ onClick, children, ...props }) {
  return (
    <button className="btn" onClick={onClick} {...props}>
      {children}
    </button>
  );
}
// Native <button> provides:
// - Keyboard focusable by default
// - Announced as "button" by screen readers
// - Enter and Space trigger onClick automatically
// - Participates in form submission
```

---

### Q2. What is semantic HTML and why is it the foundation of accessibility in React?

**Answer:**

**Semantic HTML** means using HTML elements that carry inherent meaning and behavior — `<button>`, `<nav>`, `<main>`, `<header>`, `<table>`, `<form>`, `<label>`, `<h1>`–`<h6>` — rather than generic containers like `<div>` and `<span>` for everything.

Semantic elements provide three critical things **for free**:

1. **Roles** — a `<button>` is announced as "button" by screen readers; a `<nav>` is a "navigation" landmark.
2. **Keyboard behavior** — `<button>` is focusable and activates with Enter/Space; `<a href>` is focusable and activates with Enter; `<input>` participates in tab order.
3. **Browser defaults** — `<form>` submits on Enter; `<details>` collapses/expands; `<select>` opens a dropdown.

**React-specific considerations:**

- JSX maps 1:1 to HTML elements. `<button>` in JSX renders `<button>` in the DOM.
- React uses `htmlFor` instead of `for` (reserved word in JS) and `className` instead of `class`.
- Fragments (`<>...</>`) let you avoid unnecessary wrapper `<div>`s that dilute semantic structure.

```jsx
// ❌ "Div soup" — no semantics, inaccessible
function Page() {
  return (
    <div className="page">
      <div className="header">
        <div className="logo">My App</div>
        <div className="nav">
          <div className="nav-link" onClick={() => navigate('/home')}>Home</div>
          <div className="nav-link" onClick={() => navigate('/about')}>About</div>
        </div>
      </div>
      <div className="content">
        <div className="title">Welcome</div>
        <div className="text">Some content here.</div>
      </div>
    </div>
  );
}

// ✅ Semantic HTML — accessible, meaningful, less code
function Page() {
  return (
    <>
      <header>
        <h1>My App</h1>
        <nav aria-label="Main navigation">
          <ul>
            <li><a href="/home">Home</a></li>
            <li><a href="/about">About</a></li>
          </ul>
        </nav>
      </header>
      <main>
        <h2>Welcome</h2>
        <p>Some content here.</p>
      </main>
    </>
  );
}
// Screen reader users can now:
// - Jump to <main> landmark
// - Navigate by headings (h1, h2)
// - Use the <nav> landmark to find links
// - Tab through <a> links with keyboard
```

---

### Q3. What are ARIA attributes and when should you use them in React?

**Answer:**

**ARIA (Accessible Rich Internet Applications)** is a set of HTML attributes that provide additional semantics to assistive technologies when native HTML alone is insufficient. The three main categories are:

1. **Roles** — `role="dialog"`, `role="alert"`, `role="tablist"` — define what an element *is*.
2. **Properties** — `aria-label`, `aria-describedby`, `aria-required` — provide additional information.
3. **States** — `aria-expanded`, `aria-checked`, `aria-disabled` — convey dynamic state.

**The First Rule of ARIA: Don't use ARIA if you can use a native HTML element.** A `<button>` is always better than `<div role="button" tabIndex={0}>`. ARIA does *not* add behavior — only semantics. If you set `role="button"` on a `<div>`, you still need to manually handle keyboard events (Enter/Space) and focus management.

In React, all `aria-*` attributes are passed through to the DOM unchanged:

```jsx
// React passes aria-* attributes directly to the DOM
function SearchBar() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');

  return (
    <div role="search">
      {/* aria-label: provides an accessible name when there's no visible label */}
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Search products"
        aria-expanded={isOpen}           {/* State: tells SR if results are showing */}
        aria-controls="search-results"   {/* Property: points to the results container */}
        aria-autocomplete="list"
      />

      {isOpen && (
        <ul id="search-results" role="listbox" aria-label="Search results">
          {/* aria-describedby: provides supplementary info */}
          <li role="option" aria-describedby="result-1-detail">
            Widget Pro
            <span id="result-1-detail" className="sr-only">
              $29.99 — 4.5 stars, 120 reviews
            </span>
          </li>
        </ul>
      )}
    </div>
  );
}

// Common ARIA attributes in React:
// aria-label        → accessible name (no visible label)
// aria-labelledby   → accessible name from another element's text
// aria-describedby  → supplementary description
// aria-live         → announce dynamic changes ("polite" or "assertive")
// aria-hidden       → hide decorative elements from screen readers
// aria-expanded     → toggle state (dropdowns, accordions)
// aria-current      → current item (nav links, pagination)
```

---

### Q4. How does keyboard navigation work in React, and what is tab order?

**Answer:**

**Keyboard navigation** is essential for users who cannot use a mouse — people with motor disabilities, power users, and screen reader users. The primary mechanism is the **Tab key**, which moves focus between interactive elements in the **tab order**.

**Tab order** follows the DOM order of focusable elements by default:

| Element | Focusable by Default? |
|---|---|
| `<button>`, `<a href>`, `<input>`, `<select>`, `<textarea>` | Yes |
| `<div>`, `<span>`, `<p>`, `<section>` | No |
| Any element with `tabIndex={0}` | Yes (in DOM order) |
| Any element with `tabIndex={-1}` | Only programmatically (via `.focus()`) |
| Any element with `tabIndex > 0` | Yes, but **avoid** — breaks natural order |

**React considerations:**

- React's component model means the visual order (CSS) can differ from DOM order. Always ensure DOM order matches visual reading order.
- `autoFocus` prop works in React but use it sparingly — it can be disorienting for screen reader users.
- All keyboard shortcuts should be documented and should not conflict with assistive technology shortcuts.

```jsx
// Managing keyboard interactions in a custom component
function ToolbarButton({ icon, label, onClick }) {
  const handleKeyDown = (e) => {
    // For custom interactive elements, handle Enter and Space
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick();
    }
  };

  return (
    // Using native <button> gives you Enter/Space handling for free!
    <button
      className="toolbar-btn"
      onClick={onClick}
      aria-label={label}
      title={label}
    >
      {icon}
    </button>
  );
}

// Arrow key navigation within a toolbar (roving tabindex pattern)
function Toolbar({ items }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const refs = useRef([]);

  const handleKeyDown = (e) => {
    let newIndex = activeIndex;

    switch (e.key) {
      case 'ArrowRight':
        newIndex = (activeIndex + 1) % items.length;
        break;
      case 'ArrowLeft':
        newIndex = (activeIndex - 1 + items.length) % items.length;
        break;
      case 'Home':
        newIndex = 0;
        break;
      case 'End':
        newIndex = items.length - 1;
        break;
      default:
        return;
    }

    e.preventDefault();
    setActiveIndex(newIndex);
    refs.current[newIndex]?.focus();
  };

  return (
    <div role="toolbar" aria-label="Text formatting" onKeyDown={handleKeyDown}>
      {items.map((item, index) => (
        <button
          key={item.id}
          ref={(el) => (refs.current[index] = el)}
          tabIndex={index === activeIndex ? 0 : -1}  {/* Roving tabindex */}
          aria-pressed={item.active}
          onClick={item.onClick}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
```

---

### Q5. How do you make forms accessible in React? What is the role of labels?

**Answer:**

Forms are one of the most critical areas for accessibility. Every form control **must** have an accessible name — the text that a screen reader announces when the user focuses the input. The primary mechanism is the `<label>` element.

**Three ways to associate labels with inputs:**

1. **Explicit association** (preferred) — `<label htmlFor="id">` matches `<input id="id">`
2. **Implicit association** — wrapping: `<label>Name <input /></label>`
3. **ARIA** (last resort) — `aria-label` or `aria-labelledby`

**Key form accessibility patterns:**

- Every input needs a label (even if visually hidden)
- Error messages must be associated with their input via `aria-describedby`
- Required fields should use `aria-required="true"` (or the native `required` attribute)
- Invalid fields should use `aria-invalid="true"`
- Group related inputs with `<fieldset>` and `<legend>`

```jsx
function AccessibleRegistrationForm() {
  const [errors, setErrors] = useState({});

  const validate = (formData) => {
    const newErrors = {};
    if (!formData.get('name')) newErrors.name = 'Name is required.';
    if (!formData.get('email')) newErrors.email = 'Email is required.';
    const password = formData.get('password');
    if (!password || password.length < 8)
      newErrors.password = 'Password must be at least 8 characters.';
    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newErrors = validate(formData);
    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      // Submit the form
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="User registration">
      {/* Grouped radio buttons use fieldset + legend */}
      <fieldset>
        <legend>Account Type</legend>
        <label>
          <input type="radio" name="accountType" value="personal" defaultChecked />
          Personal
        </label>
        <label>
          <input type="radio" name="accountType" value="business" />
          Business
        </label>
      </fieldset>

      {/* Explicit label association + error messaging */}
      <div>
        <label htmlFor="reg-name">Full Name *</label>
        <input
          id="reg-name"
          name="name"
          type="text"
          required
          aria-required="true"
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? 'name-error' : undefined}
        />
        {errors.name && (
          <span id="name-error" role="alert" className="error">
            {errors.name}
          </span>
        )}
      </div>

      <div>
        <label htmlFor="reg-email">Email *</label>
        <input
          id="reg-email"
          name="email"
          type="email"
          required
          aria-required="true"
          aria-invalid={!!errors.email}
          aria-describedby="email-hint email-error"
          autoComplete="email"
        />
        <span id="email-hint" className="hint">
          We'll send a verification link.
        </span>
        {errors.email && (
          <span id="email-error" role="alert" className="error">
            {errors.email}
          </span>
        )}
      </div>

      <div>
        <label htmlFor="reg-password">Password *</label>
        <input
          id="reg-password"
          name="password"
          type="password"
          required
          aria-required="true"
          aria-invalid={!!errors.password}
          aria-describedby="password-requirements password-error"
          autoComplete="new-password"
        />
        <span id="password-requirements" className="hint">
          Minimum 8 characters, one uppercase, one number.
        </span>
        {errors.password && (
          <span id="password-error" role="alert" className="error">
            {errors.password}
          </span>
        )}
      </div>

      <button type="submit">Create Account</button>
    </form>
  );
}
```

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you manage focus with `useRef` in React 18, particularly for modals and dynamic content?

**Answer:**

Focus management is one of the most important — and most overlooked — aspects of accessibility. When content appears dynamically (a modal opens, a new section loads, an error appears), **sighted users** can immediately see it, but **screen reader and keyboard users** may not know it exists unless focus is moved programmatically.

React's `useRef` hook gives you a reference to a DOM node, and calling `.focus()` on it moves keyboard focus there. Combined with `useEffect`, you can respond to state changes by shifting focus appropriately.

**Key patterns:**

| Scenario | Focus Target |
|---|---|
| Modal opens | First focusable element inside the modal (or the modal itself) |
| Modal closes | The element that triggered the modal |
| Error appears | The error message or the first invalid field |
| Content loads dynamically | The new content container or a heading within it |
| Item deleted from a list | The next item, or the previous item, or the list heading |

```jsx
import { useRef, useEffect, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';

function useModal() {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef(null);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => {
    setIsOpen(false);
    // Return focus to the trigger element when the modal closes
    // Use requestAnimationFrame to ensure the DOM has updated
    requestAnimationFrame(() => {
      triggerRef.current?.focus();
    });
  }, []);

  return { isOpen, open, close, triggerRef };
}

function Modal({ isOpen, onClose, title, children }) {
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // Store the currently focused element so we can restore it later
      previousFocusRef.current = document.activeElement;
      // Move focus into the modal
      modalRef.current?.focus();

      // Prevent scrolling on the body
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        tabIndex={-1}               {/* Allows programmatic focus */}
        onClick={(e) => e.stopPropagation()}
        className="modal-content"
      >
        <h2 id="modal-title">{title}</h2>
        {children}
        <button onClick={onClose} aria-label="Close dialog">
          ✕
        </button>
      </div>
    </div>,
    document.body
  );
}

// Usage
function App() {
  const { isOpen, open, close, triggerRef } = useModal();

  return (
    <main>
      <button ref={triggerRef} onClick={open}>
        Delete Account
      </button>

      <Modal isOpen={isOpen} onClose={close} title="Confirm Deletion">
        <p>Are you sure you want to delete your account? This cannot be undone.</p>
        <div className="modal-actions">
          <button onClick={close}>Cancel</button>
          <button onClick={() => { /* delete logic */ close(); }}>
            Delete
          </button>
        </div>
      </Modal>
    </main>
  );
}
```

---

### Q7. What are skip navigation links and how do you implement them in React?

**Answer:**

**Skip navigation links** allow keyboard and screen reader users to bypass repetitive content (navigation bars, headers, sidebars) and jump directly to the main content of the page. Without them, a keyboard user might have to Tab through 20+ navigation links on every single page before reaching the content they want.

WCAG 2.1 Success Criterion **2.4.1 (Bypass Blocks)** at Level A requires a mechanism to skip repeated content blocks.

**Implementation strategy:**

1. Place an anchor link as the very first focusable element in the DOM.
2. The link targets the `<main>` content area via an `id`.
3. Visually hide the link by default, but make it visible when focused (so sighted keyboard users can see it).

```jsx
// components/SkipNav.jsx
import './SkipNav.css';

function SkipNav() {
  return (
    <a href="#main-content" className="skip-nav">
      Skip to main content
    </a>
  );
}

// App.jsx — usage at the top level
function App() {
  return (
    <>
      <SkipNav />
      <header>
        <nav aria-label="Main navigation">
          <a href="/">Home</a>
          <a href="/products">Products</a>
          <a href="/about">About</a>
          <a href="/contact">Contact</a>
          {/* ... 15+ more links ... */}
        </nav>
      </header>

      {/* The target — id must match the skip link href */}
      <main id="main-content" tabIndex={-1}>
        <h1>Welcome to Our Store</h1>
        <p>Browse our collection of products.</p>
      </main>

      <footer>
        <p>© 2024 Our Store</p>
      </footer>
    </>
  );
}
```

```jsx
/* SkipNav.css */
/* Visually hidden by default, visible on focus */
.skip-nav {
  position: absolute;
  top: -100%;
  left: 16px;
  z-index: 9999;
  padding: 12px 24px;
  background: #1a1a2e;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  border-radius: 0 0 8px 8px;
  transition: top 0.2s ease;
}

.skip-nav:focus {
  top: 0;                          /* Slides into view when focused */
  outline: 3px solid #e94560;
  outline-offset: 2px;
}
```

For SPAs with React Router, you may also need to **reset focus to the skip link target** on route changes — see Q15 for route change announcements.

---

### Q8. How do you test accessibility with screen readers, and what strategies should you follow?

**Answer:**

Automated tools catch roughly **30–40% of accessibility issues** (the mechanical ones — missing alt text, low contrast, missing labels). The remaining 60–70% require **manual testing with assistive technologies** — particularly screen readers — to verify that the *experience* makes sense.

**Screen readers to test with:**

| Screen Reader | OS | Browser | Market Share |
|---|---|---|---|
| **NVDA** | Windows | Firefox, Chrome | ~40% (free) |
| **JAWS** | Windows | Chrome, Edge | ~30% (commercial) |
| **VoiceOver** | macOS / iOS | Safari | ~25% (built-in) |
| **TalkBack** | Android | Chrome | ~5% (built-in) |

**Testing strategy for a React 18 app:**

1. **Keyboard-only test first** — Tab through the entire page. Can you reach every interactive element? Can you operate it? Can you see where focus is?
2. **Screen reader navigation** — Use heading navigation (H key in NVDA/JAWS), landmark navigation (D key), and form mode to verify structure.
3. **Dynamic content** — Open modals, trigger notifications, navigate between routes. Does the screen reader announce changes?
4. **Focus management** — When a modal opens, does focus move into it? When it closes, does focus return to the trigger?

```jsx
// Testing setup: a component and its accessibility test using jest-axe
// components/Alert.jsx
function Alert({ type = 'info', message, onDismiss }) {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`alert alert-${type}`}
    >
      <span className="alert-icon" aria-hidden="true">
        {type === 'error' ? '⚠' : 'ℹ'}
      </span>
      <span>{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label={`Dismiss ${type} alert: ${message}`}
        >
          ✕
        </button>
      )}
    </div>
  );
}

// __tests__/Alert.test.jsx
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import Alert from '../components/Alert';

expect.extend(toHaveNoViolations);

describe('Alert component accessibility', () => {
  it('should have no axe violations', async () => {
    const { container } = render(
      <Alert type="error" message="Something went wrong" onDismiss={() => {}} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should be announced by screen readers via role="alert"', () => {
    render(<Alert type="error" message="Something went wrong" />);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Something went wrong');
  });

  it('dismiss button should have an accessible name', () => {
    render(
      <Alert type="error" message="Something went wrong" onDismiss={() => {}} />
    );
    const button = screen.getByRole('button', {
      name: /dismiss error alert/i,
    });
    expect(button).toBeInTheDocument();
  });
});
```

---

### Q9. What are the requirements for color contrast and visual accessibility, and how do you handle them in React?

**Answer:**

**Color contrast** refers to the difference in luminance between foreground (text) and background colors. Insufficient contrast makes text unreadable for people with low vision or color blindness (affecting ~8% of males and ~0.5% of females).

**WCAG 2.1 contrast requirements:**

| Content | Level AA | Level AAA |
|---|---|---|
| Normal text (< 18px or < 14px bold) | **4.5:1** minimum | 7:1 minimum |
| Large text (≥ 18px or ≥ 14px bold) | **3:1** minimum | 4.5:1 minimum |
| UI components & graphical objects | **3:1** minimum | — |

**Key principles:**

1. **Never use color as the only means** of conveying information (WCAG 1.4.1). Error fields should not just turn red — add an icon and/or text.
2. **Ensure focus indicators are visible** — the default browser outline has at least 3:1 contrast, but custom focus styles often fail this.
3. **Support dark mode and high-contrast mode** — Windows High Contrast Mode overrides your CSS.
4. **Test with color blindness simulators** (e.g., Chrome DevTools → Rendering → Emulate vision deficiencies).

```jsx
// A design system color utility that enforces contrast at the component level
import { useState, useEffect } from 'react';

// Utility: calculate relative luminance (WCAG formula)
function getLuminance(hex) {
  const rgb = hex.match(/\w\w/g).map((x) => {
    const c = parseInt(x, 16) / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
}

function getContrastRatio(hex1, hex2) {
  const l1 = getLuminance(hex1);
  const l2 = getLuminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Badge component that ensures accessible contrast
function Badge({ label, bgColor, textColor }) {
  const ratio = getContrastRatio(bgColor, textColor);
  const meetsAA = ratio >= 4.5;

  if (process.env.NODE_ENV === 'development' && !meetsAA) {
    console.warn(
      `Badge "${label}": contrast ratio ${ratio.toFixed(2)}:1 fails WCAG AA (min 4.5:1). ` +
      `bg=${bgColor}, text=${textColor}`
    );
  }

  return (
    <span
      className="badge"
      style={{ backgroundColor: bgColor, color: textColor }}
    >
      {label}
    </span>
  );
}

// Form validation that doesn't rely solely on color
function FormField({ label, error, children }) {
  return (
    <div className={`field ${error ? 'field--error' : ''}`}>
      <label>{label}</label>
      {children}
      {error && (
        <div className="field-error" role="alert">
          {/* Icon + text — not just color */}
          <svg aria-hidden="true" className="error-icon" /* ... */ />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

// CSS for visible focus indicators
/*
  .btn:focus-visible {
    outline: 3px solid #2563eb;
    outline-offset: 2px;
  }

  // Never do this:
  // *:focus { outline: none; }  ← removes keyboard focus indicator entirely!
*/
```

---

### Q10. How do you build an accessible modal/dialog with a focus trap in React 18?

**Answer:**

An accessible modal (WCAG pattern: dialog) must satisfy several requirements:

1. **Focus trap** — Tab and Shift+Tab cycle only through elements inside the modal; focus never escapes to the page behind it.
2. **Focus on open** — Focus moves to the first focusable element (or the dialog itself) when it opens.
3. **Focus on close** — Focus returns to the element that triggered the modal.
4. **Escape key** — Pressing Escape closes the modal.
5. **Background inert** — Content behind the modal is not accessible to screen readers (`aria-modal="true"` or the `inert` attribute on the background).
6. **Announced as dialog** — `role="dialog"` and `aria-labelledby` pointing to the title.
7. **Rendered in a portal** — To escape z-index stacking contexts.

```jsx
import { useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';

function FocusTrap({ children }) {
  const trapRef = useRef(null);

  useEffect(() => {
    const trapElement = trapRef.current;
    if (!trapElement) return;

    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    const handleKeyDown = (e) => {
      if (e.key !== 'Tab') return;

      const focusableElements = trapElement.querySelectorAll(focusableSelectors);
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        // Shift+Tab: if focus is on the first element, wrap to the last
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab: if focus is on the last element, wrap to the first
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    trapElement.addEventListener('keydown', handleKeyDown);
    return () => trapElement.removeEventListener('keydown', handleKeyDown);
  }, []);

  return <div ref={trapRef}>{children}</div>;
}

function AccessibleModal({ isOpen, onClose, title, children }) {
  const dialogRef = useRef(null);
  const triggerRef = useRef(null);

  // Store the trigger element when opening
  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement;

      // Move focus to the dialog
      requestAnimationFrame(() => {
        dialogRef.current?.focus();
      });

      // Make background content inert (HTML inert attribute)
      const appRoot = document.getElementById('root');
      if (appRoot) appRoot.setAttribute('inert', '');

      return () => {
        if (appRoot) appRoot.removeAttribute('inert');
      };
    }
  }, [isOpen]);

  // Restore focus on close
  useEffect(() => {
    if (!isOpen && triggerRef.current) {
      triggerRef.current.focus();
      triggerRef.current = null;
    }
  }, [isOpen]);

  // Escape key handler
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  if (!isOpen) return null;

  return createPortal(
    <div
      className="modal-backdrop"
      onClick={onClose}
      onKeyDown={handleKeyDown}
    >
      <FocusTrap>
        <div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby="dialog-title"
          aria-describedby="dialog-desc"
          tabIndex={-1}
          className="modal-dialog"
          onClick={(e) => e.stopPropagation()}
        >
          <h2 id="dialog-title">{title}</h2>
          <div id="dialog-desc">{children}</div>
          <button onClick={onClose} aria-label="Close dialog">
            ✕
          </button>
        </div>
      </FocusTrap>
    </div>,
    document.body
  );
}

// Production usage
function SettingsPage() {
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <section>
      <h1>Settings</h1>
      <button onClick={() => setShowConfirm(true)}>
        Reset All Preferences
      </button>

      <AccessibleModal
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        title="Reset Preferences?"
      >
        <p>This will restore all settings to their default values.</p>
        <div className="modal-actions">
          <button onClick={() => setShowConfirm(false)}>Cancel</button>
          <button
            onClick={() => {
              resetPreferences();
              setShowConfirm(false);
            }}
            className="btn-danger"
          >
            Reset
          </button>
        </div>
      </AccessibleModal>
    </section>
  );
}
```

---

### Q11. How do you build an accessible dropdown menu and combobox in React?

**Answer:**

Dropdowns and comboboxes are notoriously difficult to make accessible because they combine several interaction patterns: a trigger that toggles visibility, a list of options, keyboard navigation (arrow keys), type-ahead filtering, and selection. The WAI-ARIA authoring practices define two primary patterns:

1. **Menu** (`role="menu"`) — for action menus (like a file menu). Items are `role="menuitem"`.
2. **Listbox / Combobox** (`role="listbox"`, `role="combobox"`) — for selection from a list of options.

**Key requirements:**

- **Trigger** announces its expanded state (`aria-expanded`)
- **Arrow keys** navigate between options; **Home/End** jump to first/last
- **Enter/Space** select the active option
- **Escape** closes the menu and returns focus to the trigger
- **Type-ahead** — typing characters jumps to matching options
- The active option uses `aria-activedescendant` (combobox) or receives focus directly (menu)

```jsx
import { useState, useRef, useCallback, useEffect } from 'react';

function AccessibleCombobox({ label, options, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  const filtered = options.filter((opt) =>
    opt.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleInputChange = (e) => {
    setQuery(e.target.value);
    setIsOpen(true);
    setActiveIndex(0);
  };

  const selectOption = useCallback(
    (option) => {
      setQuery(option.label);
      setIsOpen(false);
      setActiveIndex(-1);
      onSelect(option);
      inputRef.current?.focus();
    },
    [onSelect]
  );

  const handleKeyDown = (e) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setActiveIndex(0);
        } else {
          setActiveIndex((prev) => Math.min(prev + 1, filtered.length - 1));
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (isOpen && activeIndex >= 0 && filtered[activeIndex]) {
          selectOption(filtered[activeIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setActiveIndex(-1);
        inputRef.current?.focus();
        break;
      case 'Home':
        e.preventDefault();
        setActiveIndex(0);
        break;
      case 'End':
        e.preventDefault();
        setActiveIndex(filtered.length - 1);
        break;
    }
  };

  // Scroll active option into view
  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const activeOption = listRef.current.children[activeIndex];
      activeOption?.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex]);

  const activeId = activeIndex >= 0 ? `combo-option-${activeIndex}` : undefined;

  return (
    <div className="combobox-wrapper">
      <label htmlFor="combo-input" id="combo-label">
        {label}
      </label>
      <div className="combobox-container">
        <input
          ref={inputRef}
          id="combo-input"
          role="combobox"
          aria-expanded={isOpen}
          aria-controls="combo-listbox"
          aria-activedescendant={activeId}
          aria-autocomplete="list"
          aria-labelledby="combo-label"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query && setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          autoComplete="off"
        />
        <button
          tabIndex={-1}
          aria-label={isOpen ? 'Close suggestions' : 'Open suggestions'}
          aria-expanded={isOpen}
          onClick={() => {
            setIsOpen(!isOpen);
            inputRef.current?.focus();
          }}
        >
          ▾
        </button>
      </div>

      {isOpen && filtered.length > 0 && (
        <ul
          ref={listRef}
          id="combo-listbox"
          role="listbox"
          aria-label={label}
        >
          {filtered.map((option, index) => (
            <li
              key={option.value}
              id={`combo-option-${index}`}
              role="option"
              aria-selected={index === activeIndex}
              className={index === activeIndex ? 'active' : ''}
              onClick={() => selectOption(option)}
              onMouseEnter={() => setActiveIndex(index)}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}

      {isOpen && filtered.length === 0 && (
        <div role="status" className="no-results">
          No matching options
        </div>
      )}

      {/* Live region for screen reader announcements */}
      <div aria-live="polite" className="sr-only">
        {isOpen && filtered.length > 0
          ? `${filtered.length} result${filtered.length !== 1 ? 's' : ''} available`
          : ''}
      </div>
    </div>
  );
}

// Usage
function CountrySelector() {
  const countries = [
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
    { value: 'ca', label: 'Canada' },
    { value: 'au', label: 'Australia' },
    // ... more countries
  ];

  return (
    <AccessibleCombobox
      label="Select Country"
      options={countries}
      onSelect={(country) => console.log('Selected:', country)}
    />
  );
}
```

---

### Q12. What are live regions and how do you use `aria-live` for dynamic content in React 18?

**Answer:**

**Live regions** are ARIA-designated areas of the page that tell assistive technologies to **announce changes** to their content automatically — without the user needing to navigate to them. This is critical in React applications where content updates dynamically (notifications, form validation, loading states, real-time data).

**`aria-live` values:**

| Value | Behavior | Use Case |
|---|---|---|
| `"polite"` | Waits until the screen reader finishes current speech | Status updates, search results count, non-urgent notifications |
| `"assertive"` | Interrupts current speech immediately | Error messages, time-sensitive alerts, urgent warnings |
| `"off"` | No announcements (default) | Explicitly silencing a region |

**Important companion attributes:**

- `aria-atomic="true"` — Announce the **entire** region content on change, not just the changed node.
- `aria-relevant="additions text"` — What types of changes to announce (additions, removals, text, all).

**Critical React gotcha:** The live region container **must exist in the DOM before the content changes**. If you conditionally render the container and its content at the same time, screen readers may miss the announcement.

```jsx
import { useState, useEffect, useCallback } from 'react';

// ❌ WRONG: Conditional rendering of the live region itself
function BadNotification({ message }) {
  // Screen readers may NOT announce this because the container
  // and its content appear simultaneously
  return message ? (
    <div role="alert" aria-live="assertive">
      {message}
    </div>
  ) : null;
}

// ✅ CORRECT: Live region container always in the DOM; content changes within it
function Notification({ message }) {
  return (
    <div role="status" aria-live="polite" aria-atomic="true">
      {/* Container always exists; only inner content changes */}
      {message && <p>{message}</p>}
    </div>
  );
}

// Production example: real-time search with live result announcements
function LiveSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [announcement, setAnnouncement] = useState('');

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setAnnouncement('');
      return;
    }

    setIsSearching(true);
    const controller = new AbortController();

    const timer = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/search?q=${encodeURIComponent(query)}`,
          { signal: controller.signal }
        );
        const data = await res.json();
        setResults(data.items);

        // Update the live region with result count
        setAnnouncement(
          data.items.length === 0
            ? `No results found for "${query}"`
            : `${data.items.length} result${data.items.length !== 1 ? 's' : ''} found for "${query}"`
        );
      } catch (err) {
        if (err.name !== 'AbortError') {
          setAnnouncement('Search failed. Please try again.');
        }
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  return (
    <div>
      <label htmlFor="search-input">Search</label>
      <input
        id="search-input"
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-describedby="search-status"
        aria-controls="search-results"
      />

      {/* Live region: always in the DOM, content changes trigger announcements */}
      <div
        id="search-status"
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {isSearching ? 'Searching…' : announcement}
      </div>

      <ul id="search-results" role="list" aria-label="Search results">
        {results.map((item) => (
          <li key={item.id}>
            <a href={item.url}>{item.title}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you test accessibility programmatically using jest-axe, axe-core, and Lighthouse?

**Answer:**

Automated accessibility testing catches structural issues — missing labels, broken ARIA, insufficient contrast — at scale. A robust strategy layers multiple tools:

| Tool | What It Tests | When It Runs |
|---|---|---|
| **jest-axe** | Component-level HTML against axe-core rules | Unit/integration tests |
| **axe-core** (via Playwright/Cypress) | Full rendered pages | E2E tests |
| **Lighthouse CI** | Page-level audit (a11y + perf + SEO) | CI pipeline on every PR |
| **eslint-plugin-jsx-a11y** | Static JSX analysis (missing alts, bad roles) | Lint time (IDE + CI) |

**jest-axe** wraps `axe-core` for use with Jest and Testing Library. It analyzes the rendered DOM and reports WCAG violations.

```jsx
// 1. jest-axe: Component-level tests
// __tests__/DataTable.test.jsx
import { render, screen, within } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { DataTable } from '../components/DataTable';

expect.extend(toHaveNoViolations);

const mockData = [
  { id: 1, name: 'Alice', role: 'Engineer', status: 'Active' },
  { id: 2, name: 'Bob', role: 'Designer', status: 'Inactive' },
];

describe('DataTable accessibility', () => {
  it('should have no axe violations', async () => {
    const { container } = render(
      <DataTable
        caption="Team members"
        data={mockData}
        columns={['name', 'role', 'status']}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have no violations when sorted', async () => {
    const { container } = render(
      <DataTable
        caption="Team members"
        data={mockData}
        columns={['name', 'role', 'status']}
        sortable
      />
    );

    // Trigger a sort
    const nameHeader = screen.getByRole('columnheader', { name: /name/i });
    await userEvent.click(nameHeader);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  // Test specific ARIA attributes manually (jest-axe won't catch everything)
  it('sort buttons should announce sort direction', async () => {
    render(
      <DataTable
        caption="Team members"
        data={mockData}
        columns={['name', 'role', 'status']}
        sortable
      />
    );

    const nameHeader = screen.getByRole('columnheader', { name: /name/i });
    const sortButton = within(nameHeader).getByRole('button');

    expect(sortButton).toHaveAttribute('aria-sort', 'none');

    await userEvent.click(sortButton);
    expect(sortButton).toHaveAttribute('aria-sort', 'ascending');

    await userEvent.click(sortButton);
    expect(sortButton).toHaveAttribute('aria-sort', 'descending');
  });
});

// 2. axe-core with Playwright: E2E page-level testing
// e2e/accessibility.spec.ts (Playwright)
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility audit', () => {
  test('home page should have no a11y violations', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .exclude('.third-party-widget') // Exclude content you don't control
      .analyze();

    expect(results.violations).toEqual([]);
  });

  test('modal dialog should be accessible when open', async ({ page }) => {
    await page.goto('/settings');
    await page.click('button:has-text("Delete Account")');

    // Wait for modal to appear
    await page.waitForSelector('[role="dialog"]');

    const results = await new AxeBuilder({ page })
      .include('[role="dialog"]')
      .analyze();

    expect(results.violations).toEqual([]);
  });
});

// 3. ESLint plugin for static analysis — .eslintrc.js
/*
  module.exports = {
    plugins: ['jsx-a11y'],
    extends: ['plugin:jsx-a11y/recommended'],
    rules: {
      'jsx-a11y/anchor-is-valid': 'error',
      'jsx-a11y/click-events-have-key-events': 'error',
      'jsx-a11y/no-static-element-interactions': 'error',
      'jsx-a11y/label-has-associated-control': ['error', {
        assert: 'either',
      }],
    },
  };
*/
```

---

### Q14. How do you build an accessible data table with sorting in React?

**Answer:**

Data tables are one of the most information-dense components in a web app. Screen reader users rely entirely on proper table semantics (`<table>`, `<thead>`, `<th>`, `<tbody>`, `<td>`) and ARIA attributes to navigate and understand tabular data. A screen reader typically announces "Row 3, Column 2: Designer" — but only if the markup is correct.

**Requirements for an accessible sortable table:**

1. Use native `<table>` elements — not `<div>` grids
2. `<caption>` or `aria-label` provides the table's accessible name
3. `<th scope="col">` for column headers, `<th scope="row">` for row headers
4. Sort buttons inside `<th>` use `aria-sort` ("ascending", "descending", or "none")
5. Live region announces the sort change to screen readers
6. Keyboard navigation: Tab to sort buttons, Enter/Space to activate

```jsx
import { useState, useCallback } from 'react';

function AccessibleSortableTable({ caption, columns, data }) {
  const [sortConfig, setSortConfig] = useState({
    key: null,
    direction: 'none', // 'none' | 'ascending' | 'descending'
  });
  const [announcement, setAnnouncement] = useState('');

  const sortedData = useCallback(() => {
    if (!sortConfig.key || sortConfig.direction === 'none') return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal < bVal) return sortConfig.direction === 'ascending' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'ascending' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig])();

  const handleSort = (columnKey, columnLabel) => {
    let newDirection;
    if (sortConfig.key !== columnKey || sortConfig.direction === 'none') {
      newDirection = 'ascending';
    } else if (sortConfig.direction === 'ascending') {
      newDirection = 'descending';
    } else {
      newDirection = 'none';
    }

    setSortConfig({ key: columnKey, direction: newDirection });

    // Announce the sort change via live region
    if (newDirection === 'none') {
      setAnnouncement(`Table is no longer sorted.`);
    } else {
      setAnnouncement(
        `Table sorted by ${columnLabel}, ${newDirection} order.`
      );
    }
  };

  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey || sortConfig.direction === 'none') {
      return '⇅'; // unsorted
    }
    return sortConfig.direction === 'ascending' ? '↑' : '↓';
  };

  return (
    <div>
      {/* Live region for sort announcements */}
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      <table aria-label={caption}>
        <caption>{caption}</caption>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                aria-sort={
                  sortConfig.key === col.key ? sortConfig.direction : 'none'
                }
              >
                {col.sortable ? (
                  <button
                    className="sort-button"
                    onClick={() => handleSort(col.key, col.label)}
                    aria-label={`Sort by ${col.label}`}
                  >
                    {col.label}
                    <span aria-hidden="true" className="sort-icon">
                      {getSortIcon(col.key)}
                    </span>
                  </button>
                ) : (
                  col.label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, rowIndex) => (
            <tr key={row.id ?? rowIndex}>
              {columns.map((col, colIndex) => {
                const CellTag = colIndex === 0 ? 'th' : 'td';
                return (
                  <CellTag
                    key={col.key}
                    {...(colIndex === 0 ? { scope: 'row' } : {})}
                  >
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </CellTag>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Usage
function EmployeeDashboard() {
  const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'department', label: 'Department', sortable: true },
    { key: 'salary', label: 'Salary', sortable: true,
      render: (val) => `$${val.toLocaleString()}` },
    { key: 'status', label: 'Status', sortable: true,
      render: (val) => (
        <span className={`badge badge-${val.toLowerCase()}`}>
          {val}
        </span>
      )
    },
  ];

  const employees = [
    { id: 1, name: 'Alice Johnson', department: 'Engineering', salary: 120000, status: 'Active' },
    { id: 2, name: 'Bob Smith', department: 'Design', salary: 95000, status: 'Active' },
    { id: 3, name: 'Carol White', department: 'Marketing', salary: 85000, status: 'On Leave' },
  ];

  return (
    <AccessibleSortableTable
      caption="Employee Directory"
      columns={columns}
      data={employees}
    />
  );
}
```

---

### Q15. How do you announce route changes in a single-page application (SPA) built with React?

**Answer:**

In traditional multi-page applications, every page navigation triggers a full page load. Screen readers automatically announce the new page title. In SPAs built with React Router (or similar), the DOM is updated dynamically — **screen readers get no automatic notification that the page changed**. This is one of the most common accessibility failures in SPAs.

**Requirements (WCAG 2.4.2 — Page Titled, WCAG 3.2.3 — Consistent Navigation):**

1. Update `document.title` on every route change
2. Announce the new page to screen readers (live region or focus management)
3. Move focus to the page heading or a landmark

**Implementation strategies:**

| Strategy | Pros | Cons |
|---|---|---|
| **Focus main heading** | Natural reading flow; works with all SRs | May scroll page; heading must exist |
| **Live region announcement** | Non-disruptive; works with any layout | SR may not announce in all contexts |
| **Both** (recommended) | Covers all edge cases | Slightly more code |

```jsx
// RouteAnnouncer.jsx — works with React Router v6
import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';

// Route-to-title mapping
const routeTitles = {
  '/': 'Home',
  '/products': 'Products',
  '/about': 'About Us',
  '/contact': 'Contact',
  '/dashboard': 'Dashboard',
};

function RouteAnnouncer() {
  const location = useLocation();
  const [announcement, setAnnouncement] = useState('');
  const headingRef = useRef(null);

  useEffect(() => {
    // 1. Update the document title
    const title = routeTitles[location.pathname] || 'Page';
    document.title = `${title} | My App`;

    // 2. Announce the route change via live region
    setAnnouncement(`Navigated to ${title}`);

    // 3. Move focus to the main heading (h1)
    // Use requestAnimationFrame to wait for the new route to render
    requestAnimationFrame(() => {
      const h1 = document.querySelector('h1');
      if (h1) {
        // Set tabIndex if not already focusable
        if (!h1.hasAttribute('tabindex')) {
          h1.setAttribute('tabindex', '-1');
        }
        h1.focus({ preventScroll: false });
      }
    });

    // 4. Scroll to top (sighted user expectation)
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div
      role="status"
      aria-live="assertive"
      aria-atomic="true"
      className="sr-only"
      style={{
        position: 'absolute',
        width: '1px',
        height: '1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        border: 0,
      }}
    >
      {announcement}
    </div>
  );
}

// App.jsx — integration
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <RouteAnnouncer />
      <SkipNav />
      <header>
        <nav aria-label="Main navigation">
          <a href="/" aria-current={location.pathname === '/' ? 'page' : undefined}>
            Home
          </a>
          <a href="/products" aria-current={location.pathname === '/products' ? 'page' : undefined}>
            Products
          </a>
          <a href="/about" aria-current={location.pathname === '/about' ? 'page' : undefined}>
            About
          </a>
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

// Each page component should have an h1
function ProductsPage() {
  return (
    <section>
      <h1>Products</h1> {/* RouteAnnouncer will focus this */}
      <p>Browse our catalog.</p>
    </section>
  );
}
```

---

### Q16. How do you implement reduced motion preferences using `prefers-reduced-motion` in React?

**Answer:**

Some users experience vestibular disorders, motion sickness, or seizures triggered by animations and motion effects. The `prefers-reduced-motion` media query allows users to indicate via their OS settings that they prefer minimal motion. WCAG 2.3.3 (Level AAA) and the broader 2.3.1 (Level A — no content flashes more than 3 times per second) address this.

**Who is affected?**

- People with vestibular disorders (motion sickness, vertigo) — estimated 35% of adults over 40
- People with epilepsy (photosensitive seizures)
- People with ADHD or cognitive disabilities who find animations distracting

**Implementation levels:**

1. **CSS** — use `@media (prefers-reduced-motion: reduce)` to disable/reduce animations
2. **React hook** — use `matchMedia` to conditionally render animation logic
3. **Animation libraries** — pass the preference to Framer Motion, React Spring, etc.

```jsx
import { useState, useEffect, useCallback } from 'react';

// Custom hook to detect reduced motion preference
function usePrefersReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    // SSR-safe: default to true (safer — no motion) if window is unavailable
    if (typeof window === 'undefined') return true;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handler = (event) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReducedMotion;
}

// Example 1: Conditionally animate a notification toast
function Toast({ message, onDismiss }) {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className="toast"
      role="status"
      aria-live="polite"
      style={{
        // Instant appearance vs. slide-in animation
        animation: prefersReducedMotion
          ? 'none'
          : 'slideInFromRight 0.3s ease-out',
      }}
    >
      <p>{message}</p>
      <button onClick={onDismiss} aria-label="Dismiss notification">
        ✕
      </button>
    </div>
  );
}

// Example 2: Hero animation that degrades gracefully
function HeroSection() {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <section className="hero">
      {prefersReducedMotion ? (
        // Static image for reduced motion
        <img
          src="/hero-static.jpg"
          alt="Products displayed on a modern desk"
        />
      ) : (
        // Animated background for full motion
        <video
          autoPlay
          muted
          loop
          playsInline
          aria-label="Products displayed on a modern desk"
        >
          <source src="/hero-video.mp4" type="video/mp4" />
        </video>
      )}
      <h1>Welcome to Our Store</h1>
    </section>
  );
}

// Example 3: Integration with Framer Motion
import { motion, AnimatePresence } from 'framer-motion';

function AnimatedList({ items }) {
  const prefersReducedMotion = usePrefersReducedMotion();

  const variants = prefersReducedMotion
    ? {
        // Instant: no motion, just opacity
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
      }
    : {
        // Full animation: slide + fade
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, x: -100 },
      };

  return (
    <ul>
      <AnimatePresence>
        {items.map((item) => (
          <motion.li
            key={item.id}
            variants={variants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.3 }}
          >
            {item.name}
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
```

CSS-level safeguard (should always be in your global stylesheet):

```jsx
/* Global reduced motion safeguard */
/*
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
*/
```

---

### Q17. How do you implement accessible drag-and-drop in React?

**Answer:**

Drag-and-drop is one of the most challenging patterns to make accessible. The HTML Drag and Drop API is inherently inaccessible — it relies entirely on mouse events and provides no keyboard or screen reader support. An accessible implementation must provide:

1. **Keyboard alternative** — select an item, then move it with arrow keys (or a "Move" action menu)
2. **Screen reader announcements** — announce when an item is grabbed, its position as it moves, and when it's dropped
3. **Visual + non-visual feedback** — both sighted and non-sighted users need to understand what's happening
4. **ARIA roles** — items should communicate their draggable state and current position

```jsx
import { useState, useCallback, useRef } from 'react';

function AccessibleDragDropList({ items: initialItems, onReorder }) {
  const [items, setItems] = useState(initialItems);
  const [grabbedIndex, setGrabbedIndex] = useState(null);
  const [announcement, setAnnouncement] = useState('');
  const listRef = useRef(null);

  const isGrabbed = grabbedIndex !== null;

  // Keyboard-driven reordering
  const handleKeyDown = useCallback(
    (e, index) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();

        if (!isGrabbed) {
          // Pick up the item
          setGrabbedIndex(index);
          setAnnouncement(
            `Grabbed "${items[index].label}". ` +
            `Position ${index + 1} of ${items.length}. ` +
            `Use arrow keys to move, Space or Enter to drop, Escape to cancel.`
          );
        } else {
          // Drop the item
          setGrabbedIndex(null);
          setAnnouncement(
            `Dropped "${items[index].label}" at position ${index + 1} of ${items.length}.`
          );
          onReorder?.(items);
        }
      }

      if (isGrabbed && e.key === 'Escape') {
        e.preventDefault();
        // Cancel: restore original order
        setItems(initialItems);
        setGrabbedIndex(null);
        setAnnouncement(
          `Reorder cancelled. "${items[grabbedIndex].label}" returned to original position.`
        );
      }

      if (isGrabbed && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        e.preventDefault();
        const newIndex = e.key === 'ArrowUp'
          ? Math.max(0, grabbedIndex - 1)
          : Math.min(items.length - 1, grabbedIndex + 1);

        if (newIndex !== grabbedIndex) {
          const newItems = [...items];
          const [movedItem] = newItems.splice(grabbedIndex, 1);
          newItems.splice(newIndex, 0, movedItem);
          setItems(newItems);
          setGrabbedIndex(newIndex);

          setAnnouncement(
            `"${movedItem.label}" moved to position ${newIndex + 1} of ${items.length}.`
          );

          // Keep focus on the moved item
          requestAnimationFrame(() => {
            const listItems = listRef.current?.querySelectorAll('[role="option"]');
            listItems?.[newIndex]?.focus();
          });
        }
      }
    },
    [isGrabbed, grabbedIndex, items, initialItems, onReorder]
  );

  return (
    <div>
      <h2 id="dnd-label">Reorder Tasks</h2>
      <p id="dnd-instructions" className="sr-only">
        Use Space or Enter to grab an item, arrow keys to move it,
        Space or Enter to drop, Escape to cancel.
      </p>

      {/* Live region for screen reader announcements */}
      <div
        role="status"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      >
        {announcement}
      </div>

      <ul
        ref={listRef}
        role="listbox"
        aria-labelledby="dnd-label"
        aria-describedby="dnd-instructions"
        className="dnd-list"
      >
        {items.map((item, index) => (
          <li
            key={item.id}
            role="option"
            aria-selected={grabbedIndex === index}
            aria-roledescription="sortable item"
            aria-label={`${item.label}, position ${index + 1} of ${items.length}`}
            tabIndex={0}
            className={`dnd-item ${grabbedIndex === index ? 'dnd-item--grabbed' : ''}`}
            onKeyDown={(e) => handleKeyDown(e, index)}
          >
            <span className="dnd-handle" aria-hidden="true">⠿</span>
            <span>{item.label}</span>
            <span className="sr-only">
              {grabbedIndex === index ? ', grabbed' : ''}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// Usage
function TaskBoard() {
  const tasks = [
    { id: '1', label: 'Review pull request' },
    { id: '2', label: 'Write unit tests' },
    { id: '3', label: 'Update documentation' },
    { id: '4', label: 'Fix production bug' },
    { id: '5', label: 'Deploy to staging' },
  ];

  const handleReorder = (newOrder) => {
    console.log('New task order:', newOrder.map((t) => t.label));
    // Persist to API...
  };

  return (
    <AccessibleDragDropList
      items={tasks}
      onReorder={handleReorder}
    />
  );
}
```

**Production tip:** For complex drag-and-drop (multi-container Kanban boards, sortable grids), use the **`@dnd-kit`** library, which was built with accessibility as a first-class concern. It provides live region announcements, keyboard sensors, and screen reader instructions out of the box.

---

### Q18. How do you set up an automated accessibility testing pipeline in CI/CD?

**Answer:**

An accessibility CI/CD pipeline ensures that a11y regressions are caught **before** they reach production. The key is layering multiple tools at different stages of the pipeline:

**Pipeline stages:**

| Stage | Tool | What It Catches | Speed |
|---|---|---|---|
| **Pre-commit / Lint** | `eslint-plugin-jsx-a11y` | Missing alt text, bad ARIA, non-interactive handlers on divs | Instant |
| **Unit Tests** | `jest-axe` | Component-level WCAG violations in rendered HTML | Fast |
| **E2E Tests** | `@axe-core/playwright` or `cypress-axe` | Full page violations with real browser rendering | Medium |
| **PR Check** | Lighthouse CI | Page-level a11y score threshold | Slow |
| **Monitoring** | `axe-core` in production (sampling) | Real-world violations with real data | Ongoing |

```jsx
// 1. ESLint configuration — catches issues at development time
// .eslintrc.js
/*
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:jsx-a11y/strict', // Use 'strict' mode for maximum coverage
  ],
  plugins: ['jsx-a11y'],
  rules: {
    'jsx-a11y/anchor-is-valid': 'error',
    'jsx-a11y/aria-props': 'error',
    'jsx-a11y/aria-proptypes': 'error',
    'jsx-a11y/aria-unsupported-elements': 'error',
    'jsx-a11y/role-has-required-aria-props': 'error',
    'jsx-a11y/role-supports-aria-props': 'error',
    'jsx-a11y/no-redundant-roles': 'error',
  },
};
*/

// 2. jest-axe test helper — reusable across all component tests
// test-utils/a11y.js
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

export async function expectNoA11yViolations(container) {
  const results = await axe(container, {
    rules: {
      // Customize rules if needed
      region: { enabled: true }, // All content must be in landmarks
    },
  });

  // Custom error formatting for CI readability
  if (results.violations.length > 0) {
    const violations = results.violations
      .map(
        (v) =>
          `[${v.impact}] ${v.id}: ${v.description}\n` +
          `  Help: ${v.helpUrl}\n` +
          `  Affected:\n${v.nodes.map((n) => `    - ${n.html}`).join('\n')}`
      )
      .join('\n\n');

    throw new Error(`Accessibility violations:\n\n${violations}`);
  }
}

// Usage in tests:
// import { expectNoA11yViolations } from '../test-utils/a11y';
// it('has no a11y violations', async () => {
//   const { container } = render(<MyComponent />);
//   await expectNoA11yViolations(container);
// });

// 3. Playwright E2E accessibility test suite
// e2e/a11y-audit.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const CRITICAL_PAGES = [
  { path: '/', name: 'Home' },
  { path: '/products', name: 'Products' },
  { path: '/checkout', name: 'Checkout' },
  { path: '/login', name: 'Login' },
  { path: '/dashboard', name: 'Dashboard' },
];

for (const page of CRITICAL_PAGES) {
  test(`${page.name} page should pass WCAG 2.1 AA`, async ({ page: pwPage }) => {
    await pwPage.goto(page.path);
    await pwPage.waitForLoadState('networkidle');

    const results = await new AxeBuilder({ page: pwPage })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    // Log violations for CI output
    if (results.violations.length > 0) {
      console.error(
        `A11y violations on ${page.name}:`,
        JSON.stringify(results.violations, null, 2)
      );
    }

    expect(results.violations).toEqual([]);
  });
}

// 4. GitHub Actions workflow
// .github/workflows/a11y.yml
/*
name: Accessibility CI

on:
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npx eslint --ext .jsx,.tsx src/ --rule 'jsx-a11y/alt-text: error'

  unit-a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npx jest --testPathPattern='a11y|accessibility'

  e2e-a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npm run start &
      - run: npx wait-on http://localhost:3000
      - run: npx playwright test e2e/a11y-audit.spec.ts

  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci && npm run build
      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v11
        with:
          urls: |
            http://localhost:3000/
            http://localhost:3000/products
          budgetPath: ./lighthouserc.json
          uploadArtifacts: true
*/

// 5. lighthouserc.json — fail PR if a11y score drops below threshold
/*
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["warn", { "minScore": 0.8 }]
      }
    }
  }
}
*/
```

---

### Q19. How do accessibility-focused component libraries like Radix UI and Headless UI work, and when should you use them?

**Answer:**

Building truly accessible interactive components from scratch is *extremely* difficult. A custom dropdown, dialog, combobox, or tabs component needs to handle: ARIA roles and states, keyboard interactions (arrow keys, Home/End, Escape, Enter), focus management, screen reader announcements, and edge cases across different browser/AT combinations. **Accessibility-focused component libraries** solve this by providing **unstyled, headless primitives** that handle all the behavior and ARIA semantics while leaving the visual design entirely to you.

**Key libraries:**

| Library | Style Approach | Framework | Key Strength |
|---|---|---|---|
| **Radix UI** | Unstyled (bring your own CSS) | React | Compositional API, animation support |
| **Headless UI** | Unstyled (built for Tailwind) | React, Vue | Tight Tailwind integration |
| **React Aria** (Adobe) | Hooks-based (lowest level) | React | Maximum flexibility, SSR support |
| **Reach UI** | Minimally styled | React | Precursor to Remix; simple API |
| **Ark UI** | Unstyled (state machines) | React, Vue, Solid | Cross-framework, Zag.js powered |

**Why use them over building your own?**

1. Hundreds of hours of accessibility work already done
2. Tested across screen readers (NVDA, JAWS, VoiceOver, TalkBack)
3. WAI-ARIA Authoring Practices compliance
4. Handles edge cases you won't think of (iOS VoiceOver quirks, JAWS virtual cursor behavior)

```jsx
// Example 1: Radix UI — Accessible Dialog (Modal)
import * as Dialog from '@radix-ui/react-dialog';

function ConfirmDeleteDialog({ onConfirm }) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="btn btn-danger">Delete Account</button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          {/* Radix handles: focus trap, Escape to close, focus restoration,
              aria-modal, role="dialog", aria-labelledby, aria-describedby */}
          <Dialog.Title className="dialog-title">
            Are you sure?
          </Dialog.Title>
          <Dialog.Description className="dialog-description">
            This will permanently delete your account and all associated data.
            This action cannot be undone.
          </Dialog.Description>

          <div className="dialog-actions">
            <Dialog.Close asChild>
              <button className="btn">Cancel</button>
            </Dialog.Close>
            <button className="btn btn-danger" onClick={onConfirm}>
              Yes, delete my account
            </button>
          </div>

          <Dialog.Close asChild>
            <button className="dialog-close-btn" aria-label="Close">
              ✕
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// Example 2: Headless UI — Accessible Listbox (Select)
import { Listbox, Transition } from '@headlessui/react';
import { useState, Fragment } from 'react';

const statuses = [
  { id: 1, name: 'Active', color: 'green' },
  { id: 2, name: 'Inactive', color: 'gray' },
  { id: 3, name: 'Pending', color: 'yellow' },
  { id: 4, name: 'Suspended', color: 'red' },
];

function StatusSelect() {
  const [selected, setSelected] = useState(statuses[0]);

  return (
    <Listbox value={selected} onChange={setSelected}>
      {/* Headless UI handles: aria-expanded, aria-activedescendant,
          keyboard navigation (arrows, Home, End, type-ahead),
          role="listbox", role="option", aria-selected */}
      <Listbox.Label className="label">Account Status</Listbox.Label>

      <div className="listbox-wrapper">
        <Listbox.Button className="listbox-button">
          <span className={`status-dot status-${selected.color}`} />
          {selected.name}
        </Listbox.Button>

        <Transition
          as={Fragment}
          leave="transition-leave"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="listbox-options">
            {statuses.map((status) => (
              <Listbox.Option
                key={status.id}
                value={status}
                className={({ active, selected }) =>
                  `listbox-option ${active ? 'active' : ''} ${selected ? 'selected' : ''}`
                }
              >
                {({ selected }) => (
                  <>
                    <span className={`status-dot status-${status.color}`} />
                    <span className={selected ? 'font-bold' : ''}>
                      {status.name}
                    </span>
                    {selected && <span aria-hidden="true">✓</span>}
                  </>
                )}
              </Listbox.Option>
            ))}
          </Listbox.Options>
        </Transition>
      </div>
    </Listbox>
  );
}

// Example 3: React Aria — Hooks for maximum control
import { useButton, useFocusRing } from 'react-aria';
import { useRef } from 'react';

function AriaButton(props) {
  const ref = useRef(null);
  // useButton handles: keyboard activation, press events, disabled state,
  // ARIA attributes, and press event normalization across devices
  const { buttonProps } = useButton(props, ref);
  // useFocusRing provides a visible focus indicator only for keyboard users
  const { isFocusVisible, focusProps } = useFocusRing();

  return (
    <button
      {...buttonProps}
      {...focusProps}
      ref={ref}
      className={`btn ${isFocusVisible ? 'btn--focus-ring' : ''}`}
    >
      {props.children}
    </button>
  );
}
```

**When to use headless libraries vs. building your own:**

- **Use headless libraries** for: dialogs, dropdowns, comboboxes, tabs, accordions, popovers, menus, sliders — any WAI-ARIA design pattern.
- **Build your own** for: simple buttons, links, forms (native HTML is sufficient), or highly custom interactions that no library covers.

---

### Q20. How would you audit and remediate an existing React application to achieve WCAG 2.1 AA compliance?

**Answer:**

Making an existing production app WCAG 2.1 AA compliant is a structured, multi-phase effort — not a one-time task. Here is a production-tested audit and remediation framework:

**Phase 1: Automated Discovery (Week 1)**

Run automated scans to find the low-hanging fruit (30–40% of issues):

```jsx
// audit-script.js — Run axe-core against all critical pages
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'fs';

const PAGES = [
  '/', '/login', '/signup', '/dashboard', '/products',
  '/products/1', '/checkout', '/settings', '/help',
];

async function runAudit() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const allResults = {};

  for (const path of PAGES) {
    const page = await context.newPage();
    await page.goto(`http://localhost:3000${path}`);
    await page.waitForLoadState('networkidle');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    allResults[path] = {
      violations: results.violations.length,
      critical: results.violations.filter((v) => v.impact === 'critical'),
      serious: results.violations.filter((v) => v.impact === 'serious'),
      moderate: results.violations.filter((v) => v.impact === 'moderate'),
      minor: results.violations.filter((v) => v.impact === 'minor'),
      details: results.violations,
    };

    await page.close();
  }

  // Generate report
  const report = Object.entries(allResults).map(([path, data]) => ({
    page: path,
    total: data.violations,
    critical: data.critical.length,
    serious: data.serious.length,
    moderate: data.moderate.length,
    minor: data.minor.length,
    topIssues: data.details.slice(0, 5).map((v) => `${v.id}: ${v.description}`),
  }));

  fs.writeFileSync(
    'a11y-audit-report.json',
    JSON.stringify(report, null, 2)
  );

  console.table(report.map(({ page, total, critical, serious }) => ({
    page, total, critical, serious,
  })));

  await browser.close();
}

runAudit();
```

**Phase 2: Manual Audit (Weeks 2–3)**

Automated tools miss ~60% of issues. Conduct manual testing:

```jsx
// Manual audit checklist — build into your testing process

const MANUAL_AUDIT_CHECKLIST = {
  keyboard: [
    'Can you tab to every interactive element?',
    'Can you see where focus is at all times (visible focus indicator)?',
    'Can you operate every control with keyboard only (Enter, Space, Escape, Arrow keys)?',
    'Can you escape from modals and popups?',
    'Does tab order follow a logical reading sequence?',
    'Are there any keyboard traps (focus cannot leave a component)?',
  ],
  screenReader: [
    'Does every image have meaningful alt text (or alt="" for decorative)?',
    'Are headings used in proper hierarchy (h1 → h2 → h3)?',
    'Do all form inputs have accessible labels?',
    'Are error messages announced when they appear?',
    'Do modal dialogs announce their title when opened?',
    'Are dynamic content changes announced (notifications, loading states)?',
    'Do data tables have proper headers and captions?',
    'Are route changes announced in the SPA?',
  ],
  visual: [
    'Does all text meet 4.5:1 contrast ratio (or 3:1 for large text)?',
    'Is information conveyed by more than just color?',
    'Does the page work at 200% zoom?',
    'Does the layout work on a 320px wide viewport (reflow)?',
    'Are focus indicators visible against all backgrounds?',
    'Does the site respect prefers-reduced-motion?',
  ],
  content: [
    'Do all pages have unique, descriptive <title> elements?',
    'Is the language of the page set (<html lang="en">)?',
    'Are link texts descriptive (no "click here")?',
    'Are error messages clear and actionable?',
    'Is there a skip navigation link?',
  ],
};
```

**Phase 3: Remediation (Weeks 3–8)**

Prioritize fixes by impact and frequency:

```jsx
// Common remediation patterns for React apps

// 1. Fix: Missing accessible names on icon buttons
// Before:
<button onClick={onDelete}><TrashIcon /></button>

// After:
<button onClick={onDelete} aria-label="Delete item">
  <TrashIcon aria-hidden="true" />
</button>

// 2. Fix: Custom components that should be native elements
// Before:
<div className="link" onClick={() => navigate('/about')}>About</div>

// After:
<a href="/about">About</a>

// 3. Fix: Images without alt text
// Before:
<img src={product.image} />

// After — meaningful:
<img src={product.image} alt={`${product.name} — ${product.color} variant`} />

// After — decorative:
<img src="/divider.svg" alt="" role="presentation" />

// 4. Fix: Add a skip navigation link (see Q7)

// 5. Fix: Add route change announcements (see Q15)

// 6. Fix: Global styles for focus visibility
/*
  // Reset: NEVER globally remove outlines
  // Instead, use :focus-visible for keyboard-only indicators

  :focus-visible {
    outline: 3px solid #2563eb;
    outline-offset: 2px;
  }

  // Only remove default outline if you've added a custom one:
  :focus:not(:focus-visible) {
    outline: none;
  }
*/

// 7. Fix: Create an accessible ErrorBoundary that announces errors
class AccessibleErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" aria-live="assertive">
          <h2>Something went wrong</h2>
          <p>
            We encountered an unexpected error. Please try refreshing the page
            or <a href="/support">contact support</a>.
          </p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

**Phase 4: Prevention (Ongoing)**

```jsx
// Prevent regressions with automated gates

// 1. Add a11y tests to every new component (template)
/*
  // __tests__/NewComponent.test.jsx — template for all new components
  import { render } from '@testing-library/react';
  import { axe, toHaveNoViolations } from 'jest-axe';
  import NewComponent from '../NewComponent';

  expect.extend(toHaveNoViolations);

  describe('NewComponent', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<NewComponent />);
      expect(await axe(container)).toHaveNoViolations();
    });
  });
*/

// 2. PR template with a11y checklist
/*
  ## Accessibility Checklist
  - [ ] New/modified components have jest-axe tests
  - [ ] Interactive elements are keyboard accessible
  - [ ] Images have meaningful alt text
  - [ ] Form inputs have associated labels
  - [ ] Color is not the sole means of conveying information
  - [ ] Dynamic content changes are announced to screen readers
  - [ ] Tested with keyboard navigation
  - [ ] Tested with VoiceOver/NVDA (for significant UI changes)
*/

// 3. Storybook a11y addon for design-time testing
/*
  // .storybook/main.js
  module.exports = {
    addons: ['@storybook/addon-a11y'],
  };

  // Stories automatically show a11y violations panel
  // with axe-core results for every component state
*/

// 4. Production monitoring — sample real user sessions
function useA11yMonitor() {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') return;
    if (Math.random() > 0.01) return; // 1% sampling

    import('axe-core').then((axe) => {
      axe.run(document, {
        runOnly: ['wcag2a', 'wcag2aa'],
      }).then((results) => {
        if (results.violations.length > 0) {
          // Send to your monitoring service
          fetch('/api/a11y-violations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              url: window.location.href,
              timestamp: new Date().toISOString(),
              violations: results.violations.map((v) => ({
                id: v.id,
                impact: v.impact,
                description: v.description,
                nodes: v.nodes.length,
              })),
            }),
          });
        }
      });
    });
  }, []);
}
```

**WCAG 2.1 AA Compliance Summary — the 25 success criteria most React apps fail:**

| # | WCAG Criterion | Common React Failure |
|---|---|---|
| 1.1.1 | Non-text Content | Missing alt text on `<img>` |
| 1.3.1 | Info and Relationships | Using `<div>` instead of semantic HTML |
| 1.4.3 | Contrast (Minimum) | Text below 4.5:1 contrast |
| 1.4.11 | Non-text Contrast | Focus indicators below 3:1 |
| 2.1.1 | Keyboard | `onClick` on `<div>` without keyboard handler |
| 2.1.2 | No Keyboard Trap | Modal without Escape key handling |
| 2.4.1 | Bypass Blocks | No skip navigation link |
| 2.4.2 | Page Titled | SPA doesn't update `document.title` |
| 2.4.3 | Focus Order | CSS `order` / `flex-direction` breaking tab order |
| 2.4.7 | Focus Visible | `outline: none` in global CSS |
| 4.1.2 | Name, Role, Value | Custom components without ARIA |

---

*End of Accessibility (a11y) in React 18 Interview Questions*
