# 4. Functions and Function Types

## Q1. (Easy) How do you type a function’s parameters and return type?

**Answer:**  
**`function add(a: number, b: number): number { return a + b }`** or **`const add = (a: number, b: number): number => a + b`**. Return type can be inferred; explicit return type helps catch errors. **`(a: number, b: number) => number`** is the function type.

---

## Q2. (Easy) What is an optional parameter? How does it affect the type?

**Answer:**  
**`function f(x: number, y?: number)`** — **y** is optional. Its type is **number | undefined**. Callers can omit it: **f(1)** or **f(1, 2)**. Optional must come after required parameters (or use a default).

---

## Q3. (Easy) What is a default parameter? How is it typed?

**Answer:**  
**`function f(x: number, y = 0)`** — **y** defaults to **0**; TypeScript infers **y** as **number** (not **number | undefined** for the caller, because default is supplied). So **f(1)** is valid and **y** is **0** inside.

---

## Q4. (Medium) How do you type a function that accepts a callback? What about the callback’s parameters?

**Answer:**  
**`function run(cb: (x: number) => string) { return cb(1) }`**. The callback type is **(x: number) => string**. You can name the parameter: **(value: number) => string**. For optional callback params, use **?** or **| undefined**.

---

## Q5. (Medium) What is the difference between **function** type syntax and **=>** in a type? (e.g. `(x: number) => string` vs `{ (x: number): string }`)

**Answer:**  
**`(x: number) => string`** is the usual callable type. **`{ (x: number): string }`** is an object type with a **call signature** (same call shape). For a single call signature they behave the same; the object form allows adding properties (e.g. **{ (): void; id: string }**).

---

## Q6. (Medium) What is **this** parameter? How do you type it?

**Answer:**  
**this** parameter is a fake first parameter that types **this** inside the function: **`function f(this: SomeObj, x: number) { }`**. It’s not an argument at call site; it only affects typing. Used so that **this** is correctly typed when the function is used as a method or with **call/apply**.

---

## Q7. (Medium) Can you overload functions in TypeScript? How?

**Answer:**  
Yes, with **overload signatures** (no body) followed by one **implementation** signature (with body). Overloads are the callable signatures; implementation must be compatible. Example: **function f(x: string): string; function f(x: number): number; function f(x: string | number): string | number { return x }**. Callers see the overloads; implementation handles the union.

---

## Q8. (Tough) What does TypeScript infer for the return type of a function that has multiple return paths (e.g. string and number)?

**Answer:**  
Inferred return type is the **union** of all return types, e.g. **string | number**. If you want a specific overload, use explicit overload signatures. Without overloads, the implementation’s inferred return is the union of every return statement.

---

## Q9. (Tough) How do you type a method that can be called with different argument counts (e.g. one arg or two args)?

**Answer:**  
Use **overloads**: **f(a: number): void; f(a: number, b: string): void; f(a: number, b?: string): void { }**. Or a single signature with optional/second parameter: **f(a: number, b?: string)**. Overloads give precise typing per call shape.

---

## Q10. (Tough) What is **strictFunctionTypes**? How does it affect callback parameter types?

**Answer:**  
**strictFunctionTypes** makes function parameter types checked **contravariantly** (and return types covariantly). So a callback that accepts **Animal** cannot be passed where **(x: Dog) => void** is expected (because the callee might pass a Dog and the callback could use Dog-only members). With it off, parameters are bivariant (unsafe). Enable it for type-safe callbacks.
