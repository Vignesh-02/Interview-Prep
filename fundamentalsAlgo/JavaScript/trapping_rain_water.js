/*
Trapping Rain Water (LeetCode #3)

Problem:
Given an array of non-negative integers representing elevation heights,
compute how much water can be trapped after raining.

Example:
Input:  height = [0,1,0,2,1,0,1,3,2,1,2,1]
Output: 6
Explanation: Water is trapped in the dips between higher bars.
*/

function trapBruteforce(height) {
  /*
  Brute force:
  For each index, find the max bar on the left and right.
  Water at i = min(maxLeft, maxRight) - height[i].

  Time:  O(n^2)
  Space: O(1)
  */
  const n = height.length;
  let water = 0;
  for (let i = 0; i < n; i += 1) {
    const maxLeft = Math.max(...height.slice(0, i + 1));
    const maxRight = Math.max(...height.slice(i));
    water += Math.max(0, Math.min(maxLeft, maxRight) - height[i]);
  }
  return water;
}

// Explanation (Brute Force):
// For every position, you scan left and right to find the tallest bars.
// The height of water at that position depends on the shorter of those two bars.
// Example: height = [0,1,0,2,...]
// At index 2 (height 0), left max=1, right max=3 => water=1-0=1.
// Time Complexity: O(n^2)
// Space Complexity: O(1)

function trapOptimized(height) {
  /*
  Optimized (two pointers):
  Move pointers inward while tracking maxLeft and maxRight.
  The smaller side determines trapped water at each step.

  Time:  O(n)
  Space: O(1)
  */
  let left = 0;
  let right = height.length - 1;
  let maxLeft = 0;
  let maxRight = 0;
  let water = 0;

  while (left <= right) {
    if (height[left] <= height[right]) {
      if (height[left] >= maxLeft) {
        maxLeft = height[left];
      } else {
        water += maxLeft - height[left];
      }
      left += 1;
    } else {
      if (height[right] >= maxRight) {
        maxRight = height[right];
      } else {
        water += maxRight - height[right];
      }
      right -= 1;
    }
  }

  return water;
}

// Explanation (Optimized):
// The pointer on the lower side limits water height. If left bar is smaller,
// we can safely compute water at left using maxLeft. Same for right.
// Time Complexity: O(n)
// Space Complexity: O(1)

if (require.main === module) {
  const height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1];
  console.log("Brute force result:", trapBruteforce(height));
  console.log("Optimized result:", trapOptimized(height));
}

module.exports = { trapBruteforce, trapOptimized };
