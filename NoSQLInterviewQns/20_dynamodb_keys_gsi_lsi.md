# 20. DynamoDB Keys, GSI, LSI & Single-Table Design

## Q1. (Beginner) What is a GSI (Global Secondary Index)? How does it differ from the base table key?

**Answer:**  
A **GSI** is an **index** with its own **partition key and optional sort key** (can differ from the base table). DynamoDB maintains it automatically. Query/Scan can target the GSI. **Difference**: base table key is unique per item; GSI keys can repeat (multiple items per GSI key). GSI has its own throughput (provisioned) or on-demand; eventual consistency by default. Use GSI for **alternative access patterns** (e.g. query by email when base table is keyed by userId).

---

## Q2. (Beginner) What is an LSI (Local Secondary Index)? How does it differ from a GSI?

**Answer:**  
**LSI** has the **same partition key** as the base table but a **different sort key**. So you can query the same partition with a different sort order or filter on sort key. **Difference from GSI**: LSI is **local** to the partition (same partition key); GSI can have a completely different partition key. LSI must be created at table creation; GSI can be added later. LSI shares throughput with the base table; GSI has its own. Use LSI when you need another sort key for the same partition.

---

## Q3. (Intermediate) When would you use a GSI with a different partition key? Give an example.

**Answer:**  
When you need to **query by another attribute**. Example: base table (userId PK, sk SK) for user data; **GSI** with (email PK) so you can “get user by email” — Query GSI where email = 'x@y.com'. Another: base (orderId PK); GSI (userId PK, orderDate SK) for “all orders by user by date.”

---

## Q4. (Intermediate) What is single-table design? What is the benefit and the trade-off?

**Answer:**  
**Single-table design**: store multiple entity types and relationships in **one** table using **composite keys** (e.g. PK = USER#123, SK = PROFILE; PK = USER#123, SK = ORDER#456). **Benefit**: one Query can fetch related items (e.g. PK = USER#123); fewer tables and GSIs; flexible access patterns with careful key design. **Trade-off**: complex key design; one table to reason about; need to overload keys (e.g. PK/SK patterns for different entities).

---

## Q5. (Intermediate) How do you model “get all orders for a user” in single-table design? Show key design and Query call.

**Answer:**  
**Key design**: PK = `USER#userId`, SK = `ORDER#orderId` (or ORDER#timestamp). One item per order; same PK for all orders of that user. **Query**: `KeyConditionExpression: 'pk = :pk AND begins_with(sk, :prefix)', ExpressionAttributeValues: { ':pk': 'USER#u1', ':prefix': 'ORDER#' }`. Orders are returned in sort key order; add SK like timestamp for “latest first.”

---

## Q6. (Advanced) What is a hot partition in DynamoDB? How do you avoid it when the partition key has low cardinality?

**Answer:**  
**Hot partition**: one partition key gets much more read/write than others; that partition is throttled. **Avoid**: (1) **High cardinality** partition key (e.g. userId, not “type”). (2) **Add suffix** to spread: e.g. PK = shardId (random 0–N) + userId, or use composite (userId, date). (3) **Use write sharding**: e.g. PK = tenantId#randomSuffix for even spread; query with multiple queries and merge if needed. Design so traffic is spread across many partition keys.

---

## Q7. (Advanced) How do you implement “get item by ID” and “list items by type” in single-table design with one GSI?

**Answer:**  
**Base table**: PK = `ENTITY#id`, SK = `METADATA` (or same as PK if no SK) for “get by ID” (GetItem). **GSI**: GSI_PK = `TYPE#typeName`, GSI_SK = `createdAt` (or id). Items carry **type** and **createdAt**; GSI projects them. “List by type”: Query GSI where GSI_PK = TYPE#post, order by GSI_SK. **Alternative**: base PK = TYPE#typeName, SK = id; then “list by type” is Query on base table; “get by ID” needs GSI on id or a second table. One GSI can serve “by type” if base is “by id.”

---

## Q8. (Advanced) Production scenario: You need to support (1) get user by userId, (2) get user by email, (3) list orders by userId (by date). Design keys and indexes (single table) and list the operations.

**Answer:**  
**Base table**: PK = `USER#userId`, SK = `PROFILE` for user profile; PK = `USER#userId`, SK = `ORDER#date#orderId` for orders. **Operations**: (1) GetItem PK=USER#userId, SK=PROFILE. (2) GSI: GSI_PK = email (or EMAIL#email), GSI_SK = userId; Query GSI by email → get userId, then GetItem or store email in item and Query GSI to get one item. (3) Query base table PK=USER#userId, SK begins_with ORDER#. **GSI**: partition key = email (unique), sort key = userId; one item per user for “get user by email.”

---

## Q9. (Advanced) What is sparse index? How do you use a GSI for “find items where attribute X exists”?

**Answer:**  
**Sparse index**: GSI (or LSI) includes only items that have the index key attributes. So only items with that attribute appear in the GSI. Use: **GSI with PK = status, SK = updated** where status is only set when “active”; then Query GSI where status = 'active' returns only active items. Or GSI on “type” so only items of that type are in the GSI. Sparse = smaller index, efficient for “exists” queries.

---

## Q10. (Advanced) Compare DynamoDB’s key model and query model to Cassandra’s. What is similar and what is different?

**Answer:**  
**Similar**: partition key determines location; sort key gives ordering within partition; no JOINs; design for access patterns. **Differences**: DynamoDB has GSIs (alternative partition key); Cassandra has clustering columns and materialized views. DynamoDB Query always by partition key (+ optional sort condition); Cassandra same. DynamoDB is managed, single-region or global table; Cassandra is self-managed or managed (e.g. Astra), multi-DC. Both favor denormalization and single-table/similar design for access patterns.
