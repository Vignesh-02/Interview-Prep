// Worst case: O(log n) - target found after log2(n) iterations, or not found
// Each iteration halves the search space, so the number of iterations is logarithmic

// O(log n) time and O(1) space
function binarySearch(nums, target) {
  let left = 0;
  let right = nums.length - 1;

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (target < nums[mid]) {
      right = mid - 1;
    } else if (target > nums[mid]) {
      left = mid + 1;
    } else {
      return mid;
    }
  }

  return -1;
}

const out = binarySearch([3, 4, 5, 7, 8, 10, 12], 10);
console.log(out);

module.exports = { binarySearch };
