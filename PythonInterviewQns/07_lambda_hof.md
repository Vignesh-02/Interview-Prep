# 7. Lambda and Higher-Order Functions

## Q1. (Easy) What is a lambda? How is it different from a def function?

**Answer:**  
A **lambda** is an anonymous expression: `lambda x: x + 1`. It returns a single expression’s value; no statements, no annotations, no docstring. A **def** can have multiple statements, return, and a body. Lambdas are limited to one expression; use def for anything more complex.

---

## Q2. (Easy) Name three built-in higher-order functions that take a function and an iterable.

**Answer:**  
**map(f, it)** — apply `f` to each element. **filter(pred, it)** — keep elements where `pred(x)` is true. **sorted(it, key=f)** — sort by key function. Also **functools.reduce(f, it[, initial])** — reduce to a single value.

---

## Q3. (Easy) What does `map(lambda x: x * 2, [1, 2, 3])` return in Python 3?

**Answer:**  
A **map object** (iterator), not a list. It yields 2, 4, 6 when consumed. To get a list: **`list(map(...))`**. In Python 2, map returned a list; in Python 3 it’s lazy.

---

## Q4. (Medium) What is `functools.reduce`? Write a one-liner that multiplies all numbers in a list.

**Answer:**  
**reduce(f, iterable[, initial])** applies a two-argument function cumulatively: `f(f(f(initial, x0), x1), x2)...`. Multiply all: **`reduce(lambda a, b: a * b, lst)`** or **`reduce(operator.mul, lst)`**. For empty list, you must provide `initial` (e.g. 1 for product).

---

## Q5. (Medium) What does `sorted(lst, key=lambda x: x[1])` do? How do you sort descending?

**Answer:**  
Sorts by the second element of each item (e.g. list of pairs). For descending, use **`reverse=True`** or **`key=lambda x: -x[1]`** (for numbers).

---

## Q6. (Medium) What is a higher-order function? Give an example that returns a function.

**Answer:**  
A **higher-order function** takes one or more functions as arguments and/or returns a function. Example: **`def make_adder(n): return lambda x: x + n`** — returns a function that adds `n` to its argument.

---

## Q7. (Medium) Why might you prefer list comprehensions over map/filter? When might map be better?

**Answer:**  
Comprehensions are often clearer and can do more (nested loops, conditions). **map** is good when the function already exists (e.g. `map(str, nums)`) and you want a lazy iterator. **filter** is equivalent to `[x for x in it if pred(x)]`. Style and readability usually favor comprehensions for simple cases.

---

## Q8. (Tough) What does `functools.partial` do? Write an example.

**Answer:**  
**partial(f, *args, **kwargs)** returns a callable that, when called, forwards its arguments to `f` along with the fixed args/kwargs. Example: `from functools import partial; double = partial(map, lambda x: x * 2)` or `inc = partial(lambda a, b: a + b, 1)` so `inc(2)` → 3.

---

## Q9. (Tough) Implement a function `compose(f, g)` that returns a function such that `compose(f, g)(x) == f(g(x))`.

**Answer:**
```python
def compose(f, g):
    return lambda x: f(g(x))

# For multiple functions:
from functools import reduce
def compose(*fs):
    return reduce(lambda f, g: lambda x: f(g(x)), fs)
```

---

## Q10. (Tough) What is the output and why?

```python
funcs = [lambda x: x + i for i in range(3)]
print([f(0) for f in funcs])
```

**Answer:**  
**[2, 2, 2].** The lambda closes over the **variable** `i`, not its value at loop time. When the lambdas are called, `i` is 2 (the last value). Fix: `lambda x, i=i: x + i` to capture the current value of `i` by default argument.
