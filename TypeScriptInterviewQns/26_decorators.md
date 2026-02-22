# 26. Decorators — Senior

## Q1. (Easy) What is a decorator in TypeScript? What can it be applied to?

**Answer:**  
A **decorator** is a function that customizes a **class**, **method**, **accessor**, **property**, or **parameter**. It’s called with metadata (target, key, descriptor, etc.) and can modify or replace the target. Enable with **experimentalDecorators** (and **emitDecoratorMetadata** optionally) in **tsconfig**. Stage-2 decorators (TS 5+) may use a different API.

---

## Q2. (Easy) How do you enable decorators in TypeScript?

**Answer:**  
In **tsconfig.json**: **"experimentalDecorators": true**. For metadata (e.g. parameter types): **"emitDecoratorMetadata": true**. Decorators are still “experimental” and the TC39 spec has evolved; TS 5.0+ can support a different decorator shape. Check the TS version and docs.

---

## Q3. (Medium) What arguments does a **class** decorator receive?

**Answer:**  
A **class** decorator receives one argument: the **constructor** (the class function). So **function classDec(Ctor: Function) { }**. It can return a new constructor to replace the class, or return nothing. **function classDec<T extends new (...args: any[]) => any>(Ctor: T) { return class extends Ctor { } }**.

---

## Q4. (Medium) What arguments does a **method** decorator receive?

**Answer:**  
**target** (prototype or constructor for static), **propertyKey** (string | symbol), **descriptor** (PropertyDescriptor). So **function methodDec(target: any, key: string, descriptor: PropertyDescriptor) { }**. You can return a new **PropertyDescriptor** to replace the method. **target** is the prototype for instance methods, the constructor for static methods.

---

## Q5. (Medium) What is a **property** decorator? What can it not do that a method decorator can?

**Answer:**  
A **property** decorator receives **target** (prototype or constructor), **propertyKey**. There is **no descriptor** (property decorators run before the property is created). So you can’t replace the property descriptor directly; you might use it to register or track metadata, or to define a getter/setter on the target that replace the property (by overwriting on the prototype).

---

## Q6. (Medium) What is a **parameter** decorator? What are its arguments?

**Answer:**  
**parameter** decorator receives **target** (prototype or constructor), **propertyKey** (method name), **parameterIndex** (number). Used to mark or validate parameters (e.g. for DI or validation). Often used with **reflect-metadata** and **emitDecoratorMetadata** to get parameter types. Cannot change the parameter; only observe or attach metadata.

---

## Q7. (Tough) How do you write a decorator that runs only in development (e.g. logs method calls)?

**Answer:**  
Check **process.env.NODE_ENV** (or a build-time flag) inside the decorator: **function log(target: any, key: string, descriptor: PropertyDescriptor) { if (process.env.NODE_ENV !== "production") { const fn = descriptor.value; descriptor.value = function (...args: any[]) { console.log(key, args); return fn.apply(this, args); }; } return descriptor; }**. Or return the original descriptor in production.

---

## Q8. (Tough) What is **emitDecoratorMetadata**? What extra information is emitted?

**Answer:**  
**emitDecoratorMetadata: true** makes TS emit **metadata** (via **reflect-metadata**) for decorated targets: parameter types, return type, and property types. So at runtime you can read **Reflect.getMetadata("design:paramtypes", target, key)** to get parameter types. Requires **reflect-metadata** package and polyfill. Used by DI frameworks (e.g. Angular, Inversify).

---

## Q9. (Tough) What is the order of execution when multiple decorators are applied (e.g. **@a @b method()**)?

**Answer:**  
**Decorators** are applied **bottom-up** (reverse order of appearance). So **@a @b** means **b** is applied first, then **a**. **Evaluation** (calling the decorator factory) is **top-down**. So for **@a() @b()**, **a()** is evaluated first, then **b()**; but the resulting decorators are applied **b** then **a**. Think: “evaluate top-down, apply bottom-up.”

---

## Q10. (Tough) How do you type a class decorator that returns a new constructor (possibly a subclass)?

**Answer:**  
**function classDec<T extends new (...args: any[]) => any>(Ctor: T): T { return class extends Ctor { } as T }** — or return a constructor that is assignable to **T**. The generic **T** is the constructor type; **InstanceType<T>** is the instance type. So **T** preserves the original class type for type checking; the returned class should be compatible (same or extended constructor signature).
