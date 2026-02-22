# 2. Document Model & MongoDB Basics

## Q1. (Beginner) What is a “document” in MongoDB? What format is it stored in?

**Answer:**  
A **document** is a single record: a JSON-like structure of key-value pairs, stored as **BSON** (Binary JSON) — supports types like ObjectId, Date, BinData. Documents live inside a **collection** (analogous to a table). A collection has no enforced schema; documents can have different fields, which gives flexibility for evolution and nested data.

---

## Q2. (Beginner) What is the difference between a collection and a table (RDBMS)? What is `_id`?

**Answer:**  
A **collection** is like a table but **schema-less**: documents in the same collection can have different fields. **`_id`** is a unique identifier for each document; if you don’t provide one, MongoDB generates an **ObjectId** (12-byte, sortable by creation time). Every document must have an `_id`; it’s the primary key.

---

## Q3. (Intermediate) Write a MongoDB shell command to insert one document into a collection `users` with fields `name`, `email`, and `createdAt`.

**Answer:**
```javascript
db.users.insertOne({
  name: "Jane Doe",
  email: "jane@example.com",
  createdAt: new Date()
});
```
For multiple: `db.users.insertMany([{ ... }, { ... }])`.

---

## Q4. (Intermediate) How do you find all documents in a collection? How do you find one by `_id`?

**Answer:**
```javascript
db.users.find();                    // all
db.users.findOne({ _id: userId });   // one by _id (userId can be ObjectId or value)
```
For `_id` as string you may need: `db.users.findOne({ _id: new ObjectId("...") })`.

---

## Q5. (Intermediate) What is BSON and how does it differ from JSON for a backend developer?

**Answer:**  
**BSON** is Binary JSON: extended types (ObjectId, Date, BinData, int/long, decimal). **JSON** has no date type (strings or numbers); BSON has native Date. When the backend sends JSON to MongoDB, the driver serializes to BSON; when reading, BSON is deserialized (e.g. Date stays Date in Node). Use native Date in app code; the driver handles conversion.

---

## Q6. (Advanced) Production scenario: Your Node.js API stores user profiles in MongoDB. A new field `preferences.theme` must be added for existing users without a full migration. How do you model and backfill?

**Answer:**  
**Model**: Store `preferences` as an optional subdocument; `preferences.theme` optional (e.g. `'light' | 'dark' | 'system'`). **Backfill**: Run an update that sets default only where missing (no overwrite of existing preferences):

```javascript
// MongoDB shell or Node driver
db.users.updateMany(
  { "preferences.theme": { $exists: false } },
  { $set: { "preferences.theme": "system" } }
);
```

**Mongoose**: Same with `User.updateMany(...)`. New users get `preferences.theme` in app code; existing users get it via this one-time backfill. Application code should treat missing `preferences.theme` as default (e.g. `user.preferences?.theme ?? 'system'`).

---

## Q7. (Advanced) How does the MongoDB driver in Node.js represent `_id` and Date? How do you return JSON to an API client without leaking internal types?

**Answer:**  
**Driver**: `_id` is typically an **ObjectId**; dates are **Date**. To return JSON: (1) Call **`.toObject()`** on a Mongoose doc and then set `_id: doc._id.toString()` if you want string IDs. (2) Or use **lean()** and serialize: `JSON.stringify(doc, (k, v) => k === '_id' ? v.toString() : v)`. (3) Mongoose schema option **`toJSON: { virtuals: true, transform: (_, ret) => { ret.id = ret._id; delete ret._id; return ret; } }`** for API-shaped output. Never send raw ObjectId/BSON to REST clients; convert to string or a stable shape.

---

## Q8. (Advanced) What is the maximum BSON document size? How does it affect data modeling?

**Answer:**  
**Maximum document size is 16 MB**. So you cannot store unbounded arrays (e.g. millions of items) in one document. Use **referencing** or **bucketing** (e.g. comments in separate collection, or comments grouped by time bucket in a document). Design so that the largest expected document (with growth) stays under 16 MB.

---

## Q9. (Advanced) Compare inserting a document from Node.js using the native `mongodb` driver vs Mongoose. When would you use each?

**Answer:**  
**Native driver**: `collection.insertOne({ name: 'x', email: 'y' })` — no schema, no validation, no middleware. Use for simple scripts, high-throughput bulk ops, or when you don’t need ODM features. **Mongoose**: Define schema, then `User.create({ name, email })` — validation, defaults, middleware (pre/post), casting, virtuals. Use for application CRUD with business rules and consistent shape. Same MongoDB underneath; choose by need for schema and app logic.

---

## Q10. (Advanced) How would you implement “soft delete” for documents in MongoDB so the backend can filter them in all queries?

**Answer:**  
Add a field like **`deleted: true`** or **`deletedAt: ISODate`**. **Queries**: always add `deleted: { $ne: true }` (or `deletedAt: null`). **Mongoose**: global query middleware so every `find`, `findOne`, etc. gets `deleted: { $ne: true }` unless you use `.find().where('deleted').equals(true)` for admin. **Index**: compound index on (query filters + deleted) so performance stays good. Restore by setting `deleted: false` or `deletedAt: null`.
