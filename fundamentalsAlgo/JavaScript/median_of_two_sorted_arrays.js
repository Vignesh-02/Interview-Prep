/*
Median of Two Sorted Arrays (LeetCode #4)

Problem:
Given two sorted arrays nums1 and nums2, return the median of the two sorted arrays.
The overall time complexity should be O(log(min(m, n))).

Example:
Input: nums1 = [1, 3], nums2 = [2]
Output: 2.0
Explanation: Merged array = [1,2,3], median = 2.
*/

function medianBruteforce(nums1, nums2) {
  /*
  Brute force:
  Merge the arrays, then compute the median.

  Time:  O((m + n) log(m + n))
  Space: O(m + n)
  */
  const merged = [...nums1, ...nums2].sort((a, b) => a - b);
  const total = merged.length;
  const mid = Math.floor(total / 2);
  if (total % 2 === 1) return merged[mid];
  return (merged[mid - 1] + merged[mid]) / 2;
}

// Explanation (Brute Force):
// The simplest method is to combine both arrays, sort them, and pick the middle.
// Example: [1,3] + [2] => [1,2,3], median = 2.
// Time Complexity: O((m + n) log(m + n))
// Space Complexity: O(m + n)

function medianOptimized(nums1, nums2) {
  /*
  Optimized (binary search partition):
  Partition the smaller array so that left halves contain half the elements,
  and all left elements <= all right elements.

  Time:  O(log(min(m, n)))
  Space: O(1)
  */
  let A = nums1;
  let B = nums2;
  if (A.length > B.length) {
    A = nums2;
    B = nums1;
  }

  const m = A.length;
  const n = B.length;
  const totalLeft = Math.floor((m + n + 1) / 2);
  let left = 0;
  let right = m;

  while (left <= right) {
    const i = Math.floor((left + right) / 2);
    const j = totalLeft - i;

    const ALeft = i > 0 ? A[i - 1] : -Infinity;
    const ARight = i < m ? A[i] : Infinity;
    const BLeft = j > 0 ? B[j - 1] : -Infinity;
    const BRight = j < n ? B[j] : Infinity;

    if (ALeft <= BRight && BLeft <= ARight) {
      if ((m + n) % 2 === 1) return Math.max(ALeft, BLeft);
      return (Math.max(ALeft, BLeft) + Math.min(ARight, BRight)) / 2;
    } else if (ALeft > BRight) {
      right = i - 1;
    } else {
      left = i + 1;
    }
  }

  throw new Error("Input arrays are not sorted correctly");
}

// Explanation (Optimized):
// We choose a cut in the smaller array and infer the cut in the larger array.
// When all left elements are <= all right elements, we can compute the median.
// Time Complexity: O(log(min(m, n)))
// Space Complexity: O(1)

if (require.main === module) {
  const nums1 = [1, 3];
  const nums2 = [2];
  console.log("Brute force result:", medianBruteforce(nums1, nums2));
  console.log("Optimized result:", medianOptimized(nums1, nums2));
}

module.exports = { medianBruteforce, medianOptimized };
