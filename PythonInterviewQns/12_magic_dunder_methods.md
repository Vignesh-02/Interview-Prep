# 12. Magic (Dunder) Methods

## Q1. (Easy) What are “dunder” methods? Name three common ones.

**Answer:**  
**Dunder** = double underscore; special methods like **`__init__`**, **`__str__`**, **`__len__`**. They hook into built-in behavior (construction, string conversion, len(), etc.). Don’t invent new ones; use the documented protocol names.

---

## Q2. (Easy) What is the difference between `__str__` and `__repr__`?

**Answer:**  
**`__str__`** — for “user-friendly” string (e.g. `print(obj)`). **`__repr__`** — for “developer” representation; ideally `eval(repr(obj)) == obj`. If only one is defined, __str__ may fall back to __repr__. repr is used in the interactive prompt and by debuggers.

---

## Q3. (Easy) Which method is called when you use `len(obj)`? What should it return?

**Answer:**  
**`__len__(self)`**. It should return a non-negative integer (the “length”). If you don’t define it, `len(obj)` raises TypeError. Used by sequences and collections.

---

## Q4. (Medium) What methods implement “container” protocol (in, indexing)? What about iteration?

**Answer:**  
**`__contains__(self, item)`** — for `item in self`. **`__getitem__(self, key)`** — for `self[key]`. **`__setitem__`** / **`__delitem__`** for assignment and deletion. Iteration: **`__iter__(self)`** (return an iterator) and optionally **`__next__`** if the object is its own iterator.

---

## Q5. (Medium) How do you make an object callable (like a function)? What method?

**Answer:**  
Define **`__call__(self, *args, **kwargs)`**. Then `obj(...)` invokes __call__. Used for callable objects (functors), decorators, or when you want “object()” syntax.

---

## Q6. (Medium) What do `__eq__` and `__hash__` have to do with each other? When must you implement both?

**Answer:**  
If a class defines **__eq__** and is intended to be **hashable** (e.g. in a set or as dict key), it must define **__hash__** so that `a == b` implies `hash(a) == hash(b)`. Mutable objects typically should not be hashable; defining __eq__ without __hash__ makes the class unhashable (which is default for user classes in Python 3).

---

## Q7. (Medium) What does `__getattr__` do? How is it different from `__getattribute__`?

**Answer:**  
**`__getattr__(self, name)`** is called only when the attribute is **not** found by normal lookup. **`__getattribute__(self, name)`** is called for **every** attribute access; it’s easy to cause infinite recursion (use `object.__getattribute__(self, name)` to get attributes). Use __getattr__ for “virtual” or fallback attributes.

---

## Q8. (Tough) Implement a class that supports addition of two instances (e.g. `a + b`). What method(s)?

**Answer:**
```python
class Vec:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __add__(self, other):
        if not isinstance(other, Vec):
            return NotImplemented
        return Vec(self.x + other.x, self.y + other.y)
```
**`__add__`** for `self + other`. Return **NotImplemented** if you don’t support the type so Python can try `other.__radd__(self)`.

---

## Q9. (Tough) What is `__slots__`? What are the benefits and trade-offs?

**Answer:**  
**`__slots__`** is a class attribute (e.g. `__slots__ = ('x', 'y')`) that restricts instance attributes to those names. Benefits: less memory (no __dict__), faster attribute access. Trade-offs: no dynamic attributes, no __dict__, inheritance can be trickier (subclasses get __dict__ unless they also define __slots__). Use for many small instances with fixed attributes.

---

## Q10. (Tough) What is the difference between `__iter__` and `__next__`? When does each get called?

**Answer:**  
**`__iter__`** is called when you iterate (e.g. `for x in obj`); it must return an **iterator** (an object with __next__). **`__next__`** is called for each value; it returns the next value or raises **StopIteration** when done. A class can be its own iterator by implementing both: __iter__ returns self, __next__ returns values. Or __iter__ returns a separate iterator object.
