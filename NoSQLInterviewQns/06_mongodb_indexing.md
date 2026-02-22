# 6. MongoDB Indexing (Single, Compound, TTL, Geo)

## Q1. (Beginner) What is an index in MongoDB? Why use one?

**Answer:**  
An **index** is a structure (e.g. B-tree) that lets MongoDB find documents by field value(s) without scanning the whole collection. **Benefits**: faster finds and sorts; **cost**: more storage and slower writes (indexes must be updated). Create indexes on fields you filter or sort by.

---

## Q2. (Beginner) How do you create a single-field index? How do you list indexes on a collection?

**Answer:**  
**Create**: `db.users.createIndex({ email: 1 })` — ascending; `-1` for descending. For unique: `db.users.createIndex({ email: 1 }, { unique: true })`. **List**: `db.users.getIndexes()`. The `_id` index is created by default.

---

## Q3. (Intermediate) What is a compound index? What is the “prefix” rule?

**Answer:**  
A **compound index** is on multiple fields, e.g. `{ status: 1, createdAt: -1 }`. The **prefix rule**: the index can support queries that use a **left prefix** of the index keys: e.g. `{ status: 1, createdAt: -1 }` supports `{ status }` and `{ status, createdAt }`, but not a query that uses only `{ createdAt }` (no prefix).

---

## Q4. (Intermediate) When would you use a compound index with ascending vs descending? How does sort order matter?

**Answer:**  
Index order (1 or -1) should match **equality then sort** for the query. Query `{ status: 'active' }` with `sort({ createdAt: -1 })` is efficient with index `{ status: 1, createdAt: -1 }`. If sort direction differs from index, MongoDB may use the index for filter but do an in-memory sort for the rest. Match the sort direction to the index when possible.

---

## Q5. (Intermediate) What is a TTL index? Give one use case and show how to create it.

**Answer:**  
A **TTL index** automatically deletes documents after a period. Use for: session data, temporary tokens, log entries. **Create**: `db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 })` — documents are removed when `createdAt` is older than 3600 seconds. The field must be a date or array of dates. A background job runs periodically to delete expired docs.

---

## Q6. (Advanced) What is a “covered” query? How do you check if a query is covered?

**Answer:**  
A query is **covered** when all requested fields are in the index, so MongoDB can return results from the index only (no document fetch). **Check**: run `.explain("executionStats")` and look for `"totalDocsExamined": 0` and that the returned fields are only from the index. Use projection to limit returned fields so they match the index keys.

---

## Q7. (Advanced) When would you use a geospatial index? How do you create a 2dsphere index and query “near”?

**Answer:**  
Use for location-based queries (near, within, geoWithin). **Create**: `db.places.createIndex({ location: '2dsphere' })` where `location` is GeoJSON (e.g. `{ type: 'Point', coordinates: [lng, lat] }`). **Query near**: `db.places.find({ location: { $nearSphere: { $geometry: { type: 'Point', coordinates: [lng, lat] } } } }).limit(10)`.

---

## Q8. (Advanced) Production scenario: Your API serves a feed sorted by `createdAt` desc and filtered by `userId`. Queries are slow. What index would you add and how would you verify it’s used?

**Answer:**  
Add a **compound index**: `{ userId: 1, createdAt: -1 }` so filter and sort are both satisfied by the index.

```javascript
db.posts.createIndex({ userId: 1, createdAt: -1 });
// Verify:
db.posts.find({ userId: 'u1' }).sort({ createdAt: -1 }).explain('executionStats');
// Check: winningPlan.inputStage.indexName, totalDocsExamined should be low
```
If you also filter by `status`, add it: `{ userId: 1, status: 1, createdAt: -1 }` (equality before range/sort).

---

## Q9. (Advanced) What is a text index? What are its limitations compared to a dedicated search engine (e.g. Elasticsearch)?

**Answer:**  
A **text index** supports full-text search (e.g. `$text: { $search: '...' }`), stemmed matching, and text score. **Limitations**: one text index per collection (or compound with one text key); no faceting, typo tolerance, or ranking sophistication like Elasticsearch; heavier load on the primary DB. Use for simple in-DB search; use Elasticsearch for rich search, analytics, and scale.

---

## Q10. (Advanced) How do you use `explain()` to see whether a query used an index? What key fields in the output should you look at?

**Answer:**  
Run `db.collection.find(...).explain("executionStats")`. **Look at**: (1) **winningPlan.inputStage.indexName** — which index was used (or COLLSCAN). (2) **executionStats.totalDocsExamined** vs **nReturned** — if examined >> returned, consider a better index. (3) **executionStats.executionTimeMillis**. (4) **stage: "IXSCAN"** — index scan; **stage: "COLLSCAN"** — collection scan (bad for large collections). Use **explain("allPlansExecution")** to compare plans.
