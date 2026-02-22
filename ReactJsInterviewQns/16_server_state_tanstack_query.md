# Server State & TanStack Query (React Query) — React 18 Interview Questions

## Topic Introduction

**Server state** is fundamentally different from **client state**. Client state — things like whether a modal is open, the current theme, or the value of a form input — is ephemeral, synchronous, and fully owned by the browser. Server state, on the other hand, is **persisted remotely**, is **asynchronous** by nature, and is **shared** — meaning another user or process can change it without your knowledge at any time. The moment you fetch data from an API and store it in a `useState` or Redux slice, you are holding a **snapshot** that may already be stale. This distinction is critical because it means server state has challenges that client state simply does not: caching, background refetching, deduplication, pagination, optimistic updates, retry logic, garbage collection, and offline support. Treating server state like client state (the classic `useEffect` + `useState` + `isLoading` pattern) inevitably leads to duplicated boilerplate, race conditions, waterfalls, and bugs that are hard to reproduce. React 18's concurrent features (Suspense, transitions, automatic batching) amplify both the opportunities and the pitfalls of data fetching, making a dedicated server-state library essential for production applications.

**TanStack Query** (formerly React Query, now framework-agnostic under the TanStack umbrella) is the de-facto standard for managing server state in React 18 applications. At its core, it provides a **smart, observable cache** keyed by structured query keys. When a component calls `useQuery`, TanStack Query first checks the cache — if fresh data exists it returns it immediately (zero-latency UI), while simultaneously deciding whether to refetch in the background based on configurable staleness thresholds. It handles loading, error, and success states out of the box; deduplicates identical in-flight requests; retries failed requests with exponential backoff; garbage-collects unused cache entries; and provides `useMutation` with hooks for optimistic updates and automatic query invalidation. Combined with React 18's `Suspense` and streaming SSR, TanStack Query enables architectures where pages feel instant — data is prefetched on the server, hydrated on the client, and kept fresh transparently. It replaces hundreds of lines of hand-rolled data-fetching code with a declarative, composable API that scales from a simple todo app to a complex SaaS dashboard with dozens of interdependent data sources.

```jsx
// A taste of TanStack Query in React 18 — replacing useEffect + useState
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function TodoList() {
  const queryClient = useQueryClient();

  // Fetch todos — handles loading, error, caching, refetching automatically
  const { data: todos, isLoading, error } = useQuery({
    queryKey: ['todos'],
    queryFn: () => fetch('/api/todos').then(res => res.json()),
    staleTime: 30_000, // data stays fresh for 30 seconds
  });

  // Create todo — with automatic cache invalidation
  const addTodo = useMutation({
    mutationFn: (newTodo) =>
      fetch('/api/todos', {
        method: 'POST',
        body: JSON.stringify(newTodo),
        headers: { 'Content-Type': 'application/json' },
      }).then(res => res.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <ul>
      {todos.map(todo => (
        <li key={todo.id}>{todo.title}</li>
      ))}
    </ul>
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is server state, and why should it be managed separately from client state?

**Answer:**

**Server state** is any data that originates from and is persisted on a remote server — database records, API responses, user profiles, product catalogs, etc. **Client state** is data that lives entirely in the browser — UI toggles, form inputs, theme preferences, route parameters.

They should be managed separately because they have fundamentally different characteristics:

| Characteristic | Client State | Server State |
|---|---|---|
| **Ownership** | Fully controlled by the browser | Controlled by the server; shared across users |
| **Persistence** | Ephemeral (lost on refresh unless stored) | Persisted in a database |
| **Synchronicity** | Synchronous — you set it, it updates instantly | Asynchronous — requires network requests |
| **Staleness** | Always "fresh" (you are the source of truth) | Can become stale at any moment (someone else may have changed it) |
| **Complexity** | Simple get/set | Requires caching, refetching, deduplication, retry, pagination |

When you mix them (e.g., storing API responses in Redux alongside UI state), you end up writing enormous amounts of boilerplate for loading/error states, cache invalidation, and request deduplication — and you still miss edge cases like stale data, race conditions, and background refetching.

```jsx
// ❌ The old way — mixing server state into client state with useEffect + useState
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => {
        if (!cancelled) {
          setUser(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err);
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [userId]);

  // No caching, no refetching, no deduplication, race-condition-prone
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <div>{user.name}</div>;
}

// ✅ The modern way — TanStack Query manages server state
function UserProfile({ userId }) {
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['users', userId],
    queryFn: () => fetch(`/api/users/${userId}`).then(res => res.json()),
  });

  // Caching, deduplication, background refetching, retries — all automatic
  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <div>{user.name}</div>;
}
```

The `useQuery` version is shorter, safer, and far more capable. If two components mount with the same `userId`, TanStack Query makes **one** network request and shares the result. It retries on failure, refetches when the window regains focus, and serves cached data instantly while refreshing in the background.

---

### Q2. How does `useQuery` work — explain queryKey, queryFn, and the loading/error/success states?

**Answer:**

`useQuery` is the primary hook for **reading** (GET) server data. It accepts a configuration object with two required properties and many optional ones:

- **`queryKey`**: A serializable array that **uniquely identifies** this piece of server data in the cache. TanStack Query uses structural equality to match keys. If the key changes, it triggers a new fetch. Think of it as the "address" of data in the cache.
- **`queryFn`**: An async function that **actually fetches** the data. It receives a context object containing the `queryKey`, an `AbortSignal` for cancellation, and metadata. It must return data or throw an error.

The hook returns a rich result object with three mutually exclusive states:

| State | `isLoading` | `isError` | `isSuccess` | Description |
|---|---|---|---|---|
| Loading | `true` | `false` | `false` | First fetch, no cached data yet |
| Error | `false` | `true` | `false` | Fetch failed (after retries) |
| Success | `false` | `false` | `true` | Data available |

Additionally, `isFetching` is `true` whenever **any** request is in flight — including background refetches when `isSuccess` is already `true`. This distinction lets you show a subtle spinner for background updates without hiding the existing data.

```jsx
import { useQuery } from '@tanstack/react-query';

// API function — keep it separate for reuse and testing
async function fetchProducts(categoryId) {
  const response = await fetch(`/api/products?category=${categoryId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch products: ${response.status}`);
  }
  return response.json();
}

function ProductList({ categoryId }) {
  const {
    data: products,
    isLoading,       // true on first load only (no cached data)
    isFetching,      // true whenever a request is in-flight (includes bg refetch)
    isError,
    error,
    isSuccess,
    refetch,         // manual refetch trigger
  } = useQuery({
    queryKey: ['products', { categoryId }],  // changes when categoryId changes
    queryFn: () => fetchProducts(categoryId),
    staleTime: 60_000,    // data considered fresh for 60s
    retry: 2,             // retry failed requests twice
    refetchOnWindowFocus: true, // refetch when user tabs back (default)
  });

  if (isLoading) {
    return <ProductSkeleton count={8} />;
  }

  if (isError) {
    return (
      <div className="error">
        <p>Something went wrong: {error.message}</p>
        <button onClick={() => refetch()}>Try Again</button>
      </div>
    );
  }

  return (
    <div>
      {/* Subtle indicator for background refetch — data is still visible */}
      {isFetching && <div className="bg-refresh-bar" />}

      <div className="product-grid">
        {products.map(product => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}
```

**Key insight**: `isLoading` is `true` only when there is **no cached data** and a fetch is in progress (hard loading). When the user navigates away and comes back, TanStack Query serves cached data instantly (`isSuccess` is `true`) while refetching in the background (`isFetching` is `true`). This is what makes the UI feel instant.

---

### Q3. What is `useMutation` and how do you use it to create, update, or delete data?

**Answer:**

While `useQuery` is for **reading** data, `useMutation` is for **writing** data — POST, PUT, PATCH, DELETE operations that change server state. Unlike queries, mutations:

- Are **not cached** in the query cache.
- Are **not automatic** — they execute only when you call the `mutate()` or `mutateAsync()` function.
- Provide lifecycle callbacks: `onMutate`, `onSuccess`, `onError`, and `onSettled` — which are essential for optimistic updates and cache invalidation.

The hook returns a `mutate` function plus status flags similar to `useQuery` (`isLoading`/`isPending`, `isError`, `isSuccess`).

```jsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

// API functions
const createTask = (task) =>
  fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  }).then(res => {
    if (!res.ok) throw new Error('Failed to create task');
    return res.json();
  });

const updateTask = ({ id, ...updates }) =>
  fetch(`/api/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  }).then(res => {
    if (!res.ok) throw new Error('Failed to update task');
    return res.json();
  });

const deleteTask = (id) =>
  fetch(`/api/tasks/${id}`, { method: 'DELETE' }).then(res => {
    if (!res.ok) throw new Error('Failed to delete task');
  });

function TaskManager({ projectId }) {
  const queryClient = useQueryClient();

  // CREATE
  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: (newTask) => {
      // Invalidate the tasks list so it refetches with the new task
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
    },
    onError: (error) => {
      toast.error(`Create failed: ${error.message}`);
    },
  });

  // UPDATE
  const updateMutation = useMutation({
    mutationFn: updateTask,
    onSuccess: (updatedTask) => {
      // Update the specific task in cache directly (no refetch needed)
      queryClient.setQueryData(
        ['tasks', projectId],
        (oldTasks) => oldTasks.map(t => t.id === updatedTask.id ? updatedTask : t)
      );
    },
  });

  // DELETE
  const deleteMutation = useMutation({
    mutationFn: deleteTask,
    onSuccess: (_, deletedId) => {
      queryClient.setQueryData(
        ['tasks', projectId],
        (oldTasks) => oldTasks.filter(t => t.id !== deletedId)
      );
    },
  });

  const handleCreate = () => {
    createMutation.mutate({
      title: 'New Task',
      projectId,
      status: 'todo',
    });
  };

  const handleToggle = (task) => {
    updateMutation.mutate({
      id: task.id,
      status: task.status === 'done' ? 'todo' : 'done',
    });
  };

  const handleDelete = (taskId) => {
    deleteMutation.mutate(taskId);
  };

  return (
    <div>
      <button onClick={handleCreate} disabled={createMutation.isPending}>
        {createMutation.isPending ? 'Creating…' : 'Add Task'}
      </button>

      {/* Task list rendering with update/delete handlers */}
      {tasks.map(task => (
        <div key={task.id}>
          <span>{task.title}</span>
          <button onClick={() => handleToggle(task)}>Toggle</button>
          <button onClick={() => handleDelete(task.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
}
```

**Pro tip**: Use `mutateAsync` when you need to `await` the result in an event handler (e.g., to navigate after creation). Use `mutate` when you just want fire-and-forget with callbacks.

---

### Q4. What is query invalidation and why is it central to the TanStack Query workflow?

**Answer:**

**Query invalidation** is the mechanism by which you tell TanStack Query that certain cached data is **no longer reliable** and should be refetched. When you call `queryClient.invalidateQueries(...)`, TanStack Query marks matching queries as **stale** and, if any component is currently observing that query, triggers an automatic background refetch.

This is the glue between mutations and queries — the standard pattern is:

1. User performs a mutation (create, update, delete).
2. Mutation succeeds.
3. In `onSuccess`, invalidate the related queries.
4. TanStack Query automatically refetches, and the UI updates with fresh server data.

This is **dramatically simpler** and more correct than manually updating cache state for every possible mutation, because the server is always the source of truth.

```jsx
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

function CommentSection({ postId }) {
  const queryClient = useQueryClient();

  // Fetch comments
  const { data: comments } = useQuery({
    queryKey: ['posts', postId, 'comments'],
    queryFn: () => fetch(`/api/posts/${postId}/comments`).then(r => r.json()),
  });

  // Add a comment
  const addComment = useMutation({
    mutationFn: (text) =>
      fetch(`/api/posts/${postId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      }).then(r => r.json()),

    onSuccess: () => {
      // Invalidate comments list — triggers refetch
      queryClient.invalidateQueries({
        queryKey: ['posts', postId, 'comments'],
      });

      // Also invalidate the post itself (comment count may have changed)
      queryClient.invalidateQueries({
        queryKey: ['posts', postId],
      });

      // Invalidate ALL posts (if the list shows comment counts)
      // The `exact` option controls matching precision
      queryClient.invalidateQueries({
        queryKey: ['posts'],
        // Without `exact: true`, this matches any key that STARTS with ['posts']
      });
    },
  });

  // Example: invalidation filters
  const handleBulkInvalidation = () => {
    // Invalidate everything that starts with ['posts']
    queryClient.invalidateQueries({ queryKey: ['posts'] });

    // Invalidate only the exact key ['posts'] — not ['posts', 1] etc.
    queryClient.invalidateQueries({ queryKey: ['posts'], exact: true });

    // Invalidate with a predicate function
    queryClient.invalidateQueries({
      predicate: (query) =>
        query.queryKey[0] === 'posts' &&
        query.state.dataUpdatedAt < Date.now() - 60_000,
    });

    // Nuclear option — invalidate everything
    queryClient.invalidateQueries();
  };

  return (
    <div>
      <CommentForm onSubmit={(text) => addComment.mutate(text)} />
      {comments?.map(c => <Comment key={c.id} comment={c} />)}
    </div>
  );
}
```

**Key matching behavior**: Query key matching is **hierarchical** (prefix-based by default). Invalidating `['posts']` will also invalidate `['posts', 1]`, `['posts', 1, 'comments']`, etc. Use `exact: true` if you want to match only the exact key.

---

### Q5. What is the difference between `staleTime` and `gcTime` (formerly `cacheTime`)?

**Answer:**

These two timers control different parts of the caching lifecycle and are the most commonly confused concepts in TanStack Query:

- **`staleTime`** (default: `0`): How long fetched data is considered **fresh**. While data is fresh, TanStack Query will **never** refetch — it serves the cached version directly. Once the stale time expires, the data is marked as **stale**, and TanStack Query will refetch in the background on certain triggers (window focus, component mount, interval, etc.).

- **`gcTime`** (default: `5 minutes`, formerly `cacheTime`): How long **inactive** (unobserved) data stays in the cache before being **garbage collected**. A query becomes inactive when no component is subscribed to it. Once `gcTime` expires, the cache entry is deleted entirely.

Think of it like food storage: `staleTime` is the "best before" date — still edible (servable) but you might want fresh. `gcTime` is the "throw away" date — the food (data) is discarded entirely.

```jsx
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';

// Configure defaults at the QueryClient level
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,   // 30s — data is fresh for 30 seconds
      gcTime: 5 * 60_000,  // 5min — unused cache entries survive 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}

// Timeline example:
// T=0s:  Component A mounts, fetches ['users']. Data is FRESH.
// T=10s: Component B mounts with same key. Data still FRESH → served from cache instantly.
//        No network request at all.
// T=35s: User navigates, Component A and B unmount. Data is now INACTIVE and STALE.
//        gcTime countdown begins (5 minutes).
// T=60s: User navigates back, Component A remounts.
//        Data is STALE but still in cache (gcTime hasn't expired).
//        → TanStack Query shows cached data IMMEDIATELY, refetches in background.
//        User sees instant content while fresh data loads.
// T=6min: If no component remounted, gcTime expired → cache entry is deleted.
// T=7min: Component mounts → hard loading state, full fetch, no cached data.

function UserList() {
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
    staleTime: 2 * 60_000,  // override: fresh for 2 minutes (data rarely changes)
    gcTime: 10 * 60_000,    // keep in cache for 10 minutes after unmount
  });

  return (
    <div>
      {/* isLoading = first load (no cache). isFetching = any refetch including bg */}
      {isLoading && <FullPageSpinner />}
      {!isLoading && isFetching && <TopBarProgress />}
      {data?.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
}

// Common staleTime strategies for different data types:
// Static reference data (countries, currencies): staleTime: Infinity
// User profile: staleTime: 5 * 60_000 (5 min)
// Dashboard metrics: staleTime: 30_000 (30s)
// Real-time chat messages: staleTime: 0 (always refetch)
```

**Renamed in v5**: `cacheTime` was renamed to `gcTime` (garbage collection time) in TanStack Query v5 to reduce confusion. The behavior is identical.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How should you structure query keys in a complex application?

**Answer:**

Query keys are the backbone of TanStack Query's caching and invalidation system. In a complex app with hundreds of queries, a well-designed key structure is critical. The best practice is to use a **hierarchical, coarse-to-fine** structure — similar to a REST URL path — and to use **query key factories** to ensure consistency.

**Principles:**
1. **General → Specific**: Start with the entity type, then narrow down with IDs, filters, and pagination.
2. **Objects for variable parts**: Use objects for filters/params so key order doesn't matter (TanStack Query uses deep equality).
3. **Key factories**: Centralize key construction in a factory object to avoid typos and enable powerful invalidation.

```jsx
// ──────────────────────────────────────────────
// query-keys.js — centralized query key factory
// ──────────────────────────────────────────────
export const taskKeys = {
  // ['tasks'] — matches all task-related queries
  all: ['tasks'],

  // ['tasks', 'lists'] — all list-type queries
  lists: () => [...taskKeys.all, 'lists'],

  // ['tasks', 'lists', { projectId, status, page }] — specific filtered list
  list: (filters) => [...taskKeys.lists(), filters],

  // ['tasks', 'details'] — all detail-type queries
  details: () => [...taskKeys.all, 'details'],

  // ['tasks', 'details', taskId] — specific task
  detail: (taskId) => [...taskKeys.details(), taskId],

  // ['tasks', 'details', taskId, 'comments'] — task's comments
  comments: (taskId) => [...taskKeys.detail(taskId), 'comments'],
};

export const userKeys = {
  all: ['users'],
  lists: () => [...userKeys.all, 'lists'],
  list: (filters) => [...userKeys.lists(), filters],
  details: () => [...userKeys.all, 'details'],
  detail: (userId) => [...userKeys.details(), userId],
  preferences: (userId) => [...userKeys.detail(userId), 'preferences'],
};

// ──────────────────────────────────────────────
// Usage in components
// ──────────────────────────────────────────────
import { taskKeys } from './query-keys';

function TaskBoard({ projectId }) {
  // Fetch tasks filtered by project and status
  const { data: todoTasks } = useQuery({
    queryKey: taskKeys.list({ projectId, status: 'todo' }),
    queryFn: () => fetchTasks({ projectId, status: 'todo' }),
  });

  const { data: doneTasks } = useQuery({
    queryKey: taskKeys.list({ projectId, status: 'done' }),
    queryFn: () => fetchTasks({ projectId, status: 'done' }),
  });

  return <Board todo={todoTasks} done={doneTasks} />;
}

function TaskDetail({ taskId }) {
  const { data: task } = useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => fetchTask(taskId),
  });

  return <TaskView task={task} />;
}

// ──────────────────────────────────────────────
// Powerful invalidation using the key hierarchy
// ──────────────────────────────────────────────
function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      // Invalidate ALL task lists (any filter combination) but NOT task details
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
}

function useUpdateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateTask,
    onSuccess: (_, { taskId }) => {
      // Invalidate this specific task detail
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(taskId) });
      // Also invalidate all lists (task might have moved between status columns)
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
    },
  });
}

function useDeleteProject(projectId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      // Nuclear: invalidate EVERYTHING related to tasks
      queryClient.invalidateQueries({ queryKey: taskKeys.all });
    },
  });
}
```

This factory pattern gives you **surgical precision** for invalidation: you can invalidate all tasks, all task lists, all task details, a specific task, or a specific task's comments — all by choosing the right level of the hierarchy.

---

### Q7. How do you implement optimistic updates with `useMutation`?

**Answer:**

**Optimistic updates** make the UI feel instant by updating the cache **before** the server confirms the mutation. If the server returns an error, you **roll back** to the previous state. TanStack Query's `onMutate` / `onError` / `onSettled` callbacks make this pattern straightforward.

The flow is:
1. **`onMutate`**: Cancel outgoing refetches (to avoid overwriting our optimistic update), snapshot the current cache, apply the optimistic update. Return the snapshot as context.
2. **`onError`**: Use the snapshot from context to roll back to the previous state.
3. **`onSettled`**: Invalidate the query so we refetch the real server state regardless of success or failure.

```jsx
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { taskKeys } from './query-keys';

function useToggleTaskStatus(projectId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, newStatus }) =>
      fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      }).then(res => {
        if (!res.ok) throw new Error('Failed to update task');
        return res.json();
      }),

    // ── Step 1: Optimistic update ──
    onMutate: async ({ taskId, newStatus }) => {
      // Cancel in-flight refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({
        queryKey: taskKeys.list({ projectId }),
      });

      // Snapshot the current cache value
      const previousTasks = queryClient.getQueryData(
        taskKeys.list({ projectId })
      );

      // Optimistically update the cache
      queryClient.setQueryData(
        taskKeys.list({ projectId }),
        (oldTasks) =>
          oldTasks?.map(task =>
            task.id === taskId ? { ...task, status: newStatus } : task
          )
      );

      // Return snapshot as context for rollback
      return { previousTasks };
    },

    // ── Step 2: Rollback on error ──
    onError: (error, variables, context) => {
      // Restore from snapshot
      queryClient.setQueryData(
        taskKeys.list({ projectId }),
        context.previousTasks
      );
      toast.error('Failed to update task. Changes reverted.');
    },

    // ── Step 3: Always refetch after mutation settles ──
    onSettled: () => {
      // Whether success or error, sync with server truth
      queryClient.invalidateQueries({
        queryKey: taskKeys.list({ projectId }),
      });
    },
  });
}

// Usage in a component
function TaskItem({ task, projectId }) {
  const toggleStatus = useToggleTaskStatus(projectId);

  const handleToggle = () => {
    const newStatus = task.status === 'done' ? 'todo' : 'done';
    toggleStatus.mutate({ taskId: task.id, newStatus });
    // UI updates INSTANTLY — no waiting for server
  };

  return (
    <div className={`task ${task.status}`}>
      <input
        type="checkbox"
        checked={task.status === 'done'}
        onChange={handleToggle}
      />
      <span>{task.title}</span>
    </div>
  );
}
```

**Production consideration**: For simple toggles and status changes, optimistic updates provide excellent UX. For complex mutations (like creating a new item that needs a server-generated ID), it's often better to use `invalidateQueries` and show a pending state instead — the optimistic approach would require generating temporary IDs and replacing them when the server responds.

---

### Q8. How does `useInfiniteQuery` work for implementing infinite scroll?

**Answer:**

`useInfiniteQuery` is designed for paginated data where the user loads more pages incrementally — infinite scroll, "Load More" buttons, and similar patterns. Instead of storing a single page of data, it stores **all fetched pages** in an array and provides `fetchNextPage` / `fetchPreviousPage` functions.

The key difference from `useQuery` is the `getNextPageParam` function, which extracts the cursor (or page number) for the next page from the last fetched page's response. When it returns `undefined`, TanStack Query knows there are no more pages.

```jsx
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';
import { useEffect } from 'react';

// API function — returns { items, nextCursor }
async function fetchNotifications({ pageParam = null }) {
  const url = new URL('/api/notifications', window.location.origin);
  if (pageParam) url.searchParams.set('cursor', pageParam);
  url.searchParams.set('limit', '20');

  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch notifications');
  return res.json(); // { items: [...], nextCursor: "abc123" | null }
}

function NotificationFeed() {
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,        // true if getNextPageParam returned a value
    isFetchingNextPage, // true while the next page is loading
  } = useInfiniteQuery({
    queryKey: ['notifications'],
    queryFn: fetchNotifications,
    initialPageParam: null,

    // Extract the cursor for the next page from the last fetched page
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,

    // Optional: also support fetching previous pages (for bi-directional scroll)
    // getPreviousPageParam: (firstPage) => firstPage.prevCursor ?? undefined,

    staleTime: 30_000,
  });

  // Intersection Observer — auto-fetch when sentinel comes into view
  const { ref: sentinelRef, inView } = useInView({ threshold: 0 });

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (isLoading) return <NotificationSkeleton count={5} />;
  if (isError) return <p>Error: {error.message}</p>;

  // data.pages is an array of page responses
  // Flatten all pages into a single list
  const allNotifications = data.pages.flatMap(page => page.items);

  return (
    <div className="notification-feed">
      {allNotifications.map(notification => (
        <NotificationItem key={notification.id} notification={notification} />
      ))}

      {/* Sentinel element at the bottom */}
      <div ref={sentinelRef} className="sentinel">
        {isFetchingNextPage && <Spinner size="small" />}
        {!hasNextPage && <p className="text-muted">You're all caught up!</p>}
      </div>
    </div>
  );
}
```

**How the cache looks internally:**

```jsx
// queryClient.getQueryData(['notifications']) returns:
{
  pages: [
    { items: [/* 20 items */], nextCursor: "cursor_page2" },  // page 1
    { items: [/* 20 items */], nextCursor: "cursor_page3" },  // page 2
    { items: [/* 15 items */], nextCursor: null },             // page 3 (last)
  ],
  pageParams: [null, "cursor_page2", "cursor_page3"],
}
```

When you invalidate an infinite query, TanStack Query refetches **all loaded pages** in sequence to ensure data consistency (items may have shifted between pages).

---

### Q9. How do you prefetch data for instant page transitions?

**Answer:**

**Prefetching** loads data into the cache *before* the user navigates to a page, so when they do navigate, the data is already available and the page renders instantly with no loading spinner. TanStack Query provides `queryClient.prefetchQuery()` for this purpose.

Common prefetching triggers:
1. **On hover** — prefetch when the user hovers over a link (gives ~300ms head start).
2. **On route load** — prefetch in a route loader (React Router, TanStack Router).
3. **After initial render** — prefetch likely next pages in the background.

```jsx
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { Link, useLoaderData } from 'react-router-dom';
import { productKeys } from './query-keys';

// ──────────────────────────────────────────
// Strategy 1: Prefetch on hover
// ──────────────────────────────────────────
function ProductListItem({ product }) {
  const queryClient = useQueryClient();

  const handleMouseEnter = () => {
    // Prefetch product detail — if data is already fresh, this is a no-op
    queryClient.prefetchQuery({
      queryKey: productKeys.detail(product.id),
      queryFn: () => fetchProduct(product.id),
      staleTime: 60_000, // don't re-prefetch if data is < 1 min old
    });
  };

  return (
    <Link
      to={`/products/${product.id}`}
      onMouseEnter={handleMouseEnter}
      onFocus={handleMouseEnter} // accessibility: also prefetch on keyboard focus
    >
      <div className="product-card">
        <img src={product.thumbnail} alt={product.name} />
        <h3>{product.name}</h3>
        <p>${product.price}</p>
      </div>
    </Link>
  );
}

// ──────────────────────────────────────────
// Strategy 2: Prefetch in a route loader (React Router v6.4+)
// ──────────────────────────────────────────
// router.js
import { createBrowserRouter } from 'react-router-dom';

export function createRouter(queryClient) {
  return createBrowserRouter([
    {
      path: '/products/:productId',
      element: <ProductDetail />,
      loader: async ({ params }) => {
        // ensureQueryData: returns cached data if fresh, otherwise fetches
        await queryClient.ensureQueryData({
          queryKey: productKeys.detail(params.productId),
          queryFn: () => fetchProduct(params.productId),
          staleTime: 60_000,
        });
        return { productId: params.productId };
      },
    },
  ]);
}

// ProductDetail.jsx — data is already in cache by the time this renders!
function ProductDetail() {
  const { productId } = useLoaderData();

  const { data: product } = useQuery({
    queryKey: productKeys.detail(productId),
    queryFn: () => fetchProduct(productId),
    staleTime: 60_000,
  });

  // `isLoading` is false because the loader already ensured the data exists
  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
    </div>
  );
}

// ──────────────────────────────────────────
// Strategy 3: Prefetch the next likely page after current render
// ──────────────────────────────────────────
function ProductList({ page }) {
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: productKeys.list({ page }),
    queryFn: () => fetchProducts({ page }),
  });

  // After the current page loads, prefetch the next page
  useEffect(() => {
    if (data?.hasNextPage) {
      queryClient.prefetchQuery({
        queryKey: productKeys.list({ page: page + 1 }),
        queryFn: () => fetchProducts({ page: page + 1 }),
      });
    }
  }, [data, page, queryClient]);

  return <ProductGrid products={data?.items} />;
}
```

**`prefetchQuery` vs `ensureQueryData`**: `prefetchQuery` fires and forgets — it does not return data and never throws. `ensureQueryData` returns the data and can be awaited, which makes it perfect for route loaders where you want to block navigation until data is ready.

---

### Q10. What are dependent (serial) queries and how do you implement them?

**Answer:**

**Dependent queries** are queries that depend on the result of a previous query — they must execute in **series**, not in parallel. A classic example: first fetch the current user, then use their `orgId` to fetch the organization details.

TanStack Query handles this with the `enabled` option. When `enabled` is `false`, the query does not execute. You set it to `true` only when the prerequisite data is available.

```jsx
import { useQuery } from '@tanstack/react-query';

function UserDashboard() {
  // Step 1: Fetch the current user
  const {
    data: user,
    isLoading: isUserLoading,
  } = useQuery({
    queryKey: ['currentUser'],
    queryFn: () => fetch('/api/me').then(r => r.json()),
  });

  // Step 2: Fetch the user's organization — depends on user.orgId
  const {
    data: organization,
    isLoading: isOrgLoading,
  } = useQuery({
    queryKey: ['organizations', user?.orgId],
    queryFn: () =>
      fetch(`/api/organizations/${user.orgId}`).then(r => r.json()),
    enabled: !!user?.orgId, // only runs when user is loaded AND has an orgId
  });

  // Step 3: Fetch the org's subscription plan — depends on organization
  const {
    data: plan,
    isLoading: isPlanLoading,
  } = useQuery({
    queryKey: ['plans', organization?.planId],
    queryFn: () =>
      fetch(`/api/plans/${organization.planId}`).then(r => r.json()),
    enabled: !!organization?.planId,
  });

  // Combined loading state
  if (isUserLoading) return <DashboardSkeleton />;

  return (
    <div className="dashboard">
      <header>
        <h1>Welcome, {user.name}</h1>
      </header>

      <section>
        <h2>Organization</h2>
        {isOrgLoading ? (
          <Skeleton width={200} />
        ) : (
          <p>{organization?.name}</p>
        )}
      </section>

      <section>
        <h2>Current Plan</h2>
        {isPlanLoading ? (
          <Skeleton width={150} />
        ) : (
          <PlanBadge plan={plan} />
        )}
      </section>
    </div>
  );
}

// More complex example: dependent query with transformation
function ProjectAnalytics({ projectId }) {
  // Fetch project to get its team members
  const { data: project } = useQuery({
    queryKey: ['projects', projectId],
    queryFn: () => fetchProject(projectId),
  });

  // Fetch analytics only for the project's active members
  const memberIds = project?.members
    ?.filter(m => m.active)
    ?.map(m => m.id);

  const { data: analytics } = useQuery({
    queryKey: ['analytics', projectId, { memberIds }],
    queryFn: () => fetchAnalytics(projectId, memberIds),
    // Enable only when we have member IDs to query
    enabled: !!memberIds?.length,
  });

  return <AnalyticsChart data={analytics} />;
}
```

**Important**: When a query is disabled (`enabled: false`), its status will be `isPending` (not `isLoading`) in TanStack Query v5 — because `isLoading` specifically means "pending AND fetching", while `isPending` just means "no data yet". This distinction matters for showing appropriate UI states.

---

### Q11. How do you run queries in parallel, and what is `useQueries`?

**Answer:**

By default, if you call multiple `useQuery` hooks in the same component, they all fire **in parallel** — TanStack Query does not wait for one to finish before starting another. However, when the **number** of parallel queries is dynamic (e.g., fetching details for a variable-length list of IDs), you cannot call hooks in a loop (hooks rules). This is where `useQueries` comes in.

`useQueries` accepts an array of query configurations and returns an array of query results, running them all in parallel.

```jsx
import { useQuery, useQueries } from '@tanstack/react-query';

// ──────────────────────────────────────────
// Static parallel queries — just use multiple useQuery calls
// ──────────────────────────────────────────
function DashboardOverview() {
  // These three queries fire simultaneously
  const { data: revenue } = useQuery({
    queryKey: ['metrics', 'revenue'],
    queryFn: fetchRevenueMetrics,
  });

  const { data: users } = useQuery({
    queryKey: ['metrics', 'users'],
    queryFn: fetchUserMetrics,
  });

  const { data: orders } = useQuery({
    queryKey: ['metrics', 'orders'],
    queryFn: fetchOrderMetrics,
  });

  return (
    <div className="metrics-grid">
      <MetricCard title="Revenue" data={revenue} />
      <MetricCard title="Users" data={users} />
      <MetricCard title="Orders" data={orders} />
    </div>
  );
}

// ──────────────────────────────────────────
// Dynamic parallel queries — useQueries for variable-length lists
// ──────────────────────────────────────────
function TeamMemberProfiles({ memberIds }) {
  // memberIds is dynamic — could be [1, 2, 3] or [5, 8, 12, 15, 22]
  const memberQueries = useQueries({
    queries: memberIds.map(id => ({
      queryKey: ['users', id],
      queryFn: () => fetchUser(id),
      staleTime: 5 * 60_000,
    })),
  });

  const isAnyLoading = memberQueries.some(q => q.isLoading);
  const allMembers = memberQueries
    .filter(q => q.isSuccess)
    .map(q => q.data);

  if (isAnyLoading) return <TeamSkeleton count={memberIds.length} />;

  return (
    <div className="team-grid">
      {allMembers.map(member => (
        <MemberCard key={member.id} member={member} />
      ))}
    </div>
  );
}

// ──────────────────────────────────────────
// Combining results from useQueries
// ──────────────────────────────────────────
function MultiRepoStats({ repoNames }) {
  const repoQueries = useQueries({
    queries: repoNames.map(name => ({
      queryKey: ['repos', name, 'stats'],
      queryFn: () => fetchRepoStats(name),
    })),
    // v5 feature: combine all results into a single derived value
    combine: (results) => {
      return {
        data: results.map(r => r.data).filter(Boolean),
        isLoading: results.some(r => r.isLoading),
        totalStars: results.reduce(
          (sum, r) => sum + (r.data?.stars ?? 0), 0
        ),
      };
    },
  });

  // repoQueries is now the combined result
  if (repoQueries.isLoading) return <Spinner />;

  return (
    <div>
      <h2>Total Stars: {repoQueries.totalStars}</h2>
      {repoQueries.data.map(repo => (
        <RepoCard key={repo.name} repo={repo} />
      ))}
    </div>
  );
}
```

**The `combine` option** (TanStack Query v5) is powerful — it lets you merge all query results into a single derived value, making it easy to compute aggregates, check combined loading states, and pass a clean API to child components.

---

### Q12. What are the pagination patterns in TanStack Query — cursor-based vs offset-based?

**Answer:**

TanStack Query supports both pagination strategies. The choice between them depends on your backend API and data characteristics:

- **Offset-based** (`?page=2&limit=20`): Simple, supports jumping to arbitrary pages, but can miss or duplicate items if data changes between page fetches.
- **Cursor-based** (`?cursor=abc123&limit=20`): More robust for real-time data, no duplicates/gaps when items are added/removed, but cannot jump to arbitrary pages.

```jsx
import { useQuery, useInfiniteQuery, keepPreviousData } from '@tanstack/react-query';
import { useState } from 'react';

// ──────────────────────────────────────────
// Pattern 1: Offset-based pagination with page numbers
// ──────────────────────────────────────────
function PaginatedOrderList() {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, isFetching, isPlaceholderData } = useQuery({
    queryKey: ['orders', { page, pageSize }],
    queryFn: () =>
      fetch(`/api/orders?page=${page}&limit=${pageSize}`)
        .then(r => r.json()),
    // Keep showing previous page data while fetching the next page
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });

  return (
    <div>
      {/* Show subtle loading indicator during page transitions */}
      <div style={{ opacity: isFetching ? 0.5 : 1, transition: 'opacity 0.2s' }}>
        <table>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.orders.map(order => (
              <tr key={order.id}>
                <td>{order.id}</td>
                <td>{order.customerName}</td>
                <td>${order.total.toFixed(2)}</td>
                <td>{order.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination controls */}
      <div className="pagination">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </button>

        <span>
          Page {page} of {data?.totalPages ?? '…'}
        </span>

        <button
          onClick={() => setPage(p => p + 1)}
          disabled={isPlaceholderData || !data?.hasMore}
        >
          Next
        </button>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────
// Pattern 2: Cursor-based pagination (infinite scroll)
// ──────────────────────────────────────────
function CursorPaginatedFeed() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['feed'],
    queryFn: async ({ pageParam }) => {
      const url = new URL('/api/feed', window.location.origin);
      if (pageParam) url.searchParams.set('cursor', pageParam);
      url.searchParams.set('limit', '15');
      const res = await fetch(url);
      return res.json();
      // Response shape: { items: [...], nextCursor: "eyJ..." | null }
    },
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
  });

  const allItems = data?.pages.flatMap(p => p.items) ?? [];

  if (isLoading) return <FeedSkeleton />;

  return (
    <div className="feed">
      {allItems.map(item => (
        <FeedItem key={item.id} item={item} />
      ))}

      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading more…' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

**`keepPreviousData` (v5) / `placeholderData: keepPreviousData`**: This is essential for offset pagination — it tells TanStack Query to keep displaying the previous page's data while the new page loads, preventing the jarring flash of a loading skeleton on every page change. The `isPlaceholderData` flag tells you when the displayed data is from the previous page.

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you implement query cancellation with `AbortSignal`?

**Answer:**

When a component unmounts or a query key changes before a fetch completes, TanStack Query can **automatically cancel** the in-flight request by passing an `AbortSignal` to your `queryFn`. This prevents wasted bandwidth, avoids race conditions, and is especially important for expensive or slow queries.

The `queryFn` receives a context object that includes a `signal` property — you pass this to `fetch()` or any other cancellable API (like Axios).

```jsx
import { useQuery } from '@tanstack/react-query';

// ──────────────────────────────────────────
// Basic cancellation with fetch
// ──────────────────────────────────────────
function SearchResults({ query }) {
  const { data, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: async ({ signal }) => {
      // `signal` is an AbortSignal — if the query is cancelled,
      // this signal will be aborted and fetch will throw an AbortError
      const response = await fetch(
        `/api/search?q=${encodeURIComponent(query)}`,
        { signal } // ← pass the signal to fetch
      );

      if (!response.ok) throw new Error('Search failed');
      return response.json();
    },
    enabled: query.length >= 2, // don't search for single characters
  });

  // When `query` changes quickly (user typing), TanStack Query:
  // 1. Cancels the previous in-flight request (AbortSignal fires)
  // 2. Starts a new request with the new query
  // → No race conditions, no stale results displayed

  return (
    <div>
      {isLoading && <SearchSkeleton />}
      {data?.results.map(r => <SearchResult key={r.id} result={r} />)}
    </div>
  );
}

// ──────────────────────────────────────────
// Cancellation with Axios
// ──────────────────────────────────────────
import axios from 'axios';

const fetchReport = async ({ queryKey, signal }) => {
  const [, reportId, params] = queryKey;

  const { data } = await axios.get(`/api/reports/${reportId}`, {
    params,
    signal, // Axios also supports AbortSignal
  });

  return data;
};

function ReportViewer({ reportId, dateRange }) {
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['reports', reportId, { dateRange }],
    queryFn: fetchReport,
    staleTime: 5 * 60_000,
  });

  return (
    <div>
      {isFetching && <ProgressBar />}
      {data && <ReportChart data={data} />}
    </div>
  );
}

// ──────────────────────────────────────────
// Manual cancellation
// ──────────────────────────────────────────
function ExpensiveAnalytics({ filters }) {
  const queryClient = useQueryClient();

  const { data, isFetching } = useQuery({
    queryKey: ['analytics', filters],
    queryFn: ({ signal }) => fetchAnalytics(filters, signal),
  });

  // User can manually cancel a long-running query
  const handleCancel = () => {
    queryClient.cancelQueries({ queryKey: ['analytics', filters] });
  };

  return (
    <div>
      {isFetching && (
        <div className="loading-bar">
          <span>Crunching numbers…</span>
          <button onClick={handleCancel}>Cancel</button>
        </div>
      )}
      {data && <AnalyticsDashboard data={data} />}
    </div>
  );
}
```

**Why this matters in production**: Without cancellation, if a user rapidly types in a search box (triggering a new query on each keystroke), you could have 10+ pending requests. Without `AbortSignal`, all 10 responses come back and the last one to resolve "wins" — which may not be the most recent query. With `AbortSignal`, only the latest request completes, saving bandwidth and preventing stale results.

---

### Q14. How do you handle global error handling and retry strategies in TanStack Query?

**Answer:**

TanStack Query provides both **automatic retries** (with configurable backoff) and **global error handling** callbacks. In production, you configure these at the `QueryClient` level so every query benefits from consistent retry logic and error reporting without per-component boilerplate.

**Retry behavior (defaults):**
- Queries retry **3 times** with **exponential backoff** (1s, 2s, 4s).
- Mutations do **not** retry by default.

```jsx
import { QueryClient, QueryClientProvider, QueryCache, MutationCache } from '@tanstack/react-query';
import { toast } from 'sonner';

// ──────────────────────────────────────────
// Global error handling via QueryCache and MutationCache callbacks
// ──────────────────────────────────────────
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      // Only show toast for queries that already had data (background refetch failed)
      // Don't toast for initial loads — the component handles that UI
      if (query.state.data !== undefined) {
        toast.error(`Background update failed: ${error.message}`);
      }

      // Report to error tracking
      if (error.status !== 401 && error.status !== 403) {
        Sentry.captureException(error, {
          tags: { queryKey: JSON.stringify(query.queryKey) },
        });
      }
    },
  }),

  mutationCache: new MutationCache({
    onError: (error, variables, context, mutation) => {
      // Global mutation error handling
      toast.error(`Operation failed: ${error.message}`);
      Sentry.captureException(error);
    },
  }),

  defaultOptions: {
    queries: {
      // ── Retry configuration ──
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors) — they won't magically fix themselves
        if (error.status >= 400 && error.status < 500) return false;
        // Retry up to 3 times for server errors and network issues
        return failureCount < 3;
      },

      // Custom backoff delay
      retryDelay: (attemptIndex) => {
        // Exponential backoff: 1s, 2s, 4s — capped at 30s
        return Math.min(1000 * 2 ** attemptIndex, 30_000);
      },

      // ── Staleness & refetching ──
      staleTime: 30_000,
      refetchOnWindowFocus: 'always', // refetch stale queries on tab focus
      refetchOnReconnect: true,        // refetch when network comes back

      // ── Error handling ──
      // Global default: use error boundaries for unexpected errors
      throwOnError: (error) => error.status >= 500,
    },

    mutations: {
      retry: false, // mutations should not retry by default
      throwOnError: false,
    },
  },
});

// ──────────────────────────────────────────
// Per-query retry override
// ──────────────────────────────────────────
function CriticalDataComponent() {
  const { data } = useQuery({
    queryKey: ['billing', 'invoice'],
    queryFn: fetchCurrentInvoice,
    // Override: critical data gets more retries
    retry: 5,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 60_000),
  });

  return <InvoiceDisplay invoice={data} />;
}

// ──────────────────────────────────────────
// Error boundary integration with React 18
// ──────────────────────────────────────────
import { ErrorBoundary } from 'react-error-boundary';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';

function AppErrorBoundary({ children }) {
  const { reset } = useQueryErrorResetBoundary();

  return (
    <ErrorBoundary
      onReset={reset}
      fallbackRender={({ resetErrorBoundary, error }) => (
        <div className="error-page">
          <h2>Something went wrong</h2>
          <p>{error.message}</p>
          <button onClick={resetErrorBoundary}>Try Again</button>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
}

// App.jsx
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppErrorBoundary>
        <Router />
      </AppErrorBoundary>
    </QueryClientProvider>
  );
}
```

**Production strategy**: Use the `QueryCache.onError` callback for **side effects** (toasts, logging) and `throwOnError` for **rendering** error boundaries. The callback runs for every error; `throwOnError` determines whether the error propagates to the nearest React error boundary.

---

### Q15. How do you implement offline support and cache persistence with `persistQueryClient`?

**Answer:**

TanStack Query can persist its entire cache to `localStorage`, `IndexedDB`, or any storage adapter so that when users reload the page or come back offline, they see cached data instantly instead of a blank loading screen. This is implemented via the `@tanstack/query-persist-client-core` and adapter packages.

The basic idea: serialize the query cache to storage on every change, and **hydrate** it back when the app starts. Combined with `staleTime`, this gives you an offline-first experience.

```jsx
import { QueryClient } from '@tanstack/react-query';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import { get, set, del } from 'idb-keyval'; // IndexedDB wrapper

// ──────────────────────────────────────────
// Option 1: localStorage persister (sync, simple, 5MB limit)
// ──────────────────────────────────────────
const localStoragePersister = createSyncStoragePersister({
  storage: window.localStorage,
  key: 'REACT_QUERY_CACHE',
  // Optional: throttle writes to avoid performance issues
  throttleTime: 1000,
  // Optional: custom serialization (e.g., compress with lz-string)
  serialize: (data) => JSON.stringify(data),
  deserialize: (data) => JSON.parse(data),
});

// ──────────────────────────────────────────
// Option 2: IndexedDB persister (async, larger capacity)
// ──────────────────────────────────────────
const indexedDbPersister = createAsyncStoragePersister({
  storage: {
    getItem: (key) => get(key),
    setItem: (key, value) => set(key, value),
    removeItem: (key) => del(key),
  },
  key: 'REACT_QUERY_CACHE',
});

// ──────────────────────────────────────────
// QueryClient configuration for persistence
// ──────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // CRITICAL for persistence: set gcTime high enough that data survives
      // between sessions. Default is 5 min — too short for offline use.
      gcTime: 24 * 60 * 60 * 1000, // 24 hours

      // Data persisted from last session is stale — refetch in background
      staleTime: 60_000,

      // Don't retry indefinitely when offline
      retry: (failureCount, error) => {
        if (!navigator.onLine) return false;
        return failureCount < 3;
      },

      // Use network status to determine if we should refetch
      networkMode: 'offlineFirst', // serve cache first, refetch when online
    },
  },
});

// ──────────────────────────────────────────
// App setup with PersistQueryClientProvider
// ──────────────────────────────────────────
function App() {
  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{
        persister: localStoragePersister,
        // Max age of the persisted cache — discard if older
        maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
        // Only persist specific queries (optional)
        dehydrateOptions: {
          shouldDehydrateQuery: (query) => {
            // Don't persist sensitive data
            const key = query.queryKey[0];
            return key !== 'auth' && key !== 'tokens';
          },
        },
      }}
      // Show app immediately, don't wait for cache restoration
      onSuccess={() => {
        // After cache is restored, invalidate stale queries
        queryClient.resumePausedMutations().then(() => {
          queryClient.invalidateQueries();
        });
      }}
    >
      <RouterProvider router={router} />
    </PersistQueryClientProvider>
  );
}

// ──────────────────────────────────────────
// Offline-aware component
// ──────────────────────────────────────────
function OfflineAwareList() {
  const { data, isLoading, isFetching, dataUpdatedAt } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks,
  });

  const isOnline = useOnlineStatus();

  return (
    <div>
      {!isOnline && (
        <div className="offline-banner">
          You're offline. Showing cached data from{' '}
          {new Date(dataUpdatedAt).toLocaleString()}.
        </div>
      )}
      {data?.map(task => <TaskItem key={task.id} task={task} />)}
    </div>
  );
}
```

**Key gotcha**: The default `gcTime` of 5 minutes means inactive cache entries are garbage collected before they can be persisted between sessions. For persistence, set `gcTime` to at least 24 hours. Also, be mindful of storage limits — `localStorage` has a 5-10MB limit per origin.

---

### Q16. What are placeholder data and initial data patterns, and when do you use each?

**Answer:**

Both `placeholderData` and `initialData` let you provide data to the UI **before** the first fetch completes, but they have fundamentally different semantics:

| Feature | `initialData` | `placeholderData` |
|---|---|---|
| **Stored in cache** | Yes — treated as real cached data | No — only shown as a fallback |
| **Affects staleness** | Yes — `staleTime` counts from when `initialData` was set | No — query is always in `loading`/`pending` state |
| **Affects `dataUpdatedAt`** | Yes — you can set `initialDataUpdatedAt` | No |
| **Survives unmount/remount** | Yes (it's in the cache) | No |
| **Use case** | You have real (possibly stale) data from another source | You have a partial/shaped preview for UX |

```jsx
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';

// ──────────────────────────────────────────
// initialData: Using data from another query (cache seeding)
// ──────────────────────────────────────────
function ProductDetail({ productId }) {
  const queryClient = useQueryClient();

  const { data: product } = useQuery({
    queryKey: ['products', productId],
    queryFn: () => fetchProduct(productId),

    // Seed initial data from the product list cache
    initialData: () => {
      // Look in the products list cache for this specific product
      const productsListData = queryClient.getQueryData(['products', 'list']);
      return productsListData?.items?.find(p => p.id === productId);
    },

    // Tell TanStack Query when this initial data was last updated
    // so it can decide if it's still fresh or needs a background refetch
    initialDataUpdatedAt: () => {
      return queryClient.getQueryState(['products', 'list'])?.dataUpdatedAt;
    },

    staleTime: 60_000,
  });

  // If the product was in the list cache, `product` is immediately available
  // (no loading state!). TanStack Query will refetch in the background if stale.
  return product ? <ProductView product={product} /> : <ProductSkeleton />;
}

// ──────────────────────────────────────────
// placeholderData: Showing a preview while loading
// ──────────────────────────────────────────
function UserProfile({ userId }) {
  const { data: user, isPlaceholderData } = useQuery({
    queryKey: ['users', userId],
    queryFn: () => fetchUser(userId),

    // Show a placeholder structure while the real data loads
    placeholderData: {
      id: userId,
      name: 'Loading…',
      email: '—',
      avatar: '/placeholder-avatar.png',
      bio: '',
    },
  });

  return (
    <div style={{ opacity: isPlaceholderData ? 0.6 : 1 }}>
      <img src={user.avatar} alt={user.name} />
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
}

// ──────────────────────────────────────────
// placeholderData with keepPreviousData — smooth transitions
// ──────────────────────────────────────────
function SearchResults({ searchTerm }) {
  const { data, isPlaceholderData, isFetching } = useQuery({
    queryKey: ['search', searchTerm],
    queryFn: () => searchProducts(searchTerm),

    // Keep showing previous search results while new ones load
    placeholderData: keepPreviousData,
  });

  return (
    <div>
      {isFetching && <TopProgressBar />}

      <div style={{ opacity: isPlaceholderData ? 0.7 : 1 }}>
        {data?.results.map(result => (
          <SearchResultItem key={result.id} result={result} />
        ))}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────
// initialData from server props (SSR / SSG)
// ──────────────────────────────────────────
function ServerRenderedPage({ serverData }) {
  const { data } = useQuery({
    queryKey: ['page-data'],
    queryFn: fetchPageData,

    // Data rendered on the server — use it as initial cache entry
    initialData: serverData,
    initialDataUpdatedAt: serverData.__fetchedAt, // timestamp from server
    staleTime: 60_000,
  });

  return <PageContent data={data} />;
}
```

**Rule of thumb**: Use `initialData` when you have **real data** from a known source (another cache entry, server props, URL state). Use `placeholderData` when you want a **visual preview** or want to keep previous data visible during transitions.

---

### Q17. How do you test components that use TanStack Query?

**Answer:**

Testing TanStack Query components requires a few patterns: wrapping components in a `QueryClientProvider` with a fresh `QueryClient`, mocking the `queryFn` or the network layer, and using `@testing-library/react`'s async utilities to wait for query resolution.

**Key testing principles:**
1. Create a **fresh `QueryClient`** per test to prevent cache leakage.
2. Disable **retries** in tests (they slow down tests and make error assertions harder).
3. Use `renderHook` for testing custom hooks, `render` for components.
4. Mock at the **network level** (MSW) or at the **function level** (jest.fn).

```jsx
// ──────────────────────────────────────────
// test-utils.jsx — shared test utilities
// ──────────────────────────────────────────
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, renderHook } from '@testing-library/react';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,       // don't retry in tests
        gcTime: 0,          // garbage collect immediately
        staleTime: 0,       // always stale in tests
      },
      mutations: {
        retry: false,
      },
    },
    // Suppress console error logs during tests
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {},
    },
  });
}

export function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

export function renderWithQuery(ui, options = {}) {
  const queryClient = createTestQueryClient();
  const Wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  };
}

// ──────────────────────────────────────────
// Testing a component — mocking at function level
// ──────────────────────────────────────────
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithQuery } from './test-utils';
import { TaskList } from './TaskList';
import * as api from './api';

// Mock the API module
jest.mock('./api');

describe('TaskList', () => {
  it('renders tasks after loading', async () => {
    // Arrange: mock the fetch function
    api.fetchTasks.mockResolvedValue([
      { id: 1, title: 'Write tests', status: 'todo' },
      { id: 2, title: 'Ship feature', status: 'done' },
    ]);

    // Act: render with query provider
    renderWithQuery(<TaskList projectId="proj-1" />);

    // Assert: loading state appears first
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    // Assert: tasks appear after fetch resolves
    await waitFor(() => {
      expect(screen.getByText('Write tests')).toBeInTheDocument();
      expect(screen.getByText('Ship feature')).toBeInTheDocument();
    });

    // Verify the API was called with correct args
    expect(api.fetchTasks).toHaveBeenCalledWith('proj-1');
  });

  it('shows error state on fetch failure', async () => {
    api.fetchTasks.mockRejectedValue(new Error('Network error'));

    renderWithQuery(<TaskList projectId="proj-1" />);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('creates a task and invalidates the list', async () => {
    const user = userEvent.setup();
    api.fetchTasks.mockResolvedValue([]);
    api.createTask.mockResolvedValue({ id: 3, title: 'New task', status: 'todo' });

    const { queryClient } = renderWithQuery(<TaskList projectId="proj-1" />);

    await waitFor(() => {
      expect(screen.getByText(/no tasks/i)).toBeInTheDocument();
    });

    // Spy on invalidation
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

    // Click "Add Task"
    await user.click(screen.getByRole('button', { name: /add task/i }));

    await waitFor(() => {
      expect(api.createTask).toHaveBeenCalled();
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['tasks', 'proj-1'] })
      );
    });
  });
});

// ──────────────────────────────────────────
// Testing a custom hook with renderHook
// ──────────────────────────────────────────
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from './test-utils';
import { useUser } from './useUser';

describe('useUser', () => {
  it('returns user data', async () => {
    // Mock fetch globally or use MSW
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1, name: 'Alice' }),
    });

    const { result } = renderHook(() => useUser(1), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    // Wait for data
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual({ id: 1, name: 'Alice' });
  });
});
```

**MSW (Mock Service Worker)** is the recommended approach for integration tests — it intercepts requests at the network level, so your `queryFn` code runs exactly as in production. Jest mocks are faster but less realistic.

---

### Q18. How do you implement server-side rendering (SSR) with TanStack Query — prefetching data on the server?

**Answer:**

TanStack Query supports SSR by **prefetching** queries on the server, **dehydrating** the cache into a serializable state, sending it to the client as HTML/JSON, and **hydrating** it on the client so that `useQuery` has data immediately — no client-side loading spinners for prefetched data.

This works with Next.js (App Router and Pages Router), Remix, and any custom SSR setup.

```jsx
// ──────────────────────────────────────────
// Next.js App Router (React Server Components) — recommended approach
// ──────────────────────────────────────────

// app/providers.jsx (Client Component)
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function QueryProvider({ children }) {
  // Create QueryClient inside useState to avoid sharing between requests
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            // Don't refetch immediately on client — server data is fresh enough
            refetchOnMount: false,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

// app/layout.jsx
import { QueryProvider } from './providers';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}

// app/products/page.jsx (Server Component — prefetch here)
import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query';
import { ProductList } from './ProductList';

export default async function ProductsPage() {
  const queryClient = new QueryClient();

  // Prefetch on the server
  await queryClient.prefetchQuery({
    queryKey: ['products', 'list', { page: 1 }],
    queryFn: () =>
      fetch('https://api.example.com/products?page=1').then(r => r.json()),
  });

  // Prefetch multiple queries in parallel
  await Promise.all([
    queryClient.prefetchQuery({
      queryKey: ['categories'],
      queryFn: () =>
        fetch('https://api.example.com/categories').then(r => r.json()),
    }),
    queryClient.prefetchQuery({
      queryKey: ['featured-products'],
      queryFn: () =>
        fetch('https://api.example.com/products/featured').then(r => r.json()),
    }),
  ]);

  return (
    // HydrationBoundary serializes the cache and sends it to the client
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ProductList />
    </HydrationBoundary>
  );
}

// app/products/ProductList.jsx (Client Component — uses prefetched data)
'use client';

import { useQuery } from '@tanstack/react-query';

export function ProductList() {
  // This data was already prefetched on the server!
  // No loading state — data is immediately available from hydrated cache
  const { data: products } = useQuery({
    queryKey: ['products', 'list', { page: 1 }],
    queryFn: () =>
      fetch('/api/products?page=1').then(r => r.json()),
    staleTime: 60_000,
  });

  return (
    <div className="product-grid">
      {products?.items.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

// ──────────────────────────────────────────
// Next.js Pages Router approach
// ──────────────────────────────────────────
import { dehydrate, QueryClient, HydrationBoundary } from '@tanstack/react-query';

export async function getServerSideProps() {
  const queryClient = new QueryClient();

  await queryClient.prefetchQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
  });

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
    },
  };
}

export default function ProductsPage({ dehydratedState }) {
  return (
    <HydrationBoundary state={dehydratedState}>
      <ProductList />
    </HydrationBoundary>
  );
}
```

**Critical SSR gotcha**: Never create a `QueryClient` as a module-level singleton in SSR — it would be shared across all requests, leaking data between users. Always create it inside a function (per-request on the server, inside `useState` on the client).

---

### Q19. How do you integrate real-time data (WebSockets) with TanStack Query?

**Answer:**

TanStack Query is designed for **request/response** patterns, not streaming data. But in production, you often need to combine both: fetch initial data with TanStack Query, then keep it fresh via WebSocket events. The recommended pattern is to use WebSocket messages to **invalidate** or **directly update** the query cache.

There are three strategies, from simplest to most sophisticated:

1. **Invalidation**: WebSocket event triggers `invalidateQueries` → refetch from HTTP API.
2. **Direct cache update**: WebSocket event directly updates cache via `setQueryData`.
3. **Hybrid**: Use initial HTTP fetch + WebSocket for subsequent updates.

```jsx
import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

// ──────────────────────────────────────────
// Strategy 1: WebSocket triggers invalidation (simplest)
// ──────────────────────────────────────────
function useRealtimeInvalidation() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket('wss://api.example.com/events');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'task_created':
        case 'task_updated':
        case 'task_deleted':
          // Just invalidate — TanStack Query refetches from the HTTP API
          queryClient.invalidateQueries({ queryKey: ['tasks'] });
          break;

        case 'comment_added':
          queryClient.invalidateQueries({
            queryKey: ['tasks', message.taskId, 'comments'],
          });
          break;

        case 'notification':
          queryClient.invalidateQueries({ queryKey: ['notifications'] });
          break;
      }
    };

    ws.onerror = () => {
      // Fallback: poll via refetchInterval when WebSocket is down
      console.warn('WebSocket error — falling back to polling');
    };

    return () => ws.close();
  }, [queryClient]);
}

// ──────────────────────────────────────────
// Strategy 2: Direct cache update (more efficient, no extra HTTP request)
// ──────────────────────────────────────────
function useRealtimeTaskUpdates(projectId) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket(
      `wss://api.example.com/projects/${projectId}/tasks/stream`
    );

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'task_created':
          queryClient.setQueryData(
            ['tasks', { projectId }],
            (oldTasks) => oldTasks ? [...oldTasks, message.task] : [message.task]
          );
          break;

        case 'task_updated':
          queryClient.setQueryData(
            ['tasks', { projectId }],
            (oldTasks) =>
              oldTasks?.map(t =>
                t.id === message.task.id ? { ...t, ...message.task } : t
              )
          );
          // Also update the detail cache
          queryClient.setQueryData(
            ['tasks', message.task.id],
            (old) => old ? { ...old, ...message.task } : undefined
          );
          break;

        case 'task_deleted':
          queryClient.setQueryData(
            ['tasks', { projectId }],
            (oldTasks) => oldTasks?.filter(t => t.id !== message.taskId)
          );
          queryClient.removeQueries({
            queryKey: ['tasks', message.taskId],
          });
          break;
      }
    };

    return () => ws.close();
  }, [projectId, queryClient]);
}

// ──────────────────────────────────────────
// Strategy 3: Hybrid — initial HTTP + WebSocket with polling fallback
// ──────────────────────────────────────────
function useRealtimeTasks(projectId) {
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState(false);

  // Initial data from HTTP
  const query = useQuery({
    queryKey: ['tasks', { projectId }],
    queryFn: () => fetchTasks(projectId),
    // If WebSocket is down, fall back to polling every 10s
    refetchInterval: wsConnected ? false : 10_000,
    staleTime: wsConnected ? Infinity : 5_000, // trust WebSocket updates
  });

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket(
      `wss://api.example.com/projects/${projectId}/stream`
    );

    ws.onopen = () => setWsConnected(true);

    ws.onmessage = (event) => {
      const { type, payload } = JSON.parse(event.data);
      if (type === 'tasks_changed') {
        queryClient.setQueryData(['tasks', { projectId }], payload);
      }
    };

    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);

    return () => {
      ws.close();
      setWsConnected(false);
    };
  }, [projectId, queryClient]);

  return { ...query, wsConnected };
}

// Usage
function LiveTaskBoard({ projectId }) {
  const { data: tasks, wsConnected } = useRealtimeTasks(projectId);

  return (
    <div>
      <ConnectionIndicator connected={wsConnected} />
      <TaskBoard tasks={tasks} />
    </div>
  );
}
```

**Strategy recommendation**: Start with Strategy 1 (invalidation) — it's the simplest and guarantees data consistency because the source of truth is always the HTTP API. Move to Strategy 2 (direct updates) only if the extra HTTP requests from invalidation cause performance issues or if you need sub-second latency.

---

### Q20. How do you architect a production data layer for a complex SaaS dashboard using TanStack Query?

**Answer:**

Building a data layer for a complex SaaS dashboard requires more than just sprinkling `useQuery` calls in components. You need a **structured, scalable architecture** that centralizes API logic, provides type safety, handles authentication, manages error states, and scales across dozens of features and hundreds of queries.

Here is a production-ready architecture:

```jsx
// ──────────────────────────────────────────
// 1. API Client — centralized HTTP layer with auth & error handling
// ──────────────────────────────────────────
// lib/api-client.js

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function apiClient(endpoint, { method = 'GET', body, signal } = {}) {
  const token = getAuthToken(); // from cookie, localStorage, or auth provider

  const response = await fetch(`${process.env.REACT_APP_API_URL}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    ...(body && { body: JSON.stringify(body) }),
    signal,
  });

  if (response.status === 401) {
    // Token expired — trigger re-auth
    await refreshToken();
    // Retry the request once
    return apiClient(endpoint, { method, body, signal });
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      errorData?.message || `Request failed: ${response.status}`,
      response.status,
      errorData
    );
  }

  if (response.status === 204) return null;
  return response.json();
}

export { apiClient, ApiError };

// ──────────────────────────────────────────
// 2. Query Key Factory — organized by domain
// ──────────────────────────────────────────
// lib/query-keys.js

export const queryKeys = {
  // Auth
  auth: {
    all: ['auth'],
    currentUser: () => [...queryKeys.auth.all, 'currentUser'],
    permissions: () => [...queryKeys.auth.all, 'permissions'],
  },

  // Projects
  projects: {
    all: ['projects'],
    lists: () => [...queryKeys.projects.all, 'list'],
    list: (filters) => [...queryKeys.projects.lists(), filters],
    details: () => [...queryKeys.projects.all, 'detail'],
    detail: (id) => [...queryKeys.projects.details(), id],
    metrics: (id) => [...queryKeys.projects.detail(id), 'metrics'],
    members: (id) => [...queryKeys.projects.detail(id), 'members'],
  },

  // Billing
  billing: {
    all: ['billing'],
    subscription: () => [...queryKeys.billing.all, 'subscription'],
    invoices: (params) => [...queryKeys.billing.all, 'invoices', params],
    usage: (period) => [...queryKeys.billing.all, 'usage', period],
  },

  // Analytics
  analytics: {
    all: ['analytics'],
    dashboard: (dateRange) => [...queryKeys.analytics.all, 'dashboard', dateRange],
    report: (reportId, params) => [...queryKeys.analytics.all, 'report', reportId, params],
  },
};

// ──────────────────────────────────────────
// 3. Domain-specific hooks — one file per feature
// ──────────────────────────────────────────
// features/projects/hooks/useProjects.js

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { queryKeys } from '@/lib/query-keys';

// ── Queries ──

export function useProjects(filters) {
  return useQuery({
    queryKey: queryKeys.projects.list(filters),
    queryFn: ({ signal }) =>
      apiClient(`/projects?${new URLSearchParams(filters)}`, { signal }),
    staleTime: 2 * 60_000,
    placeholderData: keepPreviousData,
  });
}

export function useProject(projectId) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: queryKeys.projects.detail(projectId),
    queryFn: ({ signal }) =>
      apiClient(`/projects/${projectId}`, { signal }),
    staleTime: 60_000,
    enabled: !!projectId,
    // Seed from list cache
    initialData: () => {
      const lists = queryClient.getQueriesData({
        queryKey: queryKeys.projects.lists(),
      });
      for (const [, data] of lists) {
        const project = data?.items?.find(p => p.id === projectId);
        if (project) return project;
      }
      return undefined;
    },
  });
}

export function useProjectMetrics(projectId, dateRange) {
  return useQuery({
    queryKey: queryKeys.projects.metrics(projectId),
    queryFn: ({ signal }) =>
      apiClient(
        `/projects/${projectId}/metrics?start=${dateRange.start}&end=${dateRange.end}`,
        { signal }
      ),
    staleTime: 30_000,
    enabled: !!projectId,
  });
}

// ── Mutations ──

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) =>
      apiClient('/projects', { method: 'POST', body: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists() });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, ...data }) =>
      apiClient(`/projects/${projectId}`, { method: 'PATCH', body: data }),
    onSuccess: (updatedProject) => {
      // Update detail cache directly
      queryClient.setQueryData(
        queryKeys.projects.detail(updatedProject.id),
        updatedProject
      );
      // Invalidate lists (name/status might have changed)
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists() });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId) =>
      apiClient(`/projects/${projectId}`, { method: 'DELETE' }),
    onSuccess: (_, projectId) => {
      queryClient.removeQueries({
        queryKey: queryKeys.projects.detail(projectId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists() });
    },
  });
}

// ──────────────────────────────────────────
// 4. QueryClient configuration — production-grade
// ──────────────────────────────────────────
// lib/query-client.js

import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';
import { toast } from 'sonner';
import * as Sentry from '@sentry/react';
import { ApiError } from './api-client';

export function createAppQueryClient() {
  return new QueryClient({
    queryCache: new QueryCache({
      onError: (error, query) => {
        // 401 → redirect to login (handled by apiClient interceptor)
        if (error instanceof ApiError && error.status === 401) return;

        // Background refetch failure → subtle toast
        if (query.state.data !== undefined) {
          toast.warning('Data may be outdated. Retrying…');
        }

        // Report server errors
        if (!(error instanceof ApiError) || error.status >= 500) {
          Sentry.captureException(error, {
            tags: { queryKey: JSON.stringify(query.queryKey) },
          });
        }
      },
    }),

    mutationCache: new MutationCache({
      onError: (error) => {
        if (error instanceof ApiError) {
          toast.error(error.message);
          if (error.status >= 500) Sentry.captureException(error);
        } else {
          toast.error('An unexpected error occurred');
          Sentry.captureException(error);
        }
      },
    }),

    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 10 * 60_000,
        retry: (count, error) => {
          if (error instanceof ApiError && error.status < 500) return false;
          return count < 3;
        },
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
        refetchOnWindowFocus: true,
        throwOnError: (error) =>
          error instanceof ApiError && error.status >= 500,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// ──────────────────────────────────────────
// 5. App entry point — putting it all together
// ──────────────────────────────────────────
// App.jsx

import { useState } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { createAppQueryClient } from '@/lib/query-client';

function App() {
  const [queryClient] = useState(createAppQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </ErrorBoundary>
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}

// ──────────────────────────────────────────
// 6. Dashboard page — composing the data layer
// ──────────────────────────────────────────
// pages/Dashboard.jsx

import { useProjects, useProjectMetrics } from '@/features/projects/hooks';
import { useCurrentUser } from '@/features/auth/hooks';
import { useBillingUsage } from '@/features/billing/hooks';

function Dashboard() {
  const { data: user } = useCurrentUser();
  const { data: projects } = useProjects({ orgId: user?.orgId, status: 'active' });
  const { data: usage } = useBillingUsage('current_month');

  return (
    <div className="dashboard">
      <WelcomeHeader user={user} />
      <UsageWidget usage={usage} />
      <ProjectGrid projects={projects?.items} />
    </div>
  );
}
```

**Architecture summary:**

| Layer | Responsibility | Files |
|---|---|---|
| **API Client** | HTTP, auth, error normalization | `lib/api-client.js` |
| **Query Keys** | Cache addressing, invalidation hierarchy | `lib/query-keys.js` |
| **Feature Hooks** | Domain logic, query/mutation config | `features/*/hooks/*.js` |
| **QueryClient** | Global retry, error handling, defaults | `lib/query-client.js` |
| **Components** | UI rendering, composing hooks | `pages/*.jsx`, `components/*.jsx` |

This separation means components never touch `fetch` directly, query keys are consistent and typo-free, invalidation is predictable, and new features follow an established pattern. The DevTools (`ReactQueryDevtools`) give visibility into every cache entry during development.

---

*TanStack Query is the modern standard for server state management in React 18. It replaces the fragile `useEffect` + `useState` pattern with a declarative, cache-first approach that handles the full complexity of real-world data fetching — loading states, caching, deduplication, retries, pagination, optimistic updates, prefetching, and offline support — out of the box.*
