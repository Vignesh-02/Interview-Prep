# 5. Control Flow and Loops

## Q1. (Easy) What values are truthy/falsy in Python? Name the main falsy ones.

**Answer:**  
**Falsy:** `False`, `None`, `0`, `0.0`, `""`, `[]`, `{}`, `()`, `set()`, and objects whose `__bool__` or `__len__` returns False/0. Everything else is **truthy**. So empty sequences and zero are falsy.

---

## Q2. (Easy) What is the ternary (conditional) expression syntax?

**Answer:**  
**`x if condition else y`** — evaluates to `x` when `condition` is true, else `y`. Example: `max_val = a if a > b else b`. No “then” keyword; order is value_if_true, condition, value_if_false.

---

## Q3. (Easy) What is the difference between `break` and `continue`? What about `else` on a loop?

**Answer:**  
**break** exits the loop immediately. **continue** skips to the next iteration. A **for/while … else** runs the `else` block only if the loop **completed normally** (no `break`). So `else` runs when no break was hit — useful for search loops (“if we didn’t break, nothing was found”).

---

## Q4. (Medium) How do you iterate over a list with indices? Over a dict’s keys and values?

**Answer:**  
Indices: **`for i, x in enumerate(lst):`** — `i` is index, `x` is value. Dict: **`for k, v in d.items():`** for keys and values. For keys only: `for k in d:` or `d.keys()`. For values: `d.values()`.

---

## Q5. (Medium) What does `pass` do? When would you use it?

**Answer:**  
`pass` is a **no-op**; it does nothing. Use it as a placeholder where syntax requires a block: empty `class`, `except`, or `if` bodies. Lets you run code before you implement the body.

---

## Q6. (Medium) How do you loop over multiple lists in parallel? What if they have different lengths?

**Answer:**  
Use **`zip(a, b, c)`** — iterates until the **shortest** iterable is exhausted. For same-length pairing this is correct. For different lengths, use **`itertools.zip_longest(a, b, fillvalue=None)`** to go to the longest and fill missing with `fillvalue`.

---

## Q7. (Medium) What is the difference between `for i in range(len(lst))` and `for i, x in enumerate(lst)`? When is each better?

**Answer:**  
`range(len(lst))` gives only indices; you access `lst[i]` yourself. `enumerate(lst)` gives index and value; cleaner and avoids indexing. Prefer **enumerate** when you need both. Use `range(len)` only when you need to mutate by index or need the index for something other than the current element.

---

## Q8. (Tough) What does this print and why?

```python
for i in range(3):
    print(i)
else:
    print("done")
```

**Answer:**  
Prints `0`, `1`, `2`, then **"done"**. The loop completed without a `break`, so the `else` block runs. If you had `break` inside the loop, "done" would not print.

---

## Q9. (Tough) Write a loop that finds the first index where a condition holds, or -1 if none. Use for-else.

**Answer:**
```python
def find_first(lst, predicate):
    for i, x in enumerate(lst):
        if predicate(x):
            return i
    return -1

# With for-else (else = "no break"):
def find_first(lst, predicate):
    for i, x in enumerate(lst):
        if predicate(x):
            break
    else:
        return -1
    return i
```

---

## Q10. (Tough) What is the output and why?

```python
x = 1
if True:
    x = 2
else:
    x = 3
print(x)
```

**Answer:**  
**2.** The condition is `True`, so the `if` block runs and `x` is set to 2. The `else` block is skipped. So `x` is 2.
