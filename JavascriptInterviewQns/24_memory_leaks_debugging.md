# 24. Memory Leaks & Debugging (Senior)

## Q1. What are the most common causes of memory leaks in JavaScript (browser)?

**Answer:**  
(1) **Global variables** or accidental globals (e.g. assigning to undeclared variables). (2) **Forgotten timers** (setInterval/setTimeout) that keep references. (3) **Closures** holding large objects or DOM nodes. (4) **Detached DOM** (nodes removed from the tree but still referenced in JS). (5) **Event listeners** not removed when the component is discarded. (6) **Caches** or maps that grow unbounded.

---

## Q2. How would you detect a memory leak in the browser? What tools do you use?

**Answer:**  
Use **Chrome DevTools → Memory** (or equivalent): take heap snapshots before and after an action (e.g. open/close a modal). Compare snapshots; look for growing retained size, detached DOM nodes, or objects that should have been collected. **Performance** tab can show rising JS heap over time. **Allocation instrumentation** shows where allocations happen. Fix by removing references (listeners, closures, timers, cache limits).

---

## Q3. What is a “detached DOM node” and how does it cause a leak?

**Answer:**  
A node is **detached** when it has been removed from the document (e.g. `element.remove()`) but JavaScript still holds a reference to it (e.g. in a closure, variable, or cache). The DOM tree for that node stays in memory because the engine can’t collect it. Fix: null out references when you remove the node, and avoid storing DOM nodes in long-lived closures or global structures.

---

## Q4. You have a component that adds a resize listener. How do you avoid a leak when the component is torn down?

**Answer:**  
Store the handler reference and call **removeEventListener** in a cleanup phase (e.g. component unmount, dispose, or finalization):

```javascript
const handler = () => { /* ... */ };
window.addEventListener('resize', handler);
// on teardown:
window.removeEventListener('resize', handler);
```
If the handler is inline, you must keep the same function reference to remove it. In frameworks (React, etc.), use useEffect cleanup or equivalent lifecycle to remove listeners.

---

## Q5. Implement a cache with a maximum size (e.g. LRU or “evict oldest”) to avoid unbounded growth.

**Answer:**  
Simple “evict oldest” with Map (insertion order):

```javascript
function createLimitedCache(maxSize) {
  const map = new Map();
  return {
    set(key, value) {
      if (map.size >= maxSize && !map.has(key)) {
        const first = map.keys().next().value;
        map.delete(first);
      }
      map.set(key, value);
    },
    get(key) {
      if (!map.has(key)) return undefined;
      const v = map.get(key);
      map.delete(key);
      map.set(key, v);
      return v;
    }
  };
}
```
For true LRU, the get also moves the key to “most recently used” (as above); for FIFO eviction, don’t re-insert on get.

---

## Q6. What is the difference between a heap snapshot and allocation timeline? When would you use each?

**Answer:**  
**Heap snapshot**: Point-in-time view of all objects in the heap. Use to see what’s retaining memory, find detached DOM, or compare before/after to see what grew. **Allocation timeline** (or allocation instrumentation): Records allocations over time and ties them to allocation sites. Use to see what code is allocating and whether those allocations are short-lived or long-lived.

---

## Q7. How can closures cause memory leaks? Give a pattern that leaks and how to fix it.

**Answer:**  
A closure keeps its outer scope alive. If that scope holds a large object or DOM node, and the closure is stored (e.g. in a global, or in an event listener that’s never removed), that data can’t be GC’d. Example: storing a DOM element in a closure used as a callback and never removing the listener. Fix: don’t capture unnecessary data in the closure; remove the listener when done; null out references.

---

## Q8. In Node.js, how would you debug high memory usage or a suspected leak?

**Answer:**  
(1) Use **heap snapshots**: `--heapsnapshot-signal=SIGUSR2` or `v8.writeHeapSnapshot()`. (2) Compare snapshots to see what’s growing. (3) Use **process.memoryUsage()** over time. (4) Check for global caches, retained modules, or event listeners that are never removed. (5) Use tools like clinic.js or node --inspect with Chrome DevTools for heap and CPU.

---

## Q9. What is a weak reference (WeakRef) and how can it help with caching without leaking?

**Answer:**  
**WeakRef** holds a reference that doesn’t prevent the object from being garbage-collected. When the object is collected, the WeakRef’s deref() returns undefined. Useful for caches: store values in WeakRefs so they can be collected under memory pressure. **FinalizationRegistry** can notify when an object is GC’d (e.g. to clean up associated resources). Use with care; GC timing is non-deterministic.

---

## Q10. You suspect a third-party library is leaking. How do you isolate and confirm it?

**Answer:**  
(1) Reproduce with a minimal page that only loads the library and performs the leaking action. (2) Take heap snapshots before and after the action (e.g. create/destroy widget) and compare; see what’s retained. (3) Check if the library exposes cleanup/destroy/dispose; call it and see if retention drops. (4) Search the library’s code for globals, timers, and listeners. (5) If it’s closed source, report to the vendor with a minimal repro and snapshot comparison.
