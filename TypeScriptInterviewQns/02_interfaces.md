# 2. Interfaces

## Q1. (Easy) How do you define an interface? Can it have optional properties?

**Answer:**  
**`interface User { name: string; id: number }`**. Optional: **`age?: number`**. Readonly: **`readonly id: number`**. Interfaces describe object shapes and can be extended or implemented by classes.

---

## Q2. (Easy) How do you extend an interface? Can you extend multiple interfaces?

**Answer:**  
**`interface Admin extends User { role: string }`**. Multiple: **`interface X extends A, B { }`**. The child has all properties from the extended interfaces plus its own.

---

## Q3. (Easy) What is a readonly property? Can you change it inside the class?

**Answer:**  
**readonly** means the property cannot be reassigned after initialization. For a **class**, you can assign to it in the constructor; after that, reassignment is a type error. It does not make nested objects immutable (only the reference is readonly).

---

## Q4. (Medium) What are index signatures? When would you use one?

**Answer:**  
**`[key: string]: number`** — allows any string key with a number value. Use when you have dynamic keys (e.g. dictionary, record). You can mix known properties with an index signature; all declared properties must be compatible with the index type. **`[key: number]: string`** for numeric keys (array-like).

---

## Q5. (Medium) Can an interface describe a function? How?

**Answer:**  
Yes. **`interface Fn { (x: number): string }`** — call signature. Then **const f: Fn = (x) => String(x)**. Or use **type Fn = (x: number) => string**. Interfaces can also have both properties and a call signature (hybrid type).

---

## Q6. (Medium) What is “excess property checking”? When does it apply?

**Answer:**  
When you assign an **object literal** directly to a typed variable, TypeScript checks that the literal has **no extra properties** not in the type. So **const u: User = { name: "a", id: 1, extra: true }** errors. It does **not** apply when you assign from another variable (e.g. **const o = { name: "a", id: 1, extra: true }; const u: User = o** is allowed). Use to catch typos and wrong shapes at the source.

---

## Q7. (Medium) How do you make a property optional in an interface? What is the type of that property?

**Answer:**  
**`prop?: number`** — optional. The type includes **undefined**, so it’s **number | undefined**. Accessing **obj.prop** gives **number | undefined**; narrow with **if (obj.prop !== undefined)** or optional chaining.

---

## Q8. (Tough) What is declaration merging? How does it apply to interfaces?

**Answer:**  
**Declaration merging** means multiple declarations with the same name (e.g. same **interface** name) are merged into one. So **interface Window { x: number }** and **interface Window { y: string }** become one **Window** with **x** and **y**. Used for augmenting global or library types. **type** aliases cannot be merged — duplicate **type** names error.

---

## Q9. (Tough) Can an interface extend a type alias? Can a type alias extend an interface?

**Answer:**  
An **interface** can **extend** a type alias if the alias is an object type: **interface B extends A { }** where **A** is a type. A **type alias** can **intersect** an interface: **type B = A & { extra: number }** where **A** is an interface. So “extend” for interface is **extends**; for type it’s **&** (intersection).

---

## Q10. (Tough) What is the difference between **interface** and **type** for describing the same object? When would you choose one over the other?

**Answer:**  
Both can describe the same shape. **interface**: can be merged (declaration merging), uses **extends**, and is open for augmentation. **type**: can express unions, primitives, tuples, and mapped/conditional types; no merging. Choose **interface** for public object contracts and when you might augment (e.g. global/module augmentation). Choose **type** for unions, intersections, and complex type logic.
