# 12. Self-Joins and Hierarchical Data

## Q1. (Beginner) What is a self-join? When would you use one?

**Answer:**  
A **self-join** is joining a table to itself (usually with different aliases). Use when rows in the table relate to other rows in the same table (e.g. employee → manager, category → parent category). You give the table two aliases and join on the relationship column (e.g. **e.manager_id = m.emp_id**).

---

## Q2. (Beginner) Write a query that lists each employee and their manager’s name. Table: employees(id, name, manager_id).

**Answer:**
```sql
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```
LEFT JOIN so employees with no manager (CEO) still appear with NULL manager name.

---

## Q3. (Intermediate) How do you find “employees who have the same manager”? Use a self-join.

**Answer:**  
Join employees to employees on same manager_id and different employee id: **SELECT a.name, b.name FROM employees a JOIN employees b ON a.manager_id = b.manager_id AND a.id < b.id**. **a.id < b.id** avoids duplicate pairs (A-B and B-A) and self-pairs. Or use **a.id <> b.id** and accept both orderings (then use DISTINCT or filter in application).

---

## Q4. (Intermediate) What is a hierarchical or tree structure in a table? How is it usually stored?

**Answer:**  
Stored as **adjacency list**: each row has a **parent_id** (or similar) pointing to another row in the same table. Root has parent_id NULL. To walk the tree you use recursive CTEs (or multiple self-joins for fixed depth). Alternative: path enumeration, nested sets—each has trade-offs for query vs update.

---

## Q5. (Intermediate) Write a query that finds the “grandmanager” (manager of manager) for each employee. Assume at most two levels (employee → manager → grandmanager).

**Answer:**
```sql
SELECT e.name AS employee, m.name AS manager, g.name AS grandmanager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id
LEFT JOIN employees g ON m.manager_id = g.id;
```
Two self-joins: first to manager, second to manager’s manager. For arbitrary depth use a recursive CTE.

---

## Q6. (Advanced) How do you find all ancestors of a given node (e.g. path from node to root) in a table with (id, parent_id)? Use a recursive CTE (syntax for your DB).

**Answer:**  
**PostgreSQL**:
```sql
WITH RECURSIVE ancestors AS (
  SELECT id, parent_id, 1 AS level FROM nodes WHERE id = $given_id
  UNION ALL
  SELECT n.id, n.parent_id, a.level + 1 FROM nodes n JOIN ancestors a ON n.id = a.parent_id
)
SELECT * FROM ancestors ORDER BY level;
```
Anchor: the given node. Recursive part: join to parent until no parent (root). Oracle: CONNECT BY; MySQL 8+: recursive CTE similar to PostgreSQL.

---

## Q7. (Advanced) How do you find all descendants of a given node (e.g. all reports under a manager)? Sketch a recursive CTE.

**Answer:**  
**PostgreSQL**:
```sql
WITH RECURSIVE descendants AS (
  SELECT id, parent_id, 1 AS level FROM nodes WHERE id = $given_id
  UNION ALL
  SELECT n.id, n.parent_id, d.level + 1 FROM nodes n JOIN descendants d ON n.parent_id = d.id
)
SELECT * FROM descendants;
```
Anchor: the given node. Recursive: rows whose parent_id is in the current set. Stop when no more children.

---

## Q8. (Advanced) Production scenario: An org chart is stored as (employee_id, name, manager_id). You need an API that returns a subtree for a given manager: all direct and indirect reports with their level (1 = direct report). Design the query and suggest how the backend (e.g. Node/Python) should expose it (single query vs recursive fetch).

**Answer:**  
Use a **recursive CTE** to get all descendants and their depth:
```sql
WITH RECURSIVE subtree AS (
  SELECT employee_id, name, manager_id, 1 AS level
  FROM employees WHERE manager_id = $manager_id
  UNION ALL
  SELECT e.employee_id, e.name, e.manager_id, s.level + 1
  FROM employees e JOIN subtree s ON e.manager_id = s.employee_id
)
SELECT * FROM subtree ORDER BY level, name;
```
Backend: run **one** query with parameter **$manager_id**; build the tree in memory (group by level or parent) if the API needs a nested JSON structure. Avoid N+1 (one query per level or per employee).

---

## Q9. (Advanced) What is the risk of a self-join on a very deep hierarchy (e.g. 10 levels)? How does a recursive CTE compare?

**Answer:**  
Self-joining 10 times (e.g. e → m1 → m2 → … → m10) requires 10 JOINs and is verbose and fixed-depth. A **recursive CTE** handles arbitrary depth in one definition and stops when no more rows are found. Recursive CTEs can be expensive on very wide/deep trees; set a max depth (e.g. **WHERE level <= 20**) and index **parent_id** (and **id**) for performance.

---

## Q10. (Advanced) In Oracle, how do you query a hierarchy using CONNECT BY? How do you get the path from root to leaf?

**Answer:**  
**SELECT * FROM employees START WITH manager_id IS NULL CONNECT BY PRIOR id = manager_id** — from root(s) down. **START WITH id = 123 CONNECT BY PRIOR parent_id = id** — ancestors of node 123. **PATH**: use **SYS_CONNECT_BY_PATH(name, '/')** to get a string path. **LEVEL** gives depth. **CONNECT BY** is Oracle-specific; recursive CTEs are standard and available in PostgreSQL, MySQL 8+, SQL Server, Oracle 11g+.
