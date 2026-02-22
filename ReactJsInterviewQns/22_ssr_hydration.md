# Server-Side Rendering (SSR) & Hydration — React 18 Interview Questions

## Topic Introduction

**Server-Side Rendering (SSR)** is a technique where the React component tree is rendered to HTML on the server and sent to the browser as a fully-formed HTML document. The browser can immediately display the HTML to the user — no JavaScript needs to execute before meaningful content appears on screen. This dramatically improves **First Contentful Paint (FCP)** and **Largest Contentful Paint (LCP)**, and it is essential for **SEO** because search engine crawlers receive complete HTML rather than an empty `<div id="root"></div>` that would only be populated by client-side JavaScript. In React 18, SSR received a major overhaul: the legacy `renderToString` API was joined by the new **streaming** APIs (`renderToPipeableStream` for Node.js and `renderToReadableStream` for Web Streams), which allow the server to progressively flush HTML chunks to the browser as components resolve. This fundamentally changes how we think about SSR — instead of waiting for the entire tree to be ready before sending any HTML, the server can start sending content immediately, and components wrapped in `<Suspense>` boundaries can stream in later, complete with their hydration scripts.

**Hydration** is the process by which React "takes over" server-rendered HTML on the client side. When the browser receives the SSR HTML and loads the JavaScript bundle, React walks the existing DOM nodes and attaches event handlers, reconciles its internal fiber tree with the already-present markup, and makes the page fully interactive. In React 18, hydration became **selective**: React can now hydrate different parts of the page independently, prioritising the sections the user is interacting with. If a user clicks on a component that hasn't hydrated yet, React will eagerly hydrate that subtree first. This is orchestrated via `<Suspense>` boundaries — each boundary acts as a hydration unit that can proceed at its own pace, enabling near-instant interactivity for critical above-the-fold content while deferring hydration of less important below-the-fold sections. The new `hydrateRoot` API (replacing the legacy `ReactDOM.hydrate`) powers this concurrent hydration model.

Together, SSR and hydration form the backbone of production React applications that need fast load times, good SEO, and progressive interactivity. Frameworks like Next.js, Remix, and Gatsby abstract many of the low-level details, but understanding the primitives — `renderToPipeableStream`, `hydrateRoot`, `<Suspense>`, streaming, selective hydration, state serialization, and error handling — is what separates a developer who merely uses a framework from one who can debug, optimize, and architect high-performance SSR systems at scale.

```jsx
// Minimal React 18 SSR + Hydration example

// ---- server.js (Node / Express) ----
import express from "express";
import React from "react";
import { renderToPipeableStream } from "react-dom/server";
import App from "./App";

const app = express();
app.use(express.static("public"));

app.get("*", (req, res) => {
  const { pipe } = renderToPipeableStream(<App url={req.url} />, {
    bootstrapScripts: ["/bundle.js"],
    onShellReady() {
      // The shell (everything outside <Suspense> boundaries) is ready
      res.setHeader("Content-Type", "text/html");
      res.statusCode = 200;
      pipe(res);
    },
    onShellError(error) {
      res.statusCode = 500;
      res.send("<h1>Something went wrong</h1>");
    },
    onError(error) {
      console.error("SSR streaming error:", error);
    },
  });
});

app.listen(3000);

// ---- client.js (browser entry) ----
import React from "react";
import { hydrateRoot } from "react-dom/client";
import App from "./App";

hydrateRoot(document.getElementById("root"), <App url={window.location.pathname} />);
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is Server-Side Rendering (SSR) and why would you use it over Client-Side Rendering?

**Answer:**

**Server-Side Rendering (SSR)** means that the React component tree is rendered to HTML on the server for every request. The server sends complete HTML to the browser, which can display it immediately without waiting for JavaScript to download and execute.

The three primary motivations for SSR are:

1. **SEO** — Search engine crawlers receive fully-rendered HTML. While Google's crawler can execute JavaScript, many crawlers cannot, and even Google's rendering queue introduces delays. SSR ensures your content is indexed immediately and reliably.

2. **Faster First Paint** — In a CSR (Client-Side Rendering) app, the browser receives an empty HTML shell, downloads a large JS bundle, parses and executes it, then renders the UI. With SSR, the browser paints meaningful content as soon as the HTML arrives, before any JS executes. This improves **FCP** (First Contentful Paint) and **LCP** (Largest Contentful Paint).

3. **Performance on slow devices / networks** — SSR shifts the rendering work from the user's device (which may be a low-end phone) to the server (which is powerful). The user sees content faster, and the JavaScript bundle handles only interactivity (hydration), not initial rendering.

The trade-off is **server load** — every request requires CPU on the server to render the tree, and **Time to Interactive (TTI)** may not improve if the JS bundle is large, because the page looks ready but isn't interactive until hydration completes.

```jsx
// Client-Side Rendering — user sees blank page until JS loads
// index.html
<html>
  <body>
    <div id="root"></div>  <!-- empty! -->
    <script src="/bundle.js"></script>
  </body>
</html>

// Server-Side Rendering — user sees content immediately
// The server sends:
<html>
  <body>
    <div id="root">
      <header><nav>...</nav></header>
      <main>
        <h1>Welcome to our store</h1>
        <div class="product-grid">
          <div class="product-card">Product 1 — $29.99</div>
          <div class="product-card">Product 2 — $49.99</div>
          <!-- ... fully rendered product listing ... -->
        </div>
      </main>
    </div>
    <script src="/bundle.js"></script> <!-- hydration script -->
  </body>
</html>
```

---

### Q2. What are the differences between CSR, SSR, SSG, and ISR?

**Answer:**

These are four rendering strategies for React applications, each suited to different use cases:

| Strategy | When HTML is Generated | Content Freshness | Use Case |
|---|---|---|---|
| **CSR** (Client-Side Rendering) | In the browser at runtime | Always fresh (fetches live data) | Dashboards, SPAs behind auth |
| **SSR** (Server-Side Rendering) | On the server per request | Fresh per request | E-commerce PLPs, search results, user-specific pages |
| **SSG** (Static Site Generation) | At build time | Stale until rebuild | Blogs, docs, marketing pages |
| **ISR** (Incremental Static Regeneration) | At build time + revalidated in background | Fresh within revalidation window | Product pages, content-heavy sites with frequent updates |

**CSR** sends a minimal HTML shell and relies entirely on client JavaScript. Great for authenticated dashboards where SEO doesn't matter.

**SSR** generates HTML on every request. Ideal when content changes per user/request (personalisation, search results) or when SEO is critical.

**SSG** generates all pages at build time as static `.html` files. Fastest possible TTFB since you serve pre-built files from a CDN. But any content change requires a full rebuild (or ISR).

**ISR** (a Next.js concept) is SSG with a twist — pages are statically generated at build time but can be **revalidated** in the background after a configurable time interval. The first request after the interval triggers a server-side re-render, and subsequent visitors get the updated static page.

```jsx
// Next.js examples showing all four strategies in one codebase

// 1. CSR — no data fetching at build/request time, everything in useEffect
function Dashboard() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch("/api/analytics").then((r) => r.json()).then(setData);
  }, []);
  return data ? <Chart data={data} /> : <Spinner />;
}

// 2. SSR — fresh data every request
export async function getServerSideProps(context) {
  const products = await db.products.findMany({
    where: { category: context.query.category },
  });
  return { props: { products } };
}

// 3. SSG — generated once at build time
export async function getStaticProps() {
  const posts = await cms.getPosts();
  return { props: { posts } };
}

// 4. ISR — SSG + revalidation every 60 seconds
export async function getStaticProps() {
  const products = await db.products.findMany();
  return {
    props: { products },
    revalidate: 60, // Regenerate page in the background every 60s
  };
}
```

---

### Q3. What are `renderToString` and `renderToPipeableStream`, and how do they differ in React 18?

**Answer:**

Both are React DOM Server APIs that render your component tree to HTML on the server, but they work very differently:

**`renderToString`** (legacy) is a **synchronous, blocking** call. It renders the entire component tree to a single HTML string and returns it. It does not support `<Suspense>` on the server — if a component suspends, `renderToString` throws an error (or renders the fallback, depending on the React version). Because it is synchronous, it blocks the Node.js event loop for the entire duration of the render, which limits server throughput.

**`renderToPipeableStream`** (React 18, Node.js) is an **asynchronous, streaming** API. It returns a stream that you can pipe into the HTTP response. It fully supports `<Suspense>` — the "shell" (everything outside `<Suspense>` boundaries) is flushed first, and suspended subtrees are streamed in later as they resolve. This means the browser starts receiving and painting HTML immediately instead of waiting for the slowest data source. It also doesn't block the event loop.

```jsx
// ---- renderToString (legacy, synchronous) ----
import { renderToString } from "react-dom/server";

app.get("/", (req, res) => {
  // Blocks the event loop until the ENTIRE tree is rendered
  const html = renderToString(<App />);

  res.send(`
    <!DOCTYPE html>
    <html>
      <body>
        <div id="root">${html}</div>
        <script src="/bundle.js"></script>
      </body>
    </html>
  `);
});

// ---- renderToPipeableStream (React 18, streaming) ----
import { renderToPipeableStream } from "react-dom/server";

app.get("/", (req, res) => {
  const { pipe, abort } = renderToPipeableStream(
    <App />,
    {
      bootstrapScripts: ["/bundle.js"],
      onShellReady() {
        // Shell HTML (outside <Suspense>) is ready — start streaming
        res.statusCode = 200;
        res.setHeader("Content-Type", "text/html");
        pipe(res);
        // Suspended subtrees will stream in as they resolve
      },
      onAllReady() {
        // Everything including all Suspense boundaries is resolved
        // Useful for crawlers — wait for full HTML before responding
      },
      onShellError(error) {
        // Shell itself failed — send a fallback
        res.statusCode = 500;
        res.send("<h1>Server Error</h1>");
      },
      onError(error) {
        console.error("Streaming error:", error);
      },
    }
  );

  // Timeout: abort if rendering takes too long
  setTimeout(() => abort(), 10000);
});
```

The key takeaway: **use `renderToPipeableStream` in new React 18 projects**. It is strictly superior — it supports streaming, `<Suspense>`, selective hydration, and does not block the event loop.

---

### Q4. What is hydration, and how does React attach event handlers to server-rendered HTML?

**Answer:**

**Hydration** is the process of making server-rendered HTML interactive. When the server sends pre-rendered HTML to the browser, it's just static markup — clicking a button does nothing because no JavaScript event handlers are attached. Hydration is the step where React "takes over" that static HTML.

Here's what happens during hydration:

1. React loads in the browser and calls `hydrateRoot(container, <App />)`.
2. React traverses its virtual component tree (same tree that was rendered on the server) and the existing DOM simultaneously.
3. Instead of creating new DOM nodes (as it would in a fresh `createRoot().render()`), React **reuses** the existing DOM nodes.
4. React attaches event handlers (`onClick`, `onChange`, etc.) to the DOM nodes.
5. React sets up internal fiber data structures so it can manage future updates.
6. After hydration completes, the page is fully interactive.

In React 18, `hydrateRoot` replaces the legacy `ReactDOM.hydrate`. The new API enables **concurrent hydration** — React can pause hydration to handle user events and resume it later, preventing long hydration tasks from blocking the main thread.

```jsx
// ---- Legacy hydration (React 17) ----
import ReactDOM from "react-dom";
import App from "./App";

// Synchronous — blocks the main thread for the entire tree
ReactDOM.hydrate(<App />, document.getElementById("root"));

// ---- React 18 hydration ----
import { hydrateRoot } from "react-dom/client";
import App from "./App";

// Concurrent — can yield to browser events mid-hydration
const root = hydrateRoot(document.getElementById("root"), <App />);

// You can later update the root just like createRoot
root.render(<App updated />);
```

```jsx
// Illustrating what hydration does under the hood (conceptual)

// Server sends this HTML:
// <button id="like-btn">Like (0)</button>

// After hydration, React has attached:
function LikeButton() {
  const [count, setCount] = useState(0);

  // This onClick handler is attached during hydration
  // Before hydration: clicking the button does nothing
  // After hydration: clicking increments the count
  return (
    <button onClick={() => setCount((c) => c + 1)}>
      Like ({count})
    </button>
  );
}
```

---

### Q5. What is a hydration mismatch, and how do you fix common causes?

**Answer:**

A **hydration mismatch** occurs when the HTML rendered on the server differs from the HTML that React expects to render on the client during hydration. React compares its virtual tree against the existing DOM, and if they don't match, React logs a warning in development and may need to discard the server-rendered markup and re-render from scratch on the client — losing all the performance benefits of SSR.

**Common causes:**

1. **Browser-only APIs** — Using `window`, `localStorage`, `Date.now()`, or `Math.random()` during render, which produce different values on server vs. client.
2. **Timestamps / time zones** — Server and client may be in different time zones.
3. **Extensions / injected HTML** — Browser extensions modify the DOM before hydration.
4. **Invalid HTML nesting** — e.g., `<p>` inside `<p>`, `<div>` inside `<p>`. Browsers "fix" the HTML, producing a DOM that doesn't match React's tree.
5. **Conditional rendering based on environment** — e.g., `typeof window !== 'undefined' && <ClientOnlyWidget />`.

**How to fix:**

The primary pattern is to defer browser-only content to a `useEffect`, which only runs on the client after hydration:

```jsx
// BAD — causes hydration mismatch
function Greeting() {
  // window.innerWidth is undefined on server, causes mismatch
  const isMobile = window.innerWidth < 768;
  return <p>{isMobile ? "Mobile view" : "Desktop view"}</p>;
}

// GOOD — defer to useEffect
function Greeting() {
  const [isMobile, setIsMobile] = useState(false); // safe default for SSR

  useEffect(() => {
    // Runs only on the client, after hydration
    setIsMobile(window.innerWidth < 768);

    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <p>{isMobile ? "Mobile view" : "Desktop view"}</p>;
}
```

```jsx
// Another common fix: suppressHydrationWarning for content that
// will always differ (e.g., timestamps)
function LastUpdated({ timestamp }) {
  return (
    <time suppressHydrationWarning>
      {new Date(timestamp).toLocaleString()}
    </time>
  );
}

// For entire client-only subtrees, use a "ClientOnly" wrapper
function ClientOnly({ children }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted ? children : null;
}

// Usage
function Page() {
  return (
    <div>
      <h1>Welcome</h1>
      <ClientOnly>
        <BrowserOnlyChart /> {/* Not rendered during SSR at all */}
      </ClientOnly>
    </div>
  );
}
```

---

## Intermediate Level (Q6–Q12)

---

### Q6. How does streaming SSR work in React 18, and what are its benefits?

**Answer:**

Streaming SSR allows the server to **progressively flush HTML to the browser** instead of waiting for the entire page to be ready. In React 18, this is powered by `renderToPipeableStream` and `<Suspense>` boundaries.

**How it works:**

1. The server starts rendering the component tree.
2. When it hits a `<Suspense>` boundary whose child suspends (e.g., waiting for data), it renders the **fallback** as a placeholder and continues rendering the rest of the tree.
3. Once the "shell" (everything outside suspended boundaries) is ready, the `onShellReady` callback fires and the server begins piping HTML to the browser.
4. The browser receives and paints the shell HTML immediately.
5. As each suspended component resolves, the server streams an additional HTML chunk — a `<template>` tag containing the resolved content plus an inline `<script>` that swaps the fallback with the real content.
6. This happens progressively: fast data sources resolve first, slow ones arrive later.

**Benefits:**

- **TTFB improvement** — The browser starts receiving bytes much sooner.
- **Progressive rendering** — Users see content incrementally instead of waiting for the slowest API.
- **Non-blocking** — The Node.js event loop isn't blocked by slow data fetches; rendering yields and resumes.

```jsx
// App component with Suspense boundaries for streaming
import { Suspense } from "react";

function App() {
  return (
    <html>
      <head><title>Streaming SSR</title></head>
      <body>
        <Header />  {/* Renders instantly — part of the shell */}
        
        <Suspense fallback={<ProductGridSkeleton />}>
          {/* ProductGrid fetches data — streams in when ready */}
          <ProductGrid />
        </Suspense>

        <Suspense fallback={<ReviewsSkeleton />}>
          {/* Reviews may take longer — streams independently */}
          <Reviews />
        </Suspense>

        <Footer /> {/* Part of the shell, renders instantly */}
      </body>
    </html>
  );
}
```

```jsx
// Server setup for streaming
import { renderToPipeableStream } from "react-dom/server";

app.get("*", (req, res) => {
  const { pipe, abort } = renderToPipeableStream(<App />, {
    bootstrapScripts: ["/client.js"],
    onShellReady() {
      // Browser receives: <Header />, skeletons, <Footer />
      res.setHeader("Content-Type", "text/html");
      pipe(res);
      // As ProductGrid and Reviews resolve, their HTML
      // is streamed in chunks with inline swap scripts
    },
    onError(error) {
      console.error(error);
    },
  });

  // Safety timeout
  setTimeout(() => abort(), 15000);
});

// What the browser receives over time:
// t=0ms:   <header>...</header><div class="skeleton">...</div><footer>...</footer>
// t=200ms: <template id="s1">...(ProductGrid HTML)...</template><script>swap("s1")</script>
// t=800ms: <template id="s2">...(Reviews HTML)...</template><script>swap("s2")</script>
```

---

### Q7. How does selective hydration work with `<Suspense>` boundaries in React 18?

**Answer:**

**Selective hydration** means React can hydrate different `<Suspense>` boundaries independently, in any order, and can prioritise hydration of components the user is interacting with.

In React 17 and earlier, hydration was an all-or-nothing synchronous process — the entire tree had to hydrate before anything became interactive. In React 18, each `<Suspense>` boundary acts as a **hydration unit**:

1. React starts hydrating the shell.
2. When it encounters a `<Suspense>` boundary, it can hydrate it separately. If the code-split chunk for that boundary hasn't loaded yet, React skips it and continues hydrating other parts.
3. If the user clicks on a component inside a `<Suspense>` boundary that hasn't hydrated yet, React **eagerly prioritises** hydrating that boundary (ahead of others) so the interaction can be processed.
4. This means critical interactive elements (e.g., "Add to Cart" button) hydrate first, while non-critical sections (e.g., footer, recommendations) hydrate later.

```jsx
import { Suspense, lazy } from "react";

// Code-split heavy components
const HeavyRecommendations = lazy(() => import("./Recommendations"));
const HeavyReviews = lazy(() => import("./Reviews"));

function ProductPage({ product }) {
  return (
    <div>
      {/* Shell — hydrates first */}
      <Header />
      <ProductDetails product={product} />
      <AddToCartButton productId={product.id} /> {/* Interactive ASAP */}

      {/* Separate hydration unit — hydrates independently */}
      <Suspense fallback={<RecommendationsSkeleton />}>
        <HeavyRecommendations productId={product.id} />
      </Suspense>

      {/* Another independent hydration unit */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <HeavyReviews productId={product.id} />
      </Suspense>

      <Footer />
    </div>
  );
}

// Hydration priority scenario:
// 1. Page loads — shell hydrates (Header, ProductDetails, AddToCart, Footer)
// 2. Recommendations JS chunk loads — React starts hydrating it in the background
// 3. User scrolls down and clicks "Write a Review" inside <HeavyReviews>
// 4. React PAUSES Recommendations hydration
// 5. React PRIORITISES Reviews hydration so the click can be processed
// 6. Reviews becomes interactive — click is replayed
// 7. React resumes Recommendations hydration
```

```jsx
// Nested Suspense boundaries for fine-grained hydration control
function Dashboard() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardLayout>
        {/* Critical — hydrates with the parent */}
        <KPICards />

        <Suspense fallback={<ChartSkeleton />}>
          {/* Secondary — hydrates after KPICards */}
          <RevenueChart />
        </Suspense>

        <Suspense fallback={<TableSkeleton />}>
          {/* Tertiary — hydrates last (below the fold) */}
          <TransactionsTable />
        </Suspense>
      </DashboardLayout>
    </Suspense>
  );
}
```

---

### Q8. How do you handle data fetching in SSR, and what patterns exist in React 18?

**Answer:**

Data fetching in SSR requires the data to be available **before** or **during** server rendering so it can be included in the HTML. There are several patterns:

**1. Framework-level loaders (recommended for most apps):**

Next.js uses `getServerSideProps` (Pages Router) or Server Components with `async/await` (App Router). Remix uses `loader` functions. These run on the server, fetch data, and pass it as props to your component.

**2. React 18 Suspense with data fetching:**

React 18's streaming SSR natively supports components that "suspend" while waiting for data. Libraries like React Query, SWR, or custom cache implementations integrate with Suspense to trigger data fetching and suspension.

**3. State serialization (window.__INITIAL_STATE__):**

After fetching data on the server, you serialize it into a `<script>` tag so the client can pick it up during hydration without refetching.

```jsx
// Pattern 1: Next.js getServerSideProps
export async function getServerSideProps(context) {
  const { slug } = context.params;
  const product = await db.products.findUnique({ where: { slug } });

  if (!product) {
    return { notFound: true };
  }

  return {
    props: {
      product: JSON.parse(JSON.stringify(product)), // serialize dates
    },
  };
}

function ProductPage({ product }) {
  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <span>${product.price}</span>
    </div>
  );
}
```

```jsx
// Pattern 2: Remix loaders
import { json } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";

export async function loader({ params }) {
  const product = await db.products.findUnique({
    where: { slug: params.slug },
  });

  if (!product) throw new Response("Not Found", { status: 404 });

  return json(product, {
    headers: {
      "Cache-Control": "public, max-age=300, stale-while-revalidate=600",
    },
  });
}

export default function ProductPage() {
  const product = useLoaderData();
  return (
    <div>
      <h1>{product.name}</h1>
      <p>${product.price}</p>
    </div>
  );
}
```

```jsx
// Pattern 3: Suspense-based data fetching with streaming SSR
// A cache that integrates with React Suspense
const dataCache = new Map();

function fetchWithSuspense(key, fetcher) {
  if (!dataCache.has(key)) {
    const promise = fetcher().then(
      (data) => dataCache.set(key, { status: "resolved", data }),
      (error) => dataCache.set(key, { status: "rejected", error })
    );
    dataCache.set(key, { status: "pending", promise });
  }

  const entry = dataCache.get(key);
  if (entry.status === "pending") throw entry.promise;   // Suspends!
  if (entry.status === "rejected") throw entry.error;
  return entry.data;
}

function ProductDetails({ slug }) {
  // This will suspend on the server — streaming SSR handles it gracefully
  const product = fetchWithSuspense(`product-${slug}`, () =>
    fetch(`https://api.example.com/products/${slug}`).then((r) => r.json())
  );

  return <h1>{product.name}</h1>;
}

// In the server-rendered App:
function App() {
  return (
    <Suspense fallback={<ProductSkeleton />}>
      <ProductDetails slug="awesome-widget" />
    </Suspense>
  );
}
```

---

### Q9. How do you set up SSR with React Router (using `createStaticHandler`)?

**Answer:**

React Router v6.4+ provides dedicated SSR utilities: `createStaticHandler` for running loaders on the server, `createStaticRouter` for building a server-side router, and `StaticRouterProvider` for rendering. This gives you a Remix-like data loading pattern without using Remix.

The flow is:

1. Define your routes with `loader` functions (data fetching) and component mappings.
2. On the server, create a `staticHandler`, pass in the incoming request, and call `handler.query(request)` — this runs all matching route loaders.
3. Build a `staticRouter` from the handler context.
4. Render `<StaticRouterProvider>` with the router and context.
5. On the client, use `createBrowserRouter` with the same routes and hydrate with `hydrateRoot`.

```jsx
// routes.js — shared between server and client
import { lazy } from "react";

const Home = lazy(() => import("./pages/Home"));
const Product = lazy(() => import("./pages/Product"));

export const routes = [
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Home />,
        loader: async () => {
          const res = await fetch("https://api.example.com/featured");
          return res.json();
        },
      },
      {
        path: "products/:slug",
        element: <Product />,
        loader: async ({ params }) => {
          const res = await fetch(`https://api.example.com/products/${params.slug}`);
          if (!res.ok) throw new Response("Not Found", { status: 404 });
          return res.json();
        },
      },
    ],
  },
];
```

```jsx
// server.js — Express SSR with React Router static handler
import express from "express";
import { renderToPipeableStream } from "react-dom/server";
import {
  createStaticHandler,
  createStaticRouter,
  StaticRouterProvider,
} from "react-router-dom/server";
import { routes } from "./routes";

const app = express();
app.use(express.static("public"));

app.get("*", async (req, res) => {
  // 1. Create a static handler with your routes
  const handler = createStaticHandler(routes);

  // 2. Convert Express request to a Fetch API Request
  const fetchRequest = new Request(`http://${req.headers.host}${req.url}`, {
    method: req.method,
    headers: new Headers(req.headers),
  });

  // 3. Run loaders — this fetches all data for matching routes
  const context = await handler.query(fetchRequest);

  // If a loader threw a redirect Response, handle it
  if (context instanceof Response) {
    return res.redirect(context.status, context.headers.get("Location"));
  }

  // 4. Create a static router from the context
  const router = createStaticRouter(handler.dataRoutes, context);

  // 5. Render with streaming
  const { pipe } = renderToPipeableStream(
    <StaticRouterProvider router={router} context={context} />,
    {
      bootstrapScripts: ["/client.js"],
      onShellReady() {
        res.setHeader("Content-Type", "text/html");
        pipe(res);
      },
    }
  );
});

app.listen(3000);
```

```jsx
// client.js — Hydrate with browser router
import { hydrateRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { routes } from "./routes";

const router = createBrowserRouter(routes);

hydrateRoot(
  document.getElementById("root"),
  <RouterProvider router={router} />
);
```

---

### Q10. How do you handle environment-specific code (browser-only APIs) in an SSR application?

**Answer:**

In an SSR application, your component code runs in two environments: **Node.js (server)** and the **browser (client)**. Many browser APIs (`window`, `document`, `localStorage`, `navigator`, `IntersectionObserver`, etc.) don't exist on the server. Accessing them during server rendering throws errors or causes hydration mismatches.

**Strategies:**

1. **`useEffect` / `useLayoutEffect`** — These hooks only run on the client. Put all browser-only logic inside them.
2. **`typeof window` checks** — Guard environment-specific code with runtime checks. But avoid using these checks to conditionally render different UI (causes hydration mismatches).
3. **Dynamic imports with `next/dynamic` or `React.lazy`** — Load browser-only components only on the client.
4. **`isServer` utility** — Create a helper constant for clean guards.

```jsx
// Strategy 1: useEffect for browser-only side effects
function AnalyticsTracker({ page }) {
  useEffect(() => {
    // Safe — only runs in the browser
    window.gtag("event", "page_view", { page_path: page });
  }, [page]);

  return null; // Renders nothing
}
```

```jsx
// Strategy 2: typeof window guard (for non-rendering logic)
function getAuthToken() {
  if (typeof window === "undefined") {
    // Server — read from request cookies (passed via context)
    return null;
  }
  // Client — read from localStorage
  return localStorage.getItem("auth_token");
}
```

```jsx
// Strategy 3: Dynamic imports — load a component only on the client
// Next.js approach
import dynamic from "next/dynamic";

const MapView = dynamic(() => import("./MapView"), {
  ssr: false, // Don't render on server at all
  loading: () => <div className="map-skeleton">Loading map…</div>,
});

function StoreLocator({ stores }) {
  return (
    <div>
      <h1>Find a Store</h1>
      <StoreList stores={stores} /> {/* SSR-safe */}
      <MapView stores={stores} />  {/* Client-only, uses Leaflet/Google Maps */}
    </div>
  );
}
```

```jsx
// Strategy 4: A reusable "ClientOnly" boundary
import { useState, useEffect, type ReactNode } from "react";

function ClientOnly({ children, fallback = null }: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
  }, []);

  if (!hasMounted) return fallback;
  return children;
}

// Usage — no hydration mismatch because server and initial client
// render both show the fallback
function ThemeSwitcher() {
  return (
    <ClientOnly fallback={<div style={{ width: 40, height: 40 }} />}>
      <ThemeSwitcherWithLocalStorage />
    </ClientOnly>
  );
}
```

---

### Q11. How do you handle CSS in SSR to avoid Flash of Unstyled Content (FOUC)?

**Answer:**

In SSR, the server sends HTML but not necessarily the styles that go with it. If CSS is loaded asynchronously (e.g., via JS bundles in a CSR setup), the user sees a flash of unstyled content before the CSS loads and applies. This is called **FOUC**.

**Strategies to avoid FOUC:**

1. **Critical CSS extraction** — Extract CSS used by the rendered components and inline it in the `<head>` of the SSR response.
2. **CSS Modules / compiled CSS** — Tools like CSS Modules, Tailwind CSS, or Vanilla Extract generate CSS at build time. The SSR framework includes `<link>` tags for the relevant CSS files in the HTML.
3. **CSS-in-JS with SSR support** — Libraries like styled-components, Emotion, and Stitches have server-side APIs that collect styles during render and inject them into the `<head>`.

```jsx
// styled-components SSR — collecting and injecting critical CSS
import { renderToString } from "react-dom/server";
import { ServerStyleSheet } from "styled-components";

app.get("*", (req, res) => {
  const sheet = new ServerStyleSheet();

  try {
    // Wrap the app to collect styles during render
    const html = renderToString(
      sheet.collectStyles(<App />)
    );

    // Get all the style tags as a string
    const styleTags = sheet.getStyleTags();

    res.send(`
      <!DOCTYPE html>
      <html>
        <head>
          ${styleTags}  <!-- Critical CSS inlined in <head> -->
        </head>
        <body>
          <div id="root">${html}</div>
          <script src="/bundle.js"></script>
        </body>
      </html>
    `);
  } finally {
    sheet.seal(); // Clean up
  }
});
```

```jsx
// Emotion SSR with streaming (React 18 compatible)
import { renderToPipeableStream } from "react-dom/server";
import createEmotionServer from "@emotion/server/create-instance";
import createCache from "@emotion/cache";
import { CacheProvider } from "@emotion/react";

app.get("*", (req, res) => {
  const cache = createCache({ key: "css" });
  const { extractCriticalToChunks, constructStyleTagsFromChunks } =
    createEmotionServer(cache);

  // For streaming, Emotion integrates differently —
  // you can use a transform stream to inject styles
  const { pipe } = renderToPipeableStream(
    <CacheProvider value={cache}>
      <App />
    </CacheProvider>,
    {
      bootstrapScripts: ["/bundle.js"],
      onShellReady() {
        res.setHeader("Content-Type", "text/html");
        pipe(res);
      },
    }
  );
});
```

```jsx
// Tailwind CSS / CSS Modules — simplest approach for SSR
// CSS is extracted at build time, no runtime collection needed

// Next.js automatically handles this:
// - CSS Modules: import styles from "./Button.module.css"
// - Global CSS: imported in _app.tsx
// - Tailwind: className="bg-blue-500 text-white p-4 rounded"
// The framework injects <link> tags in the <head> for SSR pages

function ProductCard({ product }) {
  return (
    <div className="bg-white shadow-lg rounded-xl p-6 hover:shadow-xl transition-shadow">
      <img
        src={product.image}
        alt={product.name}
        className="w-full h-48 object-cover rounded-lg"
      />
      <h2 className="text-xl font-bold mt-4">{product.name}</h2>
      <p className="text-gray-600 mt-2">${product.price}</p>
    </div>
  );
}
```

---

### Q12. What caching strategies can you use with SSR to reduce server load?

**Answer:**

SSR is CPU-intensive — every request triggers a full React render on the server. Caching is essential for production SSR at scale. There are several layers:

**1. Full-page cache (CDN / reverse proxy):**
Cache the entire SSR HTML response at the CDN edge. Best for pages that are the same for all users (product pages, blog posts). Use `Cache-Control` headers to control TTL.

**2. Stale-while-revalidate (SWR):**
Serve a stale cached page immediately while revalidating in the background. Users get instant responses, and the cache is updated asynchronously.

**3. Fragment / component cache:**
Cache individual component renders (HTML fragments) on the server. Useful when a page has a mix of static and dynamic sections — cache the static parts, render only the dynamic parts per request.

**4. Data cache:**
Cache API/database responses so that even when you do SSR, the data fetching is fast. Redis, in-memory LRU caches, or HTTP cache headers on upstream APIs.

**5. ISR (Incremental Static Regeneration):**
A Next.js pattern that statically generates pages at build time and revalidates them on a timer. Essentially an automated SSG + cache invalidation strategy.

```jsx
// 1. Full-page CDN caching with Cache-Control headers
app.get("/products/:slug", async (req, res) => {
  const product = await getProduct(req.params.slug);

  // Cache at CDN for 5 minutes, serve stale for 1 hour while revalidating
  res.setHeader(
    "Cache-Control",
    "public, s-maxage=300, stale-while-revalidate=3600"
  );

  const { pipe } = renderToPipeableStream(<ProductPage product={product} />, {
    bootstrapScripts: ["/bundle.js"],
    onShellReady() {
      res.setHeader("Content-Type", "text/html");
      pipe(res);
    },
  });
});
```

```jsx
// 2. Fragment / component caching with Redis
import Redis from "ioredis";
import { renderToString } from "react-dom/server";

const redis = new Redis(process.env.REDIS_URL);

async function renderCachedFragment(key, Component, props, ttl = 300) {
  // Check cache first
  const cached = await redis.get(`fragment:${key}`);
  if (cached) return cached;

  // Render the component to string
  const html = renderToString(<Component {...props} />);

  // Cache for future requests (non-blocking)
  redis.set(`fragment:${key}`, html, "EX", ttl);

  return html;
}

// Usage in SSR handler
app.get("/", async (req, res) => {
  // Cache the header and footer (same for all users)
  const headerHtml = await renderCachedFragment("header-v3", Header, {}, 3600);
  const footerHtml = await renderCachedFragment("footer-v3", Footer, {}, 3600);

  // Render user-specific content fresh
  const user = await getUser(req);
  const contentHtml = renderToString(<Dashboard user={user} />);

  res.send(`
    <!DOCTYPE html>
    <html>
      <body>
        ${headerHtml}
        <main id="root">${contentHtml}</main>
        ${footerHtml}
        <script src="/bundle.js"></script>
      </body>
    </html>
  `);
});
```

```jsx
// 3. ISR in Next.js — automatic SSG + background revalidation
export async function getStaticProps({ params }) {
  const product = await db.products.findUnique({
    where: { slug: params.slug },
  });

  return {
    props: { product },
    revalidate: 60, // Revalidate every 60 seconds

    // How it works:
    // 1. First request: page is statically generated and cached
    // 2. For the next 60s: all requests serve the cached static page (instant)
    // 3. After 60s: next request still serves cached page instantly,
    //    but triggers a background re-render
    // 4. Once the re-render completes, the cache is updated
    // 5. Subsequent requests get the updated page
  };
}

// On-demand revalidation (ISR v2) — triggered by webhook
// pages/api/revalidate.js
export default async function handler(req, res) {
  const { slug, secret } = req.query;

  if (secret !== process.env.REVALIDATION_SECRET) {
    return res.status(401).json({ message: "Invalid token" });
  }

  try {
    await res.revalidate(`/products/${slug}`);
    return res.json({ revalidated: true });
  } catch (err) {
    return res.status(500).json({ message: "Error revalidating" });
  }
}
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you optimize SSR performance with streaming, cache headers, and edge rendering?

**Answer:**

Production SSR performance is a multi-layered optimization problem. The three primary axes are: **reducing render time** (streaming), **avoiding unnecessary renders** (caching), and **moving rendering closer to the user** (edge).

**1. Streaming optimizations:**
- Use `renderToPipeableStream` with strategically placed `<Suspense>` boundaries to flush the shell early.
- Ensure the "shell" (header, navigation, layout, above-the-fold content) renders without any data dependencies — it should stream instantly.
- Wrap slow data-dependent sections in `<Suspense>` so they don't block the shell.
- Set timeouts with `abort()` to prevent indefinitely hanging renders.

**2. Cache headers:**
- Use `Cache-Control: public, s-maxage=N, stale-while-revalidate=M` for CDN-cacheable pages.
- Use `Vary: Cookie` or `Vary: Authorization` if pages differ by user (or avoid CDN caching for those).
- Set `ETag` or `Last-Modified` headers for conditional requests.
- Use `private, no-store` for user-specific pages that should never be cached at the CDN.

**3. Edge rendering:**
- Deploy SSR functions to edge locations (Cloudflare Workers, Vercel Edge Functions, Deno Deploy).
- Edge reduces TTFB by eliminating the round trip to a centralised origin server.
- Edge functions have constraints: no Node.js APIs, limited execution time, limited memory.
- Use `renderToReadableStream` (Web Streams API) at the edge instead of `renderToPipeableStream` (Node.js Streams).

```jsx
// Production streaming SSR with performance optimizations
import { renderToPipeableStream } from "react-dom/server";
import { performance } from "perf_hooks";

app.get("*", async (req, res) => {
  const startTime = performance.now();

  // Determine cache strategy based on route
  const isPublicPage = !req.cookies.session_id;
  if (isPublicPage) {
    res.setHeader(
      "Cache-Control",
      "public, s-maxage=300, stale-while-revalidate=3600"
    );
  } else {
    res.setHeader("Cache-Control", "private, no-store");
  }

  let didError = false;

  const { pipe, abort } = renderToPipeableStream(
    <App url={req.url} user={req.user} />,
    {
      bootstrapScripts: ["/static/js/client.js"],
      onShellReady() {
        // Shell is ready — stream it immediately
        res.statusCode = didError ? 500 : 200;
        res.setHeader("Content-Type", "text/html; charset=utf-8");

        // Add Server-Timing header for performance monitoring
        const shellTime = performance.now() - startTime;
        res.setHeader("Server-Timing", `shell;dur=${shellTime.toFixed(1)}`);

        pipe(res);
      },
      onAllReady() {
        // Log total render time for monitoring
        const totalTime = performance.now() - startTime;
        console.log(`SSR complete: ${req.url} in ${totalTime.toFixed(1)}ms`);
      },
      onShellError(error) {
        // Shell failed — fall back to client-side rendering
        res.statusCode = 500;
        res.setHeader("Content-Type", "text/html");
        res.send(`
          <!DOCTYPE html>
          <html>
            <body>
              <div id="root"></div>
              <script src="/static/js/client.js"></script>
            </body>
          </html>
        `);
      },
      onError(error) {
        didError = true;
        console.error("SSR error:", error);
      },
    }
  );

  // Hard timeout — abort after 10 seconds
  setTimeout(() => {
    abort();
  }, 10000);
});
```

```jsx
// Edge SSR with renderToReadableStream (Cloudflare Workers / Vercel Edge)
import { renderToReadableStream } from "react-dom/server";

export default {
  async fetch(request) {
    const url = new URL(request.url);

    const stream = await renderToReadableStream(
      <App url={url.pathname} />,
      {
        bootstrapScripts: ["/client.js"],
        onError(error) {
          console.error("Edge SSR error:", error);
        },
      }
    );

    // Optionally wait for all content (for crawlers)
    const userAgent = request.headers.get("user-agent") || "";
    if (/googlebot|bingbot/i.test(userAgent)) {
      await stream.allReady; // Wait for full HTML before responding
    }

    return new Response(stream, {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "public, s-maxage=300, stale-while-revalidate=3600",
      },
    });
  },
};
```

---

### Q14. How do you handle errors in SSR using `onError`, `onShellError`, and error boundaries?

**Answer:**

React 18's `renderToPipeableStream` provides granular error handling through several callbacks, and React's error boundaries work during SSR as well (with caveats).

**Error callback types:**

- **`onShellError(error)`** — Called when the shell (content outside `<Suspense>` boundaries) fails to render. This is a critical failure — you typically respond with a 500 status and a fallback HTML page. The stream is not usable after this.

- **`onError(error)`** — Called for any error during rendering, including errors inside `<Suspense>` boundaries. If an error occurs inside a `<Suspense>` boundary, the server emits the fallback HTML for that boundary, and the client error boundary can catch it during hydration. Use this for logging/monitoring.

- **Error Boundaries** — On the server, error boundaries catch errors and render their fallback UI. The fallback is included in the SSR HTML. On the client, the error boundary is hydrated with the fallback, and if the component succeeds on the client, it can recover.

```jsx
// Error boundary component
class SSRErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log to monitoring service (client-side only)
    if (typeof window !== "undefined") {
      logErrorToService(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="error-container">
            <h2>Something went wrong</h2>
            <p>We're working on fixing this. Please try refreshing.</p>
            <button onClick={() => this.setState({ hasError: false })}>
              Try again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
```

```jsx
// Full error handling strategy in SSR
import { renderToPipeableStream } from "react-dom/server";

app.get("*", (req, res) => {
  let shellErrored = false;
  const errors = [];

  const { pipe, abort } = renderToPipeableStream(
    <SSRErrorBoundary fallback={<AppLevelError />}>
      <App url={req.url} />
    </SSRErrorBoundary>,
    {
      bootstrapScripts: ["/client.js"],

      onShellReady() {
        // Shell rendered (possibly with error boundary fallbacks)
        res.statusCode = shellErrored ? 500 : 200;
        res.setHeader("Content-Type", "text/html");
        pipe(res);
      },

      onShellError(error) {
        // CRITICAL: The entire shell failed — can't even render the layout
        // This means error boundaries couldn't catch it
        // Send a completely static fallback
        shellErrored = true;
        console.error("Shell error:", error);

        res.statusCode = 500;
        res.setHeader("Content-Type", "text/html");
        res.send(`
          <!DOCTYPE html>
          <html>
            <head><title>Error</title></head>
            <body>
              <h1>Server Error</h1>
              <p>Something went wrong. Please try again later.</p>
              <div id="root"></div>
              <script src="/client.js"></script>
            </body>
          </html>
        `);
      },

      onError(error) {
        // Called for ALL errors (shell + Suspense boundaries)
        // Log every error for monitoring
        errors.push({
          message: error.message,
          stack: error.stack,
          url: req.url,
          timestamp: Date.now(),
        });
        console.error("SSR error:", error);

        // Report to monitoring (Sentry, DataDog, etc.)
        reportToMonitoring(error, { url: req.url, userAgent: req.headers["user-agent"] });
      },

      onAllReady() {
        if (errors.length > 0) {
          console.warn(
            `SSR for ${req.url} completed with ${errors.length} error(s)`
          );
        }
      },
    }
  );

  // Abort on timeout to prevent hanging requests
  setTimeout(() => {
    abort(new Error(`SSR timeout for ${req.url}`));
  }, 10000);
});
```

```jsx
// Granular error handling with nested Suspense + Error Boundaries
function ProductPage({ productId }) {
  return (
    <div>
      <Header /> {/* Critical — if this errors, the shell errors */}

      {/* Error in reviews won't crash the page */}
      <SSRErrorBoundary fallback={<p>Could not load reviews.</p>}>
        <Suspense fallback={<ReviewsSkeleton />}>
          <Reviews productId={productId} />
        </Suspense>
      </SSRErrorBoundary>

      {/* Error in recommendations is isolated too */}
      <SSRErrorBoundary fallback={<p>Could not load recommendations.</p>}>
        <Suspense fallback={<RecommendationsSkeleton />}>
          <Recommendations productId={productId} />
        </Suspense>
      </SSRErrorBoundary>
    </div>
  );
}
// If Reviews throws during SSR:
// 1. onError callback fires (for logging)
// 2. The Suspense fallback (<ReviewsSkeleton />) is sent in the HTML
// 3. The ErrorBoundary's fallback ("Could not load reviews") renders on the client
// 4. The rest of the page is unaffected
```

---

### Q15. How do you manage meta tags and SEO in SSR (document head management)?

**Answer:**

SEO in SSR requires dynamically setting `<title>`, `<meta>`, Open Graph tags, structured data (JSON-LD), canonical URLs, and other `<head>` elements based on the rendered page's content. Since the server sends the full HTML, these tags must be set **during the server render**, not after hydration.

**Libraries for head management:**

- **react-helmet-async** — A fork of react-helmet designed for SSR and concurrent rendering. Uses a `HelmetProvider` with a server-side `context` to collect head tags.
- **Next.js `<Head>`** — Built-in component in the Pages Router.
- **Next.js `generateMetadata`** — App Router's server-first approach.
- **Remix `meta` export** — Route-level meta function.

```jsx
// react-helmet-async — SSR-compatible head management

// App component
import { Helmet, HelmetProvider } from "react-helmet-async";

function ProductPage({ product }) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.description,
    image: product.image,
    offers: {
      "@type": "Offer",
      price: product.price,
      priceCurrency: "USD",
      availability: product.inStock
        ? "https://schema.org/InStock"
        : "https://schema.org/OutOfStock",
    },
  };

  return (
    <>
      <Helmet>
        <title>{product.name} | MyStore</title>
        <meta name="description" content={product.description.slice(0, 160)} />

        {/* Open Graph */}
        <meta property="og:title" content={product.name} />
        <meta property="og:description" content={product.description} />
        <meta property="og:image" content={product.image} />
        <meta property="og:type" content="product" />
        <meta property="og:url" content={`https://mystore.com/products/${product.slug}`} />

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={product.name} />

        {/* Canonical */}
        <link rel="canonical" href={`https://mystore.com/products/${product.slug}`} />

        {/* Structured Data (JSON-LD) */}
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      </Helmet>

      <div>
        <h1>{product.name}</h1>
        <p>{product.description}</p>
      </div>
    </>
  );
}
```

```jsx
// Server-side: collecting and injecting head tags
import { renderToString } from "react-dom/server";
import { HelmetProvider } from "react-helmet-async";

app.get("*", (req, res) => {
  const helmetContext = {};

  const html = renderToString(
    <HelmetProvider context={helmetContext}>
      <App url={req.url} />
    </HelmetProvider>
  );

  const { helmet } = helmetContext;

  res.send(`
    <!DOCTYPE html>
    <html ${helmet.htmlAttributes.toString()}>
      <head>
        ${helmet.title.toString()}
        ${helmet.meta.toString()}
        ${helmet.link.toString()}
        ${helmet.script.toString()}
      </head>
      <body ${helmet.bodyAttributes.toString()}>
        <div id="root">${html}</div>
        <script src="/bundle.js"></script>
      </body>
    </html>
  `);
});
```

```jsx
// Next.js App Router — generateMetadata (server-first, no client JS needed)
// app/products/[slug]/page.tsx

export async function generateMetadata({ params }) {
  const product = await getProduct(params.slug);

  return {
    title: `${product.name} | MyStore`,
    description: product.description.slice(0, 160),
    openGraph: {
      title: product.name,
      description: product.description,
      images: [{ url: product.image, width: 1200, height: 630 }],
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: product.name,
      images: [product.image],
    },
    alternates: {
      canonical: `https://mystore.com/products/${params.slug}`,
    },
  };
}

export default async function ProductPage({ params }) {
  const product = await getProduct(params.slug);
  return <ProductDetails product={product} />;
}
```

---

### Q16. How do you handle authentication and session management in SSR?

**Answer:**

Authentication in SSR is fundamentally different from CSR because the server must determine the user's identity **before rendering** so it can return personalised HTML. The primary mechanism is **cookies** — they are automatically sent with every HTTP request to the server. Tokens stored in `localStorage` are not available during SSR.

**Key considerations:**

1. **Cookie-based sessions**: The server reads the session cookie, validates it, and fetches the user's data before rendering.
2. **Token forwarding**: When the SSR server fetches data from backend APIs on behalf of the user, it must forward the user's cookies or authorization headers.
3. **Security**: Never serialize sensitive data (tokens, passwords) into the HTML. Only serialize what the client needs to display.
4. **Cache implications**: Authenticated pages are user-specific and should have `Cache-Control: private, no-store` to prevent CDNs from caching one user's page and serving it to another.

```jsx
// Express middleware to extract user from session cookie
import jwt from "jsonwebtoken";

async function authMiddleware(req, res, next) {
  const token = req.cookies.auth_token;

  if (token) {
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      req.user = await db.users.findUnique({ where: { id: decoded.userId } });
    } catch (err) {
      // Token expired or invalid — user is not authenticated
      req.user = null;
      res.clearCookie("auth_token");
    }
  } else {
    req.user = null;
  }

  next();
}

app.use(authMiddleware);
```

```jsx
// SSR handler that passes user context
app.get("*", (req, res) => {
  // Never cache authenticated pages at the CDN
  if (req.user) {
    res.setHeader("Cache-Control", "private, no-store");
  } else {
    res.setHeader("Cache-Control", "public, s-maxage=300");
  }

  // Safely serializable user data (NO tokens, passwords, etc.)
  const safeUser = req.user
    ? {
        id: req.user.id,
        name: req.user.name,
        email: req.user.email,
        avatarUrl: req.user.avatarUrl,
        role: req.user.role,
      }
    : null;

  const { pipe } = renderToPipeableStream(
    <AuthProvider user={safeUser}>
      <App url={req.url} />
    </AuthProvider>,
    {
      bootstrapScripts: ["/bundle.js"],
      onShellReady() {
        res.setHeader("Content-Type", "text/html");
        pipe(res);
      },
    }
  );
});
```

```jsx
// AuthProvider that works on both server and client
import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ user: initialUser, children }) {
  const [user, setUser] = useState(initialUser);

  // On the client, you can refresh the user from an API if needed
  useEffect(() => {
    if (!initialUser) {
      // No server-side user — check if there's a valid session
      fetch("/api/me", { credentials: "include" })
        .then((r) => (r.ok ? r.json() : null))
        .then(setUser)
        .catch(() => setUser(null));
    }
  }, [initialUser]);

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

// Usage in components
function Header() {
  const { user } = useAuth();

  return (
    <header>
      <nav>
        <Logo />
        {user ? (
          <div>
            <span>Welcome, {user.name}</span>
            <img src={user.avatarUrl} alt={user.name} />
            <LogoutButton />
          </div>
        ) : (
          <LoginButton />
        )}
      </nav>
    </header>
  );
}
```

```jsx
// Forwarding auth cookies when SSR server fetches from backend APIs
async function fetchProductsForUser(req) {
  const response = await fetch("https://api.mystore.com/products/recommended", {
    headers: {
      // Forward the user's cookies to the backend API
      Cookie: req.headers.cookie || "",
      // Or forward an Authorization header
      Authorization: req.headers.authorization || "",
    },
  });

  if (!response.ok) throw new Error("Failed to fetch products");
  return response.json();
}
```

---

### Q17. How do you serialize server state and transfer it to the client (`window.__INITIAL_STATE__`)?

**Answer:**

When the server fetches data and renders HTML, the client needs that same data during hydration — otherwise React would need to re-fetch everything, causing a flash of loading states. **State serialization** is the process of embedding the server-fetched data into the HTML document so the client can pick it up instantly.

The classic pattern is injecting a `<script>` tag that assigns the data to a global variable like `window.__INITIAL_STATE__`. The client reads this variable during initialization to hydrate stores (Redux, Zustand, React Query, etc.) with the same data the server used.

**Critical security concern:** You must protect against **XSS via JSON injection**. If the data contains a `</script>` string (e.g., user-generated content), it can break out of the script tag. Always sanitize the serialized JSON.

```jsx
// Server: serializing state into the HTML
import serialize from "serialize-javascript"; // Safe JSON serialization

app.get("*", async (req, res) => {
  // Fetch data on the server
  const products = await db.products.findMany({ take: 20 });
  const user = req.user
    ? { id: req.user.id, name: req.user.name }
    : null;

  const initialState = {
    products: { items: products, page: 1, hasMore: true },
    auth: { user },
  };

  const html = renderToString(
    <StoreProvider initialState={initialState}>
      <App url={req.url} />
    </StoreProvider>
  );

  res.send(`
    <!DOCTYPE html>
    <html>
      <head><title>MyStore</title></head>
      <body>
        <div id="root">${html}</div>

        <!-- State transfer: serialize-javascript escapes </script>, HTML entities, etc. -->
        <script>
          window.__INITIAL_STATE__ = ${serialize(initialState, { isJSON: true })};
        </script>

        <script src="/bundle.js"></script>
      </body>
    </html>
  `);
});
```

```jsx
// Client: picking up the serialized state
import { hydrateRoot } from "react-dom/client";
import { StoreProvider } from "./store";
import App from "./App";

// Read the serialized state from the global variable
const initialState = window.__INITIAL_STATE__;

// Clean up the global to avoid leaking state
delete window.__INITIAL_STATE__;

hydrateRoot(
  document.getElementById("root"),
  <StoreProvider initialState={initialState}>
    <App url={window.location.pathname} />
  </StoreProvider>
);
```

```jsx
// StoreProvider that initializes from server state
import { createContext, useContext, useReducer } from "react";

const StoreContext = createContext(null);

function storeReducer(state, action) {
  switch (action.type) {
    case "SET_PRODUCTS":
      return { ...state, products: action.payload };
    case "SET_USER":
      return { ...state, auth: { user: action.payload } };
    default:
      return state;
  }
}

const defaultState = {
  products: { items: [], page: 1, hasMore: false },
  auth: { user: null },
};

export function StoreProvider({ initialState, children }) {
  const [state, dispatch] = useReducer(
    storeReducer,
    initialState || defaultState // Use server state if available
  );

  return (
    <StoreContext.Provider value={{ state, dispatch }}>
      {children}
    </StoreContext.Provider>
  );
}

export function useStore() {
  return useContext(StoreContext);
}
```

```jsx
// React Query SSR state transfer (modern approach)
import { QueryClient, QueryClientProvider, dehydrate, Hydrate } from "@tanstack/react-query";

// Server
app.get("*", async (req, res) => {
  const queryClient = new QueryClient();

  // Prefetch queries on the server
  await queryClient.prefetchQuery(["products"], () =>
    fetch("https://api.mystore.com/products").then((r) => r.json())
  );

  // Dehydrate the query cache
  const dehydratedState = dehydrate(queryClient);

  const html = renderToString(
    <QueryClientProvider client={queryClient}>
      <App url={req.url} />
    </QueryClientProvider>
  );

  res.send(`
    <!DOCTYPE html>
    <html>
      <body>
        <div id="root">${html}</div>
        <script>
          window.__REACT_QUERY_STATE__ = ${serialize(dehydratedState, { isJSON: true })};
        </script>
        <script src="/bundle.js"></script>
      </body>
    </html>
  `);

  queryClient.clear(); // Prevent memory leaks
});

// Client
const queryClient = new QueryClient();
const dehydratedState = window.__REACT_QUERY_STATE__;

hydrateRoot(
  document.getElementById("root"),
  <QueryClientProvider client={queryClient}>
    <Hydrate state={dehydratedState}>
      <App url={window.location.pathname} />
    </Hydrate>
  </QueryClientProvider>
);
```

---

### Q18. What is partial hydration and islands architecture, and how do they relate to React?

**Answer:**

**Partial hydration** is the idea that not all server-rendered HTML needs to be hydrated on the client. In a traditional React SSR app, the **entire** component tree is hydrated — even static content like headers, footers, and article text that have no interactivity. This is wasteful because hydration requires downloading the JS for every component, parsing it, and running it.

**Islands architecture** takes this further: the page is treated as a sea of **static HTML** with small **islands of interactivity** that are individually hydrated. Only the interactive islands ship JavaScript to the client. The static parts are server-rendered HTML with zero client-side JS cost.

**React's position:**

- React 18's **selective hydration** (`<Suspense>` boundaries) is a step toward partial hydration — it allows *prioritising* which parts hydrate first, but it still hydrates *everything* eventually.
- **React Server Components (RSC)** are a more direct solution: Server Components render only on the server and send zero JS to the client. Client Components (marked with `"use client"`) are the interactive islands.
- Frameworks like **Astro** implement true islands architecture and can use React components as islands.

```jsx
// React Server Components (Next.js App Router) — partial hydration in practice

// This component is a Server Component (default in App Router)
// It sends ZERO JavaScript to the client
// app/products/[slug]/page.tsx
async function ProductPage({ params }) {
  const product = await db.products.findUnique({
    where: { slug: params.slug },
  });

  return (
    <article>
      {/* All of this is static HTML — no JS shipped for it */}
      <h1>{product.name}</h1>
      <p className="text-lg text-gray-600">{product.description}</p>
      <img src={product.image} alt={product.name} />

      {/* This is an "island" — it has interactivity, so it's a Client Component */}
      <AddToCartButton productId={product.id} price={product.price} />

      {/* Static content continues — no JS */}
      <section>
        <h2>Specifications</h2>
        <SpecTable specs={product.specs} /> {/* Server Component */}
      </section>

      {/* Another interactive island */}
      <ReviewForm productId={product.id} />
    </article>
  );
}
```

```jsx
// AddToCartButton — a Client Component (interactive island)
// app/products/[slug]/AddToCartButton.tsx
"use client";

import { useState, useTransition } from "react";

export function AddToCartButton({ productId, price }) {
  const [quantity, setQuantity] = useState(1);
  const [isPending, startTransition] = useTransition();

  async function handleAddToCart() {
    startTransition(async () => {
      await fetch("/api/cart", {
        method: "POST",
        body: JSON.stringify({ productId, quantity }),
      });
    });
  }

  return (
    <div>
      <select value={quantity} onChange={(e) => setQuantity(Number(e.target.value))}>
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>{n}</option>
        ))}
      </select>
      <button onClick={handleAddToCart} disabled={isPending}>
        {isPending ? "Adding..." : `Add to Cart — $${(price * quantity).toFixed(2)}`}
      </button>
    </div>
  );
}
```

```jsx
// Astro — true islands architecture with React components
// src/pages/product/[slug].astro

---
import Header from "../components/Header.astro";   // Zero JS
import Footer from "../components/Footer.astro";   // Zero JS
import AddToCart from "../components/AddToCart";     // React island
import ReviewCarousel from "../components/ReviewCarousel"; // React island

const product = await getProduct(Astro.params.slug);
---

<html>
  <body>
    <!-- Static HTML — no JavaScript at all -->
    <Header />
    <h1>{product.name}</h1>
    <p>{product.description}</p>

    <!-- React island — hydrated on the client -->
    <!-- client:visible means it hydrates only when scrolled into view -->
    <AddToCart client:load productId={product.id} price={product.price} />

    <!-- This island hydrates lazily when it enters the viewport -->
    <ReviewCarousel client:visible reviews={product.reviews} />

    <Footer />
  </body>
</html>

<!-- Result: only AddToCart + ReviewCarousel JS is shipped to the browser -->
<!-- The rest is static HTML with ZERO JavaScript overhead -->
```

---

### Q19. How does Edge SSR work, and what are the trade-offs of rendering at the edge vs. origin?

**Answer:**

**Edge SSR** means running your SSR logic at CDN edge locations (Cloudflare Workers, Vercel Edge Functions, Deno Deploy, AWS Lambda@Edge) that are geographically distributed close to users. Instead of all SSR requests going to a central origin server, they are handled by the nearest edge node.

**Benefits:**
- **Lower latency** — TTFB drops dramatically (sometimes from 200-500ms to 20-50ms) because the edge node is physically closer to the user.
- **Global performance** — Consistent performance worldwide, not just for users near your origin.
- **Built-in scaling** — Edge platforms auto-scale at each edge location.

**Trade-offs and constraints:**
- **No Node.js runtime** — Edge functions use V8 isolates (like Web Workers), not Node.js. You can't use Node.js APIs (`fs`, `crypto.createHash`, `Buffer`, Node streams). You must use Web APIs.
- **Execution time limits** — Typically 10-50ms CPU time (Cloudflare Workers), though wall-clock time can be longer for I/O.
- **Memory limits** — Much lower than traditional servers (128MB typical).
- **Cold starts** — V8 isolates start faster than containers, but there's still startup overhead.
- **Data proximity** — If your database is in US-East and the user is in Tokyo, the edge node in Tokyo still needs to fetch data from US-East, negating latency benefits. Solutions: regional databases, database replicas, or edge-compatible databases (PlanetScale, Turso, Neon).

```jsx
// Edge SSR with renderToReadableStream (Web Streams API)
// Deployed to Cloudflare Workers or Vercel Edge Functions

import { renderToReadableStream } from "react-dom/server";
import App from "./App";

export const config = { runtime: "edge" }; // Vercel edge config

export default async function handler(request) {
  const url = new URL(request.url);

  // Fetch data from edge-compatible database
  // (e.g., PlanetScale, Turso, or KV store)
  const data = await fetchDataFromEdgeDB(url.pathname);

  try {
    const stream = await renderToReadableStream(
      <App url={url.pathname} data={data} />,
      {
        bootstrapScripts: ["/client.js"],
        onError(error) {
          console.error("Edge SSR error:", error);
        },
      }
    );

    return new Response(stream, {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "public, s-maxage=60, stale-while-revalidate=600",
        "X-Edge-Location": request.cf?.colo || "unknown", // Cloudflare
      },
    });
  } catch (error) {
    // Fallback: return a minimal HTML shell for client-side rendering
    return new Response(
      `<!DOCTYPE html>
       <html><body>
         <div id="root"></div>
         <script src="/client.js"></script>
       </body></html>`,
      {
        status: 500,
        headers: { "Content-Type": "text/html" },
      }
    );
  }
}
```

```jsx
// Hybrid approach: edge for shell, origin for data-heavy components
// Vercel Next.js middleware + Edge SSR

// middleware.ts — runs at the edge for every request
import { NextResponse } from "next/server";

export function middleware(request) {
  // Geolocation-based personalisation at the edge
  const country = request.geo?.country || "US";
  const currency = COUNTRY_CURRENCIES[country] || "USD";

  // Add headers that the SSR page can read
  const response = NextResponse.next();
  response.headers.set("x-user-country", country);
  response.headers.set("x-user-currency", currency);

  return response;
}

// app/products/[slug]/page.tsx — Server Component
// Runs at edge or origin depending on configuration
import { headers } from "next/headers";

export const runtime = "edge"; // Run this page at the edge

export default async function ProductPage({ params }) {
  const headerList = headers();
  const currency = headerList.get("x-user-currency") || "USD";

  // Fetch from edge-optimized data source
  const product = await fetch(
    `https://api.mystore.com/products/${params.slug}?currency=${currency}`,
    { next: { revalidate: 60 } } // Cache for 60 seconds
  ).then((r) => r.json());

  return <ProductDetails product={product} currency={currency} />;
}
```

```jsx
// Data proximity solution: using Turso (SQLite at the edge)
import { createClient } from "@libsql/client/web"; // Web-compatible client

const db = createClient({
  url: process.env.TURSO_DATABASE_URL,    // e.g., libsql://mydb-myorg.turso.io
  authToken: process.env.TURSO_AUTH_TOKEN,
});

// This runs at the edge — Turso has replicas at edge locations
async function fetchDataFromEdgeDB(slug) {
  const result = await db.execute({
    sql: "SELECT * FROM products WHERE slug = ?",
    args: [slug],
  });
  return result.rows[0] || null;
}
```

---

### Q20. How do you architect a production SSR system with streaming, caching, monitoring, and graceful degradation?

**Answer:**

A production SSR architecture must handle high traffic, fail gracefully, serve content fast, and give you observability into performance and errors. Here is a comprehensive architecture covering all the critical pieces:

**Architecture layers:**

1. **CDN / Edge layer** — Serves cached pages, terminates TLS, handles geographic routing.
2. **SSR server cluster** — Stateless Node.js servers behind a load balancer, running `renderToPipeableStream`.
3. **Cache layer** — Redis or Memcached for fragment cache, data cache, and session store.
4. **Backend APIs / Database** — The data sources your SSR server calls.
5. **Monitoring** — Performance metrics, error tracking, and alerting.
6. **Graceful degradation** — Fallback to CSR if SSR fails or times out.

```jsx
// Production SSR server — full architecture
import express from "express";
import compression from "compression";
import { renderToPipeableStream } from "react-dom/server";
import { performance, PerformanceObserver } from "perf_hooks";
import Redis from "ioredis";
import pino from "pino";

const logger = pino({ level: "info" });
const redis = new Redis(process.env.REDIS_URL);
const app = express();

// Middleware
app.use(compression()); // gzip/brotli compression
app.use(express.static("public", { maxAge: "1y", immutable: true }));

// Health check for load balancer
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok", uptime: process.uptime() });
});

// Full-page cache middleware
async function fullPageCache(req, res, next) {
  // Skip cache for authenticated users
  if (req.cookies.session_id) return next();

  const cacheKey = `page:${req.url}`;
  const cached = await redis.get(cacheKey);

  if (cached) {
    res.setHeader("Content-Type", "text/html");
    res.setHeader("X-Cache", "HIT");
    return res.send(cached);
  }

  // Store original send to intercept the response
  res.locals.cacheKey = cacheKey;
  res.setHeader("X-Cache", "MISS");
  next();
}

app.get("*", fullPageCache, async (req, res) => {
  const startTime = performance.now();
  const requestId = crypto.randomUUID();
  let didError = false;
  const chunks = [];

  const { pipe, abort } = renderToPipeableStream(
    <RequestContext.Provider value={{ url: req.url, user: req.user, requestId }}>
      <App url={req.url} />
    </RequestContext.Provider>,
    {
      bootstrapScripts: ["/static/js/client.js"],

      onShellReady() {
        res.statusCode = didError ? 500 : 200;
        res.setHeader("Content-Type", "text/html; charset=utf-8");
        res.setHeader("X-Request-Id", requestId);

        const renderTime = performance.now() - startTime;
        res.setHeader("Server-Timing", `render;dur=${renderTime.toFixed(1)}`);

        // Set cache headers based on route
        if (!req.cookies.session_id) {
          res.setHeader(
            "Cache-Control",
            "public, s-maxage=300, stale-while-revalidate=3600"
          );
        }

        // Pipe through a transform to collect chunks for caching
        const { PassThrough } = require("stream");
        const passthrough = new PassThrough();

        passthrough.on("data", (chunk) => chunks.push(chunk));
        passthrough.on("end", () => {
          // Cache the full page if it's a public page
          if (!req.cookies.session_id && !didError) {
            const fullHtml = Buffer.concat(chunks).toString();
            redis.set(res.locals.cacheKey, fullHtml, "EX", 300);
          }
        });

        pipe(passthrough);
        passthrough.pipe(res);
      },

      onAllReady() {
        const totalTime = performance.now() - startTime;
        logger.info({
          type: "ssr_complete",
          url: req.url,
          requestId,
          renderTimeMs: totalTime.toFixed(1),
          hadErrors: didError,
        });

        // Report metrics to monitoring
        metrics.histogram("ssr.render_time", totalTime, {
          route: req.route?.path || req.url,
          status: didError ? "error" : "success",
        });
      },

      onShellError(error) {
        logger.error({
          type: "ssr_shell_error",
          url: req.url,
          requestId,
          error: error.message,
          stack: error.stack,
        });

        // Graceful degradation: fall back to client-side rendering
        res.statusCode = 500;
        res.setHeader("Content-Type", "text/html");
        res.send(getCSRFallbackHTML());
      },

      onError(error) {
        didError = true;
        logger.error({
          type: "ssr_render_error",
          url: req.url,
          requestId,
          error: error.message,
        });
      },
    }
  );

  // Hard timeout — abort SSR and fall back to CSR
  const timeout = setTimeout(() => {
    logger.warn({ type: "ssr_timeout", url: req.url, requestId });
    abort();
  }, 8000);

  res.on("close", () => clearTimeout(timeout));
});

// CSR fallback HTML — used when SSR fails
function getCSRFallbackHTML() {
  return `
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>MyApp</title>
        <link rel="stylesheet" href="/static/css/main.css" />
      </head>
      <body>
        <div id="root">
          <div class="loading-screen">
            <div class="spinner"></div>
            <p>Loading...</p>
          </div>
        </div>
        <script src="/static/js/client.js"></script>
      </body>
    </html>
  `;
}

// Start server with cluster for multi-core utilisation
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`SSR server running on port ${PORT}`);
});
```

```jsx
// Client entry — resilient hydration with error handling
import { hydrateRoot } from "react-dom/client";
import App from "./App";

function hydrate() {
  try {
    const root = hydrateRoot(
      document.getElementById("root"),
      <App url={window.location.pathname} />,
      {
        onRecoverableError(error, errorInfo) {
          // Log hydration mismatches and recoverable errors
          console.warn("Recoverable hydration error:", error);
          reportToMonitoring("hydration_error", {
            error: error.message,
            componentStack: errorInfo?.componentStack,
            url: window.location.href,
          });
        },
      }
    );
  } catch (error) {
    // Hydration completely failed — fall back to full client render
    console.error("Hydration failed, falling back to CSR:", error);

    const { createRoot } = require("react-dom/client");
    const container = document.getElementById("root");
    container.innerHTML = ""; // Clear server HTML
    const root = createRoot(container);
    root.render(<App url={window.location.pathname} />);
  }
}

// Start hydration
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", hydrate);
} else {
  hydrate();
}
```

```jsx
// Monitoring dashboard metrics to track SSR health
// This would be reported to DataDog, Grafana, or similar

const SSR_METRICS = {
  // Latency
  "ssr.shell_ready_time":    "Time until shell HTML is ready to stream",
  "ssr.total_render_time":   "Time until all Suspense boundaries resolve",
  "ssr.ttfb":                "Time to first byte (measured at CDN)",

  // Throughput
  "ssr.requests_per_second": "SSR requests handled per second per instance",
  "ssr.cache_hit_rate":      "Percentage of requests served from cache",

  // Errors
  "ssr.shell_errors":        "Number of shell render failures (critical)",
  "ssr.stream_errors":       "Errors during Suspense boundary streaming",
  "ssr.hydration_mismatches":"Client-reported hydration mismatch count",
  "ssr.timeout_count":       "Requests that hit the SSR timeout",

  // Resources
  "ssr.memory_usage_mb":     "Memory per Node.js process",
  "ssr.event_loop_lag_ms":   "Event loop lag (indicates CPU saturation)",
  "ssr.concurrent_renders":  "Number of simultaneous SSR renders in flight",
};

// Alert thresholds
const ALERTS = {
  "ssr.shell_ready_time > 2000ms":  "CRITICAL — shell taking too long",
  "ssr.cache_hit_rate < 0.5":       "WARNING  — cache hit rate dropped",
  "ssr.shell_errors > 10/min":      "CRITICAL — high shell failure rate",
  "ssr.event_loop_lag_ms > 100":    "WARNING  — CPU saturation, scale up",
  "ssr.concurrent_renders > 50":    "WARNING  — too many in-flight renders",
};
```

The key principles of production SSR architecture: **stream everything**, **cache aggressively**, **fail gracefully** (always have a CSR fallback), **monitor everything** (TTFB, render times, error rates, cache hit rates), and **keep the shell fast** (no data dependencies in the shell so it streams instantly).

---

*End of SSR & Hydration interview questions.*
