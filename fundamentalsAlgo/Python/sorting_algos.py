"""
Comprehensive Sorting Algorithms Implementation
All algorithms sort in-place or return a new sorted array
"""


# ============================================================================
# 1. BUBBLE SORT
# ============================================================================
# Time Complexity: O(n²) - best, average, worst
# Space Complexity: O(1) - in-place
# Stable: Yes
def bubble_sort(arr):
    """
    Repeatedly steps through the list, compares adjacent elements and swaps them
    if they are in the wrong order.
    """
    n = len(arr)
    arr = arr.copy()  # Don't modify original
    
    for i in range(n):
        swapped = False
        # Last i elements are already in place
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        
        # If no swapping occurred, array is sorted
        if not swapped:
            break
    
    return arr


# ============================================================================
# 2. SELECTION SORT
# ============================================================================
# Time Complexity: O(n²) - best, average, worst
# Space Complexity: O(1) - in-place
# Stable: No
def selection_sort(arr):
    """
    Finds the minimum element and places it at the beginning.
    Repeats for remaining unsorted portion.
    """
    n = len(arr)
    arr = arr.copy()
    
    for i in range(n):
        # Find minimum element in remaining unsorted array
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        
        # Swap the found minimum with the first element
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    
    return arr


# ============================================================================
# 3. INSERTION SORT
# ============================================================================
# Time Complexity: O(n) - best (already sorted), O(n²) - average, worst
# Space Complexity: O(1) - in-place
# Stable: Yes
def insertion_sort(arr):
    """
    Builds the sorted array one item at a time by inserting each element
    into its correct position in the sorted portion.
    """
    arr = arr.copy()
    
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        
        # Move elements greater than key one position ahead
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        
        arr[j + 1] = key
    
    return arr


# ============================================================================
# 4. MERGE SORT
# ============================================================================
# Time Complexity: O(n log n) - best, average, worst
# Space Complexity: O(n) - requires temporary array
# Stable: Yes
def merge_sort(arr):
    """
    Divide and conquer: divides array into halves, sorts them, then merges.
    """
    if len(arr) <= 1:
        return arr
    
    # Divide
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    # Conquer (merge)
    return merge(left, right)


def merge(left, right):
    """Helper function to merge two sorted arrays."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Add remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result


# ============================================================================
# 5. QUICK SORT
# ============================================================================
# Time Complexity: O(n log n) - best, average, O(n²) - worst (rare)
# Space Complexity: O(log n) - average (recursion stack), O(n) - worst
# Stable: No (typical implementation)
def quick_sort(arr):
    """
    Divide and conquer: picks a pivot, partitions array around pivot,
    then recursively sorts sub-arrays.
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)


def quick_sort_in_place(arr, low=0, high=None):
    """
    In-place version of quicksort using Lomuto partition scheme.
    More memory efficient.
    """
    if high is None:
        high = len(arr) - 1
    
    if low < high:
        # Partition and get pivot index
        pivot_idx = partition(arr, low, high)
        
        # Recursively sort elements before and after partition
        quick_sort_in_place(arr, low, pivot_idx - 1)
        quick_sort_in_place(arr, pivot_idx + 1, high)
    
    return arr


def partition(arr, low, high):
    """Lomuto partition scheme - places pivot at correct position."""
    pivot = arr[high]
    i = low - 1  # Index of smaller element
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


# ============================================================================
# 6. HEAP SORT
# ============================================================================
# Time Complexity: O(n log n) - best, average, worst
# Space Complexity: O(1) - in-place
# Stable: No
def heap_sort(arr):
    """
    Builds a max heap, then repeatedly extracts the maximum element
    and places it at the end of the sorted portion.
    """
    n = len(arr)
    arr = arr.copy()
    
    # Build max heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # Extract elements from heap one by one
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]  # Move root to end
        heapify(arr, i, 0)  # Heapify reduced heap
    
    return arr


def heapify(arr, n, i):
    """Maintains heap property: parent >= children."""
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    # Check if left child exists and is greater than root
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    # Check if right child exists and is greater than root
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    # If largest is not root, swap and continue heapifying
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


# ============================================================================
# 7. COUNTING SORT
# ============================================================================
# Time Complexity: O(n + k) where k is range of input
# Space Complexity: O(k) - requires count array
# Stable: Yes
def counting_sort(arr):
    """
    Sorts by counting occurrences of each element.
    Works best when range of input values is small.
    """
    if not arr:
        return []
    
    # Find range of input values
    min_val = min(arr)
    max_val = max(arr)
    range_size = max_val - min_val + 1
    
    # Count occurrences
    count = [0] * range_size
    for num in arr:
        count[num - min_val] += 1
    
    # Build output array
    output = []
    for i in range(range_size):
        output.extend([i + min_val] * count[i])
    
    return output


# ============================================================================
# 8. RADIX SORT
# ============================================================================
# Time Complexity: O(d * (n + k)) where d is number of digits, k is base (10)
# Space Complexity: O(n + k)
# Stable: Yes
def radix_sort(arr):
    """
    Sorts by processing digits from least significant to most significant.
    Uses counting sort as a subroutine for each digit.
    """
    if not arr:
        return []
    
    arr = arr.copy()
    
    # Find maximum number to know number of digits
    max_num = max(arr)
    
    # Do counting sort for every digit
    exp = 1
    while max_num // exp > 0:
        counting_sort_by_digit(arr, exp)
        exp *= 10
    
    return arr


def counting_sort_by_digit(arr, exp):
    """Counting sort for a specific digit position."""
    n = len(arr)
    output = [0] * n
    count = [0] * 10
    
    # Count occurrences of each digit
    for i in range(n):
        index = (arr[i] // exp) % 10
        count[index] += 1
    
    # Change count so it contains actual position
    for i in range(1, 10):
        count[i] += count[i - 1]
    
    # Build output array
    for i in range(n - 1, -1, -1):
        index = (arr[i] // exp) % 10
        output[count[index] - 1] = arr[i]
        count[index] -= 1
    
    # Copy output to original array
    for i in range(n):
        arr[i] = output[i]


# ============================================================================
# 9. BUCKET SORT
# ============================================================================
# Time Complexity: O(n) - average, O(n²) - worst
# Space Complexity: O(n)
# Stable: Yes (when using stable sort for buckets)
def bucket_sort(arr, num_buckets=None):
    """
    Distributes elements into buckets, sorts each bucket, then concatenates.
    Works best when input is uniformly distributed.
    """
    if not arr:
        return []
    
    if num_buckets is None:
        num_buckets = len(arr)
    
    # Find min and max values
    min_val = min(arr)
    max_val = max(arr)
    
    if min_val == max_val:
        return arr.copy()
    
    # Create empty buckets
    buckets = [[] for _ in range(num_buckets)]
    
    # Distribute array elements into buckets
    bucket_range = (max_val - min_val) / num_buckets
    for num in arr:
        bucket_idx = int((num - min_val) / bucket_range)
        # Handle edge case for max value
        if bucket_idx == num_buckets:
            bucket_idx = num_buckets - 1
        buckets[bucket_idx].append(num)
    
    # Sort each bucket and concatenate
    result = []
    for bucket in buckets:
        result.extend(sorted(bucket))  # Using built-in sort for buckets
    
    return result


# ============================================================================
# TESTING & COMPARISON
# ============================================================================
if __name__ == "__main__":
    # Test arrays
    test_arrays = [
        [64, 34, 25, 12, 22, 11, 90],
        [5, 2, 8, 1, 9],
        [1, 2, 3, 4, 5],  # Already sorted
        [5, 4, 3, 2, 1],  # Reverse sorted
        [42],  # Single element
        [],  # Empty array
    ]
    
    sorting_functions = {
        "Bubble Sort": bubble_sort,
        "Selection Sort": selection_sort,
        "Insertion Sort": insertion_sort,
        "Merge Sort": merge_sort,
        "Quick Sort": quick_sort,
        "Heap Sort": heap_sort,
        "Counting Sort": counting_sort,
        "Radix Sort": radix_sort,
        "Bucket Sort": bucket_sort,
    }
    
    print("=" * 70)
    print("SORTING ALGORITHMS TEST")
    print("=" * 70)
    
    for test_arr in test_arrays:
        print(f"\nOriginal: {test_arr}")
        for name, func in sorting_functions.items():
            try:
                result = func(test_arr.copy() if test_arr else [])
                print(f"  {name:20s}: {result}")
            except Exception as e:
                print(f"  {name:20s}: ERROR - {e}")
    
    print("\n" + "=" * 70)
    print("COMPLEXITY SUMMARY")
    print("=" * 70)
    print("""
    Algorithm          | Best      | Average   | Worst     | Space    | Stable
    -------------------|-----------|-----------|-----------|----------|--------
    Bubble Sort        | O(n²)     | O(n²)     | O(n²)     | O(1)     | Yes
    Selection Sort     | O(n²)     | O(n²)     | O(n²)     | O(1)     | No
    Insertion Sort     | O(n)      | O(n²)     | O(n²)     | O(1)     | Yes
    Merge Sort         | O(n log n)| O(n log n)| O(n log n)| O(n)     | Yes
    Quick Sort         | O(n log n)| O(n log n)| O(n²)     | O(log n) | No
    Heap Sort          | O(n log n)| O(n log n)| O(n log n)| O(1)     | No
    Counting Sort      | O(n + k)  | O(n + k)  | O(n + k)  | O(k)     | Yes
    Radix Sort         | O(d * n)  | O(d * n)  | O(d * n)  | O(n + k) | Yes
    Bucket Sort        | O(n)      | O(n)      | O(n²)     | O(n)     | Yes
    """)