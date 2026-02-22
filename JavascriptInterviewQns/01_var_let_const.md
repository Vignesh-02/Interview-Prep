# 1. var, let, and const

## Q1. What are the differences between `var`, `let`, and `const` in terms of scoping?

**Answer:**
- **var**: Function-scoped (or global if declared outside a function). Declaring `var` inside a block (e.g. `if`, `for`) does not create block scope.
- **let**: Block-scoped. Exists only inside the block (including loops and conditionals) where it is declared.
- **const**: Block-scoped like `let`. Must be initialized at declaration and cannot be reassigned (the binding is constant; for objects/arrays the contents can still be mutated).

Understanding the difference between these three is basically the "rite of passage" for modern JavaScript. It usually comes down to where the variable "lives" and whether you can change your mind about its value later.Here are some clear examples to illustrate those definitions.1. var: The Old School (Function Scope)var doesn't care about curly braces {} unless they belong to a function. If you declare it in an if block or a for loop, it "leaks" out to the rest of the function.JavaScriptfunction varExample() {
    if (true) {
        var name = "Gemini";
    }
    console.log(name); // "Gemini" — It escaped the if-block!
}

varExample();
2. let: The Modern Standard (Block Scope)let is much more polite. It stays exactly where you put it. If you declare it inside an if statement or a loop, it stays inside those braces.JavaScriptfunction letExample() {
    if (true) {
        let secret = "I am hidden";
        console.log(secret); // "I am hidden"
    }
    // console.log(secret); // ReferenceError: secret is not defined
}

letExample();
3. const: The Commitment (Block Scope + Immutable Binding)const works like let regarding scope, but you can’t reassign it. However, there is a catch: if the const is an object or array, you can still change the properties inside it.The "No-No":JavaScriptconst pi = 3.14;
// pi = 3.14159; // TypeError: Assignment to constant variable.
The "Object Loophole":JavaScriptconst user = { name: "Alice" };

// This is fine:
user.name = "Bob"; 

// This is NOT fine (reassigning the whole thing):
// user = { name: "Charlie" }; 

Feature,var,let,const
Scope,Function,Block,Block
Reassignable,Yes,Yes,No
Hoisted,Yes (as undefined),Yes (but inaccessible),Yes (but inaccessible)
Can Re-declare,Yes,No,No

Quick Tip: In modern coding, the general rule of thumb is to use const by default. If you know the value needs to change later (like a counter in a loop), use let. Try to avoid var entirely to prevent those "leaky" variable bugs!
---

## Q2. Explain hoisting for `var` vs `let`/`const`. What is the Temporal Dead Zone (TDZ)?

**Answer:**
- **var**: Declarations are hoisted to the top of their scope and initialized with `undefined`. You can use the variable before the line it’s declared on (it will be `undefined`).
- **let** and **const**: Also hoisted in terms of scope, but not initialized. Accessing them before their declaration throws a **ReferenceError** because they are in the **Temporal Dead Zone** (TDZ)—the region from the start of the block until the declaration is executed.

```javascript
console.log(a); // undefined (var is hoisted and initialized)
var a = 1;

console.log(b); // ReferenceError: Cannot access 'b' before initialization
let b = 2;
```

Think of hoisting as the JavaScript engine doing a "pre-scan" of your code. Before it runs a single line, it looks for all variable declarations and moves them to the top of their respective scopes in memory.

However, how it handles that move depends entirely on the keyword you used.

1. var: The "Half-Finished" Move
When you use var, the engine moves the declaration to the top and immediately gives it a default value of undefined. It’s like a waiter putting an empty plate on your table before you've even ordered—the plate is there, but there’s no food on it yet.

JavaScript
console.log(snack); // Output: undefined
var snack = "Cookie"; 
console.log(snack); // Output: "Cookie"
What the engine actually sees:

JavaScript
var snack;          // Declaration is hoisted and initialized to undefined
console.log(snack); // Works, but it's empty
snack = "Cookie";   // Assignment stays where it was
2. let & const: The "Blackout" (TDZ)
These are also hoisted, but with a major catch: they are not initialized. They exist in memory, but the engine forbids you from touching them until it reaches the line where you actually declared them.

The space between the start of the block and the declaration line is the Temporal Dead Zone (TDZ).

JavaScript
{
    // --- START OF BLOCK ---
    // This area is the TDZ for 'price'
    // console.log(price); // ReferenceError! (The TDZ is active)
    
    let price = 100;    // <--- TDZ ENDS HERE
    
    console.log(price); // Output: 100
}

Step,var,let / const
1. Declaration,Hoisted to top of scope,Hoisted to top of scope
2. Initialization,Automatically set to undefined,Remains uninitialized
3. Accessing early,Returns undefined,Throws ReferenceError
4. Execution line,Assigned the actual value,Initialized & assigned value

---

## Q3. Can you redeclare `var`, `let`, and `const` in the same scope?

**Answer:**
- **var**: Yes. Redeclaring `var x` in the same scope is allowed and just refers to the same variable.
- **let** and **const**: No. Redeclaring in the same scope causes a **SyntaxError**.

```javascript
var x = 1;
var x = 2; // OK

let y = 1;
let y = 2; // SyntaxError: Identifier 'y' has already been declared
```

---

## Q4. Predict the output of this loop using `var` vs `let`.

**Question:**
```javascript
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
```

**Answer:** It logs `3`, `3`, `3`.  
`var i` is function/global scoped, so there is only one `i`. By the time the timeouts run, the loop has finished and `i` is 3.

**With let:**
```javascript
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
```
Output: `0`, `1`, `2`. Each iteration has its own block-scoped `i` (a new binding per iteration).

Feature,var in a loop,let in a loop
Number of i variables,One (reused),Multiple (one per loop)
Scope level,Function/Global,Block (the loop body)
Closure behavior,Captures a reference to the shared i,Captures the value of that iteration's i
Final Result,"3, 3, 3","0, 1, 2"

---

## Q5. Is `const` really immutable? Can you change a `const` object or array?

**Answer:**  
`const` makes the **binding** immutable (you cannot reassign the variable). It does **not** make the referenced value immutable. You can mutate properties of an object or elements of an array.

```javascript
const obj = { a: 1 };
obj.a = 2;   // OK
obj = {};    // TypeError: Assignment to constant variable

const arr = [1, 2];
arr.push(3); // OK
arr = [];    // TypeError: Assignment to constant variable
```

---

## Q6. Why does the following throw, and how would you fix it?

**Question:**
```javascript
const PI;
PI = 3.14;
```

**Answer:**  
`const` must be initialized at declaration. You cannot declare it and assign later. Fix: initialize in one statement: `const PI = 3.14;`

If you try to run that code, it will throw a SyntaxError.

Specifically, in most modern browsers and Node.js environments, the error message looks like this:

Uncaught SyntaxError: Missing initializer in const declaration

Why is it a SyntaxError?
Unlike other errors that happen while the code is running (Runtime Errors), a SyntaxError happens during the parsing phase. JavaScript looks at your code and says, "Wait, this violates the fundamental rules of the language."

---

## Q7. In strict mode vs non-strict, what happens when you assign to an undeclared variable?

**Answer:**
- **Non-strict**: Assigning to an undeclared identifier (e.g. `x = 10`) creates a global variable (bad practice).
- **Strict mode** (`'use strict'`): Same assignment throws **ReferenceError**. Use `let`/`const`/`var` to declare variables.

This is one of those "hidden" behaviors in JavaScript that causes massive headaches in large codebases. The difference essentially boils down to whether JavaScript tries to "help" you (and fails) or whether it strictly enforces the rules.

1. Non-Strict Mode: The "Implicit Global"
In non-strict mode, if you assign a value to a variable that hasn't been declared with var, let, or const, JavaScript doesn't panic. Instead, it climbs all the way up the scope chain. When it fails to find the variable anywhere, it says, "I'll just create a new one on the global object for you!"

JavaScript
function looseFunction() {
    message = "Hello"; // No var/let/const!
}

looseFunction();
console.log(window.message); // "Hello" (In a browser)
The Danger: You've just created a "leaky" variable. It now lives forever in the global scope, potentially crashing into other scripts or consuming memory you didn't intend to use.

2. Strict Mode: The "Safety First" Approach
When you add "use strict"; at the top of your file or function, JavaScript stops trying to be "helpful." It treats an assignment to an undeclared variable as a bug.

JavaScript
"use strict";

function strictFunction() {
    message = "Hello"; // ReferenceError: message is not defined
}

strictFunction();
The Error: It throws a ReferenceError. This is actually a good thing! It forces you to be intentional about where your variables live.

---

## Q8. Write a snippet where `let` in a block shadows an outer `let`, and explain the output.

**Answer:**
```javascript
let x = 10;
{
  let x = 20;
  console.log(x); // 20 (inner block scope)
}
console.log(x);   // 10 (outer scope unchanged)
```
The inner `let x` creates a new binding for `x` in the block; it does not reassign the outer `x`.

Great question. This is where the distinction between shadowing (creating a new variable) and reassignment (updating an existing one) becomes really important.

If you remove the keyword let inside the block and just write x = 30, you are no longer "shadowing." Instead, you are reaching out into the outer scope and mutating the original variable.

The "Reassignment" Snippet
JavaScript
let x = 10; 

{
  x = 30;         // No 'let' here! We are talking to the 'x' from line 1.
  console.log(x); // 30
}

console.log(x);   // 30 (The outer 'x' was permanently changed)
Shadowing vs. Reassignment: The Visual Difference
Think of scopes like a series of nested glass boxes.

Shadowing (let x = 20): You place a new post-it note labeled "x" inside the inner box. When you look from inside that box, you see your new note, which hides (shadows) the one outside. When you leave that box, your inner note is destroyed, and the original "x" is still there, untouched.

Reassignment (x = 30): You don't have a note in your inner box. You look through the glass, see the "x" in the outer box, reach out, and erase the 10 to write 30. That change stays even after you leave the inner box.

---

## Q9. What is the output of this code?

**Question:**
```javascript
function test() {
  console.log(a);
  console.log(b);
  var a = 1;
  let b = 2;
}
test();
```

**Answer:**  
First log: `undefined` (var `a` is hoisted and initialized as `undefined`).  
Second log: **ReferenceError: Cannot access 'b' before initialization** (TDZ for `let`).

---

## Q10. When would you choose `const` over `let` in real code?

**Answer:**  
Use **const** by default for every variable that will not be reassigned (e.g. function references, objects, arrays, primitives that don’t change). Use **let** only when you need to reassign (e.g. loop counters, accumulators). Avoid **var** in new code to prevent scope and hoisting surprises.
