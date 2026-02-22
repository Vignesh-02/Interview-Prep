# 6. UNION, UNION ALL, INTERSECT, EXCEPT

## Q1. (Beginner) What is the difference between UNION and UNION ALL?

**Answer:**  
**UNION** combines two result sets and **removes duplicates** (like DISTINCT on the combined rows). **UNION ALL** keeps all rows, including duplicates. **UNION ALL** is faster when you know there are no duplicates or when duplicates are acceptable, because it skips the deduplication step.

---

## Q2. (Beginner) What must be true about the two SELECTs in a UNION? How many columns and what types?

**Answer:**  
Both SELECTs must have the **same number of columns**, and corresponding columns must have **compatible types** (same or implicitly convertible). Column names come from the first SELECT unless you use aliases. ORDER BY applies to the whole result and must reference columns by position or by the first query’s names/aliases.

---

## Q3. (Intermediate) What does INTERSECT do? Give a one-line example.

**Answer:**  
**INTERSECT** returns rows that appear in **both** result sets (set intersection). Example: **SELECT id FROM a INTERSECT SELECT id FROM b** — IDs that are in both **a** and **b**. Duplicates are removed. Not supported in MySQL (use IN + subquery or EXISTS to emulate).

---

## Q4. (Intermediate) What does EXCEPT (or MINUS) do? Which databases use which name?

**Answer:**  
**EXCEPT** (SQL standard, PostgreSQL) and **MINUS** (Oracle) return rows that are in the first set but **not** in the second. Example: **SELECT id FROM a EXCEPT SELECT id FROM b** — IDs in **a** but not in **b**. MySQL doesn’t have EXCEPT; emulate with **NOT IN** or **NOT EXISTS** (watch NULLs with NOT IN).

---

## Q5. (Intermediate) How do you order the result of a UNION? Can you ORDER BY a column name from the second query?

**Answer:**  
Put **ORDER BY** once at the end of the full UNION; it applies to the combined result. You can only reference columns by the **first** query’s names/aliases or by position (e.g. **ORDER BY 1**). So give the first SELECT clear column aliases and use those in ORDER BY.

---

## Q6. (Advanced) Emulate INTERSECT in MySQL (which has no INTERSECT). Write “ids that exist in both table_a and table_b.”

**Answer:**
```sql
SELECT DISTINCT a.id
FROM table_a a
WHERE a.id IN (SELECT id FROM table_b);
```
Or: **SELECT DISTINCT a.id FROM table_a a INNER JOIN table_b b ON a.id = b.id**. Both return the intersection. JOIN can be faster with an index on **id** in both tables.

---

## Q7. (Advanced) Emulate EXCEPT in MySQL: “rows in table_a that are not in table_b.” Handle NULLs safely.

**Answer:**  
**SELECT a.* FROM table_a a WHERE NOT EXISTS (SELECT 1 FROM table_b b WHERE b.id = a.id)**. Prefer NOT EXISTS over **NOT IN (SELECT id FROM table_b)** because if **b.id** has any NULL, NOT IN can return no rows. For “all columns of a”: **SELECT a.***; for “matching key only”: **SELECT a.id**.

---

## Q8. (Advanced) Production scenario: You have two tables of “feature flags” per user (from different sources). You need a single list of all unique user_ids that have at least one flag, and a column indicating source: ‘A’, ‘B’, or ‘BOTH’. Write the SQL.

**Answer:**
```sql
SELECT user_id, 
       CASE WHEN a.user_id IS NOT NULL AND b.user_id IS NOT NULL THEN 'BOTH'
            WHEN a.user_id IS NOT NULL THEN 'A'
            ELSE 'B' END AS source
FROM (SELECT DISTINCT user_id FROM flags_a) a
FULL OUTER JOIN (SELECT DISTINCT user_id FROM flags_b) b USING (user_id);
```
MySQL (no FULL OUTER): **SELECT user_id, 'A' AS source FROM (SELECT DISTINCT user_id FROM flags_a) a WHERE user_id NOT IN (SELECT user_id FROM flags_b) UNION ALL SELECT user_id, 'B' FROM flags_b WHERE user_id NOT IN (SELECT user_id FROM flags_a) UNION ALL SELECT a.user_id, 'BOTH' FROM flags_a a INNER JOIN flags_b b ON a.user_id = b.user_id**. Or use UNION of distinct user_ids and then LEFT JOIN both tables and use CASE for source.

---

## Q9. (Advanced) When would you prefer UNION ALL over UNION for performance? When is the extra sort/dedup of UNION justified?

**Answer:**  
Prefer **UNION ALL** when: (1) the two queries are known to be disjoint (e.g. by type or date range); (2) duplicates are acceptable for the use case; (3) you want to avoid the cost of deduplication. Use **UNION** when you need a distinct set and the application doesn’t want to deduplicate in code. The sort/dedup of UNION can be expensive on large result sets; measure and consider filtering duplicates in the application if you already have a unique key.

---

## Q10. (Advanced) Compare how PostgreSQL, MySQL, and Oracle handle INTERSECT and EXCEPT (or MINUS). What are the main syntax or feature differences?

**Answer:**  
- **PostgreSQL**: **INTERSECT**, **EXCEPT** (standard names). All set ops remove duplicates by default; **INTERSECT ALL** / **EXCEPT ALL** available.  
- **Oracle**: **INTERSECT**, **MINUS** (not EXCEPT). No *ALL* variants.  
- **MySQL**: No INTERSECT or EXCEPT/MINUS. Emulate with IN + subquery, NOT EXISTS, or JOINs.  
Backend: for portability, avoid INTERSECT/EXCEPT in shared code if you must support MySQL; use IN/EXISTS/JOIN patterns instead.
