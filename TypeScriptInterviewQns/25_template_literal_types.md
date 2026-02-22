# 25. Template Literal Types and String Manipulation — Senior

## Q1. (Easy) What is a template literal type? Give an example.

**Answer:**  
Template literal types build string types from other types: **`${T}`** in a type. **type EventName = `on${string}`** — strings that start with **"on"**. **type X = `a_${"b" | "c"}`** → **"a_b" | "a_c"**. Used for event names, CSS units, API routes, etc.

---

## Q2. (Easy) What does **Capitalize<T>** do? (built-in intrinsic)

**Answer:**  
**Capitalize<T>** (TS 4.1+) is an intrinsic type that capitalizes the first character of string type **T**. So **Capitalize<"hello">** is **"Hello"**. Similarly **Uncapitalize**, **Uppercase**, **Lowercase**. Used in template literal types for naming (e.g. **get** + **Capitalize<Key>**).

---

## Q3. (Medium) Write a type that prefixes every key of an object with **"get"** and capitalizes the key. (e.g. **name** → **getName**)

**Answer:**  
**type Getters<T> = { [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P] }**. So **Getters<{ name: string }>** has **getName: () => string**. **string & P** ensures **P** is a string key for **Capitalize**. Key remapping **as** builds the new key.

---

## Q4. (Medium) What is **Uppercase<T>** and **Lowercase<T>**? When are they useful?

**Answer:**  
**Uppercase<T>** and **Lowercase<T>** are intrinsic types that convert string type **T** to upper/lower case. Useful for API conventions (e.g. **HTTPMethod = Uppercase<"get" | "post">** → **"GET" | "POST"**) or for normalizing key names in mapped types.

---

## Q5. (Medium) How do you create a union of string literals from a tuple type? (e.g. **["a", "b"]** → **"a" | "b"**)

**Answer:**  
**type TupleToUnion<T> = T extends readonly (infer U)[] ? U : never**. So for **T = readonly ["a", "b"]**, **U** is **"a" | "b"**. Or **T[number]** for a tuple **T** — **T[number]** is the union of all element types. So **type Arr = ["a", "b"]; type U = Arr[number]** → **"a" | "b"**.

---

## Q6. (Medium) What type does **`${"a" | "b"}_${"x" | "y"}`** produce?

**Answer:**  
**"a_x" | "a_y" | "b_x" | "b_y"** — the cross product (all combinations). Template literal types distribute over unions in each position.

---

## Q7. (Tough) How do you type a function that takes a string and returns an object with that key? (e.g. **key("name")** → **{ name: ... }**)

**Answer:**  
For a fixed set of keys you can use overloads or a generic: **function key<K extends string>(k: K): Record<K, unknown>** — return type **Record<K, unknown>** has key **K**. So **key("name")** returns **{ name: unknown }** (or you refine with a second generic for value type). For “only certain keys” use **K extends AllowedKeys**.

---

## Q8. (Tough) Write a type **Join<T, S>** that joins a tuple of strings with **S**. (e.g. **Join<["a","b","c"], ".">** → **"a.b.c"**)

**Answer:**  
**type Join<T extends string[], S extends string> = T extends [infer F extends string, ...infer R extends string[]] ? R["length"] extends 0 ? F : `${F}${S}${Join<R, S>}` : ""**. Recursive: first element + separator + join of rest. Base case: single element, no separator. TS 4.7+ supports **infer F extends string**.

---

## Q9. (Tough) What is **Split<S, D>** that splits string type **S** by delimiter **D** into a tuple?

**Answer:**  
**type Split<S extends string, D extends string> = S extends `${infer L}${D}${infer R}` ? [L, ...Split<R, D>] : [S]**. So **Split<"a.b.c", ".">** is **["a", "b", "c"]**. **L** is the part before first **D**, **R** is the rest; recurse on **R**, base case is **S** when **D** is not found.

---

## Q10. (Tough) How do you implement **StartsWith<S, Prefix>** and **EndsWith<S, Suffix>** as types?

**Answer:**  
**type StartsWith<S extends string, P extends string> = S extends `${P}${string}` ? true : false**. **type EndsWith<S extends string, P extends string> = S extends `${string}${P}` ? true : false**. So **StartsWith<"hello", "he">** is **true**; **EndsWith<"hello", "lo">** is **true**. Use **${string}** for “rest of string.”
