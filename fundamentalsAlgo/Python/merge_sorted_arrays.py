# given two sorted integer arrays num1 and num2,
# merge nums2 into nums1 as one sorted array

# You may assume that nums1 has enough space (size that 
# is equal to m + n) to hold additional elements from nums2

# m and n are the number of elements in each list

# naive solution 1

# Time complexity O(m+n)
# Space complexity O(m+n)


# imp

class Solution1:
    def merge_sorted_array(self,nums1,nums2, m, n):
        temp = [None] * (m + n)
        i=0
        j=0
        k=0
        while i < m and j < n:
            if nums1[i] < nums2[j]:
                temp[k] = nums1[i]
                k=k+1
                i=i+1
            else: 
                temp[k] = nums2[j]
                k=k+1
                j=j+1

        while i < m:
            temp[k] =  nums1[i]
            k=k+1
            i=i+1
        while j < n:
            temp[k] =  nums2[j]
            k=k+1
            j=j+1
        return temp
         

arr1 = [1,2,3]
arr2 = [4,5,6]
s1 = Solution1()
print(s1.merge_sorted_array(arr1, arr2,3,3))
# print(s1.twoSum(arr,4))


# Time complexity O(m)
# Space complexity O(1) no extra space is allowed

class Solution2:
    def merge_sorted_arrays(self, nums1, nums2, m, n):
        # getting to the last element of nums 1
        last = m + n - 1
        while m > 0 and n > 0:
            if nums1[m-1] > nums2[n-1]:
                nums1[last] = nums1[m-1]
                m=m-1
            else:
                nums1[last] = nums2[n-1]
                n=n-1
            last=last-1
        while n > 0:
            nums1[last] = nums2[n-1]
            n=n-1
            last=last-1
        return nums1

arr1 = [1,2,3,0,0,0]
arr2 = [4,5,6]
s2 = Solution2()
print(s2.merge_sorted_arrays(arr1, arr2,3,3))





