# JSX, Components & Props — React 18 Interview Questions

## Topic Introduction

**JSX (JavaScript XML)** is a syntax extension for JavaScript that lets you write HTML-like markup directly inside your JavaScript code. Under the hood, JSX is not valid JavaScript — it is transformed at build time (by Babel or SWC) into function calls that produce plain JavaScript objects called **React elements**. Prior to React 17, every JSX expression compiled to `React.createElement(type, props, ...children)`, which is why you had to `import React from 'react'` in every file that used JSX. Starting with React 17, the new **automatic JSX runtime** (`react/jsx-runtime`) is injected by the compiler, eliminating that boilerplate import. Understanding this compilation step is essential because it explains why JSX has certain limitations — for example, you can only use *expressions* (not statements) inside `{}`, and component names must start with a capital letter so the compiler can distinguish them from native DOM elements.

**Components** are the fundamental building blocks of any React application. In React 18, **functional components** are the standard — they are plain JavaScript functions that accept a `props` object and return React elements (JSX). Class components still work but are considered legacy; hooks (introduced in React 16.8 and expanded in React 18) provide all the capabilities that once required classes — state, side effects, context, refs, and more. React 18 also introduced **Server Components**, a new component type that renders exclusively on the server and can pass serializable props to Client Components across the network boundary. This distinction is becoming central to modern React architecture (especially in frameworks like Next.js 13+).

**Props (short for properties)** are the mechanism through which data flows from parent to child in React's unidirectional data model. Props are read-only — a component must never mutate its own props. They can carry any JavaScript value: primitives, objects, arrays, functions, and even other React elements (via `children` or render props). Mastering patterns like prop destructuring, default props, the `children` prop, prop spreading, compound components, and polymorphic `as` props is what separates junior developers from senior ones who can design robust, reusable component APIs for large-scale applications and design systems.

```jsx
// A quick taste — a functional component receiving props in React 18
function Greeting({ name, role = "developer" }) {
  return (
    <section>
      <h1>Hello, {name}!</h1>
      <p>Your role: {role}</p>
    </section>
  );
}

// Usage
<Greeting name="Vignesh" />
// renders: Hello, Vignesh! / Your role: developer
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is JSX, and how does it get compiled to JavaScript?

**Answer:**

JSX stands for **JavaScript XML**. It is a declarative syntax extension that allows you to write markup that *looks* like HTML inside JavaScript files. JSX is not understood by browsers or Node.js natively — it must be compiled (transpiled) into regular JavaScript before execution.

**Before React 17 (classic runtime):**

Every JSX element was compiled into a `React.createElement()` call. This is why you needed `import React from 'react'` at the top of every file that contained JSX, even if you never referenced `React` directly.

```jsx
// You write:
const element = <h1 className="title">Hello</h1>;

// Babel compiles it to (classic runtime):
const element = React.createElement('h1', { className: 'title' }, 'Hello');
```

`React.createElement` returns a plain JavaScript object (a "React element") that looks roughly like:

```jsx
{
  type: 'h1',
  props: {
    className: 'title',
    children: 'Hello'
  },
  key: null,
  ref: null,
  // ... internal fields
}
```

**React 17+ (automatic JSX runtime):**

With the new JSX transform, the compiler automatically imports helper functions from `react/jsx-runtime`. You no longer need to import React manually just for JSX.

```jsx
// You write (no React import needed):
const element = <h1 className="title">Hello</h1>;

// Babel/SWC compiles it to:
import { jsx as _jsx } from 'react/jsx-runtime';
const element = _jsx('h1', { className: 'title', children: 'Hello' });
```

**Why this matters in interviews:**
- It explains why component names must be **capitalized** — lowercase tags compile to strings (`'div'`), uppercase tags compile to variable references (`MyComponent`).
- It explains why you can only use **expressions** inside `{}` — they become function arguments.
- It explains why JSX attributes use `className` instead of `class` — they map to JavaScript object properties.

---

### Q2. What are functional components, and why are they preferred over class components in React 18?

**Answer:**

A **functional component** is a plain JavaScript function that accepts a `props` object as its argument and returns JSX (React elements). A **class component** extends `React.Component` and defines a `render()` method.

```jsx
// Functional component (modern, preferred)
function Welcome({ name }) {
  return <h1>Welcome, {name}</h1>;
}

// Class component (legacy)
class Welcome extends React.Component {
  render() {
    return <h1>Welcome, {this.props.name}</h1>;
  }
}
```

**Why functional components are preferred in React 18:**

1. **Hooks provide full parity:** Since React 16.8, hooks (`useState`, `useEffect`, `useContext`, `useRef`, etc.) give functional components every capability that previously required classes — state management, lifecycle effects, context consumption, imperative handles, and more.

2. **Simpler mental model:** No `this` binding issues. In class components, you must carefully bind event handlers or use arrow functions to avoid `this` being `undefined`. Functional components use closures, which are more intuitive.

3. **Better optimization:** Functional components are easier for React to optimize. They work seamlessly with `React.memo()` for memoization, and they don't carry the overhead of class instances.

4. **Hooks can't be used in classes:** Custom hooks — the primary way to share stateful logic — only work in functional components.

5. **Concurrent features require functions:** React 18's concurrent features (automatic batching, transitions, Suspense improvements) are designed around functional components and hooks. Server Components are also function-based.

6. **Less boilerplate:** No constructor, no `this.state`, no `this.setState`, no lifecycle method juggling.

```jsx
// Production example: a functional component using multiple hooks
import { useState, useEffect, useCallback } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => {
        if (!cancelled) {
          setUser(data);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [userId]);

  if (loading) return <Skeleton />;
  if (!user) return <EmptyState message="User not found" />;

  return (
    <Card>
      <Avatar src={user.avatar} alt={user.name} />
      <h2>{user.name}</h2>
      <p>{user.bio}</p>
    </Card>
  );
}
```

**Bottom line:** Unless you are maintaining a legacy codebase, there is no reason to write class components in React 18.

---

### Q3. How do you pass, receive, and destructure props in a functional component? What are default props?

**Answer:**

Props are passed to components as JSX attributes and received as a single object argument. Destructuring is the idiomatic way to extract individual prop values.

**Passing props:**

```jsx
<UserCard
  name="Vignesh"
  age={28}
  isAdmin={true}
  hobbies={['reading', 'coding']}
  onEdit={handleEdit}
/>
```

**Receiving props (three common styles):**

```jsx
// Style 1: Destructure in the parameter list (most common, preferred)
function UserCard({ name, age, isAdmin, hobbies, onEdit }) {
  return <div>{name} — {age}</div>;
}

// Style 2: Receive the full props object
function UserCard(props) {
  return <div>{props.name} — {props.age}</div>;
}

// Style 3: Destructure with rest (useful for forwarding remaining props)
function UserCard({ name, age, ...rest }) {
  return <div {...rest}>{name} — {age}</div>;
}
```

**Default props (three approaches):**

```jsx
// Approach 1: Default parameter values (recommended for functional components)
function UserCard({ name = "Anonymous", role = "viewer" }) {
  return <p>{name} ({role})</p>;
}

// Approach 2: defaultProps (legacy, still works but not recommended for new code)
function UserCard({ name, role }) {
  return <p>{name} ({role})</p>;
}
UserCard.defaultProps = {
  name: "Anonymous",
  role: "viewer",
};

// Approach 3: Nullish coalescing inside the body
function UserCard({ name, role }) {
  const displayName = name ?? "Anonymous";
  const displayRole = role ?? "viewer";
  return <p>{displayName} ({displayRole})</p>;
}
```

**Important nuance:** ES6 default parameters only kick in when the value is `undefined`, not when it is `null`. If a parent explicitly passes `name={null}`, the default `"Anonymous"` will NOT be used. Use nullish coalescing (`??`) if you need to handle both `null` and `undefined`.

```jsx
// Demonstrating the undefined vs null gotcha
function Badge({ label = "Default" }) {
  return <span>{label}</span>;
}

<Badge />              // renders: "Default" (label is undefined)
<Badge label={null} /> // renders: nothing (null, NOT "Default")
```

---

### Q4. What is `React.Fragment`, and why does it matter?

**Answer:**

`React.Fragment` lets you group multiple elements without adding an extra DOM node. Every component must return a single root element, and before Fragments, you had to wrap sibling elements in a `<div>` — polluting the DOM, breaking CSS layouts (Flexbox/Grid), and causing invalid HTML (e.g., a `<div>` inside a `<tr>`).

```jsx
// Problem: extra <div> wrapper breaks table layout
function TableRow({ data }) {
  return (
    <div>           {/* ← Invalid inside <table> */}
      <td>{data.name}</td>
      <td>{data.age}</td>
    </div>
  );
}

// Solution: React.Fragment adds no DOM node
function TableRow({ data }) {
  return (
    <React.Fragment>
      <td>{data.name}</td>
      <td>{data.age}</td>
    </React.Fragment>
  );
}

// Shorthand syntax (most common)
function TableRow({ data }) {
  return (
    <>
      <td>{data.name}</td>
      <td>{data.age}</td>
    </>
  );
}
```

**When you need the full `<React.Fragment>` syntax:**

The only time you cannot use the shorthand `<>...</>` is when you need to pass a `key` — which happens when rendering lists of fragments:

```jsx
function DefinitionList({ items }) {
  return (
    <dl>
      {items.map(item => (
        <React.Fragment key={item.id}>
          <dt>{item.term}</dt>
          <dd>{item.definition}</dd>
        </React.Fragment>
      ))}
    </dl>
  );
}
```

**Production scenarios where Fragments are essential:**
- Table components (`<tr>` cannot have `<div>` children)
- CSS Grid/Flexbox layouts (extra wrappers break direct child selectors)
- Accessibility (screen readers may misinterpret extra `<div>`s)
- Definition lists (`<dl>` expects `<dt>/<dd>` pairs as direct children)

---

### Q5. What are the rules for embedding expressions in JSX? Why can't you use `if` statements inside `{}`?

**Answer:**

Inside JSX curly braces `{}`, you can use any valid JavaScript **expression** — something that evaluates to a value. You **cannot** use **statements** (like `if`, `for`, `while`, `switch`) because JSX compiles to function arguments, and you cannot pass a statement as a function argument.

```jsx
// ✅ Valid: Expressions inside {}
<h1>{user.firstName + ' ' + user.lastName}</h1>      // string concatenation
<p>{isLoggedIn ? 'Welcome back' : 'Please log in'}</p> // ternary
<p>{count > 0 && <Badge count={count} />}</p>          // logical AND
<p>{formatDate(new Date())}</p>                         // function call
<ul>{items.map(item => <li key={item.id}>{item.name}</li>)}</ul> // .map()

// ❌ Invalid: Statements inside {}
<p>{if (isLoggedIn) { return 'Welcome' }}</p>          // SyntaxError
<ul>{for (let item of items) { <li>{item}</li> }}</ul> // SyntaxError
```

**How to handle conditional rendering without `if`:**

```jsx
function StatusMessage({ status }) {
  // Approach 1: Ternary operator (two branches)
  return <p>{status === 'success' ? '✓ Done' : '⏳ Pending'}</p>;

  // Approach 2: Logical AND (show or hide)
  return <p>{status === 'error' && <Alert message="Something failed" />}</p>;

  // Approach 3: Early return / if-else BEFORE the JSX
  if (status === 'loading') return <Spinner />;
  if (status === 'error') return <ErrorPage />;
  return <Dashboard />;

  // Approach 4: IIFE (rarely used, but valid)
  return (
    <div>
      {(() => {
        switch (status) {
          case 'loading': return <Spinner />;
          case 'error':   return <ErrorPage />;
          default:        return <Dashboard />;
        }
      })()}
    </div>
  );
}
```

**Gotcha with `&&`:** Be careful with falsy values like `0` and `NaN`. They are valid React renderable values and will appear in the DOM:

```jsx
// Bug: renders "0" in the DOM when count is 0
{count && <Badge count={count} />}

// Fix: explicitly check with a boolean expression
{count > 0 && <Badge count={count} />}
```

---

## Intermediate Level (Q6–Q12)

---

### Q6. Explain props spreading (`{...props}`). When is it useful, and what are its dangers?

**Answer:**

Props spreading uses the JavaScript spread operator to forward an entire object as props to a component or DOM element.

```jsx
// Basic spreading
const buttonProps = { type: 'submit', disabled: true, className: 'btn' };
<button {...buttonProps}>Submit</button>

// Equivalent to:
<button type="submit" disabled={true} className="btn">Submit</button>
```

**When it is useful:**

1. **Forwarding props in wrapper components** — you extract the props you need and forward the rest to a child:

```jsx
function PrimaryButton({ variant, size, ...rest }) {
  const classes = `btn btn-${variant} btn-${size}`;
  return <button className={classes} {...rest} />;
}

// Consumer can pass any native button attribute (onClick, disabled, type, aria-*)
<PrimaryButton variant="primary" size="lg" onClick={handleClick} disabled={isSubmitting}>
  Save
</PrimaryButton>
```

2. **HOCs and utility wrappers** that need to be transparent to the wrapped component.

3. **Form libraries** (React Hook Form, Formik) that return props objects to be spread onto inputs.

```jsx
// React Hook Form example
const { register } = useForm();
<input {...register('email', { required: true })} />
```

**Dangers of props spreading:**

1. **Passing invalid HTML attributes to DOM elements:**

```jsx
// Dangerous: all props (including custom ones) are passed to <div>
function Card(props) {
  return <div {...props}>{props.children}</div>;
  // If someone passes <Card onRetry={fn} />, the DOM gets an invalid "onRetry" attribute
  // React will warn: "Unknown prop `onRetry` on <div> tag"
}

// Safe: destructure known custom props, spread the rest
function Card({ onRetry, variant, children, ...domProps }) {
  return <div {...domProps}>{children}</div>;
}
```

2. **Accidental prop overwriting (order matters):**

```jsx
// Bug: user's onClick gets overwritten by the spread
<button onClick={internalHandler} {...props}>Click</button>

// Fix: spread first, then override
<button {...props} onClick={internalHandler}>Click</button>

// Or merge handlers:
<button {...props} onClick={(e) => { props.onClick?.(e); internalHandler(e); }}>
  Click
</button>
```

3. **Security risk** — spreading user-controlled data could inject `dangerouslySetInnerHTML`:

```jsx
// NEVER do this with untrusted data
const userInput = { dangerouslySetInnerHTML: { __html: '<script>alert("xss")</script>' } };
<div {...userInput} />
```

4. **Performance** — spreading can make it harder for React to optimize because it obscures which props actually changed.

**Best practice:** Always destructure the props you own, spread only the remaining `...rest`, and place the spread *before* any props you want to guarantee.

---

### Q7. Explain the `children` prop. What are the different patterns for using it?

**Answer:**

`children` is a special prop in React that contains whatever you place *between* a component's opening and closing tags. It can be any renderable value: a string, a number, JSX elements, an array, a function, or even `null`/`undefined`/`boolean` (which render nothing).

**Pattern 1: Primitive children (text)**

```jsx
function Badge({ children }) {
  return <span className="badge">{children}</span>;
}

<Badge>New</Badge>
// children = "New"
```

**Pattern 2: Element children (JSX)**

```jsx
function Card({ children }) {
  return <div className="card">{children}</div>;
}

<Card>
  <h2>Title</h2>
  <p>Description</p>
</Card>
// children = [<h2>Title</h2>, <p>Description</p>]
```

**Pattern 3: Function as children (render prop via children)**

This is a powerful pattern where the child is a function that receives data from the parent:

```jsx
function MouseTracker({ children }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handler = (e) => setPosition({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  return <div className="tracker">{children(position)}</div>;
}

// Usage
<MouseTracker>
  {({ x, y }) => <p>Mouse is at ({x}, {y})</p>}
</MouseTracker>
```

**Pattern 4: Using `React.Children` utilities**

React provides utilities to work with `children` safely because `children` can be a single element, an array, or `undefined`:

```jsx
function Tabs({ children }) {
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <div>
      <div className="tab-headers">
        {React.Children.map(children, (child, index) => (
          <button
            className={index === activeIndex ? 'active' : ''}
            onClick={() => setActiveIndex(index)}
          >
            {child.props.label}
          </button>
        ))}
      </div>
      <div className="tab-content">
        {React.Children.toArray(children)[activeIndex]}
      </div>
    </div>
  );
}

function Tab({ label, children }) {
  return <div>{children}</div>;
}

// Usage
<Tabs>
  <Tab label="Profile"><ProfileForm /></Tab>
  <Tab label="Settings"><SettingsForm /></Tab>
  <Tab label="Billing"><BillingInfo /></Tab>
</Tabs>
```

**Pattern 5: Named slots via explicit props (alternative to children)**

When you need multiple "slots," use named props instead of a single `children`:

```jsx
function PageLayout({ header, sidebar, children, footer }) {
  return (
    <div className="layout">
      <header>{header}</header>
      <aside>{sidebar}</aside>
      <main>{children}</main>
      <footer>{footer}</footer>
    </div>
  );
}

<PageLayout
  header={<NavBar />}
  sidebar={<SideMenu />}
  footer={<FooterLinks />}
>
  <DashboardContent />
</PageLayout>
```

---

### Q8. Component composition vs inheritance — why does React favor composition?

**Answer:**

React's official guidance is: **"Use composition instead of inheritance."** In thousands of components built at Facebook (Meta), they found zero cases where they'd recommend inheritance hierarchies.

**What is composition?**

Composition means building complex UIs by combining simpler components. A parent component controls *what* children render by passing them as props or JSX children.

```jsx
// Composition: a Dialog is composed of generic parts
function Dialog({ title, children, actions }) {
  return (
    <div className="dialog-overlay">
      <div className="dialog" role="dialog" aria-labelledby="dialog-title">
        <h2 id="dialog-title">{title}</h2>
        <div className="dialog-body">{children}</div>
        {actions && <div className="dialog-actions">{actions}</div>}
      </div>
    </div>
  );
}

// Specialization: specific dialogs are just Dialog with specific content
function ConfirmDeleteDialog({ itemName, onConfirm, onCancel }) {
  return (
    <Dialog
      title="Confirm Deletion"
      actions={
        <>
          <Button variant="ghost" onClick={onCancel}>Cancel</Button>
          <Button variant="danger" onClick={onConfirm}>Delete {itemName}</Button>
        </>
      }
    >
      <p>Are you sure you want to delete <strong>{itemName}</strong>? This action cannot be undone.</p>
    </Dialog>
  );
}

function UnsavedChangesDialog({ onSave, onDiscard, onCancel }) {
  return (
    <Dialog
      title="Unsaved Changes"
      actions={
        <>
          <Button variant="ghost" onClick={onDiscard}>Discard</Button>
          <Button variant="ghost" onClick={onCancel}>Cancel</Button>
          <Button variant="primary" onClick={onSave}>Save</Button>
        </>
      }
    >
      <p>You have unsaved changes. What would you like to do?</p>
    </Dialog>
  );
}
```

**Why not inheritance?**

```jsx
// ❌ Anti-pattern: Using inheritance (this is how you'd do it in OOP, not React)
class Dialog extends React.Component {
  render() {
    return (
      <div className="dialog">
        <h2>{this.getTitle()}</h2>
        <div>{this.renderBody()}</div>
      </div>
    );
  }
}

class ConfirmDeleteDialog extends Dialog {
  getTitle() { return "Confirm Deletion"; }
  renderBody() { return <p>Are you sure?</p>; }
}
// Problems:
// - Tightly coupled — changing Dialog's render breaks subclasses
// - No hooks — inheritance only works with classes
// - Hard to compose — what if you want a Dialog inside a Modal inside a Drawer?
// - Fragile base class problem — adding a method to Dialog might clash with subclass methods
```

**Composition patterns that replace inheritance:**

| Inheritance concept | Composition equivalent |
|---|---|
| Base class with abstract methods | Component with slot props (`children`, `header`, `footer`) |
| Subclass overriding methods | Wrapper component passing different props |
| Mixins | Custom hooks |
| Protected methods | Context or callback props |

**Production example — extensible component via composition:**

```jsx
// A DataTable that is composed, not inherited
function DataTable({ columns, data, emptyState, rowAction, header }) {
  if (data.length === 0) return emptyState ?? <p>No data available.</p>;

  return (
    <div>
      {header}
      <table>
        <thead>
          <tr>{columns.map(col => <th key={col.key}>{col.label}</th>)}</tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.id} onClick={() => rowAction?.(row)}>
              {columns.map(col => <td key={col.key}>{col.render(row)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Usage — no subclassing needed; just different props
<DataTable
  columns={userColumns}
  data={users}
  emptyState={<EmptyUsersIllustration />}
  rowAction={(user) => navigate(`/users/${user.id}`)}
  header={<SearchBar onSearch={handleSearch} />}
/>
```

---

### Q9. How do PropTypes compare to TypeScript for prop validation? Which should you use in production?

**Answer:**

Both PropTypes and TypeScript validate component props, but they work at fundamentally different stages and provide different levels of safety.

**PropTypes (runtime validation):**

```jsx
import PropTypes from 'prop-types';

function UserCard({ name, age, role, onEdit }) {
  return (
    <div>
      <h3>{name}</h3>
      <p>Age: {age} | Role: {role}</p>
      <button onClick={onEdit}>Edit</button>
    </div>
  );
}

UserCard.propTypes = {
  name: PropTypes.string.isRequired,
  age: PropTypes.number,
  role: PropTypes.oneOf(['admin', 'editor', 'viewer']),
  onEdit: PropTypes.func.isRequired,
};

UserCard.defaultProps = {
  age: 0,
  role: 'viewer',
};
```

**TypeScript (compile-time validation):**

```jsx
interface UserCardProps {
  name: string;
  age?: number;
  role?: 'admin' | 'editor' | 'viewer';
  onEdit: () => void;
}

function UserCard({ name, age = 0, role = 'viewer', onEdit }: UserCardProps) {
  return (
    <div>
      <h3>{name}</h3>
      <p>Age: {age} | Role: {role}</p>
      <button onClick={onEdit}>Edit</button>
    </div>
  );
}
```

**Comparison table:**

| Aspect | PropTypes | TypeScript |
|---|---|---|
| **When it catches errors** | Runtime (in browser console) | Compile time (in editor/CI) |
| **Feedback loop** | Slow (run app → see console warning) | Instant (red squiggles as you type) |
| **Stripped in production** | Yes (via babel plugin) | Yes (types don't exist at runtime) |
| **Autocomplete/IntelliSense** | No | Yes |
| **Refactoring support** | No | Yes (rename prop → updates all usages) |
| **Complex types** | Limited (custom validators are verbose) | Full power (generics, unions, mapped types) |
| **Bundle size** | Adds ~2KB (prop-types package) | Zero runtime cost |
| **Works with JS** | Yes | Requires `.tsx` / `tsconfig` |

**Recommendation for production:**

Use **TypeScript**. It has become the industry standard for React applications. The developer experience is vastly superior — you get instant feedback, autocomplete, refactoring tools, and the type system catches entire categories of bugs that PropTypes cannot (like passing the wrong shape of an object, or forgetting to handle a union member).

```jsx
// TypeScript catches this at compile time — PropTypes only catches at runtime
interface NotificationProps {
  type: 'success' | 'warning' | 'error';
  message: string;
  onDismiss?: () => void;
}

function Notification({ type, message, onDismiss }: NotificationProps) {
  return (
    <div className={`notification notification-${type}`} role="alert">
      <p>{message}</p>
      {onDismiss && <button onClick={onDismiss} aria-label="Dismiss">×</button>}
    </div>
  );
}

// ❌ TypeScript error: Type '"info"' is not assignable to type '"success" | "warning" | "error"'
<Notification type="info" message="Hello" />
```

PropTypes still has a niche: if you maintain a JavaScript (non-TypeScript) library consumed by other JavaScript projects, PropTypes provide runtime safety for consumers who don't use TypeScript.

---

### Q10. How should you structure component files in a large-scale React application?

**Answer:**

There is no single "correct" structure, but battle-tested patterns have emerged. The key principle is: **colocation** — keep related code close together and organize by feature/domain, not by file type.

**Anti-pattern: Organizing by file type (avoid in large apps):**

```
src/
  components/
    UserCard.tsx
    ProductCard.tsx
    OrderList.tsx
    CheckoutForm.tsx    ← 200 components in one flat folder
  hooks/
    useUser.ts
    useProduct.ts
  utils/
    formatUser.ts
    formatProduct.ts
```

This breaks down quickly because related files are scattered across directories.

**Recommended: Feature-based structure with colocation:**

```
src/
  features/
    auth/
      components/
        LoginForm.tsx
        LoginForm.test.tsx
        SignupForm.tsx
        PasswordStrengthMeter.tsx
      hooks/
        useAuth.ts
        useSession.ts
      utils/
        validateCredentials.ts
      types.ts
      index.ts              ← public API barrel file

    dashboard/
      components/
        DashboardLayout.tsx
        MetricsCard.tsx
        ActivityFeed.tsx
      hooks/
        useDashboardData.ts
      index.ts

    orders/
      components/
        OrderList.tsx
        OrderDetail.tsx
        OrderFilters.tsx
      hooks/
        useOrders.ts
        useOrderMutation.ts
      api/
        orderApi.ts
      types.ts
      index.ts

  shared/                   ← truly shared/reusable code
    components/
      ui/                   ← design system primitives
        Button/
          Button.tsx
          Button.test.tsx
          Button.stories.tsx
          index.ts
        Input/
        Modal/
        Toast/
      layout/
        PageLayout.tsx
        Sidebar.tsx
    hooks/
      useDebounce.ts
      useMediaQuery.ts
      useClickOutside.ts
    utils/
      formatDate.ts
      cn.ts                 ← className merge utility
    types/
      common.ts

  app/                      ← app-level setup
    routes.tsx
    providers.tsx
    App.tsx
```

**Key principles:**

```jsx
// Barrel files (index.ts) define the public API of each feature
// features/auth/index.ts
export { LoginForm } from './components/LoginForm';
export { SignupForm } from './components/SignupForm';
export { useAuth } from './hooks/useAuth';
export type { User, Session } from './types';

// Other features import from the barrel, not internal paths
// features/dashboard/components/DashboardLayout.tsx
import { useAuth } from '@/features/auth'; // ✅ Clean import
// import { useAuth } from '@/features/auth/hooks/useAuth'; // ❌ Reaches into internals
```

**Component file structure (for complex components):**

```
Button/
  Button.tsx          ← component implementation
  Button.test.tsx     ← tests
  Button.stories.tsx  ← Storybook stories
  Button.module.css   ← scoped styles (or .styled.ts)
  index.ts            ← re-export: export { Button } from './Button'
```

This structure scales to hundreds of features and thousands of components because each feature is self-contained, changes are localized, and the codebase remains navigable.

---

### Q11. What are controlled vs uncontrolled components? When would you use each?

**Answer:**

This distinction is about **who owns the source of truth** for a form element's value — React state (controlled) or the DOM itself (uncontrolled).

**Controlled component:** React state drives the value. Every change goes through a state update cycle.

```jsx
function ControlledInput() {
  const [email, setEmail] = useState('');

  const handleChange = (e) => {
    // You control the value — you can validate, format, or reject changes
    const value = e.target.value.toLowerCase().trim();
    setEmail(value);
  };

  return (
    <input
      type="email"
      value={email}           // React owns the value
      onChange={handleChange}  // Every keystroke updates state
      placeholder="Enter email"
    />
  );
}
```

**Uncontrolled component:** The DOM owns the value. You read it when you need it (e.g., on submit) using a ref.

```jsx
function UncontrolledInput() {
  const emailRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Read the value from the DOM when needed
    console.log('Email:', emailRef.current.value);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        ref={emailRef}            // DOM owns the value
        defaultValue=""           // Initial value only (not continuously controlled)
        placeholder="Enter email"
      />
      <button type="submit">Submit</button>
    </form>
  );
}
```

**Comparison:**

| Aspect | Controlled | Uncontrolled |
|---|---|---|
| Source of truth | React state | DOM |
| Validation timing | On every change | On submit / on blur |
| Instant feedback | Yes (can show errors as user types) | No (until you read the ref) |
| Programmatic value changes | Easy (`setState`) | Harder (manipulate ref) |
| Performance with many fields | Re-renders on every keystroke | No re-renders until submit |
| Integration with React ecosystem | Native | Requires refs |

**Production example — a form with both patterns:**

```jsx
import { useState, useRef } from 'react';

function ProfileForm({ onSave }) {
  // Controlled: we need real-time validation
  const [username, setUsername] = useState('');
  const [usernameError, setUsernameError] = useState('');

  // Uncontrolled: file inputs MUST be uncontrolled (you can't set file input value)
  const avatarRef = useRef(null);

  const handleUsernameChange = (e) => {
    const value = e.target.value;
    setUsername(value);
    if (value.length < 3) {
      setUsernameError('Username must be at least 3 characters');
    } else if (!/^[a-zA-Z0-9_]+$/.test(value)) {
      setUsernameError('Only letters, numbers, and underscores');
    } else {
      setUsernameError('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (usernameError) return;

    const formData = new FormData();
    formData.append('username', username);
    if (avatarRef.current.files[0]) {
      formData.append('avatar', avatarRef.current.files[0]);
    }
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          value={username}
          onChange={handleUsernameChange}
        />
        {usernameError && <span className="error">{usernameError}</span>}
      </div>

      <div>
        <label htmlFor="avatar">Avatar</label>
        <input id="avatar" type="file" ref={avatarRef} accept="image/*" />
      </div>

      <button type="submit" disabled={!!usernameError}>
        Save Profile
      </button>
    </form>
  );
}
```

**When to use each:**
- **Controlled:** When you need instant validation, conditional disabling, value formatting, or your UI depends on the current input value.
- **Uncontrolled:** File inputs, integrating with non-React code, or performance-critical forms with hundreds of fields. Libraries like React Hook Form use uncontrolled inputs internally for better performance.

---

### Q12. How does `React.createElement` work internally? Walk through what happens from JSX to DOM.

**Answer:**

Understanding the full pipeline from JSX to pixels helps you debug, optimize, and reason about React at a deeper level.

**Step 1: JSX → React.createElement (compile time)**

```jsx
// Your JSX:
<div className="card">
  <h2>{title}</h2>
  <Button onClick={handleClick}>Save</Button>
</div>

// Compiles to (classic runtime):
React.createElement(
  'div',
  { className: 'card' },
  React.createElement('h2', null, title),
  React.createElement(Button, { onClick: handleClick }, 'Save')
);
```

**Step 2: React.createElement → React Element (runtime)**

`React.createElement(type, props, ...children)` does very little — it's essentially a *validated object factory*:

```jsx
// Simplified implementation of React.createElement
function createElement(type, config, ...children) {
  const props = {};

  // Copy config to props, separating reserved keys
  let key = null;
  let ref = null;

  if (config != null) {
    if (config.key !== undefined) key = '' + config.key;
    if (config.ref !== undefined) ref = config.ref;

    for (const prop in config) {
      if (config.hasOwnProperty(prop) && prop !== 'key' && prop !== 'ref') {
        props[prop] = config[prop];
      }
    }
  }

  // Handle children
  if (children.length === 1) {
    props.children = children[0];
  } else if (children.length > 1) {
    props.children = children;
  }

  // Apply defaultProps
  if (type && type.defaultProps) {
    for (const prop in type.defaultProps) {
      if (props[prop] === undefined) {
        props[prop] = type.defaultProps[prop];
      }
    }
  }

  // Return a React element (just a plain object!)
  return {
    $$typeof: Symbol.for('react.element'), // Security: prevents JSON injection
    type,    // 'div', 'h2', Button (function reference)
    key,
    ref,
    props,
  };
}
```

**Step 3: React Element → Fiber Node (reconciliation)**

React's reconciler (called "Fiber") takes the tree of React elements and builds/updates an internal **Fiber tree**. Each Fiber node tracks:
- The component type and props
- Current state and hooks
- Pointers to parent, child, and sibling fibers
- Effect flags (needs update, needs deletion, etc.)

**Step 4: Fiber Tree → DOM mutations (commit phase)**

After reconciliation determines *what* changed, the commit phase applies the minimal set of DOM mutations:

```jsx
// Conceptual flow:
// JSX → createElement() → React Element (object) → Fiber Node → DOM Node

// The $$typeof field is crucial for security:
// JSON.parse cannot produce Symbol values, so even if an attacker injects
// JSON into your data, React will refuse to render it as an element
// because it won't have $$typeof: Symbol.for('react.element')
```

**Why this matters in production:**

1. **Key prop:** React uses `key` during reconciliation to match old and new elements. Without keys (or with index keys), React may reuse the wrong DOM nodes and cause bugs.

2. **Component identity:** If `type` changes between renders (e.g., you define a component inline), React unmounts and remounts — destroying all state.

```jsx
// ❌ Bug: new function reference every render → remounts Input → loses focus
function Form() {
  const StyledInput = (props) => <input className="styled" {...props} />;
  return <StyledInput />;
}

// ✅ Fix: define outside the render
const StyledInput = (props) => <input className="styled" {...props} />;
function Form() {
  return <StyledInput />;
}
```

3. **`$$typeof` prevents XSS:** If your server returns user-generated JSON and you accidentally render it as JSX, the absence of `Symbol.for('react.element')` means React will refuse to treat it as an element.

---

## Advanced Level (Q13–Q20)

---

### Q13. Compare Higher-Order Components (HOCs), Render Props, and Custom Hooks for sharing cross-cutting logic. When would you still use each?

**Answer:**

All three patterns solve the same problem — **sharing stateful or behavioral logic** across components — but they have very different ergonomics, composability, and tradeoffs.

**Pattern 1: Higher-Order Component (HOC)**

A function that takes a component and returns a new enhanced component:

```jsx
function withAuth(WrappedComponent) {
  return function AuthenticatedComponent(props) {
    const { user, isLoading } = useAuth();

    if (isLoading) return <Spinner />;
    if (!user) return <Navigate to="/login" />;

    return <WrappedComponent {...props} user={user} />;
  };
}

// Usage
const ProtectedDashboard = withAuth(Dashboard);
<ProtectedDashboard someProp="value" />
```

**Pattern 2: Render Props**

A component that takes a function as a prop (or children) and calls it with data:

```jsx
function AuthGate({ children, fallback = <Navigate to="/login" /> }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <Spinner />;
  if (!user) return fallback;

  return children(user);
}

// Usage
<AuthGate>
  {(user) => <Dashboard user={user} />}
</AuthGate>
```

**Pattern 3: Custom Hook (recommended)**

A function that encapsulates stateful logic using built-in hooks:

```jsx
function useAuth() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    authService.onAuthStateChanged((user) => {
      setUser(user);
      setIsLoading(false);
    });
  }, []);

  const login = useCallback(async (credentials) => {
    return authService.signIn(credentials);
  }, []);

  const logout = useCallback(async () => {
    return authService.signOut();
  }, []);

  return { user, isLoading, login, logout };
}

// Usage — clean, composable, no wrapper nesting
function Dashboard() {
  const { user, isLoading, logout } = useAuth();

  if (isLoading) return <Spinner />;
  if (!user) return <Navigate to="/login" />;

  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <button onClick={logout}>Log out</button>
    </div>
  );
}
```

**Detailed comparison:**

| Aspect | HOC | Render Props | Custom Hooks |
|---|---|---|---|
| Composability | Wrapper hell with multiple HOCs | Callback hell with nesting | Flat — just call multiple hooks |
| TypeScript support | Hard (complex generics for prop injection) | Medium | Excellent (standard function types) |
| Debugging (DevTools) | Extra wrapper components in tree | Extra wrapper components | No extra components |
| Static analysis | Props are injected magically | Explicit data flow | Explicit return values |
| Can share non-UI logic | Yes (but adds wrapper) | Not well (requires a component) | Yes (pure logic, no JSX) |
| Server Components | Not compatible | Not compatible | Compatible |

**When you'd still use each in 2024+:**

- **Custom hooks:** Default choice for 95% of cases. Sharing data fetching, form logic, subscriptions, animations, etc.
- **Render props:** When the *parent* needs to control what renders based on child state (e.g., headless UI libraries like Downshift, Radix primitives).
- **HOCs:** Rarely. Some legacy patterns (like `connect()` from old Redux) and route-level wrappers. Can still be useful for adding behavior to third-party components you don't control.

```jsx
// Production example: composing multiple hooks (no wrapper hell)
function OrderPage({ orderId }) {
  const { user } = useAuth();
  const { order, isLoading, error } = useOrder(orderId);
  const { track } = useAnalytics();
  const { toast } = useToast();

  useEffect(() => {
    track('order_viewed', { orderId });
  }, [orderId, track]);

  // Compare this to: withAuth(withOrder(withAnalytics(withToast(OrderPage))))
  // Hooks are dramatically cleaner!
}
```

---

### Q14. How does `React.lazy` work for component lazy loading? What are the production considerations?

**Answer:**

`React.lazy` enables **code splitting** at the component level. It takes a function that returns a dynamic `import()` and renders the component only when it's needed, loading the JavaScript bundle on demand.

```jsx
import { lazy, Suspense } from 'react';

// The import() call tells the bundler (webpack/Vite/esbuild) to create a separate chunk
const AdminPanel = lazy(() => import('./features/admin/AdminPanel'));
const Analytics = lazy(() => import('./features/analytics/Analytics'));
const Settings = lazy(() => import('./features/settings/Settings'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/admin" element={<AdminPanel />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

**How it works internally:**

1. `React.lazy()` returns a special "lazy" component object.
2. On first render, React calls the factory function (`() => import(...)`) which returns a Promise.
3. React **suspends** rendering — it throws the Promise up to the nearest `<Suspense>` boundary.
4. `<Suspense>` catches the thrown Promise and shows the `fallback` while waiting.
5. When the Promise resolves, React re-renders and the loaded component appears.
6. Subsequent renders use the cached module — no re-fetching.

**Production considerations:**

**1. Error handling with Error Boundaries:**

```jsx
import { Component, lazy, Suspense } from 'react';

class ChunkErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  handleRetry = () => {
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="chunk-error">
          <p>Failed to load this section.</p>
          <button onClick={this.handleRetry}>Retry</button>
        </div>
      );
    }
    return this.props.children;
  }
}

const HeavyChart = lazy(() => import('./HeavyChart'));

function Dashboard() {
  return (
    <ChunkErrorBoundary>
      <Suspense fallback={<ChartSkeleton />}>
        <HeavyChart data={chartData} />
      </Suspense>
    </ChunkErrorBoundary>
  );
}
```

**2. Preloading chunks (avoid loading spinners):**

```jsx
const AdminPanel = lazy(() => import('./AdminPanel'));

// Preload when the user hovers over the nav link
function NavLink({ to, children, preloadComponent }) {
  return (
    <Link
      to={to}
      onMouseEnter={() => preloadComponent?.()}
      onFocus={() => preloadComponent?.()}
    >
      {children}
    </Link>
  );
}

// The preload function — calling import() starts the download
const preloadAdmin = () => import('./AdminPanel');

<NavLink to="/admin" preloadComponent={preloadAdmin}>
  Admin Panel
</NavLink>
```

**3. Named exports (React.lazy requires default exports):**

```jsx
// If your module uses named exports, wrap the import:
const UserProfile = lazy(() =>
  import('./UserProfile').then(module => ({ default: module.UserProfile }))
);
```

**4. Route-level vs component-level splitting:**

```jsx
// Route-level splitting (most common, biggest impact)
const routes = [
  { path: '/dashboard', component: lazy(() => import('./pages/Dashboard')) },
  { path: '/reports',   component: lazy(() => import('./pages/Reports')) },
];

// Component-level splitting (for heavy widgets within a page)
function ProductPage({ product }) {
  const [showReviews, setShowReviews] = useState(false);
  const Reviews = lazy(() => import('./Reviews'));

  return (
    <div>
      <ProductInfo product={product} />
      <button onClick={() => setShowReviews(true)}>Show Reviews</button>
      {showReviews && (
        <Suspense fallback={<ReviewsSkeleton />}>
          <Reviews productId={product.id} />
        </Suspense>
      )}
    </div>
  );
}
```

**Important:** Never define `lazy()` calls inside a component render. The factory would be recreated on every render, causing the component to unmount and remount. Always define lazy components at module scope or in a stable reference.

---

### Q15. Explain the Compound Component pattern. How do you implement it with React context and props?

**Answer:**

The **Compound Component pattern** allows a set of components to work together implicitly, sharing state internally while presenting a clean, declarative API to the consumer. Think of how `<select>` and `<option>` work in HTML — `<option>` implicitly knows about the `<select>` it belongs to.

**Production example: an Accordion component:**

```jsx
import { createContext, useContext, useState, useCallback, useId } from 'react';

// 1. Create a shared context
const AccordionContext = createContext(null);

function useAccordionContext() {
  const context = useContext(AccordionContext);
  if (!context) {
    throw new Error('Accordion compound components must be used within <Accordion>');
  }
  return context;
}

// 2. Parent component provides context
function Accordion({ children, multiple = false, defaultOpenItems = [] }) {
  const [openItems, setOpenItems] = useState(new Set(defaultOpenItems));

  const toggle = useCallback((itemId) => {
    setOpenItems(prev => {
      const next = new Set(multiple ? prev : []);
      if (prev.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  }, [multiple]);

  const isOpen = useCallback((itemId) => openItems.has(itemId), [openItems]);

  return (
    <AccordionContext.Provider value={{ toggle, isOpen }}>
      <div className="accordion" role="presentation">
        {children}
      </div>
    </AccordionContext.Provider>
  );
}

// 3. Child components consume context
function AccordionItem({ children, itemId }) {
  const generatedId = useId();
  const id = itemId ?? generatedId;
  const { isOpen } = useAccordionContext();

  return (
    <div className={`accordion-item ${isOpen(id) ? 'is-open' : ''}`} data-item-id={id}>
      {typeof children === 'function' ? children({ isOpen: isOpen(id), id }) : children}
    </div>
  );
}

function AccordionTrigger({ children, itemId }) {
  const { toggle, isOpen } = useAccordionContext();
  const contentId = `accordion-content-${itemId}`;

  return (
    <button
      className="accordion-trigger"
      onClick={() => toggle(itemId)}
      aria-expanded={isOpen(itemId)}
      aria-controls={contentId}
    >
      {children}
      <span className="accordion-chevron" aria-hidden="true">
        {isOpen(itemId) ? '▲' : '▼'}
      </span>
    </button>
  );
}

function AccordionContent({ children, itemId }) {
  const { isOpen } = useAccordionContext();
  const contentId = `accordion-content-${itemId}`;

  if (!isOpen(itemId)) return null;

  return (
    <div className="accordion-content" id={contentId} role="region">
      {children}
    </div>
  );
}

// 4. Attach sub-components for clean API
Accordion.Item = AccordionItem;
Accordion.Trigger = AccordionTrigger;
Accordion.Content = AccordionContent;
```

**Consumer usage — clean and declarative:**

```jsx
function FAQ() {
  return (
    <Accordion multiple defaultOpenItems={['q1']}>
      <Accordion.Item itemId="q1">
        <Accordion.Trigger itemId="q1">
          What is your return policy?
        </Accordion.Trigger>
        <Accordion.Content itemId="q1">
          <p>You can return items within 30 days of purchase...</p>
        </Accordion.Content>
      </Accordion.Item>

      <Accordion.Item itemId="q2">
        <Accordion.Trigger itemId="q2">
          How long does shipping take?
        </Accordion.Trigger>
        <Accordion.Content itemId="q2">
          <p>Standard shipping takes 5-7 business days...</p>
        </Accordion.Content>
      </Accordion.Item>
    </Accordion>
  );
}
```

**Why this pattern is powerful:**

- **Implicit state sharing:** Consumer doesn't need to manage open/close state.
- **Flexible layout:** Consumer controls the structure and can insert custom elements between compound children.
- **Encapsulation:** Internal state management is hidden. The consumer only needs the declarative API.
- **Used by major libraries:** Radix UI, Reach UI, Headless UI, and Chakra UI all use this pattern extensively.

---

### Q16. What is the polymorphic component pattern (the `as` prop)? How do you implement it with type safety?

**Answer:**

A **polymorphic component** can render as different HTML elements or other components depending on a prop — typically called `as` or `component`. This is crucial in design systems where a `Button` might need to render as an `<a>` tag for navigation, or a `Text` component might render as `<p>`, `<span>`, `<h1>`, etc.

**Basic implementation (JavaScript):**

```jsx
function Box({ as: Component = 'div', children, ...rest }) {
  return <Component {...rest}>{children}</Component>;
}

// Usage
<Box>Default div</Box>
<Box as="section">Renders as section</Box>
<Box as="a" href="/about">Renders as anchor</Box>
<Box as={Link} to="/about">Renders as React Router Link</Box>
```

**The type-safety challenge:**

Without TypeScript, there's no guarantee that the props you pass match the element you render as. You could pass `href` to a `<div>` without any warning.

**Type-safe implementation (TypeScript):**

```jsx
import { ComponentPropsWithoutRef, ElementType, ReactNode } from 'react';

// Generic type: C is the element type (defaults to 'div')
type BoxProps<C extends ElementType = 'div'> = {
  as?: C;
  children?: ReactNode;
} & Omit<ComponentPropsWithoutRef<C>, 'as' | 'children'>;

function Box<C extends ElementType = 'div'>({
  as,
  children,
  ...rest
}: BoxProps<C>) {
  const Component = as || 'div';
  return <Component {...rest}>{children}</Component>;
}

// ✅ TypeScript knows <a> accepts href
<Box as="a" href="/about">Link</Box>

// ✅ TypeScript knows <button> accepts onClick and type
<Box as="button" onClick={() => {}} type="submit">Submit</Box>

// ❌ TypeScript error: Property 'href' does not exist on type for 'div'
<Box href="/about">Broken</Box>

// ❌ TypeScript error: Property 'href' does not exist on type for 'button'
<Box as="button" href="/about">Also broken</Box>
```

**Production example — a polymorphic `Text` component for a design system:**

```jsx
import { ComponentPropsWithoutRef, ElementType, forwardRef, ReactNode } from 'react';

type TextVariant = 'h1' | 'h2' | 'h3' | 'body' | 'caption' | 'label';

const variantStyles: Record<TextVariant, string> = {
  h1: 'text-4xl font-bold tracking-tight',
  h2: 'text-2xl font-semibold',
  h3: 'text-xl font-medium',
  body: 'text-base',
  caption: 'text-sm text-gray-500',
  label: 'text-sm font-medium',
};

const defaultElements: Record<TextVariant, ElementType> = {
  h1: 'h1',
  h2: 'h2',
  h3: 'h3',
  body: 'p',
  caption: 'span',
  label: 'label',
};

type TextProps<C extends ElementType> = {
  as?: C;
  variant?: TextVariant;
  children: ReactNode;
} & Omit<ComponentPropsWithoutRef<C>, 'as' | 'variant' | 'children'>;

function Text<C extends ElementType = 'p'>({
  as,
  variant = 'body',
  children,
  className = '',
  ...rest
}: TextProps<C>) {
  const Component = as || defaultElements[variant];
  const classes = `${variantStyles[variant]} ${className}`.trim();

  return (
    <Component className={classes} {...rest}>
      {children}
    </Component>
  );
}

// Usage
<Text variant="h1">Page Title</Text>                  // renders <h1>
<Text variant="body">Paragraph text</Text>             // renders <p>
<Text variant="body" as="span">Inline text</Text>      // renders <span>
<Text variant="label" as="label" htmlFor="email">       // renders <label> with htmlFor
  Email
</Text>
```

**Why this pattern is essential for design systems:**
- A single `Button` component can work as `<button>`, `<a>`, or a router `<Link>` without duplicating styling logic.
- A `Card` component can render as `<article>`, `<section>`, or `<li>` depending on semantic context.
- It enforces correct prop usage through TypeScript — you can't pass `href` to a button.

---

### Q17. How would you design a component API for a production design system? What principles guide your decisions?

**Answer:**

Designing component APIs for a design system is one of the highest-leverage activities in frontend engineering. A well-designed API accelerates development, enforces consistency, and prevents misuse. A poorly designed one becomes a permanent tax on every developer.

**Core principles:**

**1. Constrain the design tokens, liberate the composition:**

```jsx
// ❌ Bad: too flexible — allows any value, impossible to maintain consistency
<Button color="#3b82f6" fontSize="14px" padding="8px 16px" />

// ✅ Good: constrained to design tokens
<Button variant="primary" size="md" />
```

```jsx
// Implementation
type ButtonProps = {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
  disabled?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  children: ReactNode;
} & Omit<ComponentPropsWithoutRef<'button'>, 'className'>;

function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled = false,
  leftIcon,
  rightIcon,
  children,
  ...nativeProps
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      className={cn(
        'btn',
        `btn-${variant}`,
        `btn-${size}`,
        fullWidth && 'btn-full',
        loading && 'btn-loading'
      )}
      disabled={isDisabled}
      aria-busy={loading}
      {...nativeProps}
    >
      {loading ? <Spinner size={size} /> : leftIcon}
      <span>{children}</span>
      {!loading && rightIcon}
    </button>
  );
}
```

**2. Forward refs and spread native props:**

```jsx
// Design system components MUST forward refs and native HTML attributes
const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, size = 'md', ...nativeProps }, ref) => {
    const id = useId();

    return (
      <div className={cn('input-group', error && 'input-group-error')}>
        {label && <label htmlFor={id}>{label}</label>}
        <input
          ref={ref}
          id={id}
          className={cn('input', `input-${size}`)}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          {...nativeProps}
        />
        {error && <p id={`${id}-error`} className="input-error" role="alert">{error}</p>}
        {!error && hint && <p id={`${id}-hint`} className="input-hint">{hint}</p>}
      </div>
    );
  }
);
```

**3. Composition over configuration:**

```jsx
// ❌ Over-configured: one component tries to do everything
<Card
  title="User Profile"
  subtitle="Active since 2020"
  avatar="/img/user.jpg"
  actions={[{ label: 'Edit', onClick: handleEdit }]}
  footer="Last updated: yesterday"
  badge="Pro"
/>

// ✅ Composable: each part is a separate component
<Card>
  <Card.Header>
    <Avatar src="/img/user.jpg" />
    <div>
      <Card.Title>User Profile</Card.Title>
      <Card.Subtitle>Active since 2020</Card.Subtitle>
    </div>
    <Badge>Pro</Badge>
  </Card.Header>
  <Card.Body>
    {/* Consumer controls the content */}
  </Card.Body>
  <Card.Footer>
    <Button onClick={handleEdit}>Edit</Button>
  </Card.Footer>
</Card>
```

**4. Accessibility by default:**

```jsx
// The component handles ARIA attributes so consumers don't have to
function Alert({ variant = 'info', children, dismissible, onDismiss }) {
  return (
    <div
      role="alert"
      aria-live={variant === 'error' ? 'assertive' : 'polite'}
      className={cn('alert', `alert-${variant}`)}
    >
      <AlertIcon variant={variant} />
      <div className="alert-content">{children}</div>
      {dismissible && (
        <button onClick={onDismiss} aria-label="Dismiss alert" className="alert-dismiss">
          <CloseIcon />
        </button>
      )}
    </div>
  );
}
```

**5. Design the API around usage, not implementation:**

Write the consumer code *first*, then implement the component:

```jsx
// Step 1: Write how you WANT to use it
<Combobox value={selected} onChange={setSelected}>
  <Combobox.Input placeholder="Search countries..." />
  <Combobox.Options>
    {countries.map(c => (
      <Combobox.Option key={c.code} value={c}>
        <Flag code={c.code} /> {c.name}
      </Combobox.Option>
    ))}
  </Combobox.Options>
</Combobox>

// Step 2: Implement to match this API
```

---

### Q18. What are the performance implications of inline JSX vs extracted components? When does it matter?

**Answer:**

This question tests deep understanding of React's reconciliation algorithm and when micro-optimizations actually matter.

**Inline JSX:**

```jsx
function ProductPage({ products }) {
  return (
    <div>
      {products.map(product => (
        // Inline JSX — NOT a separate component
        <div key={product.id} className="product-card">
          <img src={product.image} alt={product.name} />
          <h3>{product.name}</h3>
          <p>${product.price}</p>
        </div>
      ))}
    </div>
  );
}
```

**Extracted component:**

```jsx
function ProductCard({ product }) {
  return (
    <div className="product-card">
      <img src={product.image} alt={product.name} />
      <h3>{product.name}</h3>
      <p>${product.price}</p>
    </div>
  );
}

function ProductPage({ products }) {
  return (
    <div>
      {products.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
```

**Performance comparison:**

| Aspect | Inline JSX | Extracted Component |
|---|---|---|
| createElement calls | Same number | Same number |
| Reconciliation | Diffs the JSX tree | Diffs the component tree |
| React.memo possible | No | Yes |
| Re-render scope | Always re-renders with parent | Can skip with memo |
| Code readability | Worse for complex markup | Better separation of concerns |

**When it matters — `React.memo`:**

The key difference is that extracted components can be wrapped in `React.memo()` to skip re-renders when their props haven't changed.

```jsx
// This component only re-renders when `product` changes
const ProductCard = React.memo(function ProductCard({ product }) {
  console.log(`Rendering ${product.name}`);
  return (
    <div className="product-card">
      <img src={product.image} alt={product.name} />
      <h3>{product.name}</h3>
      <p>${product.price}</p>
    </div>
  );
});

function ProductPage({ products, sortOrder }) {
  // When sortOrder changes, ProductPage re-renders
  // But individual ProductCards skip re-rendering if their product prop is the same
  const sorted = useMemo(
    () => [...products].sort(comparators[sortOrder]),
    [products, sortOrder]
  );

  return (
    <div>
      <SortControls value={sortOrder} />
      {sorted.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
```

**The critical anti-pattern — components defined inside render:**

```jsx
// ❌ CRITICAL BUG: Component defined inside render creates a new type every render
function Parent() {
  // New function reference every render → React treats it as a new component type
  // → unmounts and remounts → all internal state is LOST
  function Child() {
    const [count, setCount] = useState(0); // resets to 0 every parent render!
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
  }

  return <Child />;
}

// ✅ Fix: Define component outside
function Child() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}

function Parent() {
  return <Child />;
}
```

**When to extract vs inline — practical guidelines:**

- **Extract** when: the markup is complex, you need `React.memo`, the component has its own state/hooks, or it's reused.
- **Inline** is fine for: simple, non-reusable markup that doesn't need memoization (e.g., a few `<li>` elements in a short list).
- **Never define components inside render functions.** This is not an optimization question — it causes bugs.

---

### Q19. Explain React Server Components vs Client Components. What are the rules around the props serialization boundary?

**Answer:**

React Server Components (RSC), introduced experimentally in React 18 and stabilized in frameworks like Next.js 13+, represent a fundamental shift in React architecture. They split the component tree into two environments: **server** and **client**.

**Server Components (default in Next.js App Router):**

```jsx
// app/users/page.tsx — Server Component (no 'use client' directive)
// Runs ONLY on the server, never shipped to the browser

import { db } from '@/lib/database';

async function UsersPage() {
  // Direct database access — no API needed!
  const users = await db.query('SELECT * FROM users ORDER BY name');

  return (
    <div>
      <h1>Users ({users.length})</h1>
      <UserList users={users} />
      <AddUserButton />  {/* This is a Client Component */}
    </div>
  );
}

export default UsersPage;
```

**Client Components:**

```jsx
// app/users/AddUserButton.tsx
'use client'; // This directive marks it as a Client Component

import { useState } from 'react';

function AddUserButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Add User</button>
      {isOpen && <UserFormModal onClose={() => setIsOpen(false)} />}
    </>
  );
}
```

**The serialization boundary — the critical concept:**

When a Server Component renders a Client Component, it must pass props across a **network boundary** (server → client). These props are serialized as JSON and sent in the RSC payload. This means:

**Serializable (can cross the boundary):**
- Primitives: `string`, `number`, `boolean`, `null`, `undefined`
- Plain objects and arrays (containing serializable values)
- `Date` objects (serialized as ISO strings)
- Server Actions (special async functions with `'use server'`)
- React elements (JSX) — Server Components can pass pre-rendered JSX as props!

**NOT serializable (cannot cross the boundary):**
- Functions (except Server Actions)
- Classes / class instances
- Symbols
- DOM nodes
- Closures
- `Map`, `Set`, `WeakMap`, `WeakSet`
- Event handlers (`onClick`, `onChange`)

```jsx
// ✅ Valid: passing serializable data across the boundary
// Server Component
async function ProductPage({ params }) {
  const product = await getProduct(params.id);

  return (
    <div>
      <h1>{product.name}</h1>
      {/* String, number, boolean — all serializable */}
      <AddToCartButton
        productId={product.id}
        price={product.price}
        inStock={product.stock > 0}
      />
    </div>
  );
}

// ❌ Invalid: passing a function across the boundary
async function ProductPage({ params }) {
  const product = await getProduct(params.id);

  return (
    <AddToCartButton
      productId={product.id}
      // ERROR: Functions are not serializable
      onAddToCart={() => addToCart(product.id)}
    />
  );
}

// ✅ Fix: use a Server Action
// actions.ts
'use server';
export async function addToCartAction(productId: string) {
  await db.cart.add({ productId, userId: getCurrentUser().id });
  revalidatePath('/cart');
}

// Server Component
import { addToCartAction } from './actions';

async function ProductPage({ params }) {
  const product = await getProduct(params.id);

  return (
    <AddToCartButton
      productId={product.id}
      addToCartAction={addToCartAction} // Server Action — serializable!
    />
  );
}
```

**Passing pre-rendered JSX (Server Components as props):**

```jsx
// Server Component
async function Dashboard() {
  const metrics = await getMetrics();

  // Pre-rendered JSX can be passed as a prop — it's already a React element
  return (
    <DashboardLayout
      sidebar={<ServerRenderedSidebar data={metrics} />}
    >
      <InteractiveCharts />
    </DashboardLayout>
  );
}

// Client Component
'use client';
function DashboardLayout({ sidebar, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="dashboard">
      {sidebarOpen && <aside>{sidebar}</aside>} {/* Server-rendered content! */}
      <main>{children}</main>
    </div>
  );
}
```

**Key mental model:**

Think of the Server/Client boundary like a REST API. Everything crossing it must be JSON-serializable. Server Components are like the backend that queries data. Client Components are like the frontend that handles interactivity. The RSC protocol is the transport layer between them.

---

### Q20. Build a fully type-safe polymorphic component that supports `ref` forwarding. Walk through the TypeScript generics involved.

**Answer:**

This is the "final boss" of React TypeScript challenges. A type-safe polymorphic component with ref forwarding requires advanced generics to ensure that: (a) the props match the rendered element, (b) the `ref` type matches the element, and (c) custom props don't collide with native props.

**Step-by-step implementation:**

**Step 1: Define the core generic types**

```jsx
import {
  ElementType,
  ComponentPropsWithRef,
  forwardRef,
  ReactNode,
  ForwardedRef,
} from 'react';

/**
 * Extracts the ref type for a given element type.
 * For 'button' → HTMLButtonElement, for 'a' → HTMLAnchorElement, etc.
 */
type ElementRef<C extends ElementType> =
  ComponentPropsWithRef<C> extends { ref?: infer R } ? R : never;

/**
 * The base props for our polymorphic component.
 * C is the element type generic parameter.
 */
type PolymorphicProps<
  C extends ElementType,
  CustomProps = {}
> = CustomProps & {
  as?: C;
  children?: ReactNode;
} & Omit<
  ComponentPropsWithRef<C>,
  keyof CustomProps | 'as' | 'children'
>;
```

**Step 2: Build a reusable polymorphic `forwardRef` helper**

```jsx
/**
 * A type-safe forwardRef wrapper for polymorphic components.
 * This is needed because React's forwardRef doesn't support generic components
 * out of the box — it "locks in" the generic when you call forwardRef.
 */
type PolymorphicComponent<
  DefaultElement extends ElementType,
  CustomProps = {}
> = <C extends ElementType = DefaultElement>(
  props: PolymorphicProps<C, CustomProps> & { ref?: ForwardedRef<ElementRef<C>> }
) => ReactNode;
```

**Step 3: Implement a production `Box` component**

```jsx
type BoxCustomProps = {
  padding?: 'none' | 'sm' | 'md' | 'lg';
  radius?: 'none' | 'sm' | 'md' | 'lg' | 'full';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
};

const paddingMap = { none: '', sm: 'p-2', md: 'p-4', lg: 'p-8' };
const radiusMap = { none: '', sm: 'rounded-sm', md: 'rounded-md', lg: 'rounded-lg', full: 'rounded-full' };
const shadowMap = { none: '', sm: 'shadow-sm', md: 'shadow-md', lg: 'shadow-lg' };

export const Box: PolymorphicComponent<'div', BoxCustomProps> = forwardRef(
  function Box<C extends ElementType = 'div'>(
    {
      as,
      padding = 'none',
      radius = 'none',
      shadow = 'none',
      className,
      children,
      ...rest
    }: PolymorphicProps<C, BoxCustomProps>,
    ref: ForwardedRef<any>
  ) {
    const Component = as || 'div';
    const classes = [
      paddingMap[padding],
      radiusMap[radius],
      shadowMap[shadow],
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <Component ref={ref} className={classes || undefined} {...rest}>
        {children}
      </Component>
    );
  }
) as any; // The final `as any` is needed because forwardRef's types can't express generics
```

**Step 4: Demonstrate type safety in action**

```jsx
function App() {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const anchorRef = useRef<HTMLAnchorElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <>
      {/* ✅ Renders as <div>, ref is HTMLDivElement */}
      <Box padding="md" radius="lg" shadow="sm">
        Default div box
      </Box>

      {/* ✅ Renders as <button>, accepts button-specific props */}
      <Box
        as="button"
        ref={buttonRef}
        padding="sm"
        radius="md"
        type="submit"
        onClick={(e) => {
          // e is React.MouseEvent<HTMLButtonElement>
          console.log('clicked', e.currentTarget.form);
        }}
      >
        Submit Button
      </Box>

      {/* ✅ Renders as <a>, accepts anchor-specific props */}
      <Box
        as="a"
        ref={anchorRef}
        href="https://example.com"
        target="_blank"
        rel="noopener noreferrer"
        padding="sm"
      >
        External Link
      </Box>

      {/* ✅ Renders as <input>, accepts input-specific props */}
      <Box
        as="input"
        ref={inputRef}
        type="email"
        placeholder="Enter email"
        padding="sm"
        radius="md"
        onChange={(e) => {
          // e is React.ChangeEvent<HTMLInputElement>
          console.log(e.target.value);
        }}
      />

      {/* ❌ TypeScript error: href is not valid on <button> */}
      {/* <Box as="button" href="/about">Broken</Box> */}

      {/* ❌ TypeScript error: type 'HTMLAnchorElement' is not assignable to 'HTMLButtonElement' */}
      {/* <Box as="button" ref={anchorRef}>Broken</Box> */}
    </>
  );
}
```

**Step 5: Extend for a concrete design system component**

```jsx
type ButtonCustomProps = {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
};

export const Button: PolymorphicComponent<'button', ButtonCustomProps> = forwardRef(
  function Button<C extends ElementType = 'button'>(
    {
      as,
      variant = 'primary',
      size = 'md',
      loading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      className,
      ...rest
    }: PolymorphicProps<C, ButtonCustomProps>,
    ref: ForwardedRef<any>
  ) {
    const Component = as || 'button';
    const isDisabled = disabled || loading;

    return (
      <Component
        ref={ref}
        disabled={Component === 'button' ? isDisabled : undefined}
        aria-disabled={isDisabled}
        aria-busy={loading}
        className={`btn btn-${variant} btn-${size} ${className ?? ''}`}
        {...rest}
      >
        {loading ? <Spinner size={size} /> : leftIcon}
        <span>{children}</span>
        {!loading && rightIcon}
      </Component>
    );
  }
) as any;

// Usage:
// As a button (default)
<Button variant="primary" onClick={save}>Save</Button>

// As a link (anchor tag) — gets href, target, etc.
<Button as="a" variant="ghost" href="/settings">Settings</Button>

// As a React Router Link — gets 'to' prop
<Button as={Link} variant="secondary" to="/dashboard">Dashboard</Button>
```

**Why this matters for senior engineers:**

- Design systems at companies like Shopify (Polaris), GitHub (Primer), and Atlassian (Atlaskit) all use polymorphic components.
- It demonstrates mastery of TypeScript generics, React's type system, and component API design.
- The `forwardRef` + generics limitation is a known pain point in React's TypeScript support — understanding the workaround (`as any` assertion) shows you've hit real-world edges.
- React's team is working on making `ref` a regular prop (removing the need for `forwardRef`), which will simplify this pattern in future versions.

---

## Summary

| # | Topic | Level |
|---|---|---|
| Q1 | JSX compilation (createElement / jsx runtime) | Beginner |
| Q2 | Functional vs class components | Beginner |
| Q3 | Props: passing, destructuring, defaults | Beginner |
| Q4 | React.Fragment | Beginner |
| Q5 | JSX expressions vs statements | Beginner |
| Q6 | Props spreading and its dangers | Intermediate |
| Q7 | The children prop (multiple patterns) | Intermediate |
| Q8 | Composition vs inheritance | Intermediate |
| Q9 | PropTypes vs TypeScript | Intermediate |
| Q10 | Component file structure in large apps | Intermediate |
| Q11 | Controlled vs uncontrolled components | Intermediate |
| Q12 | React.createElement internals | Intermediate |
| Q13 | HOC vs render props vs hooks | Advanced |
| Q14 | React.lazy and code splitting | Advanced |
| Q15 | Compound component pattern | Advanced |
| Q16 | Polymorphic components (as prop) | Advanced |
| Q17 | Component API design for design systems | Advanced |
| Q18 | Inline JSX vs extracted components performance | Advanced |
| Q19 | Server Components vs Client Components | Advanced |
| Q20 | Type-safe polymorphic component with ref | Advanced |
