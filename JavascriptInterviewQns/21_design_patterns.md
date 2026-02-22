# 21. Design Patterns (Senior)

## Q1. Implement the Module pattern (revealing module) and explain how it provides encapsulation.

**Answer:**
```javascript
const counterModule = (function () {
  let count = 0;  // private
  function increment() {
    count++;
  }
  function getCount() {
    return count;
  }
  return {
    increment,
    getCount
  };
})();
```
The IIFE creates a closure so `count` and the inner logic stay private. Only the returned object is public. No direct access to `count` from outside.

---

## Q2. Implement a Singleton that works in JavaScript (with and without classes).

**Answer:**
```javascript
// Classic: IIFE + closure
const Singleton = (function () {
  let instance;
  function createInstance() {
    return { id: Math.random() };
  }
  return {
    getInstance() {
      if (!instance) instance = createInstance();
      return instance;
    }
  };
})();

// Class-based
class SingletonClass {
  static #instance;
  constructor() {
    if (SingletonClass.#instance) return SingletonClass.#instance;
    SingletonClass.#instance = this;
    return this;
  }
}
```

---

## Q3. Implement the Observer (Pub/Sub) pattern. When would you use it?

**Answer:**
```javascript
function createPubSub() {
  const subscribers = {};
  return {
    subscribe(event, fn) {
      (subscribers[event] = subscribers[event] || []).push(fn);
      return () => {
        subscribers[event] = subscribers[event].filter((f) => f !== fn);
      };
    },
    publish(event, data) {
      (subscribers[event] || []).forEach((fn) => fn(data));
    }
  };
}
```
Use for decoupling: UI updates, event-driven architecture, multiple listeners for one source (e.g. state changes).

---

## Q4. What is the Factory pattern? Implement a simple factory that returns different “product” types.

**Answer:**  
Factory is a function (or object) that creates and returns objects without exposing the constructor. Callers depend on the factory interface, not concrete types.

```javascript
function createUser(type) {
  const types = {
    admin: () => ({ role: 'admin', permissions: ['read', 'write', 'delete'] }),
    guest: () => ({ role: 'guest', permissions: ['read'] })
  };
  return (types[type] || types.guest)();
}
```

---

## Q5. Implement the Decorator pattern (or a simple decorator) that adds logging to any function.

**Answer:**
```javascript
function withLogging(fn) {
  return function (...args) {
    console.log(`Calling ${fn.name} with`, args);
    const result = fn.apply(this, args);
    console.log(`Result:`, result);
    return result;
  };
}
const add = withLogging((a, b) => a + b);
add(1, 2); // logs call and result
```

---

## Q6. What is the Strategy pattern? Give an example where it simplifies conditionals.

**Answer:**  
Strategy encapsulates algorithms (or behaviors) behind a common interface so they can be swapped. Replaces big if/switch with a map of strategies.

```javascript
const strategies = {
  add: (a, b) => a + b,
  subtract: (a, b) => a - b,
  multiply: (a, b) => a * b
};
function execute(op, a, b) {
  return strategies[op]?.(a, b);
}
```

---

## Q7. How would you implement a simple Middleware pattern (e.g. Express-style)?

**Answer:**
```javascript
function createMiddlewareRunner() {
  const middlewares = [];
  return {
    use(fn) {
      middlewares.push(fn);
    },
    run(context) {
      let i = 0;
      function next() {
        if (i >= middlewares.length) return Promise.resolve();
        const m = middlewares[i++];
        return Promise.resolve(m(context, next));
      }
      return next();
    }
  };
}
```

---

## Q8. What is the difference between the Module pattern and ES modules?

**Answer:**  
Module pattern uses IIFE + closure and a single global; dependencies are implicit or passed in. ES modules have explicit `import`/`export`, static structure, singleton per module, and are the language standard. ES modules don’t rely on closure hacks and support tree-shaking and static analysis.

---

## Q9. Implement a simple Memoization pattern (cache function results by arguments).

**Answer:**
```javascript
function memoize(fn) {
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };
}
```
For recursive functions, memoize the inner function or use a wrapper so recursive calls use the cache.

---

## Q10. When would you choose Composition over Inheritance in JavaScript? Give a short example.

**Answer:**  
Prefer composition when behavior is shared in a “has-a” or “uses-a” way, to avoid fragile base classes and deep chains. Example: instead of `AdminUser extends User`, do `user.withRole(adminRole)` or `const admin = { ...user, ...adminBehavior }`. Composition keeps objects flexible and easier to test and change.
