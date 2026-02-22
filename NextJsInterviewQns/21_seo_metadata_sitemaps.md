# 21. SEO, Metadata & Sitemaps

## Topic Introduction

**SEO in Next.js 15/16** is driven by the **Metadata API** (App Router), **generateMetadata**, **sitemaps**, **robots.txt**, and correct use of semantic HTML and Open Graph. Server Components and static generation give crawlers fast, pre-rendered HTML. Senior developers must ensure canonical URLs, hreflang for i18n, and avoid common pitfalls (duplicate meta, client-only content, slow TTI).

```
SEO flow in App Router:
┌────────────────────────────────────────────────────────────┐
│  Crawler requests /blog/my-post                              │
│     │                                                       │
│     ▼                                                       │
│  generateMetadata({ params }) → title, description,          │
│    openGraph, twitter, alternates.canonical,                 │
│    alternates.languages (hreflang)                           │
│     │                                                       │
│     ▼                                                       │
│  Page component renders (Server Component) → full HTML      │
│  (no "content only after JS" — crawlers see content)         │
│     │                                                       │
│     ▼                                                       │
│  Sitemap (app/sitemap.ts) → lists all public URLs           │
│  Robots (app/robots.ts) → Allow/Disallow                    │
└────────────────────────────────────────────────────────────┘
```

**Next.js 15 vs 16**: Same Metadata API. Next.js 16 may improve caching of metadata for static routes. Always use **metadataBase** for correct absolute URLs in OG images.

---

## Q1. (Beginner) How do you set the page title and description in the App Router?

**Scenario**: Every page should have a unique `<title>` and `<meta name="description">`.

**Answer**:

Export a **metadata** object (static) or **generateMetadata** (dynamic) from the page or layout.

```tsx
// app/about/page.tsx — static
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About Us | MyApp',
  description: 'Learn about our team and mission.',
};

export default function AboutPage() {
  return <main><h1>About Us</h1></main>;
}
```

```tsx
// app/blog/[slug]/page.tsx — dynamic
import type { Metadata } from 'next';

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(slug);
  return {
    title: `${post.title} | MyApp Blog`,
    description: post.excerpt,
  };
}

export default async function BlogPost({ params }: Props) {
  const post = await getPost((await params).slug);
  return <article>{post.content}</article>;
}
```

---

## Q2. (Beginner) What is metadataBase and why is it important for Open Graph images?

**Scenario**: Social shares show a broken image or wrong URL for OG image.

**Answer**:

**metadataBase** is the base URL used to resolve **relative** URLs in metadata (e.g. `openGraph.images: ['/og.png']`). Without it, Next.js cannot build an absolute URL for OG image, so platforms may fail to load it.

```tsx
// app/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  metadataBase: new URL('https://myapp.com'),
  title: { template: '%s | MyApp', default: 'MyApp' },
  openGraph: {
    images: ['/og-default.png'], // Resolves to https://myapp.com/og-default.png
  },
};
```

```tsx
// app/blog/[slug]/page.tsx
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPost((await params).slug);
  return {
    openGraph: {
      images: [post.ogImageUrl], // Prefer absolute URL, or path relative to metadataBase
    },
  };
}
```

---

## Q3. (Beginner) How do you add a sitemap in Next.js 15?

**Scenario**: You want a sitemap at /sitemap.xml for all public pages.

**Answer**:

Create **app/sitemap.ts** (or **sitemap.xml/route.ts**). Return an array of URL objects.

```tsx
// app/sitemap.ts
import { MetadataRoute } from 'next';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://myapp.com';
  const posts = await getPostSlugs();

  return [
    { url: baseUrl, lastModified: new Date(), changeFrequency: 'daily', priority: 1 },
    { url: `${baseUrl}/about`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
    ...posts.map((slug) => ({
      url: `${baseUrl}/blog/${slug}`,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: 0.6,
    })),
  ];
}
```

---

## Q4. (Beginner) How do you add robots.txt in the App Router?

**Scenario**: Allow all crawlers but disallow /api and /admin.

**Answer**:

Create **app/robots.ts**.

```tsx
// app/robots.ts
import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: '*', allow: '/', disallow: ['/api/', '/admin/'] },
      { userAgent: 'Googlebot', allow: '/', disallow: ['/api/', '/admin/'] },
    ],
    sitemap: 'https://myapp.com/sitemap.xml',
  };
}
```

---

## Q5. (Beginner) What is the difference between static metadata and generateMetadata?

**Answer**:

| | Static `metadata` | `generateMetadata` |
|--|-------------------|---------------------|
| When | Known at build time | Depends on params/searchParams/data |
| Use for | Fixed pages (about, pricing) | Dynamic pages (blog slug, product id) |
| Async | No | Yes (async function) |
| Data | Literal object | Fetched (e.g. from CMS/DB) |

Use **generateMetadata** whenever the title/description/OG depend on the request (route params or data).

---

## Q6. (Intermediate) Implement full Open Graph and Twitter Card metadata for a blog post page, including OG image and article:published_time.

**Scenario**: Social shares should show correct image, title, description, and publish time.

**Answer**:

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from 'next';

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(slug);

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: 'article',
      publishedTime: post.publishedAt,
      authors: [post.author.name],
      images: [
        {
          url: post.ogImage ?? '/og-default.png',
          width: 1200,
          height: 630,
          alt: post.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description: post.excerpt,
      images: [post.ogImage ?? '/og-default.png'],
    },
    alternates: {
      canonical: `https://myapp.com/blog/${slug}`,
    },
  };
}

export default async function BlogPostPage({ params }: Props) {
  const post = await getPost((await params).slug);
  return <article>{post.content}</article>;
}
```

Ensure **metadataBase** is set in root layout so relative image paths resolve.

---

## Q7. (Intermediate) How do you generate a dynamic OG image per page (e.g. with @vercel/og or next/og)?

**Scenario**: Blog post OG image should show title and author (image generated at request time).

**Answer**:

Use **ImageResponse** from `next/og` in a **Route Handler** and reference it in metadata as the page URL with special query (or use the route path).

```tsx
// app/blog/[slug]/opengraph-image.tsx (or opengraph-image.tsx that reads params)
import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const alt = 'Blog post';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

type Props = { params: Promise<{ slug: string }> };

export default async function Image({ params }: Props) {
  const { slug } = await params;
  const post = await getPost(slug);

  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 48,
          background: 'linear-gradient(#111, #333)',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
        }}
      >
        <h1>{post.title}</h1>
        <p>{post.author.name}</p>
      </div>
    ),
    { ...size }
  );
}
```

Next.js will automatically use this for the page’s Open Graph image when the route is requested with the right format.

---

## Q8. (Intermediate) Production scenario: Google shows the wrong title for a dynamic page. What could be wrong?

**Scenario**: generateMetadata returns the correct title in dev, but Google shows a generic title.

**Answer**:

Possible causes:

1. **Page is client-rendered only** — Crawlers may not execute JS. Ensure the page is Server Rendered or statically generated so the title is in the initial HTML.
2. **Title in a Client Component** — `<title>` must be set by the Metadata API or layout/page (server). Do not set document title only in `useEffect` for SEO.
3. **Caching** — Old HTML cached by CDN or browser. Set cache headers or revalidate so crawlers get fresh HTML.
4. **Wrong canonical** — If canonical points to another URL, Google may prefer that page’s title.
5. **generateMetadata not awaited / error** — If it throws or returns undefined, fallback metadata is used. Check logs and ensure it returns a valid object.

---

## Q9. (Intermediate) How do you avoid duplicate content when you have both www and non-www (or multiple domains)?

**Scenario**: myapp.com and www.myapp.com both serve the same content; you want one canonical.

**Answer**:

- **Redirect** one to the other in middleware or at the host (e.g. redirect www → non-www).
- Set **metadataBase** and **canonical** to the single canonical origin (e.g. `https://myapp.com`).
- In **sitemap**, list only canonical URLs. In **robots.txt**, use the same canonical base.

```tsx
// middleware.ts
export function middleware(request: NextRequest) {
  const host = request.nextUrl.host;
  if (host.startsWith('www.')) {
    const url = request.nextUrl.clone();
    url.host = host.replace('www.', '');
    return NextResponse.redirect(url, 301);
  }
  return NextResponse.next();
}
```

---

## Q10. (Intermediate) Implement a sitemap that includes all locales (e.g. /en/blog/1, /fr/blog/1) with correct lastModified per page.

**Scenario**: Multi-locale app; sitemap must list each URL once per locale.

**Answer**:

```tsx
// app/sitemap.ts
import { MetadataRoute } from 'next';
import { locales } from '@/i18n/config';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://myapp.com';
  const posts = await getPostSlugs();
  const entries: MetadataRoute.Sitemap = [];

  for (const locale of locales) {
    entries.push({
      url: `${baseUrl}/${locale}`,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    });
    for (const slug of posts) {
      const lastMod = await getPostLastModified(slug, locale);
      entries.push({
        url: `${baseUrl}/${locale}/blog/${slug}`,
        lastModified: lastMod,
        changeFrequency: 'weekly',
        priority: 0.6,
      });
    }
  }
  return entries;
}
```

---

## Q11. (Intermediate) How do you add JSON-LD (structured data) for an article or product in Next.js?

**Scenario**: Google should understand the page as an Article or Product for rich results.

**Answer**:

Inject a `<script type="application/ld+json">` in the page or layout with the structured data object. Prefer Server Component so it’s in the initial HTML.

```tsx
// app/blog/[slug]/page.tsx
export default async function BlogPostPage({ params }: Props) {
  const post = await getPost((await params).slug);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: post.title,
    description: post.excerpt,
    image: post.ogImage,
    datePublished: post.publishedAt,
    dateModified: post.updatedAt,
    author: {
      '@type': 'Person',
      name: post.author.name,
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <article>{post.content}</article>
    </>
  );
}
```

Escape the JSON so it’s safe (no user-controlled content without escaping), or use a library that outputs safe JSON-LD.

---

## Q12. (Intermediate) Find the bug: Metadata is correct in dev but production OG image is 404.

**Wrong setup**:

```tsx
// app/layout.tsx
export const metadata = {
  openGraph: { images: ['/og.png'] },
};

// app/blog/[slug]/page.tsx
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPost((await params).slug);
  return {
    openGraph: { images: [post.image] }, // post.image is relative: "/uploads/og-1.jpg"
  };
}
```

**Answer**:

Relative paths for OG images are resolved against **metadataBase**. If **metadataBase** is not set, Next.js may resolve them against the request host (which can be wrong in serverless or behind a proxy). Also, if `post.image` is a path like `/uploads/og-1.jpg`, ensure that URL is publicly reachable (e.g. served from the same origin or a CDN).

**Fix**:

```tsx
// app/layout.tsx
export const metadata: Metadata = {
  metadataBase: new URL('https://myapp.com'),
  // ...
};
```

And ensure `/uploads/*` is served (e.g. from `public/` or your CDN). For dynamic images, use absolute URLs: `post.image.startsWith('http') ? post.image : new URL(post.image, process.env.NEXT_PUBLIC_BASE_URL).toString()`.

---

## Q13. (Advanced) How does Next.js 16 handle metadata caching compared to 15? Does generateMetadata get deduplicated with page data fetch?

**Answer**:

In both 15 and 16, **fetch** calls inside **generateMetadata** are part of the same request as the page; Next.js **request memoization** deduplicates identical `fetch` calls. So if the page and generateMetadata both call `getPost(slug)`, only one request runs. Next.js 16 does not change this behavior significantly; the main difference is Turbopack and default cache behavior (e.g. fetch not cached by default in 15+). For static generation, both params and metadata are computed at build time when using generateStaticParams.

---

## Q14. (Advanced) Production scenario: A client-rendered dashboard is not indexed; you need key landing sections to be crawlable. How do you fix it without making the whole page server-rendered?

**Scenario**: Dashboard is behind auth but you want the “marketing” part (hero, features) to be in the initial HTML for SEO.

**Answer**:

- **Server-render the public shell**: Use a layout or page that is a Server Component and renders the hero/features (and any shared meta). Fetch minimal data needed for meta and above-the-fold content on the server.
- **Client-only dashboard**: Wrap the authenticated dashboard in a Client Component that mounts after auth check; that part can remain client-rendered. Crawlers will see the server-rendered shell and meta; the interactive dashboard may not be indexed, which is often acceptable for private UX.
- **Alternative**: Use a separate public landing route (e.g. `/` or `/home`) that is fully server-rendered and links to `/dashboard`; keep `/dashboard` behind auth and optionally noindex if it’s not meant to be indexed.

---

## Q15. (Advanced) Implement a sitemap index (sitemap.xml that links to sitemap-0.xml, sitemap-1.xml) for 100k URLs.

**Scenario**: Single sitemap has a 50k URL limit; you need a sitemap index.

**Answer**:

Return a **sitemap index** from **app/sitemap.ts** by returning the special format (array of sitemap objects with `url` and optional `lastModified`). Next.js allows returning either URL entries or child sitemap references.

```tsx
// app/sitemap.ts
import { MetadataRoute } from 'next';

const BASE = 'https://myapp.com';
const SITEMAP_SIZE = 50_000;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const total = await getTotalPostCount();
  const pages = Math.ceil(total / SITEMAP_SIZE);

  // Return sitemap index
  const index: MetadataRoute.Sitemap = [];
  for (let i = 0; i < pages; i++) {
    index.push({
      url: `${BASE}/sitemap-${i}.xml`,
      lastModified: new Date(),
    });
  }
  return index;
}
```

Then add **app/sitemap-0.xml/route.ts** (or dynamic route) that returns XML for URLs in range `[0, 50000)`, etc. Alternatively use a single **sitemap.ts** that returns only the first 50k and add **sitemap-[n].ts** files for other chunks; or use the Route Handler approach to serve `sitemap-0.xml` that lists URLs. (Next.js 15 docs support multiple sitemaps by returning different structures; for 100k URLs, splitting into multiple sitemap files and a sitemap index is the standard approach.)

---

## Q16. (Advanced) How do you noindex a route (e.g. /dashboard) while keeping it crawlable for authenticated preview? Should you use robots meta or X-Robots-Tag?

**Answer**:

- **robots meta tag**: Add `robots: { index: false, follow: true }` in that route’s metadata. Crawlers that respect the tag will not index the page but may follow links.
- **X-Robots-Tag header**: In middleware or a route handler for that path, set `X-Robots-Tag: noindex`. Useful for API responses or when you don’t want to render a full page for bots.
- **robots.txt disallow**: Use `disallow: /dashboard` only if you want to block crawling entirely (no indexing and no following links from that path). For “don’t index but allow links to be followed,” prefer noindex meta or header and do not disallow in robots.txt.

---

## Q17. (Advanced) Find the bug: generateMetadata throws "Dynamic server usage" when using cookies() to personalize meta.

**Wrong code**:

```tsx
// app/dashboard/page.tsx
import { cookies } from 'next/headers';

export async function generateMetadata() {
  const cookieStore = await cookies();
  const theme = cookieStore.get('theme')?.value ?? 'light';
  return { title: `Dashboard (${theme})` };
}
```

**Scenario**: Build or static export fails or warns about dynamic usage.

**Answer**:

Calling **cookies()** (or **headers()**, **searchParams** in some cases) makes the route **dynamic**, so the page is not statically generated. That’s valid if you want per-request metadata. The “Dynamic server usage” error in some setups (e.g. static export) happens because static export does not support server-only APIs. **Fix**: If you need static export, do not use cookies/headers in generateMetadata for that route. If you’re on Node/serverless (no static export), using cookies() in generateMetadata is fine and simply opts the route into dynamic rendering.

---

## Q18. (Advanced) Compare Next.js 15 and 16 behavior for metadata and sitemap when using ISR (revalidate) on a page.

**Answer**:

- **Next.js 15**: With `revalidate`, the page (and its metadata) can be revalidated on the interval or on-demand. generateMetadata runs when the page is (re)generated; metadata is part of the cached RSC payload.
- **Next.js 16**: Same idea. Turbopack does not change metadata semantics. Caching and revalidation behavior for metadata follow the same rules as the page. When you revalidatePath or revalidateTag, the page and its metadata are regenerated together.

---

## Q19. (Advanced) How do you ensure crawlers see the correct hreflang when using middleware that rewrites /fr to an internal path? Does the crawler see /fr or the rewritten path?

**Scenario**: Middleware rewrites request from `/fr/pricing` to internal `/pricing` with locale header. You want hreflang to point to `https://myapp.com/fr/pricing`.

**Answer**:

The crawler sees the **requested** URL (e.g. `https://myapp.com/fr/pricing`), not the internal rewrite. So in generateMetadata you must know the **public** locale path. When you use a dynamic segment like `[locale]`, the params contain `locale: 'fr'`, so your canonical and hreflang should use that. Generate metadata from the same `params` (and optionally `searchParams`) so that alternates.languages and canonical use the public URL pattern (e.g. `/${locale}/pricing`). Do not use the internal path in metadata; use the path the user/crawler requested, which in a proper setup is the same as the path with `[locale]` in it.

---

## Q20. (Advanced) Design a metadata strategy for a large e-commerce site: category pages, product pages, and programmatic OG images. Include caching and revalidation.

**Answer**:

- **Category pages**: generateMetadata with `params.category`. Tag data fetches with `category-${slug}`. On-demand revalidate when category name/description changes. Use generateStaticParams for top categories; dynamicParams for long tail.
- **Product pages**: generateMetadata with `params.productId`. Programmatic OG image via **opengraph-image.tsx** (or API route) using product name, price, image. Cache OG image generation (e.g. revalidate 3600 or on product update via tag). Canonical URL = product URL; avoid duplicate content from query params (e.g. ?ref=) by canonicalizing.
- **Caching**: Use fetch with `next: { tags: ['product-${id}'] }` for product data; revalidateTag when product is updated. Metadata is part of the same request, so it stays consistent with page data.
- **Sitemap**: Generate sitemap from DB/cms; include category and product URLs with lastModified. Split into multiple sitemaps if > 50k URLs; serve sitemap index at /sitemap.xml.
