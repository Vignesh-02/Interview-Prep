# 28. Type-Safe Async (Promises, async/await, generics) — Senior

## Q1. (Easy) What is the type of a **Promise** in TypeScript? How do you type **Promise<string>**?

**Answer:**  
**Promise<T>** — **T** is the type of the value the promise resolves to. So **Promise<string>** is a promise that resolves to **string**. **async function f(): Promise<number>** returns **Promise<number>**. You can omit the return type and let TS infer **Promise<...>** from the return value.

---

## Q2. (Easy) What does TypeScript infer for the return type of an **async** function?

**Answer:**  
An **async** function always returns a **Promise**. The inferred return type is **Promise<T>** where **T** is the type of the value you **return** (or **Promise<void>`** if you return nothing). So **async function f() { return 1 }** has return type **Promise<number>**.

---

## Q3. (Medium) How do you type a function that returns **Promise<T>** and use **T** in the caller?

**Answer:**  
Declare return type **Promise<T>** and use **await** or **.then()` in the caller. The caller gets **T** from **await fn()` or from the **.then** callback argument. For a generic fetcher: **async function fetchJson<T>(url: string): Promise<T> { const res = await fetch(url); return res.json() }** — then **const data = await fetchJson<User>(url)** gives **data: User**.

---

## Q4. (Medium) What is the type of **await**? What about **Promise.all**?

**Answer:**  
**await p** has the type **Awaited<P>** (the unwrapped type of **P**). So **await promise** where **promise** is **Promise<number>** has type **number**. **Promise.all([p1, p2])** returns **Promise<[Awaited<P1>, Awaited<P2>]>** when given a tuple of promises — so **await Promise.all([p1, p2])** is a tuple of resolved types.

---

## Q5. (Medium) How do you type a generic “fetch and parse” function that returns **T**?

**Answer:**  
**async function fetchAs<T>(url: string): Promise<T> { const res = await fetch(url); return res.json() as Promise<T> }**. The **as Promise<T>** is a cast (**fetch**’s **json()** returns **Promise<any>**). Call with **fetchAs<User>(url)** to get **Promise<User>**. For stricter typing you might validate the response at runtime and then assert or narrow.

---

## Q6. (Medium) What is the type of a **rejected** promise? How do you type **Promise<T>** that might reject with **E**?

**Answer:**  
TypeScript’s **Promise<T>** does not model the rejection type in the type system. So **Promise<T>** only describes the resolved value. To model errors you use **Promise<T | Error>**, or a **Result** type **Promise<Result<T, E>>**, or document **E** in comments. So “reject with E” is not expressed in **Promise<T>**; you use a wrapper type or convention.

---

## Q7. (Tough) How do you type **Promise.all** so the result is a tuple with correct element types?

**Answer:**  
**Promise.all** is typed to preserve the tuple when given a tuple: **Promise.all([p1, p2] as const)** or **Promise.all([p1, p2])** where the argument is inferred as a tuple. So **const [a, b] = await Promise.all([fetchA(), fetchB()])** — **a** and **b** have the resolved types of **fetchA** and **fetchB**. If you pass **Promise.all(arr)** with **arr: Promise<unknown>[]**, the result is **Promise<unknown[]>**; use a tuple type or **as const** for the array to get a tuple result.

---

## Q8. (Tough) Write a type-safe **retry<T>** that runs **fn: () => Promise<T>** and returns **Promise<T>**.

**Answer:**  
**async function retry<T>(fn: () => Promise<T>, n: number): Promise<T> { try { return await fn() } catch (e) { if (n <= 1) throw e; return retry(fn, n - 1) } }**. Return type **Promise<T>** is preserved; the generic **T** flows from **fn**’s return type. So **retry(() => fetchUser(), 3)** returns **Promise<User>** if **fetchUser** returns **Promise<User>**.

---

## Q9. (Tough) How do you type an **async** generator (async function*)? What does it yield?

**Answer:**  
**async function* gen(): AsyncGenerator<number, void, unknown>** — yields **number**. Or let TS infer: **async function* gen() { yield 1 }** — yield type inferred. **AsyncGenerator<Y, R, N>** — yield **Y**, return **R**, next argument **N**. Use **for await (const x of gen())**; **x** has the yield type.

---

## Q10. (Tough) How do you combine **Promise<T>** with **Result** or **Either** for type-safe errors (no untyped reject)?

**Answer:**  
Instead of rejecting, return **Promise<Result<T, E>>** or **Promise<Either<L, R>>**: **type Result<T, E> = { ok: true; value: T } | { ok: false; error: E }**. Then **async function fetch(): Promise<Result<User, Error>> { try { const u = await ...; return { ok: true, value: u } } catch (e) { return { ok: false, error: e } } }**. Callers get a union type and must check **ok**; no untyped rejection. So “type-safe async” by encoding errors in the return type.
