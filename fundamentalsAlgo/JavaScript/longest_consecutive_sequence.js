/*
Longest Consecutive Sequence (LeetCode #8)

Problem:
Given an unsorted array of integers, return the length of the longest consecutive
sequence of elements.

Example:
Input:  nums = [100, 4, 200, 1, 3, 2]
Output: 4
Explanation: The longest consecutive sequence is [1, 2, 3, 4].
*/

function longestConsecutiveBruteforce(nums) {
  /*
  Brute force (sorting):
  Sort the array, then scan and count the longest run of consecutive numbers.

  Time:  O(n log n)
  Space: O(1) or O(n) depending on sort implementation
  */
  if (!nums.length) return 0;

  const numsSorted = [...nums].sort((a, b) => a - b);
  let longest = 1;
  let current = 1;

  for (let i = 1; i < numsSorted.length; i += 1) {
    if (numsSorted[i] === numsSorted[i - 1] + 1) {
      current += 1;
    } else if (numsSorted[i] === numsSorted[i - 1]) {
      continue;
    } else {
      longest = Math.max(longest, current);
      current = 1;
    }
  }

  return Math.max(longest, current);
}

// Explanation (Brute Force):
// Sorting makes consecutive numbers adjacent. We then scan and track the longest run.
// Time Complexity: O(n log n)
// Space Complexity: O(1) extra (or O(n) depending on sort)

function longestConsecutiveOptimized(nums) {
  /*
  Optimized (hash set):
  Use a set to allow O(1) lookups. Only start counting from numbers
  that are the beginning of a sequence (num - 1 not in set).

  Time:  O(n)
  Space: O(n)
  */
  const numSet = new Set(nums);
  let longest = 0;

  for (const num of numSet) {
    if (!numSet.has(num - 1)) {
      let current = num;
      let length = 1;
      while (numSet.has(current + 1)) {
        current += 1;
        length += 1;
      }
      longest = Math.max(longest, length);
    }
  }

  return longest;
}

// Explanation (Optimized):
// Each sequence is counted only once, from its smallest element.
// This yields linear time with a hash set.
// Time Complexity: O(n)
// Space Complexity: O(n)

if (require.main === module) {
  const nums = [100, 4, 200, 1, 3, 2];
  console.log("Brute force result:", longestConsecutiveBruteforce(nums));
  console.log("Optimized result:", longestConsecutiveOptimized(nums));
}

module.exports = {
  longestConsecutiveBruteforce,
  longestConsecutiveOptimized,
};
