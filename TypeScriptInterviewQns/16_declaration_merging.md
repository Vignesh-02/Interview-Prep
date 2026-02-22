# 16. Declaration Merging and Module Augmentation

## Q1. (Easy) What is declaration merging? Which declarations can merge?

**Answer:**  
**Declaration merging** is when the compiler merges multiple declarations with the same name into one. **Interfaces** with the same name merge. **Namespaces** merge. **Namespace** + **interface** with same name merge (namespace augments the interface). **type** aliases do **not** merge — duplicate **type** names error.

---

## Q2. (Easy) If you declare **interface Window { x: number }** in a file, what happens?

**Answer:**  
It **merges** with the global **Window** interface (from lib.dom.d.ts). So **Window** now has **x: number** in addition to existing properties. Used to add custom properties to **window** (e.g. **window.myApp**). Must be in global scope or in a **global augmentation** (declare global).

---

## Q3. (Medium) How do you augment a module (e.g. add types to an existing module)?

**Answer:**  
**declare module "module-name" { export interface Added { } export function added(): void }**. Your augmentation merges with the module’s existing declarations. Use to add types for untyped modules or to extend typed modules. The block must only contain declarations (no implementation).

---

## Q4. (Medium) What is **declare global**? When do you use it?

**Answer:**  
**declare global { ... }** — code inside is in the **global** scope. Used inside a module (which otherwise has its own scope) to add or augment global declarations (e.g. **interface Window**, **var myGlobal**). Ensures augmentation is applied to the global namespace.

---

## Q5. (Medium) Can you merge an interface with a namespace? What do you get?

**Answer:**  
Yes. **interface Foo { a: number }** and **namespace Foo { export const b = 1 }** merge. Then **Foo** has property **a** (from interface) and **Foo.b** (from namespace). Used for static members on an interface (e.g. **interface Array** and **namespace Array** for **Array.isArray**).

---

## Q6. (Medium) How do you augment an existing interface in a different file (e.g. extend Express Request)?

**Answer:**  
In a **.d.ts** or **.ts** file (that is included in the project), write **declare global { namespace Express { interface Request { user?: User } } }** (for Express). Or **export {}** to make the file a module, then **declare global { ... }** and put the **Express** augmentation inside. The augmentation merges with **Express.Request** from **@types/express**.

---

## Q7. (Tough) What happens if two interfaces with the same name have a property with the same name but different types?

**Answer:**  
Declaration merging requires that **same-named** properties have **compatible** types (same type or one is a subtype). If they conflict (e.g. **a: string** in one and **a: number** in another), you get a **duplicate identifier** or type conflict error. So merged interfaces must agree on property types for the same key.

---

## Q8. (Tough) How do you “patch” a third-party module’s types without forking its .d.ts?

**Answer:**  
Create a **.d.ts** file (e.g. **types/my-module.d.ts**) with **declare module "my-module" { ... }** and add the extra or overridden declarations. Ensure the file is included (e.g. in **tsconfig** **include** or **typeRoots**). TypeScript merges your declaration with the module. Use **module augmentation** for adding; for replacing you might need to redeclare the exports you need.

---

## Q9. (Tough) What is **interface** merging vs **type** alias for extensibility?

**Answer:**  
**interface** can be merged by consumers (e.g. in another file, **interface Foo { extra: number }** merges with existing **Foo**). **type** cannot be merged — you’d have to use **type Foo = ExistingFoo & { extra: number }** in one place. So for “extensible by others” (e.g. library types), **interface** is preferred so users can augment via merging.

---

## Q10. (Tough) How do you ensure your augmentation runs (is applied) when the project compiles?

**Answer:**  
The augmentation file must be **included** in the compilation (via **include** in tsconfig or by being imported somewhere). It should be a **.d.ts** or **.ts** file. If it’s a module (has **import**/ **export**), use **declare global { }** so the augmentation is global. No “run” at runtime — it’s type-only. Ensure **tsconfig** doesn’t exclude the file and that the augmented module/global is the one the rest of the code uses.
