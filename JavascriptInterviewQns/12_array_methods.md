# 12. Array Methods (map, filter, reduce)

## Q1. What does `map` do? What does it return?

**Answer:**  
`map(callback)` creates a **new array** by calling `callback` on each element. The return value of the callback becomes the element at that index in the new array. It does not mutate the original array. Length of the result equals the original length.

---

## Q2. Implement a function that flattens an array one level (like `flat(1)`).

**Answer:**
```javascript
function flattenOne(arr) {
  return arr.reduce((acc, item) => {
    return acc.concat(Array.isArray(item) ? item : [item]);
  }, []);
}
// or: arr.flat(1) or [].concat(...arr)
```

---

## Q3. Use `reduce` to implement `map`.

**Answer:**
```javascript
function mapWithReduce(arr, fn) {
  return arr.reduce((acc, item, i) => {
    acc.push(fn(item, i, arr));
    return acc;
  }, []);
}
```

---

## Q4. What is the difference between `find` and `filter`?

**Answer:**  
- **filter**: Returns a **new array** of all elements that pass the predicate.
- **find**: Returns the **first element** that passes the predicate, or `undefined`. It stops as soon as one match is found.

---

## Q5. Flatten an array of any depth using `reduce` and recursion.

**Answer:**
```javascript
function flattenDeep(arr) {
  return arr.reduce((acc, item) => {
    return acc.concat(Array.isArray(item) ? flattenDeep(item) : item);
  }, []);
}
```

---

## Q6. What does `reduce` return when the array is empty and no initial value is provided?

**Answer:**  
It **throws** `TypeError: Reduce of empty array with no initial value`. You must either pass an initial value or ensure the array is not empty when using reduce without one.

---

## Q7. Implement `groupBy`: group array of objects by a key (e.g. by `category`).

**Answer:**
```javascript
function groupBy(arr, key) {
  return arr.reduce((acc, obj) => {
    const k = typeof key === 'function' ? key(obj) : obj[key];
    (acc[k] = acc[k] || []).push(obj);
    return acc;
  }, {});
}
```

---

## Q8. What do `some` and `every` return? When do they short-circuit?

**Answer:**  
- **some**: Returns true if any element passes the predicate; false if none. Stops as soon as one passes.
- **every**: Returns true if every element passes; false as soon as one fails. Empty array: `every` returns true, `some` returns false.

---

## Q9. Use `reduce` to implement a function that returns the maximum value in an array of numbers.

**Answer:**
```javascript
function maxReducer(arr) {
  if (arr.length === 0) return undefined;
  return arr.reduce((max, n) => (n > max ? n : max), arr[0]);
}
```

---

## Q10. (Tricky) What is the output?

**Question:**
```javascript
const arr = [1, 2, 3];
const result = arr.map((n, i) => {
  arr.push(n * 10);
  return n + i;
});
console.log(result);
console.log(arr);
```

**Answer:**  
`map` iterates over the initial length (3). During iteration you push three more items; those are not visited by this `map`. So:
- **result**: `[1, 3, 5]` (1+0, 2+1, 3+2).
- **arr**: `[1, 2, 3, 10, 20, 30]`. Mutating the array while iterating is allowed but can be confusing; avoid it in production.
