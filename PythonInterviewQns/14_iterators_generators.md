# 14. Iterators and Generators

## Q1. (Easy) What is an iterator? What two methods must it implement?

**Answer:**  
An **iterator** is an object that produces a sequence of values. It must implement **`__iter__`** (returning itself) and **`__next__`** (return the next value or raise **StopIteration** when done). **Iterables** implement __iter__ and return an iterator; iterators are iterables that return themselves from __iter__.

---

## Q2. (Easy) What is a generator? How do you create one?

**Answer:**  
A **generator** is an iterator defined with **`yield`**. Create with a **generator function** (a function that contains `yield`) — calling it returns a generator object. Or use a **generator expression**: `(x for x in range(5))`. No yield in the body until you call the function; then execution pauses at each yield and resumes on next().

---

## Q3. (Easy) What does `yield` do? How is it different from `return`?

**Answer:**  
**yield** produces a value to the caller and **pauses** the function; on the next **next()** call, execution resumes after the yield. **return** ends the function and (with a value) that value becomes the StopIteration value. A generator can have multiple yields; after return (or end of function), the generator is exhausted.

---

## Q4. (Medium) What does `yield from iterable` do?

**Answer:**  
**`yield from iterable`** delegates to that iterable: it yields every value from it. Equivalent to `for x in iterable: yield x` but more efficient and preserves subgenerator semantics (e.g. send/throw propagate to the subgenerator). Use to compose generators.

---

## Q5. (Medium) How do you send a value into a generator? What method? What does the generator receive?

**Answer:**  
Use **`gen.send(value)`**. The generator receives that value as the result of the **current** **yield** expression (the one that paused). So `x = yield` receives the sent value in `x`. **next(gen)** is equivalent to **gen.send(None)**. The first send must be None (or use next()) because there’s no current yield to receive yet.

---

## Q6. (Medium) What is the difference between an iterable and an iterator? Is a list an iterator?

**Answer:**  
**Iterable** has **__iter__** (and optionally __getitem__ for legacy); you get values by iterating (e.g. for loop). **Iterator** has __iter__ and __next__; it is stateful and consumed. A **list** is iterable but **not** an iterator — each `iter(list)` gives a new iterator. Calling **next** on a list is TypeError; call **next(iter(list))** or use in a for loop.

---

## Q7. (Medium) Why might you use a generator instead of returning a list?

**Answer:**  
**Lazy evaluation** — values are produced on demand, so you can represent infinite or large sequences without storing everything. **Memory** — only one value in memory at a time. **Pipeline** — chain generators without building intermediate lists. Use a list when you need random access, length, or multiple passes.

---

## Q8. (Tough) Implement an iterator class that yields 0, 1, 2, ... up to a limit set in the constructor.

**Answer:**
```python
class CountUpTo:
    def __init__(self, n):
        self.n = n
        self.current = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self.current >= self.n:
            raise StopIteration
        val = self.current
        self.current += 1
        return val
```

---

## Q9. (Tough) What does `gen.throw(exc)` do? When would you use it?

**Answer:**  
**gen.throw(exc)** injects an exception at the current **yield**; the generator can catch it and handle it (or let it propagate). Used for error handling in cooperative coroutines or to signal the generator to clean up. Similar to how send() injects a value, throw() injects an exception.

---

## Q10. (Tough) What is the output and why?

```python
def gen():
    yield 1
    return 2
g = gen()
print(next(g))
print(next(g))
```

**Answer:**  
First **1** (first yield). Second **next(g)** causes the generator to run past the yield, hit **return 2**, and finish. The return value **2** is attached to the **StopIteration** as `StopIteration.value`. So you get **StopIteration** raised; in a for loop it’s swallowed. To get the value: catch StopIteration and read `.value`, or use `yield from` in a parent generator to receive it.
