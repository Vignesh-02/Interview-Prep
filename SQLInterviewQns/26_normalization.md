# 26. Normalization and Normal Forms — Senior

## Q1. (Beginner) What is database normalization? What problem does it solve?

**Answer:**  
**Normalization** is designing tables to reduce **redundancy** and **update anomalies** by splitting data into tables linked by keys. It avoids: (1) **Update anomaly** — changing a fact in one place. (2) **Insert anomaly** — can’t insert without unrelated data. (3) **Delete anomaly** — deleting one fact removes others. We use **normal forms** (1NF, 2NF, 3NF, BCNF) as rules.

---

## Q2. (Beginner) What is 1NF? What does “atomic” mean here?

**Answer:**  
**First Normal Form (1NF)**: Each column has **atomic** (indivisible) values; no repeating groups; each row is unique (e.g. has a primary key). “Atomic” means one value per cell (e.g. no comma-separated list in one column). So split “phones” into a separate row per phone or a separate table.

---

## Q3. (Intermediate) What is 2NF? When is a table in 2NF?

**Answer:**  
**Second Normal Form (2NF)**: Table is in 1NF and every **non-prime** attribute depends on the **whole** primary key (no partial dependency). So if PK is (order_id, product_id), no column should depend only on order_id. Violation example: order_date in that table (depends only on order_id). Fix: move order_date to an orders table.

---

## Q4. (Intermediate) What is 3NF? What is “transitive dependency”?

**Answer:**  
**Third Normal Form (3NF)**: Table is in 2NF and no **transitive dependency**: no non-prime attribute depends on another non-prime attribute. So if A → B and B → C, then A → C is transitive through B. Example: (emp_id, dept_id, dept_name) — dept_name depends on dept_id. Fix: move (dept_id, dept_name) to a department table.

---

## Q5. (Intermediate) What is BCNF? How does it differ from 3NF?

**Answer:**  
**Boyce-Codd Normal Form (BCNF)**: For every non-trivial functional dependency **X → Y**, **X** is a superkey (X determines the whole row). Stricter than 3NF: 3NF allows Y to be part of a candidate key; BCNF requires every determinant to be a superkey. BCNF removes more redundancy; in practice 3NF is often enough and sometimes we accept controlled redundancy (denormalization).

---

## Q6. (Advanced) When might you **denormalize**? Give two examples.

**Answer:**  
(1) **Reporting/analytics** — avoid many JOINs; duplicate columns (e.g. customer_name on orders) for faster reads. (2) **High read load** — duplicate or aggregate data (e.g. count on parent) to avoid recomputing. (3) **Historical snapshot** — store denormalized copy at event time (e.g. order with product name as of order date). Trade-off: more storage and update cost; use when read performance or simplicity matters more.

---

## Q7. (Advanced) What is a functional dependency? How does it relate to keys?

**Answer:**  
A **functional dependency** (FD) **X → Y** means: for each value of X there is exactly one value of Y (X determines Y). A **candidate key** is a minimal set of attributes that determines the whole row (superkey). Normal forms are defined using FDs: 2NF/3NF/BCNF restrict which FDs are allowed (no partial dependency, no transitive dependency, every determinant is a superkey).

---

## Q8. (Advanced) Production scenario: You’re designing schema for an e-commerce “order” and “order line.” Someone suggests storing product_name and product_price on each order line “for history.” Is that normalized? Is it a good idea? Justify.

**Answer:**  
Storing **product_name** and **product_price** on the order line is **denormalization** (they depend on product_id; in 3NF they’d live in products). It’s **good** for orders: (1) **Historical accuracy** — we keep the name/price at order time even if the product changes later. (2) **Read performance** — order detail page doesn’t need to JOIN products. (3) **Audit** — we know what was charged. So: keep product_id (FK) for reference, and **also** store name and price on the line. Normalize current catalog in products; denormalize snapshot on orders.

---

## Q9. (Advanced) What is 4NF and 5NF? When do they matter?

**Answer:**  
**4NF** (Fourth NF): No non-trivial **multivalued dependencies** (MVD) unless the determining side is a superkey. MVD: X →→ Y means for each X there is a **set** of Y values independent of other attributes. **5NF** (Project-Join NF): No non-trivial **join dependencies** that aren’t implied by keys. They matter when you have multi-valued or complex join dependencies (e.g. ternary relationships). Many practical schemas stop at 3NF or BCNF.

---

## Q10. (Advanced) How does normalization interact with how the backend (e.g. ORM) models entities and relationships?

**Answer:**  
Normalized tables map to **entities** and **relationships**: one table per entity (or per many-to-many with a join table). ORMs map tables to models and use **relations** (e.g. order has many order_lines; order_line belongs to product). Normalization keeps one source of truth; the ORM loads related data via JOINs or separate queries. Denormalized columns (e.g. product_name on order_line) can be mapped as plain attributes; the app must not treat them as the source of truth for the current product. Migrations and seeding become important when schema is normalized (many related tables).
