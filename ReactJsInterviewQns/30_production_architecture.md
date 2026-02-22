# Production-Grade React Architecture & System Design — React 18/19 Interview Questions

## Topic Introduction

Building a **production-grade React application** goes far beyond knowing hooks, state management, and component composition. It is the intersection of software architecture, infrastructure engineering, developer experience, and product reliability. A production-grade React app is one that can be deployed with confidence, scaled across teams, monitored in real time, recovered from failure gracefully, and evolved over years without a rewrite. It means having a thoughtful project structure that scales to hundreds of components, a CI/CD pipeline that catches regressions before they reach users, an error monitoring system that alerts engineers within seconds, feature flags that decouple deployments from releases, and a performance budget enforced by automated tooling. In interviews at companies like Meta, Stripe, Airbnb, and Shopify, senior and staff-level candidates are expected to design entire frontend systems — not just implement UI features — and articulate the trade-offs behind architectural choices.

What separates a hobby project from a production system is the **operational surface area**: environment configuration across dev/staging/production, authentication flows with refresh token rotation, internationalization that supports right-to-left languages and pluralization rules, analytics instrumentation that respects user consent, offline-first capabilities for unreliable networks, and deployment strategies that minimize downtime. A production React application is also a **team artifact** — it must support multiple engineers working in parallel through monorepo tooling, design systems, clear module boundaries, and architectural decision records. React 18's concurrent features (Suspense, transitions, streaming SSR) and React 19's server actions, `use()` hook, and enhanced form handling have further expanded what "production-grade" means by enabling new patterns for data fetching, progressive rendering, and server/client composition.

The following code illustrates the skeleton of a production React application's entry point — notice the layered provider architecture, error boundaries, monitoring initialization, and feature flag integration that you would never see in a tutorial app:

```jsx
// src/main.tsx — Production application entry point
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import * as Sentry from '@sentry/react';
import { FlagProvider } from '@unleash/proxy-client-react';
import { IntlProvider } from 'react-intl';
import { AuthProvider } from '@/features/auth/AuthProvider';
import { ThemeProvider } from '@/design-system/ThemeProvider';
import { AppErrorBoundary } from '@/components/AppErrorBoundary';
import { PerformanceMonitor } from '@/monitoring/PerformanceMonitor';
import { loadMessages, detectLocale } from '@/i18n';
import { appConfig } from '@/config';
import App from './App';

// Initialize error monitoring before anything else
Sentry.init({
  dsn: appConfig.SENTRY_DSN,
  environment: appConfig.APP_ENV,
  release: appConfig.APP_VERSION,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration({ maskAllText: true }),
  ],
  tracesSampleRate: appConfig.APP_ENV === 'production' ? 0.1 : 1.0,
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: (failureCount, error) => {
        if (error?.status === 401 || error?.status === 403) return false;
        return failureCount < 3;
      },
    },
  },
});

const locale = detectLocale();
const messages = await loadMessages(locale);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Sentry.ErrorBoundary fallback={<AppErrorBoundary />}>
      <FlagProvider config={{ url: appConfig.UNLEASH_URL, clientKey: appConfig.UNLEASH_KEY }}>
        <IntlProvider locale={locale} messages={messages}>
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              <ThemeProvider>
                <BrowserRouter>
                  <PerformanceMonitor />
                  <App />
                </BrowserRouter>
              </ThemeProvider>
            </AuthProvider>
            {appConfig.APP_ENV !== 'production' && <ReactQueryDevtools />}
          </QueryClientProvider>
        </IntlProvider>
      </FlagProvider>
    </Sentry.ErrorBoundary>
  </StrictMode>
);
```

---

## Beginner Level (Q1–Q5)

---

### Q1. How should you structure a large-scale React project, and why is feature-based organization preferred over type-based organization?

**Answer:**

In a **type-based** (or "Rails-style") structure, files are grouped by their technical role — all components in `/components`, all hooks in `/hooks`, all services in `/services`. This works for small apps but breaks down at scale because a single feature's code is scattered across many directories, making it hard to understand, modify, or delete a feature in isolation.

A **feature-based** (or "domain-driven") structure groups files by business domain. Each feature folder is a self-contained module with its own components, hooks, API calls, types, tests, and utilities. This approach mirrors how product teams think — in terms of features, not file types — and enables better code ownership, lazy loading at the feature boundary, and easier extraction into packages or micro-frontends.

The key architectural principles are:
- **Colocation**: keep related code together (tests next to components, types next to implementations).
- **Explicit public API**: each feature exports only what other features need via a barrel `index.ts`.
- **Dependency direction**: features can depend on `shared/` but never on each other directly — cross-feature communication goes through the global state or event bus.
- **Flat within features**: avoid deeply nested folders; 2-3 levels deep is the practical maximum.

```jsx
// Feature-based project structure for a large React application
//
// src/
// ├── app/                        # Application shell
// │   ├── App.tsx                 # Root component, route definitions
// │   ├── AppProviders.tsx        # Composed provider tree
// │   └── routes.tsx              # Route configuration (lazy-loaded)
// │
// ├── features/                   # Business domains (the heart of the app)
// │   ├── auth/
// │   │   ├── components/         # LoginForm, SignupForm, ProtectedRoute
// │   │   ├── hooks/              # useAuth, useSession, usePermissions
// │   │   ├── api/                # authApi.ts (login, logout, refresh)
// │   │   ├── stores/             # authStore.ts (Zustand slice or context)
// │   │   ├── types/              # auth.types.ts
// │   │   ├── utils/              # tokenStorage.ts, roleChecks.ts
// │   │   ├── __tests__/          # Unit and integration tests
// │   │   └── index.ts            # Public API: export { useAuth, ProtectedRoute }
// │   │
// │   ├── dashboard/
// │   │   ├── components/
// │   │   ├── hooks/
// │   │   ├── api/
// │   │   └── index.ts
// │   │
// │   └── settings/
// │       ├── components/
// │       ├── hooks/
// │       └── index.ts
// │
// ├── shared/                     # Cross-cutting concerns (no business logic)
// │   ├── components/             # Button, Modal, Toast, DataTable
// │   ├── hooks/                  # useDebounce, useMediaQuery, useLocalStorage
// │   ├── utils/                  # formatDate, cn(), invariant()
// │   ├── types/                  # ApiResponse<T>, Pagination, etc.
// │   └── constants/              # ROUTES, QUERY_KEYS, BREAKPOINTS
// │
// ├── design-system/              # Theme tokens, global styles
// ├── config/                     # Environment config, feature flags
// ├── i18n/                       # Translations, locale setup
// ├── monitoring/                 # Sentry, analytics, Web Vitals
// └── lib/                        # Configured third-party instances (axios, queryClient)

// Enforcing boundaries with ESLint
// .eslintrc.js
module.exports = {
  rules: {
    'no-restricted-imports': ['error', {
      patterns: [
        {
          group: ['@/features/*/*'],
          message: 'Import from feature index: @/features/auth, not @/features/auth/hooks/useAuth',
        },
      ],
    }],
  },
};
```

**Why it matters in production:** Feature-based structure enables parallel team development (team A owns `features/checkout`, team B owns `features/catalog`), clean code splitting (each feature is a lazy-loaded route), and safe deletion (removing a feature means deleting one folder and its route entry).

---

### Q2. What is a monorepo, and how do tools like Nx and Turborepo help manage large React codebases?

**Answer:**

A **monorepo** is a single version-controlled repository that contains multiple projects (applications and libraries). For React teams, this typically means housing the web app, mobile app (React Native), component library, shared utilities, API client, and configuration packages in one repository. The alternative — polyrepo — puts each in its own repository, which causes dependency synchronization nightmares, duplicated configuration, and slow cross-project changes.

**Nx** and **Turborepo** are monorepo build orchestration tools that solve the key challenge: when you have 50+ packages, you cannot rebuild and retest everything on every commit. Both tools provide:

1. **Task caching**: if the inputs (source code + dependencies) haven't changed, skip the build/test and return the cached output. Turborepo also supports **remote caching** so CI and teammates share build artifacts.
2. **Task orchestration**: run tasks in the correct dependency order with maximum parallelism. If `app` depends on `ui-lib` and `utils`, build `utils` first, then `ui-lib` and `app` in parallel.
3. **Affected detection**: only run tasks for projects that were impacted by the current changeset.

**Nx** goes further with code generators, dependency graph visualization, and first-class support for module boundaries via `@nx/enforce-module-boundaries` ESLint rule. **Turborepo** is lighter and focuses purely on task running and caching.

```jsx
// Example Turborepo monorepo structure for a React product team
//
// my-company/
// ├── apps/
// │   ├── web/                  # Main React SPA (Vite + React 18)
// │   ├── admin/                # Admin dashboard (Next.js)
// │   └── mobile/               # React Native app
// │
// ├── packages/
// │   ├── ui/                   # Shared component library
// │   │   ├── src/
// │   │   │   ├── Button/
// │   │   │   ├── Modal/
// │   │   │   └── index.ts
// │   │   ├── package.json      # { "name": "@company/ui" }
// │   │   └── tsconfig.json
// │   │
// │   ├── api-client/           # Generated API client (OpenAPI → TypeScript)
// │   │   ├── src/
// │   │   └── package.json      # { "name": "@company/api-client" }
// │   │
// │   ├── utils/                # Shared utilities
// │   ├── config-eslint/        # Shared ESLint config
// │   ├── config-typescript/    # Shared TSConfig base
// │   └── config-tailwind/      # Shared Tailwind preset
// │
// ├── turbo.json
// └── package.json              # Root with workspaces

// turbo.json — Task pipeline definition
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [".env"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],      // Build dependencies first (topological)
      "outputs": ["dist/**", ".next/**"],
      "env": ["NODE_ENV", "API_URL"]
    },
    "test": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tests/**"],
      "cache": true
    },
    "lint": {
      "cache": true
    },
    "dev": {
      "persistent": true,            // Long-running dev server
      "cache": false
    }
  }
}

// Using a shared package in the web app:
// apps/web/package.json
{
  "dependencies": {
    "@company/ui": "workspace:*",
    "@company/api-client": "workspace:*",
    "@company/utils": "workspace:*"
  }
}

// apps/web/src/pages/Dashboard.tsx
import { Button, Card, DataTable } from '@company/ui';
import { useGetOrders } from '@company/api-client';
import { formatCurrency } from '@company/utils';

export function Dashboard() {
  const { data: orders } = useGetOrders();
  return (
    <Card>
      <DataTable
        data={orders}
        columns={[
          { key: 'id', header: 'Order ID' },
          { key: 'total', header: 'Total', render: (v) => formatCurrency(v) },
        ]}
      />
      <Button variant="primary">Export</Button>
    </Card>
  );
}
```

**Production tip:** Run `turbo run build --filter=web...` to build only the `web` app and its transitive dependencies. On CI, combine this with remote caching (`--remote-cache`) to cut build times from 15 minutes to under 2 minutes for unchanged packages.

---

### Q3. How do you manage environment-specific configuration across development, staging, and production in a React application?

**Answer:**

Environment configuration in React apps must solve three problems: (1) injecting different values per environment (API URLs, feature flags, analytics keys), (2) preventing secrets from leaking into the client bundle, and (3) validating that required variables are present at build time — not at runtime when a user hits a blank page.

**The build-time approach** (Vite, Create React App) replaces `import.meta.env.VITE_*` or `process.env.REACT_APP_*` references at bundle time. The values are literally string-replaced into the JavaScript, meaning they are public and visible in the bundle. This is appropriate for API URLs and public keys, never for secrets.

**The runtime approach** injects config via a `<script>` tag that sets `window.__CONFIG__` before the app loads. This lets you build once and deploy the same artifact to staging and production, just swapping the config injection (often via Kubernetes ConfigMaps or CDN edge functions). This is the preferred pattern for Docker-based deployments.

**Validation** is critical — use a library like `zod` to parse environment variables at startup and fail fast with descriptive errors.

```jsx
// 1. Build-time config with Vite — .env files
// .env                  → shared defaults
// .env.development      → local dev overrides
// .env.staging          → staging (loaded via --mode staging)
// .env.production       → production values

// .env.production
// VITE_API_URL=https://api.myapp.com
// VITE_SENTRY_DSN=https://abc@sentry.io/123
// VITE_APP_ENV=production
// VITE_UNLEASH_URL=https://flags.myapp.com/api/frontend

// 2. Validated config module — src/config/index.ts
import { z } from 'zod';

const envSchema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_APP_ENV: z.enum(['development', 'staging', 'production']),
  VITE_SENTRY_DSN: z.string().url(),
  VITE_UNLEASH_URL: z.string().url(),
  VITE_APP_VERSION: z.string().default('0.0.0-dev'),
});

// Parse and validate — throws at build/startup if invalid
const parsed = envSchema.safeParse(import.meta.env);

if (!parsed.success) {
  console.error('❌ Invalid environment configuration:');
  console.error(parsed.error.flatten().fieldErrors);
  throw new Error('Missing or invalid environment variables. Check .env files.');
}

export const appConfig = Object.freeze({
  API_URL: parsed.data.VITE_API_URL,
  APP_ENV: parsed.data.VITE_APP_ENV,
  SENTRY_DSN: parsed.data.VITE_SENTRY_DSN,
  UNLEASH_URL: parsed.data.VITE_UNLEASH_URL,
  APP_VERSION: parsed.data.VITE_APP_VERSION,
  IS_PRODUCTION: parsed.data.VITE_APP_ENV === 'production',
  IS_DEV: parsed.data.VITE_APP_ENV === 'development',
});

// 3. Runtime config for build-once-deploy-everywhere
// public/config.js — overwritten per environment at deploy time
// window.__RUNTIME_CONFIG__ = {
//   API_URL: "https://api.myapp.com",
//   FEATURE_FLAGS_URL: "https://flags.myapp.com"
// };

// src/config/runtime.ts
const runtimeConfig = window.__RUNTIME_CONFIG__ ?? {};
export const apiUrl = runtimeConfig.API_URL || import.meta.env.VITE_API_URL;

// 4. Using config in components — never reference import.meta.env directly
import { appConfig } from '@/config';

function ApiStatus() {
  return (
    <footer>
      <small>
        ENV: {appConfig.APP_ENV} | Version: {appConfig.APP_VERSION}
      </small>
    </footer>
  );
}
```

**Key rule:** Components and hooks import from `@/config`, never from `import.meta.env` directly. This creates a single source of truth, enables testing with mock configs, and makes environment switches trivial.

---

### Q4. What does a CI/CD pipeline for a production React application look like, and what stages should it include?

**Answer:**

A robust CI/CD pipeline for React ensures that every change is validated before reaching users. The pipeline typically runs on GitHub Actions, GitLab CI, or CircleCI and consists of these stages:

1. **Install & Cache** — Install dependencies with a lockfile (`npm ci`) and cache `node_modules` for subsequent runs.
2. **Lint & Type Check** — Run ESLint and TypeScript compiler (`tsc --noEmit`) in parallel. These catch issues instantly without running the full build.
3. **Unit & Integration Tests** — Run Vitest/Jest with coverage thresholds. Fail the build if coverage drops below the configured minimum.
4. **Build** — Create the production bundle. This also validates that the build succeeds with production environment variables.
5. **E2E Tests** — Run Playwright or Cypress against the built app (served via `preview`). Tests critical user flows: login, core feature, checkout.
6. **Bundle Analysis** — Check bundle size against a budget. Fail if the main bundle exceeds 200KB gzipped.
7. **Deploy to Preview** — Deploy a preview environment for the PR (Vercel preview, Netlify deploy preview, or custom).
8. **Deploy to Production** — On merge to `main`, deploy to production with a canary or blue-green strategy.

```jsx
// .github/workflows/ci.yml — GitHub Actions pipeline
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true          # Cancel stale PR runs

jobs:
  quality:
    name: Lint, Type Check & Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      # Run lint, typecheck, and test in parallel
      - name: Lint
        run: npm run lint

      - name: Type Check
        run: npx tsc --noEmit

      - name: Unit Tests
        run: npm run test -- --coverage --reporter=json
        env:
          CI: true

      - name: Check Coverage Thresholds
        run: |
          node -e "
            const coverage = require('./coverage/coverage-summary.json');
            const { lines, branches } = coverage.total;
            if (lines.pct < 80 || branches.pct < 75) {
              console.error('Coverage below threshold');
              process.exit(1);
            }
          "

  build:
    name: Build & Bundle Analysis
    runs-on: ubuntu-latest
    needs: quality
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npm run build
        env:
          VITE_APP_ENV: production
          VITE_API_URL: ${{ secrets.API_URL }}

      # Bundle size check
      - name: Bundle Size
        uses: andresz1/size-limit-action@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # Configured in package.json "size-limit" field

      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - uses: actions/download-artifact@v4
        with: { name: build-output, path: dist/ }
      - name: Run Playwright
        run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/

  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, e2e]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/download-artifact@v4
        with: { name: build-output, path: dist/ }
      - name: Deploy to CDN
        run: npx wrangler pages deploy dist/ --project-name=my-app
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_TOKEN }}
```

**Production tip:** Use `concurrency` groups to cancel outdated CI runs on the same PR. Use `actions/cache` aggressively. Gate production deploys behind manual approval for critical apps. Add Slack/Teams notifications on deploy success or failure.

---

### Q5. What is error monitoring in production React apps, and how do you integrate a tool like Sentry?

**Answer:**

Error monitoring captures, aggregates, and alerts on runtime errors that occur in users' browsers. Without it, you are blind to bugs that slip past testing — JavaScript exceptions, unhandled promise rejections, API failures, and rendering errors. **Sentry** is the industry standard for frontend error monitoring.

The integration has four layers:
1. **Global error capture** — Sentry's SDK hooks into `window.onerror` and `window.onunhandledrejection` to catch uncaught exceptions.
2. **React Error Boundaries** — Sentry provides `<Sentry.ErrorBoundary>` that catches rendering errors in the component tree and reports them with the full component stack.
3. **Performance tracing** — Sentry can trace page loads and navigations as "transactions," breaking them down into spans (API calls, component renders).
4. **Session Replay** — Records DOM mutations so you can watch exactly what the user saw when the error occurred (with PII masking).

A good setup also includes **source map uploads** so that minified stack traces are deobfuscated, **release tracking** so errors are tied to specific deployments, and **alerting rules** so the on-call engineer is paged for new critical errors.

```jsx
// src/monitoring/sentry.ts — Initialize Sentry with production best practices
import * as Sentry from '@sentry/react';
import { appConfig } from '@/config';

export function initSentry() {
  if (appConfig.IS_DEV) return; // Don't pollute Sentry in development

  Sentry.init({
    dsn: appConfig.SENTRY_DSN,
    environment: appConfig.APP_ENV,
    release: `my-app@${appConfig.APP_VERSION}`,

    integrations: [
      // Automatic performance instrumentation
      Sentry.browserTracingIntegration({
        tracePropagationTargets: ['api.myapp.com'], // Only trace our API
      }),
      // Session replay for debugging — capture 10% of sessions, 100% on error
      Sentry.replayIntegration({
        maskAllText: true,      // PII protection
        blockAllMedia: true,
      }),
    ],

    tracesSampleRate: appConfig.APP_ENV === 'production' ? 0.1 : 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Filter out noise
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      'Non-Error promise rejection captured',
      /Loading chunk \d+ failed/,     // Code splitting failures (retry instead)
    ],

    beforeSend(event) {
      // Don't send errors from browser extensions
      if (event.exception?.values?.[0]?.stacktrace?.frames?.some(
        f => f.filename?.includes('chrome-extension')
      )) {
        return null;
      }
      return event;
    },
  });
}

// src/components/AppErrorBoundary.tsx
import * as Sentry from '@sentry/react';

export function AppErrorBoundary({ children }) {
  return (
    <Sentry.ErrorBoundary
      fallback={({ error, resetError }) => (
        <div role="alert" className="error-page">
          <h1>Something went wrong</h1>
          <p>Our team has been notified. Please try again.</p>
          <button onClick={resetError}>Retry</button>
          <details>
            <summary>Error details</summary>
            <pre>{error?.message}</pre>
          </details>
        </div>
      )}
      onError={(error, componentStack) => {
        // Additional context for debugging
        Sentry.setContext('componentStack', { stack: componentStack });
      }}
    >
      {children}
    </Sentry.ErrorBoundary>
  );
}

// Using Sentry in API calls for breadcrumb context
import * as Sentry from '@sentry/react';

async function fetchOrders() {
  Sentry.addBreadcrumb({
    category: 'api',
    message: 'Fetching orders',
    level: 'info',
  });

  try {
    const response = await apiClient.get('/orders');
    return response.data;
  } catch (error) {
    Sentry.captureException(error, {
      tags: { feature: 'orders', action: 'fetch' },
      extra: { endpoint: '/orders' },
    });
    throw error;
  }
}

// vite.config.ts — Upload source maps on build
import { sentryVitePlugin } from '@sentry/vite-plugin';

export default defineConfig({
  build: { sourcemap: true },
  plugins: [
    sentryVitePlugin({
      org: 'my-company',
      project: 'web-app',
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
});
```

**Production tip:** Always upload source maps during CI/CD but **do not** serve them publicly (Sentry fetches them via its own API). Set up alert rules: "Alert #frontend-oncall when a new issue has > 10 events in 5 minutes."

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you implement feature flags and gradual rollouts in a React application?

**Answer:**

**Feature flags** (also called feature toggles) decouple deployment from release. You deploy code to production that is hidden behind a flag, then enable it for specific users or percentages without redeploying. This enables canary releases, A/B testing, kill switches for broken features, and beta programs.

The architecture involves three parts:
1. **Flag management service** — A backend (LaunchDarkly, Unleash, Flagsmith, or a custom service) that stores flag definitions, targeting rules, and rollout percentages.
2. **Client SDK** — A React provider that connects to the flag service, evaluates flags for the current user, and streams updates in real time (SSE or polling).
3. **Application integration** — Components conditionally render based on flag values; code-split to avoid loading hidden feature code.

**Key design decisions:**
- **Default values**: Always provide a sensible default (usually `false`) so the app works if the flag service is down.
- **Flag types**: Boolean flags for on/off, multivariate flags for A/B/C variants, JSON flags for remote configuration.
- **Cleanup**: Establish a process to remove flags after full rollout. Stale flags are tech debt.

```jsx
// Using Unleash (open-source) with React

// src/flags/FlagProvider.tsx
import { FlagProvider as UnleashProvider } from '@unleash/proxy-client-react';
import { appConfig } from '@/config';

const flagConfig = {
  url: appConfig.UNLEASH_URL,
  clientKey: appConfig.UNLEASH_CLIENT_KEY,
  appName: 'my-web-app',
  refreshInterval: 30,                // Poll every 30 seconds
  environment: appConfig.APP_ENV,
};

export function FlagProvider({ children }) {
  return (
    <UnleashProvider config={flagConfig}>
      {children}
    </UnleashProvider>
  );
}

// src/flags/useFeatureFlag.ts — Custom wrapper with defaults and analytics
import { useFlag, useVariant } from '@unleash/proxy-client-react';
import { analytics } from '@/monitoring/analytics';

export function useFeatureFlag(flagName, defaultValue = false) {
  const enabled = useFlag(flagName);

  // Track flag exposure for analytics
  useEffect(() => {
    analytics.track('feature_flag_exposure', {
      flag: flagName,
      enabled,
    });
  }, [flagName, enabled]);

  return enabled ?? defaultValue;
}

export function useFeatureVariant(flagName) {
  const variant = useVariant(flagName);
  return {
    name: variant.name ?? 'control',
    payload: variant.payload?.value ? JSON.parse(variant.payload.value) : null,
    enabled: variant.enabled ?? false,
  };
}

// src/features/checkout/CheckoutPage.tsx — Feature flag in action
import { useFeatureFlag, useFeatureVariant } from '@/flags/useFeatureFlag';
import { lazy, Suspense } from 'react';

const NewCheckoutFlow = lazy(() => import('./NewCheckoutFlow'));
const LegacyCheckoutFlow = lazy(() => import('./LegacyCheckoutFlow'));

export function CheckoutPage() {
  const useNewCheckout = useFeatureFlag('new-checkout-flow');
  const paymentVariant = useFeatureVariant('payment-ui-experiment');

  return (
    <Suspense fallback={<CheckoutSkeleton />}>
      {useNewCheckout ? (
        <NewCheckoutFlow paymentVariant={paymentVariant.name} />
      ) : (
        <LegacyCheckoutFlow />
      )}
    </Suspense>
  );
}

// Gradual rollout strategy (configured in Unleash/LaunchDarkly dashboard):
//
// Day 1: Enable for internal employees (targeting rule: email ends with @company.com)
// Day 3: Enable for 5% of users (gradual rollout by userId hash)
// Day 5: Increase to 25% — monitor error rates and performance
// Day 7: Increase to 50%
// Day 10: Full rollout to 100%
// Day 14: Remove feature flag from code (cleanup PR)
```

**Production tip:** Wrap flag evaluation in a custom hook so you have a single place to add default values, analytics tracking, and override capabilities for QA testing (e.g., `?flag_override=new-checkout-flow` in the URL).

---

### Q7. How do you set up performance monitoring with Web Vitals and Lighthouse CI in a React application?

**Answer:**

**Web Vitals** are Google's metrics for measuring real user experience: **LCP** (Largest Contentful Paint), **INP** (Interaction to Next Paint, replacing FID in 2024), **CLS** (Cumulative Layout Shift), **FCP** (First Contentful Paint), and **TTFB** (Time to First Byte). Monitoring these in production with real user data (RUM — Real User Monitoring) is essential because synthetic tests (Lighthouse in CI) test a single device/network, while real users have diverse conditions.

The strategy has two prongs:
1. **RUM (Real User Monitoring)** — Collect Web Vitals from actual user sessions and send them to your analytics backend. The `web-vitals` library provides this data.
2. **Synthetic monitoring (Lighthouse CI)** — Run Lighthouse on every PR against a performance budget. This catches regressions before they reach production.

```jsx
// 1. Real User Monitoring — src/monitoring/webVitals.ts
import { onLCP, onINP, onCLS, onFCP, onTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  // Send to your analytics endpoint
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,      // 'good', 'needs-improvement', or 'poor'
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
    url: window.location.pathname,
    // Additional context
    connectionType: navigator.connection?.effectiveType,
    deviceMemory: navigator.deviceMemory,
    timestamp: Date.now(),
  });

  // Use sendBeacon for reliability (fires even on page unload)
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/vitals', body);
  } else {
    fetch('/api/vitals', { body, method: 'POST', keepalive: true });
  }
}

export function initWebVitalsReporting() {
  onLCP(sendToAnalytics);
  onINP(sendToAnalytics);
  onCLS(sendToAnalytics);
  onFCP(sendToAnalytics);
  onTTFB(sendToAnalytics);
}

// 2. PerformanceMonitor component — src/monitoring/PerformanceMonitor.tsx
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { initWebVitalsReporting } from './webVitals';

export function PerformanceMonitor() {
  const location = useLocation();

  useEffect(() => {
    initWebVitalsReporting();
  }, []);

  // Track route changes as performance marks
  useEffect(() => {
    performance.mark(`route-change:${location.pathname}`);
  }, [location.pathname]);

  return null; // Render nothing — purely a side-effect component
}

// 3. Lighthouse CI — lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:4173/', 'http://localhost:4173/dashboard'],
      startServerCommand: 'npm run preview',
      startServerReadyPattern: 'Local:',
      numberOfRuns: 3,       // Run 3 times for stability
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'first-contentful-paint': ['warn', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
      },
    },
    upload: {
      target: 'lhci',      // Upload to Lighthouse CI server for historical tracking
      serverBaseUrl: 'https://lhci.mycompany.com',
    },
  },
};

// 4. Performance budget in package.json (checked by size-limit)
// {
//   "size-limit": [
//     { "path": "dist/assets/index-*.js", "limit": "150 KB", "gzip": true },
//     { "path": "dist/assets/vendor-*.js", "limit": "100 KB", "gzip": true },
//     { "path": "dist/assets/index-*.css", "limit": "30 KB", "gzip": true }
//   ]
// }
```

**Production dashboards:** Build a Grafana/Datadog dashboard showing p50, p75, and p95 for each Web Vital, segmented by route, device type, and geography. Set alerts when p75 LCP exceeds 2.5s or p75 INP exceeds 200ms.

---

### Q8. How does Webpack Module Federation enable micro-frontend architecture with React?

**Answer:**

**Micro-frontends** apply the microservices principle to the frontend: split a monolithic React app into independently deployable sub-applications, each owned by a different team. **Module Federation** (a Webpack 5 plugin, also available in Rspack and Vite via plugins) enables this at runtime — a "host" application dynamically loads remote modules from separately deployed "remote" applications at runtime, without needing to rebuild the host.

**Architecture:**
- **Host (shell)**: The container app that provides the layout, routing, and shared dependencies (React, React DOM). It declares what remotes it consumes.
- **Remote (micro-app)**: An independently deployed app that exposes specific modules (components, pages, hooks). Each remote has its own CI/CD pipeline.
- **Shared dependencies**: React, React DOM, and other large libraries are declared as shared singletons to avoid duplicate downloads.

**Key challenges:**
- **Shared state**: Micro-frontends should communicate via events, URL state, or a shared context — not shared global stores.
- **CSS isolation**: Use CSS Modules, CSS-in-JS with scoped class names, or Shadow DOM to prevent style conflicts.
- **Version skew**: Remote A might use React 18.2 while Remote B uses 18.3. Module Federation's `singleton` + `requiredVersion` handles this.
- **Error isolation**: An error in a remote should not crash the host — wrap remotes in error boundaries.

```jsx
// HOST application — webpack.config.js (or rspack.config.js)
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'shell',
      remotes: {
        // Remote URLs are loaded at runtime — can be updated without redeploying shell
        catalog: 'catalog@https://catalog.myapp.com/remoteEntry.js',
        checkout: 'checkout@https://checkout.myapp.com/remoteEntry.js',
        userProfile: 'userProfile@https://profile.myapp.com/remoteEntry.js',
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
        'react-router-dom': { singleton: true, requiredVersion: '^6.0.0' },
      },
    }),
  ],
};

// REMOTE application (catalog) — webpack.config.js
module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'catalog',
      filename: 'remoteEntry.js',
      exposes: {
        './CatalogPage': './src/pages/CatalogPage',
        './ProductCard': './src/components/ProductCard',
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
};

// HOST — Loading a remote micro-frontend with error boundary
// src/app/routes.tsx
import { lazy, Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

// Dynamic import from federated remote
const CatalogPage = lazy(() => import('catalog/CatalogPage'));
const CheckoutPage = lazy(() => import('checkout/CheckoutPage'));

function RemoteWrapper({ children, fallback }) {
  return (
    <ErrorBoundary
      fallback={
        <div className="remote-error">
          <h2>This section is temporarily unavailable</h2>
          <button onClick={() => window.location.reload()}>Reload</button>
        </div>
      }
    >
      <Suspense fallback={fallback || <SectionSkeleton />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}

export const routes = [
  {
    path: '/catalog/*',
    element: (
      <RemoteWrapper>
        <CatalogPage />
      </RemoteWrapper>
    ),
  },
  {
    path: '/checkout/*',
    element: (
      <RemoteWrapper>
        <CheckoutPage />
      </RemoteWrapper>
    ),
  },
];

// Communication between micro-frontends via custom events
// In catalog remote:
function handleAddToCart(product) {
  window.dispatchEvent(
    new CustomEvent('cart:add', { detail: { product } })
  );
}

// In shell (host):
useEffect(() => {
  const handler = (e) => cartStore.addItem(e.detail.product);
  window.addEventListener('cart:add', handler);
  return () => window.removeEventListener('cart:add', handler);
}, []);
```

**When to use micro-frontends:** Only when you have genuinely independent teams (3+ teams working on the same product) that need autonomous deployment cycles. For a single team, micro-frontends add complexity without benefit — use a well-structured monolith or monorepo instead.

---

### Q9. How do you architect a design system and component library for a production React application?

**Answer:**

A **design system** is the single source of truth for UI — it combines design tokens (colors, spacing, typography), reusable components, patterns, and documentation. In a production React codebase, the component library is typically a separate package in a monorepo, consumed by multiple applications.

**Architecture layers:**
1. **Design tokens** — Primitive values (colors, spacing, radii, shadows) expressed as CSS custom properties or a JS/TS theme object. These are the foundation.
2. **Primitive components** — Low-level building blocks: `Button`, `Input`, `Card`, `Modal`, `Tooltip`. These implement the tokens and handle accessibility.
3. **Composite components** — Combinations of primitives for common patterns: `FormField` (label + input + error), `DataTable` (table + sorting + pagination), `CommandPalette`.
4. **Documentation** — Storybook for interactive documentation, visual regression testing, and design-developer handoff.

**Key design decisions:**
- **Headless vs styled**: Headless libraries (Radix UI, React Aria) provide behavior and accessibility without styles, letting you apply your own design tokens. This is the modern approach.
- **Polymorphic `as` prop**: Let consumers change the rendered element (`<Button as="a" href="...">`) for semantic HTML flexibility.
- **Variant-based API**: Use a variant system (like `cva` — Class Variance Authority) for type-safe, composable styling.
- **Compound components**: For complex components like `Tabs`, use the compound component pattern for maximum flexibility.

```jsx
// Design system package structure:
// packages/ui/
// ├── src/
// │   ├── tokens/
// │   │   ├── colors.ts        # { primary: { 50: '#eff6ff', ... } }
// │   │   ├── spacing.ts       # { 1: '0.25rem', 2: '0.5rem', ... }
// │   │   └── index.ts
// │   ├── primitives/
// │   │   ├── Button/
// │   │   │   ├── Button.tsx
// │   │   │   ├── Button.test.tsx
// │   │   │   ├── Button.stories.tsx
// │   │   │   └── index.ts
// │   │   ├── Input/
// │   │   └── ...
// │   ├── composites/
// │   │   ├── DataTable/
// │   │   ├── FormField/
// │   │   └── ...
// │   └── index.ts              # Public API barrel

// Button with variant system using CVA + Tailwind
// packages/ui/src/primitives/Button/Button.tsx
import { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { Slot } from '@radix-ui/react-slot';
import { cn } from '../../utils/cn';

const buttonVariants = cva(
  // Base styles
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500',
        secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-500',
        destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
        ghost: 'hover:bg-gray-100 hover:text-gray-900',
        link: 'text-blue-600 underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;               // Polymorphic via Radix Slot
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, isLoading, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Spinner className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </Comp>
    );
  }
);

Button.displayName = 'Button';

// Compound component pattern — Tabs
// packages/ui/src/composites/Tabs/Tabs.tsx
import * as TabsPrimitive from '@radix-ui/react-tabs';

export const Tabs = TabsPrimitive.Root;
export const TabsList = forwardRef(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn('inline-flex h-10 items-center gap-1 rounded-md bg-gray-100 p-1', className)}
    {...props}
  />
));
export const TabsTrigger = forwardRef(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      'inline-flex items-center justify-center rounded-sm px-3 py-1.5 text-sm',
      'data-[state=active]:bg-white data-[state=active]:shadow-sm',
      className
    )}
    {...props}
  />
));
export const TabsContent = TabsPrimitive.Content;

// Usage in consuming app:
import { Button, Tabs, TabsList, TabsTrigger, TabsContent } from '@company/ui';

function SettingsPage() {
  return (
    <Tabs defaultValue="profile">
      <TabsList>
        <TabsTrigger value="profile">Profile</TabsTrigger>
        <TabsTrigger value="security">Security</TabsTrigger>
      </TabsList>
      <TabsContent value="profile"><ProfileForm /></TabsContent>
      <TabsContent value="security"><SecuritySettings /></TabsContent>
    </Tabs>
  );
}
```

**Production tip:** Use **Chromatic** (from the Storybook team) for visual regression testing — it captures screenshots of every component story and diffs them on every PR to catch unintended visual changes.

---

### Q10. How do you design a robust API layer in a React application with interceptors and a request/response pipeline?

**Answer:**

A well-designed API layer centralizes all HTTP communication behind an abstraction that handles authentication headers, request/response transformation, error normalization, retry logic, request cancellation, and logging. Instead of scattering `fetch()` calls across components, you create a configured client instance that every feature's API module uses.

**Architecture:**
- **Base client** — A configured `axios` instance (or a `fetch` wrapper) with base URL, default headers, timeout, and interceptors.
- **Request interceptor** — Attaches the auth token to every request, adds correlation IDs for tracing, and logs outgoing requests.
- **Response interceptor** — Normalizes error shapes, handles 401 (trigger token refresh), retries on network failures, and logs responses.
- **Feature API modules** — Thin wrappers that call the base client with specific endpoints and return typed data.

```jsx
// src/lib/apiClient.ts — Production-grade API client
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { appConfig } from '@/config';
import { tokenStorage } from '@/features/auth/tokenStorage';
import { authEvents } from '@/features/auth/authEvents';
import * as Sentry from '@sentry/react';
import { v4 as uuid } from 'uuid';

// --- Create base instance ---
export const apiClient = axios.create({
  baseURL: appConfig.API_URL,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
    'X-Client-Version': appConfig.APP_VERSION,
  },
});

// --- Request Interceptor: Auth + Tracing ---
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Attach auth token
  const token = tokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Attach correlation ID for distributed tracing
  config.headers['X-Request-ID'] = uuid();

  // Sentry breadcrumb
  Sentry.addBreadcrumb({
    category: 'http',
    message: `${config.method?.toUpperCase()} ${config.url}`,
    level: 'info',
  });

  return config;
});

// --- Response Interceptor: Error handling + Token refresh ---
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

function processQueue(error: Error | null, token: string | null) {
  failedQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve(token);
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response, // Pass through successful responses
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 — Refresh token and retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${appConfig.API_URL}/auth/refresh`, {
          refreshToken: tokenStorage.getRefreshToken(),
        });

        tokenStorage.setTokens(data.accessToken, data.refreshToken);
        processQueue(null, data.accessToken);

        originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        tokenStorage.clearTokens();
        authEvents.emit('session-expired');     // Redirect to login
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Normalize error shape
    const normalizedError = {
      status: error.response?.status ?? 0,
      message: error.response?.data?.message ?? error.message ?? 'Unknown error',
      code: error.response?.data?.code ?? 'UNKNOWN',
      requestId: error.config?.headers?.['X-Request-ID'],
    };

    // Report to Sentry for 5xx errors
    if (error.response?.status && error.response.status >= 500) {
      Sentry.captureException(error, {
        tags: {
          api_status: error.response.status,
          api_url: error.config?.url,
        },
      });
    }

    return Promise.reject(normalizedError);
  }
);

// --- Feature API module example ---
// src/features/orders/api/ordersApi.ts
import { apiClient } from '@/lib/apiClient';
import type { Order, CreateOrderPayload, PaginatedResponse } from './orders.types';

export const ordersApi = {
  list: (params: { page: number; limit: number; status?: string }) =>
    apiClient.get<PaginatedResponse<Order>>('/orders', { params }).then(r => r.data),

  getById: (id: string) =>
    apiClient.get<Order>(`/orders/${id}`).then(r => r.data),

  create: (payload: CreateOrderPayload) =>
    apiClient.post<Order>('/orders', payload).then(r => r.data),

  cancel: (id: string, reason: string) =>
    apiClient.patch<Order>(`/orders/${id}/cancel`, { reason }).then(r => r.data),
};

// --- Integration with TanStack Query ---
// src/features/orders/hooks/useOrders.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersApi } from '../api/ordersApi';

export const orderKeys = {
  all: ['orders'] as const,
  lists: () => [...orderKeys.all, 'list'] as const,
  list: (params) => [...orderKeys.lists(), params] as const,
  detail: (id: string) => [...orderKeys.all, 'detail', id] as const,
};

export function useOrders(params) {
  return useQuery({
    queryKey: orderKeys.list(params),
    queryFn: () => ordersApi.list(params),
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }) => ordersApi.cancel(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: orderKeys.lists() });
    },
  });
}
```

**Production tip:** Create an `AbortController` wrapper for search/autocomplete requests so that when the user types a new character, the previous inflight request is cancelled. TanStack Query handles this automatically when query keys change.

---

### Q11. How do you implement internationalization (i18n) at scale in a React application?

**Answer:**

Internationalization at scale is not just translating strings — it encompasses date/time formatting, number/currency formatting, pluralization rules, right-to-left (RTL) layout, dynamic locale loading, translation management workflows, and maintaining translation quality across dozens of languages.

**Architecture decisions:**
- **Library choice**: `react-intl` (FormatJS) is the most comprehensive for complex formatting rules. `next-intl` is purpose-built for Next.js. `i18next` + `react-i18next` is the most popular and has the richest plugin ecosystem.
- **Message format**: ICU Message Syntax is the standard — it handles plurals, selects (gender), and nested structures.
- **Translation loading**: Load only the current locale's messages, not all locales. Use dynamic `import()` so translations are code-split per locale.
- **Translation management**: Use a TMS (Translation Management System) like Crowdin, Lokalise, or Phrase that syncs with your repo. Developers push English strings; translators work in the TMS; CI pulls translated strings.

```jsx
// i18n architecture with react-intl (FormatJS)

// src/i18n/messages/en.json
// {
//   "common.welcome": "Welcome, {name}!",
//   "orders.count": "{count, plural, =0 {No orders} one {# order} other {# orders}}",
//   "orders.status": "{status, select, pending {Pending} shipped {Shipped} delivered {Delivered} other {Unknown}}",
//   "cart.total": "Total: {amount, number, ::currency/USD}",
//   "date.relative": "Last updated {date, date, medium} at {date, time, short}"
// }

// src/i18n/index.ts — Locale detection and async message loading
const SUPPORTED_LOCALES = ['en', 'es', 'fr', 'de', 'ja', 'ar'] as const;
type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

export function detectLocale(): SupportedLocale {
  const stored = localStorage.getItem('locale');
  if (stored && SUPPORTED_LOCALES.includes(stored as SupportedLocale)) {
    return stored as SupportedLocale;
  }

  // Use browser language, falling back to English
  const browserLang = navigator.language.split('-')[0];
  return SUPPORTED_LOCALES.includes(browserLang as SupportedLocale)
    ? (browserLang as SupportedLocale)
    : 'en';
}

export async function loadMessages(locale: SupportedLocale) {
  // Dynamic import — only loads the needed locale (code splitting)
  switch (locale) {
    case 'en': return (await import('./messages/en.json')).default;
    case 'es': return (await import('./messages/es.json')).default;
    case 'fr': return (await import('./messages/fr.json')).default;
    case 'de': return (await import('./messages/de.json')).default;
    case 'ja': return (await import('./messages/ja.json')).default;
    case 'ar': return (await import('./messages/ar.json')).default;
    default:   return (await import('./messages/en.json')).default;
  }
}

// src/i18n/IntlProvider.tsx — Provider with locale switching
import { IntlProvider as ReactIntlProvider } from 'react-intl';
import { useState, useCallback, createContext, useContext } from 'react';

const LocaleContext = createContext({
  locale: 'en',
  switchLocale: (l: string) => {},
  isRTL: false,
});

export function IntlProvider({ children }) {
  const [locale, setLocale] = useState(detectLocale);
  const [messages, setMessages] = useState(null);

  useEffect(() => {
    loadMessages(locale).then(setMessages);
    // Set document direction for RTL languages
    document.documentElement.dir = ['ar', 'he', 'fa'].includes(locale) ? 'rtl' : 'ltr';
    document.documentElement.lang = locale;
  }, [locale]);

  const switchLocale = useCallback(async (newLocale) => {
    const msgs = await loadMessages(newLocale);
    setMessages(msgs);
    setLocale(newLocale);
    localStorage.setItem('locale', newLocale);
  }, []);

  if (!messages) return <LoadingSpinner />;

  return (
    <LocaleContext.Provider value={{ locale, switchLocale, isRTL: ['ar', 'he'].includes(locale) }}>
      <ReactIntlProvider locale={locale} messages={messages} defaultLocale="en">
        {children}
      </ReactIntlProvider>
    </LocaleContext.Provider>
  );
}

export const useLocale = () => useContext(LocaleContext);

// Usage in components
import { FormattedMessage, FormattedNumber, useIntl } from 'react-intl';
import { useLocale } from '@/i18n/IntlProvider';

function OrderSummary({ orders, total }) {
  const intl = useIntl();
  const { switchLocale, locale } = useLocale();

  return (
    <div>
      <h2>
        <FormattedMessage id="common.welcome" values={{ name: 'Vignesh' }} />
      </h2>
      <p>
        <FormattedMessage id="orders.count" values={{ count: orders.length }} />
      </p>
      <p>
        <FormattedNumber value={total} style="currency" currency="USD" />
      </p>
      {/* Programmatic formatting (for aria-labels, etc.) */}
      <time
        dateTime={new Date().toISOString()}
        aria-label={intl.formatDate(new Date(), { dateStyle: 'full' })}
      >
        {intl.formatRelativeTime(-2, 'day')}
      </time>

      {/* Locale switcher */}
      <select value={locale} onChange={(e) => switchLocale(e.target.value)}>
        <option value="en">English</option>
        <option value="es">Español</option>
        <option value="ar">العربية</option>
      </select>
    </div>
  );
}
```

**Production tip:** Extract message IDs automatically from code using FormatJS CLI (`formatjs extract`). Set up a CI step that pushes new/changed strings to your TMS and fails the build if any message IDs are missing translations for your required locales.

---

### Q12. How do you decide what type of state management to use for different data in a React application?

**Answer:**

The biggest state management mistake in production React apps is putting everything in one global store. Different types of state have different lifetimes, update patterns, and ownership. A **state architecture decision tree** helps teams make consistent choices:

| State Type | Examples | Tool | Why |
|---|---|---|---|
| **Local UI state** | Form input, modal open/close, accordion expanded | `useState`, `useReducer` | Scoped to one component; dies when component unmounts |
| **Shared UI state** | Theme, sidebar collapsed, toast notifications | Zustand, Jotai, or Context | Needed by multiple unrelated components |
| **Server state** | API data (users, orders, products) | TanStack Query, SWR | Has a source of truth on the server; needs caching, revalidation, optimistic updates |
| **URL state** | Current page, filters, sort order, search query | React Router, `useSearchParams`, `nuqs` | Must be shareable via URL, survives page refresh |
| **Form state** | Multi-step form values, validation, dirty state | React Hook Form, Formik | Complex validation, field-level state, performance-sensitive |
| **Global app state** | Authenticated user, permissions, feature flags | Zustand + Context | True global singletons with rare updates |
| **Persistent state** | User preferences, draft content, cart | Zustand `persist` middleware, localStorage | Survives session; synced to storage |

```jsx
// Decision tree in practice — an e-commerce product page

import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/features/auth';
import { useCartStore } from '@/features/cart';

function ProductPage({ productId }) {
  // SERVER STATE — Product data from API, with caching and revalidation
  const { data: product, isLoading } = useQuery({
    queryKey: ['products', productId],
    queryFn: () => productsApi.getById(productId),
    staleTime: 5 * 60 * 1000,
  });

  // URL STATE — Selected variant, visible in URL for sharing/SEO
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedColor = searchParams.get('color') ?? product?.defaultColor;
  const setColor = (color) => setSearchParams({ color }, { replace: true });

  // LOCAL UI STATE — Image gallery index, only matters to this component
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  // LOCAL UI STATE — "Added to cart" confirmation toast
  const [showConfirmation, setShowConfirmation] = useState(false);

  // FORM STATE — Review form with validation
  const reviewForm = useForm({
    defaultValues: { rating: 5, comment: '' },
  });

  // GLOBAL STATE — Auth (needed to check if user can review)
  const { user, isAuthenticated } = useAuthStore();

  // GLOBAL PERSISTENT STATE — Cart (persisted to localStorage, shared across pages)
  const addToCart = useCartStore((s) => s.addItem);

  // SERVER STATE — Mutation for submitting review
  const queryClient = useQueryClient();
  const submitReview = useMutation({
    mutationFn: (review) => reviewsApi.create(productId, review),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products', productId, 'reviews'] });
      reviewForm.reset();
    },
  });

  function handleAddToCart() {
    addToCart({ productId, color: selectedColor, quantity: 1 });
    setShowConfirmation(true);
    setTimeout(() => setShowConfirmation(false), 3000);
  }

  // Each piece of state is managed by the right tool for its nature
  return (
    <div>
      <ImageGallery
        images={product?.images}
        activeIndex={activeImageIndex}
        onSelect={setActiveImageIndex}  // Local state
      />
      <ColorPicker
        colors={product?.colors}
        selected={selectedColor}         // URL state
        onSelect={setColor}
      />
      <Button onClick={handleAddToCart}>Add to Cart</Button>
      {showConfirmation && <Toast>Added to cart!</Toast>}

      {isAuthenticated && (
        <ReviewForm
          form={reviewForm}              // Form state
          onSubmit={reviewForm.handleSubmit((data) => submitReview.mutate(data))}
          isSubmitting={submitReview.isPending}
        />
      )}
    </div>
  );
}
```

**The golden rule:** Start with the simplest state solution (local `useState`) and only escalate when you have a concrete reason (multiple consumers need it, it must survive navigation, it comes from a server). Premature globalization of state is the #1 architectural mistake in React apps.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you architect authentication in a production React SPA, including OAuth flows, session management, and refresh token rotation?

**Answer:**

Authentication architecture in a production React SPA must handle: (1) initial login (OAuth 2.0 / OpenID Connect), (2) session persistence across tabs and page reloads, (3) automatic token refresh before expiry, (4) concurrent request handling during refresh, (5) secure token storage, and (6) logout and session invalidation.

**Security architecture decisions:**
- **Token storage**: Store the **access token** in memory only (a JavaScript variable — not localStorage, not sessionStorage). Store the **refresh token** in an `httpOnly`, `Secure`, `SameSite=Strict` cookie set by the backend. This prevents XSS from stealing tokens.
- **Token refresh**: The access token is short-lived (5-15 minutes). When it expires, the client sends the refresh token cookie to a dedicated `/auth/refresh` endpoint. The server issues new access + refresh tokens (refresh token rotation).
- **Silent refresh**: On page load, make a `/auth/refresh` call to get a new access token from the refresh token cookie. This restores the session without storing tokens client-side.
- **Race condition handling**: When multiple API requests fail with 401 simultaneously, only one should trigger a refresh. Others should queue and retry after the refresh completes.

```jsx
// src/features/auth/AuthProvider.tsx — Complete auth architecture
import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { apiClient } from '@/lib/apiClient';
import * as Sentry from '@sentry/react';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (provider: 'google' | 'github') => void;
  logout: () => Promise<void>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,        // True until initial session check completes
  });

  // Store access token in memory — NEVER in localStorage
  const accessTokenRef = useRef<string | null>(null);

  // Attempt silent session restoration on mount
  useEffect(() => {
    silentRefresh();
  }, []);

  // Silent refresh — uses httpOnly refresh token cookie
  const silentRefresh = useCallback(async () => {
    try {
      const { data } = await apiClient.post('/auth/refresh', null, {
        withCredentials: true,    // Send refresh token cookie
      });

      accessTokenRef.current = data.accessToken;
      setState({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
      });

      // Set Sentry user context
      Sentry.setUser({ id: data.user.id, email: data.user.email });

      // Schedule next refresh before token expires
      const expiresInMs = (data.expiresIn - 60) * 1000; // Refresh 60s before expiry
      setTimeout(silentRefresh, expiresInMs);
    } catch {
      accessTokenRef.current = null;
      setState({ user: null, isAuthenticated: false, isLoading: false });
      Sentry.setUser(null);
    }
  }, []);

  // OAuth login — redirect to provider
  const login = useCallback((provider: 'google' | 'github') => {
    const returnUrl = encodeURIComponent(window.location.pathname);
    window.location.href =
      `${appConfig.API_URL}/auth/${provider}?redirect=${returnUrl}`;
  }, []);

  // OAuth callback handler (called from callback route)
  // The backend sets the httpOnly refresh token cookie and redirects
  // back to the app. AuthProvider's useEffect calls silentRefresh.

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout', null, { withCredentials: true });
    } finally {
      accessTokenRef.current = null;
      setState({ user: null, isAuthenticated: false, isLoading: false });
      Sentry.setUser(null);
      window.location.href = '/login';
    }
  }, []);

  const getAccessToken = useCallback(() => accessTokenRef.current, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, getAccessToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

// src/features/auth/ProtectedRoute.tsx — Route guard
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthProvider';

export function ProtectedRoute({ children, requiredRole }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) return <FullPageSpinner />;

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && !user.roles.includes(requiredRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
}

// Route configuration
import { ProtectedRoute } from '@/features/auth';

const routes = [
  { path: '/login', element: <LoginPage /> },
  { path: '/auth/callback', element: <OAuthCallback /> },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/*',
    element: (
      <ProtectedRoute requiredRole="admin">
        <AdminLayout />
      </ProtectedRoute>
    ),
  },
];

// Cross-tab session sync — logout all tabs when one logs out
useEffect(() => {
  const handler = (e) => {
    if (e.key === 'auth-logout') {
      accessTokenRef.current = null;
      setState({ user: null, isAuthenticated: false, isLoading: false });
    }
  };
  window.addEventListener('storage', handler);
  return () => window.removeEventListener('storage', handler);
}, []);

// In logout function, trigger cross-tab sync:
// localStorage.setItem('auth-logout', Date.now().toString());
```

**Security checklist:**
- Access tokens in memory only (not localStorage/sessionStorage).
- Refresh tokens in `httpOnly`, `Secure`, `SameSite=Strict` cookies.
- Refresh token rotation on every use.
- CSRF protection via double-submit cookie or SameSite attribute.
- Rate limiting on `/auth/refresh` endpoint.
- Logout invalidates the refresh token server-side.

---

### Q14. How do you design an analytics and tracking architecture for a production React application?

**Answer:**

Analytics in production React apps must handle multiple providers (Google Analytics, Mixpanel, Amplitude, internal data warehouse), respect user consent (GDPR, CCPA), separate tracking logic from business logic, and provide type-safe event definitions. The key pattern is an **analytics abstraction layer** that decouples the app from specific providers.

**Architecture:**
1. **Event schema** — A TypeScript definition of all trackable events and their properties. This is the contract between product managers and engineers.
2. **Analytics service** — A singleton that routes events to configured providers. It handles consent, batching, and user identification.
3. **React integration** — Hooks and HOCs that automatically track page views, component impressions, and user interactions.
4. **Consent management** — A consent layer that gates tracking based on user preferences, with a cookie banner for opt-in/opt-out.

```jsx
// 1. Event schema — src/monitoring/analytics/events.ts
// Typed event definitions — the single source of truth
export interface AnalyticsEventMap {
  // Page views
  'page.viewed': { path: string; title: string; referrer: string };

  // Auth events
  'auth.login': { method: 'google' | 'github' | 'email' };
  'auth.logout': {};
  'auth.signup_started': { source: string };
  'auth.signup_completed': { method: string; timeToCompleteMs: number };

  // Product events
  'product.viewed': { productId: string; category: string; price: number };
  'product.added_to_cart': { productId: string; quantity: number; source: string };
  'product.search': { query: string; resultsCount: number };

  // Checkout events
  'checkout.started': { cartValue: number; itemCount: number };
  'checkout.step_completed': { step: number; stepName: string };
  'checkout.completed': { orderId: string; total: number; paymentMethod: string };
  'checkout.abandoned': { step: number; cartValue: number };

  // Feature engagement
  'feature.used': { name: string; variant?: string };

  // Error events
  'error.api': { endpoint: string; status: number; message: string };
  'error.ui': { component: string; error: string };
}

// 2. Analytics service — src/monitoring/analytics/service.ts
type EventName = keyof AnalyticsEventMap;
type EventProperties<T extends EventName> = AnalyticsEventMap[T];

interface AnalyticsProvider {
  name: string;
  identify: (userId: string, traits: Record<string, any>) => void;
  track: (event: string, properties: Record<string, any>) => void;
  page: (name: string, properties: Record<string, any>) => void;
  reset: () => void;
}

class AnalyticsService {
  private providers: AnalyticsProvider[] = [];
  private consentGiven = false;
  private userId: string | null = null;
  private superProperties: Record<string, any> = {};

  registerProvider(provider: AnalyticsProvider) {
    this.providers.push(provider);
  }

  setConsent(given: boolean) {
    this.consentGiven = given;
    if (!given) this.reset();
  }

  identify(userId: string, traits: Record<string, any> = {}) {
    if (!this.consentGiven) return;
    this.userId = userId;
    this.providers.forEach(p => p.identify(userId, traits));
  }

  setSuperProperties(props: Record<string, any>) {
    this.superProperties = { ...this.superProperties, ...props };
  }

  track<T extends EventName>(event: T, properties: EventProperties<T>) {
    if (!this.consentGiven) return;

    const enrichedProperties = {
      ...this.superProperties,
      ...properties,
      timestamp: new Date().toISOString(),
      sessionId: this.getSessionId(),
      url: window.location.href,
    };

    this.providers.forEach(p => p.track(event, enrichedProperties));

    // Also log to console in development
    if (import.meta.env.DEV) {
      console.log(`[Analytics] ${event}`, enrichedProperties);
    }
  }

  page(name: string, properties: Record<string, any> = {}) {
    if (!this.consentGiven) return;
    this.providers.forEach(p => p.page(name, properties));
  }

  reset() {
    this.userId = null;
    this.providers.forEach(p => p.reset());
  }

  private getSessionId(): string {
    let id = sessionStorage.getItem('analytics_session_id');
    if (!id) {
      id = crypto.randomUUID();
      sessionStorage.setItem('analytics_session_id', id);
    }
    return id;
  }
}

export const analytics = new AnalyticsService();

// 3. React hooks — src/monitoring/analytics/hooks.ts
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { analytics } from './service';

// Auto-track page views on route change
export function usePageTracking() {
  const location = useLocation();
  const prevPath = useRef(location.pathname);

  useEffect(() => {
    analytics.page(document.title, {
      path: location.pathname,
      referrer: prevPath.current,
      search: location.search,
    });
    prevPath.current = location.pathname;
  }, [location.pathname]);
}

// Track component visibility (impression tracking)
export function useTrackImpression<T extends keyof AnalyticsEventMap>(
  event: T,
  properties: AnalyticsEventMap[T],
  elementRef: React.RefObject<HTMLElement>
) {
  const tracked = useRef(false);

  useEffect(() => {
    if (!elementRef.current || tracked.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !tracked.current) {
          analytics.track(event, properties);
          tracked.current = true;
          observer.disconnect();
        }
      },
      { threshold: 0.5 }
    );

    observer.observe(elementRef.current);
    return () => observer.disconnect();
  }, [event, properties]);
}

// Usage in components:
function ProductCard({ product }) {
  const cardRef = useRef(null);

  useTrackImpression('product.viewed', {
    productId: product.id,
    category: product.category,
    price: product.price,
  }, cardRef);

  return (
    <div ref={cardRef}>
      <h3>{product.name}</h3>
      <button
        onClick={() => {
          addToCart(product);
          analytics.track('product.added_to_cart', {
            productId: product.id,
            quantity: 1,
            source: 'product_card',
          });
        }}
      >
        Add to Cart
      </button>
    </div>
  );
}
```

**Production tip:** Define your event schema in a shared package so that the data team, product team, and engineering team all reference the same contract. Use a "tracking plan" document that maps business questions to events (e.g., "What is the cart abandonment rate?" → requires `checkout.started` and `checkout.completed` events).

---

### Q15. What are the different deployment strategies for production React applications, and when do you use each?

**Answer:**

Deployment strategy determines how your React application reaches users — it affects performance (TTFB, caching), reliability (zero-downtime deploys), cost, and developer experience. The main strategies are:

1. **Static CDN hosting** — Build to static files, upload to a CDN (Cloudflare Pages, Vercel, Netlify, S3+CloudFront). Best for SPAs. Fastest TTFB, cheapest, infinitely scalable, but no server-side rendering.

2. **Edge deployment** — Run your app's server logic on edge nodes (Cloudflare Workers, Vercel Edge Functions, Deno Deploy). Combines CDN-like latency with server capabilities (SSR, API routes, auth). Best for Next.js/Remix apps.

3. **Serverless deployment** — Deploy server functions (AWS Lambda, Google Cloud Functions) that render pages on demand. Scales to zero (cost-efficient for low traffic), but has cold start latency.

4. **Container deployment** — Docker containers on Kubernetes, ECS, or Cloud Run. Full control over the runtime, sidecar containers for monitoring, horizontal scaling. Best for enterprise apps with complex infrastructure requirements.

5. **Blue-green deployment** — Run two identical production environments. Deploy to the inactive one, run smoke tests, then switch traffic. Enables instant rollback by switching back.

6. **Canary deployment** — Route a small percentage of traffic (1-5%) to the new version. Monitor error rates and performance. Gradually increase traffic if metrics are healthy. Catch regressions before they affect all users.

```jsx
// Deployment architecture comparison:
//
// Strategy          | TTFB      | SSR  | Cost Model     | Rollback    | Use Case
// ------------------|-----------|------|----------------|-------------|------------------
// Static CDN        | ~50ms     | No   | Bandwidth      | Instant     | SPAs, marketing sites
// Edge              | ~50-100ms | Yes  | Requests       | Instant     | Dynamic SSR apps
// Serverless        | ~200-500ms| Yes  | Invocations    | Redeploy    | Variable traffic
// Container         | ~100-300ms| Yes  | Compute time   | Roll back   | Enterprise apps
// Blue-Green        | Same      | Any  | 2x infra       | Switch DNS  | Zero-downtime critical
// Canary            | Same      | Any  | 1.01-1.1x infra| Route back  | Gradual validation

// 1. Static CDN — Cloudflare Pages with cache headers
// wrangler.toml (or via dashboard)
// [site]
// bucket = "./dist"
//
// [[headers]]
//   for = "/assets/*"
//   [headers.values]
//     Cache-Control = "public, max-age=31536000, immutable"  # Hashed filenames
//
// [[headers]]
//   for = "/*"
//   [headers.values]
//     Cache-Control = "public, max-age=0, must-revalidate"   # HTML always fresh

// 2. Canary deployment with Cloudflare Workers
// This worker routes 5% of traffic to the canary version

// canary-router.ts (Cloudflare Worker)
export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Sticky assignment via cookie (user always sees same version)
    const cookie = request.headers.get('Cookie') || '';
    let version = cookie.match(/deploy-version=(stable|canary)/)?.[1];

    if (!version) {
      // Assign 5% to canary based on hash of user identifier
      const ip = request.headers.get('CF-Connecting-IP') || '';
      const hash = await hashString(ip);
      version = (hash % 100) < 5 ? 'canary' : 'stable';
    }

    const origins = {
      stable: 'https://my-app-stable.pages.dev',
      canary: 'https://my-app-canary.pages.dev',
    };

    const response = await fetch(origins[version] + url.pathname + url.search, {
      headers: request.headers,
    });

    const newResponse = new Response(response.body, response);
    newResponse.headers.set('Set-Cookie', `deploy-version=${version}; Path=/; Max-Age=3600`);
    newResponse.headers.set('X-Deploy-Version', version);
    return newResponse;
  },
};

// 3. Docker deployment with multi-stage build
// Dockerfile
// FROM node:20-alpine AS builder
// WORKDIR /app
// COPY package*.json ./
// RUN npm ci
// COPY . .
// RUN npm run build
//
// FROM nginx:alpine AS production
// COPY --from=builder /app/dist /usr/share/nginx/html
// COPY nginx.conf /etc/nginx/conf.d/default.conf
// EXPOSE 80
// HEALTHCHECK --interval=30s CMD wget -q --spider http://localhost/health || exit 1

// 4. GitHub Actions deploy with canary validation
// .github/workflows/deploy.yml (excerpt)
// deploy-canary:
//   steps:
//     - run: wrangler pages deploy dist/ --branch canary
//     - name: Run smoke tests against canary
//       run: npx playwright test --config=playwright.smoke.config.ts
//       env:
//         BASE_URL: https://canary.my-app.pages.dev
//     - name: Monitor error rate for 10 minutes
//       run: |
//         node scripts/check-error-rate.js --version=canary --threshold=0.5 --duration=600
//
// promote-to-production:
//   needs: deploy-canary
//   steps:
//     - run: wrangler pages deploy dist/ --branch main
```

**Production tip:** Always deploy with hashed asset filenames (`main.a3b4c5.js`) and set `Cache-Control: immutable` on assets. For HTML files, use `Cache-Control: no-cache` (or short max-age with `stale-while-revalidate`) so users always get the latest entry point that references the correct asset hashes.

---

### Q16. How do you integrate a headless CMS with a React application for database-driven UI?

**Answer:**

A **headless CMS** (Contentful, Sanity, Strapi, Payload CMS) provides content management capabilities (WYSIWYG editing, content modeling, publishing workflows) without a built-in frontend. It exposes content via APIs (REST or GraphQL), and your React app fetches and renders it. This enables non-technical teams to update content (marketing copy, FAQs, landing pages, product descriptions) without code deployments.

**Architecture patterns:**
- **Build-time fetching (SSG)**: Fetch content at build time (Next.js `getStaticProps`, Astro). Fastest for users, but requires rebuilds on content changes. Use webhook-triggered rebuilds.
- **Runtime fetching (SSR/CSR)**: Fetch content on each request or on the client. Always fresh, but adds latency. Use stale-while-revalidate caching.
- **Incremental Static Regeneration (ISR)**: Build pages statically but revalidate in the background after a configurable interval. Best of both worlds (Next.js ISR).
- **Preview mode**: Let content editors preview draft content before publishing, via a special preview URL with draft API tokens.

```jsx
// Architecture with Sanity CMS + React (Next.js)

// 1. Content schema definition (in Sanity Studio)
// schemas/blogPost.ts
export default {
  name: 'blogPost',
  title: 'Blog Post',
  type: 'document',
  fields: [
    { name: 'title', type: 'string', validation: (Rule) => Rule.required() },
    { name: 'slug', type: 'slug', options: { source: 'title' } },
    { name: 'excerpt', type: 'text', rows: 3 },
    {
      name: 'body',
      type: 'array',
      of: [
        { type: 'block' },                       // Rich text
        { type: 'image', options: { hotspot: true } },
        { type: 'code' },                        // Code blocks
        {
          name: 'callout',                        // Custom block
          type: 'object',
          fields: [
            { name: 'type', type: 'string', options: { list: ['info', 'warning', 'tip'] } },
            { name: 'text', type: 'text' },
          ],
        },
      ],
    },
    { name: 'author', type: 'reference', to: [{ type: 'author' }] },
    { name: 'publishedAt', type: 'datetime' },
    { name: 'seo', type: 'seo' },                // SEO fields
  ],
};

// 2. Sanity client — src/lib/sanity.ts
import { createClient } from '@sanity/client';
import imageUrlBuilder from '@sanity/image-url';

export const sanityClient = createClient({
  projectId: process.env.NEXT_PUBLIC_SANITY_PROJECT_ID,
  dataset: process.env.NEXT_PUBLIC_SANITY_DATASET,
  useCdn: process.env.NODE_ENV === 'production',  // CDN for production reads
  apiVersion: '2024-01-01',
});

// Preview client (fetches drafts)
export const previewClient = createClient({
  ...sanityClient.config(),
  useCdn: false,
  token: process.env.SANITY_PREVIEW_TOKEN,  // Server-only!
});

const builder = imageUrlBuilder(sanityClient);
export const urlFor = (source) => builder.image(source);

// 3. GROQ queries — src/lib/queries.ts
export const blogPostsQuery = `
  *[_type == "blogPost" && defined(slug.current)] | order(publishedAt desc) {
    _id,
    title,
    "slug": slug.current,
    excerpt,
    publishedAt,
    "author": author->{name, "avatar": avatar.asset->url},
    "estimatedReadTime": round(length(pt::text(body)) / 5 / 180),
    seo
  }
`;

export const blogPostBySlugQuery = `
  *[_type == "blogPost" && slug.current == $slug][0] {
    ...,
    "author": author->{name, bio, "avatar": avatar.asset->url},
    body[] {
      ...,
      _type == "image" => {
        ...,
        "url": asset->url,
        "dimensions": asset->metadata.dimensions
      }
    }
  }
`;

// 4. Page component with ISR — app/blog/[slug]/page.tsx (Next.js App Router)
import { sanityClient, previewClient, urlFor } from '@/lib/sanity';
import { blogPostBySlugQuery } from '@/lib/queries';
import { PortableText } from '@portabletext/react';
import { notFound } from 'next/navigation';

// Custom components for Sanity's Portable Text (rich text)
const portableTextComponents = {
  types: {
    image: ({ value }) => (
      <figure>
        <img
          src={urlFor(value).width(800).format('webp').url()}
          alt={value.alt || ''}
          loading="lazy"
          width={value.dimensions?.width}
          height={value.dimensions?.height}
        />
        {value.caption && <figcaption>{value.caption}</figcaption>}
      </figure>
    ),
    callout: ({ value }) => (
      <aside className={`callout callout-${value.type}`} role="note">
        {value.text}
      </aside>
    ),
    code: ({ value }) => (
      <pre><code className={`language-${value.language}`}>{value.code}</code></pre>
    ),
  },
};

export const revalidate = 3600; // ISR: revalidate every hour

export default async function BlogPostPage({ params }) {
  const post = await sanityClient.fetch(blogPostBySlugQuery, { slug: params.slug });
  if (!post) notFound();

  return (
    <article>
      <h1>{post.title}</h1>
      <div className="meta">
        <img src={post.author.avatar} alt="" />
        <span>{post.author.name}</span>
        <time dateTime={post.publishedAt}>
          {new Date(post.publishedAt).toLocaleDateString()}
        </time>
      </div>
      <div className="prose">
        <PortableText value={post.body} components={portableTextComponents} />
      </div>
    </article>
  );
}
```

**Production tip:** Set up a webhook from the CMS to your deployment platform so that publishing content triggers an on-demand revalidation (`res.revalidate('/blog/' + slug)`) instead of waiting for the ISR interval. This gives you the speed of static pages with the freshness of dynamic rendering.

---

### Q17. How do you build an offline-first React application using service workers and IndexedDB?

**Answer:**

An **offline-first** architecture assumes the network is unreliable and designs the app to work without it. The app loads from a local cache, reads data from a local database (IndexedDB), queues mutations when offline, and syncs them when connectivity returns. This is critical for field workers, mobile users in areas with poor connectivity, and any app where data loss is unacceptable.

**Architecture components:**
1. **Service Worker** — Intercepts network requests and serves cached responses. Handles caching strategies (cache-first, network-first, stale-while-revalidate). Workbox is the standard library.
2. **IndexedDB** — A browser database for storing structured data offline. Much larger capacity than localStorage (hundreds of MB). Use `idb` or Dexie for a nicer API.
3. **Sync queue** — When mutations happen offline, store them in a queue (IndexedDB). When connectivity returns, replay them against the server. Handle conflicts.
4. **Background Sync API** — The browser can trigger sync even after the tab is closed, ensuring queued mutations are eventually sent.

```jsx
// 1. Service Worker with Workbox — sw.ts (using workbox-webpack-plugin or vite-plugin-pwa)
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { BackgroundSyncPlugin } from 'workbox-background-sync';

// Precache all build output (HTML, JS, CSS, images)
precacheAndRoute(self.__WB_MANIFEST);

// Cache API responses — stale-while-revalidate for reads
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/') && !url.pathname.includes('/auth/'),
  new StaleWhileRevalidate({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 60 * 60 }), // 1 hour
    ],
  })
);

// Cache images — cache-first (images rarely change)
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'image-cache',
    plugins: [
      new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 30 * 24 * 60 * 60 }), // 30 days
    ],
  })
);

// Queue failed POST/PUT/DELETE requests for background sync
const bgSyncPlugin = new BackgroundSyncPlugin('mutation-queue', {
  maxRetentionTime: 24 * 60, // Retry for up to 24 hours
  onSync: async ({ queue }) => {
    let entry;
    while ((entry = await queue.shiftRequest())) {
      try {
        await fetch(entry.request.clone());
      } catch (error) {
        await queue.unshiftRequest(entry); // Put it back if it fails again
        throw error;
      }
    }
  },
});

registerRoute(
  ({ url, request }) =>
    url.pathname.startsWith('/api/') && ['POST', 'PUT', 'DELETE'].includes(request.method),
  new NetworkFirst({
    plugins: [bgSyncPlugin],
  }),
  'POST' // Match POST method
);

// 2. IndexedDB for local data — src/lib/offlineDb.ts
import Dexie from 'dexie';

class AppDatabase extends Dexie {
  tasks: Dexie.Table<Task, string>;
  syncQueue: Dexie.Table<SyncQueueItem, string>;

  constructor() {
    super('MyAppDB');
    this.version(1).stores({
      tasks: 'id, projectId, status, updatedAt',
      syncQueue: '++id, type, entityId, timestamp, [status+timestamp]',
    });
  }
}

export const db = new AppDatabase();

// 3. Offline-first hook — src/hooks/useOfflineFirst.ts
import { useLiveQuery } from 'dexie-react-hooks';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { db } from '@/lib/offlineDb';

export function useOfflineTasks(projectId: string) {
  // Read from IndexedDB (instant, works offline)
  const localTasks = useLiveQuery(
    () => db.tasks.where('projectId').equals(projectId).toArray(),
    [projectId]
  );

  // Sync with server in the background
  const serverQuery = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => tasksApi.list(projectId),
    staleTime: 5 * 60 * 1000,
    // On success, update IndexedDB
    onSuccess: async (serverTasks) => {
      await db.transaction('rw', db.tasks, async () => {
        // Upsert server data into local DB
        await db.tasks.bulkPut(serverTasks);
      });
    },
    // Don't fail if offline
    retry: (count, error) => navigator.onLine && count < 3,
  });

  // Return local data immediately, server sync happens in background
  return {
    tasks: localTasks ?? [],
    isLoading: localTasks === undefined,
    isSyncing: serverQuery.isFetching,
    lastSynced: serverQuery.dataUpdatedAt,
  };
}

// 4. Offline mutation with sync queue
export function useCreateTaskOffline() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (newTask: CreateTaskPayload) => {
      const task = { ...newTask, id: crypto.randomUUID(), syncStatus: 'pending' };

      // Save to IndexedDB immediately
      await db.tasks.add(task);

      // Queue for server sync
      await db.syncQueue.add({
        type: 'CREATE_TASK',
        entityId: task.id,
        payload: task,
        timestamp: Date.now(),
        status: 'pending',
      });

      // Try to sync now if online
      if (navigator.onLine) {
        try {
          const serverTask = await tasksApi.create(newTask);
          await db.tasks.update(task.id, { ...serverTask, syncStatus: 'synced' });
          await db.syncQueue.where('entityId').equals(task.id).delete();
          return serverTask;
        } catch {
          // Will be synced later via background sync
        }
      }

      return task;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

// 5. Online/offline status indicator
function OnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const pendingCount = useLiveQuery(() => db.syncQueue.count());

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <div className={`status-bar ${isOnline ? 'online' : 'offline'}`}>
      {isOnline ? '✓ Online' : '⚠ Offline — changes will sync when connected'}
      {pendingCount > 0 && <span>{pendingCount} changes pending sync</span>}
    </div>
  );
}
```

**Conflict resolution strategy:** When syncing offline mutations, the server may reject them due to conflicts (another user edited the same record). Implement a "last-write-wins" strategy for simple cases, or present a conflict resolution UI for critical data. Always log conflicts for debugging.

---

### Q18. How do you architect a multi-tenant SaaS application with React?

**Answer:**

A **multi-tenant SaaS** application serves multiple customers (tenants) from a single codebase and deployment. Each tenant sees their own data, branding, and possibly features, but shares the underlying infrastructure. The React frontend must handle tenant isolation, dynamic theming, tenant-specific configuration, and routing.

**Tenancy models:**
- **Subdomain-based**: `tenant1.app.com`, `tenant2.app.com`. Tenant identified from `window.location.hostname`. Most common for B2B SaaS.
- **Path-based**: `app.com/tenant1/dashboard`. Simpler infrastructure (single domain), but clutters URLs.
- **Custom domain**: `tenant1.com` → your app. Requires wildcard SSL and DNS configuration per tenant.

**Architecture concerns:**
- **Tenant identification**: Extract tenant slug from subdomain/path on app load, fetch tenant config from API.
- **Data isolation**: Every API request includes the tenant context (via header, path prefix, or JWT claim). The backend enforces row-level security.
- **Theming**: Load tenant-specific colors, logos, and custom CSS. Use CSS custom properties for runtime theme switching.
- **Feature tiers**: Different tenants have different feature sets (Free vs Pro vs Enterprise). Combine with feature flags.
- **Performance**: Tenant assets (logos, custom fonts) are loaded dynamically. Avoid bundling all tenant themes.

```jsx
// Multi-tenant SaaS architecture

// 1. Tenant identification — src/tenancy/useTenant.ts
import { createContext, useContext, useState, useEffect } from 'react';

interface TenantConfig {
  id: string;
  slug: string;
  name: string;
  plan: 'free' | 'pro' | 'enterprise';
  theme: {
    primaryColor: string;
    logoUrl: string;
    faviconUrl: string;
    customCss?: string;
  };
  features: string[];            // Enabled feature flags for this tenant
  settings: {
    ssoProvider?: string;        // Enterprise SSO
    allowedDomains: string[];
    maxUsers: number;
    dataRegion: 'us' | 'eu' | 'ap';
  };
}

const TenantContext = createContext<TenantConfig | null>(null);

export function TenantProvider({ children }) {
  const [tenant, setTenant] = useState<TenantConfig | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function loadTenant() {
      const slug = extractTenantSlug();
      if (!slug) {
        setError(new Error('No tenant found. Please check the URL.'));
        return;
      }

      try {
        const response = await fetch(`/api/tenants/${slug}/config`);
        if (!response.ok) throw new Error('Tenant not found');
        const config = await response.json();
        setTenant(config);
        applyTenantTheme(config.theme);
      } catch (err) {
        setError(err);
      }
    }
    loadTenant();
  }, []);

  if (error) return <TenantNotFound error={error} />;
  if (!tenant) return <TenantLoadingScreen />;

  return (
    <TenantContext.Provider value={tenant}>
      {children}
    </TenantContext.Provider>
  );
}

function extractTenantSlug(): string | null {
  // Subdomain-based: acme.app.com → "acme"
  const hostname = window.location.hostname;
  const parts = hostname.split('.');

  // For localhost development: use query param or header
  if (hostname === 'localhost') {
    return new URLSearchParams(window.location.search).get('tenant') || 'demo';
  }

  // acme.myapp.com → ['acme', 'myapp', 'com']
  if (parts.length >= 3) {
    return parts[0];
  }

  return null;
}

function applyTenantTheme(theme: TenantConfig['theme']) {
  const root = document.documentElement;
  root.style.setProperty('--color-primary', theme.primaryColor);

  // Dynamically set favicon
  const favicon = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
  if (favicon) favicon.href = theme.logoUrl;

  // Inject custom CSS if enterprise tenant has it
  if (theme.customCss) {
    const style = document.createElement('style');
    style.textContent = theme.customCss;
    style.id = 'tenant-custom-css';
    document.head.appendChild(style);
  }

  document.title = `${theme.name || 'App'}`;
}

export const useTenant = () => {
  const ctx = useContext(TenantContext);
  if (!ctx) throw new Error('useTenant must be within TenantProvider');
  return ctx;
};

// 2. Tenant-aware API client — src/lib/tenantApiClient.ts
import { apiClient } from '@/lib/apiClient';
import { useTenant } from '@/tenancy/useTenant';

// Interceptor adds tenant context to every request
apiClient.interceptors.request.use((config) => {
  const tenantSlug = extractTenantSlug();
  if (tenantSlug) {
    config.headers['X-Tenant-ID'] = tenantSlug;
  }
  return config;
});

// 3. Feature gating by tenant plan — src/tenancy/TenantGate.tsx
import { useTenant } from './useTenant';

interface TenantGateProps {
  requiredPlan?: 'pro' | 'enterprise';
  requiredFeature?: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function TenantGate({ requiredPlan, requiredFeature, fallback, children }) {
  const tenant = useTenant();

  const planHierarchy = { free: 0, pro: 1, enterprise: 2 };
  const hasPlan = !requiredPlan || planHierarchy[tenant.plan] >= planHierarchy[requiredPlan];
  const hasFeature = !requiredFeature || tenant.features.includes(requiredFeature);

  if (!hasPlan || !hasFeature) {
    return fallback ?? <UpgradeBanner requiredPlan={requiredPlan} />;
  }

  return children;
}

// Usage — Feature gating in navigation
function AppSidebar() {
  return (
    <nav>
      <NavLink to="/dashboard">Dashboard</NavLink>
      <NavLink to="/projects">Projects</NavLink>

      <TenantGate requiredPlan="pro">
        <NavLink to="/analytics">Analytics</NavLink>
        <NavLink to="/automations">Automations</NavLink>
      </TenantGate>

      <TenantGate requiredPlan="enterprise">
        <NavLink to="/audit-log">Audit Log</NavLink>
        <NavLink to="/sso-settings">SSO Settings</NavLink>
      </TenantGate>

      <TenantGate requiredFeature="beta-ai-assistant">
        <NavLink to="/ai-assistant">AI Assistant (Beta)</NavLink>
      </TenantGate>
    </nav>
  );
}

// 4. Tenant-scoped routing
function AppRoutes() {
  const tenant = useTenant();

  return (
    <Routes>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/projects/*" element={<Projects />} />

      {/* Pro+ routes */}
      {planHierarchy[tenant.plan] >= 1 && (
        <Route path="/analytics/*" element={<Analytics />} />
      )}

      {/* Enterprise routes */}
      {tenant.plan === 'enterprise' && (
        <>
          <Route path="/audit-log" element={<AuditLog />} />
          <Route path="/sso-settings" element={<SSOSettings />} />
          <Route path="/admin/*" element={<TenantAdmin />} />
        </>
      )}

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
```

**Production tip:** For enterprise customers with custom domains, use a reverse proxy (Cloudflare for SaaS, or a custom Nginx config) that maps custom domains to tenant slugs. Store the domain-to-tenant mapping in a fast lookup (Redis or edge KV store) to avoid database queries on every request.

---

### Q19. How do you plan and execute a migration from a legacy application to modern React?

**Answer:**

Migrating a legacy app (jQuery, AngularJS, older React with class components, or a server-rendered monolith) to modern React is one of the most challenging architectural tasks. The key principle is **incremental migration** — never attempt a Big Bang rewrite. The strangler fig pattern gradually replaces legacy code with new React code until the legacy app can be decommissioned.

**Migration strategies:**

1. **Strangler Fig Pattern**: Run the legacy and new React apps side-by-side. New features are built in React. Existing features are migrated one at a time. A router (reverse proxy or client-side) sends traffic to the right app based on the URL.

2. **Micro-frontend bridge**: Embed React components inside the legacy app using a mounting bridge. This lets you migrate individual widgets or sections without touching the legacy routing.

3. **Iframe embedding**: Lowest-effort integration — embed the new React app in an iframe within the legacy shell. Limited interactivity between old and new, but zero risk of CSS/JS conflicts.

4. **API-first migration**: Before migrating the frontend, refactor the backend to expose clean REST/GraphQL APIs. Then build the new React frontend against those APIs. This decouples frontend and backend migration timelines.

**Phase planning:**
- **Phase 0 (Preparation)**: Set up the new React project, CI/CD, design system. Map all legacy routes and features. Define the migration order (start with low-risk, high-value pages).
- **Phase 1 (Coexistence)**: Set up the routing bridge. Migrate 1-2 pages to prove the pattern works. Establish shared auth between old and new.
- **Phase 2 (Incremental migration)**: Migrate features one by one, following the dependency graph. Retire legacy code for each migrated feature.
- **Phase 3 (Cleanup)**: Remove the routing bridge, legacy app, and all compatibility code.

```jsx
// Migration architecture: Strangler Fig with reverse proxy

// 1. Reverse proxy routing (nginx.conf)
// All requests go to the React app by default.
// Legacy routes are explicitly proxied to the old app.
//
// server {
//   listen 80;
//
//   # Migrated routes → React app
//   location / {
//     proxy_pass http://react-app:3000;
//   }
//
//   # Legacy routes still in old app
//   location /legacy/reports {
//     proxy_pass http://legacy-app:8080;
//   }
//   location /legacy/admin {
//     proxy_pass http://legacy-app:8080;
//   }
// }

// 2. Embedding React components in a legacy jQuery/AngularJS app
// This bridge mounts React components into DOM elements in the legacy app

// react-bridge.ts — Mount React components into legacy pages
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/features/auth';

const queryClient = new QueryClient();
const mountedRoots = new Map();

export function mountReactComponent(
  containerId: string,
  Component: React.ComponentType,
  props: Record<string, any> = {}
) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container #${containerId} not found`);
    return;
  }

  // Clean up existing root if re-mounting
  if (mountedRoots.has(containerId)) {
    mountedRoots.get(containerId).unmount();
  }

  const root = createRoot(container);
  root.render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Component {...props} />
      </AuthProvider>
    </QueryClientProvider>
  );

  mountedRoots.set(containerId, root);
  return () => {
    root.unmount();
    mountedRoots.delete(containerId);
  };
}

export function unmountReactComponent(containerId: string) {
  if (mountedRoots.has(containerId)) {
    mountedRoots.get(containerId).unmount();
    mountedRoots.delete(containerId);
  }
}

// Usage in legacy HTML page:
// <div id="react-notifications"></div>
// <script src="/static/react-bridge.bundle.js"></script>
// <script>
//   window.ReactBridge.mountReactComponent(
//     'react-notifications',
//     window.ReactBridge.components.NotificationCenter,
//     { userId: currentUser.id }
//   );
// </script>

// 3. Shared authentication between legacy and React app
// Both apps use the same httpOnly cookie for auth.
// The React app reads the session from the same cookie domain.

// src/features/auth/legacyAuthBridge.ts
export function syncAuthFromLegacy() {
  // Legacy app stores user info in a cookie or global variable
  const legacyUser = window.__LEGACY_USER__;
  if (legacyUser) {
    return {
      id: legacyUser.id,
      email: legacyUser.email,
      token: legacyUser.token,
    };
  }
  return null;
}

// 4. Migration tracking dashboard
// Track migration progress per feature/route

const migrationPlan = [
  // Phase 1 — Quick wins (low risk, high visibility)
  { route: '/dashboard',      status: 'migrated',    team: 'frontend-1', sprint: '2024-Q1' },
  { route: '/profile',        status: 'migrated',    team: 'frontend-1', sprint: '2024-Q1' },
  { route: '/notifications',  status: 'migrated',    team: 'frontend-2', sprint: '2024-Q1' },

  // Phase 2 — Core features
  { route: '/orders/*',       status: 'in-progress', team: 'frontend-1', sprint: '2024-Q2' },
  { route: '/products/*',     status: 'in-progress', team: 'frontend-2', sprint: '2024-Q2' },
  { route: '/search',         status: 'planned',     team: 'frontend-2', sprint: '2024-Q2' },

  // Phase 3 — Complex features
  { route: '/reports/*',      status: 'planned',     team: 'frontend-1', sprint: '2024-Q3' },
  { route: '/admin/*',        status: 'planned',     team: 'frontend-3', sprint: '2024-Q3' },
  { route: '/settings/*',     status: 'planned',     team: 'frontend-2', sprint: '2024-Q3' },

  // Phase 4 — Cleanup
  { route: '(legacy removal)', status: 'planned',    team: 'all',        sprint: '2024-Q4' },
];

// 5. Feature parity testing — Playwright tests for both old and new
// test/migration/orders.spec.ts
import { test, expect } from '@playwright/test';

const LEGACY_URL = 'http://legacy-app.staging.internal';
const REACT_URL = 'http://react-app.staging.internal';

test.describe('Orders page — feature parity', () => {
  test('both apps show the same order count', async ({ page }) => {
    // Check legacy
    await page.goto(`${LEGACY_URL}/orders`);
    const legacyCount = await page.locator('.order-count').textContent();

    // Check React
    await page.goto(`${REACT_URL}/orders`);
    const reactCount = await page.locator('[data-testid="order-count"]').textContent();

    expect(reactCount).toBe(legacyCount);
  });

  test('search works identically in both apps', async ({ page }) => {
    const query = 'shipped';

    await page.goto(`${LEGACY_URL}/orders?search=${query}`);
    const legacyResults = await page.locator('.order-row').count();

    await page.goto(`${REACT_URL}/orders?search=${query}`);
    const reactResults = await page.locator('[data-testid="order-row"]').count();

    expect(reactResults).toBe(legacyResults);
  });
});
```

**Production tip:** The most common failure mode is trying to migrate too much at once. Migrate one route at a time, validate with automated tests and real user feedback, then move on. Keep the migration plan visible (a simple spreadsheet or project board) so the whole team and stakeholders can track progress. Budget 20% of each sprint for migration work alongside new feature development.

---

### Q20. System Design Interview: Architect a complete production e-commerce platform with React featuring SSR, real-time updates, auth, i18n, accessibility, and monitoring.

**Answer:**

This is a capstone system design question. You're asked to architect a full e-commerce platform — let's call it **ShopWave** — supporting millions of users across multiple countries. Here's how a staff-level engineer would approach this in an interview.

**Requirements gathering:**
- **Functional**: Product catalog with search/filters, shopping cart, checkout with payments, user accounts, order tracking, admin dashboard, wishlists, reviews.
- **Non-functional**: < 2s LCP on 3G, 99.9% uptime, WCAG 2.1 AA accessibility, support for 12 languages (including RTL), real-time inventory and order status updates, GDPR compliance.

**High-level architecture:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CDN (Cloudflare)                           │
│   Static assets (JS, CSS, images) + Edge caching for HTML pages     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      Next.js Application (Vercel Edge)              │
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │ Product Pages │ │ Cart/Checkout│ │ User Account │ │ Admin Panel│ │
│  │ (SSG + ISR)  │ │ (SSR)        │ │ (SSR)        │ │ (CSR + Auth)│ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Shared: Auth, i18n, Design System, Analytics, Error Monitoring  ││
│  └─────────────────────────────────────────────────────────────────┘│
└──────────┬──────────────┬─────────────────┬────────────────────────┘
           │              │                 │
    ┌──────▼──────┐ ┌─────▼─────┐  ┌───────▼───────┐
    │ REST/GraphQL│ │ WebSocket │  │ Headless CMS  │
    │ API Gateway │ │ Server    │  │ (Sanity)      │
    └──────┬──────┘ └─────┬─────┘  └───────────────┘
           │              │
    ┌──────▼──────────────▼───────────────────┐
    │ Backend Microservices                    │
    │ (Catalog, Cart, Orders, Payments, Users) │
    └──────────────────────────────────────────┘
```

**Technology decisions:**

| Concern | Choice | Rationale |
|---|---|---|
| Framework | Next.js 14+ (App Router) | SSR, SSG, ISR, API routes, built-in image optimization |
| State | TanStack Query (server) + Zustand (client) | Server cache for products/orders, client store for cart/UI |
| Styling | Tailwind CSS + CVA | Utility-first, tree-shaken, variant system for components |
| i18n | next-intl | Built for Next.js, ICU message format, route-based locale |
| Auth | NextAuth.js + custom JWT | OAuth providers, session management, RBAC |
| Real-time | Socket.IO or Ably | Live inventory, order tracking, admin notifications |
| CMS | Sanity | Marketing pages, product descriptions, SEO content |
| Monitoring | Sentry + Datadog RUM | Error tracking + performance monitoring |
| Testing | Vitest + Playwright | Unit/integration + E2E |
| Deployment | Vercel (Edge) + Cloudflare CDN | Edge SSR, automatic preview deploys |

```jsx
// ShopWave — Key architectural components

// 1. Rendering strategy per route (hybrid rendering)
//
// Route                  | Strategy | Why
// /                      | SSG+ISR  | Marketing page, rarely changes, max performance
// /products              | SSG+ISR  | Product listings, revalidate every 60s
// /products/[slug]       | SSG+ISR  | Product detail pages, generated at build time
// /search                | SSR      | Dynamic search results, personalized
// /cart                  | CSR      | Highly interactive, client-side state
// /checkout              | SSR      | Server validation, payment security
// /account/*             | SSR      | Authenticated, personalized
// /admin/*               | CSR      | Complex dashboards, behind auth

// 2. Product page with ISR, i18n, accessibility, and real-time stock
// app/[locale]/products/[slug]/page.tsx
import { getTranslations, unstable_setRequestLocale } from 'next-intl/server';
import { sanityClient } from '@/lib/sanity';
import { Suspense } from 'react';

export const revalidate = 60; // ISR: revalidate every 60 seconds

export async function generateStaticParams() {
  const slugs = await sanityClient.fetch(`*[_type == "product"].slug.current`);
  const locales = ['en', 'es', 'fr', 'de', 'ja', 'ar'];
  return locales.flatMap(locale =>
    slugs.map(slug => ({ locale, slug }))
  );
}

export default async function ProductPage({ params: { locale, slug } }) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations('product');
  const product = await sanityClient.fetch(productQuery, { slug, locale });

  // Structured data for SEO
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: product.description,
    image: product.images[0]?.url,
    offers: {
      '@type': 'Offer',
      price: product.price,
      priceCurrency: product.currency,
      availability: product.inStock
        ? 'https://schema.org/InStock'
        : 'https://schema.org/OutOfStock',
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <main>
        <nav aria-label={t('breadcrumb')}>
          <ol role="list">
            <li><a href="/">{t('home')}</a></li>
            <li><a href={`/products?category=${product.category}`}>{product.category}</a></li>
            <li aria-current="page">{product.name}</li>
          </ol>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ProductImageGallery
            images={product.images}
            alt={product.name}
          />

          <div>
            <h1 className="text-3xl font-bold">{product.name}</h1>
            <p className="text-2xl font-semibold mt-2">
              {new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: product.currency,
              }).format(product.price)}
            </p>

            {/* Real-time stock — client component for live updates */}
            <Suspense fallback={<StockSkeleton />}>
              <LiveStockIndicator productId={product.id} />
            </Suspense>

            <ProductVariantSelector variants={product.variants} />

            <AddToCartButton product={product} />

            {/* Accessible tabs for description, reviews, shipping */}
            <ProductTabs product={product} />
          </div>
        </div>

        {/* Related products — loaded on scroll */}
        <Suspense fallback={<ProductGridSkeleton count={4} />}>
          <RelatedProducts category={product.category} excludeId={product.id} />
        </Suspense>
      </main>
    </>
  );
}

// 3. Real-time stock indicator — client component
// components/LiveStockIndicator.tsx
'use client';

import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { useTranslations } from 'next-intl';

export function LiveStockIndicator({ productId }) {
  const [stock, setStock] = useState(null);
  const t = useTranslations('product');

  useEffect(() => {
    const socket = io(process.env.NEXT_PUBLIC_WS_URL, {
      query: { productId },
    });

    socket.on('stock:update', (data) => {
      if (data.productId === productId) {
        setStock(data.quantity);
      }
    });

    // Initial fetch
    fetch(`/api/products/${productId}/stock`)
      .then(r => r.json())
      .then(data => setStock(data.quantity));

    return () => socket.disconnect();
  }, [productId]);

  if (stock === null) return null;

  return (
    <div
      role="status"
      aria-live="polite"               // Announce stock changes to screen readers
      className={stock > 10 ? 'text-green-600' : stock > 0 ? 'text-amber-600' : 'text-red-600'}
    >
      {stock === 0 && t('outOfStock')}
      {stock > 0 && stock <= 10 && t('lowStock', { count: stock })}
      {stock > 10 && t('inStock')}
    </div>
  );
}

// 4. Accessible cart with keyboard navigation and screen reader support
'use client';

import { useCartStore } from '@/features/cart/cartStore';
import { useTranslations } from 'next-intl';

export function CartDrawer({ isOpen, onClose }) {
  const t = useTranslations('cart');
  const { items, removeItem, updateQuantity, total } = useCartStore();
  const cartRef = useRef(null);

  // Trap focus when open
  useEffect(() => {
    if (isOpen) {
      cartRef.current?.focus();
      document.body.style.overflow = 'hidden';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={t('title')}
      ref={cartRef}
      tabIndex={-1}
      className={`cart-drawer ${isOpen ? 'open' : ''}`}
    >
      <div className="flex justify-between items-center">
        <h2 id="cart-title">{t('title')}</h2>
        <button
          onClick={onClose}
          aria-label={t('close')}
        >
          ✕
        </button>
      </div>

      {items.length === 0 ? (
        <p>{t('empty')}</p>
      ) : (
        <ul role="list" aria-label={t('itemsList')}>
          {items.map(item => (
            <li key={item.id} className="cart-item">
              <img src={item.image} alt="" width={64} height={64} />
              <div>
                <p className="font-medium">{item.name}</p>
                <label>
                  {t('quantity')}
                  <select
                    value={item.quantity}
                    onChange={(e) => updateQuantity(item.id, Number(e.target.value))}
                    aria-label={t('quantityFor', { product: item.name })}
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </label>
              </div>
              <button
                onClick={() => removeItem(item.id)}
                aria-label={t('remove', { product: item.name })}
              >
                {t('removeButton')}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div aria-live="polite" className="cart-total">
        <strong>{t('total')}: {formatCurrency(total)}</strong>
      </div>

      <button
        className="checkout-button"
        disabled={items.length === 0}
        onClick={() => router.push('/checkout')}
      >
        {t('proceedToCheckout')}
      </button>
    </div>
  );
}

// 5. Monitoring and observability setup
// middleware.ts — Server-side performance tracking

import { NextResponse } from 'next/server';

export function middleware(request) {
  const response = NextResponse.next();

  // Add Server-Timing header for backend visibility
  const start = Date.now();
  response.headers.set('Server-Timing', `middleware;dur=${Date.now() - start}`);

  // Security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://js.stripe.com; style-src 'self' 'unsafe-inline'; img-src 'self' https://cdn.sanity.io data:; connect-src 'self' https://api.shopwave.com wss://ws.shopwave.com https://o*.ingest.sentry.io;"
  );

  return response;
}

// Performance budget enforcement
// next.config.js
module.exports = {
  experimental: {
    webVitalsAttribution: ['CLS', 'LCP', 'INP'],  // Detailed attribution
  },
  images: {
    formats: ['image/avif', 'image/webp'],          // Modern formats
    domains: ['cdn.sanity.io'],
    deviceSizes: [640, 750, 828, 1080, 1200],
  },
  headers: async () => [
    {
      source: '/_next/static/:path*',
      headers: [
        { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
      ],
    },
  ],
};

// 6. Complete provider tree composition — app/[locale]/layout.tsx
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';

export default async function RootLayout({ children, params: { locale } }) {
  const messages = await getMessages();

  return (
    <html lang={locale} dir={['ar', 'he'].includes(locale) ? 'rtl' : 'ltr'}>
      <body>
        <NextIntlClientProvider messages={messages}>
          <AuthProvider>
            <CartProvider>
              <SentryErrorBoundary>
                <SkipToContent />
                <Header />
                <main id="main-content" tabIndex={-1}>
                  {children}
                </main>
                <Footer />
                <CookieConsentBanner />
                <PerformanceMonitor />
              </SentryErrorBoundary>
            </CartProvider>
          </AuthProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

**System design interview tips:**
1. **Start with requirements** — Clarify functional and non-functional requirements before designing.
2. **Choose the rendering strategy per route** — Not everything needs SSR. Products are SSG+ISR, checkout is SSR, cart is CSR.
3. **Discuss trade-offs explicitly** — "I chose Next.js over a Vite SPA because product pages benefit from SSG for SEO and LCP, but the trade-off is more complex deployment and server costs."
4. **Address cross-cutting concerns** — Auth, i18n, a11y, monitoring, and error handling are what distinguish a production design from a prototype.
5. **Mention scale considerations** — CDN caching strategy, database indexing for search, WebSocket scaling with Redis pub/sub, image optimization pipeline.
6. **Draw the architecture** — In a real interview, sketch the system diagram on the whiteboard showing the CDN, edge layer, API gateway, microservices, databases, and real-time infrastructure.

This architecture handles millions of users by serving static assets from the CDN edge (< 50ms TTFB), rendering product pages via ISR (fresh content without server load), isolating real-time concerns to WebSocket connections, and providing a robust monitoring stack that catches issues before users report them.

---

*This capstone file covers the full spectrum of production React architecture — from project structure and CI/CD to system design interviews. Mastering these topics is what separates a mid-level React developer who can build features from a senior/staff engineer who can architect, deploy, and operate production systems at scale.*
