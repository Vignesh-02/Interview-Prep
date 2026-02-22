# 20. Tricky Inference and Edge Cases

## Q1. (Easy) What type does TypeScript infer for **const arr = [1, "a"]**?

**Answer:**  
**(string | number)[]** — array of string or number. For a tuple with literals, use **as const**: **const arr = [1, "a"] as const** → **readonly [1, "a"]**.

---

## Q2. (Easy) What is the inferred return type of **function f() { return 1; return "a"; }**?

**Answer:**  
**number** — the second **return** is unreachable, so it’s ignored for inference. So the return type is **number**. If both were reachable, it would be **number | string**.

---

## Q3. (Medium) What does **T extends U ? X : Y** mean in a type? When is the result **X** vs **Y**?

**Answer:**  
**Conditional type**: if **T** is assignable to **U**, the result is **X**, else **Y**. So **T extends U** is a type-level “is T a subtype of U?”. Used for conditional types (e.g. **T extends string ? T : never**). So the result is **X** when **T extends U**, **Y** otherwise.

---

## Q4. (Medium) What is the inferred type of **const fn = (x) => x** without **noImplicitAny**? With **noImplicitAny**?

**Answer:**  
Without **noImplicitAny**: **x** is **any**, return is **any**. With **noImplicitAny**: **x** has no type → error (implicit any). You must annotate: **const fn = (x: number) => x** or **<T>(x: T): T => x**.

---

## Q5. (Medium) Why might **obj[key]** have a broader type than expected? What is **noUncheckedIndexedAccess**?

**Answer:**  
**obj[key]** is typed as the **value** type of the object (e.g. **T[keyof T]**), not **T[K]** for a specific **K**, when **key** is just **string**. So you get a union of all value types. **noUncheckedIndexedAccess** adds **| undefined** to indexed access to reflect possible out-of-bounds access.

---

## Q6. (Tough) What is the type of **[]** in **const empty: number[] = []**? What about **const empty = []**?

**Answer:**  
**const empty: number[] = []** — **empty** is **number[]**. **const empty = []** — **empty** is **never[]** (no elements to infer). So **empty.push(1)** might error on **never[]** in strict inference. Prefer annotating: **const empty: number[] = []**.

---

## Q7. (Tough) In **function f<T>(x: T): T { return x }**, what is **f(null)**? What is **T**?

**Answer:**  
**f(null)** — **T** is inferred as **null**, so return type is **null**. So **const y = f(null)** gives **y** type **null**. If you want **T** to be a broader type when passing **null**, use a constraint or default: **<T = unknown>** or **T extends object**.

---

## Q8. (Tough) What is **distributive conditional type**? When does **T extends U ? X : Y** distribute over **T**?

**Answer:**  
When **T** is a **union**, a “naked” type parameter in **T extends U ? X : Y** distributes: **A | B extends U ? X : Y** becomes **(A extends U ? X : Y) | (B extends U ? X : Y)**. So each member of the union is evaluated separately. “Naked” means **T** appears as **T** directly, not inside another type like **T[]** or **() => T**. Wrapping in a tuple **[T] extends [U]** disables distribution.

---

## Q9. (Tough) What type does **keyof** give for **{ [key: string]: number }**? Why?

**Answer:**  
**string | number**. In JS, object keys are strings (or symbols); numeric keys are converted to strings. TypeScript’s **keyof** for a string index signature includes **number** because **obj[0]** is the same as **obj["0"]**. So **keyof** for **[key: string]: number** is **string | number**.

---

## Q10. (Tough) How do **interface** and **type** differ when used with **extends** in terms of error messages and assignability?

**Answer:**  
**interface A extends B** — **B** can be an interface or a type (object type). If **B** has incompatible properties, you get an error on the **extends** line. **type A = B & C** — intersection; conflicts might produce **never** or odd unions. **interface** gives a single declarative contract; **type** with **&** can express more complex combinations. For error messages, **interface extends** often gives clearer “property X is incompatible” messages than deep intersections.
