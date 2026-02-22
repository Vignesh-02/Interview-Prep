# 6. The this Keyword

## Q1. What determines the value of `this` in JavaScript?

**Answer:**  
`this` is determined by **how** a function is called (call site), not where it is defined. The main cases: (1) method call: `obj.method()` → `this` is `obj`. (2) Default in non-strict: standalone call → global object; in strict → `undefined`. (3) `new`: `this` is the new instance. (4) `call`/`apply`/`bind`: explicit `this`.

---

## Q2. What is the output?

**Question:**
```javascript
const obj = {
  name: 'Obj',
  getName: function () {
    return this.name;
  }
};
const getName = obj.getName;
console.log(obj.getName());
console.log(getName());
```

**Answer:**  
`obj.getName()` → **'Obj'** (method call, `this` is `obj`).  
`getName()` → In non-strict: **undefined** or global name (default `this` is global); in strict: error when accessing `this.name` because `this` is `undefined`. The key point: losing the “receiver” (obj) makes `this` no longer the object.

---

## Q3. Explain `call`, `apply`, and `bind`. How do they differ?

**Answer:**
- **call(thisArg, arg1, arg2, ...)**: Invokes the function with a given `this` and individual arguments.
- **apply(thisArg, [args])**: Same as `call` but arguments are passed as an array.
- **bind(thisArg, ...args)**: Returns a new function with `this` (and optionally some arguments) fixed. It does not invoke the function.

```javascript
function greet(greeting, punct) {
  return greeting + ', ' + this.name + punct;
}
const user = { name: 'Alice' };
greet.call(user, 'Hi', '!');   // "Hi, Alice!"
greet.apply(user, ['Hi', '!']); // "Hi, Alice!"
const bound = greet.bind(user, 'Hi');
bound('!');                    // "Hi, Alice!"
```

---

## Q4. What is `this` inside an arrow function?

**Answer:**  
Arrow functions **do not** have their own `this`. They inherit `this` from the enclosing lexical (static) scope at the time they are defined. So `this` inside an arrow function is the same as `this` where the arrow function was written.

---

## Q5. Predict the output.

**Question:**
```javascript
const obj = {
  value: 42,
  getValue: function () {
    return this.value;
  },
  getValueArrow: () => this.value
};
console.log(obj.getValue());
console.log(obj.getValueArrow());
```

**Answer:**  
`obj.getValue()` → **42** (normal function, `this` is `obj`).  
`obj.getValueArrow()` → In browser global context, **undefined** (or global’s value if it has one). The arrow function takes `this` from its enclosing scope (e.g. global or module), not from `obj`.

---

## Q6. How do you fix “losing” `this` when passing a method as a callback?

**Answer:**  
(1) Wrap in an arrow function: `setTimeout(() => obj.method(), 100)`. (2) Bind: `setTimeout(obj.method.bind(obj), 100)`. (3) Wrap in a function that calls with the right receiver: `setTimeout(function () { obj.method(); }, 100)`.

---

## Q7. What does `this` refer to when using `new`?

**Answer:**  
When a function is called with `new`, a new object is created and `this` inside that function refers to that new object. If the function doesn’t return another object, that new object is returned as the result of the `new` expression.

---

## Q8. What is the output of this code?

**Question:**
```javascript
function Person(name) {
  this.name = name;
  setTimeout(function () {
    console.log(this.name);
  }, 100);
}
new Person('Alice');
```

**Answer:**  
After 100ms, the callback runs as a normal function (not as a method), so `this` is the global object (or `undefined` in strict mode). So it logs the global’s `name` (often `''`) or throws in strict. To log `'Alice'`, use an arrow function or `.bind(this)` so the callback keeps the instance as `this`.

---

## Q9. Implement a simple `bind` polyfill (without full edge cases).

**Answer:**
```javascript
function myBind(fn, thisArg, ...boundArgs) {
  return function (...args) {
    return fn.apply(thisArg, [...boundArgs, ...args]);
  };
}
```

---

## Q10. (Tricky) What is logged?

**Question:**
```javascript
const length = 10;
function fn() {
  console.log(this.length);
}
const obj = {
  length: 5,
  method: function (fn) {
    fn();
    arguments[0]();
  }
};
obj.method(fn, 1);
```

**Answer:**  
First call `fn()`: default `this` (global in non-strict), so `this.length` is the global `length` (10).  
Second call `arguments[0]()`: `arguments` is the array-like object of `obj.method`’s arguments; calling `arguments[0]()` means `this` is `arguments`. `arguments.length` is 2 (fn and 1). So first log **10**, second log **2**.
