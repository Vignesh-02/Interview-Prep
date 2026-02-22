# 11. Event Propagation (Bubbling and Capturing)

## Q1. What is event bubbling?

**Answer:**  
**Bubbling** is the phase where an event moves from the target element up through its ancestors toward the document root. So after the target handles the event, the same event fires on the parent, then the grandparent, and so on. Most events bubble (e.g. click); some do not (e.g. focus, blur).

---

## Q2. What is event capturing?

**Answer:**  
**Capturing** is the phase where the event travels from the root down to the target. So the outermost ancestor gets the event first, then its child, until the target. To listen in the capture phase, use `addEventListener(..., true)` or `{ capture: true }`. The order is: capture (root → target) → target → bubble (target → root).

---

## Q3. What is the difference between `event.stopPropagation()` and `event.preventDefault()`?

**Answer:**  
- **stopPropagation()**: Stops the event from continuing to other elements in the capture or bubble phase. Only the current handler runs; parents or children (depending on phase) won’t receive the event.
- **preventDefault()**: Prevents the browser’s default action for the event (e.g. following a link, submitting a form). It does not stop propagation. Use when you want to handle the event in JS but not trigger the default behavior.

---

## Q4. How do you attach a listener that runs in the capture phase?

**Answer:**  
Pass `true` as the third argument, or use an options object with `capture: true`:

```javascript
element.addEventListener('click', handler, true);
// or
element.addEventListener('click', handler, { capture: true });
```

---

## Q5. What is event delegation and why is it useful?

**Answer:**  
**Event delegation** is putting a single listener on a parent (or document) and handling events for child elements by checking `event.target`. Benefits: fewer listeners (better performance and memory), and it works for dynamically added children without re-attaching listeners.

Example: one listener on a list that handles clicks on any list item.

---

## Q6. Write a simple event delegation handler for a list where each item has a data-id.

**Answer:**
```javascript
document.getElementById('list').addEventListener('click', (e) => {
  const item = e.target.closest('[data-id]');
  if (!item) return;
  e.preventDefault();
  console.log('Clicked id:', item.dataset.id);
});
```

---

## Q7. What is `event.target` vs `event.currentTarget`?

**Answer:**  
- **event.target**: The element that actually triggered the event (the one the user clicked, etc.). It doesn’t change as the event propagates.
- **event.currentTarget**: The element that the listener is attached to. It’s the same as `this` in a non-arrow handler. So in a delegated handler on a parent, `target` might be a child, `currentTarget` is the parent.

---

## Q8. Can you stop only bubbling but still let other handlers on the same element run?

**Answer:**  
**stopPropagation()** stops the event from reaching other *elements* (ancestors/descendants). It does not remove other listeners on the *same* element; those are both on the same target and will still run in registration order. To prevent other listeners on the same element from running, you’d need **stopImmediatePropagation()**.

---

## Q9. What does `stopImmediatePropagation()` do?

**Answer:**  
It stops the event from propagating to other elements **and** prevents any other listeners on the **same element** for the same event from being called. So only the current listener runs; other listeners on that element and all propagation are skipped.

---

## Q10. (Tricky) If you call both `preventDefault()` and `stopPropagation()` in a link’s click handler, what happens when the user clicks the link?

**Answer:**  
The browser’s default action (navigating to the href) is prevented, and the event does not bubble to parent elements. So: no navigation, and parent click handlers don’t run for that click. The link’s own handler still runs (it already did); anything that depends on the event reaching parents won’t see it.
