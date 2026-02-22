# 22. Query Optimization and Execution Plans — Senior

## Q1. (Beginner) What is an execution plan? How do you get it in PostgreSQL and MySQL?

**Answer:**  
The **execution plan** is how the DB will execute the query (which indexes, join order, scan types). **PostgreSQL**: **EXPLAIN** or **EXPLAIN ANALYZE** (run and show actual times). **MySQL**: **EXPLAIN** or **EXPLAIN FORMAT=JSON**. **Oracle**: **EXPLAIN PLAN FOR ...** then **SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY)**. Use it to see full table scans, missing indexes, or expensive operations.

---

## Q2. (Beginner) What does “full table scan” mean? When might it be acceptable?

**Answer:**  
**Full table scan** means the engine reads every row of the table (no index used). It can be **acceptable** when: the table is small, you need most of the rows, or there’s no selective predicate. It’s a **problem** when the table is large and you need few rows; then an index should be used. Check the plan to see “Seq Scan” (PostgreSQL) or “ALL” (MySQL) and the row estimate.

---

## Q3. (Intermediate) What steps would you take to optimize a slow query? List 4–5.

**Answer:**  
(1) **Get the plan**: EXPLAIN (ANALYZE). (2) **Find bottlenecks**: high cost, large row estimates, sequential scans on big tables. (3) **Check indexes**: add or adjust indexes for WHERE/JOIN/ORDER BY. (4) **Rewrite**: avoid non-sargable predicates (functions on columns, leading %), simplify JOINs, reduce columns. (5) **Schema**: consider partitioning, summary tables, or denormalization for heavy reports. (6) **Tune**: statistics, work_mem (PostgreSQL), buffer pool (MySQL).

---

## Q4. (Intermediate) What is “predicate sargability”? Why is `WHERE LOWER(col) = 'x'` often non-sargable?

**Answer:**  
A predicate is **sargable** when the DB can use an **index** on the column (search argument = sarg). **LOWER(col) = 'x'** is non-sargable because the index is on **col**, not on **LOWER(col)**; the engine must evaluate LOWER for every row. Fix: **expression index** (e.g. **CREATE INDEX ON t (LOWER(col))** ) or store a lowercased column and index that. Same idea for **col + 1 = 5** (use **col = 4**).

---

## Q5. (Intermediate) In EXPLAIN output, what does “Index Scan” vs “Index Only Scan” mean (PostgreSQL)?

**Answer:**  
**Index Scan**: uses the index to find rows, then fetches the row from the table (heap) for remaining columns. **Index Only Scan**: all needed columns are in the index (covering index), so the table is not accessed. Index Only Scan is faster when the index is covering. Use **INCLUDE** or composite indexes to make more queries index-only.

---

## Q6. (Advanced) What are nested loop, hash join, and merge join? When might the optimizer choose each?

**Answer:**  
**Nested loop**: for each row of outer table, scan inner (or index lookup). Good when one side is small or indexed. **Hash join**: build a hash table from one side, probe with the other. Good for large, non-indexed joins and equality. **Merge join**: both sides sorted on join key; merge. Good when both inputs are already sorted (e.g. index order). Optimizer picks based on size, indexes, and cost model.

---

## Q7. (Advanced) How do you use EXPLAIN to detect a missing index? What would you look for?

**Answer:**  
Look for **Seq Scan** (or full scan) on a **large** table when the query has a selective **WHERE** or **JOIN** on a column. High “rows” estimate and “cost” for that node suggest that an index on the filter/join column could reduce work. Add the index, run **ANALYZE** (or equivalent), and compare EXPLAIN again. Also check “Index Cond” vs “Filter” — filter applied after fetch can indicate a useful index wasn’t used for the predicate.

---

## Q8. (Advanced) Production scenario: A query that joins 5 tables and filters by date range is slow. The app runs it on every page load. Outline a systematic approach: how you’d capture the query, get the plan, identify the bottleneck, and fix it. What would you tell the backend team?

**Answer:**  
(1) **Capture**: Enable slow-query log or APM; get the exact SQL and parameters. (2) **Plan**: Run **EXPLAIN (ANALYZE)** with representative parameters. (3) **Find**: Look for sequential scans on large tables, high row estimates, expensive joins. Check if date column is in an index and used. (4) **Fix**: Add composite index (e.g. (date_col, join_key)); avoid functions on date; consider a summary table or materialized view for this report. (5) **Backend**: Cache the result (e.g. 5–15 min), or move to async/reporting DB; use connection pooling and limit concurrency. Never run heavy ad-hoc reports on the OLTP DB at high frequency without caching or pre-aggregation.

---

## Q9. (Advanced) What is “cost” in EXPLAIN? Is it absolute or relative? Can you compare two plans from different databases?

**Answer:**  
**Cost** is an internal unit (e.g. arbitrary “cost units”) used by the planner; it’s not seconds. It’s **relative** within the same DB and config (e.g. work_mem). You can’t directly compare cost numbers across DBs or even across different server configs. Use **EXPLAIN ANALYZE** for **actual time** (ms) to compare. Focus on reducing actual time and logical reads.

---

## Q10. (Advanced) What is a “correlated subquery” in the plan? How might the optimizer handle it (e.g. rewrite to join)?

**Answer:**  
A correlated subquery references the outer query; it’s executed once per outer row (or per group). The optimizer may **rewrite** it to a **semi-join** or **join** + distinct so it’s executed once. Check EXPLAIN: if you see “SubPlan” or many executions of the same node, it may be correlated. Rewriting to **EXISTS** or **JOIN** in your SQL often gives the optimizer a better shape and avoids N executions. Use EXPLAIN to confirm the plan after rewrite.
