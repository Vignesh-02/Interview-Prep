# 18. Error Handling

## Q1. What is the difference between `throw` and `return` in a function?

**Answer:**  
`return` exits the function and returns a value to the caller; execution continues in the caller. `throw` creates an exception and exits the function (and possibly callers) until a `try/catch` (or the host) handles it. Unhandled exceptions terminate the current run (or crash the process).

---

## Q2. What happens if you don’t catch a rejected Promise?

**Answer:**  
The rejection becomes an “unhandled rejection.” In browsers/Node you may get a warning or error in the console; in Node, unhandled rejections can eventually terminate the process. Always attach `.catch()` or use try/catch with async/await, or use a global `unhandledrejection` handler for logging.

---

## Q3. What does the `finally` block do in try/catch? When does it run?

**Answer:**  
`finally` runs after the try (and catch if present), whether the try completed normally or threw. It runs before the function returns or before the exception propagates. Use it for cleanup (e.g. closing resources). If `finally` throws or returns, that overrides the previous completion or exception.

---

## Q4. How do you create a custom Error type?

**Answer:**
```javascript
class CustomError extends Error {
  constructor(message, code) {
    super(message);
    this.name = 'CustomError';
    this.code = code;
    Object.setPrototypeOf(this, CustomError.prototype);
  }
}
```
Setting the prototype ensures `instanceof CustomError` works after transpilation. Then use: `throw new CustomError('msg', 'CODE');`

---

## Q5. What is the output?

**Question:**
```javascript
try {
  throw new Error('a');
} catch (e) {
  console.log(e.message);
  throw new Error('b');
} finally {
  console.log('finally');
}
console.log('after');
```

**Answer:**  
Logs **'a'**, then **'finally'**. The throw of `Error('b')` happens after the catch runs; `finally` still runs. Then the new error propagates, so **'after'** is never logged (exception continues up).

---

## Q6. Is it possible to have `try` without `catch`? Without `finally`?

**Answer:**  
Yes. You can have `try { } finally { }` (no catch)—exceptions still propagate after finally. You can have `try { } catch { }` without finally. So: try is required; catch and/or finally are optional (at least one of them usually present).

---

## Q7. What does `Error.stack` contain and when is it set?

**Answer:**  
`Error.stack` is a string (often multi-line) showing the call stack at the time the error was created. Format is implementation-dependent. It’s set when the Error object is constructed; it’s not updated if you re-throw.

---

## Q8. In async/await, if you `throw` in a try block, does the catch block run?

**Answer:**  
Yes. Throwing (or a rejected promise from `await`) inside try is caught by the corresponding catch. So you can use try/catch for both sync throws and async rejections when using await.

---

## Q9. What is the difference between `throw e` and `throw new Error(e)` after catching?

**Answer:**  
`throw e` re-throws the same error, preserving stack and type. `throw new Error(e)` wraps it in a new Error; the original might be in `cause` or the message, but you lose the original type and can alter the stack. Prefer re-throwing the same error unless you intentionally want to wrap.

---

## Q10. (Tricky) What gets logged?

**Question:**
```javascript
function run() {
  try {
    return 1;
  } finally {
    return 2;
  }
}
console.log(run());
```

**Answer:** **2.** When `finally` runs and does `return 2`, that return overrides the previous `return 1`. So the function returns 2. Using return in `finally` is allowed but can be surprising; avoid it when possible.
