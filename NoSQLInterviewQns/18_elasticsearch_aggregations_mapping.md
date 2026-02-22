# 18. Elasticsearch Aggregations & Mapping

## Q1. (Beginner) What is an aggregation in Elasticsearch? Name two types.

**Answer:**  
**Aggregations** compute **metrics** or **buckets** over search results (or full index). **Metric**: sum, avg, min, max, cardinality (unique count). **Bucket**: group by field (terms), by range (range/date_range), by histogram. Results appear in the response under **aggregations**.

---

## Q2. (Beginner) How do you get the count of documents matching a query without returning hits?

**Answer:**  
Use **size: 0** and optionally **track_total_hits: true** (for exact count above 10k). The response has **hits.total** and **hits.hits** is empty. Or use **count** API: `client.count({ index, body: { query } })` which returns only the count.

---

## Q3. (Intermediate) Write an aggregation that buckets documents by a term (e.g. category) and returns the count per bucket. How do you get top 10 categories?

**Answer:**
```json
"aggs": {
  "by_category": {
    "terms": {
      "field": "category.keyword",
      "size": 10,
      "order": { "_count": "desc" }
    }
  }
}
```
Use **keyword** subfield for terms agg (text field is not suitable). Response: `aggregations.by_category.buckets` — array of { key, doc_count }.

---

## Q4. (Intermediate) What is a date_histogram aggregation? Give one use case.

**Answer:**  
**date_histogram** buckets documents by time interval (e.g. 1h, 1d). Use for: requests per hour, errors per day, time-series charts. Example: `"aggs": { "per_day": { "date_histogram": { "field": "timestamp", "calendar_interval": "day" } } }`. Returns buckets with key_as_string (date) and doc_count.

---

## Q5. (Intermediate) How do you combine a filter with aggregations (e.g. aggregate only over a subset)?

**Answer:**  
Use **query** in the search body to restrict the document set; aggregations run on the **matching** documents. Or use **filter** aggregation: `"aggs": { "filtered": { "filter": { "term": { "status": "active" } }, "aggs": { "by_cat": { "terms": { "field": "category.keyword" } } } } }` so the inner agg runs only on active docs.

---

## Q6. (Advanced) Write a search that returns: (1) hits for "laptop", (2) aggregation of top 5 categories, (3) aggregation of average price. Show Node.js request and how to read aggs.

**Answer:**
```javascript
const result = await client.search({
  index: 'products',
  body: {
    query: { match: { title: 'laptop' } },
    size: 20,
    aggs: {
      top_categories: {
        terms: { field: 'category.keyword', size: 5 }
      },
      avg_price: {
        avg: { field: 'price' }
      }
    }
  }
});
const hits = result.body.hits.hits;
const buckets = result.body.aggregations.top_categories.buckets;
const avgPrice = result.body.aggregations.avg_price.value;
```

---

## Q7. (Advanced) What is nested type vs object type? When do you need nested for aggregations?

**Answer:**  
**object**: default for JSON object; fields are flattened; array of objects is flattened so relation between inner fields is lost (e.g. “size” and “color” of same array element). **nested**: each array element is a hidden document; **nested** query/agg work on that sub-doc. Use **nested** when you have arrays of objects and need to query or aggregate per element (e.g. filter by one line item and aggregate by another field of the same item).

---

## Q8. (Advanced) Production scenario: You have an index of orders with line items (product_id, quantity, price). You need “total revenue by product_id” (sum of quantity*price per product). How do you model and aggregate?

**Answer:**  
**Option 1**: Denormalize at index time — each document = one line item (order_id, product_id, quantity, price, line_total). Then **terms** agg on product_id.keyword, **sum** sub-agg on line_total. **Option 2**: Nested line items — order doc has nested `items`. Use **nested** agg, then **terms** on product_id, **sum** on (quantity*price) via scripted_metric or store `line_total` in nested and sum it. Option 1 is simpler and usually faster; use it if you can index per line item.

---

## Q9. (Advanced) What is dynamic mapping? When would you explicitly disable it or set strict mapping?

**Answer:**  
**Dynamic mapping**: ES infers field types from the first document(s). New fields can be added automatically. **Disable** (e.g. "dynamic": "false") when you want to reject unknown fields (avoid accidental mapping drift). **Strict** ("dynamic": "strict") throws on unknown fields. Use explicit mapping + "dynamic": "false" or "strict" in production to control schema.

---

## Q10. (Advanced) How do you do a “global” aggregation (e.g. overall stats) plus a “filtered” aggregation (e.g. same stats for a subset) in one request?

**Answer:**  
Use two top-level aggs: one with **global** bucket (no filter), one with **filter** bucket, then same sub-aggs under each:
```json
"aggs": {
  "all": {
    "global": {},
    "aggs": {
      "avg_price": { "avg": { "field": "price" } }
    }
  },
  "active_only": {
    "filter": { "term": { "status": "active" } },
    "aggs": {
      "avg_price": { "avg": { "field": "price" } }
    }
  }
}
```
One request returns both overall and filtered metrics.
