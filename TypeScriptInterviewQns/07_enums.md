# 7. Enums

## Q1. (Easy) What is a numeric enum? What does it compile to?

**Answer:**  
**enum Dir { Up, Down, Left, Right }** — numeric enum; **Up** is 0, then 1, 2, 3. Compiles to a JS object with reverse mapping (number → name) for numeric enums. So **Dir.Up** is 0 and **Dir[0]** is **"Up"**.

---

## Q2. (Easy) What is a string enum? How is it different from numeric at runtime?

**Answer:**  
**enum Color { Red = "RED", Green = "GREEN" }**. No auto-increment; no reverse mapping. Compiles to **{ Red: "RED", Green: "GREEN" }**. Better for debugging and serialization; no **Color["RED"]** lookup.

---

## Q3. (Easy) Can you mix numeric and string members in one enum?

**Answer:**  
Yes, but the next numeric member after a string (or uninitialized) must have an explicit value, because there’s no automatic increment from a string. **enum M { A = 1, B = "b", C = 2 }** is valid.

---

## Q4. (Medium) What is a const enum? What happens at compile time?

**Answer:**  
**const enum E { A = 1, B = 2 }** — **const enum** is inlined at use sites; no JS object is emitted. **E.A** becomes **1**. Cannot use **E** as a value (e.g. **Object.keys(E)**) because there’s no runtime object. Use for smaller output and no reverse mapping.

---

## Q5. (Medium) When would you use an enum vs a union of string literals?

**Answer:**  
**Enum**: when you want a **namespace** and possibly reverse mapping (numeric) or a single object to reference. **Union of literals** (**"a" | "b" | "c"**): lighter, no runtime object, works with **const** objects for “enum-like” keys. Many prefer **as const** object + type from keys for type-safe “enums” without enum semantics.

---

## Q6. (Medium) How do you get the type of an enum’s values? (e.g. type that is 0 | 1 | 2 for numeric enum)

**Answer:**  
**type DirVal = Dir** — the enum type **Dir** already is the union of its values. So **let d: Dir = Dir.Up** and **Dir** as a type means **Dir.Up | Dir.Down | ...**. For string enum, **type ColorVal = Color** is **Color.Red | Color.Green** (i.e. the string literals).

---

## Q7. (Medium) What is the type of an enum member? (e.g. `Dir.Up`)

**Answer:**  
For numeric enum, **Dir.Up** has type **Dir** (the enum type). So it’s the union of all members. Literal type **Dir.Up** is the number literal (e.g. **0**). So **const x = Dir.Up** gives **x** type **Dir**; in a const context you might get literal **0** depending on inference.

---

## Q8. (Tough) Why might enums be considered “not type-safe” in some cases? (Hint: numeric enum and arbitrary numbers)

**Answer:**  
**Numeric enums** allow assigning any number: **let d: Dir = 99** is valid because enum values are numbers. So you can pass invalid numbers where an enum is expected. **String enums** are stricter — only the exact string literals. Use **string enum** or union of literals for stricter checking.

---

## Q9. (Tough) How do you create an “enum-like” object with type-safe values without using **enum**? (const object + type)

**Answer:**
```ts
const Status = { Idle: "idle", Loading: "loading", Done: "done" } as const;
type Status = (typeof Status)[keyof typeof Status]; // "idle" | "loading" | "done"
```
Then **Status** (value) has keys; **Status** (type) is the union of values. No reverse mapping; full type safety and tree-shaking friendly.

---

## Q10. (Tough) What are ambient enums? When would you use **declare enum**?

**Answer:**  
**declare enum E { A, B }** — ambient enum; no JS is emitted; you’re declaring an enum that exists at runtime (e.g. from another script). Used in **.d.ts** for typing existing enums. **declare const enum** is ambient const enum; use sites are inlined; the object doesn’t exist at runtime.
