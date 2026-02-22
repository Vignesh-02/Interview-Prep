# 22. State Management — Server vs Client

## Topic Introduction

In Next.js 15/16, **state** is split between **server** and **client**. Server state (data from DB/API) lives in Server Components and is fetched per request or cached. Client state (UI state, form state) lives in Client Components via React state, Context, or libraries like Zustand/Redux. Senior developers must decide where state lives to minimize JS, avoid waterfalls, and keep UX smooth.

```
State in App Router:
┌─────────────────────────────────────────────────────────────┐
│  SERVER STATE                                                 │
│  • Fetched in Server Components (fetch, DB)                  │
│  • Cached via fetch cache / React cache() / revalidateTag     │
│  • No useState; no client bundle                               │
│  • Refreshed by revalidatePath(), router.refresh(), or        │
│    revalidation on time/tag                                    │
├─────────────────────────────────────────────────────────────┤
│  CLIENT STATE                                                 │
│  • useState, useReducer, Context (in "use client" tree)         │
│  • Zustand, Redux, Jotai (Client Components only)             │
│  • Persisted in URL (searchParams), cookie, or localStorage    │
│  • Hydration must match server output                          │
└─────────────────────────────────────────────────────────────┘
```

**Why this matters**: Putting server data in client state too early causes over-fetching and large bundles. Putting UI state on the server causes full reloads. The right split (server for data, client for interactivity, URL for shareable state) is a core senior skill.

---

## Q1. (Beginner) Where should "list of products from API" state live — server or client? Why?

**Scenario**: Home page shows 20 products from your API.

**Answer**:

Keep it on the **server**: fetch in a Server Component and pass the result as props (or render it directly). No useState, no useEffect, no client fetch for initial list.

**Why**: Initial HTML contains the products; no client JS needed for first paint; better SEO and TTI. Use client state only for **interactions** on top of that (e.g. filters, sort, add to cart).

```tsx
// app/page.tsx — Server Component
export default async function HomePage() {
  const products = await fetch('https://api.example.com/products').then(r => r.json());
  return (
    <div>
      <ProductList products={products} />
      <FilterBar /> {/* Client: updates URL or local state */}
    </div>
  );
}
```

---

## Q2. (Beginner) How do you "refresh" server state after a mutation (e.g. after adding an item) without a full page reload?

**Scenario**: User adds item to cart; the cart count in the header should update.

**Answer**:

- **router.refresh()**: Re-runs Server Components and re-fetches server data; no full reload. Call it after a Server Action or client mutation.
- **revalidatePath / revalidateTag**: In a Server Action, call these so the next request (or refresh) sees fresh data.

```tsx
// actions/cart.ts
'use server';
import { revalidatePath } from 'next/cache';

export async function addToCart(productId: string) {
  await db.cart.add(productId);
  revalidatePath('/');       // Revalidate layout that shows cart count
  revalidatePath('/cart');
}
```

```tsx
// components/AddToCartButton.tsx
'use client';
import { useRouter } from 'next/navigation';
import { addToCart } from '@/actions/cart';

export function AddToCartButton({ productId }: { productId: string }) {
  const router = useRouter();

  async function handleClick() {
    await addToCart(productId);
    router.refresh(); // Re-run server components; header cart count updates
  }

  return <button onClick={handleClick}>Add to cart</button>;
}
```

---

## Q3. (Beginner) When would you use URL state (searchParams) vs React state for "selected filters"?

**Scenario**: User selects category and sort; you want shareable and back-button friendly behavior.

**Answer**:

Use **URL state** (searchParams) when:
- The state should be **shareable** (copy link, bookmark).
- **Back/forward** should work (browser history).
- You want **server** to read filters (e.g. for SEO or initial load).

Use **React state** when:
- State is **ephemeral** (e.g. modal open, accordion expanded).
- You don’t want to pollute the URL.

For "selected filters" that affect listing data, prefer **URL**: e.g. `?category=shoes&sort=price`. Read in Server Component from `searchParams`; update in Client Component with `router.push` or `router.replace`.

---

## Q4. (Beginner) Can you use React Context in a Server Component? Why or why not?

**Answer**:

**No.** Context relies on **useContext**, which is a client hook. Server Components don’t run in the browser and don’t have a "current" context. Use Context only inside Client Components. To pass "context-like" data from server to client, pass it as **props** (e.g. theme, locale, user) from a Server Component into a Client Component or a provider that wraps client children.

---

## Q5. (Beginner) What is the "donut" pattern for combining server and client state?

**Answer**:

The **donut** pattern: a **Client** component (e.g. provider) wraps **children** that are pre-rendered on the **server**. The server-rendered tree is passed as `children` into the client provider so you get client state (theme, auth UI state) without forcing the whole tree to be client.

```tsx
// app/layout.tsx
<ThemeProvider>
  <Header />   {/* Can be server; receives theme via provider */}
  {children}   {/* Server-rendered page */}
</ThemeProvider>
```

The provider holds client state; the inner content stays server-rendered and is passed in as props.

---

## Q6. (Intermediate) Implement a global "cart count" that is server-sourced but updates after client mutations without full reload.

**Scenario**: Header shows "Cart (3)". After add-to-cart, it should show "Cart (4)" without full page reload.

**Answer**:

- **Server**: Layout (or a Server Component in the layout) fetches cart count and renders it.
- **Client**: After addToCart Server Action, call **router.refresh()** so the layout re-runs and re-fetches cart count. Optionally use **useOptimistic** to show an optimistic count before refresh.

```tsx
// app/layout.tsx
import { getCartCount } from '@/lib/cart';
import { Header } from '@/components/Header';

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const cartCount = await getCartCount(); // From DB/cache
  return (
    <html>
      <body>
        <Header initialCartCount={cartCount} />
        {children}
      </body>
    </html>
  );
}
```

```tsx
// components/Header.tsx
'use client';
import { useRouter } from 'next/navigation';
import { useOptimistic } from 'react';

export function Header({ initialCartCount }: { initialCartCount: number }) {
  const router = useRouter();
  const [optimisticCount, addOptimistic] = useOptimistic(
    initialCartCount,
    (state, delta: number) => state + delta
  );

  async function onAddToCart() {
    addOptimistic(1);
    await addToCart(productId);
    router.refresh();
  }

  return <header>Cart ({optimisticCount})</header>;
}
```

---

## Q7. (Intermediate) How do you use Zustand in the App Router without causing hydration mismatches?

**Scenario**: You use Zustand for sidebar "collapsed" state; SSR and client render differ and you see a flash.

**Answer**:

- **Initialize from a safe default** so the first server and client render match (e.g. `collapsed: false`).
- **Persist to localStorage** only after mount (in useEffect) so the server never reads localStorage. On first client render, use the same default; then in useEffect restore from localStorage and update state. That way server and first client paint match; the only change happens after hydration.

```tsx
// store/sidebar.ts
'use client';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useSidebarStore = create(
  persist(
    (set) => ({
      collapsed: false,
      toggle: () => set((s) => ({ collapsed: !s.collapsed })),
    }),
    { name: 'sidebar', skipHydration: true } // Skip initial hydration from storage
  )
);

// In layout or provider: hydrate once on client
if (typeof window !== 'undefined') {
  useSidebarStore.persist.rehydrate();
}
```

Render UI from the store with a default that matches the server (e.g. always start with `collapsed: false`), then rehydrate in useEffect so after first paint the persisted value applies.

---

## Q8. (Intermediate) When would you use React Query or SWR in a Next.js App Router app? How do they interact with Server Components?

**Scenario**: You have a dashboard that shows live data and you want caching and refetch on focus.

**Answer**:

Use **React Query or SWR** in **Client Components** for:
- Client-side fetching after mount (e.g. polling, refetch on focus).
- Client-side caching and deduplication.
- Optimistic updates and mutations.

They do **not** replace Server Component data for the initial load. Pattern: **Server Component** fetches initial data and passes it as props; the **Client Component** can pass that as **initialData** (React Query) or **fallbackData** (SWR) and then take over for refetches. That way the first paint is server-driven and you get client-side reactivity on top.

```tsx
// Server passes initial data
<ClientDashboard initialStats={stats} />

// Client: use as initialData and refetch in background
const { data } = useQuery({ queryKey: ['stats'], initialData: initialStats, ... });
```

---

## Q9. (Intermediate) Production scenario: Layout shows user name from a Server Component; after login in a modal, the layout still shows "Login" until full reload. How do you fix it?

**Scenario**: Login is done in a Client Component modal; the layout is a Server Component that reads the session.

**Answer**:

After login, the server must "see" the new session on the next render. Options:

1. **Redirect after login** to the same or another page so the full tree (including layout) is re-rendered on the server with the new cookie. No need for client state for "user name" in the layout; the server will read the new session and render the name.
2. **router.refresh()** after setting the session cookie (e.g. after your login API sets the cookie). Then the layout (Server Component) runs again and fetches the updated session.

So: set the session cookie (e.g. via your auth API or Server Action), then call **router.refresh()** (and optionally close the modal and redirect). The layout will re-run and show the user name.

---

## Q10. (Intermediate) How do you pass "current user" from server to multiple Client Components without prop drilling?

**Scenario**: Header, sidebar, and profile page all need the current user.

**Answer**:

- **Option A**: Fetch user in the **root or segment layout** (Server Component) and pass it as a prop to a **Client provider** that holds it in React Context. All client children can then use the context. The server does one fetch; the client receives it once via props into the provider.
- **Option B**: Each Client Component receives `user` as a prop from the nearest Server parent. That can be the layout; no need to pass through every intermediate component if the layout renders both the header and the main content and passes `user` to each.

Recommended: **Layout fetches user** → passes to a **Client Context provider** (e.g. `UserProvider`) that wraps the tree. Client components use `useContext(UserContext)` to read the user. No prop drilling; single source of truth from the server.

---

## Q11. (Intermediate) What is useOptimistic and when would you use it with Server Actions?

**Scenario**: User clicks "Like"; you want the count to update immediately, then reconcile with the server.

**Answer**:

**useOptimistic** (React 19) lets you show an **optimistic** state (e.g. count + 1) immediately, then replace it with the real state when the server responds. Use it with a Server Action that performs the mutation and then **router.refresh()** (or return updated data).

```tsx
'use client';
import { useOptimistic } from 'react';

export function LikeButton({ postId, initialCount }: { postId: string; initialCount: number }) {
  const [optimisticCount, addOptimistic] = useOptimistic(initialCount, (s, delta: number) => s + delta);

  async function handleClick() {
    addOptimistic(1);
    await likePost(postId);
    router.refresh();
  }

  return <button onClick={handleClick}>Like ({optimisticCount})</button>;
}
```

---

## Q12. (Intermediate) Find the bug: Cart count in the header never updates after addToCart because the layout doesn’t re-run.

**Wrong flow**:

```tsx
// actions/cart.ts
'use server';
export async function addToCart(id: string) {
  await db.cart.add(id);
  return { ok: true };
}

// components/Header.tsx (Server Component)
export async function Header() {
  const count = await getCartCount();
  return <span>Cart ({count})</span>;
}

// AddToCartButton calls addToCart() but does not trigger any refresh.
```

**Answer**:

The layout (and Header) run once. After the Server Action, the server doesn’t re-render the layout, so the count doesn’t change. **Fix**: After the mutation, trigger a refresh so the layout re-runs and re-fetches the count.

- In the Client Component that calls addToCart: after `await addToCart(id)`, call **router.refresh()**.
- Optionally use **revalidatePath('/')** or a tag used by the layout’s data inside the Server Action so the next request sees fresh data; **router.refresh()** will then show it without a full reload.

---

## Q13. (Advanced) Design state flow for a multi-step checkout: step index, form data, and validation. Server vs client, and how to persist on refresh.

**Scenario**: Checkout has 3 steps; user can refresh or go back; form data should persist and be valid.

**Answer**:

- **Step index**: Keep in **URL** (e.g. `/checkout?step=2`) so back/forward and refresh preserve step.
- **Form data**: Keep in **client state** (or in a Client Component + URL for critical fields). Optionally persist to **sessionStorage** in useEffect so refresh keeps it; or save drafts to the server (e.g. PATCH /api/checkout/draft) and rehydrate from server on load.
- **Validation**: Run **client-side** for UX (instant feedback); run **server-side** in the Server Action before committing the order. Use the same schema (e.g. Zod) on both.
- **Server**: On final submit, run Server Action that validates and creates the order; then redirect to success page. No need to put the whole form state on the server until submit.

---

## Q14. (Advanced) How do you avoid "flash of wrong content" when using persisted client state (e.g. theme) that differs from server default?

**Scenario**: Server renders "light"; user had "dark" in localStorage; you see a flash of light then dark.

**Answer**:

- **Server**: Always render the same default (e.g. light) and use a **non-blocking** script or a class that doesn’t change layout (e.g. only colors) so the flash is minimal.
- **Client**: In a **layout effect** or very first client render, read theme from localStorage and apply it (e.g. class on `<html>`). Use **suppressHydrationWarning** on `<html>` if you change a class that affects many nodes, to avoid React hydration warnings when the first client render differs.
- **Better**: Inject a small **inline script** in `<head>` that runs before paint and sets `document.documentElement.classList.add('dark')` (or similar) from localStorage, so the first paint is already correct. Then your React app just reads the same value and doesn’t change it on first mount, avoiding a flash.

---

## Q15. (Advanced) Compare using URL state for filters vs storing filters in a global client store. Tradeoffs for SEO, shareability, and back/forward.

**Answer**:

| | URL state | Client store |
|--|-----------|--------------|
| Shareable | Yes (copy link) | No |
| Back/forward | Yes | No (unless you sync to URL) |
| SEO | Server can read and pre-render filtered list | Server sees default; filters applied only on client |
| Complexity | Need to parse/serialize searchParams | Simpler state, but no shareability |

For **filters that define "what page this is"** (e.g. category, sort), prefer **URL state** so the page is shareable and SEO-friendly. For purely UI state (e.g. "modal open"), use client state.

---

## Q16. (Advanced) Can you use Redux in the App Router? How do you provide the store to both server and client trees?

**Answer**:

Redux is **client-only**. You cannot use the store in Server Components. Pattern:

- Create the store in a **Client Component** (e.g. `ReduxProvider`) and wrap your app with it. The store is created once on the client.
- **Server Components** cannot read from Redux. Pass any server data into the client tree as props (e.g. initial state or prefetched data). You can pass **preloaded state** into the provider so the client store is initialized from server data (e.g. `preloadedState` from getServerSideProps-like data in the layout).

So: **Server** fetches data → passes to **layout/page** → passes to **ReduxProvider** as initial state → **Client** components use the store. The server never "uses" Redux; it only supplies initial data.

---

## Q17. (Advanced) Next.js 15 vs 16: Does the default caching change (e.g. fetch no longer cached by default) affect how you design server state?

**Answer**:

**Next.js 15**: `fetch` is **not** cached by default. You must opt in with `cache: 'force-cache'` or `next: { revalidate }`. So server state is "fresh" unless you explicitly cache.

**Next.js 16**: Same direction (no default fetch cache). Design impact:

- **Explicit caching**: Use `next: { tags: ['x'], revalidate: 3600 }` where you want cache and on-demand invalidation.
- **Request memoization**: Still applies per request; identical fetches in the same render are deduplicated.
- **Router cache**: Client-side cache of RSC payloads; affected by staleTimes and revalidation. So "server state" design stays the same: decide what to cache and when to revalidate; the main change is you’re not accidentally caching everything.

---

## Q18. (Advanced) Production scenario: You need "last N visited products" across the app. Where do you store it and how do you avoid hydration issues?

**Scenario**: Show "Recently viewed" in sidebar; data is only from client navigation.

**Answer**:

Store in **client** (e.g. **localStorage** or in-memory + localStorage for persistence). Server has no way to know "last N visited" without sending it on every request (cookie or API).

- **Hydration**: Server renders a **placeholder** (e.g. "Loading…" or empty list). Client, in **useEffect**, reads from localStorage and sets state; then render the list. That way server and first client render match (both placeholder), and you avoid hydration mismatch. Do **not** read localStorage during the first render (only in useEffect).

---

## Q19. (Advanced) How do you implement "optimistic UI" for a list when the user deletes an item, and the Server Action might fail?

**Scenario**: User clicks "Remove"; item disappears; if the action fails, item should reappear and show error.

**Answer**:

- Use **useOptimistic**: Render list from `optimisticList`; on "Remove" call `removeOptimistic(id)` so the item is removed from the list immediately. Then call the Server Action. If it **succeeds**, call **router.refresh()** so the server list replaces the optimistic one (and they match). If it **fails**, **useOptimistic** will revert to the previous state when you don’t pass a new optimistic value (or you pass the error and revert manually). So: on failure, either let the hook revert (if you didn’t commit) or set the list back to the previous and show a toast.

```tsx
const [optimisticList, removeOptimistic] = useOptimistic(
  items,
  (state, removedId: string) => state.filter((i) => i.id !== removedId)
);

async function handleRemove(id: string) {
  removeOptimistic(id);
  try {
    await removeItem(id);
    router.refresh();
  } catch {
    toast.error('Failed to remove');
    router.refresh(); // Restore from server
  }
}
```

---

## Q20. (Advanced) Design a pattern where the server sends "initial state" and the client can override it with real-time updates (e.g. WebSocket) without losing server-driven defaults.

**Scenario**: Dashboard shows server-rendered stats; then a WebSocket pushes live updates; on refresh, user sees server data again.

**Answer**:

- **Server**: Fetches initial stats and passes them as props to a Client Component.
- **Client**: Uses that as **initial state** (or **initialData** in React Query). Subscribes to WebSocket in useEffect and updates local state (or query cache) when messages arrive. On **router.refresh()**, the server sends new initial state and you can either replace the client state with that or merge (e.g. use server data as baseline and only override fields that have been updated via WebSocket). Key: treat server as source of truth on load and after refresh; WebSocket as overlay for live updates. Use a **key** (e.g. page path) so that when the user navigates or refreshes, you reinitialize from server and don’t carry stale WebSocket state across pages.
