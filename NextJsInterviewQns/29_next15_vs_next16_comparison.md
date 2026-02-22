# 29. Next.js 15 vs Next.js 16 — Comparison & When to Use What

## Topic Introduction

**Next.js 15** established the **App Router** as stable, **params**/searchParams as **Promises**, and **fetch** no longer cached by default. **Next.js 16** builds on that with **Turbopack** as the default bundler (dev and build), refined **caching** (e.g. **staleTimes**), and continued **React 19** and **Partial Prerendering (PPR)** support. Senior developers know version differences to plan upgrades and choose the right features.

```
Next 15 → 16 at a glance:
┌─────────────────────────────────────────────────────────────┐
│  Next 15: App Router stable, async params, fetch opt-in cache│
│  Next 16: Turbopack default, caching refinements, same RSC   │
│  Both: PPR (experimental/stable), React 19, Server Actions   │
└─────────────────────────────────────────────────────────────┘
```

---

## Q1. (Beginner) What is the main difference in how you use dynamic route params in Next.js 15 vs 14?

**Answer**:

In **Next.js 15**, **params** (and **searchParams**) in **page.tsx** and **layout.tsx** are **Promises** and must be **await**ed. In **Next.js 14**, they were plain objects. So in 15: **const { slug } = await params**. This allows async resolution and aligns with streaming.

---

## Q2. (Beginner) In Next.js 15, is fetch cached by default?

**Answer**:

**No.** In Next.js 15, **fetch** is **not** cached by default (in 14 it was). You opt in with **cache: 'force-cache'** or **next: { revalidate: N }** or **tags**. This makes caching explicit and avoids accidental long-lived cache.

---

## Q3. (Beginner) What role does Turbopack play in Next.js 16?

**Answer**:

In **Next.js 16**, **Turbopack** is the **default** bundler for both **development** and **production** builds. It replaces Webpack and gives faster builds and faster Fast Refresh. You don’t have to enable it; it’s on by default. You can opt out if you hit compatibility issues.

---

## Q4. (Beginner) Are the App Router and Pages Router APIs the same in Next.js 15 and 16?

**Answer**:

**Largely yes.** Both 15 and 16 use the same App Router conventions (layouts, **page.tsx**, **route.ts**, Server/Client Components). **next/navigation** and **next/headers** behave the same. Differences are in **bundler** (Turbopack in 16), **caching** defaults/tuning, and any new options in 16 (e.g. **staleTimes**). No major API removals for the App Router between 15 and 16.

---

## Q5. (Beginner) Do you need different next.config.js for Next.js 15 vs 16?

**Answer**:

**Usually no.** The same **next.config.js** works for both. In 16, some **experimental** flags may be promoted or renamed; check the upgrade guide. If you used **webpack** custom config, test with Turbopack in 16 (it has different extension points). No new **required** config for 16.

---

## Q6. (Intermediate) Compare data fetching and caching in Next.js 15 vs 16: what stays the same and what changes?

**Answer**:

- **Same**: **fetch** opt-in caching (**cache**, **next.revalidate**, **tags**), **revalidatePath** / **revalidateTag**, **unstable_cache** / **cache()**, Server Component async fetch.
- **16**: **staleTimes** (Router Cache) and other caching refinements may be tuned; same APIs but potentially different default behavior for how long client-side RSC payloads are considered fresh. Check the 16 release notes for exact defaults.

---

## Q7. (Intermediate) You’re on Next.js 15 and use generateStaticParams for 1000 paths. Will the build be faster on Next.js 16? Why?

**Answer**:

**Often yes.** Next.js 16 uses **Turbopack** for production build by default, which is typically **faster** than Webpack for large apps. So the same **generateStaticParams** and static generation will run with a faster bundling step. The actual work (fetching data for 1000 paths) is the same unless you also use caching (e.g. Turbo remote cache) or parallelization improvements in 16.

---

## Q8. (Intermediate) Production scenario: You rely on the client Router Cache (back/forward shows cached data). Should you expect different behavior in Next.js 16?

**Answer**:

**Possibly.** Next.js 16 may change **staleTimes** or how long the client keeps RSC payloads. If your app depends on “stale” being shown for a certain time (or immediately refetched), check the 16 docs and test back/forward and **router.refresh()** after upgrading. Adjust **staleTimes** in 16 if the defaults don’t match your product needs.

---

## Q9. (Intermediate) What is PPR (Partial Prerendering) and is it different in Next.js 15 vs 16?

**Answer**:

**PPR** serves a **static shell** immediately and streams **dynamic** parts (Suspense boundaries) when ready. It’s the same concept in 15 and 16; in 16 it may be **stable** or better optimized. You enable it in **next.config.js** and use **Suspense** around dynamic content. No API change between 15 and 16 for PPR.

---

## Q10. (Intermediate) Find the bug: Code works in Next.js 14 but breaks in 15 with “params is not iterable” or similar.

**Wrong code**:

```tsx
export default function Page({ params }: { params: { slug: string } }) {
  return <h1>{params.slug}</h1>;
}
```

**Answer**:

In **Next.js 15**, **params** is a **Promise**. Destructuring **params** directly or using **params.slug** without **await** can throw. **Fix**: Make the component **async** and **await params**.

```tsx
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <h1>{slug}</h1>;
}
```

---

## Q11. (Intermediate) When would you stay on Next.js 15 instead of upgrading to 16 immediately?

**Answer**:

- **Plugin or dependency** not yet compatible with Turbopack (e.g. custom Webpack loaders).
- **Stability**: Prefer waiting for a few 16 patch releases if the project is critical.
- **CI/build**: Need to validate that 16’s build output and cache behave as expected.
- **Documentation**: Team and runbooks are still on 15; plan the upgrade and test in staging first.

---

## Q12. (Intermediate) How do you run the same app in both Next.js 15 and 16 during an upgrade (e.g. in CI)?

**Answer**:

In CI, install the desired version (e.g. **npm install next@15** vs **next@16**) and run **build** and tests. Use a matrix job to run one job with 15 and one with 16. Or upgrade the project to 16 and run CI; if you need to compare, temporarily use **npx create-next-app** or a branch with 15 and diff behavior. You don’t run “both” in one process; you run two builds with two versions.

---

## Q13. (Advanced) Summarize the main breaking or behavioral changes from Next.js 14 → 15 and 15 → 16.

**Answer**:

- **14 → 15**: **params** and **searchParams** are Promises (must **await**). **fetch** no longer cached by default. **cookies()** and **headers()** are async. Any **getStaticProps**/getServerSideProps migration to App Router is a separate migration, not a version bump.
- **15 → 16**: **Turbopack** default for dev and build; possible **staleTimes**/caching tweaks; some **experimental** flags may be promoted or removed. Fewer breaking API changes than 14 → 15; mainly build/runtime behavior.

---

## Q14. (Advanced) How does Turbopack in Next.js 16 affect custom webpack config (e.g. next.config.js webpack function)?

**Answer**:

**Turbopack does not use the Webpack config.** So **next.config.js** **webpack** and **webpackDevMiddleware** are **ignored** when Turbopack is used. If you depend on custom Webpack loaders or plugins, you either: (1) Find Turbopack equivalents or community solutions, (2) Opt out of Turbopack (if 16 allows) and keep using Webpack, or (3) Replace the need for that config (e.g. use a different way to achieve the same result).

---

## Q15. (Advanced) In both Next.js 15 and 16, how do you choose between static generation, SSR, and PPR for a given page in production?

**Answer**:

- **Static (SSG)**: Public, same for all users, build-time data (e.g. marketing, blog with **generateStaticParams**). Use **revalidate** or **revalidateTag** for freshness.
- **SSR**: Per-request data, auth-dependent, or always fresh. No **generateStaticParams**; fetch in Server Component; dynamic.
- **PPR**: Page has both static shell (header, layout) and dynamic parts (user-specific, live data). Use **Suspense** for dynamic segments; get fast TTI + fresh content. Prefer PPR when the page clearly splits into static and dynamic.

---

## Q16. (Advanced) Does Next.js 16 change how Middleware runs (e.g. Edge, limits)?

**Answer**:

**No fundamental change.** Middleware still runs on the **Edge**; same **NextRequest**/ **NextResponse** API. Turbopack may compile middleware differently (faster), but behavior is the same. Check release notes for any Edge runtime limits (e.g. body size, execution time) in 16.

---

## Q17. (Advanced) How do Server Actions behave in Next.js 15 vs 16? Any differences?

**Answer**:

**Same model:** **"use server"**, form actions, **useFormStatus**, **useActionState**. No breaking change in 16. Possible improvements in 16 (e.g. error handling or serialization) are implementation details; the API you use stays the same.

---

## Q18. (Advanced) Production scenario: After upgrading 15 → 16, production build fails with “Turbopack doesn’t support X”. What are your options?

**Answer**:

- **Option 1**: Disable Turbopack for the production build (if 16 supports it), e.g. **next build --no-turbopack** or a **next.config.js** option, and keep using Webpack for build.
- **Option 2**: Replace “X” (e.g. a Webpack plugin) with a Turbopack-compatible approach or wait for Turbopack support.
- **Option 3**: Stay on 15 until 16 supports “X” or you can remove the dependency.

---

## Q19. (Advanced) Compare the recommended way to set metadata (title, description) in Next.js 15 and 16.

**Answer**:

**Identical.** Both use the **Metadata** API: **metadata** export and **generateMetadata** in **layout.tsx** / **page.tsx**. No change in 16. **metadataBase**, **openGraph**, **twitter**, etc. work the same.

---

## Q20. (Advanced) Create a one-page “upgrade checklist” for moving a production app from Next.js 15 to 16.

**Answer**:

1. **Changelog**: Read Next.js 16 release/upgrade guide.
2. **Dependencies**: Bump **next** (and **react**/react-dom if required); run **npm install**.
3. **Build**: Run **next build**; fix any Turbopack errors (e.g. unsupported plugins).
4. **Params/searchParams**: Already async in 15; no change for 16.
5. **Caching**: Test **fetch** cache, **revalidateTag**, and client navigation (Router Cache); adjust **staleTimes** if needed.
6. **Tests**: Run unit, integration, and E2E tests.
7. **Staging**: Deploy to staging; smoke-test critical flows and performance.
8. **Rollback**: Have a plan to revert to 15 (e.g. redeploy previous build) if issues appear in production.
9. **Monitoring**: Watch errors and Core Web Vitals after rollout.
10. **Docs**: Update README and deployment docs to “Next.js 16”.
