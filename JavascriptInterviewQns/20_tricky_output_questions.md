# 20. Tricky Output & Edge Cases

## Q1. What is the output?

**Question:**
```javascript
console.log(typeof null);
console.log(typeof undefined);
console.log(null === undefined);
console.log(null == undefined);
```

**Answer:**  
`'object'` (historic bug), `'undefined'`, **false**, **true**.

---

## Q2. What does this log?

**Question:**
```javascript
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
```

**Answer:** **3**, **3**, **3**. One shared `var i`; by the time callbacks run, loop has finished and `i` is 3.

---

## Q3. Predict the output.

**Question:**
```javascript
console.log(1 + '2' + '2');
console.log(1 + +'2' + '2');
console.log(1 + -'1' + '2');
```

**Answer:**  
`'122'` (string concat).  
`1 + +'2'` → 3, then `3 + '2'` → `'32'`.  
`1 + -'1'` → 0, then `0 + '2'` → `'02'`.

---

## Q4. What is the result?

**Question:**
```javascript
const arr = [10, 12, 15, 21];
for (var i = 0; i < arr.length; i++) {
  setTimeout(function () {
    console.log('Index: ' + i + ', value: ' + arr[i]);
  }, 1000);
}
```

**Answer:**  
After 1s: four logs of **"Index: 4, value: undefined"**. `i` is 4 and `arr[4]` is undefined. Fix with `let i` or IIFE to capture `i`.

---

## Q5. What gets logged?

**Question:**
```javascript
(function () {
  var a = (b = 3);
})();
console.log(typeof a);
console.log(typeof b);
```

**Answer:**  
`a` is function-scoped (inside the IIFE) → **'undefined'** in global. `b = 3` assigns to an implicit global (non-strict) → **'number'**. So `typeof a === 'undefined'`, `typeof b === 'number'`.

---

## Q6. Output of this?

**Question:**
```javascript
var x = 1;
function foo() {
  console.log(x);
  var x = 2;
  console.log(x);
}
foo();
```

**Answer:** **undefined**, then **2**. First `x` is the hoisted local `var x` (not yet assigned). Second is after assignment.

---

## Q7. What is the result?

**Question:**
```javascript
console.log([] + []);
console.log([] + {});
console.log(true + true);
console.log('5' - '2');
```

**Answer:**  
`'' + ''` → **''**.  
`'' + '[object Object]'` → **'[object Object]'**.  
**2**.  
**3** (numeric coercion).

---

## Q8. (Tricky) What does this output?

**Question:**
```javascript
function foo() {
  return
  {
    bar: 1
  };
}
console.log(foo());
```

**Answer:** **undefined.** Automatic semicolon insertion: return is followed by newline, so JS inserts `;` and the function returns undefined. The object literal is never reached. Fix: put `{` on the same line as `return`.

---

## Q9. Predict the output.

**Question:**
```javascript
var a = 1;
function b() {
  a = 10;
  return;
  function a() {}
}
b();
console.log(a);
```

**Answer:** **1.** The inner `function a()` is hoisted inside `b`, so the local `a` is the function. The assignment `a = 10` updates that local, not the outer `a`. So global `a` stays 1.

---

## Q10. (Very tricky) What is logged?

**Question:**
```javascript
const obj = {
  prop: 'value',
  method: function () {
    return this.prop;
  }
};
const { method } = obj;
console.log(method());
console.log(obj.method());
```

**Answer:**  
First: **undefined** (or error in strict). `method` is called without a receiver, so `this` is global/undefined; `this.prop` is undefined.  
Second: **'value'**. Called as `obj.method()`, so `this` is obj.

---

## Bonus: More tricky ones

**A.**
```javascript
Number("")      // 0
Number("  ")    // 0
parseInt("")    // NaN
```

**B.**
```javascript
[] == false   // true ([] → '' → 0, false → 0)
[] == true    // false
![] == false  // true (![] is false)
```

**C.**
```javascript
(function (x) {
  return (function (y) {
    console.log(x);
  })(2);
})(1);
// logs 1 (closure over x)
```

Practicing these concepts will make you confident in interviews. Good luck!
