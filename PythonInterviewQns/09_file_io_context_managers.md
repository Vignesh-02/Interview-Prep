# 9. File I/O and Context Managers (with)

## Q1. (Easy) How do you open a file for reading? What is the default encoding?

**Answer:**  
**`open(path)`** or **`open(path, 'r')`** — opens for text reading. Default encoding is **platform-dependent** (often utf-8 on modern systems). Prefer **`open(path, encoding='utf-8')`** for portability. Always close the file or use `with`.

---

## Q2. (Easy) What does the `with` statement do? Why use it instead of open/close by hand?

**Answer:**  
**`with open(...) as f:`** ensures the file is **closed** when the block is left (normally or by exception). It calls `f.__enter__()` at the start and `f.__exit__(...)` on exit. So you avoid leaking file handles and don’t need a try/finally.

---

## Q3. (Easy) What is the difference between `'r'`, `'w'`, and `'a'`? What does `'r+'` mean?

**Answer:**  
**r** — read (file must exist). **w** — write (truncates if exists). **a** — append (creates if not exists; writes at end). **r+** — read and write; file must exist; position at start. **w+** truncates; **a+** positions at end for read/write.

---

## Q4. (Medium) What does `f.read()` return? What about `f.readline()` and `f.readlines()`?

**Answer:**  
**read()** — entire file as one string (or bytes in binary mode). **readline()** — one line (including `\n`), or `""` at EOF. **readlines()** — list of lines. For large files, iterate the file object: **`for line in f:`** — memory-efficient, one line at a time.

---

## Q5. (Medium) What is a context manager? Name the two methods it must support.

**Answer:**  
A **context manager** is an object used with `with`. It must support **`__enter__(self)`** (called when entering the block; return value is bound to `as`) and **`__exit__(self, exc_type, exc_val, exc_tb)`** (called when leaving; return True to suppress the exception).

---

## Q6. (Medium) How do you write a context manager using a generator and `contextlib.contextmanager`?

**Answer:**
```python
from contextlib import contextmanager

@contextmanager
def my_cm():
    # __enter__: code before yield
    resource = setup()
    try:
        yield resource
    finally:
        # __exit__: code after yield
        cleanup(resource)
```
What’s before `yield` runs on enter; what’s after (in finally) runs on exit. The value after `yield` is the value of `with ... as x`.

---

## Q7. (Medium) What does `open(path, 'rb')` return? When do you use binary mode?

**Answer:**  
**Binary mode** (`'rb'`, `'wb'`, `'ab'`) returns **bytes**, not str. No encoding/decoding. Use for images, executables, or when you must read exact bytes. Use text mode (`'r'`, `'w'`) when you want strings and need encoding (e.g. utf-8).

---

## Q8. (Tough) What happens if an exception is raised inside a `with` block? Does the file still get closed?

**Answer:**  
Yes. The context manager’s **`__exit__`** is called when leaving the block, including when an exception is raised. The file object’s `__exit__` closes the file. If you need to handle the exception, catch it inside the block or let it propagate after `__exit__` (unless `__exit__` returns True to suppress it).

---

## Q9. (Tough) Write a simple context manager class that measures the time spent inside the block.

**Answer:**
```python
import time

class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
        return False  # do not suppress exceptions
```
Usage: `with Timer() as t: ...; print(t.elapsed)`.

---

## Q10. (Tough) What is `contextlib.suppress`? When would you use it?

**Answer:**  
**`contextlib.suppress(*exceptions)`** is a context manager that **suppresses** the listed exceptions if they occur in the block. Use when you expect an exception and want to ignore it (e.g. `with suppress(FileNotFoundError): os.remove(path)`). Cleaner than a bare try/except/pass.
