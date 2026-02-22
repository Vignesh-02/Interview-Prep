# 3. Scaling Node.js — Cluster, Worker Threads & Horizontal Scale

## Topic Introduction

Node.js runs JavaScript on a **single thread**. To use all CPU cores and handle traffic growth, you need scaling strategies: **cluster mode** (multiple processes), **worker threads** (CPU parallelism within a process), and **horizontal scaling** (multiple machines behind a load balancer).

```
                           Load Balancer
                          /      |      \
                     Node P1   Node P2   Node P3   (cluster or containers)
                      │          │          │
                   Event Loop  Event Loop  Event Loop
                      │
                   Worker Thread Pool (for CPU tasks)
```

**Key insight**: I/O scales on a single event loop (10k+ concurrent connections). CPU work does NOT — it blocks the loop. The skill is knowing when to reach for each scaling tool.

**Go/Java tradeoff**: Go's goroutines give you M:N parallelism out of the box — one process uses all cores. Java has native threads. Node requires explicit use of `cluster` or `worker_threads` for multi-core utilization.

---

## Q1. (Beginner) Why is Node.js single-threaded, and how does it still handle thousands of concurrent connections?

**Scenario**: Your Node.js API serves 5,000 concurrent users but only uses one CPU core.

**Answer**: Node uses **one thread for JavaScript** but delegates I/O to the OS (via epoll/kqueue) and libuv's thread pool. Each connection is just a file descriptor + callback — no thread or stack per connection.

```js
// This server can handle 10k+ concurrent connections on ONE thread
const http = require('http');
http.createServer((req, res) => {
  // Each request = callback, NOT a thread
  db.query('SELECT ...').then(data => res.end(JSON.stringify(data)));
}).listen(3000);
```

Memory per connection: ~10-50KB (vs ~1MB per thread in Java's traditional model). This is why Node excels at I/O-heavy workloads like APIs, real-time apps, and proxies.

---

## Q2. (Beginner) What is the `cluster` module? How does it help?

**Scenario**: Your server has 8 CPU cores but Node only uses 1.

```js
const cluster = require('cluster');
const os = require('os');

if (cluster.isPrimary) {
  const cpus = os.cpus().length;
  console.log(`Primary ${process.pid}: forking ${cpus} workers`);
  for (let i = 0; i < cpus; i++) cluster.fork();

  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} died, restarting`);
    cluster.fork(); // auto-restart
  });
} else {
  const http = require('http');
  http.createServer((req, res) => {
    res.end(`Hello from worker ${process.pid}`);
  }).listen(3000);
}
```

**Answer**: `cluster` forks multiple Node.js **processes** that share the same port. The OS distributes connections across workers (round-robin on Linux). Each worker has its own event loop and memory space. If one crashes, others continue serving.

---

## Q3. (Beginner) What are Worker Threads? How are they different from cluster?

**Answer**:

| | **Cluster** | **Worker Threads** |
|---|---|---|
| Creates | Separate **processes** | Threads within **same process** |
| Memory | Isolated (separate heap) | Shared (SharedArrayBuffer, MessageChannel) |
| Use case | Scale HTTP server across cores | Offload CPU work from event loop |
| Communication | IPC messages | `postMessage` / shared memory |
| Crash isolation | One worker crash doesn't kill others | Thread crash can crash the process |

```js
// Worker Thread — offload CPU-heavy work
const { Worker, isMainThread, workerData, parentPort } = require('worker_threads');

if (isMainThread) {
  const worker = new Worker(__filename, { workerData: { n: 40 } });
  worker.on('message', (result) => console.log('Fibonacci:', result));
} else {
  function fib(n) { return n <= 1 ? n : fib(n - 1) + fib(n - 2); }
  parentPort.postMessage(fib(workerData.n));
}
```

**Rule of thumb**: Cluster for **scaling HTTP servers**. Worker threads for **CPU-heavy tasks** within a request.

---

## Q4. (Beginner) What is PM2 and why do teams use it?

**Scenario**: You need to run your Node.js app in production with auto-restart and cluster mode.

```bash
# Start with cluster mode (uses all cores)
pm2 start app.js -i max

# Monitor
pm2 monit

# Zero-downtime reload
pm2 reload app.js
```

**Answer**: PM2 is a **process manager** that provides:
- **Cluster mode** without writing cluster code
- **Auto-restart** on crash
- **Zero-downtime reload** (graceful restart)
- **Log management** and **monitoring**
- **Startup scripts** (survive server reboot)

**Alternative**: In containerized environments (K8s), you typically run **one process per container** and let the orchestrator handle scaling and restarts. PM2 is most useful on bare VMs.

---

## Q5. (Beginner) How do you decide between vertical scaling and horizontal scaling for a Node.js app?

**Answer**:

| Strategy | What | When |
|----------|------|------|
| **Vertical** | Bigger machine (more RAM, CPU) | Quick win; single-process bottleneck |
| **Horizontal** | More machines behind load balancer | True scale; fault tolerance |

```
Vertical:  1 machine × 64 cores (cluster mode)
Horizontal: 10 machines × 8 cores (load balanced)
```

**Node.js specifics**:
- Vertical: Use `cluster` or PM2 to use all cores on one machine
- Horizontal: Stateless app + load balancer + shared state (Redis/DB)

**Key requirement for horizontal**: Your app must be **stateless** — no in-memory sessions, no local file state. Use Redis for sessions, S3 for files, DB for data.

---

## Q6. (Intermediate) How do you implement a worker thread pool for CPU-intensive tasks?

**Scenario**: Your API generates PDF reports. Each takes 2 seconds of CPU. You get 50 requests/minute.

```js
// worker-pool.js
const { Worker } = require('worker_threads');
const os = require('os');

class WorkerPool {
  constructor(workerFile, poolSize = os.cpus().length) {
    this.workers = [];
    this.queue = [];
    for (let i = 0; i < poolSize; i++) {
      this.workers.push({ worker: new Worker(workerFile), busy: false });
    }
  }

  run(data) {
    return new Promise((resolve, reject) => {
      const available = this.workers.find(w => !w.busy);
      if (available) {
        this._execute(available, data, resolve, reject);
      } else {
        this.queue.push({ data, resolve, reject });
      }
    });
  }

  _execute(entry, data, resolve, reject) {
    entry.busy = true;
    entry.worker.postMessage(data);
    entry.worker.once('message', (result) => {
      entry.busy = false;
      resolve(result);
      if (this.queue.length > 0) {
        const next = this.queue.shift();
        this._execute(entry, next.data, next.resolve, next.reject);
      }
    });
    entry.worker.once('error', (err) => {
      entry.busy = false;
      reject(err);
    });
  }
}

// Usage
const pool = new WorkerPool('./pdf-worker.js', 4);
app.post('/reports', async (req, res) => {
  const pdf = await pool.run(req.body); // doesn't block event loop
  res.send(pdf);
});
```

**Answer**: A worker pool pre-creates N workers and queues tasks. This avoids the overhead of spawning workers per request and caps CPU usage. Libraries like `workerpool` or `piscina` provide battle-tested implementations.

**Tradeoff with Go**: Go doesn't need this — goroutines are cheap. Just `go generatePDF(data)`.

---

## Q7. (Intermediate) How does `cluster` module share a port? What's the OS-level mechanism?

**Answer**: The primary process creates a server socket and **passes the file descriptor** to worker processes via IPC. Workers accept connections on the shared socket.

On Linux, the OS uses **round-robin** distribution (since Node v0.12). On other OSes, the primary may accept and distribute connections.

```
Primary Process
  └── Listen on port 3000 (creates socket FD)
      ├── Worker 1 (receives FD, accepts connections)
      ├── Worker 2 (receives FD, accepts connections)
      └── Worker 3 (receives FD, accepts connections)
```

**Gotcha**: Workers don't share memory. If you cache data in-process, each worker has its own cache (wasted memory, inconsistent state). Use Redis for shared state.

---

## Q8. (Intermediate) How do you implement zero-downtime restarts (graceful reload)?

**Scenario**: You need to deploy a new version without dropping any in-flight requests.

```js
// Graceful shutdown in each worker
process.on('SIGTERM', () => {
  console.log('Worker received SIGTERM, finishing current requests...');

  server.close(() => {
    // All connections drained
    console.log('All connections closed, exiting');
    process.exit(0);
  });

  // Force exit after 30s if connections don't close
  setTimeout(() => {
    console.error('Forcing exit after timeout');
    process.exit(1);
  }, 30000);
});
```

**Rolling restart with cluster**:
```js
// Primary process
function rollingRestart() {
  const workers = Object.values(cluster.workers);
  let i = 0;

  function restartNext() {
    if (i >= workers.length) return;
    const worker = workers[i++];
    const replacement = cluster.fork();
    replacement.on('listening', () => {
      worker.kill('SIGTERM'); // old worker drains and exits
      restartNext();
    });
  }
  restartNext();
}
```

**Answer**: Restart workers one at a time. Fork a new worker, wait for it to be ready (`listening`), then send SIGTERM to the old worker. The old worker stops accepting new connections, drains existing ones, and exits.

---

## Q9. (Intermediate) When should you use Worker Threads vs a separate microservice for CPU work?

**Scenario**: Your app needs image resizing. Should you use worker threads or a separate service?

**Answer**:

| Factor | **Worker Threads** | **Separate Service** |
|--------|-------------------|---------------------|
| Latency | Lower (no network hop) | Higher (HTTP/gRPC call) |
| Scaling | Limited to host cores | Independent horizontal scaling |
| Fault isolation | Thread crash may affect process | Complete isolation |
| Deployment | Same codebase | Independent deploy/scale |
| Complexity | Lower | Higher (network, discovery) |

**Decision framework**:
- **Worker threads**: Task is quick (<5s), needs low latency, moderate volume
- **Separate service**: Task is long-running, needs independent scaling, high volume, or different language (Go/Rust for CPU work)
- **Queue + worker**: Task is async (user doesn't wait), needs retries, high reliability

```js
// Small startup: worker threads
const pool = new Piscina({ filename: './resize.js' });
const result = await pool.run({ image: buffer, width: 200 });

// Scaling up: queue + separate worker service
await imageQueue.add('resize', { imageUrl, width: 200 });
// Worker service (could be in Go for better CPU perf):
// imageQueue.process('resize', handler);
```

---

## Q10. (Intermediate) How do you share data between worker threads safely?

```js
const { Worker, isMainThread } = require('worker_threads');

if (isMainThread) {
  // SharedArrayBuffer — shared memory between threads
  const shared = new SharedArrayBuffer(4);
  const view = new Int32Array(shared);

  const w1 = new Worker(__filename, { workerData: { shared } });
  const w2 = new Worker(__filename, { workerData: { shared } });

  setTimeout(() => console.log('Counter:', Atomics.load(view, 0)), 2000);
} else {
  const { shared } = require('worker_threads').workerData;
  const view = new Int32Array(shared);

  for (let i = 0; i < 1000; i++) {
    Atomics.add(view, 0, 1); // atomic increment — thread-safe
  }
}
```

**Answer**: Worker threads communicate via:
1. **`postMessage`** — copies data (safe but slow for large data)
2. **`SharedArrayBuffer`** — zero-copy shared memory (fast but requires `Atomics` for thread safety)
3. **`MessageChannel`** — direct thread-to-thread communication

**Rule**: Use `postMessage` for small data. Use `SharedArrayBuffer` + `Atomics` for large arrays or high-frequency updates (e.g., metrics counters).

---

## Q11. (Intermediate) How does Node.js compare to Go for scaling concurrent workloads?

**Answer**:

| Aspect | **Node.js** | **Go** |
|--------|-------------|--------|
| Concurrency model | Single-threaded event loop | Goroutines (M:N scheduling) |
| CPU parallelism | Cluster + worker threads | Built-in (GOMAXPROCS) |
| Memory per connection | ~10-50KB | ~4KB (goroutine stack) |
| Scaling HTTP | Cluster mode or containers | Single process, all cores |
| CPU-bound work | Must offload explicitly | Just runs on goroutines |
| Ecosystem | Massive (npm) | Growing, strong stdlib |
| Developer speed | Very fast (JS/TS) | Fast (simple language) |

**When Node wins**: I/O-heavy APIs, real-time apps, rapid prototyping, JS/TS team
**When Go wins**: CPU-heavy services, systems programming, need single binary deploys

**Senior answer**: "I'd use Node for the API layer and BFF, and Go for CPU-intensive microservices like image processing or data pipelines."

---

## Q12. (Intermediate) How do you detect if your Node.js app needs more workers or horizontal scaling?

**Answer**: Monitor these metrics:

```js
// 1. Event loop delay — if high, CPU is saturated per-process
const { monitorEventLoopDelay } = require('perf_hooks');

// 2. CPU utilization per worker — should be <70% for headroom
// 3. Memory usage — approaching --max-old-space-size limit
// 4. Request queue depth — growing = not enough capacity
// 5. p99 latency — increasing under stable traffic = saturation
```

**Decision matrix**:
| Symptom | Solution |
|---------|----------|
| High event loop lag, CPU at 100% on one core | Add cluster workers |
| All workers at 100% CPU | Horizontal scale (more machines) |
| Memory growing, low CPU | Memory leak or need more RAM |
| DB queries slow | DB scaling, not app scaling |
| p99 high but CPU/memory fine | External dependency bottleneck |

---

## Q13. (Advanced) Design a scaling strategy for a Node.js API that handles 100k requests/second.

**Scenario**: E-commerce checkout API. 100k req/s peak. Each request does: auth check, read product from cache, write order to DB.

**Answer**:

```
                    CDN / Edge (static + cache)
                            │
                    API Gateway (rate limit, auth)
                            │
                    Load Balancer (Layer 7)
                    /       |       \
              K8s Pod 1  Pod 2   Pod N  (autoscale 10-50 pods)
              (Node.js, single process per container)
                    │
              ┌─────┼─────────┐
              │     │         │
            Redis  PostgreSQL  Kafka
            (cache) (orders)  (events)
```

**Key decisions**:
1. **One Node.js process per container** (not cluster) — let K8s handle scaling
2. **Stateless** — sessions in Redis, files in S3
3. **Connection pooling** — 20 DB connections per pod × 50 pods = 1000 connections to DB
4. **Cache-first** — product reads from Redis (sub-ms), not DB
5. **Async writes** — order events to Kafka, processed by separate workers
6. **Autoscale** on CPU and request latency metrics

```js
// Connection pool config per pod
const pool = new Pool({ max: 20, idleTimeoutMillis: 30000 });
const redis = new Redis({ maxRetriesPerRequest: 3 });

app.post('/checkout', async (req, res) => {
  const product = await redis.get(`product:${req.body.productId}`); // cache
  const order = await db.query('INSERT INTO orders ...', [...]); // DB
  await kafka.send({ topic: 'orders', messages: [{ value: JSON.stringify(order) }] });
  res.json({ orderId: order.id });
});
```

**Tradeoff with Java**: Java Spring Boot with virtual threads (Loom) could handle this with fewer pods (better CPU utilization per pod). But Node's lower memory footprint means you can run more pods per node, and the JS ecosystem provides faster iteration.

---

## Q14. (Advanced) How do you handle sticky sessions with horizontal scaling?

**Scenario**: Your app uses WebSockets. Load balancer sends a reconnect to a different server — state is lost.

**Answer**: **Sticky sessions** route a client to the same server for the duration of their session.

**Options**:
1. **Load balancer sticky** (by cookie or IP hash):
```nginx
# nginx
upstream backend {
    ip_hash;
    server node1:3000;
    server node2:3000;
}
```

2. **Avoid stickiness** — externalize state:
```js
// Store WebSocket state in Redis instead of in-memory
const redis = new Redis();

wss.on('connection', async (ws, req) => {
  const userId = authenticate(req);
  await redis.set(`ws:${userId}`, serverInstanceId);

  ws.on('message', async (msg) => {
    // State is in Redis, not in-memory
    const state = await redis.hgetall(`user:${userId}:state`);
    // Process...
  });
});
```

3. **Redis Pub/Sub for cross-server broadcasting**:
```js
// Server A receives message for user on Server B
const sub = new Redis();
sub.subscribe('messages');
sub.on('message', (channel, msg) => {
  const { userId, data } = JSON.parse(msg);
  const localWs = localConnections.get(userId);
  if (localWs) localWs.send(data);
});
```

**Best practice**: Avoid sticky sessions when possible. Externalize ALL state. This gives you true horizontal scaling with no routing constraints.

---

## Q15. (Advanced) How do you implement graceful shutdown that handles in-flight requests, WebSocket connections, and background jobs?

```js
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

async function gracefulShutdown(signal) {
  console.log(`Received ${signal}, shutting down gracefully...`);

  // 1. Stop accepting new connections
  server.close();

  // 2. Close WebSocket connections with a close frame
  wss.clients.forEach(ws => {
    ws.close(1001, 'Server shutting down');
  });

  // 3. Wait for in-flight HTTP requests (server.close callback)
  await new Promise(resolve => server.on('close', resolve));

  // 4. Drain background job queues
  await worker.close(); // BullMQ worker drains current job

  // 5. Close database connections
  await pool.end();
  await redis.quit();

  console.log('Shutdown complete');
  process.exit(0);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Force exit after 30s
setTimeout(() => {
  console.error('Forced exit after timeout');
  process.exit(1);
}, 30000).unref();
```

**Answer**: Graceful shutdown order: (1) Stop accepting new work, (2) Drain in-flight work, (3) Close external connections, (4) Exit. The `setTimeout` force-exit prevents hanging if connections don't close.

**K8s integration**: K8s sends SIGTERM, waits `terminationGracePeriodSeconds` (default 30s), then SIGKILL. Your shutdown must complete within that window.

---

## Q16. (Advanced) How do you handle the "thundering herd" problem when scaling with cluster?

**Scenario**: All cluster workers wake up for each incoming connection, but only one can accept it.

**Answer**: Modern Linux (and Node.js) mitigate this with **round-robin** scheduling in the cluster module. The primary process accepts and distributes, or workers accept via `SO_REUSEPORT`.

But the thundering herd can still happen with:
- **Cache invalidation**: All workers try to rebuild cache simultaneously
- **Reconnection storms**: All WebSocket clients reconnect at once after a deploy

**Fix for cache stampede**:
```js
const locks = new Map();

async function getWithLock(key, fetchFn) {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  // Only one caller fetches, others wait
  if (!locks.has(key)) {
    locks.set(key, fetchFn().then(async (data) => {
      await redis.set(key, JSON.stringify(data), 'EX', 60);
      locks.delete(key);
      return data;
    }));
  }
  return locks.get(key);
}
```

**Fix for reconnection storm**: Add jittered backoff in clients.

---

## Q17. (Advanced) How would you architect a Node.js system with both CPU-heavy and I/O-heavy workloads?

**Scenario**: SaaS platform with: REST API (I/O), PDF generation (CPU), video transcoding (heavy CPU), real-time notifications (WebSocket).

**Answer**:

```
┌──────────────────────────────────────────────┐
│                API Layer (Node.js)             │
│  - REST endpoints                              │
│  - WebSocket server                            │
│  - Authentication middleware                   │
│  - Route to queues for CPU work               │
└──────────────────┬───────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   Redis Cache   PostgreSQL  Message Queue
                              (BullMQ/SQS)
        ┌──────────┼──────────┐
        │          │          │
   PDF Worker    Video Worker  Notification Worker
   (Node.js +    (Go/Rust     (Node.js)
    Piscina)     service)
```

**Decision rationale**:
- **API**: Node.js — I/O-heavy, event loop efficient
- **PDF generation**: Node.js with `piscina` worker pool — moderate CPU, moderate volume
- **Video transcoding**: **Go or Rust** service — heavy CPU, Node is the wrong tool
- **Notifications**: Node.js — I/O-heavy (send push/email), natural fit
- **Queue**: Decouples CPU work from API, adds retry/backpressure

**Tradeoff**: A startup might do everything in Node.js with worker threads. An enterprise would use Go/Rust for heavy CPU and Node for the API layer.

---

## Q18. (Advanced) How do you load test a Node.js application to find its breaking point?

```bash
# Using autocannon (Node.js-based load tester)
npx autocannon -c 100 -d 30 -p 10 http://localhost:3000/api/users
# -c 100 concurrent connections
# -d 30 seconds duration
# -p 10 pipelining (requests per connection)
```

**Answer**: Load testing methodology:

1. **Baseline**: Single user, measure p50/p99 latency
2. **Ramp up**: Increase concurrent connections (100, 500, 1000, 5000)
3. **Find saturation**: Where p99 latency starts spiking
4. **Find breaking point**: Where errors start appearing

**Monitor during test**:
```js
// Expose metrics endpoint
app.get('/metrics', (req, res) => {
  res.json({
    eventLoopLag: /* from perf_hooks */,
    heapUsed: process.memoryUsage().heapUsed,
    activeHandles: process._getActiveHandles().length,
    activeRequests: process._getActiveRequests().length,
  });
});
```

**Common findings**:
- Event loop lag spikes → CPU bottleneck → add workers
- Memory grows linearly → memory leak → fix leak
- DB connection errors → pool exhaustion → increase pool or add replicas
- p99 degrades before p50 → backpressure needed

---

## Q19. (Advanced) What is `SharedArrayBuffer` and `Atomics`? When would you use them in production?

**Scenario**: Multiple worker threads need to update a shared counter (e.g., request metrics) without message passing overhead.

```js
// Main thread
const shared = new SharedArrayBuffer(8); // 8 bytes = 2 Int32 slots
const metrics = new Int32Array(shared);
// metrics[0] = request count, metrics[1] = error count

const workers = Array.from({ length: 4 }, () =>
  new Worker('./handler.js', { workerData: { metrics: shared } })
);

setInterval(() => {
  console.log({
    requests: Atomics.load(metrics, 0),
    errors: Atomics.load(metrics, 1),
  });
}, 1000);

// handler.js (worker)
const { workerData } = require('worker_threads');
const metrics = new Int32Array(workerData.metrics);

function handleRequest() {
  Atomics.add(metrics, 0, 1); // atomic increment — no race condition
}
```

**Answer**: `SharedArrayBuffer` provides shared memory between threads. `Atomics` provides atomic operations (add, load, store, compareExchange) to prevent race conditions. Use for **high-frequency counters** or **large data buffers** that would be too expensive to copy via `postMessage`.

**Production use cases**: Shared metrics counters, shared lookup tables, inter-thread coordination (Atomics.wait/notify).

---

## Q20. (Advanced) Your Node.js service runs 8 cluster workers. During deploy, 2 workers crash and don't restart. How do you prevent this and implement self-healing?

**Answer**:

```js
// Primary process — self-healing cluster
const cluster = require('cluster');
const os = require('os');

if (cluster.isPrimary) {
  const WORKER_COUNT = os.cpus().length;
  const restartCounts = new Map(); // track rapid restarts

  function forkWorker() {
    const worker = cluster.fork();
    restartCounts.set(worker.id, Date.now());
    return worker;
  }

  for (let i = 0; i < WORKER_COUNT; i++) forkWorker();

  cluster.on('exit', (worker, code, signal) => {
    console.error(`Worker ${worker.process.pid} exited (code: ${code}, signal: ${signal})`);

    // Anti-thrash: if worker restarted within 5s, delay restart
    const lastRestart = restartCounts.get(worker.id) || 0;
    const timeSinceRestart = Date.now() - lastRestart;

    if (timeSinceRestart < 5000) {
      console.error('Worker restarting too fast, delaying 5s...');
      setTimeout(forkWorker, 5000);
    } else {
      forkWorker();
    }
  });

  // Health check — ensure minimum workers running
  setInterval(() => {
    const active = Object.keys(cluster.workers).length;
    if (active < WORKER_COUNT) {
      console.warn(`Only ${active}/${WORKER_COUNT} workers, forking...`);
      forkWorker();
    }
  }, 10000);
}
```

**Prevention strategies**:
1. **Auto-restart** with anti-thrash delay (above)
2. **Health check endpoint** per worker — liveness probe in K8s
3. **Memory limits** — restart worker if heap exceeds threshold:
```js
setInterval(() => {
  const { heapUsed } = process.memoryUsage();
  if (heapUsed > 1.5 * 1024 ** 3) { // 1.5GB
    console.error('Memory limit exceeded, exiting for restart');
    process.exit(1); // primary will restart
  }
}, 30000);
```
4. **Uncaught exception handler** — log and exit (let cluster restart):
```js
process.on('uncaughtException', (err) => {
  console.error('Uncaught exception:', err);
  process.exit(1); // DO exit — unknown state
});
```

**Senior take**: In Kubernetes, you get self-healing for free (pod restarts). On bare metal, cluster module + PM2 + monitoring is essential. Always have alerting when worker count drops below expected.
