# 12. Generics (Basics)

## Q1. (Easy) What is a generic? Why use it?

**Answer:**  
A **generic** is a type (or function/class) parameterized by one or more **type parameters** (e.g. **T**). It lets you write one implementation that works for many types while keeping type safety. Example: **function identity<T>(x: T): T { return x }** — input and output types stay linked.

---

## Q2. (Easy) How do you define a generic function? How do you call it with an explicit type argument?

**Answer:**  
**function id<T>(x: T): T { return x }**. Call: **id<string>("hi")** or **id("hi")** (inferred). Type arguments go in **<>** before the **()**. Multiple: **function pair<T, U>(a: T, b: U): [T, U] { return [a, b] }**.

---

## Q3. (Easy) What is the inferred type of **identity(5)** and **identity("a")**?

**Answer:**  
**identity(5)** → **T** is **number**, return **number**. **identity("a")** → **T** is **string**, return **string**. TypeScript infers **T** from the argument. So you get precise types without writing **identity<number>(5)**.

---

## Q4. (Medium) How do you define a generic interface or type?

**Answer:**  
**interface Box<T> { value: T }** or **type Box<T> = { value: T }**. Use: **const b: Box<number> = { value: 1 }**. Generic type alias: **type Pair<T, U> = [T, U]**.

---

## Q5. (Medium) How do you define a generic class?

**Answer:**  
**class Container<T> { constructor(public value: T) {} }**. Instance type is **Container<T>**; static members cannot use **T** (T is per instance). **new Container<string>("hi")** — **value** is **string**.

---

## Q6. (Medium) What is a generic constraint? Give a one-line example.

**Answer:**  
A constraint limits what **T** can be: **T extends SomeType**. Example: **function len<T extends { length: number }>(x: T): number { return x.length }** — **T** must have **length**. So **len("hi")** and **len([1,2])** work; **len(42)** errors.

---

## Q7. (Medium) Can a generic have a default type parameter? Example.

**Answer:**  
Yes (TS 2.3+): **type Box<T = string> = { value: T }**. Then **Box** without argument is **Box<string>**. **function f<T = number>(x: T)** — **f()** without type arg uses **number** for **T** if inference fails. Used in utility types (e.g. **Partial<T>**).

---

## Q8. (Tough) What is the difference between **Array<T>** and **T[]** in a generic context? Are they the same?

**Answer:**  
They are the same type. In generics both work: **function first<T>(arr: T[]): T** and **function first<T>(arr: Array<T>): T** are equivalent. **T[]** is shorthand for **Array<T>**.

---

## Q9. (Tough) Write a generic function that takes an array and returns the first element. What is the return type when the array is empty?

**Answer:**  
**function first<T>(arr: T[]): T | undefined { return arr[0] }**. Return **T | undefined** because **arr[0]** might be undefined for empty array. If you want **T** only when non-empty, you need a tuple or overload: **function first<T>(arr: [T, ...T[]]): T**.

---

## Q10. (Tough) How do you type a generic “factory” function that takes a class (constructor) and returns an instance?

**Answer:**  
**function create<T>(Ctor: new () => T): T { return new Ctor() }**. So **Ctor** is a constructor that takes no args and returns **T**. For constructor with args: **new (...args: any[]) => T** or a generic args tuple. Use **InstanceType<typeof Ctor>** as an alternative to **T** when you only have the constructor type.
