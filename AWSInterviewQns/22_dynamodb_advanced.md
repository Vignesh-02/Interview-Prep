# 22. DynamoDB Advanced (Global Tables, DAX) — Senior

## Q1. (Beginner) What is DynamoDB Global Tables? How does replication work?

**Answer:**  
**Global Tables**: one logical table **replicated** to **2+ regions**; **last-writer-wins** conflict resolution; **eventually consistent** across regions. Writes in any region replicate to others (usually within seconds). Use for **multi-region** app (low-latency writes in each region) and **DR**. **Replication**: DynamoDB streams in each region drive replication to other regions (managed by AWS).

---

## Q2. (Beginner) What is DAX? When would you use it?

**Answer:**  
**DAX** (DynamoDB Accelerator): **in-memory cache** in front of DynamoDB; **microsecond** read latency; **compatible** with DynamoDB API (with cache-through). **Use** when: **read-heavy** workload; **hot keys** (same keys read very often); need **sub-millisecond** reads. **Cost**: cluster (nodes); use when read cost or latency justifies it. **Alternative**: **cache in application** (ElastiCache) with DynamoDB as source.

---

## Q3. (Intermediate) What is a hot partition in DynamoDB? How do you avoid it when the partition key has low cardinality?

**Answer:**  
**Hot partition**: one **partition key** value gets disproportionate traffic; that partition is throttled. **Avoid**: (1) **High cardinality** key (e.g. userId, not status). (2) **Write sharding**: add random suffix (e.g. pk = userId#0..9); write to random shard; read and merge. (3) **Composite** key (e.g. userId + date) to spread. (4) **Adaptive capacity** helps but doesn’t remove need for good design. Design so traffic is **spread** across many partition keys.

---

## Q4. (Intermediate) Production scenario: Your DynamoDB bill is high due to read traffic on a few hot keys (e.g. global config). How do you fix without increasing provisioned throughput?

**Answer:**  
(1) **DAX**: put **DAX** in front; cache the hot keys; reads served from cache (no DynamoDB read cost for cached items). (2) **Application cache**: cache in **ElastiCache** or in-app; TTL (e.g. 60 s); reduce read units. (3) **Eventually consistent** reads (half the RCU cost) if acceptable. (4) **Reduce** read frequency (longer cache TTL, batch). **Best**: **DAX** or **ElastiCache** for truly hot, read-mostly keys.

---

## Q5. (Intermediate) How do you implement conditional writes (e.g. “increment counter only if current value < 100”) in DynamoDB? Show UpdateItem with condition.

**Answer:**  
Use **ConditionExpression** on **UpdateItem**:
```javascript
await docClient.send(new UpdateCommand({
  TableName: 'Counters',
  Key: { pk: 'views', sk: 'page1' },
  UpdateExpression: 'SET #v = if_not_exists(#v, :zero) + :one',
  ConditionExpression: '#v < :max',
  ExpressionAttributeNames: { '#v': 'value' },
  ExpressionAttributeValues: { ':one': 1, ':zero': 0, ':max': 100 }
}));
```
If condition fails, you get **ConditionalCheckFailedException**; handle (e.g. return “limit reached”).

---

## Q6. (Advanced) What is DynamoDB Streams? How would you use it for an audit log or to sync to another system?

**Answer:**  
**DynamoDB Streams**: **change log** of item-level changes (INSERT, MODIFY, REMOVE); **ordered** per partition key. **Use**: (1) **Audit**: Lambda triggered by stream; write to S3 or another table (who changed what, when). (2) **Sync**: Lambda or Kinesis consumer writes to **Elasticsearch**, **RDS**, or **cache**. (3) **Event-driven**: trigger workflows (e.g. order updated → send notification). Enable stream (NEW_AND_OLD_IMAGES or KEYS_ONLY); attach **Lambda** or **Kinesis** trigger.

---

## Q7. (Advanced) Production scenario: You need strong consistency for “deduct balance” and “credit balance” across two items (e.g. two accounts). How do you do it in DynamoDB?

**Answer:**  
Use **TransactWriteItems**: one call that **atomically** updates multiple items (up to 100). (1) **ConditionCheck** or **Update** for account A (deduct); **ConditionExpression** balance >= amount. (2) **Update** for account B (credit). (3) Both in **TransactWriteItems**; if any condition fails, **entire transaction** is rolled back. **Idempotency**: use **ClientRequestToken** (idempotency key) so retries don’t double-apply. **Alternative**: single item with **transfer** record and **ConditionExpression**; or use **Step Functions** + compensating transactions (saga) if you need cross-table and can accept eventual consistency.

---

## Q8. (Advanced) How do you design for “query by status” (e.g. all PENDING orders) when the base table is keyed by userId and orderId?

**Answer:**  
**GSI**: create **GSI** with **partition key = status**, **sort key = createdAt** (or orderId). **Query** GSI where status = 'PENDING'. **Sparse**: only items with **status** set appear in GSI (or use a fixed attribute for all items). **Consider**: **status** has low cardinality (few values) → **hot partition** if many items share status. **Mitigation**: (1) **Composite** GSI key (e.g. status#date) for better spread. (2) **Limit** query (pagination). (3) Use **Scan** with filter only for rare admin queries; not for high QPS.

---

## Q9. (Advanced) Compare DynamoDB for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: on-demand; simple key design; single region. **Medium**: provisioned + auto scaling; **GSIs** for access patterns; **backup** (PITR). **Enterprise**: **Global Tables** for multi-region; **DAX** for read-heavy; **Streams** for audit/sync; **TransactWriteItems** for consistency; **single-table design**; encryption (KMS); fine-grained IAM.

---

## Q10. (Advanced) Senior red flags to avoid with DynamoDB

**Answer:**  
- **Scan** for regular API paths.  
- **Hot partition** (design for cardinality and sharding).  
- **No GSI** for “query by X” (don’t rely on Scan).  
- **Overuse of consistent read** (2× cost).  
- **No retry/backoff** for throttling.  
- **No backup** or point-in-time recovery.  
- **Sensitive data** without encryption (KMS).  
- **Ignoring** Streams for audit or event-driven use cases.

---

**Tradeoffs:** Startup: on-demand, simple keys. Medium: GSIs, backup. Enterprise: Global Tables, DAX, Streams, transactions.
