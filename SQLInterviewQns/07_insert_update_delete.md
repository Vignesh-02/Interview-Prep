# 7. INSERT, UPDATE, DELETE Basics

## Q1. (Beginner) What is the syntax for inserting a single row? How do you insert only into specific columns?

**Answer:**  
**INSERT INTO t (a, b) VALUES (1, 'x');** — specify columns and values. Omit columns that have defaults or accept NULL. **INSERT INTO t VALUES (1, 'x', 2);** — all columns in table order (fragile if schema changes). Prefer listing columns explicitly.

---

## Q2. (Beginner) How do you insert multiple rows in one statement?

**Answer:**  
**INSERT INTO t (a, b) VALUES (1, 'x'), (2, 'y'), (3, 'z');** — comma-separated value lists. Standard and supported in PostgreSQL, MySQL, etc. Oracle: **INSERT ALL INTO t VALUES (1,'x') INTO t VALUES (2,'y') SELECT 1 FROM DUAL;** or use a single INSERT with a SELECT union.

---

## Q3. (Intermediate) What is INSERT ... SELECT? When would you use it?

**Answer:**  
**INSERT INTO t (a, b) SELECT x, y FROM other_table WHERE ...;** — insert rows from a query result. Use for copying data between tables, archiving (INSERT into archive_table SELECT ... FROM live_table WHERE ...), or populating from another source. Column count and types must match.

---

## Q4. (Intermediate) What does UPDATE ... WHERE do? What happens if you omit WHERE?

**Answer:**  
**UPDATE t SET col = value WHERE condition;** — updates rows that match the condition. If you **omit WHERE**, **all rows** in the table are updated (often a mistake). Always double-check WHERE in production; use a transaction and SELECT first to verify row count.

---

## Q5. (Intermediate) What is the difference between DELETE and TRUNCATE (conceptually)? Which can be rolled back?

**Answer:**  
**DELETE** removes rows one by one (or in batches), can have WHERE, fires triggers, and can be rolled back (within a transaction). **TRUNCATE** removes all rows by deallocating data pages (fast), no WHERE, typically doesn’t fire row-level triggers, and in many DBs commits implicitly or cannot be rolled back. So: DELETE is row-by-row and transactional; TRUNCATE is bulk and often non-rollback (DB-dependent).

---

## Q6. (Advanced) How do you do an “upsert” (INSERT or UPDATE if exists)? Give PostgreSQL and MySQL syntax.

**Answer:**  
**PostgreSQL**: **INSERT INTO t (id, name) VALUES (1, 'a') ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;** (requires unique constraint on id). **MySQL**: **INSERT INTO t (id, name) VALUES (1, 'a') ON DUPLICATE KEY UPDATE name = VALUES(name);** (or **name = 'a'** in newer MySQL). **Oracle**: MERGE statement. Backend: use parameterized queries; one round-trip for upsert reduces race conditions.

---

## Q7. (Advanced) Write an UPDATE that sets a column based on another table (e.g. update orders with the customer’s current email from customers table).

**Answer:**  
**PostgreSQL/MySQL**: **UPDATE orders o SET o.email = c.email FROM customers c WHERE o.customer_id = c.id;** (MySQL: **UPDATE orders o JOIN customers c ON o.customer_id = c.id SET o.email = c.email;**). **Oracle**: **UPDATE orders o SET email = (SELECT email FROM customers c WHERE c.id = o.customer_id) WHERE EXISTS (SELECT 1 FROM customers c WHERE c.id = o.customer_id);** Subquery form works everywhere; JOIN form is clearer where supported.

---

## Q8. (Advanced) Production scenario: You need to soft-delete users (set `deleted_at = NOW()`) when they request account deletion. The backend receives a list of user IDs. How do you write the UPDATE safely? How would you call it from the backend (e.g. parameterized query, batch size)?

**Answer:**  
**UPDATE users SET deleted_at = NOW(), updated_at = NOW() WHERE id = ANY($1::bigint[]) AND deleted_at IS NULL;** (PostgreSQL; $1 is array of IDs). Or **WHERE id IN (?) ** with parameterized list. Backend: use a single parameterized statement with an array or a batch of IDs (e.g. 100 at a time) to avoid huge IN lists and SQL injection. Never concatenate IDs into the query string. Use a transaction if you also need to invalidate sessions or update related tables.

---

## Q9. (Advanced) What is RETURNING (PostgreSQL) or OUTPUT (SQL Server)? How is it useful with INSERT/UPDATE/DELETE?

**Answer:**  
**RETURNING** (PostgreSQL) / **OUTPUT** (SQL Server) returns the rows affected (inserted, updated, or deleted) in the same statement. Example: **INSERT INTO t (name) VALUES ('x') RETURNING id;** — get the generated id without a second query. Useful for getting defaults, generated keys, or updated values in one round-trip from the backend.

---

## Q10. (Advanced) How do you delete duplicate rows from a table (keeping one row per key)? Assume columns (id, key_col, data); duplicates on key_col.

**Answer:**  
**PostgreSQL**: **DELETE FROM t t1 USING t t2 WHERE t1.key_col = t2.key_col AND t1.id > t2.id;** (keeps row with smallest id). Or with CTE: **WITH dupes AS (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY key_col ORDER BY id) rn FROM t) x WHERE rn > 1) DELETE FROM t WHERE id IN (SELECT id FROM dupes);**. **MySQL**: use a temporary table or same idea with a delete join (syntax varies). Backend: run in a transaction; consider doing in batches for very large tables.
