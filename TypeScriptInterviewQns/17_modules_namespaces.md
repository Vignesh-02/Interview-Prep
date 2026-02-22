# 17. Modules and Namespaces

## Q1. (Easy) What is the difference between **import type** and **import**?

**Answer:**  
**import type { T } from "mod"** — imports only the **type**; erased at compile time; use for types only. **import { T } from "mod"** — can import value or type; **T** might be a value. Use **import type** when you only need the type to avoid pulling in runtime code and to make “type-only” clear. **import type** can also use **type** in **export type**.

---

## Q2. (Easy) What does **namespace** do? How do you define one?

**Answer:**  
**namespace** groups code and creates an object in JS (IIFE or global). **namespace N { export const x = 1; export function f() {} }**. Use **N.x**, **N.f()**. Legacy pattern; prefer **ES modules** (**import**/ **export**) for new code. Namespaces can merge and nest.

---

## Q3. (Easy) How do you export a type and a value with the same name?

**Answer:**  
**export type { MyThing }; export { MyThing }** — or **export { MyThing }; export type { MyThing }**. In TS, type and value namespaces are separate, so **MyThing** can be both a type and a value (e.g. a class). Re-export: **export { MyThing }** and **export type { MyThing }** if the source has both.

---

## Q4. (Medium) What is **export default** vs **export**? How do you import each?

**Answer:**  
**export default** — one default per module; **import X from "mod"** (any name). **export { a, b }** or **export const a** — named; **import { a, b } from "mod"**. Default is convenient for a single main export; named exports are explicit and support tree-shaking.

---

## Q5. (Medium) What is **import * as NS from "mod"**? What is the type of **NS**?

**Answer:**  
**NS** is a namespace object — all named exports as properties. Type of **NS** is the module’s export type (object with those keys). So **NS.foo** if **foo** is exported. Use when you want one object with many exports or to avoid name clashes.

---

## Q6. (Medium) When would you use **namespace** today vs ES modules?

**Answer:**  
Use **namespace** mainly for **legacy** code, **global** script output, or **declaration merging** (e.g. augmenting an interface with a same-named namespace for static members). Prefer **ES modules** (import/export) for new code: better tooling, tree-shaking, and standard JS.

---

## Q7. (Tough) What is **/// <reference path="..." />** and **/// <reference types="..." />**?

**Answer:**  
**Triple-slash directives**. **reference path** — includes another file in the compilation (like a dependency). **reference types** — includes **@types** package (e.g. **/// <reference types="node" />**). Used in **.d.ts** or when you don’t use **import** to pull in types. Modern approach is **import** or **types** in **tsconfig**.

---

## Q8. (Tough) How do you re-export everything from a module? What about “export * from” and default?

**Answer:**  
**export * from "mod"** — re-exports all **named** exports (not default). **export * as N from "mod"** — re-exports as a single namespace **N**. To re-export default: **export { default } from "mod"** or **export { default as Foo } from "mod"**. **export *** does not re-export the default.

---

## Q9. (Tough) What is **isolatedModules** and why does it matter for Babel or esbuild?

**Answer:**  
**isolatedModules** forces each file to be compilable in isolation (no cross-file type-only information). So **import type** and **export type** are required for type-only imports/exports; re-exports must be valid in isolation. Babel and esbuild strip types without full project analysis; **isolatedModules** ensures the TS you write is safe for that workflow.

---

## Q10. (Tough) How do you type a dynamic **import()**? What is the type of **import("./mod")**?

**Answer:**  
**import("./mod")** returns **Promise<typeof import("./mod")>** — the module namespace type. So **const mod = await import("./mod")** — **mod** has the type of the module’s exports. For a module with default: **Promise<{ default: DefaultType; ... }>**. Use **Promise<typeof import("mod")>** when typing a variable that will hold the result of **import("mod")**.
