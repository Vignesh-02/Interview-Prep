# 7. Prototypal Inheritance

## Q1. What is the prototype chain in JavaScript?

**Answer:**  
Every object has an internal `[[Prototype]]` (exposed as `__proto__` in many environments). When you access a property, the engine looks on the object, then on its prototype, then that object’s prototype, and so on until `null`. This chain is the prototype chain. It’s how inheritance and shared behavior work in JS.

---

## Q2. What is the difference between `__proto__` and `prototype`?

**Answer:**  
- **`prototype`**: A property on **constructor functions**. When you call the constructor with `new`, the new object’s `[[Prototype]]` is set to that constructor’s `prototype`. So `Constructor.prototype` is the object that instances inherit from.
- **`__proto__`**: The object’s own link in the chain (its `[[Prototype]]`). So `obj.__proto__` is typically `Constructor.prototype` when `obj` was created with `new Constructor()`.

---

## Q3. How do you create an object that inherits from another without using `class`?

**Answer:**
```javascript
function Animal(name) {
  this.name = name;
}
Animal.prototype.speak = function () {
  return this.name + ' makes a sound';
};
function Dog(name) {
  Animal.call(this, name);
}
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;
Dog.prototype.speak = function () {
  return this.name + ' barks';
};
const d = new Dog('Rex');
console.log(d.speak()); // "Rex barks"
```

---

## Q4. What does `Object.create()` do?

**Answer:**  
`Object.create(proto)` creates a new object whose `[[Prototype]]` is `proto`. Optional second argument can add own properties. It’s a direct way to set up inheritance without a constructor: `const child = Object.create(parent)`.

---

## Q5. What is the output?

**Question:**
```javascript
function Foo() {}
Foo.prototype.bar = 1;
const a = new Foo();
const b = new Foo();
Foo.prototype.bar = 2;
console.log(a.bar);
console.log(b.bar);
```

**Answer:**  
Both **2**. `a` and `b` share `Foo.prototype`. Changing `Foo.prototype.bar` to 2 updates the single prototype object, so both instances see 2.

---

## Q6. How does `instanceof` work?

**Answer:**  
`obj instanceof Constructor` checks whether `Constructor.prototype` appears anywhere in `obj`’s prototype chain. It does not check whether the object was created by that constructor, only the prototype link.

---

## Q7. Implement a function that checks if an object has a property on itself (not the prototype).

**Answer:**
```javascript
function hasOwn(obj, prop) {
  return Object.prototype.hasOwnProperty.call(obj, prop);
}
// or use built-in: Object.hasOwn(obj, prop)
```

---

## Q8. What does this code output?

**Question:**
```javascript
const obj = {};
console.log(obj.toString);
obj.toString = function () {
  return 'custom';
};
console.log(obj.toString());
delete obj.toString;
console.log(obj.toString());
```

**Answer:**  
First log: **function** (inherited from `Object.prototype`).  
Second: **'custom'** (own property).  
After `delete`, own `toString` is removed, so third log calls the inherited `Object.prototype.toString()` → **'[object Object]'**.

---

## Q9. What is the end of the prototype chain?

**Answer:**  
`Object.prototype.__proto__` is **null**. So the chain always ends at `null`; that’s why property lookup can “give up” and return `undefined`.

---

## Q10. (Tricky) Predict the output.

**Question:**
```javascript
function A() {}
function B() {}
A.prototype = B.prototype = {};
const a = new A();
console.log(a instanceof A);
console.log(a instanceof B);
```

**Answer:**  
Both **true**. `a.__proto__` is `A.prototype`, which was set to the same object as `B.prototype`. So both `A.prototype` and `B.prototype` are in `a`’s prototype chain (they’re the same object). So `a instanceof A` and `a instanceof B` are both true.
