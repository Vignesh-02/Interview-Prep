# 30. OLAP vs OLTP, Denormalization, Analytics — Senior

## Q1. (Beginner) What is OLTP? What is OLAP? How do they differ in purpose and query pattern?

**Answer:**  
**OLTP** (Online Transaction Processing): operational systems; many **short** transactions (insert, update, single-row or small scope); strong consistency; normalized schema. **OLAP** (Online Analytical Processing): reporting/analytics; **read-heavy**, complex aggregations, full scans, ad-hoc queries; often denormalized or star schema; may accept eventual consistency or batch updates. OLTP = run the business; OLAP = understand the business.

---

## Q2. (Beginner) What is a “star schema”? What are fact and dimension tables?

**Answer:**  
**Star schema**: a **fact** table (measures and foreign keys) surrounded by **dimension** tables (descriptive attributes). **Fact**: e.g. sales (amount, quantity, date_id, product_id, store_id). **Dimensions**: date (date_id, year, month, …), product (product_id, name, category), store. Queries JOIN fact to dimensions and aggregate. Good for analytics and reporting; denormalized dimensions (redundant attributes) for simpler queries.

---

## Q3. (Intermediate) When would you recommend a separate “reporting” or “analytics” database (replica or warehouse)?

**Answer:**  
When: (1) **Heavy reporting** on the OLTP DB slows transactions. (2) **Different schema** (star, aggregates) is needed for analytics. (3) **Different workload** (long scans, big JOINs) doesn’t fit OLTP. Use a **replica** for read-only, same-schema reporting; use a **warehouse** (e.g. Redshift, BigQuery, Snowflake) or **analytics DB** for transformed/denormalized data and heavy aggregations. ETL or CDC keeps the analytics DB updated.

---

## Q4. (Intermediate) What is “eventual consistency” in the context of replicas and reporting?

**Answer:**  
**Eventual consistency**: replicas (or derived stores) may lag the primary; after writes stop, they will eventually match. So a report on a replica might not see the latest few seconds of data. Acceptable for dashboards and many reports; not for “just committed” transactional reads. Use the primary for real-time; use replicas or warehouse for reporting and accept a short lag.

---

## Q5. (Intermediate) Give two examples where denormalization in the same OLTP DB is justified.

**Answer:**  
(1) **Counters on parent**: e.g. **order_count** on customers — updated by trigger or application when orders change; avoids **COUNT(*)** on orders for “how many orders does this customer have?” (2) **Snapshot on child**: e.g. **product_name**, **unit_price** on order_lines — historical accuracy and avoids JOIN to products for order display. Both trade write cost for read performance and simplicity.

---

## Q6. (Advanced) What is a “materialized view” in the context of OLAP? How does it differ from a view and when would you refresh it?

**Answer:**  
A **materialized view** stores the **result** of a query (aggregation, join). Reads are fast; data is stale until **refresh**. In OLAP: use for pre-aggregated reports (e.g. daily sales by product). Refresh: **nightly** (batch), **on schedule** (e.g. every hour), or **on commit** (expensive, use sparingly). Differs from a view: view is virtual (query runs each time); MV is stored. Use MV when the query is expensive and real-time isn’t required.

---

## Q7. (Advanced) How would you design a “daily summary” table that the backend (or a job) updates? What columns and how do you avoid double-counting?

**Answer:**  
Table: e.g. **(date, product_id, total_qty, total_amount, order_count)**. **Update strategy**: (1) **Full refresh** — truncate and **INSERT ... SELECT** from raw table grouped by date and product (no double-count if source is authoritative). (2) **Incremental** — only process new/changed source rows (e.g. **WHERE created_at >= last_run**); aggregate and **INSERT ... ON CONFLICT UPDATE** (upsert) into summary. Use a **batch_id** or **last_updated** to track what’s been summarized; idempotent jobs (e.g. re-run same window) avoid double-count by design (replace or sum only new facts).

---

## Q8. (Advanced) Production scenario: The same PostgreSQL database is used for both OLTP (orders, payments) and internal dashboards (revenue by day, by product). Dashboards are slow and sometimes affect OLTP. Propose an architecture and what the backend should do.

**Answer:**  
(1) **Read replica**: point dashboards to a **replica**; OLTP stays on primary. Dashboards get slightly stale data; no load on primary. (2) **Pre-aggregate**: build **summary tables** or **materialized views** (e.g. daily_revenue_by_product); refresh by a **scheduled job** (nightly or every hour). Dashboards query only summaries. (3) **Separate analytics DB**: ETL to a warehouse or analytics DB; dashboards query that. Backend: configurable **read host** (replica) for report queries; use connection routing (e.g. read vs write) so dashboard code uses the read host and summary tables. Keep heavy ad-hoc queries off the primary.

---

## Q9. (Advanced) What is “columnar” storage (e.g. in a data warehouse)? Why is it better for analytics?

**Answer:**  
**Columnar** storage stores data **by column** (all values of column A, then column B, …) instead of by row. **Benefits for analytics**: (1) **Compression** — similar values in a column compress well. (2) **Scan only needed columns** — e.g. SUM(amount) only reads the amount column. (3) **Better for aggregation** — less I/O. OLTP is usually row-based (good for single-row access); warehouses (Redshift, BigQuery, etc.) use columnar for analytical workloads.

---

## Q10. (Advanced) How do PostgreSQL, MySQL, and Oracle position themselves for OLAP (e.g. parallel query, columnar extensions, partitioning)?

**Answer:**  
**PostgreSQL**: **Parallel query** (workers for scans/joins); **partitioning**; **BRIN** for large ordered data; extensions (e.g. **Citrus**, columnar). Good for mid-size analytics. **MySQL**: Limited parallelism; partitioning; no native columnar. **Oracle**: **Parallel execution**, **partitioning**, **Exadata** (columnar cache), **In-Memory** option. **SQL Server**: Columnstore indexes, parallel query. For heavy OLAP, organizations often use a dedicated warehouse (Snowflake, Redshift, BigQuery) and ETL from OLTP; use the RDBMS for lighter reporting and pre-aggregated tables.
