// O(n) time and O(1) space
function palindrome(s) {
  let left = 0;
  let right = s.length - 1;
  while (left <= right) {
    if (s[left].toLowerCase() !== s[right].toLowerCase()) {
      return "Not a Palindrome";
    }
    left += 1;
    right -= 1;
  }
  return "It is a Palindrome";
}

const out = palindrome("bubba");
console.log(out);

module.exports = { palindrome };
