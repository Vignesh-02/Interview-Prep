# 14. Debounce and Throttle

## Q1. What is debouncing and when would you use it?

**Answer:**  
**Debounce** delays running a function until after a period of inactivity. If the action is triggered again before that period ends, the timer resets. Use it for: search input (wait until user stops typing), window resize (run logic once resize stops), form validation on blur/after typing stops.

---

## Q2. Implement debounce: the function runs only after `wait` ms of no calls.

**Answer:**
```javascript
function debounce(fn, wait) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), wait);
  };
}
```

---

## Q3. What is throttling and how is it different from debounce?

**Answer:**  
**Throttle** ensures the function runs at most once per time window. So if you throttle to 100ms, the first call runs immediately (or after 100ms), and further calls within 100ms are ignored until the window passes. Difference: debounce waits for “quiet”; throttle runs at a steady rate. Use throttle for scroll/resize handlers, button clicks to prevent double submit.

---

## Q4. Implement throttle (leading edge: run on first call, then ignore until wait passes).

**Answer:**
```javascript
function throttle(fn, wait) {
  let last = 0;
  return function (...args) {
    const now = Date.now();
    if (now - last >= wait) {
      last = now;
      return fn.apply(this, args);
    }
  };
}
```

---

## Q5. Implement throttle with trailing edge: run once at the end of the wait window if there was a call.

**Answer:**
```javascript
function throttleTrailing(fn, wait) {
  let timeoutId = null;
  return function (...args) {
    if (timeoutId === null) {
      timeoutId = setTimeout(() => {
        fn.apply(this, args);
        timeoutId = null;
      }, wait);
    }
  };
}
```

---

## Q6. Debounce with immediate option: run on first call, then debounce subsequent calls.

**Answer:**
```javascript
function debounceImmediate(fn, wait, immediate = false) {
  let timeoutId;
  return function (...args) {
    const callNow = immediate && !timeoutId;
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      timeoutId = null;
      if (!immediate) fn.apply(this, args);
    }, wait);
    if (callNow) fn.apply(this, args);
  };
}
```

---

## Q7. Why use `fn.apply(this, args)` instead of `fn(args)` in debounce/throttle?

**Answer:**  
So that when the debounced/throttled function is called as a method (e.g. `obj.handleScroll()`), the original `fn` still runs with the correct `this` (obj). Passing `args` with spread preserves the exact arguments. Without that, `this` would be wrong (or undefined in strict mode) and arguments could be wrong.

---

## Q8. Use debounce for a search input: log the search term 300ms after user stops typing.

**Answer:**
```javascript
const logSearch = debounce((term) => console.log('Search:', term), 300);
document.querySelector('input').addEventListener('input', (e) => {
  logSearch(e.target.value);
});
```

---

## Q9. Throttle scroll events so a handler runs at most every 100ms. Write the handler registration.

**Answer:**
```javascript
const throttledScroll = throttle(() => {
  console.log('Scroll position:', window.scrollY);
}, 100);
window.addEventListener('scroll', throttledScroll);
```

---

## Q10. (Tricky) Implement a debounce that supports cancellation (e.g. `cancel()` method).

**Answer:**
```javascript
function debounceWithCancel(fn, wait) {
  let timeoutId;
  const debounced = function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), wait);
  };
  debounced.cancel = function () {
    clearTimeout(timeoutId);
    timeoutId = null;
  };
  return debounced;
}
```
