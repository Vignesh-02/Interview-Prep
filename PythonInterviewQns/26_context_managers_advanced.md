# 26. Context Managers (Advanced) and Resource Management — Senior

## Q1. (Easy) What two methods must a context manager implement? What does each do?

**Answer:**  
**__enter__(self)** — called when entering the **with** block; return value is bound to **as** (if used). **__exit__(self, exc_type, exc_val, exc_tb)** — called when leaving; receives exception info (or three Nones if no exception). Return **True** to suppress the exception; **False** or nothing to propagate. Use for setup and teardown (e.g. acquire/release lock, open/close file).

---

## Q2. (Easy) What does __exit__ receive when an exception occurred? When no exception?

**Answer:**  
When an **exception** occurred: **exc_type** (exception class), **exc_val** (instance), **exc_tb** (traceback). When **no exception**: all three are **None**. So you can do **if exc_type is not None:** to handle only the exception path. __exit__ is always called; it’s the right place to clean up.

---

## Q3. (Medium) How does contextlib.contextmanager work? What must the generator yield?

**Answer:**  
**@contextmanager** decorates a **generator**. Code **before** **yield** runs in **__enter__**; code **after** yield runs in **__exit__** (in a finally so it always runs). The **yield** value is the value of **with ... as x**. So **yield resource** makes **resource** available as the **as** target. The generator must yield exactly once.

---

## Q4. (Medium) What is contextlib.ExitStack? When would you use it?

**Answer:**  
**ExitStack** lets you manage **multiple** context managers dynamically: **with ExitStack() as stack:** then **stack.enter_context(cm)** for each. All are exited (in reverse order) when the with block ends. Use when: you don’t know how many context managers upfront, or you’re building them in a loop or from config. Replaces nested **with** when the set is dynamic.

---

## Q5. (Medium) How do you write an async context manager? What methods?

**Answer:**  
Define **__aenter__** and **__aexit__** (both **async**). Use with **async with**. Or use **@asynccontextmanager** (async generator): **async def ...; yield**. Example: **async with aiohttp.ClientSession() as session:**. The event loop drives __aenter__/__aexit__.

---

## Q6. (Tough) If __exit__ returns True, what happens to the exception? What if the caller needs to know an exception occurred?

**Answer:**  
Returning **True** from __exit__ **suppresses** the exception — it won’t propagate. The caller’s **try/except** won’t see it; code after the **with** runs as if nothing happened. So the caller **cannot** know an exception occurred if you suppress it. Only return True when you’ve fully handled the exception (e.g. logging and swallowing). Otherwise return False or nothing so the exception propagates.

---

## Q7. (Tough) Implement a reentrant (same-thread) context manager that counts enter/exit and only releases on the outermost exit.

**Answer:**
```python
class ReentrantLock:
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()
    def __enter__(self):
        if self._count == 0:
            self._lock.acquire()
        self._count += 1
        return self
    def __exit__(self, *args):
        self._count -= 1
        if self._count == 0:
            self._lock.release()
        return False
```
Only the first enter acquires; only the last exit releases.

---

## Q8. (Tough) What is contextlib.suppress? How is it implemented?

**Answer:**  
**suppress(*exceptions)** is a context manager that **catches** the listed exceptions in its __exit__ and returns **True** (suppress). So exceptions matching the list don’t propagate. Implemented by __exit__ doing something like **return type(exc_val) in self.exceptions**. Use for “expected” exceptions you want to ignore (e.g. FileNotFoundError when removing a file).

---

## Q9. (Tough) How do you ensure cleanup runs even if the user doesn’t use with? (e.g. optional context manager)

**Answer:**  
You can’t force cleanup without **with** or an explicit **close()**/dispose. Options: (1) Document that the object must be used as a context manager or **close()** called. (2) Use **weakref.finalize** to register a callback when the object is GC’d — runs at collection time (unpredictable). (3) Provide **close()** and recommend **with** or **try/finally**. Best practice: make the object a context manager and document it.

---

## Q10. (Tough) What is the difference between closing() and a regular context manager for a resource?

**Answer:**  
**contextlib.closing(thing)** is a context manager that calls **thing.close()** on exit. Use when the resource has a **close()** method but no **__enter__**/__exit__. So **with closing(urllib.urlopen(...)) as f:** ensures **f.close()** is called. For objects that already support **with** (e.g. open()), use them directly; use **closing** for legacy or minimal APIs that only have close().
