# 9. Literal Types and const Assertions

## Q1. (Easy) What is a string literal type? Give an example.

**Answer:**  
A type that is exactly one string value: **`type Dir = "up" | "down"`**. So **let d: Dir = "up"** is valid; **d = "left"** is not. Used for fixed sets of strings (enum-like) and in discriminated unions.

---

## Q2. (Easy) What is a numeric literal type?

**Answer:**  
A type that is exactly one number: **`type One = 1`** or **`let x: 42 = 42`**. Used in tuples, overloads, and conditional types. **1 | 2 | 3** is a union of numeric literals.

---

## Q3. (Easy) What does **as const** do to a string? To a number?

**Answer:**  
**"hello" as const** has type **"hello"** (literal), not **string**. **42 as const** has type **42**, not **number**. So the type is narrowed to the exact literal. Useful when you need the narrow type in inference or generics.

---

## Q4. (Medium) What is the inferred type of **const obj = { a: 1, b: "x" }** with and without **as const**?

**Answer:**  
Without **as const**: **{ a: number; b: string }** — properties are widened. With **as const**: **{ readonly a: 1; readonly b: "x" }** — literal types and readonly. So **obj.a** is type **1**, **obj.b** is type **"x"**.

---

## Q5. (Medium) How do you get a union of keys from an object type? (e.g. "a" | "b" from { a: number; b: string })

**Answer:**  
**keyof T** — so **keyof { a: number; b: string }** is **"a" | "b"**. For a **value** object **O**, **keyof typeof O** gives the keys. So **type Keys = keyof typeof myObj**.

---

## Q6. (Medium) How do you get a union of values from an object type? (e.g. number | string from { a: number; b: string })

**Answer:**  
**T[keyof T]** — indexed access. So **{ a: number; b: string }[keyof { a: number; b: string }]** is **number | string**. For value **O**, **(typeof O)[keyof typeof O]** gives the union of property values.

---

## Q7. (Medium) When would you use **boolean** vs **true | false**? Are they the same?

**Answer:**  
They are the same type. **true** or **false** alone are literal types (used in conditional types, e.g. **T extends true ? A : B**). So **boolean** and **true | false** are equivalent; use **boolean** for clarity unless you need a single literal.

---

## Q8. (Tough) What is the type of **const arr = [1, "a"] as const**? What about **const arr = [1, "a"]**?

**Answer:**  
**as const**: **readonly [1, "a"]** — tuple of two elements, types **1** and **"a"**. Without: **(string | number)[]** — array of string or number, length not fixed. So **as const** preserves tuple shape and literal types.

---

## Q9. (Tough) How do you create a type that is “only these string literals” from an array at type level? (e.g. **["a", "b", "c"]** → **"a" | "b" | "c"**)

**Answer:**  
**const arr = ["a", "b", "c"] as const; type Keys = typeof arr[number]** — **arr[number]** is the union of element types, so **"a" | "b" | "c"**. The array must be **as const** so the type is a tuple of literals, not **string[]**.

---

## Q10. (Tough) What is **satisfies** (TS 4.9+)? How is it different from **as** or a type annotation?

**Answer:**  
**expr satisfies T** — checks that **expr** is assignable to **T** but **infers** the type of **expr** from the expression (narrower if literals). So **const c = { a: 1 } satisfies { a: number }** — **c** has type **{ a: 1 }**, not **{ a: number }**. Unlike **as**, it doesn’t widen; unlike **: T**, it preserves literal types. Use when you want validation plus precise inference.
