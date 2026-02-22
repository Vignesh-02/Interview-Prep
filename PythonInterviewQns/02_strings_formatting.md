# 2. Strings and String Formatting

## Q1. (Easy) How do you create a multi-line string? What is the difference between `'''` and `"""`?

**Answer:**  
Use triple quotes: `'''...'''` or `"""..."""`. Both allow newlines and embedded quotes. There is no semantic difference; use the one that avoids escaping (e.g. `"""` if the string contains `'`).

---

## Q2. (Easy) What is string slicing? What does `s[::-1]` do?

**Answer:**  
Slicing is `s[start:stop:step]`. Omitted start/stop default to beginning/end. Negative indices count from the end. `s[::-1]` uses step -1 and reverses the string.

---

## Q3. (Easy) Name three ways to format strings in Python (old, .format, f-string).

**Answer:**  
(1) **% formatting**: `"Hello, %s" % name`. (2) **str.format**: `"Hello, {}".format(name)` or `"{0} {1}".format(a, b)`. (3) **f-strings** (3.6+): `f"Hello, {name}"` — expressions in `{}`, evaluated at runtime. Prefer f-strings for readability and performance.

---

## Q4. (Medium) What does `s.strip()` do? What about `s.strip('x')`?

**Answer:**  
`strip()` removes leading and trailing **whitespace**. `strip(chars)` removes leading and trailing characters that are in the string `chars` (not a prefix/suffix). So `"xyxhello".strip("xy")` removes `x` and `y` from both ends, giving `"hello"`.

---

## Q5. (Medium) Why are strings immutable? What if you need to build a long string from many parts?

**Answer:**  
Strings are immutable so they can be hashed, used as dict keys, and shared safely. To build a long string from many parts, use **list.append()** and then **`str.join(list)`** — this is O(n) instead of repeated `+=` which can be O(n²) due to creating new strings each time.

---

## Q6. (Medium) What is the difference between `str.split()` and `str.splitlines()`?

**Answer:**  
`split(sep=None)` splits by whitespace (or by `sep` if given); returns list of tokens. `splitlines()` splits by line boundaries (`\n`, `\r`, `\r\n`, etc.) and returns list of lines; it handles different line endings. Use `splitlines()` for “one line per element.”

---

## Q7. (Medium) In an f-string, how do you display a literal `{` or `}`? How do you format a number to 2 decimal places?

**Answer:**  
Double the brace: `f"{{"` and `f"}}"`. For 2 decimals: `f"{x:.2f}"`. Format spec: `{value:format_spec}`; `.2f` means 2 decimal places, fixed point.

---

## Q8. (Tough) What does `str.encode()` and `bytes.decode()` do? What is the default encoding?

**Answer:**  
`str.encode(encoding='utf-8')` converts a string to **bytes** using the given encoding. `bytes.decode(encoding='utf-8')` converts bytes to **str**. Default is **utf-8**. Use the same encoding on both sides; wrong encoding causes `UnicodeDecodeError` or mojibake.

---

## Q9. (Tough) What is the output and why?

```python
s = "hello"
s[0] = "H"
```

**Answer:**  
**TypeError: 'str' object does not support item assignment.** Strings are immutable; you cannot change a character in place. Create a new string instead, e.g. `s = "H" + s[1:]` or use a list of characters and `''.join()`.

---

## Q10. (Tough) Write a function that capitalizes the first letter of each word (title case) without using `.title()`. Handle multiple spaces.

**Answer:**
```python
def my_title(s: str) -> str:
    return " ".join(word.capitalize() for word in s.split())

# Handles multiple spaces (split() with no arg collapses whitespace):
def my_title(s: str) -> str:
    return " ".join(word.capitalize() for word in s.split())
```
`.split()` with no argument splits on any whitespace and collapses multiple spaces.
