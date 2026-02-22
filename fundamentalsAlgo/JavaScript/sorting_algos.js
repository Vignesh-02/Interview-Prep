/*
Comprehensive Sorting Algorithms Implementation
All algorithms sort in-place or return a new sorted array
*/

// ============================================================================
// 1. BUBBLE SORT
// ============================================================================
// Time Complexity: O(n^2) - best, average, worst
// Space Complexity: O(1) - in-place
// Stable: Yes
function bubbleSort(arr) {
  // Repeatedly steps through the list, compares adjacent elements and swaps them
  // if they are in the wrong order.
  const a = arr.slice();
  const n = a.length;

  for (let i = 0; i < n; i += 1) {
    let swapped = false;
    for (let j = 0; j < n - i - 1; j += 1) {
      if (a[j] > a[j + 1]) {
        const temp = a[j];
        a[j] = a[j + 1];
        a[j + 1] = temp;
        swapped = true;
      }
    }
    if (!swapped) break;
  }

  return a;
}

// ============================================================================
// 2. SELECTION SORT
// ============================================================================
// Time Complexity: O(n^2) - best, average, worst
// Space Complexity: O(1) - in-place
// Stable: No
function selectionSort(arr) {
  // Finds the minimum element and places it at the beginning.
  // Repeats for remaining unsorted portion.
  const a = arr.slice();
  const n = a.length;

  for (let i = 0; i < n; i += 1) {
    let minIdx = i;
    for (let j = i + 1; j < n; j += 1) {
      if (a[j] < a[minIdx]) minIdx = j;
    }
    const temp = a[i];
    a[i] = a[minIdx];
    a[minIdx] = temp;
  }

  return a;
}

// ============================================================================
// 3. INSERTION SORT
// ============================================================================
// Time Complexity: O(n) - best, O(n^2) - average, worst
// Space Complexity: O(1) - in-place
// Stable: Yes
function insertionSort(arr) {
  // Builds the sorted array one item at a time by inserting each element
  // into its correct position in the sorted portion.
  const a = arr.slice();

  for (let i = 1; i < a.length; i += 1) {
    const key = a[i];
    let j = i - 1;
    while (j >= 0 && a[j] > key) {
      a[j + 1] = a[j];
      j -= 1;
    }
    a[j + 1] = key;
  }

  return a;
}

// ============================================================================
// 4. MERGE SORT
// ============================================================================
// Time Complexity: O(n log n) - best, average, worst
// Space Complexity: O(n) - requires temporary array
// Stable: Yes
function mergeSort(arr) {
  if (arr.length <= 1) return arr;
  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid));
  const right = mergeSort(arr.slice(mid));
  return merge(left, right);
}

function merge(left, right) {
  const result = [];
  let i = 0;
  let j = 0;

  while (i < left.length && j < right.length) {
    if (left[i] <= right[j]) {
      result.push(left[i]);
      i += 1;
    } else {
      result.push(right[j]);
      j += 1;
    }
  }

  return result.concat(left.slice(i)).concat(right.slice(j));
}

// ============================================================================
// 5. QUICK SORT
// ============================================================================
// Time Complexity: O(n log n) - best, average, O(n^2) - worst
// Space Complexity: O(log n) average (recursion), O(n) worst
// Stable: No
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = [];
  const middle = [];
  const right = [];

  for (const x of arr) {
    if (x < pivot) left.push(x);
    else if (x > pivot) right.push(x);
    else middle.push(x);
  }

  return quickSort(left).concat(middle, quickSort(right));
}

function quickSortInPlace(arr, low = 0, high = arr.length - 1) {
  if (low < high) {
    const pivotIdx = partition(arr, low, high);
    quickSortInPlace(arr, low, pivotIdx - 1);
    quickSortInPlace(arr, pivotIdx + 1, high);
  }
  return arr;
}

function partition(arr, low, high) {
  const pivot = arr[high];
  let i = low - 1;

  for (let j = low; j < high; j += 1) {
    if (arr[j] <= pivot) {
      i += 1;
      const temp = arr[i];
      arr[i] = arr[j];
      arr[j] = temp;
    }
  }

  const temp = arr[i + 1];
  arr[i + 1] = arr[high];
  arr[high] = temp;
  return i + 1;
}

// ============================================================================
// 6. HEAP SORT
// ============================================================================
// Time Complexity: O(n log n) - best, average, worst
// Space Complexity: O(1) - in-place
// Stable: No
function heapSort(arr) {
  const a = arr.slice();
  const n = a.length;

  for (let i = Math.floor(n / 2) - 1; i >= 0; i -= 1) {
    heapify(a, n, i);
  }

  for (let i = n - 1; i > 0; i -= 1) {
    const temp = a[0];
    a[0] = a[i];
    a[i] = temp;
    heapify(a, i, 0);
  }

  return a;
}

function heapify(arr, n, i) {
  let largest = i;
  const left = 2 * i + 1;
  const right = 2 * i + 2;

  if (left < n && arr[left] > arr[largest]) largest = left;
  if (right < n && arr[right] > arr[largest]) largest = right;

  if (largest !== i) {
    const temp = arr[i];
    arr[i] = arr[largest];
    arr[largest] = temp;
    heapify(arr, n, largest);
  }
}

// ============================================================================
// 7. COUNTING SORT
// ============================================================================
// Time Complexity: O(n + k) where k is range of input
// Space Complexity: O(k)
// Stable: Yes
function countingSort(arr) {
  if (!arr.length) return [];

  const minVal = Math.min(...arr);
  const maxVal = Math.max(...arr);
  const rangeSize = maxVal - minVal + 1;

  const count = new Array(rangeSize).fill(0);
  for (const num of arr) {
    count[num - minVal] += 1;
  }

  const output = [];
  for (let i = 0; i < rangeSize; i += 1) {
    for (let c = 0; c < count[i]; c += 1) {
      output.push(i + minVal);
    }
  }

  return output;
}

// ============================================================================
// 8. RADIX SORT
// ============================================================================
// Time Complexity: O(d * (n + k)) where d is number of digits, k is base (10)
// Space Complexity: O(n + k)
// Stable: Yes
function radixSort(arr) {
  if (!arr.length) return [];
  const a = arr.slice();
  let maxNum = Math.max(...a);
  let exp = 1;
  while (Math.floor(maxNum / exp) > 0) {
    countingSortByDigit(a, exp);
    exp *= 10;
  }
  return a;
}

function countingSortByDigit(arr, exp) {
  const n = arr.length;
  const output = new Array(n).fill(0);
  const count = new Array(10).fill(0);

  for (let i = 0; i < n; i += 1) {
    const index = Math.floor(arr[i] / exp) % 10;
    count[index] += 1;
  }

  for (let i = 1; i < 10; i += 1) {
    count[i] += count[i - 1];
  }

  for (let i = n - 1; i >= 0; i -= 1) {
    const index = Math.floor(arr[i] / exp) % 10;
    output[count[index] - 1] = arr[i];
    count[index] -= 1;
  }

  for (let i = 0; i < n; i += 1) {
    arr[i] = output[i];
  }
}

// ============================================================================
// 9. BUCKET SORT
// ============================================================================
// Time Complexity: O(n) average, O(n^2) worst
// Space Complexity: O(n)
// Stable: Yes (when using stable sort for buckets)
function bucketSort(arr, numBuckets = null) {
  if (!arr.length) return [];
  const bucketsCount = numBuckets == null ? arr.length : numBuckets;

  const minVal = Math.min(...arr);
  const maxVal = Math.max(...arr);
  if (minVal === maxVal) return arr.slice();

  const buckets = Array.from({ length: bucketsCount }, () => []);
  const bucketRange = (maxVal - minVal) / bucketsCount;

  for (const num of arr) {
    let idx = Math.floor((num - minVal) / bucketRange);
    if (idx === bucketsCount) idx = bucketsCount - 1;
    buckets[idx].push(num);
  }

  const result = [];
  for (const bucket of buckets) {
    bucket.sort((a, b) => a - b);
    result.push(...bucket);
  }

  return result;
}

// ============================================================================
// TESTING & COMPARISON
// ============================================================================
if (require.main === module) {
  const testArrays = [
    [64, 34, 25, 12, 22, 11, 90],
    [5, 2, 8, 1, 9],
    [1, 2, 3, 4, 5],
    [5, 4, 3, 2, 1],
    [42],
    [],
  ];

  const sortingFunctions = {
    "Bubble Sort": bubbleSort,
    "Selection Sort": selectionSort,
    "Insertion Sort": insertionSort,
    "Merge Sort": mergeSort,
    "Quick Sort": quickSort,
    "Heap Sort": heapSort,
    "Counting Sort": countingSort,
    "Radix Sort": radixSort,
    "Bucket Sort": bucketSort,
  };

  console.log("=".repeat(70));
  console.log("SORTING ALGORITHMS TEST");
  console.log("=".repeat(70));

  for (const testArr of testArrays) {
    console.log(`\nOriginal: ${JSON.stringify(testArr)}`);
    for (const [name, func] of Object.entries(sortingFunctions)) {
      try {
        const result = func(testArr.slice());
        console.log(`${name.padEnd(20, " ")}: ${JSON.stringify(result)}`);
      } catch (e) {
        console.log(`${name.padEnd(20, " ")}: ERROR - ${e.message}`);
      }
    }
  }
}

module.exports = {
  bubbleSort,
  selectionSort,
  insertionSort,
  mergeSort,
  quickSort,
  quickSortInPlace,
  heapSort,
  countingSort,
  radixSort,
  bucketSort,
};
