# 14. keyof and typeof

## Q1. (Easy) What does **keyof T** produce for an object type?

**Answer:**  
**keyof T** is the union of all **keys** of **T** (string, number, or symbol depending on **T**). So **keyof { a: number; b: string }** is **"a" | "b"**. For a class, it includes public members. Used to type “a key of T” or to iterate over keys at the type level.

---

## Q2. (Easy) What does **typeof** do in type position? (e.g. **typeof obj**)

**Answer:**  
In **type** position, **typeof value** gives the **type** of **value**. So **const o = { a: 1 }; type O = typeof o** — **O** is **{ a: number }**. Used to derive types from values (constants, functions, classes) so you don’t duplicate the shape.

---

## Q3. (Easy) What is **keyof typeof obj** for a value **obj**?

**Answer:**  
**keyof typeof obj** is the union of **obj**’s keys. So **const o = { a: 1, b: "x" }; keyof typeof o** is **"a" | "b"**. **typeof** gets the type of **o**, **keyof** gets the keys of that type.

---

## Q4. (Medium) What is the type of **T[K]** for a type **T** and key **K**?

**Answer:**  
**T[K]** is **indexed access** — the type of the property of **T** at key **K**. So **T["a"]** is the type of **T.a**. **K** must be assignable to **keyof T**. Used to extract property types and build mapped/utility types.

---

## Q5. (Medium) How do you get the type of a function’s return value without calling it?

**Answer:**  
**ReturnType<typeof fn>** — built-in utility. So **type R = ReturnType<typeof myFunc>**. For overloaded functions, **ReturnType** uses the last signature. You need **typeof** because **ReturnType** takes a **type**, and the function is a value.

---

## Q6. (Medium) What is **typeof MyClass**? What is the instance type of **MyClass**?

**Answer:**  
**typeof MyClass** is the type of the **constructor** (the class value) — includes static members and the **new** signature. The **instance** type is **InstanceType<typeof MyClass>** or in TS, using the class name in type position (e.g. **let x: MyClass**) often refers to the instance type; **MyClass** as a value is the constructor.

---

## Q7. (Medium) What does **keyof** produce for an interface with optional and readonly properties?

**Answer:**  
**keyof** includes **all** property names (optional and readonly don’t change the key set). So **keyof { a: number; b?: string; readonly c: boolean }** is **"a" | "b" | "c"**. Optional and readonly affect the **property type**, not the key union.

---

## Q8. (Tough) What is **keyof** for a string index signature **[key: string]: number**?

**Answer:**  
**keyof** for **{ [key: string]: number }** is **string | number** (number because numeric keys are a subset of string keys in JS). So the keys are **string | number**. For **[key: number]: string**, **keyof** would include **number** and symbol-like keys.

---

## Q9. (Tough) How do you type “a function that takes a key of T and returns T[that key]”?

**Answer:**  
**<T, K extends keyof T>(obj: T, key: K): T[K]** — so the return type is **T[K]**. Then **get(obj, "name")** has return type **T["name"]**. This is the type-safe **get** pattern; **K extends keyof T** ensures **key** is valid and **T[K]** is the precise property type.

---

## Q10. (Tough) What is **Parameters<typeof fn>** and **ConstructorParameters<typeof Ctor>**?

**Answer:**  
**Parameters<T>** is a utility that extracts the parameter tuple of a function type **T**. So **Parameters<typeof fn>** is the tuple of **fn**’s parameters. **ConstructorParameters<T>** does the same for a constructor type **T** (the **new (...args) => any** part). Used to reuse parameter types for wrappers or composition.
