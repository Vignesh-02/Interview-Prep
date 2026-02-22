# 29. Declaration Files (.d.ts) and Ambient Declarations — Senior

## Q1. (Easy) What is a **.d.ts** file? What does it contain?

**Answer:**  
A **.d.ts** file contains **type declarations** only — no implementation. It describes types for JavaScript or for other TypeScript code. Used for typing existing JS libraries (ambient declarations) or for publishing types (with or without implementation). Only **declare** and types; no **const x = 1** (values) unless **declare const x: number** (ambient).

---

## Q2. (Easy) What is **declare**? When do you use **declare const** or **declare function**?

**Answer:**  
**declare** says “this exists at runtime elsewhere.” **declare const x: number** — **x** is a global (or module-scoped) value of type **number**. **declare function f(x: number): string** — **f** exists with that signature. No implementation; just the type. Used in **.d.ts** or in **.ts** when you reference globals (e.g. from a script tag).

---

## Q3. (Medium) What is **declare module**? How do you type an untyped npm package?

**Answer:**  
**declare module "package-name" { export const x: number; export function f(): void }** — declares the shape of the module. Put in a **.d.ts** (e.g. **types/package-name.d.ts**) so TS uses it when you **import** from **"package-name"**. Use to type a package that has no **@types/package-name** or to override types.

---

## Q4. (Medium) What is **declare global**? When is it needed?

**Answer:**  
**declare global { interface Window { myApp: App } }** — adds to the **global** scope from inside a **module** (a file with **import**/ **export** is a module and has no global scope by default). So **declare global** lets you augment **Window**, **globalThis**, or other globals from a module. Needed when your **.d.ts** or **.ts** is a module but you want to add global declarations.

---

## Q5. (Medium) What does **/// <reference types="node" />** do?

**Answer:**  
It’s a **triple-slash directive** that includes **@types/node** in the compilation. So Node globals (**process**, **Buffer**, etc.) are available. Equivalent to having **"types": ["node"]** in **tsconfig** or installing **@types/node**. Use in a file that needs Node types without importing from **"node"**.

---

## Q6. (Medium) What is the **types** or **typeRoots** option in **tsconfig**?

**Answer:**  
**typeRoots** — list of directories where TS looks for **@types**-style packages (e.g. **./node_modules/@types**). **types** — list of package names to include (e.g. **["node", "jest"]**); only those are loaded from typeRoots. Default **typeRoots** is **node_modules/@types**; default **types** is “all in typeRoots.” Setting **types** limits which **@types** are included.

---

## Q7. (Tough) How do you publish types for a library? What is **types** or **typings** in **package.json**?

**Answer:**  
In **package.json**: **"types": "dist/index.d.ts"** (or **"typings"**) points to the main declaration file. TS and editors use it when someone imports your package. Generate **.d.ts** with **declaration: true** in **tsconfig**. For a dual **ESM + CJS** package, use **exports** with **types** condition: **"exports": { ".": { "types": "./dist/index.d.ts", "import": "...", "require": "..." } }**.

---

## Q8. (Tough) What is an **ambient module** vs a **module augmentation**?

**Answer:**  
**Ambient module**: **declare module "x" { }** — declares the module **"x"** from scratch (e.g. for an untyped lib). **Module augmentation**: you **declare module "x" { }** and add/override exports — they **merge** with existing declarations for **"x"**. So augmentation extends a module that already has types (e.g. **@types/express**); ambient is for “no types yet.”

---

## Q9. (Tough) How do you type a global variable that exists only in a browser (e.g. **window.myLib**)?

**Answer:**  
**declare global { interface Window { myLib: MyLibType } }** in a **.d.ts** or **.ts** file that is a module (then add **export {}** if needed so **declare global** is valid). Or in a global **.d.ts** (no import/export): **interface Window { myLib: MyLibType }** (merges with **Window**). Then **window.myLib** is typed.

---

## Q10. (Tough) What is **declare namespace** vs **declare module**? When use which?

**Answer:**  
**declare namespace N { }** — declares a **namespace** (global or in a module) that exists at runtime. **declare module "m" { }** — declares a **module** (the string is the module path/specifier). Use **namespace** for global objects (e.g. **declare namespace NodeJS { }**). Use **module "name"** for typing **import "name"** or **require("name")**. Namespaces can nest; modules are flat by path.
