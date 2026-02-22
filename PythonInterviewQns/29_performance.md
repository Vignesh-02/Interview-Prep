# 29. Performance (profiling, optimization, C extensions) — Senior

## Q1. (Easy) What is cProfile? How do you run it on a script?

**Answer:**  
**cProfile** is a C-based **profiler** in the standard library. It records function calls and time spent. Run: **python -m cProfile script.py** or **cProfile.run("main()")**. Output shows cumulative time per function. Use **-s cumtime** to sort by cumulative time. For more readable output, use **pstats** or **snakeviz** to visualize.

---

## Q2. (Easy) What is the difference between cProfile and profile? When use which?

**Answer:**  
**profile** is pure Python; **cProfile** is C and has much less overhead. Prefer **cProfile** for real profiling. **profile** can be extended in Python and is useful when you need that. For most performance work, **cProfile** is the right choice.

---

## Q3. (Medium) What is __slots__ and how does it improve memory and attribute access?

**Answer:**  
**__slots__** declares a fixed set of instance attribute names; the class uses a small array instead of **__dict__**. **Memory**: no per-instance dict, so less memory for many small instances. **Access**: faster attribute lookup (no dict hash). Trade-off: no dynamic attributes, inheritance can be trickier. Use for data-heavy classes with many instances and fixed attributes.

---

## Q4. (Medium) What is a hot loop? How would you optimize a loop over a large list of numbers (e.g. sum, filter)?

**Answer:**  
A **hot loop** is a tight loop that runs very often and dominates runtime. Optimize by: (1) **Move work out** (precompute, hoist invariants). (2) **Use built-ins and libraries** — **sum()**, **numpy** (vectorized), **filter**/comprehensions. (3) **Avoid function call overhead** in the loop (inline, local refs). (4) **Use C extensions** (numpy, Cython) for numeric work. (5) **Profile first** to confirm the bottleneck.

---

## Q5. (Medium) What is Cython? When would you use it?

**Answer:**  
**Cython** is a superset of Python that compiles to C and then to a native extension. You add type annotations and C-like syntax to get speed; you can also call C code. Use when: a hot path is in Python and you need 10–100x speedup, or you’re wrapping C libraries. Good for numeric loops and algorithms that don’t fit numpy well.

---

## Q6. (Tough) How do you use tracemalloc to find memory growth or leaks?

**Answer:**  
**tracemalloc** (stdlib) tracks memory allocations. **tracemalloc.start()** then run your code; **tracemalloc.get_traced_memory()** for current size; **tracemalloc.get_object_traceback(obj)** or **snapshot** and **compare_to** to see what grew. Take snapshots before/after an operation and diff to see which allocations remained. Use to find leaks or unexpected retention.

---

## Q7. (Tough) What is the cost of function calls in Python? How can you reduce it in a tight loop?

**Answer:**  
Function calls have **overhead** (frame creation, argument passing, name lookup). Reduce by: (1) **Inline** the logic or use a **local reference**: **f = some_module.func** then call **f(x)** in the loop. (2) **Avoid calling** in the loop — build a list and call once (e.g. **map** or one batch call). (3) **Use C/numpy** for the inner loop. (4) **Cache** results if the same inputs repeat.

---

## Q8. (Tough) When would you use PyPy instead of CPython? What are the trade-offs?

**Answer:**  
**PyPy** is a JIT implementation of Python. Use for **CPU-bound** workloads where PyPy’s JIT can speed things up (often 2–10x). Trade-offs: **Compatibility** — some C extensions don’t work (CPython C API); **startup** can be slower; **memory** can differ. Best for pure-Python or PyPy-compatible stacks. For heavy numpy/C extensions, CPython is often the norm.

---

## Q9. (Tough) What is the purpose of functools.lru_cache? How does it interact with mutable arguments?

**Answer:**  
**lru_cache** memoizes return values keyed by arguments (must be hashable). **Mutable arguments** (list, dict) are not hashable, so they can’t be used as key. If you pass a tuple of hashable items, that’s fine. Don’t pass lists/dicts; use tuple or a hashable key. **maxsize** and **typed** control cache size and whether 1 and 1.0 are the same key.

---

## Q10. (Tough) How would you expose a C library to Python? Name two approaches.

**Answer:**  
(1) **Extension module** — write C (or Cython) that uses the **Python C API** (or **PyBind11**, **pybind11**); build a **.so**/**.pyd** and **import** it. (2) **ctypes** — load the **.so**/DLL and define **argtypes**/restype; call C functions from Python with no C compile step. (3) **cffi** — similar to ctypes but with a cleaner ABI/API mode. (4) **Cython** — write Python-like code and call C directly. Choose by: need for speed and API shape (Cython/pybind11) vs quick binding (ctypes/cffi).
