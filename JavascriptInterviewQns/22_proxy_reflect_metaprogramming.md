# 22. Proxy and Reflect (Senior)

## Q1. What is the Proxy object and what is it used for?

**Answer:**  
**Proxy** wraps another object and intercepts operations (property access, assignment, enumeration, function calls, etc.). You define handlers (e.g. `get`, `set`, `has`, `apply`) to customize or validate behavior. Used for: validation, logging, default values, virtual properties, revocable references, and building reactive systems.

---

## Q2. Implement a Proxy that logs every property access and assignment.

**Answer:**
```javascript
const target = { a: 1 };
const logged = new Proxy(target, {
  get(obj, prop) {
    console.log('get', prop);
    return Reflect.get(obj, prop);
  },
  set(obj, prop, value) {
    console.log('set', prop, value);
    return Reflect.set(obj, prop, value);
  }
});
logged.a;      // logs 'get a'
logged.b = 2; // logs 'set b 2'
```

---

## Q3. What is Reflect and why use it with Proxy?

**Answer:**  
**Reflect** is a built-in object whose methods mirror Proxy traps (get, set, has, deleteProperty, etc.). They provide the default behavior for those operations. In a Proxy handler, use `Reflect.get(target, prop)` instead of `target[prop]` so that getters, inheritance, and non-writable properties are handled correctly. Reflect methods also return success booleans where useful (e.g. `Reflect.set`).

---

## Q4. Create a Proxy that returns a default value for missing properties (e.g. 0 for numbers).

**Answer:**
```javascript
function withDefaults(target, defaultValue = 0) {
  return new Proxy(target, {
    get(obj, prop) {
      if (prop in obj) return obj[prop];
      return defaultValue;
    }
  });
}
const obj = withDefaults({ a: 1 });
console.log(obj.a); // 1
console.log(obj.b); // 0
```

---

## Q5. What trap would you use to hide the existence of certain properties from `in` and hasOwnProperty-style checks?

**Answer:**  
Use the **`has`** trap. `'prop' in proxy` and `Reflect.has(proxy, 'prop')` invoke the handler. Return false for “hidden” keys so they appear as if they don’t exist. Note: `Object.hasOwn(proxy, 'prop')` may still go to the target depending on implementation; for full control you need to understand which operations go through the proxy.

---

## Q6. Implement a read-only Proxy (no new properties, no modifications to existing).

**Answer:**
```javascript
function readOnly(obj) {
  return new Proxy(obj, {
    set() {
      return false; // or throw
    },
    defineProperty() {
      return false;
    },
    deleteProperty() {
      return false;
    }
  });
}
```

---

## Q7. What is a revocable Proxy and when is it useful?

**Answer:**  
`Proxy.revocable(target, handler)` returns `{ proxy, revoke }`. After you call `revoke()`, any operation on the proxy throws. Useful for handing temporary access to an object (e.g. to a third-party or a worker) and then cutting off access without keeping the original reference.

---

## Q8. Can you proxy a function? What trap handles invocation?

**Answer:**  
Yes. Proxying a function uses the **`apply`** trap: `apply(target, thisArg, argumentsList)`. It’s invoked when the proxy is called as a function. Use it for logging, validation, or wrapping (e.g. timing, error handling).

```javascript
const fn = new Proxy(function (a, b) { return a + b; }, {
  apply(target, thisArg, args) {
    console.log('called with', args);
    return Reflect.apply(target, thisArg, args);
  }
});
```

---

## Q9. Why might a Proxy cause “proxy not extensible” or unexpected behavior with Object.* methods?

**Answer:**  
Some `Object.*` operations (e.g. `Object.keys`, `Object.getOwnPropertyNames`) may query the target or the proxy’s invariants. If your trap returns something inconsistent with the target’s state (e.g. claim a property doesn’t exist when it does, or make a non-configurable property disappear), the engine can throw to preserve invariants. Traps should be consistent with the target and with each other.

---

## Q10. Implement a simple “reactive” object: when a property changes, run a callback (e.g. notify subscribers).

**Answer:**
```javascript
function reactive(initial, onChange) {
  return new Proxy(initial, {
    set(obj, prop, value) {
      const old = obj[prop];
      const result = Reflect.set(obj, prop, value);
      if (result && old !== value) onChange(prop, value, old);
      return result;
    }
  });
}
const state = reactive({ count: 0 }, (key, val, old) => {
  console.log(`${key} changed from ${old} to ${val}`);
});
state.count = 1; // logs change
```
