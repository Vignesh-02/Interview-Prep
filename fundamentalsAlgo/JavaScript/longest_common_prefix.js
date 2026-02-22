/*
Longest Common Prefix (LeetCode #6)

Problem:
Write a function to find the longest common prefix string amongst an array of strings.
If there is no common prefix, return an empty string "".

Example:
Input:  strs = ["flower", "flow", "flight"]
Output: "fl"
*/

function longestCommonPrefixBruteforce(strs) {
  /*
  Brute force:
  Take all prefixes of the first string and check if each is a prefix
  of all other strings, keeping the longest.

  Time:  O(n * m^2) in worst case (n strings, m length)
  Space: O(1)
  */
  if (!strs.length) return "";

  const first = strs[0];
  let best = "";
  for (let end = 1; end <= first.length; end += 1) {
    const prefix = first.slice(0, end);
    const ok = strs.slice(1).every((s) => s.startsWith(prefix));
    if (ok) {
      best = prefix;
    } else {
      break;
    }
  }
  return best;
}

// Explanation (Brute Force):
// We try prefixes of the first string in increasing length and verify
// each one across the remaining strings until it fails.
// Time Complexity: O(n * m^2) in worst case
// Space Complexity: O(1)

function longestCommonPrefixOptimized(strs) {
  /*
  Optimized:
  Sort the list. The common prefix of the whole set is the common prefix
  between the first and last strings after sorting.

  Time:  O(n log n * m) due to sorting comparisons
  Space: O(1) extra
  */
  if (!strs.length) return "";

  const sorted = [...strs].sort();
  const first = sorted[0];
  const last = sorted[sorted.length - 1];

  let i = 0;
  while (i < first.length && i < last.length && first[i] === last[i]) {
    i += 1;
  }
  return first.slice(0, i);
}

// Explanation (Optimized):
// Sorting places lexicographically smallest and largest strings at the ends.
// Their common prefix must be the common prefix for the entire list.
// Time Complexity: O(n log n * m)
// Space Complexity: O(1) extra

if (require.main === module) {
  const strs = ["flower", "flow", "flight"];
  console.log("Brute force result:", longestCommonPrefixBruteforce(strs));
  console.log("Optimized result:", longestCommonPrefixOptimized(strs));
}

module.exports = {
  longestCommonPrefixBruteforce,
  longestCommonPrefixOptimized,
};
