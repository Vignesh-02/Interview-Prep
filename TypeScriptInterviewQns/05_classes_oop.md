# 5. Classes and OOP Basics

## Q1. (Easy) How do you add types to class properties and the constructor?

**Answer:**  
**`class C { name: string; id: number; constructor(name: string, id: number) { this.name = name; this.id = id } }`**. Properties can have **readonly**. Parameter properties: **constructor(public name: string, private id: number)** creates and assigns **this.name** and **this.id** and applies visibility.

---

## Q2. (Easy) What are the access modifiers? What does each do?

**Answer:**  
**public** — default; visible everywhere. **protected** — visible in class and subclasses. **private** — visible only in the class (compile-time only in classic TS; **#** in JS is true private). **readonly** — cannot reassign after init. Modifiers apply to properties and methods.

---

## Q3. (Easy) How do you implement an interface in a class?

**Answer:**  
**`class User implements IUser { ... }`**. The class must have all members required by **IUser** (and their types must match). You can **implements** multiple interfaces: **class C implements A, B { }**.

---

## Q4. (Medium) What is the difference between **interface** and **abstract class** for typing?

**Answer:**  
**interface** — only shape; no implementation, no constructor; can be implemented by many unrelated classes. **abstract class** — can have implementation, constructor, and **abstract** members; single inheritance; you extend it. Use interface for contracts; use abstract class when you want shared code and single inheritance.

---

## Q5. (Medium) How do you type a class constructor (e.g. “a function that returns an instance of C”)?

**Answer:**  
**`type Ctor = new (...args: any[]) => C`** — constructor type with **new**. Or **`typeof MyClass`** for the class type (includes static members and constructor). **`InstanceType<typeof MyClass>`** is the instance type.

---

## Q6. (Medium) What is **private** vs **#** (private field)? Which is enforced at runtime?

**Answer:**  
**private** (TS keyword) is only enforced by TypeScript; it compiles to a normal property. **#field** (ES private field) is real JavaScript privacy; not accessible outside the class at runtime. Prefer **#** for true encapsulation when target supports it.

---

## Q7. (Medium) Can a class extend a type alias? Can it extend an interface?

**Answer:**  
A class can **extend** only a type that has a **constructor** (a class or constructor signature). So **extends** works with **class** and with object types that TypeScript treats as class-like. An **interface** has no runtime; you **implement** it. So **class A extends B** — B is usually another class; for interface you use **implements**.

---

## Q8. (Tough) What is the type of **this** in a class method? How do you type a method that returns the class instance (for chaining)?

**Answer:**  
**this** in a method is the instance type (the class type). For chaining, return **this**: **method(): this { ... return this }**. So the return type is the actual subclass when extended, not only the base class. TypeScript uses **this** as a type to represent the current instance (polymorphic **this**).

---

## Q9. (Tough) How do you type a static method and a static property? What is the type of the class (constructor) itself?

**Answer:**  
**static prop: number; static method(): void { }**. The **class** value has type that includes constructor **new (...args) => Instance** and all static members. So **typeof MyClass** is the type of the class constructor object; **MyClass** in type position often refers to the instance type in older TS; in modern TS the class name in value position is the constructor, in type position it’s the instance type.

---

## Q10. (Tough) What happens when a class implements an interface with optional properties? Must the class declare them?

**Answer:**  
The class must satisfy the interface. **Optional** properties in the interface can be omitted in the class if the class doesn’t need to expose them. If the interface has **opt?: number**, the class can have **opt?: number** or omit it (then the class has an implicit **undefined** for that property from the interface’s perspective). Implementation is compatible if assignable to the interface.
