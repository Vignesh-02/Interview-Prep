# React Server Components (RSC) — React 18/19 Interview Questions

## Topic Introduction

**React Server Components (RSC)** represent the most significant architectural shift in React since hooks. Introduced experimentally in React 18 and stabilized in React 19, Server Components are a new kind of component that **runs exclusively on the server** — they never ship JavaScript to the browser, never re-render on the client, and have direct access to server-side resources like databases, file systems, and internal APIs. Unlike traditional Server-Side Rendering (SSR), which renders the *same* components on both server and client (and then "hydrates" the client-side copy so it becomes interactive), Server Components produce a **serialized React tree** (an intermediate wire format, not HTML) that the client can merge into its existing component tree without needing the component's source code at all. This means heavy dependencies used inside a Server Component — think `marked` for Markdown parsing, `highlight.js` for syntax highlighting, or `date-fns` for date formatting — contribute **zero bytes** to the client-side JavaScript bundle. The result is dramatically smaller bundles, faster page loads, and a cleaner separation between data-fetching logic and interactive UI logic.

The key mental model is that React now has **two component runtimes**: one on the server and one on the client. Server Components run in the server runtime, Client Components run in both (server for SSR, then client for hydration and interactivity). The boundary between them is defined by the `'use client'` directive — any module that starts with `'use client'` becomes a Client Component, and everything it imports also runs on the client. Conversely, `'use server'` marks **Server Actions** — asynchronous functions that can be called from Client Components and execute on the server (useful for form submissions, mutations, and data writes). This two-runtime model is fundamentally different from SSR: SSR renders a snapshot of HTML for faster first paint and then downloads the same JavaScript to make it interactive; RSC **never sends the Server Component code to the client at all**. The server streams a compact description of the rendered tree, and the client stitches it together with the Client Components it already has. Understanding this distinction — RSC is about **what code runs where**, while SSR is about **when HTML is generated** — is the single most important conceptual leap for modern React interviews.

In production, RSC is most commonly used via **Next.js App Router** (13.4+), which makes every component a Server Component by default. Vercel, Shopify, and other large-scale platforms have adopted RSC for performance-critical pages such as product listings, dashboards, and content-heavy marketing sites. React 19 (stable since December 2024) fully supports RSC as a first-class feature, and the ecosystem — including bundlers like Turbopack and frameworks like Remix — is rapidly converging on this model. For 2026 interviews, RSC is not a "nice to know" — it is the **core architectural pattern** that interviewers expect senior React engineers to deeply understand, reason about, and build with.

```jsx
// The fundamental difference in one glance:

// ---- Server Component (default in Next.js App Router) ----
// This file has NO 'use client' directive, so it's a Server Component.
// It can directly await data, access the DB, and import heavy libs —
// NONE of this code ships to the browser.

import { db } from '@/lib/database';
import { formatDistanceToNow } from 'date-fns';  // 0 bytes on client!

export default async function RecentOrders() {
  const orders = await db.order.findMany({
    take: 10,
    orderBy: { createdAt: 'desc' },
    include: { customer: true },
  });

  return (
    <section>
      <h2>Recent Orders</h2>
      <ul>
        {orders.map((order) => (
          <li key={order.id}>
            {order.customer.name} — ${order.total.toFixed(2)}
            <span className="text-muted">
              {formatDistanceToNow(order.createdAt, { addSuffix: true })}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

// ---- Client Component (interactive) ----
'use client';

import { useState } from 'react';

export function OrderFilter({ children }) {
  const [status, setStatus] = useState('all');

  return (
    <div>
      <select value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="all">All</option>
        <option value="pending">Pending</option>
        <option value="shipped">Shipped</option>
      </select>
      {children}  {/* Server Component output can be passed as children */}
    </div>
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What are React Server Components, and how do they differ from traditional Server-Side Rendering (SSR)?

**Answer:**

React Server Components (RSC) are a component type that **executes exclusively on the server**. They produce a serialized React tree (a special wire format, not HTML) that is sent to the client, where it is integrated into the client-side React tree. The component's source code, its dependencies, and any server-only logic (database queries, file reads, etc.) are **never shipped to the browser**.

Traditional SSR, by contrast, renders the **same** components on the server to produce an HTML string for faster first paint, but then the client downloads all the JavaScript for those components and "hydrates" them — attaching event handlers and re-initializing state. After hydration, SSR components are fully client-side components.

**Key differences:**

| Aspect | SSR | RSC |
|---|---|---|
| **Code sent to client** | All component JS is sent (for hydration) | Server Component JS is **never** sent |
| **Interactivity** | Full (after hydration) | None — SC cannot have state or handlers |
| **Re-renders on client** | Yes (after hydration) | No — only re-fetched from server |
| **Bundle size impact** | Same as CSR (all deps shipped) | Zero-bundle-size for SC deps |
| **Output format** | HTML string | Serialized React tree (RSC payload) |
| **Data fetching** | useEffect, getServerSideProps, loaders | Direct async/await inside the component |

```jsx
// SSR component — this code ships to the client for hydration
// Even though it renders on the server first, the browser still
// downloads highlight.js (~200KB) for hydration.
import hljs from 'highlight.js';

export default function CodeBlock({ code, language }) {
  const html = hljs.highlight(code, { language }).value;
  return <pre dangerouslySetInnerHTML={{ __html: html }} />;
}

// RSC equivalent — highlight.js NEVER reaches the client
// No 'use client' directive = Server Component by default (in Next.js)
import hljs from 'highlight.js';

export default function CodeBlock({ code, language }) {
  const html = hljs.highlight(code, { language }).value;
  return <pre dangerouslySetInnerHTML={{ __html: html }} />;
}
// The code looks identical, but the RSC version sends only the rendered
// <pre> tag in the RSC payload — not the hljs library.
```

**Why this matters:** In a traditional SSR app with a 300KB syntax-highlighting library, every visitor downloads that 300KB even though the highlighting is already done on the server. With RSC, that 300KB never leaves the server. Multiply this across a dozen heavy dependencies and you can cut client bundles by 50–80%.

---

### Q2. What do the `'use client'` and `'use server'` directives mean?

**Answer:**

These are **module-level directives** (similar to `'use strict'`) that tell the React bundler which runtime a module belongs to.

**`'use client'`** — placed at the very top of a file, it marks that module (and everything it imports) as a **Client Component**. Client Components can use hooks (`useState`, `useEffect`, etc.), attach event handlers, and access browser APIs. They are the familiar interactive React components. In the Next.js App Router, components are Server Components by default, so you add `'use client'` only when you need interactivity.

**`'use server'`** — has two uses:
1. At the **top of a file**: marks every exported function in that file as a **Server Action** — an async function that executes on the server but can be called from Client Components (e.g., in form `action` props or `onClick` handlers).
2. **Inline inside an async function** (inside a Server Component): marks that specific function as a Server Action.

Server Actions are the RSC answer to API routes for mutations — they handle form submissions, database writes, and other side effects without needing a separate API layer.

```jsx
// --- file: components/LikeButton.tsx ---
'use client';  // <-- This is a Client Component

import { useState, useTransition } from 'react';
import { likePost } from '@/actions/social';  // Server Action

export function LikeButton({ postId, initialLikes }) {
  const [likes, setLikes] = useState(initialLikes);
  const [isPending, startTransition] = useTransition();

  const handleLike = () => {
    startTransition(async () => {
      const updatedLikes = await likePost(postId);  // Calls the server
      setLikes(updatedLikes);
    });
  };

  return (
    <button onClick={handleLike} disabled={isPending}>
      ❤️ {likes} {isPending ? '...' : ''}
    </button>
  );
}

// --- file: actions/social.ts ---
'use server';  // <-- Every export in this file is a Server Action

import { db } from '@/lib/database';
import { revalidatePath } from 'next/cache';

export async function likePost(postId: string) {
  const post = await db.post.update({
    where: { id: postId },
    data: { likes: { increment: 1 } },
  });
  revalidatePath(`/posts/${postId}`);
  return post.likes;
}
```

**Important nuances:**
- `'use client'` does NOT mean the component only runs on the client — it still runs on the server during SSR. It means the component is part of the **client bundle** and can hydrate.
- `'use server'` does NOT make a component a Server Component — it creates a Server Action (an RPC endpoint).
- You cannot use `'use client'` and `'use server'` in the same file.

---

### Q3. When should you use a Server Component vs. a Client Component?

**Answer:**

The decision comes down to a simple question: **does this component need interactivity or browser APIs?**

**Use a Server Component when:**
- The component only displays data (read-only UI)
- You need to fetch data from a database, file system, or internal API
- You use heavy libraries for rendering (Markdown parsers, syntax highlighters, date formatters)
- You want to keep secrets (API keys, DB connection strings) off the client
- The component does not need `useState`, `useEffect`, `useRef`, or event handlers

**Use a Client Component when:**
- The component needs state (`useState`, `useReducer`)
- The component needs lifecycle effects (`useEffect`, `useLayoutEffect`)
- The component attaches event handlers (`onClick`, `onChange`, `onSubmit`)
- The component uses browser-only APIs (`window`, `localStorage`, `IntersectionObserver`)
- The component uses third-party libraries that depend on client-side APIs (e.g., animation libraries, rich text editors)

**The golden rule:** Default to Server Components. Only add `'use client'` when you hit a specific need for interactivity. Push the `'use client'` boundary as far down the tree as possible — wrap only the smallest interactive leaf, not an entire page.

```jsx
// ✅ GOOD: Granular client boundary — only the interactive part is a Client Component

// page.tsx (Server Component — default)
import { db } from '@/lib/database';
import { AddToCartButton } from './AddToCartButton';

export default async function ProductPage({ params }) {
  const product = await db.product.findUnique({ where: { slug: params.slug } });

  return (
    <article>
      <h1>{product.name}</h1>
      <p>{product.description}</p>             {/* Static — Server Component */}
      <span>${product.price.toFixed(2)}</span>  {/* Static — Server Component */}
      <AddToCartButton productId={product.id} /> {/* Interactive — Client Component */}
    </article>
  );
}

// AddToCartButton.tsx (Client Component)
'use client';

import { useState } from 'react';
import { addToCart } from '@/actions/cart';

export function AddToCartButton({ productId }) {
  const [added, setAdded] = useState(false);

  return (
    <button
      onClick={async () => {
        await addToCart(productId);
        setAdded(true);
      }}
    >
      {added ? 'Added ✓' : 'Add to Cart'}
    </button>
  );
}

// ❌ BAD: Entire page is a Client Component just because the button needs state
'use client';
import { useState, useEffect } from 'react';

export default function ProductPage({ params }) {
  const [product, setProduct] = useState(null);

  useEffect(() => {
    fetch(`/api/products/${params.slug}`).then(r => r.json()).then(setProduct);
  }, [params.slug]);
  // Now ALL of this page's code ships to the client...
}
```

---

### Q4. What are the limitations of Server Components? What can you NOT do inside them?

**Answer:**

Server Components run **once** on the server and produce a static (serialized) output. They do not participate in the client-side React lifecycle. This means they cannot use any feature that requires client-side state, effects, or browser interaction.

**You CANNOT use inside a Server Component:**

| Feature | Why |
|---|---|
| `useState`, `useReducer` | SC has no client-side state |
| `useEffect`, `useLayoutEffect` | SC has no lifecycle — it runs once |
| `useRef` (for DOM refs) | SC output is serialized, not a live DOM |
| Event handlers (`onClick`, etc.) | SC doesn't exist on the client to handle events |
| Browser APIs (`window`, `document`, `localStorage`) | SC runs on the server, no browser |
| `createContext` / `useContext` | Context is a client-side feature (but you can read context values passed via props) |
| CSS-in-JS that requires runtime (`styled-components` without SSR config) | Requires browser runtime |
| Custom hooks that use any of the above | Transitively forbidden |

**You CAN do inside a Server Component:**

- `async/await` (Server Components can be async functions!)
- Direct database queries
- File system access (`fs.readFile`)
- Access environment variables and secrets
- Import and use heavy libraries (zero client cost)
- Render Client Components as children
- Pass serializable props to Client Components

```jsx
// Server Component — demonstrating what IS and ISN'T allowed

import { readFile } from 'fs/promises';
import matter from 'gray-matter';       // Heavy Markdown frontmatter parser — 0 bytes on client
import { notFound } from 'next/navigation';

// ✅ Server Components CAN be async
export default async function BlogPost({ params }) {
  let content;
  try {
    const raw = await readFile(`./content/posts/${params.slug}.md`, 'utf-8');
    content = matter(raw);
  } catch {
    notFound();  // ✅ Can use server-side navigation helpers
  }

  // ❌ CANNOT do any of these:
  // const [liked, setLiked] = useState(false);      // No state
  // useEffect(() => { ... });                        // No effects
  // <button onClick={() => setLiked(true)}>Like</button>  // No handlers

  return (
    <article>
      <h1>{content.data.title}</h1>
      <time>{new Date(content.data.date).toLocaleDateString()}</time>
      <div dangerouslySetInnerHTML={{ __html: content.content }} />
    </article>
  );
}
```

**Interview tip:** If an interviewer asks "Can Server Components use hooks?", the nuanced answer is: they cannot use **stateful or effectful hooks** (`useState`, `useEffect`, `useRef`, `useContext`). They can use `use()` (React 19's new hook for reading promises and context), which is designed to work in both server and client contexts.

---

### Q5. How does data fetching work in Server Components compared to Client Components?

**Answer:**

Server Components can **directly `await` asynchronous data** inside the component function body — no `useEffect`, no `useState` for loading states, no waterfall of client-server round-trips. This is the most ergonomic data-fetching model React has ever had.

In Client Components, you still need the traditional patterns: `useEffect` + `useState`, React Query / SWR, or the new `use()` hook with Suspense.

**Server Component data fetching:**
- Component is `async` — you can `await` anywhere
- Data is fetched during rendering on the server
- No loading state needed in the component itself (use `<Suspense>` at the boundary)
- No client-server waterfall — data is already on the server
- Secrets (DB passwords, API keys) stay on the server

**Client Component data fetching:**
- Cannot be `async` (hooks don't support it)
- Requires `useEffect` or a data-fetching library
- Creates a waterfall: render → mount → fetch → re-render
- Must use public API endpoints (no direct DB access)

```jsx
// ---- Server Component: Direct async data fetching ----
import { db } from '@/lib/database';
import { Suspense } from 'react';

// The page itself is a Server Component
export default function DashboardPage() {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Each section fetches independently with its own Suspense boundary */}
      <Suspense fallback={<Skeleton type="revenue" />}>
        <RevenueChart />
      </Suspense>
      <Suspense fallback={<Skeleton type="orders" />}>
        <RecentOrders />
      </Suspense>
    </div>
  );
}

// Server Component — async, direct DB access
async function RevenueChart() {
  const revenue = await db.$queryRaw`
    SELECT DATE_TRUNC('month', created_at) as month, SUM(total) as revenue
    FROM orders
    WHERE created_at > NOW() - INTERVAL '12 months'
    GROUP BY month ORDER BY month
  `;

  // Transform data and return JSX — no useState, no useEffect
  return (
    <div className="chart-container">
      <h3>Revenue (Last 12 Months)</h3>
      {/* Pass serializable data to a Client Component for interactivity */}
      <InteractiveChart data={revenue.map(r => ({
        month: r.month.toISOString(),
        revenue: Number(r.revenue),
      }))} />
    </div>
  );
}

// ---- Client Component: Traditional pattern (for comparison) ----
'use client';

import { useState, useEffect } from 'react';

function RevenueChartClient() {
  const [revenue, setRevenue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/revenue')
      .then((r) => {
        if (!r.ok) throw new Error('Failed');
        return r.json();
      })
      .then(setRevenue)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Skeleton type="revenue" />;
  if (error) return <ErrorMessage error={error} />;

  return <InteractiveChart data={revenue} />;
  // Problem: waterfall — page loads → JS downloads → component mounts → fetch starts
  // With RSC, data is already available when the page streams to the client.
}
```

**Performance impact:** In a dashboard with 5 data panels, the Client Component approach creates a sequential waterfall: HTML → JS download → hydration → 5 parallel fetches → render. With RSC, all 5 queries execute on the server in parallel during rendering, and the results stream to the client as they complete. This can save **seconds** on initial load.

---

## Intermediate Level (Q6–Q12)

---

### Q6. What is the serialization boundary, and what can and cannot be passed across it?

**Answer:**

The **serialization boundary** is the conceptual divide between Server Components and Client Components. When a Server Component renders a Client Component, it must pass props across this boundary. Since those props travel over the network (as part of the RSC payload), they must be **serializable** — convertible to a format that can be transmitted and reconstructed on the client.

**CAN be passed across the boundary (serializable):**
- Primitives: `string`, `number`, `boolean`, `null`, `undefined`, `bigint`
- Plain objects and arrays (containing serializable values)
- `Date` objects (serialized as ISO strings in practice)
- `Map` and `Set` (React 19 supports these in RSC payload)
- **Server Actions** (functions marked with `'use server'`) — serialized as references
- JSX / React elements (serialized as part of the RSC payload)
- `FormData`
- Typed arrays (`Uint8Array`, etc.)

**CANNOT be passed across the boundary:**
- Regular functions / closures (not Server Actions)
- Class instances (custom classes)
- DOM nodes
- Symbols (except well-known ones)
- Streams, WeakMap, WeakSet
- Circular references

```jsx
// Server Component passing props to a Client Component

import { db } from '@/lib/database';
import { UserProfile } from './UserProfile';      // Client Component
import { updateBio } from '@/actions/user';        // Server Action

export default async function UserPage({ params }) {
  const user = await db.user.findUnique({
    where: { id: params.id },
    select: { id: true, name: true, bio: true, createdAt: true },
  });

  return (
    <UserProfile
      // ✅ Serializable props — these all work:
      name={user.name}                        // string
      bio={user.bio}                          // string | null
      joinedAt={user.createdAt.toISOString()} // string (serialize Date manually)
      isAdmin={user.role === 'ADMIN'}         // boolean
      tags={['react', 'typescript']}          // array of strings
      onSaveBio={updateBio}                   // ✅ Server Action — serialized as reference

      // ❌ These would FAIL:
      // formatName={(n) => n.toUpperCase()}  // Regular function — NOT serializable
      // dbConnection={db}                     // Class instance — NOT serializable
      // userInstance={user}                   // Prisma model instance — may contain non-serializable fields
    />
  );
}

// UserProfile.tsx
'use client';

import { useState } from 'react';

export function UserProfile({ name, bio, joinedAt, isAdmin, tags, onSaveBio }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(bio ?? '');

  return (
    <div>
      <h1>{name} {isAdmin && '(Admin)'}</h1>
      <p>Joined: {new Date(joinedAt).toLocaleDateString()}</p>
      <div>{tags.map(t => <span key={t} className="badge">{t}</span>)}</div>

      {editing ? (
        <form action={async () => {
          await onSaveBio(draft);  // Calls the Server Action
          setEditing(false);
        }}>
          <textarea value={draft} onChange={e => setDraft(e.target.value)} />
          <button type="submit">Save</button>
        </form>
      ) : (
        <>
          <p>{bio}</p>
          <button onClick={() => setEditing(true)}>Edit Bio</button>
        </>
      )}
    </div>
  );
}
```

**Common interview pitfall:** A candidate might say "you can't pass functions across the boundary." The nuanced answer is: you can't pass **regular functions**, but you **can** pass **Server Actions** — they are serialized as references and, when called on the client, trigger an HTTP request to the server to execute the actual function.

---

### Q7. How do Server Components achieve zero-bundle-size, and why does this matter at scale?

**Answer:**

Server Components achieve **zero-bundle-size** because their source code and all their unique dependencies are **never included in the client JavaScript bundle**. The bundler (Webpack, Turbopack, or Vite with RSC plugin) treats Server Components differently from Client Components: it does not create chunks for them, does not include them in the client manifest, and does not send their imports to the browser.

When a Server Component runs on the server, it produces a **serialized React tree** (the RSC payload). This payload contains the rendered output — string content, HTML-like element descriptors, and references to Client Components (which ARE in the bundle). The client receives this payload and reconstructs the tree using only the Client Components it already has.

**Why this matters at scale:**

Consider a real-world product page that uses:
- `marked` (40KB) for Markdown rendering
- `highlight.js` (200KB) for code syntax highlighting
- `date-fns` (20KB) for date formatting
- `sanitize-html` (30KB) for HTML sanitization
- `sharp` (native image processing — can't even run in browser)

In a traditional CSR/SSR app, you'd either ship ~290KB of JS to the client or create complex code-splitting strategies. With RSC, all of these run on the server and contribute **0 bytes** to the client bundle.

```jsx
// Server Component — ALL of these imports are zero-cost on the client

import { marked } from 'marked';                    // 40KB — server only
import hljs from 'highlight.js';                     // 200KB — server only
import sanitizeHtml from 'sanitize-html';            // 30KB — server only
import { formatRelative } from 'date-fns';           // 20KB — server only
import { db } from '@/lib/database';                 // Prisma — server only

// Configure marked to use highlight.js
marked.setOptions({
  highlight: (code, lang) => hljs.highlight(code, { language: lang }).value,
});

export default async function BlogPost({ params }) {
  const post = await db.post.findUnique({
    where: { slug: params.slug },
    include: { author: true },
  });

  const htmlContent = sanitizeHtml(marked.parse(post.content), {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(['img', 'pre', 'code']),
  });

  return (
    <article className="prose lg:prose-xl">
      <header>
        <h1>{post.title}</h1>
        <p>
          By {post.author.name} ·{' '}
          {formatRelative(post.publishedAt, new Date())}
        </p>
      </header>
      <div dangerouslySetInnerHTML={{ __html: htmlContent }} />

      {/* Only this tiny Client Component ships JS to the browser */}
      <ShareButtons url={`/blog/${params.slug}`} title={post.title} />
    </article>
  );
}

// Bundle analysis:
// Without RSC: ~290KB+ of JS for page dependencies
// With RSC:    ~3KB (just the ShareButtons component + React runtime)
// That's a 99% reduction in page-specific JavaScript.
```

**Scaling impact:** A large e-commerce site with 50 product attributes, complex pricing logic, inventory calculations, and rich content rendering might have 500KB+ of "rendering logic" JavaScript. With RSC, that logic stays on the server. When you multiply this across hundreds of pages and millions of users, the bandwidth savings alone justify the architectural shift — not to mention faster Time-to-Interactive (TTI) on low-end mobile devices.

---

### Q8. Explain the composition pattern: Server Components wrapping Client Components and vice versa.

**Answer:**

The composition of Server and Client Components follows specific rules that you must internalize:

**Rule 1: Server Components CAN render Client Components.** This is the primary composition direction. A Server Component imports and renders a Client Component, passing serializable props.

**Rule 2: Client Components CANNOT import Server Components.** Once you cross the `'use client'` boundary, everything imported into that file is part of the client bundle. You cannot `import` a Server Component into a Client Component file.

**Rule 3: Client Components CAN render Server Components via `children` or other JSX props.** This is the critical escape hatch. A Server Component can pass another Server Component as the `children` prop to a Client Component. The Client Component doesn't import the Server Component — it just receives pre-rendered JSX.

This third rule enables the powerful **"donut" pattern**: a Client Component provides interactivity (the donut), with a Server Component "hole" in the middle rendered via `children`.

```jsx
// ======= Pattern 1: Server wraps Client (straightforward) =======
// layout.tsx — Server Component
import { Sidebar } from './Sidebar';  // Client Component for interactivity
import { db } from '@/lib/database';

export default async function DashboardLayout({ children }) {
  const user = await db.user.findUnique({ where: { id: getCurrentUserId() } });

  return (
    <div className="flex">
      <Sidebar userName={user.name} role={user.role} />
      <main className="flex-1">{children}</main>
    </div>
  );
}

// Sidebar.tsx — Client Component
'use client';
import { useState } from 'react';

export function Sidebar({ userName, role }) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <nav className={collapsed ? 'w-16' : 'w-64'}>
      <button onClick={() => setCollapsed(!collapsed)}>Toggle</button>
      {!collapsed && <p>Welcome, {userName}</p>}
    </nav>
  );
}

// ======= Pattern 2: The "Donut" — Client wraps Server via children =======
// page.tsx — Server Component
import { TabContainer } from './TabContainer';  // Client Component (interactive tabs)
import { ServerRenderedContent } from './ServerRenderedContent';  // Server Component

export default async function Page() {
  return (
    <TabContainer
      tabs={['Overview', 'Analytics', 'Settings']}
    >
      {/* This Server Component is pre-rendered and passed as children */}
      <ServerRenderedContent />
    </TabContainer>
  );
}

// TabContainer.tsx — Client Component
'use client';
import { useState } from 'react';

export function TabContainer({ tabs, children }) {
  const [activeTab, setActiveTab] = useState(0);
  return (
    <div>
      <div className="tab-bar">
        {tabs.map((tab, i) => (
          <button
            key={tab}
            className={i === activeTab ? 'active' : ''}
            onClick={() => setActiveTab(i)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="tab-content">
        {children}  {/* Server Component output rendered here */}
      </div>
    </div>
  );
}

// ServerRenderedContent.tsx — Server Component (no 'use client')
import { db } from '@/lib/database';

export async function ServerRenderedContent() {
  const stats = await db.analytics.getOverview();
  return (
    <div>
      <p>Total Users: {stats.totalUsers.toLocaleString()}</p>
      <p>Revenue: ${stats.revenue.toFixed(2)}</p>
    </div>
  );
}

// ======= Pattern 3: WRONG — Client importing Server (will NOT work) =======
'use client';
// ❌ This import would pull the Server Component into the client bundle,
// where it will fail (no access to db, fs, etc.)
// import { ServerRenderedContent } from './ServerRenderedContent';
```

**Key takeaway for interviews:** The `children` prop pattern is how you compose Server Components inside Client Components. The Server Component is rendered on the server, its output becomes part of the RSC payload, and the Client Component receives it as opaque JSX — it never needs to know or import the Server Component.

---

### Q9. How do Server Actions work, and how do you call server functions from Client Components?

**Answer:**

**Server Actions** are `async` functions marked with the `'use server'` directive that run on the server but can be invoked from Client Components. Under the hood, React creates an HTTP endpoint for each Server Action. When a Client Component calls the action, it makes a `POST` request to the server, the action executes, and the result is returned to the client. This replaces the need for manually creating API routes for mutations.

Server Actions can be used in two primary ways:
1. **As the `action` prop on `<form>`** — progressive enhancement; works even before JS loads
2. **Called directly** inside event handlers or `useTransition`

Server Actions automatically integrate with React's transition system, providing pending states and optimistic updates.

```jsx
// --- actions/todo.ts ---
'use server';

import { db } from '@/lib/database';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const TodoSchema = z.object({
  title: z.string().min(1).max(200),
  priority: z.enum(['low', 'medium', 'high']),
});

// Server Action: Create a todo
export async function createTodo(formData: FormData) {
  const parsed = TodoSchema.safeParse({
    title: formData.get('title'),
    priority: formData.get('priority'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await db.todo.create({
    data: {
      title: parsed.data.title,
      priority: parsed.data.priority,
      userId: await getCurrentUserId(),  // Server-side auth
    },
  });

  revalidatePath('/todos');
  return { success: true };
}

// Server Action: Delete a todo
export async function deleteTodo(todoId: string) {
  await db.todo.delete({ where: { id: todoId, userId: await getCurrentUserId() } });
  revalidatePath('/todos');
}

// --- components/TodoForm.tsx ---
'use client';

import { useActionState } from 'react';  // React 19 hook
import { createTodo } from '@/actions/todo';

export function TodoForm() {
  // useActionState wraps a Server Action with pending + state management
  const [state, formAction, isPending] = useActionState(
    async (previousState, formData) => {
      const result = await createTodo(formData);
      return result;
    },
    null
  );

  return (
    <form action={formAction}>
      <input
        name="title"
        placeholder="What needs to be done?"
        required
        disabled={isPending}
      />
      <select name="priority" defaultValue="medium">
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>
      <button type="submit" disabled={isPending}>
        {isPending ? 'Adding...' : 'Add Todo'}
      </button>
      {state?.error && (
        <p className="text-red-500">{JSON.stringify(state.error)}</p>
      )}
    </form>
  );
}

// --- components/TodoItem.tsx ---
'use client';

import { useTransition, useOptimistic } from 'react';
import { deleteTodo } from '@/actions/todo';

export function TodoItem({ todo }) {
  const [isPending, startTransition] = useTransition();
  const [optimisticTodo, setOptimisticTodo] = useOptimistic(todo);

  const handleDelete = () => {
    // Optimistic update — immediately mark as deleting
    setOptimisticTodo({ ...todo, deleting: true });
    startTransition(async () => {
      await deleteTodo(todo.id);
    });
  };

  return (
    <li className={optimisticTodo.deleting ? 'opacity-50' : ''}>
      <span>{todo.title}</span>
      <button onClick={handleDelete} disabled={isPending}>
        {isPending ? 'Deleting...' : '🗑️'}
      </button>
    </li>
  );
}
```

**Key Server Action properties:**
- They are **progressively enhanced** — `<form action={serverAction}>` works even without JavaScript
- They run **sequentially** by default (React serializes calls to prevent race conditions)
- They can return values, which are passed back to the calling component
- They can call `revalidatePath()` or `revalidateTag()` to refresh cached data
- They can `redirect()` to navigate the user after a mutation
- They are automatically protected against CSRF attacks (React adds a token)

---

### Q10. How does streaming work with Server Components?

**Answer:**

**Streaming** is the mechanism by which Server Components send their rendered output to the client incrementally, as each piece becomes ready, rather than waiting for the entire page to finish rendering. This is powered by React's integration with `<Suspense>` boundaries and HTTP streaming (chunked transfer encoding).

When a Server Component tree contains `<Suspense>` boundaries, React can:
1. Render the parts of the tree that are immediately available
2. Stream the initial HTML/RSC payload with fallbacks for pending parts
3. As each suspended component resolves (e.g., a slow database query finishes), stream the replacement content
4. The client swaps out the fallback for the real content — no full-page reload

This means the user sees meaningful content **as soon as it's ready**, rather than staring at a blank screen while the slowest query finishes.

```jsx
// page.tsx — Server Component with streaming via Suspense

import { Suspense } from 'react';
import { UserHeader } from './UserHeader';
import { RecommendedProducts } from './RecommendedProducts';
import { OrderHistory } from './OrderHistory';
import { PersonalizedFeed } from './PersonalizedFeed';

export default function DashboardPage() {
  // This page has multiple data-fetching Server Components.
  // Each is wrapped in Suspense so they stream independently.
  return (
    <div className="dashboard">
      {/* Fast — user data from cache, renders immediately */}
      <Suspense fallback={<HeaderSkeleton />}>
        <UserHeader />
      </Suspense>

      <div className="grid grid-cols-3 gap-6">
        {/* Medium speed — ~200ms DB query */}
        <Suspense fallback={<OrdersSkeleton />}>
          <OrderHistory />
        </Suspense>

        {/* Slow — ~800ms ML recommendation API call */}
        <Suspense fallback={<RecommendationsSkeleton />}>
          <RecommendedProducts />
        </Suspense>

        {/* Slowest — ~1.5s aggregation pipeline */}
        <Suspense fallback={<FeedSkeleton />}>
          <PersonalizedFeed />
        </Suspense>
      </div>
    </div>
  );
}

// Each component fetches independently and streams when ready

async function UserHeader() {
  const user = await getUser();  // ~50ms (cached)
  return <header><h1>Welcome, {user.name}</h1></header>;
}

async function OrderHistory() {
  const orders = await db.order.findMany({
    where: { userId: getCurrentUserId() },
    take: 5,
    orderBy: { createdAt: 'desc' },
  });
  // Renders at ~200ms — streamed to client immediately
  return (
    <section>
      <h2>Recent Orders</h2>
      {orders.map(order => (
        <div key={order.id}>
          #{order.id} — ${order.total} — {order.status}
        </div>
      ))}
    </section>
  );
}

async function RecommendedProducts() {
  // Slow external API call — but it streams independently!
  const products = await fetch('https://ml-api.internal/recommendations', {
    headers: { 'Authorization': `Bearer ${process.env.ML_API_KEY}` },
  }).then(r => r.json());

  return (
    <section>
      <h2>Recommended for You</h2>
      <div className="product-grid">
        {products.map(p => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </section>
  );
}
```

**Streaming timeline for the user:**
```
0ms    → Shell HTML + CSS arrives, skeletons visible for all sections
50ms   → UserHeader streams in, replaces HeaderSkeleton
200ms  → OrderHistory streams in, replaces OrdersSkeleton
800ms  → RecommendedProducts streams in, replaces RecommendationsSkeleton
1500ms → PersonalizedFeed streams in, replaces FeedSkeleton
```

Without streaming, the user would see nothing until 1500ms. With streaming, they see the header at 50ms and progressively more content — a dramatically better perceived performance.

**Technical detail:** The RSC payload is streamed as a sequence of chunks. Each chunk represents a resolved Suspense boundary. The client-side React runtime processes these chunks as they arrive and performs **selective hydration** — it hydrates the most urgent parts first (e.g., the part the user is interacting with).

---

### Q11. How do caching and revalidation patterns work with Server Components?

**Answer:**

Caching in the RSC model (as implemented in Next.js) operates at multiple layers: **request-level deduplication**, **data cache**, and **full-route cache**. Understanding these layers is essential for building performant production applications.

**1. Request Memoization:** Within a single server render, multiple components that call the same `fetch()` URL automatically share the result. React deduplicates the request.

**2. Data Cache:** `fetch()` results are cached on the server across requests. You control this with `cache` and `next.revalidate` options.

**3. Full Route Cache:** The entire RSC payload and HTML output for static routes are cached at build time and served from the edge.

**Revalidation strategies:**
- **Time-based:** `{ next: { revalidate: 60 } }` — re-fetch after 60 seconds
- **On-demand:** `revalidatePath('/products')` or `revalidateTag('products')` — triggered by mutations
- **Opt-out:** `{ cache: 'no-store' }` — always fetch fresh data

```jsx
// ---- Caching strategies in Server Components ----

// 1. Static data — cached at build time, revalidated every hour
async function ProductCategories() {
  const categories = await fetch('https://api.store.com/categories', {
    next: { revalidate: 3600 },  // Revalidate every hour
  }).then(r => r.json());

  return (
    <nav>
      {categories.map(cat => (
        <a key={cat.id} href={`/category/${cat.slug}`}>{cat.name}</a>
      ))}
    </nav>
  );
}

// 2. Dynamic data — never cached, always fresh
async function LiveInventory({ productId }) {
  const stock = await fetch(`https://api.store.com/inventory/${productId}`, {
    cache: 'no-store',  // Always fetch fresh data
  }).then(r => r.json());

  return (
    <span className={stock.count > 0 ? 'text-green-600' : 'text-red-600'}>
      {stock.count > 0 ? `${stock.count} in stock` : 'Out of stock'}
    </span>
  );
}

// 3. Tag-based caching for on-demand revalidation
async function ProductDetails({ productId }) {
  const product = await fetch(`https://api.store.com/products/${productId}`, {
    next: { tags: [`product-${productId}`] },  // Tag for targeted revalidation
  }).then(r => r.json());

  return (
    <div>
      <h1>{product.name}</h1>
      <p>${product.price}</p>
    </div>
  );
}

// 4. Server Action that revalidates after mutation
'use server';

import { revalidateTag, revalidatePath } from 'next/cache';

export async function updateProductPrice(productId: string, newPrice: number) {
  await db.product.update({
    where: { id: productId },
    data: { price: newPrice },
  });

  // Option A: Revalidate specific product
  revalidateTag(`product-${productId}`);

  // Option B: Revalidate an entire path
  revalidatePath('/products');

  // Option C: Revalidate everything (nuclear option)
  // revalidatePath('/', 'layout');
}

// 5. Request deduplication — same fetch is called in multiple components
//    but only executed ONCE per request

async function ProductPage({ params }) {
  // Both of these components call the same endpoint — React deduplicates
  return (
    <>
      <ProductHeader productId={params.id} />
      <ProductReviews productId={params.id} />
    </>
  );
}

async function ProductHeader({ productId }) {
  // This fetch is deduped with the one in ProductReviews
  const product = await fetch(`https://api.store.com/products/${productId}`).then(r => r.json());
  return <h1>{product.name}</h1>;
}

async function ProductReviews({ productId }) {
  // Same URL — React reuses the result from ProductHeader's fetch
  const product = await fetch(`https://api.store.com/products/${productId}`).then(r => r.json());
  return (
    <div>
      <h2>Reviews ({product.reviews.length})</h2>
      {product.reviews.map(r => <Review key={r.id} review={r} />)}
    </div>
  );
}
```

**Using `unstable_cache` (Next.js) for non-fetch data:**

```jsx
import { unstable_cache } from 'next/cache';
import { db } from '@/lib/database';

// Cache database queries with tags and revalidation
const getCachedProducts = unstable_cache(
  async (categoryId: string) => {
    return db.product.findMany({
      where: { categoryId },
      orderBy: { createdAt: 'desc' },
    });
  },
  ['products-by-category'],  // Cache key prefix
  {
    revalidate: 300,                    // 5 minutes
    tags: ['products'],                  // For on-demand revalidation
  }
);

export default async function CategoryPage({ params }) {
  const products = await getCachedProducts(params.categoryId);
  return <ProductGrid products={products} />;
}
```

**Production tip:** Use time-based revalidation for content that changes predictably (blog posts, product catalogs) and on-demand revalidation for user-triggered mutations (price updates, inventory changes). Avoid `cache: 'no-store'` unless data is truly real-time (stock prices, live scores).

---

### Q12. How can Server Components directly access databases and ORMs?

**Answer:**

Because Server Components execute on the server, they can **directly import and use database clients, ORMs, and other server-only resources** — something that was impossible in traditional React components without an API layer in between. This eliminates an entire class of API routes and data-fetching boilerplate.

The key advantage: data flows directly from the database to the rendered JSX, with no intermediate serialization to JSON, no API route handler, no client-side fetch, and no loading state management.

**Security note:** Since Server Component code never ships to the browser, database credentials and connection strings remain safely on the server. However, you must be careful not to accidentally expose sensitive data in the **props** you pass to Client Components.

```jsx
// ---- Direct database access in Server Components ----

// lib/database.ts — Prisma client (server-only)
import { PrismaClient } from '@prisma/client';

// Prevent multiple instances in development (Next.js hot reload)
const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };
export const db = globalForPrisma.prisma || new PrismaClient();
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db;

// ---- Example 1: Complex query with joins and aggregations ----
import { db } from '@/lib/database';

export default async function SalesReport() {
  // Direct Prisma query — no API route needed
  const report = await db.order.groupBy({
    by: ['status'],
    _count: { id: true },
    _sum: { total: true },
    where: {
      createdAt: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
    },
  });

  const topProducts = await db.orderItem.groupBy({
    by: ['productId'],
    _sum: { quantity: true, subtotal: true },
    orderBy: { _sum: { subtotal: 'desc' } },
    take: 10,
  });

  // Enrich with product names
  const productIds = topProducts.map(p => p.productId);
  const products = await db.product.findMany({
    where: { id: { in: productIds } },
    select: { id: true, name: true, imageUrl: true },
  });

  const enrichedTopProducts = topProducts.map(tp => ({
    ...tp,
    product: products.find(p => p.id === tp.productId),
  }));

  return (
    <div className="space-y-8">
      <section>
        <h2>Order Status Breakdown (Last 30 Days)</h2>
        <table>
          <thead>
            <tr><th>Status</th><th>Count</th><th>Revenue</th></tr>
          </thead>
          <tbody>
            {report.map(row => (
              <tr key={row.status}>
                <td>{row.status}</td>
                <td>{row._count.id}</td>
                <td>${row._sum.total?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Top 10 Products by Revenue</h2>
        {enrichedTopProducts.map(({ product, _sum }) => (
          <div key={product?.id} className="flex items-center gap-4">
            <img src={product?.imageUrl} alt="" width={48} height={48} />
            <span>{product?.name}</span>
            <span className="ml-auto font-bold">${_sum.subtotal?.toFixed(2)}</span>
            <span className="text-muted">{_sum.quantity} sold</span>
          </div>
        ))}
      </section>
    </div>
  );
}

// ---- Example 2: Using raw SQL for complex analytics ----
import { db } from '@/lib/database';

export async function CohortAnalysis() {
  const cohorts = await db.$queryRaw`
    WITH user_cohorts AS (
      SELECT
        user_id,
        DATE_TRUNC('month', MIN(created_at)) AS cohort_month
      FROM orders
      GROUP BY user_id
    )
    SELECT
      uc.cohort_month,
      DATE_TRUNC('month', o.created_at) AS order_month,
      COUNT(DISTINCT o.user_id) AS active_users,
      SUM(o.total) AS revenue
    FROM user_cohorts uc
    JOIN orders o ON o.user_id = uc.user_id
    WHERE uc.cohort_month >= NOW() - INTERVAL '6 months'
    GROUP BY uc.cohort_month, order_month
    ORDER BY uc.cohort_month, order_month
  `;

  return (
    <div>
      <h2>Cohort Retention Analysis</h2>
      {/* Render cohort table — all SQL runs on server, result is just HTML */}
      <CohortTable data={cohorts} />
    </div>
  );
}

// ---- Example 3: Protecting against data leakage ----
import { db } from '@/lib/database';
import { UserCard } from './UserCard'; // Client Component

export default async function AdminUserList() {
  const users = await db.user.findMany({
    select: {
      id: true,
      name: true,
      email: true,
      role: true,
      // ⚠️ passwordHash, sessionTokens, etc. are NOT selected
    },
  });

  // ✅ Only pass safe, serializable data to Client Components
  return (
    <div>
      {users.map(user => (
        <UserCard
          key={user.id}
          id={user.id}
          name={user.name}
          email={user.email}
          role={user.role}
          // ❌ NEVER pass: passwordHash, internalNotes, etc.
        />
      ))}
    </div>
  );
}
```

**Production best practice:** Use the `server-only` package to ensure a module can never be accidentally imported into a Client Component:

```jsx
// lib/database.ts
import 'server-only';  // Build error if imported in a 'use client' file
import { PrismaClient } from '@prisma/client';

export const db = new PrismaClient();
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you implement authentication patterns with Server Components?

**Answer:**

Server Components are ideal for authentication because they run on the server where you have access to cookies, headers, and session stores. The pattern is to check authentication at the **layout or page level** (Server Component), then pass only the necessary user data to Client Components as props.

**Key principles:**
- Read session cookies/tokens in Server Components using `cookies()` from `next/headers`
- Never expose session tokens or sensitive auth data to Client Components
- Use middleware for route protection; use Server Components for data-level authorization
- Pass only the minimum user profile data needed for UI rendering

```jsx
// ---- lib/auth.ts — Server-only auth utilities ----
import 'server-only';
import { cookies } from 'next/headers';
import { db } from '@/lib/database';
import { jwtVerify } from 'jose';  // Server-only — 0 bytes on client

const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET);

export async function getCurrentUser() {
  const cookieStore = await cookies();
  const token = cookieStore.get('session')?.value;

  if (!token) return null;

  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    const user = await db.user.findUnique({
      where: { id: payload.sub as string },
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        avatarUrl: true,
        // Never select: passwordHash, totpSecret, etc.
      },
    });
    return user;
  } catch {
    return null;
  }
}

export async function requireAuth() {
  const user = await getCurrentUser();
  if (!user) {
    redirect('/login');
  }
  return user;
}

export async function requireRole(role: 'ADMIN' | 'MANAGER') {
  const user = await requireAuth();
  if (user.role !== role) {
    redirect('/unauthorized');
  }
  return user;
}

// ---- app/dashboard/layout.tsx — Auth at the layout level ----
import { requireAuth } from '@/lib/auth';
import { NavBar } from '@/components/NavBar';

export default async function DashboardLayout({ children }) {
  const user = await requireAuth();  // Redirects to /login if not authenticated

  return (
    <div className="min-h-screen">
      {/* Pass minimal user data to the Client Component navbar */}
      <NavBar
        userName={user.name}
        avatarUrl={user.avatarUrl}
        role={user.role}
      />
      <main className="p-6">{children}</main>
    </div>
  );
}

// ---- app/admin/users/page.tsx — Role-based authorization ----
import { requireRole } from '@/lib/auth';
import { db } from '@/lib/database';

export default async function AdminUsersPage() {
  const admin = await requireRole('ADMIN');  // Redirects if not admin

  const users = await db.user.findMany({
    select: { id: true, name: true, email: true, role: true, createdAt: true },
    orderBy: { createdAt: 'desc' },
  });

  return (
    <div>
      <h1>User Management</h1>
      <p>Logged in as: {admin.name} (Admin)</p>
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>Role</th><th>Joined</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>{user.createdAt.toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---- Server Action with auth check ----
'use server';

import { requireRole } from '@/lib/auth';
import { db } from '@/lib/database';
import { revalidatePath } from 'next/cache';

export async function changeUserRole(userId: string, newRole: string) {
  // Always re-verify auth in Server Actions — don't trust the client
  const admin = await requireRole('ADMIN');

  // Prevent self-demotion
  if (userId === admin.id) {
    throw new Error('Cannot change your own role');
  }

  await db.user.update({
    where: { id: userId },
    data: { role: newRole },
  });

  revalidatePath('/admin/users');
}

// ---- components/NavBar.tsx — Client Component ----
'use client';

import { useState } from 'react';
import { logoutAction } from '@/actions/auth';

export function NavBar({ userName, avatarUrl, role }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="flex items-center justify-between p-4 bg-gray-900 text-white">
      <span className="font-bold">Dashboard</span>
      <div className="relative">
        <button onClick={() => setMenuOpen(!menuOpen)} className="flex items-center gap-2">
          <img src={avatarUrl} alt="" className="w-8 h-8 rounded-full" />
          <span>{userName}</span>
          {role === 'ADMIN' && <span className="badge bg-red-500">Admin</span>}
        </button>
        {menuOpen && (
          <div className="absolute right-0 mt-2 bg-white text-black rounded shadow-lg p-2">
            <a href="/settings" className="block px-4 py-2">Settings</a>
            <form action={logoutAction}>
              <button type="submit" className="block w-full text-left px-4 py-2">
                Sign Out
              </button>
            </form>
          </div>
        )}
      </div>
    </nav>
  );
}
```

**Production security checklist:**
- Always re-verify authentication in **every** Server Action (don't assume the client is authorized)
- Use `server-only` imports for auth utilities to prevent accidental client inclusion
- Use `select` in database queries to avoid leaking sensitive fields
- Set `HttpOnly`, `Secure`, `SameSite=Lax` on session cookies
- Implement CSRF protection (Server Actions do this automatically in Next.js)

---

### Q14. How do you think about nested Server/Client component boundaries in a complex application?

**Answer:**

In a complex application, the component tree alternates between Server and Client boundaries multiple times. The key mental model is **thinking in layers**:

1. **Server layer** (default) — data fetching, layout, static content
2. **Client island** — interactive widget (button, form, dropdown)
3. **Server layer again** — rendered via `children` or slot props passed through the client island
4. **Client island** — another interactive element deeper in the tree

The boundaries are **not** a simple split at one level. You can nest them arbitrarily deep using the `children` prop pattern.

**Rules to internalize:**
- A `'use client'` directive creates a boundary. Everything **imported** by that module is client-side.
- But anything **passed as JSX props** (like `children`) can still be Server Components.
- Server Components cannot be imported into Client Components, but they can be **composed into** Client Components from a Server Component parent.

```jsx
// Complex real-world layout with multiple nested boundaries

// ---- app/dashboard/page.tsx (Server Component) ----
import { db } from '@/lib/database';
import { DashboardShell } from './DashboardShell';           // Client (interactive layout)
import { MetricsGrid } from './MetricsGrid';                  // Server (data-heavy)
import { ActivityFeed } from './ActivityFeed';                 // Server (data-heavy)
import { QuickActions } from './QuickActions';                 // Client (interactive)

export default async function DashboardPage() {
  const user = await getCurrentUser();

  return (
    // Layer 1: Client Component (provides collapsible sidebar, theme toggle)
    <DashboardShell
      userName={user.name}
      // Layer 2: Server Components passed as props — rendered on server,
      // received by DashboardShell as pre-rendered JSX
      sidebar={<DashboardSidebar userId={user.id} />}
      header={<DashboardHeader user={user} />}
    >
      {/* Layer 2 continued: Server Components as children */}
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8">
          <MetricsGrid userId={user.id} />
        </div>
        <div className="col-span-4">
          <QuickActions />        {/* Client Component */}
          <ActivityFeed userId={user.id} />  {/* Server Component */}
        </div>
      </div>
    </DashboardShell>
  );
}

// ---- DashboardShell.tsx (Client Component — interactive layout) ----
'use client';

import { useState } from 'react';

export function DashboardShell({ userName, sidebar, header, children }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState('light');

  return (
    <div className={`dashboard ${theme}`}>
      <aside className={sidebarCollapsed ? 'w-16' : 'w-64'}>
        <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
          {sidebarCollapsed ? '→' : '←'}
        </button>
        {!sidebarCollapsed && sidebar}  {/* Server-rendered sidebar content */}
      </aside>
      <div className="flex-1">
        <header className="flex justify-between items-center p-4">
          {header}  {/* Server-rendered header content */}
          <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </header>
        <main className="p-6">
          {children}  {/* Mix of Server and Client components */}
        </main>
      </div>
    </div>
  );
}

// ---- DashboardSidebar.tsx (Server Component — data fetching) ----
import { db } from '@/lib/database';

async function DashboardSidebar({ userId }) {
  const projects = await db.project.findMany({
    where: { members: { some: { userId } } },
    select: { id: true, name: true, color: true },
    take: 10,
  });

  const unreadCount = await db.notification.count({
    where: { userId, read: false },
  });

  return (
    <nav className="space-y-4">
      <div>
        <h3>Projects</h3>
        <ul>
          {projects.map(p => (
            <li key={p.id}>
              <a href={`/projects/${p.id}`}>
                <span style={{ color: p.color }}>●</span> {p.name}
              </a>
            </li>
          ))}
        </ul>
      </div>
      <a href="/notifications" className="flex justify-between">
        Notifications
        {unreadCount > 0 && (
          <span className="badge bg-red-500">{unreadCount}</span>
        )}
      </a>
    </nav>
  );
}

// ---- MetricsGrid.tsx (Server Component) ----
import { db } from '@/lib/database';
import { InteractiveChart } from './InteractiveChart';  // Client Component

async function MetricsGrid({ userId }) {
  const [revenue, orders, visitors] = await Promise.all([
    db.order.aggregate({ _sum: { total: true }, where: { userId } }),
    db.order.count({ where: { userId } }),
    db.pageView.count({ where: { userId } }),
  ]);

  const chartData = await db.$queryRaw`
    SELECT DATE(created_at) as date, SUM(total) as daily_revenue
    FROM orders WHERE user_id = ${userId}
    AND created_at > NOW() - INTERVAL '30 days'
    GROUP BY date ORDER BY date
  `;

  return (
    <div className="space-y-6">
      {/* Static cards — pure Server Component */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard title="Revenue" value={`$${revenue._sum.total?.toFixed(2)}`} />
        <MetricCard title="Orders" value={orders.toString()} />
        <MetricCard title="Visitors" value={visitors.toLocaleString()} />
      </div>
      {/* Interactive chart — Client Component with serialized data */}
      <InteractiveChart
        data={chartData.map(d => ({
          date: d.date.toISOString(),
          revenue: Number(d.daily_revenue),
        }))}
      />
    </div>
  );
}
```

**The mental model:** Think of your component tree like a sandwich — Server/Client/Server/Client — with data flowing down and `children` being the mechanism that lets server-rendered content pass through client boundaries unmodified.

---

### Q15. How do you handle errors in Server Components?

**Answer:**

Error handling in Server Components uses a combination of **try/catch** within the component, **Error Boundaries** (via `error.tsx` in Next.js), and **`notFound()`** for missing resources. Since Server Components can be async, you can catch errors at the data-fetching level and decide how to handle them.

**Key error handling layers:**
1. **In-component try/catch** — handle expected errors (missing data, validation failures)
2. **Error Boundary (`error.tsx`)** — catch unexpected errors and show a fallback UI
3. **`not-found.tsx`** — handle 404 cases specifically
4. **Global error handler (`global-error.tsx`)** — catch errors in the root layout

**Important:** `error.tsx` must be a Client Component (it needs to manage retry state), but it catches errors from Server Components in its subtree.

```jsx
// ---- app/products/[id]/page.tsx — Server Component with error handling ----
import { db } from '@/lib/database';
import { notFound } from 'next/navigation';

export default async function ProductPage({ params }) {
  const product = await db.product.findUnique({
    where: { id: params.id },
    include: {
      category: true,
      reviews: { take: 10, orderBy: { createdAt: 'desc' } },
    },
  });

  // Handle 404 — renders the nearest not-found.tsx
  if (!product) {
    notFound();
  }

  // Handle business logic errors gracefully
  let recommendations = [];
  try {
    const res = await fetch(`${process.env.ML_API}/recommendations/${params.id}`, {
      signal: AbortSignal.timeout(3000),  // 3 second timeout
    });
    if (res.ok) {
      recommendations = await res.json();
    }
    // If the ML API is down, we just show no recommendations — not a hard error
  } catch (error) {
    console.error('Recommendations API failed:', error);
    // Graceful degradation — page still renders without recommendations
  }

  return (
    <div>
      <h1>{product.name}</h1>
      <p>${product.price}</p>
      <div>{product.description}</div>

      {recommendations.length > 0 && (
        <section>
          <h2>You might also like</h2>
          {recommendations.map(r => <ProductCard key={r.id} product={r} />)}
        </section>
      )}
    </div>
  );
}

// ---- app/products/[id]/not-found.tsx — 404 handler ----
export default function ProductNotFound() {
  return (
    <div className="text-center py-20">
      <h1 className="text-4xl font-bold">Product Not Found</h1>
      <p className="text-gray-500 mt-4">
        The product you're looking for doesn't exist or has been removed.
      </p>
      <a href="/products" className="text-blue-600 underline mt-4 block">
        Browse all products
      </a>
    </div>
  );
}

// ---- app/products/[id]/error.tsx — Error boundary (MUST be Client Component) ----
'use client';

import { useEffect } from 'react';

export default function ProductError({ error, reset }) {
  useEffect(() => {
    // Log to error reporting service
    console.error('Product page error:', error);
    // Sentry.captureException(error);
  }, [error]);

  return (
    <div className="text-center py-20">
      <h1 className="text-2xl font-bold text-red-600">Something went wrong</h1>
      <p className="text-gray-500 mt-2">{error.message}</p>
      <button
        onClick={() => reset()}  // Re-renders the Server Component
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Try Again
      </button>
    </div>
  );
}

// ---- Error handling in Server Actions ----
'use server';

import { db } from '@/lib/database';
import { z } from 'zod';
import { revalidatePath } from 'next/cache';

const ReviewSchema = z.object({
  rating: z.number().min(1).max(5),
  comment: z.string().min(10).max(1000),
});

export async function submitReview(productId: string, formData: FormData) {
  // 1. Validate input
  const parsed = ReviewSchema.safeParse({
    rating: Number(formData.get('rating')),
    comment: formData.get('comment'),
  });

  if (!parsed.success) {
    // Return validation errors to the client — don't throw
    return {
      success: false,
      errors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    // 2. Attempt the mutation
    await db.review.create({
      data: {
        productId,
        userId: await getCurrentUserId(),
        rating: parsed.data.rating,
        comment: parsed.data.comment,
      },
    });

    revalidatePath(`/products/${productId}`);
    return { success: true };
  } catch (error) {
    // 3. Handle database errors
    if (error.code === 'P2002') {
      return { success: false, errors: { _form: ['You already reviewed this product'] } };
    }
    // 4. Unexpected errors — throw to trigger error boundary
    throw new Error('Failed to submit review. Please try again.');
  }
}
```

**Best practices:**
- Use `notFound()` for missing resources — it's more semantic than throwing a 404 error
- Use try/catch for external API calls and implement **graceful degradation** (show the page without the failed section)
- Return validation errors from Server Actions as data, don't throw them
- Throw unexpected errors to let the error boundary catch them
- Always log errors server-side before re-throwing

---

### Q16. Compare the performance characteristics of RSC vs. traditional SSR vs. CSR.

**Answer:**

Understanding the performance tradeoffs between these three rendering strategies is crucial for architectural decisions. Each has distinct characteristics across the key Web Vitals metrics.

**Client-Side Rendering (CSR):**
- Browser downloads an empty HTML shell + large JS bundle
- JS executes, fetches data, then renders the UI
- Worst FCP/LCP, worst SEO, but simplest deployment
- Every dependency ships to the client

**Server-Side Rendering (SSR):**
- Server renders full HTML → browser receives meaningful content immediately
- Browser downloads JS bundle → hydration makes it interactive
- Better FCP/LCP than CSR, but same bundle size (hydration needs all the code)
- Time to Interactive (TTI) can be worse than CSR if hydration is heavy

**React Server Components (RSC):**
- Server renders a mix of static HTML and RSC payload
- Client receives HTML (for fast FCP) + RSC payload (for React tree reconciliation)
- Only Client Component JS is sent → dramatically smaller bundles
- Streaming means each section appears as soon as it's ready
- TTI is much better because there's less JS to parse and execute

```jsx
// ---- Performance comparison: same feature, three approaches ----

// SCENARIO: Product page with Markdown description, reviews, and an "Add to Cart" button

// ====== Approach 1: CSR ======
// Bundle: React (~40KB) + react-markdown (~60KB) + date-fns (~20KB) + app code (~30KB)
// Total JS: ~150KB
// Timeline:
//   0ms     HTML shell (blank page)
//   500ms   JS downloaded + parsed
//   600ms   Component mounts, fetch('/api/product/123') fires
//   900ms   Data arrives, page renders
//   FCP: ~900ms | TTI: ~600ms | LCP: ~900ms

'use client';
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { format } from 'date-fns';

export default function ProductPage({ params }) {
  const [product, setProduct] = useState(null);
  useEffect(() => {
    fetch(`/api/products/${params.id}`).then(r => r.json()).then(setProduct);
  }, []);
  if (!product) return <Loading />;
  return (
    <div>
      <h1>{product.name}</h1>
      <ReactMarkdown>{product.description}</ReactMarkdown>
      <span>{format(new Date(product.createdAt), 'PPP')}</span>
      <button onClick={() => addToCart(product.id)}>Add to Cart</button>
    </div>
  );
}

// ====== Approach 2: SSR (getServerSideProps) ======
// Bundle: SAME ~150KB (all code ships for hydration)
// Timeline:
//   0ms     Server fetches data, renders HTML
//   200ms   Full HTML arrives (meaningful content visible)
//   700ms   JS downloaded + parsed, hydration begins
//   800ms   Hydration complete, page is interactive
//   FCP: ~200ms | TTI: ~800ms | LCP: ~200ms
// Problem: TTI is 800ms because browser must download + parse + hydrate 150KB of JS

import ReactMarkdown from 'react-markdown';
import { format } from 'date-fns';

export async function getServerSideProps({ params }) {
  const product = await db.product.findUnique({ where: { id: params.id } });
  return { props: { product: JSON.parse(JSON.stringify(product)) } };
}

export default function ProductPage({ product }) {
  return (
    <div>
      <h1>{product.name}</h1>
      <ReactMarkdown>{product.description}</ReactMarkdown>
      <span>{format(new Date(product.createdAt), 'PPP')}</span>
      <button onClick={() => addToCart(product.id)}>Add to Cart</button>
    </div>
  );
}

// ====== Approach 3: RSC ======
// Bundle: React (~40KB) + tiny AddToCartButton (~2KB)
// Total JS: ~42KB (72% reduction!)
// Timeline:
//   0ms     Server starts rendering, streams HTML immediately
//   100ms   Initial HTML + shell arrives
//   150ms   RSC payload streams in with product content
//   250ms   JS downloaded, only AddToCartButton hydrates
//   300ms   Fully interactive
//   FCP: ~100ms | TTI: ~300ms | LCP: ~150ms

import { db } from '@/lib/database';
import { marked } from 'marked';                    // 0 bytes on client
import { format } from 'date-fns';                   // 0 bytes on client
import { AddToCartButton } from './AddToCartButton';  // ~2KB on client

export default async function ProductPage({ params }) {
  const product = await db.product.findUnique({ where: { id: params.id } });
  const descriptionHtml = marked.parse(product.description);

  return (
    <div>
      <h1>{product.name}</h1>
      <div dangerouslySetInnerHTML={{ __html: descriptionHtml }} />
      <span>{format(product.createdAt, 'PPP')}</span>
      <AddToCartButton productId={product.id} />
    </div>
  );
}
```

**Summary table:**

| Metric | CSR | SSR | RSC |
|---|---|---|---|
| First Contentful Paint (FCP) | Worst (~900ms) | Good (~200ms) | Best (~100ms, streamed) |
| Time to Interactive (TTI) | Moderate (~600ms) | Worst (~800ms, hydration) | Best (~300ms, minimal JS) |
| Largest Contentful Paint (LCP) | Worst | Good | Best (streaming) |
| JS Bundle Size | Full (~150KB) | Full (~150KB) | Minimal (~42KB) |
| TTFB | Fast (static HTML) | Slow (server render) | Moderate (streaming) |
| SEO | Poor (empty shell) | Good (full HTML) | Best (full HTML + streaming) |
| Subsequent navigations | Fast (client routing) | Moderate (new HTML) | Fast (RSC payload + client routing) |

**Interview insight:** RSC doesn't replace SSR — it complements it. Client Components still get SSR'd for fast FCP. The difference is that Server Components are SSR'd but **never hydrated**, so they contribute zero JS to the bundle and zero hydration cost.

---

### Q17. What is a practical migration strategy from a CSR (Create React App / Vite) to RSC?

**Answer:**

Migrating from a fully client-side rendered app to RSC is a significant but achievable effort. The key principle is **incremental adoption** — you don't rewrite everything at once. Instead, you progressively move components from the client to the server, starting with the ones that benefit most (data-fetching, heavy dependencies).

**Phase 1: Framework Migration (1-2 weeks)**

Move from CRA/Vite to Next.js App Router (or another RSC-supporting framework). Initially, every page is a Client Component.

**Phase 2: Identify Server Component Candidates (1 week)**

Audit your components and categorize them. The best candidates for conversion to Server Components are:
- Data-fetching wrapper components (pages that use `useEffect` + `fetch`)
- Static/presentational components that display data
- Components using heavy rendering libraries (Markdown, syntax highlighting, etc.)

**Phase 3: Incremental Conversion (ongoing)**

Convert components one-by-one, pushing the `'use client'` boundary down.

**Phase 4: Replace API Routes with Server Actions**

For mutations that currently go through custom API routes, migrate to Server Actions.

```jsx
// ---- BEFORE: Typical CSR pattern (CRA/Vite) ----

// src/pages/Products.tsx — Everything is client-side
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { format } from 'date-fns';

export function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const category = searchParams.get('category');

  useEffect(() => {
    fetch(`/api/products?category=${category}`)
      .then(r => r.json())
      .then(setProducts)
      .finally(() => setLoading(false));
  }, [category]);

  if (loading) return <Spinner />;

  return (
    <div>
      <h1>Products</h1>
      <CategoryFilter current={category} />  {/* Interactive */}
      <div className="grid grid-cols-3 gap-4">
        {products.map(product => (
          <div key={product.id} className="card">
            <h2>{product.name}</h2>
            <ReactMarkdown>{product.description}</ReactMarkdown>
            <span>{format(new Date(product.createdAt), 'PPP')}</span>
            <span>${product.price}</span>
            <AddToCartButton productId={product.id} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- MIGRATION Step 1: Move to Next.js App Router ----
// Just add 'use client' to make it work immediately in App Router

// app/products/page.tsx
'use client';  // Entire page is still a Client Component — that's OK for now
// ... same code as above, using next/navigation instead of react-router

// ---- MIGRATION Step 2: Extract the page-level data fetching to Server Component ----

// app/products/page.tsx — NOW a Server Component (no 'use client')
import { db } from '@/lib/database';
import { marked } from 'marked';
import { format } from 'date-fns';
import { CategoryFilter } from './CategoryFilter';
import { AddToCartButton } from './AddToCartButton';

export default async function ProductsPage({ searchParams }) {
  const category = searchParams.category;

  const products = await db.product.findMany({
    where: category ? { category: { slug: category } } : undefined,
    orderBy: { createdAt: 'desc' },
  });

  return (
    <div>
      <h1>Products</h1>
      <CategoryFilter current={category} />  {/* Still Client — interactive */}
      <div className="grid grid-cols-3 gap-4">
        {products.map(product => (
          <div key={product.id} className="card">
            <h2>{product.name}</h2>
            {/* Markdown now rendered on server — 0 JS cost */}
            <div dangerouslySetInnerHTML={{
              __html: marked.parse(product.description)
            }} />
            <span>{format(product.createdAt, 'PPP')}</span>
            <span>${product.price}</span>
            <AddToCartButton productId={product.id} />  {/* Still Client */}
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- MIGRATION Step 3: Replace API route with Server Action ----

// BEFORE: src/api/cart.ts (API route)
// export async function POST(req) { ... }

// AFTER: actions/cart.ts (Server Action)
'use server';

import { db } from '@/lib/database';
import { getCurrentUser } from '@/lib/auth';
import { revalidatePath } from 'next/cache';

export async function addToCart(productId: string) {
  const user = await getCurrentUser();
  await db.cartItem.upsert({
    where: { userId_productId: { userId: user.id, productId } },
    create: { userId: user.id, productId, quantity: 1 },
    update: { quantity: { increment: 1 } },
  });
  revalidatePath('/cart');
}
```

**Migration checklist:**
1. Set up Next.js App Router alongside existing pages (if needed, use a gradual migration)
2. Add `'use client'` to ALL existing components initially (everything still works)
3. Identify leaf components that are purely presentational → remove `'use client'`
4. Identify page-level data-fetching components → convert to async Server Components
5. Move heavy dependencies (Markdown, syntax highlighting, etc.) to Server Components
6. Replace `useEffect` + `fetch` patterns with direct `async/await`
7. Replace API routes for mutations with Server Actions
8. Add `<Suspense>` boundaries for streaming
9. Optimize with caching and revalidation strategies
10. Remove unused API routes

---

### Q18. How do you use Server Components effectively in the Next.js App Router?

**Answer:**

Next.js App Router (13.4+) is the most mature production implementation of RSC. In the App Router, **every component is a Server Component by default**. You opt into client-side rendering with `'use client'`. This is the opposite of the Pages Router, where everything was effectively a Client Component.

**Key App Router + RSC conventions:**

- `page.tsx` — Server Component (the route's main UI)
- `layout.tsx` — Server Component (shared UI that wraps pages)
- `loading.tsx` — Client/Server Component (Suspense fallback for the route)
- `error.tsx` — Client Component (error boundary)
- `not-found.tsx` — Client/Server Component (404 UI)
- `route.tsx` — API route handler (not a component)

```jsx
// ---- Complete Next.js App Router structure with RSC ----

// app/layout.tsx — Root layout (Server Component)
import { Inter } from 'next/font/google';
import { getCurrentUser } from '@/lib/auth';
import { ThemeProvider } from '@/components/ThemeProvider';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'My Store',
  description: 'An e-commerce store built with RSC',
};

export default async function RootLayout({ children }) {
  const user = await getCurrentUser();  // Auth check at the root

  return (
    <html lang="en" className={inter.className}>
      <body>
        {/* ThemeProvider is a Client Component — but children pass through */}
        <ThemeProvider>
          <header>
            <nav>
              <a href="/">Home</a>
              <a href="/products">Products</a>
              {user ? (
                <span>Welcome, {user.name}</span>
              ) : (
                <a href="/login">Sign In</a>
              )}
            </nav>
          </header>
          <main>{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}

// app/products/page.tsx — Products listing (Server Component)
import { Suspense } from 'react';
import { db } from '@/lib/database';
import { ProductGrid } from './ProductGrid';
import { SearchBar } from './SearchBar';
import { ProductGridSkeleton } from './skeletons';

// Metadata generation — also runs on server
export async function generateMetadata({ searchParams }) {
  const category = searchParams.category;
  return {
    title: category ? `${category} Products` : 'All Products',
  };
}

export default async function ProductsPage({ searchParams }) {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Products</h1>
      {/* Client Component — needs onChange handler */}
      <SearchBar />
      {/* Suspense enables streaming — skeleton shows while products load */}
      <Suspense
        key={JSON.stringify(searchParams)}  // Re-suspend when params change
        fallback={<ProductGridSkeleton />}
      >
        <FilteredProducts searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

// Separate async Server Component for data fetching
async function FilteredProducts({ searchParams }) {
  const { category, q, sort, page = '1' } = searchParams;
  const pageNum = parseInt(page);
  const PAGE_SIZE = 12;

  const where = {
    ...(category && { category: { slug: category } }),
    ...(q && { name: { contains: q, mode: 'insensitive' } }),
  };

  const [products, totalCount] = await Promise.all([
    db.product.findMany({
      where,
      orderBy: sort === 'price_asc' ? { price: 'asc' }
             : sort === 'price_desc' ? { price: 'desc' }
             : { createdAt: 'desc' },
      skip: (pageNum - 1) * PAGE_SIZE,
      take: PAGE_SIZE,
      include: { category: true },
    }),
    db.product.count({ where }),
  ]);

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  return (
    <>
      <p className="text-gray-500 mb-4">{totalCount} products found</p>
      <ProductGrid products={products.map(p => ({
        id: p.id,
        name: p.name,
        price: p.price,
        imageUrl: p.imageUrl,
        category: p.category.name,
        slug: p.slug,
      }))} />
      <Pagination currentPage={pageNum} totalPages={totalPages} />
    </>
  );
}

// app/products/[slug]/page.tsx — Product detail (Server Component)
import { db } from '@/lib/database';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import { AddToCartForm } from './AddToCartForm';
import { ReviewsList } from './ReviewsList';

// Static params for build-time generation of popular products
export async function generateStaticParams() {
  const products = await db.product.findMany({
    where: { featured: true },
    select: { slug: true },
  });
  return products.map(p => ({ slug: p.slug }));
}

export default async function ProductDetailPage({ params }) {
  const product = await db.product.findUnique({
    where: { slug: params.slug },
    include: { category: true },
  });

  if (!product) notFound();

  return (
    <div className="container mx-auto py-8">
      <div className="grid grid-cols-2 gap-8">
        <div>
          <img
            src={product.imageUrl}
            alt={product.name}
            className="rounded-lg w-full"
          />
        </div>
        <div>
          <span className="text-sm text-gray-500">{product.category.name}</span>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-2xl font-semibold mt-2">${product.price}</p>
          <p className="mt-4 text-gray-700">{product.description}</p>

          {/* Client Component — interactive form */}
          <AddToCartForm productId={product.id} inStock={product.stock > 0} />
        </div>
      </div>

      {/* Streaming — reviews load independently */}
      <Suspense fallback={<div>Loading reviews...</div>}>
        <ReviewsList productId={product.id} />
      </Suspense>
    </div>
  );
}

// Server Component — fetches reviews
async function ReviewsList({ productId }) {
  const reviews = await db.review.findMany({
    where: { productId },
    include: { user: { select: { name: true, avatarUrl: true } } },
    orderBy: { createdAt: 'desc' },
    take: 20,
  });

  if (reviews.length === 0) {
    return <p className="text-gray-500 mt-8">No reviews yet.</p>;
  }

  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-4">Reviews ({reviews.length})</h2>
      <div className="space-y-4">
        {reviews.map(review => (
          <div key={review.id} className="border rounded-lg p-4">
            <div className="flex items-center gap-2">
              <img src={review.user.avatarUrl} alt="" className="w-8 h-8 rounded-full" />
              <span className="font-medium">{review.user.name}</span>
              <span className="text-yellow-500">{'★'.repeat(review.rating)}</span>
            </div>
            <p className="mt-2">{review.comment}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
```

**Next.js-specific RSC tips:**
- Use `generateStaticParams()` for static generation of RSC pages at build time
- Use `export const dynamic = 'force-dynamic'` to opt out of static rendering
- Use `export const revalidate = 60` for ISR (Incremental Static Regeneration)
- Use `unstable_cache` for caching database queries (not just `fetch`)
- Use `headers()` and `cookies()` for request-specific data (makes the route dynamic)
- Use `<Link>` prefetching — Next.js prefetches the RSC payload for linked pages

---

### Q19. How do React Server Components change the architecture of React applications? What is the future direction?

**Answer:**

RSC fundamentally changes how we think about React application architecture. The shift is from **"everything is a client-side component"** to **"server by default, client by exception."** This has cascading effects on data fetching, state management, bundle optimization, and the role of APIs.

**Architectural shifts:**

**1. The end of the "API-first" frontend:**
Traditional React apps require a separate API layer (REST or GraphQL) between the frontend and the database. With RSC, Server Components access the database directly, and Server Actions handle mutations directly. API routes become optional — you only need them for third-party consumers (mobile apps, webhooks, etc.).

**2. State management simplification:**
Much of what we used Redux/Zustand/React Query for was fetching and caching server data on the client. RSC moves data fetching to the server, eliminating the need for client-side server-state management. Client state libraries are still useful for **truly client-side state** (UI state, forms, optimistic updates), but their scope shrinks dramatically.

**3. Component architecture: the "island" model:**
Instead of large client-side component trees, RSC applications have a **mostly-server tree** with small **"client islands"** for interactivity. This is similar to Astro's islands architecture but with React's component model.

**4. The new build pipeline:**
RSC requires a bundler that understands the server/client boundary. The build produces two bundles: a server bundle (Server Components + Server Actions) and a client bundle (Client Components only). This is fundamentally different from traditional webpack/Vite builds.

```jsx
// ---- Architecture comparison ----

// BEFORE (Traditional React + API):
//
// Client (React SPA)                    Server (Express/Next API)
// ┌──────────────────┐                  ┌──────────────────┐
// │ ProductPage      │  fetch('/api')   │ GET /api/products│
// │   useState       │ ───────────────► │   query DB       │
// │   useEffect      │ ◄─────────────── │   serialize JSON │
// │   Redux store    │                  │                  │
// │   react-query    │                  │ POST /api/cart   │
// │   150KB bundle   │ ───────────────► │   validate       │
// └──────────────────┘                  │   mutate DB      │
//                                       └──────────────────┘

// AFTER (RSC Architecture):
//
// Server Runtime                        Client Runtime
// ┌──────────────────┐                  ┌──────────────────┐
// │ ProductPage (SC) │  RSC payload     │ AddToCart (CC)    │
// │   async/await DB │ ───────────────► │   useState        │
// │   heavy deps     │                  │   onClick         │
// │   auth checks    │                  │   2KB bundle      │
// │                  │  Server Action   │                   │
// │ addToCart (SA)   │ ◄─────────────── │   calls SA        │
// │   validate       │                  │                   │
// │   mutate DB      │                  │                   │
// └──────────────────┘                  └──────────────────┘
// No API routes needed!                 Tiny client bundle!

// ---- Example: Modern RSC-first architecture ----

// Instead of a Redux store with slices for products, cart, and user...
// you have a simple Server Component tree:

// app/page.tsx — Server Component
import { db } from '@/lib/database';
import { getCurrentUser } from '@/lib/auth';
import { CartIndicator } from '@/components/CartIndicator';

export default async function HomePage() {
  const user = await getCurrentUser();
  const featuredProducts = await db.product.findMany({
    where: { featured: true },
    take: 8,
  });

  const cartCount = user
    ? await db.cartItem.count({ where: { userId: user.id } })
    : 0;

  // No Redux. No React Query. No useEffect.
  // Data flows directly from DB to JSX.
  return (
    <div>
      <CartIndicator count={cartCount} />  {/* Tiny Client Component */}
      <h1>Featured Products</h1>
      <div className="grid grid-cols-4 gap-4">
        {featuredProducts.map(p => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  );
}

// When the user adds to cart (Server Action), we revalidatePath('/')
// and the Server Component re-executes with the new count.
// No client-side state to synchronize. No stale data bugs.
```

**Future direction (React 2025-2026 and beyond):**

1. **Partial Pre-Rendering (PPR):** Next.js is shipping PPR — a hybrid where static parts of a page are served from the edge instantly, and dynamic parts stream in from the server. This combines the speed of static sites with the freshness of dynamic rendering.

2. **RSC in more frameworks:** Remix, Expo (React Native), and other frameworks are adopting RSC. The model is becoming framework-agnostic.

3. **Improved DevTools:** React DevTools are being updated to show the server/client boundary, RSC payload sizes, and streaming timelines.

4. **Server Components in React Native:** The RSC model is being explored for mobile — server-rendered UI that streams to native apps.

5. **Compiler optimizations:** The React Compiler (React Forget) + RSC will enable automatic memoization and even more aggressive dead-code elimination.

**The big picture:** RSC moves React from a "client-side UI library" to a "full-stack component framework." Components are no longer just UI — they are the entire data-fetching, rendering, and mutation pipeline. This is the biggest paradigm shift since React itself was introduced in 2013.

---

### Q20. Production scenario: Build a data-heavy analytics dashboard using RSC with Client Component islands.

**Answer:**

This question tests your ability to architect a real-world application using RSC principles. Let's build an analytics dashboard that displays metrics, charts, data tables, and filters — the kind of page that would traditionally require 500KB+ of JavaScript.

**Architecture decisions:**
- **Server Components** for: data fetching, aggregations, table rendering, metric cards
- **Client Components** for: interactive charts (Recharts), date range picker, filters, export buttons
- **Streaming** for: each dashboard section loads independently
- **Server Actions** for: saving dashboard preferences, exporting reports

```jsx
// ---- app/dashboard/analytics/page.tsx (Server Component — orchestrator) ----

import { Suspense } from 'react';
import { db } from '@/lib/database';
import { requireAuth } from '@/lib/auth';
import { DashboardFilters } from './DashboardFilters';
import { MetricCards } from './MetricCards';
import { RevenueSection } from './RevenueSection';
import { TopProductsTable } from './TopProductsTable';
import { UserAcquisition } from './UserAcquisition';
import { RealTimeVisitors } from './RealTimeVisitors';
import {
  MetricsSkeleton,
  ChartSkeleton,
  TableSkeleton,
} from './skeletons';

export default async function AnalyticsDashboardPage({ searchParams }) {
  const user = await requireAuth();

  // Parse filter params (default: last 30 days)
  const range = searchParams.range || '30d';
  const startDate = getStartDate(range);
  const endDate = new Date();

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        {/* Client Component — interactive date range picker + filters */}
        <DashboardFilters currentRange={range} />
      </div>

      {/* Row 1: Metric cards — fast query, streams first */}
      <Suspense fallback={<MetricsSkeleton />}>
        <MetricCards userId={user.id} startDate={startDate} endDate={endDate} />
      </Suspense>

      {/* Row 2: Charts — medium speed, stream independently */}
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8">
          <Suspense fallback={<ChartSkeleton title="Revenue" />}>
            <RevenueSection userId={user.id} startDate={startDate} endDate={endDate} />
          </Suspense>
        </div>
        <div className="col-span-4">
          <Suspense fallback={<ChartSkeleton title="Visitors" />}>
            <RealTimeVisitors userId={user.id} />
          </Suspense>
        </div>
      </div>

      {/* Row 3: Tables — slower aggregation queries */}
      <div className="grid grid-cols-2 gap-6">
        <Suspense fallback={<TableSkeleton title="Top Products" />}>
          <TopProductsTable userId={user.id} startDate={startDate} endDate={endDate} />
        </Suspense>
        <Suspense fallback={<TableSkeleton title="User Acquisition" />}>
          <UserAcquisition userId={user.id} startDate={startDate} endDate={endDate} />
        </Suspense>
      </div>
    </div>
  );
}

function getStartDate(range) {
  const now = new Date();
  switch (range) {
    case '7d': return new Date(now.setDate(now.getDate() - 7));
    case '30d': return new Date(now.setDate(now.getDate() - 30));
    case '90d': return new Date(now.setDate(now.getDate() - 90));
    case '1y': return new Date(now.setFullYear(now.getFullYear() - 1));
    default: return new Date(now.setDate(now.getDate() - 30));
  }
}

// ---- MetricCards.tsx (Server Component — fast aggregation) ----
import { db } from '@/lib/database';

export async function MetricCards({ userId, startDate, endDate }) {
  // Parallel queries for speed
  const [revenue, orders, customers, conversionRate] = await Promise.all([
    db.order.aggregate({
      _sum: { total: true },
      where: { userId, createdAt: { gte: startDate, lte: endDate } },
    }),
    db.order.count({
      where: { userId, createdAt: { gte: startDate, lte: endDate } },
    }),
    db.customer.count({
      where: { orders: { some: { userId, createdAt: { gte: startDate, lte: endDate } } } },
    }),
    db.$queryRaw`
      SELECT
        ROUND(COUNT(DISTINCT CASE WHEN o.id IS NOT NULL THEN v.session_id END)::numeric /
              NULLIF(COUNT(DISTINCT v.session_id), 0) * 100, 2) as rate
      FROM page_views v
      LEFT JOIN orders o ON o.session_id = v.session_id
      WHERE v.user_id = ${userId}
        AND v.created_at BETWEEN ${startDate} AND ${endDate}
    `,
  ]);

  // Compare with previous period for trend indicators
  const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
  const prevStart = new Date(startDate);
  prevStart.setDate(prevStart.getDate() - daysDiff);

  const prevRevenue = await db.order.aggregate({
    _sum: { total: true },
    where: { userId, createdAt: { gte: prevStart, lte: startDate } },
  });

  const revenueTrend = prevRevenue._sum.total
    ? ((revenue._sum.total - prevRevenue._sum.total) / prevRevenue._sum.total * 100).toFixed(1)
    : null;

  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard
        title="Revenue"
        value={`$${(revenue._sum.total || 0).toLocaleString()}`}
        trend={revenueTrend ? `${revenueTrend}%` : 'N/A'}
        trendUp={Number(revenueTrend) > 0}
      />
      <MetricCard title="Orders" value={orders.toLocaleString()} />
      <MetricCard title="Customers" value={customers.toLocaleString()} />
      <MetricCard
        title="Conversion Rate"
        value={`${conversionRate[0]?.rate || 0}%`}
      />
    </div>
  );
}

function MetricCard({ title, value, trend, trendUp }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border">
      <p className="text-sm text-gray-500 font-medium">{title}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
      {trend && (
        <p className={`text-sm mt-2 ${trendUp ? 'text-green-600' : 'text-red-600'}`}>
          {trendUp ? '↑' : '↓'} {trend} vs previous period
        </p>
      )}
    </div>
  );
}

// ---- RevenueSection.tsx (Server Component wrapping Client chart) ----
import { db } from '@/lib/database';
import { RevenueChart } from './RevenueChart';  // Client Component

export async function RevenueSection({ userId, startDate, endDate }) {
  const dailyRevenue = await db.$queryRaw`
    SELECT
      DATE(created_at) as date,
      SUM(total) as revenue,
      COUNT(*) as order_count
    FROM orders
    WHERE user_id = ${userId}
      AND created_at BETWEEN ${startDate} AND ${endDate}
    GROUP BY DATE(created_at)
    ORDER BY date
  `;

  // Serialize for the client — only plain objects
  const chartData = dailyRevenue.map(row => ({
    date: row.date.toISOString().split('T')[0],
    revenue: Number(row.revenue),
    orders: Number(row.order_count),
  }));

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border">
      <h2 className="text-lg font-semibold mb-4">Revenue Over Time</h2>
      {/* Client Component — interactive chart with tooltips, zoom, etc. */}
      <RevenueChart data={chartData} />
    </div>
  );
}

// ---- RevenueChart.tsx (Client Component — interactive Recharts) ----
'use client';

import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { useState } from 'react';

export function RevenueChart({ data }) {
  const [metric, setMetric] = useState('revenue');

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          className={`px-3 py-1 rounded ${metric === 'revenue' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
          onClick={() => setMetric('revenue')}
        >
          Revenue
        </button>
        <button
          className={`px-3 py-1 rounded ${metric === 'orders' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
          onClick={() => setMetric('orders')}
        >
          Orders
        </button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip
            formatter={(value) =>
              metric === 'revenue' ? `$${value.toLocaleString()}` : value
            }
          />
          <Area
            type="monotone"
            dataKey={metric}
            stroke="#3b82f6"
            fill="#93c5fd"
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---- TopProductsTable.tsx (Server Component — heavy aggregation) ----
import { db } from '@/lib/database';
import { ExportButton } from './ExportButton';  // Client Component
import { exportProductReport } from '@/actions/export';  // Server Action

export async function TopProductsTable({ userId, startDate, endDate }) {
  const topProducts = await db.$queryRaw`
    SELECT
      p.id,
      p.name,
      p.image_url,
      SUM(oi.quantity) as total_quantity,
      SUM(oi.subtotal) as total_revenue,
      COUNT(DISTINCT o.id) as order_count,
      ROUND(AVG(oi.subtotal / NULLIF(oi.quantity, 0)), 2) as avg_price
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    JOIN products p ON p.id = oi.product_id
    WHERE o.user_id = ${userId}
      AND o.created_at BETWEEN ${startDate} AND ${endDate}
    GROUP BY p.id, p.name, p.image_url
    ORDER BY total_revenue DESC
    LIMIT 20
  `;

  // All this heavy SQL runs on the server.
  // The client receives a pre-rendered HTML table — minimal JS.

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Top Products</h2>
        {/* Client Component — just a button */}
        <ExportButton
          action={exportProductReport.bind(null, startDate.toISOString(), endDate.toISOString())}
        />
      </div>
      <table className="w-full">
        <thead>
          <tr className="text-left text-sm text-gray-500 border-b">
            <th className="pb-2">Product</th>
            <th className="pb-2">Units Sold</th>
            <th className="pb-2">Revenue</th>
            <th className="pb-2">Avg Price</th>
            <th className="pb-2">Orders</th>
          </tr>
        </thead>
        <tbody>
          {topProducts.map((product, i) => (
            <tr key={product.id} className="border-b last:border-0">
              <td className="py-3 flex items-center gap-3">
                <span className="text-gray-400 w-6">{i + 1}</span>
                <img
                  src={product.image_url}
                  alt=""
                  className="w-10 h-10 rounded object-cover"
                />
                <span className="font-medium">{product.name}</span>
              </td>
              <td>{Number(product.total_quantity).toLocaleString()}</td>
              <td className="font-semibold">
                ${Number(product.total_revenue).toLocaleString()}
              </td>
              <td>${Number(product.avg_price).toFixed(2)}</td>
              <td>{Number(product.order_count).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---- DashboardFilters.tsx (Client Component — interactive) ----
'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useTransition } from 'react';

export function DashboardFilters({ currentRange }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const handleRangeChange = (range) => {
    startTransition(() => {
      const params = new URLSearchParams(searchParams);
      params.set('range', range);
      router.push(`?${params.toString()}`);
      // This triggers a new Server Component render!
      // All the Server Components re-execute with the new date range.
    });
  };

  const ranges = [
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: '90d', label: '90 Days' },
    { value: '1y', label: '1 Year' },
  ];

  return (
    <div className="flex items-center gap-2">
      {isPending && <span className="text-sm text-gray-400">Updating...</span>}
      {ranges.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => handleRangeChange(value)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            currentRange === value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          disabled={isPending}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

// ---- actions/export.ts (Server Action for CSV export) ----
'use server';

import { db } from '@/lib/database';
import { requireAuth } from '@/lib/auth';

export async function exportProductReport(startDate, endDate) {
  const user = await requireAuth();

  const products = await db.$queryRaw`
    SELECT p.name, SUM(oi.quantity) as units, SUM(oi.subtotal) as revenue
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    JOIN products p ON p.id = oi.product_id
    WHERE o.user_id = ${user.id}
      AND o.created_at BETWEEN ${startDate}::timestamp AND ${endDate}::timestamp
    GROUP BY p.name ORDER BY revenue DESC
  `;

  const csv = [
    'Product,Units Sold,Revenue',
    ...products.map(p => `"${p.name}",${p.units},${p.revenue}`),
  ].join('\n');

  return csv;  // Return to client for download
}
```

**Bundle size analysis for this dashboard:**

| Component | Traditional CSR Bundle | RSC Architecture |
|---|---|---|
| Prisma client | ~150KB | 0KB (server only) |
| SQL queries / data logic | ~20KB | 0KB (server only) |
| date-fns | ~20KB | 0KB (server only) |
| Table rendering logic | ~15KB | 0KB (server only) |
| Metric cards | ~5KB | 0KB (server only) |
| **Recharts** (interactive) | **~120KB** | **~120KB** (client) |
| **DashboardFilters** | **~3KB** | **~3KB** (client) |
| **ExportButton** | **~1KB** | **~1KB** (client) |
| React runtime | ~40KB | ~40KB |
| **TOTAL** | **~374KB** | **~164KB** |

**That's a 56% bundle reduction** — and the initial content (metric cards, table) streams to the user before the chart JS even downloads. On a 3G connection, this difference is the gap between a 3-second load and a 7-second load.

**Key architectural takeaways:**
1. **Server Components are the orchestrators** — they fetch data and compose the page
2. **Client Components are the interactive islands** — minimal, focused, leaf-level
3. **Suspense boundaries enable independent streaming** — slow sections don't block fast ones
4. **Server Actions replace API routes** — mutations are just function calls
5. **Data flows from DB → Server Component → serialized props → Client Component** — no intermediate API layer
6. **The URL is the state** — filter changes update searchParams, which triggers a full Server Component re-render with fresh data

---

## Quick Reference: RSC Decision Tree

```
Is your component interactive? (state, events, browser APIs)
├── YES → 'use client' (Client Component)
│         Keep it as small as possible.
│         Can it be split? Move data display to a Server Component,
│         keep only the interactive part as Client.
│
└── NO → Server Component (default)
          Does it fetch data? → async function, direct DB access
          Does it use heavy libs? → Zero bundle cost
          Does it render static content? → Perfect for SC
          Need to wrap a Client Component? → Pass SC as children
```

---

## Key Terms Glossary

| Term | Definition |
|---|---|
| **RSC Payload** | The serialized wire format that Server Components produce — a compact description of the rendered tree, not HTML |
| **Client Boundary** | The `'use client'` directive that marks where client-side code begins |
| **Server Action** | An async function marked with `'use server'` that runs on the server but is callable from the client |
| **Hydration** | The process of attaching event handlers and state to server-rendered HTML (only for Client Components) |
| **Selective Hydration** | React's ability to hydrate the most urgent parts of the page first |
| **Streaming** | Sending the RSC payload incrementally as each Suspense boundary resolves |
| **Zero-Bundle-Size** | Server Component dependencies that never appear in the client JavaScript bundle |
| **The Donut Pattern** | A Client Component wrapping Server Component children passed via props |
| **Request Memoization** | Automatic deduplication of identical fetch calls within a single server render |
| **Partial Pre-Rendering (PPR)** | Next.js feature that serves static shells from the edge with dynamic content streamed in |
