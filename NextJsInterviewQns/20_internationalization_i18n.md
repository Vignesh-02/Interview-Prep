# 20. Internationalization (i18n) in Next.js

## Topic Introduction

**Internationalization (i18n)** in Next.js 15/16 is not built into the App Router like it was in the Pages Router (`i18n` in `next.config.js`). Senior developers must implement locale detection, routing (sub-path or domain-based), and server/client translations using libraries such as **next-intl**, **next-i18next**, or custom middleware.

```
App Router i18n flow:
┌─────────────────────────────────────────────────────────────┐
│  Request: /fr/dashboard                                      │
│     │                                                        │
│     ▼                                                        │
│  middleware.ts                                                │
│     ├─ Detect locale (Accept-Language, cookie, path)          │
│     ├─ Rewrite to /dashboard (internal) with locale header   │
│     └─ Or: use sub-path /fr/ as-is                            │
│     │                                                        │
│     ▼                                                        │
│  app/[locale]/layout.tsx                                      │
│     ├─ Load messages for locale (server)                      │
│     └─ Provide locale + messages to tree                       │
│     │                                                        │
│     ▼                                                        │
│  app/[locale]/dashboard/page.tsx                              │
│     └─ useTranslations() or getTranslations()                  │
└─────────────────────────────────────────────────────────────┘
```

**Next.js 15 vs 16**: Both use the same App Router i18n patterns. Next.js 16 may improve caching of locale-specific static output. Always use **generateStaticParams** for `[locale]` when doing SSG with multiple locales.

**Why this matters for senior developers**: Incorrect i18n can break SEO (wrong hreflang, duplicate content), cause layout shifts (RTL), and hurt performance if messages are loaded on the client instead of the server. Production apps need locale in the URL for shareability and crawlers.

---

## Q1. (Beginner) How do you add multiple locales to a Next.js 15 App Router app using sub-path routing (e.g. /en, /fr)?

**Scenario**: Marketing wants the site available in English and French with URLs like `myapp.com/en/pricing` and `myapp.com/fr/pricing`.

**Answer**:

Use a dynamic `[locale]` segment and middleware to validate and redirect.

```tsx
// i18n/config.ts
export const locales = ['en', 'fr'] as const;
export const defaultLocale = 'en';
export type Locale = (typeof locales)[number];

// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { locales, defaultLocale } from './i18n/config';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const pathnameHasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (pathnameHasLocale) return NextResponse.next();

  // Redirect /dashboard → /en/dashboard (or locale from cookie/header)
  const locale = request.cookies.get('NEXT_LOCALE')?.value || defaultLocale;
  const validLocale = locales.includes(locale as any) ? locale : defaultLocale;
  request.nextUrl.pathname = `/${validLocale}${pathname}`;
  return NextResponse.redirect(request.nextUrl);
}

export const config = { matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'] };
```

```tsx
// app/[locale]/layout.tsx
import { locales, type Locale } from '@/i18n/config';

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export default function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  return (
    <html lang={(await params).locale}>
      <body>{children}</body>
    </html>
  );
}
```

---

## Q2. (Beginner) Where do you load translation messages in an App Router i18n setup — server or client?

**Scenario**: You're using `next-intl` and see a flash of untranslated keys on first load.

**Answer**:

Load messages **on the server** and pass them into the tree so the first paint is already translated. Avoid loading translations only in Client Components (e.g. with `useEffect`), which causes a flash.

```tsx
// app/[locale]/layout.tsx
import { getMessages, setRequestLocale } from 'next-intl/server';
import { NextIntlClientProvider } from 'next-intl';

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const messages = await getMessages(); // Server: load messages once per request

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

```tsx
// In any Client Component — no flash; messages already in provider
'use client';
import { useTranslations } from 'next-intl';

export function PricingCard() {
  const t = useTranslations('Pricing');
  return <h2>{t('title')}</h2>;
}
```

---

## Q3. (Beginner) How do you switch the current locale and persist the choice (e.g. for "Language" in the header)?

**Scenario**: User clicks "Français" in the header; the next page should be in French and the choice remembered.

**Answer**:

Update the path to the new locale and set a cookie so middleware can redirect non-prefixed URLs to the chosen locale.

```tsx
// components/LocaleSwitcher.tsx
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { locales, type Locale } from '@/i18n/config';

export function LocaleSwitcher() {
  const pathname = usePathname();
  const router = useRouter();

  function switchLocale(newLocale: Locale) {
    document.cookie = `NEXT_LOCALE=${newLocale};path=/;max-age=31536000`;
    // pathname is e.g. /en/dashboard → replace /en with /fr
    const segments = pathname.split('/');
    segments[1] = newLocale;
    router.push(segments.join('/'));
  }

  return (
    <select
      value={pathname.split('/')[1]}
      onChange={(e) => switchLocale(e.target.value as Locale)}
    >
      {locales.map((loc) => (
        <option key={loc} value={loc}>{loc === 'en' ? 'English' : 'Français'}</option>
      ))}
    </select>
  );
}
```

---

## Q4. (Beginner) How do you format dates and numbers per locale in Next.js?

**Scenario**: The dashboard shows "Revenue: $1,234.56" and "Last login: 3/15/2025". These should follow the user's locale (e.g. French: "1 234,56 €" and "15/03/2025").

**Answer**:

Use the **Intl** API (built into the browser and Node). No extra library is required.

```tsx
// lib/format.ts
export function formatCurrency(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: locale === 'fr' ? 'EUR' : 'USD',
  }).format(value);
}

export function formatDate(date: Date, locale: string) {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
  }).format(date);
}
```

```tsx
// app/[locale]/dashboard/page.tsx
import { formatCurrency, formatDate } from '@/lib/format';

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const revenue = 1234.56;
  const lastLogin = new Date();

  return (
    <div>
      <p>Revenue: {formatCurrency(revenue, locale)}</p>
      <p>Last login: {formatDate(lastLogin, locale)}</p>
    </div>
  );
}
```

---

## Q5. (Beginner) What is the difference between sub-path routing (/en, /fr) and domain-based routing (en.myapp.com, fr.myapp.com)?

**Answer**:

| Approach | Example | Pros | Cons |
|----------|---------|------|------|
| **Sub-path** | `/en/pricing`, `/fr/pricing` | Single deployment, simple DNS | Single domain; locale in path |
| **Domain** | `en.myapp.com`, `fr.myapp.com` | SEO per region, clean URLs | Multiple domains, SSL, more DNS |

**Sub-path** is common for one codebase and one domain. **Domain-based** is useful when you have separate brands or strong regional SEO (e.g. `myapp.fr` vs `myapp.com`). In Next.js you can detect locale in middleware from `request.nextUrl.hostname` and set a header or rewrite accordingly.

---

## Q6. (Intermediate) Implement middleware that detects locale from Accept-Language, cookie, and path, with a clear priority.

**Scenario**: Priority should be: 1) path (/fr/...), 2) cookie NEXT_LOCALE, 3) Accept-Language header, 4) default.

**Answer**:

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { locales, defaultLocale, type Locale } from '@/i18n/config';

function getLocaleFromPath(pathname: string): Locale | null {
  const segment = pathname.split('/')[1];
  return locales.includes(segment as Locale) ? (segment as Locale) : null;
}

function getLocaleFromAcceptLanguage(header: string | null): Locale {
  if (!header) return defaultLocale;
  // Accept-Language: fr-FR,fr;q=0.9,en;q=0.8
  const preferred = header.split(',')[0].split('-')[0].toLowerCase();
  return locales.includes(preferred as Locale) ? (preferred as Locale) : defaultLocale;
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const pathLocale = getLocaleFromPath(pathname);

  if (pathLocale) {
    // Path already has locale; optionally set cookie for next time
    const res = NextResponse.next();
    res.cookies.set('NEXT_LOCALE', pathLocale, { path: '/', maxAge: 31536000 });
    return res;
  }

  const cookieLocale = request.cookies.get('NEXT_LOCALE')?.value as Locale | undefined;
  const headerLocale = getLocaleFromAcceptLanguage(request.headers.get('accept-language'));

  const locale = (cookieLocale && locales.includes(cookieLocale))
    ? cookieLocale
    : headerLocale;

  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname}`;
  const res = NextResponse.redirect(url);
  res.cookies.set('NEXT_LOCALE', locale, { path: '/', maxAge: 31536000 });
  return res;
}

export const config = { matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'] };
```

---

## Q7. (Intermediate) How do you generate static pages for all locales at build time with Next.js 15?

**Scenario**: You have 10 static pages and 3 locales; you want 30 pre-rendered HTML files.

**Answer**:

Use **generateStaticParams** for both `[locale]` and any other dynamic segment so every combination is built.

```tsx
// app/[locale]/blog/[slug]/page.tsx
import { locales, type Locale } from '@/i18n/config';

export async function generateStaticParams() {
  const posts = await getPostSlugs(); // e.g. ['hello', 'world']
  const params: { locale: string; slug: string }[] = [];
  for (const locale of locales) {
    for (const slug of posts) {
      params.push({ locale, slug });
    }
  }
  return params;
}

export default async function BlogPost({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  const post = await getPost(slug, locale);
  return <article>{post.content}</article>;
}
```

---

## Q8. (Intermediate) How do you set locale-specific metadata (title, description) and hreflang for SEO?

**Scenario**: Google should index both /en/pricing and /fr/pricing with correct alternate links.

**Answer**:

Use **generateMetadata** and add **alternates.languages** for hreflang.

```tsx
// app/[locale]/pricing/page.tsx
import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { locales } from '@/i18n/config';

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'Pricing' });

  const baseUrl = 'https://myapp.com';
  const languageAlternates = Object.fromEntries(
    locales.map((loc) => [loc, `${baseUrl}/${loc}/pricing`])
  );

  return {
    title: t('title'),
    description: t('description'),
    alternates: {
      canonical: `${baseUrl}/${locale}/pricing`,
      languages: languageAlternates,
    },
  };
}

export default async function PricingPage({ params }: Props) {
  const { locale } = await params;
  return <div>...</div>;
}
```

---

## Q9. (Intermediate) Support RTL (right-to-left) for a locale like Arabic. What do you need to change?

**Scenario**: Adding `ar` as a locale; layout and text must flip.

**Answer**:

Set `dir="rtl"` on `<html>` and use logical CSS (e.g. `margin-inline-start` instead of `margin-left`) or a class that flips when `dir="rtl"`.

```tsx
// i18n/config.ts
export const locales = ['en', 'fr', 'ar'] as const;
export const rtlLocales: string[] = ['ar'];

// app/[locale]/layout.tsx
export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dir = rtlLocales.includes(locale) ? 'rtl' : 'ltr';

  return (
    <html lang={locale} dir={dir}>
      <body className={dir === 'rtl' ? 'font-arabic' : ''}>{children}</body>
    </html>
  );
}
```

```css
/* Use logical properties so RTL flips automatically */
.card { margin-inline-start: 1rem; }
```

---

## Q10. (Intermediate) How do you handle pluralization (e.g. "1 item" vs "5 items") with next-intl?

**Scenario**: You need "No items", "1 item", "2 items" in every locale.

**Answer**:

Use ICU plural rules in your message files and pass a count.

```json
// messages/en.json
{
  "Cart": {
    "items": "{count, plural, =0 {No items} one {# item} other {# items}}"
  }
}
```

```tsx
const t = useTranslations('Cart');
t('items', { count: 0 });  // "No items"
t('items', { count: 1 });  // "1 item"
t('items', { count: 5 });  // "5 items"
```

---

## Q11. (Intermediate) Compare next-intl and next-i18next in the App Router. Which would you choose for a new project?

**Answer**:

| | next-intl | next-i18next |
|--|-----------|----------------|
| App Router | First-class (async server components) | Requires adapter / app dir support |
| Server Components | Yes (getTranslations) | Limited; originally Pages-focused |
| Bundle size | Smaller | Larger (i18next) |
| Learning curve | Simpler for App Router | Familiar if coming from i18next |

**Recommendation for App Router**: **next-intl** is designed for the App Router and Server Components (async, no context needed on server). Use next-i18next if you are already on it and have a migration path for App Router.

---

## Q12. (Intermediate) Production scenario: Users report wrong language after login. You use cookie NEXT_LOCALE and middleware. What could be wrong?

**Scenario**: After login, the app redirects to /dashboard and shows English even though the user chose French and cookie is set.

**Answer**:

Common causes:

1. **Redirect after login goes to path without locale**  
   Fix: Redirect to `/${locale}/dashboard` (or use middleware to always add locale so `/dashboard` becomes `/fr/dashboard`).

2. **Cookie not set on the same domain/path**  
   Fix: Set cookie with `path: '/'` and same `domain` as the app.

3. **Server Component reads locale from params but redirect URL had no locale**  
   Fix: Ensure login redirect uses the current locale from the request (e.g. from cookie in middleware and rewrite).

```tsx
// Correct: after login, redirect to locale-prefixed path
const locale = getLocaleFromCookie(request);
redirect(`/${locale}/dashboard`);
```

---

## Q13. (Advanced) Find the bug: Middleware runs on every request and calls an external API to resolve the user's country and set locale. Pages are slow. Fix it.

**Scenario**: Code below; production is slow and the API has rate limits.

**Wrong code**:

```tsx
// middleware.ts
export async function middleware(request: NextRequest) {
  const ip = request.ip ?? request.headers.get('x-forwarded-for');
  const res = await fetch(`https://api.geo.com/country?ip=${ip}`);
  const { country } = await res.json();
  const locale = country === 'FR' ? 'fr' : 'en';
  request.nextUrl.pathname = `/${locale}${request.nextUrl.pathname}`;
  return NextResponse.rewrite(request.nextUrl);
}
```

**Answer**:

Calling an external API in middleware on every request adds latency and can hit rate limits. Prefer path or cookie first; only use geo as a one-time hint and cache it.

**Fix**:

```tsx
// 1) Prefer path; then cookie; then optional geo (with cache)
export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (pathname.startsWith('/en/') || pathname.startsWith('/fr/')) return NextResponse.next();

  let locale = request.cookies.get('NEXT_LOCALE')?.value;

  if (!locale) {
    // Optional: geo only when no cookie, and cache by IP (e.g. in Vercel KV or Edge Config)
    const ip = request.ip ?? request.headers.get('x-forwarded-for') ?? '';
    const cacheKey = `geo:${ip}`;
    // ... get from edge cache/KV; if miss, call API once and set cache TTL 24h
    locale = await getLocaleFromGeoOrCache(cacheKey, ip);
  }

  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname}`;
  const res = NextResponse.redirect(url);
  res.cookies.set('NEXT_LOCALE', locale, { path: '/', maxAge: 31536000 });
  return res;
}
```

---

## Q14. (Advanced) Design an i18n setup that works with Next.js 16 caching: static pages per locale, on-demand revalidation per locale.

**Scenario**: You have 50 pages × 5 locales. You want to revalidate only "French blog" when the CMS updates French content.

**Answer**:

- Use **generateStaticParams** for `[locale]` (and other segments) so each locale gets its own static output.
- Tag fetches by locale (and entity) and call **revalidateTag** when CMS updates that locale.

```tsx
// app/[locale]/blog/[slug]/page.tsx
export default async function BlogPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  const post = await fetch(`https://cms.example.com/posts/${locale}/${slug}`, {
    next: { tags: [`blog-${locale}`, `blog-${locale}-${slug}`] },
  }).then((r) => r.json());
  return <article>{post.content}</article>;
}

// In a webhook or Server Action when CMS updates French content:
import { revalidateTag } from 'next/cache';
revalidateTag('blog-fr');
```

---

## Q15. (Advanced) How do you run E2E tests for multiple locales (e.g. Playwright) without duplicating tests?

**Scenario**: You have 100 Playwright tests; you need them to run for both en and fr.

**Answer**:

Use a project or loop over locales and set baseURL or path prefix so tests are parameterized by locale.

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

const locales = ['en', 'fr'];

export default defineConfig({
  projects: locales.flatMap((locale) => [
    {
      name: `chromium-${locale}`,
      use: {
        ...devices['Desktop Chrome'],
        baseURL: `http://localhost:3000/${locale}`,
        locale: locale === 'fr' ? 'fr-FR' : 'en-US',
      },
    },
  ]),
});
```

```ts
// tests/pricing.spec.ts
import { test, expect } from '@playwright/test';

test('pricing page has correct title', async ({ page, baseURL }) => {
  await page.goto('/pricing');
  await expect(page).toHaveTitle(/Pricing|Tarifs/);
});
```

---

## Q16. (Advanced) Implement a "find the bug" fix: Translations work in Server Components but are undefined in a Client Component that receives `locale` as a prop.

**Wrong code**:

```tsx
// app/[locale]/dashboard/page.tsx
export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return (
    <div>
      <ServerPart />
      <ClientPart locale={locale} />
    </div>
  );
}

// components/ClientPart.tsx
'use client';
import { useTranslations } from 'next-intl';

export function ClientPart({ locale }: { locale: string }) {
  const t = useTranslations('Dashboard');
  return <span>{t('title')}</span>; // t('title') is undefined
}
```

**Answer**:

`useTranslations` in next-intl relies on **NextIntlClientProvider** having **messages** (and optionally locale) in the tree. Passing only `locale` to a Client Component does not provide messages. Messages must be loaded in the server layout and passed to the provider; the Client Component then uses the same provider.

**Fix**: Ensure the root layout (or locale layout) loads messages and wraps the app with `NextIntlClientProvider` (see Q2). Do not pass only `locale` and expect translations to work in the client; the provider already has locale from the server. If you need locale in the client for other reasons (e.g. formatting), pass it as a prop, but translations will work once the provider has messages.

---

## Q17. (Advanced) How does Next.js 16 differ from 15 for i18n or locale-aware caching?

**Answer**:

- **Next.js 15**: No built-in i18n in App Router; caching is opt-in (fetch not cached by default). Static params for `[locale]` work as today.
- **Next.js 16**: Turbopack default; no fundamental change to i18n. Possible improvements: faster builds when using many `generateStaticParams` (locale × pages), and more predictable cache keys for locale-prefixed routes.

When comparing 15 vs 16, focus on **build performance** and **cache behavior** (e.g. `staleTimes`) rather than a new i18n API.

---

## Q18. (Advanced) Production scenario: You use `next-intl` with middleware that rewrites `/` to `/en`. How do you avoid duplicate content (same content on / and /en) for SEO?

**Scenario**: Google indexes both `/` and `/en` with the same content; duplicate content penalty risk.

**Answer**:

- **Redirect instead of rewrite**: In middleware, **redirect** `/` to `/en` (or to the resolved locale) with a 302/301 so there is only one canonical URL.
- **Canonical and hreflang**: Set `alternates.canonical` to the locale-prefixed URL (e.g. `https://myapp.com/en`) and provide `alternates.languages` so search engines know which URL is for which language.
- **Sitemap**: Include only locale-prefixed URLs (e.g. `/en`, `/fr`) in the sitemap, not the root `/`.

---

## Q19. (Advanced) How do you lazy-load translation namespaces in a Client Component to reduce initial JS without causing layout shift?

**Scenario**: Dashboard has 5 namespaces; you want to load only "Dashboard" first and "Reports" when the user opens the Reports tab.

**Answer**:

With **next-intl**, you can pass only the namespaces you need to the provider (server) and load more on the client. To avoid layout shift, reserve space (skeleton) or load the namespace before rendering the tab content.

```tsx
// Server layout provides base namespaces
<NextIntlClientProvider messages={baseMessages}>

// Client: load extra namespace when tab is opened
'use client';
import { useTranslations } from 'next-intl';
import { useState, useEffect } from 'react';

function ReportsTab() {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    import('@/messages/reports.json').then((msgs) => {
      // next-intl: merge or set messages for 'Reports' namespace
      setReady(true);
    });
  }, []);
  if (!ready) return <ReportsSkeleton />;
  return <ReportsContent />;
}
```

Alternatively, use a single bundle with all namespaces but code-split the component that uses "Reports" so the namespace is loaded with the chunk (no separate lazy load of JSON). The key is to show a stable placeholder until the translation is available.

---

## Q20. (Advanced) Implement a single middleware that handles: locale detection, auth redirect for /dashboard, and A/B test cookie. Keep it fast.

**Scenario**: One middleware must 1) set locale and rewrite to /[locale]/..., 2) redirect unauthenticated users from /dashboard to /login, 3) set an A/B cookie if missing. All with minimal latency.

**Answer**:

- Do **no** async I/O in middleware for the common path (no DB, no external API). Use only cookie/header/path.
- Order: first check path (locale prefix); then auth (cookie or header); then A/B cookie; then locale redirect.

```tsx
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { locales, defaultLocale } from '@/i18n/config';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const res = NextResponse.next();

  // 1) A/B cookie (cheap)
  if (!request.cookies.has('ab_variant')) {
    res.cookies.set('ab_variant', Math.random() < 0.5 ? 'A' : 'B', {
      path: '/',
      maxAge: 2592000,
    });
  }

  // 2) Auth: redirect /dashboard to /login if no session (cookie-only check)
  if (pathname.includes('/dashboard') && !request.cookies.has('session')) {
    const locale = pathname.split('/')[1];
    const loginUrl = new URL(`/${locales.includes(locale as any) ? locale : defaultLocale}/login`, request.url);
    return NextResponse.redirect(loginUrl);
  }

  // 3) Locale: if no locale in path, redirect to /[locale]/...
  const hasLocale = locales.some((l) => pathname === `/${l}` || pathname.startsWith(`/${l}/`));
  if (!hasLocale) {
    const locale = request.cookies.get('NEXT_LOCALE')?.value || defaultLocale;
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}${pathname}`;
    res.headers.set('x-middleware-rewrite', url.pathname);
    return NextResponse.redirect(url);
  }

  return res;
}
```

Keep auth as a lightweight cookie check; do full session validation in the dashboard layout or API.
