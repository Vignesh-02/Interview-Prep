/*
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
*/

function rotateBruteforce(matrix) {
  /*
  Brute force:
  Create a new matrix and map each element to its rotated position.

  Time:  O(n^2)
  Space: O(n^2)
  */
  const n = matrix.length;
  const rotated = Array.from({ length: n }, () => Array(n).fill(0));
  for (let i = 0; i < n; i += 1) {
    for (let j = 0; j < n; j += 1) {
      rotated[j][n - 1 - i] = matrix[i][j];
    }
  }
  return rotated;
}

// Explanation (Brute Force):
// We build a new matrix and place each original element into its rotated location.
// Example: element (0,0) goes to (0, n-1), and so on.
// Time Complexity: O(n^2)
// Space Complexity: O(n^2)

function rotateOptimized(matrix) {
  /*
  Optimized (in-place):
  First transpose the matrix, then reverse each row.

  Time:  O(n^2)
  Space: O(1)
  */
  const n = matrix.length;

  // Transpose
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 1; j < n; j += 1) {
      const temp = matrix[i][j];
      matrix[i][j] = matrix[j][i];
      matrix[j][i] = temp;
    }
  }

  // Reverse each row
  for (let i = 0; i < n; i += 1) {
    matrix[i].reverse();
  }
}

// Explanation (Optimized):
// Transposing swaps rows with columns. Reversing each row completes the 90 degree rotation.
// Time Complexity: O(n^2)
// Space Complexity: O(1)

if (require.main === module) {
  const matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
  ];

  const rotated = rotateBruteforce(matrix);
  console.log("Brute force result:", rotated);

  rotateOptimized(matrix);
  console.log("Optimized result:", matrix);
}

module.exports = { rotateBruteforce, rotateOptimized };
