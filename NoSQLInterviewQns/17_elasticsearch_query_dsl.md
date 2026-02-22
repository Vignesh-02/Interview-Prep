# 17. Elasticsearch Query DSL & Search

## Q1. (Beginner) What is the difference between a query and a filter in Elasticsearch? What is the filter context vs query context?

**Answer:**  
**Query context**: affects **relevance score** (e.g. full-text match). **Filter context**: yes/no match, no score; can be cached. Use **bool** with **must** (query) for scoring and **filter** for exact conditions (e.g. status=active, date range). Filters are cached and often faster for structured conditions.

---

## Q2. (Beginner) How do you search for a term in a keyword field? How do you full-text search in a text field?

**Answer:**  
**Keyword** (exact): `{ "term": { "status": "active" } }` or `{ "terms": { "tags": ["a","b"] } }`. **Text** (full-text): `{ "match": { "description": "laptop computer" } }` — analyzed and scored. **Match phrase**: `{ "match_phrase": { "description": "laptop computer" } }` for phrase proximity.

---

## Q3. (Intermediate) Write a bool query that: must match "error" in message, filter by timestamp in last 24 hours and level = "error".

**Answer:**
```json
{
  "bool": {
    "must": [
      { "match": { "message": "error" } }
    ],
    "filter": [
      { "range": { "timestamp": { "gte": "now-24h" } } },
      { "term": { "level": "error" } }
    ]
  }
}
```

---

## Q4. (Intermediate) What is match_phrase vs match? When would you use match_phrase_prefix?

**Answer:**  
**match**: terms are analyzed; documents matching any term (with optional minimum_should_match) are returned; terms can be in any order. **match_phrase**: terms must appear in that order and close together (slop). **match_phrase_prefix**: like phrase but last term is prefix (e.g. "quick brown f" matches "quick brown fox"); good for autocomplete.

---

## Q5. (Intermediate) How do you implement pagination? What are from/size and search_after?

**Answer:**  
**from/size**: `from: 0, size: 20` for first page; `from: 20, size: 20` for second. Deep pagination (e.g. from=10000) is expensive — ES must fetch and skip. **search_after**: sort by a unique field (e.g. _id) and pass last sort values from previous page; no global offset. Prefer **search_after** for deep pagination; use **from/size** for small page numbers only.

---

## Q6. (Advanced) How do you run a search from Node.js and parse hits? Show a minimal example with filters and pagination.

**Answer:**
```javascript
const result = await client.search({
  index: 'logs',
  body: {
    query: {
      bool: {
        filter: [
          { "range": { "timestamp": { "gte": "now-24h" } } },
          { "term": { "level": "error" } }
        ]
      }
    },
    from: 0,
    size: 20,
    sort: [{ timestamp: 'desc' }]
  }
});
const hits = result.body.hits.hits;  // array of { _source, _id, _score }
const total = result.body.hits.total?.value ?? result.body.hits.total;
const docs = hits.map(h => ({ id: h._id, ...h._source }));
```

---

## Q7. (Advanced) What is the difference between query_string and simple_query_string? When would you use each?

**Answer:**  
**query_string**: full Lucene syntax (AND, OR, wildcards, phrases, etc.); powerful but can throw on invalid input; avoid exposing directly to users. **simple_query_string**: subset of syntax, more forgiving; good for user-facing search boxes. Use **simple_query_string** for end-user input; **query_string** for internal or controlled input.

---

## Q8. (Advanced) Production scenario: Your API has a search box. User types "wireless mouse". You want: (1) relevance by text match, (2) filter by category and price range from query params, (3) pagination. Build the Elasticsearch query and show how the backend builds it.

**Answer:**
```javascript
function buildSearchBody(q, filters = {}, from = 0, size = 20) {
  const body = {
    query: {
      bool: {
        must: [],
        filter: []
      }
    },
    from,
    size,
    sort: [{ _score: 'desc' }, { created: 'desc' }]
  };
  if (q && q.trim()) {
    body.query.bool.must.push({ match: { title: { query: q, fuzziness: 'AUTO' } } });
  }
  if (filters.category) {
    body.query.bool.filter.push({ term: { category: filters.category } });
  }
  if (filters.minPrice != null || filters.maxPrice != null) {
    const range = {};
    if (filters.minPrice != null) range.gte = filters.minPrice;
    if (filters.maxPrice != null) range.lte = filters.maxPrice;
    body.query.bool.filter.push({ range: { price: range } });
  }
  return body;
}
// Usage: client.search({ index: 'products', body: buildSearchBody(req.query.q, req.query, page*20, 20) })
```

---

## Q9. (Advanced) What are multi_match and best_fields vs cross_fields? When would you search across multiple fields?

**Answer:**  
**multi_match**: same query against multiple fields (e.g. title, description). **best_fields**: score from the best matching field (default). **cross_fields**: treat multiple fields as one big field (good for “first name + last name” spread across fields). Use **multi_match** when the user query could match title or description; use **cross_fields** when the meaning spans fields.

---

## Q10. (Advanced) How do you implement highlighting (show snippet where the match occurred)? Show the request and how to read fragments in the response.

**Answer:**  
Add **highlight** to the request:
```json
"highlight": {
  "fields": {
    "title": {},
    "body": { "fragment_size": 150, "number_of_fragments": 3 }
  }
}
```
Response: each hit has `highlight.title` or `highlight.body` — array of strings with `<em>` around matched terms. In Node: `hit.highlight?.body ?? hit._source.body` for snippet; render with HTML escaped.
