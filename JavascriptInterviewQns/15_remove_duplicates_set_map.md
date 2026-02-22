# 15. Remove Duplicates, Set & Map

## Q1. How do you remove duplicates from an array of primitives (e.g. numbers)?

**Answer:**
```javascript
const arr = [1, 2, 2, 3, 1, 4];
const unique = [...new Set(arr)];  // [1, 2, 3, 4]
```
`Set` keeps unique values; spread back into an array. Works for strings and numbers; for objects, see below.

---

## Q2. Remove duplicates from an array of objects by a key (e.g. keep one per `id`).

**Answer:**
```javascript
function uniqueBy(arr, key) {
  const seen = new Set();
  return arr.filter((obj) => {
    const k = typeof key === 'function' ? key(obj) : obj[key];
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}
```

---

## Q3. What is the difference between `Set` and `WeakSet`?

**Answer:**  
- **Set**: Holds any values; references are strong. Keys are not garbage-collected while in the set.
- **WeakSet**: Holds only **objects**. References are weak: if nothing else references the object, it can be GC’d and will disappear from the WeakSet. No iteration, no `.size`, no primitives. Use for tagging objects without preventing GC.

---

## Q4. When would you use `Map` instead of a plain object `{}`?

**Answer:**  
Use **Map** when: keys are not strings (objects, numbers, etc.), you need insertion order, you need a reliable `.size`, or you want to avoid prototype/key collisions. Objects are fine for string keys and when you don’t need those guarantees.

---

## Q5. Implement “two sum”: return indices of two numbers that add up to `target`. Assume one solution exists.

**Answer:**
```javascript
function twoSum(nums, target) {
  const map = new Map();
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    if (map.has(need)) return [map.get(need), i];
    map.set(nums[i], i);
  }
}
```

---

## Q6. Find the first duplicate in an array (value that appears at least twice). Return the value or undefined.

**Answer:**
```javascript
function firstDuplicate(arr) {
  const seen = new Set();
  for (const v of arr) {
    if (seen.has(v)) return v;
    seen.add(v);
  }
  return undefined;
}
```

---

## Q7. Count frequency of each element and return an object (or Map).

**Answer:**
```javascript
function frequency(arr) {
  const map = new Map();
  for (const v of arr) {
    map.set(v, (map.get(v) || 0) + 1);
  }
  return map;
}
// or object: arr.reduce((acc, v) => ({ ...acc, [v]: (acc[v] || 0) + 1 }), {})
```

---

## Q8. Given two arrays, find their intersection (unique common elements).

**Answer:**
```javascript
function intersection(a, b) {
  const setB = new Set(b);
  return [...new Set(a)].filter((x) => setB.has(x));
}
```

---

## Q9. What does `Map` preserve that object iteration does not?

**Answer:**  
**Insertion order.** When you iterate a Map with `for...of` or `.forEach()`, entries come in the order they were inserted. Plain object key order is now predictable (integer keys sorted, then string keys by insertion, then symbols), but Map guarantees insertion order for all keys and is often clearer for “key → value” collections.

---

## Q10. (Tricky) Remove duplicates from an array of objects by “value equality” (e.g. same keys and values), without a key function.

**Answer:**  
One approach: serialize to a comparable form and use a Set to track seen:

```javascript
function uniqueByValue(arr) {
  const seen = new Set();
  return arr.filter((obj) => {
    const key = JSON.stringify(Object.keys(obj).sort().map((k) => [k, obj[k]]));
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
```
Note: JSON.stringify has limitations (key order, undefined, functions). For robust value equality, use a library or a custom hash. For “same reference” uniqueness, use `Set` with a symbol or identity key per object.
