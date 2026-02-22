# 4. null vs undefined

## Q1. What is the difference between `null` and `undefined`?

**Answer:**
- **undefined**: A variable has been declared but not assigned a value, or a function has no explicit return, or an optional parameter was not passed. It is the default “empty” value for uninitialized bindings.
- **null**: An intentional “no value” or “empty object” placeholder. You assign `null` when you want to express “no value” by design.

---

## Q2. In what situations do you get `undefined`?

**Answer:**
- Declared variable not initialized: `let x; console.log(x)`.
- Function with no return or bare `return`: `function f() {} f()`.
- Missing argument: `function f(a) { return a; } f()`.
- Accessing non-existent object property: `const o = {}; o.foo`.
- Array index out of range: `[1,2][10]`.
- Void operator: `void 0` → `undefined`.

---

## Q3. What is the type of `null` and `undefined`?

**Answer:**  
`typeof undefined` → `'undefined'`.  
`typeof null` → `'object'` (historic bug; null is not an object). Use `value === null` to check for null.

---


## Q4. What does `undefined == null` and `undefined === null` return?

**Answer:**  
`undefined == null` → **true** (they are the only two values that are equal with `==`).  
`undefined === null` → **false** (different types).

---

## Q5. How do you safely check for “null or undefined” in one condition?

**Answer:**
- Loose: `value == null` (true for both `null` and `undefined`).
- Explicit: `value === null || value === undefined`.
- Optional chaining / nullish: Use `value ?? default` when you only care about null/undefined.

---

## Q6. What is the output?

**Question:**
```javascript
function test(a, b) {
  console.log(a, b);
}
test(1);
```

**Answer:**  
`1 undefined`. First parameter `a` is `1`; second parameter `b` was not passed, so it is `undefined`.

---

## Q7. What does the following return?

**Question:**
```javascript
const obj = { a: 1, b: undefined, c: null };
console.log(obj.b);
console.log(obj.c);
console.log('b' in obj);
console.log('c' in obj);
```

**Answer:**
- `obj.b` → **undefined** (property exists, value is undefined).
- `obj.c` → **null**.
- `'b' in obj` → **true** (key exists).
- `'c' in obj` → **true** (key exists).

So “missing” vs “present but undefined” can be distinguished with `in` or `Object.hasOwn()`.

---

## Q8. What is the Nullish Coalescing operator `??`? How is it different from `||`?

**Answer:**  
`??` returns the right-hand side only when the left-hand side is **null** or **undefined**.  
`||` returns the right-hand side when the left-hand side is any **falsy** value (false, 0, `''`, NaN, null, undefined). So `0 ?? 10` is `0`, while `0 || 10` is `10`.

---

Checking for "nullish" values is a classic JavaScript task. Because null and undefined are technically different types but often represent the same "absence of a value," knowing how the engine compares them is key.

Here is the breakdown of why those methods work and which one you should pick.

1. The "Loose Equality" Shortcut (== null)
This is one of the rare cases where even strict-mode advocates use loose equality. In JavaScript, null and undefined are loosely equal to each other, but not to anything else (like 0, false, or "").

JavaScript
let a = null;
let b = undefined;
let c = 0;

console.log(a == null); // true
console.log(b == null); // true
console.log(c == null); // false
2. The Modern Standard: Nullish Coalescing (??)
If your goal isn't just to check but to provide a fallback, use the ?? operator. This is safer than the logical OR (||) because it only triggers for null or undefined.

Operator	Triggers on...	Example 0 ?? 10	Example "" ?? "Hi"
**`		` (OR)**	All "falsy" values (0, "", false, null, undefined)
?? (Nullish)	Only null or undefined	0	""
3. Optional Chaining (?.)
If you are checking for null/undefined nested deep within an object, don't use an if statement at all. Use optional chaining to prevent the dreaded Uncaught TypeError: Cannot read property of undefined.

JavaScript
const user = { profile: null };

// Safe way:
console.log(user?.profile?.name); // undefined (doesn't crash!)

// Old way:
// console.log(user.profile.name); // TypeError!
Summary Table: Which to use?
Use Case	Recommended Syntax
Logic Check	if (value == null)
Variable Fallback	const x = value ?? "Default"
Deep Object Access	const x = user?.settings?.theme
Strict Specificity	if (value === undefined)
A Word on Truthy/Falsy
Remember that if (!value) is the most common check, but it is dangerous. If your value is 0 (a valid number), if (!value) will treat it as "empty" because 0 is falsy.

Pro-Tip: If you are dealing with numbers or strings where 0 or "" are valid data, always use == null or ?? to ensure you aren't accidentally deleting your data!

Does this help you see why ?? has largely replaced || for setting default values?


## Q9. Predict the output.

**Question:**
```javascript
let x;
console.log(x);
x = null;
console.log(x);
console.log(typeof x);
```

**Answer:**
- First log: **undefined** (declared but not assigned).
- Second log: **null** (after assignment).
- `typeof x`: **'object'** (typeof null quirk).

---

## Q10. When would you explicitly assign `null` vs leave a variable `undefined`?

**Answer:**  
Use **null** when you want to signal “no value” or “reset” (e.g. clearing a reference, optional result that can be “none”). Use **undefined** when something hasn’t been set yet or is optional and omitted. APIs often use `null` for “no result” and leave `undefined` for “not provided.”


Optional Chaining (?.)If you are checking for null/undefined nested deep within an object, don't use an if statement at all. Use optional chaining to prevent the dreaded Uncaught TypeError: Cannot read property of undefined.JavaScriptconst user = { profile: null };

// Safe way:
console.log(user?.profile?.name); // undefined (doesn't crash!)

// Old way:
// console.log(user.profile.name); // TypeError!
Summary Table: Which to use?Use CaseRecommended SyntaxLogic Checkif (value == null)Variable Fallbackconst x = value ?? "Default"Deep Object Accessconst x = user?.settings?.themeStrict Specificityif (value === undefined)A Word on Truthy/FalsyRemember that if (!value) is the most common check, but it is dangerous. If your value is 0 (a valid number), if (!value) will treat it as "empty" because 0 is falsy.Pro-Tip: If you are dealing with numbers or strings where 0 or "" are valid data, always use == null or ?? to ensure you aren't accidentally deleting your data!