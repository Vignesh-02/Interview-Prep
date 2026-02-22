# 3. MongoDB CRUD & Mongoose (Node.js)

## Q1. (Beginner) How do you insert a single document using the MongoDB Node.js driver? How with Mongoose?

**Answer:**  
**Driver**: `const result = await db.collection('users').insertOne({ name: 'A', email: 'a@x.com' });` — `result.insertedId` gives the new `_id`. **Mongoose**: `const user = await User.create({ name: 'A', email: 'a@x.com' });` — returns the saved document with `_id`. Both are async (Promises).

---

## Q2. (Beginner) How do you update one document by `_id` in MongoDB? Give both “replace” and “partial update” approaches.

**Answer:**  
**Replace** (overwrite whole document): `db.collection('users').replaceOne({ _id: id }, { name: 'B', email: 'b@x.com' });`  
**Partial update** (only change some fields): `db.collection('users').updateOne({ _id: id }, { $set: { name: 'B' } });`  
Use **updateOne** so only one document is updated; **replaceOne** for full-document replace.

---

## Q3. (Intermediate) Write Mongoose code to define a `User` schema with `name` (required string), `email` (required, unique), and `createdAt` (default Date), then create and save a user.

**Answer:**
```javascript
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema);

const user = await User.create({ name: 'Jane', email: 'jane@example.com' });
// user has _id, name, email, createdAt
```

---

## Q4. (Intermediate) What is the difference between `findOne` and `findById` in Mongoose? When would you use each?

**Answer:**  
**findById(id)** is shorthand for `findOne({ _id: id })`; it accepts string or ObjectId and converts. Use for “get by primary key.” **findOne(filter)** accepts any query (e.g. `{ email: 'x@y.com' }`). Use when looking up by a non-_id field. Both return one document or null.

---

## Q5. (Intermediate) How do you delete one document in MongoDB (driver and Mongoose)?

**Answer:**  
**Driver**: `await db.collection('users').deleteOne({ _id: id });`  
**Mongoose**: `await User.deleteOne({ _id: id });` or `await User.findByIdAndDelete(id);`  
Both return a result with `deletedCount`. Use **deleteOne** for a single doc; **deleteMany** only when you intend to remove multiple.

---

## Q6. (Advanced) What are Mongoose middleware (pre/post hooks)? Give one example of `pre('save')` that hashes a password before saving.

**Answer:**  
**Middleware** runs before or after a certain operation (e.g. save, remove). **pre('save')** runs before `.save()` (not before `.create()` unless it triggers save). Example: hash password before save:

```javascript
const bcrypt = require('bcrypt');

userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  this.password = await bcrypt.hash(this.password, 10);
  next();
});
```
Use **this.isModified('password')** so we only hash when password changed. Call **next()** (or pass error) to continue.

---

## Q7. (Advanced) Production scenario: Your API must create an order and update product stock in one “transaction.” How do you do it with MongoDB and Mongoose so both succeed or both fail?

**Answer:**  
Use **multi-document transactions** (MongoDB 4.0+). Start a session, start transaction, perform both ops, commit (or abort on error):

```javascript
const session = await mongoose.startSession();
session.startTransaction();
try {
  await Order.create([{ userId, items, total }], { session });
  for (const item of items) {
    await Product.updateOne(
      { _id: item.productId },
      { $inc: { stock: -item.qty } },
      { session }
    );
  }
  await session.commitTransaction();
} catch (e) {
  await session.abortTransaction();
  throw e;
} finally {
  session.endSession();
}
```
Requires a **replica set** (not standalone). Both create and update use the same `session` so they commit or roll back together.

---

## Q8. (Advanced) How do you do an “upsert” in MongoDB (insert if not exists, else update)? Show with Mongoose.

**Answer:**  
Use **updateOne** (or **findOneAndUpdate**) with **upsert: true**:

```javascript
await User.updateOne(
  { email: 'jane@example.com' },
  { $set: { name: 'Jane', lastLogin: new Date() } },
  { upsert: true }
);
```
Mongoose: same options on **updateOne** or **findOneAndUpdate**. **findOneAndUpdate** with `upsert: true` and `new: true` returns the document after update or the newly inserted one.

---

## Q9. (Advanced) What is the difference between `updateOne` and `updateMany`? What about `findOneAndUpdate`?

**Answer:**  
**updateOne**: at most one document updated (first match). **updateMany**: all documents matching the filter. **findOneAndUpdate**: same as updateOne but returns the document (before or after, depending on `new: true`). Use updateOne for “update this user”; updateMany for “mark all as read”; findOneAndUpdate when you need the updated (or previous) document in the response.

---

## Q10. (Advanced) How would you implement “find or create” (get user by email, or create if not exists) in Mongoose without race conditions?

**Answer:**  
Use **findOneAndUpdate** with **upsert: true** so a single atomic operation does “match or insert”:

```javascript
const user = await User.findOneAndUpdate(
  { email },
  { $setOnInsert: { name: name || email, createdAt: new Date() } },
  { upsert: true, new: true }
);
```
**$setOnInsert** only sets fields on insert, not on update. For true “find or create” with unique email, ensure a **unique index** on `email` so two concurrent requests don’t both insert. Alternatively use a try/catch: findOne, and if null then create; on duplicate key error, find again.
