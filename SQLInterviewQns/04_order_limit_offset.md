# 4. ORDER BY, LIMIT, OFFSET, TOP

## Q1. (Beginner) What does ORDER BY do? What is the default sort order?

**Answer:**  
**ORDER BY** sorts the result set. Default is **ASC** (ascending). Use **ORDER BY col DESC** for descending. You can order by multiple columns: **ORDER BY a ASC, b DESC**. NULLs sort first or last depending on DB (e.g. PostgreSQL: NULLS LAST by default for DESC; use **NULLS FIRST** / **NULLS LAST** to control).

---

## Q2. (Beginner) How do you get “top 10” rows in PostgreSQL, MySQL, and Oracle?

**Answer:**  
- **PostgreSQL / MySQL**: **ORDER BY col DESC LIMIT 10**.  
- **Oracle**: **SELECT * FROM (SELECT t.* FROM t ORDER BY col DESC) WHERE ROWNUM <= 10** (careful: ROWNUM is applied before ORDER BY in subquery), or **FETCH FIRST 10 ROWS ONLY** (12c+).  
- **SQL Server**: **SELECT TOP 10 * FROM t ORDER BY col DESC** or **OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY**.

---

## Q3. (Intermediate) What is OFFSET? What are the performance implications of OFFSET for large values?

**Answer:**  
**OFFSET n** skips the first **n** rows (used with LIMIT for pagination). **LIMIT 10 OFFSET 1000** still forces the DB to compute and skip 1000 rows, then return 10—so performance degrades as OFFSET grows. Prefer “keyset” or “cursor” pagination (WHERE id > last_seen_id ORDER BY id LIMIT 10) for large offsets.

---

## Q4. (Intermediate) Can you ORDER BY a column that is not in the SELECT list? Can you ORDER BY an alias from SELECT?

**Answer:**  
Yes to both in standard SQL. **SELECT name FROM users ORDER BY created_at** is valid. **SELECT name AS n FROM users ORDER BY n** is valid—ORDER BY runs after SELECT so aliases are visible. Some DBs allow ORDER BY ordinal: **ORDER BY 1** (first column in SELECT). Prefer column names or aliases for clarity.

---

## Q5. (Intermediate) How do you sort NULLs first or last explicitly in PostgreSQL and Oracle?

**Answer:**  
**PostgreSQL**: **ORDER BY col NULLS LAST** or **NULLS FIRST**. **Oracle**: **ORDER BY col NULLS FIRST** (default for ASC), **NULLS LAST** (default for DESC); override with **NULLS LAST** in ASC. **MySQL**: NULLs sort first in ASC, last in DESC; no standard NULLS FIRST/LAST (workaround: **ORDER BY col IS NULL, col**).

---

## Q6. (Advanced) Implement “page 3” of results (page size 20) in standard SQL. Then write the same using keyset pagination.

**Answer:**  
Offset-based: **ORDER BY id LIMIT 20 OFFSET 40** (page 3 = skip 40, take 20).  
Keyset: assume last id from page 2 was 100: **WHERE id > 100 ORDER BY id LIMIT 20**. Keyset is stable and fast even for deep pages; offset-based gets slower as OFFSET grows.

---

## Q7. (Advanced) What happens if you use ORDER BY with columns from different tables in a JOIN and the optimizer chooses a different join order? Is the result order guaranteed?

**Answer:**  
If ORDER BY columns uniquely determine the order, the result order is guaranteed. If there are ties (same values for all ORDER BY columns), order among tied rows is **undefined** unless you add more columns to ORDER BY. The optimizer can change join order; it must still satisfy ORDER BY. For deterministic pagination, include a unique column (e.g. id) in ORDER BY.

---

## Q8. (Advanced) Production scenario: An API returns paginated products (page size 50). Current implementation uses LIMIT 50 OFFSET (page * 50). For page 100, the query is slow. Propose a better approach and give the SQL pattern.

**Answer:**  
Use **keyset (cursor) pagination**. Return a cursor (e.g. last product_id and optionally last name for tie-breaking). Next page: **SELECT * FROM products WHERE (name, id) > ($last_name, $last_id) ORDER BY name, id LIMIT 50**. Index on (name, id). No OFFSET, so cost is stable. API returns **next_cursor** (e.g. base64 of last name+id); client sends it back for the next page. Explain to the interviewer: “We avoid OFFSET for large pages by filtering on the sort key and a unique column.”

---

## Q9. (Advanced) In MySQL, what is the difference between LIMIT in a subquery vs in the outer query? When is LIMIT in a subquery useful?

**Answer:**  
**LIMIT** in outer query limits final result. **LIMIT** in subquery limits rows fed into the outer query (e.g. “top 10 per group” by using a subquery that orders and limits per group, then outer query can use that). In MySQL, ORDER BY in subquery can be ignored without LIMIT in some versions; LIMIT can force the subquery to use a sort. Use “top N per group” patterns with window functions (ROW_NUMBER) where available for clarity.

---

## Q10. (Advanced) How do Oracle’s ROWNUM and ROW_NUMBER() differ? Why can’t you do “WHERE ROWNUM > 10” for pagination?

**Answer:**  
**ROWNUM** is a pseudo-column assigned before ORDER BY and is incremental (1, 2, 3…). Once a row gets ROWNUM 11, it is filtered out, so **ROWNUM > 10** never returns rows (ROWNUM goes 1 to N; no row gets 11). For “skip 10, take 10” in Oracle use a subquery: **SELECT * FROM (SELECT t.*, ROWNUM rn FROM (SELECT * FROM t ORDER BY col) t WHERE ROWNUM <= 20) WHERE rn > 10**, or **OFFSET ... FETCH** in 12c+.
