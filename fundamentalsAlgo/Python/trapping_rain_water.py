"""
Trapping Rain Water (LeetCode #3)

Problem:
Given an array of non-negative integers representing elevation heights,
compute how much water can be trapped after raining.

Example:
Input:  height = [0,1,0,2,1,0,1,3,2,1,2,1]
Output: 6
Explanation: Water is trapped in the dips between higher bars.
"""

from typing import List


def trap_bruteforce(height: List[int]) -> int:
    """
    Brute force:
    For each index, find the max bar on the left and right.
    Water at i = min(max_left, max_right) - height[i].

    Time:  O(n^2)
    Space: O(1)
    """
    n = len(height)
    water = 0
    for i in range(n):
        max_left = max(height[: i + 1])
        max_right = max(height[i:])
        water += max(0, min(max_left, max_right) - height[i])
    return water


# Explanation (Brute Force):
# For every position, you scan left and right to find the tallest bars.
# The height of water at that position depends on the shorter of those two bars.
# Example: height = [0,1,0,2,...]
# At index 2 (height 0), left max=1, right max=3 => water=1-0=1.
# Time Complexity: O(n^2)
# Space Complexity: O(1)


def trap_optimized(height: List[int]) -> int:
    """
    Optimized (two pointers):
    Move pointers inward while tracking max_left and max_right.
    The smaller side determines trapped water at each step.

    Time:  O(n)
    Space: O(1)
    """
    left, right = 0, len(height) - 1
    max_left = max_right = 0
    water = 0

    while left <= right:
        if height[left] <= height[right]:
            if height[left] >= max_left:
                max_left = height[left]
            else:
                water += max_left - height[left]
            left += 1
        else:
            if height[right] >= max_right:
                max_right = height[right]
            else:
                water += max_right - height[right]
            right -= 1

    return water


# Explanation (Optimized):
# The pointer on the lower side limits water height. If left bar is smaller,
# we can safely compute water at left using max_left. Same for right.
# Time Complexity: O(n)
# Space Complexity: O(1)


if __name__ == "__main__":
    height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
    print("Brute force result:", trap_bruteforce(height))
    print("Optimized result:", trap_optimized(height))
