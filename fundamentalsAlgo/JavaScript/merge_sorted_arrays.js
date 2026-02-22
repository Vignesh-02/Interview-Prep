// given two sorted integer arrays num1 and num2,
// merge nums2 into nums1 as one sorted array

// You may assume that nums1 has enough space (size that
// is equal to m + n) to hold additional elements from nums2

// m and n are the number of elements in each list

// naive solution 1

// Time complexity O(m+n)
// Space complexity O(m+n)

function mergeSortedArray(nums1, nums2, m, n) {
  const temp = new Array(m + n);
  let i = 0;
  let j = 0;
  let k = 0;
  while (i < m && j < n) {
    if (nums1[i] < nums2[j]) {
      temp[k] = nums1[i];
      k += 1;
      i += 1;
    } else {
      temp[k] = nums2[j];
      k += 1;
      j += 1;
    }
  }

  while (i < m) {
    temp[k] = nums1[i];
    k += 1;
    i += 1;
  }
  while (j < n) {
    temp[k] = nums2[j];
    k += 1;
    j += 1;
  }

  return temp;
}

const arr1 = [1, 2, 3];
const arr2 = [4, 5, 6];
console.log(mergeSortedArray(arr1, arr2, 3, 3));

// Time complexity O(m+n)
// Space complexity O(1) no extra space is allowed

function mergeSortedArraysInPlace(nums1, nums2, m, n) {
  let last = m + n - 1;
  let i = m - 1;
  let j = n - 1;

  while (i >= 0 && j >= 0) {
    if (nums1[i] > nums2[j]) {
      nums1[last] = nums1[i];
      i -= 1;
    } else {
      nums1[last] = nums2[j];
      j -= 1;
    }
    last -= 1;
  }

  while (j >= 0) {
    nums1[last] = nums2[j];
    j -= 1;
    last -= 1;
  }

  return nums1;
}

const arr3 = [1, 2, 3, 0, 0, 0];
const arr4 = [4, 5, 6];
console.log(mergeSortedArraysInPlace(arr3, arr4, 3, 3));

module.exports = { mergeSortedArray, mergeSortedArraysInPlace };
