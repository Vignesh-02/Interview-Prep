# 21. Window Functions (RANK, DENSE_RANK, ROW_NUMBER, moving avg) — Senior

## Q1. (Beginner) What is a window function? How does it differ from GROUP BY aggregation?

**Answer:**  
A **window function** computes a value from a set of rows (the “window”) **without** collapsing rows. Each row keeps its identity and gets an extra column (e.g. rank, running total). **GROUP BY** aggregates and returns one row per group. So: GROUP BY reduces rows; window functions add columns to every row. Syntax: **func() OVER (PARTITION BY ... ORDER BY ...)**.

---

## Q2. (Beginner) What do RANK(), DENSE_RANK(), and ROW_NUMBER() return? How do they handle ties?

**Answer:**  
**ROW_NUMBER()** — unique integers 1, 2, 3, …; ties get arbitrary order (e.g. 1, 2, 3 for three equal values). **RANK()** — same rank for ties; next rank skips (e.g. 1, 1, 3). **DENSE_RANK()** — same rank for ties; next rank is consecutive (e.g. 1, 1, 2). Use ROW_NUMBER for “exactly one row per group” (e.g. top 1); use RANK/DENSE_RANK when ties should get the same rank.

---

## Q3. (Intermediate) Write a query that assigns a row number per department (partition by dept_id), ordered by salary descending.

**Answer:**
```sql
SELECT emp_id, dept_id, salary,
       ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rn
FROM employees;
```
Use **PARTITION BY dept_id** so numbering restarts per department; **ORDER BY salary DESC** defines the order.

---

## Q4. (Intermediate) What is the difference between PARTITION BY and GROUP BY?

**Answer:**  
**PARTITION BY** (in a window) defines **groups** for the window function but does **not** reduce rows; every row stays and gets a value per its partition. **GROUP BY** collapses rows into one per group and you use aggregates (SUM, COUNT, etc.). So PARTITION BY = “group for calculation only”; GROUP BY = “collapse to one row per group.”

---

## Q5. (Intermediate) Write a query that computes a 3-month moving average of sales for each product (monthly sales, then average of current and previous 2 months).

**Answer:**  
**PostgreSQL**:
```sql
SELECT product_id, month, sales,
       AVG(sales) OVER (PARTITION BY product_id ORDER BY month
                        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3
FROM monthly_sales;
```
**RANGE** or **ROWS**: ROWS is “physical” rows; RANGE is “logical” (same ORDER BY value). Use ROWS for “last 3 rows”; use RANGE for “last 3 months” if month is the ordering column. **MySQL**: same idea with **RANGE** or **ROWS** (MySQL 8+).

---

## Q6. (Advanced) What is LAG and LEAD? Give a use case for each.

**Answer:**  
**LAG(col, n)** — value of **col** from the **n**th row **before** the current row (in ORDER BY order). **LEAD(col, n)** — value from the **n**th row **after**. Use **LAG** for “previous row” (e.g. previous month sales, delta). Use **LEAD** for “next row” (e.g. next due date). Both take optional default for out-of-window (e.g. first/last row).

---

## Q7. (Advanced) How do you get “top N per group” (e.g. top 3 products by revenue per category) using a window function?

**Answer:**  
**WITH ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY revenue DESC) rn FROM product_revenue) SELECT * FROM ranked WHERE rn <= 3**. Use ROW_NUMBER so each group has exactly one 1, 2, 3 (no ties that would give more than 3). Use DENSE_RANK if you want “all rows that are in top 3 by rank” (could be more than 3 rows if ties).

---

## Q8. (Advanced) Production scenario: A report needs “each customer’s order count and the percentile they fall into (e.g. top 10%, bottom 25%).” Orders are in `orders(customer_id, ...)`. Write the query using window functions and explain how the backend would expose percentiles.

**Answer:**
```sql
WITH cust_counts AS (
  SELECT customer_id, COUNT(*) AS order_count
  FROM orders GROUP BY customer_id
),
with_pct AS (
  SELECT *, NTILE(100) OVER (ORDER BY order_count) AS pct_band
  FROM cust_counts
)
SELECT * FROM with_pct;
```
**NTILE(100)** splits into 100 buckets (percentiles). Or use **PERCENT_RANK()** for continuous 0–1. Backend: return **pct_band** (1–100) or map to “top 10%” (e.g. pct_band >= 90). Cache or materialize for dashboards.

---

## Q9. (Advanced) What is the frame clause (ROWS BETWEEN / RANGE BETWEEN)? What is the default frame for a window with ORDER BY?

**Answer:**  
The **frame** defines which rows are in the window for the current row. **ROWS BETWEEN 2 PRECEDING AND CURRENT ROW** = current row and 2 rows before. **RANGE** is based on the ORDER BY value (e.g. “all rows with same month”). Default with **ORDER BY**: **RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW** (running aggregate). Default without ORDER BY: entire partition. So **SUM() OVER (PARTITION BY x)** = sum of partition; **SUM() OVER (PARTITION BY x ORDER BY y)** = running sum.

---

## Q10. (Advanced) Compare window function support in PostgreSQL, MySQL, and Oracle. Any notable syntax or function differences?

**Answer:**  
**PostgreSQL**: Full support (RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD, NTILE, frame clauses, etc.). **MySQL 8.0+**: Window functions supported; similar to standard. **Oracle**: Long-standing support (RANK, ROW_NUMBER, LAG, LEAD, etc.); **RATIO_TO_REPORT**, **FIRST_VALUE**, **LAST_VALUE**. **MySQL < 8**: No window functions; use variables or self-joins. Backend: use window functions for “per-group” logic without subqueries; ensure DB version supports them (e.g. MySQL 8+).
