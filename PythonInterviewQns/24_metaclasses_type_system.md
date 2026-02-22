# 24. Metaclasses and the Type System — Senior

## Q1. (Easy) What is a metaclass? What is the default metaclass of a class?

**Answer:**  
A **metaclass** is the class of a class; it defines how a class is created. When you define **class C:**, the **metaclass** (default **type**) is used to construct **C**. So **type** is the default metaclass; **type(name, bases, dict)** creates a new class. Custom metaclasses subclass **type**.

---

## Q2. (Easy) What are the three arguments to type() when used to create a class dynamically?

**Answer:**  
**type(name, bases, dict)** — **name** is the class name (string), **bases** is a tuple of base classes, **dict** is the namespace (attributes and methods) for the class body. So **C = type('C', (), {'x': 1})** creates a class C with attribute x=1. It’s equivalent to **class C: x = 1** (simplified).

---

## Q3. (Medium) How do you assign a custom metaclass to a class? Python 3 syntax.

**Answer:**  
**class C(metaclass=MyMeta):** or **class C(Base, metaclass=MyMeta):**. **MyMeta** must be a callable that can create a class (usually a subclass of **type**). It’s invoked as **MyMeta(name, bases, dict)** (or with extra keyword arguments if supported). Python 3 uses **metaclass=** in the class definition; Python 2 used **__metaclass__** in the body.

---

## Q4. (Medium) In what order are metaclass and base classes used when creating a class?

**Answer:**  
The **metaclass** is resolved first (explicit **metaclass=**, or inherited from a base, or **type**). Then the **bases** are collected. The metaclass’s **__new__** and **__init__** are called with (name, bases, namespace) to create and initialize the class object. So: resolve metaclass → prepare namespace (class body) → call metaclass to build the class.

---

## Q5. (Medium) What is ABC (Abstract Base Class)? How does it use metaclasses?

**Answer:**  
**abc.ABC** is a base class that uses **abc.ABCMeta** as its metaclass. **ABCMeta** tracks **@abstractmethod** and prevents instantiation of a class that hasn’t overridden all abstract methods. So ABCs enforce an interface without multiple inheritance from “type”; the metaclass does the check at class creation and at instantiation time.

---

## Q6. (Tough) What does a metaclass’s __new__ receive? What might you do there?

**Answer:**  
**metaclass.__new__(mcs, name, bases, namespace, **kwargs)** — **mcs** is the metaclass, **name** the class name, **bases** the base classes, **namespace** the dict from the class body. You can **inspect or modify** the namespace (add/remove/change attributes), change **bases**, or return a different class. Then **__init__(cls, name, bases, namespace)** is called to initialize the class object. __new__ creates it; __init__ customizes it.

---

## Q7. (Tough) When would you use a metaclass vs a class decorator vs a normal base class?

**Answer:**  
**Metaclass** — when you need to control **how the class itself is created** (e.g. register all subclasses, enforce naming, change the namespace before the class exists). **Class decorator** — when you can do the same by **wrapping or modifying the class object** after it’s created (e.g. add methods, wrap methods). **Base class** — when subclasses just need to **inherit behavior** and data. Prefer the simpler option: base class → decorator → metaclass.

---

## Q8. (Tough) What is the “type of type”? How does type create a class?

**Answer:**  
**type(type)** is **type**. So **type** is its own metaclass. When you do **class C:**, Python effectively calls **type('C', (bases,), namespace)**. **type**’s **__new__** allocates the class object and **__init__** initializes it. So **type** is both the built-in type of instances and the default class factory.

---

## Q9. (Tough) Implement a metaclass that adds a simple “registry” of all its subclasses (list or set on the base class).

**Answer:**
```python
class RegistryMeta(type):
    def __init__(cls, name, bases, ns):
        super().__init__(name, bases, ns)
        if not hasattr(cls, '_registry'):
            cls._registry = []
        else:
            cls._registry.append(cls)

class Base(metaclass=RegistryMeta):
    _registry = []
# Subclasses of Base get appended to Base._registry
```

---

## Q10. (Tough) What are __init_subclass__ and __set_name__? How do they reduce the need for metaclasses?

**Answer:**  
**__init_subclass__(cls)** is called on a base class when a **subclass** is created; you can customize subclass creation without a metaclass. **__set_name__(self, owner, name)** is called on a **descriptor** when the owner class is created, with the attribute name — used by descriptors (e.g. dataclasses fields) to know their name. Both were added to cover common metaclass use cases with simpler hooks.
