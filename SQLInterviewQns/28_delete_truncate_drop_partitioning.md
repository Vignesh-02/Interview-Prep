# 28. DELETE vs TRUNCATE vs DROP; Partitioning — Senior

## Q1. (Beginner) What is the difference between DELETE, TRUNCATE, and DROP in terms of what they remove and whether they can be rolled back?

**Answer:**  
**DELETE** — removes **rows** (can have WHERE); row-by-row or in batches; fires triggers; can be rolled back in a transaction. **TRUNCATE** — removes **all rows** (no WHERE); deallocates data pages (fast); typically no row triggers; in many DBs **cannot** be rolled back (implicit commit or no undo). **DROP** — removes the **table** (structure and data); cannot be rolled back (DDL). So: DELETE = rows, transactional; TRUNCATE = all rows, fast, often not rollback; DROP = table gone.

---

## Q2. (Beginner) Why is TRUNCATE faster than DELETE for removing all rows?

**Answer:**  
**TRUNCATE** doesn’t scan rows one-by-one; it **deallocates** the data pages (and resets identity/sequence in many DBs). So it’s O(1) in terms of rows. **DELETE** logs each row (or batch) for rollback and fires triggers, so it’s O(n). TRUNCATE also doesn’t usually fire row-level triggers. Use TRUNCATE when you want to empty the table quickly and don’t need row-level control or rollback.

---

## Q3. (Intermediate) What does TRUNCATE do to identity/sequence columns? What about foreign keys?

**Answer:**  
**Identity/sequence**: TRUNCATE typically **resets** the counter (e.g. next value back to 1). **Foreign keys**: in many DBs you cannot TRUNCATE a table that is **referenced** by another table’s FK (or you must truncate in order: referenced tables first, or use CASCADE where supported). **PostgreSQL**: **TRUNCATE ... CASCADE** truncates dependent tables. **MySQL**: TRUNCATE fails if there are FKs from other tables (disable FK checks or delete in order). Check DB docs.

---

## Q4. (Intermediate) What is table partitioning? What problem does it solve?

**Answer:**  
**Partitioning** splits one logical table into multiple **partitions** (separate physical segments) by a **partition key** (e.g. range of dates, list of regions, hash of id). It helps: (1) **Query performance** — partition pruning (skip irrelevant partitions). (2) **Maintenance** — drop/archive old partitions instead of DELETE. (3) **Parallelism** — scans across partitions. Use for large, time-series or range-based data.

---

## Q5. (Intermediate) What are range, list, and hash partitioning? When would you use each?

**Answer:**  
**Range**: Partition by range of a column (e.g. date: Jan, Feb, …). Good for time-series; easy to add/drop “latest” or “old” partitions. **List**: Partition by discrete values (e.g. region IN ('US','EU')). Good for categorical keys. **Hash**: Partition by hash of key (e.g. user_id % 4). Good for even distribution. **Composite**: e.g. range by month, then hash by id within month.

---

## Q6. (Advanced) How do you “remove” old data in a partitioned table (e.g. drop data older than 1 year)?

**Answer:**  
**Drop the partition** (DDL): **ALTER TABLE t DROP PARTITION p_2020** (syntax is DB-specific). That’s instant (no row-by-row delete). Or **detach** the partition and archive it. Don’t DELETE row-by-row from a partition if you can drop/detach instead. Schedule a job that drops partitions older than 1 year (or N months).

---

## Q7. (Advanced) In PostgreSQL, how do you create a range-partitioned table and add a new partition?

**Answer:**  
**CREATE TABLE t (id int, dt date, ...) PARTITION BY RANGE (dt);** then **CREATE TABLE t_2024_01 PARTITION OF t FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');**. Add a new partition: **CREATE TABLE t_2024_02 PARTITION OF t FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');**. Default partition (optional): **FOR VALUES FROM (MINVALUE) TO (MAXVALUE)**. Use **pg_partition_tree** or system catalogs to list partitions.

---

## Q8. (Advanced) Production scenario: A high-volume events table is growing 10GB/month. Queries are always filtered by (tenant_id, created_at). Propose partitioning and retention. How would the backend or DBA add new partitions and drop old ones?

**Answer:**  
**Partition by range on created_at** (e.g. monthly). **Partition pruning** for queries with **created_at** range; optionally **tenant_id** in the key or as secondary. **Retention**: drop partitions older than 12 months (or per policy) with **ALTER TABLE ... DROP PARTITION ...**. **Add new partition**: monthly job (cron/scheduler) runs **CREATE PARTITION FOR next month** before the month starts. **Backend**: no change to queries (same table name); ensure queries include **created_at** filter so pruning works. DBA or automation: script that adds next month’s partition and drops partitions older than N months.

---

## Q9. (Advanced) What is “partition pruning”? How does the optimizer use the partition key?

**Answer:**  
**Partition pruning** is when the optimizer **excludes** partitions that cannot contain matching rows (based on WHERE and the partition key). Example: **WHERE created_at >= '2024-01-01' AND created_at < '2024-02-01'** on a date-range partitioned table → only the January partition is scanned. The partition key should appear in the query filter for pruning to work. Use EXPLAIN to confirm “Partition Prune” or similar in the plan.

---

## Q10. (Advanced) Compare partitioning support in PostgreSQL, MySQL, and Oracle. Any limitations or syntax differences?

**Answer:**  
**PostgreSQL** (10+): Range, list, hash; composite; default partition; **PARTITION BY RANGE/LIST/HASH**. **MySQL**: Range, list, hash, key; **PARTITION BY RANGE** etc.; some limitations (e.g. unique key must include partition key in many cases). **Oracle**: Range, list, hash, composite, interval; very mature (partition exchange, etc.). **SQL Server**: Similar. All support basic range/list; check for default partition, subpartitioning, and maintenance (exchange, split, merge) per DB. Backend: use same SQL; partitioning is transparent for SELECT/INSERT with partition key in the predicate.
