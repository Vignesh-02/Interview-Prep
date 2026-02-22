# 10. Callbacks and Higher-Order Functions

## Q1. What is a callback function?

**Answer:**  
A **callback** is a function passed as an argument to another function, to be invoked later (e.g. when an async operation completes, when an event occurs, or after some work). The receiving function “calls back” by invoking the callback. Example: `setTimeout(() => console.log('done'), 1000)` — the arrow function is the callback.

---

## Q2. What is a higher-order function (HOF)?

**Answer:**  
A **higher-order function** is a function that either (1) takes one or more functions as arguments, or (2) returns a function (or both). Examples: `map`, `filter`, `reduce`, `setTimeout`, `once`. They enable abstraction and composition.

---

## Q3. Implement `map` without using the built-in array method.

**Answer:**
```javascript
function map(arr, callback) {
  const result = [];
  for (let i = 0; i < arr.length; i++) {
    result.push(callback(arr[i], i, arr));
  }
  return result;
}
```

---

## Q4. What is “callback hell” and how do Promises/async-await help?

**Answer:**  
Callback hell is deeply nested callbacks (e.g. multiple async steps, each with its own callback), which make code hard to read and error-handle. Promises allow chaining with `.then()/.catch()`. Async/await lets you write sequential-looking code with `await`, avoiding nested callbacks and making flow and error handling clearer.

---

## Q5. Implement `filter` from scratch.

**Answer:**
```javascript
function filter(arr, predicate) {
  const result = [];
  for (let i = 0; i < arr.length; i++) {
    if (predicate(arr[i], i, arr)) {
      result.push(arr[i]);
    }
  }
  return result;
}
```

---

## Q6. What does this code do and what could go wrong?

**Question:**
```javascript
function doSomething(callback) {
  setTimeout(() => {
    callback(null, 'result');
  }, 1000);
}
doSomething((err, data) => {
  if (err) throw err;
  console.log(data);
});
```

**Answer:**  
It runs an async operation and calls the callback with (null, 'result') after 1 second. **Problem**: Throwing inside the callback does not propagate to the caller of `doSomething`; the error happens in the timer callback, so it can be unhandled. Better: use try/catch in the callback and pass errors to a central handler, or return a Promise and use .catch().

---

## Q7. Write a higher-order function that runs a function only if a condition is true.

**Answer:**
```javascript
function when(condition, fn) {
  return function (...args) {
    if (condition(...args)) {
      return fn(...args);
    }
  };
}
// usage: const safeLog = when(() => true, console.log);
```

---

## Q8. Implement `reduce` from scratch.

**Answer:**
```javascript
function reduce(arr, reducer, initialValue) {
  let accumulator = initialValue;
  let start = 0;
  if (arguments.length < 3) {
    if (arr.length === 0) throw new TypeError('Reduce of empty array with no initial value');
    accumulator = arr[0];
    start = 1;
  }
  for (let i = start; i < arr.length; i++) {
    accumulator = reducer(accumulator, arr[i], i, arr);
  }
  return accumulator;
}
```

---

## Q9. What is the “error-first callback” convention (Node-style)?

**Answer:**  
The callback is called with `(err, ...results)`. If the operation failed, the first argument is an Error (or other truthy value). If it succeeded, the first argument is null/undefined and the rest are the results. This allows a single callback to handle both success and failure: `if (err) return handleError(err); use(results);`

---

## Q10. Create a function `pipe(fn1, fn2, fn3)` that returns a function which runs the argument through fn1, then fn2, then fn3.

**Answer:**
```javascript
function pipe(...fns) {
  return function (value) {
    return fns.reduce((acc, fn) => fn(acc), value);
  };
}
const add1 = (x) => x + 1;
const double = (x) => x * 2;
const add1ThenDouble = pipe(add1, double);
console.log(add1ThenDouble(5)); // (5+1)*2 = 12
```
