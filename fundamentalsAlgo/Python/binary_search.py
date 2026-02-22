
# Worst case: O(log n) — target found after log₂(n) iterations, or not found
# Each iteration halves the search space, so the number of iterations is logarithmic in the input size


# O(logn) time and O(1) space
def binary_search(nums, target):
    l=0
    mid=0
    r=len(nums)-1
    
    while l<r:
        mid=(l+r)//2


        if target < nums[mid]:
            r=mid

        elif target > nums[mid]:
            l=mid

        else:
            return mid

    return -1

out = binary_search([3,4,5,7,8,10,12], 10)
print(out)