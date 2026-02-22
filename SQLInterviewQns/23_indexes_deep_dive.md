# 23. Indexes Deep Dive (clustered, non-clustered, composite) — Senior

## Q1. (Beginner) What is a B-tree index? Why is it common for primary keys and range queries?

**Answer:**  
A **B-tree** (or B+ tree) index is a balanced tree: keys are sorted, so equality and **range** (e.g. col > 5, BETWEEN) can be resolved efficiently. Lookup is O(log n). It’s the default index type in most RDBMSs. Good for **ORDER BY** and **range** predicates. Primary keys are usually stored in a B-tree (or as the clustering key).

---

## Q2. (Beginner) What is a composite index? What is the “leftmost prefix” rule?

**Answer:**  
A **composite** index is on multiple columns, e.g. **(a, b, c)**. The **leftmost prefix** rule: the index can be used for queries that filter on **a**, **(a, b)**, or **(a, b, c)** in that order. It generally **cannot** be used for **b** alone or **c** alone (unless the engine does index skip-scan). Column order matters: put equality and high-selectivity columns first, range column last when possible.

---

## Q3. (Intermediate) What is a clustered index? How does it affect INSERT and range scan performance?

**Answer:**  
A **clustered** index stores the table rows in the **order** of the index key. There is one clustered index per table (e.g. primary key in MySQL InnoDB). **INSERT**: rows are inserted in key order, which can cause **page splits** if the insert is in the middle. **Range scan**: very efficient because rows are contiguous on disk. **Non-clustered** indexes point to the row (or clustering key); they don’t dictate table order.

---

## Q4. (Intermediate) What is an index “covering” a query? What is an index-only scan?

**Answer:**  
An index **covers** a query when all columns needed (SELECT, WHERE, JOIN, ORDER BY) are in the index. The engine can then do an **index-only scan** (or “covering index scan”) without visiting the table. Add **INCLUDE** columns (PostgreSQL, SQL Server) or put columns in the key to cover more queries. Reduces I/O.

---

## Q5. (Intermediate) How do indexes impact INSERT and UPDATE? Why might bulk insert be faster with indexes dropped and recreated?

**Answer:**  
Each index must be updated on INSERT/UPDATE/DELETE. So more indexes → more write cost. For **bulk insert**, dropping non-critical indexes, loading data, then recreating indexes can be faster than updating many indexes row-by-row. Do this in maintenance windows; ensure the table is not live or use a staging table and swap.

---

## Q6. (Advanced) What is a partial (filtered) index? When is it useful? Which DBs support it?

**Answer:**  
A **partial** index only includes rows that satisfy a **WHERE** predicate (e.g. **CREATE INDEX ... ON t (col) WHERE status = 'active'**). Smaller index, faster for queries that use the same predicate. **PostgreSQL** supports it; **SQL Server** has “filtered index”; **Oracle** has function-based and similar; **MySQL** does not have true partial indexes. Use for “hot” subset of rows (e.g. active orders, recent logs).

---

## Q7. (Advanced) What is a hash index? When would you choose it over B-tree?

**Answer:**  
A **hash** index hashes the key to a bucket; lookup is **equality-only** (no range, no ORDER BY). **PostgreSQL**: hash index exists but B-tree is usually preferred. **MySQL**: MEMORY engine supports hash. Use hash for **exact match** only, high cardinality; use B-tree for range, sort, or prefix. In practice B-tree is the default; hash is niche.

---

## Q8. (Advanced) Production scenario: A table has (tenant_id, user_id, created_at). Queries are: “users for tenant X” (tenant_id = ?), “recent events for user” (tenant_id = ? AND user_id = ? AND created_at > ?). Propose index(es) and order of columns. Justify.

**Answer:**  
**Composite index (tenant_id, user_id, created_at)**. Equality on tenant_id and user_id, then range on created_at — matches the “recent events for user” query. The “users for tenant X” query can use the same index (leftmost prefix: tenant_id). Alternative: **(tenant_id, user_id, created_at DESC)** if you always want “latest first.” One composite index serves both patterns. Add tenant_id first for multi-tenant isolation and to support tenant-level scans.

---

## Q9. (Advanced) What is index bloat (e.g. in PostgreSQL)? How do you detect and fix it?

**Answer:**  
**Bloat** is when an index (or table) has many dead tuples (from updates/deletes) that haven’t been reclaimed. Detected by **pgstattuple** or **pg_stat_user_indexes** (e.g. index size vs expected). **Fix**: **REINDEX** (rebuild the index) or **VACUUM FULL** (rebuild table and indexes). **VACUUM** (without FULL) reclaims space but doesn’t compact; regular VACUUM reduces bloat over time. Schedule REINDEX during low traffic.

---

## Q10. (Advanced) Compare clustered vs non-clustered index in SQL Server and MySQL InnoDB. How does Oracle differ?

**Answer:**  
**SQL Server**: One **clustered** index (data order); **non-clustered** indexes reference the clustered key (or row id). **MySQL InnoDB**: Primary key is the clustered index; secondary indexes store the primary key for row lookup. **Oracle**: Heap table by default; “index-organized table” (IOT) is like clustered. So: in MySQL, secondary index → PK → row; in SQL Server, secondary → clustering key → row. Affects choice of PK (e.g. narrow, stable key for clustering).
