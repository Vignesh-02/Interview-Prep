# 17. Transactions (BEGIN, COMMIT, ROLLBACK)

## Q1. (Beginner) What is a transaction? What does COMMIT do? What does ROLLBACK do?

**Answer:**  
A **transaction** is a unit of work: either all changes are applied (**COMMIT**) or none are (**ROLLBACK**). **COMMIT** makes the changes permanent and visible to others. **ROLLBACK** discards changes since the last COMMIT (or since start of transaction). After COMMIT or ROLLBACK, the transaction ends.

---

## Q2. (Beginner) How do you start a transaction in PostgreSQL, MySQL, and Oracle?

**Answer:**  
**PostgreSQL**: **BEGIN;** or **START TRANSACTION;** (implicit with first statement in some configs). **MySQL**: **START TRANSACTION;** or **BEGIN;** (InnoDB). **Oracle**: Transactions are implicit; no explicit BEGIN (transaction starts on first DML); **COMMIT** / **ROLLBACK** end it. **SQL Server**: **BEGIN TRANSACTION;**.

---

## Q3. (Intermediate) What is autocommit? How does it affect when a transaction starts and ends?

**Answer:**  
With **autocommit** on, each statement is its own transaction (implicit COMMIT after each). So a single UPDATE is committed immediately. Turn autocommit off to group statements: **SET autocommit = 0** (MySQL) or use **BEGIN** (PostgreSQL). Backend drivers often default to autocommit; use connection-level transaction control (e.g. **connection.beginTransaction()**) to run multiple statements in one transaction.

---

## Q4. (Intermediate) What is a savepoint? When would you use one?

**Answer:**  
A **savepoint** is a named point within a transaction that you can roll back to (without rolling back the whole transaction). **SAVEPOINT name;** then **ROLLBACK TO name;**. Use when part of the work is optional: try an operation, and if it fails, roll back to the savepoint and continue. Not all DBs support savepoints (PostgreSQL, Oracle, MySQL InnoDB do).

---

## Q5. (Intermediate) Why should the backend use a single transaction for “create order + insert order_items”?

**Answer:**  
So that either **all** inserts succeed or **none** do. Without a transaction, if order_items insert fails after order insert, you get an order with no items (orphan or inconsistent state). With a transaction, on failure you ROLLBACK and retry or report; on success COMMIT. Also keeps the operation atomic for other sessions (they see the full order or nothing).

---

## Q6. (Advanced) What is “read uncommitted” vs “read committed”? Which problem does each prevent or allow?

**Answer:**  
**Read uncommitted**: Can see uncommitted changes (dirty reads). **Read committed**: Only see committed data; no dirty reads. So read committed prevents dirty reads; read uncommitted does not. Read committed can still have non-repeatable reads (same query twice, different result) and phantom reads (new rows appear). Higher isolation (repeatable read, serializable) address those.

---

## Q7. (Advanced) What happens if the client disconnects in the middle of a transaction without COMMIT or ROLLBACK?

**Answer:**  
The DB **rolls back** the transaction (connection close or timeout is treated as abort). So uncommitted changes are lost. That’s why backends should explicitly COMMIT on success and ROLLBACK on error (or let the driver do it on disconnect). Use connection pooling carefully: return a connection to the pool only after COMMIT/ROLLBACK so the next user doesn’t see an open transaction.

---

## Q8. (Advanced) Production scenario: A payment flow does: (1) insert into payments, (2) update orders set paid=true, (3) call external inventory API. How would you structure transactions and the external call? What if the API call fails?

**Answer:**  
Run (1) and (2) in **one database transaction**. After COMMIT, call (3) the inventory API. If the API fails: you’ve already committed payment and order update, so you need **compensating actions** (e.g. refund, mark order for manual review, or retry queue). Do **not** hold the DB transaction open during the API call (long lock, risk of deadlock/timeout). Optionally: store “payment succeeded, inventory not yet updated” and have a job retry the API; on permanent failure, trigger refund workflow. Backend: transaction for DB; then async or sync API call with idempotency and retries.

---

## Q9. (Advanced) What is an implicit transaction (e.g. in Oracle)? How does that affect application code?

**Answer:**  
In **Oracle**, a transaction starts implicitly with the first DML; there’s no explicit BEGIN. **COMMIT** or **ROLLBACK** ends it. So application code must always end with COMMIT or ROLLBACK; otherwise the next statement might still be in the previous transaction or a new one (driver-dependent). In PostgreSQL/MySQL with autocommit off, you must BEGIN explicitly in app code. Backend: use a pattern like “begin → run statements → commit or rollback” and ensure rollback on exception.

---

## Q10. (Advanced) How does connection pooling interact with transactions? What can go wrong?

**Answer:**  
If a connection is returned to the pool with an **open transaction** (no COMMIT/ROLLBACK), the next user of that connection can see or continue that transaction (connection state leak). So: always **COMMIT** or **ROLLBACK** before returning the connection; use a wrapper that rolls back on exception. Some pools can reset the connection (e.g. ROLLBACK on checkout). Never assume a connection from the pool is in autocommit or clean state; set isolation level and state explicitly when needed.
