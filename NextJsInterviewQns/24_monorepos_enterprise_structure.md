# 24. Monorepos, Multi-zones & Enterprise Structure

## Topic Introduction

**Enterprise Next.js** often runs in **monorepos** (Turborepo, Nx, pnpm workspaces) with shared packages (ui, config, types) and sometimes **multi-zones** (multiple Next.js apps under one domain). Senior developers need to structure apps for scale, team boundaries, and consistent builds.

```
Monorepo (Turborepo example):
apps/
  web/          ← Next.js (App Router)
  docs/         ← Next.js or Docusaurus
  api/          ← Node/Edge API
packages/
  ui/           ← Shared React components
  config-eslint/
  config-typescript/
  tsconfig/     ← Base tsconfig
```

**Multi-zones**: Different Next.js apps serve different path prefixes (e.g. `/blog` from app A, `/dashboard` from app B) behind one domain using rewrites or a gateway.

---

## Q1. (Beginner) What is a monorepo and why use it for a Next.js app?

**Scenario**: You have a Next.js app and a shared component library; you want one repo and atomic changes.

**Answer**:

A **monorepo** is one repository containing multiple packages or apps. Benefits: **single PR** for app + shared code, **shared tooling** (ESLint, TypeScript), **atomic refactors**, and **faster CI** with incremental builds (Turborepo, Nx). For Next.js, you typically have `apps/web` (the Next app) and `packages/ui` (or similar) consumed by the app via workspace protocol (`"ui": "workspace:*"`).

---

## Q2. (Beginner) How do you import a local package (e.g. `@company/ui`) into a Next.js app in a monorepo?

**Scenario**: apps/web should use components from packages/ui.

**Answer**:

- In **package.json** of apps/web: `"@company/ui": "workspace:*"` (pnpm/yarn) or `"@company/ui": "*"` with workspaces in root.
- In **packages/ui**: Export components (e.g. `export { Button } from './Button'`).
- In Next.js, **transpile** the package so Next compiles it: in **next.config.js** add `transpilePackages: ['@company/ui']`.
- Import in app: `import { Button } from '@company/ui'`.

---

## Q3. (Beginner) What are Next.js "multi-zones"?

**Answer**:

**Multi-zones** let multiple Next.js apps (or other apps) run under one domain on different paths. One app is the "main" app; others are mounted at paths (e.g. `/blog` → blog app). Implemented via **rewrites** in next.config.js of the main app pointing to another app’s URL (e.g. `destination: 'https://blog.myapp.com'`). The user sees one origin; the main app proxies or redirects to the other app for those paths.

---

## Q4. (Beginner) Where do you put shared TypeScript types in a monorepo — app or package?

**Answer**:

Put them in a **shared package** (e.g. `packages/types`) and have both app and other packages depend on it. That way types are single source of truth and the app doesn’t own types that other services need. Export from `packages/types` and add `"@company/types": "workspace:*"` in apps and packages that need them.

---

## Q5. (Beginner) What is Turborepo and how does it help a Next.js monorepo?

**Answer**:

**Turborepo** is a build system for monorepos. It runs tasks (e.g. `build`, `lint`) with **caching** (local and optional remote) and **task dependencies** (e.g. build `ui` before `web`). It only runs a task when inputs changed. So `turbo run build` builds only what’s needed and reuses cache for unchanged packages, speeding up CI and local builds.

---

## Q6. (Intermediate) How do you structure environment variables in a monorepo with multiple Next.js apps?

**Scenario**: apps/web and apps/docs need different env vars; some are shared.

**Answer**:

- **Per-app**: Each app has its own `.env.local` (and deployment env). Don’t put secrets in the root.
- **Shared**: Use a root `.env.example` listing all vars; each app copies what it needs. Or use a shared `packages/config` that reads from `process.env` and is used only by server code; each app sets its own env in deployment.
- **Naming**: Prefix with app name if needed (e.g. `WEB_API_URL`, `DOCS_API_URL`) to avoid collisions when running multiple apps in one process (e.g. in e2e).

---

## Q7. (Intermediate) Configure Next.js in a monorepo so that the app builds when a dependency in packages/ui changes.

**Scenario**: Changing a component in packages/ui should invalidate the Next.js build cache.

**Answer**:

- **Turborepo**: Declare that `web` depends on `ui` (e.g. `"build": ["ui"]` in pipeline). When `ui` changes, Turborepo will rebuild `ui` and then `web`. Next.js will see the updated `ui` package because it’s linked via workspace.
- **Next.js**: `transpilePackages: ['@company/ui']` ensures the package is recompiled as part of the app build, so changes in `ui` are picked up when you build the app.

---

## Q8. (Intermediate) How do you run the Next.js app in dev mode with hot reload when you change code in a linked package?

**Answer**:

- **transpilePackages**: Next.js compiles the package; in dev, changing a file in the package should trigger a rebuild if the package is inside the repo and watched. Ensure the package path is not excluded from the watcher.
- **Symlinks**: Workspace packages are symlinked; Next.js (and Turbopack) watch those paths. If HMR doesn’t pick up changes, ensure the package is in `transpilePackages` and that you’re not running the app from a different workspace root that doesn’t see the symlink.

---

## Q9. (Intermediate) Production scenario: Build fails in CI with "Module not found: @company/ui" even though it works locally. What could be wrong?

**Answer**:

- **Install**: CI might not run `pnpm install` (or equivalent) at the repo root, so workspace links aren’t created. Fix: run install at root in CI.
- **Build order**: If CI builds only the Next app and doesn’t build `packages/ui` first, the package might not have its `dist` or built output. Fix: build dependencies first (Turborepo pipeline or explicit `pnpm --filter @company/ui build` then `pnpm --filter web build`).
- **Hoisting**: Some installers don’t hoist `@company/ui` the same way. Prefer a single lockfile and same package manager (e.g. pnpm) in CI and locally.

---

## Q10. (Intermediate) How do you share ESLint and TypeScript config across apps in a monorepo?

**Answer**:

- **packages/config-eslint**: Export a base config (e.g. `extends: ['next/core-web-vitals']`) and in each app’s `.eslintrc.js`: `extends: ['@company/config-eslint']`.
- **packages/config-typescript** or **tsconfig/base.json** at root: Export `extends` and options; each app’s `tsconfig.json` has `"extends": "@company/config-typescript"` or `"extends": "../../tsconfig.base.json"` and overrides (e.g. `paths`, `include`).

---

## Q11. (Intermediate) What is the difference between building the Next.js app from the app directory vs from the repo root with Turborepo?

**Answer**:

- **From app directory** (`cd apps/web && pnpm build`): Next.js runs in that directory; it resolves workspace packages via node_modules symlinks. No Turborepo cache or dependency ordering.
- **From root** (`turbo run build`): Turborepo runs `build` in each package that has it; order follows the pipeline (e.g. build `ui` then `web`). Outputs can be cached. Same Next.js build, but with orchestration and cache.

---

## Q12. (Intermediate) How do you set up path aliases (@/components, etc.) in a Next.js app that lives in apps/web in a monorepo?

**Answer**:

In **apps/web/tsconfig.json**: `"paths": { "@/*": ["./*"] }` so `@/components` resolves to `apps/web/components`. If you want `@company/ui` to resolve to the local package, it’s already the package name; no need for a path alias unless you alias it to a subpath (e.g. `@company/ui/*` → `../../packages/ui/src/*`). Usually the package name and `transpilePackages` are enough.

---

## Q13. (Advanced) Design a multi-zone setup: main app at myapp.com, blog at myapp.com/blog served by a different Next.js app. Describe config and deployment.

**Answer**:

- **Main app** (myapp.com): In **next.config.js**, add rewrite: `source: '/blog', destination: 'https://blog-app.vercel.app/blog'` (or your blog app URL). So when users hit myapp.com/blog, the main app proxies to the blog app; the browser still shows myapp.com/blog.
- **Blog app**: Deployed separately; basePath can be `/blog` so its routes are under /blog. Or blog app has no basePath and the main app rewrites `/blog` to the blog app’s `/` and the blog app serves content that appears at myapp.com/blog.
- **Deployment**: Main app and blog app are two deployments. Main app’s rewrites point to the blog app’s deployment URL. Cookies/domain: if both are on same parent domain you can share cookies; otherwise use separate auth or SSO.

---

## Q14. (Advanced) How do you avoid circular dependencies between packages in a monorepo (e.g. ui → hooks → ui)?

**Answer**:

- **Split packages**: e.g. `ui` (only presentational components), `hooks` (only hooks), `utils` (only pure utils). Dependencies flow one way: ui can depend on hooks and utils; hooks should not depend on ui. If a hook needs a component, consider putting it in the app or a higher-level package.
- **Extract shared types**: Put shared types in `packages/types` so both ui and hooks depend on types, not on each other.
- **Dependency graph**: Use a tool (e.g. madge, Nx graph) to detect cycles and break them by moving code or introducing a small shared package.

---

## Q15. (Advanced) Production scenario: After adding a new package, `next build` is slow because it recompiles the whole app. How do you optimize?

**Answer**:

- **transpilePackages**: Only list packages that must be compiled (React, ESM-only packages). If the new package is already built (e.g. emits CJS/ESM from `dist`), don’t add it to transpilePackages so Next doesn’t recompile it.
- **Turborepo**: Ensure the package has a `build` script and the Next app depends on it; then Turborepo builds the package once and caches it. Next.js then just consumes the built output.
- **Incremental**: Use Turbopack in Next 16 for faster builds. Ensure `.next/cache` is preserved in CI if you use persistent cache.

---

## Q16. (Advanced) How do you version and publish shared packages (e.g. ui) from a monorepo without publishing the Next.js app?

**Answer**:

- Use **changesets** or **lerna**: You version only the packages that changed and run `publish` for those packages. The Next app (apps/web) is typically not published to npm; it’s a private app. So you run `changeset version` and `changeset publish` (or lerna publish) and only `packages/ui` (and similar) get version bumps and publish; apps stay unpublished.
- **Private registry**: If packages are private, use a private npm registry or GitHub Packages and set `publishConfig` in each publishable package.

---

## Q17. (Advanced) Next.js 15 vs 16: Any impact on monorepo or Turborepo usage?

**Answer**:

No structural change. Next.js 16 with Turbopack may **build faster**, which helps when the monorepo has one or more Next apps. Turborepo’s remote cache still works the same. No new monorepo-specific APIs in 15 or 16.

---

## Q18. (Advanced) How do you run E2E tests (Playwright) that cover the main app and a multi-zone blog in one suite?

**Answer**:

- E2E tests run against one **origin** (e.g. localhost:3000). The main app is served there with rewrites pointing the blog to the same host (e.g. another process on a different port and rewrite `destination: 'http://localhost:3001/blog'`) or the same server that mounts both. So when tests visit `/blog`, they hit the blog app via the main app’s rewrite.
- **Start both**: In CI, start the main app and the blog app (or a combined server), then run Playwright against the main app’s URL. Tests that navigate to `/blog` will get the blog content via the rewrite.

---

## Q19. (Advanced) Find the bug: "Cannot find module '@company/ui'" at runtime in production even though build succeeded.

**Scenario**: Build and deploy succeed; at runtime the server or client throws the above.

**Answer**:

- **Server**: The deployed server might not have `node_modules/@company/ui` (or the symlink might not be preserved). In a monorepo deploy, ensure the **install** step runs at the root (or that the deploy includes the workspace and runs install so the linked package is present). Some platforms deploy only one app directory; then you must either publish `@company/ui` to a registry and install it as a dependency, or configure the deploy to include the monorepo and install from root.
- **Client**: If the package is only used in Server Components, it shouldn’t be in the client bundle. If it’s used in Client Components, it’s bundled at build time; runtime "module not found" on the client usually means the chunk failed to load (CDN/network), not that the package is missing. So the fix is usually on the server: ensure the deployed artifact has the package (or it’s installed from a registry).

---

## Q20. (Advanced) Design an enterprise structure: 3 teams (Auth, Billing, Dashboard), each owning part of the same Next.js app. How do you split code and allow independent deploys?

**Answer**:

- **Option A – Single app, owned routes**: One repo, one Next app. Folders by domain: `app/(auth)/`, `app/(billing)/`, `app/(dashboard)/`. Each team owns its route group and related components/actions. Deploy is one app; ownership is by directory and CODEOWNERS. No independent deploys; use feature flags and trunk-based development.
- **Option B – Multi-zones**: Each team has its own Next app (e.g. apps/auth, apps/billing, apps/dashboard). Main app rewrites `/auth`, `/billing`, `/dashboard` to each app’s deployment. Teams deploy their app independently. Shared: packages/ui, packages/types. Harder: shared layout, navigation, and auth state across zones (e.g. shared cookie domain, or iframe/redirects).
- **Option C – Monorepo + single app + ownership**: One app, monorepo with `apps/web` and `packages/auth`, `packages/billing`, `packages/dashboard` as internal packages. Each team maintains a package; the app composes them. Deploy is still one app, but code ownership and PRs are per package. Independent "releases" can be achieved by versioning packages and updating the app’s dependency when a team ships.

Choose based on how much you need true independent deploys (B) vs simpler structure with clear ownership (A or C).
