# 24. Recursive CTEs and Hierarchical Queries — Senior

## Q1. (Beginner) What are the two parts of a recursive CTE? What does each produce?

**Answer:**  
(1) **Anchor** (non-recursive term): the base case; runs once and produces the initial result set. (2) **Recursive term**: references the CTE and unions with the anchor; runs repeatedly, using the current result set, until it returns no rows. Final result = union of all iterations.

---

## Q2. (Beginner) Write a recursive CTE that generates the numbers 1 to 10 (without a table).

**Answer:**  
**PostgreSQL**:
```sql
WITH RECURSIVE nums(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM nums WHERE n < 10
)
SELECT * FROM nums;
```
Anchor: 1. Recursive: n+1 while n < 10. Stop when recursive part returns no rows.

---

## Q3. (Intermediate) Write a recursive CTE that returns all ancestors of a given node in (id, parent_id). Assume node_id = 5.

**Answer:**  
**PostgreSQL**:
```sql
WITH RECURSIVE ancestors AS (
  SELECT id, parent_id, 1 AS level FROM tree WHERE id = 5
  UNION ALL
  SELECT t.id, t.parent_id, a.level + 1
  FROM tree t JOIN ancestors a ON t.id = a.parent_id
)
SELECT * FROM ancestors ORDER BY level;
```
Anchor: node 5. Recursive: rows whose id is the current row’s parent_id. Stops at root (no parent).

---

## Q4. (Intermediate) How do you prevent infinite recursion in a recursive CTE (e.g. cycle in the graph)?

**Answer:**  
(1) Add a **depth limit**: **WHERE level < 100**. (2) **Exclude already-visited nodes**: keep a path (array/set) and **WHERE id NOT IN (SELECT unnest(path))** or use a cycle-detection column. **PostgreSQL**: **WITH RECURSIVE ... CYCLE id SET is_cycle USING path** (or manual path array). Stop when **is_cycle** or when the “visited” set would grow. Always bound depth or detect cycles in production.

---

## Q5. (Intermediate) In Oracle, how do you query a hierarchy without a recursive CTE? What is CONNECT BY?

**Answer:**  
**CONNECT BY**: **SELECT * FROM tree START WITH id = 5 CONNECT BY PRIOR parent_id = id** (ancestors). **START WITH parent_id IS NULL CONNECT BY PRIOR id = parent_id** (descendants from root). **LEVEL**, **SYS_CONNECT_BY_PATH**, **CONNECT_BY_ROOT** are available. **NOCYCLE** and **CONNECT_BY_ISCYCLE** handle cycles. Oracle 11g+ also supports recursive CTEs (WITH ...).

---

## Q6. (Advanced) Write a recursive CTE that lists all descendants of a given node (e.g. all reports under manager 3).

**Answer:**  
**PostgreSQL**:
```sql
WITH RECURSIVE descendants AS (
  SELECT id, name, parent_id, 1 AS level FROM employees WHERE id = 3
  UNION ALL
  SELECT e.id, e.name, e.parent_id, d.level + 1
  FROM employees e JOIN descendants d ON e.parent_id = d.id
)
SELECT * FROM descendants ORDER BY level;
```
Anchor: manager 3. Recursive: employees whose parent_id is in the current set. Stops when no more children.

---

## Q7. (Advanced) How do you compute “depth” or “level” and “path” (e.g. root-to-node string) in a recursive CTE?

**Answer:**  
**Level**: increment in the recursive term (e.g. **anchor: level 1**, **recursive: level + 1**). **Path**: in the recursive term, append the current node to the path. **PostgreSQL**: **path || id** or **array_append(path, id)**; pass **path** in the CTE columns. **MySQL**: **CONCAT(path, ',', id)**. Use path for cycle detection (if id already in path, stop) and for displaying the hierarchy.

---

## Q8. (Advanced) Production scenario: A “category” table has (id, parent_id, name). You need an API that returns the full category tree (nested JSON). Should you build the tree in SQL (recursive CTE) or in the backend? Outline both approaches.

**Answer:**  
**SQL**: Recursive CTE to get (id, parent_id, name, level) or (id, path). Return a flat list; backend builds the tree (group by parent_id, build nested dict/array). **Backend**: Single query with recursive CTE or “all categories” + build tree in memory (one query: **SELECT * FROM categories**; build tree by parent_id). Prefer **one query** (recursive or full table) and **build tree in backend** for flexibility and to avoid DB-specific tree formatting. For very deep trees, recursive CTE with depth limit; cache the tree if it changes rarely.

---

## Q9. (Advanced) What is the performance concern with recursive CTEs on large graphs? How do you mitigate?

**Answer:**  
Recursive CTEs can do many iterations and touch many rows; they can be slow and memory-heavy. **Mitigate**: (1) **Index** (parent_id, id) so each recursive step is a lookup. (2) **Limit depth**: **WHERE level <= N**. (3) **Cycle detection** to avoid infinite loops. (4) For “all descendants of X,” ensure the anchor is selective (one node). (5) Consider **materialized path** or **closure table** if you need “all ancestors/descendants” very often (precompute and store).

---

## Q10. (Advanced) Compare recursive CTE syntax and limits in PostgreSQL, MySQL 8, and Oracle.

**Answer:**  
**PostgreSQL**: **WITH RECURSIVE**; no strict iteration limit (until no rows); cycle detection with **CYCLE** or manual. **MySQL 8**: **WITH RECURSIVE**; **cte_max_recursion_depth** (default 1000) limits iterations. **Oracle**: **CONNECT BY** (legacy) or **WITH** recursive (11g+); **CONNECT_BY_ISCYCLE**, **NOCYCLE**. All support the same idea; syntax for path and cycle differs. Backend: use standard recursive CTE where possible; set recursion limit in MySQL; test with large hierarchies.
