"""
Longest Substring Without Repeating Characters (LeetCode #5)

Problem:
Given a string s, find the length of the longest substring without repeating characters.

Example:
Input:  s = "abcabcbb"
Output: 3
Explanation: The answer is "abc" with length 3.
"""

from typing import Dict


def longest_substring_bruteforce(s: str) -> int:
    """
    Brute force:
    Check every substring and see if it has all unique characters.

    Time:  O(n^3) in worst case (generate substrings and check uniqueness)
    Space: O(1) or O(k) for a set
    """
    n = len(s)
    best = 0
    for i in range(n):
        for j in range(i, n):
            sub = s[i : j + 1]
            if len(set(sub)) == len(sub):
                best = max(best, len(sub))
    return best


# Explanation (Brute Force):
# We try all substrings and keep the longest one with all unique characters.
# Example: "abcabcbb" -> best found is "abc" of length 3.
# Time Complexity: O(n^3) in worst case
# Space Complexity: O(1) extra (or O(k) for set)


def longest_substring_optimized(s: str) -> int:
    """
    Optimized (sliding window):
    Expand the right pointer, and if a character repeats, move left pointer
    to the right of the last occurrence.

    Time:  O(n)
    Space: O(min(n, alphabet))
    """
    last_seen: Dict[str, int] = {}
    left = 0
    best = 0

    for right, ch in enumerate(s):
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)

    return best


# Explanation (Optimized):
# The window [left, right] always has unique characters. If we see a duplicate,
# we move left just past its previous index, keeping the window valid.
# Time Complexity: O(n)
# Space Complexity: O(min(n, alphabet))


if __name__ == "__main__":
    s = "abcabcbb"
    print("Brute force result:", longest_substring_bruteforce(s))
    print("Optimized result:", longest_substring_optimized(s))
