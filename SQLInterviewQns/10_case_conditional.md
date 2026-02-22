# 10. CASE and Conditional Logic

## Q1. (Beginner) What is the syntax of a simple CASE expression? When is it evaluated?

**Answer:**  
**CASE WHEN condition1 THEN result1 WHEN condition2 THEN result2 ELSE default END**. It is an **expression** (returns a value); can be used in SELECT, WHERE, ORDER BY, etc. Evaluated in order; first matching WHEN wins. **ELSE** is optional (NULL if omitted and no match).

---

## Q2. (Beginner) What is the difference between CASE in SELECT and CASE in WHERE?

**Answer:**  
In **SELECT**, CASE produces a **value** per row (e.g. a label or computed column). In **WHERE**, CASE is used in a **condition** (e.g. **WHERE CASE WHEN x THEN 1 ELSE 0 END = 1**), but it’s often clearer to write **WHERE (x)** or **WHERE condition**. Use CASE in WHERE when you need different predicates (e.g. “if param=1 filter by A, else by B”).

---

## Q3. (Intermediate) Write a query that returns a column **bucket**: “low” if amount < 100, “mid” if 100–500, “high” if > 500.

**Answer:**
```sql
SELECT id, amount,
  CASE
    WHEN amount < 100 THEN 'low'
    WHEN amount <= 500 THEN 'mid'
    ELSE 'high'
  END AS bucket
FROM orders;
```
Order of WHEN matters; put more specific conditions first if they overlap.

---

## Q4. (Intermediate) How do you use CASE in ORDER BY to implement custom sort order (e.g. status: “pending” first, then “active”, then “done”)?

**Answer:**  
**ORDER BY CASE status WHEN 'pending' THEN 1 WHEN 'active' THEN 2 WHEN 'done' THEN 3 ELSE 4 END**. Or **ORDER BY CASE WHEN status = 'pending' THEN 1 ... END**. This gives a numeric ordering that you control. Same idea for “NULLs last”: **ORDER BY col NULLS LAST** or **CASE WHEN col IS NULL THEN 1 ELSE 0 END, col**.

---

## Q5. (Intermediate) What is NULLIF? Give an example where it avoids division by zero.

**Answer:**  
**NULLIF(a, b)** returns NULL if a = b, else a. **SELECT amount / NULLIF(quantity, 0) AS unit_price** — when quantity is 0, NULLIF returns NULL, so division result is NULL instead of error. Handle the NULL in application or with COALESCE (e.g. **COALESCE(amount/NULLIF(quantity,0), 0)**).

---

## Q6. (Advanced) Write a query that pivots rows into columns using CASE (e.g. count of orders per status as separate columns: pending_count, active_count).

**Answer:**
```sql
SELECT
  COUNT(CASE WHEN status = 'pending' THEN 1 END) AS pending_count,
  COUNT(CASE WHEN status = 'active' THEN 1 END)  AS active_count,
  COUNT(CASE WHEN status = 'done' THEN 1 END)    AS done_count
FROM orders;
```
Or **SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END)**. Use when you need a fixed set of columns; for dynamic pivoting use application code or DB-specific PIVOT (e.g. SQL Server, Oracle).

---

## Q7. (Advanced) How do you implement “conditional WHERE” (e.g. filter by optional parameter: if @status is provided filter by it, else ignore)?

**Answer:**  
**WHERE (@status IS NULL OR status = @status)**. When **@status** is NULL the first part is true so the filter is skipped; when provided, **status = @status** is applied. Same for multiple optional params: **WHERE (@a IS NULL OR col_a = @a) AND (@b IS NULL OR col_b = @b)**. Backend: pass NULL for “no filter” and use parameterized queries.

---

## Q8. (Advanced) Production scenario: A dashboard shows “traffic tier” per customer: “high” (>= 1000 requests/month), “medium” (100–999), “low” (< 100). Data is in `usage` (customer_id, month, request_count). Write the query and mention how you’d cache or materialize it for the dashboard.

**Answer:**
```sql
SELECT customer_id, month, request_count,
  CASE
    WHEN request_count >= 1000 THEN 'high'
    WHEN request_count >= 100 THEN 'medium'
    ELSE 'low'
  END AS traffic_tier
FROM usage
WHERE month = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month');
```
For dashboard: run nightly or on a schedule; store result in a **materialized view** or **dashboard_usage** table and serve the UI from that. Add index on (month, customer_id) for the source table. Backend: read from the precomputed table; avoid running heavy aggregation on every page load.

---

## Q9. (Advanced) What is the difference between COALESCE and CASE for providing defaults? When is each better?

**Answer:**  
**COALESCE(a, b, c)** is shorthand for “first non-NULL among a, b, c.” **CASE** can express any condition (e.g. **CASE WHEN col < 0 THEN 0 ELSE col END**). Use COALESCE for “first non-NULL”; use CASE for ranges, complex logic, or when the “default” depends on another column.

---

## Q10. (Advanced) In MySQL, how do you simulate IFNULL or provide a default? How does Oracle’s NVL relate?

**Answer:**  
**MySQL**: **IFNULL(a, b)** — same as **COALESCE(a, b)** for two arguments. **Oracle**: **NVL(a, b)** — returns b if a is NULL. **NVL2(a, b, c)** — returns b if a is not NULL, else c. **COALESCE** is standard and multi-argument; use it for portability where possible.
