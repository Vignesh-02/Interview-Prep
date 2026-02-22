# 30. Observables & Reactive Patterns (Senior)

## Q1. What is an Observable (in the RxJS / TC39 sense) and how does it differ from a Promise?

**Answer:**  
An **Observable** represents a stream of values over time. You subscribe to it; it can emit zero, one, or many values (and optionally complete or error). **Promise** resolves once with a single value (or rejects). Observables are lazy (no work until subscribe), cancellable (subscription.unsubscribe()), and composable (operators like map, filter, merge). Promises are eager and not cancellable (by spec).

---

## Q2. Implement a minimal Observable: subscribe(fn) and a way to push values. No operators.

**Answer:**
```javascript
function createObservable(produce) {
  return {
    subscribe(observer) {
      const next = typeof observer === 'function' ? observer : observer.next;
      const unsubscribe = produce({
        next: (v) => next?.(v),
        error: (e) => observer.error?.(e),
        complete: () => observer.complete?.()
      });
      return {
        unsubscribe: () => (typeof unsubscribe === 'function' ? unsubscribe() : undefined)
      };
    }
  };
}
// usage: createObservable((sub) => { sub.next(1); sub.next(2); sub.complete(); })
```

---

## Q3. What does “backpressure” mean in streams/observables and how can you handle it?

**Answer:**  
**Backpressure** is when a producer is faster than the consumer; without handling it, buffers grow and memory can spike. Handling: (1) **Pull-based**: Consumer requests the next value (e.g. iterator, async iterator). (2) **Bounded buffers**: Drop or block when buffer is full. (3) **Operators**: In Rx, use operators that slow production (e.g. buffer, sample, or consumer-controlled pace). (4) **Cancel or pause**: Unsubscribe or signal the producer to slow down.

---

## Q4. What is the difference between hot and cold Observables?

**Answer:**  
**Cold**: Each subscriber triggers the producer; each gets its own stream (e.g. HTTP request per subscribe). **Hot**: Producer runs regardless of subscribers; all subscribers share the same stream (e.g. mouse events). You can make a cold observable “hot” by multicasting (share, publish) so one subscription drives the source and others receive the same values.

---

## Q5. Implement a simple Subject: an Observable that you can call .next(value) on to push to subscribers.

**Answer:**
```javascript
function createSubject() {
  const subscribers = new Set();
  return {
    subscribe(observer) {
      subscribers.add(observer);
      return {
        unsubscribe() {
          subscribers.delete(observer);
        }
      };
    },
    next(value) {
      subscribers.forEach((obs) => obs.next?.(value));
    },
    error(e) {
      subscribers.forEach((obs) => obs.error?.(e));
      subscribers.clear();
    },
    complete() {
      subscribers.forEach((obs) => obs.complete?.());
      subscribers.clear();
    }
  };
}
```

---

## Q6. When would you use an Observable over async/await or Promises?

**Answer:**  
Use Observables when: (1) **Multiple values** over time (events, WebSocket, intervals). (2) **Cancellation** is needed (abort long-running or repeatable work). (3) **Composition** of streams (merge, switchMap, debounce across async sources). (4) **Backpressure** or pacing matters. Use Promises/async-await when: single async result, simple flow, and no need for cancellation or stream composition.

---

## Q7. What does “switchMap” do (conceptually) and when is it useful?

**Answer:**  
**switchMap** (or “switch”) subscribes to an inner Observable for each outer value; when a new outer value arrives, it **unsubscribes** from the previous inner and subscribes to the new one. Useful for **search-as-you-type**: each keystroke triggers a request; you only care about the latest request’s result, so you cancel previous ones. Prevents stale responses from overwriting newer ones.

---

## Q8. How would you debounce user input in a simple event stream (without Rx)?

**Answer:**  
Keep a timer; on each event, clear the previous timer and set a new one that fires the handler after `delay` ms. Only the last event in a burst triggers the handler:

```javascript
function debounce(fn, delay) {
  let id;
  return (...args) => {
    clearTimeout(id);
    id = setTimeout(() => fn(...args), delay);
  };
}
input.addEventListener('input', debounce((e) => fetchSuggestions(e.target.value), 300));
```

---

## Q9. What is the Observer pattern vs Pub/Sub? How do they relate to Observables?

**Answer:**  
**Observer**: Subject holds a list of observers and notifies them directly (tight coupling to the subject’s type). **Pub/Sub**: Publishers and subscribers don’t know each other; a broker routes messages by topic/channel. Observables are like a generalized observer: the “subject” is the observable, and subscribers get a subscription; the observable pushes values. Pub/Sub is often used for application events; Observables model a single stream with a well-defined protocol (next/error/complete).

---

## Q10. What are async iterables (async generators) and how do they compare to Observables for async sequences?

**Answer:**  
**Async iterables** (async function*, for await...of): Pull-based; the consumer requests the next value and awaits it. One consumer per iteration; natural for I/O and request/response. **Observables**: Push-based; the producer pushes values; can have many subscribers; good for events and composition. Use async iterables when you want pull, simple consumption, and integration with for-await. Use Observables when you need push, multiple subscribers, or rich operators (e.g. RxJS).
