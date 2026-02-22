# 2. JOINs (INNER, LEFT, RIGHT, FULL)

## Q1. (Beginner) What is the difference between INNER JOIN and LEFT (OUTER) JOIN?

**Answer:**  
**INNER JOIN** returns only rows where there is a match in both tables. **LEFT JOIN** returns all rows from the left table and matching rows from the right; if no match, right-side columns are NULL. So LEFT JOIN keeps “all from left”; INNER keeps only “matching pairs.”

---

## Q2. (Beginner) How do you join two tables on a common column? Write the syntax.

**Answer:**  
**SELECT * FROM a INNER JOIN b ON a.id = b.a_id**. Or with USING if the column name is the same: **JOIN b USING (id)**. Always specify ON (or USING) to avoid accidental cross joins. Prefer explicit JOIN over comma (old-style) for clarity.

---

## Q3. (Intermediate) What is a CROSS JOIN? When would you use it?

**Answer:**  
**CROSS JOIN** returns the Cartesian product: every row of A paired with every row of B. No ON clause. Use for “all combinations” (e.g. every product × every store, or generating a series). Can be expensive; use with small sets or with WHERE to limit.

---

## Q4. (Intermediate) Write a query that lists all employees and their department name. Include employees with no department (NULL department name).

**Answer:**
```sql
SELECT e.emp_id, e.name, d.dept_name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.dept_id;
```
LEFT JOIN keeps all employees; missing department shows as NULL in **dept_name**.

---

## Q5. (Intermediate) What is the difference between RIGHT JOIN and LEFT JOIN? How can you rewrite a RIGHT JOIN as a LEFT JOIN?

**Answer:**  
**RIGHT JOIN** keeps all rows from the right table and matches from the left. **A RIGHT JOIN B** is the same as **B LEFT JOIN A** (swap table order and use LEFT). Most codebases use LEFT JOIN and swap table order instead of RIGHT for consistency.

---

## Q6. (Advanced) What is a FULL OUTER JOIN? Give a practical use case and write an example.

**Answer:**  
**FULL OUTER JOIN** returns all rows from both tables; matched where possible, NULLs where no match. Use case: “all customers and all orders, with matches where they exist” or comparing two lists (in both, only in A, only in B). Example: **SELECT * FROM a FULL OUTER JOIN b ON a.id = b.a_id**. MySQL doesn’t have FULL OUTER JOIN; emulate with UNION of LEFT and RIGHT (excluding inner).

---

## Q7. (Advanced) How do you join more than two tables? What order does the optimizer use?

**Answer:**  
Chain JOINs: **FROM a JOIN b ON ... JOIN c ON ...**. The logical order is determined by ON conditions; the physical order is chosen by the optimizer. Order of tables in FROM can affect which join algorithm is used (e.g. smaller table first for nested loops). Use explicit JOINs and let the optimizer decide unless you have a reason to force order.

---

## Q8. (Advanced) Production scenario: You have `orders`, `order_items`, and `products`. You need “all orders with at least one item, with product names, and total amount per order.” One order can have many items. Write the query and state how the backend should consume it (single query vs N+1).

**Answer:**
```sql
SELECT o.order_id, o.created_at,
       p.name AS product_name, oi.quantity, oi.unit_price,
       SUM(oi.quantity * oi.unit_price) OVER (PARTITION BY o.order_id) AS order_total
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
ORDER BY o.order_id, oi.order_item_id;
```
Or get order total via subquery or GROUP BY in a CTE, then JOIN. Backend: run this **single query** and group by order in app code, or use two queries (orders, then order_items + products by order_ids) to avoid N+1. Prefer one query with JOINs or a CTE for simplicity and fewer round-trips.

---

## Q9. (Advanced) What is a “theta join” vs “equi join”? Can you write a join condition that is not equality?

**Answer:**  
**Equi join** — condition is equality (a.id = b.id). **Theta join** — condition is any predicate (e.g. **a.value > b.value**, **a.date BETWEEN b.start AND b.end**). Example: **FROM a JOIN b ON a.amount > b.threshold**. Non-equi joins can be expensive (harder to use indexes); consider filtering in WHERE or restructuring data.

---

## Q10. (Advanced) In PostgreSQL vs MySQL vs Oracle, what are the main differences in join behavior or syntax you should be aware of?

**Answer:**  
- **FULL OUTER JOIN**: PostgreSQL and Oracle support it; MySQL does not (emulate with UNION).  
- **JOIN ... ON** vs **USING**: All support both; USING requires same column name.  
- **NATURAL JOIN**: All support; joins on all same-named columns (risky if schema changes).  
- **LATERAL** (PostgreSQL): Allows correlated subquery in FROM; Oracle has LATERAL; MySQL 8.0+ has LATERAL.  
- **Optimizer**: Each DB has different join algorithms (hash, merge, nested loop) and hints; use EXPLAIN/EXPLAIN PLAN to compare. Backend: use parameterized queries and standard JOIN syntax for portability; use dialect-specific features only when needed.
