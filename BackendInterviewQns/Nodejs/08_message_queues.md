# 8. Message Queues & Async Processing

## Topic Introduction

Message queues **decouple producers from consumers**, enabling async processing, retry logic, and independent scaling. Instead of processing heavy work during an HTTP request, you push a message to a queue and a worker picks it up later.

```
                            Queue
Client → API ──publish──► [msg1|msg2|msg3] ──consume──► Worker(s)
         │                                                 │
         └── 202 Accepted                                  └── Process, retry, DLQ
```

Common queues: **Redis (BullMQ)** for simplicity, **RabbitMQ** for routing/priority, **Kafka** for high-throughput event streaming, **SQS** for serverless/AWS.

**Why this matters**: Every production backend eventually needs queues — for emails, notifications, report generation, webhooks, data pipelines, and any work that shouldn't block the user.

**Go/Java tradeoff**: Go uses channels internally and Kafka/NATS for distributed. Java has JMS, Spring AMQP, and Kafka Streams. Node.js excels here because BullMQ + Redis is extremely easy to set up, and the async nature of Node aligns perfectly with message-driven architectures.

---

## Q1. (Beginner) What is a message queue? Why use one instead of processing work synchronously?

**Scenario**: Your API sends welcome emails inline. When the email provider is slow (2s), every registration request takes 2s+.

```js
// BAD: synchronous — user waits for email to send
app.post('/register', async (req, res) => {
  const user = await createUser(req.body);
  await sendWelcomeEmail(user.email); // 2 seconds blocking!
  res.json(user); // user waited 2+ seconds
});

// GOOD: async with queue — user gets instant response
app.post('/register', async (req, res) => {
  const user = await createUser(req.body);
  await emailQueue.add('welcome', { email: user.email, name: user.name });
  res.status(201).json(user); // instant response (~50ms)
});

// Worker (separate process)
const worker = new Worker('emailQueue', async (job) => {
  await sendWelcomeEmail(job.data.email);
}, { connection: redisConnection });
```

**Answer**: Queues decouple the request from heavy/unreliable work. Benefits: faster responses, retry on failure, independent scaling (add more workers), and resilience (email provider down doesn't crash registration).

---

## Q2. (Beginner) What is BullMQ? Show a basic producer/consumer example.

```js
const { Queue, Worker } = require('bullmq');
const IORedis = require('ioredis');

const connection = new IORedis({ host: 'localhost', port: 6379 });

// Producer (in API)
const queue = new Queue('notifications', { connection });
await queue.add('send-push', {
  userId: 123,
  title: 'Order shipped',
  body: 'Your order #456 has been shipped',
});

// Consumer (separate process)
const worker = new Worker('notifications', async (job) => {
  console.log(`Processing job ${job.id}: ${job.name}`);
  await sendPushNotification(job.data.userId, job.data.title, job.data.body);
}, {
  connection,
  concurrency: 5, // process 5 jobs simultaneously
});

worker.on('completed', (job) => console.log(`Job ${job.id} completed`));
worker.on('failed', (job, err) => console.error(`Job ${job.id} failed:`, err));
```

**Answer**: BullMQ is a Node.js queue library backed by Redis. It provides: job prioritization, retries with backoff, delayed jobs, rate limiting, job progress tracking, and dead-letter queues. It's the go-to choice for Node.js teams that already use Redis.

---

## Q3. (Beginner) What is at-least-once vs at-most-once vs exactly-once delivery?

**Answer**:

| Guarantee | Behavior | Risk | Use case |
|-----------|----------|------|----------|
| **At-most-once** | Fire and forget | Messages may be lost | Logging, analytics |
| **At-least-once** | Retry until acknowledged | Duplicates possible | Notifications, email |
| **Exactly-once** | Process exactly once | Hardest to implement | Payments (in theory) |

```js
// At-least-once with BullMQ (default)
// If worker crashes mid-processing, job is returned to queue and retried
const worker = new Worker('payments', async (job) => {
  await processPayment(job.data); // if this crashes, BullMQ retries
}, {
  connection,
  settings: { backoffStrategy: 'exponential' },
});

// Effectively exactly-once = at-least-once + idempotent consumer
const worker = new Worker('payments', async (job) => {
  const processed = await redis.get(`processed:${job.data.orderId}`);
  if (processed) return; // idempotent — skip duplicate
  await processPayment(job.data);
  await redis.set(`processed:${job.data.orderId}`, '1', 'EX', 86400);
});
```

---

## Q4. (Beginner) What is a dead-letter queue (DLQ)? Why do you need one?

**Scenario**: A job keeps failing (e.g., malformed data). After 3 retries, it should stop retrying and be investigated.

```js
// BullMQ: failed jobs go to a separate "failed" state
const queue = new Queue('orders', { connection });
await queue.add('process', { orderId: 123 }, {
  attempts: 3,                    // retry 3 times
  backoff: { type: 'exponential', delay: 1000 }, // 1s, 2s, 4s
  removeOnFail: false,           // keep failed jobs for inspection
});

// Monitor failed jobs
const failed = await queue.getFailed(0, 100);
for (const job of failed) {
  console.log(`Failed job ${job.id}:`, job.failedReason);
  // Option 1: Move to DLQ
  await dlqQueue.add('investigate', { originalJob: job.data, error: job.failedReason });
  await job.remove();
  // Option 2: Alert the team
}
```

**Answer**: A DLQ holds messages that couldn't be processed after all retries. Without it, poison messages (corrupted data, bugs) would retry forever, wasting resources. DLQs let you: investigate failures, replay messages after fixing bugs, and alert on processing issues.

---

## Q5. (Beginner) When should you use Redis-based queues (BullMQ) vs Kafka vs RabbitMQ vs SQS?

**Answer**:

| Queue | Best for | Scale | Ordering | Node.js support |
|-------|----------|-------|----------|----------------|
| **BullMQ (Redis)** | Simple background jobs, small-medium teams | Medium | Per-queue | Excellent (native) |
| **RabbitMQ** | Complex routing, priority, RPC | Medium-high | Per-queue | Good (amqplib) |
| **Kafka** | High-throughput event streaming, log | Very high (millions/sec) | Per-partition | Good (kafkajs) |
| **SQS** | AWS serverless, zero-ops | High | Best-effort / FIFO | Good (aws-sdk) |

**Decision framework**:
- **Startup**: BullMQ (already using Redis, simple setup)
- **Growing company**: RabbitMQ or SQS (more features, managed options)
- **High-throughput data**: Kafka (event sourcing, stream processing)

---

## Q6. (Intermediate) How do you implement job retry with exponential backoff?

```js
// BullMQ retry configuration
await queue.add('send-webhook', webhookData, {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 1000, // 1s → 2s → 4s → 8s → 16s
  },
});

// Custom backoff strategy
await queue.add('charge', paymentData, {
  attempts: 3,
  backoff: {
    type: 'custom',
  },
});

// In worker, define custom backoff
const worker = new Worker('payments', async (job) => {
  try {
    await processPayment(job.data);
  } catch (err) {
    if (err.code === 'RATE_LIMITED') {
      // Retry after the specified wait time
      throw new DelayedError(err.retryAfter * 1000);
    }
    throw err; // other errors use default backoff
  }
}, { connection });
```

**Answer**: Exponential backoff prevents overwhelming a failing downstream service. Each retry waits longer: 1s, 2s, 4s, 8s... Add **jitter** (random delay) to prevent all retrying jobs from hitting the service simultaneously.

---

## Q7. (Intermediate) How do you implement delayed jobs and scheduled tasks with BullMQ?

```js
// Delayed job — runs 10 minutes from now
await queue.add('send-reminder', { userId: 123, type: 'cart-abandoned' }, {
  delay: 10 * 60 * 1000, // 10 minutes
});

// Recurring job — runs every hour
await queue.add('cleanup', { type: 'expired-sessions' }, {
  repeat: { every: 3600000 }, // every hour
});

// Cron-style scheduling
await queue.add('daily-report', {}, {
  repeat: { cron: '0 9 * * 1-5' }, // 9 AM every weekday
});

// Scheduled for specific time
const scheduledTime = new Date('2024-12-25T00:00:00Z');
await queue.add('christmas-promo', { discount: 25 }, {
  delay: scheduledTime.getTime() - Date.now(),
});
```

**Answer**: BullMQ supports delayed jobs (run after N ms), repeatable jobs (cron or interval), and priority jobs. This eliminates the need for external cron schedulers for most use cases.

---

## Q8. (Intermediate) How do you handle job progress tracking and notify the client?

**Scenario**: A report generation takes 2 minutes. The client needs progress updates.

```js
// API: Create job and return job ID
app.post('/reports', async (req, res) => {
  const job = await reportQueue.add('generate', req.body);
  res.status(202).json({ jobId: job.id, statusUrl: `/reports/status/${job.id}` });
});

// Worker: report progress
const worker = new Worker('reports', async (job) => {
  const data = await fetchData(job.data);
  await job.updateProgress(25);

  const processed = await transformData(data);
  await job.updateProgress(50);

  const pdf = await generatePDF(processed);
  await job.updateProgress(75);

  const url = await uploadToS3(pdf);
  await job.updateProgress(100);
  return { url };
});

// API: Check status
app.get('/reports/status/:jobId', async (req, res) => {
  const job = await reportQueue.getJob(req.params.jobId);
  if (!job) return res.status(404).json({ error: 'Job not found' });

  const state = await job.getState(); // waiting, active, completed, failed
  res.json({
    state,
    progress: job.progress,
    result: state === 'completed' ? job.returnvalue : undefined,
    error: state === 'failed' ? job.failedReason : undefined,
  });
});
```

**Answer**: Return a job ID with the initial request (202 Accepted). Workers update progress as they work. Client polls a status endpoint or receives updates via WebSocket/SSE.

---

## Q9. (Intermediate) How do you implement priority queues?

```js
// BullMQ priority (lower number = higher priority)
await queue.add('urgent-alert', alertData, { priority: 1 });
await queue.add('normal-email', emailData, { priority: 5 });
await queue.add('bulk-export', exportData, { priority: 10 });

// Workers process highest priority first
// If there are 3 urgent-alerts and 100 bulk-exports,
// all urgent-alerts process before any bulk-export
```

**Answer**: Priority queues ensure critical jobs (alerts, payments) run before lower-priority ones (reports, cleanup). BullMQ uses Redis sorted sets with priority as the score. In Kafka, you'd use separate topics for priority levels.

---

## Q10. (Intermediate) How do you scale queue workers independently from the API?

**Scenario**: 100k emails/day queued. API handles 1000 req/s. Email workers are slow.

```
API (3 pods) → Redis Queue → Email Workers (10 pods, auto-scaled)
                             Report Workers (2 pods)
                             Webhook Workers (5 pods)
```

```js
// Worker process (deployed separately from API)
// worker.js
const { Worker } = require('bullmq');

const concurrency = parseInt(process.env.WORKER_CONCURRENCY || '10');

const worker = new Worker('emails', async (job) => {
  await sendEmail(job.data);
}, {
  connection: redis,
  concurrency, // process 10 jobs simultaneously per pod
  limiter: { max: 50, duration: 1000 }, // global: 50 emails/sec (API limit)
});

// Kubernetes HPA can scale workers based on queue depth
// Custom metric: bullmq_waiting_count{queue="emails"}
```

**Answer**: Workers are separate processes/containers. Scale them based on queue depth (jobs waiting). Use `concurrency` to control how many jobs each worker processes simultaneously. Use `limiter` to respect external rate limits (e.g., email provider's send rate).

---

## Q11. (Intermediate) How do you implement saga-style workflows with queues?

```js
// Order saga: create order → charge payment → reserve inventory → send confirmation
const orderSaga = {
  steps: [
    { name: 'create-order', queue: orderQueue, compensate: 'cancel-order' },
    { name: 'charge-payment', queue: paymentQueue, compensate: 'refund-payment' },
    { name: 'reserve-inventory', queue: inventoryQueue, compensate: 'release-inventory' },
    { name: 'send-confirmation', queue: emailQueue }, // no compensating action needed
  ],
};

// Orchestrator worker
async function executeSaga(sagaDef, data) {
  const completed = [];

  for (const step of sagaDef.steps) {
    try {
      const job = await step.queue.add(step.name, data);
      const result = await job.waitUntilFinished(queueEvents);
      completed.push({ step: step.name, result });
      data = { ...data, ...result }; // pass results to next step
    } catch (err) {
      // Compensate in reverse order
      for (const done of completed.reverse()) {
        const compensateStep = sagaDef.steps.find(s => s.name === done.step);
        if (compensateStep?.compensate) {
          await compensateStep.queue.add(compensateStep.compensate, data);
        }
      }
      throw err;
    }
  }
  return data;
}
```

**Answer**: A saga orchestrator executes steps sequentially. If any step fails, it runs compensating actions for all completed steps in reverse order. Each step and compensation must be idempotent.

---

## Q12. (Intermediate) How does Kafka differ from BullMQ? When would you choose Kafka?

**Answer**:

| | **BullMQ (Redis)** | **Kafka** |
|---|---|---|
| Model | Job queue (consume & delete) | Event log (consume & retain) |
| Throughput | ~10k msg/sec | Millions msg/sec |
| Retention | Until processed | Configurable (days/weeks/forever) |
| Consumer groups | Single consumer per job | Multiple consumer groups (each sees all messages) |
| Replay | Not possible (consumed = gone) | Replay by resetting offset |
| Use case | Background jobs, tasks | Event streaming, data pipelines, event sourcing |

**Choose Kafka when**: Multiple consumers need the same events, event replay/audit trail is needed, throughput > 100k msg/sec, or you're doing event-driven architecture.

```js
// Kafka with kafkajs
const { Kafka } = require('kafkajs');
const kafka = new Kafka({ brokers: ['localhost:9092'] });
const producer = kafka.producer();
const consumer = kafka.consumer({ groupId: 'order-service' });

// Produce event
await producer.send({
  topic: 'orders',
  messages: [{ key: orderId, value: JSON.stringify(orderData) }],
});

// Consume events (each consumer group gets every message)
await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const order = JSON.parse(message.value.toString());
    await processOrder(order);
  },
});
```

---

## Q13. (Advanced) Production scenario: Queue has 500k jobs backed up. Workers can't keep up. How do you handle it?

**Answer**:

```js
// Step 1: Monitor queue depth
const waiting = await queue.getWaitingCount();
const active = await queue.getActiveCount();
console.log(`Queue: ${waiting} waiting, ${active} active`);
// Alert if waiting > threshold

// Step 2: Scale workers horizontally
// K8s HPA based on queue depth metric
// kubectl scale deployment email-workers --replicas=20

// Step 3: Increase concurrency per worker
const worker = new Worker('emails', handler, {
  concurrency: 20, // was 5, increase to 20
});

// Step 4: Prioritize — process critical jobs first
// If backlog is mixed priority, ensure high-priority jobs aren't starved

// Step 5: Temporary rate limit producers
// If backlog is growing faster than drain rate, slow down the API
app.use(async (req, res, next) => {
  const depth = await queue.getWaitingCount();
  if (depth > 100000) {
    return res.status(503).json({ error: 'System busy, try later', retryAfter: 60 });
  }
  next();
});

// Step 6: Batch processing (if applicable)
const worker = new Worker('emails', async (job) => {
  // Process in batches of 100 instead of 1
  const batch = await queue.getJobs(['waiting'], 0, 99);
  await sendEmailBatch(batch.map(j => j.data));
  // Mark all as completed
});
```

---

## Q14. (Advanced) How do you ensure exactly-once processing with Kafka in Node.js?

```js
// Kafka transactional producer + consumer (exactly-once semantics)
const producer = kafka.producer({
  transactionalId: 'order-processor',
  maxInFlightRequests: 1,
  idempotent: true,
});

const consumer = kafka.consumer({
  groupId: 'order-service',
  readUncommitted: false, // only read committed messages
});

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const transaction = await producer.transaction();
    try {
      // Process the message
      const result = processOrder(JSON.parse(message.value));

      // Produce output message AND commit offset in same transaction
      await transaction.send({
        topic: 'order-events',
        messages: [{ value: JSON.stringify(result) }],
      });
      await transaction.sendOffsets({
        consumerGroupId: 'order-service',
        topics: [{ topic, partitions: [{ partition, offset: (Number(message.offset) + 1).toString() }] }],
      });

      await transaction.commit();
    } catch (err) {
      await transaction.abort();
      throw err;
    }
  },
});
```

**Answer**: Kafka's exactly-once semantics works by wrapping the message processing, output production, and offset commit in a **single transaction**. If any part fails, the entire transaction aborts. This only works within Kafka (produce → consume → produce). For external side effects (DB writes), you still need idempotent consumers.

---

## Q15. (Advanced) How do you implement a fan-out pattern (one event → multiple consumers)?

```js
// Pattern 1: Kafka topics — multiple consumer groups
// Each consumer group independently processes ALL messages
// Consumer group "email-service" → sends email
// Consumer group "analytics-service" → records metrics
// Consumer group "inventory-service" → updates stock

// Pattern 2: Redis pub/sub + BullMQ
// Publish event → multiple queues subscribe
const eventBus = new Redis();

async function publishEvent(event) {
  await eventBus.publish('order-events', JSON.stringify(event));
}

// Each service subscribes and adds to its own queue
const subscriber = new Redis();
subscriber.subscribe('order-events');
subscriber.on('message', async (channel, message) => {
  const event = JSON.parse(message);
  switch (event.type) {
    case 'order.created':
      await emailQueue.add('order-confirmation', event.data);
      await analyticsQueue.add('track-order', event.data);
      await inventoryQueue.add('reserve-stock', event.data);
      break;
  }
});
```

**Answer**: Fan-out distributes one event to multiple independent consumers. Kafka does this natively with consumer groups. With Redis, use pub/sub to fan out to separate BullMQ queues. Each consumer is independent — failure of one doesn't affect others.

---

## Q16. (Advanced) How do you handle poison messages (messages that always fail)?

```js
const worker = new Worker('orders', async (job) => {
  // Track attempt number
  const attemptsMade = job.attemptsMade;

  if (attemptsMade >= 3) {
    // Last attempt — extra logging and DLQ
    console.error(`Poison message detected: job ${job.id}`, job.data);
    await dlqQueue.add('investigate', {
      originalQueue: 'orders',
      jobId: job.id,
      data: job.data,
      failedReason: job.failedReason,
      attempts: attemptsMade,
    });
    await alertTeam(`Poison message in orders queue: ${job.id}`);
    return; // don't throw — mark as completed to stop retries
  }

  await processOrder(job.data); // may throw
}, {
  connection,
  settings: {
    maxStalledCount: 2, // move to failed if stalled 2 times
  },
});
```

**Answer**: Poison messages are messages that can never be processed successfully (corrupted data, schema mismatch, bug). Set a **max retry limit**, move to DLQ after exhaustion, and alert the team. The key is to prevent poison messages from blocking the queue while preserving them for investigation.

---

## Q17. (Advanced) How does message queue usage differ between Go and Node.js?

**Answer**:

```go
// Go with Kafka — blocking consumer (goroutine)
reader := kafka.NewReader(kafka.ReaderConfig{
    Brokers: []string{"localhost:9092"},
    Topic:   "orders",
    GroupID: "order-service",
})
for {
    msg, _ := reader.ReadMessage(context.Background()) // blocks goroutine (cheap)
    processOrder(msg.Value)
}
// Go advantage: blocking read is natural, goroutine is cheap
```

```js
// Node.js with Kafka — event-driven consumer
await consumer.run({
  eachMessage: async ({ message }) => {
    await processOrder(message.value); // non-blocking, event loop friendly
  },
});
// Node advantage: natural fit for event-driven processing
```

**Key difference**: Go blocks a goroutine per consumer (cheap, simple). Node uses callbacks/async (no blocking, but complex error handling). For CPU-heavy message processing, Go wins. For I/O-heavy processing (DB writes, HTTP calls), Node is equally good.

---

## Q18. (Advanced) How do you implement ordered processing with parallel workers?

**Scenario**: Orders for the same customer must process in order, but different customers can process in parallel.

```js
// Kafka: partition by customer ID
await producer.send({
  topic: 'orders',
  messages: [{
    key: customerId.toString(), // same customer → same partition → same consumer
    value: JSON.stringify(order),
  }],
});
// Each partition is consumed by ONE consumer in the group → ordered per customer

// BullMQ: use job groups (concurrency per group)
await queue.add('process-order', orderData, {
  group: { id: customerId.toString() }, // BullMQ Pro feature
  // Jobs in the same group are processed sequentially
  // Different groups process in parallel
});
```

**Answer**: In Kafka, partition by the ordering key. All messages with the same key go to the same partition, which is consumed by one consumer. In BullMQ, use named job groups. This gives you per-customer ordering with parallel processing across customers.

---

## Q19. (Advanced) How do you monitor and alert on queue health in production?

```js
// BullMQ metrics exposed to Prometheus
const metrics = {
  waiting: new Gauge({ name: 'bullmq_waiting', help: 'Jobs waiting', labelNames: ['queue'] }),
  active: new Gauge({ name: 'bullmq_active', help: 'Jobs active', labelNames: ['queue'] }),
  completed: new Counter({ name: 'bullmq_completed_total', help: 'Jobs completed', labelNames: ['queue'] }),
  failed: new Counter({ name: 'bullmq_failed_total', help: 'Jobs failed', labelNames: ['queue'] }),
  duration: new Histogram({ name: 'bullmq_duration_seconds', help: 'Job duration', labelNames: ['queue'] }),
};

// Collect metrics periodically
setInterval(async () => {
  for (const queueName of ['emails', 'orders', 'reports']) {
    const q = new Queue(queueName, { connection });
    metrics.waiting.set({ queue: queueName }, await q.getWaitingCount());
    metrics.active.set({ queue: queueName }, await q.getActiveCount());
  }
}, 10000);

// Alert rules (in Prometheus/Grafana):
// bullmq_waiting{queue="orders"} > 10000 for 5m → "Order queue backing up"
// rate(bullmq_failed_total[5m]) > 10 → "High failure rate"
// bullmq_duration_seconds_p99 > 30 → "Slow job processing"
```

---

## Q20. (Advanced) Senior red flags in queue usage code reviews.

**Answer**:

1. **Processing heavy work in the HTTP handler** instead of queueing it
2. **No retry configuration** — jobs fail once and are lost
3. **No dead-letter queue** — failed jobs disappear or retry forever
4. **No idempotent consumers** — retries cause duplicate side effects
5. **Queue as database** — storing important state only in the queue (not durable)
6. **No backpressure** — producer adds faster than consumers drain, queue grows unbounded
7. **No monitoring** — can't see queue depth, failure rate, or processing time
8. **Blocking the event loop in worker** — defeats the purpose of async processing
9. **Single consumer for critical queues** — no redundancy, single point of failure
10. **No graceful shutdown** — worker killed mid-job, job stuck in "active" state

**Senior interview answer**: "I use queues for any work that doesn't need to block the user response. I ensure at-least-once delivery with idempotent consumers for effective exactly-once semantics, implement dead-letter queues for poison messages, scale workers based on queue depth, and monitor throughput and failure rates."
