/*
Add Two Numbers (LeetCode #2)

Problem:
You are given two non-empty linked lists representing two non-negative integers.
The digits are stored in reverse order, and each node contains a single digit.
Add the two numbers and return the sum as a linked list.

Example:
Input:  l1 = 2 -> 4 -> 3  (342)
        l2 = 5 -> 6 -> 4  (465)
Output: 7 -> 0 -> 8       (807)
*/

class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

function buildList(values) {
  let head = null;
  let tail = null;
  for (const v of values) {
    const node = new ListNode(v);
    if (!head) {
      head = node;
      tail = node;
    } else {
      tail.next = node;
      tail = node;
    }
  }
  return head;
}

function listToArray(head) {
  const out = [];
  let curr = head;
  while (curr) {
    out.push(curr.val);
    curr = curr.next;
  }
  return out;
}

function addTwoNumbersBruteforce(l1, l2) {
  /*
  Brute force approach:
  1) Convert both linked lists into integers.
  2) Add them.
  3) Convert the sum back into a linked list.

  Time:  O(n + m)
  Space: O(n + m)
  */
  function toInt(node) {
    let place = 1;
    let value = 0;
    let curr = node;
    while (curr) {
      value += curr.val * place;
      place *= 10;
      curr = curr.next;
    }
    return value;
  }

  function toList(number) {
    if (number === 0) return new ListNode(0);
    let head = null;
    let tail = null;
    let n = number;
    while (n > 0) {
      const digit = n % 10;
      const node = new ListNode(digit);
      if (!head) {
        head = node;
        tail = node;
      } else {
        tail.next = node;
        tail = node;
      }
      n = Math.floor(n / 10);
    }
    return head;
  }

  const total = toInt(l1) + toInt(l2);
  return toList(total);
}

// Explanation (Brute Force):
// We read each list as a base-10 number (because the digits are reversed),
// add them, and then rebuild a linked list from the sum.
// Example: l1 = 2->4->3 => 342, l2 = 5->6->4 => 465, sum = 807 => 7->0->8.
// Time Complexity: O(n + m)
// Space Complexity: O(n + m)

function addTwoNumbersOptimized(l1, l2) {
  /*
  Optimized approach (digit-by-digit with carry):
  Traverse both lists simultaneously, add digits and carry, build the result list.

  Time:  O(n + m)
  Space: O(1) extra (not counting output list)
  */
  const dummy = new ListNode(0);
  let tail = dummy;
  let carry = 0;
  let a = l1;
  let b = l2;

  while (a || b || carry) {
    const x = a ? a.val : 0;
    const y = b ? b.val : 0;
    const total = x + y + carry;
    carry = Math.floor(total / 10);
    const digit = total % 10;
    tail.next = new ListNode(digit);
    tail = tail.next;
    if (a) a = a.next;
    if (b) b = b.next;
  }

  return dummy.next;
}

// Explanation (Optimized):
// This simulates manual addition. At each digit, we add the two digits plus carry,
// store the new digit, and carry forward any overflow.
// Example: (2->4->3) + (5->6->4)
// 2+5=7 carry0, 4+6=10 => digit0 carry1, 3+4+1=8 => digit8.
// Time Complexity: O(n + m)
// Space Complexity: O(1) extra (output list not counted)

if (require.main === module) {
  const l1 = buildList([2, 4, 3]);
  const l2 = buildList([5, 6, 4]);

  const brute = addTwoNumbersBruteforce(l1, l2);
  const opt = addTwoNumbersOptimized(l1, l2);

  console.log("Brute force result:", listToArray(brute));
  console.log("Optimized result:", listToArray(opt));
}

module.exports = {
  ListNode,
  buildList,
  listToArray,
  addTwoNumbersBruteforce,
  addTwoNumbersOptimized,
};
