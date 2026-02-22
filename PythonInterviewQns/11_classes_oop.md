# 11. Classes and OOP (inheritance, encapsulation)

## Q1. (Easy) How do you define a class and create an instance?

**Answer:**  
**`class MyClass:`** then methods with `self` as first parameter. Create: **`obj = MyClass()`**. The constructor is **`__init__(self, ...)`** — not required; if present it’s called when the object is created.

---

## Q2. (Easy) What is `self`? Why is it the first parameter of instance methods?

**Answer:**  
**self** is the instance on which the method is called. When you call `obj.method()`, Python passes `obj` as the first argument. By convention that parameter is named `self`. It gives the method access to the instance’s attributes and other methods.

---

## Q3. (Easy) What is the difference between a class attribute and an instance attribute?

**Answer:**  
**Class attribute** is defined on the class; shared by all instances; access via `Class.attr` or `self.attr` (if not shadowed). **Instance attribute** is set on the instance (e.g. in `__init__`); each instance has its own. If you assign to `self.attr` in a method, you create/update an instance attribute (may shadow a class attribute for that instance).

---

## Q4. (Medium) How does inheritance work? What is `super()`?

**Answer:**  
Define with **`class Child(Parent):`**. Child has access to Parent’s attributes and methods. **`super()`** returns a proxy to the next class in the MRO (method resolution order); use **`super().method()`** to call the parent’s implementation. In multiple inheritance, super follows the MRO.

---

## Q5. (Medium) What is “name mangling” (e.g. `__attr`)? When is it used?

**Answer:**  
A name starting with **double underscore** (and not ending with underscore) is **mangled** to `_ClassName__attr`. It’s a hint for “private” to avoid accidental override in subclasses — not true privacy (can still access as `_Class__attr`). Single leading underscore is convention for “internal use.”

---

## Q6. (Medium) What is the difference between `__init__` and `__new__`?

**Answer:**  
**`__new__(cls, ...)`** is the actual constructor; it creates and returns the instance (usually `object.__new__(cls)`). **`__init__(self, ...)`** is the initializer; it receives the instance and sets up state. __new__ runs first; __init__ runs on the object returned by __new__. Most classes only override __init__.

---

## Q7. (Medium) What does `isinstance(x, C)` check? What about `issubclass(C, B)`?

**Answer:**  
**isinstance(x, C)** — True if `x` is an instance of `C` or a subclass of `C`. **issubclass(C, B)** — True if `C` is a subclass of (or equal to) `B`. Both respect the inheritance hierarchy.

---

## Q8. (Tough) What is the Method Resolution Order (MRO)? How do you see it?

**Answer:**  
**MRO** is the order in which base classes are searched for an attribute (used for multiple inheritance). It follows the **C3 linearization** algorithm. See it: **`ClassName.__mro__`** or **`ClassName.mro()`**. Ensures each class appears once and a subclass comes before its base.

---

## Q9. (Tough) What is the output and why?

```python
class A:
    def f(self):
        return "A"
class B(A):
    def f(self):
        return "B"
class C(A):
    def f(self):
        return "C"
class D(B, C):
    pass
print(D().f())
```

**Answer:**  
**"B".** MRO for D is typically D → B → C → A → object. So the first `f` found is B’s. So `D().f()` returns `"B"`.

---

## Q10. (Tough) How do you make a class “abstract” so it can’t be instantiated directly? How do you force subclasses to implement a method?

**Answer:**  
Use **abc.ABC** and **@abstractmethod**: `from abc import ABC, abstractmethod`. `class Base(ABC): @abstractmethod def must_implement(self): pass`. Instantiating Base (or a subclass that doesn’t implement all abstract methods) raises **TypeError**. ABC stands for Abstract Base Class.
