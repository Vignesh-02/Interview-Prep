# 29. Web Workers & Concurrency (Senior)

## Q1. What is a Web Worker and what can/can’t it access?

**Answer:**  
A **Web Worker** is a script that runs on a separate thread from the main window. It has its own global scope and event loop. **Can**: Run CPU-heavy code without blocking the UI, use timers, fetch, and most APIs that don’t require a window. **Cannot**: Access the DOM, `window`, or `document`; must communicate with the main thread via **postMessage** and receive messages via **onmessage**. No shared mutable state by default (only copied or transferred data).

---

## Q2. How do you pass data to a worker and back? What is structured clone vs transferable?

**Answer:**  
**postMessage(data)** sends a copy of `data` to the worker (or from worker to main). The data is **structured-cloned** (same algorithm as structuredClone): no functions, no symbols, no certain objects; cycles and many built-in types are supported. **Transferables**: For ArrayBuffer and similar, you can pass them as the second argument: `postMessage(buffer, [buffer])`. The buffer is **transferred** (no longer usable in the sender) for zero-copy, avoiding clone cost and keeping ownership clear.

---

## Q3. What is a SharedArrayBuffer and what problem does it solve? What are the risks?

**Answer:**  
**SharedArrayBuffer** is memory shared between the main thread and workers (or between workers). Multiple threads can read/write the same bytes. Solves: high-throughput communication without copying, and shared memory for coordination. **Risks**: Data races if you don’t synchronize. Use **Atomics** (e.g. Atomics.add, wait/wake) for synchronization. Browsers require cross-origin isolation (COOP/COEP headers) to enable SharedArrayBuffer to mitigate Spectre-style attacks.

---

## Q4. Implement a simple worker that computes the sum of an array and posts the result back.

**Answer:**
```javascript
// main.js
const w = new Worker('worker.js');
w.postMessage([1, 2, 3, 4, 5]);
w.onmessage = (e) => console.log('Sum:', e.data);

// worker.js
self.onmessage = (e) => {
  const sum = e.data.reduce((a, b) => a + b, 0);
  self.postMessage(sum);
};
```

---

## Q5. What is the difference between a dedicated worker and a shared worker?

**Answer:**  
**Dedicated worker**: Tied to one parent (the script that created it). Only that script can communicate with it. **Shared worker**: Can be shared by multiple scripts (e.g. multiple tabs or frames from the same origin). All connect to the same worker via `new SharedWorker(url)`. The worker receives a `port` for each connection and can broadcast or reply per port. Use shared workers for cross-tab coordination (e.g. single background connection).

---

## Q6. How would you parallelize a CPU-heavy task (e.g. process 1M items) using multiple workers?

**Answer:**  
(1) Create a pool of workers (e.g. `navigator.hardwareConcurrency`). (2) Split the work into chunks (e.g. 1M / N chunks). (3) Assign each chunk to a worker via postMessage. (4) Each worker processes its chunk and posts the result back. (5) Main thread collects results (e.g. in order using chunk index) and combines. (6) Reuse workers for the next batch. Use transferable if passing large buffers to avoid copy. Optionally use SharedArrayBuffer + Atomics if workers need to share state or progress.

---

## Q7. What is Atomics.wait and Atomics.notify? When would you use them?

**Answer:**  
**Atomics.wait(typedArray, index, value)**: Blocks the worker until the element at `index` is not equal to `value` (or timeout). **Atomics.notify(typedArray, index, count)**: Wakes up to `count` waiters on that index. Used to build locks, condition variables, or producer-consumer patterns on top of SharedArrayBuffer. Allows workers to sleep instead of spinning, saving CPU.

---

## Q8. Why can’t you pass a DOM node or a function to a worker via postMessage?

**Answer:**  
postMessage uses the **structured clone** algorithm. DOM nodes and functions are not cloneable (they’re tied to the main thread and execution context). So you can’t send them. You send data (e.g. serialized state, IDs, or a description of what to do); the worker does the computation and sends back data. For large binary data, use transferables (ArrayBuffer) instead of copying.

---

## Q9. What are the COOP and COEP headers and why might you need them when using SharedArrayBuffer?

**Answer:**  
**COOP** (Cross-Origin-Opener-Policy): e.g. `Cross-Origin-Opener-Policy: same-origin` isolates your window from cross-origin openers. **COEP** (Cross-Origin-Embedder-Policy): e.g. `Cross-Origin-Embedder-Policy: require-corp` requires all cross-origin resources to opt in (CORS or Cross-Origin-Resource-Policy). Together they enable a **cross-origin isolated** environment, which browsers require to allow **SharedArrayBuffer** (to mitigate side-channel attacks like Spectre). So to use SharedArrayBuffer you must send these headers and ensure embedded resources support them.

---

## Q10. When would you choose a worker over splitting work with setTimeout/setImmediate chunks on the main thread?

**Answer:**  
Use **workers** when: (1) Work is CPU-heavy and would block the main thread for noticeable time (e.g. crypto, parsing, heavy math). (2) You need true parallelism (multiple cores). (3) You have large data and can use transferables. Use **chunking on the main thread** (setTimeout/requestIdleCallback) when: (1) Work is short and you only need to yield to the event loop so the UI stays responsive. (2) You need to touch the DOM or main-thread-only APIs. (3) You want to avoid the overhead of worker setup and message passing for small tasks.
