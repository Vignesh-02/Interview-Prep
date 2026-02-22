# 29. N+1, Sargability, Backend Integration — Senior

## Q1. (Beginner) What is the N+1 query problem? Give an example.

**Answer:**  
**N+1** is when you run **1** query to get a list (e.g. orders), then **N** queries (one per order) to get a related entity (e.g. customer for each order). So 1 + N queries instead of 1 or 2. Example: **SELECT * FROM orders**; then for each order **SELECT * FROM customers WHERE id = ?**. Fix: one query for orders and one for all needed customers (e.g. **WHERE id IN (...)**), or use a JOIN and group in app.

---

## Q2. (Beginner) How does an ORM (e.g. Sequelize, TypeORM, SQLAlchemy) cause N+1 and how do you fix it?

**Answer:**  
ORM loads a relation **lazily** when you access it (e.g. **order.customer** triggers a query per order). **Fix**: **eager load** (e.g. **include: [Customer]** or **joinedload**). That does a JOIN or a second query with IN so all related rows are loaded at once. Always specify eager loading for relations you know you’ll use in the response.

---

## Q3. (Intermediate) What does “sargable” mean? Give two examples of non-sargable predicates and how to make them sargable.

**Answer:**  
**Sargable** = the predicate can use an **index** (search argument). **Non-sargable**: (1) **LOWER(col) = 'x'** — index on col can’t help. Make sargable: **expression index** on LOWER(col), or store lowercased column. (2) **col LIKE '%x'** — leading wildcard prevents index use. Make sargable: full-text search or reverse index for suffix search. **col LIKE 'x%'** is sargable (prefix).

---

## Q4. (Intermediate) How should the backend pass date/time filters to the DB to ensure indexes are used?

**Answer:**  
Pass **same type** as the column (e.g. timestamp with time zone). Use **parameterized** queries: **WHERE created_at >= $1 AND created_at < $2**. Avoid **functions on the column** (e.g. **DATE(created_at) = ?**); use **created_at >= ? AND created_at < ?** (range). Store in UTC; convert in app or in DB with proper time zone. So the column appears “as-is” in the predicate and the index can be used.

---

## Q5. (Intermediate) What is connection pooling? Why is it important for backend-to-DB?

**Answer:**  
**Connection pooling** keeps a set of open DB connections and hands them to the application when needed; when the app is done, the connection returns to the pool. Opening a connection is expensive; pooling avoids creating/destroying per request. Set pool size based on DB **max_connections** and app concurrency (e.g. pool size 10–20 per app instance). Don’t hold connections long (no long transactions in the pool).

---

## Q6. (Advanced) How do you solve N+1 when the relationship is “one-to-many” and you need a list of parents with their children? Write the two-query approach (parents, then children by parent_ids).

**Answer:**  
(1) **SELECT * FROM parents WHERE ...** (get list of parents). (2) **SELECT * FROM children WHERE parent_id IN (?, ?, ...)** with the list of parent IDs from step 1. In app: build a map **parent_id → [children]** and attach to each parent. So 2 queries total. Alternative: one query with JOIN; then in app, group rows by parent (parent columns duplicate for each child). Both avoid N+1.

---

## Q7. (Advanced) What is “prepared statement” or “parameterized query”? Why must the backend use it?

**Answer:**  
A **parameterized** (prepared) query sends SQL with **placeholders** and binds values separately (e.g. **SELECT * FROM t WHERE id = $1**; bind **$1 = 5**). **Benefits**: (1) **No SQL injection** — user input is never parsed as SQL. (2) **Reuse of plan** — DB can cache the plan. Always use parameters for user input; never concatenate into the SQL string.

---

## Q8. (Advanced) Production scenario: An API returns a paginated list of “posts” with “author” (name, avatar). The current implementation does: 1 query for posts (LIMIT/OFFSET), then 1 query per post for author (N+1). Describe the fix and give the SQL pattern the backend should use.

**Answer:**  
**Fix**: (1) Query posts (with LIMIT/OFFSET). (2) Collect distinct **author_id** from those posts. (3) One query: **SELECT * FROM authors WHERE id IN (...)**. (4) In app: map author_id → author; attach to each post. So **2 queries** regardless of page size. SQL: **SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 0**; then **SELECT * FROM authors WHERE id IN (1,2,3,...)**. Backend: use ORM eager load (e.g. **include: ['author']**) or raw SQL with the two-query pattern. Ensure authors are loaded in bulk by ID list.

---

## Q9. (Advanced) How does the backend handle “too many IDs” in an IN clause (e.g. 50,000 IDs)? What are the options?

**Answer:**  
(1) **Batch IN**: split into chunks (e.g. 500 or 1000 per query) and run multiple queries; merge results in app. (2) **Temporary table**: insert IDs into a temp table, then **JOIN** or **WHERE id IN (SELECT id FROM temp)**. (3) **Limit the use case**: if the user can select 50k rows, consider streaming or cursor-based export instead of loading all into memory. (4) **Application filter**: if data is already in app memory, filter in app instead of sending 50k IDs. Avoid single IN with 50k literals (long SQL, plan issues).

---

## Q10. (Advanced) Compare how Node (e.g. pg), Python (e.g. psycopg2, SQLAlchemy), and Java (e.g. JDBC, Hibernate) typically interact with the DB: connection handling, parameterization, and N+1 prevention.

**Answer:**  
**Node (pg)**: Connection pool (pg.Pool); parameterized with **$1, $2**; N+1 avoided by batching queries or using an ORM (e.g. Sequelize) with **include**. **Python (psycopg2)**: **%s** placeholders; connection pool (e.g. SQLAlchemy pool); SQLAlchemy **joinedload**/ **selectinload** to avoid N+1. **Java (JDBC/Hibernate)**: DataSource for pooling; **PreparedStatement** for parameters; Hibernate **JOIN FETCH** or **@EntityGraph** to eager load and avoid N+1. All: use pool, parameterize, and eager-load or batch when loading relations.
