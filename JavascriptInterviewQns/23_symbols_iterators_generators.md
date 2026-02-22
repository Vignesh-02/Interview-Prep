# 23. Symbols, Iterators, and Generators (Senior)

## Q1. What is a Symbol and why can’t you rely on for...in or Object.keys to list them?

**Answer:**  
**Symbol** is a primitive type for unique property keys. Symbol keys are not enumerable in `for...in` or `Object.keys()`; they don’t show up in JSON. Use `Object.getOwnPropertySymbols(obj)` to get symbol keys. This allows “hidden” properties that won’t clash with string keys and won’t be accidentally serialized or iterated.

---

## Q2. What are well-known Symbols (e.g. Symbol.iterator, Symbol.toStringTag)? Give one use.

**Answer:**  
They are built-in symbols that define protocol behavior. Examples: **Symbol.iterator** (makes an object iterable with for-of and spread), **Symbol.toStringTag** (customizes `Object.prototype.toString`), **Symbol.asyncIterator** (async iteration). Use: implement `obj[Symbol.iterator]` so your object works with `for...of` and destructuring.

---

## Q3. Make a plain object iterable (for-of over its values) using Symbol.iterator.

**Answer:**
```javascript
const obj = { a: 1, b: 2, c: 3 };
obj[Symbol.iterator] = function* () {
  for (const key of Object.keys(this)) {
    yield this[key];
  }
};
for (const v of obj) console.log(v); // 1, 2, 3
// or: obj[Symbol.iterator] = function () {
//   const keys = Object.keys(this);
//   let i = 0;
//   return { next: () => ({ value: this[keys[i]], done: i++ >= keys.length }) };
// }
```

---

## Q4. What is the difference between an iterator and a generator?

**Answer:**  
An **iterator** is any object with a `next()` method returning `{ value, done }`. A **generator** is a function declared with `function*` that returns an iterator when called; `yield` produces values and pauses. Generators are a convenient way to implement iterators and lazy sequences; they maintain state between `next()` calls.

---

## Q5. Implement an infinite sequence (e.g. natural numbers) using a generator. How do you stop consuming it?

**Answer:**
```javascript
function* naturals() {
  let n = 0;
  while (true) yield n++;
}
const it = naturals();
console.log(it.next().value); // 0
console.log(it.next().value); // 1
// Stop by not calling next(), or use a limit:
function* take(gen, n) {
  for (let i = 0; i < n; i++) yield gen.next().value;
}
```

---

## Q6. What does yield* do? Use it to flatten a nested generator.

**Answer:**  
`yield*` delegates to another iterable or generator; it yields each value from that iterable. Use it to compose generators.

```javascript
function* flatten(nested) {
  for (const item of nested) {
    if (Symbol.iterator in Object(item) && typeof item !== 'string') {
      yield* flatten(item);
    } else {
      yield item;
    }
  }
}
```

---

## Q7. How do you pass a value into a generator (via next)? What does the generator receive?

**Answer:**  
`next(value)` passes `value` into the generator. That value becomes the result of the **current** `yield` expression (the one that paused the generator). So `const received = yield 1;` — the first `next(42)` sends 42 into the generator, and `received` will be 42 on the next resume. The first `next()` call’s argument is ignored (no current yield to receive it).

---

## Q8. Implement a simple async generator (async function*) that yields results of an array of Promises in order.

**Answer:**
```javascript
async function* resolveInOrder(promises) {
  for (const p of promises) {
    yield await p;
  }
}
// usage: for await (const value of resolveInOrder([p1, p2, p3])) { ... }
```

---

## Q9. What is Symbol.for and Symbol.keyFor? When would you use them?

**Answer:**  
**Symbol.for(key)** creates (or retrieves) a symbol from the global registry for that string key. Same key always returns the same symbol across the app. **Symbol.keyFor(sym)** returns the string key for a registry symbol, or undefined. Use when you need a shared symbol across realms (e.g. iframes, workers) or when you need to look up “the” symbol for a known name.

---

## Q10. (Tricky) What does this output and why?

**Question:**
```javascript
const sym = Symbol('id');
const obj = { [sym]: 1, id: 2 };
console.log(obj[sym]);
console.log(JSON.stringify(obj));
console.log(Object.keys(obj).length);
```

**Answer:**  
`obj[sym]` → **1**.  
`JSON.stringify(obj)` → **'{"id":2}'** (symbol keys are omitted).  
`Object.keys(obj).length` → **1** (only `'id'`; symbol keys are not enumerable for keys()). So the symbol key is present and accessible but invisible to keys/stringify.
