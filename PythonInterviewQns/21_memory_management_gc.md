# 21. Memory Management (heap, reference counting, GC) — Senior

## Q1. (Easy) Where does Python store objects? What is the “private heap”?

**Answer:**  
Python stores object data on a **private heap** managed by the interpreter. All Python objects (ints, lists, dicts, etc.) live in this heap. The programmer doesn’t allocate/free it directly; the interpreter uses **reference counting** and a **garbage collector** to reclaim memory. The heap is process-local.

---

## Q2. (Easy) What is reference counting? When is an object’s refcount increased or decreased?

**Answer:**  
Each object has a **reference count** (number of references to it). It increases when: you assign to a variable, pass an argument, put it in a container, etc. It decreases when: you reassign/delete the reference, the variable goes out of scope, the container is removed, etc. When the refcount reaches **0**, the object is deallocated immediately (in CPython).

---

## Q3. (Medium) What problem does the cyclic garbage collector solve? Reference counting alone isn’t enough for what?

**Answer:**  
**Reference counting** can’t reclaim **cycles**: A points to B, B points to A, no one else points to them — both refcounts are 1, so neither is freed. The **cyclic GC** (gc module) traverses objects and detects cycles; it then breaks cycles and frees unreachable groups. So it handles circular references that refcount alone would leak.

---

## Q4. (Medium) What is `sys.getrefcount(x)`? Why is it often 1 or 2 higher than you expect?

**Answer:**  
**getrefcount(x)** returns the current reference count of the object. The **argument** to getrefcount itself is a temporary reference, so the count is at least 1 higher than “external” references. Plus implementation may hold internal refs. So use it for relative comparison, not absolute “number of variables.”

---

## Q5. (Medium) What does `gc.collect()` do? When would you call it?

**Answer:**  
**gc.collect()** runs a **full** collection (or the requested generation). It finds and breaks cycles and frees unreachable objects. You might call it: after deleting large structures to reclaim memory sooner, in tests to assert cleanup, or in long-running processes where you want to force collection. Usually the automatic GC is enough.

---

## Q6. (Medium) What are generations in the cyclic GC? Why does Python use a generational collector?

**Answer:**  
The cyclic GC uses **generations** (typically 0, 1, 2). New objects go to generation 0; objects that survive a collection are promoted. **Young** objects are collected often; **old** objects are collected less often. Most objects die young, so this reduces cost by not scanning long-lived objects every time.

---

## Q7. (Tough) How can you create a circular reference in Python? Show a cycle the cyclic GC will collect.

**Answer:**
```python
class Node:
    def __init__(self):
        self.ref = None
a = Node()
b = Node()
a.ref = b
b.ref = a
# Now no external refs to a, b — only cycle. Refcount of each is 1.
del a, b  # Cyclic GC will find and collect them
```
Without cyclic GC, deleting both would leave the cycle unfreed. The GC traces from a small set of “roots” and finds that the cycle is unreachable.

---

## Q8. (Tough) What is `__del__` and why is it dangerous with cycles or during interpreter shutdown?

**Answer:**  
**__del__** is the finalizer; called when the object is about to be destroyed. **Dangers:** (1) During **cycle collection**, order of destruction is arbitrary; __del__ can run when other objects in the cycle are half-destroyed. (2) During **shutdown**, modules may already be gone; __del__ can’t safely import or use globals. Prefer **context managers** or **atexit** for cleanup.

---

## Q9. (Tough) What does `gc.disable()` do? When might you use it?

**Answer:**  
**gc.disable()** turns off **automatic** cyclic GC. Refcounting still frees non-cyclic objects. Use when: you have no cycles and want to avoid GC overhead in a tight loop, or you’re doing your own collection with **gc.collect()** at controlled points. Re-enable with **gc.enable()**. Risky if you do create cycles.

---

## Q10. (Tough) How does Python’s memory allocator (e.g. pymalloc) relate to the system allocator? Why have a custom allocator?

**Answer:**  
CPython uses **pymalloc** for small objects (e.g. under 512 bytes): it allocates large blocks from the OS and parcels them out, reducing fragmentation and malloc/free calls. Large allocations go to the system allocator. Benefits: fewer system calls, better locality, lower fragmentation for small, short-lived objects typical in Python.
