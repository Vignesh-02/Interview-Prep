# 11. HAVING vs WHERE

## Q1. (Beginner) What is the difference between WHERE and HAVING?

**Answer:**  
**WHERE** filters **rows** before grouping (and before aggregates are computed). **HAVING** filters **groups** after GROUP BY (and can use aggregate expressions). So: WHERE on raw columns; HAVING on group-level conditions (aggregates or columns in GROUP BY).

---

## Q2. (Beginner) Can you use an aggregate function in WHERE? In HAVING?

**Answer:**  
You **cannot** use aggregates in **WHERE** (aggregates don’t exist yet). You **can** use them in **HAVING** (e.g. **HAVING COUNT(*) > 1**, **HAVING SUM(amount) > 1000**). To filter by an aggregate, use HAVING or a subquery/CTE that computes the aggregate and then filter in an outer WHERE.

---

## Q3. (Intermediate) Write a query that lists departments that have more than 5 employees. Use HAVING.

**Answer:**
```sql
SELECT dept_id, COUNT(*) AS emp_count
FROM employees
GROUP BY dept_id
HAVING COUNT(*) > 5;
```
HAVING runs after GROUP BY, so you can filter on **COUNT(*)**.

---

## Q4. (Intermediate) Can you reference a SELECT alias in HAVING? What about in WHERE?

**Answer:**  
In standard SQL, **HAVING** can reference **aggregates** and **GROUP BY** columns; whether it can use a **SELECT** alias is DB-dependent (e.g. PostgreSQL allows **HAVING count > 5** if **count** is an alias for **COUNT(*)** in the same SELECT). **WHERE** cannot use SELECT aliases because WHERE is evaluated before SELECT. Prefer repeating the expression in HAVING (e.g. **HAVING COUNT(*) > 5**) for portability.

---

## Q5. (Intermediate) “Find products that have been ordered at least 3 times.” Write it with GROUP BY and HAVING.

**Answer:**
```sql
SELECT product_id, COUNT(*) AS order_count
FROM order_items
GROUP BY product_id
HAVING COUNT(*) >= 3;
```
If “ordered” means distinct orders: **COUNT(DISTINCT order_id) >= 3**.

---

## Q6. (Advanced) When would you filter in a subquery or CTE with WHERE instead of using HAVING?

**Answer:**  
When the condition is on **raw rows** (not on the group), filter in **WHERE** so fewer rows are grouped (better performance). Example: “departments with more than 5 employees in region ‘US’” — use **WHERE region = 'US'** before GROUP BY, then **HAVING COUNT(*) > 5**. Pushing filters into WHERE reduces the working set before aggregation.

---

## Q7. (Advanced) Write a query: “Customers whose total order amount exceeds the average total order amount per customer.” Use HAVING and a subquery.

**Answer:**
```sql
SELECT customer_id, SUM(amount) AS total
FROM orders
GROUP BY customer_id
HAVING SUM(amount) > (SELECT AVG(cust_total) FROM (SELECT SUM(amount) AS cust_total FROM orders GROUP BY customer_id) t);
```
The subquery computes the average of per-customer totals; HAVING keeps only customers above that average.

---

## Q8. (Advanced) Production scenario: You need “sales reps who had at least 10 deals closed in the last quarter, with total deal value > $50k.” Tables: `deals` (rep_id, closed_at, amount, status). Write the query; should the “last quarter” filter be in WHERE or HAVING?

**Answer:**  
Put **last quarter** in **WHERE** so you only aggregate relevant rows. **HAVING** for group-level conditions:
```sql
SELECT rep_id, COUNT(*) AS deal_count, SUM(amount) AS total_value
FROM deals
WHERE status = 'closed'
  AND closed_at >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
  AND closed_at <  DATE_TRUNC('quarter', CURRENT_DATE)
GROUP BY rep_id
HAVING COUNT(*) >= 10 AND SUM(amount) > 50000;
```
Filtering by time in WHERE reduces rows before grouping; HAVING enforces “at least 10” and “> 50k” per rep.

---

## Q9. (Advanced) In which order does SQL evaluate WHERE, GROUP BY, HAVING, and SELECT? Why does this order matter for performance?

**Answer:**  
Logical order: **FROM** → **WHERE** → **GROUP BY** → **HAVING** → **SELECT** → **ORDER BY**. So WHERE reduces rows before grouping; HAVING filters groups after aggregation. For performance: push as much as possible into WHERE so the engine works on fewer rows and smaller groups. Use HAVING only for conditions that truly depend on aggregates.

---

## Q10. (Advanced) Can you use HAVING without GROUP BY? What does it do?

**Answer:**  
Yes. Without GROUP BY, the whole table is one group. **SELECT COUNT(*) FROM t HAVING COUNT(*) > 0** returns one row if the table has rows, none if empty. Rarely useful; more common with GROUP BY. In standard SQL, HAVING without GROUP BY can only reference aggregates; all rows form a single group.
