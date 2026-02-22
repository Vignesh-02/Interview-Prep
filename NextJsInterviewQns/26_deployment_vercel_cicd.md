# 26. Deployment, Vercel & CI/CD

## Topic Introduction

**Deploying Next.js 15/16** commonly targets **Vercel** (optimized for Next), **Node server** (e.g. Docker), or **static export**. CI/CD runs **lint**, **test**, and **build**; then deploys the output. Senior developers understand **environment variables**, **build cache**, **output modes**, and **edge vs serverless** so deployments are fast and correct.

```
Deploy flow (typical):
┌─────────────────────────────────────────────────────────────┐
│  Git push → CI (lint, test, build) → Build artifact          │
│       → Deploy to Vercel / Node / Static host                 │
│  Env: Set in platform (Vercel, AWS, etc.)                    │
│  Cache: .next/cache, node_modules (or Turbo remote cache)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Q1. (Beginner) What is the default output of `next build` and where can you deploy it?

**Answer**:

Default is **standalone**-capable **serverless/Node** output: a **.next** folder and **node_modules** (or a minimal standalone folder with **output: 'standalone'**). You run **node .next/standalone/server.js** (or the serverless functions) on a Node host or a platform that supports Node (Vercel, AWS Lambda, Docker, etc.). You can also use **output: 'export'** for static HTML/CSS/JS only (no server routes; no Server Actions at runtime).

---

## Q2. (Beginner) How do you set environment variables for a Next.js app on Vercel?

**Scenario**: You need DATABASE_URL and NEXT_PUBLIC_API_URL in production.

**Answer**:

In **Vercel**: Project → Settings → Environment Variables. Add **DATABASE_URL** and **NEXT_PUBLIC_API_URL** for the **Production** (and optionally Preview) environment. **NEXT_PUBLIC_*** are inlined at build time; ensure they’re set for the environment you’re building. Redeploy after changing env vars so the new values are used.

---

## Q3. (Beginner) What is the difference between building locally and building on Vercel?

**Answer**:

- **Locally**: Uses your local Node and `.env.local`; build output is on your machine.
- **Vercel**: Build runs in Vercel’s environment; env vars come from the project settings. Vercel may use a different Node version and **caching** (e.g. `.next/cache`, `node_modules`) to speed up builds. **NEXT_PUBLIC_*** are baked in at build time on Vercel, so they must be set in the project for the branch you’re building.

---

## Q4. (Beginner) What does `output: 'standalone'` do in next.config.js?

**Answer**:

It creates a **standalone** folder under `.next/standalone` that contains a minimal Node server and only the dependencies needed to run the app. You can copy that folder (and `.next/static`, `public`) to a server and run **node server.js** without a full **node_modules** install. Used for **Docker** or self-hosted Node deployments.

---

## Q5. (Beginner) When would you use `output: 'export'` and what are the limitations?

**Answer**:

Use **static export** when you want to host the app as **static files** (no Node server). Limitations: **no** Server Routes (API routes, dynamic server logic), **no** Server Actions at runtime, **no** incremental static regeneration (ISR), **no** rewrites/redirects that need the server. Only **statically generated** pages and client-side behavior work. Good for marketing sites or fully static apps.

---

## Q6. (Intermediate) How do you run the Next.js app in a Docker container for production?

**Scenario**: You need a production Dockerfile that runs the app.

**Answer**:

Use **output: 'standalone'** and a multi-stage Dockerfile: (1) Build stage: install deps, run `next build`. (2) Run stage: copy `.next/standalone`, `.next/static`, and `public` into a minimal image (e.g. `node:alpine`) and run `node server.js`. Don’t copy the full `node_modules`; the standalone output has a minimal set. Set **NODE_ENV=production** and expose the port (e.g. 3000).

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static .next/static
COPY --from=builder /app/public public
EXPOSE 3000
CMD ["node", "server.js"]
```

---

## Q7. (Intermediate) How do you configure a CI pipeline (e.g. GitHub Actions) to build and run tests before deploy?

**Scenario**: On every PR you want lint, test, and build; on merge to main you want deploy.

**Answer**:

- **On pull_request**: Checkout, install (e.g. `pnpm install`), run `pnpm lint`, `pnpm test`, `pnpm build`. Cache `node_modules` and optionally `.next/cache` to speed up.
- **On push to main**: Same steps; then deploy (e.g. trigger Vercel deploy via API, or push to a branch that Vercel auto-deploys). Use **secrets** for any deploy tokens.

```yaml
# Example (simplified)
- run: pnpm install
- run: pnpm lint
- run: pnpm test
- run: pnpm build
# Then deploy (e.g. Vercel CLI or platform integration)
```

---

## Q8. (Intermediate) Production scenario: Build succeeds in CI but the deployed app shows "Application error" or blank page. What do you check?

**Answer**:

- **Runtime env**: Required env vars (e.g. DATABASE_URL) might be missing in the deployment environment. Check the platform’s env settings and that they’re applied to the right environment (production/preview).
- **Serverless function limits**: Cold start or timeout; increase memory/timeout if the app does heavy work on first request.
- **Client-side error**: Open browser console and network tab; check for 4xx/5xx or JS errors. If the page is blank, often a client error during hydration or a missing **NEXT_PUBLIC_** var.
- **Output mode**: If you used **output: 'export'** but have server features (API routes, Server Actions), the app can’t work; remove static export or move those features to a separate backend.

---

## Q9. (Intermediate) What are Vercel’s "Preview" deployments and how do they differ from Production?

**Answer**:

**Preview** deployments are created for every push (or every PR). They get a unique URL and typically use **Preview** env vars. **Production** is usually the main branch (e.g. main) and uses **Production** env vars. Use Preview for QA and staging; Production for live traffic. You can set different env values for Preview (e.g. staging API) and Production.

---

## Q10. (Intermediate) How do you run database migrations as part of a deploy (e.g. before the new app goes live)?

**Answer**:

Run migrations in **CI** or in a **deploy hook** **before** switching traffic to the new version. For example: in GitHub Actions, after build, run `pnpm db:migrate` (or a script that runs your migration tool) against the **production** DB (using production DB URL from secrets). Then deploy the app. That way the new code sees the migrated schema. Optionally use **read-only** during migration and then switch; or run migrations that are backward-compatible so the old app still works during deploy.

---

## Q11. (Intermediate) Find the bug: Build works locally but fails on Vercel with "Module not found".

**Scenario**: You use a path alias or a local file that exists locally but not in the Vercel build.

**Answer**:

- **Path alias**: Ensure **tsconfig.json** paths and **next.config.js** (if any) match. Vercel builds from a clean clone; paths are relative to the repo root. Case sensitivity (Linux on Vercel vs Windows locally) can cause "module not found" if the path case is wrong.
- **Missing file**: A file might be in **.gitignore** (e.g. env or generated file) and not present in the Vercel build. Don’t rely on files that aren’t in the repo; use env vars or build-time generation instead.
- **Optional dependency**: A module might be optional locally but required in the serverless runtime. Add it as a direct dependency or ensure the code path that uses it isn’t hit at build time if it’s not installed.

---

## Q12. (Intermediate) How do you use the Vercel CLI to link a local project to a Vercel project and pull env vars?

**Answer**:

- **Link**: Run **vercel link** in the project directory; choose or create a Vercel project. This creates `.vercel/project.json` (and optionally `.vercel/settings.json`).
- **Pull env**: Run **vercel env pull** to download env vars from the linked project into `.env.local` (or a file you specify). Use this to test locally with production-like env (be careful with production DB URLs).

---

## Q13. (Advanced) How do you implement zero-downtime deployment for a self-hosted Next.js app (e.g. behind a load balancer)?

**Answer**:

- **Blue-green or rolling**: Run two (or more) instances; build the new version, start new instances, then switch the load balancer to the new instances and drain the old ones. Next.js doesn’t require special handling; just ensure the new process is healthy before switching.
- **Process manager**: Use PM2 or similar: start the new process, then reload so the new process takes over. Brief overlap or reload can cause minimal downtime; for zero downtime you need multiple processes and a graceful handover (e.g. load balancer health checks).

---

## Q14. (Advanced) What is the difference between deploying to Vercel Edge vs Node.js serverless for a Route Handler?

**Answer**:

- **Edge**: Runs on the edge (V8 isolates); very low latency and no cold start in the same sense as Lambda; limited Node APIs (no full Node modules). Use for **middleware** and lightweight Route Handlers that don’t need Node.
- **Node serverless**: Runs in a Node runtime (e.g. Lambda); full Node APIs and larger cold starts. Use for Route Handlers that need DB drivers, heavy libs, or long execution.

Set **export const runtime = 'edge'** in the Route Handler to force edge; omit or set **'nodejs'** for Node.

---

## Q15. (Advanced) How do you cache the Next.js build in CI (e.g. .next/cache) to speed up builds?

**Answer**:

- **GitHub Actions**: Cache the `.next/cache` directory (and optionally `node_modules`) using **actions/cache** with a key that includes the lockfile hash (and optionally the branch). Restore before `pnpm install` and `next build`; save after build.
- **Vercel**: Vercel caches `.next/cache` and `node_modules` by default; no extra config.
- **Turborepo**: Use **turbo run build** with remote caching so the Next app’s build can be restored from cache when inputs haven’t changed.

---

## Q16. (Advanced) Production scenario: After deploy, some users get stale content. You use ISR with revalidate. What could be wrong?

**Answer**:

- **CDN**: The CDN might be caching the page beyond your **revalidate** window. Set **Cache-Control** (e.g. `s-maxage=<revalidate>, stale-while-revalidate`) so the CDN respects revalidation. Next.js sets these for ISR when you use **revalidate** in fetch or **revalidatePath**/revalidateTag.
- **Multiple regions**: Edge nodes might have different cache state; ensure cache keys include the route (and locale if applicable) and that revalidation is propagated (e.g. Vercel does this; for custom CDN you may need to purge or set short s-maxage).
- **Client Router Cache**: Users might see cached RSC payload from the client. **router.refresh()** or a full reload fetches fresh data; for critical updates, consider shorter **staleTimes** or prompting a refresh.

---

## Q17. (Advanced) How do you run E2E tests against a Preview deployment URL in CI?

**Answer**:

After the deploy step (or via Vercel’s deploy hook), get the **Preview URL** (e.g. from the Vercel API or the GitHub deployment payload). Set it as an env var (e.g. **BASE_URL**) and run Playwright (or Cypress) with **baseURL** set to that. So: deploy → get URL → run E2E against that URL. This tests the real deployed build, not just local.

---

## Q18. (Advanced) Next.js 15 vs 16: Any deployment or config differences?

**Answer**:

- **Next.js 16**: Turbopack as default for builds; same **output** options (standalone, export). Deployment steps (build command, start command) are unchanged. No new deployment-specific APIs.
- **Config**: **next.config.js** is the same; no new required fields for deployment. If you had **experimental** flags, check if they’re stable or renamed in 16.

---

## Q19. (Advanced) How do you implement a canary or percentage-based rollout for a Next.js app on Vercel?

**Answer**:

Vercel supports **rollouts** (percentage of traffic to a new deployment). Use the dashboard or API to set a percentage for the new deployment; the rest stays on the previous. For self-hosted, use a load balancer or gateway (e.g. feature flags or routing by header/cookie) to send a percentage of traffic to the new version.

---

## Q20. (Advanced) Design a CI/CD pipeline that runs lint, unit tests, E2E tests, and build; then deploys to staging and, on approval, to production. Include rollback.

**Answer**:

- **On PR**: Lint, unit tests, build. Optional: deploy to Preview and run E2E against Preview URL.
- **On merge to main**: Lint, unit tests, build, deploy to **staging** (e.g. staging.vercel.app or a staging branch). Run E2E against staging. Notify or wait for approval.
- **On approval** (manual or automated): Deploy the same artifact to **production** (e.g. production branch or promote the deployment).
- **Rollback**: Revert the git commit and re-run the pipeline to deploy the previous version; or in Vercel, "Promote to Production" the previous deployment. Keep last N production deployments available for quick rollback.
