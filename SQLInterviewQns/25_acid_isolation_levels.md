# 25. ACID and Transaction Isolation Levels — Senior

## Q1. (Beginner) What do the ACID properties stand for? Briefly define each.

**Answer:**  
**A**tomicity — transaction is all-or-nothing (commit or rollback). **C**onsistency — transaction leaves the DB in a valid state (constraints hold). **I**solation — concurrent transactions don’t see each other’s uncommitted work in a way that breaks guarantees. **D**urability — committed data survives crashes (written to durable storage).

---

## Q2. (Beginner) What is a “dirty read”? Which isolation level prevents it?

**Answer:**  
A **dirty read** is reading **uncommitted** data from another transaction. If that transaction rolls back, you’ve seen data that “never existed.” **Read uncommitted** allows it; **read committed** and above prevent it. So **read committed** is the minimum level that prevents dirty reads.

---

## Q3. (Intermediate) What are “non-repeatable read” and “phantom read”? Which isolation levels prevent them?

**Answer:**  
**Non-repeatable read**: same row read twice in one transaction, but the row is **updated** by another transaction in between (value changes). **Phantom read**: same query run twice returns **different sets of rows** (new rows inserted or deleted by another transaction). **Repeatable read** typically prevents non-repeatable reads (same row); **serializable** prevents phantoms (same predicate). Exact behavior is DB-specific (e.g. PostgreSQL repeatable read uses snapshots and can block phantoms in practice).

---

## Q4. (Intermediate) List the four standard isolation levels (from least to most strict) and what they prevent.

**Answer:**  
(1) **Read uncommitted** — allows dirty reads. (2) **Read committed** — no dirty reads; non-repeatable reads and phantoms possible. (3) **Repeatable read** — no dirty reads, no non-repeatable reads; phantoms possible (in standard). (4) **Serializable** — full isolation; no dirty, non-repeatable, or phantom reads. Stricter levels can reduce concurrency (more blocking or aborts).

---

## Q5. (Intermediate) How do you set the isolation level for a session or transaction? Give PostgreSQL and MySQL syntax.

**Answer:**  
**PostgreSQL**: **SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED**; or **BEGIN; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE; ...**. **MySQL**: **SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ**; or **SET TRANSACTION ...** before START TRANSACTION. **Oracle**: **ALTER SESSION SET ISOLATION_LEVEL = SERIALIZABLE**; or at transaction start. Usually set at transaction start; some DBs allow only before first statement.

---

## Q6. (Advanced) What is “snapshot isolation” (or “MVCC”)? How does it differ from locking for isolation?

**Answer:**  
**Snapshot isolation** (often implemented via **MVCC** — multiversion concurrency control): each transaction sees a **consistent snapshot** of the DB (as of transaction start or first read). Reads don’t block writes; writes don’t block reads (until they conflict). **Locking**: readers/writers block each other (e.g. shared/exclusive locks). MVCC gives better read concurrency; conflicts are detected at commit (e.g. “first committer wins” or serializable snapshot isolation with rollback).

---

## Q7. (Advanced) In PostgreSQL, what is the difference between “Read committed” and “Repeatable read” in terms of when the snapshot is taken?

**Answer:**  
**Read committed**: a new snapshot is taken for **each statement**; so you see the latest committed state before each query. **Repeatable read**: the snapshot is taken at the **start of the first statement** in the transaction; all subsequent statements see that same snapshot. So in repeatable read you don’t see changes committed by others after your snapshot, and you avoid non-repeatable reads.

---

## Q8. (Advanced) Production scenario: A financial “transfer” runs as: read balance A, read balance B, update A, update B, commit. Under read committed, what can go wrong? What isolation level (or pattern) would you use, and how would the backend implement it?

**Answer:**  
Under **read committed**: two concurrent transfers can interleave (e.g. both read A=100, both debit 10, both write 90 — one update lost). Use **repeatable read** or **serializable** so each transaction sees a consistent view and the second to commit can be aborted (e.g. “could not serialize”) and retried. Or use **explicit locking**: **SELECT ... FOR UPDATE** on rows A and B so the second transaction blocks until the first commits. Backend: run in one transaction with **REPEATABLE READ** or **SERIALIZABLE**, and **SELECT ... FOR UPDATE** on the two accounts; on serialization failure, retry. Never do “read balance, then update” without locking or sufficient isolation.

---

## Q9. (Advanced) What is “write skew”? Does repeatable read prevent it? Does serializable?

**Answer:**  
**Write skew**: two transactions read overlapping data (e.g. “total bookings < capacity”), both see “OK,” both write, and the combined result violates the invariant (e.g. overbooked). **Repeatable read** (in standard and many implementations) does **not** prevent write skew (each sees a consistent snapshot but doesn’t re-check the predicate on commit). **Serializable** (true serializability) prevents it by detecting the conflict and aborting one transaction. Use serializable or explicit locks (e.g. lock a “guard” row) for such invariants.

---

## Q10. (Advanced) How do PostgreSQL, MySQL, and Oracle implement serializable isolation? What should the application do on serialization failure?

**Answer:**  
**PostgreSQL**: Serializable snapshot isolation (SSI); detects read-write conflicts and aborts one transaction with **serialization_failure**. **MySQL InnoDB**: Serializable uses strong locking (e.g. range locks); can block. **Oracle**: Serializable uses snapshots and can return **ORA-08177** on conflict. **Application**: catch the error (e.g. **40001** or **serialization_failure**), **rollback**, and **retry** the transaction (with backoff). Design so retries are idempotent or safe.
