# 17. ES6+ Features (Destructuring, Spread, etc.)

## Q1. What is destructuring? Give examples for array and object.

**Answer:**  
Destructuring unpacks values from arrays or properties from objects into variables.

```javascript
const [a, b] = [1, 2];           // a=1, b=2
const { x, y } = { x: 1, y: 2 }; // x=1, y=2
const [first, ...rest] = [1, 2, 3]; // first=1, rest=[2,3]
const { name: n, age = 0 } = obj;   // rename and default
```

---

## Q2. How do you swap two variables using destructuring?

**Answer:**
```javascript
let a = 1, b = 2;
[a, b] = [b, a];
// a=2, b=1
```

---

## Q3. What does the rest operator (`...`) do in destructuring vs in function parameters?

**Answer:**  
In **destructuring**: rest collects the remaining elements/properties into an array (array destructuring) or object (object destructuring).  
In **function parameters**: rest collects remaining arguments into one array parameter. Only one rest parameter is allowed and it must be last.

---

## Q4. What is the output?

**Question:**
```javascript
const { a: x, b: y } = { a: 1, b: 2 };
console.log(a, b, x, y);
```

**Answer:**  
**ReferenceError** for `a` and `b`. The syntax `{ a: x }` means “take property `a` and assign to variable `x`”. So only `x` and `y` exist (1 and 2). `a` and `b` are not defined as variables.

---

## Q5. Explain default parameters. What is the value of `arguments` when using them?

**Answer:**  
Default parameters let you assign a default value when the argument is `undefined`: `function f(a = 1, b = 2) {}`. When you use default parameters (or rest), the `arguments` object does not reflect the default/rest values in strict mode; in non-strict it can be confusing. Prefer not to rely on `arguments` when using default/rest.

---

## Q6. What are template literals and tagged template literals?

**Answer:**  
**Template literals**: Backtick strings with `${expression}` for interpolation and support for multi-line strings.  
**Tagged templates**: A function name before the template; the function receives an array of string segments and the interpolated values: `tag`Hello ${name}` → tag(['Hello ', ''], name). Used for sanitization, i18n, DSLs.

---

## Q7. What does this destructuring do?

**Question:**
```javascript
const [,, third] = [1, 2, 3, 4];
const { a, b, ...rest } = { a: 1, b: 2, c: 3, d: 4 };
```

**Answer:**  
First: skips first two elements, assigns the third to `third` → `third === 3`.  
Second: `a === 1`, `b === 2`, `rest === { c: 3, d: 4 }`. Rest collects remaining own enumerable properties.

---

## Q8. What are shorthand property and method syntax in object literals?

**Answer:**  
When the property name and the variable name are the same: `{ name }` instead of `{ name: name }`. Methods can be written as `{ method() {} }` instead of `{ method: function () {} }`. Arrow functions are not “methods” in the same way (no own `this`).

---

## Q9. What is the difference between spread in array vs object literal?

**Answer:**  
- **Array**: `[...arr]` or `[...arr1, ...arr2]` spreads iterable elements into the new array. Only iterables (and array-like with indexing) work.
- **Object**: `{ ...obj }` copies own enumerable properties. Works with any object. Later properties override earlier: `{ ...a, ...b }`.

---

## Q10. (Tricky) What is logged?

**Question:**
```javascript
const obj = { a: 1, b: 2, c: 3 };
const { a, ...o } = obj;
console.log(o);
const copy = { ...obj, a: 10 };
console.log(copy);
```

**Answer:**  
First: `o` is **`{ b: 2, c: 3 }`** (rest after taking `a`).  
Second: `copy` is **`{ a: 10, b: 2, c: 3 }`** — spread copies `obj` then `a: 10` overrides, so `a` is 10.
