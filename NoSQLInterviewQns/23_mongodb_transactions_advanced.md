# 23. MongoDB Transactions & Advanced Aggregation — Senior

## Q1. (Beginner) When did MongoDB support multi-document ACID transactions? What is the requirement (e.g. replica set)?

**Answer:**  
**Multi-document transactions** are supported in MongoDB 4.0+ (replica set) and 4.2+ (sharded). **Requirement**: replica set (or sharded cluster); standalone doesn’t support transactions. Transactions are ACID across multiple documents/collections within a single replica set or shard.

---

## Q2. (Beginner) How do you start a transaction and commit or abort it in the Node.js driver?

**Answer:**
```javascript
const session = client.startSession();
try {
  await session.withTransaction(async () => {
    await col1.insertOne({ a: 1 }, { session });
    await col2.updateOne({ _id: 2 }, { $set: { x: 2 } }, { session });
  });
} finally {
  await session.endSession();
}
```
**withTransaction** runs the callback; on success it commits; on throw it aborts. All ops must use **session**. Or manually: `session.startTransaction()`, then `session.commitTransaction()` / `session.abortTransaction()` in try/catch/finally.

---

## Q3. (Intermediate) What is $lookup? When would you use it instead of embedding or multiple application queries?

**Answer:**  
**$lookup** is a left-outer-join-like stage: for each document, look up matching documents in another collection and add as an array field. Use when: (1) Referenced data is in another collection and you want one aggregation to return combined result. (2) Referenced data changes often (normalized). (3) One-to-many where “many” is bounded per doc. Prefer **embedding** when data is read together and stable; prefer **application-level** queries when $lookup would pull too much data or you need to paginate the “many” side.

---

## Q4. (Intermediate) What is $facet? Give one use case.

**Answer:**  
**$facet** runs **multiple pipelines** on the same input documents and returns multiple outputs in one stage. Use when you need **several aggregations** in one pass (e.g. total count, top 5 by category, and histogram by date from the same set). Example: one $match, then $facet with "count", "topByCategory", "byDate" each running different $group/$sort. Reduces round-trips and re-scanning.

---

## Q5. (Intermediate) How do you use $setWindowFields (or window functions in aggregation)? What is it for?

**Answer:**  
**$setWindowFields** (MongoDB 5.0+) computes values over a **window** of documents (partition + order + frame). Use for: running totals, moving averages, rank, row number. Example: partition by userId, order by date, compute sum over previous rows. Replaces some application-side logic and multiple passes.

---

## Q6. (Advanced) Production scenario: You need to move balance from account A to account B (two documents). Implement it with a multi-document transaction in Node.js (Mongoose or driver). Handle abort and retry.

**Answer:**
```javascript
async function transfer(fromId, toId, amount) {
  const session = await mongoose.startSession();
  session.startTransaction();
  try {
    const from = await Account.findOneAndUpdate(
      { _id: fromId, balance: { $gte: amount } },
      { $inc: { balance: -amount } },
      { new: true, session }
    );
    if (!from) throw new Error('Insufficient balance');
    await Account.findOneAndUpdate(
      { _id: toId },
      { $inc: { balance: amount } },
      { session }
    );
    await session.commitTransaction();
  } catch (e) {
    await session.abortTransaction();
    throw e;
  } finally {
    session.endSession();
  }
}
```
Use **findOneAndUpdate** with condition so we don’t deduct if balance &lt; amount; both updates in same session; commit or abort.

---

## Q7. (Advanced) What are transaction time limit and write concern for transactions? How do you set them?

**Answer:**  
**Time limit**: transactions have a default max duration (e.g. 60s); after that they abort. Set **maxCommitTimeMS** in commit options or in withTransaction options. **Write concern**: use **writeConcern** in session or in withTransaction (e.g. w: 'majority') so commit is durable. Long-running transactions should be avoided; break work into smaller transactions if needed.

---

## Q8. (Advanced) Write an aggregation that: for each product, joins its category name from a `categories` collection, then groups by category and sums quantity sold. Use $lookup and $group.

**Answer:**
```javascript
db.sales.aggregate([
  { $lookup: { from: 'categories', localField: 'categoryId', foreignField: '_id', as: 'cat' } },
  { $unwind: '$cat' },
  { $group: { _id: '$cat.name', totalQty: { $sum: '$quantity' } } }
]);
```
If sales have categoryId and categories have _id and name; $unwind converts one-element array to object. Then group by category name and sum.

---

## Q9. (Advanced) What is the difference between $project and $addFields in aggregation? When does order of stages matter for performance?

**Answer:**  
**$project**: reshapes the document; only listed fields are kept (unless you use exclusion). **$addFields**: adds or overwrites fields; all others remain. **Order**: put **$match** as early as possible to reduce documents; then **$project**/$addFields to reduce size before $group/$sort. $match before $lookup when the match is on the current collection so $lookup sees fewer docs.

---

## Q10. (Advanced) How do transactions interact with MongoDB sharding? What are the limitations?

**Answer:**  
In **sharded** clusters, multi-document transactions are supported (4.2+) but with **limits**: (1) Operations in a transaction cannot span **multiple shards** for writes (single shard or same shard). (2) Or they can target multiple shards but with two-phase commit (more overhead). (3) Transaction size and time limits apply. Design so transactional writes touch one shard when possible (e.g. same shard key); otherwise use application-level consistency (e.g. saga) or accept cross-shard transaction overhead.
