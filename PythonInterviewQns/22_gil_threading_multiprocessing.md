# 22. GIL, Multithreading, and Multiprocessing — Senior

## Q1. (Easy) What is the GIL? Where does it live?

**Answer:**  
The **Global Interpreter Lock (GIL)** is a mutex in CPython that protects access to Python objects. Only one thread can **execute Python bytecode** at a time (per interpreter). So even with multiple threads, only one runs Python code at once. It lives in the CPython interpreter; it’s released during I/O and in some C extensions (e.g. numpy when doing heavy computation in C).

---

## Q2. (Easy) What is the main impact of the GIL on CPU-bound multithreaded code?

**Answer:**  
**CPU-bound** threads (doing lots of Python bytecode or CPU work that holds the GIL) cannot run in parallel on multiple cores — they take turns. So you don’t get a speedup from adding more threads for pure Python CPU work. Use **multiprocessing** (separate processes, each with its own GIL) for CPU-bound parallelism.

---

## Q3. (Medium) When is multithreading still useful despite the GIL?

**Answer:**  
Useful when threads spend time **waiting** (I/O, network, sleep, or in C code that releases the GIL). While one thread waits, another can run. So **I/O-bound** programs (web servers handling many connections, file I/O, APIs) can benefit from threads. Concurrency comes from overlapping I/O, not from parallel CPU execution.

---

## Q4. (Medium) What is the difference between threading and multiprocessing in Python?

**Answer:**  
**threading** — multiple **threads** in the **same process**; share memory; limited by the GIL for CPU work. **multiprocessing** — multiple **processes**; separate memory (or explicit shared memory); **no** GIL between processes; true CPU parallelism. Use threading for I/O-bound; use multiprocessing for CPU-bound when you need more cores.

---

## Q5. (Medium) How do you create a thread? How do you wait for it to finish?

**Answer:**  
**`threading.Thread(target=func, args=(a, b))`** then **`t.start()`**. Wait: **`t.join()`**. Or subclass **Thread** and override **run()**. Prefer **concurrent.futures.ThreadPoolExecutor** for a pool and **future.result()** to wait and get the return value.

---

## Q6. (Medium) What are common pitfalls with shared state in threads? What is a race condition?

**Answer:**  
**Race condition** — two threads read/write the same data without synchronization; outcome depends on timing. Pitfalls: non-atomic operations (e.g. read-modify-write), inconsistent state visible to another thread. Use **locks** (**threading.Lock**), or avoid shared mutable state (e.g. pass results via queues). Prefer **thread-safe** data structures or explicit synchronization.

---

## Q7. (Tough) How does multiprocessing pass data between processes? What are the options and trade-offs?

**Answer:**  
Processes have **separate memory**. Options: (1) **Pickle** — arguments and return values of pool methods are serialized; simple but can be slow and not everything is picklable. (2) **multiprocessing.Queue** or **Pipe** — send pickled objects. (3) **shared memory** — **multiprocessing.shared_memory** (3.8+) or **multiprocessing.Array/Value** for raw shared memory. Trade-off: serialization cost vs complexity of shared memory and synchronization.

---

## Q8. (Tough) What is a daemon thread? When would you use one?

**Answer:**  
A **daemon thread** (**thread.daemon = True** before start) does not prevent the process from exiting. When all non-daemon threads are done, the process exits and daemon threads are killed mid-run. Use for **background** tasks that can be abandoned (e.g. a watchdog, logging flusher). Don’t use when the thread must finish or clean up.

---

## Q9. (Tough) Why might a C extension release the GIL? How does that affect threading?

**Answer:**  
A C extension can **release the GIL** during long-running computation (e.g. numpy doing array math in C). While released, **other threads** can run Python code. So CPU-bound work in such extensions can run in parallel with other threads. That’s why numpy can get speedup with threads for heavy array operations.

---

## Q10. (Tough) Compare threading, multiprocessing, and asyncio. When would you choose each?

**Answer:**  
**threading** — I/O-bound; many concurrent connections/tasks; shared memory; GIL limits CPU parallelism. **multiprocessing** — CPU-bound; need multiple cores; isolation; no GIL between processes; higher overhead. **asyncio** — I/O-bound; single-threaded event loop; cooperative multitasking; no GIL issues; great for many network/file I/O tasks. Choose by: CPU-bound → multiprocessing; I/O-bound with shared state or legacy APIs → threading; I/O-bound and async-friendly → asyncio.
