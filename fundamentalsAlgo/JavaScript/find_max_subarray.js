// Given an integer array nums, find the maximum sum of a contiguous subarray.

// Example
// nums = [-2,1,-3,4,-1,2,1,-5,4]
// Output: 6
// Subarray: [4, -1, 2, 1]

// O(n) time and O(1) space
function maxSubarray(nums) {
  let currentSum = nums[0];
  let maxSum = nums[0];

  for (let i = 1; i < nums.length; i += 1) {
    // At each index, decide to extend or start new
    currentSum = Math.max(nums[i], nums[i] + currentSum);
    maxSum = Math.max(maxSum, currentSum);
  }

  return maxSum;
}

// Print the max subarray and the sum
function maxSubarrayWithRange(nums) {
  let currentSum = nums[0];
  let maxSum = nums[0];
  let start = 0;
  let end = 0;
  let tempStart = 0;

  for (let i = 1; i < nums.length; i += 1) {
    if (nums[i] > currentSum + nums[i]) {
      currentSum = nums[i];
      tempStart = i;
    } else {
      currentSum = currentSum + nums[i];
    }

    if (currentSum > maxSum) {
      maxSum = currentSum;
      start = tempStart;
      end = i;
    }
  }

  return { maxSum, subarray: nums.slice(start, end + 1) };
}

const test = [-2, 1, -3, 4, -1, 2, 1, -5, 4];
const { maxSum, subarray } = maxSubarrayWithRange(test);
console.log("The sum of the max subarray is:", maxSum);
console.log("The max subarray is:", subarray);

// Kadane's Algorithm is a dynamic programming technique used to find the maximum sum
// of a contiguous subarray within a 1-D array of numbers - in linear time.

// Maximum product subarray
// O(n) time and O(1) space
function maxProductSubarray(nums) {
  let maxProd = nums[0];
  let minProd = nums[0];
  let result = nums[0];

  for (let i = 1; i < nums.length; i += 1) {
    const n = nums[i];
    if (n < 0) {
      const temp = maxProd;
      maxProd = minProd;
      minProd = temp;
    }

    maxProd = Math.max(n, n * maxProd);
    minProd = Math.min(n, n * minProd);
    result = Math.max(result, maxProd);
  }

  return result;
}

const nums = [2, 3, -2, 4];
console.log("The output is", maxProductSubarray(nums));

module.exports = { maxSubarray, maxSubarrayWithRange, maxProductSubarray };
