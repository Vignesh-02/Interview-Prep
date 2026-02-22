# 24. Mapped Types — Senior

## Q1. (Easy) What is a mapped type? Give the syntax.

**Answer:**  
A **mapped type** iterates over keys and produces a new object type: **{ [P in K]: T }**. **K** must be assignable to **keyof any** (string | number | symbol). So **{ [P in "a" | "b"]: number }** is **{ a: number; b: number }**. **P** is the loop variable (each key).

---

## Q2. (Easy) How do you map over **keyof T** to create a type from **T**?

**Answer:**  
**{ [P in keyof T]: T[P] }** — identity mapped type (same as **T** for object types). To transform: **{ [P in keyof T]: SomeTransform<T[P]> }**. So you iterate **P** over all keys of **T** and set the value type (e.g. **T[P]** or **T[P] | null**).

---

## Q3. (Medium) What is the **readonly** modifier in a mapped type? How do you add or remove it?

**Answer:**  
**{ readonly [P in keyof T]: T[P] }** — adds **readonly**. To **remove** readonly: **{ -readonly [P in keyof T]: T[P] }** — the **-** prefix removes the modifier. So **-readonly** and **-?** (remove optional) are supported in mapped types.

---

## Q4. (Medium) What is **key remapping** (as clause) in mapped types? (TS 4.1+)

**Answer:**  
**{ [P in keyof T as NewKey]: T[P] }** — **as NewKey** renames the key. **NewKey** can be a string type (e.g. **`${P}Key`**), or **never** to filter out keys. So **{ [P in keyof T as P extends string ? `get${Capitalize<P>}` : never]: T[P] }** — new keys like **getName** from **name**. Use **as never** to omit a key.

---

## Q5. (Medium) How do you create a type that makes only some keys of **T** optional? (e.g. keys that extend **string**)

**Answer:**  
**type PartialByKeys<T, K extends keyof T = keyof T> = Omit<T, K> & Partial<Pick<T, K>>** — then **PartialByKeys<Obj, "a" | "b">** makes **a** and **b** optional. Or with mapped types: **{ [P in keyof T as P extends K ? P : never]?: T[P] } & { [P in keyof T as P extends K ? never : P]: T[P] }** — first part optional for **K**, second part required for the rest.

---

## Q6. (Medium) What does **+readonly** and **-?** do in a mapped type?

**Answer:**  
**+readonly** explicitly adds readonly (optional; default when you write **readonly**). **-?** removes the optional modifier, making the property required. So **{ [P in keyof T]-?: T[P] }** is **Required<T>**. The **+** and **-** control adding/removing modifiers.

---

## Q7. (Tough) Write a mapped type that converts all properties of **T** to **boolean** (e.g. for “flags” from shape).

**Answer:**  
**type ToFlags<T> = { [P in keyof T]: boolean }**. So **ToFlags<{ a: number; b: string }>** is **{ a: boolean; b: boolean }**. Used for “option” or “dirty” flags per key.

---

## Q8. (Tough) How do you create a type with only the readonly keys of **T**? (ReadonlyKeys pattern)

**Answer:**  
**type ReadonlyKeys<T> = { [P in keyof T]: Readonly<Pick<T, P>> extends Pick<T, P> ? P : never }[keyof T]**. If a key is readonly, **Readonly<Pick<T, P>>** equals **Pick<T, P>**; otherwise the optional/readonly differs. So we get the union of keys that are readonly. Simpler heuristic: **type ReadonlyKeys<T> = { [P in keyof T]: T[P] extends { readonly [K in P]: T[P] } ? P : never }[keyof T]** — often implemented with a conditional that checks “if we add readonly, does it still match T?”

---

## Q9. (Tough) Write a type **Nullable<T>** that makes every property of **T** type **T[P] | null**.

**Answer:**  
**type Nullable<T> = { [P in keyof T]: T[P] | null }**. So each property can be its original type or **null**. For deep nullable you’d recurse: **T[P] extends object ? Nullable<T[P]> | null : T[P] | null** (with care for arrays/functions).

---

## Q10. (Tough) What is the difference between **{ [P in K]: T }** when **K** is **string** vs **"a" | "b"**?

**Answer:**  
**K = "a" | "b"** — you get **{ a: T; b: T }** (two specific keys). **K = string** — you get **{ [key: string]: T }** (index signature; any string key). So **K** as a union of literals gives a specific shape; **K** as **string** (or **number**/ **symbol**) gives an index signature. **keyof T** for a concrete **T** is a union of literals; so **{ [P in keyof T]: T[P] }** is a normal mapped type, not an index signature.
