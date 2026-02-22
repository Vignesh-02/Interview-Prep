# 3. == vs === and Type Coercion

## Q1. What is the difference between `==` and `===`?

**Answer:**
- **`==` (loose equality)**: Compares values after applying type coercion. Converts operands to a common type before comparing (e.g. `'5' == 5` is `true`).
- **`===` (strict equality)**: Compares without coercion. Returns `true` only if both value and type are the same. `'5' === 5` is `false`.

---

## Q2. What is the output of each comparison?

**Question:**
```javascript
console.log([] == false);
console.log([] == ![]);
console.log(null == undefined);
```

**Answer:**
- `[] == false`: `[]` is coerced to primitive: `''`. Then `'' == false` → `''` coerced to number `0`, `false` → `0`. So `0 == 0` → **true**.
- `[] == ![]`: `![]` is `false`. So `[] == false`. Same as above: `'' == 0` → **true**.
- `null == undefined`: Per spec, **true** (they only equal each other with `==`).

---

## Q3. Explain how type coercion works when using `==` with different types.

**Answer:**  
If types differ, the engine converts one or both operands (often to number or string). Rules include: when comparing number and string, string is converted to number; when comparing with boolean, boolean is converted to number (true→1, false→0); objects are converted to primitives (often via `valueOf`/`toString`). `null` and `undefined` are equal only to each other with `==`.

---

## Q4. What does this output?

**Question:**
```javascript
console.log('0' == false);
console.log('0' === false);
console.log(0 == false);
console.log(0 === false);
```

**Answer:**
- `'0' == false`: false → 0, then `'0'` → 0. `0 == 0` → **true**.
- `'0' === false`: different types → **false**.
- `0 == false`: false → 0 → **true**.
- `0 === false`: number vs boolean → **false**.

---

## Q5. Why does `NaN === NaN` evaluate to false? How do you check for NaN?

**Answer:**  
By design in IEEE 754, NaN is not equal to itself. Use **`Number.isNaN(x)`** to check if a value is NaN (or `x !== x` as a trick). Avoid `isNaN(x)` for strict checks because it coerces (e.g. `isNaN('hello')` is true).

---

## Q6. What is the result of `Object.is(NaN, NaN)` and `Object.is(0, -0)`?

**Answer:**
- `Object.is(NaN, NaN)` → **true** (unlike `===`).
- `Object.is(0, -0)` → **false** (0 and -0 are distinct; `===` treats them equal).

`Object.is` uses “SameValue” comparison: no coercion, and distinguishes NaN and ±0.

---

## Q7. Predict the output.

**Question:**
```javascript
console.log(true + true + true);
console.log('5' - 3);
console.log('5' + 3);
```

**Answer:**
- `true + true + true`: booleans coerce to numbers (1). `1 + 1 + 1` → **3**.
- `'5' - 3`: `-` triggers numeric conversion. `5 - 3` → **2**.
- `'5' + 3`: `+` with string does string concatenation. `'5' + '3'` → **'53'**.

---

## Q8. What does `[] + {}` and `{} + []` return? (Tricky)

**Answer:**
- `[] + {}`: `[]` → `''`, `{}` → `'[object Object]'`. `'' + '[object Object]'` → **'[object Object]'**.
- `{} + []`: In many environments, `{}` is parsed as an empty block, not an object. So it becomes `+ []`. Unary `+` converts `[]` to number: `0`. Result **0**. (In other contexts it might be string concatenation; context and parser matter.)

---

## Q9. When should you use `==` vs `===` in production code?

**Answer:**  
Prefer **`===`** (and `!==`) by default. It avoids subtle bugs from coercion. Use `==` only when you intentionally want coercion (e.g. `value == null` to match both `null` and `undefined` in one check).

---

## Q10. What is the output of this chain?

**Question:**
```javascript
const a = { valueOf: () => 1 };
const b = { valueOf: () => 2 };
console.log(a + b);
console.log(a == 1);
console.log(a === 1);
```

**Answer:**
- `a + b`: Both objects coerced to number via `valueOf()` → 1 + 2 → **3**.
- `a == 1`: `a` coerced to number 1 → **true**.
- `a === 1`: object vs number, no coercion → **false**.
