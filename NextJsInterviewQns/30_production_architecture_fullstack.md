# 30. Production Architecture — Full-Stack Next.js at Scale

## Topic Introduction

**Production architecture** for Next.js at scale involves **rendering strategy** (SSG, SSR, PPR, streaming), **data layer** (DB, cache, APIs), **auth**, **security**, **deployment**, and **observability**. Senior developers design a **three-tier**-style separation: presentation (Next.js), business/API layer, and data/store; they know when to use Server Components, Server Actions, Route Handlers, and external services.

```
Three-tier style with Next.js:
┌─────────────────────────────────────────────────────────────┐
│  Presentation: Next.js (RSC, Client Components, routing)     │
│  Application: Server Actions, Route Handlers, BFF, or API     │
│  Data: DB, cache (Redis), external APIs, queues              │
│  Cross-cutting: Auth (Middleware + server), env, monitoring  │
└─────────────────────────────────────────────────────────────┘
```

---

## Q1. (Beginner) What are the main “tiers” in a typical production Next.js app?

**Answer**:

(1) **Presentation**: Next.js pages, layouts, Server and Client Components. (2) **Application**: Server Actions, Route Handlers, and/or a separate BFF/API that Next.js calls. (3) **Data**: Database, Redis/cache, external APIs. **Cross-cutting**: Auth (middleware + server checks), env vars, logging/monitoring.

---

## Q2. (Beginner) Where should secrets (DB URL, API keys) live in production?

**Answer**:

In the **deployment platform’s environment** (e.g. Vercel env vars, AWS Secrets Manager). Never in the repo. In Next.js, use **server-only** env (no **NEXT_PUBLIC_**) so they’re not in the client bundle. Load them in Server Components, Server Actions, Route Handlers, and API clients that run on the server.

---

## Q3. (Beginner) What is the role of Middleware in a production Next.js app?

**Answer**:

Run **before** the request hits the page: **auth** (redirect unauthenticated users), **i18n** (locale detection/redirect), **rewrites**, **A/B** (rewrite to variant), **security headers**. Keep it small and fast (Edge); heavy logic or DB calls belong in Server Components or Route Handlers.

---

## Q4. (Beginner) When would you use a Route Handler instead of a Server Action?

**Answer**:

**Route Handler**: Non-GET HTTP (e.g. webhooks, third-party callbacks), file download, or when the client is not a form (e.g. fetch from another service). **Server Action**: Form submissions, mutations triggered from the same app’s UI, and when you want a single function call from the client without a separate REST endpoint.

---

## Q5. (Beginner) Why is it important to avoid fetching in the client when the same data could be fetched on the server?

**Answer**:

Server fetch: **one** round trip (server → DB → server → HTML), better **SEO**, no loading state for initial data, and secrets stay on the server. Client fetch: extra round trip (browser → server → DB), possible flash of loading, and you may need to expose an API and handle auth/CORS. Prefer server fetch for initial data; use client fetch for follow-up or user-triggered data.

---

## Q6. (Intermediate) Design the data flow for a “user dashboard” page: auth required, data from DB, and a “refresh” button.

**Answer**:

- **Auth**: Middleware checks session/cookie; redirect to login if missing. Page (Server Component) can also call **cookies()** / **headers()** and validate.
- **Data**: Server Component fetches dashboard data (DB or API) using the session; render the initial UI. Use **cache()** or **revalidate** as needed.
- **Refresh**: Client Component with a button that calls **router.refresh()** (refetches RSC payload) or a Server Action that revalidates and then **router.refresh()**. Alternatively, a client fetch to an API that returns fresh data and update local state; Server Action + refresh is simpler and keeps one source of truth.

---

## Q7. (Intermediate) How do you structure environment-specific config (API base URL, feature flags) for Next.js in production?

**Answer**:

Use **env vars** (e.g. **NEXT_PUBLIC_APP_URL**, **API_BASE_URL**). Set different values per environment in the platform (Vercel: Production vs Preview). For feature flags, use **NEXT_PUBLIC_FEATURE_X** if the client needs it, or a server-only var and expose via Server Component or API. Optionally a small **config** module that reads **process.env** and exports typed config; keep it server-only where possible.

---

## Q8. (Intermediate) Production scenario: You have a Server Action that updates the DB. How do you ensure the client sees updated data after submit?

**Answer**:

After the Server Action succeeds, call **router.refresh()** so Next.js refetches the RSC tree and the page re-renders with new data. Optionally use **revalidatePath** or **revalidateTag** inside the Server Action so the refreshed data is up to date. If the UI is in a Client Component, you can also return the new data from the Server Action and set state, but **revalidatePath** + **router.refresh()** keeps server and client in sync with one source of truth.

---

## Q9. (Intermediate) Where would you put rate limiting in a Next.js app that has both Server Actions and Route Handlers?

**Answer**:

- **Middleware**: Rate limit by IP or identifier for all requests (simple, at the edge). Good for global protection.
- **Route Handlers**: Check rate limit inside the handler (e.g. Redis counter) for API routes; return **429** when exceeded.
- **Server Actions**: Call the same rate-limit logic (e.g. shared helper that checks Redis) at the start of the action; throw or return an error when exceeded. Prefer Middleware for coarse limits and per-route/per-action logic for finer control.

---

## Q10. (Intermediate) Find the bug: In production, some users see other users’ data on a dynamic page.

**Wrong code** (conceptually):

```tsx
// app/dashboard/page.tsx
export default async function Dashboard() {
  const userId = cookies().get('userId')?.value; // sync in 14, async in 15
  const data = await db.query('SELECT * FROM orders'); // no filter
  return <Orders orders={data} />;
}
```

**Answer**:

Two bugs: (1) **cookies()** in Next.js 15 is async: use **const cookieStore = await cookies()**. (2) **Data is not scoped to the user**: query must filter by **userId** (e.g. `WHERE user_id = $1`). Otherwise the DB returns all orders and you leak data. **Fix**: **await cookies()**, get **userId**, validate it, and pass it to the query. Never trust client-only; validate session on the server and use it in the query.

---

## Q11. (Intermediate) How do you integrate a third-party API (e.g. payment provider webhook) that must receive POSTs with a secret?

**Answer**:

Use a **Route Handler** (e.g. **app/api/webhooks/payment/route.ts**). In **POST**, read the raw body (or use the framework’s body), verify the signature (e.g. HMAC with shared secret from env), then process the event (e.g. update DB, enqueue job). Return **200** quickly so the provider doesn’t retry; do heavy work in a background job if needed. Keep the webhook secret in server env only.

---

## Q12. (Intermediate) Explain how you would run Next.js behind a CDN and ensure dynamic routes are not cached incorrectly.

**Answer**:

- **Static/ISR**: Next.js sends **Cache-Control** (e.g. **s-maxage**, **stale-while-revalidate**); CDN caches and respects it.
- **Dynamic**: Next.js sends **no-store** or **private** so the CDN doesn’t cache. Ensure dynamic routes (or their data fetches) don’t set long **s-maxage**.
- **Vercel**: Edge handles this; for custom CDN, set cache rules by path (e.g. cache **/_next/static** and static pages; bypass cache for **/api/** and authenticated pages) or rely on **Cache-Control** from Next.js.

---

## Q13. (Advanced) Design a three-tier architecture: Next.js (front + BFF), business logic service (Node/other), and DB. What does Next.js call and when?

**Answer**:

- **Next.js**: Renders UI; for data it calls the **business logic service** (HTTP/gRPC), not the DB directly. Server Components and Server Actions call that service.
- **Business service**: Owns validation, transactions, and DB access; exposes REST or gRPC. Next.js is a client of this service.
- **DB**: Only the business service talks to it. Next.js never has DB credentials. Use this when multiple clients (web, mobile, partners) share the same backend; Next.js stays a thin BFF that can add auth and formatting.

---

## Q14. (Advanced) How do you handle long-running or heavy work (e.g. report generation, email send) triggered from a Next.js Server Action?

**Answer**:

Don’t block the response. **Options**: (1) **Queue**: Server Action enqueues a job (e.g. Redis/Bull, SQS); a worker processes it. Return “Accepted” to the user and poll or use SSE/WebSocket for status. (2) **Background**: In a Node server (not serverless), you could spawn a background task after responding, but serverless can’t do that reliably. (3) **Third-party**: Use a service (e.g. Inngest, Trigger.dev) that the Server Action calls to enqueue work. Prefer queue + worker for production.

---

## Q15. (Advanced) How do you ensure auth is enforced consistently across Server Components, Server Actions, and Route Handlers?

**Answer**:

- **Middleware**: Validate session (e.g. JWT or session cookie); redirect unauthenticated users to login for protected paths. Reduces duplicate checks but doesn’t replace server checks.
- **Server**: In every Server Component that needs auth, call **await cookies()** or **headers()** and validate; in Server Actions and Route Handlers, validate at the start. Use a shared **getSession()** (or similar) that reads cookie, verifies token, returns user or null. Never trust only the client; always validate on the server for each boundary.

---

## Q16. (Advanced) Production scenario: DB is slow; the dashboard times out. What do you optimize?

**Answer**:

- **Query**: Add indexes, reduce N+1, limit columns and rows; use **read replicas** if available.
- **Caching**: Cache the result in Redis (or **unstable_cache**/cache()) with a short TTL; revalidate on mutation.
- **UI**: Use **Suspense** and streaming so the shell renders immediately and the slow part streams in; show a skeleton for the dashboard block. Optionally move the slow query to a **loading** boundary so the rest of the page isn’t blocked.
- **Timeout**: Increase serverless function timeout if acceptable; better to fix the query and cache so timeouts are rare.

---

## Q17. (Advanced) How do you structure a large App Router codebase for multiple teams (e.g. marketing, dashboard, admin)?

**Answer**:

- **Route groups**: **(marketing)**, **(dashboard)**, **(admin)** for layout and file organization without changing URLs.
- **Parallel routes**: Use **@slots** for shared layout (e.g. dashboard sidebar + content).
- **Monorepo**: Next app in one package; shared UI and libs in other packages. Clear ownership per route group or package.
- **Conventions**: Shared **getSession()**, error boundaries, and data-fetching patterns so each team doesn’t reinvent. Document which team owns which routes.

---

## Q18. (Advanced) Next.js 15 vs 16 in this architecture: what would you document or adjust?

**Answer**:

- **16**: Turbopack as default; document that custom Webpack is not used. Build and deploy steps stay the same. If you use **staleTimes** or Router Cache behavior, document 16’s defaults and any overrides.
- **Caching**: In both 15 and 16, document **fetch** cache (opt-in in 15), **revalidatePath**/revalidateTag usage, and any CDN rules so ops and other devs know how freshness works.
- **No architectural change** between 15 and 16 for tiers, auth, or data flow; only build and cache tuning.

---

## Q19. (Advanced) How do you add observability (logging, tracing, errors) to a production Next.js app?

**Answer**:

- **Errors**: Use **error.tsx** and **global-error.tsx**; report to Sentry (or similar) in the error boundary and in **instrumentation.ts** (if used).
- **Logging**: Structured logs in Server Actions and Route Handlers; include request id (from headers or generate). Send to CloudWatch, Datadog, or your log aggregator.
- **Tracing**: Use OpenTelemetry or vendor (e.g. Sentry) to trace requests from Middleware → Server Component → fetch/DB. Next.js supports **instrumentation.ts** for startup and request hooks. Correlate logs and traces with the same request id.

---

## Q20. (Advanced) Design a production checklist for launching a new Next.js app (auth, data, caching, security, deploy).

**Answer**:

1. **Auth**: Middleware + server-side validation on every protected route and Server Action; secure, HttpOnly cookies; no secrets in client.
2. **Data**: All queries parameterized and scoped to the authenticated user; no raw user input in queries; use connection pooling and timeouts.
3. **Caching**: **fetch** cache and **revalidate**/tags documented; dynamic routes not cached at CDN; **staleTimes** or Router Cache considered.
4. **Security**: **NEXT_PUBLIC_** only for non-secret config; CSRF considered for state-changing operations; headers (CSP, HSTS) in next.config or Middleware; no **dangerouslySetInnerHTML** with user input.
5. **Deploy**: Env vars set in platform; build uses correct Node version; health check endpoint if needed; migrations run before or with deploy; rollback plan and monitoring (errors, latency, Core Web Vitals) in place.
