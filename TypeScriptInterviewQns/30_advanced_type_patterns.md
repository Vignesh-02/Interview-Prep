# 30. Advanced Type Patterns (branded types, type-level programming) — Senior

## Q1. (Easy) What is a **branded** (or **nominal**) type? Why is it useful?

**Answer:**  
A **branded type** is a type that is structurally identical to another but treated as distinct. Example: **type UserId = string & { readonly brand: unique symbol }**. So **UserId** is a **string** at runtime but not assignable from a plain **string** without a cast. Used to prevent mixing IDs (e.g. **UserId** vs **OrderId**) or to enforce “validated” vs “raw” at the type level.

---

## Q2. (Easy) How do you create a branded type in TypeScript? (minimal example)

**Answer:**  
**type Brand<T, B> = T & { readonly __brand: B }**. Then **type UserId = Brand<string, "UserId">**. Or with **unique symbol**: **type UserId = string & { readonly __brand: unique symbol }** and **const userId = (id: string) => id as UserId**. The **__brand** property is never present at runtime; it’s type-only.

---

## Q3. (Medium) What is **unique symbol**? How is it used in branded types?

**Answer:**  
**unique symbol** is a type for values created with **Symbol()** or **Symbol.for()**; each symbol type is unique. So **const U = Symbol(); type B = string & { [U]: true }** — the brand is keyed by a unique symbol so it doesn’t collide with other brands. **readonly __brand: unique symbol** in a type makes the brand nominal and unique.

---

## Q4. (Medium) What is a **type-level** computation? Give an example (e.g. **Length** of a tuple).

**Answer:**  
Type-level computation uses **conditional types**, **infer**, **mapped types**, and **recursion** to compute types. Example: **type Length<T extends readonly any[]> = T["length"]** — **Length<[1,2,3]>** is **3**. Or recursive: **type Length<T> = T extends readonly [any, ...infer R] ? 1 + Length<R> : 0** (with **Length** in the RHS). No runtime code; only types.

---

## Q5. (Medium) What is **TupleToUnion<T>**? Write it.

**Answer:**  
**type TupleToUnion<T extends readonly any[]> = T[number]** — **T[number]** is the union of all element types. So **TupleToUnion<["a", "b", "c"]>** is **"a" | "b" | "c"**. Or **T extends (infer U)[] ? U : never** for a tuple **T**.

---

## Q6. (Medium) What is **DeepReadonly<T>**? Sketch it with a conditional and mapped type.

**Answer:**  
**type DeepReadonly<T> = T extends object ? { readonly [P in keyof T]: DeepReadonly<T[P]> } : T**. So primitives stay as-is; objects (and arrays) get all keys readonly and recursively **DeepReadonly** for values. Refinements: exclude **Function** or use **T extends object & ({} | [])** to avoid making functions readonly in a weird way if desired.

---

## Q7. (Tough) How do you implement **Equals<A, B>** that is **true** if **A** and **B** are the same type, else **false**?

**Answer:**  
**type Equals<A, B> = (<T>() => T extends A ? 1 : 2) extends (<T>() => T extends B ? 1 : 2) ? true : false**. Uses the fact that conditional types are checked with a fresh type parameter; if **A** and **B** are identical, the two function types are the same. So **Equals<string, string>** is **true**; **Equals<string, number>** is **false**.

---

## Q8. (Tough) What is a **recursive type alias**? What limit does TypeScript have?

**Answer:**  
A type that references itself, e.g. **type Json = string | number | boolean | null | Json[] | { [key: string]: Json }**. TypeScript allows recursive type aliases (with a depth limit to avoid infinite expansion). So **Json** describes JSON-compatible values. The limit is implementation-defined (roughly 50 levels or so); very deep recursion can cause slow checks or errors.

---

## Q9. (Tough) How do you type “array that has at least one element” (non-empty array)?

**Answer:**  
**type NonEmptyArray<T> = [T, ...T[]]** — at least one **T**, then zero or more. Or **type NonEmptyArray<T> = T[] & { 0: T }** (intersection with “has index 0”). So **[T, ...T[]]** is the common pattern; **function first<T>(arr: [T, ...T[]]): T { return arr[0] }** ensures non-empty and returns **T**.

---

## Q10. (Tough) What is **noInfer** or “don’t infer this type parameter” and how can you simulate it?

**Answer:**  
Sometimes you want a type parameter to be inferred from one place but not participate in inference elsewhere. TS 4.7+ has **NoInfer<T>** in some scenarios. To simulate: use **T** in a position that doesn’t contribute to inference (e.g. **T extends unknown ? ... : never** or a conditional that “hides” **T** from inference). Or use a default: **function f<T, U = NoInfer<T>>(x: T, y: U)** so **U** is inferred from **y** only and not from **T**. **NoInfer<T>** (when available) is a built-in helper that prevents **T** from being inferred from certain positions.
