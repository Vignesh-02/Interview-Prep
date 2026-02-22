# 27. Migration — Pages to App Router, Next 15 to 16

## Topic Introduction

**Migration** topics include moving from the **Pages Router** to the **App Router**, upgrading **Next.js 15 → 16**, and handling **breaking changes** (e.g. **params** as Promise, **fetch** caching defaults, **client** Router Cache). Senior developers plan incremental migrations, preserve URLs and behavior, and fix compatibility issues.

```
Migration strategies:
┌─────────────────────────────────────────────────────────────┐
│  Pages → App: Route by route; keep both during transition    │
│  Next 15 → 16: Changelog; fix params/async; test caching     │
│  Coexistence: App Router takes precedence for same path     │
└─────────────────────────────────────────────────────────────┘
```

---

## Q1. (Beginner) Can the Pages Router and App Router coexist in the same Next.js project?

**Answer**:

Yes. **App Router** is used for routes under **app/**; **Pages Router** for routes under **pages/**. If the same path exists in both (e.g. **app/dashboard/page.tsx** and **pages/dashboard.tsx**), the **App Router** wins. Use this to migrate route by route: add the new route in **app/** and remove it from **pages/** when done.

---

## Q2. (Beginner) What is the first file you need when adopting the App Router?

**Answer**:

**app/layout.tsx** (root layout). It must export a default component that renders **<html>** and **<body>**. Without it, the App Router doesn’t run. You can start with a minimal layout and migrate **pages/index.tsx** to **app/page.tsx** so the home page is served by the App Router.

---

## Q3. (Beginner) When migrating getServerSideProps to the App Router, where does the data fetching go?

**Answer**:

Into the **page** (or layout) as a **Server Component**. Fetch (or call your data layer) directly in the component; no separate function. Use **async** and **await**; the result is rendered on the server. For **getStaticProps**-style behavior, use **generateStaticParams** and static generation; for **getServerSideProps**-style, just fetch in the Server Component (it runs per request unless cached).

---

## Q4. (Beginner) What changed in Next.js 15 regarding params in page and layout components?

**Answer**:

**params** (and **searchParams**) are now **Promises** and must be **await**ed. So instead of `params.slug` you do `const { slug } = await params`. This applies to **page.tsx**, **layout.tsx**, and **generateMetadata**. In Client Components that receive **params** as a prop, use React’s **use()** to unwrap the Promise.

---

## Q5. (Beginner) What changed in Next.js 15 regarding fetch caching?

**Answer**:

In **Next.js 15**, **fetch** is **no longer cached by default** (previously it was). So you must opt in with **cache: 'force-cache'** or **next: { revalidate: N }** (or **tags**) if you want caching. This avoids accidental long-lived cache and makes behavior more predictable.

---

## Q6. (Intermediate) Migrate a Pages Router dynamic route (e.g. pages/blog/[slug].tsx) to the App Router. Include getStaticPaths equivalent.

**Scenario**: You have getStaticPaths and getStaticProps for blog posts.

**Answer**:

- **getStaticPaths** → **generateStaticParams** in **app/blog/[slug]/page.tsx**.
- **getStaticProps** → Fetch inside the **page** component (and optionally in **generateMetadata**).

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from 'next';

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  const posts = await getSlugs();
  return posts.map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPost((await params).slug);
  return { title: post.title, description: post.excerpt };
}

export default async function BlogPost({ params }: Props) {
  const post = await getPost((await params).slug);
  return <article>{post.content}</article>;
}
```

---

## Q7. (Intermediate) How do you migrate _app.tsx and _document.tsx into the App Router?

**Answer**:

- **_document.tsx**: Custom **<html>** or **<head>** move into **app/layout.tsx**. Root layout must render **<html>** and **<body>**. Use the **metadata** export (and **generateMetadata**) instead of **<Head>** for title and meta.
- **_app.tsx**: **Provider** wrappers and global state go in **app/layout.tsx** (e.g. wrap **{children}** with your providers). **pageProps** are no longer used; data is fetched in each page/layout in the App Router.

---

## Q8. (Intermediate) You have an API route (pages/api/hello.ts). How do you migrate it to the App Router?

**Answer**:

Create **app/api/hello/route.ts** and export **GET**, **POST**, etc. as functions that receive **Request** and return **Response** (or **NextResponse**).

```tsx
// app/api/hello/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ message: 'Hello' });
}

export async function POST(request: Request) {
  const body = await request.json();
  return NextResponse.json({ received: body });
}
```

---

## Q9. (Intermediate) Production scenario: After upgrading to Next.js 15, some pages show 404. What could be wrong?

**Answer**:

- **params** is now a **Promise**: If you didn’t update to **await params**, the page might throw or behave incorrectly and the framework might surface a 404 or error. Fix: **const { slug } = await params** (and same for **searchParams** where used).
- **Dynamic segment not in generateStaticParams**: If **dynamicParams** is **false** and the requested segment wasn’t returned by **generateStaticParams**, the route 404s. Either set **dynamicParams: true** or add the missing params to **generateStaticParams**.
- **File moved or renamed**: Ensure the file is under **app/** and follows the convention (e.g. **page.tsx** for the route). Check for typos in folder names.

---

## Q10. (Intermediate) How do you preserve existing URLs (e.g. /blog/:slug) when migrating from Pages to App so that links and SEO don’t break?

**Answer**:

Use the **same** path structure in the App Router. So **pages/blog/[slug].tsx** becomes **app/blog/[slug]/page.tsx**. The URL **/blog/my-post** stays the same. No redirect needed. Ensure **generateMetadata** and **alternates.canonical** (if any) use the same URL pattern. If you had a different structure (e.g. **pages/post/[slug].tsx**), add **app/post/[slug]/page.tsx** or add a **redirect** in **next.config.js** or middleware from the old path to the new one.

---

## Q11. (Intermediate) What is the recommended order to migrate: layout first or pages first?

**Answer**:

Migrate **layout** first (root layout with **<html>**, **<body>**, and providers), then **leaf pages** (no nested layout), then nested layouts and their pages. That way you establish the shell and then fill in routes one by one. Migrating a whole section (e.g. **/dashboard/**) including its layout at once is also fine if the section is self-contained.

---

## Q12. (Intermediate) Find the bug: After migrating to App Router, redirect in a Server Action doesn’t work (user stays on the same page).

**Wrong code**:

```tsx
'use server';
import { redirect } from 'next/navigation';

export async function submit(formData: FormData) {
  await save(formData);
  redirect('/thank-you');  // Called inside try?
}
```

**Answer**:

**redirect()** throws a special error. If it’s inside a **try**, the **catch** might swallow it and the redirect never happens. **Fix**: Don’t catch the redirect; let it propagate. Or check for the redirect error and rethrow it in catch.

```tsx
try {
  await save(formData);
  redirect('/thank-you');
} catch (e) {
  if (e?.digest?.startsWith('NEXT_REDIRECT')) throw e;
  return { error: 'Failed' };
}
```

---

## Q13. (Advanced) You use next/router (useRouter, usePathname) in the Pages Router. What do you change when moving to the App Router?

**Answer**:

In the App Router, use **next/navigation** instead of **next/router**: **useRouter**, **usePathname**, **useSearchParams** come from **next/navigation**. The API is similar but not identical (e.g. **router.push** vs **router.push**; **router.refresh()** exists in **next/navigation**). Replace imports and fix any API differences (e.g. **query** is now **useSearchParams()**).

---

## Q14. (Advanced) How do you migrate a page that uses getServerSideProps and depends on request headers (e.g. cookie) to the App Router?

**Answer**:

Use the **headers()** (and **cookies()**) APIs from **next/headers** in the Server Component or layout. They are async in Next.js 15. So in the page or layout, **const cookieStore = await cookies()** and **const headersList = await headers()**, then read what you need. The page will be dynamic (no static generation at build time for that route).

---

## Q15. (Advanced) Next.js 16: What breaking or behavioral changes should you test when upgrading from 15?

**Answer**:

- **Turbopack** as default: Build and dev might behave slightly differently (e.g. plugin compatibility). Test build and runtime.
- **Caching**: Confirm **staleTimes** and Router Cache behavior if you rely on it; 16 may tune defaults.
- **params/searchParams** as Promise: Same as 15; ensure all usages **await**.
- **Changelog**: Check the official upgrade guide for any new deprecations or config changes (e.g. **experimental** flags promoted or removed).

---

## Q16. (Advanced) You have middleware that runs for both Pages and App routes. What should you watch when migrating routes to the App Router?

**Answer**:

Middleware runs for **all** matching requests regardless of router. When you move a route from **pages** to **app**, the **pathname** in **NextRequest** is the same (e.g. **/dashboard**). So URL-based logic (e.g. redirect by path) still works. Be careful if middleware **rewrites** to a path that used to be in **pages** and is now in **app**; the rewrite target might need to match the App Router structure (e.g. **/[locale]/dashboard** if you use locale). Test middleware after each migrated route.

---

## Q17. (Advanced) How do you run the Pages and App Router in parallel during migration and run E2E tests against both?

**Answer**:

Keep both **pages/** and **app/** in the repo. E2E tests can hit the same base URL; routes that were migrated return the same URL from the App Router. So run the full E2E suite; tests that hit migrated routes will hit the new implementation. Add or update tests for any route you migrate so behavior is locked. You don’t run "two apps"; it’s one app with two routers, so one test run is enough.

---

## Q18. (Advanced) Migrate a page that uses getStaticProps with revalidate (ISR) to the App Router with equivalent behavior.

**Answer**:

- **getStaticProps** with **revalidate: 60** → In the App Router, fetch in the page (or layout) with **next: { revalidate: 60 }** (or **tags** + **revalidateTag** for on-demand). Use **generateStaticParams** if you want the same set of paths pre-rendered at build time. The combination of **generateStaticParams** + **revalidate** in fetch gives ISR: static at build, revalidate after 60 seconds (or when you call revalidateTag).

---

## Q19. (Advanced) Production scenario: After migrating one page to the App Router, that page’s metadata (title) is wrong. The old page used next/head. What did you miss?

**Answer**:

In the App Router, **next/head** is not used. You must set metadata via the **metadata** export or **generateMetadata**. If you only migrated the body of the page and didn’t add **metadata** or **generateMetadata**, the root layout’s default title (or none) will show. **Fix**: Add **export const metadata** or **export async function generateMetadata** to that page (or its layout) with the correct title and description.

---

## Q20. (Advanced) Design a checklist for a full migration from Pages Router to App Router for a 50-page app.

**Answer**:

1. **Setup**: Add **app/layout.tsx** (html, body, providers). Add **app/globals.css** if needed.
2. **Metadata**: Plan **metadata** / **generateMetadata** for each route; replace **next/head** and **getStaticProps**-returned meta.
3. **Routes**: Migrate in order (e.g. by traffic or dependency): home → **app/page.tsx**; then top-level routes; then dynamic routes with **generateStaticParams** where applicable.
4. **Data**: Replace **getServerSideProps** / **getStaticProps** with Server Component fetch or data layer calls; use **cache()** or **revalidate** as needed.
5. **API routes**: Move **pages/api/*** to **app/api/*/route.ts**.
6. **Client code**: Replace **next/router** with **next/navigation**; ensure **params**/searchParams are **await**ed or **use()**d where they’re Promises.
7. **Middleware**: Keep; test after each batch of migrated routes.
8. **Tests**: Run E2E and key user flows; fix regressions.
9. **Cleanup**: Remove migrated files from **pages/**; eventually remove **pages/** and **_app**/**_document** if fully migrated.
10. **Docs**: Update README and deployment notes (e.g. any env or build assumptions).
