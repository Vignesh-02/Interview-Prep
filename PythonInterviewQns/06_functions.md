# 6. Functions (args, kwargs, scope)

## Q1. (Easy) What is the difference between a parameter and an argument?

**Answer:**  
A **parameter** is the variable name in the function definition (e.g. `def f(x, y)` — `x` and `y` are parameters). An **argument** is the value passed when calling the function (e.g. `f(1, 2)` — `1` and `2` are arguments).

---

## Q2. (Easy) What does `return` without a value do? What does a function return if it has no return statement?

**Answer:**  
`return` without a value (or just `return`) exits the function and returns **None**. A function that reaches the end without hitting `return` also returns **None**.

---

## Q3. (Easy) What is local scope? When is a variable “local” to a function?

**Answer:**  
Variables assigned inside a function are **local** to that function (from the point of assignment). They are not visible outside and are discarded when the function returns. Reading a name looks in local scope first, then enclosing, then global, then builtins (LEGB).

---

## Q4. (Medium) What is the difference between `*args` and `**kwargs`? Can you use other names?

**Answer:**  
**`*args`** collects extra **positional** arguments into a tuple. **`**kwargs`** collects extra **keyword** arguments into a dict. The names `args` and `kwargs` are convention; you can use any name (e.g. `*rest`, `**options`). The important part is the single/double asterisk.

---

## Q5. (Medium) What happens if you assign to a variable inside a function that was already used (e.g. read) in the same function?

**Answer:**  
If you **assign** to a name anywhere in the function, that name is treated as **local** for the **entire** function. So if you read it before assigning, you get **UnboundLocalError** (read before assignment). To assign to a global variable, use **`global name`**; to assign to an enclosing variable, use **`nonlocal name`**.

---

## Q6. (Medium) What is the order of parameters in a function definition (positional, *args, keyword-only, **kwargs)?

**Answer:**  
Correct order: (1) positional-only (optional, with `/`), (2) positional and keyword, (3) `*args` or bare `*`, (4) keyword-only, (5) `**kwargs`. Example: `def f(a, b=1, *args, k, **kwargs):` — `k` is keyword-only after `*args`.

---

## Q7. (Medium) What does `global x` do? What about `nonlocal x`?

**Answer:**  
**`global x`** declares that assignments to `x` in the function refer to the **module-level** `x`. **`nonlocal x`** declares that assignments refer to `x` in the **nearest enclosing** scope (not global). Both are only needed when you **assign**; reading can see outer scopes without declaring.

---

## Q8. (Tough) What is the output and why?

```python
x = 10
def f():
    print(x)
    x = 20
f()
```

**Answer:**  
**UnboundLocalError.** Because `x` is assigned later in the function, Python treats `x` as local for the whole function. The `print(x)` then tries to read the local `x` before it has been assigned. Fix: use `global x` if you mean the global, or use a different name for the local.

---

## Q9. (Tough) Write a function that accepts only keyword arguments after the first two (enforce keyword-only).

**Answer:**
```python
def f(a, b, *, option1=None, option2=None):
    pass
```
The bare **`*`** means everything after it must be passed by keyword. So `f(1, 2, option1=3)` is valid; `f(1, 2, 3)` is invalid for the third argument.

---

## Q10. (Tough) What does this print and why?

```python
def f(a, b, *args, c=10, **kwargs):
    print(a, b, args, c, kwargs)
f(1, 2, 3, 4, c=5, x=6)
```

**Answer:**  
**1 2 (3, 4) 5 {'x': 6}.** `a=1`, `b=2`; extra positional go to `args` → `(3, 4)`; `c` is keyword-only and gets 5; extra keyword `x=6` goes to `kwargs` → `{'x': 6}`.
