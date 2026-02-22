# 16. Elasticsearch Basics & Indexing

## Q1. (Beginner) What is Elasticsearch? What is it best used for?

**Answer:**  
**Elasticsearch** is a **search and analytics** engine built on Apache Lucene. It stores documents (JSON) in **indices** and provides full-text search, filters, and aggregations. Best for: full-text search (e.g. product search, log search), log analytics, metrics, APM. Often used with Kibana for visualization.

---

## Q2. (Beginner) What is an index? What is a document in Elasticsearch?

**Answer:**  
An **index** is a collection of **documents** (like a table). A **document** is a JSON object with a unique `_id` within the index. Documents are **inverted-indexed** for search (terms → document IDs). Index can have a **mapping** (schema for fields: type, analyzer, etc.).

---

## Q3. (Intermediate) How do you index a single document using the Elasticsearch REST API? How with the Node.js client?

**Answer:**  
**REST**: `PUT /my_index/_doc/1` with JSON body. **Node.js (@elastic/elasticsearch):**
```javascript
await client.index({
  index: 'my_index',
  id: '1',
  document: { title: 'Hello', body: 'World', created: new Date() }
});
```
Omit `id` for auto-generated ID. Use **bulk** API for many documents.

---

## Q4. (Intermediate) What is the difference between refresh and flush? When is a document searchable?

**Answer:**  
**Refresh**: makes recent index changes visible to **search** (in-memory segment → searchable). Default refresh_interval is 1s. **Flush**: writes in-memory segments to **disk** (durability). A document is **searchable** after refresh (not necessarily after flush). For near-real-time search, refresh happens periodically; for bulk load you might disable refresh and refresh once at the end.

---

## Q5. (Intermediate) What is an analyzer? What are tokenizer and token filters?

**Answer:**  
An **analyzer** turns text into **tokens** for indexing and search. It has: (1) **Tokenizer** — splits text (e.g. standard, whitespace). (2) **Token filters** — lowercasing, stop words, synonym, etc. **Analysis** happens at index time (index analyzer) and at search time (search analyzer); they’re often the same. Custom analyzer = tokenizer + list of token filters.

---

## Q6. (Advanced) How does the backend (Node.js) connect to Elasticsearch and index a batch of documents? Show bulk indexing.

**Answer:**
```javascript
const { Client } = require('@elastic/elasticsearch');
const client = new Client({ node: process.env.ES_URL });

async function bulkIndex(indexName, docs) {
  const body = docs.flatMap(doc => [
    { index: { _index: indexName, _id: doc.id } },
    { title: doc.title, body: doc.body, created: doc.created }
  ]);
  const result = await client.bulk({ refresh: false, body });
  if (result.errors) {
    const failed = result.items.filter(i => i.index?.error);
    throw new Error(JSON.stringify(failed));
  }
  return result;
}
```
Use **refresh: false** during bulk to avoid refreshing every batch; refresh once after all batches or rely on default interval.

---

## Q7. (Advanced) What is the inverted index? How does it relate to full-text search?

**Answer:**  
**Inverted index**: for each **term** (token), a list of **document IDs** (and positions) that contain that term. So “hello” → [doc1, doc3]. Search: look up terms in the index, get document sets, combine (AND/OR), rank. Full-text search uses this for fast lookup and scoring (TF-IDF, BM25). Exact match uses keyword (not analyzed) field; full-text uses analyzed text field.

---

## Q8. (Advanced) Production scenario: Your app writes events to MongoDB and you want them searchable in Elasticsearch. How do you keep them in sync? Describe two approaches.

**Answer:**  
(1) **Dual write**: app writes to MongoDB and to Elasticsearch (or to a queue that a worker consumes and indexes). Risk: two systems can get out of sync; use idempotent indexing and retries. (2) **Change stream / CDC**: tail MongoDB oplog or change stream; a worker publishes changes to a queue; indexer consumes and updates Elasticsearch. Single source of truth (MongoDB); Elasticsearch is eventually consistent. Prefer CDC for consistency; dual write for simplicity if you can tolerate drift and repair.

---

## Q9. (Advanced) What is the difference between keyword and text mapping? When would you use each?

**Answer:**  
**keyword**: not analyzed; stored and indexed as a single term. Use for **exact match**, filters, aggregations, sorting (e.g. status, category, id). **text**: analyzed (tokenized, lowercased, etc.). Use for **full-text search** (e.g. product description, log message). A field can have both: **fields** sub-mapping — e.g. `title` as text and `title.keyword` as keyword for sort/agg.

---

## Q10. (Advanced) How do you create an index with a custom mapping and a custom analyzer (e.g. with synonym filter)? Show minimal example.

**Answer:**
```javascript
await client.indices.create({
  index: 'products',
  body: {
    settings: {
      analysis: {
        analyzer: {
          my_synonyms: {
            tokenizer: 'standard',
            filter: ['lowercase', 'my_synonym_filter']
          }
        },
        filter: {
          my_synonym_filter: {
            type: 'synonym',
            synonyms: ['laptop, notebook']
          }
        }
      }
    },
    mappings: {
      properties: {
        title: { type: 'text', analyzer: 'my_synonyms' },
        sku: { type: 'keyword' }
      }
    }
  }
});
```
