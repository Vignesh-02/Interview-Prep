# 2. React Server Components vs Client Components

## Topic Introduction

**React Server Components (RSC)** are the foundational paradigm shift in Next.js 15/16's App Router. Unlike traditional React where ALL components ship JavaScript to the browser, RSC introduces a **split architecture**:

```
┌──────────────────────────────────────────────────┐
│                  Server Components                │
│  ┌────────────────────────────────────────────┐  │
│  │ • Render on the server ONLY                │  │
│  │ • Zero client-side JavaScript              │  │
│  │ • Can access databases, file system, etc.  │  │
│  │ • Cannot use hooks (useState, useEffect)   │  │
│  │ • Cannot use browser APIs                  │  │
│  │ • Can import Client Components             │  │
│  │ • Default in app/ directory                │  │
│  └────────────────────────────────────────────┘  │
│                                                    │
│                  Client Components                 │
│  ┌────────────────────────────────────────────┐  │
│  │ • "use client" directive at top of file    │  │
│  │ • Ship JS to browser + hydrate             │  │
│  │ • Can use hooks, event handlers            │  │
│  │ • Can use browser APIs (localStorage etc.) │  │
│  │ • Pre-render on server, hydrate on client  │  │
│  │ • Cannot import Server Components          │  │
│  │   (but can receive them as children)       │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

The key insight is that **Server Components are not SSR**. SSR renders components to HTML on the server, then hydrates them with JavaScript on the client. Server Components render on the server and **never hydrate** — their JavaScript never ships to the client. They produce a special format called **RSC Payload** that React uses to stitch the server-rendered tree with client-rendered parts.

This distinction has massive production implications: reduced bundle sizes, faster TTI, and the ability to access backend resources directly without API endpoints.

---

## Q1. (Beginner) What is a React Server Component, and how is it different from a regular React component?

**Scenario**: A junior dev asks why they don't need `useEffect` to fetch data in the App Router.

**Answer**:

A **React Server Component (RSC)** is a component that runs exclusively on the server. It can be `async`, directly access databases, read files, and call APIs — all without sending any JavaScript to the browser.

```tsx
// Server Component (default in app/ directory)
// app/users/page.tsx — NO "use client" directive
import { db } from '@/lib/database';

export default async function UsersPage() {
  // Direct database query — no API endpoint needed!
  const users = await db.user.findMany({
    select: { id: true, name: true, email: true },
  });

  return (
    <div>
      <h1>Users ({users.length})</h1>
      <ul>
        {users.map(user => (
          <li key={user.id}>
            {user.name} — {user.email}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

A traditional React component (Client Component) requires `"use client"` and is what you're familiar with from React 18:

```tsx
// Client Component — marked explicitly
'use client';

import { useState, useEffect } from 'react';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Needs an API endpoint to fetch data
  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

| Aspect | Server Component | Client Component |
|--------|-----------------|------------------|
| Runs on | Server only | Server (pre-render) + Client (hydrate) |
| JS sent to browser | None | Yes — all component code |
| Can use hooks | No | Yes |
| Can use `async/await` | Yes | No (use `use()` in React 19) |
| Can access DB/filesystem | Yes | No |
| Can use event handlers | No | Yes |

---

## Q2. (Beginner) How do you decide whether a component should be a Server Component or Client Component?

**Answer**:

Use this decision tree:

```
Does it need interactivity (onClick, onChange, etc.)?
  └─ YES → Client Component

Does it use React hooks (useState, useEffect, useRef)?
  └─ YES → Client Component

Does it use browser APIs (localStorage, window, navigator)?
  └─ YES → Client Component

Does it only display data / layout / static content?
  └─ YES → Server Component ✅

Does it fetch data from a database or API?
  └─ YES → Server Component ✅ (no need for API layer)
```

**Real-world example — E-commerce product page**:

```tsx
// app/product/[id]/page.tsx — Server Component (data fetching + layout)
import { AddToCartButton } from './_components/AddToCartButton';
import { ImageGallery } from './_components/ImageGallery';
import { ReviewsList } from './_components/ReviewsList';

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = await getProduct(id);

  return (
    <div>
      {/* Server Component — just displays data */}
      <h1>{product.name}</h1>
      <p className="text-2xl font-bold">${product.price}</p>
      <p>{product.description}</p>

      {/* Client Component — needs interactivity (zoom, swipe) */}
      <ImageGallery images={product.images} />

      {/* Client Component — needs onClick + state */}
      <AddToCartButton productId={product.id} price={product.price} />

      {/* Server Component — just fetches and displays reviews */}
      <ReviewsList productId={product.id} />
    </div>
  );
}
```

**Rule of thumb**: Start with Server Components. Only add `"use client"` when you hit a wall (need hooks, interactivity, or browser APIs). Push the `"use client"` boundary as far down the tree as possible.

---

## Q3. (Beginner) What can you pass as props from a Server Component to a Client Component?

**Scenario**: You try to pass a function from a Server Component to a Client Component and get an error.

**Answer**:

Only **serializable** data can cross the Server → Client boundary (because the data is sent as JSON over the network).

```tsx
// ✅ ALLOWED — Serializable data
<ClientComponent
  name="Vignesh"                      // string
  count={42}                          // number
  isActive={true}                     // boolean
  tags={['react', 'nextjs']}          // array of primitives
  user={{ id: 1, name: 'Vignesh' }}   // plain object
  createdAt={new Date().toISOString()} // string (NOT Date object)
/>

// ❌ NOT ALLOWED — Non-serializable
<ClientComponent
  onClick={() => console.log('click')} // Function!
  dbConnection={pool}                   // Class instance!
  createdAt={new Date()}                // Date object!
  nodeStream={readableStream}           // Stream!
  regex={/pattern/}                     // RegExp!
/>
```

**Workarounds**:

```tsx
// Pass Date as string, parse on client
// Server Component:
<ClientComponent date={product.createdAt.toISOString()} />

// Client Component:
function ClientComponent({ date }: { date: string }) {
  const parsedDate = new Date(date);
  return <time dateTime={date}>{parsedDate.toLocaleDateString()}</time>;
}

// For functions — use Server Actions instead
// Server Component:
import { addToCart } from './actions';

<AddToCartForm action={addToCart} productId={product.id} />

// actions.ts
'use server';
export async function addToCart(productId: string) {
  await db.cart.add({ productId });
}
```

**Special exception**: React Server Components CAN pass JSX/React elements as props (they're serializable in the RSC protocol):

```tsx
// Server Component
<ClientTabs
  tab1={<ServerRenderedContent />}  // ✅ Works! RSC renders this on server
  tab2={<AnotherServerComponent />} // ✅ Also works
/>
```

---

## Q4. (Beginner) What is the `"use client"` directive, and where exactly should you place it?

**Answer**:

`"use client"` is a module-level directive that marks a file as a **Client Component boundary**. It must be the first expression in the file (before any imports).

```tsx
// ✅ Correct placement
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

export default function Counter() {
  const [count, setCount] = useState(0);
  return <Button onClick={() => setCount(c => c + 1)}>Count: {count}</Button>;
}
```

```tsx
// ❌ Wrong — directive must come before imports
import { useState } from 'react';
'use client'; // Too late! This won't work correctly

export default function Counter() { /* ... */ }
```

**Key misconception**: `"use client"` does NOT mean the component only renders on the client. Client Components are **pre-rendered on the server** (like SSR) and then **hydrated** on the client. The directive means: "this component and its imports need to be included in the client bundle."

```
"use client" marks the BOUNDARY:
  
  Server boundary          Client boundary
  ┌─────────────┐          ┌──────────────────┐
  │ page.tsx     │──import──│ Counter.tsx       │ ← "use client"
  │ (Server)     │          │ Button.tsx        │ ← auto client (imported by Counter)
  │ layout.tsx   │          │ AnimatedDiv.tsx   │ ← auto client (imported by Counter)
  │ (Server)     │          └──────────────────┘
  └─────────────┘
```

**Every file imported by a `"use client"` file is automatically a Client Component** — you don't need to add `"use client"` to each one. This is why the directive should be placed as deep in the tree as possible.

---

## Q5. (Beginner) Can a Client Component render a Server Component? How?

**Answer**:

A Client Component **cannot import** a Server Component, but it **can receive** one as a prop (typically `children`).

```tsx
// ❌ WRONG — Client Component importing Server Component
'use client';
import ServerComponent from './ServerComponent'; // Build error!

export function ClientWrapper() {
  return <ServerComponent />;
}
```

```tsx
// ✅ CORRECT — Server Component passed as children
// ClientWrapper.tsx
'use client';
import { useState } from 'react';

export function ClientWrapper({ children }: { children: React.ReactNode }) {
  const [isVisible, setIsVisible] = useState(true);
  return (
    <div>
      <button onClick={() => setIsVisible(!isVisible)}>Toggle</button>
      {isVisible && children}
    </div>
  );
}

// page.tsx (Server Component)
import { ClientWrapper } from './ClientWrapper';
import { ExpensiveServerData } from './ExpensiveServerData';

export default async function Page() {
  return (
    <ClientWrapper>
      {/* This is rendered on the server, then passed as serialized JSX */}
      <ExpensiveServerData />
    </ClientWrapper>
  );
}

// ExpensiveServerData.tsx (Server Component)
export async function ExpensiveServerData() {
  const data = await db.query('SELECT * FROM analytics');
  return <div>{/* render data — zero JS shipped */}</div>;
}
```

**Why this works**: The Server Component is rendered on the server first. Its output (RSC payload) is then passed as a prop to the Client Component. The Client Component doesn't need to know how to render it — it just receives pre-rendered content.

**This pattern is fundamental** — it's how you keep interactivity (Client) while minimizing the JS bundle (Server).

---

## Q6. (Intermediate) Explain the RSC Payload format. What does Next.js send over the wire for Server Components?

**Scenario**: You're debugging network requests and see a strange format in the response — not HTML, not JSON.

**Answer**:

The **RSC Payload** is a special streaming format that React uses to transmit the Server Component tree to the client. It's neither HTML nor JSON — it's a line-delimited protocol.

```
// When you navigate to /dashboard, the response looks like:
0:["$","div",null,{"className":"flex","children":[["$","aside",null,{"children":"Sidebar content"}],["$","$L1",null,{"data":{"revenue":50000}}]]}]
1:I["client-chunk-abc123.js",["Counter"],"default"]
```

**Breaking this down**:

```
Line 0: A serialized React tree
  "$" = React element
  "div" = element type
  null = key
  {...} = props + children

  "$L1" = Reference to a CLIENT component (lazy loaded)
  
Line 1: Client module reference
  "I" = Import instruction
  "client-chunk-abc123.js" = The JS chunk to load
  ["Counter"] = The export to use
```

**The full data flow**:

```
Server renders:
  <DashboardLayout>           → Serialized as HTML + RSC payload
    <Sidebar />               → Server Component → inline in payload
    <Counter data={...} />    → Client Component → reference in payload
  </DashboardLayout>

Client receives:
  1. HTML stream (for immediate paint)
  2. RSC Payload stream (for React reconciliation)
  3. Client JS chunks (for hydration of Client Components only)

Client reconciles:
  - Server Components: already rendered, no JS needed
  - Client Components: hydrate with received JS + props from RSC payload
```

**Why this matters for production**:
- Server Components add ZERO bytes to the client bundle
- The RSC payload is much smaller than full HTML + full JS
- Streaming means content appears progressively
- Navigations only need the RSC payload (not full HTML) because the shell is already loaded

```tsx
// To inspect RSC payload in dev:
// Visit your page and look for requests with `?_rsc=` query parameter
// Or in the Network tab, look for requests with content-type: text/x-component
```

---

## Q7. (Intermediate) How does data fetching work differently in Server Components? Explain `fetch`, `cache()`, and request deduplication.

**Answer**:

In Server Components, data fetching is **direct** — no need for `useEffect`, `useSWR`, or API routes.

**1. Direct `fetch` with caching:**

```tsx
// app/products/page.tsx
export default async function ProductsPage() {
  // Next.js extends fetch with caching options
  const products = await fetch('https://api.example.com/products', {
    cache: 'force-cache',         // Cache indefinitely (default in Next 14, NOT in 15)
    // cache: 'no-store',         // Never cache — always fresh
    // next: { revalidate: 3600 }, // ISR: revalidate every hour
    // next: { tags: ['products'] }, // Tag-based revalidation
  }).then(res => res.json());

  return <ProductList products={products} />;
}
```

**Next.js 15 change**: `fetch` requests are **NOT cached by default** (changed from Next.js 14). You must opt-in:

```tsx
// Next.js 14: cached by default
fetch(url);              // ← Cached
fetch(url, { cache: 'no-store' }); // ← Opt out

// Next.js 15: NOT cached by default
fetch(url);              // ← NOT cached
fetch(url, { cache: 'force-cache' }); // ← Opt in
fetch(url, { next: { revalidate: 60 } }); // ← Opt in with ISR
```

**2. `cache()` for non-fetch data sources:**

```tsx
import { cache } from 'react';
import { db } from '@/lib/database';

// Wrapping in cache() deduplicates across the same request
export const getUser = cache(async (userId: string) => {
  console.log('Fetching user:', userId); // Only logs ONCE per request
  return await db.user.findUnique({ where: { id: userId } });
});

// Even if called in multiple components during the same render:
// layout.tsx
const user = await getUser('123'); // Executes DB query

// page.tsx
const user = await getUser('123'); // Returns memoized result (no DB hit)
```

**3. Automatic fetch deduplication:**

```tsx
// These two fetches in different components are automatically deduplicated
// Component A
const data = await fetch('https://api.example.com/config');

// Component B (same request during same render)
const data = await fetch('https://api.example.com/config');
// ↑ Only ONE network request is made. The second call gets the memoized result.
```

**Deduplication rules**:
- Same URL + same options = deduplicated
- Only works within a single server render pass
- Only works for GET requests
- Does NOT work across different requests from different users
- `POST` requests are NEVER deduplicated

---

## Q8. (Intermediate) What is the `server-only` and `client-only` packages? When and why should you use them?

**Answer**:

These packages are **build-time guards** that prevent code from being used in the wrong environment.

```bash
npm install server-only client-only
```

```tsx
// lib/db.ts — Should NEVER run on the client
import 'server-only';    // ← Build error if imported in Client Component
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL, // Contains credentials!
});

export async function query(sql: string) {
  return pool.query(sql);
}
```

```tsx
// lib/analytics-client.ts — Only makes sense in the browser
import 'client-only';    // ← Build error if imported in Server Component

export function trackEvent(name: string, data: object) {
  window.gtag('event', name, data); // Uses window — browser only
}
```

**Without these guards, bad things happen**:

```tsx
// ❌ Without server-only, this could accidentally be imported in a Client Component:
// lib/email.ts
import { SES } from '@aws-sdk/client-ses';

const ses = new SES({ region: 'us-east-1' });

export async function sendEmail(to: string, body: string) {
  // AWS credentials would be bundled into the client JS! 💀
  await ses.sendEmail({ /* ... */ });
}

// ✅ With server-only:
import 'server-only';
import { SES } from '@aws-sdk/client-ses';
// Now if any Client Component imports this, the build fails with a clear error.
```

**Production best practice**: Add `import 'server-only'` to:
- Database query modules
- Email/notification services
- Anything using secrets or credentials
- Internal API clients with auth tokens
- File system operations

---

## Q9. (Intermediate) How do you share data between Server Components without prop drilling?

**Scenario**: Your app's layout fetches user data. Multiple nested Server Components need this data. You don't want to pass it through 5 levels of props.

**Answer**:

**Method 1: `cache()` function (recommended)**

```tsx
// lib/user.ts
import { cache } from 'react';
import { cookies } from 'next/headers';
import { db } from './database';

// cache() memoizes within a SINGLE request (not across requests)
export const getCurrentUser = cache(async () => {
  const cookieStore = await cookies();
  const token = cookieStore.get('session')?.value;
  if (!token) return null;

  const user = await db.user.findByToken(token);
  return user;
});
```

```tsx
// app/layout.tsx
import { getCurrentUser } from '@/lib/user';

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser(); // First call — hits DB
  return (
    <html>
      <body>
        <Header user={user} />
        {children}
      </body>
    </html>
  );
}

// app/dashboard/page.tsx
import { getCurrentUser } from '@/lib/user';

export default async function DashboardPage() {
  const user = await getCurrentUser(); // Second call — returns memoized (no DB hit)
  return <h1>Welcome, {user?.name}</h1>;
}

// app/dashboard/sidebar.tsx
import { getCurrentUser } from '@/lib/user';

export default async function Sidebar() {
  const user = await getCurrentUser(); // Third call — still memoized
  return <div>Plan: {user?.plan}</div>;
}
```

**Method 2: Fetch deduplication (for external APIs)**

```tsx
// If multiple Server Components call the same fetch, it's automatically deduplicated
async function getConfig() {
  const res = await fetch('https://api.example.com/config', {
    next: { tags: ['config'] },
  });
  return res.json();
}

// Layout and Page both call getConfig() — only ONE HTTP request is made
```

**Why NOT `useContext`**: Context requires `"use client"` and would make everything below it a Client Component. For server-side data sharing, `cache()` is the correct pattern.

---

## Q10. (Intermediate) Explain the "donut pattern" — how do you wrap a Server Component with a Client Component that provides context?

**Answer**:

The "donut pattern" (or "children slot pattern") lets you use Client-side context providers without making the entire subtree client-side:

```
┌─────── Client (Provider) ──────┐
│   ┌────── Server ──────────┐   │
│   │  Server Component      │   │  ← The "donut hole" — stays on server
│   │  (passed as children)  │   │
│   └────────────────────────┘   │
└────────────────────────────────┘
```

```tsx
// providers/ThemeProvider.tsx
'use client';

import { createContext, useContext, useState } from 'react';

const ThemeContext = createContext<{ theme: string; toggleTheme: () => void } | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState('light');

  return (
    <ThemeContext.Provider value={{
      theme,
      toggleTheme: () => setTheme(t => t === 'light' ? 'dark' : 'light'),
    }}>
      <div data-theme={theme}>{children}</div>
    </ThemeContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};
```

```tsx
// app/layout.tsx — Server Component
import { ThemeProvider } from '@/providers/ThemeProvider';
import { Header } from './_components/Header'; // Server Component

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const config = await getAppConfig(); // Server-side data fetch

  return (
    <html lang="en">
      <body>
        <ThemeProvider>           {/* Client boundary starts */}
          <Header config={config} /> {/* Server Component — rendered on server, */}
          {children}                  {/* passed as pre-rendered children */}
        </ThemeProvider>            {/* Client boundary ends */}
      </body>
    </html>
  );
}
```

**How it works**: `children` is evaluated (rendered) in the Server Component context first. The resulting RSC payload is passed to the Client Component. The Client Component (ThemeProvider) wraps it but doesn't need to re-render the children — they're already rendered.

**This is the recommended pattern for**:
- Theme providers
- Auth providers
- i18n providers
- Any context that wraps the app

---

## Q11. (Intermediate) How do you handle third-party libraries that use `useEffect` or browser APIs in the App Router?

**Scenario**: You want to use a chart library (e.g., Chart.js, Recharts) that requires `window` and DOM access.

**Answer**:

Third-party libraries that rely on browser APIs or hooks must be wrapped in Client Components. There are several strategies:

**Strategy 1: Create a Client Component wrapper**

```tsx
// components/charts/RevenueChart.tsx
'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface RevenueChartProps {
  data: Array<{ month: string; revenue: number }>;
}

export function RevenueChart({ data }: RevenueChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

```tsx
// app/dashboard/page.tsx — Server Component
import { RevenueChart } from '@/components/charts/RevenueChart';

export default async function DashboardPage() {
  const data = await db.revenue.getMonthly(); // Server-side query

  return (
    <div>
      <h1>Dashboard</h1>
      <RevenueChart data={data} /> {/* Client Component — receives serializable data */}
    </div>
  );
}
```

**Strategy 2: Dynamic import with `ssr: false` for libraries that crash on server**

```tsx
// Some libraries access `window` at import time (not just in useEffect)
// app/dashboard/page.tsx
import dynamic from 'next/dynamic';

const MapComponent = dynamic(
  () => import('@/components/Map'),
  {
    ssr: false,                     // Don't render on server AT ALL
    loading: () => <div className="h-[400px] bg-gray-100 animate-pulse" />,
  }
);

export default async function LocationPage() {
  const locations = await getLocations();
  return <MapComponent locations={locations} />;
}
```

**Strategy 3: Re-export with `"use client"`**

```tsx
// lib/motion.ts — Re-export a client-only library
'use client';

export { motion, AnimatePresence } from 'framer-motion';
// Now any Server Component file can import from this file,
// and the compiler knows it's a Client Component boundary
```

---

## Q12. (Intermediate) What are the performance implications of the `"use client"` boundary? How does it affect bundle size?

**Answer**:

Every `"use client"` file creates a **split point** in the module graph. All code reachable from that file (imports, dependencies) is included in the client bundle.

```tsx
// ❌ BAD: "use client" at a high level — everything below is client
// components/Dashboard.tsx
'use client'; // This pulls in ALL imports into the client bundle

import { useState } from 'react';
import { DataTable } from './DataTable';        // Now client
import { Chart } from './Chart';                 // Now client
import { HeavyAnalytics } from './Analytics';    // Now client (1MB library!)
import { formatDate, formatCurrency } from 'date-fns'; // Now client

export function Dashboard() { /* ... */ }
```

```tsx
// ✅ GOOD: Push "use client" to the leaves
// components/Dashboard.tsx — Server Component (no directive)
import { DataDisplay } from './DataDisplay';     // Server Component
import { InteractiveChart } from './Chart';      // Client Component (has "use client")
import { SortButton } from './SortButton';       // Client Component (has "use client")

export async function Dashboard() {
  const data = await fetchDashboardData();
  return (
    <div>
      <DataDisplay data={data} />        {/* Zero JS */}
      <InteractiveChart data={data} />    {/* Only chart JS shipped */}
      <SortButton />                      {/* Only tiny button JS shipped */}
    </div>
  );
}
```

**Measuring the impact**:

```bash
# Build with analysis
ANALYZE=true next build

# In next.config.js:
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({});
```

**The "1000 component" test**:
- 1000 Server Components = ~0 KB added to client bundle
- 1000 Client Components = potentially MBs of JS

**Rule**: If a component doesn't need interactivity, it should be a Server Component. Even if it's imported by a Client Component, restructure using the children pattern to keep it on the server.

---

## Q13. (Advanced) Explain the serialization boundary between Server and Client Components. What are edge cases that can cause runtime errors?

**Answer**:

The Server-Client boundary serializes data using a protocol similar to JSON but with extensions for React elements, Promises, and references. Understanding edge cases is critical for production stability.

**Edge Case 1: Passing non-serializable props silently fails**

```tsx
// Server Component
export default function Page() {
  const handler = () => console.log('click');

  // ❌ This will throw:
  // "Functions cannot be passed directly to Client Components unless you
  //  explicitly expose it by marking it with 'use server'"
  return <ClientButton onClick={handler} />;

  // ✅ Fix with Server Action:
  async function handleClick() {
    'use server';
    console.log('Clicked — runs on server');
  }
  return <ClientButton onClick={handleClick} />;
}
```

**Edge Case 2: Class instances**

```tsx
// ❌ Class instances lose their prototype
class User {
  constructor(public name: string) {}
  greet() { return `Hi, ${this.name}`; }
}

// Server Component
const user = new User('Vignesh');
return <ClientProfile user={user} />;
// Client receives: { name: 'Vignesh' } — greet() method is GONE

// ✅ Fix: serialize to plain object
return <ClientProfile user={{ name: user.name, greeting: user.greet() }} />;
```

**Edge Case 3: Date objects**

```tsx
// ❌ Date objects are not directly serializable
const createdAt = new Date();
return <ClientCard date={createdAt} />;
// Error: Only plain objects, and a few built-ins, can be passed to Client Components

// ✅ Fix: convert to ISO string
return <ClientCard date={createdAt.toISOString()} />;
```

**Edge Case 4: Circular references**

```tsx
// ❌ Circular objects cannot be serialized
const a: any = {};
const b: any = { a };
a.b = b;
return <ClientComponent data={a} />;
// Error: Circular reference detected

// ✅ Fix: break the cycle before passing
```

**Edge Case 5: Large data**

```tsx
// ❌ Passing megabytes of data bloats the RSC payload
const allProducts = await db.product.findMany(); // 50,000 products
return <ClientTable data={allProducts} />;
// RSC payload = several MB → slow first paint

// ✅ Fix: paginate on server, only send what's needed
const products = await db.product.findMany({ take: 20, skip: page * 20 });
return <ClientTable data={products} />;
```

**Edge Case 6: Conditional `"use client"` doesn't work**

```tsx
// ❌ You can't conditionally opt into client rendering
if (isInteractive) {
  'use client'; // This is a NO-OP — must be at module top level
}
```

---

## Q14. (Advanced) How does Selective Hydration work with Server Components and Suspense?

**Answer**:

**Selective Hydration** (React 18+) allows React to prioritize hydrating components that the user is interacting with, rather than hydrating everything top-to-bottom.

```tsx
// app/page.tsx
import { Suspense } from 'react';
import { Header } from './Header';        // Client Component
import { HeroSection } from './Hero';      // Server Component
import { ProductGrid } from './Products';  // Client Component (interactive)
import { Reviews } from './Reviews';       // Client Component (interactive)
import { Footer } from './Footer';         // Client Component

export default async function Page() {
  return (
    <>
      <Header />

      <HeroSection /> {/* Server Component — no hydration needed */}

      <Suspense fallback={<ProductGridSkeleton />}>
        <ProductGrid />   {/* Hydrates independently */}
      </Suspense>

      <Suspense fallback={<ReviewsSkeleton />}>
        <Reviews />        {/* Hydrates independently */}
      </Suspense>

      <Footer />
    </>
  );
}
```

**Hydration flow**:

```
1. Server sends HTML stream
   └─ User sees fully rendered page (but not interactive yet)

2. React starts hydrating Client Components
   └─ Header → ProductGrid → Reviews → Footer (normal order)

3. User clicks on Reviews section BEFORE it's hydrated
   └─ React DEPRIORITIZES ProductGrid hydration
   └─ React PRIORITIZES Reviews hydration
   └─ Reviews becomes interactive first

4. React continues hydrating remaining components
```

**This works because of Suspense boundaries**: Each `<Suspense>` creates an independent hydration unit. Without Suspense, the entire page is one hydration unit (all-or-nothing).

**Production implications**:
- Wrap each major interactive section in `<Suspense>`
- Critical interactive elements (search bar, CTA buttons) should hydrate first
- Server Components between Client Components create natural break points

---

## Q15. (Advanced) Explain the `taintObjectReference` and `taintUniqueValue` APIs in React 19 / Next.js 15. How do they prevent data leaks?

**Answer**:

These experimental APIs prevent sensitive data from accidentally crossing the Server → Client boundary.

```tsx
// lib/user.ts
import { experimental_taintObjectReference as taintObjectReference } from 'react';
import { experimental_taintUniqueValue as taintUniqueValue } from 'react';

export async function getUser(id: string) {
  const user = await db.user.findUnique({
    where: { id },
    select: {
      id: true,
      name: true,
      email: true,
      ssn: true,           // Sensitive!
      creditCard: true,    // Sensitive!
    },
  });

  // Taint the entire object — passing it to a Client Component will throw
  taintObjectReference(
    'Do not pass user objects to Client Components. Use a DTO instead.',
    user
  );

  // Taint specific values
  taintUniqueValue(
    'Do not pass SSN to Client Components',
    user,
    user.ssn
  );

  return user;
}
```

```tsx
// app/profile/page.tsx
import { getUser } from '@/lib/user';

export default async function ProfilePage() {
  const user = await getUser('123');

  // ✅ Server Component can use the full object
  return (
    <div>
      <h1>{user.name}</h1>

      {/* ❌ This would throw at build/runtime: */}
      {/* <ClientComponent user={user} /> */}
      {/* Error: "Do not pass user objects to Client Components..." */}

      {/* ✅ Create a DTO (Data Transfer Object) with only safe fields */}
      <ClientComponent user={{ id: user.id, name: user.name }} />
    </div>
  );
}
```

**Why this matters**: In large teams, it's easy for a developer to accidentally pass a full database record (with sensitive fields) to a Client Component. Tainting provides a **defense-in-depth** layer that catches these mistakes at runtime.

---

## Q16. (Advanced) How would you implement a real-time collaborative feature (like Google Docs cursors) using Server Components and Client Components together?

**Scenario**: You need to show live cursors of other users editing the same document.

**Answer**:

```tsx
// app/doc/[id]/page.tsx — Server Component
import { getDocument } from '@/lib/documents';
import { CollaborativeEditor } from './_components/CollaborativeEditor';
import { auth } from '@/lib/auth';

export default async function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [doc, session] = await Promise.all([
    getDocument(id),
    auth(),
  ]);

  if (!doc) notFound();

  // Server Component renders the initial document state
  // Client Component handles real-time collaboration
  return (
    <div>
      <header className="border-b p-4">
        <h1>{doc.title}</h1>
        <p className="text-sm text-gray-500">Last saved: {doc.updatedAt.toISOString()}</p>
      </header>

      <CollaborativeEditor
        documentId={id}
        initialContent={doc.content}
        userId={session.user.id}
        userName={session.user.name}
      />
    </div>
  );
}
```

```tsx
// _components/CollaborativeEditor.tsx
'use client';

import { useEffect, useState, useCallback } from 'react';

interface Cursor {
  userId: string;
  userName: string;
  position: { x: number; y: number };
  color: string;
}

export function CollaborativeEditor({
  documentId,
  initialContent,
  userId,
  userName,
}: {
  documentId: string;
  initialContent: string;
  userId: string;
  userName: string;
}) {
  const [content, setContent] = useState(initialContent);
  const [cursors, setCursors] = useState<Map<string, Cursor>>(new Map());
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/doc/${documentId}`
    );

    socket.onopen = () => {
      socket.send(JSON.stringify({
        type: 'join',
        userId,
        userName,
      }));
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case 'cursor_move':
          setCursors(prev => {
            const next = new Map(prev);
            next.set(msg.userId, {
              userId: msg.userId,
              userName: msg.userName,
              position: msg.position,
              color: msg.color,
            });
            return next;
          });
          break;

        case 'content_update':
          if (msg.userId !== userId) {
            setContent(msg.content);
          }
          break;

        case 'user_left':
          setCursors(prev => {
            const next = new Map(prev);
            next.delete(msg.userId);
            return next;
          });
          break;
      }
    };

    setWs(socket);
    return () => socket.close();
  }, [documentId, userId, userName]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    ws?.send(JSON.stringify({
      type: 'cursor_move',
      position: { x: e.clientX, y: e.clientY },
    }));
  }, [ws]);

  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    ws?.send(JSON.stringify({
      type: 'content_update',
      content: newContent,
    }));
  }, [ws]);

  return (
    <div className="relative" onMouseMove={handleMouseMove}>
      {/* Other users' cursors */}
      {Array.from(cursors.values()).map(cursor => (
        <div
          key={cursor.userId}
          className="absolute pointer-events-none z-50 transition-all duration-100"
          style={{ left: cursor.position.x, top: cursor.position.y }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill={cursor.color}>
            <path d="M0 0L16 6L6 16Z" />
          </svg>
          <span className="text-xs px-1 rounded" style={{ backgroundColor: cursor.color }}>
            {cursor.userName}
          </span>
        </div>
      ))}

      {/* Editor */}
      <textarea
        value={content}
        onChange={(e) => handleContentChange(e.target.value)}
        className="w-full min-h-[600px] p-4 font-mono"
      />
    </div>
  );
}
```

**Architecture insight**: The Server Component loads the initial document state (fast, cacheable, SEO-friendly). The Client Component handles real-time collaboration. This separation means:
- First paint is instant (server-rendered content)
- WebSocket connection is established after hydration
- If WebSocket fails, the user still sees the document

---

## Q17. (Advanced) What is `React.cache()` vs `unstable_cache()` vs `fetch` cache in Next.js 15? Compare all caching mechanisms.

**Answer**:

| Cache Type | Scope | Persists across requests | Storage | Use Case |
|-----------|-------|------------------------|---------|----------|
| `React.cache()` | Single request | No | In-memory (per-render) | Deduplicate within one render |
| `fetch` cache | Across requests | Yes | Data Cache (disk) | HTTP responses |
| `unstable_cache()` | Across requests | Yes | Data Cache (disk) | Non-fetch data (DB queries) |
| Router Cache | Client-side | Yes (30s dynamic, 5min static) | Browser memory | RSC payloads |
| Full Route Cache | Build time | Yes | Server disk | Pre-rendered HTML + RSC |

```tsx
// 1. React.cache() — Request-level deduplication
import { cache } from 'react';

export const getUser = cache(async (id: string) => {
  // Called 5 times in different Server Components during one render
  // → Only executes ONCE per request
  return db.user.findUnique({ where: { id } });
});

// 2. fetch with cache — Cross-request caching
const data = await fetch('https://api.example.com/data', {
  next: {
    revalidate: 3600,         // Revalidate every hour
    tags: ['homepage-data'],  // Tag for on-demand revalidation
  },
});

// 3. unstable_cache() — Cross-request caching for non-fetch
import { unstable_cache } from 'next/cache';

const getCachedUser = unstable_cache(
  async (id: string) => {
    return db.user.findUnique({ where: { id } });
  },
  ['user'],               // Cache key prefix
  {
    revalidate: 3600,     // Seconds
    tags: ['user'],       // For on-demand revalidation
  }
);
```

**Revalidation**:

```tsx
// On-demand revalidation (e.g., after admin updates content)
// app/api/revalidate/route.ts
import { revalidateTag, revalidatePath } from 'next/cache';

export async function POST(request: Request) {
  const { tag, path } = await request.json();

  if (tag) revalidateTag(tag);     // Revalidate all fetches with this tag
  if (path) revalidatePath(path);  // Revalidate a specific route

  return Response.json({ revalidated: true });
}
```

---

## Q18. (Advanced) How do Streaming and Progressive Rendering work with RSC? Trace the bytes from server to painted pixels.

**Answer**:

```
Server (Node.js):
┌──────────────────────────────────────────────────┐
│ 1. Start rendering root layout                    │
│ 2. Hit first <Suspense> → send shell HTML         │─── HTML chunk 1 → Browser
│ 3. Continue rendering synchronous components      │
│ 4. Hit async component → start data fetch         │
│ 5. Send more completed HTML                       │─── HTML chunk 2 → Browser
│ 6. Async component resolves → send its HTML       │─── HTML chunk 3 → Browser
│ 7. Send closing tags + inline <script> for hydrate│─── Final chunk → Browser
└──────────────────────────────────────────────────┘

Browser:
┌──────────────────────────────────────────────────┐
│ Chunk 1 arrives:                                  │
│ ├─ Parse HTML, paint layout + loading skeleton    │ ← FCP
│ ├─ Start downloading JS bundles                   │
│                                                    │
│ Chunk 2 arrives:                                  │
│ ├─ Paint more server-rendered content              │
│                                                    │
│ Chunk 3 arrives:                                  │
│ ├─ Replace loading skeleton with real content      │ ← LCP
│ ├─ React processes inline <script> to swap content │
│                                                    │
│ JS Bundles loaded:                                 │
│ ├─ Hydrate Client Components                      │
│ ├─ Selective hydration (prioritize user clicks)    │ ← TTI
└──────────────────────────────────────────────────┘
```

```tsx
// Example: Streaming product page
import { Suspense } from 'react';

export default async function ProductPage({ params }: Props) {
  const { id } = await params;

  return (
    <div>
      {/* Chunk 1: Renders immediately */}
      <header>
        <nav>...</nav>
      </header>

      {/* Chunk 2: Renders when product data resolves */}
      <Suspense fallback={<ProductSkeleton />}>
        <ProductDetails id={id} />
      </Suspense>

      {/* Chunk 3: Renders when reviews resolve (might be slower) */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <ReviewsSection id={id} />
      </Suspense>

      {/* Chunk 1: Renders immediately (static) */}
      <footer>...</footer>
    </div>
  );
}

async function ProductDetails({ id }: { id: string }) {
  const product = await getProduct(id); // 200ms
  return <div><h1>{product.name}</h1><p>${product.price}</p></div>;
}

async function ReviewsSection({ id }: { id: string }) {
  const reviews = await getReviews(id); // 800ms — slower!
  return <div>{reviews.map(r => <Review key={r.id} {...r} />)}</div>;
}
```

**The inline `<script>` trick**: When a Suspense boundary resolves, Next.js sends an inline `<script>` tag that tells React to swap the fallback with the real content. This happens without any client-side JavaScript bundle — it's a tiny inline script that moves DOM nodes.

---

## Q19. (Advanced) Design a Server Component architecture that handles authorization at multiple levels (route, component, and data).

**Answer**:

```tsx
// lib/auth.ts
import 'server-only';
import { cache } from 'react';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export const getSession = cache(async () => {
  const cookieStore = await cookies();
  const token = cookieStore.get('session-token')?.value;
  if (!token) return null;

  const session = await verifyToken(token);
  return session;
});

export async function requireAuth() {
  const session = await getSession();
  if (!session) redirect('/login');
  return session;
}

export async function requireRole(role: 'admin' | 'editor' | 'viewer') {
  const session = await requireAuth();
  const roleHierarchy = { admin: 3, editor: 2, viewer: 1 };
  if (roleHierarchy[session.role] < roleHierarchy[role]) {
    redirect('/unauthorized');
  }
  return session;
}
```

```tsx
// Level 1: ROUTE-LEVEL AUTH (middleware)
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedRoutes = ['/dashboard', '/admin', '/settings'];

export function middleware(request: NextRequest) {
  const token = request.cookies.get('session-token')?.value;
  const isProtected = protectedRoutes.some(route =>
    request.nextUrl.pathname.startsWith(route)
  );

  if (isProtected && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}
```

```tsx
// Level 2: COMPONENT-LEVEL AUTH
// app/admin/page.tsx
import { requireRole } from '@/lib/auth';

export default async function AdminPage() {
  const session = await requireRole('admin');
  // Only admins reach this point

  return (
    <div>
      <h1>Admin Panel</h1>
      <AdminDashboard userId={session.userId} />
    </div>
  );
}
```

```tsx
// Level 3: DATA-LEVEL AUTH (row-level security)
// lib/data.ts
import 'server-only';
import { getSession } from './auth';

export async function getUserProjects() {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  // Only return projects the user has access to
  return db.project.findMany({
    where: {
      OR: [
        { ownerId: session.userId },
        { members: { some: { userId: session.userId } } },
      ],
    },
  });
}

export async function getProject(id: string) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const project = await db.project.findUnique({
    where: { id },
    include: { members: true },
  });

  // Verify access at the data level
  const hasAccess = project?.ownerId === session.userId ||
    project?.members.some(m => m.userId === session.userId);

  if (!hasAccess) throw new Error('Forbidden');

  return project;
}
```

**Why three levels**: Defense in depth. Middleware catches unauthenticated users fast (at the edge). Component-level auth handles role-based access. Data-level auth ensures users can only see their own data even if the route is accessible.

---

## Q20. (Advanced) Compare the mental model of Server Components in Next.js vs traditional SSR (Pages Router `getServerSideProps`). Why is RSC fundamentally different?

**Answer**:

```
Traditional SSR (Pages Router):
┌─────────────────────────────────────────┐
│ getServerSideProps()                     │
│   → Fetch data on server                │
│   → Return props                        │
│                                          │
│ Component(props)                         │
│   → Render to HTML on server             │
│   → Send HTML + ALL JS to client         │
│   → Hydrate ENTIRE component tree        │
│   → Component runs AGAIN on client       │
│                                          │
│ Result: Same code runs on BOTH sides     │
└─────────────────────────────────────────┘

React Server Components:
┌─────────────────────────────────────────┐
│ Server Component                         │
│   → Render on server (with data)         │
│   → Produce RSC Payload (not just HTML)  │
│   → JS NEVER sent to client              │
│   → NEVER runs on client                 │
│   → NEVER hydrates                       │
│                                          │
│ Client Component                         │
│   → Pre-render on server (HTML)          │
│   → Send HTML + JS to client             │
│   → Hydrate on client                    │
│   → Runs on client for interactivity     │
│                                          │
│ Result: Clear separation of concerns     │
└─────────────────────────────────────────┘
```

**Key differences**:

| Aspect | Traditional SSR | RSC |
|--------|----------------|-----|
| Data fetching | Separate function (`getServerSideProps`) | Inline in component (`async`) |
| JS bundle | Full component code shipped to client | Only Client Components shipped |
| Re-renders | Component re-renders on client (hydration) | Server Components never re-render on client |
| State | Must be serializable (props boundary) | Server Components don't have state |
| Composability | Data fetching only at page level | Any component can fetch its own data |
| Streaming | Limited (full page or nothing) | Granular with Suspense boundaries |
| Refetching | Full page reload or client-side fetch | `router.refresh()` re-runs Server Components |

**The composability point is crucial**:

```tsx
// Pages Router: ONLY the page can fetch data
// pages/dashboard.tsx
export async function getServerSideProps() {
  const user = await getUser();
  const stats = await getStats();
  const notifications = await getNotifications();
  // ALL data fetching must happen HERE — can't be in child components
  return { props: { user, stats, notifications } };
}

// App Router: ANY Server Component can fetch its own data
// app/dashboard/page.tsx
export default function DashboardPage() {
  return (
    <div>
      <UserProfile />        {/* Fetches its own data */}
      <Stats />              {/* Fetches its own data */}
      <Notifications />      {/* Fetches its own data */}
    </div>
  );
}

// Each component is self-contained:
async function UserProfile() {
  const user = await getUser();
  return <div>{user.name}</div>;
}

async function Stats() {
  const stats = await getStats();
  return <div>{stats.revenue}</div>;
}
```

**This eliminates the "data waterfall" problem** of the Pages Router (where all data had to flow through `getServerSideProps`) and enables **parallel data fetching** naturally.
