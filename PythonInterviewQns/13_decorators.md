# 13. Decorators

## Q1. (Easy) What is a decorator? What does `@decorator` above a function do?

**Answer:**  
A **decorator** is a callable that takes a function (or class) and returns a replacement. **`@decorator`** above `def f(): ...` is equivalent to **`f = decorator(f)`**. So the name `f` now refers to the result of the decorator (often a wrapper that calls the original).

---

## Q2. (Easy) Write a simple decorator that prints “before” and “after” when a function is called.

**Answer:**
```python
def log(f):
    def wrapper(*args, **kwargs):
        print("before")
        result = f(*args, **kwargs)
        print("after")
        return result
    return wrapper
```
Use **functools.wraps(f)** on wrapper to preserve __name__ and __doc__.

---

## Q3. (Easy) What does `functools.wraps` do? Why use it?

**Answer:**  
**`@wraps(f)`** (applied to the wrapper) copies **__name__**, **__doc__**, and other metadata from `f` to the wrapper. So `help(decorated)` and `decorated.__name__` look correct. Without it, the wrapper’s name would be "wrapper" and docstring would be lost.

---

## Q4. (Medium) How do you write a decorator that accepts arguments (e.g. `@retry(3)`)?

**Answer:**  
The decorator with arguments must return a decorator that takes the function. So you need two levels: `def retry(n): return lambda f: ...` or a nested def that takes `f` and returns the wrapper. Example: `def retry(n): def dec(f): ... return dec` then `return dec(f)` and use `n` in the wrapper.

---

## Q5. (Medium) What does this do and what’s wrong with it? `def dec(f): return f`

**Answer:**  
It’s a “no-op” decorator — returns the same function. Nothing is wrong if you want to tag or register the function without wrapping. But if you meant to wrap and forgot, callers would get the original `f` with no extra behavior.

---

## Q6. (Medium) How do you decorate a method so that `self` is still passed correctly?

**Answer:**  
The wrapper should accept **`*args, **kwargs`** and call **`f(*args, **kwargs)`**. So `args[0]` will be `self` when `f` is a method. No special handling needed as long as you pass through all arguments. Using **functools.wraps** keeps the wrapper’s signature sensible for introspection.

---

## Q7. (Medium) What is a class decorator? Give a one-line idea.

**Answer:**  
A **class decorator** is a callable that takes a class and returns a (possibly modified or replaced) class. **`@dec`** above `class C:` means **`C = dec(C)`**. Use to register classes, add methods, or wrap construction (e.g. singleton).

---

## Q8. (Tough) Implement a `@memoize` decorator that caches return values by arguments (assume hashable args).

**Answer:**
```python
from functools import wraps

def memoize(f):
    cache = {}
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]
    return wrapper
```
For unhashable args you’d need to convert to something hashable or use a different key strategy.

---

## Q9. (Tough) What is the order of execution when multiple decorators are stacked? `@a` then `@b` on `def f`?

**Answer:**  
**`@a`** then **`@b`** means `f = a(b(f))`. So **b** is applied first (innermost), then **a**. Execution order when calling `f()`: a’s wrapper runs first, then b’s wrapper, then the original `f`. So decorators run “bottom-up” in application, “top-down” in execution.

---

## Q10. (Tough) Write a decorator that raises an error if the function is called with keyword arguments (for learning; not for production style).

**Answer:**
```python
def no_kwargs(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs:
            raise TypeError("Keyword arguments not allowed")
        return f(*args, **kwargs)
    return wrapper
```
