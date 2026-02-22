# 26. Background Jobs & Task Scheduling

## Topic Introduction

Not every operation should happen during an HTTP request. Sending emails, generating reports, processing images, and syncing data are better handled **asynchronously** in the background. This keeps API responses fast and allows retries without affecting users.

```
Synchronous (blocking):         Asynchronous (background):
Client → API → Send Email →    Client → API → Queue Job → Response (fast!)
         Wait 3 seconds...                         ↓
         ← Response (slow)      Worker → Send Email (whenever ready)
```

**Key tools**: BullMQ (Redis-based, most popular for Node.js), Agenda (MongoDB-based), node-cron (simple scheduling), Temporal (complex workflows), AWS SQS + Lambda.

**Go/Java tradeoff**: Java has robust scheduling with Spring Batch and Quartz. Go uses goroutines + channels for lightweight background work. Node.js needs external job queues (BullMQ) because the event loop shouldn't be blocked by long tasks.

---

## Q1. (Beginner) What are background jobs and why do you need them?

**Answer**: Background jobs are tasks that run outside the HTTP request-response cycle.

| Run in request (synchronous) | Run as background job |
|---|---|
| Validate input | Send emails/notifications |
| Read/write to DB | Generate PDF reports |
| Return response | Process uploaded images |
| | Sync data with third parties |
| | Aggregate analytics |
| | Clean up expired data |

```js
// BAD: email in request path (user waits for email to send)
app.post('/api/orders', async (req, res) => {
  const order = await Order.create(req.body);
  await sendEmail(order.userId, 'Order confirmed!'); // 2-3 seconds!
  res.json(order); // user waited 3+ seconds
});

// GOOD: queue email as background job (user gets instant response)
app.post('/api/orders', async (req, res) => {
  const order = await Order.create(req.body);
  await emailQueue.add('order-confirmation', { orderId: order.id }); // <1ms
  res.json(order); // instant response
});
```

---

## Q2. (Beginner) How do you set up BullMQ for background job processing?

```js
const { Queue, Worker } = require('bullmq');
const Redis = require('ioredis');

const connection = new Redis({ host: 'redis', port: 6379, maxRetriesPerRequest: null });

// 1. Create a queue
const emailQueue = new Queue('email', { connection });

// 2. Add jobs to the queue
await emailQueue.add('order-confirmation', {
  orderId: 'order-123',
  userId: 'user-42',
  template: 'order_confirmation',
}, {
  attempts: 3,           // retry 3 times on failure
  backoff: {
    type: 'exponential',
    delay: 5000,          // 5s, 10s, 20s between retries
  },
  removeOnComplete: 1000, // keep last 1000 completed jobs
  removeOnFail: 5000,     // keep last 5000 failed jobs
});

// 3. Create a worker to process jobs
const emailWorker = new Worker('email', async (job) => {
  const { orderId, userId, template } = job.data;
  console.log(`Processing email job ${job.id}: ${template} for user ${userId}`);

  const user = await User.findById(userId);
  const order = await Order.findById(orderId);
  await sendEmail(user.email, template, { order });

  return { sent: true, email: user.email };
}, {
  connection,
  concurrency: 5,   // process 5 jobs simultaneously
  limiter: {
    max: 10,         // max 10 jobs per 1 second (rate limit)
    duration: 1000,
  },
});

// 4. Handle events
emailWorker.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result);
});

emailWorker.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed:`, err.message);
  if (job.attemptsMade >= job.opts.attempts) {
    // All retries exhausted — alert team
    alerting.send('Email job failed permanently', { jobId: job.id, error: err.message });
  }
});
```

---

## Q3. (Beginner) How do you implement simple cron-like scheduling in Node.js?

```js
const cron = require('node-cron');

// Run every day at midnight
cron.schedule('0 0 * * *', async () => {
  console.log('Running daily cleanup...');
  await cleanupExpiredSessions();
  await archiveOldOrders();
});

// Run every hour
cron.schedule('0 * * * *', async () => {
  await syncInventory();
});

// Run every 5 minutes
cron.schedule('*/5 * * * *', async () => {
  await checkHealthOfExternalServices();
});

// Cron expression format:
// ┌─────────── second (optional, 0-59)
// │ ┌───────── minute (0-59)
// │ │ ┌─────── hour (0-23)
// │ │ │ ┌───── day of month (1-31)
// │ │ │ │ ┌─── month (1-12)
// │ │ │ │ │ ┌─ day of week (0-7, 0 or 7 = Sunday)
// * * * * * *
```

**Problem**: If you have 3 server instances, the cron runs 3 times. Solution: use BullMQ's `repeat` option (only one worker processes).

```js
// BullMQ repeatable job (runs once across all instances)
await reportQueue.add('daily-report', {}, {
  repeat: {
    pattern: '0 0 * * *', // midnight daily
  },
});
```

---

## Q4. (Beginner) What are job priorities and how do you use them?

```js
// Priority: lower number = higher priority

// Critical: password reset email (priority 1)
await emailQueue.add('password-reset', { userId, token }, { priority: 1 });

// Normal: order confirmation (priority 5)
await emailQueue.add('order-confirmation', { orderId }, { priority: 5 });

// Low: marketing newsletter (priority 10)
await emailQueue.add('newsletter', { campaignId }, { priority: 10 });

// Worker processes highest priority first
// If there are password resets waiting, they're processed before newsletters
```

---

## Q5. (Beginner) How do you handle job failures and retries?

```js
// Configure retry strategy
await queue.add('process-payment', paymentData, {
  attempts: 5,
  backoff: {
    type: 'exponential', // 1s, 2s, 4s, 8s, 16s
    delay: 1000,
  },
});

// Custom retry logic in worker
const worker = new Worker('payments', async (job) => {
  try {
    return await processPayment(job.data);
  } catch (err) {
    if (err.code === 'CARD_DECLINED') {
      // Don't retry — it'll fail again
      throw new UnrecoverableError('Card declined');
    }
    if (err.code === 'NETWORK_ERROR') {
      // Retry — might work next time
      throw err;
    }
    throw err;
  }
}, { connection });

// Move permanently failed jobs to dead letter queue
worker.on('failed', async (job, err) => {
  if (job.attemptsMade >= job.opts.attempts) {
    await deadLetterQueue.add('failed-payment', {
      originalJob: job.data,
      error: err.message,
      failedAt: new Date(),
      attempts: job.attemptsMade,
    });
  }
});
```

---

## Q6. (Intermediate) How do you implement delayed and scheduled jobs?

```js
// Delayed job: process after a specific delay
await queue.add('send-reminder', { orderId: 'o1' }, {
  delay: 24 * 60 * 60 * 1000, // 24 hours from now
});

// Scheduled job: process at a specific time
const scheduledTime = new Date('2024-12-25T09:00:00Z');
await queue.add('christmas-promo', { campaignId: 'xmas' }, {
  delay: scheduledTime.getTime() - Date.now(),
});

// Repeatable jobs (cron-like)
await queue.add('cleanup', {}, {
  repeat: {
    pattern: '0 3 * * *',   // 3 AM daily
    tz: 'America/New_York',  // timezone-aware
  },
});

await queue.add('health-check', {}, {
  repeat: { every: 60000 },  // every 60 seconds
});

// List repeatable jobs
const repeatableJobs = await queue.getRepeatableJobs();
console.log(repeatableJobs);

// Remove a repeatable job
await queue.removeRepeatableByKey(repeatableJobs[0].key);
```

---

## Q7. (Intermediate) How do you monitor background jobs in production?

```js
const { QueueEvents } = require('bullmq');

// Prometheus metrics for job queues
const jobDuration = new Histogram({ name: 'job_duration_seconds', help: 'Job processing duration', labelNames: ['queue', 'jobName'] });
const jobsCompleted = new Counter({ name: 'jobs_completed_total', help: 'Total completed jobs', labelNames: ['queue', 'jobName'] });
const jobsFailed = new Counter({ name: 'jobs_failed_total', help: 'Total failed jobs', labelNames: ['queue', 'jobName'] });
const queueSize = new Gauge({ name: 'queue_size', help: 'Current queue size', labelNames: ['queue', 'state'] });

const queueEvents = new QueueEvents('email', { connection });

queueEvents.on('completed', ({ jobId, returnvalue }) => {
  jobsCompleted.inc({ queue: 'email', jobName: 'email' });
});

queueEvents.on('failed', ({ jobId, failedReason }) => {
  jobsFailed.inc({ queue: 'email', jobName: 'email' });
});

// Poll queue stats periodically
setInterval(async () => {
  const waiting = await emailQueue.getWaitingCount();
  const active = await emailQueue.getActiveCount();
  const delayed = await emailQueue.getDelayedCount();
  const failed = await emailQueue.getFailedCount();

  queueSize.set({ queue: 'email', state: 'waiting' }, waiting);
  queueSize.set({ queue: 'email', state: 'active' }, active);
  queueSize.set({ queue: 'email', state: 'delayed' }, delayed);
  queueSize.set({ queue: 'email', state: 'failed' }, failed);
}, 15000);

// BullMQ Board for visual monitoring
const { createBullBoard } = require('@bull-board/api');
const { BullMQAdapter } = require('@bull-board/api/bullMQAdapter');
const { ExpressAdapter } = require('@bull-board/express');

const serverAdapter = new ExpressAdapter();
createBullBoard({
  queues: [new BullMQAdapter(emailQueue), new BullMQAdapter(reportQueue)],
  serverAdapter,
});
app.use('/admin/queues', authAdmin, serverAdapter.getRouter());
```

---

## Q8. (Intermediate) How do you scale background job workers?

```js
// Option 1: Concurrency within one process
const worker = new Worker('tasks', processTask, {
  connection,
  concurrency: 10, // process 10 jobs at once
});

// Option 2: Multiple worker processes (horizontal scaling)
// Run multiple instances of the worker process
// Each instance picks up different jobs from the queue
// BullMQ handles distribution automatically

// Option 3: Auto-scaling based on queue depth
async function autoScale() {
  const waiting = await queue.getWaitingCount();
  const active = await queue.getActiveCount();

  if (waiting > 1000 && active < 50) {
    console.log('Queue is backing up — scale up workers');
    // kubectl scale deployment worker --replicas=5
    // or: PM2 scale worker +2
  }
  if (waiting === 0 && active < 5) {
    console.log('Queue is empty — scale down');
    // kubectl scale deployment worker --replicas=1
  }
}

setInterval(autoScale, 30000);

// Rate limiting to protect external APIs
const worker = new Worker('api-sync', syncData, {
  connection,
  limiter: {
    max: 100,
    duration: 60000, // max 100 jobs per minute
  },
});
```

---

## Q9. (Intermediate) How do you implement job progress tracking?

```js
// Worker reports progress
const worker = new Worker('reports', async (job) => {
  const data = await fetchReportData(job.data);
  await job.updateProgress(25);

  const processed = await processData(data);
  await job.updateProgress(50);

  const pdf = await generatePDF(processed);
  await job.updateProgress(75);

  const url = await uploadToS3(pdf);
  await job.updateProgress(100);

  return { url, pages: pdf.pages };
}, { connection });

// API to check job progress
app.post('/api/reports', auth, async (req, res) => {
  const job = await reportQueue.add('generate', req.body);
  res.json({ jobId: job.id });
});

app.get('/api/reports/:jobId/status', auth, async (req, res) => {
  const job = await reportQueue.getJob(req.params.jobId);
  if (!job) return res.status(404).json({ error: 'Job not found' });

  const state = await job.getState();
  res.json({
    state,
    progress: job.progress,
    result: state === 'completed' ? job.returnvalue : undefined,
    failedReason: state === 'failed' ? job.failedReason : undefined,
  });
});

// Real-time progress via SSE
app.get('/api/reports/:jobId/progress', auth, (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');

  const queueEvents = new QueueEvents('reports', { connection });
  queueEvents.on('progress', ({ jobId, data }) => {
    if (jobId === req.params.jobId) {
      res.write(`data: ${JSON.stringify({ progress: data })}\n\n`);
    }
  });
  queueEvents.on('completed', ({ jobId, returnvalue }) => {
    if (jobId === req.params.jobId) {
      res.write(`data: ${JSON.stringify({ state: 'completed', result: returnvalue })}\n\n`);
      res.end();
    }
  });

  req.on('close', () => queueEvents.close());
});
```

---

## Q10. (Intermediate) How do you handle job dependencies (job A must complete before job B)?

```js
// BullMQ flow: parent-child job dependencies
const { FlowProducer } = require('bullmq');
const flowProducer = new FlowProducer({ connection });

// Define a workflow: process order → charge payment → send email
const flow = await flowProducer.add({
  name: 'send-confirmation',
  queueName: 'email',
  data: { template: 'order_complete' },
  children: [
    {
      name: 'charge-payment',
      queueName: 'payments',
      data: { amount: 99.99 },
      children: [
        {
          name: 'validate-order',
          queueName: 'orders',
          data: { orderId: 'o1', items: [...] },
        },
      ],
    },
  ],
});

// Execution order:
// 1. validate-order runs first (leaf node)
// 2. charge-payment runs after validate-order completes
// 3. send-confirmation runs after charge-payment completes

// Access parent job data from child
const worker = new Worker('email', async (job) => {
  // Get results from child jobs
  const childResults = await job.getChildrenValues();
  console.log('Payment result:', childResults); // { 'charge-payment': { transactionId: '...' } }
});
```

---

## Q11. (Intermediate) How do you prevent duplicate job processing?

```js
// Problem: user clicks "send" twice, two identical emails are queued

// Solution 1: Unique job ID
await emailQueue.add('welcome-email', { userId: 'u1' }, {
  jobId: `welcome-${userId}`, // same ID = same job (deduplication)
});
// Second add with same jobId is ignored

// Solution 2: Debounce (reset delay on duplicate)
await emailQueue.add('sync-user', { userId: 'u1' }, {
  jobId: `sync-${userId}`,
  delay: 5000,
  // If added again within 5 seconds, delay resets
});

// Solution 3: Application-level dedup
async function enqueueIfNotProcessed(queueName, jobName, data, uniqueKey) {
  const dedupKey = `dedup:${queueName}:${uniqueKey}`;
  const alreadyProcessed = await redis.set(dedupKey, '1', 'EX', 3600, 'NX');
  if (!alreadyProcessed) {
    console.log(`Job ${uniqueKey} already processed, skipping`);
    return null;
  }
  return queue.add(jobName, data);
}
```

---

## Q12. (Intermediate) How do you implement batch processing for large datasets?

```js
// Process 1 million records in batches
const BATCH_SIZE = 1000;

// Queue batch jobs
async function startBatchExport(exportId) {
  const totalRecords = await db('orders').count('* as count').first();
  const totalBatches = Math.ceil(totalRecords.count / BATCH_SIZE);

  for (let i = 0; i < totalBatches; i++) {
    await batchQueue.add('export-batch', {
      exportId,
      offset: i * BATCH_SIZE,
      limit: BATCH_SIZE,
      batchNumber: i + 1,
      totalBatches,
    }, {
      priority: 5,
      attempts: 3,
    });
  }

  await db('exports').update({ status: 'processing', totalBatches }).where({ id: exportId });
}

// Worker: process one batch
const batchWorker = new Worker('batch', async (job) => {
  const { exportId, offset, limit, batchNumber, totalBatches } = job.data;

  const records = await db('orders').offset(offset).limit(limit);
  const csvLines = records.map(r => `${r.id},${r.total},${r.status}`).join('\n');

  // Append to S3 file
  await appendToS3(`exports/${exportId}/batch-${batchNumber}.csv`, csvLines);

  // Track progress
  await job.updateProgress(Math.round((batchNumber / totalBatches) * 100));

  // Check if all batches done
  const completed = await batchQueue.getCompletedCount();
  if (completed >= totalBatches) {
    // Merge all batch files into final export
    await mergeBatchFiles(exportId, totalBatches);
    await db('exports').update({ status: 'completed' }).where({ id: exportId });
  }
}, { connection, concurrency: 5 });
```

---

## Q13. (Advanced) How do you implement a workflow engine with BullMQ?

```js
// Complex workflow: User signs up → verify email → create profile → welcome email → analytics
class Workflow {
  constructor(name, steps) {
    this.name = name;
    this.steps = steps;
  }

  async start(data) {
    const workflowId = randomUUID();
    await redis.set(`workflow:${workflowId}`, JSON.stringify({
      name: this.name,
      currentStep: 0,
      data,
      startedAt: new Date(),
    }));

    await this.executeStep(workflowId, 0, data);
    return workflowId;
  }

  async executeStep(workflowId, stepIndex, data) {
    if (stepIndex >= this.steps.length) {
      await redis.set(`workflow:${workflowId}:status`, 'completed');
      return;
    }

    const step = this.steps[stepIndex];
    await queue.add(step.name, {
      workflowId,
      stepIndex,
      data,
    }, {
      attempts: step.retries || 3,
      backoff: { type: 'exponential', delay: 1000 },
    });
  }
}

// Define workflow
const signupWorkflow = new Workflow('user-signup', [
  { name: 'verify-email', queue: 'email', retries: 3 },
  { name: 'create-profile', queue: 'users', retries: 2 },
  { name: 'send-welcome', queue: 'email', retries: 3 },
  { name: 'track-signup', queue: 'analytics', retries: 1 },
]);

// Start workflow
app.post('/api/signup', async (req, res) => {
  const user = await User.create(req.body);
  const workflowId = await signupWorkflow.start({ userId: user.id });
  res.json({ userId: user.id, workflowId });
});

// Worker advances to next step on completion
worker.on('completed', async (job) => {
  const { workflowId, stepIndex, data } = job.data;
  await signupWorkflow.executeStep(workflowId, stepIndex + 1, data);
});
```

---

## Q14. (Advanced) How do you handle idempotency in background jobs?

```js
// Jobs may be processed more than once (worker crashes, timeout, retry)
// EVERY job must be idempotent

// NON-IDEMPOTENT (dangerous):
async function processPayment(job) {
  await db.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [job.data.amount, job.data.accountId]);
  // If processed twice, money deducted twice!
}

// IDEMPOTENT (safe):
async function processPayment(job) {
  const { paymentId, amount, accountId } = job.data;

  // Check if already processed
  const existing = await db.query('SELECT * FROM payments WHERE id = $1', [paymentId]);
  if (existing.rows.length > 0) {
    console.log(`Payment ${paymentId} already processed, skipping`);
    return existing.rows[0];
  }

  // Process atomically with idempotency check
  await db.transaction(async (trx) => {
    // Double-check inside transaction (prevents race condition)
    const dupe = await trx('payments').where({ id: paymentId }).first();
    if (dupe) return dupe;

    await trx('payments').insert({ id: paymentId, amount, account_id: accountId, status: 'completed' });
    await trx.raw('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, accountId]);
  });
}
```

---

## Q15. (Advanced) How do you handle poison messages that repeatedly fail?

```js
// After all retries exhausted, job goes to "failed" state
// But what if it keeps blocking the queue?

const worker = new Worker('orders', async (job) => {
  try {
    return await processOrder(job.data);
  } catch (err) {
    // Classify the error
    if (isTransient(err)) throw err; // let BullMQ retry
    if (isPermanent(err)) {
      // Move to DLQ manually, don't retry
      await deadLetterQueue.add('failed-order', {
        originalData: job.data,
        error: err.message,
        jobId: job.id,
      });
      return; // don't throw — marks as completed (removes from queue)
    }
    throw err;
  }
}, { connection });

function isTransient(err) {
  return ['ECONNRESET', 'ETIMEDOUT', 'ECONNREFUSED'].includes(err.code) || err.status >= 500;
}

function isPermanent(err) {
  return err.code === 'VALIDATION_ERROR' || err.code === 'NOT_FOUND' || err.status === 400;
}

// Admin endpoint to replay DLQ messages after fixing the bug
app.post('/admin/dlq/replay', authAdmin, async (req, res) => {
  const failedJobs = await deadLetterQueue.getCompleted(0, 100);
  for (const job of failedJobs) {
    await orderQueue.add('process-order', job.data.originalData);
  }
  res.json({ replayed: failedJobs.length });
});
```

---

## Q16. (Advanced) How do you implement rate-limited job processing for external APIs?

```js
// Scenario: Stripe API rate limit is 100 req/s
// You have 10,000 invoices to generate

const worker = new Worker('invoices', async (job) => {
  return await stripe.invoices.create(job.data);
}, {
  connection,
  concurrency: 5,
  limiter: {
    max: 90,          // 90 per duration (leave 10 for other traffic)
    duration: 1000,    // per second
  },
});

// Global rate limiter across multiple queues
class GlobalRateLimiter {
  constructor(redis, key, maxPerSecond) {
    this.redis = redis;
    this.key = `ratelimit:${key}`;
    this.max = maxPerSecond;
  }

  async acquire() {
    const count = await this.redis.incr(this.key);
    if (count === 1) await this.redis.expire(this.key, 1);
    if (count > this.max) {
      const ttl = await this.redis.pttl(this.key);
      await new Promise(r => setTimeout(r, ttl > 0 ? ttl : 100));
      return this.acquire(); // retry
    }
  }
}

const stripeLimiter = new GlobalRateLimiter(redis, 'stripe-api', 90);

const worker = new Worker('stripe-jobs', async (job) => {
  await stripeLimiter.acquire(); // wait for rate limit slot
  return await stripe[job.data.method](job.data.params);
}, { connection, concurrency: 10 });
```

---

## Q17. (Advanced) How do you ensure exactly-once processing in distributed job systems?

**Answer**: True exactly-once is theoretically impossible in distributed systems. In practice, we achieve **effectively exactly-once** through idempotency.

```js
// Pattern: at-least-once delivery + idempotent processing = effectively exactly-once

// 1. BullMQ guarantees at-least-once delivery
// (job acknowledged only after worker function returns without error)

// 2. Idempotent processing with database constraint
async function processJob(job) {
  const { eventId, data } = job.data;

  try {
    await db.transaction(async (trx) => {
      // Insert into processed_events (unique constraint on event_id)
      await trx('processed_events').insert({ event_id: eventId, processed_at: new Date() });
      // If we get here, it's the first time processing this event
      await trx('orders').insert(data);
    });
  } catch (err) {
    if (err.code === '23505') { // unique_violation in PostgreSQL
      console.log(`Event ${eventId} already processed, skipping`);
      return; // idempotent — safe to skip
    }
    throw err; // real error — retry
  }
}
```

---

## Q18. (Advanced) How do you implement job scheduling for multi-tenant SaaS?

```js
// Each tenant can have their own scheduled jobs

// Tenant-aware job scheduling
async function scheduleTenantJob(tenantId, jobName, schedule, data) {
  const jobKey = `tenant:${tenantId}:${jobName}`;

  await queue.add(jobName, {
    tenantId,
    ...data,
  }, {
    repeat: {
      pattern: schedule,
      key: jobKey,
    },
    jobId: jobKey,
  });
}

// Worker: process with tenant context
const worker = new Worker('tenant-jobs', async (job) => {
  const { tenantId, ...data } = job.data;

  // Set tenant context for this job
  const tenantDb = getTenantDatabase(tenantId);
  const tenantConfig = await getTenantConfig(tenantId);

  // Process with tenant isolation
  switch (job.name) {
    case 'daily-report':
      return await generateReport(tenantDb, tenantConfig, data);
    case 'data-sync':
      return await syncExternalData(tenantDb, tenantConfig, data);
  }
}, { connection });

// API for tenants to manage their schedules
app.post('/api/schedules', auth, async (req, res) => {
  const { jobName, schedule, data } = req.body;
  await scheduleTenantJob(req.user.tenantId, jobName, schedule, data);
  res.json({ scheduled: true });
});
```

---

## Q19. (Advanced) How do you handle graceful shutdown of job workers?

```js
// Problem: server receives SIGTERM, worker is mid-job. If you exit immediately, job is lost.

const worker = new Worker('tasks', processTask, { connection, concurrency: 5 });

async function gracefulShutdown(signal) {
  console.log(`${signal} received. Shutting down worker gracefully...`);

  // 1. Stop accepting new jobs
  await worker.close();
  // BullMQ close() waits for current jobs to finish (with timeout)

  // 2. Close connections
  await connection.quit();

  console.log('Worker shutdown complete');
  process.exit(0);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// For very long-running jobs, implement checkpoints
const worker = new Worker('long-tasks', async (job) => {
  const { items, processedCount = 0 } = job.data;

  for (let i = processedCount; i < items.length; i++) {
    await processItem(items[i]);

    // Save progress every 100 items (checkpoint)
    if (i % 100 === 0) {
      await job.updateData({ ...job.data, processedCount: i });
      await job.updateProgress(Math.round((i / items.length) * 100));
    }
  }
}, { connection });
// If worker crashes, job retries from last checkpoint, not from beginning
```

---

## Q20. (Advanced) Senior red flags in background job systems.

**Answer**:

1. **No retry strategy** — transient failures permanently lose jobs
2. **No dead letter queue** — failed jobs disappear with no way to investigate or replay
3. **Non-idempotent jobs** — duplicate processing causes data corruption
4. **Synchronous processing in API requests** — emails, reports block user responses
5. **No monitoring** — queue grows to 100k jobs and nobody notices
6. **No concurrency limits** — workers overwhelm external APIs or databases
7. **Cron jobs on multiple instances** — same job runs N times without deduplication
8. **No graceful shutdown** — in-flight jobs lost on deploy
9. **No job timeout** — stuck jobs hold a worker slot forever
10. **Storing job results in Redis indefinitely** — Redis memory grows unbounded

```js
// RED FLAG: no timeout on job processing
const worker = new Worker('tasks', async (job) => {
  await longRunningTask(); // could hang forever, blocking this worker slot
});

// FIX: add timeout
const worker = new Worker('tasks', async (job) => {
  const result = await Promise.race([
    longRunningTask(),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Job timeout')), 300000)),
  ]);
  return result;
}, { connection, lockDuration: 300000 }); // lock matches timeout
```

**Senior interview answer**: "I use BullMQ with Redis for background jobs. Every job is idempotent (safe to process multiple times). I implement retry with exponential backoff, dead letter queues for permanent failures, job progress tracking for long tasks, and rate limiting for external API calls. Workers shut down gracefully on SIGTERM, completing in-flight jobs before exiting. I monitor queue depth, processing time, and failure rate via Prometheus dashboards."
