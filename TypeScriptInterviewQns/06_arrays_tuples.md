# 6. Arrays, Tuples, and Iteration

## Q1. (Easy) What is the type of an empty array `[]`? How do you type a non-empty array?

**Answer:**  
**[]** is inferred as **never[]** in strict settings (no elements to infer). Type it: **`const a: number[] = []`** or **`const a: number[] = [1, 2, 3]`**. **Array<number>** is equivalent to **number[]**.

---

## Q2. (Easy) What is a tuple type? How do you define one?

**Answer:**  
A **tuple** is a fixed-length array with known types per index: **`type Pair = [string, number]`** — first element string, second number. **`const p: Pair = ["a", 1]`**. Optional/rest elements: **`[string, number?]`** or **`[string, ...number[]]**.

---

## Q3. (Easy) What is the type of **arguments** in a function? How do you type it if needed?

**Answer:**  
**arguments** is the legacy array-like object. TypeScript types it loosely. To type: **function f(...args: number[]) { }** and use **args** instead, or **function f() { const args: IArguments = arguments }**. Prefer **rest parameters** (**...args**) for proper typing.

---

## Q4. (Medium) What is a read-only tuple? How do you create one?

**Answer:**  
**readonly [string, number]** or **Readonly<[string, number]>**. **as const** makes the tuple (and its elements) readonly literals: **`const t = ["a", 1] as const`** — type **readonly ["a", 1]**. Use for fixed-length, immutable data.

---

## Q5. (Medium) What is the difference between **Array<T>** and **T[]**? Are they the same?

**Answer:**  
They are the **same** for one dimension. **T[][]** and **Array<Array<T>>** are the same. **Array<T>** is generic and can be used in type expressions like **Array<string | number>**. No semantic difference for typing.

---

## Q6. (Medium) How do you type a function that returns an array of a generic type?

**Answer:**  
**`function toArray<T>(x: T): T[] { return [x] }`** or **`: Array<T>`**. Return type **T[]** means “array of whatever T is.” For tuples: **`function pair<T, U>(a: T, b: U): [T, U] { return [a, b] }`**.

---

## Q7. (Medium) What is a rest parameter in a tuple? Example: `[string, ...number[]]`

**Answer:**  
**...[number[]]** in a tuple type means “zero or more numbers after the first element.” So ** [string, ...number[]]** is “string followed by any number of numbers.” Used for variadic tuple types. **...T[]** is the “rest” of the tuple.

---

## Q8. (Tough) What is **readonly** on an array type? Can you assign a mutable array to a readonly array?

**Answer:**  
**readonly number[]** or **ReadonlyArray<number>** — no **push**, **pop**, or assignment to indices. You **can** assign a mutable array to a readonly-typed variable (readonly is a constraint on the reference). The opposite (readonly to mutable) is not allowed without assertion. So **const a: readonly number[] = [1, 2]** is valid; **a.push(3)** is an error.

---

## Q9. (Tough) How do you type a generic “array or single value” and normalize to array? (e.g. `T | T[]` → array)

**Answer:**  
**`function toArray<T>(x: T | T[]): T[] { return Array.isArray(x) ? x : [x] }`**. Type parameter **T**; argument **T | T[]**; return **T[]**. So **toArray(1)** → **[1]**, **toArray([1,2])** → **[1, 2]** with correct type.

---

## Q10. (Tough) What is a variadic tuple type? Example: “tuple of at least one string, then any number of numbers.”

**Answer:**  
**`[string, ...number[]]`** — at least one string, then rest numbers. For “at least one element” in generics, use **`[T, ...T[]]`** or **`[T, ...Rest]`**. Variadic tuple types (TS 4.0+) allow **...** in tuple types and **infer** in rest positions for type-level operations on tuple shapes.
