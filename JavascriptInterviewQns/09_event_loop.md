# 9. Event Loop

## Q1. What is the event loop and why does JavaScript need it?

**Answer:**  
JavaScript is single-threaded: one call stack executes code. The **event loop** is the mechanism that takes tasks from the task queues and pushes them onto the call stack when the stack is empty. It allows the engine to handle I/O, timers, and UI events without blocking, by deferring work to queues and running it when the current code finishes.

---

## Q2. What are the call stack, task queue (macrotask), and microtask queue?

**Answer:**
- **Call stack**: Where the runtime executes code. One function runs at a time; when it returns, the next frame runs.
- **Task queue (macrotask)**: Callbacks for `setTimeout`, `setInterval`, I/O, UI events. One task runs per event loop turn (after the current script and microtasks).
- **Microtask queue**: Callbacks for Promises (then/catch/finally), `queueMicrotask`, and in browsers `MutationObserver`. All ready microtasks run after the current script and before the next macrotask.

---

## Q3. In what order are tasks and microtasks executed?

**Answer:**  
(1) Run one macrotask (e.g. script or a timer callback). (2) Run **all** microtasks that are currently queued. (3) Optionally render (browser). (4) Pick the next macrotask and repeat. So microtasks always run before the next macrotask; they can “starve” macrotasks if you keep queuing microtasks.

---

## Q4. Predict the output.

**Question:**
```javascript
console.log(1);
setTimeout(() => console.log(2), 0);
Promise.resolve().then(() => console.log(3));
console.log(4);
```

**Answer:** **1**, **4**, **3**, **2**. Sync code runs first (1, 4). Then microtasks run (3 from the promise). Then the next macrotask runs the setTimeout callback (2).

---

## Q5. What is the output?

**Question:**
```javascript
setTimeout(() => console.log('A'), 0);
Promise.resolve()
  .then(() => console.log('B'))
  .then(() => console.log('C'));
console.log('D');
```

**Answer:** **D**, **B**, **C**, **A**. D is sync. Then all microtasks: first then logs B and returns a promise; its then logs C. Then the setTimeout (macrotask) runs and logs A.

---

## Q6. How does `setTimeout(fn, 0)` differ from `queueMicrotask(fn)`?

**Answer:**  
`setTimeout(fn, 0)` schedules `fn` as a **macrotask**; it runs after the current script and after **all** microtasks. `queueMicrotask(fn)` schedules `fn` as a **microtask**; it runs after the current script and before the next macrotask. So microtasks run earlier in the same “round” of the event loop.

---

## Q7. What can happen if you add microtasks indefinitely inside a microtask?

**Answer:**  
The microtask queue would never empty. The event loop would keep running microtasks and never move on to the next macrotask (e.g. timers, I/O, UI). The UI can freeze and other callbacks get delayed. So avoid infinite or very long microtask chains.

---

## Q8. (Tricky) Predict the order of logs.

**Question:**
```javascript
async function async1() {
  console.log('async1 start');
  await async2();
  console.log('async1 end');
}
async function async2() {
  console.log('async2');
}
console.log('script start');
setTimeout(() => console.log('setTimeout'), 0);
async1();
new Promise((resolve) => {
  console.log('promise1');
  resolve();
}).then(() => console.log('promise2'));
console.log('script end');
```

**Answer:**  
script start → async1 start → async2 → promise1 → script end → async1 end → promise2 → setTimeout.  
Reason: `await async2()` runs async2 (sync), then the rest of async1 is scheduled as a microtask. The Promise executor runs (promise1), then its then is a microtask. After “script end”, microtasks: “async1 end”, then “promise2”. Then macrotask: “setTimeout”.

---

## Q9. What is the difference between setInterval and recursive setTimeout for repeating work?

**Answer:**  
`setInterval` schedules the next run at a fixed delay from the *start* of the previous run, so if the callback takes longer than the interval, runs can pile up or fire back-to-back. **Recursive setTimeout** (calling `setTimeout` again at the end of the callback) schedules the next run after the previous run *finishes*, so the delay is between the end of one run and the start of the next. Recursive setTimeout is often better for reliable spacing.

---

## Q10. In Node.js, how does the event loop differ from the browser?

**Answer:**  
Node’s event loop has multiple phases (timers, I/O callbacks, idle/prepare, poll, check, close). Timers (setTimeout/setInterval) run in the timers phase; setImmediate runs in the check phase; I/O callbacks and the poll phase handle network/file I/O. Microtasks (promises, process.nextTick) still run between phases; `process.nextTick` runs before other microtasks. So the ordering of “setTimeout vs setImmediate” and “nextTick vs promise” can differ from the browser.
