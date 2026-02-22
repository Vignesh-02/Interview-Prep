# 22. Utility Types (Partial, Required, Pick, Omit, Record, etc.) — Senior

## Q1. (Easy) What does **Partial<T>** do? When would you use it?

**Answer:**  
**Partial<T>** makes all properties of **T** **optional**. So **Partial<{ a: number; b: string }>** is **{ a?: number; b?: string }**. Use for “updates” or “patch” objects where every field is optional. Built-in: **type Partial<T> = { [P in keyof T]?: T[P] }**.

---

## Q2. (Easy) What does **Required<T>** do?

**Answer:**  
**Required<T>** makes all properties of **T** **required** (removes optional). So **Required<{ a?: number }>** is **{ a: number }**. Built-in: **type Required<T> = { [P in keyof T]-?: T[P] }** — the **-?** removes the optional modifier.

---

## Q3. (Easy) What does **Readonly<T>** do?

**Answer:**  
**Readonly<T>** makes all properties of **T** **readonly**. So you can’t reassign **obj.prop**. Built-in: **type Readonly<T> = { readonly [P in keyof T]: T[P] }**. Does not make nested objects immutable (shallow readonly).

---

## Q4. (Medium) What does **Pick<T, K>** do? What must **K** extend?

**Answer:**  
**Pick<T, K>** creates a type with only the keys **K** from **T**. **K** must extend **keyof T**. So **Pick<{ a: number; b: string }, "a">** is **{ a: number }**. **type Pick<T, K extends keyof T> = { [P in K]: T[P] }**.

---

## Q5. (Medium) What does **Omit<T, K>** do? How is it typically implemented?

**Answer:**  
**Omit<T, K>** creates a type with all keys of **T** **except** those in **K**. **type Omit<T, K extends keyof any> = Pick<T, Exclude<keyof T, K>>**. So **Omit<{ a: number; b: string }, "a">** is **{ b: string }**. **K** can be **string | number | symbol** (keyof any).

---

## Q6. (Medium) What does **Record<K, V>** do? What is **Record<string, number>**?

**Answer:**  
**Record<K, V>** creates an object type with keys **K** and value type **V**. **Record<string, number>** is **{ [key: string]: number }**. **Record<"a" | "b", number>** is **{ a: number; b: number }**. **type Record<K extends keyof any, T> = { [P in K]: T }**.

---

## Q7. (Medium) What is **Exclude<T, U>** and **Extract<T, U>**?

**Answer:**  
**Exclude<T, U>** — remove from **T** any type that assigns to **U**: **T extends U ? never : T** (distributes over union **T**). So **Exclude<"a" | "b" | "c", "a">** is **"b" | "c"**. **Extract<T, U>** — keep only those in **T** that assign to **U**: **T extends U ? T : never**. So **Extract<"a" | "b", "a">** is **"a"**.

---

## Q8. (Tough) What is **NonNullable<T>**? How is it defined?

**Answer:**  
**NonNullable<T>** removes **null** and **undefined** from **T**. **type NonNullable<T> = T extends null | undefined ? never : T**. So **NonNullable<string | null>** is **string**. Used to get a type that’s safe after null checks.

---

## Q9. (Tough) Implement a **DeepPartial<T>** that makes all properties (including nested) optional.

**Answer:**
```ts
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
```
Caveat: **object** includes arrays and functions; you might want to exclude them (e.g. **T[P] extends object & ({} | [])** or use a more precise condition) so that primitives and functions aren’t recursed.

---

## Q10. (Tough) What is **Required<Pick<T, K>>** vs **Pick<Required<T>, K>**? When are they different?

**Answer:**  
**Required<Pick<T, K>>** — take only **K** from **T**, then make those keys required. So optional keys in **T** that are in **K** become required. **Pick<Required<T>, K>** — make all of **T** required first, then pick **K**; same result when **K** is a subset of **T**’s keys. They are the same when **K** is exactly the optional keys or when **T** has no optional keys. Difference appears when **T** has both required and optional keys: **Required<Pick<T, K>>** only affects the picked keys; **Pick<Required<T>, K>** first requires everything, so both give “all picked keys required.”
