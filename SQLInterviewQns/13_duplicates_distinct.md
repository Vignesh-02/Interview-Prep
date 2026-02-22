# 13. Duplicates and DISTINCT

## Q1. (Beginner) What does DISTINCT do? Does it work on one column or the whole row?

**Answer:**  
**DISTINCT** removes duplicate **rows** from the result. So **SELECT DISTINCT a, b** returns unique **(a, b)** pairs. It’s row-level, not per-column. To get distinct values of one column while selecting others, use **DISTINCT ON** (PostgreSQL) or **GROUP BY** that column (and aggregate or pick others).

---

## Q2. (Beginner) What is the difference between COUNT(*) and COUNT(DISTINCT col)?

**Answer:**  
**COUNT(*)** counts all rows in the group. **COUNT(DISTINCT col)** counts distinct non-NULL values of **col**. So for (1, 1, 2, NULL), COUNT(*) = 4, COUNT(DISTINCT col) = 2. Use COUNT(DISTINCT col) when you want “number of unique values.”

---

## Q3. (Intermediate) How do you find duplicate rows (same values in key columns)? Return one row per duplicate set with a count.

**Answer:**  
**SELECT col1, col2, COUNT(*) FROM t GROUP BY col1, col2 HAVING COUNT(*) > 1**. This returns the duplicate **key** and how many times it appears. To see all rows that are duplicates, join back: **SELECT t.* FROM t JOIN (SELECT col1, col2 FROM t GROUP BY col1, col2 HAVING COUNT(*) > 1) d ON t.col1 = d.col1 AND t.col2 = d.col2**.

---

## Q4. (Intermediate) How do you delete duplicate rows but keep one (e.g. keep the row with the smallest id)? Give a generic approach.

**Answer:**  
**PostgreSQL**: **DELETE FROM t t1 USING t t2 WHERE t1.key_col = t2.key_col AND t1.id > t2.id** (keeps min id per key). Or with CTE: **WITH dupes AS (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY key_col ORDER BY id) rn FROM t) x WHERE rn > 1) DELETE FROM t WHERE id IN (SELECT id FROM dupes)**. **MySQL**: similar with a delete join or temp table (syntax varies; some versions can’t reference same table in subquery of DELETE). Run in a transaction; backup or test on copy first.

---

## Q5. (Intermediate) When would you use DISTINCT vs GROUP BY to get unique rows?

**Answer:**  
**DISTINCT** when you only need unique rows and no aggregates. **GROUP BY** when you need uniqueness **and** aggregates (e.g. COUNT, SUM) or when you need to pick one value per group (e.g. MAX(date)). For “unique key + one value per group,” GROUP BY with MIN/MAX is common. DISTINCT is simpler when you don’t need aggregates.

---

## Q6. (Advanced) How do you find “exact duplicate” rows (all columns identical)? What if the table has no primary key?

**Answer:**  
**SELECT col1, col2, ... COUNT(*) FROM t GROUP BY col1, col2, ... HAVING COUNT(*) > 1** (list all columns). Or use a hash: **SELECT checksum_col, COUNT(*) FROM (SELECT col1, col2, ..., MD5(col1||col2||...) AS checksum_col FROM t) x GROUP BY checksum_col HAVING COUNT(*) > 1** (concatenation and hash are DB-specific). Without a key, “keep one” delete is trickier—use a CTE with ROW_NUMBER() over all columns if the DB supports it, or copy distinct rows to a new table and replace.

---

## Q7. (Advanced) In PostgreSQL, what is DISTINCT ON? How do you get “one row per customer, the most recent order”?

**Answer:**  
**DISTINCT ON (expr)** keeps the first row per distinct value of **expr** (order determined by ORDER BY; the ORDER BY must start with the DISTINCT ON columns). **SELECT DISTINCT ON (customer_id) * FROM orders ORDER BY customer_id, created_at DESC** — one row per customer_id, the one with latest created_at. Handy for “top 1 per group” without window functions.

---

## Q8. (Advanced) Production scenario: A sync job sometimes inserts the same event twice (same event_id). You need to de-duplicate the `events` table by event_id, keeping the row with the latest `inserted_at`. Table has millions of rows. Propose a safe approach (SQL and strategy).

**Answer:**  
(1) **Identify**: **SELECT event_id, COUNT(*), MAX(inserted_at) FROM events GROUP BY event_id HAVING COUNT(*) > 1**. (2) **Delete duplicates**: In batches to avoid long locks: **WITH ranked AS (SELECT id, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY inserted_at DESC) rn FROM events) DELETE FROM events WHERE id IN (SELECT id FROM ranked WHERE rn > 1)** — run in chunks (e.g. WHERE id IN (SELECT id FROM ranked WHERE rn > 1 LIMIT 10000)). (3) Add **UNIQUE (event_id)** to prevent future duplicates. (4) Run during low traffic; use a transaction and measure. Backend: run as a batch job; consider a “dedupe” table keyed by event_id and merge instead of deleting if table is append-only.

---

## Q9. (Advanced) What is the cost of DISTINCT? When might it be expensive?

**Answer:**  
DISTINCT usually requires a **sort** or **hash** to detect duplicates, so it can be expensive on large result sets. If the query already has an ORDER BY or GROUP BY, the planner may combine. For “unique on one column” with many columns in SELECT, consider GROUP BY that column and MAX/MIN of others, or DISTINCT ON in PostgreSQL, and ensure indexes support the query.

---

## Q10. (Advanced) How do MySQL, PostgreSQL, and Oracle handle “keep one row per group” when deleting duplicates? Compare ROW_NUMBER-based delete and native options.

**Answer:**  
**PostgreSQL**: **DELETE USING** with self-join or CTE with **ROW_NUMBER() OVER (PARTITION BY key ORDER BY id)** then delete where rn > 1. **MySQL**: No CTE in DELETE in older versions; use a temp table or delete join. **Oracle**: **DELETE FROM t WHERE rowid NOT IN (SELECT MIN(rowid) FROM t GROUP BY key_col)** or ROW_NUMBER in subquery. All can use a “copy distinct to new table, swap” strategy for very large tables to minimize locking.
