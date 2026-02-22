# 14. Indexes (Concepts and Types)

## Q1. (Beginner) What is an index? Why do we use it?

**Answer:**  
An **index** is a data structure (often B-tree) that lets the DB find rows by key(s) without scanning the whole table. It speeds up **WHERE**, **JOIN**, and **ORDER BY** on the indexed columns. Trade-off: faster reads, slower writes (indexes must be updated) and extra storage.

---

## Q2. (Beginner) What is a primary key? Is it always indexed?

**Answer:**  
A **primary key** uniquely identifies each row; it’s unique and (in practice) not NULL. In all major RDBMSs, a primary key has an index (or is the clustering key). So lookups and joins on the PK are efficient. There is only one primary key per table.

---

## Q3. (Intermediate) What is the difference between a unique index and a non-unique index?

**Answer:**  
A **unique** index enforces uniqueness (no two rows can have the same key); it can also be used for lookups. A **non-unique** index only speeds up access; it doesn’t prevent duplicates. Use a unique index for natural keys (e.g. email, (order_id, line_no)); use non-unique for filter/sort columns (e.g. status, created_at).

---

## Q4. (Intermediate) When might an index not be used by the optimizer (e.g. for a WHERE clause)?

**Answer:**  
Index might not be used when: (1) **Function on column** (e.g. **WHERE LOWER(col) = 'x'**); (2) **Leading wildcard** (e.g. **LIKE '%x'**); (3) **Type mismatch** (e.g. string vs number); (4) **Very small table** (full scan cheaper); (5) **Low selectivity** (most rows match); (6) **OR** on different columns sometimes. Fix: write sargable predicates, match types, consider expression index (e.g. LOWER(col)) where supported.

---

## Q5. (Intermediate) What is a composite (multi-column) index? What is the rule for using it in a WHERE clause?

**Answer:**  
A **composite** index is on multiple columns (e.g. **(a, b, c)**). It can be used for **a**, **(a, b)**, or **(a, b, c)** (left prefix). It generally cannot be used for **b** or **c** alone (unless the DB has skip-scan or similar). Put the most selective or equality columns first; range column last often helps (e.g. **(status, created_at)** for **WHERE status = 'x' AND created_at > ...**).

---

## Q6. (Advanced) What is a clustered index vs a non-clustered index (concept)? How does it affect table storage?

**Answer:**  
**Clustered**: The table’s rows are stored in the index order (one clustered index per table). The leaf level of the index is the data. **Non-clustered**: Separate structure; leaves point to the row (or to the clustered key). **PostgreSQL**: heap table + index (no “clustered” in MySQL sense); **CLUSTER** command can reorder. **MySQL InnoDB**: PK is clustered. **SQL Server/Oracle**: can define clustered vs non-clustered. Clustered affects physical order and thus range scans on the clustering key.

---

## Q7. (Advanced) How do indexes affect INSERT, UPDATE, and DELETE performance?

**Answer:**  
Each index must be updated when rows are inserted, updated (if indexed columns change), or deleted. So more indexes → slower writes. Balance: add indexes for important read patterns; avoid redundant indexes; drop or consolidate indexes that aren’t used (check usage stats). For bulk loads, dropping non-critical indexes, loading, then recreating can be faster.

---

## Q8. (Advanced) Production scenario: A high-traffic table has (user_id, event_type, created_at). Queries are “recent events for user X” and “count by event_type in last 24h.” Propose indexes and justify. How would the backend pass time bounds to avoid full scans?

**Answer:**  
(1) **(user_id, created_at DESC)** — for “recent events for user X” (equality on user_id, range on created_at). (2) **(event_type, created_at)** — for “count by event_type in last 24h” (equality on event_type, range on created_at). Or **(created_at, event_type)** if most queries filter by time first. Backend: always pass **created_at** (or equivalent) bounds (e.g. **created_at >= NOW() - INTERVAL '24 hours'**) so the optimizer can use the index; use parameterized queries. Monitor slow queries and index usage.

---

## Q9. (Advanced) What is a covering index? When is it beneficial?

**Answer:**  
A **covering** index includes all columns needed for a query (key + included columns), so the engine can satisfy the query from the index alone without visiting the table (“index-only scan”). Beneficial for read-heavy queries that select a small set of columns. PostgreSQL: **INCLUDE** in index; MySQL: include columns in the key or use a secondary index that covers; SQL Server: **INCLUDE**. Reduces I/O.

---

## Q10. (Advanced) Compare index types or options in PostgreSQL, MySQL, and Oracle (B-tree, hash, full-text, partial).

**Answer:**  
**B-tree**: Default in all; good for equality and range. **Hash**: PostgreSQL (equality only); MySQL (memory engine). **Full-text**: PostgreSQL (tsvector/GIN); MySQL (FULLTEXT); Oracle (Oracle Text). **Partial**: PostgreSQL supports **WHERE** in index definition (partial index); Oracle has similar (function-based, etc.). **Unique, composite, INCLUDE**: syntax varies. Choose index type and options based on access pattern and DB capabilities.
