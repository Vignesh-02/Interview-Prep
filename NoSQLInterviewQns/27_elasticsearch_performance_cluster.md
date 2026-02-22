# 27. Elasticsearch Performance & Cluster Management — Senior

## Q1. (Beginner) What is an Elasticsearch cluster? What are node roles (master, data, ingest)?

**Answer:**  
A **cluster** is a set of **nodes** that share the same cluster name and hold data and indices. **Node roles**: **master-eligible**: can be elected master (cluster state, index metadata). **data**: stores shards. **ingest**: runs ingest pipelines. A node can have multiple roles. **Master** node manages cluster; **data** nodes hold primary and replica shards.

---

## Q2. (Beginner) What is a primary shard vs a replica shard? Why do we have replicas?

**Answer:**  
**Primary shard**: the main copy of a shard’s data; writes go to primary then replicated. **Replica shard**: copy of a primary; used for **HA** (if primary is lost, replica is promoted) and **read scaling** (search can hit replica). Number of replicas is configurable per index (e.g. 1 replica = 2 copies total per shard).

---

## Q3. (Intermediate) How do you find slow queries in Elasticsearch? What is the slow log?

**Answer:**  
**Slow log**: index search and index (write) requests that exceed thresholds. Enable in index settings: `index.search.slowlog.threshold.query.warn: 2s`, `index.indexing.slowlog.threshold.index.warn: 1s`. Logs go to cluster logs or a dedicated log. **Profile API**: add `"profile": true` to the search body to get per-component timings. Use **Search Slow Log** and **Profile** to find and fix slow queries.

---

## Q4. (Intermediate) What is refresh interval? How does it affect search and indexing throughput?

**Answer:**  
**Refresh** makes new index changes **searchable**. **refresh_interval** (default 1s) controls how often refresh runs. **Shorter** (e.g. 100ms): more real-time search, more CPU and I/O. **Longer** (e.g. 30s) or **-1** (manual): better indexing throughput for bulk; search sees data only after refresh. For bulk indexing, set refresh_interval to -1 and refresh once at the end.

---

## Q5. (Intermediate) What is the bulk API and why use it for indexing from the backend?

**Answer:**  
**Bulk API** sends multiple index/update/delete operations in one HTTP request (NDJSON body). **Benefits**: fewer round-trips, higher throughput. From backend: collect documents (or batches of 500–1000), send one bulk request; handle errors in the response (per-item errors don’t fail the whole bulk). Use for initial load, sync from DB, or event ingestion.

---

## Q6. (Advanced) Production scenario: Search latency is high during peak. How do you diagnose and what levers can you pull (index, query, cluster)?

**Answer:**  
**Diagnose**: (1) **Profile API** or slow log to find slow queries. (2) **Nodes stats** (CPU, heap, GC). (3) **Index stats** (size, segment count). **Levers**: (1) **Query**: add filters, use filter context, avoid expensive aggregations or deep pagination (search_after). (2) **Index**: ensure mapping (keyword vs text), add replicas for read scaling, forcemerge to reduce segments (during low traffic). (3) **Cluster**: more data nodes, size heap (e.g. up to 31GB), avoid swapping. (4) **Caching**: filter cache, shard request cache where applicable.

---

## Q7. (Advanced) What is circuit breaker in Elasticsearch? Why can a query trigger “circuit_breaking_exception”?

**Answer:**  
**Circuit breakers** limit memory use (e.g. request circuit breaker, field data circuit breaker). If a single request or field data would exceed the limit, Elasticsearch throws **circuit_breaking_exception** to protect the node. **Fix**: reduce request size (e.g. aggregation size, batch size), add memory, or optimize query (e.g. avoid loading huge field data). Don’t disable circuit breakers; fix the query or scale.

---

## Q8. (Advanced) How do you add a new node to an existing cluster? What about rebalancing?

**Answer:**  
**Add node**: start Elasticsearch on the new machine with the same **cluster.name** and **discovery.seeds**; it joins the cluster. **Rebalancing**: by default, shards are allocated and rebalanced automatically. Control with **cluster.routing.rebalance.enable** and **allocation** settings. New node will receive shards (replicas or primaries) according to allocation rules. Monitor **cluster health** and **shard allocation**; use **cluster reroute** only for manual control or to unstick allocation.

---

## Q9. (Advanced) What is the difference between query_then_fetch and dfs_query_then_fetch? When does it matter?

**Answer:**  
**query_then_fetch**: each shard runs the query locally (with local IDF); coordinator merges and returns. **dfs_query_then_fetch**: first phase gathers **global** term frequencies, then runs the query with correct global IDF; more accurate relevance when you have multiple shards. Use **dfs** when you need consistent scoring across shards (e.g. small index with many shards). Cost: extra round-trip; use only when necessary.

---

## Q10. (Advanced) How would the backend (Node.js) implement a retry and backoff when Elasticsearch returns 503 or circuit_breaking_exception?

**Answer:**  
Wrap the search/index call in a retry loop with exponential backoff:

```javascript
async function searchWithRetry(client, params, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await client.search(params);
    } catch (e) {
      const retryable = e.meta?.statusCode === 503 || e.body?.error?.type === 'circuit_breaking_exception';
      if (!retryable || i === maxRetries - 1) throw e;
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 100));
    }
  }
}
```
Use for search and bulk; limit retries and backoff cap to avoid long delays.
