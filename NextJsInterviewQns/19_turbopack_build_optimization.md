# 19. Turbopack & Build Optimization

## Topic Introduction

**Turbopack** is the Rust-based successor to Webpack, built specifically for the Next.js ecosystem. Introduced as the default development bundler in Next.js 15, it provides dramatically faster Hot Module Replacement (HMR) and dev server startup. Understanding Turbopack's architecture and broader build optimization techniques is essential for senior developers working on large-scale Next.js applications.

### Turbopack vs Webpack Architecture

```
WEBPACK (JavaScript-based):
┌─────────────────────────────────────────────────┐
│  Entry Point                                     │
│  └─▶ Resolve modules (one by one)               │
│      └─▶ Apply loaders (transform)              │
│          └─▶ Build dependency graph             │
│              └─▶ Code splitting                 │
│                  └─▶ Optimization (terser)       │
│                      └─▶ Output bundles         │
│                                                 │
│  Cold start: ~30s (large app)                    │
│  HMR: ~2-5s                                      │
│  Full rebuild: ~60s                              │
└─────────────────────────────────────────────────┘

TURBOPACK (Rust-based):
┌─────────────────────────────────────────────────┐
│  Entry Point                                     │
│  └─▶ Incremental computation engine             │
│      ├─▶ Module resolution (parallel, cached)   │
│      ├─▶ Transform (SWC, parallel)              │
│      ├─▶ Dependency graph (incremental)         │
│      └─▶ On-demand bundling                     │
│                                                 │
│  Cold start: ~3s (same large app)               │
│  HMR: ~10-50ms                                   │
│  Incremental rebuild: ~100ms                     │
└─────────────────────────────────────────────────┘
```

### Key Turbopack Concepts

```
┌──────────────────────────────────────────────────┐
│  INCREMENTAL COMPUTATION                          │
│                                                  │
│  Traditional: Change 1 file → Rebuild everything │
│  Turbopack:   Change 1 file → Rebuild ONLY the  │
│               affected computation graph nodes   │
│                                                  │
│  File A changed                                  │
│    ├─▶ Re-transform A (cached neighbors skip)   │
│    ├─▶ Re-resolve A's deps (if imports changed)  │
│    └─▶ Re-bundle chunk containing A             │
│        (other chunks untouched)                  │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  FUNCTION-LEVEL CACHING                           │
│                                                  │
│  Every function in the build pipeline is cached: │
│    resolve(path) → cached result                 │
│    transform(file) → cached result               │
│    bundle(chunk) → cached result                 │
│                                                  │
│  Cache is invalidated only when inputs change    │
└──────────────────────────────────────────────────┘
```

**Why this matters for senior developers**: Build performance directly impacts developer productivity and CI/CD costs. A 10x faster build means faster iteration, cheaper CI bills, and happier teams. Understanding how to optimize both the bundler and your code for build performance is a critical production skill.

---

## Q1. (Beginner) What is Turbopack and how does it differ from Webpack?

**Scenario**: Your team is evaluating whether to enable Turbopack for your Next.js 15 project. You need to explain the key differences.

**Answer**:

**Turbopack** is a Rust-based incremental bundler developed by Vercel (by the creator of Webpack, Tobias Koppers). It's designed to replace Webpack as the default bundler for Next.js.

| Feature | Webpack | Turbopack |
|---------|---------|-----------|
| Language | JavaScript | Rust |
| Architecture | Full graph rebuild | Incremental computation |
| Dev server startup | 10-60s (large apps) | 1-5s |
| HMR speed | 500ms - 5s | 10-50ms |
| Memory usage | High (JS heap) | Lower (Rust memory mgmt) |
| Caching | Basic file-based | Function-level granular |
| Parallelism | Limited (single-thread JS) | True multi-core parallelism |
| Plugin ecosystem | Massive (webpack plugins) | Growing (limited in Next.js 15) |
| Production builds | Fully supported | Stable in Next.js 15 (dev), 16 (prod) |
| Config | `webpack` in next.config | `turbopack` in next.config |

```
Performance comparison (10,000 module app):

Dev Server Cold Start:
  Webpack:   ████████████████████████████████ 28.2s
  Turbopack: ████ 3.1s                        (9x faster)

HMR (file save to browser update):
  Webpack:   ████████████████ 1,600ms
  Turbopack: █ 12ms                           (133x faster)

Route Change (dev):
  Webpack:   ████████████ 1,200ms
  Turbopack: ██ 230ms                         (5x faster)
```

**How Turbopack achieves this speed**:

1. **Rust**: No garbage collection pauses, predictable memory, true parallelism
2. **Incremental computation**: Only recalculates what changed (like a reactive spreadsheet)
3. **Lazy compilation**: Only bundles code for the route you're viewing
4. **SWC**: Uses the SWC Rust-based compiler instead of Babel
5. **Function-level cache**: Every internal function's output is cached and invalidated granularly

```tsx
// Enable Turbopack in development (default in Next.js 15)
// package.json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start"
  }
}
```

---

## Q2. (Beginner) How do you enable and configure Turbopack in a Next.js project?

**Scenario**: You're setting up a new Next.js 15 project and want to use Turbopack with custom configuration.

**Answer**:

Turbopack is enabled by default in Next.js 15 for development. For production builds, Turbopack support became stable in Next.js 15.

**Enabling Turbopack**:

```bash
# Development — Turbopack is the default in Next.js 15
npx next dev              # Uses Turbopack by default
npx next dev --turbopack  # Explicit flag (same result)

# To opt OUT of Turbopack and use Webpack:
npx next dev --no-turbopack

# Production — Turbopack for production builds (Next.js 15+)
npx next build --turbopack
```

**Configuring Turbopack in `next.config.ts`**:

```tsx
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Turbopack-specific configuration
  turbopack: {
    // Module resolution aliases (like webpack resolve.alias)
    resolveAlias: {
      '@components': './src/components',
      '@utils': './src/utils',
      '@lib': './src/lib',
      // Replace a module with a custom implementation
      'old-library': 'new-library',
    },

    // File extension resolution order
    resolveExtensions: ['.tsx', '.ts', '.jsx', '.js', '.json', '.css'],

    // Custom module rules (like webpack module.rules)
    rules: {
      // Handle SVG files as React components
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
      // Handle MDX files
      '*.mdx': {
        loaders: ['@mdx-js/loader'],
        as: '*.js',
      },
    },
  },

  // These settings work with both Webpack and Turbopack
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.example.com' },
    ],
  },
};

export default nextConfig;
```

**Migrating from Webpack config to Turbopack**:

```tsx
// BEFORE: Webpack configuration
const nextConfig = {
  webpack: (config, { isServer }) => {
    // SVG handling
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    // Aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@components': path.resolve('./src/components'),
    };

    return config;
  },
};

// AFTER: Turbopack configuration
const nextConfig: NextConfig = {
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
    resolveAlias: {
      '@components': './src/components',
    },
  },
};
```

**Common gotcha**: Not all Webpack plugins/loaders work with Turbopack. Check the compatibility before migrating:

```
Compatible with Turbopack:
  ✓ @svgr/webpack
  ✓ @mdx-js/loader
  ✓ PostCSS plugins
  ✓ Tailwind CSS
  ✓ CSS Modules
  ✓ Sass
  ✓ TypeScript (via SWC)

May need alternatives:
  ✗ Custom Webpack plugins → Check Turbopack equivalents
  ✗ Babel plugins → Migrate to SWC plugins
  ✗ webpack-bundle-analyzer → Use @next/bundle-analyzer
```

---

## Q3. (Beginner) What is tree shaking and how does Next.js optimize it?

**Scenario**: You imported a large utility library but only use one function. After building, the entire library is included in the bundle. How do you fix this?

**Answer**:

**Tree shaking** is the process of eliminating dead code — code that is imported but never used. Modern bundlers (both Webpack and Turbopack) perform tree shaking automatically, but it requires your code and dependencies to be structured correctly.

```
Without tree shaking:
  import { format } from 'date-fns'  // Imports ALL of date-fns
  // Bundle: 200KB

With tree shaking:
  import { format } from 'date-fns'  // Only imports format()
  // Bundle: 5KB (if date-fns supports ES modules)
```

```
How tree shaking works:

Source:
  // utils.ts
  export function add(a, b) { return a + b; }     ← USED
  export function subtract(a, b) { return a - b; } ← NOT USED
  export function multiply(a, b) { return a * b; } ← NOT USED

  // page.tsx
  import { add } from './utils'
  console.log(add(1, 2))

After tree shaking:
  function add(a, b) { return a + b; }
  console.log(add(1, 2))
  // subtract and multiply are removed!
```

**Prerequisites for tree shaking**:

```tsx
// ✅ ES Modules (tree-shakeable)
export function doSomething() { ... }
export function doSomethingElse() { ... }

// ❌ CommonJS (NOT tree-shakeable)
module.exports = {
  doSomething() { ... },
  doSomethingElse() { ... },
};
```

**Verifying tree shaking in your build**:

```bash
# Install bundle analyzer
npm install -D @next/bundle-analyzer
```

```tsx
// next.config.ts
import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig = {
  // your config
};

export default withBundleAnalyzer(nextConfig);
```

```bash
# Run build with analysis
ANALYZE=true npm run build
# Opens interactive treemap in browser
```

**Common tree shaking killers and fixes**:

```tsx
// ❌ BAD: Barrel file imports everything
// lib/index.ts
export * from './auth';
export * from './database';
export * from './email';
export * from './analytics';

// page.tsx — imports just auth, but barrel pulls in ALL modules
import { signIn } from '@/lib';

// ✅ GOOD: Import directly from the module
import { signIn } from '@/lib/auth';
```

```tsx
// ❌ BAD: Side effects prevent tree shaking
// utils.ts
console.log('Utils loaded!'); // Side effect — file can't be tree-shaken

export function helper() { ... }

// ✅ GOOD: Mark package as side-effect-free
// package.json
{
  "sideEffects": false
}
// Or specify which files have side effects:
{
  "sideEffects": ["./src/polyfills.ts", "*.css"]
}
```

```tsx
// ❌ BAD: Dynamic property access prevents tree shaking
import * as utils from './utils';
const fn = utils[someVariable]; // Bundler can't determine which exports are used

// ✅ GOOD: Static imports
import { specificFunction } from './utils';
```

**Next.js automatic optimizations**:

```tsx
// Next.js automatically optimizes these popular packages:
// - lodash → lodash-es (automatic rewrite)
// - date-fns → individual function imports
// - @mui/material → individual component imports
// - lucide-react → individual icon imports

// These work because of `optimizePackageImports` in next.config
const nextConfig = {
  experimental: {
    optimizePackageImports: [
      'lodash',
      'date-fns',
      '@mui/material',
      '@mui/icons-material',
      'lucide-react',
      '@heroicons/react',
      'recharts',
    ],
  },
};
```

---

## Q4. (Beginner) How does code splitting work in Next.js, and what are the automatic splitting strategies?

**Scenario**: Your application's main bundle is 500KB. Users on slow connections take 10+ seconds to see the first page. You need to reduce the initial load.

**Answer**:

**Code splitting** divides your application into smaller chunks that are loaded on demand, rather than sending everything upfront.

Next.js performs **three types of automatic code splitting**:

```
1. ROUTE-BASED SPLITTING (automatic):
   Each route gets its own JavaScript bundle

   /             → page-home-[hash].js     (15KB)
   /about        → page-about-[hash].js    (8KB)
   /dashboard    → page-dashboard-[hash].js (25KB)

   User visits / → downloads only page-home-[hash].js
                   (not about or dashboard code)

2. SHARED CHUNK SPLITTING (automatic):
   Code used by multiple routes is extracted into shared chunks

   page-home.js     ──┐
   page-about.js    ──┼──▶ shared-[hash].js (React, common components)
   page-dashboard.js──┘

3. COMPONENT-LEVEL SPLITTING (manual via dynamic imports):
   Heavy components loaded on demand

   Page loads → lightweight shell
   User scrolls → load heavy chart component
   User clicks → load modal component
```

**Automatic route-based splitting**:

```
Build output:

Route (app)                    Size     First Load JS
┌ ○ /                          5.2 kB   89.1 kB
├ ○ /about                     1.2 kB   85.1 kB
├ ○ /blog                      3.4 kB   87.3 kB
├ λ /dashboard                 8.1 kB   92.0 kB
└ ○ /pricing                   2.7 kB   86.6 kB

+ First Load JS shared by all  83.9 kB
  ├ chunks/main-[hash].js      30.2 kB   ← React runtime
  ├ chunks/pages/_app-[hash].js 50.1 kB  ← App shell + shared deps
  └ chunks/framework-[hash].js  3.6 kB   ← Next.js framework
```

**Manual code splitting with `dynamic()`**:

```tsx
// app/dashboard/page.tsx
import dynamic from 'next/dynamic';

// Heavy chart library — only loaded when dashboard is viewed
const AnalyticsChart = dynamic(() => import('@/components/AnalyticsChart'), {
  loading: () => (
    <div className="h-64 bg-gray-100 animate-pulse rounded-lg" />
  ),
  ssr: false, // Skip server rendering for client-only components
});

// Heavy editor — loaded on demand
const RichTextEditor = dynamic(() => import('@/components/RichTextEditor'), {
  loading: () => <div className="h-48 border rounded-lg animate-pulse" />,
});

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1>Dashboard</h1>
      <AnalyticsChart />
      <RichTextEditor />
    </div>
  );
}
```

**Named exports with dynamic import**:

```tsx
// When the component isn't the default export
const SpecificChart = dynamic(
  () => import('@/components/Charts').then((mod) => mod.BarChart),
  { loading: () => <ChartSkeleton /> }
);
```

**Conditional dynamic imports**:

```tsx
// Only load admin tools for admin users
'use client';

import dynamic from 'next/dynamic';
import { useSession } from 'next-auth/react';

const AdminPanel = dynamic(() => import('@/components/AdminPanel'));

export function Dashboard() {
  const { data: session } = useSession();

  return (
    <div>
      <MainContent />
      {session?.user?.role === 'admin' && <AdminPanel />}
    </div>
  );
}
```

---

## Q5. (Beginner) What is `@next/bundle-analyzer` and how do you use it to find bundle size issues?

**Scenario**: Your First Load JS is 350KB and you need to identify which packages are contributing the most.

**Answer**:

`@next/bundle-analyzer` generates an interactive treemap visualization of your bundle contents, showing exactly what's inside each chunk and how much space it takes.

```bash
npm install -D @next/bundle-analyzer
```

```tsx
// next.config.ts
import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
  openAnalyzer: true, // Auto-open in browser
});

const nextConfig = {
  // your config
};

export default withBundleAnalyzer(nextConfig);
```

```bash
ANALYZE=true npm run build
```

**Reading the treemap**:

```
┌─────────────────────────────────────────────────┐
│  client.js (350KB)                               │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  node_modules │  │  src/         │             │
│  │  (280KB)      │  │  (70KB)       │             │
│  │  ┌──────────┐│  │  ┌──────────┐ │             │
│  │  │ moment   ││  │  │components│ │             │
│  │  │ (65KB!)  ││  │  │ (40KB)   │ │             │
│  │  └──────────┘│  │  └──────────┘ │             │
│  │  ┌──────────┐│  │  ┌──────────┐ │             │
│  │  │ lodash   ││  │  │ utils    │ │             │
│  │  │ (72KB!)  ││  │  │ (30KB)   │ │             │
│  │  └──────────┘│  │  └──────────┘ │             │
│  │  ┌──────────┐│  │               │             │
│  │  │ chart.js ││  │               │             │
│  │  │ (143KB!) ││  │               │             │
│  │  └──────────┘│  │               │             │
│  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────┘

Action items:
1. moment (65KB) → Replace with date-fns (16KB) or dayjs (2KB)
2. lodash (72KB) → Use lodash-es + tree shaking, or native JS
3. chart.js (143KB) → Dynamic import (load on demand)
```

**Automated bundle size monitoring in CI**:

```tsx
// scripts/check-bundle-size.ts
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

interface BundleLimit {
  pattern: string;
  maxSize: number; // in KB
}

const limits: BundleLimit[] = [
  { pattern: 'First Load JS shared by all', maxSize: 100 },
  { pattern: '/_app', maxSize: 60 },
  { pattern: '/page', maxSize: 30 },
];

function checkBundleSize() {
  const buildDir = join(process.cwd(), '.next');

  // Read the build manifest
  const manifestPath = join(buildDir, 'build-manifest.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));

  // Check chunk sizes
  const chunkDir = join(buildDir, 'static', 'chunks');
  const chunks = readdirSync(chunkDir);

  let totalSize = 0;
  const violations: string[] = [];

  for (const chunk of chunks) {
    const stat = require('fs').statSync(join(chunkDir, chunk));
    const sizeKB = stat.size / 1024;
    totalSize += sizeKB;

    if (sizeKB > 200) {
      violations.push(`WARNING: ${chunk} is ${sizeKB.toFixed(1)}KB (>200KB limit)`);
    }
  }

  console.log(`Total JS size: ${totalSize.toFixed(1)}KB`);

  if (violations.length > 0) {
    console.error('\nBundle size violations:');
    violations.forEach((v) => console.error(`  ${v}`));
    process.exit(1);
  }

  console.log('\n✓ All chunks within size limits');
}

checkBundleSize();
```

---

## Q6. (Intermediate) How does Turbopack's incremental computation engine work under the hood?

**Scenario**: A colleague asks why Turbopack's HMR is so fast. You need to explain the technical architecture.

**Answer**:

Turbopack's core innovation is its **incremental computation engine** (called "Turbo Engine"), which treats the entire build process as a dependency graph of pure functions.

```
Traditional Bundler (Webpack):
┌─────────────────────────────────────────────┐
│  File Change Detected                        │
│  └─▶ Invalidate module                      │
│      └─▶ Re-parse file                      │
│          └─▶ Re-resolve ALL imports          │
│              └─▶ Re-build dependency graph   │
│                  └─▶ Re-bundle ALL chunks    │
│                      └─▶ Re-optimize ALL     │
│                                             │
│  Even if only 1 import changed, entire       │
│  chunks need rebuilding                      │
└─────────────────────────────────────────────┘

Turbopack (Incremental):
┌─────────────────────────────────────────────┐
│  File Change Detected                        │
│  └─▶ Identify changed computation nodes     │
│      └─▶ Re-execute ONLY those nodes        │
│          └─▶ Propagate changes to dependents│
│              └─▶ Re-bundle ONLY affected    │
│                  chunks                      │
│                                             │
│  If only a CSS property changed:            │
│  - Re-parse CSS file ✓                      │
│  - Skip JS resolution ✓                     │
│  - Skip unused chunk bundling ✓             │
│  - Update only the affected CSS chunk ✓     │
└─────────────────────────────────────────────┘
```

**The computation graph**:

```
Every build operation is a "function" node in a graph:

resolve("./Button")
    │
    ▼
read_file("src/components/Button.tsx")
    │
    ▼
parse_module("src/components/Button.tsx")
    │
    ├──▶ resolve("react")
    │        │
    │        ▼
    │    read_file("node_modules/react/index.js")
    │        │
    │        ▼
    │    parse_module(...)
    │
    ├──▶ resolve("./Button.css")
    │        │
    │        ▼
    │    read_file("src/components/Button.css")
    │        │
    │        ▼
    │    process_css(...)
    │
    ▼
bundle_chunk("page-main")
    │
    ▼
emit_chunk("page-main-[hash].js")
```

**When `Button.css` changes**:

```
ONLY these nodes re-execute:
  ✓ read_file("src/components/Button.css")  ← file changed
  ✓ process_css(...)                         ← input changed
  ✓ bundle_chunk("page-main")              ← CSS dependency changed
  ✓ emit_chunk("page-main-[hash].js")      ← bundle changed

These nodes are SKIPPED (cached):
  ✗ resolve("./Button")                     ← imports unchanged
  ✗ read_file("src/components/Button.tsx")  ← file unchanged
  ✗ parse_module("Button.tsx")              ← file unchanged
  ✗ resolve("react")                        ← unchanged
  ✗ All other modules                       ← unchanged
```

**Key architectural features**:

1. **Function-level memoization**: Every function's output is cached based on its inputs. If inputs haven't changed, the cached output is returned instantly.

2. **Fine-grained invalidation**: Unlike Webpack which invalidates at the module level, Turbopack invalidates at the function level. A CSS-only change doesn't invalidate JS parsing.

3. **Parallel execution**: Since functions are pure (output depends only on inputs), independent functions can execute in parallel across CPU cores.

4. **Lazy evaluation**: Functions only execute when their output is needed. If you're viewing `/about`, functions related to `/dashboard` aren't executed.

```
Parallelism example (8-core CPU):

Webpack (mostly single-threaded):
  Core 1: ████████████████████████████████ (all work)
  Core 2: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (idle)
  Core 3-8: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (idle)

Turbopack (parallel):
  Core 1: ████████ resolve(A) ████ parse(A)
  Core 2: ████████ resolve(B) ████ parse(B)
  Core 3: ████████ resolve(C) ████ parse(C)
  Core 4: ████████ resolve(D) ████ parse(D)
  Core 5: ████ css(A)  ████ bundle(1)
  Core 6: ████ css(B)  ████ bundle(2)
  Core 7: ████ css(C)  ████ bundle(3)
  Core 8: ████ css(D)  ████ emit(1,2,3)
```

---

## Q7. (Intermediate) How do you optimize barrel files and module re-exports to reduce bundle size?

**Scenario**: Your `components/index.ts` re-exports 200 components. Importing one component pulls in code for all 200. Build time is 3 minutes.

**Answer**:

**Barrel files** (`index.ts` files that re-export from multiple modules) are one of the biggest build performance and bundle size killers in Next.js applications.

```
The barrel file problem:

// components/index.ts (barrel file)
export { Button } from './Button';
export { Modal } from './Modal';
export { Chart } from './Chart';     // ← 500KB chart library!
export { DataGrid } from './DataGrid'; // ← 300KB grid library!
... (200 more exports)

// page.tsx — only needs Button
import { Button } from '@/components';
// ↑ Bundler may pull in ALL exports, including Chart (500KB)!
```

**Solution 1: `optimizePackageImports` (Next.js built-in)**:

```tsx
// next.config.ts
const nextConfig = {
  experimental: {
    optimizePackageImports: [
      // Your own barrel files
      '@/components',
      '@/lib',
      '@/hooks',
      // Third-party packages with barrel exports
      'lucide-react',
      '@heroicons/react',
      'date-fns',
      '@mui/material',
      '@mui/icons-material',
      'rxjs',
      'recharts',
    ],
  },
};
```

This tells Next.js to transform barrel imports into direct imports:

```tsx
// Before optimization (what you write):
import { Button, Input } from '@/components';

// After optimization (what the bundler sees):
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
```

**Solution 2: Restructure imports (manual)**:

```tsx
// ❌ BAD: Barrel import
import { Button } from '@/components';

// ✅ GOOD: Direct import
import { Button } from '@/components/ui/Button';
```

**Solution 3: Detect barrel file issues with ESLint**:

```tsx
// .eslintrc.js
module.exports = {
  rules: {
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: ['@/components'],
            message: 'Import directly from component file, e.g., @/components/ui/Button',
          },
          {
            group: ['lodash'],
            importNames: ['default'],
            message: 'Import individual lodash functions: import debounce from "lodash/debounce"',
          },
        ],
      },
    ],
  },
};
```

**Solution 4: Smart barrel files with lazy exports**:

```tsx
// components/index.ts — Lazy barrel pattern
// Light components: direct re-export
export { Button } from './ui/Button';
export { Input } from './ui/Input';
export { Badge } from './ui/Badge';

// Heavy components: export as dynamic imports
export const Chart = dynamic(() => import('./Chart'));
export const DataGrid = dynamic(() => import('./DataGrid'));
export const RichTextEditor = dynamic(() => import('./RichTextEditor'));
```

**Measuring barrel file impact**:

```bash
# Check how much a barrel import adds to your bundle
# Compare these two builds:

# Build 1: With barrel import
echo "import { Button } from '@/components'" > /tmp/test-barrel.tsx

# Build 2: With direct import
echo "import { Button } from '@/components/ui/Button'" > /tmp/test-direct.tsx

# Compare First Load JS in build output
```

---

## Q8. (Intermediate) How do you implement dynamic imports and lazy loading for optimal performance?

**Scenario**: Your dashboard page loads 2MB of JavaScript because it includes a chart library, a data grid, and a rich text editor — all above the fold but only partially visible on initial render.

**Answer**:

```tsx
// ❌ BEFORE: Everything loads upfront (2MB)
import { BarChart, LineChart, PieChart } from 'recharts';
import { DataGrid } from '@mui/x-data-grid';
import ReactQuill from 'react-quill';

// ✅ AFTER: Components load on demand

// Strategy 1: next/dynamic for page-level splitting
import dynamic from 'next/dynamic';

const BarChart = dynamic(
  () => import('recharts').then((mod) => mod.BarChart),
  {
    loading: () => <div className="h-64 animate-pulse bg-gray-100 rounded-lg" />,
    ssr: false, // Charts don't need SSR
  }
);

const DataGrid = dynamic(
  () => import('@mui/x-data-grid').then((mod) => mod.DataGrid),
  {
    loading: () => <TableSkeleton rows={10} />,
  }
);

const RichTextEditor = dynamic(
  () => import('react-quill'),
  {
    loading: () => <div className="h-48 border animate-pulse" />,
    ssr: false, // Editor needs browser APIs
  }
);
```

**Strategy 2: Intersection Observer for below-the-fold content**:

```tsx
// components/LazySection.tsx
'use client';

import { useEffect, useRef, useState, ReactNode } from 'react';

interface LazySectionProps {
  children: ReactNode;
  fallback?: ReactNode;
  rootMargin?: string;
  threshold?: number;
}

export function LazySection({
  children,
  fallback = <div className="h-64 animate-pulse bg-gray-50 rounded-lg" />,
  rootMargin = '200px', // Start loading 200px before visible
  threshold = 0,
}: LazySectionProps) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin, threshold }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [rootMargin, threshold]);

  return <div ref={ref}>{isVisible ? children : fallback}</div>;
}
```

```tsx
// Usage in dashboard page
import { LazySection } from '@/components/LazySection';
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('@/components/charts/HeavyChart'), {
  ssr: false,
});

const DataExplorer = dynamic(() => import('@/components/DataExplorer'));

export default function DashboardPage() {
  return (
    <div className="space-y-8 p-6">
      {/* Above the fold — loads immediately */}
      <DashboardHeader />
      <QuickStats />

      {/* Below the fold — lazy loaded when scrolled near */}
      <LazySection>
        <HeavyChart />
      </LazySection>

      <LazySection rootMargin="400px">
        <DataExplorer />
      </LazySection>
    </div>
  );
}
```

**Strategy 3: Route-based preloading with `<Link prefetch>`**:

```tsx
// Prefetch heavy pages when the user is likely to visit them
import Link from 'next/link';

export function Navigation() {
  return (
    <nav>
      {/* Prefetch on hover (default) */}
      <Link href="/dashboard">Dashboard</Link>

      {/* Disable prefetch for rarely visited pages */}
      <Link href="/admin/reports" prefetch={false}>
        Reports
      </Link>

      {/* Explicit prefetch for likely next page */}
      <Link href="/checkout" prefetch={true}>
        Checkout
      </Link>
    </nav>
  );
}
```

**Strategy 4: Module-level code splitting for utilities**:

```tsx
// ❌ BAD: Import heavy library at module level
import * as XLSX from 'xlsx';

export function ExportButton({ data }) {
  const handleExport = () => {
    const workbook = XLSX.utils.book_new();
    // ...
  };
  return <button onClick={handleExport}>Export</button>;
}

// ✅ GOOD: Dynamic import when user clicks
export function ExportButton({ data }) {
  const handleExport = async () => {
    const XLSX = await import('xlsx');
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');
    XLSX.writeFile(workbook, 'export.xlsx');
  };

  return <button onClick={handleExport}>Export to Excel</button>;
}
```

---

## Q9. (Intermediate) What is the production build optimization checklist for Next.js?

**Scenario**: You're preparing your Next.js application for a production launch. Create a comprehensive optimization checklist.

**Answer**:

```
PRODUCTION BUILD OPTIMIZATION CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ 1. Bundle Size Analysis
□ 2. Image Optimization
□ 3. Font Optimization
□ 4. Third-party Script Loading
□ 5. Server Component Optimization
□ 6. Build Configuration
□ 7. Caching Strategy
□ 8. Compression
□ 9. Monitoring
```

**1. Bundle Size — Target: First Load JS < 100KB**:

```tsx
// next.config.ts
const nextConfig = {
  // Enable experimental optimizations
  experimental: {
    optimizePackageImports: [
      'lodash-es', 'date-fns', 'lucide-react',
      '@heroicons/react', '@mui/material', '@mui/icons-material',
    ],
  },

  // Externalize server-only packages
  serverExternalPackages: ['sharp', 'bcrypt', 'canvas'],

  // Enable modern output
  output: 'standalone', // For Docker deployments
};
```

**2. Image Optimization**:

```tsx
// Use next/image for automatic optimization
import Image from 'next/image';

// ✅ Optimized
<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority           // LCP image — preload
  quality={80}       // Reduce quality for faster loading
  sizes="(max-width: 768px) 100vw, 1200px"
  placeholder="blur" // Show blur while loading
  blurDataURL={blurHash}
/>

// next.config.ts — image optimization config
const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'], // Modern formats
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
    minimumCacheTTL: 60 * 60 * 24 * 365, // 1 year
  },
};
```

**3. Font Optimization**:

```tsx
// app/layout.tsx — Use next/font for zero-layout-shift fonts
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',    // Don't block rendering
  variable: '--font-inter',
});

const mono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
});

export default function RootLayout({ children }) {
  return (
    <html className={`${inter.variable} ${mono.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
```

**4. Third-party Scripts**:

```tsx
// Use next/script for optimized loading
import Script from 'next/script';

// Analytics — load after page is interactive
<Script
  src="https://analytics.example.com/script.js"
  strategy="afterInteractive"
/>

// Non-critical — load when browser is idle
<Script
  src="https://widget.example.com/embed.js"
  strategy="lazyOnload"
/>

// Critical — load before interactive (use sparingly)
<Script
  src="https://cdn.example.com/critical.js"
  strategy="beforeInteractive"
/>
```

**5. Server Component Optimization**:

```tsx
// Keep as much as possible as Server Components
// Only add 'use client' when absolutely needed

// ✅ Server Component (zero JS sent to client)
export default async function ProductList() {
  const products = await getProducts();
  return (
    <ul>
      {products.map(p => <ProductCard key={p.id} product={p} />)}
    </ul>
  );
}

// Only the interactive parts are Client Components
// components/AddToCartButton.tsx
'use client';
export function AddToCartButton({ productId }: { productId: string }) {
  return <button onClick={() => addToCart(productId)}>Add to Cart</button>;
}
```

**6. Build Configuration**:

```tsx
// next.config.ts — comprehensive production config
const nextConfig = {
  // Compression
  compress: true,

  // Generate source maps (disable for smaller builds if not debugging)
  productionBrowserSourceMaps: false,

  // Strict mode for React
  reactStrictMode: true,

  // Powered-by header (remove for security)
  poweredByHeader: false,

  // Enable standalone output for Docker
  output: 'standalone',

  // Compiler optimizations
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Headers for caching
  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
    ];
  },
};
```

---

## Q10. (Intermediate) How do you reduce First Load JS size in a Next.js application?

**Scenario**: Your build output shows First Load JS of 250KB. Your target is under 100KB. What strategies do you use?

**Answer**:

```
Current state:
  First Load JS shared by all  250 kB
  ├ chunks/framework-[hash].js  45 kB  ← React (can't reduce much)
  ├ chunks/main-[hash].js       35 kB  ← Next.js runtime
  ├ chunks/[hash].js            85 kB  ← YOUR CODE + deps
  └ chunks/[hash].js            85 kB  ← MORE deps

Target: < 100KB
Need to cut: ~150KB
```

**Strategy 1: Audit and replace heavy dependencies**:

```tsx
// Common heavy packages and lighter alternatives:

// moment.js (65KB) → date-fns (16KB) or dayjs (2KB)
// Before:
import moment from 'moment';
moment().format('YYYY-MM-DD');

// After:
import { format } from 'date-fns';
format(new Date(), 'yyyy-MM-dd');

// lodash (72KB) → native JS or lodash-es individual imports
// Before:
import _ from 'lodash';
_.debounce(fn, 300);

// After:
import debounce from 'lodash-es/debounce';
debounce(fn, 300);

// Or use native:
function debounce(fn: Function, ms: number) {
  let timer: NodeJS.Timeout;
  return (...args: any[]) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

// axios (13KB) → native fetch (0KB)
// Before:
import axios from 'axios';
const { data } = await axios.get('/api/data');

// After:
const data = await fetch('/api/data').then(r => r.json());
```

**Strategy 2: Move code to Server Components**:

```tsx
// ❌ Client Component — all code shipped to browser
'use client';
import { marked } from 'marked';        // 35KB
import { sanitize } from 'dompurify';  // 20KB

export function BlogPost({ markdown }: { markdown: string }) {
  const html = sanitize(marked(markdown));
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

// ✅ Server Component — zero JS shipped
import { marked } from 'marked';
import { sanitize } from 'dompurify';

export function BlogPost({ markdown }: { markdown: string }) {
  const html = sanitize(marked(markdown));
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
// marked and dompurify are NOT included in client bundle!
```

**Strategy 3: Analyze and eliminate dead code**:

```bash
# Find unused exports
npx knip
# Output:
# Unused exports:
#   src/utils/helpers.ts: formatCurrency, parseDate, validateEmail
#   src/components/legacy/OldWidget.tsx: default export
#   src/lib/analytics.ts: trackEvent, setUser
```

**Strategy 4: Use `React.lazy` + Suspense for client component splitting**:

```tsx
'use client';

import { Suspense, lazy } from 'react';

// Split heavy client components
const HeavyForm = lazy(() => import('./HeavyForm'));
const HeavyTable = lazy(() => import('./HeavyTable'));

export function DashboardClient() {
  return (
    <div>
      <Suspense fallback={<FormSkeleton />}>
        <HeavyForm />
      </Suspense>
      <Suspense fallback={<TableSkeleton />}>
        <HeavyTable />
      </Suspense>
    </div>
  );
}
```

**Measuring impact**:

```
After optimizations:
  First Load JS shared by all  87 kB  (was 250KB, -65% !)
  ├ chunks/framework-[hash].js  45 kB  ← Same (React)
  ├ chunks/main-[hash].js       32 kB  ← Slightly smaller
  └ chunks/[hash].js            10 kB  ← YOUR CODE (minimal)
```

---

## Q11. (Intermediate) How do you optimize Next.js builds in CI/CD pipelines?

**Scenario**: Your CI builds take 15 minutes. Deployment is blocked until the build completes. How do you speed this up?

**Answer**:

```
Current CI timeline (15 min):
  npm install:     ████████░░░░░░░░░░░░ 4 min
  next build:      ████████████████░░░░ 8 min
  tests:           ██████░░░░░░░░░░░░░░ 3 min

Optimized CI timeline (5 min):
  npm install (cached): █░░░░░░░░░░░░░░░░ 30s
  next build (cached):  ████░░░░░░░░░░░░░ 2 min
  tests (parallel):     ████░░░░░░░░░░░░░ 2 min
  total with parallel:  █████░░░░░░░░░░░░ ~3 min
```

**1. Cache `node_modules` and Next.js build cache**:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'  # Caches node_modules automatically

      # Cache Next.js build output
      - uses: actions/cache@v4
        with:
          path: |
            .next/cache
          key: nextjs-${{ runner.os }}-${{ hashFiles('package-lock.json') }}-${{ hashFiles('**/*.ts', '**/*.tsx') }}
          restore-keys: |
            nextjs-${{ runner.os }}-${{ hashFiles('package-lock.json') }}-
            nextjs-${{ runner.os }}-

      - run: npm ci
      - run: npm run build

      # Cache build artifacts for deployment job
      - uses: actions/cache/save@v4
        with:
          path: .next
          key: build-${{ github.sha }}
```

**2. Turbopack for CI builds** (Next.js 15+):

```json
{
  "scripts": {
    "build": "next build --turbopack",
    "build:ci": "NEXT_TELEMETRY_DISABLED=1 next build --turbopack"
  }
}
```

**3. Parallel test execution**:

```yaml
# Run build and lint in parallel
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npm run lint

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npx tsc --noEmit

  build:
    runs-on: ubuntu-latest
    needs: [lint, typecheck]  # Only build if lint + typecheck pass
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npm run build
```

**4. Skip unnecessary work**:

```yaml
# Only run build when relevant files change
on:
  push:
    paths:
      - 'src/**'
      - 'app/**'
      - 'package.json'
      - 'package-lock.json'
      - 'next.config.*'
      - 'tsconfig.json'
    paths-ignore:
      - '*.md'
      - 'docs/**'
      - '.github/ISSUE_TEMPLATE/**'
```

**5. Remote caching with Turborepo** (monorepos):

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**"]
    },
    "lint": {},
    "typecheck": {}
  }
}
```

```bash
# Enable remote caching
npx turbo login
npx turbo link

# Build with remote cache
npx turbo build --remote-cache
# Second run: ~90% cache hit → 10x faster!
```

---

## Q12. (Intermediate) How do you optimize builds in a Next.js monorepo?

**Scenario**: Your monorepo has `apps/web`, `apps/docs`, `packages/ui`, `packages/db`. Building everything takes 20 minutes. Most commits only touch one package.

**Answer**:

```
Monorepo structure:
monorepo/
├── apps/
│   ├── web/        (Next.js — main app)
│   ├── docs/       (Next.js — documentation)
│   └── admin/      (Next.js — admin panel)
├── packages/
│   ├── ui/         (shared React components)
│   ├── db/         (Prisma schema + client)
│   ├── config/     (shared configs — eslint, tsconfig)
│   └── utils/      (shared utilities)
├── turbo.json
└── package.json
```

**Turborepo configuration for optimized builds**:

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [
    "**/.env.*local",
    ".env"
  ],
  "globalEnv": ["NODE_ENV", "VERCEL_URL"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": [
        "src/**",
        "app/**",
        "public/**",
        "package.json",
        "tsconfig.json",
        "next.config.*"
      ],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"],
      "env": ["DATABASE_URL", "NEXT_PUBLIC_*"]
    },
    "lint": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "app/**", ".eslintrc.*"]
    },
    "typecheck": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "app/**", "tsconfig.json"]
    },
    "test": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "app/**", "__tests__/**", "*.test.*"],
      "outputs": ["coverage/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

**Filtering builds to affected packages**:

```bash
# Only build packages affected by recent changes
npx turbo build --filter=...[HEAD~1]

# Build specific app and its dependencies
npx turbo build --filter=web...

# Build everything except docs
npx turbo build --filter=!docs

# Build only packages that changed since main
npx turbo build --filter=...[origin/main]
```

**Shared Next.js configuration**:

```tsx
// packages/config/next-config.ts
import type { NextConfig } from 'next';

export function createNextConfig(appSpecific: Partial<NextConfig> = {}): NextConfig {
  return {
    reactStrictMode: true,
    compress: true,
    poweredByHeader: false,

    experimental: {
      optimizePackageImports: [
        '@repo/ui',
        'lucide-react',
        'date-fns',
      ],
    },

    transpilePackages: ['@repo/ui', '@repo/utils'],

    ...appSpecific,
  };
}
```

```tsx
// apps/web/next.config.ts
import { createNextConfig } from '@repo/config/next-config';

export default createNextConfig({
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.example.com' },
    ],
  },
});
```

**CI optimization for monorepos**:

```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      web: ${{ steps.filter.outputs.web }}
      docs: ${{ steps.filter.outputs.docs }}
      packages: ${{ steps.filter.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            web:
              - 'apps/web/**'
              - 'packages/**'
            docs:
              - 'apps/docs/**'
              - 'packages/ui/**'
            packages:
              - 'packages/**'

  build-web:
    needs: detect-changes
    if: needs.detect-changes.outputs.web == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npx turbo build --filter=web...
```

---

## Q13. (Advanced) How does Turbopack handle CSS, PostCSS, and Tailwind CSS processing?

**Scenario**: Your project uses Tailwind CSS v4 with PostCSS plugins. You need to understand how Turbopack processes styles differently from Webpack.

**Answer**:

Turbopack has built-in support for CSS Modules, PostCSS, Sass, and Tailwind CSS. Unlike Webpack, it processes CSS in Rust for better performance.

```
Webpack CSS Pipeline:
  .css/.scss file
    → postcss-loader (JS)
    → css-loader (JS)
    → style-loader / MiniCssExtractPlugin (JS)
    → Output CSS

Turbopack CSS Pipeline:
  .css/.scss file
    → SWC CSS parser (Rust)
    → PostCSS plugins (JS — interop layer)
    → Turbopack CSS optimizer (Rust)
    → Output CSS

Key difference: Parsing and optimization in Rust = faster
PostCSS plugins still run in JS (for compatibility)
```

**Tailwind CSS v4 with Turbopack**:

```tsx
// app/globals.css — Tailwind v4 uses CSS-native configuration
@import "tailwindcss";

/* Tailwind v4 configuration via CSS */
@theme {
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
  --font-sans: 'Inter', sans-serif;
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
}
```

```tsx
// postcss.config.ts — Turbopack supports standard PostCSS config
import type { Config } from 'postcss-load-config';

const config: Config = {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
};

export default config;
```

**CSS Modules with Turbopack**:

```tsx
// Turbopack handles CSS Modules identically to Webpack
// components/Button.module.css
.button {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
}

.button:hover {
  opacity: 0.9;
}

.primary {
  composes: button;
  background-color: var(--color-primary);
  color: white;
}

.secondary {
  composes: button;
  background-color: var(--color-secondary);
  color: white;
}
```

```tsx
// components/Button.tsx
import styles from './Button.module.css';

export function Button({
  variant = 'primary',
  children,
}: {
  variant?: 'primary' | 'secondary';
  children: React.ReactNode;
}) {
  return (
    <button className={styles[variant]}>
      {children}
    </button>
  );
}
```

**Sass/SCSS with Turbopack**:

```bash
npm install -D sass
```

```scss
// styles/variables.scss
$primary: #3b82f6;
$spacing-unit: 0.25rem;

@mixin responsive($breakpoint) {
  @if $breakpoint == 'md' {
    @media (min-width: 768px) { @content; }
  } @else if $breakpoint == 'lg' {
    @media (min-width: 1024px) { @content; }
  }
}
```

```scss
// components/Card.module.scss
@use '../styles/variables' as *;

.card {
  border-radius: $spacing-unit * 4;
  padding: $spacing-unit * 6;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

  @include responsive('md') {
    padding: $spacing-unit * 8;
  }
}
```

**Turbopack CSS performance comparison**:

```
Processing 500 CSS files with PostCSS + Tailwind:

Webpack:
  Parse:     ████████████░░░░░ 3.2s
  PostCSS:   ████████████████░ 4.1s
  Optimize:  ████░░░░░░░░░░░░░ 1.2s
  Total:     8.5s

Turbopack:
  Parse:     ██░░░░░░░░░░░░░░░ 0.4s  (Rust SWC parser)
  PostCSS:   ████████████████░ 3.8s  (JS — same speed)
  Optimize:  █░░░░░░░░░░░░░░░░ 0.2s  (Rust optimizer)
  Total:     4.4s (~2x faster)
```

---

## Q14. (Advanced) How do you implement advanced code splitting strategies for large applications?

**Scenario**: Your e-commerce app has 500+ routes with heavy vendor dependencies. The shared JS chunk is 300KB. You need a granular code splitting strategy.

**Answer**:

```
Problem:
  All vendor code in ONE shared chunk = 300KB
  Every page loads: React + Router + Auth + Analytics + UI lib + ...
  Even if a page only needs React + Router

Solution: Split vendors into granular chunks:
  framework.js  = React + ReactDOM (45KB)
  router.js     = Next.js router (15KB)
  auth.js       = Auth library (20KB, loaded on auth pages only)
  analytics.js  = Analytics (30KB, loaded lazily)
  ui-core.js    = Button, Input, Badge (10KB)
  ui-heavy.js   = DataGrid, Chart (200KB, loaded on demand)
```

**Custom chunk splitting with webpack** (when not using Turbopack for prod builds):

```tsx
// next.config.ts
const nextConfig = {
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          // Framework: React, ReactDOM
          framework: {
            test: /[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/,
            name: 'framework',
            priority: 40,
            enforce: true,
          },

          // Core UI library
          ui: {
            test: /[\\/]node_modules[\\/](@radix-ui|@headlessui|class-variance-authority)[\\/]/,
            name: 'ui-lib',
            priority: 30,
          },

          // Heavy vendors — loaded on specific routes only
          charts: {
            test: /[\\/]node_modules[\\/](recharts|d3|victory)[\\/]/,
            name: 'charts',
            priority: 30,
            chunks: 'async', // Only loaded when dynamically imported
          },

          dataGrid: {
            test: /[\\/]node_modules[\\/](@tanstack[\\/]react-table|@mui[\\/]x-data-grid)[\\/]/,
            name: 'data-grid',
            priority: 30,
            chunks: 'async',
          },

          // Common vendor code shared by 2+ chunks
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendor',
            priority: 10,
            minChunks: 2,
            reuseExistingChunk: true,
          },

          // Your shared code
          common: {
            name: 'common',
            minChunks: 3,
            priority: 5,
            reuseExistingChunk: true,
          },
        },
      };
    }
    return config;
  },
};
```

**Route-group-based splitting pattern**:

```
app/
├── (marketing)/           ← Light: minimal JS
│   ├── layout.tsx         ← Only loads marketing deps
│   ├── page.tsx           ← Homepage
│   ├── about/
│   └── pricing/
├── (app)/                 ← Medium: auth + app deps
│   ├── layout.tsx         ← Loads auth, common app deps
│   ├── dashboard/
│   ├── settings/
│   └── profile/
├── (analytics)/           ← Heavy: chart libraries
│   ├── layout.tsx         ← Loads chart deps
│   ├── reports/
│   └── insights/
```

```tsx
// app/(marketing)/layout.tsx — Minimal deps
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <MarketingHeader />
      {children}
      <MarketingFooter />
    </div>
  );
}

// app/(analytics)/layout.tsx — Heavy deps loaded only for analytics routes
import dynamic from 'next/dynamic';

const ChartProvider = dynamic(
  () => import('@/providers/ChartProvider'),
  { ssr: false }
);

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  return (
    <ChartProvider>
      <div className="min-h-screen">
        <AppHeader />
        {children}
      </div>
    </ChartProvider>
  );
}
```

**Measuring the impact of code splitting**:

```tsx
// scripts/analyze-chunks.ts
import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

function analyzeChunks() {
  const staticDir = join(process.cwd(), '.next', 'static', 'chunks');
  const chunks = readdirSync(staticDir)
    .filter(f => f.endsWith('.js'))
    .map(f => ({
      name: f,
      size: statSync(join(staticDir, f)).size / 1024,
    }))
    .sort((a, b) => b.size - a.size);

  console.log('\nChunk Analysis:');
  console.log('─'.repeat(60));

  let total = 0;
  for (const chunk of chunks) {
    const bar = '█'.repeat(Math.ceil(chunk.size / 10));
    console.log(`${chunk.name.padEnd(35)} ${chunk.size.toFixed(1).padStart(8)}KB ${bar}`);
    total += chunk.size;
  }

  console.log('─'.repeat(60));
  console.log(`Total: ${total.toFixed(1)}KB across ${chunks.length} chunks`);
}

analyzeChunks();
```

---

## Q15. (Advanced) How do you configure `next.config.ts` optimization flags for maximum performance?

**Scenario**: You need to document all performance-related configuration options in `next.config.ts` for your team.

**Answer**:

```tsx
// next.config.ts — Comprehensive production optimization
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // ═══════════════════════════════════════════════
  // CORE PERFORMANCE
  // ═══════════════════════════════════════════════

  // Enable gzip compression (default: true)
  compress: true,

  // Remove X-Powered-By header (saves bytes + security)
  poweredByHeader: false,

  // React strict mode (catches bugs, no performance impact in prod)
  reactStrictMode: true,

  // Generate ETags for caching (default: true)
  generateEtags: true,

  // Standalone output for optimized Docker deployments
  // Copies only necessary node_modules (reduces image size by ~80%)
  output: 'standalone',

  // ═══════════════════════════════════════════════
  // COMPILER OPTIMIZATIONS
  // ═══════════════════════════════════════════════

  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production'
      ? { exclude: ['error', 'warn'] }
      : false,

    // Styled-components optimization (if using)
    // styledComponents: true,

    // Emotion optimization (if using)
    // emotion: true,

    // React compiler (Next.js 15+)
    // reactCompiler: true,
  },

  // ═══════════════════════════════════════════════
  // BUNDLE OPTIMIZATION
  // ═══════════════════════════════════════════════

  experimental: {
    // Optimize barrel file imports
    optimizePackageImports: [
      'lodash-es',
      'date-fns',
      'lucide-react',
      '@heroicons/react/24/outline',
      '@heroicons/react/24/solid',
      '@mui/material',
      '@mui/icons-material',
      'recharts',
      'rxjs',
      '@iconify/react',
    ],

    // Client-side Router Cache configuration
    staleTimes: {
      dynamic: 30,   // Cache dynamic pages for 30s on client
      static: 300,   // Cache static pages for 5min on client
    },

    // Partial Prerendering (Next.js 15+)
    ppr: true,

    // Server Actions (stable in Next.js 15)
    serverActions: {
      bodySizeLimit: '2mb',
    },

    // Typed routes (type-safe Links)
    typedRoutes: true,
  },

  // Packages that should stay external on the server
  // (not bundled — reduces server bundle size)
  serverExternalPackages: [
    'sharp',
    'bcrypt',
    'canvas',
    '@prisma/client',
    'puppeteer',
  ],

  // ═══════════════════════════════════════════════
  // IMAGE OPTIMIZATION
  // ═══════════════════════════════════════════════

  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.example.com',
      },
    ],
  },

  // ═══════════════════════════════════════════════
  // CACHING HEADERS
  // ═══════════════════════════════════════════════

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

  // ═══════════════════════════════════════════════
  // TURBOPACK CONFIGURATION
  // ═══════════════════════════════════════════════

  turbopack: {
    resolveAlias: {
      '@': './src',
      '@components': './src/components',
      '@lib': './src/lib',
    },
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },

  // ═══════════════════════════════════════════════
  // LOGGING (development)
  // ═══════════════════════════════════════════════

  logging: {
    fetches: {
      fullUrl: true,
      hmrRefreshes: true,
    },
  },

  // ═══════════════════════════════════════════════
  // SOURCE MAPS
  // ═══════════════════════════════════════════════

  // Disable browser source maps in production (saves build time + size)
  productionBrowserSourceMaps: false,
};

export default nextConfig;
```

---

## Q16. (Advanced) How does Partial Prerendering (PPR) work in Next.js 15+, and how does it optimize build output?

**Scenario**: Your product page has static product info but a dynamic user-specific "Add to Cart" section. Currently the entire page is dynamic. PPR can make it partially static.

**Answer**:

**Partial Prerendering (PPR)** is a rendering strategy in Next.js 15+ that allows a single route to be **both static AND dynamic**. The static shell is served instantly from the CDN, and dynamic parts stream in via Suspense.

```
Traditional rendering:
  Static route:  Entire page pre-rendered at build ─── Fast, but stale
  Dynamic route: Entire page rendered per request  ─── Fresh, but slow

PPR:
  Static shell pre-rendered at build ──── Fast!
  Dynamic holes filled per request   ──── Fresh!

┌─────────────────────────────────────────────┐
│  Product Page (PPR)                          │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Product Image, Title, Description  │   │  ← STATIC
│  │  (pre-rendered at build time)       │   │     (served from CDN)
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  ██████████████████████████████████ │   │  ← DYNAMIC HOLE
│  │  Price (personalized), Add to Cart  │   │     (Suspense boundary)
│  │  (rendered per request)             │   │     (streams in)
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Reviews, Specs, Related Products   │   │  ← STATIC
│  │  (pre-rendered at build time)       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Enabling PPR**:

```tsx
// next.config.ts
const nextConfig = {
  experimental: {
    ppr: true, // Enable Partial Prerendering
  },
};
```

**Implementation**:

```tsx
// app/products/[id]/page.tsx
import { Suspense } from 'react';
import { getProduct, getReviews } from '@/lib/products';

// This page uses PPR:
// - Static: product info, reviews (pre-rendered)
// - Dynamic: personalized pricing, cart (streamed)

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // These fetches run at BUILD TIME (static)
  const product = await getProduct(id); // Cached
  const reviews = await getReviews(id); // Cached

  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* ═══ STATIC SHELL (pre-rendered at build) ═══ */}
      <div className="grid grid-cols-2 gap-8">
        <img src={product.image} alt={product.name} className="rounded-xl" />
        <div>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="mt-4 text-gray-600">{product.description}</p>

          {/* ═══ DYNAMIC HOLE (streamed per request) ═══ */}
          <Suspense fallback={<PriceSkeleton />}>
            <PersonalizedPricing productId={id} />
          </Suspense>

          <Suspense fallback={<CartButtonSkeleton />}>
            <AddToCartSection productId={id} />
          </Suspense>
        </div>
      </div>

      {/* ═══ STATIC (pre-rendered) ═══ */}
      <ReviewList reviews={reviews} />
      <RelatedProducts categoryId={product.categoryId} />
    </div>
  );
}

// Dynamic component — uses cookies() which forces dynamic rendering
async function PersonalizedPricing({ productId }: { productId: string }) {
  const { cookies } = await import('next/headers');
  const cookieStore = await cookies();
  const region = cookieStore.get('user-region')?.value || 'US';

  const pricing = await fetch(`https://api.example.com/pricing/${productId}?region=${region}`, {
    cache: 'no-store', // Always fresh
  }).then(r => r.json());

  return (
    <div className="mt-4">
      <p className="text-3xl font-bold text-green-600">
        {pricing.currency}{pricing.amount}
      </p>
      {pricing.discount && (
        <p className="text-sm text-red-500">
          {pricing.discount}% off — was {pricing.currency}{pricing.originalAmount}
        </p>
      )}
    </div>
  );
}
```

**Build output with PPR**:

```
Route (app)                     Size    First Load JS
┌ ◐ /products/[id]             8.2 kB   92.1 kB
│   ├ Static shell: 4.5KB (pre-rendered HTML)
│   └ Dynamic holes: 2 Suspense boundaries

◐ = Partially prerendered (PPR)
○ = Static
λ = Dynamic
```

**PPR vs other rendering strategies**:

| Strategy | Initial Load | Freshness | TTFB | When to Use |
|----------|-------------|-----------|------|-------------|
| Static (SSG) | Instant | Stale | ~50ms | Marketing, docs |
| ISR | Instant | Semi-fresh | ~50ms | Blog, catalog |
| Dynamic (SSR) | Slow | Always fresh | ~200-500ms | Dashboard, auth |
| **PPR** | **Fast static shell** | **Fresh dynamic parts** | **~50ms** | **Best of both worlds** |

---

## Q17. (Advanced) How do you optimize Next.js for serverless deployment (cold starts, bundle size, memory)?

**Scenario**: Your Next.js app deployed on AWS Lambda (or Vercel serverless functions) has 5-second cold starts. Users on the first request after idle periods experience terrible performance.

**Answer**:

```
Cold Start Anatomy:
  ┌──────────────────────────────────────┐
  │ 1. Container startup:     ~500ms     │
  │ 2. Node.js initialization: ~200ms    │
  │ 3. Load server bundle:    ~2000ms ← biggest bottleneck
  │ 4. Initialize framework:   ~500ms    │
  │ 5. Process first request:  ~800ms    │
  │ Total cold start:         ~4000ms    │
  └──────────────────────────────────────┘
```

**Optimization 1: Reduce server bundle size with `standalone` output**:

```tsx
// next.config.ts
const nextConfig = {
  output: 'standalone',
  // This creates a minimal deployment package:
  // .next/standalone/
  //   ├── server.js         (entry point)
  //   ├── node_modules/     (only used packages — NOT everything)
  //   └── .next/            (build output)
  //
  // Typical reduction: 500MB → 50MB
};
```

**Optimization 2: Externalize heavy packages**:

```tsx
// next.config.ts
const nextConfig = {
  // Keep these as external — don't bundle into server code
  serverExternalPackages: [
    'sharp',          // Image processing (native addon)
    '@prisma/client', // Database client
    'bcrypt',         // Native crypto
    'canvas',         // Native rendering
    'puppeteer',      // Browser automation
  ],

  // For Turbopack, use:
  turbopack: {
    resolveAlias: {
      // Replace heavy dev dependencies with lighter alternatives
    },
  },
};
```

**Optimization 3: Lazy initialization of expensive resources**:

```tsx
// ❌ BAD: Initialize on module load (every cold start pays this cost)
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient(); // Runs on every cold start!

// ✅ GOOD: Lazy singleton — only initialize when first used
let prisma: PrismaClient | null = null;

export function getDb(): PrismaClient {
  if (!prisma) {
    prisma = new PrismaClient({
      log: process.env.NODE_ENV === 'development' ? ['query'] : [],
    });
  }
  return prisma;
}
```

```tsx
// ✅ EVEN BETTER: Module-level lazy with top-level await guard
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}
```

**Optimization 4: Route-level function splitting**:

```tsx
// Vercel automatically splits each route into its own serverless function
// But you can control the grouping:

// next.config.ts
const nextConfig = {
  // Each route gets its own function (default on Vercel)
  // This means /api/users and /api/posts are separate functions
  // with separate cold starts but smaller bundles

  // For self-hosted Lambda:
  output: 'standalone',
};
```

**Optimization 5: Keep functions warm**:

```tsx
// lib/keep-warm.ts (for self-hosted serverless)
// A cron job that pings your functions to prevent cold starts

// Vercel: Use vercel.json crons
// vercel.json
{
  "crons": [
    {
      "path": "/api/health",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

```tsx
// app/api/health/route.ts
export const runtime = 'nodejs'; // or 'edge'

export async function GET() {
  return Response.json({
    status: 'ok',
    timestamp: Date.now(),
    region: process.env.VERCEL_REGION || 'unknown',
  });
}
```

**Optimization 6: Use Edge Runtime for lightweight routes**:

```tsx
// app/api/lightweight/route.ts
export const runtime = 'edge'; // Runs on V8 isolates — near-zero cold start

export async function GET(request: Request) {
  // Edge Runtime limitations:
  // - No Node.js APIs (fs, path, crypto)
  // - No native addons
  // - Limited to Web APIs
  // But: ~0ms cold start!

  const data = await fetch('https://api.example.com/data').then(r => r.json());
  return Response.json(data);
}
```

**Cold start comparison**:

| Runtime | Cold Start | Best For |
|---------|-----------|----------|
| Node.js Serverless | 1-5s | Full API routes, SSR |
| Edge Runtime | ~0ms | Lightweight APIs, middleware |
| Node.js + standalone | 1-3s | Docker/K8s deployments |
| Node.js + warm pool | ~0ms | High-traffic routes |

---

## Q18. (Advanced) How do you use the React Compiler (React 19) with Next.js for automatic optimization?

**Scenario**: Your team manually adds `useMemo`, `useCallback`, and `React.memo` everywhere. The React Compiler can automate this. How do you set it up with Next.js?

**Answer**:

The **React Compiler** (previously "React Forget") is an automatic optimization tool that adds memoization to your React components at build time. It ships with React 19 and is supported in Next.js 15+.

```
Without React Compiler:
  Component renders → re-creates functions, objects → children re-render

  function Parent() {
    const [count, setCount] = useState(0);
    const items = [1, 2, 3]; // ← New array EVERY render
    const handler = () => {}; // ← New function EVERY render
    return <Child items={items} onClick={handler} />;
    // Child re-renders every time Parent renders,
    // even if count change is unrelated to Child
  }

With React Compiler:
  function Parent() {
    const [count, setCount] = useState(0);
    const items = [1, 2, 3];     // ← Compiler auto-memoizes
    const handler = () => {};     // ← Compiler auto-memoizes
    return <Child items={items} onClick={handler} />;
    // Child SKIPS re-render if items and handler haven't changed
    // Compiler adds memoization automatically!
  }
```

**Enabling the React Compiler in Next.js**:

```bash
npm install -D babel-plugin-react-compiler
```

```tsx
// next.config.ts
const nextConfig = {
  experimental: {
    reactCompiler: true,
    // Or with options:
    reactCompiler: {
      compilationMode: 'annotation', // Only compile opted-in components
    },
  },
};
```

**What the compiler does automatically**:

```tsx
// YOUR CODE (what you write):
function ProductCard({ product, onAddToCart }) {
  const discountedPrice = product.price * (1 - product.discount);
  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(discountedPrice);

  return (
    <div className="border rounded-lg p-4">
      <h3>{product.name}</h3>
      <p>{formattedPrice}</p>
      <button onClick={() => onAddToCart(product.id)}>Add to Cart</button>
    </div>
  );
}

// COMPILED OUTPUT (what the compiler produces — conceptually):
function ProductCard({ product, onAddToCart }) {
  const $ = useMemoCache(5); // Compiler-generated cache

  let discountedPrice;
  if ($[0] !== product.price || $[1] !== product.discount) {
    discountedPrice = product.price * (1 - product.discount);
    $[0] = product.price;
    $[1] = product.discount;
    $[2] = discountedPrice;
  } else {
    discountedPrice = $[2];
  }

  // ... similar memoization for formattedPrice, JSX, callbacks
}
```

**Compiler modes**:

```tsx
// Mode 1: Full (default) — compile everything
const nextConfig = {
  experimental: {
    reactCompiler: true,
  },
};

// Mode 2: Annotation — only compile opted-in components
const nextConfig = {
  experimental: {
    reactCompiler: {
      compilationMode: 'annotation',
    },
  },
};

// Then opt in with directive:
'use memo'; // ← Compiler directive
function ExpensiveComponent({ data }) {
  // This component will be auto-memoized
}

// Mode 3: Opt-out specific components
'use no memo'; // ← Skip compiler for this component
function SimpleComponent({ text }) {
  return <span>{text}</span>;
}
```

**After enabling the compiler, you can remove manual memoization**:

```tsx
// BEFORE (manual memoization):
const MemoizedChild = React.memo(ChildComponent);

function Parent() {
  const [count, setCount] = useState(0);
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);
  const config = useMemo(() => ({ theme: 'dark' }), []);

  return <MemoizedChild onClick={handleClick} config={config} />;
}

// AFTER (compiler handles it):
function Parent() {
  const [count, setCount] = useState(0);
  const handleClick = () => console.log('clicked');
  const config = { theme: 'dark' };

  return <ChildComponent onClick={handleClick} config={config} />;
}
// Compiler auto-memoizes everything! Cleaner code, same performance.
```

---

## Q19. (Advanced) How do you set up build performance monitoring and regression detection?

**Scenario**: Your build times are creeping up over months. You need automated tracking and alerts when build performance degrades.

**Answer**:

```tsx
// scripts/build-metrics.ts
import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

interface BuildMetrics {
  timestamp: string;
  commitSha: string;
  branch: string;
  totalBuildTime: number;
  routeCount: number;
  staticRoutes: number;
  dynamicRoutes: number;
  firstLoadJsShared: number;
  largestPageJs: number;
  totalAssetSize: number;
  nodeModulesSize?: number;
  warnings: string[];
}

async function collectBuildMetrics(): Promise<BuildMetrics> {
  const startTime = Date.now();

  // Run the build
  try {
    execSync('next build', {
      stdio: 'pipe',
      env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1' },
    });
  } catch (error: any) {
    console.error('Build failed:', error.stderr?.toString());
    process.exit(1);
  }

  const buildTime = Date.now() - startTime;

  // Parse build output
  const buildManifest = JSON.parse(
    readFileSync(join('.next', 'build-manifest.json'), 'utf-8')
  );

  const routesManifest = JSON.parse(
    readFileSync(join('.next', 'routes-manifest.json'), 'utf-8')
  );

  // Calculate sizes
  const staticDir = join('.next', 'static');
  const totalAssetSize = getDirectorySize(staticDir);

  // Get chunk sizes
  const chunksDir = join(staticDir, 'chunks');
  const chunks = existsSync(chunksDir)
    ? require('fs').readdirSync(chunksDir)
        .filter((f: string) => f.endsWith('.js'))
        .map((f: string) => ({
          name: f,
          size: require('fs').statSync(join(chunksDir, f)).size,
        }))
    : [];

  const sharedSize = chunks
    .filter((c: any) => c.name.includes('framework') || c.name.includes('main'))
    .reduce((sum: number, c: any) => sum + c.size, 0);

  const largestPage = Math.max(...chunks.map((c: any) => c.size), 0);

  const metrics: BuildMetrics = {
    timestamp: new Date().toISOString(),
    commitSha: execSync('git rev-parse HEAD').toString().trim(),
    branch: execSync('git branch --show-current').toString().trim(),
    totalBuildTime: buildTime,
    routeCount: routesManifest.staticRoutes.length + routesManifest.dynamicRoutes.length,
    staticRoutes: routesManifest.staticRoutes.length,
    dynamicRoutes: routesManifest.dynamicRoutes.length,
    firstLoadJsShared: Math.round(sharedSize / 1024),
    largestPageJs: Math.round(largestPage / 1024),
    totalAssetSize: Math.round(totalAssetSize / 1024),
    warnings: [],
  };

  // Check for regressions
  const previousMetrics = loadPreviousMetrics();
  if (previousMetrics) {
    const buildTimeDiff = metrics.totalBuildTime - previousMetrics.totalBuildTime;
    const sizeDiff = metrics.firstLoadJsShared - previousMetrics.firstLoadJsShared;

    if (buildTimeDiff > 30000) { // 30s slower
      metrics.warnings.push(
        `Build time increased by ${(buildTimeDiff / 1000).toFixed(1)}s`
      );
    }
    if (sizeDiff > 10) { // 10KB larger
      metrics.warnings.push(
        `Shared JS increased by ${sizeDiff}KB`
      );
    }
  }

  return metrics;
}

function getDirectorySize(dir: string): number {
  const fs = require('fs');
  const path = require('path');
  let size = 0;

  if (!fs.existsSync(dir)) return 0;

  for (const file of fs.readdirSync(dir)) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      size += getDirectorySize(filePath);
    } else {
      size += stat.size;
    }
  }
  return size;
}

function loadPreviousMetrics(): BuildMetrics | null {
  const metricsFile = join('.next', 'build-metrics.json');
  if (existsSync(metricsFile)) {
    return JSON.parse(readFileSync(metricsFile, 'utf-8'));
  }
  return null;
}

// Run
collectBuildMetrics().then((metrics) => {
  console.log('\n📊 Build Metrics:');
  console.log(`  Build Time:     ${(metrics.totalBuildTime / 1000).toFixed(1)}s`);
  console.log(`  Routes:         ${metrics.routeCount} (${metrics.staticRoutes} static, ${metrics.dynamicRoutes} dynamic)`);
  console.log(`  Shared JS:      ${metrics.firstLoadJsShared}KB`);
  console.log(`  Largest Page:   ${metrics.largestPageJs}KB`);
  console.log(`  Total Assets:   ${metrics.totalAssetSize}KB`);

  if (metrics.warnings.length > 0) {
    console.log('\n⚠️  Warnings:');
    metrics.warnings.forEach((w) => console.log(`  - ${w}`));
  }

  // Save for next comparison
  writeFileSync(
    join('.next', 'build-metrics.json'),
    JSON.stringify(metrics, null, 2)
  );
});
```

**GitHub Action for build size regression detection**:

```yaml
# .github/workflows/bundle-check.yml
name: Bundle Size Check
on: [pull_request]

jobs:
  bundle-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci

      - name: Build and measure
        run: |
          npm run build
          node scripts/build-metrics.ts > metrics.json

      - name: Compare with main
        uses: actions/github-script@v7
        with:
          script: |
            const metrics = require('./metrics.json');
            const MAX_SHARED_JS = 100; // KB
            const MAX_BUILD_TIME = 120; // seconds

            let comment = '## Bundle Size Report\n\n';
            comment += `| Metric | Value | Limit | Status |\n`;
            comment += `|--------|-------|-------|--------|\n`;
            comment += `| Shared JS | ${metrics.firstLoadJsShared}KB | ${MAX_SHARED_JS}KB | ${metrics.firstLoadJsShared <= MAX_SHARED_JS ? '✅' : '❌'} |\n`;
            comment += `| Build Time | ${(metrics.totalBuildTime/1000).toFixed(1)}s | ${MAX_BUILD_TIME}s | ${metrics.totalBuildTime/1000 <= MAX_BUILD_TIME ? '✅' : '❌'} |\n`;

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: comment,
            });
```

---

## Q20. (Advanced) What is the complete build optimization strategy for a Next.js application targeting Core Web Vitals?

**Scenario**: Your Lighthouse score is 65. You need to get it above 90 for all Core Web Vitals (LCP, FID/INP, CLS) through build optimization alone.

**Answer**:

```
Core Web Vitals Targets:
  LCP  (Largest Contentful Paint): < 2.5s  ← Build: reduce JS, optimize images
  INP  (Interaction to Next Paint): < 200ms ← Build: code split, reduce main thread work
  CLS  (Cumulative Layout Shift):  < 0.1   ← Build: font optimization, image dimensions

Current scores:
  LCP: 4.2s  ❌  (too much JS blocking render)
  INP: 350ms ❌  (heavy main thread work)
  CLS: 0.25  ❌  (layout shifts from fonts + images)
```

**LCP Optimization (build-level)**:

```tsx
// 1. Preload critical assets
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        {/* Preload LCP image */}
        <link
          rel="preload"
          href="/hero-image.webp"
          as="image"
          type="image/webp"
          fetchPriority="high"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}

// 2. Use priority on LCP images
import Image from 'next/image';

<Image
  src="/hero.webp"
  alt="Hero"
  width={1200}
  height={600}
  priority  // Adds fetchpriority="high" and preload
  sizes="100vw"
/>

// 3. Inline critical CSS (Next.js does this automatically for small CSS)
// No config needed — CSS < 2KB is automatically inlined

// 4. Reduce blocking JS
// Move heavy components below the fold with lazy loading
const BelowFold = dynamic(() => import('./BelowFold'), {
  ssr: true, // Still SSR, but JS is split
});
```

**INP Optimization (build-level)**:

```tsx
// 1. Code split event handlers
// ❌ Heavy handler loaded upfront
import { processData } from './heavy-processor'; // 100KB

function Button() {
  return <button onClick={() => processData()}>Process</button>;
}

// ✅ Handler loaded on demand
function Button() {
  const handleClick = async () => {
    const { processData } = await import('./heavy-processor');
    processData();
  };
  return <button onClick={handleClick}>Process</button>;
}

// 2. Use React.startTransition for non-urgent updates
'use client';
import { startTransition, useState } from 'react';

function SearchFilter({ onFilter }) {
  const [query, setQuery] = useState('');

  return (
    <input
      value={query}
      onChange={(e) => {
        setQuery(e.target.value); // Urgent: update input immediately
        startTransition(() => {
          onFilter(e.target.value); // Non-urgent: can be deferred
        });
      }}
    />
  );
}

// 3. Use React Compiler for automatic memoization
// next.config.ts
const nextConfig = {
  experimental: {
    reactCompiler: true,
  },
};
```

**CLS Optimization (build-level)**:

```tsx
// 1. Font optimization — prevent layout shift
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',          // Show fallback font immediately
  adjustFontFallback: true, // Adjust metrics to match fallback
  preload: true,
});

// 2. Image dimensions — always specify width/height
<Image
  src={product.image}
  alt={product.name}
  width={400}
  height={300}
  placeholder="blur"
  blurDataURL={product.blurHash} // Prevent empty space during load
/>

// 3. Skeleton loading states with exact dimensions
export default function Loading() {
  return (
    <div className="space-y-4">
      {/* Match exact layout of loaded content */}
      <div className="h-[600px] w-full bg-gray-100 animate-pulse rounded-xl" />
      <div className="h-8 w-1/3 bg-gray-100 animate-pulse rounded" />
      <div className="h-4 w-2/3 bg-gray-100 animate-pulse rounded" />
    </div>
  );
}

// 4. Reserve space for dynamic content
<div className="min-h-[200px]"> {/* Reserve space */}
  <Suspense fallback={<AdSkeleton />}>
    <DynamicAd />
  </Suspense>
</div>
```

**Complete optimization config**:

```tsx
// next.config.ts — Optimized for Core Web Vitals
const nextConfig = {
  compress: true,
  poweredByHeader: false,
  reactStrictMode: true,

  compiler: {
    removeConsole: process.env.NODE_ENV === 'production'
      ? { exclude: ['error'] }
      : false,
    reactCompiler: true,
  },

  experimental: {
    ppr: true,
    optimizePackageImports: ['lucide-react', 'date-fns', '@mui/material'],
    staleTimes: { dynamic: 30, static: 300 },
  },

  images: {
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 2592000,
  },

  async headers() {
    return [
      {
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
        ],
      },
    ];
  },
};
```

**After optimization**:

```
Lighthouse Score: 96 ✅

LCP:  1.8s  ✅  (was 4.2s — reduced JS, optimized images, PPR)
INP:  120ms ✅  (was 350ms — code splitting, React Compiler)
CLS:  0.02  ✅  (was 0.25 — font optimization, image dimensions)
```

---
