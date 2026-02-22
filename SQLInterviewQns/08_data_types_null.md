# 8. Data Types, NULL, and COALESCE

## Q1. (Beginner) What does NULL mean in SQL? Is NULL equal to NULL?

**Answer:**  
**NULL** means “unknown” or “missing” value. **NULL = NULL** is not TRUE; it evaluates to **UNKNOWN** (treated as false in WHERE). So use **IS NULL** and **IS NOT NULL** for null checks. In general, any comparison with NULL yields UNKNOWN except for **IS NULL** / **IS NOT NULL**.

---

## Q2. (Beginner) What does COALESCE do? Give an example.

**Answer:**  
**COALESCE(a, b, c, ...)** returns the first argument that is **not NULL**. Example: **COALESCE(middle_name, '')** — use middle name or empty string. **COALESCE(SUM(amount), 0)** — 0 when SUM is NULL (no rows or all NULLs). Useful for defaults and avoiding NULL in results.

---

## Q3. (Intermediate) What is the difference between COALESCE and NULLIF?

**Answer:**  
**COALESCE(x, y)** returns first non-NULL. **NULLIF(a, b)** returns **NULL** if **a = b**, else **a**. So **NULLIF(col, 0)** turns 0 into NULL (e.g. to avoid division by zero: **x / NULLIF(y, 0)**). **COALESCE** picks among values; **NULLIF** conditionally nullifies one value.

---

## Q4. (Intermediate) How do aggregate functions treat NULL (SUM, AVG, COUNT)?

**Answer:**  
**SUM**, **AVG**, **MIN**, **MAX** **ignore** NULL (only non-NULL values participate). **COUNT(column)** counts non-NULL values; **COUNT(*)** counts rows (including NULLs in other columns). So **AVG** of (10, NULL, 20) is 15; **COUNT(col)** is 2.

---

## Q5. (Intermediate) What are typical numeric and date types in PostgreSQL, MySQL, and Oracle?

**Answer:**  
**Numeric**: PostgreSQL — INTEGER, BIGINT, NUMERIC(p,s), REAL, DOUBLE PRECISION; MySQL — INT, BIGINT, DECIMAL(p,s), FLOAT, DOUBLE; Oracle — NUMBER(p,s), BINARY_FLOAT, BINARY_DOUBLE. **Date/time**: PostgreSQL — DATE, TIMESTAMP, TIMESTAMPTZ, INTERVAL; MySQL — DATE, DATETIME, TIMESTAMP; Oracle — DATE (includes time), TIMESTAMP, INTERVAL. Use TIMESTAMPTZ for time zones when needed.

---

## Q6. (Advanced) Why does “WHERE col NOT IN (subquery)” return no rows when the subquery returns any NULL?

**Answer:**  
**col NOT IN (a, b, NULL)** is equivalent to **col <> a AND col <> b AND col <> NULL**. **col <> NULL** is UNKNOWN, so the whole AND is UNKNOWN (false). So NOT IN with any NULL yields no rows. Fix: use **NOT EXISTS** or ensure the subquery excludes NULLs (**WHERE col NOT IN (SELECT x FROM t WHERE x IS NOT NULL)**).

---

## Q7. (Advanced) How do you replace NULL with a default in a SELECT without changing the table? What about in an ORDER BY (sort NULLs last)?

**Answer:**  
**SELECT COALESCE(col, 0) AS col FROM t**. For ORDER BY: **ORDER BY col NULLS LAST** (PostgreSQL); or **ORDER BY COALESCE(col, -1)** or a sentinel value so NULLs sort last. **ORDER BY col IS NULL, col** in MySQL (NULLs first when ASC).

---

## Q8. (Advanced) Production scenario: A reporting query joins `orders` with `refunds`. Some orders have no refund; `refund.amount` is NULL. You need “order total minus refund total” per order. How do you handle NULLs so the report is correct?

**Answer:**  
**SELECT o.order_id, o.total - COALESCE(SUM(r.amount), 0) AS net_total FROM orders o LEFT JOIN refunds r ON r.order_id = o.order_id GROUP BY o.order_id, o.total**. **COALESCE(SUM(r.amount), 0)** turns NULL (no refunds) into 0 so **o.total - 0** is correct. Without COALESCE, **total - NULL** is NULL. Backend: ensure the report type (e.g. decimal) handles the result; no division by zero if you add computed ratios later.

---

## Q9. (Advanced) What is the difference between VARCHAR and TEXT in PostgreSQL and MySQL? When would you choose one over the other?

**Answer:**  
**PostgreSQL**: VARCHAR(n) has a length limit; TEXT has no limit (stored the same internally). Prefer TEXT for unbounded strings. **MySQL**: VARCHAR(n) stored inline up to a size; TEXT is off-page. VARCHAR is better for indexing and when you have a sensible max length. **Oracle**: VARCHAR2(n); no TEXT type like PostgreSQL. Backend: map to string type; watch max length for APIs (e.g. VARCHAR(255) vs TEXT).

---

## Q10. (Advanced) How do PostgreSQL, MySQL, and Oracle handle boolean types? What if a column is “truthy” (0/1 or 'Y'/'N')?

**Answer:**  
**PostgreSQL**: Native **BOOLEAN** (true/false). **MySQL**: TINYINT(1) or BOOLEAN (alias); 0/1. **Oracle**: No native boolean; use NUMBER(1) or CHAR(1) 'Y'/'N'. For “truthy” columns: in SQL use **CASE WHEN col IN (1, 'Y', 'true') THEN true ELSE false END** or application-side mapping. Backend: use driver types (e.g. bool in Python/Node) and map DB representation consistently.
