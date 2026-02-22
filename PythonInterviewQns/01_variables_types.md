# 1. Variables, Data Types, and Type Hints

## Q1. (Easy) What are the main built-in numeric types in Python? How do int and float differ?

**Answer:**  
The main numeric types are **int** (arbitrary-precision integers) and **float** (IEEE 754 double). There is also **complex** (e.g. `3+4j`). **int** has no fixed size (limited by memory); **float** is 64-bit and can have precision issues (e.g. `0.1 + 0.2 != 0.3` in representation). Division `/` always returns float; `//` is floor division and returns int when both operands are int.

---

## Q2. (Easy) What is the type of `type`? What does `type(x)` return?

**Answer:**  
`type` is a class (a type); `type(type)` is `type`. `type(x)` returns the class (type) of the object `x`. You can use it to check types at runtime, though `isinstance(x, SomeClass)` is usually preferred for subclasses.

---

## Q3. (Easy) What is the difference between `is` and `==`?

**Answer:**  
`==` checks **value equality** (calls `__eq__`). `is` checks **identity**: whether two names refer to the same object in memory. Use `is` for singletons like `None` (`x is None`). For small integers, CPython caches objects, so `a is b` might be True for equal small ints, but never rely on that; use `==` for values.

---

## Q4. (Medium) What are type hints? Does Python enforce them at runtime?

**Answer:**  
Type hints are annotations (e.g. `def f(x: int) -> str`) that describe expected types. They are **not enforced at runtime** by default; they are for static checkers (mypy, pyright) and documentation. Use `typing` module for generics (e.g. `List[int]`, `Optional[str]`). Runtime inspection is possible via `__annotations__` or tools like `typing.get_type_hints()`.

---

## Q5. (Medium) What is `None`? Is it the same as False or an empty string?

**Answer:**  
`None` is the single instance of `NoneType`; it means “no value.” It is not the same as `False` (boolean) or `""` (str). In a boolean context it’s falsy, but `None is None` is True and `None == False` is False. Use `if x is None` to check for absence of value.

---

## Q6. (Medium) Explain `Optional[T]` and `Union[T, None]`. What does `X | None` mean (Python 3.10+)?

**Answer:**  
`Optional[T]` is equivalent to `Union[T, None]` — a value of type T or None. In Python 3.10+, you can write **`T | None`** (union syntax) instead of `Optional[T]`. All mean “either T or None.”

---

## Q7. (Medium) What are the mutable and immutable built-in types? Why does it matter?

**Answer:**  
**Immutable:** int, float, str, tuple, frozenset, bytes, range. **Mutable:** list, dict, set, bytearray, and most custom classes. Immutable objects can be used as dict keys and set elements; they are safe to share. Mutable default arguments (e.g. `def f(x=[])`) are a classic bug because the same list is reused across calls.

---

## Q8. (Tough) Predict the output and explain.

```python
a = 256
b = 256
print(a is b)
c = 257
d = 257
print(c is d)
```

**Answer:**  
First: **True** — CPython caches small integers (typically -5 to 256); `a` and `b` refer to the same object. Second: **False** — 257 is outside the cache, so `c` and `d` are different objects. Never rely on `is` for integers; use `==`.

---

## Q9. (Tough) What does `__annotations__` contain for a function? How can you use it at runtime?

**Answer:**  
`function.__annotations__` is a dict mapping parameter names (and `'return'`) to their annotation objects. You can use it for validation, serialization, or dependency injection. Annotations are not enforced; they’re just stored. Use `typing.get_type_hints(f)` for resolved forward references and Optional.

---

## Q10. (Tough) Write a generic function that accepts either an int or a list of ints and returns the sum. Use type hints (Union or `|`).

**Answer:**
```python
from typing import Union

def sum_int_or_list(x: Union[int, list[int]]) -> int:
    if isinstance(x, int):
        return x
    return sum(x)

# Python 3.10+:
def sum_int_or_list(x: int | list[int]) -> int:
    return x if isinstance(x, int) else sum(x)
```
