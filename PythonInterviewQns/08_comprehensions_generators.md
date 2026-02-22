# 8. List Comprehensions and Generator Expressions

## Q1. (Easy) What is a list comprehension? Give the syntax.

**Answer:**  
A list comprehension builds a list in one expression: **`[expr for item in iterable]`**. Optional: **`[expr for item in iterable if condition]`**. It’s equivalent to a for-loop that appends to a list, but more concise.

---

## Q2. (Easy) What is the difference between `[x for x in range(5)]` and `(x for x in range(5))`?

**Answer:**  
The first is a **list comprehension** — it builds the full list in memory. The second is a **generator expression** — it returns a generator that yields values on demand (lazy). The generator is memory-efficient and single-use.

---

## Q3. (Easy) How do you do a nested list comprehension? Flatten a list of lists in one line.

**Answer:**  
Nested: **`[expr for inner in outer for item in inner]`** (order like nested for loops). Flatten: **`[x for sub in matrix for x in sub]`**.

---

## Q4. (Medium) What is a dict comprehension? Set comprehension?

**Answer:**  
**Dict:** `{k: v for item in iterable}` or `{k: v for k, v in items}`. **Set:** `{expr for item in iterable}` — like list comp but with `{}`, so duplicates are removed. Both support an optional `if`.

---

## Q5. (Medium) When would you prefer a generator expression over a list comprehension?

**Answer:**  
Use a generator when: (1) You don’t need the full list in memory (large or infinite). (2) You only iterate once. (3) You want to short-circuit (e.g. with `any`/`all` or breaking). List comp is better when you need indexing, length, or multiple iterations.

---

## Q6. (Medium) What does `sum(x for x in range(10) if x % 2 == 0)` return? No brackets — why is that valid?

**Answer:**  
Returns **20** (0+2+4+6+8). The parentheses around the generator expression are implied when it’s the only argument: `sum((x for ...))` can be written `sum(x for x in ...)`. So it’s a generator expression, not a tuple.

---

## Q7. (Medium) How do you build a list of tuples with a list comprehension? Example: (index, value) for a list.

**Answer:**  
**`[(i, x) for i, x in enumerate(lst)]`** or **`list(enumerate(lst))`**. For two lists in parallel: **`[(a, b) for a, b in zip(lst1, lst2)]`**.

---

## Q8. (Tough) What is wrong with this and how do you fix it? `matrix = [[0] * 3] * 4`

**Answer:**  
All four rows are the **same** list (same reference). Changing `matrix[0][0] = 1` changes the first column in every row. Fix: **`[[0] * 3 for _ in range(4)]`** — each row is a new list.

---

## Q9. (Tough) Write a one-liner that returns the list of prime numbers in range(2, n) using a sieve-like idea or a simple check (no need for full sieve).

**Answer:**  
Simple “trial division” in one line (readable version):
```python
def primes(n):
    return [p for p in range(2, n) if all(p % d != 0 for d in range(2, int(p**0.5) + 1))]
```
Or using a set to mark composites (sieve style) is usually done with a loop; a compact sieve is possible but less readable.

---

## Q10. (Tough) What is the output and why?

```python
gen = (x for x in [1, 2, 3])
print(list(gen))
print(list(gen))
```

**Answer:**  
First: **`[1, 2, 3]`**. Second: **`[]`**. A generator is **exhausted** after one full iteration; it doesn’t store the values. So the second `list(gen)` has nothing left to consume.
