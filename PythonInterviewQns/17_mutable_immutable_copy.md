# 17. Mutable vs Immutable, Shallow vs Deep Copy

## Q1. (Easy) List mutable and immutable built-in types.

**Answer:**  
**Immutable:** int, float, str, tuple, frozenset, bytes, range. **Mutable:** list, dict, set, bytearray. Custom class instances are mutable by default. Immutable objects can be used as dict keys and set elements; their “value” doesn’t change (any “change” creates a new object).

---

## Q2. (Easy) What does `copy.copy(x)` do? What about `copy.deepcopy(x)`?

**Answer:**  
**copy.copy(x)** — **shallow copy**: new top-level object; nested objects are **shared** (same references). **copy.deepcopy(x)** — **deep copy**: recursively copies everything so no shared mutable nested structure. For a list of lists, shallow copy: outer list new, inner lists shared.

---

## Q3. (Easy) Is a tuple always immutable? What if it contains a list?

**Answer:**  
The **tuple** itself is immutable (you can’t add/remove/replace elements). But if an element is **mutable** (e.g. a list), the **contents** of that element can change. So `t = (1, [2]); t[1].append(3)` is valid and changes the list inside the tuple. The tuple’s identity and references don’t change.

---

## Q4. (Medium) What is the difference between `lst[:]` and `list(lst)` for a list? Are they deep copies?

**Answer:**  
Both are **shallow** copies: new list, same elements (same references). **lst[:]** — slice copy. **list(lst)** — construct from iterable. For nested structures, neither copies the inner lists/dicts. Use **copy.deepcopy** for full independence.

---

## Q5. (Medium) Why does `def f(a=[]):` lead to a bug? What is the fix?

**Answer:**  
The **default is evaluated once** when the function is defined, not per call. So every call that uses the default shares the **same** list. Appending in one call affects the next. Fix: **`def f(a=None): a = a if a is not None else []`** or **`def f(a=None): a = [] if a is None else a`** — or use a sentinel and create a new list inside the function.

---

## Q6. (Medium) What does `x += 1` do for an int? What about `lst += [1]` for a list?

**Answer:**  
For **int**, **x += 1** rebinds **x** to a new integer (ints are immutable). For **list**, **lst += [1]** is **in-place** (like extend); it mutates the list and doesn’t reassign. So **+=** behaves as in-place when the type has **__iadd__** (list does); otherwise it’s like **x = x + 1** (new object).

---

## Q7. (Medium) How do you copy a dict shallowly? Deeply?

**Answer:**  
Shallow: **`d.copy()`** or **`dict(d)`** or **`{**d}`**. Deep: **`copy.deepcopy(d)`**. Shallow: nested dicts/lists are shared. Deep: full recursive copy.

---

## Q8. (Tough) What is the output and why?

```python
a = [1, 2, 3]
b = a
b += [4]
print(a)
```

**Answer:**  
**[1, 2, 3, 4].** **b** and **a** refer to the same list. **+=** on a list is in-place, so the shared list is mutated. So **a** sees the change. If it were **b = b + [4]**, **b** would be rebound to a new list and **a** would be unchanged.

---

## Q9. (Tough) What can go wrong with `copy.deepcopy`? When might you need a custom __deepcopy__?

**Answer:**  
**deepcopy** can hit **recursive** structures (cycle); the module handles that with a memo dict. It may not know how to copy **custom objects** correctly (e.g. file handles, threads). Define **__deepcopy__(self, memo)** to control how your class is deep-copied and to register copies in **memo** to handle cycles.

---

## Q10. (Tough) Implement a function that returns a deep copy of a nested list of integers (no other types). No copy module.

**Answer:**
```python
def deep_copy_list(lst):
    return [deep_copy_list(x) if isinstance(x, list) else x for x in lst]
```
For a dict-of-lists or mixed structures you’d add branches for dict, set, etc., and use a memo dict if cycles are possible.
