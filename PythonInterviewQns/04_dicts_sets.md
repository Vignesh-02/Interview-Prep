# 4. Dictionaries and Sets

## Q1. (Easy) What is the difference between a dict and a set? What can be a key in a dict?

**Answer:**  
**dict** maps keys to values; **set** stores unique elements (no duplicates, no order before 3.7). Dict keys must be **hashable** (immutable and implementing `__hash__` and `__eq__`). So int, str, tuple (of hashables) can be keys; list and dict cannot. Set elements must also be hashable.

---

## Q2. (Easy) How do you safely get a value from a dict with a default if the key is missing?

**Answer:**  
Use **`d.get(key, default)`** — returns `d[key]` if key exists, else `default`. Or use **`d.setdefault(key, default)`** to get the value and set `d[key] = default` if key was missing. For “default dict” behavior, use **`collections.defaultdict`**.

---

## Q3. (Easy) How do you merge two dicts (Python 3.9+ and older way)?

**Answer:**  
**3.9+:** `d1 | d2` or `d1 |= d2` (update). **Older:** `{**d1, **d2}` (creates new dict; later overwrites earlier for same keys). Or `d1.update(d2)` to mutate `d1`.

---

## Q4. (Medium) What does `dict.fromkeys(['a', 'b'], 0)` return? When is it useful?

**Answer:**  
It returns **`{'a': 0, 'b': 0}`** — keys from the first iterable, same value for all. Useful for initializing a dict with a set of keys and a single default. Beware: if the value is mutable (e.g. a list), all keys share the same object; use a dict comp or loop to get separate objects.

---

## Q5. (Medium) Why can’t a list or dict be an element of a set? How do you get “set of lists” behavior?

**Answer:**  
Set elements must be **hashable**. Lists and dicts are mutable and not hashable. Use **frozenset** for sets of sets. For “set of lists,” convert each list to a **tuple** (if elements are hashable) and put tuples in the set, or use a dict keyed by tuple to store associated data.

---

## Q6. (Medium) What is the time complexity of dict lookup, insertion, and set membership?

**Answer:**  
Average **O(1)** for get, set, delete, and `key in dict`. Set membership is also O(1) average. Implemented via hash tables. Worst case O(n) with many collisions, but rare with a good hash function.

---

## Q7. (Medium) What does `d.pop(key, default)` do? What if key is missing and you don’t pass default?

**Answer:**  
Removes the key and returns its value. If key is missing and `default` is given, returns `default`. If key is missing and `default` is not given, **KeyError** is raised.

---

## Q8. (Tough) Implement a function that inverts a dict (values become keys). What if values are not unique?

**Answer:**
```python
def invert(d):
    inv = {}
    for k, v in d.items():
        inv.setdefault(v, []).append(k)
    return inv
```
If values are unique, you can do `{v: k for k, v in d.items()}`. For non-unique values, values in the inverted dict must be lists (or some collection) of original keys.

---

## Q9. (Tough) What is the order of iteration over a dict (Python 3.7+)? How do you iterate in reverse or by value?

**Answer:**  
**3.7+:** Dicts preserve **insertion order**. Iteration is in that order. Reverse: `for k in reversed(d):` or `reversed(d.keys())`. By value: `for k in sorted(d, key=d.get):` or `sorted(d.items(), key=lambda x: x[1])`.

---

## Q10. (Tough) Given a list of strings, return a dict mapping each string to the list of indices where it appears. One pass only.

**Answer:**
```python
def index_map(words):
    out = {}
    for i, w in enumerate(words):
        out.setdefault(w, []).append(i)
    return out
```
`setdefault(w, [])` returns the list (creating it if needed); we append `i` to it.
