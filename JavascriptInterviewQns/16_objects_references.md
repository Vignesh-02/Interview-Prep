# 16. Objects and Reference Types

## Q1. What is the difference between primitive and reference types in JavaScript?

**Answer:**  
**Primitives** (number, string, boolean, null, undefined, symbol, bigint) are stored by value. Copying or passing them copies the value. **Reference types** (objects, arrays, functions) are stored by reference. Assigning or passing copies the reference, so two variables can point to the same object and mutations are visible from both.

---

## Q2. What does this code output and why?

**Question:**
```javascript
const a = { x: 1 };
const b = a;
b.x = 2;
console.log(a.x);
```

**Answer:** **2.** `b` and `a` reference the same object. Changing `b.x` mutates that object, so `a.x` is also 2.

---

## Q3. How do you create a shallow copy of an object? Of an array?

**Answer:**  
Object: `const copy = { ...obj };` or `Object.assign({}, obj)`.  
Array: `const copy = [...arr];` or `arr.slice()`.  
These copy only the top level; nested objects/arrays are still shared (shallow).

---

## Q4. How do you create a deep copy? What are the pitfalls?

**Answer:**  
- **JSON**: `JSON.parse(JSON.stringify(obj))`. Fails for functions, undefined, symbols, circular references, and non-JSON types (e.g. Date becomes string).
- **Structured clone**: `structuredClone(obj)` (modern browsers/Node) handles many built-in types and circular refs, but not functions or symbols.
- **Lodash**: `_.cloneDeep(obj)` for a robust implementation.  
For full control (functions, classes), use a custom recursive copier or a library.

---

## Q5. What is the output?

**Question:**
```javascript
const o1 = { a: 1 };
const o2 = { a: 1 };
console.log(o1 === o2);
console.log(o1 == o2);
```

**Answer:**  
Both **false**. Two different objects are never equal by reference. `==` does not compare object contents; it compares references (or coerces to primitives if one side is primitive).

---

## Q6. How do you check if an object has a property (own, not inherited)?

**Answer:**  
- **Own**: `Object.hasOwn(obj, 'prop')` or `Object.prototype.hasOwnProperty.call(obj, 'prop')`.
- **Including inherited**: `'prop' in obj`.

---

## Q7. What does `Object.freeze` do? Is the freeze deep?

**Answer:**  
`Object.freeze(obj)` makes `obj` non-extensible and makes its own properties non-writable and non-configurable. You cannot add, remove, or change properties. It is **not** deep: nested objects can still be mutated. For deep freeze, recursively freeze nested objects.

---

## Q8. What is the difference between `Object.assign` and the spread operator for merging?

**Answer:**  
Both do shallow merge. `Object.assign(target, ...sources)` mutates `target` and returns it. Spread `{ ...a, ...b }` creates a new object. Spread is often preferred when you want to avoid mutating. Later sources override earlier in both (same property order semantics for own enumerable properties).

---

## Q9. Predict the output.

**Question:**
```javascript
const arr = [1, 2, 3];
const fn = (list) => {
  list = [4, 5, 6];
  return list;
};
console.log(fn(arr));
console.log(arr);
```

**Answer:**  
`fn(arr)` returns `[4, 5, 6]` and logs it. `arr` is still **`[1, 2, 3]`**. Reassigning `list` inside the function only changes the local parameter; it does not change the original `arr` reference. So the caller’s `arr` is unchanged.

---

## Q10. (Tricky) What does this log?

**Question:**
```javascript
const obj = {
  a: 1,
  get b() {
    return this.a + 1;
  }
};
const copy = { ...obj };
obj.a = 10;
console.log(copy.b);
```

**Answer:** **2.** Spread copies own enumerable properties. The getter is copied as a property with the **value** it had when copied: `copy.b` was evaluated once during the spread, so `copy.b` is 2 (1+1). It’s not a live getter on `copy` that would use `copy.a`. So when `obj.a` is set to 10, `copy` is unchanged; `copy.a` is still 1, and `copy.b` is the number 2.
