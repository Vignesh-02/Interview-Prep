# 13. String Manipulation & Coding Challenges

## Q1. Write a function to reverse a string without using `reverse()`.

**Answer:**
```javascript
function reverseString(str) {
  let result = '';
  for (let i = str.length - 1; i >= 0; i--) {
    result += str[i];
  }
  return result;
}
// or: str.split('').reverse().join('')
// or: [...str].reverse().join('')  (better for Unicode)
```

---

## Q2. Check if a string is a palindrome (ignoring case and non-alphanumeric).

**Answer:**
```javascript
function isPalindrome(str) {
  const cleaned = str.toLowerCase().replace(/[^a-z0-9]/g, '');
  let left = 0, right = cleaned.length - 1;
  while (left < right) {
    if (cleaned[left] !== cleaned[right]) return false;
    left++;
    right--;
  }
  return true;
}
```

---

## Q3. Find the first non-repeating character in a string. Return the character or null.

**Answer:**
```javascript
function firstNonRepeating(str) {
  const counts = {};
  for (const c of str) {
    counts[c] = (counts[c] || 0) + 1;
  }
  for (const c of str) {
    if (counts[c] === 1) return c;
  }
  return null;
}
```

---

## Q4. Implement a function that capitalizes the first letter of each word.

**Answer:**
```javascript
function capitalizeWords(str) {
  return str
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}
```

---

## Q5. Check if two strings are anagrams (same characters, same frequency).

**Answer:**
```javascript
function areAnagrams(a, b) {
  if (a.length !== b.length) return false;
  const count = {};
  for (const c of a) count[c] = (count[c] || 0) + 1;
  for (const c of b) {
    if (!count[c]) return false;
    count[c]--;
  }
  return true;
}
```

---

## Q6. Count the number of vowels in a string.

**Answer:**
```javascript
function countVowels(str) {
  const vowels = 'aeiouAEIOU';
  return [...str].filter((c) => vowels.includes(c)).length;
}
// or: (str.match(/[aeiou]/gi) || []).length
```

---

## Q7. Longest substring without repeating characters (return its length).

**Answer:**
```javascript
function lengthOfLongestSubstring(s) {
  const seen = new Set();
  let left = 0, max = 0;
  for (let right = 0; right < s.length; right++) {
    while (seen.has(s[right])) {
      seen.delete(s[left]);
      left++;
    }
    seen.add(s[right]);
    max = Math.max(max, right - left + 1);
  }
  return max;
}
```

---

## Q8. Truncate a string to a given length and append "..." if truncated.

**Answer:**
```javascript
function truncate(str, maxLen) {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen - 3) + '...';
}
```

---

## Q9. Implement a simple string compression: "aabbbcc" → "a2b3c2". Only compress if result is shorter.

**Answer:**
```javascript
function compress(str) {
  let result = '';
  let count = 1;
  for (let i = 1; i <= str.length; i++) {
    if (str[i] === str[i - 1]) {
      count++;
    } else {
      result += str[i - 1] + (count > 1 ? count : '');
      count = 1;
    }
  }
  return result.length < str.length ? result : str;
}
```

---

## Q10. (Tricky) What is the output of `"🤷".length` and why? How would you count “visible” characters?

**Answer:**  
`"🤷".length` is **2** (in most JS engines), because the character is a UTF-16 surrogate pair and `length` counts code units. To count user-perceived characters (grapheme clusters), use **`[...str].length`** or **`Intl.Segmenter`** (e.g. segment by 'grapheme'). So `[...'🤷'].length` is 1.
