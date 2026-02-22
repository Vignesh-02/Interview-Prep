# 27. Concurrency, Locking, and Deadlocks — Senior

## Q1. (Beginner) What is a deadlock? How does the DB detect and resolve it?

**Answer:**  
A **deadlock** is when two (or more) transactions each wait for a resource held by the other, so neither can proceed. The DB **detects** deadlocks (e.g. wait-for graph) and **resolves** by **aborting** one transaction (victim), which releases its locks and allows the other(s) to continue. The aborted transaction gets a deadlock error; the application should retry.

---

## Q2. (Beginner) What is a lock? What is the difference between shared (read) and exclusive (write) lock?

**Answer:**  
A **lock** protects a resource (row, page, table) so that concurrent transactions don’t conflict. **Shared lock**: multiple transactions can hold it for reading; blocks writers. **Exclusive lock**: one transaction holds it for write; blocks other writers and readers (depending on isolation). Writers acquire exclusive locks; readers may hold shared locks (or no lock under MVCC).

---

## Q3. (Intermediate) How can you reduce the chance of deadlocks in application code?

**Answer:**  
(1) **Lock order**: always acquire locks in the same order (e.g. always lock account A before B by sorting IDs). (2) **Short transactions** — do work quickly and commit. (3) **Avoid holding locks across user input or external calls**. (4) **Use consistent access order** (e.g. same ORDER BY when updating multiple rows). (5) **Retry** on deadlock (with backoff). Design so all code paths lock in the same order.

---

## Q4. (Intermediate) What is SELECT ... FOR UPDATE? When would you use it?

**Answer:**  
**SELECT ... FOR UPDATE** locks the selected rows (exclusive lock) until the transaction ends. Use when you need to **read and then update** without another transaction changing the row (e.g. “read balance, then update”). It prevents lost updates and avoids non-repeatable reads for those rows. Use with a short transaction; avoid holding across many rows or long work.

---

## Q5. (Intermediate) What is a lock timeout? How do you set it (e.g. in PostgreSQL)?

**Answer:**  
**Lock timeout** is the maximum time a statement will wait to acquire a lock before failing. **PostgreSQL**: **SET lock_timeout = '2s'** (per session or in config). Prevents a transaction from waiting forever and helps detect blocking. Use in application or session for long-running or interactive operations. **MySQL**: **innodb_lock_wait_timeout**. **Oracle**: different parameters. Set appropriately so slow queries fail fast and can be retried.

---

## Q6. (Advanced) What is “lock escalation”? When does it happen and what is the downside?

**Answer:**  
**Lock escalation** is when the DB converts many fine-grained locks (e.g. row locks) into fewer coarse-grained locks (e.g. table lock) to reduce lock memory. Downside: concurrency drops (more of the table is locked). It happens when the number of locks held by a transaction exceeds a threshold. Mitigate: keep transactions short, touch fewer rows, or use hints to avoid escalation (DB-specific). SQL Server has lock escalation; PostgreSQL doesn’t escalate row to table in the same way.

---

## Q7. (Advanced) How do you debug a deadlock? What does the DB log or return?

**Answer:**  
On deadlock, the DB returns an error (e.g. **deadlock_detected**, **1213** in MySQL). **Logs**: enable deadlock logging (e.g. **log_lock_waits** and **deadlock_timeout** in PostgreSQL; **innodb_print_all_deadlocks** in MySQL). The log shows which transactions and statements were involved and which was chosen as victim. Use that to see lock order and conflicting statements; fix by making lock order consistent or reducing contention.

---

## Q8. (Advanced) Production scenario: Two backend workers both run “deduct inventory for order A, then for order B” but in different order (worker 1: A then B; worker 2: B then A). Deadlocks occur. How do you fix it in the DB and in the backend?

**Answer:**  
**Fix**: **Always lock in the same order**. For example, sort resource IDs: both workers lock the **smaller** ID first (e.g. lock order A, then B if A < B). So **UPDATE inventory SET qty = qty - 1 WHERE product_id IN (...) ORDER BY product_id** and acquire row locks in that order (or in app: sort (A, B), then SELECT FOR UPDATE in that order). Backend: in code, sort the list of product_ids (or order_ids) and perform updates in that order so every transaction takes locks in the same sequence. Retry on deadlock with exponential backoff as a safety net.

---

## Q9. (Advanced) What is optimistic vs pessimistic locking? When would you use each?

**Answer:**  
**Pessimistic**: lock rows (e.g. SELECT FOR UPDATE) so others can’t change them until you commit. Use when contention is high or you must guarantee no conflict. **Optimistic**: don’t lock; read, then update with a condition (e.g. **UPDATE t SET ... WHERE id = ? AND version = ?**); if no row updated, someone else changed it — retry. Use when contention is low and you want to avoid blocking. Choose based on conflict rate and retry cost.

---

## Q10. (Advanced) How do PostgreSQL, MySQL, and Oracle handle row-level vs table-level locking? What about advisory locks?

**Answer:**  
**PostgreSQL**: Row-level locks (FOR UPDATE, FOR SHARE); table-level (LOCK TABLE); **advisory locks** (pg_advisory_lock) for application-defined locking. **MySQL InnoDB**: Row locks (and gap locks in RR); table locks (explicit or implicit). **Oracle**: Row-level (TX locks); table-level (TM locks); **DBMS_LOCK** for application locks. All support row-level for DML; table-level for DDL or bulk operations. Advisory locks are useful for “lock a logical resource” (e.g. job name) without a row.
