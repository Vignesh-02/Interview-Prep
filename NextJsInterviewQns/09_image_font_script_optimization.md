# 9. Image, Font & Script Optimization

## Topic Introduction

Next.js provides **three dedicated optimization components** — `next/image`, `next/font`, and `next/script` — that directly address Core Web Vitals (LCP, CLS, FID/INP). These aren't just convenience wrappers; they implement Google's recommended loading strategies automatically, making production-grade performance the default rather than the exception.

```
┌──────────────────────────────────────────────────────────────────┐
│                  Next.js Optimization Stack                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  next/image   │  │  next/font   │  │    next/script       │   │
│  │              │  │              │  │                      │   │
│  │ • Auto WebP/ │  │ • Zero-CLS  │  │ • beforeInteractive  │   │
│  │   AVIF       │  │ • Self-host │  │ • afterInteractive   │   │
│  │ • Lazy load  │  │ • Subsetting│  │ • lazyOnload         │   │
│  │ • Responsive │  │ • Variable  │  │ • worker (off-main)  │   │
│  │ • Blur hash  │  │   fonts     │  │                      │   │
│  │ • CDN-ready  │  │ • Preload   │  │                      │   │
│  └──────┬───────┘  └──────┬──────┘  └──────────┬───────────┘   │
│         │                 │                     │               │
│         ▼                 ▼                     ▼               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Core Web Vitals Impact                      │    │
│  │  LCP ◄── Image priority + preload + responsive sizes    │    │
│  │  CLS ◄── width/height required + font-display: swap     │    │
│  │  INP ◄── Lazy loading + worker scripts + font subsetting│    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

**Image Optimization Pipeline**:

```
Request: /image.jpg?w=640&q=75
         │
         ▼
┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│  next/image      │────▶│  Image Optimizer  │────▶│  CDN / Cache  │
│  Component       │     │  (sharp/squoosh)  │     │               │
│                  │     │                   │     │  • Browser    │
│  • width/height  │     │  • Resize         │     │  • Edge       │
│  • sizes attr    │     │  • Format convert │     │  • minimumCTL │
│  • priority      │     │  • Quality adjust │     │               │
│  • placeholder   │     │  • AVIF > WebP >  │     │  Cache-Control│
│  • loader        │     │    JPEG fallback  │     │  headers      │
└─────────────────┘     └──────────────────┘     └───────────────┘
```

**Font Loading Strategy**:

```
Build Time                          Runtime
┌──────────────────┐    ┌────────────────────────────────┐
│  next/font        │    │  Browser                        │
│                   │    │                                 │
│  1. Download font │    │  1. CSS with font-face injected │
│  2. Self-host     │───▶│  2. Font file served from /_next│
│  3. Generate CSS  │    │  3. No external requests!       │
│  4. Create        │    │  4. Zero layout shift           │
│     className     │    │  5. Optimal font-display        │
└──────────────────┘    └────────────────────────────────┘
```

**Key Next.js 15/16 Updates**:
- `next/image` now uses `fetchPriority="high"` instead of just `loading="eager"` for priority images
- `next/font` has improved tree-shaking and subsets by default
- `next/script` supports the `worker` strategy via Partytown for true off-main-thread execution
- Image component supports `overrideSrc` prop for art-direction patterns
- Built-in AVIF support is default when the browser supports it
- `sizes` prop can now use viewport-based responsive logic with improved TypeScript types

---

## Q1. (Beginner) What is `next/image` and why should you always use it instead of a raw `<img>` tag in Next.js?

**Scenario**: A junior developer on your team is adding product images to an e-commerce site using plain `<img>` tags. The Lighthouse score drops significantly.

**Answer**:

`next/image` is Next.js's built-in image optimization component that automatically handles resizing, format conversion, lazy loading, and responsive image generation. Using raw `<img>` tags means you miss all of these optimizations and directly hurt Core Web Vitals.

| Feature | Raw `<img>` | `next/image` |
|---------|-------------|--------------|
| Lazy loading | Manual (need `loading="lazy"`) | Automatic (default) |
| Format conversion | Manual (need build pipeline) | Auto AVIF/WebP |
| Responsive sizes | Manual `srcset` | Auto `srcset` generation |
| CLS prevention | Must set width/height manually | Required width/height props |
| Priority loading | Manual `fetchpriority` | `priority` prop |
| Blur placeholder | Not built-in | `placeholder="blur"` |
| CDN optimization | Manual setup | Built-in image optimizer |

```tsx
// ❌ BAD — Raw <img> tag (no optimization)
export default function ProductCard({ product }: { product: Product }) {
  return (
    <div>
      <img src={product.imageUrl} alt={product.name} />
      <h2>{product.name}</h2>
      <p>${product.price}</p>
    </div>
  );
}

// ✅ GOOD — next/image with proper optimization
import Image from 'next/image';

export default function ProductCard({ product }: { product: Product }) {
  return (
    <div className="relative">
      <Image
        src={product.imageUrl}
        alt={product.name}
        width={400}
        height={300}
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        placeholder="blur"
        blurDataURL={product.blurHash}
        className="rounded-lg object-cover"
      />
      <h2>{product.name}</h2>
      <p>${product.price}</p>
    </div>
  );
}
```

**What happens under the hood when `next/image` renders**:

```
Browser requests: /_next/image?url=%2Fproducts%2Fshoe.jpg&w=640&q=75
                           │
                           ▼
              ┌─────────────────────────┐
              │  Next.js Image Optimizer │
              │  1. Check cache          │
              │  2. Fetch original       │
              │  3. Detect browser       │
              │     Accept header        │
              │  4. Convert to AVIF/WebP │
              │  5. Resize to w=640      │
              │  6. Apply quality=75     │
              │  7. Cache result         │
              │  8. Serve with headers   │
              └─────────────────────────┘
```

The `next/image` component generates an optimized `srcset` with multiple sizes so the browser picks the best one for the device's viewport and DPR (device pixel ratio).

---

## Q2. (Beginner) How do the `width`, `height`, `fill`, and `sizes` props work in `next/image`?

**Scenario**: You're building a hero section with a full-width background image and a grid of product thumbnails.

**Answer**:

There are **two rendering modes** for `next/image`:

1. **Fixed size mode** — Provide explicit `width` and `height`
2. **Fill mode** — Use `fill` prop, image fills its parent container

```tsx
import Image from 'next/image';

// MODE 1: Fixed width/height — for known dimensions
function ProductThumbnail({ src, name }: { src: string; name: string }) {
  return (
    <Image
      src={src}
      alt={name}
      width={300}        // intrinsic width
      height={200}       // intrinsic height
      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 300px"
      className="rounded-md object-cover"
    />
  );
}

// MODE 2: Fill mode — for responsive/unknown dimensions
function HeroSection() {
  return (
    <div className="relative h-[60vh] w-full">
      <Image
        src="/hero-banner.jpg"
        alt="Summer collection hero"
        fill                          // fills parent container
        sizes="100vw"                 // full viewport width
        priority                      // preload (above the fold)
        className="object-cover"      // CSS object-fit via className
        quality={85}
      />
      <div className="relative z-10 flex items-center justify-center h-full">
        <h1 className="text-5xl font-bold text-white">Summer Sale</h1>
      </div>
    </div>
  );
}
```

**The `sizes` prop is critical for performance**. It tells the browser which `srcset` entry to download before layout is computed:

```
sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 300px"

Breakpoint Logic:
┌────────────────────┬──────────────────┬─────────────────────┐
│  Viewport Width    │  Image Width     │  File Downloaded     │
├────────────────────┼──────────────────┼─────────────────────┤
│  ≤ 640px           │  100vw (640px)   │  640w variant        │
│  641–1024px        │  50vw (~512px)   │  640w variant        │
│  > 1024px          │  300px           │  384w variant        │
└────────────────────┴──────────────────┴─────────────────────┘
```

**When to use `fill`**:
- Background images
- Images where dimensions come from CMS and vary
- Art-direction responsive images
- Card images that should fill their container

**When to use explicit width/height**:
- Thumbnails with known fixed sizes
- Avatars
- Icons or logos

```tsx
// Fill mode with responsive grid
function ProductGrid({ products }: { products: Product[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {products.map((product) => (
        <div key={product.id} className="relative aspect-square">
          <Image
            src={product.image}
            alt={product.name}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
            className="object-cover rounded-lg"
          />
        </div>
      ))}
    </div>
  );
}
```

**Important**: When using `fill`, the parent element MUST have `position: relative` (or `absolute`/`fixed`) and defined dimensions. Without this, the image won't render correctly.

---

## Q3. (Beginner) How does `next/font` work, and why does it eliminate layout shift?

**Scenario**: Your site uses Google Fonts loaded via a `<link>` tag. Users notice a flash of unstyled text (FOUT) and slight layout jumps on every page load.

**Answer**:

`next/font` downloads fonts **at build time**, self-hosts them as static assets, and injects optimized `@font-face` CSS with `size-adjust` to achieve zero CLS (Cumulative Layout Shift).

```tsx
// app/layout.tsx
import { Inter, Roboto_Mono } from 'next/font/google';

// Fonts are downloaded at build time and self-hosted
const inter = Inter({
  subsets: ['latin'],          // only include latin characters
  display: 'swap',            // show fallback immediately, swap when loaded
  variable: '--font-inter',   // CSS variable for Tailwind
});

const robotoMono = Roboto_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-roboto-mono',
  weight: ['400', '700'],     // only include needed weights
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${robotoMono.variable}`}>
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
```

**Traditional approach vs `next/font`**:

```
Traditional (External Google Fonts):
┌────────┐    ┌───────────────────┐    ┌───────────────────┐
│ Browser │───▶│ fonts.googleapis  │───▶│ fonts.gstatic.com │
│         │    │ (CSS file)         │    │ (font files)      │
│ FOUT!   │    │ Render-blocking!  │    │ Extra DNS lookup! │
│ CLS!    │    │                   │    │                   │
└────────┘    └───────────────────┘    └───────────────────┘

next/font (Self-hosted at build time):
┌────────┐    ┌──────────────────────────┐
│ Browser │───▶│ /_next/static/media/     │
│         │    │ font-abc123.woff2        │
│ No FOUT │    │ Same origin!             │
│ No CLS  │    │ No external requests!    │
│         │    │ Preloaded!               │
└────────┘    └──────────────────────────┘
```

**How CLS is eliminated**: `next/font` computes `size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` values for the fallback font. This makes the fallback font's metrics match the web font, so when the swap happens, there's no layout shift.

```css
/* Auto-generated CSS (simplified) */
@font-face {
  font-family: '__Inter_abc123';
  src: url('/_next/static/media/inter-abc123.woff2') format('woff2');
  font-display: swap;
  font-weight: 100 900;
}

@font-face {
  font-family: '__Inter_Fallback_abc123';
  src: local('Arial');
  ascent-override: 90.49%;
  descent-override: 22.56%;
  line-gap-override: 0%;
  size-adjust: 107.06%;
}
```

**Integration with Tailwind CSS**:

```js
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-roboto-mono)', 'monospace'],
      },
    },
  },
};

export default config;
```

```tsx
// Usage in components
<h1 className="font-sans text-4xl">Clean Typography</h1>
<code className="font-mono">const x = 42;</code>
```

---

## Q4. (Beginner) What is `next/script` and when should you use each loading strategy?

**Scenario**: Your marketing team wants to add Google Analytics, a chatbot widget, and a social sharing script. How do you load them efficiently?

**Answer**:

`next/script` provides **four loading strategies** that control when and how third-party scripts execute:

| Strategy | When it Loads | Use Case |
|----------|--------------|----------|
| `beforeInteractive` | Before hydration (in `<head>`) | Polyfills, consent managers, critical A/B testing |
| `afterInteractive` | After hydration (default) | Analytics, tag managers |
| `lazyOnload` | During browser idle time | Chat widgets, social embeds, non-critical |
| `worker` | In a Web Worker (via Partytown) | Heavy analytics, ad scripts |

```tsx
import Script from 'next/script';

// app/layout.tsx — Scripts in layout apply to ALL pages
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}

        {/* CRITICAL: Cookie consent must run before any tracking */}
        <Script
          src="https://cdn.cookielaw.org/consent.js"
          strategy="beforeInteractive"
        />

        {/* ANALYTICS: Load after page is interactive */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"
          strategy="afterInteractive"
        />
        <Script id="gtag-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-XXXXXXX', {
              page_path: window.location.pathname,
            });
          `}
        </Script>

        {/* CHATBOT: Low priority, load when idle */}
        <Script
          src="https://widget.intercom.io/widget/abc123"
          strategy="lazyOnload"
          onLoad={() => {
            console.log('Intercom widget loaded');
          }}
        />
      </body>
    </html>
  );
}
```

**Loading timeline visualization**:

```
Page Load Timeline:
│
├── DNS/TCP/TLS
├── HTML Download
├── ▓▓▓ beforeInteractive scripts (blocking)
├── HTML Parse
├── React Hydration
├── ▓▓▓ afterInteractive scripts (default)
├── Page Interactive (FID/INP starts)
├── ... idle time ...
├── ▓▓▓ lazyOnload scripts (requestIdleCallback)
│
└── worker scripts run in Web Worker (parallel, off main thread)
```

**Event handlers available**:

```tsx
<Script
  src="/analytics.js"
  strategy="afterInteractive"
  onLoad={() => console.log('Script loaded')}
  onReady={() => console.log('Script ready (also fires on re-mount)')}
  onError={(e) => console.error('Script failed:', e)}
/>
```

**Key rule**: `beforeInteractive` can only be used in the root `layout.tsx` (or `_document.tsx` in Pages Router) because it must be injected into the initial HTML `<head>`.

---

## Q5. (Beginner) How does `next/image` handle automatic format conversion and quality optimization?

**Scenario**: Your e-commerce site has 10,000 product images in JPEG format. You want to serve AVIF to modern browsers and WebP as a fallback without manually converting all images.

**Answer**:

Next.js automatically detects the browser's `Accept` header and serves the most efficient format. You don't need to convert images manually — the image optimizer handles it on-the-fly and caches the result.

**Format Selection Logic**:

```
Browser sends: Accept: image/avif,image/webp,image/png,*/*
                        │
                        ▼
              ┌───────────────────────┐
              │  Next.js Image Server  │
              │                       │
              │  1. AVIF supported?   │──── Yes ──▶ Serve AVIF (best)
              │       │               │
              │       No              │
              │       ▼               │
              │  2. WebP supported?   │──── Yes ──▶ Serve WebP (good)
              │       │               │
              │       No              │
              │       ▼               │
              │  3. Serve original    │──────────▶ Serve JPEG/PNG
              └───────────────────────┘
```

**File size comparison** (typical 1200×800 photo):

```
Format    │  Size     │  Savings vs JPEG
──────────┼───────────┼─────────────────
JPEG      │  180 KB   │  baseline
WebP      │  120 KB   │  ~33% smaller
AVIF      │  85 KB    │  ~53% smaller
```

```tsx
// next.config.ts — configure image optimization
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    // Allowed formats (order = preference)
    formats: ['image/avif', 'image/webp'],

    // Quality setting (1-100, default 75)
    // Lower = smaller files, more compression artifacts
    quality: 80,

    // Device sizes for srcset generation
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],

    // Image sizes for the `sizes` prop
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],

    // Remote image domains (required for external images)
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.example.com',
        port: '',
        pathname: '/products/**',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],

    // Cache TTL for optimized images (seconds)
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
  },
};

export default nextConfig;
```

```tsx
// Per-image quality override
import Image from 'next/image';

// High-quality hero image (above the fold)
<Image
  src="/hero.jpg"
  alt="Hero banner"
  width={1920}
  height={1080}
  quality={90}       // Higher quality for hero
  priority           // Preload — critical for LCP
/>

// Lower-quality thumbnails (below the fold)
<Image
  src="/thumb.jpg"
  alt="Product thumbnail"
  width={300}
  height={200}
  quality={60}       // Lower quality acceptable for small images
/>
```

**Production tip**: Set `minimumCacheTTL` to at least 30 days for production. The image optimizer caches results in `.next/cache/images/`, and on platforms like Vercel, they're cached at the CDN edge. This means the first request for a size/format combo triggers optimization, but all subsequent requests are served from cache instantly.

---

## Q6. (Intermediate) How do you implement responsive art-direction images with `next/image` for different viewports?

**Scenario**: Your design team requires a landscape banner on desktop, a square crop on tablet, and a portrait crop on mobile — all from different source images.

**Answer**:

True art direction (different crops for different viewports) requires the HTML `<picture>` element, which `next/image` doesn't directly support. However, there are two production patterns to achieve this:

**Pattern 1: CSS-based art direction with `fill` mode**:

```tsx
import Image from 'next/image';

function HeroBanner() {
  return (
    <div className="relative w-full">
      {/* Mobile: Portrait crop (shown on small screens) */}
      <div className="block sm:hidden relative aspect-[3/4]">
        <Image
          src="/hero-mobile.jpg"
          alt="Summer sale"
          fill
          sizes="100vw"
          priority
          className="object-cover"
        />
      </div>

      {/* Tablet: Square crop */}
      <div className="hidden sm:block lg:hidden relative aspect-square">
        <Image
          src="/hero-tablet.jpg"
          alt="Summer sale"
          fill
          sizes="100vw"
          priority
          className="object-cover"
        />
      </div>

      {/* Desktop: Landscape banner */}
      <div className="hidden lg:block relative aspect-[21/9]">
        <Image
          src="/hero-desktop.jpg"
          alt="Summer sale"
          fill
          sizes="100vw"
          priority
          className="object-cover"
        />
      </div>
    </div>
  );
}
```

**Pattern 2: Custom `<picture>` element with `getImageProps` (Next.js 15+)**:

```tsx
import { getImageProps } from 'next/image';

function ArtDirectedHero() {
  const common = {
    alt: 'Summer collection hero banner',
    sizes: '100vw',
    priority: true,
  };

  const {
    props: { srcSet: desktopSrcSet, ...desktopRest },
  } = getImageProps({
    ...common,
    width: 1920,
    height: 820,
    quality: 85,
    src: '/hero-desktop.jpg',
  });

  const {
    props: { srcSet: tabletSrcSet, ...tabletRest },
  } = getImageProps({
    ...common,
    width: 1024,
    height: 1024,
    quality: 80,
    src: '/hero-tablet.jpg',
  });

  const {
    props: { srcSet: mobileSrcSet, ...mobileRest },
  } = getImageProps({
    ...common,
    width: 640,
    height: 853,
    quality: 75,
    src: '/hero-mobile.jpg',
  });

  return (
    <picture>
      <source media="(min-width: 1024px)" srcSet={desktopSrcSet} />
      <source media="(min-width: 640px)" srcSet={tabletSrcSet} />
      <source srcSet={mobileSrcSet} />
      {/* Fallback img — uses mobile props */}
      <img {...mobileRest} className="w-full h-auto object-cover" />
    </picture>
  );
}
```

**When to use which pattern**:

```
┌──────────────────────┬─────────────────────────────────┐
│  CSS-based (Pattern 1)│  getImageProps (Pattern 2)      │
├──────────────────────┼─────────────────────────────────┤
│ Simpler to implement │ True <picture> element          │
│ Multiple Image tags   │ Single <picture> + sources      │
│ Downloads ALL images │ Browser picks ONE source        │
│ CSS hides unused ones│ More efficient bandwidth        │
│ Good for 2 variants  │ Best for 3+ variants            │
│ Keeps next/image opts│ Still uses Next.js optimization │
└──────────────────────┴─────────────────────────────────┘
```

**Production recommendation**: Use Pattern 2 (`getImageProps`) for hero images where bandwidth savings matter. Use Pattern 1 for simpler cases where you only need to adjust `object-position` rather than entirely different crops.

---

## Q7. (Intermediate) How do you implement a custom image loader for external CDNs like Cloudinary, Imgix, or Akamai?

**Scenario**: Your company uses Cloudinary for all product images. You want `next/image` optimizations but served through Cloudinary's transformation pipeline instead of Next.js's built-in optimizer.

**Answer**:

A **custom loader** tells `next/image` to construct URLs pointing to your CDN's transformation API instead of Next.js's `/_next/image` endpoint. This offloads optimization to the CDN while keeping the DX of `next/image`.

```tsx
// lib/image-loaders.ts
import type { ImageLoaderProps } from 'next/image';

// Cloudinary loader
export function cloudinaryLoader({ src, width, quality }: ImageLoaderProps): string {
  const params = [
    'f_auto',                    // auto format (AVIF/WebP)
    'c_limit',                   // limit resize (don't upscale)
    `w_${width}`,                // width
    `q_${quality || 'auto'}`,    // quality (Cloudinary's auto is smart)
  ];
  return `https://res.cloudinary.com/your-cloud/image/upload/${params.join(',')}/${src}`;
}

// Imgix loader
export function imgixLoader({ src, width, quality }: ImageLoaderProps): string {
  const url = new URL(`https://your-domain.imgix.net${src}`);
  url.searchParams.set('auto', 'format');
  url.searchParams.set('fit', 'max');
  url.searchParams.set('w', width.toString());
  if (quality) url.searchParams.set('q', quality.toString());
  return url.toString();
}

// Akamai Image Manager loader
export function akamaiLoader({ src, width, quality }: ImageLoaderProps): string {
  return `https://cdn.example.com${src}?imwidth=${width}&imquality=${quality || 75}`;
}
```

**Usage — Per-component loader**:

```tsx
import Image from 'next/image';
import { cloudinaryLoader } from '@/lib/image-loaders';

export default function ProductImage({ publicId, name }: {
  publicId: string;
  name: string;
}) {
  return (
    <Image
      loader={cloudinaryLoader}
      src={publicId}              // e.g., "products/shoe-red-v2"
      alt={name}
      width={600}
      height={400}
      sizes="(max-width: 768px) 100vw, 50vw"
      quality={80}
    />
  );
}
```

**Usage — Global loader (applies to all images)**:

```ts
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    loader: 'custom',
    loaderFile: './lib/image-loaders.ts',
    // When using a custom loader, you may still need remotePatterns
    // for the <Image> component's security checks
  },
};

export default nextConfig;
```

```ts
// lib/image-loaders.ts (default export for global loader)
'use client';

import type { ImageLoaderProps } from 'next/image';

export default function globalLoader({ src, width, quality }: ImageLoaderProps): string {
  // Handle both local and remote images
  if (src.startsWith('/')) {
    // Local images — use Cloudinary upload
    return `https://res.cloudinary.com/your-cloud/image/upload/f_auto,c_limit,w_${width},q_${quality || 'auto'}${src}`;
  }
  // Already a full URL — append transformation params
  const url = new URL(src);
  url.searchParams.set('w', width.toString());
  url.searchParams.set('q', (quality || 75).toString());
  return url.toString();
}
```

**Advanced: Cloudinary with blur placeholder generation**:

```tsx
// lib/cloudinary-blur.ts
export function getCloudinaryBlurUrl(publicId: string): string {
  return `https://res.cloudinary.com/your-cloud/image/upload/w_10,q_10,f_auto,e_blur:1000/${publicId}`;
}

// Component with blur placeholder from Cloudinary
import Image from 'next/image';
import { cloudinaryLoader } from '@/lib/image-loaders';
import { getCloudinaryBlurUrl } from '@/lib/cloudinary-blur';

export default function CloudinaryImage({
  publicId,
  alt,
  width,
  height,
}: {
  publicId: string;
  alt: string;
  width: number;
  height: number;
}) {
  return (
    <Image
      loader={cloudinaryLoader}
      src={publicId}
      alt={alt}
      width={width}
      height={height}
      placeholder="blur"
      blurDataURL={getCloudinaryBlurUrl(publicId)}
    />
  );
}
```

**Architecture diagram**:

```
With custom CDN loader:
┌──────────────┐      ┌────────────────────┐
│  next/image   │──X──▶│ Next.js Optimizer   │ (bypassed)
│  component    │      └────────────────────┘
│               │
│  loader={cdn} │─────▶┌────────────────────┐
│               │      │  CDN (Cloudinary)   │
└──────────────┘      │  /f_auto,w_640/img  │
                       │  Optimized at edge  │
                       └────────────────────┘
```

---

## Q8. (Intermediate) How do you use `next/font` with local fonts and variable fonts? What's the performance difference?

**Scenario**: Your brand uses a custom proprietary font (not on Google Fonts). You need to load it with zero CLS and optimal subsetting.

**Answer**:

`next/font/local` handles local font files. Variable fonts are strongly preferred because a single file replaces multiple weight-specific files.

**Variable font (single file, all weights)**:

```tsx
// app/layout.tsx
import localFont from 'next/font/local';

// Variable font — one file covers all weights
const brandFont = localFont({
  src: '../fonts/BrandSans-Variable.woff2',
  display: 'swap',
  variable: '--font-brand',
  weight: '100 900',           // full weight range
  fallback: ['system-ui', 'Arial', 'sans-serif'],
  preload: true,
  adjustFontFallback: 'Arial', // generate size-adjust for this fallback
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={brandFont.variable}>
      <body className={brandFont.className}>{children}</body>
    </html>
  );
}
```

**Static fonts (multiple files per weight/style)**:

```tsx
import localFont from 'next/font/local';

const brandFont = localFont({
  src: [
    {
      path: '../fonts/BrandSans-Light.woff2',
      weight: '300',
      style: 'normal',
    },
    {
      path: '../fonts/BrandSans-Regular.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../fonts/BrandSans-RegularItalic.woff2',
      weight: '400',
      style: 'italic',
    },
    {
      path: '../fonts/BrandSans-Bold.woff2',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../fonts/BrandSans-BoldItalic.woff2',
      weight: '700',
      style: 'italic',
    },
  ],
  display: 'swap',
  variable: '--font-brand',
  fallback: ['system-ui', 'sans-serif'],
  adjustFontFallback: 'Arial',
});
```

**Performance comparison**:

```
Static Fonts (5 weight files):
┌────────────────────────────┐
│ BrandSans-Light.woff2   35KB │
│ BrandSans-Regular.woff2 38KB │
│ BrandSans-RegItalic.woff2 40KB │
│ BrandSans-Bold.woff2    42KB │
│ BrandSans-BoldItalic.woff2 44KB │
├────────────────────────────┤
│ Total: ~199KB (5 requests)    │
│ Only used weights downloaded  │
└────────────────────────────┘

Variable Font (1 file):
┌────────────────────────────┐
│ BrandSans-Variable.woff2 85KB │
├────────────────────────────┤
│ Total: 85KB (1 request)       │
│ All weights in one file       │
│ ~57% smaller total            │
└────────────────────────────┘
```

**Advanced: Font subsetting for CJK or icon fonts**:

```tsx
import localFont from 'next/font/local';

// CJK font with Unicode range subsetting
const notoSansJP = localFont({
  src: [
    {
      path: '../fonts/NotoSansJP-Regular-subset1.woff2',
      weight: '400',
      style: 'normal',
    },
  ],
  display: 'swap',
  variable: '--font-noto-jp',
  declarations: [
    // Only load glyphs in this Unicode range
    { prop: 'unicode-range', value: 'U+3000-30FF, U+4E00-9FFF' },
  ],
});
```

**Production font loading strategy**:

```
                     Build Time
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ Download  │    │ Generate CSS  │    │ Compute      │
│ font file │    │ @font-face    │    │ size-adjust  │
│           │    │ declarations  │    │ metrics      │
└──────┬───┘    └──────┬───────┘    └──────┬───────┘
       │               │                   │
       ▼               ▼                   ▼
  /_next/static/    Injected into     Fallback font
  media/font.woff2  <head> via         matches web
                    className          font metrics
```

---

## Q9. (Intermediate) How do you generate blur placeholders for dynamic/remote images in Next.js?

**Scenario**: Your product images come from a headless CMS. You want blur-up placeholders like static imports provide, but for remote images fetched at runtime.

**Answer**:

Static imports automatically generate `blurDataURL`, but remote/dynamic images require manual blur placeholder generation. Here are production patterns:

**Pattern 1: Generate blur at build time with `plaiceholder`**:

```tsx
// lib/get-blur-data.ts
import { getPlaiceholder } from 'plaiceholder';

export async function getBlurDataURL(imageUrl: string): Promise<string> {
  try {
    const response = await fetch(imageUrl);
    const buffer = Buffer.from(await response.arrayBuffer());
    const { base64 } = await getPlaiceholder(buffer, { size: 10 });
    return base64;
  } catch (error) {
    // Return transparent 1x1 pixel as fallback
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
  }
}
```

```tsx
// app/products/page.tsx
import Image from 'next/image';
import { getBlurDataURL } from '@/lib/get-blur-data';

interface Product {
  id: string;
  name: string;
  imageUrl: string;
  price: number;
}

async function getProducts(): Promise<Product[]> {
  const res = await fetch('https://api.example.com/products', {
    next: { revalidate: 3600 },
  });
  return res.json();
}

export default async function ProductsPage() {
  const products = await getProducts();

  // Generate blur placeholders in parallel
  const productsWithBlur = await Promise.all(
    products.map(async (product) => ({
      ...product,
      blurDataURL: await getBlurDataURL(product.imageUrl),
    }))
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {productsWithBlur.map((product) => (
        <div key={product.id} className="group">
          <div className="relative aspect-square overflow-hidden rounded-lg">
            <Image
              src={product.imageUrl}
              alt={product.name}
              fill
              sizes="(max-width: 768px) 100vw, 33vw"
              placeholder="blur"
              blurDataURL={product.blurDataURL}
              className="object-cover transition-transform group-hover:scale-105"
            />
          </div>
          <h3 className="mt-2 font-semibold">{product.name}</h3>
          <p className="text-gray-600">${product.price}</p>
        </div>
      ))}
    </div>
  );
}
```

**Pattern 2: ThumbHash — smaller and supports transparency**:

```tsx
// lib/thumbhash-blur.ts
import { rgbaToThumbHash, thumbHashToDataURL } from 'thumbhash';
import sharp from 'sharp';

export async function getThumbHashDataURL(imageUrl: string): Promise<string> {
  const response = await fetch(imageUrl);
  const buffer = Buffer.from(await response.arrayBuffer());

  // Resize to max 100x100 for ThumbHash
  const { data, info } = await sharp(buffer)
    .resize(100, 100, { fit: 'inside' })
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });

  const hash = rgbaToThumbHash(info.width, info.height, data);
  return thumbHashToDataURL(hash);
}
```

**Pattern 3: Store blur hashes in your CMS/database**:

```tsx
// Recommended production pattern: pre-compute and store
// scripts/generate-blur-hashes.ts
import { getPlaiceholder } from 'plaiceholder';
import { db } from '@/lib/db';

async function generateAndStoreBlurHashes() {
  const products = await db.product.findMany({
    where: { blurDataURL: null },
    select: { id: true, imageUrl: true },
  });

  for (const product of products) {
    try {
      const response = await fetch(product.imageUrl);
      const buffer = Buffer.from(await response.arrayBuffer());
      const { base64 } = await getPlaiceholder(buffer, { size: 10 });

      await db.product.update({
        where: { id: product.id },
        data: { blurDataURL: base64 },
      });

      console.log(`Generated blur hash for product ${product.id}`);
    } catch (error) {
      console.error(`Failed for product ${product.id}:`, error);
    }
  }
}

generateAndStoreBlurHashes();
```

**Performance considerations**:

```
Approach          │ When Generated │ Latency Impact    │ Best For
──────────────────┼───────────────┼──────────────────┼──────────────
plaiceholder      │ Server render  │ +50-200ms/image  │ Small catalogs
ThumbHash         │ Server render  │ +30-100ms/image  │ Transparent images
Pre-computed DB   │ Background job │ 0ms (cached)     │ Large catalogs ✅
CDN blur URL      │ CDN transform  │ Extra request    │ Cloudinary/Imgix users
CSS gradient      │ Instant        │ 0ms              │ Minimalist approach
```

---

## Q10. (Intermediate) How do you implement the `worker` strategy with `next/script` using Partytown for off-main-thread scripts?

**Scenario**: Your site loads Google Tag Manager, Facebook Pixel, and HotJar. Together they add 300ms to INP (Interaction to Next Paint). You need to move them off the main thread.

**Answer**:

The `worker` strategy in `next/script` uses **Partytown** to run third-party scripts in a Web Worker, keeping the main thread free for user interactions. This is a Next.js 15+ experimental feature.

```
Main Thread (WITHOUT worker strategy):
┌──────────────────────────────────────────────────┐
│  React Render │ GTM │ FB Pixel │ HotJar │ User │
│               │ 80ms│  60ms    │  50ms   │ Input│
│               │     │          │         │ SLOW │
└──────────────────────────────────────────────────┘
INP: 190ms+ (degraded by scripts)

Main Thread (WITH worker strategy):
┌──────────────────────────────────────────────────┐
│  React Render │                      │ User Input │
│               │    (thread free!)    │  FAST      │
└──────────────────────────────────────────────────┘
Web Worker:
┌──────────────────────────────────────────────────┐
│  GTM │ FB Pixel │ HotJar (runs here, isolated)   │
└──────────────────────────────────────────────────┘
INP: ~50ms (scripts don't block)
```

**Setup**:

```ts
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    nextScriptWorkers: true,
  },
};

export default nextConfig;
```

```bash
npm install @builder.io/partytown
```

```tsx
// app/layout.tsx
import Script from 'next/script';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}

        {/* Google Tag Manager — runs in Web Worker */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"
          strategy="worker"
        />
        <Script id="gtag-init" strategy="worker">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-XXXXXXX');
          `}
        </Script>

        {/* Facebook Pixel — runs in Web Worker */}
        <Script id="fb-pixel" strategy="worker">
          {`
            !function(f,b,e,v,n,t,s)
            {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', 'YOUR_PIXEL_ID');
            fbq('track', 'PageView');
          `}
        </Script>

        {/* HotJar — runs in Web Worker */}
        <Script id="hotjar" strategy="worker">
          {`
            (function(h,o,t,j,a,r){
              h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
              h._hjSettings={hjid:YOUR_ID,hjsv:6};
              a=o.getElementsByTagName('head')[0];
              r=o.createElement('script');r.async=1;
              r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
              a.appendChild(r);
            })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
          `}
        </Script>
      </body>
    </html>
  );
}
```

**Partytown configuration for proxying requests**:

```tsx
// Some scripts need DOM access — Partytown proxies these calls
// app/layout.tsx
import { Partytown } from '@builder.io/partytown/react';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Partytown
          debug={process.env.NODE_ENV === 'development'}
          forward={[
            'dataLayer.push',    // GTM data layer
            'fbq',               // Facebook Pixel
            'hj',                // HotJar
          ]}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

**Known limitations**:
- Scripts in Web Worker can't directly access DOM (Partytown proxies DOM calls, adding ~1ms latency per call)
- `document.cookie` access is proxied asynchronously
- Some scripts rely on synchronous DOM access and may break
- Test thoroughly — not all third-party scripts are compatible

**Decision matrix**:

```
Script Type              │ Compatible? │ Strategy Recommendation
─────────────────────────┼────────────┼────────────────────────
Google Analytics/GTM     │ ✅ Yes      │ worker
Facebook Pixel           │ ✅ Yes      │ worker
HotJar                   │ ✅ Yes      │ worker
Intercom                 │ ⚠️ Partial  │ lazyOnload (safer)
Stripe.js                │ ❌ No       │ afterInteractive
reCAPTCHA                │ ❌ No       │ afterInteractive
Cookie consent banners   │ ❌ No       │ beforeInteractive
```

---

## Q11. (Intermediate) How do you optimize LCP (Largest Contentful Paint) with `next/image` priority loading and preload hints?

**Scenario**: Your landing page has an LCP score of 3.2 seconds. The LCP element is a hero image. You need to get it below 2.5 seconds.

**Answer**:

LCP is most often caused by a large hero image loading too slowly. Here's a systematic approach to optimize it:

**Step 1: Mark the LCP image as `priority`**:

```tsx
import Image from 'next/image';

// The priority prop does THREE things:
// 1. Sets loading="eager" (disables lazy loading)
// 2. Adds fetchPriority="high" to the <img> tag
// 3. Generates a <link rel="preload"> in <head>
export default function HeroSection() {
  return (
    <section className="relative h-screen">
      <Image
        src="/hero-banner.jpg"
        alt="Product launch hero"
        fill
        sizes="100vw"
        priority            // ← This is the critical prop
        quality={85}
        className="object-cover"
      />
    </section>
  );
}
```

**What `priority` generates in HTML**:

```html
<head>
  <!-- Preload hint — browser fetches ASAP, before CSS/JS -->
  <link
    rel="preload"
    as="image"
    imagesrcset="/_next/image?url=%2Fhero.jpg&w=640&q=85 640w,
                 /_next/image?url=%2Fhero.jpg&w=750&q=85 750w,
                 /_next/image?url=%2Fhero.jpg&w=1920&q=85 1920w"
    imagesizes="100vw"
    fetchpriority="high"
  />
</head>
<body>
  <img
    srcset="..."
    sizes="100vw"
    loading="eager"
    fetchpriority="high"
    decoding="async"
  />
</body>
```

**Step 2: Optimize the `sizes` attribute**:

```tsx
// ❌ BAD — Forces browser to download largest variant
<Image src="/hero.jpg" fill priority sizes="100vw" />
// On a 375px phone, this downloads the 3840w image (wasteful!)

// ✅ GOOD — Browser picks the right size for the device
<Image
  src="/hero.jpg"
  fill
  priority
  sizes="(max-width: 640px) 640px, (max-width: 1024px) 1024px, 1920px"
/>
```

**Step 3: Configure device sizes for your breakpoints**:

```ts
// next.config.ts
const nextConfig = {
  images: {
    deviceSizes: [640, 828, 1080, 1200, 1920],  // Remove 2048, 3840 if not needed
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    formats: ['image/avif', 'image/webp'],        // AVIF is ~50% smaller
    minimumCacheTTL: 60 * 60 * 24 * 365,          // 1 year cache
  },
};
```

**Step 4: Use a CDN with edge caching**:

```
LCP optimization waterfall:
                                                                
Without priority:               With priority + CDN:
├── HTML download               ├── HTML download
├── CSS download                ├── CSS download  
├── JS download                 ├── Image preload starts ◄── parallel!
├── React hydration             ├── JS download
├── Lazy load triggered         ├── React hydration
├── Image request               ├── Image already loaded! ✅
├── Image download              │
├── Image decode                ├── LCP: ~1.5s
├── LCP: ~3.2s                  │
```

**Step 5: Consider static image imports for above-the-fold images**:

```tsx
// Static import — generates blurDataURL automatically at build time
import heroImage from '@/public/hero-banner.jpg';
import Image from 'next/image';

export default function HeroSection() {
  return (
    <Image
      src={heroImage}            // Static import — optimized at build
      alt="Hero banner"
      priority
      placeholder="blur"          // Auto blur placeholder
      sizes="100vw"
      className="object-cover w-full h-screen"
    />
  );
}
```

**LCP checklist**:

```
✅ Hero image has priority={true}
✅ sizes prop accurately reflects rendered size
✅ Image format is AVIF/WebP (not JPEG)
✅ Image quality is 75-85 (not 100)
✅ CDN caches optimized images at edge
✅ deviceSizes matches your breakpoints
✅ No render-blocking resources before image
✅ Server response time < 200ms (TTFB)
```

---

## Q12. (Intermediate) How do you implement font subsetting and optimize font loading for multilingual sites?

**Scenario**: Your SaaS product supports English, Japanese, Korean, and Arabic. Loading all font weights for all languages would be over 5MB.

**Answer**:

The key strategy is **per-language font loading with Unicode range subsetting**. Each language loads only the glyphs it needs.

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google';
import { Noto_Sans_JP, Noto_Sans_KR, Noto_Sans_Arabic } from 'next/font/google';

// Latin — ~100KB (all weights)
const inter = Inter({
  subsets: ['latin', 'latin-ext'],
  display: 'swap',
  variable: '--font-latin',
  preload: true,       // preload for primary language
});

// Japanese — loaded only when needed
const notoSansJP = Noto_Sans_JP({
  subsets: ['latin'],  // Google Fonts auto-subsets CJK
  weight: ['400', '700'],
  display: 'swap',
  variable: '--font-jp',
  preload: false,       // don't preload — only needed for Japanese pages
});

// Korean
const notoSansKR = Noto_Sans_KR({
  subsets: ['latin'],
  weight: ['400', '700'],
  display: 'swap',
  variable: '--font-kr',
  preload: false,
});

// Arabic
const notoSansArabic = Noto_Sans_Arabic({
  subsets: ['arabic'],
  weight: ['400', '700'],
  display: 'swap',
  variable: '--font-arabic',
  preload: false,
});

export default function RootLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  // All font variables are always available via CSS
  const fontClasses = `${inter.variable} ${notoSansJP.variable} ${notoSansKR.variable} ${notoSansArabic.variable}`;

  return (
    <html lang="en" className={fontClasses}>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

**Per-locale font selection with CSS**:

```css
/* globals.css */
:root {
  --font-sans: var(--font-latin), system-ui, sans-serif;
}

[lang="ja"] {
  --font-sans: var(--font-jp), var(--font-latin), sans-serif;
}

[lang="ko"] {
  --font-sans: var(--font-kr), var(--font-latin), sans-serif;
}

[lang="ar"] {
  --font-sans: var(--font-arabic), var(--font-latin), sans-serif;
  direction: rtl;
}

body {
  font-family: var(--font-sans);
}
```

**Advanced: Per-route locale layout**:

```tsx
// app/[locale]/layout.tsx
import { Inter, Noto_Sans_JP, Noto_Sans_KR, Noto_Sans_Arabic } from 'next/font/google';

const fontMap = {
  en: Inter({ subsets: ['latin'], display: 'swap' }),
  ja: Noto_Sans_JP({ subsets: ['latin'], weight: ['400', '700'], display: 'swap' }),
  ko: Noto_Sans_KR({ subsets: ['latin'], weight: ['400', '700'], display: 'swap' }),
  ar: Noto_Sans_Arabic({ subsets: ['arabic'], weight: ['400', '700'], display: 'swap' }),
} as const;

type Locale = keyof typeof fontMap;

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const font = fontMap[locale as Locale] || fontMap.en;

  return (
    <html lang={locale} dir={locale === 'ar' ? 'rtl' : 'ltr'}>
      <body className={font.className}>{children}</body>
    </html>
  );
}
```

**Font loading budget**:

```
Language │ Font          │ Size (subset) │ Preload?
─────────┼──────────────┼──────────────┼─────────
English  │ Inter         │ ~100KB        │ Yes ✅
Japanese │ Noto Sans JP  │ ~1.5MB*       │ No (on demand)
Korean   │ Noto Sans KR  │ ~800KB*       │ No (on demand)
Arabic   │ Noto Sans AR  │ ~150KB        │ No (on demand)

* Google Fonts auto-subsets CJK into ~120 chunks
  Browser only downloads chunks containing used characters
  Typical page loads 3-5 chunks (~50KB each)
```

**Google Fonts CJK auto-subsetting**: Google Fonts automatically splits CJK fonts into ~120 Unicode range subsets. When the browser encounters a character, it only downloads the subset containing that character. This is why `next/font` for CJK languages is efficient despite the large total font file.

---

## Q13. (Advanced) How do you build a production image pipeline with `next/image` for an e-commerce site handling 100K+ product images?

**Scenario**: You're architecting the image system for a large e-commerce platform. Images come from multiple vendors, vary in quality, and must load fast globally.

**Answer**:

A production image pipeline at scale involves five layers: ingestion, processing, storage, delivery, and rendering.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Production Image Pipeline                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐    ┌──────────┐  │
│  │  Ingest   │───▶│   Process    │───▶│   Store   │───▶│  Deliver │  │
│  │           │    │              │    │           │    │          │  │
│  │ • Upload  │    │ • Validate   │    │ • S3/R2   │    │ • CDN    │  │
│  │ • API     │    │ • Resize     │    │ • GCS     │    │ • Edge   │  │
│  │ • Webhook │    │ • Strip EXIF │    │ • Blob    │    │ • Cache  │  │
│  │ • Scrape  │    │ • Blur hash  │    │           │    │          │  │
│  └──────────┘    │ • AI tag     │    └───────────┘    └──────────┘  │
│                   └──────────────┘                                    │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │  Render Layer (next/image)                                    │   │
│  │  • Custom loader → CDN transform URL                          │   │
│  │  • Blur placeholder from pre-computed DB field                │   │
│  │  • Responsive sizes per component context                     │   │
│  │  • Priority for above-fold, lazy for below-fold               │   │
│  └───────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Layer 1: Image Ingestion Service**:

```tsx
// app/api/images/upload/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import sharp from 'sharp';
import { nanoid } from 'nanoid';
import { db } from '@/lib/db';

const s3 = new S3Client({ region: process.env.AWS_REGION });

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const file = formData.get('image') as File;

  if (!file) {
    return NextResponse.json({ error: 'No image provided' }, { status: 400 });
  }

  const buffer = Buffer.from(await file.arrayBuffer());
  const metadata = await sharp(buffer).metadata();

  // Validation
  if (!metadata.width || !metadata.height) {
    return NextResponse.json({ error: 'Invalid image' }, { status: 400 });
  }

  if (metadata.width < 400 || metadata.height < 400) {
    return NextResponse.json({ error: 'Image too small (min 400x400)' }, { status: 400 });
  }

  // Process: strip EXIF, normalize orientation, generate variants
  const processed = sharp(buffer)
    .rotate()              // auto-rotate based on EXIF
    .withMetadata({})      // strip EXIF data (privacy)
    .jpeg({ quality: 90 }); // normalize to high-quality JPEG

  const processedBuffer = await processed.toBuffer();

  // Generate blur hash
  const { data: blurBuffer, info: blurInfo } = await sharp(buffer)
    .resize(10, 10, { fit: 'inside' })
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });

  const blurBase64 = `data:image/jpeg;base64,${
    (await sharp(blurBuffer, {
      raw: { width: blurInfo.width, height: blurInfo.height, channels: 4 },
    })
      .jpeg({ quality: 20 })
      .toBuffer()
    ).toString('base64')
  }`;

  // Upload to S3
  const key = `products/${nanoid()}.jpg`;
  await s3.send(
    new PutObjectCommand({
      Bucket: process.env.S3_BUCKET,
      Key: key,
      Body: processedBuffer,
      ContentType: 'image/jpeg',
      CacheControl: 'public, max-age=31536000, immutable',
    })
  );

  // Store metadata in database
  const image = await db.productImage.create({
    data: {
      key,
      width: metadata.width,
      height: metadata.height,
      blurDataURL: blurBase64,
      originalFilename: file.name,
      sizeBytes: processedBuffer.length,
      cdnUrl: `https://cdn.example.com/${key}`,
    },
  });

  return NextResponse.json({ imageId: image.id, url: image.cdnUrl });
}
```

**Layer 2: CDN Loader with Cloudflare Image Resizing**:

```tsx
// lib/production-image-loader.ts
import type { ImageLoaderProps } from 'next/image';

export function productionImageLoader({ src, width, quality }: ImageLoaderProps): string {
  // Cloudflare Image Resizing
  if (process.env.NEXT_PUBLIC_CDN_PROVIDER === 'cloudflare') {
    return `https://cdn.example.com/cdn-cgi/image/width=${width},quality=${quality || 80},format=auto/${src}`;
  }

  // Cloudinary
  if (process.env.NEXT_PUBLIC_CDN_PROVIDER === 'cloudinary') {
    return `https://res.cloudinary.com/${process.env.NEXT_PUBLIC_CLOUD_NAME}/image/upload/f_auto,q_${quality || 80},w_${width}/${src}`;
  }

  // Imgix
  return `https://${process.env.NEXT_PUBLIC_IMGIX_DOMAIN}/${src}?auto=format&fit=max&w=${width}&q=${quality || 80}`;
}
```

**Layer 3: Optimized Product Image Component**:

```tsx
// components/product-image.tsx
import Image from 'next/image';
import { productionImageLoader } from '@/lib/production-image-loader';

interface ProductImageProps {
  image: {
    key: string;
    width: number;
    height: number;
    blurDataURL: string;
    cdnUrl: string;
  };
  alt: string;
  priority?: boolean;
  variant: 'thumbnail' | 'card' | 'detail' | 'zoom';
}

const variantConfig = {
  thumbnail: {
    width: 100,
    height: 100,
    sizes: '100px',
    quality: 60,
  },
  card: {
    width: 400,
    height: 400,
    sizes: '(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw',
    quality: 75,
  },
  detail: {
    width: 800,
    height: 800,
    sizes: '(max-width: 768px) 100vw, 50vw',
    quality: 85,
  },
  zoom: {
    width: 1600,
    height: 1600,
    sizes: '100vw',
    quality: 90,
  },
};

export function ProductImage({ image, alt, priority, variant }: ProductImageProps) {
  const config = variantConfig[variant];

  return (
    <Image
      loader={productionImageLoader}
      src={image.key}
      alt={alt}
      width={config.width}
      height={config.height}
      sizes={config.sizes}
      quality={config.quality}
      priority={priority}
      placeholder="blur"
      blurDataURL={image.blurDataURL}
      className="object-cover"
    />
  );
}
```

**Layer 4: Cache warming strategy for popular products**:

```tsx
// scripts/warm-image-cache.ts
// Run after deployment to pre-warm CDN cache for top products
async function warmImageCache() {
  const topProducts = await db.product.findMany({
    where: { featured: true },
    include: { images: true },
    take: 1000,
  });

  const sizes = [640, 750, 828, 1080, 1200];
  const formats = ['avif', 'webp'];

  for (const product of topProducts) {
    for (const image of product.images) {
      for (const size of sizes) {
        for (const format of formats) {
          // Request each variant to populate CDN cache
          const url = `https://cdn.example.com/cdn-cgi/image/width=${size},format=${format}/${image.key}`;
          await fetch(url, { method: 'HEAD' });
        }
      }
    }
  }
}
```

This architecture handles 100K+ images efficiently because:
1. Original images are stored once in object storage
2. CDN transforms on-the-fly and caches at edge
3. Pre-computed blur hashes add zero runtime cost
4. `next/image` generates optimal `srcset` per viewport
5. Cache warming ensures zero cold-start latency for popular items

---

## Q14. (Advanced) How do you implement a complete font performance strategy with `next/font` including metrics overrides, critical CSS, and font preloading?

**Scenario**: Your design system uses a custom variable font plus an icon font. You need sub-100ms font swap with zero CLS across all routes, including SSR and streaming.

**Answer**:

A comprehensive font strategy addresses four aspects: loading, rendering, fallback matching, and monitoring.

```
Font Performance Strategy:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  1. LOADING          2. RENDERING       3. FALLBACK MATCHING    │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │ • Preload     │   │ • font-display│   │ • size-adjust      │  │
│  │ • Self-host   │   │ • unicode-   │   │ • ascent-override  │  │
│  │ • Subset      │   │   range      │   │ • descent-override │  │
│  │ • Compress    │   │ • Swap period│   │ • line-gap-override│  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│                                                                  │
│  4. MONITORING                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • Font loading events • CLS measurement • FOUT detection│     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Step 1: Font declaration with precise fallback metrics**:

```tsx
// app/fonts.ts — centralize all font config
import localFont from 'next/font/local';
import { JetBrains_Mono } from 'next/font/google';

// Primary brand font — variable weight
export const brandFont = localFont({
  src: [
    {
      path: '../public/fonts/BrandSans-Variable.woff2',
      style: 'normal',
    },
    {
      path: '../public/fonts/BrandSans-Variable-Italic.woff2',
      style: 'italic',
    },
  ],
  display: 'swap',
  variable: '--font-brand',
  weight: '100 900',
  preload: true,
  fallback: ['system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
  adjustFontFallback: 'Arial', // auto-compute metrics against Arial

  // Manual overrides (if auto doesn't match perfectly)
  declarations: [
    { prop: 'size-adjust', value: '105%' },
    { prop: 'ascent-override', value: '90%' },
    { prop: 'descent-override', value: '22%' },
    { prop: 'line-gap-override', value: '0%' },
  ],
});

// Icon font — only load icon glyphs
export const iconFont = localFont({
  src: '../public/fonts/BrandIcons.woff2',
  display: 'block',     // block display for icons (invisible > wrong glyph)
  variable: '--font-icons',
  preload: true,
  declarations: [
    { prop: 'unicode-range', value: 'U+E000-E999' }, // PUA range for icons
  ],
});

// Code font — for code blocks
export const codeFont = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-code',
  weight: ['400', '700'],
  preload: false,        // code blocks are rarely above-fold
});
```

**Step 2: Layout with font application**:

```tsx
// app/layout.tsx
import { brandFont, iconFont, codeFont } from './fonts';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${brandFont.variable} ${iconFont.variable} ${codeFont.variable}`}
    >
      <body className={brandFont.className}>
        {children}
      </body>
    </html>
  );
}
```

**Step 3: CSS integration with Tailwind**:

```ts
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-brand)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-code)', 'Consolas', 'monospace'],
        icons: ['var(--font-icons)'],
      },
    },
  },
};

export default config;
```

**Step 4: Font loading monitoring component**:

```tsx
// components/font-metrics.tsx
'use client';

import { useEffect } from 'react';

export function FontMetrics() {
  useEffect(() => {
    if (typeof document === 'undefined') return;

    // Monitor font loading performance
    if ('fonts' in document) {
      const startTime = performance.now();

      document.fonts.ready.then(() => {
        const loadTime = performance.now() - startTime;

        // Report to analytics
        if (window.gtag) {
          window.gtag('event', 'font_loaded', {
            event_category: 'Web Vitals',
            value: Math.round(loadTime),
            event_label: 'All fonts ready',
          });
        }

        // Log in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`[Fonts] All fonts loaded in ${loadTime.toFixed(1)}ms`);
          document.fonts.forEach((font) => {
            console.log(`  - ${font.family} ${font.weight} ${font.style}: ${font.status}`);
          });
        }
      });

      // Detect FOUT
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'layout-shift' && (entry as any).value > 0.01) {
            console.warn('[CLS] Layout shift detected during font load:', (entry as any).value);
          }
        }
      });

      observer.observe({ type: 'layout-shift', buffered: true });
      return () => observer.disconnect();
    }
  }, []);

  return null; // This component renders nothing
}
```

**Step 5: Icon font component with type-safe icons**:

```tsx
// components/icon.tsx
const iconMap = {
  home: '\uE001',
  search: '\uE002',
  cart: '\uE003',
  user: '\uE004',
  close: '\uE005',
  menu: '\uE006',
  check: '\uE007',
  arrow_right: '\uE008',
} as const;

type IconName = keyof typeof iconMap;

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
  'aria-label'?: string;
}

export function Icon({ name, size = 24, className = '', ...props }: IconProps) {
  return (
    <span
      className={`font-icons inline-block leading-none ${className}`}
      style={{ fontSize: size }}
      role="img"
      aria-hidden={!props['aria-label']}
      {...props}
    >
      {iconMap[name]}
    </span>
  );
}
```

This strategy ensures: zero CLS from font loading, minimal FOUT window, efficient loading budget (only preload critical fonts), and monitoring to catch regressions.

---

## Q15. (Advanced) How do you manage third-party scripts in a Next.js application for GDPR/CCPA compliance with consent management?

**Scenario**: Your site operates in the EU and California. You must not load analytics, marketing, or personalization scripts until the user gives explicit consent, and must remove them if consent is withdrawn.

**Answer**:

This requires a **consent-gated script loading system** that integrates with `next/script` and a consent management platform (CMP).

```
Consent-Gated Script Loading Flow:
┌──────────┐     ┌─────────────┐     ┌──────────────────┐
│  Page Load │────▶│ CMP Banner   │────▶│  User Decision   │
│            │     │ (beforeInt.) │     │                  │
└──────────┘     └─────────────┘     │  Accept All ──┐  │
                                      │  Reject All ──┤  │
                                      │  Customize ───┤  │
                                      └───────────────┘  │
                                               │          │
                              ┌────────────────┘          │
                              ▼                           │
                   ┌─────────────────┐                    │
                   │ Consent State    │                    │
                   │                  │                    │
                   │ analytics: ✅/❌ │                    │
                   │ marketing: ✅/❌ │◄───────────────────┘
                   │ functional: ✅/❌│ (can change later)
                   │ necessary: ✅    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ ConditionalScript│
                   │ Components       │
                   │                  │
                   │ Only load scripts│
                   │ matching consent │
                   └─────────────────┘
```

**Step 1: Consent context and hook**:

```tsx
// lib/consent-context.tsx
'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';

export type ConsentCategory = 'necessary' | 'functional' | 'analytics' | 'marketing';

interface ConsentState {
  necessary: boolean;   // always true
  functional: boolean;
  analytics: boolean;
  marketing: boolean;
  decided: boolean;     // user has made a decision
}

interface ConsentContextType {
  consent: ConsentState;
  updateConsent: (category: ConsentCategory, value: boolean) => void;
  acceptAll: () => void;
  rejectAll: () => void;
  hasConsent: (category: ConsentCategory) => boolean;
}

const ConsentContext = createContext<ConsentContextType | null>(null);

const COOKIE_NAME = 'cookie_consent';
const COOKIE_MAX_AGE = 365 * 24 * 60 * 60; // 1 year

const defaultConsent: ConsentState = {
  necessary: true,
  functional: false,
  analytics: false,
  marketing: false,
  decided: false,
};

function getConsentFromCookie(): ConsentState {
  if (typeof document === 'undefined') return defaultConsent;
  const cookie = document.cookie
    .split('; ')
    .find((c) => c.startsWith(`${COOKIE_NAME}=`));
  if (!cookie) return defaultConsent;
  try {
    return { ...JSON.parse(decodeURIComponent(cookie.split('=')[1])), decided: true };
  } catch {
    return defaultConsent;
  }
}

function setConsentCookie(consent: ConsentState) {
  const value = encodeURIComponent(JSON.stringify(consent));
  document.cookie = `${COOKIE_NAME}=${value}; max-age=${COOKIE_MAX_AGE}; path=/; SameSite=Lax; Secure`;
}

export function ConsentProvider({ children }: { children: React.ReactNode }) {
  const [consent, setConsent] = useState<ConsentState>(defaultConsent);

  useEffect(() => {
    setConsent(getConsentFromCookie());
  }, []);

  const updateConsent = useCallback((category: ConsentCategory, value: boolean) => {
    setConsent((prev) => {
      const next = { ...prev, [category]: value, decided: true };
      setConsentCookie(next);

      // Fire consent update event for GTM
      if (typeof window !== 'undefined' && window.dataLayer) {
        window.dataLayer.push({
          event: 'consent_update',
          consent_analytics: next.analytics ? 'granted' : 'denied',
          consent_marketing: next.marketing ? 'granted' : 'denied',
        });
      }

      return next;
    });
  }, []);

  const acceptAll = useCallback(() => {
    const next: ConsentState = {
      necessary: true,
      functional: true,
      analytics: true,
      marketing: true,
      decided: true,
    };
    setConsent(next);
    setConsentCookie(next);
  }, []);

  const rejectAll = useCallback(() => {
    const next: ConsentState = {
      necessary: true,
      functional: false,
      analytics: false,
      marketing: false,
      decided: true,
    };
    setConsent(next);
    setConsentCookie(next);

    // Clean up existing tracking cookies
    cleanUpTrackingCookies();
  }, []);

  const hasConsent = useCallback(
    (category: ConsentCategory) => consent[category],
    [consent]
  );

  return (
    <ConsentContext.Provider
      value={{ consent, updateConsent, acceptAll, rejectAll, hasConsent }}
    >
      {children}
    </ConsentContext.Provider>
  );
}

export function useConsent() {
  const context = useContext(ConsentContext);
  if (!context) throw new Error('useConsent must be used within ConsentProvider');
  return context;
}

function cleanUpTrackingCookies() {
  const trackingCookies = ['_ga', '_gid', '_gat', '_fbp', '_fbc', 'hubspotutk'];
  trackingCookies.forEach((name) => {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.${window.location.hostname}`;
  });
}
```

**Step 2: Consent-gated script component**:

```tsx
// components/consent-script.tsx
'use client';

import Script from 'next/script';
import { useConsent, type ConsentCategory } from '@/lib/consent-context';

interface ConsentScriptProps {
  category: ConsentCategory;
  src?: string;
  id?: string;
  strategy?: 'afterInteractive' | 'lazyOnload' | 'worker';
  children?: string;
  onLoad?: () => void;
}

export function ConsentScript({
  category,
  src,
  id,
  strategy = 'afterInteractive',
  children,
  onLoad,
}: ConsentScriptProps) {
  const { hasConsent } = useConsent();

  // Don't render the script if consent not granted
  if (!hasConsent(category)) {
    return null;
  }

  return (
    <Script
      src={src}
      id={id}
      strategy={strategy}
      onLoad={onLoad}
    >
      {children}
    </Script>
  );
}
```

**Step 3: Usage in layout**:

```tsx
// app/layout.tsx
import Script from 'next/script';
import { ConsentProvider } from '@/lib/consent-context';
import { ConsentScript } from '@/components/consent-script';
import { CookieBanner } from '@/components/cookie-banner';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ConsentProvider>
          {/* Cookie consent banner — always loads first */}
          <Script
            id="consent-defaults"
            strategy="beforeInteractive"
          >
            {`
              // Set default consent state (denied) before any scripts load
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('consent', 'default', {
                'analytics_storage': 'denied',
                'ad_storage': 'denied',
                'ad_personalization': 'denied',
                'ad_user_data': 'denied',
                'functionality_storage': 'granted',
                'security_storage': 'granted',
              });
            `}
          </Script>

          {children}

          {/* Analytics — only loads after consent */}
          <ConsentScript
            category="analytics"
            src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"
            strategy="worker"
          />
          <ConsentScript category="analytics" id="ga-init" strategy="worker">
            {`
              gtag('consent', 'update', { 'analytics_storage': 'granted' });
              gtag('js', new Date());
              gtag('config', 'G-XXXXXXX');
            `}
          </ConsentScript>

          {/* Marketing — only loads after consent */}
          <ConsentScript category="marketing" id="fb-pixel" strategy="worker">
            {`
              !function(f,b,e,v,n,t,s){/* ... FB Pixel code ... */}
              (window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
              fbq('consent', 'grant');
              fbq('init', 'PIXEL_ID');
              fbq('track', 'PageView');
            `}
          </ConsentScript>

          {/* Cookie banner UI */}
          <CookieBanner />
        </ConsentProvider>
      </body>
    </html>
  );
}
```

**Step 4: Cookie banner component**:

```tsx
// components/cookie-banner.tsx
'use client';

import { useConsent } from '@/lib/consent-context';

export function CookieBanner() {
  const { consent, acceptAll, rejectAll } = useConsent();

  if (consent.decided) return null;

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t shadow-lg p-6"
    >
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center gap-4">
        <p className="text-sm text-gray-700 flex-1">
          We use cookies to enhance your experience. By clicking &quot;Accept All&quot;,
          you consent to analytics and marketing cookies.
          <a href="/privacy" className="underline ml-1">Learn more</a>
        </p>
        <div className="flex gap-3">
          <button
            onClick={rejectAll}
            className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50"
          >
            Reject All
          </button>
          <button
            onClick={acceptAll}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Accept All
          </button>
        </div>
      </div>
    </div>
  );
}
```

This pattern ensures legal compliance while maintaining good performance: scripts never load without consent, consent state persists, and consent can be withdrawn (removing scripts and clearing cookies).

---

## Q16. (Advanced) How do you implement progressive image loading with blur-to-sharp transitions and intersection observer-based loading?

**Scenario**: Your media-heavy news site needs a polished image loading experience — tiny blur placeholder that smoothly transitions to the full image as users scroll, with minimal JavaScript overhead.

**Answer**:

While `next/image` handles lazy loading natively, a production media site often needs custom transitions and precise control over loading behavior. Here's a complete progressive image loading system:

```
Progressive Loading Stages:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Stage 1      │    │  Stage 2      │    │  Stage 3      │
│  Color/Blur   │───▶│  Low Quality  │───▶│  Full Image   │
│  Placeholder   │    │  Progressive  │    │  Sharp        │
│  (~200 bytes)  │    │  (~5KB)       │    │  (~50-200KB)  │
│  Instant       │    │  ~100ms       │    │  ~500ms-2s    │
└──────────────┘    └──────────────┘    └──────────────┘
```

**The Enhanced Image Component**:

```tsx
// components/progressive-image.tsx
'use client';

import Image from 'next/image';
import { useState, useCallback, useRef, useEffect } from 'react';

interface ProgressiveImageProps {
  src: string;
  alt: string;
  width: number;
  height: number;
  blurDataURL?: string;
  dominantColor?: string; // hex color from image analysis
  sizes?: string;
  priority?: boolean;
  className?: string;
  quality?: number;
  onLoadComplete?: () => void;
}

type LoadingState = 'placeholder' | 'loading' | 'loaded' | 'error';

export function ProgressiveImage({
  src,
  alt,
  width,
  height,
  blurDataURL,
  dominantColor = '#e5e7eb',
  sizes,
  priority = false,
  className = '',
  quality = 80,
  onLoadComplete,
}: ProgressiveImageProps) {
  const [loadingState, setLoadingState] = useState<LoadingState>(
    priority ? 'loading' : 'placeholder'
  );
  const [isInView, setIsInView] = useState(priority);
  const containerRef = useRef<HTMLDivElement>(null);

  // Intersection Observer for scroll-triggered loading
  useEffect(() => {
    if (priority || isInView) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          setLoadingState('loading');
          observer.disconnect();
        }
      },
      {
        rootMargin: '200px', // start loading 200px before visible
        threshold: 0,
      }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, [priority, isInView]);

  const handleLoad = useCallback(() => {
    setLoadingState('loaded');
    onLoadComplete?.();
  }, [onLoadComplete]);

  const handleError = useCallback(() => {
    setLoadingState('error');
  }, []);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${className}`}
      style={{
        aspectRatio: `${width}/${height}`,
        backgroundColor: dominantColor,
      }}
    >
      {/* Blur placeholder — always rendered, fades out */}
      {blurDataURL && (
        <div
          className="absolute inset-0 transition-opacity duration-700 ease-out"
          style={{
            opacity: loadingState === 'loaded' ? 0 : 1,
            backgroundImage: `url(${blurDataURL})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: 'blur(20px)',
            transform: 'scale(1.1)', // hide blur edges
          }}
          aria-hidden="true"
        />
      )}

      {/* Actual image — loaded when in view */}
      {(isInView || priority) && (
        <Image
          src={src}
          alt={alt}
          width={width}
          height={height}
          sizes={sizes}
          quality={quality}
          priority={priority}
          loading={priority ? 'eager' : 'lazy'}
          onLoad={handleLoad}
          onError={handleError}
          className={`
            absolute inset-0 w-full h-full object-cover
            transition-opacity duration-500 ease-in
            ${loadingState === 'loaded' ? 'opacity-100' : 'opacity-0'}
          `}
        />
      )}

      {/* Error state */}
      {loadingState === 'error' && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="text-center text-gray-400">
            <svg
              className="mx-auto h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5"
              />
            </svg>
            <p className="mt-2 text-sm">Failed to load image</p>
          </div>
        </div>
      )}

      {/* Loading skeleton animation */}
      {loadingState === 'loading' && (
        <div
          className="absolute inset-0 animate-pulse bg-gradient-to-r from-transparent via-white/20 to-transparent"
          style={{ animationDuration: '1.5s' }}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
```

**Usage in a news article**:

```tsx
// app/articles/[slug]/page.tsx
import { ProgressiveImage } from '@/components/progressive-image';

interface Article {
  title: string;
  heroImage: {
    url: string;
    width: number;
    height: number;
    blurDataURL: string;
    dominantColor: string;
  };
  body: Array<{
    type: 'paragraph' | 'image';
    content?: string;
    image?: {
      url: string;
      width: number;
      height: number;
      blurDataURL: string;
      dominantColor: string;
      caption: string;
    };
  }>;
}

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article: Article = await fetch(`https://cms.example.com/articles/${slug}`, {
    next: { revalidate: 300 },
  }).then((r) => r.json());

  return (
    <article className="max-w-3xl mx-auto px-4">
      <h1 className="text-4xl font-bold mt-8 mb-6">{article.title}</h1>

      {/* Hero image — priority load with blur transition */}
      <ProgressiveImage
        src={article.heroImage.url}
        alt={article.title}
        width={article.heroImage.width}
        height={article.heroImage.height}
        blurDataURL={article.heroImage.blurDataURL}
        dominantColor={article.heroImage.dominantColor}
        sizes="(max-width: 768px) 100vw, 768px"
        priority
        className="rounded-xl"
        quality={85}
      />

      {/* Article body with inline images */}
      {article.body.map((block, i) => {
        if (block.type === 'paragraph') {
          return <p key={i} className="my-4 text-lg leading-relaxed">{block.content}</p>;
        }
        if (block.type === 'image' && block.image) {
          return (
            <figure key={i} className="my-8">
              <ProgressiveImage
                src={block.image.url}
                alt={block.image.caption}
                width={block.image.width}
                height={block.image.height}
                blurDataURL={block.image.blurDataURL}
                dominantColor={block.image.dominantColor}
                sizes="(max-width: 768px) 100vw, 768px"
                className="rounded-lg"
              />
              <figcaption className="mt-2 text-center text-sm text-gray-500">
                {block.image.caption}
              </figcaption>
            </figure>
          );
        }
        return null;
      })}
    </article>
  );
}
```

The three-stage progressive loading (color → blur → sharp) provides a polished experience. The intersection observer with 200px rootMargin starts loading images just before they scroll into view. The CSS transitions create smooth blur-to-sharp animations.

---

## Q17. (Advanced) How do you handle image optimization at the edge with middleware and dynamic OG images in Next.js?

**Scenario**: You need to generate dynamic Open Graph images for social sharing (each blog post gets a unique preview image) and apply image transformations at the edge for a global audience.

**Answer**:

Next.js supports **dynamic OG image generation** via the `ImageResponse` API from `next/og` (built on Satori and Resvg) and edge-based image transformations through middleware.

**Dynamic OG Image Generation**:

```tsx
// app/blog/[slug]/opengraph-image.tsx
import { ImageResponse } from 'next/og';

// Route segment config
export const runtime = 'edge';
export const alt = 'Blog post preview';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default async function OGImage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Fetch post data (edge-compatible fetch)
  const post = await fetch(`https://api.example.com/posts/${slug}`).then((r) =>
    r.json()
  );

  // Load font for the OG image
  const interBold = await fetch(
    new URL('../../../public/fonts/Inter-Bold.ttf', import.meta.url)
  ).then((res) => res.arrayBuffer());

  const interRegular = await fetch(
    new URL('../../../public/fonts/Inter-Regular.ttf', import.meta.url)
  ).then((res) => res.arrayBuffer());

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '60px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          fontFamily: 'Inter',
        }}
      >
        {/* Category badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '18px',
            }}
          >
            {post.category}
          </div>
          <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '18px' }}>
            {new Date(post.publishedAt).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </div>
        </div>

        {/* Title */}
        <div
          style={{
            fontSize: '56px',
            fontWeight: 700,
            color: 'white',
            lineHeight: 1.2,
            maxWidth: '900px',
          }}
        >
          {post.title}
        </div>

        {/* Author and site */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={post.author.avatarUrl}
              alt=""
              width={48}
              height={48}
              style={{ borderRadius: '50%' }}
            />
            <div style={{ color: 'white', fontSize: '20px' }}>
              {post.author.name}
            </div>
          </div>
          <div
            style={{
              color: 'rgba(255,255,255,0.8)',
              fontSize: '20px',
              fontWeight: 700,
            }}
          >
            yourblog.com
          </div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: 'Inter', data: interBold, weight: 700, style: 'normal' },
        { name: 'Inter', data: interRegular, weight: 400, style: 'normal' },
      ],
    }
  );
}
```

**Edge Middleware for Image Transformations**:

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;

  // Handle image transformation requests: /images/transform/*
  if (pathname.startsWith('/images/transform/')) {
    const imagePath = pathname.replace('/images/transform/', '');
    const width = searchParams.get('w') || '800';
    const quality = searchParams.get('q') || '80';
    const format = searchParams.get('f') || 'auto';

    // Detect client hints for optimal format
    const acceptHeader = request.headers.get('Accept') || '';
    let optimalFormat = 'jpeg';
    if (acceptHeader.includes('image/avif')) optimalFormat = 'avif';
    else if (acceptHeader.includes('image/webp')) optimalFormat = 'webp';

    // Rewrite to CDN transformation URL
    const cdnUrl = new URL(
      `https://cdn.example.com/transform/${imagePath}`
    );
    cdnUrl.searchParams.set('w', width);
    cdnUrl.searchParams.set('q', quality);
    cdnUrl.searchParams.set('f', format === 'auto' ? optimalFormat : format);

    const response = NextResponse.rewrite(cdnUrl);

    // Set aggressive cache headers
    response.headers.set(
      'Cache-Control',
      'public, max-age=31536000, immutable'
    );
    response.headers.set('Vary', 'Accept'); // Vary by format support

    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/images/transform/:path*'],
};
```

**Dynamic OG image with cached variants**:

```tsx
// app/api/og/route.tsx
import { ImageResponse } from 'next/og';
import { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const title = searchParams.get('title') || 'Default Title';
  const theme = searchParams.get('theme') || 'dark';

  const bgColor = theme === 'dark' ? '#1a1a2e' : '#ffffff';
  const textColor = theme === 'dark' ? '#ffffff' : '#1a1a2e';

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: bgColor,
          padding: '48px',
        }}
      >
        <h1
          style={{
            fontSize: '64px',
            color: textColor,
            textAlign: 'center',
            lineHeight: 1.3,
          }}
        >
          {title}
        </h1>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      headers: {
        'Cache-Control': 'public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800',
      },
    }
  );
}
```

**Metadata integration**:

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from 'next';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await fetch(`https://api.example.com/posts/${slug}`).then((r) =>
    r.json()
  );

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: 'article',
      publishedTime: post.publishedAt,
      authors: [post.author.name],
      // OG image auto-discovered from opengraph-image.tsx
      // OR use the API route for more control:
      images: [
        {
          url: `/api/og?title=${encodeURIComponent(post.title)}&theme=dark`,
          width: 1200,
          height: 630,
          alt: post.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
    },
  };
}
```

The `opengraph-image.tsx` convention auto-generates OG images per route without needing manual metadata. The edge middleware pattern enables global image transformation with CDN caching.

---

## Q18. (Advanced) How do you prevent CLS (Cumulative Layout Shift) comprehensively across images, fonts, and dynamic content in Next.js?

**Scenario**: Your e-commerce site has a CLS score of 0.25 (poor). The three main culprits are: images loading without reserved space, font swaps shifting layout, and dynamically injected ads/banners. Target: CLS < 0.1 (good).

**Answer**:

CLS prevention requires addressing every source of layout shift. Here's a systematic approach covering images, fonts, and dynamic content:

```
CLS Sources and Solutions:
┌────────────────────────┬────────────────────────────────────────┐
│  CLS Source             │  Solution                              │
├────────────────────────┼────────────────────────────────────────┤
│  Images without dims   │  next/image (width/height required)    │
│  Font swap              │  next/font (size-adjust metrics)       │
│  Late-loaded ads        │  CSS min-height + contain: layout     │
│  Dynamic banners        │  Skeleton placeholders                 │
│  Async component insert │  CSS aspect-ratio + Suspense          │
│  FOUC (flash)           │  Critical CSS inline                   │
└────────────────────────┴────────────────────────────────────────┘
```

**1. Image CLS prevention**:

```tsx
// ✅ next/image always prevents CLS (width/height required)
import Image from 'next/image';

function ProductCard({ product }: { product: Product }) {
  return (
    <div className="w-full">
      {/* Fixed aspect ratio container for fill mode */}
      <div className="relative aspect-square">
        <Image
          src={product.image}
          alt={product.name}
          fill
          sizes="(max-width: 640px) 100vw, 25vw"
          className="object-cover"
        />
      </div>
      <h3>{product.name}</h3>
    </div>
  );
}

// For user-generated content where dimensions are unknown
function UserImage({ url }: { url: string }) {
  return (
    // aspect-ratio CSS prevents CLS even before image loads
    <div className="w-full" style={{ aspectRatio: '16/9' }}>
      <Image
        src={url}
        alt="User uploaded content"
        fill
        sizes="100vw"
        className="object-cover"
      />
    </div>
  );
}
```

**2. Font CLS prevention**:

```tsx
// app/fonts.ts
import { Inter } from 'next/font/google';
import localFont from 'next/font/local';

// next/font auto-generates size-adjust to match fallback metrics
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  adjustFontFallback: true, // default — computes CLS-preventing overrides
});

// For custom fonts, provide the fallback to match against
const customFont = localFont({
  src: '../fonts/Custom-Variable.woff2',
  display: 'swap',
  adjustFontFallback: 'Times New Roman', // match metrics against this fallback
});
```

**3. Ad slot CLS prevention**:

```tsx
// components/ad-slot.tsx
'use client';

import { useEffect, useRef, useState } from 'react';

interface AdSlotProps {
  slotId: string;
  format: 'banner' | 'rectangle' | 'leaderboard' | 'skyscraper';
}

const adDimensions = {
  banner: { width: 468, height: 60 },
  rectangle: { width: 300, height: 250 },
  leaderboard: { width: 728, height: 90 },
  skyscraper: { width: 160, height: 600 },
};

export function AdSlot({ slotId, format }: AdSlotProps) {
  const [adLoaded, setAdLoaded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const dims = adDimensions[format];

  useEffect(() => {
    // Load ad into the pre-sized container
    if (typeof window !== 'undefined' && window.googletag) {
      window.googletag.cmd.push(() => {
        window.googletag.display(slotId);
        setAdLoaded(true);
      });
    }
  }, [slotId]);

  return (
    <div
      ref={containerRef}
      id={slotId}
      className="mx-auto bg-gray-50 flex items-center justify-center"
      style={{
        // Pre-reserve EXACT space — critical for CLS prevention
        width: dims.width,
        height: dims.height,
        minHeight: dims.height,
        contain: 'layout size', // prevent internal changes from affecting layout
        contentVisibility: 'auto',
      }}
    >
      {!adLoaded && (
        <span className="text-xs text-gray-300">Advertisement</span>
      )}
    </div>
  );
}
```

**4. Dynamic banner/notification CLS prevention**:

```tsx
// components/promo-banner.tsx
'use client';

import { useState, useEffect } from 'react';

export function PromoBanner() {
  const [banner, setBanner] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    fetch('/api/active-promotion')
      .then((r) => r.json())
      .then((data) => setBanner(data.message))
      .catch(() => {});
  }, []);

  if (dismissed) return null;

  return (
    // FIXED height prevents CLS — always reserves space
    <div
      className="h-10 bg-blue-600 text-white flex items-center justify-center text-sm overflow-hidden"
      style={{ contain: 'layout' }}
    >
      {banner ? (
        <div className="flex items-center gap-4">
          <span>{banner}</span>
          <button
            onClick={() => setDismissed(true)}
            className="text-white/80 hover:text-white"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      ) : (
        // Invisible placeholder maintains height
        <span className="invisible">placeholder</span>
      )}
    </div>
  );
}
```

**5. Streaming/Suspense CLS prevention**:

```tsx
// app/products/page.tsx
import { Suspense } from 'react';

function ProductListSkeleton() {
  return (
    <div className="grid grid-cols-4 gap-6">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="animate-pulse">
          {/* EXACT same dimensions as real content */}
          <div className="aspect-square bg-gray-200 rounded-lg" />
          <div className="h-5 bg-gray-200 rounded mt-3 w-3/4" />
          <div className="h-4 bg-gray-200 rounded mt-2 w-1/2" />
        </div>
      ))}
    </div>
  );
}

export default function ProductsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Products</h1>
      <Suspense fallback={<ProductListSkeleton />}>
        <ProductList />
      </Suspense>
    </div>
  );
}
```

**CLS monitoring in production**:

```tsx
// components/cls-monitor.tsx
'use client';

import { useEffect } from 'react';

export function CLSMonitor() {
  useEffect(() => {
    let clsValue = 0;
    const clsEntries: PerformanceEntry[] = [];

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const layoutShift = entry as any;
        if (!layoutShift.hadRecentInput) {
          clsValue += layoutShift.value;
          clsEntries.push(entry);
        }
      }
    });

    observer.observe({ type: 'layout-shift', buffered: true });

    // Report on page hide
    const reportCLS = () => {
      if (clsValue > 0.1) {
        console.warn(`[CLS] Poor CLS: ${clsValue.toFixed(3)}`);
        // Send to analytics
        fetch('/api/vitals', {
          method: 'POST',
          body: JSON.stringify({ metric: 'CLS', value: clsValue }),
          keepalive: true,
        });
      }
    };

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') reportCLS();
    });

    return () => observer.disconnect();
  }, []);

  return null;
}
```

Achieving CLS < 0.1 requires: reserving space for every element that loads asynchronously, using `next/image` and `next/font` for automatic CLS prevention, using `contain: layout` for third-party injections, and matching skeleton dimensions to real content.

---

## Q19. (Advanced) How do you implement image optimization for a headless CMS (Contentful/Sanity/Strapi) with `next/image` in production?

**Scenario**: Your marketing site uses Sanity as the headless CMS. Editors upload images of varying sizes and formats. You need `next/image` to work seamlessly with Sanity's image CDN while supporting blur placeholders, responsive sizes, and hotspot/crop metadata.

**Answer**:

Each headless CMS has its own image transformation API. The key is building a custom loader that maps `next/image` props to the CMS's URL parameters.

**Sanity.io Integration**:

```tsx
// lib/sanity-image.ts
import imageUrlBuilder from '@sanity/image-url';
import type { SanityImageSource } from '@sanity/image-url/lib/types/types';
import { client } from './sanity-client';
import type { ImageLoaderProps } from 'next/image';

const builder = imageUrlBuilder(client);

// Type-safe image reference
interface SanityImage {
  _type: 'image';
  asset: {
    _ref: string;
    _type: 'reference';
  };
  hotspot?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  crop?: {
    top: number;
    bottom: number;
    left: number;
    right: number;
  };
}

// Generate full URL from Sanity image reference
export function urlFor(source: SanityImageSource) {
  return builder.image(source);
}

// Custom loader for next/image
export function sanityImageLoader({ src, width, quality }: ImageLoaderProps): string {
  // src is the Sanity image URL
  const url = new URL(src);
  url.searchParams.set('w', width.toString());
  url.searchParams.set('q', (quality || 80).toString());
  url.searchParams.set('auto', 'format'); // auto AVIF/WebP
  url.searchParams.set('fit', 'max');
  return url.toString();
}

// Get image dimensions from Sanity asset reference
export async function getImageDimensions(
  image: SanityImage
): Promise<{ width: number; height: number }> {
  const ref = image.asset._ref;
  // Format: image-<id>-<width>x<height>-<format>
  const [, , dimensions] = ref.split('-');
  const [width, height] = dimensions.split('x').map(Number);

  // Apply crop if present
  if (image.crop) {
    const croppedWidth = Math.round(
      width * (1 - image.crop.left - image.crop.right)
    );
    const croppedHeight = Math.round(
      height * (1 - image.crop.top - image.crop.bottom)
    );
    return { width: croppedWidth, height: croppedHeight };
  }

  return { width, height };
}

// Generate blur data URL from Sanity's LQIP
export function getSanityBlurUrl(image: SanityImage): string {
  return urlFor(image).width(20).quality(20).blur(50).url();
}
```

**Sanity Image Component**:

```tsx
// components/sanity-image.tsx
import Image from 'next/image';
import { urlFor, sanityImageLoader, getImageDimensions, getSanityBlurUrl } from '@/lib/sanity-image';
import type { SanityImageSource } from '@sanity/image-url/lib/types/types';

interface SanityImageProps {
  image: SanityImageSource & {
    asset: { _ref: string };
    hotspot?: { x: number; y: number };
    crop?: { top: number; bottom: number; left: number; right: number };
    alt?: string;
  };
  alt?: string;
  sizes?: string;
  priority?: boolean;
  fill?: boolean;
  className?: string;
}

export async function SanityImage({
  image,
  alt,
  sizes = '100vw',
  priority = false,
  fill = false,
  className,
}: SanityImageProps) {
  const imageUrl = urlFor(image).url();
  const dimensions = await getImageDimensions(image);
  const blurUrl = getSanityBlurUrl(image);

  // Compute object-position from hotspot
  const objectPosition = image.hotspot
    ? `${image.hotspot.x * 100}% ${image.hotspot.y * 100}%`
    : 'center';

  if (fill) {
    return (
      <Image
        loader={sanityImageLoader}
        src={imageUrl}
        alt={alt || image.alt || ''}
        fill
        sizes={sizes}
        priority={priority}
        placeholder="blur"
        blurDataURL={blurUrl}
        className={className}
        style={{ objectPosition }}
      />
    );
  }

  return (
    <Image
      loader={sanityImageLoader}
      src={imageUrl}
      alt={alt || image.alt || ''}
      width={dimensions.width}
      height={dimensions.height}
      sizes={sizes}
      priority={priority}
      placeholder="blur"
      blurDataURL={blurUrl}
      className={className}
      style={{ objectPosition }}
    />
  );
}
```

**Contentful Integration**:

```tsx
// lib/contentful-image.ts
import type { ImageLoaderProps } from 'next/image';

interface ContentfulAsset {
  fields: {
    file: {
      url: string;
      details: {
        image: { width: number; height: number };
        size: number;
      };
      contentType: string;
    };
    title: string;
    description: string;
  };
}

export function contentfulImageLoader({ src, width, quality }: ImageLoaderProps): string {
  // Contentful Images API
  const url = new URL(`https:${src}`);
  url.searchParams.set('w', width.toString());
  url.searchParams.set('q', (quality || 80).toString());
  url.searchParams.set('fm', 'webp'); // Contentful doesn't auto-negotiate format
  url.searchParams.set('fit', 'fill');
  return url.toString();
}

export function getContentfulImageProps(asset: ContentfulAsset) {
  return {
    src: asset.fields.file.url,
    width: asset.fields.file.details.image.width,
    height: asset.fields.file.details.image.height,
    alt: asset.fields.description || asset.fields.title,
    blurDataURL: `https:${asset.fields.file.url}?w=10&q=10&fm=webp`,
  };
}
```

**Usage in page components**:

```tsx
// app/blog/[slug]/page.tsx
import { SanityImage } from '@/components/sanity-image';
import { getPost } from '@/lib/sanity-queries';

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);

  return (
    <article className="max-w-4xl mx-auto">
      {/* Hero with hotspot-aware cropping */}
      <div className="relative aspect-[21/9] rounded-2xl overflow-hidden">
        <SanityImage
          image={post.heroImage}
          alt={post.title}
          sizes="(max-width: 768px) 100vw, 896px"
          priority
          fill
          className="object-cover"
        />
      </div>

      <h1 className="text-4xl font-bold mt-8">{post.title}</h1>

      {/* Portable Text with inline images */}
      {post.body.map((block: any, i: number) => {
        if (block._type === 'image') {
          return (
            <figure key={i} className="my-8">
              <SanityImage
                image={block}
                sizes="(max-width: 768px) 100vw, 768px"
                className="rounded-lg"
              />
              {block.caption && (
                <figcaption className="text-center text-sm text-gray-500 mt-2">
                  {block.caption}
                </figcaption>
              )}
            </figure>
          );
        }
        return null;
      })}
    </article>
  );
}
```

**next.config.ts for CMS image domains**:

```ts
// next.config.ts
const nextConfig = {
  images: {
    remotePatterns: [
      // Sanity CDN
      { protocol: 'https', hostname: 'cdn.sanity.io' },
      // Contentful CDN
      { protocol: 'https', hostname: 'images.ctfassets.net' },
      // Strapi
      { protocol: 'https', hostname: 'your-strapi.s3.amazonaws.com' },
    ],
    // Use CDN's optimization instead of Next.js built-in
    loader: 'custom',
    loaderFile: './lib/sanity-image.ts',
  },
};
```

This integration provides: CDN-based image transformation (no load on Next.js server), hotspot-aware cropping, automatic format negotiation, blur placeholders from CMS, and type-safe image handling with full CMS metadata.

---

## Q20. (Advanced) How do you audit and optimize the complete asset loading waterfall (images, fonts, scripts) in a Next.js application for production?

**Scenario**: You're preparing a Next.js application for a production launch. Lighthouse scores are 65 for Performance. You need to audit the entire asset loading pipeline and create a systematic optimization plan to reach 95+.

**Answer**:

A production asset audit involves analyzing the loading waterfall, identifying bottlenecks, and applying optimizations across all asset types in priority order.

**Phase 1: Audit — Map the current loading waterfall**:

```
Current Waterfall (before optimization):
Time ──────────────────────────────────────────────────────────▶

HTML  ████ (200ms)
CSS   ░░░░████████ (300ms parse-blocking)
Fonts ░░░░░░░░░░████████████████ (800ms — external Google Fonts!)
JS    ░░░░████████████████████████████ (1.2s — large bundle)
GTM   ░░░░░░░░░░░░░░░░████████████ (500ms — render blocking!)
Hero  ░░░░░░░░░░░░░░░░░░░░░░░░████████████████ (1.5s — late!)
LCP   ─────────────────────────────────────────── 3.2s (POOR)
```

```tsx
// scripts/audit-assets.ts — Automated asset audit
// Run: npx tsx scripts/audit-assets.ts

import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

interface AssetAudit {
  type: 'image' | 'font' | 'script' | 'css';
  path: string;
  sizeKB: number;
  issue?: string;
  recommendation?: string;
}

function auditBuildOutput(): AssetAudit[] {
  const audits: AssetAudit[] = [];
  const buildDir = join(process.cwd(), '.next');

  // Audit static assets
  function walkDir(dir: string) {
    try {
      const files = readdirSync(dir);
      for (const file of files) {
        const fullPath = join(dir, file);
        const stat = statSync(fullPath);
        if (stat.isDirectory()) {
          walkDir(fullPath);
        } else {
          const sizeKB = Math.round(stat.size / 1024);
          const ext = file.split('.').pop()?.toLowerCase();

          // Images
          if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(ext || '')) {
            const audit: AssetAudit = {
              type: 'image',
              path: fullPath,
              sizeKB,
            };
            if (ext === 'png' && sizeKB > 100) {
              audit.issue = 'Large PNG — consider WebP/AVIF';
            }
            if (ext === 'gif' && sizeKB > 500) {
              audit.issue = 'Large GIF — consider video/WebM';
            }
            if (ext === 'svg' && sizeKB > 20) {
              audit.issue = 'Large SVG — consider optimizing with SVGO';
            }
            audits.push(audit);
          }

          // Fonts
          if (['woff', 'woff2', 'ttf', 'otf'].includes(ext || '')) {
            const audit: AssetAudit = {
              type: 'font',
              path: fullPath,
              sizeKB,
            };
            if (ext === 'ttf' || ext === 'otf') {
              audit.issue = 'Uncompressed font format';
              audit.recommendation = 'Convert to WOFF2';
            }
            if (sizeKB > 200) {
              audit.issue = 'Large font file — check subsetting';
            }
            audits.push(audit);
          }

          // JS bundles
          if (ext === 'js' && sizeKB > 100) {
            audits.push({
              type: 'script',
              path: fullPath,
              sizeKB,
              issue: sizeKB > 250 ? 'Bundle > 250KB — consider code splitting' : undefined,
            });
          }
        }
      }
    } catch {
      // skip
    }
  }

  walkDir(join(buildDir, 'static'));
  return audits;
}

const results = auditBuildOutput();
console.table(results.filter((r) => r.issue));
```

**Phase 2: Optimize — Apply fixes in priority order**:

```tsx
// next.config.ts — Production-optimized configuration
import type { NextConfig } from 'next';
import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 365, // 1 year
    remotePatterns: [
      { protocol: 'https', hostname: 'cdn.example.com' },
    ],
  },

  // Reduce JS bundle size
  experimental: {
    optimizePackageImports: [
      'lucide-react',
      '@heroicons/react',
      'date-fns',
      'lodash-es',
      'recharts',
    ],
    nextScriptWorkers: true, // Enable worker strategy
  },

  // Compression
  compress: true,

  // Headers for optimal caching
  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/fonts/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);
```

**Phase 3: Optimized layout with all best practices**:

```tsx
// app/layout.tsx — Production-optimized root layout
import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import Script from 'next/script';
import { CLSMonitor } from '@/components/cls-monitor';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  preload: true,
});

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
  ],
};

export const metadata: Metadata = {
  title: {
    default: 'My App',
    template: '%s | My App',
  },
  description: 'Production-optimized Next.js application',
  metadataBase: new URL('https://example.com'),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        {/* Preconnect to critical origins */}
        <link rel="preconnect" href="https://cdn.example.com" />
        <link rel="dns-prefetch" href="https://www.googletagmanager.com" />
      </head>
      <body className={`${inter.className} antialiased`}>
        {children}

        {/* Analytics — after interactive, won't block */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"
          strategy="worker"
        />

        {/* Chat widget — lazy, loads during idle */}
        <Script
          src="https://widget.intercom.io/widget/abc123"
          strategy="lazyOnload"
        />

        {/* CLS monitoring in production */}
        {process.env.NODE_ENV === 'production' && <CLSMonitor />}
      </body>
    </html>
  );
}
```

**Phase 4: Verify — Optimized loading waterfall**:

```
Optimized Waterfall (after):
Time ──────────────────────────────────────────────────────────▶

HTML  ██ (100ms — streaming SSR)
CSS   ░██ (50ms — critical CSS inlined)
Fonts ░░██ (80ms — self-hosted, preloaded via next/font)
Hero  ░░██████ (300ms — priority + preload + AVIF + CDN)
JS    ░░░░░░████████ (400ms — code-split, tree-shaken)
LCP   ─────────────── 0.8s (GOOD ✅)

GTM   [runs in Web Worker — doesn't affect main thread]
Chat  [loads during idle — doesn't affect any metric]
```

**Phase 5: Continuous monitoring**:

```tsx
// app/api/vitals/route.ts
import { NextRequest, NextResponse } from 'next/server';

interface WebVital {
  name: 'LCP' | 'CLS' | 'INP' | 'FCP' | 'TTFB';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  pathname: string;
}

export async function POST(request: NextRequest) {
  const vital: WebVital = await request.json();

  // Log to your monitoring service
  console.log(`[Web Vital] ${vital.name}: ${vital.value} (${vital.rating}) on ${vital.pathname}`);

  // Send to analytics backend
  await fetch('https://analytics.example.com/vitals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...vital,
      timestamp: Date.now(),
      userAgent: request.headers.get('user-agent'),
    }),
  });

  return NextResponse.json({ ok: true });
}
```

```tsx
// components/web-vitals-reporter.tsx
'use client';

import { useReportWebVitals } from 'next/web-vitals';

export function WebVitalsReporter() {
  useReportWebVitals((metric) => {
    const rating =
      metric.rating || (metric.value < getThreshold(metric.name) ? 'good' : 'poor');

    // Only report poor/needs-improvement to reduce noise
    if (rating !== 'good') {
      fetch('/api/vitals', {
        method: 'POST',
        body: JSON.stringify({
          name: metric.name,
          value: Math.round(metric.value),
          rating,
          pathname: window.location.pathname,
        }),
        keepalive: true,
      });
    }
  });

  return null;
}

function getThreshold(name: string): number {
  const thresholds: Record<string, number> = {
    LCP: 2500,
    CLS: 0.1,
    INP: 200,
    FCP: 1800,
    TTFB: 800,
  };
  return thresholds[name] || 0;
}
```

**Complete optimization checklist**:

```
Images:
  ✅ All images use next/image
  ✅ Hero/LCP images have priority={true}
  ✅ sizes prop matches actual rendered size
  ✅ AVIF/WebP enabled (formats config)
  ✅ CDN with edge caching (minimumCacheTTL)
  ✅ Blur placeholders for visible images
  ✅ quality set appropriately (75-85)

Fonts:
  ✅ next/font for all fonts (zero CLS)
  ✅ Only needed weights/subsets loaded
  ✅ Variable fonts where possible
  ✅ Preload only above-fold fonts
  ✅ font-display: swap configured

Scripts:
  ✅ Analytics uses worker/afterInteractive
  ✅ Non-critical scripts use lazyOnload
  ✅ No render-blocking third-party scripts
  ✅ Consent-gated for GDPR compliance

Bundle:
  ✅ optimizePackageImports configured
  ✅ Bundle analyzed (ANALYZE=true)
  ✅ No unused dependencies
  ✅ Dynamic imports for heavy components

Caching:
  ✅ Immutable cache headers for static assets
  ✅ Preconnect to critical origins
  ✅ Service worker for repeat visits (optional)

Monitoring:
  ✅ Web Vitals reported to analytics
  ✅ CLS monitoring active
  ✅ Performance budget alerts configured
```

---
