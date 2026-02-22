"""
Longest Consecutive Sequence (LeetCode #8)

Problem:
Given an unsorted array of integers, return the length of the longest consecutive
sequence of elements.

Example:
Input:  nums = [100, 4, 200, 1, 3, 2]
Output: 4
Explanation: The longest consecutive sequence is [1, 2, 3, 4].
"""

from typing import List


def longest_consecutive_bruteforce(nums: List[int]) -> int:
    """
    Brute force (sorting):
    Sort the array, then scan and count the longest run of consecutive numbers.

    Time:  O(n log n)
    Space: O(1) or O(n) depending on sort implementation
    """
    if not nums:
        return 0

    nums_sorted = sorted(nums)
    longest = 1
    current = 1

    for i in range(1, len(nums_sorted)):
        if nums_sorted[i] == nums_sorted[i - 1] + 1:
            current += 1
        elif nums_sorted[i] == nums_sorted[i - 1]:
            continue
        else:
            longest = max(longest, current)
            current = 1

    return max(longest, current)


# Explanation (Brute Force):
# Sorting makes consecutive numbers adjacent. We then scan and track the longest run.
# Time Complexity: O(n log n)
# Space Complexity: O(1) extra (or O(n) depending on sort)


def longest_consecutive_optimized(nums: List[int]) -> int:
    """
    Optimized (hash set):
    Use a set to allow O(1) lookups. Only start counting from numbers
    that are the beginning of a sequence (num - 1 not in set).

    Time:  O(n)
    Space: O(n)
    """
    num_set = set(nums)
    longest = 0

    for num in num_set:
        if num - 1 not in num_set:
            current = num
            length = 1
            while current + 1 in num_set:
                current += 1
                length += 1
            longest = max(longest, length)

    return longest


# Explanation (Optimized):
# Each sequence is counted only once, from its smallest element.
# This yields linear time with a hash set.
# Time Complexity: O(n)
# Space Complexity: O(n)


if __name__ == "__main__":
    nums = [100, 4, 200, 1, 3, 2]
    print("Brute force result:", longest_consecutive_bruteforce(nums))
    print("Optimized result:", longest_consecutive_optimized(nums))
