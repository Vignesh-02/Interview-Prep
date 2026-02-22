// T = O(2^n) time and O(n) space (recursion stack)
// Using recursion
function fib(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}

console.log(fib(5));
// return the nth fibonacci number

// O(n) time and O(1) space
// Using iteration, constant space
function fib1(n) {
  let a = 0;
  let b = 1;
  for (let i = 0; i < n; i += 1) {
    const next = a + b;
    a = b;
    b = next;
  }
  return a;
}

console.log(fib1(5));

// O(n) time and O(n) space (memoized)
function fib2(n, memo = new Map()) {
  if (memo.has(n)) return memo.get(n);
  if (n < 2) return n;
  const val = fib2(n - 1, memo) + fib2(n - 2, memo);
  memo.set(n, val);
  return val;
}

console.log(fib2(5));

// O(n) time and O(n) space
function fib3(n) {
  if (n < 2) return n;
  const dp = new Array(n + 1).fill(0);
  dp[1] = 1;
  for (let i = 2; i <= n; i += 1) {
    dp[i] = dp[i - 1] + dp[i - 2];
  }
  return dp[n];
}

console.log(fib3(5));

// O(log n) time and space (recursion)
// Matrix method
function fibonacci(n) {
  if (n === 0) return 0;

  function multiply(A, B) {
    return [
      [A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]],
      [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]],
    ];
  }

  function power(matrix, exp) {
    if (exp === 1) return matrix;
    if (exp % 2 === 0) {
      const half = power(matrix, Math.floor(exp / 2));
      return multiply(half, half);
    }
    return multiply(matrix, power(matrix, exp - 1));
  }

  const base = [
    [1, 1],
    [1, 0],
  ];

  return power(base, n)[0][1];
}

console.log(fibonacci(5));

module.exports = { fib, fib1, fib2, fib3, fibonacci };
