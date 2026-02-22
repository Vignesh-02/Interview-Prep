# 3. Lists, Tuples, and Sequences

## Q1. (Easy) What is the difference between a list and a tuple?

**Answer:**  
**List** is mutable (append, remove, change elements); **tuple** is immutable. Tuples can be used as dict keys and set elements; lists cannot. Tuples are slightly more memory-efficient and can signal “fixed structure” (e.g. coordinates). Syntax: `[]` vs `()` (or just commas).

---

## Q2. (Easy) How do you get the last element of a list? What about the last n elements?

**Answer:**  
Last element: `lst[-1]`. Last n: `lst[-n:]` (e.g. `lst[-3:]` for last three). Negative indices count from the end.

---

## Q3. (Easy) What does `list.append(x)` return? What is the difference between `append` and `extend`?

**Answer:**  
`append(x)` returns **None**; it mutates the list. `append` adds one element (even if it’s a list: `[1, 2, [3, 4]]`). `extend(iterable)` adds each item from the iterable: `[1, 2].extend([3, 4])` → `[1, 2, 3, 4]`.

---

## Q4. (Medium) What is the difference between `lst.sort()` and `sorted(lst)`?

**Answer:**  
`lst.sort()` sorts **in place**, returns None, and only works for lists. `sorted(iterable)` returns a **new list** and does not mutate the original; it works on any iterable. Use `sorted()` when you need to keep the original or sort something that isn’t a list.

---

## Q5. (Medium) What does `lst += [1, 2]` do? How is it different from `lst = lst + [1, 2]`?

**Answer:**  
`lst += [1, 2]` is **in-place** (like `extend`); it mutates `lst` and does not reassign. `lst = lst + [1, 2]` creates a **new** list and rebinds `lst`; the original list is unchanged (and may be garbage-collected). For a list, `+=` uses `__iadd__` (in-place); `+` uses `__add__` (new list).

---

## Q6. (Medium) What is `range(5)`, and is it a list? How do you get a list from it?

**Answer:**  
`range(5)` is a **range object** (iterable), not a list; it yields 0, 1, 2, 3, 4 without storing all in memory. Convert with **`list(range(5))`** → `[0, 1, 2, 3, 4]`.

---

## Q7. (Medium) Explain slice assignment: `lst[1:3] = [10, 20, 30]`. What happens to the length?

**Answer:**  
Slice assignment **replaces** that slice with the elements of the iterable on the right. So `lst[1:3] = [10, 20, 30]` removes elements at indices 1 and 2 and inserts three elements there; the list length can change. The right-hand side can have a different length than the slice.

---

## Q8. (Tough) What is the output and why?

```python
t = (1,)
t = t + (2,)
print(t)
t[0] = 0
```

**Answer:**  
First: `t` becomes `(1, 2)` — concatenation creates a new tuple. Second: **TypeError** — tuples are immutable; you cannot assign to `t[0]`.

---

## Q9. (Tough) How do you implement a stack and a queue using lists? What are the time complexities?

**Answer:**  
**Stack:** Use `append()` for push and `pop()` for pop — both amortized O(1). **Queue:** Using `list.pop(0)` is O(n). For a proper O(1) queue use **`collections.deque`**: `append`/`popleft` or `appendleft`/`pop`.

---

## Q10. (Tough) What does `*lst` do in a function call or in an assignment? Give an example of unpacking into a new list.

**Answer:**  
In a **function call**, `*lst` unpacks the iterable as positional arguments: `f(*[1, 2, 3])` → `f(1, 2, 3)`. In **assignment**, `*rest` captures the rest: `a, *mid, b = [1, 2, 3, 4]` → `a=1`, `mid=[2, 3]`, `b=4`. Example: `[*[1, 2], 3, *[4, 5]]` → `[1, 2, 3, 4, 5]`.
