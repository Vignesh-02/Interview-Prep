# 1. SELECT, WHERE, and Basic Filtering

## Q1. (Beginner) What is the order of evaluation of SELECT, FROM, and WHERE? Which runs first logically?

**Answer:**  
Logically: **FROM** (which tables) → **WHERE** (filter rows) → **SELECT** (which columns and expressions). So you cannot use a column alias defined in SELECT inside WHERE; the alias doesn’t exist yet when WHERE runs. In standard SQL, ORDER BY can use SELECT aliases because it runs after SELECT.

---

## Q2. (Beginner) How do you select all columns from a table? Why might that be a bad idea in production code?

**Answer:**  
**SELECT * FROM table_name**. In production, avoid **SELECT *** because: (1) schema changes (new/removed columns) break application code or expose sensitive columns; (2) you fetch more data than needed; (3) it hurts clarity and refactoring. Prefer listing columns explicitly.

---

## Q3. (Intermediate) Write a query that returns rows where a column is NULL. Why does `col = NULL` not work?

**Answer:**  
**SELECT * FROM t WHERE col IS NULL**. **col = NULL** is always unknown (not true) in SQL because NULL is not equal to anything, including itself. Use **IS NULL** and **IS NOT NULL** for null checks.

---

## Q4. (Intermediate) How do you filter with multiple conditions using AND and OR? How do you avoid ambiguity?

**Answer:**  
**WHERE a = 1 AND b = 2** or **WHERE a = 1 OR b = 2**. When mixing AND and OR, use parentheses: **WHERE (a = 1 OR a = 2) AND b = 3**. Without parentheses, AND binds first and can change the meaning. Always use parentheses when combining AND and OR.

---

## Q5. (Intermediate) What is the difference between **IN (list)** and **BETWEEN**? When would you use each?

**Answer:**  
**IN (a, b, c)** — row matches any of the listed values. **BETWEEN x AND y** — inclusive range (col >= x AND col <= y). Use **IN** for discrete values (e.g. status in ('active','pending')); use **BETWEEN** for ranges (e.g. date or number range). **BETWEEN** is inclusive on both ends.

---

## Q6. (Advanced) Write a query that finds customers who have never placed an order, using only SELECT and WHERE (no JOIN). Use a subquery.

**Answer:**
```sql
SELECT * FROM customers c
WHERE NOT EXISTS (
  SELECT 1 FROM orders o WHERE o.customer_id = c.id
);
```
Or: **SELECT * FROM customers WHERE id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL);** — be careful with NULLs in NOT IN (if any customer_id is NULL, NOT IN can return no rows). **NOT EXISTS** is usually safer.

---

## Q7. (Advanced) How do you select distinct combinations of two columns? What if you want to count how many times each combination appears?

**Answer:**  
Distinct combinations: **SELECT DISTINCT col1, col2 FROM t**. Count per combination: **SELECT col1, col2, COUNT(*) FROM t GROUP BY col1, col2**. DISTINCT removes duplicate rows; GROUP BY aggregates and can return counts.

---

## Q8. (Advanced) Production scenario: You have a `users` table and an `audit_log` table. Business wants “all users who logged in during the last 7 days.” The audit log has `user_id`, `action`, and `created_at`. Write the query and mention how you’d index for performance.

**Answer:**
```sql
SELECT DISTINCT u.id, u.email
FROM users u
WHERE EXISTS (
  SELECT 1 FROM audit_log a
  WHERE a.user_id = u.id
    AND a.action = 'login'
    AND a.created_at >= CURRENT_DATE - INTERVAL '7 days'
);
```
Indexes: **audit_log(action, created_at)** or **audit_log(user_id, action, created_at)** so the EXISTS subquery can use an index. Backend: run once per report; avoid N+1 by not querying per user.

---

## Q9. (Advanced) Compare how PostgreSQL, MySQL, and Oracle handle **LIMIT**/pagination syntax. Write equivalent “top 10 rows” queries.

**Answer:**  
- **PostgreSQL / MySQL**: **SELECT * FROM t ORDER BY id LIMIT 10**.  
- **MySQL**: **LIMIT 10 OFFSET 20** for skip/take.  
- **Oracle**: **SELECT * FROM ( SELECT t.*, ROWNUM rn FROM t WHERE ROWNUM <= 10 ) WHERE rn >= 1**; or **FETCH FIRST 10 ROWS ONLY** (12c+): **SELECT * FROM t ORDER BY id FETCH FIRST 10 ROWS ONLY**.  
- **SQL Server**: **TOP 10** or **ORDER BY id OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY**.

---

## Q10. (Advanced) What is short-circuit evaluation in WHERE? Does SQL guarantee that conditions are evaluated left-to-right, and can that affect performance?

**Answer:**  
SQL does **not** guarantee left-to-right evaluation of WHERE clauses. The optimizer can reorder predicates. So don’t rely on “cheap condition first” to avoid evaluating an expensive one. For expensive checks (e.g. function on column), consider filtering in application code or using a computed/indexed column so the engine can use indexes and statistics effectively.
