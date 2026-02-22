# 5. MongoDB Aggregation Pipeline

## Q1. (Beginner) What is the aggregation pipeline? What are stages?

**Answer:**  
The **aggregation pipeline** is a sequence of **stages**; each stage takes a stream of documents and passes transformed documents to the next. Stages do filtering (`$match`), grouping (`$group`), sorting (`$sort`), projecting (`$project`), etc. Result is a single cursor of documents (or one doc if you use `$limit: 1`).

---

## Q2. (Beginner) What do `$match` and `$group` do? In what order should you typically put them?

**Answer:**  
**$match**: filters documents (like find). **$group**: groups by a key and computes aggregations (e.g. sum, avg, push). Put **$match** early to reduce documents before **$group** (better performance). Order: `$match` → `$group` → `$sort` / `$project` is common.

---

## Q3. (Intermediate) Write a pipeline that groups orders by `status` and counts how many orders per status.

**Answer:**
```javascript
db.orders.aggregate([
  { $group: { _id: '$status', count: { $sum: 1 } } }
]);
```
Result: `{ _id: 'shipped', count: 42 }, { _id: 'pending', count: 10 }, ...`

---

## Q4. (Intermediate) What is the difference between `$project` and `$addFields`?

**Answer:**  
**$project**: shapes the document; you choose which fields to include/exclude/rename; fields not listed can be dropped. **$addFields**: adds or overwrites only the specified fields; all other fields remain. Use **$project** to restrict or reshape; use **$addFields** when you only want to add or update a few fields and keep the rest.

---

## Q5. (Intermediate) How do you do a “join” in aggregation? What does `$lookup` do?

**Answer:**  
**$lookup** does a left-outer-join-like step: for each document, it looks up matching documents in another collection and adds them as an array field. Syntax: `$lookup: { from: 'collection', localField: 'field', foreignField: 'field', as: 'outputArray' }`. Then you can `$unwind` the array or keep it as a nested array. Use when data is in another collection; for frequently updated or large referenced data, $lookup is appropriate; for stable, small data, embedding might be simpler.

---

## Q6. (Advanced) When would you use `$lookup` instead of embedding documents? When would you prefer embedding?

**Answer:**  
Use **$lookup** when: (1) Referenced data changes often and should be normalized. (2) Many-to-many or one-to-many where the “many” is unbounded (document size limit). (3) Same entity is referenced from many places. Prefer **embedding** when: (1) Data is read together and rarely updated. (2) One-to-few (e.g. a few addresses per user). (3) You want to avoid extra round-trips and keep one read. Trade-off: embedding = one read, but duplication and size limit; $lookup = normalized, but extra stage and possible performance cost.

---

## Q7. (Advanced) Write a pipeline that: (1) matches orders with `status: 'completed'`, (2) groups by `customerId` and sums `total`, (3) sorts by total descending, (4) limits to top 10.

**Answer:**
```javascript
db.orders.aggregate([
  { $match: { status: 'completed' } },
  { $group: { _id: '$customerId', totalSpent: { $sum: '$total' } } },
  { $sort: { totalSpent: -1 } },
  { $limit: 10 }
]);
```

---

## Q8. (Advanced) Production scenario: You need “revenue by product category per month” from an `orders` collection where each order has `items: [{ productId, category, amount }]`. Design a pipeline and show the key stages.

**Answer:**  
Unwind items, then group by month (derived from order date) and category; sum amount:

```javascript
db.orders.aggregate([
  { $match: { status: 'completed' } },  // optional
  { $unwind: '$items' },
  {
    $group: {
      _id: {
        month: { $dateToString: { format: '%Y-%m', date: '$createdAt' } },
        category: '$items.category'
      },
      revenue: { $sum: '$items.amount' }
    }
  },
  { $sort: { _id.month: 1, revenue: -1 } }
]);
```
If `category` lives in a products collection, add a **$lookup** on `items.productId` to get category, then group by that.

---

## Q9. (Advanced) What do `$unwind` and `$unwind` with `preserveNullAndEmptyArrays` do?

**Answer:**  
**$unwind**: deconstructs an array field; one output document per array element; documents without the field or with empty array are dropped. **preserveNullAndEmptyArrays: true**: documents with missing or empty array still appear once (with the array field as null or empty). Use when you want to keep “parent” docs that have no array elements (e.g. left-join style after $lookup).

---

## Q10. (Advanced) How would you compute a “3-month moving average” of sales per product using the aggregation pipeline?

**Answer:**  
One approach: (1) $group by product and month to get monthly sales. (2) $sort by product and month. (3) Use **$setWindowFields** (MongoDB 5.0+) to compute moving average over a window:

```javascript
{ $setWindowFields: {
    partitionBy: '$_id.product',
    sortBy: { _id.month: 1 },
    output: {
      movingAvg: {
        $avg: '$sales',
        window: { range: [ -2, 0 ], unit: 'month' }  // current + 2 previous months
      }
    }
  }
}
```
Or: output monthly series, then in application code compute moving average over the last 3 months per product.
