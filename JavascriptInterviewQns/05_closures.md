# 5. Closures

## Q1. What is a closure?

**Answer:**  
A closure is when a function “remembers” the variables from the scope where it was created, even after that outer scope has finished executing. So an inner function can access and use the outer function’s variables long after the outer function has returned.

---

function foo(a){
    return function bar(b){
        return a + " " + b
    }
};

const val = foo('hello')
console.log(val('yello'))

## Q2. Write a simple closure and explain why it works.

**Answer:**
```javascript
function makeGreeter(greeting) {
  return function (name) {
    return greeting + ', ' + name;
  };
}
const sayHi = makeGreeter('Hi');
sayHi('Alice'); // "Hi, Alice"
```
`sayHi` is the inner function. It was created inside `makeGreeter` and closes over the parameter `greeting`. When `makeGreeter('Hi')` returns, `greeting` would normally be gone, but the returned function keeps a reference to that scope, so `greeting` stays `'Hi'`.

---

## Q3. What is the output of this loop and how do you fix it with a closure?

**Question:**
```javascript
for (var i = 0; i < 3; i++) {
  setTimeout(function () {
    console.log(i);
  }, 100);
}
```

**Answer:**  
Prints `3` three times (one shared `var i`).  
Fix with IIFE closure to capture `i` per iteration:
```javascript
for (var i = 0; i < 3; i++) {
  (function (j) {
    setTimeout(function () {
      console.log(j);
    }, 100);
  })(i);
}
```
Or use `let i` so each iteration has its own `i`.

---

## Q4. How do closures enable private variables in JavaScript?

**Answer:**  
Variables in an outer function are not accessible from outside. If you return an object or functions that use those variables, only those returned functions can read/update them—effectively private state:

```javascript
function createCounter() {
  let count = 0;
  return {
    increment() {
      return ++count;
    },
    getCount() {
      return count;
    }
  };
}
```

---

## Q5. What will this code output?

**Question:**
```javascript
function buildFunctions() {
  const arr = [];
  for (var i = 0; i < 3; i++) {
    arr.push(function () {
      console.log(i);
    });
  }
  return arr;
}
const funcs = buildFunctions();
funcs[0]();
funcs[1]();
funcs[2]();
```

**Answer:**  
`3`, `3`, `3`. All three functions close over the same `var i`. When they run, the loop has ended and `i` is 3. Fix: use `let i` or capture `i` in an IIFE with a parameter.

---

## Q6. What is a potential downside of closures (e.g. memory)?

**Answer:**  
Closures keep their outer scope in memory. If you hold references to closures (e.g. in global variables or long-lived objects), the outer scope cannot be garbage-collected. Too many or large closures can increase memory use. Avoid keeping unnecessary references when possible.

---

## Q7. Implement a function that only runs once using a closure.

**Answer:**
```javascript
function once(fn) {
  let called = false;
  let result;
  return function (...args) {
    if (!called) {
      called = true;
      result = fn.apply(this, args);
    }
    return result;
  };
}
const init = once(() => console.log('Initialized'));
init(); // logs "Initialized"
init(); // no log
```

---

## Q8. Predict the output.

**Question:**
```javascript
function outer() {
  const x = 10;
  function inner() {
    console.log(x);
  }
  x = 20;
  return inner;
}
const fn = outer();
fn();
```

**Answer:**  
**20.** Closures capture variables by reference, not by value. When `inner` runs, it reads the current `x` in that scope, which was set to 20 before `inner` was returned.

---

## Q9. Write a closure-based function that creates a multiplier.

**Answer:**
```javascript
function createMultiplier(factor) {
  return function (n) {
    return n * factor;
  };
}
const double = createMultiplier(2);
const triple = createMultiplier(3);
console.log(double(5));  // 10
console.log(triple(5));  // 15
```

---

## Q10. (Tricky) What is logged?

**Question:**
```javascript
let count = 0;
(function immediate() {
  if (count === 0) {
    let count = 1;
    console.log(count);
  }
  console.log(count);
})();
```

**Answer:**  
First log: **1** (inner block-scoped `count`).  
Second log: **0** (outer `count`; inner `count` is not in scope outside the `if` block). The inner `let count` shadows the outer one only inside the block.
