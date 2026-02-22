# 4. MongoDB Queries, Projection & Operators

## Q1. (Beginner) How do you find documents where a field equals a value? How do you find where a field is in a list of values?

**Answer:**  
Equals: `db.users.find({ status: 'active' })`.  
In list: `db.users.find({ status: { $in: ['active', 'pending'] } })`.  
Not in list: `db.users.find({ status: { $nin: ['banned'] } })`.

---

## Q2. (Beginner) What is projection? How do you return only `name` and `email` from `users`?

**Answer:**  
**Projection** limits which fields are returned. Second argument to `find`:

```javascript
db.users.find({}, { name: 1, email: 1 });
// or exclude: { password: 0, internal: 0 }
```
`_id` is included by default; to exclude: `{ name: 1, email: 1, _id: 0 }`.

---

## Q3. (Intermediate) Write a query that finds users where `age` is greater than or equal to 18 and less than 65.

**Answer:**
```javascript
db.users.find({
  age: { $gte: 18, $lt: 65 }
});
```
Other comparison operators: `$gt`, `$lte`, `$ne`, `$eq`.

---

## Q4. (Intermediate) How do you query for documents where a nested field matches (e.g. `address.city` equals "NYC")?

**Answer:**  
Use dot notation: `db.users.find({ "address.city": "NYC" })`. For nested objects, quotes are required when the key contains a dot. Same in projection: `{ "address.city": 1 }`.

---

## Q5. (Intermediate) What do `$and`, `$or`, and `$nor` do? Write a query: status is "active" OR (role is "admin" AND verified is true).

**Answer:**  
**$and**: all conditions must match. **$or**: at least one. **$nor**: none.

```javascript
db.users.find({
  $or: [
    { status: 'active' },
    { $and: [ { role: 'admin' }, { verified: true } ] }
  ]
});
```

---

## Q6. (Advanced) How do you query for documents where an array field contains a value? Where it contains all of a set of values? Where it has at least one element matching a condition?

**Answer:**  
**Contains value**: `db.items.find({ tags: 'javascript' })` or `{ tags: { $in: ['javascript'] } }`.  
**Contains all**: `db.items.find({ tags: { $all: ['javascript', 'node'] } })`.  
**At least one element matching**: `db.items.find({ scores: { $elemMatch: { $gte: 80, $lt: 90 } } })` or for a single condition `{ "scores": { $gt: 80 } }` (matches if any element > 80).

---

## Q7. (Advanced) What is `$exists`? How do you find documents that have a field vs that don’t?

**Answer:**  
**$exists: true** — field is present (can be null). **$exists: false** — field is missing.

```javascript
db.users.find({ phone: { $exists: true } });
db.users.find({ phone: { $exists: false } });
```
To find “has field and is not null”: `{ phone: { $exists: true, $ne: null } }`.

---

## Q8. (Advanced) Production scenario: Your API supports filtering products by `category`, `minPrice`, `maxPrice`, and optional `tags` (array). Build a MongoDB filter object from request query params in Node.js.

**Answer:**
```javascript
function buildProductFilter(query) {
  const filter = {};
  if (query.category) filter.category = query.category;
  if (query.minPrice != null || query.maxPrice != null) {
    filter.price = {};
    if (query.minPrice != null) filter.price.$gte = Number(query.minPrice);
    if (query.maxPrice != null) filter.price.$lte = Number(query.maxPrice);
  }
  if (query.tags && query.tags.length) {
    filter.tags = { $all: Array.isArray(query.tags) ? query.tags : [query.tags] };
  }
  return filter;
}

// Usage: Product.find(buildProductFilter(req.query))
```
Validate/sanitize input (e.g. category whitelist, max limit on tags) in production.

---

## Q9. (Advanced) How do you use a regex in a MongoDB query? How do you make it case-insensitive and use an index when possible?

**Answer:**  
**Regex**: `db.users.find({ name: /john/i })` or `{ name: { $regex: 'john', $options: 'i' } }`. **Case-insensitive**: `$options: 'i'`. **Index**: leading wildcard (`/^prefix/`) can use an index; `/suffix$/` can use index in some cases; `/.*substring.*/` generally cannot. Prefer anchored regex when you can (e.g. `^john`) for index use.

---

## Q10. (Advanced) What is the difference between `find` + cursor and `find().toArray()` in the driver? When would you use a cursor in the backend?

**Answer:**  
**find()** returns a **cursor** (lazy); documents are fetched in batches as you iterate. **.toArray()** loads all matching documents into memory. Use a **cursor** when: result set can be large (e.g. export, batch processing); use **cursor.forEach()** or **for await (const doc of cursor)** to stream. Use **toArray()** or **find().limit(n)** when the result set is bounded and small (e.g. API page). Never call **toArray()** on unbounded result sets in production.
