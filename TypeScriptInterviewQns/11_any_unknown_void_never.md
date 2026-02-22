# 11. any, unknown, void, and never

## Q1. (Easy) What is **any**? Why is it unsafe?

**Answer:**  
**any** opts out of type checking. You can read any property, call it as a function, assign to/from anything. No type errors. Unsafe because mistakes are not caught; use only when necessary (e.g. migrating JS or typing external data before narrowing). Prefer **unknown** when you don’t know the type.

---

## Q2. (Easy) What is **unknown**? How do you use it safely?

**Answer:**  
**unknown** is the type-safe counterpart of **any**. You can’t use a value of type **unknown** without first **narrowing** (typeof, instanceof, type guard) or asserting. So **let x: unknown = get(); x.toUpperCase()** errors; **if (typeof x === "string") x.toUpperCase()** is valid. Use for values from outside your type system.

---

## Q3. (Easy) What is **void**? When is it used?

**Answer:**  
**void** means “no useful return value.” Used as function return type when the function returns **undefined** or nothing. You can still **return undefined** or **return;**; **void** tells callers to ignore the result. **void** in type position is **undefined** (or a special void type depending on context).

---

## Q4. (Medium) What is **never**? When does a function return **never**?

**Answer:**  
**never** is the type with **no values**. A function returns **never** when it **never** returns normally — it always throws or runs an infinite loop. So **function fail(): never { throw new Error() }**. Used in exhaustive checks and in conditional types (e.g. **never** in a union “disappears”).

---

## Q5. (Medium) What is the difference between **any** and **unknown** for assignment?

**Answer:**  
**any** is assignable **to** and **from** anything. **unknown** is assignable **from** anything, but you can only assign **unknown** to **unknown** or **any** (until you narrow). So **let a: any = x** and **let b: any = y** always work; **let u: unknown = x** works; **let s: string = u** errors until you narrow **u**.

---

## Q6. (Medium) When would you explicitly annotate **void** vs let the compiler infer?

**Answer:**  
Annotate **void** when the function might otherwise be inferred to return **undefined** or a more specific type and you want to signal “ignore return.” Callbacks (e.g. **() => void**) often use **void** so the caller isn’t required to use the return value. Let the compiler infer when the intent is clear.

---

## Q7. (Medium) How is **never** used in exhaustive switch/union checks?

**Answer:**  
In a switch on a union, if you’ve handled all cases, the **default** branch should never run. Type the default with **never**: **default: const _: never = x; return _;** — if you add a new union member and forget a case, **x** in default is not **never** and you get a type error. So **never** ensures exhaustiveness.

---

## Q8. (Tough) What is the type of **void** in a conditional type? Is **void** assignable to **undefined**?

**Answer:**  
In **strict** mode, **void** as a return type is distinct; in some contexts **void** and **undefined** are treated similarly for assignability. **undefined** is assignable to **void**. A function typed **() => void** can return **undefined**; the caller’s type is **void** (ignored). So they’re related but **void** is the “no value” contract.

---

## Q9. (Tough) Why might **never** appear as an inferred type? (e.g. in an array or after a return)

**Answer:**  
**never** is inferred when TypeScript concludes no value can exist there. Examples: empty array **[]** with no context can be **never[]**; code after **return** or **throw** is **never**; the **default** in an exhaustive switch when **x** is **never**. So **never** means “unreachable” or “empty.”

---

## Q10. (Tough) How do you type “function that may throw” vs “function that never returns”? Return type of both?

**Answer:**  
A function that **may throw** still has a normal return type (e.g. **string**); the type system doesn’t model thrown exceptions. A function that **never returns** (only throws or loops) has return type **never**. So **function fail(): never { throw new Error() }** — **never**; **function parse(): string { ... throw ... }** — **string** (throw doesn’t change return type).
