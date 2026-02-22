# 16. *args, **kwargs, and Unpacking

## Q1. (Easy) What does `*args` collect in a function definition?

**Answer:**  
**`*args`** collects any extra **positional** arguments into a **tuple**. So `def f(a, *args):` — after `a` is bound, the rest go into `args`. The name can be anything (`*rest`); the single `*` is what matters.

---

## Q2. (Easy) What does `**kwargs` collect?

**Answer:**  
**`**kwargs`** collects extra **keyword** arguments into a **dict** (name → value). The name can be anything; the double `**` is what matters. Only keyword arguments that weren’t bound to a parameter go into kwargs.

---

## Q3. (Easy) In a function call, what does `*lst` do? What about `**d`?

**Answer:**  
In a **call**, **`*iterable`** unpacks the iterable as **positional** arguments. **`**dict`** unpacks the dict as **keyword** arguments (keys must be strings valid as identifiers). So `f(*[1, 2], **{'c': 3})` is like `f(1, 2, c=3)`.

---

## Q4. (Medium) In assignment, what does `a, *rest, b = [1, 2, 3, 4]` give?

**Answer:**  
**a=1**, **rest=[2, 3]**, **b=4**. The **starred** name collects “the rest” into a list. So you get first element, middle as list, last element. Works for any iterable on the right; the starred target is always a list.

---

## Q5. (Medium) Can you have both `*args` and `**kwargs` in the same function? What order?

**Answer:**  
Yes. Order must be: normal params, then **`*args`**, then keyword-only (optional), then **`**kwargs`**. So **`def f(a, *args, kw=1, **kwargs):`** — args gets extra positional, kwargs gets extra keyword.

---

## Q6. (Medium) What does `print(*[1, 2, 3], sep=',')` output? Why?

**Answer:**  
**1,2,3**. **`*[1, 2, 3]`** unpacks to three positional arguments, so it’s like `print(1, 2, 3, sep=',')`. So the separator is a comma and no space. Output: **1,2,3**.

---

## Q7. (Medium) How do you merge two dicts into one (without mutating) using unpacking?

**Answer:**  
**`{**d1, **d2}`** — creates a new dict; keys from d1 then d2; duplicate keys get the value from d2. Python 3.9+: **`d1 | d2`** also creates a new dict (d2 overwrites d1 for common keys).

---

## Q8. (Tough) What is the output and why?

```python
def f(*args, **kwargs):
    print(args, kwargs)
f(1, 2, x=3, 4)
```

**Answer:**  
**SyntaxError** (or invalid call). You cannot pass a positional argument after a keyword argument. So **4** after **x=3** is invalid. If the call were `f(1, 2, x=3)`, you’d get **args=(1, 2)**, **kwargs={'x': 3}**.

---

## Q9. (Tough) Write a function that forwards all arguments to another function: `forward(f, *args, **kwargs)` that returns `f(*args, **kwargs)`.

**Answer:**
```python
def forward(f, *args, **kwargs):
    return f(*args, **kwargs)
```
So the caller does `forward(print, 1, 2, sep=' ')` and that’s equivalent to `print(1, 2, sep=' ')`.

---

## Q10. (Tough) What does this do? `a, b, *c = (1,)`

**Answer:**  
**a=1**, **b** gets nothing — so **ValueError** (not enough values to unpack). For **`a, *b = (1,)`** you’d get a=1, b=[]. So with two non-starred names and a one-element tuple, unpacking fails. To allow “optional” rest, you need exactly one starred target: **a, *rest = (1,)** gives a=1, rest=[].
