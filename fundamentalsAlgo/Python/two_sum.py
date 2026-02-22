



def two_sum(nums,target):
    obj={}

    for i, val in enumerate(nums):
        diff=target-val
        if diff in obj:
            return (obj[diff], i)
        obj[val]=i
        

nums=[9,5,4,3]
target=12
print('The two sum is ', two_sum(nums, target))


