# 19. Regular Expressions

## Q1. (Easy) How do you compile a regex in Python? How do you get a match?

**Answer:**  
**`re.compile(pattern)`** returns a regex object. **`re.match(pattern, s)`** tries to match from the **start** of the string. **`re.search(pattern, s)`** finds the first match **anywhere**. **`re.findall(pattern, s)`** returns all non-overlapping matches. Use the compiled object: **`m = compiled.match(s)`** then **m.group()**, **m.groups()**, etc.

---

## Q2. (Easy) What is the difference between `re.match` and `re.search`?

**Answer:**  
**match** — only matches at the **beginning** of the string (like anchoring with ^). **search** — finds the first match **anywhere** in the string. So **match("c", "abc")** is None; **search("c", "abc")** finds "c".

---

## Q3. (Easy) What does `re.findall` return? What if the pattern has groups?

**Answer:**  
**findall** returns a **list** of all non-overlapping matches. If the pattern has **one or more groups**, it returns a **list of tuples** (one tuple per match; each tuple has the groups). If no groups, list of strings. **finditer** returns an iterator of match objects.

---

## Q4. (Medium) What do `\d`, `\w`, `\s` mean? What about `\D`, `\W`, `\S`?

**Answer:**  
**\d** — digit [0-9]. **\w** — word character [a-zA-Z0-9_] (and Unicode letters/digits in Unicode mode). **\s** — whitespace. Uppercase is negation: **\D** non-digit, **\W** non-word, **\S** non-whitespace.

---

## Q5. (Medium) What is a greedy vs non-greedy match? How do you make a quantifier non-greedy?

**Answer:**  
**Greedy** (e.g. **\***, **+**, **?** after a pattern) matches as much as possible while still allowing the rest of the regex to match. **Non-greedy** (e.g. **\*?**, **+?**, **??**) matches as little as possible. Add **?** after the quantifier: **.*?** instead of **.\***.

---

## Q6. (Medium) What does `re.sub(pattern, repl, string)` do? What if repl is a function?

**Answer:**  
**sub** replaces the **first** or **all** (with **count=0** default) non-overlapping matches of pattern in string. **repl** can be a string (with **\1**, **\g<name>** for groups) or a **function** called with the match object for each match; the return value is the replacement string.

---

## Q7. (Medium) What is a raw string (r"...") and why use it for regex?

**Answer:**  
**r"..."** is a raw string — backslashes are **not** escape characters (except for the quote). So **r"\n"** is backslash + n, not newline. Regex uses many backslashes (**\d**, **\w**, **\1**); raw strings avoid double escaping. So **r"\d+"** instead of **"\\\\d+"**.

---

## Q8. (Tough) Write a regex that matches a simple email (e.g. local@domain.tld). Don’t worry about full RFC compliance.

**Answer:**
```python
import re
# Simple: non-whitespace before @, non-whitespace after
pattern = r'\S+@\S+\.\S+'
# Slightly stricter:
pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
```
Full email validation is complex; use a library or keep it simple per requirements.

---

## Q9. (Tough) What does `(?:...)` do? What is the difference between `(group)` and `(?:non-capturing)`?

**Answer:**  
**`(?:...)`** is a **non-capturing** group. It groups for repetition/alternation but doesn’t create a capture (no **group()** or **\1**). **`(...)`** is a capturing group — it’s stored and can be referenced by **\1**, **group(1)**, or in repl. Use **?:** when you don’t need to capture to improve clarity and sometimes performance.

---

## Q10. (Tough) How do you use a named group? How do you refer to it in sub and in the pattern?

**Answer:**  
**`(?P<name>...)`** defines a named group. In **repl** in sub: **`\g<name>`** or **`\g<1>`**. In the **pattern**: **`(?P=name)`** matches the same text as the named group (backreference). Access in code: **m.group('name')** or **m.group(1)**. Example: **`r'(?P<word>\w+) \s+ (?P=word)'`** matches repeated words.
