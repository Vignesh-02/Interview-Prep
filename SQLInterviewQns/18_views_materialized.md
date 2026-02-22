# 18. Views and Materialized Views

## Q1. (Beginner) What is a view? Does it store data?

**Answer:**  
A **view** is a named **query** (virtual table). It does **not** store data; each time you query the view, the underlying query runs. So **SELECT * FROM my_view** executes the view’s definition. Use for simplifying queries, hiding columns, or centralizing logic. Updates (INSERT/UPDATE/DELETE) on views are possible only when the view is “updatable” (rules vary by DB).

---

## Q2. (Beginner) What is a materialized view? How does it differ from a regular view?

**Answer:**  
A **materialized view** stores the **result** of the query (like a table). Reads are fast (no recomputation); data can be **stale** until refreshed. **REFRESH MATERIALIZED VIEW name** (or equivalent) recomputes it. Use for expensive aggregations or joins that don’t need real-time data. PostgreSQL, Oracle, SQL Server support them; MySQL does not (use a regular table + job to refresh).

---

## Q3. (Intermediate) When would you use a view instead of writing the same query in the application?

**Answer:**  
Use a view when: (1) The same complex query is used in many places (DRY). (2) You want to restrict columns/rows (security). (3) You want a stable “table” name while the underlying query evolves. (4) The DB can optimize or cache. Use the application when: logic is dynamic, or you want to keep all SQL in one place (e.g. ORM, query builder). Views are good for shared, static definitions.

---

## Q4. (Intermediate) Can you insert into a view? What makes a view “updatable”?

**Answer:**  
Only if the view is **updatable**: typically single table, no DISTINCT/aggregation/GROUP BY, no JOINs (or simple join that maps to one base table), and the columns map to base table columns. Rules differ by DB. **PostgreSQL**: INSTEAD OF triggers can implement custom INSERT/UPDATE/DELETE on any view. In practice, many views are read-only; write to base tables or use triggers.

---

## Q5. (Intermediate) How do you refresh a materialized view in PostgreSQL? What is CONCURRENTLY?

**Answer:**  
**REFRESH MATERIALIZED VIEW mv_name;** — locks the MV for the refresh (reads can block). **REFRESH MATERIALIZED VIEW CONCURRENTLY mv_name;** — builds a new version and then swaps, so reads don’t block; requires a **UNIQUE** index on the MV. Use CONCURRENTLY for large MVs in production so queries aren’t blocked. Schedule REFRESH via cron or a job.

---

## Q6. (Advanced) What are the pros and cons of a materialized view vs a summary table updated by triggers or a job?

**Answer:**  
**Materialized view**: Declarative; DB handles definition; REFRESH recomputes from scratch (or incremental where supported). **Summary table + job**: You control when and how (incremental, partial); can be more efficient for “append-only + delta.” **Summary table + triggers**: Real-time but triggers add cost and complexity. Choose MV for simplicity and full refresh; choose summary table + job for incremental or custom logic.

---

## Q7. (Advanced) In Oracle, what is the difference between a view and a materialized view? Does Oracle support incremental refresh?

**Answer:**  
**View**: Virtual; no storage. **Materialized view**: Persisted; can be refreshed. **Oracle** supports **FAST** (incremental) refresh for MVs that meet certain conditions (e.g. materialized view log on base tables). **COMPLETE** refresh recomputes all. **ON COMMIT** refresh updates the MV when the base tables are committed. Use FAST refresh for large, incrementally changing data.

---

## Q8. (Advanced) Production scenario: A dashboard shows “daily revenue by product.” The base query joins orders, order_items, and products and aggregates. The table is huge. Would you use a view, a materialized view, or a nightly summary table? Justify and outline refresh strategy.

**Answer:**  
Use a **materialized view** or a **nightly summary table** (e.g. **dashboard_daily_revenue**). A **view** would run the heavy aggregation on every dashboard load — not acceptable. **Materialized view**: **REFRESH MATERIALIZED VIEW CONCURRENTLY** once per night (or every hour if needed). **Summary table**: **TRUNCATE** + **INSERT INTO ... SELECT ...** from the same query, or incremental if you have a “last_updated” and only aggregate new/changed data. Backend: query only the MV or summary table; never hit the raw tables for this report. Cache the API response (e.g. 5–15 min) if needed.

---

## Q9. (Advanced) Can a view depend on another view? What are the risks?

**Answer:**  
Yes. A view’s definition can reference other views. Risks: (1) **Chain of dependencies** — changing a base view can break dependent views. (2) **Performance** — the optimizer may or may not flatten the nesting; nested views can lead to complex plans. (3) **Debugging** — harder to trace. Document dependencies; consider avoiding deep nesting or replacing with a single view or CTE for critical paths.

---

## Q10. (Advanced) How would the backend (e.g. Node.js with pg, or Python with SQLAlchemy) read from a materialized view? Does the application need to trigger REFRESH?

**Answer:**  
Read from the MV like a table: **SELECT * FROM mv_daily_sales**. No special API. **Refresh** is usually triggered by a **scheduled job** (cron, Celery, pg_cron, etc.), not by the app on each request. The app only reads. Optionally, an admin endpoint or internal tool can call a “refresh MV” action that runs **REFRESH MATERIALIZED VIEW** (with appropriate permissions and rate limiting).
