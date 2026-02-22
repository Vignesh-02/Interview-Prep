# 7. MongoDB Data Modeling (Embed vs Reference)

## Q1. (Beginner) What does “embedding” mean in MongoDB? What does “referencing” mean?

**Answer:**  
**Embedding**: storing related data inside a single document as subdocuments or arrays (e.g. user with embedded addresses). **Referencing**: storing an ID (e.g. ObjectId) in one document that points to another document in another collection (e.g. order with `userId`). One read can get embedded data; referenced data needs a second query or $lookup.

---

## Q2. (Beginner) When is embedding a good choice? When is referencing a good choice?

**Answer:**  
**Embed** when: data is read together, one-to-few, rarely updated independently, small. **Reference** when: one-to-many with large “many,” many-to-many, or referenced data changes often and should live in one place. Also reference when a single document would exceed 16 MB or grow unbounded.

---

## Q3. (Intermediate) How do you model a one-to-many (e.g. one user, many orders) if the “many” side can grow large?

**Answer:**  
Store the “many” in a **separate collection** with a reference to the one: e.g. `orders` collection with `userId`. Query orders by `userId`; use indexing and pagination. Do **not** embed all orders in the user document (size limit, performance).

---

## Q4. (Intermediate) What is the “bucket” pattern? When would you use it?

**Answer:**  
The **bucket pattern**: group many items into documents by a bucket key (e.g. time window or category). Example: one document per user per month of events: `{ userId, month: '2024-01', events: [...] }`. Use when you have one-to-many that grows large but can be read in chunks (e.g. time-series); keeps document count and size under control while still batching reads.

---

## Q5. (Intermediate) How would you model a many-to-many (e.g. users and groups) in MongoDB?

**Answer:**  
**Option 1**: Store an array of IDs on one side (e.g. `group.memberIds: [userId1, userId2]`) and query “groups for user” with `find({ memberIds: userId })` (index on `memberIds`). **Option 2**: Junction collection `memberships: { userId, groupId }` with compound index; query both directions. Choose based on query patterns and size of the many-to-many.

---

## Q6. (Advanced) How do you model a product catalog with variable attributes (e.g. shirt has size/color, laptop has RAM/storage) without a fixed schema?

**Answer:**  
Use a **flexible document** per product: common fields (name, sku, price) plus an **attributes** object or array of { key, value }. Example: `{ name: 'Shirt', sku: 'S1', attributes: { size: 'M', color: 'blue' } }` and `{ name: 'Laptop', attributes: { ram: '16GB', storage: '512GB' } }`. Query with dot notation: `find({ 'attributes.color': 'blue' })`. For complex filtering, consider a search index or Elasticsearch. Avoid unbounded arrays of variable keys; keep attributes as a single object or bounded set.

---

## Q7. (Advanced) Production scenario: You are modeling “posts” and “comments.” Comments can be added frequently; the feed shows the latest 20 comments per post. Design the model and justify embed vs reference.

**Answer:**  
**Recommendation**: **Reference** — store comments in a `comments` collection with `postId` (and `userId`, `text`, `createdAt`). **Why**: comments grow unbounded; embedding would hit 16 MB and make post document writes heavy. Feed “latest 20 comments”: `db.comments.find({ postId }).sort({ createdAt: -1 }).limit(20)` with index `{ postId: 1, createdAt: -1 }`. **Alternative**: embed only the **last N** comments in the post (e.g. 5) for a quick preview and store the rest in `comments` — hybrid for different read paths.

---

## Q8. (Advanced) What is the “extended reference” pattern? When is it useful?

**Answer:**  
**Extended reference**: store not only the foreign key but a few frequently needed fields from the related entity (e.g. order stores `productId`, `productName`, `productPrice`). **Useful** when you always need those fields when reading the parent (e.g. order line always shows name and price) and want to avoid $lookup or extra reads. Trade-off: duplication and need to update if the source field changes (often acceptable for historical snapshots like orders).

---

## Q9. (Advanced) How would you model a category hierarchy (tree) in MongoDB for “get all descendants” or “get path to root”?

**Answer:**  
**Option 1**: Each node has `parentId` (reference). Get descendants: recursive application code or recursive aggregation (e.g. $graphLookup). Get path to root: walk parentId until null. **Option 2**: Store `ancestorIds` array on each document (materialized path); get descendants: `find({ ancestorIds: rootId })`; get path: use ancestorIds. **Option 3**: Nested document (embed children); good for small, static trees; harder to query “all descendants.”

---

## Q10. (Advanced) Compare storing “last 10 activities” embedded in a user document vs in a separate `activities` collection. Consider write volume and read patterns.

**Answer:**  
**Embedded last 10**: one read gets user + recent activity; each new activity is an update (e.g. $push + $slice to keep 10). Good for low write rate and when you only need “last 10.” **Separate collection**: better for high write volume (no large document updates), full history, and queries like “all activities for user in date range.” Use embedded for a small, fixed-size “preview”; use separate collection for full activity stream and analytics.
