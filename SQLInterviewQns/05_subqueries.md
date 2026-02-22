# 5. Subqueries

## Q1. (Beginner) What is a subquery? Name two places a subquery can appear.

**Answer:**  
A **subquery** is a SELECT inside another statement. It can appear in **WHERE** (e.g. **WHERE col IN (SELECT ...)**), in **FROM** (derived table), in **SELECT** (scalar subquery), or in **INSERT/UPDATE**. Subqueries can be correlated (reference outer query) or uncorrelated.

---

## Q2. (Beginner) What is a scalar subquery? What must it return?

**Answer:**  
A **scalar** subquery returns exactly **one row and one column**. It can be used where a single value is expected (SELECT list, WHERE). If it returns no rows, it evaluates to NULL; if more than one row, it is an error in standard SQL. Example: **SELECT name, (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) FROM customers c**.

---

## Q3. (Intermediate) What is the difference between IN (subquery) and EXISTS (subquery)? When might EXISTS be faster?

**Answer:**  
**IN (subquery)** — subquery returns a set of values; row is kept if column is in that set. **EXISTS (subquery)** — returns true if subquery returns at least one row; often used with correlated subquery. **EXISTS** can be faster because the DB can stop evaluating the subquery after the first match (short-circuit). For “row exists in related table,” EXISTS is often preferred and handles NULLs in the column correctly (NOT IN with NULLs can return no rows).

---

## Q4. (Intermediate) Write a query that finds employees whose salary is above the average salary. Use a subquery.

**Answer:**
```sql
SELECT * FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```
The subquery returns one value (average); WHERE compares each row to it. Alternative: **SELECT * FROM employees e WHERE salary > (SELECT AVG(salary) FROM employees)** — same.

---

## Q5. (Intermediate) What is a correlated subquery? How does it differ from an uncorrelated one?

**Answer:**  
A **correlated** subquery references columns from the outer query (e.g. **WHERE o.customer_id = c.id**). It is evaluated once per row (or per group) of the outer query. An **uncorrelated** subquery can be evaluated once; its result does not depend on the outer row. Correlated subqueries can be expensive; consider rewriting with JOIN or window functions.

---

## Q6. (Advanced) Rewrite this correlated subquery as a JOIN: “Customers who have placed at least one order in the last 30 days.”

**Answer:**  
Correlated: **SELECT * FROM customers c WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id AND o.created_at >= CURRENT_DATE - 30)**.  
JOIN: **SELECT DISTINCT c.* FROM customers c JOIN orders o ON o.customer_id = c.id AND o.created_at >= CURRENT_DATE - 30**. Use DISTINCT if customers can have multiple matching orders. JOIN is often optimized better; EXISTS can be better when you only need “exists” and no columns from the other table.

---

## Q7. (Advanced) When can you use a subquery in the FROM clause? What must you give it (e.g. in PostgreSQL)?

**Answer:**  
A subquery in **FROM** is a **derived table**. It must have an **alias** in most DBs: **SELECT * FROM (SELECT id, name FROM t) AS sub**. You can reference its columns as **sub.id**, etc. Use for multi-step logic, limiting/ordering before a join, or pre-aggregation. In PostgreSQL, **AS** is optional for aliases but recommended.

---

## Q8. (Advanced) Production scenario: You need “all users who have not logged in for 90 days” for a re-engagement campaign. Tables: `users`, `logins` (user_id, login_at). Write the query; then suggest how the backend (e.g. Node/Python) should run it (batch size, indexing).

**Answer:**
```sql
SELECT u.id, u.email
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM logins l
  WHERE l.user_id = u.id
    AND l.login_at >= CURRENT_DATE - INTERVAL '90 days'
);
```
Index: **logins(user_id, login_at)** so the EXISTS subquery is efficient. Backend: run once (or on a schedule); stream or paginate with **LIMIT/OFFSET** or keyset if the result is huge. Use a batch job (e.g. 10k user IDs per batch) to send emails to avoid long-running transactions and memory spikes.

---

## Q9. (Advanced) What is the difference between ANY/SOME and ALL with subqueries? Give an example of each.

**Answer:**  
**col = ANY (subquery)** — true if col equals any value returned (same as IN). **col > ALL (subquery)** — true if col is greater than every value (i.e. greater than MAX of subquery). **col > ANY (subquery)** — true if greater than at least one (i.e. greater than MIN). Example: “salary greater than all in department 5”: **WHERE salary > ALL (SELECT salary FROM employees WHERE dept_id = 5)**. ALL/ANY can be rewritten with MAX/MIN subqueries for readability.

---

## Q10. (Advanced) In MySQL, how does the optimizer handle IN (subquery) vs EXISTS? When might you force materialization?

**Answer:**  
MySQL can convert **IN (subquery)** to a semi-join or materialize the subquery. **EXISTS** is often executed as a semi-join (stop at first match). For large, uncorrelated subqueries, materialization can be better; for correlated, semi-join is typical. You can sometimes influence with hints (e.g. **SEMIJOIN** or **MATERIALIZATION** in MySQL). Use EXPLAIN to see the chosen strategy and add indexes or rewrite (e.g. to JOIN) if slow.
