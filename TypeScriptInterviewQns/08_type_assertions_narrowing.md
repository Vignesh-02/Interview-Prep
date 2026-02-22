# 8. Type Assertions and Type Narrowing

## Q1. (Easy) What is a type assertion? What are the two syntaxes?

**Answer:**  
You tell the compiler “treat this as type T.” **Angle-bracket:** **`<string>value`** (avoid in JSX). **As syntax:** **`value as string`**. No runtime check; misuse can be unsafe. Use when you know more than the type system (e.g. after a runtime check or when consuming untyped data).

---

## Q2. (Easy) What is type narrowing? Name two ways to narrow.

**Answer:**  
**Narrowing** reduces a union (or broad type) to a more specific type in a branch. Ways: **typeof x === "string"**, **instanceof**, **in** operator, **truthiness**, **discriminated unions** (checking a literal property), and **type guard** functions (e.g. **function isStr(x: unknown): x is string**).

---

## Q3. (Easy) What does **typeof** narrow for? What values does it distinguish?

**Answer:**  
**typeof x** narrows to **"string" | "number" | "boolean" | "symbol" | "undefined" | "object" | "function" | "bigint"**. So **if (typeof x === "string")** narrows **x** to **string**. **typeof null** is **"object"** — so **x** might still be **null** in the object branch.

---

## Q4. (Medium) What is a type guard? What is a user-defined type guard (predicate)?

**Answer:**  
A **type guard** is an expression that narrows type in a conditional block. **User-defined**: a function that returns **x is T** (predicate). Example: **function isStr(x: unknown): x is string { return typeof x === "string" }**. Then **if (isStr(val))** narrows **val** to **string**.

---

## Q5. (Medium) When is **as** assertion unsafe? What is **double assertion**?

**Answer:**  
**as** is unsafe when the value isn’t actually that type at runtime. **Double assertion**: **x as unknown as T** — first to **unknown**, then to **T** — bypasses normal assignability. Use only when you’re sure (e.g. bridging incompatible library types). Prefer narrowing or proper types.

---

## Q6. (Medium) What is **const** assertion? What does **as const** do to an object or array?

**Answer:**  
**as const** makes the expression **readonly** and **literal**. **const a = [1, 2] as const** — type **readonly [1, 2]** (tuple of literals). **const o = { x: 1 } as const** — **{ readonly x: 1 }**. Narrows strings to literal types and makes arrays tuples when possible.

---

## Q7. (Medium) How does **in** operator narrow types?

**Answer:**  
**"prop" in obj** — if true, TypeScript can narrow **obj** to a type that has **prop** (when you have a union of types where only some have **prop**). So **if ("kind" in shape)** can narrow **shape** to the variant that has **kind**. Useful for discriminated unions and object shapes.

---

## Q8. (Tough) What is **control flow analysis**? How does it apply to **return** and **throw**?

**Answer:**  
TypeScript analyzes **control flow** (if/else, return, throw) to narrow types. After **return** or **throw**, the following code is **unreachable**; TypeScript may infer type **never** there. So in **function f(x: string | null) { if (x === null) throw new Error(); return x }**, after the throw, **x** is **string** and return type is **string**.

---

## Q9. (Tough) What is **assertion signature**? How do you type “asserts x is T”?

**Answer:**  
**asserts condition** in a function’s return type means: if the function returns, **condition** is true, and TypeScript narrows accordingly. **function assert(x: unknown): asserts x is string { if (typeof x !== "string") throw new Error() }**. After **assert(val)**, **val** is **string**. Used for assertion functions.

---

## Q10. (Tough) Why might **x as T** be wrong when **x** is **unknown**? What should you do instead?

**Answer:**  
**unknown** is safe because you must narrow before use. **x as string** bypasses that and pretends **x** is **string** with no check. Instead: narrow with **typeof**, **instanceof**, or a type guard (**isString(x)**), then use **x**. Use **as** only when you’ve already ensured the value is correct (e.g. after a guard) or when bridging external types.
