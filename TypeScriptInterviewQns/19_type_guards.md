# 19. Type Guards and Error Handling

## Q1. (Easy) What is a type guard? Name two built-in ways to narrow.

**Answer:**  
A **type guard** is an expression that narrows the type in a conditional block. Built-in: **typeof x === "string"** (narrows to **string**), **instanceof C** (narrows to **C** or subclass), **x === null**, **"prop" in x**. Control flow (if/return) uses these to narrow.

---

## Q2. (Easy) What is a user-defined type guard (type predicate)? Give the syntax.

**Answer:**  
A function whose return type is **x is T**: **function isString(x: unknown): x is string { return typeof x === "string" }**. When you use **if (isString(val))**, TypeScript narrows **val** to **string** in the true branch. The function must return **boolean**; the **x is T** tells the compiler how to narrow.

---

## Q3. (Easy) How do you narrow **unknown** to a specific type before use?

**Answer:**  
Use **typeof**, **instanceof**, or a type guard: **if (typeof x === "string") { x.toUpperCase() }**, or **function isStr(x: unknown): x is string { return typeof x === "string" }** then **if (isStr(x)) { ... }**. Or **assertion** after a runtime check: **if (isValid(x)) { use(x as T) }**. Prefer guards over bare assertions.

---

## Q4. (Medium) What is **asserts condition** (assertion signature)? How does it narrow?

**Answer:**  
**function assert(condition: unknown): asserts condition** — if the function returns, **condition** is true (and TypeScript narrows using it). **function assertIsString(x: unknown): asserts x is string { if (typeof x !== "string") throw new Error() }** — after **assertIsString(val)**, **val** is **string**. Used for assertion helpers.

---

## Q5. (Medium) How do you narrow a union with a discriminant? Example.

**Answer:**  
Check the discriminant property: **type Shape = { kind: "circle"; r: number } | { kind: "rect"; w: number; h: number }**. **if (s.kind === "circle")** narrows **s** to the circle variant so **s.r** is available. Use a common literal property (**kind**, **type**, etc.) as the discriminant.

---

## Q6. (Medium) What is **in** operator narrowing?

**Answer:**  
**"prop" in obj** — if true, TypeScript can narrow **obj** to a type that has **prop** (when **obj** is a union and only some variants have **prop**). So **if ("tag" in x)** can narrow **x** to the variant with **tag**. Useful for discriminated unions and object shapes.

---

## Q7. (Tough) How do you type a **catch** clause? What type does **e** have by default?

**Answer:**  
In **catch (e)**, **e** is **unknown** (TS 4.4+ with **useUnknownInCatchVariables** or **strict**). You must narrow before use: **if (e instanceof Error) { e.message }** or **if (e instanceof Error) throw e; throw new Error(String(e))**. Don’t assume **e** is **Error**; narrow or rethrow.

---

## Q8. (Tough) Write a type guard that checks if a value is an object with a property **id: string**.

**Answer:**
```ts
function hasId(x: unknown): x is { id: string } {
  return typeof x === "object" && x !== null && "id" in x && typeof (x as { id: unknown }).id === "string";
}
```
Or use a type assertion after the checks: **x is { id: string }**. Ensure **x** is object, not null, and **id** is string.

---

## Q9. (Tough) What is “narrowing from truthiness”? When can it backfire?

**Answer:**  
Using **if (x)** or **if (!x)** narrows: **false**, **0**, **""**, **null**, **undefined**, **NaN** are falsy; truthy branch excludes them. So **if (x) { }** can narrow **x** from **string | null** to **string**. Backfire: **0** or **""** are valid values; narrowing them out might be wrong. Use **x != null** or **x !== undefined** when you only want to exclude null/undefined.

---

## Q10. (Tough) How do you implement exhaustive checking for a union with a switch? What type do you use in **default**?

**Answer:**  
**switch (x) { case "a": ... break; case "b": ... break; default: const _: never = x; return _; }**. In **default**, **x** should be **never** if all cases are handled. If you add a new union member and forget a case, **x** in default is not **never** and you get a type error. So **never** in default enforces exhaustiveness.
