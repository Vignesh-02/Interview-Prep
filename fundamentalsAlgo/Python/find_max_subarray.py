# Given an integer array nums, find the maximum sum of a contiguous subarray.

# Example
# nums = [-2,1,-3,4,-1,2,1,-5,4]

# Output:
# 6


# Subarray:
# [4, -1, 2, 1]

# O(n) time and O(1) space
def max_subarray(nums):
    current_sum=nums[0]
    max_sum=nums[0]

    for i in range(1, len(nums)):
        # if nums[i] is negative

        # “At each index, I decide whether to extend the previous subarray or start a new one.”
        current_sum=max(nums[i], nums[i] + current_sum)
        max_sum=max(max_sum, current_sum)
    
    return max_sum




# Print the max subaary and the sum

def max_subarray1(nums):
    current_sum=nums[0]
    max_sum=nums[0]

    start=end=temp_start=0

    for i in range(1, len(nums)):
        # if nums[i] is negative

        if nums[i]>current_sum+nums[i]:
            current_sum=nums[i]
            temp_start=i
        else:
            current_sum=current_sum+nums[i]

        if current_sum > max_sum:
            max_sum=current_sum
            start=temp_start
            # we keep going till the end when current sum > max sum
            end=i
    
    return max_sum, nums[start:end+1]

test=[-2, 1, -3, 4, -1, 2, 1, -5, 4]

val, arr = max_subarray1(test)
print("The sum of the max subarray is:", val)
print("The max subarray is:", arr)

# Kadane’s Algorithm is a dynamic programming technique used to find the maximum sum of a contiguous subarray within a 1-D array of numbers — in linear time.

# It is one of the most important algorithms in SDE interviews.

# Maximum product subaarray
# Why Kadane fails here

# With products:

# negative × negative → positive

# zero resets everything

# So we track both max and min products.

# Root Cause of Failure
# ❌ Kadane Assumption

# “A bad prefix can never become good later.”

# ❌ False for Product
# negative × negative = positive


# So:

# You cannot discard negative prefixes

# You must remember the worst product, not just the best

# current_sum[i] = max(nums[i], nums[i] + current_sum[i-1])
# max_sum = max(max_sum, current_sum[i])


# O(n) time and O(1) space
def max_product_subarray(nums):
    max_prod=min_prod=result=nums[0]

    for i in range(1,len(nums)):
        n=nums[i]

        # most important line

        # if current value is -ve, the  leastest value become the greatest value
        if n<0:
            max_prod, min_prod = min_prod, max_prod

        max_prod=max(max_prod, n)
        min_prod=min(min_prod, n)

        result = max(max_prod, result)
        

    return result



nums = [2,3,-2,4]
print("The output is ", max_product_subarray(nums))


# Maximum Circular Subarray Sum (Kadane Twice)
# 1️⃣ What “circular” actually means

# In a normal array, subarrays must be contiguous without wrapping.

# In a circular array, the end connects back to the beginning:

# [5, -2, 3, 4]
#        ↖ wrap ↩


# So valid subarrays include:

# [5, -2, 3]

# [3, 4, 5] ← wraps around

# [4, 5]

# 2️⃣ Key Insight (This is the Interview Moment)

# A maximum circular subarray is either:

# Case 1️⃣ Normal (non-circular)

# Just regular Kadane.

# Case 2️⃣ Circular (wrap-around)

# Take:

# Total Sum of Array
# − Minimum Subarray Sum


# Why?

# Because wrapping means:

# “Take everything except the worst (minimum) contiguous subarray.”

# 3️⃣ Visual Intuition
# Array:   [ 5,  -3,   5 ]
# Min subarray = [-3]

# Circular max = (5 + -3 + 5) - (-3) = 10
# Subarray = [5, 5] (wraps around)

# 4️⃣ Algorithm Breakdown (Kadane Twice)

# Run Kadane → get max_subarray_sum

# Run Kadane for minimum → get min_subarray_sum

# Compute total_sum

# Answer = max(max_subarray_sum, total_sum - min_subarray_sum)

# ⚠️ Special Case:
# If all numbers are negative, circular logic breaks.
# → Return max_subarray_sum

# 5️⃣ Interview-Ready Python Code (Clean & Readable)
# def max_subarray_sum(nums):
#     current = best = nums[0]
#     for num in nums[1:]:
#         current = max(num, current + num)
#         best = max(best, current)
#     return best


# def min_subarray_sum(nums):
#     current = best = nums[0]
#     for num in nums[1:]:
#         current = min(num, current + num)
#         best = min(best, current)
#     return best


# def max_circular_subarray_sum(nums):
#     max_normal = max_subarray_sum(nums)

#     # If all numbers are negative
#     if max_normal < 0:
#         return max_normal

#     total_sum = sum(nums)
#     min_subarray = min_subarray_sum(nums)

#     max_circular = total_sum - min_subarray

#     return max(max_normal, max_circular)


# Example Walkthrough
# nums = [5, -3, 5]

# Step	Value
# max_normal	7
# total_sum	7
# min_subarray	-3
# max_circular	10
# answer	10
# 7️⃣ Time & Space Complexity
# Metric	Value
# Time	O(n)
# Space	O(1)

# Can Max Product Subarray Code Be Used Here? ❌
# ❌ No — and here’s why (interview-level explanation)
# Max Circular Sum	Max Product
# Based on addition	Based on multiplication
# Uses complement (total - min)	❌ No equivalent
# Monotonic behavior	❌ Sign flipping
# Kadane works	Kadane fails

# “The maximum circular subarray is either a normal Kadane subarray or a wrapping one, which equals total sum minus the minimum subarray sum.”