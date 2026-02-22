# 20. Tricky Output and Edge Cases

## Q1. (Easy) What does this print? `print([] or "default")`

**Answer:** **"default".** **or** returns the first truthy value; **[]** is falsy, so the result is **"default"**.

---

## Q2. (Easy) What is the output? `x = 1; x += 1; print(x)` and `lst = [1]; lst += [2]; print(lst)`

**Answer:** **x** is **2** (rebound). **lst** is **[1, 2]** — list **+=** is in-place (extend). So int gets a new value; list is mutated.

---

## Q3. (Medium) What does this print and why?

```python
def f(lst=[]):
    lst.append(1)
    return lst
print(f())
print(f())
```

**Answer:** **[1]** then **[1, 1].** The default **[]** is created once and shared. First call appends 1; second call appends to the same list. So you get a growing list. Fix: default to **None** and create a new list inside.

---

## Q4. (Medium) What is the output?

```python
a = [1, 2, 3]
b = a
b = b + [4]
print(a)
```

**Answer:** **[1, 2, 3].** **b = b + [4]** creates a **new** list and rebinds **b**; **a** still refers to the original list. So **a** is unchanged.

---

## Q5. (Medium) What does this print?

```python
for i in range(3):
    print(i)
    i = 10
```

**Answer:** **0**, **1**, **2**. Assigning to **i** inside the loop doesn’t change the loop variable for the next iteration; **range** controls the values. So **i = 10** has no effect on the loop.

---

## Q6. (Tough) What is the output?

```python
t = (1, 2, [3])
t[2] += [4]
```

**Answer:** **TypeError** (or, in some versions, the tuple might still show the mutation). **t[2]** is a list; **+=** mutates it in place, but the assignment part of **+=** tries to assign back to **t[2]**, which is illegal because tuples are immutable. So you get an error even though the list **did** get **[4]** appended — don’t rely on that; avoid mutating tuple elements.

---

## Q7. (Tough) What does this print?

```python
d = {}
d[[1, 2]] = 3
```

**Answer:** **TypeError: unhashable type: 'list'.** Dict keys must be **hashable**. Lists are mutable and not hashable. Use a **tuple** instead: **d[(1, 2)] = 3** or **d[tuple([1, 2])] = 3**.

---

## Q8. (Tough) Predict the output.

```python
a = 256
b = 256
print(a is b)
x = 257
y = 257
print(x is y)
```

**Answer:** **True** then **False** (in CPython). Small integers (-5 to 256) are cached; **256** is the same object. **257** is not cached, so **x** and **y** may be different objects. Never rely on **is** for integers; use **==**.

---

## Q9. (Tough) What is printed?

```python
def f():
    try:
        return 1
    finally:
        return 2
print(f())
```

**Answer:** **2.** The **finally** block runs when leaving the try; its **return** overrides the try’s return. So the function returns **2**.

---

## Q10. (Tough) What does this output and why?

```python
class C:
    pass
c = C()
c.x = 1
def get_x(self):
    return self.x
C.get_x = get_x
print(c.get_x())
```

**Answer:** **1.** You added a **method** to the class **after** creating the instance. Instances look up methods on the class; **C.get_x** now exists and receives **c** as **self**. So **c.get_x()** returns **c.x** which is **1**.
