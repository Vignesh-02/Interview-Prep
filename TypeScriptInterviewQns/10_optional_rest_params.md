# 10. Optional, Default, and Rest Parameters

## Q1. (Easy) What is the type of an optional parameter **x?: number**?

**Answer:**  
**number | undefined**. Callers can omit it or pass **undefined**. Inside the function, **x** has type **number | undefined** unless you narrow.

---

## Q2. (Easy) What is the type of a rest parameter **...args: number[]**?

**Answer:**  
**args** is **number[]** — array of all remaining arguments. So **function f(...args: number[])** — **args** has type **number[]**. For mixed types you’d use **...args: (string | number)[]** or a tuple type for variadic typing.

---

## Q3. (Easy) Can you put a required parameter after an optional one?

**Answer:**  
No. Optional and default parameters must come **after** required parameters. So **function f(a?: number, b: string)** is invalid; use **function f(b: string, a?: number)** or give **a** a default.

---

## Q4. (Medium) What is the difference between **x?: number** and **x: number | undefined** for a parameter?

**Answer:**  
**x?: number** — callers can **omit** the argument (**f()**) or pass **undefined**. **x: number | undefined** — callers **must** pass an argument; it can be **undefined** (**f(undefined)**). So **?** allows omission; **| undefined** does not. With **strictOptionalParameters** (or similar), the distinction is enforced.

---

## Q5. (Medium) How do you type a function that accepts one string and then any number of numbers?

**Answer:**  
**`function f(first: string, ...rest: number[]) { }`**. **rest** is **number[]**. For a tuple of at least one number: **...rest: [number, ...number[]]** if you need “one or more.”

---

## Q6. (Medium) What is the inferred type of **args** in **function f(...args: [string, number])**?

**Answer:**  
**args** is the tuple **[string, number]** — exactly two arguments. So **f("a", 1)** is valid; **f("a")** or **f("a", 1, 2)** are not. Used for fixed-arity overload-like typing with rest.

---

## Q7. (Medium) Can a rest parameter be typed as a tuple? When is that useful?

**Answer:**  
Yes: **function f(...args: [string, number, ...boolean[]]) { }**. Useful for **variadic tuple types** — e.g. “first two args are string and number, then any number of booleans,” or for type-safe spread/forwarding with preserved tuple types.

---

## Q8. (Tough) What happens to **this** in the type of a function with a rest parameter? How do you type **this**?

**Answer:**  
**this** is typed with a **this** parameter (fake first parameter): **function f(this: Context, ...args: number[]) { }**. **this** doesn’t count as a rest argument; it’s only for typing. So the call signature is **(this: Context, ...args: number[]) => ...**.

---

## Q9. (Tough) How do you type “optional rest” — i.e. either no extra args or one or more of type T?

**Answer:**  
**...args: T[]** allows zero or more. For “one or more”: **...args: [T, ...T[]]** — at least one. For “zero or one”: **arg?: T** (single optional). So “optional rest” as “maybe some” is just **...args: T[]** (zero or more); “at least one” needs a tuple.

---

## Q10. (Tough) In an overloaded function with optional/rest, what rule does TypeScript use for which overload to pick?

**Answer:**  
TypeScript picks the **first** overload whose parameter list is **compatible** with the call. So order matters: put more specific overloads (e.g. with more required args) before more general ones (optional/rest). The implementation signature must be compatible with all overloads (usually a union of parameter types and return type).
