# 25. Descriptors and Properties — Senior

## Q1. (Easy) What is a descriptor? What protocol does it implement?

**Answer:**  
A **descriptor** is an object that defines **__get__**, and optionally **__set__** or **__delete__**, and is stored as a **class** attribute (not instance). When you access an attribute that is a descriptor, Python calls its **__get__(self, instance, owner)** (or __set__/__delete__). So it customizes attribute access for that name on instances of **owner**.

---

## Q2. (Easy) What is the difference between a data and non-data descriptor?

**Answer:**  
A **data descriptor** defines **__set__** (or **__delete__**). A **non-data descriptor** has only **__get__**. **Data descriptors** take precedence over the instance **__dict__** (so they’re used even if the instance has an attribute of the same name). **Non-data descriptors** are overridden by instance attributes. So **property** is a data descriptor; methods (functions) are non-data descriptors.

---

## Q3. (Medium) How do you define a property? What does property() return?

**Answer:**  
**property(fget=None, fset=None, fdel=None, doc=None)** — **@property** is used as a decorator: **def x(self): return self._x** then **x = property(x)**. You can add **@x.setter** and **@x.deleter**. **property()** returns a **descriptor** that calls the getter/setter/deleter when the attribute is accessed or set. So **obj.x** calls the getter; **obj.x = v** calls the setter if defined.

---

## Q4. (Medium) What arguments does __get__ receive? What does it return?

**Answer:**  
**__get__(self, instance, owner)** — **self** is the descriptor, **instance** is the instance (None when accessed on the class), **owner** is the class. Return the value to use for the attribute. When **instance is None**, you typically return **self** (so the descriptor is visible on the class) or a class-level value.

---

## Q5. (Medium) Implement a simple read-only property using a descriptor (no property()).

**Answer:**
```python
class ReadOnly:
    def __init__(self, value):
        self.value = value
    def __get__(self, instance, owner):
        return self.value
    def __set__(self, instance, value):
        raise AttributeError("read-only")
```
Store the value on the descriptor (shared by all instances) or in instance __dict__ under a private name if you need per-instance and the descriptor is used to expose it read-only.

---

## Q6. (Medium) What is __set_name__? How do descriptors use it?

**Answer:**  
**__set_name__(self, owner, name)** is called when the **owner** class is created, with the **name** of the attribute the descriptor is assigned to. So the descriptor learns “I am the attribute named 'x' on class C.” Used by **dataclasses**, **ORM** columns, etc., to know the attribute name without the user repeating it.

---

## Q7. (Tough) Why do methods work as descriptors? What does function.__get__ do?

**Answer:**  
**Functions** are **non-data descriptors**. **function.__get__(instance, owner)** returns a **bound method** (or unbound if instance is None): a callable that, when called, passes **instance** as the first argument (self). So **obj.method** is **type(obj).method.__get__(obj, type(obj))** → bound method. That’s how **self** gets passed automatically.

---

## Q8. (Tough) Implement a descriptor that validates that the value is positive when set.

**Answer:**
```python
class Positive:
    def __set_name__(self, owner, name):
        self.storage_name = '_' + name
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.storage_name, 0)
    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("must be positive")
        setattr(instance, self.storage_name, value)
```
Store the value on the instance under a private name to avoid sharing between instances.

---

## Q9. (Tough) What is the order of attribute lookup (e.g. data descriptor vs instance __dict__)?

**Answer:**  
Lookup order (simplified): (1) **data descriptor** on the class (and base classes, MRO), (2) **instance __dict__**, (3) **non-data descriptor** or normal class attribute (MRO). So a data descriptor wins over the instance dict; a non-data descriptor loses to the instance dict. **__getattribute__** implements this; **__getattr__** is only called if the attribute wasn’t found.

---

## Q10. (Tough) How do slots interact with descriptors? Can a class have both __slots__ and a descriptor for the same name?

**Answer:**  
**__slots__** reserves space for names; the implementation uses **descriptors** (at the C level) for each slot. So slots are implemented via descriptors. You can have a **custom descriptor** for a name that’s also in **__slots__** only if you don’t use that name in __slots__ (slots and descriptor would conflict for the same name). Typically you use either a slot or a descriptor for a given attribute, not both for the same name.
