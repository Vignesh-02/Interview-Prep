# 30. Production Readiness & Zero-Downtime Deploys

## Topic Introduction

Production readiness is everything between "it works on my machine" and "it runs reliably for millions of users." It encompasses: **graceful shutdown**, **health checks**, **configuration management**, **zero-downtime deployment**, **rollback strategies**, **monitoring**, and **incident response**.

```
Development → Staging → Canary (5%) → Production (100%)
                                         │
                              ┌───────────┤
                              │           │
                         Monitoring   Auto-rollback
                         & Alerting   on error spike
```

This is the capstone topic — it ties together everything from the previous 29 topics into a production-ready Node.js service.

---

## Q1. (Beginner) What is graceful shutdown? Why does it matter?

```js
const server = http.createServer(app);

async function shutdown(signal) {
  console.log(`${signal} received. Starting graceful shutdown...`);

  // 1. Stop accepting new connections
  server.close(() => {
    console.log('HTTP server closed');
  });

  // 2. Wait for in-flight requests to complete (max 30s)
  const forceTimeout = setTimeout(() => {
    console.error('Forcing shutdown after timeout');
    process.exit(1);
  }, 30000);
  forceTimeout.unref();

  // 3. Close database connections
  await pool.end();
  await redis.quit();

  // 4. Stop background job workers
  await worker.close();

  console.log('Graceful shutdown complete');
  process.exit(0);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
```

**Answer**: Without graceful shutdown, in-flight requests are dropped, database transactions are left incomplete, and job workers abandon mid-processing. K8s sends SIGTERM before killing pods — your app must drain connections within `terminationGracePeriodSeconds`.

---

## Q2. (Beginner) What health check endpoints should every service have?

```js
// Liveness — "Is the process running?" (K8s restarts if this fails)
app.get('/health/live', (req, res) => {
  res.json({ status: 'alive', uptime: process.uptime() });
});

// Readiness — "Can I serve traffic?" (K8s stops routing if this fails)
app.get('/health/ready', async (req, res) => {
  const checks = {};
  try { await pool.query('SELECT 1'); checks.database = 'ok'; }
  catch { checks.database = 'fail'; }
  try { await redis.ping(); checks.redis = 'ok'; }
  catch { checks.redis = 'fail'; }

  const ready = Object.values(checks).every(v => v === 'ok');
  res.status(ready ? 200 : 503).json({ status: ready ? 'ready' : 'not_ready', checks });
});

// Startup — "Has the app finished initializing?" (K8s waits during startup)
let started = false;
app.get('/health/startup', (req, res) => {
  res.status(started ? 200 : 503).json({ started });
});

// After initialization:
await runMigrations();
await warmCache();
started = true;
server.listen(3000);
```

---

## Q3. (Beginner) How do you manage configuration across environments?

```js
// Configuration validation at startup (fail fast)
const { z } = require('zod');

const configSchema = z.object({
  NODE_ENV: z.enum(['development', 'staging', 'production']),
  PORT: z.string().transform(Number).default('3000'),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

const config = configSchema.parse(process.env);
// If any required variable is missing → app crashes at startup with clear error
// NOT after the first request hits the missing config

module.exports = config;
```

---

## Q4. (Beginner) What are the essential npm scripts for a production Node.js app?

```json
{
  "scripts": {
    "start": "node dist/server.js",
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "test": "jest --coverage",
    "test:integration": "jest --config jest.integration.config.js",
    "lint": "eslint src/",
    "migrate": "node-pg-migrate up",
    "migrate:down": "node-pg-migrate down",
    "typecheck": "tsc --noEmit",
    "docker:build": "docker build -t myapp .",
    "health": "curl -f http://localhost:3000/health/ready || exit 1"
  }
}
```

---

## Q5. (Beginner) How do you write a production Dockerfile for Node.js?

```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build
RUN npm prune --production

FROM node:20-alpine
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER app
EXPOSE 3000
HEALTHCHECK CMD wget -q --spider http://localhost:3000/health/live || exit 1
CMD ["node", "dist/server.js"]
```

**Key practices**: Multi-stage build (smaller image), non-root user, production dependencies only, health check, alpine base (small).

---

## Q6. (Intermediate) How do you implement zero-downtime deployments?

**Answer**: Zero-downtime deployment ensures users never see errors or downtime during deploys.

```
Strategy 1: Rolling update (K8s default)
  Pod 1 (old) ✓    Pod 1 (old) ✓    Pod 1 (new) ✓    Pod 1 (new) ✓
  Pod 2 (old) ✓ →  Pod 2 (new) ... → Pod 2 (new) ✓ →  Pod 2 (new) ✓
  Pod 3 (old) ✓    Pod 3 (old) ✓    Pod 3 (old) ✓    Pod 3 (new) ✓

Strategy 2: Blue-green
  Blue (current) ← traffic     Blue  ← traffic     Blue (remove)
  Green (deploy) ─ no traffic  Green ─ no traffic → Green ← ALL traffic

Strategy 3: Canary
  Stable: 100% traffic → Stable: 95% | Canary: 5% → Stable: 0% | New: 100%
```

**Requirements**: (1) Graceful shutdown, (2) Readiness probe, (3) Database migrations are backward compatible, (4) API changes are backward compatible.

---

## Q7. (Intermediate) How do you implement feature flags for safe deployments?

```js
// Feature flag check before using new code path
const flags = require('./feature-flags');

app.get('/dashboard', async (req, res) => {
  if (await flags.isEnabled('new-dashboard-v2', { userId: req.user.id })) {
    return renderNewDashboard(req, res);
  }
  return renderOldDashboard(req, res);
});

// Deploy new code behind flag → enable for 5% → 25% → 100%
// If issues: disable flag instantly (no redeploy needed)
```

---

## Q8. (Intermediate) How do you handle secrets rotation without downtime?

```js
// Watch for secret changes (Vault, AWS Secrets Manager)
const secretsManager = require('@aws-sdk/client-secrets-manager');

let dbCredentials = null;

async function refreshSecrets() {
  const secret = await sm.getSecretValue({ SecretId: 'prod/db-credentials' });
  const newCreds = JSON.parse(secret.SecretString);

  // Create new connection pool with new credentials
  const newPool = new Pool({ connectionString: newCreds.connectionString });
  await newPool.query('SELECT 1'); // verify new creds work

  // Swap pools
  const oldPool = global.pool;
  global.pool = newPool;

  // Drain old pool gracefully
  await oldPool.end();
}

// Refresh every hour
setInterval(refreshSecrets, 3600000);
```

---

## Q9. (Intermediate) How do you implement canary deployments with automatic rollback?

```js
// Canary deployment monitoring
// Deploy new version to 5% of pods
// Compare error rates between canary and stable

async function monitorCanary() {
  const canaryErrorRate = await prometheus.query(
    'rate(http_errors_total{version="canary"}[5m]) / rate(http_requests_total{version="canary"}[5m])'
  );
  const stableErrorRate = await prometheus.query(
    'rate(http_errors_total{version="stable"}[5m]) / rate(http_requests_total{version="stable"}[5m])'
  );

  if (canaryErrorRate > stableErrorRate * 2) { // canary error rate 2x higher
    console.error('Canary error rate too high, rolling back!');
    await kubectl('rollout undo deployment/my-app');
    await alertTeam('Canary rollback triggered');
  }
}
```

---

## Q10. (Intermediate) What is a production readiness checklist?

**Answer**:

```
☐ Graceful shutdown (SIGTERM handling)
☐ Health check endpoints (liveness, readiness, startup)
☐ Structured logging (JSON, request IDs)
☐ Metrics exposed (/metrics for Prometheus)
☐ Error handling (no stack traces to clients)
☐ Input validation on all endpoints
☐ Authentication & authorization
☐ Rate limiting
☐ CORS and security headers (helmet)
☐ Database connection pooling
☐ Database migrations versioned and tested
☐ Environment variable validation at startup
☐ No secrets in code or logs
☐ Docker image (multi-stage, non-root)
☐ CI/CD pipeline (lint, test, build, deploy)
☐ Monitoring dashboard
☐ Alerting rules (error rate, latency, saturation)
☐ Runbook for common incidents
☐ Backup and recovery plan
☐ Load tested to expected peak
```

---

## Q11. (Intermediate) How do you manage Node.js process memory in production?

```js
// Monitor memory usage
setInterval(() => {
  const { heapUsed, heapTotal, rss, external } = process.memoryUsage();
  metrics.heapUsed.set(heapUsed);
  metrics.rss.set(rss);

  // Alert if approaching limit
  const heapLimit = v8.getHeapStatistics().heap_size_limit;
  if (heapUsed / heapLimit > 0.85) {
    logger.warn({ heapUsed, heapLimit }, 'Memory usage high — possible leak');
  }
}, 30000);

// Set memory limit explicitly
// node --max-old-space-size=2048 server.js  (2GB)
// In K8s: resources.limits.memory should be ~1.5x --max-old-space-size
```

---

## Q12. (Intermediate) How do you handle database migrations during zero-downtime deploys?

```
Deploy sequence for backward-compatible migration:

1. Run migration (ALTER TABLE ADD COLUMN — backward compatible)
2. Deploy new code (reads new column if present, handles missing gracefully)
3. Backfill data in new column
4. Deploy code that requires new column
5. (Later) Remove old column if needed

NEVER:
- Drop a column before all app versions stop using it
- Rename a column (add new + copy + drop old)
- Add NOT NULL constraint without default on existing column
```

---

## Q13. (Advanced) Production scenario: You're deploying a major version. Walk through the complete deployment strategy.

**Answer**:

```
Pre-deploy:
  ☐ Run migration in staging, verify
  ☐ Load test new version
  ☐ Feature-flag new functionality (disabled)
  ☐ Update runbook with rollback steps

Deploy (canary):
  1. Run database migration (backward compatible)
  2. Deploy to 1 canary pod (5% traffic)
  3. Monitor for 15 minutes: error rate, latency, logs
  4. If healthy → deploy to 25%, then 50%, then 100%
  5. If unhealthy → rollback canary, investigate

Post-deploy:
  ☐ Enable feature flags gradually (5% → 25% → 100%)
  ☐ Monitor for 24 hours
  ☐ Update team on deployment status
  ☐ Clean up old feature flag code in next sprint
```

---

## Q14. (Advanced) How do you implement automated rollback based on metrics?

```yaml
# Argo Rollouts canary with automatic rollback
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 5
        - pause: { duration: 5m }
        - analysis:
            templates:
              - templateName: error-rate
        - setWeight: 25
        - pause: { duration: 10m }
        - setWeight: 100
  # Analysis template checks Prometheus metrics
  # If error rate > threshold → automatic rollback
```

---

## Q15. (Advanced) How do you design a multi-environment pipeline (dev → staging → production)?

```yaml
# CI/CD pipeline (GitHub Actions)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm ci && npm test && npm run lint && npm run typecheck

  build:
    needs: test
    steps:
      - run: docker build -t myapp:${{ github.sha }} .
      - run: docker push myapp:${{ github.sha }}

  deploy-staging:
    needs: build
    environment: staging
    steps:
      - run: kubectl set image deployment/myapp myapp=myapp:${{ github.sha }} -n staging
      - run: kubectl rollout status deployment/myapp -n staging --timeout=300s

  deploy-production:
    needs: deploy-staging
    environment: production  # requires manual approval
    steps:
      - run: kubectl set image deployment/myapp myapp=myapp:${{ github.sha }} -n production
      - run: kubectl rollout status deployment/myapp -n production --timeout=300s
```

---

## Q16. (Advanced) How do you handle production incidents? Describe your incident response process.

```
1. DETECT: Alert fires (error rate > 5%)
2. ACKNOWLEDGE: On-call engineer acknowledges within 5 min
3. TRIAGE: Severity assessment (S1-S4)
   - S1: Full outage → all hands
   - S2: Major feature degraded → on-call team
   - S3: Minor issue → next business day
4. MITIGATE: Focus on restoring service, not root cause
   - Rollback? Feature flag off? Scale up? Restart?
5. COMMUNICATE: Status page update, stakeholder notification
6. RESOLVE: Fix the issue
7. POST-MORTEM: Blameless review within 48 hours
   - Timeline of events
   - Root cause analysis
   - Action items (prevent recurrence)
```

---

## Q17. (Advanced) How do you implement observability-driven deployment (deploy with confidence)?

```js
// Pre-deploy: baseline metrics
const baseline = {
  errorRate: await getMetric('error_rate_5m'),
  p99Latency: await getMetric('request_duration_p99'),
  qps: await getMetric('request_rate_5m'),
};

// Post-deploy: compare with baseline
async function validateDeploy() {
  const current = {
    errorRate: await getMetric('error_rate_5m'),
    p99Latency: await getMetric('request_duration_p99'),
    qps: await getMetric('request_rate_5m'),
  };

  if (current.errorRate > baseline.errorRate * 1.5) return { healthy: false, reason: 'error rate increased 50%' };
  if (current.p99Latency > baseline.p99Latency * 2) return { healthy: false, reason: 'latency doubled' };
  if (current.qps < baseline.qps * 0.5) return { healthy: false, reason: 'traffic dropped 50%' };
  return { healthy: true };
}
```

---

## Q18. (Advanced) How do you handle dependency updates and security patches?

```bash
# Automated security scanning
npm audit
npx snyk test

# Dependabot/Renovate for automated PRs
# renovate.json
{
  "extends": ["config:base"],
  "schedule": ["every weekend"],
  "packageRules": [
    { "matchUpdateTypes": ["patch"], "automerge": true },
    { "matchUpdateTypes": ["minor", "major"], "automerge": false }
  ]
}
```

---

## Q19. (Advanced) How does production readiness compare across Go, Java, and Node.js?

| Aspect | **Node.js** | **Go** | **Java** |
|--------|-------------|--------|----------|
| Cold start | ~200ms | ~50ms | ~1-5s (without GraalVM) |
| Memory footprint | 50-200MB | 10-50MB | 200MB-1GB |
| Graceful shutdown | Manual (SIGTERM handler) | Manual (context.Done) | Spring handles it |
| Health checks | Manual middleware | Manual handler | Spring Actuator (built-in) |
| Configuration | dotenv + zod validation | viper (structured) | Spring Config (declarative) |
| Docker image | ~150MB (alpine) | ~10MB (scratch) | ~200MB+ |
| Hot reload | tsx, nodemon | air | Spring DevTools |

**Go advantage**: Tiny images, fast start, single binary. **Java advantage**: Spring Boot Actuator gives health, metrics, config, shutdown for free. **Node advantage**: Fast iteration, huge ecosystem, small memory footprint.

---

## Q20. (Advanced) Senior production readiness red flags.

**Answer**:

1. **No graceful shutdown** — requests dropped during deploys
2. **No health checks** — K8s can't route traffic correctly
3. **console.log instead of structured logging** — can't debug in production
4. **No monitoring or alerting** — issues discovered by users, not metrics
5. **Secrets in environment without validation** — crash on first request, not startup
6. **No database migration strategy** — manual ALTER TABLE in production
7. **No rollback plan** — if deploy fails, panic
8. **No load testing** — first real load test is production traffic
9. **Running as root in container** — security risk
10. **No CI/CD pipeline** — manual deploys are error-prone
11. **No feature flags** — every feature is all-or-nothing
12. **No backup/recovery testing** — assume backups work without testing

**Senior interview answer**: "Production readiness is a checklist, not a feeling. I ensure graceful shutdown, comprehensive health checks, structured logging, Prometheus metrics, automated CI/CD with canary deployments, feature flags for safe rollouts, and a tested rollback plan. Every deploy is monitored against baseline metrics with automatic rollback on regression."
