/*
Longest Substring Without Repeating Characters (LeetCode #5)

Problem:
Given a string s, find the length of the longest substring without repeating characters.

Example:
Input:  s = "abcabcbb"
Output: 3
Explanation: The answer is "abc" with length 3.
*/

function longestSubstringBruteforce(s) {
  /*
  Brute force:
  Check every substring and see if it has all unique characters.

  Time:  O(n^3) in worst case (generate substrings and check uniqueness)
  Space: O(1) or O(k) for a set
  */
  const n = s.length;
  let best = 0;
  for (let i = 0; i < n; i += 1) {
    for (let j = i; j < n; j += 1) {
      const sub = s.slice(i, j + 1);
      const set = new Set(sub);
      if (set.size === sub.length) {
        best = Math.max(best, sub.length);
      }
    }
  }
  return best;
}

// Explanation (Brute Force):
// We try all substrings and keep the longest one with all unique characters.
// Example: "abcabcbb" -> best found is "abc" of length 3.
// Time Complexity: O(n^3) in worst case
// Space Complexity: O(1) extra (or O(k) for set)

function longestSubstringOptimized(s) {
  /*
  Optimized (sliding window):
  Expand the right pointer, and if a character repeats, move left pointer
  to the right of the last occurrence.

  Time:  O(n)
  Space: O(min(n, alphabet))
  */
  const lastSeen = new Map();
  let left = 0;
  let best = 0;

  for (let right = 0; right < s.length; right += 1) {
    const ch = s[right];
    if (lastSeen.has(ch) && lastSeen.get(ch) >= left) {
      left = lastSeen.get(ch) + 1;
    }
    lastSeen.set(ch, right);
    best = Math.max(best, right - left + 1);
  }

  return best;
}

// Explanation (Optimized):
// The window [left, right] always has unique characters. If we see a duplicate,
// we move left just past its previous index, keeping the window valid.
// Time Complexity: O(n)
// Space Complexity: O(min(n, alphabet))

if (require.main === module) {
  const s = "abcabcbb";
  console.log("Brute force result:", longestSubstringBruteforce(s));
  console.log("Optimized result:", longestSubstringOptimized(s));
}

module.exports = {
  longestSubstringBruteforce,
  longestSubstringOptimized,
};
