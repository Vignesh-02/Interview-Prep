# 23. Async/Await and Asyncio — Senior

## Q1. (Easy) What is asyncio? What problem does it solve?

**Answer:**  
**asyncio** is Python’s library for **asynchronous I/O** and **concurrency** using an event loop. It solves **I/O-bound** concurrency: many tasks can wait on network/file/database without blocking the process. One thread runs the loop; tasks **cooperate** by yielding at **await** points. No threads needed for high concurrency of I/O.

---

## Q2. (Easy) What is the difference between async and sync functions? What does await do?

**Answer:**  
**async def** defines a **coroutine**; calling it returns a coroutine object (it doesn’t run until awaited or scheduled). **await** pauses the coroutine until the awaited **awaitable** (e.g. another coroutine, a Future) completes; control goes back to the event loop. So **await** means “pause here until this is done; let others run.”

---

## Q3. (Medium) How do you run an async function from synchronous code? What does asyncio.run() do?

**Answer:**  
Use **asyncio.run(main())** — it creates an event loop, runs the given coroutine until it completes, and closes the loop. It’s the main entry point from sync code (e.g. in **if __name__ == "__main__"**). Don’t nest run(); use one loop per “app.” In older code you might see **loop.run_until_complete(main())**.

---

## Q4. (Medium) What is a Future? How does it relate to a Task?

**Answer:**  
A **Future** is a low-level awaitable representing a result that may not be ready yet. A **Task** is a **Future** that wraps a coroutine and schedules it on the event loop. **asyncio.create_task(coro)** creates a Task and starts running the coroutine; you can await it or let it run in the background. Tasks are the main way to run multiple coroutines concurrently.

---

## Q5. (Medium) What happens if you await a coroutine without scheduling it (e.g. just await coro())? What about create_task?

**Answer:**  
**await coro()** runs the coroutine until it finishes; you’re not running anything else concurrently unless that coroutine awaits something. **create_task(coro())** schedules the coroutine on the loop and returns a Task; the coroutine runs **concurrently** with the current one. So use **create_task** when you want “fire and forget” or true concurrency; **await coro()** when you want to run one after another (or the only one).

---

## Q6. (Medium) What is asyncio.gather? When would you use it?

**Answer:**  
**asyncio.gather(*awaitables)** runs multiple awaitables **concurrently** and returns a list of results (in order). If one raises, gather raises by default; **return_exceptions=True** collects exceptions as results. Use when you have several independent async operations and want to wait for all and get all results.

---

## Q7. (Tough) Why can’t you use blocking I/O (e.g. time.sleep, requests.get) inside an async function without special handling?

**Answer:**  
**Blocking** calls hold the **thread** (and the event loop runs on that thread), so the whole loop is stuck and no other task runs. Use **await asyncio.sleep(1)** instead of **time.sleep(1)**; use **aiohttp** or **httpx** (async) instead of **requests**. If you must call blocking code, run it in **executor**: **await loop.run_in_executor(None, blocking_func)**.

---

## Q8. (Tough) What is an async context manager? How do you define and use one?

**Answer:**  
An async context manager supports **async with**: it has **__aenter__** and **__aexit__** (both async). Use **async with** to enter and exit. Define with **@contextlib.asynccontextmanager** (async generator) or a class with **__aenter__**/__aexit__. Example: **async with aiohttp.ClientSession() as session:**.

---

## Q9. (Tough) What is asyncio.Lock? When would you use it in async code?

**Answer:**  
**asyncio.Lock** is a **mutex** for async code: **async with lock:** ensures only one coroutine holds the lock at a time. Use when shared state is accessed from multiple coroutines and you need mutual exclusion. Unlike threading locks, it doesn’t block the thread — it yields to the event loop so other coroutines can run while waiting.

---

## Q10. (Tough) How do you run both sync and async code in the same application (e.g. legacy sync library and asyncio)?

**Answer:**  
(1) Run sync in a **thread pool**: **await loop.run_in_executor(executor, sync_func, arg)** so it doesn’t block the loop. (2) Run the event loop in a **thread** and call **asyncio.run_coroutine_threadsafe(coro, loop)** from sync code to submit work. (3) Wrap sync APIs in async with **run_in_executor** so the rest of the app stays async. Avoid blocking the loop from async code.
