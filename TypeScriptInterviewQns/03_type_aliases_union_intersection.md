# 3. Type Aliases, Union & Intersection Types

## Q1. (Easy) What is a type alias? Give an example.

**Answer:**  
A **type alias** gives a name to a type: **`type ID = string | number`**. Then **`let id: ID = "abc"`**. Useful for reuse and readability. **type User = { name: string; id: number }** for object shapes.

---

## Q2. (Easy) What is a union type? What is the type of a value with type `A | B`?

**Answer:**  
**Union** — value can be **one of** the listed types: **`string | number`**. A value of type **A | B** is either A or B. TypeScript only allows operations that are valid for **all** members (common members); you narrow (e.g. **typeof**, **in**, type guards) to use type-specific operations.

---

## Q3. (Easy) What is an intersection type? How do you write it?

**Answer:**  
**Intersection** — value must satisfy **all** types: **`A & B`**. So **`{ a: number } & { b: string }`** is an object with both **a** and **b**. Used to combine object shapes or mix in properties. **type Named = Person & { displayName: string }**.

---

## Q4. (Medium) When would you use a union vs an intersection for two object types?

**Answer:**  
**Union (A | B)**: value is **either** A **or** B (e.g. “either Admin or Guest”). You get only common properties unless you narrow. **Intersection (A & B)**: value has **both** A and B (e.g. “Person with Timestamp”). Use union for “one of”; intersection for “all of” when combining shapes.

---

## Q5. (Medium) What is a discriminated union? How do you narrow it?

**Answer:**  
A **discriminated union** is a union of object types that share a common **literal** property (the discriminant), e.g. **type Shape = { kind: "circle"; r: number } | { kind: "rect"; w: number; h: number }**. Narrow with **if (s.kind === "circle")** — then TypeScript knows **s** is the circle variant and **s.r** is available.

---

## Q6. (Medium) Can you use a type alias before it’s defined (forward reference)? What about in a union/intersection?

**Answer:**  
Type aliases can **reference** themselves or others as long as the structure is not infinitely recursive in an invalid way. **type A = B; type B = A** is a circular reference that can be allowed for object-like structures. For recursive types (e.g. tree nodes), **type Node = { value: number; children: Node[] }** is fine.

---

## Q7. (Medium) What does `string | number | boolean` mean when used as a function parameter? How does the function body treat it?

**Answer:**  
The parameter accepts **string**, **number**, or **boolean**. In the function body, you can only use operations valid for **all** three (e.g. **return**). To use type-specific ops you must **narrow** (typeof, type guard, or switch on the value).

---

## Q8. (Tough) What is the result type of `(A | B) & C`? What about `(A & B) | C`?

**Answer:**  
**(A | B) & C** distributes to **(A & C) | (B & C)** conceptually — value must be C and also either A or B. **(A & B) | C** — value is either (A and B) or C. Intersection binds tighter in the type algebra; use parentheses to be explicit.

---

## Q9. (Tough) How do you express “array of string or number” so that the whole array is either all strings or all numbers (not mixed)?

**Answer:**  
**`string[] | number[]`** — the array is either all strings or all numbers. **`(string | number)[]`** allows mixed elements. So **string[] | number[]** is the “tuple” of “either string array or number array.”

---

## Q10. (Tough) What is the difference between `never` and `void` in a union? When does `A | never` simplify?

**Answer:**  
**void** is a real type (function return). **never** is the empty type — no value. In a union, **A | never** simplifies to **A** (adding nothing). So **never** “disappears” in unions. Used in conditional types and exhaustive checks: **never** in a switch default means “no remaining cases.”
