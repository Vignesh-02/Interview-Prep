# 23. Conditional Types — Senior

## Q1. (Easy) What is the syntax of a conditional type? When is the “true” branch taken?

**Answer:**  
**T extends U ? X : Y** — if **T** is assignable to **U**, the result is **X**, else **Y**. The “true” branch is taken when **T extends U** (i.e. **T** is a subtype of or equal to **U**). Used for type-level logic.

---

## Q2. (Easy) What is “distributive” conditional type? When does distribution happen?

**Answer:**  
When **T** is a **union** and **T** appears **naked** (directly, not inside another type) in **T extends U ? X : Y**, the conditional **distributes** over each member of **T**. So **A | B extends U ? X : Y** becomes **(A extends U ? X : Y) | (B extends U ? X : Y)**. So you get a union of results.

---

## Q3. (Medium) How do you **disable** distribution? Example: treat **T** as a whole.

**Answer:**  
Wrap **T** in a tuple (or another type): **[T] extends [U] ? X : Y**. Then **T** is not naked, so the conditional is applied once to the whole **T**. So **[A | B] extends [U] ? X : Y** is either **X** or **Y** once, not a union. Use when you want “if the whole union extends U” rather than “for each member.”

---

## Q4. (Medium) Write a type **IsString<T>** that is **true** if **T** is **string**, else **false** (use literal types).

**Answer:**  
**type IsString<T> = T extends string ? true : false**. So **IsString<string>** is **true**, **IsString<number>** is **false**. For **string** exactly (not **string | number**), you might use **[T] extends [string]** to avoid distribution if needed. **T extends string ? true : false** works for **string** and literal strings.

---

## Q5. (Medium) What is **T extends never ? X : Y**? What is the result?

**Answer:**  
When **T** is **never**, **never extends never** is true, so the result is **X**. But in a distributive conditional, **never** is the empty union, so the result is **never** (no members to distribute). So **T extends never ? X : Y** with **T = never** (naked) gives **never**; with **[T] extends [never] ? X : Y** and **T = never**, you get **X**.

---

## Q6. (Medium) Write **Exclude<T, U>** using a conditional type.

**Answer:**  
**type Exclude<T, U> = T extends U ? never : T**. When **T** is a union, it distributes: each member that extends **U** becomes **never**, others stay. **never** in a union disappears, so you get the union of members that don’t extend **U**.

---

## Q7. (Tough) Write a type **NonNullableKeys<T>** that is the union of keys of **T** whose value is not **null** or **undefined**.

**Answer:**  
**type NonNullableKeys<T> = { [K in keyof T]: null extends T[K] ? never : undefined extends T[K] ? never : K }[keyof T]** — but that gives **never** for optional (they extend undefined). Better: **type NonNullableKeys<T> = { [K in keyof T]: T[K] extends null | undefined ? never : K }[keyof T]** — optional props still extend **undefined**, so we exclude those. So we get keys where the value type does not extend **null | undefined**.

---

## Q8. (Tough) What is **infer** in the false branch? Is it allowed?

**Answer:**  
**infer** is allowed only in the **true** (extends) branch of a conditional type, and only in a position that would be matched when the condition is true. So **T extends (infer U)[] ? U : never** — **infer** in the “then” branch is valid. You cannot use **infer** in the “else” branch; it’s not supported. So “infer in the false branch” isn’t a thing — put the **infer** in the true branch.

---

## Q9. (Tough) Write a type **If<C, T, F>** where **C** is a boolean type (**true** | **false**), **T** when **C** is **true**, **F** when **C** is **false**.

**Answer:**  
**type If<C extends boolean, T, F> = C extends true ? T : F**. So **If<true, string, number>** is **string**, **If<false, string, number>** is **number**. Used for type-level conditionals.

---

## Q10. (Tough) Write a type **PromiseType<T>** that unwraps **Promise<T>** (single level). Then make it recursive for **Promise<Promise<T>>**.

**Answer:**  
**type PromiseType<T> = T extends Promise<infer U> ? U : T**. Single level. Recursive: **type PromiseType<T> = T extends Promise<infer U> ? PromiseType<U> : T**. So **PromiseType<Promise<Promise<number>>>** is **number**. Same idea as **Awaited<T>**.
