# 1. Basic Types and Type Annotations

## Q1. (Easy) What are the primitive types in TypeScript? How do you annotate a variable?

**Answer:**  
Primitives: **string**, **number**, **boolean**, **null**, **undefined**, **symbol**, **bigint**. Annotate with a colon: **`let x: number = 5`** or **`const s: string = "hi"`**. TypeScript infers types when you initialize; annotations are optional when inference is clear.

---

## Q2. (Easy) What is the type of an array? How do you type “array of numbers”?

**Answer:**  
**`number[]`** or **`Array<number>`** — both mean array of numbers. **`string[]`** for strings. For mixed or unknown elements you’d use **`(string | number)[]`** or **`unknown[]`**.

---

## Q3. (Easy) What does `strictNullChecks` do? What is the type of `null` and `undefined` without it?

**Answer:**  
With **strictNullChecks** off, **null** and **undefined** are assignable to every type (so `string` includes null/undefined). With it **on**, they are distinct; a **string** only accepts string unless you use **string | null** or **string | undefined**. Always prefer enabling it for safer code.

---

## Q4. (Medium) What is the difference between `let` and `const` in terms of typing? Can you reassign a const object’s properties?

**Answer:**  
**let** allows reassignment of the variable; **const** does not. For **const obj = { a: 1 }**, you cannot do **obj = {}**, but you **can** do **obj.a = 2** — the object is mutable; only the binding is constant. TypeScript tracks the literal type more narrowly for **const** in some cases (e.g. **const x = 1** has type **1** in strict literal inference).

---

## Q5. (Medium) What is the type of a function that takes no arguments and returns void?

**Answer:**  
**`() => void`** or **`function (): void`**. For a method: **`(): void`**. The **void** return type means “we ignore the return value”; the function can still return something at runtime.

---

## Q6. (Medium) How do you type an object with known properties? What if a property might be missing?

**Answer:**  
**`{ name: string; age: number }`**. For optional property: **`{ name: string; age?: number }`** — **age** can be **undefined**. Or use **`age: number | undefined`** explicitly. Optional (**?**) implies **undefined** in the type.

---

## Q7. (Medium) What is the difference between **type** and **interface** for a simple object shape? (One line each.)

**Answer:**  
Both can describe an object. **interface** can be **declaration-merged** and **extended** with **extends**; **type** can represent **unions**, **intersections**, **primitives**, and **mapped/conditional types**. For a simple object, either works; interface is often used for public API shapes.

---

## Q8. (Tough) What does TypeScript infer for `let x = null` and `let y = undefined`? How does strictNullChecks affect this?

**Answer:**  
By default, **x** gets type **null** and **y** gets type **undefined**. With **strictNullChecks**, that’s accurate. Without it, **x** might be inferred as **any** in older behavior. For **let z = null; z = 5** without strict mode, **z** might widen to **any**. With strict, **z** stays **null** and assigning **5** is an error. Use explicit types when you intend to assign later.

---

## Q9. (Tough) What is **boolean** vs **true | false**? Are they the same?

**Answer:**  
**boolean** is the same as **true | false** — both represent either true or false. So they are equivalent. Literal types **true** or **false** alone are narrower and used in conditional types and discriminated unions.

---

## Q10. (Tough) How do you type a variable that can be a string or a number? What about “string or number or null”?

**Answer:**  
**`string | number`** for string or number. **`string | number | null`** for the three. Use **union types** with **|**. For optional (may be absent), **`string | undefined`** or **`string?`** in object types.
