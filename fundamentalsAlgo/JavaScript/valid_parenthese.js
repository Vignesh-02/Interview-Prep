// O(n) time and O(n) space
function validParenthesis(s) {
  const stack = [];
  const mapping = { ")": "(", "]": "[", "}": "{" };

  for (const c of s) {
    if (mapping[c]) {
      if (stack.length && stack[stack.length - 1] === mapping[c]) {
        stack.pop();
      } else {
        return false;
      }
    } else {
      stack.push(c);
    }
  }

  return stack.length === 0;
}

const out = validParenthesis("{{}}[]");
console.log(out);

module.exports = { validParenthesis };
