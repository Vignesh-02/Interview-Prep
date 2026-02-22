# 16. Table Design, PK, FK, Constraints

## Q1. (Beginner) What is a primary key? Can it be NULL? Can it be composite?

**Answer:**  
A **primary key** uniquely identifies each row. It cannot be **NULL** (in standard SQL). It can be **composite** (multiple columns); then the combination must be unique and not NULL. A table has at most one primary key. It’s the default “clustering” or main index in many engines.

---

## Q2. (Beginner) What is a foreign key? What does ON DELETE CASCADE do?

**Answer:**  
A **foreign key** references a primary or unique key in another (or same) table. It enforces referential integrity. **ON DELETE CASCADE**: when the referenced row is deleted, the DB automatically deletes rows that reference it. Alternatives: **ON DELETE SET NULL**, **ON DELETE RESTRICT** (default in many DBs; prevent delete if references exist), **ON DELETE NO ACTION**.

---

## Q3. (Intermediate) What is the difference between UNIQUE and PRIMARY KEY?

**Answer:**  
**PRIMARY KEY** is unique and not NULL; there is one per table. **UNIQUE** allows NULL (in standard SQL, one NULL per column; DBs differ). You can have multiple UNIQUE constraints. Use UNIQUE for alternate keys (e.g. email); use PK for the main identifier (often a surrogate id).

---

## Q4. (Intermediate) When would you use a surrogate key (e.g. auto-increment id) vs a natural key (e.g. email, (order_id, line_no)) as primary key?

**Answer:**  
**Surrogate** (id): stable, simple joins, no change when business key changes (e.g. email). **Natural**: fewer joins, no extra column, enforces business uniqueness. Use surrogate when the natural key can change, is large, or composite and used everywhere. Use natural when it’s stable and small (e.g. (order_id, line_no) for order lines). Often: surrogate PK + UNIQUE on natural key(s).

---

## Q5. (Intermediate) What is a CHECK constraint? Give an example.

**Answer:**  
A **CHECK** constraint is a boolean expression that must hold for every row. Example: **CHECK (amount >= 0)**, **CHECK (status IN ('pending', 'active', 'done'))**. It rejects INSERT/UPDATE that violate the condition. Use for simple invariants; complex logic may go in triggers or application.

---

## Q6. (Advanced) Design a schema for “orders” and “order_items” (one order, many items). Include keys and foreign keys. Should order_items have a separate PK?

**Answer:**  
**orders**: order_id (PK), customer_id (FK), created_at, total. **order_items**: order_id (FK), line_no (e.g. 1, 2, 3), product_id (FK), quantity, price. PK of order_items: **(order_id, line_no)** (natural) or add **item_id** (surrogate) as PK and UNIQUE(order_id, line_no). FK: order_items.order_id → orders.order_id. Separate PK (item_id) is useful if items are referenced elsewhere (e.g. refunds); otherwise composite (order_id, line_no) is fine.

---

## Q7. (Advanced) What is a self-referencing foreign key? Give an example and a constraint consideration.

**Answer:**  
A **self-referencing** FK points to the same table (e.g. **employees.manager_id** → **employees.employee_id**). Ensures every manager_id is a valid employee. Consider **ON DELETE**: RESTRICT or SET NULL (don’t CASCADE if deleting a person would delete their reports). Check for cycles if you allow updates (application or trigger).

---

## Q8. (Advanced) Production scenario: You’re adding a “teams” feature: users can be in one team; teams have a name and a lead (user_id). Design tables with PKs, FKs, and constraints. How would the backend (e.g. an ORM) create a team and assign the lead without violating FKs?

**Answer:**  
**teams**: team_id (PK), name, lead_user_id (FK → users.user_id, nullable initially or deferrable). **users**: user_id (PK), team_id (FK → teams.team_id, nullable). Chicken-and-egg: creating a team with a lead requires the user to exist; assigning the user to the team requires the team to exist. Options: (1) Create team with lead_user_id NULL, update user’s team_id, then update team’s lead_user_id. (2) Use **DEFERRABLE** constraints (Oracle, PostgreSQL) and commit after both updates. (3) Create team and user in one transaction; insert team first with lead_user_id NULL, insert/update user with team_id, then update team.lead_user_id. Backend: run in a single transaction; use application-level ordering or deferred constraints.

---

## Q9. (Advanced) What is DEFERRABLE constraint (PostgreSQL/Oracle)? When is it useful?

**Answer:**  
**DEFERRABLE** constraints can be checked at **commit** instead of at the end of each statement. So you can insert A, then B (where B references A), and the FK is checked when you commit. Useful for circular references or when the order of operations within a transaction would temporarily violate the constraint. **SET CONSTRAINTS ... DEFERRED** in the transaction.

---

## Q10. (Advanced) How do PostgreSQL, MySQL, and Oracle differ in default behavior for FK (e.g. ON DELETE, deferrability, naming)?

**Answer:**  
**PostgreSQL**: Default ON DELETE is NO ACTION (check at end of statement); supports DEFERRABLE. **MySQL**: Default is RESTRICT; InnoDB checks immediately; no DEFERRABLE. **Oracle**: Default NO ACTION; supports DEFERRABLE. Naming: all allow naming constraints; syntax differs (e.g. **CONSTRAINT fk_name FOREIGN KEY ...**). Backend: design FKs so that application logic doesn’t rely on DB-specific behavior; document ON DELETE/UPDATE and handle in code if needed.
