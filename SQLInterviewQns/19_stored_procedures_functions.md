# 19. Stored Procedures and Functions

## Q1. (Beginner) What is a stored procedure? How does it differ from a function (in SQL)?

**Answer:**  
A **stored procedure** is a named block of SQL (and often procedural code) that can be **called** (e.g. **CALL proc()**). It can perform multiple operations, use transactions, and may not return a value (or returns via OUT parameters/result sets). A **function** typically returns a **single value** (or table) and is used inside expressions (e.g. **SELECT my_func(x)**). Procedures: side effects, transactions; functions: often expected to be more “pure” in some DBs (e.g. no DML in PostgreSQL function by default depending on context).

---

## Q2. (Beginner) Why might you use a stored procedure instead of sending multiple statements from the application?

**Answer:**  
(1) **Reduce round-trips** — one CALL instead of many statements. (2) **Encapsulate logic** — business rules in one place. (3) **Security** — grant EXECUTE on the procedure instead of direct table access. (4) **Consistency** — same logic for all clients. (5) **Transaction** — procedure can run in one transaction. Downsides: logic in DB (harder to test, version with app, fewer tools); prefer application code for complex logic when possible.

---

## Q3. (Intermediate) What is an OUT or INOUT parameter? Give a one-line use case.

**Answer:**  
**OUT** (or **INOUT**) parameters let the procedure return values to the caller. **INOUT** is both input and output. Use case: procedure that computes a result and also returns an error code or a generated ID via OUT. Example: **CREATE PROCEDURE create_order(IN p_customer_id INT, OUT p_order_id INT)**.

---

## Q4. (Intermediate) In PostgreSQL, what is the difference between a function that returns void and a procedure (CREATE PROCEDURE)?

**Answer:**  
**PostgreSQL**: **PROCEDURE** (since PG 11) is called with **CALL**; can commit/rollback inside (transaction control). **FUNCTION** is called in an expression; traditionally runs in the caller’s transaction (no COMMIT inside). So use PROCEDURE when you need transaction control or multiple result sets; use FUNCTION when you need a return value in a query. Other DBs: semantics differ (e.g. Oracle procedure vs function).

---

## Q5. (Intermediate) How would the backend call a stored procedure? Give an example (pseudo-code) for Node and Python.

**Answer:**  
**Node (pg)**: **await client.query('CALL my_proc($1, $2)', [a, b]);** or **SELECT * FROM my_func($1)** for a function. **Python (psycopg2)**: **cur.callproc('my_proc', [a, b])** or **cur.execute('CALL my_proc(%s, %s)', [a, b])**. Use parameterized calls; never concatenate user input. Procedures that return result sets: **cur.execute('CALL ...'); rows = cur.fetchall()** (driver-dependent).

---

## Q6. (Advanced) What is a trigger? When would you use one vs doing the same in the application?

**Answer:**  
A **trigger** runs automatically when a table event occurs (INSERT/UPDATE/DELETE, before or after). Use for: audit log, maintaining derived columns, enforcing rules that must hold regardless of which app writes. Prefer application when: logic is complex, needs to be testable in app code, or should be consistent across services. Triggers are “invisible” to callers and can make debugging and reasoning harder; use sparingly.

---

## Q7. (Advanced) How do you return a result set from a stored procedure in PostgreSQL and MySQL?

**Answer:**  
**PostgreSQL**: A **FUNCTION** can **RETURNS SETOF row_type** or **RETURNS TABLE(...)** and use **RETURN QUERY SELECT ...**. Call with **SELECT * FROM my_func()**. Procedures (CALL) can have OUT parameters; returning a result set from CALL is done via refcursor or by having the procedure run a query that the driver can fetch (driver-specific). **MySQL**: **CALL** can produce result sets; the client fetches them like normal query results (multiple result sets possible). Backend: use driver APIs for multiple result sets if the procedure returns more than one.

---

## Q8. (Advanced) Production scenario: “When an order is inserted, reserve inventory (decrement stock) and send a notification.” Should this be in a trigger, a stored procedure, or the application? Discuss trade-offs.

**Answer:**  
**Application**: (1) Insert order. (2) Update inventory (or call inventory service). (3) Publish notification (queue/HTTP). Use a **transaction** for (1)+(2); then (3) after commit. Keeps logic in one place, testable, and notification doesn’t block the transaction. **Stored procedure**: Can do (1)+(2) in one transaction and return; app then does (3). Ensures order+inventory are atomic if all callers use the procedure. **Trigger**: Can do (1)+(2) in one transaction but (3) inside the DB is awkward (no HTTP from trigger); use trigger only for DB-only side effects (e.g. audit). Recommendation: procedure or application for order+inventory; application or async job for notification after commit.

---

## Q9. (Advanced) What is the risk of putting business logic in stored procedures for a multi-service or microservice architecture?

**Answer:**  
Logic is **locked in the DB**; only services that can call that DB can use it. Other services (different language, different DB) would duplicate logic or need to call this DB. Versioning and deployment: procedure changes require DB migrations and can break clients. Prefer **API + application logic** so all services use the same API; use procedures for performance-critical or atomic multi-table operations that one service owns.

---

## Q10. (Advanced) Compare PostgreSQL, MySQL, and Oracle in terms of procedure/function language, calling convention, and returning result sets.

**Answer:**  
**PostgreSQL**: **PL/pgSQL**; **CALL** for procedures; functions with **RETURNS TABLE** or **SETOF**; can use other languages (e.g. PL/Python). **MySQL**: **Stored procedures** in SQL-like syntax; **CALL**; can return result sets from SELECTs inside the procedure. **Oracle**: **PL/SQL**; procedures and functions; **RETURN** for functions; procedures use OUT parameters or ref cursors for result sets. **SQL Server**: T-SQL; **EXEC**; result sets from SELECT in procedure. Backend: use standard parameterized calls and handle result sets per driver documentation.
