"""
Longest Common Prefix (LeetCode #6)

Problem:
Write a function to find the longest common prefix string amongst an array of strings.
If there is no common prefix, return an empty string "".

Example:
Input:  strs = ["flower", "flow", "flight"]
Output: "fl"
"""

from typing import List


def longest_common_prefix_bruteforce(strs: List[str]) -> str:
    """
    Brute force:
    Take all prefixes of the first string and check if each is a prefix
    of all other strings, keeping the longest.

    Time:  O(n * m^2) in worst case (n strings, m length)
    Space: O(1)
    """
    if not strs:
        return ""

    first = strs[0]
    best = ""
    for end in range(1, len(first) + 1):
        prefix = first[:end]
        if all(s.startswith(prefix) for s in strs[1:]):
            best = prefix
        else:
            break
    return best


# Explanation (Brute Force):
# We try prefixes of the first string in increasing length and verify
# each one across the remaining strings until it fails.
# Time Complexity: O(n * m^2) in worst case
# Space Complexity: O(1)


def longest_common_prefix_optimized(strs: List[str]) -> str:
    """
    Optimized:
    Sort the list. The common prefix of the whole set is the common prefix
    between the first and last strings after sorting.

    Time:  O(n log n * m) due to sorting comparisons
    Space: O(1) extra
    """
    if not strs:
        return ""

    strs_sorted = sorted(strs)
    first = strs_sorted[0]
    last = strs_sorted[-1]

    i = 0
    while i < len(first) and i < len(last) and first[i] == last[i]:
        i += 1
    return first[:i]


# Explanation (Optimized):
# Sorting places lexicographically smallest and largest strings at the ends.
# Their common prefix must be the common prefix for the entire list.
# Time Complexity: O(n log n * m)
# Space Complexity: O(1) extra


if __name__ == "__main__":
    strs = ["flower", "flow", "flight"]
    print("Brute force result:", longest_common_prefix_bruteforce(strs))
    print("Optimized result:", longest_common_prefix_optimized(strs))
