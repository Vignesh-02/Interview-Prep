"""
Add Two Numbers (LeetCode #2)

Problem:
You are given two non-empty linked lists representing two non-negative integers.
The digits are stored in reverse order, and each node contains a single digit.
Add the two numbers and return the sum as a linked list.

Example:
Input:  l1 = 2 -> 4 -> 3  (342)
        l2 = 5 -> 6 -> 4  (465)
Output: 7 -> 0 -> 8       (807)
"""

from typing import Optional, List


class ListNode:
    def __init__(self, val: int = 0, next: Optional["ListNode"] = None):
        self.val = val
        self.next = next

    def __repr__(self) -> str:
        return f"ListNode({self.val})"


def build_list(values: List[int]) -> Optional[ListNode]:
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if not head:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head


def list_to_pylist(head: Optional[ListNode]) -> List[int]:
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


def add_two_numbers_bruteforce(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    """
    Brute force approach:
    1) Convert both linked lists into integers.
    2) Add them.
    3) Convert the sum back into a linked list.

    Time:  O(n + m)
    Space: O(n + m)
    """
    def to_int(node: Optional[ListNode]) -> int:
        place = 1
        value = 0
        while node:
            value += node.val * place
            place *= 10
            node = node.next
        return value

    def to_list(number: int) -> Optional[ListNode]:
        if number == 0:
            return ListNode(0)
        head = None
        tail = None
        while number > 0:
            digit = number % 10
            node = ListNode(digit)
            if not head:
                head = node
                tail = node
            else:
                tail.next = node
                tail = node
            number //= 10
        return head

    total = to_int(l1) + to_int(l2)
    return to_list(total)


# Explanation (Brute Force):
# We read each list as a base-10 number (because the digits are reversed),
# add them, and then rebuild a linked list from the sum.
# Example: l1 = 2->4->3 => 342, l2 = 5->6->4 => 465, sum = 807 => 7->0->8.
# Time Complexity: O(n + m)
# Space Complexity: O(n + m)


def add_two_numbers_optimized(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    """
    Optimized approach (digit-by-digit with carry):
    Traverse both lists simultaneously, add digits and carry, build the result list.

    Time:  O(n + m)
    Space: O(1) extra (not counting output list)
    """
    dummy = ListNode(0)
    tail = dummy
    carry = 0

    while l1 or l2 or carry:
        x = l1.val if l1 else 0
        y = l2.val if l2 else 0
        total = x + y + carry
        carry = total // 10
        digit = total % 10
        tail.next = ListNode(digit)
        tail = tail.next
        if l1:
            l1 = l1.next
        if l2:
            l2 = l2.next

    return dummy.next


# Explanation (Optimized):
# This simulates manual addition. At each digit, we add the two digits plus carry,
# store the new digit, and carry forward any overflow.
# Example: (2->4->3) + (5->6->4)
# 2+5=7 carry0, 4+6=10 => digit0 carry1, 3+4+1=8 => digit8.
# Time Complexity: O(n + m)
# Space Complexity: O(1) extra (output list not counted)


if __name__ == "__main__":
    l1 = build_list([2, 4, 3])
    l2 = build_list([5, 6, 4])

    brute = add_two_numbers_bruteforce(l1, l2)
    opt = add_two_numbers_optimized(l1, l2)

    print("Brute force result:", list_to_pylist(brute))
    print("Optimized result:", list_to_pylist(opt))
