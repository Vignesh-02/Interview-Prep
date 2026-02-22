# 10. Exception Handling (try, except, else, finally)

## Q1. (Easy) What is the syntax of try/except? How do you catch a specific exception?

**Answer:**  
**`try:`** block, then **`except ExceptionType as e:`** to catch that type and bind to `e`. You can have multiple `except` clauses. **`except:`** (no type) catches everything — avoid; catch concrete types or `Exception`. Use **`except E as e:`** to inspect the exception.

---

## Q2. (Easy) What is the difference between `except Exception` and `except BaseException`?

**Answer:**  
**Exception** is the usual base for “normal” exceptions (ValueError, TypeError, etc.). **BaseException** is above that and also includes **KeyboardInterrupt** and **SystemExit**. Catching `BaseException` (or bare `except`) will also catch those; usually you want to catch **Exception** so you don’t prevent the user from interrupting the program.

---

## Q3. (Easy) What does the `else` clause on a try block do? When does it run?

**Answer:**  
The **try/except/else**: the **else** block runs only if the **try** block completed **without** raising an exception. So it’s “what to do on success.” It runs before `finally`. Use it to keep the try block small (only the code that might raise) and put the “success path” in else.

---

## Q4. (Medium) When does the `finally` block run? What if there’s a return in try or except?

**Answer:**  
**finally** runs when leaving the try/except/else block — whether by normal exit, exception, or **return**. So it always runs (except for os._exit or fatal interpreter crash). Use it for cleanup (close files, release locks). If finally has a return, it overrides the return in try/except.

---

## Q5. (Medium) How do you re-raise an exception after handling it? Why would you do that?

**Answer:**  
Use **`raise`** with no arguments inside an except block — re-raises the current exception and preserves the traceback. Do this when you log or do partial handling but want the caller to still see the exception. Or **`raise e`** to re-raise a caught exception (can lose traceback; prefer bare `raise`).

---

## Q6. (Medium) What is the difference between `raise E` and `raise E from e`?

**Answer:**  
**`raise E`** raises a new exception. **`raise E from e`** sets `E.__cause__` to `e` (chaining). The traceback will show “The above exception was the direct cause of the following exception.” Use **`raise E from None`** to suppress the original traceback (when you’re replacing an internal error with a user-facing one).

---

## Q7. (Medium) How do you define a custom exception? Best practice for hierarchy?

**Answer:**  
Subclass **Exception** (or a more specific base): `class MyError(Exception): pass`. Add an optional message: `class MyError(Exception): pass` then `raise MyError("details")`. For a hierarchy, subclass your own base: `class MyValueError(MyError): pass`. Don’t inherit from BaseException for app-level exceptions.

---

## Q8. (Tough) What is the output and why?

```python
def f():
    try:
        return 1
    finally:
        return 2
print(f())
```

**Answer:**  
**2.** The finally block runs when leaving the try. The return in finally **overrides** the return in try, so the function returns 2. Generally avoid returning a value from finally; use it only for cleanup.

---

## Q9. (Tough) How do you catch multiple exception types in one except? How do you get the same handling for different types?

**Answer:**  
**`except (TypeError, ValueError) as e:`** — tuple of types; if any is raised, this block runs. For the same handling for different types, put them in a tuple. You can also use **`except (A, B):`** and then handle both the same way.

---

## Q10. (Tough) What does `assert x > 0` do? When should you not use assert for validation?

**Answer:**  
**assert** checks the condition; if False, raises **AssertionError**. With **`python -O`** (optimize), asserts are **removed** — so never use assert for input validation or critical checks. Use it for “this should never happen” invariants during development. For validation, use explicit if/raise.
