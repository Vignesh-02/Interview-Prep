# 1. Event Loop, Microtasks & I/O Phases

## Topic Introduction

The event loop is the heart of Node.js. It is a **single-threaded scheduler** that processes callbacks when the call stack is empty. Node offloads I/O to the OS (via `epoll`/`kqueue`/`IOCP`) or libuv's thread pool, then queues callbacks back onto the main thread.

```
┌─────────────────────────┐
│      Call Stack          │  ← JS executes here (one thing at a time)
└────────────┬────────────┘
             │
   ┌─────────▼──────────┐
   │  process.nextTick   │  ← highest priority microtask (Node-specific)
   ├─────────────────────┤
   │  Promise microtasks  │  ← V8-managed
   └─────────┬───────────┘
             │
┌────────────▼────────────┐
│      Event Loop          │
│ 1) Timers (setTimeout)   │
│ 2) I/O Callbacks         │
│ 3) Poll (network, fs)    │
│ 4) Check (setImmediate)  │
│ 5) Close Callbacks       │
└──────────────────────────┘
```

Understanding the event loop is the **single most important** Node.js concept for a senior backend engineer. Every decision about scaling, CPU work, and concurrency flows from it.

**Go/Java tradeoff**: Go uses goroutines with a built-in scheduler (M:N threading). Java uses virtual threads (Project Loom) or a thread-per-request model. Node's single-threaded event loop has lower overhead for I/O but requires explicit offloading for CPU work.

---

## Q1. (Beginner) What is the Node.js event loop? Explain with a simple example.

**Scenario**: You write this code and wonder why the output order isn't what you expect.

```js
console.log('A');
setTimeout(() => console.log('B'), 0);
console.log('C');
```

**Answer**:
Output: `A`, `C`, `B`.

The event loop processes the call stack first (synchronous code `A` and `C`). `setTimeout` schedules its callback into the **timers** phase. Only after the stack is empty does the event loop pick up `B`.

The event loop is a **loop** that repeatedly: (1) executes the call stack, (2) drains microtask queues, (3) moves through phases (timers → I/O → poll → check → close).

---

## Q2. (Beginner) What are the six phases of the event loop? Name each and give one example.

**Answer**:

| Phase | What runs | Example |
|-------|-----------|---------|
| **Timers** | `setTimeout`, `setInterval` callbacks whose delay has elapsed | `setTimeout(fn, 100)` |
| **I/O Callbacks** | Deferred I/O callbacks (e.g. TCP errors) | TCP `ECONNRESET` handler |
| **Idle/Prepare** | Internal use only | (internal) |
| **Poll** | Retrieve new I/O events; execute their callbacks | `fs.readFile` callback |
| **Check** | `setImmediate` callbacks | `setImmediate(fn)` |
| **Close** | Close event handlers | `socket.on('close', fn)` |

Between every phase, Node drains the **microtask queue** (Promises) and **nextTick queue**.

---

## Q3. (Beginner) What is the difference between microtasks and macrotasks?

**Scenario**: Predict the output:

```js
setTimeout(() => console.log('timeout'), 0);
Promise.resolve().then(() => console.log('promise'));
console.log('sync');
```

**Answer**:
Output: `sync`, `promise`, `timeout`.

| Type | Examples | Priority |
|------|----------|----------|
| **Microtask** | `Promise.then`, `queueMicrotask`, `process.nextTick` | High — runs after current stack, before next phase |
| **Macrotask** | `setTimeout`, `setInterval`, `setImmediate`, I/O | Lower — runs in event loop phases |

**Rule**: All microtasks drain before the event loop moves to the next phase.

---

## Q4. (Beginner) What is `process.nextTick`? How is it different from `Promise.then`?

**Scenario**: Predict the output:

```js
process.nextTick(() => console.log('nextTick'));
Promise.resolve().then(() => console.log('promise'));
```

**Answer**:
Output: `nextTick`, `promise`.

`process.nextTick` callbacks run **before** Promise microtasks. Priority order:
1. Call stack completes
2. `process.nextTick` queue drains (all of it)
3. Promise microtask queue drains
4. Event loop phase begins

**Warning**: Recursive `nextTick` can **starve** the event loop because it never yields to I/O.

```js
// BAD: starves the event loop
function bad() { process.nextTick(bad); }
bad(); // setTimeout callbacks will NEVER fire
```

---

## Q5. (Beginner) What is `setImmediate` and when does it fire before `setTimeout(0)`?

**Scenario**: Inside an I/O callback, which fires first?

```js
const fs = require('fs');
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));
});
```

**Answer**:
Output: `immediate`, `timeout`.

Inside an I/O callback, Node is in the **poll** phase. After poll completes it moves to the **check** phase (`setImmediate`) before looping back to **timers**. So `setImmediate` fires first.

Outside I/O, the order of `setTimeout(0)` vs `setImmediate` is **non-deterministic** because it depends on system clock granularity.

---

## Q6. (Intermediate) What is libuv? What role does it play in Node.js?

**Scenario**: You're debugging why `fs.readFile` is slower than expected under load. You suspect the thread pool is saturated.

**Answer**:
libuv is a **C library** that provides:
- The **event loop** (phases, timers, poll)
- A **thread pool** (default 4 threads) for blocking I/O (fs, DNS `lookup`, crypto, zlib)
- Cross-platform async I/O abstraction (epoll on Linux, kqueue on macOS, IOCP on Windows)

```
JavaScript (V8)  →  Node.js C++ bindings  →  libuv (C)  →  OS kernel
```

The thread pool is shared. If you do 10 concurrent `fs.readFile` calls and 5 `crypto.pbkdf2` calls, they all compete for 4 threads.

**Fix**: Increase pool size: `UV_THREADPOOL_SIZE=16 node app.js` (max 128).

**Tradeoff with Go**: Go's goroutine scheduler handles this automatically — file I/O uses OS threads transparently. In Node, you must be aware of thread pool contention.

---

## Q7. (Intermediate) How does async/await work internally in terms of the event loop?

**Scenario**: Explain what happens under the hood:

```js
async function fetchData() {
  console.log('1');
  const data = await fetch('https://api.example.com/data');
  console.log('2');
  return data;
}
fetchData();
console.log('3');
```

**Answer**:
Output: `1`, `3`, `2`.

`async/await` is syntactic sugar over Promises. `await` pauses the function execution and schedules the remainder as a **microtask** when the awaited Promise resolves.

Equivalent:
```js
function fetchData() {
  console.log('1');
  return fetch('https://api.example.com/data').then((data) => {
    console.log('2');
    return data;
  });
}
```

The code after `await` is a **microtask continuation**. It runs after the current call stack empties and before the next event loop phase.

---

## Q8. (Intermediate) What happens when you block the event loop? Show a production example.

**Scenario**: Your API suddenly has 30s response times. CPU is at 100%. Traffic hasn't increased.

```js
// Someone added this endpoint
app.get('/report', (req, res) => {
  const data = JSON.parse(fs.readFileSync('huge-10gb.json')); // BLOCKS
  const result = data.filter(row => row.active).map(transform);
  res.json(result);
});
```

**Answer**:
**Every** other request (including health checks) waits because the single JS thread is occupied. Symptoms:
- All endpoints time out simultaneously
- CPU is 100% but throughput is 0
- Event loop delay spikes to seconds

**Fix**:
```js
const { Worker } = require('worker_threads');

app.get('/report', async (req, res) => {
  const result = await new Promise((resolve, reject) => {
    const w = new Worker('./report-worker.js');
    w.on('message', resolve);
    w.on('error', reject);
  });
  res.json(result);
});
```

**Detection**: Use `perf_hooks.monitorEventLoopDelay()` and alert when mean delay > 100ms.

---

## Q9. (Intermediate) How do you measure event loop lag in production?

**Scenario**: Your p99 latency is 5s but average is 50ms. You suspect event loop blocking.

```js
const { monitorEventLoopDelay } = require('perf_hooks');
const histogram = monitorEventLoopDelay({ resolution: 20 });
histogram.enable();

setInterval(() => {
  console.log({
    mean: (histogram.mean / 1e6).toFixed(2) + 'ms',
    p99: (histogram.percentile(99) / 1e6).toFixed(2) + 'ms',
    max: (histogram.max / 1e6).toFixed(2) + 'ms',
  });
  histogram.reset();
}, 5000);
```

**Answer**:
- **mean > 50ms**: Something is blocking occasionally
- **p99 > 200ms**: Significant blocking under load
- **max > 1000ms**: A request is doing synchronous heavy work

Combine with: (1) CPU profile (`node --prof`), (2) Flamegraphs (0x, Clinic.js), (3) Prometheus metric `nodejs_eventloop_lag_seconds`.

**Tradeoff with Go**: Go doesn't have this problem — goroutines are preemptively scheduled. In Java, virtual threads also avoid this. Node requires explicit monitoring.

---

## Q10. (Intermediate) What is the "Zalgo" problem and how do you avoid it?

**Scenario**: A function sometimes calls its callback synchronously, sometimes asynchronously:

```js
function getData(key, cb) {
  if (cache[key]) {
    cb(null, cache[key]); // SYNC — Zalgo!
  } else {
    db.get(key, cb);      // ASYNC
  }
}
```

**Answer**:
This is **"releasing Zalgo"** — mixing sync and async callback behavior. The caller can't predict when `cb` fires, leading to subtle race conditions.

**Fix** — always be async:
```js
function getData(key, cb) {
  if (cache[key]) {
    process.nextTick(() => cb(null, cache[key]));
  } else {
    db.get(key, cb);
  }
}
```

Or use Promises (inherently always async):
```js
async function getData(key) {
  if (cache[key]) return cache[key];
  return db.get(key);
}
```

---

## Q11. (Intermediate) Predict the output of this nested scheduling code. Explain step by step.

```js
setImmediate(() => {
  console.log('A');
  process.nextTick(() => console.log('B'));
  Promise.resolve().then(() => console.log('C'));
});

setTimeout(() => {
  console.log('D');
  process.nextTick(() => console.log('E'));
  Promise.resolve().then(() => console.log('F'));
}, 0);

process.nextTick(() => console.log('G'));
Promise.resolve().then(() => console.log('H'));
```

**Answer**:
```
G       ← nextTick drains first
H       ← then Promise microtasks
D       ← timers phase (setTimeout)
E       ← nextTick after timer callback
F       ← Promise microtask after timer callback
A       ← check phase (setImmediate)
B       ← nextTick after setImmediate callback
C       ← Promise microtask after setImmediate callback
```

**Rule**: After each callback, Node drains nextTick then Promise queues before moving on.

---

## Q12. (Intermediate) What runs on the libuv thread pool vs what uses OS async I/O?

**Answer**:

| **Thread Pool** (blocking) | **OS Async I/O** (non-blocking) |
|---|---|
| `fs.*` (file system) | TCP/UDP sockets (network) |
| `dns.lookup()` | `dns.resolve()` |
| `crypto.pbkdf2`, `crypto.randomBytes` | HTTP requests |
| `zlib` compress/decompress | Pipes, signals |

**Production impact**: If you have 50 concurrent file reads and only 4 threads, they queue up. Network I/O (database queries, HTTP calls) does NOT use the thread pool — it uses the OS kernel directly.

```bash
# Increase thread pool for file-heavy workloads
UV_THREADPOOL_SIZE=16 node server.js
```

---

## Q13. (Advanced) You have a Node.js API doing 10,000 req/s. Suddenly p99 latency jumps from 50ms to 3s. CPU is only at 30%. Walk through your debugging process.

**Answer**:
Low CPU + high latency = **event loop contention**, not CPU saturation.

**Step 1**: Check event loop delay metric. If spiking → something is blocking.

**Step 2**: Take a CPU profile or flamegraph:
```bash
node --prof server.js
# or
npx clinic doctor -- node server.js
```

**Step 3**: Look for synchronous hotspots:
- `JSON.parse` on large payloads
- `RegExp` with catastrophic backtracking
- Synchronous `fs` calls (`readFileSync`)
- Large `Array.sort` or `map` on big datasets

**Step 4**: Check thread pool saturation:
```js
// If many concurrent fs or crypto ops, pool exhaustion causes queuing
// Symptom: DNS or fs callbacks delayed even though CPU is free
```

**Step 5**: Check garbage collection pauses:
```bash
node --trace-gc server.js
# look for long GC pauses (>100ms)
```

**Fix**: Offload blocking work to worker threads, increase thread pool, or split into microservices.

**Tradeoff**: In Go, goroutine scheduling is preemptive — a single slow goroutine doesn't block others. In Java with virtual threads (Loom), blocking I/O doesn't starve the scheduler. Node requires the developer to explicitly avoid blocking.

---

## Q14. (Advanced) Design a Node.js service that handles both I/O-heavy API requests and CPU-heavy PDF generation without blocking.

**Scenario**: An e-commerce API serves product data (I/O-heavy) and generates invoice PDFs (CPU-heavy). 50k daily users.

**Answer**:

```
                    ┌─────────────────┐
  HTTP requests ───►│  Node.js API    │──► DB/Cache (I/O, non-blocking)
                    │  (event loop)   │
                    └───────┬─────────┘
                            │ POST /invoices
                            ▼
                    ┌─────────────────┐
                    │  BullMQ Queue   │ (Redis-backed)
                    └───────┬─────────┘
                            ▼
                    ┌─────────────────┐
                    │  Worker Service  │ (separate process or container)
                    │  - PDF gen       │
                    │  - Upload to S3  │
                    └─────────────────┘
```

```js
// API handler — never blocks the event loop
app.post('/invoices', async (req, res) => {
  const job = await invoiceQueue.add('generate', {
    orderId: req.body.orderId,
    userId: req.user.id,
  });
  res.status(202).json({ jobId: job.id, status: 'processing' });
});

// Worker process (separate)
const worker = new Worker('invoiceQueue', async (job) => {
  const pdf = await generatePDF(job.data.orderId); // CPU-heavy
  await uploadToS3(pdf);
  await db.updateInvoiceStatus(job.data.orderId, 'ready');
}, { connection: redis });
```

**Key decisions**:
- API returns **202 Accepted** immediately (async)
- CPU work isolated in **separate process** (not worker threads on the same machine)
- Queue provides **retry**, **backpressure**, **dead-letter** handling

**Tradeoff with Go**: Go could handle PDF generation in a goroutine without blocking other requests (goroutines are multiplexed). But you'd still want a queue for retry/fault tolerance at scale.

---

## Q15. (Advanced) Explain event loop starvation from recursive microtasks. Show the problem and fix.

**Scenario**: A developer writes a "fast loop" using Promises:

```js
// BAD: event loop starvation
function processAll(items, i = 0) {
  if (i >= items.length) return;
  processItem(items[i]);
  return Promise.resolve().then(() => processAll(items, i + 1));
}
processAll(millionItems); // setTimeout/setInterval callbacks NEVER fire
```

**Answer**:
Each `Promise.resolve().then(...)` adds to the **microtask queue**. Node drains ALL microtasks before moving to the next event loop phase. With a million items, the timers and I/O phases are starved.

**Fix** — yield to the event loop with `setImmediate`:
```js
function processAll(items, i = 0) {
  if (i >= items.length) return;
  processItem(items[i]);
  setImmediate(() => processAll(items, i + 1)); // yields to event loop
}
```

Or batch with `setImmediate` every N items:
```js
function processAll(items, i = 0) {
  const BATCH = 1000;
  for (let j = i; j < Math.min(i + BATCH, items.length); j++) {
    processItem(items[j]);
  }
  if (i + BATCH < items.length) {
    setImmediate(() => processAll(items, i + BATCH));
  }
}
```

---

## Q16. (Advanced) How does Node.js compare to Go, Java, and Python for concurrency? When is Node the wrong choice?

**Answer**:

| | **Node.js** | **Go** | **Java** | **Python** |
|---|---|---|---|---|
| **Model** | Single-threaded event loop | Goroutines (M:N scheduler) | Thread pool / Virtual threads (Loom) | GIL + async (asyncio) |
| **I/O concurrency** | Excellent | Excellent | Excellent (NIO/Loom) | Good (asyncio) |
| **CPU parallelism** | Worker threads (explicit) | Native goroutines | Native threads | multiprocessing (separate processes) |
| **Memory per connection** | Very low (~few KB) | Low (~4KB goroutine stack) | Higher (thread stack ~1MB) | Moderate |
| **Sweet spot** | I/O-heavy APIs, real-time | Systems, CLI, microservices | Enterprise, CPU+I/O mix | Data, ML, scripting |

**Node is the wrong choice when**:
- Heavy CPU computation is the primary workload (use Go or Rust)
- You need true multi-threaded parallelism within a single process (use Java or Go)
- Latency sensitivity requires predictable GC pauses (use Go or Rust)

**Node is excellent when**:
- High I/O concurrency (thousands of connections)
- Real-time WebSocket servers
- Rapid development with JavaScript/TypeScript ecosystem
- BFF (Backend for Frontend) layers

---

## Q17. (Advanced) Your team reports that `dns.lookup` calls are causing random 500ms delays. Explain why and fix it.

**Scenario**: HTTP requests to external APIs occasionally take 500ms+ longer than expected, but the external API responds in 10ms.

**Answer**:
`dns.lookup()` (used by default in `http.request` and most HTTP clients) uses the **libuv thread pool**. If all 4 threads are busy with `fs` or `crypto` operations, DNS lookups **queue behind them**.

```js
const https = require('https');
// This internally calls dns.lookup() → thread pool
https.get('https://api.stripe.com/...', callback);
```

**Fix options**:

1. **Increase thread pool size**: `UV_THREADPOOL_SIZE=16`
2. **Use `dns.resolve`** instead (uses c-ares, non-blocking, no thread pool):
```js
const dns = require('dns');
const resolver = new dns.Resolver();
resolver.resolve4('api.stripe.com', (err, addresses) => { /* ... */ });
```
3. **Cache DNS results** in application:
```js
const { LookupCache } = require('dns-cache');
// or use a library like cacheable-lookup
```
4. **Use an HTTP client** that supports DNS caching (e.g., `got` with `cacheable-lookup`).

---

## Q18. (Advanced) What happens during garbage collection in V8? How does it affect the event loop in production?

**Scenario**: Your Node.js service has periodic 200ms latency spikes every 30 seconds under heavy load.

**Answer**:
V8 uses a **generational garbage collector**:
- **Scavenge** (minor GC): Collects short-lived objects in the "new space". Fast (1-5ms). Frequent.
- **Mark-Sweep-Compact** (major GC): Collects old space. Can pause for 50-200ms+.

GC **pauses the event loop** — no callbacks execute during collection.

```bash
# Trace GC pauses
node --trace-gc server.js
# Output: Scavenge 3.2ms, Mark-sweep 147.3ms
```

**Mitigations**:
```js
// 1. Increase old space to reduce frequency of major GC
// node --max-old-space-size=4096 server.js

// 2. Avoid creating unnecessary objects in hot paths
// BAD
app.get('/users', (req, res) => {
  const result = users.map(u => ({ ...u, fullName: u.first + ' ' + u.last }));
  res.json(result);
});

// BETTER — reuse objects or use streaming
app.get('/users', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.write('[');
  users.forEach((u, i) => {
    if (i > 0) res.write(',');
    res.write(JSON.stringify(u));
  });
  res.end(']');
});
```

**Tradeoff**: Go has a concurrent GC with sub-millisecond pauses. Java's ZGC/Shenandoah achieve <1ms pauses. Node's V8 GC is good but can cause noticeable pauses with large heaps.

---

## Q19. (Advanced) Design a system where Node.js handles 100k concurrent WebSocket connections. What are the bottlenecks?

**Scenario**: A real-time dashboard serves 100k users simultaneously via WebSocket.

**Answer**:

```
                         Load Balancer (sticky sessions)
                         /          |          \
                    Node 1       Node 2       Node 3
                   (25k conn)  (25k conn)   (25k conn) ...
                         \          |          /
                          Redis Pub/Sub (fan-out)
```

**Bottlenecks and solutions**:

1. **File descriptors**: Default `ulimit` is 1024. Set to 100k+:
```bash
ulimit -n 100000
```

2. **Memory**: Each WebSocket connection uses ~10-50KB. 100k × 50KB = 5GB.
```bash
node --max-old-space-size=8192 server.js
```

3. **Message broadcasting**: Don't iterate 100k connections on one process:
```js
// Use Redis pub/sub for cross-process broadcast
const Redis = require('ioredis');
const pub = new Redis();
const sub = new Redis();

sub.subscribe('dashboard-updates');
sub.on('message', (channel, message) => {
  // Only send to connections on THIS process
  localConnections.forEach(ws => ws.send(message));
});
```

4. **Event loop saturation**: Serializing 100k messages blocks. Use `setImmediate` to batch:
```js
function broadcastBatched(connections, message, batchSize = 1000) {
  let i = 0;
  function sendBatch() {
    const end = Math.min(i + batchSize, connections.length);
    for (; i < end; i++) connections[i].send(message);
    if (i < connections.length) setImmediate(sendBatch);
  }
  sendBatch();
}
```

---

## Q20. (Advanced) What are the top 5 event loop anti-patterns that a senior engineer must catch in code review?

**Answer**:

**1. Synchronous file I/O in request handlers**:
```js
// RED FLAG
app.get('/config', (req, res) => {
  const data = fs.readFileSync('/etc/config.json'); // blocks ALL requests
  res.json(JSON.parse(data));
});
```

**2. CPU-heavy computation on the main thread**:
```js
// RED FLAG
app.post('/hash', (req, res) => {
  const hash = crypto.pbkdf2Sync(req.body.password, salt, 100000, 64, 'sha512');
  res.json({ hash: hash.toString('hex') });
});
// FIX: use crypto.pbkdf2 (async) or worker thread
```

**3. Unbounded concurrency (no backpressure)**:
```js
// RED FLAG — fires 10,000 HTTP requests simultaneously
const results = await Promise.all(urls.map(url => fetch(url)));
// FIX: use p-limit or p-queue to cap concurrency
```

**4. Recursive microtasks / nextTick (event loop starvation)**:
```js
// RED FLAG
function drain() { process.nextTick(drain); }
```

**5. Unhandled Promise rejections**:
```js
// RED FLAG — silent crash or memory leak
async function doWork() { throw new Error('oops'); }
doWork(); // no .catch(), no await, no try/catch
// FIX: always await or .catch(); use process.on('unhandledRejection', handler)
```

**Senior interview answer**: "I look for synchronous I/O, CPU on the main thread, unbounded parallelism, microtask starvation, and unhandled rejections. Each one can take down a production Node.js service."
