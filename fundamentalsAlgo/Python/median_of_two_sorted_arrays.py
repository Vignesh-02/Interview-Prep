"""
Median of Two Sorted Arrays (LeetCode #4)

Problem:
Given two sorted arrays nums1 and nums2, return the median of the two sorted arrays.
The overall time complexity should be O(log(min(m, n))).

Example:
Input: nums1 = [1, 3], nums2 = [2]
Output: 2.0
Explanation: Merged array = [1,2,3], median = 2.
"""

from typing import List


def median_bruteforce(nums1: List[int], nums2: List[int]) -> float:
    """
    Brute force:
    Merge the arrays, then compute the median.

    Time:  O((m + n) log(m + n))
    Space: O(m + n)
    """
    merged = sorted(nums1 + nums2)
    total = len(merged)
    mid = total // 2
    if total % 2 == 1:
        return float(merged[mid])
    return (merged[mid - 1] + merged[mid]) / 2.0


# Explanation (Brute Force):
# The simplest method is to combine both arrays, sort them, and pick the middle.
# Example: [1,3] + [2] => [1,2,3], median = 2.
# Time Complexity: O((m + n) log(m + n))
# Space Complexity: O(m + n)


def median_optimized(nums1: List[int], nums2: List[int]) -> float:
    """
    Optimized (binary search partition):
    Partition the smaller array so that left halves contain half the elements,
    and all left elements <= all right elements.

    Time:  O(log(min(m, n)))
    Space: O(1)
    """
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1

    m, n = len(nums1), len(nums2)
    total_left = (m + n + 1) // 2
    left, right = 0, m

    while left <= right:
        i = (left + right) // 2
        j = total_left - i

        nums1_left = nums1[i - 1] if i > 0 else float("-inf")
        nums1_right = nums1[i] if i < m else float("inf")
        nums2_left = nums2[j - 1] if j > 0 else float("-inf")
        nums2_right = nums2[j] if j < n else float("inf")

        if nums1_left <= nums2_right and nums2_left <= nums1_right:
            if (m + n) % 2 == 1:
                return float(max(nums1_left, nums2_left))
            return (max(nums1_left, nums2_left) + min(nums1_right, nums2_right)) / 2.0
        elif nums1_left > nums2_right:
            right = i - 1
        else:
            left = i + 1

    raise ValueError("Input arrays are not sorted correctly")


# Explanation (Optimized):
# We choose a cut in the smaller array and infer the cut in the larger array.
# When all left elements are <= all right elements, we can compute the median.
# Time Complexity: O(log(min(m, n)))
# Space Complexity: O(1)


if __name__ == "__main__":
    nums1 = [1, 3]
    nums2 = [2]
    print("Brute force result:", median_bruteforce(nums1, nums2))
    print("Optimized result:", median_optimized(nums1, nums2))
