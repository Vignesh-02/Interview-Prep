from functools import lru_cache
# T = O(2n) time and O(1) space
# Using Recursion
def fib(n):
    if n<2:
        return n
    return fib(n-1) + fib(n-2)

out =fib(5)
print(out)
# return the nth fibonacci number

# O(n) time and O(1) space
# Using iteration, constant space and temp variable in other languages
def fib1(n):
    a,b=0,1
    for _ in range(n):
        a,b = b,a+b
    return a

out =fib1(5)
print(out)

# O(n) time and O(n) space as fib2(n) value once computed gets stored in cache, it's memoized
# cons: uses recursion stack and extra memory for cache
@lru_cache
def fib2(n):
    if n<2:
        return n
    return fib2(n-1) + fib2(n-2)

out =fib2(5)
print(out)

# O(n) time and O(n) space
# stores unnecessary values
def fib3(n):
    if n<2:
        return n
    dp=[0]*(n+1)
    dp[1]=1   #important, without this program will always return 0
    for i in range(2,n+1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]

out =fib3(5)
print(out)

# O(logn) time and space
# Matrix method
# Study this!
def fibonacci(n):
    if n == 0:
        return 0

    def multiply(A, B):
        return [
            [
                A[0][0] * B[0][0] + A[0][1] * B[1][0],
                A[0][0] * B[0][1] + A[0][1] * B[1][1]
            ],
            [
                A[1][0] * B[0][0] + A[1][1] * B[1][0],
                A[1][0] * B[0][1] + A[1][1] * B[1][1]
            ]
        ]

    def power(matrix, n):
        if n == 1:
            return matrix

        if n % 2 == 0:
            half = power(matrix, n // 2)
            return multiply(half, half)
        else:
            return multiply(matrix, power(matrix, n - 1))

    base = [
        [1, 1],
        [1, 0]
    ]

    return power(base, n)[0][1]

out =fibonacci(5)
print(out)

# check out fast doubling method

# “While Fibonacci can be solved in multiple ways, the optimal practical solution in Python is the iterative O(n) time, O(1) space approach. For extremely large n, matrix exponentiation gives O(log n) time.”

# When O(n) Is NOT Enough

# If:

# n is extremely large (e.g. 10^18)

# Then use:

# Matrix exponentiation!

# Fast doubling method!

# Time:

# O(log n)