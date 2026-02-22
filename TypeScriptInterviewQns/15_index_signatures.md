# 15. Index Signatures and Excess Property Checks

## Q1. (Easy) What is an index signature? Give the syntax for string and number keys.

**Answer:**  
**`[key: string]: T`** — any string key has type **T**. **`[key: number]: T`** — numeric keys (array-like). The key name is just a label; only the key **type** (string, number, symbol) matters. All declared properties must be compatible with the index type.

---

## Q2. (Easy) Can an object type have both specific properties and an index signature? What rule do they follow?

**Answer:**  
Yes. Example: **`{ name: string; [key: string]: string | number }`**. **name** must be assignable to **string | number** (the index value type). So the index signature type must be a supertype of all explicit property types (or you use a union that includes them).

---

## Q3. (Easy) What triggers “excess property checking”? When is it skipped?

**Answer:**  
Triggered when you assign an **object literal** directly to a variable or parameter. Extra properties not in the type cause an error. Skipped when: assigning from another variable, using type assertion, or when the target has an index signature that allows extra keys. So **const o: User = { name: "a", id: 1, extra: true }** errors; **const x = { name: "a", id: 1, extra: true }; const o: User = x** does not.

---

## Q4. (Medium) How do you allow “any extra string keys” while still having known properties?

**Answer:**  
Add an index signature: **`{ name: string; [key: string]: string }`** — then **name** and any other string key must be **string**. To allow extra keys with **any** value: **`{ name: string; [key: string]: string | unknown }`** or **`{ name: string; [key: string]: any }`** (known props must still match).

---

## Q5. (Medium) What is a **symbol** index signature?

**Answer:**  
**`[key: symbol]: T`** — keys can be symbols. Used for “well-known” or internal keys. You can have **string**, **number**, and **symbol** index signatures on the same type (they describe different key subsets). Object type can have at most one string and one number index signature.

---

## Q6. (Medium) How do you bypass excess property checking when you know the object is compatible?

**Answer:**  
(1) Assign to an intermediate variable, then assign to the typed variable. (2) Use assertion: **as User** or **as unknown as User**. (3) Use a type that includes an index signature. Prefer (1) when the extra props are intentional and you’re sure the type is safe.

---

## Q7. (Tough) Why might **{ a: number }** not be assignable to **{ [key: string]: number }** in some cases?

**Answer:**  
With **strict** settings, an object literal **{ a: number }** is inferred as **{ a: number }**. It *is* assignable to **{ [key: string]: number }** because **a** is a string key and its value is number. They are usually assignable. If you had **{ a: number; b: string }** and **{ [key: string]: number }**, it would fail because **b** is not **number**. So the issue is when explicit properties don’t match the index value type.

---

## Q8. (Tough) How do you type “object with at least keys A and B, and possibly more”?

**Answer:**  
**`{ a: number; b: string } & { [key: string]: unknown }`** or use **extends**: **T extends { a: number; b: string }**. For “at least” you often use **T extends { a: number; b: string }** in generics. For a concrete type, **{ a: number; b: string; [x: string]: any }** allows more keys.

---

## Q9. (Tough) What is the difference between **Record<string, number>** and **{ [key: string]: number }**?

**Answer:**  
They are equivalent for typing. **Record<string, number>** is a utility type; **{ [key: string]: number }** is inline. **Record<K, V>** is defined as **{ [P in K]: V }** (mapped type). So **Record<string, number>** is the same shape. **Record** is more readable and works with **keyof** for **K** (e.g. **Record<keyof T, boolean>**).

---

## Q10. (Tough) How do you express “object whose keys are only from set K” and values are V? (no extra keys)

**Answer:**  
**{ [P in K]: V }** — mapped type. So **type Exact<K extends string, V> = { [P in K]: V }** gives an object with exactly keys in **K**. For “no extra keys” at runtime you can’t enforce it; TypeScript’s type system gives you “has these keys” and optionally index signature for “and nothing else” by not having an index signature (then excess property check applies to literals).
