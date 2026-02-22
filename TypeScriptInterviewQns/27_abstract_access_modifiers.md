# 27. Abstract Classes and Access Modifiers — Senior

## Q1. (Easy) What is an **abstract class**? Can you instantiate it?

**Answer:**  
An **abstract class** is declared with **abstract class**. It can have **abstract** members (no implementation). You **cannot** instantiate it with **new**; it’s a base for subclasses. Subclasses must implement all abstract members (unless they are also abstract). Used to define a contract and shared implementation.

---

## Q2. (Easy) What is an **abstract** method? How does it differ from an interface method?

**Answer:**  
An **abstract** method has no body: **abstract run(): void**. The subclass must provide the implementation. An **interface** only declares the shape; an **abstract class** can mix abstract and concrete members and have state (fields, constructor). So abstract class = contract + optional shared code + single inheritance.

---

## Q3. (Medium) What are **public**, **protected**, and **private**? What is the difference at compile time vs runtime?

**Answer:**  
**public** — visible everywhere (default). **protected** — visible in the class and subclasses. **private** — visible only in the class. In classic TS (no **#**), these are **compile-time only**; the emitted JS has no notion of private/protected (property names are unchanged). **#field** (ES private) is **runtime** private; **private** in TS is not.

---

## Q4. (Medium) Can an **abstract** class have a constructor? Can it be **protected**?

**Answer:**  
Yes. An abstract class can have a **constructor**; often it’s **protected** so only subclasses can call it (not **new AbstractClass()** from outside). **protected constructor() { }** — then **new AbstractClass()** errors; **class Child extends AbstractClass { }** and **new Child()** can call **super()**.

---

## Q5. (Medium) How does **protected** differ from **private** for a subclass?

**Answer:**  
**protected** members are visible in **subclasses**; **private** members are not. So a subclass can use **this.protectedMember** but not **this.privateMember**. Both are compile-time only in classic TS. **#private** (ES) is not visible in subclasses either (true encapsulation).

---

## Q6. (Medium) What is **readonly**? Can you assign to a readonly property in the constructor?

**Answer:**  
**readonly** means the property cannot be reassigned after initialization. You **can** assign in the constructor (and only there, or at declaration). So **readonly id: number** in the constructor body is allowed. It does not make nested objects immutable.

---

## Q7. (Tough) Can an **interface** extend an **abstract class**? Can an **abstract class** implement an **interface**?

**Answer:**  
An **interface** cannot **extend** a class in the “extends” sense (interfaces extend interfaces or object types). An **abstract class** can **implement** an **interface**: **abstract class Base implements I { abstract m(): void }**. So the abstract class must satisfy the interface (with abstract or concrete members). For “interface extends class,” TS allows **interface I extends Class** to inherit the class’s instance type (the contract); it’s a special case.

---

## Q8. (Tough) What is **private** vs **#** (hash) for a field? Which is enforced in emitted JavaScript?

**Answer:**  
**private name: string** — TypeScript only; emitted JS is a normal property. **#name: string** — ES private field; emitted JS has the **#** and is truly private at runtime. **#** is not accessible in subclasses; **private** is only enforced by the type checker. Prefer **#** when you need runtime privacy and target supports it.

---

## Q9. (Tough) How do you expose a **protected** member to the outside in a subclass? (e.g. for API design)

**Answer:**  
In the subclass, add a **public** (or **protected**) method that returns or calls the protected member: **class Child extends Base { public getProtected() { return this.protectedMember } }**. Or redeclare as **public** in the subclass (in TS you can override and change visibility to **public** for a member that was **protected** in the base). So “expose” by wrapping or by making the override public.

---

## Q10. (Tough) When would you choose an **abstract class** over an **interface** + **interface** + implementation class?

**Answer:**  
Use **abstract class** when you want **shared implementation** (methods, state, constructor logic) and a **single inheritance** hierarchy. Use **interface** when you only need a contract (no implementation), multiple implementation freedom, or multiple “implements” (no multiple inheritance of implementation). So: abstract class = “base with some code”; interface = “shape only” or “multiple contracts.”
