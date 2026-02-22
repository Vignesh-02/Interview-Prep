"""
Rotate Image (LeetCode #10)

Problem:
You are given an n x n 2D matrix representing an image.
Rotate the image by 90 degrees (clockwise) in-place.

Example:
Input:  matrix = [
  [1, 2, 3],
  [4, 5, 6],
  [7, 8, 9]
]
Output: [
  [7, 4, 1],
  [8, 5, 2],
  [9, 6, 3]
]
"""

from typing import List


def rotate_bruteforce(matrix: List[List[int]]) -> List[List[int]]:
    """
    Brute force:
    Create a new matrix and map each element to its rotated position.

    Time:  O(n^2)
    Space: O(n^2)
    """
    n = len(matrix)
    rotated = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            rotated[j][n - 1 - i] = matrix[i][j]
    return rotated


# Explanation (Brute Force):
# We build a new matrix and place each original element into its rotated location.
# Example: element (0,0) goes to (0, n-1), and so on.
# Time Complexity: O(n^2)
# Space Complexity: O(n^2)


def rotate_optimized(matrix: List[List[int]]) -> None:
    """
    Optimized (in-place):
    First transpose the matrix, then reverse each row.

    Time:  O(n^2)
    Space: O(1)
    """
    n = len(matrix)

    # Transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    # Reverse each row
    for i in range(n):
        matrix[i].reverse()


# Explanation (Optimized):
# Transposing swaps rows with columns. Reversing each row completes the 90° rotation.
# Time Complexity: O(n^2)
# Space Complexity: O(1)


if __name__ == "__main__":
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]

    rotated = rotate_bruteforce(matrix)
    print("Brute force result:", rotated)

    rotate_optimized(matrix)
    print("Optimized result:", matrix)
