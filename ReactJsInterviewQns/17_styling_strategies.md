# Styling Strategies in React 18 — Interview Questions

## Topic Introduction

**Styling in React** is a rich and sometimes contentious topic because the framework deliberately does not prescribe a single approach. Unlike Angular (which ships with built-in component-scoped styles) or Svelte (which scopes `<style>` blocks automatically), React gives you the freedom — and the burden — of choosing from a wide spectrum of strategies: plain CSS files, CSS Modules, utility-first frameworks like Tailwind CSS, CSS-in-JS libraries (styled-components, Emotion, Stitches), zero-runtime solutions (vanilla-extract, Panda CSS, Linaria), and hybrids. Each approach makes different tradeoffs across **developer experience**, **runtime performance**, **bundle size**, **server-side rendering compatibility**, and **design-system scalability**. In React 18, with concurrent rendering, streaming SSR (`renderToPipeableStream`), and Server Components becoming mainstream, these tradeoffs have sharpened — runtime CSS-in-JS libraries, for example, can interfere with streaming because they need to collect styles synchronously during render, while zero-runtime or build-time solutions work seamlessly.

At the **component level**, React's `className` prop maps directly to the DOM `class` attribute, and its `style` prop accepts a JavaScript object with camelCased properties. This simplicity is deceptive: production applications need scoping to prevent class collisions, theming for dark/light modes and brand consistency, responsive design for a matrix of screen sizes, animation orchestration, and a strategy for critical CSS extraction during SSR. The modern React ecosystem answers these needs through a combination of tooling (PostCSS, Vite plugins, bundler integrations), patterns (design tokens stored as CSS custom properties, variant-driven APIs via `cva`), and libraries that range from zero-config (Tailwind) to highly customizable (Emotion with a custom cache and `CacheProvider`).

Understanding when and why to choose one strategy over another is a hallmark of senior-level React engineering. Interviewers at top companies expect candidates to discuss not just "how to make a button red" but the downstream effects on **bundle size budgets**, **hydration mismatches**, **streaming SSR compatibility**, **team collaboration** (can designers contribute? can junior devs use it consistently?), and **long-term maintenance**. The questions below span these dimensions from beginner fundamentals to advanced architectural decisions.

```jsx
// A quick taste — three ways to style the same component in React 18

// 1. CSS Modules
import styles from './Button.module.css';

// 2. Tailwind CSS
function TailwindButton({ children }) {
  return (
    <button className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition-colors">
      {children}
    </button>
  );
}

// 3. styled-components (CSS-in-JS)
import styled from 'styled-components';

const StyledButton = styled.button`
  border-radius: 0.5rem;
  background-color: #2563eb;
  padding: 0.5rem 1rem;
  color: white;
  transition: background-color 150ms;
  &:hover {
    background-color: #1d4ed8;
  }
`;

// 4. Inline style (limited, but sometimes correct)
function InlineButton({ children }) {
  return (
    <button style={{ borderRadius: '0.5rem', backgroundColor: '#2563eb', padding: '0.5rem 1rem', color: 'white' }}>
      {children}
    </button>
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. How do inline styles work in React, and when are they an appropriate choice?

**Answer:**

In React, the `style` prop accepts a **JavaScript object** where property names are camelCased versions of CSS properties and values are strings (or numbers for unitless properties like `zIndex`, `opacity`, `flexGrow`). React serializes this object to an inline `style` attribute on the DOM element.

**When inline styles are appropriate:**

1. **Truly dynamic values** computed at render time — e.g., positioning a tooltip at `{ top: cursorY, left: cursorX }`, or setting a progress bar's `width` based on a percentage.
2. **Animation interpolations** — libraries like `react-spring` and Framer Motion apply animated values as inline styles for performance (they bypass CSS parsing and go straight to the CSSOM).
3. **One-off overrides** in prototyping or when the style depends entirely on props/state and adding a class would be more verbose.

**Limitations of inline styles:**

- **No pseudo-classes or pseudo-elements** — you cannot write `:hover`, `:focus`, `::before`, or `::after` in an inline style object.
- **No media queries** — responsive design is impossible with inline styles alone.
- **No keyframe animations** — `@keyframes` rules cannot be defined inline.
- **No cascading or specificity control** — every inline style has high specificity, making overrides awkward.
- **Performance concerns** — React creates a new object reference every render (unless memoized), and the browser must parse and apply inline styles per-element rather than sharing cached CSS rules.

```jsx
// ✅ Good use — dynamic positioning
function Tooltip({ x, y, children }) {
  return (
    <div
      style={{
        position: 'fixed',
        top: y,
        left: x,
        backgroundColor: '#1e293b',
        color: 'white',
        padding: '6px 12px',
        borderRadius: 6,       // unitless → treated as px by React
        pointerEvents: 'none',
        zIndex: 9999,
      }}
    >
      {children}
    </div>
  );
}

// ❌ Bad use — static button styling (no hover, no responsive)
function BadButton({ children }) {
  return (
    <button
      style={{
        backgroundColor: 'blue',
        color: 'white',
        padding: '8px 16px',
        // Can't do :hover, :focus, media queries, etc.
      }}
    >
      {children}
    </button>
  );
}
```

**Key takeaway:** Use inline styles only for values that are **truly dynamic at runtime**. For everything else, prefer CSS Modules, Tailwind, or CSS-in-JS.

---

### Q2. What are CSS Modules and how do they scope styles to a component?

**Answer:**

**CSS Modules** are regular CSS files (typically named `*.module.css`) that are processed by the bundler (Vite, webpack, etc.) so that every class name is **locally scoped by default**. When you import a CSS Module, you get a JavaScript object whose keys are the class names you authored and whose values are the auto-generated, unique class names emitted in the final CSS bundle.

**How scoping works under the hood:**

1. You write `.button { color: red; }` in `Button.module.css`.
2. The bundler transforms it to something like `._button_x7k2q_1 { color: red; }`.
3. The import `styles` maps `button` → `_button_x7k2q_1`.
4. You use `className={styles.button}`, which renders `class="_button_x7k2q_1"` in the DOM.

This means two different components can both have a `.button` class in their respective module files without any collision.

**Advantages:**

- Zero runtime cost — everything is resolved at build time, output is plain CSS.
- Full access to standard CSS features (pseudo-classes, media queries, animations).
- Excellent SSR compatibility — no hydration mismatch concerns.
- TypeScript support via `typed-css-modules` or bundler plugins for auto-generated `.d.ts` files.

```jsx
/* Button.module.css */
/*
.button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  background-color: #2563eb;
  color: white;
  cursor: pointer;
  transition: background-color 150ms ease;
}

.button:hover {
  background-color: #1d4ed8;
}

.button:focus-visible {
  outline: 2px solid #60a5fa;
  outline-offset: 2px;
}

.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
*/

// Button.jsx
import styles from './Button.module.css';

function Button({ children, disabled, onClick }) {
  // Combine classes conditionally
  const className = disabled
    ? `${styles.button} ${styles.disabled}`
    : styles.button;

  return (
    <button className={className} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
}

export default Button;
```

CSS Modules are one of the most popular choices in production because they offer the best balance of simplicity, performance, and full CSS capability with zero runtime overhead.

---

### Q3. What is the difference between global CSS and scoped CSS in React, and what are the tradeoffs?

**Answer:**

**Global CSS** is a traditional `.css` file imported without the `.module.css` convention. Every class, element, and ID selector in that file is globally available throughout the application. **Scoped CSS** (via CSS Modules, CSS-in-JS, or Tailwind's utility classes) limits style influence to the component or scope that applies it.

| Aspect | Global CSS | Scoped CSS (CSS Modules / CSS-in-JS) |
|---|---|---|
| **Name collisions** | High risk — any component can accidentally override another's `.card` class | Eliminated — names are locally scoped or auto-generated |
| **Dead code elimination** | Hard — difficult to know if a class is still used | Easier — bundlers can tree-shake unused module exports |
| **Onboarding** | Familiar to all developers | Slight learning curve for CSS Modules or library APIs |
| **Theming** | Easy with CSS custom properties | Same, or enhanced via context-based theme providers |
| **Debugging** | Simple selectors in DevTools | Auto-generated class names can be cryptic (mitigated by `generateScopedName` config) |
| **Performance** | Single cached stylesheet | Same for CSS Modules; runtime cost for some CSS-in-JS |
| **Reusability** | Copy-paste selectors | Import and compose explicitly |

**When global CSS makes sense:**

- CSS resets / normalize (`reset.css`, `normalize.css`).
- Base typography and root-level custom properties (`:root { --color-primary: ... }`).
- Third-party library styles that must be global (e.g., a date-picker's default theme).

**When scoped CSS is preferred:**

- Component-level styles in any application with more than a handful of components.
- Design system libraries that must not leak styles into consumer applications.
- Large teams where naming convention discipline (BEM, OOCSS) cannot be reliably enforced.

```jsx
// ❌ Global CSS — prone to collision
// styles.css
// .card { padding: 16px; border: 1px solid #e2e8f0; }

// Any component importing this (or not!) inherits the global .card class
import './styles.css';

function ProductCard() {
  return <div className="card">Product</div>; // ← collides with any other .card
}

// ✅ Scoped CSS — CSS Modules
// ProductCard.module.css
// .card { padding: 16px; border: 1px solid #e2e8f0; }

import styles from './ProductCard.module.css';

function ProductCard() {
  return <div className={styles.card}>Product</div>; // ← unique hash, no collision
}
```

**Best practice:** Use global CSS only for resets, custom properties, and base element styles. Scope everything else.

---

### Q4. How does Tailwind CSS work with React, and what is the utility-first approach?

**Answer:**

**Tailwind CSS** is a utility-first CSS framework that provides a comprehensive set of small, single-purpose classes (e.g., `px-4`, `text-blue-600`, `rounded-lg`) that you compose directly in your JSX markup to build designs without writing custom CSS.

**How it works with React:**

1. Install Tailwind and configure it to scan your `.jsx`/`.tsx` files for class usage.
2. At build time, Tailwind's JIT (Just-In-Time) engine scans your source code, identifies which utility classes are used, and generates **only** those classes in the final CSS bundle.
3. You apply classes via the `className` prop just like regular CSS classes.

**Utility-first philosophy:**

Instead of writing semantic class names (`.primary-button`) and then defining their styles in a separate CSS file, you describe the *visual appearance* directly in the markup. This eliminates the indirection between markup and styles, reduces context switching, and produces highly predictable results.

**Advantages:**

- No naming — eliminates bikeshedding about `.btn-primary` vs `.button--primary`.
- Tiny production bundles — JIT ensures only used utilities ship.
- Consistency — spacing, colors, and typography are constrained to your `tailwind.config.js` design tokens.
- No runtime overhead — output is plain CSS.

**Common criticism and counters:**

- "Cluttered markup" → Extract repeated patterns into React components (the component *is* the abstraction).
- "Hard to read" → IDE extensions (Tailwind CSS IntelliSense) provide autocomplete and hover previews.

```jsx
// A production-quality card component using Tailwind CSS in React 18
function ProductCard({ title, price, imageUrl, onAddToCart }) {
  return (
    <article className="group relative overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      <div className="aspect-square overflow-hidden">
        <img
          src={imageUrl}
          alt={title}
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
      </div>
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h3>
        <p className="mt-1 text-xl font-bold text-blue-600 dark:text-blue-400">
          ${price.toFixed(2)}
        </p>
        <button
          onClick={onAddToCart}
          className="mt-3 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 active:bg-blue-800"
        >
          Add to Cart
        </button>
      </div>
    </article>
  );
}
```

Tailwind CSS has become one of the most popular styling choices in the React ecosystem due to its performance characteristics and rapid development velocity.

---

### Q5. What are CSS-in-JS libraries, and how do styled-components and Emotion work at a high level?

**Answer:**

**CSS-in-JS** is a paradigm where styles are authored in JavaScript (or TypeScript) co-located with component logic. Instead of separate `.css` files, you define styles as template literals or objects within your JS files. The library then generates actual CSS at **runtime** (or at build time for some solutions), injects it into the `<head>` via `<style>` tags, and gives your component the auto-generated class name.

**styled-components** and **Emotion** are the two most popular runtime CSS-in-JS libraries:

| Feature | styled-components | Emotion |
|---|---|---|
| API surface | `styled.div``...`` + `css` prop (via Babel plugin) | `styled` API (like sc) + `css` prop + `css()` function |
| Theme injection | `<ThemeProvider>` with `useTheme()` | Same, plus `useTheme()` hook |
| SSR support | `ServerStyleSheet` for collecting styles | `createEmotionServer` + `CacheProvider` |
| Bundle size | ~13 kB gzipped | ~7 kB gzipped (core) |
| Unique feature | `.attrs()` for default props, `createGlobalStyle` | Highly composable, `@emotion/react` vs `@emotion/styled` split |

**How they work at runtime:**

1. You define a styled component: `const Title = styled.h1`font-size: 2rem; color: ${props => props.color};``.
2. When `<Title color="red" />` renders, the library hashes the interpolated CSS string to generate a unique class name.
3. It injects a `<style>` rule (`.sc-abc123 { font-size: 2rem; color: red; }`) into the DOM.
4. The component renders `<h1 class="sc-abc123">`.

```jsx
// styled-components example
import styled from 'styled-components';

const Card = styled.article`
  padding: 1.5rem;
  border-radius: 1rem;
  background: ${({ theme }) => theme.colors.surface};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 200ms ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
`;

const Title = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text};
`;

const Price = styled.span`
  font-size: 1.5rem;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
`;

// Emotion equivalent using the css prop
/** @jsxImportSource @emotion/react */
import { css, useTheme } from '@emotion/react';

function ProductCard({ title, price }) {
  const theme = useTheme();

  return (
    <article
      css={css`
        padding: 1.5rem;
        border-radius: 1rem;
        background: ${theme.colors.surface};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
      `}
    >
      <h2 css={css`font-size: 1.25rem; color: ${theme.colors.text};`}>{title}</h2>
      <span css={css`font-size: 1.5rem; font-weight: 700; color: ${theme.colors.primary};`}>
        ${price}
      </span>
    </article>
  );
}
```

**Key consideration for React 18:** Runtime CSS-in-JS libraries execute style generation during render, which can conflict with concurrent features (streaming SSR, `useTransition`). This has led the community to increasingly favor build-time or zero-runtime alternatives.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you conditionally apply class names in React, and what role do libraries like `clsx` and `classnames` play?

**Answer:**

Conditional styling is one of the most common patterns in React. You frequently need to apply different classes based on component state, props, or context. While you can use template literals or manual string concatenation, this gets messy quickly — libraries like **`clsx`** (lightweight, ~228 bytes) and **`classnames`** (more established, ~300 bytes) provide a clean, declarative API.

**Manual approaches and their downsides:**

```jsx
// ❌ Template literal — hard to read with many conditions
<button className={`btn ${isPrimary ? 'btn-primary' : 'btn-secondary'} ${isLarge ? 'btn-lg' : ''} ${isDisabled ? 'btn-disabled' : ''}`}>

// ❌ Array join — undefined/false values leave extra spaces
<button className={[
  'btn',
  isPrimary && 'btn-primary',
  isLarge && 'btn-lg',
].filter(Boolean).join(' ')}>
```

**The `clsx` solution:**

`clsx` accepts strings, objects, and arrays, ignoring falsy values:

```jsx
import clsx from 'clsx';

function Button({ variant = 'primary', size = 'md', disabled, className, children }) {
  return (
    <button
      className={clsx(
        // Base styles always applied
        'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        // Variant styles — object syntax: key is class, value is condition
        {
          'bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-blue-600':
            variant === 'primary',
          'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:outline-gray-400':
            variant === 'secondary',
          'bg-red-600 text-white hover:bg-red-700 focus-visible:outline-red-600':
            variant === 'danger',
        },
        // Size styles
        {
          'px-3 py-1.5 text-sm': size === 'sm',
          'px-4 py-2 text-base': size === 'md',
          'px-6 py-3 text-lg': size === 'lg',
        },
        // Disabled state
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        // Allow consumer overrides
        className,
      )}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

// Usage
<Button variant="primary" size="lg">Submit</Button>
<Button variant="danger" disabled>Delete</Button>
<Button variant="secondary" className="mt-4">Cancel</Button>
```

**Why `clsx` over `classnames`:** `clsx` is a drop-in replacement that is smaller and faster. The API is identical for all common use cases. Most new projects prefer `clsx`.

**With CSS Modules:**

```jsx
import clsx from 'clsx';
import styles from './Alert.module.css';

function Alert({ type = 'info', children }) {
  return (
    <div className={clsx(styles.alert, styles[type])}>
      {children}
    </div>
  );
}
```

This pattern of `clsx` + CSS Modules (or `clsx` + Tailwind) is the dominant conditional styling approach in production React applications.

---

### Q7. How do you implement responsive design in React, and what approaches work best for different styling strategies?

**Answer:**

Responsive design in React can be handled at multiple levels depending on your styling strategy:

**1. CSS-level (recommended for most cases):**

The most performant approach is to let CSS handle responsiveness via **media queries** and **container queries**. CSS Modules, Tailwind, and CSS-in-JS all support these natively.

**2. JavaScript-level (for structural changes):**

Sometimes you need to render entirely different component trees — not just different styles — based on screen size. For this, you use a custom hook that listens to `window.matchMedia`.

**3. Container queries (modern approach):**

Container queries scope responsive behavior to the **container's** size rather than the viewport, making components truly portable.

```jsx
// APPROACH 1: Tailwind — responsive prefixes (mobile-first)
function Dashboard({ stats, chart }) {
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl bg-white p-4 shadow-sm md:p-6"
        >
          <p className="text-sm text-gray-500 md:text-base">{stat.label}</p>
          <p className="text-2xl font-bold md:text-3xl">{stat.value}</p>
        </div>
      ))}
      {/* Chart spans full width on mobile, 2 cols on md, 3 cols on lg */}
      <div className="col-span-1 md:col-span-2 lg:col-span-3">
        {chart}
      </div>
    </div>
  );
}

// APPROACH 2: CSS Modules with media queries
/* Sidebar.module.css */
/*
.sidebar {
  position: fixed;
  left: -280px;
  width: 280px;
  height: 100vh;
  transition: left 300ms ease;
}

.sidebar.open {
  left: 0;
}

@media (min-width: 1024px) {
  .sidebar {
    position: sticky;
    left: 0;
    top: 0;
  }
}
*/

// APPROACH 3: Container queries for portable components
/* Card.module.css */
/*
.wrapper {
  container-type: inline-size;
  container-name: card;
}

.card {
  display: flex;
  flex-direction: column;
}

@container card (min-width: 400px) {
  .card {
    flex-direction: row;
    align-items: center;
  }
}
*/

// APPROACH 4: JS-level for structural changes — useMediaQuery hook
import { useSyncExternalStore } from 'react';

function useMediaQuery(query) {
  const subscribe = (callback) => {
    const mql = window.matchMedia(query);
    mql.addEventListener('change', callback);
    return () => mql.removeEventListener('change', callback);
  };

  const getSnapshot = () => window.matchMedia(query).matches;

  // SSR fallback — assume mobile-first
  const getServerSnapshot = () => false;

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

// Usage — render different layouts
function Navigation() {
  const isDesktop = useMediaQuery('(min-width: 1024px)');

  return isDesktop ? <DesktopNav /> : <MobileNav />;
}
```

**Best practice:** Let CSS handle responsive *styling* (spacing, font sizes, grid columns). Use JavaScript only when you need to render entirely different *component structures*. The `useSyncExternalStore` approach shown above is React 18–idiomatic and safe for concurrent rendering.

---

### Q8. How do you implement theming with CSS custom properties and React Context?

**Answer:**

The most performant and widely compatible theming approach combines **CSS custom properties** (CSS variables) with a **React Context** that manages the active theme. CSS variables handle the visual switching (instant, no re-render needed), while Context provides the React-side API for toggling themes and persisting preferences.

**Why CSS custom properties over JS-based themes?**

- **Zero re-renders on theme switch** — changing a CSS variable on `:root` or a container instantly cascades to all elements using it, without React needing to re-render anything.
- **Works with any styling strategy** — CSS Modules, Tailwind, CSS-in-JS, and plain CSS can all reference `var(--color-primary)`.
- **SSR-friendly** — variables are in the stylesheet, not injected at runtime.

```jsx
// theme-tokens.css — define your design tokens as CSS custom properties
/*
:root,
[data-theme='light'] {
  --color-bg: #ffffff;
  --color-surface: #f8fafc;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-border: #e2e8f0;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --radius-lg: 0.75rem;
}

[data-theme='dark'] {
  --color-bg: #0f172a;
  --color-surface: #1e293b;
  --color-text: #f1f5f9;
  --color-text-muted: #94a3b8;
  --color-primary: #3b82f6;
  --color-primary-hover: #60a5fa;
  --color-border: #334155;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}
*/

// ThemeContext.jsx — React Context for theme management
import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ThemeContext = createContext(null);

function getInitialTheme() {
  if (typeof window === 'undefined') return 'light'; // SSR fallback

  const stored = localStorage.getItem('theme');
  if (stored === 'light' || stored === 'dark') return stored;

  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(getInitialTheme);

  // Apply theme to DOM and persist
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Listen for OS-level changes
  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => {
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

// ThemeToggle.jsx — component that uses the theme context
function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      style={{
        background: 'var(--color-surface)',
        color: 'var(--color-text)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: '0.5rem 1rem',
        cursor: 'pointer',
      }}
    >
      {theme === 'light' ? '🌙 Dark' : '☀️ Light'}
    </button>
  );
}
```

This pattern is used by major component libraries (Radix, shadcn/ui) and scales well from small apps to large design systems.

---

### Q9. What are the performance concerns with runtime CSS-in-JS libraries in React 18?

**Answer:**

Runtime CSS-in-JS libraries (styled-components, Emotion in its default runtime mode) generate and inject CSS **during the React render cycle**. In React 18's concurrent rendering model, this introduces several performance concerns:

**1. Style generation during render:**

Every time a styled component renders, the library must:
- Interpolate dynamic props into the template string.
- Hash the resulting CSS string to generate a unique class name.
- Check if that class already exists (deduplication).
- If new, inject a `<style>` rule into the DOM.

This work happens **synchronously during render**, blocking the main thread.

**2. Serialization cost:**

For server-side rendering, runtime CSS-in-JS libraries must collect all generated styles during render and serialize them into the HTML. With React 18's streaming SSR (`renderToPipeableStream`), this becomes problematic — the library needs all styles up-front, but streaming means chunks of HTML are sent progressively.

**3. React Server Components incompatibility:**

RSC cannot use runtime CSS-in-JS because Server Components cannot inject `<style>` tags into the DOM or hold client-side state for style caches.

**4. Hydration mismatches:**

If the class name hash differs between server and client (due to rendering order differences in concurrent mode), you get hydration warnings and a flash of unstyled content.

```jsx
// Demonstration: Why runtime CSS-in-JS conflicts with concurrent rendering

// styled-components — style generation happens during render
import styled from 'styled-components';

const DynamicBox = styled.div`
  /* This interpolation runs on every render */
  background-color: ${(props) => props.$color};
  padding: ${(props) => props.$spacing}px;
  border-radius: 8px;
  /* The library must hash this entire string, check cache, possibly inject */
`;

function Dashboard({ items }) {
  // In concurrent mode, React may render this component multiple times
  // before committing. Each render triggers style serialization.
  return (
    <div>
      {items.map((item) => (
        // Each unique combination of $color + $spacing generates a new CSS rule
        <DynamicBox key={item.id} $color={item.color} $spacing={item.spacing}>
          {item.label}
        </DynamicBox>
      ))}
    </div>
  );
}

// ✅ Better approach: CSS custom properties + CSS Modules (zero runtime)
/* DynamicBox.module.css */
/*
.box {
  background-color: var(--box-color);
  padding: var(--box-spacing);
  border-radius: 8px;
}
*/

import styles from './DynamicBox.module.css';

function DashboardOptimized({ items }) {
  return (
    <div>
      {items.map((item) => (
        <div
          key={item.id}
          className={styles.box}
          style={{
            '--box-color': item.color,
            '--box-spacing': `${item.spacing}px`,
          }}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
}
```

**Benchmarks in practice:**

The React core team at Meta published data showing that runtime CSS-in-JS was responsible for ~15% of render time in their benchmarks. This led to the development of **StyleX** (Meta's internal zero-runtime solution) and broader industry movement toward build-time CSS solutions.

**Mitigation strategies if you must use runtime CSS-in-JS:**
- Avoid highly dynamic interpolations — prefer a fixed set of variants.
- Use the `css` prop with static styles (easier to cache).
- Consider migrating to zero-runtime alternatives like vanilla-extract or Panda CSS.

---

### Q10. How does Tailwind CSS work with component variants using `cva` (class-variance-authority)?

**Answer:**

While Tailwind CSS provides the utility classes, it doesn't natively offer a way to define **component variants** (like `variant="primary"`, `size="lg"`) with type safety. **`cva` (class-variance-authority)** fills this gap by providing a structured, type-safe API for defining variant-driven class compositions that work perfectly with Tailwind.

**What `cva` provides:**

1. **Base classes** — applied to every instance of the component.
2. **Variants** — named groups of mutually exclusive style options.
3. **Compound variants** — styles applied when specific variant combinations are active.
4. **Default variants** — fallback values when a variant isn't specified.
5. **Full TypeScript inference** — variant props are auto-typed.

```jsx
// button.variants.ts — define variants separately for reuse
import { cva, type VariantProps } from 'class-variance-authority';

export const buttonVariants = cva(
  // Base classes — always applied
  [
    'inline-flex items-center justify-center gap-2',
    'rounded-lg font-medium whitespace-nowrap',
    'transition-colors duration-150',
    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
    'disabled:opacity-50 disabled:pointer-events-none',
  ],
  {
    variants: {
      variant: {
        primary:
          'bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-blue-600',
        secondary:
          'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:outline-gray-500 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700',
        destructive:
          'bg-red-600 text-white hover:bg-red-700 focus-visible:outline-red-600',
        ghost:
          'bg-transparent text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800',
        outline:
          'border border-gray-300 bg-transparent text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
        icon: 'h-10 w-10',
      },
    },
    compoundVariants: [
      // When both destructive AND outline, change the border/text color
      {
        variant: 'outline',
        size: 'lg',
        className: 'text-base font-semibold', // extra emphasis for large outlined
      },
    ],
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export type ButtonVariants = VariantProps<typeof buttonVariants>;

// Button.tsx — the actual component
import { forwardRef } from 'react';
import { buttonVariants, type ButtonVariants } from './button.variants';
import { clsx } from 'clsx';

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    ButtonVariants {
  asChild?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant, size, className, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={clsx(buttonVariants({ variant, size }), className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
export { Button };

// Usage — fully typed variants
function App() {
  return (
    <div className="flex gap-3">
      <Button>Default (primary md)</Button>
      <Button variant="secondary" size="lg">Large Secondary</Button>
      <Button variant="destructive" size="sm">Delete</Button>
      <Button variant="ghost" size="icon">
        <SearchIcon className="h-5 w-5" />
      </Button>
      {/* TypeScript error: variant="banana" is not assignable */}
    </div>
  );
}
```

**Why `cva` is popular:**

- It is the pattern behind **shadcn/ui**, the most popular React component toolkit.
- It works at build time — zero runtime overhead.
- The variant definitions serve as living documentation of the component's design API.
- It composes cleanly with `clsx` for consumer-level overrides via the `className` prop.

---

### Q11. What are the advanced features of styled-components (extending, polymorphic `as`, and `attrs`)?

**Answer:**

styled-components provides several advanced APIs that enable building flexible, reusable component systems:

**1. Extending styled components:**

You can create a new styled component based on an existing one, inheriting its styles and adding or overriding rules. This is the primary mechanism for building component hierarchies.

**2. Polymorphic `as` prop:**

Every styled component accepts an `as` prop that changes the underlying HTML element or component it renders, without changing its styles. This is essential for semantic HTML and accessibility.

**3. `.attrs()` method:**

`.attrs()` lets you define default or computed HTML attributes and props. It is called before the component renders and can be used for setting static attributes, computing values from props, or providing defaults.

```jsx
import styled, { css } from 'styled-components';

// === 1. EXTENDING ===

const BaseButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms ease;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Extend BaseButton with primary styles
const PrimaryButton = styled(BaseButton)`
  background-color: #2563eb;
  color: white;

  &:hover:not(:disabled) {
    background-color: #1d4ed8;
  }
`;

// Extend further for a danger variant
const DangerButton = styled(BaseButton)`
  background-color: #dc2626;
  color: white;

  &:hover:not(:disabled) {
    background-color: #b91c1c;
  }
`;

// === 2. POLYMORPHIC `as` PROP ===

const Text = styled.p`
  font-size: ${(props) => {
    const sizes = { sm: '0.875rem', md: '1rem', lg: '1.25rem', xl: '1.5rem' };
    return sizes[props.$size] || sizes.md;
  }};
  color: ${(props) => props.$muted ? 'var(--color-text-muted)' : 'var(--color-text)'};
  line-height: 1.6;
`;

function Article() {
  return (
    <article>
      {/* Renders as <h1> but with Text's styles */}
      <Text as="h1" $size="xl">Article Title</Text>

      {/* Renders as <span> inline */}
      <Text as="span" $size="sm" $muted>Published: Jan 2026</Text>

      {/* Default: renders as <p> */}
      <Text>Body paragraph here.</Text>

      {/* Renders as a React Router Link */}
      <Text as={Link} to="/about" $size="sm">Read more</Text>
    </article>
  );
}

// === 3. `.attrs()` METHOD ===

// Static attrs — always set type="button" to prevent form submission
const IconButton = styled.button.attrs({
  type: 'button',
})`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;

  &:hover {
    background: rgba(0, 0, 0, 0.05);
  }
`;

// Dynamic attrs — compute aria-label and tabIndex from props
const Input = styled.input.attrs((props) => ({
  type: props.type || 'text',
  'aria-invalid': props.$hasError ? 'true' : undefined,
  'aria-describedby': props.$hasError ? `${props.id}-error` : undefined,
}))`
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid ${(props) => (props.$hasError ? '#dc2626' : '#d1d5db')};
  border-radius: 0.5rem;
  font-size: 1rem;
  outline: none;
  transition: border-color 150ms;

  &:focus {
    border-color: ${(props) => (props.$hasError ? '#dc2626' : '#2563eb')};
    box-shadow: 0 0 0 3px ${(props) =>
      props.$hasError ? 'rgba(220, 38, 38, 0.2)' : 'rgba(37, 99, 235, 0.2)'};
  }
`;

// Usage
function LoginForm() {
  return (
    <form>
      <Input id="email" placeholder="Email" $hasError={false} />
      <Input id="password" type="password" placeholder="Password" $hasError={true} />
      {/* IconButton always renders type="button" */}
      <IconButton onClick={() => {}}>👁</IconButton>
    </form>
  );
}
```

**Important note:** In styled-components v5.1+, the convention is to prefix custom props with `$` (transient props) to prevent them from being forwarded to the DOM element (e.g., `$size`, `$hasError`).

---

### Q12. What are the major animation strategies in React, and when should you use each?

**Answer:**

Animation in React falls into several categories, each optimized for different use cases:

| Strategy | Best for | Runtime cost | Learning curve |
|---|---|---|---|
| CSS transitions/animations | Simple state changes (hover, enter/exit) | Zero JS cost | Low |
| Framer Motion | Complex orchestrated animations, gestures, layout | ~30 kB | Medium |
| react-spring | Physics-based, interruptible animations | ~18 kB | Medium-High |
| CSS `@keyframes` | Looping/continuous animations (spinners, pulses) | Zero JS cost | Low |
| Web Animations API (WAAPI) | Programmatic, performance-critical animations | Zero dependency | High |

**Principle:** Always prefer CSS-only solutions when possible. Reach for JS animation libraries only when you need orchestration, physics, gesture control, or layout animations.

```jsx
// === 1. CSS TRANSITIONS — simple hover/state changes ===
/* Card.module.css */
/*
.card {
  transform: translateY(0);
  opacity: 1;
  transition: transform 300ms ease, opacity 300ms ease, box-shadow 300ms ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.cardEnter {
  opacity: 0;
  transform: translateY(20px);
}

.cardEnterActive {
  opacity: 1;
  transform: translateY(0);
}
*/

// === 2. FRAMER MOTION — orchestrated animations ===
import { motion, AnimatePresence } from 'framer-motion';

function NotificationList({ notifications, onDismiss }) {
  return (
    <div className="fixed right-4 top-4 flex flex-col gap-2 z-50">
      <AnimatePresence mode="popLayout">
        {notifications.map((notif) => (
          <motion.div
            key={notif.id}
            // Enter animation
            initial={{ opacity: 0, x: 100, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            // Exit animation
            exit={{ opacity: 0, x: 100, scale: 0.95 }}
            // Spring physics
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            // Layout animation — smoothly reflows when siblings are removed
            layout
            className="rounded-lg bg-white p-4 shadow-lg border"
          >
            <p>{notif.message}</p>
            <button onClick={() => onDismiss(notif.id)}>Dismiss</button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

// === 3. REACT-SPRING — physics-based, interruptible ===
import { useSpring, animated } from '@react-spring/web';

function AnimatedCounter({ value }) {
  const spring = useSpring({
    from: { number: 0 },
    to: { number: value },
    config: { mass: 1, tension: 170, friction: 26 },
  });

  return (
    <animated.span className="text-4xl font-bold tabular-nums">
      {spring.number.to((n) => Math.floor(n).toLocaleString())}
    </animated.span>
  );
}

// === 4. CSS @keyframes — looping animations (zero JS) ===
function Spinner() {
  return (
    <svg
      className="h-5 w-5 animate-spin text-blue-600"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12" cy="12" r="10"
        stroke="currentColor" strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
```

**Decision guide:**
- **Hover effects, simple enter/exit** → CSS transitions.
- **Spinners, skeleton loaders** → CSS `@keyframes`.
- **Toast notifications, modals, route transitions, drag/drop** → Framer Motion.
- **Number counters, scroll-linked, physics-based** → react-spring.
- **Maximum performance, no dependency** → Web Animations API via `useRef` + `element.animate()`.

---

## Advanced Level (Q13–Q20)

---

### Q13. What are zero-runtime CSS-in-JS solutions (vanilla-extract, Panda CSS, Linaria), and why is the industry moving toward them?

**Answer:**

**Zero-runtime CSS-in-JS** solutions let you author styles using JavaScript/TypeScript APIs — getting the DX benefits of CSS-in-JS (co-location, type safety, dynamic theming) — but extract everything to **static CSS files at build time**. No JavaScript runs in the browser to generate or inject styles.

**Why the shift:**

1. **React 18 concurrent rendering** — runtime CSS-in-JS interferes with `useTransition`, `Suspense` boundaries, and streaming SSR because style generation is synchronous and side-effectful.
2. **React Server Components** — RSC cannot run browser-side code; runtime CSS-in-JS libraries are inherently client-only.
3. **Performance** — Meta's data showed runtime CSS-in-JS contributed 10-15% of render time. Removing it is "free" performance.
4. **Bundle size** — no library code (styled-components ~13 kB, Emotion ~7 kB) needs to ship to the client.

| Library | Approach | TypeScript | Theme support | Ecosystem |
|---|---|---|---|---|
| **vanilla-extract** | `.css.ts` files compiled by Vite/webpack plugin | First-class (types from tokens) | `createTheme` + `createThemeContract` | Growing, used by Shopify Polaris |
| **Panda CSS** | Config-driven, generates utility + recipe CSS | First-class codegen | Tokens + semantic tokens in config | Newer, by Chakra UI team |
| **Linaria** | Tagged template literals compiled away | Basic | Via CSS variables | Mature but smaller community |
| **StyleX** | Atomic CSS from object styles | First-class | Tokens via `stylex.defineVars` | Meta's internal solution, open-sourced |

```jsx
// === vanilla-extract example ===
// Button.css.ts — this file is ONLY processed at build time
import { style, styleVariants } from '@vanilla-extract/css';
import { vars } from './theme.css'; // typed theme tokens

export const base = style({
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: vars.radius.md,
  fontWeight: 500,
  border: 'none',
  cursor: 'pointer',
  transition: 'background-color 150ms ease',
  ':disabled': {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
});

export const variant = styleVariants({
  primary: {
    backgroundColor: vars.color.primary,
    color: 'white',
    ':hover': { backgroundColor: vars.color.primaryHover },
  },
  secondary: {
    backgroundColor: vars.color.surfaceAlt,
    color: vars.color.text,
    ':hover': { backgroundColor: vars.color.surfaceAltHover },
  },
});

export const size = styleVariants({
  sm: { height: '2rem', padding: '0 0.75rem', fontSize: '0.875rem' },
  md: { height: '2.5rem', padding: '0 1rem', fontSize: '0.875rem' },
  lg: { height: '3rem', padding: '0 1.5rem', fontSize: '1rem' },
});

// Button.tsx — the runtime component has zero style generation
import * as styles from './Button.css';
import { clsx } from 'clsx';

function Button({ variant: v = 'primary', size: s = 'md', className, ...props }) {
  return (
    <button
      className={clsx(styles.base, styles.variant[v], styles.size[s], className)}
      {...props}
    />
  );
}

// === Panda CSS example ===
// panda.config.ts defines tokens, then you use generated utilities
import { css, cva } from '../styled-system/css';

const button = cva({
  base: {
    display: 'inline-flex',
    alignItems: 'center',
    borderRadius: 'md',
    fontWeight: 'medium',
    cursor: 'pointer',
    transition: 'colors',
  },
  variants: {
    variant: {
      primary: { bg: 'blue.600', color: 'white', _hover: { bg: 'blue.700' } },
      secondary: { bg: 'gray.100', color: 'gray.900', _hover: { bg: 'gray.200' } },
    },
    size: {
      sm: { h: '8', px: '3', textStyle: 'sm' },
      md: { h: '10', px: '4', textStyle: 'sm' },
    },
  },
  defaultVariants: { variant: 'primary', size: 'md' },
});

function PandaButton({ variant, size, children }) {
  return <button className={button({ variant, size })}>{children}</button>;
}
```

**Recommendation for new projects in 2025+:** If you want CSS-in-JS DX with zero runtime cost, **vanilla-extract** (for type-safe atomic/scoped CSS) or **Panda CSS** (for utility-first + recipes) are the strongest choices. If you prefer simplicity, **Tailwind + cva** achieves similar goals without a CSS-in-JS abstraction.

---

### Q14. How do you build a design token system with CSS variables for a React application?

**Answer:**

A **design token system** codifies your visual language — colors, spacing, typography, shadows, radii, breakpoints — as named, reusable values. CSS custom properties are the ideal storage mechanism because they cascade, can be scoped, support runtime overrides (theming), and work with every styling approach.

**Token architecture (3 tiers):**

1. **Primitive tokens** — raw values: `--blue-600: #2563eb`.
2. **Semantic tokens** — meaningful aliases: `--color-primary: var(--blue-600)`.
3. **Component tokens** — scoped to a component: `--button-bg: var(--color-primary)`.

This layering enables theme switching by only redefining the semantic layer.

```jsx
// tokens.css — the complete token system
/*
:root {
  /* === Primitive Tokens === */
  /* Spacing (4px base unit) */
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-12: 3rem;     /* 48px */

  /* Typography scale */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;

  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;

  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;

  /* Radii */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

  /* === Semantic Tokens (Light theme) === */
  --color-bg: #ffffff;
  --color-surface: #f8fafc;
  --color-surface-raised: #ffffff;
  --color-text: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #94a3b8;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-text: #ffffff;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-error: #dc2626;
}

[data-theme="dark"] {
  --color-bg: #0f172a;
  --color-surface: #1e293b;
  --color-surface-raised: #334155;
  --color-text: #f1f5f9;
  --color-text-secondary: #cbd5e1;
  --color-text-muted: #64748b;
  --color-primary: #3b82f6;
  --color-primary-hover: #60a5fa;
  --color-primary-text: #ffffff;
  --color-border: #334155;
  --color-border-strong: #475569;
  --color-success: #22c55e;
  --color-warning: #fbbf24;
  --color-error: #ef4444;

  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
}
*/

// useDesignTokens.js — utility hook to read computed token values if needed in JS
import { useMemo } from 'react';

export function useDesignToken(tokenName) {
  return useMemo(() => {
    if (typeof window === 'undefined') return '';
    return getComputedStyle(document.documentElement)
      .getPropertyValue(tokenName)
      .trim();
  }, [tokenName]);
}

// Card.module.css — component using tokens
/*
.card {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 200ms ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.title {
  font-family: var(--font-sans);
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.description {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}
*/

import styles from './Card.module.css';

function Card({ title, description }) {
  return (
    <div className={styles.card}>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.description}>{description}</p>
    </div>
  );
}
```

**Why this architecture works at scale:**

- Designers update tokens in one file; changes cascade everywhere.
- Dark mode is a single `data-theme` attribute swap.
- New themes (high-contrast, brand variants) only require redefining the semantic layer.
- Components never hard-code colors or spacing — they reference tokens.

---

### Q15. What are the common patterns for implementing dark mode in a React application?

**Answer:**

Dark mode implementation requires coordination across three concerns: **detection** (what is the user's preference?), **persistence** (remembering the choice), and **application** (swapping styles without flicker). Here is the production-grade approach:

**The FOUC (Flash of Unstyled Content) problem:**

If you wait for React to hydrate before setting the theme, users see a flash of the default (usually light) theme. The solution is an **inline blocking script** in the `<head>` that runs before any content paints.

```jsx
// === 1. Anti-flicker script (goes in <head> BEFORE React) ===
// In Next.js: app/layout.tsx or pages/_document.tsx
// In Vite: index.html

/*
<script>
  (function() {
    const stored = localStorage.getItem('theme');
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const theme = stored || preferred;
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;
  })();
</script>
*/

// === 2. CSS with data-theme attribute (see Q8 for full token definitions) ===
/*
:root, [data-theme="light"] {
  color-scheme: light;
  --color-bg: #ffffff;
  --color-text: #0f172a;
  /* ...more tokens... */
}

[data-theme="dark"] {
  color-scheme: dark;
  --color-bg: #0f172a;
  --color-text: #f1f5f9;
  /* ...more tokens... */
}

body {
  background-color: var(--color-bg);
  color: var(--color-text);
  transition: background-color 200ms ease, color 200ms ease;
}
*/

// === 3. React Context for theme management ===
import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light';
    // Read what the blocking script already set
    return document.documentElement.getAttribute('data-theme') || 'light';
  });

  const setThemeAndPersist = useCallback((newTheme) => {
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    document.documentElement.style.colorScheme = newTheme;
    localStorage.setItem('theme', newTheme);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeAndPersist(theme === 'light' ? 'dark' : 'light');
  }, [theme, setThemeAndPersist]);

  // Sync with OS preference changes (only if user hasn't manually chosen)
  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => {
      const hasManualPreference = localStorage.getItem('theme');
      if (!hasManualPreference) {
        setThemeAndPersist(e.matches ? 'dark' : 'light');
      }
    };
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [setThemeAndPersist]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme: setThemeAndPersist, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
};

// === 4. Theme toggle component with system option ===
function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  const options = [
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
    { value: 'system', label: 'System' },
  ];

  const handleChange = (value) => {
    if (value === 'system') {
      localStorage.removeItem('theme');
      const osTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      setTheme(osTheme);
    } else {
      setTheme(value);
    }
  };

  return (
    <div role="radiogroup" aria-label="Color theme" className="flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
      {options.map((opt) => (
        <button
          key={opt.value}
          role="radio"
          aria-checked={theme === opt.value}
          onClick={() => handleChange(opt.value)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            theme === opt.value
              ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white'
              : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// === 5. Tailwind dark mode integration ===
// tailwind.config.js: { darkMode: 'selector', ... }
// Then [data-theme="dark"] activates Tailwind's dark: prefix

function TailwindDarkCard({ children }) {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800 dark:shadow-gray-900/20">
      <p className="text-gray-900 dark:text-gray-100">{children}</p>
    </div>
  );
}
```

**Key details:**

- `color-scheme: dark` tells the browser to use dark defaults for scrollbars, form controls, and `system-colors`.
- The blocking script ensures zero flash — it runs synchronously before first paint.
- The three-option approach (light/dark/system) is the UX gold standard.
- Tailwind's `darkMode: 'selector'` (v3.4+) or `'class'` mode works directly with `data-theme` or a CSS class.

---

### Q16. How does CSS Module composition work, and how do you handle global overrides within modules?

**Answer:**

CSS Modules support two powerful features for style reuse and escape hatches: **`composes`** (for composing local and external classes) and **`:global()`** (for opting specific selectors out of local scoping).

**`composes` keyword:**

Allows one class to inherit all styles from another class — either from the same file or from an external module. Unlike Sass `@extend`, `composes` works by adding multiple class names to the element rather than duplicating CSS rules.

**`:global()` selector:**

Wraps a selector to prevent it from being locally scoped. Useful for targeting third-party library classes, `data-*` attribute selectors, or state classes added by JavaScript libraries.

```jsx
// === COMPOSITION: same file ===
/* typography.module.css */
/*
.base {
  font-family: var(--font-sans);
  line-height: 1.5;
}

.heading {
  composes: base;
  font-weight: var(--weight-bold);
  letter-spacing: -0.02em;
  color: var(--color-text);
}

.h1 {
  composes: heading;
  font-size: var(--text-3xl);
}

.h2 {
  composes: heading;
  font-size: var(--text-2xl);
}

.body {
  composes: base;
  font-size: var(--text-base);
  color: var(--color-text-secondary);
}

.caption {
  composes: base;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
*/

// When you use styles.h1, the element gets:
// class="h1_x7k2q heading_x7k2q base_x7k2q"
// All three class rules apply — no CSS duplication.

import typo from './typography.module.css';

function PageHeader({ title, subtitle }) {
  return (
    <header>
      <h1 className={typo.h1}>{title}</h1>
      <p className={typo.body}>{subtitle}</p>
    </header>
  );
}

// === COMPOSITION: from another file ===
/* Button.module.css */
/*
.button {
  composes: focusRing from './shared.module.css';
  composes: transition from './shared.module.css';
  display: inline-flex;
  align-items: center;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
}
*/

// === :global() for third-party overrides ===
/* DatePicker.module.css */
/*
.wrapper {
  position: relative;
}

/* Override react-datepicker's global classes within our wrapper */
.wrapper :global(.react-datepicker) {
  font-family: var(--font-sans);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.wrapper :global(.react-datepicker__header) {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.wrapper :global(.react-datepicker__day--selected) {
  background: var(--color-primary);
  color: var(--color-primary-text);
}

/* Mix local and global: .wrapper is scoped, [data-state] is global */
.wrapper :global([data-state="open"]) {
  animation: fadeIn 150ms ease;
}
*/

import styles from './DatePicker.module.css';
import ReactDatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css'; // base styles

function DatePicker({ value, onChange }) {
  return (
    <div className={styles.wrapper}>
      <ReactDatePicker selected={value} onChange={onChange} />
    </div>
  );
}

// === :global() for state-based classes from JS ===
/* Modal.module.css */
/*
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

/* When body has a global .no-scroll class (added via JS) */
:global(body.no-scroll) {
  overflow: hidden;
}

/* Scoped class that only applies within the modal context */
.overlay :global(.focus-trap-active) {
  outline: 2px solid var(--color-primary);
}
*/
```

**Best practices:**

- Use `composes` for building a typography or spacing utility system within CSS Modules.
- Use `:global()` sparingly — only for third-party library overrides and JavaScript-driven state classes.
- Prefer `:global()` scoped within a local parent (`.wrapper :global(.lib-class)`) to limit blast radius.

---

### Q17. How do you handle critical CSS extraction and style management for server-side rendering in React 18?

**Answer:**

React 18's `renderToPipeableStream` enables **streaming SSR**, where HTML is sent to the client in chunks as components resolve. This fundamentally changes how styles must be managed — styles for each chunk must be available *before or alongside* that chunk, or users see unstyled content.

**The challenge by styling strategy:**

| Strategy | SSR behavior | Streaming compatible? |
|---|---|---|
| CSS Modules / Tailwind | Static CSS files linked in `<head>` | Yes — CSS loads first, HTML streams after |
| styled-components | Styles collected via `ServerStyleSheet` during render | Partial — requires wrapping, can block streaming |
| Emotion | `extractCriticalToChunks` collects styles | Partial — similar constraints |
| vanilla-extract | Static `.css` files | Yes — fully compatible |

**Approach 1: Static CSS (CSS Modules / Tailwind) — best for streaming**

```jsx
// Next.js app router — styles are in the CSS bundle, no special handling needed

// layout.tsx
import './globals.css'; // Tailwind / global tokens
// CSS Modules are automatically extracted into the CSS bundle by the bundler

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        {/* CSS is linked here automatically by the framework */}
      </head>
      <body>{children}</body>
    </html>
  );
}
```

**Approach 2: styled-components with streaming SSR**

```jsx
// For styled-components in a custom Node.js server with React 18 streaming
import { renderToPipeableStream } from 'react-dom/server';
import { ServerStyleSheet, StyleSheetManager } from 'styled-components';
import { Transform } from 'stream';

function handleRequest(req, res) {
  const sheet = new ServerStyleSheet();

  const { pipe, abort } = renderToPipeableStream(
    <StyleSheetManager sheet={sheet.instance}>
      <App />
    </StyleSheetManager>,
    {
      onShellReady() {
        res.statusCode = 200;
        res.setHeader('Content-Type', 'text/html');

        // Inject collected styles into the stream
        const styleTags = sheet.getStyleTags();

        // Transform stream to inject styles before </head>
        const transform = new Transform({
          transform(chunk, encoding, callback) {
            const html = chunk.toString();
            if (html.includes('</head>')) {
              callback(null, html.replace('</head>', `${styleTags}</head>`));
            } else {
              callback(null, chunk);
            }
          },
        });

        pipe(transform).pipe(res);
      },
      onError(error) {
        console.error(error);
        res.statusCode = 500;
        res.end('Internal Server Error');
      },
      onAllReady() {
        sheet.seal(); // Clean up
      },
    }
  );

  setTimeout(() => abort(), 10000); // 10s timeout
}

// === Critical CSS extraction with a Vite/webpack plugin ===
// For CSS Modules, tools like critters (used by Next.js) can inline
// critical above-the-fold CSS and defer the rest:

/*
// vite.config.js
import critters from 'vite-plugin-critters';

export default {
  plugins: [
    critters({
      // Inline critical CSS, preload the rest
      preload: 'swap',
      // Only inline styles needed for above-the-fold content
      inlineFonts: false,
    }),
  ],
};
*/
```

**Approach 3: Emotion with Next.js App Router**

```jsx
// Emotion requires a CacheProvider for SSR in Next.js App Router
'use client';

import { CacheProvider } from '@emotion/react';
import createEmotionCache from './createEmotionCache';
import { useServerInsertedHTML } from 'next/navigation';
import { useState } from 'react';

export function EmotionProvider({ children }) {
  const [cache] = useState(() => createEmotionCache());

  useServerInsertedHTML(() => {
    const entries = Object.entries(cache.inserted);
    if (entries.length === 0) return null;

    const styles = entries.map(([key, value]) => value).join('');
    // Clear after extraction to avoid duplicates
    cache.inserted = {};

    return (
      <style
        data-emotion={`${cache.key}`}
        dangerouslySetInnerHTML={{ __html: styles }}
      />
    );
  });

  return <CacheProvider value={cache}>{children}</CacheProvider>;
}
```

**Recommendation:** For new React 18 projects using streaming SSR or RSC, prefer **static CSS solutions** (CSS Modules, Tailwind, vanilla-extract) that require no special SSR handling. If using CSS-in-JS, vanilla-extract or Panda CSS (zero-runtime) are the path of least resistance.

---

### Q18. How do you optimize style performance in React, avoiding layout thrashing and using GPU-accelerated properties?

**Answer:**

Style performance optimization in React requires understanding the browser's rendering pipeline: **Style → Layout → Paint → Composite**. Certain CSS properties trigger expensive layout recalculations (reflows), while others can be handled entirely by the GPU compositor.

**Layout-triggering properties (expensive):**
`width`, `height`, `padding`, `margin`, `top`, `left`, `font-size`, `border` — reading or writing these forces the browser to recalculate the layout of potentially the entire page.

**Compositor-only properties (cheap):**
`transform`, `opacity`, `filter` — these can be handled on the GPU without touching the main thread.

**Layout thrashing** occurs when you interleave DOM reads and writes, forcing the browser to recalculate layout multiple times in a single frame.

```jsx
// === 1. Prefer transform over top/left for animations ===

/* ❌ Bad — triggers layout on every frame */
/*
.animate-bad {
  position: absolute;
  transition: top 300ms, left 300ms;
}
*/

/* ✅ Good — compositor-only, GPU accelerated */
/*
.animate-good {
  transition: transform 300ms ease;
  will-change: transform;
}
*/

// === 2. Avoid layout thrashing in React ===

import { useRef, useLayoutEffect, useCallback } from 'react';

// ❌ BAD: Reads then writes in a loop → layout thrashing
function BadResizer({ items }) {
  const refs = useRef([]);

  useLayoutEffect(() => {
    refs.current.forEach((el) => {
      const height = el.offsetHeight;   // READ → forces layout
      el.style.minHeight = `${height + 20}px`; // WRITE → invalidates layout
      // Next iteration: READ forces recalculation again!
    });
  });

  return items.map((item, i) => (
    <div key={item.id} ref={(el) => (refs.current[i] = el)}>
      {item.content}
    </div>
  ));
}

// ✅ GOOD: Batch reads, then batch writes
function GoodResizer({ items }) {
  const refs = useRef([]);

  useLayoutEffect(() => {
    // PHASE 1: Batch all reads
    const measurements = refs.current.map((el) => el.offsetHeight);

    // PHASE 2: Batch all writes (no layout recalc between writes)
    refs.current.forEach((el, i) => {
      el.style.minHeight = `${measurements[i] + 20}px`;
    });
  });

  return items.map((item, i) => (
    <div key={item.id} ref={(el) => (refs.current[i] = el)}>
      {item.content}
    </div>
  ));
}

// === 3. will-change usage — hint, not a silver bullet ===

/* Card.module.css */
/*
.card {
  border-radius: var(--radius-lg);
  transition: transform 200ms ease, box-shadow 200ms ease;
}

/* Only promote to compositor layer on hover intent */
.card:hover {
  will-change: transform;
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

/* ❌ Don't: will-change on everything, always */
/* .everything { will-change: transform, opacity; }   ← wastes GPU memory */

/* ✅ Do: apply will-change just before animation starts, remove after */
*/

// === 4. Avoiding expensive style recalculations in lists ===
import { memo, useMemo } from 'react';

// ✅ Memoize style objects to prevent unnecessary reconciliation
const ListItem = memo(function ListItem({ item, isSelected }) {
  const style = useMemo(() => ({
    transform: isSelected ? 'scale(1.02)' : 'scale(1)',
    opacity: isSelected ? 1 : 0.8,
    transition: 'transform 150ms ease, opacity 150ms ease',
  }), [isSelected]);

  return (
    <div style={style} className="rounded-lg border p-4">
      {item.label}
    </div>
  );
});

// === 5. CSS containment for large lists ===
/* ListItem.module.css */
/*
.item {
  contain: content;  /* Tells browser this element's internals don't affect outside layout */
  content-visibility: auto;  /* Skip rendering for off-screen items */
  contain-intrinsic-size: auto 80px;  /* Estimated size for skipped items */
}
*/

// === 6. Prefer CSS transitions over JS-driven animation loops ===
function ExpandablePanel({ isOpen, children }) {
  const contentRef = useRef(null);
  const [height, setHeight] = useState(0);

  useLayoutEffect(() => {
    if (contentRef.current) {
      setHeight(contentRef.current.scrollHeight);
    }
  }, [children]);

  return (
    <div
      style={{
        maxHeight: isOpen ? height : 0,
        overflow: 'hidden',
        transition: 'max-height 300ms ease-in-out',
      }}
    >
      <div ref={contentRef}>{children}</div>
    </div>
  );
}
```

**Performance checklist:**

1. **Animate only `transform` and `opacity`** when possible — these are compositor-only.
2. **Batch DOM reads before writes** in `useLayoutEffect` — prevents layout thrashing.
3. **Use `will-change` surgically** — only on elements about to animate, not globally.
4. **Use `contain: content`** on repeated elements to isolate layout calculations.
5. **Use `content-visibility: auto`** for long lists to skip rendering off-screen items.
6. **Memoize style objects** to prevent unnecessary React reconciliation.
7. **Avoid inline style objects that change identity on every render** — use `useMemo` or extract to module scope.

---

### Q19. How do you build a consistent design system with tokens and variants in React?

**Answer:**

A production design system combines **design tokens** (the values), **variant-driven component APIs** (the interfaces), and **documentation/constraints** (the guardrails). The goal is to make it easy to build consistent UIs and hard to deviate from the system.

**Architecture layers:**

1. **Token layer** — CSS custom properties (see Q14) defining colors, spacing, typography, etc.
2. **Component layer** — React components with typed variant props that map to token-based styles.
3. **Composition layer** — Layout primitives (`Stack`, `Grid`, `Container`) that enforce spacing and alignment rules.
4. **Documentation layer** — Storybook stories showcasing each variant, state, and composition pattern.

```jsx
// === TOKEN LAYER: tailwind.config.ts extending with your tokens ===
/*
import type { Config } from 'tailwindcss';

export default {
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a5f',
        },
        surface: {
          DEFAULT: 'var(--color-surface)',
          raised: 'var(--color-surface-raised)',
        },
      },
      spacing: {
        // Design system uses 4px grid
        4.5: '1.125rem', // 18px — for specific use cases
      },
      borderRadius: {
        DEFAULT: 'var(--radius-md)',
      },
    },
  },
} satisfies Config;
*/

// === VARIANT LAYER: variant definitions with cva ===
import { cva, type VariantProps } from 'class-variance-authority';

// Badge component variants
const badgeVariants = cva(
  'inline-flex items-center rounded-full font-medium ring-1 ring-inset',
  {
    variants: {
      variant: {
        default: 'bg-gray-50 text-gray-700 ring-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:ring-gray-700',
        success: 'bg-green-50 text-green-700 ring-green-200 dark:bg-green-900/30 dark:text-green-400 dark:ring-green-800',
        warning: 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:ring-amber-800',
        error:   'bg-red-50 text-red-700 ring-red-200 dark:bg-red-900/30 dark:text-red-400 dark:ring-red-800',
        info:    'bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:ring-blue-800',
      },
      size: {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-1 text-xs',
        lg: 'px-3 py-1.5 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>;

function Badge({ variant, size, className, ...props }: BadgeProps) {
  return <span className={clsx(badgeVariants({ variant, size }), className)} {...props} />;
}

// === COMPOSITION LAYER: Layout primitives ===
import { clsx } from 'clsx';

interface StackProps {
  gap?: '1' | '2' | '3' | '4' | '6' | '8';
  direction?: 'row' | 'column';
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between';
  children: React.ReactNode;
  className?: string;
  as?: React.ElementType;
}

const gapMap = {
  '1': 'gap-1', '2': 'gap-2', '3': 'gap-3',
  '4': 'gap-4', '6': 'gap-6', '8': 'gap-8',
} as const;

const dirMap = { row: 'flex-row', column: 'flex-col' } as const;
const alignMap = { start: 'items-start', center: 'items-center', end: 'items-end', stretch: 'items-stretch' } as const;
const justifyMap = { start: 'justify-start', center: 'justify-center', end: 'justify-end', between: 'justify-between' } as const;

function Stack({
  gap = '4',
  direction = 'column',
  align = 'stretch',
  justify = 'start',
  as: Component = 'div',
  className,
  children,
}: StackProps) {
  return (
    <Component
      className={clsx(
        'flex',
        dirMap[direction],
        gapMap[gap],
        alignMap[align],
        justifyMap[justify],
        className
      )}
    >
      {children}
    </Component>
  );
}

// === USAGE: Composing design system components ===
function UserProfile({ user }) {
  return (
    <Stack gap="6">
      <Stack direction="row" align="center" gap="4">
        <Avatar src={user.avatar} size="lg" />
        <Stack gap="1">
          <Text size="lg" weight="semibold">{user.name}</Text>
          <Text size="sm" color="muted">{user.email}</Text>
        </Stack>
        <Badge variant={user.isActive ? 'success' : 'default'}>
          {user.isActive ? 'Active' : 'Inactive'}
        </Badge>
      </Stack>

      <Stack direction="row" gap="3">
        <Button variant="primary">Edit Profile</Button>
        <Button variant="outline">View Activity</Button>
      </Stack>
    </Stack>
  );
}
```

**What makes this system "consistent":**

- **Constrained choices** — variants are an enum, not arbitrary strings. You can't invent `variant="kinda-blue"`.
- **Composable primitives** — `Stack`, `Grid`, and layout components enforce spacing rhythm.
- **Token-based** — all colors, spacing, and typography reference the token system.
- **Type-safe** — TypeScript catches invalid variant usage at build time.
- **Themeable** — swap the CSS variable layer and the entire system re-skins.

---

### Q20. How do you choose a styling strategy for a large React application with a big team?

**Answer:**

Choosing a styling strategy for a large-scale application is an **architectural decision** with long-term consequences. The right choice depends on your team's size, skill distribution, framework, SSR requirements, and performance budget. Here is a decision framework:

**Key evaluation criteria:**

| Criteria | Why it matters |
|---|---|
| **Runtime performance** | Does the solution add JS execution time on every render? |
| **Bundle size** | Does it ship library code to the client? |
| **SSR/streaming compatibility** | Does it work with React 18 `renderToPipeableStream` and RSC? |
| **Type safety** | Can TypeScript catch styling errors at build time? |
| **Team scalability** | Can 50+ developers use it consistently without deep expertise? |
| **Design system fit** | Does it support tokens, variants, and theming natively? |
| **Migration cost** | How hard is it to adopt incrementally or migrate away from? |
| **Tooling/DX** | IDE support, hot reload speed, debugging experience? |

**Decision matrix:**

```jsx
/*
┌─────────────────────────────┬──────────────┬─────────────┬──────────────┬──────────────┐
│ Strategy                    │ Performance  │ SSR/RSC     │ Team Scale   │ Best For     │
├─────────────────────────────┼──────────────┼─────────────┼──────────────┼──────────────┤
│ Tailwind + cva              │ ★★★★★        │ ★★★★★       │ ★★★★★        │ Most teams   │
│ CSS Modules                 │ ★★★★★        │ ★★★★★       │ ★★★★☆        │ Simple apps  │
│ vanilla-extract             │ ★★★★★        │ ★★★★★       │ ★★★☆☆        │ Type-safe DS │
│ Panda CSS                   │ ★★★★★        │ ★★★★★       │ ★★★★☆        │ Utility + DS │
│ StyleX                      │ ★★★★★        │ ★★★★★       │ ★★★★☆        │ Meta-scale   │
│ styled-components / Emotion │ ★★★☆☆        │ ★★★☆☆       │ ★★★★☆        │ Legacy apps  │
│ Sass/SCSS (global)          │ ★★★★★        │ ★★★★★       │ ★★☆☆☆        │ Legacy only  │
└─────────────────────────────┴──────────────┴─────────────┴──────────────┴──────────────┘
*/

// === RECOMMENDED ARCHITECTURE FOR LARGE TEAMS (2025+) ===

// 1. Token Layer — CSS custom properties in a global stylesheet
//    tokens.css → defines ALL design tokens (colors, spacing, type scale)
//    Consumed by both Tailwind config and CSS Modules

// 2. Utility Layer — Tailwind CSS for rapid, consistent styling
//    - JIT ensures only used classes ship
//    - Responsive, dark mode, and state variants built-in
//    - IDE intellisense for autocomplete

// 3. Component API Layer — cva for typed variant definitions
//    - Every shared component has a .variants.ts file
//    - Enforces design system constraints via TypeScript
//    - Works at build time (zero runtime)

// 4. Escape Hatch — CSS Modules for complex/animated components
//    - Used when Tailwind classes get unwieldy (complex animations, container queries)
//    - Scoped by default, reference tokens via var()
//    - Zero runtime, excellent SSR

// === FILE STRUCTURE ===
/*
src/
├── styles/
│   ├── tokens.css            # CSS custom properties (primitive + semantic)
│   ├── globals.css            # Reset, base element styles, @import tokens
│   └── tailwind.config.ts     # Tailwind extending tokens
├── components/
│   ├── ui/                    # Design system primitives
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── button.variants.ts    # cva definition
│   │   │   └── Button.module.css     # Complex styles if needed
│   │   ├── Badge/
│   │   ├── Input/
│   │   └── Stack/
│   └── features/              # Feature-specific components
│       └── Dashboard/
│           ├── StatCard.tsx           # Uses ui/ primitives + Tailwind
│           └── Chart.module.css       # Complex chart-specific styles
*/

// === ESLINT RULES TO ENFORCE CONSISTENCY ===
/*
// .eslintrc.js — enforce the strategy
module.exports = {
  rules: {
    // Ban inline style objects (except for truly dynamic values)
    'react/forbid-component-props': ['warn', {
      forbid: [{
        propName: 'style',
        message: 'Use Tailwind classes or CSS Modules instead of inline styles.'
      }]
    }],
  },
};
*/

// === MIGRATION STRATEGY FOR EXISTING APPS ===

// If moving from styled-components → Tailwind + CSS Modules:
// 1. Install Tailwind, configure design tokens
// 2. New components use Tailwind + cva exclusively
// 3. Codemods convert simple styled-components → Tailwind classes
// 4. Complex components → CSS Modules with token variables
// 5. Gradually remove styled-components as components are refactored
// 6. Remove styled-components dependency once migration is complete

// Example codemod: styled.div`padding: 16px; color: red;`
// → <div className="p-4 text-red-600">

function MigrationExample() {
  // BEFORE: styled-components
  // const Card = styled.div`
  //   padding: 1.5rem;
  //   border-radius: 0.75rem;
  //   background: white;
  //   box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  // `;

  // AFTER: Tailwind
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-gray-800">
      Migrated component
    </div>
  );
}
```

**Practical recommendations by team size:**

- **1-5 developers, new project:** Tailwind CSS + cva + CSS Modules for edge cases. This is the shadcn/ui stack and the current industry default.
- **5-20 developers, established codebase:** Evaluate current strategy. If using runtime CSS-in-JS, plan migration to Tailwind or Panda CSS. If using CSS Modules, add cva for variant management.
- **20-100+ developers, design system team:** Tailwind + cva for application code, vanilla-extract or Panda CSS for the core design system library (better type safety for library authors). Publish the design system as a package with exported variant definitions.
- **Meta-scale (thousands of engineers):** StyleX or a custom atomic CSS solution. These enforce static analysis and optimal deduplication at scale.

**The wrong question is "Which library is best?" The right question is "Which approach enables my team to build consistent, performant UIs with the least friction and highest ceiling?"**

---

*End of Styling Strategies in React 18 — 20 Interview Questions*
