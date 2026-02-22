# 2. Scope and Hoisting

## Q1. What are global scope, function scope, and block scope in JavaScript?

**Answer:**
- **Global scope**: Variables declared outside any function (or at top level in non-module scripts) are global. They are properties of the global object (`window` in browsers, `global`/`globalThis` in Node).
- **Function scope**: Variables declared with `var` inside a function are visible only inside that function.
- **Block scope**: A block is `{ }` (e.g. `if`, `for`, `while`). Variables declared with `let` or `const` inside a block are visible only inside that block.

---

## Q2. Explain hoisting. What gets hoisted and what doesn’t?

**Answer:**  
Hoisting is the behavior where declarations are treated as if they were moved to the top of their scope before execution.

- **Function declarations**: Fully hoisted (declaration + body). You can call them before the line they’re written on.
- **var**: Declaration is hoisted and initialized with `undefined`.
- **let** / **const**: Declarations are hoisted but not initialized (TDZ until the declaration line).
- **Function expressions** (e.g. `const fn = function () {}`): Only the variable is hoisted (as `undefined` or in TDZ), not the function itself.

Gemini said
When it comes to functions, "hoisting" is the reason why some code works perfectly while other code crashes with a TypeError. The key is how you define the function: as a Declaration or an Expression.

1. Function Declarations: The "VIP" Hoist
Function declarations are the only things in JavaScript that are fully hoisted. Both the name of the function and the actual code inside it (the body) are moved to the top of the scope during the compile phase.

JavaScript
// This works!
greet(); 

function greet() {
  console.log("Hello from the top!");
}
Why? The engine sees the function keyword at the start of the line and allocates memory for the entire block before running the first line of code.

2. Function Expressions with var
When you assign a function to a var, only the variable name is hoisted. It follows the same rule as any other var: it is initialized as undefined.

JavaScript
// console.log(sayHi); // Output: undefined
// sayHi();           // TypeError: sayHi is not a function

var sayHi = function() {
  console.log("Hi!");
};
The Catch: Since sayHi is undefined until the code reaches the assignment line, trying to call it as a function results in a TypeError. You’re basically trying to do undefined().

3. Function Expressions with let and const
These behave exactly like standard let and const variables. They are hoisted to the top of the block, but they are uninitialized. They stay in the Temporal Dead Zone (TDZ) until the execution hits that line.

JavaScript
// boom(); // ReferenceError: Cannot access 'boom' before initialization

const boom = () => {
  console.log("Explosion!");
};
Comparison Summary: Function Hoisting
Type	Syntax	Hoisting Behavior	Result if called early
Declaration	function name() {}	Full (Name + Body)	Works perfectly
var Expression	var name = function() {}	Partial (Name only)	TypeError (is not a function)
let/const Expr	const name = () => {}	None (Stays in TDZ)	ReferenceError

The "Why" Behind the Errors
ReferenceError: "I have no idea what this variable is yet." (Happens with let/const in the TDZ).

TypeError: "I know what this variable is, but it's not a function." (Happens with var because it's currently undefined).

Pro-Tip for Clean Code
Even though function declarations allow you to call functions before they are defined, most modern style guides (like Airbnb or Google) recommend defining functions before you use them. This makes the "flow" of the data much easier for humans to read, even if the machine doesn't care!
---

## Q3. What is the output of this code?

**Question:**
```javascript
console.log(foo());
function foo() {
  return 'hoisted';
}
console.log(bar());
var bar = function () {
  return 'not hoisted';
};
```

**Answer:**  
First `console.log(foo())` prints `'hoisted'` because function declarations are hoisted.  
Second `console.log(bar())` throws **TypeError: bar is not a function** because `bar` is hoisted as `var bar = undefined`; the function is assigned later, so at call time `bar` is still `undefined`.

---

## Q4. What is lexical scope (static scope)?

**Answer:**  
Lexical scope means that the scope of a variable is determined by where it is written in the source code (the “lexical” environment), not by the call stack. JavaScript uses lexical scope: a function’s access to variables is defined by its physical placement in the code, so inner functions can access variables from outer functions.

o understand Lexical Scope, you have to think about "Geography." In JavaScript, where you physically type your function in the file determines what data it can see.It’s called Static Scope because it is determined at "compile time" (when the code is being read by the engine), not at "runtime" (when the functions are being called).1. The "Nested Boxes" ConceptImagine your code as a series of nested folders. A function inside a folder can look out at the files in the parent folders, but a parent folder cannot look into the sub-folders to see their private files.JavaScriptconst globalVar = "I am Global";

function outer() {
  const outerVar = "I am Outer";

  function inner() {
    const innerVar = "I am Inner";
    
    // Inner can see everything "outside" its walls
    console.log(innerVar); // "I am Inner"
    console.log(outerVar); // "I am Outer"
    console.log(globalVar); // "I am Global"
  }

  inner();
}

outer();
2. The Great Distinction: Lexical vs. DynamicMany people get confused because they think scope depends on who calls the function. That is called Dynamic Scope, and it is NOT how JavaScript works.The Test Case:JavaScriptconst name = "Global Name";

function logName() {
  console.log(name); 
}

function wrapper() {
  const name = "Wrapper Name";
  logName(); // Where will logName look for 'name'?
}

wrapper(); 
Output: "Global Name"Why?Even though logName was called inside wrapper, it was written (lexically defined) in the Global Scope. Therefore, its "Outer Environment" is the Global Scope, not the wrapper scope. It doesn't care who calls it; it only cares where it was born.3. How it works in the RAM (The Technical Part)Earlier, we talked about the Environment Record on the Stack. When a function is created, the engine attaches a hidden property to it (internal property called [[Scopes]]).This property acts like a permanent map of all the parent Environment Records that existed at the moment the function was born.When you look for a variable, JavaScript checks the current function's Record.If it’s not there, it uses that map to jump to the parent Record. This is the Scope Chain.Summary of Lexical ScopeFeatureDescriptionWhen it's setDuring the "Creation Phase" (when code is parsed).DirectionInner scopes can look up/out; outer scopes cannot look down/in.StabilityIt never changes, no matter where the function is called from.FoundationThis is the fundamental concept that makes Closures possible.Key Takeaway: If you ever get lost, just look at the indentation of your code. If function B is indented inside function A, function B has access to function A's variables. It’s that simple!

---

## Q5. Predict the output.

**Question:**
```javascript
var x = 1;
function first() {
  console.log(x);
}
function second() {
  var x = 2;
  first();
}
second();
```

**Answer:**  
Output is `1`. `first` is defined in the global scope, so when it runs, it looks up `x` in its lexical scope (global), where `x` is `1`. The `x` inside `second` is not in `first`’s scope chain.

---

## Q6. What is the difference between a function declaration and a function expression in terms of hoisting?

**Answer:**
- **Function declaration** (`function name() {}`): Entire declaration (including body) is hoisted. The function is available from the start of its scope.
- **Function expression** (`var f = function () {}` or `const f = () => {}`): Only the variable binding is hoisted. The function is assigned when that line runs, so you cannot call it before the assignment.

---

## Q7. What does the following code output and why?

**Question:**
```javascript
function outer() {
  var a = 10;
  if (true) {
    var a = 20;
    console.log(a);
  }
  console.log(a);
}
outer();
```

**Answer:**  
Both logs print `20`. `var` is function-scoped, so both `var a` declarations refer to the same variable in `outer`. The inner assignment updates that single `a`.

---

## Q8. How does the scope chain work when resolving a variable?

**Answer:**  
When JavaScript looks up a variable, it first checks the current execution context’s scope. If not found, it goes to the parent lexical environment, and so on until the global scope. This chain of environments is the scope chain. Resolution stops at the first match.

---

## Q9. What is the output?

**Question:**
```javascript
let a = 1;
{
  console.log(a);
  let a = 2;
}
```

**Answer:**  
**ReferenceError: Cannot access 'a' before initialization.** The inner `let a` makes `a` refer to the block-scoped binding. That binding is in the TDZ from the start of the block until the line `let a = 2`, so `console.log(a)` is in the TDZ.

---

## Q10. How would you create a private variable using scope (without classes)?

**Answer:**  
Use a function scope and return an object or methods that close over the variable:

```javascript
function createCounter() {
  let count = 0;  // "private" due to closure
  return {
    increment() {
      return ++count;
    },
    getCount() {
      return count;
    }
  };
}
const counter = createCounter();
counter.increment(); // 1
counter.getCount();  // 1
// count is not directly accessible
```

function adder(num){
    let out=0;
    return {
        add5(num){
            return out+5;
        },
        add10(num){
            return out+10
        }
    }
}

let num=5
const val=adder()
val.add5(num)
val.add10(num)