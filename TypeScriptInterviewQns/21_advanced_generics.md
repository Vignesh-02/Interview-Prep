# 21. Advanced Generics (infer, default type params) — Senior

## Q1. (Easy) What is **infer** in a conditional type? Where can it appear?

**Answer:**  
**infer** introduces a **type variable** that TypeScript infers from a matching position. It can only appear in the **extends** clause of a conditional type, in the **true** branch. Example: **T extends (infer R)[] ? R : never** — **R** is inferred as the element type of the array. Used to “extract” a type from another type.

---

## Q2. (Easy) What does **ReturnType<T>** do? How is it implemented using **infer**?

**Answer:**  
**ReturnType<T>** extracts the return type of a function type **T**. **type ReturnType<T> = T extends (...args: any[]) => infer R ? R : any**. So **R** is inferred from the return position. **ReturnType<typeof fn>** gives the return type of **fn**.

---

## Q3. (Medium) What does **Parameters<T>** do? Write it using **infer**.

**Answer:**  
**Parameters<T>** extracts the parameter tuple of a function type. **type Parameters<T> = T extends (...args: infer P) => any ? P : never**. So **P** is the tuple of parameter types. **Parameters<typeof fn>** gives the parameter types of **fn**.

---

## Q4. (Medium) How do you give a generic a default type? Example: **type Box<T = string>**.

**Answer:**  
**type Box<T = string> = { value: T }**. When **Box** is used without a type argument, **T** is **string**. **function f<T = number>(x: T)** — **T** defaults to **number** when inference doesn’t provide it. Defaults are used when the type argument is omitted and can’t be inferred.

---

## Q5. (Medium) What is **infer** in a union? Does **T extends (infer U)[]** distribute over a union **T**?

**Answer:**  
**infer** is used inside a conditional type; it doesn’t “distribute over union” by itself. When **T** is a union and you have **T extends (infer U)[] ? U : never**, the conditional **distributes** over **T** (naked **T**), so you get **U** for each union member that is an array type, then a union of those **U**s. So **(string[] | number[]) extends (infer U)[] ? U : never** → **string | number**.

---

## Q6. (Medium) Write a type that extracts the first parameter of a function.

**Answer:**  
**type FirstParam<T> = T extends (first: infer F, ...args: any[]) => any ? F : never**. Or use **Parameters<T>[0]** — **type FirstParam<T> = Parameters<T> extends [infer F, ...any[]] ? F : never**. So **FirstParam<typeof fn>** is the type of the first argument.

---

## Q7. (Tough) What is **InstanceType<T>**? Write it with **infer**.

**Answer:**  
**InstanceType<T>** extracts the instance type of a constructor type **T**. **type InstanceType<T> = T extends new (...args: any[]) => infer R ? R : any**. So **R** is the type constructed by **new T()**. **InstanceType<typeof MyClass>** is the instance type of **MyClass**.

---

## Q8. (Tough) How do you infer from a nested position? Example: extract the type of **data** from **Promise<{ data: T }>**.

**Answer:**  
**type Data<T> = T extends Promise<{ data: infer D }> ? D : never**. So **infer D** captures the type of **data** when **T** matches **Promise<{ data: ... }>**. You can chain: **T extends SomeShape<infer D> ? D : never**.

---

## Q9. (Tough) What happens when **infer** appears in multiple positions? Example: **T extends { a: infer A; b: infer B } ? [A, B] : never**.

**Answer:**  
TypeScript infers **A** and **B** from the respective positions when **T** matches the shape. So for **T = { a: string; b: number }**, you get **[string, number]**. All **infer** positions are inferred together from the same **T**; they must be consistent (same match).

---

## Q10. (Tough) Write a generic type **Awaited<T>** that unwraps **Promise<T>** (and optionally **Promise<Promise<T>>**).

**Answer:**  
**type Awaited<T> = T extends Promise<infer U> ? Awaited<U> : T**. So **Awaited<Promise<Promise<number>>>** is **number** (recursive unwrap). TS 4.5+ has built-in **Awaited<T>** that also handles **thenable**-like types. The recursive form handles nested promises.
