# 26. Module Systems (ESM vs CJS) (Senior)

## Q1. What are the key differences between CommonJS (require/module.exports) and ES Modules (import/export)?

**Answer:**  
**CJS**: Synchronous loading; runtime resolution; `require()` returns the module object; `module.exports` or `exports`; used in Node by default (legacy). **ESM**: Static structure (imports/exports parsed at load time); asynchronous loading possible; `import`/`export` syntax; single export or named exports; default in browsers and modern Node. ESM enables tree-shaking; CJS does not. ESM has a single shared module instance per spec; CJS caches by path.

---

## Q2. Why can’t you use `import` inside a conditional or `require` at top level in ESM?

**Answer:**  
ESM **import** declarations are static: they are parsed and resolved before the module runs. The spec requires that the set of imports is known at parse time so the loader can fetch and link modules. Conditionals and dynamic code run at runtime, so you can’t put static `import` there. For dynamic loading in ESM you use **`import()`** (dynamic import), which returns a Promise.

---

## Q3. What is tree-shaking and why does it require ES modules?

**Answer:**  
**Tree-shaking** is dead-code elimination: bundlers (e.g. webpack, Rollup) analyze the static import/export graph and drop exports that are never imported. It works with ESM because the dependency graph is statically analyzable. CJS’s dynamic `require()` and runtime `module.exports` make it impossible to know at build time what is used, so tree-shaking is limited or not applied to CJS.

---

## Q4. In Node.js, how do you use ES modules (file extension, package.json, and interop with require)?

**Answer:**  
Use **`.mjs`** extension or **`"type": "module"`** in package.json so `.js` is treated as ESM. In ESM files you use `import`/`export`; `require` is not available by default. To load a CJS module from ESM use `import cjs from 'cjs-pkg'` (default import of `module.exports`). To use ESM from CJS you must use dynamic `import()` (returns a Promise), since CJS is synchronous.

---

## Q5. What is the difference between default export and named exports? When would you prefer one?

**Answer:**  
**Default export**: One per module; import with any name: `import X from './m'`. Good for the “main” thing the module represents (e.g. a React component or class). **Named exports**: Multiple per module; names must match (or use alias). Better for utilities, constants, or when you want explicit names and tree-shaking of unused names. Libraries often use named exports for better DX and tree-shaking.

---

## Q6. What does `import * as ns from 'module'` give you? How is it different from a default import?

**Answer:**  
`import * as ns` creates a **module namespace object**: an object whose properties are the module’s (own) exports. So `ns.foo` is the named export `foo`; `ns.default` is the default export if present. It’s different from `import def from 'module'`: that gives only the default export, not the namespace. Use `* as ns` when you need both default and named or want to pass the module object around.

---

## Q7. What is circular dependency and how do ESM and CJS handle it differently?

**Answer:**  
**Circular dependency**: A imports B, B imports A (directly or through a chain). In **CJS**, when B is loading and does `require(A)`, A might not be finished; so B can see a partially initialized A (e.g. undefined exports). In **ESM**, the loader builds the graph first and instantiates in dependency order; exports are bound live, so by the time code runs, cycles are wired. You can still get undefined if you access an export before its declaration has run.

---

## Q8. What is `export { x as y }` and re-exporting? Why is it useful?

**Answer:**  
`export { x as y }` re-exports a binding from the current module under a different name. `export { foo } from './other'` re-exports without bringing `foo` into the current module’s scope. Useful for **barrel files** (one entry that re-exports many modules) and for exposing a public API while keeping internal structure modular.

---

## Q9. In a bundler (e.g. webpack), what is the difference between static and dynamic `import()`?

**Answer:**  
**Static** `import 'x'` / `import a from 'x'`: Resolved at build time; bundled into the same chunk (unless the bundler splits). **Dynamic** `import('x')`: Treated as a split point; the module is usually in a separate chunk and loaded at runtime when the `import()` runs. Used for code-splitting and lazy loading. The bundler may still analyze string literals in `import('path')` to include that module in the split chunk.

---

## Q10. How would you design a small library to support both ESM and CJS consumers (dual package)?

**Answer:**  
(1) Publish two entry points in **package.json**: `"main"` for CJS (e.g. `dist/index.cjs`) and `"module"` or `"exports"` for ESM (e.g. `dist/index.js`). (2) Use **"exports"** with conditions: `"import"` → ESM file, `"require"` → CJS file. (3) Build the same source to both formats (e.g. with Rollup or tsup). (4) Optionally ship TypeScript types via `"types"`. (5) Avoid relying on `__dirname`/`require` in shared code; use conditional exports or separate entry files so ESM and CJS each get the right implementation.
