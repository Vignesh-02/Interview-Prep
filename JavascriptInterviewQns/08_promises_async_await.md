# 8. Promises and async/await

## Q1. What are the three states of a Promise?

**Answer:**  
(1) **Pending**: Initial state, neither fulfilled nor rejected. (2) **Fulfilled**: Operation completed; the promise has a value. (3) **Rejected**: Operation failed; the promise has a reason. A promise is **settled** when it is either fulfilled or rejected (no longer pending).

---

## Q2. What is the output of this code?

**Question:**
```javascript
const p = new Promise((resolve) => {
  console.log(1);
  resolve(2);
  console.log(3);
});
p.then((v) => console.log(v));
console.log(4);
```

**Answer:**  
Order: **1**, **3**, **4**, **2**. The executor runs synchronously (1, then resolve(2), then 3). `then` callbacks run in the microtask queue after the current script. So 4 runs, then the microtask runs and logs 2.

---

## Q3. What is the difference between `.then()`/`.catch()` and async/await?

**Answer:**  
`.then()`/`.catch()` chain callbacks and return new promises; control flow is callback-based. **async/await** lets you write asynchronous code in a linear, synchronous style: `await` pauses the async function until the promise settles and unwraps the value (or throws on rejection). Under the hood, async/await still uses promises.

---

## Q4. How do you run two promises in parallel and wait for both?

**Answer:**  
Use **`Promise.all([p1, p2])`**. It returns a promise that fulfills with an array of results when all fulfill, or rejects when the first rejects. For “wait for all to settle” (success or failure), use **`Promise.allSettled([p1, p2])`**.

---

## Q5. What does this async function return?

**Question:**
```javascript
async function getValue() {
  return 42;
}
console.log(getValue());
```

**Answer:**  
It logs a **Promise** (not 42). An async function always returns a promise. The value 42 is the fulfilled value of that promise. To get 42 you’d do `getValue().then(console.log)` or `await getValue()` inside another async function.

---

## Q6. How do you handle errors in async/await?

**Answer:**  
Use **try/catch** around the awaited call. Rejected promises throw inside the async function, so catch handles them:

```javascript
async function fetchData() {
  try {
    const res = await fetch(url);
    const data = await res.json();
    return data;
  } catch (err) {
    console.error(err);
  }
}
```

You can also use `.catch()` on the returned promise: `fetchData().catch(console.error)`.

---

## Q7. Implement `Promise.all` from scratch (simplified).

**Answer:**
```javascript
function myPromiseAll(promises) {
  return new Promise((resolve, reject) => {
    if (!Array.isArray(promises)) {
      return reject(new TypeError('Argument must be an array'));
    }
    const results = [];
    let completed = 0;
    const len = promises.length;
    if (len === 0) return resolve(results);
    promises.forEach((p, i) => {
      Promise.resolve(p).then(
        (val) => {
          results[i] = val;
          completed++;
          if (completed === len) resolve(results);
        },
        (err) => reject(err)
      );
    });
  });
}
```

---

## Q8. What is the output?

**Question:**
```javascript
async function foo() {
  console.log(1);
  await Promise.resolve();
  console.log(2);
}
foo();
console.log(3);
```

**Answer:** **1**, **3**, **2**. The async function runs until the first `await`; then it suspends and the rest of the script runs (3). After the current task and microtasks, the awaited promise is done, so the async function resumes and logs 2.

---

## Q9. What is `Promise.race`? Give a use case.

**Answer:**  
`Promise.race(iterable)` returns a promise that settles (fulfills or rejects) as soon as one of the input promises settles, with that promise’s value or reason. Use case: timeout—race a real operation against a timeout promise and reject if the timeout wins.

---

## Q10. (Tricky) What gets logged?

**Question:**
```javascript
Promise.resolve()
  .then(() => {
    console.log(1);
    throw new Error('err');
  })
  .catch(() => console.log(2))
  .then(() => console.log(3))
  .catch(() => console.log(4));
```

**Answer:** **1**, **2**, **3**. First `then` logs 1 and throws; the next `catch` handles it and logs 2. That catch returns a fulfilled promise (undefined), so the next `then` runs and logs 3. No second rejection, so 4 is never logged.
