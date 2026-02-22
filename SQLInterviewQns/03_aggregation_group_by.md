# 3. Aggregation and GROUP BY

## Q1. (Beginner) Name five common aggregate functions. What do they return when applied to an empty set or all NULLs?

**Answer:**  
**COUNT**, **SUM**, **AVG**, **MIN**, **MAX**. **COUNT(*)** on no rows → 0; **COUNT(column)** → 0; **SUM/AVG/MIN/MAX** of no rows or all NULLs → NULL. **COUNT** never returns NULL (returns 0 for no rows). **AVG** ignores NULLs in the column.

---

## Q2. (Beginner) What is GROUP BY? Can you SELECT a column that is not in GROUP BY?

**Answer:**  
**GROUP BY** groups rows that share the same values in the listed columns; aggregates are computed per group. In standard SQL, every column in SELECT must either be in GROUP BY or be an aggregate. So **SELECT region, SUM(sales) FROM t GROUP BY region** is valid; **SELECT region, name, SUM(sales) ... GROUP BY region** is invalid unless **name** is in GROUP BY or inside an aggregate (e.g. MAX(name)). MySQL in only-full-group-by mode enforces this; some modes allow non-aggregated columns (non-deterministic).

---

## Q3. (Intermediate) What is the difference between COUNT(*) and COUNT(column)? What about COUNT(DISTINCT column)?

**Answer:**  
**COUNT(*)** counts all rows in the group (including NULLs). **COUNT(column)** counts rows where **column** is NOT NULL. **COUNT(DISTINCT column)** counts distinct non-NULL values of **column**. So COUNT(*) >= COUNT(column) >= COUNT(DISTINCT column) for a group.

---

## Q4. (Intermediate) Write a query that returns the total sales per region and the number of orders. Include regions with zero orders.

**Answer:**  
If “regions” come from a dimension table: **SELECT r.region_id, r.name, COUNT(o.order_id) AS order_count, COALESCE(SUM(o.amount), 0) AS total_sales FROM regions r LEFT JOIN orders o ON o.region_id = r.region_id GROUP BY r.region_id, r.name**. LEFT JOIN keeps all regions; COUNT(order_id) gives 0 for regions with no orders; SUM with COALESCE gives 0 for NULL.

---

## Q5. (Intermediate) What does GROUP BY with multiple columns do? What is the difference between GROUP BY a, b and GROUP BY a?

**Answer:**  
**GROUP BY a, b** groups by unique **(a, b)** pairs. **GROUP BY a** groups only by **a** (one row per distinct **a**). So GROUP BY a, b produces at least as many groups as GROUP BY a (unless b is determined by a). Each group in GROUP BY a, b is a subset of a group in GROUP BY a.

---

## Q6. (Advanced) Write a query to find the second-highest salary (or second-largest value) in a table. Handle ties and single-row tables.

**Answer:**  
**SELECT MAX(salary) AS second_highest FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);**  
Or with window: **SELECT DISTINCT salary FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) rk FROM employees) t WHERE rk = 2;**  
Single row: first query returns NULL (correct); window returns no row if there is no second. Decide whether “second” means second distinct value (DENSE_RANK) or second row (ROW_NUMBER).

---

## Q7. (Advanced) How do you compute a percentage of total (e.g. each product’s sales as % of total sales) in one query without a self-join?

**Answer:**  
Use a window aggregate: **SELECT product_id, amount, amount * 100.0 / SUM(amount) OVER () AS pct FROM sales;**  
Or with GROUP BY: **SELECT product_id, SUM(amount) AS amt, SUM(amount) * 100.0 / (SELECT SUM(amount) FROM sales) AS pct FROM sales GROUP BY product_id;**. Window avoids subquery and is often clearer.

---

## Q8. (Advanced) Production scenario: A reporting table has one row per day per store with `revenue`. Business wants: total revenue per store, and each store’s share of total (%). Write the SQL; assume very large data—should aggregation be in DB or in the application?

**Answer:**
```sql
WITH totals AS (
  SELECT store_id, SUM(revenue) AS store_total
  FROM daily_revenue
  GROUP BY store_id
),
grand AS (SELECT SUM(store_total) AS total FROM totals)
SELECT t.store_id, t.store_total,
       ROUND(t.store_total * 100.0 / g.total, 2) AS pct
FROM totals t CROSS JOIN grand g
ORDER BY t.store_total DESC;
```
Do aggregation in the **database**: use GROUP BY and the CTE so the DB sends only aggregated rows. Doing it in the app would require fetching all rows (or many) and summing in code—worse for large data and network.

---

## Q9. (Advanced) What is ROLLUP and CUBE (GROUP BY extensions)? Give a one-line use case for each.

**Answer:**  
**ROLLUP** produces subtotals and grand total along a hierarchy: **GROUP BY ROLLUP(a, b)** gives groups (a,b), (a), (). Use for “totals by region, then by country, then overall.” **CUBE** produces all combinations: **GROUP BY CUBE(a, b)** gives (a,b), (a), (b), (). Use for cross-tab style summaries. Syntax varies: PostgreSQL and Oracle support both; MySQL has limited support (check version).

---

## Q10. (Advanced) In PostgreSQL, how do you filter groups by an aggregate (e.g. “only groups where SUM(sales) > 1000”)? How does this differ from filtering before grouping?

**Answer:**  
Use **HAVING**: **SELECT region, SUM(sales) FROM t GROUP BY region HAVING SUM(sales) > 1000**. **WHERE** filters rows **before** grouping; **HAVING** filters **after** grouping (on aggregates or group columns). So “regions with total sales > 1000” must use HAVING. You can also use HAVING with conditions on grouped columns (e.g. HAVING region <> 'Unknown').
