# 13. Generic Constraints

## Q1. (Easy) What does **T extends U** mean in a generic?

**Answer:**  
**T** must be **assignable to U** — i.e. **T** is a subtype of (or equal to) **U**. So **T** has at least the shape of **U**. Used to constrain **T** so you can use **U**’s properties or pass **T** where **U** is expected.

---

## Q2. (Easy) Why would you constrain **T extends { length: number }**?

**Answer:**  
So you can safely use **x.length** inside the function for any **T** that has **length**. Arrays and strings satisfy it. Lets you write one function that works for both **string** and **array** (or any array-like) while staying type-safe.

---

## Q3. (Medium) What is **T extends keyof any**? What is **keyof any**?

**Answer:**  
**keyof any** is **string | number | symbol** (the types that can be object keys). **T extends keyof any** means **T** must be a valid key type. Used when you’re building object types and **T** will be used as a key (e.g. **Record<T, V>**).

---

## Q4. (Medium) How do you constrain a generic to be an object (has string keys and values)?

**Answer:**  
**T extends object** — ensures **T** is not primitive (null, undefined, number, string, etc.). For “record-like”: **T extends Record<string, unknown>** or **T extends { [key: string]: any }**. Use **object** or **Record<string, unknown>** depending on how strict you want to be.

---

## Q5. (Medium) Can you have multiple constraints on one type parameter? **T extends A & B**?

**Answer:**  
Yes. **T extends A & B** — **T** must satisfy both **A** and **B** (intersection). So **T** is assignable to both. Example: **T extends { id: number } & { name: string }** — **T** must have **id** and **name**.

---

## Q6. (Medium) What is **T extends never**? When is it true?

**Answer:**  
**T extends never** is true only when **T** is **never** (no type extends **never** except **never** itself). Used in conditional types to filter or detect **never**. In **T extends never ? A : B**, the **A** branch is taken only for **never**.

---

## Q7. (Tough) How do you constrain **T** so that **T** has a property **id: string**?

**Answer:**  
**T extends { id: string }**. Then inside the function you can access **x.id**. For “optional id”: **T extends { id?: string }** or use a more complex conditional. For “at least id”: **T extends { id: string }** is the standard approach.

---

## Q8. (Tough) What is the difference between **T extends object** and **T extends {}**?

**Answer:**  
**object** in TypeScript means “non-primitive” (not number, string, boolean, symbol, null, undefined). **{}** is an empty object type; in TS, **{}** is assignable from almost everything except **null** and **undefined** (with strict null checks). So **T extends object** excludes primitives; **T extends {}** is a very weak constraint (only excludes null/undefined in strict mode). Prefer **T extends object** for “must be an object.”

---

## Q9. (Tough) How do you express “T must be a constructor (newable)”?

**Answer:**  
**T extends new (...args: any[]) => any** — **T** is a construct signature. For a specific instance type: **T extends new (...args: any[]) => infer R ? R : never** or **T extends new (...args: any[]) => infer R** and then use **R**. So **Ctor extends new (...args: any[]) => Instance** constrains **Ctor** to be a constructor that returns **Instance**.

---

## Q10. (Tough) In **function f<T extends string | number>(x: T)**, what can **T** be at a call site? Can **T** be **string | number**?

**Answer:**  
**T** can be **string**, **number**, or (when the argument is **string | number**) **string | number**. So **f("a")** → **T** is **string**; **f(1)** → **T** is **number**; **f(Math.random() ? "a" : 1)** → **T** is **string | number**. So yes, **T** can be the full union when the argument is the union.
