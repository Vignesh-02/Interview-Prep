# 25. Performance, Web Vitals & Monitoring

## Topic Introduction

**Performance** in Next.js 15/16 covers **Core Web Vitals** (LCP, FID/INP, CLS), **streaming**, **caching**, **bundle size**, and **observability** (e.g. Vercel Analytics, Sentry, custom RUM). Senior developers use **next/image**, **next/script**, **Suspense**, and **analyzer** tools, and know how to interpret **Lighthouse** and **Real User Monitoring** to fix regressions.

```
Performance levers:
┌─────────────────────────────────────────────────────────────┐
│  Server: Streaming, parallel fetch, cache(), revalidate      │
│  Client: Code split, lazy load, minimize "use client"         │
│  Assets: next/image, next/font, next/script strategy          │
│  Measure: LCP, INP, CLS, TTFB, FCP, TTI                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Q1. (Beginner) What are Core Web Vitals and which ones does Next.js help with?

**Answer**:

- **LCP (Largest Contentful Paint)**: Loading performance. Next.js helps with SSR/streaming, **next/image** (priority for LCP image), and **next/font** to avoid layout shift.
- **INP (Interaction to Next Paint)**: Responsiveness. Next.js helps by reducing JS (Server Components) and code splitting so the main thread isn’t blocked.
- **CLS (Cumulative Layout Shift)**: Visual stability. Use **next/image** (dimensions), **next/font**, and reserve space for dynamic content.

---

## Q2. (Beginner) How do you use next/image to improve LCP and avoid CLS?

**Scenario**: Hero image is the LCP element; it should load fast and not shift layout.

**Answer**:

- Use **next/image** with **width** and **height** (or **fill** with a sized container) so layout doesn’t shift.
- Set **priority** for the LCP image so it preloads and isn’t lazy-loaded.
- Use **sizes** so the correct resolution is loaded (e.g. `sizes="(max-width: 768px) 100vw, 50vw"`).

```tsx
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={630}
  priority
  sizes="100vw"
/>
```

---

## Q3. (Beginner) What is the purpose of next/script and the strategy option (beforeInteractive, afterInteractive, lazyOnload)?

**Answer**:

**next/script** loads third-party scripts in a controlled way so they don’t block the main thread as much.

- **beforeInteractive**: Injected before any Next.js code; use for critical scripts (e.g. bot detection). Rare.
- **afterInteractive** (default): After page becomes interactive. Good for analytics, chat.
- **lazyOnload**: After load event (during idle). Good for non-critical ads, social widgets.

Use **lazyOnload** when possible to improve LCP and INP.

---

## Q4. (Beginner) How do you find which JavaScript is slowing down the page (e.g. bundle size)?

**Answer**:

- **@next/bundle-analyzer**: Run `ANALYZE=true next build` to get a treemap of client bundles. Find large dependencies and replace or dynamic-import them.
- **Lighthouse**: "Reduce JavaScript execution time" and "Opportunities" suggest what to fix.
- **Next.js build output**: Shows first-load JS size per route; focus on the largest routes.

---

## Q5. (Beginner) What is the difference between TTFB, FCP, LCP, and TTI?

**Answer**:

- **TTFB (Time to First Byte)**: When the server sends the first byte. Affected by server, cache, and network.
- **FCP (First Contentful Paint)**: When the first content (e.g. text or image) is painted. Affected by HTML size, critical CSS, and blocking scripts.
- **LCP**: When the largest content element is painted. Key for "feels fast."
- **TTI (Time to Interactive)**: When the page is fully interactive (main thread free). Affected by JS execution and hydration.

Next.js improves TTFB/FCP/LCP with streaming and SSR; TTI improves with less client JS (Server Components) and code splitting.

---

## Q6. (Intermediate) How do you integrate Real User Monitoring (RUM) or Web Vitals reporting in a Next.js app?

**Scenario**: You want to send LCP, INP, CLS to your analytics.

**Answer**:

Use **web-vitals** and report in a Client Component (e.g. in root layout’s client child or a dedicated script).

```tsx
'use client';
import { useReportWebVitals } from 'next/web-vitals';

export function WebVitalsReporter() {
  useReportWebVitals((metric) => {
    // Send to your analytics
    analytics.track(metric.name, {
      value: metric.value,
      id: metric.id,
      label: metric.label,
    });
  });
  return null;
}
```

Add **WebVitalsReporter** in the root layout (inside a Client boundary). For **next/analytics**, Vercel’s package does this automatically when deployed on Vercel.

---

## Q7. (Intermediate) Production scenario: LCP regressed after a deploy. Walk through a systematic debugging process.

**Answer**:

1. **Confirm**: Check RUM or Lighthouse for the new LCP value and which element is LCP.
2. **Caching**: Did cache headers or CDN change? Check TTFB; if TTFB increased, fix caching or origin.
3. **LCP element**: Is it an image? Ensure **next/image** with **priority** and **sizes**; ensure image isn’t hidden by CSS or below the fold so the browser picks a later element.
4. **Blocking**: New render-blocking script or large sync JS? Use **next/script** with **lazyOnload** or defer.
5. **Streaming**: Did a slow Server Component block the shell? Wrap slow parts in **Suspense** so the shell (and LCP) can paint first.
6. **Revert**: If possible, bisect deploy to find the change that caused the regression.

---

## Q8. (Intermediate) How do you use React Profiler or Chrome DevTools to find why a Client Component is slow to interact?

**Answer**:

- **React DevTools Profiler**: Record a session, interact with the page, and see which components took long to render. Focus on expensive re-renders and long commit phases.
- **Chrome Performance**: Record, find long tasks on the main thread, and see which scripts run. Reduce work (e.g. break up long lists with virtualization, defer non-critical JS).
- **React**: Use **memo**, **useMemo**, **useCallback** where appropriate; avoid putting huge lists in state that change often.

---

## Q9. (Intermediate) What is the effect of too many "use client" boundaries on TTI and bundle size?

**Answer**:

Every **"use client"** boundary pulls that module and its dependencies into the client bundle. Many boundaries high in the tree mean a lot of JS is shipped and executed before the page is interactive (TTI worsens). **Fix**: Push **"use client"** to the leaves; keep as much as possible as Server Components so they add zero client JS.

---

## Q10. (Intermediate) How do you lazy-load a heavy Client Component (e.g. a chart) so it doesn’t block initial paint?

**Answer**:

Use **dynamic** import with **ssr: false** if the component doesn’t need to be server-rendered, and a **loading** fallback to reserve space (avoid CLS).

```tsx
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('@/components/Chart'), {
  ssr: false,
  loading: () => <div className="h-[400px] animate-pulse bg-gray-100" />,
});
```

---

## Q11. (Intermediate) Configure Next.js to emit a performance budget (fail build if bundle exceeds X KB).

**Answer**:

Next.js doesn’t have built-in bundle budgets. Use **@next/bundle-analyzer** in a custom script that parses build output or the analyzer JSON and fails if size > threshold. Or use a **Lighthouse CI** step in your pipeline that fails if LCP or total blocking time exceeds a limit.

---

## Q12. (Intermediate) Find the bug: LCP is good in Lighthouse but poor in the field (RUM).

**Scenario**: Lab and production differ.

**Answer**:

- **Device/network**: Real users are on slower devices and networks; lab is often fast. Test with Lighthouse "Slow 4G" and "Mobile" to approximate.
- **Caching**: Lab might hit cache; real users might get cold cache or different CDN nodes.
- **Third parties**: RUM includes third-party scripts and ads that don’t run in Lighthouse. Defer or remove non-critical third parties.
- **LCP element**: In the field, the LCP element might be different (e.g. a late ad). Use **content-visibility** or ensure the main content is the LCP; avoid large below-the-fold images being reported as LCP.

---

## Q13. (Advanced) How do you use Sentry (or similar) to trace a request from the client through Server Components and Server Actions?

**Scenario**: You want one trace for "submit form" that includes client, Server Action, and DB.

**Answer**:

- **Sentry**: Use the Next.js SDK (e.g. **@sentry/nextjs**) which instruments server and client. Create a **transaction** or **span** on the client when the user submits; propagate **trace id** (e.g. in headers or in the Server Action call). On the server, continue the trace (same trace id) in the Server Action and in any downstream calls. Sentry’s Next.js integration can do this automatically for fetch and Server Actions if configured.
- **OpenTelemetry**: Instrument the app with OTel; use a distributed tracer that supports Next.js (e.g. Vercel’s integration or a custom wrapper) so one trace links client span, Server Action span, and DB span.

---

## Q14. (Advanced) Next.js 15 vs 16: What performance-related changes should you expect?

**Answer**:

- **Next.js 16**: **Turbopack** as default for production build → faster builds; runtime behavior (streaming, caching) is similar. **staleTimes** (experimental) can reduce client-side Router Cache usage and may improve memory/consistency.
- **Both**: **fetch** not cached by default in 15+; you opt in. So no accidental over-caching; you explicitly add cache where needed. For performance, the main levers (Server Components, streaming, next/image, code split) are the same; 16 mainly improves build speed and tooling.

---

## Q15. (Advanced) How do you reduce CLS when content is streamed in (e.g. a Suspense block that loads later)?

**Answer**:

Reserve space for the streamed content so layout doesn’t shift when it appears. Use a **loading** fallback with the **same dimensions** as the final content (e.g. skeleton with min-height or fixed height). Avoid fallbacks that are 0 height or much smaller than the real content.

---

## Q16. (Advanced) Production scenario: You have a "find the wrong code" — the following causes a large layout shift. Fix it.

**Wrong code**:

```tsx
// Hero has no dimensions; image loads and shifts layout
<div className="hero">
  <img src="/hero.jpg" alt="Hero" />
</div>
```

**Answer**:

Use **next/image** with explicit dimensions (or **fill** with a sized container) and **priority** for the LCP image. Reserve space so CLS is zero.

```tsx
<div className="hero relative h-[60vh] w-full">
  <Image
    src="/hero.jpg"
    alt="Hero"
    fill
    className="object-cover"
    priority
    sizes="100vw"
  />
</div>
```

---

## Q17. (Advanced) How do you measure and improve Time to First Byte (TTFB) for a dynamic Next.js page?

**Answer**:

- **Measure**: Use **Navigation Timing** (e.g. `performance.getEntriesByType('navigation')[0].responseStart`) or RUM. TTFB = responseStart (or similar) in the nav entry.
- **Improve**: Reduce server work (parallelize DB/API calls, use **cache()** and **revalidate**), use a close CDN/edge, and avoid cold starts (e.g. keep serverless warm or use edge for that route). For static pages, TTFB is low if served from CDN.

---

## Q18. (Advanced) What is INP (Interaction to Next Paint) and how does Next.js 15/16 help improve it?

**Answer**:

**INP** is a metric for responsiveness (replacing FID): how quickly the page responds to user input. Next.js helps by: (1) reducing client JS (Server Components) so the main thread is less busy; (2) code splitting so only necessary JS runs; (3) avoiding long tasks (e.g. defer non-critical scripts with **next/script**). Improving INP is about reducing main-thread work and breaking up long tasks.

---

## Q19. (Advanced) How do you use the Experimental "staleTimes" (Next.js 15+) to tune the client-side Router Cache and what impact does it have on performance?

**Answer**:

**staleTimes** (experimental) controls how long the client keeps RSC payloads in the Router Cache. Lower values (e.g. 0 for dynamic) mean more frequent refetches; higher values mean more reuse and fewer requests but possibly staler UI. Tuning: use lower staleTimes for highly dynamic routes and higher for static-like routes to balance freshness and performance (fewer round-trips, faster navigations when cached).

---

## Q20. (Advanced) Design a performance monitoring dashboard: what metrics would you collect from a Next.js app in production and how would you aggregate them?

**Answer**:

- **Core Web Vitals**: LCP, INP, CLS (per page, per device/connection bucket). Aggregate p75, p95.
- **Custom**: TTFB, FCP, TTI (if measurable). Time to Server Component render (custom span).
- **Errors**: JS errors, Server Action failures, 5xx rate.
- **Business**: Conversion funnel, key action latency (e.g. "add to cart" click to success).

**How**: Use **web-vitals** + your analytics (e.g. Sentry, Vercel Analytics, DataDog RUM). Send metrics with page, route, and optionally user/device. Aggregate in your analytics backend by route and time window; alert on p95 LCP or error rate regressions.
