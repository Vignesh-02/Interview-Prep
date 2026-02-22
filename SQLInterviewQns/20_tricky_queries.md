# 20. Tricky Queries and Edge Cases

## Q1. (Beginner) What does “division by zero” return in SQL? How do you avoid it in a query?

**Answer:**  
In most DBs, **col / 0** returns **NULL** (or an error in strict mode). Avoid with **NULLIF**: **col / NULLIF(other_col, 0)** so divisor is NULL when other_col is 0, and the result is NULL. Or **CASE WHEN other_col = 0 THEN NULL ELSE col / other_col END**.

---

## Q2. (Beginner) What happens when you compare anything with NULL using = or <>?

**Answer:**  
**x = NULL** and **x <> NULL** both evaluate to **UNKNOWN** (treated as false in WHERE). So no rows match. Use **IS NULL** and **IS NOT NULL**. For “column equals value or is null when value is null”: **(col = @value OR (col IS NULL AND @value IS NULL))** or **col IS NOT DISTINCT FROM @value** (PostgreSQL).

---

## Q3. (Intermediate) Write a query that returns “the row with the max value in column X” (e.g. the order with the highest amount). Handle ties (return one row).

**Answer:**  
**SELECT * FROM orders ORDER BY amount DESC LIMIT 1** (PostgreSQL/MySQL). Or **SELECT * FROM orders WHERE amount = (SELECT MAX(amount) FROM orders) LIMIT 1**. For “all rows that tie for max”: **WHERE amount = (SELECT MAX(amount) FROM orders)** (no LIMIT). **Oracle**: **FETCH FIRST 1 ROW ONLY** or subquery with ROWNUM.

---

## Q4. (Intermediate) How do you select every Nth row (e.g. every 2nd row)? Is this portable?

**Answer:**  
Use a row number and filter: **SELECT * FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY id) rn FROM t) x WHERE rn % 2 = 0**. Or **WHERE MOD(rn, 2) = 0**. Not fully portable (MOD vs %); ROW_NUMBER is standard in modern DBs. For “every 2nd” you need a deterministic ORDER BY so the Nth is well-defined.

---

## Q5. (Intermediate) What is the difference between “NOT IN (subquery)” and “NOT EXISTS (subquery)” when the subquery can return NULLs?

**Answer:**  
If the subquery returns **any NULL**, **NOT IN** can return **no rows** (because **x NOT IN (a, b, NULL)** is treated as false for all x). **NOT EXISTS** is not affected that way: it only checks for existence of a matching row. Prefer **NOT EXISTS** for “row not in set” when the set might contain NULLs, or ensure the subquery excludes NULLs (e.g. **WHERE id NOT IN (SELECT id FROM t WHERE id IS NOT NULL)**).

---

## Q6. (Advanced) How do you implement “pivot” in standard SQL (e.g. rows to columns: one row per product, columns Jan, Feb, Mar with sales)? Use CASE and GROUP BY.

**Answer:**
```sql
SELECT product_id,
  SUM(CASE WHEN month = 1 THEN amount ELSE 0 END) AS jan,
  SUM(CASE WHEN month = 2 THEN amount ELSE 0 END) AS feb,
  SUM(CASE WHEN month = 3 THEN amount ELSE 0 END) AS mar
FROM sales
GROUP BY product_id;
```
Columns must be fixed at write time. For dynamic columns use application code or DB-specific PIVOT (e.g. SQL Server, Oracle).

---

## Q7. (Advanced) “Find the 2nd highest salary.” Write it without a window function; then with ROW_NUMBER or DENSE_RANK.

**Answer:**  
Without window: **SELECT MAX(salary) FROM employees WHERE salary < (SELECT MAX(salary) FROM employees)**. With window: **SELECT salary FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) rk FROM employees) t WHERE rk = 2**. DENSE_RANK gives same rank for ties; ROW_NUMBER breaks ties arbitrarily. Decide if “2nd” means second distinct value (DENSE_RANK) or second row (ROW_NUMBER).

---

## Q8. (Advanced) Production scenario: You have a log table (id, event_type, created_at). You need “count of events per type in the last 24 hours” and “same for the previous 24 hours” side by side for comparison. Write one query that returns (event_type, count_last_24h, count_prev_24h).

**Answer:**
```sql
SELECT event_type,
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') AS count_last_24h,
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '48 hours' AND created_at < NOW() - INTERVAL '24 hours') AS count_prev_24h
FROM logs
WHERE created_at >= NOW() - INTERVAL '48 hours'
GROUP BY event_type;
```
**FILTER (WHERE ...)** is PostgreSQL; in others use **SUM(CASE WHEN ... THEN 1 ELSE 0 END)**. Index on **created_at** for the time filter.

---

## Q9. (Advanced) How do you do a “running total” or cumulative sum in standard SQL (without window functions)? With window functions?

**Answer:**  
Without window: use a correlated subquery: **SELECT t.id, t.amount, (SELECT SUM(amount) FROM orders o WHERE o.id <= t.id) AS running_total FROM orders t ORDER BY t.id**. Expensive. With window: **SELECT id, amount, SUM(amount) OVER (ORDER BY id) AS running_total FROM orders**. Window is efficient and clear. Use **ORDER BY** in the window for the cumulative order.

---

## Q10. (Advanced) Compare how NULLs are sorted in ORDER BY in PostgreSQL, MySQL, and Oracle. How do you make “NULLs last” portable?

**Answer:**  
**PostgreSQL**: NULLs last by default for ASC, first for DESC; **NULLS FIRST** / **NULLS LAST** explicit. **MySQL**: NULLs first for ASC, last for DESC; no NULLS FIRST/LAST. **Oracle**: NULLs last for ASC, first for DESC; **NULLS FIRST** / **NULLS LAST** supported. Portable “NULLs last”: **ORDER BY col IS NULL, col** (ASC) or **ORDER BY CASE WHEN col IS NULL THEN 1 ELSE 0 END, col**. Or use **COALESCE(col, sentinel)** where sentinel is beyond the data range (e.g. very large value for numbers).
