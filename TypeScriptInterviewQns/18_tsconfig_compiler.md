# 18. tsconfig and Compiler Options (strict, noImplicitAny)

## Q1. (Easy) What is **tsconfig.json**? What are **include** and **exclude**?

**Answer:**  
**tsconfig.json** is the TypeScript project config. **include** — which files/folders to compile (e.g. **["src/**/*"]**). **exclude** — which to skip (e.g. **node_modules**, **dist**). Default **include** is all **.ts** in the project; **exclude** defaults include **node_modules** and **outDir**.

---

## Q2. (Easy) What does **strict** do? Name two flags it enables.

**Answer:**  
**strict** enables a set of strict checks. It includes **strictNullChecks**, **strictFunctionTypes**, **noImplicitAny**, **strictBindCallApply**, **strictPropertyInitialization**, **noImplicitThis**, **useUnknownInCatchVariables**, and more. Two examples: **noImplicitAny** (error on implicit **any**) and **strictNullChecks** (null/undefined are separate).

---

## Q3. (Easy) What is **noImplicitAny**? What error do you get without it?

**Answer:**  
**noImplicitAny** errors when TypeScript infers **any** (e.g. untyped parameter). Without it, **function f(x) { }** gives **x** type **any** and no error. With it, you must add a type (e.g. **x: number**) or use **x: unknown**. Use it to avoid accidental **any** and keep type safety.

---

## Q4. (Medium) What is **strictNullChecks**? How does it change assignability?

**Answer:**  
With **strictNullChecks**, **null** and **undefined** are not assignable to other types unless explicitly in the union (e.g. **string | null**). So **let s: string = null** errors. You must handle null/undefined (narrowing, optional chaining). Without it, every type implicitly includes null and undefined.

---

## Q5. (Medium) What is **target** and **module**? How do they differ?

**Answer:**  
**target** — which **JS version** to emit (e.g. **ES2020**, **ES5**). **module** — which **module system** to emit (e.g. **commonjs**, **ESNext**, **NodeNext**). So **target: "ES5"** and **module: "ESNext"** means emit ES5 code with ESNext module syntax (then bundler may handle modules). **module** can also be **NodeNext** for Node’s resolution.

---

## Q6. (Medium) What is **skipLibCheck**? When would you turn it on?

**Answer:**  
**skipLibCheck: true** — skip type checking of **.d.ts** (declaration) files. Speeds up compilation; useful when **node_modules** types have errors you can’t fix. Slightly less safe (bugs in lib types go unchecked). Often enabled in large projects for build speed.

---

## Q7. (Tough) What is **strictFunctionTypes**? Why are function parameters checked contravariantly?

**Answer:**  
**strictFunctionTypes** enforces **contravariance** for function parameters (and covariance for returns). So a callback **(x: Animal) => void** is not assignable to **(x: Dog) => void** — the callee might pass a Dog and the first callback could use only Animal, but the type system forbids it to prevent passing a less capable function. With it off, parameters are bivariant (unsafe). Enable for type-safe callbacks.

---

## Q8. (Tough) What is **noUncheckedIndexedAccess** (TS 4.1+)? What type does **arr[i]** get?

**Answer:**  
**noUncheckedIndexedAccess** makes indexed access **arr[i]** or **obj[k]** have type **T | undefined** (when the index might be out of bounds). So **arr[0]** is **number | undefined** for **number[]**. You must narrow or use **!** when you know the index is valid. Reduces “undefined at runtime” bugs from invalid indices.

---

## Q9. (Tough) What is **moduleResolution**: **"node"** vs **"node16"** / **"bundler"**?

**Answer:**  
**moduleResolution** is how TS resolves **import** paths. **"node"** — classic Node resolution (e.g. **"main"**, **index.js**). **"node16"** / **"nodenext"** — Node’s ESM resolution (package **exports**, **import**/**require** conditions). **"bundler"** — for use with a bundler (ESM-style resolution, no need to add **.js** extensions in emitted code). Use **node16**/ **nodenext** for Node ESM; **bundler** for webpack/vite/etc.

---

## Q10. (Tough) How do **paths** and **baseUrl** work? What are they for?

**Answer:**  
**baseUrl** — base for non-relative module resolution (e.g. **"."** for project root). **paths** — map import paths to actual paths: **"@/*": ["src/*"]**. So **import x from "@/utils"** resolves to **src/utils**. Used for aliases; the bundler or runtime must support the same mapping (e.g. webpack **resolve.alias**). TypeScript only uses them for type resolution; they don’t rewrite the emitted import path unless a tool does it.
