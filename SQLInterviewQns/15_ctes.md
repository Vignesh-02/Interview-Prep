# 15. Common Table Expressions (CTEs)

## Q1. (Beginner) What is a CTE? What is the syntax?

**Answer:**  
A **CTE** (Common Table Expression) is a named temporary result set defined with **WITH** and used in the following SELECT (or INSERT/UPDATE/DELETE). Syntax: **WITH cte_name AS (SELECT ...) SELECT * FROM cte_name**. You can have multiple CTEs: **WITH a AS (...), b AS (...) SELECT ...**.

---

## Q2. (Beginner) Can you use a CTE in multiple places in the same query?

**Answer:**  
Yes. The CTE is defined once and can be referenced multiple times in the main query (and in later CTEs if they reference the first). So **WITH t AS (SELECT ...) SELECT * FROM t JOIN t t2 ON ...** is valid. That can simplify repeated subqueries and improve readability.

---

## Q3. (Intermediate) What is the difference between a CTE and a subquery in FROM? When might the optimizer treat them differently?

**Answer:**  
Logically similar: both define a result set. A CTE is named and reusable in the same statement; a subquery is inline. Some optimizers **inline** CTEs (expand them into the outer query); others **materialize** them (compute once). PostgreSQL 12+ can inline or materialize; you can hint with **MATERIALIZED** / **NOT MATERIALIZED** (PostgreSQL). For very large CTEs used once, materialization can be worse (full compute then scan); for small or used multiple times, it can be better.

---

## Q4. (Intermediate) Write a query using a CTE: “total sales per region” and then “regions above average total sales.”

**Answer:**
```sql
WITH region_sales AS (
  SELECT region_id, SUM(amount) AS total
  FROM sales
  GROUP BY region_id
),
avg_sales AS (SELECT AVG(total) AS avg_total FROM region_sales)
SELECT r.* FROM region_sales r
CROSS JOIN avg_sales a
WHERE r.total > a.avg_total;
```
First CTE: per-region total. Second: overall average. Main query: filter regions above average.

---

## Q5. (Intermediate) Can you INSERT/UPDATE/DELETE using a CTE? Give an example.

**Answer:**  
Yes. **WITH to_delete AS (SELECT id FROM t WHERE ...) DELETE FROM t WHERE id IN (SELECT id FROM to_delete)**. **WITH ins AS (SELECT ...) INSERT INTO t SELECT * FROM ins**. Useful to identify rows in the CTE and then modify the table. Syntax is DB-specific (e.g. PostgreSQL, SQL Server support it; MySQL’s CTE support in DML may be limited—check version).

---

## Q6. (Advanced) What is a recursive CTE? What are the anchor and recursive parts?

**Answer:**  
A **recursive CTE** has two parts: (1) **Anchor** — initial SELECT (base case). (2) **Recursive** — SELECT that references the CTE itself, unioned with the anchor. Execution: run anchor once, then repeatedly run the recursive part using the current result set until it returns no rows. Used for hierarchies, graphs, number series.

---

## Q7. (Advanced) Write a non-recursive CTE that ranks products by total sales and then select only the top 3 per category. (Use window function in CTE.)

**Answer:**
```sql
WITH ranked AS (
  SELECT product_id, category_id, SUM(amount) AS total,
         ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY SUM(amount) DESC) AS rn
  FROM sales
  GROUP BY product_id, category_id
)
SELECT * FROM ranked WHERE rn <= 3;
```
CTE computes per-product total and rank per category; main query filters rn <= 3.

---

## Q8. (Advanced) Production scenario: You need “month-over-month growth rate” for each product (current month sales vs previous month). Use a CTE to compute monthly sales, then self-join or use LAG to get previous month. Write the query and note how the backend should cache or materialize this.

**Answer:**
```sql
WITH monthly AS (
  SELECT product_id, DATE_TRUNC('month', sold_at) AS month, SUM(amount) AS total
  FROM sales
  GROUP BY 1, 2
),
with_prev AS (
  SELECT *, LAG(total) OVER (PARTITION BY product_id ORDER BY month) AS prev_total
  FROM monthly
)
SELECT product_id, month, total,
       CASE WHEN prev_total > 0 THEN ROUND((total - prev_total) * 100.0 / prev_total, 2) END AS pct_growth
FROM with_prev
ORDER BY product_id, month;
```
Backend: run as a scheduled report or cache result in a table/materialized view; avoid recalculating on every request. Use **DATE_TRUNC** and **LAG** (or equivalent) per DB.

---

## Q9. (Advanced) In PostgreSQL 12+, what does WITH ... MATERIALIZED / NOT MATERIALIZED do? When would you force materialization?

**Answer:**  
**MATERIALIZED** (default in PG 12+ for CTEs with side effects or multiple references): CTE is computed once and stored. **NOT MATERIALIZED**: CTE can be inlined into the outer query (like a subquery). Force **MATERIALIZED** when the CTE is referenced multiple times and is expensive, so you don’t compute it twice. Force **NOT MATERIALIZED** when the CTE is used once and inlining allows better join order and indexes.

---

## Q10. (Advanced) Does MySQL support CTEs? Does it support recursive CTEs? From which version?

**Answer:**  
**MySQL 8.0+** supports non-recursive and recursive CTEs. Syntax: **WITH ... AS (...) SELECT ...**. Recursive CTEs have the same anchor/recursive structure. Older MySQL: use derived tables (subqueries in FROM) or temp tables. Backend: if you support MySQL < 8, avoid CTEs or provide a fallback (derived table or application-side logic).
