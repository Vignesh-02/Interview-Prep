// Reverse a singly linked list

class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

// O(n) time and O(1) space
function reverseLinkedList(head) {
  let prev = null;
  let curr = head;

  while (curr) {
    const next = curr.next;
    curr.next = prev;
    prev = curr;
    curr = next;
  }

  return prev;
}

// O(n) time and O(n) space (recursion stack)
function reverseLinkedListRecursive(head) {
  if (!head || !head.next) return head;
  const newHead = reverseLinkedListRecursive(head.next);
  head.next.next = head;
  head.next = null;
  return newHead;
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

if (require.main === module) {
  const head = buildList([1, 2, 3, 4, 5]);
  const reversed = reverseLinkedList(head);
  console.log(listToArray(reversed));
}

module.exports = {
  ListNode,
  buildList,
  listToArray,
  reverseLinkedList,
  reverseLinkedListRecursive,
};
