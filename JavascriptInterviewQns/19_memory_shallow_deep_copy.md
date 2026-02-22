# 19. Memory, Shallow/Deep Copy

## Q1. What is a shallow copy? What is still shared?

**Answer:**  
A **shallow copy** is a new object (or array) whose top-level properties are copied. If a property value is a reference (object/array), only the reference is copied, so the original and the copy share nested objects. Changing a nested object in one is visible in the other.

---

## Q2. Implement a shallow copy for a plain object (no prototype/enumerable details).

**Answer:**
```javascript
function shallowCopy(obj) {
  return { ...obj };
}
// or Object.assign({}, obj)
```

---

## Q3. What is a deep copy? When is it needed?

**Answer:**  
A **deep copy** is a copy where every nested object/array is also copied recursively, so no reference is shared with the original. Needed when you must mutate the copy without affecting the original, or when the structure is a DAG/tree and you want full independence.

---

## Q4. What are the limitations of `JSON.parse(JSON.stringify(obj))` for deep copy?

**Answer:**  
- Loses functions, undefined, symbols.  
- Date becomes string.  
- RegExp, Map, Set lost or wrong.  
- Circular references throw.  
- Non-enumerable and prototype chain are not preserved.  
Use for simple, JSON-serializable data only.

---

## Q5. Implement a simple deep clone that handles arrays and plain objects (no cycles).

**Answer:**
```javascript
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  const copy = Array.isArray(obj) ? [] : {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      copy[key] = deepClone(obj[key]);
    }
  }
  return copy;
}
```

---

## Q6. How would you handle circular references in a deep clone?

**Answer:**  
Keep a `Map` (or WeakMap) of “already visited” objects. Before recursing into an object, check if it’s in the map; if so, return the corresponding cloned object. When you create a new clone, add the pair (original, clone) to the map. This way cycles become references to the same clone.

---

## Q7. What is the difference between `structuredClone` and a custom deep clone?

**Answer:**  
**structuredClone** (global in modern JS) supports many built-in types (Date, RegExp, Map, Set, etc.) and circular references. It does not clone functions, symbols, or some host objects. A **custom clone** can handle classes, functions (or skip them), and custom types, but you must implement and maintain it.

---

## Q8. Why might modifying a shared reference (e.g. from a shallow copy) cause bugs?

**Answer:**  
Multiple parts of the app might assume they “own” or that no one else will change the same object. One place mutates a nested object thinking it’s local; another place (holding the same reference) sees the change unexpectedly. Hard-to-trace bugs and broken invariants. Prefer immutability or explicit ownership.

---

## Q9. What does this snippet demonstrate?

**Question:**
```javascript
const original = { a: 1, nested: { b: 2 } };
const copy = { ...original };
copy.nested.b = 99;
console.log(original.nested.b);
```

**Answer:** **99.** Shallow copy: `copy.nested` is the same object as `original.nested`. Mutating `copy.nested.b` mutates the shared object, so `original.nested.b` is 99.

---

## Q10. (Tricky) How does garbage collection interact with closures and global references?

**Answer:**  
An object is eligible for GC when nothing can reach it. Closures hold references to their outer scope; if a closure is still reachable (e.g. stored in a global or long-lived object), the whole scope chain stays in memory. Global variables and module-level variables keep their references until the context is torn down. So long-lived closures and globals can prevent GC of large structures; avoid keeping unnecessary references.
