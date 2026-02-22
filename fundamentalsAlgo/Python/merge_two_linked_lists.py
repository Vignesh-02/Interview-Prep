# time O(n)
# space O(n)



# can't create copies of nodes
# 1->2->4
# 1->3->4
# 1->1->2->3->4->4 output


class ListNode():
    def __init__(self,val=0,next=None):
        self.val = val
        self.next = next

class Sol:
    def mergeTwoLists(self,l1,l2):
        dummy = ListNode()
        tail = dummy

        while l1 and l2:
            if l1.val < l2.val:
                tail.next = l1
                # forward l1
                l1 = l1.next
            else: 
                tail.next = l2
                # forward l2
                l2 = l2.next
            tail = tail.next

        if l1:
            tail.next = l1
        elif l2: 
            tail.next = l2

        return dummy.next





# class ListNode():
#     def __init__(self,val=0,next=None):
#         self.val=val
#         self.next = next


# class Solution1:
#     def mergeTwoSortedLists(self,l1,l2):
#         dummy = ListNode()
#         tail = dummy
#         # tail is our solution
#         # while list1 and list2 are not null
#         while l1 and l2:
#             if l1.val < l2.val: 
#                 tail.next = l1
#                 l1 = l1.next
#             else:
#                 tail.next = l2
#                 l2 = l2.next
#             tail = tail.next
        
#         if l1:
#             tail.next = l1
#         if l2:
#             tail.next = l2

#         # returns head of the merged list
#         return dummy.next


# recursive solution

# class Solution:
#     def mergeTwoLists(self, l1, l2):
#         if l1 is None:
#             return l2
#         elif l2 is None:
#             return l1
#         elif l1.val < l2.val:
#             l1.next = self.mergeTwoLists(l1.next, l2)
#             return l1
#         else:
#             l2.next = self.mergeTwoLists(l1, l2.next)
#             return l2