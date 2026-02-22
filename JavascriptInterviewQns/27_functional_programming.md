# 27. Functional Programming in JavaScript (Senior)

## Q1. What does “pure function” mean? Why does it matter for testing and reasoning?

**Answer:**  
A **pure function** has no side effects (doesn’t mutate state, I/O, or external state) and returns the same output for the same inputs (referential transparency). Benefits: easy to test (no mocks for globals), predictable, cacheable (memoization), and safe to run in parallel or reorder. It matters for maintainability and for frameworks that rely on referential equality (e.g. React).

---

## Q2. Implement compose(f, g)(x) that returns f(g(x)). Then implement pipe.

**Answer:**
```javascript
const compose = (...fns) => (x) =>
  fns.reduceRight((acc, fn) => fn(acc), x);

const pipe = (...fns) => (x) =>
  fns.reduce((acc, fn) => fn(acc), x);

// compose(f, g)(x) === f(g(x))
// pipe(g, f)(x) === f(g(x))
```

---

## Q3. What is immutability in the context of JavaScript? How do you update “nested” state immutably?

**Answer:**  
**Immutability**: Never mutate existing data; create new copies for changes. In JS, use spread and nested spread (or a library like Immer) to create new objects/arrays. Example: `const next = { ...state, nested: { ...state.nested, field: value } };`. For deep trees, use structural sharing (e.g. Immutable.js) or Immer (produce) to avoid manual deep spreads.

---

## Q4. What is a functor in practical JS terms? Give an example (e.g. Array as a functor).

**Answer:**  
A **functor** is a type with a map that preserves structure and identity (e.g. `arr.map(id) === arr`). In JS, **Array** is a functor: `map` returns a new array and respects composition: `arr.map(f).map(g) === arr.map(x => g(f(x)))`. So “functor” here means “something you can map over” in a consistent way. Promise is another example (then/map over the future value).

---

## Q5. Implement a Maybe (Option) type: Nothing or Just(value), with map and a way to get the value safely.

**Answer:**
```javascript
const Nothing = { map: () => Nothing, getOrElse: (d) => d, isNothing: true };
const Just = (value) => ({
  map: (fn) => Just(fn(value)),
  getOrElse: () => value,
  isNothing: false
});
const Maybe = { of: Just, nothing: () => Nothing };
// usage: Maybe.of(5).map(x => x + 1).getOrElse(0)  => 6
//        Maybe.nothing().map(x => x + 1).getOrElse(0)  => 0
```

---

## Q6. What is currying? Implement a curry(fn) that allows calling f(a)(b)(c) or f(a, b, c).

**Answer:**  
**Currying** is turning a function of N arguments into a chain of N functions of one argument. Each returns the next function until all args are supplied, then returns the result.

```javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return (...next) => curried.apply(this, [...args, ...next]);
  };
}
```

---

## Q7. What is the difference between partial application and currying?

**Answer:**  
**Currying**: One function becomes many single-argument functions; you fix arguments one at a time in order. **Partial application**: You fix some arguments (in any positions) and get a function that takes the rest. So `curry(f)(a)(b)` vs `partial(f, a)(b)`. Partial application is more flexible (e.g. bind(f, null, 1) fixes first arg); currying is uniform (always one arg per call).

---

## Q8. Implement reduce as the fundamental list operation (so map and filter can be expressed with reduce).

**Answer:**
```javascript
const reduce = (arr, fn, init) => {
  let acc = init;
  for (let i = 0; i < arr.length; i++) acc = fn(acc, arr[i], i, arr);
  return acc;
};
const map = (arr, f) => reduce(arr, (acc, x) => [...acc, f(x)], []);
const filter = (arr, p) => reduce(arr, (acc, x) => (p(x) ? [...acc, x] : acc), []);
```

---

## Q9. What are referential transparency and side effects? How do they relate to “predictable” code?

**Answer:**  
**Referential transparency**: An expression can be replaced by its value without changing behavior; no hidden dependencies. **Side effects**: Anything that reads or changes state outside the function (I/O, mutation, global state, randomness). Pure functions have no side effects and are referentially transparent. Predictable code avoids hidden state and timing so the same inputs always give the same outputs and reasoning is local.

---

## Q10. When would you choose a functional style (immutability, pure functions, composition) over an imperative one in a large codebase?

**Answer:**  
Choose functional style when: (1) correctness and reasoning matter (finance, shared state). (2) You need easy testing and refactoring. (3) Concurrency or parallelization is involved. (4) The team agrees on the style and tooling (e.g. Redux, React with hooks). Prefer imperative when: (1) Performance is critical and mutation is localized (e.g. hot loops). (2) The domain is inherently stateful (games, streams). (3) The team or ecosystem is heavily OO. Often a hybrid works: pure core, imperative at boundaries (I/O, DOM).
