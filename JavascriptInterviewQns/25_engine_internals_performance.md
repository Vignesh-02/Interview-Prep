# 25. JavaScript Engine Internals & Performance (Senior)

## Q1. At a high level, how does V8 (or a typical JS engine) execute JavaScript?

**Answer:**  
Source is parsed into an AST, then compiled to bytecode (and/or machine code). Execution uses a **call stack** and **heap**. Modern engines use **JIT**: hot code is optimized (e.g. inline caches, type feedback) and recompiled to fast machine code. Garbage collection reclaims unused heap memory. The event loop schedules tasks and microtasks. Engines also do inlining, escape analysis, and speculative optimization based on observed types.

---

## Q2. What are “hidden classes” (or “shapes”) and why do they matter for performance?

**Answer:**  
Engines infer a “shape” (hidden class) for each object based on properties added and their order. Objects with the same shape share the same hidden class and can use fast property access (offset-based). If you add properties in different orders or delete properties, you get different shapes and slower, more generic code. So: use consistent property order and avoid adding/deleting properties dynamically in hot paths for best performance.

---

## Q3. What is the difference between the call stack and the heap?

**Answer:**  
**Call stack**: Stores execution context (local variables, return address) for each function call. LIFO; one thread. Stack overflow happens when recursion or call depth is too high. **Heap**: Stores objects, closures, and other dynamically allocated data. References live on the stack or in other heap objects. GC manages the heap. Stack is fast and limited; heap is larger and shared.

---

## Q4. What is JIT compilation and what are “hot” vs “cold” code paths?

**Answer:**  
**JIT** (Just-In-Time): code is compiled at runtime. Frequently executed (“hot”) code is optimized and recompiled to fast machine code; rarely run (“cold”) code may stay as bytecode or get less optimization. Type feedback from hot paths drives optimizations (e.g. inline caches, specialized code). Cold code is deoptimized or not optimized to save time and memory.

---

## Q5. Why might adding properties to an object “in order” be faster than adding them in random order?

**Answer:**  
Engines optimize based on object shape. Adding properties in a consistent order keeps one hidden class per “layout.” Adding in random order (e.g. `obj[key]` where key varies) creates many different shapes or forces the engine to use a slower, dictionary-like representation. Consistent order also helps inlining and property offset lookups.

---

## Q6. What is “deoptimization” and what can trigger it in V8?

**Answer:**  
**Deoptimization** is when the engine falls back from optimized code to less optimized or interpreted code. Triggers include: type change (e.g. a property that was always a number suddenly becomes an object), change in object shape, overflow of an array that was thought to be dense, or other speculation failures. Deopt is expensive, so stable types and shapes in hot code help.

---

## Q7. How would you optimize a hot loop that processes a large array of numbers?

**Answer:**  
(1) Use a **typed array** (e.g. Float64Array) if possible for fixed numeric types. (2) Avoid **allocation inside the loop** (reuse objects/arrays). (3) Keep **monomorphic** code (same types); avoid mixing number/object in the same variable. (4) Prefer **local variables** over property access. (5) Avoid **creating functions** in the loop. (6) Consider **Web Workers** to move work off the main thread.

---

## Q8. What is the difference between the main thread and a Web Worker in terms of memory and execution?

**Answer:**  
**Main thread**: Single thread for JS, layout, paint; shares one heap with the DOM. Long-running JS blocks rendering and input. **Web Worker**: Separate thread and global scope; no DOM access; communicate via postMessage. Has its own heap and event loop. Good for CPU-heavy or I/O work so the main thread stays responsive. SharedArrayBuffer allows shared memory (with care).

---

## Q9. What are microtasks and how do they affect perceived performance?

**Answer:**  
Microtasks (promises, queueMicrotask) run after the current script and before the next macrotask (e.g. next timer or I/O). If you queue many microtasks, they all run in a row; the main thread is blocked and the UI can freeze. So long or unbounded microtask chains hurt responsiveness. Prefer breaking work across macrotasks (e.g. setTimeout 0) or requestIdleCallback when you have a lot of work.

---

## Q10. What is “garbage collection pause” and how can you reduce its impact in a critical path?

**Answer:**  
**GC pause**: When the engine stops (or heavily slows) execution to run a GC cycle. Large heaps and long-lived objects can cause longer pauses. Mitigations: (1) **Reduce allocation** in hot paths so less to collect. (2) **Reuse objects** (object pooling). (3) **Smaller, short-lived allocations** so the engine can collect incrementally. (4) In Node, tune `--max-old-space-size` and monitor; avoid holding huge caches. (5) Use **WeakRef** for caches so entries can be collected under pressure.
